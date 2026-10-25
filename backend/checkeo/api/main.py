"""API HTTP de Checkeo.

    GET /api/stations?q=lil&limit=10
    GET /api/profile?from=city:59350&to=city:75056&day_type=weekday&bin=60&arrive_by=09:00&leave_after=18:00
    GET /api/meta
"""

from __future__ import annotations

import datetime as dt
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Literal

import numpy as np
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ..config import DB_PATH, ROOT
from ..core.gtfs_time import parse_hhmm
from ..service import BadRequest, Checkeo, NotFound


def _default(o: Any):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(f"Type non sérialisable : {type(o)}")


class JSON(JSONResponse):
    """Réponse JSON tolérant les types numpy ; refuse NaN (JSON invalide)."""

    def render(self, content: Any) -> bytes:
        return json.dumps(content, default=_default, ensure_ascii=False, allow_nan=False).encode("utf-8")


def create_app(db_path: Path | None = None, static_dir: Path | None = None) -> FastAPI:
    db_path = db_path or DB_PATH

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = Checkeo(db_path)
        yield
        app.state.service.con.close()

    app = FastAPI(title="Checkeo", version="0.1.0", default_response_class=JSON, lifespan=lifespan)
    origins = os.environ.get("CHECKEO_CORS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], allow_headers=["*"])

    def service(request: Request) -> Checkeo:
        return request.app.state.service

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/stations")
    def stations(request: Request, q: Annotated[str, Query(min_length=1, max_length=80)],
                 limit: Annotated[int, Query(ge=1, le=50)] = 10):
        return {"results": service(request).search_stations(q, limit)}

    @app.get("/api/profile")
    def profile(
        request: Request,
        from_: Annotated[str, Query(alias="from", description="id de ville (city:…) ou de gare (StopArea:…)")],
        to: Annotated[str, Query()],
        day_type: Literal["weekday", "saturday", "sunday"] = "weekday",
        bin: Annotated[int, Query(description="pas de l'histogramme en minutes")] = 60,
        arrive_by: str = "09:00",
        leave_after: str = "18:00",
        include_buses: bool = False,
    ):
        if bin not in (15, 30, 60, 120):
            raise HTTPException(422, "bin doit valoir 15, 30, 60 ou 120")
        try:
            arrive_s, leave_s = parse_hhmm(arrive_by), parse_hhmm(leave_after)
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        try:
            return service(request).profile(
                from_, to, day_type, bin_minutes=bin, arrive_by_s=arrive_s,
                leave_after_s=leave_s, include_buses=include_buses,
            )
        except NotFound as e:
            raise HTTPException(404, str(e)) from e
        except BadRequest as e:
            raise HTTPException(400, str(e)) from e

    @app.get("/api/meta")
    def meta(request: Request):
        return service(request).public_meta()

    # En production, le frontend compilé (frontend/dist) est servi par la même application.
    static_dir = static_dir or ROOT / "frontend" / "dist"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
    return app


app = create_app()

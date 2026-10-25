"""Lecture d'un GTFS (zip ou répertoire) et normalisation en tables prêtes pour DuckDB."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from ..core.calendar import expand_service_dates
from ..core.gtfs_time import parse_gtfs_time

GTFS_FILES = [
    "agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt",
    "calendar.txt", "calendar_dates.txt", "feed_info.txt",
]

# Le mode commercial est encodé dans l'identifiant des StopPoint SNCF : "StopPoint:OCETGV INOUI-87223263".
STOP_POINT_MODE = re.compile(r"^StopPoint:OCE(.+)-\d+$")

MODE_FAMILY = {
    "TGV INOUI": "TGV",
    "OUIGO": "TGV",
    "ICE": "TGV",
    "Lyria": "TGV",
    "INTERCITES": "IC",
    "INTERCITES de nuit": "IC",
    "Train TER": "TER",
    "TramTrain": "TER",
    "Car TER": "TER",
    "Car à réservation": "TER",
}

ROUTE_TYPE_MODE = {"0": "Tram", "1": "Métro", "2": "Train", "3": "Car"}


def read_gtfs(path: str | Path) -> dict[str, pd.DataFrame]:
    """Lit les fichiers GTFS utiles, toutes colonnes en texte. Fichiers absents → non présents."""
    path = Path(path)
    tables: dict[str, pd.DataFrame] = {}

    def load(raw: bytes) -> pd.DataFrame:
        return pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False, encoding="utf-8-sig")

    if path.is_dir():
        for name in GTFS_FILES:
            f = path / name
            if f.exists():
                tables[name.removesuffix(".txt")] = load(f.read_bytes())
    else:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            for name in GTFS_FILES:
                if name in names:
                    tables[name.removesuffix(".txt")] = load(z.read(name))
    for required in ("stops", "routes", "trips", "stop_times"):
        if required not in tables:
            raise ValueError(f"GTFS incomplet : {required}.txt manquant")
    if "calendar" not in tables and "calendar_dates" not in tables:
        raise ValueError("GTFS incomplet : ni calendar.txt ni calendar_dates.txt")
    return tables


def _int(series: pd.Series, default: int = 0) -> pd.Series:
    return pd.to_numeric(series.replace("", None), errors="coerce").fillna(default).astype(int)


def mode_of_stop(stop_id: str) -> str | None:
    m = STOP_POINT_MODE.match(stop_id)
    return m.group(1) if m else None


def normalize(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Produit les tables normalisées : stops, trips, stop_times, service_dates, feed_info."""
    stops = tables["stops"].copy()
    if "parent_station" not in stops:
        stops["parent_station"] = ""
    if "location_type" not in stops:
        stops["location_type"] = "0"
    # Chaque arrêt est rattaché à sa zone d'arrêt (StopArea) ; un arrêt sans parent est sa propre zone.
    stops["stop_area_id"] = stops["parent_station"].where(stops["parent_station"] != "", stops["stop_id"])

    st = tables["stop_times"]
    area_of = dict(zip(stops["stop_id"], stops["stop_area_id"]))
    stop_times = pd.DataFrame({
        "trip_id": st["trip_id"],
        "stop_id": st["stop_id"],
        "stop_area_id": st["stop_id"].map(area_of).fillna(st["stop_id"]),
        "seq": _int(st["stop_sequence"]),
        "arr_s": st["arrival_time"].map(parse_gtfs_time),
        "dep_s": st["departure_time"].map(parse_gtfs_time),
        "pickup_type": _int(st["pickup_type"]) if "pickup_type" in st else 0,
        "drop_off_type": _int(st["drop_off_type"]) if "drop_off_type" in st else 0,
    })
    # Un horaire manquant (arrêt non « timepoint ») reprend l'autre horaire du même arrêt.
    stop_times["arr_s"] = stop_times["arr_s"].fillna(stop_times["dep_s"])
    stop_times["dep_s"] = stop_times["dep_s"].fillna(stop_times["arr_s"])
    stop_times = stop_times.dropna(subset=["arr_s", "dep_s"])
    stop_times[["arr_s", "dep_s"]] = stop_times[["arr_s", "dep_s"]].astype(int)

    routes = tables["routes"]
    trips = tables["trips"].merge(
        routes[["route_id", "route_type", "agency_id"] if "agency_id" in routes else ["route_id", "route_type"]],
        on="route_id", how="left",
    )
    if "agency_id" not in trips:
        trips["agency_id"] = ""
    # Mode commercial : celui du premier arrêt du trip.
    first_stop = stop_times.sort_values(["trip_id", "seq"]).drop_duplicates("trip_id")[["trip_id", "stop_id"]]
    trips = trips.merge(first_stop, on="trip_id", how="left")
    trips["mode"] = trips["stop_id"].fillna("").map(mode_of_stop)
    trips["mode"] = trips["mode"].fillna(trips["route_type"].map(ROUTE_TYPE_MODE)).fillna("Autre")
    trips["family"] = trips["mode"].map(MODE_FAMILY).fillna("AUTRE")
    number = trips["trip_short_name"] if "trip_short_name" in trips else pd.Series("", index=trips.index)
    if "trip_headsign" in trips:
        number = number.where(number != "", trips["trip_headsign"])
    trips["train_number"] = number.where(number != "", trips["trip_id"])
    trips["is_bus"] = trips["route_type"].isin(["3", "700", "200"]) | trips["mode"].str.startswith("Car")
    trips = trips[["trip_id", "service_id", "route_id", "route_type", "agency_id",
                   "train_number", "mode", "family", "is_bus"]]

    service_dates = expand_service_dates(tables.get("calendar"), tables.get("calendar_dates"))

    feed_info = tables.get("feed_info", pd.DataFrame())
    return {
        "stops": stops,
        "trips": trips,
        "stop_times": stop_times.drop(columns=["stop_id"]),
        "service_dates": service_dates,
        "feed_info": feed_info,
    }

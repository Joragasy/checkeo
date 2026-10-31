"""Construction de la base PostgreSQL à partir des données brutes déjà lues en mémoire.

Les tables sont chargées dans un schéma de travail (`<schéma>_build`), puis échangées avec le
schéma en service dans une seule transaction : l'ancienne base reste lisible jusqu'au bout et
une ingestion qui échoue n'y touche pas.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

import holidays as holidays_lib
import numpy as np
import pandas as pd
import psycopg
from psycopg import sql

from ..core.daytype import sample_dates
from .gtfs_load import normalize, read_gtfs
from .regularity import build_regularity, build_regularity_map, load_overrides
from .stations import build_stations

log = logging.getLogger(__name__)

DEFAULT_OVERRIDES = Path(__file__).with_name("regularity_overrides.csv")


def _feed_period(feed_info: pd.DataFrame, service_dates: pd.DataFrame) -> tuple[dt.date, dt.date, str | None]:
    if len(feed_info) and feed_info.iloc[0].get("feed_start_date") and feed_info.iloc[0].get("feed_end_date"):
        row = feed_info.iloc[0]
        start = dt.datetime.strptime(row["feed_start_date"], "%Y%m%d").date()
        end = dt.datetime.strptime(row["feed_end_date"], "%Y%m%d").date()
        return start, end, row.get("feed_version") or None
    return service_dates["date"].min(), service_dates["date"].max(), None


def trip_regions(stop_times: pd.DataFrame, stations: pd.DataFrame) -> pd.Series:
    """Région d'exploitation de chaque trip : la région la plus représentée parmi ses arrêts,
    hors Île-de-France (un TER Paris – Chartres est un TER Centre-Val de Loire)."""
    st = stop_times[["trip_id", "stop_area_id"]].merge(
        stations[["stop_area_id", "region_code"]], on="stop_area_id"
    )
    st = st[st["region_code"].notna() & (st["region_code"] != "11")]
    counts = st.groupby(["trip_id", "region_code"]).size().reset_index(name="n")
    best = counts.sort_values(["trip_id", "n"], ascending=[True, False]).drop_duplicates("trip_id")
    return best.set_index("trip_id")["region_code"]


def _pg_type(s: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(s):
        return "boolean"
    if pd.api.types.is_integer_dtype(s):
        return "bigint"
    if pd.api.types.is_float_dtype(s):
        return "double precision"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "timestamp"
    # Colonne objet (valeurs manquantes mêlées, listes, dates) : type des valeurs présentes.
    kind = pd.api.types.infer_dtype(s, skipna=True)
    if kind == "boolean":
        return "boolean"
    if kind == "integer":
        return "bigint"
    if kind in ("floating", "mixed-integer-float", "decimal"):
        return "double precision"
    if kind in ("datetime", "datetime64"):
        return "timestamp"
    if kind == "date":
        return "date"
    sample = next((v for v in s if isinstance(v, (list, tuple, np.ndarray))), None)
    if sample is not None:
        return "text[]"
    return "text"


def _cell(v):
    if isinstance(v, np.ndarray):
        return [str(x) for x in v.tolist()]
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    if isinstance(v, np.generic):
        v = v.item()
    if v is None or v is pd.NaT or (isinstance(v, float) and np.isnan(v)) or v is pd.NA:
        return None
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    return v


def write_table(cur: psycopg.Cursor, schema: str, name: str, df: pd.DataFrame) -> None:
    """Crée `schema.name` d'après les types de `df` et y copie ses lignes (COPY)."""
    types = {c: _pg_type(df[c]) for c in df.columns}
    table = sql.Identifier(schema, name)
    cur.execute(sql.SQL("CREATE TABLE {} ({})").format(
        table, sql.SQL(", ").join(sql.SQL("{} " + t).format(sql.Identifier(c)) for c, t in types.items()),
    ))
    if df.empty:
        return
    casts = {"text": str, "bigint": int, "double precision": float}
    cols = [(df[c].to_numpy(dtype=object), casts.get(types[c])) for c in df.columns]
    with cur.copy(sql.SQL("COPY {} FROM STDIN").format(table)) as copy:
        for i in range(len(df)):
            row = []
            for values, cast in cols:
                v = _cell(values[i])
                row.append(cast(v) if cast is not None and v is not None else v)
            copy.write_row(row)


def _swap_schema(cur: psycopg.Cursor, staging: str, schema: str) -> None:
    old = f"{schema}_old"
    cur.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(old)))
    cur.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", (schema,))
    if cur.fetchone():
        cur.execute(sql.SQL("ALTER SCHEMA {} RENAME TO {}").format(sql.Identifier(schema), sql.Identifier(old)))
    cur.execute(sql.SQL("ALTER SCHEMA {} RENAME TO {}").format(sql.Identifier(staging), sql.Identifier(schema)))
    cur.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(old)))


def build_database(
    *,
    gtfs_path: Path,
    gares: pd.DataFrame,
    communes: pd.DataFrame,
    tgv: pd.DataFrame,
    ter: pd.DataFrame,
    intercites: pd.DataFrame,
    dsn: str,
    schema: str,
    sample_start: dt.date | None = None,
    weeks: int = 4,
    sources: dict | None = None,
    overrides_path: Path | None = DEFAULT_OVERRIDES,
    today: dt.date | None = None,
) -> dict:
    """Construit le schéma `schema` de la base `dsn` (remplacé de façon atomique). Retourne un petit rapport."""
    today = today or dt.date.today()
    g = normalize(read_gtfs(gtfs_path))
    feed_start, feed_end, feed_version = _feed_period(g["feed_info"], g["service_dates"])

    stations, groups = build_stations(g["stops"], g["stop_times"], g["trips"], gares, communes)
    g["trips"]["region_code"] = trip_regions(g["stop_times"], stations).reindex(g["trips"]["trip_id"]).values

    hol = holidays_lib.country_holidays("FR", years=range(feed_start.year, feed_end.year + 1))
    samples = sample_dates(sample_start or today, weeks, feed_start, feed_end, hol.keys())
    samples_df = pd.DataFrame(
        [(t, d) for t, ds in samples.items() for d in ds], columns=["day_type", "date"]
    )

    regularity = build_regularity(tgv, ter, intercites)
    reg_map, reg_report = build_regularity_map(regularity, stations, load_overrides(overrides_path))

    reg_last = {
        fam: (sub["month"].max().isoformat() if len(sub) else None)
        for fam, sub in regularity.groupby("family")
    }
    meta = {
        "built_at": dt.datetime.now().isoformat(timespec="seconds"),
        "feed_start": feed_start.isoformat(),
        "feed_end": feed_end.isoformat(),
        "feed_version": feed_version,
        "sample_weeks": weeks,
        "samples": {t: [d.isoformat() for d in ds] for t, ds in samples.items()},
        "regularity_last_month": reg_last,
        "sources": sources or {},
    }

    tables = {
        "stations": stations,
        "city_groups": groups,
        "trips": g["trips"],
        "stop_times": g["stop_times"],
        "service_dates": g["service_dates"],
        "day_type_samples": samples_df,
        "regularity": regularity,
        "regularity_map": reg_map,
        "regularity_match_report": reg_report,
    }
    staging = f"{schema}_build"
    with psycopg.connect(dsn) as con, con.cursor() as cur:
        cur.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(staging)))
        cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(staging)))
        for name, df in tables.items():
            log.info("chargement de %s (%d lignes)", name, len(df))
            write_table(cur, staging, name, df)
        cur.execute(sql.SQL("CREATE TABLE {} (key text PRIMARY KEY, value text)").format(
            sql.Identifier(staging, "meta")))
        cur.executemany(sql.SQL("INSERT INTO {} VALUES (%s, %s)").format(sql.Identifier(staging, "meta")),
                        [(k, json.dumps(v)) for k, v in meta.items()])
        for index, table, column in [("st_area", "stop_times", "stop_area_id"),
                                     ("st_trip", "stop_times", "trip_id"),
                                     ("sd_service", "service_dates", "service_id")]:
            cur.execute(sql.SQL("CREATE INDEX {} ON {} ({})").format(
                sql.Identifier(index), sql.Identifier(staging, table), sql.Identifier(column)))
        con.commit()
        # ANALYZE hors transaction de chargement, puis échange des schémas en une transaction.
        for name in [*tables, "meta"]:
            cur.execute(sql.SQL("ANALYZE {}").format(sql.Identifier(staging, name)))
        _swap_schema(cur, staging, schema)
        con.commit()

    report = {name: len(df) for name, df in tables.items()}
    report["unmatched_regularity_labels"] = reg_report[reg_report["n_stops"] == 0]["label"].tolist()
    report["feed"] = [feed_start.isoformat(), feed_end.isoformat()]
    report["samples"] = {t: len(ds) for t, ds in samples.items()}
    return report

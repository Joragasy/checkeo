"""Construction de la base DuckDB à partir des données brutes déjà lues en mémoire."""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
from pathlib import Path

import duckdb
import holidays as holidays_lib
import pandas as pd

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


def build_database(
    *,
    gtfs_path: Path,
    gares: pd.DataFrame,
    communes: pd.DataFrame,
    tgv: pd.DataFrame,
    ter: pd.DataFrame,
    intercites: pd.DataFrame,
    out_path: Path,
    sample_start: dt.date | None = None,
    weeks: int = 4,
    sources: dict | None = None,
    overrides_path: Path | None = DEFAULT_OVERRIDES,
    today: dt.date | None = None,
) -> dict:
    """Construit `out_path` (remplacé de façon atomique). Retourne un petit rapport."""
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

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".tmp")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    try:
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
        for name, df in tables.items():
            con.register("df_tmp", df)
            con.execute(f"CREATE TABLE {name} AS SELECT * FROM df_tmp")
            con.unregister("df_tmp")
        con.execute("CREATE TABLE meta (key VARCHAR PRIMARY KEY, value VARCHAR)")
        con.executemany("INSERT INTO meta VALUES (?, ?)", [(k, json.dumps(v)) for k, v in meta.items()])
        con.execute("CREATE INDEX st_area ON stop_times(stop_area_id)")
        con.execute("CREATE INDEX st_trip ON stop_times(trip_id)")
        con.execute("CREATE INDEX sd_service ON service_dates(service_id)")
        con.execute("CHECKPOINT")
    finally:
        con.close()
    os.replace(tmp, out_path)

    report = {name: len(df) for name, df in tables.items()}
    report["unmatched_regularity_labels"] = reg_report[reg_report["n_stops"] == 0]["label"].tolist()
    report["feed"] = [feed_start.isoformat(), feed_end.isoformat()]
    report["samples"] = {t: len(ds) for t, ds in samples.items()}
    return report

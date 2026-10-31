"""Accès à la base PostgreSQL et calcul d'un profil navetteur complet (aller + retour + fiabilité)."""

from __future__ import annotations

import datetime as dt
import json
from functools import lru_cache
import unicodedata
from dataclasses import dataclass

import pandas as pd
import psycopg
from psycopg_pool import ConnectionPool

from .config import check_dsn
from .core.connections import connection_counts
from .core.daytype import DAY_TYPE_LABELS, typical_day
from .core.gtfs_time import format_display
from .core.indicators import direction_profile
from .core.reliability import reliability_blocks
from .ingest.stations import REGION_NAMES
from .core.trips import Journey, Leg, merge_coupled, select_direct_legs

# Identité d'un train sur un sens donné, et ce qui peut varier d'une date à l'autre.
ID = ["train_number"]
TIMES = ["o_stop", "d_stop", "dep_s", "arr_s"]
# int2, int4, int8, float4, float8, numeric
NUMERIC_OIDS = {21, 23, 20, 700, 701, 1700}


class NotFound(Exception):
    pass


class BadRequest(Exception):
    pass


def fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return " ".join("".join(c if c.isalnum() else " " for c in t).split())


@dataclass
class Place:
    id: str
    kind: str  # "city" | "station"
    name: str
    stop_area_ids: list[str]
    regions: list[tuple[str | None, str | None]]


class Checkeo:
    def __init__(self, dsn: str, schema: str = "checkeo"):
        check_dsn(dsn)
        with psycopg.connect(dsn) as con:
            found = con.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = 'meta'", (schema,)
            ).fetchone()
        if not found:
            raise RuntimeError(
                f"Schéma {schema!r} vide ou absent. Lancez d'abord `uv run python -m checkeo.ingest.run`."
            )
        # Connexions en lecture seule, sur le schéma de Checkeo.
        options = f"-c search_path={schema} -c default_transaction_read_only=on"
        self.pool = ConnectionPool(dsn, min_size=1, max_size=4, kwargs={"options": options, "autocommit": True},
                                   open=True)
        q = self._df
        self.meta = {r.key: json.loads(r.value) for r in q("SELECT key, value FROM meta").itertuples()}
        self.stations = q("SELECT * FROM stations")
        self.groups = q("SELECT * FROM city_groups")
        self.regularity = q("SELECT * FROM regularity")
        self.reg_map = q("SELECT * FROM regularity_map")
        samples = q("SELECT day_type, date FROM day_type_samples ORDER BY date")
        samples["date"] = pd.to_datetime(samples["date"]).dt.date
        self.samples = {t: list(sub["date"]) for t, sub in samples.groupby("day_type")}
        # Valeurs manquantes → None (sérialisables en JSON), y compris pour les colonnes texte.
        self.stations = self.stations.astype(object).where(self.stations.notna(), None)
        self.groups = self.groups.astype(object).where(self.groups.notna(), None)
        self.station_by_id = self.stations.set_index("stop_area_id").to_dict("index")
        self._search_index = self._build_search_index()
        # Base en lecture seule : un résultat calculé reste valable tant que l'application tourne.
        self.connections = lru_cache(maxsize=256)(self._connections)

    def _df(self, query: str, params: dict | None = None) -> pd.DataFrame:
        with self.pool.connection() as con, con.cursor() as cur:
            cur.execute(query, params)
            desc = cur.description
            df = pd.DataFrame(cur.fetchall(), columns=[d.name for d in desc])
        # Colonnes numériques : vrais types numpy (NULL → NaN).
        for d in desc:
            if d.type_code in NUMERIC_OIDS:
                df[d.name] = pd.to_numeric(df[d.name])
        return df

    def close(self) -> None:
        self.pool.close()

    # ------------------------------------------------------------------ recherche de gares
    def _build_search_index(self) -> list[dict]:
        items = []
        for g in self.groups.itertuples(index=False):
            items.append({
                "id": g.city_group_id, "kind": "city", "name": f"{g.city_name} (toutes gares)",
                "city": g.city_name, "n_stations": len(g.stop_area_ids), "modes": list(g.modes),
                "_key": fold(g.city_name), "_rank": 0,
            })
        for s in self.stations[self.stations["train_served"]].itertuples(index=False):
            items.append({
                "id": s.stop_area_id, "kind": "station", "name": s.name, "city": s.city_name,
                "n_stations": 1, "modes": list(s.modes), "_key": fold(s.name), "_rank": 1,
            })
        return items

    def search_stations(self, q: str, limit: int = 10) -> list[dict]:
        key = fold(q)
        if not key:
            return []
        words = key.split()
        prefix, contains = [], []
        for it in self._search_index:
            k = it["_key"]
            if k.startswith(key):
                prefix.append(it)
            elif all(w in k for w in words):
                contains.append(it)
        ranked = sorted(prefix, key=lambda i: (i["_rank"], len(i["_key"]), i["_key"])) + \
            sorted(contains, key=lambda i: (i["_rank"], len(i["_key"]), i["_key"]))
        return [{k: v for k, v in it.items() if not k.startswith("_")} for it in ranked[:limit]]

    # ------------------------------------------------------------------ profil
    def resolve(self, place_id: str) -> Place:
        if place_id.startswith("city:"):
            g = self.groups[self.groups["city_group_id"] == place_id]
            if g.empty:
                raise NotFound(f"Ville inconnue : {place_id}")
            row = g.iloc[0]
            return Place(place_id, "city", row["city_name"], list(row["stop_area_ids"]),
                         [(row["region_code"], row["region_name"])])
        s = self.station_by_id.get(place_id)
        if s is None:
            raise NotFound(f"Gare inconnue : {place_id}")
        return Place(place_id, "station", s["name"], [place_id], [(s["region_code"], s["region_name"])])

    def _candidates(self, origins: list[str], dests: list[str]) -> pd.DataFrame:
        sql = """
            SELECT o.trip_id, o.stop_area_id AS o_stop, o.seq AS o_seq, o.dep_s, o.pickup_type AS o_pickup,
                   d.stop_area_id AS d_stop, d.seq AS d_seq, d.arr_s, d.drop_off_type AS d_dropoff
            FROM stop_times o
            JOIN stop_times d ON o.trip_id = d.trip_id
            WHERE o.stop_area_id = ANY(%(o)s) AND d.stop_area_id = ANY(%(d)s)
              AND o.seq < d.seq
        """
        return self._df(sql, {"o": origins, "d": dests})

    def _trips_and_dates(self, trip_ids: list[str], dates: list[dt.date]) -> pd.DataFrame:
        sql = """
            SELECT t.trip_id, t.train_number, t.mode, t.family, t.is_bus, t.region_code, sd.date
            FROM trips t JOIN service_dates sd ON sd.service_id = t.service_id
            WHERE t.trip_id = ANY(%(t)s) AND sd.date = ANY(%(dates)s)
        """
        df = self._df(sql, {"t": trip_ids, "dates": dates})
        if len(df):
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def direction(self, origin: Place, dest: Place, day_type: str, include_buses: bool, threshold: float):
        """Trains directs origin → dest du jour type : (trajets réguliers, trains occasionnels, stats)."""
        dates = self.samples.get(day_type, [])
        legs = select_direct_legs(self._candidates(origin.stop_area_ids, dest.stop_area_ids))
        if legs.empty or not dates:
            occ = pd.DataFrame(columns=["date", *ID, *TIMES, "mode", "family", "region_code"])
        else:
            td = self._trips_and_dates(legs["trip_id"].tolist(), dates)
            if not include_buses:
                td = td[~td["is_bus"].astype(bool)]
            occ = legs.merge(td, on="trip_id")
        regular, occasional, stats = typical_day(occ, ID, TIMES, dates, threshold)
        # Mode et famille d'un train : ceux de l'une de ses circulations.
        attrs = occ.drop_duplicates(ID)[[*ID, "mode", "family", "region_code"]]
        regular = merge_coupled(regular.merge(attrs, on=ID, how="left"))
        occasional = merge_coupled(occasional.merge(attrs, on=ID, how="left"))
        return self._journeys(regular), self._journeys(occasional), stats

    @staticmethod
    def _journeys(trains: pd.DataFrame) -> list[Journey]:
        out = []
        for r in trains.itertuples(index=False):
            number = "/".join(r.train_numbers)
            out.append(Journey(
                legs=(Leg(number, r.mode, r.family, r.o_stop, r.d_stop, int(r.dep_s), int(r.arr_s)),),
                n_days=int(r.n_days), frequency=float(r.frequency),
                extra={"weekdays": list(r.weekdays), "dep_min_s": int(r.dep_min_s), "dep_max_s": int(r.dep_max_s),
                       "region_code": None if pd.isna(r.region_code) else r.region_code},
            ))
        return out

    def _train_rows(self, journeys: list[Journey]) -> list[dict]:
        rows = []
        for j in sorted(journeys, key=lambda j: (j.dep_s, j.arr_s)):
            leg = j.legs[0]
            rows.append({
                "train_number": leg.train_number, "mode": leg.mode, "family": leg.family,
                "from_stop": leg.from_stop, "from_name": self.station_by_id.get(leg.from_stop, {}).get("name"),
                "to_stop": leg.to_stop, "to_name": self.station_by_id.get(leg.to_stop, {}).get("name"),
                "dep_s": j.dep_s, "arr_s": j.arr_s, "dep": format_display(j.dep_s), "arr": format_display(j.arr_s),
                "duration_min": round(j.duration_s / 60), "n_days": j.n_days, "frequency": round(j.frequency, 2),
                "weekdays": j.extra.get("weekdays"),
                # Horaire de départ variable selon les dates échantillonnées (ex. travaux).
                "dep_range": [format_display(j.extra["dep_min_s"]), format_display(j.extra["dep_max_s"])]
                if j.extra.get("dep_min_s") != j.extra.get("dep_max_s") else None,
            })
        return rows

    def _reliability(self, journeys: list[Journey], today: dt.date) -> list[dict]:
        pairs: dict[str, set[tuple[str, str]]] = {}
        for j in journeys:
            for leg in j.legs:
                pairs.setdefault(leg.family, set()).add((leg.from_stop, leg.to_stop))
        src = self.meta.get("sources", {})
        modified = {
            "TGV": src.get("tgv", {}).get("modified"),
            "TER": src.get("ter", {}).get("modified"),
            "IC": src.get("intercites", {}).get("modified"),
        }
        # Pour le TER : régions d'exploitation des trains TER du profil.
        codes = sorted({j.extra.get("region_code") for j in journeys if j.legs[0].family == "TER"} - {None})
        regions = [(c, REGION_NAMES.get(c)) for c in codes]
        return reliability_blocks(
            regularity=self.regularity, reg_map=self.reg_map, families_pairs=pairs,
            regions=regions, today=today, dataset_modified=modified,
        )

    def profile(
        self,
        from_id: str,
        to_id: str,
        day_type: str = "weekday",
        bin_minutes: int = 60,
        arrive_by_s: int = 9 * 3600,
        leave_after_s: int = 18 * 3600,
        include_buses: bool = False,
        threshold: float = 0.5,
        today: dt.date | None = None,
    ) -> dict:
        if day_type not in DAY_TYPE_LABELS:
            raise BadRequest(f"day_type doit valoir {', '.join(DAY_TYPE_LABELS)}")
        origin, dest = self.resolve(from_id), self.resolve(to_id)
        if set(origin.stop_area_ids) & set(dest.stop_area_ids):
            raise BadRequest("Les gares de départ et d'arrivée doivent être différentes.")
        today = today or dt.date.today()

        out_j, out_occ, out_stats = self.direction(origin, dest, day_type, include_buses, threshold)
        in_j, in_occ, in_stats = self.direction(dest, origin, day_type, include_buses, threshold)
        common = {"bin_minutes": bin_minutes, "arrive_by_s": arrive_by_s, "leave_after_s": leave_after_s}

        return {
            "from": vars(origin) | {"regions": None},
            "to": vars(dest) | {"regions": None},
            "day_type": day_type,
            "day_type_label": DAY_TYPE_LABELS[day_type],
            "outbound": direction_profile(out_j, is_outbound=True, **common)
            | {"trains": self._train_rows(out_j), "occasional_trains": self._train_rows(out_occ),
               "daily_counts": out_stats,
               "reliability": self._reliability(out_j, today)},
            "inbound": direction_profile(in_j, is_outbound=False, **common)
            | {"trains": self._train_rows(in_j), "occasional_trains": self._train_rows(in_occ),
               "daily_counts": in_stats,
               "reliability": self._reliability(in_j, today)},
            "meta": self.public_meta() | {
                "sample_dates": [d.isoformat() for d in self.samples.get(day_type, [])],
                "presence_threshold": threshold,
                "include_buses": include_buses,
            },
            "cost": None,  # réservé : tarifs et abonnements (hors V1)
        }

    # ------------------------------------------------------------------ desserte directe
    def _reach(self, stops: list[str], direction: str, dates: list[dt.date], include_buses: bool) -> pd.DataFrame:
        """Trains reliant directement `stops` à toute autre gare : une ligne par (gare reliée, train).

        Comme `select_direct_legs`, mais par gare reliée : si le trip dessert plusieurs gares de
        `stops`, on garde la dernière montée (départs) ou la première descente (arrivées). Comme
        `typical_day`, chaque train garde son horaire le plus fréquent et son nombre de dates.
        Tout est agrégé dans PostgreSQL : un grand nœud (Paris) représente des millions de lignes
        (circulation × gare × date) qu'il ne faut pas charger en mémoire.
        """
        mine, other = ("o", "d") if direction == "outbound" else ("d", "o")
        board = "o.seq DESC" if direction == "outbound" else "d.seq"
        sql = f"""
            WITH legs AS (
                SELECT o.trip_id, {other}.stop_area_id AS stop, o.dep_s, d.arr_s,
                       row_number() OVER (PARTITION BY o.trip_id, {other}.stop_area_id ORDER BY {board}) AS rk
                FROM stop_times o
                JOIN stop_times d ON o.trip_id = d.trip_id AND o.seq < d.seq
                WHERE {mine}.stop_area_id = ANY(%(s)s) AND {other}.stop_area_id <> ALL(%(s)s)
                  AND coalesce(o.pickup_type, 0) != 1 AND coalesce(d.drop_off_type, 0) != 1
            ),
            occ AS (
                SELECT sd.date, l.stop, t.train_number, l.dep_s, l.arr_s, t.family,
                       row_number() OVER (PARTITION BY sd.date, l.stop, t.train_number ORDER BY l.dep_s) AS r
                FROM legs l
                JOIN trips t ON t.trip_id = l.trip_id
                JOIN service_dates sd ON sd.service_id = t.service_id
                WHERE l.rk = 1 AND sd.date = ANY(%(dates)s) AND (%(buses)s OR NOT coalesce(t.is_bus, false))
            ),
            variants AS (
                SELECT stop, train_number, dep_s, arr_s, min(family) AS family,
                       count(*) AS c, min(date) AS first_date
                FROM occ WHERE r = 1
                GROUP BY stop, train_number, dep_s, arr_s
            )
            SELECT stop, train_number, dep_s, arr_s, family, n_days FROM (
                SELECT *, (sum(c) OVER (PARTITION BY stop, train_number))::int AS n_days,
                       row_number() OVER (PARTITION BY stop, train_number ORDER BY c DESC, first_date) AS v
                FROM variants
            ) AS ranked WHERE v = 1
        """
        return self._df(sql, {"s": stops, "dates": dates, "buses": include_buses})

    def _connections(
        self,
        place_id: str,
        day_type: str = "weekday",
        direction: str = "outbound",
        include_buses: bool = False,
        threshold: float = 0.5,
    ) -> dict:
        """Gares reliées sans changement à `place_id`, avec leur nombre de trains du jour type."""
        if day_type not in DAY_TYPE_LABELS:
            raise BadRequest(f"day_type doit valoir {', '.join(DAY_TYPE_LABELS)}")
        if direction not in ("outbound", "inbound"):
            raise BadRequest("direction doit valoir outbound ou inbound")
        place = self.resolve(place_id)
        dates = self.samples.get(day_type, [])
        trains = self._reach(place.stop_area_ids, direction, dates, include_buses) if dates else pd.DataFrame()
        counts = connection_counts(trains, len(dates), threshold)

        stations = []
        for r in counts.itertuples(index=False):
            stop_id = r.stop
            s = self.station_by_id.get(stop_id)
            if s is None or s["lat"] is None or s["lon"] is None:
                continue
            stations.append({
                "id": stop_id,
                "name": s["name"], "city": s["city_name"], "lat": s["lat"], "lon": s["lon"],
                "trains": int(r.trains), "occasional": int(r.occasional),
                "min_duration_min": int(r.min_duration_min), "families": list(r.families),
            })
        stations.sort(key=lambda s: (-s["trains"], -s["occasional"], s["name"]))

        if place.kind == "city":
            g = self.groups[self.groups["city_group_id"] == place.id].iloc[0]
            lat, lon = g["lat"], g["lon"]
        else:
            s = self.station_by_id[place.id]
            lat, lon = s["lat"], s["lon"]
        return {
            "place": {"id": place.id, "kind": place.kind, "name": place.name, "lat": lat, "lon": lon,
                      "stop_area_ids": place.stop_area_ids},
            "day_type": day_type,
            "day_type_label": DAY_TYPE_LABELS[day_type],
            "direction": direction,
            "n_dates": len(dates),
            "presence_threshold": threshold,
            "include_buses": include_buses,
            "stations": stations,
        }

    def public_meta(self) -> dict:
        src = self.meta.get("sources", {})
        return {
            "feed_start": self.meta.get("feed_start"),
            "feed_end": self.meta.get("feed_end"),
            "feed_version": self.meta.get("feed_version"),
            "built_at": self.meta.get("built_at"),
            "samples": self.meta.get("samples"),
            "regularity_last_month": self.meta.get("regularity_last_month"),
            "sources": {
                k: {kk: v.get(kk) for kk in ("title", "url", "page", "modified", "last_modified", "license", "downloaded_at")}
                for k, v in src.items()
            },
        }

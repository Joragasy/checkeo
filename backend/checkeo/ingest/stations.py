"""Référentiel des gares : StopArea GTFS ↔ code UIC ↔ commune (INSEE) ↔ groupe ville ↔ région.

Le GTFS SNCF ne relie pas entre elles les gares d'une même ville (Lille Flandres et Lille
Europe sont deux StopArea indépendantes). On les regroupe donc par commune, grâce au code
INSEE du jeu « Gares de voyageurs » joint par code UIC.
"""

from __future__ import annotations

import re

import pandas as pd

UIC_IN_STOP_AREA = re.compile(r"OCE(\d{8})$")

REGION_NAMES = {
    "11": "Île-de-France", "24": "Centre-Val de Loire", "27": "Bourgogne-Franche-Comté",
    "28": "Normandie", "32": "Hauts-de-France", "44": "Grand Est", "52": "Pays de la Loire",
    "53": "Bretagne", "75": "Nouvelle-Aquitaine", "76": "Occitanie", "84": "Auvergne-Rhône-Alpes",
    "93": "Provence-Alpes-Côte d'Azur", "94": "Corse",
}


def city_insee(insee: str | None) -> str | None:
    """Ramène les arrondissements de Paris, Lyon et Marseille à leur commune."""
    if not isinstance(insee, str) or not insee:
        return None
    if insee.startswith("751") and insee != "75056":
        return "75056"
    if insee.startswith("6938"):
        return "69123"
    if insee.startswith("132") and len(insee) == 5 and 13201 <= int(insee) <= 13216:
        return "13055"
    return insee


def uic_of(stop_area_id: str) -> str | None:
    m = UIC_IN_STOP_AREA.search(stop_area_id)
    return m.group(1) if m else None


def build_stations(
    stops: pd.DataFrame,
    stop_times: pd.DataFrame,
    trips: pd.DataFrame,
    gares: pd.DataFrame,
    communes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retourne (stations, city_groups).

    `gares` : colonnes codes_uic, codeinsee (jeu SNCF « Gares de voyageurs »).
    `communes` : colonnes code, nom, codeRegion (API Découpage administratif).
    """
    # Zones d'arrêt réellement desservies, avec les modes et familles qui s'y arrêtent.
    served = stop_times[["trip_id", "stop_area_id"]].drop_duplicates().merge(
        trips[["trip_id", "mode", "family", "is_bus"]], on="trip_id"
    )
    agg = served.groupby("stop_area_id").agg(
        modes=("mode", lambda s: sorted(set(s))),
        families=("family", lambda s: sorted(set(s))),
        train_served=("is_bus", lambda s: bool((~s.astype(bool)).any())),
    ).reset_index()

    areas = stops[stops["stop_id"].isin(agg["stop_area_id"])][["stop_id", "stop_name", "stop_lat", "stop_lon"]]
    areas = areas.rename(columns={"stop_id": "stop_area_id", "stop_name": "name"})
    st = agg.merge(areas, on="stop_area_id", how="left")
    st["name"] = st["name"].fillna(st["stop_area_id"])
    st["lat"] = pd.to_numeric(st["stop_lat"], errors="coerce")
    st["lon"] = pd.to_numeric(st["stop_lon"], errors="coerce")
    st["uic"] = st["stop_area_id"].map(uic_of)

    # UIC → INSEE (un enregistrement peut porter plusieurs codes UIC séparés par « ; »).
    g = gares[["codes_uic", "codeinsee"]].dropna().copy()
    g["uic"] = g["codes_uic"].astype(str).str.split(r"[;,\s]+")
    g = g.explode("uic")
    g = g[g["uic"].str.fullmatch(r"\d{8}")].drop_duplicates("uic")
    st = st.merge(g[["uic", "codeinsee"]], on="uic", how="left")
    st["insee"] = st["codeinsee"].astype(object).where(st["codeinsee"].notna(), None)
    st["city_insee"] = st["insee"].map(city_insee)

    com = communes.rename(columns={"code": "city_insee", "nom": "city_name", "codeRegion": "region_code"})
    st = st.merge(com[["city_insee", "city_name", "region_code"]], on="city_insee", how="left")
    st["region_name"] = st["region_code"].map(REGION_NAMES)

    # Groupes ville : seulement les communes ayant au moins deux gares desservies par le train.
    trains = st[st["train_served"] & st["city_insee"].notna()]
    sizes = trains.groupby("city_insee").size()
    multi = set(sizes[sizes >= 2].index)
    st["city_group_id"] = st["city_insee"].map(lambda c: f"city:{c}" if c in multi else None)

    groups = (
        st[st["city_group_id"].notna() & st["train_served"]]
        .groupby(["city_group_id", "city_name", "region_code", "region_name"], dropna=False)
        .agg(
            stop_area_ids=("stop_area_id", lambda s: sorted(s)),
            modes=("modes", lambda s: sorted({m for ms in s for m in ms})),
            lat=("lat", "mean"),
            lon=("lon", "mean"),
        )
        .reset_index()
    )
    # Une commune non trouvée dans le référentiel garde un groupe nommé d'après sa première gare.
    groups["city_name"] = groups["city_name"].fillna(groups["stop_area_ids"].map(lambda ids: ids[0]))

    stations = st[[
        "stop_area_id", "uic", "name", "lat", "lon", "insee", "city_insee", "city_name",
        "city_group_id", "region_code", "region_name", "modes", "families", "train_served",
    ]].sort_values("name").reset_index(drop=True)
    return stations, groups

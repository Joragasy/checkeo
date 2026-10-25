"""Normalisation des jeux de régularité mensuelle (TGV par liaison, TER par région, Intercités
par ligne) en une table unique, et rapprochement des libellés de gares avec le GTFS."""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import pandas as pd

CAUSE_COLUMNS = {
    "prct_cause_externe": "cause_externe",
    "prct_cause_infra": "cause_infra",
    "prct_cause_gestion_trafic": "cause_gestion_trafic",
    "prct_cause_materiel_roulant": "cause_materiel_roulant",
    "prct_cause_gestion_gare": "cause_gestion_gare",
    "prct_cause_prise_en_charge_voyageurs": "cause_prise_en_charge_voyageurs",
}

# Libellés « région » du jeu TER → code région INSEE. Les sous-périmètres (« Etoile Amiens »,
# « Loire Océan », « Sud Azur ») et les anciennes régions d'avant 2016 ne sont pas rattachés.
TER_REGION_CODES = {
    "AUVERGNE RHONE ALPES": "84",
    "BOURGOGNE FRANCHE COMTE": "27",
    "BRETAGNE": "53",
    "CENTRE VAL DE LOIRE": "24",
    "GRAND EST": "44",
    "HAUTS DE FRANCE": "32",
    "NORMANDIE": "28",
    "NOUVELLE AQUITAINE": "75",
    "OCCITANIE": "76",
    "PAYS DE LA LOIRE": "52",
    "PROVENCE ALPES COTE D AZUR": "93",
}

COLUMNS = [
    "family", "scope", "label_from", "label_to", "region_label", "region_code", "month",
    "planned", "cancelled", "circulated", "late", "rate",
    "late_15", "late_30", "late_60", "avg_delay_late_arr",
    *CAUSE_COLUMNS.values(), "comment",
]


def norm(text: str | None) -> str:
    """Normalise un libellé de gare : majuscules, sans accents ni ponctuation, ST → SAINT."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().upper()
    t = re.sub(r"[^A-Z0-9]+", " ", t)
    t = re.sub(r"\bSTE\b", "SAINTE", t)
    t = re.sub(r"\bST\b", "SAINT", t)
    return re.sub(r"\s+", " ", t).strip()


def _month(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series.astype(str).str[:7], format="%Y-%m").dt.date


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df:
        return pd.Series([None] * len(df), index=df.index, dtype="float")
    return pd.to_numeric(df[col], errors="coerce")


def normalize_tgv(df: pd.DataFrame) -> pd.DataFrame:
    planned = _num(df, "nb_train_prevu")
    cancelled = _num(df, "nb_annulation")
    circulated = planned - cancelled.fillna(0)
    late = _num(df, "nb_train_retard_arrivee")
    out = pd.DataFrame({
        "family": "TGV",
        "scope": "liaison",
        "label_from": df["gare_depart"].astype(str).str.strip(),
        "label_to": df["gare_arrivee"].astype(str).str.strip(),
        "region_label": None,
        "region_code": None,
        "month": _month(df["date"]),
        "planned": planned,
        "cancelled": cancelled,
        "circulated": circulated,
        "late": late,
        # Le jeu TGV ne fournit pas de taux : on le calcule sur les trains ayant circulé.
        "rate": (100 * (1 - late / circulated)).where(circulated > 0),
        "late_15": _num(df, "nb_train_retard_sup_15"),
        "late_30": _num(df, "nb_train_retard_sup_30"),
        "late_60": _num(df, "nb_train_retard_sup_60"),
        "avg_delay_late_arr": _num(df, "retard_moyen_arrivee"),
        "comment": df.get("commentaires_retard_arrivee"),
    })
    for src, dst in CAUSE_COLUMNS.items():
        out[dst] = _num(df, src)
    return out[COLUMNS]


def _normalize_counts(df: pd.DataFrame, family: str, scope: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "family": family,
        "scope": scope,
        "month": _month(df["date"]),
        "planned": _num(df, "nombre_de_trains_programmes"),
        "cancelled": _num(df, "nombre_de_trains_annules"),
        "circulated": _num(df, "nombre_de_trains_ayant_circule"),
        "late": _num(df, "nombre_de_trains_en_retard_a_l_arrivee"),
        "rate": _num(df, "taux_de_regularite"),
        "late_15": None, "late_30": None, "late_60": None, "avg_delay_late_arr": None,
        "comment": df.get("commentaires"),
    }, index=df.index)
    for dst in CAUSE_COLUMNS.values():
        out[dst] = None
    return out


def normalize_ter(df: pd.DataFrame) -> pd.DataFrame:
    out = _normalize_counts(df, "TER", "region")
    out["label_from"] = None
    out["label_to"] = None
    out["region_label"] = df["region"].astype(str).str.strip()
    out["region_code"] = out["region_label"].map(lambda r: TER_REGION_CODES.get(norm(r)))
    return out[COLUMNS]


def normalize_intercites(df: pd.DataFrame) -> pd.DataFrame:
    out = _normalize_counts(df, "IC", "liaison")
    out["label_from"] = df["depart"].astype(str).str.strip()
    out["label_to"] = df["arrivee"].astype(str).str.strip()
    out["region_label"] = None
    out["region_code"] = None
    return out[COLUMNS]


def build_regularity(tgv: pd.DataFrame, ter: pd.DataFrame, ic: pd.DataFrame) -> pd.DataFrame:
    frames = [normalize_tgv(tgv), normalize_ter(ter), normalize_intercites(ic)]
    reg = pd.concat([f for f in frames if len(f)], ignore_index=True)
    # Lignes sans aucun compteur (ex. région ayant refusé la publication) : inutilisables.
    reg = reg[reg["circulated"].notna() | reg["rate"].notna()]
    return reg.sort_values(["family", "label_from", "label_to", "region_label", "month"]).reset_index(drop=True)


# --------------------------------------------------------------------------------------------
# Rapprochement libellés de régularité → zones d'arrêt GTFS
# --------------------------------------------------------------------------------------------

def load_overrides(path: Path | None) -> dict[str, list[str]]:
    """Surcharges manuelles : libellé normalisé → liste de codes UIC (8 chiffres) ou INSEE (5)."""
    if path is None or not path.exists():
        return {}
    out: dict[str, list[str]] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(line for line in f if not line.lstrip().startswith("#")):
            codes = [c.strip() for c in row["codes"].split(";") if c.strip()]
            out[norm(row["label"])] = codes
    return out


def match_label(label: str, stations: pd.DataFrame, overrides: dict[str, list[str]]) -> tuple[list[str], str]:
    """Zones d'arrêt désignées par un libellé de régularité, et la méthode utilisée.

    Ordre : surcharge manuelle, nom de gare exact, nom de commune exact (toutes ses gares),
    puis inclusion des mots du libellé dans un nom de gare si elle est unique.
    Un libellé composé (« ALBI/RODEZ ») désigne l'union de ses parties.
    """
    trains = stations[stations["train_served"]]
    ids: list[str] = []
    methods: list[str] = []
    for part in str(label).split("/"):
        key = norm(part)
        if not key:
            continue
        if key in overrides:
            codes = overrides[key]
            sel = trains[trains["uic"].isin(codes) | trains["city_insee"].isin(codes)]
            ids += list(sel["stop_area_id"])
            methods.append("surcharge")
            continue
        exact = trains[trains["name_norm"] == key]
        if len(exact):
            ids += list(exact["stop_area_id"])
            methods.append("gare")
            continue
        city = trains[trains["city_norm"] == key]
        if len(city):
            ids += list(city["stop_area_id"])
            methods.append("commune")
            continue
        tokens = set(key.split())
        sub = trains[trains["name_tokens"].map(lambda t: tokens <= t)]
        if len(sub) == 1:
            ids += list(sub["stop_area_id"])
            methods.append("mots")
            continue
        methods.append("introuvable")
    return sorted(set(ids)), "+".join(methods)


def build_regularity_map(
    regularity: pd.DataFrame, stations: pd.DataFrame, overrides: dict[str, list[str]]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retourne (regularity_map, rapport) : une ligne par (famille, libellé, zone d'arrêt)
    et un rapport listant chaque libellé avec la méthode de rapprochement."""
    st = stations.copy()
    st["name_norm"] = st["name"].map(norm)
    st["city_norm"] = st["city_name"].map(norm)
    st["name_tokens"] = st["name_norm"].map(lambda s: set(s.split()))

    liaisons = regularity[regularity["scope"] == "liaison"]
    labels = pd.concat([
        liaisons[["family", "label_from"]].rename(columns={"label_from": "label"}),
        liaisons[["family", "label_to"]].rename(columns={"label_to": "label"}),
    ]).drop_duplicates()

    rows, report = [], []
    for fam, label in labels.itertuples(index=False):
        ids, method = match_label(label, st, overrides)
        report.append({"family": fam, "label": label, "method": method, "n_stops": len(ids)})
        rows += [{"family": fam, "label": label, "stop_area_id": i} for i in ids]
    return (
        pd.DataFrame(rows, columns=["family", "label", "stop_area_id"]),
        pd.DataFrame(report).sort_values(["family", "label"]).reset_index(drop=True),
    )

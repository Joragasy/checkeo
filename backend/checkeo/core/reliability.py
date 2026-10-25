"""Fiabilité d'une liaison à partir des données de régularité mensuelle publiées.

Principe : ne jamais extrapoler. Une série n'est affichée que si elle correspond exactement
à la liaison (TGV, Intercités : mêmes gares de départ et d'arrivée, même sens) ou, pour le
TER, si elle est explicitement présentée comme une moyenne régionale. Sinon : indisponible.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable

import pandas as pd

FAMILY_LABELS = {"TGV": "TGV", "IC": "Intercités", "TER": "TER"}
CAUSES = {
    "cause_externe": "Causes externes (météo, obstacles, malveillance…)",
    "cause_infra": "Infrastructure (voies, signalisation, travaux)",
    "cause_gestion_trafic": "Gestion du trafic",
    "cause_materiel_roulant": "Matériel roulant",
    "cause_gestion_gare": "Gestion en gare et réutilisation de matériel",
    "cause_prise_en_charge_voyageurs": "Prise en charge des voyageurs (affluence, PSH, correspondances)",
}
STALE_AFTER_MONTHS = 3


def months_between(a: dt.date, b: dt.date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def matching_liaisons(
    regularity: pd.DataFrame,
    reg_map: pd.DataFrame,
    family: str,
    od_pairs: Iterable[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Couples de libellés (départ, arrivée) dont les gares couvrent au moins un couple
    (gare de montée, gare de descente) réellement utilisé par les trains de cette famille."""
    pairs = set(od_pairs)
    if not pairs:
        return []
    fam_map = reg_map[reg_map["family"] == family]
    stops_of = fam_map.groupby("label")["stop_area_id"].agg(set).to_dict()
    rows = regularity[(regularity["family"] == family) & (regularity["scope"] == "liaison")]
    out = []
    for lf, lt in rows[["label_from", "label_to"]].drop_duplicates().itertuples(index=False):
        sf, sd = stops_of.get(lf, set()), stops_of.get(lt, set())
        if any(o in sf and d in sd for o, d in pairs):
            out.append((lf, lt))
    return sorted(out)


def summarize(series: pd.DataFrame, today: dt.date, window: int = 12, history: int = 36) -> dict:
    """Moyenne sur les `window` derniers mois disponibles, courbe mensuelle et causes."""
    s = series.assign(month=pd.to_datetime(series["month"])).sort_values("month")
    last = s["month"].max()
    first_in_window = last - pd.DateOffset(months=window - 1)
    w = s[s["month"] >= first_in_window]

    circ, late = w["circulated"].sum(min_count=1), w["late"].sum(min_count=1)
    if pd.notna(circ) and pd.notna(late) and circ > 0:
        avg = 100 * (1 - late / circ)
    else:
        avg = w["rate"].mean()
    planned, cancelled = w["planned"].sum(min_count=1), w["cancelled"].sum(min_count=1)
    cancel = 100 * cancelled / planned if pd.notna(planned) and pd.notna(cancelled) and planned > 0 else None

    causes = None
    cause_cols = [c for c in CAUSES if c in w and w[c].notna().any()]
    if cause_cols and w["late"].notna().any():
        weights = w["late"].fillna(0)
        total = weights[w[cause_cols].notna().any(axis=1)].sum()
        if total > 0:
            causes = sorted(
                (
                    {"key": c, "label": CAUSES[c], "percent": round(float((w[c].fillna(0) * weights).sum() / total), 1)}
                    for c in cause_cols
                ),
                key=lambda x: -x["percent"],
            )

    hist_start = last - pd.DateOffset(months=history - 1)
    monthly = [
        {
            "month": r.month.strftime("%Y-%m"),
            "rate": None if pd.isna(r.rate) else round(float(r.rate), 1),
            "cancel_rate": round(100 * r.cancelled / r.planned, 1)
            if pd.notna(r.cancelled) and pd.notna(r.planned) and r.planned > 0 else None,
            "planned": None if pd.isna(r.planned) else int(r.planned),
        }
        for r in s[s["month"] >= hist_start].itertuples(index=False)
    ]
    lag = months_between(last.date(), today)
    return {
        "window": {"from": w["month"].min().strftime("%Y-%m"), "to": last.strftime("%Y-%m"), "months": int(len(w))},
        "punctuality": None if pd.isna(avg) else round(float(avg), 1),
        "cancel_rate": None if cancel is None else round(float(cancel), 2),
        "trains_planned": None if pd.isna(planned) else int(planned),
        "causes": causes,
        "monthly": monthly,
        "last_month": last.strftime("%Y-%m"),
        "stale": lag > STALE_AFTER_MONTHS,
        "lag_months": lag,
    }


def reliability_blocks(
    *,
    regularity: pd.DataFrame,
    reg_map: pd.DataFrame,
    families_pairs: dict[str, set[tuple[str, str]]],
    regions: list[tuple[str, str]],
    today: dt.date,
    dataset_modified: dict[str, str | None],
) -> list[dict]:
    """Un bloc de fiabilité par famille de trains présente dans le profil.

    `families_pairs` : famille → couples (gare de montée, gare de descente) utilisés.
    `regions` : (code, nom) des régions de la gare d'origine et de destination (pour le TER).
    """
    blocks: list[dict] = []
    for family in ("TGV", "IC", "TER"):
        if family not in families_pairs:
            continue
        base = {"family": family, "family_label": FAMILY_LABELS[family],
                "dataset_modified": dataset_modified.get(family)}
        if family in ("TGV", "IC"):
            matches = matching_liaisons(regularity, reg_map, family, families_pairs[family])
            if not matches:
                blocks.append(base | {
                    "scope": "liaison", "label": None, "available": False,
                    "note": "Donnée indisponible : cette liaison ne fait pas partie des liaisons "
                            "suivies dans le jeu de régularité publié.",
                })
            for lf, lt in matches:
                sub = regularity[(regularity["family"] == family) & (regularity["label_from"] == lf)
                                 & (regularity["label_to"] == lt)]
                blocks.append(base | {
                    "scope": "liaison", "label": f"{lf} → {lt}", "available": True,
                    "note": "Régularité de la liaison, mesurée au terminus du train." if family == "IC"
                            else "Régularité de la liaison (seuils composites 5/10/15 min selon la durée).",
                } | summarize(sub, today))
        else:
            seen = False
            for code, name in dict.fromkeys(regions):
                sub = regularity[(regularity["family"] == "TER") & (regularity["region_code"] == code)]
                if code is None or sub.empty:
                    continue
                seen = True
                blocks.append(base | {
                    "scope": "region", "label": name, "available": True,
                    "note": f"Moyenne de tous les TER de la région {name}, non spécifique à cette "
                            "ligne (les données TER ne sont pas publiées par ligne).",
                } | summarize(sub, today))
            if not seen:
                blocks.append(base | {
                    "scope": "region", "label": None, "available": False,
                    "note": "Donnée indisponible : aucune série TER régionale publiée pour ces gares.",
                })
    return blocks

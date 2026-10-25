"""Jour type : échantillonnage de dates réelles puis agrégation des trains observés.

Plutôt que de choisir une date arbitraire, on regarde plusieurs dates réelles du même type
(ex. tous les lundis-vendredis des 4 prochaines semaines hors jours fériés). Un train fait
partie du jour type s'il circule sur au moins `threshold` (50 % par défaut) de ces dates :
c'est le « mode » de présence. Sa fréquence observée est conservée pour l'affichage.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable

import pandas as pd

DAY_TYPES = ("weekday", "saturday", "sunday")
DAY_TYPE_LABELS = {"weekday": "Jour de semaine (lun.-ven.)", "saturday": "Samedi", "sunday": "Dimanche"}


def day_type_of(day: dt.date) -> str:
    wd = day.weekday()
    return "weekday" if wd < 5 else ("saturday" if wd == 5 else "sunday")


def sample_dates(
    start: dt.date,
    weeks: int,
    feed_start: dt.date,
    feed_end: dt.date,
    holidays: Iterable[dt.date] = (),
) -> dict[str, list[dt.date]]:
    """Dates échantillonnées par jour type, sur `weeks` semaines à partir de `start`.

    La fenêtre est bornée par la période de validité du GTFS ; les jours fériés sont exclus.
    """
    hol = set(holidays)
    first = max(start, feed_start)
    last = min(first + dt.timedelta(days=7 * weeks - 1), feed_end)
    out: dict[str, list[dt.date]] = {t: [] for t in DAY_TYPES}
    day = first
    while day <= last:
        if day not in hol:
            out[day_type_of(day)].append(day)
        day += dt.timedelta(days=1)
    return out


WEEKDAY_SHORT = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]


def typical_day(
    occurrences: pd.DataFrame,
    id_columns: list[str],
    time_columns: list[str],
    dates: list[dt.date],
    threshold: float = 0.5,
    dep_column: str = "dep_s",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Agrège les circulations observées sur plusieurs dates.

    `occurrences` : une ligne par (date, circulation) avec `date`, `id_columns` (identité d'un
    train, ex. son numéro) et `time_columns` (ce qui peut varier d'un jour à l'autre : gares de
    montée/descente, horaires).

    Un même train peut voir ses horaires décalés de quelques minutes d'une semaine à l'autre
    (travaux), voire partir d'une autre gare de la même ville : on le reconnaît par son
    identité et on retient sa variante la plus fréquente (à égalité, celle de la date la plus
    proche). Retourne :
    - `regular` : trains présents sur au moins `threshold` des dates (le jour type) ;
    - `occasional` : trains présents moins souvent (ex. renforts du vendredi) ;
    - des statistiques sur le nombre de trains par date (médiane, min, max).
    Chaque train porte `n_days`, `frequency`, `weekdays` (jours où il circule) et
    `dep_min_s`/`dep_max_s` (amplitude de son horaire de départ si celui-ci varie).
    """
    out_cols = [*id_columns, *time_columns, "n_days", "frequency", "weekdays", "dep_min_s", "dep_max_s"]
    n = len(dates)
    occ = occurrences[occurrences["date"].isin(set(dates))] if len(occurrences) else occurrences
    if n == 0 or occ.empty:
        per_date = {d.isoformat(): 0 for d in dates}
        stats = {"n_dates": n, "median": 0.0 if n else None, "min": 0 if n else None,
                 "max": 0 if n else None, "per_date": per_date}
        empty = pd.DataFrame(columns=out_cols)
        return empty, empty.copy(), stats

    occ = occ.drop_duplicates(subset=["date", *id_columns])

    # Nombre de circulations distinctes par date : deux numéros couplés sur le même horaire
    # ne comptent qu'une fois.
    per_date = occ.drop_duplicates(["date", *time_columns]).groupby("date").size().reindex(dates, fill_value=0)
    stats = {
        "n_dates": n,
        "median": float(per_date.median()),
        "min": int(per_date.min()),
        "max": int(per_date.max()),
        "per_date": {d.isoformat(): int(c) for d, c in per_date.items()},
    }

    # Horaire représentatif : le plus fréquent, puis le plus proche dans le temps.
    times = (
        occ.groupby([*id_columns, *time_columns], dropna=False)
        .agg(times_count=("date", "size"), first_date=("date", "min"))
        .reset_index()
        .sort_values(["times_count", "first_date"], ascending=[False, True])
        .drop_duplicates(id_columns)
        .drop(columns=["times_count", "first_date"])
    )
    agg = occ.groupby(id_columns, dropna=False).agg(
        n_days=("date", "nunique"),
        dep_min_s=(dep_column, "min"),
        dep_max_s=(dep_column, "max"),
        weekdays=("date", lambda ds: sorted({d.weekday() for d in ds})),
    ).reset_index()
    trains = times.merge(agg, on=id_columns)
    trains["frequency"] = trains["n_days"] / n
    trains["weekdays"] = trains["weekdays"].map(lambda wds: [WEEKDAY_SHORT[w] for w in wds])
    regular_mask = trains["n_days"] >= threshold * n - 1e-9
    regular = trains[regular_mask][out_cols].reset_index(drop=True)
    occasional = trains[~regular_mask][out_cols].reset_index(drop=True)
    return regular, occasional, stats

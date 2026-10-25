"""Jours de circulation des services GTFS : calendar.txt + calendar_dates.txt.

Règles GTFS :
- calendar.txt définit une plage [start_date, end_date] et des jours de semaine actifs ;
- calendar_dates.txt ajoute (exception_type=1) ou supprime (exception_type=2) des dates précises ;
- l'un ou l'autre fichier peut être absent (le GTFS SNCF n'a que calendar_dates.txt).
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

WEEKDAY_COLUMNS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _to_date(value: str) -> dt.date:
    return dt.datetime.strptime(str(value), "%Y%m%d").date()


def expand_service_dates(
    calendar: pd.DataFrame | None,
    calendar_dates: pd.DataFrame | None,
) -> pd.DataFrame:
    """Liste exhaustive des couples (service_id, date) où le service circule.

    Retourne un DataFrame trié avec les colonnes service_id (str) et date (datetime.date).
    """
    active: set[tuple[str, dt.date]] = set()

    if calendar is not None and len(calendar):
        for row in calendar.itertuples(index=False):
            start, end = _to_date(row.start_date), _to_date(row.end_date)
            flags = [str(getattr(row, c)).strip() == "1" for c in WEEKDAY_COLUMNS]
            if not any(flags):
                continue
            day = start
            while day <= end:
                if flags[day.weekday()]:
                    active.add((str(row.service_id), day))
                day += dt.timedelta(days=1)

    if calendar_dates is not None and len(calendar_dates):
        for row in calendar_dates.itertuples(index=False):
            key = (str(row.service_id), _to_date(row.date))
            exc = str(row.exception_type).strip()
            if exc == "1":
                active.add(key)
            elif exc == "2":
                active.discard(key)

    df = pd.DataFrame(sorted(active), columns=["service_id", "date"])
    return df


def active_services(service_dates: pd.DataFrame, day: dt.date) -> set[str]:
    """Services qui circulent le jour donné."""
    return set(service_dates.loc[service_dates["date"] == day, "service_id"])

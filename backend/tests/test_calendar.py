import datetime as dt

import pandas as pd

from checkeo.core.calendar import active_services, expand_service_dates
from checkeo.ingest.gtfs_load import read_gtfs

from .conftest import MINI_GTFS

D = dt.date


def cal(rows):
    cols = ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "start_date", "end_date"]
    return pd.DataFrame(rows, columns=cols, dtype=str)


def cdates(rows):
    return pd.DataFrame(rows, columns=["service_id", "date", "exception_type"], dtype=str)


def test_calendar_only_weekdays_within_range():
    sd = expand_service_dates(cal([["S", 1, 1, 1, 1, 1, 0, 0, "20300304", "20300310"]]), None)
    assert sorted(sd["date"]) == [D(2030, 3, d) for d in range(4, 9)]  # lun. 4 → ven. 8


def test_calendar_dates_only():
    """Cas du GTFS SNCF : pas de calendar.txt, uniquement des ajouts."""
    sd = expand_service_dates(None, cdates([["S", "20300309", "1"], ["S", "20300310", "1"]]))
    assert active_services(sd, D(2030, 3, 9)) == {"S"}
    assert active_services(sd, D(2030, 3, 11)) == set()


def test_exception_removes_and_adds():
    sd = expand_service_dates(
        cal([["S", 1, 1, 1, 1, 1, 0, 0, "20300304", "20300310"]]),
        cdates([["S", "20300306", "2"], ["S", "20300309", "1"]]),
    )
    days = set(sd["date"])
    assert D(2030, 3, 6) not in days  # mercredi supprimé
    assert D(2030, 3, 9) in days  # samedi ajouté
    assert D(2030, 3, 5) in days


def test_removal_outside_calendar_is_harmless():
    sd = expand_service_dates(cal([["S", 0, 0, 0, 0, 0, 1, 0, "20300301", "20300331"]]),
                              cdates([["S", "20300304", "2"]]))
    assert D(2030, 3, 4) not in set(sd["date"])
    assert len(sd) == 5  # 5 samedis en mars 2030


def test_mini_gtfs_services():
    t = read_gtfs(MINI_GTFS)
    sd = expand_service_dates(t["calendar"], t["calendar_dates"])
    assert active_services(sd, D(2030, 3, 5)) == {"WK", "ALL"}  # mardi
    assert active_services(sd, D(2030, 3, 6)) == {"ALL"}  # mercredi : WK supprimé
    assert active_services(sd, D(2030, 3, 8)) == {"WK", "ALL", "FRI"}  # vendredi
    assert active_services(sd, D(2030, 3, 9)) == {"ALL", "EXTRA"}  # samedi : ajout ponctuel

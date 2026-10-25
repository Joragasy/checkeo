import datetime as dt

import pandas as pd

from checkeo.core.daytype import day_type_of, sample_dates, typical_day

D = dt.date


def test_day_type_of():
    assert day_type_of(D(2030, 3, 4)) == "weekday"
    assert day_type_of(D(2030, 3, 9)) == "saturday"
    assert day_type_of(D(2030, 3, 10)) == "sunday"


def test_sample_dates_excludes_holidays_and_clips_to_feed():
    s = sample_dates(D(2030, 3, 4), 2, D(2030, 3, 1), D(2030, 3, 31), holidays=[D(2030, 3, 6)])
    assert len(s["weekday"]) == 9 and D(2030, 3, 6) not in s["weekday"]
    assert s["saturday"] == [D(2030, 3, 9), D(2030, 3, 16)]
    clipped = sample_dates(D(2030, 3, 25), 4, D(2030, 3, 1), D(2030, 3, 31))
    assert max(clipped["weekday"]) == D(2030, 3, 29)
    early = sample_dates(D(2030, 1, 1), 1, D(2030, 3, 4), D(2030, 3, 31))
    assert min(early["weekday"]) == D(2030, 3, 4)  # démarre au début de validité du GTFS


def occ(rows):
    return pd.DataFrame(rows, columns=["date", "train_number", "dep_s", "arr_s"])


DATES = [D(2030, 3, d) for d in (4, 5, 6, 7)]


def test_presence_threshold_and_stats():
    rows = [(d, "A", 100, 200) for d in DATES]  # 4/4
    rows += [(d, "B", 300, 400) for d in DATES[:2]]  # 2/4 → retenu (seuil 50 %)
    rows += [(DATES[0], "C", 500, 600)]  # 1/4 → occasionnel
    regular, occasional, stats = typical_day(occ(rows), ["train_number"], ["dep_s", "arr_s"], DATES)
    assert sorted(regular["train_number"]) == ["A", "B"]
    assert occasional["train_number"].tolist() == ["C"]
    assert stats["per_date"] == {"2030-03-04": 3, "2030-03-05": 2, "2030-03-06": 1, "2030-03-07": 1}
    assert stats["median"] == 1.5 and stats["min"] == 1 and stats["max"] == 3


def test_modal_times_when_schedule_shifts():
    rows = [(DATES[0], "A", 100, 200), (DATES[1], "A", 100, 200), (DATES[2], "A", 160, 260), (DATES[3], "A", 100, 200)]
    regular, _, _ = typical_day(occ(rows), ["train_number"], ["dep_s", "arr_s"], DATES)
    r = regular.iloc[0]
    assert (r["dep_s"], r["arr_s"], r["n_days"]) == (100, 200, 4)
    assert (r["dep_min_s"], r["dep_max_s"]) == (100, 160)


def test_dates_outside_sample_are_ignored_and_empty_input():
    rows = [(D(2030, 4, 1), "X", 100, 200)]
    regular, occasional, stats = typical_day(occ(rows), ["train_number"], ["dep_s", "arr_s"], DATES)
    assert regular.empty and occasional.empty and stats["median"] == 0.0
    _, _, none = typical_day(occ([]), ["train_number"], ["dep_s", "arr_s"], [])
    assert none["median"] is None

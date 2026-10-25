import pytest

from checkeo.core.indicators import (
    arrive_by, count_in_window, direction_profile, durations, histogram, largest_gap, leave_after,
)
from checkeo.core.trips import Journey, Leg

H = 3600


def j(dep_h: float, arr_h: float, n="1") -> Journey:
    return Journey(legs=(Leg(n, "TGV INOUI", "TGV", "O", "D", int(dep_h * H), int(arr_h * H)),))


JS = [j(6 + 40 / 60, 7.75, "a"), j(7, 8, "b"), j(9, 10, "c"), j(23.5, 24 + 40 / 60, "d")]


def test_histogram_hourly_and_half_hourly():
    h = histogram(JS, 60)
    assert len(h) == 24 and sum(b["count"] for b in h) == 4
    assert [h[i]["count"] for i in (6, 7, 9, 23)] == [1, 1, 1, 1]
    h30 = histogram(JS, 30)
    assert len(h30) == 48 and h30[13]["count"] == 1  # 06:40 → tranche 06:30-07:00


def test_histogram_folds_after_midnight_departures():
    h = histogram([j(24 + 10 / 60, 25)], 60)
    assert h[0]["count"] == 1


def test_histogram_rejects_bad_bin():
    with pytest.raises(ValueError):
        histogram(JS, 7)


def test_arrive_by():
    r = arrive_by(JS, 9 * H)
    assert r["count"] == 2
    assert r["first"]["train_numbers"] == ["a"]  # premier train du matin
    assert r["last"]["train_numbers"] == ["b"]  # dernier qui arrive avant 9h
    assert arrive_by(JS, 6 * H) == {"target_s": 6 * H, "count": 0, "first": None, "last": None}


def test_arrive_by_ignores_next_day_arrivals():
    assert arrive_by([j(23.5, 24.5)], 9 * H)["count"] == 0


def test_leave_after():
    js = [j(17.5, 18.5, "x"), j(18.5, 19.5, "y"), j(20, 21, "z")]
    r = leave_after(js, 18 * H)
    assert r["count"] == 2 and r["first"]["train_numbers"] == ["y"] and r["last"]["train_numbers"] == ["z"]


def test_largest_gap():
    g = largest_gap(JS)
    assert (g["from"], g["to"], g["minutes"]) == ("09:00", "21:00", 720)
    empty = largest_gap([])
    assert empty["minutes"] == 15 * 60 and empty["trains_in_window"] == 0
    single = largest_gap([j(12, 13)])
    assert single["minutes"] == 9 * 60 and single["from"] == "12:00"


def test_count_in_window_bounds_inclusive():
    assert count_in_window(JS, 7 * H, 9 * H, by="arr")["count"] == 2  # 07:45 et 08:00
    assert count_in_window([j(19, 20)], 17 * H, 20 * H, by="dep")["count"] == 1
    assert count_in_window([j(20, 21)], 17 * H, 20 * H, by="dep")["count"] == 1


def test_durations():
    assert durations(JS) == {"min": 60, "median": 62, "max": 70}
    assert durations([]) == {"min": None, "median": None, "max": None}


def test_direction_profile_keys():
    out = direction_profile(JS, is_outbound=True, bin_minutes=60, arrive_by_s=9 * H, leave_after_s=18 * H)
    assert "arrive_by" in out and "leave_after" not in out and out["peak"]["by"] == "arr"
    # Arrivées 07:45, 08:00, 10:00 et 00:40 (+1, ramenée dans la tranche 0h).
    assert out["histogram_by"] == "arr" and [out["histogram"][i]["count"] for i in (0, 7, 8, 10)] == [1, 1, 1, 1]
    back = direction_profile(JS, is_outbound=False, bin_minutes=60, arrive_by_s=9 * H, leave_after_s=18 * H)
    assert "leave_after" in back and back["peak"]["window"] == [17 * H, 20 * H]
    assert back["histogram_by"] == "dep"

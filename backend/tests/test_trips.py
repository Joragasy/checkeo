import pandas as pd

from checkeo.core.trips import merge_coupled, select_direct_legs
from checkeo.ingest.gtfs_load import normalize, read_gtfs

from .conftest import A1, A2, B1, B2, MINI_GTFS


def cand(rows):
    cols = ["trip_id", "o_stop", "o_seq", "dep_s", "o_pickup", "d_stop", "d_seq", "arr_s", "d_dropoff"]
    return pd.DataFrame(rows, columns=cols)


def test_origin_must_precede_destination():
    legs = select_direct_legs(cand([["T", "O", 3, 100, 0, "D", 1, 50, 0]]))
    assert legs.empty


def test_pickup_and_dropoff_rules():
    legs = select_direct_legs(cand([
        ["NOPICK", "O", 1, 100, 1, "D", 2, 200, 0],
        ["NODROP", "O", 1, 100, 0, "D", 2, 200, 1],
        ["OK", "O", 1, 100, 0, "D", 2, 200, 0],
    ]))
    assert list(legs["trip_id"]) == ["OK"]


def test_last_boarding_first_alighting_in_same_city():
    legs = select_direct_legs(cand([
        ["T", "O1", 1, 100, 0, "D1", 3, 300, 0],
        ["T", "O1", 1, 100, 0, "D2", 4, 400, 0],
        ["T", "O2", 2, 150, 0, "D1", 3, 300, 0],
        ["T", "O2", 2, 150, 0, "D2", 4, 400, 0],
    ]))
    assert legs.iloc[0][["o_stop", "d_stop", "dep_s", "arr_s"]].tolist() == ["O2", "D1", 150, 300]


def test_merge_coupled():
    t = pd.DataFrame({
        "train_number": ["1511", "1011", "2000"],
        "o_stop": ["O", "O", "O"], "d_stop": ["D", "D", "D"],
        "dep_s": [100, 100, 500], "arr_s": [200, 200, 600], "n_days": [5, 5, 5],
    })
    m = merge_coupled(t).sort_values("dep_s")
    assert m["train_numbers"].tolist() == [["1011", "1511"], ["2000"]]


def test_normalize_mini_gtfs():
    g = normalize(read_gtfs(MINI_GTFS))
    st = g["stop_times"]
    # Les StopPoint sont rattachés à leur StopArea.
    assert set(st["stop_area_id"]) >= {A1, A2, B1, B2}
    # Horaire au-delà de minuit conservé tel quel (24:40 = 88800 s).
    t4 = st[(st["trip_id"] == "T4") & (st["stop_area_id"] == B2)].iloc[0]
    assert t4["arr_s"] == 24 * 3600 + 40 * 60
    trips = g["trips"].set_index("trip_id")
    assert trips.loc["T1", "mode"] == "TGV INOUI" and trips.loc["T1", "family"] == "TGV"
    assert trips.loc["T4", "mode"] == "Train TER" and trips.loc["T4", "family"] == "TER"
    assert bool(trips.loc["T7", "is_bus"]) and not bool(trips.loc["T1", "is_bus"])
    assert trips.loc["T1", "train_number"] == "1001"

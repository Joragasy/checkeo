import pandas as pd

from checkeo.core.connections import connection_counts

H = 3600


def trains(rows):
    return pd.DataFrame(rows, columns=["stop", "train_number", "dep_s", "arr_s", "family", "n_days"])


def test_counts_regular_occasional_and_coupled():
    t = trains([
        ("B", "1", 7 * H, 8 * H, "TGV", 4),
        # Deux numéros couplés : une seule circulation.
        ("B", "2", 9 * H, 10 * H, "TGV", 4),
        ("B", "3", 9 * H, 10 * H, "TGV", 4),
        ("B", "4", 12 * H, 12 * H + 1800, "TER", 1),  # 1 date sur 4 : occasionnel
        ("C", "9", 7 * H, 7 * H + 1200, "TER", 2),  # 2 dates sur 4 : régulier
    ])
    c = connection_counts(t, 4, 0.5).set_index("stop")
    assert c.loc["B", "trains"] == 2 and c.loc["B", "occasional"] == 1
    assert c.loc["B", "min_duration_min"] == 60  # les trains occasionnels ne comptent pas
    assert c.loc["B", "families"] == ["TER", "TGV"]
    assert c.loc["C", "trains"] == 1 and c.loc["C", "min_duration_min"] == 20


def test_only_occasional_and_empty():
    c = connection_counts(trains([("B", "4", 12 * H, 12 * H + 1800, "TER", 1)]), 4, 0.5)
    assert c.iloc[0]["trains"] == 0 and c.iloc[0]["min_duration_min"] == 30
    assert connection_counts(trains([]), 4).empty
    assert connection_counts(trains([]), 0).empty

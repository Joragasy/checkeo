"""Desserte directe d'une gare : nombre de trains du jour type vers (ou depuis) chaque gare reliée.

Même règle que le profil (voir `daytype.typical_day`) : un train compte s'il circule sur au
moins `threshold` des dates échantillonnées. Le calcul porte sur toutes les gares reliées à la
fois ; l'agrégation par date est faite en amont dans la base (voir `Checkeo._reach`), pour ne
pas charger en mémoire une ligne par date et par circulation.
"""

from __future__ import annotations

import pandas as pd

COLUMNS = ["trains", "occasional", "min_duration_min", "families"]


def connection_counts(trains: pd.DataFrame, n_dates: int, threshold: float = 0.5, key: str = "stop") -> pd.DataFrame:
    """Agrège par gare reliée (`key`) les trains observés.

    `trains` : une ligne par (gare reliée, numéro de train) avec `key`, `train_number`, `dep_s`,
    `arr_s` (son horaire le plus fréquent), `family` et `n_days` (dates où il circule).
    Retourne une ligne par gare avec :
    - `trains` : trains réguliers du jour type, deux numéros couplés comptant une seule fois ;
    - `occasional` : trains présents moins souvent ;
    - `min_duration_min` : trajet le plus rapide (parmi les trains réguliers s'il y en a) ;
    - `families` : familles (TGV, TER…) des trains de la liaison.
    """
    if n_dates == 0 or trains.empty:
        return pd.DataFrame(columns=[key, *COLUMNS])

    t = trains.copy()
    t["regular"] = t["n_days"] >= threshold * n_dates - 1e-9
    # Trains couplés : même gare, mêmes horaires → une seule circulation (la plus fréquente).
    t = t.sort_values("n_days", ascending=False).drop_duplicates([key, "dep_s", "arr_s"])
    t["duration_min"] = ((t["arr_s"] - t["dep_s"]) / 60).round()

    out = t.groupby(key).agg(
        trains=("regular", "sum"),
        occasional=("regular", lambda s: int((~s).sum())),
        min_any=("duration_min", "min"),
        families=("family", lambda s: sorted(set(s))),
    )
    min_regular = t[t["regular"]].groupby(key)["duration_min"].min()
    out["min_duration_min"] = min_regular.reindex(out.index).fillna(out["min_any"]).astype(int)
    out["trains"] = out["trains"].astype(int)
    return out.reset_index()[[key, *COLUMNS]]

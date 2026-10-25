"""Trajets directs entre deux ensembles de gares.

Un trajet est représenté par un `Journey` composé de `Leg`. En V1 il n'y a qu'un seul leg
(trajet direct) ; un futur calcul avec correspondances produira des Journey à plusieurs legs
sans changer les indicateurs, qui ne regardent que le départ, l'arrivée et la durée.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class Leg:
    train_number: str
    mode: str
    family: str  # TGV / TER / IC / AUTRE : sert à rattacher les données de régularité
    from_stop: str
    to_stop: str
    dep_s: int
    arr_s: int


@dataclass(frozen=True)
class Journey:
    legs: tuple[Leg, ...]
    n_days: int = 0
    frequency: float = 1.0
    extra: dict = field(default_factory=dict, compare=False, hash=False)

    @property
    def dep_s(self) -> int:
        return self.legs[0].dep_s

    @property
    def arr_s(self) -> int:
        return self.legs[-1].arr_s

    @property
    def duration_s(self) -> int:
        return self.arr_s - self.dep_s


def select_direct_legs(candidates: pd.DataFrame) -> pd.DataFrame:
    """Garde, pour chaque trip, le meilleur couple (montée, descente) valide.

    `candidates` : une ligne par couple (arrêt d'origine, arrêt de destination) d'un même trip,
    colonnes trip_id, o_stop, o_seq, dep_s, o_pickup, d_stop, d_seq, arr_s, d_dropoff.

    Règles :
    - l'origine doit précéder la destination dans le trip (o_seq < d_seq) ;
    - on doit pouvoir monter à l'origine (pickup_type != 1) et descendre à destination
      (drop_off_type != 1) ;
    - si le trip dessert plusieurs gares de la ville d'origine (ou de destination), on garde la
      dernière montée possible et la première descente possible (trajet le plus court).
    """
    cols = ["trip_id", "o_stop", "o_seq", "dep_s", "d_stop", "d_seq", "arr_s"]
    if candidates.empty:
        return pd.DataFrame(columns=cols)
    c = candidates
    c = c[(c["o_seq"] < c["d_seq"]) & (c["o_pickup"] != 1) & (c["d_dropoff"] != 1)]
    if c.empty:
        return pd.DataFrame(columns=cols)
    # Dernière montée possible : plus grand o_seq ; puis première descente après celle-ci.
    last_board = c.groupby("trip_id")["o_seq"].transform("max")
    c = c[c["o_seq"] == last_board]
    first_alight = c.groupby("trip_id")["d_seq"].transform("min")
    c = c[c["d_seq"] == first_alight]
    return c[cols].drop_duplicates("trip_id").reset_index(drop=True)


def merge_coupled(trains: pd.DataFrame) -> pd.DataFrame:
    """Fusionne les trains couplés : plusieurs numéros sur le même parcours aux mêmes horaires
    (ex. deux TGV en unité multiple) ne forment qu'une seule circulation pour le voyageur."""
    if trains.empty:
        return trains.assign(train_numbers=[[] for _ in range(len(trains))])
    phys = ["o_stop", "d_stop", "dep_s", "arr_s"]
    t = trains.sort_values("train_number")
    numbers = t.groupby(phys)["train_number"].agg(list).rename("train_numbers")
    first = t.sort_values("n_days", ascending=False).drop_duplicates(phys).set_index(phys)
    return first.join(numbers).reset_index()

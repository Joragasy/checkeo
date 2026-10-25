"""Indicateurs du « profil navetteur » calculés sur les trajets d'un jour type, pour un sens."""

from __future__ import annotations

from statistics import median

from .gtfs_time import DAY, format_display
from .trips import Journey

H = 3600


def histogram(journeys: list[Journey], bin_minutes: int = 60, by: str = "dep") -> list[dict]:
    """Nombre de trains par tranche horaire sur 24 h.

    Les horaires >= 24:00 sont ramenés sur le cycle de 24 h du jour type (un train à 24:25
    compte dans la tranche 00:00).
    """
    if bin_minutes <= 0 or (24 * 60) % bin_minutes:
        raise ValueError("Le pas doit diviser 24 h (ex. 15, 30, 60, 120)")
    size = bin_minutes * 60
    counts = [0] * (DAY // size)
    for j in journeys:
        t = (j.dep_s if by == "dep" else j.arr_s) % DAY
        counts[t // size] += 1
    return [{"start_s": i * size, "end_s": (i + 1) * size, "count": c} for i, c in enumerate(counts)]


def _brief(j: Journey | None) -> dict | None:
    if j is None:
        return None
    return {
        "dep_s": j.dep_s,
        "arr_s": j.arr_s,
        "dep": format_display(j.dep_s),
        "arr": format_display(j.arr_s),
        "duration_min": round(j.duration_s / 60),
        "train_numbers": [leg.train_number for leg in j.legs],
    }


def arrive_by(journeys: list[Journey], target_s: int) -> dict:
    """Trains arrivant au plus tard à l'heure cible (ex. 9h) : le premier de la journée,
    le dernier qui permet encore d'arriver à l'heure, et leur nombre."""
    ok = sorted((j for j in journeys if j.arr_s <= target_s), key=lambda j: (j.arr_s, j.dep_s))
    return {
        "target_s": target_s,
        "count": len(ok),
        "first": _brief(ok[0]) if ok else None,
        "last": _brief(max(ok, key=lambda j: (j.dep_s, j.arr_s))) if ok else None,
    }


def leave_after(journeys: list[Journey], target_s: int) -> dict:
    """Trains partant à partir de l'heure cible (ex. 18h) : le premier, le dernier de la
    journée, et leur nombre."""
    ok = sorted((j for j in journeys if j.dep_s >= target_s), key=lambda j: (j.dep_s, j.arr_s))
    return {
        "target_s": target_s,
        "count": len(ok),
        "first": _brief(ok[0]) if ok else None,
        "last": _brief(ok[-1]) if ok else None,
    }


def largest_gap(journeys: list[Journey], start_s: int = 6 * H, end_s: int = 21 * H) -> dict:
    """Plus long intervalle sans départ dans la plage [start_s, end_s].

    Les bornes de la plage comptent comme des points : sans aucun train, l'intervalle est la
    plage entière ; avec un seul train à 12h, c'est max(12h-6h, 21h-12h).
    """
    deps = sorted({j.dep_s for j in journeys if start_s <= j.dep_s <= end_s})
    points = [start_s, *deps, end_s]
    best = (0, start_s, start_s)
    for a, b in zip(points, points[1:]):
        if b - a > best[0]:
            best = (b - a, a, b)
    gap, a, b = best
    return {
        "window": [start_s, end_s],
        "minutes": gap // 60,
        "from_s": a,
        "to_s": b,
        "from": format_display(a),
        "to": format_display(b),
        "trains_in_window": len(deps),
    }


def count_in_window(journeys: list[Journey], start_s: int, end_s: int, by: str) -> dict:
    """Nombre de trains dont le départ (by="dep") ou l'arrivée (by="arr") est dans [start, end]."""
    n = sum(1 for j in journeys if start_s <= (j.dep_s if by == "dep" else j.arr_s) <= end_s)
    return {"window": [start_s, end_s], "by": by, "count": n}


def durations(journeys: list[Journey]) -> dict:
    if not journeys:
        return {"min": None, "median": None, "max": None}
    mins = [j.duration_s / 60 for j in journeys]
    return {"min": round(min(mins)), "median": round(median(mins)), "max": round(max(mins))}


def direction_profile(
    journeys: list[Journey],
    *,
    is_outbound: bool,
    bin_minutes: int,
    arrive_by_s: int,
    leave_after_s: int,
) -> dict:
    """Assemble les indicateurs d'un sens.

    Aller : on s'intéresse à l'arrivée (histogramme par heure d'arrivée, heure cible d'arrivée,
    pointe 7h-9h à l'arrivée). Retour : au départ (histogramme par heure de départ, heure cible
    de départ, pointe 17h-20h au départ).
    """
    js = sorted(journeys, key=lambda j: (j.dep_s, j.arr_s))
    by = "arr" if is_outbound else "dep"
    out = {
        "count": len(js),
        "histogram": histogram(js, bin_minutes, by=by),
        "histogram_by": by,
        "largest_gap": largest_gap(js),
        "durations": durations(js),
    }
    if is_outbound:
        out["arrive_by"] = arrive_by(js, arrive_by_s)
        out["peak"] = count_in_window(js, 7 * H, 9 * H, by="arr")
    else:
        out["leave_after"] = leave_after(js, leave_after_s)
        out["peak"] = count_in_window(js, 17 * H, 20 * H, by="dep")
    return out

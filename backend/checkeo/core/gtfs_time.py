"""Horaires GTFS : "HH:MM:SS" relatifs au jour de service, pouvant dépasser 24:00:00."""

DAY = 86_400


def parse_gtfs_time(value: str | None) -> int | None:
    """Convertit "25:10:00" en secondes depuis minuit du jour de service (ici 90600).

    Les heures ne sont pas plafonnées à 24 : un train qui part à 23:50 et arrive à 00:20
    est noté 24:20:00 dans le GTFS et reste rattaché au jour de service de son départ.
    """
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError(f"Horaire GTFS invalide : {value!r}")
    h, m, s = (int(p) for p in parts)
    if not (0 <= m < 60 and 0 <= s < 60 and h >= 0):
        raise ValueError(f"Horaire GTFS invalide : {value!r}")
    return h * 3600 + m * 60 + s


def parse_hhmm(value: str) -> int:
    """"09:00" ou "9h30" → secondes. Utilisé pour les paramètres de l'API."""
    v = value.strip().lower().replace("h", ":")
    if v.endswith(":"):
        v += "00"
    h, _, m = v.partition(":")
    h_i, m_i = int(h), int(m or 0)
    if not (0 <= h_i <= 47 and 0 <= m_i < 60):
        raise ValueError(f"Heure invalide : {value!r}")
    return h_i * 3600 + m_i * 60


def day_offset(seconds: int) -> int:
    """Nombre de jours après le jour de service (0 avant 24:00, 1 de 24:00 à 47:59…)."""
    return seconds // DAY


def format_hhmm(seconds: int) -> str:
    """Heure civile "HH:MM", ramenée sur 24 h (24:25:00 → "00:25")."""
    s = seconds % DAY
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}"


def format_display(seconds: int) -> str:
    """Heure civile avec marqueur de lendemain : 24:25:00 → "00:25 (+1)"."""
    off = day_offset(seconds)
    return format_hhmm(seconds) + (f" (+{off})" if off else "")

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("CHECKEO_DATA_DIR", ROOT / "data"))

# Base PostgreSQL : DSN (postgresql://utilisateur:motdepasse@hôte:5432/base) et schéma des tables.
DATABASE_URL = os.environ.get("CHECKEO_DATABASE_URL","postgres.default.service.nomad")
PG_SCHEMA = os.environ.get("CHECKEO_PG_SCHEMA", "checkeo")


def check_dsn(dsn: str | None) -> str:
    """Refuse un DSN incomplet (ex. un simple nom d'hôte) avec un message clair."""
    if not dsn:
        raise ValueError("Aucune base : définissez CHECKEO_DATABASE_URL (postgresql://utilisateur:motdepasse@hôte:5432/base).")
    if "://" not in dsn and "=" not in dsn:
        raise ValueError(
            f"CHECKEO_DATABASE_URL invalide ({dsn!r}) : attendu postgresql://utilisateur:motdepasse@hôte:5432/base."
        )
    return dsn

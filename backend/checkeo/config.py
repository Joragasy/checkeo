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

# Connexion Google : identifiant client OAuth (type « Application Web ») et sessions.
GOOGLE_CLIENT_ID = os.environ.get("CHECKEO_GOOGLE_CLIENT_ID", "813966544536-ggcjidn6vgm9okm93t3kgmul662r5ohc.apps.googleusercontent.com")
# Schéma des comptes : distinct de PG_SCHEMA, que l'ingestion supprime et remplace.
AUTH_SCHEMA = os.environ.get("CHECKEO_AUTH_SCHEMA", "checkeo_auth")
# Cookie de session réservé à HTTPS ; mettre 0 en développement local (http://localhost).
COOKIE_SECURE = os.environ.get("CHECKEO_COOKIE_SECURE", "1") != "0"
SESSION_DAYS = int(os.environ.get("CHECKEO_SESSION_DAYS", "30"))
CHECKEO_COOKIE_SECURE = os.environ.get("CHECKEO_COOKIE_SECURE", "0")

"""Comptes et sessions : connexion avec Google (jeton d'identité vérifié côté serveur).

La première connexion crée le compte (inscription) ; les suivantes le mettent à jour.
Seule l'empreinte SHA-256 du jeton de session est stockée en base.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets
from typing import Any

from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import check_dsn


class InvalidCredential(Exception):
    pass


def verify_google_credential(credential: str, client_id: str) -> dict[str, Any]:
    """Vérifie un jeton d'identité Google (signature, audience, émetteur, expiration)."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    if not client_id:
        raise InvalidCredential("Connexion Google non configurée (CHECKEO_GOOGLE_CLIENT_ID).")
    try:
        claims = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id)
    except ValueError as e:
        raise InvalidCredential("Jeton Google invalide.") from e
    if not claims.get("email_verified"):
        raise InvalidCredential("Adresse e-mail Google non vérifiée.")
    return claims


def _hash(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


USER_COLUMNS = "u.id, u.email, u.name, u.picture"


class AuthStore:
    def __init__(self, dsn: str, schema: str = "checkeo_auth", session_days: int = 30):
        check_dsn(dsn)
        self.schema = schema
        self.session_days = session_days
        self.pool = ConnectionPool(
            dsn, min_size=1, max_size=2,
            kwargs={"options": f"-c search_path={schema}", "autocommit": True, "row_factory": dict_row},
            open=True,
        )
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self.pool.connection() as con:
            con.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(self.schema)))
            con.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id bigserial PRIMARY KEY,
                    google_sub text NOT NULL UNIQUE,
                    email text NOT NULL,
                    name text,
                    picture text,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    last_login_at timestamptz NOT NULL DEFAULT now()
                )""")
            con.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash bytea PRIMARY KEY,
                    user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    expires_at timestamptz NOT NULL
                )""")

    def upsert_user(self, claims: dict[str, Any]) -> dict[str, Any]:
        with self.pool.connection() as con:
            return con.execute(
                """INSERT INTO users AS u (google_sub, email, name, picture)
                   VALUES (%(sub)s, %(email)s, %(name)s, %(picture)s)
                   ON CONFLICT (google_sub) DO UPDATE
                   SET email = EXCLUDED.email, name = EXCLUDED.name, picture = EXCLUDED.picture,
                       last_login_at = now()
                   RETURNING """ + USER_COLUMNS,
                {"sub": claims["sub"], "email": claims["email"], "name": claims.get("name"),
                 "picture": claims.get("picture")},
            ).fetchone()

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        expires = dt.datetime.now(dt.UTC) + dt.timedelta(days=self.session_days)
        with self.pool.connection() as con:
            con.execute("DELETE FROM sessions WHERE expires_at < now()")
            con.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, %s)",
                        (_hash(token), user_id, expires))
        return token

    def user_for_token(self, token: str) -> dict[str, Any] | None:
        with self.pool.connection() as con:
            return con.execute(
                f"""SELECT {USER_COLUMNS} FROM sessions s JOIN users u ON u.id = s.user_id
                    WHERE s.token_hash = %s AND s.expires_at > now()""",
                (_hash(token),),
            ).fetchone()

    def delete_session(self, token: str) -> None:
        with self.pool.connection() as con:
            con.execute("DELETE FROM sessions WHERE token_hash = %s", (_hash(token),))

    def close(self) -> None:
        self.pool.close()

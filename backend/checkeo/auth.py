"""Comptes et sessions : connexion par e-mail et mot de passe, ou avec Google.

Google : le jeton d'identité est vérifié côté serveur ; la première connexion crée le compte, ou le
rattache au compte existant de même adresse (l'adresse Google est vérifiée).
Mot de passe : haché avec scrypt (sel aléatoire par compte).
Seule l'empreinte SHA-256 du jeton de session est stockée en base.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import secrets
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import check_dsn


class InvalidCredential(Exception):
    pass


class EmailTaken(Exception):
    pass


class InvalidInput(ValueError):
    pass


# ---------------------------------------------------------------- mots de passe
PASSWORD_MIN, PASSWORD_MAX = 8, 128
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def hash_password(password: str) -> str:
    """Empreinte scrypt au format scrypt$n$r$p$sel$empreinte (base64)."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, dklen=32, **_SCRYPT)
    return f"scrypt${_SCRYPT['n']}${_SCRYPT['r']}${_SCRYPT['p']}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, digest = stored.split("$")
        if algo != "scrypt":
            return False
        expected = base64.b64decode(digest)
        got = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p),
                             dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got, expected)


# Empreinte factice : un e-mail inconnu coûte autant qu'un mauvais mot de passe.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def normalize_email(email: str) -> str:
    email = email.strip().lower()
    local, _, domain = email.partition("@")
    if not local or "." not in domain or len(email) > 254 or any(c.isspace() for c in email):
        raise InvalidInput("Adresse e-mail invalide.")
    return email


def check_password(password: str) -> str:
    if not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        raise InvalidInput(f"Le mot de passe doit contenir entre {PASSWORD_MIN} et {PASSWORD_MAX} caractères.")
    return password


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
            # Comptes par mot de passe (google_sub nul) ; une seule adresse par compte.
            con.execute("ALTER TABLE users ALTER COLUMN google_sub DROP NOT NULL")
            con.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash text")
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower ON users (lower(email))")

    def upsert_user(self, claims: dict[str, Any]) -> dict[str, Any]:
        """Connexion Google : compte du même sub, sinon de la même adresse (rattaché), sinon nouveau."""
        params = {"sub": claims["sub"], "email": normalize_email(claims["email"]),
                  "name": claims.get("name"), "picture": claims.get("picture")}
        with self.pool.connection() as con, con.transaction():
            row = con.execute(
                """SELECT id FROM users WHERE google_sub = %(sub)s
                   UNION ALL
                   SELECT id FROM users WHERE google_sub IS NULL AND lower(email) = %(email)s
                   LIMIT 1""",
                params,
            ).fetchone()
            if row is None:
                return con.execute(
                    """INSERT INTO users AS u (google_sub, email, name, picture)
                       VALUES (%(sub)s, %(email)s, %(name)s, %(picture)s)
                       RETURNING """ + USER_COLUMNS,
                    params,
                ).fetchone()
            return con.execute(
                """UPDATE users AS u
                   SET google_sub = %(sub)s, email = %(email)s, name = coalesce(%(name)s, u.name),
                       picture = %(picture)s, last_login_at = now()
                   WHERE id = %(id)s
                   RETURNING """ + USER_COLUMNS,
                {**params, "id": row["id"]},
            ).fetchone()

    def create_password_user(self, email: str, password: str, name: str | None = None) -> dict[str, Any]:
        """Inscription par e-mail ; EmailTaken si l'adresse a déjà un compte."""
        email = normalize_email(email)
        password_hash = hash_password(check_password(password))
        name = (name or "").strip()[:120] or None
        try:
            with self.pool.connection() as con:
                return con.execute(
                    "INSERT INTO users AS u (email, name, password_hash) VALUES (%s, %s, %s) RETURNING "
                    + USER_COLUMNS,
                    (email, name, password_hash),
                ).fetchone()
        except psycopg.errors.UniqueViolation as e:
            raise EmailTaken("Un compte existe déjà avec cette adresse.") from e

    def authenticate_password(self, email: str, password: str) -> dict[str, Any]:
        """Connexion par e-mail ; InvalidCredential sans distinguer adresse inconnue et mauvais mot de passe."""
        try:
            email = normalize_email(email)
        except InvalidInput:
            email = ""
        with self.pool.connection() as con:
            row = con.execute(
                f"SELECT {USER_COLUMNS}, u.password_hash FROM users u WHERE lower(u.email) = %s", (email,)
            ).fetchone()
            stored = row["password_hash"] if row and row["password_hash"] else _DUMMY_HASH
            if not verify_password(password, stored) or row is None or not row["password_hash"]:
                raise InvalidCredential("E-mail ou mot de passe incorrect.")
            con.execute("UPDATE users SET last_login_at = now() WHERE id = %s", (row["id"],))
        del row["password_hash"]
        return row

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

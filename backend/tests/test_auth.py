import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from checkeo import auth
from checkeo.api.main import SESSION_COOKIE, create_app

from .conftest import ALPHA, PARIS

CLAIMS = {"sub": "g-123", "email": "ana@example.com", "email_verified": True, "name": "Ana", "picture": None}


@pytest.fixture
def client(db, tmp_path, monkeypatch):
    dsn, schema = db
    auth_schema = f"{schema}_authtest"

    def fake_verify(credential, client_id):
        if credential != "good":
            raise auth.InvalidCredential("Jeton Google invalide.")
        return CLAIMS

    monkeypatch.setattr(auth, "verify_google_credential", fake_verify)
    monkeypatch.setattr("checkeo.api.main.COOKIE_SECURE", False)  # TestClient parle en http
    app = create_app(dsn, schema, static_dir=tmp_path / "absent", auth_schema=auth_schema)
    with TestClient(app) as c:
        yield c
    with psycopg.connect(dsn, autocommit=True) as con:
        con.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(auth_schema)))


def test_data_routes_require_session(client):
    assert client.get("/api/stations", params={"q": "alph"}).status_code == 401
    assert client.get("/api/profile", params={"from": ALPHA, "to": PARIS}).status_code == 401
    assert client.get("/api/connections", params={"from": ALPHA}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/meta").status_code == 200


def test_sign_in_session_and_logout(client):
    r = client.post("/api/auth/google", json={"credential": "good"})
    assert r.status_code == 200
    user = r.json()
    assert user["email"] == "ana@example.com"
    assert SESSION_COOKIE in client.cookies

    assert client.get("/api/auth/me").json()["id"] == user["id"]
    assert client.get("/api/stations", params={"q": "alph"}).status_code == 200

    # Deuxième connexion : même compte.
    assert client.post("/api/auth/google", json={"credential": "good"}).json()["id"] == user["id"]

    token = client.cookies[SESSION_COOKIE]
    assert client.post("/api/auth/logout").status_code == 200
    client.cookies.set(SESSION_COOKIE, token)  # un jeton révoqué ne vaut plus rien
    assert client.get("/api/auth/me").status_code == 401


def test_invalid_credential(client):
    r = client.post("/api/auth/google", json={"credential": "bad"})
    assert r.status_code == 400
    assert SESSION_COOKIE not in client.cookies
    assert client.post("/api/auth/google", json={}).status_code == 422

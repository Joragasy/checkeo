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


def test_password_hash_roundtrip():
    h = auth.hash_password("correct horse")
    assert h.startswith("scrypt$")
    assert auth.verify_password("correct horse", h)
    assert not auth.verify_password("wrong horse", h)
    assert not auth.verify_password("x", "garbage")


def test_signup_login_logout(client):
    r = client.post("/api/auth/signup", json={"email": " Bob@Example.com ", "password": "s3cret-pass", "name": "Bob"})
    assert r.status_code == 201
    user = r.json()
    assert user["email"] == "bob@example.com"
    assert "password_hash" not in user
    assert client.get("/api/auth/me").json()["id"] == user["id"]

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401

    r = client.post("/api/auth/login", json={"email": "BOB@example.com", "password": "s3cret-pass"})
    assert r.status_code == 200
    assert r.json()["id"] == user["id"]
    assert client.get("/api/stations", params={"q": "alph"}).status_code == 200


def test_signup_rejects_duplicates_and_bad_input(client):
    assert client.post("/api/auth/signup", json={"email": "bob@example.com", "password": "s3cret-pass"}).status_code == 201
    r = client.post("/api/auth/signup", json={"email": "BOB@example.com", "password": "another-pass"})
    assert r.status_code == 409
    assert client.post("/api/auth/signup", json={"email": "eve@example.com", "password": "short"}).status_code == 422
    assert client.post("/api/auth/signup", json={"email": "not-an-email", "password": "s3cret-pass"}).status_code == 422


def test_login_failures(client):
    client.post("/api/auth/signup", json={"email": "bob@example.com", "password": "s3cret-pass"})
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": "bob@example.com", "password": "wrong-pass"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "s3cret-pass"}).status_code == 401
    assert SESSION_COOKIE not in client.cookies
    # Un compte Google n'a pas de mot de passe.
    client.post("/api/auth/google", json={"credential": "good"})
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": "ana@example.com", "password": "anything1"}).status_code == 401


def test_google_links_password_account(client):
    pw_user = client.post("/api/auth/signup", json={"email": "Ana@example.com", "password": "s3cret-pass"}).json()
    client.post("/api/auth/logout")
    g_user = client.post("/api/auth/google", json={"credential": "good"}).json()
    assert g_user["id"] == pw_user["id"]
    assert g_user["name"] == "Ana"
    # Le mot de passe reste valable après le rattachement.
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": "ana@example.com", "password": "s3cret-pass"}).status_code == 200

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from checkeo.api.main import create_app, current_user

from .conftest import ALPHA, PARIS


@pytest.fixture(scope="module")
def client(db, tmp_path_factory):
    dsn, schema = db
    app = create_app(dsn, schema, static_dir=tmp_path_factory.mktemp("nostatic") / "absent",
                     auth_schema=f"{schema}_auth")
    app.dependency_overrides[current_user] = lambda: {"id": 0, "email": "test@example.com"}
    with TestClient(app) as c:
        yield c
    with psycopg.connect(dsn, autocommit=True) as con:
        con.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(f"{schema}_auth")))


def test_stations(client):
    r = client.get("/api/stations", params={"q": "alph"})
    assert r.status_code == 200
    assert r.json()["results"][0]["id"] == ALPHA
    assert client.get("/api/stations").status_code == 422


def test_profile(client):
    r = client.get("/api/profile", params={"from": ALPHA, "to": PARIS, "bin": 30, "arrive_by": "8h30"})
    assert r.status_code == 200
    body = r.json()
    assert body["day_type"] == "weekday"
    assert len(body["outbound"]["histogram"]) == 48
    assert body["outbound"]["arrive_by"]["target_s"] == 8 * 3600 + 30 * 60
    assert body["outbound"]["arrive_by"]["count"] == 2
    assert body["meta"]["feed_start"] == "2030-03-01"
    assert body["cost"] is None


@pytest.mark.parametrize("params,status", [
    ({"from": ALPHA, "to": PARIS, "bin": 7}, 422),
    ({"from": ALPHA, "to": PARIS, "arrive_by": "25h99"}, 422),
    ({"from": ALPHA, "to": PARIS, "day_type": "lundi"}, 422),
    ({"from": "city:00000", "to": PARIS}, 404),
    ({"from": ALPHA, "to": ALPHA}, 400),
])
def test_profile_errors(client, params, status):
    assert client.get("/api/profile", params=params).status_code == status


def test_meta(client):
    m = client.get("/api/meta").json()
    assert m["feed_end"] == "2030-03-31"
    assert m["regularity_last_month"]["TGV"] == "2030-01-01"


def test_connections(client):
    r = client.get("/api/connections", params={"from": ALPHA, "direction": "inbound"})
    assert r.status_code == 200
    body = r.json()
    assert body["direction"] == "inbound" and body["place"]["id"] == ALPHA
    assert {"id", "name", "lat", "lon", "trains", "occasional", "min_duration_min", "families"} <= set(body["stations"][0])
    assert client.get("/api/connections", params={"from": "city:00000"}).status_code == 404
    assert client.get("/api/connections", params={"from": ALPHA, "direction": "up"}).status_code == 422

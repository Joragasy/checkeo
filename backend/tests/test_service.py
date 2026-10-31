"""Chaîne complète sur le GTFS de test : ingestion → base DuckDB → profil."""

import pytest

from checkeo.service import BadRequest, NotFound

from .conftest import A1, A2, ALPHA, B1, B2, C, PARIS, TODAY, Z

H = 3600


def test_city_groups_and_arrondissements(app_service):
    groups = app_service.groups.set_index("city_group_id")
    assert set(groups.index) == {ALPHA, PARIS}
    assert groups.loc[PARIS, "city_name"] == "Paris"
    zeta = app_service.station_by_id[Z]
    assert zeta["city_group_id"] is None and zeta["insee"] is None


def test_search(app_service):
    res = app_service.search_stations("alpha")
    assert res[0]["id"] == ALPHA and res[0]["kind"] == "city"
    assert {r["name"] for r in res[1:]} == {"Alpha Nord", "Alpha Sud"}
    assert app_service.search_stations("beta est")[0]["id"] == B2
    assert app_service.search_stations("BÉTA")[0]["id"] in {B1, B2}
    assert app_service.search_stations("   ") == []


@pytest.fixture(scope="module")
def profile(app_service):
    return app_service.profile(ALPHA, PARIS, "weekday", today=TODAY)


def test_outbound_typical_weekday(profile):
    out = profile["outbound"]
    rows = [(t["train_number"], t["dep"], t["arr"], t["n_days"]) for t in out["trains"]]
    assert rows == [
        ("1003", "06:40", "07:45", 9),  # monte à Alpha Nord (dernière gare d'Alpha desservie)
        ("1001", "07:00", "08:00", 9),
        ("1011/1511", "09:00", "10:00", 9),  # trains couplés fusionnés
        ("2001", "23:30", "00:40 (+1)", 9),  # arrivée après minuit
    ]
    # T5 (montée interdite à Alpha), T7 (car) et T3 (sens inverse) sont exclus ;
    # T6 (vendredi seulement) est un train occasionnel.
    assert [(t["train_number"], t["weekdays"]) for t in out["occasional_trains"]] == [("1007", ["ven."])]
    assert out["daily_counts"]["n_dates"] == 10
    assert out["daily_counts"]["per_date"]["2030-03-06"] == 0  # mercredi : service WK supprimé
    assert out["daily_counts"]["per_date"]["2030-03-08"] == 5
    assert out["arrive_by"]["count"] == 2 and out["arrive_by"]["last"]["dep"] == "07:00"
    assert out["peak"]["count"] == 2
    assert out["largest_gap"]["minutes"] == 720
    assert out["durations"] == {"min": 60, "median": 62, "max": 70}


def test_inbound(profile):
    back = profile["inbound"]
    assert [(t["train_number"], t["from_name"], t["to_name"]) for t in back["trains"]] == [
        ("1009", "Beta Centre", "Alpha Sud"),
        ("1005", "Beta Centre", "Alpha Nord"),
        ("1013", "Beta Est", "Alpha Nord"),
    ]
    assert back["leave_after"]["count"] == 2
    assert back["leave_after"]["last"]["dep"] == "20:00"
    assert back["peak"]["count"] == 3


def test_reliability_in_profile(profile):
    out = {b["family"]: b for b in profile["outbound"]["reliability"]}
    assert out["TGV"]["available"] and out["TGV"]["label"] == "ALPHA → BETA CENTRE"
    assert out["TGV"]["dataset_modified"] == "2030-02-02T10:00:00+00:00"
    assert out["TER"]["available"] and out["TER"]["label"] == "Hauts-de-France" and out["TER"]["stale"]
    back = {b["family"]: b for b in profile["inbound"]["reliability"]}
    assert not back["TGV"]["available"]  # aucune donnée publiée dans ce sens


def test_buses_option(app_service):
    p = app_service.profile(ALPHA, PARIS, include_buses=True, today=TODAY)
    assert "3001" in [t["train_number"] for t in p["outbound"]["trains"]]


def test_single_station_and_weekend(app_service):
    p = app_service.profile(A1, B1, "weekday", today=TODAY)
    assert [t["train_number"] for t in p["outbound"]["trains"]] == ["1003", "1001", "1011/1511"]
    sat = app_service.profile(ALPHA, PARIS, "saturday", today=TODAY)
    assert sat["outbound"]["count"] == 0 and sat["inbound"]["count"] == 2
    assert sat["meta"]["sample_dates"] == ["2030-03-09", "2030-03-16"]


def test_errors(app_service):
    with pytest.raises(NotFound):
        app_service.profile("city:00000", PARIS)
    with pytest.raises(BadRequest):
        app_service.profile(ALPHA, A1)
    with pytest.raises(BadRequest):
        app_service.profile(ALPHA, PARIS, "holiday")


def test_connections_outbound(app_service):
    res = app_service.connections(ALPHA, "weekday")
    by = {s["id"]: s for s in res["stations"]}
    assert res["place"]["kind"] == "city" and res["n_dates"] == 10
    assert A1 not in by and A2 not in by  # les gares de la ville choisie sont exclues
    # Mêmes trains que le profil Alpha → Paris : 1003, 1001, 1011/1511 vers Beta Centre, 2001 vers Beta Est.
    assert (by[B1]["trains"], by[B1]["occasional"], by[B1]["min_duration_min"]) == (3, 1, 60)
    assert by[B2]["trains"] == 1 and by[C]["trains"] == 1 and by[C]["min_duration_min"] == 20
    assert by[B1]["name"] == "Beta Centre" and by[B1]["lat"] == 48.8
    assert res["stations"][0]["id"] == B1
    with_buses = {s["id"]: s for s in app_service.connections(ALPHA, "weekday", include_buses=True)["stations"]}
    assert with_buses[B2]["trains"] == 2


def test_connections_inbound_and_errors(app_service):
    by = {s["id"]: s["trains"] for s in app_service.connections(ALPHA, "weekday", "inbound")["stations"]}
    # 1005 et 1009 depuis Beta Centre, 1013 depuis Beta Est, 2003 depuis Gamma (descente seule à Alpha Nord).
    assert by == {B1: 2, B2: 1, C: 1}
    sat = app_service.connections(A1, "saturday")["stations"]
    assert [(s["id"], s["trains"], s["occasional"]) for s in sat] == [(Z, 1, 0)]  # 2005 : 1 samedi sur 2
    with pytest.raises(NotFound):
        app_service.connections("city:00000")
    with pytest.raises(BadRequest):
        app_service.connections(ALPHA, "weekday", "sideways")

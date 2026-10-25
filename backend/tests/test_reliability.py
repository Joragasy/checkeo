import datetime as dt

import pytest

from checkeo.core.reliability import matching_liaisons, reliability_blocks, summarize
from checkeo.ingest.regularity import build_regularity, norm

from .conftest import A1, A2, B1, B2, TODAY, ic_df, ter_df, tgv_df


@pytest.fixture(scope="module")
def regularity():
    return build_regularity(tgv_df(), ter_df(), ic_df())


def test_norm():
    assert norm("Bordeaux St-Jean") == "BORDEAUX SAINT JEAN"
    assert norm("PARIS-NORD") == "PARIS NORD"
    assert norm("Nîmes") == "NIMES"


def test_tgv_rate_computed_and_old_regions_unmapped(regularity):
    tgv = regularity[regularity["family"] == "TGV"].iloc[-1]
    assert tgv["rate"] == pytest.approx(100 * (1 - 10 / 98))
    ter = regularity[regularity["family"] == "TER"]
    assert set(ter.loc[ter["region_label"] == "Hauts-de-France", "region_code"]) == {"32"}
    assert ter.loc[ter["region_label"] == "Nord Pas de Calais", "region_code"].isna().all()


def test_summarize_uses_last_12_months(regularity):
    sub = regularity[regularity["family"] == "TGV"]
    s = summarize(sub, TODAY)
    assert s["window"] == {"from": "2029-02", "to": "2030-01", "months": 12}
    # Le premier mois (50 retards) est hors fenêtre.
    assert s["punctuality"] == pytest.approx(round(100 * (1 - 120 / (98 * 12)), 1))
    assert s["cancel_rate"] == 2.0
    assert s["causes"][0]["key"] == "cause_externe" and s["causes"][0]["percent"] == 50.0
    assert not s["stale"] and s["lag_months"] == 2
    assert len(s["monthly"]) == 13


def test_stale_detection(regularity):
    s = summarize(regularity[regularity["region_code"] == "32"], TODAY)
    assert s["last_month"] == "2029-10" and s["stale"]


REG_MAP_ROWS = [("TGV", "ALPHA", A1), ("TGV", "ALPHA", A2), ("TGV", "BETA CENTRE", B1)]


def reg_map():
    import pandas as pd

    return pd.DataFrame(REG_MAP_ROWS, columns=["family", "label", "stop_area_id"])


def test_matching_requires_same_direction_and_stations(regularity):
    assert matching_liaisons(regularity, reg_map(), "TGV", {(A1, B1)}) == [("ALPHA", "BETA CENTRE")]
    assert matching_liaisons(regularity, reg_map(), "TGV", {(B1, A1)}) == []  # sens inverse
    assert matching_liaisons(regularity, reg_map(), "TGV", {(A1, B2)}) == []  # autre gare d'arrivée


def test_blocks_never_extrapolate(regularity):
    blocks = reliability_blocks(
        regularity=regularity, reg_map=reg_map(),
        families_pairs={"TGV": {(B1, A1)}, "IC": {(A1, B1)}, "TER": {(A1, B2)}},
        regions=[("32", "Hauts-de-France"), ("11", "Île-de-France")],
        today=TODAY, dataset_modified={},
    )
    by = {b["family"]: b for b in blocks}
    assert not by["TGV"]["available"] and "indisponible" in by["TGV"]["note"]
    assert not by["IC"]["available"]
    assert by["TER"]["available"] and by["TER"]["scope"] == "region" and "non spécifique" in by["TER"]["note"]
    assert len([b for b in blocks if b["family"] == "TER"]) == 1  # pas de série pour l'Île-de-France


def test_no_ter_region_at_all(regularity):
    blocks = reliability_blocks(
        regularity=regularity, reg_map=reg_map(), families_pairs={"TER": {(A1, B2)}},
        regions=[("11", "Île-de-France")], today=dt.date(2030, 3, 1), dataset_modified={},
    )
    assert blocks == [blocks[0]] and not blocks[0]["available"]

"""Fixtures : GTFS fabriqué à la main (tests/fixtures/mini_gtfs) et petits jeux de régularité.

Réseau de test :
- ville « Alpha » (INSEE 99001) : gares Alpha Nord (A1) et Alpha Sud (A2) ;
- Paris (arrondissements 75110 et 75112 → commune 75056) : Beta Centre (B1) et Beta Est (B2) ;
- Gamma (C, INSEE 99003) et Zeta (absente du référentiel des gares).
Fenêtre d'échantillonnage : 2 semaines à partir du lundi 4 mars 2030.
"""

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from checkeo.ingest.build import build_database

FIXTURES = Path(__file__).parent / "fixtures"
MINI_GTFS = FIXTURES / "mini_gtfs"
TODAY = dt.date(2030, 3, 1)
SAMPLE_START = dt.date(2030, 3, 4)

A1, A2 = "StopArea:OCE87000011", "StopArea:OCE87000029"
B1, B2 = "StopArea:OCE87000037", "StopArea:OCE87000045"
C, Z = "StopArea:OCE87000052", "StopArea:OCE87000060"
ALPHA, PARIS = "city:99001", "city:75056"


def gares_df() -> pd.DataFrame:
    return pd.DataFrame({
        "codes_uic": ["87000011", "87000029", "87000037", "87000045", "87000052"],
        "codeinsee": ["99001", "99001", "75110", "75112", "99003"],
        "nom": ["Alpha Nord", "Alpha Sud", "Beta Centre", "Beta Est", "Gamma"],
    })


def communes_df() -> pd.DataFrame:
    return pd.DataFrame({
        "code": ["99001", "75056", "99003"],
        "nom": ["Alpha", "Paris", "Gamma"],
        "codeRegion": ["32", "11", "32"],
    })


def months(start: str, n: int) -> list[str]:
    first = pd.Period(start, "M")
    return [str(first + i) for i in range(n)]


def tgv_df() -> pd.DataFrame:
    # 13 mois (01/2029 → 01/2030) : seuls les 12 derniers doivent compter dans la moyenne.
    ms = months("2029-01", 13)
    late = [50] + [10] * 12
    return pd.DataFrame({
        "date": ms,
        "service": "National",
        "gare_depart": "ALPHA",
        "gare_arrivee": "BETA CENTRE",
        "duree_moyenne": 60,
        "nb_train_prevu": 100,
        "nb_annulation": 2,
        "nb_train_retard_arrivee": late,
        "retard_moyen_arrivee": 12.0,
        "commentaires_retard_arrivee": None,
        "nb_train_retard_sup_15": 3,
        "nb_train_retard_sup_30": 1,
        "nb_train_retard_sup_60": 0,
        "prct_cause_externe": 50.0,
        "prct_cause_infra": 30.0,
        "prct_cause_gestion_trafic": 10.0,
        "prct_cause_materiel_roulant": 10.0,
        "prct_cause_gestion_gare": 0.0,
        "prct_cause_prise_en_charge_voyageurs": 0.0,
    })


def ter_df() -> pd.DataFrame:
    ms = months("2028-11", 12)  # dernier mois : 10/2029 → 5 mois de retard au 01/03/2030
    return pd.DataFrame({
        "date": ms * 2,
        "region": ["Hauts-de-France"] * 12 + ["Nord Pas de Calais"] * 12,
        "nombre_de_trains_programmes": 1000,
        "nombre_de_trains_ayant_circule": 980,
        "nombre_de_trains_annules": 20,
        "nombre_de_trains_en_retard_a_l_arrivee": 98,
        "taux_de_regularite": 90.0,
        "nombre_de_trains_a_l_heure_pour_un_train_en_retard_a_l_arrivee": 9.0,
        "commentaires": None,
    })


def ic_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "date", "depart", "arrivee", "nombre_de_trains_programmes", "nombre_de_trains_ayant_circule",
        "nombre_de_trains_annules", "nombre_de_trains_en_retard_a_l_arrivee", "taux_de_regularite",
    ])


@pytest.fixture(scope="session")
def db_path(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("db") / "test.duckdb"
    build_database(
        gtfs_path=MINI_GTFS,
        gares=gares_df(),
        communes=communes_df(),
        tgv=tgv_df(),
        ter=ter_df(),
        intercites=ic_df(),
        out_path=out,
        sample_start=SAMPLE_START,
        weeks=2,
        sources={"tgv": {"modified": "2030-02-02T10:00:00+00:00"}},
        overrides_path=None,
        today=TODAY,
    )
    return out


@pytest.fixture(scope="session")
def app_service(db_path):
    from checkeo.service import Checkeo

    return Checkeo(db_path)

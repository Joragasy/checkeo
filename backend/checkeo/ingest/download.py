"""Téléchargement des données brutes (GTFS, régularité, gares, communes) dans data/raw/."""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

ODS = "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets"

# URL trouvée dans le jeu « horaires-sncf » de ressources.data.sncf.com (et référencée sur
# transport.data.gouv.fr, jeu « Réseau SNCF TGV, Intercités et TER »).
GTFS_URL = "https://eu.ftp.opendatasoft.com/sncf/plandata/Export_OpenData_SNCF_GTFS_NewTripId.zip"

ODS_DATASETS = {
    "tgv": "regularite-mensuelle-tgv-aqst",
    "ter": "regularite-mensuelle-ter",
    "intercites": "regularite-mensuelle-intercites",
    "gares": "gares-de-voyageurs",
}

COMMUNES_URL = "https://geo.api.gouv.fr/communes?fields=nom,code,codeDepartement,codeRegion&format=json"


def _get(client: httpx.Client, url: str, dest: Path) -> dict:
    with client.stream("GET", url) as r:
        r.raise_for_status()
        tmp = dest.with_name(dest.name + ".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
        tmp.replace(dest)
        return {"url": url, "last_modified": r.headers.get("last-modified"), "bytes": dest.stat().st_size}


def download_all(raw_dir: Path) -> dict:
    """Télécharge toutes les sources ; retourne leurs métadonnées (URL, dates de mise à jour)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().isoformat(timespec="seconds")
    sources: dict[str, dict] = {}
    with httpx.Client(timeout=httpx.Timeout(120.0), follow_redirects=True) as client:
        log.info("GTFS…")
        sources["gtfs"] = _get(client, GTFS_URL, raw_dir / "gtfs.zip") | {
            "title": "Horaires SNCF (GTFS TGV, Intercités, TER)", "license": "ODbL", "page": f"{ODS}/horaires-sncf",
        }
        for key, ds in ODS_DATASETS.items():
            log.info("%s…", ds)
            info = client.get(f"{ODS}/{ds}").raise_for_status().json()
            m = info["metas"]["default"]
            sources[key] = _get(client, f"{ODS}/{ds}/exports/parquet", raw_dir / f"{key}.parquet") | {
                "dataset_id": ds,
                "title": m.get("title"),
                "modified": m.get("modified"),
                "license": m.get("license"),
                "page": f"https://ressources.data.sncf.com/explore/dataset/{ds}/",
            }
        log.info("communes…")
        sources["communes"] = _get(client, COMMUNES_URL, raw_dir / "communes.json") | {
            "title": "Découpage administratif (geo.api.gouv.fr)", "license": "Licence Ouverte 2.0",
        }
    for s in sources.values():
        s["downloaded_at"] = now
    (raw_dir / "sources.json").write_text(json.dumps(sources, indent=2, ensure_ascii=False))
    return sources

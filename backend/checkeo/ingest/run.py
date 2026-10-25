"""Point d'entrée de l'ingestion : python -m checkeo.ingest.run [--offline] [--sample-start AAAA-MM-JJ]"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from pathlib import Path

import pandas as pd

from ..config import DATA_DIR, DB_PATH
from .build import build_database
from .download import download_all


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Télécharge les données SNCF et construit la base Checkeo.")
    p.add_argument("--offline", action="store_true", help="réutilise data/raw/ sans retélécharger")
    p.add_argument("--sample-start", type=dt.date.fromisoformat, default=None,
                   help="début de la fenêtre d'échantillonnage du jour type (défaut : aujourd'hui)")
    p.add_argument("--weeks", type=int, default=4, help="nombre de semaines échantillonnées (défaut 4)")
    p.add_argument("--out", type=Path, default=DB_PATH)
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    raw = DATA_DIR / "raw"
    if args.offline:
        sources = json.loads((raw / "sources.json").read_text())
    else:
        sources = download_all(raw)

    report = build_database(
        gtfs_path=raw / "gtfs.zip",
        gares=pd.read_parquet(raw / "gares.parquet"),
        communes=pd.DataFrame(json.loads((raw / "communes.json").read_text())),
        tgv=pd.read_parquet(raw / "tgv.parquet"),
        ter=pd.read_parquet(raw / "ter.parquet"),
        intercites=pd.read_parquet(raw / "intercites.parquet"),
        out_path=args.out,
        sample_start=args.sample_start,
        weeks=args.weeks,
        sources=sources,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

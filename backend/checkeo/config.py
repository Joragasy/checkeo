import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("CHECKEO_DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("CHECKEO_DB", DATA_DIR / "checkeo.duckdb"))

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("CHECKEO_DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.environ.get("CHECKEO_DB", DATA_DIR / "checkeo.duckdb"))

# Mémoire de travail de DuckDB : le backend tourne avec 256 Mo sous Nomad. Au-delà, DuckDB
# déborde sur disque dans TMP_DIR (la base est montée en lecture seule).
DUCKDB_MEMORY_LIMIT = os.environ.get("CHECKEO_DUCKDB_MEMORY", "32MB")
DUCKDB_THREADS = int(os.environ.get("CHECKEO_DUCKDB_THREADS", "1"))
TMP_DIR = Path(os.environ.get("CHECKEO_TMP_DIR", "/tmp/checkeo-duckdb"))

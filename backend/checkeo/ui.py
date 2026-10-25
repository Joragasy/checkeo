"""Inspection de la base avec l'interface web DuckDB : python -m checkeo.ui [--db chemin] [--port 4213] [--write]"""

from __future__ import annotations

import argparse
import threading
from pathlib import Path

import duckdb

from .config import DB_PATH


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Ouvre la base Checkeo dans l'interface web DuckDB.")
    p.add_argument("--db", type=Path, default=DB_PATH)
    p.add_argument("--port", type=int, default=4213, help="port local de l'interface (défaut 4213)")
    p.add_argument("--write", action="store_true", help="ouvre la base en écriture (défaut : lecture seule)")
    args = p.parse_args(argv)

    if not args.db.exists():
        p.error(f"{args.db} introuvable : lancez d'abord `python -m checkeo.ingest.run`")

    # Connexion en mémoire + ATTACH : avec duckdb.connect(read_only=True), l'extension ne peut pas
    # créer sa propre base d'état (~/.duckdb/extension_data/ui/ui.db) et l'interface échoue.
    con = duckdb.connect()
    escaped = str(args.db.resolve()).replace("'", "''")
    con.execute(f"ATTACH '{escaped}' AS checkeo{'' if args.write else ' (READ_ONLY)'}")
    con.execute("USE checkeo")
    con.execute("INSTALL ui; LOAD ui;")
    con.execute(f"SET ui_local_port = {args.port}")
    con.execute("CALL start_ui()")
    mode = "écriture" if args.write else "lecture seule"
    print(f"DuckDB UI : http://localhost:{args.port} ({args.db}, {mode}). Ctrl+C pour arrêter.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        con.execute("CALL stop_ui_server()")
        con.close()


if __name__ == "__main__":
    main()

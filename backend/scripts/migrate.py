"""Bring the database to the current schema revision. Run from backend/:

    .venv/bin/python scripts/migrate.py

Handles all three states a local or docker database can be in:
- fresh/empty            -> alembic upgrade head (builds the full schema)
- pre-alembic (tables    -> alembic stamp head (schema was built by
  but no alembic_version)   create_all; mark it current, change nothing)
- alembic-managed        -> alembic upgrade head
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from config import settings


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def main() -> None:
    engine = create_engine(settings.database_url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    cfg = alembic_config()

    if not tables:
        print(f"Empty database at {settings.database_url} — building schema…")
        command.upgrade(cfg, "head")
    elif "alembic_version" not in tables:
        print("Pre-alembic database detected — stamping current revision…")
        command.stamp(cfg, "head")
    else:
        print("Applying any pending migrations…")
        command.upgrade(cfg, "head")
    print("Database is at the current revision. ✔")


if __name__ == "__main__":
    main()

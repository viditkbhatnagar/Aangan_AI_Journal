"""Bring the database to the current schema revision. Run from backend/:

    .venv/bin/python scripts/migrate.py

Handles every state a local or docker database can be in:
- fresh/empty          -> upgrade head (builds the full schema)
- pre-alembic, schema  -> stamp head (create_all already produced the current
  already current         schema; just record where it is)
- pre-alembic, schema  -> stamp the BASELINE, then upgrade head, so a database
  built by an older       from an older release actually receives the
  release                 migrations it is missing
- alembic-managed      -> upgrade head
"""
import sys
from pathlib import Path

# Windows consoles default to cp1252, which can't print the ✔ below — never
# let a print() make a successful migration look like a failure.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from config import settings
from db import Base
import models  # noqa: F401  (registers every table on Base.metadata)

# Revision that matches what the pre-Alembic create_all schema produced.
BASELINE_REVISION = "26dfeebc78ce"


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def _missing_schema_objects(engine) -> list:
    """Tables/columns models.py declares that the database doesn't have.
    Only additions matter here — that is what an older release lacks."""
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        diffs = compare_metadata(context, Base.metadata)
    return [d for d in diffs if isinstance(d, tuple) and d[0] in {"add_table", "add_column"}]


def main() -> None:
    engine = create_engine(settings.database_url)
    tables = set(inspect(engine).get_table_names())
    cfg = alembic_config()

    if not tables:
        print(f"Empty database at {settings.database_url} — building schema…")
        command.upgrade(cfg, "head")
    elif "alembic_version" not in tables:
        missing = _missing_schema_objects(engine)
        if missing:
            head = ScriptDirectory.from_config(cfg).get_current_head()
            print(
                f"Pre-alembic database from an older release ({len(missing)} "
                "missing table(s)/column(s)) — stamping the baseline, then "
                f"upgrading to {head}…"
            )
            command.stamp(cfg, BASELINE_REVISION)
            command.upgrade(cfg, "head")
        else:
            print("Pre-alembic database already at the current schema — stamping…")
            command.stamp(cfg, "head")
    else:
        print("Applying any pending migrations…")
        command.upgrade(cfg, "head")

    engine.dispose()
    print(f"Database at {settings.database_url} is current. ✔")


if __name__ == "__main__":
    main()

"""Migrations must stay honest: upgrading an empty DB to head has to produce
exactly the schema models.py describes, or a migration was skipped/drifted."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from db import Base

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def test_upgrade_head_matches_models(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/migrated.db"
    from config import settings

    # env.py reads settings.database_url at run time, so this redirects alembic
    monkeypatch.setattr(settings, "database_url", db_url)
    command.upgrade(_alembic_config(), "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    migrated_tables = set(inspector.get_table_names()) - {"alembic_version"}
    model_tables = set(Base.metadata.tables.keys())
    assert migrated_tables == model_tables, (
        f"missing from migrations: {model_tables - migrated_tables}; "
        f"orphaned in migrations: {migrated_tables - model_tables}"
    )

    for table in sorted(model_tables):
        migrated_cols = {c["name"] for c in inspector.get_columns(table)}
        model_cols = {c.name for c in Base.metadata.tables[table].columns}
        assert migrated_cols == model_cols, (
            f"{table}: missing {model_cols - migrated_cols}, "
            f"extra {migrated_cols - model_cols}"
        )
    engine.dispose()


def test_migrate_script_stamps_pre_alembic_db(tmp_path, monkeypatch):
    """A DB built by create_all (no alembic_version) gets stamped, not re-built."""
    db_url = f"sqlite:///{tmp_path}/legacy.db"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    from config import settings

    monkeypatch.setattr(settings, "database_url", db_url)
    import importlib

    migrate = importlib.import_module("scripts.migrate")
    migrate.main()

    engine = create_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    assert "alembic_version" in tables
    engine.dispose()

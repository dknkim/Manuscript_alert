"""Neon (PostgreSQL) connection pool, schema bootstrap, and one-time data migration."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import asyncpg

from backend.src.config import ARCHIVE_DIR, MODELS_DIR, get_app_config

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

# ---------------------------------------------------------------------------
# Schema — CREATE TABLE IF NOT EXISTS so re-runs are safe
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id         text PRIMARY KEY,
    email      text UNIQUE NOT NULL,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS settings (
    id         serial PRIMARY KEY,
    user_id    text REFERENCES users(id),
    data       jsonb NOT NULL,
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS settings_versions (
    id         serial PRIMARY KEY,
    user_id    text REFERENCES users(id),
    data       jsonb NOT NULL,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_presets (
    id         serial PRIMARY KEY,
    user_id    text REFERENCES users(id),
    name       text NOT NULL,
    data       jsonb NOT NULL,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS papers (
    id          serial PRIMARY KEY,
    user_id     text REFERENCES users(id),
    title       text NOT NULL,
    source      text,
    archived    boolean DEFAULT true,
    archived_at timestamptz DEFAULT now(),
    data        jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_papers_archived ON papers (archived);
"""


# ---------------------------------------------------------------------------
# JSON codecs — asyncpg encodes/decodes jsonb ↔ Python dict automatically
# ---------------------------------------------------------------------------
async def _init_connection(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


# ---------------------------------------------------------------------------
# Pool lifecycle
# ---------------------------------------------------------------------------
async def create_pool() -> asyncpg.Pool | None:
    """Create and store the global connection pool. Returns None if DATABASE_URL is not set."""
    global _pool
    url = get_app_config().database_url
    if not url:
        logger.info("DATABASE_URL not set — running without Neon DB (file-based fallback)")
        return None
    if _pool is None:
        _pool = await asyncpg.create_pool(url, min_size=1, max_size=10, init=_init_connection)
        logger.info("Neon DB pool created")
    return _pool


def get_pool() -> asyncpg.Pool | None:
    """Return the current pool (or None if not initialised)."""
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Neon DB pool closed")


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------
async def bootstrap(pool: asyncpg.Pool) -> None:
    """Create all tables if they don't already exist."""
    async with pool.acquire() as conn:
        await conn.execute(_SCHEMA)
    logger.info("DB schema bootstrapped")


# ---------------------------------------------------------------------------
# One-time local → DB migration
# Runs only when a table is empty; safe to call on every startup.
# ---------------------------------------------------------------------------
async def migrate_local_data(pool: asyncpg.Pool) -> None:
    """Import local file data into the DB tables if the tables are empty."""
    await _migrate_settings(pool)
    await _migrate_model_presets(pool)
    await _migrate_archive(pool)


async def _migrate_settings(pool: asyncpg.Pool) -> None:
    count = await pool.fetchval("SELECT COUNT(*) FROM settings")
    if count:
        return  # Already populated

    # Load from local settings.py via SettingsService
    try:
        from backend.src.services.settings_service import SettingsService
        data = SettingsService().load_settings()
        await pool.execute(
            "INSERT INTO settings (user_id, data) VALUES (NULL, $1)", data
        )
        logger.info("Migrated local settings.py → settings table")
    except Exception as exc:
        logger.warning(f"Could not migrate settings: {exc}")


async def _migrate_model_presets(pool: asyncpg.Pool) -> None:
    count = await pool.fetchval("SELECT COUNT(*) FROM model_presets")
    if count:
        return

    import os
    if not MODELS_DIR.exists():
        return
    migrated = 0
    for fname in os.listdir(MODELS_DIR):
        if not fname.endswith(".json"):
            continue
        name = fname.replace(".json", "")
        try:
            with open(MODELS_DIR / fname, encoding="utf-8") as fh:
                data = json.load(fh)
            await pool.execute(
                "INSERT INTO model_presets (user_id, name, data) VALUES (NULL, $1, $2)",
                name, data,
            )
            migrated += 1
        except Exception as exc:
            logger.warning(f"Could not migrate model preset {fname}: {exc}")
    if migrated:
        logger.info(f"Migrated {migrated} model preset(s) → model_presets table")


async def _migrate_archive(pool: asyncpg.Pool) -> None:
    count = await pool.fetchval("SELECT COUNT(*) FROM papers")
    if count:
        return

    archive_file = ARCHIVE_DIR / "archive.json"
    if not archive_file.exists():
        return
    try:
        with open(archive_file, encoding="utf-8") as fh:
            archive: dict = json.load(fh)
        migrated = 0
        for _date, papers in archive.items():
            for paper in papers:
                await pool.execute(
                    "INSERT INTO papers (user_id, title, source, archived, data) VALUES (NULL, $1, $2, true, $3)",
                    paper.get("title", ""),
                    paper.get("source"),
                    paper,
                )
                migrated += 1
        if migrated:
            logger.info(f"Migrated {migrated} archived paper(s) → papers table")
    except Exception as exc:
        logger.warning(f"Could not migrate archive: {exc}")

"""Async SQL data access layer — all DB queries live here."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

async def get_settings(pool: asyncpg.Pool, user_id: str | None = None) -> dict[str, Any] | None:
    """Return the current settings for this user, or None if not yet saved."""
    row = await pool.fetchrow(
        "SELECT data FROM settings WHERE user_id IS NOT DISTINCT FROM $1 ORDER BY updated_at DESC LIMIT 1",
        user_id,
    )
    return dict(row["data"]) if row else None


async def save_settings(pool: asyncpg.Pool, data: dict[str, Any], user_id: str | None = None) -> None:
    """Overwrite the current settings row for this user (delete + insert)."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM settings WHERE user_id IS NOT DISTINCT FROM $1", user_id
            )
            await conn.execute(
                "INSERT INTO settings (user_id, data, updated_at) VALUES ($1, $2, now())",
                user_id,
                data,
            )


# ---------------------------------------------------------------------------
# Model presets
# ---------------------------------------------------------------------------

async def list_model_presets(pool: asyncpg.Pool, user_id: str | None = None) -> list[dict[str, str]]:
    """Return [{name, filename, modified}, ...] sorted by name."""
    rows = await pool.fetch(
        "SELECT name, created_at FROM model_presets WHERE user_id IS NOT DISTINCT FROM $1 ORDER BY name",
        user_id,
    )
    return [
        {
            "name": r["name"].replace("_", " "),
            "filename": r["name"] + ".json",
            "modified": r["created_at"].strftime("%Y-%m-%d %H:%M"),
        }
        for r in rows
    ]


async def get_model_preset(pool: asyncpg.Pool, name: str, user_id: str | None = None) -> dict[str, Any] | None:
    """Return the data dict for the named preset, or None."""
    row = await pool.fetchrow(
        "SELECT data FROM model_presets WHERE user_id IS NOT DISTINCT FROM $1 AND name = $2",
        user_id,
        name,
    )
    return dict(row["data"]) if row else None


async def save_model_preset(
    pool: asyncpg.Pool, name: str, data: dict[str, Any], user_id: str | None = None
) -> None:
    """Insert or replace the named preset (delete + insert for upsert semantics)."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM model_presets WHERE user_id IS NOT DISTINCT FROM $1 AND name = $2",
                user_id,
                name,
            )
            await conn.execute(
                "INSERT INTO model_presets (user_id, name, data) VALUES ($1, $2, $3)",
                user_id,
                name,
                data,
            )


async def delete_model_preset(pool: asyncpg.Pool, name: str, user_id: str | None = None) -> bool:
    """Delete the named preset. Returns True if a row was deleted."""
    result = await pool.execute(
        "DELETE FROM model_presets WHERE user_id IS NOT DISTINCT FROM $1 AND name = $2",
        user_id,
        name,
    )
    return result.endswith("1")


# ---------------------------------------------------------------------------
# Archived papers
# ---------------------------------------------------------------------------

async def get_archived_papers(
    pool: asyncpg.Pool, user_id: str | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Return archived papers grouped by date: {date_str: [paper, ...]}."""
    rows = await pool.fetch(
        "SELECT archived_at, data FROM papers WHERE archived = true AND user_id IS NOT DISTINCT FROM $1 ORDER BY archived_at DESC",
        user_id,
    )
    archive: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        date_str: str = row["archived_at"].strftime("%Y-%m-%d")
        paper = dict(row["data"])
        paper["archived_at"] = row["archived_at"].isoformat()
        archive.setdefault(date_str, []).append(paper)
    return archive


async def archive_paper(
    pool: asyncpg.Pool, paper_data: dict[str, Any], user_id: str | None = None
) -> str:
    """Archive a paper. Returns 'ok' or 'already_archived'."""
    title = paper_data.get("title", "")
    exists = await pool.fetchval(
        "SELECT id FROM papers WHERE user_id IS NOT DISTINCT FROM $1 AND title = $2 AND archived = true",
        user_id,
        title,
    )
    if exists:
        return "already_archived"
    await pool.execute(
        "INSERT INTO papers (user_id, title, source, archived, archived_at, data) VALUES ($1, $2, $3, true, now(), $4)",
        user_id,
        title,
        paper_data.get("source"),
        paper_data,
    )
    return "ok"


async def unarchive_paper(
    pool: asyncpg.Pool, title: str, user_id: str | None = None
) -> bool:
    """Delete the archived paper with this title. Returns True if found and deleted."""
    result = await pool.execute(
        "DELETE FROM papers WHERE user_id IS NOT DISTINCT FROM $1 AND title = $2 AND archived = true",
        user_id,
        title,
    )
    return not result.endswith(" 0")


# ---------------------------------------------------------------------------
# Users (Clerk)
# ---------------------------------------------------------------------------

async def get_or_create_user(pool: asyncpg.Pool, user_id: str, email: str) -> None:
    """Upsert a Clerk user row on first sign-in."""
    await pool.execute(
        """
        INSERT INTO users (id, email) VALUES ($1, $2)
        ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email
        """,
        user_id,
        email,
    )

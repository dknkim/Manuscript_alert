"""Papers endpoints — /api/v1/papers (fetch, export, archive, review/SSE)."""

from __future__ import annotations

import io
import json
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated, Any

import asyncpg
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from backend.src.api.auth import CurrentUser
from backend.src.api.deps import get_db_pool, get_settings_service
from backend.src.db import models as db
from backend.src.models.schemas import (
    ArchivePaperRequest,
    FetchRequest,
    StatusResponse,
    UnarchivePaperRequest,
)
from backend.src.services import archive_service
from backend.src.services.paper_service import (
    fetch_and_rank,
    fetch_and_rank_with_progress,
)
from backend.src.services.settings_service import SettingsService

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])

SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]
DBPool = Annotated[asyncpg.Pool | None, Depends(get_db_pool)]

# Module-level cache for export reuse
_fetch_cache: dict[str, Any] | None = None


@router.post("/fetch")
async def fetch_papers(req: FetchRequest, svc: SettingsSvc, pool: DBPool, user: CurrentUser) -> dict[str, Any]:
    global _fetch_cache
    settings: dict[str, Any] = (
        (await db.get_settings(pool, user) if pool else None) or svc.load_settings()
    )
    papers, errors = fetch_and_rank(settings, req.data_sources, req.search_mode)

    must_have: list[str] = settings.get("must_have_keywords", [])
    filtered: list[dict[str, Any]] = [
        p for p in papers
        if len(p["matched_keywords"]) >= 2
        and (not must_have or any(mk in p["matched_keywords"] for mk in must_have))
    ]

    _fetch_cache = {"data_sources": req.data_sources, "search_mode": req.search_mode, "filtered": filtered}

    return {
        "papers": filtered[:50],
        "total_before_filter": len(papers),
        "total_after_filter": len(filtered),
        "errors": errors,
        "must_have_keywords": must_have,
    }


@router.post("/review")
async def review_papers(req: FetchRequest, svc: SettingsSvc, pool: DBPool, user: CurrentUser) -> EventSourceResponse:
    """SSE endpoint — streams progress events during fetch and rank."""
    settings: dict[str, Any] = (
        (await db.get_settings(pool, user) if pool else None) or svc.load_settings()
    )

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        async for evt in fetch_and_rank_with_progress(settings, req.data_sources, req.search_mode):
            yield {"event": evt["event"], "data": json.dumps(evt["data"])}

    return EventSourceResponse(event_generator())


@router.post("/export")
async def export_papers(req: FetchRequest, svc: SettingsSvc, pool: DBPool, user: CurrentUser) -> StreamingResponse:
    global _fetch_cache
    if (
        _fetch_cache is not None
        and _fetch_cache["data_sources"] == req.data_sources
        and _fetch_cache["search_mode"] == req.search_mode
    ):
        filtered = _fetch_cache["filtered"]
    else:
        settings: dict[str, Any] = (
            (await db.get_settings(pool, user) if pool else None) or svc.load_settings()
        )
        papers, _ = fetch_and_rank(settings, req.data_sources, req.search_mode)
        must_have: list[str] = settings.get("must_have_keywords", [])
        filtered = [
            p for p in papers
            if len(p["matched_keywords"]) >= 2
            and (not must_have or any(mk in p["matched_keywords"] for mk in must_have))
        ]

    buf = io.StringIO()
    pd.DataFrame(filtered).to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=papers_{datetime.now().strftime('%Y%m%d')}.csv"},
    )


@router.post("/archive")
async def archive_paper(req: ArchivePaperRequest, pool: DBPool, user: CurrentUser) -> StatusResponse:
    if pool is not None:
        status = await db.archive_paper(pool, req.paper, user)
        return StatusResponse(status=status)

    # File-based fallback
    archive: dict[str, list[dict[str, Any]]] = archive_service.load_archive()
    today: str = datetime.now().strftime("%Y-%m-%d")
    papers_today = archive.get(today, [])
    if any(p["title"] == req.paper.get("title") for p in papers_today):
        return StatusResponse(status="already_archived")
    papers_today.append({**req.paper, "archived_at": datetime.now().isoformat()})
    archive[today] = papers_today
    archive_service.save_archive(archive)
    return StatusResponse(status="ok")


@router.get("/archive")
async def list_archived_papers(pool: DBPool, user: CurrentUser) -> dict[str, Any]:
    if pool is not None:
        archive = await db.get_archived_papers(pool, user)
    else:
        archive = archive_service.load_archive()

    all_titles = [p["title"] for papers in archive.values() for p in papers]
    return {"archive": archive, "archived_titles": all_titles, "total": len(all_titles)}


@router.delete("/archive")
async def unarchive_paper(req: UnarchivePaperRequest, pool: DBPool, user: CurrentUser) -> StatusResponse:
    if pool is not None:
        found = await db.unarchive_paper(pool, req.title, user)
        if not found:
            raise HTTPException(status_code=404, detail="Paper not found in archive")
        return StatusResponse(status="ok")

    # File-based fallback
    archive = archive_service.load_archive()
    papers = archive.get(req.date, [])
    original_len = len(papers)
    papers = [p for p in papers if p["title"] != req.title]
    if len(papers) == original_len:
        raise HTTPException(status_code=404, detail="Paper not found in archive")
    if papers:
        archive[req.date] = papers
    else:
        archive.pop(req.date, None)
    archive_service.save_archive(archive)
    return StatusResponse(status="ok")

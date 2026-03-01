"""Papers endpoints — /api/v1/papers (fetch, export, archive, review/SSE)."""

from __future__ import annotations

import io
import json
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from backend.src.api.deps import get_settings_service
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

# Module-level cache for export reuse
_fetch_cache: dict[str, Any] | None = None


@router.post("/fetch")
def fetch_papers(req: FetchRequest, svc: SettingsSvc) -> dict[str, Any]:
    global _fetch_cache
    settings: dict[str, Any] = svc.load_settings()
    papers, errors = fetch_and_rank(settings, req.data_sources, req.search_mode)

    must_have: list[str] = settings.get("must_have_keywords", [])
    filtered: list[dict[str, Any]] = [
        p
        for p in papers
        if len(p["matched_keywords"]) >= 2
        and (not must_have or any(mk in p["matched_keywords"] for mk in must_have))
    ]

    _fetch_cache = {
        "data_sources": req.data_sources,
        "search_mode": req.search_mode,
        "filtered": filtered,
    }

    return {
        "papers": filtered[:50],
        "total_before_filter": len(papers),
        "total_after_filter": len(filtered),
        "errors": errors,
        "must_have_keywords": must_have,
    }


@router.post("/review")
async def review_papers(req: FetchRequest, svc: SettingsSvc) -> EventSourceResponse:
    """SSE endpoint — streams progress events during fetch and rank."""
    settings: dict[str, Any] = svc.load_settings()

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        async for evt in fetch_and_rank_with_progress(
            settings, req.data_sources, req.search_mode
        ):
            yield {
                "event": evt["event"],
                "data": json.dumps(evt["data"]),
            }

    return EventSourceResponse(event_generator())


@router.post("/export")
def export_papers(req: FetchRequest, svc: SettingsSvc) -> StreamingResponse:
    global _fetch_cache
    if (
        _fetch_cache is not None
        and _fetch_cache["data_sources"] == req.data_sources
        and _fetch_cache["search_mode"] == req.search_mode
    ):
        filtered = _fetch_cache["filtered"]
    else:
        settings: dict[str, Any] = svc.load_settings()
        papers, _ = fetch_and_rank(settings, req.data_sources, req.search_mode)
        must_have: list[str] = settings.get("must_have_keywords", [])
        filtered = [
            p
            for p in papers
            if len(p["matched_keywords"]) >= 2
            and (not must_have or any(mk in p["matched_keywords"] for mk in must_have))
        ]

    buf = io.StringIO()
    pd.DataFrame(filtered).to_csv(buf, index=False)
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=papers_{datetime.now().strftime('%Y%m%d')}.csv"
            )
        },
    )


@router.post("/archive")
def archive_paper(req: ArchivePaperRequest) -> StatusResponse:
    archive: dict[str, list[dict[str, Any]]] = archive_service.load_archive()
    today: str = datetime.now().strftime("%Y-%m-%d")

    papers_today: list[dict[str, Any]] = archive.get(today, [])
    if any(p["title"] == req.paper.get("title") for p in papers_today):
        return StatusResponse(status="already_archived")

    papers_today.append({**req.paper, "archived_at": datetime.now().isoformat()})
    archive[today] = papers_today
    archive_service.save_archive(archive)
    return StatusResponse(status="ok")


@router.get("/archive")
def list_archived_papers() -> dict[str, Any]:
    archive: dict[str, list[dict[str, Any]]] = archive_service.load_archive()
    all_titles: list[str] = []
    total: int = 0
    for papers in archive.values():
        for p in papers:
            all_titles.append(p["title"])
            total += 1
    return {
        "archive": archive,
        "archived_titles": all_titles,
        "total": total,
    }


@router.delete("/archive")
def unarchive_paper(req: UnarchivePaperRequest) -> StatusResponse:
    archive: dict[str, list[dict[str, Any]]] = archive_service.load_archive()
    papers: list[dict[str, Any]] = archive.get(req.date, [])
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

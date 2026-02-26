"""Papers endpoints — fetch, export, archive."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

import backend.src.config as config
from backend.src.models.schemas import (
    ArchivePaperRequest,
    FetchRequest,
    StatusResponse,
    UnarchivePaperRequest,
)
from backend.src.services import archive_service
from backend.src.services.paper_service import fetch_and_rank, load_settings


router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/fetch")
def fetch_papers(req: FetchRequest) -> dict[str, Any]:
    """Fetch, rank, and filter papers."""
    settings: dict[str, Any] = load_settings()
    papers: list[dict[str, Any]]
    errors: list[str]
    papers, errors = fetch_and_rank(settings, req.data_sources, req.search_mode)

    # Apply filters
    must_have: list[str] = settings.get("must_have_keywords", [])
    filtered: list[dict[str, Any]] = []
    for p in papers:
        if len(p["matched_keywords"]) < 2:
            continue
        if must_have:
            if not any(mk in p["matched_keywords"] for mk in must_have):
                continue
        filtered.append(p)

    # Cache the full filtered list so export can reuse it without re-fetching
    config._fetch_cache = {
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


@router.post("/export")
def export_papers(req: FetchRequest) -> StreamingResponse:
    """Export papers as CSV."""
    # Reuse the last fetch result if the request params match
    if (
        config._fetch_cache is not None
        and config._fetch_cache["data_sources"] == req.data_sources
        and config._fetch_cache["search_mode"] == req.search_mode
    ):
        filtered: list[dict[str, Any]] = config._fetch_cache["filtered"]
    else:
        settings: dict[str, Any] = load_settings()
        papers: list[dict[str, Any]]
        papers, _ = fetch_and_rank(settings, req.data_sources, req.search_mode)
        must_have: list[str] = settings.get("must_have_keywords", [])
        filtered = [
            p
            for p in papers
            if len(p["matched_keywords"]) >= 2
            and (not must_have or any(mk in p["matched_keywords"] for mk in must_have))
        ]

    df: pd.DataFrame = pd.DataFrame(filtered)
    buf: io.StringIO = io.StringIO()
    df.to_csv(buf, index=False)
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
    """Archive a paper's metadata under today's date."""
    archive: dict[str, list[dict[str, Any]]] = archive_service.load_archive()
    today: str = datetime.now().strftime("%Y-%m-%d")

    papers_today: list[dict[str, Any]] = archive.get(today, [])
    if any(p["title"] == req.paper.get("title") for p in papers_today):
        return StatusResponse(status="already_archived")

    entry: dict[str, Any] = {
        **req.paper,
        "archived_at": datetime.now().isoformat(),
    }
    papers_today.append(entry)
    archive[today] = papers_today
    archive_service.save_archive(archive)
    return StatusResponse(status="ok")


@router.get("/archive")
def list_archived_papers() -> dict[str, Any]:
    """Return all archived papers grouped by date, plus a flat set of titles."""
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
    """Remove a paper from the archive by title and date."""
    archive: dict[str, list[dict[str, Any]]] = archive_service.load_archive()
    papers: list[dict[str, Any]] = archive.get(req.date, [])
    original_len: int = len(papers)
    papers = [p for p in papers if p["title"] != req.title]
    if len(papers) == original_len:
        raise HTTPException(status_code=404, detail="Paper not found in archive")
    if papers:
        archive[req.date] = papers
    else:
        archive.pop(req.date, None)
    archive_service.save_archive(archive)
    return StatusResponse(status="ok")

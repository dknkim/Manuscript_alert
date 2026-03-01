"""SSE event types for the streaming paper review endpoint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SSEEvent(BaseModel):
    """Base SSE event sent to the frontend."""

    event: str
    data: dict[str, Any]


# Event constructors — keep it simple, just dicts.


def source_start(source: str) -> dict[str, Any]:
    return {"event": "source_start", "data": {"source": source}}


def source_complete(source: str, count: int) -> dict[str, Any]:
    return {"event": "source_complete", "data": {"source": source, "count": count}}


def source_error(source: str, error: str) -> dict[str, Any]:
    return {"event": "source_error", "data": {"source": source, "error": error}}


def batch_progress(
    source: str, batch: int, total: int, papers_so_far: int
) -> dict[str, Any]:
    return {
        "event": "batch_progress",
        "data": {
            "source": source,
            "batch": batch,
            "total": total,
            "papers_so_far": papers_so_far,
        },
    }


def scoring(total_papers: int = 0, criteria: list[str] | None = None) -> dict[str, Any]:
    return {
        "event": "scoring",
        "data": {"total_papers": total_papers, "criteria": criteria or []},
    }


def filtering(
    total_before: int,
    total_after: int,
    min_keywords: int = 2,
    must_have_keywords: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "event": "filtering",
        "data": {
            "total_before": total_before,
            "total_after": total_after,
            "min_keywords": min_keywords,
            "must_have_keywords": must_have_keywords or [],
        },
    }


def complete(result: dict[str, Any]) -> dict[str, Any]:
    return {"event": "complete", "data": result}

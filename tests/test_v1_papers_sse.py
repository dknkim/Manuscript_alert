"""Tests for the /api/v1/papers/review SSE endpoint."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_sse(lines: Iterable[str]) -> list[dict[str, Any]]:
    """Parse raw SSE lines into a list of {event, data} dicts.

    Ignores comment lines (starting with `:`) and keep-alive pings.
    Each event is terminated by a blank line.
    """
    events: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for raw in lines:
        line = raw.rstrip("\r")
        if not line:
            if current:
                events.append(current)
                current = {}
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            current["event"] = line[len("event:") :].strip()
        elif line.startswith("data:"):
            payload = line[len("data:") :].strip()
            try:
                current["data"] = json.loads(payload)
            except json.JSONDecodeError:
                current["data"] = payload
    if current:
        events.append(current)
    return events


def _stream_review(client: TestClient, body: dict[str, Any]) -> list[dict[str, Any]]:
    """POST to /api/v1/papers/review and parse the full SSE stream."""
    with client.stream("POST", "/api/v1/papers/review", json=body) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        return _parse_sse(r.iter_lines())


def _mock_pubmed_papers() -> list[dict[str, Any]]:
    return [
        {
            "title": "Amyloid PET in Alzheimer's disease diagnosis",
            "authors": ["Smith J"],
            "abstract": (
                "Amyloid PET imaging provides quantitative measures of amyloid "
                "burden in Alzheimer's disease patients using tau "
                "and dementia biomarkers."
            ),
            "published": "2026-02-20",
            "source": "PubMed",
            "journal": "Nature Medicine",
            "pmid": "99990001",
            "volume": "32",
            "issue": "2",
            "arxiv_url": "",
            "categories": [],
        },
        {
            "title": "Unrelated cardiology study",
            "authors": ["Jones B"],
            "abstract": "A study about cardiac procedures with no neuro keywords.",
            "published": "2026-02-19",
            "source": "PubMed",
            "journal": "Cardiology Today",
            "pmid": "99990002",
            "volume": "10",
            "issue": "1",
            "arxiv_url": "",
            "categories": [],
        },
    ]


ALL_DISABLED = {"pubmed": False, "arxiv": False, "biorxiv": False, "medrxiv": False}
PUBMED_ONLY = {"pubmed": True, "arxiv": False, "biorxiv": False, "medrxiv": False}


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------
def test_v1_review_smoke_empty_sources(client: TestClient) -> None:
    """With all sources disabled, stream ends with a `complete` event and empty papers."""
    events = _stream_review(
        client,
        {"data_sources": ALL_DISABLED, "search_mode": "Brief"},
    )

    assert events, "stream yielded no events"
    assert events[-1]["event"] == "complete"
    data = events[-1]["data"]
    assert data["papers"] == []
    assert data["total_before_filter"] == 0
    assert data["total_after_filter"] == 0


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_v1_review_happy_path_with_mock_pubmed(client: TestClient) -> None:
    """Mocked PubMed fetch emits the full event sequence and a valid complete payload."""
    with patch("backend.src.services.paper_service.pubmed_fetcher") as mock_fetcher:
        mock_fetcher.fetch_papers.return_value = _mock_pubmed_papers()

        events = _stream_review(
            client,
            {"data_sources": PUBMED_ONLY, "search_mode": "Brief"},
        )

    event_types = [e["event"] for e in events]
    # Required phases, in order
    assert "source_start" in event_types
    assert "source_complete" in event_types
    assert "scoring" in event_types
    assert "filtering" in event_types
    assert event_types[-1] == "complete"
    # source_start precedes source_complete
    assert event_types.index("source_start") < event_types.index("source_complete")
    # scoring + filtering precede complete
    assert event_types.index("scoring") < event_types.index("filtering")
    assert event_types.index("filtering") < event_types.index("complete")

    # complete payload shape
    final = events[-1]["data"]
    assert final["total_before_filter"] == 2
    for paper in final["papers"]:
        assert len(paper["matched_keywords"]) >= 2


# ---------------------------------------------------------------------------
# Event shapes match the constructors in backend/src/models/events.py
# ---------------------------------------------------------------------------
def test_v1_review_event_shapes_match_constructors(client: TestClient) -> None:
    """Every event's data dict has the fields its constructor produces."""
    with patch("backend.src.services.paper_service.pubmed_fetcher") as mock_fetcher:
        mock_fetcher.fetch_papers.return_value = _mock_pubmed_papers()
        events = _stream_review(
            client,
            {"data_sources": PUBMED_ONLY, "search_mode": "Brief"},
        )

    required_keys = {
        "source_start": {"source"},
        "source_complete": {"source", "count", "detail"},
        "source_step": {"source", "message"},
        "source_error": {"source", "error"},
        "batch_progress": {"source", "batch", "total", "papers_so_far"},
        "scoring": {"total_papers", "criteria"},
        "filtering": {"total_before", "total_after", "min_keywords", "must_have_keywords"},
    }

    for e in events:
        kind = e["event"]
        if kind == "complete":
            continue  # complete carries full result payload, not in the table
        expected = required_keys.get(kind)
        assert expected is not None, f"unexpected event type {kind!r}"
        assert expected <= e["data"].keys(), (
            f"{kind} missing fields: expected {expected}, got {set(e['data'].keys())}"
        )


# ---------------------------------------------------------------------------
# Source error emits `source_error` and other phases still complete
# ---------------------------------------------------------------------------
def test_v1_review_source_error_emits_event(client: TestClient) -> None:
    """If a fetcher raises, a source_error event is emitted and stream still completes."""
    with patch("backend.src.services.paper_service.pubmed_fetcher") as mock_fetcher:
        mock_fetcher.fetch_papers.side_effect = RuntimeError("boom")

        events = _stream_review(
            client,
            {"data_sources": PUBMED_ONLY, "search_mode": "Brief"},
        )

    event_types = [e["event"] for e in events]
    assert "source_error" in event_types
    err_event = next(e for e in events if e["event"] == "source_error")
    assert err_event["data"]["source"] == "PubMed"
    assert err_event["data"]["error"]  # non-empty message
    assert event_types[-1] == "complete"
    # Final payload carries the error string as well
    assert events[-1]["data"]["errors"]
    assert any("PubMed" in err for err in events[-1]["data"]["errors"])


# ---------------------------------------------------------------------------
# must_have_keywords filter is applied and surfaced in the complete payload
# ---------------------------------------------------------------------------
def test_v1_review_must_have_keywords_applied(
    client: TestClient, mock_settings: dict[str, Any]
) -> None:
    """Setting must_have_keywords filters the final papers list."""
    # Require a keyword that NONE of the mocked papers contain
    mock_settings["must_have_keywords"] = ["nonexistent_keyword"]
    r = client.put("/api/v1/settings", json={"settings": mock_settings})
    assert r.status_code == 200

    with patch("backend.src.services.paper_service.pubmed_fetcher") as mock_fetcher:
        mock_fetcher.fetch_papers.return_value = _mock_pubmed_papers()

        events = _stream_review(
            client,
            {"data_sources": PUBMED_ONLY, "search_mode": "Brief"},
        )

    final = events[-1]["data"]
    assert final["papers"] == []
    assert final["must_have_keywords"] == ["nonexistent_keyword"]
    # total_before_filter reflects the raw papers, filter happens after
    assert final["total_before_filter"] == 2
    assert final["total_after_filter"] == 0

"""Tests for the /api/v1/papers endpoints — fetch, archive, export."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------
def test_v1_fetch_papers_no_sources(client: TestClient) -> None:
    """Fetch with all sources disabled returns empty results."""
    resp = client.post(
        "/api/v1/papers/fetch",
        json={
            "data_sources": {
                "pubmed": False,
                "arxiv": False,
                "biorxiv": False,
                "medrxiv": False,
            },
            "search_mode": "Brief",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["papers"] == []
    assert data["total_before_filter"] == 0


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


def test_v1_fetch_papers_with_mock_pubmed(client: TestClient) -> None:
    """Fetch with mocked PubMed returns scored/filtered results."""
    with patch("backend.src.services.paper_service.pubmed_fetcher") as mock_fetcher:
        mock_fetcher.fetch_papers.return_value = _mock_pubmed_papers()

        resp = client.post(
            "/api/v1/papers/fetch",
            json={
                "data_sources": {
                    "pubmed": True,
                    "arxiv": False,
                    "biorxiv": False,
                    "medrxiv": False,
                },
                "search_mode": "Brief",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_before_filter"] == 2
    for paper in data["papers"]:
        assert len(paper["matched_keywords"]) >= 2


# ---------------------------------------------------------------------------
# Archive CRUD
# ---------------------------------------------------------------------------
def test_v1_archive_and_list(client: TestClient, sample_paper: dict[str, Any]) -> None:
    """Archive a paper, then list it."""
    resp = client.post("/api/v1/papers/archive", json={"paper": sample_paper})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp2 = client.get("/api/v1/papers/archive")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["total"] == 1
    assert sample_paper["title"] in data["archived_titles"]


def test_v1_archive_duplicate(client: TestClient, sample_paper: dict[str, Any]) -> None:
    """Archiving the same paper twice returns already_archived."""
    client.post("/api/v1/papers/archive", json={"paper": sample_paper})
    resp = client.post("/api/v1/papers/archive", json={"paper": sample_paper})
    assert resp.json()["status"] == "already_archived"


def test_v1_unarchive_paper(client: TestClient, sample_paper: dict[str, Any]) -> None:
    """Archive then unarchive a paper."""
    client.post("/api/v1/papers/archive", json={"paper": sample_paper})

    archive_resp = client.get("/api/v1/papers/archive")
    archive_data = archive_resp.json()["archive"]
    date_key = next(iter(archive_data.keys()))

    resp = client.request(
        "DELETE",
        "/api/v1/papers/archive",
        json={"title": sample_paper["title"], "date": date_key},
    )
    assert resp.status_code == 200

    resp2 = client.get("/api/v1/papers/archive")
    assert resp2.json()["total"] == 0


def test_v1_unarchive_not_found(client: TestClient) -> None:
    resp = client.request(
        "DELETE",
        "/api/v1/papers/archive",
        json={"title": "Nonexistent Paper", "date": "2026-01-01"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def test_v1_export_csv(client: TestClient) -> None:
    """Export returns a CSV response."""
    with patch("backend.src.services.paper_service.pubmed_fetcher") as mock_fetcher:
        mock_fetcher.fetch_papers.return_value = _mock_pubmed_papers()

        client.post(
            "/api/v1/papers/fetch",
            json={
                "data_sources": {
                    "pubmed": True,
                    "arxiv": False,
                    "biorxiv": False,
                    "medrxiv": False,
                },
                "search_mode": "Brief",
            },
        )

        resp = client.post(
            "/api/v1/papers/export",
            json={
                "data_sources": {
                    "pubmed": True,
                    "arxiv": False,
                    "biorxiv": False,
                    "medrxiv": False,
                },
                "search_mode": "Brief",
            },
        )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment" in resp.headers["content-disposition"]

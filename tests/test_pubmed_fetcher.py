"""Tests for PubMed E-Utilities request construction."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.src.fetchers.pubmed_fetcher import PubMedFetcher


class FakeResponse:
    def __init__(self, content: bytes = b"<root />", status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        return self.responses.pop(0)


def test_pubmed_search_uses_single_esearch_request() -> None:
    fetcher = PubMedFetcher()
    fetcher._apply_rate_limit = lambda: None  # type: ignore[method-assign]
    fetcher.session = FakeSession(
        [
            FakeResponse(
                b"""
                <eSearchResult>
                  <Count>3</Count>
                  <IdList><Id>1</Id><Id>2</Id><Id>3</Id></IdList>
                </eSearchResult>
                """,
            ),
        ],
    )  # type: ignore[assignment]

    ids = fetcher._search_papers(
        datetime(2026, 1, 1),
        datetime(2026, 1, 7),
        ["amyloid"],
        brief_mode=True,
    )

    assert ids == ["1", "2", "3"]
    assert len(fetcher.session.calls) == 1
    params = fetcher.session.calls[0]["params"]
    assert params["retmax"] == 1000
    assert params["sort"] == "pub_date"
    assert "rettype" not in params
    assert fetcher._last_total_count == 3


def test_pubmed_details_use_250_id_batches_and_session() -> None:
    fetcher = PubMedFetcher()
    fetcher._apply_rate_limit = lambda: None  # type: ignore[method-assign]
    fetcher._parse_pubmed_response = (  # type: ignore[method-assign]
        lambda _content, batch_ids: [{"pmid": pmid} for pmid in batch_ids]
    )
    fetcher.session = FakeSession(
        [FakeResponse(), FakeResponse(), FakeResponse()]
    )  # type: ignore[assignment]

    papers = fetcher._fetch_paper_details([str(i) for i in range(501)])

    assert len(papers) == 501
    assert len(fetcher.session.calls) == 3
    batch_lengths = [
        len(call["params"]["id"].split(",")) for call in fetcher.session.calls
    ]
    assert batch_lengths == [250, 250, 1]

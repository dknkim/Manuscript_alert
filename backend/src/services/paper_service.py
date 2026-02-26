"""Core business logic — journal matching, scoring, fetch & rank."""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timedelta
from typing import Any

from backend.src.config import (
    arxiv_fetcher,
    biorxiv_fetcher,
    keyword_matcher,
    pubmed_fetcher,
    settings_service,
)


def load_settings() -> dict[str, Any]:
    return settings_service.load_settings()


def is_journal_excluded(journal_name: str, settings: dict[str, Any]) -> bool:
    if not journal_name:
        return False
    journal_lower: str = journal_name.lower()
    exclusion_patterns: list[str] | dict[str, list[str]] = settings.get(
        "journal_exclusions", []
    )
    if isinstance(exclusion_patterns, list):
        for pattern in exclusion_patterns:
            if pattern.lower() in journal_lower:
                return True
    else:
        for _category, patterns in exclusion_patterns.items():
            for pattern in patterns:
                if pattern.lower() in journal_lower:
                    return True
    return False


def get_journal_match_type(journal_name: str, settings: dict[str, Any]) -> str | None:
    if not journal_name:
        return None
    journal_lower: str = journal_name.lower().strip()
    if is_journal_excluded(journal_name, settings):
        return None
    target_patterns: dict[str, list[str]] = settings.get("target_journals", {})
    for exact_match in target_patterns.get("exact_matches", []):
        if journal_lower == exact_match.lower().strip():
            return "exact"
    for family_pattern in target_patterns.get("family_matches", []):
        if journal_lower.startswith(family_pattern.lower().strip()):
            return "family"
    for specific_journal in target_patterns.get("specific_journals", []):
        if specific_journal.lower().strip() in journal_lower:
            return "specific"
    return None


def is_high_impact_journal(journal_name: str, settings: dict[str, Any]) -> bool:
    return get_journal_match_type(journal_name, settings) is not None


def fetch_and_rank(
    settings: dict[str, Any],
    data_sources: dict[str, bool],
    search_mode: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Core fetch-and-rank logic (mirrors the old Streamlit cached version)."""
    keywords: list[str] = settings.get("keywords", [])
    search_settings: dict[str, Any] = settings.get("search_settings", {})
    days_back: int = search_settings.get("days_back", 7)

    end_date: datetime = datetime.now()
    start_date: datetime = end_date - timedelta(days=days_back)

    brief_mode: bool = search_mode.startswith("Brief")
    extended_mode: bool = search_mode.startswith("Extended")

    all_papers_data: list[dict[str, Any]] = []

    # ---- parallel fetch ----
    def _fetch_arxiv() -> tuple[str, list[dict[str, Any]] | str]:
        if data_sources.get("arxiv"):
            try:
                return (
                    "arxiv",
                    arxiv_fetcher.fetch_papers(
                        start_date, end_date, keywords, brief_mode, extended_mode
                    ),
                )
            except Exception as e:
                return ("arxiv_error", str(e))
        return ("arxiv", [])

    def _fetch_biorxiv() -> tuple[str, list[dict[str, Any]] | str]:
        if data_sources.get("biorxiv") or data_sources.get("medrxiv"):
            try:
                papers: list[dict[str, Any]] = biorxiv_fetcher.fetch_papers(
                    start_date, end_date, keywords, brief_mode, extended_mode
                )
                filtered: list[dict[str, Any]] = [
                    p
                    for p in papers
                    if (p.get("source") == "biorxiv" and data_sources.get("biorxiv"))
                    or (p.get("source") == "medrxiv" and data_sources.get("medrxiv"))
                ]
                return ("biorxiv", filtered)
            except Exception as e:
                return ("biorxiv_error", str(e))
        return ("biorxiv", [])

    def _fetch_pubmed() -> tuple[str, list[dict[str, Any]] | str]:
        if data_sources.get("pubmed"):
            try:
                return (
                    "pubmed",
                    pubmed_fetcher.fetch_papers(
                        start_date, end_date, keywords, brief_mode, extended_mode
                    ),
                )
            except Exception as e:
                return ("pubmed_error", str(e))
        return ("pubmed", [])

    errors: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fn) for fn in (_fetch_arxiv, _fetch_biorxiv, _fetch_pubmed)
        ]
        for future in concurrent.futures.as_completed(futures):
            rtype, rdata = future.result()
            if rtype.endswith("_error"):
                errors.append(f"{rtype.replace('_error', '')}: {rdata}")
            else:
                all_papers_data.extend(rdata)  # type: ignore[arg-type]

    if not all_papers_data:
        return [], errors

    # ---- rank ----
    keyword_scoring: dict[str, Any] = settings.get("keyword_scoring", {})
    journal_scoring: dict[str, Any] = settings.get("journal_scoring", {})

    def process_paper(paper: dict[str, Any]) -> dict[str, Any]:
        relevance_score: float
        matched_keywords: list[str]
        relevance_score, matched_keywords = keyword_matcher.calculate_relevance(
            paper, keywords, keyword_scoring
        )

        if (
            paper.get("source") == "PubMed"
            and paper.get("journal")
            and journal_scoring.get("enabled", True)
        ):
            match_type: str | None = get_journal_match_type(paper["journal"], settings)
            if match_type:
                base_boosts: dict[str, float] = {
                    "exact": 8.0,
                    "family": 6.0,
                    "specific": 5.0,
                }
                relevance_score += base_boosts.get(match_type, 0)
                boosts: dict[str, float] = journal_scoring.get(
                    "high_impact_journal_boost", {}
                )
                n: int = len(matched_keywords)
                if n >= 5:
                    relevance_score += boosts.get("5_or_more_keywords", 5.1)
                elif n >= 4:
                    relevance_score += boosts.get("4_keywords", 3.7)
                elif n >= 3:
                    relevance_score += boosts.get("3_keywords", 2.8)
                elif n >= 2:
                    relevance_score += boosts.get("2_keywords", 1.3)
                elif n >= 1:
                    relevance_score += boosts.get("1_keyword", 0.5)

        authors: list[str] | str = paper.get("authors", [])
        if isinstance(authors, list):
            authors_str: str = ", ".join(authors[:3]) + (
                "..." if len(authors) > 3 else ""
            )
        else:
            authors_str = str(authors)

        source: str = paper.get("source", "arXiv")
        source_map: dict[str, str] = {"PubMed": "PubMed", "arxiv": "arXiv"}
        source_display: str = source_map.get(source, source.capitalize())

        return {
            "title": paper["title"],
            "authors": authors_str,
            "abstract": paper["abstract"],
            "published": paper["published"],
            "url": paper.get("arxiv_url", ""),
            "source": source_display,
            "relevance_score": round(relevance_score, 1),
            "matched_keywords": matched_keywords,
            "journal": paper.get("journal", ""),
            "volume": paper.get("volume", ""),
            "issue": paper.get("issue", ""),
            "is_high_impact": (
                is_high_impact_journal(paper.get("journal", ""), settings)
                if paper.get("source") == "PubMed"
                else False
            ),
        }

    ranked: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futs = {executor.submit(process_paper, p): p for p in all_papers_data}
        for f in concurrent.futures.as_completed(futs):
            try:
                ranked.append(f.result())
            except Exception:
                continue

    ranked.sort(key=lambda p: p["relevance_score"], reverse=True)
    return ranked, errors

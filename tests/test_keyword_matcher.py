"""Tests for KeywordMatcher — keyword matching & relevance scoring."""

from __future__ import annotations

from typing import Any

from backend.src.processors.keyword_matcher import KeywordMatcher


def test_basic_keyword_match(sample_paper: dict[str, Any]) -> None:
    matcher = KeywordMatcher()
    score, matched = matcher.calculate_relevance(
        sample_paper,
        ["Alzheimer's disease", "PET", "MRI"],
    )
    assert score > 0
    assert "Alzheimer's disease" in matched
    assert "PET" in matched


def test_no_match() -> None:
    matcher = KeywordMatcher()
    paper = {
        "title": "Quantum computing advances",
        "abstract": "New qubit architectures for fault-tolerant computation.",
        "authors": ["Feynman R"],
        "pmid": "unrelated-1",
    }
    score, matched = matcher.calculate_relevance(paper, ["Alzheimer's disease", "PET"])
    assert score == 0.0
    assert matched == []


def test_keyword_scoring_priorities(sample_paper: dict[str, Any]) -> None:
    matcher = KeywordMatcher()
    scoring = {
        "high_priority": {
            "keywords": ["Alzheimer's disease"],
            "boost": 2.0,
        },
        "medium_priority": {
            "keywords": ["PET"],
            "boost": 1.5,
        },
    }
    score_with_boost, _ = matcher.calculate_relevance(
        sample_paper, ["Alzheimer's disease", "PET"], scoring
    )

    matcher2 = KeywordMatcher()
    score_no_boost, _ = matcher2.calculate_relevance(
        sample_paper, ["Alzheimer's disease", "PET"], None
    )

    assert score_with_boost > score_no_boost


def test_title_weighting(sample_paper: dict[str, Any]) -> None:
    """Keywords in the title get extra weight (title is tripled in searchable text)."""
    matcher = KeywordMatcher()
    # "Amyloid" is in the title of sample_paper
    score_title, _ = matcher.calculate_relevance(sample_paper, ["amyloid"])

    matcher2 = KeywordMatcher()
    # Paper where keyword is only in abstract
    paper_abstract_only = {
        "title": "A general review of neuroimaging",
        "abstract": "Amyloid accumulation was measured in patients.",
        "authors": [],
        "pmid": "title-test-1",
    }
    score_abstract, _ = matcher2.calculate_relevance(paper_abstract_only, ["amyloid"])

    assert score_title > score_abstract


def test_search_papers() -> None:
    matcher = KeywordMatcher()
    papers = [
        {
            "title": "Alzheimer PET study",
            "abstract": "Amyloid imaging results",
            "authors": [],
            "pmid": "s1",
        },
        {
            "title": "Cardiac MRI review",
            "abstract": "Heart imaging overview",
            "authors": [],
            "pmid": "s2",
        },
    ]
    results = matcher.search_papers(papers, "alzheimer")
    assert len(results) == 1
    assert results[0]["title"] == "Alzheimer PET study"


def test_search_papers_empty_query() -> None:
    matcher = KeywordMatcher()
    papers = [
        {"title": "Any paper", "abstract": "Content", "authors": [], "pmid": "sq1"},
    ]
    results = matcher.search_papers(papers, "")
    assert len(results) == 1


def test_keyword_statistics() -> None:
    matcher = KeywordMatcher()
    papers = [
        {
            "title": "Alzheimer tau study",
            "abstract": "Tau and amyloid",
            "authors": [],
            "pmid": "ks1",
        },
        {
            "title": "MRI review",
            "abstract": "Brain MRI techniques",
            "authors": [],
            "pmid": "ks2",
        },
    ]
    stats = matcher.get_keyword_statistics(papers, ["tau", "MRI", "amyloid"])
    assert stats["total_papers"] == 2
    assert stats["papers_with_matches"] == 2
    counts = stats["keyword_counts"]
    assert "tau" in counts
    assert "MRI" in counts


def test_empty_keyword_ignored() -> None:
    matcher = KeywordMatcher()
    paper = {"title": "Test", "abstract": "Content", "authors": [], "pmid": "ek1"}
    score, matched = matcher.calculate_relevance(paper, ["", "  "])
    assert score == 0.0
    assert matched == []

"""Keyword matching and relevance scoring for papers."""

from __future__ import annotations

import re


class KeywordMatcher:
    """Handles keyword matching and relevance scoring for papers."""

    def __init__(self) -> None:
        self.case_sensitive: bool = False
        self._compiled_patterns: dict[str, re.Pattern[str]] = {}
        self._text_cache: dict[object, str] = {}
        self._score_cache: dict[str, tuple[float, list[str]]] = {}

    def calculate_relevance(
        self,
        paper: dict[str, object],
        keywords: list[str],
        keyword_scoring: dict[str, object] | None = None,
    ) -> tuple[float, list[str]]:
        """
        Calculate relevance score for a paper based on keyword matches.

        Args:
            paper: Paper data with title, abstract, etc.
            keywords: List of keywords to match against
            keyword_scoring: Optional keyword priority scoring configuration

        Returns:
            Tuple of (relevance_score, matched_keywords)
        """
        scoring_key: str | int = ""
        if keyword_scoring:
            hp: dict[str, object] = keyword_scoring.get("high_priority", {})  # type: ignore[assignment]
            mp: dict[str, object] = keyword_scoring.get("medium_priority", {})  # type: ignore[assignment]
            scoring_key = hash(
                str(sorted(hp.get("keywords", [])))  # type: ignore[arg-type]
                + str(sorted(mp.get("keywords", [])))  # type: ignore[arg-type]
            )
        paper_id: object = (
            paper.get("pmid") or paper.get("arxiv_id") or paper.get("doi") or id(paper)
        )
        cache_key: str = f"{paper_id}_{hash(tuple(sorted(keywords)))}_{scoring_key}"

        if cache_key in self._score_cache:
            return self._score_cache[cache_key]

        searchable_text: str = self._prepare_searchable_text(paper)

        matched_keywords: list[str] = []
        keyword_counts: dict[str, int] = {}

        for keyword in keywords:
            matches: int = self._find_keyword_matches(searchable_text, keyword)
            if matches > 0:
                matched_keywords.append(keyword)
                keyword_counts[keyword] = matches

        relevance_score: float = self._calculate_score(
            keyword_counts, paper, keyword_scoring
        )

        result: tuple[float, list[str]] = (relevance_score, matched_keywords)
        self._score_cache[cache_key] = result
        return result

    def _prepare_searchable_text(self, paper: dict[str, object]) -> str:
        """Prepare combined text for keyword searching with caching."""
        paper_id: object = (
            paper.get("pmid") or paper.get("arxiv_id") or paper.get("doi") or id(paper)
        )

        if paper_id in self._text_cache:
            return self._text_cache[paper_id]

        title: str = str(paper.get("title", ""))
        abstract: str = str(paper.get("abstract", ""))
        authors: list[str] | str = paper.get("authors", [])  # type: ignore[assignment]
        categories: list[str] | str = paper.get("categories", [])  # type: ignore[assignment]

        text_components: list[str] = [
            title * 3,
            abstract,
            " ".join(authors) if isinstance(authors, list) else str(authors),
            " ".join(categories) if isinstance(categories, list) else str(categories),
        ]

        combined_text: str = " ".join(filter(None, text_components))

        if not self.case_sensitive:
            combined_text = combined_text.lower()

        self._text_cache[paper_id] = combined_text
        return combined_text

    def _find_keyword_matches(self, text: str, keyword: str) -> int:
        """Find and count keyword matches in text with caching."""
        if not keyword.strip():
            return 0

        search_keyword: str = keyword if self.case_sensitive else keyword.lower()

        pattern_key: str = search_keyword
        if pattern_key not in self._compiled_patterns:
            flags: int = 0 if self.case_sensitive else re.IGNORECASE
            if " " in search_keyword:
                self._compiled_patterns[pattern_key] = re.compile(
                    re.escape(search_keyword), flags
                )
            else:
                self._compiled_patterns[pattern_key] = re.compile(
                    r"\b" + re.escape(search_keyword) + r"\b", flags
                )

        matches: int = len(self._compiled_patterns[pattern_key].findall(text))

        if " " in search_keyword and matches == 0:
            if search_keyword in text:
                matches = 1

        return matches

    def _calculate_score(
        self,
        keyword_counts: dict[str, int],
        paper: dict[str, object],
        keyword_scoring: dict[str, object] | None = None,
    ) -> float:
        """Calculate overall relevance score with keyword priority boosts."""
        if not keyword_counts:
            return 0.0

        high_priority_keywords: set[str] = set()
        medium_priority_keywords: set[str] = set()
        high_priority_boost: float = 1.5
        medium_priority_boost: float = 1.2

        if keyword_scoring:
            high_priority_config: dict[str, object] = keyword_scoring.get(
                "high_priority", {}
            )  # type: ignore[assignment]
            medium_priority_config: dict[str, object] = keyword_scoring.get(
                "medium_priority", {}
            )  # type: ignore[assignment]
            high_priority_keywords = set(
                high_priority_config.get("keywords", [])  # type: ignore[arg-type]
            )
            medium_priority_keywords = set(
                medium_priority_config.get("keywords", [])  # type: ignore[arg-type]
            )
            high_priority_boost = float(
                high_priority_config.get("boost", 1.5)  # type: ignore[arg-type]
            )
            medium_priority_boost = float(
                medium_priority_config.get("boost", 1.2)  # type: ignore[arg-type]
            )

        base_score: float = 0.0
        occurrence_bonus: float = 0.0

        for keyword, count in keyword_counts.items():
            if keyword in high_priority_keywords:
                boost_multiplier: float = high_priority_boost
            elif keyword in medium_priority_keywords:
                boost_multiplier = medium_priority_boost
            else:
                boost_multiplier = 1.0

            base_score += 1.0 * boost_multiplier
            occurrence_bonus += min(count - 1, 2) * boost_multiplier

        title: str = str(paper.get("title", ""))
        if not self.case_sensitive:
            title = title.lower()

        title_bonus: float = 0.0
        for keyword in keyword_counts:
            search_keyword = keyword if self.case_sensitive else keyword.lower()
            if search_keyword in title or re.search(
                r"\b" + re.escape(search_keyword) + r"\b", title
            ):
                if keyword in high_priority_keywords:
                    title_bonus += 1.0 * high_priority_boost
                elif keyword in medium_priority_keywords:
                    title_bonus += 1.0 * medium_priority_boost
                else:
                    title_bonus += 1.0

        keyword_bonus: float = 0.0
        high_value_keywords: list[str] = ["pet", "mri"]
        for keyword in keyword_counts:
            keyword_lower: str = keyword.lower()
            if keyword_lower in high_value_keywords:
                if keyword in high_priority_keywords:
                    keyword_bonus += 0.5 * high_priority_boost
                elif keyword in medium_priority_keywords:
                    keyword_bonus += 0.5 * medium_priority_boost
                else:
                    keyword_bonus += 0.5

        final_score: float = (
            base_score + occurrence_bonus + (title_bonus * 0.2) + keyword_bonus
        )
        return round(final_score, 1)

    def search_papers(
        self, papers: list[dict[str, object]], search_query: str
    ) -> list[dict[str, object]]:
        """Search through papers using a query string."""
        if not search_query.strip():
            return papers

        search_terms: list[str] = search_query.lower().split()
        filtered_papers: list[dict[str, object]] = []

        for paper in papers:
            searchable_text: str = self._prepare_searchable_text(paper).lower()
            if all(term in searchable_text for term in search_terms):
                filtered_papers.append(paper)

        return filtered_papers

    def get_keyword_statistics(
        self, papers: list[dict[str, object]], keywords: list[str]
    ) -> dict[str, object]:
        """Generate statistics about keyword matches across papers."""
        stats: dict[str, object] = {
            "keyword_counts": {},
            "total_papers": len(papers),
            "papers_with_matches": 0,
        }

        papers_with_matches: set[int] = set()
        kw_counts: dict[str, int] = {}

        for paper in papers:
            _, matched_keywords = self.calculate_relevance(paper, keywords)
            if matched_keywords:
                papers_with_matches.add(id(paper))
                for keyword in matched_keywords:
                    kw_counts[keyword] = kw_counts.get(keyword, 0) + 1

        stats["keyword_counts"] = kw_counts
        stats["papers_with_matches"] = len(papers_with_matches)
        return stats

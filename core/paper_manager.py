"""Paper Manager — Core business logic for fetching and processing papers."""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timedelta

import pandas as pd

from fetchers.arxiv_fetcher import ArxivFetcher
from fetchers.biorxiv_fetcher import BioRxivFetcher
from fetchers.pubmed_fetcher import PubMedFetcher
from processors.keyword_matcher import KeywordMatcher


class PaperManager:
    """Handles paper fetching, ranking, and processing logic."""

    def __init__(self) -> None:
        self.keyword_matcher: KeywordMatcher = KeywordMatcher()
        self.arxiv_fetcher: ArxivFetcher = ArxivFetcher()
        self.biorxiv_fetcher: BioRxivFetcher = BioRxivFetcher()
        self.pubmed_fetcher: PubMedFetcher = PubMedFetcher()

    def fetch_and_rank_papers(
        self,
        keywords: list[str],
        days_back: int,
        data_sources: dict[str, bool],
        end_date: datetime | None = None,
        search_mode: str = "Standard",
    ) -> pd.DataFrame:
        """
        Fetch papers from multiple sources and rank them by keyword relevance.

        Args:
            keywords: List of keywords to search for.
            days_back: Number of days to search back.
            data_sources: Dictionary of source names and their active status.
            end_date: End date for search (defaults to now).
            search_mode: Search mode (Standard, Brief, Extended).

        Returns:
            DataFrame of ranked papers.
        """
        if end_date is None:
            end_date = datetime.now()
        start_date: datetime = end_date - timedelta(days=days_back)

        print(f"🔍 Starting paper fetch — Keywords: {keywords}")
        print(
            f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to "
            f"{end_date.strftime('%Y-%m-%d')}"
        )
        print(f"🔧 Sources: {[k for k, v in data_sources.items() if v]}")
        print(f"⚡ Mode: {search_mode}")

        brief_mode: bool = search_mode.startswith("Brief")
        extended_mode: bool = search_mode.startswith("Extended")

        print("🚀 Starting concurrent fetch from all sources...")
        all_papers_data: list[dict[str, object]] = self._fetch_all_sources(
            data_sources, start_date, end_date, keywords, brief_mode, extended_mode
        )

        if not all_papers_data:
            print("❌ No papers found from any source")
            return pd.DataFrame()

        print(f"📄 Retrieved {len(all_papers_data)} total papers")
        print("🧮 Processing and ranking papers...")

        ranked_papers: list[dict[str, object]] = self._process_and_rank_papers(
            all_papers_data, keywords
        )

        df: pd.DataFrame = pd.DataFrame(ranked_papers)
        df = df.sort_values("relevance_score", ascending=False)

        print(f"✅ Final result: {len(df)} ranked papers")
        return df

    def _fetch_all_sources(
        self,
        data_sources: dict[str, bool],
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool,
        extended_mode: bool,
    ) -> list[dict[str, object]]:
        """Fetch papers from all active sources concurrently."""
        all_papers_data: list[dict[str, object]] = []

        fetch_functions: dict[str, object] = {
            "arxiv": lambda: self._fetch_arxiv(
                data_sources, start_date, end_date, keywords, brief_mode, extended_mode
            ),
            "biorxiv": lambda: self._fetch_biorxiv(
                data_sources, start_date, end_date, keywords, brief_mode, extended_mode
            ),
            "pubmed": lambda: self._fetch_pubmed(
                data_sources, start_date, end_date, keywords, brief_mode, extended_mode
            ),
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures: list[concurrent.futures.Future[tuple[str, list[dict[str, object]] | str]]] = []
            for source, fetch_func in fetch_functions.items():
                if self._is_source_active(source, data_sources):
                    print(f"📡 Queuing {source.upper()} fetch...")
                    futures.append(executor.submit(fetch_func))  # type: ignore[arg-type]

            print(f"⏳ Waiting for {len(futures)} concurrent requests...")
            completed: int = 0
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                rtype, rdata = future.result()
                if rtype.endswith("_error"):
                    print(f"❌ {rtype}: {rdata}")
                else:
                    print(
                        f"✅ {rtype.upper()}: {len(rdata)} papers "  # type: ignore[arg-type]
                        f"({completed}/{len(futures)} sources complete)"
                    )
                    all_papers_data.extend(rdata)  # type: ignore[arg-type]

        return all_papers_data

    def _is_source_active(self, source: str, data_sources: dict[str, bool]) -> bool:
        """Check if a source is active."""
        if source == "biorxiv":
            return data_sources.get("biorxiv", False) or data_sources.get(
                "medrxiv", False
            )
        return data_sources.get(source, False)

    def _fetch_arxiv(
        self,
        data_sources: dict[str, bool],
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool,
        extended_mode: bool,
    ) -> tuple[str, list[dict[str, object]] | str]:
        """Fetch papers from arXiv."""
        if not data_sources.get("arxiv", False):
            return ("arxiv", [])
        try:
            print("📚 ARXIV: Starting fetch...")
            papers: list[dict[str, object]] = self.arxiv_fetcher.fetch_papers(
                start_date, end_date, keywords, brief_mode, extended_mode
            )
            print(f"📚 ARXIV: Completed, retrieved {len(papers)} papers")
            return ("arxiv", papers)
        except Exception as e:
            print(f"📚 ARXIV: Error — {e!s}")
            return ("arxiv_error", str(e))

    def _fetch_biorxiv(
        self,
        data_sources: dict[str, bool],
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool,
        extended_mode: bool,
    ) -> tuple[str, list[dict[str, object]] | str]:
        """Fetch papers from bioRxiv/medRxiv."""
        if not (
            data_sources.get("biorxiv", False) or data_sources.get("medrxiv", False)
        ):
            return ("biorxiv", [])
        try:
            print("🧬 BIORXIV/MEDRXIV: Starting fetch...")
            papers: list[dict[str, object]] = self.biorxiv_fetcher.fetch_papers(
                start_date, end_date, keywords, brief_mode, extended_mode
            )
            filtered_papers: list[dict[str, object]] = [
                p
                for p in papers
                if (p.get("source") == "biorxiv" and data_sources.get("biorxiv", False))
                or (
                    p.get("source") == "medrxiv" and data_sources.get("medrxiv", False)
                )
            ]
            print(
                f"🧬 BIORXIV/MEDRXIV: Completed, retrieved {len(filtered_papers)} papers"
            )
            return ("biorxiv", filtered_papers)
        except Exception as e:
            print(f"🧬 BIORXIV/MEDRXIV: Error — {e!s}")
            return ("biorxiv_error", str(e))

    def _fetch_pubmed(
        self,
        data_sources: dict[str, bool],
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool,
        extended_mode: bool,
    ) -> tuple[str, list[dict[str, object]] | str]:
        """Fetch papers from PubMed."""
        if not data_sources.get("pubmed", False):
            return ("pubmed", [])
        try:
            print("🩺 PUBMED: Starting fetch...")
            papers: list[dict[str, object]] = self.pubmed_fetcher.fetch_papers(
                start_date, end_date, keywords, brief_mode, extended_mode
            )
            print(f"🩺 PUBMED: Completed, retrieved {len(papers)} papers")
            return ("pubmed", papers)
        except Exception as e:
            print(f"🩺 PUBMED: Error — {e!s}")
            return ("pubmed_error", str(e))

    def _process_and_rank_papers(
        self,
        all_papers_data: list[dict[str, object]],
        keywords: list[str],
    ) -> list[dict[str, object]]:
        """Process papers and calculate relevance scores."""
        ranked_papers: list[dict[str, object]] = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_paper = {
                executor.submit(self._process_single_paper, paper, keywords): paper
                for paper in all_papers_data
            }
            for future in concurrent.futures.as_completed(future_to_paper):
                try:
                    paper_data: dict[str, object] | None = future.result()
                    if paper_data:
                        ranked_papers.append(paper_data)
                except Exception:
                    pass

        return ranked_papers

    def _process_single_paper(
        self,
        paper: dict[str, object],
        keywords: list[str],
    ) -> dict[str, object] | None:
        """Process a single paper and calculate its relevance score."""
        relevance_score: float
        matched_keywords: list[str]
        relevance_score, matched_keywords = self.keyword_matcher.calculate_relevance(
            paper, keywords
        )

        relevance_score = self._apply_journal_boost(
            paper, relevance_score, matched_keywords
        )

        authors_str: str = self._format_authors(paper.get("authors", []))  # type: ignore[arg-type]
        source_display: str = self._get_source_display_name(
            str(paper.get("source", ""))
        )

        return {
            "title": paper["title"],
            "abstract": paper["abstract"],
            "authors": authors_str,
            "published": paper["published"],
            "arxiv_url": paper.get("arxiv_url", ""),
            "source": source_display,
            "relevance_score": relevance_score,
            "matched_keywords": matched_keywords,
            "journal": paper.get("journal", ""),
            "volume": paper.get("volume", ""),
            "pages": paper.get("pages", ""),
            "doi": paper.get("doi", ""),
            "pmid": paper.get("pmid", ""),
        }

    def _apply_journal_boost(
        self,
        paper: dict[str, object],
        relevance_score: float,
        matched_keywords: list[str],
    ) -> float:
        """Apply score boost for high-impact journals."""
        if paper.get("source") == "PubMed" and paper.get("journal"):
            from utils.journal_utils import is_high_impact_journal

            if is_high_impact_journal(str(paper["journal"])):
                keyword_count: int = len(matched_keywords)
                if keyword_count >= 5:
                    relevance_score += 5.1
                elif keyword_count >= 4:
                    relevance_score += 3.7
                elif keyword_count >= 3:
                    relevance_score += 2.8
                elif keyword_count >= 2:
                    relevance_score += 1.3
        return relevance_score

    def _format_authors(self, authors: list[str] | str) -> str:
        """Format authors list for display."""
        if isinstance(authors, list) and authors:
            return ", ".join(authors[:5]) + (" et al." if len(authors) > 5 else "")
        return str(authors)

    def _get_source_display_name(self, source: str) -> str:
        """Get display name for a source."""
        display_names: dict[str, str] = {
            "PubMed": "PubMed",
            "arxiv": "arXiv",
            "biorxiv": "bioRxiv",
            "medrxiv": "medRxiv",
        }
        if source in display_names:
            return display_names[source]
        for key, value in display_names.items():
            if key.lower() == source.lower():
                return value
        return source.capitalize()

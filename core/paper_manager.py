"""Paper Manager - Core business logic for fetching and processing papers."""

import concurrent.futures
from datetime import datetime, timedelta

import pandas as pd

from fetchers.arxiv_fetcher import ArxivFetcher
from fetchers.biorxiv_fetcher import BioRxivFetcher
from fetchers.pubmed_fetcher import PubMedFetcher
from processors.keyword_matcher import KeywordMatcher


class PaperManager:
    """Handles paper fetching, ranking, and processing logic."""

    def __init__(self):
        self.keyword_matcher = KeywordMatcher()
        self.arxiv_fetcher = ArxivFetcher()
        self.biorxiv_fetcher = BioRxivFetcher()
        self.pubmed_fetcher = PubMedFetcher()

    def fetch_and_rank_papers(
        self,
        keywords: list[str],
        days_back: int,
        data_sources: dict[str, bool],
        end_date: datetime | None = None,
        search_mode: str = "Standard"
    ) -> pd.DataFrame:
        """
        Fetch papers from multiple sources and rank them by keyword relevance.
        
        Args:
            keywords: List of keywords to search for
            days_back: Number of days to search back
            data_sources: Dictionary of source names and their active status
            end_date: End date for search (defaults to now)
            search_mode: Search mode (Standard, Brief, Extended)
        
        Returns:
            DataFrame of ranked papers
        """
        if end_date is None:
            end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        print(f"🔍 Starting paper fetch - Keywords: {keywords}")
        print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"🔧 Sources: {[k for k, v in data_sources.items() if v]}")
        print(f"⚡ Mode: {search_mode}")

        # Set search limits based on mode
        brief_mode = search_mode.startswith("Brief")
        extended_mode = search_mode.startswith("Extended")

        # Fetch papers from all sources concurrently
        print("🚀 Starting concurrent fetch from all sources...")
        all_papers_data = self._fetch_all_sources(
            data_sources, start_date, end_date, keywords,
            brief_mode, extended_mode
        )

        if not all_papers_data:
            print("❌ No papers found from any source")
            return pd.DataFrame()

        print(f"📄 Retrieved {len(all_papers_data)} total papers")
        print("🧮 Processing and ranking papers...")

        # Process and rank papers
        ranked_papers = self._process_and_rank_papers(
            all_papers_data, keywords
        )

        # Convert to DataFrame and sort
        df = pd.DataFrame(ranked_papers)
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
        extended_mode: bool
    ) -> list[dict]:
        """Fetch papers from all active sources concurrently."""
        all_papers_data = []

        # Define fetching functions
        fetch_functions = {
            "arxiv": lambda: self._fetch_arxiv(
                data_sources, start_date, end_date, keywords,
                brief_mode, extended_mode
            ),
            "biorxiv": lambda: self._fetch_biorxiv(
                data_sources, start_date, end_date, keywords,
                brief_mode, extended_mode
            ),
            "pubmed": lambda: self._fetch_pubmed(
                data_sources, start_date, end_date, keywords,
                brief_mode, extended_mode
            )
        }

        # Execute all API calls in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            active_sources = []
            for source, fetch_func in fetch_functions.items():
                if self._is_source_active(source, data_sources):
                    print(f"📡 Queuing {source.upper()} fetch...")
                    futures.append(executor.submit(fetch_func))
                    active_sources.append(source)

            print(f"⏳ Waiting for {len(futures)} concurrent requests...")

            # Collect results
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                result_type, result_data = future.result()
                if result_type.endswith("_error"):
                    print(f"❌ {result_type}: {result_data}")
                else:
                    print(f"✅ {result_type.upper()}: {len(result_data)} papers ({completed}/{len(futures)} sources complete)")
                    all_papers_data.extend(result_data)

        return all_papers_data

    def _is_source_active(self, source: str, data_sources: dict[str, bool]) -> bool:
        """Check if a source is active."""
        if source == "biorxiv":
            return data_sources.get("biorxiv", False) or data_sources.get("medrxiv", False)
        return data_sources.get(source, False)

    def _fetch_arxiv(
        self, data_sources, start_date, end_date, keywords,
        brief_mode, extended_mode
    ) -> tuple[str, list[dict]]:
        """Fetch papers from arXiv."""
        if not data_sources.get("arxiv", False):
            return ("arxiv", [])

        try:
            print("📚 ARXIV: Starting fetch...")
            papers = self.arxiv_fetcher.fetch_papers(
                start_date, end_date, keywords, brief_mode, extended_mode
            )
            print(f"📚 ARXIV: Completed, retrieved {len(papers)} papers")
            return ("arxiv", papers)
        except Exception as e:
            print(f"📚 ARXIV: Error - {e!s}")
            return ("arxiv_error", str(e))

    def _fetch_biorxiv(
        self, data_sources, start_date, end_date, keywords,
        brief_mode, extended_mode
    ) -> tuple[str, list[dict]]:
        """Fetch papers from bioRxiv/medRxiv."""
        if not (data_sources.get("biorxiv", False) or data_sources.get("medrxiv", False)):
            return ("biorxiv", [])

        try:
            print("🧬 BIORXIV/MEDRXIV: Starting fetch...")
            papers = self.biorxiv_fetcher.fetch_papers(
                start_date, end_date, keywords, brief_mode, extended_mode
            )
            # Filter by source selection
            filtered_papers = []
            for paper in papers:
                source = paper.get("source", "")
                if (source == "biorxiv" and data_sources.get("biorxiv", False)) or \
                   (source == "medrxiv" and data_sources.get("medrxiv", False)):
                    filtered_papers.append(paper)
            print(f"🧬 BIORXIV/MEDRXIV: Completed, retrieved {len(filtered_papers)} papers")
            return ("biorxiv", filtered_papers)
        except Exception as e:
            print(f"🧬 BIORXIV/MEDRXIV: Error - {e!s}")
            return ("biorxiv_error", str(e))

    def _fetch_pubmed(
        self, data_sources, start_date, end_date, keywords,
        brief_mode, extended_mode
    ) -> tuple[str, list[dict]]:
        """Fetch papers from PubMed."""
        if not data_sources.get("pubmed", False):
            return ("pubmed", [])

        try:
            print("🩺 PUBMED: Starting fetch...")
            papers = self.pubmed_fetcher.fetch_papers(
                start_date, end_date, keywords, brief_mode, extended_mode
            )
            print(f"🩺 PUBMED: Completed, retrieved {len(papers)} papers")
            return ("pubmed", papers)
        except Exception as e:
            print(f"🩺 PUBMED: Error - {e!s}")
            return ("pubmed_error", str(e))

    def _process_and_rank_papers(
        self, all_papers_data: list[dict], keywords: list[str]
    ) -> list[dict]:
        """Process papers and calculate relevance scores."""
        ranked_papers = []

        # Process papers in parallel for ranking
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_paper = {
                executor.submit(self._process_single_paper, paper, keywords): paper
                for paper in all_papers_data
            }

            for future in concurrent.futures.as_completed(future_to_paper):
                try:
                    paper_data = future.result()
                    if paper_data:
                        ranked_papers.append(paper_data)
                except Exception:
                    pass  # Skip failed papers

        return ranked_papers

    def _process_single_paper(
        self, paper: dict, keywords: list[str]
    ) -> dict | None:
        """Process a single paper and calculate its relevance score."""
        relevance_score, matched_keywords = self.keyword_matcher.calculate_relevance(
            paper, keywords
        )

        # Boost score for high-impact journals
        relevance_score = self._apply_journal_boost(
            paper, relevance_score, matched_keywords
        )

        # Format authors
        authors_str = self._format_authors(paper.get("authors", []))

        # Get source display name
        source_display = self._get_source_display_name(paper.get("source", ""))

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
            "pmid": paper.get("pmid", "")
        }

    def _apply_journal_boost(
        self, paper: dict, relevance_score: float, matched_keywords: list[str]
    ) -> float:
        """Apply score boost for high-impact journals."""
        if paper.get("source") == "PubMed" and paper.get("journal"):
            from utils.journal_utils import is_high_impact_journal

            if is_high_impact_journal(paper["journal"]):
                keyword_count = len(matched_keywords)
                if keyword_count >= 5:
                    relevance_score += 5.1
                elif keyword_count >= 4:
                    relevance_score += 3.7
                elif keyword_count >= 3:
                    relevance_score += 2.8
                elif keyword_count >= 2:
                    relevance_score += 1.3

        return relevance_score

    def _format_authors(self, authors: list) -> str:
        """Format authors list for display."""
        if isinstance(authors, list) and authors:
            return ", ".join(authors[:5]) + (" et al." if len(authors) > 5 else "")
        return str(authors)

    def _get_source_display_name(self, source: str) -> str:
        """Get display name for a source."""
        display_names = {
            "PubMed": "PubMed",
            "arxiv": "arXiv",
            "biorxiv": "bioRxiv",
            "medrxiv": "medRxiv"
        }

        # Try exact match first
        if source in display_names:
            return display_names[source]

        # Try case-insensitive match
        for key, value in display_names.items():
            if key.lower() == source.lower():
                return value

        return source.capitalize()

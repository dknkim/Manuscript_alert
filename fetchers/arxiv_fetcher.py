"""Fetcher for arXiv papers via the arXiv API."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote

import requests

from utils.logger import Logger

logger: Logger = Logger(__name__)


class ArxivFetcher:
    """Handles fetching papers from arXiv API."""

    def __init__(self) -> None:
        self.base_url: str = "http://export.arxiv.org/api/query"
        self.max_results: int = 1000  # Balanced for speed and coverage

    def fetch_papers(
        self,
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool = False,
        extended_mode: bool = False,
    ) -> list[dict[str, object]]:
        """
        Fetch papers from arXiv API based on date range and keywords.

        Args:
            start_date: Start date for search
            end_date: End date for search
            keywords: List of keywords to search for
            brief_mode: If True, limit results for faster retrieval
            extended_mode: If True, fetch more results for comprehensive coverage

        Returns:
            List of paper dictionaries
        """
        # Build search query
        search_query: str = self._build_search_query(keywords, start_date, end_date)

        # Set max results based on mode
        if brief_mode:
            max_results = 500
        elif extended_mode:
            max_results = 5000
        else:
            max_results = self.max_results

        # Prepare API parameters
        params: dict[str, str | int] = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            response: requests.Response = requests.get(
                self.base_url, params=params, timeout=10
            )
            response.raise_for_status()

            papers: list[dict[str, object]] = self._parse_arxiv_response(
                response.content
            )
            filtered_papers: list[dict[str, object]] = self._filter_by_date(
                papers, start_date, end_date
            )
            return filtered_papers

        except requests.RequestException as e:
            logger.error(f"Error fetching papers from arXiv: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing arXiv response: {e}")
            return []

    def _build_search_query(
        self,
        keywords: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Build arXiv search query string."""
        keyword_queries: list[str] = []
        for keyword in keywords:
            _escaped_keyword: str = quote(keyword)
            keyword_query: str = f'(ti:"{keyword}" OR abs:"{keyword}")'
            keyword_queries.append(keyword_query)

        combined_query: str = " OR ".join(keyword_queries)
        date_query: str = (
            f'submittedDate:[{start_date.strftime("%Y%m%d")}0000 '
            f'TO {end_date.strftime("%Y%m%d")}2359]'
        )
        full_query: str = f"({combined_query}) AND {date_query}"
        return full_query

    def _parse_arxiv_response(
        self, xml_content: bytes
    ) -> list[dict[str, object]]:
        """Parse arXiv API XML response."""
        papers: list[dict[str, object]] = []

        try:
            root: ET.Element = ET.fromstring(xml_content)
            namespaces: dict[str, str] = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }
            entries: list[ET.Element] = root.findall("atom:entry", namespaces)

            for entry in entries:
                paper: dict[str, object] = {}

                # Title
                title_elem: ET.Element | None = entry.find("atom:title", namespaces)
                paper["title"] = self._clean_text(
                    title_elem.text if title_elem is not None else ""
                )

                # Abstract
                summary_elem: ET.Element | None = entry.find(
                    "atom:summary", namespaces
                )
                paper["abstract"] = self._clean_text(
                    summary_elem.text if summary_elem is not None else ""
                )

                # Authors
                authors: list[str] = []
                author_elems: list[ET.Element] = entry.findall(
                    "atom:author", namespaces
                )
                for author_elem in author_elems:
                    name_elem: ET.Element | None = author_elem.find(
                        "atom:name", namespaces
                    )
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())
                paper["authors"] = authors

                # Published date
                published_elem: ET.Element | None = entry.find(
                    "atom:published", namespaces
                )
                if published_elem is not None and published_elem.text:
                    paper["published"] = self._parse_date(published_elem.text)
                else:
                    paper["published"] = datetime.now().strftime("%Y-%m-%d")

                # arXiv URL
                id_elem: ET.Element | None = entry.find("atom:id", namespaces)
                if id_elem is not None and id_elem.text:
                    arxiv_id: str = id_elem.text
                    if arxiv_id.startswith("http://arxiv.org/abs/"):
                        paper["arxiv_url"] = arxiv_id.replace("http://", "https://")
                    elif not arxiv_id.startswith("https://"):
                        if "arxiv.org/abs/" in arxiv_id:
                            arxiv_number: str = arxiv_id.split("arxiv.org/abs/")[-1]
                            paper["arxiv_url"] = (
                                f"https://arxiv.org/abs/{arxiv_number}"
                            )
                        else:
                            paper["arxiv_url"] = arxiv_id
                    else:
                        paper["arxiv_url"] = arxiv_id
                else:
                    paper["arxiv_url"] = ""

                # Categories
                categories: list[str] = []
                category_elems: list[ET.Element] = entry.findall(
                    "atom:category", namespaces
                )
                for cat_elem in category_elems:
                    term: str | None = cat_elem.get("term")
                    if term:
                        categories.append(term)
                paper["categories"] = categories

                papers.append(paper)

        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
        except Exception as e:
            logger.error(f"Error extracting paper data: {e}")

        return papers

    def _clean_text(self, text: str | None) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text.strip())

    def _parse_date(self, date_string: str) -> str:
        """Parse date string to YYYY-MM-DD format."""
        try:
            dt: datetime = datetime.fromisoformat(
                date_string.replace("Z", "+00:00")
            )
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return datetime.now().strftime("%Y-%m-%d")

    def _filter_by_date(
        self,
        papers: list[dict[str, object]],
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, object]]:
        """Additional date filtering for papers."""
        filtered_papers: list[dict[str, object]] = []
        for paper in papers:
            try:
                paper_date: datetime = datetime.strptime(
                    str(paper["published"]), "%Y-%m-%d"
                )
                if start_date.date() <= paper_date.date() <= end_date.date():
                    filtered_papers.append(paper)
            except Exception:
                # If date parsing fails, include the paper
                filtered_papers.append(paper)
        return filtered_papers

"""Fetcher for bioRxiv and medRxiv papers via the bioRxiv API."""

from __future__ import annotations

import concurrent.futures
import time
from datetime import datetime, timedelta

import requests

from utils.logger import Logger

logger: Logger = Logger(__name__)


class BioRxivFetcher:
    """Handles fetching papers from bioRxiv and medRxiv APIs."""

    def __init__(self) -> None:
        self.biorxiv_base_url: str = "https://api.biorxiv.org/details/biorxiv"
        self.medrxiv_base_url: str = "https://api.biorxiv.org/details/medrxiv"
        self.max_results: int = 1000
        self.rate_limit_delay: float = 0.5
        self.last_request_time: float = 0
        self.consecutive_rate_limits: int = 0

    def fetch_papers(
        self,
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool = False,
        extended_mode: bool = False,
    ) -> list[dict[str, object]]:
        """Fetch papers from both bioRxiv and medRxiv in parallel."""
        args = (start_date, end_date, keywords, brief_mode, extended_mode)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_bio = executor.submit(self._fetch_from_server, "biorxiv", *args)
            future_med = executor.submit(self._fetch_from_server, "medrxiv", *args)
            biorxiv_papers = future_bio.result()
            medrxiv_papers = future_med.result()
        return biorxiv_papers + medrxiv_papers

    def _fetch_from_server(
        self,
        server: str,
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool = False,
        extended_mode: bool = False,
    ) -> list[dict[str, object]]:
        """Fetch papers from a single bioRxiv/medRxiv server."""
        papers: list[dict[str, object]] = []
        api_url: str = ""
        try:
            start_str: str = start_date.strftime("%Y-%m-%d")
            end_str: str = end_date.strftime("%Y-%m-%d")
            base_url: str = (
                self.biorxiv_base_url
                if server == "biorxiv"
                else self.medrxiv_base_url
            )
            api_url = f"{base_url}/{start_str}/{end_str}"
            response: requests.Response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            data: dict[str, object] = response.json()
            if data.get("collection"):
                raw_papers: list[dict[str, str]] = data["collection"]  # type: ignore[assignment]
                if brief_mode:
                    max_results = 500
                elif extended_mode:
                    max_results = 5000
                else:
                    max_results = self.max_results
                for i, paper in enumerate(raw_papers):
                    if i >= max_results:
                        break
                    if self._paper_matches_keywords(paper, keywords):
                        processed_paper: dict[str, object] = self._process_paper(
                            paper, server
                        )
                        papers.append(processed_paper)
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 429
            ):
                self.consecutive_rate_limits += 1
                logger.warning(
                    f"Rate limited by {server} (#{self.consecutive_rate_limits}): {e}"
                )
            else:
                logger.error(f"Error fetching papers from {server}: {e}")
            if api_url:
                logger.info(f"URL attempted: {api_url}")
        except Exception as e:
            logger.error(f"Error processing {server} response: {e}")
            if api_url:
                logger.info(f"URL attempted: {api_url}")
        return papers

    def _paper_matches_keywords(
        self, paper: dict[str, str], keywords: list[str]
    ) -> bool:
        """Check if a paper matches any of the given keywords."""
        if not keywords:
            return True
        searchable_text: str = ""
        if "title" in paper:
            searchable_text += paper["title"].lower() + " "
        if "abstract" in paper:
            searchable_text += paper["abstract"].lower() + " "
        if "authors" in paper:
            searchable_text += paper["authors"].lower() + " "
        for keyword in keywords:
            if keyword.lower() in searchable_text:
                return True
        return False

    def _process_paper(
        self, paper: dict[str, str], server: str
    ) -> dict[str, object]:
        """Process a raw paper dict into the standardised format."""
        processed: dict[str, object] = {
            "title": paper.get("title", "").strip(),
            "abstract": paper.get("abstract", "").strip(),
            "published": self._parse_date(paper.get("date", "")),
            "source": server,
            "doi": paper.get("doi", ""),
            "categories": [],
        }
        authors_str: str = paper.get("authors", "")
        if authors_str:
            authors: list[str] = [
                author.strip()
                for author in authors_str.split(",")
                if author.strip()
            ]
            processed["authors"] = authors
        else:
            processed["authors"] = []

        doi: str = str(processed.get("doi", ""))
        if doi:
            processed["arxiv_url"] = f"https://doi.org/{doi}"
        else:
            processed["arxiv_url"] = ""

        categories: list[str] = []
        if server == "biorxiv":
            categories.append("bioRxiv")
        else:
            categories.append("medRxiv")
        if "category" in paper:
            categories.append(paper["category"])
        processed["categories"] = categories

        return processed

    def _parse_date(self, date_string: str) -> str:
        """Parse a date string into YYYY-MM-DD format."""
        if not date_string:
            return datetime.now().strftime("%Y-%m-%d")
        try:
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    dt: datetime = datetime.strptime(date_string, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return datetime.now().strftime("%Y-%m-%d")
        except Exception:
            return datetime.now().strftime("%Y-%m-%d")

    def _apply_rate_limit(self) -> None:
        """Apply adaptive rate limiting — only delay if we made a recent request."""
        current_time: float = time.time()
        time_since_last: float = current_time - self.last_request_time

        adjusted_delay: float = self.rate_limit_delay * (
            1 + self.consecutive_rate_limits * 0.5
        )

        if time_since_last < adjusted_delay:
            sleep_time: float = adjusted_delay - time_since_last
            if self.consecutive_rate_limits > 0:
                logger.info(
                    f"BioRxiv: Using adjusted delay {adjusted_delay:.2f}s "
                    f"after {self.consecutive_rate_limits} rate limits"
                )
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_server_status(self) -> dict[str, bool]:
        """Check whether bioRxiv/medRxiv servers are reachable."""
        status: dict[str, bool] = {"biorxiv": False, "medrxiv": False}
        try:
            test_date: str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            url: str = f"{self.biorxiv_base_url}/{test_date}/{test_date}"
            response: requests.Response = requests.get(url, timeout=30)
            status["biorxiv"] = response.status_code == 200
        except Exception:
            pass
        try:
            test_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            url = f"{self.medrxiv_base_url}/{test_date}/{test_date}"
            response = requests.get(url, timeout=30)
            status["medrxiv"] = response.status_code == 200
        except Exception:
            pass
        return status

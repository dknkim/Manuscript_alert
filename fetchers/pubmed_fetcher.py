"""Fetcher for PubMed papers via the NCBI E-Utilities API."""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote

import requests

from utils.logger import Logger

logger: Logger = Logger(__name__)


class PubMedFetcher:
    """Handles fetching papers from PubMed API."""

    def __init__(self) -> None:
        self.base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.search_url: str = f"{self.base_url}/esearch.fcgi"
        self.fetch_url: str = f"{self.base_url}/efetch.fcgi"
        self.max_results: int = 2500
        self.rate_limit_delay: float = 0.34
        self.last_request_time: float = 0
        self.consecutive_rate_limits: int = 0
        self.last_rate_limit_time: float = 0
        self.cooldown_period: int = 60

    def fetch_papers(
        self,
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool = False,
        extended_mode: bool = False,
    ) -> list[dict[str, object]]:
        """Fetch papers from PubMed API."""
        try:
            logger.info("PubMed: Searching for papers...")
            paper_ids: list[str] = self._search_papers(
                start_date, end_date, keywords, brief_mode, extended_mode
            )
            if not paper_ids:
                logger.info("PubMed: No paper IDs found")
                return []
            logger.info(f"PubMed: Found {len(paper_ids)} paper IDs")
            papers: list[dict[str, object]] = self._fetch_paper_details(paper_ids)
            return papers
        except Exception as e:
            logger.error(f"Error fetching papers from PubMed: {e}")
            return []

    def _search_papers(
        self,
        start_date: datetime,
        end_date: datetime,
        keywords: list[str],
        brief_mode: bool = False,
        extended_mode: bool = False,
    ) -> list[str]:
        """Search PubMed and return matching paper IDs."""
        search_query: str = self._build_search_query(keywords, start_date, end_date)
        logger.info(f"PubMed query: {search_query}")

        count_params: dict[str, str] = {
            "db": "pubmed",
            "term": search_query,
            "rettype": "count",
            "tool": "scientific_alert_system",
            "email": "research@example.com",
        }

        actual_max: int
        try:
            logger.info("Getting search count...")
            count_response: requests.Response = requests.get(
                self.search_url, params=count_params, timeout=10
            )
            count_response.raise_for_status()
            count_root: ET.Element = ET.fromstring(count_response.content)
            count_elem: ET.Element | None = count_root.find("Count")
            total_count: int = (
                int(count_elem.text)
                if count_elem is not None and count_elem.text
                else 0
            )
            logger.info(f"Found {total_count} total papers in PubMed")

            if brief_mode:
                max_limit = 1000
            elif extended_mode:
                max_limit = 5000
            else:
                max_limit = self.max_results
            actual_max = min(total_count, max_limit)
            logger.info(f"Will fetch {actual_max} papers (limit: {max_limit})")
        except Exception as e:
            logger.warning(f"Error getting search count: {e}")
            if brief_mode:
                actual_max = 1000
            elif extended_mode:
                actual_max = 5000
            else:
                actual_max = self.max_results
            logger.info(f"Using fallback limit: {actual_max}")

        self._apply_rate_limit()

        params: dict[str, str | int] = {
            "db": "pubmed",
            "term": search_query,
            "retmax": actual_max,
            "retmode": "xml",
            "sort": "pub_date",
            "tool": "scientific_alert_system",
            "email": "research@example.com",
        }
        try:
            logger.info("Making PubMed search request...")
            response: requests.Response = requests.get(
                self.search_url, params=params, timeout=10
            )
            response.raise_for_status()
            logger.info("PubMed search response received")
            root: ET.Element = ET.fromstring(response.content)
            id_list: ET.Element | None = root.find("IdList")
            if id_list is not None:
                paper_ids: list[str] = [
                    id_elem.text
                    for id_elem in id_list.findall("Id")
                    if id_elem.text
                ]
                logger.info(f"Extracted {len(paper_ids)} paper IDs")
                return paper_ids
            logger.info("No IdList found in response")
            return []
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return []

    def _build_search_query(
        self,
        keywords: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Build a PubMed search query string."""
        keyword_queries: list[str] = []
        for keyword in keywords:
            _escaped_keyword: str = quote(keyword)
            keyword_query: str = (
                f'("{keyword}"[Title/Abstract] OR "{keyword}"[MeSH Terms])'
            )
            keyword_queries.append(keyword_query)
        combined_query: str = " OR ".join(keyword_queries)
        start_str: str = start_date.strftime("%Y/%m/%d")
        end_str: str = end_date.strftime("%Y/%m/%d")
        date_query: str = (
            f'("{start_str}"[Date - Publication] : "{end_str}"[Date - Publication])'
        )
        full_query: str = f"({combined_query}) AND {date_query}"
        return full_query

    def _fetch_paper_details(
        self, paper_ids: list[str]
    ) -> list[dict[str, object]]:
        """Fetch full details for a list of PubMed paper IDs."""
        if not paper_ids:
            logger.info("No paper IDs to fetch details for")
            return []

        logger.info(f"Starting to fetch details for {len(paper_ids)} papers...")
        all_papers: list[dict[str, object]] = []
        batch_size: int = 100
        total_batches: int = (len(paper_ids) + batch_size - 1) // batch_size
        logger.info(
            f"Will process {total_batches} batches of {batch_size} papers each"
        )

        for i in range(0, len(paper_ids), batch_size):
            batch_num: int = (i // batch_size) + 1
            batch_ids: list[str] = paper_ids[i : i + batch_size]
            logger.info(
                f"Processing batch {batch_num}/{total_batches} "
                f"({len(batch_ids)} papers)..."
            )
            id_string: str = ",".join(batch_ids)
            params: dict[str, str] = {
                "db": "pubmed",
                "id": id_string,
                "retmode": "xml",
                "tool": "scientific_alert_system",
                "email": "research@example.com",
            }

            max_retries: int = 3
            for retry in range(max_retries):
                try:
                    self._apply_rate_limit()
                    response: requests.Response = requests.get(
                        self.fetch_url, params=params, timeout=10
                    )
                    response.raise_for_status()
                    batch_papers: list[dict[str, object]] = (
                        self._parse_pubmed_response(response.content, batch_ids)
                    )
                    all_papers.extend(batch_papers)

                    if self.consecutive_rate_limits > 0:
                        logger.info(
                            "Successful request - resetting rate limit counter"
                        )
                        self.consecutive_rate_limits = max(
                            0, self.consecutive_rate_limits - 1
                        )
                    logger.info(
                        f"Batch {batch_num}/{total_batches} completed - "
                        f"got {len(batch_papers)} papers (total: {len(all_papers)})"
                    )
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        self.consecutive_rate_limits += 1
                        self.last_rate_limit_time = time.time()
                        base_wait: float = self.rate_limit_delay * (2**retry) * 2
                        jitter: float = base_wait * 0.1 * (
                            0.5 + (hash(str(time.time())) % 100) / 100
                        )
                        wait_time: float = base_wait + jitter
                        logger.warning(
                            f"Rate limited by PubMed "
                            f"(#{self.consecutive_rate_limits}). "
                            f"Waiting {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"HTTP error fetching PubMed batch "
                            f"{i // batch_size + 1}: {e}"
                        )
                        break
                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                ) as e:
                    if retry < max_retries - 1:
                        wait_times: list[int] = [3, 10, 30]
                        wait_time_int: int = wait_times[
                            min(retry, len(wait_times) - 1)
                        ]
                        logger.warning(
                            f"Connection error for PubMed batch "
                            f"{i // batch_size + 1}. "
                            f"Retrying in {wait_time_int}s..."
                        )
                        time.sleep(wait_time_int)
                    else:
                        logger.error(
                            f"Connection failed for PubMed batch "
                            f"{i // batch_size + 1} "
                            f"after {max_retries} attempts: {e}"
                        )
                        break
                except Exception as e:
                    logger.error(
                        f"Unexpected error fetching PubMed batch "
                        f"{i // batch_size + 1}: {e}"
                    )
                    break
        return all_papers

    def _parse_pubmed_response(
        self,
        xml_content: bytes,
        batch_ids: list[str] | None = None,
    ) -> list[dict[str, object]]:
        """Parse a PubMed XML response into paper dicts."""
        papers: list[dict[str, object]] = []
        try:
            root: ET.Element = ET.fromstring(xml_content)
            articles: list[ET.Element] = root.findall(".//PubmedArticle")
            for article in articles:
                paper: dict[str, object] | None = self._extract_paper_info(article)
                if paper:
                    papers.append(paper)
        except ET.ParseError as e:
            logger.error(f"Error parsing PubMed XML: {e}")
        except Exception as e:
            logger.error(f"Error extracting PubMed paper data: {e}")
        return papers

    def _extract_paper_info(
        self, article: ET.Element
    ) -> dict[str, object] | None:
        """Extract structured paper info from a PubMed XML article."""
        try:
            paper: dict[str, object] = {}
            medline_citation: ET.Element | None = article.find("MedlineCitation")
            if medline_citation is None:
                return None
            article_elem: ET.Element | None = medline_citation.find("Article")
            if article_elem is None:
                return None

            # Title
            title_elem: ET.Element | None = article_elem.find("ArticleTitle")
            paper["title"] = self._clean_text(
                title_elem.text if title_elem is not None else ""
            )

            # Abstract
            abstract_elem: ET.Element | None = article_elem.find(
                "Abstract/AbstractText"
            )
            paper["abstract"] = (
                self._clean_text(abstract_elem.text or "")
                if abstract_elem is not None
                else ""
            )

            # Authors
            authors: list[str] = []
            author_list: ET.Element | None = article_elem.find("AuthorList")
            if author_list is not None:
                for author in author_list.findall("Author"):
                    last_name: ET.Element | None = author.find("LastName")
                    first_name: ET.Element | None = author.find("ForeName")
                    if last_name is not None and first_name is not None:
                        full_name: str = f"{first_name.text} {last_name.text}"
                        authors.append(full_name)
                    elif last_name is not None and last_name.text:
                        authors.append(last_name.text)
            paper["authors"] = authors

            # Journal info
            journal_name: str = ""
            volume: str = ""
            issue: str = ""
            journal: ET.Element | None = article_elem.find("Journal")
            if journal is not None:
                journal_title: ET.Element | None = journal.find("Title")
                if journal_title is not None and journal_title.text:
                    journal_name = journal_title.text
                else:
                    iso_abbrev: ET.Element | None = journal.find("ISOAbbreviation")
                    if iso_abbrev is not None and iso_abbrev.text:
                        journal_name = iso_abbrev.text
                journal_issue: ET.Element | None = journal.find("JournalIssue")
                if journal_issue is not None:
                    vol_elem: ET.Element | None = journal_issue.find("Volume")
                    issue_elem: ET.Element | None = journal_issue.find("Issue")
                    volume = (
                        vol_elem.text
                        if vol_elem is not None and vol_elem.text
                        else ""
                    )
                    issue = (
                        issue_elem.text
                        if issue_elem is not None and issue_elem.text
                        else ""
                    )
            if not journal_name:
                medline_ta: ET.Element | None = medline_citation.find(
                    "MedlineJournalInfo/MedlineTA"
                )
                if medline_ta is not None and medline_ta.text:
                    journal_name = medline_ta.text
            paper["journal"] = journal_name
            paper["volume"] = volume
            paper["issue"] = issue

            # Published date
            pub_date: ET.Element | None = article_elem.find(
                "Journal/JournalIssue/PubDate"
            )
            if pub_date is not None:
                paper["published"] = self._parse_pubmed_date(pub_date)
            else:
                paper["published"] = datetime.now().strftime("%Y-%m-%d")

            # PMID + URL
            pmid_elem: ET.Element | None = medline_citation.find("PMID")
            if pmid_elem is not None and pmid_elem.text:
                pmid: str = pmid_elem.text
                paper["pmid"] = pmid
                paper["arxiv_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            else:
                paper["pmid"] = ""
                paper["arxiv_url"] = ""

            # DOI
            doi_elem: ET.Element | None = article_elem.find(
                './/ELocationID[@EIdType="doi"]'
            )
            paper["doi"] = doi_elem.text if doi_elem is not None else ""

            paper["source"] = "PubMed"
            paper["categories"] = ["PubMed"]

            # MeSH terms
            mesh_list: ET.Element | None = medline_citation.find("MeshHeadingList")
            if mesh_list is not None:
                mesh_terms: list[str] = []
                for mesh_heading in mesh_list.findall("MeshHeading"):
                    descriptor: ET.Element | None = mesh_heading.find(
                        "DescriptorName"
                    )
                    if descriptor is not None and descriptor.text:
                        mesh_terms.append(descriptor.text)
                categories_list: list[str] = paper.get("categories", [])  # type: ignore[assignment]
                categories_list.extend(mesh_terms[:5])

            return paper
        except Exception as e:
            logger.error(f"Error extracting paper info: {e}")
            return None

    def _clean_text(self, text: str | None) -> str:
        """Strip HTML tags and normalise whitespace."""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text.strip())
        return text

    def _parse_pubmed_date(self, pub_date: ET.Element) -> str:
        """Parse a PubMed PubDate element into YYYY-MM-DD."""
        try:
            year_elem: ET.Element | None = pub_date.find("Year")
            month_elem: ET.Element | None = pub_date.find("Month")
            day_elem: ET.Element | None = pub_date.find("Day")

            year_raw: str | int = (
                year_elem.text if year_elem is not None and year_elem.text else str(datetime.now().year)
            )
            month_raw: str = (
                month_elem.text if month_elem is not None and month_elem.text else "1"
            )
            day_raw: str = (
                day_elem.text if day_elem is not None and day_elem.text else "1"
            )

            month_map: dict[str, str] = {
                "Jan": "1", "Feb": "2", "Mar": "3", "Apr": "4",
                "May": "5", "Jun": "6", "Jul": "7", "Aug": "8",
                "Sep": "9", "Oct": "10", "Nov": "11", "Dec": "12",
            }
            if month_raw in month_map:
                month_raw = month_map[month_raw]

            year: int = int(year_raw) if str(year_raw).isdigit() else datetime.now().year
            month: int = int(month_raw) if str(month_raw).isdigit() else 1
            day: int = int(day_raw) if str(day_raw).isdigit() else 1
            if month > 12:
                month = 12
            if day > 31:
                day = 1

            date_obj: datetime = datetime(year, month, day)
            return date_obj.strftime("%Y-%m-%d")
        except Exception:
            return datetime.now().strftime("%Y-%m-%d")

    def _apply_rate_limit(self) -> None:
        """Apply adaptive rate limiting with exponential backoff and cooldown."""
        current_time: float = time.time()
        adjusted_delay: float

        if self.consecutive_rate_limits > 0:
            time_since_rate_limit: float = current_time - self.last_rate_limit_time
            if time_since_rate_limit < self.cooldown_period:
                adjusted_delay = self.rate_limit_delay * (
                    1 + self.consecutive_rate_limits
                )
                logger.info(
                    f"In cooldown period ({time_since_rate_limit:.1f}s/"
                    f"{self.cooldown_period}s), using {adjusted_delay:.2f}s delay"
                )
            else:
                logger.info(
                    "Cooldown period expired, resuming normal rate limiting"
                )
                self.consecutive_rate_limits = 0
                adjusted_delay = self.rate_limit_delay
        else:
            adjusted_delay = self.rate_limit_delay

        time_since_last: float = current_time - self.last_request_time
        if time_since_last < adjusted_delay:
            sleep_time: float = adjusted_delay - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_api_status(self) -> bool:
        """Check whether the PubMed API is reachable."""
        try:
            params: dict[str, str | int] = {
                "db": "pubmed",
                "term": "cancer",
                "retmax": 1,
                "tool": "scientific_alert_system",
                "email": "research@example.com",
            }
            response: requests.Response = requests.get(
                self.search_url, params=params, timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False

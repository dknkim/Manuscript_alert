import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
from urllib.parse import quote

class PubMedFetcher:
    """Handles fetching papers from PubMed API"""
    
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.search_url = f"{self.base_url}/esearch.fcgi"
        self.fetch_url = f"{self.base_url}/efetch.fcgi"
        self.max_results = 2500
        self.rate_limit_delay = 0.03
    
    def fetch_papers(self, start_date, end_date, keywords, brief_mode=False, extended_mode=False):
        try:
            paper_ids = self._search_papers(start_date, end_date, keywords, brief_mode, extended_mode)
            if not paper_ids:
                return []
            time.sleep(self.rate_limit_delay)
            papers = self._fetch_paper_details(paper_ids)
            return papers
        except Exception as e:
            print(f"Error fetching papers from PubMed: {e}")
            return []
    
    def _search_papers(self, start_date, end_date, keywords, brief_mode=False, extended_mode=False):
        search_query = self._build_search_query(keywords, start_date, end_date)
        count_params = {
            'db': 'pubmed',
            'term': search_query,
            'rettype': 'count',
            'tool': 'scientific_alert_system',
            'email': 'research@example.com'
        }
        try:
            count_response = requests.get(self.search_url, params=count_params, timeout=10)
            count_response.raise_for_status()
            count_root = ET.fromstring(count_response.content)
            count_elem = count_root.find('Count')
            total_count = int(count_elem.text) if count_elem is not None and count_elem.text else 0
            if brief_mode:
                max_limit = 1000
            elif extended_mode:
                max_limit = 5000
            else:
                max_limit = self.max_results
            actual_max = min(total_count, max_limit)
        except:
            if brief_mode:
                actual_max = 1000
            elif extended_mode:
                actual_max = 5000
            else:
                actual_max = self.max_results
        time.sleep(self.rate_limit_delay)
        params = {
            'db': 'pubmed',
            'term': search_query,
            'retmax': actual_max,
            'retmode': 'xml',
            'sort': 'pub_date',
            'tool': 'scientific_alert_system',
            'email': 'research@example.com'
        }
        try:
            response = requests.get(self.search_url, params=params, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            id_list = root.find('IdList')
            if id_list is not None:
                paper_ids = [id_elem.text for id_elem in id_list.findall('Id') if id_elem.text]
                return paper_ids
            return []
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    def _build_search_query(self, keywords, start_date, end_date):
        keyword_queries = []
        for keyword in keywords:
            escaped_keyword = quote(keyword)
            keyword_query = f'("{keyword}"[Title/Abstract] OR "{keyword}"[MeSH Terms])'
            keyword_queries.append(keyword_query)
        combined_query = " OR ".join(keyword_queries)
        start_str = start_date.strftime('%Y/%m/%d')
        end_str = end_date.strftime('%Y/%m/%d')
        date_query = f'("{start_str}"[Date - Publication] : "{end_str}"[Date - Publication])'
        full_query = f'({combined_query}) AND {date_query}'
        return full_query
    
    def _fetch_paper_details(self, paper_ids):
        if not paper_ids:
            return []
        all_papers = []
        batch_size = 200
        for i in range(0, len(paper_ids), batch_size):
            batch_ids = paper_ids[i:i + batch_size]
            id_string = ",".join(batch_ids)
            params = {
                'db': 'pubmed',
                'id': id_string,
                'retmode': 'xml',
                'tool': 'scientific_alert_system',
                'email': 'research@example.com'
            }
            try:
                time.sleep(self.rate_limit_delay)
                response = requests.get(self.fetch_url, params=params, timeout=10)
                response.raise_for_status()
                batch_papers = self._parse_pubmed_response(response.content, batch_ids)
                all_papers.extend(batch_papers)
            except Exception as e:
                print(f"Error fetching PubMed paper details for batch {i//batch_size + 1}: {e}")
                continue
        return all_papers
    
    def _parse_pubmed_response(self, xml_content, batch_ids=None):
        papers = []
        try:
            root = ET.fromstring(xml_content)
            articles = root.findall('.//PubmedArticle')
            for article in articles:
                paper = self._extract_paper_info(article)
                if paper:
                    papers.append(paper)
        except ET.ParseError as e:
            print(f"Error parsing PubMed XML: {e}")
        except Exception as e:
            print(f"Error extracting PubMed paper data: {e}")
        return papers
    
    def _extract_paper_info(self, article):
        try:
            paper = {}
            medline_citation = article.find('MedlineCitation')
            if medline_citation is None:
                return None
            article_elem = medline_citation.find('Article')
            if article_elem is None:
                return None
            title_elem = article_elem.find('ArticleTitle')
            paper['title'] = self._clean_text(title_elem.text if title_elem is not None else "")
            abstract_elem = article_elem.find('Abstract/AbstractText')
            if abstract_elem is not None:
                paper['abstract'] = self._clean_text(abstract_elem.text or "")
            else:
                paper['abstract'] = ""
            authors = []
            author_list = article_elem.find('AuthorList')
            if author_list is not None:
                for author in author_list.findall('Author'):
                    last_name = author.find('LastName')
                    first_name = author.find('ForeName')
                    if last_name is not None and first_name is not None:
                        full_name = f"{first_name.text} {last_name.text}"
                        authors.append(full_name)
                    elif last_name is not None:
                        authors.append(last_name.text)
            paper['authors'] = authors
            journal_name = ""
            volume = ""
            issue = ""
            journal = article_elem.find('Journal')
            if journal is not None:
                journal_title = journal.find('Title')
                if journal_title is not None and journal_title.text:
                    journal_name = journal_title.text
                else:
                    iso_abbrev = journal.find('ISOAbbreviation') 
                    if iso_abbrev is not None and iso_abbrev.text:
                        journal_name = iso_abbrev.text
                journal_issue = journal.find('JournalIssue')
                if journal_issue is not None:
                    vol_elem = journal_issue.find('Volume')
                    issue_elem = journal_issue.find('Issue')
                    volume = vol_elem.text if vol_elem is not None and vol_elem.text else ""
                    issue = issue_elem.text if issue_elem is not None and issue_elem.text else ""
            if not journal_name:
                medline_ta = medline_citation.find('MedlineJournalInfo/MedlineTA')
                if medline_ta is not None and medline_ta.text:
                    journal_name = medline_ta.text
            paper['journal'] = journal_name
            paper['volume'] = volume
            paper['issue'] = issue
            pub_date = article_elem.find('Journal/JournalIssue/PubDate')
            if pub_date is not None:
                paper['published'] = self._parse_pubmed_date(pub_date)
            else:
                paper['published'] = datetime.now().strftime('%Y-%m-%d')
            pmid_elem = medline_citation.find('PMID')
            if pmid_elem is not None:
                pmid = pmid_elem.text
                paper['pmid'] = pmid
                paper['arxiv_url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            else:
                paper['pmid'] = ""
                paper['arxiv_url'] = ""
            doi_elem = article_elem.find('.//ELocationID[@EIdType="doi"]')
            if doi_elem is not None:
                paper['doi'] = doi_elem.text
            else:
                paper['doi'] = ""
            paper['source'] = 'PubMed'
            paper['categories'] = ['PubMed']
            mesh_list = medline_citation.find('MeshHeadingList')
            if mesh_list is not None:
                mesh_terms = []
                for mesh_heading in mesh_list.findall('MeshHeading'):
                    descriptor = mesh_heading.find('DescriptorName')
                    if descriptor is not None:
                        mesh_terms.append(descriptor.text)
                paper['categories'].extend(mesh_terms[:5])
            return paper
        except Exception as e:
            print(f"Error extracting paper info: {e}")
            return None
    
    def _clean_text(self, text):
        if not text:
            return ""
        import re
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def _parse_pubmed_date(self, pub_date):
        try:
            year_elem = pub_date.find('Year')
            month_elem = pub_date.find('Month')
            day_elem = pub_date.find('Day')
            year = year_elem.text if year_elem is not None else datetime.now().year
            month = month_elem.text if month_elem is not None else "1"
            day = day_elem.text if day_elem is not None else "1"
            month_map = {
                'Jan': '1', 'Feb': '2', 'Mar': '3', 'Apr': '4',
                'May': '5', 'Jun': '6', 'Jul': '7', 'Aug': '8',
                'Sep': '9', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
            if month in month_map:
                month = month_map[month]
            year = int(year) if str(year).isdigit() else datetime.now().year
            month = int(month) if str(month).isdigit() else 1
            day = int(day) if str(day).isdigit() else 1
            if month > 12:
                month = 12
            if day > 31:
                day = 1
            date_obj = datetime(year, month, day)
            return date_obj.strftime('%Y-%m-%d')
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')
    
    def get_api_status(self):
        try:
            params = {
                'db': 'pubmed',
                'term': 'cancer',
                'retmax': 1,
                'tool': 'scientific_alert_system',
                'email': 'research@example.com'
            }
            response = requests.get(self.search_url, params=params, timeout=10)
            return response.status_code == 200
        except Exception:
            return False



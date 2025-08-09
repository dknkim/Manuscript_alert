import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from urllib.parse import quote

class ArxivFetcher:
    """Handles fetching papers from arXiv API"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.max_results = 1000  # Balanced for speed and coverage
    
    def fetch_papers(self, start_date, end_date, keywords, brief_mode=False, extended_mode=False):
        """
        Fetch papers from arXiv API based on date range and keywords
        
        Args:
            start_date (datetime): Start date for search
            end_date (datetime): End date for search
            keywords (list): List of keywords to search for
            
        Returns:
            list: List of paper dictionaries
        """
        
        # Build search query
        search_query = self._build_search_query(keywords, start_date, end_date)
        
        # Set max results based on mode
        if brief_mode:
            max_results = 500
        elif extended_mode:
            max_results = 5000
        else:
            max_results = self.max_results
        
        # Prepare API parameters
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse XML response
            papers = self._parse_arxiv_response(response.content)
            
            # Filter by date (additional filtering as arXiv search might be imprecise)
            filtered_papers = self._filter_by_date(papers, start_date, end_date)
            
            return filtered_papers
            
        except requests.RequestException as e:
            print(f"Error fetching papers from arXiv: {e}")
            return []
        except Exception as e:
            print(f"Error processing arXiv response: {e}")
            return []
    
    def _build_search_query(self, keywords, start_date, end_date):
        """Build arXiv search query string"""
        
        # Create OR query for keywords in title, abstract, or categories
        keyword_queries = []
        for keyword in keywords:
            # Escape special characters and build query
            escaped_keyword = quote(keyword)
            keyword_query = f'(ti:"{keyword}" OR abs:"{keyword}")'
            keyword_queries.append(keyword_query)
        
        # Combine all keyword queries with OR
        combined_query = " OR ".join(keyword_queries)
        
        # Add date range (arXiv uses YYYYMMDD format)
        date_query = f'submittedDate:[{start_date.strftime("%Y%m%d")}0000 TO {end_date.strftime("%Y%m%d")}2359]'
        
        # Combine keyword and date queries
        full_query = f'({combined_query}) AND {date_query}'
        
        return full_query
    
    def _parse_arxiv_response(self, xml_content):
        """Parse arXiv API XML response"""
        
        papers = []
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Extract entries (papers)
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                paper = {}
                
                # Title
                title_elem = entry.find('atom:title', namespaces)
                paper['title'] = self._clean_text(title_elem.text if title_elem is not None else "")
                
                # Abstract
                summary_elem = entry.find('atom:summary', namespaces)
                paper['abstract'] = self._clean_text(summary_elem.text if summary_elem is not None else "")
                
                # Authors
                authors = []
                author_elems = entry.findall('atom:author', namespaces)
                for author_elem in author_elems:
                    name_elem = author_elem.find('atom:name', namespaces)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())
                paper['authors'] = authors
                
                # Published date
                published_elem = entry.find('atom:published', namespaces)
                if published_elem is not None:
                    paper['published'] = self._parse_date(published_elem.text)
                else:
                    paper['published'] = datetime.now().strftime('%Y-%m-%d')
                
                # arXiv URL
                id_elem = entry.find('atom:id', namespaces)
                if id_elem is not None and id_elem.text:
                    arxiv_id = id_elem.text
                    # Ensure the URL is properly formatted
                    if arxiv_id.startswith('http://arxiv.org/abs/'):
                        paper['arxiv_url'] = arxiv_id.replace('http://', 'https://')
                    elif not arxiv_id.startswith('https://'):
                        # Extract arXiv ID and construct proper URL
                        if 'arxiv.org/abs/' in arxiv_id:
                            arxiv_number = arxiv_id.split('arxiv.org/abs/')[-1]
                            paper['arxiv_url'] = f"https://arxiv.org/abs/{arxiv_number}"
                        else:
                            paper['arxiv_url'] = arxiv_id
                    else:
                        paper['arxiv_url'] = arxiv_id
                else:
                    paper['arxiv_url'] = ""
                
                # Categories
                categories = []
                category_elems = entry.findall('atom:category', namespaces)
                for cat_elem in category_elems:
                    term = cat_elem.get('term')
                    if term:
                        categories.append(term)
                paper['categories'] = categories
                
                papers.append(paper)
                
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
        except Exception as e:
            print(f"Error extracting paper data: {e}")
        
        return papers
    
    def _clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def _parse_date(self, date_string):
        """Parse date string to YYYY-MM-DD format"""
        try:
            # arXiv dates are in ISO format
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _filter_by_date(self, papers, start_date, end_date):
        """Additional date filtering for papers"""
        filtered_papers = []
        
        for paper in papers:
            try:
                paper_date = datetime.strptime(paper['published'], '%Y-%m-%d')
                if start_date.date() <= paper_date.date() <= end_date.date():
                    filtered_papers.append(paper)
            except:
                # If date parsing fails, include the paper
                filtered_papers.append(paper)
        
        return filtered_papers



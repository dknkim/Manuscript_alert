import requests
import json
from datetime import datetime, timedelta
import time

class BioRxivFetcher:
    """Handles fetching papers from bioRxiv and medRxiv APIs"""
    
    def __init__(self):
        self.biorxiv_base_url = "https://api.biorxiv.org/details/biorxiv"
        self.medrxiv_base_url = "https://api.biorxiv.org/details/medrxiv"
        self.max_results = 1000
        self.rate_limit_delay = 0.5
    
    def fetch_papers(self, start_date, end_date, keywords, brief_mode=False, extended_mode=False):
        all_papers = []
        biorxiv_papers = self._fetch_from_server('biorxiv', start_date, end_date, keywords, brief_mode, extended_mode)
        all_papers.extend(biorxiv_papers)
        time.sleep(self.rate_limit_delay)
        medrxiv_papers = self._fetch_from_server('medrxiv', start_date, end_date, keywords, brief_mode, extended_mode)
        all_papers.extend(medrxiv_papers)
        return all_papers
    
    def _fetch_from_server(self, server, start_date, end_date, keywords, brief_mode=False, extended_mode=False):
        papers = []
        api_url = ""
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            base_url = self.biorxiv_base_url if server == 'biorxiv' else self.medrxiv_base_url
            api_url = f"{base_url}/{start_str}/{end_str}"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'collection' in data and data['collection']:
                raw_papers = data['collection']
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
                        processed_paper = self._process_paper(paper, server)
                        papers.append(processed_paper)
        except requests.RequestException as e:
            print(f"Error fetching papers from {server}: {e}")
            if api_url:
                print(f"URL attempted: {api_url}")
        except Exception as e:
            print(f"Error processing {server} response: {e}")
            if api_url:
                print(f"URL attempted: {api_url}")
        return papers
    
    def _paper_matches_keywords(self, paper, keywords):
        if not keywords:
            return True
        searchable_text = ""
        if 'title' in paper:
            searchable_text += paper['title'].lower() + " "
        if 'abstract' in paper:
            searchable_text += paper['abstract'].lower() + " "
        if 'authors' in paper:
            searchable_text += paper['authors'].lower() + " "
        for keyword in keywords:
            if keyword.lower() in searchable_text:
                return True
        return False
    
    def _process_paper(self, paper, server):
        processed = {
            'title': paper.get('title', '').strip(),
            'abstract': paper.get('abstract', '').strip(),
            'published': self._parse_date(paper.get('date', '')),
            'source': server,
            'doi': paper.get('doi', ''),
            'categories': []
        }
        authors_str = paper.get('authors', '')
        if authors_str:
            authors = [author.strip() for author in authors_str.split(',') if author.strip()]
            processed['authors'] = authors
        else:
            processed['authors'] = []
        if processed['doi']:
            processed['arxiv_url'] = f"https://doi.org/{processed['doi']}"
        else:
            processed['arxiv_url'] = ""
        if server == 'biorxiv':
            processed['categories'].append('bioRxiv')
        else:
            processed['categories'].append('medRxiv')
        if 'category' in paper:
            processed['categories'].append(paper['category'])
        return processed
    
    def _parse_date(self, date_string):
        if not date_string:
            return datetime.now().strftime('%Y-%m-%d')
        try:
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return datetime.now().strftime('%Y-%m-%d')
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')
    
    def get_server_status(self):
        status = { 'biorxiv': False, 'medrxiv': False }
        try:
            test_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            url = f"{self.biorxiv_base_url}/{test_date}/{test_date}"
            response = requests.get(url, timeout=10)
            status['biorxiv'] = response.status_code == 200
        except:
            pass
        try:
            test_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            url = f"{self.medrxiv_base_url}/{test_date}/{test_date}"
            response = requests.get(url, timeout=10)
            status['medrxiv'] = response.status_code == 200
        except:
            pass
        return status



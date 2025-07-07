import re
from typing import List, Tuple


class KeywordMatcher:
    """Handles keyword matching and relevance scoring for papers"""

    def __init__(self):
        self.case_sensitive = False
        self._compiled_patterns = {}  # Cache compiled regex patterns
        self._text_cache = {}  # Cache processed text
        self._score_cache = {}  # Cache calculated scores

    def calculate_relevance(self, paper: dict,
                            keywords: List[str]) -> Tuple[float, List[str]]:
        """
        Calculate relevance score for a paper based on keyword matches
        
        Args:
            paper (dict): Paper data with title, abstract, etc.
            keywords (list): List of keywords to match against
            
        Returns:
            tuple: (relevance_score, matched_keywords)
        """
        
        # Create cache key for this paper-keyword combination
        paper_id = paper.get('pmid') or paper.get('arxiv_id') or paper.get('doi') or id(paper)
        cache_key = f"{paper_id}_{hash(tuple(sorted(keywords)))}"
        
        if cache_key in self._score_cache:
            return self._score_cache[cache_key]

        # Combine searchable text
        searchable_text = self._prepare_searchable_text(paper)

        # Find matching keywords with optimized loop
        matched_keywords = []
        keyword_counts = {}

        for keyword in keywords:
            matches = self._find_keyword_matches(searchable_text, keyword)
            if matches > 0:
                matched_keywords.append(keyword)
                keyword_counts[keyword] = matches

        # Calculate relevance score
        relevance_score = self._calculate_score(keyword_counts, paper)
        
        # Cache the result
        result = (relevance_score, matched_keywords)
        self._score_cache[cache_key] = result

        return result

    def _prepare_searchable_text(self, paper: dict) -> str:
        """Prepare combined text for keyword searching with caching"""

        # Create cache key from paper content
        paper_id = paper.get('pmid') or paper.get('arxiv_id') or paper.get('doi') or id(paper)
        
        if paper_id in self._text_cache:
            return self._text_cache[paper_id]

        # Build searchable text efficiently
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        authors = paper.get('authors', [])
        categories = paper.get('categories', [])
        
        # Combine components efficiently
        text_components = [
            title * 3,  # Title weighted 3x
            abstract,
            ' '.join(authors) if authors else '',
            ' '.join(categories) if categories else ''
        ]

        combined_text = ' '.join(filter(None, text_components))
        
        if not self.case_sensitive:
            combined_text = combined_text.lower()

        # Cache the result for reuse
        self._text_cache[paper_id] = combined_text
        return combined_text

    def _find_keyword_matches(self, text: str, keyword: str) -> int:
        """Find and count keyword matches in text with optimized caching"""

        if not keyword.strip():
            return 0

        # Prepare keyword for matching
        search_keyword = keyword if self.case_sensitive else keyword.lower()

        # Use cached compiled patterns for better performance
        pattern_key = search_keyword
        if pattern_key not in self._compiled_patterns:
            # For single words, use word boundaries; for phrases, use exact matches
            if ' ' in search_keyword:
                self._compiled_patterns[pattern_key] = re.compile(re.escape(search_keyword), re.IGNORECASE if not self.case_sensitive else 0)
            else:
                self._compiled_patterns[pattern_key] = re.compile(r'\b' + re.escape(search_keyword) + r'\b', re.IGNORECASE if not self.case_sensitive else 0)

        # Count matches using compiled pattern
        matches = len(self._compiled_patterns[pattern_key].findall(text))
        
        # For multi-word keywords, also check simple substring presence for robustness
        if ' ' in search_keyword and matches == 0:
            if search_keyword in text:
                matches = 1

        return matches

    def _calculate_score(self, keyword_counts: dict, paper: dict) -> float:
        """Calculate overall relevance score"""

        if not keyword_counts:
            return 0

        # Base score: number of unique keywords matched
        base_score = len(keyword_counts)

        # Bonus for multiple occurrences of the same keyword
        occurrence_bonus = sum(
            min(count - 1, 2)
            for count in keyword_counts.values())  # Cap bonus at 2 per keyword

        # Bonus for title matches (check if any keyword appears in title)
        title = paper.get('title', '')
        if not self.case_sensitive:
            title = title.lower()

        title_bonus = 0
        for keyword in keyword_counts.keys():
            search_keyword = keyword if self.case_sensitive else keyword.lower(
            )
            # Check for exact matches and word boundary matches in title
            if search_keyword in title or re.search(
                    r'\b' + re.escape(search_keyword) + r'\b', title):
                title_bonus += 1

        # Bonus for specific high-value keywords (PET and MRI)
        keyword_bonus = 0
        high_value_keywords = ['pet', 'mri']
        for keyword in keyword_counts.keys():
            keyword_lower = keyword.lower()
            if keyword_lower in high_value_keywords:
                keyword_bonus += 0.5
        
        # Calculate final score
        final_score = float(base_score) + (float(title_bonus) * 0.2) + float(keyword_bonus)
        return round(final_score, 1)

    def search_papers(self, papers: List[dict],
                      search_query: str) -> List[dict]:
        """Search through papers using a query string"""

        if not search_query.strip():
            return papers

        search_terms = search_query.lower().split()
        filtered_papers = []

        for paper in papers:
            searchable_text = self._prepare_searchable_text(paper).lower()

            # Check if all search terms are present
            if all(term in searchable_text for term in search_terms):
                filtered_papers.append(paper)

        return filtered_papers

    def get_keyword_statistics(self, papers: List[dict],
                               keywords: List[str]) -> dict:
        """Generate statistics about keyword matches across papers"""

        stats = {
            'keyword_counts': {},
            'total_papers': len(papers),
            'papers_with_matches': 0
        }

        papers_with_matches = set()

        for paper in papers:
            _, matched_keywords = self.calculate_relevance(paper, keywords)

            if matched_keywords:
                papers_with_matches.add(
                    id(paper))  # Use object id as unique identifier

                for keyword in matched_keywords:
                    stats['keyword_counts'][
                        keyword] = stats['keyword_counts'].get(keyword, 0) + 1

        stats['papers_with_matches'] = len(papers_with_matches)

        return stats

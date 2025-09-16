#!/usr/bin/env python3
"""
Knowledge Base Builder for Manuscript Alert System

This script creates a knowledge base of the top 20 articles for each of the past 4 weeks
by leveraging the existing fetching and ranking infrastructure from app.py.

The knowledge base will be saved in JSON format for future RAG integration.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import concurrent.futures
import pandas as pd

# Import the existing components from the app
from fetchers.arxiv_fetcher import ArxivFetcher
from fetchers.biorxiv_fetcher import BioRxivFetcher
from fetchers.pubmed_fetcher import PubMedFetcher
from processors.keyword_matcher import KeywordMatcher
from storage.data_storage import DataStorage


class KnowledgeBaseBuilder:
    """Builds a knowledge base from top articles over the past 4 weeks"""
    
    def __init__(self):
        """Initialize the knowledge base builder with existing components"""
        self.arxiv_fetcher = ArxivFetcher()
        self.biorxiv_fetcher = BioRxivFetcher()
        self.pubmed_fetcher = PubMedFetcher()
        self.keyword_matcher = KeywordMatcher()
        self.data_storage = DataStorage()
        
        # Default keywords from the app
        self.default_keywords = [
            "Alzheimer's disease",
            "PET",
            "MRI",
            "dementia",
            "amyloid",
            "tau",
            "plasma",
            "brain",
        ]
        
        # Data sources configuration - using all sources for comprehensive KB
        self.data_sources = {
            "arxiv": True,
            "biorxiv": True,
            "medrxiv": True,
            "pubmed": True,
        }
        
        # Search mode - using extended for comprehensive results
        self.search_mode = "Extended"
        
    def get_week_ranges(self, weeks_back: int = 4) -> List[Dict[str, datetime]]:
        """
        Generate date ranges for the past N weeks
        
        Args:
            weeks_back (int): Number of weeks to go back
            
        Returns:
            List of dictionaries with week info and date ranges
        """
        week_ranges = []
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for week in range(weeks_back):
            # Calculate week boundaries
            week_end = current_date - timedelta(days=week * 7)
            week_start = week_end - timedelta(days=6)  # 7 days per week
            
            week_info = {
                "week_number": week + 1,
                "start_date": week_start,
                "end_date": week_end,
                "week_label": f"Week {week + 1} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})"
            }
            week_ranges.append(week_info)
            
        return week_ranges
    
    def fetch_papers_for_week(self, week_info: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch and rank papers for a specific week
        
        Args:
            week_info (dict): Week information with start_date and end_date
            keywords (list): Keywords to search for
            
        Returns:
            List of paper dictionaries
        """
        print(f"\n📅 Processing {week_info['week_label']}...")
        
        start_date = week_info["start_date"]
        end_date = week_info["end_date"]
        
        all_papers_data = []
        
        # Define fetching functions for parallel execution
        def fetch_arxiv():
            if self.data_sources.get("arxiv", False):
                try:
                    print(f"  🔍 Fetching arXiv papers...")
                    papers = self.arxiv_fetcher.fetch_papers(
                        start_date, end_date, keywords, False, True  # extended_mode=True
                    )
                    print(f"  ✅ Found {len(papers)} arXiv papers")
                    return ("arxiv", papers)
                except Exception as e:
                    print(f"  ❌ Error fetching arXiv: {e}")
                    return ("arxiv_error", str(e))
            return ("arxiv", [])
        
        def fetch_biorxiv():
            if self.data_sources.get("biorxiv", False) or self.data_sources.get("medrxiv", False):
                try:
                    print(f"  🔍 Fetching bioRxiv/medRxiv papers...")
                    papers = self.biorxiv_fetcher.fetch_papers(
                        start_date, end_date, keywords, False, True  # extended_mode=True
                    )
                    # Filter by source selection
                    filtered_papers = []
                    for paper in papers:
                        source = paper.get("source", "")
                        if (source == "biorxiv" and self.data_sources.get("biorxiv", False)) or (
                            source == "medrxiv" and self.data_sources.get("medrxiv", False)
                        ):
                            filtered_papers.append(paper)
                    print(f"  ✅ Found {len(filtered_papers)} bioRxiv/medRxiv papers")
                    return ("biorxiv", filtered_papers)
                except Exception as e:
                    print(f"  ❌ Error fetching bioRxiv/medRxiv: {e}")
                    return ("biorxiv_error", str(e))
            return ("biorxiv", [])
        
        def fetch_pubmed():
            if self.data_sources.get("pubmed", False):
                try:
                    print(f"  🔍 Fetching PubMed papers...")
                    papers = self.pubmed_fetcher.fetch_papers(
                        start_date, end_date, keywords, False, True  # extended_mode=True
                    )
                    print(f"  ✅ Found {len(papers)} PubMed papers")
                    return ("pubmed", papers)
                except Exception as e:
                    print(f"  ❌ Error fetching PubMed: {e}")
                    return ("pubmed_error", str(e))
            return ("pubmed", [])
        
        # Execute all API calls in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(fetch_arxiv),
                executor.submit(fetch_biorxiv),
                executor.submit(fetch_pubmed),
            ]
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                result_type, result_data = future.result()
                
                if result_type.endswith("_error"):
                    source_name = result_type.replace("_error", "")
                    print(f"  ⚠️ Error fetching from {source_name}: {result_data}")
                else:
                    all_papers_data.extend(result_data)
        
        if not all_papers_data:
            print(f"  ⚠️ No papers found for {week_info['week_label']}")
            return []
        
        # Process and rank papers
        print(f"  📊 Processing and ranking {len(all_papers_data)} papers...")
        ranked_papers = self._process_and_rank_papers(all_papers_data, keywords)
        
        # Get top 20 papers
        top_papers = ranked_papers.head(20)
        print(f"  🏆 Selected top {len(top_papers)} papers for {week_info['week_label']}")
        
        return top_papers.to_dict('records')
    
    def _process_and_rank_papers(self, papers_data: List[Dict], keywords: List[str]) -> pd.DataFrame:
        """
        Process and rank papers using the existing logic from app.py
        
        Args:
            papers_data (list): Raw paper data from fetchers
            keywords (list): Keywords for relevance calculation
            
        Returns:
            DataFrame with ranked papers
        """
        # Define processing function for parallel execution
        def process_paper(paper):
            relevance_score, matched_keywords = self.keyword_matcher.calculate_relevance(
                paper, keywords
            )
            
            # Boost score for target journals (using logic from app.py)
            if paper.get("source") == "PubMed" and paper.get("journal"):
                if self._is_high_impact_journal(paper["journal"]):
                    if len(matched_keywords) >= 5:
                        relevance_score += 5.1
                    elif 5 > len(matched_keywords) >= 4:
                        relevance_score += 3.7
                    elif 4 > len(matched_keywords) >= 3:
                        relevance_score += 2.8
                    elif 3 > len(matched_keywords) >= 2:
                        relevance_score += 1.3
            
            # Format authors list
            authors = paper.get("authors", [])
            if isinstance(authors, list):
                authors_str = ", ".join(authors[:3]) + ("..." if len(authors) > 3 else "")
            else:
                authors_str = str(authors)
            
            return (paper, relevance_score, matched_keywords, authors_str)
        
        # Process papers in parallel for faster ranking
        ranked_papers = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_paper = {
                executor.submit(process_paper, paper): paper for paper in papers_data
            }
            
            for future in concurrent.futures.as_completed(future_to_paper):
                try:
                    paper, relevance_score, matched_keywords, authors_str = future.result()
                    
                    # Get source information
                    source = paper.get("source", "arXiv")
                    if source == "PubMed":
                        source_display = "PubMed"
                    elif source == "arxiv":
                        source_display = "arXiv"
                    else:
                        source_display = source.capitalize()
                    
                    paper_info = {
                        "title": paper["title"],
                        "authors": authors_str,
                        "abstract": paper["abstract"],
                        "published": paper["published"],
                        "arxiv_url": paper.get("arxiv_url", ""),
                        "source": source_display,
                        "relevance_score": relevance_score,
                        "matched_keywords": matched_keywords,
                        "journal": paper.get("journal", ""),
                        "volume": paper.get("volume", ""),
                        "issue": paper.get("issue", ""),
                        "pmid": paper.get("pmid", ""),
                        "doi": paper.get("doi", ""),
                        "categories": paper.get("categories", []),
                    }
                    
                    ranked_papers.append(paper_info)
                except Exception as e:
                    print(f"  ⚠️ Error processing paper: {e}")
                    continue  # Skip papers that fail processing
        
        # Convert to DataFrame and sort by relevance
        df = pd.DataFrame(ranked_papers)
        if not df.empty:
            df = df.sort_values("relevance_score", ascending=False)
        
        return df
    
    def _is_high_impact_journal(self, journal_name: str) -> bool:
        """
        Check if a journal is in the high-impact list (copied from app.py)
        
        Args:
            journal_name (str): Name of the journal
            
        Returns:
            bool: True if high-impact journal
        """
        if not journal_name:
            return False
        
        journal_lower = journal_name.lower().strip()
        
        # Define target journal patterns
        target_patterns = {
            "exact_matches": [
                "jama",
                "nature",
                "science",
                "radiology",
                "ajnr",
                "the lancet",
            ],
            "family_matches": [
                "jama ",
                "nature ",
                "science ",
                "npj ",
                "the lancet",
            ],
            "specific_journals": [
                "american journal of neuroradiology",
                "alzheimer's & dementia",
                "alzheimers dement",
                "ebiomedicine",
                "journal of magnetic resonance imaging",
                "magnetic resonance in medicine",
                "radiology",
                "jmri",
                "j magn reson imaging",
                "brain : a journal of neurology",
            ],
        }
        
        # Check exact matches first
        for exact_match in target_patterns["exact_matches"]:
            if journal_lower == exact_match:
                return True
        
        # Check family matches
        for family_pattern in target_patterns["family_matches"]:
            if journal_lower.startswith(family_pattern):
                return True
        
        # Check specific journals
        for specific_journal in target_patterns["specific_journals"]:
            if specific_journal in journal_lower:
                return True
        
        return False
    
    def build_knowledge_base(self, weeks_back: int = 4, keywords: List[str] = None) -> Dict[str, Any]:
        """
        Build the complete knowledge base
        
        Args:
            weeks_back (int): Number of weeks to include
            keywords (list): Keywords to use (defaults to app defaults)
            
        Returns:
            Dictionary containing the knowledge base
        """
        if keywords is None:
            keywords = self.default_keywords
        
        print(f"🚀 Building Knowledge Base for past {weeks_back} weeks")
        print(f"🔍 Using keywords: {', '.join(keywords)}")
        print(f"📚 Data sources: {', '.join([k for k, v in self.data_sources.items() if v])}")
        
        # Get week ranges
        week_ranges = self.get_week_ranges(weeks_back)
        
        # Build knowledge base structure
        knowledge_base = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "weeks_covered": weeks_back,
                "keywords_used": keywords,
                "data_sources": {k: v for k, v in self.data_sources.items() if v},
                "search_mode": self.search_mode,
                "total_papers": 0,
                "papers_per_week": 20
            },
            "weeks": {}
        }
        
        total_papers = 0
        
        # Process each week
        for week_info in week_ranges:
            try:
                week_papers = self.fetch_papers_for_week(week_info, keywords)
                
                # Add week data to knowledge base
                knowledge_base["weeks"][f"week_{week_info['week_number']}"] = {
                    "week_info": week_info,
                    "papers": week_papers,
                    "paper_count": len(week_papers)
                }
                
                total_papers += len(week_papers)
                print(f"  ✅ {week_info['week_label']}: {len(week_papers)} papers")
                
            except Exception as e:
                print(f"  ❌ Error processing {week_info['week_label']}: {e}")
                knowledge_base["weeks"][f"week_{week_info['week_number']}"] = {
                    "week_info": week_info,
                    "papers": [],
                    "paper_count": 0,
                    "error": str(e)
                }
        
        # Update metadata
        knowledge_base["metadata"]["total_papers"] = total_papers
        
        print(f"\n🎉 Knowledge Base Complete!")
        print(f"📊 Total papers collected: {total_papers}")
        print(f"📅 Weeks processed: {weeks_back}")
        
        return knowledge_base
    
    def save_knowledge_base(self, knowledge_base: Dict[str, Any], filename: str = None) -> str:
        """
        Save the knowledge base to a JSON file
        
        Args:
            knowledge_base (dict): The knowledge base data
            filename (str): Optional custom filename
            
        Returns:
            str: Path to the saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"knowledge_base_{timestamp}.json"
        
        # Ensure the filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"💾 Knowledge base saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving knowledge base: {e}")
            raise
    
    def load_knowledge_base(self, filepath: str) -> Dict[str, Any]:
        """
        Load a knowledge base from a JSON file
        
        Args:
            filepath (str): Path to the knowledge base file
            
        Returns:
            dict: The loaded knowledge base
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
            
            print(f"📂 Knowledge base loaded from: {filepath}")
            return knowledge_base
            
        except Exception as e:
            print(f"❌ Error loading knowledge base: {e}")
            raise
    
    def print_knowledge_base_summary(self, knowledge_base: Dict[str, Any]):
        """
        Print a summary of the knowledge base
        
        Args:
            knowledge_base (dict): The knowledge base data
        """
        metadata = knowledge_base.get("metadata", {})
        weeks = knowledge_base.get("weeks", {})
        
        print(f"\n📋 Knowledge Base Summary")
        print(f"=" * 50)
        print(f"Created: {metadata.get('created_at', 'Unknown')}")
        print(f"Weeks covered: {metadata.get('weeks_covered', 0)}")
        print(f"Total papers: {metadata.get('total_papers', 0)}")
        print(f"Papers per week: {metadata.get('papers_per_week', 0)}")
        print(f"Keywords: {', '.join(metadata.get('keywords_used', []))}")
        print(f"Data sources: {', '.join(metadata.get('data_sources', {}).keys())}")
        
        print(f"\n📅 Weekly Breakdown:")
        for week_key, week_data in weeks.items():
            week_info = week_data.get("week_info", {})
            paper_count = week_data.get("paper_count", 0)
            week_label = week_info.get("week_label", week_key)
            print(f"  {week_label}: {paper_count} papers")
        
        # Source distribution
        source_counts = {}
        for week_data in weeks.values():
            for paper in week_data.get("papers", []):
                source = paper.get("source", "Unknown")
                source_counts[source] = source_counts.get(source, 0) + 1
        
        if source_counts:
            print(f"\n📊 Source Distribution:")
            for source, count in sorted(source_counts.items()):
                print(f"  {source}: {count} papers")


def main():
    """Main function to build the knowledge base"""
    print("🧠 Manuscript Alert Knowledge Base Builder")
    print("=" * 50)
    
    # Initialize the builder
    builder = KnowledgeBaseBuilder()
    
    # Build the knowledge base
    try:
        knowledge_base = builder.build_knowledge_base(weeks_back=4)
        
        # Save the knowledge base
        filepath = builder.save_knowledge_base(knowledge_base)
        
        # Print summary
        builder.print_knowledge_base_summary(knowledge_base)
        
        print(f"\n✅ Knowledge base creation completed successfully!")
        print(f"📁 File saved: {filepath}")
        
    except Exception as e:
        print(f"❌ Error building knowledge base: {e}")
        raise


if __name__ == "__main__":
    main()

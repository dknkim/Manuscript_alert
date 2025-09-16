#!/usr/bin/env python3
"""
Knowledge Base Analyzer for Manuscript Alert System

This script provides utilities to analyze and explore the generated knowledge base.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from collections import Counter


class KnowledgeBaseAnalyzer:
    """Analyzes and provides insights about the knowledge base"""
    
    def __init__(self, knowledge_base_path: str):
        """
        Initialize the analyzer with a knowledge base file
        
        Args:
            knowledge_base_path (str): Path to the knowledge base JSON file
        """
        self.knowledge_base_path = knowledge_base_path
        self.knowledge_base = self.load_knowledge_base()
    
    def load_knowledge_base(self) -> Dict[str, Any]:
        """Load the knowledge base from JSON file"""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading knowledge base: {e}")
            raise
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the knowledge base"""
        metadata = self.knowledge_base.get("metadata", {})
        weeks = self.knowledge_base.get("weeks", {})
        
        stats = {
            "total_papers": metadata.get("total_papers", 0),
            "weeks_covered": metadata.get("weeks_covered", 0),
            "papers_per_week": metadata.get("papers_per_week", 0),
            "keywords_used": metadata.get("keywords_used", []),
            "data_sources": metadata.get("data_sources", {}),
            "created_at": metadata.get("created_at", ""),
            "weekly_breakdown": {}
        }
        
        # Weekly breakdown
        for week_key, week_data in weeks.items():
            week_info = week_data.get("week_info", {})
            paper_count = week_data.get("paper_count", 0)
            stats["weekly_breakdown"][week_key] = {
                "week_label": week_info.get("week_label", week_key),
                "paper_count": paper_count
            }
        
        return stats
    
    def get_source_distribution(self) -> Dict[str, int]:
        """Get distribution of papers by source"""
        source_counts = Counter()
        
        for week_data in self.knowledge_base.get("weeks", {}).values():
            for paper in week_data.get("papers", []):
                source = paper.get("source", "Unknown")
                source_counts[source] += 1
        
        return dict(source_counts)
    
    def get_journal_distribution(self, top_n: int = 20) -> Dict[str, int]:
        """Get distribution of papers by journal (top N)"""
        journal_counts = Counter()
        
        for week_data in self.knowledge_base.get("weeks", {}).values():
            for paper in week_data.get("papers", []):
                if paper.get("source") == "PubMed" and paper.get("journal"):
                    journal = paper.get("journal", "Unknown")
                    journal_counts[journal] += 1
        
        return dict(journal_counts.most_common(top_n))
    
    def get_keyword_analysis(self) -> Dict[str, Any]:
        """Analyze keyword matches across all papers"""
        keyword_counts = Counter()
        papers_with_keywords = 0
        total_papers = 0
        
        for week_data in self.knowledge_base.get("weeks", {}).values():
            for paper in week_data.get("papers", []):
                total_papers += 1
                matched_keywords = paper.get("matched_keywords", [])
                if matched_keywords:
                    papers_with_keywords += 1
                    for keyword in matched_keywords:
                        keyword_counts[keyword] += 1
        
        return {
            "total_papers": total_papers,
            "papers_with_keywords": papers_with_keywords,
            "keyword_frequency": dict(keyword_counts.most_common()),
            "avg_keywords_per_paper": sum(keyword_counts.values()) / total_papers if total_papers > 0 else 0
        }
    
    def get_relevance_score_analysis(self) -> Dict[str, Any]:
        """Analyze relevance scores across all papers"""
        scores = []
        
        for week_data in self.knowledge_base.get("weeks", {}).values():
            for paper in week_data.get("papers", []):
                score = paper.get("relevance_score", 0)
                scores.append(score)
        
        if not scores:
            return {"error": "No scores found"}
        
        scores.sort(reverse=True)
        
        return {
            "total_papers": len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "avg_score": sum(scores) / len(scores),
            "median_score": scores[len(scores) // 2],
            "top_10_scores": scores[:10],
            "score_distribution": {
                "9+": len([s for s in scores if s >= 9]),
                "7-9": len([s for s in scores if 7 <= s < 9]),
                "5-7": len([s for s in scores if 5 <= s < 7]),
                "3-5": len([s for s in scores if 3 <= s < 5]),
                "<3": len([s for s in scores if s < 3])
            }
        }
    
    def get_top_papers(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N papers by relevance score across all weeks"""
        all_papers = []
        
        for week_data in self.knowledge_base.get("weeks", {}).values():
            for paper in week_data.get("papers", []):
                all_papers.append(paper)
        
        # Sort by relevance score
        all_papers.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return all_papers[:n]
    
    def search_papers(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search papers by title, abstract, or authors
        
        Args:
            query (str): Search query
            case_sensitive (bool): Whether search should be case sensitive
            
        Returns:
            List of matching papers
        """
        if not query.strip():
            return []
        
        search_query = query if case_sensitive else query.lower()
        matching_papers = []
        
        for week_data in self.knowledge_base.get("weeks", {}).values():
            for paper in week_data.get("papers", []):
                # Search in title, abstract, and authors
                title = paper.get("title", "")
                abstract = paper.get("abstract", "")
                authors = paper.get("authors", "")
                
                searchable_text = f"{title} {abstract} {authors}"
                if not case_sensitive:
                    searchable_text = searchable_text.lower()
                
                if search_query in searchable_text:
                    matching_papers.append(paper)
        
        return matching_papers
    
    def export_to_csv(self, output_path: str = None) -> str:
        """
        Export the knowledge base to CSV format
        
        Args:
            output_path (str): Optional output path
            
        Returns:
            Path to the exported CSV file
        """
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(self.knowledge_base_path))[0]
            output_path = f"{base_name}_export.csv"
        
        # Flatten the data
        flattened_data = []
        
        for week_key, week_data in self.knowledge_base.get("weeks", {}).items():
            week_info = week_data.get("week_info", {})
            
            for paper in week_data.get("papers", []):
                flattened_paper = {
                    "week": week_key,
                    "week_label": week_info.get("week_label", ""),
                    "week_start": week_info.get("start_date", ""),
                    "week_end": week_info.get("end_date", ""),
                    "title": paper.get("title", ""),
                    "authors": paper.get("authors", ""),
                    "abstract": paper.get("abstract", ""),
                    "published": paper.get("published", ""),
                    "source": paper.get("source", ""),
                    "journal": paper.get("journal", ""),
                    "volume": paper.get("volume", ""),
                    "issue": paper.get("issue", ""),
                    "relevance_score": paper.get("relevance_score", 0),
                    "matched_keywords": ", ".join(paper.get("matched_keywords", [])),
                    "url": paper.get("arxiv_url", ""),
                    "pmid": paper.get("pmid", ""),
                    "doi": paper.get("doi", ""),
                }
                flattened_data.append(flattened_paper)
        
        # Create DataFrame and save
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        return output_path
    
    def print_comprehensive_report(self):
        """Print a comprehensive analysis report"""
        print("📊 Knowledge Base Analysis Report")
        print("=" * 60)
        
        # Basic stats
        stats = self.get_basic_stats()
        print(f"\n📋 Basic Statistics:")
        print(f"  Total Papers: {stats['total_papers']}")
        print(f"  Weeks Covered: {stats['weeks_covered']}")
        print(f"  Papers per Week: {stats['papers_per_week']}")
        print(f"  Created: {stats['created_at']}")
        print(f"  Keywords: {', '.join(stats['keywords_used'])}")
        
        # Weekly breakdown
        print(f"\n📅 Weekly Breakdown:")
        for week_key, week_data in stats['weekly_breakdown'].items():
            print(f"  {week_data['week_label']}: {week_data['paper_count']} papers")
        
        # Source distribution
        source_dist = self.get_source_distribution()
        print(f"\n📚 Source Distribution:")
        for source, count in sorted(source_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} papers")
        
        # Journal distribution
        journal_dist = self.get_journal_distribution(10)
        print(f"\n🏆 Top 10 Journals:")
        for journal, count in journal_dist.items():
            print(f"  {journal}: {count} papers")
        
        # Keyword analysis
        keyword_analysis = self.get_keyword_analysis()
        print(f"\n🔍 Keyword Analysis:")
        print(f"  Papers with keywords: {keyword_analysis['papers_with_keywords']}/{keyword_analysis['total_papers']}")
        print(f"  Average keywords per paper: {keyword_analysis['avg_keywords_per_paper']:.1f}")
        print(f"  Top keywords:")
        for keyword, count in list(keyword_analysis['keyword_frequency'].items())[:10]:
            print(f"    {keyword}: {count} papers")
        
        # Relevance score analysis
        score_analysis = self.get_relevance_score_analysis()
        if "error" not in score_analysis:
            print(f"\n⭐ Relevance Score Analysis:")
            print(f"  Average score: {score_analysis['avg_score']:.1f}")
            print(f"  Max score: {score_analysis['max_score']}")
            print(f"  Min score: {score_analysis['min_score']}")
            print(f"  Score distribution:")
            for range_label, count in score_analysis['score_distribution'].items():
                print(f"    {range_label}: {count} papers")
        
        # Top papers
        top_papers = self.get_top_papers(5)
        print(f"\n🏆 Top 5 Papers by Relevance Score:")
        for i, paper in enumerate(top_papers, 1):
            print(f"  {i}. {paper.get('title', 'No title')[:80]}...")
            print(f"     Score: {paper.get('relevance_score', 0)}, Source: {paper.get('source', 'Unknown')}")


def main():
    """Main function to analyze the knowledge base"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python knowledge_base_analyzer.py <knowledge_base_file.json>")
        print("Example: python knowledge_base_analyzer.py knowledge_base_20250915_204225.json")
        return
    
    knowledge_base_file = sys.argv[1]
    
    if not os.path.exists(knowledge_base_file):
        print(f"❌ File not found: {knowledge_base_file}")
        return
    
    try:
        # Initialize analyzer
        analyzer = KnowledgeBaseAnalyzer(knowledge_base_file)
        
        # Print comprehensive report
        analyzer.print_comprehensive_report()
        
        # Export to CSV
        csv_path = analyzer.export_to_csv()
        print(f"\n💾 Data exported to CSV: {csv_path}")
        
    except Exception as e:
        print(f"❌ Error analyzing knowledge base: {e}")


if __name__ == "__main__":
    main()

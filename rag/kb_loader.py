"""
Knowledge Base Loader for RAG System

This module handles loading and processing knowledge base files for the RAG system.
It extracts papers from KB files and prepares them for embedding and retrieval.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd


class KnowledgeBaseLoader:
    """Loads and processes knowledge base files for RAG"""
    
    def __init__(self, kb_directory: str = "./KB"):
        """
        Initialize the KB loader
        
        Args:
            kb_directory (str): Path to the KB directory
        """
        self.kb_directory = kb_directory
        self.papers_cache = []
        self.last_loaded = None
    
    def load_all_kb_files(self, exclude_today: bool = True) -> List[Dict[str, Any]]:
        """
        Load all knowledge base files and extract papers
        
        Args:
            exclude_today (bool): Whether to exclude papers published today
            
        Returns:
            List of paper dictionaries
        """
        if not os.path.exists(self.kb_directory):
            return []
        
        all_papers = []
        kb_files = [f for f in os.listdir(self.kb_directory) if f.endswith('.json')]
        
        # Get today's date for filtering
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        for kb_file in kb_files:
            file_path = os.path.join(self.kb_directory, kb_file)
            try:
                papers = self._load_kb_file(file_path)
                
                # Filter out papers published today if requested
                if exclude_today:
                    filtered_papers = []
                    for paper in papers:
                        paper_date = paper.get('published', '')
                        if paper_date != today_date:
                            filtered_papers.append(paper)
                        else:
                            print(f"Excluding paper from today ({today_date}): {paper.get('title', 'Unknown')[:50]}...")
                    papers = filtered_papers
                
                all_papers.extend(papers)
            except Exception as e:
                print(f"Error loading {kb_file}: {e}")
                continue
        
        # Remove duplicates based on title and authors
        unique_papers = self._remove_duplicates(all_papers)
        
        self.papers_cache = unique_papers
        self.last_loaded = datetime.now()
        
        return unique_papers
    
    def _load_kb_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load a single KB file and extract papers"""
        with open(file_path, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
        
        papers = []
        weeks = kb_data.get('weeks', {})
        
        for week_key, week_data in weeks.items():
            week_papers = week_data.get('papers', [])
            week_info = week_data.get('week_info', {})
            
            # Add week context to each paper
            for paper in week_papers:
                paper['week_info'] = week_info
                paper['kb_file'] = os.path.basename(file_path)
                papers.append(paper)
        
        return papers
    
    def _remove_duplicates(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate papers based on title and authors"""
        seen = set()
        unique_papers = []
        
        for paper in papers:
            # Create a unique identifier
            title = paper.get('title', '').lower().strip()
            authors = paper.get('authors', '').lower().strip()
            identifier = f"{title}|{authors}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique_papers.append(paper)
        
        return unique_papers
    
    def _semantic_search_papers(self, query: str, vector_store, max_papers: int = 60) -> List[Dict[str, Any]]:
        """
        Search for papers using semantic similarity via vector store
        
        Args:
            query (str): Search query
            vector_store: Vector store instance
            max_papers (int): Maximum number of papers to return
            
        Returns:
            List of papers with similarity scores
        """
        try:
            # Perform semantic search
            results = vector_store.search(query, top_k=max_papers, similarity_threshold=0.1)
            
            matching_papers = []
            for doc, similarity_score in results:
                # Find the paper in our cache by title (since vector store contains chunks)
                paper_title = doc.metadata.get('title', '')
                paper = self._find_paper_by_title(paper_title)
                
                if paper:
                    # Add similarity score to paper
                    paper['similarity_score'] = similarity_score
                    paper['query_match_score'] = similarity_score * 10  # Convert to integer-like score
                    matching_papers.append(paper)
            
            print(f"🔍 Semantic search found {len(matching_papers)} papers for query: '{query}'")
            return matching_papers
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            # Fallback to keyword search
            return self._keyword_search_papers(query)
    
    def _keyword_search_papers(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for papers using keyword matching (fallback method)
        
        Args:
            query (str): Search query
            
        Returns:
            List of papers with match scores
        """
        matching_papers = []
        query_lower = query.lower()
        
        for paper in self.papers_cache:
            # Check if query terms appear in title, abstract, or keywords
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            keywords = [kw.lower() for kw in paper.get('matched_keywords', [])]
            
            # Simple keyword matching
            query_terms = query_lower.split()
            matches = sum(1 for term in query_terms if term in title or term in abstract or any(term in kw for kw in keywords))
            
            if matches > 0:
                paper['query_match_score'] = matches
                paper['similarity_score'] = matches / len(query_terms)  # Normalize to 0-1 range
                matching_papers.append(paper)
        
        print(f"🔍 Keyword search found {len(matching_papers)} papers for query: '{query}'")
        return matching_papers
    
    def _find_paper_by_title(self, title: str) -> Dict[str, Any]:
        """
        Find a paper in the cache by title
        
        Args:
            title (str): Paper title to search for
            
        Returns:
            Paper dictionary or None if not found
        """
        for paper in self.papers_cache:
            if paper.get('title', '').lower() == title.lower():
                return paper
        return None
    
    def get_papers_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get papers within a specific date range
        
        Args:
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            List of papers within the date range
        """
        if not self.papers_cache:
            self.load_all_kb_files()
        
        filtered_papers = []
        for paper in self.papers_cache:
            try:
                paper_date = datetime.strptime(paper.get('published', ''), '%Y-%m-%d')
                if start_date <= paper_date <= end_date:
                    filtered_papers.append(paper)
            except ValueError:
                # Skip papers with invalid dates
                continue
        
        return filtered_papers
    
    def get_weekly_papers(self, weeks_back: int = 4) -> List[Dict[str, Any]]:
        """
        Get papers from the last N weeks
        
        Args:
            weeks_back (int): Number of weeks to look back
            
        Returns:
            List of papers from the specified period
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        return self.get_papers_by_date_range(start_date, end_date)
    
    def get_papers_by_keywords(self, keywords: List[str], case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Get papers that match specific keywords
        
        Args:
            keywords (List[str]): Keywords to search for
            case_sensitive (bool): Whether search should be case sensitive
            
        Returns:
            List of matching papers
        """
        if not self.papers_cache:
            self.load_all_kb_files()
        
        matching_papers = []
        search_keywords = [kw.lower() for kw in keywords] if not case_sensitive else keywords
        
        for paper in self.papers_cache:
            # Search in title, abstract, and matched keywords
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            matched_keywords = paper.get('matched_keywords', [])
            
            search_text = f"{title} {abstract} {' '.join(matched_keywords)}"
            if not case_sensitive:
                search_text = search_text.lower()
            
            # Check if any keyword matches
            if any(keyword in search_text for keyword in search_keywords):
                matching_papers.append(paper)
        
        return matching_papers
    
    def get_papers_by_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Get papers from a specific source
        
        Args:
            source (str): Source name (PubMed, arXiv, etc.)
            
        Returns:
            List of papers from the specified source
        """
        if not self.papers_cache:
            self.load_all_kb_files()
        
        return [paper for paper in self.papers_cache if paper.get('source', '').lower() == source.lower()]
    
    def get_papers_by_journal(self, journal_pattern: str) -> List[Dict[str, Any]]:
        """
        Get papers from journals matching a pattern
        
        Args:
            journal_pattern (str): Journal name pattern to match
            
        Returns:
            List of papers from matching journals
        """
        if not self.papers_cache:
            self.load_all_kb_files()
        
        matching_papers = []
        pattern_lower = journal_pattern.lower()
        
        for paper in self.papers_cache:
            journal = paper.get('journal', '').lower()
            if pattern_lower in journal:
                matching_papers.append(paper)
        
        return matching_papers
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded papers
        
        Returns:
            Dictionary with various statistics
        """
        if not self.papers_cache:
            self.load_all_kb_files()
        
        if not self.papers_cache:
            return {"total_papers": 0}
        
        # Basic statistics
        total_papers = len(self.papers_cache)
        
        # Source distribution
        sources = {}
        for paper in self.papers_cache:
            source = paper.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        # Journal distribution
        journals = {}
        for paper in self.papers_cache:
            journal = paper.get('journal', 'Unknown')
            if journal:
                journals[journal] = journals.get(journal, 0) + 1
        
        # Date range
        dates = []
        for paper in self.papers_cache:
            try:
                date = datetime.strptime(paper.get('published', ''), '%Y-%m-%d')
                dates.append(date)
            except ValueError:
                continue
        
        date_range = {}
        if dates:
            date_range = {
                "earliest": min(dates).strftime('%Y-%m-%d'),
                "latest": max(dates).strftime('%Y-%m-%d')
            }
        
        # Relevance score statistics
        scores = [paper.get('relevance_score', 0) for paper in self.papers_cache if paper.get('relevance_score')]
        score_stats = {}
        if scores:
            score_stats = {
                "min": min(scores),
                "max": max(scores),
                "avg": sum(scores) / len(scores),
                "count": len(scores)
            }
        
        return {
            "total_papers": total_papers,
            "sources": sources,
            "top_journals": dict(sorted(journals.items(), key=lambda x: x[1], reverse=True)[:10]),
            "date_range": date_range,
            "relevance_scores": score_stats,
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None
        }
    
    def analyze_trends_for_query(self, query: str, top_k: int = 20, llm_client=None, vector_store=None) -> Dict[str, Any]:
        """
        Analyze trends for a specific query using semantic search
        
        Args:
            query (str): Search query
            top_k (int): Number of top papers to analyze
            llm_client: LLM client for similarity calculations
            vector_store: Vector store for semantic search
            
        Returns:
            Dictionary with trend analysis
        """
        if not self.papers_cache:
            self.load_all_kb_files()
        
        # Use semantic search if vector store is available, otherwise fallback to keyword matching
        if vector_store and vector_store.is_available():
            print(f"🧠 Using semantic search for query: '{query}'")
            matching_papers = self._semantic_search_papers(query, vector_store, top_k * 3)  # Get more papers for better analysis
        else:
            print(f"📊 Using keyword search for query: '{query}' (vector store unavailable)")
            matching_papers = self._keyword_search_papers(query)
        
        # Sort by relevance score and similarity score
        matching_papers.sort(key=lambda x: (x.get('relevance_score', 0), x.get('similarity_score', 0)), reverse=True)
        top_papers = matching_papers[:top_k]
        
        if not top_papers:
            return {"error": "No papers found matching the query"}
        
        # Analyze trends
        trends = self._analyze_paper_trends(top_papers)
        
        # Add comparative analysis
        comparative_insights = self._generate_comparative_insights(query, top_papers, matching_papers, llm_client=llm_client)
        
        return {
            "query": query,
            "total_matching_papers": len(matching_papers),
            "analyzed_papers": len(top_papers),
            "trends": trends,
            "comparative_insights": comparative_insights,
            "top_papers": top_papers[:10]  # Top 10 for display
        }
    
    def _analyze_paper_trends(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in a set of papers"""
        if not papers:
            return {}
        
        # Source distribution
        sources = {}
        for paper in papers:
            source = paper.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        # Journal distribution
        journals = {}
        for paper in papers:
            journal = paper.get('journal', 'Unknown')
            if journal and journal != 'Unknown':
                journals[journal] = journals.get(journal, 0) + 1
        
        # Keyword frequency
        all_keywords = {}
        for paper in papers:
            for keyword in paper.get('matched_keywords', []):
                all_keywords[keyword] = all_keywords.get(keyword, 0) + 1
        
        # Date analysis
        dates = []
        for paper in papers:
            try:
                date = datetime.strptime(paper.get('published', ''), '%Y-%m-%d')
                dates.append(date)
            except ValueError:
                continue
        
        # Relevance score analysis
        relevance_scores = [paper.get('relevance_score', 0) for paper in papers if paper.get('relevance_score')]
        
        # Research themes (based on common keywords)
        research_themes = {}
        for paper in papers:
            keywords = paper.get('matched_keywords', [])
            for keyword in keywords:
                # Group related keywords
                theme = self._categorize_keyword(keyword)
                research_themes[theme] = research_themes.get(theme, 0) + 1
        
        return {
            "source_distribution": dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)),
            "top_journals": dict(sorted(journals.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_keywords": dict(sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:10]),
            "research_themes": dict(sorted(research_themes.items(), key=lambda x: x[1], reverse=True)),
            "date_range": {
                "earliest": min(dates).strftime('%Y-%m-%d') if dates else None,
                "latest": max(dates).strftime('%Y-%m-%d') if dates else None,
                "span_days": (max(dates) - min(dates)).days if len(dates) > 1 else 0
            },
            "relevance_stats": {
                "avg_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
                "max_relevance": max(relevance_scores) if relevance_scores else 0,
                "min_relevance": min(relevance_scores) if relevance_scores else 0
            }
        }
    
    def _categorize_keyword(self, keyword: str) -> str:
        """Categorize keywords into research themes"""
        keyword_lower = keyword.lower()
        
        if any(term in keyword_lower for term in ['alzheimer', 'dementia', 'cognitive']):
            return "Alzheimer's Disease & Dementia"
        elif any(term in keyword_lower for term in ['pet', 'mri', 'imaging', 'neuroimaging']):
            return "Neuroimaging & Brain Imaging"
        elif any(term in keyword_lower for term in ['tau', 'amyloid', 'biomarker']):
            return "Biomarkers & Pathology"
        elif any(term in keyword_lower for term in ['machine learning', 'deep learning', 'ai', 'artificial intelligence']):
            return "AI & Machine Learning"
        elif any(term in keyword_lower for term in ['plasma', 'blood', 'serum']):
            return "Blood-based Biomarkers"
        elif any(term in keyword_lower for term in ['brain', 'cortical', 'hippocampus']):
            return "Brain Structure & Function"
        else:
            return "Other Research Areas"
    
    def _generate_comparative_insights(self, query: str, recent_papers: List[Dict[str, Any]], all_matching_papers: List[Dict[str, Any]], llm_client=None) -> Dict[str, Any]:
        """
        Generate comparative insights between recent papers and historical papers
        
        Args:
            query (str): The search query
            recent_papers (List[Dict]): Recent papers (top N)
            all_matching_papers (List[Dict]): All matching papers
            
        Returns:
            Dictionary with comparative insights
        """
        if len(recent_papers) < 3 or len(all_matching_papers) < 10:
            return {"insights": ["Insufficient data for comparative analysis"]}
        
        # Separate recent vs historical papers
        from datetime import datetime, timedelta
        one_week_ago = datetime.now() - timedelta(days=7)
        
        recent_papers_week = []
        historical_papers = []
        
        for paper in all_matching_papers:
            try:
                pub_date = datetime.strptime(paper.get('published', ''), '%Y-%m-%d')
                if pub_date >= one_week_ago:
                    recent_papers_week.append(paper)
                else:
                    historical_papers.append(paper)
            except ValueError:
                # If date parsing fails, consider it historical
                historical_papers.append(paper)
        
        insights = []
        
        # 1. Volume comparison
        if recent_papers_week and historical_papers:
            recent_count = len(recent_papers_week)
            historical_avg = len(historical_papers) / max(1, len(set(p.get('published', '')[:7] for p in historical_papers)))  # Average per week
            
            if recent_count > historical_avg * 1.5:
                insights.append(f"📈 **Increased Research Activity**: This week shows {recent_count} papers compared to an average of {historical_avg:.1f} papers per week historically - a significant increase in research output.")
            elif recent_count < historical_avg * 0.7:
                insights.append(f"📉 **Decreased Research Activity**: This week shows {recent_count} papers compared to an average of {historical_avg:.1f} papers per week historically - a notable decrease in research output.")
            else:
                insights.append(f"📊 **Steady Research Activity**: This week shows {recent_count} papers, consistent with historical averages of {historical_avg:.1f} papers per week.")
        
        # 2. Source distribution changes
        if recent_papers_week and historical_papers:
            recent_sources = {}
            historical_sources = {}
            
            for paper in recent_papers_week:
                source = paper.get('source', 'Unknown')
                recent_sources[source] = recent_sources.get(source, 0) + 1
            
            for paper in historical_papers:
                source = paper.get('source', 'Unknown')
                historical_sources[source] = historical_sources.get(source, 0) + 1
            
            # Find significant changes in source distribution
            for source in set(list(recent_sources.keys()) + list(historical_sources.keys())):
                recent_pct = (recent_sources.get(source, 0) / len(recent_papers_week)) * 100
                historical_pct = (historical_sources.get(source, 0) / len(historical_papers)) * 100
                
                if abs(recent_pct - historical_pct) > 15:  # Significant change
                    if recent_pct > historical_pct:
                        insights.append(f"🔬 **Source Shift**: {source} publications increased from {historical_pct:.1f}% to {recent_pct:.1f}% this week, indicating a shift in publication patterns.")
                    else:
                        insights.append(f"📚 **Source Shift**: {source} publications decreased from {historical_pct:.1f}% to {recent_pct:.1f}% this week.")
        
        # 3. Keyword evolution
        if recent_papers_week and historical_papers:
            recent_keywords = {}
            historical_keywords = {}
            
            for paper in recent_papers_week:
                for keyword in paper.get('matched_keywords', []):
                    recent_keywords[keyword] = recent_keywords.get(keyword, 0) + 1
            
            for paper in historical_papers:
                for keyword in paper.get('matched_keywords', []):
                    historical_keywords[keyword] = historical_keywords.get(keyword, 0) + 1
            
            # Find emerging keywords
            emerging_keywords = []
            for keyword, count in recent_keywords.items():
                historical_count = historical_keywords.get(keyword, 0)
                recent_freq = count / len(recent_papers_week)
                historical_freq = historical_count / len(historical_papers)
                
                if recent_freq > historical_freq * 2 and count >= 2:  # At least 2 occurrences and doubled frequency
                    emerging_keywords.append(keyword)
            
            if emerging_keywords:
                insights.append(f"🆕 **Emerging Keywords**: New focus areas this week include: {', '.join(emerging_keywords[:3])} - indicating evolving research directions.")
        
        # 4. Research quality trends
        if recent_papers_week and historical_papers:
            recent_scores = [p.get('relevance_score', 0) for p in recent_papers_week if p.get('relevance_score')]
            historical_scores = [p.get('relevance_score', 0) for p in historical_papers if p.get('relevance_score')]
            
            if recent_scores and historical_scores:
                recent_avg = sum(recent_scores) / len(recent_scores)
                historical_avg = sum(historical_scores) / len(historical_scores)
                
                if recent_avg > historical_avg + 0.5:
                    insights.append(f"⭐ **Quality Improvement**: Recent papers show higher average relevance scores ({recent_avg:.1f}) compared to historical average ({historical_avg:.1f}), indicating improved research quality.")
                elif recent_avg < historical_avg - 0.5:
                    insights.append(f"📊 **Quality Variation**: Recent papers show lower average relevance scores ({recent_avg:.1f}) compared to historical average ({historical_avg:.1f}).")
        
        # 5. Methodological trends
        if recent_papers_week:
            method_keywords = ['machine learning', 'deep learning', 'ai', 'artificial intelligence', 'neural network', 'transformer', 'cnn', 'rnn']
            recent_method_papers = 0
            
            for paper in recent_papers_week:
                abstract = paper.get('abstract', '').lower()
                title = paper.get('title', '').lower()
                if any(method in abstract or method in title for method in method_keywords):
                    recent_method_papers += 1
            
            method_percentage = (recent_method_papers / len(recent_papers_week)) * 100
            
            if method_percentage > 30:
                insights.append(f"🤖 **AI/ML Focus**: {method_percentage:.1f}% of recent papers focus on AI/ML methods, highlighting the growing importance of computational approaches in this field.")
        
        # 6. Clinical vs. Basic Research trends
        if recent_papers_week:
            clinical_keywords = ['clinical', 'patient', 'trial', 'therapy', 'treatment', 'diagnosis', 'prognosis']
            clinical_papers = 0
            
            for paper in recent_papers_week:
                abstract = paper.get('abstract', '').lower()
                title = paper.get('title', '').lower()
                if any(clinical in abstract or clinical in title for clinical in clinical_keywords):
                    clinical_papers += 1
            
            clinical_percentage = (clinical_papers / len(recent_papers_week)) * 100
            
            if clinical_percentage > 40:
                insights.append(f"🏥 **Clinical Focus**: {clinical_percentage:.1f}% of recent papers have clinical applications, showing strong translational research activity.")
            elif clinical_percentage < 20:
                insights.append(f"🔬 **Basic Research Focus**: {clinical_percentage:.1f}% of recent papers have clinical applications, indicating a focus on fundamental research.")
        
        # Generate focused summary of top 3 recent papers
        top_recent_papers = self._get_top_recent_papers(recent_papers_week, query, top_n=3)
        recent_papers_summary = self._summarize_recent_papers(query, top_recent_papers)

        # Build historical context paragraphs comparing top recent to prior similar papers
        historical_context_summary = self._build_historical_context(top_recent_papers, historical_papers, llm_client=llm_client)

        return {
            "insights": insights,
            "recent_papers_count": len(recent_papers_week),
            "historical_papers_count": len(historical_papers),
            "analysis_period": "Last 7 days vs. historical data",
            "recent_papers_summary": recent_papers_summary,
            "top_recent_papers": top_recent_papers,
            "historical_context_summary": historical_context_summary
        }
    
    def _get_top_recent_papers(self, recent_papers: List[Dict[str, Any]], query: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Get the top N most relevant recent papers for a query
        
        Args:
            recent_papers (List[Dict]): List of recent papers
            query (str): Search query
            top_n (int): Number of top papers to return
            
        Returns:
            List of top papers sorted by relevance
        """
        if not recent_papers:
            return []
        
        # Sort by relevance score and query match score
        sorted_papers = sorted(
            recent_papers, 
            key=lambda x: (x.get('relevance_score', 0), x.get('query_match_score', 0)), 
            reverse=True
        )
        
        return sorted_papers[:top_n]
    
    def _summarize_recent_papers(self, query: str, top_papers: List[Dict[str, Any]]) -> str:
        """
        Generate a focused summary of the top recent papers for a specific query
        
        Args:
            query (str): The search query
            top_papers (List[Dict]): Top recent papers
            
        Returns:
            String summary of the papers
        """
        if not top_papers:
            return f"No recent papers found for '{query}' in the past 7 days."
        
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        # Extract key information from each paper
        paper_summaries = []
        
        for i, paper in enumerate(top_papers, 1):
            title = paper.get('title', 'Unknown Title')
            authors = paper.get('authors', 'Unknown Authors')
            journal = paper.get('journal', 'Unknown Journal')
            abstract = paper.get('abstract', '')
            relevance_score = paper.get('relevance_score', 0)
            
            # Extract key sentences from abstract related to the query
            key_sentences = self._extract_relevant_sentences(abstract, query_terms)
            
            # Create focused summary for this paper
            paper_summary = f"**{i}. {title}** (Relevance: {relevance_score:.1f})\n"
            paper_summary += f"*{authors} | {journal}*\n\n"
            
            if key_sentences:
                paper_summary += f"**Key Findings:** {key_sentences}\n\n"
            else:
                # Fallback to first part of abstract if no specific sentences found
                abstract_preview = abstract[:200] + "..." if len(abstract) > 200 else abstract
                paper_summary += f"**Abstract:** {abstract_preview}\n\n"
            
            paper_summaries.append(paper_summary)
        
        # Create overall summary
        if len(top_papers) == 1:
            summary = f"## Recent Research Focus: '{query}'\n\n"
            summary += f"The most relevant paper from the past 7 days:\n\n"
        else:
            summary = f"## Recent Research Focus: '{query}'\n\n"
            summary += f"The {len(top_papers)} most relevant papers from the past 7 days:\n\n"
        
        summary += "\n".join(paper_summaries)
        
        # Add overall trend analysis
        summary += self._add_trend_analysis(query, top_papers)
        
        return summary
    
    def _extract_relevant_sentences(self, abstract: str, query_terms: List[str]) -> str:
        """
        Extract sentences from abstract that are most relevant to the query terms
        
        Args:
            abstract (str): Paper abstract
            query_terms (List[str]): Query terms to match
            
        Returns:
            String of relevant sentences
        """
        if not abstract or not query_terms:
            return ""
        
        # Split abstract into sentences
        sentences = abstract.split('. ')
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Count how many query terms appear in this sentence
            term_matches = sum(1 for term in query_terms if term in sentence_lower)
            
            if term_matches > 0:
                # Score based on term matches and sentence length
                score = term_matches / len(sentence.split())  # Normalize by sentence length
                relevant_sentences.append((score, sentence.strip()))
        
        # Sort by relevance score and take top 2 sentences
        relevant_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [sent[1] for sent in relevant_sentences[:2]]
        
        return ". ".join(top_sentences) + "." if top_sentences else ""
    
    def _add_trend_analysis(self, query: str, top_papers: List[Dict[str, Any]]) -> str:
        """
        Add trend analysis to the summary
        
        Args:
            query (str): The search query
            top_papers (List[Dict]): Top recent papers
            
        Returns:
            String with trend analysis
        """
        if not top_papers:
            return ""
        
        # Analyze common themes
        all_keywords = []
        all_abstracts = []
        
        for paper in top_papers:
            all_keywords.extend(paper.get('matched_keywords', []))
            all_abstracts.append(paper.get('abstract', ''))
        
        # Find most common keywords
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        common_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Analyze methodological approaches
        method_keywords = ['machine learning', 'deep learning', 'ai', 'neural network', 'transformer', 'cnn', 'rnn']
        clinical_keywords = ['clinical', 'patient', 'trial', 'therapy', 'treatment', 'diagnosis']
        
        method_papers = 0
        clinical_papers = 0
        
        for paper in top_papers:
            abstract = paper.get('abstract', '').lower()
            title = paper.get('title', '').lower()
            
            if any(method in abstract or method in title for method in method_keywords):
                method_papers += 1
            
            if any(clinical in abstract or clinical in title for clinical in clinical_keywords):
                clinical_papers += 1
        
        # Generate trend analysis
        trend_analysis = "\n## Key Trends in Recent Research\n\n"
        
        if common_keywords:
            trend_analysis += f"**Focus Areas:** The most prominent research themes include {', '.join([kw[0] for kw in common_keywords])}.\n\n"
        
        if method_papers > 0:
            method_pct = (method_papers / len(top_papers)) * 100
            trend_analysis += f"**Methodological Approach:** {method_pct:.0f}% of recent papers employ AI/ML methods, indicating a strong computational focus.\n\n"
        
        if clinical_papers > 0:
            clinical_pct = (clinical_papers / len(top_papers)) * 100
            trend_analysis += f"**Clinical Relevance:** {clinical_pct:.0f}% of recent papers have direct clinical applications, showing translational research activity.\n\n"
        
        # Add relevance quality note
        avg_relevance = sum(p.get('relevance_score', 0) for p in top_papers) / len(top_papers)
        if avg_relevance > 7:
            trend_analysis += f"**Research Quality:** Recent papers show high relevance scores (avg: {avg_relevance:.1f}), indicating strong alignment with current research priorities.\n\n"
        elif avg_relevance > 5:
            trend_analysis += f"**Research Quality:** Recent papers show moderate relevance scores (avg: {avg_relevance:.1f}), with good potential for impact.\n\n"
        
        return trend_analysis

    def _build_historical_context(self, recent_top: List[Dict[str, Any]], historical_papers: List[Dict[str, Any]], llm_client=None) -> str:
        """Create paragraphs that summarize prior similar papers in KB for each recent top paper.
        If no similar papers exist, state that explicitly.
        """
        if not recent_top:
            return ""
        if not historical_papers:
            return "\n## Historical Context\n\nNo similar prior papers found in the knowledge base.\n"

        # Use LLM-based similarity if available, otherwise fallback to Jaccard
        def to_text(p: Dict[str, Any]) -> str:
            title = p.get('title', '') or ''
            abstract = p.get('abstract', '') or ''
            keywords = ' '.join(p.get('matched_keywords', []) or [])
            return f"{title}. {abstract}. {keywords}"

        def tokenize(s: str) -> set:
            return set([t for t in (s.lower().replace('\n', ' ').split()) if t and t.isalpha()])

        sections: List[str] = ["\n## Historical Context\n"]
        
        # Check if LLM client is available for semantic similarity
        use_llm_similarity = llm_client and llm_client.is_available()
        
        if use_llm_similarity:
            print("🧠 Using LLM-based semantic similarity for historical context...")
        else:
            print("📊 Using Jaccard similarity for historical context (LLM not available)...")
            # Pre-compute token sets for Jaccard similarity
            hist_text_tokens = [tokenize(to_text(p)) for p in historical_papers]

        for idx, rp in enumerate(recent_top, 1):
            rp_text = to_text(rp)
            
            if use_llm_similarity:
                # Use LLM-based semantic similarity
                sims = []
                rp_text_short = rp_text[:1000]  # Limit text length for LLM processing
                
                for i, hp in enumerate(historical_papers):
                    hp_text = to_text(hp)[:1000]  # Limit text length
                    if hp_text.strip():
                        similarity_score = llm_client.calculate_similarity(rp_text_short, hp_text)
                        if similarity_score > 0.0:  # Only include if similarity > 0
                            sims.append((similarity_score, i))
                
                sims.sort(reverse=True)
                top_matches = [(score, historical_papers[i]) for score, i in sims[:2] if score >= 0.1]  # LLM threshold
                
            else:
                # Fallback to Jaccard similarity
                rp_tokens = tokenize(rp_text)
                if not rp_tokens:
                    sections.append(f"\n**{idx}. {rp.get('title','Untitled')}**\nNo similar prior papers found (insufficient text).\n")
                    continue

                # Compute Jaccard similarity with all historical papers and pick top 2
                sims = []
                for i, ht in enumerate(hist_text_tokens):
                    if not ht:
                        continue
                    inter = len(rp_tokens & ht)
                    union = len(rp_tokens | ht)
                    score = inter / union if union else 0.0
                    sims.append((score, i))

                sims.sort(reverse=True)
                top_matches = [(score, historical_papers[i]) for score, i in sims[:2] if score >= 0.08]  # Jaccard threshold

            title = rp.get('title', 'Untitled')
            journal = rp.get('journal', 'Unknown Journal')
            published = rp.get('published', 'N/A')

            if not top_matches:
                sections.append(f"\n**{idx}. {title}** ({journal}, {published})\nNo similar prior papers found in the KB.\n")
                continue

            para_lines = [f"\n**{idx}. {title}** ({journal}, {published})"]
            mentions = []
            for score, hp in top_matches:
                mentions.append(
                    f"'{hp.get('title','Untitled')}' ({hp.get('journal','Unknown Journal')}, {hp.get('published','N/A')}; similarity {score:.2f})"
                )
            if len(mentions) == 1:
                para_lines.append(f"Related prior work: {mentions[0]}.")
            else:
                para_lines.append(f"Related prior works include {mentions[0]} and {mentions[1]}.")

            # Add brief overlap via shared keywords if available
            rp_kws = set(rp.get('matched_keywords', []) or [])
            kw_overlaps = []
            for _, hp in top_matches:
                hp_kws = set(hp.get('matched_keywords', []) or [])
                ov = rp_kws & hp_kws
                if ov:
                    kw_overlaps.append(', '.join(list(ov)[:3]))
            if kw_overlaps:
                para_lines.append(f"Shared themes: {', '.join(kw_overlaps)}.")

            sections.append('\n'.join(para_lines) + "\n")

        return '\n'.join(sections)

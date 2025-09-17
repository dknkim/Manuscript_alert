"""
Text Processing for RAG System

This module handles text chunking, preprocessing, and preparation for embedding.
It creates searchable text chunks from paper abstracts and titles.
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    text: str
    paper_id: str
    chunk_type: str  # 'title', 'abstract', 'combined'
    metadata: Dict[str, Any]
    chunk_index: int = 0


class TextProcessor:
    """Processes and chunks text for RAG system"""
    
    def __init__(self, max_chunk_size: int = 512, overlap_size: int = 50):
        """
        Initialize text processor
        
        Args:
            max_chunk_size (int): Maximum characters per chunk
            overlap_size (int): Overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[TextChunk]:
        """
        Process papers and create text chunks
        
        Args:
            papers (List[Dict]): List of paper dictionaries
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        
        for i, paper in enumerate(papers):
            paper_chunks = self._process_single_paper(paper, i)
            chunks.extend(paper_chunks)
        
        return chunks
    
    def _process_single_paper(self, paper: Dict[str, Any], paper_index: int) -> List[TextChunk]:
        """Process a single paper and create chunks"""
        chunks = []
        
        # Create paper ID
        paper_id = self._create_paper_id(paper, paper_index)
        
        # Extract metadata
        metadata = self._extract_metadata(paper)
        
        # Process title
        title = paper.get('title', '').strip()
        if title:
            title_chunk = TextChunk(
                text=title,
                paper_id=paper_id,
                chunk_type='title',
                metadata=metadata,
                chunk_index=0
            )
            chunks.append(title_chunk)
        
        # Process abstract
        abstract = paper.get('abstract', '').strip()
        if abstract:
            abstract_chunks = self._chunk_text(abstract, paper_id, 'abstract', metadata)
            chunks.extend(abstract_chunks)
        
        # Create combined chunk (title + abstract)
        combined_text = f"{title}\n\n{abstract}".strip()
        if combined_text:
            combined_chunks = self._chunk_text(combined_text, paper_id, 'combined', metadata)
            chunks.extend(combined_chunks)
        
        return chunks
    
    def _create_paper_id(self, paper: Dict[str, Any], paper_index: int) -> str:
        """Create a unique ID for the paper"""
        title = paper.get('title', '')
        authors = paper.get('authors', '')
        published = paper.get('published', '')
        
        # Create a hash-like ID
        id_parts = [title[:50], authors[:30], published, str(paper_index)]
        paper_id = "_".join([part.replace(" ", "_") for part in id_parts if part])
        
        # Clean up the ID
        paper_id = re.sub(r'[^\w\-_]', '', paper_id)
        return paper_id[:100]  # Limit length
    
    def _extract_metadata(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from paper"""
        return {
            'title': paper.get('title', ''),
            'authors': paper.get('authors', ''),
            'published': paper.get('published', ''),
            'source': paper.get('source', ''),
            'journal': paper.get('journal', ''),
            'relevance_score': paper.get('relevance_score', 0),
            'matched_keywords': paper.get('matched_keywords', []),
            'url': paper.get('arxiv_url', ''),
            'pmid': paper.get('pmid', ''),
            'doi': paper.get('doi', ''),
            'week_info': paper.get('week_info', {}),
            'kb_file': paper.get('kb_file', '')
        }
    
    def _chunk_text(self, text: str, paper_id: str, chunk_type: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Split text into chunks"""
        if len(text) <= self.max_chunk_size:
            return [TextChunk(
                text=text,
                paper_id=paper_id,
                chunk_type=chunk_type,
                metadata=metadata,
                chunk_index=0
            )]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.max_chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.max_chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + self.max_chunk_size // 2:
                        end = word_end
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk = TextChunk(
                    text=chunk_text,
                    paper_id=paper_id,
                    chunk_type=chunk_type,
                    metadata=metadata,
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.overlap_size
            if start >= len(text):
                break
        
        return chunks
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better embedding
        
        Args:
            text (str): Input text
            
        Returns:
            Preprocessed text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases from text
        
        Args:
            text (str): Input text
            
        Returns:
            List of key phrases
        """
        # Simple key phrase extraction
        # Look for capitalized phrases and technical terms
        phrases = []
        
        # Find capitalized words/phrases
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        phrases.extend(capitalized)
        
        # Find technical terms (words with numbers or special patterns)
        technical = re.findall(r'\b\w*[0-9]+\w*\b', text)
        phrases.extend(technical)
        
        # Find quoted terms
        quoted = re.findall(r'"([^"]+)"', text)
        phrases.extend(quoted)
        
        # Remove duplicates and filter
        unique_phrases = list(set(phrases))
        filtered_phrases = [p for p in unique_phrases if len(p) > 2 and len(p) < 50]
        
        return filtered_phrases[:20]  # Limit to top 20
    
    def create_searchable_text(self, paper: Dict[str, Any]) -> str:
        """
        Create a comprehensive searchable text from paper
        
        Args:
            paper (Dict): Paper dictionary
            
        Returns:
            Searchable text string
        """
        parts = []
        
        # Title (weighted heavily)
        title = paper.get('title', '')
        if title:
            parts.append(f"Title: {title}")
        
        # Authors
        authors = paper.get('authors', '')
        if authors:
            parts.append(f"Authors: {authors}")
        
        # Abstract
        abstract = paper.get('abstract', '')
        if abstract:
            parts.append(f"Abstract: {abstract}")
        
        # Keywords
        keywords = paper.get('matched_keywords', [])
        if keywords:
            parts.append(f"Keywords: {', '.join(keywords)}")
        
        # Journal
        journal = paper.get('journal', '')
        if journal:
            parts.append(f"Journal: {journal}")
        
        # Source
        source = paper.get('source', '')
        if source:
            parts.append(f"Source: {source}")
        
        return "\n".join(parts)

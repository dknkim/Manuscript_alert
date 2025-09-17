"""
Main RAG System

This module integrates all RAG components to provide a complete retrieval-augmented generation system.
It handles query processing, document retrieval, and response generation.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st

from .kb_loader import KnowledgeBaseLoader
from .text_processor import TextProcessor
from .vector_store import VectorStore
from .llm_client import LLMClient, LLMFactory, create_rag_prompt, create_weekly_summary_prompt, create_simple_response


class RAGSystem:
    """Main RAG system that coordinates all components"""
    
    def __init__(self, kb_directory: str = "./KB", cache_dir: str = "./rag_cache"):
        """
        Initialize RAG system
        
        Args:
            kb_directory (str): Path to knowledge base directory
            cache_dir (str): Path to cache directory
        """
        self.kb_directory = kb_directory
        self.cache_dir = cache_dir
        
        # Initialize components
        self.kb_loader = KnowledgeBaseLoader(kb_directory)
        self.text_processor = TextProcessor()
        self.vector_store = VectorStore(cache_dir=cache_dir)
        self.llm_client: Optional[LLMClient] = None
        
        # System state
        self.is_initialized = False
        self.last_update = None
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
    
    def initialize(self, llm_client_type: str = "huggingface", 
                   llm_model: str = "microsoft/DialoGPT-medium",
                   force_rebuild: bool = False) -> bool:
        """
        Initialize the RAG system
        
        Args:
            llm_client_type (str): Type of LLM client to use
            llm_model (str): LLM model name
            force_rebuild (bool): Force rebuild of vector store
            
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize LLM client
            self.llm_client = LLMFactory.create_client(
                client_type=llm_client_type,
                model_name=llm_model
            )
            
            if not self.llm_client.is_available():
                st.warning(f"⚠️ LLM client {llm_client_type} is not available")
                return False
            
            # Load knowledge base
            st.info("📚 Loading knowledge base...")
            papers = self.kb_loader.load_all_kb_files(exclude_today=True)
            
            if not papers:
                st.error("❌ No papers found in knowledge base")
                return False
            
            st.info(f"📄 Found {len(papers)} papers")
            
            # Check if vector store needs rebuilding
            vector_store_file = os.path.join(self.cache_dir, "vector_store.pkl")
            if force_rebuild or not os.path.exists(vector_store_file):
                st.info("🔄 Building vector store...")
                self._build_vector_store(papers)
            else:
                st.info("📖 Loading existing vector store...")
                if not self.vector_store.load_from_disk():
                    st.info("🔄 Rebuilding vector store...")
                    self._build_vector_store(papers)
            
            self.is_initialized = True
            self.last_update = datetime.now()
            
            st.success("✅ RAG system initialized successfully!")
            return True
            
        except Exception as e:
            st.error(f"❌ Error initializing RAG system: {e}")
            return False
    
    def _build_vector_store(self, papers: List[Dict[str, Any]]):
        """Build vector store from papers"""
        # Process papers into text chunks
        text_chunks = self.text_processor.process_papers(papers)
        
        # Convert to format expected by vector store
        chunk_data = []
        for chunk in text_chunks:
            chunk_data.append({
                'text': chunk.text,
                'paper_id': chunk.paper_id,
                'chunk_type': chunk.chunk_type,
                'metadata': chunk.metadata,
                'chunk_index': chunk.chunk_index
            })
        
        # Add to vector store
        self.vector_store.add_documents(chunk_data)
        
        # Save to disk
        self.vector_store.save_to_disk()
    
    def query(self, question: str, top_k: int = 5, 
              use_metadata_filter: bool = False,
              metadata_filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query and return response
        
        Args:
            question (str): User question
            top_k (int): Number of documents to retrieve
            use_metadata_filter (bool): Whether to use metadata filtering
            metadata_filter (Dict): Metadata filter criteria
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.is_initialized:
            return {
                "response": "❌ RAG system not initialized",
                "context_docs": [],
                "error": "System not initialized"
            }
        
        try:
            # Retrieve relevant documents
            if use_metadata_filter and metadata_filter:
                results = self.vector_store.search_by_metadata(
                    question, metadata_filter, top_k
                )
            else:
                results = self.vector_store.search(question, top_k)
            
            if not results:
                return {
                    "response": "❌ No relevant documents found for your query",
                    "context_docs": [],
                    "error": "No documents found"
                }
            
            # Extract context documents
            context_docs = []
            for doc, similarity in results:
                context_docs.append({
                    'title': doc.metadata.get('title', ''),
                    'authors': doc.metadata.get('authors', ''),
                    'abstract': doc.text,
                    'journal': doc.metadata.get('journal', ''),
                    'published': doc.metadata.get('published', ''),
                    'source': doc.metadata.get('source', ''),
                    'relevance_score': doc.metadata.get('relevance_score', 0),
                    'similarity_score': similarity,
                    'url': doc.metadata.get('url', ''),
                    'pmid': doc.metadata.get('pmid', ''),
                    'doi': doc.metadata.get('doi', '')
                })
            
            # Generate response using LLM
            prompt = create_rag_prompt(question, context_docs)
            response = self.llm_client.generate_response(prompt, max_tokens=800)
            
            # If LLM response indicates an error, use simple response
            if response.startswith("❌"):
                response = create_simple_response(question, context_docs)
            
            return {
                "response": response,
                "context_docs": context_docs,
                "query": question,
                "timestamp": datetime.now().isoformat(),
                "num_docs_retrieved": len(context_docs)
            }
            
        except Exception as e:
            return {
                "response": f"❌ Error processing query: {e}",
                "context_docs": [],
                "error": str(e)
            }
    
    def get_weekly_summary(self, weeks_back: int = 1, 
                          top_k: int = 20) -> Dict[str, Any]:
        """
        Generate a weekly summary of research changes
        
        Args:
            weeks_back (int): Number of weeks to look back
            top_k (int): Number of papers to include
            
        Returns:
            Dictionary with summary and metadata
        """
        if not self.is_initialized:
            return {
                "summary": "❌ RAG system not initialized",
                "papers": [],
                "error": "System not initialized"
            }
        
        try:
            # Get papers from the specified time period
            start_date = datetime.now() - timedelta(weeks=weeks_back)
            end_date = datetime.now()
            
            papers = self.kb_loader.get_papers_by_date_range(start_date, end_date)
            
            if not papers:
                return {
                    "summary": f"❌ No papers found for the last {weeks_back} week(s)",
                    "papers": [],
                    "error": "No papers found"
                }
            
            # Sort by relevance score and take top papers
            papers.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            top_papers = papers[:top_k]
            
            # Generate summary using LLM
            week_range = f"the last {weeks_back} week(s)"
            prompt = create_weekly_summary_prompt(top_papers, week_range)
            summary = self.llm_client.generate_response(prompt, max_tokens=1000)
            
            return {
                "summary": summary,
                "papers": top_papers,
                "week_range": week_range,
                "num_papers": len(top_papers),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "summary": f"❌ Error generating summary: {e}",
                "papers": [],
                "error": str(e)
            }
    
    def search_by_topic(self, topic: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for papers by topic
        
        Args:
            topic (str): Topic to search for
            top_k (int): Number of results to return
            
        Returns:
            List of relevant papers
        """
        if not self.is_initialized:
            return []
        
        try:
            results = self.vector_store.search(topic, top_k)
            
            papers = []
            for doc, similarity in results:
                papers.append({
                    'title': doc.metadata.get('title', ''),
                    'authors': doc.metadata.get('authors', ''),
                    'abstract': doc.text,
                    'journal': doc.metadata.get('journal', ''),
                    'published': doc.metadata.get('published', ''),
                    'source': doc.metadata.get('source', ''),
                    'relevance_score': doc.metadata.get('relevance_score', 0),
                    'similarity_score': similarity,
                    'url': doc.metadata.get('url', ''),
                    'pmid': doc.metadata.get('pmid', ''),
                    'doi': doc.metadata.get('doi', '')
                })
            
            return papers
            
        except Exception as e:
            st.error(f"❌ Error searching by topic: {e}")
            return []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and statistics"""
        status = {
            "initialized": self.is_initialized,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "kb_directory": self.kb_directory,
            "cache_dir": self.cache_dir
        }
        
        if self.is_initialized:
            # KB statistics
            kb_stats = self.kb_loader.get_statistics()
            status["kb_statistics"] = kb_stats
            
            # Vector store statistics
            vector_stats = self.vector_store.get_statistics()
            status["vector_store_statistics"] = vector_stats
            
            # LLM client status
            if self.llm_client:
                status["llm_client"] = {
                    "type": type(self.llm_client).__name__,
                    "available": self.llm_client.is_available()
                }
        
        return status
    
    def rebuild_index(self) -> bool:
        """Rebuild the vector store index"""
        try:
            st.info("🔄 Rebuilding vector store index...")
            
            # Clear existing vector store
            self.vector_store.clear()
            
            # Reload papers
            papers = self.kb_loader.load_all_kb_files(exclude_today=True)
            
            if not papers:
                st.error("❌ No papers found to rebuild index")
                return False
            
            # Rebuild vector store
            self._build_vector_store(papers)
            
            self.last_update = datetime.now()
            st.success("✅ Vector store index rebuilt successfully!")
            return True
            
        except Exception as e:
            st.error(f"❌ Error rebuilding index: {e}")
            return False
    
    def export_context(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Export context for a query without generating response
        
        Args:
            query (str): Query string
            top_k (int): Number of documents to retrieve
            
        Returns:
            Dictionary with context documents
        """
        if not self.is_initialized:
            return {"error": "System not initialized"}
        
        try:
            results = self.vector_store.search(query, top_k)
            
            context_docs = []
            for doc, similarity in results:
                context_docs.append({
                    'title': doc.metadata.get('title', ''),
                    'authors': doc.metadata.get('authors', ''),
                    'abstract': doc.text,
                    'journal': doc.metadata.get('journal', ''),
                    'published': doc.metadata.get('published', ''),
                    'source': doc.metadata.get('source', ''),
                    'relevance_score': doc.metadata.get('relevance_score', 0),
                    'similarity_score': similarity,
                    'url': doc.metadata.get('url', ''),
                    'pmid': doc.metadata.get('pmid', ''),
                    'doi': doc.metadata.get('doi', '')
                })
            
            return {
                "query": query,
                "context_docs": context_docs,
                "num_docs": len(context_docs),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}

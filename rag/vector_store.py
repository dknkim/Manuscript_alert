"""
Vector Store for RAG System

This module handles vector embeddings and similarity search using sentence-transformers.
It provides a simple but effective vector store for the RAG system.
"""

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
import streamlit as st


@dataclass
class VectorDocument:
    """Represents a document with its vector embedding"""
    text: str
    paper_id: str
    chunk_type: str
    metadata: Dict[str, Any]
    chunk_index: int
    embedding: Optional[np.ndarray] = None


class VectorStore:
    """Simple vector store for RAG system"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "./rag_cache"):
        """
        Initialize vector store
        
        Args:
            model_name (str): Sentence transformer model name
            cache_dir (str): Directory for caching embeddings
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.model = None
        self.documents: List[VectorDocument] = []
        self.embeddings: Optional[np.ndarray] = None
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize model
        self._load_model()
    
    def is_available(self) -> bool:
        """Check if vector store is ready for use"""
        return self.model is not None and self.embeddings is not None and len(self.documents) > 0
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            # Use Streamlit cache for the model
            @st.cache_resource
            def load_sentence_transformer(model_name):
                return SentenceTransformer(model_name)
            
            self.model = load_sentence_transformer(self.model_name)
            print(f"✅ Loaded model: {self.model_name}")
        except Exception as e:
            print(f"❌ Error loading model {self.model_name}: {e}")
            # Fallback to a smaller model
            try:
                self.model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
                print("✅ Loaded fallback model: paraphrase-MiniLM-L6-v2")
            except Exception as e2:
                print(f"❌ Error loading fallback model: {e2}")
                raise e2
    
    def add_documents(self, text_chunks: List[Dict[str, Any]]):
        """
        Add text chunks to the vector store
        
        Args:
            text_chunks: List of text chunk dictionaries
        """
        if not self.model:
            raise ValueError("Model not loaded")
        
        # Convert to VectorDocument objects
        new_docs = []
        for chunk in text_chunks:
            doc = VectorDocument(
                text=chunk['text'],
                paper_id=chunk['paper_id'],
                chunk_type=chunk['chunk_type'],
                metadata=chunk['metadata'],
                chunk_index=chunk['chunk_index']
            )
            new_docs.append(doc)
        
        # Generate embeddings
        texts = [doc.text for doc in new_docs]
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Add embeddings to documents
        for doc, embedding in zip(new_docs, embeddings):
            doc.embedding = embedding
        
        # Add to store
        self.documents.extend(new_docs)
        
        # Update embeddings matrix
        self._update_embeddings_matrix()
        
        print(f"✅ Added {len(new_docs)} documents to vector store")
    
    def _update_embeddings_matrix(self):
        """Update the embeddings matrix"""
        if not self.documents:
            self.embeddings = None
            return
        
        embeddings_list = [doc.embedding for doc in self.documents if doc.embedding is not None]
        if embeddings_list:
            self.embeddings = np.vstack(embeddings_list)
        else:
            self.embeddings = None
    
    def search(self, query: str, top_k: int = 5, similarity_threshold: float = 0.0) -> List[Tuple[VectorDocument, float]]:
        """
        Search for similar documents
        
        Args:
            query (str): Search query
            top_k (int): Number of results to return
            similarity_threshold (float): Minimum similarity score
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.model or not self.embeddings is not None:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity >= similarity_threshold:
                doc = self.documents[idx]
                results.append((doc, similarity))
        
        return results
    
    def search_by_metadata(self, query: str, metadata_filter: Dict[str, Any], 
                          top_k: int = 5) -> List[Tuple[VectorDocument, float]]:
        """
        Search with metadata filtering
        
        Args:
            query (str): Search query
            metadata_filter (Dict): Metadata filters
            top_k (int): Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        # First filter by metadata
        filtered_docs = []
        filtered_indices = []
        
        for i, doc in enumerate(self.documents):
            if self._matches_metadata_filter(doc.metadata, metadata_filter):
                filtered_docs.append(doc)
                filtered_indices.append(i)
        
        if not filtered_docs:
            return []
        
        # Search within filtered documents
        if not self.model:
            return []
        
        query_embedding = self.model.encode([query])
        filtered_embeddings = self.embeddings[filtered_indices]
        
        similarities = np.dot(filtered_embeddings, query_embedding.T).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            doc = filtered_docs[idx]
            results.append((doc, similarity))
        
        return results
    
    def _matches_metadata_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches the filter"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            
            metadata_value = metadata[key]
            
            # Handle different filter types
            if isinstance(value, list):
                if not any(v in str(metadata_value) for v in value):
                    return False
            elif isinstance(value, str):
                if value.lower() not in str(metadata_value).lower():
                    return False
            else:
                # Handle numpy arrays and other complex types
                if isinstance(metadata_value, np.ndarray):
                    if not isinstance(value, np.ndarray) or not np.array_equal(metadata_value, value):
                        return False
                elif isinstance(value, np.ndarray):
                    if not np.array_equal(metadata_value, value):
                        return False
                else:
                    if metadata_value != value:
                        return False
        
        return True
    
    def get_document_by_id(self, paper_id: str) -> Optional[VectorDocument]:
        """Get document by paper ID"""
        for doc in self.documents:
            if doc.paper_id == paper_id:
                return doc
        return None
    
    def get_documents_by_type(self, chunk_type: str) -> List[VectorDocument]:
        """Get all documents of a specific type"""
        return [doc for doc in self.documents if doc.chunk_type == chunk_type]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.documents:
            return {"total_documents": 0}
        
        # Count by type
        type_counts = {}
        for doc in self.documents:
            type_counts[doc.chunk_type] = type_counts.get(doc.chunk_type, 0) + 1
        
        # Count by source
        source_counts = {}
        for doc in self.documents:
            source = doc.metadata.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Date range
        dates = []
        for doc in self.documents:
            try:
                from datetime import datetime
                date_str = doc.metadata.get('published', '')
                if date_str:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    dates.append(date)
            except ValueError:
                continue
        
        date_range = {}
        if dates:
            date_range = {
                "earliest": min(dates).strftime('%Y-%m-%d'),
                "latest": max(dates).strftime('%Y-%m-%d')
            }
        
        return {
            "total_documents": len(self.documents),
            "embedding_dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "type_counts": type_counts,
            "source_counts": source_counts,
            "date_range": date_range,
            "model_name": self.model_name
        }
    
    def save_to_disk(self, filename: str = "vector_store.pkl"):
        """Save vector store to disk"""
        filepath = os.path.join(self.cache_dir, filename)
        
        # Prepare data for saving
        save_data = {
            "model_name": self.model_name,
            "documents": [asdict(doc) for doc in self.documents],
            "embeddings": self.embeddings.tolist() if self.embeddings is not None else None
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        print(f"✅ Vector store saved to {filepath}")
    
    def load_from_disk(self, filename: str = "vector_store.pkl") -> bool:
        """Load vector store from disk"""
        filepath = os.path.join(self.cache_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
            
            # Restore data
            self.model_name = save_data["model_name"]
            self.embeddings = np.array(save_data["embeddings"]) if save_data["embeddings"] else None
            
            # Restore documents
            self.documents = []
            for doc_data in save_data["documents"]:
                doc = VectorDocument(
                    text=doc_data["text"],
                    paper_id=doc_data["paper_id"],
                    chunk_type=doc_data["chunk_type"],
                    metadata=doc_data["metadata"],
                    chunk_index=doc_data["chunk_index"],
                    embedding=np.array(doc_data["embedding"]) if doc_data["embedding"] is not None else None
                )
                self.documents.append(doc)
            
            print(f"✅ Vector store loaded from {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading vector store: {e}")
            return False
    
    def clear(self):
        """Clear the vector store"""
        self.documents = []
        self.embeddings = None
        print("✅ Vector store cleared")

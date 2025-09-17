"""
LLM Client for RAG System

This module provides interfaces to various free LLM services for the RAG system.
Supports multiple free LLM options including Hugging Face, Ollama, and others.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional, Generator
from abc import ABC, abstractmethod
import streamlit as st

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available"""
        pass


class HuggingFaceClient(LLMClient):
    """Client for Hugging Face free models"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", api_token: Optional[str] = None):
        """
        Initialize Hugging Face client
        
        Args:
            model_name (str): Hugging Face model name
            api_token (str): Hugging Face API token (optional for free tier)
        """
        self.model_name = model_name
        self.api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        self.base_url = "https://api-inference.huggingface.co/models"
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response using Hugging Face API"""
        if not self.is_available():
            return "❌ Hugging Face service not available"
        
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_tokens,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/{self.model_name}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "No response generated")
                else:
                    return str(result)
            elif response.status_code == 401:
                return "❌ Hugging Face API requires authentication. Please try a different LLM client (like Groq or Ollama) or get a free API token from https://huggingface.co/settings/tokens"
            elif response.status_code == 429:
                return "❌ Hugging Face API rate limit exceeded. Please try again later or use a different LLM client."
            else:
                return f"❌ API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Hugging Face service is available"""
        try:
            response = requests.get("https://huggingface.co", timeout=5)
            return response.status_code == 200
        except:
            return False


class OllamaClient(LLMClient):
    """Client for local Ollama models"""
    
    def __init__(self, model_name: str = "llama2:7b", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client
        
        Args:
            model_name (str): Ollama model name
            base_url (str): Ollama server URL
        """
        self.model_name = model_name
        self.base_url = base_url
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response using Ollama"""
        if not self.is_available():
            return "❌ Ollama service not available. Please start Ollama server."
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated")
            else:
                return f"❌ API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class GroqClient(LLMClient):
    """Client for Groq free API (Llama models)"""
    
    def __init__(self, model_name: str = "llama2-7b-4096", api_key: Optional[str] = None):
        """
        Initialize Groq client
        
        Args:
            model_name (str): Groq model name
            api_key (str): Groq API key
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response using Groq API"""
        if not self.is_available():
            return "❌ Groq service not available. Please set GROQ_API_KEY environment variable."
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"❌ API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Groq service is available"""
        return self.api_key is not None


class SimpleLocalClient(LLMClient):
    """Simple local client using transformers library"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-small"):
        """
        Initialize simple local client
        
        Args:
            model_name (str): Hugging Face model name for local inference
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the model and tokenizer"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            @st.cache_resource
            def load_local_model(model_name):
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForCausalLM.from_pretrained(model_name)
                return tokenizer, model
            
            self.tokenizer, self.model = load_local_model(self.model_name)
            print(f"✅ Loaded local model: {self.model_name}")
        except Exception as e:
            print(f"❌ Error loading local model: {e}")
            self.model = None
            self.tokenizer = None
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response using local model"""
        if not self.is_available():
            return "❌ Local model not available"
        
        if not TORCH_AVAILABLE:
            return "❌ PyTorch not available for local model"
        
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + max_tokens,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the original prompt from response
            response = response[len(prompt):].strip()
            
            return response if response else "No response generated"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if local model is available"""
        return self.model is not None and self.tokenizer is not None


class LLMFactory:
    """Factory for creating LLM clients"""
    
    @staticmethod
    def create_client(client_type: str = "huggingface", **kwargs) -> LLMClient:
        """
        Create an LLM client
        
        Args:
            client_type (str): Type of client to create
            **kwargs: Additional arguments for the client
            
        Returns:
            LLMClient instance
        """
        if client_type.lower() == "huggingface":
            return HuggingFaceClient(**kwargs)
        elif client_type.lower() == "ollama":
            return OllamaClient(**kwargs)
        elif client_type.lower() == "groq":
            return GroqClient(**kwargs)
        elif client_type.lower() == "local":
            return SimpleLocalClient(**kwargs)
        else:
            raise ValueError(f"Unknown client type: {client_type}")
    
    @staticmethod
    def get_available_clients() -> List[Dict[str, Any]]:
        """Get list of available LLM clients"""
        clients = [
            {
                "type": "huggingface",
                "name": "Hugging Face (Free)",
                "description": "Free models via Hugging Face API",
                "models": ["microsoft/DialoGPT-medium", "gpt2", "distilgpt2"]
            },
            {
                "type": "ollama",
                "name": "Ollama (Local)",
                "description": "Local models via Ollama",
                "models": ["llama2:7b", "llama2:13b", "codellama:7b"]
            },
            {
                "type": "groq",
                "name": "Groq (Free API)",
                "description": "Fast free API with Llama models",
                "models": ["llama2-7b-4096", "llama2-70b-4096", "mixtral-8x7b-32768"]
            },
            {
                "type": "local",
                "name": "Local Transformers",
                "description": "Local models using transformers",
                "models": ["microsoft/DialoGPT-small", "gpt2", "distilgpt2"]
            }
        ]
        
        return clients


def create_simple_response(query: str, context_docs: List[Dict[str, Any]]) -> str:
    """
    Create a simple response when LLM is not available
    
    Args:
        query (str): User query
        context_docs (List[Dict]): Retrieved context documents
        
    Returns:
        Simple formatted response
    """
    if not context_docs:
        return "❌ No relevant documents found for your query. Please try different keywords or check if your knowledge base has been updated."
    
    response = f"**Query:** {query}\n\n"
    response += f"**Found {len(context_docs)} relevant papers:**\n\n"
    
    for i, doc in enumerate(context_docs, 1):
        title = doc.get('title', 'Unknown Title')
        authors = doc.get('authors', 'Unknown Authors')
        journal = doc.get('journal', 'Unknown Journal')
        published = doc.get('published', 'Unknown Date')
        relevance = doc.get('relevance_score', 0)
        similarity = doc.get('similarity_score', 0)
        
        response += f"**{i}. {title}**\n"
        response += f"- Authors: {authors}\n"
        response += f"- Journal: {journal}\n"
        response += f"- Published: {published}\n"
        response += f"- Relevance Score: {relevance:.1f}\n"
        response += f"- Similarity Score: {similarity:.3f}\n\n"
    
    response += "**Note:** This is a simple summary. For AI-generated insights, please configure an LLM client (Groq, Ollama, or Hugging Face with API token)."
    
    return response


def create_rag_prompt(query: str, context_docs: List[Dict[str, Any]], 
                     system_prompt: str = None) -> str:
    """
    Create a RAG prompt with context
    
    Args:
        query (str): User query
        context_docs (List[Dict]): Retrieved context documents
        system_prompt (str): System prompt (optional)
        
    Returns:
        Formatted prompt string
    """
    if system_prompt is None:
        system_prompt = """You are a helpful research assistant specializing in Alzheimer's disease and neuroimaging research. 
        You have access to recent research papers and can provide insights based on the latest findings.
        Please provide accurate, evidence-based responses using the provided context."""
    
    # Format context
    context_text = ""
    for i, doc in enumerate(context_docs, 1):
        title = doc.get('title', 'Unknown Title')
        abstract = doc.get('abstract', 'No abstract available')
        authors = doc.get('authors', 'Unknown Authors')
        journal = doc.get('journal', 'Unknown Journal')
        published = doc.get('published', 'Unknown Date')
        
        context_text += f"""
Document {i}:
Title: {title}
Authors: {authors}
Journal: {journal}
Published: {published}
Abstract: {abstract}

"""
    
    # Create final prompt
    prompt = f"""{system_prompt}

Context from recent research papers:
{context_text}

User Question: {query}

Please provide a comprehensive answer based on the context above. If the context doesn't contain enough information to answer the question, please say so and suggest what additional information might be needed.

Answer:"""
    
    return prompt


def create_weekly_summary_prompt(context_docs: List[Dict[str, Any]], 
                                week_range: str = "this week") -> str:
    """
    Create a prompt for weekly research summary
    
    Args:
        context_docs (List[Dict]): Retrieved context documents
        week_range (str): Time range description
        
    Returns:
        Formatted prompt string
    """
    # Group papers by topic/keywords
    topics = {}
    for doc in context_docs:
        keywords = doc.get('matched_keywords', [])
        for keyword in keywords:
            if keyword not in topics:
                topics[keyword] = []
            topics[keyword].append(doc)
    
    # Create context text
    context_text = ""
    for topic, papers in topics.items():
        context_text += f"\n## {topic.upper()}:\n"
        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'Unknown Title')
            abstract = paper.get('abstract', 'No abstract available')[:300] + "..."
            journal = paper.get('journal', 'Unknown Journal')
            
            context_text += f"""
{i}. {title}
   Journal: {journal}
   Key findings: {abstract}

"""
    
    prompt = f"""You are a research analyst summarizing the latest developments in Alzheimer's disease and neuroimaging research.

Based on the following research papers from {week_range}, please provide a comprehensive summary that includes:

1. **Key Research Themes**: What are the main research areas and topics?
2. **Notable Findings**: What are the most significant discoveries or insights?
3. **Methodological Advances**: Any new techniques, tools, or approaches?
4. **Clinical Implications**: How might these findings impact patient care?
5. **Future Directions**: What research gaps or opportunities are identified?

Research Papers from {week_range}:
{context_text}

Please provide a well-structured summary that would be valuable for researchers and clinicians in the field.

Summary:"""
    
    return prompt

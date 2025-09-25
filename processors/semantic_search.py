"""
Semantic Search for Paper Discovery

Provides semantic search using Hugging Face models. Tries SmolLM2-135M first
(HuggingFaceTB/SmolLM2-135M) and falls back to common encoder models.
Handles tokenizers without pad_token (sets to eos_token) and supports both
encoder and causal models for embedding extraction via mean pooling.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd
import torch
import streamlit as st
from transformers import (
    AutoTokenizer,
    AutoModel,
    AutoModelForCausalLM,
)


class SemanticSearcher:
    """Lightweight semantic search with robust HF model loading."""

    def __init__(self):
        self.model_name: str | None = None
        self.tokenizer = None
        self.model = None
        self.is_causal: bool = False
        self._load_model()

    def _load_model(self) -> None:
        """Load best-available model for embeddings.

        Preference order:
        1) HuggingFaceTB/SmolLM2-135M (causal)
        2) sentence-transformers/all-MiniLM-L6-v2 (encoder)
        3) distilbert-base-uncased (encoder)
        """

        candidates = [
            ("HuggingFaceTB/SmolLM2-135M", "causal"),
            ("sentence-transformers/all-MiniLM-L6-v2", "encoder"),
            ("distilbert-base-uncased", "encoder"),
        ]

        @st.cache_resource
        def _load(name: str, kind: str):
            # Load tokenizer first
            tok = AutoTokenizer.from_pretrained(name)
            
            # Set pad_token if not present
            if tok.pad_token is None:
                if tok.eos_token is not None:
                    tok.pad_token = tok.eos_token
                else:
                    tok.add_special_tokens({"pad_token": "[PAD]"})
            
            # Load model based on kind
            if kind == "causal":
                mdl = AutoModelForCausalLM.from_pretrained(name)
                return tok, mdl, True
            else:  # encoder
                mdl = AutoModel.from_pretrained(name)
                return tok, mdl, False

        for name, kind in candidates:
            try:
                tokenizer, model, is_causal = _load(name, kind)

                self.model_name = name
                self.tokenizer = tokenizer
                self.model = model
                self.is_causal = is_causal
                print(f"✅ Loaded semantic search model: {name}")
                return
            except Exception as e:
                print(f"⚠️ Failed to load {name}: {e}")

        print("❌ No semantic search model could be loaded")

    def is_available(self) -> bool:
        return self.tokenizer is not None and self.model is not None

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        if not self.is_available():
            return np.array([])

        try:
            device = torch.device("cpu")
            self.model.to(device)  # type: ignore[union-attr]

            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )

            # Move to device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)  # type: ignore[misc]
                
                # Handle different output types for encoder vs causal models
                if hasattr(outputs, 'last_hidden_state'):
                    # Encoder model
                    hidden = outputs.last_hidden_state  # [batch, seq, hidden]
                elif hasattr(outputs, 'hidden_states') and outputs.hidden_states is not None:
                    # Causal model - use last hidden state
                    hidden = outputs.hidden_states[-1]  # [batch, seq, hidden]
                else:
                    # Fallback - try to get logits and use them as embeddings
                    if hasattr(outputs, 'logits'):
                        hidden = outputs.logits  # [batch, seq, vocab_size]
                    else:
                        raise ValueError("Cannot extract embeddings from model output")
                
                # Mean pool over sequence length (mask padded positions)
                if "attention_mask" in inputs:
                    mask = inputs["attention_mask"].unsqueeze(-1).float()  # [batch, seq, 1]
                    masked = hidden * mask
                    summed = masked.sum(dim=1)
                    lengths = mask.sum(dim=1).clamp(min=1e-6)
                    emb = summed / lengths
                else:
                    emb = hidden.mean(dim=1)

            return emb.cpu().numpy()
        except Exception as e:
            print(f"❌ Error getting embeddings: {e}")
            return np.array([])

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        return self._encode_texts(texts)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        if a.ndim == 1:
            a = a.reshape(1, -1)
        if b.ndim == 1:
            b = b.reshape(1, -1)
        a = a.astype(np.float32)
        b = b.astype(np.float32)
        a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
        b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
        sim = np.dot(a_norm, b_norm.T)
        return sim[0]

    def search_papers(self, papers_df: pd.DataFrame, query: str, top_k: int = 50) -> pd.DataFrame:
        if not self.is_available() or papers_df.empty:
            return papers_df

        try:
            texts: List[str] = []
            for _, row in papers_df.iterrows():
                title = str(row.get("title", ""))
                abstract = str(row.get("abstract", ""))
                authors = str(row.get("authors", ""))
                texts.append(f"{title}. {abstract}. {authors}")

            paper_emb = self.get_embeddings(texts)
            if paper_emb.size == 0:
                print("⚠️ No paper embeddings generated")
                return papers_df

            query_emb = self.get_embeddings([query])
            if query_emb.size == 0:
                print("⚠️ No query embedding generated")
                return papers_df

            sims = self._cosine_similarity(query_emb, paper_emb)
            ranked = papers_df.copy()
            ranked["semantic_similarity"] = sims
            ranked = ranked.sort_values("semantic_similarity", ascending=False).reset_index(drop=True)
            return ranked.head(top_k)
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return papers_df

    def get_search_explanation(self) -> str:
        return (
            "**🧠 Semantic Search** ranks your results by conceptual similarity using Hugging Face "
            "embeddings (SmolLM2-135M when available)."
        )


@st.cache_resource
def get_semantic_searcher() -> SemanticSearcher:
    return SemanticSearcher()
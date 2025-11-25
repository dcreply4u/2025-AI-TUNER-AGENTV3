"""
Vector Knowledge Base with Semantic Search

Uses sentence embeddings for semantic search instead of keyword matching.
Provides much better understanding of user intent and related concepts.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

LOGGER = logging.getLogger(__name__)

# Try to import sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore

# Fallback: Use simple TF-IDF if sentence transformers not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None  # type: ignore
    cosine_similarity = None  # type: ignore

from services.ai_advisor_q_enhanced import KnowledgeEntry


class VectorKnowledgeBase:
    """
    Vector-based knowledge base with semantic search.
    
    Uses sentence embeddings for better understanding of meaning,
    not just keywords. Can find relevant information even without
    exact keyword matches.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector knowledge base.
        
        Args:
            model_name: Sentence transformer model name
        """
        self.embeddings: Dict[str, np.ndarray] = {}
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.model = None
        self.vectorizer = None
        self.use_embeddings = False
        
        # Try to use sentence transformers (best option)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                self.use_embeddings = True
                LOGGER.info("Using sentence transformers for semantic search")
            except Exception as e:
                LOGGER.warning("Failed to load sentence transformer: %s", e)
                self.use_embeddings = False
        
        # Fallback to TF-IDF if sentence transformers not available
        if not self.use_embeddings and SKLEARN_AVAILABLE:
            try:
                self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                LOGGER.info("Using TF-IDF for semantic search (fallback)")
            except Exception as e:
                LOGGER.warning("Failed to initialize TF-IDF: %s", e)
        
        if not self.use_embeddings and not self.vectorizer:
            LOGGER.warning("No semantic search available, falling back to keyword matching")
    
    def add_entry(self, entry: KnowledgeEntry) -> None:
        """
        Add knowledge entry to vector database.
        
        Args:
            entry: Knowledge entry to add
        """
        self.entries[entry.topic] = entry
        
        if self.use_embeddings and self.model:
            # Generate embedding for entry
            text = f"{entry.topic} {entry.content} {' '.join(entry.keywords)}"
            embedding = self.model.encode(text, convert_to_numpy=True)
            self.embeddings[entry.topic] = embedding
        elif self.vectorizer:
            # Will build TF-IDF matrix when searching
            pass
    
    def add_entries(self, entries: List[KnowledgeEntry]) -> None:
        """
        Add multiple knowledge entries.
        
        Args:
            entries: List of knowledge entries
        """
        for entry in entries:
            self.add_entry(entry)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Search knowledge base using semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            min_score: Minimum similarity score (0-1)
        
        Returns:
            List of (KnowledgeEntry, similarity_score) tuples
        """
        if not self.entries:
            return []
        
        if self.use_embeddings and self.model and self.embeddings:
            return self._search_embeddings(query, top_k, min_score)
        elif self.vectorizer:
            return self._search_tfidf(query, top_k, min_score)
        else:
            return self._search_keywords(query, top_k)
    
    def _search_embeddings(
        self,
        query: str,
        top_k: int,
        min_score: float
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Search using sentence embeddings."""
        # Generate query embedding
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Calculate cosine similarity with all entries
        similarities = {}
        for topic, embedding in self.embeddings.items():
            # Cosine similarity
            dot_product = np.dot(query_embedding, embedding)
            norm_query = np.linalg.norm(query_embedding)
            norm_embedding = np.linalg.norm(embedding)
            
            if norm_query > 0 and norm_embedding > 0:
                similarity = dot_product / (norm_query * norm_embedding)
                # Normalize to 0-1 range (cosine similarity is -1 to 1)
                similarity = (similarity + 1) / 2
                similarities[topic] = similarity
        
        # Filter by min_score and sort
        filtered = [(topic, score) for topic, score in similarities.items() if score >= min_score]
        sorted_topics = sorted(filtered, key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        results = []
        for topic, score in sorted_topics[:top_k]:
            if topic in self.entries:
                results.append((self.entries[topic], score))
        
        return results
    
    def _search_tfidf(
        self,
        query: str,
        top_k: int,
        min_score: float
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Search using TF-IDF (fallback method)."""
        # Build text corpus from entries
        texts = []
        topics = []
        for topic, entry in self.entries.items():
            text = f"{entry.topic} {entry.content} {' '.join(entry.keywords)}"
            texts.append(text)
            topics.append(topic)
        
        # Fit vectorizer and transform
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            query_vector = self.vectorizer.transform([query])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, tfidf_matrix)[0]
            
            # Create results
            results = []
            for i, (topic, similarity) in enumerate(zip(topics, similarities)):
                if similarity >= min_score and topic in self.entries:
                    results.append((self.entries[topic], float(similarity)))
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        except Exception as e:
            LOGGER.error("TF-IDF search failed: %s", e)
            return self._search_keywords(query, top_k)
    
    def _search_keywords(
        self,
        query: str,
        top_k: int
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """Fallback keyword-based search."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_entries = []
        for entry in self.entries.values():
            # Simple keyword matching score
            entry_text = f"{entry.topic} {' '.join(entry.keywords)} {entry.content}".lower()
            entry_words = set(entry_text.split())
            
            # Calculate overlap
            overlap = len(query_words & entry_words)
            total_words = len(query_words)
            
            if total_words > 0:
                score = overlap / total_words
                scored_entries.append((entry, score))
        
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        return scored_entries[:top_k]
    
    def get_entry(self, topic: str) -> Optional[KnowledgeEntry]:
        """Get entry by topic."""
        return self.entries.get(topic)
    
    def get_all_entries(self) -> List[KnowledgeEntry]:
        """Get all entries."""
        return list(self.entries.values())
    
    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()
        self.embeddings.clear()


__all__ = ["VectorKnowledgeBase"]










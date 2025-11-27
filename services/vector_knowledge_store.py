"""
Production Vector Knowledge Store
High-performance vector database for semantic search of tuning knowledge.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

LOGGER = logging.getLogger(__name__)

# Try to import Chroma (preferred)
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chromadb = None
    Settings = None

# Try to import sentence transformers (for embeddings)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

# Fallback: simple TF-IDF based search
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None
    cosine_similarity = None
    np = None


class VectorKnowledgeStore:
    """
    Production-grade vector knowledge store for semantic search.
    
    Uses Chroma for vector storage with sentence transformers for embeddings.
    Falls back to TF-IDF if Chroma is not available.
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "tuning_knowledge",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize vector knowledge store.
        
        Args:
            persist_directory: Directory to persist Chroma database (None = in-memory)
            collection_name: Name of the Chroma collection
            embedding_model: Sentence transformer model name
        """
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.persist_directory = persist_directory or os.path.join(
            os.path.expanduser("~"), ".aituner", "vector_db"
        )
        
        # Initialize embedding model
        self.encoder = None
        self.use_chroma = False
        self.collection = None
        self.client = None
        
        # Fallback storage
        self.documents: List[str] = []
        self.metadata_list: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize the vector store with best available backend."""
        # Try Chroma first (best option)
        if CHROMA_AVAILABLE:
            try:
                # Create persist directory if needed
                os.makedirs(self.persist_directory, exist_ok=True)
                
                # Initialize Chroma client
                self.client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(anonymized_telemetry=False, allow_reset=True)
                )
                
                # Get or create collection
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Automotive tuning knowledge base"}
                )
                
                self.use_chroma = True
                LOGGER.info(f"Chroma vector store initialized at {self.persist_directory}")
                
                # Load existing count
                count = self.collection.count()
                if count > 0:
                    LOGGER.info(f"Loaded {count} existing knowledge entries")
                
            except Exception as e:
                LOGGER.warning(f"Failed to initialize Chroma: {e}, using fallback")
                self.use_chroma = False
        
        # Initialize embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(self.embedding_model_name)
                LOGGER.info(f"Sentence transformer model '{self.embedding_model_name}' loaded")
            except Exception as e:
                LOGGER.warning(f"Failed to load sentence transformer: {e}")
                self.encoder = None
        
        # Fallback to TF-IDF if needed
        if not self.use_chroma and SKLEARN_AVAILABLE:
            try:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                LOGGER.info("Using TF-IDF fallback for vector search")
            except Exception as e:
                LOGGER.warning(f"Failed to initialize TF-IDF: {e}")
    
    def add_knowledge(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Add knowledge to the vector store.
        
        Args:
            text: Knowledge text content
            metadata: Optional metadata (topic, category, etc.)
            doc_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Document ID
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        doc_id = doc_id or str(uuid.uuid4())
        metadata = metadata or {}
        
        # Ensure metadata has required fields
        if "text" not in metadata:
            metadata["text"] = text[:200]  # Store preview
        
        if self.use_chroma and self.encoder:
            try:
                # Generate embedding
                embedding = self.encoder.encode(text).tolist()
                
                # Add to Chroma
                self.collection.add(
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
                
                LOGGER.debug(f"Added knowledge to Chroma: {metadata.get('topic', 'Unknown')}")
                return doc_id
                
            except Exception as e:
                LOGGER.error(f"Failed to add to Chroma: {e}")
                # Fall through to fallback
        
        # Fallback: in-memory storage
        self.documents.append(text)
        self.metadata_list.append(metadata)
        
        if self.encoder:
            embedding = self.encoder.encode(text).tolist()
            self.embeddings.append(embedding)
        else:
            # Placeholder for TF-IDF (will be computed on search)
            self.embeddings.append([])
        
        LOGGER.debug(f"Added knowledge to fallback store: {metadata.get('topic', 'Unknown')}")
        return doc_id
    
    def add_knowledge_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        doc_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add multiple knowledge entries in batch (more efficient).
        
        Args:
            texts: List of knowledge text content
            metadata_list: Optional list of metadata dicts (one per text)
            doc_ids: Optional list of document IDs (auto-generated if not provided)
            
        Returns:
            List of document IDs
        """
        if not texts:
            return []
        
        if metadata_list is None:
            metadata_list = [{}] * len(texts)
        elif len(metadata_list) != len(texts):
            raise ValueError("metadata_list must have same length as texts")
        
        if doc_ids is None:
            doc_ids = [str(uuid.uuid4()) for _ in texts]
        elif len(doc_ids) != len(texts):
            raise ValueError("doc_ids must have same length as texts")
        
        # Validate all inputs
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} cannot be empty")
        
        # Batch process with Chroma
        if self.use_chroma and self.encoder:
            try:
                # Generate embeddings in batch (more efficient)
                embeddings = self.encoder.encode(texts).tolist()
                
                # Prepare metadata
                metadatas = []
                for i, metadata in enumerate(metadata_list):
                    meta = metadata.copy()
                    if "text" not in meta:
                        meta["text"] = texts[i][:200]  # Store preview
                    metadatas.append(meta)
                
                # Add to Chroma in batch
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=doc_ids
                )
                
                LOGGER.info(f"Added {len(texts)} knowledge entries to Chroma in batch")
                return doc_ids
                
            except Exception as e:
                LOGGER.error(f"Failed to add batch to Chroma: {e}")
                # Fall through to fallback
        
        # Fallback: add individually
        for i, text in enumerate(texts):
            self.add_knowledge(
                text=text,
                metadata=metadata_list[i],
                doc_id=doc_ids[i]
            )
        
        LOGGER.info(f"Added {len(texts)} knowledge entries to fallback store")
        return doc_ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        min_similarity: float = 0.3,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar knowledge.
        
        Args:
            query: Search query
            n_results: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)
            filter_metadata: Optional metadata filters
            
        Returns:
            List of results with text, metadata, and similarity score
        """
        if not query or not query.strip():
            return []
        
        if self.use_chroma and self.encoder:
            try:
                # Generate query embedding
                query_embedding = self.encoder.encode(query).tolist()
                
                # Build where clause for filtering
                where = None
                if filter_metadata:
                    where = filter_metadata
                
                # Search Chroma
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where
                )
                
                # Format results
                formatted_results = []
                if results['ids'] and len(results['ids'][0]) > 0:
                    for i, doc_id in enumerate(results['ids'][0]):
                        # Chroma returns distances (lower is better), convert to similarity
                        # Chroma uses cosine distance which ranges from 0-2
                        # Convert to similarity: similarity = 1 - (distance / 2)
                        distance = results['distances'][0][i] if results['distances'] else 0.0
                        # Handle both normalized [0,1] and cosine [0,2] distances
                        if distance > 1.0:
                            # Cosine distance [0, 2] -> similarity [1, -1], normalize to [1, 0]
                            similarity = max(0.0, 1.0 - (distance / 2.0))
                        else:
                            # Normalized distance [0, 1] -> similarity [1, 0]
                            similarity = 1.0 - distance
                        
                        if similarity >= min_similarity:
                            formatted_results.append({
                                "id": doc_id,
                                "text": results['documents'][0][i],
                                "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                                "similarity": similarity
                            })
                
                return formatted_results
                
            except Exception as e:
                LOGGER.error(f"Chroma search failed: {e}, using fallback")
        
        # Fallback: in-memory search
        if not self.documents:
            return []
        
        if self.encoder:
            # Use sentence transformer embeddings
            query_embedding = self.encoder.encode(query).tolist()
            
            similarities = []
            for emb in self.embeddings:
                if emb:  # Only if embedding exists
                    similarity = self._cosine_similarity(query_embedding, emb)
                    similarities.append(similarity)
                else:
                    similarities.append(0.0)
        elif SKLEARN_AVAILABLE and self.tfidf_vectorizer:
            # Use TF-IDF
            if self.tfidf_matrix is None or len(self.documents) != (self.tfidf_matrix.shape[0] if self.tfidf_matrix is not None else 0):
                # Fit on all documents (first time or if documents changed)
                LOGGER.debug(f"Fitting TF-IDF vectorizer with {len(self.documents)} documents")
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents)
            
            query_vector = self.tfidf_vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0].tolist()
        else:
            # Last resort: simple keyword matching
            query_lower = query.lower()
            query_words = set(query_lower.split())
            similarities = []
            for doc in self.documents:
                doc_words = set(doc.lower().split())
                overlap = len(query_words.intersection(doc_words))
                similarity = overlap / max(len(query_words), 1)
                similarities.append(similarity)
        
        # Get top results
        results_with_scores = list(zip(self.documents, self.metadata_list, similarities))
        results_with_scores.sort(key=lambda x: x[2], reverse=True)
        
        formatted_results = []
        for text, metadata, similarity in results_with_scores[:n_results]:
            if similarity >= min_similarity:
                formatted_results.append({
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "metadata": metadata,
                    "similarity": float(similarity)
                })
        
        return formatted_results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def count(self) -> int:
        """Get total number of documents in store."""
        if self.use_chroma and self.collection:
            return self.collection.count()
        return len(self.documents)
    
    def clear(self):
        """Clear all knowledge from store."""
        if self.use_chroma and self.collection:
            try:
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Automotive tuning knowledge base"}
                )
            except Exception as e:
                LOGGER.error(f"Failed to clear Chroma collection: {e}")
        
        self.documents.clear()
        self.metadata_list.clear()
        self.embeddings.clear()
        self.tfidf_matrix = None
        
        LOGGER.info("Vector knowledge store cleared")
    
    def delete(self, doc_id: str):
        """Delete a document by ID."""
        if self.use_chroma and self.collection:
            try:
                self.collection.delete(ids=[doc_id])
                return
            except Exception as e:
                LOGGER.error(f"Failed to delete from Chroma: {e}")
        
        # Fallback: find and remove
        # Note: This is inefficient, but fallback only
        LOGGER.warning("Delete not fully supported in fallback mode")



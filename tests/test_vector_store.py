"""
Unit tests for vector knowledge store.
"""

import pytest
from services.vector_knowledge_store import VectorKnowledgeStore


class TestVectorKnowledgeStore:
    """Test vector knowledge store functionality."""
    
    def test_add_knowledge(self):
        """Test adding knowledge."""
        store = VectorKnowledgeStore()
        doc_id = store.add_knowledge(
            text="Test knowledge entry",
            metadata={"topic": "Test", "source": "test"}
        )
        assert doc_id is not None
    
    def test_add_knowledge_batch(self):
        """Test batch adding knowledge."""
        store = VectorKnowledgeStore()
        texts = [
            "First knowledge entry",
            "Second knowledge entry",
            "Third knowledge entry"
        ]
        metadata_list = [
            {"topic": "Test1"},
            {"topic": "Test2"},
            {"topic": "Test3"}
        ]
        doc_ids = store.add_knowledge_batch(texts, metadata_list)
        assert len(doc_ids) == 3
        assert all(doc_id is not None for doc_id in doc_ids)
    
    def test_search(self):
        """Test searching knowledge."""
        store = VectorKnowledgeStore()
        store.add_knowledge(
            text="EFI tuning requires adjusting AFR and timing",
            metadata={"topic": "EFI Tuning"}
        )
        results = store.search("EFI tuning", n_results=5)
        assert len(results) > 0
    
    def test_count(self):
        """Test counting entries."""
        store = VectorKnowledgeStore()
        initial_count = store.count()
        store.add_knowledge("Test entry", {})
        assert store.count() == initial_count + 1
    
    def test_empty_text_raises_error(self):
        """Test that empty text raises error."""
        store = VectorKnowledgeStore()
        with pytest.raises(ValueError):
            store.add_knowledge("", {})


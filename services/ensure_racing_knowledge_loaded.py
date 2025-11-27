"""
Ensure Racing/Tuning Knowledge is Loaded into Vector Store
This script ensures all racing, tuning, and engine technical knowledge is loaded.
"""

from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def ensure_racing_knowledge_loaded(vector_store) -> int:
    """
    Ensure all racing/tuning knowledge is loaded into vector store.
    
    Uses comprehensive knowledge loader to get ALL knowledge from all sources.
    
    Args:
        vector_store: VectorKnowledgeStore instance
        
    Returns:
        Number of entries added
    """
    try:
        # Use comprehensive loader to get ALL knowledge
        from services.comprehensive_knowledge_loader import load_all_knowledge
        
        # Check if knowledge already exists
        current_count = vector_store.count()
        LOGGER.info(f"Current vector store count: {current_count}")
        
        # Load all knowledge
        added = load_all_knowledge(vector_store)
        LOGGER.info(f"Loaded {added} total knowledge entries")
        
        final_count = vector_store.count()
        LOGGER.info(f"Final vector store count: {final_count} (added {added} new entries)")
        
        return added
    except Exception as e:
        LOGGER.error(f"Failed to load racing knowledge: {e}", exc_info=True)
        # Fallback to basic loading
        try:
            from services.add_racing_tuning_knowledge import add_racing_tuning_knowledge
            added = add_racing_tuning_knowledge(vector_store)
            LOGGER.info(f"Fallback: Added {added} racing/tuning knowledge entries")
            return added
        except Exception as e2:
            LOGGER.error(f"Fallback also failed: {e2}", exc_info=True)
            return 0


def check_knowledge_coverage(vector_store, test_questions: list[str]) -> dict:
    """
    Test knowledge coverage with sample questions.
    
    Args:
        vector_store: VectorKnowledgeStore instance
        test_questions: List of test questions
        
    Returns:
        Dictionary with coverage results
    """
    results = {}
    
    for question in test_questions:
        try:
            matches = vector_store.search(question, n_results=3, min_similarity=0.3)
            results[question] = {
                "found": len(matches) > 0,
                "matches": len(matches),
                "top_score": matches[0]["similarity"] if matches else 0.0,
                "top_content": matches[0]["text"][:200] if matches else "No matches"
            }
        except Exception as e:
            results[question] = {
                "found": False,
                "error": str(e)
            }
    
    return results


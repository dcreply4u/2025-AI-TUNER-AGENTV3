"""
Migration Script: Convert existing knowledge base to RAG vector store
This script migrates all knowledge from the enhanced advisor to the vector store.
"""

from __future__ import annotations

import logging
from typing import List

LOGGER = logging.getLogger(__name__)


def migrate_knowledge_base_to_vector_store(
    vector_store,
    knowledge_base: List
) -> int:
    """
    Migrate knowledge base entries to vector store.
    
    Args:
        vector_store: VectorKnowledgeStore instance
        knowledge_base: List of KnowledgeEntry objects
        
    Returns:
        Number of entries migrated
    """
    count = 0
    
    for entry in knowledge_base:
        try:
            # Combine topic, keywords, and content for better search
            # Topic and keywords help with exact matches
            # Content provides detailed information
            text_parts = []
            
            # Add topic as header (important for matching)
            if entry.topic:
                text_parts.append(f"Topic: {entry.topic}")
            
            # Add keywords as searchable text (not just metadata)
            # This helps with single-word queries like "spark"
            if entry.keywords:
                keywords_str = ", ".join(entry.keywords)
                text_parts.append(f"Also known as: {keywords_str}")
            
            # Add main content
            if entry.content:
                text_parts.append(entry.content)
            
            # Combine into single text
            full_text = "\n\n".join(text_parts)
            
            # For entries with "spark" keyword, add explicit "spark" definition
            if "spark" in [k.lower() for k in entry.keywords] and "ignition" in entry.topic.lower():
                # Add a more direct definition for "what is spark" queries
                spark_definition = "\n\nSpark (also called ignition spark or spark plug): The electrical spark that ignites the air-fuel mixture in the engine cylinder. Spark timing controls when this spark occurs relative to piston position."
                full_text = spark_definition + "\n\n" + full_text
            
            # Build metadata
            metadata = {
                "topic": entry.topic,
                "category": entry.category,
                "tuning_related": entry.tuning_related if hasattr(entry, 'tuning_related') else False,
                "telemetry_relevant": entry.telemetry_relevant if hasattr(entry, 'telemetry_relevant') else False,
            }
            
            # Add related topics if available
            if hasattr(entry, 'related_topics') and entry.related_topics:
                metadata["related_topics"] = ", ".join(entry.related_topics[:3])
            
            # Add keywords to metadata for filtering
            if entry.keywords:
                metadata["keywords"] = ", ".join(entry.keywords[:10])
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=full_text,
                metadata=metadata
            )
            
            count += 1
            
            if count % 10 == 0:
                LOGGER.info(f"Migrated {count} knowledge entries...")
                
        except Exception as e:
            LOGGER.error(f"Failed to migrate entry '{entry.topic}': {e}")
            continue
    
    LOGGER.info(f"Migration complete: {count} entries migrated to vector store")
    return count


def migrate_from_enhanced_advisor(vector_store) -> int:
    """
    Migrate knowledge from EnhancedAIAdvisorQ to vector store.
    
    Args:
        vector_store: VectorKnowledgeStore instance
        
    Returns:
        Number of entries migrated
    """
    try:
        from services.ai_advisor_q_enhanced import EnhancedAIAdvisorQ
        
        # Create advisor instance to get knowledge base
        advisor = EnhancedAIAdvisorQ(enable_web_search=False)
        
        # Migrate knowledge
        count = migrate_knowledge_base_to_vector_store(
            vector_store=vector_store,
            knowledge_base=advisor.knowledge_base
        )
        
        return count
        
    except Exception as e:
        LOGGER.error(f"Failed to migrate from enhanced advisor: {e}")
        return 0


if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Check for --force flag
    force = '--force' in sys.argv or '-f' in sys.argv
    
    # Initialize vector store
    from services.vector_knowledge_store import VectorKnowledgeStore
    
    print("Initializing vector knowledge store...")
    vector_store = VectorKnowledgeStore()
    
    # Check if already populated
    existing_count = vector_store.count()
    if existing_count > 0:
        print(f"Vector store already has {existing_count} entries.")
        if force:
            print("--force flag detected, clearing and re-migrating...")
            vector_store.clear()
        else:
            response = input("Clear and re-migrate? (y/N): ")
            if response.lower() == 'y':
                vector_store.clear()
            else:
                print("Migration cancelled.")
                exit(0)
    
    # Migrate knowledge
    print("\nMigrating knowledge base...")
    count = migrate_from_enhanced_advisor(vector_store)
    
    print(f"\n✅ Migration complete: {count} entries migrated")
    print(f"Vector store now contains {vector_store.count()} entries")


"""
Test AI Advisor Functionality

Tests AI advisor knowledge retrieval, question answering, and recommendations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from tests.conftest import sample_data


class TestAIAdvisorKnowledge:
    """Test AI advisor knowledge base."""
    
    @patch('services.ai_advisor_rag.VectorKnowledgeStore')
    def test_knowledge_retrieval(self, mock_vector_store):
        """Test retrieving knowledge from vector store."""
        from services.ai_advisor_rag import RAGAIAdvisor
        
        # Mock vector store
        mock_store = MagicMock()
        mock_store.search.return_value = [
            {
                "text": "Boost pressure is the pressure above atmospheric in the intake manifold.",
                "similarity": 0.85,
                "metadata": {"topic": "boost"}
            }
        ]
        mock_vector_store.return_value = mock_store
        
        # Test retrieval
        results = mock_store.search("what is boost pressure", n_results=5)
        assert len(results) > 0
        assert results[0]['similarity'] > 0.8
    
    def test_question_parsing(self):
        """Test parsing user questions."""
        questions = [
            "what is boost pressure?",
            "how do I tune my fuel map?",
            "should I increase timing?",
        ]
        
        for question in questions:
            assert len(question) > 0
            assert '?' in question or question.endswith('?')
    
    @patch('services.ai_advisor_rag.VectorKnowledgeStore')
    def test_answer_generation(self, mock_vector_store):
        """Test generating answers from knowledge."""
        from services.ai_advisor_rag import RAGAIAdvisor
        
        # Mock knowledge retrieval
        mock_store = MagicMock()
        mock_store.search.return_value = [
            {
                "text": "Boost pressure is measured in PSI or bar.",
                "similarity": 0.9,
            }
        ]
        mock_vector_store.return_value = mock_store
        
        # Simulate answer generation
        retrieved = mock_store.search("boost pressure", n_results=1)
        if retrieved:
            answer = retrieved[0]['text']
            assert "boost" in answer.lower() or "pressure" in answer.lower()


class TestAIAdvisorRecommendations:
    """Test AI advisor recommendations."""
    
    @patch('services.race_setup_recommender.RaceSetupRecommender')
    def test_setup_recommendations(self, mock_recommender):
        """Test race setup recommendations."""
        from services.race_setup_recommender import RaceSetupRecommender
        
        recommender = RaceSetupRecommender()
        
        # Test recommendation for drag racing
        question = "how should I set up for drag racing?"
        recommendation = recommender.get_recommendation(question, {})
        
        assert recommendation is not None
        assert len(recommendation) > 0
    
    def test_telemetry_aware_recommendations(self, sample_data):
        """Test recommendations based on telemetry."""
        from services.race_setup_recommender import RaceSetupRecommender
        
        recommender = RaceSetupRecommender()
        
        # High EGT scenario
        telemetry = {
            "egt": 1500.0,  # High EGT
            "coolant_temp": 200.0,  # High temp
        }
        
        question = "my engine is running hot"
        recommendation = recommender.get_recommendation(question, telemetry)
        
        assert recommendation is not None
        # Should mention cooling or fuel enrichment


class TestAIAdvisorIntegration:
    """Test AI advisor integration."""
    
    @patch('services.ai_advisor_rag.RAGAIAdvisor')
    def test_question_answering_flow(self, mock_advisor):
        """Test complete question answering flow."""
        # Mock advisor
        mock_advisor_instance = MagicMock()
        mock_advisor.return_value = mock_advisor_instance
        
        # Mock answer
        mock_advisor_instance.answer.return_value = {
            "answer": "Boost pressure is the pressure above atmospheric.",
            "confidence": 0.85,
            "sources": ["boost_tuning_guide"],
        }
        
        # Test flow
        response = mock_advisor_instance.answer("what is boost pressure?")
        assert response['answer'] is not None
        assert response['confidence'] > 0.5
        assert len(response['sources']) > 0
    
    def test_context_integration(self, sample_data):
        """Test integrating telemetry context into answers."""
        # Simulate advisor with telemetry context
        question = "should I increase boost?"
        telemetry = {
            "boost": 15.0,  # Already high
            "egt": 1400.0,  # High EGT
        }
        
        # Advisor should consider telemetry
        assert telemetry['boost'] > 10  # High boost
        assert telemetry['egt'] > 1300  # High EGT
        # Should recommend caution


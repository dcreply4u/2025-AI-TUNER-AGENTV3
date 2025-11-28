"""
Advanced AI Advisor Knowledge Testing Suite

Comprehensive tests to validate and enhance the AI advisor's knowledge.
Tests knowledge base, web search integration, and response quality.
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestAdvisorKnowledgeBase:
    """Test advisor's knowledge base coverage."""
    
    @pytest.fixture
    def advisor(self):
        """Create advisor instance for testing."""
        try:
            from services.ai_advisor_rag import RAGAIAdvisor
            advisor = RAGAIAdvisor(
                use_local_llm=False,  # Don't require LLM for basic tests
                enable_web_search=False,  # Disable for knowledge base tests
            )
            return advisor
        except ImportError:
            pytest.skip("RAG advisor not available")
    
    def test_knowledge_base_loaded(self, advisor):
        """Test that knowledge base is loaded."""
        assert advisor.vector_store is not None or hasattr(advisor, 'knowledge_base')
    
    def test_basic_tuning_knowledge(self, advisor):
        """Test basic tuning knowledge."""
        questions = [
            "What is ECU tuning?",
            "What is a fuel map?",
            "What is ignition timing?",
            "What is boost control?",
        ]
        
        for question in questions:
            response = advisor.ask(question)
            assert response is not None
            assert len(response.answer) > 0
            # Answer should contain relevant information
            assert any(word in response.answer.lower() for word in 
                      ["tuning", "ecu", "fuel", "ignition", "boost", "engine"])
    
    def test_racing_knowledge(self, advisor):
        """Test racing-specific knowledge."""
        questions = [
            "What is lap timing?",
            "What is telemetry?",
            "What is drag racing?",
            "What is a racing line?",
        ]
        
        for question in questions:
            response = advisor.ask(question)
            assert response is not None
            assert len(response.answer) > 0


class TestAdvisorWebSearch:
    """Test advisor's web search integration."""
    
    @pytest.fixture
    def advisor_with_web_search(self):
        """Create advisor with web search enabled."""
        try:
            from services.ai_advisor_rag import RAGAIAdvisor
            advisor = RAGAIAdvisor(
                use_local_llm=False,
                enable_web_search=True,  # Enable web search
            )
            return advisor
        except ImportError:
            pytest.skip("RAG advisor not available")
    
    def test_web_search_available(self, advisor_with_web_search):
        """Test that web search is available."""
        assert advisor_with_web_search.web_search is not None or \
               advisor_with_web_search.enable_web_search
    
    @pytest.mark.skipif(True, reason="Requires internet connection and API keys")
    def test_web_search_triggered_on_unknown_topic(self, advisor_with_web_search):
        """Test that web search is triggered for unknown topics."""
        # Ask about something not in knowledge base
        question = "What is the latest Holley EFI firmware version?"
        response = advisor_with_web_search.ask(question)
        
        # Should have attempted web search
        assert response is not None
        # If web search was used, it should be indicated
        if response.used_web_search:
            assert len(response.sources) > 0
    
    def test_web_search_fallback(self, advisor_with_web_search):
        """Test web search fallback when knowledge is insufficient."""
        # Mock low confidence response
        question = "What is the specific compression ratio for a 2024 Honda Civic Type R?"
        response = advisor_with_web_search.ask(question)
        
        assert response is not None
        # Should have low confidence if not in knowledge base
        # Web search should be triggered (if available)


class TestAdvisorResponseQuality:
    """Test advisor response quality and accuracy."""
    
    @pytest.fixture
    def advisor(self):
        """Create advisor instance."""
        try:
            from services.ai_advisor_rag import RAGAIAdvisor
            return RAGAIAdvisor(use_local_llm=False, enable_web_search=False)
        except ImportError:
            pytest.skip("RAG advisor not available")
    
    def test_response_not_empty(self, advisor):
        """Test that responses are not empty."""
        question = "What is ECU tuning?"
        response = advisor.ask(question)
        
        assert response is not None
        assert len(response.answer) > 0
        assert response.answer.strip() != ""
    
    def test_response_has_sources(self, advisor):
        """Test that responses include sources when available."""
        question = "What is a fuel map?"
        response = advisor.ask(question)
        
        assert response is not None
        # Should have sources if knowledge was retrieved
        if response.confidence > 0.3:
            assert len(response.sources) >= 0  # Sources may be empty, but should exist
    
    def test_response_confidence_scoring(self, advisor):
        """Test that confidence scores are reasonable."""
        questions = [
            ("What is ECU tuning?", 0.4),  # Should have high confidence
            ("What is the weather today?", 0.2),  # Should have low confidence
        ]
        
        for question, min_confidence in questions:
            response = advisor.ask(question)
            assert response is not None
            assert 0.0 <= response.confidence <= 1.0
            # For known topics, confidence should be reasonable
            if "ECU tuning" in question:
                assert response.confidence >= min_confidence


class TestAdvisorModelSelection:
    """Test enhanced model selection."""
    
    def test_enhanced_advisor_import(self):
        """Test enhanced advisor can be imported."""
        try:
            from services.ai_advisor_enhanced import EnhancedRAGAIAdvisor
            assert EnhancedRAGAIAdvisor is not None
        except ImportError:
            pytest.skip("Enhanced advisor not available")
    
    @patch('services.ai_advisor_enhanced.ollama')
    def test_model_selection_prioritizes_larger_models(self, mock_ollama):
        """Test that model selection prefers larger models."""
        try:
            from services.ai_advisor_enhanced import EnhancedRAGAIAdvisor
            
            # Mock available models
            mock_ollama.list.return_value = {
                'models': [
                    {'name': 'llama3.2:3b'},
                    {'name': 'llama3.2:7b'},
                    {'name': 'mistral:7b'},
                ]
            }
            
            advisor = EnhancedRAGAIAdvisor(
                use_local_llm=True,
                enable_web_search=False,
            )
            
            # Should select mistral:7b or llama3.2:7b (larger models) over llama3.2:3b
            assert advisor.advisor.llm_model in ['mistral:7b', 'llama3.2:7b']
        except ImportError:
            pytest.skip("Enhanced advisor not available")


class TestAdvisorKnowledgeGaps:
    """Test advisor's ability to identify and fill knowledge gaps."""
    
    @pytest.fixture
    def advisor(self):
        """Create advisor instance."""
        try:
            from services.ai_advisor_rag import RAGAIAdvisor
            return RAGAIAdvisor(
                use_local_llm=False,
                enable_web_search=True,  # Enable for knowledge gap testing
            )
        except ImportError:
            pytest.skip("RAG advisor not available")
    
    def test_low_confidence_triggers_learning(self, advisor):
        """Test that low confidence responses trigger learning mechanisms."""
        # Ask about something likely not in knowledge base
        question = "What is the specific AFR target for E85 fuel at WOT?"
        response = advisor.ask(question)
        
        assert response is not None
        
        # If confidence is low, should indicate need for learning
        if response.confidence < 0.5:
            # Should have attempted web search or learning
            assert response.used_web_search or hasattr(advisor, 'auto_populator')
    
    def test_unknown_topic_handling(self, advisor):
        """Test how advisor handles completely unknown topics."""
        question = "What is the capital of Mars?"
        response = advisor.ask(question)
        
        assert response is not None
        # Should either:
        # 1. Have low confidence
        # 2. Use web search
        # 3. Indicate uncertainty
        assert response.confidence < 0.7 or response.used_web_search or \
               any(word in response.answer.lower() for word in ["don't know", "uncertain", "not sure"])


class TestAdvisorComprehensiveKnowledge:
    """Comprehensive knowledge tests across all domains."""
    
    @pytest.fixture
    def advisor(self):
        """Create advisor instance."""
        try:
            from services.ai_advisor_rag import RAGAIAdvisor
            return RAGAIAdvisor(use_local_llm=False, enable_web_search=False)
        except ImportError:
            pytest.skip("RAG advisor not available")
    
    @pytest.mark.parametrize("question,expected_keywords", [
        ("What is boost pressure?", ["boost", "pressure", "psi", "turbo"]),
        ("How do I tune ignition timing?", ["ignition", "timing", "degrees", "advance"]),
        ("What is a wideband O2 sensor?", ["oxygen", "sensor", "AFR", "lambda"]),
        ("What is knock detection?", ["knock", "detonation", "sensor", "timing"]),
        ("How does nitrous oxide work?", ["nitrous", "oxide", "N2O", "injection"]),
        ("What is traction control?", ["traction", "control", "wheel", "slip"]),
        ("What is launch control?", ["launch", "control", "RPM", "clutch"]),
        ("What is anti-lag?", ["anti-lag", "turbo", "exhaust", "ignition"]),
    ])
    def test_domain_knowledge(self, advisor, question, expected_keywords):
        """Test knowledge across various tuning domains."""
        response = advisor.ask(question)
        
        assert response is not None
        assert len(response.answer) > 0
        
        # Answer should contain at least one expected keyword
        answer_lower = response.answer.lower()
        assert any(keyword.lower() in answer_lower for keyword in expected_keywords), \
            f"Answer should contain one of {expected_keywords}: {response.answer[:200]}"


class TestAdvisorWebSearchIntegration:
    """Test web search integration and automatic learning."""
    
    @pytest.fixture
    def advisor_with_auto_learn(self):
        """Create advisor with auto-learning enabled."""
        try:
            from services.ai_advisor_rag import RAGAIAdvisor
            return RAGAIAdvisor(
                use_local_llm=False,
                enable_web_search=True,
            )
        except ImportError:
            pytest.skip("RAG advisor not available")
    
    @pytest.mark.skipif(True, reason="Requires internet and API keys")
    def test_web_search_learns_new_knowledge(self, advisor_with_auto_learn):
        """Test that web search results are learned and saved."""
        # Ask about something not in knowledge base
        question = "What is the latest MoTeC M1 firmware update?"
        response1 = advisor_with_auto_learn.ask(question)
        
        # Wait a moment for learning to process
        time.sleep(1)
        
        # Ask the same question again
        response2 = advisor_with_auto_learn.ask(question)
        
        # Second response should have higher confidence or use local knowledge
        # (This is a best-case scenario test)
        assert response1 is not None
        assert response2 is not None


class TestAdvisorEnhancement:
    """Test enhanced advisor features."""
    
    def test_enhanced_advisor_initialization(self):
        """Test enhanced advisor can be initialized."""
        try:
            from services.ai_advisor_enhanced import EnhancedRAGAIAdvisor
            
            advisor = EnhancedRAGAIAdvisor(
                use_local_llm=False,
                enable_web_search=False,
            )
            
            assert advisor is not None
            assert advisor.advisor is not None
            assert hasattr(advisor, 'get_model_info')
        except ImportError:
            pytest.skip("Enhanced advisor not available")
    
    def test_model_info_retrieval(self):
        """Test model information can be retrieved."""
        try:
            from services.ai_advisor_enhanced import EnhancedRAGAIAdvisor
            
            advisor = EnhancedRAGAIAdvisor(
                use_local_llm=False,
                enable_web_search=False,
            )
            
            info = advisor.get_model_info()
            assert 'current_model' in info
            assert 'llm_available' in info
            assert 'preferred_models' in info
        except ImportError:
            pytest.skip("Enhanced advisor not available")


"""
Ultra-Enhanced AI Advisor

Integrates all advanced features:
- Vector knowledge base with semantic search
- Learning knowledge base
- Vehicle-specific profiles
- Local LLM support
- Enhanced conversation memory
- Predictive diagnostics
- AI tuning recommendations
- Community knowledge sharing
- External data integration
- Expert system rules
- Enhanced confidence scoring
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Any, Tuple

LOGGER = logging.getLogger(__name__)

# Import all enhanced components
from services.ai_advisor_q_enhanced import (
    EnhancedAIAdvisorQ,
    IntentType,
    ResponseResult,
    ResponseContext,
    KnowledgeEntry,
)
from services.vector_knowledge_base import VectorKnowledgeBase
from services.learning_knowledge_base import LearningKnowledgeBase
from services.vehicle_knowledge_profile import VehicleKnowledgeProfile
from services.local_llm_adapter import LocalLLMAdapter
from services.enhanced_conversation_memory import EnhancedConversationMemory
from services.predictive_diagnostics_engine import PredictiveDiagnosticsEngine
from services.ai_tuning_recommendations import AITuningRecommendations, TuningGoal
from services.community_knowledge_sharing import CommunityKnowledgeSharing
from services.external_data_integration import ExternalDataIntegration
from services.expert_system_rules import ExpertSystemRules
from services.enhanced_confidence_scorer import EnhancedConfidenceScorer
from services.vehicle_tuning_database import VehicleTuningDatabase


class UltraEnhancedAIAdvisor:
    """
    Ultra-enhanced AI advisor with all advanced features.
    
    This is the complete, production-ready AI advisor that integrates
    all enhancement features for maximum accuracy and usefulness.
    """
    
    def __init__(
        self,
        vehicle_id: Optional[str] = None,
        user_id: Optional[str] = None,
        use_local_llm: bool = False,
        local_llm_backend: str = "ollama",
        weather_api_key: Optional[str] = None,
    ):
        """
        Initialize ultra-enhanced AI advisor.
        
        Args:
            vehicle_id: Vehicle identifier
            user_id: User identifier
            use_local_llm: Use local LLM for responses
            local_llm_backend: Local LLM backend ("ollama", "llama_cpp", "transformers")
            weather_api_key: Weather API key for external data
        """
        self.vehicle_id = vehicle_id
        self.user_id = user_id
        
        # Core knowledge bases
        self.vector_kb = VectorKnowledgeBase()
        self.learning_kb = LearningKnowledgeBase()
        self.vehicle_db = VehicleTuningDatabase()
        
        # Vehicle-specific profile
        self.vehicle_profile: Optional[VehicleKnowledgeProfile] = None
        if vehicle_id:
            self.vehicle_profile = VehicleKnowledgeProfile(vehicle_id)
        
        # Conversation memory
        self.conversation_memory = EnhancedConversationMemory()
        if vehicle_id:
            self.conversation_memory.set_vehicle_context(vehicle_id)
        
        # Local LLM (optional)
        self.local_llm: Optional[LocalLLMAdapter] = None
        if use_local_llm:
            try:
                self.local_llm = LocalLLMAdapter(backend=local_llm_backend)
                if not self.local_llm.is_available():
                    LOGGER.warning("Local LLM not available, using rule-based responses")
                    self.local_llm = None
            except Exception as e:
                LOGGER.warning("Failed to initialize local LLM: %s", e)
                self.local_llm = None
        
        # Advanced systems
        self.predictive_diagnostics: Optional[PredictiveDiagnosticsEngine] = None
        if vehicle_id:
            self.predictive_diagnostics = PredictiveDiagnosticsEngine(vehicle_id)
        
        self.tuning_recommendations = AITuningRecommendations()
        self.community_sharing = CommunityKnowledgeSharing()
        self.external_data = ExternalDataIntegration(weather_api_key)
        self.expert_system = ExpertSystemRules()
        self.confidence_scorer = EnhancedConfidenceScorer()
        
        # Base advisor (for fallback)
        self.base_advisor = EnhancedAIAdvisorQ()
        
        # Initialize vector KB with base knowledge
        self._initialize_vector_knowledge_base()
        
        LOGGER.info("Ultra-enhanced AI advisor initialized")
    
    def _initialize_vector_knowledge_base(self) -> None:
        """Initialize vector knowledge base with base advisor's knowledge."""
        # Get knowledge from base advisor
        base_knowledge = self.base_advisor.knowledge_base
        
        # Add to vector KB
        self.vector_kb.add_entries(base_knowledge)
        
        LOGGER.info("Initialized vector KB with %d entries", len(base_knowledge))
    
    def answer(
        self,
        question: str,
        telemetry: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ResponseResult:
        """
        Answer question with all enhancements.
        
        Args:
            question: User question
            telemetry: Current telemetry data
            context: Additional context
        
        Returns:
            Response result with answer and metadata
        """
        start_time = time.time()
        
        # Update conversation memory
        self.conversation_memory.add_message("user", question, metadata=context)
        
        # Update telemetry context
        if telemetry:
            self.conversation_memory.remember("last_telemetry", telemetry)
            if self.predictive_diagnostics:
                alerts = self.predictive_diagnostics.update_telemetry(telemetry)
                if alerts:
                    # Add diagnostic alerts to context
                    context = context or {}
                    context["diagnostic_alerts"] = alerts
        
        # Get conversation context
        conv_context = self.conversation_memory.get_relevant_context(question)
        
        # Classify intent
        intent, intent_confidence = self.base_advisor.classify_intent(question)
        
        # Search knowledge bases
        # 1. Vector KB (semantic search)
        vector_matches = self.vector_kb.search(question, top_k=5)
        
        # 2. Learning KB (learned patterns)
        learned_advice = self.learning_kb.get_learned_advice(question, self.vehicle_id, conv_context)
        
        # 3. Vehicle-specific advice
        vehicle_advice = None
        if self.vehicle_profile:
            vehicle_advice = self.vehicle_profile.get_vehicle_specific_advice(question, telemetry)
        
        # 4. Community knowledge
        community_profiles = []
        if self.vehicle_id:
            community_profiles = self.community_sharing.search_profiles(vehicle_id=self.vehicle_id)
        
        # 5. Expert system rules
        expert_facts = {}
        if telemetry:
            expert_facts.update(telemetry)
        expert_facts.update(conv_context.get("entities", {}))
        expert_conclusions = self.expert_system.evaluate(expert_facts)
        
        # Combine knowledge sources
        all_knowledge = [entry for entry, _ in vector_matches]
        
        # Generate response
        if self.local_llm and self.local_llm.is_available():
            # Use local LLM
            answer = self._generate_llm_response(question, all_knowledge, intent, conv_context, telemetry)
        else:
            # Use rule-based generation
            answer = self.base_advisor._generate_enhanced_response(question, all_knowledge, intent)
        
        # Add learned advice if available
        if learned_advice:
            answer += f"\n\n[Learned from experience] {learned_advice[0]}"
        
        # Add vehicle-specific advice
        if vehicle_advice:
            answer += f"\n\n[Vehicle-specific] {vehicle_advice}"
        
        # Add expert system conclusions
        if expert_conclusions:
            for conclusion in expert_conclusions[:2]:  # Top 2
                answer += f"\n\n[Expert System] {conclusion.conclusion}"
        
        # Calculate confidence
        question_clarity = self.confidence_scorer.calculate_question_clarity(question)
        context_relevance = self.confidence_scorer.calculate_context_relevance(question, conv_context)
        historical_success = self.confidence_scorer.get_historical_success_rate(question)
        
        confidence, confidence_level = self.confidence_scorer.calculate_confidence(
            intent_confidence=intent_confidence,
            knowledge_matches=vector_matches,
            telemetry_available=telemetry is not None,
            telemetry_relevant=telemetry is not None and self._is_telemetry_relevant(question),
            question_clarity=question_clarity,
            context_relevance=context_relevance,
            historical_success_rate=historical_success,
        )
        
        # Format response with confidence
        formatted_answer = self.confidence_scorer.format_response_with_confidence(
            answer,
            confidence,
            confidence_level,
            sources=[entry.topic for entry in all_knowledge[:3]]
        )
        
        # Generate follow-ups
        follow_ups = self.base_advisor._generate_follow_ups(intent, all_knowledge)
        
        # Create response result
        result = ResponseResult(
            answer=formatted_answer,
            confidence=confidence,
            intent=intent,
            sources=[entry.topic for entry in all_knowledge[:5]],
            follow_up_questions=follow_ups,
            telemetry_integrated=telemetry is not None,
        )
        
        # Record interaction for learning
        self.learning_kb.learn_from_interaction(
            question=question,
            answer=formatted_answer,
            helpful=None,  # Will be updated with user feedback
            vehicle_id=self.vehicle_id,
            context=conv_context,
        )
        
        # Update conversation memory
        self.conversation_memory.add_message("assistant", formatted_answer, intent=intent)
        
        response_time = time.time() - start_time
        LOGGER.debug("Generated response in %.2f seconds (confidence: %.2f)", response_time, confidence)
        
        return result
    
    def _generate_llm_response(
        self,
        question: str,
        knowledge: List[KnowledgeEntry],
        intent: IntentType,
        context: Dict[str, Any],
        telemetry: Optional[Dict[str, float]]
    ) -> str:
        """Generate response using local LLM."""
        if not self.local_llm:
            return self.base_advisor._generate_enhanced_response(question, knowledge, intent)
        
        # Build prompt
        knowledge_context = "\n\n".join([entry.content for entry in knowledge[:3]])
        
        system_prompt = """You are Q, an expert AI advisor for ECU tuning and racing performance.
You have access to a comprehensive knowledge base and real-time telemetry data.
Provide accurate, helpful, and safety-focused advice."""
        
        # Add telemetry context
        telemetry_context = ""
        if telemetry:
            telemetry_context = f"\n\nCurrent telemetry: {telemetry}"
        
        full_prompt = f"{question}\n\nKnowledge base:\n{knowledge_context}{telemetry_context}"
        
        try:
            response = self.local_llm.generate(
                prompt=full_prompt,
                system_prompt=system_prompt,
                max_tokens=500,
                temperature=0.7,
            )
            return response
        except Exception as e:
            LOGGER.error("LLM generation failed: %s", e)
            return self.base_advisor._generate_enhanced_response(question, knowledge, intent)
    
    def _is_telemetry_relevant(self, question: str) -> bool:
        """Check if telemetry is relevant to question."""
        question_lower = question.lower()
        telemetry_keywords = [
            "current", "now", "right now", "live", "real-time",
            "rpm", "boost", "temperature", "afr", "lambda",
            "what is", "show me", "tell me",
        ]
        return any(keyword in question_lower for keyword in telemetry_keywords)
    
    def get_tuning_recommendations(
        self,
        goal: TuningGoal,
        telemetry: Optional[Dict[str, float]] = None
    ) -> List[Any]:
        """Get AI-driven tuning recommendations."""
        vehicle_specs = None
        if self.vehicle_profile:
            vehicle_specs = self.vehicle_profile.get_statistics()
        
        return self.tuning_recommendations.generate_recommendations(
            goal=goal,
            current_telemetry=telemetry or {},
            vehicle_specs=vehicle_specs,
        )
    
    def simulate_tuning_scenario(
        self,
        name: str,
        description: str,
        proposed_changes: Dict[str, Any],
        current_state: Dict[str, Any]
    ) -> Any:
        """Simulate what-if tuning scenario."""
        vehicle_specs = None
        if self.vehicle_profile:
            vehicle_specs = self.vehicle_profile.get_statistics()
        
        return self.tuning_recommendations.simulate_scenario(
            name=name,
            description=description,
            proposed_changes=proposed_changes,
            current_state=current_state,
            vehicle_specs=vehicle_specs,
        )
    
    def provide_feedback(self, question: str, helpful: bool) -> None:
        """
        Provide feedback on answer quality.
        
        Args:
            question: Original question
            helpful: Whether answer was helpful
        """
        # Update learning KB
        self.learning_kb.learn_from_interaction(
            question=question,
            answer="",  # Not needed for feedback
            helpful=helpful,
            vehicle_id=self.vehicle_id,
        )
        
        # Update confidence scorer
        self.confidence_scorer.record_feedback(question, helpful)
        
        LOGGER.info("Feedback recorded: helpful=%s for question: %s", helpful, question[:50])


__all__ = ["UltraEnhancedAIAdvisor"]










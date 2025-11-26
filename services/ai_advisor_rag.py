"""
Production RAG-Based AI Advisor
Modern, production-ready AI advisor using Retrieval Augmented Generation (RAG).
This is the heart of the application - built for accuracy, reliability, and performance.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple

LOGGER = logging.getLogger(__name__)

# Import vector store
try:
    from services.vector_knowledge_store import VectorKnowledgeStore
    VECTOR_STORE_AVAILABLE = True
except ImportError as e:
    LOGGER.warning(f"Vector store not available: {e}")
    VECTOR_STORE_AVAILABLE = False
    VectorKnowledgeStore = None

# Try Ollama for local LLM
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

# Try OpenAI as fallback
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Import existing services
try:
    from services.web_search_service import WebSearchService
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    WebSearchService = None

try:
    from services.conversational_responses import get_conversation_manager
    CONVERSATIONAL_RESPONSES_AVAILABLE = True
except ImportError:
    CONVERSATIONAL_RESPONSES_AVAILABLE = False
    get_conversation_manager = None

# Import learning system
try:
    from services.ai_advisor_learning_system import AILearningSystem
    LEARNING_SYSTEM_AVAILABLE = True
except ImportError:
    LEARNING_SYSTEM_AVAILABLE = False
    AILearningSystem = None

# Import knowledge base manager
try:
    from services.knowledge_base_manager import KnowledgeBaseManager
    KNOWLEDGE_BASE_MANAGER_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_MANAGER_AVAILABLE = False
    KnowledgeBaseManager = None

# Import website list manager
try:
    from services.website_list_manager import WebsiteListManager
    from services.website_ingestion_service import WebsiteIngestionService
    WEBSITE_LIST_AVAILABLE = True
except ImportError:
    WEBSITE_LIST_AVAILABLE = False
    WebsiteListManager = None
    WebsiteIngestionService = None

# Import auto knowledge populator
try:
    from services.auto_knowledge_populator import AutoKnowledgePopulator
    AUTO_POPULATOR_AVAILABLE = True
except ImportError:
    AUTO_POPULATOR_AVAILABLE = False
    AutoKnowledgePopulator = None


@dataclass
class ChatMessage:
    """Chat message with metadata."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    sources: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class RAGResponse:
    """Structured RAG response."""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    used_web_search: bool = False
    used_telemetry: bool = False
    follow_up_questions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RAGAIAdvisor:
    """
    Production RAG-based AI Advisor.
    
    Uses vector search for semantic knowledge retrieval and LLM for natural response generation.
    Integrates telemetry, web search, and all existing features.
    """
    
    def __init__(
        self,
        use_local_llm: bool = True,
        llm_model: str = "llama3.2:3b",
        use_openai: bool = False,
        openai_api_key: Optional[str] = None,
        enable_web_search: bool = True,
        telemetry_provider=None,
        vector_store: Optional[VectorKnowledgeStore] = None,
        max_history: int = 20
    ):
        """
        Initialize RAG-based AI advisor.
        
        Args:
            use_local_llm: Use local Ollama LLM (recommended for privacy/offline)
            llm_model: Ollama model name (e.g., "llama3.2:3b", "mistral:7b")
            use_openai: Use OpenAI API as fallback
            openai_api_key: OpenAI API key (if using OpenAI)
            enable_web_search: Enable web search for unknown questions
            telemetry_provider: Function to get current telemetry data
            vector_store: Optional pre-initialized vector store
            max_history: Maximum conversation history length
        """
        self.use_local_llm = use_local_llm and OLLAMA_AVAILABLE
        self.llm_model = llm_model
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.openai_api_key = openai_api_key
        self.enable_web_search = enable_web_search
        self.telemetry_provider = telemetry_provider
        self.max_history = max_history
        
        # Initialize vector store
        if vector_store:
            self.vector_store = vector_store
        elif VECTOR_STORE_AVAILABLE:
            self.vector_store = VectorKnowledgeStore()
            LOGGER.info("Vector knowledge store initialized")
        else:
            self.vector_store = None
            LOGGER.warning("Vector store not available - advisor will have limited functionality")
        
        # Initialize LLM
        self.llm_available = False
        if self.use_local_llm:
            self.llm_available = self._initialize_ollama()
        elif self.use_openai and openai_api_key:
            try:
                openai.api_key = openai_api_key
                self.llm_available = True
                LOGGER.info("OpenAI API initialized")
            except Exception as e:
                LOGGER.warning(f"Failed to initialize OpenAI: {e}")
        
        if not self.llm_available:
            LOGGER.warning("No LLM available - will use template-based responses")
        
        # Initialize web search
        self.web_search = None
        if enable_web_search and WEB_SEARCH_AVAILABLE:
            try:
                self.web_search = WebSearchService(enable_search=True)
                if self.web_search.is_available():
                    LOGGER.info("Web search enabled")
            except Exception as e:
                LOGGER.warning(f"Web search not available: {e}")
        
        # Initialize conversational manager
        self.conversation_manager = None
        if CONVERSATIONAL_RESPONSES_AVAILABLE:
            try:
                self.conversation_manager = get_conversation_manager()
            except Exception as e:
                LOGGER.debug(f"Conversation manager not available: {e}")
        
        # Conversation history
        self.conversation_history: List[ChatMessage] = []
        
        # Initialize learning system
        self.learning_system = None
        if LEARNING_SYSTEM_AVAILABLE and self.vector_store:
            try:
                self.learning_system = AILearningSystem(
                    vector_store=self.vector_store,
                    enable_auto_learning=True
                )
                LOGGER.info("Learning system initialized")
            except Exception as e:
                LOGGER.warning(f"Learning system not available: {e}")
        
        # Initialize knowledge base manager
        self.knowledge_base_manager = None
        if KNOWLEDGE_BASE_MANAGER_AVAILABLE and self.vector_store:
            try:
                self.knowledge_base_manager = KnowledgeBaseManager(
                    vector_store=self.vector_store
                )
                LOGGER.info("Knowledge base manager initialized")
            except Exception as e:
                LOGGER.warning(f"Knowledge base manager not available: {e}")
        
        # Initialize website list manager
        self.website_list_manager = None
        self.website_ingestion_service = None
        if WEBSITE_LIST_AVAILABLE and self.knowledge_base_manager:
            try:
                self.website_list_manager = WebsiteListManager()
                self.website_ingestion_service = WebsiteIngestionService(
                    website_list_manager=self.website_list_manager,
                    knowledge_base_manager=self.knowledge_base_manager
                )
                LOGGER.info("Website list manager initialized")
            except Exception as e:
                LOGGER.warning(f"Website list manager not available: {e}")
        
        # Initialize auto knowledge populator
        self.auto_populator = None
        if AUTO_POPULATOR_AVAILABLE and self.learning_system and self.website_ingestion_service:
            try:
                web_search = None
                if self.web_search:
                    web_search = self.web_search
                
                # Initialize KB file manager for saving learned knowledge
                kb_file_manager = None
                try:
                    from services.knowledge_base_file_manager import KnowledgeBaseFileManager
                    kb_file_manager = KnowledgeBaseFileManager(auto_save=True)
                    LOGGER.info("KB file manager initialized for saving learned knowledge")
                except Exception as e:
                    LOGGER.warning(f"KB file manager not available: {e}")
                
                self.auto_populator = AutoKnowledgePopulator(
                    learning_system=self.learning_system,
                    website_ingestion_service=self.website_ingestion_service,
                    knowledge_base_manager=self.knowledge_base_manager,
                    web_search_service=web_search,
                    kb_file_manager=kb_file_manager,
                    auto_populate_enabled=True,
                    confidence_threshold=0.5,
                    min_gap_frequency=1  # Auto-populate immediately (user wants instant learning)
                )
                LOGGER.info("Auto knowledge populator initialized with KB file saving")
            except Exception as e:
                LOGGER.warning(f"Auto knowledge populator not available: {e}")
        
        # System prompt for LLM
        self.system_prompt = """You are Q, an expert automotive tuning advisor with deep knowledge of:
- ECU tuning (fuel maps, ignition timing, boost control)
- Engine diagnostics and troubleshooting
- Performance optimization
- Safety and protection systems
- Racing and motorsport applications

You provide accurate, technical, and helpful advice. When you don't know something, you say so clearly.
You use the provided context to answer questions accurately. Be concise but thorough."""

        LOGGER.info("RAG AI Advisor initialized (LLM: %s, Vector Store: %s, Web Search: %s)",
                   self.llm_available, self.vector_store is not None, self.web_search is not None)
    
    def _initialize_ollama(self) -> bool:
        """Initialize Ollama LLM."""
        if not OLLAMA_AVAILABLE:
            return False
        
        try:
            # Check if Ollama is running
            models = ollama.list()
            
            # Check if our model is available
            model_names = [m['name'] for m in models.get('models', [])]
            if self.llm_model not in model_names:
                LOGGER.warning(f"Model {self.llm_model} not found. Available: {model_names}")
                LOGGER.info(f"To install: ollama pull {self.llm_model}")
                # Try to use first available model
                if model_names:
                    self.llm_model = model_names[0]
                    LOGGER.info(f"Using available model: {self.llm_model}")
                else:
                    return False
            
            # Test generation
            test_response = ollama.generate(
                model=self.llm_model,
                prompt="test",
                options={"num_predict": 1}
            )
            
            LOGGER.info(f"Ollama LLM initialized with model: {self.llm_model}")
            return True
            
        except Exception as e:
            LOGGER.warning(f"Ollama not available: {e}")
            LOGGER.info("Install Ollama from https://ollama.ai and run: ollama pull llama3.2:3b")
            return False
    
    def answer(
        self,
        question: str,
        telemetry: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            telemetry: Optional current telemetry data
            context: Optional additional context
            
        Returns:
            RAGResponse with answer, sources, and metadata
        """
        if not question or not question.strip():
            return RAGResponse(
                answer="Please ask a question.",
                confidence=0.0,
                sources=[]
            )
        
        question = question.strip()
        start_time = time.time()
        
        # Get telemetry if provider available
        if not telemetry and self.telemetry_provider:
            try:
                telemetry = self.telemetry_provider()
            except Exception as e:
                LOGGER.debug(f"Failed to get telemetry: {e}")
        
        # Step 1: Retrieve relevant knowledge
        retrieved_knowledge = []
        if self.vector_store:
            try:
                # For "what is X" questions, be more precise with the query
                search_query = question
                if "what is" in question.lower() or "what's" in question.lower():
                    # Extract the main subject for better matching
                    import re
                    parts = re.split(r"what (is|are|is the|are the|'s)", question.lower(), 1)
                    if len(parts) > 1:
                        subject = parts[-1].strip()
                        # Remove common trailing words, but keep important terms
                        # Don't remove if subject is a single important word (like "telemetryiq")
                        if len(subject.split()) > 1:
                            subject = re.sub(r"\b(for|on|in|at|with|to|the)\b.*$", "", subject).strip()
                        if subject:
                            search_query = subject  # Search for just the subject
                            LOGGER.debug(f"Refined 'what is' query to: {subject}")
                
                search_results = self.vector_store.search(
                    query=search_query,
                    n_results=5,
                    min_similarity=0.3  # Lower threshold to catch more results
                )
                
                # Filter and prioritize results for "what is" questions
                if "what is" in question.lower() or "what's" in question.lower():
                    question_lower = question.lower()
                    # Extract key terms from question (keep all terms, not just > 3 chars)
                    key_terms = set(re.findall(r'\b\w+\b', question_lower))
                    # Remove common stop words but keep important terms
                    stop_words = {"what", "is", "are", "the", "a", "an", "for", "on", "in", "at", "with", "to"}
                    key_terms = {t for t in key_terms if t not in stop_words and len(t) > 2}
                    
                    # Score and sort results by relevance
                    scored_results = []
                    for result in search_results:
                        metadata = result.get("metadata", {})
                        topic = metadata.get("topic", "").lower()
                        text = result.get("text", "").lower()
                        similarity = result.get("similarity", 0)
                        
                        # Calculate relevance score
                        score = similarity
                        
                        # Boost for topic matches
                        topic_matches = sum(1 for term in key_terms if term in topic)
                        if topic_matches > 0:
                            score += 0.2 * topic_matches
                        
                        # Strong boost for "Overview" topics for "what is" questions
                        if "overview" in topic:
                            score += 0.5  # Strong boost for overview topics
                        
                        # Boost if topic contains the main subject
                        subject_lower = search_query.lower()
                        if subject_lower in topic or any(word in topic for word in subject_lower.split() if len(word) > 3):
                            score += 0.2
                        
                        # Boost for text matches
                        text_matches = sum(1 for term in key_terms if term in text[:300])
                        if text_matches > 0:
                            score += 0.1 * text_matches
                        
                        scored_results.append((score, result))
                    
                    # Sort by score (highest first) and take top results
                    scored_results.sort(key=lambda x: x[0], reverse=True)
                    retrieved_knowledge = [r[1] for r in scored_results[:3]]
                    LOGGER.debug(f"Filtered to {len(retrieved_knowledge)} relevant results for 'what is' question")
                else:
                    retrieved_knowledge = search_results
                
                LOGGER.debug(f"Retrieved {len(retrieved_knowledge)} knowledge entries")
            except Exception as e:
                LOGGER.error(f"Vector search failed: {e}")
        
        # Step 2: Determine if web search is needed
        use_web_search = False
        web_search_results = None
        
        # Use web search if:
        # - No good local knowledge (similarity < 0.5 for "what is" questions, < 0.4 for others)
        # - Question is about specific vehicle specs
        # - Question is about current/recent information
        if self.web_search and self.enable_web_search:
            is_what_is = "what is" in question.lower() or "what's" in question.lower()
            min_similarity_threshold = 0.5 if is_what_is else 0.4  # Lower thresholds to trigger web search more often
            
            needs_web_search = (
                not retrieved_knowledge or
                (retrieved_knowledge and retrieved_knowledge[0].get("similarity", 0) < min_similarity_threshold) or
                self._is_vehicle_specific_question(question) or
                self._is_current_information_question(question)
            )
            
            if needs_web_search:
                try:
                    web_search_results = self._perform_web_search(question)
                    if web_search_results:
                        use_web_search = True
                        # Add web results to knowledge for future use
                        if self.vector_store:
                            for result in web_search_results[:2]:  # Top 2 results
                                self.vector_store.add_knowledge(
                                    text=result.get("snippet", ""),
                                    metadata={
                                        "source": "web",
                                        "url": result.get("url", ""),
                                        "title": result.get("title", "")
                                    }
                                )
                except Exception as e:
                    LOGGER.warning(f"Web search failed: {e}")
        
        # Step 3: Build context
        context_text = self._build_context(
            question=question,
            retrieved_knowledge=retrieved_knowledge,
            web_search_results=web_search_results,
            telemetry=telemetry,
            conversation_history=self.conversation_history[-3:]  # Last 3 messages
        )
        
        # Step 4: Generate response
        if self.llm_available:
            answer = self._generate_llm_response(question, context_text)
        else:
            answer = self._generate_template_response(question, retrieved_knowledge, web_search_results)
        
        # Step 5: Post-process response
        answer = self._post_process_response(answer, question)
        
        # Step 6: Calculate confidence
        confidence = self._calculate_confidence(retrieved_knowledge, use_web_search, self.llm_available)
        
        # Step 7: Extract sources
        sources = []
        for item in retrieved_knowledge[:3]:
            sources.append({
                "text": item["text"][:200],
                "metadata": item["metadata"],
                "similarity": item["similarity"]
            })
        
        if web_search_results:
            for result in web_search_results[:2]:
                sources.append({
                    "text": result.get("snippet", "")[:200],
                    "url": result.get("url", ""),
                    "title": result.get("title", "")
                })
        
        # Step 8: Generate follow-up questions
        follow_ups = self._generate_follow_ups(question, retrieved_knowledge)
        
        # Step 9: Check for warnings
        warnings = self._check_warnings(question, telemetry)
        
        # Store in history
        self.conversation_history.append(ChatMessage(
            role="user",
            content=question,
            sources=[],
            confidence=1.0
        ))
        self.conversation_history.append(ChatMessage(
            role="assistant",
            content=answer,
            sources=[s.get("title", s.get("text", ""))[:50] for s in sources],
            confidence=confidence
        ))
        
        # Keep history manageable
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        elapsed = time.time() - start_time
        LOGGER.info(f"Generated response in {elapsed:.2f}s (confidence: {confidence:.2f})")
        
        # Auto-populate knowledge if confidence is low
        auto_populate_result = None
        # Auto-populate if confidence is low (system doesn't know the answer well)
        if self.auto_populator and confidence < 0.5:
            try:
                auto_populate_result = self.auto_populator.check_and_populate(
                    question=question,
                    confidence=confidence,
                    answer=answer
                )
                if auto_populate_result.get("success"):
                    chunks_added = auto_populate_result.get("chunks_added", 0)
                    LOGGER.info(f"Auto-populated {chunks_added} chunks and saved to KB file")
                    # Add note to answer that knowledge was learned
                    if chunks_added > 0:
                        answer += "\n\n💡 I've learned about this topic and saved it for future reference. You can review/edit it in the KB files."
            except Exception as e:
                LOGGER.debug(f"Auto-population check failed: {e}")
        
        # Record interaction for learning
        if self.learning_system:
            try:
                self.learning_system.record_interaction(
                    question=question,
                    answer=answer,
                    confidence=confidence,
                    sources=sources,
                    session_id=context.get("session_id") if context else None,
                    vehicle_id=context.get("vehicle_id") if context else None,
                    response_time=elapsed
                )
            except Exception as e:
                LOGGER.debug(f"Failed to record interaction: {e}")
        
        return RAGResponse(
            answer=answer,
            confidence=confidence,
            sources=sources,
            used_web_search=use_web_search,
            used_telemetry=telemetry is not None,
            follow_up_questions=follow_ups,
            warnings=warnings
        )
    
    def _build_context(
        self,
        question: str,
        retrieved_knowledge: List[Dict[str, Any]],
        web_search_results: Optional[List[Dict[str, Any]]],
        telemetry: Optional[Dict[str, float]],
        conversation_history: List[ChatMessage]
    ) -> str:
        """Build context string for LLM."""
        context_parts = []
        
        # Add retrieved knowledge
        if retrieved_knowledge:
            context_parts.append("Relevant Knowledge:")
            for i, item in enumerate(retrieved_knowledge[:3], 1):
                context_parts.append(f"{i}. {item['text'][:500]}")
                if item.get('metadata', {}).get('topic'):
                    context_parts.append(f"   (Topic: {item['metadata']['topic']})")
        
        # Add web search results
        if web_search_results:
            context_parts.append("\nWeb Research:")
            for i, result in enumerate(web_search_results[:2], 1):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                context_parts.append(f"{i}. {title}")
                context_parts.append(f"   {snippet[:300]}")
        
        # Add telemetry if relevant
        if telemetry and self._is_telemetry_relevant(question):
            context_parts.append("\nCurrent Vehicle Data:")
            telemetry_str = self._format_telemetry(telemetry)
            context_parts.append(telemetry_str)
        
        # Add recent conversation context
        if conversation_history:
            context_parts.append("\nRecent Conversation:")
            for msg in conversation_history[-2:]:  # Last 2 messages
                role = "User" if msg.role == "user" else "Assistant"
                context_parts.append(f"{role}: {msg.content[:200]}")
        
        return "\n".join(context_parts)
    
    def _generate_llm_response(self, question: str, context: str) -> str:
        """Generate response using LLM."""
        if self.use_local_llm and OLLAMA_AVAILABLE:
            return self._generate_ollama_response(question, context)
        elif self.use_openai and OPENAI_AVAILABLE:
            return self._generate_openai_response(question, context)
        else:
            return "I'm unable to generate a response. Please check LLM configuration."
    
    def _generate_ollama_response(self, question: str, context: str) -> str:
        """Generate response using Ollama."""
        try:
            # Build prompt
            prompt = f"""Context:
{context}

Question: {question}

Answer the question using the context provided. Be accurate, technical, and helpful."""

            # Generate response
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                system=self.system_prompt,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 500,  # Limit response length
                }
            )
            
            answer = response.get("response", "").strip()
            
            # Clean up response
            if answer.startswith("Answer:"):
                answer = answer[7:].strip()
            
            return answer
            
        except Exception as e:
            LOGGER.error(f"Ollama generation failed: {e}")
            return f"I encountered an error generating a response: {str(e)}"
    
    def _generate_openai_response(self, question: str, context: str) -> str:
        """Generate response using OpenAI."""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Fast and cheap
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            LOGGER.error(f"OpenAI generation failed: {e}")
            return f"I encountered an error generating a response: {str(e)}"
    
    def _generate_template_response(
        self,
        question: str,
        retrieved_knowledge: List[Dict[str, Any]],
        web_search_results: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Generate template-based response (fallback when no LLM)."""
        if retrieved_knowledge:
            # Use best matching knowledge
            best_match = retrieved_knowledge[0]
            answer = f"Based on the information I have:\n\n{best_match['text'][:500]}"
            
            if best_match.get('metadata', {}).get('topic'):
                answer += f"\n\n(Topic: {best_match['metadata']['topic']})"
            
            return answer
        
        if web_search_results:
            result = web_search_results[0]
            answer = f"I found this information:\n\n{result.get('title', '')}\n{result.get('snippet', '')[:400]}"
            return answer
        
        return "I don't have specific information about that. Could you rephrase your question or provide more context?"
    
    def _post_process_response(self, answer: str, question: str) -> str:
        """Post-process response for better formatting."""
        # Add conversational touch if manager available
        if self.conversation_manager:
            try:
                answer = self.conversation_manager.get_contextual_response(
                    question=question,
                    base_response=answer,
                    intent="general"
                )
            except Exception as e:
                LOGGER.debug(f"Conversation manager post-processing failed: {e}")
        
        # Clean up common LLM artifacts
        answer = answer.replace("Answer:", "").strip()
        answer = answer.replace("Based on the context,", "").strip()
        
        return answer
    
    def _calculate_confidence(
        self,
        retrieved_knowledge: List[Dict[str, Any]],
        used_web_search: bool,
        used_llm: bool
    ) -> float:
        """Calculate confidence score for response."""
        if not retrieved_knowledge and not used_web_search:
            return 0.3  # Low confidence - no sources
        
        confidence = 0.5  # Base confidence
        
        # Boost for good knowledge match
        if retrieved_knowledge:
            best_similarity = retrieved_knowledge[0].get("similarity", 0.0)
            confidence += best_similarity * 0.3  # Up to +0.3
        
        # Boost for LLM generation
        if used_llm:
            confidence += 0.1
        
        # Slight boost for web search
        if used_web_search:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _generate_follow_ups(
        self,
        question: str,
        retrieved_knowledge: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate follow-up questions."""
        follow_ups = []
        
        # Suggest related topics
        if retrieved_knowledge:
            topics = set()
            for item in retrieved_knowledge[:3]:
                topic = item.get('metadata', {}).get('topic')
                if topic:
                    topics.add(topic)
            
            for topic in list(topics)[:2]:
                follow_ups.append(f"Tell me more about {topic}")
        
        # Generic follow-ups
        if "what is" in question.lower():
            follow_ups.append("How do I use this in tuning?")
        elif "how" in question.lower():
            follow_ups.append("What are the safety considerations?")
        
        return follow_ups[:3]  # Limit to 3
    
    def _check_warnings(self, question: str, telemetry: Optional[Dict[str, float]]) -> List[str]:
        """Check for safety warnings."""
        warnings = []
        
        question_lower = question.lower()
        
        # Safety-related questions
        if any(word in question_lower for word in ["dangerous", "safe", "risk", "damage"]):
            warnings.append("Always follow safety protocols when tuning. Start conservative and test thoroughly.")
        
        # Telemetry warnings
        if telemetry:
            if telemetry.get("Knock_Count", 0) > 0:
                warnings.append("⚠️ Knock detected - reduce timing or check AFR")
            if telemetry.get("EGT", 0) > 900:
                warnings.append("⚠️ High EGT - reduce boost or timing")
            if telemetry.get("AFR", 14.7) < 12.0:
                warnings.append("⚠️ Very rich AFR - may cause fouling")
            if telemetry.get("AFR", 14.7) > 15.0:
                warnings.append("⚠️ Very lean AFR - risk of knock")
        
        return warnings
    
    def _perform_web_search(self, question: str) -> Optional[List[Dict[str, Any]]]:
        """Perform web search."""
        if not self.web_search:
            return None
        
        try:
            results = self.web_search.search(question, max_results=3)
            if results and results.results:
                return [
                    {
                        "title": r.title,
                        "snippet": r.snippet,
                        "url": r.url
                    }
                    for r in results.results
                ]
        except Exception as e:
            LOGGER.warning(f"Web search error: {e}")
        
        return None
    
    def _is_vehicle_specific_question(self, question: str) -> bool:
        """Check if question is about specific vehicle."""
        vehicle_keywords = [
            "dodge", "ford", "chevrolet", "chevy", "honda", "toyota", "nissan",
            "hellcat", "demon", "corvette", "camaro", "mustang", "charger", "challenger",
            "supra", "gtr", "m3", "m4", "911", "gt3", "sti", "type r"
        ]
        question_lower = question.lower()
        return any(vk in question_lower for vk in vehicle_keywords)
    
    def _is_current_information_question(self, question: str) -> bool:
        """Check if question needs current information."""
        current_keywords = ["current", "now", "today", "latest", "recent", "2024", "2025"]
        question_lower = question.lower()
        return any(ck in question_lower for ck in current_keywords)
    
    def _is_telemetry_relevant(self, question: str) -> bool:
        """Check if question is about current telemetry."""
        telemetry_keywords = [
            "current", "now", "live", "real-time", "rpm", "boost", "afr", "lambda",
            "temperature", "egt", "knock", "pressure", "fuel pressure", "oil pressure"
        ]
        question_lower = question.lower()
        return any(tk in question_lower for tk in telemetry_keywords)
    
    def _format_telemetry(self, telemetry: Dict[str, float]) -> str:
        """Format telemetry data for context."""
        parts = []
        for key, value in telemetry.items():
            if isinstance(value, (int, float)):
                if "temp" in key.lower() or "egt" in key.lower():
                    parts.append(f"  {key}: {value:.1f}°C")
                elif "pressure" in key.lower() or "boost" in key.lower():
                    parts.append(f"  {key}: {value:.1f} PSI")
                elif "rpm" in key.lower():
                    parts.append(f"  {key}: {value:.0f}")
                else:
                    parts.append(f"  {key}: {value:.2f}")
        return "\n".join(parts) if parts else "  No telemetry data available"
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        LOGGER.info("Conversation history cleared")
    
    def record_feedback(
        self,
        question: str,
        answer: str,
        helpful: bool,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        session_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        confidence: Optional[float] = None,
        sources: Optional[List[str]] = None
    ) -> None:
        """
        Record user feedback for learning.
        
        Args:
            question: Original question
            answer: Given answer
            helpful: Whether answer was helpful
            rating: Optional rating (1-5)
            comment: Optional comment
            session_id: Session identifier
            vehicle_id: Vehicle identifier
            confidence: Answer confidence
            sources: Sources used
        """
        if self.learning_system:
            try:
                self.learning_system.record_feedback(
                    question=question,
                    answer=answer,
                    helpful=helpful,
                    rating=rating,
                    comment=comment,
                    session_id=session_id,
                    vehicle_id=vehicle_id,
                    confidence=confidence,
                    sources=sources
                )
                LOGGER.info(f"Feedback recorded: helpful={helpful}, rating={rating}")
            except Exception as e:
                LOGGER.error(f"Failed to record feedback: {e}")
    
    def get_performance_report(self) -> Optional[Dict[str, Any]]:
        """
        Get performance report from learning system.
        
        Returns:
            Performance report dictionary or None
        """
        if self.learning_system:
            try:
                return self.learning_system.get_performance_report()
            except Exception as e:
                LOGGER.error(f"Failed to get performance report: {e}")
        return None
    
    def get_knowledge_gaps(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get identified knowledge gaps.
        
        Args:
            priority: Filter by priority (low, medium, high, critical)
            
        Returns:
            List of knowledge gaps
        """
        if self.learning_system:
            try:
                gaps = self.learning_system.get_knowledge_gaps(priority=priority)
                return [asdict(g) for g in gaps]
            except Exception as e:
                LOGGER.error(f"Failed to get knowledge gaps: {e}")
        return []
    
    def add_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add a document to the knowledge base.
        
        Args:
            file_path: Path to document (PDF, TXT, DOCX, etc.)
            metadata: Optional metadata
            
        Returns:
            Result dictionary with success status and chunks added
        """
        if not self.knowledge_base_manager:
            return {
                "success": False,
                "error": "Knowledge base manager not available"
            }
        
        try:
            result = self.knowledge_base_manager.add_document(file_path, metadata)
            LOGGER.info(f"Added document: {file_path}, chunks: {result.get('chunks_added', 0)}")
            return result
        except Exception as e:
            LOGGER.error(f"Failed to add document: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_website(self, url: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scrape and add a website to the knowledge base.
        
        Args:
            url: URL to scrape
            metadata: Optional metadata
            
        Returns:
            Result dictionary with success status and chunks added
        """
        if not self.knowledge_base_manager:
            return {
                "success": False,
                "error": "Knowledge base manager not available"
            }
        
        try:
            result = self.knowledge_base_manager.add_website(url, metadata)
            LOGGER.info(f"Added website: {url}, chunks: {result.get('chunks_added', 0)}")
            return result
        except Exception as e:
            LOGGER.error(f"Failed to add website: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_forum(self, forum_url: str, search_query: str, max_posts: int = 10) -> Dict[str, Any]:
        """
        Search a forum and add results to knowledge base.
        
        Args:
            forum_url: Base URL of forum
            search_query: Search query
            max_posts: Maximum posts to retrieve
            
        Returns:
            Result dictionary with success status and posts added
        """
        if not self.knowledge_base_manager:
            return {
                "success": False,
                "error": "Knowledge base manager not available"
            }
        
        try:
            result = self.knowledge_base_manager.search_forum(forum_url, search_query, max_posts)
            LOGGER.info(f"Forum search: {search_query}, posts: {result.get('posts_added', 0)}")
            return result
        except Exception as e:
            LOGGER.error(f"Forum search failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self.knowledge_base_manager:
            return {"error": "Knowledge base manager not available"}
        
        try:
            return self.knowledge_base_manager.get_stats()
        except Exception as e:
            LOGGER.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
    
    def add_website_to_list(
        self,
        url: str,
        name: str,
        description: str = "",
        category: str = "forum",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a website to the website list.
        
        Args:
            url: Website URL
            name: Display name
            description: Description
            category: Category (forum, documentation, blog, etc.)
            metadata: Optional metadata
            
        Returns:
            Result dictionary
        """
        if not self.website_list_manager:
            return {"success": False, "error": "Website list manager not available"}
        
        try:
            success = self.website_list_manager.add_website(url, name, description, category, metadata)
            return {"success": success, "message": "Website added" if success else "Website already exists"}
        except Exception as e:
            LOGGER.error(f"Failed to add website to list: {e}")
            return {"success": False, "error": str(e)}
    
    def remove_website_from_list(self, url: str) -> Dict[str, Any]:
        """
        Remove a website from the website list.
        
        Args:
            url: Website URL to remove
            
        Returns:
            Result dictionary
        """
        if not self.website_list_manager:
            return {"success": False, "error": "Website list manager not available"}
        
        try:
            success = self.website_list_manager.remove_website(url)
            return {"success": success, "message": "Website removed" if success else "Website not found"}
        except Exception as e:
            LOGGER.error(f"Failed to remove website from list: {e}")
            return {"success": False, "error": str(e)}
    
    def get_website_list(self, enabled_only: bool = False, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of websites.
        
        Args:
            enabled_only: Only return enabled websites
            category: Filter by category
            
        Returns:
            List of website dictionaries
        """
        if not self.website_list_manager:
            return []
        
        try:
            websites = self.website_list_manager.get_websites(enabled_only=enabled_only, category=category)
            return [asdict(w) for w in websites]
        except Exception as e:
            LOGGER.error(f"Failed to get website list: {e}")
            return []
    
    def ingest_websites_from_list(
        self,
        enabled_only: bool = True,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest all websites from the website list.
        
        Args:
            enabled_only: Only ingest enabled websites
            category: Filter by category
            
        Returns:
            Summary dictionary
        """
        if not self.website_ingestion_service:
            return {"error": "Website ingestion service not available"}
        
        try:
            result = self.website_ingestion_service.ingest_all(enabled_only=enabled_only, category=category)
            LOGGER.info(f"Ingested {result['successful']} websites, {result['total_chunks']} chunks")
            return result
        except Exception as e:
            LOGGER.error(f"Failed to ingest websites: {e}")
            return {"error": str(e)}
    
    def get_website_list_stats(self) -> Dict[str, Any]:
        """
        Get website list statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self.website_list_manager:
            return {"error": "Website list manager not available"}
        
        try:
            return self.website_list_manager.get_stats()
        except Exception as e:
            LOGGER.error(f"Failed to get website list stats: {e}")
            return {"error": str(e)}
    
    def get_suggestions(self, query: str = "") -> List[str]:
        """Get suggested questions."""
        suggestions = [
            "What is fuel pressure?",
            "How do I tune ignition timing?",
            "What is the safe AFR range?",
            "How does boost control work?",
            "What causes engine knock?",
        ]
        
        if query:
            # Filter suggestions based on query
            query_lower = query.lower()
            suggestions = [s for s in suggestions if query_lower in s.lower()]
        
        return suggestions[:5]


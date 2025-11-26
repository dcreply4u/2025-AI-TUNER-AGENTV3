"""
Example RAG-based AI Advisor Implementation
This is a simplified example showing how a modern RAG-based advisor would work.
"""

from typing import Dict, List, Optional, Any
import logging

LOGGER = logging.getLogger(__name__)

# Optional imports - install if using
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


class SimpleVectorStore:
    """
    Simple in-memory vector store for demonstration.
    In production, use Chroma or similar.
    """
    
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.metadata = []
        self.encoder = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Lightweight model, good for Raspberry Pi
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                LOGGER.info("Sentence transformer loaded")
            except Exception as e:
                LOGGER.warning(f"Could not load sentence transformer: {e}")
    
    def add(self, text: str, metadata: Dict[str, Any] = None):
        """Add a document to the store."""
        if self.encoder:
            embedding = self.encoder.encode(text).tolist()
        else:
            # Fallback: simple word-based embedding (not as good)
            embedding = self._simple_embedding(text)
        
        self.documents.append(text)
        self.embeddings.append(embedding)
        self.metadata.append(metadata or {})
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.documents:
            return []
        
        if self.encoder:
            query_embedding = self.encoder.encode(query).tolist()
        else:
            query_embedding = self._simple_embedding(query)
        
        # Calculate similarities (cosine similarity)
        similarities = []
        for emb in self.embeddings:
            similarity = self._cosine_similarity(query_embedding, emb)
            similarities.append(similarity)
        
        # Get top N results
        results = sorted(
            zip(self.documents, self.metadata, similarities),
            key=lambda x: x[2],
            reverse=True
        )[:n_results]
        
        return [
            {
                "text": doc,
                "metadata": meta,
                "similarity": sim
            }
            for doc, meta, sim in results
        ]
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Simple word-based embedding (fallback)."""
        words = text.lower().split()
        # Create a simple frequency-based vector
        # In production, use proper embeddings
        return [float(len(word)) for word in words[:50]]  # Simplified
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


class RAGAIAdvisor:
    """
    Modern RAG-based AI Advisor.
    
    This is a simplified example. For production, use:
    - Chroma for vector storage
    - Ollama or OpenAI for LLM
    - Proper error handling and logging
    """
    
    def __init__(self, use_local_llm: bool = True, model: str = "llama3.2:3b"):
        """
        Initialize RAG-based advisor.
        
        Args:
            use_local_llm: Use local Ollama LLM (requires Ollama installed)
            model: Model name for Ollama
        """
        self.vector_store = SimpleVectorStore()
        self.use_local_llm = use_local_llm and OLLAMA_AVAILABLE
        self.model = model
        self.conversation_history = []
        
        # Initialize with some knowledge
        self._initialize_knowledge()
        
        LOGGER.info(f"RAG AI Advisor initialized (LLM: {self.use_local_llm})")
    
    def _initialize_knowledge(self):
        """Initialize with some basic knowledge."""
        knowledge_items = [
            {
                "text": "Fuel pressure is the pressure at which fuel is delivered to the engine. "
                       "Normal fuel pressure for most vehicles is 40-60 PSI. For high-performance "
                       "vehicles like the Dodge Hellcat, fuel pressure can be 58-65 PSI at idle.",
                "metadata": {"topic": "Fuel Pressure", "category": "technical_spec"}
            },
            {
                "text": "ECU tuning involves adjusting fuel maps, ignition timing, and boost control "
                       "to optimize engine performance. The main components are the VE (Volumetric "
                       "Efficiency) table and ignition timing maps.",
                "metadata": {"topic": "ECU Tuning", "category": "feature"}
            },
            {
                "text": "Knock sensors detect engine detonation (knock) and send signals to the ECU "
                       "to retard timing. If you're getting knock, reduce ignition timing advance "
                       "or check for lean AFR conditions.",
                "metadata": {"topic": "Knock Sensor", "category": "troubleshooting"}
            },
        ]
        
        for item in knowledge_items:
            self.vector_store.add(item["text"], item["metadata"])
    
    def answer(self, question: str, telemetry: Optional[Dict[str, float]] = None) -> str:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            telemetry: Optional current telemetry data
            
        Returns:
            Answer string
        """
        # 1. Retrieve relevant knowledge
        results = self.vector_store.search(question, n_results=3)
        
        if not results or results[0]["similarity"] < 0.3:
            # No relevant knowledge found
            if self.use_local_llm:
                return self._generate_with_llm(question, context="", use_web_search=True)
            else:
                return "I don't have specific information about that. Could you rephrase your question?"
        
        # 2. Build context from retrieved knowledge
        context_parts = []
        for result in results:
            if result["similarity"] > 0.3:  # Only use relevant results
                context_parts.append(f"- {result['text']}")
        
        context = "\n".join(context_parts)
        
        # 3. Add telemetry if relevant
        if telemetry and self._is_telemetry_relevant(question):
            telemetry_str = self._format_telemetry(telemetry)
            context += f"\n\nCurrent Vehicle Data:\n{telemetry_str}"
        
        # 4. Generate response
        if self.use_local_llm:
            response = self._generate_with_llm(question, context)
        else:
            # Fallback: simple template-based response
            response = self._generate_template_response(question, context)
        
        # 5. Store in conversation history
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return response
    
    def _generate_with_llm(self, question: str, context: str, use_web_search: bool = False) -> str:
        """Generate response using Ollama LLM."""
        if not OLLAMA_AVAILABLE:
            return self._generate_template_response(question, context)
        
        try:
            system_prompt = """You are Q, an expert automotive tuning advisor. 
Answer questions accurately using the provided context. Be concise, technical, and helpful.
If the context doesn't contain the answer, say so clearly."""
            
            # Build prompt with context
            prompt = f"""Context:
{context}

Question: {question}

Answer:"""
            
            # Call Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                system=system_prompt,
                options={
                    "temperature": 0.7,  # Balance creativity and accuracy
                    "top_p": 0.9,
                }
            )
            
            return response["response"].strip()
            
        except Exception as e:
            LOGGER.error(f"LLM generation failed: {e}")
            # Fallback to template
            return self._generate_template_response(question, context)
    
    def _generate_template_response(self, question: str, context: str) -> str:
        """Simple template-based response (fallback)."""
        if not context:
            return "I don't have enough information to answer that question accurately."
        
        # Extract first relevant piece of knowledge
        lines = context.split("\n")
        relevant_info = lines[0].replace("- ", "") if lines else context
        
        return f"Based on the information I have: {relevant_info}"
    
    def _is_telemetry_relevant(self, question: str) -> bool:
        """Check if question is about current telemetry."""
        telemetry_keywords = ["current", "now", "live", "real-time", "rpm", "boost", "afr", "temperature"]
        question_lower = question.lower()
        return any(kw in question_lower for kw in telemetry_keywords)
    
    def _format_telemetry(self, telemetry: Dict[str, float]) -> str:
        """Format telemetry data for context."""
        parts = []
        for key, value in telemetry.items():
            if isinstance(value, (int, float)):
                parts.append(f"  {key}: {value:.2f}")
        return "\n".join(parts)
    
    def add_knowledge(self, text: str, metadata: Dict[str, Any] = None):
        """Add new knowledge to the vector store."""
        self.vector_store.add(text, metadata)
        LOGGER.info(f"Added knowledge: {metadata.get('topic', 'Unknown') if metadata else 'Unknown'}")


# Example usage
if __name__ == "__main__":
    # Initialize advisor
    advisor = RAGAIAdvisor(use_local_llm=False)  # Set to True if Ollama is installed
    
    # Test questions
    questions = [
        "What is fuel pressure?",
        "What is fuel pressure for a Dodge Hellcat?",
        "How does ECU tuning work?",
        "What should I do if I'm getting knock?",
    ]
    
    print("RAG AI Advisor Test\n" + "=" * 50)
    for question in questions:
        answer = advisor.answer(question)
        print(f"\nQ: {question}")
        print(f"A: {answer}")
        print("-" * 50)



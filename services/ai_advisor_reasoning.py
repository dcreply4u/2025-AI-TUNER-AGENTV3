"""
Advanced Reasoning Module for AI Advisor

Adds chain-of-thought reasoning, multi-step problem solving, and better synthesis.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
import re

LOGGER = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Advanced reasoning engine for AI advisor.
    
    Features:
    - Chain-of-thought reasoning
    - Multi-step problem decomposition
    - Source synthesis and validation
    - Answer validation
    """
    
    def __init__(self):
        """Initialize reasoning engine."""
        self.reasoning_cache: Dict[str, str] = {}
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze question to understand intent and complexity.
        
        Returns:
            Analysis dictionary with intent, complexity, key_terms, etc.
        """
        question_lower = question.lower()
        
        # Detect question type
        question_type = "general"
        if any(k in question_lower for k in ['what is', "what's", 'define', 'explain']):
            question_type = "definition"
        elif any(k in question_lower for k in ['how', 'why']):
            question_type = "process"
        elif any(k in question_lower for k in ['should', 'recommend', 'best', 'optimal', 'ideal']):
            question_type = "recommendation"
        elif any(k in question_lower for k in ['problem', 'issue', 'error', 'fault', 'wrong', 'broken']):
            question_type = "troubleshooting"
        elif any(k in question_lower for k in ['compare', 'difference', 'vs', 'versus']):
            question_type = "comparison"
        elif any(k in question_lower for k in ['when', 'where']):
            question_type = "temporal_spatial"
        
        # Extract key terms
        words = re.findall(r'\b\w+\b', question_lower)
        stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'for', 'on', 'in', 'at', 'with', 'to', 
                     'how', 'why', 'when', 'where', 'should', 'can', 'could', 'would', 'do', 'does'}
        key_terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Assess complexity
        complexity = "simple"
        if len(key_terms) > 5 or question_type in ["process", "troubleshooting", "comparison"]:
            complexity = "complex"
        elif len(key_terms) > 3:
            complexity = "moderate"
        
        # Detect if needs multi-step reasoning
        needs_reasoning = complexity in ["complex", "moderate"] or question_type in ["process", "troubleshooting", "recommendation"]
        
        return {
            "question_type": question_type,
            "complexity": complexity,
            "key_terms": key_terms,
            "needs_reasoning": needs_reasoning,
            "original_question": question
        }
    
    def decompose_question(self, question: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Decompose complex question into sub-questions.
        
        Returns:
            List of sub-questions to answer
        """
        if not analysis.get("needs_reasoning"):
            return [question]
        
        question_type = analysis.get("question_type", "general")
        sub_questions = []
        
        if question_type == "troubleshooting":
            # Break down troubleshooting into steps
            sub_questions.append(f"What are the symptoms described in: {question}?")
            sub_questions.append(f"What are common causes of these symptoms?")
            sub_questions.append(f"What are the recommended solutions?")
        
        elif question_type == "process":
            # Break down "how" questions
            sub_questions.append(f"What is the goal in: {question}?")
            sub_questions.append(f"What are the steps to achieve this?")
            sub_questions.append(f"What are important considerations?")
        
        elif question_type == "recommendation":
            # Break down recommendation questions
            sub_questions.append(f"What are the requirements in: {question}?")
            sub_questions.append(f"What are the available options?")
            sub_questions.append(f"What are the trade-offs?")
            sub_questions.append(f"What is the best recommendation?")
        
        elif question_type == "comparison":
            # Break down comparison questions
            parts = re.split(r'\b(vs|versus|compared to|difference between)\b', question, flags=re.IGNORECASE)
            if len(parts) >= 3:
                item1 = parts[0].strip()
                item2 = parts[2].strip()
                sub_questions.append(f"What are the characteristics of {item1}?")
                sub_questions.append(f"What are the characteristics of {item2}?")
                sub_questions.append(f"What are the key differences?")
        
        return sub_questions if sub_questions else [question]
    
    def synthesize_sources(
        self,
        knowledge_sources: List[Dict[str, Any]],
        web_sources: List[Dict[str, Any]],
        question: str
    ) -> Dict[str, Any]:
        """
        Synthesize information from multiple sources intelligently.
        
        Returns:
            Synthesized information dictionary
        """
        synthesis = {
            "main_points": [],
            "supporting_details": [],
            "conflicts": [],
            "confidence": 0.0,
            "sources_used": []
        }
        
        all_sources = []
        
        # Combine knowledge and web sources
        for item in knowledge_sources:
            all_sources.append({
                "text": item.get("text", ""),
                "similarity": item.get("similarity", 0),
                "source": "knowledge_base",
                "metadata": item.get("metadata", {})
            })
        
        for item in web_sources:
            all_sources.append({
                "text": item.get("snippet", ""),
                "similarity": 0.7,  # Default for web sources
                "source": "web",
                "title": item.get("title", ""),
                "url": item.get("url", "")
            })
        
        # Sort by relevance
        all_sources.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        
        # Extract main points from top sources
        main_points = set()
        for source in all_sources[:3]:
            text = source.get("text", "")
            # Extract key sentences (simple heuristic)
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences[:2]:  # Top 2 sentences per source
                sentence = sentence.strip()
                if len(sentence) > 20 and len(sentence) < 200:
                    main_points.add(sentence)
        
        synthesis["main_points"] = list(main_points)[:5]  # Top 5 main points
        
        # Collect supporting details
        for source in all_sources[:5]:
            synthesis["supporting_details"].append({
                "text": source.get("text", "")[:200],
                "source": source.get("source", "unknown"),
                "relevance": source.get("similarity", 0)
            })
        
        # Check for conflicts
        # Simple conflict detection: look for contradictory keywords
        positive_keywords = ['should', 'must', 'recommended', 'optimal', 'best', 'good']
        negative_keywords = ['avoid', 'never', 'bad', 'wrong', 'problem', 'issue']
        
        positive_count = sum(1 for s in all_sources if any(k in s.get("text", "").lower() for k in positive_keywords))
        negative_count = sum(1 for s in all_sources if any(k in s.get("text", "").lower() for k in negative_keywords))
        
        if positive_count > 0 and negative_count > 0:
            synthesis["conflicts"].append("Mixed signals detected - some sources recommend, others warn against")
        
        # Calculate confidence
        if all_sources:
            avg_similarity = sum(s.get("similarity", 0) for s in all_sources) / len(all_sources)
            source_count_bonus = min(len(all_sources) / 5, 0.3)  # Bonus for multiple sources
            synthesis["confidence"] = min(avg_similarity + source_count_bonus, 1.0)
        
        synthesis["sources_used"] = [s.get("source", "unknown") for s in all_sources[:5]]
        
        return synthesis
    
    def validate_answer(self, answer: str, question: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate answer quality and completeness.
        
        Returns:
            Validation results
        """
        validation = {
            "is_complete": False,
            "is_accurate": True,  # Assume accurate unless proven otherwise
            "missing_info": [],
            "warnings": []
        }
        
        # Check completeness
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # Check if answer addresses the question
        key_terms = re.findall(r'\b\w{4,}\b', question_lower)  # Words 4+ chars
        key_terms = [t for t in key_terms if t not in ['what', 'how', 'why', 'when', 'where', 'should']]
        
        terms_mentioned = sum(1 for term in key_terms if term in answer_lower)
        if terms_mentioned < len(key_terms) * 0.5:
            validation["missing_info"].append("Answer may not fully address all aspects of the question")
        
        # Check for uncertainty markers
        uncertainty_markers = ['not sure', 'uncertain', 'unclear', "don't know", "can't", "unable"]
        if any(marker in answer_lower for marker in uncertainty_markers):
            validation["warnings"].append("Answer contains uncertainty markers")
        
        # Check for sources
        if not sources:
            validation["warnings"].append("No sources cited")
        
        # Check answer length (too short might be incomplete)
        if len(answer) < 50 and len(question.split()) > 5:
            validation["missing_info"].append("Answer seems too brief for the complexity of the question")
        
        validation["is_complete"] = len(validation["missing_info"]) == 0
        
        return validation
    
    def generate_reasoning_chain(self, question: str, analysis: Dict[str, Any]) -> str:
        """
        Generate chain-of-thought reasoning steps.
        
        Returns:
            Reasoning chain as formatted string
        """
        reasoning_steps = []
        
        reasoning_steps.append(f"**Step 1: Understanding the Question**")
        reasoning_steps.append(f"Question type: {analysis.get('question_type', 'general')}")
        reasoning_steps.append(f"Key terms: {', '.join(analysis.get('key_terms', [])[:5])}")
        reasoning_steps.append(f"Complexity: {analysis.get('complexity', 'simple')}")
        
        if analysis.get("needs_reasoning"):
            reasoning_steps.append(f"\n**Step 2: Breaking Down the Problem**")
            sub_questions = self.decompose_question(question, analysis)
            for i, sq in enumerate(sub_questions, 1):
                reasoning_steps.append(f"{i}. {sq}")
        
        reasoning_steps.append(f"\n**Step 3: Gathering Information**")
        reasoning_steps.append("Reviewing knowledge base, web search results, and telemetry data...")
        
        reasoning_steps.append(f"\n**Step 4: Synthesizing Information**")
        reasoning_steps.append("Combining information from multiple sources...")
        
        reasoning_steps.append(f"\n**Step 5: Formulating Answer**")
        reasoning_steps.append("Constructing comprehensive answer based on analysis...")
        
        return "\n".join(reasoning_steps)


__all__ = ["ReasoningEngine"]


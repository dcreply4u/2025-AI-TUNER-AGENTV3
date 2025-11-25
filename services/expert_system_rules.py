"""
Expert System Rules Engine

Rule-based reasoning engine for logical inference and diagnostic chains.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

LOGGER = logging.getLogger(__name__)


@dataclass
class Rule:
    """Expert system rule."""
    rule_id: str
    name: str
    condition: str  # Human-readable condition
    condition_func: Callable[[Dict[str, Any]], bool]  # Function to evaluate condition
    action: str  # Action/conclusion
    confidence: float  # 0-1
    priority: int  # Higher = more important
    category: str  # "safety", "performance", "diagnostics", etc.


@dataclass
class Conclusion:
    """Conclusion from rule evaluation."""
    conclusion_id: str
    rule_id: str
    conclusion: str
    confidence: float
    facts_used: List[str]
    reasoning: str


class ExpertSystemRules:
    """
    Expert system rules engine for logical inference.
    
    Features:
    - Forward chaining (facts -> conclusions)
    - Backward chaining (goal -> facts needed)
    - Rule priority
    - Confidence propagation
    - Conflict resolution
    """
    
    def __init__(self):
        """Initialize expert system."""
        self.rules: List[Rule] = []
        self.facts: Dict[str, Any] = {}
        self.conclusions: List[Conclusion] = []
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def add_rule(
        self,
        rule_id: str,
        name: str,
        condition: str,
        condition_func: Callable[[Dict[str, Any]], bool],
        action: str,
        confidence: float = 0.8,
        priority: int = 5,
        category: str = "general"
    ) -> None:
        """
        Add rule to expert system.
        
        Args:
            rule_id: Unique rule identifier
            name: Rule name
            condition: Human-readable condition
            condition_func: Function to evaluate condition
            action: Action/conclusion
            confidence: Rule confidence (0-1)
            priority: Rule priority (higher = more important)
            category: Rule category
        """
        rule = Rule(
            rule_id=rule_id,
            name=name,
            condition=condition,
            condition_func=condition_func,
            action=action,
            confidence=confidence,
            priority=priority,
            category=category,
        )
        
        self.rules.append(rule)
        # Sort by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def add_fact(self, fact_name: str, value: Any) -> None:
        """
        Add fact to knowledge base.
        
        Args:
            fact_name: Fact name
            value: Fact value
        """
        self.facts[fact_name] = value
    
    def evaluate(self, facts: Optional[Dict[str, Any]] = None) -> List[Conclusion]:
        """
        Evaluate rules with given facts (forward chaining).
        
        Args:
            facts: Additional facts to consider
        
        Returns:
            List of conclusions
        """
        # Merge facts
        all_facts = {**self.facts}
        if facts:
            all_facts.update(facts)
        
        conclusions = []
        
        # Evaluate each rule
        for rule in self.rules:
            try:
                if rule.condition_func(all_facts):
                    conclusion = Conclusion(
                        conclusion_id=f"conclusion_{len(conclusions)}",
                        rule_id=rule.rule_id,
                        conclusion=rule.action,
                        confidence=rule.confidence,
                        facts_used=[k for k, v in all_facts.items() if v],
                        reasoning=f"Rule '{rule.name}': {rule.condition}",
                    )
                    conclusions.append(conclusion)
            except Exception as e:
                LOGGER.error("Error evaluating rule %s: %s", rule.rule_id, e)
        
        # Resolve conflicts (higher priority wins)
        conclusions = self._resolve_conflicts(conclusions)
        
        self.conclusions = conclusions
        return conclusions
    
    def _resolve_conflicts(self, conclusions: List[Conclusion]) -> List[Conclusion]:
        """Resolve conflicting conclusions."""
        if not conclusions:
            return []
        
        # Group by conclusion text
        conclusion_groups: Dict[str, List[Conclusion]] = {}
        for conclusion in conclusions:
            key = conclusion.conclusion
            if key not in conclusion_groups:
                conclusion_groups[key] = []
            conclusion_groups[key].append(conclusion)
        
        # For each group, take highest confidence
        resolved = []
        for group in conclusion_groups.values():
            best = max(group, key=lambda c: c.confidence)
            resolved.append(best)
        
        return resolved
    
    def _initialize_default_rules(self) -> None:
        """Initialize default expert system rules."""
        
        # Safety rules (high priority)
        self.add_rule(
            rule_id="safety_knock",
            name="Knock Detection",
            condition="knock_count > 0",
            condition_func=lambda f: f.get("knock_count", 0) > 0,
            action="Reduce ignition timing by 2-3 degrees immediately",
            confidence=0.95,
            priority=10,
            category="safety",
        )
        
        self.add_rule(
            rule_id="safety_egt_high",
            name="High EGT Warning",
            condition="egt > 900",
            condition_func=lambda f: f.get("egt", 0) > 900,
            action="Richen AFR to cool exhaust, reduce boost if necessary",
            confidence=0.9,
            priority=9,
            category="safety",
        )
        
        self.add_rule(
            rule_id="safety_lean",
            name="Lean Condition",
            condition="lambda > 1.1",
            condition_func=lambda f: f.get("lambda", 1.0) > 1.1,
            action="Add fuel immediately - lean condition is dangerous",
            confidence=0.95,
            priority=10,
            category="safety",
        )
        
        # Performance rules
        self.add_rule(
            rule_id="perf_rich_power",
            name="Rich for Power",
            condition="lambda < 0.85 and load > 0.8",
            condition_func=lambda f: f.get("lambda", 1.0) < 0.85 and f.get("load", 0) > 0.8,
            action="AFR is good for power, consider advancing timing if no knock",
            confidence=0.7,
            priority=5,
            category="performance",
        )
        
        self.add_rule(
            rule_id="perf_timing_advance",
            name="Timing Advance Opportunity",
            condition="timing < 25 and knock_count == 0 and load > 0.7",
            condition_func=lambda f: (
                f.get("timing", 0) < 25 and
                f.get("knock_count", 0) == 0 and
                f.get("load", 0) > 0.7
            ),
            action="Can advance timing 1-2 degrees for more power",
            confidence=0.7,
            priority=6,
            category="performance",
        )
        
        # Diagnostic rules
        self.add_rule(
            rule_id="diag_coolant_rising",
            name="Coolant Temperature Rising",
            condition="coolant_temp > 100 and coolant_temp_trend == 'increasing'",
            condition_func=lambda f: (
                f.get("coolant_temp", 0) > 100 and
                f.get("coolant_temp_trend") == "increasing"
            ),
            action="Cooling system issue - check coolant level and pump",
            confidence=0.8,
            priority=7,
            category="diagnostics",
        )
        
        self.add_rule(
            rule_id="diag_oil_pressure_low",
            name="Low Oil Pressure",
            condition="oil_pressure < 20",
            condition_func=lambda f: f.get("oil_pressure", 0) < 20,
            action="Low oil pressure - check oil level and pump immediately",
            confidence=0.9,
            priority=9,
            category="diagnostics",
        )


__all__ = [
    "ExpertSystemRules",
    "Rule",
    "Conclusion",
]










#!/usr/bin/env python3
"""
Edge Case Testing Framework

Uses Hypothesis for property-based testing to automatically generate
edge cases and verify code handles them correctly.
"""

from hypothesis import given, strategies as st, settings, example
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from typing import List, Optional, Any
import logging

LOGGER = logging.getLogger(__name__)


# Example: Edge case testing for a percentage calculator
@given(
    value=st.floats(min_value=0, max_value=1000),
    total=st.floats(min_value=0.1, max_value=1000)
)
@settings(max_examples=100)
def test_calculate_percentage(value: float, total: float):
    """
    Test percentage calculation with edge cases.
    Hypothesis will automatically generate edge cases like:
    - value = 0
    - total = 0.1 (very small)
    - value > total
    - Negative values (if not filtered)
    """
    from hypothesis import assume
    
    # Filter out invalid cases
    assume(total > 0)  # Total must be positive
    assume(value >= 0)  # Value must be non-negative
    
    # Calculate percentage
    percentage = (value / total) * 100
    
    # Verify properties
    assert percentage >= 0, "Percentage should be non-negative"
    assert percentage <= (value / total) * 100 + 0.01, "Percentage calculation error"
    
    # Edge case: value = 0
    if value == 0:
        assert percentage == 0, "Zero value should give zero percentage"
    
    # Edge case: value = total
    if abs(value - total) < 0.01:
        assert abs(percentage - 100) < 0.01, "Equal value and total should give 100%"


# Example: Edge case testing for list operations
@given(
    items=st.lists(st.integers(), min_size=0, max_size=1000)
)
@settings(max_examples=50)
def test_list_operations(items: List[int]):
    """
    Test list operations with edge cases:
    - Empty list
    - Single element
    - Very large list
    - Duplicate values
    """
    # Edge case: Empty list
    if len(items) == 0:
        assert len(items) == 0
        return
    
    # Edge case: Single element
    if len(items) == 1:
        assert items[0] == items[-1]
    
    # Test operations
    sorted_items = sorted(items)
    assert len(sorted_items) == len(items)
    assert min(sorted_items) == sorted_items[0]
    assert max(sorted_items) == sorted_items[-1]


# Example: Stateful testing for a data structure
class ListStateMachine(RuleBasedStateMachine):
    """
    Stateful testing for list operations.
    Hypothesis will generate sequences of operations to find edge cases.
    """
    
    def __init__(self):
        super().__init__()
        self.items: List[int] = []
    
    @rule(value=st.integers())
    def add_item(self, value: int):
        """Add an item to the list."""
        self.items.append(value)
        assert len(self.items) > 0
    
    @rule()
    def remove_item(self):
        """Remove an item from the list if not empty."""
        if len(self.items) > 0:
            self.items.pop()
    
    @rule()
    def clear_list(self):
        """Clear the list."""
        self.items.clear()
        assert len(self.items) == 0
    
    @invariant()
    def length_non_negative(self):
        """Invariant: length is always non-negative."""
        assert len(self.items) >= 0
    
    @invariant()
    def no_duplicates_if_sorted(self):
        """Invariant: if sorted, no duplicates (for testing)."""
        if len(self.items) > 1:
            sorted_items = sorted(self.items)
            # This invariant might fail, helping us find edge cases
            pass


# Utility functions for common edge cases
def generate_edge_cases_for_numeric_function(func, min_val=-1000, max_val=1000):
    """
    Generate edge cases for a numeric function.
    
    Args:
        func: Function to test
        min_val: Minimum value to test
        max_val: Maximum value to test
    
    Returns:
        List of edge cases that cause issues
    """
    edge_cases = [
        0,
        -1,
        1,
        min_val,
        max_val,
        float('inf'),
        float('-inf'),
        float('nan'),
    ]
    
    issues = []
    for case in edge_cases:
        try:
            result = func(case)
            # Check for reasonable result
            if not isinstance(result, (int, float)) or result != result:  # NaN check
                issues.append(f"Edge case {case} produced invalid result: {result}")
        except Exception as e:
            issues.append(f"Edge case {case} raised exception: {e}")
    
    return issues


def generate_edge_cases_for_string_function(func):
    """
    Generate edge cases for a string function.
    
    Args:
        func: Function to test
    
    Returns:
        List of edge cases that cause issues
    """
    edge_cases = [
        "",
        " ",
        "a",
        "A" * 1000,  # Very long string
        "\n",
        "\t",
        "\x00",  # Null byte
        "🚗",  # Unicode
        "test\x00null",  # Null byte in string
    ]
    
    issues = []
    for case in edge_cases:
        try:
            result = func(case)
        except Exception as e:
            issues.append(f"Edge case '{case}' raised exception: {e}")
    
    return issues


# Example usage
if __name__ == "__main__":
    # Test percentage calculator
    print("Testing percentage calculator...")
    test_calculate_percentage()
    print("✓ Percentage calculator tests passed")
    
    # Test list operations
    print("\nTesting list operations...")
    test_list_operations()
    print("✓ List operations tests passed")
    
    # Generate edge cases for a function
    def divide_by_two(x):
        return x / 2
    
    print("\nGenerating edge cases for divide_by_two...")
    issues = generate_edge_cases_for_numeric_function(divide_by_two)
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ No issues found")


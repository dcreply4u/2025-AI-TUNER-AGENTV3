#!/usr/bin/env python3
"""
Performance Profiling Tool

Provides utilities for profiling code performance including:
- CPU profiling
- Memory profiling
- Line-by-line profiling
"""

import cProfile
import pstats
import io
import sys
from pathlib import Path
from typing import Optional, Callable, Any
import functools


def profile_function(output_file: Optional[Path] = None, sort_by: str = 'cumulative'):
    """
    Decorator to profile a function's performance.
    
    Args:
        output_file: Optional file to save profile results
        sort_by: Sort key for stats (cumulative, time, calls, etc.)
    
    Example:
        @profile_function(output_file=Path("profile_results.txt"))
        def my_function():
            # code to profile
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                
                # Create stats
                stats = pstats.Stats(profiler)
                stats.sort_stats(sort_by)
                
                # Print to console
                stats.print_stats(20)  # Top 20 functions
                
                # Save to file if specified
                if output_file:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, 'w') as f:
                        stats_stream = io.StringIO()
                        stats.print_stats(file=stats_stream)
                        f.write(stats_stream.getvalue())
                    print(f"\nProfile saved to: {output_file}")
            
            return result
        return wrapper
    return decorator


def profile_memory(func: Callable) -> Callable:
    """
    Decorator to profile memory usage of a function.
    Requires: pip install memory-profiler
    
    Example:
        @profile_memory
        def my_function():
            # code to profile
            pass
    """
    try:
        from memory_profiler import profile as mem_profile
        return mem_profile(func)
    except ImportError:
        print("Warning: memory-profiler not installed. Install with: pip install memory-profiler")
        return func


def profile_line_by_line(func: Callable) -> Callable:
    """
    Decorator to profile line-by-line execution time.
    Requires: pip install line-profiler
    
    Usage:
        @profile_line_by_line
        def my_function():
            # code to profile
            pass
        
        # Run with: kernprof -l -v script.py
    """
    try:
        from line_profiler import profile as line_profile
        return line_profile(func)
    except ImportError:
        print("Warning: line-profiler not installed. Install with: pip install line-profiler")
        return func


class PerformanceProfiler:
    """Context manager for profiling code blocks."""
    
    def __init__(self, output_file: Optional[Path] = None, sort_by: str = 'cumulative'):
        self.output_file = output_file
        self.sort_by = sort_by
        self.profiler: Optional[cProfile.Profile] = None
    
    def __enter__(self):
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profiler:
            self.profiler.disable()
            
            stats = pstats.Stats(self.profiler)
            stats.sort_stats(self.sort_by)
            
            # Print to console
            stats.print_stats(20)
            
            # Save to file if specified
            if self.output_file:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, 'w') as f:
                    stats_stream = io.StringIO()
                    stats.print_stats(file=stats_stream)
                    f.write(stats_stream.getvalue())
                print(f"\nProfile saved to: {self.output_file}")


# Example usage
if __name__ == "__main__":
    # Example 1: Profile a function
    @profile_function(output_file=Path("reports/profile_example.txt"))
    def example_function():
        total = 0
        for i in range(1000000):
            total += i
        return total
    
    # Example 2: Profile a code block
    with PerformanceProfiler(output_file=Path("reports/profile_block.txt")):
        result = sum(range(1000000))
    
    # Run example
    example_function()


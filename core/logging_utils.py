"""
Enhanced Logging Utilities

Provides decorators and context managers for:
- Performance logging
- Error tracking
- Function call logging
- Resource usage monitoring
"""

from __future__ import annotations

import functools
import logging
import time
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar

from core.logging_config import get_logger, log_performance

F = TypeVar('F', bound=Callable[..., Any])


def log_function_call(logger: Optional[logging.Logger] = None, log_args: bool = False, log_result: bool = False):
    """
    Decorator to log function calls.
    
    Args:
        logger: Logger instance (uses module logger if None)
        log_args: Whether to log function arguments
        log_result: Whether to log function return value
    """
    def decorator(func: F) -> F:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = f"{func.__module__}.{func.__name__}"
            logger.debug(f"Calling {func_name}")
            
            if log_args:
                logger.debug(f"  Args: {args}")
                logger.debug(f"  Kwargs: {kwargs}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if log_result:
                    logger.debug(f"  Result: {result}")
                
                logger.debug(f"{func_name} completed in {duration*1000:.2f}ms")
                log_performance(func_name, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{func_name} failed after {duration*1000:.2f}ms: {e}")
                logger.debug(traceback.format_exc())
                raise
        
        return wrapper  # type: ignore
    return decorator


def log_performance_metric(operation: str):
    """
    Decorator to log performance metrics for a function.
    
    Args:
        operation: Operation name for logging
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance(operation or func.__name__, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_performance(operation or func.__name__, duration, error=str(e))
                raise
        
        return wrapper  # type: ignore
    return decorator


@contextmanager
def log_execution_time(operation: str, logger: Optional[logging.Logger] = None):
    """
    Context manager to log execution time.
    
    Usage:
        with log_execution_time("database_query"):
            result = db.query(...)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    start_time = time.time()
    logger.debug(f"Starting {operation}")
    
    try:
        yield
        duration = time.time() - start_time
        logger.debug(f"{operation} completed in {duration*1000:.2f}ms")
        log_performance(operation, duration)
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{operation} failed after {duration*1000:.2f}ms: {e}")
        log_performance(operation, duration, error=str(e))
        raise


@contextmanager
def log_resource_usage(operation: str, logger: Optional[logging.Logger] = None):
    """
    Context manager to log resource usage (memory, CPU).
    
    Usage:
        with log_resource_usage("data_processing"):
            process_data()
    """
    if logger is None:
        logger = get_logger(__name__)
    
    try:
        import psutil
        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024 ** 2)  # MB
        cpu_before = process.cpu_percent()
    except ImportError:
        psutil = None
        mem_before = None
        cpu_before = None
    
    start_time = time.time()
    logger.debug(f"Starting {operation}")
    
    try:
        yield
        duration = time.time() - start_time
        
        if psutil:
            mem_after = process.memory_info().rss / (1024 ** 2)  # MB
            cpu_after = process.cpu_percent()
            mem_delta = mem_after - mem_before
            
            logger.debug(
                f"{operation} completed in {duration*1000:.2f}ms - "
                f"Memory: {mem_before:.1f}MB -> {mem_after:.1f}MB ({mem_delta:+.1f}MB), "
                f"CPU: {cpu_before:.1f}% -> {cpu_after:.1f}%"
            )
            log_performance(
                operation,
                duration,
                memory_mb_before=mem_before,
                memory_mb_after=mem_after,
                memory_delta_mb=mem_delta,
                cpu_percent_before=cpu_before,
                cpu_percent_after=cpu_after,
            )
        else:
            logger.debug(f"{operation} completed in {duration*1000:.2f}ms")
            log_performance(operation, duration)
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{operation} failed after {duration*1000:.2f}ms: {e}")
        log_performance(operation, duration, error=str(e))
        raise


def log_error_with_context(
    logger: Optional[logging.Logger] = None,
    reraise: bool = True,
    include_traceback: bool = True,
):
    """
    Decorator to log errors with full context.
    
    Args:
        logger: Logger instance
        reraise: Whether to re-raise the exception
        include_traceback: Whether to include full traceback
    """
    def decorator(func: F) -> F:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {func.__module__}.{func.__name__}: {e}"
                
                if include_traceback:
                    logger.error(error_msg, exc_info=True)
                else:
                    logger.error(error_msg)
                
                if reraise:
                    raise
        
        return wrapper  # type: ignore
    return decorator


__all__ = [
    "log_function_call",
    "log_performance_metric",
    "log_execution_time",
    "log_resource_usage",
    "log_error_with_context",
]


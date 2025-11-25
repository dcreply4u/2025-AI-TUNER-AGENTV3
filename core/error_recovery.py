"""
Error Recovery and Resilience Module

Provides automatic recovery mechanisms for common failures.
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar, Optional

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            delay: Initial delay between retries (seconds)
            backoff: Multiplier for delay after each retry
            exceptions: Tuple of exceptions to catch and retry
        """
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions


def retry_with_backoff(config: Optional[RetryConfig] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        config: Retry configuration (uses defaults if None)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cfg = config or RetryConfig()

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = cfg.delay
            last_exception: Optional[Exception] = None

            for attempt in range(cfg.max_attempts):
                try:
                    return func(*args, **kwargs)
                except cfg.exceptions as e:
                    last_exception = e
                    if attempt < cfg.max_attempts - 1:
                        LOGGER.warning(
                            "%s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                            func.__name__,
                            attempt + 1,
                            cfg.max_attempts,
                            e,
                            delay,
                        )
                        time.sleep(delay)
                        delay *= cfg.backoff
                    else:
                        LOGGER.error("%s failed after %d attempts: %s", func.__name__, cfg.max_attempts, e)

            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed after {cfg.max_attempts} attempts")

        return wrapper

    return decorator


class ConnectionManager:
    """Manages connection state and automatic reconnection."""

    def __init__(
        self,
        connect_func: Callable[[], Any],
        disconnect_func: Optional[Callable[[], None]] = None,
        health_check_func: Optional[Callable[[], bool]] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        """
        Initialize connection manager.

        Args:
            connect_func: Function to establish connection
            disconnect_func: Optional function to close connection
            health_check_func: Optional function to check connection health
            retry_config: Retry configuration for reconnection
        """
        self.connect_func = connect_func
        self.disconnect_func = disconnect_func
        self.health_check_func = health_check_func
        self.retry_config = retry_config or RetryConfig()
        self.connected = False
        self.connection: Any = None

    def connect(self) -> bool:
        """Establish connection with retry."""
        if self.connected and self.health_check_func:
            if self.health_check_func():
                return True

        @retry_with_backoff(self.retry_config)
        def _connect() -> Any:
            return self.connect_func()

        try:
            self.connection = _connect()
            self.connected = True
            LOGGER.info("Connection established successfully")
            return True
        except Exception as e:
            LOGGER.error("Failed to establish connection: %s", e)
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Close connection."""
        if self.disconnect_func and self.connection:
            try:
                self.disconnect_func()
            except Exception as e:
                LOGGER.warning("Error during disconnect: %s", e)
        self.connected = False
        self.connection = None

    def ensure_connected(self) -> bool:
        """Ensure connection is active, reconnect if needed."""
        if not self.connected:
            return self.connect()

        if self.health_check_func:
            if not self.health_check_func():
                LOGGER.warning("Connection health check failed, reconnecting...")
                self.disconnect()
                return self.connect()

        return True


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time to wait before attempting to close circuit (seconds)
            expected_exception: Exception type to count as failures
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open
            Exception: If function raises an exception
        """
        if self.state == "open":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                self.state = "half_open"
                LOGGER.info("Circuit breaker entering half-open state")
            else:
                raise RuntimeError("Circuit breaker is OPEN - operation blocked")

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                LOGGER.info("Circuit breaker closed - operation successful")
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                LOGGER.error(
                    "Circuit breaker OPENED after %d failures. Blocking operations for %.1fs",
                    self.failure_count,
                    self.timeout,
                )

            raise


__all__ = ["RetryConfig", "retry_with_backoff", "ConnectionManager", "CircuitBreaker"]

"""Retry policy implementation for resilient operations."""

import asyncio
import random
import time
from typing import Callable, Any, Optional, List, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod
from infrastructure.logging.logger_factory import get_module_logger


class BackoffStrategy(ABC):
    """Abstract base class for backoff strategies."""
    
    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number."""
        pass


class ExponentialBackoff(BackoffStrategy):
    """Exponential backoff strategy with optional jitter."""
    
    def __init__(
        self, 
        base_delay: float = 1.0, 
        max_delay: float = 60.0, 
        multiplier: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize exponential backoff.
        
        Args:
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            multiplier: Exponential multiplier
            jitter: Whether to add random jitter
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number."""
        delay = self.base_delay * (self.multiplier ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


class LinearBackoff(BackoffStrategy):
    """Linear backoff strategy."""
    
    def __init__(self, base_delay: float = 1.0, increment: float = 1.0, max_delay: float = 30.0):
        """
        Initialize linear backoff.
        
        Args:
            base_delay: Base delay in seconds
            increment: Delay increment per attempt
            max_delay: Maximum delay in seconds
        """
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number."""
        delay = self.base_delay + (self.increment * (attempt - 1))
        return min(delay, self.max_delay)


class FixedBackoff(BackoffStrategy):
    """Fixed delay backoff strategy."""
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize fixed backoff.
        
        Args:
            delay: Fixed delay in seconds
        """
        self.delay = delay
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number."""
        return self.delay


@dataclass
class RetryConfig:
    """Configuration for retry policy."""
    max_attempts: int = 3
    backoff_strategy: BackoffStrategy = None
    retryable_exceptions: List[Type[Exception]] = None
    timeout_per_attempt: Optional[float] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.backoff_strategy is None:
            self.backoff_strategy = ExponentialBackoff()
        
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [Exception]


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, attempts: int, last_exception: Exception):
        """
        Initialize retry exhausted error.
        
        Args:
            attempts: Number of attempts made
            last_exception: The last exception that occurred
        """
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"Retry exhausted after {attempts} attempts: {last_exception}")


class RetryPolicy:
    """
    Retry policy implementation for resilient operations.
    
    Provides configurable retry logic with different backoff strategies
    and exception handling for robust error recovery.
    """
    
    def __init__(self, config: RetryConfig, name: str = "default"):
        """
        Initialize retry policy.
        
        Args:
            config: Retry configuration
            name: Name for logging and identification
        """
        self.config = config
        self.name = name
        self.logger = get_module_logger(__name__)
        
        # Statistics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_attempts = 0
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry policy.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryExhaustedError: If all retry attempts are exhausted
        """
        self.total_calls += 1
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            self.total_attempts += 1
            
            try:
                self.logger.debug(f"Retry policy {self.name} - attempt {attempt}/{self.config.max_attempts}")
                
                # Execute with timeout if configured
                if self.config.timeout_per_attempt:
                    result = await asyncio.wait_for(
                        self._execute_function(func, *args, **kwargs),
                        timeout=self.config.timeout_per_attempt
                    )
                else:
                    result = await self._execute_function(func, *args, **kwargs)
                
                # Success
                self.successful_calls += 1
                if attempt > 1:
                    self.logger.info(f"Retry policy {self.name} succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if exception is retryable
                if not self._is_retryable_exception(e):
                    self.logger.warning(f"Non-retryable exception in {self.name}: {e}")
                    self.failed_calls += 1
                    raise e
                
                # Check if we have more attempts
                if attempt >= self.config.max_attempts:
                    break
                
                # Calculate delay and wait
                delay = self.config.backoff_strategy.get_delay(attempt)
                self.logger.warning(
                    f"Retry policy {self.name} - attempt {attempt} failed: {e}. "
                    f"Retrying in {delay:.2f}s"
                )
                
                await asyncio.sleep(delay)
        
        # All attempts exhausted
        self.failed_calls += 1
        self.logger.error(
            f"Retry policy {self.name} exhausted after {self.config.max_attempts} attempts. "
            f"Last error: {last_exception}"
        )
        
        raise RetryExhaustedError(self.config.max_attempts, last_exception)
    
    async def _execute_function(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function (async or sync)."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)
    
    def _is_retryable_exception(self, exception: Exception) -> bool:
        """Check if exception is retryable."""
        return any(
            isinstance(exception, exc_type) 
            for exc_type in self.config.retryable_exceptions
        )
    
    def get_stats(self) -> dict:
        """Get retry policy statistics."""
        success_rate = (
            (self.successful_calls / self.total_calls * 100) 
            if self.total_calls > 0 else 0
        )
        
        avg_attempts = (
            self.total_attempts / self.total_calls 
            if self.total_calls > 0 else 0
        )
        
        return {
            "name": self.name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "total_attempts": self.total_attempts,
            "success_rate": success_rate,
            "average_attempts": avg_attempts,
            "config": {
                "max_attempts": self.config.max_attempts,
                "timeout_per_attempt": self.config.timeout_per_attempt,
                "retryable_exceptions": [exc.__name__ for exc in self.config.retryable_exceptions]
            }
        }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_attempts = 0


# Convenience function for simple retry
async def retry(
    func: Callable,
    max_attempts: int = 3,
    backoff_strategy: Optional[BackoffStrategy] = None,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    timeout_per_attempt: Optional[float] = None,
    *args,
    **kwargs
) -> Any:
    """
    Simple retry function with default configuration.
    
    Args:
        func: Function to execute
        max_attempts: Maximum number of attempts
        backoff_strategy: Backoff strategy to use
        retryable_exceptions: List of retryable exception types
        timeout_per_attempt: Timeout per attempt in seconds
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_strategy=backoff_strategy or ExponentialBackoff(),
        retryable_exceptions=retryable_exceptions or [Exception],
        timeout_per_attempt=timeout_per_attempt
    )
    
    policy = RetryPolicy(config, "simple_retry")
    return await policy.execute(func, *args, **kwargs)


# Decorator for retry functionality
def retry_on_failure(
    max_attempts: int = 3,
    backoff_strategy: Optional[BackoffStrategy] = None,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    timeout_per_attempt: Optional[float] = None
):
    """
    Decorator for adding retry functionality to functions.
    
    Args:
        max_attempts: Maximum number of attempts
        backoff_strategy: Backoff strategy to use
        retryable_exceptions: List of retryable exception types
        timeout_per_attempt: Timeout per attempt in seconds
    """
    def decorator(func: Callable):
        config = RetryConfig(
            max_attempts=max_attempts,
            backoff_strategy=backoff_strategy or ExponentialBackoff(),
            retryable_exceptions=retryable_exceptions or [Exception],
            timeout_per_attempt=timeout_per_attempt
        )
        
        policy = RetryPolicy(config, func.__name__)
        
        async def wrapper(*args, **kwargs):
            return await policy.execute(func, *args, **kwargs)
        
        wrapper.retry_policy = policy
        return wrapper
    
    return decorator

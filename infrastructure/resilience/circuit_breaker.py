"""Circuit breaker pattern implementation for resilience."""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from infrastructure.logging.logger_factory import get_module_logger


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    timeout_duration: int = 60
    half_open_max_calls: int = 3
    expected_exception: type = Exception


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for handling failures gracefully.
    
    The circuit breaker monitors failures and prevents calls to failing services,
    allowing them time to recover while providing fast failure responses.
    """
    
    def __init__(self, config: CircuitBreakerConfig, name: str = "default"):
        """
        Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
            name: Name for logging and identification
        """
        self.config = config
        self.name = name
        self.logger = get_module_logger(__name__)
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        
        # Statistics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original function exceptions
        """
        async with self._lock:
            self.total_calls += 1
            
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    self.logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                else:
                    self.logger.warning(f"Circuit breaker {self.name} is OPEN - rejecting call")
                    raise CircuitBreakerError(f"Circuit breaker {self.name} is open")
            
            elif self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    self.logger.warning(f"Circuit breaker {self.name} HALF_OPEN limit reached")
                    raise CircuitBreakerError(f"Circuit breaker {self.name} half-open limit reached")
                
                self.half_open_calls += 1
        
        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self._on_success()
            return result
            
        except self.config.expected_exception as e:
            await self._on_failure()
            raise e
        except Exception as e:
            # Unexpected exceptions don't count as failures
            self.logger.warning(f"Unexpected exception in circuit breaker {self.name}: {e}")
            raise e
    
    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self.successful_calls += 1
            
            if self.state == CircuitState.HALF_OPEN:
                # Reset circuit breaker on successful half-open call
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_failure_time = None
                self.logger.info(f"Circuit breaker {self.name} reset to CLOSED")
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.failed_calls += 1
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.config.failure_threshold:
                if self.state != CircuitState.OPEN:
                    self.state = CircuitState.OPEN
                    self.logger.warning(
                        f"Circuit breaker {self.name} opened after {self.failure_count} failures"
                    )
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) >= self.config.timeout_duration
    
    async def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        async with self._lock:
            success_rate = (
                (self.successful_calls / self.total_calls * 100) 
                if self.total_calls > 0 else 0
            )
            
            return {
                "name": self.name,
                "state": self.state.value,
                "total_calls": self.total_calls,
                "successful_calls": self.successful_calls,
                "failed_calls": self.failed_calls,
                "failure_count": self.failure_count,
                "success_rate": success_rate,
                "last_failure_time": self.last_failure_time,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "timeout_duration": self.config.timeout_duration,
                    "half_open_max_calls": self.config.half_open_max_calls
                }
            }
    
    async def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.half_open_calls = 0
            self.logger.info(f"Circuit breaker {self.name} manually reset")
    
    async def force_open(self) -> None:
        """Manually force circuit breaker to open state."""
        async with self._lock:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            self.logger.warning(f"Circuit breaker {self.name} manually opened")


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    
    Provides centralized management and monitoring of circuit breakers
    across different services and operations.
    """
    
    def __init__(self):
        """Initialize circuit breaker manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = get_module_logger(__name__)
    
    def create_circuit_breaker(
        self, 
        name: str, 
        config: CircuitBreakerConfig
    ) -> CircuitBreaker:
        """
        Create and register a new circuit breaker.
        
        Args:
            name: Unique name for the circuit breaker
            config: Circuit breaker configuration
            
        Returns:
            CircuitBreaker instance
        """
        if name in self.circuit_breakers:
            self.logger.warning(f"Circuit breaker {name} already exists")
            return self.circuit_breakers[name]
        
        circuit_breaker = CircuitBreaker(config, name)
        self.circuit_breakers[name] = circuit_breaker
        
        self.logger.info(f"Created circuit breaker: {name}")
        return circuit_breaker
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.circuit_breakers.get(name)
    
    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        stats = {}
        for name, cb in self.circuit_breakers.items():
            stats[name] = await cb.get_stats()
        return stats
    
    async def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            await cb.reset()
        self.logger.info("All circuit breakers reset")
    
    def remove_circuit_breaker(self, name: str) -> bool:
        """Remove circuit breaker by name."""
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            self.logger.info(f"Removed circuit breaker: {name}")
            return True
        return False


# Global circuit breaker manager instance
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager instance."""
    global _circuit_breaker_manager
    
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    
    return _circuit_breaker_manager


def create_medical_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Create standard circuit breakers for medical services."""
    manager = get_circuit_breaker_manager()
    
    # ASR circuit breaker
    asr_config = CircuitBreakerConfig(
        failure_threshold=3,
        timeout_duration=30,
        half_open_max_calls=2
    )
    asr_cb = manager.create_circuit_breaker("asr_service", asr_config)
    
    # TTS circuit breaker
    tts_config = CircuitBreakerConfig(
        failure_threshold=3,
        timeout_duration=30,
        half_open_max_calls=2
    )
    tts_cb = manager.create_circuit_breaker("tts_service", tts_config)
    
    # Medical AI circuit breaker
    medical_config = CircuitBreakerConfig(
        failure_threshold=5,
        timeout_duration=60,
        half_open_max_calls=3
    )
    medical_cb = manager.create_circuit_breaker("medical_ai", medical_config)
    
    return {
        "asr": asr_cb,
        "tts": tts_cb,
        "medical": medical_cb
    }

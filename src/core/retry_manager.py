"""
Intelligent Retry Manager for VidTanium
Provides adaptive retry mechanisms with circuit breaker pattern and intelligent backoff
"""

import time
import asyncio
from typing import Callable, Any, Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from loguru import logger

from .exceptions import VidTaniumException, ErrorCategory, ErrorSeverity, ErrorContext
from .error_handler import EnhancedErrorHandler, RetryStrategy


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    timestamp: float
    exception: Optional[VidTaniumException] = None
    success: bool = False
    duration: float = 0.0


@dataclass
class RetrySession:
    """Tracks retry session for an operation"""
    operation_id: str
    start_time: float = field(default_factory=time.time)
    attempts: List[RetryAttempt] = field(default_factory=list)
    max_retries: int = 3
    total_delay: float = 0.0
    context: Optional[ErrorContext] = None


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: float = 60.0  # Seconds to wait before trying half-open
    success_threshold: int = 3  # Successes needed to close circuit from half-open
    monitoring_window: float = 300.0  # Window for failure rate calculation


class CircuitBreaker:
    """Circuit breaker implementation for preventing cascade failures"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.recent_attempts: List[Tuple[float, bool]] = []
        self.lock = Lock()
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        with self.lock:
            now = time.time()
            
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                if now - self.last_failure_time >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
    
    def record_success(self):
        """Record successful operation"""
        with self.lock:
            now = time.time()
            self.recent_attempts.append((now, True))
            self._cleanup_old_attempts(now)
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit breaker {self.name} transitioning to CLOSED")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed operation"""
        with self.lock:
            now = time.time()
            self.recent_attempts.append((now, False))
            self._cleanup_old_attempts(now)
            
            self.failure_count += 1
            self.last_failure_time = now
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning(f"Circuit breaker {self.name} transitioning to OPEN")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} transitioning back to OPEN")
    
    def _cleanup_old_attempts(self, now: float):
        """Remove attempts outside monitoring window"""
        cutoff = now - self.config.monitoring_window
        self.recent_attempts = [
            (timestamp, success) for timestamp, success in self.recent_attempts
            if timestamp >= cutoff
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            now = time.time()
            self._cleanup_old_attempts(now)
            
            total_attempts = len(self.recent_attempts)
            failures = sum(1 for _, success in self.recent_attempts if not success)
            failure_rate = failures / total_attempts if total_attempts > 0 else 0.0
            
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "total_attempts_recent": total_attempts,
                "failure_rate": failure_rate,
                "last_failure_time": self.last_failure_time
            }


class IntelligentRetryManager:
    """Intelligent retry manager with circuit breaker and adaptive strategies"""
    
    def __init__(self, error_handler: Optional[EnhancedErrorHandler] = None):
        self.error_handler = error_handler
        self.active_sessions: Dict[str, RetrySession] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.lock = Lock()
        
        # Default circuit breaker configs for different categories
        self.circuit_configs = {
            ErrorCategory.NETWORK: CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                success_threshold=2
            ),
            ErrorCategory.FILESYSTEM: CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=10.0,
                success_threshold=1
            ),
            ErrorCategory.ENCRYPTION: CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=60.0,
                success_threshold=1
            )
        }
    
    def execute_with_retry(
        self,
        operation: Callable[[], Any],
        operation_id: str,
        context: Optional[ErrorContext] = None,
        max_retries: Optional[int] = None
    ) -> Any:
        """Execute operation with intelligent retry logic"""
        
        # Create or get existing retry session
        session = self._get_or_create_session(operation_id, context, max_retries)
        
        while True:
            attempt_number = len(session.attempts) + 1
            
            # Check circuit breaker
            circuit_breaker = self._get_circuit_breaker(operation_id, context)
            if circuit_breaker and not circuit_breaker.can_execute():
                raise VidTaniumException(
                    message=f"Circuit breaker is OPEN for {operation_id}",
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.HIGH,
                    context=context,
                    is_retryable=False
                )
            
            # Create attempt record
            attempt = RetryAttempt(
                attempt_number=attempt_number,
                timestamp=time.time()
            )
            
            try:
                # Execute the operation
                start_time = time.time()
                result = operation()
                attempt.duration = time.time() - start_time
                attempt.success = True
                
                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success()
                
                session.attempts.append(attempt)
                self._cleanup_session(operation_id)
                
                logger.debug(f"Operation {operation_id} succeeded on attempt {attempt_number}")
                return result
                
            except Exception as e:
                attempt.duration = time.time() - start_time
                
                # Convert to VidTaniumException
                if self.error_handler:
                    enhanced_exception = self.error_handler.handle_exception(
                        e, context, operation_id
                    )
                else:
                    # Create a basic VidTaniumException wrapper
                    from .exceptions import VidTaniumException, ErrorCategory, ErrorSeverity
                    enhanced_exception = VidTaniumException(
                        message=str(e),
                        category=ErrorCategory.SYSTEM,
                        severity=ErrorSeverity.HIGH,
                        original_exception=e
                    )
                attempt.exception = enhanced_exception
                session.attempts.append(attempt)
                
                # Record failure in circuit breaker
                if circuit_breaker:
                    circuit_breaker.record_failure()
                
                # Check if we should retry
                if not self._should_retry(enhanced_exception, session):
                    self._cleanup_session(operation_id)
                    logger.error(f"Operation {operation_id} failed permanently after {attempt_number} attempts")
                    raise enhanced_exception
                
                # Calculate and apply retry delay
                if self.error_handler:
                    delay = self.error_handler.get_retry_delay(enhanced_exception, attempt_number - 1)
                else:
                    delay = min(2 ** (attempt_number - 1), 60)  # Exponential backoff with max 60s
                session.total_delay += delay
                
                logger.warning(
                    f"Operation {operation_id} failed on attempt {attempt_number}, "
                    f"retrying in {delay:.2f}s: {enhanced_exception.message}"
                )
                
                time.sleep(delay)
    
    async def execute_with_retry_async(
        self,
        operation: Callable[[], Any],
        operation_id: str,
        context: Optional[ErrorContext] = None,
        max_retries: Optional[int] = None
    ) -> Any:
        """Async version of execute_with_retry"""
        
        session = self._get_or_create_session(operation_id, context, max_retries)
        
        while True:
            attempt_number = len(session.attempts) + 1
            
            # Check circuit breaker
            circuit_breaker = self._get_circuit_breaker(operation_id, context)
            if circuit_breaker and not circuit_breaker.can_execute():
                raise VidTaniumException(
                    message=f"Circuit breaker is OPEN for {operation_id}",
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.HIGH,
                    context=context,
                    is_retryable=False
                )
            
            attempt = RetryAttempt(
                attempt_number=attempt_number,
                timestamp=time.time()
            )
            
            try:
                start_time = time.time()
                if asyncio.iscoroutinefunction(operation):
                    result = await operation()
                else:
                    result = operation()
                
                attempt.duration = time.time() - start_time
                attempt.success = True
                
                if circuit_breaker:
                    circuit_breaker.record_success()
                
                session.attempts.append(attempt)
                self._cleanup_session(operation_id)
                
                return result
                
            except Exception as e:
                attempt.duration = time.time() - start_time
                
                if self.error_handler:
                    enhanced_exception = self.error_handler.handle_exception(
                        e, context, operation_id
                    )
                else:
                    # Create a basic VidTaniumException wrapper
                    from .exceptions import VidTaniumException, ErrorCategory, ErrorSeverity
                    enhanced_exception = VidTaniumException(
                        message=str(e),
                        category=ErrorCategory.SYSTEM,
                        severity=ErrorSeverity.HIGH,
                        original_exception=e
                    )
                attempt.exception = enhanced_exception
                session.attempts.append(attempt)
                
                if circuit_breaker:
                    circuit_breaker.record_failure()
                
                if not self._should_retry(enhanced_exception, session):
                    self._cleanup_session(operation_id)
                    raise enhanced_exception
                
                if self.error_handler:
                    delay = self.error_handler.get_retry_delay(enhanced_exception, attempt_number - 1)
                else:
                    delay = min(2 ** (attempt_number - 1), 60)  # Exponential backoff with max 60s
                session.total_delay += delay
                
                await asyncio.sleep(delay)
    
    def _get_or_create_session(
        self,
        operation_id: str,
        context: Optional[ErrorContext],
        max_retries: Optional[int]
    ) -> RetrySession:
        """Get existing or create new retry session"""
        with self.lock:
            if operation_id not in self.active_sessions:
                self.active_sessions[operation_id] = RetrySession(
                    operation_id=operation_id,
                    max_retries=max_retries or 3,
                    context=context
                )
            return self.active_sessions[operation_id]
    
    def _get_circuit_breaker(
        self,
        operation_id: str,
        context: Optional[ErrorContext]
    ) -> Optional[CircuitBreaker]:
        """Get or create circuit breaker for operation"""
        if not context:
            return None
        
        # Use task_id or operation_id as circuit breaker key
        cb_key = context.task_id or operation_id
        
        with self.lock:
            if cb_key not in self.circuit_breakers:
                # Determine config based on operation type
                config = self.circuit_configs.get(
                    ErrorCategory.NETWORK,  # Default
                    CircuitBreakerConfig()
                )
                
                self.circuit_breakers[cb_key] = CircuitBreaker(cb_key, config)
            
            return self.circuit_breakers[cb_key]
    
    def _should_retry(self, exception: VidTaniumException, session: RetrySession) -> bool:
        """Determine if operation should be retried"""
        if len(session.attempts) >= session.max_retries:
            return False
        
        if self.error_handler:
            return self.error_handler.should_retry(exception, len(session.attempts))
        else:
            # Default retry logic: retry on network/temporary errors
            return hasattr(exception, 'is_retryable') and exception.is_retryable
    
    def _cleanup_session(self, operation_id: str):
        """Clean up completed retry session"""
        with self.lock:
            if operation_id in self.active_sessions:
                del self.active_sessions[operation_id]
    
    def get_session_stats(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a retry session"""
        with self.lock:
            session = self.active_sessions.get(operation_id)
            if not session:
                return None
            
            return {
                "operation_id": session.operation_id,
                "start_time": session.start_time,
                "attempts": len(session.attempts),
                "max_retries": session.max_retries,
                "total_delay": session.total_delay,
                "success_rate": sum(1 for a in session.attempts if a.success) / len(session.attempts),
                "average_duration": sum(a.duration for a in session.attempts) / len(session.attempts)
            }
    
    def get_all_circuit_breaker_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        with self.lock:
            return {
                name: cb.get_stats()
                for name, cb in self.circuit_breakers.items()
            }


# Global retry manager instance
retry_manager = IntelligentRetryManager(error_handler=None)  # Will be initialized later

import pytest
import time
import asyncio
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, List, Optional, Any, Callable
from threading import Lock

from src.core.retry_manager import (
    IntelligentRetryManager, RetryAttempt, RetrySession, CircuitBreaker,
    CircuitBreakerConfig, CircuitState, retry_manager
)
from src.core.exceptions import (
    VidTaniumException, ErrorCategory, ErrorSeverity, ErrorContext,
    NetworkException, FilesystemException, EncryptionException
)
from src.core.error_handler import EnhancedErrorHandler


class TestCircuitState:
    """Test suite for CircuitState enum."""

    def test_state_values(self) -> None:
        """Test enum values."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestRetryAttempt:
    """Test suite for RetryAttempt dataclass."""

    def test_attempt_creation(self) -> None:
        """Test RetryAttempt creation with all fields."""
        exception = NetworkException("Network error")
        attempt = RetryAttempt(
            attempt_number=2,
            timestamp=1234567890.0,
            exception=exception,
            success=False,
            duration=5.5
        )
        
        assert attempt.attempt_number == 2
        assert attempt.timestamp == 1234567890.0
        assert attempt.exception == exception
        assert attempt.success is False
        assert attempt.duration == 5.5

    def test_attempt_defaults(self) -> None:
        """Test RetryAttempt with default values."""
        attempt = RetryAttempt(
            attempt_number=1,
            timestamp=1234567890.0
        )
        
        assert attempt.exception is None
        assert attempt.success is False
        assert attempt.duration == 0.0


class TestRetrySession:
    """Test suite for RetrySession dataclass."""

    def test_session_creation(self) -> None:
        """Test RetrySession creation with all fields."""
        context = ErrorContext(task_id="test_task")
        attempts = [RetryAttempt(1, time.time())]
        
        session = RetrySession(
            operation_id="test_operation",
            start_time=1234567890.0,
            attempts=attempts,
            max_retries=5,
            total_delay=10.0,
            context=context
        )
        
        assert session.operation_id == "test_operation"
        assert session.start_time == 1234567890.0
        assert session.attempts == attempts
        assert session.max_retries == 5
        assert session.total_delay == 10.0
        assert session.context == context

    def test_session_defaults(self) -> None:
        """Test RetrySession with default values."""
        session = RetrySession(operation_id="test_operation")
        
        assert session.operation_id == "test_operation"
        assert session.start_time > 0
        assert session.attempts == []
        assert session.max_retries == 3
        assert session.total_delay == 0.0
        assert session.context is None


class TestCircuitBreakerConfig:
    """Test suite for CircuitBreakerConfig dataclass."""

    def test_config_creation(self) -> None:
        """Test CircuitBreakerConfig creation with all fields."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120.0,
            success_threshold=5,
            monitoring_window=600.0
        )
        
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 120.0
        assert config.success_threshold == 5
        assert config.monitoring_window == 600.0

    def test_config_defaults(self) -> None:
        """Test CircuitBreakerConfig with default values."""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.success_threshold == 3
        assert config.monitoring_window == 300.0


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=10.0,
            success_threshold=2
        )
        self.breaker = CircuitBreaker("test_breaker", self.config)

    def test_initialization(self) -> None:
        """Test CircuitBreaker initialization."""
        assert self.breaker.name == "test_breaker"
        assert self.breaker.config == self.config
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0
        assert self.breaker.success_count == 0
        assert self.breaker.last_failure_time == 0.0
        assert isinstance(self.breaker.recent_attempts, list)
        assert isinstance(self.breaker.lock, Lock)

    def test_can_execute_closed_state(self) -> None:
        """Test can_execute in CLOSED state."""
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.can_execute() is True

    def test_can_execute_open_state_within_timeout(self) -> None:
        """Test can_execute in OPEN state within recovery timeout."""
        # Force to OPEN state
        self.breaker.state = CircuitState.OPEN
        self.breaker.last_failure_time = time.time()
        
        assert self.breaker.can_execute() is False

    def test_can_execute_open_state_after_timeout(self) -> None:
        """Test can_execute in OPEN state after recovery timeout."""
        # Force to OPEN state with old failure time
        self.breaker.state = CircuitState.OPEN
        self.breaker.last_failure_time = time.time() - 15.0  # 15 seconds ago
        
        result = self.breaker.can_execute()
        
        assert result is True
        assert self.breaker.state == CircuitState.HALF_OPEN
        assert self.breaker.success_count == 0

    def test_can_execute_half_open_state(self) -> None:
        """Test can_execute in HALF_OPEN state."""
        self.breaker.state = CircuitState.HALF_OPEN
        assert self.breaker.can_execute() is True

    def test_record_success_closed_state(self) -> None:
        """Test record_success in CLOSED state."""
        self.breaker.record_success()
        
        assert self.breaker.success_count == 1
        assert self.breaker.state == CircuitState.CLOSED
        assert len(self.breaker.recent_attempts) == 1
        assert self.breaker.recent_attempts[0][1] is True  # Success flag

    def test_record_success_half_open_to_closed(self) -> None:
        """Test record_success transitioning from HALF_OPEN to CLOSED."""
        self.breaker.state = CircuitState.HALF_OPEN
        
        # Record enough successes to close circuit
        for _ in range(self.config.success_threshold):
            self.breaker.record_success()
        
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0

    def test_record_failure_closed_state(self) -> None:
        """Test record_failure in CLOSED state."""
        self.breaker.record_failure()
        
        assert self.breaker.failure_count == 1
        assert self.breaker.last_failure_time > 0
        assert self.breaker.state == CircuitState.CLOSED
        assert len(self.breaker.recent_attempts) == 1
        assert self.breaker.recent_attempts[0][1] is False  # Failure flag

    def test_record_failure_closed_to_open(self) -> None:
        """Test record_failure transitioning from CLOSED to OPEN."""
        # Record enough failures to open circuit
        for _ in range(self.config.failure_threshold):
            self.breaker.record_failure()
        
        assert self.breaker.state == CircuitState.OPEN
        assert self.breaker.failure_count == self.config.failure_threshold

    def test_record_failure_half_open_to_open(self) -> None:
        """Test record_failure transitioning from HALF_OPEN to OPEN."""
        self.breaker.state = CircuitState.HALF_OPEN
        
        self.breaker.record_failure()
        
        assert self.breaker.state == CircuitState.OPEN

    def test_get_stats(self) -> None:
        """Test get_stats method."""
        # Record some attempts
        self.breaker.record_success()
        self.breaker.record_failure()
        self.breaker.record_success()
        
        stats = self.breaker.get_stats()
        
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 1
        assert stats["success_count"] == 2
        assert stats["total_attempts_recent"] == 3
        assert stats["failure_rate"] == 1/3
        assert stats["last_failure_time"] > 0

    def test_cleanup_old_attempts(self) -> None:
        """Test cleanup of old attempts."""
        # Add old attempt (beyond monitoring window)
        old_time = time.time() - 400  # 400 seconds ago
        self.breaker.recent_attempts.append((old_time, True))
        
        # Add recent attempt
        self.breaker.record_success()
        
        # Get stats should trigger cleanup
        stats = self.breaker.get_stats()
        
        # Should only have recent attempt
        assert stats["total_attempts_recent"] == 1


class TestIntelligentRetryManager:
    """Test suite for IntelligentRetryManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.error_handler = Mock(spec=EnhancedErrorHandler)
        self.manager = IntelligentRetryManager(error_handler=self.error_handler)

    def test_initialization(self) -> None:
        """Test IntelligentRetryManager initialization."""
        assert self.manager.error_handler == self.error_handler
        assert isinstance(self.manager.active_sessions, dict)
        assert isinstance(self.manager.circuit_breakers, dict)
        assert isinstance(self.manager.lock, Lock)
        assert isinstance(self.manager.circuit_configs, dict)
        
        # Check default circuit configs
        assert ErrorCategory.NETWORK in self.manager.circuit_configs
        assert ErrorCategory.FILESYSTEM in self.manager.circuit_configs
        assert ErrorCategory.ENCRYPTION in self.manager.circuit_configs

    def test_initialization_without_error_handler(self) -> None:
        """Test initialization without error handler."""
        manager = IntelligentRetryManager()
        assert manager.error_handler is None

    def test_execute_with_retry_success(self) -> None:
        """Test successful operation execution."""
        operation = Mock(return_value="success")
        
        result = self.manager.execute_with_retry(
            operation=operation,
            operation_id="test_op",
            context=ErrorContext(task_id="test_task"),
            max_retries=3
        )
        
        assert result == "success"
        operation.assert_called_once()
        assert "test_op" not in self.manager.active_sessions  # Should be cleaned up

    def test_execute_with_retry_failure_then_success(self) -> None:
        """Test operation that fails then succeeds."""
        operation = Mock(side_effect=[Exception("First failure"), "success"])
        self.error_handler.handle_exception.return_value = NetworkException("Network error")
        self.error_handler.should_retry.return_value = True
        self.error_handler.get_retry_delay.return_value = 0.1
        
        result = self.manager.execute_with_retry(
            operation=operation,
            operation_id="test_op",
            max_retries=3
        )
        
        assert result == "success"
        assert operation.call_count == 2
        self.error_handler.handle_exception.assert_called_once()

    def test_execute_with_retry_permanent_failure(self) -> None:
        """Test operation that fails permanently."""
        operation = Mock(side_effect=Exception("Permanent failure"))
        enhanced_exception = NetworkException("Network error")
        enhanced_exception.is_retryable = False
        
        self.error_handler.handle_exception.return_value = enhanced_exception
        self.error_handler.should_retry.return_value = False
        
        with pytest.raises(NetworkException):
            self.manager.execute_with_retry(
                operation=operation,
                operation_id="test_op",
                max_retries=3
            )
        
        operation.assert_called_once()

    def test_execute_with_retry_max_retries_exceeded(self) -> None:
        """Test operation that exceeds max retries."""
        operation = Mock(side_effect=Exception("Always fails"))
        enhanced_exception = NetworkException("Network error")
        enhanced_exception.is_retryable = True
        
        self.error_handler.handle_exception.return_value = enhanced_exception
        self.error_handler.should_retry.side_effect = [True, True, False]  # Fail after 3 attempts
        self.error_handler.get_retry_delay.return_value = 0.1
        
        with pytest.raises(NetworkException):
            self.manager.execute_with_retry(
                operation=operation,
                operation_id="test_op",
                max_retries=2
            )
        
        assert operation.call_count == 3  # Initial + 2 retries

    def test_execute_with_retry_circuit_breaker_open(self) -> None:
        """Test operation blocked by open circuit breaker."""
        # Create and configure circuit breaker
        context = ErrorContext(url="https://example.com")
        circuit_breaker = self.manager._get_circuit_breaker("test_op", context)
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.last_failure_time = time.time()
        
        operation = Mock(return_value="success")
        
        with pytest.raises(VidTaniumException) as exc_info:
            self.manager.execute_with_retry(
                operation=operation,
                operation_id="test_op",
                context=context
            )
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
        operation.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_retry_async_success(self) -> None:
        """Test successful async operation execution."""
        async def async_operation() -> None:
            return "async_success"
        
        result = await self.manager.execute_with_retry_async(
            operation=async_operation,
            operation_id="test_async_op"
        )
        
        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_async_failure(self) -> None:
        """Test async operation that fails then succeeds."""
        call_count = 0
        
        async def async_operation() -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First failure")
            return "async_success"
        
        self.error_handler.handle_exception.return_value = NetworkException("Network error")
        self.error_handler.should_retry.return_value = True
        self.error_handler.get_retry_delay.return_value = 0.1
        
        result = await self.manager.execute_with_retry_async(
            operation=async_operation,
            operation_id="test_async_op"
        )
        
        assert result == "async_success"
        assert call_count == 2

    def test_get_or_create_session_new(self) -> None:
        """Test creating new retry session."""
        context = ErrorContext(task_id="test_task")
        
        session = self.manager._get_or_create_session("new_op", context, 5)
        
        assert session.operation_id == "new_op"
        assert session.context == context
        assert session.max_retries == 5
        assert "new_op" in self.manager.active_sessions

    def test_get_or_create_session_existing(self) -> None:
        """Test getting existing retry session."""
        context = ErrorContext(task_id="test_task")
        
        # Create first session
        session1 = self.manager._get_or_create_session("existing_op", context, 3)
        
        # Get same session
        session2 = self.manager._get_or_create_session("existing_op", context, 5)
        
        assert session1 is session2
        assert session2.max_retries == 3  # Should keep original max_retries

    def test_get_circuit_breaker_new(self) -> None:
        """Test creating new circuit breaker."""
        context = ErrorContext(url="https://example.com")
        
        breaker = self.manager._get_circuit_breaker("test_op", context)
        
        assert breaker is not None
        assert breaker.name == "test_op"
        assert "test_op" in self.manager.circuit_breakers

    def test_get_circuit_breaker_existing(self) -> None:
        """Test getting existing circuit breaker."""
        context = ErrorContext(url="https://example.com")
        
        # Create first breaker
        breaker1 = self.manager._get_circuit_breaker("existing_op", context)
        
        # Get same breaker
        breaker2 = self.manager._get_circuit_breaker("existing_op", context)
        
        assert breaker1 is breaker2

    def test_should_retry_with_error_handler(self) -> None:
        """Test retry decision with error handler."""
        exception = NetworkException("Network error")
        session = RetrySession("test_op", max_retries=3)
        session.attempts = [RetryAttempt(1, time.time())]
        
        self.error_handler.should_retry.return_value = True
        
        result = self.manager._should_retry(exception, session)
        
        assert result is True
        self.error_handler.should_retry.assert_called_once_with(exception, 1)

    def test_should_retry_without_error_handler(self) -> None:
        """Test retry decision without error handler."""
        manager = IntelligentRetryManager()  # No error handler
        
        exception = NetworkException("Network error")
        exception.is_retryable = True
        session = RetrySession("test_op", max_retries=3)
        session.attempts = [RetryAttempt(1, time.time())]
        
        result = manager._should_retry(exception, session)
        
        assert result is True

    def test_should_retry_max_attempts_exceeded(self) -> None:
        """Test retry decision when max attempts exceeded."""
        exception = NetworkException("Network error")
        session = RetrySession("test_op", max_retries=2)
        session.attempts = [
            RetryAttempt(1, time.time()),
            RetryAttempt(2, time.time())
        ]
        
        result = self.manager._should_retry(exception, session)
        
        assert result is False

    def test_cleanup_session(self) -> None:
        """Test session cleanup."""
        session = RetrySession("test_op")
        self.manager.active_sessions["test_op"] = session
        
        self.manager._cleanup_session("test_op")
        
        assert "test_op" not in self.manager.active_sessions

    def test_get_session_stats(self) -> None:
        """Test getting session statistics."""
        session = RetrySession("test_op", max_retries=5, start_time=1234567890.0)
        session.attempts = [
            RetryAttempt(1, time.time(), success=False, duration=1.0),
            RetryAttempt(2, time.time(), success=True, duration=2.0)
        ]
        session.total_delay = 5.0
        
        self.manager.active_sessions["test_op"] = session
        
        stats = self.manager.get_session_stats("test_op")
        
        assert stats["operation_id"] == "test_op"
        assert stats["start_time"] == 1234567890.0
        assert stats["attempts"] == 2
        assert stats["max_retries"] == 5
        assert stats["total_delay"] == 5.0
        assert stats["success_rate"] == 0.5
        assert stats["average_duration"] == 1.5

    def test_get_session_stats_nonexistent(self) -> None:
        """Test getting stats for nonexistent session."""
        stats = self.manager.get_session_stats("nonexistent")
        assert stats is None

    def test_get_all_circuit_breaker_stats(self) -> None:
        """Test getting all circuit breaker statistics."""
        # Create some circuit breakers
        context1 = ErrorContext(url="https://example1.com")
        context2 = ErrorContext(url="https://example2.com")
        
        breaker1 = self.manager._get_circuit_breaker("op1", context1)
        breaker2 = self.manager._get_circuit_breaker("op2", context2)
        
        # Record some activity
        breaker1.record_success()
        breaker2.record_failure()
        
        stats = self.manager.get_all_circuit_breaker_stats()
        
        assert "op1" in stats
        assert "op2" in stats
        assert stats["op1"]["success_count"] == 1
        assert stats["op2"]["failure_count"] == 1

    def test_global_retry_manager_instance(self) -> None:
        """Test global retry manager instance."""
        assert retry_manager is not None
        assert isinstance(retry_manager, IntelligentRetryManager)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

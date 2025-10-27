"""
Tests for circuit breaker management
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.core.circuit_breaker import (
    CircuitBreakerManager, CircuitState, CircuitBreaker, CircuitBreakerConfig,
    RequestResult, CircuitBreakerMetrics, circuit_breaker_manager
)


class TestCircuitState:
    """Test CircuitState enum"""
    
    def test_circuit_states(self) -> None:
        """Test CircuitState enum values"""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig dataclass"""
    
    def test_default_config(self) -> None:
        """Test default CircuitBreakerConfig values"""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 3
        assert config.timeout == 60.0
        assert config.rolling_window_size == 20
        assert config.min_requests == 10
        assert config.failure_rate_threshold == 0.5
    
    def test_custom_config(self) -> None:
        """Test custom CircuitBreakerConfig"""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout=120.0
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 5
        assert config.timeout == 120.0


class TestRequestResult:
    """Test RequestResult dataclass"""
    
    def test_success_result(self) -> None:
        """Test successful request result"""
        result = RequestResult(
            timestamp=time.time(),
            success=True,
            response_time=1.5
        )
        assert result.success is True
        assert result.response_time == 1.5
        assert result.error_message == ""
    
    def test_failure_result(self) -> None:
        """Test failed request result"""
        result = RequestResult(
            timestamp=time.time(),
            success=False,
            error_message="Connection timeout"
        )
        assert result.success is False
        assert result.error_message == "Connection timeout"


class TestCircuitBreakerMetrics:
    """Test CircuitBreakerMetrics class"""
    
    def test_initialization(self) -> None:
        """Test CircuitBreakerMetrics initialization"""
        metrics = CircuitBreakerMetrics(window_size=20)
        assert metrics.window_size == 20
        assert metrics.total_requests == 0
        assert metrics.total_failures == 0
        assert metrics.total_successes == 0
        assert metrics.consecutive_failures == 0
        assert metrics.consecutive_successes == 0
    
    def test_record_success(self) -> None:
        """Test recording successful request"""
        metrics = CircuitBreakerMetrics()
        result = RequestResult(timestamp=time.time(), success=True, response_time=1.0)
        
        metrics.record_request(result)
        
        assert metrics.total_requests == 1
        assert metrics.total_successes == 1
        assert metrics.total_failures == 0
        assert metrics.consecutive_successes == 1
        assert metrics.consecutive_failures == 0
    
    def test_record_failure(self) -> None:
        """Test recording failed request"""
        metrics = CircuitBreakerMetrics()
        result = RequestResult(timestamp=time.time(), success=False)
        
        metrics.record_request(result)
        
        assert metrics.total_requests == 1
        assert metrics.total_failures == 1
        assert metrics.total_successes == 0
        assert metrics.consecutive_failures == 1
        assert metrics.consecutive_successes == 0
    
    def test_get_failure_rate(self) -> None:
        """Test failure rate calculation"""
        metrics = CircuitBreakerMetrics()
        
        # Add 3 successes and 2 failures
        for _ in range(3):
            metrics.record_request(RequestResult(timestamp=time.time(), success=True))
        for _ in range(2):
            metrics.record_request(RequestResult(timestamp=time.time(), success=False))
        
        assert metrics.get_failure_rate() == 0.4  # 2/5


class TestCircuitBreaker:
    """Test CircuitBreaker class"""
    
    def test_initialization(self) -> None:
        """Test CircuitBreaker initialization"""
        config = CircuitBreakerConfig(failure_threshold=5, success_threshold=3)
        cb = CircuitBreaker("example.com", config)
        
        assert cb.host == "example.com"
        assert cb.config.failure_threshold == 5
        assert cb.state == CircuitState.CLOSED
        assert cb.metrics.total_requests == 0
    
    def test_can_execute_closed_state(self) -> None:
        """Test can_execute in CLOSED state"""
        cb = CircuitBreaker("example.com")
        assert cb.can_execute() is True
    
    def test_can_execute_open_state_within_timeout(self) -> None:
        """Test can_execute in OPEN state within timeout"""
        config = CircuitBreakerConfig(timeout=60.0)
        cb = CircuitBreaker("example.com", config)
        cb.state = CircuitState.OPEN
        cb.state_changed_at = time.time()
        
        assert cb.can_execute() is False
    
    def test_can_execute_open_state_after_timeout(self) -> None:
        """Test can_execute in OPEN state after timeout"""
        config = CircuitBreakerConfig(timeout=1.0)
        cb = CircuitBreaker("example.com", config)
        cb.state = CircuitState.OPEN
        cb.state_changed_at = time.time() - 2.0
        
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_record_success(self) -> None:
        """Test recording successful request"""
        cb = CircuitBreaker("example.com")
        cb.record_success(1.5)
        
        assert cb.metrics.total_successes == 1
        assert cb.metrics.consecutive_successes == 1
        assert cb.state == CircuitState.CLOSED
    
    def test_record_failure_below_threshold(self) -> None:
        """Test recording failures below threshold"""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker("example.com", config)
        
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        
        assert cb.metrics.consecutive_failures == 2
        assert cb.state == CircuitState.CLOSED
    
    def test_record_failure_at_threshold(self) -> None:
        """Test recording failures at threshold"""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("example.com", config)
        
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        cb.record_failure("Error 3")
        
        assert cb.metrics.consecutive_failures == 3
        assert cb.state == CircuitState.OPEN
    
    def test_force_open(self) -> None:
        """Test forcing circuit breaker open"""
        cb = CircuitBreaker("example.com")
        cb.force_open()
        
        assert cb.state == CircuitState.OPEN
    
    def test_reset(self) -> None:
        """Test resetting circuit breaker"""
        cb = CircuitBreaker("example.com")
        cb.record_failure("Error")
        cb.state = CircuitState.OPEN
        
        cb.reset()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.metrics.total_requests == 0


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager class"""
    
    def test_initialization(self) -> None:
        """Test CircuitBreakerManager initialization"""
        manager = CircuitBreakerManager()
        assert manager.circuit_breakers == {}
        assert manager.monitoring_active is False
    
    def test_get_circuit_breaker_new_host(self) -> None:
        """Test getting circuit breaker for new host"""
        manager = CircuitBreakerManager()
        cb = manager.get_circuit_breaker("example.com")
        
        assert isinstance(cb, CircuitBreaker)
        assert cb.host == "example.com"
        assert "example.com" in manager.circuit_breakers
    
    def test_get_circuit_breaker_existing_host(self) -> None:
        """Test getting circuit breaker for existing host"""
        manager = CircuitBreakerManager()
        cb1 = manager.get_circuit_breaker("example.com")
        cb2 = manager.get_circuit_breaker("example.com")
        
        assert cb1 is cb2
    
    def test_can_execute(self) -> None:
        """Test can_execute method"""
        manager = CircuitBreakerManager()
        assert manager.can_execute("example.com") is True
    
    def test_record_success(self) -> None:
        """Test recording success"""
        manager = CircuitBreakerManager()
        manager.record_success("example.com", 1.5)
        
        cb = manager.get_circuit_breaker("example.com")
        assert cb.metrics.total_successes == 1
    
    def test_record_failure(self) -> None:
        """Test recording failure"""
        manager = CircuitBreakerManager()
        manager.record_failure("example.com", "Connection error")
        
        cb = manager.get_circuit_breaker("example.com")
        assert cb.metrics.total_failures == 1
    
    def test_get_all_stats(self) -> None:
        """Test getting statistics"""
        manager = CircuitBreakerManager()
        manager.record_success("example.com", 1.0)
        manager.record_success("test.com", 2.0)

        stats = manager.get_all_stats()
        assert stats["total_circuit_breakers"] == 2
        assert "circuit_breakers" in stats
        assert "state_summary" in stats


class TestGlobalCircuitBreakerManager:
    """Test global circuit breaker manager instance"""
    
    def test_global_instance_exists(self) -> None:
        """Test that global instance exists"""
        assert circuit_breaker_manager is not None
        assert isinstance(circuit_breaker_manager, CircuitBreakerManager)
    
    def test_global_instance_functionality(self) -> None:
        """Test basic functionality of global instance"""
        host = "global-test.example.com"
        
        assert circuit_breaker_manager.can_execute(host) is True
        circuit_breaker_manager.record_success(host, 1.0)
        
        cb = circuit_breaker_manager.get_circuit_breaker(host)
        assert cb.metrics.total_successes == 1


if __name__ == "__main__":
    pytest.main([__file__])


"""
Tests for circuit breaker management
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.core.circuit_breaker import (
    CircuitBreakerManager, CircuitBreakerState, CircuitBreaker, 
    circuit_breaker_manager
)


class TestCircuitBreakerState:
    """Test CircuitBreakerState enum"""
    
    def test_circuit_breaker_states(self) -> None:
        """Test CircuitBreakerState enum values"""
        assert CircuitBreakerState.CLOSED.value == "closed"
        assert CircuitBreakerState.OPEN.value == "open"
        assert CircuitBreakerState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    """Test CircuitBreaker class"""
    
    def test_initialization(self) -> None:
        """Test CircuitBreaker initialization"""
        host = "example.com"
        failure_threshold = 5
        recovery_timeout = 60.0
        success_threshold = 3
        
        cb = CircuitBreaker(host, failure_threshold, recovery_timeout, success_threshold)
        
        assert cb.host == host
        assert cb.failure_threshold == failure_threshold
        assert cb.recovery_timeout == recovery_timeout
        assert cb.success_threshold == success_threshold
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.last_failure_time == 0.0
        assert cb.last_success_time == 0.0
    
    def test_can_execute_closed_state(self) -> None:
        """Test can_execute in CLOSED state"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        
        assert cb.can_execute() is True
    
    def test_can_execute_open_state_within_timeout(self) -> None:
        """Test can_execute in OPEN state within recovery timeout"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        cb.state = CircuitBreakerState.OPEN
        cb.last_failure_time = time.time()
        
        assert cb.can_execute() is False
    
    def test_can_execute_open_state_after_timeout(self) -> None:
        """Test can_execute in OPEN state after recovery timeout"""
        cb = CircuitBreaker("example.com", 5, 1.0, 3)  # 1 second timeout
        cb.state = CircuitBreakerState.OPEN
        cb.last_failure_time = time.time() - 2.0  # 2 seconds ago
        
        # Should transition to HALF_OPEN
        assert cb.can_execute() is True
        assert cb.state == CircuitBreakerState.HALF_OPEN
    
    def test_can_execute_half_open_state(self) -> None:
        """Test can_execute in HALF_OPEN state"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        cb.state = CircuitBreakerState.HALF_OPEN
        
        assert cb.can_execute() is True
    
    def test_record_success_closed_state(self) -> None:
        """Test recording success in CLOSED state"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        
        cb.record_success(1.5)
        
        assert cb.success_count == 1
        assert cb.failure_count == 0
        assert cb.last_success_time > 0
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_record_success_half_open_state_insufficient(self) -> None:
        """Test recording success in HALF_OPEN state with insufficient successes"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        cb.state = CircuitBreakerState.HALF_OPEN
        
        cb.record_success(1.5)
        cb.record_success(1.2)
        
        assert cb.success_count == 2
        assert cb.state == CircuitBreakerState.HALF_OPEN
    
    def test_record_success_half_open_state_sufficient(self) -> None:
        """Test recording success in HALF_OPEN state with sufficient successes"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        cb.state = CircuitBreakerState.HALF_OPEN
        
        cb.record_success(1.5)
        cb.record_success(1.2)
        cb.record_success(1.8)
        
        assert cb.success_count == 3
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0  # Reset on transition to CLOSED
    
    def test_record_failure_closed_state_below_threshold(self) -> None:
        """Test recording failure in CLOSED state below threshold"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        
        cb.record_failure("Connection error")
        cb.record_failure("Timeout")
        
        assert cb.failure_count == 2
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_record_failure_closed_state_at_threshold(self) -> None:
        """Test recording failure in CLOSED state at threshold"""
        cb = CircuitBreaker("example.com", 3, 60.0, 3)  # Lower threshold for testing
        
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        cb.record_failure("Error 3")
        
        assert cb.failure_count == 3
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.last_failure_time > 0
    
    def test_record_failure_half_open_state(self) -> None:
        """Test recording failure in HALF_OPEN state"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        cb.state = CircuitBreakerState.HALF_OPEN
        
        cb.record_failure("Connection error")
        
        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.last_failure_time > 0
    
    def test_get_stats(self) -> None:
        """Test getting circuit breaker statistics"""
        cb = CircuitBreaker("example.com", 5, 60.0, 3)
        cb.record_success(1.5)
        cb.record_failure("Error")
        
        stats = cb.get_stats()
        
        assert stats["host"] == "example.com"
        assert stats["state"] == CircuitBreakerState.CLOSED.value
        assert stats["failure_count"] == 1
        assert stats["success_count"] == 1
        assert stats["failure_threshold"] == 5
        assert stats["success_threshold"] == 3
        assert "last_failure_time" in stats
        assert "last_success_time" in stats


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager class"""
    
    @pytest.fixture
    def cb_manager(self) -> None:
        """Create a fresh CircuitBreakerManager for testing"""
        manager = CircuitBreakerManager()
        yield manager
        # Cleanup
        manager.stop_health_monitoring()
    
    def test_initialization(self, cb_manager) -> None:
        """Test CircuitBreakerManager initialization"""
        assert cb_manager.circuit_breakers == {}
        assert cb_manager.default_failure_threshold == 5
        assert cb_manager.default_recovery_timeout == 60.0
        assert cb_manager.default_success_threshold == 3
        assert cb_manager.health_check_interval == 30.0
        assert cb_manager.monitoring_active is False
        assert cb_manager.health_thread is None
    
    def test_get_circuit_breaker_new_host(self, cb_manager) -> None:
        """Test getting circuit breaker for new host"""
        url = "https://example.com/test"
        
        cb = cb_manager._get_circuit_breaker(url)
        
        assert isinstance(cb, CircuitBreaker)
        assert cb.host == "example.com"
        assert "example.com" in cb_manager.circuit_breakers
    
    def test_get_circuit_breaker_existing_host(self, cb_manager) -> None:
        """Test getting circuit breaker for existing host"""
        url = "https://example.com/test"
        
        cb1 = cb_manager._get_circuit_breaker(url)
        cb2 = cb_manager._get_circuit_breaker(url)
        
        # Should return the same instance
        assert cb1 is cb2
    
    def test_can_execute_new_host(self, cb_manager) -> None:
        """Test can_execute for new host"""
        url = "https://example.com/test"
        
        # Should allow execution for new host
        assert cb_manager.can_execute(url) is True
    
    def test_can_execute_existing_host(self, cb_manager) -> None:
        """Test can_execute for existing host"""
        url = "https://example.com/test"
        
        # Create circuit breaker and set to OPEN
        cb = cb_manager._get_circuit_breaker(url)
        cb.state = CircuitBreakerState.OPEN
        cb.last_failure_time = time.time()
        
        assert cb_manager.can_execute(url) is False
    
    def test_record_success(self, cb_manager) -> None:
        """Test recording success"""
        url = "https://example.com/test"
        response_time = 1.5
        
        cb_manager.record_success(url, response_time)
        
        cb = cb_manager.circuit_breakers["example.com"]
        assert cb.success_count == 1
        assert cb.last_success_time > 0
    
    def test_record_failure(self, cb_manager) -> None:
        """Test recording failure"""
        url = "https://example.com/test"
        error_message = "Connection timeout"
        
        cb_manager.record_failure(url, error_message)
        
        cb = cb_manager.circuit_breakers["example.com"]
        assert cb.failure_count == 1
        assert cb.last_failure_time > 0
    
    def test_configure_circuit_breaker(self, cb_manager) -> None:
        """Test configuring circuit breaker"""
        host = "example.com"
        failure_threshold = 10
        recovery_timeout = 120.0
        success_threshold = 5
        
        cb_manager.configure_circuit_breaker(
            host, failure_threshold, recovery_timeout, success_threshold
        )
        
        # Create circuit breaker for this host
        url = f"https://{host}/test"
        cb = cb_manager._get_circuit_breaker(url)
        
        assert cb.failure_threshold == failure_threshold
        assert cb.recovery_timeout == recovery_timeout
        assert cb.success_threshold == success_threshold
    
    def test_get_all_stats(self, cb_manager) -> None:
        """Test getting all circuit breaker statistics"""
        # Initially empty
        stats = cb_manager.get_all_stats()
        assert stats["total_circuit_breakers"] == 0
        assert stats["state_summary"]["closed"] == 0
        assert stats["state_summary"]["open"] == 0
        assert stats["state_summary"]["half_open"] == 0
        
        # Add some circuit breakers
        cb_manager.record_success("https://example.com/test", 1.5)
        cb_manager.record_failure("https://test.com/path", "Error")
        
        stats = cb_manager.get_all_stats()
        assert stats["total_circuit_breakers"] == 2
        assert "circuit_breakers" in stats
        assert "example.com" in stats["circuit_breakers"]
        assert "test.com" in stats["circuit_breakers"]
    
    def test_start_stop_health_monitoring(self, cb_manager) -> None:
        """Test starting and stopping health monitoring"""
        assert cb_manager.monitoring_active is False
        
        cb_manager.start_health_monitoring()
        assert cb_manager.monitoring_active is True
        assert cb_manager.health_thread is not None
        
        cb_manager.stop_health_monitoring()
        assert cb_manager.monitoring_active is False
    
    def test_health_check_cycle(self, cb_manager) -> None:
        """Test health check cycle"""
        # Create some circuit breakers
        cb_manager.record_success("https://example.com/test", 1.5)
        cb_manager.record_failure("https://test.com/path", "Error")
        
        # Run health check
        cb_manager._health_check_cycle()
        
        # Should complete without errors
        assert len(cb_manager.circuit_breakers) == 2
    
    def test_get_host_from_url(self, cb_manager) -> None:
        """Test extracting host from URL"""
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://subdomain.example.com:8080/path", "subdomain.example.com"),
            ("https://192.168.1.1/test", "192.168.1.1"),
        ]
        
        for url, expected_host in test_cases:
            host = cb_manager._get_host_from_url(url)
            assert host == expected_host
    
    def test_circuit_breaker_state_transitions(self, cb_manager) -> None:
        """Test complete circuit breaker state transitions"""
        url = "https://example.com/test"
        
        # Start in CLOSED state
        assert cb_manager.can_execute(url) is True
        cb = cb_manager.circuit_breakers["example.com"]
        assert cb.state == CircuitBreakerState.CLOSED
        
        # Record failures to trigger OPEN state
        for i in range(5):
            cb_manager.record_failure(url, f"Error {i}")
        
        assert cb.state == CircuitBreakerState.OPEN
        assert cb_manager.can_execute(url) is False
        
        # Mock time to simulate recovery timeout
        cb.recovery_timeout = 0.1  # Very short timeout for testing
        time.sleep(0.2)
        
        # Should transition to HALF_OPEN
        assert cb_manager.can_execute(url) is True
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        # Record successes to transition back to CLOSED
        for i in range(3):
            cb_manager.record_success(url, 1.0)
        
        assert cb.state == CircuitBreakerState.CLOSED


class TestGlobalCircuitBreakerManager:
    """Test global circuit breaker manager instance"""
    
    def test_global_instance_exists(self) -> None:
        """Test that global instance exists and is properly initialized"""
        assert circuit_breaker_manager is not None
        assert isinstance(circuit_breaker_manager, CircuitBreakerManager)
    
    def test_global_instance_functionality(self) -> None:
        """Test basic functionality of global instance"""
        url = "https://global-cb-test.example.com/test"
        
        # Should be able to check execution and record results
        can_execute = circuit_breaker_manager.can_execute(url)
        assert isinstance(can_execute, bool)
        
        circuit_breaker_manager.record_success(url, 1.5)
        circuit_breaker_manager.record_failure(url, "Test error")
        
        # Should have created circuit breaker
        host = circuit_breaker_manager._get_host_from_url(url)
        assert host in circuit_breaker_manager.circuit_breakers


if __name__ == "__main__":
    pytest.main([__file__])

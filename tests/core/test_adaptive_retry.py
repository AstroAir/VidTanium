"""
Tests for adaptive retry strategies
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.core.adaptive_retry import (
    AdaptiveRetryManager, RetryReason, HostRetryMetrics, adaptive_retry_manager
)


class TestRetryReason:
    """Test RetryReason enum"""
    
    def test_retry_reason_values(self) -> None:
        """Test RetryReason enum values"""
        assert RetryReason.NETWORK_TIMEOUT.value == "network_timeout"
        assert RetryReason.CONNECTION_ERROR.value == "connection_error"
        assert RetryReason.SERVER_ERROR.value == "server_error"
        assert RetryReason.RATE_LIMITED.value == "rate_limited"
        assert RetryReason.UNKNOWN_ERROR.value == "unknown_error"


class TestHostRetryMetrics:
    """Test HostRetryMetrics dataclass"""
    
    def test_default_metrics(self) -> None:
        """Test default HostRetryMetrics values"""
        metrics = HostRetryMetrics()
        assert metrics.total_attempts == 0
        assert metrics.successful_attempts == 0
        assert metrics.failed_attempts == 0
        assert metrics.retry_counts == {}
        assert metrics.reason_counts == {}
        assert metrics.total_retry_delay == 0.0
        assert metrics.last_success_time == 0.0
        assert metrics.last_failure_time == 0.0
        assert metrics.consecutive_failures == 0
        assert metrics.last_updated <= time.time()
    
    def test_record_attempt_success(self) -> None:
        """Test recording successful attempt"""
        metrics = HostRetryMetrics()
        
        metrics.record_attempt(
            attempt_number=1,
            reason=RetryReason.UNKNOWN_ERROR,
            success=True,
            response_time=1.5
        )
        
        assert metrics.total_attempts == 1
        assert metrics.successful_attempts == 1
        assert metrics.failed_attempts == 0
        assert metrics.consecutive_failures == 0
        assert metrics.last_success_time > 0
        assert 1 in metrics.retry_counts
        assert metrics.retry_counts[1] == 1
    
    def test_record_attempt_failure(self) -> None:
        """Test recording failed attempt"""
        metrics = HostRetryMetrics()
        
        metrics.record_attempt(
            attempt_number=2,
            reason=RetryReason.NETWORK_TIMEOUT,
            success=False,
            response_time=5.0
        )
        
        assert metrics.total_attempts == 1
        assert metrics.successful_attempts == 0
        assert metrics.failed_attempts == 1
        assert metrics.consecutive_failures == 1
        assert metrics.last_failure_time > 0
        assert RetryReason.NETWORK_TIMEOUT in metrics.reason_counts
        assert metrics.reason_counts[RetryReason.NETWORK_TIMEOUT] == 1
    
    def test_multiple_attempts(self) -> None:
        """Test recording multiple attempts"""
        metrics = HostRetryMetrics()
        
        # First attempt fails
        metrics.record_attempt(1, RetryReason.CONNECTION_ERROR, False, 3.0)
        # Second attempt succeeds
        metrics.record_attempt(2, RetryReason.CONNECTION_ERROR, True, 2.0)
        
        assert metrics.total_attempts == 2
        assert metrics.successful_attempts == 1
        assert metrics.failed_attempts == 1
        assert metrics.consecutive_failures == 0  # Reset on success
    
    def test_get_success_rate(self) -> None:
        """Test success rate calculation"""
        metrics = HostRetryMetrics()
        
        # No attempts
        assert metrics.get_success_rate() == 1.0
        
        # With attempts
        metrics.record_attempt(1, RetryReason.UNKNOWN_ERROR, True, 1.0)
        metrics.record_attempt(1, RetryReason.UNKNOWN_ERROR, True, 1.0)
        metrics.record_attempt(1, RetryReason.UNKNOWN_ERROR, False, 1.0)
        
        assert metrics.get_success_rate() == 2.0 / 3.0
    
    def test_get_average_retry_delay(self) -> None:
        """Test average retry delay calculation"""
        metrics = HostRetryMetrics()
        
        # No retries
        assert metrics.get_average_retry_delay() == 0.0
        
        # With retries
        metrics.total_retry_delay = 10.0
        metrics.retry_counts[2] = 2  # 2 attempts that needed 1 retry each
        metrics.retry_counts[3] = 1  # 1 attempt that needed 2 retries
        
        # Total retries = 2 + 2 = 4
        assert metrics.get_average_retry_delay() == 2.5


class TestAdaptiveRetryManager:
    """Test AdaptiveRetryManager class"""
    
    @pytest.fixture
    def retry_manager(self) -> None:
        """Create a fresh AdaptiveRetryManager for testing"""
        return AdaptiveRetryManager()
    
    def test_initialization(self, retry_manager) -> None:
        """Test AdaptiveRetryManager initialization"""
        assert retry_manager.host_metrics == {}
        assert retry_manager.base_retry_delay == 1.0
        assert retry_manager.max_retry_delay == 60.0
        assert retry_manager.backoff_multiplier == 2.0
        assert retry_manager.jitter_factor == 0.1
        assert retry_manager.max_retries == 5
        assert retry_manager.success_threshold == 0.8
        assert retry_manager.failure_threshold == 0.3
    
    def test_should_retry_new_host(self, retry_manager) -> None:
        """Test retry decision for new host"""
        url = "https://example.com/test"
        
        # Should allow retries for new host
        assert retry_manager.should_retry(url, 1, RetryReason.NETWORK_TIMEOUT)
        assert retry_manager.should_retry(url, 3, RetryReason.CONNECTION_ERROR)
        
        # Should not exceed max retries
        assert not retry_manager.should_retry(url, 6, RetryReason.UNKNOWN_ERROR)
    
    def test_should_retry_successful_host(self, retry_manager) -> None:
        """Test retry decision for host with good success rate"""
        url = "https://example.com/test"
        
        # Record successful attempts
        for i in range(10):
            retry_manager.record_attempt(url, 1, RetryReason.UNKNOWN_ERROR, True, 1.0)
        
        # Should be more lenient with retries
        assert retry_manager.should_retry(url, 1, RetryReason.NETWORK_TIMEOUT)
        assert retry_manager.should_retry(url, 4, RetryReason.CONNECTION_ERROR)
    
    def test_should_retry_failing_host(self, retry_manager) -> None:
        """Test retry decision for host with poor success rate"""
        url = "https://example.com/test"
        
        # Record many failed attempts
        for i in range(10):
            retry_manager.record_attempt(url, 2, RetryReason.CONNECTION_ERROR, False, 5.0)
        
        # Should be less lenient with retries
        assert not retry_manager.should_retry(url, 3, RetryReason.CONNECTION_ERROR)
    
    def test_get_retry_delay_base_case(self, retry_manager) -> None:
        """Test retry delay calculation for base case"""
        url = "https://example.com/test"
        
        delay = retry_manager.get_retry_delay(url, 1, RetryReason.NETWORK_TIMEOUT)
        
        # Should be around base delay with some jitter
        assert 0.9 <= delay <= 1.1  # base_delay ± jitter
    
    def test_get_retry_delay_exponential_backoff(self, retry_manager) -> None:
        """Test exponential backoff in retry delay"""
        url = "https://example.com/test"
        
        delay1 = retry_manager.get_retry_delay(url, 1, RetryReason.NETWORK_TIMEOUT)
        delay2 = retry_manager.get_retry_delay(url, 2, RetryReason.NETWORK_TIMEOUT)
        delay3 = retry_manager.get_retry_delay(url, 3, RetryReason.NETWORK_TIMEOUT)
        
        # Each delay should be roughly double the previous (with jitter)
        assert delay2 > delay1
        assert delay3 > delay2
    
    def test_get_retry_delay_reason_based(self, retry_manager) -> None:
        """Test retry delay based on failure reason"""
        url = "https://example.com/test"
        
        timeout_delay = retry_manager.get_retry_delay(url, 1, RetryReason.NETWORK_TIMEOUT)
        rate_limit_delay = retry_manager.get_retry_delay(url, 1, RetryReason.RATE_LIMITED)
        
        # Rate limiting should have longer delay
        assert rate_limit_delay > timeout_delay
    
    def test_get_retry_delay_max_cap(self, retry_manager) -> None:
        """Test retry delay maximum cap"""
        url = "https://example.com/test"
        
        # Very high attempt number should be capped
        delay = retry_manager.get_retry_delay(url, 10, RetryReason.NETWORK_TIMEOUT)
        
        assert delay <= retry_manager.max_retry_delay
    
    def test_record_attempt_new_host(self, retry_manager) -> None:
        """Test recording attempt for new host"""
        url = "https://example.com/test"
        
        retry_manager.record_attempt(url, 1, RetryReason.NETWORK_TIMEOUT, True, 1.5)
        
        host = retry_manager._get_host_from_url(url)
        assert host in retry_manager.host_metrics
        
        metrics = retry_manager.host_metrics[host]
        assert metrics.total_attempts == 1
        assert metrics.successful_attempts == 1
    
    def test_record_attempt_existing_host(self, retry_manager) -> None:
        """Test recording attempt for existing host"""
        url = "https://example.com/test"
        
        # First attempt
        retry_manager.record_attempt(url, 1, RetryReason.NETWORK_TIMEOUT, True, 1.5)
        # Second attempt
        retry_manager.record_attempt(url, 2, RetryReason.CONNECTION_ERROR, False, 3.0)
        
        host = retry_manager._get_host_from_url(url)
        metrics = retry_manager.host_metrics[host]
        
        assert metrics.total_attempts == 2
        assert metrics.successful_attempts == 1
        assert metrics.failed_attempts == 1
    
    def test_get_host_from_url(self, retry_manager) -> None:
        """Test extracting host from URL"""
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://subdomain.example.com:8080/path", "subdomain.example.com"),
            ("https://192.168.1.1/test", "192.168.1.1"),
        ]
        
        for url, expected_host in test_cases:
            host = retry_manager._get_host_from_url(url)
            assert host == expected_host
    
    def test_calculate_reason_multiplier(self, retry_manager) -> None:
        """Test reason-based delay multiplier"""
        multipliers = {
            RetryReason.NETWORK_TIMEOUT: retry_manager._calculate_reason_multiplier(RetryReason.NETWORK_TIMEOUT),
            RetryReason.CONNECTION_ERROR: retry_manager._calculate_reason_multiplier(RetryReason.CONNECTION_ERROR),
            RetryReason.SERVER_ERROR: retry_manager._calculate_reason_multiplier(RetryReason.SERVER_ERROR),
            RetryReason.RATE_LIMITED: retry_manager._calculate_reason_multiplier(RetryReason.RATE_LIMITED),
            RetryReason.UNKNOWN_ERROR: retry_manager._calculate_reason_multiplier(RetryReason.UNKNOWN_ERROR),
        }
        
        # Rate limiting should have highest multiplier
        assert multipliers[RetryReason.RATE_LIMITED] >= max(multipliers.values())
        
        # All multipliers should be >= 1.0
        for multiplier in multipliers.values():
            assert multiplier >= 1.0
    
    def test_get_global_stats(self, retry_manager) -> None:
        """Test getting global statistics"""
        # Initially empty
        stats = retry_manager.get_global_stats()
        assert stats["total_hosts"] == 0
        assert stats["total_attempts"] == 0
        
        # Add some data
        retry_manager.record_attempt("https://example.com/test", 1, RetryReason.NETWORK_TIMEOUT, True, 1.0)
        retry_manager.record_attempt("https://test.com/path", 2, RetryReason.CONNECTION_ERROR, False, 3.0)
        
        stats = retry_manager.get_global_stats()
        assert stats["total_hosts"] == 2
        assert stats["total_attempts"] == 2
        assert "hosts" in stats
        assert "example.com" in stats["hosts"]
        assert "test.com" in stats["hosts"]
    
    def test_cleanup_old_metrics(self, retry_manager) -> None:
        """Test cleanup of old metrics"""
        url = "https://example.com/test"
        
        # Record an attempt
        retry_manager.record_attempt(url, 1, RetryReason.NETWORK_TIMEOUT, True, 1.0)
        host = retry_manager._get_host_from_url(url)
        assert host in retry_manager.host_metrics
        
        # Mock time to simulate old metrics
        with patch('time.time') as mock_time:
            # Set current time to far in the future
            mock_time.return_value = time.time() + 86400 * 8  # 8 days later
            
            retry_manager.cleanup_old_metrics()
            
            # Old metrics should be removed
            assert host not in retry_manager.host_metrics


class TestGlobalAdaptiveRetryManager:
    """Test global adaptive retry manager instance"""
    
    def test_global_instance_exists(self) -> None:
        """Test that global instance exists and is properly initialized"""
        assert adaptive_retry_manager is not None
        assert isinstance(adaptive_retry_manager, AdaptiveRetryManager)
    
    def test_global_instance_functionality(self) -> None:
        """Test basic functionality of global instance"""
        url = "https://global-retry-test.example.com/test"
        
        # Should be able to make retry decisions and record attempts
        should_retry = adaptive_retry_manager.should_retry(url, 1, RetryReason.NETWORK_TIMEOUT)
        assert isinstance(should_retry, bool)
        
        delay = adaptive_retry_manager.get_retry_delay(url, 1, RetryReason.NETWORK_TIMEOUT)
        assert isinstance(delay, (int, float))
        assert delay > 0
        
        adaptive_retry_manager.record_attempt(url, 1, RetryReason.NETWORK_TIMEOUT, True, 1.5)
        
        # Should have recorded the attempt
        host = adaptive_retry_manager._get_host_from_url(url)
        assert host in adaptive_retry_manager.host_metrics


if __name__ == "__main__":
    pytest.main([__file__])

"""
Tests for adaptive retry strategies
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.core.adaptive_retry import (
    AdaptiveRetryManager, RetryReason, RetryAttempt, HostRetryMetrics,
    RetryConfig, RetryStrategy, adaptive_retry_manager
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


class TestRetryConfig:
    """Test RetryConfig dataclass"""

    def test_default_config(self) -> None:
        """Test default RetryConfig values"""
        config = RetryConfig()
        assert config.max_attempts == 5
        assert config.base_delay == 1.0
        assert config.max_delay == 300.0
        assert config.strategy == RetryStrategy.ADAPTIVE_BACKOFF
        assert config.jitter_factor == 0.1
        assert config.backoff_multiplier == 2.0

    def test_custom_config(self) -> None:
        """Test custom RetryConfig"""
        config = RetryConfig(
            max_attempts=10,
            base_delay=2.0,
            max_delay=600.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        assert config.max_attempts == 10
        assert config.base_delay == 2.0
        assert config.max_delay == 600.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF


class TestHostRetryMetrics:
    """Test HostRetryMetrics dataclass"""

    def test_default_metrics(self) -> None:
        """Test default HostRetryMetrics values"""
        metrics = HostRetryMetrics(host="example.com")
        assert metrics.host == "example.com"
        assert metrics.total_attempts == 0
        assert metrics.successful_attempts == 0
        assert metrics.failed_attempts == 0
        assert metrics.avg_response_time == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.consecutive_failures == 0

    def test_record_attempt_success(self) -> None:
        """Test recording successful attempt"""
        metrics = HostRetryMetrics(host="example.com")
        attempt = RetryAttempt(
            attempt_number=1,
            timestamp=time.time(),
            reason=RetryReason.UNKNOWN_ERROR,
            delay=1.0,
            success=True,
            response_time=1.5
        )

        metrics.record_attempt(attempt)

        assert metrics.total_attempts == 1
        assert metrics.successful_attempts == 1
        assert metrics.failed_attempts == 0
        assert metrics.consecutive_failures == 0
        assert metrics.last_success_time > 0

    def test_record_attempt_failure(self) -> None:
        """Test recording failed attempt"""
        metrics = HostRetryMetrics(host="example.com")
        attempt = RetryAttempt(
            attempt_number=1,
            timestamp=time.time(),
            reason=RetryReason.NETWORK_TIMEOUT,
            delay=1.0,
            success=False,
            response_time=5.0
        )

        metrics.record_attempt(attempt)

        assert metrics.total_attempts == 1
        assert metrics.successful_attempts == 0
        assert metrics.failed_attempts == 1
        assert metrics.consecutive_failures == 1
        assert RetryReason.NETWORK_TIMEOUT in metrics.error_patterns

    def test_multiple_attempts(self) -> None:
        """Test recording multiple attempts"""
        metrics = HostRetryMetrics(host="example.com")

        # First attempt fails
        attempt1 = RetryAttempt(
            attempt_number=1,
            timestamp=time.time(),
            reason=RetryReason.CONNECTION_ERROR,
            delay=1.0,
            success=False,
            response_time=3.0
        )
        metrics.record_attempt(attempt1)

        # Second attempt succeeds
        attempt2 = RetryAttempt(
            attempt_number=2,
            timestamp=time.time(),
            reason=RetryReason.CONNECTION_ERROR,
            delay=2.0,
            success=True,
            response_time=2.0
        )
        metrics.record_attempt(attempt2)

        assert metrics.total_attempts == 2
        assert metrics.successful_attempts == 1
        assert metrics.failed_attempts == 1
        assert metrics.consecutive_failures == 0  # Reset on success

    def test_is_healthy(self) -> None:
        """Test host health check"""
        metrics = HostRetryMetrics(host="example.com")

        # New host should be healthy
        assert metrics.is_healthy()

        # Add many failures
        for i in range(10):
            attempt = RetryAttempt(
                attempt_number=i+1,
                timestamp=time.time(),
                reason=RetryReason.CONNECTION_ERROR,
                delay=1.0,
                success=False
            )
            metrics.record_attempt(attempt)

        # Should be unhealthy after many failures
        assert not metrics.is_healthy()

    def test_get_dominant_error_type(self) -> None:
        """Test getting dominant error type"""
        metrics = HostRetryMetrics(host="example.com")

        # No errors yet
        assert metrics.get_dominant_error_type() is None

        # Add multiple errors
        for i in range(3):
            attempt = RetryAttempt(
                attempt_number=i+1,
                timestamp=time.time(),
                reason=RetryReason.NETWORK_TIMEOUT,
                delay=1.0,
                success=False
            )
            metrics.record_attempt(attempt)

        for i in range(2):
            attempt = RetryAttempt(
                attempt_number=i+4,
                timestamp=time.time(),
                reason=RetryReason.CONNECTION_ERROR,
                delay=1.0,
                success=False
            )
            metrics.record_attempt(attempt)

        # NETWORK_TIMEOUT should be dominant
        assert metrics.get_dominant_error_type() == RetryReason.NETWORK_TIMEOUT


class TestAdaptiveRetryManager:
    """Test AdaptiveRetryManager class"""

    @pytest.fixture
    def retry_manager(self) -> AdaptiveRetryManager:
        """Create a fresh AdaptiveRetryManager for testing"""
        return AdaptiveRetryManager()

    def test_initialization(self, retry_manager) -> None:
        """Test AdaptiveRetryManager initialization"""
        assert retry_manager.host_metrics == {}
        assert retry_manager.default_config.max_attempts == 5
        assert retry_manager.default_config.base_delay == 1.0
        assert retry_manager.default_config.max_delay == 300.0
        assert retry_manager.global_network_quality == 1.0
        assert retry_manager.global_server_load == 1.0

    def test_configure_host(self, retry_manager) -> None:
        """Test configuring retry settings for a specific host"""
        host = "example.com"
        config = RetryConfig(max_attempts=10, base_delay=2.0)

        retry_manager.configure_host(host, config)

        assert host in retry_manager.host_configs
        assert retry_manager.host_configs[host].max_attempts == 10
        assert retry_manager.host_configs[host].base_delay == 2.0

    def test_should_retry_new_host(self, retry_manager) -> None:
        """Test retry decision for new host"""
        host = "example.com"

        # Should allow retries for new host
        assert retry_manager.should_retry(host, 1, RetryReason.NETWORK_TIMEOUT)
        assert retry_manager.should_retry(host, 3, RetryReason.CONNECTION_ERROR)

        # Should not exceed max retries
        assert not retry_manager.should_retry(host, 6, RetryReason.UNKNOWN_ERROR)

    def test_should_retry_rate_limited(self, retry_manager) -> None:
        """Test retry decision for rate limited errors"""
        host = "example.com"

        # Rate limited should always retry (within attempt limit)
        assert retry_manager.should_retry(host, 1, RetryReason.RATE_LIMITED)
        assert retry_manager.should_retry(host, 4, RetryReason.RATE_LIMITED)

    def test_should_retry_server_error(self, retry_manager) -> None:
        """Test retry decision for server errors"""
        host = "example.com"

        # Server errors should retry but with limits
        assert retry_manager.should_retry(host, 1, RetryReason.SERVER_ERROR)
        assert retry_manager.should_retry(host, 3, RetryReason.SERVER_ERROR)
        assert not retry_manager.should_retry(host, 4, RetryReason.SERVER_ERROR)

    def test_should_retry_non_retryable_error(self, retry_manager) -> None:
        """Test retry decision for non-retryable errors"""
        host = "example.com"

        # Authentication errors should not retry
        assert not retry_manager.should_retry(host, 1, RetryReason.UNKNOWN_ERROR, "authentication failed")
        assert not retry_manager.should_retry(host, 1, RetryReason.UNKNOWN_ERROR, "forbidden")

    def test_get_retry_delay_base_case(self, retry_manager) -> None:
        """Test retry delay calculation for base case"""
        host = "example.com"

        delay = retry_manager.get_retry_delay(host, 1, RetryReason.NETWORK_TIMEOUT)

        # Should be positive and within reasonable bounds (base_delay with jitter and error multiplier)
        assert delay > 0
        assert delay <= retry_manager.default_config.max_delay

    def test_get_retry_delay_exponential_backoff(self, retry_manager) -> None:
        """Test exponential backoff in retry delay"""
        host = "example.com"

        delay1 = retry_manager.get_retry_delay(host, 1, RetryReason.NETWORK_TIMEOUT)
        delay2 = retry_manager.get_retry_delay(host, 2, RetryReason.NETWORK_TIMEOUT)
        delay3 = retry_manager.get_retry_delay(host, 3, RetryReason.NETWORK_TIMEOUT)

        # Each delay should be roughly double the previous (with jitter)
        assert delay2 > delay1
        assert delay3 > delay2

    def test_get_retry_delay_reason_based(self, retry_manager) -> None:
        """Test retry delay based on failure reason"""
        host = "example.com"

        timeout_delay = retry_manager.get_retry_delay(host, 1, RetryReason.NETWORK_TIMEOUT)
        rate_limit_delay = retry_manager.get_retry_delay(host, 1, RetryReason.RATE_LIMITED)

        # Rate limiting should have longer delay (minimum 30 seconds with jitter tolerance)
        assert rate_limit_delay >= 25.0  # Allow for jitter
        assert rate_limit_delay > timeout_delay

    def test_get_retry_delay_max_cap(self, retry_manager) -> None:
        """Test retry delay maximum cap"""
        host = "example.com"

        # Very high attempt number should be capped
        delay = retry_manager.get_retry_delay(host, 10, RetryReason.NETWORK_TIMEOUT)

        assert delay <= retry_manager.default_config.max_delay

    def test_record_attempt_new_host(self, retry_manager) -> None:
        """Test recording attempt for new host"""
        host = "example.com"

        retry_manager.record_attempt(host, 1, RetryReason.NETWORK_TIMEOUT, True, 1.5)

        assert host in retry_manager.host_metrics
        metrics = retry_manager.host_metrics[host]
        assert metrics.total_attempts == 1
        assert metrics.successful_attempts == 1

    def test_record_attempt_existing_host(self, retry_manager) -> None:
        """Test recording attempt for existing host"""
        host = "example.com"

        # First attempt
        retry_manager.record_attempt(host, 1, RetryReason.NETWORK_TIMEOUT, True, 1.5)
        # Second attempt
        retry_manager.record_attempt(host, 2, RetryReason.CONNECTION_ERROR, False, 3.0)

        metrics = retry_manager.host_metrics[host]

        assert metrics.total_attempts == 2
        assert metrics.successful_attempts == 1
        assert metrics.failed_attempts == 1

    def test_get_host_stats(self, retry_manager) -> None:
        """Test getting host statistics"""
        host = "example.com"

        # No data yet
        stats = retry_manager.get_host_stats(host)
        assert stats["no_data"] is True

        # Add some attempts
        retry_manager.record_attempt(host, 1, RetryReason.NETWORK_TIMEOUT, True, 1.0)
        retry_manager.record_attempt(host, 2, RetryReason.CONNECTION_ERROR, False, 3.0)

        stats = retry_manager.get_host_stats(host)
        assert stats["host"] == host
        assert stats["total_attempts"] == 2
        assert stats["success_rate"] == 0.5

    def test_get_global_stats(self, retry_manager) -> None:
        """Test getting global statistics"""
        # Initially empty
        stats = retry_manager.get_global_stats()
        assert stats["tracked_hosts"] == 0

        # Add some data
        retry_manager.record_attempt("example.com", 1, RetryReason.NETWORK_TIMEOUT, True, 1.0)
        retry_manager.record_attempt("test.com", 2, RetryReason.CONNECTION_ERROR, False, 3.0)

        stats = retry_manager.get_global_stats()
        assert stats["tracked_hosts"] == 2
        assert stats["global_network_quality"] < 1.0  # Some failures

    def test_reset_host_metrics(self, retry_manager) -> None:
        """Test resetting metrics for a host"""
        host = "example.com"

        # Record an attempt
        retry_manager.record_attempt(host, 1, RetryReason.NETWORK_TIMEOUT, True, 1.0)
        assert host in retry_manager.host_metrics

        # Reset
        retry_manager.reset_host_metrics(host)
        assert host not in retry_manager.host_metrics


class TestGlobalAdaptiveRetryManager:
    """Test global adaptive retry manager instance"""

    def test_global_instance_exists(self) -> None:
        """Test that global instance exists and is properly initialized"""
        assert adaptive_retry_manager is not None
        assert isinstance(adaptive_retry_manager, AdaptiveRetryManager)

    def test_global_instance_functionality(self) -> None:
        """Test basic functionality of global instance"""
        host = "global-retry-test.example.com"

        # Should be able to make retry decisions and record attempts
        should_retry = adaptive_retry_manager.should_retry(host, 1, RetryReason.NETWORK_TIMEOUT)
        assert isinstance(should_retry, bool)

        delay = adaptive_retry_manager.get_retry_delay(host, 1, RetryReason.NETWORK_TIMEOUT)
        assert isinstance(delay, (int, float))
        assert delay > 0

        adaptive_retry_manager.record_attempt(host, 1, RetryReason.NETWORK_TIMEOUT, True, 1.5)

        # Should have recorded the attempt
        assert host in adaptive_retry_manager.host_metrics


if __name__ == "__main__":
    pytest.main([__file__])

"""
Tests for adaptive timeout management
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.core.adaptive_timeout import (
    AdaptiveTimeoutManager, NetworkMetrics, adaptive_timeout_manager
)


class TestNetworkMetrics:
    """Test NetworkMetrics dataclass"""

    def test_default_metrics(self):
        """Test default NetworkMetrics values"""
        metrics = NetworkMetrics("example.com")
        assert metrics.host == "example.com"
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 1.0
        assert metrics.connection_failures == 0
        assert metrics.timeout_failures == 0
        assert metrics.last_updated <= time.time()
    
    def test_add_request_success(self):
        """Test adding successful request"""
        metrics = HostMetrics()
        response_time = 1.5
        
        metrics.add_request(response_time, success=True)
        
        assert metrics.request_count == 1
        assert metrics.success_count == 1
        assert metrics.failure_count == 0
        assert metrics.total_response_time == response_time
        assert metrics.min_response_time == response_time
        assert metrics.max_response_time == response_time
        assert metrics.timeout_count == 0
    
    def test_add_request_failure(self):
        """Test adding failed request"""
        metrics = HostMetrics()
        response_time = 2.0
        
        metrics.add_request(response_time, success=False, is_timeout=True)
        
        assert metrics.request_count == 1
        assert metrics.success_count == 0
        assert metrics.failure_count == 1
        assert metrics.total_response_time == response_time
        assert metrics.min_response_time == response_time
        assert metrics.max_response_time == response_time
        assert metrics.timeout_count == 1
    
    def test_multiple_requests(self):
        """Test multiple requests with different response times"""
        metrics = HostMetrics()
        
        metrics.add_request(1.0, success=True)
        metrics.add_request(3.0, success=True)
        metrics.add_request(2.0, success=False, is_timeout=True)
        
        assert metrics.request_count == 3
        assert metrics.success_count == 2
        assert metrics.failure_count == 1
        assert metrics.total_response_time == 6.0
        assert metrics.min_response_time == 1.0
        assert metrics.max_response_time == 3.0
        assert metrics.timeout_count == 1
    
    def test_get_average_response_time(self):
        """Test average response time calculation"""
        metrics = HostMetrics()
        
        # No requests
        assert metrics.get_average_response_time() == 0.0
        
        # With requests
        metrics.add_request(2.0, success=True)
        metrics.add_request(4.0, success=True)
        
        assert metrics.get_average_response_time() == 3.0
    
    def test_get_success_rate(self):
        """Test success rate calculation"""
        metrics = HostMetrics()
        
        # No requests
        assert metrics.get_success_rate() == 1.0
        
        # With requests
        metrics.add_request(1.0, success=True)
        metrics.add_request(2.0, success=True)
        metrics.add_request(3.0, success=False)
        
        assert metrics.get_success_rate() == 2.0 / 3.0
    
    def test_get_timeout_rate(self):
        """Test timeout rate calculation"""
        metrics = HostMetrics()
        
        # No requests
        assert metrics.get_timeout_rate() == 0.0
        
        # With requests
        metrics.add_request(1.0, success=True)
        metrics.add_request(2.0, success=False, is_timeout=True)
        metrics.add_request(3.0, success=False, is_timeout=True)
        
        assert metrics.get_timeout_rate() == 2.0 / 3.0


class TestAdaptiveTimeoutManager:
    """Test AdaptiveTimeoutManager class"""
    
    @pytest.fixture
    def timeout_manager(self):
        """Create a fresh AdaptiveTimeoutManager for testing"""
        return AdaptiveTimeoutManager()
    
    def test_initialization(self, timeout_manager):
        """Test AdaptiveTimeoutManager initialization"""
        assert timeout_manager.host_metrics == {}
        assert timeout_manager.base_connection_timeout == 30.0
        assert timeout_manager.base_read_timeout == 60.0
        assert timeout_manager.min_timeout == 5.0
        assert timeout_manager.max_timeout == 300.0
        assert timeout_manager.timeout_multiplier == 2.0
        assert timeout_manager.learning_rate == 0.1
    
    def test_get_timeouts_new_host(self, timeout_manager):
        """Test getting timeouts for new host"""
        url = "https://example.com/test"
        
        conn_timeout, read_timeout = timeout_manager.get_timeouts(url)
        
        # Should return base timeouts for new host
        assert conn_timeout == timeout_manager.base_connection_timeout
        assert read_timeout == timeout_manager.base_read_timeout
        
        # Host should be added to metrics
        assert "example.com" in timeout_manager.host_metrics
    
    def test_get_timeouts_existing_host_good_performance(self, timeout_manager):
        """Test getting timeouts for host with good performance"""
        url = "https://example.com/test"
        
        # Record some successful fast requests
        timeout_manager.record_request(url, 0.5, success=True)
        timeout_manager.record_request(url, 0.7, success=True)
        timeout_manager.record_request(url, 0.6, success=True)
        
        conn_timeout, read_timeout = timeout_manager.get_timeouts(url)
        
        # Should reduce timeouts for fast host
        assert conn_timeout < timeout_manager.base_connection_timeout
        assert read_timeout < timeout_manager.base_read_timeout
    
    def test_get_timeouts_existing_host_poor_performance(self, timeout_manager):
        """Test getting timeouts for host with poor performance"""
        url = "https://example.com/test"
        
        # Record some slow/failed requests
        timeout_manager.record_request(url, 5.0, success=False, is_timeout=True)
        timeout_manager.record_request(url, 4.5, success=False, is_timeout=True)
        timeout_manager.record_request(url, 6.0, success=True)
        
        conn_timeout, read_timeout = timeout_manager.get_timeouts(url)
        
        # Should increase timeouts for slow host
        assert conn_timeout > timeout_manager.base_connection_timeout
        assert read_timeout > timeout_manager.base_read_timeout
    
    def test_record_request_new_host(self, timeout_manager):
        """Test recording request for new host"""
        url = "https://example.com/test"
        response_time = 1.5
        
        timeout_manager.record_request(url, response_time, success=True)
        
        assert "example.com" in timeout_manager.host_metrics
        metrics = timeout_manager.host_metrics["example.com"]
        assert metrics.request_count == 1
        assert metrics.success_count == 1
        assert metrics.total_response_time == response_time
    
    def test_record_request_existing_host(self, timeout_manager):
        """Test recording request for existing host"""
        url = "https://example.com/test"
        
        # First request
        timeout_manager.record_request(url, 1.0, success=True)
        
        # Second request
        timeout_manager.record_request(url, 2.0, success=False, is_timeout=True)
        
        metrics = timeout_manager.host_metrics["example.com"]
        assert metrics.request_count == 2
        assert metrics.success_count == 1
        assert metrics.failure_count == 1
        assert metrics.timeout_count == 1
        assert metrics.total_response_time == 3.0
    
    def test_get_host_from_url(self, timeout_manager):
        """Test extracting host from URL"""
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://subdomain.example.com:8080/path", "subdomain.example.com"),
            ("https://192.168.1.1/test", "192.168.1.1"),
            ("ftp://files.example.org/file.txt", "files.example.org"),
        ]
        
        for url, expected_host in test_cases:
            host = timeout_manager._get_host_from_url(url)
            assert host == expected_host
    
    def test_calculate_adaptive_timeout_fast_host(self, timeout_manager):
        """Test adaptive timeout calculation for fast host"""
        metrics = HostMetrics()
        metrics.add_request(0.5, success=True)
        metrics.add_request(0.7, success=True)
        metrics.add_request(0.6, success=True)
        
        base_timeout = 30.0
        adaptive_timeout = timeout_manager._calculate_adaptive_timeout(base_timeout, metrics)
        
        # Should be less than base timeout
        assert adaptive_timeout < base_timeout
        assert adaptive_timeout >= timeout_manager.min_timeout
    
    def test_calculate_adaptive_timeout_slow_host(self, timeout_manager):
        """Test adaptive timeout calculation for slow host"""
        metrics = HostMetrics()
        metrics.add_request(5.0, success=False, is_timeout=True)
        metrics.add_request(4.0, success=False, is_timeout=True)
        metrics.add_request(6.0, success=True)
        
        base_timeout = 30.0
        adaptive_timeout = timeout_manager._calculate_adaptive_timeout(base_timeout, metrics)
        
        # Should be greater than base timeout
        assert adaptive_timeout > base_timeout
        assert adaptive_timeout <= timeout_manager.max_timeout
    
    def test_calculate_adaptive_timeout_no_data(self, timeout_manager):
        """Test adaptive timeout calculation with no data"""
        metrics = HostMetrics()
        base_timeout = 30.0
        
        adaptive_timeout = timeout_manager._calculate_adaptive_timeout(base_timeout, metrics)
        
        # Should return base timeout
        assert adaptive_timeout == base_timeout
    
    def test_get_global_stats(self, timeout_manager):
        """Test getting global statistics"""
        # Initially empty
        stats = timeout_manager.get_global_stats()
        assert stats["total_hosts"] == 0
        assert stats["total_requests"] == 0
        
        # Add some data
        timeout_manager.record_request("https://example.com/test", 1.0, success=True)
        timeout_manager.record_request("https://test.com/path", 2.0, success=False)
        
        stats = timeout_manager.get_global_stats()
        assert stats["total_hosts"] == 2
        assert stats["total_requests"] == 2
        assert "hosts" in stats
        assert "example.com" in stats["hosts"]
        assert "test.com" in stats["hosts"]
    
    def test_cleanup_old_metrics(self, timeout_manager):
        """Test cleanup of old metrics"""
        url = "https://example.com/test"
        
        # Record a request
        timeout_manager.record_request(url, 1.0, success=True)
        assert "example.com" in timeout_manager.host_metrics
        
        # Mock time to simulate old metrics
        with patch('time.time') as mock_time:
            # Set current time to far in the future
            mock_time.return_value = time.time() + 86400 * 8  # 8 days later
            
            timeout_manager.cleanup_old_metrics()
            
            # Old metrics should be removed
            assert "example.com" not in timeout_manager.host_metrics


class TestGlobalAdaptiveTimeoutManager:
    """Test global adaptive timeout manager instance"""
    
    def test_global_instance_exists(self):
        """Test that global instance exists and is properly initialized"""
        assert adaptive_timeout_manager is not None
        assert isinstance(adaptive_timeout_manager, AdaptiveTimeoutManager)
    
    def test_global_instance_functionality(self):
        """Test basic functionality of global instance"""
        url = "https://global-test.example.com/test"
        
        # Should be able to get timeouts and record requests
        conn_timeout, read_timeout = adaptive_timeout_manager.get_timeouts(url)
        assert isinstance(conn_timeout, (int, float))
        assert isinstance(read_timeout, (int, float))
        
        adaptive_timeout_manager.record_request(url, 1.5, success=True)
        
        # Should have recorded the request
        assert "global-test.example.com" in adaptive_timeout_manager.host_metrics


if __name__ == "__main__":
    pytest.main([__file__])

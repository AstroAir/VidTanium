"""
Tests for enhanced connection pool management
"""

import pytest
import time
import threading
import requests
from unittest.mock import Mock, patch, MagicMock
from requests import Session, RequestException
from urllib.parse import urlparse

from src.core.connection_pool import (
    ConnectionPoolManager, HostPoolConfig, ConnectionInfo,
    connection_pool_manager
)
from src.core.exceptions import NetworkException, ErrorContext


class TestHostPoolConfig:
    """Test HostPoolConfig dataclass"""
    
    def test_default_config(self) -> None:
        """Test default configuration values"""
        config = HostPoolConfig()
        assert config.max_connections == 10
        assert config.max_connections_per_host == 5
        assert config.connection_timeout == 30.0
        assert config.read_timeout == 60.0
        assert config.max_retries == 3
        assert config.backoff_factor == 0.3
        assert config.keep_alive_timeout == 300.0
        assert config.health_check_interval == 60.0
    
    def test_custom_config(self) -> None:
        """Test custom configuration values"""
        config = HostPoolConfig(
            max_connections=20,
            max_connections_per_host=8,
            connection_timeout=45.0,
            read_timeout=120.0
        )
        assert config.max_connections == 20
        assert config.max_connections_per_host == 8
        assert config.connection_timeout == 45.0
        assert config.read_timeout == 120.0


class TestConnectionInfo:
    """Test ConnectionInfo wrapper"""

    def test_connection_info_creation(self) -> None:
        """Test ConnectionInfo creation and attributes"""
        mock_session = Mock(spec=Session)
        host = "example.com"
        config = HostPoolConfig()

        from src.core.connection_pool import ConnectionStats
        stats = ConnectionStats()
        connection_info = ConnectionInfo(mock_session, stats, host, config)

        assert connection_info.session == mock_session
        assert connection_info.host == host
        assert connection_info.pool_config == config
        assert connection_info.stats.created_at <= time.time()
        assert connection_info.stats.last_used <= time.time()
        assert connection_info.stats.requests_count == 0
        assert connection_info.stats.is_healthy is True
    
    def test_needs_health_check(self) -> None:
        """Test health check timing"""
        mock_session = Mock(spec=Session)
        config = HostPoolConfig(health_check_interval=1.0)  # 1 second interval

        from src.core.connection_pool import ConnectionStats
        stats = ConnectionStats()
        connection_info = ConnectionInfo(mock_session, stats, "example.com", config)

        # Should not need health check immediately
        assert not connection_info.needs_health_check()

        # Mock time to simulate health check needed
        connection_info.last_health_check = time.time() - 2.0  # 2 seconds ago
        assert connection_info.needs_health_check()


class TestConnectionPoolManager:
    """Test ConnectionPoolManager class"""
    
    @pytest.fixture
    def pool_manager(self) -> None:
        """Create a fresh ConnectionPoolManager for testing"""
        manager = ConnectionPoolManager()
        yield manager
        # Cleanup
        manager.stop_monitoring()
        manager.cleanup_all_connections()
    
    def test_initialization(self, pool_manager) -> None:
        """Test ConnectionPoolManager initialization"""
        assert len(pool_manager.connection_pools) == 0
        assert len(pool_manager.host_configs) == 0
        assert pool_manager.monitoring_active is False
        assert pool_manager.health_monitor_thread is None
    
    def test_configure_host_pool(self, pool_manager) -> None:
        """Test configuring host pool"""
        host = "example.com"
        config = HostPoolConfig(max_connections=15)

        pool_manager.configure_host(host, config)

        assert host in pool_manager.host_configs
        assert pool_manager.host_configs[host] == config
    
    def test_get_session_new_host(self, pool_manager) -> None:
        """Test getting session for new host"""
        url = "https://example.com/test"
        error_context = ErrorContext(task_id="test_task")

        with patch('requests.Session') as mock_session_class:
            mock_session = Mock(spec=Session)
            mock_session_class.return_value = mock_session

            session = pool_manager.get_session(url, error_context)

            # Should return the mocked session
            assert session == mock_session
            # Check that host pool was created
            host = "https://example.com"
            assert host in pool_manager.connection_pools
    
    def test_get_session_existing_host(self, pool_manager) -> None:
        """Test getting session for existing host"""
        url = "https://example.com/test"
        error_context = ErrorContext(task_id="test_task")

        with patch('requests.Session') as mock_session_class:
            mock_session = Mock(spec=Session)
            mock_session_class.return_value = mock_session

            # Get first session
            session1 = pool_manager.get_session(url, error_context)

            # Release it back to pool
            pool_manager.release_session(session1, url, success=True)

            # Get session again
            session2 = pool_manager.get_session(url, error_context)

            # Both should be the mocked session
            assert session1 == mock_session
            assert session2 == mock_session
    
    def test_release_session_success(self, pool_manager) -> None:
        """Test releasing session with success"""
        url = "https://example.com/test"
        error_context = ErrorContext(task_id="test_task")

        with patch('requests.Session') as mock_session_class:
            mock_session = Mock(spec=Session)
            mock_session_class.return_value = mock_session

            session = pool_manager.get_session(url, error_context)

            # Should not raise an exception
            pool_manager.release_session(
                session, url, success=True,
                bytes_transferred=1024, response_time=0.5
            )

            # Verify host pool exists
            host = "https://example.com"
            assert host in pool_manager.connection_pools
    
    def test_release_session_failure(self, pool_manager) -> None:
        """Test releasing session with failure"""
        url = "https://example.com/test"
        error_context = ErrorContext(task_id="test_task")

        with patch('requests.Session') as mock_session_class:
            mock_session = Mock(spec=Session)
            mock_session_class.return_value = mock_session

            session = pool_manager.get_session(url, error_context)

            # Should not raise an exception
            pool_manager.release_session(
                session, url, success=False,
                bytes_transferred=0, response_time=5.0
            )

            # Verify host pool exists
            host = "https://example.com"
            assert host in pool_manager.connection_pools
    
    def test_start_stop_monitoring(self, pool_manager) -> None:
        """Test starting and stopping monitoring"""
        assert pool_manager.monitoring_active is False

        pool_manager.start_monitoring()
        assert pool_manager.monitoring_active is True
        assert pool_manager.health_monitor_thread is not None

        pool_manager.stop_monitoring()
        assert pool_manager.monitoring_active is False

    def test_get_pool_stats(self, pool_manager) -> None:
        """Test getting pool statistics"""
        # Initially empty
        stats = pool_manager.get_stats()
        assert "total_hosts" in stats
        assert "hosts" in stats

        # Should start with 0 hosts
        assert stats["total_hosts"] == 0


class TestGlobalConnectionPoolManager:
    """Test global connection pool manager instance"""
    
    def test_global_instance_exists(self) -> None:
        """Test that global instance exists and is properly initialized"""
        assert connection_pool_manager is not None
        assert isinstance(connection_pool_manager, ConnectionPoolManager)
    
    def test_global_instance_functionality(self) -> None:
        """Test basic functionality of global instance"""
        url = "https://test.example.com/test"
        error_context = ErrorContext(task_id="global_test")

        with patch('requests.Session') as mock_session_class:
            mock_session = Mock(spec=Session)
            mock_session_class.return_value = mock_session

            # Should be able to get and release sessions
            session = connection_pool_manager.get_session(url, error_context)
            assert session == mock_session

            connection_pool_manager.release_session(session, url, success=True)

            # Cleanup
            connection_pool_manager.cleanup_all_connections()


if __name__ == "__main__":
    pytest.main([__file__])

"""
Integration tests for enhanced components working together
"""

import pytest
import tempfile
import os
import time
import threading
from unittest.mock import Mock, patch, MagicMock

from src.core.downloader import DownloadManager, DownloadTask, TaskStatus, TaskPriority
from src.core.connection_pool import connection_pool_manager
from src.core.adaptive_timeout import adaptive_timeout_manager
from src.core.memory_optimizer import memory_optimizer
from src.core.resource_manager import resource_manager
from src.core.adaptive_retry import adaptive_retry_manager, RetryReason
from src.core.circuit_breaker import circuit_breaker_manager
from src.core.progressive_recovery import progressive_recovery_manager
from src.core.segment_validator import segment_validator
from src.core.integrity_verifier import content_integrity_verifier, IntegrityLevel
from src.core.exceptions import ErrorContext


class TestEnhancedComponentsIntegration:
    """Test integration of all enhanced components"""
    
    @pytest.fixture
    def temp_dir(self) -> None:
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def download_manager(self, temp_dir) -> None:
        """Create a DownloadManager for testing"""
        # Mock settings
        mock_settings = Mock()
        mock_settings.get.return_value = 3  # max_concurrent_tasks
        
        manager = DownloadManager(settings=mock_settings)
        yield manager
        # Cleanup
        manager.stop()
    
    def test_all_components_initialization(self, download_manager) -> None:
        """Test that all enhanced components are properly initialized"""
        # Check that all components are accessible
        assert download_manager.connection_pool is not None
        assert download_manager.timeout_manager is not None
        assert download_manager.memory_optimizer is not None
        assert download_manager.adaptive_retry_manager is not None
        assert download_manager.circuit_breaker_manager is not None
        assert download_manager.recovery_manager is not None
        assert download_manager.segment_validator is not None
        assert download_manager.integrity_verifier is not None
        
        # Check that global instances are the same
        assert download_manager.connection_pool is connection_pool_manager
        assert download_manager.timeout_manager is adaptive_timeout_manager
        assert download_manager.memory_optimizer is memory_optimizer
        assert download_manager.adaptive_retry_manager is adaptive_retry_manager
        assert download_manager.circuit_breaker_manager is circuit_breaker_manager
        assert download_manager.recovery_manager is progressive_recovery_manager
        assert download_manager.segment_validator is segment_validator
        assert download_manager.integrity_verifier is content_integrity_verifier
    
    def test_monitoring_systems_started(self, download_manager) -> None:
        """Test that all monitoring systems are started"""
        download_manager.start()
        
        # Check that monitoring is active
        assert resource_manager.monitoring_active is True
        assert circuit_breaker_manager.monitoring_active is True
        assert connection_pool_manager.monitoring_active is True
    
    def test_comprehensive_stats_collection(self, download_manager) -> None:
        """Test comprehensive statistics collection from all components"""
        download_manager.start()
        
        # Get comprehensive stats
        stats = download_manager.get_comprehensive_stats()
        
        # Verify all component stats are included
        assert "download_manager" in stats
        assert "connection_pool" in stats
        assert "adaptive_timeout" in stats
        assert "memory_optimizer" in stats
        assert "resource_manager" in stats
        assert "adaptive_retry" in stats
        assert "circuit_breakers" in stats
        assert "segment_validator" in stats
        assert "integrity_verifier" in stats
        
        # Verify stats structure
        assert "total_tasks" in stats["download_manager"]
        assert "total_hosts" in stats["connection_pool"]
        assert "total_hosts" in stats["adaptive_timeout"]
        assert "system_memory" in stats["memory_optimizer"]
        assert "total_resources" in stats["resource_manager"]
        assert "total_hosts" in stats["adaptive_retry"]
        assert "total_circuit_breakers" in stats["circuit_breakers"]
        assert "total_validations" in stats["segment_validator"]
        assert "total_verifications" in stats["integrity_verifier"]
    
    def test_performance_metrics_collection(self, download_manager) -> None:
        """Test performance metrics collection"""
        download_manager.start()
        
        # Get performance metrics
        metrics = download_manager.get_performance_metrics()
        
        # Verify all performance metrics are included
        assert "network_quality" in metrics
        assert "memory_usage" in metrics
        assert "connection_health" in metrics
        assert "retry_success_rate" in metrics
        assert "circuit_breaker_status" in metrics
        assert "validation_success_rate" in metrics
        
        # Verify metric types
        assert isinstance(metrics["network_quality"], (int, float))
        assert isinstance(metrics["memory_usage"], dict)
        assert isinstance(metrics["connection_health"], dict)
        assert isinstance(metrics["retry_success_rate"], dict)
        assert isinstance(metrics["circuit_breaker_status"], dict)
        assert isinstance(metrics["validation_success_rate"], (int, float))
    
    def test_system_health_assessment(self, download_manager) -> None:
        """Test system health assessment"""
        download_manager.start()
        
        # Get system health
        health = download_manager.get_system_health()
        
        # Verify health structure
        assert "overall_health" in health
        assert "network_health" in health
        assert "memory_health" in health
        assert "circuit_health" in health
        assert "status" in health
        assert "recommendations" in health
        
        # Verify health values
        assert 0.0 <= health["overall_health"] <= 1.0
        assert 0.0 <= health["network_health"] <= 1.0
        assert 0.0 <= health["memory_health"] <= 1.0
        assert 0.0 <= health["circuit_health"] <= 1.0
        assert health["status"] in ["healthy", "degraded", "critical"]
        assert isinstance(health["recommendations"], list)
    
    @patch('requests.Session')
    def test_connection_pool_integration(self, mock_session_class, download_manager) -> None:
        """Test connection pool integration"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        url = "https://test.example.com/segment.ts"
        error_context = ErrorContext(task_id="test_task")
        
        # Get session from connection pool
        pooled_session = connection_pool_manager.get_session(url, error_context)
        
        assert pooled_session is not None
        assert pooled_session.host == "test.example.com"
        
        # Release session
        connection_pool_manager.release_session(pooled_session, url, success=True)
        
        # Verify session was returned to pool
        stats = connection_pool_manager.get_pool_stats()
        assert stats["total_hosts"] >= 1
    
    def test_adaptive_timeout_integration(self, download_manager) -> None:
        """Test adaptive timeout integration"""
        url = "https://test.example.com/segment.ts"
        
        # Get initial timeouts
        conn_timeout, read_timeout = adaptive_timeout_manager.get_timeouts(url)
        
        assert isinstance(conn_timeout, (int, float))
        assert isinstance(read_timeout, (int, float))
        assert conn_timeout > 0
        assert read_timeout > 0
        
        # Record some requests
        adaptive_timeout_manager.record_request(url, 1.5, success=True)
        adaptive_timeout_manager.record_request(url, 2.0, success=True)
        
        # Get updated timeouts
        new_conn_timeout, new_read_timeout = adaptive_timeout_manager.get_timeouts(url)
        
        # Timeouts should be optimized for fast responses
        assert new_conn_timeout <= conn_timeout
        assert new_read_timeout <= read_timeout
    
    def test_memory_optimizer_integration(self, download_manager) -> None:
        """Test memory optimizer integration"""
        buffer_id = "test_integration_buffer"
        
        # Create streaming buffer
        buffer = memory_optimizer.create_streaming_buffer(buffer_id)
        
        assert buffer is not None
        assert buffer.buffer_id == buffer_id
        assert buffer_id in memory_optimizer.streaming_buffers
        
        # Get optimal buffer size
        optimal_size = memory_optimizer.get_optimal_buffer_size(buffer_id)
        assert isinstance(optimal_size, int)
        assert optimal_size > 0
        
        # Record performance
        memory_optimizer.record_buffer_performance(buffer_id, 1024, 1.0)
        
        # Release buffer
        memory_optimizer.release_streaming_buffer(buffer_id)
        assert buffer_id not in memory_optimizer.streaming_buffers
    
    def test_adaptive_retry_integration(self, download_manager) -> None:
        """Test adaptive retry integration"""
        url = "https://test.example.com/segment.ts"
        
        # Test retry decision
        should_retry = adaptive_retry_manager.should_retry(url, 1, RetryReason.NETWORK_TIMEOUT)
        assert isinstance(should_retry, bool)
        
        # Get retry delay
        delay = adaptive_retry_manager.get_retry_delay(url, 1, RetryReason.NETWORK_TIMEOUT)
        assert isinstance(delay, (int, float))
        assert delay > 0
        
        # Record attempt
        adaptive_retry_manager.record_attempt(url, 1, RetryReason.NETWORK_TIMEOUT, True, 1.5)
        
        # Verify attempt was recorded
        stats = adaptive_retry_manager.get_global_stats()
        assert stats["total_hosts"] >= 1
        assert stats["total_attempts"] >= 1
    
    def test_circuit_breaker_integration(self, download_manager) -> None:
        """Test circuit breaker integration"""
        url = "https://test.example.com/segment.ts"
        
        # Test execution permission
        can_execute = circuit_breaker_manager.can_execute(url)
        assert can_execute is True  # Should allow execution initially
        
        # Record success
        circuit_breaker_manager.record_success(url, 1.5)
        
        # Record failure
        circuit_breaker_manager.record_failure(url, "Test error")
        
        # Verify circuit breaker was created
        stats = circuit_breaker_manager.get_all_stats()
        assert stats["total_circuit_breakers"] >= 1
    
    def test_progressive_recovery_integration(self, download_manager) -> None:
        """Test progressive recovery integration"""
        task_id = "test_recovery_task"
        
        # Create recovery session
        session = progressive_recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://test.example.com/video.m3u8",
            "/tmp/output.mp4", 10
        )
        
        assert session is not None
        assert session.task_id == task_id
        
        # Mark segment complete
        progressive_recovery_manager.mark_segment_complete(task_id, 0, "/tmp/segment_0.ts", 1024)
        
        # Get resume info
        resume_info = progressive_recovery_manager.get_resume_info(task_id)
        assert resume_info is not None
        assert resume_info["can_resume"] is True
        assert resume_info["completion_percentage"] == 10.0
        
        # Cleanup
        progressive_recovery_manager.remove_session(task_id)
    
    def test_segment_validator_integration(self, download_manager) -> None:
        """Test segment validator integration"""
        # Create a temporary test file
        fd, temp_file = tempfile.mkstemp(suffix=".ts")
        test_data = b"Test segment data"
        os.write(fd, test_data)
        os.close(fd)
        
        try:
            # Validate segment
            result = segment_validator.validate_segment(1, temp_file, len(test_data))
            
            assert result is not None
            assert result.segment_id == 1
            assert result.is_valid is True
            assert result.file_size == len(test_data)
            
            # Verify stats were updated
            stats = segment_validator.get_validation_stats()
            assert stats["total_validations"] >= 1
            assert stats["successful_validations"] >= 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_integrity_verifier_integration(self, download_manager) -> None:
        """Test integrity verifier integration"""
        # Create a temporary test file
        fd, temp_file = tempfile.mkstemp(suffix=".ts")
        test_data = b"Test content for integrity verification"
        os.write(fd, test_data)
        os.close(fd)
        
        try:
            import hashlib
            expected_hash = hashlib.md5(test_data).hexdigest()
            
            # Verify file integrity
            result = content_integrity_verifier.verify_file_integrity(
                temp_file, expected_hash, IntegrityLevel.STANDARD
            )
            
            assert result is not None
            assert result.file_path == temp_file
            assert result.is_valid is True
            assert result.integrity_level == IntegrityLevel.STANDARD
            
            # Verify stats were updated
            stats = content_integrity_verifier.get_verification_stats()
            assert stats["total_verifications"] >= 1
            assert stats["successful_verifications"] >= 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_resource_manager_integration(self, download_manager) -> None:
        """Test resource manager integration"""
        from src.core.resource_manager import ResourceType
        
        # Register a test resource
        test_resource = {"test": "data"}
        resource_id = resource_manager.register_resource(
            test_resource, ResourceType.DOWNLOAD_TASK, metadata={"test": True}
        )
        
        assert resource_id is not None
        assert resource_id in resource_manager.resources
        
        # Access resource
        accessed_resource = resource_manager.access_resource(resource_id)
        assert accessed_resource is test_resource
        
        # Get enhanced stats
        stats = resource_manager.get_enhanced_stats()
        assert stats["total_resources"] >= 1
        assert stats["active_resources"] >= 1
        
        # Cleanup resource
        success = resource_manager.cleanup_resource_enhanced(resource_id, force=True)
        assert success is True
        assert resource_id not in resource_manager.resources
    
    def test_component_shutdown_integration(self, download_manager) -> None:
        """Test that all components shut down properly"""
        download_manager.start()
        
        # Verify components are running
        assert resource_manager.monitoring_active is True
        assert circuit_breaker_manager.monitoring_active is True
        assert connection_pool_manager.monitoring_active is True
        
        # Stop download manager
        download_manager.stop()
        
        # Verify components are stopped
        assert resource_manager.monitoring_active is False
        assert circuit_breaker_manager.monitoring_active is False
        assert connection_pool_manager.monitoring_active is False


if __name__ == "__main__":
    pytest.main([__file__])

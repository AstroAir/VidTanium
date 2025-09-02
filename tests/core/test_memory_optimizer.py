"""
Tests for memory optimization
"""

import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from src.core.memory_optimizer import (
    MemoryOptimizer, StreamingBuffer, memory_optimizer
)


class TestStreamingBuffer:
    """Test StreamingBuffer class"""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing"""
        fd, path = tempfile.mkstemp()
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    def test_streaming_buffer_creation(self):
        """Test StreamingBuffer creation"""
        buffer_id = "test_buffer"
        buffer_size = 1024
        
        buffer = StreamingBuffer(buffer_id, buffer_size)
        
        assert buffer.buffer_id == buffer_id
        assert buffer.max_size == buffer_size
        assert buffer.current_size == 0
        assert buffer.data == b""
        assert buffer.created_at <= time.time()
        assert buffer.last_accessed <= time.time()
        assert buffer.write_count == 0
        assert buffer.flush_count == 0
    
    def test_write_within_capacity(self):
        """Test writing data within buffer capacity"""
        buffer = StreamingBuffer("test", 1024)
        data = b"Hello, World!"
        
        bytes_written = buffer.write(data)
        
        assert bytes_written == len(data)
        assert buffer.current_size == len(data)
        assert buffer.data == data
        assert buffer.write_count == 1
    
    def test_write_exceeds_capacity(self):
        """Test writing data that exceeds buffer capacity"""
        buffer = StreamingBuffer("test", 10)
        data = b"This is a long string that exceeds buffer capacity"
        
        bytes_written = buffer.write(data)
        
        # Should only write up to buffer capacity
        assert bytes_written == 10
        assert buffer.current_size == 10
        assert buffer.data == data[:10]
        assert buffer.write_count == 1
    
    def test_flush_to_file(self, temp_file):
        """Test flushing buffer to file"""
        buffer = StreamingBuffer("test", 1024)
        data = b"Test data for flushing"
        buffer.write(data)
        
        with open(temp_file, 'wb') as f:
            buffer.flush_to_file(f)
        
        # Buffer should be empty after flush
        assert buffer.current_size == 0
        assert buffer.data == b""
        assert buffer.flush_count == 1
        
        # File should contain the data
        with open(temp_file, 'rb') as f:
            file_content = f.read()
        assert file_content == data
    
    def test_clear_buffer(self):
        """Test clearing buffer"""
        buffer = StreamingBuffer("test", 1024)
        buffer.write(b"Some data")
        
        assert buffer.current_size > 0
        
        buffer.clear()
        
        assert buffer.current_size == 0
        assert buffer.data == b""
    
    def test_get_stats(self):
        """Test getting buffer statistics"""
        buffer = StreamingBuffer("test", 1024)
        buffer.write(b"Test data")
        
        stats = buffer.get_stats()
        
        assert stats["buffer_id"] == "test"
        assert stats["max_size"] == 1024
        assert stats["current_size"] == len(b"Test data")
        assert stats["write_count"] == 1
        assert stats["flush_count"] == 0
        assert "created_at" in stats
        assert "last_accessed" in stats


class TestMemoryOptimizer:
    """Test MemoryOptimizer class"""
    
    @pytest.fixture
    def memory_optimizer_instance(self):
        """Create a fresh MemoryOptimizer for testing"""
        return MemoryOptimizer()
    
    def test_initialization(self, memory_optimizer_instance):
        """Test MemoryOptimizer initialization"""
        optimizer = memory_optimizer_instance
        assert optimizer.streaming_buffers == {}
        assert optimizer.buffer_performance == {}
        assert optimizer.memory_threshold == 0.8
        assert optimizer.cleanup_threshold == 0.9
        assert optimizer.min_buffer_size == 8192
        assert optimizer.max_buffer_size == 1048576
        assert optimizer.default_buffer_size == 65536
    
    @patch('psutil.virtual_memory')
    def test_check_memory_pressure_normal(self, mock_memory, memory_optimizer_instance):
        """Test memory pressure check under normal conditions"""
        # Mock normal memory usage (60%)
        mock_memory.return_value = Mock(
            total=8 * 1024**3,  # 8GB
            available=3.2 * 1024**3,  # 3.2GB available
            percent=60.0
        )
        
        result = memory_optimizer_instance.check_memory_pressure()
        
        assert result["action"] == "continue"
        assert result["memory_percent"] == 60.0
        assert result["available_mb"] > 0
    
    @patch('psutil.virtual_memory')
    def test_check_memory_pressure_high(self, mock_memory, memory_optimizer_instance):
        """Test memory pressure check under high memory usage"""
        # Mock high memory usage (85%)
        mock_memory.return_value = Mock(
            total=8 * 1024**3,  # 8GB
            available=1.2 * 1024**3,  # 1.2GB available
            percent=85.0
        )
        
        result = memory_optimizer_instance.check_memory_pressure()
        
        assert result["action"] == "reduce_usage"
        assert result["memory_percent"] == 85.0
    
    @patch('psutil.virtual_memory')
    def test_check_memory_pressure_critical(self, mock_memory, memory_optimizer_instance):
        """Test memory pressure check under critical memory usage"""
        # Mock critical memory usage (95%)
        mock_memory.return_value = Mock(
            total=8 * 1024**3,  # 8GB
            available=0.4 * 1024**3,  # 0.4GB available
            percent=95.0
        )
        
        result = memory_optimizer_instance.check_memory_pressure()
        
        assert result["action"] == "emergency_cleanup"
        assert result["memory_percent"] == 95.0
    
    def test_create_streaming_buffer(self, memory_optimizer_instance):
        """Test creating streaming buffer"""
        buffer_id = "test_buffer"
        
        buffer = memory_optimizer_instance.create_streaming_buffer(buffer_id)
        
        assert isinstance(buffer, StreamingBuffer)
        assert buffer.buffer_id == buffer_id
        assert buffer_id in memory_optimizer_instance.streaming_buffers
    
    def test_create_streaming_buffer_custom_size(self, memory_optimizer_instance):
        """Test creating streaming buffer with custom size"""
        buffer_id = "test_buffer"
        custom_size = 32768
        
        buffer = memory_optimizer_instance.create_streaming_buffer(buffer_id, custom_size)
        
        assert buffer.max_size == custom_size
    
    def test_get_optimal_buffer_size_normal_memory(self, memory_optimizer_instance):
        """Test optimal buffer size calculation under normal memory"""
        with patch.object(memory_optimizer_instance, 'check_memory_pressure') as mock_check:
            mock_check.return_value = {"action": "continue", "memory_percent": 60.0}
            
            size = memory_optimizer_instance.get_optimal_buffer_size("test")
            
            assert size == memory_optimizer_instance.default_buffer_size
    
    def test_get_optimal_buffer_size_high_memory(self, memory_optimizer_instance):
        """Test optimal buffer size calculation under high memory pressure"""
        with patch.object(memory_optimizer_instance, 'check_memory_pressure') as mock_check:
            mock_check.return_value = {"action": "reduce_usage", "memory_percent": 85.0}
            
            size = memory_optimizer_instance.get_optimal_buffer_size("test")
            
            assert size < memory_optimizer_instance.default_buffer_size
            assert size >= memory_optimizer_instance.min_buffer_size
    
    def test_get_optimal_buffer_size_critical_memory(self, memory_optimizer_instance):
        """Test optimal buffer size calculation under critical memory pressure"""
        with patch.object(memory_optimizer_instance, 'check_memory_pressure') as mock_check:
            mock_check.return_value = {"action": "emergency_cleanup", "memory_percent": 95.0}
            
            size = memory_optimizer_instance.get_optimal_buffer_size("test")
            
            assert size == memory_optimizer_instance.min_buffer_size
    
    def test_release_streaming_buffer(self, memory_optimizer_instance):
        """Test releasing streaming buffer"""
        buffer_id = "test_buffer"
        buffer = memory_optimizer_instance.create_streaming_buffer(buffer_id)
        
        assert buffer_id in memory_optimizer_instance.streaming_buffers
        
        memory_optimizer_instance.release_streaming_buffer(buffer_id)
        
        assert buffer_id not in memory_optimizer_instance.streaming_buffers
    
    def test_record_buffer_performance(self, memory_optimizer_instance):
        """Test recording buffer performance"""
        buffer_id = "test_buffer"
        bytes_processed = 1024
        duration = 1.5
        
        memory_optimizer_instance.record_buffer_performance(buffer_id, bytes_processed, duration)
        
        assert buffer_id in memory_optimizer_instance.buffer_performance
        perf = memory_optimizer_instance.buffer_performance[buffer_id]
        assert perf["total_bytes"] == bytes_processed
        assert perf["total_duration"] == duration
        assert perf["operation_count"] == 1
    
    def test_record_buffer_performance_multiple(self, memory_optimizer_instance):
        """Test recording multiple buffer performance entries"""
        buffer_id = "test_buffer"
        
        memory_optimizer_instance.record_buffer_performance(buffer_id, 1024, 1.0)
        memory_optimizer_instance.record_buffer_performance(buffer_id, 2048, 1.5)
        
        perf = memory_optimizer_instance.buffer_performance[buffer_id]
        assert perf["total_bytes"] == 3072
        assert perf["total_duration"] == 2.5
        assert perf["operation_count"] == 2
    
    def test_get_memory_stats(self, memory_optimizer_instance):
        """Test getting memory statistics"""
        # Create some buffers
        buffer1 = memory_optimizer_instance.create_streaming_buffer("buffer1")
        buffer2 = memory_optimizer_instance.create_streaming_buffer("buffer2")
        buffer1.write(b"test data")
        
        # Record some performance
        memory_optimizer_instance.record_buffer_performance("buffer1", 1024, 1.0)
        
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = Mock(
                total=8 * 1024**3,
                available=4 * 1024**3,
                percent=50.0
            )
            
            stats = memory_optimizer_instance.get_memory_stats()
            
            assert "system_memory" in stats
            assert "optimizer_stats" in stats
            assert stats["optimizer_stats"]["active_buffers"] == 2
            assert stats["optimizer_stats"]["total_buffer_memory"] > 0
    
    def test_cleanup_old_buffers(self, memory_optimizer_instance):
        """Test cleanup of old buffers"""
        buffer_id = "old_buffer"
        buffer = memory_optimizer_instance.create_streaming_buffer(buffer_id)
        
        # Mock old timestamp
        buffer.last_accessed = time.time() - 3700  # Over 1 hour old
        
        memory_optimizer_instance.cleanup_old_buffers()
        
        # Old buffer should be removed
        assert buffer_id not in memory_optimizer_instance.streaming_buffers
    
    def test_cleanup(self, memory_optimizer_instance):
        """Test general cleanup"""
        # Create some buffers and performance data
        memory_optimizer_instance.create_streaming_buffer("buffer1")
        memory_optimizer_instance.create_streaming_buffer("buffer2")
        memory_optimizer_instance.record_buffer_performance("buffer1", 1024, 1.0)
        
        memory_optimizer_instance.cleanup()
        
        # All data should be cleared
        assert len(memory_optimizer_instance.streaming_buffers) == 0
        assert len(memory_optimizer_instance.buffer_performance) == 0


class TestGlobalMemoryOptimizer:
    """Test global memory optimizer instance"""
    
    def test_global_instance_exists(self):
        """Test that global instance exists and is properly initialized"""
        assert memory_optimizer is not None
        assert isinstance(memory_optimizer, MemoryOptimizer)
    
    def test_global_instance_functionality(self):
        """Test basic functionality of global instance"""
        buffer_id = "global_test_buffer"
        
        # Should be able to create and release buffers
        buffer = memory_optimizer.create_streaming_buffer(buffer_id)
        assert isinstance(buffer, StreamingBuffer)
        
        memory_optimizer.release_streaming_buffer(buffer_id)
        assert buffer_id not in memory_optimizer.streaming_buffers


if __name__ == "__main__":
    pytest.main([__file__])

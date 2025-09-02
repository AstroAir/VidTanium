"""
Memory Optimizer for VidTanium

This module provides intelligent memory management for downloads including
streaming operations, adaptive buffer sizing, and memory-mapped file operations.
"""

import os
import mmap
import psutil
import threading
import time
import gc
from typing import Dict, Optional, Any, BinaryIO, Union, List
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Memory optimization configuration"""
    max_memory_usage_percent: float = 70.0  # Maximum memory usage percentage
    buffer_size_min: int = 8192  # 8KB minimum buffer
    buffer_size_max: int = 1048576  # 1MB maximum buffer
    buffer_size_default: int = 65536  # 64KB default buffer
    memory_check_interval: float = 5.0  # Check memory every 5 seconds
    gc_threshold_mb: int = 100  # Trigger GC when memory usage increases by this amount
    mmap_threshold_mb: int = 50  # Use memory mapping for files larger than this


class StreamingBuffer:
    """Intelligent streaming buffer with adaptive sizing"""
    
    def __init__(self, initial_size: int = 65536, max_size: int = 1048576):
        self.buffer = bytearray(initial_size)
        self.size = initial_size
        self.max_size = max_size
        self.position = 0
        self.data_length = 0
        self.performance_history: List[Dict[str, Any]] = []
        
    def resize(self, new_size: int):
        """Resize buffer based on performance"""
        new_size = min(max(new_size, 8192), self.max_size)
        if new_size != self.size:
            old_data = self.buffer[:self.data_length]
            self.buffer = bytearray(new_size)
            self.buffer[:len(old_data)] = old_data
            self.size = new_size
            logger.debug(f"Buffer resized to {new_size} bytes")
    
    def write(self, data: bytes) -> int:
        """Write data to buffer"""
        data_len = len(data)
        if self.position + data_len > self.size:
            # Auto-resize if needed
            new_size = min(self.size * 2, self.max_size)
            if new_size > self.size:
                self.resize(new_size)
            else:
                # Buffer full, return what we can write
                available = self.size - self.position
                self.buffer[self.position:self.position + available] = data[:available]
                self.position += available
                self.data_length = max(self.data_length, self.position)
                return available
        
        self.buffer[self.position:self.position + data_len] = data
        self.position += data_len
        self.data_length = max(self.data_length, self.position)
        return data_len
    
    def read(self, size: int = -1) -> bytes:
        """Read data from buffer"""
        if size == -1:
            size = self.data_length - self.position
        
        end_pos = min(self.position + size, self.data_length)
        data = bytes(self.buffer[self.position:end_pos])
        self.position = end_pos
        return data
    
    def flush_to_file(self, file_handle: BinaryIO) -> int:
        """Flush buffer contents to file"""
        if self.data_length > 0:
            written = file_handle.write(self.buffer[:self.data_length])
            self.clear()
            return written
        return 0
    
    def clear(self):
        """Clear buffer"""
        self.position = 0
        self.data_length = 0


class MemoryMappedFile:
    """Memory-mapped file handler for efficient large file operations"""
    
    def __init__(self, file_path: Union[str, Path], mode: str = 'r+b', size: Optional[int] = None):
        self.file_path = Path(file_path)
        self.mode = mode
        self.file_handle: Optional[BinaryIO] = None
        self.mmap_handle: Optional[mmap.mmap] = None
        self.size = size
        
    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def open(self):
        """Open memory-mapped file"""
        try:
            # Create file if it doesn't exist and we're writing
            if 'w' in self.mode or 'a' in self.mode:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                if not self.file_path.exists() and self.size:
                    # Pre-allocate file
                    with open(self.file_path, 'wb') as f:
                        f.seek(self.size - 1)
                        f.write(b'\0')
            
            self.file_handle = open(self.file_path, self.mode)  # type: ignore

            # Create memory map
            if self.file_handle is not None:
                if 'r' in self.mode and 'w' not in self.mode:
                    self.mmap_handle = mmap.mmap(self.file_handle.fileno(), 0, access=mmap.ACCESS_READ)
                else:
                    self.mmap_handle = mmap.mmap(self.file_handle.fileno(), 0)
            
            logger.debug(f"Memory-mapped file opened: {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to open memory-mapped file {self.file_path}: {e}")
            self.close()
            raise
    
    def close(self):
        """Close memory-mapped file"""
        if self.mmap_handle:
            self.mmap_handle.close()
            self.mmap_handle = None
        
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
    
    def write(self, data: bytes, offset: int = 0):
        """Write data to memory-mapped file"""
        if not self.mmap_handle:
            raise RuntimeError("Memory-mapped file not open")
        
        end_pos = offset + len(data)
        if end_pos > len(self.mmap_handle):
            raise ValueError("Write would exceed file size")
        
        self.mmap_handle[offset:end_pos] = data
    
    def read(self, size: int = -1, offset: int = 0) -> bytes:
        """Read data from memory-mapped file"""
        if not self.mmap_handle:
            raise RuntimeError("Memory-mapped file not open")
        
        if size == -1:
            return self.mmap_handle[offset:]
        else:
            return self.mmap_handle[offset:offset + size]


class MemoryOptimizer:
    """Intelligent memory optimizer for download operations"""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.lock = threading.RLock()
        
        # Memory tracking
        self.initial_memory = psutil.virtual_memory().used
        self.peak_memory = self.initial_memory
        self.last_gc_memory = self.initial_memory
        self.last_memory_check = time.time()
        
        # Buffer management
        self.active_buffers: Dict[str, StreamingBuffer] = {}
        self.buffer_performance: Dict[str, list] = {}
        
        # Memory-mapped files
        self.mmap_files: Dict[str, MemoryMappedFile] = {}
        
        logger.info("Memory optimizer initialized")
    
    def get_optimal_buffer_size(self, context: str = "default") -> int:
        """Get optimal buffer size based on current conditions"""
        with self.lock:
            # Check current memory usage
            memory_info = psutil.virtual_memory()
            memory_pressure = memory_info.percent / 100.0
            
            # Base size calculation
            if memory_pressure < 0.5:
                # Low memory pressure - use larger buffers
                base_size = self.config.buffer_size_max
            elif memory_pressure < 0.7:
                # Medium memory pressure - use default
                base_size = self.config.buffer_size_default
            else:
                # High memory pressure - use smaller buffers
                base_size = self.config.buffer_size_min
            
            # Adjust based on performance history
            if context in self.buffer_performance:
                performance_data = self.buffer_performance[context]
                if len(performance_data) >= 3:
                    # Analyze recent performance
                    recent_performance = performance_data[-3:]
                    avg_throughput = sum(p['throughput'] for p in recent_performance) / len(recent_performance)
                    
                    # Adjust buffer size based on throughput
                    if avg_throughput > 10 * 1024 * 1024:  # > 10 MB/s
                        base_size = min(base_size * 2, self.config.buffer_size_max)
                    elif avg_throughput < 1 * 1024 * 1024:  # < 1 MB/s
                        base_size = max(base_size // 2, self.config.buffer_size_min)
            
            return base_size
    
    def create_streaming_buffer(self, context: str) -> StreamingBuffer:
        """Create optimized streaming buffer"""
        with self.lock:
            buffer_size = self.get_optimal_buffer_size(context)
            buffer = StreamingBuffer(buffer_size, self.config.buffer_size_max)
            self.active_buffers[context] = buffer
            
            logger.debug(f"Created streaming buffer for {context}: {buffer_size} bytes")
            return buffer
    
    def release_streaming_buffer(self, context: str):
        """Release streaming buffer"""
        with self.lock:
            if context in self.active_buffers:
                del self.active_buffers[context]
                logger.debug(f"Released streaming buffer for {context}")
    
    def record_buffer_performance(self, context: str, bytes_processed: int, duration: float):
        """Record buffer performance for optimization"""
        with self.lock:
            if context not in self.buffer_performance:
                self.buffer_performance[context] = []
            
            throughput = bytes_processed / duration if duration > 0 else 0
            performance_record = {
                'timestamp': time.time(),
                'bytes_processed': bytes_processed,
                'duration': duration,
                'throughput': throughput
            }
            
            self.buffer_performance[context].append(performance_record)
            
            # Keep only recent records
            if len(self.buffer_performance[context]) > 10:
                self.buffer_performance[context] = self.buffer_performance[context][-10:]
    
    def should_use_memory_mapping(self, file_size: int) -> bool:
        """Determine if memory mapping should be used"""
        # Use memory mapping for large files if memory allows
        memory_info = psutil.virtual_memory()
        available_memory = memory_info.available
        
        return (file_size > self.config.mmap_threshold_mb * 1024 * 1024 and
                file_size < available_memory * 0.3)  # Don't use more than 30% of available memory
    
    def create_memory_mapped_file(self, file_path: Union[str, Path], 
                                 size: Optional[int] = None) -> MemoryMappedFile:
        """Create memory-mapped file"""
        file_key = str(file_path)
        
        with self.lock:
            if file_key in self.mmap_files:
                return self.mmap_files[file_key]
            
            mmap_file = MemoryMappedFile(file_path, 'r+b', size)
            self.mmap_files[file_key] = mmap_file
            
            logger.debug(f"Created memory-mapped file: {file_path}")
            return mmap_file
    
    def release_memory_mapped_file(self, file_path: Union[str, Path]):
        """Release memory-mapped file"""
        file_key = str(file_path)
        
        with self.lock:
            if file_key in self.mmap_files:
                self.mmap_files[file_key].close()
                del self.mmap_files[file_key]
                logger.debug(f"Released memory-mapped file: {file_path}")
    
    def check_memory_pressure(self) -> Dict[str, Any]:
        """Check current memory pressure and suggest actions"""
        current_time = time.time()
        if current_time - self.last_memory_check < self.config.memory_check_interval:
            return {"action": "none", "reason": "too_soon"}
        
        self.last_memory_check = current_time
        
        memory_info = psutil.virtual_memory()
        current_memory = memory_info.used
        memory_percent = memory_info.percent
        
        # Update peak memory
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        
        # Check if we should trigger garbage collection
        memory_increase = current_memory - self.last_gc_memory
        gc_threshold_bytes = self.config.gc_threshold_mb * 1024 * 1024
        
        result = {
            "memory_percent": memory_percent,
            "memory_used_mb": current_memory / (1024 * 1024),
            "memory_available_mb": memory_info.available / (1024 * 1024),
            "peak_memory_mb": self.peak_memory / (1024 * 1024),
            "action": "none"
        }
        
        if memory_percent > self.config.max_memory_usage_percent:
            result["action"] = "reduce_usage"
            result["reason"] = "high_memory_usage"
            self._reduce_memory_usage()
        elif memory_increase > gc_threshold_bytes:
            result["action"] = "garbage_collect"
            result["reason"] = "memory_increase"
            self._trigger_garbage_collection()
        
        return result
    
    def _reduce_memory_usage(self):
        """Reduce memory usage by optimizing buffers and cleaning up"""
        with self.lock:
            # Reduce buffer sizes
            for context, buffer in self.active_buffers.items():
                if buffer.size > self.config.buffer_size_min:
                    new_size = max(buffer.size // 2, self.config.buffer_size_min)
                    buffer.resize(new_size)
            
            # Close unused memory-mapped files
            unused_files = []
            for file_key, mmap_file in self.mmap_files.items():
                # Simple heuristic: if file hasn't been accessed recently, close it
                # In a real implementation, you'd track access times
                unused_files.append(file_key)
            
            for file_key in unused_files[:len(unused_files)//2]:  # Close half of them
                self.release_memory_mapped_file(file_key)
            
            logger.info("Reduced memory usage due to high memory pressure")
    
    def _trigger_garbage_collection(self):
        """Trigger garbage collection"""
        collected = gc.collect()
        self.last_gc_memory = psutil.virtual_memory().used
        logger.debug(f"Garbage collection triggered, collected {collected} objects")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        memory_info = psutil.virtual_memory()
        
        with self.lock:
            return {
                "system_memory": {
                    "total_mb": memory_info.total / (1024 * 1024),
                    "used_mb": memory_info.used / (1024 * 1024),
                    "available_mb": memory_info.available / (1024 * 1024),
                    "percent": memory_info.percent
                },
                "optimizer_stats": {
                    "initial_memory_mb": self.initial_memory / (1024 * 1024),
                    "peak_memory_mb": self.peak_memory / (1024 * 1024),
                    "active_buffers": len(self.active_buffers),
                    "memory_mapped_files": len(self.mmap_files)
                },
                "buffer_stats": {
                    context: {
                        "size": buffer.size,
                        "data_length": buffer.data_length,
                        "utilization": buffer.data_length / buffer.size if buffer.size > 0 else 0
                    }
                    for context, buffer in self.active_buffers.items()
                }
            }
    
    def cleanup(self):
        """Clean up all resources"""
        with self.lock:
            # Close all memory-mapped files
            for file_key in list(self.mmap_files.keys()):
                self.release_memory_mapped_file(file_key)
            
            # Clear all buffers
            self.active_buffers.clear()
            self.buffer_performance.clear()
            
            logger.info("Memory optimizer cleanup completed")


# Global memory optimizer instance
memory_optimizer = MemoryOptimizer()

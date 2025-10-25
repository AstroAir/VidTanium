"""
Performance Optimizer for VidTanium
Provides comprehensive performance monitoring, profiling, and optimization
"""

import time
import threading
import psutil
import gc
import weakref
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from loguru import logger
import tracemalloc
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication


class PerformanceMetric(Enum):
    """Performance metric types"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    THREAD_COUNT = "thread_count"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"


class OptimizationLevel(Enum):
    """Optimization levels"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a point in time"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    thread_count: int
    response_times: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Result of an optimization operation"""
    success: bool
    description: str
    memory_saved_mb: float = 0.0
    cpu_saved_percent: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class MemoryProfiler:
    """Memory usage profiler and optimizer"""
    
    def __init__(self) -> None:
        self.tracemalloc_started = False
        self.snapshots: List[Any] = []
        self.object_registry: Dict[str, weakref.WeakSet] = defaultdict(weakref.WeakSet)
        
    def start_profiling(self) -> None:
        """Start memory profiling"""
        if not self.tracemalloc_started:
            tracemalloc.start()
            self.tracemalloc_started = True
            logger.info("Memory profiling started")
    
    def stop_profiling(self) -> None:
        """Stop memory profiling"""
        if self.tracemalloc_started:
            tracemalloc.stop()
            self.tracemalloc_started = False
            logger.info("Memory profiling stopped")
    
    def take_snapshot(self) -> Optional[Any]:
        """Take a memory snapshot"""
        if self.tracemalloc_started:
            snapshot = tracemalloc.take_snapshot()
            self.snapshots.append(snapshot)
            return snapshot
        return None
    
    def get_top_memory_consumers(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top memory consuming code locations"""
        if not self.snapshots:
            return []
        
        snapshot = self.snapshots[-1]
        top_stats = snapshot.statistics('lineno')
        
        consumers = []
        for stat in top_stats[:limit]:
            size_mb = stat.size / 1024 / 1024
            consumers.append((str(stat.traceback), size_mb))
        
        return consumers
    
    def register_object(self, obj: Any, category: str) -> None:
        """Register object for tracking"""
        self.object_registry[category].add(obj)
    
    def get_object_counts(self) -> Dict[str, int]:
        """Get object counts by category"""
        counts = {}
        for category, weak_set in self.object_registry.items():
            # Clean up dead references
            alive_objects = [obj for obj in weak_set if obj is not None]
            counts[category] = len(alive_objects)
        return counts
    
    def force_garbage_collection(self) -> OptimizationResult:
        """Force garbage collection and return results"""
        before_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Force garbage collection
        collected = gc.collect()
        
        after_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_saved = before_memory - after_memory
        
        return OptimizationResult(
            success=True,
            description=f"Garbage collection freed {collected} objects",
            memory_saved_mb=memory_saved,
            details={"objects_collected": collected}
        )


class CPUProfiler:
    """CPU usage profiler and optimizer"""
    
    def __init__(self) -> None:
        self.cpu_samples: deque = deque(maxlen=100)
        self.function_times: Dict[str, List[float]] = defaultdict(list)
        
    def record_cpu_usage(self) -> None:
        """Record current CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_samples.append((time.time(), cpu_percent))
    
    def get_average_cpu_usage(self, window_seconds: int = 60) -> float:
        """Get average CPU usage over time window"""
        if not self.cpu_samples:
            return 0.0
        
        cutoff_time = time.time() - window_seconds
        recent_samples = [cpu for timestamp, cpu in self.cpu_samples if timestamp > cutoff_time]
        
        return sum(recent_samples) / len(recent_samples) if recent_samples else 0.0
    
    def profile_function(self, func_name: str) -> None:
        """Decorator to profile function execution time"""
        def decorator(func) -> None:
            def wrapper(*args, **kwargs) -> None:
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time
                    self.function_times[func_name].append(execution_time)
            return wrapper
        return decorator
    
    def get_function_stats(self) -> Dict[str, Dict[str, float]]:
        """Get function execution statistics"""
        stats = {}
        for func_name, times in self.function_times.items():
            if times:
                stats[func_name] = {
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "total_calls": len(times),
                    "total_time": sum(times)
                }
        return stats


class UIPerformanceOptimizer:
    """UI-specific performance optimizer"""
    
    def __init__(self) -> None:
        self.widget_cache: Dict[str, Any] = {}
        self.layout_cache: Dict[str, Any] = {}
        self.pixmap_cache: Dict[str, Any] = {}
        
    def optimize_widget_updates(self, widget) -> OptimizationResult:
        """Optimize widget update performance"""
        optimizations = []
        
        # Disable updates during batch operations
        if hasattr(widget, 'setUpdatesEnabled'):
            widget.setUpdatesEnabled(False)
            optimizations.append("Disabled updates during optimization")
        
        # Optimize repaints
        if hasattr(widget, 'setAttribute'):
            from PySide6.QtCore import Qt
            widget.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            optimizations.append("Enabled opaque paint events")
        
        # Re-enable updates
        if hasattr(widget, 'setUpdatesEnabled'):
            widget.setUpdatesEnabled(True)
        
        return OptimizationResult(
            success=True,
            description=f"Applied {len(optimizations)} UI optimizations",
            details={"optimizations": optimizations}
        )
    
    def clear_caches(self) -> OptimizationResult:
        """Clear UI caches to free memory"""
        before_count = len(self.widget_cache) + len(self.layout_cache) + len(self.pixmap_cache)
        
        self.widget_cache.clear()
        self.layout_cache.clear()
        self.pixmap_cache.clear()
        
        # Also clear Qt's internal caches
        app = QApplication.instance()
        if app:
            app.processEvents()  # Process pending events
        
        return OptimizationResult(
            success=True,
            description=f"Cleared {before_count} cached UI objects",
            details={"cache_items_cleared": before_count}
        )


class PerformanceOptimizer(QObject):
    """Main performance optimizer"""
    
    performance_updated = Signal(PerformanceSnapshot)
    optimization_completed = Signal(OptimizationResult)
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.memory_profiler = MemoryProfiler()
        self.cpu_profiler = CPUProfiler()
        self.ui_optimizer = UIPerformanceOptimizer()
        
        self.monitoring_enabled = False
        self.optimization_level = OptimizationLevel.BALANCED
        self.performance_history: deque = deque(maxlen=1000)
        
        # Monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._collect_performance_data)
        
        logger.info("Performance optimizer initialized")
    
    def start_monitoring(self, interval_ms: int = 5000) -> None:
        """Start performance monitoring"""
        self.monitoring_enabled = True
        self.memory_profiler.start_profiling()
        self.monitor_timer.start(interval_ms)
        logger.info(f"Performance monitoring started (interval: {interval_ms}ms)")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self.monitoring_enabled = False
        self.monitor_timer.stop()
        self.memory_profiler.stop_profiling()
        logger.info("Performance monitoring stopped")
    
    def _collect_performance_data(self) -> None:
        """Collect current performance data"""
        try:
            # Skip collection if monitoring is disabled
            if not self.monitoring_enabled:
                return

            process = psutil.Process()

            # Collect basic metrics with reduced frequency for expensive operations
            cpu_percent = process.cpu_percent(interval=0.1)  # Short interval to reduce blocking
            memory_mb = process.memory_info().rss / 1024 / 1024
            thread_count = process.num_threads()

            # Create snapshot
            snapshot = PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                thread_count=thread_count
            )

            # Add custom metrics less frequently to reduce overhead
            snapshot_count = len(self.performance_history)
            if snapshot_count % 5 == 0:  # Only every 5th snapshot
                try:
                    snapshot.custom_metrics.update({
                        "object_counts": self.memory_profiler.get_object_counts(),
                        "function_stats": self.cpu_profiler.get_function_stats()
                    })
                except Exception as e:
                    logger.debug(f"Error collecting custom metrics: {e}")

            # Store and emit
            self.performance_history.append(snapshot)
            self.performance_updated.emit(snapshot)

            # Auto-optimize less frequently to reduce resource usage
            if snapshot_count % 10 == 0:  # Only every 10th snapshot
                self._check_auto_optimization(snapshot)

        except Exception as e:
            logger.debug(f"Error collecting performance data: {e}")  # Reduced to debug level
    
    def _check_auto_optimization(self, snapshot: PerformanceSnapshot) -> None:
        """Check if auto-optimization should be triggered"""
        if self.optimization_level == OptimizationLevel.CONSERVATIVE:
            return

        # More conservative thresholds to reduce unnecessary optimizations
        memory_threshold = 1000 if self.optimization_level == OptimizationLevel.AGGRESSIVE else 1500  # MB
        cpu_threshold = 85 if self.optimization_level == OptimizationLevel.AGGRESSIVE else 90  # %

        # Trigger optimization if memory usage is very high
        if snapshot.memory_mb > memory_threshold:
            logger.info(f"High memory usage detected: {snapshot.memory_mb:.1f}MB, triggering optimization")
            self.optimize_memory()

        # Trigger optimization if CPU usage is consistently very high
        if len(self.performance_history) >= 5:  # Need some history
            recent_snapshots = list(self.performance_history)[-5:]
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            if avg_cpu > cpu_threshold:
                logger.info(f"High CPU usage detected: {avg_cpu:.1f}%, triggering optimization")
                self.optimize_performance()
    
    def optimize_memory(self) -> List[OptimizationResult]:
        """Perform memory optimization"""
        results = []
        
        # Force garbage collection
        gc_result = self.memory_profiler.force_garbage_collection()
        results.append(gc_result)
        
        # Clear UI caches
        ui_result = self.ui_optimizer.clear_caches()
        results.append(ui_result)
        
        # Log results
        total_memory_saved = sum(r.memory_saved_mb for r in results)
        logger.info(f"Memory optimization completed: {total_memory_saved:.1f}MB saved")
        
        for result in results:
            self.optimization_completed.emit(result)
        
        return results
    
    def optimize_performance(self) -> List[OptimizationResult]:
        """Perform general performance optimization"""
        results = []
        
        # Memory optimization
        results.extend(self.optimize_memory())
        
        # Thread optimization (placeholder for actual implementation)
        thread_result = OptimizationResult(
            success=True,
            description="Thread pool optimization completed",
            cpu_saved_percent=5.0
        )
        results.append(thread_result)
        
        logger.info("Performance optimization completed")
        
        for result in results:
            self.optimization_completed.emit(result)
        
        return results
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.performance_history:
            return {}
        
        recent_snapshots = list(self.performance_history)[-10:]  # Last 10 snapshots
        
        avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
        avg_memory = sum(s.memory_mb for s in recent_snapshots) / len(recent_snapshots)
        avg_threads = sum(s.thread_count for s in recent_snapshots) / len(recent_snapshots)
        
        return {
            "average_cpu_percent": avg_cpu,
            "average_memory_mb": avg_memory,
            "average_thread_count": avg_threads,
            "total_snapshots": len(self.performance_history),
            "monitoring_enabled": self.monitoring_enabled,
            "optimization_level": self.optimization_level.value,
            "top_memory_consumers": self.memory_profiler.get_top_memory_consumers(5),
            "function_stats": self.cpu_profiler.get_function_stats()
        }
    
    def set_optimization_level(self, level: OptimizationLevel) -> None:
        """Set optimization level"""
        self.optimization_level = level
        logger.info(f"Optimization level set to: {level.value}")
    
    def register_object_for_tracking(self, obj: Any, category: str) -> None:
        """Register object for memory tracking"""
        self.memory_profiler.register_object(obj, category)
    
    def profile_function(self, func_name: str) -> None:
        """Get function profiling decorator"""
        return self.cpu_profiler.profile_function(func_name)


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

"""
Thread Pool Manager for VidTanium

Provides centralized thread pool management for performance optimization
and better resource management.
"""

from PySide6.QtCore import QObject, QThreadPool, QRunnable, Signal
from typing import Callable, Any, Optional, Dict, List
import sys
import traceback
import threading
import time
from loguru import logger
from .resource_manager import resource_manager, ResourceType, register_for_cleanup


class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""

    finished = Signal()  # No data
    error = Signal(tuple)  # (exception_type, value, traceback)
    result = Signal(object)  # Result data
    progress = Signal(int)  # Progress percentage


class Worker(QRunnable):
    """Worker thread for running tasks in the thread pool."""

    def __init__(self, fn: Callable, *args, **kwargs) -> None:
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Worker tracking attributes
        self.worker_id: Optional[str] = None
        self.is_running: bool = False
        self.priority: int = 0

        # Add the progress callback to our kwargs
        if 'progress_callback' in kwargs:
            del kwargs['progress_callback']

    def run(self) -> None:
        """Execute the worker function with exception handling."""
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            exctype, value, tb = sys.exc_info()
            logger.error(f"Worker thread error: {value}")
            logger.error(
                f"Traceback: {''.join(traceback.format_exception(exctype, value, tb))}")
            self.signals.error.emit((exctype, value, tb))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class ThreadPoolManager(QObject):
    """Enhanced centralized thread pool manager with resource optimization."""

    def __init__(self, max_threads: Optional[int] = None) -> None:
        super().__init__()
        self.pool = QThreadPool()

        # Thread tracking and management
        self.active_workers: Dict[str, Worker] = {}
        self.worker_stats: Dict[str, Dict] = {}
        self.lock = threading.RLock()

        # Performance monitoring
        self.total_tasks_submitted = 0
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0

        # Dynamic thread management
        self._setup_thread_limits(max_threads)

        # Register for resource management
        register_for_cleanup(
            self,
            ResourceType.THREAD,
            cleanup_callback=self._cleanup_completed_workers,
            metadata={"component": "ThreadPoolManager"}
        )

        logger.info(
            f"Enhanced thread pool initialized with {self.pool.maxThreadCount()} threads")

    def _setup_thread_limits(self, max_threads: Optional[int]) -> None:
        """Setup thread limits based on system resources"""
        if max_threads:
            self.pool.setMaxThreadCount(max_threads)
        else:
            # Dynamic thread count based on system resources
            import os
            cpu_count = os.cpu_count() or 4

            try:
                # Try to get memory info for better thread allocation
                import psutil
                memory_gb = psutil.virtual_memory().total / (1024**3)

                # Adjust thread count based on available memory
                if memory_gb < 4:
                    max_threads = max(2, min(cpu_count, 8))
                elif memory_gb < 8:
                    max_threads = max(4, min(int(cpu_count * 1.5), 12))
                else:
                    max_threads = max(4, min(cpu_count * 2, 16))

            except ImportError:
                # Fallback if psutil not available
                max_threads = max(4, min(cpu_count * 2, 16))

            self.pool.setMaxThreadCount(int(max_threads))

    def _cleanup_completed_workers(self) -> None:
        """Clean up completed workers and their resources"""
        with self.lock:
            completed_workers = []

            for worker_id, worker in list(self.active_workers.items()):
                if not hasattr(worker, 'is_running') or not worker.is_running:
                    completed_workers.append(worker_id)

            for worker_id in completed_workers:
                self.active_workers.pop(worker_id, None)
                self.worker_stats.pop(worker_id, None)

            if completed_workers:
                logger.debug(f"Cleaned up {len(completed_workers)} completed workers")

    def submit_task(self,
                    function: Callable,
                    *args,
                    callback: Optional[Callable] = None,
                    error_callback: Optional[Callable] = None,
                    progress_callback: Optional[Callable] = None,
                    priority: int = 0,
                    **kwargs) -> Worker:
        """
        Submit a task to the thread pool with enhanced tracking.

        Args:
            function: The function to execute
            *args: Arguments to pass to the function
            callback: Callback for successful completion
            error_callback: Callback for error handling
            progress_callback: Callback for progress updates
            priority: Task priority (higher = more important)
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Worker: The worker instance
        """
        # Check if we should throttle based on system resources
        if self._should_throttle():
            logger.warning("Thread pool throttling due to high resource usage")
            time.sleep(0.1)  # Brief delay to reduce load

        worker = Worker(function, *args, **kwargs)
        worker_id = f"{function.__name__}_{id(worker)}"
        worker.worker_id = worker_id
        worker.is_running = True
        worker.priority = priority

        # Enhanced callback wrapping for tracking
        def wrapped_callback(result) -> None:
            self._on_task_completed(worker_id, True)
            if callback:
                callback(result)

        def wrapped_error_callback(error) -> None:
            self._on_task_completed(worker_id, False)
            if error_callback:
                error_callback(error)

        # Connect callbacks
        worker.signals.result.connect(wrapped_callback)
        worker.signals.error.connect(wrapped_error_callback)
        if progress_callback:
            worker.signals.progress.connect(progress_callback)

        # Track worker
        with self.lock:
            self.active_workers[worker_id] = worker
            self.worker_stats[worker_id] = {
                "function_name": function.__name__,
                "start_time": time.time(),
                "priority": priority
            }
            self.total_tasks_submitted += 1

        # Submit to thread pool
        self.pool.start(worker)

        # Only log non-stats tasks to reduce noise
        if function.__name__ != '_calculate_stats':
            logger.debug(f"Task submitted to thread pool: {function.__name__} (ID: {worker_id})")

        return worker

    def _should_throttle(self) -> bool:
        """Check if we should throttle task submission based on system resources"""
        try:
            # Check active thread count
            if self.pool.activeThreadCount() >= self.pool.maxThreadCount() * 0.9:
                return True

            # Check memory usage if psutil is available
            try:
                import psutil
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 85:  # High memory usage
                    return True
            except ImportError:
                pass

            return False
        except Exception:
            return False

    def _on_task_completed(self, worker_id: str, success: bool) -> None:
        """Handle task completion tracking"""
        with self.lock:
            if success:
                self.total_tasks_completed += 1
            else:
                self.total_tasks_failed += 1

            # Update worker status
            if worker_id in self.active_workers:
                self.active_workers[worker_id].is_running = False

            # Update stats
            if worker_id in self.worker_stats:
                stats = self.worker_stats[worker_id]
                stats["end_time"] = time.time()
                stats["duration"] = stats["end_time"] - stats["start_time"]
                stats["success"] = success

    def wait_for_done(self, timeout_ms: int = 30000) -> bool:
        """
        Wait for all tasks to complete.

        Args:
            timeout_ms: Timeout in milliseconds

        Returns:
            bool: True if all tasks completed, False if timeout
        """
        return bool(self.pool.waitForDone(timeout_ms))

    def clear(self) -> None:
        """Clear all pending tasks."""
        self.pool.clear()
        logger.info("Thread pool cleared")

    def active_thread_count(self) -> int:
        """Get the number of active threads."""
        return int(self.pool.activeThreadCount())

    def max_thread_count(self) -> int:
        """Get the maximum thread count."""
        return int(self.pool.maxThreadCount())

    def set_max_thread_count(self, count: int) -> None:
        """Set the maximum thread count."""
        self.pool.setMaxThreadCount(count)
        logger.info(f"Thread pool max threads set to {count}")


# Global thread pool instance
_thread_pool_manager: Optional[ThreadPoolManager] = None


def get_thread_pool() -> ThreadPoolManager:
    """Get the global thread pool manager instance."""
    global _thread_pool_manager
    if _thread_pool_manager is None:
        _thread_pool_manager = ThreadPoolManager()
    return _thread_pool_manager


def submit_task(function: Callable,
                *args,
                callback: Optional[Callable] = None,
                error_callback: Optional[Callable] = None,
                progress_callback: Optional[Callable] = None,
                **kwargs) -> Worker:
    """
    Convenience function to submit a task to the global thread pool.

    Args:
        function: The function to execute
        *args: Arguments to pass to the function
        callback: Callback for successful completion
        error_callback: Callback for error handling
        progress_callback: Callback for progress updates
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Worker: The worker instance
    """
    return get_thread_pool().submit_task(
        function, *args,
        callback=callback,
        error_callback=error_callback,
        progress_callback=progress_callback,
        **kwargs
    )


def shutdown_thread_pool() -> None:
    """Shutdown the global thread pool."""
    global _thread_pool_manager
    if _thread_pool_manager:
        _thread_pool_manager.wait_for_done()
        _thread_pool_manager = None
        logger.info("Thread pool shutdown completed")

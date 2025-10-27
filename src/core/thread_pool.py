"""
Thread Pool Manager for VidTanium

Provides centralized thread pool management for performance optimization
and better resource management. Pure Python implementation without Qt dependencies.
"""

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Optional, Dict, List, Tuple
import sys
import traceback
import threading
import time
from loguru import logger
from .resource_manager import resource_manager, ResourceType, register_for_cleanup


class WorkerCallbacks:
    """Container for worker callbacks (replaces Qt signals)"""

    def __init__(self):
        self.on_finished: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[Tuple], None]] = None
        self.on_result: Optional[Callable[[Any], None]] = None
        self.on_progress: Optional[Callable[[int], None]] = None


class Worker:
    """Worker task for running in the thread pool (replaces QRunnable)"""

    def __init__(self, fn: Callable, *args, **kwargs) -> None:
        # Store constructor arguments
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.callbacks = WorkerCallbacks()

        # Worker tracking attributes
        self.worker_id: Optional[str] = None
        self.is_running: bool = False
        self.priority: int = 0
        self.future: Optional[Future] = None

        # Extract progress callback if provided
        self.progress_callback = kwargs.pop('progress_callback', None)

    def __call__(self) -> Any:
        """Execute the worker function with exception handling"""
        self.is_running = True
        try:
            result = self.fn(*self.args, **self.kwargs)
            if self.callbacks.on_result:
                self.callbacks.on_result(result)
            return result
        except Exception:
            exctype, value, tb = sys.exc_info()
            logger.error(f"Worker thread error: {value}")
            logger.error(
                f"Traceback: {''.join(traceback.format_exception(exctype, value, tb))}")
            if self.callbacks.on_error:
                self.callbacks.on_error((exctype, value, tb))
            raise
        finally:
            self.is_running = False
            if self.callbacks.on_finished:
                self.callbacks.on_finished()


class ThreadPoolManager:
    """Enhanced centralized thread pool manager with resource optimization (Pure Python)"""

    def __init__(self, max_threads: Optional[int] = None) -> None:
        # Determine thread count
        self._max_threads = self._calculate_thread_count(max_threads)

        # Create thread pool executor
        self.pool = ThreadPoolExecutor(
            max_workers=self._max_threads,
            thread_name_prefix="VidTanium-Worker"
        )

        # Thread tracking and management
        self.active_workers: Dict[str, Worker] = {}
        self.worker_stats: Dict[str, Dict] = {}
        self.lock = threading.RLock()

        # Performance monitoring
        self.total_tasks_submitted = 0
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0

        # Shutdown flag
        self._shutdown = False

        # Register for resource management
        register_for_cleanup(
            self,
            ResourceType.THREAD,
            cleanup_callback=self._cleanup_completed_workers,
            metadata={"component": "ThreadPoolManager"}
        )

        logger.info(
            f"Enhanced thread pool initialized with {self._max_threads} threads")

    def _calculate_thread_count(self, max_threads: Optional[int]) -> int:
        """Calculate optimal thread count based on system resources"""
        if max_threads:
            return max_threads

        # Dynamic thread count based on system resources
        import os
        cpu_count = os.cpu_count() or 4

        try:
            # Try to get memory info for better thread allocation
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)

            # Adjust thread count based on available memory
            if memory_gb < 4:
                calculated_threads = max(2, min(cpu_count, 8))
            elif memory_gb < 8:
                calculated_threads = max(4, min(int(cpu_count * 1.5), 12))
            else:
                calculated_threads = max(4, min(cpu_count * 2, 16))

        except ImportError:
            # Fallback if psutil not available
            calculated_threads = max(4, min(cpu_count * 2, 16))

        return int(calculated_threads)

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
        if self._shutdown:
            raise RuntimeError("Cannot submit task to shutdown thread pool")

        # Check if we should throttle based on system resources
        if self._should_throttle():
            logger.warning("Thread pool throttling due to high resource usage")
            time.sleep(0.1)  # Brief delay to reduce load

        worker = Worker(function, *args, **kwargs)
        worker_id = f"{function.__name__}_{id(worker)}"
        worker.worker_id = worker_id
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

        # Set callbacks on worker
        worker.callbacks.on_result = wrapped_callback
        worker.callbacks.on_error = wrapped_error_callback
        if progress_callback:
            worker.callbacks.on_progress = progress_callback

        # Track worker
        with self.lock:
            self.active_workers[worker_id] = worker
            self.worker_stats[worker_id] = {
                "function_name": function.__name__,
                "start_time": time.time(),
                "priority": priority
            }
            self.total_tasks_submitted += 1

        # Submit to thread pool and store future
        worker.future = self.pool.submit(worker)

        # Only log non-stats tasks to reduce noise
        if function.__name__ != '_calculate_stats':
            logger.debug(f"Task submitted to thread pool: {function.__name__} (ID: {worker_id})")

        return worker

    def _should_throttle(self) -> bool:
        """Check if we should throttle task submission based on system resources"""
        try:
            # Check active worker count
            with self.lock:
                active_count = sum(1 for w in self.active_workers.values() if w.is_running)

            if active_count >= self._max_threads * 0.9:
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
        timeout_sec = timeout_ms / 1000.0
        try:
            # Shutdown with wait, but don't prevent new submissions
            # Just wait for current tasks
            with self.lock:
                futures = [w.future for w in self.active_workers.values() if w.future]

            if not futures:
                return True

            # Wait for all futures with timeout
            from concurrent.futures import wait, FIRST_COMPLETED, ALL_COMPLETED
            done, not_done = wait(futures, timeout=timeout_sec, return_when=ALL_COMPLETED)

            return len(not_done) == 0
        except Exception as e:
            logger.error(f"Error waiting for tasks: {e}")
            return False

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the thread pool"""
        self._shutdown = True
        self.pool.shutdown(wait=wait)
        logger.info("Thread pool shutdown completed")

    def active_thread_count(self) -> int:
        """Get the number of active threads"""
        with self.lock:
            return sum(1 for w in self.active_workers.values() if w.is_running)

    def max_thread_count(self) -> int:
        """Get the maximum thread count"""
        return self._max_threads

    def set_max_thread_count(self, count: int) -> None:
        """
        Set the maximum thread count.
        Note: ThreadPoolExecutor doesn't support dynamic resizing,
        so this will only affect new pool instances.
        """
        logger.warning("ThreadPoolExecutor doesn't support dynamic thread count changes")
        logger.info(f"Thread pool max threads would be set to {count} on next restart")


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


def shutdown_thread_pool(wait: bool = True) -> None:
    """Shutdown the global thread pool."""
    global _thread_pool_manager
    if _thread_pool_manager:
        _thread_pool_manager.shutdown(wait=wait)
        _thread_pool_manager = None
        logger.info("Global thread pool shutdown completed")

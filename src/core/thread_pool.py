"""
Thread Pool Manager for VidTanium

Provides centralized thread pool management for performance optimization
and better resource management.
"""

from PySide6.QtCore import QObject, QThreadPool, QRunnable, Signal
from typing import Callable, Any, Optional
import sys
import traceback
from loguru import logger


class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""

    finished = Signal()  # No data
    error = Signal(tuple)  # (exception_type, value, traceback)
    result = Signal(object)  # Result data
    progress = Signal(int)  # Progress percentage


class Worker(QRunnable):
    """Worker thread for running tasks in the thread pool."""

    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the progress callback to our kwargs
        if 'progress_callback' in kwargs:
            del kwargs['progress_callback']

    def run(self):
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
    """Centralized thread pool manager for the application."""

    def __init__(self, max_threads: Optional[int] = None):
        super().__init__()
        self.pool = QThreadPool()

        if max_threads:
            self.pool.setMaxThreadCount(max_threads)
        else:
            # Set reasonable defaults based on CPU count
            import os
            cpu_count = os.cpu_count() or 4
            self.pool.setMaxThreadCount(max(4, min(cpu_count * 2, 16)))

        logger.info(
            f"Thread pool initialized with {self.pool.maxThreadCount()} threads")

    def submit_task(self,
                    function: Callable,
                    *args,
                    callback: Optional[Callable] = None,
                    error_callback: Optional[Callable] = None,
                    progress_callback: Optional[Callable] = None,
                    **kwargs) -> Worker:
        """
        Submit a task to the thread pool.

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
        worker = Worker(function, *args, **kwargs)

        # Connect callbacks if provided
        if callback:
            worker.signals.result.connect(callback)
        if error_callback:
            worker.signals.error.connect(error_callback)
        if progress_callback:
            worker.signals.progress.connect(progress_callback)

        # Submit to thread pool
        self.pool.start(worker)

        # Only log non-stats tasks to reduce noise
        if function.__name__ != '_calculate_stats':
            logger.debug(f"Task submitted to thread pool: {function.__name__}")

        return worker

    def wait_for_done(self, timeout_ms: int = 30000) -> bool:
        """
        Wait for all tasks to complete.

        Args:
            timeout_ms: Timeout in milliseconds

        Returns:
            bool: True if all tasks completed, False if timeout
        """
        return bool(self.pool.waitForDone(timeout_ms))

    def clear(self):
        """Clear all pending tasks."""
        self.pool.clear()
        logger.info("Thread pool cleared")

    def active_thread_count(self) -> int:
        """Get the number of active threads."""
        return int(self.pool.activeThreadCount())

    def max_thread_count(self) -> int:
        """Get the maximum thread count."""
        return int(self.pool.maxThreadCount())

    def set_max_thread_count(self, count: int):
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


def shutdown_thread_pool():
    """Shutdown the global thread pool."""
    global _thread_pool_manager
    if _thread_pool_manager:
        _thread_pool_manager.wait_for_done()
        _thread_pool_manager = None
        logger.info("Thread pool shutdown completed")

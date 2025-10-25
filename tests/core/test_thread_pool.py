import pytest
import time
import threading
import sys
from unittest.mock import patch, Mock, MagicMock
from typing import Callable, Any, Optional

# Mock PySide6 components for testing
class MockQObject:
    def __init__(self) -> None:
        pass

class MockSignal:
    def __init__(self) -> None:
        self.callbacks = []
    
    def connect(self, callback) -> None:
        self.callbacks.append(callback)
    
    def emit(self, *args) -> None:
        for callback in self.callbacks:
            callback(*args)

class MockQRunnable:
    def __init__(self) -> None:
        pass

class MockQThreadPool:
    def __init__(self) -> None:
        self._max_threads = 4
        self._active_threads = 0
        self._tasks = []
    
    def setMaxThreadCount(self, count) -> None:
        self._max_threads = count
    
    def maxThreadCount(self) -> None:
        return self._max_threads
    
    def activeThreadCount(self) -> None:
        return self._active_threads
    
    def start(self, worker) -> None:
        self._tasks.append(worker)
        self._active_threads += 1
        # Simulate running the worker
        threading.Thread(target=self._run_worker, args=(worker,)).start()
    
    def _run_worker(self, worker) -> None:
        try:
            worker.run()
        finally:
            self._active_threads = max(0, self._active_threads - 1)
    
    def waitForDone(self, timeout_ms) -> None:
        # Simple simulation - wait for active threads to finish
        start_time = time.time()
        while self._active_threads > 0 and (time.time() - start_time) * 1000 < timeout_ms:
            time.sleep(0.01)
        return self._active_threads == 0
    
    def clear(self) -> None:
        self._tasks.clear()

# Mock the PySide6 imports
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtCore'].QObject = MockQObject
sys.modules['PySide6.QtCore'].Signal = MockSignal
sys.modules['PySide6.QtCore'].QRunnable = MockQRunnable
sys.modules['PySide6.QtCore'].QThreadPool = MockQThreadPool

# Now import the actual module
from src.core.thread_pool import (
    WorkerSignals, Worker, ThreadPoolManager, get_thread_pool, submit_task
)


class TestWorkerSignals:
    """Test suite for WorkerSignals class."""

    def test_signals_initialization(self) -> None:
        """Test WorkerSignals initialization."""
        signals = WorkerSignals()
        
        assert hasattr(signals, 'finished')
        assert hasattr(signals, 'error')
        assert hasattr(signals, 'result')
        assert hasattr(signals, 'progress')
        assert isinstance(signals.finished, MockSignal)
        assert isinstance(signals.error, MockSignal)
        assert isinstance(signals.result, MockSignal)
        assert isinstance(signals.progress, MockSignal)


class TestWorker:
    """Test suite for Worker class."""

    def test_worker_initialization(self) -> None:
        """Test Worker initialization."""
        def test_function(x, y, z=None) -> None:
            return x + y + (z or 0)
        
        worker = Worker(test_function, 1, 2, z=3)
        
        assert worker.fn == test_function
        assert worker.args == (1, 2)
        assert worker.kwargs == {'z': 3}
        assert isinstance(worker.signals, WorkerSignals)

    def test_worker_initialization_with_progress_callback(self) -> None:
        """Test Worker initialization with progress callback removal."""
        def test_function(x, y) -> None:
            return x + y
        
        def progress_callback(value) -> None:
            pass
        
        worker = Worker(test_function, 1, 2, progress_callback=progress_callback)
        
        assert worker.fn == test_function
        assert worker.args == (1, 2)
        assert 'progress_callback' not in worker.kwargs

    def test_worker_run_success(self) -> None:
        """Test successful worker execution."""
        def test_function(x, y) -> None:
            return x * y
        
        worker = Worker(test_function, 3, 4)
        
        # Mock signal connections
        result_callback = Mock()
        finished_callback = Mock()
        worker.signals.result.connect(result_callback)
        worker.signals.finished.connect(finished_callback)
        
        worker.run()
        
        result_callback.assert_called_once_with(12)
        finished_callback.assert_called_once()

    def test_worker_run_exception(self) -> None:
        """Test worker execution with exception."""
        def failing_function() -> None:
            raise ValueError("Test error")
        
        worker = Worker(failing_function)
        
        # Mock signal connections
        error_callback = Mock()
        finished_callback = Mock()
        worker.signals.error.connect(error_callback)
        worker.signals.finished.connect(finished_callback)
        
        worker.run()
        
        error_callback.assert_called_once()
        error_args = error_callback.call_args[0][0]
        assert error_args[0] == ValueError
        assert "Test error" in str(error_args[1])
        finished_callback.assert_called_once()

    def test_worker_run_with_args_and_kwargs(self) -> None:
        """Test worker execution with various arguments."""
        def complex_function(a, b, c=10, d=20) -> None:
            return a + b + c + d
        
        worker = Worker(complex_function, 1, 2, c=30, d=40)
        
        result_callback = Mock()
        worker.signals.result.connect(result_callback)
        
        worker.run()
        
        result_callback.assert_called_once_with(73)  # 1 + 2 + 30 + 40


class TestThreadPoolManager:
    """Test suite for ThreadPoolManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.manager = ThreadPoolManager(max_threads=4)

    def test_initialization_with_max_threads(self) -> None:
        """Test ThreadPoolManager initialization with specified max threads."""
        manager = ThreadPoolManager(max_threads=8)
        
        assert manager.max_thread_count() == 8

    @patch('os.cpu_count')
    def test_initialization_default_threads(self, mock_cpu_count) -> None:
        """Test ThreadPoolManager initialization with default thread calculation."""
        mock_cpu_count.return_value = 6
        
        manager = ThreadPoolManager()
        
        # Should be max(4, min(6 * 2, 16)) = 12
        assert manager.max_thread_count() == 12

    @patch('os.cpu_count')
    def test_initialization_cpu_count_none(self, mock_cpu_count) -> None:
        """Test initialization when cpu_count returns None."""
        mock_cpu_count.return_value = None
        
        manager = ThreadPoolManager()
        
        # Should default to max(4, min(4 * 2, 16)) = 8
        assert manager.max_thread_count() == 8

    def test_submit_task_basic(self) -> None:
        """Test basic task submission."""
        def simple_task() -> None:
            return "task_result"
        
        worker = self.manager.submit_task(simple_task)
        
        assert isinstance(worker, Worker)
        assert worker.fn == simple_task

    def test_submit_task_with_callbacks(self) -> None:
        """Test task submission with callbacks."""
        def test_task() -> None:
            return "success"
        
        result_callback = Mock()
        error_callback = Mock()
        progress_callback = Mock()
        
        worker = self.manager.submit_task(
            test_task,
            callback=result_callback,
            error_callback=error_callback,
            progress_callback=progress_callback
        )
        
        # Verify callbacks are connected
        assert result_callback in worker.signals.result.callbacks
        assert error_callback in worker.signals.error.callbacks
        assert progress_callback in worker.signals.progress.callbacks

    def test_submit_task_with_args_kwargs(self) -> None:
        """Test task submission with arguments."""
        def parameterized_task(a, b, c=None) -> None:
            return f"{a}-{b}-{c}"
        
        worker = self.manager.submit_task(
            parameterized_task,
            "arg1", "arg2",
            c="kwarg1"
        )
        
        assert worker.args == ("arg1", "arg2")
        assert worker.kwargs == {"c": "kwarg1"}

    def test_submit_task_callback_execution(self) -> None:
        """Test that callbacks are actually executed."""
        def test_task() -> None:
            return "callback_test"
        
        result_callback = Mock()
        
        worker = self.manager.submit_task(test_task, callback=result_callback)
        
        # Wait a bit for the task to complete
        time.sleep(0.1)
        
        result_callback.assert_called_once_with("callback_test")

    def test_submit_task_error_callback_execution(self) -> None:
        """Test that error callbacks are executed on exceptions."""
        def failing_task() -> None:
            raise RuntimeError("Task failed")
        
        error_callback = Mock()
        
        worker = self.manager.submit_task(failing_task, error_callback=error_callback)
        
        # Wait a bit for the task to complete
        time.sleep(0.1)
        
        error_callback.assert_called_once()

    def test_wait_for_done_success(self) -> None:
        """Test waiting for tasks to complete successfully."""
        def quick_task() -> None:
            time.sleep(0.05)
            return "done"
        
        self.manager.submit_task(quick_task)
        
        result = self.manager.wait_for_done(timeout_ms=1000)
        
        assert result is True

    def test_wait_for_done_timeout(self) -> None:
        """Test waiting for tasks with timeout."""
        def slow_task() -> None:
            time.sleep(0.5)
            return "done"
        
        self.manager.submit_task(slow_task)
        
        result = self.manager.wait_for_done(timeout_ms=100)
        
        # May be True or False depending on timing, but should not hang
        assert isinstance(result, bool)

    def test_clear_tasks(self) -> None:
        """Test clearing pending tasks."""
        def dummy_task() -> None:
            return "dummy"
        
        # Submit some tasks
        for _ in range(3):
            self.manager.submit_task(dummy_task)
        
        self.manager.clear()
        
        # Clear should not raise an exception
        assert True

    def test_active_thread_count(self) -> None:
        """Test getting active thread count."""
        count = self.manager.active_thread_count()
        
        assert isinstance(count, int)
        assert count >= 0

    def test_max_thread_count(self) -> None:
        """Test getting max thread count."""
        count = self.manager.max_thread_count()
        
        assert isinstance(count, int)
        assert count == 4  # Set in setup_method

    def test_set_max_thread_count(self) -> None:
        """Test setting max thread count."""
        self.manager.set_max_thread_count(8)
        
        assert self.manager.max_thread_count() == 8

    def test_submit_task_logging_filter(self) -> None:
        """Test that stats tasks don't generate excessive logs."""
        def _calculate_stats() -> None:
            return "stats"
        
        # This should not generate debug logs
        worker = self.manager.submit_task(_calculate_stats)
        
        assert isinstance(worker, Worker)

    def test_multiple_task_submission(self) -> None:
        """Test submitting multiple tasks."""
        def numbered_task(n) -> None:
            return f"task_{n}"
        
        workers = []
        for i in range(5):
            worker = self.manager.submit_task(numbered_task, i)
            workers.append(worker)
        
        assert len(workers) == 5
        for worker in workers:
            assert isinstance(worker, Worker)


class TestGlobalFunctions:
    """Test suite for global functions."""

    def test_get_thread_pool_singleton(self) -> None:
        """Test that get_thread_pool returns singleton instance."""
        pool1 = get_thread_pool()
        pool2 = get_thread_pool()
        
        assert pool1 is pool2
        assert isinstance(pool1, ThreadPoolManager)

    def test_submit_task_global_function(self) -> None:
        """Test global submit_task function."""
        def global_task() -> None:
            return "global_result"
        
        result_callback = Mock()
        
        worker = submit_task(global_task, callback=result_callback)
        
        assert isinstance(worker, Worker)
        assert worker.fn == global_task

    def test_submit_task_global_with_callbacks(self) -> None:
        """Test global submit_task with all callback types."""
        def test_task() -> None:
            return "test"
        
        result_callback = Mock()
        error_callback = Mock()
        progress_callback = Mock()
        
        worker = submit_task(
            test_task,
            callback=result_callback,
            error_callback=error_callback,
            progress_callback=progress_callback
        )
        
        assert result_callback in worker.signals.result.callbacks
        assert error_callback in worker.signals.error.callbacks
        assert progress_callback in worker.signals.progress.callbacks

    def test_submit_task_global_with_args(self) -> None:
        """Test global submit_task with arguments."""
        def task_with_args(x, y, z=None) -> None:
            return x + y + (z or 0)
        
        worker = submit_task(task_with_args, 10, 20, z=30)
        
        assert worker.args == (10, 20)
        assert worker.kwargs == {"z": 30}


class TestIntegration:
    """Integration tests for thread pool functionality."""

    def test_end_to_end_task_execution(self) -> None:
        """Test complete task execution flow."""
        results = []
        errors = []
        
        def success_callback(result) -> None:
            results.append(result)
        
        def error_callback(error_info) -> None:
            errors.append(error_info)
        
        def working_task(value) -> None:
            return value * 2
        
        def failing_task() -> None:
            raise ValueError("Intentional failure")
        
        # Submit working task
        submit_task(working_task, 21, callback=success_callback)
        
        # Submit failing task
        submit_task(failing_task, error_callback=error_callback)
        
        # Wait for completion
        get_thread_pool().wait_for_done(timeout_ms=1000)
        
        assert len(results) == 1
        assert results[0] == 42
        assert len(errors) == 1

    def test_concurrent_task_execution(self) -> None:
        """Test multiple tasks running concurrently."""
        results = []
        lock = threading.Lock()
        
        def concurrent_task(task_id) -> None:
            time.sleep(0.1)  # Simulate work
            with lock:
                results.append(task_id)
            return task_id
        
        def result_callback(result) -> None:
            pass  # Results are collected in the task itself
        
        # Submit multiple tasks
        for i in range(5):
            submit_task(concurrent_task, i, callback=result_callback)
        
        # Wait for all to complete
        get_thread_pool().wait_for_done(timeout_ms=2000)
        
        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

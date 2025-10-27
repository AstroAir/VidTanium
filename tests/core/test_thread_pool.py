"""
Tests for thread pool management
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from typing import List

from src.core.thread_pool import (
    Worker, WorkerCallbacks, ThreadPoolManager, get_thread_pool, submit_task
)


@pytest.fixture
def thread_pool_manager():
    """Create ThreadPoolManager instance for testing"""
    manager = ThreadPoolManager(max_threads=4)
    yield manager
    # Cleanup
    try:
        manager.shutdown(wait=True)
    except:
        pass


class TestWorkerCallbacks:
    """Test WorkerCallbacks class"""
    
    def test_initialization(self) -> None:
        """Test WorkerCallbacks initialization"""
        callbacks = WorkerCallbacks()
        
        assert callbacks.on_finished is None
        assert callbacks.on_error is None
        assert callbacks.on_result is None
        assert callbacks.on_progress is None
    
    def test_set_callbacks(self) -> None:
        """Test setting callbacks"""
        callbacks = WorkerCallbacks()
        
        def finished_cb():
            pass
        
        def error_cb(error):
            pass
        
        callbacks.on_finished = finished_cb
        callbacks.on_error = error_cb
        
        assert callbacks.on_finished == finished_cb
        assert callbacks.on_error == error_cb


class TestWorker:
    """Test Worker class"""
    
    def test_worker_initialization(self) -> None:
        """Test Worker initialization"""
        def test_func():
            return "result"
        
        worker = Worker(test_func, 1, 2, key="value")
        
        assert worker.fn == test_func
        assert worker.args == (1, 2)
        assert worker.kwargs == {"key": "value"}
        assert worker.is_running is False
        assert worker.priority == 0
        assert isinstance(worker.callbacks, WorkerCallbacks)
    
    def test_worker_call_success(self) -> None:
        """Test worker execution with success"""
        def test_func(a, b):
            return a + b
        
        worker = Worker(test_func, 2, 3)
        result_holder = []
        
        def on_result(result):
            result_holder.append(result)
        
        worker.callbacks.on_result = on_result
        
        result = worker()
        
        assert result == 5
        assert result_holder == [5]
        assert worker.is_running is False
    
    def test_worker_call_with_error(self) -> None:
        """Test worker execution with error"""
        def test_func():
            raise ValueError("Test error")
        
        worker = Worker(test_func)
        error_holder = []
        
        def on_error(error):
            error_holder.append(error)
        
        worker.callbacks.on_error = on_error
        
        with pytest.raises(ValueError):
            worker()
        
        assert len(error_holder) == 1
        assert worker.is_running is False


class TestThreadPoolManager:
    """Test ThreadPoolManager class"""
    
    def test_initialization(self) -> None:
        """Test ThreadPoolManager initialization"""
        manager = ThreadPoolManager(max_threads=8)
        
        assert manager.max_thread_count() == 8
        assert manager.active_thread_count() == 0
        assert manager.total_tasks_submitted == 0
        assert manager.total_tasks_completed == 0
        assert manager.total_tasks_failed == 0
        
        manager.shutdown()
    
    def test_submit_task_basic(self, thread_pool_manager) -> None:
        """Test basic task submission"""
        def simple_task():
            return "result"
        
        worker = thread_pool_manager.submit_task(simple_task)
        
        assert isinstance(worker, Worker)
        assert worker.fn == simple_task
        assert worker.worker_id is not None
        assert thread_pool_manager.total_tasks_submitted == 1
    
    def test_submit_task_with_callback(self, thread_pool_manager) -> None:
        """Test task submission with callback"""
        results = []
        
        def test_task():
            return 42
        
        def on_result(result):
            results.append(result)
        
        worker = thread_pool_manager.submit_task(test_task, callback=on_result)
        
        # Wait for task to complete
        thread_pool_manager.wait_for_done(timeout_ms=5000)
        
        assert len(results) == 1
        assert results[0] == 42
    
    def test_submit_task_with_error_callback(self, thread_pool_manager) -> None:
        """Test task submission with error callback"""
        errors = []
        
        def failing_task():
            raise RuntimeError("Test error")
        
        def on_error(error):
            errors.append(error)
        
        worker = thread_pool_manager.submit_task(failing_task, error_callback=on_error)
        
        # Wait for task to complete
        thread_pool_manager.wait_for_done(timeout_ms=5000)
        
        assert len(errors) == 1
        assert thread_pool_manager.total_tasks_failed == 1
    
    def test_submit_task_with_args(self, thread_pool_manager) -> None:
        """Test task submission with arguments"""
        results = []
        
        def add_task(a, b):
            return a + b
        
        def on_result(result):
            results.append(result)
        
        worker = thread_pool_manager.submit_task(add_task, 5, 3, callback=on_result)
        
        # Wait for task to complete
        thread_pool_manager.wait_for_done(timeout_ms=5000)
        
        assert len(results) == 1
        assert results[0] == 8
    
    def test_submit_task_with_priority(self, thread_pool_manager) -> None:
        """Test task submission with priority"""
        def test_task():
            return "result"
        
        worker = thread_pool_manager.submit_task(test_task, priority=10)
        
        assert worker.priority == 10
    
    def test_wait_for_done(self, thread_pool_manager) -> None:
        """Test waiting for all tasks to complete"""
        results = []
        
        def test_task(n):
            time.sleep(0.1)
            return n * 2
        
        def on_result(result):
            results.append(result)
        
        # Submit multiple tasks
        for i in range(3):
            thread_pool_manager.submit_task(test_task, i, callback=on_result)
        
        # Wait for all to complete
        completed = thread_pool_manager.wait_for_done(timeout_ms=5000)
        
        assert completed is True
        assert len(results) == 3
        assert set(results) == {0, 2, 4}
    
    def test_shutdown(self) -> None:
        """Test thread pool shutdown"""
        manager = ThreadPoolManager(max_threads=4)
        
        def test_task():
            return "result"
        
        manager.submit_task(test_task)
        manager.shutdown(wait=True)
        
        assert manager._shutdown is True
    
    def test_max_thread_count(self) -> None:
        """Test max thread count"""
        manager = ThreadPoolManager(max_threads=6)
        
        assert manager.max_thread_count() == 6
        
        manager.shutdown()


class TestGlobalThreadPool:
    """Test global thread pool functions"""
    
    def test_get_thread_pool(self) -> None:
        """Test getting global thread pool instance"""
        pool1 = get_thread_pool()
        pool2 = get_thread_pool()
        
        assert pool1 is pool2
        assert isinstance(pool1, ThreadPoolManager)
    
    def test_submit_task_global(self) -> None:
        """Test submitting task to global thread pool"""
        results = []
        
        def test_task():
            return "global_result"
        
        def on_result(result):
            results.append(result)
        
        worker = submit_task(test_task, callback=on_result)
        
        assert isinstance(worker, Worker)
        
        # Wait for completion
        get_thread_pool().wait_for_done(timeout_ms=5000)
        
        assert len(results) == 1
        assert results[0] == "global_result"


if __name__ == "__main__":
    pytest.main([__file__])

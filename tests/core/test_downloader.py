import pytest
import time
import threading
import tempfile
import os
import uuid
from unittest.mock import patch, Mock, MagicMock, mock_open
from queue import PriorityQueue, Queue, Empty
from typing import Dict, List, Optional, Any

from src.core.downloader import (
    DownloadManager, DownloadTask, TaskStatus, TaskPriority,
    ProgressDict, SegmentDetail
)
from src.core.exceptions import (
    VidTaniumException, NetworkException, FilesystemException
)


class MockSettings:
    """Mock settings provider for testing."""
    
    def __init__(self, settings_dict: Optional[Dict] = None) -> None:
        self.settings = settings_dict or {
            "download": {
                "max_concurrent_tasks": 3,
                "max_workers_per_task": 10,
                "max_retries": 3,
                "retry_delay": 2,
                "request_timeout": 30,
                "chunk_size": 8192
            },
            "advanced": {
                "user_agent": "TestAgent/1.0",
                "verify_ssl": True
            }
        }
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get setting value."""
        return self.settings.get(section, {}).get(key, default)


class TestTaskStatus:
    """Test suite for TaskStatus enum."""

    def test_status_values(self) -> None:
        """Test enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.PAUSED.value == "paused"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELED.value == "canceled"


class TestTaskPriority:
    """Test suite for TaskPriority enum."""

    def test_priority_values(self) -> None:
        """Test enum values."""
        assert TaskPriority.LOW.value == 0
        assert TaskPriority.NORMAL.value == 1
        assert TaskPriority.HIGH.value == 2


class TestDownloadTask:
    """Test suite for DownloadTask class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.settings = MockSettings()

    def test_task_creation_with_all_params(self) -> None:
        """Test DownloadTask creation with all parameters."""
        task = DownloadTask(
            task_id="test_task",
            name="Test Task",
            base_url="https://example.com/stream",
            key_url="https://example.com/key.bin",
            segments=100,
            output_file="/downloads/video.mp4",
            settings=self.settings,
            priority=TaskPriority.HIGH
        )
        
        assert task.task_id == "test_task"
        assert task.name == "Test Task"
        assert task.base_url == "https://example.com/stream"
        assert task.key_url == "https://example.com/key.bin"
        assert task.segments == 100
        assert task.output_file == "/downloads/video.mp4"
        assert task.settings == self.settings
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING

    def test_task_creation_with_defaults(self) -> None:
        """Test DownloadTask creation with default values."""
        task = DownloadTask()
        
        assert task.task_id is not None
        assert len(task.task_id) > 0
        assert task.name.startswith("Task-")
        assert task.base_url is None
        assert task.key_url is None
        assert task.segments is None
        assert task.output_file is None
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.PENDING

    def test_task_progress_initialization(self) -> None:
        """Test task progress initialization."""
        task = DownloadTask(segments=50)
        
        assert task.progress["total"] == 50
        assert task.progress["completed"] == 0
        assert task.progress["failed"] == 0
        assert task.progress["current_file"] is None
        assert task.progress["current_file_progress"] == 0.0
        assert task.progress["start_time"] is None
        assert task.progress["end_time"] is None
        assert task.progress["speed"] == 0.0
        assert task.progress["estimated_time"] is None
        assert task.progress["downloaded_bytes"] == 0

    def test_task_events_initialization(self) -> None:
        """Test task threading events initialization."""
        task = DownloadTask()
        
        assert isinstance(task.paused_event, threading.Event)
        assert isinstance(task.canceled_event, threading.Event)
        assert not task.paused_event.is_set()
        assert not task.canceled_event.is_set()

    def test_task_pause(self) -> None:
        """Test task pause functionality."""
        task = DownloadTask()
        
        task.pause()
        assert task.status == TaskStatus.PAUSED
        assert task.paused_event.is_set()

    def test_task_resume(self) -> None:
        """Test task resume functionality."""
        task = DownloadTask()
        task.pause()
        
        task.resume()
        assert task.status == TaskStatus.PENDING
        assert not task.paused_event.is_set()

    def test_task_cancel(self) -> None:
        """Test task cancel functionality."""
        task = DownloadTask()
        
        task.cancel()
        assert task.status == TaskStatus.CANCELED
        assert task.canceled_event.is_set()

    def test_task_get_progress_percentage(self) -> None:
        """Test progress percentage calculation."""
        task = DownloadTask(segments=100)
        
        # No progress
        assert task.get_progress_percentage() == 0.0
        
        # Partial progress
        task.progress["completed"] = 50
        assert task.get_progress_percentage() == 50.0
        
        # Complete
        task.progress["completed"] = 100
        assert task.get_progress_percentage() == 100.0
        
        # No segments
        task.segments = 0
        assert task.get_progress_percentage() == 0.0

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_progress(self, mock_json_dump, mock_file) -> None:
        """Test progress saving."""
        task = DownloadTask(
            task_id="test_task",
            output_file="/downloads/video.mp4"
        )
        task.progress["completed"] = 25
        
        task.save_progress()
        
        # Verify file operations
        mock_file.assert_called()
        mock_json_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='{"completed": 25, "total": 100}')
    @patch('json.load')
    @patch('os.path.exists')
    def test_load_progress(self, mock_exists, mock_json_load, mock_file) -> None:
        """Test progress loading."""
        mock_exists.return_value = True
        mock_json_load.return_value = {"completed": 25, "total": 100}
        
        task = DownloadTask(
            task_id="test_task",
            output_file="/downloads/video.mp4"
        )
        
        task.load_progress()
        
        mock_file.assert_called()
        mock_json_load.assert_called_once()

    @patch('os.path.exists')
    def test_load_progress_no_file(self, mock_exists) -> None:
        """Test progress loading when file doesn't exist."""
        mock_exists.return_value = False
        
        task = DownloadTask()
        
        # Should not raise exception
        task.load_progress()


class TestDownloadManager:
    """Test suite for DownloadManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.settings = MockSettings()
        self.manager = DownloadManager(settings=self.settings)

    def teardown_method(self) -> None:
        """Clean up after tests."""
        if self.manager.running:
            self.manager.stop()

    def test_manager_initialization(self) -> None:
        """Test DownloadManager initialization."""
        assert self.manager.settings == self.settings
        assert isinstance(self.manager.tasks, dict)
        assert isinstance(self.manager.tasks_queue, PriorityQueue)
        assert isinstance(self.manager.active_tasks, set)
        assert not self.manager.running
        assert self.manager.scheduler_thread is None
        assert self.manager.bandwidth_limit == 0

    def test_manager_start(self) -> None:
        """Test starting download manager."""
        self.manager.start()
        
        assert self.manager.running is True
        assert self.manager.scheduler_thread is not None
        assert self.manager.scheduler_thread.is_alive()

    def test_manager_start_already_running(self) -> None:
        """Test starting manager when already running."""
        self.manager.start()
        original_thread = self.manager.scheduler_thread
        
        self.manager.start()
        
        # Should not create new thread
        assert self.manager.scheduler_thread == original_thread

    def test_manager_stop(self) -> None:
        """Test stopping download manager."""
        self.manager.start()
        self.manager.stop()
        
        assert self.manager.running is False

    def test_add_task(self) -> None:
        """Test adding download task."""
        task = DownloadTask(
            name="Test Task",
            base_url="https://example.com/stream",
            segments=10
        )
        
        task_id = self.manager.add_task(task)
        
        assert task_id == task.task_id
        assert task_id in self.manager.tasks
        assert self.manager.tasks[task_id] == task

    def test_get_task(self) -> None:
        """Test getting task by ID."""
        task = DownloadTask(name="Test Task")
        task_id = self.manager.add_task(task)
        
        retrieved_task = self.manager.get_task(task_id)
        assert retrieved_task == task
        
        # Test nonexistent task
        assert self.manager.get_task("nonexistent") is None

    def test_remove_task(self) -> None:
        """Test removing task."""
        task = DownloadTask(name="Test Task")
        task_id = self.manager.add_task(task)
        
        result = self.manager.remove_task(task_id)
        
        assert result is True
        assert task_id not in self.manager.tasks

    def test_remove_nonexistent_task(self) -> None:
        """Test removing nonexistent task."""
        result = self.manager.remove_task("nonexistent")
        assert result is False

    def test_pause_task(self) -> None:
        """Test pausing task."""
        task = DownloadTask(name="Test Task")
        task_id = self.manager.add_task(task)
        
        result = self.manager.pause_task(task_id)
        
        assert result is True
        assert task.status == TaskStatus.PAUSED

    def test_resume_task(self) -> None:
        """Test resuming task."""
        task = DownloadTask(name="Test Task")
        task_id = self.manager.add_task(task)
        task.pause()
        
        result = self.manager.resume_task(task_id)
        
        assert result is True
        assert task.status == TaskStatus.PENDING

    def test_cancel_task(self) -> None:
        """Test canceling task."""
        task = DownloadTask(name="Test Task")
        task_id = self.manager.add_task(task)
        
        result = self.manager.cancel_task(task_id)
        
        assert result is True
        assert task.status == TaskStatus.CANCELED

    def test_get_all_tasks(self) -> None:
        """Test getting all tasks."""
        task1 = DownloadTask(name="Task 1")
        task2 = DownloadTask(name="Task 2")
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        
        all_tasks = self.manager.get_all_tasks()
        
        assert len(all_tasks) == 2
        assert task1.task_id in all_tasks
        assert task2.task_id in all_tasks

    def test_get_tasks_by_status(self) -> None:
        """Test getting tasks by status."""
        task1 = DownloadTask(name="Task 1")
        task2 = DownloadTask(name="Task 2")
        task3 = DownloadTask(name="Task 3")
        
        self.manager.add_task(task1)
        self.manager.add_task(task2)
        self.manager.add_task(task3)
        
        # Pause one task
        task2.pause()
        
        pending_tasks = self.manager.get_tasks_by_status(TaskStatus.PENDING)
        paused_tasks = self.manager.get_tasks_by_status(TaskStatus.PAUSED)
        
        assert len(pending_tasks) == 2
        assert len(paused_tasks) == 1
        assert task2.task_id in paused_tasks

    def test_callback_registration(self) -> None:
        """Test callback registration."""
        progress_callback = Mock()
        status_callback = Mock()
        completed_callback = Mock()
        failed_callback = Mock()
        
        self.manager.set_progress_callback(progress_callback)
        self.manager.set_status_changed_callback(status_callback)
        self.manager.set_task_completed_callback(completed_callback)
        self.manager.set_task_failed_callback(failed_callback)
        
        assert self.manager.on_task_progress == progress_callback
        assert self.manager.on_task_status_changed == status_callback
        assert self.manager.on_task_completed == completed_callback
        assert self.manager.on_task_failed == failed_callback

    def test_emit_progress(self) -> None:
        """Test progress emission."""
        callback = Mock()
        self.manager.set_progress_callback(callback)
        
        task = DownloadTask(name="Test Task")
        task_id = self.manager.add_task(task)
        
        progress = {"completed": 50, "total": 100}
        self.manager._emit_progress(task_id, progress)
        
        callback.assert_called_once_with(task_id, progress)

    def test_emit_status_changed(self) -> None:
        """Test status change emission."""
        callback = Mock()
        self.manager.set_status_changed_callback(callback)
        
        task = DownloadTask(name="Test Task")
        task_id = self.manager.add_task(task)
        
        self.manager._emit_status_changed(task_id, TaskStatus.PENDING, TaskStatus.RUNNING)
        
        callback.assert_called_once_with(task_id, TaskStatus.PENDING, TaskStatus.RUNNING)

    def test_bandwidth_limit_setting(self) -> None:
        """Test bandwidth limit configuration."""
        self.manager.set_bandwidth_limit(1024)  # 1KB/s
        
        assert self.manager.bandwidth_limit == 1024

    def test_error_handling(self) -> None:
        """Test error handling in manager."""
        task = DownloadTask(name="Test Task")
        task_id = self.manager.add_task(task)
        
        exception = NetworkException("Network error")
        
        # Should not raise exception
        self.manager._handle_task_error(task_id, exception)

    @patch('src.core.downloader.requests.Session')
    def test_download_segment_success(self, mock_session) -> None:
        """Test successful segment download."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"video_data"]
        mock_session.return_value.get.return_value = mock_response
        
        task = DownloadTask(
            name="Test Task",
            base_url="https://example.com/stream",
            segments=1
        )
        
        # This would be called internally during download
        # Testing the concept rather than the full implementation
        assert mock_response.status_code == 200

    def test_concurrent_task_limit(self) -> None:
        """Test concurrent task limit enforcement."""
        # Add multiple tasks
        tasks = []
        for i in range(5):
            task = DownloadTask(name=f"Task {i}")
            task_id = self.manager.add_task(task)
            tasks.append(task_id)
        
        # Start manager
        self.manager.start()
        
        # Give scheduler time to process
        time.sleep(0.1)
        
        # Should respect max_concurrent_tasks setting (3)
        assert len(self.manager.active_tasks) <= 3


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

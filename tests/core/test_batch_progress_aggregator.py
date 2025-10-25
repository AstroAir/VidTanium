import pytest
import time
import threading
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, List, Optional

from src.core.batch_progress_aggregator import (
    BatchProgressAggregator, TaskProgress, BatchProgress,
    AggregationMethod
)


class TestTaskProgress:
    """Test suite for TaskProgress dataclass."""

    def test_task_progress_creation(self) -> None:
        """Test TaskProgress creation with all fields."""
        progress = TaskProgress(
            task_id="test_task",
            name="Test Task",
            progress_percentage=50.0,
            bytes_downloaded=1024,
            total_bytes=2048,
            speed=512.0,
            eta=10.0,
            status="running"
        )
        
        assert progress.task_id == "test_task"
        assert progress.name == "Test Task"
        assert progress.progress_percentage == 50.0
        assert progress.bytes_downloaded == 1024
        assert progress.total_bytes == 2048
        assert progress.speed == 512.0
        assert progress.eta == 10.0
        assert progress.status == "running"

    def test_task_progress_defaults(self) -> None:
        """Test TaskProgress with default values."""
        progress = TaskProgress(
            task_id="test_task",
            name="Test Task",
            progress_percentage=50.0,
            bytes_downloaded=1024,
            total_bytes=2048,
            speed=512.0
        )
        
        assert progress.eta is None
        assert progress.status == "unknown"
        assert progress.last_updated > 0


class TestBatchProgress:
    """Test suite for BatchProgress dataclass."""

    def test_batch_progress_creation(self) -> None:
        """Test BatchProgress creation with all fields."""
        batch = BatchProgress(
            batch_id="test_batch",
            name="Test Batch",
            overall_progress=75.0,
            total_tasks=4,
            completed_tasks=3,
            active_tasks=1,
            failed_tasks=0,
            paused_tasks=0,
            total_bytes=4096,
            downloaded_bytes=3072,
            combined_speed=1024.0
        )
        
        assert batch.batch_id == "test_batch"
        assert batch.name == "Test Batch"
        assert batch.overall_progress == 75.0
        assert batch.total_tasks == 4
        assert batch.completed_tasks == 3
        assert batch.active_tasks == 1
        assert batch.total_bytes == 4096
        assert batch.downloaded_bytes == 3072
        assert batch.combined_speed == 1024.0

    def test_batch_progress_defaults(self) -> None:
        """Test BatchProgress with default values."""
        batch = BatchProgress(
            batch_id="test_batch",
            name="Test Batch",
            overall_progress=0.0,
            total_tasks=0,
            completed_tasks=0,
            active_tasks=0,
            failed_tasks=0,
            paused_tasks=0,
            total_bytes=0,
            downloaded_bytes=0,
            combined_speed=0.0
        )
        
        assert batch.estimated_time_remaining is None
        assert batch.start_time > 0
        assert batch.last_updated > 0
        assert isinstance(batch.task_progresses, dict)
        assert len(batch.task_progresses) == 0


class TestBatchProgressAggregator:
    """Test suite for BatchProgressAggregator class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.aggregator = BatchProgressAggregator()

    def teardown_method(self) -> None:
        """Clean up after tests."""
        # Stop cleanup timer
        if hasattr(self.aggregator, 'cleanup_timer'):
            self.aggregator.cleanup_timer.cancel()

    def test_initialization(self) -> None:
        """Test BatchProgressAggregator initialization."""
        assert isinstance(self.aggregator.batches, dict)
        assert isinstance(self.aggregator.task_to_batch, dict)
        assert isinstance(self.aggregator.progress_callbacks, list)
        assert isinstance(self.aggregator.completion_callbacks, list)
        assert self.aggregator.update_interval == 1.0
        assert self.aggregator.stale_threshold == 30.0

    def test_create_batch(self) -> None:
        """Test batch creation."""
        task_ids = ["task1", "task2", "task3"]
        batch = self.aggregator.create_batch("batch1", "Test Batch", task_ids)
        
        assert batch.batch_id == "batch1"
        assert batch.name == "Test Batch"
        assert batch.total_tasks == 3
        assert batch.completed_tasks == 0
        assert batch.active_tasks == 0
        
        # Check task mapping
        for task_id in task_ids:
            assert self.aggregator.task_to_batch[task_id] == "batch1"
        
        # Check batch is stored
        assert "batch1" in self.aggregator.batches

    def test_create_batch_existing(self) -> None:
        """Test creating batch with existing ID."""
        task_ids1 = ["task1", "task2"]
        task_ids2 = ["task3", "task4"]
        
        batch1 = self.aggregator.create_batch("batch1", "First Batch", task_ids1)
        batch2 = self.aggregator.create_batch("batch1", "Second Batch", task_ids2)
        
        # Should update existing batch
        assert batch2.name == "Second Batch"
        assert batch2.total_tasks == 2

    def test_update_task_progress(self) -> None:
        """Test updating task progress."""
        # Create batch first
        self.aggregator.create_batch("batch1", "Test Batch", ["task1", "task2"])
        
        # Update task progress
        self.aggregator.update_task_progress(
            task_id="task1",
            progress_percentage=50.0,
            bytes_downloaded=1024,
            total_bytes=2048,
            speed=512.0,
            status="running",
            eta=10.0,
            task_name="Task 1"
        )
        
        batch = self.aggregator.get_batch_progress("batch1")
        assert "task1" in batch.task_progresses
        
        task_progress = batch.task_progresses["task1"]
        assert task_progress.progress_percentage == 50.0
        assert task_progress.bytes_downloaded == 1024
        assert task_progress.total_bytes == 2048
        assert task_progress.speed == 512.0
        assert task_progress.status == "running"
        assert task_progress.eta == 10.0
        assert task_progress.name == "Task 1"

    def test_update_task_progress_nonexistent_task(self) -> None:
        """Test updating progress for nonexistent task."""
        # Should not raise error
        self.aggregator.update_task_progress(
            task_id="nonexistent",
            progress_percentage=50.0,
            bytes_downloaded=1024,
            total_bytes=2048,
            speed=512.0
        )
        
        # Should not create any batches
        assert len(self.aggregator.batches) == 0

    def test_remove_task_from_batch(self) -> None:
        """Test removing task from batch."""
        # Create batch
        self.aggregator.create_batch("batch1", "Test Batch", ["task1", "task2"])
        
        # Add some progress
        self.aggregator.update_task_progress(
            task_id="task1",
            progress_percentage=50.0,
            bytes_downloaded=1024,
            total_bytes=2048,
            speed=512.0
        )
        
        # Remove task
        self.aggregator.remove_task_from_batch("task1")
        
        batch = self.aggregator.get_batch_progress("batch1")
        assert "task1" not in batch.task_progresses
        assert "task1" not in self.aggregator.task_to_batch
        assert batch.total_tasks == 1

    def test_remove_nonexistent_task(self) -> None:
        """Test removing nonexistent task."""
        # Should not raise error
        self.aggregator.remove_task_from_batch("nonexistent")

    def test_recalculate_batch_progress_empty(self) -> None:
        """Test recalculating progress for empty batch."""
        batch = self.aggregator.create_batch("batch1", "Test Batch", [])
        
        assert batch.overall_progress == 0.0
        assert batch.completed_tasks == 0
        assert batch.active_tasks == 0
        assert batch.failed_tasks == 0
        assert batch.total_bytes == 0
        assert batch.downloaded_bytes == 0
        assert batch.combined_speed == 0.0
        assert batch.estimated_time_remaining is None

    def test_recalculate_batch_progress_with_tasks(self) -> None:
        """Test recalculating progress with tasks."""
        # Create batch
        self.aggregator.create_batch("batch1", "Test Batch", ["task1", "task2", "task3"])
        
        # Add task progress
        self.aggregator.update_task_progress("task1", 100.0, 2048, 2048, 0.0, "completed")
        self.aggregator.update_task_progress("task2", 50.0, 1024, 2048, 512.0, "running")
        self.aggregator.update_task_progress("task3", 0.0, 0, 2048, 0.0, "failed")
        
        batch = self.aggregator.get_batch_progress("batch1")
        
        assert batch.completed_tasks == 1
        assert batch.active_tasks == 1
        assert batch.failed_tasks == 1
        assert batch.total_bytes == 6144  # 3 * 2048
        assert batch.downloaded_bytes == 3072  # 2048 + 1024 + 0
        assert batch.combined_speed == 512.0  # Only from running task
        assert batch.overall_progress == 50.0  # 3072/6144 * 100

    def test_get_batch_progress(self) -> None:
        """Test getting batch progress."""
        batch = self.aggregator.create_batch("batch1", "Test Batch", ["task1"])
        
        retrieved = self.aggregator.get_batch_progress("batch1")
        assert retrieved == batch
        
        # Test nonexistent batch
        assert self.aggregator.get_batch_progress("nonexistent") is None

    def test_get_all_batches(self) -> None:
        """Test getting all batches."""
        self.aggregator.create_batch("batch1", "Batch 1", ["task1"])
        self.aggregator.create_batch("batch2", "Batch 2", ["task2"])
        
        all_batches = self.aggregator.get_all_batches()
        
        assert len(all_batches) == 2
        assert "batch1" in all_batches
        assert "batch2" in all_batches

    def test_delete_batch(self) -> None:
        """Test deleting batch."""
        # Create batch
        self.aggregator.create_batch("batch1", "Test Batch", ["task1", "task2"])
        
        # Delete batch
        self.aggregator.delete_batch("batch1")
        
        assert "batch1" not in self.aggregator.batches
        assert "task1" not in self.aggregator.task_to_batch
        assert "task2" not in self.aggregator.task_to_batch

    def test_delete_nonexistent_batch(self) -> None:
        """Test deleting nonexistent batch."""
        # Should not raise error
        self.aggregator.delete_batch("nonexistent")

    def test_register_callbacks(self) -> None:
        """Test callback registration."""
        progress_callback = Mock()
        completion_callback = Mock()
        
        self.aggregator.register_progress_callback(progress_callback)
        self.aggregator.register_completion_callback(completion_callback)
        
        assert progress_callback in self.aggregator.progress_callbacks
        assert completion_callback in self.aggregator.completion_callbacks

    def test_trigger_progress_callbacks(self) -> None:
        """Test progress callback triggering."""
        callback = Mock()
        self.aggregator.register_progress_callback(callback)
        
        # Create batch and update progress
        batch = self.aggregator.create_batch("batch1", "Test Batch", ["task1"])
        self.aggregator.update_task_progress("task1", 50.0, 1024, 2048, 512.0)
        
        # Callback should be triggered
        callback.assert_called()

    def test_trigger_completion_callbacks(self) -> None:
        """Test completion callback triggering."""
        callback = Mock()
        self.aggregator.register_completion_callback(callback)
        
        # Create batch and complete all tasks
        self.aggregator.create_batch("batch1", "Test Batch", ["task1"])
        self.aggregator.update_task_progress("task1", 100.0, 2048, 2048, 0.0, "completed")
        
        # Completion callback should be triggered
        callback.assert_called()

    def test_callback_error_handling(self) -> None:
        """Test error handling in callbacks."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()
        
        self.aggregator.register_progress_callback(error_callback)
        self.aggregator.register_progress_callback(good_callback)
        
        # Create batch and update progress
        self.aggregator.create_batch("batch1", "Test Batch", ["task1"])
        self.aggregator.update_task_progress("task1", 50.0, 1024, 2048, 512.0)
        
        # Both callbacks should be called despite error
        error_callback.assert_called()
        good_callback.assert_called()

    def test_get_aggregation_summary(self) -> None:
        """Test getting aggregation summary."""
        # Create multiple batches
        self.aggregator.create_batch("batch1", "Batch 1", ["task1", "task2"])
        self.aggregator.create_batch("batch2", "Batch 2", ["task3"])
        
        # Update some progress
        self.aggregator.update_task_progress("task1", 100.0, 2048, 2048, 0.0, "completed")
        self.aggregator.update_task_progress("task2", 50.0, 1024, 2048, 512.0, "running")
        self.aggregator.update_task_progress("task3", 100.0, 1024, 1024, 0.0, "completed")
        
        summary = self.aggregator.get_aggregation_summary()
        
        assert summary["total_batches"] == 2
        assert summary["active_batches"] == 1  # batch1 has active task
        assert summary["completed_batches"] == 1  # batch2 is complete
        assert summary["total_tasks"] == 3
        assert summary["total_active_tasks"] == 1
        assert summary["combined_speed"] == 512.0
        assert summary["total_bytes"] == 5120  # 2048 + 2048 + 1024
        assert summary["downloaded_bytes"] == 4096  # 2048 + 1024 + 1024


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

import pytest
import time
import threading
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, List, Optional, Any
from collections import defaultdict

from src.core.queue_manager import (
    QueueManager, QueuedTask, TaskPriority, SchedulingStrategy,
    QueueStatistics, SmartScheduler, queue_manager
)


class TestTaskPriority:
    """Test suite for TaskPriority enum."""

    def test_priority_values(self) -> None:
        """Test enum values."""
        assert TaskPriority.URGENT.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.NORMAL.value == 3
        assert TaskPriority.LOW.value == 4
        assert TaskPriority.BACKGROUND.value == 5


class TestSchedulingStrategy:
    """Test suite for SchedulingStrategy enum."""

    def test_strategy_values(self) -> None:
        """Test enum values."""
        assert SchedulingStrategy.PRIORITY_FIRST.value == "priority_first"
        assert SchedulingStrategy.SIZE_OPTIMIZED.value == "size_optimized"
        assert SchedulingStrategy.TIME_BALANCED.value == "time_balanced"
        assert SchedulingStrategy.RESOURCE_AWARE.value == "resource_aware"
        assert SchedulingStrategy.USER_DEFINED.value == "user_defined"


class TestQueuedTask:
    """Test suite for QueuedTask dataclass."""

    def test_task_creation(self) -> None:
        """Test QueuedTask creation with all fields."""
        task = QueuedTask(
            task_id="test_task",
            name="Test Task",
            url="https://example.com/video.m3u8",
            output_path="/downloads/video.mp4",
            file_size=1048576,
            priority=TaskPriority.HIGH,
            estimated_duration=120.0,
            dependencies=["dep1", "dep2"],
            metadata={"quality": "720p"},
            attempts=1,
            max_attempts=5
        )
        
        assert task.task_id == "test_task"
        assert task.name == "Test Task"
        assert task.url == "https://example.com/video.m3u8"
        assert task.output_path == "/downloads/video.mp4"
        assert task.file_size == 1048576
        assert task.priority == TaskPriority.HIGH
        assert task.estimated_duration == 120.0
        assert task.dependencies == ["dep1", "dep2"]
        assert task.metadata == {"quality": "720p"}
        assert task.attempts == 1
        assert task.max_attempts == 5

    def test_task_defaults(self) -> None:
        """Test QueuedTask with default values."""
        task = QueuedTask(
            task_id="test_task",
            name="Test Task",
            url="https://example.com/video.m3u8",
            output_path="/downloads/video.mp4",
            file_size=1048576,
            priority=TaskPriority.NORMAL,
            estimated_duration=60.0
        )
        
        assert task.dependencies == []
        assert task.metadata == {}
        assert task.created_at > 0
        assert task.scheduled_at is None
        assert task.attempts == 0
        assert task.max_attempts == 3

    def test_task_comparison(self) -> None:
        """Test task comparison for priority queue."""
        task1 = QueuedTask(
            task_id="task1", name="Task 1", url="url1", output_path="path1",
            file_size=1000, priority=TaskPriority.HIGH, estimated_duration=60.0
        )
        
        task2 = QueuedTask(
            task_id="task2", name="Task 2", url="url2", output_path="path2",
            file_size=2000, priority=TaskPriority.NORMAL, estimated_duration=120.0
        )
        
        task3 = QueuedTask(
            task_id="task3", name="Task 3", url="url3", output_path="path3",
            file_size=500, priority=TaskPriority.HIGH, estimated_duration=30.0
        )
        
        # Higher priority (lower value) should be less than lower priority
        assert task1 < task2
        
        # Same priority, smaller file should be less than larger file
        assert task3 < task1


class TestQueueStatistics:
    """Test suite for QueueStatistics dataclass."""

    def test_statistics_creation(self) -> None:
        """Test QueueStatistics creation."""
        stats = QueueStatistics(
            total_tasks=10,
            pending_tasks=3,
            running_tasks=2,
            completed_tasks=4,
            failed_tasks=1,
            average_wait_time=45.5,
            estimated_total_time=300.0,
            queue_efficiency=80.0,
            priority_distribution={"HIGH": 2, "NORMAL": 5, "LOW": 3},
            size_distribution={"small": 4, "medium": 4, "large": 2}
        )
        
        assert stats.total_tasks == 10
        assert stats.pending_tasks == 3
        assert stats.running_tasks == 2
        assert stats.completed_tasks == 4
        assert stats.failed_tasks == 1
        assert stats.average_wait_time == 45.5
        assert stats.estimated_total_time == 300.0
        assert stats.queue_efficiency == 80.0
        assert stats.priority_distribution["HIGH"] == 2
        assert stats.size_distribution["small"] == 4


class TestSmartScheduler:
    """Test suite for SmartScheduler class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.scheduler = SmartScheduler()

    def test_initialization(self) -> None:
        """Test SmartScheduler initialization."""
        assert self.scheduler.strategy == SchedulingStrategy.PRIORITY_FIRST
        assert self.scheduler.max_concurrent_tasks == 3
        assert self.scheduler.size_threshold_mb == 100
        assert self.scheduler.time_threshold_minutes == 30

    def test_schedule_tasks_priority_first(self) -> None:
        """Test priority-first scheduling."""
        pending_tasks = [
            QueuedTask("task1", "Task 1", "url1", "path1", 1000, TaskPriority.LOW, 60.0),
            QueuedTask("task2", "Task 2", "url2", "path2", 2000, TaskPriority.HIGH, 120.0),
            QueuedTask("task3", "Task 3", "url3", "path3", 1500, TaskPriority.NORMAL, 90.0)
        ]
        
        running_tasks = []
        system_resources = {"cpu": 50.0, "memory": 60.0, "network": 70.0}
        
        scheduled = self.scheduler.schedule_tasks(pending_tasks, running_tasks, system_resources)
        
        # Should schedule high priority task first
        assert len(scheduled) > 0
        assert scheduled[0].priority == TaskPriority.HIGH

    def test_schedule_tasks_size_optimized(self) -> None:
        """Test size-optimized scheduling."""
        self.scheduler.strategy = SchedulingStrategy.SIZE_OPTIMIZED
        
        pending_tasks = [
            QueuedTask("task1", "Task 1", "url1", "path1", 5000, TaskPriority.NORMAL, 300.0),
            QueuedTask("task2", "Task 2", "url2", "path2", 1000, TaskPriority.NORMAL, 60.0),
            QueuedTask("task3", "Task 3", "url3", "path3", 3000, TaskPriority.NORMAL, 180.0)
        ]
        
        running_tasks = []
        system_resources = {"cpu": 50.0, "memory": 60.0, "network": 70.0}
        
        scheduled = self.scheduler.schedule_tasks(pending_tasks, running_tasks, system_resources)
        
        # Should schedule smaller tasks first
        assert len(scheduled) > 0
        assert scheduled[0].file_size == 1000

    def test_schedule_tasks_with_max_concurrent_limit(self) -> None:
        """Test scheduling with concurrent task limit."""
        pending_tasks = [
            QueuedTask("task1", "Task 1", "url1", "path1", 1000, TaskPriority.HIGH, 60.0),
            QueuedTask("task2", "Task 2", "url2", "path2", 2000, TaskPriority.HIGH, 120.0),
            QueuedTask("task3", "Task 3", "url3", "path3", 1500, TaskPriority.HIGH, 90.0),
            QueuedTask("task4", "Task 4", "url4", "path4", 1200, TaskPriority.HIGH, 75.0)
        ]
        
        # Already have 2 running tasks
        running_tasks = [
            QueuedTask("running1", "Running 1", "url_r1", "path_r1", 1000, TaskPriority.NORMAL, 60.0),
            QueuedTask("running2", "Running 2", "url_r2", "path_r2", 2000, TaskPriority.NORMAL, 120.0)
        ]
        
        system_resources = {"cpu": 50.0, "memory": 60.0, "network": 70.0}
        
        scheduled = self.scheduler.schedule_tasks(pending_tasks, running_tasks, system_resources)
        
        # Should only schedule 1 more task (max_concurrent_tasks = 3, 2 already running)
        assert len(scheduled) <= 1


class TestQueueManager:
    """Test suite for QueueManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.manager = QueueManager()

    def test_initialization(self) -> None:
        """Test QueueManager initialization."""
        assert isinstance(self.manager.pending_queue, list)
        assert isinstance(self.manager.running_tasks, dict)
        assert isinstance(self.manager.completed_tasks, dict)
        assert isinstance(self.manager.failed_tasks, dict)
        assert hasattr(self.manager.lock, 'acquire') and hasattr(self.manager.lock, 'release')
        assert isinstance(self.manager.scheduler, SmartScheduler)
        assert self.manager.auto_schedule_enabled is True

    def test_add_task(self) -> None:
        """Test adding task to queue."""
        result = self.manager.add_task(
            task_id="test_task",
            name="Test Task",
            url="https://example.com/video.m3u8",
            output_path="/downloads/video.mp4",
            file_size=1048576,
            priority=TaskPriority.HIGH,
            estimated_duration=120.0,
            dependencies=["dep1"],
            metadata={"quality": "720p"}
        )
        
        assert result is True
        assert len(self.manager.pending_queue) == 1
        
        task = self.manager.pending_queue[0]
        assert task.task_id == "test_task"
        assert task.name == "Test Task"
        assert task.priority == TaskPriority.HIGH
        assert task.dependencies == ["dep1"]
        assert task.metadata == {"quality": "720p"}

    def test_add_duplicate_task(self) -> None:
        """Test adding duplicate task."""
        # Add first task
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000)
        
        # Try to add duplicate
        result = self.manager.add_task("test_task", "Duplicate Task", "url2", "path2", 2000)
        
        assert result is False
        assert len(self.manager.pending_queue) == 1

    def test_remove_task_from_pending(self) -> None:
        """Test removing task from pending queue."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000)
        
        result = self.manager.remove_task("test_task")
        
        assert result is True
        assert len(self.manager.pending_queue) == 0

    def test_remove_task_from_running(self) -> None:
        """Test removing task from running tasks."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000)
        self.manager.mark_task_running("test_task")
        
        result = self.manager.remove_task("test_task")
        
        assert result is True
        assert "test_task" not in self.manager.running_tasks

    def test_remove_nonexistent_task(self) -> None:
        """Test removing nonexistent task."""
        result = self.manager.remove_task("nonexistent")
        assert result is False

    def test_get_task_from_pending(self) -> None:
        """Test getting task from pending queue."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000)
        
        task = self.manager.get_task("test_task")
        
        assert task is not None
        assert task.task_id == "test_task"

    def test_get_task_from_running(self) -> None:
        """Test getting task from running tasks."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000)
        self.manager.mark_task_running("test_task")
        
        task = self.manager.get_task("test_task")
        
        assert task is not None
        assert task.task_id == "test_task"

    def test_get_nonexistent_task(self) -> None:
        """Test getting nonexistent task."""
        task = self.manager.get_task("nonexistent")
        assert task is None

    def test_update_task_priority(self) -> None:
        """Test updating task priority."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000, TaskPriority.NORMAL)
        
        result = self.manager.update_task_priority("test_task", TaskPriority.HIGH)
        
        assert result is True
        task = self.manager.get_task("test_task")
        assert task.priority == TaskPriority.HIGH

    def test_update_priority_nonexistent_task(self) -> None:
        """Test updating priority of nonexistent task."""
        result = self.manager.update_task_priority("nonexistent", TaskPriority.HIGH)
        assert result is False

    def test_reorder_tasks(self) -> None:
        """Test reordering tasks in queue."""
        # Add multiple tasks
        self.manager.add_task("task1", "Task 1", "url1", "path1", 1000)
        self.manager.add_task("task2", "Task 2", "url2", "path2", 2000)
        self.manager.add_task("task3", "Task 3", "url3", "path3", 1500)
        
        # Reorder: task3, task1, task2
        new_order = ["task3", "task1", "task2"]
        result = self.manager.reorder_tasks(new_order)
        
        assert result is True
        assert self.manager.pending_queue[0].task_id == "task3"
        assert self.manager.pending_queue[1].task_id == "task1"
        assert self.manager.pending_queue[2].task_id == "task2"

    def test_reorder_tasks_invalid_order(self) -> None:
        """Test reordering with invalid task order."""
        self.manager.add_task("task1", "Task 1", "url1", "path1", 1000)
        
        # Try to reorder with nonexistent task
        result = self.manager.reorder_tasks(["nonexistent", "task1"])
        assert result is False

    def test_get_next_tasks(self) -> None:
        """Test getting next tasks to schedule."""
        # Add tasks with different priorities
        self.manager.add_task("task1", "Task 1", "url1", "path1", 1000, TaskPriority.LOW)
        self.manager.add_task("task2", "Task 2", "url2", "path2", 2000, TaskPriority.HIGH)
        self.manager.add_task("task3", "Task 3", "url3", "path3", 1500, TaskPriority.NORMAL)
        
        next_tasks = self.manager.get_next_tasks(count=2)
        
        assert len(next_tasks) <= 2
        # Should prioritize high priority task
        if next_tasks:
            assert next_tasks[0].priority == TaskPriority.HIGH

    def test_get_next_tasks_with_dependencies(self) -> None:
        """Test getting next tasks with dependencies."""
        # Add task with dependency
        self.manager.add_task("dep_task", "Dependency Task", "url1", "path1", 1000)
        self.manager.add_task("main_task", "Main Task", "url2", "path2", 2000, 
                            dependencies=["dep_task"])
        
        # Main task should not be schedulable yet
        next_tasks = self.manager.get_next_tasks()
        schedulable_ids = [task.task_id for task in next_tasks]
        assert "main_task" not in schedulable_ids
        
        # Complete dependency
        self.manager.mark_task_running("dep_task")
        self.manager.mark_task_completed("dep_task")
        
        # Now main task should be schedulable
        next_tasks = self.manager.get_next_tasks()
        schedulable_ids = [task.task_id for task in next_tasks]
        assert "main_task" in schedulable_ids

    def test_mark_task_running(self) -> None:
        """Test marking task as running."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000)
        
        result = self.manager.mark_task_running("test_task")
        
        assert result is True
        assert "test_task" in self.manager.running_tasks
        assert len(self.manager.pending_queue) == 0
        
        task = self.manager.running_tasks["test_task"]
        assert task.scheduled_at is not None

    def test_mark_nonexistent_task_running(self) -> None:
        """Test marking nonexistent task as running."""
        result = self.manager.mark_task_running("nonexistent")
        assert result is False

    def test_mark_task_completed(self) -> None:
        """Test marking task as completed."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000)
        self.manager.mark_task_running("test_task")
        
        result = self.manager.mark_task_completed("test_task")
        
        assert result is True
        assert "test_task" in self.manager.completed_tasks
        assert "test_task" not in self.manager.running_tasks

    def test_mark_task_failed_with_retry(self) -> None:
        """Test marking task as failed with retry."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000, max_attempts=3)
        self.manager.mark_task_running("test_task")
        
        result = self.manager.mark_task_failed("test_task", retry=True)
        
        assert result is True
        assert "test_task" not in self.manager.running_tasks
        assert "test_task" not in self.manager.failed_tasks
        # Should be back in pending queue with incremented attempts
        task = self.manager.get_task("test_task")
        assert task.attempts == 1

    def test_mark_task_failed_max_attempts(self) -> None:
        """Test marking task as failed after max attempts."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000, max_attempts=1)
        self.manager.mark_task_running("test_task")
        
        # First failure should exhaust max attempts
        result = self.manager.mark_task_failed("test_task", retry=True)
        
        assert result is True
        assert "test_task" in self.manager.failed_tasks
        assert "test_task" not in self.manager.running_tasks

    def test_clear_completed_tasks(self) -> None:
        """Test clearing completed tasks."""
        # Add and complete some tasks
        self.manager.add_task("task1", "Task 1", "url1", "path1", 1000)
        self.manager.add_task("task2", "Task 2", "url2", "path2", 2000)
        
        self.manager.mark_task_running("task1")
        self.manager.mark_task_completed("task1")
        self.manager.mark_task_running("task2")
        self.manager.mark_task_completed("task2")
        
        assert len(self.manager.completed_tasks) == 2
        
        self.manager.clear_completed_tasks()
        
        assert len(self.manager.completed_tasks) == 0

    def test_clear_failed_tasks(self) -> None:
        """Test clearing failed tasks."""
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000, max_attempts=1)
        self.manager.mark_task_running("test_task")
        self.manager.mark_task_failed("test_task", retry=False)
        
        assert len(self.manager.failed_tasks) == 1
        
        self.manager.clear_failed_tasks()
        
        assert len(self.manager.failed_tasks) == 0

    def test_get_queue_statistics(self) -> None:
        """Test getting queue statistics."""
        # Add various tasks
        self.manager.add_task("pending1", "Pending 1", "url1", "path1", 1000, TaskPriority.HIGH)
        self.manager.add_task("pending2", "Pending 2", "url2", "path2", 2000, TaskPriority.NORMAL)
        self.manager.add_task("running1", "Running 1", "url3", "path3", 1500, TaskPriority.LOW)
        self.manager.add_task("completed1", "Completed 1", "url4", "path4", 3000)
        
        # Change states
        self.manager.mark_task_running("running1")
        self.manager.mark_task_running("completed1")
        self.manager.mark_task_completed("completed1")
        
        stats = self.manager.get_queue_statistics()
        
        assert stats.total_tasks == 4
        assert stats.pending_tasks == 2
        assert stats.running_tasks == 1
        assert stats.completed_tasks == 1
        assert stats.failed_tasks == 0
        assert stats.average_wait_time >= 0
        assert stats.queue_efficiency == 100.0  # No failed tasks
        assert "HIGH" in stats.priority_distribution
        assert "NORMAL" in stats.priority_distribution

    def test_callback_registration(self) -> None:
        """Test callback registration."""
        scheduled_callback = Mock()
        completed_callback = Mock()
        changed_callback = Mock()
        
        self.manager.register_task_scheduled_callback(scheduled_callback)
        self.manager.register_task_completed_callback(completed_callback)
        self.manager.register_queue_changed_callback(changed_callback)
        
        assert scheduled_callback in self.manager.task_scheduled_callbacks
        assert completed_callback in self.manager.task_completed_callbacks
        assert changed_callback in self.manager.queue_changed_callbacks

    def test_callback_triggering(self) -> None:
        """Test callback triggering."""
        completed_callback = Mock()
        changed_callback = Mock()
        
        self.manager.register_task_completed_callback(completed_callback)
        self.manager.register_queue_changed_callback(changed_callback)
        
        # Add and complete task
        self.manager.add_task("test_task", "Test Task", "url", "path", 1000)
        self.manager.mark_task_running("test_task")
        self.manager.mark_task_completed("test_task")
        
        # Callbacks should be triggered
        completed_callback.assert_called()
        changed_callback.assert_called()

    def test_global_queue_manager_instance(self) -> None:
        """Test global queue manager instance."""
        assert queue_manager is not None
        assert isinstance(queue_manager, QueueManager)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

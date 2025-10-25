import pytest
import time
import threading
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, List, Optional, Set

from src.core.task_state_manager import (
    TaskStateManager, TaskState, StateTransitionError, StateTransition,
    TaskStateInfo, task_state_manager
)
from src.core.exceptions import (
    VidTaniumException, ErrorCategory, ErrorSeverity, ErrorContext
)


class TestTaskState:
    """Test suite for TaskState enum."""

    def test_state_values(self) -> None:
        """Test enum values."""
        assert TaskState.CREATED.value == "created"
        assert TaskState.QUEUED.value == "queued"
        assert TaskState.PREPARING.value == "preparing"
        assert TaskState.RUNNING.value == "running"
        assert TaskState.PAUSED.value == "paused"
        assert TaskState.PAUSING.value == "pausing"
        assert TaskState.RESUMING.value == "resuming"
        assert TaskState.CANCELING.value == "canceling"
        assert TaskState.CANCELED.value == "canceled"
        assert TaskState.COMPLETED.value == "completed"
        assert TaskState.FAILED.value == "failed"
        assert TaskState.RETRYING.value == "retrying"
        assert TaskState.CLEANING_UP.value == "cleaning_up"


class TestStateTransitionError:
    """Test suite for StateTransitionError exception."""

    def test_error_creation(self) -> None:
        """Test StateTransitionError creation."""
        error = StateTransitionError(
            from_state=TaskState.COMPLETED,
            to_state=TaskState.RUNNING,
            reason="Task already completed"
        )
        
        assert error.from_state == TaskState.COMPLETED
        assert error.to_state == TaskState.RUNNING
        assert "completed" in error.message
        assert "running" in error.message
        assert "Task already completed" in error.message
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM

    def test_error_without_reason(self) -> None:
        """Test StateTransitionError without reason."""
        error = StateTransitionError(
            from_state=TaskState.FAILED,
            to_state=TaskState.COMPLETED
        )
        
        assert "failed" in error.message
        assert "completed" in error.message


class TestStateTransition:
    """Test suite for StateTransition dataclass."""

    def test_transition_creation(self) -> None:
        """Test StateTransition creation with all fields."""
        transition = StateTransition(
            from_state=TaskState.QUEUED,
            to_state=TaskState.RUNNING,
            timestamp=1234567890.0,
            reason="Task started",
            metadata={"worker_id": "worker_1"}
        )
        
        assert transition.from_state == TaskState.QUEUED
        assert transition.to_state == TaskState.RUNNING
        assert transition.timestamp == 1234567890.0
        assert transition.reason == "Task started"
        assert transition.metadata == {"worker_id": "worker_1"}

    def test_transition_defaults(self) -> None:
        """Test StateTransition with default values."""
        transition = StateTransition(
            from_state=TaskState.CREATED,
            to_state=TaskState.QUEUED,
            timestamp=time.time()
        )
        
        assert transition.reason is None
        assert transition.metadata is None


class TestTaskStateInfo:
    """Test suite for TaskStateInfo dataclass."""

    def test_state_info_creation(self) -> None:
        """Test TaskStateInfo creation with all fields."""
        transitions = [
            StateTransition(TaskState.CREATED, TaskState.QUEUED, time.time())
        ]
        
        state_info = TaskStateInfo(
            task_id="test_task",
            current_state=TaskState.RUNNING,
            previous_state=TaskState.QUEUED,
            state_changed_at=1234567890.0,
            transition_history=transitions,
            retry_count=2,
            error_count=1,
            metadata={"priority": "high"}
        )
        
        assert state_info.task_id == "test_task"
        assert state_info.current_state == TaskState.RUNNING
        assert state_info.previous_state == TaskState.QUEUED
        assert state_info.state_changed_at == 1234567890.0
        assert state_info.transition_history == transitions
        assert state_info.retry_count == 2
        assert state_info.error_count == 1
        assert state_info.metadata == {"priority": "high"}

    def test_state_info_defaults(self) -> None:
        """Test TaskStateInfo with default values."""
        state_info = TaskStateInfo(
            task_id="test_task",
            current_state=TaskState.CREATED
        )
        
        assert state_info.previous_state is None
        assert state_info.state_changed_at > 0
        assert state_info.transition_history == []
        assert state_info.retry_count == 0
        assert state_info.error_count == 0
        assert state_info.last_error is None
        assert state_info.metadata == {}


class TestTaskStateManager:
    """Test suite for TaskStateManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.manager = TaskStateManager()

    def test_initialization(self) -> None:
        """Test TaskStateManager initialization."""
        assert isinstance(self.manager.task_states, dict)
        assert isinstance(self.manager.state_callbacks, dict)
        assert isinstance(self.manager.transition_callbacks, list)
        assert isinstance(self.manager.lock, threading.RLock)
        assert isinstance(self.manager.valid_transitions, dict)
        assert isinstance(self.manager.active_states, set)
        assert isinstance(self.manager.terminal_states, set)
        assert isinstance(self.manager.transitional_states, set)

    def test_valid_transitions_definition(self) -> None:
        """Test valid transitions are properly defined."""
        transitions = self.manager.valid_transitions
        
        # Check some key transitions
        assert TaskState.QUEUED in transitions[TaskState.CREATED]
        assert TaskState.RUNNING in transitions[TaskState.PREPARING]
        assert TaskState.PAUSED in transitions[TaskState.PAUSING]
        assert TaskState.COMPLETED in transitions[TaskState.RUNNING]
        assert TaskState.RETRYING in transitions[TaskState.FAILED]
        
        # Terminal states should have limited or no transitions
        assert len(transitions[TaskState.COMPLETED]) == 0
        assert len(transitions[TaskState.CANCELED]) == 0

    def test_create_task(self) -> None:
        """Test creating a new task."""
        metadata = {"priority": "high", "user": "test_user"}
        
        state_info = self.manager.create_task("test_task", metadata)
        
        assert state_info.task_id == "test_task"
        assert state_info.current_state == TaskState.CREATED
        assert state_info.metadata == metadata
        assert "test_task" in self.manager.task_states

    def test_create_duplicate_task(self) -> None:
        """Test creating duplicate task raises error."""
        self.manager.create_task("test_task")
        
        with pytest.raises(ValueError, match="already exists"):
            self.manager.create_task("test_task")

    def test_transition_state_valid(self) -> None:
        """Test valid state transition."""
        self.manager.create_task("test_task")
        
        result = self.manager.transition_state(
            "test_task",
            TaskState.QUEUED,
            reason="Task queued for processing",
            metadata={"queue_position": 1}
        )
        
        assert result is True
        
        state_info = self.manager.get_task_state("test_task")
        assert state_info.current_state == TaskState.QUEUED
        assert state_info.previous_state == TaskState.CREATED
        assert len(state_info.transition_history) == 1
        
        transition = state_info.transition_history[0]
        assert transition.from_state == TaskState.CREATED
        assert transition.to_state == TaskState.QUEUED
        assert transition.reason == "Task queued for processing"
        assert transition.metadata == {"queue_position": 1}

    def test_transition_state_invalid(self) -> None:
        """Test invalid state transition."""
        self.manager.create_task("test_task")
        
        # Try to go directly from CREATED to RUNNING (invalid)
        result = self.manager.transition_state("test_task", TaskState.RUNNING)
        
        assert result is False
        
        # State should remain unchanged
        state_info = self.manager.get_task_state("test_task")
        assert state_info.current_state == TaskState.CREATED

    def test_transition_state_force(self) -> None:
        """Test forced state transition."""
        self.manager.create_task("test_task")
        
        # Force invalid transition
        result = self.manager.transition_state(
            "test_task",
            TaskState.RUNNING,
            reason="Forced transition",
            force=True
        )
        
        assert result is True
        
        state_info = self.manager.get_task_state("test_task")
        assert state_info.current_state == TaskState.RUNNING

    def test_transition_nonexistent_task(self) -> None:
        """Test transitioning nonexistent task."""
        result = self.manager.transition_state("nonexistent", TaskState.QUEUED)
        assert result is False

    def test_is_valid_transition(self) -> None:
        """Test transition validation."""
        # Valid transitions
        assert self.manager._is_valid_transition(TaskState.CREATED, TaskState.QUEUED)
        assert self.manager._is_valid_transition(TaskState.RUNNING, TaskState.COMPLETED)
        assert self.manager._is_valid_transition(TaskState.FAILED, TaskState.RETRYING)
        
        # Invalid transitions
        assert not self.manager._is_valid_transition(TaskState.COMPLETED, TaskState.RUNNING)
        assert not self.manager._is_valid_transition(TaskState.CREATED, TaskState.RUNNING)

    def test_handle_special_transitions_retry(self) -> None:
        """Test special handling for retry transitions."""
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        self.manager.transition_state("test_task", TaskState.PREPARING)
        self.manager.transition_state("test_task", TaskState.RUNNING)
        self.manager.transition_state("test_task", TaskState.FAILED)
        
        # Transition to retrying should increment retry count
        self.manager.transition_state("test_task", TaskState.RETRYING)
        
        state_info = self.manager.get_task_state("test_task")
        assert state_info.retry_count == 1

    def test_handle_special_transitions_failed(self) -> None:
        """Test special handling for failed transitions."""
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        self.manager.transition_state("test_task", TaskState.PREPARING)
        self.manager.transition_state("test_task", TaskState.RUNNING)
        
        # Transition to failed should increment error count
        self.manager.transition_state("test_task", TaskState.FAILED, reason="Network error")
        
        state_info = self.manager.get_task_state("test_task")
        assert state_info.error_count == 1
        assert state_info.metadata.get("last_error_reason") == "Network error"

    def test_handle_special_transitions_completed(self) -> None:
        """Test special handling for completed transitions."""
        self.manager.create_task("test_task")
        state_info = self.manager.get_task_state("test_task")
        state_info.metadata["last_error_reason"] = "Previous error"
        
        self.manager.transition_state("test_task", TaskState.QUEUED)
        self.manager.transition_state("test_task", TaskState.PREPARING)
        self.manager.transition_state("test_task", TaskState.RUNNING)
        self.manager.transition_state("test_task", TaskState.COMPLETED)
        
        # Completion should clear error information
        state_info = self.manager.get_task_state("test_task")
        assert state_info.last_error is None
        assert "last_error_reason" not in state_info.metadata

    def test_handle_special_transitions_transitional_timeout(self) -> None:
        """Test timeout setting for transitional states."""
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        self.manager.transition_state("test_task", TaskState.PREPARING)
        self.manager.transition_state("test_task", TaskState.RUNNING)
        
        # Transition to transitional state should set timeout
        self.manager.transition_state("test_task", TaskState.PAUSING)
        
        state_info = self.manager.get_task_state("test_task")
        assert "transition_timeout" in state_info.metadata
        assert state_info.metadata["transition_timeout"] > time.time()

    def test_get_task_state(self) -> None:
        """Test getting task state."""
        self.manager.create_task("test_task")
        
        state_info = self.manager.get_task_state("test_task")
        assert state_info is not None
        assert state_info.task_id == "test_task"
        
        # Test nonexistent task
        assert self.manager.get_task_state("nonexistent") is None

    def test_get_tasks_by_state(self) -> None:
        """Test getting tasks by state."""
        # Create tasks in different states
        self.manager.create_task("task1")
        self.manager.create_task("task2")
        self.manager.create_task("task3")
        
        self.manager.transition_state("task1", TaskState.QUEUED)
        self.manager.transition_state("task2", TaskState.QUEUED)
        # task3 remains in CREATED state
        
        queued_tasks = self.manager.get_tasks_by_state(TaskState.QUEUED)
        created_tasks = self.manager.get_tasks_by_state(TaskState.CREATED)
        
        assert len(queued_tasks) == 2
        assert len(created_tasks) == 1
        assert queued_tasks[0].task_id in ["task1", "task2"]
        assert queued_tasks[1].task_id in ["task1", "task2"]
        assert created_tasks[0].task_id == "task3"

    def test_get_active_tasks(self) -> None:
        """Test getting active (non-terminal) tasks."""
        # Create tasks in different states
        self.manager.create_task("active1")
        self.manager.create_task("active2")
        self.manager.create_task("completed")
        self.manager.create_task("failed")
        
        self.manager.transition_state("active1", TaskState.QUEUED)
        self.manager.transition_state("active2", TaskState.QUEUED)
        self.manager.transition_state("active2", TaskState.PREPARING)
        self.manager.transition_state("active2", TaskState.RUNNING)
        
        # Move to terminal states
        self.manager.transition_state("completed", TaskState.QUEUED)
        self.manager.transition_state("completed", TaskState.PREPARING)
        self.manager.transition_state("completed", TaskState.RUNNING)
        self.manager.transition_state("completed", TaskState.COMPLETED)
        
        self.manager.transition_state("failed", TaskState.QUEUED)
        self.manager.transition_state("failed", TaskState.PREPARING)
        self.manager.transition_state("failed", TaskState.FAILED)
        
        active_tasks = self.manager.get_active_tasks()
        
        # Should have 2 active tasks (active1, active2)
        assert len(active_tasks) == 2
        active_ids = [task.task_id for task in active_tasks]
        assert "active1" in active_ids
        assert "active2" in active_ids
        assert "completed" not in active_ids
        assert "failed" not in active_ids

    def test_cleanup_task_terminal_state(self) -> None:
        """Test cleaning up task in terminal state."""
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        self.manager.transition_state("test_task", TaskState.PREPARING)
        self.manager.transition_state("test_task", TaskState.RUNNING)
        self.manager.transition_state("test_task", TaskState.COMPLETED)
        
        result = self.manager.cleanup_task("test_task")
        
        assert result is True
        assert "test_task" not in self.manager.task_states

    def test_cleanup_task_non_terminal_state(self) -> None:
        """Test cleaning up task in non-terminal state."""
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        
        result = self.manager.cleanup_task("test_task")
        
        assert result is False
        assert "test_task" in self.manager.task_states

    def test_cleanup_nonexistent_task(self) -> None:
        """Test cleaning up nonexistent task."""
        result = self.manager.cleanup_task("nonexistent")
        assert result is False

    def test_check_transitional_timeouts(self) -> None:
        """Test checking for transitional state timeouts."""
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        self.manager.transition_state("test_task", TaskState.PREPARING)
        self.manager.transition_state("test_task", TaskState.RUNNING)
        self.manager.transition_state("test_task", TaskState.PAUSING)
        
        # Manually set timeout to past time
        state_info = self.manager.get_task_state("test_task")
        state_info.metadata["transition_timeout"] = time.time() - 1
        
        timed_out_tasks = self.manager.check_transitional_timeouts()
        
        assert "test_task" in timed_out_tasks
        
        # Task should be transitioned to failed state
        state_info = self.manager.get_task_state("test_task")
        assert state_info.current_state == TaskState.FAILED

    def test_register_state_callback(self) -> None:
        """Test registering state callback."""
        callback = Mock()
        
        self.manager.register_state_callback(TaskState.COMPLETED, callback)
        
        assert TaskState.COMPLETED in self.manager.state_callbacks
        assert callback in self.manager.state_callbacks[TaskState.COMPLETED]

    def test_register_transition_callback(self) -> None:
        """Test registering transition callback."""
        callback = Mock()
        
        self.manager.register_transition_callback(callback)
        
        assert callback in self.manager.transition_callbacks

    def test_trigger_state_callbacks(self) -> None:
        """Test triggering state callbacks."""
        callback = Mock()
        self.manager.register_state_callback(TaskState.COMPLETED, callback)
        
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        self.manager.transition_state("test_task", TaskState.PREPARING)
        self.manager.transition_state("test_task", TaskState.RUNNING)
        self.manager.transition_state("test_task", TaskState.COMPLETED)
        
        callback.assert_called_once_with("test_task")

    def test_trigger_transition_callbacks(self) -> None:
        """Test triggering transition callbacks."""
        callback = Mock()
        self.manager.register_transition_callback(callback)
        
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        
        callback.assert_called_once_with("test_task", TaskState.CREATED, TaskState.QUEUED)

    def test_callback_error_handling(self) -> None:
        """Test error handling in callbacks."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()
        
        self.manager.register_state_callback(TaskState.QUEUED, error_callback)
        self.manager.register_state_callback(TaskState.QUEUED, good_callback)
        
        self.manager.create_task("test_task")
        self.manager.transition_state("test_task", TaskState.QUEUED)
        
        # Both callbacks should be called despite error
        error_callback.assert_called_once()
        good_callback.assert_called_once()

    def test_get_state_statistics(self) -> None:
        """Test getting state statistics."""
        # Create tasks in various states
        self.manager.create_task("created1")
        self.manager.create_task("created2")
        self.manager.create_task("queued1")
        self.manager.create_task("running1")
        self.manager.create_task("completed1")
        
        self.manager.transition_state("queued1", TaskState.QUEUED)
        self.manager.transition_state("running1", TaskState.QUEUED)
        self.manager.transition_state("running1", TaskState.PREPARING)
        self.manager.transition_state("running1", TaskState.RUNNING)
        self.manager.transition_state("completed1", TaskState.QUEUED)
        self.manager.transition_state("completed1", TaskState.PREPARING)
        self.manager.transition_state("completed1", TaskState.RUNNING)
        self.manager.transition_state("completed1", TaskState.COMPLETED)
        
        stats = self.manager.get_state_statistics()
        
        assert stats["total_tasks"] == 5
        assert stats["state_counts"][TaskState.CREATED.value] == 2
        assert stats["state_counts"][TaskState.QUEUED.value] == 1
        assert stats["state_counts"][TaskState.RUNNING.value] == 1
        assert stats["state_counts"][TaskState.COMPLETED.value] == 1
        assert stats["active_tasks"] == 4  # All except completed
        assert stats["terminal_tasks"] == 1  # Only completed

    def test_detect_state_issues(self) -> None:
        """Test detecting state issues."""
        # Create task stuck in transitional state
        self.manager.create_task("stuck_task")
        self.manager.transition_state("stuck_task", TaskState.QUEUED)
        self.manager.transition_state("stuck_task", TaskState.PREPARING)
        self.manager.transition_state("stuck_task", TaskState.RUNNING)
        self.manager.transition_state("stuck_task", TaskState.PAUSING)
        
        # Manually set old timestamp
        state_info = self.manager.get_task_state("stuck_task")
        state_info.state_changed_at = time.time() - 400  # 400 seconds ago
        
        # Create task with excessive retries
        self.manager.create_task("retry_task")
        retry_state_info = self.manager.get_task_state("retry_task")
        retry_state_info.retry_count = 15
        
        # Create old failed task
        self.manager.create_task("old_failed")
        self.manager.transition_state("old_failed", TaskState.QUEUED)
        self.manager.transition_state("old_failed", TaskState.PREPARING)
        self.manager.transition_state("old_failed", TaskState.FAILED)
        old_failed_info = self.manager.get_task_state("old_failed")
        old_failed_info.state_changed_at = time.time() - 90000  # 25 hours ago
        
        issues = self.manager.detect_state_issues()
        
        assert len(issues) == 3
        assert any("stuck in transitional state" in issue for issue in issues)
        assert any("excessive retry count" in issue for issue in issues)
        assert any("failed state for over 24 hours" in issue for issue in issues)

    def test_global_task_state_manager_instance(self) -> None:
        """Test global task state manager instance."""
        assert task_state_manager is not None
        assert isinstance(task_state_manager, TaskStateManager)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

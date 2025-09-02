import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, ANY
# Removed List, Optional, Callable, cast as per linter feedback
from typing import Dict, Any, List

from src.core.scheduler import TaskScheduler, SchedulerTask, TaskType


class TestSchedulerTask:
    """Test suite for the SchedulerTask class."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.now = datetime(2023, 1, 1, 12, 0, 0)  # Sunday, noon

    @patch('datetime.datetime')
    def test_init_defaults(self, mock_datetime: MagicMock) -> None:
        """Test initialization with default values."""
        # Configure mock
        mock_datetime.now.return_value = self.now

        # Create task with minimal arguments
        task = SchedulerTask()

        # Verify defaults
        assert task.task_id is not None
        assert task.name.startswith("Task-")
        assert task.task_type == TaskType.ONE_TIME
        assert task.data == {}
        assert task.first_run == self.now
        assert task.interval == 0
        assert task.days == []
        assert task.enabled is True
        assert task.last_run is None
        assert task.next_run == self.now  # For one-time tasks, next_run is first_run

    def test_init_with_values(self) -> None:
        """Test initialization with custom values."""
        task_id = "test-task-1"
        name = "Test Task"
        task_type = TaskType.DAILY
        data = {"key": "value"}
        first_run = datetime(2023, 1, 1, 8, 0, 0)
        interval = 3600
        days = [0, 2, 4]  # Monday, Wednesday, Friday

        task = SchedulerTask(
            task_id=task_id,
            name=name,
            task_type=task_type,
            data=data,
            first_run=first_run,
            interval=interval,
            days=days
        )

        assert task.task_id == task_id
        assert task.name == name
        assert task.task_type == task_type
        assert task.data == data
        assert task.first_run == first_run
        assert task.interval == interval
        assert task.days == days

    @patch('datetime.datetime')
    def test_calculate_next_run_one_time_future(self, mock_datetime: MagicMock) -> None:
        """Test next run calculation for one-time task scheduled in the future."""
        # Now is 2023-01-01 12:00
        mock_datetime.now.return_value = self.now

        # Task scheduled for 2023-01-01 14:00 (2 hours later)
        future_time = self.now + timedelta(hours=2)
        task = SchedulerTask(
            task_type=TaskType.ONE_TIME,
            first_run=future_time
        )

        assert task.next_run == future_time

    @patch('datetime.datetime')
    def test_calculate_next_run_one_time_past(self, mock_datetime: MagicMock) -> None:
        """Test next run calculation for one-time task scheduled in the past."""
        # Now is 2023-01-01 12:00
        mock_datetime.now.return_value = self.now

        # Task scheduled for 2023-01-01 10:00 (2 hours ago)
        past_time = self.now - timedelta(hours=2)
        task = SchedulerTask(
            task_type=TaskType.ONE_TIME,
            first_run=past_time
        )

        # For one-time tasks, next_run should still be first_run even if it's in the past
        assert task.next_run == past_time

    @patch('datetime.datetime')
    def test_calculate_next_run_daily(self, mock_datetime: MagicMock) -> None:
        """Test next run calculation for daily task."""
        # Now is 2023-01-01 12:00
        mock_datetime.now.return_value = self.now

        # Configure mock for datetime.combine
        mock_datetime.combine = datetime.combine

        # Task scheduled for 14:00 daily
        first_run = datetime(2023, 1, 1, 14, 0, 0)
        task = SchedulerTask(
            task_type=TaskType.DAILY,
            first_run=first_run
        )

        # Next run should be today at 14:00
        expected = datetime(2023, 1, 1, 14, 0, 0)
        assert task.next_run == expected

        # If current time is after the scheduled time, next run should be tomorrow
        mock_datetime.now.return_value = datetime(2023, 1, 1, 15, 0, 0)
        # Re-create task or call a method to re-calculate next_run if state changes affect it
        task_after_time = SchedulerTask(
            task_type=TaskType.DAILY,
            first_run=first_run
        )
        expected_tomorrow = datetime(2023, 1, 2, 14, 0, 0)
        assert task_after_time.next_run == expected_tomorrow

    @patch('datetime.datetime')
    def test_calculate_next_run_weekly(self, mock_datetime: MagicMock) -> None:
        """Test next run calculation for weekly task."""
        # Sunday 2023-01-01 12:00
        mock_datetime.now.return_value = self.now

        # Configure mock for datetime.combine
        mock_datetime.combine = datetime.combine

        # Task scheduled for 14:00 on Monday (weekday 0) and Wednesday (weekday 2)
        first_run = datetime(2023, 1, 1, 14, 0, 0)  # Time part is used
        task = SchedulerTask(
            task_type=TaskType.WEEKLY,
            first_run=first_run,
            days=[0, 2]  # Monday and Wednesday
        )

        # Next run should be Monday (tomorrow) at 14:00
        expected = datetime(2023, 1, 2, 14, 0, 0)  # Monday
        assert task.next_run == expected

    @patch('datetime.datetime')
    def test_calculate_next_run_interval(self, mock_datetime: MagicMock) -> None:
        """Test next run calculation for interval task."""
        # Now is 2023-01-01 12:00
        mock_datetime.now.return_value = self.now

        # Task scheduled to run every hour, first run at 10:00 (2 hours ago)
        first_run_for_interval = self.now - timedelta(hours=2)  # 10:00
        task = SchedulerTask(
            task_type=TaskType.INTERVAL,
            first_run=first_run_for_interval,
            interval=3600  # 1 hour in seconds
        )
        # Expected: first_run (10:00) + N * interval > now (12:00)
        # N=1: 10:00 + 1h = 11:00 (past)
        # N=2: 10:00 + 2h = 12:00 (past or now, logic is `intervals_passed = int(time_diff / self.interval) + 1`)
        # time_diff = (12:00 - 10:00).total_seconds() = 7200
        # intervals_passed = int(7200 / 3600) + 1 = 2 + 1 = 3
        # next_run = 10:00 + 3 * 3600s = 10:00 + 3h = 13:00
        expected = first_run_for_interval + timedelta(hours=3)
        assert task.next_run == expected

    def test_mark_executed(self) -> None:
        """Test marking a task as executed."""
        # Create a daily task
        task = SchedulerTask(
            task_type=TaskType.DAILY,
            first_run=datetime(2023, 1, 1, 8, 0, 0)
        )

        with patch('datetime.datetime') as mock_datetime_patch:
            # Set current time to 2023-01-01 10:00
            execution_time = datetime(2023, 1, 1, 10, 0, 0)
            mock_datetime_patch.now.return_value = execution_time
            # Ensure datetime.combine is also available if _calculate_next_run uses it indirectly
            mock_datetime_patch.combine = datetime.combine

            # Mark as executed
            task.mark_executed()

            # Check that last_run was updated
            assert task.last_run == execution_time

            # For daily task, next_run should be tomorrow at 8:00
            expected_next = datetime(2023, 1, 2, 8, 0, 0)
            assert task.next_run == expected_next

    def test_enable_disable(self) -> None:
        """Test enabling and disabling a task."""
        with patch('datetime.datetime') as mock_datetime_patch:  # Patch for consistent 'now'
            mock_datetime_patch.now.return_value = self.now
            mock_datetime_patch.combine = datetime.combine

            task = SchedulerTask(task_type=TaskType.DAILY, first_run=self.now)

            # By default, task is enabled
            assert task.enabled is True
            assert task.next_run is not None

            # Disable task
            task.disable()
            assert task.enabled is False
            assert task.next_run is None

            # Enable task
            task.enable()
            assert task.enabled is True
            assert task.next_run is not None

    def test_to_dict(self) -> None:
        """Test converting task to dictionary."""
        first_run = datetime(2023, 1, 1, 8, 0, 0)
        task = SchedulerTask(
            task_id="test-task",
            name="Test Task",
            task_type=TaskType.WEEKLY,
            data={"key": "value"},
            first_run=first_run,
            interval=3600,
            days=[0, 2, 4]
        )

        task_dict = task.to_dict()

        assert task_dict["task_id"] == "test-task"
        assert task_dict["name"] == "Test Task"
        assert task_dict["task_type"] == "weekly"
        assert task_dict["data"] == {"key": "value"}
        assert task_dict["first_run"] == first_run.isoformat()
        assert task_dict["interval"] == 3600
        assert task_dict["days"] == [0, 2, 4]
        assert task_dict["enabled"] is True

    def test_from_dict(self) -> None:
        """Test creating task from dictionary."""
        task_data_dict: Dict[str, Any] = {
            "task_id": "test-task",
            "name": "Test Task",
            "task_type": "weekly",
            "data": {"key": "value"},
            "first_run": "2023-01-01T08:00:00",
            "interval": 3600,
            "days": [0, 2, 4],
            "enabled": True,
            "last_run": "2023-01-01T10:00:00"
            # next_run is calculated, not directly from dict
        }

        with patch('datetime.datetime') as mock_datetime_patch:
            mock_datetime_patch.now.return_value = self.now  # For _calculate_next_run
            mock_datetime_patch.fromisoformat = datetime.fromisoformat
            mock_datetime_patch.combine = datetime.combine

            task = SchedulerTask.from_dict(task_data_dict)

        assert task.task_id == "test-task"
        assert task.name == "Test Task"
        assert task.task_type == TaskType.WEEKLY
        assert task.data == {"key": "value"}
        assert task.first_run == datetime(2023, 1, 1, 8, 0, 0)
        assert task.interval == 3600
        assert task.days == [0, 2, 4]
        assert task.enabled is True
        assert task.last_run == datetime(2023, 1, 1, 10, 0, 0)
        # Add assertion for next_run if its calculation is stable and predictable here
        # For this weekly task, last run 2023-01-01 10:00 (Sun), days [Mon, Wed, Fri], first_run time 08:00
        # Next run should be Mon, 2023-01-02 08:00:00
        assert task.next_run == datetime(2023, 1, 2, 8, 0, 0)


class MockScheduler(TaskScheduler):
    """测试用的调度器子类，允许访问受保护的方法进行测试"""

    def public_load_tasks(self) -> None:
        self._load_tasks()

    def public_save_tasks(self) -> None:
        self._save_tasks()

    def public_scheduler_loop(self) -> None:
        self._scheduler_loop()

    def public_execute_task(self, task: SchedulerTask) -> None:
        self._execute_task(task)


class TestTaskScheduler:
    """Test suite for the TaskScheduler class."""

    scheduler: MockScheduler  # Type hint for self.scheduler
    now: datetime
    task1: SchedulerTask
    task2: SchedulerTask

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.test_config_dir = Path(
            "/tmp/scheduler_test_dir")  # Ensure unique name

        with patch('pathlib.Path.mkdir'):
            self.scheduler = MockScheduler(str(self.test_config_dir))

        self.scheduler.tasks_file = self.test_config_dir / "scheduled_tasks.json"

        self.now = datetime(2023, 1, 1, 12, 0, 0)
        self.task1 = SchedulerTask(
            task_id="task1",
            name="Task One",
            task_type=TaskType.ONE_TIME,
            data={"handler_type": "test_handler"},
            first_run=self.now + timedelta(hours=1)
        )
        self.task2 = SchedulerTask(
            task_id="task2",
            name="Task Two",
            task_type=TaskType.DAILY,
            data={"handler_type": "test_handler"},
            first_run=self.now - timedelta(hours=1)
        )

    def test_init_default_config_dir(self) -> None:
        """Test initialization with default config directory."""
        with patch('pathlib.Path.home') as mock_home, \
                patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_home.return_value = Path("/fake/home")
            scheduler = TaskScheduler()
            assert scheduler.config_dir == Path(
                "/fake/home/.encrypted_video_downloader")
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_init_custom_config_dir(self) -> None:
        """Test initialization with custom config directory."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            scheduler = TaskScheduler("/custom/config/dir")
            assert scheduler.config_dir == Path("/custom/config/dir")
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_register_handler(self) -> None:
        """Test registering a task handler."""
        def sample_handler(task_data: Dict[str, Any]) -> None:
            if task_data:  # Use the parameter
                pass
        self.scheduler.register_handler("test_type", sample_handler)
        assert self.scheduler.task_handlers["test_type"] == sample_handler

    def test_add_task(self) -> None:
        """Test adding a task to the scheduler."""
        with patch.object(self.scheduler, 'public_save_tasks') as mock_save:
            task_id = self.scheduler.add_task(self.task1)
            assert task_id == "task1"
            assert self.scheduler.tasks["task1"] == self.task1
            mock_save.assert_called_once()

    def test_remove_task(self) -> None:
        """Test removing a task from the scheduler."""
        self.scheduler.tasks["task1"] = self.task1
        with patch.object(self.scheduler, 'public_save_tasks') as mock_save:
            result = self.scheduler.remove_task("task1")
            assert result is True
            assert "task1" not in self.scheduler.tasks
            mock_save.assert_called_once()
            result_non_existent = self.scheduler.remove_task("non_existent")
            assert result_non_existent is False

    def test_enable_task(self) -> None:
        """Test enabling a task."""
        self.task1.disable()  # Ensure it's disabled first
        self.scheduler.tasks["task1"] = self.task1
        with patch.object(self.scheduler, 'public_save_tasks') as mock_save, \
                patch('datetime.datetime') as mock_datetime_patch:  # For next_run calculation
            mock_datetime_patch.now.return_value = self.now
            mock_datetime_patch.combine = datetime.combine

            result = self.scheduler.enable_task("task1")
            assert result is True
            assert self.scheduler.tasks["task1"].enabled is True
            # Check if next_run is recalculated
            assert self.scheduler.tasks["task1"].next_run is not None
            mock_save.assert_called_once()
            result_non_existent = self.scheduler.enable_task("non_existent")
            assert result_non_existent is False

    def test_disable_task(self) -> None:
        """Test disabling a task."""
        self.scheduler.tasks["task1"] = self.task1  # Ensure it's enabled
        self.task1.enable()  # Explicitly enable
        with patch.object(self.scheduler, 'public_save_tasks') as mock_save:
            result = self.scheduler.disable_task("task1")
            assert result is True
            assert self.scheduler.tasks["task1"].enabled is False
            # Check if next_run is cleared
            assert self.scheduler.tasks["task1"].next_run is None
            mock_save.assert_called_once()
            result_non_existent = self.scheduler.disable_task("non_existent")
            assert result_non_existent is False

    def test_get_task(self) -> None:
        """Test retrieving a task by ID."""
        self.scheduler.tasks["task1"] = self.task1
        assert self.scheduler.get_task("task1") == self.task1
        assert self.scheduler.get_task("non_existent") is None

    def test_get_all_tasks(self) -> None:
        """Test retrieving all tasks."""
        self.scheduler.tasks["task1"] = self.task1
        self.scheduler.tasks["task2"] = self.task2
        all_tasks = self.scheduler.get_all_tasks()
        assert len(all_tasks) == 2
        assert self.task1 in all_tasks
        assert self.task2 in all_tasks

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_tasks(self, mock_json_load: MagicMock, mock_file_open: MagicMock,
                        mock_os_exists: MagicMock) -> None:
        """Test loading tasks from a file."""
        mock_os_exists.return_value = True
        task_data_list: List[dict[str, Any]] = [{
            "task_id": "task1", "name": "Task One", "task_type": "one_time",
            "data": {"handler_type": "test_handler"}, "first_run": (self.now + timedelta(hours=1)).isoformat(),
            "interval": 0, "days": [], "enabled": True
        }]
        mock_json_load.return_value = task_data_list

        # Mock from_dict to control task creation and avoid issues with datetime.now in _calculate_next_run
        # if not also patching datetime.datetime globally for this part of from_dict.
        created_task = SchedulerTask(task_id="task1", name="Task One", task_type=TaskType.ONE_TIME,
                                     data=task_data_list[0]["data"], first_run=datetime.fromisoformat(task_data_list[0]["first_run"]))

        with patch.object(SchedulerTask, 'from_dict', return_value=created_task) as mock_task_from_dict, \
                patch('datetime.datetime') as mock_datetime_patch:  # For _calculate_next_run inside from_dict if not fully mocked
            mock_datetime_patch.now.return_value = self.now
            mock_datetime_patch.fromisoformat = datetime.fromisoformat
            mock_datetime_patch.combine = datetime.combine

            self.scheduler.public_load_tasks()

            mock_file_open.assert_called_once_with(
                self.scheduler.tasks_file, 'r', encoding='utf-8')
            mock_task_from_dict.assert_called_once_with(task_data_list[0])
            assert "task1" in self.scheduler.tasks
            assert self.scheduler.tasks["task1"] == created_task

    def test_save_tasks(self) -> None:
        """Test saving tasks to a file."""
        self.scheduler.tasks["task1"] = self.task1

        # Ensure task1.to_dict() is called
        with patch.object(self.task1, 'to_dict', return_value={"task_id": "task1_dict_data"}) as mock_task_to_dict, \
                patch('builtins.open', new_callable=mock_open) as mock_file_open, \
                patch('json.dump') as mock_json_dump:

            self.scheduler.public_save_tasks()

            mock_task_to_dict.assert_called_once()
            mock_file_open.assert_called_once_with(
                self.scheduler.tasks_file, 'w', encoding='utf-8')
            mock_json_dump.assert_called_once_with(
                [{"task_id": "task1_dict_data"}], mock_file_open(), ensure_ascii=False, indent=2)

    def test_start_stop_scheduler(self) -> None:
        """Test starting and stopping the scheduler."""
        with patch('threading.Thread') as mock_thread_class:
            mock_thread_instance = MagicMock()
            mock_thread_class.return_value = mock_thread_instance

            self.scheduler.start()

            mock_thread_class.assert_called_once_with(target=ANY, daemon=True)
            # Verify the target was the scheduler's loop method
            called_target = mock_thread_class.call_args[1].get('target')
            assert called_target is not None
            assert called_target.__name__ == '_scheduler_loop'
            # Check it's bound to the scheduler instance
            assert getattr(called_target, '__self__', None) is self.scheduler

            assert mock_thread_instance.daemon is True
            mock_thread_instance.start.assert_called_once()
            assert self.scheduler.running is True

            # Starting again should do nothing if already running
            self.scheduler.start()
            assert mock_thread_instance.start.call_count == 1  # start() on instance, not class

            with patch.object(self.scheduler, 'public_save_tasks') as mock_save:
                self.scheduler.stop()
                assert self.scheduler.running is False
                mock_thread_instance.join.assert_called_once_with(timeout=2)
                mock_save.assert_called_once()

                # Stopping again should do nothing
                self.scheduler.stop()
                assert mock_thread_instance.join.call_count == 1

    def mock_sleep_stops_scheduler(self, _seconds: float) -> None:
        """Mock for time.sleep that stops the scheduler's running flag."""
        # _seconds is type-hinted but its value is not used in this mock's logic.
        setattr(self.scheduler, 'running', False)

    @patch('datetime.datetime')
    def test_scheduler_loop(self, mock_datetime_patch: MagicMock) -> None:
        """Test the scheduler loop."""
        mock_datetime_patch.now.return_value = self.now
        mock_datetime_patch.combine = datetime.combine  # Ensure combine is available

        # Task1 is due, Task2 is not
        self.task1.next_run = self.now - timedelta(minutes=5)
        self.task2.next_run = self.now + timedelta(minutes=5)
        self.scheduler.tasks = {"task1": self.task1, "task2": self.task2}

        with patch.object(self.scheduler, 'public_execute_task') as mock_execute_task, \
                patch('time.sleep', side_effect=self.mock_sleep_stops_scheduler):

            self.scheduler.running = True  # Manually set running for the loop
            self.scheduler.public_scheduler_loop()  # Call the loop once

            mock_execute_task.assert_called_once_with(self.task1)

    def test_execute_task(self) -> None:
        """Test executing a task."""
        task_to_execute = SchedulerTask(
            task_id="exec_task", name="Exec Task", task_type=TaskType.ONE_TIME,
            data={"handler_type": "test_handler"}, first_run=self.now
        )
        mock_task_handler = MagicMock()
        self.scheduler.register_handler("test_handler", mock_task_handler)

        with patch('datetime.datetime') as mock_datetime_patch, \
                patch.object(self.scheduler, 'public_save_tasks') as mock_save_tasks:

            execution_time = self.now + timedelta(hours=1)
            mock_datetime_patch.now.return_value = execution_time
            mock_datetime_patch.combine = datetime.combine

            self.scheduler.public_execute_task(task_to_execute)

            mock_task_handler.assert_called_once_with(
                {"handler_type": "test_handler"})
            assert task_to_execute.last_run == execution_time
            assert task_to_execute.enabled is False  # One-time task should be disabled
            mock_save_tasks.assert_called_once()

    def test_execute_task_no_handler(self) -> None:
        """Test executing a task with no registered handler."""
        task_no_handler = SchedulerTask(
            task_id="no_handler_task", name="No Handler Task", task_type=TaskType.ONE_TIME,
            data={"handler_type": "unknown_handler"}, first_run=self.now
        )

        with patch('datetime.datetime') as mock_datetime_patch, \
                patch.object(self.scheduler, 'public_save_tasks') as mock_save_tasks, \
                patch('loguru.logger.warning') as mock_logger_warning:  # To check warning

            execution_time = self.now + timedelta(hours=1)
            mock_datetime_patch.now.return_value = execution_time
            mock_datetime_patch.combine = datetime.combine

            self.scheduler.public_execute_task(task_no_handler)

            mock_logger_warning.assert_called_with(
                "No task handler found for type: unknown_handler")
            assert task_no_handler.last_run == execution_time  # Should still mark executed
            assert task_no_handler.enabled is False  # One-time task disabled
            mock_save_tasks.assert_called_once()

    def test_execute_task_handler_exception(self) -> None:
        """Test handling exceptions from task handlers."""
        task_exception = SchedulerTask(
            task_id="exception_task", name="Exception Task", task_type=TaskType.ONE_TIME,
            data={"handler_type": "exception_handler"}, first_run=self.now
        )
        mock_exception_handler = MagicMock(
            side_effect=Exception("Handler error!"))
        self.scheduler.register_handler(
            "exception_handler", mock_exception_handler)

        with patch('datetime.datetime') as mock_datetime_patch, \
                patch.object(self.scheduler, 'public_save_tasks') as mock_save_tasks, \
                patch('loguru.logger.error') as mock_logger_error:

            # Not used by task.mark_executed if handler fails before
            execution_time = self.now + timedelta(hours=1)
            # For logger if it logs current time
            mock_datetime_patch.now.return_value = execution_time
            mock_datetime_patch.combine = datetime.combine

            self.scheduler.public_execute_task(task_exception)

            mock_exception_handler.assert_called_once()
            mock_logger_error.assert_called_once()
            # Task should not be marked executed or saved if handler fails before mark_executed
            assert task_exception.last_run is None
            mock_save_tasks.assert_not_called()


if __name__ == "__main__":
    # Added --tb=line for concise tracebacks
    pytest.main(["-v", "--tb=line", "test_scheduler.py"])

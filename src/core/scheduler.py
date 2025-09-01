import threading
import time
import uuid
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, TypeVar
from loguru import logger


class TaskType(Enum):
    """Task type enumeration"""
    ONE_TIME = "one_time"  # One-time task
    DAILY = "daily"        # Daily task
    WEEKLY = "weekly"      # Weekly task
    INTERVAL = "interval"  # Interval-based recurring task


T = TypeVar('T', bound='SchedulerTask')


class SchedulerTask:
    """Scheduler task class"""

    def __init__(self,
                 task_id: Optional[str] = None,
                 name: Optional[str] = None,
                 task_type: TaskType = TaskType.ONE_TIME,
                 data: Optional[Dict[str, Any]] = None,
                 first_run: Optional[datetime] = None,
                 interval: int = 0,
                 days: Optional[List[int]] = None,
                 enabled: bool = True):
        """
        Initialize scheduler task

        Args:
            task_id: Task ID
            name: Task name
            task_type: Task type
            data: Task data
            first_run: First run time
            interval: Repeat interval (seconds)
            days: Weekly schedule (0-6, where 0 is Monday)
            enabled: Whether task is enabled
        """
        self.task_id: str = task_id or str(uuid.uuid4())
        self.name: str = name or f"Task-{self.task_id[:8]}"
        self.task_type: TaskType = task_type
        self.data: Dict[str, Any] = data or {}
        self.first_run: datetime = first_run or datetime.now()
        self.interval: int = interval
        self.days: List[int] = days or []
        self.enabled: bool = enabled
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = self._calculate_next_run()

    def _calculate_next_run(self) -> Optional[datetime]:
        """Calculate the next run time"""
        if not self.enabled:
            return None

        now = datetime.now()

        if self.last_run is None:
            # First calculation
            if self.first_run > now:
                return self.first_run

            # First run time has passed, calculate next run based on task type
            if self.task_type == TaskType.ONE_TIME:
                return self.first_run  # One-time task still returns first run time

            elif self.task_type == TaskType.INTERVAL:
                # Find the next time point that meets the interval
                time_diff = (now - self.first_run).total_seconds()
                intervals_passed = int(time_diff / self.interval) + 1
                return self.first_run + timedelta(seconds=intervals_passed * self.interval)

            elif self.task_type == TaskType.DAILY:
                # Today at specified time
                target_time = datetime(
                    now.year, now.month, now.day,
                    self.first_run.hour, self.first_run.minute, self.first_run.second
                )

                if target_time > now:
                    return target_time
                else:
                    # Same time tomorrow
                    return target_time + timedelta(days=1)

            elif self.task_type == TaskType.WEEKLY:
                if not self.days:
                    return None

                today_weekday = now.weekday()
                target_time = datetime(
                    now.year, now.month, now.day,
                    self.first_run.hour, self.first_run.minute, self.first_run.second
                )

                # Check if today is a specified weekday
                if today_weekday in self.days and target_time > now:
                    return target_time

                # Find the next matching weekday
                days_ahead = 1
                while days_ahead < 8:  # Maximum 7 days
                    next_day = (today_weekday + days_ahead) % 7
                    if next_day in self.days:
                        return target_time + timedelta(days=days_ahead)
                    days_ahead += 1

                return None

        else:
            # Not first calculation
            if self.task_type == TaskType.ONE_TIME:
                return None  # One-time task already executed

            elif self.task_type == TaskType.INTERVAL:
                return self.last_run + timedelta(seconds=self.interval)

            elif self.task_type == TaskType.DAILY:
                # Same time next day
                target_time = datetime(
                    self.last_run.year, self.last_run.month, self.last_run.day,
                    self.first_run.hour, self.first_run.minute, self.first_run.second
                )
                return target_time + timedelta(days=1)

            elif self.task_type == TaskType.WEEKLY:
                if not self.days:
                    return None

                last_run_weekday = self.last_run.weekday()

                # Find the next matching weekday
                days_ahead = 1
                while days_ahead < 8:  # Maximum 7 days
                    next_day = (last_run_weekday + days_ahead) % 7
                    if next_day in self.days:
                        last_run_date = datetime(
                            self.last_run.year, self.last_run.month, self.last_run.day
                        )
                        target_time = datetime.combine(
                            last_run_date.date(),
                            datetime.min.time()
                        ) + timedelta(days=days_ahead,
                                      hours=self.first_run.hour,
                                      minutes=self.first_run.minute,
                                      seconds=self.first_run.second)
                        return target_time
                    days_ahead += 1

                return None

    def mark_executed(self) -> None:
        """Mark task as executed"""
        self.last_run = datetime.now()
        self.next_run = self._calculate_next_run()

    def enable(self) -> None:
        """Enable task"""
        self.enabled = True
        self.next_run = self._calculate_next_run()

    def disable(self) -> None:
        """Disable task"""
        self.enabled = False
        self.next_run = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "task_type": self.task_type.value,
            "data": self.data,
            "first_run": self.first_run.isoformat() if self.first_run else None,
            "interval": self.interval,
            "days": self.days,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchedulerTask':
        """Create task from dictionary"""
        first_run = datetime.fromisoformat(
            data["first_run"]) if data.get("first_run") else None
        last_run = datetime.fromisoformat(
            data["last_run"]) if data.get("last_run") else None

        task_id: Optional[str] = data.get("task_id")
        name: Optional[str] = data.get("name")
        task_type_val: str = data.get("task_type", "one_time")
        task_type: TaskType = TaskType(task_type_val)
        task_data: Dict[str, Any] = data.get("data", {})
        interval: int = data.get("interval", 0)
        days: List[int] = data.get("days", [])
        enabled: bool = data.get("enabled", True)

        task = cls(
            task_id=task_id,
            name=name,
            task_type=task_type,
            data=task_data,
            first_run=first_run,
            interval=interval,
            days=days,
            enabled=enabled
        )

        task.last_run = last_run
        task.next_run = task._calculate_next_run()

        return task


class TaskScheduler:
    """Task scheduler"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the task scheduler

        Args:
            config_dir: Configuration directory for storing task data
        """
        # Determine configuration directory
        if config_dir is None:
            from pathlib import Path
            self.config_dir = Path.home() / ".encrypted_video_downloader"
        else:
            from pathlib import Path
            self.config_dir = Path(config_dir)

        # Ensure configuration directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Task file path
        self.tasks_file = self.config_dir / "scheduled_tasks.json"

        # Task dictionary
        self.tasks: Dict[str, SchedulerTask] = {}

        # Task handlers
        self.task_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}

        # Control and threads
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()

        # Load tasks
        self._load_tasks()

    def start(self) -> None:
        """Start the scheduler"""
        if self.running:
            return

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

        logger.info("Task scheduler started")

    def stop(self) -> None:
        """Stop the scheduler"""
        if not self.running:
            return

        self.running = False

        # Wait for scheduler thread to end
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)

        # Save tasks
        self._save_tasks()

        logger.info("Task scheduler stopped")

    def register_handler(self, task_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register task handler

        Args:
            task_type: Task type identifier
            handler: Handler function that accepts task data dictionary as parameter
        """
        self.task_handlers[task_type] = handler
        logger.debug(f"Registered task handler for type: {task_type}")

    def add_task(self, task: SchedulerTask) -> str:
        """
        Add scheduled task

        Args:
            task: Task object

        Returns:
            Task ID
        """
        with self.lock:
            self.tasks[task.task_id] = task
            self._save_tasks()
            logger.info(
                f"Added scheduled task: {task.name} (ID: {task.task_id})")

            # Log additional details at debug level
            logger.debug(f"Task details - Type: {task.task_type.value}, "
                         f"Enabled: {task.enabled}, "
                         f"Next run: {task.next_run}")

        return task.task_id

    def remove_task(self, task_id: str) -> bool:
        """
        Remove scheduled task

        Args:
            task_id: Task ID

        Returns:
            Whether successfully removed
        """
        with self.lock:
            if task_id in self.tasks:
                task_name = self.tasks[task_id].name
                del self.tasks[task_id]
                self._save_tasks()
                logger.info(
                    f"Removed scheduled task: {task_name} (ID: {task_id})")
                return True
            else:
                logger.warning(f"Scheduled task does not exist: {task_id}")
                return False

    def enable_task(self, task_id: str) -> bool:
        """
        Enable scheduled task

        Args:
            task_id: Task ID

        Returns:
            Whether successfully enabled
        """
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.enable()
                next_run = task.next_run.strftime(
                    '%Y-%m-%d %H:%M:%S') if task.next_run else "None"
                self._save_tasks()
                logger.info(
                    f"Enabled scheduled task: {task.name} (ID: {task_id}), next run: {next_run}")
                return True
            else:
                logger.warning(f"Scheduled task does not exist: {task_id}")
                return False

    def disable_task(self, task_id: str) -> bool:
        """
        Disable scheduled task

        Args:
            task_id: Task ID

        Returns:
            Whether successfully disabled
        """
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.disable()
                self._save_tasks()
                logger.info(
                    f"Disabled scheduled task: {task.name} (ID: {task_id})")
                return True
            else:
                logger.warning(f"Scheduled task does not exist: {task_id}")
                return False

    def get_task(self, task_id: str) -> Optional[SchedulerTask]:
        """
        Get scheduled task

        Args:
            task_id: Task ID

        Returns:
            Task object, or None if it doesn't exist
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[SchedulerTask]:
        """
        Get all scheduled tasks

        Returns:
            List of task objects
        """
        return list(self.tasks.values())

    def _scheduler_loop(self) -> None:
        """Scheduler main loop"""
        logger.debug("Scheduler loop started")

        while self.running:
            try:
                now = datetime.now()

                # Check and execute due tasks
                with self.lock:
                    for task_id, task in list(self.tasks.items()):
                        if not task.enabled or not task.next_run:
                            continue

                        # Check if task is due
                        if task.next_run <= now:
                            logger.debug(
                                f"Task due for execution: {task.name} (ID: {task_id})")
                            self._execute_task(task)

                # Avoid excessive CPU usage
                time.sleep(1)

            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                time.sleep(5)  # Increase delay on error

    def _execute_task(self, task: SchedulerTask) -> None:
        """Execute task"""
        try:
            # Get task type
            task_type: str = task.data.get("handler_type", "")
            logger.debug(
                f"Executing task: {task.name} (ID: {task.task_id}), handler type: {task_type}")

            if task_type in self.task_handlers:
                # Call handler
                handler = self.task_handlers[task_type]
                handler(task.data)

                logger.success(
                    f"Successfully executed scheduled task: {task.name} (ID: {task.task_id})")
            else:
                logger.warning(f"No task handler found for type: {task_type}")

            # Mark task as executed
            task.mark_executed()

            # Log next execution time
            next_run = task.next_run.strftime(
                '%Y-%m-%d %H:%M:%S') if task.next_run else "None"
            logger.debug(f"Task {task.name} next run: {next_run}")

            # If one-time task and completed, disable task
            if task.task_type == TaskType.ONE_TIME:
                task.disable()
                logger.debug(
                    f"Disabled one-time task after execution: {task.name} (ID: {task.task_id})")

            # Save task status
            self._save_tasks()

        except Exception as e:
            logger.error(
                f"Error executing task: {task.name} (ID: {task.task_id}), error: {e}", exc_info=True)

    def _load_tasks(self) -> None:
        """Load tasks from file"""
        if not os.path.exists(self.tasks_file):
            logger.debug(f"Tasks file not found at: {self.tasks_file}")
            return

        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                tasks_data: List[Dict[str, Any]] = json.load(f)

            # Parse tasks
            for task_data in tasks_data:
                try:
                    task = SchedulerTask.from_dict(task_data)
                    self.tasks[task.task_id] = task
                    next_run = task.next_run.strftime(
                        '%Y-%m-%d %H:%M:%S') if task.next_run else "None"
                    logger.debug(
                        f"Loaded task: {task.name} (ID: {task.task_id}), next run: {next_run}")
                except Exception as e:
                    logger.error(
                        f"Error parsing task data: {e}", exc_info=True)

            logger.info(f"Loaded {len(self.tasks)} scheduled tasks")

        except Exception as e:
            logger.error(f"Error loading tasks: {e}", exc_info=True)

    def _save_tasks(self) -> None:
        """Save tasks to file"""
        try:
            tasks_data: List[Dict[str, Any]] = [task.to_dict()
                                                for task in self.tasks.values()]

            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(self.tasks)} scheduled tasks")

        except Exception as e:
            logger.error(f"Error saving tasks: {e}", exc_info=True)

import requests
import time
import threading
import os
import json
import uuid
from queue import PriorityQueue, Queue, Empty
from enum import Enum
from datetime import datetime
from loguru import logger
from typing import (
    Optional, List, Dict, Tuple, Set, Callable, Any, Union, Literal, Protocol, TypedDict
)


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskPriority(Enum):
    """Task priority enumeration"""
    LOW = 0
    NORMAL = 1
    HIGH = 2


class ProgressDict(TypedDict):
    total: int
    completed: int
    failed: int
    current_file: Optional[str]
    current_file_progress: float
    start_time: Optional[float]
    end_time: Optional[float]
    speed: float
    estimated_time: Optional[float]
    downloaded_bytes: int


class SegmentDetail(TypedDict):
    status: str
    size: int
    timestamp: float


class SettingsProvider(Protocol):
    def get(self, section: str, key: str, default: Any = None) -> Any: ...


class DownloadTask:
    """Download task class"""

    task_id: str
    name: str
    base_url: Optional[str]
    key_url: Optional[str]
    segments: Optional[int]
    output_file: Optional[str]
    # Assuming settings or {} results in a valid SettingsProvider
    settings: SettingsProvider
    priority: TaskPriority
    status: TaskStatus
    progress: ProgressDict
    segments_info: Dict[str, SegmentDetail]
    downloaded_size: int
    key_data: Optional[bytes]
    worker_thread: Optional[threading.Thread]
    paused_event: threading.Event
    canceled_event: threading.Event
    progress_file: Optional[str]
    recent_speeds: List[float]

    def __init__(self,
                 task_id: Optional[str] = None,
                 name: Optional[str] = None,
                 base_url: Optional[str] = None,
                 key_url: Optional[str] = None,
                 segments: Optional[int] = None,
                 output_file: Optional[str] = None,
                 # Actual settings object or dict-like
                 settings: Optional[SettingsProvider] = None,
                 priority: TaskPriority = TaskPriority.NORMAL):
        """Initialize download task"""
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name or f"Task-{self.task_id[:8]}"
        self.base_url = base_url
        self.key_url = key_url
        self.segments = segments
        self.output_file = output_file
        # If settings is None, self.settings becomes an empty dict, which might not satisfy SettingsProvider.
        # This assumes that an empty dict can be cast or used as a SettingsProvider,
        # or that the actual default is a conforming object.
        # For simplicity, we'll assume `settings or {}` is handled appropriately by the caller
        # or that SettingsProvider can accommodate an empty dict-like structure for its `get`.
        # A more robust approach might involve a default SettingsProvider object.
        self.settings = settings or {}  # type: ignore
        self.priority = priority

        # Status information
        self.status = TaskStatus.PENDING
        self.progress = {
            "total": segments or 0,
            "completed": 0,
            "failed": 0,
            "current_file": None,
            "current_file_progress": 0.0,
            "start_time": None,
            "end_time": None,
            "speed": 0.0,
            "estimated_time": None,
            "downloaded_bytes": 0
        }

        # Download details
        self.segments_info = {}
        self.downloaded_size = 0
        self.key_data = None

        # Threads and events
        self.worker_thread = None
        self.paused_event = threading.Event()
        self.canceled_event = threading.Event()
        self.paused_event.set()  # Not paused by default

        # Progress tracking
        self.progress_file = f"{output_file}.progress" if output_file else None
        self.recent_speeds = []

    def get_progress_percentage(self) -> float:
        """Get progress percentage"""
        if self.progress["total"] == 0:
            return 0.0
        return round((self.progress["completed"] / self.progress["total"]) * 100, 2)

    def start(self, worker_func: Callable[[str], None]) -> None:
        """Start task"""
        if self.status == TaskStatus.RUNNING:
            return

        self.status = TaskStatus.RUNNING
        self.progress["start_time"] = self.progress.get(
            "start_time") or time.time()
        self.paused_event.set()  # Cancel pause state
        self.canceled_event.clear()  # Clear cancel flag

        # Create worker thread
        self.worker_thread = threading.Thread(
            target=worker_func,
            args=(self.task_id,)
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def pause(self) -> None:
        """Pause task"""
        if self.status != TaskStatus.RUNNING:
            return

        self.status = TaskStatus.PAUSED
        self.paused_event.clear()  # Set pause event

    def resume(self) -> None:
        """Resume task"""
        if self.status != TaskStatus.PAUSED:
            return

        self.status = TaskStatus.RUNNING
        self.paused_event.set()  # Clear pause event

    def cancel(self) -> None:
        """Cancel task"""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]:
            return

        self.status = TaskStatus.CANCELED
        self.canceled_event.set()  # Set cancel event
        self.paused_event.set()  # Release pause to allow task to detect cancellation

    def save_progress(self) -> None:
        """Save progress to file"""
        if not self.progress_file:
            return

        try:
            progress_data: Dict[str, Any] = {
                "task_id": self.task_id,
                "name": self.name,
                "status": self.status.value,
                "progress": self.progress,
                "segments_info": self.segments_info,
                "last_updated": datetime.now().isoformat()
            }

            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Progress saved for task {self.name}")
        except Exception as e:
            logger.error(f"Failed to save task progress: {e}", exc_info=True)

    def load_progress(self) -> bool:
        """Load progress from file"""
        if not self.progress_file or not os.path.exists(self.progress_file):
            return False

        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data: Dict[str, Any] = json.load(f)

            # Restore progress information
            if data.get("task_id") == self.task_id:
                self.name = data.get("name", self.name)
                self.status = TaskStatus(data.get("status", self.status.value))
                self.progress = data.get("progress", self.progress)
                self.segments_info = data.get(
                    "segments_info", self.segments_info)
                logger.info(
                    f"Progress loaded for task {self.name}: {self.progress['completed']}/{self.progress['total']} segments completed")
                return True
        except Exception as e:
            logger.error(f"Failed to load task progress: {e}", exc_info=True)

        return False

    def update_speed(self, bytes_downloaded: int, elapsed_time: float) -> None:
        """Update download speed statistics with accurate calculation"""
        if elapsed_time > 0:
            current_speed: float = bytes_downloaded / elapsed_time
            current_time = time.time()
            
            # Track speed samples with timestamps for better accuracy
            if not hasattr(self, 'speed_samples'):
                self.speed_samples = []
            
            self.speed_samples.append((current_time, current_speed))
            
            # Keep only speed samples from the last 30 seconds for better accuracy
            cutoff_time = current_time - 30.0
            self.speed_samples = [(t, s) for t, s in self.speed_samples if t >= cutoff_time]
            
            # Calculate weighted average speed (more recent samples have higher weight)
            if self.speed_samples:
                total_weight = 0
                weighted_speed = 0
                for sample_time, speed in self.speed_samples:
                    # Weight decreases exponentially with age
                    age = current_time - sample_time
                    weight = max(0.1, 1.0 - (age / 30.0))  # Minimum weight of 0.1
                    weighted_speed += speed * weight
                    total_weight += weight
                
                if total_weight > 0:
                    self.progress["speed"] = weighted_speed / total_weight
                else:
                    self.progress["speed"] = current_speed
            else:
                self.progress["speed"] = current_speed

            # Also keep the simple recent speeds for backup calculation
            self.recent_speeds.append(current_speed)
            if len(self.recent_speeds) > 20:
                self.recent_speeds.pop(0)

            # Estimate remaining time based on actual progress and current speed
            if self.progress["speed"] > 0 and self.progress["total"] > 0:
                completed_ratio = self.progress["completed"] / self.progress["total"]
                if completed_ratio > 0 and self.progress["downloaded_bytes"] > 0:
                    # Estimate total download size based on current progress
                    estimated_total_bytes = self.progress["downloaded_bytes"] / completed_ratio
                    remaining_bytes = estimated_total_bytes - self.progress["downloaded_bytes"]
                    if remaining_bytes > 0:
                        self.progress["estimated_time"] = remaining_bytes / self.progress["speed"]
                    else:
                        self.progress["estimated_time"] = 0
                else:
                    self.progress["estimated_time"] = None
            else:
                self.progress["estimated_time"] = None


# Define EventTuple for DownloadManager.event_queue
EventTuple = Union[
    Tuple[Literal["status_changed"], str, Optional[TaskStatus], TaskStatus],
    Tuple[Literal["progress"], str, ProgressDict],
    Tuple[Literal["completed"], str, str],
    Tuple[Literal["failed"], str, str]
]


class DownloadManager:
    """Download manager"""

    settings: Optional[SettingsProvider]
    tasks: Dict[str, DownloadTask]
    # Task priority queue (neg_priority, time, task_id)
    tasks_queue: "PriorityQueue[Tuple[int, float, str]]"
    active_tasks: Set[str]
    running: bool
    scheduler_thread: Optional[threading.Thread]
    lock: threading.RLock
    bandwidth_limiter: Any  # Placeholder for actual type
    bandwidth_limit: int
    on_task_progress: Optional[Callable[[str, ProgressDict], None]]
    on_task_status_changed: Optional[Callable[[
        str, Optional[TaskStatus], TaskStatus], None]]
    on_task_completed: Optional[Callable[[str, str], None]]
    on_task_failed: Optional[Callable[[str, str], None]]
    event_queue: "Queue[EventTuple]"
    event_thread: Optional[threading.Thread]

    def __init__(self, settings: Optional[SettingsProvider] = None):
        """Initialize download manager"""
        self.settings = settings
        self.tasks = {}
        self.tasks_queue = PriorityQueue()
        self.active_tasks = set()

        # Controls and events
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.RLock()

        # Bandwidth control
        self.bandwidth_limiter = None
        self.bandwidth_limit = 0

        # Signal handling and callbacks
        self.on_task_progress = None
        self.on_task_status_changed = None
        self.on_task_completed = None
        self.on_task_failed = None

        # Event queue
        self.event_queue = Queue()
        self.event_thread = None

    def start(self) -> None:
        """Start download manager"""
        if self.running:
            return

        self.running = True

        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

        # Start event handling thread
        self.event_thread = threading.Thread(target=self._event_loop)
        self.event_thread.daemon = True
        self.event_thread.start()

        logger.info("Download manager started")

    def stop(self) -> None:
        """Stop download manager"""
        if not self.running:
            return

        self.running = False

        # Pause all tasks
        with self.lock:
            active_task_ids = list(self.active_tasks)  # Iterate over a copy
            for task_id in active_task_ids:
                task = self.tasks.get(task_id)
                if task:
                    task.pause()

        # Wait for scheduler thread to end
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2)

        # Wait for event handling thread to end
        if self.event_thread and self.event_thread.is_alive():
            self.event_thread.join(timeout=2)

        # Save progress for all tasks
        for task in self.tasks.values():
            task.save_progress()

        logger.info("Download manager stopped")

    def add_task(self, task: DownloadTask) -> str:
        """Add download task"""
        with self.lock:
            self.tasks[task.task_id] = task
            # Add task to priority queue
            self.tasks_queue.put(
                (-task.priority.value, time.time(), task.task_id))
            logger.info(f"Task added: {task.name} (ID: {task.task_id})")

        # Notify status change
        self._emit_status_changed(task.task_id, None, task.status)

        return task.task_id

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Get specified task"""
        return self.tasks.get(task_id)

    def start_task(self, task_id: str) -> bool:
        """Start specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            # Don't start if task is already completed or canceled
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]:
                logger.info(f"Task already ended, cannot restart: {task_id}")
                return False

            # If task is already running, return immediately
            if task.status == TaskStatus.RUNNING:
                return True

            # Try to load progress
            task.load_progress()

            # Start task
            old_status: Optional[TaskStatus] = task.status
            task.start(self._task_worker)

            # Add to active tasks
            self.active_tasks.add(task_id)

            # Notify status change
            self._emit_status_changed(task_id, old_status, task.status)

            return True

    def pause_task(self, task_id: str) -> bool:
        """Pause specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            if task.status != TaskStatus.RUNNING:
                return False

            old_status: TaskStatus = task.status
            task.pause()
            self._emit_status_changed(task_id, old_status, task.status)
            return True

    def resume_task(self, task_id: str) -> bool:
        """Resume specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            if task.status != TaskStatus.PAUSED:
                return False

            old_status: TaskStatus = task.status
            task.resume()
            self._emit_status_changed(task_id, old_status, task.status)
            return True

    def cancel_task(self, task_id: str) -> bool:
        """Cancel specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            old_status: TaskStatus = task.status
            task.cancel()

            # Remove from active tasks if present
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)

            self._emit_status_changed(task_id, old_status, task.status)
            return True

    def remove_task(self, task_id: str, delete_files: bool = False) -> bool:
        """Remove specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            # Cancel if task is running or paused
            if task.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
                task.cancel()  # This will also set its status to CANCELED

            # Remove from active tasks if present
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)

            # Delete progress file
            if task.progress_file and os.path.exists(task.progress_file):
                try:
                    os.remove(task.progress_file)
                except Exception as e:
                    logger.error(
                        f"Failed to delete progress file: {task.progress_file}, {e}", exc_info=True)

            # Delete output file
            if delete_files and task.output_file and os.path.exists(task.output_file):
                try:
                    os.remove(task.output_file)
                    logger.info(f"Deleted output file: {task.output_file}")
                except Exception as e:
                    logger.error(
                        f"Failed to delete output file: {task.output_file}, {e}", exc_info=True)

            # Remove from task dictionary
            if task_id in self.tasks:
                del self.tasks[task_id]
            logger.info(f"Task removed: {task.name} (ID: {task_id})")
            # Optionally emit a final status change or a specific "removed" event
            # self._emit_status_changed(task_id, task.status, TaskStatus.CANCELED) # Or a new "REMOVED" status
            return True
        return False

    def _emit_status_changed(self, task_id: str, old_status: Optional[TaskStatus], new_status: TaskStatus) -> None:
        """Emit task status change event"""
        if self.on_task_status_changed:
            event: EventTuple = ("status_changed", task_id,
                                 old_status, new_status)
            self.event_queue.put(event)

    def _emit_progress(self, task_id: str, progress: ProgressDict) -> None:
        """Emit task progress event"""
        if self.on_task_progress:
            event: EventTuple = ("progress", task_id, progress)
            self.event_queue.put(event)

    def _emit_completed(self, task_id: str, success: bool, message: str) -> None:
        """Emit task completion event"""
        if success and self.on_task_completed:
            event: EventTuple = ("completed", task_id, message)
            self.event_queue.put(event)
        elif not success and self.on_task_failed:
            event: EventTuple = ("failed", task_id, message)
            self.event_queue.put(event)

    def _event_loop(self) -> None:
        """Event handling loop"""
        
        while self.running:
            try:
                # Get event from queue
                event: EventTuple = self.event_queue.get(timeout=0.5)
                
                if not event:  # Should not happen with Queue.get unless None is put
                    continue

                event_type = event[0]

                if event_type == "status_changed" and self.on_task_status_changed:
                    if len(event) >= 4:
                        _, task_id_ev, old_status_ev, new_status_ev = event
                        if isinstance(task_id_ev, str):
                            self.on_task_status_changed(task_id_ev, old_status_ev, new_status_ev)

                elif event_type == "progress" and self.on_task_progress:
                    if len(event) >= 3 and event[0] == "progress":
                        progress_event = event  # Type should be Tuple[Literal["progress"], str, ProgressDict]
                        task_id_ev = progress_event[1]
                        progress_ev = progress_event[2]
                        if isinstance(task_id_ev, str) and isinstance(progress_ev, dict):
                            self.on_task_progress(task_id_ev, progress_ev)

                elif event_type == "completed" and self.on_task_completed:
                    if len(event) >= 3 and event[0] == "completed":
                        completed_event = event  # Type should be Tuple[Literal["completed"], str, str]
                        task_id_ev = completed_event[1]
                        message_ev = completed_event[2]
                        if isinstance(task_id_ev, str) and isinstance(message_ev, str):
                            self.on_task_completed(task_id_ev, message_ev)

                elif event_type == "failed" and self.on_task_failed:
                    if len(event) >= 3 and event[0] == "failed":
                        failed_event = event  # Type should be Tuple[Literal["failed"], str, str]
                        task_id_ev = failed_event[1]
                        message_ev = failed_event[2]
                        if isinstance(task_id_ev, str) and isinstance(message_ev, str):
                            self.on_task_failed(task_id_ev, message_ev)

                # Mark event as processed
                self.event_queue.task_done()

            except Empty:  # Changed from generic Exception for Empty
                continue
            except Exception as e:
                # if isinstance(e, (Empty, TimeoutError)): # TimeoutError not applicable for Queue.get
                #     continue
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Error processing event: {e}\n{error_details}")

    def _scheduler_loop(self) -> None:
        """Scheduler main loop"""
        while self.running:
            try:
                max_concurrent: int = 3
                if self.settings:
                    max_concurrent = int(self.settings.get(
                        "download", "max_concurrent_tasks", 3))

                with self.lock:
                    active_count: int = len(self.active_tasks)
                    if active_count < max_concurrent and not self.tasks_queue.empty():
                        try:
                            # Type assertion for item from PriorityQueue
                            # type: Tuple[int, float, str]
                            _prio, _time, task_id_sched = self.tasks_queue.get_nowait()

                            if task_id_sched not in self.tasks:
                                continue

                            task_to_start = self.tasks[task_id_sched]

                            if task_to_start.status in [TaskStatus.PENDING, TaskStatus.PAUSED]:
                                old_status_sched: Optional[TaskStatus] = task_to_start.status
                                task_to_start.start(self._task_worker)
                                self.active_tasks.add(task_id_sched)
                                self._emit_status_changed(
                                    task_id_sched, old_status_sched, task_to_start.status)
                        except Empty:  # If queue becomes empty between check and get
                            pass
                        except Exception as e:
                            logger.error(
                                f"Error starting task from scheduler: {e}", exc_info=True)
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                time.sleep(1)

    def _task_worker(self, task_id: str) -> None:
        """Task worker thread function"""
        from .decryptor import decrypt_data  # Assuming decrypt_data(bytes, bytes, bytes, bool) -> bytes
        # Assuming merge_files(List[str], str, Optional[SettingsProvider]) -> Dict[str, Any]
        from .merger import merge_files

        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task not found in worker: {task_id}")
            return

        try:
            logger.info(
                f"Starting task execution: {task.name} (ID: {task_id})")
            session = requests.Session()

            user_agent: str = "Mozilla/5.0"
            if self.settings:
                user_agent = str(self.settings.get(
                    "advanced", "user_agent", "Mozilla/5.0"))
            session.headers.update({"User-Agent": user_agent})

            proxy_str: str = ""
            if self.settings:
                proxy_str = str(self.settings.get("advanced", "proxy", ""))
            if proxy_str:
                session.proxies = {"http": proxy_str, "https": proxy_str}

            verify_ssl_val: bool = True
            if self.settings:
                verify_ssl_val = bool(self.settings.get(
                    "advanced", "verify_ssl", True))
            session.verify = verify_ssl_val

            max_retries_val: int = 5
            retry_delay_val: float = 2.0
            timeout_val: int = 60
            chunk_size_val: int = 8192

            if self.settings:
                max_retries_val = int(self.settings.get(
                    "download", "max_retries", 5))
                retry_delay_val = float(self.settings.get(
                    "download", "retry_delay", 2.0))
                timeout_val = int(self.settings.get(
                    "download", "request_timeout", 60))
                chunk_size_val = int(self.settings.get(
                    "download", "chunk_size", 8192))

            if not task.key_data and task.key_url:
                logger.info(f"Downloading encryption key: {task.key_url}")
                task.progress["current_file"] = "Encryption Key"
                for attempt in range(max_retries_val):
                    if task.canceled_event.is_set():
                        break
                    try:
                        response = session.get(
                            task.key_url, timeout=timeout_val)
                        if response.status_code == 200:
                            task.key_data = response.content
                            key_size = len(task.key_data) if task.key_data else 0
                            logger.debug(
                                f"Successfully downloaded encryption key ({key_size} bytes)")
                            break
                        else:
                            logger.warning(
                                f"Key download failed, HTTP status: {response.status_code}, retry ({attempt+1}/{max_retries_val})")
                    except Exception as e:
                        logger.warning(
                            f"Key download error: {e}, retry ({attempt+1}/{max_retries_val})")
                    time.sleep(retry_delay_val * (attempt + 1))
                if not task.key_data:
                    raise Exception("Failed to download encryption key")

            if not task.output_file:
                raise Exception("Output file not specified for task.")

            output_dir: str = os.path.dirname(task.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            temp_dir: str = f"{task.output_file}_temp"
            os.makedirs(temp_dir, exist_ok=True)

            iv = bytes.fromhex('00000000000000000000000000000000')
            successful_files: List[str] = []

            if task.segments is None:  # Should not happen if initialized correctly
                task.segments = 0
                task.progress["total"] = 0

            logger.info(
                f"Downloading {task.segments} segments for task: {task.name}")

            for i in range(task.segments):
                if task.canceled_event.is_set():
                    break
                while task.status == TaskStatus.PAUSED:
                    if task.canceled_event.is_set():
                        break
                    time.sleep(0.5)
                if task.canceled_event.is_set():
                    break  # Check again after pause

                segment_key = str(i)
                ts_filename = os.path.join(temp_dir, f"segment_{i}.ts")
                if segment_key in task.segments_info and task.segments_info[segment_key].get("status") == "completed" and os.path.exists(ts_filename):
                    logger.debug(f"Skipping already downloaded segment {i}")
                    successful_files.append(ts_filename)
                    continue

                if not task.base_url:
                    raise Exception(
                        "Base URL not specified for task segments.")
                segment_url = f"{task.base_url}/index{i}.ts"
                temp_filename = f"{ts_filename}.temp"
                task.progress["current_file"] = f"Segment {i+1}/{task.segments}"
                segment_success = False
                segment_start_time = time.time()

                for attempt in range(max_retries_val):
                    if task.canceled_event.is_set():
                        break
                    try:
                        logger.debug(
                            f"Downloading segment {i+1}/{task.segments} from {segment_url}")
                        response = session.get(
                            segment_url, stream=True, timeout=timeout_val)
                        if response.status_code != 200:
                            logger.warning(
                                f"Segment download failed (HTTP {response.status_code}), retry ({attempt+1}/{max_retries_val})")
                            time.sleep(retry_delay_val * (attempt + 1))
                            continue

                        total_size = int(
                            response.headers.get('content-length', 0))
                        downloaded_this_segment = 0
                        chunk_start_time = time.time()
                        last_speed_update = chunk_start_time
                        
                        with open(temp_filename, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=chunk_size_val):
                                if task.canceled_event.is_set():
                                    break
                                while not task.paused_event.is_set():  # Corrected: check if PAUSED
                                    if task.canceled_event.is_set():
                                        break
                                    time.sleep(0.1)
                                if task.canceled_event.is_set():
                                    break  # Check again
                                if not chunk:
                                    continue

                                chunk_process_start = time.time()
                                if task.key_data:  # Ensure key_data is present
                                    decrypted_chunk = decrypt_data(chunk, task.key_data, iv, last_block=(
                                        downloaded_this_segment + len(chunk) >= total_size and total_size > 0))
                                    f.write(decrypted_chunk)
                                else:  # Should not happen if key download is successful
                                    # Write raw if no key (fallback, might be wrong for encrypted content)
                                    f.write(chunk)

                                downloaded_this_segment += len(chunk)
                                task.progress["current_file_progress"] = downloaded_this_segment / \
                                    total_size if total_size > 0 else 0
                                task.progress["downloaded_bytes"] += len(chunk)
                                
                                # Update speed calculation more accurately
                                current_time = time.time()
                                chunk_elapsed = current_time - chunk_process_start
                                if current_time - last_speed_update >= 0.5:  # Update speed every 0.5 seconds
                                    task.update_speed(len(chunk), chunk_elapsed)
                                    last_speed_update = current_time
                                    self._emit_progress(task_id, task.progress)

                        if task.canceled_event.is_set():
                            break  # Check after writing loop

                        os.rename(temp_filename, ts_filename)
                        successful_files.append(ts_filename)
                        task.segments_info[segment_key] = {"status": "completed", "size": os.path.getsize(
                            ts_filename), "timestamp": time.time()}
                        segment_success = True
                        logger.debug(
                            f"Successfully downloaded segment {i+1}/{task.segments}")
                        break
                    except Exception as e:
                        logger.error(
                            f"Failed to download segment {i}: {e}", exc_info=True)
                        if os.path.exists(temp_filename):
                            try:
                                os.remove(temp_filename)
                            except OSError:
                                pass
                        time.sleep(retry_delay_val * (attempt + 1))

                if task.canceled_event.is_set():
                    break
                if segment_success:
                    task.progress["completed"] += 1
                else:
                    task.progress["failed"] += 1
                if i % 10 == 0 or not segment_success:
                    task.save_progress()
                self._emit_progress(task_id, task.progress)

            if task.canceled_event.is_set():
                logger.info(
                    f"Task canceled during segments download: {task.name}")
                task.status = TaskStatus.CANCELED
            elif task.progress["failed"] > 0 and task.progress["completed"] == 0:
                logger.error(
                    f"All segments failed to download for task: {task.name}")
                task.status = TaskStatus.FAILED
            elif successful_files:
                logger.info(
                    f"Starting to merge {len(successful_files)} video segments for {task.name}")
                task.progress["current_file"] = "Merging video"
                # Update UI before merge
                self._emit_progress(task_id, task.progress)

                merge_result: Dict[str, Any] = merge_files(
                    successful_files, task.output_file, None)
                if merge_result.get("success"):
                    logger.success(
                        f"Video merge successful: {task.output_file}")
                    task.status = TaskStatus.COMPLETED
                else:
                    logger.error(
                        f"Video merge failed: {merge_result.get('error', 'Unknown error')}")
                    task.status = TaskStatus.FAILED
            # No successful files and not canceled (e.g. all segments failed)
            else:
                logger.error(
                    f"No successfully downloaded video segments to merge for task: {task.name}")
                task.status = TaskStatus.FAILED

            task.progress["end_time"] = time.time()
            # Assuming it was RUNNING
            self._emit_status_changed(task_id, TaskStatus.RUNNING, task.status)
            if task.status == TaskStatus.COMPLETED:
                self._emit_completed(
                    task_id, True, f"Video download and merge successful: {task.output_file}")
            elif task.status != TaskStatus.CANCELED:  # FAILED or other non-canceled states
                error_message = "Task failed."
                if task.progress["failed"] > 0 and task.progress["completed"] == 0:
                    error_message = "All segments failed to download."
                elif not successful_files and task.segments > 0:  # task.segments should be > 0
                    error_message = "No segments were successfully downloaded to merge."
                elif 'error' in locals().get('merge_result', {}):  # Check if merge_result exists and has error
                    error_message = f"Video merge failed: {locals()['merge_result']['error']}"

                self._emit_completed(task_id, False, error_message)

            auto_cleanup_val: bool = True
            keep_temp_val: bool = False
            if self.settings:
                auto_cleanup_val = bool(self.settings.get(
                    "general", "auto_cleanup", True))
                keep_temp_val = bool(self.settings.get(
                    "advanced", "keep_temp_files", False))

            if auto_cleanup_val and not keep_temp_val and os.path.exists(temp_dir):
                logger.info(f"Cleaning up temporary files in: {temp_dir}")
                # successful_files list contains paths within temp_dir
                for file_path in successful_files:  # These should have been merged
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except OSError as e:
                            logger.warning(
                                f"Failed to clean up file: {file_path}, error: {e}")
                # Attempt to remove other temp files if any (e.g. .temp parts)
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                    except OSError as e:
                        logger.warning(
                            f"Failed to clean up temp item: {item_path}, error: {e}")
                try:
                    os.rmdir(temp_dir)
                except OSError as e:
                    logger.warning(
                        f"Failed to delete temporary directory: {temp_dir}, error: {e} (may not be empty)")
            task.save_progress()

        except Exception as e:
            logger.error(
                f"Task execution error for {task.name} (ID: {task_id}): {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            # Assuming it was RUNNING
            self._emit_status_changed(task_id, TaskStatus.RUNNING, task.status)
            self._emit_completed(
                task_id, False, f"Task execution error: {str(e)}")
        finally:
            with self.lock:
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)

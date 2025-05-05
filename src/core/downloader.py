import requests
import time
import threading
import os
import json
import uuid
from queue import PriorityQueue, Queue
from enum import Enum
from datetime import datetime
from loguru import logger


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


class DownloadTask:
    """Download task class"""

    def __init__(self,
                 task_id=None,
                 name=None,
                 base_url=None,
                 key_url=None,
                 segments=None,
                 output_file=None,
                 settings=None,
                 priority=TaskPriority.NORMAL):
        """Initialize download task"""
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name or f"Task-{self.task_id[:8]}"
        self.base_url = base_url
        self.key_url = key_url
        self.segments = segments
        self.output_file = output_file
        self.settings = settings or {}
        self.priority = priority

        # Status information
        self.status = TaskStatus.PENDING
        self.progress = {
            "total": segments or 0,
            "completed": 0,
            "failed": 0,
            "current_file": None,
            "current_file_progress": 0,
            "start_time": None,
            "end_time": None,
            "speed": 0,
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
        self.recent_speeds = []  # Stores recent download speeds for average calculation

    def get_progress_percentage(self):
        """Get progress percentage"""
        if self.progress["total"] == 0:
            return 0
        return round((self.progress["completed"] / self.progress["total"]) * 100, 2)

    def start(self, worker_func):
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

    def pause(self):
        """Pause task"""
        if self.status != TaskStatus.RUNNING:
            return

        self.status = TaskStatus.PAUSED
        self.paused_event.clear()  # Set pause event

    def resume(self):
        """Resume task"""
        if self.status != TaskStatus.PAUSED:
            return

        self.status = TaskStatus.RUNNING
        self.paused_event.set()  # Clear pause event

    def cancel(self):
        """Cancel task"""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]:
            return

        self.status = TaskStatus.CANCELED
        self.canceled_event.set()  # Set cancel event
        self.paused_event.set()  # Release pause to allow task to detect cancellation

    def save_progress(self):
        """Save progress to file"""
        if not self.progress_file:
            return

        try:
            progress_data = {
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

    def load_progress(self):
        """Load progress from file"""
        if not self.progress_file or not os.path.exists(self.progress_file):
            return False

        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Restore progress information
            if data["task_id"] == self.task_id:
                self.name = data["name"]
                self.status = TaskStatus(data["status"])
                self.progress = data["progress"]
                self.segments_info = data["segments_info"]
                logger.info(
                    f"Progress loaded for task {self.name}: {self.progress['completed']}/{self.progress['total']} segments completed")
                return True
        except Exception as e:
            logger.error(f"Failed to load task progress: {e}", exc_info=True)

        return False

    def update_speed(self, bytes_downloaded, elapsed_time):
        """Update download speed statistics"""
        if elapsed_time > 0:
            current_speed = bytes_downloaded / elapsed_time
            self.recent_speeds.append(current_speed)

            # Keep only the 10 most recent speed samples
            if len(self.recent_speeds) > 10:
                self.recent_speeds.pop(0)

            # Calculate average speed
            if self.recent_speeds:
                self.progress["speed"] = sum(
                    self.recent_speeds) / len(self.recent_speeds)

            # Estimate remaining time
            if self.progress["speed"] > 0 and self.progress["total"] > 0:
                remaining = self.progress["total"] - self.progress["completed"]
                # Assuming average segment size
                self.progress["estimated_time"] = remaining / \
                    (self.progress["speed"] / 8192)
            else:
                self.progress["estimated_time"] = None


class DownloadManager:
    """Download manager"""

    def __init__(self, settings=None):
        """Initialize download manager"""
        self.settings = settings
        self.tasks = {}  # Task dictionary, key is task ID
        self.tasks_queue = PriorityQueue()  # Task priority queue
        self.active_tasks = set()  # Set of active task IDs

        # Controls and events
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.RLock()

        # Bandwidth control
        self.bandwidth_limiter = None
        self.bandwidth_limit = 0  # 0 means unlimited

        # Signal handling and callbacks
        self.on_task_progress = None
        self.on_task_status_changed = None
        self.on_task_completed = None
        self.on_task_failed = None

        # Event queue
        self.event_queue = Queue()
        self.event_thread = None

    def start(self):
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

    def stop(self):
        """Stop download manager"""
        if not self.running:
            return

        self.running = False

        # Pause all tasks
        with self.lock:
            for task_id in self.active_tasks:
                task = self.tasks.get(task_id)
                if task:
                    task.pause()

        # Wait for scheduler thread to end
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)

        # Wait for event handling thread to end
        if self.event_thread:
            self.event_thread.join(timeout=2)

        # Save progress for all tasks
        for task in self.tasks.values():
            task.save_progress()

        logger.info("Download manager stopped")

    def add_task(self, task):
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

    def get_task(self, task_id):
        """Get specified task"""
        return self.tasks.get(task_id)

    def start_task(self, task_id):
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
            old_status = task.status
            task.start(self._task_worker)

            # Add to active tasks
            self.active_tasks.add(task_id)

            # Notify status change
            self._emit_status_changed(task_id, old_status, task.status)

            return True

    def pause_task(self, task_id):
        """Pause specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            if task.status != TaskStatus.RUNNING:
                return False

            old_status = task.status
            task.pause()

            # Notify status change
            self._emit_status_changed(task_id, old_status, task.status)

            return True

    def resume_task(self, task_id):
        """Resume specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            if task.status != TaskStatus.PAUSED:
                return False

            old_status = task.status
            task.resume()

            # Notify status change
            self._emit_status_changed(task_id, old_status, task.status)

            return True

    def cancel_task(self, task_id):
        """Cancel specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            old_status = task.status
            task.cancel()

            # Remove from active tasks if present
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)

            # Notify status change
            self._emit_status_changed(task_id, old_status, task.status)

            return True

    def remove_task(self, task_id, delete_files=False):
        """Remove specified task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            # Cancel if task is running or paused
            if task.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
                task.cancel()

            # Remove from active tasks if present
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)

            # Delete progress file
            if task.progress_file and os.path.exists(task.progress_file):
                try:
                    os.remove(task.progress_file)
                except Exception as e:
                    logger.error(
                        f"Failed to delete progress file: {e}", exc_info=True)

            # Delete output file
            if delete_files and task.output_file and os.path.exists(task.output_file):
                try:
                    os.remove(task.output_file)
                    logger.info(f"Deleted output file: {task.output_file}")
                except Exception as e:
                    logger.error(
                        f"Failed to delete output file: {e}", exc_info=True)

            # Remove from task dictionary
            del self.tasks[task_id]
            logger.info(f"Task removed: {task.name} (ID: {task_id})")

            return True

    def _emit_status_changed(self, task_id, old_status, new_status):
        """Emit task status change event"""
        if self.on_task_status_changed:
            self.event_queue.put(
                ("status_changed", task_id, old_status, new_status))

    def _emit_progress(self, task_id, progress):
        """Emit task progress event"""
        if self.on_task_progress:
            self.event_queue.put(("progress", task_id, progress))

    def _emit_completed(self, task_id, success, message):
        """Emit task completion event"""
        if success and self.on_task_completed:
            self.event_queue.put(("completed", task_id, message))
        elif not success and self.on_task_failed:
            self.event_queue.put(("failed", task_id, message))

    def _event_loop(self):
        """Event handling loop"""
        while self.running:
            try:
                # Get event from queue
                event = self.event_queue.get(timeout=0.5)
                if not event:
                    continue

                event_type = event[0]

                if event_type == "status_changed" and self.on_task_status_changed:
                    _, task_id, old_status, new_status = event
                    self.on_task_status_changed(
                        task_id, old_status, new_status)

                elif event_type == "progress" and self.on_task_progress:
                    _, task_id, progress = event
                    self.on_task_progress(task_id, progress)

                elif event_type == "completed" and self.on_task_completed:
                    _, task_id, message = event
                    self.on_task_completed(task_id, message)

                elif event_type == "failed" and self.on_task_failed:
                    _, task_id, message = event
                    self.on_task_failed(task_id, message)

                # Mark event as processed
                self.event_queue.task_done()

            except Exception as e:
                if isinstance(e, TimeoutError):
                    continue
                logger.error(f"Error processing event: {e}", exc_info=True)

    def _scheduler_loop(self):
        """Scheduler main loop"""
        while self.running:
            try:
                # Check if there are available task slots
                max_concurrent = int(self.settings.get(
                    "download", "max_concurrent_tasks", 3)) if self.settings else 3

                with self.lock:
                    # Current number of active tasks
                    active_count = len(self.active_tasks)

                    # Start new tasks if slots available and queue not empty
                    if active_count < max_concurrent and not self.tasks_queue.empty():
                        try:
                            _, _, task_id = self.tasks_queue.get_nowait()

                            # Check if task still exists
                            if task_id not in self.tasks:
                                continue

                            task = self.tasks[task_id]

                            if task.status in [TaskStatus.PENDING, TaskStatus.PAUSED]:
                                # Start task
                                old_status = task.status
                                task.start(self._task_worker)
                                self.active_tasks.add(task_id)

                                # Notify status change
                                self._emit_status_changed(
                                    task_id, old_status, task.status)
                        except Exception as e:
                            logger.error(
                                f"Error starting task: {e}", exc_info=True)

                # Avoid excessive CPU usage
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                time.sleep(1)  # Increase delay on error

    def _task_worker(self, task_id):
        """Task worker thread function"""
        from .decryptor import decrypt_data
        from .merger import merge_files

        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return

        try:
            logger.info(
                f"Starting task execution: {task.name} (ID: {task_id})")

            # Initialize HTTP session
            session = requests.Session()

            # Set request headers
            user_agent = self.settings.get(
                "advanced", "user_agent", "Mozilla/5.0") if self.settings else "Mozilla/5.0"
            session.headers.update({"User-Agent": user_agent})

            # Set proxy
            proxy = self.settings.get(
                "advanced", "proxy", "") if self.settings else ""
            if proxy:
                session.proxies = {
                    "http": proxy,
                    "https": proxy
                }

            # Set SSL verification
            verify_ssl = self.settings.get(
                "advanced", "verify_ssl", True) if self.settings else True
            session.verify = verify_ssl

            # Get download parameters
            max_retries = int(self.settings.get(
                "download", "max_retries", 5)) if self.settings else 5
            retry_delay = float(self.settings.get(
                "download", "retry_delay", 2)) if self.settings else 2
            timeout = int(self.settings.get(
                "download", "request_timeout", 60)) if self.settings else 60
            chunk_size = int(self.settings.get(
                "download", "chunk_size", 8192)) if self.settings else 8192

            # Download encryption key
            if not task.key_data:
                logger.info(f"Downloading encryption key: {task.key_url}")
                task.progress["current_file"] = "Encryption Key"

                for attempt in range(max_retries):
                    try:
                        response = session.get(task.key_url, timeout=timeout)
                        if response.status_code == 200:
                            task.key_data = response.content
                            logger.debug(
                                f"Successfully downloaded encryption key ({len(task.key_data)} bytes)")
                            break
                        else:
                            logger.warning(
                                f"Key download failed, HTTP status: {response.status_code}, retry ({attempt+1}/{max_retries})")
                    except Exception as e:
                        logger.warning(
                            f"Key download error: {e}, retry ({attempt+1}/{max_retries})")

                    # Check if task was canceled
                    if task.canceled_event.is_set():
                        logger.info(f"Task canceled: {task.name}")
                        return

                    # Wait before retry
                    time.sleep(retry_delay * (attempt + 1))

                if not task.key_data:
                    error_msg = "Failed to download encryption key"
                    logger.error(error_msg)
                    raise Exception(error_msg)

            # Create output directory
            output_dir = os.path.dirname(task.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.debug(f"Created output directory: {output_dir}")

            # Create temporary directory
            temp_dir = f"{task.output_file}_temp"
            os.makedirs(temp_dir, exist_ok=True)
            logger.debug(f"Created temporary directory: {temp_dir}")

            # Initialize IV (Initialization Vector)
            iv = bytes.fromhex('00000000000000000000000000000000')

            # Download and decrypt all segments
            successful_files = []
            start_time = time.time()

            logger.info(
                f"Downloading {task.segments} segments for task: {task.name}")

            for i in range(task.segments):
                # Check if task was canceled
                if task.canceled_event.is_set():
                    logger.info(f"Task canceled: {task.name}")
                    break

                # Check if task is paused
                while task.status == TaskStatus.PAUSED:
                    time.sleep(0.5)
                    if task.canceled_event.is_set():
                        break

                # Skip if segment already downloaded
                segment_key = str(i)
                if segment_key in task.segments_info and task.segments_info[segment_key].get("status") == "completed":
                    ts_filename = os.path.join(temp_dir, f"segment_{i}.ts")
                    if os.path.exists(ts_filename):
                        logger.debug(
                            f"Skipping already downloaded segment {i}")
                        successful_files.append(ts_filename)
                        continue

                # Generate segment URL
                segment_url = f"{task.base_url}/index{i}.ts"
                ts_filename = os.path.join(temp_dir, f"segment_{i}.ts")
                temp_filename = f"{ts_filename}.temp"

                # Update progress info
                task.progress["current_file"] = f"Segment {i+1}/{task.segments}"

                # Download and decrypt segment
                success = False

                for attempt in range(max_retries):
                    if task.canceled_event.is_set():
                        break

                    try:
                        # Stream download
                        logger.debug(
                            f"Downloading segment {i+1}/{task.segments}")
                        response = session.get(
                            segment_url, stream=True, timeout=timeout)

                        if response.status_code != 200:
                            logger.warning(
                                f"Segment download failed, HTTP status: {response.status_code}, retry ({attempt+1}/{max_retries})")
                            time.sleep(retry_delay * (attempt + 1))
                            continue

                        # Get file size
                        total_size = int(
                            response.headers.get('content-length', 0))

                        # Decrypt and save segment
                        with open(temp_filename, 'wb') as f:
                            downloaded = 0

                            for chunk in response.iter_content(chunk_size=chunk_size):
                                # Check task status
                                if task.canceled_event.is_set():
                                    break

                                # Wait if task is paused
                                while not task.paused_event.is_set():
                                    time.sleep(0.5)
                                    if task.canceled_event.is_set():
                                        break

                                if not chunk:
                                    continue

                                # Decrypt data block
                                decrypted_chunk = decrypt_data(
                                    chunk,
                                    task.key_data,
                                    iv,
                                    last_block=(
                                        downloaded + len(chunk) >= total_size)
                                )
                                f.write(decrypted_chunk)

                                # Update download progress
                                downloaded += len(chunk)
                                task.progress["current_file_progress"] = downloaded / \
                                    total_size if total_size > 0 else 0
                                task.progress["downloaded_bytes"] += len(chunk)

                                # Update download speed
                                elapsed = time.time() - start_time
                                task.update_speed(len(chunk), elapsed)

                                # Send progress notification
                                self._emit_progress(task_id, task.progress)

                        # Rename temporary file
                        if os.path.exists(temp_filename):
                            os.rename(temp_filename, ts_filename)
                            successful_files.append(ts_filename)

                            # Update segment info
                            task.segments_info[segment_key] = {
                                "status": "completed",
                                "size": os.path.getsize(ts_filename),
                                "timestamp": time.time()
                            }

                            success = True
                            logger.debug(
                                f"Successfully downloaded segment {i+1}/{task.segments}")
                            break

                    except Exception as e:
                        logger.error(
                            f"Failed to download segment {i}: {e}", exc_info=True)

                        # Clean up failed temporary file
                        if os.path.exists(temp_filename):
                            try:
                                os.remove(temp_filename)
                            except:
                                pass

                    # Wait before retry
                    time.sleep(retry_delay * (attempt + 1))

                # Update task progress
                if success:
                    task.progress["completed"] += 1
                else:
                    task.progress["failed"] += 1

                # Save progress periodically
                if i % 10 == 0:
                    task.save_progress()

                # Send progress notification
                self._emit_progress(task_id, task.progress)

            # Handle download results
            if task.canceled_event.is_set():
                logger.info(f"Task canceled: {task.name}")
                task.status = TaskStatus.CANCELED
                self._emit_status_changed(
                    task_id, TaskStatus.RUNNING, task.status)
                task.save_progress()
                return

            # Merge video files
            if successful_files:
                logger.info(
                    f"Starting to merge {len(successful_files)} video segments")
                task.progress["current_file"] = "Merging video"

                # Merge files
                merge_result = merge_files(
                    successful_files, task.output_file, self.settings)

                if merge_result["success"]:
                    logger.success(
                        f"Video merge successful: {task.output_file}")
                    task.status = TaskStatus.COMPLETED
                    task.progress["end_time"] = time.time()
                    self._emit_status_changed(
                        task_id, TaskStatus.RUNNING, task.status)
                    self._emit_completed(
                        task_id, True, f"Video download and merge successful: {task.output_file}")
                else:
                    logger.error(
                        f"Video merge failed: {merge_result['error']}")
                    task.status = TaskStatus.FAILED
                    self._emit_status_changed(
                        task_id, TaskStatus.RUNNING, task.status)
                    self._emit_completed(
                        task_id, False, f"Video merge failed: {merge_result['error']}")
            else:
                logger.error(
                    "No successfully downloaded video segments to merge")
                task.status = TaskStatus.FAILED
                self._emit_status_changed(
                    task_id, TaskStatus.RUNNING, task.status)
                self._emit_completed(
                    task_id, False, "No successfully downloaded video segments to merge")

            # Auto cleanup temporary files
            auto_cleanup = self.settings.get(
                "general", "auto_cleanup", True) if self.settings else True
            keep_temp = self.settings.get(
                "advanced", "keep_temp_files", False) if self.settings else False

            if auto_cleanup and not keep_temp:
                logger.info(f"Cleaning up temporary files: {temp_dir}")
                for file in successful_files:
                    try:
                        if os.path.exists(file):
                            os.remove(file)
                    except Exception as e:
                        logger.warning(
                            f"Failed to clean up file: {file}, error: {e}")

                try:
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                except Exception as e:
                    logger.warning(
                        f"Failed to delete temporary directory: {temp_dir}, error: {e}")

            # Save final progress
            task.save_progress()

            # Remove from active tasks
            with self.lock:
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)

        except Exception as e:
            logger.error(f"Task execution error: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())

            task.status = TaskStatus.FAILED
            self._emit_status_changed(task_id, TaskStatus.RUNNING, task.status)
            self._emit_completed(
                task_id, False, f"Task execution error: {str(e)}")

            # Remove from active tasks
            with self.lock:
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)

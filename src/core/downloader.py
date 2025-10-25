import requests
import time
import threading
import os
import json
import uuid
from pathlib import Path
from queue import PriorityQueue, Queue, Empty
from enum import Enum
from datetime import datetime
from loguru import logger
from typing import (
    Optional, List, Dict, Tuple, Set, Callable, Any, Union, Literal, Protocol, TypedDict
)

# Enhanced error handling imports
from .exceptions import (
    VidTaniumException, ErrorCategory, ErrorSeverity, ErrorContext,
    NetworkException, ConnectionTimeoutException, HTTPException,
    FilesystemException, InsufficientSpaceException, PermissionException,
    EncryptionException, DecryptionKeyException, ValidationException,
    InvalidURLException, InvalidSegmentException, ResourceException,
    MemoryException, SystemException, ConfigurationException
)
from .error_handler import ErrorHandler, error_handler
from .retry_manager import IntelligentRetryManager, retry_manager
from .resource_manager import resource_manager, ResourceType, register_for_cleanup
from .connection_pool import connection_pool_manager, HostPoolConfig
from .adaptive_timeout import adaptive_timeout_manager
from .memory_optimizer import memory_optimizer
# Enhanced resource manager is now merged into resource_manager
from .adaptive_retry import adaptive_retry_manager, RetryReason
from .circuit_breaker import circuit_breaker_manager
from .progressive_recovery import progressive_recovery_manager
from .segment_validator import segment_validator, ValidationResult
from .intelligent_recovery import intelligent_recovery_system
from .integrity_verifier import content_integrity_verifier, IntegrityLevel


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
    retry_manager: Optional[ErrorHandler]  # Changed to Optional[ErrorHandler]
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
                 priority: TaskPriority = TaskPriority.NORMAL) -> None:
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
        self.settings = settings or {}  # 
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
        # paused_event.is_set() == True means paused, False means not paused
        # Initialize as not paused (clear)

        # Progress tracking
        self.progress_file = f"{output_file}.progress" if output_file else None
        self.recent_speeds = []

    def get_progress_percentage(self) -> float:
        """Get progress percentage"""
        if self.progress["total"] == 0 or self.segments == 0:
            return 0.0
        return round((self.progress["completed"] / self.progress["total"]) * 100, 2)

    def start(self, worker_func: Callable[[str], None]) -> None:
        """Start task"""
        if self.status == TaskStatus.RUNNING:
            return

        self.status = TaskStatus.RUNNING
        self.progress["start_time"] = self.progress.get(
            "start_time") or time.time()
        self.paused_event.clear()  # Clear pause state (not paused)
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
        if self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]:
            return

        self.status = TaskStatus.PAUSED
        self.paused_event.set()  # Set pause event

    def resume(self) -> None:
        """Resume task"""
        if self.status != TaskStatus.PAUSED:
            return

        self.status = TaskStatus.PENDING
        self.paused_event.clear()  # Clear pause event

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
            self.speed_samples = [
                (t, s) for t, s in self.speed_samples if t >= cutoff_time]

            # Calculate weighted average speed (more recent samples have higher weight)
            if self.speed_samples:
                total_weight: float = 0.0
                weighted_speed: float = 0.0
                for sample_time, speed in self.speed_samples:
                    # Weight decreases exponentially with age
                    age = current_time - sample_time
                    # Minimum weight of 0.1
                    weight = max(0.1, 1.0 - (age / 30.0))
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
                completed_ratio = self.progress["completed"] / \
                    self.progress["total"]
                if completed_ratio > 0 and self.progress["downloaded_bytes"] > 0:
                    # Estimate total download size based on current progress
                    estimated_total_bytes = self.progress["downloaded_bytes"] / \
                        completed_ratio
                    remaining_bytes = estimated_total_bytes - \
                        self.progress["downloaded_bytes"]
                    if remaining_bytes > 0:
                        self.progress["estimated_time"] = remaining_bytes / \
                            self.progress["speed"]
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
    """Enhanced download manager with intelligent error handling and retry mechanisms"""

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

    # Enhanced error handling components
    error_handler: ErrorHandler
    retry_manager: IntelligentRetryManager
    on_error_occurred: Optional[Callable[[str, VidTaniumException], None]]

    def __init__(self, settings: Optional[SettingsProvider] = None) -> None:
        """Initialize enhanced download manager with error handling"""
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
        self.on_error_occurred = None

        # Enhanced error handling components
        self.error_handler = ErrorHandler()
        self.retry_manager = IntelligentRetryManager(self.error_handler)

        # Enhanced connection pooling
        self.connection_pool = connection_pool_manager
        self._configure_connection_pools()

        # Adaptive timeout management
        self.timeout_manager = adaptive_timeout_manager

        # Memory optimization
        self.memory_optimizer = memory_optimizer

        # Enhanced resource management (now integrated into resource_manager)
        resource_manager.start_monitoring()

        # Adaptive retry management
        self.adaptive_retry_manager = adaptive_retry_manager

        # Circuit breaker management
        self.circuit_breaker_manager = circuit_breaker_manager
        self.circuit_breaker_manager.start_health_monitoring()

        # Progressive recovery management
        self.recovery_manager = progressive_recovery_manager

        # Segment validation
        self.segment_validator = segment_validator

        # Content integrity verification
        self.integrity_verifier = content_integrity_verifier

        # Callback lists
        self.progress_callbacks: List[Callable[[str, ProgressDict], None]] = []
        self.status_callbacks: List[Callable[[str, Optional[TaskStatus], TaskStatus], None]] = []

        # Event queue for old callback system
        self.event_queue = Queue()

        # Resource management integration
        self._register_for_resource_management()

        # Memory optimization settings
        self._max_concurrent_downloads = self._get_max_concurrent_downloads()
        self._memory_threshold = self._get_memory_threshold()
        self._last_memory_log: float = time.time()

    def _configure_connection_pools(self) -> None:
        """Configure connection pools for optimal performance"""
        # Start connection pool monitoring
        self.connection_pool.start_monitoring()

        # Configure default pool settings
        default_config = HostPoolConfig(
            max_connections=20,
            max_connections_per_host=8,
            connection_timeout=30.0,
            read_timeout=120.0,
            max_retries=3,
            backoff_factor=0.5,
            keep_alive_timeout=300.0,
            health_check_interval=60.0
        )

        # Apply settings from configuration if available
        if self.settings:
            max_conn = int(self.settings.get("download", "max_connections", 20))
            max_conn_per_host = int(self.settings.get("download", "max_connections_per_host", 8))
            conn_timeout = float(self.settings.get("download", "connection_timeout", 30.0))
            read_timeout = float(self.settings.get("download", "read_timeout", 120.0))

            default_config.max_connections = max_conn
            default_config.max_connections_per_host = max_conn_per_host
            default_config.connection_timeout = conn_timeout
            default_config.read_timeout = read_timeout

        # Store default config for new hosts
        self.default_pool_config = default_config

        logger.info(f"Connection pools configured: max_connections={default_config.max_connections}, "
                   f"max_per_host={default_config.max_connections_per_host}")

    def _register_for_resource_management(self) -> None:
        """Register this download manager for automatic resource management"""
        register_for_cleanup(
            self,
            ResourceType.DOWNLOAD_TASK,
            cleanup_callback=self._cleanup_resources,
            metadata={"component": "DownloadManager"}
        )

    def _get_max_concurrent_downloads(self) -> int:
        """Get maximum concurrent downloads based on system resources"""
        if self.settings:
            return int(self.settings.get("download", "max_concurrent_tasks", 3))
        return 3

    def _get_memory_threshold(self) -> int:
        """Get memory threshold in MB for triggering cleanup"""
        if self.settings:
            return int(self.settings.get("advanced", "memory_threshold_mb", 512))
        return 512

    def _cleanup_resources(self) -> None:
        """Cleanup resources when called by resource manager"""
        try:
            # Clean up completed tasks
            completed_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]
            ]

            for task_id in completed_tasks:
                self._cleanup_task_resources(task_id)

            # Force garbage collection if many tasks were cleaned
            if len(completed_tasks) > 5:
                import gc
                gc.collect()

            logger.debug(f"Cleaned up {len(completed_tasks)} completed tasks")

        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}", exc_info=True)

    def _handle_task_error(self, task_id: str, exception: Exception, retry_count: int = 0) -> None:
        """Handle task error with enhanced error reporting and intelligent recovery"""
        task = self.tasks.get(task_id)

        # Create error context
        error_context = ErrorContext(
            task_id=task_id,
            task_name=task.name if task else None,
            url=task.base_url if task else None,
            file_path=task.output_file if task else None,
            retry_count=retry_count
        )

        # Convert to VidTaniumException if needed
        enhanced_exception = self.error_handler.handle_exception(
            exception, error_context, f"task_{task_id}"
        )

        # Create intelligent recovery plan
        recovery_context = {
            "task_id": task_id,
            "task": task,
            "retry_count": retry_count,
            "segment_based": True,  # M3U8 downloads are segment-based
            "downloader": self
        }

        recovery_plan = intelligent_recovery_system.create_recovery_plan(
            enhanced_exception, recovery_context
        )

        # Try automated recovery first
        recovery_success, recovery_message = intelligent_recovery_system.execute_recovery_plan(
            recovery_plan, recovery_context
        )

        if recovery_success:
            logger.info(f"Automated recovery successful for task {task_id}: {recovery_message}")
            # Optionally restart the task or continue with recovery
        else:
            logger.warning(f"Automated recovery failed for task {task_id}: {recovery_message}")
            # Provide user guidance from the recovery plan
            if recovery_plan.user_guidance:
                logger.info("User guidance for recovery:")
                for guidance in recovery_plan.user_guidance:
                    logger.info(f"  - {guidance}")

        # Emit error signal with recovery information
        if self.on_error_occurred:
            # Enhance the exception with recovery information
            enhanced_exception.recovery_plan = recovery_plan
            enhanced_exception.recovery_attempted = recovery_success
            self.on_error_occurred(task_id, enhanced_exception)

        # Update task status if task exists
        if task:
            if enhanced_exception.severity == ErrorSeverity.CRITICAL:
                task.status = TaskStatus.FAILED
            elif not enhanced_exception.is_retryable:
                task.status = TaskStatus.FAILED

        logger.error(f"Task error handled: {enhanced_exception.get_user_friendly_message()}")

    def _execute_with_retry(self, operation: Callable, operation_id: str, context: ErrorContext) -> Any:
        """Execute operation with intelligent retry logic"""
        return self.retry_manager.execute_with_retry(
            operation, operation_id, context
        )

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

        # Stop all enhanced components
        try:
            # Stop circuit breaker health monitoring
            self.circuit_breaker_manager.stop_health_monitoring()

            # Stop resource manager monitoring
            resource_manager.stop_monitoring()

            # Stop connection pool monitoring
            self.connection_pool.stop_monitoring()

            # Clean up memory optimizer
            self.memory_optimizer.cleanup()

            # Clean up recovery manager
            # Note: Progressive recovery sessions are kept for resume capability

            logger.info("All enhanced components stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping enhanced components: {e}")

        logger.info("Download manager stopped")

    def add_task(self, task: DownloadTask) -> str:
        """Add download task with memory optimization"""
        with self.lock:
            # Check memory usage before adding new task
            self._check_memory_usage()

            self.tasks[task.task_id] = task
            # Add task to priority queue
            self.tasks_queue.put(
                (-task.priority.value, time.time(), task.task_id))

            # Register task for resource management
            register_for_cleanup(
                task,
                ResourceType.DOWNLOAD_TASK,
                cleanup_callback=lambda: self._cleanup_task_resources(task.task_id),
                metadata={"task_name": task.name, "task_id": task.task_id}
            )

            # Register with enhanced resource manager (now integrated)
            resource_manager.register_resource(
                task,
                ResourceType.DOWNLOAD_TASK,
                resource_id=task.task_id,
                cleanup_callback=lambda: self._enhanced_cleanup_task(task.task_id),
                metadata={"task_name": task.name, "priority": task.priority.value}
            )

            logger.info(f"Task added: {task.name} (ID: {task.task_id})")

        # Don't emit status change for initial status setting
        # Only emit when status actually changes from one state to another

        return task.task_id

    def _check_memory_usage(self) -> None:
        """Check memory usage and trigger cleanup if needed with enhanced optimization"""
        # Use the memory optimizer for comprehensive memory management
        memory_status = self.memory_optimizer.check_memory_pressure()

        if memory_status["action"] == "reduce_usage":
            logger.warning(f"High memory usage detected: {memory_status['memory_percent']:.1f}%")
            self._cleanup_resources()

        elif memory_status["action"] == "garbage_collect":
            logger.debug("Triggered garbage collection due to memory increase")

        # Log memory statistics periodically
        if hasattr(self, '_last_memory_log'):
            if time.time() - self._last_memory_log > 300:  # Every 5 minutes
                stats = self.memory_optimizer.get_memory_stats()
                logger.info(f"Memory stats - Used: {stats['system_memory']['used_mb']:.1f}MB, "
                           f"Available: {stats['system_memory']['available_mb']:.1f}MB, "
                           f"Active buffers: {stats['optimizer_stats']['active_buffers']}")
                self._last_memory_log = time.time()
        else:
            self._last_memory_log = time.time()

    def _cleanup_task_resources(self, task_id: str) -> None:
        """Clean up resources for a specific task"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return

            # Clean up temporary files
            if hasattr(task, 'temp_files'):
                for temp_file in getattr(task, 'temp_files', []):
                    try:
                        if Path(temp_file).exists():
                            Path(temp_file).unlink()
                            logger.debug(f"Cleaned up temp file: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temp file {temp_file}: {e}")

            # Clear large data structures
            if hasattr(task, 'segments_data'):
                task.segments_data = None

        except Exception as e:
            logger.error(f"Error cleaning up task resources for {task_id}: {e}")

    def _enhanced_cleanup_task(self, task_id: str) -> None:
        """Enhanced cleanup for tasks using the enhanced resource manager"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return

            # Perform standard cleanup
            self._cleanup_task_resources(task_id)

            # Additional enhanced cleanup
            if hasattr(task, 'worker_thread') and task.worker_thread:
                if task.worker_thread.is_alive():
                    task.cancel()
                    task.worker_thread.join(timeout=5.0)

            # Clean up any streaming buffers
            buffer_context = f"segment_{task_id}_*"
            # Note: In a real implementation, you'd track active buffers per task

            # Remove from tasks dictionary if completed/failed/cancelled
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]:
                with self.lock:
                    if task_id in self.tasks:
                        del self.tasks[task_id]
                        logger.debug(f"Removed task {task_id} from tasks dictionary")

        except Exception as e:
            logger.error(f"Error in enhanced cleanup for task {task_id}: {e}")

    def _classify_error_for_retry(self, exception: Exception) -> RetryReason:
        """Classify exception for adaptive retry strategy"""
        error_message = str(exception).lower()
        exception_type = type(exception).__name__.lower()

        # Network timeout errors
        if ('timeout' in error_message or 'timeout' in exception_type or
            'timed out' in error_message):
            return RetryReason.NETWORK_TIMEOUT

        # Connection errors
        if ('connection' in error_message or 'connection' in exception_type or
            'connect' in error_message or 'unreachable' in error_message):
            return RetryReason.CONNECTION_ERROR

        # HTTP errors
        if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            status_code = exception.response.status_code
            if status_code == 429:
                return RetryReason.RATE_LIMITED
            elif 500 <= status_code < 600:
                return RetryReason.SERVER_ERROR
            elif 400 <= status_code < 500:
                return RetryReason.HTTP_ERROR

        # Rate limiting
        if ('rate limit' in error_message or 'too many requests' in error_message or
            '429' in error_message):
            return RetryReason.RATE_LIMITED

        # Server errors
        if ('server error' in error_message or '500' in error_message or
            'internal server' in error_message or 'service unavailable' in error_message):
            return RetryReason.SERVER_ERROR

        # Temporary failures
        if ('temporary' in error_message or 'retry' in error_message or
            'unavailable' in error_message):
            return RetryReason.TEMPORARY_FAILURE

        return RetryReason.UNKNOWN_ERROR

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

            # Check for existing recovery session
            recovery_info = self.recovery_manager.get_resume_info(task_id)
            if recovery_info and recovery_info["can_resume"]:
                logger.info(f"Found existing recovery session for task {task_id}: "
                           f"{recovery_info['completion_percentage']:.1f}% complete")
                # Update task progress from recovery info
                task.progress["completed"] = len(recovery_info["completed_segments"])
                task.progress["downloaded_bytes"] = recovery_info["downloaded_size"]

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

            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED, TaskStatus.PAUSED]:
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

    def _emit_status_changed(self, task_id: str, old_status: Optional[TaskStatus], new_status: TaskStatus) -> None:
        """Emit task status change event"""
        # Call old callback system
        if self.on_task_status_changed:
            event: EventTuple = ("status_changed", task_id,
                                 old_status, new_status)
            self.event_queue.put(event)

        # Call new callback system
        for callback in self.status_callbacks:
            try:
                callback(task_id, old_status, new_status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")

    def _emit_progress(self, task_id: str, progress: ProgressDict) -> None:
        """Emit task progress event"""
        # Call old callback system
        if self.on_task_progress:
            event: EventTuple = ("progress", task_id, progress)
            self.event_queue.put(event)

        # Call new callback system
        for callback in self.progress_callbacks:
            try:
                callback(task_id, progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def _emit_completed(self, task_id: str, success: bool, message: str) -> None:
        """Emit task completion event"""
        if success and self.on_task_completed:
            completion_event: EventTuple = ("completed", task_id, message)
            self.event_queue.put(completion_event)
        elif not success and self.on_task_failed:
            failure_event: EventTuple = ("failed", task_id, message)
            self.event_queue.put(failure_event)

    def _event_loop(self) -> None:
        """Event handling loop"""

        while self.running:
            try:
                # Get event from queue
                event: EventTuple = self.event_queue.get(timeout=0.5)
                event_type = event[0]

                if event_type == "status_changed" and self.on_task_status_changed:
                    if len(event) >= 4:
                        _, task_id_ev, old_status_ev, new_status_ev = event
                        if isinstance(task_id_ev, str):
                            self.on_task_status_changed(
                                task_id_ev, old_status_ev, new_status_ev)

                elif event_type == "progress" and self.on_task_progress:
                    if len(event) >= 3 and event[0] == "progress":
                        # Type should be Tuple[Literal["progress"], str, ProgressDict]
                        progress_event = event
                        task_id_ev = progress_event[1]
                        progress_ev = progress_event[2]
                        if isinstance(task_id_ev, str) and isinstance(progress_ev, dict):
                            self.on_task_progress(task_id_ev, progress_ev)

                elif event_type == "completed" and self.on_task_completed:
                    if len(event) >= 3 and event[0] == "completed":
                        # Type should be Tuple[Literal["completed"], str, str]
                        completed_event = event
                        task_id_ev = completed_event[1]
                        message_ev = completed_event[2]
                        if isinstance(task_id_ev, str) and isinstance(message_ev, str):
                            self.on_task_completed(task_id_ev, message_ev)

                elif event_type == "failed" and self.on_task_failed:
                    if len(event) >= 3 and event[0] == "failed":
                        # Type should be Tuple[Literal["failed"], str, str]
                        failed_event = event
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
                            _prio, _time, task_id_sched = self.tasks_queue.get_nowait()  # type: Tuple[int, float, str]

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
        """Enhanced task worker thread function with intelligent error handling"""
        from .decryptor import decrypt_data  # Assuming decrypt_data(bytes, bytes, bytes, bool) -> bytes
        # Assuming merge_files(List[str], str, Optional[SettingsProvider]) -> Dict[str, Any]
        from .merger import merge_files

        task = self.tasks.get(task_id)
        if not task:
            error_context = ErrorContext(task_id=task_id)
            exception = SystemException(
                message=f"Task not found in worker: {task_id}",
                context=error_context
            )
            self._handle_task_error(task_id, exception)
            return

        # Create error context for this task
        error_context = ErrorContext(
            task_id=task_id,
            task_name=task.name,
            url=task.base_url,
            file_path=task.output_file
        )

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

                    # Check if we should retry using adaptive retry manager
                    if attempt > 0:
                        retry_reason = RetryReason.UNKNOWN_ERROR  # Will be updated based on actual error
                        if not self.adaptive_retry_manager.should_retry(
                            task.key_url, attempt, retry_reason
                        ):
                            logger.warning(f"Adaptive retry manager suggests stopping retries for {task.key_url}")
                            break

                        # Get adaptive retry delay
                        retry_delay = self.adaptive_retry_manager.get_retry_delay(
                            task.key_url, attempt, retry_reason
                        )
                        logger.debug(f"Adaptive retry delay: {retry_delay:.2f}s for attempt {attempt}")
                        time.sleep(retry_delay)

                    try:
                        response = session.get(
                            task.key_url, timeout=timeout_val)
                        if response.status_code == 200:
                            task.key_data = response.content
                            key_size = len(
                                task.key_data) if task.key_data else 0
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
                    raise DecryptionKeyException(
                        key_url=task.key_url or "unknown",
                        key_error="Failed to download encryption key after retries",
                        context=ErrorContext(task_id=task_id)
                    )

            if not task.output_file:
                raise ConfigurationException(
                    setting="output_file",
                    value=None,
                    context=ErrorContext(task_id=task_id)
                )

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

            # Create recovery session for this task
            recovery_session = self.recovery_manager.create_recovery_session(
                task_id, task.name, task.base_url or "", task.output_file, task.segments
            )

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
                    raise InvalidURLException(
                        url="",
                        reason="Base URL not specified for task segments",
                        context=ErrorContext(task_id=task_id)
                    )
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

                        # Check circuit breaker before attempting download
                        if not self.circuit_breaker_manager.can_execute(segment_url):
                            logger.warning(f"Circuit breaker is OPEN for {segment_url}, skipping attempt")
                            time.sleep(retry_delay_val * (attempt + 1))
                            continue

                        # Use enhanced connection pooling
                        pooled_session = self.connection_pool.get_session(
                            segment_url,
                            error_context
                        )

                        # Get adaptive timeouts based on network conditions
                        conn_timeout, read_timeout = self.timeout_manager.get_timeouts(segment_url)
                        adaptive_timeout = (conn_timeout, read_timeout)

                        segment_start_time = time.time()
                        try:
                            response = pooled_session.get(
                                segment_url, stream=True, timeout=adaptive_timeout)

                            if response.status_code != 200:
                                # Enhanced error handling with specific status code handling
                                error_msg = f"HTTP {response.status_code}: {response.reason}"

                                if response.status_code == 404:
                                    logger.error(f"Segment not found (404): {segment_url}")
                                    # For 404, don't retry as the segment likely doesn't exist
                                    if attempt >= max_retries_val - 1:
                                        raise Exception(f"Segment not found: {error_msg}")
                                elif response.status_code == 403:
                                    logger.error(f"Access forbidden (403): {segment_url}")
                                    # For 403, try with different headers or authentication
                                    if attempt >= max_retries_val - 1:
                                        raise Exception(f"Access denied: {error_msg}")
                                elif response.status_code >= 500:
                                    logger.warning(f"Server error ({response.status_code}): {segment_url}")
                                    # Server errors are often temporary, retry with exponential backoff
                                    retry_delay = retry_delay_val * (2 ** attempt)
                                else:
                                    logger.warning(f"Client error ({response.status_code}): {segment_url}")
                                    retry_delay = retry_delay_val * (attempt + 1)

                                logger.warning(
                                    f"Segment download failed ({error_msg}), retry ({attempt+1}/{max_retries_val}) in {retry_delay:.1f}s")
                                time.sleep(retry_delay)
                                continue

                        except requests.exceptions.Timeout as e:
                            logger.warning(f"Segment download timeout: {segment_url} (attempt {attempt+1}/{max_retries_val})")
                            # Record timeout for adaptive timeout adjustment
                            self.timeout_manager.record_request(segment_url, 0, False, "timeout")

                            if attempt >= max_retries_val - 1:
                                raise Exception(f"Segment download timeout after {max_retries_val} attempts: {str(e)}")

                            # Increase timeout for next attempt
                            adaptive_timeout = (adaptive_timeout[0] * 1.5, adaptive_timeout[1] * 1.5)
                            time.sleep(retry_delay_val * (attempt + 1))
                            continue

                        except requests.exceptions.ConnectionError as e:
                            logger.warning(f"Connection error for segment: {segment_url} (attempt {attempt+1}/{max_retries_val})")
                            # Record connection error
                            self.timeout_manager.record_request(segment_url, 0, False, "connection")

                            if attempt >= max_retries_val - 1:
                                raise Exception(f"Connection failed after {max_retries_val} attempts: {str(e)}")

                            # Wait longer for connection errors
                            time.sleep(retry_delay_val * (attempt + 2))
                            continue

                        except requests.exceptions.RequestException as e:
                            logger.warning(f"Request error for segment: {segment_url} (attempt {attempt+1}/{max_retries_val}): {str(e)}")

                            if attempt >= max_retries_val - 1:
                                raise Exception(f"Request failed after {max_retries_val} attempts: {str(e)}")

                            time.sleep(retry_delay_val * (attempt + 1))
                            continue

                        total_size = int(
                            response.headers.get('content-length', 0))
                        downloaded_this_segment = 0
                        chunk_start_time = time.time()
                        last_speed_update = chunk_start_time

                        # Create optimized streaming buffer for this segment
                        buffer_context = f"segment_{task_id}_{i}"
                        streaming_buffer = self.memory_optimizer.create_streaming_buffer(buffer_context)

                        # Get optimal chunk size based on memory conditions
                        optimal_chunk_size = self.memory_optimizer.get_optimal_buffer_size(buffer_context)
                        chunk_size_val = min(chunk_size_val, optimal_chunk_size)

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

                                # Process chunk (decrypt if needed)
                                processed_chunk = chunk
                                if task.key_data:  # Ensure key_data is present
                                    processed_chunk = decrypt_data(chunk, task.key_data, iv, last_block=(
                                        downloaded_this_segment + len(chunk) >= total_size and total_size > 0))

                                # Use streaming buffer for efficient memory usage
                                bytes_written = streaming_buffer.write(processed_chunk)
                                if bytes_written < len(processed_chunk):
                                    # Buffer full, flush to file
                                    streaming_buffer.flush_to_file(f)
                                    streaming_buffer.write(processed_chunk[bytes_written:])

                                downloaded_this_segment += len(chunk)
                                task.progress["current_file_progress"] = downloaded_this_segment / \
                                    total_size if total_size > 0 else 0
                                task.progress["downloaded_bytes"] += len(chunk)

                                # Update speed calculation more accurately
                                current_time = time.time()
                                chunk_elapsed = current_time - chunk_process_start
                                if current_time - last_speed_update >= 0.5:  # Update speed every 0.5 seconds
                                    task.update_speed(
                                        len(chunk), chunk_elapsed)
                                    last_speed_update = current_time
                                    self._emit_progress(task_id, task.progress)

                        if task.canceled_event.is_set():
                            break  # Check after writing loop

                        # Flush any remaining data in buffer
                        streaming_buffer.flush_to_file(f)

                        # Record buffer performance for optimization
                        buffer_duration = time.time() - chunk_start_time
                        self.memory_optimizer.record_buffer_performance(
                            buffer_context, downloaded_this_segment, buffer_duration
                        )

                        # Release streaming buffer
                        self.memory_optimizer.release_streaming_buffer(buffer_context)

                        os.rename(temp_filename, ts_filename)
                        successful_files.append(ts_filename)
                        task.segments_info[segment_key] = {"status": "completed", "size": os.path.getsize(
                            ts_filename), "timestamp": time.time()}
                        segment_success = True

                        # Release session back to pool with success metrics
                        segment_end_time = time.time()
                        response_time = segment_end_time - segment_start_time
                        bytes_transferred = os.path.getsize(ts_filename)

                        # Record performance for adaptive timeout learning
                        self.timeout_manager.record_request(
                            segment_url,
                            response_time,
                            success=True
                        )

                        # Record successful attempt for adaptive retry learning
                        self.adaptive_retry_manager.record_attempt(
                            segment_url,
                            attempt + 1,
                            RetryReason.UNKNOWN_ERROR,  # Success case
                            success=True,
                            response_time=response_time
                        )

                        # Record success for circuit breaker
                        self.circuit_breaker_manager.record_success(segment_url, response_time)

                        # Validate downloaded segment
                        validation_report = self.segment_validator.validate_segment(
                            i, ts_filename, expected_size=downloaded_this_segment
                        )

                        if not validation_report.is_valid():
                            logger.warning(f"Segment {i} validation failed: {validation_report.error_message}")
                            # Remove invalid segment and retry
                            if os.path.exists(ts_filename):
                                os.remove(ts_filename)
                            continue

                        # Additional integrity verification for critical segments
                        if validation_report.has_warnings():
                            integrity_result = self.integrity_verifier.verify_file_integrity(
                                ts_filename, expected_hash=""
                            )
                            if not integrity_result.is_valid:
                                logger.warning(f"Segment {i} integrity check failed: {integrity_result.error_message}")
                                if os.path.exists(ts_filename):
                                    os.remove(ts_filename)
                                continue

                        # Update recovery session with completed segment
                        self.recovery_manager.mark_segment_complete(
                            task_id, i, ts_filename, os.path.getsize(ts_filename)
                        )

                        self.connection_pool.release_session(
                            pooled_session,
                            segment_url,
                            success=True,
                            bytes_transferred=bytes_transferred,
                            response_time=response_time
                        )

                        logger.debug(
                            f"Successfully downloaded segment {i+1}/{task.segments}")
                        break
                    except Exception as e:
                        # Clean up streaming buffer on error
                        if 'buffer_context' in locals():
                            self.memory_optimizer.release_streaming_buffer(buffer_context)

                        # Determine retry reason based on exception type
                        retry_reason = self._classify_error_for_retry(e)

                        # Record failure for adaptive timeout learning
                        if 'segment_start_time' in locals():
                            failure_time = time.time() - segment_start_time
                            error_type = type(e).__name__
                            self.timeout_manager.record_request(
                                segment_url,
                                failure_time,
                                success=False,
                                error_type=error_type
                            )

                            # Record failed attempt for adaptive retry learning
                            self.adaptive_retry_manager.record_attempt(
                                segment_url,
                                attempt + 1,
                                retry_reason,
                                success=False,
                                response_time=failure_time,
                                error_message=str(e)
                            )

                            # Record failure for circuit breaker
                            self.circuit_breaker_manager.record_failure(segment_url, str(e))

                        # Release session back to pool with failure metrics
                        if 'pooled_session' in locals():
                            self.connection_pool.release_session(
                                pooled_session,
                                segment_url,
                                success=False,
                                bytes_transferred=0,
                                response_time=failure_time if 'failure_time' in locals() else 0.0
                            )

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
            # Handle error with enhanced error handling system
            self._handle_task_error(task_id, e)

            # Update task status
            if task:
                task.status = TaskStatus.FAILED
                # Assuming it was RUNNING
                self._emit_status_changed(task_id, TaskStatus.RUNNING, task.status)

                # Create user-friendly error message
                enhanced_exception = self.error_handler.handle_exception(
                    e, error_context, f"task_{task_id}"
                )
                self._emit_completed(
                    task_id, False, enhanced_exception.get_user_friendly_message()
                )
        finally:
            with self.lock:
                if task_id in self.active_tasks:
                    self.active_tasks.remove(task_id)

    def get_all_tasks(self) -> List[str]:
        """Get all task IDs"""
        with self.lock:
            return list(self.tasks.keys())

    def get_tasks_by_status(self, status: TaskStatus) -> List[str]:
        """Get task IDs by status"""
        with self.lock:
            return [task_id for task_id, task in self.tasks.items() if task.status == status]

    def set_progress_callback(self, callback: Callable[[str, ProgressDict], None]) -> None:
        """Set progress callback"""
        self.progress_callbacks.append(callback)
        self.on_task_progress = callback  # Also set old-style callback for compatibility

    def set_status_changed_callback(self, callback: Callable[[str, Optional[TaskStatus], TaskStatus], None]) -> None:
        """Set status changed callback"""
        self.status_callbacks.append(callback)
        self.on_task_status_changed = callback  # Also set old-style callback for compatibility

    def set_bandwidth_limit(self, limit: Optional[int]) -> None:
        """Set bandwidth limit in bytes per second"""
        self.bandwidth_limit = limit or 0
        logger.info(f"Bandwidth limit set to: {limit} bytes/sec" if limit else "Bandwidth limit removed")

    def set_task_completed_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set task completed callback"""
        self.on_task_completed = callback

    def set_task_failed_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set task failed callback"""
        self.on_task_failed = callback

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all enhanced components"""
        stats = {
            "download_manager": {
                "total_tasks": len(self.tasks),
                "active_tasks": len(self.get_tasks_by_status(TaskStatus.RUNNING)),
                "completed_tasks": len(self.get_tasks_by_status(TaskStatus.COMPLETED)),
                "failed_tasks": len(self.get_tasks_by_status(TaskStatus.FAILED)),
            },
            "connection_pool": self.connection_pool.get_stats(),
            "adaptive_timeout": self.timeout_manager.get_global_stats(),
            "memory_optimizer": self.memory_optimizer.get_memory_stats(),
            "resource_manager": resource_manager.get_enhanced_stats(),
            "adaptive_retry": self.adaptive_retry_manager.get_global_stats(),
            "circuit_breakers": self.circuit_breaker_manager.get_all_stats(),
            "segment_validator": self.segment_validator.get_validation_stats(),
            "integrity_verifier": self.integrity_verifier.get_verification_stats(),
        }
        return stats

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from all components"""
        return {
            "network_quality": self.timeout_manager.get_global_stats().get("global_network_quality", 1.0),
            "memory_usage": self.memory_optimizer.get_memory_stats(),
            "connection_health": self.connection_pool.get_stats(),
            "retry_success_rate": self.adaptive_retry_manager.get_global_stats(),
            "circuit_breaker_status": self.circuit_breaker_manager.get_all_stats()["state_summary"],
            "validation_success_rate": self.segment_validator.get_validation_stats().get("success_rate", 1.0),
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        stats = self.get_comprehensive_stats()

        # Calculate health scores
        network_health = stats["adaptive_timeout"].get("global_network_quality", 1.0)
        memory_health = 1.0 - (stats["memory_optimizer"]["system_memory"]["percent"] / 100.0)
        circuit_health = 1.0 - (stats["circuit_breakers"]["state_summary"]["open"] /
                               max(stats["circuit_breakers"]["total_circuit_breakers"], 1))

        overall_health = (network_health + memory_health + circuit_health) / 3.0

        return {
            "overall_health": overall_health,
            "network_health": network_health,
            "memory_health": memory_health,
            "circuit_health": circuit_health,
            "status": "healthy" if overall_health > 0.7 else "degraded" if overall_health > 0.4 else "critical",
            "recommendations": self._get_health_recommendations(stats)
        }

    def _get_health_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Get health improvement recommendations"""
        recommendations = []

        # Memory recommendations
        memory_percent = stats["memory_optimizer"]["system_memory"]["percent"]
        if memory_percent > 80:
            recommendations.append("High memory usage detected - consider reducing concurrent downloads")

        # Circuit breaker recommendations
        open_circuits = stats["circuit_breakers"]["state_summary"]["open"]
        if open_circuits > 0:
            recommendations.append(f"{open_circuits} circuit breakers are open - check network connectivity")

        # Network quality recommendations
        network_quality = stats["adaptive_timeout"].get("global_network_quality", 1.0)
        if network_quality < 0.5:
            recommendations.append("Poor network quality detected - consider reducing concurrency or checking connection")

        return recommendations

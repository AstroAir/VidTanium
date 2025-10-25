"""
Queue Manager for VidTanium
Provides advanced download queue management with priority, reordering, and smart scheduling
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from queue import PriorityQueue
import heapq
from collections import defaultdict

from loguru import logger


class TaskPriority(Enum):
    """Task priority levels"""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class SchedulingStrategy(Enum):
    """Queue scheduling strategies"""
    PRIORITY_FIRST = "priority_first"
    SIZE_OPTIMIZED = "size_optimized"
    TIME_BALANCED = "time_balanced"
    RESOURCE_AWARE = "resource_aware"
    USER_DEFINED = "user_defined"


@dataclass
class QueuedTask:
    """Task in the download queue"""
    task_id: str
    name: str
    url: str
    output_path: str
    file_size: int
    priority: TaskPriority
    estimated_duration: float
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    scheduled_at: Optional[float] = None
    attempts: int = 0
    max_attempts: int = 3
    
    def __lt__(self, other) -> None:
        """Comparison for priority queue"""
        # Lower priority value = higher priority
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        # If same priority, prefer smaller files for faster completion
        return self.file_size < other.file_size


@dataclass
class QueueStatistics:
    """Queue statistics and metrics"""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_wait_time: float
    estimated_total_time: float
    queue_efficiency: float
    priority_distribution: Dict[str, int]
    size_distribution: Dict[str, int]


class SmartScheduler:
    """Smart scheduling algorithms for queue optimization"""
    
    def __init__(self) -> None:
        self.strategy = SchedulingStrategy.PRIORITY_FIRST
        self.max_concurrent_tasks = 3
        self.size_threshold_mb = 100
        self.time_threshold_minutes = 30
    
    def schedule_tasks(
        self,
        pending_tasks: List[QueuedTask],
        running_tasks: List[QueuedTask],
        system_resources: Dict[str, float]
    ) -> List[QueuedTask]:
        """Schedule tasks based on current strategy"""
        
        if self.strategy == SchedulingStrategy.PRIORITY_FIRST:
            return self._priority_first_scheduling(pending_tasks, running_tasks)
        elif self.strategy == SchedulingStrategy.SIZE_OPTIMIZED:
            return self._size_optimized_scheduling(pending_tasks, running_tasks)
        elif self.strategy == SchedulingStrategy.TIME_BALANCED:
            return self._time_balanced_scheduling(pending_tasks, running_tasks)
        elif self.strategy == SchedulingStrategy.RESOURCE_AWARE:
            return self._resource_aware_scheduling(pending_tasks, running_tasks, system_resources)
        else:
            return self._priority_first_scheduling(pending_tasks, running_tasks)
    
    def _priority_first_scheduling(
        self,
        pending_tasks: List[QueuedTask],
        running_tasks: List[QueuedTask]
    ) -> List[QueuedTask]:
        """Schedule based on priority only"""
        available_slots = max(0, self.max_concurrent_tasks - len(running_tasks))
        if available_slots == 0:
            return []
        
        # Sort by priority and take top tasks
        sorted_tasks = sorted(pending_tasks, key=lambda t: (t.priority.value, t.created_at))
        return sorted_tasks[:available_slots]
    
    def _size_optimized_scheduling(
        self,
        pending_tasks: List[QueuedTask],
        running_tasks: List[QueuedTask]
    ) -> List[QueuedTask]:
        """Schedule smaller files first for faster completion"""
        available_slots = max(0, self.max_concurrent_tasks - len(running_tasks))
        if available_slots == 0:
            return []
        
        # Separate by priority, then sort by size within each priority
        priority_groups = defaultdict(list)
        for task in pending_tasks:
            priority_groups[task.priority].append(task)
        
        scheduled: List[QueuedTask] = []
        for priority in sorted(priority_groups.keys(), key=lambda p: p.value):
            if len(scheduled) >= available_slots:
                break
            
            # Sort by size within priority group
            group_tasks = sorted(priority_groups[priority], key=lambda t: t.file_size)
            remaining_slots = available_slots - len(scheduled)
            scheduled.extend(group_tasks[:remaining_slots])
        
        return scheduled
    
    def _time_balanced_scheduling(
        self,
        pending_tasks: List[QueuedTask],
        running_tasks: List[QueuedTask]
    ) -> List[QueuedTask]:
        """Balance between quick wins and important tasks"""
        available_slots = max(0, self.max_concurrent_tasks - len(running_tasks))
        if available_slots == 0:
            return []
        
        # Score tasks based on priority and estimated completion time
        scored_tasks = []
        for task in pending_tasks:
            priority_score = 6 - task.priority.value  # Higher priority = higher score
            size_score = max(1, 10 - (task.file_size / (100 * 1024 * 1024)))  # Smaller = higher score
            time_score = max(1, 10 - (task.estimated_duration / 3600))  # Faster = higher score
            
            total_score = priority_score * 0.5 + size_score * 0.3 + time_score * 0.2
            scored_tasks.append((total_score, task))
        
        # Sort by score and take top tasks
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        return [task for _, task in scored_tasks[:available_slots]]
    
    def _resource_aware_scheduling(
        self,
        pending_tasks: List[QueuedTask],
        running_tasks: List[QueuedTask],
        system_resources: Dict[str, float]
    ) -> List[QueuedTask]:
        """Schedule based on system resource availability"""
        cpu_usage = system_resources.get('cpu_percent', 50)
        memory_usage = system_resources.get('memory_percent', 50)
        network_usage = system_resources.get('network_percent', 50)
        
        # Adjust concurrent tasks based on resource usage
        if cpu_usage > 80 or memory_usage > 80:
            max_tasks = max(1, self.max_concurrent_tasks - 1)
        elif network_usage > 90:
            max_tasks = max(1, self.max_concurrent_tasks - 2)
        else:
            max_tasks = self.max_concurrent_tasks
        
        available_slots = max(0, max_tasks - len(running_tasks))
        if available_slots == 0:
            return []
        
        # Prefer smaller tasks when resources are constrained
        if cpu_usage > 70 or memory_usage > 70:
            return self._size_optimized_scheduling(pending_tasks, running_tasks)
        else:
            return self._priority_first_scheduling(pending_tasks, running_tasks)


class QueueManager:
    """Download queue manager with smart scheduling"""
    
    def __init__(self) -> None:
        self.pending_queue: List[QueuedTask] = []
        self.running_tasks: Dict[str, QueuedTask] = {}
        self.completed_tasks: Dict[str, QueuedTask] = {}
        self.failed_tasks: Dict[str, QueuedTask] = {}
        
        self.lock = threading.RLock()
        self.scheduler = SmartScheduler()
        
        # Callbacks
        self.task_scheduled_callbacks: List[Callable[[QueuedTask], None]] = []
        self.task_completed_callbacks: List[Callable[[QueuedTask], None]] = []
        self.queue_changed_callbacks: List[Callable[[], None]] = []
        
        # Statistics
        self.statistics_history: List[Tuple[float, QueueStatistics]] = []
        self.max_history_size = 1000
        
        # Auto-scheduling
        self.auto_schedule_enabled = True
        self.schedule_interval = 5.0  # seconds
        self._schedule_timer: Optional[threading.Timer] = None
        self._start_auto_scheduling()
    
    def add_task(
        self,
        task_id: str,
        name: str,
        url: str,
        output_path: str,
        file_size: int = 0,
        priority: TaskPriority = TaskPriority.NORMAL,
        estimated_duration: float = 0,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3
    ) -> bool:
        """Add task to queue"""
        with self.lock:
            # Check if task already exists
            if (task_id in self.running_tasks or 
                task_id in self.completed_tasks or
                any(t.task_id == task_id for t in self.pending_queue)):
                logger.warning(f"Task {task_id} already exists in queue")
                return False
            
            task = QueuedTask(
                task_id=task_id,
                name=name,
                url=url,
                output_path=output_path,
                file_size=file_size,
                priority=priority,
                estimated_duration=estimated_duration,
                dependencies=dependencies or [],
                metadata=metadata or {},
                max_attempts=max_attempts
            )
            
            # Insert in priority order
            self._insert_task_by_priority(task)
            
            logger.info(f"Added task {task_id} to queue with priority {priority.name}")
            self._trigger_queue_changed_callbacks()
            
            # Trigger immediate scheduling if auto-schedule is enabled
            if self.auto_schedule_enabled:
                self._schedule_next_tasks()
            
            return True
    
    def _insert_task_by_priority(self, task: QueuedTask) -> None:
        """Insert task in queue maintaining priority order"""
        inserted = False
        for i, existing_task in enumerate(self.pending_queue):
            if task < existing_task:
                self.pending_queue.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.pending_queue.append(task)
    
    def remove_task(self, task_id: str) -> bool:
        """Remove task from queue"""
        with self.lock:
            # Check pending queue
            for i, task in enumerate(self.pending_queue):
                if task.task_id == task_id:
                    del self.pending_queue[i]
                    logger.info(f"Removed task {task_id} from pending queue")
                    self._trigger_queue_changed_callbacks()
                    return True
            
            # Check running tasks
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
                logger.info(f"Removed running task {task_id}")
                self._trigger_queue_changed_callbacks()
                return True
            
            return False
    
    def move_task(self, task_id: str, new_position: int) -> bool:
        """Move task to new position in queue"""
        with self.lock:
            # Find task in pending queue
            task_index = -1
            for i, task in enumerate(self.pending_queue):
                if task.task_id == task_id:
                    task_index = i
                    break
            
            if task_index == -1:
                return False
            
            # Remove and reinsert at new position
            task = self.pending_queue.pop(task_index)
            new_position = max(0, min(new_position, len(self.pending_queue)))
            self.pending_queue.insert(new_position, task)
            
            logger.info(f"Moved task {task_id} to position {new_position}")
            self._trigger_queue_changed_callbacks()
            return True
    
    def change_task_priority(self, task_id: str, new_priority: TaskPriority) -> bool:
        """Change task priority and reorder queue"""
        with self.lock:
            # Find task in pending queue
            task_index = -1
            for i, task in enumerate(self.pending_queue):
                if task.task_id == task_id:
                    task_index = i
                    break
            
            if task_index == -1:
                return False
            
            # Update priority and reorder
            task = self.pending_queue.pop(task_index)
            task.priority = new_priority
            self._insert_task_by_priority(task)
            
            logger.info(f"Changed task {task_id} priority to {new_priority.name}")
            self._trigger_queue_changed_callbacks()
            return True
    
    def get_next_tasks(self, count: int = 1) -> List[QueuedTask]:
        """Get next tasks to be scheduled"""
        with self.lock:
            system_resources = self._get_system_resources()
            available_tasks = [t for t in self.pending_queue if self._can_schedule_task(t)]
            
            scheduled_tasks = self.scheduler.schedule_tasks(
                available_tasks,
                list(self.running_tasks.values()),
                system_resources
            )
            return list(scheduled_tasks[:count])
    
    def _can_schedule_task(self, task: QueuedTask) -> bool:
        """Check if task can be scheduled (dependencies met)"""
        if not task.dependencies:
            return True
        
        # Check if all dependencies are completed
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        
        return True
    
    def mark_task_running(self, task_id: str) -> bool:
        """Mark task as running"""
        with self.lock:
            # Find task in pending queue
            for i, task in enumerate(self.pending_queue):
                if task.task_id == task_id:
                    task.scheduled_at = time.time()
                    self.running_tasks[task_id] = self.pending_queue.pop(i)
                    logger.info(f"Task {task_id} started running")
                    self._trigger_queue_changed_callbacks()
                    return True
            
            return False
    
    def mark_task_completed(self, task_id: str) -> bool:
        """Mark task as completed"""
        with self.lock:
            if task_id in self.running_tasks:
                task = self.running_tasks.pop(task_id)
                self.completed_tasks[task_id] = task
                logger.info(f"Task {task_id} completed")
                
                self._trigger_task_completed_callbacks(task)
                self._trigger_queue_changed_callbacks()
                
                # Schedule next tasks
                if self.auto_schedule_enabled:
                    self._schedule_next_tasks()
                
                return True
            
            return False
    
    def mark_task_failed(self, task_id: str, retry: bool = True) -> bool:
        """Mark task as failed"""
        with self.lock:
            if task_id in self.running_tasks:
                task = self.running_tasks.pop(task_id)
                task.attempts += 1
                
                if retry and task.attempts < task.max_attempts:
                    # Retry: put back in queue with lower priority
                    if task.priority.value < TaskPriority.BACKGROUND.value:
                        task.priority = TaskPriority(task.priority.value + 1)
                    
                    self._insert_task_by_priority(task)
                    logger.info(f"Task {task_id} failed, retrying (attempt {task.attempts})")
                else:
                    # Max attempts reached or no retry
                    self.failed_tasks[task_id] = task
                    logger.info(f"Task {task_id} failed permanently")
                
                self._trigger_queue_changed_callbacks()
                
                # Schedule next tasks
                if self.auto_schedule_enabled:
                    self._schedule_next_tasks()
                
                return True
            
            return False
    
    def _schedule_next_tasks(self) -> None:
        """Schedule next available tasks"""
        next_tasks = self.get_next_tasks(self.scheduler.max_concurrent_tasks)
        
        for task in next_tasks:
            if len(self.running_tasks) < self.scheduler.max_concurrent_tasks:
                self._trigger_task_scheduled_callbacks(task)
    
    def _get_system_resources(self) -> Dict[str, float]:
        """Get current system resource usage"""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'network_percent': 50.0  # Placeholder - would need network monitoring
            }
        except ImportError:
            return {'cpu_percent': 50.0, 'memory_percent': 50.0, 'network_percent': 50.0}
    
    def get_queue_statistics(self) -> QueueStatistics:
        """Get current queue statistics"""
        with self.lock:
            total_tasks = (len(self.pending_queue) + len(self.running_tasks) + 
                          len(self.completed_tasks) + len(self.failed_tasks))
            
            # Calculate average wait time
            current_time = time.time()
            wait_times = []
            for task in self.pending_queue:
                wait_times.append(current_time - task.created_at)
            for task in self.running_tasks.values():
                if task.scheduled_at:
                    wait_times.append(task.scheduled_at - task.created_at)
            
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
            
            # Priority distribution
            priority_dist: Dict[str, int] = defaultdict(int)
            for task in self.pending_queue:
                priority_dist[task.priority.name] += 1
            
            # Size distribution
            size_dist = {"small": 0, "medium": 0, "large": 0}
            for task in self.pending_queue:
                if task.file_size < 10 * 1024 * 1024:  # < 10MB
                    size_dist["small"] += 1
                elif task.file_size < 100 * 1024 * 1024:  # < 100MB
                    size_dist["medium"] += 1
                else:
                    size_dist["large"] += 1
            
            # Estimated total time
            estimated_time = sum(task.estimated_duration for task in self.pending_queue)
            
            # Queue efficiency (completed vs failed ratio)
            total_finished = len(self.completed_tasks) + len(self.failed_tasks)
            efficiency = (len(self.completed_tasks) / total_finished * 100) if total_finished > 0 else 100
            
            return QueueStatistics(
                total_tasks=total_tasks,
                pending_tasks=len(self.pending_queue),
                running_tasks=len(self.running_tasks),
                completed_tasks=len(self.completed_tasks),
                failed_tasks=len(self.failed_tasks),
                average_wait_time=avg_wait_time,
                estimated_total_time=estimated_time,
                queue_efficiency=efficiency,
                priority_distribution=dict(priority_dist),
                size_distribution=size_dist
            )
    
    def _start_auto_scheduling(self) -> None:
        """Start auto-scheduling timer"""
        if self._schedule_timer:
            self._schedule_timer.cancel()
        
        self._schedule_timer = threading.Timer(self.schedule_interval, self._auto_schedule_tick)
        self._schedule_timer.daemon = True
        self._schedule_timer.start()
    
    def _auto_schedule_tick(self) -> None:
        """Auto-scheduling timer tick"""
        try:
            if self.auto_schedule_enabled:
                self._schedule_next_tasks()
        except Exception as e:
            logger.error(f"Error in auto-scheduling: {e}")
        finally:
            self._start_auto_scheduling()
    
    def register_task_scheduled_callback(self, callback: Callable[[QueuedTask], None]) -> None:
        """Register callback for when tasks are scheduled"""
        self.task_scheduled_callbacks.append(callback)
    
    def register_task_completed_callback(self, callback: Callable[[QueuedTask], None]) -> None:
        """Register callback for when tasks are completed"""
        self.task_completed_callbacks.append(callback)
    
    def register_queue_changed_callback(self, callback: Callable[[], None]) -> None:
        """Register callback for queue changes"""
        self.queue_changed_callbacks.append(callback)
    
    def _trigger_task_scheduled_callbacks(self, task: QueuedTask) -> None:
        """Trigger task scheduled callbacks"""
        for callback in self.task_scheduled_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Error in task scheduled callback: {e}")
    
    def _trigger_task_completed_callbacks(self, task: QueuedTask) -> None:
        """Trigger task completed callbacks"""
        for callback in self.task_completed_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Error in task completed callback: {e}")
    
    def _trigger_queue_changed_callbacks(self) -> None:
        """Trigger queue changed callbacks"""
        for callback in self.queue_changed_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in queue changed callback: {e}")

    def get_task(self, task_id: str) -> Optional[QueuedTask]:
        """Get task by ID from any queue"""
        with self.lock:
            # Check pending tasks
            for task in self.pending_queue:
                if task.task_id == task_id:
                    return task

            # Check running tasks
            if task_id in self.running_tasks:
                return self.running_tasks[task_id]

            # Check completed tasks
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]

            # Check failed tasks
            if task_id in self.failed_tasks:
                return self.failed_tasks[task_id]

            return None

    def update_task_priority(self, task_id: str, new_priority: TaskPriority) -> bool:
        """Update task priority"""
        with self.lock:
            # Find task in pending queue
            for i, task in enumerate(self.pending_queue):
                if task.task_id == task_id:
                    # Remove from current position
                    self.pending_queue.pop(i)
                    # Update priority
                    task.priority = new_priority
                    # Re-insert with new priority
                    self._insert_task_by_priority(task)
                    logger.info(f"Updated task {task_id} priority to {new_priority.name}")
                    self._trigger_queue_changed_callbacks()
                    return True

            return False

    def reorder_tasks(self, new_order: List[str]) -> bool:
        """Reorder pending tasks"""
        with self.lock:
            # Validate that all task IDs exist in pending queue
            pending_ids = {task.task_id for task in self.pending_queue}
            if set(new_order) != pending_ids:
                return False

            # Create new ordered list
            task_map = {task.task_id: task for task in self.pending_queue}
            self.pending_queue = [task_map[task_id] for task_id in new_order]

            logger.info(f"Reordered {len(new_order)} pending tasks")
            self._trigger_queue_changed_callbacks()
            return True

    def clear_completed_tasks(self) -> int:
        """Clear all completed tasks"""
        with self.lock:
            count = len(self.completed_tasks)
            self.completed_tasks.clear()
            logger.info(f"Cleared {count} completed tasks")
            self._trigger_queue_changed_callbacks()
            return count


# Global queue manager instance
queue_manager = QueueManager()

# Backward compatibility alias
EnhancedQueueManager = QueueManager

"""
Batch Progress Aggregator for VidTanium
Provides progress aggregation and reporting for multiple simultaneous download operations
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

from loguru import logger


class AggregationMethod(Enum):
    """Methods for aggregating progress"""
    WEIGHTED_AVERAGE = "weighted_average"  # Based on file sizes
    SIMPLE_AVERAGE = "simple_average"     # Equal weight for all tasks
    COMPLETION_RATIO = "completion_ratio"  # Completed vs total tasks
    BYTES_RATIO = "bytes_ratio"           # Downloaded vs total bytes


@dataclass
class TaskProgress:
    """Progress information for a single task"""
    task_id: str
    name: str
    progress_percentage: float  # 0.0 to 100.0
    bytes_downloaded: int
    total_bytes: int
    speed: float  # bytes per second
    eta: Optional[float] = None  # seconds remaining
    status: str = "unknown"
    last_updated: float = field(default_factory=time.time)


@dataclass
class BatchProgress:
    """Aggregated progress for a batch of tasks"""
    batch_id: str
    name: str
    overall_progress: float  # 0.0 to 100.0
    total_tasks: int
    completed_tasks: int
    active_tasks: int
    failed_tasks: int
    paused_tasks: int
    total_bytes: int
    downloaded_bytes: int
    combined_speed: float  # bytes per second
    estimated_time_remaining: Optional[float] = None  # seconds
    start_time: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    task_progresses: Dict[str, TaskProgress] = field(default_factory=dict)


class BatchProgressAggregator:
    """Aggregates progress from multiple download tasks"""
    
    def __init__(self):
        self.batches: Dict[str, BatchProgress] = {}
        self.task_to_batch: Dict[str, str] = {}  # Map task ID to batch ID
        self.lock = threading.RLock()
        
        # Callbacks
        self.progress_callbacks: List[Callable[[str, BatchProgress], None]] = []
        self.completion_callbacks: List[Callable[[str, BatchProgress], None]] = []
        
        # Configuration
        self.update_interval = 1.0  # seconds
        self.stale_threshold = 30.0  # seconds
        
        # Statistics tracking
        self.statistics: Dict[str, Dict] = defaultdict(dict)
        
        # Auto-cleanup timer
        self.cleanup_timer = threading.Timer(300.0, self._cleanup_stale_data)  # 5 minutes
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
    
    def create_batch(
        self,
        batch_id: str,
        name: str,
        task_ids: List[str]
    ) -> BatchProgress:
        """Create a new batch for progress aggregation"""
        with self.lock:
            if batch_id in self.batches:
                logger.warning(f"Batch {batch_id} already exists, updating task list")
            
            batch = BatchProgress(
                batch_id=batch_id,
                name=name,
                overall_progress=0.0,
                total_tasks=len(task_ids),
                completed_tasks=0,
                active_tasks=0,
                failed_tasks=0,
                paused_tasks=0,
                total_bytes=0,
                downloaded_bytes=0,
                combined_speed=0.0
            )
            
            self.batches[batch_id] = batch
            
            # Map tasks to batch
            for task_id in task_ids:
                self.task_to_batch[task_id] = batch_id
            
            logger.info(f"Created batch {batch_id} with {len(task_ids)} tasks")
            return batch
    
    def update_task_progress(
        self,
        task_id: str,
        progress_percentage: float,
        bytes_downloaded: int,
        total_bytes: int,
        speed: float,
        status: str = "running",
        eta: Optional[float] = None,
        task_name: Optional[str] = None
    ):
        """Update progress for a specific task"""
        with self.lock:
            batch_id = self.task_to_batch.get(task_id)
            if not batch_id or batch_id not in self.batches:
                return
            
            batch = self.batches[batch_id]
            
            # Update task progress
            task_progress = TaskProgress(
                task_id=task_id,
                name=task_name or task_id,
                progress_percentage=progress_percentage,
                bytes_downloaded=bytes_downloaded,
                total_bytes=total_bytes,
                speed=speed,
                eta=eta,
                status=status
            )
            
            batch.task_progresses[task_id] = task_progress
            
            # Recalculate batch progress
            self._recalculate_batch_progress(batch_id)
            
            # Trigger callbacks
            self._trigger_progress_callbacks(batch_id, batch)
    
    def remove_task_from_batch(self, task_id: str):
        """Remove a task from its batch"""
        with self.lock:
            batch_id = self.task_to_batch.get(task_id)
            if not batch_id or batch_id not in self.batches:
                return
            
            batch = self.batches[batch_id]
            
            # Remove task
            if task_id in batch.task_progresses:
                del batch.task_progresses[task_id]
            
            del self.task_to_batch[task_id]
            batch.total_tasks = len(batch.task_progresses)
            
            # Recalculate progress
            self._recalculate_batch_progress(batch_id)
            
            logger.debug(f"Removed task {task_id} from batch {batch_id}")
    
    def _recalculate_batch_progress(self, batch_id: str):
        """Recalculate aggregated progress for a batch"""
        batch = self.batches[batch_id]
        task_progresses = list(batch.task_progresses.values())
        
        if not task_progresses:
            batch.overall_progress = 0.0
            batch.completed_tasks = 0
            batch.active_tasks = 0
            batch.failed_tasks = 0
            batch.paused_tasks = 0
            batch.total_bytes = 0
            batch.downloaded_bytes = 0
            batch.combined_speed = 0.0
            batch.estimated_time_remaining = None
            return
        
        # Count tasks by status
        status_counts: Dict[str, int] = defaultdict(int)
        for task in task_progresses:
            status_counts[task.status] += 1
        
        batch.completed_tasks = status_counts.get("completed", 0)
        batch.active_tasks = status_counts.get("running", 0) + status_counts.get("downloading", 0)
        batch.failed_tasks = status_counts.get("failed", 0)
        batch.paused_tasks = status_counts.get("paused", 0)
        
        # Calculate totals
        batch.total_bytes = sum(task.total_bytes for task in task_progresses)
        batch.downloaded_bytes = sum(task.bytes_downloaded for task in task_progresses)
        
        # Calculate combined speed (only from active tasks)
        active_tasks = [task for task in task_progresses if task.status in ["running", "downloading"]]
        batch.combined_speed = sum(task.speed for task in active_tasks)
        
        # Calculate overall progress using weighted average
        if batch.total_bytes > 0:
            batch.overall_progress = (batch.downloaded_bytes / batch.total_bytes) * 100.0
        else:
            # Fallback to simple average if no size information
            batch.overall_progress = statistics.mean(task.progress_percentage for task in task_progresses)
        
        # Calculate ETA
        remaining_bytes = batch.total_bytes - batch.downloaded_bytes
        if batch.combined_speed > 0 and remaining_bytes > 0:
            batch.estimated_time_remaining = remaining_bytes / batch.combined_speed
        else:
            # Use average of individual ETAs
            valid_etas = [task.eta for task in task_progresses if task.eta is not None and task.eta > 0]
            if valid_etas:
                batch.estimated_time_remaining = statistics.mean(valid_etas)
            else:
                batch.estimated_time_remaining = None
        
        batch.last_updated = time.time()
        
        # Update statistics
        self._update_batch_statistics(batch_id, batch)
        
        # Check for completion
        if batch.completed_tasks == batch.total_tasks and batch.total_tasks > 0:
            self._trigger_completion_callbacks(batch_id, batch)
    
    def get_batch_progress(self, batch_id: str) -> Optional[BatchProgress]:
        """Get current progress for a batch"""
        with self.lock:
            return self.batches.get(batch_id)
    
    def get_all_batches(self) -> Dict[str, BatchProgress]:
        """Get all current batches"""
        with self.lock:
            return self.batches.copy()
    
    def delete_batch(self, batch_id: str) -> bool:
        """Delete a batch and clean up associated data"""
        with self.lock:
            if batch_id not in self.batches:
                return False
            
            batch = self.batches[batch_id]
            
            # Remove task mappings
            task_ids_to_remove = []
            for task_id, mapped_batch_id in self.task_to_batch.items():
                if mapped_batch_id == batch_id:
                    task_ids_to_remove.append(task_id)
            
            for task_id in task_ids_to_remove:
                del self.task_to_batch[task_id]
            
            # Remove batch
            del self.batches[batch_id]
            
            # Clean up statistics
            if batch_id in self.statistics:
                del self.statistics[batch_id]
            
            logger.info(f"Deleted batch {batch_id}")
            return True
    
    def get_batch_statistics(self, batch_id: str) -> Optional[Dict]:
        """Get detailed statistics for a batch"""
        with self.lock:
            return self.statistics.get(batch_id)
    
    def _update_batch_statistics(self, batch_id: str, batch: BatchProgress):
        """Update statistics for a batch"""
        stats = self.statistics[batch_id]
        
        # Track progress over time
        if "progress_history" not in stats:
            stats["progress_history"] = []
        
        stats["progress_history"].append({
            "timestamp": time.time(),
            "progress": batch.overall_progress,
            "speed": batch.combined_speed,
            "active_tasks": batch.active_tasks
        })
        
        # Keep only recent history (last hour)
        cutoff_time = time.time() - 3600
        stats["progress_history"] = [
            entry for entry in stats["progress_history"]
            if entry["timestamp"] >= cutoff_time
        ]
        
        # Calculate derived statistics
        if len(stats["progress_history"]) > 1:
            recent_entries = stats["progress_history"][-10:]  # Last 10 entries
            
            # Average speed over recent period
            stats["average_speed"] = statistics.mean(entry["speed"] for entry in recent_entries)
            
            # Progress rate (percentage per minute)
            if len(recent_entries) >= 2:
                time_diff = recent_entries[-1]["timestamp"] - recent_entries[0]["timestamp"]
                progress_diff = recent_entries[-1]["progress"] - recent_entries[0]["progress"]
                
                if time_diff > 0:
                    stats["progress_rate"] = (progress_diff / time_diff) * 60  # per minute
                else:
                    stats["progress_rate"] = 0
            
            # Peak speed
            all_speeds = [entry["speed"] for entry in stats["progress_history"]]
            stats["peak_speed"] = max(all_speeds) if all_speeds else 0
        
        # Efficiency metrics
        if batch.total_tasks > 0:
            stats["completion_rate"] = batch.completed_tasks / batch.total_tasks
            stats["failure_rate"] = batch.failed_tasks / batch.total_tasks
            stats["active_ratio"] = batch.active_tasks / batch.total_tasks
        
        # Duration
        stats["duration"] = time.time() - batch.start_time
    
    def _cleanup_stale_data(self):
        """Clean up stale batches and restart timer"""
        try:
            with self.lock:
                current_time = time.time()
                stale_batches = []
                
                for batch_id, batch in self.batches.items():
                    if current_time - batch.last_updated > self.stale_threshold:
                        # Check if batch is actually complete or abandoned
                        if (batch.completed_tasks == batch.total_tasks or 
                            batch.active_tasks == 0):
                            stale_batches.append(batch_id)
                
                for batch_id in stale_batches:
                    logger.info(f"Cleaning up stale batch: {batch_id}")
                    self.delete_batch(batch_id)
        
        except Exception as e:
            logger.error(f"Error during batch cleanup: {e}")
        
        finally:
            # Restart cleanup timer
            self.cleanup_timer = threading.Timer(300.0, self._cleanup_stale_data)
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()
    
    def register_progress_callback(self, callback: Callable[[str, BatchProgress], None]):
        """Register callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def register_completion_callback(self, callback: Callable[[str, BatchProgress], None]):
        """Register callback for batch completion"""
        self.completion_callbacks.append(callback)
    
    def _trigger_progress_callbacks(self, batch_id: str, batch: BatchProgress):
        """Trigger progress update callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(batch_id, batch)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def _trigger_completion_callbacks(self, batch_id: str, batch: BatchProgress):
        """Trigger completion callbacks"""
        for callback in self.completion_callbacks:
            try:
                callback(batch_id, batch)
            except Exception as e:
                logger.error(f"Error in completion callback: {e}")
    
    def get_aggregation_summary(self) -> Dict:
        """Get summary of all batch aggregations"""
        with self.lock:
            return {
                "total_batches": len(self.batches),
                "active_batches": len([b for b in self.batches.values() if b.active_tasks > 0]),
                "completed_batches": len([b for b in self.batches.values() 
                                        if b.completed_tasks == b.total_tasks and b.total_tasks > 0]),
                "total_tasks": sum(b.total_tasks for b in self.batches.values()),
                "total_active_tasks": sum(b.active_tasks for b in self.batches.values()),
                "combined_speed": sum(b.combined_speed for b in self.batches.values()),
                "total_bytes": sum(b.total_bytes for b in self.batches.values()),
                "downloaded_bytes": sum(b.downloaded_bytes for b in self.batches.values())
            }


# Global batch progress aggregator instance
batch_progress_aggregator = BatchProgressAggregator()

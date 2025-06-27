"""
Enhanced progress reporting utilities for accurate and smooth progress updates
"""

import time
from dataclasses import dataclass
from typing import Optional, Callable, List, Union
from threading import RLock


@dataclass
class ProgressMetrics:
    """Container for progress metrics"""
    current: int = 0
    total: int = 0
    speed: float = 0.0  # bytes per second
    eta: Optional[float] = None  # seconds
    percentage: float = 0.0
    elapsed_time: float = 0.0


class SmoothProgressReporter:
    """
    Enhanced progress reporter with smooth updates and accurate calculations
    """
    
    def __init__(self, update_interval: float = 0.1, smoothing_factor: float = 0.3):
        """
        Args:
            update_interval: Minimum interval between progress updates (seconds)
            smoothing_factor: Factor for exponential smoothing (0-1)
        """
        self.update_interval = update_interval
        self.smoothing_factor = smoothing_factor
        
        self._lock = RLock()
        self._start_time: Optional[float] = None
        self._last_update_time: float = 0
        self._last_progress: int = 0
        self._speed_samples: List[float] = []
        self._smooth_speed: float = 0.0
          # Callbacks
        self._progress_callback: Optional[Callable[[ProgressMetrics], None]] = None
        self._completion_callback: Optional[Callable[[], None]] = None
    
    def set_progress_callback(self, callback: Callable[[ProgressMetrics], None]):
        """Set the progress update callback"""
        self._progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[], None]):
        """Set the completion callback"""
        self._completion_callback = callback
    
    def start(self):
        """Start progress tracking"""
        with self._lock:
            self._start_time = time.time()
            self._last_update_time = self._start_time
            self._last_progress = 0
            self._speed_samples.clear()
            self._smooth_speed = 0.0
    
    def update(self, current: int, total: int, force_update: bool = False):
        """
        Update progress
        
        Args:
            current: Current progress value
            total: Total value
            force_update: Force update even if interval hasn't passed
        """
        with self._lock:
            if self._start_time is None:
                self.start()
            
            now = time.time()
            
            # Check if we should update based on time interval
            if not force_update and (now - self._last_update_time) < self.update_interval:
                return
            
            # Calculate metrics
            metrics = self._calculate_metrics(current, total, now)
            
            # Update internal state
            self._last_update_time = now
            self._last_progress = current
              # Call progress callback
            if self._progress_callback:
                self._progress_callback(metrics)
            
            # Check for completion
            if current >= total and self._completion_callback:
                self._completion_callback()
    
    def _calculate_metrics(self, current: int, total: int, now: float) -> ProgressMetrics:
        """Calculate progress metrics"""
        if self._start_time is None:
            elapsed_time = 0.0
        else:
            elapsed_time = now - self._start_time
        
        # Calculate percentage
        percentage = (current / total * 100) if total > 0 else 0
        
        # Calculate speed
        speed = self._calculate_smooth_speed(current, now)
        
        # Calculate ETA
        eta = None
        if speed > 0 and current < total:
            remaining = total - current
            eta = remaining / speed
        
        return ProgressMetrics(
            current=current,
            total=total,
            speed=speed,
            eta=eta,
            percentage=percentage,
            elapsed_time=elapsed_time
        )
    
    def _calculate_smooth_speed(self, current: int, now: float) -> float:
        """Calculate smoothed speed using exponential smoothing"""
        if self._last_update_time == 0:
            return 0.0
        
        time_diff = now - self._last_update_time
        if time_diff <= 0:
            return self._smooth_speed
        
        # Calculate instantaneous speed
        progress_diff = current - self._last_progress
        instant_speed = progress_diff / time_diff
        
        # Add to samples
        self._speed_samples.append(instant_speed)
        
        # Keep only recent samples (last 10 seconds worth)
        max_samples = int(10 / self.update_interval)
        if len(self._speed_samples) > max_samples:
            self._speed_samples = self._speed_samples[-max_samples:]
        
        # Apply exponential smoothing
        if self._smooth_speed == 0:
            self._smooth_speed = instant_speed
        else:
            self._smooth_speed = (
                self.smoothing_factor * instant_speed + 
                (1 - self.smoothing_factor) * self._smooth_speed
            )
        
        return max(0, self._smooth_speed)
    
    def finish(self):
        """Mark progress as finished"""
        with self._lock:
            if self._completion_callback:
                self._completion_callback()
    
    def reset(self):
        """Reset progress state"""
        with self._lock:
            self._start_time = None
            self._last_update_time = 0
            self._last_progress = 0
            self._speed_samples.clear()
            self._smooth_speed = 0.0


class BatchProgressReporter:
    """
    Progress reporter for batch operations with multiple items
    """
    
    def __init__(self, total_items: int, update_callback: Optional[Callable] = None):
        self.total_items = total_items
        self.update_callback = update_callback
        
        self._completed_items = 0
        self._current_item_progress = 0.0
        self._lock = RLock()
    
    def start_item(self, item_index: int, item_name: str = ""):
        """Start processing a new item"""
        with self._lock:
            self._current_item_progress = 0.0
            if self.update_callback:
                self.update_callback({
                    'type': 'item_started',
                    'item_index': item_index,
                    'item_name': item_name,
                    'total_items': self.total_items
                })
    
    def update_item_progress(self, progress: float):
        """Update current item progress (0.0 to 1.0)"""
        with self._lock:
            self._current_item_progress = max(0.0, min(1.0, progress))
            self._notify_overall_progress()
    
    def complete_item(self):
        """Mark current item as completed"""
        with self._lock:
            self._completed_items += 1
            self._current_item_progress = 1.0
            self._notify_overall_progress()
            
            if self.update_callback:
                self.update_callback({
                    'type': 'item_completed',
                    'completed_items': self._completed_items,
                    'total_items': self.total_items
                })
    
    def _notify_overall_progress(self):
        """Calculate and notify overall progress"""
        if self.total_items == 0:
            overall_progress = 1.0
        else:
            overall_progress = (
                self._completed_items + self._current_item_progress
            ) / self.total_items
        
        if self.update_callback:
            self.update_callback({
                'type': 'overall_progress',
                'progress': overall_progress,
                'completed_items': self._completed_items,
                'current_item_progress': self._current_item_progress,
                'total_items': self.total_items
            })
    
    def is_complete(self) -> bool:
        """Check if all items are completed"""
        return self._completed_items >= self.total_items

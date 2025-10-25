"""
Event Handling System for VidTanium
Streamlines event handling to improve GUI responsiveness and reduce overhead
"""

import time
import weakref
from typing import Dict, List, Callable, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from loguru import logger


class EventPriority(Enum):
    """Event priority levels"""
    CRITICAL = 0    # Immediate processing
    HIGH = 1        # Process within 10ms
    NORMAL = 2      # Process within 50ms
    LOW = 3         # Process within 200ms
    BACKGROUND = 4  # Process when idle


@dataclass
class Event:
    """Event structure"""
    event_type: str
    data: Any
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    source_id: Optional[str] = None
    callback: Optional[Callable[['Event'], None]] = None
    processed: bool = False
    
    def __post_init__(self) -> None:
        if self.timestamp == 0:
            self.timestamp = time.time()


class EventBatcher:
    """Batches similar events to reduce processing overhead"""
    
    def __init__(self, batch_window: float = 0.016) -> None:  # ~60fps
        self.batch_window = batch_window
        self.batched_events: Dict[str, List[Event]] = {}
        self.last_flush: Dict[str, float] = {}
    
    def add_event(self, event: Event) -> bool:
        """Add event to batch, returns True if should be processed immediately"""
        event_key = f"{event.event_type}_{event.source_id}"
        current_time = time.time()
        
        # Critical events are never batched
        if event.priority == EventPriority.CRITICAL:
            return True
        
        # Initialize batch if needed
        if event_key not in self.batched_events:
            self.batched_events[event_key] = []
            self.last_flush[event_key] = current_time
        
        # Add to batch
        self.batched_events[event_key].append(event)
        
        # Check if batch should be flushed
        time_since_last_flush = current_time - self.last_flush[event_key]
        batch_size = len(self.batched_events[event_key])
        
        # Flush conditions
        should_flush = (
            time_since_last_flush >= self.batch_window or
            batch_size >= 10 or  # Max batch size
            event.priority in [EventPriority.HIGH, EventPriority.CRITICAL]
        )
        
        return should_flush
    
    def flush_batch(self, event_key: str) -> List[Event]:
        """Flush and return batched events"""
        events = self.batched_events.get(event_key, [])
        if events:
            self.batched_events[event_key] = []
            self.last_flush[event_key] = time.time()
        return events
    
    def get_ready_batches(self) -> Dict[str, List[Event]]:
        """Get all batches ready for processing"""
        ready_batches = {}
        current_time = time.time()
        
        for event_key, events in self.batched_events.items():
            if not events:
                continue
                
            time_since_last_flush = current_time - self.last_flush[event_key]
            if time_since_last_flush >= self.batch_window:
                ready_batches[event_key] = self.flush_batch(event_key)
        
        return ready_batches


class EventSystem(QObject):
    """Event system with batching and priority queues"""
    
    # Signals for different priority levels
    critical_event = Signal(object)
    high_priority_event = Signal(object)
    normal_event = Signal(object)
    low_priority_event = Signal(object)
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        # Event queues by priority
        self.event_queues: Dict[EventPriority, deque[Event]] = {
            priority: deque() for priority in EventPriority
        }

        # Event batching
        self.batcher = EventBatcher()

        # Registered handlers
        self.handlers: Dict[str, List[weakref.ref[Callable[[Event], None]]]] = {}
        self.handler_stats: Dict[str, Dict[str, Any]] = {}
        
        # Processing control
        self.processing_enabled = True
        self.max_events_per_cycle = 50
        self.processing_stats = {
            "events_processed": 0,
            "events_dropped": 0,
            "average_processing_time": 0.0
        }
        
        # Timers for different priority levels
        self._setup_processing_timers()
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
    
    def _setup_processing_timers(self) -> None:
        """Setup timers for processing different priority events"""
        # Critical events - immediate processing
        self.critical_timer = QTimer()
        self.critical_timer.timeout.connect(lambda: self._process_priority_queue(EventPriority.CRITICAL))
        self.critical_timer.setSingleShot(True)
        
        # High priority - 10ms intervals
        self.high_priority_timer = QTimer()
        self.high_priority_timer.timeout.connect(lambda: self._process_priority_queue(EventPriority.HIGH))
        self.high_priority_timer.start(10)
        
        # Normal priority - 50ms intervals
        self.normal_timer = QTimer()
        self.normal_timer.timeout.connect(lambda: self._process_priority_queue(EventPriority.NORMAL))
        self.normal_timer.start(50)
        
        # Low priority - 200ms intervals
        self.low_priority_timer = QTimer()
        self.low_priority_timer.timeout.connect(lambda: self._process_priority_queue(EventPriority.LOW))
        self.low_priority_timer.start(200)
        
        # Background - 1000ms intervals
        self.background_timer = QTimer()
        self.background_timer.timeout.connect(lambda: self._process_priority_queue(EventPriority.BACKGROUND))
        self.background_timer.start(1000)
    
    def register_handler(self, event_type: str, handler: Callable[[Event], None], priority: EventPriority = EventPriority.NORMAL) -> None:
        """Register an event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
            self.handler_stats[event_type] = {
                "call_count": 0,
                "total_time": 0.0,
                "average_time": 0.0,
                "error_count": 0
            }
        
        # Use weak reference to avoid memory leaks
        handler_ref = weakref.ref(handler)
        self.handlers[event_type].append(handler_ref)
        
        logger.debug(f"Registered handler for event type: {event_type}")
    
    def emit_event(self, event_type: str, data: Any = None, priority: EventPriority = EventPriority.NORMAL,
                   source_id: Optional[str] = None, callback: Optional[Callable[[Event], None]] = None) -> None:
        """Emit an event"""
        if not self.processing_enabled:
            self.processing_stats["events_dropped"] += 1
            return
        
        event = Event(
            event_type=event_type,
            data=data,
            priority=priority,
            source_id=source_id,
            callback=callback
        )
        
        # Check if event should be batched
        if priority != EventPriority.CRITICAL:
            should_process_immediately = self.batcher.add_event(event)
            if not should_process_immediately:
                return  # Event was batched
        
        # Add to appropriate priority queue
        self.event_queues[priority].append(event)
        
        # Trigger immediate processing for critical events
        if priority == EventPriority.CRITICAL:
            self.critical_timer.start(0)
    
    def _process_priority_queue(self, priority: EventPriority) -> None:
        """Process events from a specific priority queue"""
        if not self.processing_enabled:
            return
        
        queue = self.event_queues[priority]
        processed_count = 0
        start_time = time.time()
        
        # Process ready batches first
        if priority != EventPriority.CRITICAL:
            ready_batches = self.batcher.get_ready_batches()
            for event_key, events in ready_batches.items():
                for event in events:
                    if event.priority == priority:
                        queue.append(event)
        
        # Process events from queue
        while queue and processed_count < self.max_events_per_cycle:
            event = queue.popleft()
            
            try:
                self._process_single_event(event)
                processed_count += 1
                self.processing_stats["events_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing event {event.event_type}: {e}", exc_info=True)
                if event.event_type in self.handler_stats:
                    self.handler_stats[event.event_type]["error_count"] += 1
        
        # Update performance stats
        processing_time = time.time() - start_time
        if processed_count > 0:
            avg_time = processing_time / processed_count
            self.performance_monitor.record_processing_time(priority, avg_time)
    
    def _process_single_event(self, event: Event) -> None:
        """Process a single event"""
        if event.processed:
            return
        
        handlers = self.handlers.get(event.event_type, [])
        if not handlers:
            return
        
        # Clean up dead references and call live handlers
        live_handlers = []
        for handler_ref in handlers:
            handler = handler_ref()
            if handler is not None:
                live_handlers.append(handler)
                
                # Call handler with performance tracking
                start_time = time.time()
                try:
                    handler(event)
                    
                    # Update stats
                    call_time = time.time() - start_time
                    stats = self.handler_stats[event.event_type]
                    stats["call_count"] += 1
                    stats["total_time"] += call_time
                    stats["average_time"] = stats["total_time"] / stats["call_count"]
                    
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type}: {e}")
                    self.handler_stats[event.event_type]["error_count"] += 1
        
        # Update handlers list to remove dead references
        if len(live_handlers) != len(handlers):
            self.handlers[event.event_type] = [weakref.ref(h) for h in live_handlers]
        
        # Call event callback if provided
        if event.callback:
            try:
                event.callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
        
        event.processed = True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "processing_stats": self.processing_stats.copy(),
            "handler_stats": self.handler_stats.copy(),
            "queue_sizes": {
                priority.name: len(queue) for priority, queue in self.event_queues.items()
            },
            "performance_monitor": self.performance_monitor.get_stats()
        }


class PerformanceMonitor:
    """Monitors event processing performance"""
    
    def __init__(self, history_size: int = 1000) -> None:
        self.history_size = history_size
        self.processing_times: Dict[EventPriority, deque] = {
            priority: deque(maxlen=history_size) for priority in EventPriority
        }
    
    def record_processing_time(self, priority: EventPriority, time_ms: float) -> None:
        """Record processing time for a priority level"""
        self.processing_times[priority].append(time_ms)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        
        for priority, times in self.processing_times.items():
            if times:
                stats[priority.name] = {
                    "count": len(times),
                    "average": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times)
                }
            else:
                stats[priority.name] = {"count": 0, "average": 0, "min": 0, "max": 0}
        
        return stats


# Global event system instance
_event_system: Optional[EventSystem] = None


def get_event_system() -> EventSystem:
    """Get the global event system instance"""
    global _event_system
    if _event_system is None:
        _event_system = EventSystem()
    return _event_system


def emit_event(event_type: str, data: Any = None, priority: EventPriority = EventPriority.NORMAL) -> None:
    """Convenience function to emit an event"""
    get_event_system().emit_event(event_type, data, priority)

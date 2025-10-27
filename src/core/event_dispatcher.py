"""
Pure Python Event Dispatcher for VidTanium Core

Provides a thread-safe, Qt-independent event system for communication between
core components and GUI layers. Uses weak references to prevent memory leaks.
"""

import threading
import weakref
from typing import Callable, Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class EventType(Enum):
    """Core event types for download operations"""
    TASK_PROGRESS = "task_progress"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ERROR_OCCURRED = "error_occurred"
    BANDWIDTH_UPDATE = "bandwidth_update"
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_PAUSED = "download_paused"
    DOWNLOAD_RESUMED = "download_resumed"
    DOWNLOAD_CANCELED = "download_canceled"


@dataclass
class Event:
    """Event data container"""
    event_type: EventType
    data: Dict[str, Any]
    source: Optional[str] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            import time
            self.timestamp = time.time()


class EventDispatcher:
    """
    Thread-safe event dispatcher with weak reference support.
    
    This dispatcher allows components to subscribe to events without creating
    strong references that could prevent garbage collection.
    
    Example:
        dispatcher = EventDispatcher()
        
        def on_progress(event):
            print(f"Progress: {event.data}")
        
        # Subscribe to events
        dispatcher.subscribe(EventType.TASK_PROGRESS, on_progress)
        
        # Emit events
        dispatcher.emit(EventType.TASK_PROGRESS, {"task_id": "123", "progress": 50})
        
        # Unsubscribe
        dispatcher.unsubscribe(EventType.TASK_PROGRESS, on_progress)
    """

    def __init__(self):
        """Initialize the event dispatcher"""
        # Store callbacks with weak references where possible
        self._subscribers: Dict[EventType, List[Any]] = {}
        self._lock = threading.RLock()
        self._enabled = True
        
        # Statistics
        self._event_count: Dict[EventType, int] = {}
        self._total_events = 0

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None], 
                  weak: bool = True) -> bool:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event is emitted
            weak: If True, use weak reference (default). Set False for lambdas/bound methods.
        
        Returns:
            bool: True if subscription successful
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            # Check if already subscribed
            for existing in self._subscribers[event_type]:
                existing_callback = self._get_callback(existing)
                if existing_callback is callback:
                    logger.debug(f"Callback already subscribed to {event_type.value}")
                    return False
            
            # Store callback with weak reference if possible
            if weak:
                try:
                    # Try to create weak reference
                    if hasattr(callback, '__self__'):
                        # Bound method - need to keep weak refs to both object and function
                        obj = callback.__self__
                        func = callback.__func__
                        weak_ref = weakref.ref(obj, self._make_cleanup_callback(event_type))
                        self._subscribers[event_type].append(('weak_method', weak_ref, func))
                    else:
                        # Regular function
                        weak_ref = weakref.ref(callback, self._make_cleanup_callback(event_type))
                        self._subscribers[event_type].append(('weak_func', weak_ref))
                except TypeError:
                    # Can't create weak reference (e.g., lambda), store strong reference
                    logger.debug(f"Cannot create weak reference for callback, using strong reference")
                    self._subscribers[event_type].append(('strong', callback))
            else:
                # Strong reference requested
                self._subscribers[event_type].append(('strong', callback))
            
            logger.debug(f"Subscribed to {event_type.value} (weak={weak})")
            return True

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
        
        Returns:
            bool: True if unsubscription successful
        """
        with self._lock:
            if event_type not in self._subscribers:
                return False
            
            # Find and remove the callback
            subscribers = self._subscribers[event_type]
            for i, subscriber in enumerate(subscribers):
                existing_callback = self._get_callback(subscriber)
                if existing_callback is callback:
                    subscribers.pop(i)
                    logger.debug(f"Unsubscribed from {event_type.value}")
                    return True
            
            return False

    def emit(self, event_type: EventType, data: Dict[str, Any], 
             source: Optional[str] = None) -> int:
        """
        Emit an event to all subscribers.
        
        Args:
            event_type: The type of event to emit
            data: Event data dictionary
            source: Optional source identifier
        
        Returns:
            int: Number of callbacks invoked
        """
        if not self._enabled:
            return 0
        
        event = Event(event_type=event_type, data=data, source=source)
        
        with self._lock:
            # Update statistics
            self._total_events += 1
            self._event_count[event_type] = self._event_count.get(event_type, 0) + 1
            
            if event_type not in self._subscribers:
                return 0
            
            # Clean up dead weak references and collect valid callbacks
            valid_callbacks = []
            dead_refs = []
            
            for i, subscriber in enumerate(self._subscribers[event_type]):
                callback = self._get_callback(subscriber)
                if callback is None:
                    dead_refs.append(i)
                else:
                    valid_callbacks.append(callback)
            
            # Remove dead references (in reverse order to maintain indices)
            for i in reversed(dead_refs):
                self._subscribers[event_type].pop(i)
        
        # Invoke callbacks outside the lock to prevent deadlocks
        invoked = 0
        for callback in valid_callbacks:
            try:
                callback(event)
                invoked += 1
            except Exception as e:
                logger.error(f"Error in event callback for {event_type.value}: {e}", exc_info=True)
        
        return invoked

    def clear_subscribers(self, event_type: Optional[EventType] = None) -> None:
        """
        Clear all subscribers for a specific event type or all events.
        
        Args:
            event_type: Event type to clear, or None to clear all
        """
        with self._lock:
            if event_type is None:
                self._subscribers.clear()
                logger.debug("Cleared all event subscribers")
            elif event_type in self._subscribers:
                self._subscribers[event_type].clear()
                logger.debug(f"Cleared subscribers for {event_type.value}")

    def get_subscriber_count(self, event_type: EventType) -> int:
        """Get the number of active subscribers for an event type"""
        with self._lock:
            if event_type not in self._subscribers:
                return 0
            
            # Count only valid (non-dead) references
            count = 0
            for subscriber in self._subscribers[event_type]:
                if self._get_callback(subscriber) is not None:
                    count += 1
            return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get event dispatcher statistics"""
        with self._lock:
            return {
                "total_events": self._total_events,
                "event_counts": {et.value: count for et, count in self._event_count.items()},
                "subscriber_counts": {
                    et.value: self.get_subscriber_count(et) 
                    for et in EventType
                }
            }

    def enable(self) -> None:
        """Enable event dispatching"""
        self._enabled = True
        logger.debug("Event dispatcher enabled")

    def disable(self) -> None:
        """Disable event dispatching"""
        self._enabled = False
        logger.debug("Event dispatcher disabled")

    def _get_callback(self, subscriber: Any) -> Optional[Callable]:
        """Extract callback from subscriber tuple"""
        ref_type = subscriber[0]
        
        if ref_type == 'strong':
            return subscriber[1]
        elif ref_type == 'weak_func':
            weak_ref = subscriber[1]
            return weak_ref()
        elif ref_type == 'weak_method':
            weak_ref = subscriber[1]
            func = subscriber[2]
            obj = weak_ref()
            if obj is None:
                return None
            # Reconstruct bound method
            return func.__get__(obj, type(obj))
        
        return None

    def _make_cleanup_callback(self, event_type: EventType) -> Callable:
        """Create a cleanup callback for when weak references die"""
        def cleanup(weak_ref):
            # This is called when the weak reference is garbage collected
            # We don't need to do anything here as cleanup happens in emit()
            pass
        return cleanup


# Global event dispatcher instance
_global_dispatcher: Optional[EventDispatcher] = None
_dispatcher_lock = threading.Lock()


def get_event_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher instance"""
    global _global_dispatcher
    
    if _global_dispatcher is None:
        with _dispatcher_lock:
            if _global_dispatcher is None:
                _global_dispatcher = EventDispatcher()
    
    return _global_dispatcher


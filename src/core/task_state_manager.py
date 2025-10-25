"""
Enhanced Task State Manager for VidTanium
Provides robust task state management with consistent transitions and edge case handling
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from .exceptions import VidTaniumException, ErrorCategory, ErrorSeverity, ErrorContext


class TaskState(Enum):
    """Enhanced task states with clear definitions"""
    CREATED = "created"          # Task created but not queued
    QUEUED = "queued"           # Task queued for execution
    PREPARING = "preparing"      # Task preparing to start (validating, etc.)
    RUNNING = "running"         # Task actively running
    PAUSED = "paused"           # Task paused by user
    PAUSING = "pausing"         # Task in process of pausing
    RESUMING = "resuming"       # Task in process of resuming
    CANCELING = "canceling"     # Task in process of canceling
    CANCELED = "canceled"       # Task canceled by user
    COMPLETED = "completed"     # Task completed successfully
    FAILED = "failed"           # Task failed with error
    RETRYING = "retrying"       # Task retrying after failure
    CLEANING_UP = "cleaning_up" # Task cleaning up resources


class StateTransitionError(VidTaniumException):
    """Error for invalid state transitions"""
    
    def __init__(self, from_state: TaskState, to_state: TaskState, reason: str = "") -> None:
        message = f"Invalid transition from {from_state.value} to {to_state.value}"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM
        )
        self.from_state = from_state
        self.to_state = to_state


@dataclass
class StateTransition:
    """Information about a state transition"""
    from_state: TaskState
    to_state: TaskState
    timestamp: float
    reason: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class TaskStateInfo:
    """Complete task state information"""
    task_id: str
    current_state: TaskState
    previous_state: Optional[TaskState] = None
    state_changed_at: float = field(default_factory=time.time)
    transition_history: List[StateTransition] = field(default_factory=list)
    retry_count: int = 0
    error_count: int = 0
    last_error: Optional[VidTaniumException] = None
    metadata: Dict = field(default_factory=dict)


class TaskStateManager:
    """Enhanced task state manager with robust transition handling"""
    
    def __init__(self) -> None:
        self.task_states: Dict[str, TaskStateInfo] = {}
        self.state_callbacks: Dict[TaskState, List[Callable]] = {}
        self.transition_callbacks: List[Callable[[str, TaskState, TaskState], None]] = []
        self.lock = threading.RLock()
        
        # Define valid state transitions
        self.valid_transitions = self._define_valid_transitions()
        
        # State groups for easier management
        self.active_states = {TaskState.RUNNING, TaskState.PAUSING, TaskState.RESUMING, TaskState.RETRYING}
        self.terminal_states = {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED}
        self.transitional_states = {TaskState.PAUSING, TaskState.RESUMING, TaskState.CANCELING, TaskState.CLEANING_UP}
    
    def _define_valid_transitions(self) -> Dict[TaskState, Set[TaskState]]:
        """Define valid state transitions"""
        return {
            TaskState.CREATED: {
                TaskState.QUEUED, TaskState.CANCELED
            },
            TaskState.QUEUED: {
                TaskState.PREPARING, TaskState.CANCELED
            },
            TaskState.PREPARING: {
                TaskState.RUNNING, TaskState.FAILED, TaskState.CANCELED
            },
            TaskState.RUNNING: {
                TaskState.PAUSING, TaskState.CANCELING, TaskState.COMPLETED, 
                TaskState.FAILED, TaskState.RETRYING, TaskState.CLEANING_UP
            },
            TaskState.PAUSED: {
                TaskState.RESUMING, TaskState.CANCELING, TaskState.FAILED
            },
            TaskState.PAUSING: {
                TaskState.PAUSED, TaskState.CANCELING, TaskState.FAILED
            },
            TaskState.RESUMING: {
                TaskState.RUNNING, TaskState.FAILED, TaskState.CANCELING
            },
            TaskState.RETRYING: {
                TaskState.RUNNING, TaskState.FAILED, TaskState.CANCELING
            },
            TaskState.CANCELING: {
                TaskState.CANCELED, TaskState.CLEANING_UP
            },
            TaskState.CLEANING_UP: {
                TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED
            },
            # Terminal states generally don't transition
            TaskState.COMPLETED: set(),
            TaskState.FAILED: {TaskState.RETRYING, TaskState.QUEUED},  # Allow retry
            TaskState.CANCELED: set()
        }
    
    def create_task(self, task_id: str, initial_metadata: Optional[Dict] = None) -> TaskStateInfo:
        """Create a new task with initial state"""
        with self.lock:
            if task_id in self.task_states:
                raise ValueError(f"Task {task_id} already exists")
            
            state_info = TaskStateInfo(
                task_id=task_id,
                current_state=TaskState.CREATED,
                metadata=initial_metadata or {}
            )
            
            self.task_states[task_id] = state_info
            logger.debug(f"Created task {task_id} in state {TaskState.CREATED.value}")
            
            return state_info
    
    def transition_state(
        self,
        task_id: str,
        new_state: TaskState,
        reason: Optional[str] = None,
        metadata: Optional[Dict] = None,
        force: bool = False
    ) -> bool:
        """Transition task to new state with validation"""
        with self.lock:
            if task_id not in self.task_states:
                logger.error(f"Task {task_id} not found for state transition")
                return False
            
            state_info = self.task_states[task_id]
            current_state = state_info.current_state
            
            # Check if transition is valid
            if not force and not self._is_valid_transition(current_state, new_state):
                error = StateTransitionError(current_state, new_state, reason or "")
                logger.error(f"Invalid state transition for task {task_id}: {error.message}")
                return False
            
            # Handle special transition logic
            if not self._handle_special_transitions(state_info, new_state, reason):
                return False
            
            # Perform the transition
            previous_state = current_state
            state_info.previous_state = previous_state
            state_info.current_state = new_state
            state_info.state_changed_at = time.time()
            
            # Record transition in history
            transition = StateTransition(
                from_state=previous_state,
                to_state=new_state,
                timestamp=state_info.state_changed_at,
                reason=reason,
                metadata=metadata
            )
            state_info.transition_history.append(transition)
            
            # Update metadata if provided
            if metadata:
                state_info.metadata.update(metadata)
            
            logger.info(f"Task {task_id} transitioned from {previous_state.value} to {new_state.value}")
            
            # Trigger callbacks
            self._trigger_callbacks(task_id, previous_state, new_state)
            
            return True
    
    def _is_valid_transition(self, from_state: TaskState, to_state: TaskState) -> bool:
        """Check if state transition is valid"""
        valid_targets = self.valid_transitions.get(from_state, set())
        return to_state in valid_targets
    
    def _handle_special_transitions(
        self,
        state_info: TaskStateInfo,
        new_state: TaskState,
        reason: Optional[str]
    ) -> bool:
        """Handle special transition logic and edge cases"""
        
        # Handle retry transitions
        if new_state == TaskState.RETRYING:
            state_info.retry_count += 1
            logger.info(f"Task {state_info.task_id} retry attempt {state_info.retry_count}")
        
        # Handle error transitions
        elif new_state == TaskState.FAILED:
            state_info.error_count += 1
            if reason:
                # Store error information if provided
                state_info.metadata['last_error_reason'] = reason
        
        # Handle completion transitions
        elif new_state == TaskState.COMPLETED:
            # Clear any error information
            state_info.last_error = None
            state_info.metadata.pop('last_error_reason', None)
        
        # Handle transitional state timeouts
        elif new_state in self.transitional_states:
            # Set timeout for transitional states
            timeout_seconds = 30  # 30 seconds timeout for transitional states
            state_info.metadata['transition_timeout'] = time.time() + timeout_seconds
        
        return True
    
    def get_task_state(self, task_id: str) -> Optional[TaskStateInfo]:
        """Get current state information for a task"""
        with self.lock:
            return self.task_states.get(task_id)
    
    def get_tasks_by_state(self, state: TaskState) -> List[TaskStateInfo]:
        """Get all tasks in a specific state"""
        with self.lock:
            return [
                state_info for state_info in self.task_states.values()
                if state_info.current_state == state
            ]
    
    def get_active_tasks(self) -> List[TaskStateInfo]:
        """Get all active (non-terminal) tasks"""
        with self.lock:
            return [
                state_info for state_info in self.task_states.values()
                if state_info.current_state not in self.terminal_states
            ]
    
    def cleanup_task(self, task_id: str) -> bool:
        """Clean up task state information"""
        with self.lock:
            if task_id not in self.task_states:
                return False
            
            state_info = self.task_states[task_id]
            
            # Only allow cleanup of terminal states
            if state_info.current_state not in self.terminal_states:
                logger.warning(f"Cannot cleanup task {task_id} in non-terminal state {state_info.current_state.value}")
                return False
            
            del self.task_states[task_id]
            logger.debug(f"Cleaned up task {task_id}")
            return True
    
    def check_transitional_timeouts(self) -> List[str]:
        """Check for tasks stuck in transitional states and handle timeouts"""
        timed_out_tasks = []
        current_time = time.time()
        
        with self.lock:
            for task_id, state_info in self.task_states.items():
                if state_info.current_state in self.transitional_states:
                    timeout = state_info.metadata.get('transition_timeout', 0)
                    if timeout > 0 and current_time > timeout:
                        logger.warning(f"Task {task_id} timed out in transitional state {state_info.current_state.value}")
                        
                        # Force transition to failed state
                        self.transition_state(
                            task_id,
                            TaskState.FAILED,
                            reason="Transitional state timeout",
                            force=True
                        )
                        timed_out_tasks.append(task_id)
        
        return timed_out_tasks
    
    def register_state_callback(self, state: TaskState, callback: Callable) -> None:
        """Register callback for when tasks enter a specific state"""
        if state not in self.state_callbacks:
            self.state_callbacks[state] = []
        self.state_callbacks[state].append(callback)
    
    def register_transition_callback(self, callback: Callable[[str, TaskState, TaskState], None]) -> None:
        """Register callback for state transitions"""
        self.transition_callbacks.append(callback)
    
    def _trigger_callbacks(self, task_id: str, from_state: TaskState, to_state: TaskState) -> None:
        """Trigger registered callbacks"""
        # State-specific callbacks
        if to_state in self.state_callbacks:
            for callback in self.state_callbacks[to_state]:
                try:
                    callback(task_id)
                except Exception as e:
                    logger.error(f"Error in state callback for {task_id}: {e}")
        
        # Transition callbacks
        for callback in self.transition_callbacks:
            try:
                callback(task_id, from_state, to_state)
            except Exception as e:
                logger.error(f"Error in transition callback for {task_id}: {e}")
    
    def get_state_statistics(self) -> Dict[str, int]:
        """Get statistics about task states"""
        with self.lock:
            stats: Dict[str, Any] = {}
            for state_info in self.task_states.values():
                state_name = state_info.current_state.value
                stats[state_name] = stats.get(state_name, 0) + 1
            return stats
    
    def validate_state_consistency(self) -> List[str]:
        """Validate state consistency and return list of issues"""
        issues = []
        current_time = time.time()
        
        with self.lock:
            for task_id, state_info in self.task_states.items():
                # Check for tasks stuck in transitional states
                if (state_info.current_state in self.transitional_states and
                    current_time - state_info.state_changed_at > 300):  # 5 minutes
                    issues.append(f"Task {task_id} stuck in transitional state {state_info.current_state.value}")
                
                # Check for excessive retries
                if state_info.retry_count > 10:
                    issues.append(f"Task {task_id} has excessive retry count: {state_info.retry_count}")
                
                # Check for old failed tasks
                if (state_info.current_state == TaskState.FAILED and
                    current_time - state_info.state_changed_at > 86400):  # 24 hours
                    issues.append(f"Task {task_id} has been in failed state for over 24 hours")
        
        return issues


# Global task state manager instance
task_state_manager = TaskStateManager()

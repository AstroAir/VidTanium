"""
Enhanced Resource Management System for VidTanium

This module provides comprehensive resource lifecycle management including
automatic cleanup, leak detection, and resource monitoring capabilities.
Combines the original resource manager with enhanced features.
"""

import gc
import os
import psutil
import threading
import time
import weakref
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be managed"""
    DOWNLOAD_TASK = "download_task"
    TEMP_FILE = "temp_file"
    THREAD = "thread"
    NETWORK = "network"
    NETWORK_CONNECTION = "network_connection"
    CACHE_ENTRY = "cache_entry"
    UI_COMPONENT = "ui_component"
    FILE = "file"
    MEMORY = "memory"
    DATABASE = "database"


class ResourceState(Enum):
    """Resource lifecycle states"""
    CREATED = "created"
    ACTIVE = "active"
    IDLE = "idle"
    CLEANUP_PENDING = "cleanup_pending"
    CLEANED = "cleaned"
    LEAKED = "leaked"


@dataclass
class ResourceMetrics:
    """Metrics for resource usage tracking"""
    creation_time: float = field(default_factory=time.time)
    last_access_time: float = field(default_factory=time.time)
    access_count: int = 0
    memory_usage: int = 0  # bytes
    cleanup_attempts: int = 0
    state_changes: List[tuple] = field(default_factory=list)  # (timestamp, old_state, new_state)

    def record_access(self) -> None:
        """Record resource access"""
        self.last_access_time = time.time()
        self.access_count += 1

    def record_state_change(self, old_state: ResourceState, new_state: ResourceState) -> None:
        """Record state transition"""
        self.state_changes.append((time.time(), old_state, new_state))

    def get_age(self) -> float:
        """Get resource age in seconds"""
        return time.time() - self.creation_time

    def get_idle_time(self) -> float:
        """Get time since last access"""
        return time.time() - self.last_access_time


@dataclass
class ResourceInfo:
    """Enhanced information about a managed resource"""
    resource_id: str
    resource_type: ResourceType
    resource_ref: weakref.ref[Any]
    state: ResourceState = ResourceState.CREATED
    metrics: ResourceMetrics = field(default_factory=ResourceMetrics)
    cleanup_callback: Optional[Callable[[], None]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)

    # Backward compatibility properties
    @property
    def created_at(self) -> float:
        return self.metrics.creation_time

    @property
    def last_accessed(self) -> float:
        return self.metrics.last_access_time

    def is_alive(self) -> bool:
        """Check if the resource is still alive"""
        return self.resource_ref() is not None

    def should_cleanup(self, max_age: float, max_idle: float) -> bool:
        """Check if resource should be cleaned up based on age and idle time"""
        age = self.metrics.get_age()
        idle_time = self.metrics.get_idle_time()
        return age > max_age or idle_time > max_idle

    def transition_state(self, new_state: ResourceState) -> None:
        """Transition to new state"""
        old_state = self.state
        self.state = new_state
        self.metrics.record_state_change(old_state, new_state)
        logger.debug(f"Resource {self.resource_id} transitioned from {old_state.value} to {new_state.value}")


class LeakDetector:
    """Resource leak detection system"""

    def __init__(self, check_interval: float = 300.0) -> None:  # 5 minutes
        self.check_interval = check_interval
        self.leak_thresholds = {
            "age_threshold": 3600.0,  # 1 hour
            "idle_threshold": 1800.0,  # 30 minutes
            "access_threshold": 0,     # No access
            "memory_threshold": 100 * 1024 * 1024  # 100MB
        }
        self.detected_leaks: Dict[str, float] = {}  # resource_id -> detection_time

    def check_for_leaks(self, resources: Dict[str, ResourceInfo]) -> List[str]:
        """Check for potential resource leaks"""
        potential_leaks = []
        current_time = time.time()

        for resource_id, resource_info in resources.items():
            # Skip already cleaned resources
            if resource_info.state == ResourceState.CLEANED:
                continue

            # Check if resource is still alive
            if resource_info.resource_ref() is None:
                # Resource was garbage collected but not properly cleaned
                potential_leaks.append(resource_id)
                continue

            # Check age threshold
            if resource_info.metrics.get_age() > self.leak_thresholds["age_threshold"]:
                potential_leaks.append(resource_id)
                continue

            # Check idle threshold for active resources
            if (resource_info.state == ResourceState.ACTIVE and
                resource_info.metrics.get_idle_time() > self.leak_thresholds["idle_threshold"]):
                potential_leaks.append(resource_id)
                continue

            # Check memory usage
            if resource_info.metrics.memory_usage > self.leak_thresholds["memory_threshold"]:
                potential_leaks.append(resource_id)
                continue

        # Update detected leaks
        for resource_id in potential_leaks:
            if resource_id not in self.detected_leaks:
                self.detected_leaks[resource_id] = current_time
                logger.warning(f"Potential resource leak detected: {resource_id}")

        return potential_leaks


class ResourceManager:
    """Enhanced centralized automatic resource management system"""

    def __init__(self) -> None:
        self.resources: Dict[str, ResourceInfo] = {}
        self.cleanup_rules: Dict[ResourceType, Dict[str, float]] = {}
        self.cleanup_thread: Optional[threading.Thread] = None
        self.cleanup_interval = 30.0  # seconds
        self.running = False
        self.lock = threading.RLock()

        # Enhanced features
        self.leak_detector = LeakDetector()
        self.monitoring_active = False
        self.auto_cleanup_enabled = True
        self.max_idle_time = 1800.0  # 30 minutes
        self.max_resource_age = 3600.0  # 1 hour

        # Statistics
        self.stats = {
            "total_created": 0,
            "total_cleaned": 0,
            "total_leaked": 0,
            "cleanup_failures": 0,
            "memory_recovered": 0
        }

        # Default cleanup rules (max_age, max_idle in seconds)
        self._setup_default_cleanup_rules()
        
    def _setup_default_cleanup_rules(self) -> None:
        """Setup default cleanup rules for different resource types"""
        self.cleanup_rules = {
            ResourceType.DOWNLOAD_TASK: {"max_age": 3600, "max_idle": 1800},  # 1h age, 30m idle
            ResourceType.TEMP_FILE: {"max_age": 1800, "max_idle": 600},       # 30m age, 10m idle
            ResourceType.THREAD: {"max_age": 7200, "max_idle": 3600},         # 2h age, 1h idle
            ResourceType.NETWORK: {"max_age": 300, "max_idle": 60},           # 5m age, 1m idle
            ResourceType.NETWORK_CONNECTION: {"max_age": 300, "max_idle": 60}, # 5m age, 1m idle
            ResourceType.CACHE_ENTRY: {"max_age": 1800, "max_idle": 900},     # 30m age, 15m idle
            ResourceType.UI_COMPONENT: {"max_age": 7200, "max_idle": 3600},   # 2h age, 1h idle
            ResourceType.FILE: {"max_age": 1800, "max_idle": 600},            # 30m age, 10m idle
            ResourceType.MEMORY: {"max_age": 900, "max_idle": 300},           # 15m age, 5m idle
            ResourceType.DATABASE: {"max_age": 3600, "max_idle": 1800},       # 1h age, 30m idle
        }
    
    def start(self) -> None:
        """Start the automatic cleanup system"""
        if self.running:
            return

        self.running = True
        self.monitoring_active = True
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="ResourceCleanupThread",
            daemon=True
        )
        self.cleanup_thread.start()
        logger.info("Enhanced automatic resource cleanup system started")
    
    def stop(self) -> None:
        """Stop the automatic cleanup system"""
        self.running = False
        self.monitoring_active = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5.0)
        logger.info("Enhanced automatic resource cleanup system stopped")
    
    def register_resource(
        self,
        resource: Any,
        resource_type: ResourceType,
        resource_id: Optional[str] = None,
        cleanup_callback: Optional[Callable[[], None]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a resource for automatic management"""
        if resource_id is None:
            resource_id = f"{resource_type.value}_{id(resource)}_{int(time.time())}"

        with self.lock:
            # Create weak reference with cleanup callback
            def on_delete(ref) -> None:
                self._on_resource_deleted(resource_id)

            resource_ref = weakref.ref(resource, on_delete)

            # Estimate memory usage
            memory_usage = self._estimate_memory_usage(resource)

            # Create enhanced resource info with backward compatibility
            resource_info = ResourceInfo(
                resource_id=resource_id,
                resource_type=resource_type,
                resource_ref=resource_ref,
                cleanup_callback=cleanup_callback,
                metadata=metadata or {}
            )

            resource_info.metrics.memory_usage = memory_usage
            resource_info.transition_state(ResourceState.ACTIVE)

            self.resources[resource_id] = resource_info
            self.stats["total_created"] += 1

            logger.debug(f"Registered resource: {resource_id} ({resource_type.value})")

        return resource_id
    
    def unregister_resource(self, resource_id: str) -> bool:
        """Unregister a resource from management"""
        with self.lock:
            if resource_id in self.resources:
                resource_info = self.resources.pop(resource_id)
                logger.debug(f"Unregistered resource: {resource_id}")
                return True
            return False
    
    def access_resource(self, resource_id: str) -> Optional[Any]:
        """Access a resource and update metrics"""
        with self.lock:
            if resource_id not in self.resources:
                return None

            resource_info = self.resources[resource_id]
            resource = resource_info.resource_ref()

            if resource is None:
                # Resource was garbage collected
                self._mark_as_leaked(resource_id)
                return None

            resource_info.metrics.record_access()
            if resource_info.state == ResourceState.IDLE:
                resource_info.transition_state(ResourceState.ACTIVE)

            return resource
    
    def force_cleanup_resource(self, resource_id: str) -> bool:
        """Force cleanup of a specific resource"""
        with self.lock:
            if resource_id not in self.resources:
                return False

            resource_info = self.resources[resource_id]
            success = self._cleanup_resource(resource_info)

            if success:
                self.resources.pop(resource_id, None)

            return success

    def cleanup_resource_enhanced(self, resource_id: str, force: bool = False) -> bool:
        """Enhanced cleanup with dependency checking and statistics"""
        with self.lock:
            if resource_id not in self.resources:
                return False

            resource_info = self.resources[resource_id]

            # Check dependencies
            if not force and resource_info.dependents:
                logger.warning(f"Cannot cleanup resource {resource_id}: has dependents {resource_info.dependents}")
                return False

            # Attempt cleanup
            success = self._cleanup_resource(resource_info)

            if success:
                resource_info.transition_state(ResourceState.CLEANED)
                self.stats["total_cleaned"] += 1
                self.stats["memory_recovered"] += resource_info.metrics.memory_usage

                # Clean up dependency relationships
                for dep_id in resource_info.dependencies:
                    if dep_id in self.resources:
                        self.resources[dep_id].dependents.discard(resource_id)

                self.resources.pop(resource_id)
                logger.debug(f"Successfully cleaned up resource: {resource_id}")
            else:
                self.stats["cleanup_failures"] += 1
                resource_info.metrics.cleanup_attempts += 1
                logger.error(f"Failed to cleanup resource: {resource_id}")

            return success
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get statistics about managed resources"""
        with self.lock:
            stats: Dict[str, Any] = {
                "total_resources": len(self.resources),
                "by_type": {},
                "memory_usage": 0
            }

            for resource_info in self.resources.values():
                resource_type = resource_info.resource_type.value
                by_type_dict = stats["by_type"]
                if resource_type not in by_type_dict:
                    by_type_dict[resource_type] = 0
                by_type_dict[resource_type] += 1

                # Estimate memory usage (simplified)
                if resource_info.is_alive():
                    try:
                        resource = resource_info.resource_ref()
                        if hasattr(resource, '__sizeof__'):
                            stats["memory_usage"] += resource.__sizeof__()
                    except Exception:
                        pass

            return stats

    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics with enhanced metrics"""
        with self.lock:
            active_resources = sum(1 for r in self.resources.values()
                                 if r.state == ResourceState.ACTIVE)
            idle_resources = sum(1 for r in self.resources.values()
                               if r.state == ResourceState.IDLE)
            leaked_resources = sum(1 for r in self.resources.values()
                                 if r.state == ResourceState.LEAKED)

            total_memory = sum(r.metrics.memory_usage for r in self.resources.values()
                             if r.state in [ResourceState.ACTIVE, ResourceState.IDLE])

            return {
                "total_resources": len(self.resources),
                "active_resources": active_resources,
                "idle_resources": idle_resources,
                "leaked_resources": leaked_resources,
                "total_memory_mb": total_memory / (1024 * 1024),
                "stats": self.stats.copy(),
                "leak_report": self.leak_detector.check_for_leaks(self.resources)
            }

    def _estimate_memory_usage(self, resource: Any) -> int:
        """Estimate memory usage of a resource"""
        try:
            import sys
            return sys.getsizeof(resource)
        except:
            return 0

    def _mark_as_leaked(self, resource_id: str) -> None:
        """Mark resource as leaked"""
        if resource_id in self.resources:
            self.resources[resource_id].transition_state(ResourceState.LEAKED)
            self.stats["total_leaked"] += 1
            logger.warning(f"Resource leaked: {resource_id}")

    def _cleanup_loop(self) -> None:
        """Enhanced cleanup loop with leak detection"""
        while self.running:
            try:
                self._perform_cleanup_cycle()

                # Enhanced leak detection
                if self.monitoring_active:
                    self._check_for_leaks()

                time.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Error in resource cleanup loop: {e}", exc_info=True)
                time.sleep(self.cleanup_interval)

    def _check_for_leaks(self) -> None:
        """Check for resource leaks using enhanced detection"""
        with self.lock:
            potential_leaks = self.leak_detector.check_for_leaks(self.resources)

            if potential_leaks:
                logger.warning(f"Detected {len(potential_leaks)} potential resource leaks")

                # Force cleanup of leaked resources
                for resource_id in potential_leaks:
                    if resource_id in self.resources:
                        self.cleanup_resource_enhanced(resource_id, force=True)

    def _perform_cleanup_cycle(self) -> None:
        """Perform one cleanup cycle"""
        resources_to_cleanup = []
        
        with self.lock:
            for resource_id, resource_info in list(self.resources.items()):
                # Check if resource is still alive
                if not resource_info.is_alive():
                    resources_to_cleanup.append(resource_id)
                    continue
                
                # Check cleanup rules
                rules = self.cleanup_rules.get(resource_info.resource_type, {})
                max_age = rules.get("max_age", float('inf'))
                max_idle = rules.get("max_idle", float('inf'))
                
                if resource_info.should_cleanup(max_age, max_idle):
                    resources_to_cleanup.append(resource_id)
        
        # Cleanup resources outside the lock to avoid deadlocks
        cleaned_count = 0
        for resource_id in resources_to_cleanup:
            if self.force_cleanup_resource(resource_id):
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} resources")
            
        # Force garbage collection periodically
        if cleaned_count > 0:
            gc.collect()
    
    def _cleanup_resource(self, resource_info: ResourceInfo) -> bool:
        """Cleanup a specific resource"""
        try:
            # Call custom cleanup callback if provided
            if resource_info.cleanup_callback:
                resource_info.cleanup_callback()
            
            # Perform type-specific cleanup
            self._perform_type_specific_cleanup(resource_info)
            
            logger.debug(f"Cleaned up resource: {resource_info.resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up resource {resource_info.resource_id}: {e}")
            return False
    
    def _perform_type_specific_cleanup(self, resource_info: ResourceInfo) -> None:
        """Perform cleanup specific to resource type"""
        resource = resource_info.resource_ref()
        if resource is None:
            return
        
        if resource_info.resource_type == ResourceType.TEMP_FILE:
            # Clean up temporary files
            if isinstance(resource, (str, Path)):
                file_path = Path(resource)
                if file_path.exists():
                    try:
                        file_path.unlink()
                        logger.debug(f"Deleted temp file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file_path}: {e}")
        
        elif resource_info.resource_type == ResourceType.THREAD:
            # Clean up threads
            if hasattr(resource, 'join') and hasattr(resource, 'is_alive'):
                if resource.is_alive():
                    try:
                        resource.join(timeout=1.0)
                    except Exception as e:
                        logger.warning(f"Failed to join thread: {e}")
        
        elif resource_info.resource_type == ResourceType.NETWORK_CONNECTION:
            # Clean up network connections
            if hasattr(resource, 'close'):
                try:
                    resource.close()
                except Exception as e:
                    logger.warning(f"Failed to close connection: {e}")
    
    def _on_resource_deleted(self, resource_id: str) -> None:
        """Enhanced callback when a resource is garbage collected"""
        with self.lock:
            if resource_id in self.resources:
                resource_info = self.resources[resource_id]
                if resource_info.state not in [ResourceState.CLEANED, ResourceState.CLEANUP_PENDING]:
                    self._mark_as_leaked(resource_id)
                self.resources.pop(resource_id, None)
        logger.debug(f"Resource garbage collected: {resource_id}")

    def cleanup_all_resources(self) -> None:
        """Clean up all resources"""
        with self.lock:
            resource_ids = list(self.resources.keys())

        for resource_id in resource_ids:
            self.cleanup_resource_enhanced(resource_id, force=True)

        logger.info(f"Cleaned up all {len(resource_ids)} resources")

    def start_monitoring(self) -> None:
        """Start enhanced monitoring (alias for start)"""
        self.start()

    def stop_monitoring(self) -> None:
        """Stop enhanced monitoring (alias for stop)"""
        self.stop()


# Global resource manager instance
resource_manager = ResourceManager()


def register_for_cleanup(
    resource: Any,
    resource_type: ResourceType,
    cleanup_callback: Optional[Callable[[], None]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Convenience function to register a resource for cleanup"""
    return resource_manager.register_resource(
        resource, resource_type, cleanup_callback=cleanup_callback, metadata=metadata
    )


def cleanup_temp_file(file_path: Path) -> str:
    """Convenience function to register a temporary file for cleanup"""
    return register_for_cleanup(
        file_path,
        ResourceType.TEMP_FILE,
        metadata={"path": str(file_path)}
    )

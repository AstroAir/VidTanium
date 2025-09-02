"""
Enhanced Component Registration System for VidTanium
Eliminates duplicate component registration patterns across GUI systems
"""

import weakref
from typing import Dict, List, Set, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtCore import QObject, Signal
from loguru import logger


class ComponentType(Enum):
    """Types of components that can be registered"""
    WIDGET = "widget"
    DIALOG = "dialog"
    WINDOW = "window"
    MANAGER = "manager"
    SERVICE = "service"
    THEME_COMPONENT = "theme_component"
    EVENT_HANDLER = "event_handler"


@dataclass
class ComponentInfo:
    """Information about a registered component"""
    component_id: str
    component_type: ComponentType
    component_ref: weakref.ref[Any]
    registration_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    initialization_callbacks: List[Callable[[], None]] = field(default_factory=list)
    cleanup_callbacks: List[Callable[[], None]] = field(default_factory=list)
    
    def is_alive(self) -> bool:
        """Check if the component is still alive"""
        return self.component_ref() is not None
    
    def get_component(self) -> Optional[Any]:
        """Get the actual component instance"""
        return self.component_ref()


class ComponentRegistry(QObject):
    """Enhanced registry for all GUI components to eliminate registration redundancy"""
    
    # Signals
    component_registered = Signal(str, str)  # component_id, component_type
    component_unregistered = Signal(str)     # component_id
    component_initialized = Signal(str)      # component_id
    
    def __init__(self) -> None:
        super().__init__()

        # Component storage
        self.components: Dict[str, ComponentInfo] = {}
        self.components_by_type: Dict[ComponentType, Set[str]] = {
            comp_type: set() for comp_type in ComponentType
        }

        # Registration patterns and factories
        self.registration_patterns: Dict[str, Callable[[Any], Optional[str]]] = {}
        self.component_factories: Dict[ComponentType, List[Callable[..., Any]]] = {
            comp_type: [] for comp_type in ComponentType
        }
        
        # Dependency management
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.initialization_order: List[str] = []
        
        # Auto-registration for common patterns
        self._setup_auto_registration_patterns()
    
    def _setup_auto_registration_patterns(self):
        """Setup automatic registration patterns for common component types"""
        # Theme component pattern
        self.register_pattern(
            "theme_component",
            lambda comp: self.register_component(
                comp, ComponentType.THEME_COMPONENT,
                auto_theme_registration=True
            )
        )
        
        # Event handler pattern
        self.register_pattern(
            "event_handler",
            lambda comp: self.register_component(
                comp, ComponentType.EVENT_HANDLER,
                auto_event_registration=True
            )
        )
        
        # Manager pattern
        self.register_pattern(
            "manager",
            lambda comp: self.register_component(
                comp, ComponentType.MANAGER,
                auto_resource_management=True
            )
        )
    
    def register_component(
        self,
        component: Any,
        component_type: ComponentType,
        component_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        initialization_callback: Optional[Callable[[], None]] = None,
        cleanup_callback: Optional[Callable[[], None]] = None,
        **kwargs
    ) -> str:
        """Register a component with the enhanced registry"""
        
        # Generate ID if not provided
        if component_id is None:
            component_id = f"{component_type.value}_{component.__class__.__name__}_{id(component)}"
        
        # Check for duplicate registration
        if component_id in self.components:
            logger.warning(f"Component {component_id} already registered, updating...")
            self.unregister_component(component_id)
        
        # Create component info
        import time
        component_info = ComponentInfo(
            component_id=component_id,
            component_type=component_type,
            component_ref=weakref.ref(component, lambda ref: self._on_component_deleted(component_id)),
            registration_time=time.time(),
            metadata=metadata or {},
            dependencies=dependencies or []
        )
        
        # Add callbacks
        if initialization_callback:
            component_info.initialization_callbacks.append(initialization_callback)
        if cleanup_callback:
            component_info.cleanup_callbacks.append(cleanup_callback)
        
        # Store component
        self.components[component_id] = component_info
        self.components_by_type[component_type].add(component_id)
        
        # Handle dependencies
        if dependencies:
            self.dependency_graph[component_id] = set(dependencies)
            self._update_initialization_order()
        
        # Apply auto-registration features
        self._apply_auto_registration_features(component, component_type, **kwargs)
        
        # Emit signal
        self.component_registered.emit(component_id, component_type.value)
        
        logger.debug(f"Registered component: {component_id} ({component_type.value})")
        return component_id
    
    def unregister_component(self, component_id: str) -> bool:
        """Unregister a component from the registry"""
        if component_id not in self.components:
            return False
        
        component_info = self.components[component_id]
        
        # Call cleanup callbacks
        for callback in component_info.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback for {component_id}: {e}")
        
        # Remove from storage
        self.components.pop(component_id)
        self.components_by_type[component_info.component_type].discard(component_id)
        self.dependency_graph.pop(component_id, None)
        
        # Update initialization order
        if component_id in self.initialization_order:
            self.initialization_order.remove(component_id)
        
        # Emit signal
        self.component_unregistered.emit(component_id)
        
        logger.debug(f"Unregistered component: {component_id}")
        return True
    
    def get_component(self, component_id: str) -> Optional[Any]:
        """Get a component by ID"""
        component_info = self.components.get(component_id)
        if component_info and component_info.is_alive():
            return component_info.get_component()
        return None
    
    def get_components_by_type(self, component_type: ComponentType) -> List[Any]:
        """Get all components of a specific type"""
        components = []
        for component_id in self.components_by_type[component_type]:
            component = self.get_component(component_id)
            if component is not None:
                components.append(component)
        return components
    
    def register_pattern(self, pattern_name: str, registration_func: Callable[[Any], Optional[str]]) -> None:
        """Register a reusable registration pattern"""
        self.registration_patterns[pattern_name] = registration_func
        logger.debug(f"Registered pattern: {pattern_name}")
    
    def apply_pattern(self, pattern_name: str, component: Any) -> Optional[str]:
        """Apply a registration pattern to a component"""
        if pattern_name in self.registration_patterns:
            try:
                return self.registration_patterns[pattern_name](component)
            except Exception as e:
                logger.error(f"Error applying pattern {pattern_name}: {e}")
        return None
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the component registry"""
        stats: Dict[str, Any] = {
            "total_components": len(self.components),
            "by_type": {},
            "alive_components": 0,
            "dead_references": 0
        }

        for component_type, component_ids in self.components_by_type.items():
            alive_count = 0
            for component_id in component_ids:
                component_info = self.components.get(component_id)
                if component_info and component_info.is_alive():
                    alive_count += 1
                    stats["alive_components"] = stats["alive_components"] + 1
                else:
                    stats["dead_references"] = stats["dead_references"] + 1

            by_type_dict = stats["by_type"]
            by_type_dict[component_type.value] = {
                "total": len(component_ids),
                "alive": alive_count
            }

        return stats
    
    def _apply_auto_registration_features(self, component: Any, component_type: ComponentType, **kwargs):
        """Apply automatic registration features based on component type and kwargs"""
        
        # Auto theme registration
        if kwargs.get("auto_theme_registration", False):
            try:
                from .enhanced_theme_system import get_theme_system
                get_theme_system().register_component(component)
            except Exception as e:
                logger.warning(f"Auto theme registration failed: {e}")
        
        # Auto event registration
        if kwargs.get("auto_event_registration", False):
            try:
                from .enhanced_event_system import get_event_system
                # Register common event handlers if component has them
                if hasattr(component, 'handle_event'):
                    get_event_system().register_handler(
                        f"{component.__class__.__name__}_event",
                        component.handle_event
                    )
            except Exception as e:
                logger.warning(f"Auto event registration failed: {e}")
        
        # Auto resource management
        if kwargs.get("auto_resource_management", False):
            try:
                from ..core.resource_manager import register_for_cleanup, ResourceType
                register_for_cleanup(component, ResourceType.UI_COMPONENT)
            except Exception as e:
                logger.warning(f"Auto resource management registration failed: {e}")
    
    def _update_initialization_order(self):
        """Update the component initialization order based on dependencies"""
        # Simple topological sort for dependency resolution
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component_id: str):
            if component_id in temp_visited:
                logger.warning(f"Circular dependency detected involving {component_id}")
                return
            if component_id in visited:
                return
            
            temp_visited.add(component_id)
            
            # Visit dependencies first
            for dep_id in self.dependency_graph.get(component_id, []):
                if dep_id in self.components:
                    visit(dep_id)
            
            temp_visited.remove(component_id)
            visited.add(component_id)
            order.append(component_id)
        
        # Visit all components
        for component_id in self.components:
            if component_id not in visited:
                visit(component_id)
        
        self.initialization_order = order
    
    def _on_component_deleted(self, component_id: str):
        """Handle component deletion via weak reference callback"""
        if component_id in self.components:
            self.unregister_component(component_id)


# Global component registry instance
_component_registry: Optional[ComponentRegistry] = None


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry instance"""
    global _component_registry
    if _component_registry is None:
        _component_registry = ComponentRegistry()
    return _component_registry


def register_component(component: Any, component_type: ComponentType, **kwargs) -> str:
    """Convenience function to register a component"""
    return get_component_registry().register_component(component, component_type, **kwargs)


def apply_registration_pattern(pattern_name: str, component: Any) -> Optional[str]:
    """Convenience function to apply a registration pattern"""
    return get_component_registry().apply_pattern(pattern_name, component)

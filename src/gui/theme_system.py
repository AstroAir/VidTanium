"""
Theme Management System for VidTanium
Consolidates theme management logic to reduce duplication across components
"""

from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget
from qfluentwidgets import setTheme, Theme, SystemThemeListener, qconfig
from loguru import logger
import weakref


class ThemeMode(Enum):
    """Available theme modes"""
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


@dataclass
class ThemeConfiguration:
    """Theme configuration settings"""
    mode: ThemeMode = ThemeMode.SYSTEM
    accent_color: str = "#0078d4"
    animations_enabled: bool = True
    custom_styles: Dict[str, str] = field(default_factory=dict)
    component_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ThemeableComponent:
    """Interface for components that can be themed"""
    
    def apply_theme(self, config: ThemeConfiguration) -> None:
        """Apply theme configuration to this component"""
        raise NotImplementedError
    
    def get_theme_requirements(self) -> Dict[str, Any]:
        """Get theme requirements for this component"""
        return {}


class ThemeSystem(QObject):
    """Theme system that consolidates all theme management logic"""
    
    # Signals
    theme_changed = Signal(str)  # theme_mode
    accent_changed = Signal(str)  # accent_color
    theme_applied = Signal(ThemeConfiguration)
    
    def __init__(self, settings_provider: Any = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.settings = settings_provider
        self._current_config = ThemeConfiguration()

        # Component management
        self._registered_components: Set[weakref.ref[Any]] = set()
        self._component_callbacks: Dict[str, List[Callable[[ThemeConfiguration], None]]] = {}
        
        # Theme state management
        self._theme_listener: Optional[SystemThemeListener] = None
        self._applying_theme = False
        self._theme_cache: Dict[str, Any] = {}
        
        # Batch update management
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._apply_pending_updates)
        self._update_timer.setSingleShot(True)
        self._pending_updates: Set[str] = set()
        
        # Load initial configuration
        self._load_theme_configuration()

    def _load_theme_configuration(self) -> None:
        """Load theme configuration from settings"""
        if not self.settings:
            return
            
        try:
            theme_mode = self.settings.get("general", "theme", "system")
            accent_color = self.settings.get("ui", "accent_color", "#0078d4")
            animations_enabled = self.settings.get("ui", "animations_enabled", True)
            
            self._current_config = ThemeConfiguration(
                mode=ThemeMode(theme_mode),
                accent_color=accent_color,
                animations_enabled=animations_enabled
            )
            
        except Exception as e:
            logger.warning(f"Error loading theme configuration: {e}")
            self._current_config = ThemeConfiguration()
    
    def register_component(self, component: Any, component_id: Optional[str] = None) -> str:
        """Register a component for theme management"""
        if component_id is None:
            component_id = f"{component.__class__.__name__}_{id(component)}"
        
        # Create weak reference to avoid circular references
        component_ref = weakref.ref(component, lambda ref: self._on_component_deleted(component_id))
        self._registered_components.add(component_ref)
        
        # Apply current theme to new component
        self._apply_theme_to_component(component, self._current_config)
        
        logger.debug(f"Registered component for theming: {component_id}")
        return component_id
    
    def set_theme_mode(self, mode: ThemeMode, animate: bool = True) -> bool:
        """Set the theme mode with optional animation"""
        if self._applying_theme:
            return False
            
        try:
            old_mode = self._current_config.mode
            self._current_config.mode = mode
            
            # Clean up existing listener
            self._cleanup_theme_listener()
            
            # Apply theme
            success = self._apply_theme_mode(mode, animate)
            
            if success:
                # Save to settings
                if self.settings:
                    self.settings.set("general", "theme", mode.value)
                    self.settings.save_settings()
                
                # Emit signals
                self.theme_changed.emit(mode.value)
                self.theme_applied.emit(self._current_config)
                
                logger.info(f"Theme mode changed: {old_mode.value} -> {mode.value}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error setting theme mode '{mode.value}': {e}", exc_info=True)
            return False
    
    def get_current_configuration(self) -> ThemeConfiguration:
        """Get the current theme configuration"""
        return self._current_config
    
    def apply_theme_to_all_components(self, force: bool = False) -> None:
        """Apply current theme to all registered components"""
        if self._applying_theme and not force:
            return
            
        self._applying_theme = True
        try:
            # Clean up dead references
            self._cleanup_dead_references()
            
            # Apply to all live components
            for component_ref in list(self._registered_components):
                component = component_ref()
                if component is not None:
                    self._apply_theme_to_component(component, self._current_config)
            
            # Call registered callbacks
            for callbacks in self._component_callbacks.values():
                for callback in callbacks:
                    try:
                        callback(self._current_config)
                    except Exception as e:
                        logger.warning(f"Error in theme callback: {e}")
                        
        finally:
            self._applying_theme = False
    
    def _apply_theme_mode(self, mode: ThemeMode, animate: bool) -> bool:
        """Apply the theme mode to the application"""
        try:
            if mode == ThemeMode.SYSTEM:
                setTheme(Theme.AUTO)
                self._theme_listener = SystemThemeListener(self.parent())
                self._theme_listener.start()
                
            elif mode == ThemeMode.LIGHT:
                setTheme(Theme.LIGHT)
                
            elif mode == ThemeMode.DARK:
                setTheme(Theme.DARK)
            
            # Save QFluentWidgets configuration
            qconfig.save()
            
            # Apply to all components
            if not animate:
                self.apply_theme_to_all_components()
            else:
                # Schedule delayed update for animation
                self._schedule_component_update()
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying theme mode '{mode.value}': {e}")
            return False
    
    def _apply_theme_to_component(self, component: Any, config: ThemeConfiguration) -> None:
        """Apply theme configuration to a specific component"""
        try:
            # Check if component implements ThemeableComponent interface
            if isinstance(component, ThemeableComponent):
                component.apply_theme(config)
            
            # Apply standard QWidget theming if applicable
            elif isinstance(component, QWidget):
                self._apply_widget_theme(component, config)
                
        except Exception as e:
            logger.warning(f"Error applying theme to component {type(component).__name__}: {e}")
    
    def _apply_widget_theme(self, widget: QWidget, config: ThemeConfiguration) -> None:
        """Apply theme to a standard QWidget"""
        # Basic theme application for QWidget
        pass
    
    def _schedule_component_update(self) -> None:
        """Schedule a batched component update"""
        if not self._update_timer.isActive():
            self._update_timer.start(50)  # 50ms delay for batching
    
    def _apply_pending_updates(self) -> None:
        """Apply pending theme updates"""
        if self._pending_updates:
            self.apply_theme_to_all_components()
            self._pending_updates.clear()
    
    def _cleanup_theme_listener(self) -> None:
        """Clean up the current theme listener"""
        if self._theme_listener:
            try:
                self._theme_listener.terminate()
                self._theme_listener.deleteLater()
            except Exception as e:
                logger.warning(f"Error cleaning up theme listener: {e}")
            finally:
                self._theme_listener = None
    
    def _cleanup_dead_references(self) -> None:
        """Clean up dead weak references"""
        dead_refs = set()
        for component_ref in self._registered_components:
            if component_ref() is None:
                dead_refs.add(component_ref)
        
        self._registered_components -= dead_refs
    
    def _on_component_deleted(self, component_id: str) -> None:
        """Handle component deletion"""
        self._component_callbacks.pop(component_id, None)
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._cleanup_theme_listener()
            self._update_timer.stop()
            self._registered_components.clear()
            self._component_callbacks.clear()
            self._theme_cache.clear()
        except Exception as e:
            logger.error(f"Error during theme system cleanup: {e}")


# Global theme system instance
_theme_system: Optional[ThemeSystem] = None


def get_theme_system() -> ThemeSystem:
    """Get the global theme system instance"""
    global _theme_system
    if _theme_system is None:
        _theme_system = ThemeSystem()
    return _theme_system


def register_for_theming(component: Any, component_id: Optional[str] = None) -> str:
    """Convenience function to register a component for theming"""
    return get_theme_system().register_component(component, component_id)

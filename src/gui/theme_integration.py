"""
Comprehensive Theme Integration Module for VidTanium
Provides centralized theme management leveraging QFluentWidgets theming system
"""
from typing import Dict, List, Optional, Any, TYPE_CHECKING, cast
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal, QTimer
from qfluentwidgets import setTheme, Theme, isDarkTheme, setThemeColor
from loguru import logger

if TYPE_CHECKING:
    from .theme_manager import ThemeManager
    from .main_window import MainWindow


class QFluentWidgetsThemeIntegration(QObject):
    """QFluentWidgets-focused theme integration manager for VidTanium"""
    
    # Signals
    theme_applied = Signal(str)  # Theme name
    accent_changed = Signal(str)  # Accent color
    qfluent_theme_updated = Signal()
    
    def __init__(self, main_window: "MainWindow", theme_manager: "ThemeManager") -> None:
        super().__init__()
        self.main_window = main_window
        self.theme_manager = theme_manager
        self._registered_qfluent_components: List[QWidget] = []
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._apply_qfluent_updates)
        self._update_timer.setSingleShot(True)
        
        # Track QFluentWidgets theme state
        self._current_qfluent_theme: Optional[str] = None
        self._current_accent: Optional[str] = None
        
        self._setup_qfluent_theming()
    
    def _setup_qfluent_theming(self) -> None:
        """Setup QFluentWidgets theming integration"""
        try:
            # Set QFluentWidgets theme based on current theme
            if isDarkTheme():
                setTheme(Theme.DARK)
                self._current_qfluent_theme = "dark"
            else:
                setTheme(Theme.LIGHT)
                self._current_qfluent_theme = "light"
            
            # Set accent color if available
            if self.theme_manager:
                accent = self.theme_manager.get_current_accent()
                accent_color = self.theme_manager.ACCENT_COLORS.get(accent, '#0078D4')
                setThemeColor(accent_color)
                self._current_accent = accent_color
                
            logger.info(f"QFluentWidgets theme initialized: {self._current_qfluent_theme}")
            
        except Exception as e:
            logger.warning(f"Could not initialize QFluentWidgets theming: {e}")
    
    def register_qfluent_component(self, component: QWidget, component_type: str = "qfluent") -> None:
        """Register a QFluentWidgets component for theme updates"""
        if component not in self._registered_qfluent_components:
            self._registered_qfluent_components.append(component)
            logger.debug(f"Registered QFluentWidgets {component_type} component")
            
            # QFluentWidgets components automatically inherit theme
            # No manual styling needed in most cases
    
    def unregister_qfluent_component(self, component: QWidget) -> None:
        """Unregister a QFluentWidgets component"""
        if component in self._registered_qfluent_components:
            self._registered_qfluent_components.remove(component)
    
    def apply_qfluent_theme(self, theme_name: Optional[str] = None, accent_color: Optional[str] = None) -> None:
        """Apply QFluentWidgets theme globally"""
        try:
            # Update QFluentWidgets theme
            if theme_name:
                if theme_name.lower() in ['dark', 'black']:
                    setTheme(Theme.DARK)
                    self._current_qfluent_theme = "dark"
                else:
                    setTheme(Theme.LIGHT)
                    self._current_qfluent_theme = "light"
            
            # Update accent color
            if accent_color:
                setThemeColor(accent_color)
                self._current_accent = accent_color
            elif self.theme_manager:
                accent = self.theme_manager.get_current_accent()
                accent_color = self.theme_manager.ACCENT_COLORS.get(accent, '#0078D4')
                setThemeColor(accent_color)
                self._current_accent = accent_color
            
            # Batch update registered components
            self._update_timer.start(50)  # Small delay for QFluentWidgets to process
            
        except Exception as e:
            logger.error(f"Error applying QFluentWidgets theme: {e}")
    
    def _apply_qfluent_updates(self) -> None:
        """Apply pending QFluentWidgets theme updates"""
        try:
            # QFluentWidgets components automatically update with setTheme()
            # We just need to trigger any custom updates for enhanced components
            
            self._update_enhanced_components()
            
            # Emit global update signal
            self.qfluent_theme_updated.emit()
            
            logger.debug("QFluentWidgets theme updates applied")
            
        except Exception as e:
            logger.error(f"Error applying QFluentWidgets updates: {e}")
    
    def _update_enhanced_components(self) -> None:
        """Update enhanced components that have custom theming"""
        try:
            # Update main window enhanced components
            if hasattr(self.main_window, 'dashboard_interface'):
                dashboard = self.main_window.dashboard_interface
                if hasattr(dashboard, 'update_theme'):
                    dashboard.update_theme(self.theme_manager)
            
            # Update other enhanced components that need custom theming
            for component in self._registered_qfluent_components[:]:
                try:
                    if hasattr(component, 'update_theme'):
                        component.update_theme(self.theme_manager)
                except Exception as e:
                    logger.debug(f"Could not update enhanced component: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating enhanced components: {e}")
    
    def on_system_theme_changed(self) -> None:
        """Handle system theme changes"""
        try:
            # Detect system theme and apply accordingly
            if isDarkTheme():
                self.apply_qfluent_theme("dark")
                self.theme_applied.emit("dark")
            else:
                self.apply_qfluent_theme("light")
                self.theme_applied.emit("light")
                
        except Exception as e:
            logger.error(f"Error handling system theme change: {e}")
    
    def get_current_qfluent_theme(self) -> str:
        """Get current QFluentWidgets theme"""
        return self._current_qfluent_theme or ("dark" if isDarkTheme() else "light")
    
    def get_component_count(self) -> int:
        """Get count of registered QFluentWidgets components"""
        return len(self._registered_qfluent_components)
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._update_timer.stop()
            self._registered_qfluent_components.clear()
        except Exception as e:
            logger.error(f"Error cleaning up QFluentWidgets theme integration: {e}")


class QFluentWidgetsComponentMixin:
    """Mixin for components using QFluentWidgets that want enhanced theming"""
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._qfluent_integration_registered = False
    
    def register_for_qfluent_theming(self, integration: QFluentWidgetsThemeIntegration) -> None:
        """Register for QFluentWidgets theme updates"""
        if not self._qfluent_integration_registered:
            integration.register_qfluent_component(cast(QWidget, self), self.__class__.__name__)
            self._qfluent_integration_registered = True
    
    def update_qfluent_theme(self, theme_manager: "ThemeManager") -> None:
        """Override for custom theming on top of QFluentWidgets"""
        # Most QFluentWidgets components don't need custom theming
        # Override only when you need additional styling
        pass


# QFluentWidgets helpers
def apply_qfluent_theme_to_app(theme_name: str = "auto", accent_color: Optional[str] = None) -> None:
    """Apply QFluentWidgets theme to entire application"""
    try:
        if theme_name == "auto":
            theme = Theme.DARK if isDarkTheme() else Theme.LIGHT
        elif theme_name.lower() in ['dark', 'black']:
            theme = Theme.DARK
        else:
            theme = Theme.LIGHT
        
        setTheme(theme)
        
        if accent_color:
            setThemeColor(accent_color)
        
        logger.info(f"Applied QFluentWidgets theme: {theme.name}")
        
    except Exception as e:
        logger.error(f"Error applying QFluentWidgets theme: {e}")


def create_qfluent_component(component_class, *args, **kwargs) -> None:
    """Factory for creating QFluentWidgets components with automatic theming"""
    try:
        component = component_class(*args, **kwargs)
        # QFluentWidgets components automatically inherit the current theme
        return component
    except Exception as e:
        logger.error(f"Error creating QFluentWidgets component: {e}")
        # Fallback to basic component creation
        return component_class(*args, **kwargs)


# Legacy compatibility
ThemeIntegrationManager = QFluentWidgetsThemeIntegration
ComponentThemeMixin = QFluentWidgetsComponentMixin
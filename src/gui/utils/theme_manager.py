"""
Theme Manager for VidTanium
Advanced theme management with smooth transitions and custom themes
"""

from typing import Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QColor, QPalette

from qfluentwidgets import (
    Theme, setTheme, isDarkTheme, SystemThemeListener,
    qconfig, ConfigItem, OptionsConfigItem
)

from .design_system import DesignSystem, EnhancedDesignSystem


class ThemeManager(QObject):
    """Theme manager with smooth transitions and custom themes"""
    
    theme_changed = Signal(str)
    transition_finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme: str = "auto"
        self.custom_themes: Dict[str, Dict[str, str]] = {}
        self.transition_duration = 300
        self.widgets_to_update: list = []
        
        self._setup_system_listener()
        self._register_custom_themes()
    
    def _setup_system_listener(self):
        """Setup system theme listener"""
        self.system_listener = SystemThemeListener(self)
        # Note: SystemThemeListener doesn't have themeChanged signal in current version
        # We'll handle theme changes through qconfig instead
    
    def _register_custom_themes(self):
        """Register custom theme variants"""
        # Midnight Blue Theme
        self.custom_themes["midnight"] = {
            'primary': '#1E3A8A',
            'accent_blue': '#3B82F6',
            'accent_purple': '#6366F1',
            'surface_dark': '#0F172A',
            'surface_secondary_dark': '#1E293B',
            'surface_tertiary_dark': '#334155',
            'text_primary_dark': '#F1F5F9',
            'text_secondary_dark': '#CBD5E1',
        }
        
        # Forest Green Theme
        self.custom_themes["forest"] = {
            'primary': '#059669',
            'accent_blue': '#0891B2',
            'accent_purple': '#7C3AED',
            'surface_dark': '#064E3B',
            'surface_secondary_dark': '#065F46',
            'surface_tertiary_dark': '#047857',
            'text_primary_dark': '#ECFDF5',
            'text_secondary_dark': '#A7F3D0',
        }
        
        # Sunset Orange Theme
        self.custom_themes["sunset"] = {
            'primary': '#EA580C',
            'accent_blue': '#0EA5E9',
            'accent_purple': '#A855F7',
            'surface_dark': '#7C2D12',
            'surface_secondary_dark': '#9A3412',
            'surface_tertiary_dark': '#C2410C',
            'text_primary_dark': '#FFF7ED',
            'text_secondary_dark': '#FDBA74',
        }
    
    def register_widget(self, widget: QWidget):
        """Register widget for theme updates"""
        if widget not in self.widgets_to_update:
            self.widgets_to_update.append(widget)
    
    def unregister_widget(self, widget: QWidget):
        """Unregister widget from theme updates"""
        if widget in self.widgets_to_update:
            self.widgets_to_update.remove(widget)
    
    def set_theme(self, theme_name: str, animate: bool = True):
        """Set theme with optional animation"""
        if theme_name == self.current_theme:
            return
        
        old_theme = self.current_theme
        self.current_theme = theme_name
        
        if animate:
            self._animate_theme_transition(old_theme, theme_name)
        else:
            self._apply_theme_immediately(theme_name)
        
        self.theme_changed.emit(theme_name)
    
    def _apply_theme_immediately(self, theme_name: str):
        """Apply theme immediately without animation"""
        if theme_name == "auto":
            setTheme(Theme.AUTO)
        elif theme_name == "light":
            setTheme(Theme.LIGHT)
        elif theme_name == "dark":
            setTheme(Theme.DARK)
        elif theme_name in self.custom_themes:
            self._apply_custom_theme(theme_name)
        
        self._update_registered_widgets()
    
    def _animate_theme_transition(self, old_theme: str, new_theme: str):
        """Animate theme transition with smooth fade effect"""
        # Create fade out animation for current theme
        self.fade_timer = QTimer()
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(lambda: self._complete_theme_transition(new_theme))
        
        # Start fade out
        self._fade_widgets(0.7)
        self.fade_timer.start(self.transition_duration // 2)
    
    def _complete_theme_transition(self, new_theme: str):
        """Complete theme transition after fade out"""
        # Apply new theme
        self._apply_theme_immediately(new_theme)
        
        # Fade back in
        QTimer.singleShot(50, lambda: self._fade_widgets(1.0))
        QTimer.singleShot(self.transition_duration // 2, self.transition_finished.emit)
    
    def _fade_widgets(self, opacity: float):
        """Fade widgets to specified opacity"""
        for widget in self.widgets_to_update:
            if hasattr(widget, 'setWindowOpacity'):
                widget.setWindowOpacity(opacity)
    
    def _apply_custom_theme(self, theme_name: str):
        """Apply custom theme colors"""
        if theme_name not in self.custom_themes:
            return
        
        theme_colors = self.custom_themes[theme_name]
        
        # Update DesignSystem colors
        for color_key, color_value in theme_colors.items():
            DesignSystem.COLORS[color_key] = color_value
        
        # Set base theme to dark for custom themes
        setTheme(Theme.DARK)
    
    def _update_registered_widgets(self):
        """Update all registered widgets with new theme"""
        for widget in self.widgets_to_update:
            if hasattr(widget, 'update_theme'):
                widget.update_theme()
            else:
                widget.update()
    
    def _on_system_theme_changed(self, theme: Theme):
        """Handle system theme change"""
        if self.current_theme == "auto":
            self._update_registered_widgets()
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get list of available themes"""
        themes = {
            "auto": "Follow System",
            "light": "Light",
            "dark": "Dark"
        }
        
        # Add custom themes
        for theme_name in self.custom_themes:
            themes[theme_name] = theme_name.title()
        
        return themes
    
    def get_current_theme(self) -> str:
        """Get current theme name"""
        return self.current_theme
    
    def is_dark_theme_active(self) -> bool:
        """Check if dark theme is currently active"""
        if self.current_theme == "auto":
            return bool(isDarkTheme())
        elif self.current_theme == "light":
            return False
        else:
            return True  # Dark and custom themes are considered dark
    
    def create_theme_config_item(self) -> OptionsConfigItem:
        """Create config item for theme selection"""
        return OptionsConfigItem(
            "Theme",
            "auto",
            OptionsValidator(list(self.get_available_themes().keys())),
            restart=False
        )


class ThemeAwareWidget:
    """Mixin class for widgets that need theme awareness"""
    
    def __init__(self):
        self.theme_manager: Optional["EnhancedThemeManager"] = None

    def set_theme_manager(self, theme_manager: "EnhancedThemeManager"):
        """Set theme manager for this widget"""
        self.theme_manager = theme_manager
        self.theme_manager.register_widget(self)
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
    
    def on_theme_changed(self, theme_name: str):
        """Handle theme change - override in subclasses"""
        self.update_theme()
    
    def update_theme(self):
        """Update widget styling for current theme - override in subclasses"""
        if hasattr(self, 'update'):
            self.update()
    
    def get_theme_color(self, color_key: str) -> str:
        """Get color for current theme"""
        return EnhancedDesignSystem.get_color(color_key)


class OptionsValidator:
    """Simple options validator for config items"""
    
    def __init__(self, options: list):
        self.options = options
    
    def validate(self, value):
        return value in self.options


# Global theme manager instance
_theme_manager = None

def get_theme_manager() -> "EnhancedThemeManager":
    """Get global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = EnhancedThemeManager()
    return _theme_manager


# Backward compatibility alias
EnhancedThemeManager = ThemeManager

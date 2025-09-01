"""
Enhanced theme manager for VidTanium with QFluentWidgets integration
Provides advanced theming, animations, and visual enhancements
"""

from typing import Optional, Dict, Any, cast
from PySide6.QtCore import QObject, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtGui import QColor, QPalette
from qfluentwidgets import (
    setTheme, Theme, qconfig, SystemThemeListener, isDarkTheme,
    setThemeColor, ThemeColor, FluentStyleSheet
)
from loguru import logger


class EnhancedThemeManager(QObject):
    """Enhanced theme manager with advanced visual features"""

    theme_changed = Signal(str)  # Emitted when theme changes
    accent_color_changed = Signal(QColor)  # Emitted when accent color changes
    
    # Predefined accent colors
    ACCENT_COLORS = {
        "blue": "#0078D4",
        "purple": "#8B5CF6", 
        "green": "#10B981",
        "orange": "#F59E0B",
        "red": "#EF4444",
        "pink": "#EC4899",
        "indigo": "#6366F1",
        "teal": "#14B8A6"
    }
    
    # Theme-specific styling
    LIGHT_THEME_COLORS = {
        "background": "#FAFAFA",
        "surface": "#FFFFFF",
        "card": "#FFFFFF",
        "border": "#E5E7EB",
        "text_primary": "#1F2937",
        "text_secondary": "#6B7280",
        "shadow": "rgba(0, 0, 0, 0.1)"
    }
    
    DARK_THEME_COLORS = {
        "background": "#0F172A",
        "surface": "#1E293B",
        "card": "#334155",
        "border": "#475569",
        "text_primary": "#F8FAFC",
        "text_secondary": "#CBD5E1",
        "shadow": "rgba(0, 0, 0, 0.3)"
    }

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.theme_listener: Optional[SystemThemeListener] = None
        self._current_theme: str = "system"
        self._current_accent: str = "blue"
        self._animations_enabled: bool = True
        
        # Animation timers
        self._theme_transition_timer = QTimer()
        self._theme_transition_timer.setSingleShot(True)
        
        # Apply initial theme and accent
        self.apply_theme_from_settings()
        self.apply_accent_from_settings()

    def apply_theme_from_settings(self):
        """Apply theme based on current settings"""
        theme_mode = self.settings.get("general", "theme", "system")
        self.set_theme(theme_mode)

    def apply_accent_from_settings(self):
        """Apply accent color based on current settings"""
        accent_color = self.settings.get("ui", "accent_color", "blue")
        self.set_accent_color(accent_color)

    def set_theme(self, theme_mode: str, animate: bool = True):
        """Set application theme with optional animation
        
        Args:
            theme_mode: One of "system", "light", "dark"
            animate: Whether to animate the transition
        """
        try:
            # Clean up existing listener
            if self.theme_listener:
                self.theme_listener.terminate()
                self.theme_listener.deleteLater()
                self.theme_listener = None

            old_theme = self._current_theme
            self._current_theme = theme_mode

            if animate and self._animations_enabled:
                self._animate_theme_transition(old_theme, theme_mode)
            else:
                self._apply_theme_immediately(theme_mode)

        except Exception as e:
            logger.error(f"Error setting theme '{theme_mode}': {e}", exc_info=True)
            self._apply_fallback_theme()

    def _apply_theme_immediately(self, theme_mode: str):
        """Apply theme without animation"""
        if theme_mode == "system":
            setTheme(Theme.AUTO)
            self.theme_listener = SystemThemeListener(self.parent())
            self.theme_listener.start()
            logger.info("Enabled system theme following")

        elif theme_mode == "light":
            setTheme(Theme.LIGHT)
            logger.info("Applied light theme")

        elif theme_mode == "dark":
            setTheme(Theme.DARK)
            logger.info("Applied dark theme")

        # Save configuration
        qconfig.save()
        self.settings.set("general", "theme", theme_mode)
        self.settings.save_settings()
        
        # Apply custom styling
        self._apply_custom_styling()
        
        # Emit signal
        self.theme_changed.emit(theme_mode)

    def _animate_theme_transition(self, old_theme: str, new_theme: str):
        """Animate theme transition"""
        if not self.parent():
            self._apply_theme_immediately(new_theme)
            return
            
        # Create opacity effect for smooth transition
        effect = QGraphicsOpacityEffect()
        parent = self.parent()
        if parent and hasattr(parent, 'setGraphicsEffect'):
            parent.setGraphicsEffect(effect)
        
        # Fade out animation
        self.fade_out_animation = QPropertyAnimation(parent=self)
        self.fade_out_animation.setTargetObject(effect)
        self.fade_out_animation.setPropertyName(b"opacity")
        self.fade_out_animation.setDuration(150)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.7)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Fade in animation
        self.fade_in_animation = QPropertyAnimation(parent=self)
        self.fade_in_animation.setTargetObject(effect)
        self.fade_in_animation.setPropertyName(b"opacity")
        self.fade_in_animation.setDuration(150)
        self.fade_in_animation.setStartValue(0.7)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # Connect animations
        self.fade_out_animation.finished.connect(
            lambda: self._on_fade_out_finished(new_theme)
        )
        self.fade_in_animation.finished.connect(
            lambda: self._clear_graphics_effect()
        )
        
        # Start fade out
        self.fade_out_animation.start()

    def _clear_graphics_effect(self):
        """Clear graphics effect from parent widget"""
        parent = self.parent()
        if parent and hasattr(parent, 'setGraphicsEffect'):
            parent.setGraphicsEffect(None)

    def _on_fade_out_finished(self, new_theme: str):
        """Handle fade out completion"""
        self._apply_theme_immediately(new_theme)
        self.fade_in_animation.start()

    def set_accent_color(self, color_name: str):
        """Set accent color
        
        Args:
            color_name: Name of the accent color or hex value
        """
        try:
            if color_name in self.ACCENT_COLORS:
                color_hex = self.ACCENT_COLORS[color_name]
            elif color_name.startswith("#"):
                color_hex = color_name
            else:
                color_hex = self.ACCENT_COLORS["blue"]  # fallback
                
            color = QColor(color_hex)
            setThemeColor(color)
            
            self._current_accent = color_name
            self.settings.set("ui", "accent_color", color_name)
            self.settings.save_settings()
            
            # Apply custom styling with new accent
            self._apply_custom_styling()
            
            self.accent_color_changed.emit(color)
            logger.info(f"Applied accent color: {color_name} ({color_hex})")
            
        except Exception as e:
            logger.error(f"Error setting accent color '{color_name}': {e}")

    def _apply_custom_styling(self):
        """Apply custom styling enhancements"""
        try:
            is_dark = self.is_dark_theme()
            colors = self.DARK_THEME_COLORS if is_dark else self.LIGHT_THEME_COLORS
            
            # Custom stylesheet for enhanced appearance
            custom_style = f"""
            /* Enhanced card styling */
            ElevatedCardWidget {{
                background-color: {colors['card']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px {colors['shadow']};
            }}
            
            /* Enhanced button styling */
            PrimaryPushButton {{
                border-radius: 8px;
                font-weight: 600;
                padding: 8px 16px;
            }}
            
            /* Enhanced scroll area */
            ScrollArea {{
                background-color: {colors['background']};
                border: none;
            }}
            
            /* Enhanced navigation */
            NavigationWidget {{
                background-color: {colors['surface']};
                border-right: 1px solid {colors['border']};
            }}
            
            /* Enhanced status widgets */
            .status-widget {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 12px;
            }}
            
            /* Enhanced progress bars */
            ProgressBar {{
                border-radius: 4px;
                background-color: {colors['border']};
            }}
            """
            
            # Apply to application
            if self.parent():
                self.parent().setStyleSheet(custom_style)
                
        except Exception as e:
            logger.error(f"Error applying custom styling: {e}")

    def _apply_fallback_theme(self):
        """Apply fallback theme in case of errors"""
        try:
            setTheme(Theme.AUTO)
            logger.warning("Applied fallback auto theme")
        except Exception as e:
            logger.error(f"Error applying fallback theme: {e}")

    def get_current_theme(self) -> str:
        """Get current theme mode"""
        return self._current_theme

    def get_current_accent(self) -> str:
        """Get current accent color"""
        return self._current_accent

    def is_dark_theme(self) -> bool:
        """Check if current theme is dark"""
        return cast(bool, isDarkTheme())

    def get_theme_colors(self) -> Dict[str, str]:
        """Get current theme color palette"""
        return self.DARK_THEME_COLORS if self.is_dark_theme() else self.LIGHT_THEME_COLORS

    def enable_animations(self, enabled: bool = True):
        """Enable or disable theme animations"""
        self._animations_enabled = enabled
        self.settings.set("ui", "animations_enabled", enabled)
        self.settings.save_settings()
        logger.debug(f"Theme animations {'enabled' if enabled else 'disabled'}")

    def are_animations_enabled(self) -> bool:
        """Check if animations are enabled"""
        return self._animations_enabled

    def apply_widget_enhancement(self, widget, enhancement_type: str = "card"):
        """Apply visual enhancements to a widget
        
        Args:
            widget: Widget to enhance
            enhancement_type: Type of enhancement ("card", "button", "status")
        """
        try:
            if enhancement_type == "card":
                widget.setObjectName("enhanced-card")
            elif enhancement_type == "status":
                widget.setObjectName("status-widget")
            
            # Apply current styling
            self._apply_custom_styling()
            
        except Exception as e:
            logger.error(f"Error applying widget enhancement: {e}")

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.theme_listener:
                self.theme_listener.terminate()
                self.theme_listener.deleteLater()
                self.theme_listener = None
                
            # Clean up animations
            if hasattr(self, 'fade_out_animation'):
                self.fade_out_animation.stop()
            if hasattr(self, 'fade_in_animation'):
                self.fade_in_animation.stop()
                
            logger.info("Enhanced theme manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up enhanced theme manager: {e}")


# Backward compatibility alias
ThemeManager = EnhancedThemeManager

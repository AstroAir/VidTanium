"""
Enhanced theme manager for VidTanium with QFluentWidgets integration
"""

import logging
from typing import Optional
from PySide6.QtCore import QObject, Signal, QTimer
from qfluentwidgets import setTheme, Theme, qconfig, SystemThemeListener, isDarkTheme

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """Enhanced theme manager with system theme listening"""
    
    theme_changed = Signal(str)  # Emitted when theme changes
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.theme_listener: Optional[SystemThemeListener] = None
        self._current_theme = "system"
        
        # Apply initial theme
        self.apply_theme_from_settings()
    
    def apply_theme_from_settings(self):
        """Apply theme based on current settings"""
        theme_mode = self.settings.get("general", "theme", "system")
        self.set_theme(theme_mode)
    
    def set_theme(self, theme_mode: str):
        """Set application theme
        
        Args:
            theme_mode: One of "system", "light", "dark"
        """
        try:
            # Clean up existing listener
            if self.theme_listener:
                self.theme_listener.terminate()
                self.theme_listener.deleteLater()
                self.theme_listener = None
            
            self._current_theme = theme_mode
            
            if theme_mode == "system":
                # Use system theme with listener
                setTheme(Theme.AUTO)
                self.theme_listener = SystemThemeListener(self.parent())
                self.theme_listener.start()
                logger.info("Enabled system theme following")
                
            elif theme_mode == "light":
                # Force light theme
                setTheme(Theme.LIGHT)
                logger.info("Applied light theme")
                
            elif theme_mode == "dark":
                # Force dark theme
                setTheme(Theme.DARK)
                logger.info("Applied dark theme")
            
            # Save configuration
            qconfig.save()
            
            # Update settings
            self.settings.set("general", "theme", theme_mode)
            self.settings.save_settings()
            
            # Emit signal
            self.theme_changed.emit(theme_mode)
            
        except Exception as e:
            logger.error(f"Error setting theme '{theme_mode}': {e}", exc_info=True)
            # Fallback to auto theme
            try:
                setTheme(Theme.AUTO)
            except:
                pass
    
    def get_current_theme(self) -> str:
        """Get current theme mode"""
        return self._current_theme
    
    def is_dark_theme(self) -> bool:
        """Check if current theme is dark"""
        return isDarkTheme()
    
    def cleanup(self):
        """Clean up resources"""
        if self.theme_listener:
            try:
                self.theme_listener.terminate()
                self.theme_listener.deleteLater()
                self.theme_listener = None
                logger.info("Theme listener cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up theme listener: {e}")

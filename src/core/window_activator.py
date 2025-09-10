"""
Window Activator for VidTanium

Provides platform-specific window activation functionality to bring
the application window to the foreground when requested.
"""

import os
import sys
import platform
import subprocess
from abc import ABC, abstractmethod
from typing import Optional, Any
from loguru import logger
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QWindow


class WindowActivatorBase(ABC):
    """Abstract base class for platform-specific window activation"""
    
    @abstractmethod
    def activate_window(self, widget: Optional[QWidget] = None) -> bool:
        """Activate and bring window to foreground"""
        pass
    
    @abstractmethod
    def show_and_raise_window(self, widget: Optional[QWidget] = None) -> bool:
        """Show window and raise it to the top"""
        pass
    
    def get_main_window(self) -> Optional[QWidget]:
        """Get the main application window"""
        app = QApplication.instance()
        if not app:
            return None
        
        # Find the main window
        for widget in app.topLevelWidgets():
            if widget.isWindow() and not widget.isHidden():
                return widget
        
        # If no visible window found, return the first top-level widget
        widgets = app.topLevelWidgets()
        return widgets[0] if widgets else None


class WindowsWindowActivator(WindowActivatorBase):
    """Windows-specific window activation using Win32 API"""
    
    def __init__(self):
        self.user32 = None
        self.kernel32 = None
        self._init_win32_apis()
    
    def _init_win32_apis(self):
        """Initialize Win32 APIs"""
        try:
            import ctypes
            from ctypes import wintypes
            
            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32
            
            # Define function prototypes
            self.user32.SetForegroundWindow.argtypes = [wintypes.HWND]
            self.user32.SetForegroundWindow.restype = wintypes.BOOL
            
            self.user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
            self.user32.ShowWindow.restype = wintypes.BOOL
            
            self.user32.IsIconic.argtypes = [wintypes.HWND]
            self.user32.IsIconic.restype = wintypes.BOOL
            
            self.user32.BringWindowToTop.argtypes = [wintypes.HWND]
            self.user32.BringWindowToTop.restype = wintypes.BOOL
            
            logger.debug("Win32 APIs initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Win32 APIs not available: {e}")
            self.user32 = None
            self.kernel32 = None
    
    def _get_window_handle(self, widget: Optional[QWidget] = None) -> Optional[int]:
        """Get the native window handle"""
        if not widget:
            widget = self.get_main_window()
        
        if not widget:
            logger.warning("No window found to activate")
            return None
        
        # Get the native window handle
        window_handle = widget.winId()
        if window_handle:
            return int(window_handle)
        
        return None
    
    def activate_window(self, widget: Optional[QWidget] = None) -> bool:
        """Activate window using Win32 API"""
        if not self.user32:
            return self._fallback_activation(widget)
        
        hwnd = self._get_window_handle(widget)
        if not hwnd:
            return False
        
        try:
            # Constants for ShowWindow
            SW_RESTORE = 9
            SW_SHOW = 5
            
            # If window is minimized, restore it
            if self.user32.IsIconic(hwnd):
                self.user32.ShowWindow(hwnd, SW_RESTORE)
            else:
                self.user32.ShowWindow(hwnd, SW_SHOW)
            
            # Bring window to top and set foreground
            self.user32.BringWindowToTop(hwnd)
            success = self.user32.SetForegroundWindow(hwnd)
            
            if success:
                logger.info("Successfully activated window using Win32 API")
                return True
            else:
                logger.warning("SetForegroundWindow failed, trying fallback")
                return self._fallback_activation(widget)
                
        except Exception as e:
            logger.error(f"Error activating window with Win32 API: {e}")
            return self._fallback_activation(widget)
    
    def show_and_raise_window(self, widget: Optional[QWidget] = None) -> bool:
        """Show and raise window"""
        if not widget:
            widget = self.get_main_window()
        
        if not widget:
            return False
        
        try:
            # Use Qt methods first
            widget.show()
            widget.raise_()
            widget.activateWindow()
            
            # Then use Win32 API for better activation
            return self.activate_window(widget)
            
        except Exception as e:
            logger.error(f"Error showing and raising window: {e}")
            return False
    
    def _fallback_activation(self, widget: Optional[QWidget] = None) -> bool:
        """Fallback activation using Qt methods"""
        if not widget:
            widget = self.get_main_window()
        
        if not widget:
            return False
        
        try:
            widget.show()
            widget.raise_()
            widget.activateWindow()
            
            # Try to request attention
            if hasattr(widget, 'requestActivate'):
                widget.requestActivate()
            
            logger.info("Used fallback window activation")
            return True
            
        except Exception as e:
            logger.error(f"Fallback window activation failed: {e}")
            return False


class MacOSWindowActivator(WindowActivatorBase):
    """macOS-specific window activation"""
    
    def activate_window(self, widget: Optional[QWidget] = None) -> bool:
        """Activate window on macOS"""
        try:
            # Use osascript to activate the application
            script = '''
            tell application "System Events"
                set frontmost of first application process whose name is "VidTanium" to true
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("Successfully activated window using AppleScript")
                return self._qt_activation(widget)
            else:
                logger.warning(f"AppleScript activation failed: {result.stderr}")
                return self._qt_activation(widget)
                
        except subprocess.TimeoutExpired:
            logger.warning("AppleScript activation timed out")
            return self._qt_activation(widget)
        except Exception as e:
            logger.error(f"Error activating window with AppleScript: {e}")
            return self._qt_activation(widget)
    
    def show_and_raise_window(self, widget: Optional[QWidget] = None) -> bool:
        """Show and raise window on macOS"""
        if not widget:
            widget = self.get_main_window()
        
        if not widget:
            return False
        
        try:
            # Use Qt methods
            widget.show()
            widget.raise_()
            widget.activateWindow()
            
            # Use macOS-specific activation
            return self.activate_window(widget)
            
        except Exception as e:
            logger.error(f"Error showing and raising window on macOS: {e}")
            return False
    
    def _qt_activation(self, widget: Optional[QWidget] = None) -> bool:
        """Qt-based activation as fallback"""
        if not widget:
            widget = self.get_main_window()
        
        if not widget:
            return False
        
        try:
            widget.show()
            widget.raise_()
            widget.activateWindow()
            
            # Try to get application focus
            app = QApplication.instance()
            if app:
                app.setActiveWindow(widget)
            
            logger.info("Used Qt-based window activation on macOS")
            return True
            
        except Exception as e:
            logger.error(f"Qt window activation failed on macOS: {e}")
            return False


class LinuxWindowActivator(WindowActivatorBase):
    """Linux-specific window activation"""
    
    def activate_window(self, widget: Optional[QWidget] = None) -> bool:
        """Activate window on Linux"""
        # Try different methods in order of preference
        methods = [
            self._activate_with_wmctrl,
            self._activate_with_xdotool,
            self._activate_with_qt
        ]
        
        for method in methods:
            try:
                if method(widget):
                    return True
            except Exception as e:
                logger.debug(f"Window activation method failed: {e}")
                continue
        
        logger.warning("All window activation methods failed on Linux")
        return False
    
    def show_and_raise_window(self, widget: Optional[QWidget] = None) -> bool:
        """Show and raise window on Linux"""
        if not widget:
            widget = self.get_main_window()
        
        if not widget:
            return False
        
        try:
            widget.show()
            widget.raise_()
            widget.activateWindow()
            
            return self.activate_window(widget)
            
        except Exception as e:
            logger.error(f"Error showing and raising window on Linux: {e}")
            return False
    
    def _activate_with_wmctrl(self, widget: Optional[QWidget] = None) -> bool:
        """Try to activate window using wmctrl"""
        try:
            # Check if wmctrl is available
            check_result = subprocess.run(['which', 'wmctrl'], capture_output=True)
            if check_result.returncode != 0:
                return False
            
            # Try to activate VidTanium window
            result: subprocess.CompletedProcess[bytes] = subprocess.run(
                ['wmctrl', '-a', 'VidTanium'],
                capture_output=True,
                timeout=3
            )
            
            if result.returncode == 0:
                logger.info("Successfully activated window using wmctrl")
                return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def _activate_with_xdotool(self, widget: Optional[QWidget] = None) -> bool:
        """Try to activate window using xdotool"""
        try:
            # Check if xdotool is available
            check_result = subprocess.run(['which', 'xdotool'], capture_output=True)
            if check_result.returncode != 0:
                return False
            
            # Find and activate VidTanium window
            result: subprocess.CompletedProcess[bytes] = subprocess.run(
                ['xdotool', 'search', '--name', 'VidTanium', 'windowactivate'],
                capture_output=True,
                timeout=3
            )
            
            if result.returncode == 0:
                logger.info("Successfully activated window using xdotool")
                return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def _activate_with_qt(self, widget: Optional[QWidget] = None) -> bool:
        """Activate window using Qt methods"""
        if not widget:
            widget = self.get_main_window()
        
        if not widget:
            return False
        
        try:
            widget.show()
            widget.raise_()
            widget.activateWindow()
            
            # Try to request attention
            if hasattr(widget, 'requestActivate'):
                widget.requestActivate()
            
            logger.info("Used Qt-based window activation on Linux")
            return True
            
        except Exception as e:
            logger.error(f"Qt window activation failed on Linux: {e}")
            return False


class WindowActivator:
    """Main window activator that provides a unified interface"""
    
    def __init__(self):
        self._implementation = self._create_implementation()
    
    def _create_implementation(self) -> WindowActivatorBase:
        """Create platform-specific window activator"""
        system = platform.system().lower()
        
        if system == "windows":
            return WindowsWindowActivator()
        elif system == "darwin":
            return MacOSWindowActivator()
        else:
            # Linux and other Unix-like systems
            return LinuxWindowActivator()
    
    def activate_window(self, widget: Optional[QWidget] = None) -> bool:
        """Activate and bring window to foreground"""
        return self._implementation.activate_window(widget)
    
    def show_and_raise_window(self, widget: Optional[QWidget] = None) -> bool:
        """Show window and raise it to the top"""
        return self._implementation.show_and_raise_window(widget)
    
    def activate_with_delay(self, widget: Optional[QWidget] = None, delay_ms: int = 100) -> None:
        """Activate window with a small delay (useful for Qt event processing)"""
        def delayed_activation():
            self.show_and_raise_window(widget)
        
        QTimer.singleShot(delay_ms, delayed_activation)


# Global window activator instance
_window_activator: Optional[WindowActivator] = None


def get_window_activator() -> WindowActivator:
    """Get the global window activator instance"""
    global _window_activator
    if _window_activator is None:
        _window_activator = WindowActivator()
    return _window_activator

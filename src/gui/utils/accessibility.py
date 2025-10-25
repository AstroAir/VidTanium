"""
Accessibility Enhancement System for VidTanium
Provides comprehensive accessibility features including keyboard navigation,
screen reader support, and high contrast modes
"""

from PySide6.QtWidgets import (
    QWidget, QApplication, QLabel, QFrame, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEvent, QRect
from PySide6.QtGui import (
    QKeySequence, QPalette, QColor, QFont, QFontMetrics, QPainter,
    QAccessibleInterface, QAccessible, QPixmap, QShortcut
)
from qfluentwidgets import FluentIcon as FIF
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from .i18n import tr


class AccessibilityMode(Enum):
    """Accessibility mode types"""
    NORMAL = "normal"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    KEYBOARD_ONLY = "keyboard_only"
    SCREEN_READER = "screen_reader"


class NavigationDirection(Enum):
    """Navigation direction for keyboard navigation"""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    NEXT = "next"
    PREVIOUS = "previous"
    FIRST = "first"
    LAST = "last"


@dataclass
class AccessibilitySettings:
    """Accessibility settings configuration"""
    high_contrast: bool = False
    large_text: bool = False
    keyboard_navigation: bool = True
    screen_reader_support: bool = True
    focus_indicators: bool = True
    audio_feedback: bool = False
    reduced_motion: bool = False
    text_scale_factor: float = 1.0
    contrast_ratio: float = 1.0


class FocusIndicator(QFrame):
    """Visual focus indicator for accessibility"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            FocusIndicator {
                border: 2px solid #0078d4;
                background: transparent;
                border-radius: 4px;
            }
        """)
        self.hide()
    
    def show_around(self, widget: QWidget) -> None:
        """Show focus indicator around a widget"""
        if not widget or not widget.isVisible():
            self.hide()
            return
        
        # Position the indicator around the widget
        rect = widget.geometry()
        parent_widget = widget.parent()
        if parent_widget and isinstance(parent_widget, QWidget):
            # Convert to parent coordinates
            global_pos = widget.mapToGlobal(widget.rect().topLeft())
            parent_pos = parent_widget.mapFromGlobal(global_pos)
            rect.moveTo(parent_pos)
        
        # Add padding around the widget
        padding = 4
        rect.adjust(-padding, -padding, padding, padding)
        
        self.setGeometry(rect)
        self.show()
        self.raise_()


class KeyboardNavigationManager(QObject):
    """Manages keyboard navigation throughout the application"""
    
    focus_changed = Signal(QWidget)
    navigation_requested = Signal(NavigationDirection)
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.navigable_widgets: List[QWidget] = []
        self.current_focus_index = -1
        self.focus_indicator = None
        self.shortcuts: Dict[str, QShortcut] = {}
        self._setup_navigation_shortcuts()
    
    def _setup_navigation_shortcuts(self) -> None:
        """Setup keyboard shortcuts for navigation"""
        # Simplified shortcut setup - will be enhanced later
        logger.debug("Navigation shortcuts setup (simplified implementation)")
    
    def register_widget(self, widget: QWidget, group: str = "default") -> None:
        """Register a widget for keyboard navigation"""
        if widget not in self.navigable_widgets:
            self.navigable_widgets.append(widget)
            widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
            # Add accessibility properties
            widget.setAccessibleName(widget.objectName() or widget.__class__.__name__)
            if hasattr(widget, 'toolTip') and widget.toolTip():
                widget.setAccessibleDescription(widget.toolTip())
    
    def unregister_widget(self, widget: QWidget) -> None:
        """Unregister a widget from keyboard navigation"""
        if widget in self.navigable_widgets:
            self.navigable_widgets.remove(widget)
    
    def set_focus_indicator(self, indicator: FocusIndicator) -> None:
        """Set the focus indicator widget"""
        self.focus_indicator = indicator
    
    def _navigate_next(self) -> None:
        """Navigate to next widget"""
        if not self.navigable_widgets:
            return
        
        self.current_focus_index = (self.current_focus_index + 1) % len(self.navigable_widgets)
        self._set_focus_to_current()
    
    def _navigate_previous(self) -> None:
        """Navigate to previous widget"""
        if not self.navigable_widgets:
            return
        
        self.current_focus_index = (self.current_focus_index - 1) % len(self.navigable_widgets)
        self._set_focus_to_current()
    
    def _navigate_first(self) -> None:
        """Navigate to first widget"""
        if not self.navigable_widgets:
            return
        
        self.current_focus_index = 0
        self._set_focus_to_current()
    
    def _navigate_last(self) -> None:
        """Navigate to last widget"""
        if not self.navigable_widgets:
            return
        
        self.current_focus_index = len(self.navigable_widgets) - 1
        self._set_focus_to_current()
    
    def _navigate_direction(self, direction: NavigationDirection) -> None:
        """Navigate in a specific direction"""
        self.navigation_requested.emit(direction)
    
    def _cycle_focus_groups(self) -> None:
        """Cycle through focus groups (F6 functionality)"""
        # This would cycle through major UI sections
        logger.info("Cycling focus groups")
    
    def _set_focus_to_current(self) -> None:
        """Set focus to current widget"""
        if 0 <= self.current_focus_index < len(self.navigable_widgets):
            widget = self.navigable_widgets[self.current_focus_index]
            if widget.isVisible() and widget.isEnabled():
                widget.setFocus()
                self.focus_changed.emit(widget)
                
                if self.focus_indicator:
                    self.focus_indicator.show_around(widget)


class ScreenReaderSupport(QObject):
    """Provides screen reader support and announcements"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.enabled = True
        self.announcement_queue: List[str] = []
        self.announcement_timer = QTimer()
        self.announcement_timer.timeout.connect(self._process_announcements)
        self.announcement_timer.start(100)  # Process every 100ms
    
    def _process_announcements(self) -> None:
        """Process queued announcements"""
        if self.announcement_queue and self.enabled:
            # Process announcement (simplified implementation)
            announcement = self.announcement_queue.pop(0)
            logger.debug(f"Screen reader announcement: {announcement}")
    
    def announce(self, text: str, priority: str = "normal") -> None:
        """Announce text to screen reader"""
        if not self.enabled or not text:
            return
        
        # Add to queue with priority
        if priority == "urgent":
            self.announcement_queue.insert(0, text)
        else:
            self.announcement_queue.append(text)
        
        logger.debug(f"Screen reader announcement: {text}")
    
    def announce_widget_focus(self, widget: QWidget) -> None:
        """Announce widget focus change"""
        if not widget:
            return
        
        # Build announcement text
        text_parts = []
        
        # Widget name
        name = widget.accessibleName() or widget.objectName()
        if name:
            text_parts.append(name)
        
        # Widget type
        widget_type = self._get_widget_type_description(widget)
        if widget_type:
            text_parts.append(widget_type)
        
        # Widget state
        state = self._get_widget_state_description(widget)
        if state:
            text_parts.append(state)
        
        # Widget description
        description = widget.accessibleDescription() or widget.toolTip()
        if description:
            text_parts.append(description)
        
        if text_parts:
            announcement = ", ".join(text_parts)
            self.announce(announcement)
    
    def _get_widget_type_description(self, widget: QWidget) -> str:
        """Get human-readable widget type description"""
        type_map = {
            "QPushButton": tr("accessibility.button"),
            "QLineEdit": tr("accessibility.text_input"),
            "QTextEdit": tr("accessibility.text_area"),
            "QComboBox": tr("accessibility.dropdown"),
            "QCheckBox": tr("accessibility.checkbox"),
            "QRadioButton": tr("accessibility.radio_button"),
            "QSlider": tr("accessibility.slider"),
            "QProgressBar": tr("accessibility.progress_bar"),
            "QLabel": tr("accessibility.label"),
            "QListWidget": tr("accessibility.list"),
            "QTreeWidget": tr("accessibility.tree"),
            "QTabWidget": tr("accessibility.tab_container")
        }
        
        widget_class = widget.__class__.__name__
        return type_map.get(widget_class, "")
    
    def _get_widget_state_description(self, widget: QWidget) -> str:
        """Get widget state description"""
        states = []
        
        if not widget.isEnabled():
            states.append(tr("accessibility.disabled"))
        
        if hasattr(widget, 'isChecked') and widget.isChecked():
            states.append(tr("accessibility.checked"))
        
        if hasattr(widget, 'isReadOnly') and widget.isReadOnly():
            states.append(tr("accessibility.read_only"))
        
        if hasattr(widget, 'isRequired') and widget.isRequired():
            states.append(tr("accessibility.required"))
        
        return ", ".join(states)
    
    def _process_announcements(self) -> None:
        """Process announcement queue"""
        if self.announcement_queue:
            text = self.announcement_queue.pop(0)
            # In a real implementation, this would interface with screen reader APIs
            # For now, we'll just log the announcement
            logger.debug(f"Screen reader announcement: {text}")


class HighContrastTheme(QObject):
    """High contrast theme for accessibility"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.original_palette = None
        self.high_contrast_palette = None
        self._create_high_contrast_palette()
    
    def _create_high_contrast_palette(self) -> None:
        """Create high contrast color palette"""
        palette = QPalette()
        
        # High contrast colors
        black = QColor(0, 0, 0)
        white = QColor(255, 255, 255)
        blue = QColor(0, 120, 215)
        yellow = QColor(255, 255, 0)
        
        # Set palette colors
        palette.setColor(QPalette.ColorRole.Window, white)
        palette.setColor(QPalette.ColorRole.WindowText, black)
        palette.setColor(QPalette.ColorRole.Base, white)
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Text, black)
        palette.setColor(QPalette.ColorRole.Button, white)
        palette.setColor(QPalette.ColorRole.ButtonText, black)
        palette.setColor(QPalette.ColorRole.Highlight, blue)
        palette.setColor(QPalette.ColorRole.HighlightedText, white)
        palette.setColor(QPalette.ColorRole.Link, blue)
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(128, 0, 128))
        
        self.high_contrast_palette = palette
    
    def apply_high_contrast(self, app: QApplication) -> None:
        """Apply high contrast theme"""
        if not self.original_palette:
            self.original_palette = app.palette()
        
        if self.high_contrast_palette:
            app.setPalette(self.high_contrast_palette)
        
        # Apply high contrast stylesheet
        high_contrast_style = """
            QWidget {
                background-color: white;
                color: black;
                border: 1px solid black;
            }
            
            QPushButton {
                background-color: white;
                color: black;
                border: 2px solid black;
                padding: 4px 8px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            
            QPushButton:focus {
                border: 3px solid #0078d4;
            }
            
            QLineEdit, QTextEdit {
                background-color: white;
                color: black;
                border: 2px solid black;
                padding: 2px;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border: 3px solid #0078d4;
            }
            
            QComboBox {
                background-color: white;
                color: black;
                border: 2px solid black;
                padding: 2px;
            }
            
            QComboBox:focus {
                border: 3px solid #0078d4;
            }
            
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid black;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: black;
            }
            
            QRadioButton::indicator:checked {
                background-color: black;
                border-radius: 8px;
            }
        """
        
        app.setStyleSheet(high_contrast_style)
    
    def restore_normal_theme(self, app: QApplication) -> None:
        """Restore normal theme"""
        if self.original_palette:
            app.setPalette(self.original_palette)
        
        app.setStyleSheet("")  # Clear custom stylesheet


class AccessibilityManager(QObject):
    """Main accessibility manager"""

    settings_changed = Signal(AccessibilitySettings)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.settings = AccessibilitySettings()
        self._initialized = False

        # Lazy initialization - will be done when first used
        self.keyboard_nav = None
        self.screen_reader = None
        self.high_contrast = None
        self.focus_indicator = None

        logger.info("Accessibility manager created (lazy initialization)")

    def _ensure_initialized(self) -> None:
        """Ensure components are initialized"""
        if self._initialized:
            return

        try:
            self.keyboard_nav = KeyboardNavigationManager(self)
            self.screen_reader = ScreenReaderSupport(self)
            self.high_contrast = HighContrastTheme(self)
            self.focus_indicator = FocusIndicator()

            # Connect signals
            self.keyboard_nav.focus_changed.connect(self.screen_reader.announce_widget_focus)
            self.keyboard_nav.set_focus_indicator(self.focus_indicator)

            self._initialized = True
            logger.info("Accessibility manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize accessibility manager: {e}")
            self._initialized = False
    
    def apply_settings(self, settings: AccessibilitySettings) -> None:
        """Apply accessibility settings"""
        self._ensure_initialized()
        if not self._initialized:
            logger.warning("Accessibility manager not initialized, skipping settings application")
            return

        self.settings = settings
        app = QApplication.instance()

        # Apply high contrast theme (only if app is QApplication)
        if app and isinstance(app, QApplication) and self.high_contrast:
            if settings.high_contrast:
                self.high_contrast.apply_high_contrast(app)
            else:
                self.high_contrast.restore_normal_theme(app)

        # Apply text scaling
        if settings.large_text or settings.text_scale_factor != 1.0:
            self._apply_text_scaling(settings.text_scale_factor)

        # Enable/disable screen reader support
        if self.screen_reader:
            self.screen_reader.enabled = settings.screen_reader_support

        # Show/hide focus indicators
        if self.focus_indicator:
            if settings.focus_indicators:
                self.focus_indicator.show()
            else:
                self.focus_indicator.hide()

        self.settings_changed.emit(settings)
        logger.info(f"Applied accessibility settings: {settings}")
    
    def _apply_text_scaling(self, scale_factor: float) -> None:
        """Apply text scaling"""
        app = QApplication.instance()
        if app and isinstance(app, QApplication):
            font = app.font()
            original_size = font.pointSize()
            new_size = int(original_size * scale_factor)
            font.setPointSize(max(8, min(72, new_size)))  # Clamp between 8 and 72
            app.setFont(font)
    
    def register_widget(self, widget: QWidget, group: str = "default") -> None:
        """Register widget for accessibility"""
        self._ensure_initialized()
        if self.keyboard_nav:
            self.keyboard_nav.register_widget(widget, group)

    def unregister_widget(self, widget: QWidget) -> None:
        """Unregister widget from accessibility"""
        self._ensure_initialized()
        if self.keyboard_nav:
            self.keyboard_nav.unregister_widget(widget)

    def announce(self, text: str, priority: str = "normal") -> None:
        """Make screen reader announcement"""
        self._ensure_initialized()
        if self.screen_reader:
            self.screen_reader.announce(text, priority)
    
    def get_settings(self) -> AccessibilitySettings:
        """Get current accessibility settings"""
        return self.settings


# Global accessibility manager instance
accessibility_manager = AccessibilityManager()

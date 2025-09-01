from typing import Optional
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Signal, Slot, QObject, QTimer, QPropertyAnimation, QEasingCurve
from qfluentwidgets import (
    FluentIcon as FIF, RoundMenu, Action, MenuAnimationType,
    InfoBar, InfoBarPosition, isDarkTheme
)
import logging
from ..utils.i18n import tr
from ..theme_manager import EnhancedThemeManager
from loguru import logger

class EnhancedSystemTrayIcon(QObject):
    """Enhanced system tray icon manager with modern notifications and theming"""

    # Signal definitions
    action_triggered = Signal(str)  # Action name
    notification_clicked = Signal(str)  # Notification data

    def __init__(self, app, settings, theme_manager=None, parent=None):
        super().__init__(parent)

        self.app = app
        self.settings = settings
        self.theme_manager = theme_manager
        self.parent_widget = parent

        # Animation and visual state
        self._is_blinking = False
        self._blink_timer = QTimer()
        self._blink_timer.timeout.connect(self._blink_animation)
        self._notification_queue = []
        self._current_icon_state = "normal"

        # Create enhanced tray icon
        self.tray_icon = QSystemTrayIcon(parent)
        
        # Create enhanced context menu
        self.tray_menu = RoundMenu(parent=parent)
        self.tray_menu.setObjectName("SystemTrayMenu")
        
        # Setup enhanced components
        self._setup_enhanced_icon()
        self._create_enhanced_menu()
        self._apply_enhanced_styling()
        
        # Connect signals
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.messageClicked.connect(self._on_notification_clicked)

    def _setup_enhanced_icon(self):
        """Setup enhanced icon with dynamic states"""
        # Create base icon with theme awareness
        self._update_icon_for_theme()
        
        # Set tooltip
        self.tray_icon.setToolTip(tr("system_tray.tooltip"))

    def _update_icon_for_theme(self):
        """Update icon based on current theme"""
        if self.theme_manager:
            # Use theme-aware colors
            colors = self.theme_manager.get_theme_colors()
            accent_color = self.theme_manager.ACCENT_COLORS.get(
                self.theme_manager.get_current_accent(), '#0078D4'
            )
            icon = self._create_dynamic_icon(accent_color)
        else:
            # Fallback to system icon
            icon = self.app.style().standardIcon(
                self.app.style().StandardPixmap.SP_MediaPlay
            )
        
        self.tray_icon.setIcon(icon)

    def _create_dynamic_icon(self, accent_color: str) -> QIcon:
        """Create dynamic icon with accent color"""
        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw modern circular icon
        painter.setBrush(QColor(accent_color))
        painter.setPen(QColor(accent_color))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw play symbol
        painter.setBrush(QColor("white"))
        painter.setPen(QColor("white"))
        
        # Create triangle for play button
        triangle = [
            (12, 10),
            (12, 22),
            (22, 16)
        ]
        
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QPolygon
        
        points = [QPoint(x, y) for x, y in triangle]
        polygon = QPolygon(points)
        painter.drawPolygon(polygon)
        
        painter.end()
        return QIcon(pixmap)

    def _create_enhanced_menu(self):
        """Create enhanced context menu with modern design"""
        # Clear existing menu
        self.tray_menu.clear()
        
        # Show/Hide window
        self.show_action = Action(FIF.VIEW, tr("system_tray.menu.show"))
        self.show_action.triggered.connect(
            lambda: self.action_triggered.emit("show"))
        self.tray_menu.addAction(self.show_action)

        self.hide_action = Action(FIF.HIDE, tr("system_tray.menu.hide"))
        self.hide_action.triggered.connect(
            lambda: self.action_triggered.emit("hide"))
        self.tray_menu.addAction(self.hide_action)

        self.tray_menu.addSeparator()

        # Task control with enhanced icons
        self.start_all_action = Action(FIF.PLAY, tr("system_tray.menu.start_all"))
        self.start_all_action.triggered.connect(
            lambda: self.action_triggered.emit("start_all"))
        self.tray_menu.addAction(self.start_all_action)

        self.pause_all_action = Action(FIF.PAUSE, tr("system_tray.menu.pause_all"))
        self.pause_all_action.triggered.connect(
            lambda: self.action_triggered.emit("pause_all"))
        self.tray_menu.addAction(self.pause_all_action)

        self.stop_all_action = Action(FIF.STOP, tr("system_tray.menu.stop_all"))
        self.stop_all_action.triggered.connect(
            lambda: self.action_triggered.emit("stop_all"))
        self.tray_menu.addAction(self.stop_all_action)

        self.tray_menu.addSeparator()

        # Quick actions
        self.new_task_action = Action(FIF.ADD, tr("system_tray.menu.new_task"))
        self.new_task_action.triggered.connect(
            lambda: self.action_triggered.emit("new_task"))
        self.tray_menu.addAction(self.new_task_action)

        self.settings_action = Action(FIF.SETTING, tr("system_tray.menu.settings"))
        self.settings_action.triggered.connect(
            lambda: self.action_triggered.emit("settings"))
        self.tray_menu.addAction(self.settings_action)

        self.tray_menu.addSeparator()

        # Exit
        self.exit_action = Action(FIF.POWER_BUTTON, tr("system_tray.menu.exit"))
        self.exit_action.triggered.connect(
            lambda: self.action_triggered.emit("exit"))
        self.tray_menu.addAction(self.exit_action)

        # Set context menu
        self.tray_icon.setContextMenu(self.tray_menu)

    def _apply_enhanced_styling(self):
        """Apply enhanced styling to menu"""
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            accent_color = self.theme_manager.ACCENT_COLORS.get(
                self.theme_manager.get_current_accent(), '#0078D4'
            )
            
            # Apply enhanced menu styling
            self.tray_menu.setStyleSheet(f"""
                RoundMenu {{
                    background-color: {colors.get('surface', '#FFFFFF')};
                    border: 1px solid {colors.get('border', '#E5E7EB')};
                    border-radius: 8px;
                    padding: 4px;
                }}
                QMenu::item {{
                    background-color: transparent;
                    color: {colors.get('text_primary', '#1F2937')};
                    padding: 8px 16px;
                    border-radius: 4px;
                    margin: 2px;
                }}
                QMenu::item:selected {{
                    background-color: {accent_color}15;
                    color: {accent_color};
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {colors.get('border', '#E5E7EB')};
                    margin: 4px 12px;
                }}
            """)

    def _on_tray_activated(self, reason):
        """Handle tray icon activation with enhanced behavior"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - toggle window
            if self.parent_widget is not None:
                if self.parent_widget.isVisible():
                    self.action_triggered.emit("hide")
                else:
                    self.action_triggered.emit("show")
            else:
                self.action_triggered.emit("show")
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click - always show window
            self.action_triggered.emit("show")
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            # Middle click - quick action
            self.action_triggered.emit("new_task")

    def _on_notification_clicked(self):
        """Handle notification click"""
        if self._notification_queue:
            notification_data = self._notification_queue.pop(0)
            self.notification_clicked.emit(notification_data.get('action', 'show'))

    def show_enhanced_notification(self, title: str, message: str,
                                 notification_type: str = "info",
                                 duration: int = 5000,
                                 action_data: Optional[str] = None):
        """Show enhanced notification with modern styling"""
        if not self.settings.get("ui", "show_notifications", True):
            return

        # Store notification data for click handling
        if action_data:
            self._notification_queue.append({
                'title': title,
                'message': message,
                'action': action_data
            })

        # Use appropriate icon based on type
        icon_map = {
            "info": QSystemTrayIcon.MessageIcon.Information,
            "warning": QSystemTrayIcon.MessageIcon.Warning,
            "error": QSystemTrayIcon.MessageIcon.Critical,
            "success": QSystemTrayIcon.MessageIcon.Information
        }
        
        icon = icon_map.get(notification_type, QSystemTrayIcon.MessageIcon.Information)
        
        # Show notification
        self.tray_icon.showMessage(title, message, icon, duration)
        
        # Start blinking animation for important notifications
        if notification_type in ["warning", "error"]:
            self._start_blink_animation()

    def _start_blink_animation(self):
        """Start blinking animation for attention"""
        if not self._is_blinking:
            self._is_blinking = True
            self._blink_timer.start(500)  # Blink every 500ms

    def _stop_blink_animation(self):
        """Stop blinking animation"""
        self._is_blinking = False
        self._blink_timer.stop()
        self._update_icon_for_theme()

    def _blink_animation(self):
        """Handle blink animation frame"""
        if self._current_icon_state == "normal":
            self._current_icon_state = "alert"
            # Create alert icon (e.g., red or orange)
            if self.theme_manager:
                alert_icon = self._create_dynamic_icon("#FF4444")
                self.tray_icon.setIcon(alert_icon)
        else:
            self._current_icon_state = "normal"
            self._update_icon_for_theme()

    def update_menu_state(self, running_tasks: int = 0, paused_tasks: int = 0):
        """Update menu state based on task status"""
        has_running = running_tasks > 0
        has_paused = paused_tasks > 0
        has_tasks = has_running or has_paused

        # Update action states
        self.start_all_action.setEnabled(not has_running or has_paused)
        self.pause_all_action.setEnabled(has_running)
        self.stop_all_action.setEnabled(has_tasks)

        # Update tooltip with status information
        if has_running:
            tooltip = tr("system_tray.tooltip_running", count=running_tasks)
            if has_paused:
                tooltip += f" ({paused_tasks} paused)"
        elif has_paused:
            tooltip = tr("system_tray.tooltip_paused", count=paused_tasks)
        else:
            tooltip = tr("system_tray.tooltip")

        self.tray_icon.setToolTip(tooltip)

        # Stop blinking if all tasks are handled
        if not has_running and not has_paused:
            self._stop_blink_animation()

    def update_theme(self, theme_manager: Optional[EnhancedThemeManager] = None):
        """Update theme styling"""
        if theme_manager:
            self.theme_manager = theme_manager
        
        self._update_icon_for_theme()
        self._apply_enhanced_styling()

    def show_progress_notification(self, title: str, progress: int, total: int):
        """Show progress notification"""
        percentage = int((progress / total) * 100) if total > 0 else 0
        message = f"Progress: {progress}/{total} ({percentage}%)"
        self.show_enhanced_notification(title, message, "info", 3000)

    def show_completion_notification(self, task_name: str, success: bool = True):
        """Show task completion notification"""
        if success:
            title = tr("system_tray.notifications.task_completed")
            message = tr("system_tray.notifications.task_success", task=task_name)
            self.show_enhanced_notification(title, message, "success", 4000, "show")
        else:
            title = tr("system_tray.notifications.task_failed")
            message = tr("system_tray.notifications.task_error", task=task_name)
            self.show_enhanced_notification(title, message, "error", 6000, "show")

    def show_system_notification(self, message: str, level: str = "info"):
        """Show system-level notification"""
        title = tr("system_tray.notifications.system_message")
        self.show_enhanced_notification(title, message, level, 5000)

    def show(self):
        """Show tray icon"""
        self.tray_icon.show()

    def hide(self):
        """Hide tray icon"""
        self.tray_icon.hide()
        self._stop_blink_animation()

    def is_supported(self):
        """Check if system tray is supported"""
        return QSystemTrayIcon.isSystemTrayAvailable()

    def cleanup(self):
        """Clean up resources"""
        self._stop_blink_animation()
        if self.tray_icon:
            self.tray_icon.hide()


# Backward compatibility alias
SystemTrayIcon = EnhancedSystemTrayIcon

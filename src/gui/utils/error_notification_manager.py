"""
Error Notification Manager for VidTanium
Manages error notifications, user feedback, and action handling
"""

import time
from typing import Optional, Dict, Any, Callable, List
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtWidgets import QWidget

from qfluentwidgets import InfoBar, InfoBarPosition, FluentIcon as FIF

from ..widgets.error_dialog import ErrorDialog as EnhancedErrorDialog
from src.core.exceptions import VidTaniumException, ErrorSeverity, ErrorCategory, UserAction
from src.core.error_handler import ErrorReport, EnhancedErrorHandler
from .i18n import tr
from loguru import logger


class ErrorNotificationManager(QObject):
    """Manages error notifications and user interactions"""
    
    # Signals
    action_requested = Signal(str, str, dict)  # task_id, action_type, action_data
    retry_requested = Signal(str)  # task_id
    error_dismissed = Signal(str)  # task_id
    
    def __init__(self, parent_widget: QWidget, error_handler: EnhancedErrorHandler):
        super().__init__()
        self.parent_widget = parent_widget
        self.error_handler = error_handler
        self.active_dialogs: Dict[str, EnhancedErrorDialog] = {}
        self.notification_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
        # Auto-dismiss timer for non-critical errors
        self.auto_dismiss_timer = QTimer()
        self.auto_dismiss_timer.timeout.connect(self._auto_dismiss_notifications)
        self.auto_dismiss_timer.start(30000)  # Check every 30 seconds
    
    def show_error(
        self,
        exception: VidTaniumException,
        task_id: Optional[str] = None,
        retry_count: int = 0,
        show_dialog: Optional[bool] = None
    ):
        """Show error notification with appropriate UI"""
        
        # Create error report
        error_report = self.error_handler.create_error_report(exception, retry_count)
        
        # Determine if we should show dialog
        if show_dialog is None:
            show_dialog = self._should_show_dialog(error_report)
        
        # Add to history
        self._add_to_history(error_report, task_id)
        
        if show_dialog:
            self._show_error_dialog(error_report, task_id)
        else:
            self._show_error_infobar(error_report, task_id)
    
    def _should_show_dialog(self, error_report: ErrorReport) -> bool:
        """Determine if error should show dialog vs InfoBar"""
        
        # Always show dialog for critical errors
        if error_report.severity == ErrorSeverity.CRITICAL:
            return True
        
        # Show dialog for high severity errors with actions
        if error_report.severity == ErrorSeverity.HIGH and error_report.suggested_actions:
            return True
        
        # Show dialog for authentication/validation errors (user input needed)
        if error_report.category in [ErrorCategory.AUTHENTICATION, ErrorCategory.VALIDATION]:
            return True
        
        # Show dialog if there are high-priority manual actions
        high_priority_manual_actions = [
            action for action in error_report.suggested_actions
            if action.priority <= 2 and not action.is_automatic
        ]
        if high_priority_manual_actions:
            return True
        
        return False
    
    def _show_error_dialog(self, error_report: ErrorReport, task_id: Optional[str]):
        """Show enhanced error dialog"""
        
        # Close existing dialog for this task if any
        if task_id and task_id in self.active_dialogs:
            self.active_dialogs[task_id].close()
            del self.active_dialogs[task_id]
        
        # Create new dialog
        dialog = EnhancedErrorDialog(error_report, self.parent_widget)
        
        # Connect signals
        dialog.action_requested.connect(
            lambda action_type, action_data: self._handle_action_request(
                task_id, action_type, action_data
            )
        )
        dialog.retry_requested.connect(
            lambda: self._handle_retry_request(task_id)
        )
        dialog.dismiss_requested.connect(
            lambda: self._handle_dismiss_request(task_id)
        )
        
        # Store dialog reference
        if task_id:
            self.active_dialogs[task_id] = dialog
        
        # Show dialog
        dialog.show()
        
        logger.info(f"Showed error dialog for task {task_id}: {error_report.title}")
    
    def _show_error_infobar(self, error_report: ErrorReport, task_id: Optional[str]):
        """Show error as InfoBar notification"""
        
        # Determine InfoBar type based on severity
        if error_report.severity == ErrorSeverity.CRITICAL:
            info_bar_func = InfoBar.error
            duration = 10000  # 10 seconds
            icon = FIF.CANCEL
        elif error_report.severity == ErrorSeverity.HIGH:
            info_bar_func = InfoBar.error
            duration = 8000  # 8 seconds
            icon = FIF.WARNING
        elif error_report.severity == ErrorSeverity.MEDIUM:
            info_bar_func = InfoBar.warning
            duration = 6000  # 6 seconds
            icon = FIF.INFO
        else:
            info_bar_func = InfoBar.info
            duration = 4000  # 4 seconds
            icon = FIF.INFO
        
        # Create InfoBar with action buttons if applicable
        content = error_report.message
        if len(content) > 100:
            content = content[:97] + "..."
        
        info_bar = info_bar_func(
            title=error_report.title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self.parent_widget
        )
        
        # Add action buttons for high-priority actions
        high_priority_actions = [
            action for action in error_report.suggested_actions
            if action.priority <= 2
        ]
        
        for action in high_priority_actions[:2]:  # Limit to 2 actions in InfoBar
            action_button = info_bar.addAction(action.description)
            action_button.clicked.connect(
                lambda checked, a=action: self._handle_action_request(
                    task_id, a.action_type, {
                        "action_type": a.action_type,
                        "description": a.description,
                        "is_automatic": a.is_automatic,
                        "priority": a.priority
                    }
                )
            )
        
        logger.info(f"Showed error InfoBar for task {task_id}: {error_report.title}")
    
    def _handle_action_request(self, task_id: Optional[str], action_type: str, action_data: Dict[str, Any]):
        """Handle user action request"""
        logger.info(f"Action requested for task {task_id}: {action_type}")
        
        # Emit signal for external handling
        if task_id:
            self.action_requested.emit(task_id, action_type, action_data)
        
        # Handle common actions internally
        if action_type == "retry":
            self._handle_retry_request(task_id)
        elif action_type == "show_details":
            # TODO: Implement show_details method
            pass
        elif action_type == "copy_details":
            # TODO: Implement copy_details method
            pass
    
    def _handle_retry_request(self, task_id: Optional[str]):
        """Handle retry request"""
        logger.info(f"Retry requested for task {task_id}")
        
        # Close dialog if open
        if task_id and task_id in self.active_dialogs:
            self.active_dialogs[task_id].close()
            del self.active_dialogs[task_id]
        
        # Emit retry signal
        if task_id:
            self.retry_requested.emit(task_id)
    
    def _handle_dismiss_request(self, task_id: Optional[str]):
        """Handle dismiss request"""
        logger.info(f"Error dismissed for task {task_id}")
        
        # Close dialog if open
        if task_id and task_id in self.active_dialogs:
            self.active_dialogs[task_id].close()
            del self.active_dialogs[task_id]
        
        # Emit dismiss signal
        if task_id:
            self.error_dismissed.emit(task_id)
    
    def _add_to_history(self, error_report: ErrorReport, task_id: Optional[str]):
        """Add error to notification history"""
        history_entry = {
            "timestamp": time.time(),
            "task_id": task_id,
            "title": error_report.title,
            "message": error_report.message,
            "category": error_report.category.value,
            "severity": error_report.severity.value,
            "retry_count": error_report.retry_count
        }
        
        self.notification_history.append(history_entry)
        
        # Trim history if too large
        if len(self.notification_history) > self.max_history_size:
            self.notification_history = self.notification_history[-self.max_history_size:]
    
    def _auto_dismiss_notifications(self):
        """Auto-dismiss old notifications"""
        current_time = time.time()
        
        # Remove old history entries (older than 1 hour)
        self.notification_history = [
            entry for entry in self.notification_history
            if current_time - entry["timestamp"] < 3600
        ]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error notification statistics"""
        if not self.notification_history:
            return {}
        
        recent_errors = [
            entry for entry in self.notification_history
            if time.time() - entry["timestamp"] < 3600  # Last hour
        ]
        
        category_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}
        
        for entry in recent_errors:
            category = entry["category"]
            severity = entry["severity"]
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_notifications_last_hour": len(recent_errors),
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "active_dialogs": len(self.active_dialogs)
        }
    
    def close_all_dialogs(self):
        """Close all active error dialogs"""
        for dialog in list(self.active_dialogs.values()):
            dialog.close()
        self.active_dialogs.clear()
    
    def has_active_dialog(self, task_id: str) -> bool:
        """Check if task has active error dialog"""
        return task_id in self.active_dialogs


class ErrorActionHandler:
    """Handles common error actions"""
    
    def __init__(self):
        self.action_handlers: Dict[str, Callable] = {
            "check_connection": self._check_connection,
            "check_permissions": self._check_permissions,
            "free_space": self._free_space,
            "check_url": self._check_url,
            "increase_timeout": self._increase_timeout,
            "reduce_concurrent": self._reduce_concurrent,
            "restart_app": self._restart_app,
            "reset_settings": self._reset_settings
        }
    
    def handle_action(self, action_type: str, action_data: Dict[str, Any]) -> bool:
        """Handle error action"""
        handler = self.action_handlers.get(action_type)
        if handler:
            try:
                return bool(handler(action_data))
            except Exception as e:
                logger.error(f"Error handling action {action_type}: {e}")
                return False
        else:
            logger.warning(f"No handler for action type: {action_type}")
            return False
    
    def _check_connection(self, action_data: Dict[str, Any]) -> bool:
        """Handle check connection action"""
        # This would typically open network diagnostics or show connection status
        logger.info("User requested connection check")
        return True
    
    def _check_permissions(self, action_data: Dict[str, Any]) -> bool:
        """Handle check permissions action"""
        # This would typically show file/folder permissions dialog
        logger.info("User requested permissions check")
        return True
    
    def _free_space(self, action_data: Dict[str, Any]) -> bool:
        """Handle free space action"""
        # This would typically open disk cleanup or show storage usage
        logger.info("User requested disk space management")
        return True
    
    def _check_url(self, action_data: Dict[str, Any]) -> bool:
        """Handle check URL action"""
        # This would typically validate or test the URL
        logger.info("User requested URL validation")
        return True
    
    def _increase_timeout(self, action_data: Dict[str, Any]) -> bool:
        """Handle increase timeout action"""
        # This would typically open settings to adjust timeout
        logger.info("User requested timeout increase")
        return True
    
    def _reduce_concurrent(self, action_data: Dict[str, Any]) -> bool:
        """Handle reduce concurrent downloads action"""
        # This would typically adjust concurrent download settings
        logger.info("User requested concurrent download reduction")
        return True
    
    def _restart_app(self, action_data: Dict[str, Any]) -> bool:
        """Handle restart application action"""
        # This would typically show restart confirmation
        logger.info("User requested application restart")
        return True
    
    def _reset_settings(self, action_data: Dict[str, Any]) -> bool:
        """Handle reset settings action"""
        # This would typically show settings reset confirmation
        logger.info("User requested settings reset")
        return True


# Global instances
error_notification_manager = None  # Will be initialized with parent widget
error_action_handler = ErrorActionHandler()

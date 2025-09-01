"""
Contextual Help Manager for VidTanium
Provides intelligent contextual help, tooltips, and action suggestions based on current state
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from PySide6.QtWidgets import QWidget, QToolTip, QApplication
from PySide6.QtCore import QObject, Signal, QTimer, QPoint
from PySide6.QtGui import QCursor

from ..widgets.tooltip import EnhancedTooltip
from ..utils.i18n import tr
from loguru import logger


class HelpContext(Enum):
    """Different contexts where help can be provided"""
    TASK_CREATION = "task_creation"
    DOWNLOAD_PROGRESS = "download_progress"
    ERROR_STATE = "error_state"
    SETTINGS = "settings"
    BATCH_OPERATIONS = "batch_operations"
    TASK_MANAGEMENT = "task_management"


class ActionPriority(Enum):
    """Priority levels for suggested actions"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class HelpContent:
    """Content for contextual help"""
    title: str
    description: str
    detailed_info: Optional[str] = None
    learn_more_url: Optional[str] = None
    related_settings: Optional[List[str]] = None


@dataclass
class SuggestedAction:
    """Suggested action with contextual information"""
    action_id: str
    title: str
    description: str
    icon: str
    priority: ActionPriority
    callback: Optional[Callable] = None
    conditions: Optional[Dict[str, Any]] = None
    help_text: Optional[str] = None


class ContextualHelpManager(QObject):
    """Manages contextual help and smart suggestions"""
    
    help_requested = Signal(str, dict)  # context, data
    action_suggested = Signal(str, dict)  # action_id, action_data
    
    def __init__(self):
        super().__init__()
        self.help_content: Dict[str, Dict[str, HelpContent]] = {}
        self.suggested_actions: Dict[str, List[SuggestedAction]] = {}
        self.active_tooltips: Dict[QWidget, EnhancedTooltip] = {}
        self.context_history: List[str] = []
        self.user_preferences: Dict[str, Any] = {}
        
        # Timer for delayed tooltip showing
        self.tooltip_timer = QTimer()
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self._show_delayed_tooltip)
        
        self._initialize_help_content()
        self._initialize_suggested_actions()
    
    def _initialize_help_content(self):
        """Initialize help content for different contexts"""
        
        # Task Creation Help
        self.help_content[HelpContext.TASK_CREATION.value] = {
            "url_input": HelpContent(
                title=tr("help.url_input.title"),
                description=tr("help.url_input.description"),
                detailed_info=tr("help.url_input.detailed"),
                related_settings=["network.timeout", "network.user_agent"]
            ),
            "output_path": HelpContent(
                title=tr("help.output_path.title"),
                description=tr("help.output_path.description"),
                detailed_info=tr("help.output_path.detailed"),
                related_settings=["general.default_download_path"]
            ),
            "quality_selection": HelpContent(
                title=tr("help.quality_selection.title"),
                description=tr("help.quality_selection.description"),
                detailed_info=tr("help.quality_selection.detailed")
            )
        }
        
        # Download Progress Help
        self.help_content[HelpContext.DOWNLOAD_PROGRESS.value] = {
            "speed_optimization": HelpContent(
                title=tr("help.speed_optimization.title"),
                description=tr("help.speed_optimization.description"),
                detailed_info=tr("help.speed_optimization.detailed"),
                related_settings=["download.max_workers_per_task", "download.chunk_size"]
            ),
            "pause_resume": HelpContent(
                title=tr("help.pause_resume.title"),
                description=tr("help.pause_resume.description"),
                detailed_info=tr("help.pause_resume.detailed")
            ),
            "progress_tracking": HelpContent(
                title=tr("help.progress_tracking.title"),
                description=tr("help.progress_tracking.description"),
                detailed_info=tr("help.progress_tracking.detailed")
            )
        }
        
        # Error State Help
        self.help_content[HelpContext.ERROR_STATE.value] = {
            "network_errors": HelpContent(
                title=tr("help.network_errors.title"),
                description=tr("help.network_errors.description"),
                detailed_info=tr("help.network_errors.detailed"),
                related_settings=["download.max_retries", "download.retry_delay"]
            ),
            "file_errors": HelpContent(
                title=tr("help.file_errors.title"),
                description=tr("help.file_errors.description"),
                detailed_info=tr("help.file_errors.detailed")
            ),
            "authentication_errors": HelpContent(
                title=tr("help.authentication_errors.title"),
                description=tr("help.authentication_errors.description"),
                detailed_info=tr("help.authentication_errors.detailed")
            )
        }
        
        # Settings Help
        self.help_content[HelpContext.SETTINGS.value] = {
            "concurrent_downloads": HelpContent(
                title=tr("help.concurrent_downloads.title"),
                description=tr("help.concurrent_downloads.description"),
                detailed_info=tr("help.concurrent_downloads.detailed")
            ),
            "bandwidth_limiting": HelpContent(
                title=tr("help.bandwidth_limiting.title"),
                description=tr("help.bandwidth_limiting.description"),
                detailed_info=tr("help.bandwidth_limiting.detailed")
            ),
            "auto_cleanup": HelpContent(
                title=tr("help.auto_cleanup.title"),
                description=tr("help.auto_cleanup.description"),
                detailed_info=tr("help.auto_cleanup.detailed")
            )
        }
    
    def _initialize_suggested_actions(self):
        """Initialize suggested actions for different contexts"""
        
        # Task Creation Actions
        self.suggested_actions[HelpContext.TASK_CREATION.value] = [
            SuggestedAction(
                action_id="validate_url",
                title=tr("actions.validate_url.title"),
                description=tr("actions.validate_url.description"),
                icon="globe",
                priority=ActionPriority.HIGH,
                help_text=tr("actions.validate_url.help")
            ),
            SuggestedAction(
                action_id="choose_quality",
                title=tr("actions.choose_quality.title"),
                description=tr("actions.choose_quality.description"),
                icon="video",
                priority=ActionPriority.MEDIUM,
                help_text=tr("actions.choose_quality.help")
            ),
            SuggestedAction(
                action_id="set_output_path",
                title=tr("actions.set_output_path.title"),
                description=tr("actions.set_output_path.description"),
                icon="folder",
                priority=ActionPriority.MEDIUM,
                help_text=tr("actions.set_output_path.help")
            )
        ]
        
        # Download Progress Actions
        self.suggested_actions[HelpContext.DOWNLOAD_PROGRESS.value] = [
            SuggestedAction(
                action_id="optimize_speed",
                title=tr("actions.optimize_speed.title"),
                description=tr("actions.optimize_speed.description"),
                icon="speed",
                priority=ActionPriority.MEDIUM,
                conditions={"speed_below_threshold": True},
                help_text=tr("actions.optimize_speed.help")
            ),
            SuggestedAction(
                action_id="pause_other_tasks",
                title=tr("actions.pause_other_tasks.title"),
                description=tr("actions.pause_other_tasks.description"),
                icon="pause",
                priority=ActionPriority.LOW,
                conditions={"multiple_active_tasks": True},
                help_text=tr("actions.pause_other_tasks.help")
            )
        ]
        
        # Error State Actions
        self.suggested_actions[HelpContext.ERROR_STATE.value] = [
            SuggestedAction(
                action_id="retry_with_different_settings",
                title=tr("actions.retry_different_settings.title"),
                description=tr("actions.retry_different_settings.description"),
                icon="refresh",
                priority=ActionPriority.HIGH,
                help_text=tr("actions.retry_different_settings.help")
            ),
            SuggestedAction(
                action_id="check_network_connection",
                title=tr("actions.check_network.title"),
                description=tr("actions.check_network.description"),
                icon="wifi",
                priority=ActionPriority.HIGH,
                conditions={"error_type": "network"},
                help_text=tr("actions.check_network.help")
            ),
            SuggestedAction(
                action_id="free_disk_space",
                title=tr("actions.free_disk_space.title"),
                description=tr("actions.free_disk_space.description"),
                icon="storage",
                priority=ActionPriority.CRITICAL,
                conditions={"error_type": "disk_space"},
                help_text=tr("actions.free_disk_space.help")
            )
        ]
    
    def show_contextual_help(
        self,
        widget: QWidget,
        context: HelpContext,
        help_key: str,
        position: Optional[QPoint] = None,
        delay: int = 500
    ):
        """Show contextual help for a widget"""
        
        help_content = self.help_content.get(context.value, {}).get(help_key)
        if not help_content:
            logger.warning(f"No help content found for {context.value}.{help_key}")
            return
        
        # Store tooltip data for delayed showing
        self.pending_tooltip_data = {
            "widget": widget,
            "content": help_content,
            "position": position or QCursor.pos()
        }
        
        # Start delay timer
        self.tooltip_timer.start(delay)
    
    def _show_delayed_tooltip(self):
        """Show tooltip after delay"""
        if not hasattr(self, 'pending_tooltip_data'):
            return
        
        data = self.pending_tooltip_data
        widget = data["widget"]
        content = data["content"]
        position = data["position"]
        
        # Create enhanced tooltip
        tooltip = EnhancedTooltip(
            title=content.title,
            description=content.description,
            detailed_info=content.detailed_info,
            learn_more_url=content.learn_more_url
        )
        
        # Show tooltip at position
        tooltip.show_at_position(position)
        
        # Store reference
        self.active_tooltips[widget] = tooltip
        
        # Clean up when tooltip is closed
        tooltip.closed.connect(lambda: self._cleanup_tooltip(widget))
    
    def hide_contextual_help(self, widget: QWidget):
        """Hide contextual help for a widget"""
        if widget in self.active_tooltips:
            self.active_tooltips[widget].hide()
            del self.active_tooltips[widget]
    
    def get_suggested_actions(
        self,
        context: HelpContext,
        current_state: Optional[Dict[str, Any]] = None
    ) -> List[SuggestedAction]:
        """Get suggested actions for current context and state"""
        
        actions = self.suggested_actions.get(context.value, [])
        filtered_actions = []
        
        for action in actions:
            # Check if action conditions are met
            if action.conditions and current_state:
                conditions_met = all(
                    current_state.get(key) == value
                    for key, value in action.conditions.items()
                )
                if not conditions_met:
                    continue
            
            filtered_actions.append(action)
        
        # Sort by priority
        filtered_actions.sort(key=lambda x: x.priority.value)
        
        return filtered_actions
    
    def get_smart_suggestions(
        self,
        context: HelpContext,
        task_data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Get smart suggestions based on context and task data"""
        
        suggestions = []
        
        if context == HelpContext.TASK_CREATION:
            if task_data and not task_data.get("url"):
                suggestions.append(tr("suggestions.enter_url"))
            if task_data and not task_data.get("output_path"):
                suggestions.append(tr("suggestions.choose_output_path"))
        
        elif context == HelpContext.DOWNLOAD_PROGRESS:
            if task_data:
                speed = task_data.get("speed", 0)
                if speed < 100000:  # Less than 100 KB/s
                    suggestions.append(tr("suggestions.slow_speed"))
                
                error_count = task_data.get("error_count", 0)
                if error_count > 3:
                    suggestions.append(tr("suggestions.many_errors"))
        
        elif context == HelpContext.ERROR_STATE:
            if task_data:
                error_type = task_data.get("error_type")
                if error_type == "network":
                    suggestions.append(tr("suggestions.network_error"))
                elif error_type == "disk_space":
                    suggestions.append(tr("suggestions.disk_space_error"))
                elif error_type == "permission":
                    suggestions.append(tr("suggestions.permission_error"))
        
        return suggestions
    
    def update_user_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences for help system"""
        self.user_preferences.update(preferences)
    
    def should_show_help(self, help_key: str) -> bool:
        """Determine if help should be shown based on user preferences"""
        # Check if user has disabled this specific help
        if self.user_preferences.get(f"disable_help_{help_key}", False):
            return False
        
        # Check global help setting
        if not self.user_preferences.get("show_contextual_help", True):
            return False
        
        return True
    
    def mark_help_as_seen(self, help_key: str):
        """Mark help as seen by user"""
        self.user_preferences[f"help_seen_{help_key}"] = True
    
    def _cleanup_tooltip(self, widget: QWidget):
        """Clean up tooltip reference"""
        if widget in self.active_tooltips:
            del self.active_tooltips[widget]
    
    def get_help_statistics(self) -> Dict[str, Any]:
        """Get help system usage statistics"""
        return {
            "active_tooltips": len(self.active_tooltips),
            "context_history_length": len(self.context_history),
            "help_content_count": sum(len(content) for content in self.help_content.values()),
            "suggested_actions_count": sum(len(actions) for actions in self.suggested_actions.values())
        }


# Global contextual help manager instance
contextual_help_manager = ContextualHelpManager()

"""
VidTanium GUI Module
Enhanced user interface components with improved error handling and user interactions
"""

# Error handling UI components
from .widgets.error_dialog import ErrorDialog
from .widgets.status_widget import StatusWidget, StatusInfo
from .dialogs.confirmation_dialog import ConfirmationDialog, create_delete_confirmation, create_cancel_confirmation
from .widgets.tooltip import Tooltip, SmartTooltipMixin, create_quick_tooltip
from .widgets.analytics_dashboard import AnalyticsDashboard, MetricCard, ETADisplayWidget, BandwidthAnalyticsWidget
from .widgets.bulk_operations_manager import BulkOperationsManager, SelectionWidget, BulkActionsWidget

# Utility components
from .utils.error_notification_manager import ErrorNotificationManager, ErrorActionHandler
from .utils.contextual_help_manager import ContextualHelpManager, contextual_help_manager

__all__ = [
    # Error handling widgets
    'ErrorDialog',
    'StatusWidget',
    'StatusInfo',
    'ConfirmationDialog',
    'create_delete_confirmation',
    'create_cancel_confirmation',
    'Tooltip',
    'SmartTooltipMixin',
    'create_quick_tooltip',

    # Analytics and dashboard widgets
    'AnalyticsDashboard',
    'MetricCard',
    'ETADisplayWidget',
    'BandwidthAnalyticsWidget',

    # Bulk operations widgets
    'BulkOperationsManager',
    'SelectionWidget',
    'BulkActionsWidget',

    # Utility managers
    'ErrorNotificationManager',
    'ErrorActionHandler',
    'ContextualHelpManager',
    'contextual_help_manager'
]


def initialize_gui_systems(parent_widget, error_handler):
    """Initialize all GUI systems with proper dependencies"""
    from .utils.error_notification_manager import error_notification_manager

    # Initialize error notification manager with parent widget
    global error_notification_manager
    error_notification_manager = ErrorNotificationManager(parent_widget, error_handler)

    # Initialize contextual help manager
    contextual_help_manager.update_user_preferences({
        'show_contextual_help': True,
        'help_delay_ms': 500
    })

    return {
        'error_notification_manager': error_notification_manager,
        'contextual_help_manager': contextual_help_manager
    }
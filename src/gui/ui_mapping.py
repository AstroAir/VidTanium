"""
UI Component Mapping System for VidTanium
Provides centralized mapping and registration for all UI components
"""

from typing import Dict, Type, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass
from PySide6.QtWidgets import QWidget, QDialog, QMainWindow
from qfluentwidgets import FluentIcon as FIF

# Import UI components
from .main_window import MainWindow
from .component_registry import ComponentType, ComponentRegistry

# Dialogs
from .dialogs.about_dialog import AboutDialog
from .dialogs.task_dialog import TaskDialog
from .dialogs.batch_url_dialog import BatchURLDialog
from .dialogs.confirmation_dialog import ConfirmationDialog
from .dialogs.media_processing_dialog import MediaProcessingDialog
from .dialogs.schedule_dialog import ScheduleDialog
from .dialogs.settings.settings_dialog import SettingsDialog

# Widgets
from .widgets.task_manager import TaskManager
from .widgets.log_viewer import LogViewer
from .widgets.analytics_dashboard import AnalyticsDashboard
from .widgets.bulk_operations_manager import BulkOperationsManager
from .widgets.status_widget import StatusWidget
from .widgets.system_tray import EnhancedSystemTrayIcon
from .widgets.error_dialog import ErrorDialog
from .widgets.tooltip import Tooltip
from .widgets.progress import ProgressCard, ProgressSummaryCard
from .widgets.navigation import NavigationPanel, ModernBreadcrumb
from .widgets.dashboard import DashboardInterface

# Dashboard components
from .widgets.dashboard.dashboard_interface import DashboardInterface
from .widgets.dashboard.hero_section import DashboardHeroSection
from .widgets.dashboard.stats_section import DashboardStatsSection
from .widgets.dashboard.system_status import DashboardSystemStatus
from .widgets.dashboard.task_preview import DashboardTaskPreview

# Settings components
from .widgets.settings.settings_interface import SettingsInterface

# Utils
from .utils.theme_manager import ThemeManager
from .utils.responsive import ResponsiveManager
from .utils.error_notification_manager import ErrorNotificationManager
from .utils.contextual_help_manager import ContextualHelpManager


class UIComponentCategory(Enum):
    """UI component categories for better organization"""
    MAIN_WINDOW = "main_window"
    DIALOG = "dialog"
    WIDGET = "widget"
    DASHBOARD = "dashboard"
    NAVIGATION = "navigation"
    SETTINGS = "settings"
    UTILITY = "utility"
    MANAGER = "manager"


@dataclass
class ComponentMapping:
    """Component mapping information"""
    component_id: str
    component_class: Type
    category: UIComponentCategory
    description: str
    dependencies: Optional[List[str]] = None
    icon: Optional[Any] = None
    route: Optional[str] = None


class UIMapping:
    """Central UI component mapping system"""
    
    def __init__(self) -> None:
        self.component_registry = ComponentRegistry()
        self._initialize_mappings()
    
    def _initialize_mappings(self) -> None:
        """Initialize all component mappings"""
        
        # Main window components
        self.MAIN_COMPONENTS = {
            "main_window": ComponentMapping(
                "main_window",
                MainWindow,
                UIComponentCategory.MAIN_WINDOW,
                "Primary application window",
                icon=FIF.HOME
            )
        }
        
        # Dialog components
        self.DIALOG_COMPONENTS = {
            "about_dialog": ComponentMapping(
                "about_dialog",
                AboutDialog,
                UIComponentCategory.DIALOG,
                "Application about dialog",
                icon=FIF.INFO
            ),
            "task_dialog": ComponentMapping(
                "task_dialog",
                TaskDialog,
                UIComponentCategory.DIALOG,
                "Task configuration dialog",
                icon=FIF.ADD
            ),
            "batch_url_dialog": ComponentMapping(
                "batch_url_dialog",
                BatchURLDialog,
                UIComponentCategory.DIALOG,
                "Batch URL input dialog",
                icon=FIF.LINK
            ),
            "confirmation_dialog": ComponentMapping(
                "confirmation_dialog",
                ConfirmationDialog,
                UIComponentCategory.DIALOG,
                "User confirmation dialog",
                icon=FIF.QUESTION
            ),
            "media_processing_dialog": ComponentMapping(
                "media_processing_dialog",
                MediaProcessingDialog,
                UIComponentCategory.DIALOG,
                "Media processing options dialog",
                icon=FIF.VIDEO
            ),
            "schedule_dialog": ComponentMapping(
                "schedule_dialog",
                ScheduleDialog,
                UIComponentCategory.DIALOG,
                "Task scheduling dialog",
                icon=FIF.CALENDAR
            ),
            "settings_dialog": ComponentMapping(
                "settings_dialog",
                SettingsDialog,
                UIComponentCategory.DIALOG,
                "Application settings dialog",
                icon=FIF.SETTING
            ),
            "error_dialog": ComponentMapping(
                "error_dialog",
                ErrorDialog,
                UIComponentCategory.DIALOG,
                "Error display dialog",
                icon=FIF.CANCEL
            )
        }
        
        # Widget components
        self.WIDGET_COMPONENTS = {
            "task_manager": ComponentMapping(
                "task_manager",
                TaskManager,
                UIComponentCategory.WIDGET,
                "Task management widget",
                icon=FIF.TILES
            ),
            "log_viewer": ComponentMapping(
                "log_viewer",
                LogViewer,
                UIComponentCategory.WIDGET,
                "Log viewing widget",
                icon=FIF.HISTORY
            ),
            "analytics_dashboard": ComponentMapping(
                "analytics_dashboard",
                AnalyticsDashboard,
                UIComponentCategory.WIDGET,
                "Analytics and metrics dashboard",
                icon=FIF.PIE_SINGLE
            ),
            "bulk_operations_manager": ComponentMapping(
                "bulk_operations_manager",
                BulkOperationsManager,
                UIComponentCategory.WIDGET,
                "Bulk operations management widget",
                icon=FIF.CHECKBOX
            ),
            "status_widget": ComponentMapping(
                "status_widget",
                StatusWidget,
                UIComponentCategory.WIDGET,
                "System status display widget",
                icon=FIF.SPEED_HIGH
            ),
            "system_tray": ComponentMapping(
                "system_tray",
                EnhancedSystemTrayIcon,
                UIComponentCategory.WIDGET,
                "System tray integration",
                icon=FIF.MINIMIZE
            ),
            "tooltip": ComponentMapping(
                "tooltip",
                Tooltip,
                UIComponentCategory.WIDGET,
                "Smart tooltip system",
                icon=FIF.HELP
            ),
            "progress_card": ComponentMapping(
                "progress_card",
                ProgressCard,
                UIComponentCategory.WIDGET,
                "Progress display card",
                icon=FIF.PROGRESS_RING_DOTS
            ),
            "progress_summary_card": ComponentMapping(
                "progress_summary_card",
                ProgressSummaryCard,
                UIComponentCategory.WIDGET,
                "Progress summary display",
                icon=FIF.CHART
            )
        }
        
        # Dashboard components
        self.DASHBOARD_COMPONENTS = {
            "dashboard": ComponentMapping(
                "dashboard",
                DashboardInterface,
                UIComponentCategory.DASHBOARD,
                "Main dashboard interface",
                route="/dashboard",
                icon=FIF.HOME
            ),
            "dashboard_interface": ComponentMapping(
                "dashboard_interface",
                DashboardInterface,
                UIComponentCategory.DASHBOARD,
                "Enhanced dashboard interface",
                route="/dashboard/interface"
            ),
            "hero_section": ComponentMapping(
                "hero_section",
                DashboardHeroSection,
                UIComponentCategory.DASHBOARD,
                "Dashboard hero section"
            ),
            "stats_section": ComponentMapping(
                "stats_section",
                DashboardStatsSection,
                UIComponentCategory.DASHBOARD,
                "Statistics display section"
            ),
            "system_status": ComponentMapping(
                "system_status",
                DashboardSystemStatus,
                UIComponentCategory.DASHBOARD,
                "System status overview"
            ),
            "task_preview": ComponentMapping(
                "task_preview",
                DashboardTaskPreview,
                UIComponentCategory.DASHBOARD,
                "Task preview widget"
            )
        }
        
        # Navigation components
        self.NAVIGATION_COMPONENTS = {
            "navigation_panel": ComponentMapping(
                "navigation_panel",
                NavigationPanel,
                UIComponentCategory.NAVIGATION,
                "Main navigation panel",
                icon=FIF.MENU
            ),
            "modern_breadcrumb": ComponentMapping(
                "modern_breadcrumb",
                ModernBreadcrumb,
                UIComponentCategory.NAVIGATION,
                "Modern breadcrumb navigation",
                icon=FIF.CHEVRON_RIGHT
            )
        }
        
        # Settings components
        self.SETTINGS_COMPONENTS = {
            "settings_interface": ComponentMapping(
                "settings_interface",
                SettingsInterface,
                UIComponentCategory.SETTINGS,
                "Settings management interface",
                route="/settings",
                icon=FIF.SETTING
            )
        }
        
        # Utility managers
        self.UTILITY_COMPONENTS = {
            "theme_manager": ComponentMapping(
                "theme_manager",
                ThemeManager,
                UIComponentCategory.UTILITY,
                "Theme management system"
            ),
            "responsive_manager": ComponentMapping(
                "responsive_manager",
                ResponsiveManager,
                UIComponentCategory.UTILITY,
                "Responsive design manager"
            ),
            "error_notification_manager": ComponentMapping(
                "error_notification_manager",
                ErrorNotificationManager,
                UIComponentCategory.UTILITY,
                "Error notification system"
            ),
            "contextual_help_manager": ComponentMapping(
                "contextual_help_manager",
                ContextualHelpManager,
                UIComponentCategory.UTILITY,
                "Contextual help system"
            )
        }
    
    def get_all_components(self) -> Dict[str, ComponentMapping]:
        """Get all registered components"""
        all_components = {}
        all_components.update(self.MAIN_COMPONENTS)
        all_components.update(self.DIALOG_COMPONENTS)
        all_components.update(self.WIDGET_COMPONENTS)
        all_components.update(self.DASHBOARD_COMPONENTS)
        all_components.update(self.NAVIGATION_COMPONENTS)
        all_components.update(self.SETTINGS_COMPONENTS)
        all_components.update(self.UTILITY_COMPONENTS)
        return all_components
    
    def get_component_by_id(self, component_id: str) -> Optional[ComponentMapping]:
        """Get component mapping by ID"""
        return self.get_all_components().get(component_id)
    
    def get_components_by_category(self, category: UIComponentCategory) -> Dict[str, ComponentMapping]:
        """Get all components in a specific category"""
        all_components = self.get_all_components()
        return {
            comp_id: mapping for comp_id, mapping in all_components.items()
            if mapping.category == category
        }
    
    def register_component_instance(self, component_id: str, instance: Any) -> bool:
        """Register a component instance with the registry"""
        mapping = self.get_component_by_id(component_id)
        if not mapping:
            return False
        
        # Convert category to ComponentType
        component_type_map = {
            UIComponentCategory.MAIN_WINDOW: ComponentType.WINDOW,
            UIComponentCategory.DIALOG: ComponentType.DIALOG,
            UIComponentCategory.WIDGET: ComponentType.WIDGET,
            UIComponentCategory.DASHBOARD: ComponentType.WIDGET,
            UIComponentCategory.NAVIGATION: ComponentType.WIDGET,
            UIComponentCategory.SETTINGS: ComponentType.WIDGET,
            UIComponentCategory.UTILITY: ComponentType.MANAGER,
        }
        
        component_type = component_type_map.get(mapping.category, ComponentType.WIDGET)
        
        self.component_registry.register_component(
            component=instance,
            component_type=component_type,
            component_id=component_id,
            dependencies=mapping.dependencies,
            metadata={
                "description": mapping.description,
                "category": mapping.category.value,
                "icon": mapping.icon,
                "route": mapping.route
            }
        )
        return True


# Global UI mapping instance
ui_mapping = UIMapping()


# Navigation routes mapping
NAVIGATION_ROUTES = {
    "/": "dashboard",
    "/dashboard": "dashboard",
    "/dashboard/interface": "dashboard_interface",
    "/download": "task_manager",
    "/logs": "log_viewer",
    "/analytics": "analytics_dashboard",
    "/help": "help_interface",
    "/help/index": "help_interface",
    "/help/getting-started": "help_interface",
    "/help/user-guide": "help_interface",
    "/help/troubleshooting": "help_interface",
    "/settings": "settings_interface",
    "/settings/general": "settings_interface",
    "/settings/download": "settings_interface",
    "/settings/advanced": "settings_interface",
    "/settings/ui": "settings_interface"
}


# Icon mappings for quick access
COMPONENT_ICONS = {
    "dashboard": FIF.HOME,
    "download": FIF.DOWNLOAD,
    "logs": FIF.HISTORY,
    "analytics": FIF.PIE_SINGLE,
    "settings": FIF.SETTING,
    "tasks": FIF.TILES,
    "schedule": FIF.CALENDAR,
    "media": FIF.VIDEO,
    "batch": FIF.LINK,
    "help": FIF.HELP,
    "about": FIF.INFO
}


def get_component_class(component_id: str) -> Optional[Type]:
    """Get component class by ID"""
    mapping = ui_mapping.get_component_by_id(component_id)
    return mapping.component_class if mapping else None


def get_component_route(component_id: str) -> Optional[str]:
    """Get component route by ID"""
    mapping = ui_mapping.get_component_by_id(component_id)
    return mapping.route if mapping else None


def get_route_component(route: str) -> Optional[str]:
    """Get component ID by route"""
    return NAVIGATION_ROUTES.get(route)

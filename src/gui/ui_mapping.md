# VidTanium UI Component Mapping

## Overview
This document provides a comprehensive mapping of all UI components in the VidTanium application, organized by category and functionality.

## Component Categories

### 1. Main Window Components
| Component ID | Class | Description | Icon | Route |
|-------------|-------|-------------|------|-------|
| `main_window` | `MainWindow` | Primary application window | `FIF.HOME` | - |

### 2. Dialog Components
| Component ID | Class | Description | Icon | Route |
|-------------|-------|-------------|------|-------|
| `about_dialog` | `AboutDialog` | Application about dialog | `FIF.INFO` | - |
| `task_dialog` | `TaskDialog` | Task configuration dialog | `FIF.ADD` | - |
| `batch_url_dialog` | `BatchURLDialog` | Batch URL input dialog | `FIF.LINK` | - |
| `confirmation_dialog` | `ConfirmationDialog` | User confirmation dialog | `FIF.QUESTION` | - |
| `media_processing_dialog` | `MediaProcessingDialog` | Media processing options dialog | `FIF.VIDEO` | - |
| `schedule_dialog` | `ScheduleDialog` | Task scheduling dialog | `FIF.CALENDAR` | - |
| `settings_dialog` | `SettingsDialog` | Application settings dialog | `FIF.SETTING` | - |
| `error_dialog` | `ErrorDialog` | Error display dialog | `FIF.CANCEL` | - |

### 3. Widget Components
| Component ID | Class | Description | Icon | Route |
|-------------|-------|-------------|------|-------|
| `task_manager` | `TaskManager` | Task management widget | `FIF.TILES` | - |
| `log_viewer` | `LogViewer` | Log viewing widget | `FIF.HISTORY` | - |
| `analytics_dashboard` | `AnalyticsDashboard` | Analytics and metrics dashboard | `FIF.PIE_SINGLE` | - |
| `bulk_operations_manager` | `BulkOperationsManager` | Bulk operations management widget | `FIF.CHECKBOX` | - |
| `status_widget` | `StatusWidget` | System status display widget | `FIF.SPEED_HIGH` | - |
| `system_tray` | `SystemTray` | System tray integration | `FIF.MINIMIZE` | - |
| `tooltip` | `Tooltip` | Smart tooltip system | `FIF.HELP` | - |
| `progress_card` | `ProgressCard` | Progress display card | `FIF.PROGRESS_RING_DOTS` | - |
| `progress_summary_card` | `ProgressSummaryCard` | Progress summary display | `FIF.CHART` | - |

### 4. Dashboard Components
| Component ID | Class | Description | Icon | Route |
|-------------|-------|-------------|------|-------|
| `dashboard` | `Dashboard` | Main dashboard interface | `FIF.HOME` | `/dashboard` |
| `dashboard_interface` | `DashboardInterface` | Enhanced dashboard interface | - | `/dashboard/interface` |
| `hero_section` | `HeroSection` | Dashboard hero section | - | - |
| `stats_section` | `StatsSection` | Statistics display section | - | - |
| `system_status` | `SystemStatus` | System status overview | - | - |
| `task_preview` | `TaskPreview` | Task preview widget | - | - |

### 5. Navigation Components
| Component ID | Class | Description | Icon | Route |
|-------------|-------|-------------|------|-------|
| `navigation_panel` | `NavigationPanel` | Main navigation panel | `FIF.MENU` | - |
| `modern_breadcrumb` | `ModernBreadcrumb` | Modern breadcrumb navigation | `FIF.CHEVRON_RIGHT` | - |

### 6. Settings Components
| Component ID | Class | Description | Icon | Route |
|-------------|-------|-------------|------|-------|
| `settings_interface` | `SettingsInterface` | Settings management interface | `FIF.SETTING` | `/settings` |

### 7. Utility Components
| Component ID | Class | Description | Icon | Route |
|-------------|-------|-------------|------|-------|
| `theme_manager` | `ThemeManager` | Theme management system | - | - |
| `responsive_manager` | `ResponsiveManager` | Responsive design manager | - | - |
| `error_notification_manager` | `ErrorNotificationManager` | Error notification system | - | - |
| `contextual_help_manager` | `ContextualHelpManager` | Contextual help system | - | - |

## Navigation Routes

### Primary Routes
| Route | Component ID | Description |
|-------|-------------|-------------|
| `/` | `dashboard` | Home/Dashboard |
| `/dashboard` | `dashboard` | Main dashboard |
| `/dashboard/interface` | `dashboard_interface` | Enhanced dashboard |
| `/download` | `task_manager` | Download management |
| `/logs` | `log_viewer` | Activity logs |
| `/analytics` | `analytics_dashboard` | Performance analytics |
| `/settings` | `settings_interface` | Application settings |

### Settings Sub-routes
| Route | Component ID | Description |
|-------|-------------|-------------|
| `/settings/general` | `settings_interface` | General settings |
| `/settings/download` | `settings_interface` | Download settings |
| `/settings/advanced` | `settings_interface` | Advanced settings |
| `/settings/ui` | `settings_interface` | UI settings |

## Component Icons Mapping

### Quick Access Icons
| Context | Icon | Usage |
|---------|------|-------|
| `dashboard` | `FIF.HOME` | Dashboard/Home |
| `download` | `FIF.DOWNLOAD` | Download management |
| `logs` | `FIF.HISTORY` | Activity logs |
| `analytics` | `FIF.PIE_SINGLE` | Analytics dashboard |
| `settings` | `FIF.SETTING` | Settings |
| `tasks` | `FIF.TILES` | Task management |
| `schedule` | `FIF.CALENDAR` | Scheduling |
| `media` | `FIF.VIDEO` | Media processing |
| `batch` | `FIF.LINK` | Batch operations |
| `help` | `FIF.HELP` | Help/Support |
| `about` | `FIF.INFO` | About dialog |

## Component Categories Enum

```python
class UIComponentCategory(Enum):
    MAIN_WINDOW = "main_window"
    DIALOG = "dialog"
    WIDGET = "widget"
    DASHBOARD = "dashboard"
    NAVIGATION = "navigation"
    SETTINGS = "settings"
    UTILITY = "utility"
    MANAGER = "manager"
```

## Usage Examples

### Getting Component by ID
```python
from src.gui.ui_mapping import ui_mapping

# Get component mapping
mapping = ui_mapping.get_component_by_id("task_manager")
component_class = mapping.component_class  # TaskManager
```

### Getting Components by Category
```python
from src.gui.ui_mapping import ui_mapping, UIComponentCategory

# Get all dialog components
dialogs = ui_mapping.get_components_by_category(UIComponentCategory.DIALOG)
```

### Route Navigation
```python
from src.gui.ui_mapping import get_route_component, get_component_route

# Get component for route
component_id = get_route_component("/dashboard")  # Returns "dashboard"

# Get route for component
route = get_component_route("settings_interface")  # Returns "/settings"
```

### Component Registration
```python
from src.gui.ui_mapping import ui_mapping

# Register component instance
task_manager_instance = TaskManager()
ui_mapping.register_component_instance("task_manager", task_manager_instance)
```

## File Structure Integration

### Import Paths
```python
# Main components
from .main_window import MainWindow

# Dialogs
from .dialogs.about_dialog import AboutDialog
from .dialogs.task_dialog import TaskDialog
from .dialogs.settings.settings_dialog import SettingsDialog

# Widgets
from .widgets.task_manager import TaskManager
from .widgets.dashboard import Dashboard
from .widgets.analytics_dashboard import AnalyticsDashboard

# Utils
from .utils.theme_manager import ThemeManager
from .utils.responsive import ResponsiveManager
```

## Integration with Component Registry

The UI mapping system integrates seamlessly with the existing `ComponentRegistry`:

- **Automatic Registration**: Components can be automatically registered with proper metadata
- **Dependency Management**: Component dependencies are tracked and managed
- **Type Conversion**: UI categories are mapped to ComponentRegistry types
- **Metadata Storage**: Icons, routes, and descriptions are stored as metadata

## Best Practices

1. **Consistent Naming**: Use snake_case for component IDs
2. **Clear Descriptions**: Provide meaningful descriptions for each component
3. **Icon Assignment**: Assign appropriate FluentIcons for visual consistency
4. **Route Planning**: Use logical route hierarchies for navigation
5. **Category Organization**: Group related components in appropriate categories
6. **Dependency Declaration**: Clearly specify component dependencies

## Extension Guidelines

When adding new components:

1. Add the component to the appropriate category dictionary
2. Create a `ComponentMapping` with all required information
3. Update navigation routes if the component has a route
4. Add appropriate icons to the icon mapping
5. Update this documentation

This mapping system provides a centralized, organized approach to managing all UI components in the VidTanium application, making it easier for developers and AI systems to understand and work with the codebase.

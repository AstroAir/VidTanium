# Custom Widgets and Component Inventory

## Overview

VidTanium contains 20+ custom widget components organized into modular subsystems. Widgets extend QFluentWidgets base classes with domain-specific functionality for download management, task tracking, and visualization.

## Part 1: Evidence - Widget Components

### Code Section: Progress Card Widget

**File:** `d:\Project\VidTanium\src\gui\widgets\progress.py`
**Lines:** 20-180
**Purpose:** Display progress information with controls and animations

```python
class ProgressCard(AnimatedCard):
    """Progress card with detailed information and controls"""

    pause_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.progress_value = 0
        self.is_paused = False
        # Animated progress bar with gradient
        self.progress_bar = ProgressBar()
        self.progress_bar.setStyleSheet(f"""
            ProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {DesignSystem.get_color('primary')},
                    stop:1 {DesignSystem.get_color('accent_blue')});
                border-radius: 4px;
            }}
        """)
        # Progress animation with OutCubic easing
        self.progress_animation = QPropertyAnimation(
            self.progress_bar, QByteArray(b"value"))
        self.progress_animation.setDuration(500)
        self.progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
```

**Key Details:**

- Extends AnimatedCard for consistent styling
- Emits pause/cancel signals for task control
- Uses property-based animations for smooth progress updates
- Supports state indicators: paused (warning color), completed (success), error
- Three information labels: percentage, speed, ETA

### Code Section: Status Widget Component

**File:** `d:\Project\VidTanium\src\gui\widgets\status_widget.py`
**Lines:** 28-100
**Purpose:** Comprehensive status feedback with animation

```python
@dataclass
class StatusInfo:
    """Comprehensive status information"""
    status: str
    progress: float  # 0.0 to 1.0
    current_file: Optional[str] = None
    speed: Optional[float] = None
    eta: Optional[float] = None
    completed_items: int = 0
    total_items: int = 0
    bytes_downloaded: int = 0
    total_bytes: int = 0

class StatusBadge(QWidget):
    """Animated status badge with color coding"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_text = ""
        self.status_color = VidTaniumTheme.TEXT_SECONDARY
        self.animation = QPropertyAnimation(
            self, QByteArray(b"geometry"))
        self.animation.setEasingCurve(
            QEasingCurve.Type.InOutSine)

    def update_status(self, status: str, animated: bool = False):
        """Update status with optional animation"""
        status_colors = {
            "downloading": VidTaniumTheme.SUCCESS_GREEN,
            "paused": VidTaniumTheme.WARNING_ORANGE,
            "completed": VidTaniumTheme.ACCENT_CYAN,
            "failed": VidTaniumTheme.ERROR_RED,
        }
        self.status_color = status_colors.get(
            status.lower(), VidTaniumTheme.TEXT_SECONDARY)
```

**Key Details:**

- Uses dataclass for structured status information
- Status badge uses semantic status colors
- Supports pulsing animation for active states
- Formatted display of speed, duration, progress metrics

### Code Section: Navigation Components

**File:** `d:\Project\VidTanium\src\gui\widgets\navigation.py`
**Lines:** 20-100
**Purpose:** Modern navigation patterns with animations

```python
class NavigationItem(AnimatedCard):
    """Navigation item with modern styling and animations"""

    clicked = Signal(str)

    def __init__(self, route_key: str, icon: FIF, text: str,
                 badge_count: int = 0, parent=None):
        super().__init__(parent)
        self.route_key = route_key
        self.is_active = False

        # Icon display (24x24)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setPixmap(
            icon.icon().pixmap(24, 24))

        # Badge for notifications
        if badge_count > 0:
            self.badge_label = self._create_badge()

    def _create_badge(self) -> QLabel:
        """Create notification badge"""
        badge = QLabel(str(self.badge_count))
        badge.setFixedSize(20, 20)
        badge.setStyleSheet(f"""
            QLabel {{
                background: {DesignSystem.get_color('error')};
                color: white;
                border-radius: 10px;
                font-weight: 600;
            }}
        """)
        return badge

    def _update_styling(self) -> None:
        """Update styling based on active state"""
        if self.is_active:
            self.setStyleSheet(f"""
                background: {DesignSystem.get_color('primary')};
                border: 1px solid {DesignSystem.get_color('primary')};
                border-radius: {DesignSystem.RADIUS['lg']}px;
            """)
```

**Key Details:**

- Uses slide animation for smooth transitions
- Badge support for notifications (right-aligned)
- Active/inactive state styling
- 56px fixed height for touch targets
- Horizontal layout: icon (24px) + text + stretch + badge

### Code Section: Dashboard Components

**File:** `d:\Project\VidTanium\src\gui\widgets\dashboard\hero_section.py`
**Lines:** 23-80
**Purpose:** Welcome/welcome screen with responsive layout

```python
class EnhancedDashboardHeroSection(ResponsiveWidget):
    """Enhanced hero section with responsive design"""

    def __init__(self, main_window, theme_manager=None, parent=None):
        super().__init__(parent)
        self.responsive_manager = ResponsiveManager.instance()

    def _setup_enhanced_ui(self) -> None:
        """Setup responsive hero section"""
        current_bp = self.responsive_manager.get_current_breakpoint()

        # Card sizing based on breakpoint
        if current_bp.value in ['xs', 'sm']:
            # Small screens: 140-200px
            self.hero_card.setMinimumHeight(140)
            layout = QVBoxLayout(self.hero_card)  # Vertical stack
        elif current_bp.value == 'md':
            # Medium screens: 160-220px
            self.hero_card.setMinimumHeight(160)
        else:
            # Large screens: 180-240px
            self.hero_card.setMinimumHeight(180)
            layout = QHBoxLayout(self.hero_card)  # Horizontal layout
```

**Key Details:**

- Extends ResponsiveWidget for breakpoint awareness
- Responsive height ranges for different screen sizes
- Layout switches from vertical (small screens) to horizontal (large)
- Uses ResponsiveManager singleton for current breakpoint

### Code Section: Statistics Dashboard

**File:** `d:\Project\VidTanium\src\gui\widgets\dashboard\stats_section.py`
**Lines:** 25-80
**Purpose:** Statistics display cards with responsive grid

```python
class EnhancedDashboardStatsSection(ResponsiveWidget):
    """Enhanced statistics cards with responsive grid layout"""

    def __init__(self, main_window, theme_manager=None, parent=None):
        super().__init__(parent)
        self.total_tasks_card: Optional[ElevatedCardWidget] = None
        self.running_tasks_card: Optional[ElevatedCardWidget] = None
        self.completed_tasks_card: Optional[ElevatedCardWidget] = None
        self.speed_card: Optional[ElevatedCardWidget] = None

        # Performance optimization flags
        self._last_task_count = 0
        self._skip_update_count = 0

    def _setup_enhanced_ui(self) -> None:
        """Setup responsive statistics grid"""
        current_bp = self.responsive_manager.get_current_breakpoint()

        if current_bp.value in ['xs', 'sm']:
            # 2x2 grid for small screens
            main_layout = QVBoxLayout(self)
            first_row = QHBoxLayout()  # 2 cards per row
            second_row = QHBoxLayout()
            main_layout.addLayout(first_row)
            main_layout.addLayout(second_row)
        else:
            # Single row for larger screens
            main_layout = QHBoxLayout(self)
            main_layout.setSpacing(
                16 if current_bp.value == 'md' else 20)
```

**Key Details:**

- Four card types: Total, Running, Completed, Speed
- Responsive grid: 2x2 (small), 1x4 (medium/large)
- Spacing adjusts with breakpoint: 12px (small), 16px (medium), 20px (large)
- Performance optimization: skips updates when no change detected
- Cards display numeric values with semantic colors

## Part 2: Complete Widget Inventory

### Core Widget Files

| File | Class(es) | Purpose |
|------|-----------|---------|
| `progress.py` | ProgressCard, CircularProgressCard, ProgressSummaryCard | Progress display with animations |
| `navigation.py` | NavigationItem, NavigationPanel, ModernBreadcrumb | Navigation UI components |
| `status_widget.py` | StatusBadge, StatusInfo, comprehensive status display | Status indicators |
| `task_manager.py` | Custom task display with status badges | Task list management |
| `dashboard.py` | Dashboard interface wrapper | Main dashboard container |
| `tooltip.py` | Custom tooltip components | Enhanced tooltips |
| `error_dialog.py` | Error presentation widgets | Error display dialogs |

### Dashboard Subsystem (`dashboard/`)

| File | Class | Purpose |
|------|-------|---------|
| `dashboard_interface.py` | EnhancedDashboardInterface | Main dashboard container |
| `hero_section.py` | EnhancedDashboardHeroSection | Welcome section |
| `stats_section.py` | EnhancedDashboardStatsSection | Statistics cards grid |
| `task_preview.py` | DashboardTaskPreview | Task preview cards |
| `system_status.py` | EnhancedDashboardSystemStatus | System information display |

### Settings Subsystem (`settings/`)

| File | Class | Purpose |
|------|-------|---------|
| `settings_interface.py` | SettingsInterface | Main settings UI with navigation |
| `settings_dialog.py` | SettingsDialog | Standalone settings window |

### Log Viewer Subsystem (`log/`)

| File | Class | Purpose |
|------|-------|---------|
| `log_viewer.py` | LogViewer | Log viewing and filtering |
| `log_entry.py` | LogEntry components | Individual log entries |
| `log_filter_bar.py` | LogFilterBar | Filtering controls |
| `log_detail_panel.py` | LogDetailPanel | Detailed log view |

### Help System (`help/`)

| File | Class | Purpose |
|------|-------|---------|
| `help_interface.py` | HelpInterface | Help documentation viewer |
| `markdown_viewer.py` | MarkdownViewer | Markdown content display |
| `help_navigation.py` | HelpNavigation | Help topic navigation |

### Schedule System (`schedule/`)

| File | Class | Purpose |
|------|-------|---------|
| `schedule_manager.py` | ScheduleManager | Scheduled task management |
| `task_table.py` | TaskTable | Schedule display table |
| `schedule_toolbar.py` | ScheduleToolbar | Schedule action controls |

### Dialogs (`dialogs/`)

| Type | Purpose |
|------|---------|
| `task_dialog.py` | New/edit task dialog |
| `batch_url_dialog.py` | Batch URL input dialog |
| `confirmation_dialog.py` | Generic confirmation |
| `media_processing_dialog.py` | Encoding/processing options |
| `recovery_dialog.py` | Recovery and resumption |

## Design Patterns Used

### 1. Animated Card Pattern
Multiple widgets extend `AnimatedCard` base class:
```python
class AnimatedCard(ElevatedCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_animations()
        self.hover_animation = QPropertyAnimation(...)
```

### 2. Responsive Widget Pattern
Components inherit from `ResponsiveWidget`:
```python
class EnhancedDashboardHeroSection(ResponsiveWidget):
    def _setup_enhanced_ui(self):
        current_bp = self.responsive_manager.get_current_breakpoint()
        # Layout adapts based on breakpoint
```

### 3. Signal-Based Communication
Widgets use Qt signals for parent/child communication:
```python
class ProgressCard(AnimatedCard):
    pause_clicked = Signal()
    cancel_clicked = Signal()
```

### 4. Dataclass for Structured Data
Status and configuration information use dataclasses:
```python
@dataclass
class StatusInfo:
    status: str
    progress: float
    speed: Optional[float] = None
```

## Widget Styling Summary

**Base Style Application:**
- QFluentWidgets components use built-in styling
- Custom widgets override via `setStyleSheet()`
- Inline f-string stylesheets generated from design tokens
- GraphicsDropShadowEffect for depth

**Animation Patterns:**
- QPropertyAnimation for progress and state changes
- EasingCurve.Type.OutCubic (500ms) for smooth transitions
- InOutSine (1000ms) for pulsing effects
- Opacity animations for fade transitions

**Responsive Patterns:**
- Breakpoint-aware height/width adjustments
- Layout switching (VBox to HBox)
- Spacing and margin scaling
- Font size adjustments for small screens


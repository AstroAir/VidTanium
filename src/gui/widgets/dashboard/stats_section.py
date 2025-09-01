"""
Enhanced Dashboard Statistics Section Component with responsive design and modern theming
"""
from typing import TYPE_CHECKING, Optional, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Slot
from qfluentwidgets import (
    TitleLabel, BodyLabel, IconWidget, FluentIcon as FIF,
    ElevatedCardWidget, HeaderCardWidget, VBoxLayout,
    setTheme, Theme, isDarkTheme, SimpleCardWidget
)

from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme
from ...utils.responsive import ResponsiveWidget, ResponsiveManager, ResponsiveContainer
from ...utils.formatters import format_speed
from ...theme_manager import EnhancedThemeManager
from src.core.thread_pool import submit_task
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class EnhancedDashboardStatsSection(ResponsiveWidget):
    """Enhanced statistics cards section component with responsive design and modern theming
    
    Features:
    - Responsive grid layout that adapts to screen size
    - Enhanced theming integration with EnhancedThemeManager
    - Modern gradient cards with smooth animations
    - Performance-optimized statistics calculation
    - Adaptive typography and spacing
    """

    def __init__(self, main_window: "MainWindow", theme_manager=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.theme_manager = theme_manager
        self.responsive_manager = ResponsiveManager.instance()
        self.total_tasks_card: Optional[ElevatedCardWidget] = None
        self.running_tasks_card: Optional[ElevatedCardWidget] = None
        self.completed_tasks_card: Optional[ElevatedCardWidget] = None
        self.speed_card: Optional[ElevatedCardWidget] = None

        # Performance optimization flags
        self._last_task_count = 0
        self._last_stats = None
        self._has_active_tasks = False
        self._skip_update_count = 0

        self._setup_enhanced_ui()
        self._apply_enhanced_theming()

    def _setup_enhanced_ui(self):
        """Setup enhanced responsive statistics section UI"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Responsive layout based on screen size using QFluentWidgets layouts
        if current_bp.value in ['xs', 'sm']:
            # Vertical grid layout for small screens (2x2)
            main_layout = VBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(12)
            
            # First row
            first_row = QHBoxLayout()
            first_row.setSpacing(12)

            # Second row
            second_row = QHBoxLayout()
            second_row.setSpacing(12)

        else:
            # Horizontal layout for larger screens
            main_layout = QHBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(16 if current_bp.value == 'md' else 20)

        # Create enhanced statistics cards with responsive design
        self.total_tasks_card = self._create_enhanced_stats_card(
            tr("dashboard.stats.total_tasks"),
            "0",
            FIF.MENU,
            [VidTaniumTheme.PRIMARY_BLUE, VidTaniumTheme.PRIMARY_PURPLE]
        )

        self.running_tasks_card = self._create_enhanced_stats_card(
            tr("dashboard.stats.active_downloads"),
            "0",
            FIF.DOWNLOAD,
            [VidTaniumTheme.SUCCESS_GREEN, VidTaniumTheme.SUCCESS_LIGHT]
        )

        self.completed_tasks_card = self._create_enhanced_stats_card(
            tr("dashboard.stats.completed"),
            "0",
            FIF.ACCEPT,
            [VidTaniumTheme.ACCENT_CYAN, VidTaniumTheme.ACCENT_GREEN]
        )

        self.speed_card = self._create_enhanced_stats_card(
            tr("dashboard.stats.total_speed"),
            "0 MB/s",
            FIF.SPEED_HIGH,
            [VidTaniumTheme.WARNING_ORANGE, VidTaniumTheme.WARNING_LIGHT]
        )

        # Add cards to responsive layout
        if current_bp.value in ['xs', 'sm']:
            # 2x2 grid for small screens
            first_row.addWidget(self.total_tasks_card, 1)
            first_row.addWidget(self.running_tasks_card, 1)
            
            second_row.addWidget(self.completed_tasks_card, 1)
            second_row.addWidget(self.speed_card, 1)
            
            main_layout.addLayout(first_row)
            main_layout.addLayout(second_row)
        else:
            # Horizontal layout for larger screens
            main_layout.addWidget(self.total_tasks_card, 1)
            main_layout.addWidget(self.running_tasks_card, 1)
            main_layout.addWidget(self.completed_tasks_card, 1)
            main_layout.addWidget(self.speed_card, 1)

    def _create_enhanced_stats_card(self, title: str, value: str, icon: FIF, gradient_colors: List[str]) -> ElevatedCardWidget:
        """Create enhanced statistics card with responsive design and modern theming"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        card = ElevatedCardWidget()
        
        # Responsive card sizing
        if current_bp.value in ['xs', 'sm']:
            card.setMinimumSize(140, 90)
            card.setMaximumHeight(110)
        elif current_bp.value == 'md':
            card.setMinimumSize(160, 100)
            card.setMaximumHeight(130)
        else:
            card.setMinimumSize(180, 110)
            card.setMaximumHeight(150)

        # Set responsive size policy
        from PySide6.QtWidgets import QSizePolicy
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = VBoxLayout(card)
        
        # Responsive margins and spacing
        if current_bp.value in ['xs', 'sm']:
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(6)
        else:
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(8)

        # Header with icon and value using Qt layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Responsive icon sizing using QFluentWidgets IconWidget
        icon_widget = IconWidget(icon)
        icon_size = 20 if current_bp.value in ['xs', 'sm'] else 24
        icon_widget.setFixedSize(icon_size, icon_size)
        # Let QFluentWidgets handle the icon theming automatically

        # Responsive value text using QFluentWidgets typography
        value_label = TitleLabel(value)
        # Let QFluentWidgets handle responsive font sizing and colors
        value_label.setWordWrap(True)

        header_layout.addWidget(icon_widget)
        header_layout.addWidget(value_label, 1)

        # Responsive title using QFluentWidgets typography
        title_label = BodyLabel(title)
        # Let QFluentWidgets handle the text styling automatically
        title_label.setWordWrap(True)

        layout.addLayout(header_layout)
        layout.addWidget(title_label)
        layout.addStretch()

        # Store references for updates
        setattr(card, 'value_label', value_label)
        setattr(card, 'title_label', title_label)
        setattr(card, 'gradient_colors', gradient_colors)

        return card

    def update_stats_threaded(self):
        """Update statistics using thread pool for better performance"""
        try:
            # Performance optimization: skip updates when no tasks and no recent activity
            if (not self._has_active_tasks and
                self._last_task_count == 0 and
                    self._skip_update_count < 5):  # Update every 10 seconds when idle
                self._skip_update_count += 1
                logger.debug("Skipping stats update - no active tasks")
                return

            self._skip_update_count = 0

            submit_task(
                self._calculate_stats,
                callback=self._on_stats_calculated,
                error_callback=self._on_stats_error
            )
        except Exception as e:
            logger.error(f"Error submitting stats update task: {e}")
            # Fallback to direct update
            self._update_stats_fallback()

    def _calculate_stats(self):
        """Calculate statistics in background thread"""
        try:
            if not self.main_window or not self.main_window.download_manager:
                return {
                    'total_tasks': 0,
                    'running_tasks': 0,
                    'completed_tasks': 0,
                    'total_speed': 0
                }

            # Get real data from download manager
            tasks = getattr(self.main_window.download_manager, 'tasks', {})

            # Early exit if no tasks to avoid unnecessary computation
            if not tasks:
                self._last_task_count = 0
                self._has_active_tasks = False
                return {
                    'total_tasks': 0,
                    'running_tasks': 0,
                    'completed_tasks': 0,
                    'total_speed': 0
                }

            total_tasks = len(tasks)
            running_tasks = 0
            completed_tasks = 0
            total_speed = 0

            # Single loop for efficiency
            for task in tasks.values():
                status = getattr(task, 'status', '')
                if status == 'downloading':
                    running_tasks += 1
                    if hasattr(task, 'speed'):
                        total_speed += getattr(task, 'speed', 0)
                elif status == 'completed':
                    completed_tasks += 1

            # Update optimization flags
            self._last_task_count = total_tasks
            self._has_active_tasks = running_tasks > 0

            stats = {
                'total_tasks': total_tasks,
                'running_tasks': running_tasks,
                'completed_tasks': completed_tasks,
                'total_speed': total_speed
            }

            # Cache the stats to compare for changes
            self._last_stats = stats
            return stats

        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            raise

    @Slot()
    def _on_stats_calculated(self, stats):
        """Handle calculated statistics on main thread"""
        try:
            # Update stats cards
            if self.total_tasks_card:
                value_label = getattr(
                    self.total_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(stats['total_tasks']))

            if self.running_tasks_card:
                value_label = getattr(
                    self.running_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(stats['running_tasks']))

            if self.completed_tasks_card:
                value_label = getattr(
                    self.completed_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(stats['completed_tasks']))

            if self.speed_card:
                value_label = getattr(self.speed_card, 'value_label', None)
                if value_label:
                    speed_text = format_speed(stats['total_speed'])
                    value_label.setText(speed_text)

        except Exception as e:
            logger.error(f"Error updating stats display: {e}")

    @Slot()
    def _on_stats_error(self, error_tuple):
        """Handle stats calculation errors"""
        try:
            exctype, value, tb = error_tuple
            logger.error(f"Stats calculation error: {value}")
            # Fallback to direct update on error
            self._update_stats_fallback()
        except Exception as e:
            logger.error(f"Error in stats error callback: {e}")

    def _update_stats_fallback(self):
        """Fallback method for updating stats without thread pool"""
        try:
            if not self.main_window or not self.main_window.download_manager:
                return

            # Get real data from download manager
            tasks = getattr(self.main_window.download_manager, 'tasks', {})

            total_tasks = len(tasks)
            running_tasks = sum(1 for task in tasks.values()
                                if getattr(task, 'status', '') == 'downloading')
            completed_tasks = sum(1 for task in tasks.values()
                                  if getattr(task, 'status', '') == 'completed')

            # Update stats cards using getattr to avoid type issues
            if self.total_tasks_card:
                value_label = getattr(
                    self.total_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(total_tasks))

            if self.running_tasks_card:
                value_label = getattr(
                    self.running_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(running_tasks))

            if self.completed_tasks_card:
                value_label = getattr(
                    self.completed_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(completed_tasks))

            if self.speed_card:
                value_label = getattr(self.speed_card, 'value_label', None)
                if value_label:
                    # Calculate total speed (placeholder for now)
                    value_label.setText("2.5 MB/s")

        except Exception as e:
            logger.error(f"Error in fallback stats update: {e}")

    def update_statistics(self):
        """Public method to update statistics"""
        self.update_stats_threaded()

    def _apply_enhanced_theming(self):
        """Apply enhanced theming using QFluentWidgets theming system"""
        if not self.theme_manager:
            return
            
        cards = [
            (self.total_tasks_card, [VidTaniumTheme.PRIMARY_BLUE, VidTaniumTheme.PRIMARY_PURPLE]),
            (self.running_tasks_card, [VidTaniumTheme.SUCCESS_GREEN, VidTaniumTheme.SUCCESS_LIGHT]),
            (self.completed_tasks_card, [VidTaniumTheme.ACCENT_CYAN, VidTaniumTheme.ACCENT_GREEN]),
            (self.speed_card, [VidTaniumTheme.WARNING_ORANGE, VidTaniumTheme.WARNING_LIGHT])
        ]
        
        for card, gradient_colors in cards:
            if card:
                # Apply minimal gradient background - let QFluentWidgets handle everything else
                card.setStyleSheet(f"""
                    ElevatedCardWidget {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 {gradient_colors[0]}, stop:1 {gradient_colors[1]});
                    }}
                """)

    def on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        logger.debug(f"Stats section adapting to breakpoint: {breakpoint}")
        # Recreate UI with new breakpoint
        self._setup_enhanced_ui()
        self._apply_enhanced_theming()

    def update_theme(self, theme_manager: Optional[EnhancedThemeManager] = None):
        """Update theme styling"""
        if theme_manager:
            self.theme_manager = theme_manager
        self._apply_enhanced_theming()


# Backward compatibility alias
DashboardStatsSection = EnhancedDashboardStatsSection

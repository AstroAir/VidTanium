"""
Dashboard Statistics Section Component
"""
from typing import TYPE_CHECKING, Optional, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Slot
from qfluentwidgets import (
    TitleLabel, BodyLabel, IconWidget, CardWidget, FluentIcon as FIF
)

from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme, ThemeManager
from ...utils.formatters import format_speed
from src.core.thread_pool import submit_task
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class DashboardStatsSection(QWidget):
    """Statistics cards section component"""
    
    def __init__(self, main_window: "MainWindow", parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.total_tasks_card: Optional[CardWidget] = None
        self.running_tasks_card: Optional[CardWidget] = None
        self.completed_tasks_card: Optional[CardWidget] = None
        self.speed_card: Optional[CardWidget] = None
        
        # Performance optimization flags
        self._last_task_count = 0
        self._last_stats = None
        self._has_active_tasks = False
        self._skip_update_count = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the statistics section UI with responsive design"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)  # Reduced spacing for better space usage

        # Create statistics cards with responsive design
        self.total_tasks_card = self._create_animated_stats_card(
            tr("dashboard.stats.total_tasks"),
            "0",
            FIF.MENU,
            [VidTaniumTheme.PRIMARY_BLUE, VidTaniumTheme.PRIMARY_PURPLE]
        )

        self.running_tasks_card = self._create_animated_stats_card(
            tr("dashboard.stats.active_downloads"),
            "0",
            FIF.DOWNLOAD,
            [VidTaniumTheme.SUCCESS_GREEN, VidTaniumTheme.SUCCESS_LIGHT]
        )

        self.completed_tasks_card = self._create_animated_stats_card(
            tr("dashboard.stats.completed"),
            "0",
            FIF.ACCEPT,
            [VidTaniumTheme.ACCENT_CYAN, VidTaniumTheme.ACCENT_GREEN]
        )

        self.speed_card = self._create_animated_stats_card(
            tr("dashboard.stats.total_speed"),
            "0 MB/s",
            FIF.SPEED_HIGH,
            [VidTaniumTheme.WARNING_ORANGE, VidTaniumTheme.WARNING_LIGHT]
        )

        # Add cards with equal stretch for responsive layout
        layout.addWidget(self.total_tasks_card, 1)
        layout.addWidget(self.running_tasks_card, 1)
        layout.addWidget(self.completed_tasks_card, 1)
        layout.addWidget(self.speed_card, 1)

    def _create_animated_stats_card(self, title: str, value: str, icon: FIF, gradient_colors: List[str]) -> CardWidget:
        """Create beautiful animated statistics card with responsive design"""
        card = CardWidget()
        # Use responsive sizing instead of fixed size
        card.setMinimumSize(160, 100)  # Minimum size to prevent cards from being too small
        card.setMaximumHeight(140)     # Maximum height to prevent cards from being too tall
        
        # Set size policy for responsive behavior
        from PySide6.QtWidgets import QSizePolicy
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Apply themed gradient background with better scaling
        card.setStyleSheet(f"""
            CardWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {gradient_colors[0]}, stop:1 {gradient_colors[1]});
                border: none;
                border-radius: {VidTaniumTheme.RADIUS_LARGE};
                margin: 2px;  /* Add small margin for shadow effect */
            }}
        """)

        # Add themed shadow with scaling consideration
        card.setGraphicsEffect(ThemeManager.get_shadow_effect(16, 3, 25))

        layout = QVBoxLayout(card)
        # Use relative margins that scale better
        margin = max(12, int(card.width() * 0.06)) if hasattr(card, 'width') else 16
        if callable(getattr(card, "width", None)):
            margin = max(12, int(card.width() * 0.06))
        else:
            margin = 16
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(6)

        # Icon and value row with responsive sizing
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        icon_widget = IconWidget(icon)
        # Use scalable icon size
        icon_size = max(20, min(28, int(card.height() * 0.2))) if hasattr(card, 'height') else 24
        icon_widget.setFixedSize(icon_size, icon_size)
        icon_widget.setStyleSheet(f"""
            IconWidget {{
                color: {VidTaniumTheme.TEXT_WHITE}; 
                background: transparent;
            }}
        """)

        value_label = TitleLabel(value)
        value_label.setStyleSheet(f"""
            TitleLabel {{
                color: {VidTaniumTheme.TEXT_WHITE};
                font-size: {VidTaniumTheme.FONT_SIZE_SUBTITLE};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD};
                background: transparent;
            }}
        """)
        # Enable word wrap for long values
        value_label.setWordWrap(True)

        header_layout.addWidget(icon_widget)
        header_layout.addWidget(value_label, 1)  # Give value label stretch factor

        # Title label with responsive text
        title_label = BodyLabel(title)
        title_label.setStyleSheet(f"""
            BodyLabel {{
                color: {VidTaniumTheme.TEXT_WHITE_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
                background: transparent;
            }}
        """)
        # Enable word wrap for long titles
        title_label.setWordWrap(True)

        layout.addLayout(header_layout)
        layout.addWidget(title_label)
        layout.addStretch()

        # Store reference to value label for updates
        setattr(card, 'value_label', value_label)
        setattr(card, 'title_label', title_label)

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
                value_label = getattr(self.total_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(stats['total_tasks']))

            if self.running_tasks_card:
                value_label = getattr(self.running_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(stats['running_tasks']))

            if self.completed_tasks_card:
                value_label = getattr(self.completed_tasks_card, 'value_label', None)
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
                value_label = getattr(self.total_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(total_tasks))

            if self.running_tasks_card:
                value_label = getattr(self.running_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(running_tasks))

            if self.completed_tasks_card:
                value_label = getattr(self.completed_tasks_card, 'value_label', None)
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

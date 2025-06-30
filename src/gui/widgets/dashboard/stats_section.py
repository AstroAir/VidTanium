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
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the statistics section UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Create statistics cards
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

        layout.addWidget(self.total_tasks_card)
        layout.addWidget(self.running_tasks_card)
        layout.addWidget(self.completed_tasks_card)
        layout.addWidget(self.speed_card)

    def _create_animated_stats_card(self, title: str, value: str, icon: FIF, gradient_colors: List[str]) -> CardWidget:
        """Create beautiful animated statistics card"""
        card = CardWidget()
        card.setFixedSize(200, 120)

        # Apply themed gradient background
        card.setStyleSheet(f"""
            CardWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {gradient_colors[0]}, stop:1 {gradient_colors[1]});
                border: none;
                border-radius: {VidTaniumTheme.RADIUS_LARGE};
            }}
        """)

        # Add themed shadow
        card.setGraphicsEffect(ThemeManager.get_shadow_effect(20, 4, 30))

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # Icon and value row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(24, 24)
        icon_widget.setStyleSheet(f"color: {VidTaniumTheme.TEXT_WHITE}; background: transparent;")

        value_label = TitleLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE};
                font-size: {VidTaniumTheme.FONT_SIZE_SUBTITLE};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD};
                background: transparent;
            }}
        """)

        header_layout.addWidget(icon_widget)
        header_layout.addWidget(value_label)
        header_layout.addStretch()

        # Title label
        title_label = BodyLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
                background: transparent;
            }}
        """)

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

            total_tasks = len(tasks)
            running_tasks = sum(1 for task in tasks.values()
                                if getattr(task, 'status', '') == 'downloading')
            completed_tasks = sum(1 for task in tasks.values()
                                  if getattr(task, 'status', '') == 'completed')

            # Calculate total speed
            total_speed = 0
            for task in tasks.values():
                if hasattr(task, 'speed') and getattr(task, 'status', '') == 'downloading':
                    total_speed += getattr(task, 'speed', 0)

            return {
                'total_tasks': total_tasks,
                'running_tasks': running_tasks,
                'completed_tasks': completed_tasks,
                'total_speed': total_speed
            }
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

"""
Beautiful Dashboard interface with modern Fluent Design and unified theme - Refactored with Components
"""
from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import QTimer, QObject
from qfluentwidgets import (
    ScrollArea
)

from ...utils.theme import VidTaniumTheme
from .hero_section import DashboardHeroSection
from .stats_section import DashboardStatsSection
from .task_preview import DashboardTaskPreview
from .system_status import DashboardSystemStatus
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class DashboardInterface(QObject):
    """Beautiful Dashboard interface with modern animations and gradients - Component-based"""

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.main_window = main_window
        
        # Component instances
        self.hero_section: Optional[DashboardHeroSection] = None
        self.stats_section: Optional[DashboardStatsSection] = None
        self.task_preview: Optional[DashboardTaskPreview] = None
        self.system_status: Optional[DashboardSystemStatus] = None

        # Animation timer for dynamic effects
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(2000)  # Update every 2 seconds

    def create_interface(self) -> QWidget:
        """Create the beautiful dashboard interface using components"""
        interface = ScrollArea()
        interface.setWidgetResizable(True)
        interface.setObjectName("dashboard_scroll_area")
        interface.setStyleSheet(f"""
            ScrollArea {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {VidTaniumTheme.BG_SECONDARY}, stop:1 {VidTaniumTheme.BG_PRIMARY});
                border: none;
            }}
        """)

        # Main container with beautiful styling
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)

        # Create component instances
        self.hero_section = DashboardHeroSection(self.main_window)
        main_layout.addWidget(self.hero_section)

        # Statistics dashboard
        self.stats_section = DashboardStatsSection(self.main_window)
        main_layout.addWidget(self.stats_section)

        # Content cards section
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        # Task preview card
        self.task_preview = DashboardTaskPreview(self.main_window)
        content_layout.addWidget(self.task_preview, 2)

        # System status card
        self.system_status = DashboardSystemStatus(self.main_window)
        content_layout.addWidget(self.system_status, 1)

        main_layout.addLayout(content_layout)

        interface.setWidget(main_container)
        return interface

    def _update_animations(self):
        """Update dashboard animations and data"""
        # Update components periodically
        try:
            if self.stats_section:
                self.stats_section.update_statistics()
            if self.task_preview:
                self.task_preview.update_task_preview()
            if self.system_status:
                self.system_status.update_system_status()
        except Exception as e:
            logger.error(f"Error updating dashboard animations: {e}")

    def update_statistics(self) -> None:
        """Update statistics information - delegates to stats component"""
        try:
            if self.stats_section:
                self.stats_section.update_statistics()
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")

    def update_task_preview(self):
        """Update task preview - delegates to task preview component"""
        try:
            if self.task_preview:
                self.task_preview.update_task_preview()
        except Exception as e:
            logger.error(f"Error updating task preview: {e}")

    def update_system_status(self) -> None:
        """Update system status - delegates to system status component"""
        try:
            if self.system_status:
                self.system_status.update_system_status()
        except Exception as e:
            logger.error(f"Error updating system status: {e}")

    # Compatibility methods for backward compatibility
    def update_stats(self):
        """Update statistics - compatibility method"""
        self.update_statistics()

    def update_task_preview_original(self) -> None:
        """Legacy method - kept for compatibility"""
        self.update_task_preview()

    def _format_speed(self, speed_bytes_per_sec: float) -> str:
        """Format speed in human-readable format - compatibility method"""
        from ...utils.formatters import format_speed
        return format_speed(speed_bytes_per_sec)

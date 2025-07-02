"""
Dashboard Task Preview Component
"""
from typing import TYPE_CHECKING, Optional, Dict
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from qfluentwidgets import (
    BodyLabel, SubtitleLabel, CaptionLabel, IconWidget, CardWidget,
    FluentIcon as FIF, ProgressRing, TextEdit
)

from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class DashboardTaskPreview(QWidget):
    """Task preview component showing recent tasks"""
    
    def __init__(self, main_window: "MainWindow", parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.task_preview_content: Optional[QWidget] = None
        self.main_log_preview: Optional[TextEdit] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the task preview UI with responsive design"""
        # Main card container with responsive sizing
        card = CardWidget()
        card.setMinimumHeight(280)
        card.setMaximumHeight(500)  # Prevent excessive growth
        
        # Set responsive size policy
        # Set responsive size policy
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        card.setStyleSheet(VidTaniumTheme.get_card_style())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)  # Slightly reduced margins
        layout.setSpacing(12)  # Reduced spacing

        # Header
        header_layout = self._create_header()
        layout.addLayout(header_layout)

        # Task preview content with responsive layout
        self.task_preview_content = QWidget()
        preview_layout = QVBoxLayout(self.task_preview_content)
        preview_layout.setSpacing(6)  # Reduced spacing for better fit

        # Sample recent tasks (placeholder) - limit to visible amount
        for i in range(3):
            task_item = self._create_preview_task_item(
                f"Sample Task {i+1}",
                "downloading" if i == 0 else "completed",
                75 if i == 0 else 100
            )
            preview_layout.addWidget(task_item)

        preview_layout.addStretch()
        layout.addWidget(self.task_preview_content, 1)  # Give content stretch factor
        
        # Set up main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card)

    def _create_header(self) -> QHBoxLayout:
        """Create the header section"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        icon = IconWidget(FIF.HISTORY)
        icon.setFixedSize(20, 20)
        icon.setStyleSheet(f"color: {VidTaniumTheme.PRIMARY_BLUE};")

        title = SubtitleLabel(tr("dashboard.recent_tasks.title"))
        title.setStyleSheet(f"""
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD}; 
            color: {VidTaniumTheme.TEXT_PRIMARY};
            font-size: {VidTaniumTheme.FONT_SIZE_HEADING};
        """)

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        return header_layout

    def _create_preview_task_item(self, name: str, status: str, progress: int) -> QWidget:
        """Create a preview task item with responsive design"""
        item = QWidget()
        item.setMinimumHeight(50)  # Minimum height for readability
        item.setMaximumHeight(70)  # Maximum height to prevent excessive growth
        
        # Set responsive size policy
        # Set responsive size policy
        item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        item.setStyleSheet(f"""
                background-color: {VidTaniumTheme.BG_CARD};
                border-radius: {VidTaniumTheme.RADIUS_MEDIUM};
                border: 1px solid {VidTaniumTheme.BORDER_LIGHT};
            }}
            QWidget:hover {{
                background-color: {VidTaniumTheme.BG_CARD_HOVER};
                border-color: {VidTaniumTheme.BORDER_ACCENT};
            }}
        """)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Status icon with themed colors
        status_icons = {
            "downloading": FIF.DOWNLOAD,
            "completed": FIF.ACCEPT,
            "paused": FIF.PAUSE,
            "error": FIF.CLOSE
        }

        status_colors = {
            "downloading": VidTaniumTheme.INFO_BLUE,
            "completed": VidTaniumTheme.SUCCESS_GREEN,
            "paused": VidTaniumTheme.WARNING_ORANGE,
            "error": VidTaniumTheme.ERROR_RED
        }

        icon = IconWidget(status_icons.get(status, FIF.INFO))
        icon.setFixedSize(16, 16)
        icon.setStyleSheet(f"color: {status_colors.get(status, VidTaniumTheme.TEXT_SECONDARY)};")

        # Task info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = BodyLabel(name)
        name_label.setStyleSheet(f"""
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD}; 
            color: {VidTaniumTheme.TEXT_PRIMARY};
        """)

        status_label = CaptionLabel(f"{status.title()} - {progress}%")
        status_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")

        info_layout.addWidget(name_label)
        info_layout.addWidget(status_label)

        # Progress ring for active downloads
        if status == "downloading":
            progress_ring = ProgressRing()
            progress_ring.setFixedSize(24, 24)
            progress_ring.setValue(progress)
            layout.addWidget(progress_ring)

        layout.addWidget(icon)
        layout.addLayout(info_layout)
        layout.addStretch()

        return item

    def update_task_preview(self):
        """Update task preview panel with recent activity"""
        try:
            if not self.main_window.download_manager:
                return

            # Get recent tasks
            tasks = getattr(self.main_window.download_manager, 'tasks', {})
            if not isinstance(tasks, dict):
                return

            # Sort tasks by status priority (running first, then recent)
            sorted_tasks = []
            for task_id, task in tasks.items():
                try:
                    status = str(getattr(task, 'status', 'unknown')).lower()
                    priority = 0
                    if status in ['running', 'downloading']:
                        priority = 3
                    elif status == 'paused':
                        priority = 2
                    elif status == 'completed':
                        priority = 1

                    sorted_tasks.append((priority, task_id, task))
                except Exception:
                    continue

            sorted_tasks.sort(key=lambda x: x[0], reverse=True)

            # Clear existing items
            if self.task_preview_content:
                layout = self.task_preview_content.layout()
                if layout and isinstance(layout, QVBoxLayout):
                    # Remove all existing widgets
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()

                    # Add updated task items (show top 5 tasks)
                    for i, (_, task_id, task) in enumerate(sorted_tasks[:5]):
                        try:
                            name = getattr(task, 'name', f'Task {task_id[:8]}')
                            status = str(getattr(task, 'status', 'unknown')).lower()

                            # Get progress if available
                            progress = 0
                            if hasattr(task, 'progress'):
                                task_progress = getattr(task, 'progress', {})
                                if isinstance(task_progress, dict):
                                    completed = task_progress.get('completed', 0)
                                    total = task_progress.get('total', 0)
                                    if total > 0:
                                        progress = int((completed / total) * 100)
                                elif isinstance(task_progress, (int, float)):
                                    progress = int(task_progress)

                            task_item = self._create_preview_task_item(name, status, progress)
                            layout.addWidget(task_item)
                        except Exception as e:
                            logger.error(f"Error creating task preview item: {e}")
                            continue

                    layout.addStretch()

        except Exception as e:
            logger.error(f"Error updating task preview: {e}")

    def _create_task_preview_widget(self, task) -> QWidget:
        """Create task preview widget for individual task"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Task status icon
        try:
            task_status = getattr(task, 'status', None)
            if task_status == 'running':
                status_icon = IconWidget(FIF.PLAY)
            else:
                status_icon = IconWidget(FIF.PAUSE)
        except:
            status_icon = IconWidget(FIF.PAUSE)

        status_icon.setFixedSize(16, 16)
        layout.addWidget(status_icon)

        # Task name
        name_label = BodyLabel(getattr(task, 'name', 'Unknown Task'))
        name_label.setFixedWidth(150)
        layout.addWidget(name_label)

        layout.addStretch()

        # Progress info
        if hasattr(task, 'progress'):
            progress_text = f"{task.progress:.1f}%"
        else:
            progress_text = tr("dashboard.task_status.waiting")
        progress_label = BodyLabel(progress_text)
        progress_label.setStyleSheet("color: #666666;")
        layout.addWidget(progress_label)

        return widget

import os
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QFrame,
    QGraphicsDropShadowEffect, QApplication, QMessageBox, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect, QByteArray
from PySide6.QtGui import QColor, QPainter, QPainterPath

from qfluentwidgets import (
    PrimaryPushButton, PushButton, ProgressBar,
    FluentIcon as FIF, StrongBodyLabel, BodyLabel, TransparentToolButton, CaptionLabel,
    ElevatedCardWidget, CheckBox, ComboBox, SearchLineEdit,
    SmoothScrollArea, ProgressRing, IndeterminateProgressRing
)
from ..utils.formatters import format_speed, format_bytes, format_time, format_percentage, format_eta
from ..utils.i18n import tr
from ..utils.responsive import ResponsiveWidget, ResponsiveManager, ResponsiveContainer
# Import optimized progress components
from ..utils.fluent_progress import FluentProgressBar, ProgressCardWidget, CompactProgressBar
from qfluentwidgets import isDarkTheme, qconfig
from loguru import logger


class ModernStatusBadge(BodyLabel):
    """Status badge using qfluentwidgets native components"""

    def __init__(self, text="", status_type="default", parent=None) -> None:
        super().__init__(text, parent)
        self.status_type = status_type
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)
        self.setMinimumWidth(60)
        self._setup_style()

    def _setup_style(self) -> None:
        """Setup style using theme-aware colors"""
        # Use qfluentwidgets theme colors
        # Status colors will be handled by qconfig theme system
        self.setObjectName(f"status-badge-{self.status_type}")

    def update_status(self, status_type: str, text: str) -> None:
        """Update badge status and text with smooth animation"""
        if self.status_type != status_type:
            # Add fade transition for status changes
            self.fade_animation = QPropertyAnimation(parent=self)
            self.fade_animation.setTargetObject(self)
            self.fade_animation.setPropertyName(b"windowOpacity")
            self.fade_animation.setDuration(200)
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.7)
            self.fade_animation.finished.connect(lambda: self._complete_status_update(status_type, text))
            self.fade_animation.start()
        else:
            self.setText(text)

    def _complete_status_update(self, status_type: str, text: str) -> None:
        """Complete the status update animation"""
        self.status_type = status_type
        self.setText(text)
        self._setup_style()
        
        # Fade back in
        self.fade_in_animation = QPropertyAnimation(parent=self)
        self.fade_in_animation.setTargetObject(self)
        self.fade_in_animation.setPropertyName(b"windowOpacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0.7)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.start()


class CustomSeparator(QFrame):
    """Simple separator widget using qfluentwidgets theme"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setFixedWidth(1)
        # Let qfluentwidgets handle the color automatically


class TaskItem(ResponsiveContainer):
    """Task item with responsive design and modern animations"""

    # Signals
    playClicked = Signal(str)  # task_id
    pauseClicked = Signal(str)
    stopClicked = Signal(str)
    deleteClicked = Signal(str)

    def __init__(self, task_id: str, task_data: dict, parent=None) -> None:
        super().__init__(parent)
        self.task_id = task_id
        self.task_data = task_data
        self.is_expanded = False
        self.responsive_manager = ResponsiveManager.instance()
        
        # Performance optimization
        self._last_progress_update = 0
        self._update_throttle_ms = 100  # Minimum time between updates
        
        self._create_ui()
        self._setup_style()
        self._setup_animations()

    def _create_ui(self) -> None:
        """Create the enhanced responsive task item UI"""
        # Main card container
        self.card = ElevatedCardWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.card)

        self.main_layout = QVBoxLayout(self.card)
        
        # Responsive margins based on screen size
        self._setup_responsive_margins()
        self.main_layout.setSpacing(16)

        # Header section with responsive design
        self._create_header()

        # Progress section with enhanced indicators
        self._create_progress_section()

        # Details section (collapsible and responsive)
        self._create_details_section()

        # Actions section with responsive buttons
        self._create_actions_section()

    def _setup_responsive_margins(self) -> None:
        """Setup margins that adapt to screen size"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        margin_config = {
            'xs': 12,
            'sm': 16,
            'md': 20,
            'lg': 24,
            'xl': 28
        }
        
        margin = margin_config.get(current_bp.value, 20)
        self.main_layout.setContentsMargins(margin, margin//2, margin, margin//2)

    def on_breakpoint_changed(self, breakpoint: str) -> None:
        """Handle responsive breakpoint changes"""
        self._setup_responsive_margins()
        self._adapt_layout_for_breakpoint(breakpoint)

    def _adapt_layout_for_breakpoint(self, breakpoint: str) -> None:
        """Adapt layout based on current breakpoint"""
        if breakpoint in ['xs', 'sm']:
            # Compact layout for small screens
            self._set_compact_mode(True)
        else:
            # Full layout for larger screens
            self._set_compact_mode(False)

    def _set_compact_mode(self, compact: bool) -> None:
        """Switch between compact and full layout modes"""
        if compact:
            # Hide less important elements on small screens
            if hasattr(self, 'url_label'):
                self.url_label.setVisible(False)
            if hasattr(self, 'details_section'):
                self.details_section.setVisible(False)
                self.is_expanded = False
        else:
            # Show all elements on larger screens
            if hasattr(self, 'url_label'):
                self.url_label.setVisible(True)
            if hasattr(self, 'details_section') and self.is_expanded:
                self.details_section.setVisible(True)

    def _create_header(self) -> None:
        """Create responsive header with adaptive layout"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Task icon with responsive sizing
        self._create_task_icon(header_layout)
        
        # Task information with responsive text
        self._create_task_info(header_layout)
        
        header_layout.addStretch()

        # Status and controls with responsive layout
        self._create_status_controls(header_layout)

        self.main_layout.addLayout(header_layout)

    def _create_task_icon(self, header_layout: QHBoxLayout) -> None:
        """Create responsive task icon"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        icon_size = 40 if current_bp.value in ['xs', 'sm'] else 48
        
        icon_container = QWidget()
        icon_container.setFixedSize(icon_size, icon_size)
        # Use theme color for icon background
        theme_color = qconfig.themeColor()
        icon_container.setStyleSheet(f"""
            QWidget {{
                background-color: {theme_color.name()};
                border-radius: {icon_size//2}px;
            }}
        """)

        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        self.task_icon = TransparentToolButton(FIF.VIDEO)
        self.task_icon.setIconSize(QSize(icon_size//2, icon_size//2))
        self.task_icon.setStyleSheet(
            "background: transparent; border: none; color: white;")
        icon_layout.addWidget(self.task_icon, 0, Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(icon_container)

    def _create_task_info(self, header_layout: QHBoxLayout) -> None:
        """Create responsive task information section"""
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.title_label = StrongBodyLabel(
            self.task_data.get('name', tr('task_manager.unknown_task')))
        # Let qfluentwidgets StrongBodyLabel handle styling automatically
        # No custom stylesheet needed
        self.title_label.setWordWrap(True)

        self.url_label = CaptionLabel(self.task_data.get('url', ''))
        # CaptionLabel already has appropriate styling from qfluentwidgets
        # No custom stylesheet needed
        self.url_label.setWordWrap(True)
        
        # Limit URL length for better responsive display
        url_text = self.task_data.get('url', '')
        if len(url_text) > 80:
            url_text = url_text[:77] + "..."
        self.url_label.setText(url_text)

        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.url_label)
        info_layout.addStretch()

        header_layout.addLayout(info_layout)

    def _create_status_controls(self, header_layout: QHBoxLayout) -> None:
        """Create responsive status and control section"""
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)

        self.status_badge = ModernStatusBadge()
        self._update_status_badge(self.task_data.get('status', 'unknown'))

        self.expand_btn = TransparentToolButton(FIF.DOWN)
        self.expand_btn.setIconSize(QSize(16, 16))
        self.expand_btn.setToolTip(tr('task_manager.expand_details'))
        self.expand_btn.clicked.connect(self._toggle_expand)
        # TransparentToolButton already has proper hover effects from qfluentwidgets
        # No custom stylesheet needed

        status_layout.addWidget(self.status_badge, 0, Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(self.expand_btn, 0, Qt.AlignmentFlag.AlignRight)

        header_layout.addLayout(status_layout)

    def _create_progress_section(self) -> None:
        """Create beautiful progress visualization with Fluent Design"""
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 8, 0, 8)
        progress_layout.setSpacing(8)

        # Use the new optimized progress card
        self.progress_card = ProgressCardWidget()
        self.progress_card.setTitle("Download Progress")

        # Connect the legacy progress bar references for compatibility
        self.progress_bar = self.progress_card.progress_bar
        self.progress_label = self.progress_card.percentage_label
        self.speed_label = self.progress_card.speed_label
        self.eta_label = self.progress_card.eta_label

        progress_layout.addWidget(self.progress_card)
        self.main_layout.addWidget(progress_container)

    def _create_details_section(self) -> None:
        """Create collapsible details section"""
        self.details_widget = QWidget()
        self.details_widget.setFixedHeight(0)  # Initially collapsed
        self.details_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(52, 73, 94, 0.05);
                border-radius: 8px;
                margin: 4px 0;
            }
        """)

        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(16, 12, 16, 12)
        details_layout.setSpacing(8)

        # File information
        file_info_layout = QHBoxLayout()
        file_info_layout.setSpacing(20)

        # File size
        size_layout = QVBoxLayout()
        size_layout.setSpacing(2)
        size_label = CaptionLabel(tr('task_manager.file_size'))
        # CaptionLabel already styled by qfluentwidgets
        self.file_size_label = BodyLabel("0 MB")
        # BodyLabel already styled by qfluentwidgets
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.file_size_label)

        # Download path
        path_layout = QVBoxLayout()
        path_layout.setSpacing(2)
        path_label = CaptionLabel(tr('task_manager.download_path'))
        # CaptionLabel already styled by qfluentwidgets
        self.download_path_label = BodyLabel(
            self.task_data.get('output_dir', ''))
        # BodyLabel already styled by qfluentwidgets
        self.download_path_label.setWordWrap(True)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.download_path_label)

        file_info_layout.addLayout(size_layout)
        file_info_layout.addLayout(path_layout)
        file_info_layout.addStretch()

        details_layout.addLayout(file_info_layout)

        self.main_layout.addWidget(self.details_widget)

    def _create_actions_section(self) -> None:
        """Create modern action buttons"""
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        # Primary action buttons with beautiful styling
        self.play_btn = PrimaryPushButton(tr('task_manager.start'))
        self.play_btn.setIcon(FIF.PLAY)
        self.play_btn.setFixedHeight(36)
        self.play_btn.clicked.connect(
            lambda: self.playClicked.emit(self.task_id))

        self.pause_btn = PushButton(tr('task_manager.pause'))
        self.pause_btn.setIcon(FIF.PAUSE)
        self.pause_btn.setFixedHeight(36)
        self.pause_btn.clicked.connect(
            lambda: self.pauseClicked.emit(self.task_id))

        self.stop_btn = PushButton(tr('task_manager.stop'))
        self.stop_btn.setIcon(FIF.CANCEL)
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.clicked.connect(
            lambda: self.stopClicked.emit(self.task_id))

        # Danger button for delete
        self.delete_btn = TransparentToolButton(FIF.DELETE)
        self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setToolTip(tr('task_manager.delete'))
        self.delete_btn.setStyleSheet("""
            TransparentToolButton {
                border-radius: 18px;
                background-color: rgba(231, 76, 60, 0.1);
                padding: 8px;
                color: #e74c3c;
            }
            TransparentToolButton:hover {
                background-color: rgba(231, 76, 60, 0.2);
            }
        """)
        self.delete_btn.clicked.connect(
            lambda: self.deleteClicked.emit(self.task_id))

        actions_layout.addWidget(self.play_btn)
        actions_layout.addWidget(self.pause_btn)
        actions_layout.addWidget(self.stop_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.delete_btn)

        self.main_layout.addLayout(actions_layout)

    def _setup_style(self) -> None:
        """Setup beautiful card styling with hover effects"""
        self.setStyleSheet("""
            EnhancedTaskItem {
                background-color: white;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 12px;
                margin: 4px;
            }
            EnhancedTaskItem:hover {
                border: 1px solid rgba(52, 152, 219, 0.3);
                background-color: rgba(52, 152, 219, 0.02);
            }
        """)

    def _setup_animations(self) -> None:
        """Setup smooth animations"""
        self.expand_animation = QPropertyAnimation(
            self.details_widget, QByteArray(b"maximumHeight"))
        self.expand_animation.setDuration(300)
        self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _toggle_expand(self) -> None:
        """Toggle details section with smooth animation"""
        if self.is_expanded:
            # Collapse
            self.expand_animation.setEndValue(0)
            self.expand_btn.setIcon(FIF.DOWN)
            self.expand_btn.setToolTip(tr('task_manager.expand_details'))
        else:
            # Expand
            self.expand_animation.setEndValue(120)  # Approximate height
            self.expand_btn.setIcon(FIF.UP)
            self.expand_btn.setToolTip(tr('task_manager.collapse_details'))

        self.expand_animation.start()
        self.is_expanded = not self.is_expanded

    def _update_status_badge(self, status: str) -> None:
        """Update status badge with appropriate styling"""
        status_map = {
            'downloading': ('downloading', tr('task_manager.status.downloading')),
            'completed': ('completed', tr('task_manager.status.completed')),
            'error': ('error', tr('task_manager.status.error')),
            'paused': ('paused', tr('task_manager.status.paused')),
            'stopped': ('default', tr('task_manager.status.stopped')),
        }

        status_type, status_text = status_map.get(status, ('default', status))
        self.status_badge.update_status(status_type, status_text)


# Legacy compatibility
class TaskManagerCompat:
    """Legacy TaskManager for backward compatibility"""
    pass

# Backward compatibility alias
EnhancedTaskItem = TaskItem


class TaskManager(QWidget):
    """Enhanced task manager with modern Fluent Design"""

    # Signals
    task_action_requested = Signal(str, str)  # task_id, action

    def __init__(self, download_manager, parent=None) -> None:
        super().__init__(parent)
        self.download_manager = download_manager
        self.task_items = {}  # task_id -> ModernTaskItem
        self.filter_status = "all"
        self.search_text = ""
        self._create_ui()
        self._setup_refresh_timer()

    def _create_ui(self) -> None:
        """Create the beautiful modern UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Beautiful header using qfluentwidgets theme
        header_card = ElevatedCardWidget()
        # Use theme color for header background
        theme_color = qconfig.themeColor()
        header_card.setStyleSheet(f"""
            ElevatedCardWidget {{
                background-color: {theme_color.name()};
                border: none;
                border-radius: 12px;
            }}
        """)

        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(30, 24, 30, 24)
        header_layout.setSpacing(20)

        # Title section with stats
        title_section = self._create_title_section()
        header_layout.addLayout(title_section)

        # Controls section
        controls_section = self._create_controls_section()
        header_layout.addLayout(controls_section)

        layout.addWidget(header_card)

        # Task list with beautiful styling
        self._create_task_list_area(layout)

        # Connect signals
        self._connect_signals()

    def _create_title_section(self) -> QHBoxLayout:
        """Create beautiful title section with stats"""
        title_layout = QHBoxLayout()
        title_layout.setSpacing(20)

        # Main title with themed styling
        title_label = StrongBodyLabel(tr("task_manager.title"))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)

        # Statistics cards with themed colors
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        # Active downloads stat
        self.active_stat = self._create_stat_widget(
            tr("task_manager.stats.active"), "0", FIF.DOWNLOAD
        )

        # Completed stat
        self.completed_stat = self._create_stat_widget(
            tr("task_manager.stats.completed"), "0", FIF.ACCEPT
        )

        # Total speed stat
        self.speed_stat = self._create_stat_widget(
            tr("task_manager.stats.speed"), "0 MB/s", FIF.SPEED_HIGH
        )

        stats_layout.addWidget(self.active_stat)
        stats_layout.addWidget(self.completed_stat)
        stats_layout.addWidget(self.speed_stat)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addLayout(stats_layout)

        return title_layout

    def _create_stat_widget(self, label: str, value: str, icon: FIF) -> QWidget:
        """Create a beautiful statistics widget"""
        widget = QWidget()
        widget.setFixedSize(100, 60)
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        # Icon and value row
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        icon_label.setPixmap(icon.icon().pixmap(16, 16))
        icon_label.setStyleSheet("background: transparent;")

        value_label = StrongBodyLabel(value)
        value_label.setStyleSheet(
            "color: white; font-size: 14px; font-weight: 600; background: transparent;")

        top_layout.addWidget(icon_label)
        top_layout.addWidget(value_label)
        top_layout.addStretch()

        # Label
        label_widget = CaptionLabel(label)
        label_widget.setStyleSheet(
            "color: rgba(255, 255, 255, 0.8); font-size: 10px; background: transparent;")

        layout.addLayout(top_layout)
        layout.addWidget(label_widget)

        # Store references for updates using setattr to avoid type checker issues
        setattr(widget, 'value_label', value_label)
        setattr(widget, 'label_widget', label_widget)

        return widget

    def _create_controls_section(self) -> QHBoxLayout:
        """Create modern controls section"""
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)

        # Search with modern styling
        self.search_box = SearchLineEdit()
        self.search_box.setPlaceholderText(
            tr("task_manager.search_placeholder"))
        self.search_box.setFixedWidth(280)
        self.search_box.setStyleSheet("""
            SearchLineEdit {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: white;
                padding: 8px 12px;
            }
            SearchLineEdit:focus {
                border: 2px solid rgba(255, 255, 255, 0.5);
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.search_box.textChanged.connect(self._on_search_changed)

        # Filter dropdown with styling
        self.filter_combo = ComboBox()
        self.filter_combo.addItems([
            tr("task_manager.filter.all"),
            tr("task_manager.filter.downloading"),
            tr("task_manager.filter.paused"),
            tr("task_manager.filter.completed"),
            tr("task_manager.filter.failed")
        ])
        self.filter_combo.setFixedWidth(140)
        self.filter_combo.setStyleSheet("""
            ComboBox {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: white;
                padding: 8px 12px;
            }
        """)
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)

        # Action buttons with modern styling
        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.35);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.5);
            }
        """

        self.start_selected_btn = PushButton(
            tr("task_manager.actions.start_selected"))
        self.start_selected_btn.setIcon(FIF.PLAY)
        self.start_selected_btn.setEnabled(False)
        self.start_selected_btn.setStyleSheet(button_style)

        self.pause_selected_btn = PushButton(
            tr("task_manager.actions.pause_selected"))
        self.pause_selected_btn.setIcon(FIF.PAUSE)
        self.pause_selected_btn.setEnabled(False)
        self.pause_selected_btn.setStyleSheet(button_style)

        self.clear_completed_btn = PushButton(
            tr("task_manager.actions.clear_completed"))
        self.clear_completed_btn.setIcon(FIF.DELETE)
        self.clear_completed_btn.setStyleSheet(button_style)

        controls_layout.addWidget(self.search_box)
        controls_layout.addWidget(self.filter_combo)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(self.start_selected_btn)
        controls_layout.addWidget(self.pause_selected_btn)
        controls_layout.addWidget(self.clear_completed_btn)
        controls_layout.addStretch()

        return controls_layout

    def _create_task_list_area(self, parent_layout: QVBoxLayout) -> None:
        """Create beautiful task list area"""
        # Task list with smooth scrolling and themed styling
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # SmoothScrollArea already has proper styling from qfluentwidgets
        # No custom styling needed

        # Task container
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setSpacing(12)

        # Beautiful empty state
        self.empty_widget = self._create_beautiful_empty_state()
        self.task_layout.addWidget(self.empty_widget)

        self.task_layout.addStretch()

        self.scroll_area.setWidget(self.task_container)
        parent_layout.addWidget(self.scroll_area, 1)

    def _create_beautiful_empty_state(self) -> QWidget:
        """Create beautiful empty state widget with themed design"""
        widget = ElevatedCardWidget()
        # Let qfluentwidgets handle the styling
        widget.setObjectName("empty-state")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Animated icon container
        icon_container = QWidget()
        icon_container.setFixedSize(120, 120)
        icon_container.setStyleSheet("""
            QWidget {
                background-color: #667eea;
                border-radius: 60px;
            }
        """)

        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setPixmap(FIF.DOWNLOAD.icon().pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent; color: white;")
        icon_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Text content
        title_label = StrongBodyLabel(tr("task_manager.empty.title"))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #2c3e50;
                background: transparent;
            }
        """)

        desc_label = BodyLabel(tr("task_manager.empty.description"))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                line-height: 1.5;
                background: transparent;
            }
        """)

        # Action button - removed for simplicity
        layout.addWidget(icon_container, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        return widget

    def _setup_refresh_timer(self) -> None:
        """Setup timer for refreshing task display"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_tasks)
        self.refresh_timer.start(1000)  # Refresh every second

    def _connect_signals(self) -> None:
        """Connect UI signals"""
        self.clear_completed_btn.clicked.connect(self._clear_completed_tasks)
        # Note: select_all_check was removed in the new design

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change"""
        self.search_text = text.lower()
        self._filter_tasks()

    def _on_filter_changed(self, status: str) -> None:
        """Handle filter change"""
        self.filter_status = status.lower()
        self._filter_tasks()

    def _filter_tasks(self) -> None:
        """Filter visible tasks based on search and status"""
        for task_item in self.task_items.values():
            should_show = True

            # Filter by search text
            if self.search_text:
                task_name = task_item.task_data.get('name', '').lower()
                task_url = task_item.task_data.get('url', '').lower()
                should_show = (self.search_text in task_name or
                               self.search_text in task_url)

            # Filter by status
            if should_show and self.filter_status != "all":
                task_status = task_item.task_data.get('status', '').lower()
                should_show = self.filter_status in task_status

            task_item.setVisible(should_show)

        self._update_summary()

    def _update_summary(self) -> None:
        """Update task statistics"""
        visible_count = sum(
            1 for item in self.task_items.values() if item.isVisible())
        total_count = len(self.task_items)

        # Update statistics widgets
        active_count = sum(1 for item in self.task_items.values()
                           if hasattr(item, 'task_data') and
                           item.task_data.get('status') == 'downloading')
        completed_count = sum(1 for item in self.task_items.values()
                              if hasattr(item, 'task_data') and
                              item.task_data.get('status') == 'completed')

        # Calculate total speed
        total_speed = sum(item.task_data.get('speed', 0) for item in self.task_items.values()
                          if hasattr(item, 'task_data') and
                          item.task_data.get('status') == 'downloading')

        # Update stat widgets using getattr to avoid type checker issues
        if hasattr(self, 'active_stat'):
            value_label = getattr(self.active_stat, 'value_label', None)
            if value_label:
                value_label.setText(str(active_count))
        if hasattr(self, 'completed_stat'):
            value_label = getattr(self.completed_stat, 'value_label', None)
            if value_label:
                value_label.setText(str(completed_count))
        if hasattr(self, 'speed_stat'):
            value_label = getattr(self.speed_stat, 'value_label', None)
            if value_label:
                value_label.setText(format_speed(total_speed))

    def _refresh_tasks(self) -> None:
        """Refresh task data from download manager"""
        if not self.download_manager:
            return

        # This would typically sync with the actual download manager
        # For now, we'll just update the display
        self._update_summary()

    def _clear_completed_tasks(self) -> None:
        """Clear all completed tasks"""
        completed_items = []
        for task_id, task_item in self.task_items.items():
            if task_item.task_data.get('status', '').lower() == 'completed':
                completed_items.append(task_id)

        for task_id in completed_items:
            self.remove_task(task_id)

    def _on_select_all_toggled(self, checked: bool) -> None:
        """Handle select all toggle"""
        # This would implement bulk selection
        # For now, just enable/disable bulk action buttons
        self.start_selected_btn.setEnabled(checked)
        self.pause_selected_btn.setEnabled(checked)

    def add_task(self, task_id: str, task_data: dict) -> None:
        """Add a new task item"""
        if task_id in self.task_items:
            return

        # Hide empty state
        self.empty_widget.setVisible(False)

        # Create task item
        task_item = ModernTaskItem(task_id, task_data)

        # Connect signals
        task_item.playClicked.connect(
            lambda tid: self.task_action_requested.emit(tid, "start"))
        task_item.pauseClicked.connect(
            lambda tid: self.task_action_requested.emit(tid, "pause"))
        task_item.stopClicked.connect(
            lambda tid: self.task_action_requested.emit(tid, "stop"))
        task_item.deleteClicked.connect(
            lambda tid: self.task_action_requested.emit(tid, "delete"))

        # Add to layout (insert before stretch)
        self.task_layout.insertWidget(self.task_layout.count() - 1, task_item)
        self.task_items[task_id] = task_item

        self._update_summary()

    def remove_task(self, task_id: str) -> None:
        """Remove a task item"""
        if task_id not in self.task_items:
            return

        task_item = self.task_items[task_id]
        self.task_layout.removeWidget(task_item)
        task_item.deleteLater()
        del self.task_items[task_id]

        # Show empty state if no tasks
        if not self.task_items:
            self.empty_widget.setVisible(True)

        self._update_summary()

    def update_task_progress(self, task_id: str, progress_data: dict) -> None:
        """Update progress for a specific task with error handling"""
        try:
            if task_id in self.task_items:
                task_item = self.task_items[task_id]
                task_item.update_progress(progress_data)
                self._update_summary()
            else:
                # If task doesn't exist, try to create it from download manager
                self._refresh_tasks()
        except Exception as e:
            print(f"Error updating task progress for {task_id}: {e}")

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update status for a specific task with error handling"""
        try:
            if task_id in self.task_items:
                task_item = self.task_items[task_id]
                task_item.update_status(status)
                self._update_summary()
                self._filter_tasks()  # Re-apply filters as status might affect visibility
            else:
                # If task doesn't exist, try to create it from download manager
                self._refresh_tasks()
        except Exception as e:
            print(f"Error updating task status for {task_id}: {e}")

    def _create_task_item_safe(self, task_id: str, task) -> None:
        """Create a new task item widget safely"""
        try:
            # Extract task data safely
            task_data = {
                'name': getattr(task, 'name', f'Task {task_id[:8]}'),
                'url': getattr(task, 'base_url', 'Unknown URL'),
                'status': str(getattr(task, 'status', 'unknown')).lower(),
                'progress': 0,
                'speed': '0 B/s',
                'size_info': '',
                'eta': ''
            }

            # Get progress data if available
            if hasattr(task, 'progress'):
                progress = getattr(task, 'progress', {})
                if isinstance(progress, dict):
                    task_data.update({
                        'progress': progress.get('completed', 0) / max(progress.get('total', 1), 1) * 100,
                        'speed': progress.get('speed', 0),
                        'downloaded_bytes': progress.get('downloaded_bytes', 0),
                        'total': progress.get('total', 0),
                        'completed': progress.get('completed', 0),
                        'estimated_time': progress.get('estimated_time', None)
                    })

            # Create task item widget
            task_item = ModernTaskItem(task_id, task_data, self)

            # Connect signals
            task_item.playClicked.connect(
                lambda tid: self.task_action_requested.emit(tid, 'start'))
            task_item.pauseClicked.connect(
                lambda tid: self.task_action_requested.emit(tid, 'pause'))
            task_item.stopClicked.connect(
                lambda tid: self.task_action_requested.emit(tid, 'stop'))
            task_item.deleteClicked.connect(
                lambda tid: self._confirm_delete_task(tid))

            self.task_items[task_id] = task_item
            self.task_layout.addWidget(task_item)

            # Hide empty state if this is the first task
            if len(self.task_items) == 1:
                self.empty_widget.setVisible(False)

        except Exception as e:
            print(f"Error creating task item for {task_id}: {e}")

    def _update_task_item_safe(self, task_id: str, task) -> None:
        """Update existing task item with latest data safely"""
        try:
            if task_id in self.task_items:
                task_item = self.task_items[task_id]

                # Update status
                status = str(getattr(task, 'status', 'unknown')).lower()
                task_item.update_status(status)

                # Update progress
                if hasattr(task, 'progress'):
                    progress = getattr(task, 'progress', {})
                    if isinstance(progress, dict):
                        task_item.update_progress(progress)
        except Exception as e:
            print(f"Error updating task item for {task_id}: {e}")

    def _remove_task_item_safe(self, task_id: str) -> None:
        """Remove a task item widget safely"""
        try:
            if task_id in self.task_items:
                task_item = self.task_items[task_id]
                self.task_layout.removeWidget(task_item)
                task_item.deleteLater()
                del self.task_items[task_id]

                # Show empty state if no tasks remain
                if len(self.task_items) == 0:
                    self.empty_widget.setVisible(True)
        except Exception as e:
            print(f"Error removing task item for {task_id}: {e}")

    def _confirm_delete_task(self, task_id: str) -> None:
        """Show confirmation dialog before deleting task"""
        try:
            from PySide6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this download task?\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.task_action_requested.emit(task_id, 'delete')
        except Exception as e:
            print(f"Error showing delete confirmation for {task_id}: {e}")

    def refresh_from_manager(self) -> None:
        """Refresh task list from download manager with proper sync"""
        try:
            if not self.download_manager or not hasattr(self.download_manager, 'tasks'):
                return

            current_task_ids = set(self.task_items.keys())
            manager_task_ids = set()

            # Get tasks from download manager
            tasks = getattr(self.download_manager, 'tasks', {})
            if isinstance(tasks, dict):
                for task_id, task in tasks.items():
                    manager_task_ids.add(task_id)
                    if task_id not in self.task_items:
                        self._create_task_item_safe(task_id, task)
                    else:
                        # Update existing task item
                        self._update_task_item_safe(task_id, task)

            # Remove tasks that no longer exist in the manager
            removed_tasks = current_task_ids - manager_task_ids
            for task_id in removed_tasks:
                self._remove_task_item_safe(task_id)

            self._update_summary()
            self._filter_tasks()
        except Exception as e:
            print(f"Error refreshing tasks from manager: {e}")

    # ...existing code...

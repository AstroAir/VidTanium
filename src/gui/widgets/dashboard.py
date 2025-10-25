"""
Dashboard Components for VidTanium
Modern dashboard with improved visual hierarchy and interactive elements
"""

from typing import Dict, List, Optional, Any

__all__ = ['Dashboard']
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QProgressBar, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtGui import QFont, QPainter, QPainterPath, QColor, QPixmap

from qfluentwidgets import (
    ElevatedCardWidget, HeaderCardWidget, FluentIcon as FIF,
    TitleLabel, SubtitleLabel, BodyLabel, StrongBodyLabel, CaptionLabel,
    PrimaryPushButton, TransparentToolButton, ProgressBar, ProgressRing,
    IconWidget, Theme, isDarkTheme
)

from ..utils.design_system import (
    DesignSystem, AnimatedCard, GradientCard, ModernProgressCard
)


class MetricCard(AnimatedCard):
    """Enhanced metric card with animations and modern styling"""
    
    def __init__(self, title: str, value: str, icon: FIF,
                 trend: Optional[str] = None, color: str = "primary", parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.trend = trend
        self.color = color

        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self) -> None:
        """Setup metric card UI"""
        self.setFixedHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Header with icon and trend
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Icon
        self.icon_widget = IconWidget(self.icon)
        self.icon_widget.setFixedSize(24, 24)
        header_layout.addWidget(self.icon_widget)
        
        header_layout.addStretch()
        
        # Trend indicator
        if self.trend:
            self.trend_label = CaptionLabel(self.trend)
            trend_color = DesignSystem.get_color('success' if '+' in self.trend else 'error')
            self.trend_label.setStyleSheet(f"""
                color: {trend_color};
                font-weight: 600;
                background: {trend_color}20;
                padding: 2px 6px;
                border-radius: 8px;
            """)
            header_layout.addWidget(self.trend_label)

        layout.addLayout(header_layout)

        # Value
        self.value_label = TitleLabel(self.value)
        self.value_label.setStyleSheet(f"""
            {DesignSystem.get_typography_style('title_large')}
            color: {DesignSystem.get_color(self.color)};
            font-weight: 700;
        """)
        layout.addWidget(self.value_label)

        # Title
        self.title_label = BodyLabel(self.title)
        self.title_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_secondary_adaptive')};
        """)
        layout.addWidget(self.title_label)
    
    def _setup_animations(self) -> None:
        """Setup value change animations"""
        if hasattr(self, 'value_label'):
            self.value_animation = QPropertyAnimation(self.value_label, b"geometry")
            self.value_animation.setDuration(300)
            self.value_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def update_value(self, new_value: str, new_trend: Optional[str] = None) -> None:
        """Update metric value with animation"""
        self.value = new_value
        self.value_label.setText(new_value)
        
        if new_trend and hasattr(self, 'trend_label'):
            self.trend = new_trend
            self.trend_label.setText(new_trend)
            trend_color = DesignSystem.get_color('success' if '+' in new_trend else 'error')
            self.trend_label.setStyleSheet(f"""
                color: {trend_color};
                font-weight: 600;
                background: {trend_color}20;
                padding: 2px 6px;
                border-radius: 8px;
            """)


class ActivityCard(AnimatedCard):
    """Enhanced activity card showing recent activities"""
    
    def __init__(self, title: str = "Recent Activity", parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.activities: List[Dict[str, Any]] = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup activity card UI"""
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = SubtitleLabel(self.title)
        title_label.setStyleSheet(DesignSystem.get_typography_style('subtitle'))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # View all button
        view_all_btn = TransparentToolButton(FIF.MORE)
        view_all_btn.setFixedSize(32, 32)
        header_layout.addWidget(view_all_btn)
        
        layout.addLayout(header_layout)
        
        # Activities container
        self.activities_container = QWidget()
        self.activities_layout = QVBoxLayout(self.activities_container)
        self.activities_layout.setContentsMargins(0, 0, 0, 0)
        self.activities_layout.setSpacing(12)
        
        layout.addWidget(self.activities_container)
        layout.addStretch()
    
    def add_activity(self, icon: FIF, title: str, description: str, time: str) -> None:
        """Add activity item"""
        activity_widget = self._create_activity_item(icon, title, description, time)
        self.activities_layout.addWidget(activity_widget)
        
        # Keep only last 5 activities
        if self.activities_layout.count() > 5:
            old_item = self.activities_layout.takeAt(0)
            if old_item.widget():
                old_item.widget().deleteLater()
    
    def _create_activity_item(self, icon: FIF, title: str, description: str, time: str) -> QWidget:
        """Create individual activity item"""
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)
        
        # Icon
        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(20, 20)
        layout.addWidget(icon_widget)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        title_label = BodyLabel(title)
        title_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_primary_adaptive')};
            font-weight: 500;
        """)
        content_layout.addWidget(title_label)

        desc_label = CaptionLabel(description)
        desc_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_secondary_adaptive')};
        """)
        content_layout.addWidget(desc_label)

        layout.addLayout(content_layout)
        layout.addStretch()

        # Time
        time_label = CaptionLabel(time)
        time_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_secondary_adaptive')};
        """)
        layout.addWidget(time_label)
        
        return item


class QuickActionsCard(AnimatedCard):
    """Enhanced quick actions card with modern buttons"""
    
    action_clicked = Signal(str)
    
    def __init__(self, title: str = "Quick Actions", parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup quick actions UI"""
        self.setFixedHeight(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Header
        title_label = SubtitleLabel(self.title)
        title_label.setStyleSheet(DesignSystem.get_typography_style('subtitle'))
        layout.addWidget(title_label)
        
        # Actions grid
        actions_layout = QGridLayout()
        actions_layout.setSpacing(12)
        
        # Define quick actions
        actions = [
            ("new_task", FIF.ADD, "New Task"),
            ("batch_download", FIF.DOWNLOAD, "Batch Download"),
            ("schedule", FIF.CALENDAR, "Schedule"),
            ("settings", FIF.SETTING, "Settings"),
        ]
        
        for i, (action_id, icon, text) in enumerate(actions):
            btn = self._create_action_button(action_id, icon, text)
            row, col = divmod(i, 2)
            actions_layout.addWidget(btn, row, col)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
    
    def _create_action_button(self, action_id: str, icon: FIF, text: str) -> QWidget:
        """Create action button"""
        button = AnimatedCard()
        button.setFixedHeight(60)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(button)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(24, 24)
        layout.addWidget(icon_widget)
        
        # Text
        text_label = BodyLabel(text)
        text_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_primary_adaptive')};
            font-weight: 500;
        """)
        layout.addWidget(text_label)
        
        layout.addStretch()
        
        # Connect click event
        def on_click() -> None:
            self.action_clicked.emit(action_id)
        
        button.mousePressEvent = lambda e: on_click() if e.button() == Qt.MouseButton.LeftButton else None
        
        return button


class Dashboard(QWidget):
    """Dashboard with modern layout and components"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._setup_demo_data()
    
    def _setup_ui(self) -> None:
        """Setup dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Metrics row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        self.active_tasks_metric = MetricCard("Active Tasks", "0", FIF.DOWNLOAD, "+2", "primary")
        self.completed_metric = MetricCard("Completed", "0", FIF.ACCEPT, "+5", "success")
        self.speed_metric = MetricCard("Speed", "0 MB/s", FIF.SPEED_HIGH, color="info")
        
        metrics_layout.addWidget(self.active_tasks_metric)
        metrics_layout.addWidget(self.completed_metric)
        metrics_layout.addWidget(self.speed_metric)
        
        layout.addLayout(metrics_layout)
        
        # Content row
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # Left column
        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        
        self.activity_card = ActivityCard()
        left_column.addWidget(self.activity_card)
        
        content_layout.addLayout(left_column, 2)
        
        # Right column
        right_column = QVBoxLayout()
        right_column.setSpacing(16)
        
        self.quick_actions = QuickActionsCard()
        self.quick_actions.action_clicked.connect(self._handle_quick_action)
        right_column.addWidget(self.quick_actions)
        
        right_column.addStretch()
        
        content_layout.addLayout(right_column, 1)
        
        layout.addLayout(content_layout)
    
    def _create_header(self) -> QWidget:
        """Create dashboard header"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = TitleLabel("Dashboard")
        title.setStyleSheet(DesignSystem.get_typography_style('display'))
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = PrimaryPushButton("Refresh")
        refresh_btn.setIcon(FIF.SYNC)
        layout.addWidget(refresh_btn)
        
        return header
    
    def _setup_demo_data(self) -> None:
        """Setup demo data for the dashboard"""
        # Add some demo activities
        self.activity_card.add_activity(
            FIF.DOWNLOAD, "Download Started", "video.mp4 - 1.2 GB", "2 min ago"
        )
        self.activity_card.add_activity(
            FIF.ACCEPT, "Download Completed", "movie.mkv - 4.5 GB", "5 min ago"
        )
        self.activity_card.add_activity(
            FIF.ADD, "Task Created", "Batch download - 15 items", "10 min ago"
        )
    
    def _handle_quick_action(self, action_id: str) -> None:
        """Handle quick action clicks"""
        print(f"Quick action clicked: {action_id}")
        # This would be connected to the main application's routing system

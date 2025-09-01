"""
Status Widget for VidTanium
Provides comprehensive status feedback and progress reporting with detailed information
"""

import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPainter, QPainterPath, QColor, QLinearGradient

from qfluentwidgets import (
    FluentIcon as FIF, ProgressBar, ProgressRing,
    BodyLabel, CaptionLabel, StrongBodyLabel,
    ElevatedCardWidget, TransparentToolButton
)

from ..utils.i18n import tr
from ..utils.theme import VidTaniumTheme
from ..utils.formatters import format_size, format_speed, format_duration
from ..utils.responsive import ResponsiveWidget, ResponsiveManager


@dataclass
class StatusInfo:
    """Comprehensive status information"""
    status: str
    progress: float  # 0.0 to 1.0
    current_file: Optional[str] = None
    speed: Optional[float] = None  # bytes per second
    eta: Optional[float] = None  # seconds remaining
    completed_items: int = 0
    total_items: int = 0
    bytes_downloaded: int = 0
    total_bytes: int = 0
    error_count: int = 0
    retry_count: int = 0
    start_time: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None


class StatusBadge(QWidget):
    """Animated status badge with color coding"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_text = ""
        self.status_color = VidTaniumTheme.TEXT_SECONDARY
        self.is_animated = False
        self.setFixedHeight(24)
        self.setMinimumWidth(80)
        
        # Animation for pulsing effect
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        self._setup_style()
    
    def _setup_style(self):
        """Setup styling"""
        self.setStyleSheet(f"""
            QWidget {{
                background: {VidTaniumTheme.BG_SURFACE};
                border: 1px solid {VidTaniumTheme.BORDER_COLOR};
                border-radius: 12px;
                padding: 4px 12px;
            }}
        """)
    
    def update_status(self, status: str, animated: bool = False):
        """Update status with optional animation"""
        self.status_text = status
        self.is_animated = animated
        
        # Set color based on status
        status_colors = {
            "downloading": VidTaniumTheme.SUCCESS_GREEN,
            "paused": VidTaniumTheme.WARNING_ORANGE,
            "completed": VidTaniumTheme.ACCENT_CYAN,
            "failed": VidTaniumTheme.ERROR_RED,
            "pending": VidTaniumTheme.TEXT_SECONDARY,
            "canceled": VidTaniumTheme.TEXT_DISABLED
        }
        
        self.status_color = status_colors.get(status.lower(), VidTaniumTheme.TEXT_SECONDARY)
        
        if animated and status.lower() == "downloading":
            self._start_pulse_animation()
        else:
            self._stop_pulse_animation()
        
        self.update()
    
    def _start_pulse_animation(self):
        """Start pulsing animation for active status"""
        if not self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.setLoopCount(-1)  # Infinite loop
            self.animation.start()
    
    def _stop_pulse_animation(self):
        """Stop pulsing animation"""
        if self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.stop()
    
    def paintEvent(self, event):
        """Custom paint event for status badge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        rect = self.rect()
        painter.fillRect(rect, QColor(self.status_color + "20"))
        
        # Border
        painter.setPen(QColor(self.status_color))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 12, 12)
        
        # Text
        painter.setPen(QColor(self.status_color))
        font = painter.font()
        font.setWeight(QFont.Weight.Bold)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.status_text)


class ProgressMetricsWidget(QWidget):
    """Widget displaying detailed progress metrics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QGridLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Speed metric
        self.speed_label = CaptionLabel(tr("status.speed"))
        self.speed_value = BodyLabel("--")
        self.speed_value.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: 500;")
        layout.addWidget(self.speed_label, 0, 0)
        layout.addWidget(self.speed_value, 0, 1)
        
        # ETA metric
        self.eta_label = CaptionLabel(tr("status.eta"))
        self.eta_value = BodyLabel("--")
        self.eta_value.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: 500;")
        layout.addWidget(self.eta_label, 0, 2)
        layout.addWidget(self.eta_value, 0, 3)
        
        # Progress metric
        self.progress_label = CaptionLabel(tr("status.progress"))
        self.progress_value = BodyLabel("--")
        self.progress_value.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: 500;")
        layout.addWidget(self.progress_label, 1, 0)
        layout.addWidget(self.progress_value, 1, 1)
        
        # Size metric
        self.size_label = CaptionLabel(tr("status.size"))
        self.size_value = BodyLabel("--")
        self.size_value.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: 500;")
        layout.addWidget(self.size_label, 1, 2)
        layout.addWidget(self.size_value, 1, 3)
        
        # Set column stretch
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
    
    def update_metrics(self, status_info: StatusInfo):
        """Update all metrics"""
        # Speed
        if status_info.speed is not None and status_info.speed > 0:
            self.speed_value.setText(format_speed(status_info.speed))
        else:
            self.speed_value.setText("--")
        
        # ETA
        if status_info.eta is not None and status_info.eta > 0:
            self.eta_value.setText(format_duration(status_info.eta))
        else:
            self.eta_value.setText("--")
        
        # Progress
        if status_info.total_items > 0:
            progress_text = f"{status_info.completed_items}/{status_info.total_items}"
            if status_info.progress > 0:
                progress_text += f" ({status_info.progress:.1f}%)"
            self.progress_value.setText(progress_text)
        else:
            self.progress_value.setText(f"{status_info.progress:.1f}%")
        
        # Size
        if status_info.total_bytes > 0:
            size_text = f"{format_size(status_info.bytes_downloaded)} / {format_size(status_info.total_bytes)}"
            self.size_value.setText(size_text)
        elif status_info.bytes_downloaded > 0:
            self.size_value.setText(format_size(status_info.bytes_downloaded))
        else:
            self.size_value.setText("--")


class StatusProgressBar(ProgressBar):
    """Progress bar with gradient and animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self.gradient_colors = [VidTaniumTheme.SUCCESS_GREEN, VidTaniumTheme.ACCENT_CYAN]
        self._setup_style()
    
    def _setup_style(self):
        """Setup enhanced styling"""
        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: {VidTaniumTheme.BG_SURFACE};
                text-align: center;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.gradient_colors[0]},
                    stop:1 {self.gradient_colors[1]});
            }}
        """)
    
    def set_gradient_colors(self, start_color: str, end_color: str):
        """Set custom gradient colors"""
        self.gradient_colors = [start_color, end_color]
        self._setup_style()


class CurrentFileWidget(QWidget):
    """Widget displaying current file being processed"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # File icon
        self.file_icon = QLabel()
        self.file_icon.setPixmap(FIF.DOCUMENT.icon().pixmap(16, 16))
        layout.addWidget(self.file_icon)
        
        # File name
        self.file_label = CaptionLabel(tr("status.current_file"))
        self.file_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        layout.addWidget(self.file_label)
        
        self.file_name = BodyLabel("--")
        self.file_name.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: 500;")
        layout.addWidget(self.file_name)
        
        layout.addStretch()
    
    def update_current_file(self, filename: Optional[str]):
        """Update current file display"""
        if filename:
            # Truncate long filenames
            display_name = filename
            if len(display_name) > 50:
                display_name = display_name[:47] + "..."
            self.file_name.setText(display_name)
            self.file_name.setToolTip(filename)
        else:
            self.file_name.setText("--")
            self.file_name.setToolTip("")


class StatusWidget(ElevatedCardWidget, ResponsiveWidget):
    """Status widget with comprehensive progress reporting"""
    
    status_clicked = Signal(str)  # task_id
    
    def __init__(self, task_id: str, parent=None):
        ElevatedCardWidget.__init__(self, parent)
        ResponsiveWidget.__init__(self)
        
        self.task_id = task_id
        self.current_status = StatusInfo(status="pending", progress=0.0)
        self.responsive_manager = ResponsiveManager.instance()
        
        self._setup_ui()
        self._setup_responsive()
        
        # Update timer for smooth animations
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # Update every 100ms
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Header with status badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        self.status_badge = StatusBadge()
        header_layout.addWidget(self.status_badge)
        
        header_layout.addStretch()
        
        # Action button
        self.action_button = TransparentToolButton(FIF.MORE)
        self.action_button.setFixedSize(24, 24)
        self.action_button.clicked.connect(lambda: self.status_clicked.emit(self.task_id))
        header_layout.addWidget(self.action_button)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = StatusProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Current file widget
        self.current_file_widget = CurrentFileWidget()
        layout.addWidget(self.current_file_widget)
        
        # Metrics widget
        self.metrics_widget = ProgressMetricsWidget()
        layout.addWidget(self.metrics_widget)
        
        # Error/retry info (initially hidden)
        self.error_info_widget = QWidget()
        error_layout = QHBoxLayout(self.error_info_widget)
        error_layout.setContentsMargins(0, 0, 0, 0)
        error_layout.setSpacing(8)
        
        self.error_icon = QLabel()
        self.error_icon.setPixmap(FIF.WARNING.icon().pixmap(16, 16))
        error_layout.addWidget(self.error_icon)
        
        self.error_text = CaptionLabel("")
        self.error_text.setStyleSheet(f"color: {VidTaniumTheme.WARNING_ORANGE};")
        error_layout.addWidget(self.error_text)
        
        error_layout.addStretch()
        
        self.error_info_widget.setVisible(False)
        layout.addWidget(self.error_info_widget)
    
    def _setup_responsive(self):
        """Setup responsive behavior"""
        self.responsive_manager.size_changed.connect(self._on_size_changed)
    
    def _on_size_changed(self, size_category: str):
        """Handle responsive size changes"""
        if size_category == "compact":
            self.metrics_widget.setVisible(False)
            self.current_file_widget.setVisible(False)
        else:
            self.metrics_widget.setVisible(True)
            self.current_file_widget.setVisible(True)
    
    def update_status(self, status_info: StatusInfo):
        """Update status information"""
        self.current_status = status_info
        self._update_display()
    
    def _update_display(self):
        """Update all display elements"""
        status_info = self.current_status
        
        # Update status badge
        self.status_badge.update_status(
            status_info.status,
            animated=(status_info.status.lower() == "downloading")
        )
        
        # Update progress bar
        progress_value = int(status_info.progress * 100)
        self.progress_bar.setValue(progress_value)
        
        # Set progress bar colors based on status
        if status_info.status.lower() == "downloading":
            self.progress_bar.set_gradient_colors(
                VidTaniumTheme.SUCCESS_GREEN,
                VidTaniumTheme.ACCENT_CYAN
            )
        elif status_info.status.lower() == "paused":
            self.progress_bar.set_gradient_colors(
                VidTaniumTheme.WARNING_ORANGE,
                VidTaniumTheme.WARNING_ORANGE
            )
        elif status_info.status.lower() == "failed":
            self.progress_bar.set_gradient_colors(
                VidTaniumTheme.ERROR_RED,
                VidTaniumTheme.ERROR_RED
            )
        
        # Update current file
        self.current_file_widget.update_current_file(status_info.current_file)
        
        # Update metrics
        self.metrics_widget.update_metrics(status_info)
        
        # Update error/retry info
        if status_info.error_count > 0 or status_info.retry_count > 0:
            error_text = ""
            if status_info.retry_count > 0:
                error_text += f"Retry {status_info.retry_count}"
            if status_info.error_count > 0:
                if error_text:
                    error_text += f", {status_info.error_count} errors"
                else:
                    error_text = f"{status_info.error_count} errors"
            
            self.error_text.setText(error_text)
            self.error_info_widget.setVisible(True)
        else:
            self.error_info_widget.setVisible(False)

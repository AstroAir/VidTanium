"""
Progress Components for VidTanium
Modern progress indicators with smooth animations and better visual feedback
"""

from typing import Optional, Union, Dict, Any
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QRect, QByteArray
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtGui import QPainter, QPainterPath, QColor, QFont, QLinearGradient

from qfluentwidgets import (
    ProgressBar, ProgressRing, IndeterminateProgressRing,
    ElevatedCardWidget, BodyLabel, CaptionLabel, FluentIcon as FIF,
    TransparentToolButton
)

from ..utils.design_system import DesignSystem, AnimatedCard
from ..utils.unified_design_system import UnifiedDesignSystem as DS


class ProgressCard(AnimatedCard):
    """Progress card with detailed information and controls"""
    
    pause_clicked = Signal()
    cancel_clicked = Signal()
    
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.progress_value = 0
        self.is_paused = False
        self.speed = "0 MB/s"
        self.eta = "Unknown"
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self) -> None:
        """Setup progress card UI"""
        self.setMinimumHeight(140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        
        self.title_label = BodyLabel(self.title)
        self.title_label.setStyleSheet(f"""
            {DesignSystem.get_typography_style('body')}
            color: {DS.color('on_surface')};
            font-weight: 600;
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Control buttons
        self.pause_btn = TransparentToolButton(FIF.PAUSE)
        self.pause_btn.setFixedSize(28, 28)
        self.pause_btn.clicked.connect(self._toggle_pause)
        header_layout.addWidget(self.pause_btn)
        
        self.cancel_btn = TransparentToolButton(FIF.CANCEL)
        self.cancel_btn.setFixedSize(28, 28)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        header_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(f"""
            ProgressBar {{
                background: {DS.color('surface_variant')};
                border-radius: 4px;
            }}
            ProgressBar::chunk {{
                background-color: {DS.color('primary')}});
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Progress info
        info_layout = QHBoxLayout()
        
        self.progress_label = CaptionLabel("0%")
        self.progress_label.setStyleSheet(f"""
            color: {DS.color('on_surface_variant')};
            font-weight: 500;
        """)
        info_layout.addWidget(self.progress_label)

        info_layout.addStretch()

        self.speed_label = CaptionLabel(self.speed)
        self.speed_label.setStyleSheet(f"""
            color: {DS.color('on_surface_variant')};
        """)
        info_layout.addWidget(self.speed_label)

        self.eta_label = CaptionLabel(f"ETA: {self.eta}")
        self.eta_label.setStyleSheet(f"""
            color: {DS.color('on_surface_variant')};
        """)
        info_layout.addWidget(self.eta_label)
        
        layout.addLayout(info_layout)
    
    def _setup_animations(self) -> None:
        """Setup progress animations"""
        if hasattr(self, 'progress_bar'):
            self.progress_animation = QPropertyAnimation(self.progress_bar, QByteArray(b"value"))
            self.progress_animation.setDuration(500)
            self.progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def _toggle_pause(self) -> None:
        """Toggle pause state"""
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.setIcon(FIF.PLAY)
            self.setStyleSheet(f"""
                ProgressCard {{
                    border-left: 4px solid {DS.color('warning')};
                }}
            """)
        else:
            self.pause_btn.setIcon(FIF.PAUSE)
            self.setStyleSheet("")
        
        self.pause_clicked.emit()
    
    def update_progress(self, value: int, speed: Optional[str] = None, eta: Optional[str] = None) -> None:
        """Update progress with animation"""
        # Animate progress bar if available
        if hasattr(self, 'progress_animation') and hasattr(self, 'progress_bar'):
            self.progress_animation.setStartValue(self.progress_value)
            self.progress_animation.setEndValue(value)
            self.progress_animation.start()

        self.progress_value = value
        if hasattr(self, 'progress_label'):
            self.progress_label.setText(f"{value}%")

        if speed and hasattr(self, 'speed_label'):
            self.speed = speed
            self.speed_label.setText(speed)

        if eta and hasattr(self, 'eta_label'):
            self.eta = eta
            self.eta_label.setText(f"ETA: {eta}")
    
    def set_completed(self) -> None:
        """Set progress as completed"""
        self.update_progress(100)
        self.setStyleSheet(f"""
            ProgressCard {{
                border-left: 4px solid {DS.color('success')};
            }}
        """)
        self.pause_btn.hide()
        self.cancel_btn.hide()

    def set_error(self, error_message: str = "Error occurred") -> None:
        """Set progress as error state"""
        self.setStyleSheet(f"""
            ProgressCard {{
                border-left: 4px solid {DS.color('error')};
            }}
        """)
        self.speed_label.setText(error_message)
        self.speed_label.setStyleSheet(f"""
            color: {DS.color('error')};
        """)


class CircularProgressCard(AnimatedCard):
    """Circular progress card for compact display"""
    
    def __init__(self, title: str, size: int = 80, parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.size = size
        self.progress_value = 0
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup circular progress UI"""
        self.setFixedSize(140, 120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Circular progress
        self.progress_ring = ProgressRing()
        self.progress_ring.setFixedSize(self.size, self.size)
        self.progress_ring.setStyleSheet(f"""
            ProgressRing {{
                qproperty-backgroundColor: {DS.color('surface_variant')};
                qproperty-progressColor: {DS.color('primary')};
            }}
        """)
        layout.addWidget(self.progress_ring, 0, Qt.AlignmentFlag.AlignCenter)

        # Title
        self.title_label = CaptionLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"""
            color: {DS.color('on_surface_variant')};
            font-weight: 500;
        """)
        layout.addWidget(self.title_label)
    
    def update_progress(self, value: int) -> None:
        """Update circular progress"""
        self.progress_value = value
        self.progress_ring.setValue(value)


class ProgressSummaryCard(AnimatedCard):
    """Summary card showing overall progress statistics"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.stats = {
            'total': 0,
            'completed': 0,
            'active': 0,
            'failed': 0
        }
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup progress summary UI"""
        self.setFixedHeight(100)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(24)
        
        # Create stat items
        self.total_stat = self._create_stat_item("Total", "0", "text_primary_adaptive")
        self.completed_stat = self._create_stat_item("Completed", "0", "success")
        self.active_stat = self._create_stat_item("Active", "0", "primary")
        self.failed_stat = self._create_stat_item("Failed", "0", "error")
        
        layout.addWidget(self.total_stat)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.completed_stat)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.active_stat)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.failed_stat)
    
    def _create_stat_item(self, label: str, value: str, color: str) -> QWidget:
        """Create individual stat item"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Value
        value_label = BodyLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"""
            {DesignSystem.get_typography_style('title')}
            color: {DesignSystem.get_color(color)};
            font-weight: 700;
        """)
        layout.addWidget(value_label)

        # Label
        label_widget = CaptionLabel(label)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_widget.setStyleSheet(f"""
            color: {DS.color('on_surface_variant')};
        """)
        layout.addWidget(label_widget)
        
        # Store reference for updates
        setattr(widget, 'value_label', value_label)
        
        return widget
    
    def _create_separator(self) -> QWidget:
        """Create separator between stats"""
        separator = QLabel("|")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator.setStyleSheet(f"""
            color: {DS.color('outline')};
            font-size: 16px;
        """)
        return separator
    
    def update_stats(self, stats: Dict[str, int]) -> None:
        """Update progress statistics"""
        self.stats.update(stats)
        
        self.total_stat.value_label.setText(str(self.stats['total']))
        self.completed_stat.value_label.setText(str(self.stats['completed']))
        self.active_stat.value_label.setText(str(self.stats['active']))
        self.failed_stat.value_label.setText(str(self.stats['failed']))

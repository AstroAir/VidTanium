"""
Enhanced Fluent Design Progress Components with Responsive Design
Modern, smooth, and accessible progress indicators with responsive behavior and advanced theming
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Signal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient
from qfluentwidgets import (
    ProgressBar, ProgressRing, IndeterminateProgressRing, 
    CaptionLabel, BodyLabel, CardWidget, StrongBodyLabel
)
from typing import Optional, Dict, Any
from .responsive import ResponsiveWidget, ResponsiveManager
from .theme import VidTaniumTheme
from ..theme_manager import EnhancedThemeManager
from loguru import logger


class EnhancedFluentProgressBar(ProgressBar, ResponsiveWidget):
    """Enhanced responsive progress bar with advanced theming and animations"""

    finished = Signal()
    progress_changed = Signal(int, int)  # current, total

    def __init__(self, parent=None):
        ProgressBar.__init__(self, parent)
        ResponsiveWidget.__init__(self)
        
        self.responsive_manager = ResponsiveManager.instance()
        self._animation_enabled = True
        self._gradient_colors = None
        
        # Connect signals
        self.valueChanged.connect(self._on_value_changed)
        
        # Setup responsive sizing
        self._setup_responsive_sizing()
        
        # Apply enhanced styling
        self._apply_enhanced_styling()

    def _setup_responsive_sizing(self):
        """Setup responsive sizing based on breakpoint"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Responsive thickness based on screen size
        thickness_config = {
            'xs': 6,
            'sm': 8,
            'md': 10,
            'lg': 12,
            'xl': 14,
            'xxl': 16
        }
        
        thickness = thickness_config.get(current_bp.value, 10)
        self.setFixedHeight(thickness)

    def on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        self._setup_responsive_sizing()

    def _apply_enhanced_styling(self):
        """Apply enhanced theming and styling"""
        # Get theme colors if available
        theme_manager = getattr(self.parent(), 'theme_manager', None)
        if theme_manager and isinstance(theme_manager, EnhancedThemeManager):
            colors = theme_manager.get_theme_colors()
            accent_color = theme_manager.ACCENT_COLORS.get(
                theme_manager.get_current_accent(), '#0078D4'
            )
            
            # Set custom styling
            self.setStyleSheet(f"""
                ProgressBar {{
                    background-color: {colors.get('border', '#E5E7EB')};
                    border-radius: {self.height() // 2}px;
                }}
                ProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {accent_color}, stop:1 rgba(255, 255, 255, 0.8));
                    border-radius: {self.height() // 2}px;
                }}
            """)

    def setThickness(self, thickness: int):
        """Set progress bar thickness with responsive consideration"""
        self.setFixedHeight(thickness)
        self._apply_enhanced_styling()

    def setGradientColors(self, start_color: str, end_color: str):
        """Set custom gradient colors"""
        self._gradient_colors = (start_color, end_color)
        if self._gradient_colors:
            self.setStyleSheet(f"""
                ProgressBar {{
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: {self.height() // 2}px;
                }}
                ProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {start_color}, stop:1 {end_color});
                    border-radius: {self.height() // 2}px;
                }}
            """)

    def setAnimationEnabled(self, enabled: bool):
        """Enable or disable smooth animations"""
        self._animation_enabled = enabled

    def setValue(self, value: int):
        """Set value with optional animation"""
        if self._animation_enabled:
            # Create smooth transition animation
            self.value_animation = QPropertyAnimation(parent=self)
            self.value_animation.setTargetObject(self)
            self.value_animation.setPropertyName(b"value")
            self.value_animation.setDuration(300)
            self.value_animation.setStartValue(self.value())
            self.value_animation.setEndValue(value)
            self.value_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.value_animation.start()
        else:
            super().setValue(value)

    def _on_value_changed(self, value: int):
        """Handle value changes"""
        self.progress_changed.emit(value, self.maximum())
        if value >= self.maximum():
            self.finished.emit()


class EnhancedProgressCard(CardWidget, ResponsiveWidget):
    """Enhanced progress card with responsive design and comprehensive information display"""

    def __init__(self, title: str = "", parent=None):
        CardWidget.__init__(self, parent)
        ResponsiveWidget.__init__(self)
        
        self.title = title
        self.responsive_manager = ResponsiveManager.instance()
        
        # Progress tracking
        self._current_progress = 0
        self._total_progress = 100
        self._speed: float = 0.0
        self._eta: float = 0.0
        self._status = "Ready"
        
        # Components
        self.progress_bar: Optional[EnhancedFluentProgressBar] = None
        self.title_label: Optional[StrongBodyLabel] = None
        self.status_label: Optional[BodyLabel] = None
        self.details_label: Optional[CaptionLabel] = None
        
        self._setup_ui()
        self._apply_responsive_styling()

    def _setup_ui(self):
        """Setup the progress card UI"""
        layout = QVBoxLayout(self)
        
        # Responsive margins
        self._setup_responsive_margins(layout)
        layout.setSpacing(12)

        # Header section
        self._create_header(layout)
        
        # Progress section
        self._create_progress_section(layout)
        
        # Details section
        self._create_details_section(layout)

    def _setup_responsive_margins(self, layout: QVBoxLayout):
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
        layout.setContentsMargins(margin, margin//2, margin, margin//2)

    def _create_header(self, layout: QVBoxLayout):
        """Create header with title and status"""
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = StrongBodyLabel(self.title)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
                color: {VidTaniumTheme.TEXT_PRIMARY};
                margin: 0;
            }}
        """)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Status
        self.status_label = BodyLabel(self._status)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
                margin: 0;
            }}
        """)
        
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)

    def _create_progress_section(self, layout: QVBoxLayout):
        """Create progress bar section"""
        self.progress_bar = EnhancedFluentProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Apply accent color if theme manager is available
        theme_manager = getattr(self.parent(), 'theme_manager', None)
        if theme_manager:
            accent = theme_manager.get_current_accent() if hasattr(theme_manager, 'get_current_accent') else 'blue'
            if accent in ['blue', 'purple', 'green']:
                colors = {
                    'blue': ('#0078D4', '#40E0D0'),
                    'purple': ('#8B5CF6', '#D946EF'), 
                    'green': ('#10B981', '#34D399')
                }
                start, end = colors.get(accent, colors['blue'])
                self.progress_bar.setGradientColors(start, end)
        
        layout.addWidget(self.progress_bar)

    def _create_details_section(self, layout: QVBoxLayout):
        """Create details section with speed, ETA, etc."""
        self.details_label = CaptionLabel("")
        self.details_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_CAPTION};
                margin: 0;
            }}
        """)
        self.details_label.setWordWrap(True)
        
        layout.addWidget(self.details_label)

    def _apply_responsive_styling(self):
        """Apply responsive styling to the card"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Responsive card height
        if current_bp.value in ['xs', 'sm']:
            self.setMinimumHeight(100)
            self.setMaximumHeight(120)
        else:
            self.setMinimumHeight(120)
            self.setMaximumHeight(150)

    def on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        if hasattr(self, 'layout'):
            layout = self.layout()
            if layout and isinstance(layout, QVBoxLayout):
                self._setup_responsive_margins(layout)
        self._apply_responsive_styling()

    def setTitle(self, title: str):
        """Set card title"""
        self.title = title
        if self.title_label:
            self.title_label.setText(title)

    def setProgress(self, current: int, total: int = 100, speed: float = 0, eta: float = 0):
        """Set progress information"""
        self._current_progress = current
        self._total_progress = total
        self._speed = speed
        self._eta = eta
        
        # Update progress bar
        if self.progress_bar:
            if total > 0:
                percentage = int((current / total) * 100)
                self.progress_bar.setValue(percentage)
        
        # Update details
        self._update_details()

    def setStatus(self, status: str):
        """Set status text"""
        self._status = status
        if self.status_label:
            self.status_label.setText(status)

    def _update_details(self):
        """Update details text"""
        if not self.details_label:
            return
            
        details_parts = []
        
        # Progress
        if self._total_progress > 0:
            percentage = (self._current_progress / self._total_progress) * 100
            details_parts.append(f"{self._current_progress}/{self._total_progress} ({percentage:.1f}%)")
        
        # Speed
        if self._speed > 0:
            speed_text = self._format_speed(self._speed)
            details_parts.append(f"Speed: {speed_text}")
        
        # ETA
        if self._eta > 0:
            eta_text = self._format_time(self._eta)
            details_parts.append(f"ETA: {eta_text}")
        
        self.details_label.setText(" • ".join(details_parts))

    def _format_speed(self, bytes_per_sec: float) -> str:
        """Format speed in human-readable format"""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.0f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec/1024:.1f} KB/s"
        elif bytes_per_sec < 1024 * 1024 * 1024:
            return f"{bytes_per_sec/(1024*1024):.1f} MB/s"
        else:
            return f"{bytes_per_sec/(1024*1024*1024):.1f} GB/s"

    def _format_time(self, seconds: float) -> str:
        """Format time in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m {seconds%60:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


class CompactProgressBar(EnhancedFluentProgressBar):
    """Compact progress bar for lists and small spaces"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self.setMinimumWidth(100)


# Factory functions for common use cases
def create_download_progress_card(title: str = "Download") -> EnhancedProgressCard:
    """Create a pre-configured progress card for downloads"""
    card = EnhancedProgressCard(title)
    card.setStatus("Preparing...")
    if card.progress_bar and hasattr(card.progress_bar, 'setGradientColors'):
        card.progress_bar.setGradientColors('#0078D4', '#40E0D0')
    return card


def create_processing_progress_card(title: str = "Processing") -> EnhancedProgressCard:
    """Create a pre-configured progress card for processing tasks"""
    card = EnhancedProgressCard(title)
    card.setStatus("Processing...")
    if card.progress_bar and hasattr(card.progress_bar, 'setGradientColors'):
        card.progress_bar.setGradientColors('#8B5CF6', '#D946EF')
    return card


def create_upload_progress_card(title: str = "Upload") -> EnhancedProgressCard:
    """Create a pre-configured progress card for uploads"""
    card = EnhancedProgressCard(title)
    card.setStatus("Uploading...")
    if card.progress_bar and hasattr(card.progress_bar, 'setGradientColors'):
        card.progress_bar.setGradientColors('#10B981', '#34D399')
    return card


# Backward compatibility aliases
FluentProgressBar = EnhancedFluentProgressBar
ProgressCardWidget = EnhancedProgressCard
"""
Fluent Design Progress Bar Components using qfluentwidgets
Modern, smooth, and accessible progress indicators built on top of qfluentwidgets library

This module provides enhanced wrappers around qfluentwidgets ProgressBar, ProgressRing, 
and IndeterminateProgressRing components with additional functionality and convenience methods.

Key Components:
- FluentProgressBar: Enhanced wrapper around qfluentwidgets.ProgressBar
- FluentProgressRing: Enhanced wrapper around qfluentwidgets.ProgressRing  
- FluentIndeterminateProgressRing: Enhanced wrapper around qfluentwidgets.IndeterminateProgressRing
- ProgressCardWidget: Complete progress card with labels and status information
- CompactProgressBar: Compact progress bar for lists and small spaces
- ProgressStatusWidget: Simple status widget with progress ring and text
- MinimalProgressBar: Ultra-minimal progress bar for embedded use

Factory Functions:
- create_download_progress_card(): Pre-configured card for downloads
- create_processing_progress_card(): Pre-configured card for processing
- create_upload_progress_card(): Pre-configured card for uploads
- create_compact_progress(): Create compact progress bar
- create_status_indicator(): Create status indicator widget

Usage Examples:
    # Basic Progress Bar
    progress_bar = FluentProgressBar()
    progress_bar.setRange(0, 100)
    progress_bar.setValue(50)
    progress_bar.setThickness(8)
    
    # Progress Card with all features
    card = create_download_progress_card("Download Video")
    card.setProgress(current=50, total=100, speed=2048000, eta=25.5)
    card.setStatus("Downloading...")
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from qfluentwidgets import ProgressBar, ProgressRing, IndeterminateProgressRing, CaptionLabel, BodyLabel
from typing import Optional


class FluentProgressBar(ProgressBar):
    """
    Enhanced wrapper around qfluentwidgets ProgressBar with additional functionality
    """
    
    # Signals for compatibility
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Connect to existing valueChanged signal to emit finished when complete
        self.valueChanged.connect(self._on_value_changed)
        
        # Set default styling
        self.setFixedHeight(8)
        
    def setThickness(self, thickness: int):
        """Set progress bar thickness"""
        self.setFixedHeight(thickness)
    
    def setAnimationEnabled(self, enabled: bool):
        """Enable or disable smooth animations (compatibility method)"""
        # qfluentwidgets ProgressBar has built-in animations
        pass
    
    def setColors(self, background: QColor, fill: QColor):
        """Set custom colors"""
        self.setCustomBarColor(fill, background)
    
    def _on_value_changed(self, value: int):
        """Handle value change to emit finished signal"""
        if value >= self.maximum():
            self.finished.emit()


class FluentProgressRing(ProgressRing):
    """
    Enhanced wrapper around qfluentwidgets ProgressRing with additional functionality
    """
    
    # Signals for compatibility
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Connect to existing valueChanged signal to emit finished when complete
        self.valueChanged.connect(self._on_value_changed)
        
        # Set default size and styling
        self.setFixedSize(32, 32)
        self.setStrokeWidth(4)
    
    def setSize(self, size: int):
        """Set ring size"""
        self.setFixedSize(size, size)
    
    def setThickness(self, thickness: int):
        """Set ring thickness"""
        self.setStrokeWidth(thickness)
    
    def _on_value_changed(self, value: int):
        """Handle value change to emit finished signal"""
        if value >= self.maximum():
            self.finished.emit()


class FluentIndeterminateProgressRing(IndeterminateProgressRing):
    """
    Enhanced wrapper around qfluentwidgets IndeterminateProgressRing
    """
    
    def __init__(self, parent=None, start=True):
        super().__init__(parent)
        
        # Set default size and styling
        self.setFixedSize(50, 50)
        self.setStrokeWidth(4)
        
        if start:
            self.start()
    
    def setSize(self, size: int):
        """Set ring size"""
        self.setFixedSize(size, size)
    
    def setThickness(self, thickness: int):
        """Set ring thickness"""
        self.setStrokeWidth(thickness)
    
    def start(self):
        """Start the indeterminate animation"""
        # The qfluentwidgets IndeterminateProgressRing starts automatically
        pass
    
    def stop(self):
        """Stop the indeterminate animation"""
        self.hide()
    
    def setCustomColor(self, color: QColor):
        """Set custom color for the ring"""
        # Note: qfluentwidgets may not support this directly
        pass


class ProgressCardWidget(QWidget):
    """
    Complete progress card with bar, labels, and status information
    Follows Fluent Design principles for layout and typography
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._setup_styling()
        
        # Progress tracking
        self._current = 0
        self._total = 0
        self._speed = 0.0
        self._eta = None
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Title and percentage row
        header_layout = QHBoxLayout()
        
        self.title_label = BodyLabel("Progress")
        self.title_label.setStyleSheet("font-weight: 600; color: #323130;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.percentage_label = CaptionLabel("0%")
        self.percentage_label.setStyleSheet("font-weight: 600; color: #0078d4;")
        header_layout.addWidget(self.percentage_label)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = FluentProgressBar()
        self.progress_bar.setThickness(8)
        layout.addWidget(self.progress_bar)
        
        # Status information row
        status_layout = QHBoxLayout()
        
        self.status_label = CaptionLabel("Ready")
        self.status_label.setStyleSheet("color: #605e5c;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.speed_label = CaptionLabel("")
        self.speed_label.setStyleSheet("color: #107c10;")  # Fluent green
        status_layout.addWidget(self.speed_label)
        
        self.eta_label = CaptionLabel("")
        self.eta_label.setStyleSheet("color: #d83b01;")  # Fluent orange
        status_layout.addWidget(self.eta_label)
        
        layout.addLayout(status_layout)
        
        # Connect signals
        self.progress_bar.valueChanged.connect(self._on_progress_changed)
        self.progress_bar.finished.connect(self._on_finished)
    
    def _setup_styling(self):
        """Apply Fluent Design styling"""
        self.setStyleSheet("""
            ProgressCardWidget {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 8px;
            }
            ProgressCardWidget:hover {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(0, 120, 212, 0.2);
            }
        """)
    
    def setTitle(self, title: str):
        """Set progress title"""
        self.title_label.setText(title)
    
    def setProgress(self, current: int, total: int, speed: float = 0.0, eta: Optional[float] = None):
        """Update progress with all metrics"""
        self._current = current
        self._total = total
        self._speed = speed
        self._eta = eta
        
        # Update progress bar
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.percentage_label.setText(f"{percentage}%")
        else:
            self.percentage_label.setText("0%")
        
        # Update speed
        if speed > 0:
            self.speed_label.setText(self._format_speed(speed))
            self.speed_label.setVisible(True)
        else:
            self.speed_label.setVisible(False)
        
        # Update ETA
        if eta is not None and eta > 0:
            self.eta_label.setText(self._format_eta(eta))
            self.eta_label.setVisible(True)
        else:
            self.eta_label.setVisible(False)
    
    def setStatus(self, status: str):
        """Set status text"""
        self.status_label.setText(status)
    
    def _format_speed(self, speed: float) -> str:
        """Format speed for display"""
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed / 1024:.1f} KB/s"
        elif speed < 1024 * 1024 * 1024:
            return f"{speed / (1024 * 1024):.1f} MB/s"
        else:
            return f"{speed / (1024 * 1024 * 1024):.1f} GB/s"
    
    def _format_eta(self, eta: float) -> str:
        """Format ETA for display"""
        if eta < 60:
            return f"{int(eta)}s"
        elif eta < 3600:
            minutes = int(eta // 60)
            seconds = int(eta % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(eta // 3600)
            minutes = int((eta % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _on_progress_changed(self, value: int):
        """Handle progress change"""
        if self._total > 0:
            percentage = int((value / self._total) * 100)
            self.percentage_label.setText(f"{percentage}%")
    
    def _on_finished(self):
        """Handle progress completion"""
        self.setStatus("Completed")
        self.percentage_label.setText("100%")
        self.speed_label.setVisible(False)
        self.eta_label.setVisible(False)


class CompactProgressBar(QWidget):
    """
    Compact progress bar for use in lists and small spaces
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self.setFixedHeight(24)
    
    def _setup_ui(self):
        """Setup compact UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Progress bar
        self.progress_bar = FluentProgressBar()
        self.progress_bar.setThickness(4)
        layout.addWidget(self.progress_bar, 1)
        
        # Percentage
        self.percentage_label = CaptionLabel("0%")
        self.percentage_label.setStyleSheet("font-weight: 600; color: #605e5c; min-width: 30px;")
        layout.addWidget(self.percentage_label)
        
        # Connect signals
        self.progress_bar.valueChanged.connect(self._on_progress_changed)
    
    def setProgress(self, current: int, total: int):
        """Set progress"""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            percentage = int((current / total) * 100)
            self.percentage_label.setText(f"{percentage}%")
        else:
            self.percentage_label.setText("0%")
    
    def _on_progress_changed(self, value: int):
        """Handle progress change"""
        total = self.progress_bar.maximum()
        if total > 0:
            percentage = int((value / total) * 100)
            self.percentage_label.setText(f"{percentage}%")


class ProgressStatusWidget(QWidget):
    """
    Simple status widget with progress ring and text
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Progress ring
        self.progress_ring = FluentProgressRing()
        self.progress_ring.setSize(24)
        self.progress_ring.setThickness(3)
        layout.addWidget(self.progress_ring)
        
        # Status text
        self.status_label = BodyLabel("Ready")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def setProgress(self, current: int, total: int):
        """Set progress"""
        if total > 0:
            self.progress_ring.setRange(0, total)
            self.progress_ring.setValue(current)
            percentage = int((current / total) * 100)
            self.status_label.setText(f"Progress: {percentage}%")
    
    def setStatus(self, status: str):
        """Set status text"""
        self.status_label.setText(status)
    
    def setIndeterminate(self, indeterminate: bool = True):
        """Switch between determinate and indeterminate mode"""
        if indeterminate:
            # Hide the progress ring and show indeterminate spinner
            self.progress_ring.hide()
            if not hasattr(self, 'spinner'):
                self.spinner = FluentIndeterminateProgressRing(self, start=True)
                self.spinner.setSize(24)
                self.spinner.setThickness(3)
                # Insert at the beginning of the layout
                layout = self.layout()
                if isinstance(layout, QHBoxLayout):
                    layout.insertWidget(0, self.spinner)
            self.spinner.show()
        else:
            # Show the progress ring and hide spinner
            self.progress_ring.show()
            if hasattr(self, 'spinner'):
                self.spinner.hide()


class MinimalProgressBar(ProgressBar):
    """
    Minimal progress bar for embedded use
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set minimal height
        self.setFixedHeight(2)
        
        # Hide text
        self.setTextVisible(False)
    
    def setProgress(self, current: int, total: int):
        """Set progress"""
        if total > 0:
            self.setRange(0, total)
            self.setValue(current)


# Factory functions for common use cases
def create_download_progress_card(title: str = "Download", parent=None) -> ProgressCardWidget:
    """Create a progress card configured for download operations"""
    card = ProgressCardWidget(parent)
    card.setTitle(title)
    card.setStatus("Preparing...")
    # Set blue color scheme for downloads
    card.progress_bar.setCustomBarColor(QColor(0, 120, 212), QColor(243, 242, 241))
    return card


def create_processing_progress_card(title: str = "Processing", parent=None) -> ProgressCardWidget:
    """Create a progress card configured for processing operations"""
    card = ProgressCardWidget(parent)
    card.setTitle(title)
    card.setStatus("Processing...")
    # Set orange color scheme for processing
    card.progress_bar.setCustomBarColor(QColor(255, 140, 0), QColor(243, 242, 241))
    return card


def create_upload_progress_card(title: str = "Upload", parent=None) -> ProgressCardWidget:
    """Create a progress card configured for upload operations"""
    card = ProgressCardWidget(parent)
    card.setTitle(title)
    card.setStatus("Uploading...")
    # Set green color scheme for uploads
    card.progress_bar.setCustomBarColor(QColor(16, 124, 16), QColor(243, 242, 241))
    return card


def create_compact_progress(parent=None) -> CompactProgressBar:
    """Create a compact progress bar for lists"""
    return CompactProgressBar(parent)


def create_status_indicator(parent=None) -> ProgressStatusWidget:
    """Create a status indicator with progress ring"""
    return ProgressStatusWidget(parent)

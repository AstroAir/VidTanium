"""
Responsive layout utilities for VidTanium GUI
Provides adaptive layouts, breakpoints, and responsive behavior
"""

from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
from PySide6.QtWidgets import (
    QWidget, QLayout, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QSpacerItem, QApplication
)
from PySide6.QtCore import QSize, QRect, Qt, QObject, Signal, QTimer
from PySide6.QtGui import QResizeEvent
from loguru import logger


class BreakPoint(Enum):
    """Responsive breakpoints"""
    EXTRA_SMALL = "xs"  # < 576px
    SMALL = "sm"        # >= 576px
    MEDIUM = "md"       # >= 768px
    LARGE = "lg"        # >= 992px
    EXTRA_LARGE = "xl"  # >= 1200px
    EXTRA_EXTRA_LARGE = "xxl"  # >= 1400px


class ResponsiveManager(QObject):
    """Global responsive layout manager"""
    
    # Signals
    breakpoint_changed = Signal(str)  # breakpoint name
    orientation_changed = Signal(Qt.Orientation)
    
    _instance: Optional['ResponsiveManager'] = None
    _initialized: bool
    
    # Breakpoint thresholds
    BREAKPOINTS = {
        BreakPoint.EXTRA_SMALL: 0,
        BreakPoint.SMALL: 576,
        BreakPoint.MEDIUM: 768,
        BreakPoint.LARGE: 992,
        BreakPoint.EXTRA_LARGE: 1200,
        BreakPoint.EXTRA_EXTRA_LARGE: 1400,
    }
    
    def __new__(cls) -> None:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if hasattr(self, '_initialized') and self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        self._current_breakpoint: BreakPoint = BreakPoint.MEDIUM
        self._current_orientation: Qt.Orientation = Qt.Orientation.Horizontal
        self._registered_widgets: List[QWidget] = []
        self._callbacks: Dict[str, List[Callable]] = {
            'breakpoint': [],
            'orientation': []
        }
        
        # Timer for debouncing resize events
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._handle_delayed_resize)
        
        logger.debug("ResponsiveManager initialized")
    
    @classmethod
    def instance(cls) -> 'ResponsiveManager':
        """Get singleton instance"""
        return cls()
    
    def register_widget(self, widget: QWidget) -> None:
        """Register a widget for responsive updates"""
        if widget not in self._registered_widgets:
            self._registered_widgets.append(widget)
            widget.installEventFilter(self)
            logger.debug(f"Registered widget for responsive updates: {widget.__class__.__name__}")
    
    def unregister_widget(self, widget: QWidget) -> None:
        """Unregister a widget from responsive updates"""
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)
            widget.removeEventFilter(self)
            logger.debug(f"Unregistered widget from responsive updates: {widget.__class__.__name__}")
    
    def add_breakpoint_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for breakpoint changes"""
        self._callbacks['breakpoint'].append(callback)
    
    def add_orientation_callback(self, callback: Callable[[Qt.Orientation], None]) -> None:
        """Add callback for orientation changes"""
        self._callbacks['orientation'].append(callback)
    
    def get_current_breakpoint(self) -> BreakPoint:
        """Get current breakpoint"""
        return self._current_breakpoint
    
    def get_current_orientation(self) -> Qt.Orientation:
        """Get current orientation"""
        return self._current_orientation
    
    def update_for_size(self, size: QSize) -> None:
        """Update responsive state for given size with error handling"""
        try:
            if not size or not size.isValid():
                return
                
            width, height = size.width(), size.height()
            
            # Validate dimensions
            if width <= 0 or height <= 0:
                return
            
            # Determine breakpoint
            new_breakpoint = self._get_breakpoint_for_width(width)
            if new_breakpoint != self._current_breakpoint:
                old_breakpoint = self._current_breakpoint
                self._current_breakpoint = new_breakpoint
                logger.debug(f"Breakpoint changed: {old_breakpoint.value} -> {new_breakpoint.value} (width: {width}px)")
                
                # Debounce the breakpoint change to avoid rapid updates
                self._resize_timer.stop()
                self._resize_timer.setInterval(150)  # 150ms debounce
                self._resize_timer.start()
            
            # Determine orientation
            new_orientation = Qt.Orientation.Horizontal if width > height else Qt.Orientation.Vertical
            if new_orientation != self._current_orientation:
                old_orientation = self._current_orientation
                self._current_orientation = new_orientation
                logger.debug(f"Orientation changed: {old_orientation} -> {new_orientation}")
                self.orientation_changed.emit(new_orientation)
                self._notify_orientation_callbacks(new_orientation)
                
        except Exception as e:
            logger.error(f"Error updating responsive state: {e}")
    
    def _get_breakpoint_for_width(self, width: int) -> BreakPoint:
        """Get breakpoint for given width"""
        for breakpoint in reversed(list(BreakPoint)):
            if width >= self.BREAKPOINTS[breakpoint]:
                return breakpoint
        return BreakPoint.EXTRA_SMALL
    
    def _handle_delayed_resize(self) -> None:
        """Handle delayed resize event - emit the actual breakpoint change"""
        try:
            # Emit the breakpoint change that was debounced
            if self._current_breakpoint:
                self.breakpoint_changed.emit(self._current_breakpoint.value)
                self._notify_breakpoint_callbacks(self._current_breakpoint.value)
        except Exception as e:
            logger.error(f"Error in delayed resize handler: {e}")
    
    def _notify_breakpoint_callbacks(self, breakpoint: str) -> None:
        """Notify breakpoint change callbacks"""
        for callback in self._callbacks['breakpoint']:
            try:
                callback(breakpoint)
            except Exception as e:
                logger.error(f"Error in breakpoint callback: {e}")
    
    def _notify_orientation_callbacks(self, orientation: Qt.Orientation) -> None:
        """Notify orientation change callbacks"""
        for callback in self._callbacks['orientation']:
            try:
                callback(orientation)
            except Exception as e:
                logger.error(f"Error in orientation callback: {e}")


class ResponsiveWidget(QWidget):
    """Base widget with responsive capabilities"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._responsive_manager = ResponsiveManager.instance()
        self._responsive_manager.register_widget(self)
        self._responsive_manager.breakpoint_changed.connect(self._on_breakpoint_changed)
        self._responsive_manager.orientation_changed.connect(self._on_orientation_changed)
        
    def __del__(self) -> None:
        if hasattr(self, '_responsive_manager'):
            self._responsive_manager.unregister_widget(self)
    
    def _on_breakpoint_changed(self, breakpoint: str) -> None:
        """Handle breakpoint change"""
        self.on_breakpoint_changed(breakpoint)
    
    def _on_orientation_changed(self, orientation: Qt.Orientation) -> None:
        """Handle orientation change"""
        self.on_orientation_changed(orientation)
    
    def on_breakpoint_changed(self, breakpoint: str) -> None:
        """Override to handle breakpoint changes"""
        pass
    
    def on_orientation_changed(self, orientation: Qt.Orientation) -> None:
        """Override to handle orientation changes"""
        pass
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize events"""
        super().resizeEvent(event)
        self._responsive_manager.update_for_size(event.size())


class ResponsiveLayout:
    """Utility class for creating responsive layouts"""
    
    @staticmethod
    def create_adaptive_grid(
        widgets: List[QWidget],
        breakpoint_configs: Dict[str, Dict[str, int]],
        parent: Optional[QWidget] = None
    ) -> QGridLayout:
        """
        Create adaptive grid layout
        
        Args:
            widgets: List of widgets to arrange
            breakpoint_configs: Config for each breakpoint
                Example: {
                    'xs': {'columns': 1, 'spacing': 8},
                    'sm': {'columns': 2, 'spacing': 12},
                    'md': {'columns': 3, 'spacing': 16},
                }
            parent: Parent widget
        """
        layout = QGridLayout(parent)
        
        def update_layout(breakpoint: str) -> None:
            config = breakpoint_configs.get(breakpoint, breakpoint_configs.get('md', {}))
            columns = config.get('columns', 3)
            spacing = config.get('spacing', 16)
            
            # Clear existing layout
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            
            # Re-add widgets in new configuration
            layout.setSpacing(spacing)
            for i, widget in enumerate(widgets):
                row = i // columns
                col = i % columns
                layout.addWidget(widget, row, col)
        
        # Register for breakpoint changes
        ResponsiveManager.instance().add_breakpoint_callback(update_layout)
        
        # Initial setup
        current_bp = ResponsiveManager.instance().get_current_breakpoint()
        update_layout(current_bp.value)
        
        return layout
    
    @staticmethod
    def create_adaptive_flow(
        widgets: List[QWidget],
        breakpoint_configs: Dict[str, str],
        parent: Optional[QWidget] = None
    ) -> QLayout:
        """
        Create adaptive flow layout (horizontal/vertical based on breakpoint)
        
        Args:
            widgets: List of widgets to arrange
            breakpoint_configs: Layout direction for each breakpoint
                Example: {
                    'xs': 'vertical',
                    'sm': 'vertical', 
                    'md': 'horizontal',
                    'lg': 'horizontal'
                }
            parent: Parent widget
        """
        container = QWidget(parent)
        current_layout: Optional[QLayout] = None

        def update_layout(breakpoint: str) -> None:
            nonlocal current_layout

            direction = breakpoint_configs.get(breakpoint, 'horizontal')

            # Remove old layout
            if current_layout:
                while current_layout.count():
                    item = current_layout.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                # Clear the layout by setting a temporary empty layout
                temp_layout = QVBoxLayout()
                container.setLayout(temp_layout)
                current_layout.deleteLater()

            # Create new layout
            if direction == 'vertical':
                current_layout = QVBoxLayout(container)
            else:
                current_layout = QHBoxLayout(container)

            # Add widgets
            for widget in widgets:
                if current_layout:
                    current_layout.addWidget(widget)

            if current_layout:
                container.setLayout(current_layout)
        
        # Register for breakpoint changes
        ResponsiveManager.instance().add_breakpoint_callback(update_layout)
        
        # Initial setup
        current_bp = ResponsiveManager.instance().get_current_breakpoint()
        update_layout(current_bp.value)
        
        layout = container.layout()
        if layout is None:
            # Fallback to creating a basic layout if none exists
            layout = QVBoxLayout(container)
            container.setLayout(layout)
        return layout
    
    @staticmethod
    def apply_responsive_spacing(
        layout: QLayout,
        spacing_config: Dict[str, int]
    ) -> None:
        """
        Apply responsive spacing to layout
        
        Args:
            layout: Layout to apply spacing to
            spacing_config: Spacing for each breakpoint
        """
        def update_spacing(breakpoint: str) -> None:
            spacing = spacing_config.get(breakpoint, spacing_config.get('md', 16))
            layout.setSpacing(spacing)
        
        ResponsiveManager.instance().add_breakpoint_callback(update_spacing)
        
        # Initial setup
        current_bp = ResponsiveManager.instance().get_current_breakpoint()
        update_spacing(current_bp.value)


class ResponsiveContainer(ResponsiveWidget):
    """Container widget with responsive behavior"""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._content_margins = {
            'xs': (8, 8, 8, 8),
            'sm': (12, 12, 12, 12),
            'md': (16, 16, 16, 16),
            'lg': (24, 24, 24, 24),
            'xl': (32, 32, 32, 32),
            'xxl': (40, 40, 40, 40),
        }
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup responsive container UI"""
        self.setObjectName("ResponsiveContainer")
        self._update_margins()
    
    def on_breakpoint_changed(self, breakpoint: str) -> None:
        """Update margins based on breakpoint"""
        self._update_margins()
    
    def _update_margins(self) -> None:
        """Update content margins based on current breakpoint"""
        current_bp = self._responsive_manager.get_current_breakpoint()
        margins = self._content_margins.get(current_bp.value, self._content_margins['md'])
        self.setContentsMargins(*margins)
    
    def set_margins_config(self, margins_config: Dict[str, Tuple[int, int, int, int]]) -> None:
        """Set custom margins configuration"""
        self._content_margins = margins_config
        self._update_margins()


def make_responsive(widget: QWidget) -> QWidget:
    """Make any widget responsive by wrapping it"""
    container = ResponsiveContainer()
    layout = QVBoxLayout(container)
    layout.addWidget(widget)
    return container


def get_responsive_size_policy(breakpoint: str) -> QSizePolicy:
    """Get size policy based on breakpoint"""
    if breakpoint in ['xs', 'sm']:
        return QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    else:
        return QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
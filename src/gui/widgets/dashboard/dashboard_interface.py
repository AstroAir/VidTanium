"""
Enhanced Dashboard interface with responsive design and modern aesthetics
"""
from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import QTimer, QObject, Qt
from qfluentwidgets import (
    SmoothScrollArea
)

from ...utils.unified_design_system import UnifiedDesignSystem as DS
from ...utils.responsive import ResponsiveWidget, ResponsiveManager, ResponsiveLayout
from .hero_section import DashboardHeroSection
from .stats_section import DashboardStatsSection
from .task_preview import DashboardTaskPreview
from .system_status import DashboardSystemStatus
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class DashboardInterface(ResponsiveWidget):
    """Dashboard interface with responsive design and modern theming integration
    
    Features:
    - Comprehensive theme integration with EnhancedThemeManager
    - Responsive design that adapts to different screen sizes
    - Modern animations and smooth transitions
    - Performance-optimized updates and rendering
    - Enhanced component integration
    """

    def __init__(self, main_window: "MainWindow", theme_manager=None) -> None:
        super().__init__()
        self.main_window = main_window
        self.theme_manager = theme_manager
        self.responsive_manager = ResponsiveManager.instance()

        # Component instances
        self.hero_section: Optional[DashboardHeroSection] = None
        self.stats_section: Optional[DashboardStatsSection] = None
        self.task_preview: Optional[DashboardTaskPreview] = None
        self.system_status: Optional[DashboardSystemStatus] = None
        
        # Layout containers
        self.main_container: Optional[QWidget] = None
        self.content_layout: Optional[QHBoxLayout] = None
        self._layout_mode = 'horizontal'

        # Animation timer for dynamic effects
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(2000)  # Update every 2 seconds

    def create_interface(self) -> QWidget:
        """Create the enhanced dashboard interface with responsive design"""
        interface = SmoothScrollArea()
        interface.setWidgetResizable(True)
        interface.setObjectName("dashboard_scroll_area")
        
        # Apply enhanced styling
        self._apply_interface_styling(interface)

        # Main container with responsive layout
        self.main_container = QWidget()
        main_layout = QVBoxLayout(self.main_container)
        
        # Responsive margins based on breakpoint
        self._setup_responsive_margins(main_layout)
        main_layout.setSpacing(20)

        # Create component instances with enhanced theming
        self.hero_section = DashboardHeroSection(self.main_window, self.theme_manager)
        main_layout.addWidget(self.hero_section)

        # Statistics dashboard with enhanced theming
        self.stats_section = DashboardStatsSection(self.main_window, self.theme_manager)
        main_layout.addWidget(self.stats_section)

        # Content cards section with adaptive layout
        self._setup_content_section(main_layout)

        # Add stretch at the bottom to push content up
        main_layout.addStretch()

        interface.setWidget(self.main_container)
        
        # Register for responsive updates
        self.responsive_manager.register_widget(interface)
        
        return interface

    def _apply_interface_styling(self, interface: SmoothScrollArea) -> None:
        """Apply enhanced styling to the interface"""
        # Get current theme colors
        # Let qfluentwidgets and UnifiedDesignSystem handle theming

        interface.setStyleSheet(f"""
            SmoothScrollArea {{
                background-color: {DS.color('surface')};
                border: none;
            }}
            SmoothScrollArea QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }}
            SmoothScrollArea QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }}
            SmoothScrollArea QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.5);
            }}
        """)

    def _setup_responsive_margins(self, layout: QVBoxLayout) -> None:
        """Setup responsive margins based on current breakpoint"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        margin_config = {
            'xs': 12,
            'sm': 16,
            'md': 20,
            'lg': 24,
            'xl': 32,
            'xxl': 40
        }
        
        margin = margin_config.get(current_bp.value, 20)
        layout.setContentsMargins(margin, margin, margin, margin)

    def _setup_content_section(self, main_layout: QVBoxLayout) -> None:
        """Setup the content section with adaptive layout and enhanced theming"""
        # Create task preview and system status cards with enhanced theming
        self.task_preview = DashboardTaskPreview(self.main_window)
        self.system_status = DashboardSystemStatus(self.main_window, self.theme_manager)

        # Create adaptive layout configuration
        breakpoint_configs = {
            'xs': 'vertical',
            'sm': 'vertical', 
            'md': 'horizontal',
            'lg': 'horizontal',
            'xl': 'horizontal',
            'xxl': 'horizontal'
        }

        # Create responsive flow layout
        content_widgets = [self.task_preview, self.system_status]
        responsive_layout = ResponsiveLayout.create_adaptive_flow(
            content_widgets, 
            breakpoint_configs,
            self.main_container
        )
        
        main_layout.addLayout(responsive_layout)

    def set_layout_mode(self, mode: str) -> None:
        """Set layout mode for responsive adaptation"""
        if mode != self._layout_mode:
            self._layout_mode = mode
            logger.debug(f"Dashboard layout mode changed to: {mode}")
            self._adapt_layout_for_mode(mode)

    def _adapt_layout_for_mode(self, mode: str) -> None:
        """Adapt layout based on the specified mode"""
        if not self.content_layout or not self.task_preview or not self.system_status:
            return

        # Clear existing layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if mode == 'vertical':
            # Stack components vertically on small screens
            self.content_layout.setDirection(QHBoxLayout.Direction.TopToBottom)
            self.content_layout.addWidget(self.task_preview)
            self.content_layout.addWidget(self.system_status)
        else:
            # Use horizontal layout on larger screens
            self.content_layout.setDirection(QHBoxLayout.Direction.LeftToRight)
            self.content_layout.addWidget(self.task_preview, 2)  # Takes 2/3 of space
            self.content_layout.addWidget(self.system_status, 1)  # Takes 1/3 of space

    def on_breakpoint_changed(self, breakpoint: str) -> None:
        """Handle responsive breakpoint changes"""
        logger.debug(f"Dashboard adapting to breakpoint: {breakpoint}")
        
        # Update margins
        if self.main_container:
            layout = self.main_container.layout()
            if layout and isinstance(layout, QVBoxLayout):
                self._setup_responsive_margins(layout)
        
        # Update layout mode
        if breakpoint in ['xs', 'sm']:
            self.set_layout_mode('vertical')
        else:
            self.set_layout_mode('horizontal')

    def _update_animations(self) -> None:
        """Update dashboard animations and data with performance optimization"""
        try:
            # Check if window is visible to avoid unnecessary updates
            if not self.main_window.isVisible():
                return

            # Update components periodically
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

    def update_task_preview(self) -> None:
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

    def update_theme(self, theme_manager=None) -> None:
        """Update theme for all dashboard components"""
        if theme_manager:
            self.theme_manager = theme_manager
            
        # Update theme for all components
        if self.hero_section and hasattr(self.hero_section, 'update_theme'):
            self.hero_section.update_theme(self.theme_manager)
            
        if self.stats_section and hasattr(self.stats_section, 'update_theme'):
            self.stats_section.update_theme(self.theme_manager)
            
        if self.system_status and hasattr(self.system_status, 'update_theme'):
            self.system_status.update_theme(self.theme_manager)
            
        # Update interface styling
        if hasattr(self, 'main_container') and self.main_container:
            parent_widget = self.main_container.parent()
            if parent_widget:
                self._apply_interface_styling(parent_widget)

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.animation_timer:
                self.animation_timer.stop()
            if hasattr(self, 'responsive_manager'):
                self.responsive_manager.unregister_widget(self)
        except Exception as e:
            logger.error(f"Error cleaning up dashboard: {e}")

    # Compatibility methods for backward compatibility
    def update_stats(self) -> None:
        """Update statistics - compatibility method"""
        self.update_statistics()

    def update_task_preview_original(self) -> None:
        """Legacy method - kept for compatibility"""
        self.update_task_preview()

    def _format_speed(self, speed_bytes_per_sec: float) -> str:
        """Format speed in human-readable format - compatibility method"""
        from ...utils.formatters import format_speed
        return format_speed(speed_bytes_per_sec)


# Backward compatibility alias
EnhancedDashboardInterface = DashboardInterface

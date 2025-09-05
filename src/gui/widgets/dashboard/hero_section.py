"""
Enhanced Dashboard Hero Section Component with responsive design and modern theming
"""
from typing import TYPE_CHECKING, Optional, Union
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLayout
from PySide6.QtCore import Qt, QTimer, Slot
from qfluentwidgets import (
    TitleLabel, BodyLabel, SubtitleLabel, PrimaryPushButton,
    FluentIcon as FIF, IconWidget, ElevatedCardWidget, HeaderCardWidget,
    VBoxLayout, HyperlinkCard, SimpleCardWidget, setTheme, Theme, isDarkTheme
)

from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme
from ...utils.responsive import ResponsiveWidget, ResponsiveManager
from ...theme_manager import EnhancedThemeManager
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class EnhancedDashboardHeroSection(ResponsiveWidget):
    """Enhanced hero section component with responsive design and modern theming
    
    Features:
    - Responsive design that adapts to different screen sizes
    - Enhanced theming integration with EnhancedThemeManager
    - Modern gradient backgrounds and animated effects
    - Adaptive button layouts and typography
    - Performance optimizations and smooth interactions
    """

    def __init__(self, main_window: "MainWindow", theme_manager=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.theme_manager = theme_manager
        self.responsive_manager = ResponsiveManager.instance()
        self.new_task_btn: Optional[PrimaryPushButton] = None
        self.batch_btn: Optional[PrimaryPushButton] = None
        
        self._setup_enhanced_ui()
        self._connect_signals()
        self._apply_enhanced_theming()

    def _setup_enhanced_ui(self):
        """Setup enhanced responsive hero section UI"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Enhanced hero card with responsive sizing
        self.hero_card = ElevatedCardWidget()
        
        if current_bp.value in ['xs', 'sm']:
            self.hero_card.setMinimumHeight(140)
            self.hero_card.setMaximumHeight(200)
        elif current_bp.value == 'md':
            self.hero_card.setMinimumHeight(160)
            self.hero_card.setMaximumHeight(220)
        else:
            self.hero_card.setMinimumHeight(180)
            self.hero_card.setMaximumHeight(240)

        # Set responsive size policy
        from PySide6.QtWidgets import QSizePolicy
        self.hero_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Responsive layout based on screen size
        # Create layout based on screen size
        layout: Union[QVBoxLayout, QHBoxLayout]
        if current_bp.value in ['xs', 'sm']:
            # Vertical layout for small screens
            layout = QVBoxLayout(self.hero_card)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(16)

            # Welcome content
            content_layout = self._create_responsive_welcome_content()
            layout.addLayout(content_layout)

            # Action buttons - horizontal on small screens to save space
            buttons_layout = self._create_responsive_action_buttons()
            layout.addLayout(buttons_layout)

        else:
            # Horizontal layout for larger screens
            layout = QHBoxLayout(self.hero_card)
            layout.setContentsMargins(24, 20, 24, 20)
            layout.setSpacing(20)
            
            # Welcome content
            content_layout = self._create_responsive_welcome_content()
            
            # Action buttons
            buttons_layout = self._create_responsive_action_buttons()
            
            # App icon/logo area
            icon_container = self._create_responsive_app_icon()
            
            layout.addLayout(content_layout, 2)  # Give content more space
            layout.addLayout(buttons_layout, 1)  # Buttons take less space
            if current_bp.value not in ['md']:  # Hide icon on medium screens
                layout.addStretch()
                layout.addWidget(icon_container)

        # Set up main layout using Qt VBoxLayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.hero_card)

    def _create_responsive_welcome_content(self) -> QVBoxLayout:
        """Create responsive welcome content section"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        content_layout = QVBoxLayout()
        if current_bp.value in ['xs', 'sm']:
            content_layout.setSpacing(6)
        else:
            content_layout.setSpacing(8)

        # Responsive welcome text using QFluentWidgets typography
        welcome_label = TitleLabel(tr("dashboard.welcome.title"))
        # Let QFluentWidgets handle the text styling automatically
        
        # Responsive subtitle using QFluentWidgets typography
        subtitle_label = SubtitleLabel(tr("dashboard.welcome.subtitle"))
        # QFluentWidgets handles theme-appropriate colors automatically

        content_layout.addWidget(welcome_label)
        content_layout.addWidget(subtitle_label)
        
        # Only show description on larger screens
        if current_bp.value not in ['xs', 'sm']:
            description_label = BodyLabel(tr("dashboard.welcome.description"))
            # Let QFluentWidgets handle the styling
            content_layout.addWidget(description_label)
            
        content_layout.addStretch()
        return content_layout

    def _create_responsive_action_buttons(self) -> QVBoxLayout:
        """Create responsive action buttons section"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        if current_bp.value in ['xs', 'sm']:
            # Horizontal layout for small screens to save vertical space
            buttons_container: Union[QHBoxLayout, QVBoxLayout] = QHBoxLayout()
            buttons_container.setSpacing(8)
        else:
            # Vertical layout for larger screens
            buttons_container = QVBoxLayout()
            buttons_container.setSpacing(12)

        # Responsive button sizing
        if current_bp.value in ['xs', 'sm']:
            button_height = 36
            font_size = VidTaniumTheme.FONT_SIZE_CAPTION
        elif current_bp.value == 'md':
            button_height = 40
            font_size = VidTaniumTheme.FONT_SIZE_BODY
        else:
            button_height = 44
            font_size = VidTaniumTheme.FONT_SIZE_BODY

        # New task button with responsive sizing
        self.new_task_btn = PrimaryPushButton(
            tr("dashboard.actions.new_download"))
        self.new_task_btn.setIcon(FIF.ADD)
        self.new_task_btn.setMinimumHeight(button_height)
        
        # Batch import button with responsive sizing
        self.batch_btn = PrimaryPushButton(
            tr("dashboard.actions.batch_import"))
        self.batch_btn.setIcon(FIF.FOLDER_ADD)
        self.batch_btn.setMinimumHeight(button_height)

        buttons_container.addWidget(self.new_task_btn)
        buttons_container.addWidget(self.batch_btn)
        
        if current_bp.value not in ['xs', 'sm']:
            buttons_container.addStretch()

        # Wrap in VBoxLayout for consistent return type
        wrapper_layout = QVBoxLayout()
        wrapper_layout.addLayout(buttons_container)
        return wrapper_layout

    def _create_responsive_app_icon(self) -> QWidget:
        """Create responsive app icon container"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Responsive icon sizing
        if current_bp.value in ['xs', 'sm']:
            container_size = 80
            icon_size = 40
        elif current_bp.value == 'md':
            container_size = 90
            icon_size = 50
        else:
            container_size = 100
            icon_size = 60
        
        icon_container = QWidget()
        icon_container.setFixedSize(container_size, container_size)
        icon_container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: {container_size // 2}px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
        """)

        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        app_icon = IconWidget(FIF.VIDEO)
        app_icon.setFixedSize(icon_size, icon_size)
        app_icon.setStyleSheet(
            "background: transparent; color: white;")
        icon_layout.addWidget(app_icon, 0, Qt.AlignmentFlag.AlignCenter)

        return icon_container

    def _connect_signals(self):
        """Connect button signals"""
        if self.new_task_btn:
            self.new_task_btn.clicked.connect(self._handle_new_task_clicked)
        if self.batch_btn:
            self.batch_btn.clicked.connect(self._handle_batch_import_clicked)

    @Slot()
    def _handle_new_task_clicked(self):
        """Handle new task button click"""
        try:
            logger.info("New task button clicked")

            # Disable button temporarily to prevent multiple clicks
            if self.new_task_btn:
                self.new_task_btn.setEnabled(False)

            # Execute dialog directly on main thread
            if hasattr(self.main_window, 'show_new_task_dialog'):
                self.main_window.show_new_task_dialog()
            else:
                logger.warning(
                    "Main window does not have show_new_task_dialog method")

        except Exception as e:
            logger.error(f"Error handling new task click: {e}")
        finally:
            # Re-enable button after a short delay
            if self.new_task_btn:
                QTimer.singleShot(1000, lambda: self.new_task_btn.setEnabled(
                    True) if self.new_task_btn else None)

    @Slot()
    def _handle_batch_import_clicked(self):
        """Handle batch import button click"""
        try:
            logger.info("Batch import button clicked")

            # Disable button temporarily to prevent multiple clicks
            if self.batch_btn:
                self.batch_btn.setEnabled(False)

            # Execute dialog directly on main thread
            if hasattr(self.main_window, 'import_batch_urls'):
                self.main_window.import_batch_urls()
            else:
                logger.warning(
                    "Main window does not have import_batch_urls method")

        except Exception as e:
            logger.error(f"Error handling batch import click: {e}")
        finally:
            # Re-enable button after a short delay
            if self.batch_btn:
                QTimer.singleShot(1000, lambda: self.batch_btn.setEnabled(
                    True) if self.batch_btn else None)

    def _apply_enhanced_theming(self):
        """Apply enhanced theming using QFluentWidgets theming system"""
        # Use QFluentWidgets built-in theming instead of custom styles
        if isDarkTheme():
            # Dark theme is automatically handled by QFluentWidgets
            pass
        else:
            # Light theme is automatically handled by QFluentWidgets
            pass
            
        # Only apply minimal custom styling for the gradient background
        if self.theme_manager:
            accent_color = self.theme_manager.ACCENT_COLORS.get(
                self.theme_manager.get_current_accent(), '#0078D4'
            )
            
            # Apply minimal gradient styling - let QFluentWidgets handle the rest
            self.hero_card.setStyleSheet(f"""
                ElevatedCardWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {accent_color}, stop:1 rgba(255, 255, 255, 0.1));
                }}
            """)

    def on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        logger.debug(f"Hero section adapting to breakpoint: {breakpoint}")
        # Recreate UI with new breakpoint
        self._setup_enhanced_ui()
        self._apply_enhanced_theming()

    def update_theme(self, theme_manager: Optional[EnhancedThemeManager] = None):
        """Update theme styling"""
        if theme_manager:
            self.theme_manager = theme_manager
        self._apply_enhanced_theming()


# Backward compatibility alias
DashboardHeroSection = EnhancedDashboardHeroSection

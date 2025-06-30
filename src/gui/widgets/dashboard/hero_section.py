"""
Dashboard Hero Section Component
"""
from typing import TYPE_CHECKING, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Slot
from qfluentwidgets import (
    TitleLabel, BodyLabel, SubtitleLabel, PrimaryPushButton,
    FluentIcon as FIF, IconWidget, CardWidget
)

from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme, ThemeManager
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class DashboardHeroSection(QWidget):
    """Hero section component with action buttons"""
    
    def __init__(self, main_window: "MainWindow", parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.new_task_btn: Optional[PrimaryPushButton] = None
        self.batch_btn: Optional[PrimaryPushButton] = None
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the hero section UI"""
        # Main hero card
        self.hero_card = CardWidget()
        self.hero_card.setFixedHeight(160)
        self.hero_card.setStyleSheet(f"""
            CardWidget {{
                background: {VidTaniumTheme.GRADIENT_HERO};
                border: none;
                border-radius: {VidTaniumTheme.RADIUS_XLARGE};
            }}
        """)
        
        # Add themed shadow effect
        self.hero_card.setGraphicsEffect(ThemeManager.get_colored_shadow_effect(
            VidTaniumTheme.PRIMARY_BLUE, 50
        ))
        
        layout = QHBoxLayout(self.hero_card)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)

        # Welcome content
        content_layout = self._create_welcome_content()
        
        # Action buttons
        buttons_layout = self._create_action_buttons()
        
        # App icon/logo area
        icon_container = self._create_app_icon()

        layout.addLayout(content_layout)
        layout.addLayout(buttons_layout)
        layout.addStretch()
        layout.addWidget(icon_container)
        
        # Set up main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.hero_card)
    
    def _create_welcome_content(self) -> QVBoxLayout:
        """Create welcome content section"""
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        
        welcome_label = TitleLabel(tr("dashboard.welcome.title"))
        welcome_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE};
                font-size: {VidTaniumTheme.FONT_SIZE_HERO};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD};
                background: transparent;
            }}
        """)
        
        subtitle_label = SubtitleLabel(tr("dashboard.welcome.subtitle"))
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
                background: transparent;
            }}
        """)
        
        description_label = BodyLabel(tr("dashboard.welcome.description"))
        description_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE_TERTIARY};
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
                background: transparent;
            }}
        """)
        
        content_layout.addWidget(welcome_label)
        content_layout.addWidget(subtitle_label)
        content_layout.addWidget(description_label)
        content_layout.addStretch()
        
        return content_layout
    
    def _create_action_buttons(self) -> QVBoxLayout:
        """Create action buttons section"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(12)
        
        # New task button
        self.new_task_btn = PrimaryPushButton(tr("dashboard.actions.new_download"))
        self.new_task_btn.setIcon(FIF.ADD)
        self.new_task_btn.setStyleSheet(f"""
            PrimaryPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: {VidTaniumTheme.RADIUS_MEDIUM};
                color: {VidTaniumTheme.TEXT_WHITE};
                padding: {VidTaniumTheme.SPACE_MD} {VidTaniumTheme.SPACE_XXL};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
            }}
            PrimaryPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
            PrimaryPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.35);
            }}
        """)
        
        # Batch import button
        self.batch_btn = PrimaryPushButton(tr("dashboard.actions.batch_import"))
        self.batch_btn.setIcon(FIF.FOLDER_ADD)
        self.batch_btn.setStyleSheet(self.new_task_btn.styleSheet())
        
        buttons_layout.addWidget(self.new_task_btn)
        buttons_layout.addWidget(self.batch_btn)
        buttons_layout.addStretch()
        
        return buttons_layout
    
    def _create_app_icon(self) -> QWidget:
        """Create app icon container"""
        icon_container = QWidget()
        icon_container.setFixedSize(100, 100)
        icon_container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 50px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        app_icon = IconWidget(FIF.VIDEO)
        app_icon.setFixedSize(60, 60)
        app_icon.setStyleSheet(f"background: transparent; color: {VidTaniumTheme.TEXT_WHITE};")
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
                logger.warning("Main window does not have show_new_task_dialog method")
                
        except Exception as e:
            logger.error(f"Error handling new task click: {e}")
        finally:
            # Re-enable button after a short delay
            if self.new_task_btn:
                QTimer.singleShot(1000, lambda: self.new_task_btn.setEnabled(True) if self.new_task_btn else None)
    
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
                logger.warning("Main window does not have import_batch_urls method")
                
        except Exception as e:
            logger.error(f"Error handling batch import click: {e}")
        finally:
            # Re-enable button after a short delay
            if self.batch_btn:
                QTimer.singleShot(1000, lambda: self.batch_btn.setEnabled(True) if self.batch_btn else None)

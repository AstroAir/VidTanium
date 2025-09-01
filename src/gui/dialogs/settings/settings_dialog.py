from typing import Union
from typing import Union
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QDialogButtonBox, QWidget, QSpacerItem, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShowEvent, QResizeEvent

from qfluentwidgets import (
    # Buttons
    PrimaryPushButton, PushButton,
    # Cards and Layout
    HeaderCardWidget,
    # Labels and Text
    SubtitleLabel, BodyLabel,
    # Icons and Media
    FluentIcon as FIF, IconWidget,
    # Navigation
    Pivot,
    # Dialogs and Feedback
    MessageBox,
    # Theme
    isDarkTheme
)

from ...utils.responsive import ResponsiveWidget, ResponsiveManager
from ...utils.i18n import tr
from .general_tab import GeneralTab
from .download_tab import DownloadTab
from .advanced_tab import AdvancedTab
from .ui_tab import UITab
from loguru import logger


class EnhancedSettingsDialog(ResponsiveWidget, QDialog):
    """Enhanced Settings Dialog with responsive design and modern aesthetics"""

    settings_changed = Signal()

    def __init__(self, settings, theme_manager=None, parent=None):
        QDialog.__init__(self, parent)
        ResponsiveWidget.__init__(self)
        
        self.settings = settings
        self.theme_manager = theme_manager
        self.responsive_manager = ResponsiveManager.instance()
        
        # Setup window properties
        self._setup_window()
        
        # Apply enhanced theme styles
        self._apply_enhanced_theme_styles()
        
        # Create responsive UI
        self._create_enhanced_ui()
        
        # Load current settings
        self._load_settings()

    def _setup_window(self):
        """Setup window properties with responsive sizing"""
        self.setWindowTitle(tr("settings.dialog.title"))
        self.setWindowIcon(FIF.SETTING.icon())
        
        # Responsive window sizing
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        if current_bp.value in ['xs', 'sm']:
            # Compact size for small screens
            self.setMinimumSize(500, 450)
            self.resize(550, 500)
        elif current_bp.value == 'md':
            # Medium size for medium screens
            self.setMinimumSize(650, 550)
            self.resize(700, 600)
        else:
            # Full size for large screens
            self.setMinimumSize(750, 650)
            self.resize(800, 700)

    def _apply_enhanced_theme_styles(self):
        """Apply enhanced theme-aware styles"""
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            background = colors.get('background', '#FAFAFA')
            surface = colors.get('surface', '#FFFFFF')
            border = colors.get('border', '#E5E7EB')
            shadow = colors.get('shadow', 'rgba(0, 0, 0, 0.1)')
        else:
            # Fallback colors
            if isDarkTheme():
                background = '#2d2d30'
                surface = '#1e1e1e'
                border = '#404040'
                shadow = 'rgba(0, 0, 0, 0.3)'
            else:
                background = '#FAFAFA'
                surface = '#FFFFFF'
                border = '#E5E7EB'
                shadow = 'rgba(0, 0, 0, 0.1)'

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            HeaderCardWidget {{
                background-color: {surface};
                border: 1px solid {border};
                border-radius: 8px;
                box-shadow: 0 2px 4px {shadow};
            }}
            CardWidget {{
                background-color: {surface};
                border: 1px solid {border};
                border-radius: 8px;
                margin: 4px;
            }}
            Pivot {{
                background-color: {surface};
                border-radius: 8px;
            }}
        """)

    def _create_enhanced_ui(self):
        """Create enhanced responsive user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Enhanced header with responsive design
        self._create_enhanced_header(main_layout)

        # Content area with responsive tabs
        self._create_responsive_content(main_layout)

        # Footer with responsive buttons
        self._create_responsive_footer(main_layout)

    def _create_enhanced_header(self, main_layout: QVBoxLayout):
        """Create enhanced header with gradient and responsive design"""
        header_card = HeaderCardWidget()
        header_card.setFixedHeight(80)
        
        # Apply gradient background
        if self.theme_manager and hasattr(self.theme_manager, 'ACCENT_COLORS'):
            accent_color = self.theme_manager.get_current_accent()
            header_card.setStyleSheet(f"""
                HeaderCardWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.theme_manager.ACCENT_COLORS.get(accent_color, '#0078D4')},
                        stop:1 rgba(255, 255, 255, 0.1));
                    border: none;
                    border-radius: 12px 12px 0 0;
                }}
            """)

        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(24, 16, 24, 16)
        header_layout.setSpacing(16)

        # Icon
        icon_widget = IconWidget(FIF.SETTING)
        icon_widget.setFixedSize(48, 48)
        icon_widget.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(icon_widget)

        # Title and subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = SubtitleLabel("Settings")
        title_label.setStyleSheet("color: white; font-weight: bold; margin: 0;")
        
        subtitle_label = BodyLabel("Configure application preferences")
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); margin: 0;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        main_layout.addWidget(header_card)

    def _create_responsive_content(self, main_layout: QVBoxLayout):
        """Create responsive content area with adaptive tabs"""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 0)
        content_layout.setSpacing(16)

        # Enhanced pivot with responsive behavior
        self.pivot = Pivot()
        self.pivot.setFixedHeight(40)
        
        # Tab content stack
        self.stack_widget = QStackedWidget()
        
        # Create enhanced tab pages
        self._create_enhanced_tabs()

        content_layout.addWidget(self.pivot)
        content_layout.addWidget(self.stack_widget)

        main_layout.addWidget(content_widget)

    def _create_enhanced_tabs(self):
        """Create enhanced tab pages with responsive design"""
        # General tab
        self.general_tab = GeneralTab()
        self.stack_widget.addWidget(self.general_tab)
        self.pivot.addItem(
            routeKey="general",
            text="General",
            onClick=lambda: self.stack_widget.setCurrentWidget(self.general_tab)
        )

        # Download tab
        self.download_tab = DownloadTab()
        self.stack_widget.addWidget(self.download_tab)
        self.pivot.addItem(
            routeKey="download",
            text="Download",
            onClick=lambda: self.stack_widget.setCurrentWidget(self.download_tab)
        )

        # UI tab
        self.ui_tab = UITab()
        if hasattr(self.ui_tab, '__init__'):
            # Re-initialize with theme manager if possible
            try:
                self.ui_tab = UITab(theme_manager=self.theme_manager)
            except:
                pass
        self.stack_widget.addWidget(self.ui_tab)
        self.pivot.addItem(
            routeKey="ui",
            text="Interface",
            onClick=lambda: self.stack_widget.setCurrentWidget(self.ui_tab)
        )

        # Advanced tab
        self.advanced_tab = AdvancedTab()
        self.stack_widget.addWidget(self.advanced_tab)
        self.pivot.addItem(
            routeKey="advanced",
            text="Advanced",
            onClick=lambda: self.stack_widget.setCurrentWidget(self.advanced_tab)
        )

        # Set default tab
        self.pivot.setCurrentItem("general")
        self.stack_widget.setCurrentWidget(self.general_tab)

    def _create_responsive_footer(self, main_layout: QVBoxLayout):
        """Create responsive footer with adaptive button layout"""
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(20, 16, 20, 20)
        footer_layout.setSpacing(12)

        footer_layout.addStretch()

        # Create buttons with responsive spacing
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        if current_bp.value in ['xs', 'sm']:
            # Vertical button layout for small screens
            button_layout: Union[QVBoxLayout, QHBoxLayout] = QVBoxLayout()
            button_layout.setSpacing(8)
        else:
            # Horizontal button layout for larger screens
            button_layout = QHBoxLayout()
            button_layout.setSpacing(12)

        # Reset button
        self.reset_btn = PushButton("Reset")
        self.reset_btn.setIcon(FIF.CANCEL)
        self.reset_btn.clicked.connect(self._reset_settings)

        # Apply button
        self.apply_btn = PushButton("Apply")
        self.apply_btn.setIcon(FIF.ACCEPT)
        self.apply_btn.clicked.connect(self._apply_settings)

        # OK button
        self.ok_btn = PrimaryPushButton("OK")
        self.ok_btn.setIcon(FIF.ACCEPT)
        self.ok_btn.clicked.connect(self._ok_clicked)

        # Cancel button
        self.cancel_btn = PushButton("Cancel")
        self.cancel_btn.setIcon(FIF.CANCEL)
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)

        footer_layout.addLayout(button_layout)
        main_layout.addWidget(footer_widget)

    def on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        logger.debug(f"Settings dialog adapting to breakpoint: {breakpoint}")
        self._setup_window()

    def resizeEvent(self, event: QResizeEvent):
        """Handle resize events for responsive behavior"""
        super().resizeEvent(event)
        self.responsive_manager.update_for_size(event.size())

    def _load_settings(self):
        """Load current settings into the dialog"""
        try:
            # Load settings for each tab
            if hasattr(self, 'general_tab') and hasattr(self.general_tab, 'load_settings'):
                self.general_tab.load_settings(self.settings)
            if hasattr(self, 'download_tab') and hasattr(self.download_tab, 'load_settings'):
                self.download_tab.load_settings(self.settings)
            if hasattr(self, 'ui_tab') and hasattr(self.ui_tab, 'load_settings'):
                self.ui_tab.load_settings(self.settings)
            if hasattr(self, 'advanced_tab') and hasattr(self.advanced_tab, 'load_settings'):
                self.advanced_tab.load_settings(self.settings)
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def _apply_settings(self):
        """Apply current settings"""
        try:
            # Apply settings from each tab
            if hasattr(self, 'general_tab') and hasattr(self.general_tab, 'save_settings'):
                self.general_tab.save_settings(self.settings)
            if hasattr(self, 'download_tab') and hasattr(self.download_tab, 'save_settings'):
                self.download_tab.save_settings(self.settings)
            if hasattr(self, 'ui_tab') and hasattr(self.ui_tab, 'save_settings'):
                self.ui_tab.save_settings(self.settings)
            if hasattr(self, 'advanced_tab') and hasattr(self.advanced_tab, 'save_settings'):
                self.advanced_tab.save_settings(self.settings)
            
            # Save settings to file
            if hasattr(self.settings, 'save_settings'):
                self.settings.save_settings()
            
            # Emit signal
            self.settings_changed.emit()
            
            # Show success message
            MessageBox(
                title="Success",
                content="Settings have been applied successfully.",
                parent=self
            ).show()
            
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            MessageBox(
                title="Error",
                content="Failed to apply settings. Please try again.",
                parent=self
            ).show()

    def _reset_settings(self):
        """Reset settings to defaults"""
        try:
            # Reset each tab
            if hasattr(self, 'general_tab') and hasattr(self.general_tab, 'reset_to_defaults'):
                self.general_tab.reset_to_defaults()
            if hasattr(self, 'download_tab') and hasattr(self.download_tab, 'reset_to_defaults'):
                self.download_tab.reset_to_defaults()
            if hasattr(self, 'ui_tab') and hasattr(self.ui_tab, 'reset_to_defaults'):
                self.ui_tab.reset_to_defaults()
            if hasattr(self, 'advanced_tab') and hasattr(self.advanced_tab, 'reset_to_defaults'):
                self.advanced_tab.reset_to_defaults()
                
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")

    def _ok_clicked(self):
        """Handle OK button click"""
        self._apply_settings()
        self.accept()


# Backward compatibility alias
SettingsDialog = EnhancedSettingsDialog
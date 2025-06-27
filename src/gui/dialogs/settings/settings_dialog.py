from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QDialogButtonBox, QWidget, QSpacerItem, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, Signal

from qfluentwidgets import (
    PrimaryPushButton, PushButton, FluentIcon, MessageBox,
    Pivot, HeaderCardWidget, IconWidget,
    SubtitleLabel, BodyLabel, isDarkTheme
)

from .general_tab import GeneralTab
from .download_tab import DownloadTab
from .advanced_tab import AdvancedTab
from .ui_tab import UITab


class SettingsDialog(QDialog):
    """Modern Settings Dialog with Fluent Design"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.setWindowTitle("设置")
        self.setMinimumSize(700, 600)
        self.resize(750, 650)
        self.setWindowIcon(FluentIcon.SETTING.icon())

        # Apply theme-aware styling
        self._apply_theme_styles()
        self._create_ui()
        self._load_settings()

    def _apply_theme_styles(self):
        """Apply theme-aware styles"""
        if isDarkTheme():
            # Dark theme styles
            self.setStyleSheet("""
                QDialog {
                    background-color: #2d2d30;
                    border: 1px solid #404040;
                    border-radius: 12px;
                }
            """)
        else:
            # Light theme styles
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    border: 1px solid #e5e5e5;
                    border-radius: 12px;
                }
            """)

    def _create_ui(self):
        """Create modern UI with Fluent Design"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)

        # Header section
        self._create_header(main_layout)
        
        # Content section with pivot navigation
        self._create_content(main_layout)
        
        # Action buttons
        self._create_actions(main_layout)

    def _create_header(self, parent_layout):
        """Create modern header section"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Icon
        icon_widget = IconWidget(FluentIcon.SETTING)
        icon_widget.setFixedSize(32, 32)
        header_layout.addWidget(icon_widget)

        # Title and subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = SubtitleLabel("应用设置")
        title_label.setObjectName("titleLabel")
        text_layout.addWidget(title_label)
        
        subtitle_label = BodyLabel("配置应用程序的行为和外观")
        if isDarkTheme():
            subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        else:
            subtitle_label.setStyleSheet("color: rgba(0, 0, 0, 0.6);")
        text_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        parent_layout.addLayout(header_layout)

    def _create_content(self, parent_layout):
        """Create content section with modern navigation"""
        # Create pivot navigation
        self.pivot = Pivot()
        self.pivot.setFixedHeight(48)
        
        # Create stacked widget for content
        self.stacked_widget = QStackedWidget()
        
        # Create tabs
        self.general_tab = GeneralTab(self)
        self.download_tab = DownloadTab(self)
        self.advanced_tab = AdvancedTab(self)
        self.ui_tab = UITab(self)
        
        # Add tabs to stacked widget
        self.stacked_widget.addWidget(self.general_tab)
        self.stacked_widget.addWidget(self.download_tab)
        self.stacked_widget.addWidget(self.advanced_tab)
        self.stacked_widget.addWidget(self.ui_tab)
        
        # Add pivot items
        self.pivot.addItem("general", "常规", icon=FluentIcon.HOME, 
                          onClick=lambda: self.stacked_widget.setCurrentIndex(0))
        self.pivot.addItem("download", "下载", icon=FluentIcon.DOWNLOAD,
                          onClick=lambda: self.stacked_widget.setCurrentIndex(1))
        self.pivot.addItem("advanced", "高级", icon=FluentIcon.SETTING,
                          onClick=lambda: self.stacked_widget.setCurrentIndex(2))
        self.pivot.addItem("ui", "界面", icon=FluentIcon.PALETTE,
                          onClick=lambda: self.stacked_widget.setCurrentIndex(3))
        
        # Add to layout
        parent_layout.addWidget(self.pivot)
        parent_layout.addWidget(self.stacked_widget)

    def _create_actions(self, parent_layout):
        """Create action buttons"""
        # Add spacer
        parent_layout.addItem(QSpacerItem(20, 16, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        # Reset button
        reset_button = PushButton("重置")
        reset_button.setIcon(FluentIcon.UPDATE)
        reset_button.setFixedSize(100, 36)
        reset_button.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_button)

        # Cancel button
        cancel_button = PushButton("取消")
        cancel_button.setIcon(FluentIcon.CANCEL)
        cancel_button.setFixedSize(100, 36)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Apply button
        apply_button = PrimaryPushButton("应用")
        apply_button.setIcon(FluentIcon.ACCEPT)
        apply_button.setFixedSize(100, 36)
        apply_button.clicked.connect(self.accept)
        button_layout.addWidget(apply_button)

        parent_layout.addLayout(button_layout)

    def _reset_settings(self):
        """Reset settings to default"""
        msg_box = MessageBox(
            "重置设置",
            "确定要将所有设置重置为默认值吗？",
            self
        )
        msg_box.yesButton.setText("确定")
        msg_box.cancelButton.setText("取消")

        if msg_box.exec():
            self.settings.reset_to_defaults()
            self._load_settings()

    def _load_settings(self):
        """Load settings to UI"""
        self.general_tab.load_settings(self.settings)
        self.download_tab.load_settings(self.settings)
        self.advanced_tab.load_settings(self.settings)
        self.ui_tab.load_settings(self.settings)

    def _save_settings(self):
        """Save settings"""
        self.general_tab.save_settings(self.settings)
        self.download_tab.save_settings(self.settings)
        self.advanced_tab.save_settings(self.settings)
        self.ui_tab.save_settings(self.settings)

    def accept(self):
        """Override accept to save settings"""
        self._save_settings()
        super().accept()

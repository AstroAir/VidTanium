from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal

from qfluentwidgets import (
    PushButton, FluentIcon, MessageBox
)

from .general_tab import GeneralTab
from .download_tab import DownloadTab
from .advanced_tab import AdvancedTab
from .ui_tab import UITab


class SettingsDialog(QDialog):
    """Settings Dialog"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)
        self.resize(650, 500)  # 设置合适的默认大小
        self.setWindowIcon(FluentIcon.SETTING.icon())  # 添加设置图标

        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """Create user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)  # 使标签看起来更现代

        # General tab
        self.general_tab = GeneralTab(self)
        self.tab_widget.addTab(self.general_tab, "General")

        # Download tab
        self.download_tab = DownloadTab(self)
        self.tab_widget.addTab(self.download_tab, "Download")

        # Advanced tab
        self.advanced_tab = AdvancedTab(self)
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        # UI tab
        self.ui_tab = UITab(self)
        self.tab_widget.addTab(self.ui_tab, "Interface")

        layout.addWidget(self.tab_widget)

        # 使用标准按钮盒
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # 创建重置按钮并添加到按钮盒
        self.reset_button = PushButton("Reset to Default")
        self.reset_button.setIcon(FluentIcon.SYNC)
        self.reset_button.clicked.connect(self._reset_settings)
        self.button_box.addButton(
            self.reset_button, QDialogButtonBox.ResetRole)

        # 设置按钮文本和图标
        self.button_box.button(QDialogButtonBox.Ok).setText("OK")
        self.button_box.button(QDialogButtonBox.Ok).setIcon(FluentIcon.ACCEPT)
        self.button_box.button(QDialogButtonBox.Cancel).setText("Cancel")

        # 连接信号
        self.button_box.accepted.connect(self._save_settings)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def _load_settings(self):
        """Load settings to UI"""
        # 分发设置加载到各个选项卡
        self.general_tab.load_settings(self.settings)
        self.download_tab.load_settings(self.settings)
        self.advanced_tab.load_settings(self.settings)
        self.ui_tab.load_settings(self.settings)

    def _save_settings(self):
        """Save settings"""
        # 分发设置保存到各个选项卡
        self.general_tab.save_settings(self.settings)
        self.download_tab.save_settings(self.settings)
        self.advanced_tab.save_settings(self.settings)
        self.ui_tab.save_settings(self.settings)

        # 接受对话框
        self.accept()

    def _reset_settings(self):
        """Reset settings to default"""
        # 实现重置功能，可以添加确认对话框
        msg_box = MessageBox(
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            self
        )
        msg_box.yesButton.setText("Yes")
        msg_box.cancelButton.setText("No")

        if msg_box.exec():
            # 如果用户确认，则重置设置并重新加载UI
            self.settings.reset_to_defaults()
            self._load_settings()

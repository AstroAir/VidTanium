"""
Enhanced settings interface using QFluentWidgets setting cards
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal

from qfluentwidgets import (
    ScrollArea, SettingCardGroup, SwitchSettingCard,
    OptionsSettingCard, PushSettingCard, FluentIcon as FIF,
    ComboBoxSettingCard, ExpandLayout, Theme, setTheme,
    qconfig
)

import os
from pathlib import Path
from .dialogs.settings_config import SettingsConfig, SettingsConstants, SettingsManager


class ModernSettingsInterface(ScrollArea):
    """Modern settings interface with setting cards"""

    settings_changed = Signal()

    def __init__(self, settings, theme_manager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.theme_manager = theme_manager
        # Load config
        self.config = SettingsConfig()
        SettingsManager.load_from_settings(self.config, self.settings)

        self.setObjectName("settingsInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self._create_setting_cards()

        # Connect signals
        self.config.theme.valueChanged.connect(self._on_theme_changed)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Apply transparent background
        self.enableTransparentBackground()

    def _create_setting_cards(self):
        """Create setting cards"""
        # General settings group
        self.generalGroup = SettingCardGroup("常规设置", self.scrollWidget)

        # Output directory card
        self.outputDirCard = PushSettingCard(
            "选择文件夹",
            FIF.DOWNLOAD,
            "默认下载目录",
            self.config.output_directory.value
        )
        self.outputDirCard.clicked.connect(self._choose_output_directory)

        # Auto cleanup card
        self.autoCleanupCard = SwitchSettingCard(
            FIF.DELETE,
            "自动清理临时文件",
            "下载完成后自动删除临时文件",
            configItem=self.config.auto_cleanup
        )

        # Language card
        self.languageCard = ComboBoxSettingCard(
            configItem=self.config.language,
            icon=FIF.LANGUAGE,
            title="语言",
            content="选择应用程序语言",
            texts=["自动检测", "简体中文", "English"]
        )

        self.generalGroup.addSettingCard(self.outputDirCard)
        self.generalGroup.addSettingCard(self.autoCleanupCard)
        self.generalGroup.addSettingCard(self.languageCard)

        # Appearance settings group
        self.appearanceGroup = SettingCardGroup("外观设置", self.scrollWidget)

        # Theme card
        self.themeCard = OptionsSettingCard(
            self.config.theme,
            FIF.PALETTE,
            "应用主题",
            "调整应用程序的外观",
            texts=["跟随系统设置", "浅色", "深色"]
        )

        self.appearanceGroup.addSettingCard(self.themeCard)

        # Update settings group
        self.updateGroup = SettingCardGroup("更新设置", self.scrollWidget)

        # Check updates card
        self.checkUpdatesCard = SwitchSettingCard(
            FIF.UPDATE,
            "自动检查更新",
            "启动时检查是否有新版本可用",
            configItem=self.config.check_updates
        )
        # Max recent files card (using a custom implementation)
        from qfluentwidgets import SettingCard, SpinBox

        class SimpleSpinBoxSettingCard(SettingCard):
            def __init__(self, icon, title, content, config_item):
                super().__init__(icon, title, content)
                self.config_item = config_item
                self.spinBox = SpinBox()
                self.spinBox.setRange(0, 50)
                self.spinBox.setValue(config_item.value)
                self.spinBox.valueChanged.connect(self._on_value_changed)
                self.hBoxLayout.addWidget(self.spinBox)
                self.hBoxLayout.addSpacing(16)

            def _on_value_changed(self, value):
                self.config_item.value = value

        self.maxRecentCard = SimpleSpinBoxSettingCard(
            FIF.HISTORY,
            "最大历史记录数",
            "保留的最大历史记录数量",
            self.config.max_recent_files
        )

        self.updateGroup.addSettingCard(self.checkUpdatesCard)
        self.updateGroup.addSettingCard(self.maxRecentCard)

        # Add groups to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.generalGroup)
        self.expandLayout.addWidget(self.appearanceGroup)
        self.expandLayout.addWidget(self.updateGroup)

    def _choose_output_directory(self):
        """Choose output directory"""
        from PySide6.QtWidgets import QFileDialog

        current_dir = self.config.output_directory.value
        if not os.path.exists(current_dir):
            current_dir = str(Path.home())

        folder = QFileDialog.getExistingDirectory(
            self, "选择默认下载目录", current_dir
        )

        if folder:
            self.config.output_directory.value = folder
            self.outputDirCard.setContent(folder)
            self.save_settings()

    def _on_theme_changed(self, theme_value):
        """Handle theme change"""
        if self.theme_manager:
            self.theme_manager.set_theme(theme_value)
        self.save_settings()

    def save_settings(self):
        """Save all settings using the shared SettingsManager"""
        try:
            SettingsManager.save_to_settings(self.config, self.settings)
            self.settings_changed.emit()
        except Exception as e:
            print(f"Error saving settings: {e}")
            raise

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt, Signal
import os

from qfluentwidgets import (
    PushButton, SpinBox, CheckBox, ComboBox,
    FluentIcon, CardWidget, StrongBodyLabel, BodyLabel,
    SwitchButton, LineEdit as FluentLineEdit, TransparentToolButton
)


class GeneralTab(QWidget):
    """General settings tab with modern card-based design"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """Create modern user interface with cards"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Output directory card
        output_card = self._create_output_directory_card()
        layout.addWidget(output_card)

        # Behavior settings card
        behavior_card = self._create_behavior_settings_card()
        layout.addWidget(behavior_card)

        # Appearance settings card
        appearance_card = self._create_appearance_settings_card()
        layout.addWidget(appearance_card)

        # Update settings card
        update_card = self._create_update_settings_card()
        layout.addWidget(update_card)

        layout.addStretch()

    def _create_output_directory_card(self):
        """Create output directory settings card"""
        card = CardWidget()
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Title
        title = StrongBodyLabel("默认下载目录")
        layout.addWidget(title)
        
        # Output directory input
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(8)
        
        self.output_dir_input = FluentLineEdit()
        self.output_dir_input.setPlaceholderText("选择默认下载文件夹...")
        dir_layout.addWidget(self.output_dir_input)

        self.browse_output_button = TransparentToolButton(FluentIcon.FOLDER)
        self.browse_output_button.setToolTip("浏览文件夹")
        self.browse_output_button.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(self.browse_output_button)

        layout.addLayout(dir_layout)
        
        return card

    def _create_behavior_settings_card(self):
        """Create behavior settings card"""
        card = CardWidget()
        card.setFixedHeight(100)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Title
        title = StrongBodyLabel("行为设置")
        layout.addWidget(title)
        
        # Auto cleanup
        cleanup_layout = QHBoxLayout()
        cleanup_layout.setContentsMargins(0, 0, 0, 0)
        
        cleanup_label = BodyLabel("自动清理临时文件")
        cleanup_layout.addWidget(cleanup_label)
        cleanup_layout.addStretch()
        
        self.auto_cleanup_switch = SwitchButton()
        self.auto_cleanup_switch.setOnText("开启")
        self.auto_cleanup_switch.setOffText("关闭")
        cleanup_layout.addWidget(self.auto_cleanup_switch)
        
        layout.addLayout(cleanup_layout)
        
        return card

    def _create_appearance_settings_card(self):
        """Create appearance settings card"""
        card = CardWidget()
        card.setFixedHeight(140)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Title
        title = StrongBodyLabel("外观设置")
        layout.addWidget(title)
        
        # Language setting
        lang_layout = QHBoxLayout()
        lang_layout.setContentsMargins(0, 0, 0, 0)
        
        lang_label = BodyLabel("语言")
        lang_layout.addWidget(lang_label)
        lang_layout.addStretch()
        
        self.language_combo = ComboBox()
        self.language_combo.addItem("自动检测", "auto")
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.addItem("English", "en_US")
        self.language_combo.setMinimumWidth(150)
        lang_layout.addWidget(self.language_combo)
        
        layout.addLayout(lang_layout)
        
        # Theme setting
        theme_layout = QHBoxLayout()
        theme_layout.setContentsMargins(0, 0, 0, 0)
        
        theme_label = BodyLabel("主题")
        theme_layout.addWidget(theme_label)
        theme_layout.addStretch()
        
        self.theme_combo = ComboBox()
        self.theme_combo.addItem("跟随系统", "system")
        self.theme_combo.addItem("浅色", "light")
        self.theme_combo.addItem("深色", "dark")
        self.theme_combo.setMinimumWidth(150)
        # Connect theme change to immediate preview
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        
        layout.addLayout(theme_layout)
        
        return card

    def _create_update_settings_card(self):
        """Create update settings card"""
        card = CardWidget()
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Title
        title = StrongBodyLabel("更新设置")
        layout.addWidget(title)
        
        # Check updates
        update_layout = QHBoxLayout()
        update_layout.setContentsMargins(0, 0, 0, 0)
        
        update_label = BodyLabel("启动时检查更新")
        update_layout.addWidget(update_label)
        update_layout.addStretch()
        
        self.check_updates_switch = SwitchButton()
        self.check_updates_switch.setOnText("开启")
        self.check_updates_switch.setOffText("关闭")
        update_layout.addWidget(self.check_updates_switch)
        
        layout.addLayout(update_layout)
        
        # Max recent files
        recent_layout = QHBoxLayout()
        recent_layout.setContentsMargins(0, 0, 0, 0)
        
        recent_label = BodyLabel("最大历史记录数")
        recent_layout.addWidget(recent_label)
        recent_layout.addStretch()
        
        self.max_recent_files_spin = SpinBox()
        self.max_recent_files_spin.setRange(0, 50)
        self.max_recent_files_spin.setValue(10)
        self.max_recent_files_spin.setMinimumWidth(80)
        recent_layout.addWidget(self.max_recent_files_spin)
        
        layout.addLayout(recent_layout)
        
        return card

    def _browse_output_dir(self):
        """Browse output directory"""
        from PySide6.QtWidgets import QFileDialog
        current_dir = self.output_dir_input.text()
        if not current_dir or not os.path.exists(current_dir):
            current_dir = os.path.expanduser("~")

        directory = QFileDialog.getExistingDirectory(
            self, "选择默认输出目录", current_dir
        )

        if directory:
            self.output_dir_input.setText(directory)

    def _on_theme_changed(self):
        """Handle theme change for immediate preview"""
        try:
            from qfluentwidgets import setTheme, Theme
            
            theme_data = self.theme_combo.currentData()
            if theme_data == "light":
                setTheme(Theme.LIGHT)
            elif theme_data == "dark":
                setTheme(Theme.DARK)
            else:
                setTheme(Theme.AUTO)
        except Exception as e:
            # Ignore errors during preview
            pass

    def load_settings(self, settings):
        """Load settings to UI"""
        # General settings
        self.output_dir_input.setText(
            settings.get("general", "output_directory", ""))
        self.auto_cleanup_switch.setChecked(
            settings.get("general", "auto_cleanup", True))

        language = settings.get("general", "language", "auto")
        index = self.language_combo.findData(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        theme = settings.get("general", "theme", "system")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.check_updates_switch.setChecked(
            settings.get("general", "check_updates", True))
        self.max_recent_files_spin.setValue(
            settings.get("general", "max_recent_files", 10))

    def save_settings(self, settings):
        """Save settings"""
        # General settings
        settings.set("general", "output_directory",
                     self.output_dir_input.text())
        settings.set("general", "auto_cleanup",
                     self.auto_cleanup_switch.isChecked())
        settings.set("general", "language",
                     self.language_combo.currentData())
        settings.set("general", "theme", self.theme_combo.currentData())
        settings.set("general", "check_updates",
                     self.check_updates_switch.isChecked())
        settings.set("general", "max_recent_files",
                     self.max_recent_files_spin.value())

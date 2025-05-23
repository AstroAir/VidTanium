from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt, Signal
import os

from qfluentwidgets import (
    PushButton, SpinBox, CheckBox, ComboBox,
    FluentIcon
)


class GeneralTab(QWidget):
    """General settings tab"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """Create user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Basic settings
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setSpacing(12)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        output_layout.addWidget(self.output_dir_input)

        self.browse_output_button = PushButton("Browse...")
        self.browse_output_button.setIcon(FluentIcon.FOLDER)
        self.browse_output_button.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self.browse_output_button)

        form_layout.addRow("Default output directory:", output_layout)

        # Auto cleanup
        self.auto_cleanup_check = CheckBox(
            "Automatically clean temporary files after download")
        form_layout.addRow("", self.auto_cleanup_check)

        # Language
        self.language_combo = ComboBox()
        self.language_combo.addItem("Auto", "auto")
        self.language_combo.addItem("Simplified Chinese", "zh_CN")
        self.language_combo.addItem("English", "en_US")
        form_layout.addRow("Language:", self.language_combo)

        # Theme
        self.theme_combo = ComboBox()
        self.theme_combo.addItem("Follow System", "system")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")
        form_layout.addRow("Theme:", self.theme_combo)

        # Check updates
        self.check_updates_check = CheckBox("Check for updates at startup")
        form_layout.addRow("", self.check_updates_check)

        # Max recent files
        self.max_recent_files_spin = SpinBox()
        self.max_recent_files_spin.setRange(0, 50)
        form_layout.addRow("Max recent files:", self.max_recent_files_spin)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _browse_output_dir(self):
        """Browse output directory"""
        from PySide6.QtWidgets import QFileDialog
        current_dir = self.output_dir_input.text()
        if not current_dir or not os.path.exists(current_dir):
            current_dir = os.path.expanduser("~")

        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Output Directory", current_dir
        )

        if directory:
            self.output_dir_input.setText(directory)

    def load_settings(self, settings):
        """Load settings to UI"""
        # General settings
        self.output_dir_input.setText(
            settings.get("general", "output_directory", ""))
        self.auto_cleanup_check.setChecked(
            settings.get("general", "auto_cleanup", True))

        language = settings.get("general", "language", "auto")
        index = self.language_combo.findData(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        theme = settings.get("general", "theme", "system")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.check_updates_check.setChecked(
            settings.get("general", "check_updates", True))
        self.max_recent_files_spin.setValue(
            settings.get("general", "max_recent_files", 10))

    def save_settings(self, settings):
        """Save settings"""
        # General settings
        settings.set("general", "output_directory",
                     self.output_dir_input.text())
        settings.set("general", "auto_cleanup",
                     self.auto_cleanup_check.isChecked())
        settings.set("general", "language",
                     self.language_combo.currentData())
        settings.set("general", "theme", self.theme_combo.currentData())
        settings.set("general", "check_updates",
                     self.check_updates_check.isChecked())
        settings.set("general", "max_recent_files",
                     self.max_recent_files_spin.value())

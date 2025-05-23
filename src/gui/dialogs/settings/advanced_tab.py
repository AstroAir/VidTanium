from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt, Signal
import os

from qfluentwidgets import (
    PushButton, CheckBox, FluentIcon
)


class AdvancedTab(QWidget):
    """Advanced settings tab"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """Create user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Network settings
        network_group = QGroupBox("Network Settings")
        network_layout = QFormLayout()
        network_layout.setLabelAlignment(Qt.AlignRight)
        network_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        network_layout.setSpacing(12)

        # Proxy
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText(
            "Example: http://proxy.example.com:8080")
        network_layout.addRow("Proxy server:", self.proxy_input)

        # User agent
        self.user_agent_input = QLineEdit()
        network_layout.addRow("User-Agent:", self.user_agent_input)

        # SSL verification
        self.verify_ssl_check = CheckBox("Verify SSL certificates")
        network_layout.addRow("", self.verify_ssl_check)

        network_group.setLayout(network_layout)
        layout.addWidget(network_group)

        # External tools settings
        tools_group = QGroupBox("External Tools")
        tools_layout = QFormLayout()
        tools_layout.setLabelAlignment(Qt.AlignRight)
        tools_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        tools_layout.setSpacing(12)

        # FFmpeg path
        ffmpeg_layout = QHBoxLayout()
        self.ffmpeg_path_input = QLineEdit()
        ffmpeg_layout.addWidget(self.ffmpeg_path_input)

        self.browse_ffmpeg_button = PushButton("Browse...")
        self.browse_ffmpeg_button.setIcon(FluentIcon.SEARCH)
        self.browse_ffmpeg_button.clicked.connect(self._browse_ffmpeg)
        ffmpeg_layout.addWidget(self.browse_ffmpeg_button)

        tools_layout.addRow("FFmpeg path:", ffmpeg_layout)

        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)

        # Debug options
        debug_group = QGroupBox("Debug Options")
        debug_layout = QFormLayout()
        debug_layout.setLabelAlignment(Qt.AlignRight)
        debug_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        debug_layout.setSpacing(12)

        # Keep temp files
        self.keep_temp_files_check = CheckBox("Keep temporary files")
        debug_layout.addRow("", self.keep_temp_files_check)

        # Debug logging
        self.debug_logging_check = CheckBox("Enable debug logging")
        debug_layout.addRow("", self.debug_logging_check)

        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)

        layout.addStretch()

    def _browse_ffmpeg(self):
        """Browse for FFmpeg executable"""
        from PySide6.QtWidgets import QFileDialog
        current_path = self.ffmpeg_path_input.text()

        if not current_path or not os.path.exists(current_path):
            current_path = ""

        ffmpeg_file, _ = QFileDialog.getOpenFileName(
            self, "Select FFmpeg Executable", current_path,
            "Executable (*.exe);;All Files (*)" if os.name == "nt" else "All Files (*)"
        )

        if ffmpeg_file:
            self.ffmpeg_path_input.setText(ffmpeg_file)

    def load_settings(self, settings):
        """Load settings to UI"""
        # Advanced settings
        self.proxy_input.setText(settings.get("advanced", "proxy", ""))
        self.user_agent_input.setText(settings.get(
            "advanced", "user_agent", "Mozilla/5.0"))
        self.verify_ssl_check.setChecked(
            settings.get("advanced", "verify_ssl", True))
        self.ffmpeg_path_input.setText(
            settings.get("advanced", "ffmpeg_path", ""))
        self.keep_temp_files_check.setChecked(
            settings.get("advanced", "keep_temp_files", False))
        self.debug_logging_check.setChecked(
            settings.get("advanced", "debug_logging", False))

    def save_settings(self, settings):
        """Save settings"""
        # Advanced settings
        settings.set("advanced", "proxy", self.proxy_input.text())
        settings.set("advanced", "user_agent",
                     self.user_agent_input.text())
        settings.set("advanced", "verify_ssl",
                     self.verify_ssl_check.isChecked())
        settings.set("advanced", "ffmpeg_path",
                     self.ffmpeg_path_input.text())
        settings.set("advanced", "keep_temp_files",
                     self.keep_temp_files_check.isChecked())
        settings.set("advanced", "debug_logging",
                     self.debug_logging_check.isChecked())

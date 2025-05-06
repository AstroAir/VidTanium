from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QFormLayout, QLabel, QLineEdit,
    QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, Slot
import os

from qfluentwidgets import (
    PushButton, SpinBox, CheckBox, ComboBox, Slider,
    ExpandLayout, FluentIcon, MessageBox
)


class SettingsDialog(QDialog):
    """Settings Dialog"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)

        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """Create user interface"""
        layout = QVBoxLayout(self)

        # Tabs
        self.tab_widget = QTabWidget()

        # General tab
        self.general_tab = QWidget()
        self._create_general_tab()
        self.tab_widget.addTab(self.general_tab, "General")

        # Download tab
        self.download_tab = QWidget()
        self._create_download_tab()
        self.tab_widget.addTab(self.download_tab, "Download")

        # Advanced tab
        self.advanced_tab = QWidget()
        self._create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        # UI tab
        self.ui_tab = QWidget()
        self._create_ui_tab()
        self.tab_widget.addTab(self.ui_tab, "Interface")

        layout.addWidget(self.tab_widget)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.reset_button = PushButton("Reset to Default")
        self.reset_button.setIcon(FluentIcon.SYNC)
        self.reset_button.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(self.reset_button)

        buttons_layout.addStretch()

        self.cancel_button = PushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.ok_button = PushButton("OK")
        self.ok_button.setIcon(FluentIcon.ACCEPT)
        self.ok_button.clicked.connect(self._save_settings)
        self.ok_button.setDefault(True)
        buttons_layout.addWidget(self.ok_button)

        layout.addLayout(buttons_layout)

    def _create_general_tab(self):
        """Create general tab"""
        layout = ExpandLayout(self.general_tab)

        # Basic settings
        form_layout = QFormLayout()

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

    def _create_download_tab(self):
        """Create download tab"""
        layout = ExpandLayout(self.download_tab)

        # Download settings
        form_layout = QFormLayout()

        # Max concurrent tasks
        self.max_tasks_spin = SpinBox()
        self.max_tasks_spin.setRange(1, 10)
        form_layout.addRow("Max concurrent tasks:", self.max_tasks_spin)

        # Max workers per task
        self.max_workers_spin = SpinBox()
        self.max_workers_spin.setRange(1, 32)
        form_layout.addRow("Max workers per task:", self.max_workers_spin)

        # Max retries
        self.max_retries_spin = SpinBox()
        self.max_retries_spin.setRange(1, 10)
        form_layout.addRow("Max retry attempts:", self.max_retries_spin)

        # Retry delay
        self.retry_delay_spin = SpinBox()
        self.retry_delay_spin.setRange(1, 30)
        self.retry_delay_spin.setSuffix(" seconds")
        form_layout.addRow("Retry delay:", self.retry_delay_spin)

        # Request timeout
        self.request_timeout_spin = SpinBox()
        self.request_timeout_spin.setRange(10, 300)
        self.request_timeout_spin.setSuffix(" seconds")
        form_layout.addRow("Request timeout:", self.request_timeout_spin)

        # Chunk size
        self.chunk_size_spin = SpinBox()
        self.chunk_size_spin.setRange(4096, 65536)
        self.chunk_size_spin.setSingleStep(4096)
        self.chunk_size_spin.setSuffix(" bytes")
        form_layout.addRow("Download chunk size:", self.chunk_size_spin)

        # Bandwidth limit
        bandwidth_layout = QHBoxLayout()
        self.bandwidth_slider = Slider(Qt.Horizontal)
        self.bandwidth_slider.setRange(0, 10)
        self.bandwidth_slider.setTickPosition(Slider.TicksBelow)
        self.bandwidth_slider.setTickInterval(1)
        bandwidth_layout.addWidget(self.bandwidth_slider)

        self.bandwidth_label = QLabel("No limit")
        bandwidth_layout.addWidget(self.bandwidth_label)

        self.bandwidth_slider.valueChanged.connect(
            self._update_bandwidth_label)

        form_layout.addRow("Bandwidth limit:", bandwidth_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _create_advanced_tab(self):
        """Create advanced tab"""
        layout = ExpandLayout(self.advanced_tab)

        # Network settings
        network_group = QGroupBox("Network Settings")
        network_layout = QFormLayout()

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

        # Keep temp files
        self.keep_temp_files_check = CheckBox("Keep temporary files")
        debug_layout.addRow("", self.keep_temp_files_check)

        # Debug logging
        self.debug_logging_check = CheckBox("Enable debug logging")
        debug_layout.addRow("", self.debug_logging_check)

        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)

        layout.addStretch()

    def _create_ui_tab(self):
        """Create UI tab"""
        layout = ExpandLayout(self.ui_tab)

        # UI settings
        form_layout = QFormLayout()

        # Show detailed progress
        self.show_detailed_progress_check = CheckBox(
            "Show detailed download progress")
        form_layout.addRow("", self.show_detailed_progress_check)

        # Minimize to tray
        self.minimize_to_tray_check = CheckBox("Minimize to system tray")
        form_layout.addRow("", self.minimize_to_tray_check)

        # Show notifications
        self.show_notifications_check = CheckBox("Show desktop notifications")
        form_layout.addRow("", self.show_notifications_check)

        # Exit confirmation
        self.confirm_on_exit_check = CheckBox("Confirm on exit")
        form_layout.addRow("", self.confirm_on_exit_check)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _browse_output_dir(self):
        """Browse output directory"""
        current_dir = self.output_dir_input.text()
        if not current_dir or not os.path.exists(current_dir):
            current_dir = os.path.expanduser("~")

        directory = QFileDialog.getExistingDirectory(
            self, "Select Default Output Directory", current_dir
        )

        if directory:
            self.output_dir_input.setText(directory)

    def _browse_ffmpeg(self):
        """Browse for FFmpeg executable"""
        current_path = self.ffmpeg_path_input.text()

        if not current_path or not os.path.exists(current_path):
            current_path = ""

        ffmpeg_file, _ = QFileDialog.getOpenFileName(
            self, "Select FFmpeg Executable", current_path,
            "Executable (*.exe);;All Files (*)" if os.name == "nt" else "All Files (*)"
        )

        if ffmpeg_file:
            self.ffmpeg_path_input.setText(ffmpeg_file)

    def _update_bandwidth_label(self, value):
        """Update bandwidth limit label"""
        if value == 0:
            self.bandwidth_label.setText("No limit")
        else:
            speeds = ["512KB/s", "1MB/s", "2MB/s", "5MB/s", "10MB/s",
                      "20MB/s", "50MB/s", "100MB/s", "200MB/s", "Unlimited"]
            self.bandwidth_label.setText(speeds[value - 1])

    def _load_settings(self):
        """Load settings to UI"""
        # General settings
        self.output_dir_input.setText(
            self.settings.get("general", "output_directory", ""))
        self.auto_cleanup_check.setChecked(
            self.settings.get("general", "auto_cleanup", True))

        language = self.settings.get("general", "language", "auto")
        index = self.language_combo.findData(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        theme = self.settings.get("general", "theme", "system")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.check_updates_check.setChecked(
            self.settings.get("general", "check_updates", True))
        self.max_recent_files_spin.setValue(
            self.settings.get("general", "max_recent_files", 10))

        # Download settings
        self.max_tasks_spin.setValue(self.settings.get(
            "download", "max_concurrent_tasks", 3))
        self.max_workers_spin.setValue(self.settings.get(
            "download", "max_workers_per_task", 10))
        self.max_retries_spin.setValue(
            self.settings.get("download", "max_retries", 5))
        self.retry_delay_spin.setValue(
            self.settings.get("download", "retry_delay", 2))
        self.request_timeout_spin.setValue(
            self.settings.get("download", "request_timeout", 60))
        self.chunk_size_spin.setValue(
            self.settings.get("download", "chunk_size", 8192))

        bandwidth_limit = self.settings.get("download", "bandwidth_limit", 0)
        bandwidth_value = 0
        if bandwidth_limit > 0:
            # Convert bandwidth limit to slider value
            if bandwidth_limit <= 512 * 1024:
                bandwidth_value = 1
            elif bandwidth_limit <= 1024 * 1024:
                bandwidth_value = 2
            elif bandwidth_limit <= 2 * 1024 * 1024:
                bandwidth_value = 3
            elif bandwidth_limit <= 5 * 1024 * 1024:
                bandwidth_value = 4
            elif bandwidth_limit <= 10 * 1024 * 1024:
                bandwidth_value = 5
            elif bandwidth_limit <= 20 * 1024 * 1024:
                bandwidth_value = 6
            elif bandwidth_limit <= 50 * 1024 * 1024:
                bandwidth_value = 7
            elif bandwidth_limit <= 100 * 1024 * 1024:
                bandwidth_value = 8
            else:
                bandwidth_value = 9

        self.bandwidth_slider.setValue(bandwidth_value)

        # Advanced settings
        self.proxy_input.setText(self.settings.get("advanced", "proxy", ""))
        self.user_agent_input.setText(self.settings.get(
            "advanced", "user_agent", "Mozilla/5.0"))
        self.verify_ssl_check.setChecked(
            self.settings.get("advanced", "verify_ssl", True))
        self.ffmpeg_path_input.setText(
            self.settings.get("advanced", "ffmpeg_path", ""))
        self.keep_temp_files_check.setChecked(
            self.settings.get("advanced", "keep_temp_files", False))
        self.debug_logging_check.setChecked(
            self.settings.get("advanced", "debug_logging", False))

        # UI settings
        self.show_detailed_progress_check.setChecked(
            self.settings.get("ui", "show_detailed_progress", True))
        self.minimize_to_tray_check.setChecked(
            self.settings.get("ui", "minimize_to_tray", False))
        self.show_notifications_check.setChecked(
            self.settings.get("ui", "show_notifications", True))
        self.confirm_on_exit_check.setChecked(
            self.settings.get("ui", "confirm_on_exit", True))

    def _save_settings(self):
        """Save settings"""
        # General settings
        self.settings.set("general", "output_directory",
                          self.output_dir_input.text())
        self.settings.set("general", "auto_cleanup",
                          self.auto_cleanup_check.isChecked())
        self.settings.set("general", "language",
                          self.language_combo.currentData())
        self.settings.set("general", "theme", self.theme_combo.currentData())
        self.settings.set("general", "check_updates",
                          self.check_updates_check.isChecked())
        self.settings.set("general", "max_recent_files",
                          self.max_recent_files_spin.value())

        # Download settings
        self.settings.set("download", "max_concurrent_tasks",
                          self.max_tasks_spin.value())
        self.settings.set("download", "max_workers_per_task",
                          self.max_workers_spin.value())
        self.settings.set("download", "max_retries",
                          self.max_retries_spin.value())
        self.settings.set("download", "retry_delay",
                          self.retry_delay_spin.value())
        self.settings.set("download", "request_timeout",
                          self.request_timeout_spin.value())
        self.settings.set("download", "chunk_size",
                          self.chunk_size_spin.value())

        # Bandwidth limit
        bandwidth_value = self.bandwidth_slider.value()
        bandwidth_limit = 0
        if bandwidth_value > 0:
            # Convert slider value to bandwidth limit
            limits = [
                512 * 1024,           # 512KB/s
                1024 * 1024,          # 1MB/s
                2 * 1024 * 1024,      # 2MB/s
                5 * 1024 * 1024,      # 5MB/s
                10 * 1024 * 1024,     # 10MB/s
                20 * 1024 * 1024,     # 20MB/s
                50 * 1024 * 1024,     # 50MB/s
                100 * 1024 * 1024,    # 100MB/s
                200 * 1024 * 1024,    # 200MB/s
                0                     # Unlimited
            ]
            bandwidth_limit = limits[bandwidth_value - 1]

        self.settings.set("download", "bandwidth_limit", bandwidth_limit)

        # Advanced settings
        self.settings.set("advanced", "proxy", self.proxy_input.text())
        self.settings.set("advanced", "user_agent",
                          self.user_agent_input.text())
        self.settings.set("advanced", "verify_ssl",
                          self.verify_ssl_check.isChecked())
        self.settings.set("advanced", "ffmpeg_path",
                          self.ffmpeg_path_input.text())
        self.settings.set("advanced", "keep_temp_files",
                          self.keep_temp_files_check.isChecked())
        self.settings.set("advanced", "debug_logging",
                          self.debug_logging_check.isChecked())

        # UI settings
        self.settings.set("ui", "show_detailed_progress",
                          self.show_detailed_progress_check.isChecked())
        self.settings.set("ui", "minimize_to_tray",
                          self.minimize_to_tray_check.isChecked())
        self.settings.set("ui", "show_notifications",
                          self.show_notifications_check.isChecked())
        self.settings.set("ui", "confirm_on_exit",
                          self.confirm_on_exit_check.isChecked())

        # Save settings
        self.settings.save_settings()

        # Close dialog
        self.accept()

    def _reset_settings(self):
        """Reset to default settings"""
        result = MessageBox(
            "Confirm Reset",
            "Are you sure you want to reset all settings to default values?",
            self
        ).exec()

        if result:
            # Reset settings
            self.settings.reset_to_defaults()

            # Reload settings to UI
            self._load_settings()

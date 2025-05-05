from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QFormLayout, QLabel, QLineEdit, QSpinBox,
    QPushButton, QCheckBox, QComboBox, QFileDialog,
    QGroupBox, QSlider
)
from PySide6.QtCore import Qt, Signal, Slot
import os


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 400)

        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)

        # 选项卡
        self.tab_widget = QTabWidget()

        # 常规选项卡
        self.general_tab = QWidget()
        self._create_general_tab()
        self.tab_widget.addTab(self.general_tab, "常规")

        # 下载选项卡
        self.download_tab = QWidget()
        self._create_download_tab()
        self.tab_widget.addTab(self.download_tab, "下载")

        # 高级选项卡
        self.advanced_tab = QWidget()
        self._create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "高级")

        # 界面选项卡
        self.ui_tab = QWidget()
        self._create_ui_tab()
        self.tab_widget.addTab(self.ui_tab, "界面")

        layout.addWidget(self.tab_widget)

        # 按钮
        buttons_layout = QHBoxLayout()

        self.reset_button = QPushButton("重置默认")
        self.reset_button.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(self.reset_button)

        buttons_layout.addStretch()

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self._save_settings)
        self.ok_button.setDefault(True)
        buttons_layout.addWidget(self.ok_button)

        layout.addLayout(buttons_layout)

    def _create_general_tab(self):
        """创建常规选项卡"""
        layout = QVBoxLayout(self.general_tab)

        # 基本设置
        form_layout = QFormLayout()

        # 输出目录
        output_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        output_layout.addWidget(self.output_dir_input)

        self.browse_output_button = QPushButton("浏览...")
        self.browse_output_button.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self.browse_output_button)

        form_layout.addRow("默认输出目录:", output_layout)

        # 自动清理
        self.auto_cleanup_check = QCheckBox("下载完成后自动清理临时文件")
        form_layout.addRow("", self.auto_cleanup_check)

        # 语言
        self.language_combo = QComboBox()
        self.language_combo.addItem("自动", "auto")
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.addItem("英语", "en_US")
        form_layout.addRow("语言:", self.language_combo)

        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("跟随系统", "system")
        self.theme_combo.addItem("亮色", "light")
        self.theme_combo.addItem("暗色", "dark")
        form_layout.addRow("主题:", self.theme_combo)

        # 检查更新
        self.check_updates_check = QCheckBox("启动时检查更新")
        form_layout.addRow("", self.check_updates_check)

        # 最近文件数量
        self.max_recent_files_spin = QSpinBox()
        self.max_recent_files_spin.setRange(0, 50)
        form_layout.addRow("最近文件数量:", self.max_recent_files_spin)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _create_download_tab(self):
        """创建下载选项卡"""
        layout = QVBoxLayout(self.download_tab)

        # 下载设置
        form_layout = QFormLayout()

        # 最大并发任务数
        self.max_tasks_spin = QSpinBox()
        self.max_tasks_spin.setRange(1, 10)
        form_layout.addRow("最大并发任务数:", self.max_tasks_spin)

        # 每个任务的最大线程数
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 32)
        form_layout.addRow("每个任务的最大线程数:", self.max_workers_spin)

        # 最大重试次数
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(1, 10)
        form_layout.addRow("最大重试次数:", self.max_retries_spin)

        # 重试延迟
        self.retry_delay_spin = QSpinBox()
        self.retry_delay_spin.setRange(1, 30)
        self.retry_delay_spin.setSuffix(" 秒")
        form_layout.addRow("重试延迟:", self.retry_delay_spin)

        # 请求超时
        self.request_timeout_spin = QSpinBox()
        self.request_timeout_spin.setRange(10, 300)
        self.request_timeout_spin.setSuffix(" 秒")
        form_layout.addRow("请求超时:", self.request_timeout_spin)

        # 块大小
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(4096, 65536)
        self.chunk_size_spin.setSingleStep(4096)
        self.chunk_size_spin.setSuffix(" 字节")
        form_layout.addRow("下载块大小:", self.chunk_size_spin)

        # 带宽限制
        bandwidth_layout = QHBoxLayout()
        self.bandwidth_slider = QSlider(Qt.Horizontal)
        self.bandwidth_slider.setRange(0, 10)
        self.bandwidth_slider.setTickPosition(QSlider.TicksBelow)
        self.bandwidth_slider.setTickInterval(1)
        bandwidth_layout.addWidget(self.bandwidth_slider)

        self.bandwidth_label = QLabel("不限制")
        bandwidth_layout.addWidget(self.bandwidth_label)

        self.bandwidth_slider.valueChanged.connect(
            self._update_bandwidth_label)

        form_layout.addRow("带宽限制:", bandwidth_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _create_advanced_tab(self):
        """创建高级选项卡"""
        layout = QVBoxLayout(self.advanced_tab)

        # 网络设置
        network_group = QGroupBox("网络设置")
        network_layout = QFormLayout()

        # 代理
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText(
            "例如: http://proxy.example.com:8080")
        network_layout.addRow("代理服务器:", self.proxy_input)

        # 用户代理
        self.user_agent_input = QLineEdit()
        network_layout.addRow("User-Agent:", self.user_agent_input)

        # SSL验证
        self.verify_ssl_check = QCheckBox("验证SSL证书")
        network_layout.addRow("", self.verify_ssl_check)

        network_group.setLayout(network_layout)
        layout.addWidget(network_group)

        # 外部工具设置
        tools_group = QGroupBox("外部工具")
        tools_layout = QFormLayout()

        # FFmpeg路径
        ffmpeg_layout = QHBoxLayout()
        self.ffmpeg_path_input = QLineEdit()
        ffmpeg_layout.addWidget(self.ffmpeg_path_input)

        self.browse_ffmpeg_button = QPushButton("浏览...")
        self.browse_ffmpeg_button.clicked.connect(self._browse_ffmpeg)
        ffmpeg_layout.addWidget(self.browse_ffmpeg_button)

        tools_layout.addRow("FFmpeg路径:", ffmpeg_layout)

        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)

        # 调试选项
        debug_group = QGroupBox("调试选项")
        debug_layout = QFormLayout()

        # 保留临时文件
        self.keep_temp_files_check = QCheckBox("保留临时文件")
        debug_layout.addRow("", self.keep_temp_files_check)

        # 调试日志
        self.debug_logging_check = QCheckBox("启用调试日志")
        debug_layout.addRow("", self.debug_logging_check)

        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)

        layout.addStretch()

    def _create_ui_tab(self):
        """创建界面选项卡"""
        layout = QVBoxLayout(self.ui_tab)

        # 界面设置
        form_layout = QFormLayout()

        # 显示详细进度
        self.show_detailed_progress_check = QCheckBox("显示详细下载进度")
        form_layout.addRow("", self.show_detailed_progress_check)

        # 最小化到托盘
        self.minimize_to_tray_check = QCheckBox("最小化到系统托盘")
        form_layout.addRow("", self.minimize_to_tray_check)

        # 显示通知
        self.show_notifications_check = QCheckBox("显示桌面通知")
        form_layout.addRow("", self.show_notifications_check)

        # 退出确认
        self.confirm_on_exit_check = QCheckBox("退出时确认")
        form_layout.addRow("", self.confirm_on_exit_check)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _browse_output_dir(self):
        """浏览输出目录"""
        current_dir = self.output_dir_input.text()
        if not current_dir or not os.path.exists(current_dir):
            current_dir = os.path.expanduser("~")

        directory = QFileDialog.getExistingDirectory(
            self, "选择默认输出目录", current_dir
        )

        if directory:
            self.output_dir_input.setText(directory)

    def _browse_ffmpeg(self):
        """浏览FFmpeg可执行文件"""
        current_path = self.ffmpeg_path_input.text()

        if not current_path or not os.path.exists(current_path):
            current_path = ""

        ffmpeg_file, _ = QFileDialog.getOpenFileName(
            self, "选择FFmpeg可执行文件", current_path,
            "可执行文件 (*.exe);;所有文件 (*)" if os.name == "nt" else "所有文件 (*)"
        )

        if ffmpeg_file:
            self.ffmpeg_path_input.setText(ffmpeg_file)

    def _update_bandwidth_label(self, value):
        """更新带宽限制标签"""
        if value == 0:
            self.bandwidth_label.setText("不限制")
        else:
            speeds = ["512KB/s", "1MB/s", "2MB/s", "5MB/s", "10MB/s",
                      "20MB/s", "50MB/s", "100MB/s", "200MB/s", "无限制"]
            self.bandwidth_label.setText(speeds[value - 1])

    def _load_settings(self):
        """加载设置到界面"""
        # 常规设置
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

        # 下载设置
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
            # 将带宽限制转换为滑块值
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

        # 高级设置
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

        # 界面设置
        self.show_detailed_progress_check.setChecked(
            self.settings.get("ui", "show_detailed_progress", True))
        self.minimize_to_tray_check.setChecked(
            self.settings.get("ui", "minimize_to_tray", False))
        self.show_notifications_check.setChecked(
            self.settings.get("ui", "show_notifications", True))
        self.confirm_on_exit_check.setChecked(
            self.settings.get("ui", "confirm_on_exit", True))

    def _save_settings(self):
        """保存设置"""
        # 常规设置
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

        # 下载设置
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

        # 带宽限制
        bandwidth_value = self.bandwidth_slider.value()
        bandwidth_limit = 0
        if bandwidth_value > 0:
            # 将滑块值转换为带宽限制
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
                0                     # 无限制
            ]
            bandwidth_limit = limits[bandwidth_value - 1]

        self.settings.set("download", "bandwidth_limit", bandwidth_limit)

        # 高级设置
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

        # 界面设置
        self.settings.set("ui", "show_detailed_progress",
                          self.show_detailed_progress_check.isChecked())
        self.settings.set("ui", "minimize_to_tray",
                          self.minimize_to_tray_check.isChecked())
        self.settings.set("ui", "show_notifications",
                          self.show_notifications_check.isChecked())
        self.settings.set("ui", "confirm_on_exit",
                          self.confirm_on_exit_check.isChecked())

        # 保存设置
        self.settings.save_settings()

        # 关闭对话框
        self.accept()

    def _reset_settings(self):
        """重置为默认设置"""
        from PySide6.QtWidgets import QMessageBox

        result = QMessageBox.question(
            self,
            "确认重置",
            "确定要将所有设置重置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result == QMessageBox.Yes:
            # 重置设置
            self.settings.reset_to_defaults()

            # 重新加载设置到界面
            self._load_settings()

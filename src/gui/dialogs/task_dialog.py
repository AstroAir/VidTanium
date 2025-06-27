from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFileDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QProgressDialog, QWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
import os

from qfluentwidgets import (
    PushButton, LineEdit, CheckBox, SpinBox, ComboBox,
    StrongBodyLabel, InfoBar, InfoBarPosition,
    CardWidget, SubtitleLabel, FluentIcon, BodyLabel, PrimaryPushButton,
    ToolButton, TransparentToolButton, SearchLineEdit, IconWidget, 
    setTheme, Theme, isDarkTheme
)

from src.gui.utils.i18n import tr


class TaskDialog(QDialog):
    """Modern Task Creation Dialog with Fluent Design"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings

        self.setWindowTitle(tr("task_dialog.title"))
        self.setMinimumSize(600, 550)
        self.resize(600, 550)
        self.setWindowIcon(FluentIcon.DOWNLOAD.icon())

        # Apply theme-aware styling
        self._apply_theme_styles()
        self._create_ui()

    def _apply_theme_styles(self):
        """Apply theme-aware styles"""
        if isDarkTheme():
            # Dark theme styles
            self.setStyleSheet("""
                QDialog {
                    background-color: #2d2d30;
                    border: 1px solid #404040;
                    border-radius: 8px;
                }
                QFormLayout QLabel {
                    color: #ffffff;
                    font-weight: 500;
                    padding-right: 8px;
                }
            """)
        else:
            # Light theme styles
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    border: 1px solid #e5e5e5;
                    border-radius: 8px;
                }
                QFormLayout QLabel {
                    color: #323130;
                    font-weight: 500;
                    padding-right: 8px;
                }
            """)

    def _create_ui(self):
        """Create modern UI with Fluent Design"""
        # Main layout with proper spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)

        # Header section
        self._create_header(main_layout)
        
        # Content section with cards
        self._create_content(main_layout)
        
        # Action buttons
        self._create_actions(main_layout)

        # Fill default values
        self._fill_defaults()

    def _create_header(self, parent_layout):
        """Create modern header section"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Icon
        icon_widget = IconWidget(FluentIcon.DOWNLOAD)
        icon_widget.setFixedSize(32, 32)
        header_layout.addWidget(icon_widget)

        # Title and subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = SubtitleLabel(tr("task_dialog.basic_info.title"))
        title_label.setObjectName("titleLabel")
        text_layout.addWidget(title_label)
        
        subtitle_label = BodyLabel(tr("task_dialog.basic_info.subtitle"))
        if isDarkTheme():
            subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        else:
            subtitle_label.setStyleSheet("color: rgba(0, 0, 0, 0.6);")
        text_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        parent_layout.addLayout(header_layout)

    def _create_content(self, parent_layout):
        """Create content section with modern cards"""
        # Basic Information Card
        self.basic_card = CardWidget()
        self.basic_card.setMinimumHeight(280)
        basic_card_layout = QVBoxLayout(self.basic_card)
        basic_card_layout.setContentsMargins(24, 20, 24, 24)
        basic_card_layout.setSpacing(16)        # Card title
        basic_title = StrongBodyLabel(tr("task_dialog.basic_info.card_title"))
        basic_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        basic_card_layout.addWidget(basic_title)
        
        # Form layout
        basic_layout = QFormLayout()
        basic_layout.setContentsMargins(0, 0, 0, 0)
        basic_layout.setVerticalSpacing(16)
        basic_layout.setHorizontalSpacing(16)
        basic_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        basic_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)        # Task name
        self.name_input = LineEdit()
        self.name_input.setPlaceholderText(tr("task_dialog.basic_info.name_placeholder"))
        self.name_input.setMinimumHeight(36)
        basic_layout.addRow(tr("task_dialog.basic_info.task_name"), self.name_input)

        # Video URL with extract button
        url_layout = QHBoxLayout()
        url_layout.setSpacing(8)
        url_layout.setContentsMargins(0, 0, 0, 0)        
        self.base_url_input = SearchLineEdit()
        self.base_url_input.setPlaceholderText(tr("task_dialog.basic_info.url_placeholder"))
        self.base_url_input.setMinimumHeight(36)
        url_layout.addWidget(self.base_url_input, 1)

        self.extract_button = PrimaryPushButton(tr("task_dialog.basic_info.auto_extract"))
        self.extract_button.setIcon(FluentIcon.SEARCH)
        self.extract_button.setFixedSize(80, 36)
        self.extract_button.clicked.connect(self._extract_m3u8_info)
        url_layout.addWidget(self.extract_button)

        basic_layout.addRow(tr("task_dialog.basic_info.video_url"), url_layout)        # Key URL
        self.key_url_input = LineEdit()
        self.key_url_input.setPlaceholderText(tr("task_dialog.basic_info.key_placeholder"))
        self.key_url_input.setMinimumHeight(36)
        basic_layout.addRow(tr("task_dialog.basic_info.key_url"), self.key_url_input)

        # Segments count
        self.segments_input = SpinBox()
        self.segments_input.setRange(1, 10000)
        self.segments_input.setValue(200)
        self.segments_input.setMinimumHeight(36)
        basic_layout.addRow(tr("task_dialog.basic_info.segments"), self.segments_input)

        # Output file
        output_layout = QHBoxLayout()
        output_layout.setSpacing(8)
        output_layout.setContentsMargins(0, 0, 0, 0)        
        self.output_input = LineEdit()
        self.output_input.setPlaceholderText(tr("task_dialog.basic_info.output_placeholder"))
        self.output_input.setMinimumHeight(36)
        output_layout.addWidget(self.output_input, 1)

        self.browse_button = ToolButton(FluentIcon.FOLDER)
        self.browse_button.setFixedSize(36, 36)
        self.browse_button.setToolTip(tr("task_dialog.basic_info.browse_tooltip"))
        self.browse_button.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_button)

        basic_layout.addRow(tr("task_dialog.basic_info.output_file"), output_layout)

        basic_card_layout.addLayout(basic_layout)
        parent_layout.addWidget(self.basic_card)
        
        # Advanced Options Card
        self.advanced_card = CardWidget()
        self.advanced_card.setMinimumHeight(160)
        advanced_card_layout = QVBoxLayout(self.advanced_card)
        advanced_card_layout.setContentsMargins(24, 20, 24, 24)
        advanced_card_layout.setSpacing(16)        # Card title
        advanced_title = StrongBodyLabel(tr("task_dialog.advanced_options.title"))
        advanced_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        advanced_card_layout.addWidget(advanced_title)

        # Form layout for advanced options
        advanced_layout = QFormLayout()
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setVerticalSpacing(16)
        advanced_layout.setHorizontalSpacing(16)
        advanced_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        advanced_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)        # Priority
        self.priority_combo = ComboBox()
        self.priority_combo.addItem(tr("task_dialog.advanced_options.priority_high"), "high")
        self.priority_combo.addItem(tr("task_dialog.advanced_options.priority_normal"), "normal") 
        self.priority_combo.addItem(tr("task_dialog.advanced_options.priority_low"), "low")
        self.priority_combo.setCurrentIndex(1)
        self.priority_combo.setMinimumHeight(36)
        advanced_layout.addRow(tr("task_dialog.advanced_options.priority"), self.priority_combo)

        # Options
        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)        
        self.auto_start_check = CheckBox(tr("task_dialog.advanced_options.auto_start"))
        self.auto_start_check.setChecked(True)
        options_layout.addWidget(self.auto_start_check)
        
        self.notify_check = CheckBox(tr("task_dialog.advanced_options.notify_completion"))
        self.notify_check.setChecked(True)
        options_layout.addWidget(self.notify_check)
        
        advanced_layout.addRow(tr("task_dialog.advanced_options.options"), options_widget)

        advanced_card_layout.addLayout(advanced_layout)
        parent_layout.addWidget(self.advanced_card)

    def _create_actions(self, parent_layout):
        """Create action buttons"""
        # Add spacer
        parent_layout.addItem(QSpacerItem(20, 16, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()        # Cancel button
        self.cancel_button = PushButton(tr("task_dialog.buttons.cancel"))
        self.cancel_button.setIcon(FluentIcon.CANCEL)
        self.cancel_button.setFixedSize(100, 36)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # Create button
        self.create_button = PrimaryPushButton(tr("task_dialog.buttons.create"))
        self.create_button.setIcon(FluentIcon.ACCEPT)
        self.create_button.setFixedSize(120, 36)
        self.create_button.clicked.connect(self._on_ok)
        button_layout.addWidget(self.create_button)

        parent_layout.addLayout(button_layout)

    def _fill_defaults(self):
        """填充默认值"""
        # 设置默认的输出目录
        output_dir = self.settings.get("general", "output_directory", "")
        if output_dir and os.path.exists(output_dir):
            self.output_input.setText(os.path.join(output_dir, "output.mp4"))

    def _browse_output(self):
        """浏览输出文件"""
        output_dir = self.settings.get("general", "output_directory", "")
        filename, _ = QFileDialog.getSaveFileName(
            self, tr("task_dialog.file_dialog.save_title"), output_dir, tr("task_dialog.file_dialog.video_filter")
        )

        if filename:
            self.output_input.setText(filename)            # 更新默认输出目录
            self.settings.set("general", "output_directory",
                              os.path.dirname(filename))

    def _on_ok(self):
        """确定按钮点击"""
        # 验证输入
        if not self.base_url_input.text():
            self._show_error(tr("task_dialog.errors.no_url"))
            return

        # 密钥URL不是必需的，注释掉这个检查
        # if not self.key_url_input.text():
        #     self._show_error("请输入密钥URL")
        #     return

        if not self.output_input.text():
            self._show_error(tr("task_dialog.errors.no_output"))
            return

        # 创建任务名称（如果未提供）
        if not self.name_input.text():
            filename = os.path.basename(self.output_input.text())
            name = os.path.splitext(filename)[0]
            self.name_input.setText(name)

        # 接受对话框
        self.accept()

    def _show_error(self, message):
        """显示错误消息"""
        InfoBar.error(
            title=tr("task_dialog.errors.input_error"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _extract_m3u8_info(self):
        """从M3U8 URL自动提取信息"""
        url = self.base_url_input.text().strip()
        if not url:
            self._show_error(tr("task_dialog.errors.no_url"))
            return

        # 显示加载对话框
        progress = QProgressDialog(tr("task_dialog.extraction.progress"), tr("task_dialog.extraction.cancel"), 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle(tr("task_dialog.extraction.title"))
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        try:
            # 导入M3U8解析器
            from src.core.m3u8_parser import extract_m3u8_info

            # 获取用户代理设置
            user_agent = self.settings.get("advanced", "user_agent", "")
            headers = {"User-Agent": user_agent} if user_agent else None

            # 提取信息
            result = extract_m3u8_info(url, headers)            # 关闭进度对话框
            progress.close()

            if not result["success"]:
                self._show_error(tr("task_dialog.errors.extract_failed").format(message=result['message']))
                return

            # 填充表单
            if result["base_url"]:
                self.base_url_input.setText(result["base_url"])

            if result["key_url"]:
                self.key_url_input.setText(result["key_url"])

            if result["segments"]:
                self.segments_input.setValue(result["segments"])

            # 如果没有提供任务名称，从URL创建一个
            if not self.name_input.text():
                from urllib.parse import urlparse
                from os.path import basename

                parsed_url = urlparse(url)
                path = parsed_url.path
                name = basename(path)
                if name:
                    name = name.split(".")[0]  # 移除扩展名
                    self.name_input.setText(name)            # 显示提取结果
            resolution = result['selected_stream']['resolution'] if 'resolution' in result['selected_stream'] else tr("common.unknown")
            QMessageBox.information(
                self,
                tr("task_dialog.extraction.success"),
                tr("task_dialog.extraction.success_message").format(
                    resolution=resolution,
                    segments=result['segments'],
                    duration=int(result['duration']),
                    encryption=result['encryption']
                )
            )

        except Exception as e:
            progress.close()
            import traceback
            self._show_error(tr("task_dialog.errors.extract_error").format(error=str(e)))

    def get_task_data(self):
        """获取任务数据"""
        return {
            "name": self.name_input.text(),
            "base_url": self.base_url_input.text(),
            "key_url": self.key_url_input.text(),
            "segments": self.segments_input.value(),
            "output_file": self.output_input.text(),
            "priority": self.priority_combo.currentData(),
            "auto_start": self.auto_start_check.isChecked()
        }

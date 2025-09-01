from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QWidget,
    QDialogButtonBox, QGroupBox, QProgressDialog
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
import os
from typing import Any, List, Dict, Optional, Union

from qfluentwidgets import (
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox, PushButton
)

from .file_list_widget import FileListWidget
from .output_settings_widget import OutputSettingsWidget
from .encoding_settings_widget import EncodingSettingsWidget
from src.core.media_processor import MediaProcessor
from ...utils.i18n import tr


class BatchConversionDialog(QDialog):
    """批量媒体转换对话框"""

    # 处理完成时发出信号
    processing_completed = Signal(bool, str)

    def __init__(self, settings: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.settings = settings

        self.setWindowTitle(tr("batch_conversion_dialog.title"))
        self.setMinimumSize(750, 550)
        self.setWindowIcon(QIcon(":/images/convert.png"))

        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """创建用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 创建分割器，使用户可以调整文件列表和设置区域的大小
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(self.splitter, 1)

        # ===== 文件选择部分 =====
        self.file_list_widget = FileListWidget()
        self.file_list_widget.file_list_changed.connect(
            self._on_file_list_changed)
        self.splitter.addWidget(self.file_list_widget)

        # ===== 转换设置部分 =====
        settings_container = QWidget()
        settings_container_layout = QVBoxLayout(settings_container)
        settings_container_layout.setContentsMargins(0, 0, 0, 0)

        # 转换设置组
        settings_group = QGroupBox(
            tr("batch_conversion_dialog.sections.conversion_settings"))
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.setContentsMargins(15, 20, 15, 15)
        settings_layout.setSpacing(20)

        # 输出设置组件
        self.output_settings = OutputSettingsWidget()
        settings_layout.addWidget(self.output_settings, 1)

        # 编码设置组件
        self.encoding_settings = EncodingSettingsWidget()
        settings_layout.addWidget(self.encoding_settings, 1)

        settings_container_layout.addWidget(settings_group)
        self.splitter.addWidget(settings_container)

        # 设置分割器的初始大小比例
        self.splitter.setSizes([300, 250])

        # 状态标签 - 在底部显示当前状态
        self.status_layout = QHBoxLayout()
        self.status_layout.setContentsMargins(5, 5, 5, 5)

        self.file_count_label = QLabel(
            tr("batch_conversion_dialog.status.ready"))
        self.status_layout.addWidget(self.file_count_label)
        self.status_layout.addStretch()

        # 添加标准按钮
        self.button_box = QDialogButtonBox()
        self.close_button = self.button_box.addButton(
            tr("batch_conversion_dialog.buttons.close"), QDialogButtonBox.ButtonRole.RejectRole)

        # 使用 PushButton 替代 QPushButton
        self.convert_button = PushButton("开始转换")
        self.convert_button.setIcon(FIF.PLAY)
        self.button_box.addButton(
            self.convert_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self.convert_button.setEnabled(False)  # 初始时禁用，直到有文件

        # 连接按钮信号
        self.button_box.rejected.connect(self.reject)
        self.convert_button.clicked.connect(self._start_conversion)

        # 添加状态栏和按钮到主布局
        main_layout.addLayout(self.status_layout)
        main_layout.addWidget(self.button_box)

    def _load_settings(self):
        """加载设置"""
        # 设置默认输出目录
        default_output_dir: str = self.settings.get(
            "general", "output_directory", "")
        self.output_settings.set_output_directory(default_output_dir)

        # 更新文件计数显示
        self._update_file_count(0)

    @Slot(int)
    def _on_file_list_changed(self, file_count: int):
        """处理文件列表变化"""
        self._update_file_count(file_count)

    def _update_file_count(self, count: int):
        """更新文件计数显示"""
        if count == 0:
            self.file_count_label.setText("未选择文件")
        else:
            self.file_count_label.setText(f"已选择 {count} 个文件")

        # 根据是否有文件启用或禁用转换按钮
        self.convert_button.setEnabled(count > 0)

    def _start_conversion(self):
        """开始批量转换过程"""
        input_files: List[str] = self.file_list_widget.get_input_files()

        if not input_files:
            InfoBar.warning(
                title="无文件",
                content="请添加要转换的文件",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        # 获取转换设置
        output_format: str = self.output_settings.get_output_format()
        output_dir: str = self.output_settings.get_output_directory()
        video_codec: str = self.encoding_settings.get_video_codec()
        audio_codec: str = self.encoding_settings.get_audio_codec()
        resolution: str = self.output_settings.get_resolution()
        keep_original: bool = self.output_settings.get_keep_original()

        quality_settings: Dict[str, Union[str, int]
                               ] = self.encoding_settings.get_quality_settings()
        bitrate: int = quality_settings["bitrate"] if isinstance(
            quality_settings["bitrate"], int) else 0

        # 获取 FFmpeg 路径
        ffmpeg_path: str = self.settings.get(
            "advanced", "ffmpeg_path", "ffmpeg")

        # 转换前确认
        msg_box = MessageBox(
            "确认转换",
            f"准备将 {len(input_files)} 个文件转换为 {output_format.upper()} 格式。\n此操作可能需要较长时间。\n\n确定要继续吗？",
            self
        )
        result = msg_box.exec()

        if not result:
            return

        # 显示处理对话框
        progress = QProgressDialog(
            "处理文件...", "取消", 0, len(input_files), self
        )
        progress.setWindowTitle("批量转换")
        progress.setMinimumDuration(0)
        progress.setModal(True)
        progress.show()

        processor = MediaProcessor(ffmpeg_path)

        # 定义输出选项
        options: Dict[str, Union[str, int, bool]] = {
            "format": output_format,
            "output_dir": output_dir,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "bitrate": bitrate,
            "resolution": resolution,
            "keep_original": keep_original
        }

        # 处理每个文件
        successful: int = 0
        failed: int = 0
        error_messages: List[str] = []

        for i, file_path in enumerate(input_files):
            progress.setValue(i)
            progress.setLabelText(
                f"正在处理第 {i+1}/{len(input_files)} 个文件: {os.path.basename(file_path)}")

            if progress.wasCanceled():
                break

            try:
                convert_result: Dict[str, Union[bool, str]] = processor.batch_convert_file(
                    file_path, options)
                if convert_result.get("success"):
                    successful += 1
                else:
                    failed += 1
                    error_messages.append(
                        f"转换 {os.path.basename(file_path)} 出错: {convert_result.get('message', '未知错误')}")
            except Exception as e:
                failed += 1
                error_messages.append(
                    f"转换 {os.path.basename(file_path)} 出错: {str(e)}")

        progress.setValue(len(input_files))

        # 显示结果
        if successful > 0:
            InfoBar.success(
                title="转换完成",
                content=f"成功转换 {successful} 个文件，失败: {failed}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

            # 向主窗口发送信号
            self.processing_completed.emit(
                True, f"批量转换完成: {successful} 成功, {failed} 失败"
            )
        else:
            error_summary = f"未能成功转换任何文件。失败 {failed} 个。"
            if error_messages:
                error_summary += f"部分错误: {', '.join(error_messages[:3])}"

            InfoBar.error(
                title="转换失败",
                content=error_summary,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

            # 向主窗口发送信号
            self.processing_completed.emit(
                False, f"批量转换失败: {', '.join(error_messages[:3]) if error_messages else '未知错误'}"
            )

        # 更新状态
        self.file_count_label.setText(f"转换完成。成功: {successful}, 失败: {failed}")

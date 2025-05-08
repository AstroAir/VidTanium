from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QAbstractItemView,
    QFileDialog, QFormLayout, QGroupBox, QDialogButtonBox, QSplitter, QWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
import os

from qfluentwidgets import (
    PushButton, ComboBox, LineEdit, SpinBox, CheckBox,
    FluentIcon, InfoBar, InfoBarPosition, MessageBox
)


class BatchConversionDialog(QDialog):
    """批量媒体转换对话框"""

    # 处理完成时发出信号
    processing_completed = Signal(bool, str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.input_files = []

        self.setWindowTitle("批量媒体转换")
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
        self.splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(self.splitter, 1)

        # ===== 文件选择部分 =====
        files_group = QGroupBox("输入文件")
        files_layout = QVBoxLayout(files_group)
        files_layout.setContentsMargins(10, 15, 10, 10)

        # 文件列表
        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.files_list.setAlternatingRowColors(True)
        files_layout.addWidget(self.files_list, 1)

        # 文件按钮 - 水平布局，均匀分布按钮
        file_buttons_layout = QHBoxLayout()
        file_buttons_layout.setSpacing(8)

        self.add_files_button = PushButton("添加文件")
        self.add_files_button.setIcon(FluentIcon.ADD)
        self.add_files_button.clicked.connect(self._add_files)
        file_buttons_layout.addWidget(self.add_files_button)

        self.add_folder_button = PushButton("添加文件夹")
        self.add_folder_button.setIcon(FluentIcon.FOLDER)
        self.add_folder_button.clicked.connect(self._add_folder)
        file_buttons_layout.addWidget(self.add_folder_button)

        self.remove_files_button = PushButton("移除选中")
        self.remove_files_button.setIcon(FluentIcon.REMOVE)
        self.remove_files_button.clicked.connect(self._remove_selected_files)
        file_buttons_layout.addWidget(self.remove_files_button)

        self.clear_files_button = PushButton("清空全部")
        self.clear_files_button.setIcon(FluentIcon.CLEAR)
        self.clear_files_button.clicked.connect(self.files_list.clear)
        file_buttons_layout.addWidget(self.clear_files_button)

        files_layout.addLayout(file_buttons_layout)
        self.splitter.addWidget(files_group)

        # ===== 转换设置部分 =====
        settings_container = QWidget()
        settings_container_layout = QVBoxLayout(settings_container)
        settings_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 转换设置组
        settings_group = QGroupBox("转换设置")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        settings_layout.setContentsMargins(15, 20, 15, 15)
        settings_layout.setSpacing(10)

        # 左侧和右侧设置的垂直布局
        settings_row = QHBoxLayout()
        settings_row.setSpacing(20)
        
        # 左侧设置 - 输出设置
        left_settings = QFormLayout()
        left_settings.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        left_settings.setSpacing(12)

        # 输出格式
        self.format_combo = ComboBox()
        self.format_combo.addItems(["MP4", "MKV", "AVI", "MOV", "FLV", "WebM"])
        left_settings.addRow("输出格式:", self.format_combo)

        # 输出目录
        output_layout = QHBoxLayout()
        self.output_dir_input = LineEdit()
        self.output_dir_input.setPlaceholderText("与输入文件相同目录")
        output_layout.addWidget(self.output_dir_input, 1)

        self.browse_output_button = PushButton("浏览...")
        self.browse_output_button.setIcon(FluentIcon.FOLDER)
        self.browse_output_button.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self.browse_output_button)

        left_settings.addRow("输出目录:", output_layout)

        # 分辨率
        self.resolution_combo = ComboBox()
        self.resolution_combo.addItems(["原始", "1080p", "720p", "480p", "360p"])
        left_settings.addRow("分辨率:", self.resolution_combo)

        # 其他选项
        self.keep_original_check = CheckBox("保留原始文件")
        left_settings.addRow("", self.keep_original_check)

        # 右侧设置 - 编码设置
        right_settings = QFormLayout()
        right_settings.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        right_settings.setSpacing(12)

        # 视频设置
        self.video_codec_combo = ComboBox()
        self.video_codec_combo.addItems(
            ["copy", "libx264", "libx265", "h264_nvenc", "hevc_nvenc"])
        right_settings.addRow("视频编码:", self.video_codec_combo)

        # 视频质量
        self.video_quality_combo = ComboBox()
        self.video_quality_combo.addItems(["高", "中", "低", "自定义"])
        right_settings.addRow("视频质量:", self.video_quality_combo)

        # 自定义码率
        self.bitrate_spin = SpinBox()
        self.bitrate_spin.setRange(500, 20000)
        self.bitrate_spin.setValue(2000)
        self.bitrate_spin.setSuffix(" kbps")
        self.bitrate_spin.setEnabled(False)
        right_settings.addRow("自定义码率:", self.bitrate_spin)

        # 音频设置
        self.audio_codec_combo = ComboBox()
        self.audio_codec_combo.addItems(["copy", "aac", "mp3", "opus"])
        right_settings.addRow("音频编码:", self.audio_codec_combo)

        # 添加左右两列到水平布局
        settings_row.addLayout(left_settings, 1)
        settings_row.addLayout(right_settings, 1)
        settings_layout.addRow("", settings_row)

        settings_container_layout.addWidget(settings_group)
        self.splitter.addWidget(settings_container)
        
        # 设置分割器的初始大小比例
        self.splitter.setSizes([300, 250])

        # 连接信号
        self.video_quality_combo.currentIndexChanged.connect(
            self._on_quality_changed)

        # 状态标签 - 在底部显示当前状态
        self.status_layout = QHBoxLayout()
        self.status_layout.setContentsMargins(5, 5, 5, 5)
        
        self.file_count_label = QLabel("就绪")
        self.status_layout.addWidget(self.file_count_label)
        self.status_layout.addStretch()
        
        # 添加标准按钮
        self.button_box = QDialogButtonBox()
        self.close_button = self.button_box.addButton("关闭", QDialogButtonBox.RejectRole)
        self.convert_button = self.button_box.addButton("开始转换", QDialogButtonBox.AcceptRole)
        self.convert_button.setIcon(FluentIcon.PLAY)
        
        # 连接按钮信号
        self.button_box.rejected.connect(self.reject)
        self.convert_button.clicked.connect(self._start_conversion)
        
        # 添加状态栏和按钮到主布局
        main_layout.addLayout(self.status_layout)
        main_layout.addWidget(self.button_box)

    def _load_settings(self):
        """加载设置"""
        # 设置默认输出目录
        default_output_dir = self.settings.get(
            "general", "output_directory", "")
        self.output_dir_input.setText(default_output_dir)
        
        # 更新文件计数显示
        self._update_file_count()

    def _add_files(self):
        """添加文件到列表"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(
            "媒体文件 (*.mp4 *.mkv *.avi *.mov *.flv *.webm *.ts *.m4v *.3gp *.wmv)")

        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            for file in files:
                if file not in self.input_files:
                    self.input_files.append(file)
                    self.files_list.addItem(os.path.basename(file))
                    # 设置工具提示为完整路径
                    self.files_list.item(self.files_list.count()-1).setToolTip(file)
            
            self._update_file_count()

    def _add_folder(self):
        """添加文件夹中的所有媒体文件"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择包含媒体文件的文件夹"
        )

        if folder:
            media_extensions = ['.mp4', '.mkv', '.avi', '.mov',
                                '.flv', '.webm', '.ts', '.m4v', '.3gp', '.wmv']
            
            # 记录原有文件数量
            original_count = len(self.input_files)

            # 获取文件夹中所有媒体文件
            for root, _, files in os.walk(folder):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext.lower() in media_extensions:
                        file_path = os.path.join(root, file)
                        if file_path not in self.input_files:
                            self.input_files.append(file_path)
                            self.files_list.addItem(os.path.basename(file))
                            # 设置工具提示为完整路径
                            self.files_list.item(self.files_list.count()-1).setToolTip(file_path)

            # 计算新添加的文件数量
            added_files = len(self.input_files) - original_count
            
            self._update_file_count()
            
            InfoBar.success(
                title="文件已添加",
                content=f"从文件夹中添加了 {added_files} 个媒体文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _remove_selected_files(self):
        """从列表中移除选定的文件"""
        selected_items = self.files_list.selectedItems()

        for item in selected_items:
            file_path = item.toolTip()
            if file_path in self.input_files:
                self.input_files.remove(file_path)
            self.files_list.takeItem(self.files_list.row(item))
        
        self._update_file_count()

    def _browse_output_dir(self):
        """浏览输出目录"""
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录"
        )

        if output_dir:
            self.output_dir_input.setText(output_dir)

    def _on_quality_changed(self, index):
        """处理质量选择变化"""
        # 仅对自定义质量启用码率设置
        self.bitrate_spin.setEnabled(index == 3)  # 自定义选项

    def _update_file_count(self):
        """更新文件计数显示"""
        count = len(self.input_files)
        if count == 0:
            self.file_count_label.setText("未选择文件")
        else:
            self.file_count_label.setText(f"已选择 {count} 个文件")
        
        # 根据是否有文件启用或禁用转换按钮
        self.convert_button.setEnabled(count > 0)

    def _start_conversion(self):
        """开始批量转换过程"""
        if not self.input_files:
            InfoBar.warning(
                title="无文件",
                content="请添加要转换的文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        # 获取转换设置
        output_format = self.format_combo.currentText().lower()
        output_dir = self.output_dir_input.text()
        video_codec = self.video_codec_combo.currentText()
        audio_codec = self.audio_codec_combo.currentText()
        resolution = self.resolution_combo.currentText()
        keep_original = self.keep_original_check.isChecked()

        # 处理视频质量
        quality = self.video_quality_combo.currentText()
        if quality == "自定义":
            bitrate = self.bitrate_spin.value()
        else:
            # 将质量选择映射到码率
            quality_map = {
                "高": 5000,
                "中": 2500,
                "低": 1000
            }
            bitrate = quality_map.get(quality, 2000)

        # 获取 FFmpeg 路径
        ffmpeg_path = self.settings.get("advanced", "ffmpeg_path", "ffmpeg")

        # 转换前确认
        result = MessageBox(
            "确认转换",
            f"准备将 {len(self.input_files)} 个文件转换为 {output_format.upper()} 格式。\n此操作可能需要较长时间。\n\n确定要继续吗？",
            self
        ).exec()

        if not result:
            return

        # 显示处理对话框
        from PySide6.QtWidgets import QProgressDialog
        progress = QProgressDialog(
            "处理文件...", "取消", 0, len(self.input_files), self
        )
        progress.setWindowTitle("批量转换")
        progress.setMinimumDuration(0)
        progress.setModal(True)
        progress.show()

        # 导入媒体处理器
        from src.core.media_processor import MediaProcessor
        processor = MediaProcessor(ffmpeg_path)

        # 定义输出选项
        options = {
            "format": output_format,
            "output_dir": output_dir,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "bitrate": bitrate,
            "resolution": resolution,
            "keep_original": keep_original
        }

        # 处理每个文件
        successful = 0
        failed = 0
        error_messages = []

        for i, file_path in enumerate(self.input_files):
            progress.setValue(i)
            progress.setLabelText(
                f"正在处理第 {i+1}/{len(self.input_files)} 个文件: {os.path.basename(file_path)}")

            if progress.wasCanceled():
                break

            try:
                result = processor.batch_convert_file(file_path, options)
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
                    error_messages.append(
                        f"转换 {os.path.basename(file_path)} 出错: {result['message']}")
            except Exception as e:
                failed += 1
                error_messages.append(
                    f"转换 {os.path.basename(file_path)} 出错: {str(e)}")

        progress.setValue(len(self.input_files))

        # 显示结果
        if successful > 0:
            InfoBar.success(
                title="转换完成",
                content=f"成功转换 {successful} 个文件，失败: {failed}",
                orient=Qt.Horizontal,
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
            InfoBar.error(
                title="转换失败",
                content="未能成功转换任何文件。请查看日志了解详情。",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

            # 向主窗口发送信号
            self.processing_completed.emit(
                False, f"批量转换失败: {', '.join(error_messages[:3])}"
            )

        # 更新状态
        self.file_count_label.setText(f"转换完成。成功: {successful}, 失败: {failed}")

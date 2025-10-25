from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QFormLayout, QDialog,
    QButtonGroup, QFileDialog, QTimeEdit, QStackedWidget, QDialogButtonBox
)
from PySide6.QtCore import Qt, QTime, QTimer, Signal, Slot
from PySide6.QtGui import QIntValidator, QIcon
import os
import logging

from qfluentwidgets import (
    PushButton, LineEdit, CheckBox,
    TextEdit, SpinBox, ComboBox, BodyLabel, StrongBodyLabel,
    ProgressBar, FluentIcon as FIF, CardWidget, Slider,
    RadioButton, SubtitleLabel, InfoBar,
    InfoBarPosition, Pivot, TitleLabel,
    IconWidget, PrimaryPushButton, SearchLineEdit
)

# Import optimized progress components
from ..utils.fluent_progress import ProgressCardWidget, FluentProgressBar

from src.core.media_processor import MediaProcessor
from src.gui.utils.i18n import tr

logger = logging.getLogger(__name__)


class MediaProcessingDialog(QDialog):
    """媒体处理对话框"""

    # 处理完成信号
    processing_completed = Signal(bool, str)  # 成功/失败, 消息

    def __init__(self, settings, input_file=None, parent=None) -> None:
        super().__init__(parent)

        self.settings = settings
        self.input_file = input_file

        # 获取FFmpeg路径
        self.ffmpeg_path = self.settings.get("advanced", "ffmpeg_path", "")

        # 创建媒体处理器
        self.processor = MediaProcessor(self.ffmpeg_path)

        self.setWindowTitle(tr("media_processing_dialog.title"))
        self.setMinimumSize(650, 550)
        self.resize(650, 550)
        self.setWindowIcon(FIF.MOVIE.icon())

        self._create_ui()

        # 如果提供了输入文件，填充
        if self.input_file:
            self.input_file_input.setText(self.input_file)
            self._input_file_changed()

    def _create_ui(self) -> None:
        """创建界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)        # 标题
        self.title_label = SubtitleLabel(
            tr("media_processing_dialog.subtitle"))
        main_layout.addWidget(self.title_label)

        # 文件选择卡片
        file_card = CardWidget()
        file_layout = QFormLayout()
        file_layout.setSpacing(10)
        file_layout.setContentsMargins(15, 15, 15, 15)

        # 输入文件
        input_layout = QHBoxLayout()
        self.input_file_input = LineEdit()
        self.input_file_input.setReadOnly(True)
        self.input_file_input.setPlaceholderText(
            tr("media_processing_dialog.file_section.input_placeholder"))
        self.input_file_input.textChanged.connect(self._input_file_changed)
        input_layout.addWidget(self.input_file_input)

        self.browse_input_button = PushButton(
            tr("media_processing_dialog.file_section.browse"))
        self.browse_input_button.setIcon(FIF.FOLDER)
        self.browse_input_button.clicked.connect(self._browse_input)
        input_layout.addWidget(self.browse_input_button)

        file_layout.addRow(
            tr("media_processing_dialog.file_section.input_file"), input_layout)

        # 输出文件
        output_layout = QHBoxLayout()
        self.output_file_input = LineEdit()
        self.output_file_input.setReadOnly(True)
        self.output_file_input.setPlaceholderText(
            tr("media_processing_dialog.file_section.output_placeholder"))
        output_layout.addWidget(self.output_file_input)

        self.browse_output_button = PushButton(
            tr("media_processing_dialog.file_section.browse"))
        self.browse_output_button.setIcon(FIF.SAVE)
        self.browse_output_button.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_output_button)

        file_layout.addRow(
            tr("media_processing_dialog.file_section.output_file"), output_layout)        # 文件信息
        self.file_info_label = BodyLabel(
            tr("media_processing_dialog.file_section.select_input_prompt"))
        file_layout.addRow(
            tr("media_processing_dialog.file_section.file_info"), self.file_info_label)

        file_card.setLayout(file_layout)
        main_layout.addWidget(file_card)

        # 处理选项选项卡
        self.pivot = Pivot()
        self.stacked_widget = QStackedWidget()

        self.pivot.addItem(routeKey="convert", text=tr(
            "media_processing_dialog.processing_tabs.convert"), onClick=lambda: self.stacked_widget.setCurrentIndex(0))
        self.pivot.addItem(routeKey="clip", text=tr(
            "media_processing_dialog.processing_tabs.clip"), onClick=lambda: self.stacked_widget.setCurrentIndex(1))
        self.pivot.addItem(routeKey="audio", text=tr(
            "media_processing_dialog.processing_tabs.audio"), onClick=lambda: self.stacked_widget.setCurrentIndex(2))
        self.pivot.addItem(routeKey="compress", text=tr(
            "media_processing_dialog.processing_tabs.compress"), onClick=lambda: self.stacked_widget.setCurrentIndex(3))

        # 转换格式选项卡
        self.convert_tab = QWidget()
        self._create_convert_tab()
        self.stacked_widget.addWidget(self.convert_tab)

        # 剪辑选项卡
        self.clip_tab = QWidget()
        self._create_clip_tab()
        self.stacked_widget.addWidget(self.clip_tab)

        # 提取音频选项卡
        self.audio_tab = QWidget()
        self._create_audio_tab()
        self.stacked_widget.addWidget(self.audio_tab)        # 压缩选项卡
        self.compress_tab = QWidget()
        self._create_compress_tab()
        self.stacked_widget.addWidget(self.compress_tab)

        main_layout.addWidget(self.pivot)
        main_layout.addWidget(self.stacked_widget)

        # 进度区域 - 使用优化的Fluent Design进度条
        self.progress_card = ProgressCardWidget()
        self.progress_card.setTitle("Processing Progress")
        self.progress_card.setVisible(False)

        # 保持向后兼容性的引用
        self.progress_bar = self.progress_card.progress_bar

        # Add methods for compatibility
        def set_progress_visible(visible) -> None:
            self.progress_card.setVisible(visible)

        def set_progress_format(format_string) -> None:
            self.progress_card.setStatus(format_string)

        # Store methods for later use instead of assigning to attributes
        self._set_progress_visible = set_progress_visible
        self._set_progress_format = set_progress_format

        main_layout.addWidget(self.progress_card)        # 按钮
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            tr("media_processing_dialog.buttons.start"))
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setIcon(
            FIF.PLAY.icon())
        self.button_box.button(
            QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
            tr("common.cancel"))

        self.button_box.accepted.connect(self._start_processing)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

        self.process_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Ok)
        self.cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel)

    def _create_convert_tab(self) -> None:
        """创建格式转换选项卡"""
        layout = QFormLayout(self.convert_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 添加选项卡标题
        option_title = StrongBodyLabel(
            tr("media_processing_dialog.convert_tab.title"))
        layout.addRow(option_title)

        # 输出格式
        self.format_combo = ComboBox()
        self.format_combo.addItems(
            ["MP4", "MKV", "AVI", "MOV", "WebM", "FLV", tr("media_processing_dialog.convert_tab.formats.custom")])
        self.format_combo.currentIndexChanged.connect(self._update_output_file)
        layout.addRow(
            tr("media_processing_dialog.convert_tab.output_format"), self.format_combo)

        # 视频编码
        self.video_codec_combo = ComboBox()
        self.video_codec_combo.addItems(
            [tr("media_processing_dialog.convert_tab.codecs.copy"), "H.264", "H.265", "VP9", "AV1"])
        self.video_codec_combo.setToolTip(
            tr("media_processing_dialog.convert_tab.tooltips.video_codec"))
        layout.addRow(
            tr("media_processing_dialog.convert_tab.video_codec"), self.video_codec_combo)

        # 音频编码
        self.audio_codec_combo = ComboBox()
        self.audio_codec_combo.addItems(
            [tr("media_processing_dialog.convert_tab.codecs.copy"), "AAC", "MP3", "Opus", "FLAC"])
        self.audio_codec_combo.setToolTip(
            tr("media_processing_dialog.convert_tab.tooltips.audio_codec"))
        layout.addRow(
            tr("media_processing_dialog.convert_tab.audio_codec"), self.audio_codec_combo)

        # 分辨率
        resolution_layout = QHBoxLayout()
        self.resolution_x_input = LineEdit()
        self.resolution_x_input.setValidator(QIntValidator(1, 9999))
        self.resolution_x_input.setPlaceholderText(
            tr("media_processing_dialog.convert_tab.width_placeholder"))
        resolution_layout.addWidget(self.resolution_x_input)

        resolution_layout.addWidget(BodyLabel("x"))

        self.resolution_y_input = LineEdit()
        self.resolution_y_input.setValidator(QIntValidator(1, 9999))
        self.resolution_y_input.setPlaceholderText(
            tr("media_processing_dialog.convert_tab.height_placeholder"))
        resolution_layout.addWidget(self.resolution_y_input)

        layout.addRow(
            tr("media_processing_dialog.convert_tab.resolution"), resolution_layout)

        # 帧率
        self.fps_spin = SpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        self.fps_spin.setSpecialValueText(
            tr("media_processing_dialog.convert_tab.codecs.unchanged"))
        self.fps_spin.setToolTip(
            tr("media_processing_dialog.convert_tab.tooltips.framerate"))
        layout.addRow(
            tr("media_processing_dialog.convert_tab.framerate"), self.fps_spin)

        # 添加说明
        hint_label = BodyLabel(
            tr("media_processing_dialog.convert_tab.hints.copy_faster"))
        hint_label.setWordWrap(True)
        layout.addRow("", hint_label)

    def _create_clip_tab(self) -> None:
        """创建视频剪辑选项卡"""
        layout = QFormLayout(self.clip_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 添加选项卡标题
        option_title = StrongBodyLabel(
            tr("media_processing_dialog.clip_tab.title"))
        layout.addRow(option_title)

        # 开始时间
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm:ss")
        self.start_time_edit.setCurrentSectionIndex(0)
        self.start_time_edit.setToolTip(
            tr("media_processing_dialog.clip_tab.tooltips.start_time"))
        layout.addRow(
            tr("media_processing_dialog.clip_tab.start_time"), self.start_time_edit)

        # 结束时间
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm:ss")
        self.end_time_edit.setTime(QTime(0, 5, 0))  # 默认5分钟
        self.end_time_edit.setCurrentSectionIndex(0)
        self.end_time_edit.setToolTip(
            tr("media_processing_dialog.clip_tab.tooltips.end_time"))
        layout.addRow(
            tr("media_processing_dialog.clip_tab.end_time"), self.end_time_edit)

        # 持续时间（自动计算）
        self.duration_label = StrongBodyLabel("00:05:00")
        layout.addRow(
            tr("media_processing_dialog.clip_tab.duration"), self.duration_label)

        # 连接信号以更新持续时间
        self.start_time_edit.timeChanged.connect(self._update_duration)
        self.end_time_edit.timeChanged.connect(self._update_duration)

        # 保持原始编码
        self.keep_codec_check = CheckBox(
            tr("media_processing_dialog.clip_tab.keep_codec"))
        self.keep_codec_check.setChecked(True)
        self.keep_codec_check.setToolTip(
            tr("media_processing_dialog.clip_tab.tooltips.keep_codec"))
        layout.addRow("", self.keep_codec_check)

        # 添加说明
        hint_label = BodyLabel(
            tr("media_processing_dialog.clip_tab.hints.precision"))
        hint_label.setWordWrap(True)
        layout.addRow("", hint_label)

    def _create_audio_tab(self) -> None:
        """创建提取音频选项卡"""
        layout = QFormLayout(self.audio_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 添加选项卡标题
        option_title = StrongBodyLabel(
            tr("media_processing_dialog.audio_tab.title"))
        layout.addRow(option_title)

        # 音频格式
        self.audio_format_combo = ComboBox()
        self.audio_format_combo.addItems(["MP3", "AAC", "WAV", "FLAC", "Opus"])
        self.audio_format_combo.currentIndexChanged.connect(
            self._update_output_file)
        layout.addRow(
            tr("media_processing_dialog.audio_tab.audio_format"), self.audio_format_combo)

        # 音频质量
        # quality_hints = ["非常低", "低", "中等", "高", "非常高"]
        self.audio_quality_slider = Slider(Qt.Orientation.Horizontal)
        self.audio_quality_slider.setRange(0, 4)
        self.audio_quality_slider.setValue(2)
        # self.audio_quality_slider.setHints(quality_hints)
        layout.addRow(
            tr("media_processing_dialog.audio_tab.audio_quality"), self.audio_quality_slider)

        # 添加提示
        hint_label = BodyLabel(
            tr("media_processing_dialog.audio_tab.hints.quality_size"))
        hint_label.setWordWrap(True)
        layout.addRow("", hint_label)

    def _create_compress_tab(self) -> None:
        """创建视频压缩选项卡"""
        layout = QFormLayout(self.compress_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 添加选项卡标题
        option_title = StrongBodyLabel(
            tr("media_processing_dialog.compress_tab.title"))
        layout.addRow(option_title)

        # 压缩方式
        compression_widget = QWidget()  # Create a standard QWidget
        compression_layout = QVBoxLayout(
            compression_widget)  # Layout for the widget
        compression_layout.setSpacing(10)
        compression_layout.setContentsMargins(
            0, 0, 0, 0)  # Remove margins if not needed

        self.compression_type_group = QButtonGroup(self)

        self.quality_radio = RadioButton(
            tr("media_processing_dialog.compress_tab.quality_compression"))
        self.quality_radio.setToolTip(
            tr("media_processing_dialog.compress_tab.tooltips.quality_compression"))
        self.compression_type_group.addButton(self.quality_radio, 0)
        compression_layout.addWidget(self.quality_radio)

        self.size_radio = RadioButton(
            tr("media_processing_dialog.compress_tab.size_compression"))
        self.size_radio.setToolTip(
            tr("media_processing_dialog.compress_tab.tooltips.size_compression"))
        self.compression_type_group.addButton(self.size_radio, 1)
        compression_layout.addWidget(self.size_radio)

        layout.addRow(
            tr("media_processing_dialog.compress_tab.compression_method"), compression_widget)

        # 质量设置
        quality_hints = {0: "无损", 18: "高质量",
                         23: "标准", 28: "中等", 35: "低质量", 51: "最低"}
        self.quality_slider = Slider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(0, 51)
        self.quality_slider.setValue(23)  # 默认23
        # self.quality_slider.setHints(quality_hints)
        self.quality_slider.setToolTip(
            tr("media_processing_dialog.compress_tab.tooltips.quality"))
        layout.addRow(
            tr("media_processing_dialog.compress_tab.quality"), self.quality_slider)

        # 目标大小
        self.target_size_spin = SpinBox()
        self.target_size_spin.setRange(1, 10000)
        self.target_size_spin.setValue(100)
        self.target_size_spin.setSuffix(" MB")
        self.target_size_spin.setToolTip(
            tr("media_processing_dialog.compress_tab.tooltips.target_size"))
        layout.addRow(
            tr("media_processing_dialog.compress_tab.target_size"), self.target_size_spin)

        # 设置默认选中
        self.quality_radio.setChecked(True)
        self._update_compression_ui()

        # 连接信号
        self.compression_type_group.buttonClicked.connect(
            self._update_compression_ui)

        # 添加提示
        hint_label = BodyLabel(
            tr("media_processing_dialog.compress_tab.hints.methods"))
        hint_label.setWordWrap(True)
        layout.addRow("", hint_label)

    def _browse_input(self) -> None:
        """浏览输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择媒体文件", "",
            "媒体文件 (*.mp4 *.mkv *.avi *.mov *.ts *.m4v *.wmv *.flv *.webm *.mp3 *.wav *.aac *.ogg)"
        )

        if file_path:
            self.input_file_input.setText(file_path)

            InfoBar.success(
                title="文件已选择",
                content=f"已选择输入文件: {os.path.basename(file_path)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self)

    def _browse_output(self) -> None:
        """浏览输出文件"""
        # 根据选项卡确定文件类型
        current_tab = self.stacked_widget.currentIndex()
        file_filter = ""

        if current_tab == 0:  # 格式转换
            selected_format = self.format_combo.currentText().lower()
            if selected_format == "自定义":
                file_filter = "所有文件 (*)"
            else:
                file_filter = f"{selected_format.upper()} 文件 (*.{selected_format.lower()})"

        elif current_tab == 1:  # 视频剪辑
            file_filter = "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm);;所有文件 (*)"

        elif current_tab == 2:  # 提取音频
            selected_format = self.audio_format_combo.currentText().lower()
            file_filter = f"音频文件 (*.{selected_format.lower()});;所有文件 (*)"

        elif current_tab == 3:  # 视频压缩
            file_filter = "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm);;所有文件 (*)"

        # 打开文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", file_filter
        )

        if file_path:
            self.output_file_input.setText(file_path)

    def _input_file_changed(self) -> None:
        """输入文件变化时更新"""
        input_file = self.input_file_input.text()

        if input_file and os.path.exists(input_file):
            # 显示文件信息
            self._update_file_info(input_file)

            # 更新输出文件
            self._update_output_file()

            # 启用处理按钮
            self.process_button.setEnabled(True)
        else:
            self.file_info_label.setText("请选择有效的输入文件")
            self.process_button.setEnabled(False)

    def _update_file_info(self, file_path) -> None:
        """更新文件信息"""
        # 获取文件大小
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)

        # 尝试获取更多信息
        try:
            result = self.processor.get_video_info(file_path)

            if result["success"] and "info" in result:
                info = result["info"]

                # 格式信息
                format_info = info.get("format", {})
                duration = float(format_info.get("duration", 0))
                duration_str = self._format_duration(duration)

                # 流信息
                streams = info.get("streams", [])
                video_stream = None
                audio_stream = None

                for stream in streams:
                    if stream.get("codec_type") == "video" and not video_stream:
                        video_stream = stream
                    elif stream.get("codec_type") == "audio" and not audio_stream:
                        audio_stream = stream

                info_text = f"大小: {size_mb:.2f} MB, 时长: {duration_str}"

                if video_stream:
                    # 获取视频信息
                    width = video_stream.get("width", 0)
                    height = video_stream.get("height", 0)
                    codec = video_stream.get("codec_name", "未知")

                    info_text += f"\n视频: {width}x{height}, 编码: {codec}"

                    # 预填充分辨率
                    self.resolution_x_input.setText(str(width))
                    self.resolution_y_input.setText(str(height))

                if audio_stream:
                    # 获取音频信息
                    codec = audio_stream.get("codec_name", "未知")
                    channels = audio_stream.get("channels", 0)

                    info_text += f"\n音频: {channels}声道, 编码: {codec}"

                self.file_info_label.setText(info_text)

                # 更新时间编辑器
                if (duration > 0):
                    end_time = QTime(0, 0, 0).addSecs(int(duration))
                    self.end_time_edit.setTime(end_time)
                    self._update_duration()

                return

        except Exception as e:
            logger.error(f"获取文件信息出错: {e}")

        # 如果无法获取详细信息，显示基本信息
        self.file_info_label.setText(f"大小: {size_mb:.2f} MB")

    def _update_output_file(self) -> None:
        """更新输出文件路径"""
        input_file = self.input_file_input.text()

        if not input_file:
            return

        # 解析输入文件路径
        input_dir = os.path.dirname(input_file)
        input_name = os.path.splitext(os.path.basename(input_file))[
            0]        # 根据当前选项卡确定输出文件格式
        current_tab = self.stacked_widget.currentIndex()
        output_ext = ""

        if current_tab == 0:  # 格式转换
            selected_format = self.format_combo.currentText().lower()
            if selected_format != "自定义":
                output_ext = f".{selected_format.lower()}"
            else:
                # 保持原格式
                output_ext = os.path.splitext(input_file)[1]

        elif current_tab == 1:  # 视频剪辑
            # 保持原格式
            output_ext = os.path.splitext(input_file)[1]

        elif current_tab == 2:  # 提取音频
            selected_format = self.audio_format_combo.currentText().lower()
            output_ext = f".{selected_format.lower()}"

        elif current_tab == 3:  # 视频压缩
            # 保持原格式
            output_ext = os.path.splitext(input_file)[1]

        # 构建输出文件路径
        output_file = os.path.join(
            input_dir, f"{input_name}_processed{output_ext}")

        # 设置输出文件路径
        self.output_file_input.setText(output_file)

    def _update_duration(self) -> None:
        """更新持续时间标签"""
        start_time = self.start_time_edit.time()
        end_time = self.end_time_edit.time()

        # 转换为秒
        start_seconds = start_time.hour() * 3600 + start_time.minute() * \
            60 + start_time.second()
        end_seconds = end_time.hour() * 3600 + end_time.minute() * 60 + end_time.second()

        # 计算持续时间
        duration_seconds = max(0, end_seconds - start_seconds)

        # 格式化持续时间
        duration_time = QTime(0, 0, 0).addSecs(duration_seconds)
        duration_str = duration_time.toString("HH:mm:ss")

        self.duration_label.setText(duration_str)

    def _update_compression_ui(self) -> None:
        """更新压缩UI"""
        is_quality = self.quality_radio.isChecked()

        # 启用/禁用相应控件
        self.quality_slider.setEnabled(is_quality)
        self.target_size_spin.setEnabled(not is_quality)

    def _format_duration(self, seconds) -> None:
        """格式化时长"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}时{minutes}分{secs}秒"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"

    def _start_processing(self) -> None:
        """开始处理"""
        input_file = self.input_file_input.text()
        output_file = self.output_file_input.text()

        # 验证输入
        if not input_file or not os.path.exists(input_file):
            InfoBar.error(
                title="输入错误",
                content="请选择有效的输入文件",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if not output_file:
            InfoBar.error(
                title="输入错误",
                content="请指定输出文件",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                InfoBar.error(
                    title="错误",
                    content=f"无法创建输出目录: {str(e)}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return

        # 禁用UI
        self._disable_ui()

        # 显示进度条
        if self.progress_bar:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, 0)  # 不确定进度
            self.progress_bar.setFormat("处理中...")        # 获取当前选项卡
        current_tab = self.stacked_widget.currentIndex()

        # 根据选项卡执行相应操作
        if current_tab == 0:  # 格式转换
            self._convert_format(input_file, output_file)
        elif current_tab == 1:  # 视频剪辑
            self._clip_video(input_file, output_file)
        elif current_tab == 2:  # 提取音频
            self._extract_audio(input_file, output_file)
        elif current_tab == 3:  # 视频压缩
            self._compress_video(input_file, output_file)

    def _convert_format(self, input_file, output_file) -> None:
        """转换视频格式"""
        # 准备格式选项
        format_options = {}

        # 视频编码
        video_codec = self.video_codec_combo.currentText()
        if video_codec != "复制":
            codec_map = {
                "H.264": "libx264",
                "H.265": "libx265",
                "VP9": "libvpx-vp9",
                "AV1": "libaom-av1"
            }
            format_options["codec"] = codec_map.get(video_codec, video_codec)
        else:
            format_options["codec"] = "copy"

        # 音频编码
        audio_codec = self.audio_codec_combo.currentText()
        if audio_codec != "复制":
            codec_map = {
                "AAC": "aac",
                "MP3": "libmp3lame",
                "Opus": "libopus",
                "FLAC": "flac"
            }
            format_options["audio_codec"] = codec_map.get(
                audio_codec, audio_codec)
        else:
            format_options["audio_codec"] = "copy"

        # 分辨率
        resolution_x = self.resolution_x_input.text()
        resolution_y = self.resolution_y_input.text()
        if resolution_x and resolution_y:
            format_options["resolution"] = f"{resolution_x}x{resolution_y}"

        # 帧率
        fps = self.fps_spin.value()
        if fps > 1:
            format_options["fps"] = fps

        # 执行处理
        self._execute_processing_task(
            self.processor.convert_format,
            input_file,
            output_file,
            format_options
        )

    def _clip_video(self, input_file, output_file) -> None:
        """剪辑视频"""
        # 获取开始时间和持续时间
        start_time = self.start_time_edit.time().toString("HH:mm:ss")
        end_time = self.end_time_edit.time().toString("HH:mm:ss")

        # 计算持续时间
        start_time_obj = self.start_time_edit.time()
        end_time_obj = self.end_time_edit.time()

        start_seconds = start_time_obj.hour() * 3600 + start_time_obj.minute() * \
            60 + start_time_obj.second()
        end_seconds = end_time_obj.hour() * 3600 + end_time_obj.minute() * \
            60 + end_time_obj.second()

        duration_seconds = max(0, end_seconds - start_seconds)
        duration = self._format_time_for_ffmpeg(
            QTime(0, 0, 0).addSecs(duration_seconds))

        # 获取是否保持原始编码
        keep_codec = self.keep_codec_check.isChecked()

        # 执行处理
        self._execute_processing_task(
            self.processor.clip_video,
            input_file,
            output_file,
            start_time=start_time,
            duration=duration,
            keep_codec=keep_codec
        )

    def _extract_audio(self, input_file, output_file) -> None:
        """提取音频"""
        # 获取音频格式
        audio_format = self.audio_format_combo.currentText().lower()

        # 获取音频质量
        quality_value = self.audio_quality_slider.value()
        audio_bitrate = None

        # 根据质量设置比特率
        if audio_format in ["mp3", "aac"]:
            bitrates = ["64k", "128k", "192k", "256k", "320k"]
            audio_bitrate = bitrates[quality_value]

        # 执行处理
        self._execute_processing_task(
            self.processor.extract_audio,
            input_file,
            output_file,
            audio_format=audio_format,
            audio_bitrate=audio_bitrate
        )

    def _compress_video(self, input_file, output_file) -> None:
        """压缩视频"""
        # 确定是按质量还是按大小
        is_quality = self.quality_radio.isChecked()

        if is_quality:
            # 按质量压缩
            quality = self.quality_slider.value()

            # 执行处理
            self._execute_processing_task(
                self.processor.compress_video,
                input_file,
                output_file,
                quality=quality
            )
        else:
            # 按大小压缩
            target_size = self.target_size_spin.value()

            # 执行处理
            self._execute_processing_task(
                self.processor.compress_video,
                input_file,
                output_file,
                target_size_mb=target_size
            )

    def _execute_processing_task(self, func, *args, **kwargs) -> None:
        """执行处理任务"""
        # 使用QTimer让UI有机会更新
        QTimer.singleShot(
            100, lambda: self._do_execute_task(func, *args, **kwargs))

    def _do_execute_task(self, func, *args, **kwargs) -> None:
        """实际执行任务"""
        try:
            # 调用处理函数
            result = func(*args, **kwargs)

            # 更新UI
            if self.progress_bar:
                self.progress_bar.setRange(0, 100)

            if result["success"]:
                # 处理成功
                if self.progress_bar:
                    self.progress_bar.setValue(100)
                    self.progress_bar.setFormat("处理完成 (100%)")

                # 发出成功信号
                output_file = args[1] if len(args) > 1 else ""
                self.processing_completed.emit(True, f"处理成功: {output_file}")

                # 显示成功消息
                InfoBar.success(
                    title="处理成功",
                    content=f"文件已保存至: {os.path.basename(output_file)}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

                # 关闭对话框
                QTimer.singleShot(1500, self.accept)
            else:
                # 处理失败
                if self.progress_bar:
                    self.progress_bar.setValue(0)
                    self.progress_bar.setFormat("处理失败")

                # 显示错误
                InfoBar.error(
                    title="处理失败",
                    content=f"错误: {result['error']}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )

                # 发出失败信号
                self.processing_completed.emit(
                    False, f"处理失败: {result['error']}")

                # 恢复UI
                self._enable_ui()

        except Exception as e:
            # 发生异常
            logger.error(f"处理出错: {e}")

            # 显示错误
            InfoBar.error(
                title="处理出错",
                content=f"发生异常: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

            # 发出失败信号
            self.processing_completed.emit(
                False, f"处理出错: {str(e)}")            # 恢复UI
            self._enable_ui()

    def _disable_ui(self) -> None:
        """禁用UI"""
        self.input_file_input.setEnabled(False)
        self.output_file_input.setEnabled(False)
        self.browse_input_button.setEnabled(False)
        self.browse_output_button.setEnabled(False)
        self.pivot.setEnabled(False)
        self.process_button.setEnabled(False)
        self.cancel_button.setText("取消处理")

    def _enable_ui(self) -> None:
        """启用UI"""
        self.input_file_input.setEnabled(True)
        self.output_file_input.setEnabled(True)
        self.browse_input_button.setEnabled(True)
        self.browse_output_button.setEnabled(True)
        self.pivot.setEnabled(True)
        self.process_button.setEnabled(True)
        self.cancel_button.setText("取消")
        if self.progress_bar:
            self.progress_bar.setVisible(False)

    def _format_time_for_ffmpeg(self, time) -> None:
        """将QTime格式化为FFmpeg可用的时间格式"""
        return time.toString("HH:mm:ss")

from PySide6.QtWidgets import (
    QWidget, QFormLayout
)
from PySide6.QtCore import Signal, Slot
from qfluentwidgets import (
    ComboBox, SpinBox
)


class EncodingSettingsWidget(QWidget):
    """编码设置组件，用于管理视频和音频编码参数"""

    # 设置变更信号
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建编码设置界面"""
        # 编码设置布局
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # 视频设置
        self.video_codec_combo = ComboBox()
        self.video_codec_combo.addItems(
            ["copy", "libx264", "libx265", "h264_nvenc", "hevc_nvenc"])
        self.video_codec_combo.currentIndexChanged.connect(
            lambda: self.settings_changed.emit())
        layout.addRow("视频编码:", self.video_codec_combo)

        # 视频质量
        self.video_quality_combo = ComboBox()
        self.video_quality_combo.addItems(["高", "中", "低", "自定义"])
        self.video_quality_combo.currentIndexChanged.connect(
            self._on_quality_changed)
        layout.addRow("视频质量:", self.video_quality_combo)

        # 自定义码率
        self.bitrate_spin = SpinBox()
        self.bitrate_spin.setRange(500, 20000)
        self.bitrate_spin.setValue(2000)
        self.bitrate_spin.setSuffix(" kbps")
        self.bitrate_spin.setEnabled(False)
        self.bitrate_spin.valueChanged.connect(
            lambda: self.settings_changed.emit())
        layout.addRow("自定义码率:", self.bitrate_spin)

        # 音频设置
        self.audio_codec_combo = ComboBox()
        self.audio_codec_combo.addItems(["copy", "aac", "mp3", "opus"])
        self.audio_codec_combo.currentIndexChanged.connect(
            lambda: self.settings_changed.emit())
        layout.addRow("音频编码:", self.audio_codec_combo)

    @Slot(int)
    def _on_quality_changed(self, index):
        """处理质量选择变化"""
        # 仅对自定义质量启用码率设置
        self.bitrate_spin.setEnabled(index == 3)  # 自定义选项
        self.settings_changed.emit()

    def get_video_codec(self):
        """获取视频编码设置"""
        return self.video_codec_combo.currentText()

    def get_audio_codec(self):
        """获取音频编码设置"""
        return self.audio_codec_combo.currentText()

    def get_quality_settings(self):
        """获取质量设置"""
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

        return {
            "quality": quality,
            "bitrate": bitrate
        }

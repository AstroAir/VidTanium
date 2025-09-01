from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QFormLayout, QFileDialog
)
from PySide6.QtCore import Signal
from typing import Optional
from qfluentwidgets import (
    PushButton, ComboBox, LineEdit, CheckBox, FluentIcon as FIF
)


class OutputSettingsWidget(QWidget):
    """输出设置组件，用于管理转换输出参数"""

    # 设置变更信号
    settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建输出设置界面"""
        # 输出设置布局
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # 输出格式
        self.format_combo = ComboBox()
        self.format_combo.addItems(["MP4", "MKV", "AVI", "MOV", "FLV", "WebM"])
        self.format_combo.currentIndexChanged.connect(
            lambda: self.settings_changed.emit())
        layout.addRow("输出格式:", self.format_combo)

        # 输出目录
        output_layout = QHBoxLayout()
        self.output_dir_input = LineEdit()
        self.output_dir_input.setPlaceholderText("与输入文件相同目录")
        self.output_dir_input.textChanged.connect(
            lambda: self.settings_changed.emit())
        output_layout.addWidget(self.output_dir_input, 1)

        self.browse_output_button = PushButton("浏览...")
        self.browse_output_button.setIcon(FIF.FOLDER)
        self.browse_output_button.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self.browse_output_button)

        layout.addRow("输出目录:", output_layout)

        # 分辨率
        self.resolution_combo = ComboBox()
        self.resolution_combo.addItems(["原始", "1080p", "720p", "480p", "360p"])
        self.resolution_combo.currentIndexChanged.connect(
            lambda: self.settings_changed.emit())
        layout.addRow("分辨率:", self.resolution_combo)

        # 其他选项
        self.keep_original_check = CheckBox("保留原始文件")
        self.keep_original_check.clicked.connect(
            lambda: self.settings_changed.emit())
        layout.addRow("", self.keep_original_check)

    def _browse_output_dir(self):
        """浏览输出目录"""
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录"
        )

        if output_dir:
            self.output_dir_input.setText(output_dir)
            self.settings_changed.emit()

    def set_output_directory(self, directory: str):
        """设置输出目录"""
        self.output_dir_input.setText(directory)

    def get_output_format(self) -> str:
        """获取输出格式"""
        return str(self.format_combo.currentText()).lower()

    def get_output_directory(self) -> str:
        """获取输出目录"""
        return str(self.output_dir_input.text())

    def get_resolution(self) -> str:
        """获取分辨率设置"""
        return str(self.resolution_combo.currentText())

    def get_keep_original(self) -> bool:
        """获取是否保留原始文件设置"""
        return bool(self.keep_original_check.isChecked())

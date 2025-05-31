"""文件导入选项卡"""
import os
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QFormLayout
from PySide6.QtCore import Qt, Signal
from typing import Optional, List

from qfluentwidgets import (  # type: ignore
    PushButton, LineEdit, CardWidget, BodyLabel, StrongBodyLabel, FluentIcon, InfoBarPosition, InfoBar
)

from src.core.url_extractor import URLExtractor


class FileInputTab(QWidget):
    """文件导入选项卡"""

    # 提取URL信号
    urls_extracted = Signal(list)  # 或者更精确地使用 Signal(List[str])

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 说明文本
        hint_label = BodyLabel("从文本文件导入URL:")  # type: ignore
        layout.addWidget(hint_label)

        # 文件选择
        file_card = CardWidget(self)  # type: ignore
        file_card_layout = QVBoxLayout(file_card)
        file_card_layout.setContentsMargins(15, 15, 15, 15)
        file_card_layout.setSpacing(10)

        file_layout = QHBoxLayout()

        self.file_path_input = LineEdit()  # type: ignore
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("选择文件...")
        file_layout.addWidget(self.file_path_input)

        self.browse_button = PushButton("浏览...")  # type: ignore
        self.browse_button.setIcon(FluentIcon.FOLDER)  # type: ignore
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)

        file_card_layout.addLayout(file_layout)

        # 加载按钮
        self.load_file_button = PushButton("加载文件")  # type: ignore
        self.load_file_button.setIcon(FluentIcon.DOCUMENT)  # type: ignore
        self.load_file_button.setEnabled(False)
        self.load_file_button.clicked.connect(self._load_file)
        file_card_layout.addWidget(self.load_file_button)

        layout.addWidget(file_card)

        # 选项
        options_card = CardWidget(self)  # type: ignore
        options_layout = QFormLayout(options_card)
        options_layout.setContentsMargins(15, 10, 15, 10)
        options_layout.setSpacing(10)

        # 标题
        options_title = StrongBodyLabel("过滤选项")  # type: ignore
        options_layout.addRow(options_title)

        # 正则表达式过滤
        self.file_regex_input = LineEdit()  # type: ignore
        self.file_regex_input.setPlaceholderText("例如: .*\\.mp4|.*\\.m3u8")
        options_layout.addRow("正则表达式过滤:", self.file_regex_input)

        layout.addWidget(options_card)
        layout.addStretch()

    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文本文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            self.file_path_input.setText(file_path)
            self.load_file_button.setEnabled(True)

    def _load_file(self):
        """加载文件"""
        file_path: str = self.file_path_input.text()
        if not file_path or not os.path.exists(file_path):
            return

        pattern_text: str = self.file_regex_input.text()
        pattern: Optional[str] = pattern_text if pattern_text else None

        try:
            urls: List[str] = URLExtractor.extract_urls_from_file(
                file_path, pattern)
            self.urls_extracted.emit(urls)

            InfoBar.success(  # type: ignore
                title="加载成功",
                content=f"从文件中提取了 {len(urls)} 个URL",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,  # type: ignore
                duration=2000,
                parent=self
            )
        except Exception as e:
            InfoBar.error(  # type: ignore
                title="加载失败",
                content=f"加载文件出错: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,  # type: ignore
                duration=3000,
                parent=self
            )

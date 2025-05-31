"""文本输入选项卡"""
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QFormLayout, QApplication
from PySide6.QtCore import Qt, Signal
# QIcon is not used in this file, so it can be removed if not needed elsewhere implicitly
# from PySide6.QtGui import QIcon
from typing import Optional, List  # Added List for type hinting

from qfluentwidgets import (  # type: ignore
    PushButton, LineEdit, CardWidget, BodyLabel,
    TextEdit, FluentIcon, InfoBarPosition, InfoBar,
    StrongBodyLabel
)

from src.core.url_extractor import URLExtractor


class TextInputTab(QWidget):
    """文本输入选项卡"""

    # 提取URL信号
    # Consider using Signal(List[str]) after importing List
    urls_extracted = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 说明文本
        hint_label = BodyLabel("请输入要导入的URL，每行一个:")  # type: ignore
        layout.addWidget(hint_label)

        # 文本输入区域
        self.text_input = TextEdit()  # type: ignore
        self.text_input.setPlaceholderText("在此粘贴URL...")
        self.text_input.textChanged.connect(self._process_text_input)
        layout.addWidget(self.text_input)

        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 5, 0, 5)

        self.paste_button = PushButton("从剪贴板粘贴")  # type: ignore
        self.paste_button.setIcon(FluentIcon.COPY)  # type: ignore
        self.paste_button.clicked.connect(self._paste_from_clipboard)
        buttons_layout.addWidget(self.paste_button)

        self.clear_button = PushButton("清空")  # type: ignore
        self.clear_button.setIcon(FluentIcon.DELETE)  # type: ignore
        self.clear_button.clicked.connect(self._clear_text)
        buttons_layout.addWidget(self.clear_button)

        layout.addLayout(buttons_layout)

        # 选项
        options_card = CardWidget(self)  # type: ignore
        options_layout = QFormLayout(options_card)
        options_layout.setContentsMargins(15, 10, 15, 10)
        options_layout.setSpacing(10)

        # 正则表达式过滤
        options_title = StrongBodyLabel("过滤选项")  # type: ignore
        options_layout.addRow(options_title)

        self.regex_input = LineEdit()  # type: ignore
        self.regex_input.setPlaceholderText("例如: .*\\.mp4|.*\\.m3u8")
        self.regex_input.textChanged.connect(self._process_text_input)
        options_layout.addRow("正则表达式过滤:", self.regex_input)

        layout.addWidget(options_card)

    def _paste_from_clipboard(self):
        """从剪贴板粘贴"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.text_input.setText(text)
            InfoBar.success(  # type: ignore
                title="粘贴成功",
                content="已从剪贴板粘贴文本",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,  # type: ignore
                duration=2000,
                parent=self
            )
        else:
            InfoBar.warning(  # type: ignore
                title="粘贴失败",
                content="剪贴板中没有文本内容",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,  # type: ignore
                duration=2000,
                parent=self
            )

    def _clear_text(self):
        """清空文本框"""
        self.text_input.clear()
        self._process_text_input()

        InfoBar.success(  # type: ignore
            title="已清空",
            content="文本框内容已清空",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,  # type: ignore
            duration=2000,
            parent=self
        )

    def _process_text_input(self):
        """处理文本输入"""
        text: str = self.text_input.toPlainText()
        pattern_text: str = self.regex_input.text()
        pattern: Optional[str] = pattern_text if pattern_text else None

        urls: List[str] = URLExtractor.extract_urls_from_text(text, pattern)
        self.urls_extracted.emit(urls)

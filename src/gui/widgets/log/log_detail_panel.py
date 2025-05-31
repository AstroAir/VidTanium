"""
日志详情面板组件

显示单条日志的详细信息
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QSize

from qfluentwidgets import (
    TextEdit, CardWidget, StrongBodyLabel,
    ToolButton, FluentIcon
)


class LogDetailPanel(CardWidget):
    """日志详情面板组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 标题栏
        header_layout = QHBoxLayout()
        self.detail_title = StrongBodyLabel("日志详情", self)
        header_layout.addWidget(self.detail_title)

        # 关闭按钮
        self.close_detail_btn = ToolButton(FluentIcon.CLOSE, self)
        self.close_detail_btn.setIconSize(QSize(12, 12))
        self.close_detail_btn.setToolTip("关闭详情面板")
        self.close_detail_btn.clicked.connect(lambda: self.setVisible(False))
        header_layout.addWidget(self.close_detail_btn)

        layout.addLayout(header_layout)

        # 详情内容
        self.detail_text = TextEdit(self)
        self.detail_text.setReadOnly(True)
        layout.addWidget(self.detail_text)

        self._apply_styles()

    def _apply_styles(self):
        """应用样式"""
        self.detail_text.setStyleSheet("""
            TextEdit {
                border: none;
                background-color: #f8f8f8;
            }
        """)

    def set_word_wrap(self, enabled):
        """设置自动换行"""
        from PySide6.QtGui import QTextOption
        mode = QTextOption.WrapMode.WordWrap if enabled else QTextOption.WrapMode.NoWrap
        self.detail_text.setWordWrapMode(mode)

    def set_font(self, font):
        """设置字体"""
        self.detail_text.setFont(font)

    def set_log_details(self, log_entry):
        """
        显示日志详情

        Args:
            log_entry: LogEntry对象
        """
        # 构建详情文本
        details = (
            f"时间: {log_entry.timestamp_str}\n"
            f"级别: {log_entry.level.upper()}\n"
            f"信息: {log_entry.message}\n\n"
        )

        if log_entry.details:
            details += f"详细信息:\n{log_entry.details}\n"

        self.detail_text.setPlainText(details)

    def clear(self):
        """清空详情"""
        self.detail_text.clear()

"""
日志过滤栏组件

提供日志搜索和过滤功能
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal

from qfluentwidgets import ComboBox, SearchLineEdit


class LogFilterBar(QWidget):
    """日志过滤栏组件"""

    # 信号定义
    filterChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)

        # 搜索框
        self.search_input = SearchLineEdit(self)
        self.search_input.setPlaceholderText("搜索日志...")
        self.search_input.textChanged.connect(self.filterChanged.emit)
        layout.addWidget(self.search_input, 3)

        # 日志级别过滤
        layout.addWidget(QLabel("显示级别:"), 0)
        self.level_combo = ComboBox(self)
        self.level_combo.addItems(["全部", "仅错误", "仅警告", "仅信息", "无错误"])
        self.level_combo.setToolTip("选择要显示的日志级别")
        self.level_combo.currentIndexChanged.connect(self.filterChanged.emit)
        layout.addWidget(self.level_combo, 1)

        # 日期过滤
        layout.addWidget(QLabel("时间段:"), 0)
        self.date_combo = ComboBox(self)
        self.date_combo.addItems(["全部", "今天", "一小时内", "十分钟内"])
        self.date_combo.currentIndexChanged.connect(self.filterChanged.emit)
        layout.addWidget(self.date_combo, 1)

    def get_search_text(self):
        """获取搜索文本"""
        return self.search_input.text()

    def get_level_filter(self):
        """获取级别过滤器索引"""
        return self.level_combo.currentIndex()

    def get_date_filter(self):
        """获取日期过滤器索引"""
        return self.date_combo.currentIndex()

    def reset_filters(self):
        """重置所有过滤器"""
        self.search_input.clear()
        self.level_combo.setCurrentIndex(0)
        self.date_combo.setCurrentIndex(0)

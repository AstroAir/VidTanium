from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat

from qfluentwidgets import (
    TextEdit, PushButton, ComboBox, CheckBox, 
    FluentIcon, CardWidget, StrongBodyLabel, BodyLabel,
    TransparentDropDownToolButton, FluentStyleSheet
)

class LogViewer(QWidget):
    """日志查看器组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)  # 减小间距

        # 控制栏 - 使用更现代的设计
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 6)
        
        # 设置按钮样式
        btn_style = """
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                border: 1px solid #d0d0d0;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """
        
        # 日志操作按钮
        self.clear_button = PushButton("清空日志")
        self.clear_button.setStyleSheet(btn_style)
        self.clear_button.setToolTip("清空当前所有日志")
        self.clear_button.clicked.connect(self._clear_logs)
        controls_layout.addWidget(self.clear_button)

        self.save_button = PushButton("保存日志")
        self.save_button.setStyleSheet(btn_style)
        self.save_button.setToolTip("将日志保存到文件")
        self.save_button.clicked.connect(self._save_logs)
        controls_layout.addWidget(self.save_button)
        
        # 增加过滤功能

        controls_layout.addSpacing(20)
        
        # 日志级别过滤
        controls_layout.addWidget(QLabel("显示级别:"))
        self.level_combo = ComboBox()
        self.level_combo.addItems(["全部", "仅错误", "无错误"])
        self.level_combo.setToolTip("选择要显示的日志级别")
        self.level_combo.currentIndexChanged.connect(self._filter_logs)
        controls_layout.addWidget(self.level_combo)
        
        controls_layout.addSpacing(20)
        
        # 自动滚动复选框
        self.auto_scroll = CheckBox("自动滚动")
        self.auto_scroll.setChecked(True)
        self.auto_scroll.setToolTip("新日志出现时自动滚动到底部")
        controls_layout.addWidget(self.auto_scroll)
        
        # 右侧弹簧
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # 日志文本框 - 使用更易读的配色和字体
        self.log_text = TextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.document().setMaximumBlockCount(1000)  # 限制最大行数
        
        # 设置适合阅读的字体和样式
        from PySide6.QtGui import QFont
        log_font = QFont()
        log_font.setFamily("Consolas")  # 使用等宽字体更适合显示日志
        log_font.setPointSize(9)
        self.log_text.setFont(log_font)
        
        # 设置文本编辑框样式
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)
        
        layout.addWidget(self.log_text)
        
        # 初始化日志存储
        self.log_entries = []  # 存储所有日志以便过滤

    def add_log_entry(self, message, error=False):
        """添加日志条目"""
        # 存储日志条目供过滤使用
        self.log_entries.append({"message": message, "error": error})
        
        # 应用当前过滤器
        self._apply_filter()
        
    def _apply_filter(self):
        """应用当前过滤器并更新显示"""
        # 清空当前显示
        self.log_text.clear()
        
        # 获取当前过滤设置
        filter_index = self.level_combo.currentIndex() if hasattr(self, 'level_combo') else 0
        
        # 创建文本格式
        from PySide6.QtGui import QTextCharFormat
        normal_format = QTextCharFormat()
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(200, 0, 0))
        
        # 添加符合过滤条件的日志
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        for entry in self.log_entries:
            # 根据过滤器决定是否显示
            if (filter_index == 0 or  # 全部
                (filter_index == 1 and entry["error"]) or  # 仅错误
                (filter_index == 2 and not entry["error"])):  # 无错误
                
                format = error_format if entry["error"] else normal_format
                cursor.insertText(entry["message"] + "\n", format)
        
        # 根据设置是否滚动到底部
        if hasattr(self, 'auto_scroll') and self.auto_scroll.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def _filter_logs(self):
        """过滤日志显示"""
        self._apply_filter()

    def _clear_logs(self):
        """清空日志"""
        self.log_text.clear()
        self.log_entries.clear()

    def _save_logs(self):
        """保存日志到文件"""
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime
        import os

        # 生成默认文件名，包含当前日期时间
        default_name = f"vidtanium_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存日志文件", 
            os.path.join(os.path.expanduser("~"), default_name),
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.add_log_entry(f"日志已保存到: {filename}")
            except Exception as e:
                self.add_log_entry(f"保存日志失败: {e}", error=True)

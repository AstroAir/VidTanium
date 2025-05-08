"""
日志查看器主组件

集成所有日志子组件，提供完整的日志查看功能
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QMenu
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QTextCharFormat, QColor, QFont, QTextOption, QTextCursor

from qfluentwidgets import TextEdit, CheckBox, CardWidget, FluentIcon

import os
import re
from datetime import datetime

from .log_entry import LogEntry
from .log_detail_panel import LogDetailPanel
from .log_toolbar import LogToolbar
from .log_filter_bar import LogFilterBar


class LogViewer(QWidget):
    """日志查看器组件"""
    
    # 信号定义
    logCleared = Signal()
    logSaved = Signal(str)  # 传递保存的文件路径
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_entries = []  # 存储所有日志
        self.filtered_entries = []  # 存储过滤后的日志
        self.max_log_entries = 5000  # 最大日志条目数
        self.auto_cleanup_timer = None  # 自动清理定时器
        self._create_ui()
        self._setup_auto_cleanup()
        self._connect_signals()
        
    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 顶部工具栏
        self.toolbar = LogToolbar(self)
        layout.addWidget(self.toolbar)
        
        # 搜索和过滤区域
        self.filter_bar = LogFilterBar(self)
        layout.addWidget(self.filter_bar)
        
        # 主分割视图：日志文本 + 详情面板
        self.splitter = QSplitter(Qt.Vertical, self)
        
        # 日志文本框
        self.log_card = CardWidget(self)
        log_layout = QVBoxLayout(self.log_card)
        log_layout.setContentsMargins(8, 8, 8, 8)
        log_layout.setSpacing(0)
        
        self.log_text = TextEdit(self.log_card)
        self.log_text.setReadOnly(True)
        self.log_text.document().setMaximumBlockCount(self.max_log_entries)
        
        # 设置适合阅读的字体和样式
        log_font = QFont("Consolas", 9)
        self.log_text.setFont(log_font)
        self.log_text.setWordWrapMode(QTextOption.NoWrap)  # 禁用自动换行
        
        # 右键菜单
        self.log_text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.log_text.customContextMenuRequested.connect(self._show_context_menu)
        
        log_layout.addWidget(self.log_text)
        
        self.splitter.addWidget(self.log_card)
        
        # 详情面板
        self.detail_panel = LogDetailPanel(self)
        self.detail_panel.set_font(QFont("Consolas", 9))
        self.splitter.addWidget(self.detail_panel)
        self.splitter.setStretchFactor(0, 3)  # 日志区域占比更大
        self.splitter.setStretchFactor(1, 1)
        
        # 默认隐藏详情面板
        self.detail_panel.setVisible(False)
        
        layout.addWidget(self.splitter)
        
        # 状态栏
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(4, 2, 4, 2)
        
        self.status_label = QLabel("日志条目: 0")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.auto_scroll = CheckBox("自动滚动")
        self.auto_scroll.setChecked(True)
        self.auto_scroll.setToolTip("新日志出现时自动滚动到底部")
        status_layout.addWidget(self.auto_scroll)
        
        self.wrap_text = CheckBox("自动换行")
        self.wrap_text.setChecked(False)
        self.wrap_text.toggled.connect(self._toggle_word_wrap)
        status_layout.addWidget(self.wrap_text)
        
        layout.addLayout(status_layout)
        
        # 设置样式
        self._apply_styles()
        
    def _connect_signals(self):
        """连接信号槽"""
        # 过滤栏
        self.filter_bar.filterChanged.connect(self._filter_logs)
        
        # 工具栏
        self.toolbar.clearRequested.connect(self._clear_logs)
        self.toolbar.saveRequested.connect(self._save_logs)
        self.toolbar.copyRequested.connect(self._copy_selected)
        self.toolbar.selectAllRequested.connect(self.log_text.selectAll)
        self.toolbar.detailPanelToggled.connect(self._toggle_detail_panel)
        self.toolbar.exportHtmlRequested.connect(self._export_html)
        self.toolbar.autoCleanToggled.connect(self._toggle_auto_cleanup)
        self.toolbar.zoomInRequested.connect(self._zoom_in)
        self.toolbar.zoomOutRequested.connect(self._zoom_out)
        
    def _apply_styles(self):
        """应用样式"""
        # 设置日志文本框样式
        self.log_text.setStyleSheet("""
            TextEdit {
                border: none;
                background-color: #f8f8f8;
            }
        """)
        
    def _setup_auto_cleanup(self):
        """设置自动清理"""
        self.auto_cleanup_timer = QTimer(self)
        self.auto_cleanup_timer.timeout.connect(self._perform_auto_cleanup)
        self.auto_cleanup_timer.start(60 * 1000)  # 每分钟检查一次
        
    def _perform_auto_cleanup(self):
        """执行自动清理"""
        if not self.toolbar.auto_clean_action.isChecked():
            return
            
        # 如果日志条目超过最大值的80%，则清理最旧的20%
        if len(self.log_entries) > self.max_log_entries * 0.8:
            entries_to_remove = int(len(self.log_entries) * 0.2)
            self.log_entries = self.log_entries[entries_to_remove:]
            self._filter_logs()  # 重新应用过滤器
            self.add_log_entry(f"已自动清理 {entries_to_remove} 条旧日志...", level="info")
            
    def _toggle_auto_cleanup(self, checked):
        """开关自动清理"""
        if checked and not self.auto_cleanup_timer.isActive():
            self.auto_cleanup_timer.start(60 * 1000)
            self.add_log_entry("已启用日志自动清理功能", level="info")
        elif not checked and self.auto_cleanup_timer.isActive():
            self.auto_cleanup_timer.stop()
            self.add_log_entry("已禁用日志自动清理功能", level="info")
            
    def _toggle_word_wrap(self, checked):
        """切换自动换行"""
        self.log_text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere if checked else QTextOption.NoWrap)
        self.detail_panel.set_word_wrap(checked)
        
    def _toggle_detail_panel(self, visible):
        """切换详情面板显示"""
        self.detail_panel.setVisible(visible)
        
    def _zoom_in(self):
        """放大字体"""
        self._zoom_text(1.1)
        
    def _zoom_out(self):
        """缩小字体"""
        self._zoom_text(0.9)
        
    def _zoom_text(self, factor):
        """调整文本大小"""
        font = self.log_text.font()
        new_size = max(7, int(font.pointSize() * factor))
        font.setPointSize(new_size)
        self.log_text.setFont(font)
        self.detail_panel.set_font(font)

    def add_log_entry(self, message, level="info", details=None, timestamp=None):
        """
        添加日志条目
        level: 'info', 'warning', 'error'
        """
        # 创建日志条目对象
        entry = LogEntry(message, level, details, timestamp)
        
        # 添加到日志列表
        self.log_entries.append(entry)
        
        # 如果超过最大条目数，移除最老的
        if len(self.log_entries) > self.max_log_entries:
            self.log_entries.pop(0)
        
        # 应用过滤器
        self._filter_logs()
        
        # 更新状态栏
        self.status_label.setText(f"日志条目: {len(self.log_entries)}")
        
    def _filter_logs(self):
        """过滤日志显示"""
        # 获取过滤条件
        search_text = self.filter_bar.get_search_text().lower() 
        level_filter = self.filter_bar.get_level_filter()
        date_filter = self.filter_bar.get_date_filter()
        
        # 过滤日志
        self.filtered_entries = []
        for entry in self.log_entries:
            # 搜索文本过滤
            if not entry.matches_search(search_text):
                continue
                
            # 级别过滤
            if not entry.matches_level_filter(level_filter):
                continue
                
            # 时间过滤
            if not entry.matches_date_filter(date_filter):
                continue
                
            # 通过所有过滤条件
            self.filtered_entries.append(entry)
        
        # 更新显示
        self._update_log_display()
        
    def _update_log_display(self):
        """更新日志显示"""
        # 保存当前滚动位置
        scrollbar = self.log_text.verticalScrollBar()
        previous_pos = scrollbar.value()
        at_bottom = previous_pos == scrollbar.maximum()
        
        self.log_text.clear()
        
        # 创建文本格式
        info_format = QTextCharFormat()
        info_format.setForeground(QColor(0, 0, 0))  # 黑色
        
        warning_format = QTextCharFormat()
        warning_format.setForeground(QColor(180, 90, 0))  # 橙色
        
        error_format = QTextCharFormat()
        error_format.setForeground(QColor(200, 0, 0))  # 红色
        
        # 添加日志
        cursor = self.log_text.textCursor()
        for entry in self.filtered_entries:
            if entry.level == "error":
                format = error_format
            elif entry.level == "warning":
                format = warning_format
            else:
                format = info_format
                
            cursor.insertText(entry.display_text + "\n", format)
        
        # 恢复滚动位置或滚动到底部
        if self.auto_scroll.isChecked() or at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(min(previous_pos, scrollbar.maximum()))
            
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 添加菜单项
        copy_action = menu.addAction(FluentIcon.COPY.icon(), "复制")
        copy_action.triggered.connect(self._copy_selected)
        
        if self.log_text.textCursor().hasSelection():
            show_details_action = menu.addAction(FluentIcon.INFO.icon(), "显示详情")
            show_details_action.triggered.connect(self._show_selected_details)
            
        menu.addSeparator()
        
        menu.addAction(self.toolbar.clear_action)
        menu.addAction(self.toolbar.save_action)
        
        # 显示菜单
        menu.exec(self.log_text.mapToGlobal(pos))
        
    def _copy_selected(self):
        """复制选中文本"""
        self.log_text.copy()
        
    def _show_selected_details(self):
        """显示选中日志的详细信息"""
        selected_text = self.log_text.textCursor().selectedText()
        if not selected_text:
            return
            
        # 尝试提取时间戳和级别以识别日志条目
        match = re.search(r'\[([\d\-\s:]+)\]\s+\[([A-Z]+)\]', selected_text)
        if match:
            timestamp_str = match.group(1)
            level = match.group(2)
            
            # 查找对应的日志条目
            for entry in self.log_entries:
                if entry.timestamp_str in timestamp_str and entry.level.upper() == level.upper():
                    # 显示详情
                    self.detail_panel.setVisible(True)
                    self.toolbar.set_detail_panel_visible(True)
                    self.detail_panel.set_log_details(entry)
                    break
                    
    def _clear_logs(self):
        """清空日志"""
        self.log_text.clear()
        self.log_entries.clear()
        self.filtered_entries.clear()
        self.status_label.setText("日志条目: 0")
        self.detail_panel.setVisible(False)
        self.toolbar.set_detail_panel_visible(False)
        self.detail_panel.clear()
        self.logCleared.emit()

    def _save_logs(self, filename):
        """保存日志到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # 写入所有过滤后的日志
                for entry in self.filtered_entries:
                    f.write(entry.display_text + "\n")
                    
            self.add_log_entry(f"日志已保存到: {filename}", level="info")
            self.logSaved.emit(filename)
        except Exception as e:
            self.add_log_entry(f"保存日志失败: {e}", level="error")
                
    def _export_html(self, filename):
        """导出日志为HTML格式"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # 写入HTML头
                f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>VidTanium 日志</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .log { margin-bottom: 2px; font-family: Consolas, monospace; }
        .info { color: black; }
        .warning { color: #b45a00; }
        .error { color: #c80000; }
        h1 { color: #333; }
        .summary { background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>VidTanium 日志导出</h1>
    <div class="summary">
        <p>导出时间: %s</p>
        <p>日志条目数: %d</p>
    </div>
""" % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), len(self.filtered_entries)))
                
                # 写入日志条目
                for entry in self.filtered_entries:
                    css_class = entry.level
                    f.write(f'<div class="log {css_class}">{entry.display_text}</div>\n')
                    
                # 写入HTML尾
                f.write("</body>\n</html>")
                
            self.add_log_entry(f"日志已导出为HTML: {filename}", level="info")
        except Exception as e:
            self.add_log_entry(f"导出HTML失败: {e}", level="error")
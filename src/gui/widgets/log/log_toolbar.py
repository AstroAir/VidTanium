"""
日志工具栏组件

提供日志操作的工具按钮
"""

from PySide6.QtWidgets import QToolBar, QFileDialog
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QAction

from qfluentwidgets import FluentIcon

import os
from datetime import datetime


class LogToolbar(QToolBar):
    """日志工具栏组件"""

    # 信号定义
    clearRequested = Signal()
    saveRequested = Signal(str)  # 保存文件路径
    copyRequested = Signal()
    selectAllRequested = Signal()
    detailPanelToggled = Signal(bool)
    exportHtmlRequested = Signal(str)  # 导出HTML文件路径
    autoCleanToggled = Signal(bool)
    zoomInRequested = Signal()
    zoomOutRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建工具栏界面"""
        self.setIconSize(QSize(16, 16))
        self.setMovable(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)

        # 清空日志
        self.clear_action = QAction(FluentIcon.DELETE.icon(), "清空日志", self)
        self.clear_action.setToolTip("清空当前所有日志")
        self.clear_action.triggered.connect(self.clearRequested.emit)
        self.addAction(self.clear_action)

        # 保存日志
        self.save_action = QAction(FluentIcon.SAVE.icon(), "保存日志", self)
        self.save_action.setToolTip("将日志保存到文件")
        self.save_action.triggered.connect(self._save_logs)
        self.addAction(self.save_action)

        self.addSeparator()

        # 复制选中
        self.copy_action = QAction(FluentIcon.COPY.icon(), "复制", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.setToolTip("复制选中的日志文本")
        self.copy_action.triggered.connect(self.copyRequested.emit)
        self.addAction(self.copy_action)

        # 全选
        self.select_all_action = QAction(FluentIcon.ACCEPT.icon(), "全选", self)
        self.select_all_action.setShortcut("Ctrl+A")
        self.select_all_action.triggered.connect(self.selectAllRequested.emit)
        self.addAction(self.select_all_action)

        self.addSeparator()

        # 显示详情
        self.detail_action = QAction(FluentIcon.INFO.icon(), "显示详情", self)
        self.detail_action.setCheckable(True)
        self.detail_action.setToolTip("显示或隐藏详情面板")
        self.detail_action.triggered.connect(self.detailPanelToggled.emit)
        self.addAction(self.detail_action)

        # 导出为HTML
        self.export_html_action = QAction(
            FluentIcon.DOCUMENT.icon(), "导出HTML", self)
        self.export_html_action.setToolTip("导出日志为HTML格式")
        self.export_html_action.triggered.connect(self._export_html)
        self.addAction(self.export_html_action)

        self.addSeparator()

        # 自动清理设置
        self.auto_clean_action = QAction(FluentIcon.BRUSH.icon(), "自动清理", self)
        self.auto_clean_action.setToolTip("设置自动清理选项")
        self.auto_clean_action.setCheckable(True)
        self.auto_clean_action.setChecked(True)
        self.auto_clean_action.triggered.connect(self.autoCleanToggled.emit)
        self.addAction(self.auto_clean_action)

        # 字体放大/缩小
        self.zoom_in_action = QAction(FluentIcon.ZOOM_IN.icon(), "放大", self)
        self.zoom_in_action.setToolTip("增大字体")
        self.zoom_in_action.triggered.connect(self.zoomInRequested.emit)
        self.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction(FluentIcon.ZOOM_OUT.icon(), "缩小", self)
        self.zoom_out_action.setToolTip("减小字体")
        self.zoom_out_action.triggered.connect(self.zoomOutRequested.emit)
        self.addAction(self.zoom_out_action)

        # 设置样式
        self._apply_styles()

    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QToolBar {
                border: none;
                background-color: transparent;
                spacing: 4px;
                padding: 2px;
            }
            QToolButton {
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
        """)

    def _save_logs(self):
        """保存日志到文件"""
        default_name = f"vidtanium_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        filename, _ = QFileDialog.getSaveFileName(
            self, "保存日志文件",
            os.path.join(os.path.expanduser("~"), default_name),
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if filename:
            self.saveRequested.emit(filename)

    def _export_html(self):
        """导出日志为HTML格式"""
        default_name = f"vidtanium_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        filename, _ = QFileDialog.getSaveFileName(
            self, "导出HTML日志",
            os.path.join(os.path.expanduser("~"), default_name),
            "HTML文件 (*.html);;所有文件 (*)"
        )

        if filename:
            self.exportHtmlRequested.emit(filename)

    def set_detail_panel_visible(self, visible):
        """设置详情面板可见状态"""
        self.detail_action.setChecked(visible)

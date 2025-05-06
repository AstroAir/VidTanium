import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMenu, QFrame, QLabel,
    QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QAction, QColor, QBrush, QFont

from qfluentwidgets import (
    PushButton, ToolButton, ProgressBar, InfoBar, InfoBarPosition,
    FluentIcon, StrongBodyLabel, BodyLabel, TransparentToolButton,
    FluentStyleSheet
)

from src.core.downloader import TaskStatus


class TaskManager(QWidget):
    """任务管理组件"""

    # 信号定义
    task_action_requested = Signal(str, str)  # 任务ID, 操作

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.tasks = {}
        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 8)
        toolbar_layout.setSpacing(8)

        # 新建任务按钮
        self.new_task_button = PushButton("新建任务")
        self.new_task_button.setIcon(FluentIcon.ADD)
        self.new_task_button.clicked.connect(self._on_new_task)
        toolbar_layout.addWidget(self.new_task_button)

        # 控制按钮
        self.start_all_button = PushButton("全部开始")
        self.start_all_button.setIcon(FluentIcon.PLAY)
        self.start_all_button.clicked.connect(self._on_start_all)
        toolbar_layout.addWidget(self.start_all_button)

        self.pause_all_button = PushButton("全部暂停")
        self.pause_all_button.setIcon(FluentIcon.PAUSE)
        self.pause_all_button.clicked.connect(self._on_pause_all)
        toolbar_layout.addWidget(self.pause_all_button)

        # 清理按钮
        self.clean_button = PushButton("清理已完成")
        self.clean_button.setIcon(FluentIcon.BROOM)
        self.clean_button.clicked.connect(self._on_clean)
        toolbar_layout.addWidget(self.clean_button)

        # 弹簧
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels(
            ["名称", "状态", "进度", "速度", "已完成/总计", "剩余时间", "操作"]
        )
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(
            self._show_context_menu)

        # 设置交替行颜色以提高可读性
        self.task_table.setAlternatingRowColors(True)

        # 设置表格样式 - 使用更现代的风格
        self.task_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                gridline-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f5f5f5;
            }
            QTableWidget::item:selected {
                background-color: #ecf6ff;
                color: black;
            }
            QHeaderView::section {
                background-color: #f8f8f8;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
                color: #505050;
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
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a0a0a0;
            }
        """)

        # 设置表格字体
        font = QFont()
        font.setPointSize(9)
        self.task_table.setFont(font)

        # 设置表格列宽
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 名称列可伸缩
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 进度条可手动调整
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # 固定操作列宽度

        # 预设一个合适的操作列宽度和进度条列宽度
        self.task_table.setColumnWidth(6, 180)
        self.task_table.setColumnWidth(2, 150)

        # 设置垂直标题不可见
        self.task_table.verticalHeader().setVisible(False)

        layout.addWidget(self.task_table)

        # 在没有任务时显示的提示信息
        self.empty_hint = BodyLabel("暂无下载任务，点击'新建任务'按钮开始下载")
        self.empty_hint.setAlignment(Qt.AlignCenter)
        self.empty_hint.setStyleSheet(
            "color: #808080; padding: 30px; font-size: 14px;")
        layout.addWidget(self.empty_hint)
        self.empty_hint.setVisible(False)  # 默认隐藏

    def update_tasks(self, tasks):
        """更新任务列表"""
        self.tasks = tasks
        self.task_table.setRowCount(0)

        # 检查是否有任务，如果没有则显示提示
        if not tasks:
            self.task_table.setVisible(False)
            self.empty_hint.setVisible(True)
            return
        else:
            self.task_table.setVisible(True)
            self.empty_hint.setVisible(False)

        for i, (task_id, task) in enumerate(tasks.items()):
            self.task_table.insertRow(i)

            # 名称
            name_item = QTableWidgetItem(task.name)
            name_item.setData(Qt.UserRole, task_id)
            self.task_table.setItem(i, 0, name_item)

            # 状态
            status_item = QTableWidgetItem(self._get_status_text(task.status))
            status_item.setForeground(self._get_status_color(task.status))
            self.task_table.setItem(i, 1, status_item)

            # 进度
            progress_widget = ProgressBar()
            progress_widget.setMinimum(0)
            progress_widget.setMaximum(100)
            progress_widget.setValue(int(task.get_progress_percentage()))
            progress_widget.setFormat("%p%")

            # 设置进度条样式
            progress_style = """
                QProgressBar {
                    border: 1px solid #d0d0d0;
                    border-radius: 2px;
                    text-align: center;
                    height: 18px;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 1px;
                }
            """

            # 根据任务状态调整进度条颜色
            if task.status == TaskStatus.PAUSED:
                progress_style = progress_style.replace(
                    "background-color: #0078d4;",
                    "background-color: #ff9500;"
                )
            elif task.status == TaskStatus.COMPLETED:
                progress_style = progress_style.replace(
                    "background-color: #0078d4;",
                    "background-color: #107c10;"
                )
            elif task.status == TaskStatus.FAILED:
                progress_style = progress_style.replace(
                    "background-color: #0078d4;",
                    "background-color: #d83b01;"
                )

            progress_widget.setStyleSheet(progress_style)
            self.task_table.setCellWidget(i, 2, progress_widget)

            # 速度
            speed_text = self._format_speed(task.progress.get("speed", 0))
            speed_item = QTableWidgetItem(speed_text)
            self.task_table.setItem(i, 3, speed_item)

            # 已完成/总计
            completed = task.progress.get("completed", 0)
            total = task.progress.get("total", 0)
            completed_total_item = QTableWidgetItem(f"{completed}/{total}")
            self.task_table.setItem(i, 4, completed_total_item)

            # 剩余时间
            estimated_time = task.progress.get("estimated_time")
            time_text = self._format_time(
                estimated_time) if estimated_time is not None else "--:--:--"
            time_item = QTableWidgetItem(time_text)
            self.task_table.setItem(i, 5, time_item)

            # 操作按钮
            self._create_action_buttons(i, task_id, task.status)

        # 自动调整行高以适应内容
        self.task_table.resizeRowsToContents()

    def update_task_progress(self, task_id, progress):
        """更新任务进度"""
        for row in range(self.task_table.rowCount()):
            name_item = self.task_table.item(row, 0)
            if name_item and name_item.data(Qt.UserRole) == task_id:
                # 更新进度条
                progress_bar = self.task_table.cellWidget(row, 2)
                if progress_bar:
                    completed = progress.get("completed", 0)
                    total = progress.get("total", 0)
                    percentage = int((completed / total) *
                                     100) if total > 0 else 0
                    progress_bar.setValue(percentage)

                # 更新速度
                speed_text = self._format_speed(progress.get("speed", 0))
                speed_item = self.task_table.item(row, 3)
                if speed_item:
                    speed_item.setText(speed_text)

                # 更新已完成/总计
                completed_total_item = self.task_table.item(row, 4)
                if completed_total_item:
                    completed_total_item.setText(f"{completed}/{total}")

                # 更新剩余时间
                estimated_time = progress.get("estimated_time")
                time_text = self._format_time(
                    estimated_time) if estimated_time is not None else "--:--:--"
                time_item = self.task_table.item(row, 5)
                if time_item:
                    time_item.setText(time_text)

                break

    def update_task_status(self, task_id, status):
        """更新任务状态"""
        for row in range(self.task_table.rowCount()):
            name_item = self.task_table.item(row, 0)
            if name_item and name_item.data(Qt.UserRole) == task_id:
                # 更新状态文本和颜色
                status_item = self.task_table.item(row, 1)
                if status_item:
                    status_item.setText(self._get_status_text(status))
                    status_item.setForeground(self._get_status_color(status))

                # 更新操作按钮
                self._create_action_buttons(row, task_id, status)

                break

    def _create_action_buttons(self, row, task_id, status):
        """创建操作按钮"""
        # 创建按钮容器
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(2, 0, 2, 0)
        buttons_layout.setSpacing(6)  # 增加按钮间距

        # 按钮样式
        btn_style = """
            QToolButton {
                padding: 4px 8px;
                border-radius: 3px;
                border: 1px solid transparent;
                background-color: transparent;
                color: #505050;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
            }
            QToolButton:pressed {
                background-color: #e0e0e0;
            }
        """

        start_btn_style = btn_style + """
            QToolButton {
                color: #0078d4;
            }
            QToolButton:hover {
                color: #0067b8;
            }
        """

        pause_btn_style = btn_style + """
            QToolButton {
                color: #ff9500;
            }
            QToolButton:hover {
                color: #e68600;
            }
        """

        cancel_btn_style = btn_style + """
            QToolButton {
                color: #d83b01;
            }
            QToolButton:hover {
                color: #c43500;
            }
        """

        # 根据状态创建不同的按钮
        if status == TaskStatus.PENDING or status == TaskStatus.PAUSED:
            # 开始按钮
            start_button = ToolButton()
            start_button.setText("开始")
            start_button.setStyleSheet(start_btn_style)
            start_button.setToolTip("开始任务")
            start_button.clicked.connect(
                lambda: self.task_action_requested.emit(task_id, "start"))
            buttons_layout.addWidget(start_button)

        if status == TaskStatus.RUNNING:
            # 暂停按钮
            pause_button = ToolButton()
            pause_button.setText("暂停")
            pause_button.setStyleSheet(pause_btn_style)
            pause_button.setToolTip("暂停任务")
            pause_button.clicked.connect(
                lambda: self.task_action_requested.emit(task_id, "pause"))
            buttons_layout.addWidget(pause_button)

        if status != TaskStatus.COMPLETED:
            # 取消按钮
            cancel_button = ToolButton()
            cancel_button.setText("取消")
            cancel_button.setStyleSheet(cancel_btn_style)
            cancel_button.setToolTip("取消任务")
            cancel_button.clicked.connect(
                lambda: self.task_action_requested.emit(task_id, "cancel"))
            buttons_layout.addWidget(cancel_button)

        # 删除按钮
        delete_button = ToolButton()
        delete_button.setText("删除")
        delete_button.setStyleSheet(btn_style)
        delete_button.setToolTip("删除任务")
        delete_button.clicked.connect(
            lambda: self.task_action_requested.emit(task_id, "remove"))
        buttons_layout.addWidget(delete_button)

        # 设置按钮到表格
        self.task_table.setCellWidget(row, 6, buttons_widget)

    def _show_context_menu(self, position):
        """显示上下文菜单"""
        index = self.task_table.indexAt(position)
        if not index.isValid():
            return

        row = index.row()
        name_item = self.task_table.item(row, 0)
        if not name_item:
            return

        task_id = name_item.data(Qt.UserRole)
        task = self.tasks.get(task_id)
        if not task:
            return

        # 创建上下文菜单
        menu = QMenu(self)

        # 根据任务状态添加不同的操作
        if task.status == TaskStatus.PENDING or task.status == TaskStatus.PAUSED:
            start_action = QAction("开始", self)
            start_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "start"))
            menu.addAction(start_action)

        if task.status == TaskStatus.RUNNING:
            pause_action = QAction("暂停", self)
            pause_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "pause"))
            menu.addAction(pause_action)

        # 添加取消操作
        if task.status != TaskStatus.COMPLETED and task.status != TaskStatus.FAILED and task.status != TaskStatus.CANCELED:
            cancel_action = QAction("取消", self)
            cancel_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "cancel"))
            menu.addAction(cancel_action)

        # 如果任务已完成，添加媒体处理选项
        if task.status == TaskStatus.COMPLETED and task.output_file and os.path.exists(task.output_file):
            menu.addSeparator()

            process_action = QAction("处理媒体文件", self)
            process_action.triggered.connect(
                lambda: self._show_media_processing(task_id))
            menu.addAction(process_action)

        menu.addSeparator()

        # 删除操作
        remove_action = QAction("删除任务", self)
        remove_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "remove"))
        menu.addAction(remove_action)

        remove_with_file_action = QAction("删除任务和文件", self)
        remove_with_file_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "remove_with_file"))
        menu.addAction(remove_with_file_action)

        # 显示菜单
        menu.exec(self.task_table.viewport().mapToGlobal(position))

    def _on_new_task(self):
        """新建任务按钮点击"""
        # 在父窗口中处理
        parent = self.parent()
        while parent:
            if hasattr(parent, "show_new_task_dialog"):
                parent.show_new_task_dialog()
                break
            parent = parent.parent()

    def _on_start_all(self):
        """全部开始按钮点击"""
        # 在父窗口中处理
        parent = self.parent()
        while parent:
            if hasattr(parent, "start_all_tasks"):
                parent.start_all_tasks()
                break
            parent = parent.parent()

    def _on_pause_all(self):
        """全部暂停按钮点击"""
        # 在父窗口中处理
        parent = self.parent()
        while parent:
            if hasattr(parent, "pause_all_tasks"):
                parent.pause_all_tasks()
                break
            parent = parent.parent()

    def _on_clean(self):
        """清理按钮点击"""
        # 在父窗口中处理
        parent = self.parent()
        while parent:
            if hasattr(parent, "clear_completed_tasks"):
                parent.clear_completed_tasks()
                break
            parent = parent.parent()

    def _get_status_text(self, status):
        """获取状态文本"""
        status_texts = {
            TaskStatus.PENDING: "等待中",
            TaskStatus.RUNNING: "下载中",
            TaskStatus.PAUSED: "已暂停",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "已失败",
            TaskStatus.CANCELED: "已取消"
        }
        return status_texts.get(status, str(status))

    def _get_status_color(self, status):
        """获取状态颜色"""
        status_colors = {
            TaskStatus.PENDING: QColor(150, 150, 150),  # 灰色
            TaskStatus.RUNNING: QColor(0, 120, 215),    # 蓝色
            TaskStatus.PAUSED: QColor(240, 160, 0),     # 橙色
            TaskStatus.COMPLETED: QColor(0, 160, 0),    # 绿色
            TaskStatus.FAILED: QColor(200, 0, 0),       # 红色
            TaskStatus.CANCELED: QColor(100, 100, 100)  # 深灰色
        }
        return QBrush(status_colors.get(status, QColor(0, 0, 0)))

    def _format_speed(self, bytes_per_second):
        """格式化速度显示"""
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.1f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024):.2f} MB/s"

    def _format_time(self, seconds):
        """格式化时间显示"""
        if seconds is None:
            return "--:--:--"

        seconds = max(0, int(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _show_media_processing(self, task_id):
        """显示媒体处理对话框"""
        # 在父窗口中处理
        parent = self.parent()
        while parent:
            if hasattr(parent, "show_media_processing"):
                parent.show_media_processing()
                break
            parent = parent.parent()

    # 添加获取选中行的方法
    def get_selected_rows(self):
        """获取选中的行对应的任务ID列表"""
        selected_rows = self.task_table.selectedItems()
        task_ids = []

        for item in selected_rows:
            if item.column() == 0:  # 只处理第一列的项
                task_id = item.data(Qt.UserRole)
                if task_id:
                    task_ids.append(task_id)

        return task_ids

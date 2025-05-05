from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QMenu, QAction,
    QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QBrush, QIcon, QCursor
from datetime import datetime
import logging

from src.core.scheduler import TaskType

logger = logging.getLogger(__name__)


class ScheduleManager(QWidget):
    """计划任务管理器界面"""

    # 信号定义
    task_action_requested = Signal(str, str)  # 任务ID, 操作

    def __init__(self, scheduler, parent=None):
        super().__init__(parent)

        self.scheduler = scheduler

        self._create_ui()
        self._populate_tasks()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 8)

        self.new_task_button = QPushButton("新建计划")
        self.new_task_button.clicked.connect(self._on_new_task)
        toolbar_layout.addWidget(self.new_task_button)

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self._populate_tasks)
        toolbar_layout.addWidget(self.refresh_button)

        # 添加空白
        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels(
            ["名称", "类型", "状态", "下次运行", "上次运行", "操作"]
        )
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(
            self._show_context_menu)

        # 设置表格列宽
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout.addWidget(self.task_table)

        # 提示标签
        self.hint_label = QLabel("提示: 右键点击任务可查看更多操作")
        layout.addWidget(self.hint_label)

    def _populate_tasks(self):
        """填充任务列表"""
        self.task_table.setRowCount(0)

        tasks = self.scheduler.get_all_tasks()
        self.task_table.setRowCount(len(tasks))

        for i, task in enumerate(tasks):
            # 名称
            name_item = QTableWidgetItem(task.name)
            name_item.setData(Qt.UserRole, task.task_id)
            self.task_table.setItem(i, 0, name_item)

            # 类型
            type_text = self._get_task_type_text(task.task_type)
            type_item = QTableWidgetItem(type_text)
            self.task_table.setItem(i, 1, type_item)

            # 状态
            status_text = "启用" if task.enabled else "禁用"
            status_item = QTableWidgetItem(status_text)
            status_color = QColor(
                0, 128, 0) if task.enabled else QColor(128, 128, 128)
            status_item.setForeground(QBrush(status_color))
            self.task_table.setItem(i, 2, status_item)

            # 下次运行
            next_run_text = self._format_datetime(
                task.next_run) if task.next_run else "--"
            next_run_item = QTableWidgetItem(next_run_text)
            self.task_table.setItem(i, 3, next_run_item)

            # 上次运行
            last_run_text = self._format_datetime(
                task.last_run) if task.last_run else "--"
            last_run_item = QTableWidgetItem(last_run_text)
            self.task_table.setItem(i, 4, last_run_item)

            # 操作按钮
            self._create_action_buttons(i, task)

    def _create_action_buttons(self, row, task):
        """创建操作按钮"""
        # 创建按钮容器
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)

        # 根据任务状态创建不同的按钮
        if task.enabled:
            # 禁用按钮
            disable_button = QPushButton("禁用")
            disable_button.clicked.connect(
                lambda: self.task_action_requested.emit(task.task_id, "disable"))
            buttons_layout.addWidget(disable_button)
        else:
            # 启用按钮
            enable_button = QPushButton("启用")
            enable_button.clicked.connect(
                lambda: self.task_action_requested.emit(task.task_id, "enable"))
            buttons_layout.addWidget(enable_button)

        # 删除按钮
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(
            lambda: self.task_action_requested.emit(task.task_id, "remove"))
        buttons_layout.addWidget(delete_button)

        # 设置按钮到表格
        self.task_table.setCellWidget(row, 5, buttons_widget)

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
        task = self.scheduler.get_task(task_id)
        if not task:
            return

        # 创建上下文菜单
        menu = QMenu(self)

        # 根据任务状态添加不同的操作
        if task.enabled:
            disable_action = QAction("禁用", self)
            disable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "disable"))
            menu.addAction(disable_action)
        else:
            enable_action = QAction("启用", self)
            enable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "enable"))
            menu.addAction(enable_action)

        # 立即执行
        run_now_action = QAction("立即执行", self)
        run_now_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "run_now"))
        menu.addAction(run_now_action)

        menu.addSeparator()

        # 删除操作
        remove_action = QAction("删除", self)
        remove_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "remove"))
        menu.addAction(remove_action)

        # 显示菜单
        menu.exec(QCursor.pos())

    def _on_new_task(self):
        """新建任务按钮点击"""
        # 发射信号，由父窗口处理
        self.task_action_requested.emit("", "new")

    def _get_task_type_text(self, task_type):
        """获取任务类型文本"""
        type_texts = {
            TaskType.ONE_TIME: "一次性",
            TaskType.DAILY: "每天",
            TaskType.WEEKLY: "每周",
            TaskType.INTERVAL: "间隔"
        }
        return type_texts.get(task_type, str(task_type))

    def _format_datetime(self, dt):
        """格式化日期时间"""
        if not dt:
            return "--"

        now = datetime.now()

        if dt.date() == now.date():
            # 今天
            return f"今天 {dt.strftime('%H:%M:%S')}"
        elif dt.date() == (now + datetime.timedelta(days=1)).date():
            # 明天
            return f"明天 {dt.strftime('%H:%M:%S')}"
        else:
            # 其他日期
            return dt.strftime("%Y-%m-%d %H:%M:%S")

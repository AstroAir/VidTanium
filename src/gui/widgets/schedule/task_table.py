"""任务表格组件"""

from PySide6.QtWidgets import (
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from datetime import datetime

from qfluentwidgets import TableWidget
from src.core.scheduler import TaskType
from .task_actions import TaskActionButtons

class TaskTable(TableWidget):
    """任务表格组件"""
    
    # 信号
    task_clicked = Signal(str)  # task_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()
        self._action_handlers = {}
        
    def _setup_table(self):
        """设置表格属性"""
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(
            ["名称", "类型", "状态", "下次执行", "上次执行", "操作"]
        )
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAlternatingRowColors(True)
        
        # 连接信号
        self.itemClicked.connect(self._on_item_clicked)
        
        # 设置表格列宽
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
    def set_action_handlers(self, handlers):
        """设置操作按钮的处理函数"""
        self._action_handlers = handlers
    
    def populate_tasks(self, tasks):
        """填充任务列表"""
        self.setRowCount(0)
        self.setRowCount(len(tasks))
        
        for i, task in enumerate(tasks):
            # 任务名称
            name_item = QTableWidgetItem(task.name)
            name_item.setData(Qt.UserRole, task.task_id)
            self.setItem(i, 0, name_item)
            
            # 任务类型
            type_text = self._get_task_type_text(task.task_type)
            type_item = QTableWidgetItem(type_text)
            self.setItem(i, 1, type_item)
            
            # 状态
            status_text = "已启用" if task.enabled else "已禁用"
            status_item = QTableWidgetItem(status_text)
            status_color = QColor(
                0, 128, 0) if task.enabled else QColor(128, 128, 128)
            status_item.setForeground(QBrush(status_color))
            self.setItem(i, 2, status_item)
            
            # 下次执行
            next_run_text = self._format_datetime(
                task.next_run) if task.next_run else "--"
            next_run_item = QTableWidgetItem(next_run_text)
            self.setItem(i, 3, next_run_item)
            
            # 上次执行
            last_run_text = self._format_datetime(
                task.last_run) if task.last_run else "--"
            last_run_item = QTableWidgetItem(last_run_text)
            self.setItem(i, 4, last_run_item)
            
            # 操作按钮
            self._add_action_buttons(i, task)
    
    def _add_action_buttons(self, row, task):
        """添加操作按钮"""
        action_buttons = TaskActionButtons()
        action_buttons.setup_for_task(task)
        
        # 连接按钮信号到处理函数
        action_buttons.connect_buttons(
            task.task_id,
            self._action_handlers.get('enable', lambda _: None),
            self._action_handlers.get('disable', lambda _: None),
            self._action_handlers.get('run_now', lambda _: None),
            self._action_handlers.get('show_details', lambda _: None),
            self._action_handlers.get('remove', lambda _: None)
        )
        
        self.setCellWidget(row, 5, action_buttons)
            
    def _on_item_clicked(self, item):
        """处理项目点击"""
        row = item.row()
        name_item = self.item(row, 0)
        if name_item:
            task_id = name_item.data(Qt.UserRole)
            self.task_clicked.emit(task_id)
    
    def update_task_row(self, task_id, task):
        """更新特定任务的行"""
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.data(Qt.UserRole) == task_id:
                # 更新状态
                status_text = "已启用" if task.enabled else "已禁用"
                status_color = QColor(
                    0, 128, 0) if task.enabled else QColor(128, 128, 128)
                self.item(row, 2).setText(status_text)
                self.item(row, 2).setForeground(QBrush(status_color))
                
                # 更新下次执行时间
                next_run_text = self._format_datetime(
                    task.next_run) if task.next_run else "--"
                self.item(row, 3).setText(next_run_text)
                
                # 更新上次执行时间
                last_run_text = self._format_datetime(
                    task.last_run) if task.last_run else "--"
                self.item(row, 4).setText(last_run_text)
                
                # 更新操作按钮
                self._add_action_buttons(row, task)
                break
                
    def get_visible_rows_count(self):
        """获取可见行数"""
        return sum(1 for row in range(self.rowCount()) 
                  if not self.isRowHidden(row))
    
    def get_total_rows_count(self):
        """获取总行数"""
        return self.rowCount()
    
    def filter_tasks(self, search_text="", filter_type="all"):
        """过滤任务"""
        search_text = search_text.lower() if search_text else ""
        
        for row in range(self.rowCount()):
            show_row = True
            name_item = self.item(row, 0)
            
            if not name_item:
                continue
                
            task_id = name_item.data(Qt.UserRole)
            task_name = name_item.text().lower()
            status_item = self.item(row, 2)
            type_item = self.item(row, 1)
            
            # 应用搜索过滤
            if search_text and search_text not in task_name:
                show_row = False
            
            # 应用类型过滤
            if filter_type == "enabled" and "已禁用" in status_item.text():
                show_row = False
            elif filter_type == "disabled" and "已启用" in status_item.text():
                show_row = False
            elif filter_type == "one_time" and "一次性" not in type_item.text():
                show_row = False
            elif filter_type == "recurring" and "一次性" in type_item.text():
                show_row = False
                
            self.setRowHidden(row, not show_row)
    
    def _get_task_type_text(self, task_type):
        """获取任务类型文本"""
        type_texts = {
            TaskType.ONE_TIME: "一次性",
            TaskType.DAILY: "每日",
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
        elif (dt.date() - now.date()).days == 1:
            # 明天
            return f"明天 {dt.strftime('%H:%M:%S')}"
        else:
            # 其他日期
            return dt.strftime("%Y-%m-%d %H:%M:%S")
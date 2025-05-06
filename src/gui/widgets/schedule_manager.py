from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QBrush, QIcon, QCursor
from datetime import datetime
import logging

from qfluentwidgets import (
    PushButton, TableWidget, InfoBar, InfoBarPosition,
    FluentIcon, MessageBox, Action, RoundMenu
)
from src.core.scheduler import TaskType

logger = logging.getLogger(__name__)


class ScheduleManager(QWidget):
    """Schedule Task Manager Interface"""

    # Signal definitions
    task_action_requested = Signal(str, str)  # task_id, action

    def __init__(self, scheduler, parent=None):
        super().__init__(parent)

        self.scheduler = scheduler

        self._create_ui()
        self._populate_tasks()

    def _create_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 8)

        self.new_task_button = PushButton("New Schedule")
        self.new_task_button.setIcon(FluentIcon.ADD)
        self.new_task_button.clicked.connect(self._on_new_task)
        toolbar_layout.addWidget(self.new_task_button)

        self.refresh_button = PushButton("Refresh")
        self.refresh_button.setIcon(FluentIcon.SYNC)
        self.refresh_button.clicked.connect(self._populate_tasks)
        toolbar_layout.addWidget(self.refresh_button)

        # Add stretch space
        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        # Task table
        self.task_table = TableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Status", "Next Run", "Last Run", "Actions"]
        )
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(
            self._show_context_menu)

        # Set table column widths
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout.addWidget(self.task_table)

        # Hint label
        self.hint_label = QLabel(
            "Tip: Right-click on a task to see more options")
        layout.addWidget(self.hint_label)

    def _populate_tasks(self):
        """Populate task list"""
        self.task_table.setRowCount(0)

        tasks = self.scheduler.get_all_tasks()
        self.task_table.setRowCount(len(tasks))

        for i, task in enumerate(tasks):
            # Name
            name_item = QTableWidgetItem(task.name)
            name_item.setData(Qt.UserRole, task.task_id)
            self.task_table.setItem(i, 0, name_item)

            # Type
            type_text = self._get_task_type_text(task.task_type)
            type_item = QTableWidgetItem(type_text)
            self.task_table.setItem(i, 1, type_item)

            # Status
            status_text = "Enabled" if task.enabled else "Disabled"
            status_item = QTableWidgetItem(status_text)
            status_color = QColor(
                0, 128, 0) if task.enabled else QColor(128, 128, 128)
            status_item.setForeground(QBrush(status_color))
            self.task_table.setItem(i, 2, status_item)

            # Next run
            next_run_text = self._format_datetime(
                task.next_run) if task.next_run else "--"
            next_run_item = QTableWidgetItem(next_run_text)
            self.task_table.setItem(i, 3, next_run_item)

            # Last run
            last_run_text = self._format_datetime(
                task.last_run) if task.last_run else "--"
            last_run_item = QTableWidgetItem(last_run_text)
            self.task_table.setItem(i, 4, last_run_item)

            # Action buttons
            self._create_action_buttons(i, task)

    def _create_action_buttons(self, row, task):
        """Create action buttons"""
        # Create button container
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)

        # Create different buttons based on task status
        if task.enabled:
            # Disable button
            disable_button = PushButton("Disable")
            disable_button.setIcon(FluentIcon.PAUSE)
            disable_button.clicked.connect(
                lambda: self.task_action_requested.emit(task.task_id, "disable"))
            buttons_layout.addWidget(disable_button)
        else:
            # Enable button
            enable_button = PushButton("Enable")
            enable_button.setIcon(FluentIcon.PLAY)
            enable_button.clicked.connect(
                lambda: self.task_action_requested.emit(task.task_id, "enable"))
            buttons_layout.addWidget(enable_button)

        # Delete button
        delete_button = PushButton("Delete")
        delete_button.setIcon(FluentIcon.DELETE)
        delete_button.clicked.connect(
            lambda: self.task_action_requested.emit(task.task_id, "remove"))
        buttons_layout.addWidget(delete_button)

        # Set buttons to table
        self.task_table.setCellWidget(row, 5, buttons_widget)

    def _show_context_menu(self, position):
        """Show context menu"""
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

        # Create context menu
        menu = RoundMenu(self)

        # Add different actions based on task status
        if task.enabled:
            disable_action = Action(FluentIcon.PAUSE, "Disable")
            disable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "disable"))
            menu.addAction(disable_action)
        else:
            enable_action = Action(FluentIcon.PLAY, "Enable")
            enable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "enable"))
            menu.addAction(enable_action)

        # Run now
        run_now_action = Action(FluentIcon.PLAY_SOLID, "Run Now")
        run_now_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "run_now"))
        menu.addAction(run_now_action)

        menu.addSeparator()

        # Delete action
        remove_action = Action(FluentIcon.DELETE, "Delete")
        remove_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "remove"))
        menu.addAction(remove_action)

        # Show menu
        menu.exec(QCursor.pos())

    def _on_new_task(self):
        """New task button clicked"""
        # Emit signal to be handled by parent window
        self.task_action_requested.emit("", "new")

    def _get_task_type_text(self, task_type):
        """Get task type text"""
        type_texts = {
            TaskType.ONE_TIME: "One Time",
            TaskType.DAILY: "Daily",
            TaskType.WEEKLY: "Weekly",
            TaskType.INTERVAL: "Interval"
        }
        return type_texts.get(task_type, str(task_type))

    def _format_datetime(self, dt):
        """Format datetime"""
        if not dt:
            return "--"

        now = datetime.now()

        if dt.date() == now.date():
            # Today
            return f"Today {dt.strftime('%H:%M:%S')}"
        elif dt.date() == (now.date() + datetime.timedelta(days=1)).date():
            # Tomorrow
            return f"Tomorrow {dt.strftime('%H:%M:%S')}"
        else:
            # Other dates
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    def show_message(self, title, content, type_="success"):
        """Show a message notification"""
        if type_ == "success":
            InfoBar.success(title, content, parent=self,
                            position=InfoBarPosition.TOP)
        elif type_ == "warning":
            InfoBar.warning(title, content, parent=self,
                            position=InfoBarPosition.TOP)
        elif type_ == "error":
            InfoBar.error(title, content, parent=self,
                          position=InfoBarPosition.TOP)
        else:
            InfoBar.info(title, content, parent=self,
                         position=InfoBarPosition.TOP)

"""计划任务管理器主界面 - 已重构使用拆分组件"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QCursor
from datetime import datetime
import logging

from qfluentwidgets import (
    InfoBar, InfoBarPosition, MessageBox, Action, RoundMenu,
    SearchLineEdit, ComboBox, SubtitleLabel, ToggleButton,
    CardWidget, FluentIcon
)

# 导入拆分后的组件
from .schedule.task_details_widget import TaskDetailsWidget
from .schedule.task_table import TaskTable
from .schedule.schedule_toolbar import ScheduleToolbar

# 导入国际化支持
from ..utils.i18n import tr

logger = logging.getLogger(__name__)


class ScheduleManager(QWidget):
    """计划任务管理器界面
    
    已完全集成国际化(i18n)系统：
    - 所有用户可见文本都通过翻译函数 tr() 获取
    - 支持动态语言切换，调用 update_locale() 方法
    - 翻译键值存储在 locales/zh_CN.json 和 locales/en.json 中的 schedule_manager 节点下
    - 子组件也需要实现 update_locale() 方法以支持完整的语言切换
    """

    # 可配置的自动刷新间隔（毫秒）
    AUTO_REFRESH_INTERVAL_MS = 30 * 1000  # 默认30秒

    # 信号定义
    task_action_requested = Signal(str, str)  # task_id, action

    def __init__(self, scheduler, parent=None):
        super().__init__(parent)

        self.scheduler = scheduler
        self.current_filter = "all"  # 当前过滤器
        self.refresh_timer = None

        self._create_ui()
        self._connect_signals()
        self._populate_tasks()
        self._setup_auto_refresh()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 顶部标题
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = SubtitleLabel(tr("schedule_manager.title"))
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        # 自动刷新开关
        self.auto_refresh = ToggleButton(tr("schedule_manager.auto_refresh"))
        self.auto_refresh.setChecked(True)
        title_layout.addWidget(self.auto_refresh)

        layout.addLayout(title_layout)

        # 工具栏
        self.toolbar = ScheduleToolbar(self)
        layout.addWidget(self.toolbar)

        # 主分割器: 表格 + 详情面板
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # 左侧表格
        table_card = CardWidget()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.setSpacing(10)

        # 搜索和过滤行
        filter_layout = QHBoxLayout()

        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText(tr("schedule_manager.search.placeholder"))
        filter_layout.addWidget(self.search_input, 2)

        self.filter_combo = ComboBox()
        self.filter_combo.addItems([
            tr("schedule_manager.filters.all"),
            tr("schedule_manager.filters.enabled"), 
            tr("schedule_manager.filters.disabled"),
            tr("schedule_manager.filters.one_time"),
            tr("schedule_manager.filters.recurring")
        ])
        filter_layout.addWidget(self.filter_combo, 1)

        table_layout.addLayout(filter_layout)

        # 任务表格
        self.task_table = TaskTable()
        table_layout.addWidget(self.task_table)

        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel(tr("schedule_manager.loading"))
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.next_update_label = QLabel()
        status_layout.addWidget(self.next_update_label)

        table_layout.addLayout(status_layout)

        self.splitter.addWidget(table_card)

        # 右侧详情面板
        self.task_details = TaskDetailsWidget()
        self.splitter.addWidget(self.task_details)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)

    def _connect_signals(self):
        """连接信号与槽"""
        # 自动刷新开关
        self.auto_refresh.toggled.connect(self._toggle_auto_refresh)

        # 表格过滤信号
        self.search_input.textChanged.connect(self._filter_tasks)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)

        # 表格上下文菜单
        self.task_table.customContextMenuRequested.connect(
            self._show_context_menu)
        self.task_table.task_clicked.connect(self._show_task_details)

        # 设置操作处理函数
        self.task_table.set_action_handlers({
            'enable': lambda task_id: self.task_action_requested.emit(task_id, "enable"),
            'disable': lambda task_id: self.task_action_requested.emit(task_id, "disable"),
            'run_now': lambda task_id: self.task_action_requested.emit(task_id, "run_now"),
            'show_details': self._show_task_details,
            'remove': lambda task_id: self.task_action_requested.emit(task_id, "remove")
        })

        # 详情面板按钮
        self.task_details.enable_button.clicked.connect(self._on_toggle_task)
        self.task_details.run_now_button.clicked.connect(self._on_run_now)
        self.task_details.delete_button.clicked.connect(self._on_delete_task)

        # 工具栏按钮
        self.toolbar.new_task_clicked.connect(
            lambda: self.task_action_requested.emit("", "new"))
        self.toolbar.refresh_clicked.connect(self._populate_tasks)
        self.toolbar.enable_all_clicked.connect(self._on_enable_all)
        self.toolbar.disable_all_clicked.connect(self._on_disable_all)
        self.toolbar.view_details_toggled.connect(self.task_details.setVisible)        # 初始隐藏详情面板
        self.task_details.setVisible(False)

    def _setup_auto_refresh(self):
        """设置自动刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(self.AUTO_REFRESH_INTERVAL_MS)  # 使用可配置间隔
        self._update_refresh_countdown()

    def _update_refresh_countdown(self):
        """更新刷新倒计时"""
        if self.refresh_timer and self.refresh_timer.isActive():
            seconds = self.refresh_timer.remainingTime() // 1000
            self.next_update_label.setText(tr("schedule_manager.status_bar.refresh_in", seconds=seconds))

            # 每秒更新倒计时
            QTimer.singleShot(1000, self._update_refresh_countdown)
        else:
            self.next_update_label.setText(tr("schedule_manager.auto_refresh_off"))

    def _toggle_auto_refresh(self, enabled):
        """切换自动刷新"""
        if enabled and self.refresh_timer:
            self.refresh_timer.start(self.AUTO_REFRESH_INTERVAL_MS)
            self._update_refresh_countdown()
        elif self.refresh_timer:
            self.refresh_timer.stop()
            self.next_update_label.setText(tr("schedule_manager.auto_refresh_off"))

    def _auto_refresh(self):
        """自动刷新"""
        self._populate_tasks()

    def _on_filter_changed(self, index):
        """处理过滤器变化"""
        filters = ["all", "enabled", "disabled", "one_time", "recurring"]
        if index >= 0 and index < len(filters):
            self.current_filter = filters[index]
            self._filter_tasks()

    def _filter_tasks(self):
        """过滤任务"""
        search_text = self.search_input.text()
        self.task_table.filter_tasks(search_text, self.current_filter)

        # 更新状态栏信息
        visible_rows = self.task_table.get_visible_rows_count()
        total_rows = self.task_table.get_total_rows_count()
        self.status_label.setText(tr("schedule_manager.status_bar.showing", visible=visible_rows, total=total_rows))

    def _populate_tasks(self):
        """填充任务列表"""
        tasks = self.scheduler.get_all_tasks()
        self.task_table.populate_tasks(tasks)

        # 应用当前过滤器
        self._filter_tasks()

    def _show_task_details(self, task_id):
        """显示任务详情"""
        task = self.scheduler.get_task(task_id)
        if task:
            self.toolbar.set_details_checked(True)
            self.task_details.update_task(task)

    def _on_toggle_task(self):
        """切换任务状态"""
        if not self.task_details.current_task:
            return

        task_id = self.task_details.current_task.task_id
        action = "disable" if self.task_details.current_task.enabled else "enable"
        self.task_action_requested.emit(task_id, action)

    def _on_run_now(self):
        """立即执行任务"""
        if not self.task_details.current_task:
            return

        self.task_action_requested.emit(
            self.task_details.current_task.task_id, "run_now")

    def _on_delete_task(self):
        """删除任务"""
        if not self.task_details.current_task:
            return

        self.task_action_requested.emit(
            self.task_details.current_task.task_id, "remove")

    def _show_context_menu(self, position):
        """显示上下文菜单"""
        index = self.task_table.indexAt(position)
        if not index.isValid():
            return

        row = index.row()
        name_item = self.task_table.item(row, 0)
        if not name_item:
            return

        task_id = name_item.data(Qt.ItemDataRole.UserRole)
        task = self.scheduler.get_task(task_id)
        if not task:
            return

        # 创建上下文菜单
        menu = RoundMenu(tr("schedule_manager.context_menu.task_actions"), self)

        # 添加不同操作基于任务状态
        if task.enabled:
            disable_action = Action(FluentIcon.PAUSE, tr("schedule_manager.actions.disable"))
            disable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "disable"))
            menu.addAction(disable_action)
        else:
            enable_action = Action(FluentIcon.PLAY, tr("schedule_manager.actions.enable"))
            enable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "enable"))
            menu.addAction(enable_action)

        # 立即执行
        run_now_action = Action(FluentIcon.PLAY_SOLID, tr("schedule_manager.actions.run_now"))
        run_now_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "run_now"))
        menu.addAction(run_now_action)

        # 查看详情
        view_details_action = Action(FluentIcon.INFO, tr("schedule_manager.actions.view_details"))
        view_details_action.triggered.connect(
            lambda: self._show_task_details(task_id))
        menu.addAction(view_details_action)

        menu.addSeparator()

        # 删除操作
        remove_action = Action(FluentIcon.DELETE, tr("schedule_manager.actions.delete"))
        remove_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "remove"))
        menu.addAction(remove_action)

        # 显示菜单
        menu.exec(QCursor.pos())

    def _on_enable_all(self):
        """启用所有任务"""
        result = MessageBox(tr("schedule_manager.batch_operations.title"), 
                           tr("schedule_manager.messages.confirm_enable_all"), self).exec()
        if not result:
            return

        tasks = self.scheduler.get_all_tasks()
        enabled_count = 0

        for task in tasks:
            if not task.enabled:
                self.task_action_requested.emit(task.task_id, "enable")
                enabled_count += 1

        if enabled_count > 0:
            self.show_message(tr("schedule_manager.batch_operations.title"), 
                            tr("schedule_manager.messages.batch_enabled", count=enabled_count))
        else:
            self.show_message(tr("schedule_manager.batch_operations.title"), 
                            tr("schedule_manager.messages.no_tasks_to_enable"), type_="info")

    def _on_disable_all(self):
        """禁用所有任务"""
        result = MessageBox(tr("schedule_manager.batch_operations.title"), 
                           tr("schedule_manager.messages.confirm_disable_all"), self).exec()
        if not result:
            return

        tasks = self.scheduler.get_all_tasks()
        disabled_count = 0

        for task in tasks:
            if task.enabled:
                self.task_action_requested.emit(task.task_id, "disable")
                disabled_count += 1

        if disabled_count > 0:
            self.show_message(tr("schedule_manager.batch_operations.title"), 
                            tr("schedule_manager.messages.batch_disabled", count=disabled_count))
        else:
            self.show_message(tr("schedule_manager.batch_operations.title"), 
                            tr("schedule_manager.messages.no_tasks_to_disable"), type_="info")

    def show_message(self, title, content, type_="success"):
        """显示消息通知"""
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

    def update_task(self, task_id):
        """更新特定任务"""
        task = self.scheduler.get_task(task_id)
        if task:
            # 更新表格中的任务行
            self.task_table.update_task_row(task_id, task)

            # 如果是当前显示的任务，更新详情面板
            if (self.task_details.isVisible() and
                    self.task_details.current_task and
                    self.task_details.current_task.task_id == task_id):
                self.task_details.update_task(task)

    def update_locale(self):
        """更新界面语言"""
        # 更新标题和按钮文本
        self.title_label.setText(tr("schedule_manager.title"))
        self.auto_refresh.setText(tr("schedule_manager.auto_refresh"))
        
        # 更新搜索框占位符
        self.search_input.setPlaceholderText(tr("schedule_manager.search.placeholder"))
        
        # 更新过滤器选项
        self.filter_combo.clear()
        self.filter_combo.addItems([
            tr("schedule_manager.filters.all"),
            tr("schedule_manager.filters.enabled"), 
            tr("schedule_manager.filters.disabled"),
            tr("schedule_manager.filters.one_time"),
            tr("schedule_manager.filters.recurring")
        ])
        
        # 更新状态标签
        if hasattr(self, 'task_table'):
            visible_rows = self.task_table.get_visible_rows_count()
            total_rows = self.task_table.get_total_rows_count()
            self.status_label.setText(tr("schedule_manager.status_bar.showing", visible=visible_rows, total=total_rows))
        
        # 更新刷新状态文本
        if self.refresh_timer and self.refresh_timer.isActive():
            self._update_refresh_countdown()
        else:
            self.next_update_label.setText(tr("schedule_manager.auto_refresh_off"))
        
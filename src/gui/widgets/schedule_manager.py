from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QLabel, QSplitter,
    QComboBox, QGroupBox, QFormLayout, QFrame, QToolBar, QAction
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QColor, QBrush, QIcon, QCursor
from datetime import datetime, timedelta
import logging

from qfluentwidgets import (
    PushButton, TableWidget, InfoBar, InfoBarPosition,
    FluentIcon, MessageBox, Action, RoundMenu, SearchLineEdit,
    CardWidget, StrongBodyLabel, BodyLabel, IconWidget,
    ComboBox, CheckBox, SubtitleLabel, ToggleButton,
    TransparentToggleToolButton, TransparentToolButton,
    ToolButton, ProgressRing, LineEdit
)
from src.core.scheduler import TaskType

logger = logging.getLogger(__name__)



class TaskDetailsWidget(CardWidget):
    """任务详情组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_task = None
        self._create_ui()

    def _create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 标题
        header_layout = QHBoxLayout()
        self.title_label = StrongBodyLabel("任务详情")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # 关闭按钮
        self.close_button = TransparentToolButton(FluentIcon.CLOSE, self)
        self.close_button.setIconSize(QSize(12, 12))
        self.close_button.clicked.connect(lambda: self.setVisible(False))
        header_layout.addWidget(self.close_button)

        layout.addLayout(header_layout)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # 详情表单
        details_form = QFormLayout()
        details_form.setLabelAlignment(Qt.AlignRight)
        details_form.setSpacing(10)

        # 任务名称
        self.task_name = BodyLabel("")
        details_form.addRow("任务名称:", self.task_name)

        # 任务类型
        self.task_type = BodyLabel("")
        details_form.addRow("任务类型:", self.task_type)

        # 创建时间
        self.create_time = BodyLabel("")
        details_form.addRow("创建时间:", self.create_time)

        # 状态
        self.status = BodyLabel("")
        details_form.addRow("当前状态:", self.status)

        # 下次执行
        self.next_run = BodyLabel("")
        details_form.addRow("下次执行:", self.next_run)

        # 上次执行
        self.last_run = BodyLabel("")
        details_form.addRow("上次执行:", self.last_run)

        # 执行次数
        self.run_count = BodyLabel("")
        details_form.addRow("已执行次数:", self.run_count)

        # 任务配置
        self.config_group = QGroupBox("任务配置")
        config_layout = QFormLayout(self.config_group)
        config_layout.setLabelAlignment(Qt.AlignRight)

        # 根据任务类型不同，配置项会变化
        # 周期
        self.period_label = BodyLabel("")
        config_layout.addRow("执行周期:", self.period_label)

        # 优先级
        self.priority_label = BodyLabel("")
        config_layout.addRow("任务优先级:", self.priority_label)

        # 通知
        self.notify_label = BodyLabel("")
        config_layout.addRow("完成通知:", self.notify_label)

        layout.addLayout(details_form)
        layout.addWidget(self.config_group)

        # 任务数据
        self.data_group = QGroupBox("任务数据")
        data_layout = QVBoxLayout(self.data_group)

        self.data_text = LineEdit()
        self.data_text.setReadOnly(True)
        data_layout.addWidget(self.data_text)

        layout.addWidget(self.data_group)

        # 操作按钮
        actions_layout = QHBoxLayout()

        self.enable_button = PushButton("启用")
        self.enable_button.setIcon(FluentIcon.PLAY)
        actions_layout.addWidget(self.enable_button)

        self.run_now_button = PushButton("立即执行")
        self.run_now_button.setIcon(FluentIcon.PLAY_SOLID)
        actions_layout.addWidget(self.run_now_button)

        self.delete_button = PushButton("删除")
        self.delete_button.setIcon(FluentIcon.DELETE)
        actions_layout.addWidget(self.delete_button)

        layout.addLayout(actions_layout)
        layout.addStretch(1)

    def update_task(self, task):
        """更新任务信息"""
        if not task:
            self.setVisible(False)
            return

        self.current_task = task

        # 更新基本信息
        self.task_name.setText(task.name)
        self.task_type.setText(self._get_task_type_text(task.task_type))

        create_time = task.created_at.strftime(
            "%Y-%m-%d %H:%M:%S") if task.created_at else "未知"
        self.create_time.setText(create_time)

        # 状态和下一次/上一次执行
        self.status.setText("已启用" if task.enabled else "已禁用")

        next_run = self._format_datetime(
            task.next_run) if task.next_run else "--"
        self.next_run.setText(next_run)

        last_run = self._format_datetime(
            task.last_run) if task.last_run else "--"
        self.last_run.setText(last_run)

        # 执行次数
        self.run_count.setText(str(task.run_count))

        # 配置信息
        if task.task_type == TaskType.ONE_TIME:
            self.period_label.setText("一次性任务")
        elif task.task_type == TaskType.DAILY:
            self.period_label.setText("每天")
        elif task.task_type == TaskType.WEEKLY:
            days = []
            for day in task.days:
                days.append(["周一", "周二", "周三", "周四", "周五", "周六", "周日"][day])
            self.period_label.setText(f"每周 {', '.join(days)}")
        elif task.task_type == TaskType.INTERVAL:
            hours = task.interval // 3600
            minutes = (task.interval % 3600) // 60
            self.period_label.setText(f"间隔 {hours}小时{minutes}分钟")

        # 优先级
        priority_map = {
            "high": "高",
            "normal": "中",
            "low": "低"
        }
        priority = priority_map.get(task.data.get("priority", "normal"), "中")
        self.priority_label.setText(priority)

        # 通知
        notify = "开启" if task.data.get("notify", False) else "关闭"
        self.notify_label.setText(notify)

        # 任务数据
        if "output_file" in task.data:
            self.data_text.setText(task.data["output_file"])
        elif task.data:
            self.data_text.setText(str(task.data))
        else:
            self.data_text.setText("无数据")

        # 启用/禁用按钮
        if task.enabled:
            self.enable_button.setText("禁用")
            self.enable_button.setIcon(FluentIcon.PAUSE)
        else:
            self.enable_button.setText("启用")
            self.enable_button.setIcon(FluentIcon.PLAY)

        # 显示详情面板
        self.setVisible(True)

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


class ScheduleManager(QWidget):
    """计划任务管理器界面"""

    # 信号定义
    task_action_requested = Signal(str, str)  # task_id, action

    def __init__(self, scheduler, parent=None):
        super().__init__(parent)

        self.scheduler = scheduler
        self.current_filter = "all"  # 当前过滤器
        self.refresh_timer = None

        self._create_ui()
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

        self.title_label = SubtitleLabel("计划任务管理")
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        # 自动刷新开关
        self.auto_refresh = ToggleButton("自动刷新")
        self.auto_refresh.setChecked(True)
        self.auto_refresh.toggled.connect(self._toggle_auto_refresh)
        title_layout.addWidget(self.auto_refresh)

        layout.addLayout(title_layout)

        # 工具栏
        self._create_toolbar()
        layout.addWidget(self.toolbar)

        # 主分割器: 表格 + 详情面板
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # 左侧表格
        table_card = CardWidget()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.setSpacing(10)

        # 搜索和过滤行
        filter_layout = QHBoxLayout()

        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("搜索任务...")
        self.search_input.textChanged.connect(self._filter_tasks)
        filter_layout.addWidget(self.search_input, 2)

        self.filter_combo = ComboBox()
        self.filter_combo.addItems(["全部任务", "已启用", "已禁用", "一次性", "定期任务"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo, 1)

        table_layout.addLayout(filter_layout)

        # 任务表格
        self.task_table = TableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels(
            ["名称", "类型", "状态", "下次执行", "上次执行", "操作"]
        )
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(
            self._show_context_menu)
        self.task_table.itemClicked.connect(self._on_task_clicked)
        self.task_table.setAlternatingRowColors(True)

        # 设置表格列宽
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        table_layout.addWidget(self.task_table)

        # 状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("加载中...")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.next_update_label = QLabel()
        status_layout.addWidget(self.next_update_label)

        table_layout.addLayout(status_layout)

        self.splitter.addWidget(table_card)

        # 右侧详情面板
        self.task_details = TaskDetailsWidget()
        self.task_details.enable_button.clicked.connect(self._on_toggle_task)
        self.task_details.run_now_button.clicked.connect(self._on_run_now)
        self.task_details.delete_button.clicked.connect(self._on_delete_task)
        self.task_details.setVisible(False)

        self.splitter.addWidget(self.task_details)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)

    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16, 16))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # 新建任务
        self.new_task_action = QAction(FluentIcon.ADD.icon(), "新建计划", self)
        self.new_task_action.setToolTip("创建新的计划任务")
        self.new_task_action.triggered.connect(self._on_new_task)
        self.toolbar.addAction(self.new_task_action)

        # 刷新按钮
        self.refresh_action = QAction(FluentIcon.SYNC.icon(), "刷新", self)
        self.refresh_action.setToolTip("刷新任务列表")
        self.refresh_action.triggered.connect(self._populate_tasks)
        self.toolbar.addAction(self.refresh_action)

        self.toolbar.addSeparator()

        # 批量操作按钮
        self.enable_all_action = QAction(FluentIcon.PLAY.icon(), "全部启用", self)
        self.enable_all_action.triggered.connect(self._on_enable_all)
        self.toolbar.addAction(self.enable_all_action)

        self.disable_all_action = QAction(
            FluentIcon.PAUSE.icon(), "全部禁用", self)
        self.disable_all_action.triggered.connect(self._on_disable_all)
        self.toolbar.addAction(self.disable_all_action)

        self.toolbar.addSeparator()

        # 任务详情按钮
        self.view_details_action = QAction(
            FluentIcon.INFO.icon(), "查看详情", self)
        self.view_details_action.setCheckable(True)
        self.view_details_action.triggered.connect(
            lambda checked: self.task_details.setVisible(checked))
        self.toolbar.addAction(self.view_details_action)

    def _setup_auto_refresh(self):
        """设置自动刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(30 * 1000)  # 30秒刷新一次
        self._update_refresh_countdown()

    def _update_refresh_countdown(self):
        """更新刷新倒计时"""
        if self.refresh_timer and self.refresh_timer.isActive():
            seconds = self.refresh_timer.remainingTime() // 1000
            self.next_update_label.setText(f"{seconds}秒后刷新")

            # 每秒更新倒计时
            QTimer.singleShot(1000, self._update_refresh_countdown)
        else:
            self.next_update_label.setText("自动刷新已关闭")

    def _toggle_auto_refresh(self, enabled):
        """切换自动刷新"""
        if enabled and self.refresh_timer:
            self.refresh_timer.start(30 * 1000)
            self._update_refresh_countdown()
        elif self.refresh_timer:
            self.refresh_timer.stop()
            self.next_update_label.setText("自动刷新已关闭")

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
        search_text = self.search_input.text().lower()

        for row in range(self.task_table.rowCount()):
            show_row = True
            task_id = self.task_table.item(row, 0).data(Qt.UserRole)
            task = self.scheduler.get_task(task_id)

            if not task:
                continue

            # 应用搜索过滤
            if search_text and search_text not in task.name.lower():
                show_row = False

            # 应用类型过滤
            if self.current_filter == "enabled" and not task.enabled:
                show_row = False
            elif self.current_filter == "disabled" and task.enabled:
                show_row = False
            elif self.current_filter == "one_time" and task.task_type != TaskType.ONE_TIME:
                show_row = False
            elif self.current_filter == "recurring" and task.task_type == TaskType.ONE_TIME:
                show_row = False

            self.task_table.setRowHidden(row, not show_row)

        # 更新状态栏信息
        visible_rows = sum(1 for row in range(
            self.task_table.rowCount()) if not self.task_table.isRowHidden(row))
        total_rows = self.task_table.rowCount()
        self.status_label.setText(f"显示 {visible_rows}/{total_rows} 个任务")

    def _populate_tasks(self):
        """填充任务列表"""
        self.task_table.setRowCount(0)

        tasks = self.scheduler.get_all_tasks()
        self.task_table.setRowCount(len(tasks))

        for i, task in enumerate(tasks):
            # 任务名称
            name_item = QTableWidgetItem(task.name)
            name_item.setData(Qt.UserRole, task.task_id)
            self.task_table.setItem(i, 0, name_item)

            # 任务类型
            type_text = self._get_task_type_text(task.task_type)
            type_item = QTableWidgetItem(type_text)
            self.task_table.setItem(i, 1, type_item)

            # 状态
            status_text = "已启用" if task.enabled else "已禁用"
            status_item = QTableWidgetItem(status_text)
            status_color = QColor(
                0, 128, 0) if task.enabled else QColor(128, 128, 128)
            status_item.setForeground(QBrush(status_color))
            self.task_table.setItem(i, 2, status_item)

            # 下次执行
            next_run_text = self._format_datetime(
                task.next_run) if task.next_run else "--"
            next_run_item = QTableWidgetItem(next_run_text)
            self.task_table.setItem(i, 3, next_run_item)

            # 上次执行
            last_run_text = self._format_datetime(
                task.last_run) if task.last_run else "--"
            last_run_item = QTableWidgetItem(last_run_text)
            self.task_table.setItem(i, 4, last_run_item)

            # 操作按钮
            self._create_action_buttons(i, task)

        # 应用当前过滤器
        self._filter_tasks()

    def _create_action_buttons(self, row, task):
        """创建操作按钮"""
        # 创建按钮容器
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)

        # 创建不同的按钮基于任务状态
        if task.enabled:
            # 禁用按钮
            disable_button = ToolButton(FluentIcon.PAUSE)
            disable_button.setToolTip("禁用")
            disable_button.clicked.connect(
                lambda: self.task_action_requested.emit(task.task_id, "disable"))
            buttons_layout.addWidget(disable_button)
        else:
            # 启用按钮
            enable_button = ToolButton(FluentIcon.PLAY)
            enable_button.setToolTip("启用")
            enable_button.clicked.connect(
                lambda: self.task_action_requested.emit(task.task_id, "enable"))
            buttons_layout.addWidget(enable_button)

        # 运行按钮
        run_button = ToolButton(FluentIcon.PLAY_SOLID)
        run_button.setToolTip("立即执行")
        run_button.clicked.connect(
            lambda: self.task_action_requested.emit(task.task_id, "run_now"))
        buttons_layout.addWidget(run_button)

        # 详情按钮
        info_button = ToolButton(FluentIcon.INFO)
        info_button.setToolTip("查看详情")
        info_button.clicked.connect(
            lambda: self._show_task_details(task.task_id))
        buttons_layout.addWidget(info_button)

        # 删除按钮
        delete_button = ToolButton(FluentIcon.DELETE)
        delete_button.setToolTip("删除")
        delete_button.clicked.connect(
            lambda: self.task_action_requested.emit(task.task_id, "remove"))
        buttons_layout.addWidget(delete_button)

        # 设置按钮到表格
        self.task_table.setCellWidget(row, 5, buttons_widget)

    def _show_task_details(self, task_id):
        """显示任务详情"""
        task = self.scheduler.get_task(task_id)
        if task:
            self.view_details_action.setChecked(True)
            self.task_details.update_task(task)

    def _on_task_clicked(self, item):
        """处理任务点击"""
        row = item.row()
        task_id = self.task_table.item(row, 0).data(Qt.UserRole)
        if task_id:
            self._show_task_details(task_id)

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

        task_id = name_item.data(Qt.UserRole)
        task = self.scheduler.get_task(task_id)
        if not task:
            return

        # 创建上下文菜单
        menu = RoundMenu(self)

        # 添加不同操作基于任务状态
        if task.enabled:
            disable_action = Action(FluentIcon.PAUSE, "禁用")
            disable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "disable"))
            menu.addAction(disable_action)
        else:
            enable_action = Action(FluentIcon.PLAY, "启用")
            enable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "enable"))
            menu.addAction(enable_action)

        # 立即执行
        run_now_action = Action(FluentIcon.PLAY_SOLID, "立即执行")
        run_now_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "run_now"))
        menu.addAction(run_now_action)

        # 查看详情
        view_details_action = Action(FluentIcon.INFO, "查看详情")
        view_details_action.triggered.connect(
            lambda: self._show_task_details(task_id))
        menu.addAction(view_details_action)

        menu.addSeparator()

        # 删除操作
        remove_action = Action(FluentIcon.DELETE, "删除")
        remove_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "remove"))
        menu.addAction(remove_action)

        # 显示菜单
        menu.exec(QCursor.pos())

    def _on_new_task(self):
        """新建任务按钮点击"""
        # 发出信号由父窗口处理
        self.task_action_requested.emit("", "new")

    def _on_enable_all(self):
        """启用所有任务"""
        result = MessageBox("确认操作", "是否要启用所有任务？", self).exec()
        if not result:
            return

        tasks = self.scheduler.get_all_tasks()
        enabled_count = 0

        for task in tasks:
            if not task.enabled:
                self.task_action_requested.emit(task.task_id, "enable")
                enabled_count += 1

        if enabled_count > 0:
            self.show_message("批量操作", f"已启用 {enabled_count} 个任务")
        else:
            self.show_message("批量操作", "没有需要启用的任务", type_="info")

    def _on_disable_all(self):
        """禁用所有任务"""
        result = MessageBox("确认操作", "是否要禁用所有任务？", self).exec()
        if not result:
            return

        tasks = self.scheduler.get_all_tasks()
        disabled_count = 0

        for task in tasks:
            if task.enabled:
                self.task_action_requested.emit(task.task_id, "disable")
                disabled_count += 1

        if disabled_count > 0:
            self.show_message("批量操作", f"已禁用 {disabled_count} 个任务")
        else:
            self.show_message("批量操作", "没有需要禁用的任务", type_="info")

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
        # 更新表格中的任务
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 0)
            if item and item.data(Qt.UserRole) == task_id:
                task = self.scheduler.get_task(task_id)
                if task:
                    # 更新状态
                    status_text = "已启用" if task.enabled else "已禁用"
                    status_color = QColor(
                        0, 128, 0) if task.enabled else QColor(128, 128, 128)
                    self.task_table.item(row, 2).setText(status_text)
                    self.task_table.item(row, 2).setForeground(
                        QBrush(status_color))

                    # 更新下次执行时间
                    next_run_text = self._format_datetime(
                        task.next_run) if task.next_run else "--"
                    self.task_table.item(row, 3).setText(next_run_text)

                    # 更新上次执行时间
                    last_run_text = self._format_datetime(
                        task.last_run) if task.last_run else "--"
                    self.task_table.item(row, 4).setText(last_run_text)

                    # 更新操作按钮
                    self._create_action_buttons(row, task)

                    # 如果是当前显示的任务，更新详情面板
                    if (self.task_details.isVisible() and
                            self.task_details.current_task and
                            self.task_details.current_task.task_id == task_id):
                        self.task_details.update_task(task)
                break

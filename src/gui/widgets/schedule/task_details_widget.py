"""任务详情组件"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QFrame
)
from PySide6.QtCore import Qt, QSize
from datetime import datetime

from qfluentwidgets import (
    PushButton, CardWidget, StrongBodyLabel, BodyLabel,
    FluentIcon, TransparentToolButton, LineEdit
)
from src.core.scheduler import TaskType


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
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 详情表单
        details_form = QFormLayout()
        details_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
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
        config_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

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

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QButtonGroup, QFormLayout, QAbstractButton
)
from PySide6.QtCore import Qt, QDateTime, Signal
from typing import Optional, List

from qfluentwidgets import (  # type: ignore
    RadioButton, CheckBox, SpinBox, StrongBodyLabel, DateTimeEdit
)

from src.core.scheduler import TaskType


class ScheduleOptionsWidget(QWidget):
    """计划设置选项组件"""

    # 信号
    type_changed = Signal(int)  # 任务类型改变信号

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.days_checks: List[CheckBox] = []
        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        schedule_layout = QVBoxLayout(self)
        schedule_layout.setContentsMargins(15, 15, 15, 15)
        schedule_layout.setSpacing(15)

        # 添加卡片标题
        schedule_title = StrongBodyLabel("计划设置")  # type: ignore
        schedule_layout.addWidget(schedule_title)

        # 任务类型选择
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)

        self.type_group = QButtonGroup(self)

        self.one_time_radio = RadioButton("一次性")  # type: ignore
        self.type_group.addButton(self.one_time_radio, 0)
        type_layout.addWidget(self.one_time_radio)

        self.daily_radio = RadioButton("每天")  # type: ignore
        self.type_group.addButton(self.daily_radio, 1)
        type_layout.addWidget(self.daily_radio)

        self.weekly_radio = RadioButton("每周")  # type: ignore
        self.type_group.addButton(self.weekly_radio, 2)
        type_layout.addWidget(self.weekly_radio)

        self.interval_radio = RadioButton("间隔")  # type: ignore
        self.type_group.addButton(self.interval_radio, 3)
        type_layout.addWidget(self.interval_radio)

        schedule_layout.addLayout(type_layout)

        # 连接信号
        self.type_group.buttonClicked.connect(self._update_schedule_options)
        self.type_group.buttonClicked.connect(
            lambda btn: self.type_changed.emit(
                self.type_group.id(btn))  # type: ignore
        )

        # 时间设置区域
        self.schedule_options = QWidget()
        self.schedule_options_layout = QFormLayout(self.schedule_options)
        self.schedule_options_layout.setSpacing(12)
        self.schedule_options_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight)
        self.schedule_options_layout.setContentsMargins(0, 0, 0, 0)

        # 运行时间
        self.datetime_edit = DateTimeEdit(  # type: ignore
            QDateTime.currentDateTime().addSecs(3600))  # 默认一小时后
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.schedule_options_layout.addRow("运行时间:", self.datetime_edit)

        # 间隔设置（初始隐藏）
        self.interval_widget = QWidget()
        self.interval_layout = QHBoxLayout(self.interval_widget)
        self.interval_layout.setContentsMargins(0, 0, 0, 0)
        self.interval_layout.setSpacing(10)

        self.interval_hours = SpinBox()  # type: ignore
        self.interval_hours.setRange(0, 999)
        self.interval_hours.setValue(1)
        self.interval_hours.setSuffix(" 小时")
        self.interval_layout.addWidget(self.interval_hours)

        self.interval_minutes = SpinBox()  # type: ignore
        self.interval_minutes.setRange(0, 59)
        self.interval_minutes.setValue(0)
        self.interval_minutes.setSuffix(" 分钟")
        self.interval_layout.addWidget(self.interval_minutes)

        self.schedule_options_layout.addRow("间隔时间:", self.interval_widget)

        # 星期选择（初始隐藏）
        self.days_widget = QWidget()
        self.days_layout = QHBoxLayout(self.days_widget)
        self.days_layout.setContentsMargins(0, 0, 0, 0)
        self.days_layout.setSpacing(5)

        # self.days_checks initialized in __init__
        days_text = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for day_name in days_text:
            check = CheckBox(day_name)  # type: ignore
            self.days_checks.append(check)
            self.days_layout.addWidget(check)

        self.schedule_options_layout.addRow("星期几:", self.days_widget)

        schedule_layout.addWidget(self.schedule_options)

        # 初始化UI状态
        self.one_time_radio.setChecked(True)
        self._update_schedule_options(self.one_time_radio)

    def _update_schedule_options(self, button: QAbstractButton):
        """根据选择的任务类型更新界面"""
        # 隐藏所有特定选项
        self.interval_widget.setVisible(False)
        self.days_widget.setVisible(False)

        if button == self.one_time_radio:
            # 一次性任务
            # 仅显示日期时间
            self.datetime_edit.setVisible(True)
            # 恢复日期时间显示
            self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        elif button == self.daily_radio:
            # 每日任务
            # 显示时间设置
            self.datetime_edit.setVisible(True)
            # 设置日期不可见
            self.datetime_edit.setDisplayFormat("HH:mm:ss")

        elif button == self.weekly_radio:
            # 每周任务
            # 显示时间设置和星期选择
            self.datetime_edit.setVisible(True)
            self.days_widget.setVisible(True)
            # 设置日期不可见
            self.datetime_edit.setDisplayFormat("HH:mm:ss")

        elif button == self.interval_radio:
            # 间隔任务
            # 显示间隔设置
            self.datetime_edit.setVisible(True)
            self.interval_widget.setVisible(True)
            # 恢复日期时间显示
            self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

    def get_task_type(self) -> TaskType:
        """获取任务类型"""
        if self.one_time_radio.isChecked():
            return TaskType.ONE_TIME
        elif self.daily_radio.isChecked():
            return TaskType.DAILY
        elif self.weekly_radio.isChecked():
            return TaskType.WEEKLY
        elif self.interval_radio.isChecked():
            return TaskType.INTERVAL
        return TaskType.ONE_TIME  # 默认为一次性任务

    def get_first_run_time(self) -> QDateTime:
        """获取首次运行时间"""
        return self.datetime_edit.dateTime()

    def get_interval_seconds(self) -> int:
        """获取间隔时间（秒）"""
        if self.get_task_type() == TaskType.INTERVAL:
            hours = self.interval_hours.value()
            minutes = self.interval_minutes.value()
            return hours * 3600 + minutes * 60
        return 0

    def get_weekly_days(self) -> List[int]:
        """获取每周哪几天运行，返回日期索引列表（0=周一）"""
        days_indices: List[int] = []
        if self.get_task_type() == TaskType.WEEKLY:
            for i, check in enumerate(self.days_checks):
                if check.isChecked():
                    days_indices.append(i)  # 0表示周一
        return days_indices

    def validate(self) -> bool:
        """验证输入"""
        if self.weekly_radio.isChecked():
            # 检查是否选择了至少一天
            return any(check.isChecked() for check in self.days_checks)
        return True

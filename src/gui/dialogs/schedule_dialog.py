from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QButtonGroup,
    QFormLayout, QAbstractItemView, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QDateTime, Signal, Slot
from datetime import datetime, timedelta
import logging

from qfluentwidgets import (
    LineEdit, PushButton, RadioButton, CheckBox,
    SpinBox, ComboBox, CardWidget, StrongBodyLabel, BodyLabel,
    DateTimeEdit, SubtitleLabel, FluentIcon, InfoBar,
    InfoBarPosition, TransparentGroupBox, SimpleCardWidget
)

from src.core.scheduler import SchedulerTask, TaskType

logger = logging.getLogger(__name__)


class ScheduleDialog(QDialog):
    """计划任务设置对话框"""

    # 信号定义
    task_created = Signal(object)  # 任务对象

    def __init__(self, settings, download_data=None, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.download_data = download_data or {}

        self.setWindowTitle("计划下载任务")
        self.setMinimumSize(550, 480)
        self.resize(550, 480)
        self.setWindowIcon(FluentIcon.CALENDAR.icon())

        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        # 标题
        self.title_label = SubtitleLabel("计划下载任务")
        main_layout.addWidget(self.title_label)

        # 任务信息
        info_card = CardWidget()
        info_layout = QFormLayout()
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(12)
        info_layout.setLabelAlignment(Qt.AlignRight)

        # 添加卡片标题
        info_title = StrongBodyLabel("任务信息")
        info_layout.addRow(info_title)

        # 任务名称
        self.name_input = LineEdit()
        self.name_input.setPlaceholderText("输入任务名称")
        info_layout.addRow("任务名称:", self.name_input)

        info_card.setLayout(info_layout)
        main_layout.addWidget(info_card)

        # 计划选项
        schedule_card = CardWidget()
        schedule_layout = QVBoxLayout()
        schedule_layout.setContentsMargins(15, 15, 15, 15)
        schedule_layout.setSpacing(15)

        # 添加卡片标题
        schedule_title = StrongBodyLabel("计划设置")
        schedule_layout.addWidget(schedule_title)

        # 任务类型选择
        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)

        self.type_group = QButtonGroup(self)

        self.one_time_radio = RadioButton("一次性")
        self.type_group.addButton(self.one_time_radio, 0)
        type_layout.addWidget(self.one_time_radio)

        self.daily_radio = RadioButton("每天")
        self.type_group.addButton(self.daily_radio, 1)
        type_layout.addWidget(self.daily_radio)

        self.weekly_radio = RadioButton("每周")
        self.type_group.addButton(self.weekly_radio, 2)
        type_layout.addWidget(self.weekly_radio)

        self.interval_radio = RadioButton("间隔")
        self.type_group.addButton(self.interval_radio, 3)
        type_layout.addWidget(self.interval_radio)

        schedule_layout.addLayout(type_layout)

        # 连接信号
        self.type_group.buttonClicked.connect(self._update_schedule_options)

        # 时间设置区域
        self.schedule_options = QWidget()
        self.schedule_options_layout = QFormLayout(self.schedule_options)
        self.schedule_options_layout.setSpacing(12)
        self.schedule_options_layout.setLabelAlignment(Qt.AlignRight)

        # 运行时间
        self.datetime_edit = DateTimeEdit(
            QDateTime.currentDateTime().addSecs(3600))  # 默认一小时后
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_edit.setCursor(Qt.PointingHandCursor)
        self.schedule_options_layout.addRow("运行时间:", self.datetime_edit)

        # 间隔设置（初始隐藏）
        self.interval_widget = QWidget()
        self.interval_layout = QHBoxLayout(self.interval_widget)
        self.interval_layout.setContentsMargins(0, 0, 0, 0)
        self.interval_layout.setSpacing(10)

        self.interval_hours = SpinBox()
        self.interval_hours.setRange(0, 999)
        self.interval_hours.setValue(1)
        self.interval_hours.setSuffix(" 小时")
        self.interval_layout.addWidget(self.interval_hours)

        self.interval_minutes = SpinBox()
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

        self.days_checks = []
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day in enumerate(days):
            check = CheckBox(day)
            self.days_checks.append(check)
            self.days_layout.addWidget(check)

        self.schedule_options_layout.addRow("星期几:", self.days_widget)

        schedule_layout.addWidget(self.schedule_options)

        # 任务选项
        task_options_layout = QFormLayout()
        task_options_layout.setLabelAlignment(Qt.AlignRight)
        task_options_layout.setSpacing(12)

        task_option_title = StrongBodyLabel("任务选项")
        task_options_layout.addRow(task_option_title)

        # 任务优先级
        self.priority_combo = ComboBox()
        self.priority_combo.addItem("高", "high")
        self.priority_combo.addItem("中", "normal")
        self.priority_combo.addItem("低", "low")
        self.priority_combo.setCurrentIndex(1)  # 默认选中"中"
        task_options_layout.addRow("任务优先级:", self.priority_combo)

        # 完成后通知
        self.notify_check = CheckBox("完成后发送通知")
        self.notify_check.setChecked(True)
        task_options_layout.addRow("", self.notify_check)

        schedule_layout.addLayout(task_options_layout)

        schedule_card.setLayout(schedule_layout)
        main_layout.addWidget(schedule_card)

        # 使用标准按钮盒
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("确定")
        self.button_box.button(QDialogButtonBox.Ok).setIcon(FluentIcon.ACCEPT)
        self.button_box.button(QDialogButtonBox.Cancel).setText("取消")
        self.button_box.button(
            QDialogButtonBox.Cancel).setIcon(FluentIcon.CANCEL)

        # 连接按钮信号
        self.button_box.accepted.connect(self._on_ok)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

        # 初始化UI状态
        self.one_time_radio.setChecked(True)
        self._update_schedule_options(self.one_time_radio)

        # 填充数据
        self._fill_download_data()

    def _update_schedule_options(self, button):
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

    def _fill_download_data(self):
        """填充下载任务数据"""
        if not self.download_data:
            return

        # 设置任务名称
        if "name" in self.download_data:
            self.name_input.setText(self.download_data["name"])

    def _on_ok(self):
        """确定按钮点击"""
        # 验证输入
        if not self.name_input.text():
            InfoBar.error(
                title="输入错误",
                content="请输入任务名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if self.weekly_radio.isChecked():
            # 检查是否选择了至少一天
            if not any(check.isChecked() for check in self.days_checks):
                InfoBar.error(
                    title="输入错误",
                    content="请至少选择一天",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                return

        # 创建任务
        self._create_task()

        # 接受对话框
        self.accept()

    def _create_task(self):
        """创建计划任务"""
        try:
            # 获取任务类型
            task_type = None
            if self.one_time_radio.isChecked():
                task_type = TaskType.ONE_TIME
            elif self.daily_radio.isChecked():
                task_type = TaskType.DAILY
            elif self.weekly_radio.isChecked():
                task_type = TaskType.WEEKLY
            elif self.interval_radio.isChecked():
                task_type = TaskType.INTERVAL

            # 获取运行时间
            first_run = self.datetime_edit.dateTime().toPython()

            # 获取其他设置
            interval = 0
            if task_type == TaskType.INTERVAL:
                # 计算间隔秒数
                hours = self.interval_hours.value()
                minutes = self.interval_minutes.value()
                interval = hours * 3600 + minutes * 60

            # 获取星期设置
            days = []
            if task_type == TaskType.WEEKLY:
                for i, check in enumerate(self.days_checks):
                    if check.isChecked():
                        days.append(i)  # 0表示周一

            # 准备任务数据
            task_data = self.download_data.copy()
            task_data["handler_type"] = "download"  # 指示这是下载任务
            task_data["notify"] = self.notify_check.isChecked()
            task_data["priority"] = self.priority_combo.currentData()

            # 创建任务对象
            task = SchedulerTask(
                name=self.name_input.text(),
                task_type=task_type,
                data=task_data,
                first_run=first_run,
                interval=interval,
                days=days,
                enabled=True
            )

            # 发出任务创建信号
            self.task_created.emit(task)

            # 显示成功消息
            InfoBar.success(
                title="任务创建成功",
                content=f"已成功创建计划任务: {task.name}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )

            logger.info(f"已创建计划任务: {task.name}")

        except Exception as e:
            logger.error(f"创建计划任务出错: {e}")
            import traceback
            traceback.print_exc()

            InfoBar.error(
                title="创建任务失败",
                content=f"创建任务出错: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

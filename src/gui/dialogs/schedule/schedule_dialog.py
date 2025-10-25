from PySide6.QtWidgets import (
    QVBoxLayout, QDialog, QDialogButtonBox, QWidget
)
from PySide6.QtCore import Qt, Signal, QDateTime
from PySide6.QtGui import QIcon
import logging
from typing import Optional, Dict, Any
import datetime

from qfluentwidgets import (
    CardWidget, SubtitleLabel, FluentIcon as FIF, InfoBar,
    InfoBarPosition
)

from src.core.scheduler import SchedulerTask, TaskType
from .task_info_widget import TaskInfoWidget
from .schedule_options_widget import ScheduleOptionsWidget
from .task_options_widget import TaskOptionsWidget

logger = logging.getLogger(__name__)


class ScheduleDialog(QDialog):
    """计划任务设置对话框"""

    # 信号定义
    task_created = Signal(SchedulerTask)  # 任务对象

    def __init__(self, settings: Any, download_data: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.settings = settings
        self.download_data: Dict[str, Any] = download_data or {}

        self.setWindowTitle("计划下载任务")
        self.setMinimumSize(550, 480)
        self.resize(550, 480)
        self.setWindowIcon(FIF.CALENDAR.icon())

        self._create_ui()

    def _create_ui(self) -> None:
        """创建界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        # 标题
        self.title_label = SubtitleLabel("计划下载任务")
        main_layout.addWidget(self.title_label)

        # 任务信息组件
        self.task_info_widget = TaskInfoWidget(self)
        main_layout.addWidget(self.task_info_widget)

        # 计划设置组件
        self.schedule_card = CardWidget(self)
        schedule_layout = QVBoxLayout(self.schedule_card)
        schedule_layout.setContentsMargins(0, 0, 0, 0)

        # 计划选项组件
        self.schedule_options_widget = ScheduleOptionsWidget(self)
        schedule_layout.addWidget(self.schedule_options_widget)

        # 任务选项组件
        self.task_options_widget = TaskOptionsWidget(self)
        schedule_layout.addWidget(self.task_options_widget)

        main_layout.addWidget(self.schedule_card)

        # 使用标准按钮盒
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("确定")
            ok_button.setIcon(FIF.ACCEPT.icon())

        cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel)
        if cancel_button:
            cancel_button.setText("取消")
            cancel_button.setIcon(FIF.CANCEL.icon())

        # 连接按钮信号
        self.button_box.accepted.connect(self._on_ok)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

        # 填充数据
        self._fill_download_data()

    def _fill_download_data(self) -> None:
        """填充下载任务数据"""
        if not self.download_data:
            return

        # 设置任务名称
        if "name" in self.download_data:
            name_value = self.download_data.get("name")
            if isinstance(name_value, str):
                self.task_info_widget.set_task_name(name_value)

    def _on_ok(self) -> None:
        """确定按钮点击"""
        # 验证输入
        if not self.task_info_widget.get_task_name():
            InfoBar.error(
                title="输入错误",
                content="请输入任务名称",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if not self.schedule_options_widget.validate():
            InfoBar.error(
                title="输入错误",
                content="请至少选择一天",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        # 创建任务
        self._create_task()

    def _create_task(self) -> None:
        """创建计划任务"""
        try:
            # 获取任务类型
            task_type: TaskType = self.schedule_options_widget.get_task_type()

            # 获取运行时间
            first_run_qdt: QDateTime = self.schedule_options_widget.get_first_run_time()
            first_run_dt: Optional[datetime.datetime] = None
            if first_run_qdt.isValid():
                # Explicitly cast to datetime since toPython() returns generic object
                first_run_dt = datetime.datetime.fromisoformat(
                    first_run_qdt.toString(Qt.DateFormat.ISODate)
                )

            # 获取间隔时间
            interval: int = self.schedule_options_widget.get_interval_seconds()

            # 获取星期设置
            days: list[int] = self.schedule_options_widget.get_weekly_days()

            # 准备任务数据
            task_data_copy: Dict[str, Any] = self.download_data.copy()
            task_data_copy["handler_type"] = "download"  # 指示这是下载任务
            task_data_copy["notify"] = self.task_options_widget.get_notify()
            task_data_copy["priority"] = self.task_options_widget.get_priority()

            # 创建任务对象
            task = SchedulerTask(
                name=self.task_info_widget.get_task_name(),
                task_type=task_type,
                data=task_data_copy,
                first_run=first_run_dt,
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
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )

            logger.info(f"已创建计划任务: {task.name}")
            # 接受对话框, 移到_on_ok的末尾，确保只有成功创建任务才关闭
            self.accept()

        except Exception as e:
            logger.error(f"创建计划任务出错: {e}")
            import traceback
            traceback.print_exc()

            InfoBar.error(
                title="创建任务失败",
                content=f"创建任务出错: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

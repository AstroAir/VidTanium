from PySide6.QtWidgets import (
    QVBoxLayout, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, Slot
import logging

from qfluentwidgets import (
    CardWidget, SubtitleLabel, FluentIcon, InfoBar,
    InfoBarPosition
)

from src.core.scheduler import SchedulerTask
from .task_info_widget import TaskInfoWidget
from .schedule_options_widget import ScheduleOptionsWidget
from .task_options_widget import TaskOptionsWidget

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

        # 任务信息组件
        self.task_info_widget = TaskInfoWidget()
        main_layout.addWidget(self.task_info_widget)

        # 计划设置组件
        self.schedule_card = CardWidget()
        schedule_layout = QVBoxLayout(self.schedule_card)
        schedule_layout.setContentsMargins(0, 0, 0, 0)
        
        # 计划选项组件
        self.schedule_options_widget = ScheduleOptionsWidget()
        schedule_layout.addWidget(self.schedule_options_widget)
        
        # 任务选项组件
        self.task_options_widget = TaskOptionsWidget()
        schedule_layout.addWidget(self.task_options_widget)
        
        main_layout.addWidget(self.schedule_card)

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

        # 填充数据
        self._fill_download_data()

    def _fill_download_data(self):
        """填充下载任务数据"""
        if not self.download_data:
            return

        # 设置任务名称
        if "name" in self.download_data:
            self.task_info_widget.set_task_name(self.download_data["name"])

    def _on_ok(self):
        """确定按钮点击"""
        # 验证输入
        if not self.task_info_widget.get_task_name():
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

        if not self.schedule_options_widget.validate():
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
            task_type = self.schedule_options_widget.get_task_type()

            # 获取运行时间
            first_run = self.schedule_options_widget.get_first_run_time()

            # 获取间隔时间
            interval = self.schedule_options_widget.get_interval_seconds()

            # 获取星期设置
            days = self.schedule_options_widget.get_weekly_days()

            # 准备任务数据
            task_data = self.download_data.copy()
            task_data["handler_type"] = "download"  # 指示这是下载任务
            task_data["notify"] = self.task_options_widget.get_notify()
            task_data["priority"] = self.task_options_widget.get_priority()

            # 创建任务对象
            task = SchedulerTask(
                name=self.task_info_widget.get_task_name(),
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

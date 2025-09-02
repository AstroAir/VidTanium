"""计划任务工具栏组件"""

from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QSize

from qfluentwidgets import FluentIcon as FIF


class ScheduleToolbar(QToolBar):
    """计划任务工具栏"""

    # 信号定义
    new_task_clicked = Signal()
    refresh_clicked = Signal()
    enable_all_clicked = Signal()
    disable_all_clicked = Signal()
    view_details_toggled = Signal(bool)  # 是否查看详情

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """创建用户界面"""
        self.setIconSize(QSize(16, 16))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # 新建任务
        self.new_task_action = QAction(FIF.ADD.icon(), "新建计划", self)
        self.new_task_action.setToolTip("创建新的计划任务")
        self.new_task_action.triggered.connect(self.new_task_clicked)
        self.addAction(self.new_task_action)

        # 刷新按钮
        self.refresh_action = QAction(FIF.SYNC.icon(), "刷新", self)
        self.refresh_action.setToolTip("刷新任务列表")
        self.refresh_action.triggered.connect(self.refresh_clicked)
        self.addAction(self.refresh_action)

        self.addSeparator()

        # 批量操作按钮
        self.enable_all_action = QAction(FIF.PLAY.icon(), "全部启用", self)
        self.enable_all_action.triggered.connect(self.enable_all_clicked)
        self.addAction(self.enable_all_action)

        self.disable_all_action = QAction(
            FIF.PAUSE.icon(), "全部禁用", self)
        self.disable_all_action.triggered.connect(self.disable_all_clicked)
        self.addAction(self.disable_all_action)

        self.addSeparator()

        # 任务详情按钮
        self.view_details_action = QAction(
            FIF.INFO.icon(), "查看详情", self)
        self.view_details_action.setCheckable(True)
        self.view_details_action.triggered.connect(self.view_details_toggled)
        self.addAction(self.view_details_action)

    def set_details_checked(self, checked):
        """设置详情按钮的选中状态"""
        self.view_details_action.setChecked(checked)

    def update_locale(self, translations):
        """更新工具栏按钮的文本以适应当前语言环境"""
        self.new_task_action.setText(translations.get("new_task", "新建计划"))
        self.new_task_action.setToolTip(translations.get("new_task_tooltip", "创建新的计划任务"))
        self.refresh_action.setText(translations.get("refresh", "刷新"))
        self.refresh_action.setToolTip(translations.get("refresh_tooltip", "刷新任务列表"))
        self.enable_all_action.setText(translations.get("enable_all", "全部启用"))
        self.disable_all_action.setText(translations.get("disable_all", "全部禁用"))
        self.view_details_action.setText(translations.get("view_details", "查看详情"))

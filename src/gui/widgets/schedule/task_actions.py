"""任务操作按钮组件"""

from PySide6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import ToolButton, FluentIcon

class TaskActionButtons(QWidget):
    """任务操作按钮组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()
        self._connections = []  # 存储信号连接

    def _create_ui(self):
        """创建用户界面"""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

    def setup_for_task(self, task):
        """根据任务状态设置按钮"""
        # 清除当前所有按钮
        self._clear_layout()
        
        # 根据任务状态添加不同按钮
        if task.enabled:
            # 禁用按钮
            disable_button = ToolButton(FluentIcon.PAUSE)
            disable_button.setToolTip("禁用")
            self.layout.addWidget(disable_button)
            self.disable_button = disable_button
        else:
            # 启用按钮
            enable_button = ToolButton(FluentIcon.PLAY)
            enable_button.setToolTip("启用")
            self.layout.addWidget(enable_button)
            self.enable_button = enable_button

        # 运行按钮
        run_button = ToolButton(FluentIcon.PLAY_SOLID)
        run_button.setToolTip("立即执行")
        self.layout.addWidget(run_button)
        self.run_button = run_button

        # 详情按钮
        info_button = ToolButton(FluentIcon.INFO)
        info_button.setToolTip("查看详情")
        self.layout.addWidget(info_button)
        self.info_button = info_button

        # 删除按钮
        delete_button = ToolButton(FluentIcon.DELETE)
        delete_button.setToolTip("删除")
        self.layout.addWidget(delete_button)
        self.delete_button = delete_button

    def connect_buttons(self, task_id, enable_fn, disable_fn, run_fn, info_fn, delete_fn):
        """连接按钮信号到提供的函数"""
        self._clear_connections()

        if hasattr(self, 'enable_button'):
            self._connections.append(
                self.enable_button.clicked.connect(
                    lambda: enable_fn(task_id))
            )

        if hasattr(self, 'disable_button'):
            self._connections.append(
                self.disable_button.clicked.connect(
                    lambda: disable_fn(task_id))
            )

        self._connections.append(
            self.run_button.clicked.connect(
                lambda: run_fn(task_id))
        )

        self._connections.append(
            self.info_button.clicked.connect(
                lambda: info_fn(task_id))
        )

        self._connections.append(
            self.delete_button.clicked.connect(
                lambda: delete_fn(task_id))
        )

    def _clear_layout(self):
        """清除布局中的所有按钮"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _clear_connections(self):
        """清除所有信号连接"""
        for connection in self._connections:
            try:
                connection.disconnect()
            except:
                pass
        self._connections = []
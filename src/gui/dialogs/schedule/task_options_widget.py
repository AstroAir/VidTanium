from PySide6.QtWidgets import QFormLayout, QWidget
from PySide6.QtCore import Qt
from typing import Optional, Any

from qfluentwidgets import (  # type: ignore
    CheckBox, ComboBox, StrongBodyLabel
)


class TaskOptionsWidget(QWidget):
    """任务选项组件"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        task_options_layout = QFormLayout(self)
        task_options_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        task_options_layout.setSpacing(12)
        task_options_layout.setContentsMargins(0, 0, 0, 0)

        task_option_title = StrongBodyLabel("任务选项")  # type: ignore
        task_options_layout.addRow(task_option_title)

        # 任务优先级
        self.priority_combo = ComboBox()  # type: ignore
        self.priority_combo.addItem("高", userData="high")  # type: ignore
        self.priority_combo.addItem("中", userData="normal")  # type: ignore
        self.priority_combo.addItem("低", userData="low")  # type: ignore
        self.priority_combo.setCurrentIndex(1)  # 默认选中"中"
        task_options_layout.addRow("任务优先级:", self.priority_combo)

        # 完成后通知
        self.notify_check = CheckBox("完成后发送通知")  # type: ignore
        self.notify_check.setChecked(True)
        task_options_layout.addRow("", self.notify_check)

    def get_priority(self) -> Any:
        """获取优先级"""
        return self.priority_combo.currentData()  # type: ignore

    def get_notify(self) -> bool:
        """是否需要通知"""
        return self.notify_check.isChecked()

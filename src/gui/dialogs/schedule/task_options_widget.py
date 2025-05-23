from PySide6.QtWidgets import QFormLayout, QWidget
from PySide6.QtCore import Qt

from qfluentwidgets import (
    CheckBox, ComboBox, StrongBodyLabel
)

class TaskOptionsWidget(QWidget):
    """任务选项组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._create_ui()
        
    def _create_ui(self):
        """创建界面"""
        task_options_layout = QFormLayout(self)
        task_options_layout.setLabelAlignment(Qt.AlignRight)
        task_options_layout.setSpacing(12)
        task_options_layout.setContentsMargins(0, 0, 0, 0)

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

    def get_priority(self):
        """获取优先级"""
        return self.priority_combo.currentData()

    def get_notify(self):
        """是否需要通知"""
        return self.notify_check.isChecked()

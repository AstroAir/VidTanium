from PySide6.QtWidgets import QFormLayout, QWidget
from PySide6.QtCore import Qt
from typing import Optional

from qfluentwidgets import LineEdit, CardWidget, StrongBodyLabel


class TaskInfoWidget(CardWidget):
    """任务信息组件"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        info_layout = QFormLayout()
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(12)
        info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 添加卡片标题
        info_title = StrongBodyLabel("任务信息")
        info_layout.addRow(info_title)

        # 任务名称
        self.name_input = LineEdit()
        self.name_input.setPlaceholderText("输入任务名称")
        info_layout.addRow("任务名称:", self.name_input)

        self.setLayout(info_layout)

    def get_task_name(self) -> str:
        """获取任务名称"""
        return str(self.name_input.text())

    def set_task_name(self, name: str):
        """设置任务名称"""
        self.name_input.setText(name)

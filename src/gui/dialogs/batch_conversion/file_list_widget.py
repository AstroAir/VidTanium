from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QAbstractItemView,
    QFileDialog, QGroupBox
)
from PySide6.QtCore import Qt, Signal
# from PySide6.QtGui import QIcon # Unused import
import os
from typing import List, Optional

from qfluentwidgets import (  # type: ignore
    PushButton, FluentIcon, InfoBar, InfoBarPosition
)


class FileListWidget(QWidget):
    """文件列表组件，用于管理批量转换的输入文件"""

    # 文件列表变化信号
    file_list_changed = Signal(int)  # 参数: 文件数量

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.input_files: List[str] = []
        self._create_ui()

    def _create_ui(self):
        """创建文件列表界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 文件列表组
        files_group = QGroupBox("输入文件")
        files_layout = QVBoxLayout(files_group)
        files_layout.setContentsMargins(10, 15, 10, 10)

        # 文件列表
        self.files_list = QListWidget()
        self.files_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.files_list.setAlternatingRowColors(True)
        files_layout.addWidget(self.files_list, 1)

        # 文件按钮 - 水平布局，均匀分布按钮
        file_buttons_layout = QHBoxLayout()
        file_buttons_layout.setSpacing(8)

        self.add_files_button = PushButton("添加文件")
        self.add_files_button.setIcon(FluentIcon.ADD)
        self.add_files_button.clicked.connect(self._add_files)
        file_buttons_layout.addWidget(self.add_files_button)

        self.add_folder_button = PushButton("添加文件夹")
        self.add_folder_button.setIcon(FluentIcon.FOLDER)
        self.add_folder_button.clicked.connect(self._add_folder)
        file_buttons_layout.addWidget(self.add_folder_button)

        self.remove_files_button = PushButton("移除选中")
        self.remove_files_button.setIcon(FluentIcon.REMOVE)
        self.remove_files_button.clicked.connect(self._remove_selected_files)
        file_buttons_layout.addWidget(self.remove_files_button)

        self.clear_files_button = PushButton("清空全部")
        # Assuming FluentIcon.CLEAR is valid
        self.clear_files_button.setIcon(FluentIcon.BRUSH)
        self.clear_files_button.clicked.connect(self.clear_files)
        file_buttons_layout.addWidget(self.clear_files_button)

        files_layout.addLayout(file_buttons_layout)
        layout.addWidget(files_group)

    def _add_files(self):
        """添加文件到列表"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(
            "媒体文件 (*.mp4 *.mkv *.avi *.mov *.flv *.webm *.ts *.m4v *.3gp *.wmv)")

        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            for file in files:
                if file not in self.input_files:
                    self.input_files.append(file)
                    self.files_list.addItem(os.path.basename(file))
                    # 设置工具提示为完整路径
                    self.files_list.item(
                        self.files_list.count()-1).setToolTip(file)

            self._notify_file_list_changed()

    def _add_folder(self):
        """添加文件夹中的所有媒体文件"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择包含媒体文件的文件夹"
        )

        if folder:
            media_extensions = ['.mp4', '.mkv', '.avi', '.mov',
                                '.flv', '.webm', '.ts', '.m4v', '.3gp', '.wmv']

            # 记录原有文件数量
            original_count = len(self.input_files)

            # 获取文件夹中所有媒体文件
            for root, _, files in os.walk(folder):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext.lower() in media_extensions:
                        file_path = os.path.join(root, file)
                        if file_path not in self.input_files:
                            self.input_files.append(file_path)
                            self.files_list.addItem(os.path.basename(file))
                            # 设置工具提示为完整路径
                            self.files_list.item(
                                self.files_list.count()-1).setToolTip(file_path)

            # 计算新添加的文件数量
            added_files = len(self.input_files) - original_count

            self._notify_file_list_changed()

            InfoBar.success(  # type: ignore
                title="文件已添加",
                content=f"从文件夹中添加了 {added_files} 个媒体文件",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _remove_selected_files(self):
        """从列表中移除选定的文件"""
        selected_items = self.files_list.selectedItems()

        for item in selected_items:
            file_path = item.toolTip()  # Assuming toolTip stores the full path
            if file_path in self.input_files:
                self.input_files.remove(file_path)
            self.files_list.takeItem(self.files_list.row(item))

        self._notify_file_list_changed()

    def clear_files(self):
        """清空文件列表"""
        self.files_list.clear()
        self.input_files.clear()
        self._notify_file_list_changed()

    def _notify_file_list_changed(self):
        """发出文件列表变化信号"""
        self.file_list_changed.emit(len(self.input_files))

    def get_input_files(self) -> List[str]:
        """获取输入文件列表"""
        return self.input_files

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Signal

# 导入新的对话框实现
from src.gui.dialogs.batch_conversion.dialog import BatchConversionDialog as NewBatchConversionDialog


class BatchConversionDialog(QDialog):
    """批量媒体转换对话框 - 该类现在是一个包装器，使用重构后的组件"""

    # 处理完成时发出信号
    processing_completed = Signal(bool, str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        # 创建重构后的对话框
        self._dialog = NewBatchConversionDialog(settings, parent)

        # 转发信号
        self._dialog.processing_completed.connect(self.processing_completed)

        # 设置对话框属性
        self.setWindowTitle(self._dialog.windowTitle())
        self.setMinimumSize(self._dialog.minimumSize())
        self.setWindowIcon(self._dialog.windowIcon())

    def exec(self):
        """执行对话框"""
        self._dialog.show()
        return super().exec()
        
    def close(self):
        """关闭对话框"""
        self._dialog.close()
        super().close()

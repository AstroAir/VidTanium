"""批量URL导入对话框"""
import logging
from typing import Any, List, Optional
from PySide6.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QWidget
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

from qfluentwidgets import TabWidget, FluentIcon as FIF, SubtitleLabel

from .text_input_tab import TextInputTab
from .file_input_tab import FileInputTab
from .web_scraping_tab import WebScrapingTab
from .url_preview_widget import URLPreviewWidget  # 

logger = logging.getLogger(__name__)


class BatchURLDialog(QDialog):
    """批量URL导入对话框"""

    # 导入URL信号
    urls_imported = Signal(list)  # URL列表

    def __init__(self, settings: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.settings = settings
        self.urls: List[str] = []

        self.setWindowTitle("批量导入URL")
        self.setMinimumSize(750, 550)
        self.resize(750, 550)
        self.setWindowIcon(QIcon(":/images/link.png"))  # 假设有这个图标资源

        self._create_ui()
        self._connect_signals()

    def _create_ui(self) -> None:
        """创建界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        self.title_label = SubtitleLabel("批量导入URL")
        main_layout.addWidget(self.title_label)

        # 创建选项卡
        self.tabs = TabWidget()

        # 文本输入选项卡
        self.text_tab = TextInputTab(self)
        self.tabs.addTab(self.text_tab, "文本输入")

        # 文件选项卡
        self.file_tab = FileInputTab(self)
        self.tabs.addTab(self.file_tab, "从文件导入")

        # 网页抓取选项卡
        self.web_tab = WebScrapingTab(self.settings, self)
        self.tabs.addTab(self.web_tab, "从网页抓取")

        main_layout.addWidget(self.tabs)

        # URL列表预览
        self.url_preview_widget = URLPreviewWidget(self)
        main_layout.addWidget(self.url_preview_widget)

        # 添加标准按钮
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel)

        if ok_button:
            ok_button.setText("导入")
            ok_button.setIcon(QIcon(FIF.DOWNLOAD))
            ok_button.setEnabled(False)

        if cancel_button:
            cancel_button.setText("取消")

        # 连接按钮信号
        self.button_box.accepted.connect(self._import_urls)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

    def _connect_signals(self) -> None:
        """连接信号"""
        self.text_tab.urls_extracted.connect(self._update_url_preview)
        self.file_tab.urls_extracted.connect(self._update_url_preview)
        self.web_tab.urls_extracted.connect(self._update_url_preview)

    def _update_url_preview(self, urls: List[str]) -> None:
        """更新URL预览"""
        has_urls = self.url_preview_widget.update_urls(urls)
        self.urls = urls

        # 启用/禁用导入按钮
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setEnabled(has_urls)

    def _import_urls(self) -> None:
        """导入URL"""
        if not self.urls:
            return

        # 发出信号
        self.urls_imported.emit(self.urls)

        # 关闭对话框
        self.accept()

    def get_urls(self) -> List[str]:
        """获取导入的URL"""
        return self.urls

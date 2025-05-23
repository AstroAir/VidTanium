"""批量URL导入对话框"""
import logging
from PySide6.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from qfluentwidgets import TabWidget, FluentIcon, SubtitleLabel

from .text_input_tab import TextInputTab
from .file_input_tab import FileInputTab
from .web_scraping_tab import WebScrapingTab
from .url_preview_widget import URLPreviewWidget

logger = logging.getLogger(__name__)


class BatchURLDialog(QDialog):
    """批量URL导入对话框"""

    # 导入URL信号
    urls_imported = Signal(list)  # URL列表

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.urls = []

        self.setWindowTitle("批量导入URL")
        self.setMinimumSize(750, 550)
        self.resize(750, 550)
        self.setWindowIcon(QIcon(":/images/link.png"))  # 假设有这个图标资源

        self._create_ui()
        self._connect_signals()

    def _create_ui(self):
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
        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.button_box.button(QDialogButtonBox.Ok).setText("导入")
        self.button_box.button(QDialogButtonBox.Ok).setIcon(FluentIcon.DOWNLOAD)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.Cancel).setText("取消")
        
        # 连接按钮信号
        self.button_box.accepted.connect(self._import_urls)
        self.button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(self.button_box)

    def _connect_signals(self):
        """连接信号"""
        self.text_tab.urls_extracted.connect(self._update_url_preview)
        self.file_tab.urls_extracted.connect(self._update_url_preview)
        self.web_tab.urls_extracted.connect(self._update_url_preview)

    def _update_url_preview(self, urls):
        """更新URL预览"""
        has_urls = self.url_preview_widget.update_urls(urls)
        self.urls = urls
        
        # 启用/禁用导入按钮
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(has_urls)

    def _import_urls(self):
        """导入URL"""
        if not self.urls:
            return

        # 发出信号
        self.urls_imported.emit(self.urls)

        # 关闭对话框
        self.accept()

    def get_urls(self):
        """获取导入的URL"""
        return self.urls
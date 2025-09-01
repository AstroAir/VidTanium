from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QDialog, QScrollArea, QFormLayout, QApplication
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
import os
import logging

from qfluentwidgets import (
    # Navigation
    Pivot,
    # Buttons
    PushButton, PrimaryPushButton,
    # Input Components
    LineEdit, CheckBox, TextEdit, SpinBox, ComboBox,
    # Cards and Layout
    ElevatedCardWidget,
    # Labels and Text
    BodyLabel, SubtitleLabel, StrongBodyLabel,
    # Progress and Feedback
    ProgressBar, InfoBar, InfoBarPosition,
    # Icons
    FluentIcon as FIF
)

from src.core.url_extractor import URLExtractor
from src.gui.utils.i18n import tr

logger = logging.getLogger(__name__)


class BatchURLDialog(QDialog):
    """批量URL导入对话框"""

    # 导入URL信号
    urls_imported = Signal(list)  # URL列表

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.urls = []

        self.setWindowTitle(tr("batch_url_dialog.title"))
        self.setMinimumSize(750, 550)
        self.resize(750, 550)
        self.setWindowIcon(QIcon(":/images/link.png"))  # 假设有这个图标资源

        self._create_ui()

    def _create_ui(self):
        """创建界面（优化布局和控件尺寸）"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(24, 24, 24, 24)        # 标题
        self.title_label = SubtitleLabel(tr("batch_url_dialog.subtitle"))
        self.title_label.setStyleSheet("font-size: 22px;")
        main_layout.addWidget(self.title_label)

        # 创建选项卡 - 使用Pivot而不是TabWidget
        self.tabs = Pivot(self)
        self.tabs.setFixedHeight(48)        # 文本输入选项卡
        self.text_tab = QWidget()
        self._create_text_tab()
        self.tabs.addItem(
            routeKey="text",
            text=tr("batch_url_dialog.tabs.text_input"),
            onClick=lambda: self._switch_tab(self.text_tab)
        )

        # 文件选项卡
        self.file_tab = QWidget()
        self._create_file_tab()
        self.tabs.addItem(
            routeKey="file",
            text=tr("batch_url_dialog.tabs.from_file"),
            onClick=lambda: self._switch_tab(self.file_tab)
        )

        # 网页抓取选项卡
        self.web_tab = QWidget()
        self._create_web_tab()
        self.tabs.addItem(
            routeKey="web",
            text=tr("batch_url_dialog.tabs.from_web"),
            onClick=lambda: self._switch_tab(self.web_tab)
        )

        main_layout.addWidget(self.tabs)

        # 创建堆叠布局来容纳不同的选项卡内容，外层加滚动区域
        self.stacked_widget = QWidget()
        self.stacked_layout = QVBoxLayout(self.stacked_widget)
        self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_layout.setSpacing(0)
        # 默认显示文本输入选项卡
        self.stacked_layout.addWidget(self.text_tab)
        self.current_tab = self.text_tab

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.stacked_widget)
        main_layout.addWidget(self.scroll_area, 1)

        # URL列表预览
        preview_card = ElevatedCardWidget(self)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(18, 18, 18, 18)
        preview_layout.setSpacing(10)        # 预览标题
        preview_title = StrongBodyLabel(tr("batch_url_dialog.preview.title"))
        preview_layout.addWidget(preview_title)

        self.url_preview = TextEdit()
        self.url_preview.setReadOnly(True)
        self.url_preview.setMinimumHeight(100)
        self.url_preview.setMaximumHeight(180)
        self.url_preview.setPlaceholderText(
            tr("batch_url_dialog.preview.empty"))
        preview_layout.addWidget(self.url_preview)

        # URL统计
        self.url_count_label = BodyLabel(
            tr("batch_url_dialog.preview.count").format(count=0))
        preview_layout.addWidget(self.url_count_label)

        main_layout.addWidget(preview_card)

        # Fluent 风格按钮替换 QDialogButtonBox
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()

        self.cancel_button = PushButton(tr("batch_url_dialog.buttons.cancel"))
        self.cancel_button.setIcon(FIF.CANCEL)
        self.cancel_button.setFixedSize(100, 36)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.ok_button = PrimaryPushButton(
            tr("batch_url_dialog.buttons.import"))
        self.ok_button.setIcon(FIF.DOWNLOAD)
        self.ok_button.setFixedSize(120, 36)
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self._import_urls)
        button_layout.addWidget(self.ok_button)

        main_layout.addLayout(button_layout)

    def _switch_tab(self, tab_widget):
        """切换选项卡"""
        if self.current_tab:
            self.stacked_layout.removeWidget(self.current_tab)
            self.current_tab.setParent(None)

        self.stacked_layout.addWidget(tab_widget)
        self.current_tab = tab_widget

    def _create_text_tab(self):
        layout = QVBoxLayout(self.text_tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        hint_label = BodyLabel(tr("batch_url_dialog.text_tab.title"))
        layout.addWidget(hint_label)

        self.text_input = TextEdit()
        self.text_input.setPlaceholderText(
            tr("batch_url_dialog.text_tab.placeholder"))
        self.text_input.setMinimumHeight(100)
        self.text_input.textChanged.connect(self._process_text_input)
        layout.addWidget(self.text_input)

        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 5, 0, 5)
        buttons_layout.setSpacing(10)
        self.paste_button = PushButton(tr("batch_url_dialog.text_tab.paste"))
        self.paste_button.setIcon(FIF.COPY.icon())
        self.paste_button.clicked.connect(self._paste_from_clipboard)
        buttons_layout.addWidget(self.paste_button)
        self.clear_button = PushButton(tr("batch_url_dialog.text_tab.clear"))
        self.clear_button.setIcon(FIF.DELETE.icon())
        self.clear_button.clicked.connect(self._clear_text)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # 选项
        options_card = ElevatedCardWidget(self)
        options_layout = QFormLayout(options_card)
        options_layout.setContentsMargins(15, 10, 15, 10)
        options_layout.setSpacing(10)
        options_title = StrongBodyLabel("过滤选项")
        options_layout.addRow(options_title)
        self.regex_input = LineEdit()
        self.regex_input.setPlaceholderText("例如: .*\\.mp4|.*\\.m3u8")
        self.regex_input.textChanged.connect(self._process_text_input)
        options_layout.addRow("正则表达式过滤:", self.regex_input)
        layout.addWidget(options_card)
        layout.addStretch()

    def _create_file_tab(self):
        layout = QVBoxLayout(self.file_tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        hint_label = BodyLabel("从文本文件导入URL:")
        layout.addWidget(hint_label)
        file_card = ElevatedCardWidget(self)
        file_card_layout = QVBoxLayout(file_card)
        file_card_layout.setContentsMargins(15, 15, 15, 15)
        file_card_layout.setSpacing(10)
        file_layout = QHBoxLayout()
        self.file_path_input = LineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("选择文件...")
        file_layout.addWidget(self.file_path_input)
        self.browse_button = PushButton("浏览...")
        self.browse_button.setIcon(FIF.FOLDER.icon())
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)
        file_card_layout.addLayout(file_layout)
        self.load_file_button = PushButton("加载文件")
        self.load_file_button.setIcon(FIF.DOCUMENT.icon())
        self.load_file_button.setEnabled(False)
        self.load_file_button.clicked.connect(self._load_file)
        file_card_layout.addWidget(self.load_file_button)
        layout.addWidget(file_card)
        options_card = ElevatedCardWidget(self)
        options_layout = QFormLayout(options_card)
        options_layout.setContentsMargins(15, 10, 15, 10)
        options_layout.setSpacing(10)
        options_title = StrongBodyLabel("过滤选项")
        options_layout.addRow(options_title)
        self.file_regex_input = LineEdit()
        self.file_regex_input.setPlaceholderText("例如: .*\\.mp4|.*\\.m3u8")
        options_layout.addRow("正则表达式过滤:", self.file_regex_input)
        layout.addWidget(options_card)
        layout.addStretch()

    def _create_web_tab(self):
        layout = QVBoxLayout(self.web_tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        hint_label = BodyLabel("从网页中抓取媒体URL:")
        layout.addWidget(hint_label)
        url_card = ElevatedCardWidget(self)
        url_card_layout = QVBoxLayout(url_card)
        url_card_layout.setContentsMargins(15, 15, 15, 15)
        url_card_layout.setSpacing(10)
        url_layout = QFormLayout()
        url_layout.setSpacing(10)
        self.web_url_input = LineEdit()
        self.web_url_input.setPlaceholderText("输入网页URL...")
        url_layout.addRow("网页URL:", self.web_url_input)
        url_card_layout.addLayout(url_layout)
        self.fetch_button = PushButton("抓取URL")
        self.fetch_button.setIcon(FIF.GLOBE.icon())
        self.fetch_button.clicked.connect(self._fetch_urls_from_web)
        url_card_layout.addWidget(self.fetch_button)
        layout.addWidget(url_card)
        options_card = ElevatedCardWidget(self)
        options_layout = QFormLayout(options_card)
        options_layout.setContentsMargins(15, 10, 15, 10)
        options_layout.setSpacing(10)
        options_title = StrongBodyLabel("抓取选项")
        options_layout.addRow(options_title)
        media_layout = QVBoxLayout()
        media_layout.setSpacing(5)
        self.video_check = CheckBox("视频 (.mp4, .flv, .avi, 等)")
        self.video_check.setChecked(True)
        media_layout.addWidget(self.video_check)
        self.m3u8_check = CheckBox("HLS流 (.m3u8)")
        self.m3u8_check.setChecked(True)
        media_layout.addWidget(self.m3u8_check)
        self.audio_check = CheckBox("音频 (.mp3, .aac, .wav, 等)")
        media_layout.addWidget(self.audio_check)
        options_layout.addRow("媒体类型:", media_layout)
        self.depth_spin = SpinBox()
        self.depth_spin.setRange(0, 3)
        self.depth_spin.setValue(0)
        self.depth_spin.setToolTip("抓取链接页面的深度 (0表示只抓取当前页面)")
        options_layout.addRow("递归深度:", self.depth_spin)
        layout.addWidget(options_card)
        layout.addStretch()

    def _paste_from_clipboard(self):
        """从剪贴板粘贴"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.text_input.setText(text)
            InfoBar.success(
                title="粘贴成功",
                content="已从剪贴板粘贴文本",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            InfoBar.warning(
                title="粘贴失败",
                content="剪贴板中没有文本内容",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def _clear_text(self):
        """清空文本框"""
        self.text_input.clear()

        InfoBar.success(
            title="已清空",
            content="文本框内容已清空",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def _browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文本文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            self.file_path_input.setText(file_path)
            self.load_file_button.setEnabled(True)

    def _load_file(self):
        """加载文件"""
        file_path = self.file_path_input.text()
        if not file_path or not os.path.exists(file_path):
            return

        pattern = self.file_regex_input.text() if self.file_regex_input.text() else None

        try:
            urls = URLExtractor.extract_urls_from_file(file_path, pattern)
            self._update_url_preview(urls)

            InfoBar.success(
                title="加载成功",
                content=f"从文件中提取了 {len(urls)} 个URL",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            InfoBar.error(
                title="加载失败",
                content=f"加载文件出错: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _process_text_input(self):
        """处理文本输入"""
        text = self.text_input.toPlainText()
        pattern = self.regex_input.text() if self.regex_input.text() else None

        urls = URLExtractor.extract_urls_from_text(text, pattern)
        self._update_url_preview(urls)

    def _fetch_urls_from_web(self):
        """从网页抓取URL"""
        url = self.web_url_input.text().strip()
        if not url:
            InfoBar.warning(
                title="输入错误",
                content="请输入网页URL",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 验证URL
        if not URLExtractor.validate_url(url):
            InfoBar.error(
                title="输入错误",
                content="请输入有效的URL",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 确定媒体扩展名
        extensions = []
        if self.video_check.isChecked():
            extensions.extend(['.mp4', '.flv', '.avi', '.mov', '.wmv', '.mkv'])
        if self.m3u8_check.isChecked():
            extensions.append('.m3u8')
        if self.audio_check.isChecked():
            extensions.extend(['.mp3', '.aac', '.wav', '.ogg'])

        if not extensions:
            InfoBar.warning(
                title="选择错误",
                content="请至少选择一种媒体类型",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 显示进度条
        progress = ProgressBar(self)
        progress.setTextVisible(True)
        progress.setFixedHeight(30)
        progress.setRange(0, 0)  # 不确定进度
        progress.setFormat("正在抓取URL...")

        # 添加到URL卡片的底部
        url_card = self.web_tab.findChild(ElevatedCardWidget)
        if url_card:
            url_card_layout = url_card.layout()
            if url_card_layout:
                url_card_layout.addWidget(progress)

        # 禁用抓取按钮
        self.fetch_button.setEnabled(False)

        try:
            # 获取用户代理设置
            user_agent = self.settings.get("advanced", "user_agent", "")
            headers = {"User-Agent": user_agent} if user_agent else None

            # 抓取URL
            urls = URLExtractor.extract_media_urls_from_webpage(
                url, headers, extensions)

            # 移除进度条并恢复按钮
            url_card = self.web_tab.findChild(ElevatedCardWidget)
            if url_card:
                layout = url_card.layout()
                if layout:
                    layout.removeWidget(progress)
            progress.deleteLater()
            self.fetch_button.setEnabled(True)

            # 更新URL预览
            self._update_url_preview(urls)

            InfoBar.success(
                title="抓取成功",
                content=f"从网页中提取了 {len(urls)} 个URL",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

        except Exception as e:
            # 移除进度条并恢复按钮
            url_card = self.web_tab.findChild(ElevatedCardWidget)
            if url_card:
                layout = url_card.layout()
                if layout:
                    layout.removeWidget(progress)
            progress.deleteLater()
            self.fetch_button.setEnabled(True)

            InfoBar.error(
                title="抓取失败",
                content=f"从网页抓取URL出错: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _update_url_preview(self, urls):
        """更新URL预览"""
        self.urls = urls
        preview_text = "\n".join(urls)
        self.url_preview.setText(preview_text)
        self.url_count_label.setText(f"已检测到 {len(urls)} 个URL")
        self.ok_button.setEnabled(len(urls) > 0)

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

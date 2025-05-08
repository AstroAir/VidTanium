from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QFileDialog, QDialog, QDialogButtonBox,
    QApplication, QFormLayout, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
import os
import logging

from qfluentwidgets import (
    TabWidget, PushButton, LineEdit, CheckBox,
    TextEdit, SpinBox, ComboBox, CardWidget, BodyLabel,
    SubtitleLabel, StrongBodyLabel, ProgressBar, FluentIcon,
    InfoBarPosition, SimpleCardWidget, InfoBar
)

from src.core.url_extractor import URLExtractor

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
        self.text_tab = QWidget()
        self._create_text_tab()
        self.tabs.addTab(self.text_tab, "文本输入")

        # 文件选项卡
        self.file_tab = QWidget()
        self._create_file_tab()
        self.tabs.addTab(self.file_tab, "从文件导入")

        # 网页抓取选项卡
        self.web_tab = QWidget()
        self._create_web_tab()
        self.tabs.addTab(self.web_tab, "从网页抓取")

        main_layout.addWidget(self.tabs)

        # URL列表预览
        preview_card = CardWidget(self)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(15, 15, 15, 15)

        # 预览标题
        preview_title = StrongBodyLabel("URL预览")
        preview_layout.addWidget(preview_title)

        self.url_preview = TextEdit()
        self.url_preview.setReadOnly(True)
        self.url_preview.setFixedHeight(120)
        self.url_preview.setPlaceholderText("待导入的URL将显示在这里...")
        preview_layout.addWidget(self.url_preview)

        # URL统计
        self.url_count_label = BodyLabel("已检测到 0 个URL")
        preview_layout.addWidget(self.url_count_label)

        main_layout.addWidget(preview_card)

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

    def _create_text_tab(self):
        """创建文本输入选项卡"""
        layout = QVBoxLayout(self.text_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 说明文本
        hint_label = BodyLabel("请输入要导入的URL，每行一个:")
        layout.addWidget(hint_label)

        # 文本输入区域
        self.text_input = TextEdit()
        self.text_input.setPlaceholderText("在此粘贴URL...")
        self.text_input.textChanged.connect(self._process_text_input)
        layout.addWidget(self.text_input)

        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 5, 0, 5)

        self.paste_button = PushButton("从剪贴板粘贴")
        self.paste_button.setIcon(FluentIcon.COPY)
        self.paste_button.clicked.connect(self._paste_from_clipboard)
        buttons_layout.addWidget(self.paste_button)

        self.clear_button = PushButton("清空")
        self.clear_button.setIcon(FluentIcon.DELETE)
        self.clear_button.clicked.connect(self._clear_text)
        buttons_layout.addWidget(self.clear_button)

        layout.addLayout(buttons_layout)

        # 选项
        options_card = CardWidget(self)
        options_layout = QFormLayout(options_card)
        options_layout.setContentsMargins(15, 10, 15, 10)
        options_layout.setSpacing(10)

        # 正则表达式过滤
        options_title = StrongBodyLabel("过滤选项")
        options_layout.addRow(options_title)

        self.regex_input = LineEdit()
        self.regex_input.setPlaceholderText("例如: .*\\.mp4|.*\\.m3u8")
        self.regex_input.textChanged.connect(self._process_text_input)
        options_layout.addRow("正则表达式过滤:", self.regex_input)

        layout.addWidget(options_card)

    def _create_file_tab(self):
        """创建文件选项卡"""
        layout = QVBoxLayout(self.file_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 说明文本
        hint_label = BodyLabel("从文本文件导入URL:")
        layout.addWidget(hint_label)

        # 文件选择
        file_card = CardWidget(self)
        file_card_layout = QVBoxLayout(file_card)
        file_card_layout.setContentsMargins(15, 15, 15, 15)
        file_card_layout.setSpacing(10)

        file_layout = QHBoxLayout()

        self.file_path_input = LineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("选择文件...")
        file_layout.addWidget(self.file_path_input)

        self.browse_button = PushButton("浏览...")
        self.browse_button.setIcon(FluentIcon.FOLDER)
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)

        file_card_layout.addLayout(file_layout)

        # 加载按钮
        self.load_file_button = PushButton("加载文件")
        self.load_file_button.setIcon(FluentIcon.DOCUMENT)
        self.load_file_button.setEnabled(False)
        self.load_file_button.clicked.connect(self._load_file)
        file_card_layout.addWidget(self.load_file_button)

        layout.addWidget(file_card)

        # 选项
        options_card = CardWidget(self)
        options_layout = QFormLayout(options_card)
        options_layout.setContentsMargins(15, 10, 15, 10)
        options_layout.setSpacing(10)

        # 标题
        options_title = StrongBodyLabel("过滤选项")
        options_layout.addRow(options_title)

        # 正则表达式过滤
        self.file_regex_input = LineEdit()
        self.file_regex_input.setPlaceholderText("例如: .*\\.mp4|.*\\.m3u8")
        options_layout.addRow("正则表达式过滤:", self.file_regex_input)

        layout.addWidget(options_card)
        layout.addStretch()

    def _create_web_tab(self):
        """创建网页抓取选项卡"""
        layout = QVBoxLayout(self.web_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 说明文本
        hint_label = BodyLabel("从网页中抓取媒体URL:")
        layout.addWidget(hint_label)

        # 网页URL输入卡片
        url_card = CardWidget(self)
        url_card_layout = QVBoxLayout(url_card)
        url_card_layout.setContentsMargins(15, 15, 15, 15)
        url_card_layout.setSpacing(10)

        url_layout = QFormLayout()
        url_layout.setSpacing(10)

        self.web_url_input = LineEdit()
        self.web_url_input.setPlaceholderText("输入网页URL...")
        url_layout.addRow("网页URL:", self.web_url_input)

        url_card_layout.addLayout(url_layout)

        # 抓取按钮
        self.fetch_button = PushButton("抓取URL")
        self.fetch_button.setIcon(FluentIcon.GLOBE)
        self.fetch_button.clicked.connect(self._fetch_urls_from_web)
        url_card_layout.addWidget(self.fetch_button)

        layout.addWidget(url_card)

        # 选项
        options_card = CardWidget(self)
        options_layout = QFormLayout(options_card)
        options_layout.setContentsMargins(15, 10, 15, 10)
        options_layout.setSpacing(10)

        # 标题
        options_title = StrongBodyLabel("抓取选项")
        options_layout.addRow(options_title)

        # 媒体类型
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

        # 递归深度
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
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            InfoBar.warning(
                title="粘贴失败",
                content="剪贴板中没有文本内容",
                orient=Qt.Horizontal,
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
            orient=Qt.Horizontal,
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
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            InfoBar.error(
                title="加载失败",
                content=f"加载文件出错: {str(e)}",
                orient=Qt.Horizontal,
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
                orient=Qt.Horizontal,
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
                orient=Qt.Horizontal,
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
                orient=Qt.Horizontal,
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
        url_card_layout = self.web_tab.findChild(CardWidget).layout()
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
            url_card_layout.removeWidget(progress)
            progress.deleteLater()
            self.fetch_button.setEnabled(True)

            # 更新URL预览
            self._update_url_preview(urls)

            InfoBar.success(
                title="抓取成功",
                content=f"从网页中提取了 {len(urls)} 个URL",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

        except Exception as e:
            # 移除进度条并恢复按钮
            url_card_layout.removeWidget(progress)
            progress.deleteLater()
            self.fetch_button.setEnabled(True)

            InfoBar.error(
                title="抓取失败",
                content=f"从网页抓取URL出错: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _update_url_preview(self, urls):
        """更新URL预览"""
        self.urls = urls

        # 更新预览文本框
        preview_text = "\n".join(urls)
        self.url_preview.setText(preview_text)

        # 更新URL计数
        self.url_count_label.setText(f"已检测到 {len(urls)} 个URL")

        # 启用/禁用导入按钮
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(len(urls) > 0)

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

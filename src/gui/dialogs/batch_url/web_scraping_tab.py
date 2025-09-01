"""网页抓取选项卡"""
from PySide6.QtWidgets import QVBoxLayout, QWidget, QFormLayout
from PySide6.QtCore import Qt, Signal
from typing import Any, List, Optional, Dict

from qfluentwidgets import (
    PushButton, LineEdit, CardWidget, BodyLabel, StrongBodyLabel,
    CheckBox, SpinBox, ProgressBar, FluentIcon as FIF, InfoBarPosition, InfoBar
)

from src.core.url_extractor import URLExtractor


class WebScrapingTab(QWidget):
    """网页抓取选项卡"""

    # 提取URL信号
    urls_extracted = Signal(list)

    def __init__(self, settings: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 说明文本
        hint_label = BodyLabel("从网页中抓取媒体URL:")
        layout.addWidget(hint_label)

        # 网页URL输入卡片
        self.url_card = CardWidget(self)
        url_card_layout = QVBoxLayout(self.url_card)
        url_card_layout.setContentsMargins(15, 15, 15, 15)
        url_card_layout.setSpacing(10)

        url_form_layout = QFormLayout()
        url_form_layout.setSpacing(10)

        self.web_url_input = LineEdit()
        self.web_url_input.setPlaceholderText("输入网页URL...")
        url_form_layout.addRow("网页URL:", self.web_url_input)

        url_card_layout.addLayout(url_form_layout)

        # 抓取按钮
        self.fetch_button = PushButton("抓取URL")
        self.fetch_button.setIcon(FIF.GLOBE)
        self.fetch_button.clicked.connect(self._fetch_urls_from_web)
        url_card_layout.addWidget(self.fetch_button)

        layout.addWidget(self.url_card)

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

    def _fetch_urls_from_web(self):
        """从网页抓取URL"""
        url: str = self.web_url_input.text().strip()
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
        extensions: List[str] = []
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
        url_card_layout = self.url_card.layout()
        if url_card_layout:  # Ensure layout exists
            url_card_layout.addWidget(progress)

        # 禁用抓取按钮
        self.fetch_button.setEnabled(False)

        try:
            # 获取用户代理设置
            user_agent: str = self.settings.get("advanced", "user_agent", "")
            headers: Optional[Dict[str, str]] = {
                "User-Agent": user_agent} if user_agent else None

            # 抓取URL
            extracted_urls: List[str] = URLExtractor.extract_media_urls_from_webpage(
                url, headers, extensions)

            # 移除进度条并恢复按钮
            if url_card_layout:  # Ensure layout exists
                url_card_layout.removeWidget(progress)
            progress.deleteLater()
            self.fetch_button.setEnabled(True)

            # 发出信号更新URL预览
            self.urls_extracted.emit(extracted_urls)

            InfoBar.success(
                title="抓取成功",
                content=f"从网页中提取了 {len(extracted_urls)} 个URL",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

        except Exception as e:
            # 移除进度条并恢复按钮
            if url_card_layout:  # Ensure layout exists
                url_card_layout.removeWidget(progress)
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

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QStackedWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from qfluentwidgets import (
    FluentIcon, Dialog, PushButton,
    SimpleCardWidget, TextEdit, IconWidget, ImageLabel,
    BodyLabel, TitleLabel, CaptionLabel, TabBar
)
from qfluentwidgets import FluentStyleSheet


class AboutDialog(Dialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("关于")
        self.setMinimumSize(600, 450)
        self.setWindowIcon(QIcon(":/images/logo.png"))

        self._create_ui()
        self.setStyleSheet(FluentStyleSheet.LIGHT)

    def _create_ui(self):
        """创建界面"""
        self.card = SimpleCardWidget(self)
        self.vBoxLayout.addWidget(self.card)

        main_layout = QVBoxLayout(self.card)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(15)

        # 标题和版本
        title_layout = QHBoxLayout()
        title_layout.setSpacing(15)

        # 图标
        self.icon_widget = ImageLabel(":/images/logo.png")
        self.icon_widget.setFixedSize(54, 54)
        title_layout.addWidget(self.icon_widget)

        # 标题和版本信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)

        self.title_label = TitleLabel("VidTanium")
        info_layout.addWidget(self.title_label)

        self.version_label = BodyLabel("版本 1.0.0")
        info_layout.addWidget(self.version_label)

        title_layout.addLayout(info_layout)
        title_layout.addStretch()

        main_layout.addLayout(title_layout)

        # 分隔线
        self.separator = QWidget()
        self.separator.setFixedHeight(1)
        self.separator.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(self.separator)

        # 创建TabBar和QStackedWidget组合
        tab_layout = QVBoxLayout()
        tab_layout.setSpacing(0)

        # TabBar
        self.tab_bar = TabBar()
        self.tab_bar.setFixedHeight(40)
        self.tab_bar.setMovable(False)
        tab_layout.addWidget(self.tab_bar)

        # QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setFixedHeight(320)
        tab_layout.addWidget(self.stacked_widget)

        # 关于选项卡
        self.about_tab = QWidget()
        self._create_about_tab()
        self.stacked_widget.addWidget(self.about_tab)
        self.tab_bar.addTab('关于')

        # 许可证选项卡
        self.license_tab = QWidget()
        self._create_license_tab()
        self.stacked_widget.addWidget(self.license_tab)
        self.tab_bar.addTab('许可证')

        # 第三方库选项卡
        self.third_party_tab = QWidget()
        self._create_third_party_tab()
        self.stacked_widget.addWidget(self.third_party_tab)
        self.tab_bar.addTab('第三方库')

        # 连接TabBar和StackedWidget
        self.tab_bar.currentChanged.connect(
            self.stacked_widget.setCurrentIndex)

        main_layout.addLayout(tab_layout)

        # 按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)

        buttons_layout.addStretch()

        self.close_button = PushButton('关闭')
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)

        main_layout.addLayout(buttons_layout)

    def _create_about_tab(self):
        """创建关于选项卡"""
        layout = QVBoxLayout(self.about_tab)
        layout.setContentsMargins(2, 10, 2, 10)

        about_text = TextEdit()
        about_text.setReadOnly(True)
        about_text.setOpenExternalLinks(True)
        about_text.setStyleSheet(
            "border: none; background-color: transparent;")
        about_text.setHtml("""
        <h2 style="color: #0078d4;">VidTanium</h2>
        <p>一个强大的在线视频加密下载与解密工具。</p>
        <p>版权所有 &copy; 2023-2025 VidTanium 开发团队</p>
        <p>本软件使用 Python 和 PySide6 开发，界面基于 QFluentWidgets。</p>
        <p>项目主页: <a href="https://github.com/vidtanium/vidtanium" style="color: #0078d4; text-decoration: none;">https://github.com/vidtanium/vidtanium</a></p>
        <p>问题报告: <a href="https://github.com/vidtanium/vidtanium/issues" style="color: #0078d4; text-decoration: none;">https://github.com/vidtanium/vidtanium/issues</a></p>
        """)

        layout.addWidget(about_text)

    def _create_license_tab(self):
        """创建许可证选项卡"""
        layout = QVBoxLayout(self.license_tab)
        layout.setContentsMargins(2, 10, 2, 10)

        license_text = TextEdit()
        license_text.setReadOnly(True)
        license_text.setStyleSheet(
            "border: none; background-color: transparent;")
        license_text.setHtml("""
        <h2 style="color: #0078d4;">MIT License</h2>
        <p>Copyright (c) 2023-2025 VidTanium 开发团队</p>
        <p>Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:</p>
        <p>The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.</p>
        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.</p>
        """)

        layout.addWidget(license_text)

    def _create_third_party_tab(self):
        """创建第三方库选项卡"""
        layout = QVBoxLayout(self.third_party_tab)
        layout.setContentsMargins(2, 10, 2, 10)

        third_party_text = TextEdit()
        third_party_text.setReadOnly(True)
        third_party_text.setOpenExternalLinks(True)
        third_party_text.setStyleSheet(
            "border: none; background-color: transparent;")
        third_party_text.setHtml("""
        <h2 style="color: #0078d4;">第三方库</h2>
        <p>本软件使用了以下第三方库:</p>
        <ul>
            <li><a href="https://www.python.org/" style="color: #0078d4; text-decoration: none;">Python</a> - Python Software Foundation License</li>
            <li><a href="https://www.qt.io/" style="color: #0078d4; text-decoration: none;">Qt</a> / <a href="https://wiki.qt.io/Qt_for_Python" style="color: #0078d4; text-decoration: none;">PySide6</a> - LGPL</li>
            <li><a href="https://github.com/zhiyiYo/PyQt-Fluent-Widgets" style="color: #0078d4; text-decoration: none;">PyQt-Fluent-Widgets</a> - MIT License</li>
            <li><a href="https://github.com/pycryptodome/pycryptodome" style="color: #0078d4; text-decoration: none;">PyCryptodome</a> - BSD License</li>
            <li><a href="https://github.com/psf/requests" style="color: #0078d4; text-decoration: none;">Requests</a> - Apache License 2.0</li>
            <li><a href="https://ffmpeg.org/" style="color: #0078d4; text-decoration: none;">FFmpeg</a> (外部工具) - LGPL / GPL</li>
        </ul>
        <p>完整的第三方库列表和许可证信息请参见项目文档。</p>
        """)

        layout.addWidget(third_party_text)

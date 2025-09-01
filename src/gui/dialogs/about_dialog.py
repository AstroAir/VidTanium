from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QStackedWidget,
                               QDialog, QDialogButtonBox, QScrollArea, QFrame,
                               QSpacerItem, QSizePolicy, QLabel)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtGui import QFont, QIcon, QPalette, QLinearGradient, QBrush

from qfluentwidgets import (
    FluentIcon as FIF, PushButton, CardWidget, TextEdit,
    IconWidget, ImageLabel, BodyLabel, TitleLabel,
    CaptionLabel, TabBar, SubtitleLabel, HyperlinkButton,
    InfoBar, InfoBarPosition, ProgressRing
)
from qfluentwidgets import FluentStyleSheet, setTheme, Theme

from src.gui.utils.i18n import tr


class AboutDialog(QDialog):
    """Modern and beautiful About Dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(tr("about_dialog.title"))
        self.setMinimumSize(750, 600)
        self.setMaximumSize(900, 700)
        self.setWindowIcon(QIcon(":/images/logo.png"))

        # Set window flags for better appearance
        self.setWindowFlags(Qt.WindowType.Dialog |
                            Qt.WindowType.WindowCloseButtonHint)

        # Apply custom styling
        self.setStyleSheet("""
            AboutDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 12px;
            }
        """)

        # Create main layout with margins
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        self._create_ui()
        self._setup_animations()

    def _create_ui(self):
        """Create the beautiful UI"""
        # Header section with gradient background
        self._create_header()

        # Content area with tabs
        self._create_content_area()

        # Footer with buttons
        self._create_footer()

    def _create_header(self):
        """Create an attractive header with logo and app info"""
        header_card = CardWidget()
        header_card.setFixedHeight(120)
        header_card.setStyleSheet("""
            CardWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                color: white;
            }
        """)

        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(20)

        # App icon with glow effect
        icon_container = QWidget()
        icon_container.setFixedSize(80, 80)
        icon_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 40px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)

        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        self.icon_widget = IconWidget(FIF.VIDEO)
        self.icon_widget.setFixedSize(60, 60)
        self.icon_widget.setStyleSheet(
            "color: white; background: transparent; border: none;")
        icon_layout.addWidget(self.icon_widget, 0,
                              Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(icon_container)

        # App information
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        self.title_label = TitleLabel(tr("about_dialog.app_name"))
        self.title_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 28px;")
        info_layout.addWidget(self.title_label)

        self.version_label = SubtitleLabel(tr("about_dialog.version"))
        self.version_label.setStyleSheet(
            "color: rgba(255, 255, 255, 0.9); font-size: 16px;")
        info_layout.addWidget(self.version_label)

        self.tagline_label = BodyLabel(tr("about_dialog.tagline"))
        self.tagline_label.setStyleSheet(
            "color: rgba(255, 255, 255, 0.8); font-size: 14px;")
        info_layout.addWidget(self.tagline_label)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        # Add download/star buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)

        self.github_btn = HyperlinkButton(
            tr("about_dialog.github"),
            "https://github.com/yourusername/vidtanium"
        )
        self.github_btn.setStyleSheet("""
            HyperlinkButton {
                color: white;
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            HyperlinkButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        buttons_layout.addWidget(self.github_btn)

        header_layout.addLayout(buttons_layout)

        self.main_layout.addWidget(header_card)

    def _create_content_area(self):
        """Create the main content area with tabs"""
        # Create TabBar and QStackedWidget combination
        content_card = CardWidget()
        content_card.setMinimumHeight(350)

        tab_layout = QVBoxLayout(content_card)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(0)

        # TabBar with modern styling
        self.tab_bar = TabBar()
        self.tab_bar.setFixedHeight(50)
        self.tab_bar.setMovable(False)
        self.tab_bar.setStyleSheet("""
            TabBar {
                background-color: transparent;
                border-bottom: 2px solid #e0e0e0;
            }
        """)
        tab_layout.addWidget(self.tab_bar)

        # QStackedWidget for tab content
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setMinimumHeight(280)
        tab_layout.addWidget(self.stacked_widget)

        # Create tabs
        self._create_about_tab()
        self._create_features_tab()
        self._create_license_tab()
        self._create_third_party_tab()

        # Add tabs to TabBar
        self.tab_bar.addTab(FIF.INFO.value,
                            tr('about_dialog.tabs.about'))
        self.tab_bar.addTab(FIF.TAG.value, tr(
            'about_dialog.tabs.features'))
        self.tab_bar.addTab(FIF.DOCUMENT.value,
                            tr('about_dialog.tabs.license'))
        self.tab_bar.addTab(FIF.APPLICATION.value,
                            tr('about_dialog.tabs.third_party'))

        # Connect TabBar and StackedWidget
        self.tab_bar.currentChanged.connect(
            self.stacked_widget.setCurrentIndex)

        self.main_layout.addWidget(content_card)

    def _create_footer(self):
        """Create footer with action buttons"""
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        # Add some action buttons
        self.check_updates_btn = PushButton(tr("about_dialog.check_updates"))
        self.check_updates_btn.setIcon(FIF.UPDATE)
        self.check_updates_btn.clicked.connect(self._check_updates)

        footer_layout.addWidget(self.check_updates_btn)
        footer_layout.addStretch()

        # Standard close button
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close)
        self.button_box.rejected.connect(self.reject)
        footer_layout.addWidget(self.button_box)

        self.main_layout.addLayout(footer_layout)

    def _setup_animations(self):
        """Setup entrance animations"""
        # Simple fade-in animation would be added here
        # For now, we'll keep it simple
        pass

    def _check_updates(self):
        """Handle check for updates"""
        InfoBar.success(
            title=tr("about_dialog.updates.checking"),
            content=tr("about_dialog.updates.latest"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _create_about_tab(self):
        """Create modern about tab with cards"""
        self.about_tab = QWidget()
        layout = QVBoxLayout(self.about_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # Description card
        desc_card = CardWidget()
        desc_layout = QVBoxLayout(desc_card)
        desc_layout.setContentsMargins(20, 20, 20, 20)

        desc_title = SubtitleLabel(tr("about_dialog.description.title"))
        desc_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        desc_layout.addWidget(desc_title)

        desc_text = BodyLabel(tr("about_dialog.description.content"))
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("color: #34495e; line-height: 1.6;")
        desc_layout.addWidget(desc_text)

        scroll_layout.addWidget(desc_card)

        # Features card
        features_card = CardWidget()
        features_layout = QVBoxLayout(features_card)
        features_layout.setContentsMargins(20, 20, 20, 20)

        features_title = SubtitleLabel(tr("about_dialog.key_features.title"))
        features_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        features_layout.addWidget(features_title)

        # Feature list with icons
        features = [
            ("DOWNLOAD", tr("about_dialog.key_features.encrypted_download")),
            ("SEND", tr("about_dialog.key_features.high_speed")),
            ("SYNC", tr("about_dialog.key_features.smart_retry")),
            ("BRUSH", tr("about_dialog.key_features.modern_ui")),
            ("MENU", tr("about_dialog.key_features.batch_support"))
        ]

        for icon_name, feature_text in features:
            feature_layout = QHBoxLayout()
            feature_layout.setSpacing(10)

            icon = IconWidget(getattr(FluentIcon, icon_name))
            icon.setFixedSize(20, 20)
            icon.setStyleSheet("color: #3498db;")
            feature_layout.addWidget(icon)

            label = BodyLabel(feature_text)
            label.setStyleSheet("color: #34495e;")
            feature_layout.addWidget(label)
            feature_layout.addStretch()

            features_layout.addLayout(feature_layout)

        scroll_layout.addWidget(features_card)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self.stacked_widget.addWidget(self.about_tab)

    def _create_features_tab(self):
        """Create detailed features tab"""
        self.features_tab = QWidget()
        layout = QVBoxLayout(self.features_tab)
        layout.setContentsMargins(15, 15, 15, 15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        # Feature categories
        categories = [
            {
                "icon": "DOWNLOAD",
                "title": tr("about_dialog.features.download.title"),
                "items": [
                    tr("about_dialog.features.download.m3u8"),
                    tr("about_dialog.features.download.encryption"),
                    tr("about_dialog.features.download.resume"),
                    tr("about_dialog.features.download.metadata")
                ]
            },
            {
                "icon": "SEND",
                "title": tr("about_dialog.features.performance.title"),
                "items": [
                    tr("about_dialog.features.performance.multithread"),
                    tr("about_dialog.features.performance.async"),
                    tr("about_dialog.features.performance.optimization"),
                    tr("about_dialog.features.performance.monitoring")
                ]
            },
            {
                "icon": "BRUSH",
                "title": tr("about_dialog.features.interface.title"),
                "items": [
                    tr("about_dialog.features.interface.modern"),
                    tr("about_dialog.features.interface.themes"),
                    tr("about_dialog.features.interface.responsive"),
                    tr("about_dialog.features.interface.i18n")
                ]
            }
        ]

        for category in categories:
            card = CardWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)
            card_layout.setSpacing(15)

            # Category header
            header_layout = QHBoxLayout()
            header_layout.setSpacing(10)

            icon = IconWidget(getattr(FluentIcon, category["icon"]))
            icon.setFixedSize(24, 24)
            icon.setStyleSheet("color: #3498db;")
            header_layout.addWidget(icon)

            title = SubtitleLabel(category["title"])
            title.setStyleSheet("font-weight: bold; color: #2c3e50;")
            header_layout.addWidget(title)
            header_layout.addStretch()

            card_layout.addLayout(header_layout)

            # Feature items
            for item in category["items"]:
                item_layout = QHBoxLayout()
                item_layout.setSpacing(8)

                bullet = BodyLabel("•")
                bullet.setStyleSheet("color: #3498db; font-weight: bold;")
                bullet.setFixedWidth(15)
                item_layout.addWidget(bullet)

                item_label = BodyLabel(item)
                item_label.setWordWrap(True)
                item_label.setStyleSheet("color: #34495e;")
                item_layout.addWidget(item_label)

                card_layout.addLayout(item_layout)

            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self.stacked_widget.addWidget(self.features_tab)

    def _create_license_tab(self):
        """Create beautiful license tab"""
        self.license_tab = QWidget()
        layout = QVBoxLayout(self.license_tab)
        layout.setContentsMargins(15, 15, 15, 15)

        # License card
        license_card = CardWidget()
        license_layout = QVBoxLayout(license_card)
        license_layout.setContentsMargins(25, 25, 25, 25)
        license_layout.setSpacing(15)

        # License header
        header_layout = QHBoxLayout()
        license_icon = IconWidget(FIF.DOCUMENT)
        license_icon.setFixedSize(24, 24)
        license_icon.setStyleSheet("color: #27ae60;")
        header_layout.addWidget(license_icon)

        license_title = SubtitleLabel(tr("about_dialog.license.title"))
        license_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(license_title)
        header_layout.addStretch()

        license_layout.addLayout(header_layout)

        # License content
        license_text = TextEdit()
        license_text.setReadOnly(True)
        license_text.setMaximumHeight(200)
        license_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #2c3e50;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 15px;
            }
        """)
        license_text.setPlainText(tr("about_dialog.license_content"))
        license_layout.addWidget(license_text)

        layout.addWidget(license_card)
        layout.addStretch()

        self.stacked_widget.addWidget(self.license_tab)

    def _create_third_party_tab(self):
        """Create modern third-party libraries tab"""
        self.third_party_tab = QWidget()
        layout = QVBoxLayout(self.third_party_tab)
        layout.setContentsMargins(15, 15, 15, 15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # Title card
        title_card = CardWidget()
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(20, 15, 20, 15)

        title_header = QHBoxLayout()
        libs_icon = IconWidget(FIF.APPLICATION)
        libs_icon.setFixedSize(24, 24)
        libs_icon.setStyleSheet("color: #e74c3c;")
        title_header.addWidget(libs_icon)

        libs_title = SubtitleLabel(tr("about_dialog.third_party.title"))
        libs_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        title_header.addWidget(libs_title)
        title_header.addStretch()

        title_layout.addLayout(title_header)

        desc_label = BodyLabel(tr("about_dialog.third_party.description"))
        desc_label.setStyleSheet("color: #7f8c8d;")
        title_layout.addWidget(desc_label)

        scroll_layout.addWidget(title_card)

        # Libraries list
        libraries = [
            {
                "name": "PySide6",
                "description": tr("about_dialog.libraries.pyside6"),
                "license": "LGPL v3",
                "icon": "CODE"
            },
            {
                "name": "PyQt-Fluent-Widgets",
                "description": tr("about_dialog.libraries.fluent_widgets"),
                "license": "GPL v3",
                "icon": "BRUSH"
            },
            {
                "name": "cryptography",
                "description": tr("about_dialog.libraries.cryptography"),
                "license": "Apache 2.0",
                "icon": "FINGERPRINT"
            },
            {
                "name": "requests",
                "description": tr("about_dialog.libraries.requests"),
                "license": "Apache 2.0",
                "icon": "GLOBE"
            },
            {
                "name": "aiohttp",
                "description": tr("about_dialog.libraries.aiohttp"),
                "license": "Apache 2.0",
                "icon": "SEND"
            }
        ]

        for lib in libraries:
            lib_card = CardWidget()
            lib_layout = QVBoxLayout(lib_card)
            lib_layout.setContentsMargins(20, 15, 20, 15)
            lib_layout.setSpacing(8)

            # Library header
            lib_header = QHBoxLayout()
            lib_header.setSpacing(10)

            lib_icon = IconWidget(getattr(FluentIcon, lib["icon"]))
            lib_icon.setFixedSize(20, 20)
            lib_icon.setStyleSheet("color: #9b59b6;")
            lib_header.addWidget(lib_icon)

            lib_name = SubtitleLabel(lib["name"])
            lib_name.setStyleSheet(
                "font-weight: bold; color: #2c3e50; font-size: 16px;")
            lib_header.addWidget(lib_name)

            lib_header.addStretch()

            license_label = CaptionLabel(lib["license"])
            license_label.setStyleSheet("""
                background-color: #ecf0f1;
                color: #7f8c8d;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
            """)
            lib_header.addWidget(license_label)

            lib_layout.addLayout(lib_header)

            # Library description
            lib_desc = BodyLabel(lib["description"])
            lib_desc.setWordWrap(True)
            lib_desc.setStyleSheet("color: #34495e; margin-left: 30px;")
            lib_layout.addWidget(lib_desc)

            scroll_layout.addWidget(lib_card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self.stacked_widget.addWidget(self.third_party_tab)

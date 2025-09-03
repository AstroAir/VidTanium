"""
Help Navigation Panel for VidTanium Help System
Provides navigation between different help topics and sections
"""

from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from qfluentwidgets import (
    ElevatedCardWidget, TransparentToolButton, BodyLabel, 
    TitleLabel, FluentIcon as FIF, PushButton
)

from ...utils.design_system import DesignSystem, AnimatedCard
from ...utils.i18n import tr

from loguru import logger


class HelpNavigationItem(AnimatedCard):
    """Individual navigation item for help topics"""
    
    clicked = Signal(str)  # page_name
    
    def __init__(self, page_name: str, title: str, description: str = "", icon: FIF = FIF.DOCUMENT, parent=None):
        super().__init__(parent)
        self.page_name = page_name
        self.title = title
        self.description = description
        self.icon = icon
        self.is_active = False
        
        self._setup_ui()
        self._setup_styling()
    
    def _setup_ui(self):
        """Setup navigation item UI"""
        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        self.icon_btn = TransparentToolButton(self.icon)
        self.icon_btn.setFixedSize(32, 32)
        self.icon_btn.setEnabled(False)  # Just for display
        layout.addWidget(self.icon_btn)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        
        # Title
        self.title_label = BodyLabel(self.title)
        self.title_label.setStyleSheet(f"""
            font-weight: 600;
            color: {DesignSystem.get_color('text_primary_adaptive')};
        """)
        content_layout.addWidget(self.title_label)
        
        # Description
        if self.description:
            self.desc_label = BodyLabel(self.description)
            self.desc_label.setStyleSheet(f"""
                font-size: 12px;
                color: {DesignSystem.get_color('text_secondary_adaptive')};
            """)
            content_layout.addWidget(self.desc_label)
        
        layout.addLayout(content_layout)
        layout.addStretch()
    
    def _setup_styling(self):
        """Setup item styling"""
        self.setStyleSheet(f"""
            HelpNavigationItem {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['md']}px;
            }}
            
            HelpNavigationItem:hover {{
                background: {DesignSystem.get_color('surface_hover_adaptive')};
                border-color: {DesignSystem.get_color('accent_adaptive')};
            }}
        """)
    
    def set_active(self, active: bool):
        """Set item active state"""
        self.is_active = active
        
        if active:
            self.setStyleSheet(f"""
                HelpNavigationItem {{
                    background: {DesignSystem.get_color('accent_adaptive')};
                    border: 1px solid {DesignSystem.get_color('accent_adaptive')};
                    border-radius: {DesignSystem.RADIUS['md']}px;
                }}
            """)
            self.title_label.setStyleSheet(f"""
                font-weight: 600;
                color: white;
            """)
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"""
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.8);
                """)
        else:
            self._setup_styling()
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.page_name)
        super().mousePressEvent(event)


class HelpNavigationPanel(ElevatedCardWidget):
    """Navigation panel for help topics"""
    
    page_requested = Signal(str)  # page_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.navigation_items: Dict[str, HelpNavigationItem] = {}
        self.current_page = ""
        
        self._setup_ui()
        self._setup_styling()
        self._create_navigation_items()
        
        logger.debug("Help navigation panel initialized")
    
    def _setup_ui(self):
        """Setup navigation panel UI"""
        self.setFixedWidth(280)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 20, 16, 20)
        self.main_layout.setSpacing(16)
        
        # Header
        self.header = self._create_header()
        self.main_layout.addWidget(self.header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"""
            QFrame {{
                color: {DesignSystem.get_color('border_adaptive')};
                margin: 0px;
            }}
        """)
        self.main_layout.addWidget(separator)
        
        # Navigation items container
        self.nav_container = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(8)
        
        self.main_layout.addWidget(self.nav_container)
        self.main_layout.addStretch()
    
    def _create_header(self) -> QWidget:
        """Create navigation header"""
        header = QWidget()
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Title
        title = TitleLabel(tr("help.navigation.title"))
        title.setStyleSheet(f"""
            {DesignSystem.get_typography_style('title')}
            color: {DesignSystem.get_color('text_primary_adaptive')};
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = BodyLabel(tr("help.navigation.subtitle"))
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {DesignSystem.get_color('text_secondary_adaptive')};
        """)
        layout.addWidget(subtitle)
        
        return header
    
    def _setup_styling(self):
        """Setup panel styling"""
        self.setStyleSheet(f"""
            HelpNavigationPanel {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['xl']}px;
            }}
        """)
        
        # Add shadow effect
        shadow = DesignSystem.create_shadow_effect('md')
        self.setGraphicsEffect(shadow)
    
    def _create_navigation_items(self):
        """Create navigation items for help topics"""
        # Define help topics
        help_topics = [
            {
                "page_name": "index",
                "title": tr("help.pages.index"),
                "description": tr("help.pages.index_desc"),
                "icon": FIF.HOME
            },
            {
                "page_name": "getting-started",
                "title": tr("help.pages.getting_started"),
                "description": tr("help.pages.getting_started_desc"),
                "icon": FIF.PLAY
            },
            {
                "page_name": "user-guide",
                "title": tr("help.pages.user_guide"),
                "description": tr("help.pages.user_guide_desc"),
                "icon": FIF.BOOK_SHELF
            },
            {
                "page_name": "troubleshooting",
                "title": tr("help.pages.troubleshooting"),
                "description": tr("help.pages.troubleshooting_desc"),
                "icon": FIF.HELP
            }
        ]
        
        # Create navigation items
        for topic in help_topics:
            item = HelpNavigationItem(
                page_name=topic["page_name"],
                title=topic["title"],
                description=topic["description"],
                icon=topic["icon"]
            )
            item.clicked.connect(self._on_item_clicked)
            
            self.navigation_items[topic["page_name"]] = item
            self.nav_layout.addWidget(item)
    
    def _on_item_clicked(self, page_name: str):
        """Handle navigation item click"""
        self.set_current_page(page_name)
        self.page_requested.emit(page_name)
        logger.debug(f"Help page requested: {page_name}")
    
    def set_current_page(self, page_name: str):
        """Set the current active page"""
        # Deactivate current item
        if self.current_page in self.navigation_items:
            self.navigation_items[self.current_page].set_active(False)
        
        # Activate new item
        if page_name in self.navigation_items:
            self.navigation_items[page_name].set_active(True)
            self.current_page = page_name
    
    def get_current_page(self) -> str:
        """Get current page name"""
        return self.current_page
    
    def get_available_pages(self) -> List[str]:
        """Get list of available help pages"""
        return list(self.navigation_items.keys())
    
    def add_custom_item(self, page_name: str, title: str, description: str = "", icon: FIF = FIF.DOCUMENT):
        """Add a custom navigation item"""
        if page_name in self.navigation_items:
            logger.warning(f"Navigation item already exists: {page_name}")
            return
        
        item = HelpNavigationItem(page_name, title, description, icon)
        item.clicked.connect(self._on_item_clicked)
        
        self.navigation_items[page_name] = item
        self.nav_layout.addWidget(item)
        
        logger.debug(f"Added custom help navigation item: {page_name}")
    
    def remove_item(self, page_name: str):
        """Remove a navigation item"""
        if page_name not in self.navigation_items:
            return
        
        item = self.navigation_items[page_name]
        self.nav_layout.removeWidget(item)
        item.deleteLater()
        del self.navigation_items[page_name]
        
        # If this was the current page, clear current
        if self.current_page == page_name:
            self.current_page = ""
        
        logger.debug(f"Removed help navigation item: {page_name}")
    
    def refresh_items(self):
        """Refresh navigation items (useful for language changes)"""
        # Clear existing items
        for item in self.navigation_items.values():
            self.nav_layout.removeWidget(item)
            item.deleteLater()
        
        self.navigation_items.clear()
        self.current_page = ""
        
        # Recreate items
        self._create_navigation_items()
        
        logger.debug("Help navigation items refreshed")

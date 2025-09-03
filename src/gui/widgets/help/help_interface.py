"""
Main Help Interface for VidTanium
Provides comprehensive help documentation with navigation and Markdown rendering
"""

from typing import Optional, Dict, Any
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
    QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from qfluentwidgets import (
    SmoothScrollArea, ElevatedCardWidget, TitleLabel,
    BodyLabel, FluentIcon as FIF, TransparentToolButton,
    InfoBar, InfoBarPosition
)

from ...utils.design_system import DesignSystem
from ...utils.responsive import ResponsiveWidget, ResponsiveManager
from ...utils.i18n import tr, get_i18n_manager
from .markdown_viewer import MarkdownViewer
from .help_navigation import HelpNavigationPanel

from loguru import logger


class HelpInterface(ResponsiveWidget):
    """Main help interface with navigation and content display"""
    
    # Signals
    page_changed = Signal(str)  # page_name
    error_occurred = Signal(str)  # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = "index"
        self.help_base_path = Path(__file__).parent.parent.parent.parent / "docs" / "help"
        self.responsive_manager = ResponsiveManager.instance()
        
        # Initialize UI
        self._setup_ui()
        self._setup_styling()
        self._connect_signals()
        
        # Load initial content
        QTimer.singleShot(100, self._load_initial_content)
        
        logger.info("Help interface initialized")
    
    def _setup_ui(self):
        """Setup the help interface UI"""
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)
        
        # Create main splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # Left panel: Navigation
        self.nav_panel = self._create_navigation_panel()
        self.splitter.addWidget(self.nav_panel)
        
        # Right panel: Content
        self.content_panel = self._create_content_panel()
        self.splitter.addWidget(self.content_panel)
        
        # Set splitter proportions
        self.splitter.setStretchFactor(0, 0)  # Navigation panel fixed width
        self.splitter.setStretchFactor(1, 1)  # Content panel takes remaining space
        self.splitter.setSizes([300, 800])  # Initial sizes
    
    def _create_navigation_panel(self) -> QWidget:
        """Create the navigation panel"""
        self.navigation = HelpNavigationPanel()
        self.navigation.page_requested.connect(self._on_page_requested)
        return self.navigation
    
    def _create_content_panel(self) -> QWidget:
        """Create the content display panel"""
        panel = ElevatedCardWidget()
        panel.setMinimumWidth(400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        self.header = self._create_header()
        layout.addWidget(self.header)
        
        # Content area with scroll
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Markdown viewer
        self.markdown_viewer = MarkdownViewer()
        self.markdown_viewer.link_clicked.connect(self._on_link_clicked)
        self.scroll_area.setWidget(self.markdown_viewer)
        
        layout.addWidget(self.scroll_area)
        
        return panel
    
    def _create_header(self) -> QWidget:
        """Create the content header"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Page title
        self.page_title = TitleLabel(tr("help.title"))
        self.page_title.setStyleSheet(f"""
            {DesignSystem.get_typography_style('title')}
            color: {DesignSystem.get_color('text_primary_adaptive')};
        """)
        layout.addWidget(self.page_title)
        
        layout.addStretch()
        
        # Action buttons
        self.refresh_btn = TransparentToolButton(FIF.SYNC)
        self.refresh_btn.setToolTip(tr("help.refresh"))
        self.refresh_btn.clicked.connect(self._refresh_content)
        layout.addWidget(self.refresh_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"""
            QFrame {{
                color: {DesignSystem.get_color('border_adaptive')};
                margin: 8px 0px;
            }}
        """)
        
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        header_layout.addWidget(header)
        header_layout.addWidget(separator)
        
        return header_container
    
    def _setup_styling(self):
        """Setup interface styling"""
        self.setStyleSheet(f"""
            HelpInterface {{
                background: {DesignSystem.get_color('background_adaptive')};
            }}
        """)
        
        # Apply shadow to panels
        nav_shadow = DesignSystem.create_shadow_effect('md')
        self.nav_panel.setGraphicsEffect(nav_shadow)
        
        content_shadow = DesignSystem.create_shadow_effect('lg')
        self.content_panel.setGraphicsEffect(content_shadow)
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.responsive_manager.breakpoint_changed.connect(self._on_breakpoint_changed)
    
    def _load_initial_content(self):
        """Load initial help content"""
        try:
            self.load_page("index")
        except Exception as e:
            logger.error(f"Failed to load initial help content: {e}")
            self._show_error(tr("help.error.load_failed"))
    
    def load_page(self, page_name: str):
        """Load a help page by name"""
        try:
            # Get current locale
            i18n_manager = get_i18n_manager()
            locale = i18n_manager.current_locale
            
            # Construct file path
            page_path = self.help_base_path / locale / f"{page_name}.md"
            
            # Fallback to English if locale file doesn't exist
            if not page_path.exists():
                page_path = self.help_base_path / "en" / f"{page_name}.md"
            
            if not page_path.exists():
                raise FileNotFoundError(f"Help page not found: {page_name}")
            
            # Load and display content
            with open(page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.markdown_viewer.set_markdown_content(content)
            self.current_page = page_name
            
            # Update title
            page_titles = {
                "index": tr("help.pages.index"),
                "getting-started": tr("help.pages.getting_started"),
                "user-guide": tr("help.pages.user_guide"),
                "troubleshooting": tr("help.pages.troubleshooting")
            }
            
            title = page_titles.get(page_name, page_name.replace('-', ' ').title())
            self.page_title.setText(title)
            
            # Update navigation
            self.navigation.set_current_page(page_name)
            
            self.page_changed.emit(page_name)
            logger.debug(f"Loaded help page: {page_name}")
            
        except Exception as e:
            logger.error(f"Failed to load help page '{page_name}': {e}")
            self._show_error(tr("help.error.page_not_found", page=page_name))
    
    def _on_page_requested(self, page_name: str):
        """Handle page request from navigation"""
        self.load_page(page_name)
    
    def _on_link_clicked(self, url: str):
        """Handle link clicks in markdown content"""
        try:
            # Handle internal links (markdown files)
            if url.endswith('.md'):
                page_name = url.replace('.md', '')
                self.load_page(page_name)
            else:
                # Handle external links
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl(url))
                
        except Exception as e:
            logger.error(f"Failed to handle link click: {url}, error: {e}")
    
    def _refresh_content(self):
        """Refresh current page content"""
        self.load_page(self.current_page)
        self._show_info(tr("help.content_refreshed"))
    
    def _show_error(self, message: str):
        """Show error message"""
        InfoBar.error(
            title=tr("help.error.title"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
        self.error_occurred.emit(message)
    
    def _show_info(self, message: str):
        """Show info message"""
        InfoBar.success(
            title=tr("help.info.title"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def _on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        if breakpoint in ['xs', 'sm']:
            # On small screens, hide navigation panel
            self.nav_panel.setVisible(False)
            self.splitter.setSizes([0, 1000])
        else:
            # On larger screens, show navigation panel
            self.nav_panel.setVisible(True)
            self.splitter.setSizes([300, 700])
    
    def get_current_page(self) -> str:
        """Get current page name"""
        return self.current_page
    
    def get_available_pages(self) -> list:
        """Get list of available help pages"""
        return self.navigation.get_available_pages()

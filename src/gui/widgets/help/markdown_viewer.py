"""
Markdown Viewer Widget for VidTanium Help System
Renders Markdown content with proper styling and theming
"""

import re
from typing import Optional, Dict, Any
from PySide6.QtWidgets import QTextBrowser, QWidget
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QTextDocument, QTextCursor

from qfluentwidgets import isDarkTheme

from ...utils.design_system import DesignSystem
from ...utils.i18n import tr

from loguru import logger

try:
    import markdown
    from markdown.extensions import codehilite, tables, toc
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logger.warning("Markdown library not available. Install with: pip install markdown")


class MarkdownViewer(QTextBrowser):
    """Widget for displaying Markdown content with proper styling"""
    
    # Signals
    link_clicked = Signal(str)  # url
    content_loaded = Signal()
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        self.markdown_content = ""
        self._setup_ui()
        self._setup_styling()
        
        # Connect signals
        self.anchorClicked.connect(self._on_anchor_clicked)
        
        logger.debug("MarkdownViewer initialized")
    
    def _setup_ui(self) -> None:
        """Setup the markdown viewer UI"""
        # Configure text browser
        self.setOpenExternalLinks(False)  # Handle links manually
        self.setOpenLinks(False)
        self.setReadOnly(True)
        
        # Set document properties
        document = self.document()
        document.setDocumentMargin(16)
        
        # Configure font
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.setFont(font)
    
    def _setup_styling(self) -> None:
        """Setup markdown viewer styling with design system"""
        # Get colors from design system
        bg_color = DesignSystem.get_color('surface_adaptive')
        text_color = DesignSystem.get_color('text_primary_adaptive')
        text_secondary = DesignSystem.get_color('text_secondary_adaptive')
        accent_color = DesignSystem.get_color('accent_adaptive')
        border_color = DesignSystem.get_color('border_adaptive')
        code_bg = DesignSystem.get_color('surface_variant_adaptive')
        
        # Create CSS for markdown content
        css = f"""
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: {text_color};
            background-color: {bg_color};
            margin: 0;
            padding: 16px;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: {text_color};
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }}
        
        h1 {{
            font-size: 28px;
            border-bottom: 2px solid {border_color};
            padding-bottom: 8px;
        }}
        
        h2 {{
            font-size: 24px;
            border-bottom: 1px solid {border_color};
            padding-bottom: 6px;
        }}
        
        h3 {{
            font-size: 20px;
        }}
        
        h4 {{
            font-size: 18px;
        }}
        
        h5, h6 {{
            font-size: 16px;
        }}
        
        p {{
            margin-bottom: 16px;
            color: {text_color};
        }}
        
        a {{
            color: {accent_color};
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        ul, ol {{
            margin-bottom: 16px;
            padding-left: 24px;
        }}
        
        li {{
            margin-bottom: 4px;
            color: {text_color};
        }}
        
        blockquote {{
            border-left: 4px solid {accent_color};
            margin: 16px 0;
            padding: 8px 16px;
            background-color: {code_bg};
            color: {text_secondary};
            font-style: italic;
        }}
        
        code {{
            background-color: {code_bg};
            color: {text_color};
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
        }}
        
        pre {{
            background-color: {code_bg};
            color: {text_color};
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 16px 0;
            border: 1px solid {border_color};
        }}
        
        pre code {{
            background: none;
            padding: 0;
            font-size: 13px;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        
        th, td {{
            border: 1px solid {border_color};
            padding: 8px 12px;
            text-align: left;
        }}
        
        th {{
            background-color: {code_bg};
            font-weight: 600;
            color: {text_color};
        }}
        
        td {{
            color: {text_color};
        }}
        
        hr {{
            border: none;
            border-top: 1px solid {border_color};
            margin: 24px 0;
        }}
        
        .highlight {{
            background-color: {code_bg};
            padding: 16px;
            border-radius: 8px;
            margin: 16px 0;
            border: 1px solid {border_color};
        }}
        
        .toc {{
            background-color: {code_bg};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        }}
        
        .toc ul {{
            margin: 0;
            padding-left: 20px;
        }}
        
        .toc li {{
            margin-bottom: 4px;
        }}
        
        .toc a {{
            color: {accent_color};
        }}
        """
        
        # Set the CSS
        self.document().setDefaultStyleSheet(css)
        
        # Set widget background
        self.setStyleSheet(f"""
            MarkdownViewer {{
                background-color: {bg_color};
                border: none;
                selection-background-color: {accent_color};
            }}
        """)
    
    def set_markdown_content(self, content: str) -> None:
        """Set and render markdown content"""
        self.markdown_content = content
        
        if not MARKDOWN_AVAILABLE:
            # Fallback to plain text if markdown is not available
            self._set_fallback_content(content)
            return
        
        try:
            # Configure markdown extensions
            extensions = [
                'tables',
                'fenced_code',
                'codehilite',
                'toc',
                'nl2br',
                'sane_lists'
            ]
            
            extension_configs: Dict[str, Dict[str, Any]] = {
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': False  # Use simple highlighting
                },
                'toc': {
                    'title': tr("help.table_of_contents")
                }
            }
            
            # Create markdown instance
            md = markdown.Markdown(
                extensions=extensions,
                extension_configs=extension_configs
            )
            
            # Convert markdown to HTML
            html = md.convert(content)
            
            # Set the HTML content
            self.setHtml(html)
            
            self.content_loaded.emit()
            logger.debug("Markdown content rendered successfully")
            
        except Exception as e:
            logger.error(f"Failed to render markdown content: {e}")
            self._set_fallback_content(content)
    
    def _set_fallback_content(self, content: str) -> None:
        """Set content as plain text fallback"""
        # Simple text formatting for fallback
        formatted_content = self._format_plain_text(content)
        self.setPlainText(formatted_content)
        self.content_loaded.emit()
        logger.debug("Using plain text fallback for content")
    
    def _format_plain_text(self, content: str) -> str:
        """Apply basic formatting to plain text"""
        # Remove markdown syntax for better readability
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)  # Headers
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)  # Italic
        content = re.sub(r'`(.*?)`', r'\1', content)  # Inline code
        content = re.sub(r'^\s*[-*+]\s+', '• ', content, flags=re.MULTILINE)  # Lists
        content = re.sub(r'^\s*\d+\.\s+', '1. ', content, flags=re.MULTILINE)  # Numbered lists
        
        return content
    
    def _on_anchor_clicked(self, url: QUrl) -> None:
        """Handle anchor/link clicks"""
        url_string = url.toString()
        self.link_clicked.emit(url_string)
        logger.debug(f"Link clicked: {url_string}")
    
    def get_markdown_content(self) -> str:
        """Get the current markdown content"""
        return self.markdown_content
    
    def clear_content(self) -> None:
        """Clear the viewer content"""
        self.clear()
        self.markdown_content = ""
    
    def refresh_styling(self) -> None:
        """Refresh styling (useful for theme changes)"""
        self._setup_styling()
        if self.markdown_content:
            self.set_markdown_content(self.markdown_content)
    
    def search_text(self, text: str, case_sensitive: bool = False) -> bool:
        """Search for text in the content"""
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        
        cursor = self.document().find(text, self.textCursor(), flags)
        if not cursor.isNull():
            self.setTextCursor(cursor)
            return True
        return False
    
    def zoom_in(self) -> None:
        """Increase font size"""
        self.zoomIn(1)
    
    def zoom_out(self) -> None:
        """Decrease font size"""
        self.zoomOut(1)
    
    def reset_zoom(self) -> None:
        """Reset font size to default"""
        self.zoomIn(0)  # Reset to default zoom

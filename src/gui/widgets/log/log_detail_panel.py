"""
Log Detail Panel Component

Displays detailed information for a single log entry.
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QSize

from qfluentwidgets import (
    TextEdit, CardWidget, StrongBodyLabel,
    ToolButton, FluentIcon
)


class LogDetailPanel(CardWidget):
    """Log detail panel component."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """Create the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header bar
        header_layout = QHBoxLayout()
        self.detail_title = StrongBodyLabel("Log Details", self)
        header_layout.addWidget(self.detail_title)

        # Close button
        self.close_detail_btn = ToolButton(FluentIcon.CLOSE, self)
        self.close_detail_btn.setIconSize(QSize(12, 12))
        self.close_detail_btn.setToolTip("Close detail panel")
        self.close_detail_btn.clicked.connect(lambda: self.setVisible(False))
        header_layout.addWidget(self.close_detail_btn)

        layout.addLayout(header_layout)

        # Detail content
        self.detail_text = TextEdit(self)
        self.detail_text.setReadOnly(True)
        layout.addWidget(self.detail_text)

        self._apply_styles()

    def _apply_styles(self):
        """Apply styles."""
        self.detail_text.setStyleSheet("""
            TextEdit {
                border: none;
                background-color: #f8f8f8;
            }
        """)

    def set_word_wrap(self, enabled):
        """Set word wrap."""
        from PySide6.QtGui import QTextOption
        mode = QTextOption.WrapMode.WordWrap if enabled else QTextOption.WrapMode.NoWrap
        self.detail_text.setWordWrapMode(mode)

    def set_font(self, font):
        """Set font."""
        self.detail_text.setFont(font)

    def set_log_details(self, log_entry):
        """
        Display log details.

        Args:
            log_entry: LogEntry object
        """
        # Build detailed text
        details = (
            f"Time: {log_entry.timestamp_str}\n"
            f"Level: {log_entry.level.upper()}\n"
            f"Message: {log_entry.message}\n"
        )

        if log_entry.source:
            details += f"Source: {log_entry.source}\n"

        if log_entry.details:
            details += f"\nDetails:\n{log_entry.details}\n"

        self.detail_text.setPlainText(details)

    def clear(self):
        """Clear details."""
        self.detail_text.clear()

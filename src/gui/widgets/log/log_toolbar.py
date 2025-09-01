"""
Log Toolbar Component

Provides tool buttons for log operations.
"""

from PySide6.QtWidgets import QToolBar, QFileDialog
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QAction

from qfluentwidgets import FluentIcon

import os
from datetime import datetime


class LogToolbar(QToolBar):
    """Log toolbar component."""

    # Signal definitions
    clearRequested = Signal()
    saveRequested = Signal(str)  # Save file path
    copyRequested = Signal()
    selectAllRequested = Signal()
    detailPanelToggled = Signal(bool)
    exportHtmlRequested = Signal(str)  # Export HTML file path
    autoCleanToggled = Signal(bool)
    zoomInRequested = Signal()
    zoomOutRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """Create the toolbar UI."""
        self.setIconSize(QSize(16, 16))
        self.setMovable(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)

        # Clear logs
        self.clear_action = QAction(FIF.DELETE.icon(), "Clear Logs", self)
        self.clear_action.setToolTip("Clear all current logs")
        self.clear_action.triggered.connect(self.clearRequested.emit)
        self.addAction(self.clear_action)

        # Save logs
        self.save_action = QAction(FIF.SAVE.icon(), "Save Logs", self)
        self.save_action.setToolTip("Save logs to a file")
        self.save_action.triggered.connect(self._save_logs)
        self.addAction(self.save_action)

        self.addSeparator()

        # Copy selected
        self.copy_action = QAction(FIF.COPY.icon(), "Copy", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.setToolTip("Copy selected log text")
        self.copy_action.triggered.connect(self.copyRequested.emit)
        self.addAction(self.copy_action)

        # Select all
        self.select_all_action = QAction(FIF.ACCEPT.icon(), "Select All", self)
        self.select_all_action.setShortcut("Ctrl+A")
        self.select_all_action.triggered.connect(self.selectAllRequested.emit)
        self.addAction(self.select_all_action)

        self.addSeparator()

        # Show details
        self.detail_action = QAction(FIF.INFO.icon(), "Show Details", self)
        self.detail_action.setCheckable(True)
        self.detail_action.setToolTip("Show or hide the detail panel")
        self.detail_action.triggered.connect(self.detailPanelToggled.emit)
        self.addAction(self.detail_action)

        # Export as HTML
        self.export_html_action = QAction(
            FIF.DOCUMENT.icon(), "Export as HTML", self)
        self.export_html_action.setToolTip("Export logs in HTML format")
        self.export_html_action.triggered.connect(self._export_html)
        self.addAction(self.export_html_action)

        self.addSeparator()

        # Auto clean setting
        self.auto_clean_action = QAction(FIF.BRUSH.icon(), "Auto Clean", self)
        self.auto_clean_action.setToolTip("Enable or disable auto clean option")
        self.auto_clean_action.setCheckable(True)
        self.auto_clean_action.setChecked(True)
        self.auto_clean_action.triggered.connect(self.autoCleanToggled.emit)
        self.addAction(self.auto_clean_action)

        # Font zoom in/out
        self.zoom_in_action = QAction(FIF.ZOOM_IN.icon(), "Zoom In", self)
        self.zoom_in_action.setToolTip("Increase font size")
        self.zoom_in_action.triggered.connect(self.zoomInRequested.emit)
        self.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction(FIF.ZOOM_OUT.icon(), "Zoom Out", self)
        self.zoom_out_action.setToolTip("Decrease font size")
        self.zoom_out_action.triggered.connect(self.zoomOutRequested.emit)
        self.addAction(self.zoom_out_action)

        # Apply styles
        self._apply_styles()

    def _apply_styles(self):
        """Apply styles to the toolbar."""
        self.setStyleSheet("""
            QToolBar {
                border: none;
                background-color: transparent;
                spacing: 4px;
                padding: 2px;
            }
            QToolButton {
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
        """)

    def _save_logs(self):
        """Save logs to a file."""
        default_name = f"vidtanium_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log File",
            os.path.join(os.path.expanduser("~"), default_name),
            "Text Files (*.txt);;All Files (*)"
        )

        if filename:
            self.saveRequested.emit(filename)

    def _export_html(self):
        """Export logs as HTML format."""
        default_name = f"vidtanium_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export HTML Log",
            os.path.join(os.path.expanduser("~"), default_name),
            "HTML Files (*.html);;All Files (*)"
        )

        if filename:
            self.exportHtmlRequested.emit(filename)

    def set_detail_panel_visible(self, visible):
        """Set the visibility of the detail panel."""
        self.detail_action.setChecked(visible)

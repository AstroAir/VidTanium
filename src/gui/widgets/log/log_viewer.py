"""
Enhanced log viewer with responsive design and modern Fluent aesthetics
Provides comprehensive log viewing, filtering, and management functionality
"""

from typing import Union, Optional, Callable, Any, TYPE_CHECKING, cast
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu, QFileDialog, QSplitter
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QSize, QThread
from PySide6.QtGui import QTextCharFormat, QColor, QAction, QFont

from qfluentwidgets import (
    CheckBox, FluentIcon as FIF,
    CardWidget, ElevatedCardWidget,
    PushButton, TransparentToolButton, SearchLineEdit, ComboBox,
    BodyLabel, CaptionLabel, StrongBodyLabel, SubtitleLabel,
    SmoothScrollArea, FluentWindow, MSFluentWindow, NavigationItemPosition,
    PipsPager, InfoBar, InfoBarPosition, TeachingTip, InfoBarIcon,
    Slider, SpinBox, ToggleButton, ProgressBar, RoundMenu, Action,
    TextEdit as FluentTextEdit, PlainTextEdit
)

import re
import json
import csv
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path

from .log_entry import LogEntry
from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme, ThemeManager
from ...utils.responsive import ResponsiveWidget, ResponsiveManager, ResponsiveContainer
from ...theme_manager import EnhancedThemeManager
from loguru import logger

# Import thread pool - use try/except for graceful fallback
THREAD_POOL_AVAILABLE = False
_thread_submit = None
_thread_get_pool = None

try:
    from src.core.thread_pool import submit_task, get_thread_pool
    THREAD_POOL_AVAILABLE = True
    _thread_submit = submit_task
    _thread_get_pool = get_thread_pool
except ImportError:
    pass

# Define unified interface functions
def safe_submit_task(function: Callable,
                    *args,
                    callback: Optional[Callable] = None,
                    error_callback: Optional[Callable] = None,
                    progress_callback: Optional[Callable] = None,
                    **kwargs):
    """Submit task to thread pool if available, otherwise do nothing"""
    if THREAD_POOL_AVAILABLE and _thread_submit is not None:
        return _thread_submit(function, *args, callback=callback,
                             error_callback=error_callback,
                             progress_callback=progress_callback, **kwargs)
    return None

def safe_get_thread_pool():
    """Get thread pool if available, otherwise return None"""
    if THREAD_POOL_AVAILABLE and _thread_get_pool is not None:
        return _thread_get_pool()
    return None

# Aliases for backward compatibility
submit_task = safe_submit_task
get_thread_pool = safe_get_thread_pool


class EnhancedLogViewer(ResponsiveWidget):
    """Enhanced log viewer with responsive design and modern aesthetics"""
    
    log_cleared = Signal()
    export_requested = Signal(str, str)  # format, filename
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.responsive_manager = ResponsiveManager.instance()
        self.theme_manager = None
        
        # Log management
        self.log_entries: List[LogEntry] = []
        self.filtered_entries: List[LogEntry] = []
        self.current_filters = {
            'level': 'all',
            'search': '',
            'time_range': 'all'
        }
        
        # UI Components
        self.toolbar: Optional[QWidget] = None
        self.log_display: Optional[PlainTextEdit] = None
        self.filter_panel: Optional[QWidget] = None
        self.status_bar: Optional[QWidget] = None
        
        # Performance optimization
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update_log_display)
        self._pending_updates = False
        
        self._setup_ui()
        self._setup_responsive_behavior()

    def _setup_ui(self) -> None:
        """Setup the enhanced log viewer UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create main container with responsive design
        main_container = ResponsiveContainer()
        container_layout = QVBoxLayout(main_container)
        
        # Enhanced toolbar
        self._create_enhanced_toolbar(container_layout)
        
        # Content area with splitter for responsive layout
        self._create_content_area(container_layout)
        
        # Enhanced status bar
        self._create_enhanced_status_bar(container_layout)
        
        layout.addWidget(main_container)

    def _create_enhanced_toolbar(self, layout: QVBoxLayout) -> None:
        """Create enhanced toolbar with responsive design"""
        toolbar_card = ElevatedCardWidget()
        toolbar_layout = QHBoxLayout(toolbar_card)
        
        # Responsive margins
        self._setup_responsive_margins(toolbar_layout)
        toolbar_layout.setSpacing(12)
        
        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title_label = StrongBodyLabel(tr("log_viewer.title"))
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {VidTaniumTheme.FONT_SIZE_HEADING};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD};
                color: {VidTaniumTheme.TEXT_PRIMARY};
                margin: 0;
            }}
        """)
        
        subtitle_label = CaptionLabel(tr("log_viewer.subtitle"))
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_CAPTION};
                margin: 0;
            }}
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        toolbar_layout.addLayout(title_layout)
        
        toolbar_layout.addStretch()
        
        # Control buttons with responsive layout
        self._create_control_buttons(toolbar_layout)
        
        layout.addWidget(toolbar_card)
        self.toolbar = toolbar_card

    def _create_control_buttons(self, layout: QHBoxLayout) -> None:
        """Create control buttons with responsive behavior"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Create button container
        button_container = QWidget()
        if current_bp.value in ['xs', 'sm']:
            # Vertical layout for small screens
            button_layout: Union[QVBoxLayout, QHBoxLayout] = QVBoxLayout(button_container)
            button_layout.setSpacing(8)
        else:
            # Horizontal layout for larger screens
            button_layout = QHBoxLayout(button_container)
            button_layout.setSpacing(12)
        
        # Clear logs button
        self.clear_btn = PushButton(tr("log_viewer.buttons.clear"))
        self.clear_btn.setIcon(FIF.DELETE)
        self.clear_btn.clicked.connect(self._clear_logs)
        self._apply_button_styling(self.clear_btn, "danger")
        
        # Export logs button
        self.export_btn = PushButton(tr("log_viewer.buttons.export"))
        self.export_btn.setIcon(FIF.SAVE)
        self.export_btn.clicked.connect(self._export_logs)
        self._apply_button_styling(self.export_btn, "primary")
        
        # Refresh button
        self.refresh_btn = TransparentToolButton(FIF.SYNC)
        self.refresh_btn.setToolTip(tr("log_viewer.buttons.refresh"))
        self.refresh_btn.clicked.connect(self._refresh_logs)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(button_container)

    def _create_content_area(self, layout: QVBoxLayout):
        """Create content area with responsive splitter"""
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Filter panel (collapsible on small screens)
        self._create_filter_panel(content_splitter)
        
        # Log display area
        self._create_log_display(content_splitter)
        
        # Responsive splitter sizes
        current_bp = self.responsive_manager.get_current_breakpoint()
        if current_bp.value in ['xs', 'sm']:
            # Stack vertically on small screens
            content_splitter.setOrientation(Qt.Orientation.Vertical)
            content_splitter.setSizes([100, 400])
        else:
            # Side by side on larger screens
            content_splitter.setSizes([250, 750])
        
        layout.addWidget(content_splitter)

    def _create_filter_panel(self, parent):
        """Create enhanced filter panel"""
        filter_card = CardWidget()
        filter_card.setObjectName("log-filter-panel")
        filter_layout = QVBoxLayout(filter_card)
        
        # Responsive margins
        self._setup_responsive_margins(filter_layout)
        filter_layout.setSpacing(16)
        
        # Filter header
        filter_header = StrongBodyLabel(tr("log_viewer.filters.title"))
        filter_header.setStyleSheet(f"""
            QLabel {{
                font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
                color: {VidTaniumTheme.TEXT_PRIMARY};
                margin: 0;
            }}
        """)
        filter_layout.addWidget(filter_header)
        
        # Search filter
        search_layout = QVBoxLayout()
        search_layout.setSpacing(8)
        
        search_label = BodyLabel(tr("log_viewer.filters.search"))
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText(tr("log_viewer.filters.search_placeholder"))
        self.search_input.textChanged.connect(self._on_search_changed)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        filter_layout.addLayout(search_layout)
        
        # Level filter
        level_layout = QVBoxLayout()
        level_layout.setSpacing(8)
        
        level_label = BodyLabel(tr("log_viewer.filters.level"))
        self.level_combo = ComboBox()
        self.level_combo.addItems([
            tr("log_viewer.filters.all_levels"),
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        ])
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_combo)
        filter_layout.addLayout(level_layout)
        
        # Time range filter
        time_layout = QVBoxLayout()
        time_layout.setSpacing(8)
        
        time_label = BodyLabel(tr("log_viewer.filters.time_range"))
        self.time_combo = ComboBox()
        self.time_combo.addItems([
            tr("log_viewer.filters.all_time"),
            tr("log_viewer.filters.last_hour"),
            tr("log_viewer.filters.last_day"),
            tr("log_viewer.filters.last_week")
        ])
        self.time_combo.currentTextChanged.connect(self._on_time_changed)
        
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_combo)
        filter_layout.addLayout(time_layout)
        
        filter_layout.addStretch()
        
        parent.addWidget(filter_card)
        self.filter_panel = filter_card

    def _create_log_display(self, parent):
        """Create enhanced log display area"""
        display_card = CardWidget()
        display_card.setObjectName("log-display-area")
        display_layout = QVBoxLayout(display_card)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(0)
        
        # Log display with enhanced styling
        self.log_display = PlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setObjectName("log-text-display")
        
        # Apply enhanced styling
        self._apply_log_display_styling()
        
        display_layout.addWidget(self.log_display)
        parent.addWidget(display_card)

    def _create_enhanced_status_bar(self, layout: QVBoxLayout):
        """Create enhanced status bar"""
        status_card = CardWidget()
        status_card.setObjectName("log-status-bar")
        status_layout = QHBoxLayout(status_card)
        
        # Responsive margins
        self._setup_responsive_margins(status_layout)
        status_layout.setSpacing(16)
        
        # Entry count
        self.entry_count_label = CaptionLabel("0 entries")
        self.entry_count_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_CAPTION};
            }}
        """)
        
        # Filter status
        self.filter_status_label = CaptionLabel("")
        self.filter_status_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_CAPTION};
            }}
        """)
        
        status_layout.addWidget(self.entry_count_label)
        status_layout.addWidget(self.filter_status_label)
        status_layout.addStretch()
        
        # Auto-scroll toggle
        self.auto_scroll_toggle = ToggleButton()
        self.auto_scroll_toggle.setText(tr("log_viewer.auto_scroll"))
        self.auto_scroll_toggle.setChecked(True)
        
        status_layout.addWidget(self.auto_scroll_toggle)
        
        layout.addWidget(status_card)
        self.status_bar = status_card

    def _setup_responsive_margins(self, layout):
        """Setup responsive margins"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        margin_config = {
            'xs': 8,
            'sm': 12,
            'md': 16,
            'lg': 20,
            'xl': 24
        }
        
        margin = margin_config.get(current_bp.value, 16)
        layout.setContentsMargins(margin, margin//2, margin, margin//2)

    def _apply_button_styling(self, button, style_type: str):
        """Apply enhanced button styling"""
        if not self.theme_manager:
            return
            
        colors = self.theme_manager.get_theme_colors() if hasattr(self.theme_manager, 'get_theme_colors') else {}
        
        if style_type == "primary":
            accent_color = getattr(self.theme_manager, 'ACCENT_COLORS', {}).get(
                getattr(self.theme_manager, 'get_current_accent', lambda: 'blue')(), '#0078D4'
            )
            button.setStyleSheet(f"""
                PushButton {{
                    background-color: {accent_color};
                    border: none;
                    border-radius: 6px;
                    color: white;
                    padding: 8px 16px;
                    font-weight: 600;
                }}
                PushButton:hover {{
                    background-color: {accent_color}dd;
                }}
            """)
        elif style_type == "danger":
            button.setStyleSheet(f"""
                PushButton {{
                    background-color: {VidTaniumTheme.ERROR_RED};
                    border: none;
                    border-radius: 6px;
                    color: white;
                    padding: 8px 16px;
                    font-weight: 600;
                }}
                PushButton:hover {{
                    background-color: {VidTaniumTheme.ERROR_RED}dd;
                }}
            """)

    def _apply_log_display_styling(self):
        """Apply enhanced styling to log display"""
        # Get theme colors
        colors = {}
        if self.theme_manager and hasattr(self.theme_manager, 'get_theme_colors'):
            colors = self.theme_manager.get_theme_colors()
        
        background = colors.get('surface', VidTaniumTheme.BG_SURFACE)
        text_color = colors.get('text_primary', VidTaniumTheme.TEXT_PRIMARY)
        border = colors.get('border', VidTaniumTheme.BORDER_LIGHT)
        
        if self.log_display:
            self.log_display.setStyleSheet(f"""
            PlainTextEdit {{
                background-color: {background};
                color: {text_color};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                line-height: 1.4;
            }}
            PlainTextEdit QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                border-radius: 4px;
            }}
            PlainTextEdit QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }}
            """)

    def _setup_responsive_behavior(self):
        """Setup responsive behavior"""
        self.responsive_manager.add_breakpoint_callback(self._on_breakpoint_changed)

    def _on_breakpoint_changed(self, breakpoint: str):
        """Handle breakpoint changes"""
        logger.debug(f"Log viewer adapting to breakpoint: {breakpoint}")
        
        # Update control button layout
        if hasattr(self, 'toolbar'):
            layout = self.layout()
            if layout and isinstance(layout, QVBoxLayout):
                self._create_enhanced_toolbar(layout)
        
        # Update margins throughout
        for widget in [self.toolbar, self.filter_panel, self.status_bar]:
            if widget and widget.layout():
                self._setup_responsive_margins(widget.layout())

    def set_theme_manager(self, theme_manager: EnhancedThemeManager):
        """Set theme manager for enhanced styling"""
        self.theme_manager = theme_manager
        self._apply_log_display_styling()
        
        # Update button styling
        if hasattr(self, 'export_btn'):
            self._apply_button_styling(self.export_btn, "primary")
        if hasattr(self, 'clear_btn'):
            self._apply_button_styling(self.clear_btn, "danger")

    def add_log_entry(self, entry: LogEntry):
        """Add a log entry with performance optimization"""
        self.log_entries.append(entry)
        
        # Limit entries to prevent memory issues
        if len(self.log_entries) > 10000:
            self.log_entries = self.log_entries[-8000:]  # Keep last 8000 entries
        
        # Batch updates for better performance
        if not self._pending_updates:
            self._pending_updates = True
            self._update_timer.start(100)  # Update after 100ms

    def _update_log_display(self):
        """Update log display with current filters"""
        self._pending_updates = False
        self._apply_filters()
        self._refresh_display()
        self._update_status()

    def _apply_filters(self):
        """Apply current filters to log entries"""
        self.filtered_entries = []
        
        for entry in self.log_entries:
            # Level filter
            if (self.current_filters['level'] != 'all' and 
                entry.level.upper() != self.current_filters['level']):
                continue
            
            # Search filter
            if (self.current_filters['search'] and 
                self.current_filters['search'].lower() not in entry.message.lower()):
                continue
            
            # Time filter
            if not self._passes_time_filter(entry):
                continue
            
            self.filtered_entries.append(entry)

    def _passes_time_filter(self, entry: LogEntry) -> bool:
        """Check if entry passes time filter"""
        if self.current_filters['time_range'] == 'all':
            return True
        
        now = datetime.now()
        entry_time = entry.timestamp
        
        if self.current_filters['time_range'] == 'last_hour':
            return bool(entry_time >= now - timedelta(hours=1))
        elif self.current_filters['time_range'] == 'last_day':
            return bool(entry_time >= now - timedelta(days=1))
        elif self.current_filters['time_range'] == 'last_week':
            return bool(entry_time >= now - timedelta(weeks=1))
        
        return True

    def _refresh_display(self):
        """Refresh the log display"""
        if not self.log_display:
            return
        
        self.log_display.clear()
        
        for entry in self.filtered_entries[-1000:]:  # Show last 1000 entries
            formatted_entry = self._format_log_entry(entry)
            self.log_display.appendPlainText(formatted_entry)
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll_toggle and self.auto_scroll_toggle.isChecked():
            cursor = self.log_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_display.setTextCursor(cursor)

    def _format_log_entry(self, entry: LogEntry) -> str:
        """Format a log entry for display"""
        timestamp = entry.timestamp.strftime('%H:%M:%S.%f')[:-3]
        level = entry.level.upper().ljust(8)
        return f"[{timestamp}] {level} {entry.message}"

    def _update_status(self):
        """Update status bar information"""
        total_entries = len(self.log_entries)
        filtered_entries = len(self.filtered_entries)
        
        if self.entry_count_label:
            if total_entries == filtered_entries:
                self.entry_count_label.setText(f"{total_entries} entries")
            else:
                self.entry_count_label.setText(f"{filtered_entries} of {total_entries} entries")
        
        # Update filter status
        active_filters = []
        if self.current_filters['level'] != 'all':
            active_filters.append(f"Level: {self.current_filters['level']}")
        if self.current_filters['search']:
            active_filters.append(f"Search: {self.current_filters['search']}")
        if self.current_filters['time_range'] != 'all':
            active_filters.append(f"Time: {self.current_filters['time_range']}")
        
        if self.filter_status_label:
            if active_filters:
                self.filter_status_label.setText(f"Filters: {', '.join(active_filters)}")
            else:
                self.filter_status_label.setText("")

    def _on_search_changed(self, text: str):
        """Handle search filter change"""
        self.current_filters['search'] = text
        self._update_log_display()

    def _on_level_changed(self, level: str):
        """Handle level filter change"""
        if level == tr("log_viewer.filters.all_levels"):
            self.current_filters['level'] = 'all'
        else:
            self.current_filters['level'] = level
        self._update_log_display()

    def _on_time_changed(self, time_range: str):
        """Handle time range filter change"""
        time_map = {
            tr("log_viewer.filters.all_time"): 'all',
            tr("log_viewer.filters.last_hour"): 'last_hour',
            tr("log_viewer.filters.last_day"): 'last_day',
            tr("log_viewer.filters.last_week"): 'last_week'
        }
        self.current_filters['time_range'] = time_map.get(time_range, 'all')
        self._update_log_display()

    def _clear_logs(self):
        """Clear all log entries"""
        self.log_entries.clear()
        self.filtered_entries.clear()
        if self.log_display:
            self.log_display.clear()
        self._update_status()
        self.log_cleared.emit()

    def _refresh_logs(self):
        """Refresh log display"""
        self._update_log_display()

    def _export_logs(self):
        """Export logs to file"""
        if not self.filtered_entries:
            InfoBar.warning(
                title=tr("log_viewer.messages.warning"),
                content=tr("log_viewer.messages.no_logs_to_export"),
                parent=self
            )
            return
        
        # Show export dialog
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setNameFilters([
            "Text files (*.txt)",
            "HTML files (*.html)",
            "JSON files (*.json)",
            "CSV files (*.csv)"
        ])
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            selected_filter = file_dialog.selectedNameFilter()
            
            # Determine format
            if "*.txt" in selected_filter:
                format_type = "txt"
            elif "*.html" in selected_filter:
                format_type = "html"
            elif "*.json" in selected_filter:
                format_type = "json"
            elif "*.csv" in selected_filter:
                format_type = "csv"
            else:
                format_type = "txt"
            
            self.export_requested.emit(format_type, file_path)


# Backward compatibility alias
LogViewer = EnhancedLogViewer


class LogExportWorker:
    """Worker class for log export operations using thread pool"""

    def __init__(self, log_entries: List[LogEntry], export_path: str, export_format: str = "txt"):
        self.log_entries = log_entries
        self.export_path = export_path
        self.export_format = export_format

    def export_logs(self) -> str:
        """Export logs and return success message"""
        try:
            total_entries = len(self.log_entries)
            if total_entries == 0:
                raise ValueError("没有日志条目可导出")

            if self.export_format == "txt":
                self._export_as_txt()
            elif self.export_format == "html":
                self._export_as_html()
            elif self.export_format == "json":
                self._export_as_json()
            elif self.export_format == "csv":
                self._export_as_csv()
            else:
                raise ValueError(f"不支持的导出格式: {self.export_format}")

            return f"成功导出 {total_entries} 条日志到 {self.export_path}"

        except Exception as e:
            raise Exception(f"导出失败: {str(e)}")

    def _export_as_txt(self):
        """Export logs as text file"""
        with open(self.export_path, 'w', encoding='utf-8') as f:
            f.write("VidTanium 日志导出\n")
            f.write("=" * 50 + "\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"日志条目总数: {len(self.log_entries)}\n\n")

            for entry in self.log_entries:
                f.write(
                    f"[{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] ")
                f.write(f"{entry.level.upper()}: {entry.message}\n")
                if hasattr(entry, 'source') and getattr(entry, 'source', None):
                    f.write(f"  来源: {getattr(entry, 'source', '')}\n")
                f.write("\n")

    def _export_as_html(self):
        """Export logs as HTML file"""
        with open(self.export_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>VidTanium 日志导出</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #0078d4; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .log-entry { background: white; margin: 8px 0; padding: 12px; border-radius: 6px; border-left: 4px solid #ccc; }
        .DEBUG { border-left-color: #666; }
        .INFO { border-left-color: #0078d4; }
        .WARNING { border-left-color: #ffb900; }
        .ERROR { border-left-color: #d13438; }
        .CRITICAL { border-left-color: #a80000; }
        .timestamp { color: #666; font-size: 0.9em; }
        .level { font-weight: bold; padding: 2px 8px; border-radius: 4px; color: white; }
        .level.DEBUG { background: #666; }
        .level.INFO { background: #0078d4; }
        .level.WARNING { background: #ffb900; }
        .level.ERROR { background: #d13438; }
        .level.CRITICAL { background: #a80000; }
        .message { margin: 8px 0; }
        .source { color: #666; font-style: italic; font-size: 0.9em; }
    </style>
</head>
<body>""")

            f.write(f"""
    <div class="header">
        <h1>VidTanium 日志导出</h1>
        <p>导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>日志条目总数: {len(self.log_entries)}</p>
    </div>
""")

            for entry in self.log_entries:
                level_class = entry.level.upper()
                f.write(f"""
    <div class="log-entry {level_class}">
        <div class="timestamp">{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}</div>
        <span class="level {level_class}">{entry.level.upper()}</span>
        <div class="message">{entry.message}</div>""")

                if hasattr(entry, 'source') and getattr(entry, 'source', None):
                    f.write(
                        f'        <div class="source">来源: {getattr(entry, "source", "")}</div>')

                f.write("    </div>")

            f.write("""
</body>
</html>""")

    def _export_as_json(self):
        """Export logs as JSON file"""
        from typing import List, Dict, Any
        data: Dict[str, Any] = {
            "export_info": {
                "export_time": datetime.now().isoformat(),
                "total_entries": len(self.log_entries),
                "application": "VidTanium"
            },
            "logs": []
        }

        for entry in self.log_entries:
            log_data = {
                "timestamp": entry.timestamp.isoformat(),
                "level": entry.level,
                "message": entry.message
            }
            if hasattr(entry, 'source') and getattr(entry, 'source', None):
                log_data["source"] = getattr(entry, 'source', '')

            data["logs"].append(log_data)

        with open(self.export_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _export_as_csv(self):
        """Export logs as CSV file"""
        import csv

        with open(self.export_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["时间戳", "级别", "消息", "来源"])

            for entry in self.log_entries:
                source = getattr(entry, 'source', '') or ''
                writer.writerow([
                    entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    entry.level,
                    entry.message,
                    source
                ])


class AdvancedLogFilter(ElevatedCardWidget):
    """Advanced log filtering widget with multiple criteria"""

    filterChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.date_filter_enabled = False
        self.time_range_start = None
        self.time_range_end = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Title
        title_label = StrongBodyLabel("日志筛选")
        title_label.setStyleSheet(
            "font-size: 14px; color: #323130; margin-bottom: 8px;")
        layout.addWidget(title_label)

        # Quick filters row
        quick_filters_layout = QHBoxLayout()

        # Time range quick filters
        self.time_quick_combo = ComboBox()
        self.time_quick_combo.addItems([
            "全部时间",
            "最近1小时",
            "最近6小时",
            "最近24小时",
            "最近3天",
            "最近7天",
            "自定义时间"
        ])
        self.time_quick_combo.currentTextChanged.connect(
            self._on_time_filter_changed)

        quick_filters_layout.addWidget(CaptionLabel("时间范围:"))
        quick_filters_layout.addWidget(self.time_quick_combo)
        quick_filters_layout.addStretch()

        layout.addLayout(quick_filters_layout)

        # Level filter with counts
        level_layout = QHBoxLayout()
        self.level_checkboxes = {}

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            checkbox = CheckBox(level)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self.filterChanged.emit)
            self.level_checkboxes[level] = checkbox
            level_layout.addWidget(checkbox)

        level_layout.addStretch()
        layout.addLayout(level_layout)

        # Advanced search
        search_layout = QHBoxLayout()
        self.regex_search = SearchLineEdit()
        self.regex_search.setPlaceholderText("支持正则表达式搜索...")
        self.regex_search.textChanged.connect(self.filterChanged.emit)

        self.regex_enabled = CheckBox("启用正则")
        self.regex_enabled.toggled.connect(self.filterChanged.emit)

        search_layout.addWidget(self.regex_search, 1)
        search_layout.addWidget(self.regex_enabled)

        layout.addLayout(search_layout)

    def _on_time_filter_changed(self, filter_text: str):
        now = datetime.now()

        if filter_text == "全部时间":
            self.date_filter_enabled = False
        elif filter_text == "最近1小时":
            self.date_filter_enabled = True
            self.time_range_start = now - timedelta(hours=1)
            self.time_range_end = now
        elif filter_text == "最近6小时":
            self.date_filter_enabled = True
            self.time_range_start = now - timedelta(hours=6)
            self.time_range_end = now
        elif filter_text == "最近24小时":
            self.date_filter_enabled = True
            self.time_range_start = now - timedelta(hours=24)
            self.time_range_end = now
        elif filter_text == "最近3天":
            self.date_filter_enabled = True
            self.time_range_start = now - timedelta(days=3)
            self.time_range_end = now
        elif filter_text == "最近7天":
            self.date_filter_enabled = True
            self.time_range_start = now - timedelta(days=7)
            self.time_range_end = now
        elif filter_text == "自定义时间":
            # TODO: Show date/time picker dialog
            pass

        self.filterChanged.emit()

    def get_enabled_levels(self) -> List[str]:
        return [level for level, checkbox in self.level_checkboxes.items()
                if checkbox.isChecked()]

    def get_search_text(self) -> str:
        return str(self.regex_search.text())

    def is_regex_enabled(self) -> bool:
        return bool(self.regex_enabled.isChecked())

    def should_include_entry(self, entry: LogEntry) -> bool:
        # Time filter
        if self.date_filter_enabled:
            if self.time_range_start and entry.timestamp < self.time_range_start:
                return False
            if self.time_range_end and entry.timestamp > self.time_range_end:
                return False

        # Level filter
        if entry.level not in self.get_enabled_levels():
            return False

        # Search filter
        search_text = self.get_search_text()
        if search_text:
            search_content = f"{entry.message} {getattr(entry, 'source', '')}"

            if self.is_regex_enabled():
                try:
                    if not re.search(search_text, search_content, re.IGNORECASE):
                        return False
                except re.error:
                    # Invalid regex, fall back to plain text search
                    if search_text.lower() not in search_content.lower():
                        return False
            else:
                if search_text.lower() not in search_content.lower():
                    return False

        return True


class LogDetailViewer(FluentTextEdit):
    """Detailed view for individual log entries"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(200)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.4;
            }
        """)

    def show_log_entry(self, entry: LogEntry):
        details = f"""时间: {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}
级别: {entry.level.upper()}
消息: {entry.message}"""

        if hasattr(entry, 'source'):
            source = getattr(entry, 'source', '')
            if source:
                details += f"\n来源: {source}"

        # Add any additional details if available
        if hasattr(entry, 'details') and entry.details:
            details += f"\n\n详细信息:\n{entry.details}"

        self.setPlainText(details)


class CustomSeparator(QWidget):
    """Custom separator widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.1);
                border: none;
            }
        """)


class ModernBadge(QLabel):
    """Modern badge widget with Fluent Design"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #69797e;
                color: white;
                border-radius: 10px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
                min-width: 50px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)

    def setLevel(self, level: str):
        """Set badge style based on log level"""
        level_colors = {
            'DEBUG': '#666666',
            'INFO': '#0078d4',
            'WARNING': '#ffb900',
            'ERROR': '#d13438',
            'CRITICAL': '#a80000'
        }

        color = level_colors.get(level.upper(), '#666666')
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
                min-width: 50px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }}
        """)


class EnhancedLogEntry(ElevatedCardWidget):
    """Enhanced log entry widget with interactive features"""

    entryClicked = Signal(LogEntry)
    entryDoubleClicked = Signal(LogEntry)

    def __init__(self, log_entry: LogEntry, parent=None):
        super().__init__(parent)
        self.log_entry = log_entry
        self.is_selected = False
        self._create_ui()
        self._setup_style()

    def _create_ui(self):
        """Create the enhanced log entry UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Timestamp with modern styling
        time_label = CaptionLabel(
            self.log_entry.timestamp.strftime("%H:%M:%S.%f")[:-3])
        time_label.setFixedWidth(80)
        time_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        time_label.setStyleSheet("""
            CaptionLabel {
                color: #666;
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 11px;
                font-weight: 500;
                background-color: rgba(0, 0, 0, 0.03);
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)

        # Level badge with modern design
        level_badge = ModernBadge(self.log_entry.level)
        level_badge.setLevel(self.log_entry.level)
        level_badge.setFixedWidth(60)

        # Message with enhanced typography
        message_label = BodyLabel(self.log_entry.message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        message_label.setStyleSheet("""
            BodyLabel {
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 13px;
                line-height: 1.4;
                color: #323130;
            }
        """)

        # Source info with modern styling
        source_text = getattr(self.log_entry, 'source', '') or ''
        if source_text:
            source_label = CaptionLabel(f"[{source_text}]")
            source_label.setStyleSheet("""
                CaptionLabel {
                    color: #605e5c;
                    font-family: 'Segoe UI', 'Microsoft YaHei';
                    font-size: 10px;
                    background-color: rgba(96, 94, 92, 0.1);
                    border-radius: 4px;
                    padding: 2px 6px;
                }
            """)
            source_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        else:
            source_label = QLabel()
            source_label.setVisible(False)

        layout.addWidget(time_label)
        layout.addWidget(level_badge)
        layout.addWidget(message_label, 1)
        layout.addWidget(source_label)

        self.setMinimumHeight(48)
        self.setMaximumHeight(120)

    def _setup_style(self):
        """Setup enhanced entry styling"""
        level_bg_colors = {
            'DEBUG': 'rgba(102, 102, 102, 0.02)',
            'INFO': 'rgba(0, 120, 212, 0.02)',
            'WARNING': 'rgba(255, 185, 0, 0.02)',
            'ERROR': 'rgba(209, 52, 56, 0.02)',
            'CRITICAL': 'rgba(168, 0, 0, 0.02)'
        }

        bg_color = level_bg_colors.get(
            self.log_entry.level.upper(), 'transparent')
        self.setStyleSheet(f"""
            EnhancedLogEntry {{
                background-color: {bg_color};
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.05);
                margin: 2px 0px;
            }}
            EnhancedLogEntry:hover {{
                background-color: rgba(0, 120, 212, 0.06);
                border: 1px solid rgba(0, 120, 212, 0.15);
            }}
        """)

    def mousePressEvent(self, e):
        """Handle mouse press events"""
        if e.button() == Qt.MouseButton.LeftButton:
            self.entryClicked.emit(self.log_entry)
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, event):
        """Handle double click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.entryDoubleClicked.emit(self.log_entry)
        super().mouseDoubleClickEvent(event)

    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet(self.styleSheet() + """
                EnhancedLogEntry {
                    background-color: rgba(0, 120, 212, 0.1);
                    border: 2px solid #0078d4;
                }
            """)


class EnhancedPaginatedLogContainer(QWidget):
    """Enhanced paginated container for log entries with advanced features"""

    entrySelected = Signal(LogEntry)
    entryDoubleClicked = Signal(LogEntry)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_entries: List[LogEntry] = []
        self.filtered_entries: List[LogEntry] = []
        self.entries_per_page = 50
        self.current_page = 0
        self.selected_entry: Optional[LogEntry] = None
        self.entry_widgets: List[EnhancedLogEntry] = []
        self._setup_ui()

    def _setup_ui(self):
        """Setup the enhanced paginated UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Log entries container
        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(2)

        # Empty state
        self.empty_widget = self._create_empty_state()
        self.log_layout.addWidget(self.empty_widget)
        self.log_layout.addStretch()

        self.scroll_area.setWidget(self.log_container)
        layout.addWidget(self.scroll_area, 1)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        pagination_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Page info
        self.page_info_label = CaptionLabel("第 0 页，共 0 页")
        self.page_info_label.setStyleSheet("color: #666; font-size: 12px;")

        # Pagination widget
        self.pager = PipsPager()
        self.pager.setPageNumber(1)
        self.pager.setVisibleNumber(10)
        self.pager.currentIndexChanged.connect(self._on_page_changed)

        # Page size control
        page_size_layout = QHBoxLayout()
        page_size_label = CaptionLabel("每页条数:")
        self.page_size_combo = ComboBox()
        self.page_size_combo.addItems(["25", "50", "100", "200"])
        self.page_size_combo.setCurrentText("50")
        self.page_size_combo.currentTextChanged.connect(
            self._on_page_size_changed)

        page_size_layout.addWidget(page_size_label)
        page_size_layout.addWidget(self.page_size_combo)

        pagination_layout.addLayout(page_size_layout)
        pagination_layout.addSpacing(20)
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addSpacing(20)
        pagination_layout.addWidget(self.pager)

        layout.addLayout(pagination_layout)

    def _create_empty_state(self) -> QWidget:
        """Create modern empty state widget"""
        widget = ElevatedCardWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # Icon with modern styling
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setPixmap(FIF.HISTORY.icon().pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel { 
                opacity: 0.6; 
                background-color: rgba(0, 120, 212, 0.1);
                border-radius: 32px;
                padding: 16px;
            }
        """)

        # Enhanced text
        title_label = SubtitleLabel("暂无日志条目")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 18px; color: #323130; font-weight: 600;")

        desc_label = BodyLabel("应用程序运行时的日志消息将显示在这里")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #605e5c; font-size: 14px;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        return cast(QWidget, widget)

    def _on_page_changed(self, index: int):
        """Handle page change"""
        self.current_page = index
        self._update_display()

    def _on_page_size_changed(self, size_text: str):
        """Handle page size change"""
        try:
            new_size = int(size_text)
            self.entries_per_page = new_size
            self.current_page = 0
            self._update_pagination()
            self._update_display()
        except ValueError:
            pass

    def add_log_entry(self, entry: LogEntry):
        """Add a new log entry"""
        self.log_entries.append(entry)
        self.filtered_entries = self.log_entries.copy()  # Reset filter
        self._update_pagination()

        # If we're on the last page, show the new entry
        total_pages = max(1, (len(self.filtered_entries) +
                          self.entries_per_page - 1) // self.entries_per_page)
        if self.current_page == total_pages - 1:
            self._update_display()

    def clear_entries(self):
        """Clear all log entries"""
        self.log_entries.clear()
        self.filtered_entries.clear()
        self.current_page = 0
        self.selected_entry = None
        self._update_pagination()
        self._update_display()

    def apply_filter(self, filter_func):
        """Apply a filter function to entries"""
        self.filtered_entries = [
            entry for entry in self.log_entries if filter_func(entry)]
        self.current_page = 0
        self._update_pagination()
        self._update_display()

    def _update_pagination(self):
        """Update pagination controls"""
        total_entries = len(self.filtered_entries)
        total_pages = max(
            1, (total_entries + self.entries_per_page - 1) // self.entries_per_page)

        self.pager.setPageNumber(total_pages)

        # Update page info
        if total_entries == 0:
            self.page_info_label.setText("暂无数据")
        else:
            current_page_display = self.current_page + 1
            self.page_info_label.setText(
                f"第 {current_page_display} 页，共 {total_pages} 页 (总计 {total_entries} 条)")

    def _update_display(self):
        """Update the displayed log entries for current page"""
        # Clear existing widgets (except empty state and stretch)
        self.entry_widgets.clear()
        while self.log_layout.count() > 2:
            child = self.log_layout.takeAt(1)
            if child.widget():
                child.widget().deleteLater()

        total_entries = len(self.filtered_entries)

        if total_entries == 0:
            self.empty_widget.setVisible(True)
            return

        self.empty_widget.setVisible(False)

        # Calculate entries for current page
        start_idx = self.current_page * self.entries_per_page
        end_idx = min(start_idx + self.entries_per_page, total_entries)

        # Add entries for current page
        for i in range(start_idx, end_idx):
            entry_widget = EnhancedLogEntry(self.filtered_entries[i])
            entry_widget.entryClicked.connect(self._on_entry_clicked)
            entry_widget.entryDoubleClicked.connect(
                self._on_entry_double_clicked)

            self.entry_widgets.append(entry_widget)
            self.log_layout.insertWidget(
                self.log_layout.count() - 1, entry_widget)

        # Auto-scroll to top of page
        QTimer.singleShot(
            10, lambda: self.scroll_area.verticalScrollBar().setValue(0))

    def _on_entry_clicked(self, entry: LogEntry):
        """Handle entry click"""
        # Clear previous selection
        for widget in self.entry_widgets:
            widget.set_selected(False)

        # Set new selection
        sender = self.sender()
        if isinstance(sender, EnhancedLogEntry):
            sender.set_selected(True)
            self.selected_entry = entry
            self.entrySelected.emit(entry)

    def _on_entry_double_clicked(self, entry: LogEntry):
        """Handle entry double click"""
        self.entryDoubleClicked.emit(entry)

    def get_selected_entry(self) -> Optional[LogEntry]:
        """Get currently selected entry"""
        return self.selected_entry


class ComprehensiveLogViewer(QWidget):
    """Enhanced log viewer with comprehensive features and modern design"""

    # Signals
    logCleared = Signal()
    logSaved = Signal(str)
    logEntrySelected = Signal(LogEntry)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.max_log_entries: int = 10000  # Increased for better pagination
        self.auto_scroll_enabled: bool = True
        self.auto_refresh_enabled: bool = True
        self.refresh_interval: int = 5000  # 5 seconds

        # Statistics
        self.log_stats: Dict[str, int] = {
            'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0
        }

        # Initialize UI components
        self.advanced_filter: Optional[AdvancedLogFilter] = None
        self.log_container: Optional[EnhancedPaginatedLogContainer] = None
        self.log_detail_viewer: Optional[LogDetailViewer] = None
        self.current_export_worker: Optional[Any] = None

        # Statistics widgets
        self.debug_stat: Optional[QWidget] = None
        self.info_stat: Optional[QWidget] = None
        self.warning_stat: Optional[QWidget] = None
        self.error_stat: Optional[QWidget] = None

        # Timers
        self.cleanup_timer = QTimer(self)
        self.refresh_timer = QTimer(self)

        self._create_ui()
        self._setup_timers()
        self._connect_signals()

    def _create_ui(self):
        """Create the enhanced UI with modern design"""
        from PySide6.QtWidgets import QSizePolicy
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)  # Reduced spacing

        # Header with themed design - more compact
        header_card = ElevatedCardWidget()
        header_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_card.setStyleSheet(VidTaniumTheme.get_card_style())
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(
            20, 12, 20, 12)  # Reduced vertical padding
        header_layout.setSpacing(8)  # Reduced spacing

        # Title section with modern typography
        title_section = QHBoxLayout()

        # Modern title with icon - more compact
        title_container = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(FIF.HISTORY.icon().pixmap(20, 20))  # Smaller icon
        title_icon.setStyleSheet("margin-right: 6px;")

        title_label = SubtitleLabel("活动日志")  # Simplified title
        title_label.setStyleSheet(f"""
            font-size: {VidTaniumTheme.FONT_SIZE_HEADING}; 
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD}; 
            color: {VidTaniumTheme.TEXT_PRIMARY};
        """)  # Themed styling

        title_container.addWidget(title_icon)
        title_container.addWidget(title_label)
        title_container.addStretch()

        # Enhanced statistics with modern cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)  # Reduced spacing for better alignment
        stats_layout.setContentsMargins(0, 0, 0, 0)

        # Statistics badges with themed colors
        self.debug_stat = self._create_modern_stat_badge(
            "调试", 0, VidTaniumTheme.TEXT_TERTIARY)
        self.info_stat = self._create_modern_stat_badge(
            "信息", 0, VidTaniumTheme.INFO_BLUE)
        self.warning_stat = self._create_modern_stat_badge(
            "警告", 0, VidTaniumTheme.WARNING_ORANGE)
        self.error_stat = self._create_modern_stat_badge(
            "错误", 0, VidTaniumTheme.ERROR_RED)

        stats_layout.addWidget(self.debug_stat)
        stats_layout.addWidget(self.info_stat)
        stats_layout.addWidget(self.warning_stat)
        stats_layout.addWidget(self.error_stat)
        # Remove excessive stretch

        title_section.addLayout(title_container)
        title_section.addStretch()
        title_section.addLayout(stats_layout)

        header_layout.addLayout(title_section)

        # Enhanced controls section - more compact
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        controls_layout.setContentsMargins(0, 8, 0, 0)

        # Options - grouped together
        options_layout = QHBoxLayout()
        options_layout.setSpacing(16)

        self.auto_scroll_check = CheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.toggled.connect(self._on_auto_scroll_toggled)

        self.auto_refresh_check = CheckBox("自动刷新")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.toggled.connect(self._on_auto_refresh_toggled)

        options_layout.addWidget(self.auto_scroll_check)
        options_layout.addWidget(self.auto_refresh_check)

        # Action buttons with modern styling - more compact
        button_container = QHBoxLayout()
        button_container.setSpacing(6)

        self.clear_btn = PushButton("清空日志")  # More descriptive text
        self.clear_btn.setIcon(FIF.DELETE)
        self.clear_btn.clicked.connect(self._clear_logs)
        self.clear_btn.setMinimumWidth(90)

        self.export_btn = PushButton("导出日志")  # More descriptive text
        self.export_btn.setIcon(FIF.SAVE)
        self.export_btn.clicked.connect(self._export_logs)
        self.export_btn.setMinimumWidth(90)

        self.refresh_btn = TransparentToolButton(FIF.SYNC)
        self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.setToolTip("手动刷新")
        self.refresh_btn.clicked.connect(self._refresh_logs)

        button_container.addWidget(self.clear_btn)
        button_container.addWidget(self.export_btn)
        button_container.addWidget(self.refresh_btn)

        # Arrange controls with better spacing
        controls_layout.addLayout(options_layout)
        controls_layout.addStretch()
        controls_layout.addLayout(button_container)

        header_layout.addLayout(controls_layout)
        layout.addWidget(header_card)

        # Main content area with improved layout
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Filter section at top (more accessible)
        filter_card = ElevatedCardWidget()
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(16, 8, 16, 8)
        filter_layout.setSpacing(12)

        # Time range filter
        time_label = CaptionLabel("时间范围:")
        self.time_filter_combo = ComboBox()
        self.time_filter_combo.addItems(["全部", "最近1小时", "最近6小时", "最近1天"])
        self.time_filter_combo.setFixedWidth(120)

        # Level checkboxes - horizontal layout
        level_layout = QHBoxLayout()
        level_layout.setSpacing(8)
        self.level_checkboxes = {}
        for level, label in [("DEBUG", "DE"), ("INFO", "I"), ("WARNING", "WARN"), ("ERROR", "ER"), ("CRITICAL", "CRIT")]:
            checkbox = CheckBox(label)
            checkbox.setChecked(True)
            checkbox.setToolTip(level)
            self.level_checkboxes[level] = checkbox
            level_layout.addWidget(checkbox)

        # Search box
        self.search_box = SearchLineEdit()
        self.search_box.setPlaceholderText("支持正则表达式搜索...")
        self.search_box.setFixedWidth(200)

        self.regex_enabled = CheckBox("启用正则")

        # Layout filter controls horizontally
        filter_layout.addWidget(time_label)
        filter_layout.addWidget(self.time_filter_combo)
        filter_layout.addLayout(level_layout)
        filter_layout.addStretch()
        filter_layout.addWidget(self.search_box)
        filter_layout.addWidget(self.regex_enabled)

        content_layout.addWidget(filter_card)

        # Log container - full width
        self.log_container = EnhancedPaginatedLogContainer()
        content_layout.addWidget(self.log_container, 1)

        layout.addWidget(content_widget, 1)

    def _create_modern_stat_badge(self, label: str, count: int, color: str) -> QWidget:
        """Create a modern statistics badge with themed design"""
        widget = CardWidget()
        widget.setFixedSize(80, 50)  # Smaller, more compact size
        widget.setStyleSheet(VidTaniumTheme.get_card_style())

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Count with themed typography
        count_label = StrongBodyLabel(str(count))
        count_label.setStyleSheet(f"""
            StrongBodyLabel {{
                font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING}; 
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD};
                color: {color};
            }}
        """)
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Label with themed styling
        label_label = CaptionLabel(label)
        label_label.setStyleSheet(f"""
            CaptionLabel {{
                color: {VidTaniumTheme.TEXT_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_MICRO};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_MEDIUM};
            }}
        """)
        label_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(count_label)
        layout.addWidget(label_label)

        # Store references for updates
        setattr(widget, 'count_label', count_label)
        setattr(widget, 'color', color)

        # Add subtle border based on color
        widget.setStyleSheet(f"""
            CardWidget {{
                border-left: 3px solid {color};
                background-color: rgba(255, 255, 255, 0.8);
            }}
            CardWidget:hover {{
                background-color: rgba(255, 255, 255, 1.0);
            }}
        """)

        return cast(QWidget, widget)

    def _setup_timers(self):
        """Setup automatic timers"""
        # Cleanup timer
        if not hasattr(self, 'cleanup_timer') or self.cleanup_timer is None:
            self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self._cleanup_old_entries)
        self.cleanup_timer.start(60000)  # Clean up every minute

        # Auto-refresh timer
        if not hasattr(self, 'refresh_timer') or self.refresh_timer is None:
            self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(self.refresh_interval)

    def _connect_signals(self):
        """Connect internal signals"""
        # Connect new filter controls
        if hasattr(self, 'time_filter_combo'):
            self.time_filter_combo.currentTextChanged.connect(
                self._apply_filter)

        if hasattr(self, 'search_box'):
            self.search_box.textChanged.connect(self._apply_filter)

        if hasattr(self, 'regex_enabled'):
            self.regex_enabled.toggled.connect(self._apply_filter)

        # Connect level checkboxes
        if hasattr(self, 'level_checkboxes'):
            for checkbox in self.level_checkboxes.values():
                checkbox.toggled.connect(self._apply_filter)

        if self.log_container:
            self.log_container.entrySelected.connect(self._on_entry_selected)
            self.log_container.entryDoubleClicked.connect(
                self._on_entry_double_clicked)

    def _on_auto_scroll_toggled(self, enabled: bool):
        """Handle auto-scroll toggle"""
        self.auto_scroll_enabled = enabled

    def _on_auto_refresh_toggled(self, enabled: bool):
        """Handle auto-refresh toggle"""
        self.auto_refresh_enabled = enabled
        if enabled:
            if not hasattr(self, 'refresh_timer') or self.refresh_timer is None:
                self.refresh_timer = QTimer(self)
                self.refresh_timer.timeout.connect(self._auto_refresh)
            self.refresh_timer.start(self.refresh_interval)
        else:
            if hasattr(self, 'refresh_timer') and self.refresh_timer is not None:
                self.refresh_timer.stop()

    def _apply_advanced_filter(self):
        """Apply advanced filter to log entries"""
        if not self.log_container or not self.advanced_filter:
            return

        self.log_container.apply_filter(
            self.advanced_filter.should_include_entry)

        # Show filter feedback
        filtered_count = len(self.log_container.filtered_entries)
        total_count = len(self.log_container.log_entries)

        if filtered_count != total_count:
            InfoBar.info(
                title="筛选结果",
                content=f"从 {total_count} 条记录中筛选出 {filtered_count} 条",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def _on_entry_selected(self, entry: LogEntry):
        """Handle log entry selection"""
        if self.log_detail_viewer:
            self.log_detail_viewer.show_log_entry(entry)
        self.logEntrySelected.emit(entry)

    def _on_entry_double_clicked(self, entry: LogEntry):
        """Handle log entry double-click"""
        # Show detailed dialog or expanded view
        InfoBar.info(
            title="日志详情",
            content=f"双击了日志: {entry.message[:50]}...",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def _clear_logs(self):
        """Clear all log entries with confirmation - now non-blocking"""
        def clear_operation():
            """Actual clearing operation run in thread pool"""
            try:
                if self.log_container:
                    # Get current count for reporting
                    count = len(self.log_container.log_entries)
                    # Clear entries
                    self.log_container.clear_entries()
                    return count
                return 0
            except Exception as e:
                raise Exception(f"清空日志失败: {str(e)}")

        def on_clear_success(count):
            """Handle successful clearing"""
            self.log_stats = {level: 0 for level in self.log_stats}
            self._update_statistics()

            # Clear detail viewer
            if self.log_detail_viewer:
                self.log_detail_viewer.clear()

            # Show success info
            InfoBar.success(
                title="清空完成",
                content=f"已清空 {count} 条日志记录",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self
            )
            self.logCleared.emit()

        def on_clear_error(error_info):
            """Handle clearing error"""
            exc_type, exc_value, exc_traceback = error_info
            InfoBar.error(
                title="清空失败",
                content=str(exc_value),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

        # Show immediate feedback
        InfoBar.info(
            title="清空中...",
            content="正在清空日志记录",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        )

        # Submit to thread pool for non-blocking operation
        if THREAD_POOL_AVAILABLE:
            submit_task(
                clear_operation,
                callback=on_clear_success,
                error_callback=on_clear_error
            )
        else:
            # Fallback to direct execution if thread pool not available
            try:
                count = clear_operation()
                on_clear_success(count)
            except Exception as e:
                on_clear_error((type(e), e, None))

    def _export_logs(self):
        """Export logs with format selection - now using thread pool"""
        if not self.log_container or not self.log_container.filtered_entries:
            InfoBar.warning(
                title="导出警告",
                content="没有可导出的日志条目",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # Check if export is already in progress
        if self.current_export_worker is not None:
            InfoBar.warning(
                title="导出进行中",
                content="当前已有导出任务正在进行，请等待完成后再试",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # Show format selection dialog
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setNameFilters([
            "文本文件 (*.txt)",
            "HTML文件 (*.html)",
            "JSON文件 (*.json)",
            "CSV文件 (*.csv)"
        ])
        file_dialog.setDefaultSuffix("txt")
        file_dialog.selectFile(f"vidtanium_logs_{timestamp}")

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            selected_filter = file_dialog.selectedNameFilter()

            # Determine format from filter
            if "HTML" in selected_filter:
                export_format = "html"
            elif "JSON" in selected_filter:
                export_format = "json"
            elif "CSV" in selected_filter:
                export_format = "csv"
            else:
                export_format = "txt"

            # Create export worker
            export_worker = LogExportWorker(
                self.log_container.filtered_entries, file_path, export_format)

            def on_export_success(message):
                """Handle successful export"""
                self.current_export_worker = None
                InfoBar.success(
                    title="导出完成",
                    content=message,
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                self.logSaved.emit(message)

            def on_export_error(error_info):
                """Handle export error"""
                self.current_export_worker = None
                exc_type, exc_value, exc_traceback = error_info
                InfoBar.error(
                    title="导出失败",
                    content=str(exc_value),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

            # Show immediate feedback
            InfoBar.info(
                title="导出中...",
                content=f"正在导出 {len(self.log_container.filtered_entries)} 条日志",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

            # Submit to thread pool
            if THREAD_POOL_AVAILABLE:
                self.current_export_worker = submit_task(
                    export_worker.export_logs,
                    callback=on_export_success,
                    error_callback=on_export_error
                )
            else:
                # Fallback to direct execution if thread pool not available
                try:
                    result = export_worker.export_logs()
                    on_export_success(result)
                except Exception as e:
                    on_export_error((type(e), e, None))

    def _refresh_logs(self):
        """Manual refresh of log display - now non-blocking"""
        def refresh_operation():
            """Actual refresh operation"""
            try:
                if self.advanced_filter:
                    # Apply current filters
                    return "refresh_completed"
                return "no_filter"
            except Exception as e:
                raise Exception(f"刷新失败: {str(e)}")

        def on_refresh_success(result):
            """Handle successful refresh"""
            if result == "refresh_completed":
                self._apply_advanced_filter()

            InfoBar.success(
                title="刷新完成",
                content="日志显示已刷新",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1000,
                parent=self
            )

        def on_refresh_error(error_info):
            """Handle refresh error"""
            exc_type, exc_value, exc_traceback = error_info
            InfoBar.error(
                title="刷新失败",
                content=str(exc_value),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

        # Submit to thread pool for non-blocking operation
        if THREAD_POOL_AVAILABLE:
            submit_task(
                refresh_operation,
                callback=on_refresh_success,
                error_callback=on_refresh_error
            )
        else:
            # Fallback to direct execution if thread pool not available
            try:
                result = refresh_operation()
                on_refresh_success(result)
            except Exception as e:
                on_refresh_error((type(e), e, None))

    def _auto_refresh(self):
        """Auto refresh if enabled"""
        if self.auto_refresh_enabled:
            self._apply_advanced_filter()

    def _cleanup_old_entries(self):
        """Clean up old log entries to prevent memory issues"""
        if not self.log_container:
            return

        if len(self.log_container.log_entries) > self.max_log_entries:
            # Remove oldest entries
            excess_count = len(
                self.log_container.log_entries) - self.max_log_entries

            for _ in range(excess_count):
                if self.log_container.log_entries:
                    self.log_container.log_entries.pop(0)
                    removed_entry = self.log_container.log_entries.pop(0)
                    self.log_stats[removed_entry.level] = max(
                        0, self.log_stats[removed_entry.level] - 1)

            # Update filtered entries as well
            self.log_container.filtered_entries = [
                entry for entry in self.log_container.filtered_entries
                if entry in self.log_container.log_entries
            ]

            self.log_container._update_pagination()
            self.log_container._update_display()
            self._update_statistics()

    def _update_statistics(self):
        """Update log statistics display"""
        stat_widgets = [
            (self.debug_stat, 'DEBUG'),
            (self.info_stat, 'INFO'),
            (self.warning_stat, 'WARNING'),
            (self.error_stat, 'ERROR')
        ]

        for widget, level in stat_widgets:
            if widget:
                count_label = getattr(widget, 'count_label', None)
                if count_label:
                    count_label.setText(str(self.log_stats.get(level, 0)))
                    count_label.setText(str(self.log_stats[level]))

    def add_log_entry(self, level: str, message: str, source: Optional[str] = None, timestamp: Optional[datetime] = None):
        """Add a new log entry with enhanced features"""
        if timestamp is None:
            timestamp = datetime.now()

        # Create log entry
        entry = LogEntry(level=level, message=message,
                         timestamp=timestamp, source=source)

        # Update statistics
        self.log_stats[level] = self.log_stats.get(level, 0) + 1
        self._update_statistics()

        # Add to container
        if self.log_container:
            self.log_container.add_log_entry(entry)

        # Auto-apply current filter
        if self.advanced_filter:
            self._apply_advanced_filter()

        # Show notification for error/critical levels
        if level in ['ERROR', 'CRITICAL']:
            InfoBar.error(
                title=f"{level} 日志",
                content=message[:50] + "..." if len(message) > 50 else message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )

    def get_log_count(self) -> Dict[str, int]:
        """Get current log statistics"""
        return self.log_stats.copy()

    def get_selected_entry(self) -> Optional[LogEntry]:
        """Get currently selected log entry"""
        if self.log_container:
            return self.log_container.get_selected_entry()
        return None

    def set_max_entries(self, max_entries: int):
        """Set maximum number of log entries"""
        self.max_log_entries = max_entries

    def set_refresh_interval(self, interval: int):
        """Set auto-refresh interval in milliseconds"""
        self.refresh_interval = interval
        if self.auto_refresh_enabled:
            if not hasattr(self, 'refresh_timer') or self.refresh_timer is None:
                self.refresh_timer = QTimer(self)
                self.refresh_timer.timeout.connect(self._auto_refresh)
            self.refresh_timer.start(interval)

    def _apply_filter(self):
        """Apply the new simplified filter"""
        if not self.log_container:
            return

        def should_include_entry(entry: LogEntry) -> bool:
            # Check level filter
            if hasattr(self, 'level_checkboxes'):
                level_enabled = self.level_checkboxes.get(
                    entry.level.upper(), None)
                if level_enabled and not level_enabled.isChecked():
                    return False

            # Check search filter
            if hasattr(self, 'search_box'):
                search_text = self.search_box.text().strip()
                if search_text:
                    if hasattr(self, 'regex_enabled') and self.regex_enabled.isChecked():
                        try:
                            if not re.search(search_text, entry.message, re.IGNORECASE):
                                return False
                        except:
                            # Invalid regex, fall back to normal search
                            if search_text.lower() not in entry.message.lower():
                                return False
                    else:
                        if search_text.lower() not in entry.message.lower():
                            return False

            # Check time filter
            if hasattr(self, 'time_filter_combo'):
                time_filter = self.time_filter_combo.currentText()
                if time_filter != "全部":
                    from datetime import datetime, timedelta
                    now = datetime.now()
                    if time_filter == "最近1小时":
                        cutoff = now - timedelta(hours=1)
                    elif time_filter == "最近6小时":
                        cutoff = now - timedelta(hours=6)
                    elif time_filter == "最近1天":
                        cutoff = now - timedelta(days=1)
                    else:
                        cutoff = None

                    if cutoff and entry.timestamp < cutoff:
                        return False

            return True

        self.log_container.apply_filter(should_include_entry)

    def cleanup(self):
        """Clean up resources when the widget is being destroyed"""
        # Cancel any ongoing export operation
        if self.current_export_worker is not None:
            self.current_export_worker = None

        # Stop any timers if they exist
        if hasattr(self, 'refresh_timer') and self.refresh_timer is not None:
            self.refresh_timer.stop()
            self.refresh_timer.deleteLater()
            self.refresh_timer = None
        if hasattr(self, 'cleanup_timer') and self.cleanup_timer is not None:
            self.cleanup_timer.stop()
            self.cleanup_timer.deleteLater()
            self.cleanup_timer = None

    def closeEvent(self, event):
        """Handle close event"""
        self.cleanup()
        super().closeEvent(event)

    def showEvent(self, event):
        """Handle show event - ensure proper initialization"""
        super().showEvent(event)
        # Ensure components are properly initialized when shown
        if not hasattr(self, 'export_thread'):
            self.export_thread = None

    def __del__(self):
        """Destructor - ensure cleanup is called"""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during destruction

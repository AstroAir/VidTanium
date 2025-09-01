"""
Error Dialog with User-Friendly Reporting and Actionable Suggestions
Provides comprehensive error information with suggested actions for users
"""

from typing import List, Optional, Callable, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QScrollArea, QWidget, QFrame, QSplitter,
    QGroupBox, QListWidget, QListWidgetItem, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon

from qfluentwidgets import (
    FluentIcon as FIF, InfoBar, InfoBarPosition,
    PrimaryPushButton, PushButton, TransparentToolButton,
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    ElevatedCardWidget, ScrollArea, VBoxLayout
)

from ..utils.i18n import tr
from ..utils.theme import VidTaniumTheme
from ...core.exceptions import VidTaniumException, ErrorSeverity, ErrorCategory, UserAction
from ...core.error_handler import ErrorReport


class ActionButton(PrimaryPushButton):
    """Enhanced action button with priority styling"""
    
    action_triggered = Signal(str, dict)  # action_type, action_data
    
    def __init__(self, action: UserAction, parent=None):
        super().__init__(parent)
        self.action = action
        self.setText(action.description)
        self.setToolTip(f"Priority: {action.priority}")
        
        # Style based on priority and type
        if action.is_automatic:
            self.setIcon(FIF.SYNC)
        elif action.action_type == "retry":
            self.setIcon(FIF.REFRESH)
        elif action.action_type == "check_connection":
            self.setIcon(FIF.WIFI)
        elif action.action_type == "check_permissions":
            self.setIcon(FIF.SHIELD)
        elif action.action_type == "free_space":
            self.setIcon(FIF.FOLDER)
        else:
            self.setIcon(FIF.HELP)
        
        # Priority-based styling
        if action.priority == 1:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {VidTaniumTheme.SUCCESS_GREEN};
                    border: 2px solid {VidTaniumTheme.SUCCESS_GREEN};
                    color: white;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {VidTaniumTheme.ACCENT_CYAN};
                    border-color: {VidTaniumTheme.ACCENT_CYAN};
                }}
            """)
        elif action.priority == 2:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {VidTaniumTheme.WARNING_ORANGE};
                    border: 2px solid {VidTaniumTheme.WARNING_ORANGE};
                    color: white;
                }}
            """)
        
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """Handle button click"""
        action_data = {
            "action_type": self.action.action_type,
            "description": self.action.description,
            "is_automatic": self.action.is_automatic,
            "priority": self.action.priority
        }
        self.action_triggered.emit(self.action.action_type, action_data)


class ErrorSummaryCard(ElevatedCardWidget):
    """Card displaying error summary information"""
    
    def __init__(self, error_report: ErrorReport, parent=None):
        super().__init__(parent)
        self.error_report = error_report
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = VBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Error icon based on severity
        icon_label = QLabel()
        icon_size = 32
        if self.error_report.severity == ErrorSeverity.CRITICAL:
            icon_label.setPixmap(FIF.CANCEL.icon().pixmap(icon_size, icon_size))
            icon_color = VidTaniumTheme.ERROR_RED
        elif self.error_report.severity == ErrorSeverity.HIGH:
            icon_label.setPixmap(FIF.WARNING.icon().pixmap(icon_size, icon_size))
            icon_color = VidTaniumTheme.WARNING_ORANGE
        else:
            icon_label.setPixmap(FIF.INFO.icon().pixmap(icon_size, icon_size))
            icon_color = VidTaniumTheme.ACCENT_CYAN
        
        icon_label.setFixedSize(icon_size, icon_size)
        header_layout.addWidget(icon_label)
        
        # Title and category
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title_label = SubtitleLabel(self.error_report.title)
        title_label.setStyleSheet(f"color: {icon_color}; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        category_label = CaptionLabel(f"Category: {self.error_report.category.value.title()}")
        category_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        title_layout.addWidget(category_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Retry indicator
        if self.error_report.is_retryable:
            retry_label = CaptionLabel(f"Retry {self.error_report.retry_count + 1}")
            retry_label.setStyleSheet(f"""
                background: {VidTaniumTheme.BG_SURFACE};
                border: 1px solid {VidTaniumTheme.BORDER_COLOR};
                border-radius: 12px;
                padding: 4px 8px;
                color: {VidTaniumTheme.TEXT_SECONDARY};
            """)
            header_layout.addWidget(retry_label)
        
        layout.addLayout(header_layout)
        
        # Error message
        message_label = BodyLabel(self.error_report.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; line-height: 1.4;")
        layout.addWidget(message_label)
        
        # Context information if available
        if self.error_report.context:
            context_layout = QHBoxLayout()
            context_layout.setSpacing(16)
            
            if self.error_report.context.task_name:
                task_label = CaptionLabel(f"Task: {self.error_report.context.task_name}")
                task_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
                context_layout.addWidget(task_label)
            
            if self.error_report.context.url:
                url_label = CaptionLabel(f"URL: {self.error_report.context.url[:50]}...")
                url_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
                context_layout.addWidget(url_label)
            
            context_layout.addStretch()
            layout.addLayout(context_layout)


class SuggestedActionsWidget(QWidget):
    """Widget displaying suggested actions with priority ordering"""
    
    action_requested = Signal(str, dict)  # action_type, action_data
    
    def __init__(self, actions: List[UserAction], parent=None):
        super().__init__(parent)
        self.actions = sorted(actions, key=lambda x: x.priority)  # Sort by priority
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = SubtitleLabel(tr("error_dialog.suggested_actions"))
        title_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Actions
        for action in self.actions:
            action_button = ActionButton(action)
            action_button.action_triggered.connect(self.action_requested.emit)
            layout.addWidget(action_button)
        
        layout.addStretch()


class TechnicalDetailsWidget(QWidget):
    """Widget displaying technical error details"""
    
    def __init__(self, technical_details: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.technical_details = technical_details
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = SubtitleLabel(tr("error_dialog.technical_details"))
        title_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Details text area
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setMaximumHeight(200)
        
        # Format technical details
        formatted_details = self._format_technical_details()
        details_text.setPlainText(formatted_details)
        
        details_text.setStyleSheet(f"""
            QTextEdit {{
                background: {VidTaniumTheme.BG_SURFACE};
                border: 1px solid {VidTaniumTheme.BORDER_COLOR};
                border-radius: 8px;
                padding: 8px;
                color: {VidTaniumTheme.TEXT_SECONDARY};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
        """)
        
        layout.addWidget(details_text)
    
    def _format_technical_details(self) -> str:
        """Format technical details for display"""
        lines = []
        
        for key, value in self.technical_details.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    if sub_value is not None:
                        lines.append(f"  {sub_key}: {sub_value}")
            elif value is not None:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)


class ErrorDialog(QDialog):
    """Error dialog with comprehensive error reporting"""
    
    action_requested = Signal(str, dict)  # action_type, action_data
    retry_requested = Signal()
    dismiss_requested = Signal()
    
    def __init__(self, error_report: ErrorReport, parent=None):
        super().__init__(parent)
        self.error_report = error_report
        self.setWindowTitle(tr("error_dialog.title"))
        self.setMinimumSize(600, 400)
        self.setModal(True)
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Error summary card
        summary_card = ErrorSummaryCard(self.error_report)
        layout.addWidget(summary_card)
        
        # Main content area with tabs
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {VidTaniumTheme.BORDER_COLOR};
                border-radius: 8px;
                background: {VidTaniumTheme.BG_SURFACE};
            }}
            QTabBar::tab {{
                background: {VidTaniumTheme.BG_SECONDARY};
                color: {VidTaniumTheme.TEXT_SECONDARY};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:selected {{
                background: {VidTaniumTheme.BG_SURFACE};
                color: {VidTaniumTheme.TEXT_PRIMARY};
            }}
        """)
        
        # Suggested actions tab
        if self.error_report.suggested_actions:
            actions_widget = SuggestedActionsWidget(self.error_report.suggested_actions)
            actions_widget.action_requested.connect(self.action_requested.emit)
            tab_widget.addTab(actions_widget, tr("error_dialog.actions_tab"))
        
        # Technical details tab
        if self.error_report.technical_details:
            details_widget = TechnicalDetailsWidget(self.error_report.technical_details)
            tab_widget.addTab(details_widget, tr("error_dialog.details_tab"))
        
        layout.addWidget(tab_widget)
        
        # Button area
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Copy details button
        copy_button = PushButton(tr("error_dialog.copy_details"))
        copy_button.setIcon(FIF.COPY)
        copy_button.clicked.connect(self._copy_details)
        button_layout.addWidget(copy_button)
        
        button_layout.addStretch()
        
        # Retry button (if retryable)
        if self.error_report.is_retryable:
            retry_button = PrimaryPushButton(tr("error_dialog.retry"))
            retry_button.setIcon(FIF.REFRESH)
            retry_button.clicked.connect(self.retry_requested.emit)
            retry_button.clicked.connect(self.accept)
            button_layout.addWidget(retry_button)
        
        # Dismiss button
        dismiss_button = PushButton(tr("error_dialog.dismiss"))
        dismiss_button.clicked.connect(self.dismiss_requested.emit)
        dismiss_button.clicked.connect(self.reject)
        button_layout.addWidget(dismiss_button)
        
        layout.addLayout(button_layout)
    
    def _apply_theme(self):
        """Apply theme styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {VidTaniumTheme.BG_PRIMARY};
                color: {VidTaniumTheme.TEXT_PRIMARY};
            }}
        """)
    
    def _copy_details(self):
        """Copy error details to clipboard"""
        from PySide6.QtGui import QGuiApplication
        
        details = []
        details.append(f"Error: {self.error_report.title}")
        details.append(f"Message: {self.error_report.message}")
        details.append(f"Category: {self.error_report.category.value}")
        details.append(f"Severity: {self.error_report.severity.value}")
        
        if self.error_report.context:
            details.append("\nContext:")
            if self.error_report.context.task_name:
                details.append(f"  Task: {self.error_report.context.task_name}")
            if self.error_report.context.url:
                details.append(f"  URL: {self.error_report.context.url}")
        
        if self.error_report.technical_details:
            details.append("\nTechnical Details:")
            for key, value in self.error_report.technical_details.items():
                details.append(f"  {key}: {value}")
        
        clipboard_text = "\n".join(details)
        QGuiApplication.clipboard().setText(clipboard_text)
        
        # Show confirmation
        InfoBar.success(
            title=tr("error_dialog.copied"),
            content=tr("error_dialog.copied_message"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

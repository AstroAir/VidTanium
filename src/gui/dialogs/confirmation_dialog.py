"""
Confirmation Dialog for VidTanium
Provides detailed confirmation dialogs for critical operations with comprehensive information
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QTextEdit, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from qfluentwidgets import (
    FluentIcon as FIF, PrimaryPushButton, PushButton, TransparentToolButton,
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    ElevatedCardWidget, ScrollArea, VBoxLayout, CheckBox
)

from ..utils.i18n import tr
from ..utils.theme import VidTaniumTheme
from ..utils.formatters import format_size, format_duration


class OperationInfo:
    """Information about the operation being confirmed"""
    
    def __init__(
        self,
        operation_type: str,
        title: str,
        description: str,
        warning_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        consequences: Optional[List[str]] = None,
        is_destructive: bool = False,
        requires_confirmation: bool = True
    ):
        self.operation_type = operation_type
        self.title = title
        self.description = description
        self.warning_message = warning_message
        self.details = details or {}
        self.consequences = consequences or []
        self.is_destructive = is_destructive
        self.requires_confirmation = requires_confirmation


class OperationDetailsCard(ElevatedCardWidget):
    """Card displaying operation details"""
    
    def __init__(self, operation_info: OperationInfo, parent=None):
        super().__init__(parent)
        self.operation_info = operation_info
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = VBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Operation icon and title
        header_layout = QHBoxLayout()
        
        # Icon based on operation type
        icon_label = QLabel()
        icon_size = 32
        
        if self.operation_info.is_destructive:
            icon_label.setPixmap(FIF.DELETE.icon().pixmap(icon_size, icon_size))
            icon_color = VidTaniumTheme.ERROR_RED
        elif self.operation_info.operation_type == "cancel":
            icon_label.setPixmap(FIF.CANCEL.icon().pixmap(icon_size, icon_size))
            icon_color = VidTaniumTheme.WARNING_ORANGE
        elif self.operation_info.operation_type == "pause":
            icon_label.setPixmap(FIF.PAUSE.icon().pixmap(icon_size, icon_size))
            icon_color = VidTaniumTheme.ACCENT_CYAN
        else:
            icon_label.setPixmap(FIF.INFO.icon().pixmap(icon_size, icon_size))
            icon_color = VidTaniumTheme.TEXT_PRIMARY
        
        icon_label.setFixedSize(icon_size, icon_size)
        header_layout.addWidget(icon_label)
        
        # Title and description
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title_label = SubtitleLabel(self.operation_info.title)
        title_label.setStyleSheet(f"color: {icon_color}; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        desc_label = BodyLabel(self.operation_info.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        title_layout.addWidget(desc_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Warning message if present
        if self.operation_info.warning_message:
            warning_frame = QFrame()
            warning_frame.setStyleSheet(f"""
                QFrame {{
                    background: {VidTaniumTheme.WARNING_ORANGE}20;
                    border: 1px solid {VidTaniumTheme.WARNING_ORANGE};
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            
            warning_layout = QHBoxLayout(warning_frame)
            warning_layout.setSpacing(8)
            
            warning_icon = QLabel()
            warning_icon.setPixmap(FIF.WARNING.icon().pixmap(16, 16))
            warning_layout.addWidget(warning_icon)
            
            warning_text = BodyLabel(self.operation_info.warning_message)
            warning_text.setWordWrap(True)
            warning_text.setStyleSheet(f"color: {VidTaniumTheme.WARNING_ORANGE}; font-weight: 500;")
            warning_layout.addWidget(warning_text)
            
            layout.addWidget(warning_frame)
        
        # Details section
        if self.operation_info.details:
            details_layout = QVBoxLayout()
            details_layout.setSpacing(8)
            
            details_title = CaptionLabel(tr("confirmation_dialog.details"))
            details_title.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: bold;")
            details_layout.addWidget(details_title)
            
            for key, value in self.operation_info.details.items():
                detail_layout = QHBoxLayout()
                detail_layout.setSpacing(8)
                
                key_label = CaptionLabel(f"{key}:")
                key_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
                key_label.setMinimumWidth(100)
                detail_layout.addWidget(key_label)
                
                value_label = CaptionLabel(str(value))
                value_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY};")
                detail_layout.addWidget(value_label)
                
                detail_layout.addStretch()
                details_layout.addLayout(detail_layout)
            
            layout.addLayout(details_layout)
        
        # Consequences section
        if self.operation_info.consequences:
            consequences_layout = QVBoxLayout()
            consequences_layout.setSpacing(8)
            
            consequences_title = CaptionLabel(tr("confirmation_dialog.consequences"))
            consequences_title.setStyleSheet(f"color: {VidTaniumTheme.ERROR_RED}; font-weight: bold;")
            consequences_layout.addWidget(consequences_title)
            
            for consequence in self.operation_info.consequences:
                consequence_layout = QHBoxLayout()
                consequence_layout.setSpacing(8)
                
                bullet_label = CaptionLabel("•")
                bullet_label.setStyleSheet(f"color: {VidTaniumTheme.ERROR_RED};")
                consequence_layout.addWidget(bullet_label)
                
                consequence_text = CaptionLabel(consequence)
                consequence_text.setWordWrap(True)
                consequence_text.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
                consequence_layout.addWidget(consequence_text)
                
                consequences_layout.addLayout(consequence_layout)
            
            layout.addLayout(consequences_layout)


class ConfirmationDialog(QDialog):
    """Confirmation dialog with detailed operation information"""
    
    confirmed = Signal(dict)  # operation_data
    cancelled = Signal()
    
    def __init__(self, operation_info: OperationInfo, parent=None):
        super().__init__(parent)
        self.operation_info = operation_info
        self.confirmation_data: Dict[str, Any] = {}
        
        self.setWindowTitle(tr("confirmation_dialog.title"))
        self.setMinimumSize(500, 300)
        self.setModal(True)
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Operation details card
        details_card = OperationDetailsCard(self.operation_info)
        layout.addWidget(details_card)
        
        # Additional options section
        if self.operation_info.operation_type == "delete":
            self._add_delete_options(layout)
        elif self.operation_info.operation_type == "cancel":
            self._add_cancel_options(layout)
        
        # Confirmation checkbox for destructive operations
        if self.operation_info.is_destructive and self.operation_info.requires_confirmation:
            self.confirmation_checkbox = CheckBox(
                tr("confirmation_dialog.understand_consequences")
            )
            self.confirmation_checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {VidTaniumTheme.TEXT_PRIMARY};
                    font-weight: 500;
                }}
            """)
            self.confirmation_checkbox.stateChanged.connect(self._on_confirmation_changed)
            layout.addWidget(self.confirmation_checkbox)
        
        # Button area
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Cancel button
        cancel_button = PushButton(tr("confirmation_dialog.cancel"))
        cancel_button.setIcon(FIF.CANCEL)
        cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_button)
        
        button_layout.addStretch()
        
        # Confirm button
        confirm_text = tr("confirmation_dialog.confirm")
        if self.operation_info.operation_type == "delete":
            confirm_text = tr("confirmation_dialog.delete")
        elif self.operation_info.operation_type == "cancel":
            confirm_text = tr("confirmation_dialog.cancel_task")
        
        self.confirm_button = PrimaryPushButton(confirm_text)
        
        if self.operation_info.is_destructive:
            self.confirm_button.setIcon(FIF.DELETE)
            self.confirm_button.setStyleSheet(f"""
                QPushButton {{
                    background: {VidTaniumTheme.ERROR_RED};
                    border: 2px solid {VidTaniumTheme.ERROR_RED};
                    color: white;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {VidTaniumTheme.ERROR_RED}CC;
                }}
                QPushButton:disabled {{
                    background: {VidTaniumTheme.BG_SURFACE};
                    border-color: {VidTaniumTheme.BORDER_COLOR};
                    color: {VidTaniumTheme.TEXT_DISABLED};
                }}
            """)
        else:
            self.confirm_button.setIcon(FIF.ACCEPT)
        
        self.confirm_button.clicked.connect(self._on_confirm)
        
        # Disable confirm button initially for destructive operations
        if self.operation_info.is_destructive and self.operation_info.requires_confirmation:
            self.confirm_button.setEnabled(False)
        
        button_layout.addWidget(self.confirm_button)
        
        layout.addLayout(button_layout)
    
    def _add_delete_options(self, layout: QVBoxLayout):
        """Add delete-specific options"""
        options_layout = QVBoxLayout()
        options_layout.setSpacing(8)
        
        options_title = CaptionLabel(tr("confirmation_dialog.delete_options"))
        options_title.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: bold;")
        options_layout.addWidget(options_title)
        
        self.delete_files_checkbox = CheckBox(tr("confirmation_dialog.delete_downloaded_files"))
        self.delete_files_checkbox.setToolTip(tr("confirmation_dialog.delete_files_tooltip"))
        options_layout.addWidget(self.delete_files_checkbox)
        
        self.delete_progress_checkbox = CheckBox(tr("confirmation_dialog.delete_progress_data"))
        self.delete_progress_checkbox.setChecked(True)
        self.delete_progress_checkbox.setToolTip(tr("confirmation_dialog.delete_progress_tooltip"))
        options_layout.addWidget(self.delete_progress_checkbox)
        
        layout.addLayout(options_layout)
    
    def _add_cancel_options(self, layout: QVBoxLayout):
        """Add cancel-specific options"""
        options_layout = QVBoxLayout()
        options_layout.setSpacing(8)
        
        options_title = CaptionLabel(tr("confirmation_dialog.cancel_options"))
        options_title.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: bold;")
        options_layout.addWidget(options_title)
        
        self.keep_partial_checkbox = CheckBox(tr("confirmation_dialog.keep_partial_files"))
        self.keep_partial_checkbox.setChecked(True)
        self.keep_partial_checkbox.setToolTip(tr("confirmation_dialog.keep_partial_tooltip"))
        options_layout.addWidget(self.keep_partial_checkbox)
        
        layout.addLayout(options_layout)
    
    def _apply_theme(self):
        """Apply theme styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {VidTaniumTheme.BG_PRIMARY};
                color: {VidTaniumTheme.TEXT_PRIMARY};
            }}
        """)
    
    def _on_confirmation_changed(self, state):
        """Handle confirmation checkbox state change"""
        self.confirm_button.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _on_confirm(self):
        """Handle confirm button click"""
        # Collect confirmation data
        self.confirmation_data = {
            "operation_type": self.operation_info.operation_type,
            "confirmed": True
        }
        
        # Add operation-specific data
        if self.operation_info.operation_type == "delete":
            self.confirmation_data.update({
                "delete_files": getattr(self, 'delete_files_checkbox', None) and self.delete_files_checkbox.isChecked(),
                "delete_progress": getattr(self, 'delete_progress_checkbox', None) and self.delete_progress_checkbox.isChecked()
            })
        elif self.operation_info.operation_type == "cancel":
            self.confirmation_data.update({
                "keep_partial": getattr(self, 'keep_partial_checkbox', None) and self.keep_partial_checkbox.isChecked()
            })
        
        self.confirmed.emit(self.confirmation_data)
        self.accept()
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.cancelled.emit()
        self.reject()


# Factory functions for common confirmation dialogs
def create_delete_confirmation(task_name: str, file_size: Optional[int] = None) -> ConfirmationDialog:
    """Create delete confirmation dialog"""
    details = {"Task": task_name}
    if file_size:
        details["File Size"] = format_size(file_size)
    
    operation_info = OperationInfo(
        operation_type="delete",
        title=tr("confirmation_dialog.delete_task_title"),
        description=tr("confirmation_dialog.delete_task_description", task=task_name),
        warning_message=tr("confirmation_dialog.delete_warning"),
        details=details,
        consequences=[
            tr("confirmation_dialog.delete_consequence_1"),
            tr("confirmation_dialog.delete_consequence_2"),
            tr("confirmation_dialog.delete_consequence_3")
        ],
        is_destructive=True,
        requires_confirmation=True
    )
    
    return ConfirmationDialog(operation_info)


def create_cancel_confirmation(task_name: str, progress: float) -> ConfirmationDialog:
    """Create cancel confirmation dialog"""
    operation_info = OperationInfo(
        operation_type="cancel",
        title=tr("confirmation_dialog.cancel_task_title"),
        description=tr("confirmation_dialog.cancel_task_description", task=task_name),
        details={
            "Task": task_name,
            "Progress": f"{progress:.1f}%"
        },
        consequences=[
            tr("confirmation_dialog.cancel_consequence_1"),
            tr("confirmation_dialog.cancel_consequence_2")
        ],
        is_destructive=False,
        requires_confirmation=False
    )
    
    return ConfirmationDialog(operation_info)

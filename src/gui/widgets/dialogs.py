"""
Dialog Components for VidTanium
Modern dialogs with improved UX and visual design
"""

from typing import Optional, List, Dict, Any, Callable
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QWidget, QGraphicsOpacityEffect
)
from PySide6.QtGui import QFont, QPainter, QPainterPath, QColor

from qfluentwidgets import (
    MessageBox, Dialog, FluentIcon as FIF,
    PrimaryPushButton, PushButton, TransparentToolButton,
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    LineEdit, TextEdit, ComboBox, CheckBox,
    ElevatedCardWidget, HeaderCardWidget
)

from ..utils.design_system import DesignSystem, AnimatedCard


class ModernMessageBox(Dialog):
    """Message box with modern styling"""
    
    def __init__(self, title: str, content: str, icon: FIF = FIF.INFO, parent=None) -> None:
        super().__init__(title, content, parent)
        self.icon = icon
        self._enhance_styling()
    
    def _enhance_styling(self) -> None:
        """Apply enhanced styling to message box"""
        self.setStyleSheet(f"""
            Dialog {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['xl']}px;
            }}
        """)

        # Add shadow effect
        shadow = DesignSystem.create_shadow_effect('xl')
        self.setGraphicsEffect(shadow)


class EnhancedInputDialog(Dialog):
    """Enhanced input dialog with validation and modern styling"""
    
    def __init__(self, title: str, content: str, placeholder: str = "", 
                 validator: Optional[Callable[[str], bool]] = None, parent=None) -> None:
        super().__init__(title, content, parent)
        self.placeholder = placeholder
        self.validator = validator
        self.input_value = ""
        
        self._setup_input_ui()
        self._enhance_styling()
    
    def _setup_input_ui(self) -> None:
        """Setup input dialog UI"""
        # Add input field to the dialog
        self.input_field = LineEdit()
        self.input_field.setPlaceholderText(self.placeholder)
        self.input_field.textChanged.connect(self._validate_input)
        
        # Insert input field into dialog layout
        layout = self.layout()
        layout.insertWidget(2, self.input_field)
        
        # Error label for validation
        self.error_label = CaptionLabel("")
        self.error_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('error')};
            margin-top: 4px;
        """)
        self.error_label.hide()
        layout.insertWidget(3, self.error_label)

    def _enhance_styling(self) -> None:
        """Apply enhanced styling"""
        self.setStyleSheet(f"""
            Dialog {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['xl']}px;
            }}
            LineEdit {{
                padding: 8px 12px;
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['md']}px;
                background: {DesignSystem.get_color('surface_secondary_adaptive')};
            }}
            LineEdit:focus {{
                border-color: {DesignSystem.get_color('primary')};
            }}
        """)
    
    def _validate_input(self, text: str) -> None:
        """Validate input text"""
        self.input_value = text
        
        if self.validator:
            is_valid = self.validator(text)
            if not is_valid:
                self.error_label.setText("Invalid input")
                self.error_label.show()
                self.yesButton.setEnabled(False)
            else:
                self.error_label.hide()
                self.yesButton.setEnabled(True)
        else:
            self.yesButton.setEnabled(bool(text.strip()))
    
    def get_input(self) -> str:
        """Get the input value"""
        return self.input_value


class ProgressDialog(Dialog):
    """Enhanced progress dialog with detailed progress information"""
    
    cancelled = Signal()
    
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(title, "", parent)
        self.is_cancellable = True
        self.progress_value = 0
        
        self._setup_progress_ui()
        self._enhance_styling()
    
    def _setup_progress_ui(self) -> None:
        """Setup progress dialog UI"""
        # Remove default content
        self.contentLabel.hide()
        
        # Progress container
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setSpacing(12)
        
        # Status label
        self.status_label = BodyLabel("Initializing...")
        self.status_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_primary_adaptive')};
            font-weight: 500;
        """)
        progress_layout.addWidget(self.status_label)

        # Progress bar (using progress card)
        from .progress import ProgressCard
        self.progress_card = ProgressCard("Progress")
        self.progress_card.cancel_clicked.connect(self._handle_cancel)
        progress_layout.addWidget(self.progress_card)
        
        # Details area
        self.details_area = TextEdit()
        self.details_area.setFixedHeight(100)
        self.details_area.setReadOnly(True)
        self.details_area.setStyleSheet(f"""
            TextEdit {{
                background: {DesignSystem.get_color('surface_tertiary_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['md']}px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }}
        """)
        progress_layout.addWidget(self.details_area)
        
        # Add to dialog layout
        layout = self.layout()
        layout.insertWidget(1, progress_container)
        
        # Hide default buttons, add custom cancel button
        self.yesButton.hide()
        self.cancelButton.setText("Cancel")
        self.cancelButton.clicked.connect(self._handle_cancel)
    
    def _enhance_styling(self) -> None:
        """Apply enhanced styling"""
        self.setMinimumWidth(500)
        self.setStyleSheet(f"""
            Dialog {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['xl']}px;
            }}
        """)
    
    def update_progress(self, value: int, status: str = "", details: str = "") -> None:
        """Update progress information"""
        self.progress_value = value
        self.progress_card.update_progress(value)
        
        if status:
            self.status_label.setText(status)
        
        if details:
            self.details_area.append(details)
            # Auto-scroll to bottom
            cursor = self.details_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.details_area.setTextCursor(cursor)
    
    def set_cancellable(self, cancellable: bool) -> None:
        """Set whether the dialog can be cancelled"""
        self.is_cancellable = cancellable
        self.cancelButton.setVisible(cancellable)
        self.progress_card.cancel_btn.setVisible(cancellable)
    
    def _handle_cancel(self) -> None:
        """Handle cancel button click"""
        if self.is_cancellable:
            self.cancelled.emit()
            self.reject()


class MultiStepDialog(Dialog):
    """Enhanced multi-step dialog with navigation"""
    
    step_changed = Signal(int)
    
    def __init__(self, title: str, steps: List[str], parent=None) -> None:
        super().__init__(title, "", parent)
        self.steps = steps
        self.current_step = 0
        self.step_widgets: List[QWidget] = []
        
        self._setup_multistep_ui()
        self._enhance_styling()
    
    def _setup_multistep_ui(self) -> None:
        """Setup multi-step dialog UI"""
        # Remove default content
        self.contentLabel.hide()
        
        # Step indicator
        self.step_indicator = self._create_step_indicator()
        
        # Content area
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add to dialog layout
        layout = self.layout()
        layout.insertWidget(1, self.step_indicator)
        layout.insertWidget(2, self.content_area)
        
        # Update button labels
        self.yesButton.setText("Next")
        self.cancelButton.setText("Back")
        
        # Connect navigation
        self.yesButton.clicked.connect(self._next_step)
        self.cancelButton.clicked.connect(self._previous_step)
        
        self._update_navigation()
    
    def _create_step_indicator(self) -> QWidget:
        """Create step indicator"""
        indicator = QWidget()
        indicator.setFixedHeight(60)
        layout = QHBoxLayout(indicator)
        layout.setContentsMargins(20, 16, 20, 16)
        
        self.step_labels = []
        
        for i, step in enumerate(self.steps):
            # Step circle
            step_circle = QLabel(str(i + 1))
            step_circle.setFixedSize(32, 32)
            step_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_circle.setStyleSheet(f"""
                QLabel {{
                    background: {DesignSystem.get_color('surface_tertiary_adaptive')};
                    color: {DesignSystem.get_color('text_secondary_adaptive')};
                    border-radius: 16px;
                    font-weight: 600;
                }}
            """)
            layout.addWidget(step_circle)
            
            # Step label
            step_label = CaptionLabel(step)
            step_label.setStyleSheet(f"""
                color: {DesignSystem.get_color('text_secondary_adaptive')};
                margin-left: 8px;
            """)
            layout.addWidget(step_label)
            
            self.step_labels.append((step_circle, step_label))
            
            # Connector (except for last step)
            if i < len(self.steps) - 1:
                connector = QFrame()
                connector.setFrameShape(QFrame.Shape.HLine)
                connector.setFixedHeight(2)
                connector.setStyleSheet(f"""
                    QFrame {{
                        background: {DesignSystem.get_color('border_adaptive')};
                        margin: 0px 16px;
                    }}
                """)
                layout.addWidget(connector)
        
        return indicator
    
    def _enhance_styling(self) -> None:
        """Apply enhanced styling"""
        self.setMinimumWidth(600)
        self.setStyleSheet(f"""
            Dialog {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['xl']}px;
            }}
        """)
    
    def add_step_widget(self, widget: QWidget) -> None:
        """Add widget for a step"""
        widget.hide()
        self.content_layout.addWidget(widget)
        self.step_widgets.append(widget)
        
        if len(self.step_widgets) == 1:
            widget.show()
    
    def _next_step(self) -> None:
        """Go to next step"""
        if self.current_step < len(self.steps) - 1:
            self.step_widgets[self.current_step].hide()
            self.current_step += 1
            self.step_widgets[self.current_step].show()
            self._update_step_indicator()
            self._update_navigation()
            self.step_changed.emit(self.current_step)
        else:
            self.accept()
    
    def _previous_step(self) -> None:
        """Go to previous step"""
        if self.current_step > 0:
            self.step_widgets[self.current_step].hide()
            self.current_step -= 1
            self.step_widgets[self.current_step].show()
            self._update_step_indicator()
            self._update_navigation()
            self.step_changed.emit(self.current_step)
        else:
            self.reject()
    
    def _update_step_indicator(self) -> None:
        """Update step indicator styling"""
        for i, (circle, label) in enumerate(self.step_labels):
            if i <= self.current_step:
                # Active/completed step
                circle.setStyleSheet(f"""
                    QLabel {{
                        background: {DesignSystem.get_color('primary')};
                        color: white;
                        border-radius: 16px;
                        font-weight: 600;
                    }}
                """)
                label.setStyleSheet(f"""
                    color: {DesignSystem.get_color('text_primary_adaptive')};
                    font-weight: 500;
                    margin-left: 8px;
                """)
            else:
                # Inactive step
                circle.setStyleSheet(f"""
                    QLabel {{
                        background: {DesignSystem.get_color('surface_tertiary_adaptive')};
                        color: {DesignSystem.get_color('text_secondary_adaptive')};
                        border-radius: 16px;
                        font-weight: 600;
                    }}
                """)
                label.setStyleSheet(f"""
                    color: {DesignSystem.get_color('text_secondary_adaptive')};
                    margin-left: 8px;
                """)
    
    def _update_navigation(self) -> None:
        """Update navigation button states"""
        self.cancelButton.setText("Back" if self.current_step > 0 else "Cancel")
        self.yesButton.setText("Finish" if self.current_step == len(self.steps) - 1 else "Next")

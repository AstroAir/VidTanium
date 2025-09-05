"""
Error Recovery Dialog for VidTanium
Provides user-friendly error recovery interface with guided solutions
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QGroupBox, QListWidget, QListWidgetItem,
    QSplitter, QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QPixmap, QIcon, QFont
from qfluentwidgets import (
    FluentIcon as FIF, InfoBar, InfoBarPosition, PrimaryPushButton,
    PushButton, TitleLabel, BodyLabel, CaptionLabel, CardWidget,
    IconWidget, ProgressBar, IndeterminateProgressBar
)

from src.gui.utils.i18n import tr
from src.core.intelligent_recovery import RecoveryPlan, RecoveryAction, RecoveryStrategy
from src.core.exceptions import VidTaniumException, ErrorSeverity
from loguru import logger


class RecoveryActionWidget(CardWidget):
    """Widget for displaying a single recovery action"""
    
    action_triggered = Signal(RecoveryAction)
    
    def __init__(self, action: RecoveryAction, parent=None):
        super().__init__(parent)
        self.action = action
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the action widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Strategy icon
        icon = self._get_strategy_icon(self.action.strategy)
        icon_widget = IconWidget(icon, self)
        icon_widget.setFixedSize(24, 24)
        header_layout.addWidget(icon_widget)
        
        # Action description
        title_label = BodyLabel(self.action.description)
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)
        
        # Priority indicator
        priority_label = CaptionLabel(f"Priority: {self.action.priority.name}")
        priority_label.setStyleSheet(f"color: {self._get_priority_color(self.action.priority)}")
        header_layout.addWidget(priority_label)
        
        layout.addLayout(header_layout)
        
        # Details
        details_layout = QHBoxLayout()
        
        # Success probability
        success_label = CaptionLabel(f"Success Rate: {self.action.success_probability:.0%}")
        details_layout.addWidget(success_label)
        
        # Estimated time
        if self.action.estimated_time > 0:
            time_label = CaptionLabel(f"Est. Time: {self.action.estimated_time:.0f}s")
            details_layout.addWidget(time_label)
        
        # Automated indicator
        auto_label = CaptionLabel("Automated" if self.action.automated else "Manual")
        auto_label.setStyleSheet("color: green" if self.action.automated else "color: orange")
        details_layout.addWidget(auto_label)
        
        details_layout.addStretch()
        layout.addLayout(details_layout)
        
        # Action button (only for manual actions)
        if not self.action.automated:
            button = PrimaryPushButton(tr("recovery.execute_action"))
            button.clicked.connect(lambda: self.action_triggered.emit(self.action))
            layout.addWidget(button)
    
    def _get_strategy_icon(self, strategy: RecoveryStrategy) -> FIF:
        """Get icon for recovery strategy"""
        icon_map = {
            RecoveryStrategy.IMMEDIATE_RETRY: FIF.SYNC,
            RecoveryStrategy.DELAYED_RETRY: FIF.PAUSE,
            RecoveryStrategy.ALTERNATIVE_SOURCE: FIF.GLOBE,
            RecoveryStrategy.QUALITY_DOWNGRADE: FIF.ZOOM_OUT,
            RecoveryStrategy.SEGMENT_SKIP: FIF.SKIP_FORWARD,
            RecoveryStrategy.USER_INTERVENTION: FIF.PEOPLE,
            RecoveryStrategy.ABORT: FIF.CANCEL
        }
        return icon_map.get(strategy, FIF.INFO)
    
    def _get_priority_color(self, priority) -> str:
        """Get color for priority level"""
        color_map = {
            1: "#28a745",  # Low - Green
            2: "#ffc107",  # Medium - Yellow
            3: "#fd7e14",  # High - Orange
            4: "#dc3545"   # Critical - Red
        }
        return color_map.get(priority.value, "#6c757d")


class RecoveryExecutionWorker(QObject):
    """Worker for executing recovery actions in background"""
    
    progress_updated = Signal(str)
    action_completed = Signal(bool, str)
    finished = Signal()
    
    def __init__(self, recovery_plan: RecoveryPlan, context: dict):
        super().__init__()
        self.recovery_plan = recovery_plan
        self.context = context
    
    def execute_recovery(self):
        """Execute recovery plan"""
        from src.core.intelligent_recovery import intelligent_recovery_system
        
        try:
            self.progress_updated.emit("Starting recovery process...")
            
            success, message = intelligent_recovery_system.execute_recovery_plan(
                self.recovery_plan, self.context
            )
            
            self.action_completed.emit(success, message)
            
        except Exception as e:
            logger.error(f"Recovery execution failed: {e}")
            self.action_completed.emit(False, f"Recovery failed: {str(e)}")
        finally:
            self.finished.emit()


class ErrorRecoveryDialog(QDialog):
    """Dialog for displaying error recovery options and guidance"""
    
    recovery_requested = Signal(RecoveryAction)
    recovery_completed = Signal(bool, str)
    
    def __init__(self, exception: VidTaniumException, recovery_plan: RecoveryPlan, parent=None):
        super().__init__(parent)
        self.exception = exception
        self.recovery_plan = recovery_plan
        self.recovery_context = {}
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle(tr("recovery.dialog_title"))
        self.setMinimumSize(600, 500)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Error information section
        error_group = self._create_error_info_section()
        layout.addWidget(error_group)
        
        # Recovery actions section
        recovery_group = self._create_recovery_actions_section()
        layout.addWidget(recovery_group, 1)
        
        # User guidance section
        guidance_group = self._create_user_guidance_section()
        layout.addWidget(guidance_group)
        
        # Progress section (initially hidden)
        self.progress_group = self._create_progress_section()
        self.progress_group.hide()
        layout.addWidget(self.progress_group)
        
        # Button section
        button_layout = self._create_button_section()
        layout.addLayout(button_layout)
    
    def _create_error_info_section(self) -> QGroupBox:
        """Create error information section"""
        group = QGroupBox(tr("recovery.error_information"))
        layout = QVBoxLayout(group)
        
        # Error title with severity icon
        title_layout = QHBoxLayout()
        
        severity_icon = self._get_severity_icon(self.exception.severity)
        icon_widget = IconWidget(severity_icon, self)
        icon_widget.setFixedSize(32, 32)
        title_layout.addWidget(icon_widget)
        
        title_label = TitleLabel(f"{self.exception.category.value.title()} Error")
        title_layout.addWidget(title_label, 1)
        
        layout.addLayout(title_layout)
        
        # Error message
        message_label = BodyLabel(self.exception.message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Error context if available
        if self.exception.context and self.exception.context.url:
            context_label = CaptionLabel(f"URL: {self.exception.context.url}")
            context_label.setWordWrap(True)
            layout.addWidget(context_label)
        
        return group
    
    def _create_recovery_actions_section(self) -> QGroupBox:
        """Create recovery actions section"""
        group = QGroupBox(tr("recovery.available_actions"))
        layout = QVBoxLayout(group)
        
        # Scroll area for actions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setSpacing(8)
        
        # Add recovery actions
        for action in self.recovery_plan.actions:
            action_widget = RecoveryActionWidget(action)
            action_widget.action_triggered.connect(self.recovery_requested.emit)
            actions_layout.addWidget(action_widget)
        
        # Add fallback actions if any
        if self.recovery_plan.fallback_actions:
            fallback_label = BodyLabel(tr("recovery.fallback_actions"))
            fallback_label.setStyleSheet("font-weight: bold; margin-top: 16px;")
            actions_layout.addWidget(fallback_label)
            
            for action in self.recovery_plan.fallback_actions:
                action_widget = RecoveryActionWidget(action)
                action_widget.action_triggered.connect(self.recovery_requested.emit)
                actions_layout.addWidget(action_widget)
        
        actions_layout.addStretch()
        scroll_area.setWidget(actions_widget)
        layout.addWidget(scroll_area)
        
        return group
    
    def _create_user_guidance_section(self) -> QGroupBox:
        """Create user guidance section"""
        group = QGroupBox(tr("recovery.user_guidance"))
        layout = QVBoxLayout(group)
        
        if self.recovery_plan.user_guidance:
            for guidance in self.recovery_plan.user_guidance:
                guidance_label = BodyLabel(f"• {guidance}")
                guidance_label.setWordWrap(True)
                layout.addWidget(guidance_label)
        else:
            no_guidance_label = CaptionLabel(tr("recovery.no_specific_guidance"))
            layout.addWidget(no_guidance_label)
        
        return group
    
    def _create_progress_section(self) -> QGroupBox:
        """Create progress section"""
        group = QGroupBox(tr("recovery.progress"))
        layout = QVBoxLayout(group)
        
        self.progress_label = BodyLabel(tr("recovery.initializing"))
        layout.addWidget(self.progress_label)
        
        self.progress_bar = IndeterminateProgressBar()
        layout.addWidget(self.progress_bar)
        
        return group
    
    def _create_button_section(self) -> QHBoxLayout:
        """Create button section"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # Auto-recover button
        self.auto_recover_button = PrimaryPushButton(tr("recovery.auto_recover"))
        self.auto_recover_button.clicked.connect(self._start_auto_recovery)
        layout.addWidget(self.auto_recover_button)
        
        # Close button
        close_button = PushButton(tr("common.close"))
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button)
        
        return layout
    
    def _setup_connections(self):
        """Setup signal connections"""
        self.recovery_requested.connect(self._handle_manual_recovery)
    
    def _get_severity_icon(self, severity: ErrorSeverity) -> FIF:
        """Get icon for error severity"""
        icon_map = {
            ErrorSeverity.LOW: FIF.INFO,
            ErrorSeverity.MEDIUM: FIF.WARNING,
            ErrorSeverity.HIGH: FIF.IMPORTANT,
            ErrorSeverity.CRITICAL: FIF.CANCEL
        }
        return icon_map.get(severity, FIF.INFO)
    
    def _start_auto_recovery(self):
        """Start automated recovery process"""
        self.progress_group.show()
        self.auto_recover_button.setEnabled(False)
        
        # Create worker thread
        self.recovery_thread = QThread()
        self.recovery_worker = RecoveryExecutionWorker(self.recovery_plan, self.recovery_context)
        self.recovery_worker.moveToThread(self.recovery_thread)
        
        # Connect signals
        self.recovery_thread.started.connect(self.recovery_worker.execute_recovery)
        self.recovery_worker.progress_updated.connect(self._update_progress)
        self.recovery_worker.action_completed.connect(self._handle_recovery_completed)
        self.recovery_worker.finished.connect(self.recovery_thread.quit)
        self.recovery_thread.finished.connect(self.recovery_thread.deleteLater)
        
        # Start recovery
        self.recovery_thread.start()
    
    def _update_progress(self, message: str):
        """Update progress display"""
        self.progress_label.setText(message)
    
    def _handle_recovery_completed(self, success: bool, message: str):
        """Handle recovery completion"""
        self.progress_group.hide()
        self.auto_recover_button.setEnabled(True)
        
        if success:
            InfoBar.success(
                title=tr("recovery.success"),
                content=message,
                duration=3000,
                parent=self
            )
            self.recovery_completed.emit(True, message)
        else:
            InfoBar.error(
                title=tr("recovery.failed"),
                content=message,
                duration=5000,
                parent=self
            )
            self.recovery_completed.emit(False, message)
    
    def _handle_manual_recovery(self, action: RecoveryAction):
        """Handle manual recovery action"""
        InfoBar.info(
            title=tr("recovery.manual_action"),
            content=f"Please complete: {action.description}",
            duration=5000,
            parent=self
        )
        
        # Emit signal for parent to handle
        self.recovery_requested.emit(action)
    
    def set_recovery_context(self, context: dict):
        """Set recovery context for execution"""
        self.recovery_context = context

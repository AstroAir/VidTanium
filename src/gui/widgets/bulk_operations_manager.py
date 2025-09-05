"""
Bulk Operations Manager for VidTanium
Provides enhanced batch operation interfaces with selection, filtering, and bulk actions
"""

from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass
from enum import Enum
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QCheckBox, QComboBox, QLineEdit, QPushButton, QFrame,
    QScrollArea, QButtonGroup, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QActionGroup

from qfluentwidgets import (
    FluentIcon as FIF, CheckBox, ComboBox, LineEdit, SearchLineEdit,
    PrimaryPushButton, PushButton, DropDownPushButton, TransparentToolButton,
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    ElevatedCardWidget, ScrollArea, VBoxLayout,
    InfoBar, InfoBarPosition
)

from ..utils.i18n import tr
from ..utils.theme import VidTaniumTheme
from ..utils.formatters import format_size, format_duration
from ...core.downloader import TaskStatus


class SelectionMode(Enum):
    """Selection modes for bulk operations"""
    NONE = "none"
    ALL = "all"
    BY_STATUS = "by_status"
    BY_SIZE = "by_size"
    BY_DURATION = "by_duration"
    BY_PATTERN = "by_pattern"
    CUSTOM = "custom"


class BulkAction(Enum):
    """Available bulk actions"""
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    DELETE = "delete"
    RETRY = "retry"
    MOVE_TO_TOP = "move_to_top"
    MOVE_TO_BOTTOM = "move_to_bottom"
    SET_PRIORITY = "set_priority"
    EXPORT_URLS = "export_urls"
    CHANGE_OUTPUT_PATH = "change_output_path"


@dataclass
class SelectionCriteria:
    """Criteria for task selection"""
    mode: SelectionMode
    status_filter: Optional[TaskStatus] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    name_pattern: Optional[str] = None
    url_pattern: Optional[str] = None
    custom_filter: Optional[Callable[[Dict], bool]] = None


class SelectionWidget(ElevatedCardWidget):
    """Widget for task selection with various criteria"""
    
    selection_changed = Signal(list)  # List of selected task IDs
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_tasks: Dict[str, Dict] = {}
        self.selected_tasks: Set[str] = set()
        self.selection_criteria = SelectionCriteria(SelectionMode.NONE)
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = VBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        icon_label = QLabel()
        icon_label.setPixmap(FIF.CHECKBOX.icon().pixmap(20, 20))
        header_layout.addWidget(icon_label)
        
        title_label = BodyLabel(tr("bulk_ops.selection_title"))
        title_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Selection count
        self.count_label = CaptionLabel("0 selected")
        self.count_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Quick selection buttons
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)
        
        self.select_all_btn = PushButton(tr("bulk_ops.select_all"))
        self.select_all_btn.setIcon(FIF.SELECT_ALL)
        self.select_all_btn.clicked.connect(self._select_all)
        quick_layout.addWidget(self.select_all_btn)
        
        self.select_none_btn = PushButton(tr("bulk_ops.select_none"))
        self.select_none_btn.setIcon(FIF.CANCEL)
        self.select_none_btn.clicked.connect(self._select_none)
        quick_layout.addWidget(self.select_none_btn)
        
        self.invert_btn = PushButton(tr("bulk_ops.invert_selection"))
        self.invert_btn.setIcon(FIF.SYNC)
        self.invert_btn.clicked.connect(self._invert_selection)
        quick_layout.addWidget(self.invert_btn)
        
        quick_layout.addStretch()
        layout.addLayout(quick_layout)
        
        # Advanced selection
        advanced_layout = QGridLayout()
        advanced_layout.setSpacing(8)
        
        # Status filter
        status_label = CaptionLabel(tr("bulk_ops.filter_by_status"))
        status_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        advanced_layout.addWidget(status_label, 0, 0)
        
        self.status_combo = ComboBox()
        self.status_combo.addItems([
            tr("bulk_ops.any_status"),
            tr("bulk_ops.status_pending"),
            tr("bulk_ops.status_running"),
            tr("bulk_ops.status_paused"),
            tr("bulk_ops.status_completed"),
            tr("bulk_ops.status_failed")
        ])
        advanced_layout.addWidget(self.status_combo, 0, 1)
        
        # Size filter
        size_label = CaptionLabel(tr("bulk_ops.filter_by_size"))
        size_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        advanced_layout.addWidget(size_label, 1, 0)
        
        size_layout = QHBoxLayout()
        size_layout.setSpacing(4)
        
        self.min_size_edit = LineEdit()
        self.min_size_edit.setPlaceholderText(tr("bulk_ops.min_size"))
        self.min_size_edit.setFixedWidth(80)
        size_layout.addWidget(self.min_size_edit)
        
        size_layout.addWidget(QLabel("-"))
        
        self.max_size_edit = LineEdit()
        self.max_size_edit.setPlaceholderText(tr("bulk_ops.max_size"))
        self.max_size_edit.setFixedWidth(80)
        size_layout.addWidget(self.max_size_edit)
        
        size_layout.addStretch()
        advanced_layout.addLayout(size_layout, 1, 1)
        
        # Pattern filter
        pattern_label = CaptionLabel(tr("bulk_ops.filter_by_pattern"))
        pattern_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        advanced_layout.addWidget(pattern_label, 2, 0)
        
        self.pattern_edit = SearchLineEdit()
        self.pattern_edit.setPlaceholderText(tr("bulk_ops.search_pattern"))
        advanced_layout.addWidget(self.pattern_edit, 2, 1)
        
        layout.addLayout(advanced_layout)
        
        # Apply filters button
        self.apply_filters_btn = PrimaryPushButton(tr("bulk_ops.apply_filters"))
        self.apply_filters_btn.setIcon(FIF.FILTER)
        self.apply_filters_btn.clicked.connect(self._apply_filters)
        layout.addWidget(self.apply_filters_btn)
    
    def _setup_connections(self):
        """Setup signal connections"""
        self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        self.min_size_edit.textChanged.connect(self._on_filter_changed)
        self.max_size_edit.textChanged.connect(self._on_filter_changed)
        self.pattern_edit.textChanged.connect(self._on_filter_changed)
    
    def update_available_tasks(self, tasks: Dict[str, Dict]):
        """Update available tasks for selection"""
        self.available_tasks = tasks
        self._update_selection_count()
    
    def _select_all(self):
        """Select all available tasks"""
        self.selected_tasks = set(self.available_tasks.keys())
        self._update_selection_count()
        self.selection_changed.emit(list(self.selected_tasks))
    
    def _select_none(self):
        """Clear selection"""
        self.selected_tasks.clear()
        self._update_selection_count()
        self.selection_changed.emit(list(self.selected_tasks))
    
    def _invert_selection(self):
        """Invert current selection"""
        all_tasks = set(self.available_tasks.keys())
        self.selected_tasks = all_tasks - self.selected_tasks
        self._update_selection_count()
        self.selection_changed.emit(list(self.selected_tasks))
    
    def _apply_filters(self):
        """Apply current filters to select tasks"""
        criteria = self._build_selection_criteria()
        selected = self._apply_selection_criteria(criteria)
        
        self.selected_tasks = set(selected)
        self._update_selection_count()
        self.selection_changed.emit(list(self.selected_tasks))
    
    def _build_selection_criteria(self) -> SelectionCriteria:
        """Build selection criteria from UI"""
        criteria = SelectionCriteria(SelectionMode.CUSTOM)
        
        # Status filter
        status_text = self.status_combo.currentText()
        if status_text != tr("bulk_ops.any_status"):
            status_mapping = {
                tr("bulk_ops.status_pending"): TaskStatus.PENDING,
                tr("bulk_ops.status_running"): TaskStatus.RUNNING,
                tr("bulk_ops.status_paused"): TaskStatus.PAUSED,
                tr("bulk_ops.status_completed"): TaskStatus.COMPLETED,
                tr("bulk_ops.status_failed"): TaskStatus.FAILED
            }
            criteria.status_filter = status_mapping.get(status_text)
        
        # Size filters
        try:
            if self.min_size_edit.text():
                criteria.min_size = int(self.min_size_edit.text()) * 1024 * 1024  # MB to bytes
        except ValueError:
            pass
        
        try:
            if self.max_size_edit.text():
                criteria.max_size = int(self.max_size_edit.text()) * 1024 * 1024  # MB to bytes
        except ValueError:
            pass
        
        # Pattern filter
        if self.pattern_edit.text():
            criteria.name_pattern = self.pattern_edit.text()
        
        return criteria
    
    def _apply_selection_criteria(self, criteria: SelectionCriteria) -> List[str]:
        """Apply selection criteria and return matching task IDs"""
        selected = []
        
        for task_id, task_data in self.available_tasks.items():
            if self._task_matches_criteria(task_data, criteria):
                selected.append(task_id)
        
        return selected
    
    def _task_matches_criteria(self, task_data: Dict, criteria: SelectionCriteria) -> bool:
        """Check if task matches selection criteria"""
        # Status filter
        if criteria.status_filter and task_data.get('status') != criteria.status_filter:
            return False
        
        # Size filters
        file_size = task_data.get('file_size', 0)
        if criteria.min_size and file_size < criteria.min_size:
            return False
        if criteria.max_size and file_size > criteria.max_size:
            return False
        
        # Pattern filter
        if criteria.name_pattern:
            pattern = criteria.name_pattern.lower()
            task_name = task_data.get('name', '').lower()
            task_url = task_data.get('url', '').lower()
            
            if pattern not in task_name and pattern not in task_url:
                return False
        
        return True
    
    def _on_filter_changed(self):
        """Handle filter change"""
        # Auto-apply filters if enabled
        pass
    
    def _update_selection_count(self):
        """Update selection count display"""
        count = len(self.selected_tasks)
        total = len(self.available_tasks)
        self.count_label.setText(tr("bulk_ops.selection_count").format(count=count, total=total))
    
    def get_selected_tasks(self) -> List[str]:
        """Get currently selected task IDs"""
        return list(self.selected_tasks)
    
    def set_selected_tasks(self, task_ids: List[str]):
        """Set selected tasks"""
        self.selected_tasks = set(task_ids)
        self._update_selection_count()
        self.selection_changed.emit(list(self.selected_tasks))


class BulkActionsWidget(ElevatedCardWidget):
    """Widget for bulk actions on selected tasks"""
    
    action_requested = Signal(str, list, dict)  # action, task_ids, parameters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_tasks: List[str] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = VBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        icon_label = QLabel()
        icon_label.setPixmap(FIF.PLAY.icon().pixmap(20, 20))
        header_layout.addWidget(icon_label)
        
        title_label = BodyLabel(tr("bulk_ops.actions_title"))
        title_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY}; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Action buttons grid
        actions_layout = QGridLayout()
        actions_layout.setSpacing(8)
        
        # Control actions
        self.start_btn = PushButton(tr("bulk_ops.start_selected"))
        self.start_btn.setIcon(FIF.PLAY)
        self.start_btn.clicked.connect(lambda: self._execute_action(BulkAction.START))
        actions_layout.addWidget(self.start_btn, 0, 0)
        
        self.pause_btn = PushButton(tr("bulk_ops.pause_selected"))
        self.pause_btn.setIcon(FIF.PAUSE)
        self.pause_btn.clicked.connect(lambda: self._execute_action(BulkAction.PAUSE))
        actions_layout.addWidget(self.pause_btn, 0, 1)
        
        self.resume_btn = PushButton(tr("bulk_ops.resume_selected"))
        self.resume_btn.setIcon(FIF.PLAY)
        self.resume_btn.clicked.connect(lambda: self._execute_action(BulkAction.RESUME))
        actions_layout.addWidget(self.resume_btn, 0, 2)
        
        # Management actions
        self.cancel_btn = PushButton(tr("bulk_ops.cancel_selected"))
        self.cancel_btn.setIcon(FIF.CANCEL)
        self.cancel_btn.clicked.connect(lambda: self._execute_action(BulkAction.CANCEL))
        actions_layout.addWidget(self.cancel_btn, 1, 0)
        
        self.retry_btn = PushButton(tr("bulk_ops.retry_selected"))
        self.retry_btn.setIcon(FIF.REFRESH)
        self.retry_btn.clicked.connect(lambda: self._execute_action(BulkAction.RETRY))
        actions_layout.addWidget(self.retry_btn, 1, 1)
        
        self.delete_btn = PushButton(tr("bulk_ops.delete_selected"))
        self.delete_btn.setIcon(FIF.DELETE)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {VidTaniumTheme.ERROR_RED};
                border: none;
                color: white;
            }}
            QPushButton:hover {{
                background: {VidTaniumTheme.ERROR_RED}CC;
            }}
        """)
        self.delete_btn.clicked.connect(lambda: self._execute_action(BulkAction.DELETE))
        actions_layout.addWidget(self.delete_btn, 1, 2)
        
        # Queue management
        queue_layout = QHBoxLayout()
        queue_layout.setSpacing(8)
        
        self.move_top_btn = PushButton(tr("bulk_ops.move_to_top"))
        self.move_top_btn.setIcon(FIF.UP)
        self.move_top_btn.clicked.connect(lambda: self._execute_action(BulkAction.MOVE_TO_TOP))
        queue_layout.addWidget(self.move_top_btn)
        
        self.move_bottom_btn = PushButton(tr("bulk_ops.move_to_bottom"))
        self.move_bottom_btn.setIcon(FIF.DOWN)
        self.move_bottom_btn.clicked.connect(lambda: self._execute_action(BulkAction.MOVE_TO_BOTTOM))
        queue_layout.addWidget(self.move_bottom_btn)
        
        # Priority dropdown
        self.priority_btn = DropDownPushButton(tr("bulk_ops.set_priority"))
        self.priority_btn.setIcon(FIF.FLAG)
        
        priority_menu = QMenu(self.priority_btn)
        priority_actions = [
            (tr("bulk_ops.priority_high"), "high"),
            (tr("bulk_ops.priority_normal"), "normal"),
            (tr("bulk_ops.priority_low"), "low")
        ]
        
        for text, priority in priority_actions:
            action = QAction(text, priority_menu)
            action.triggered.connect(
                lambda checked, p=priority: self._execute_action(
                    BulkAction.SET_PRIORITY, {"priority": p}
                )
            )
            priority_menu.addAction(action)
        
        self.priority_btn.setMenu(priority_menu)
        queue_layout.addWidget(self.priority_btn)
        
        actions_layout.addLayout(queue_layout, 2, 0, 1, 3)
        
        # Utility actions
        utility_layout = QHBoxLayout()
        utility_layout.setSpacing(8)
        
        self.export_urls_btn = PushButton(tr("bulk_ops.export_urls"))
        self.export_urls_btn.setIcon(FIF.SHARE)
        self.export_urls_btn.clicked.connect(lambda: self._execute_action(BulkAction.EXPORT_URLS))
        utility_layout.addWidget(self.export_urls_btn)
        
        self.change_path_btn = PushButton(tr("bulk_ops.change_output_path"))
        self.change_path_btn.setIcon(FIF.FOLDER)
        self.change_path_btn.clicked.connect(lambda: self._execute_action(BulkAction.CHANGE_OUTPUT_PATH))
        utility_layout.addWidget(self.change_path_btn)
        
        utility_layout.addStretch()
        actions_layout.addLayout(utility_layout, 3, 0, 1, 3)
        
        layout.addLayout(actions_layout)
        
        # Initially disable all buttons
        self._update_button_states()
    
    def update_selected_tasks(self, task_ids: List[str]):
        """Update selected tasks and button states"""
        self.selected_tasks = task_ids
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button enabled/disabled states based on selection"""
        has_selection = len(self.selected_tasks) > 0
        
        # Enable/disable all buttons based on selection
        for button in [
            self.start_btn, self.pause_btn, self.resume_btn,
            self.cancel_btn, self.retry_btn, self.delete_btn,
            self.move_top_btn, self.move_bottom_btn, self.priority_btn,
            self.export_urls_btn, self.change_path_btn
        ]:
            button.setEnabled(has_selection)
    
    def _execute_action(self, action: BulkAction, parameters: Optional[Dict] = None):
        """Execute bulk action on selected tasks"""
        if not self.selected_tasks:
            InfoBar.warning(
                title=tr("bulk_ops.no_selection_title"),
                content=tr("bulk_ops.no_selection_message"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        self.action_requested.emit(action.value, self.selected_tasks, parameters or {})


class BulkOperationsManager(ScrollArea):
    """Main bulk operations manager widget"""
    
    action_requested = Signal(str, list, dict)  # action, task_ids, parameters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create main widget
        main_widget = QWidget()
        self.setWidget(main_widget)
        
        layout = VBoxLayout(main_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = TitleLabel(tr("bulk_ops.manager_title"))
        title_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_PRIMARY};")
        layout.addWidget(title_label)
        
        # Selection widget
        self.selection_widget = SelectionWidget()
        self.selection_widget.selection_changed.connect(self._on_selection_changed)
        layout.addWidget(self.selection_widget)
        
        # Actions widget
        self.actions_widget = BulkActionsWidget()
        self.actions_widget.action_requested.connect(self.action_requested.emit)
        layout.addWidget(self.actions_widget)
        
        layout.addStretch()
    
    def update_available_tasks(self, tasks: Dict[str, Dict]):
        """Update available tasks for bulk operations"""
        self.selection_widget.update_available_tasks(tasks)
    
    def _on_selection_changed(self, selected_task_ids: List[str]):
        """Handle selection change"""
        self.actions_widget.update_selected_tasks(selected_task_ids)
    
    def get_selected_tasks(self) -> List[str]:
        """Get currently selected task IDs"""
        return list(self.selection_widget.get_selected_tasks())
    
    def clear_selection(self):
        """Clear current selection"""
        self.selection_widget._select_none()

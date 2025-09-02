"""Enhanced Schedule Manager with responsive design and modern theming"""

from typing import Optional, Union
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QCursor
from datetime import datetime
import logging

from qfluentwidgets import (
    InfoBar, InfoBarPosition, MessageBox, Action, RoundMenu,
    SearchLineEdit, ComboBox, SubtitleLabel, ToggleButton,
    CardWidget, FluentIcon as FIF, ElevatedCardWidget, HeaderCardWidget,
    StrongBodyLabel, BodyLabel, CaptionLabel
)

# Import split components
from .schedule.task_details_widget import TaskDetailsWidget
from .schedule.task_table import TaskTable
from .schedule.schedule_toolbar import ScheduleToolbar

# Import responsive design and theming
from ..utils.i18n import tr
from ..utils.responsive import ResponsiveWidget, ResponsiveManager, ResponsiveContainer
from ..utils.theme import VidTaniumTheme
from ..theme_manager import EnhancedThemeManager
from loguru import logger


class EnhancedScheduleManager(ResponsiveWidget):
    """Enhanced schedule manager with responsive design and modern theming
    
    Features:
    - Full responsive design with breakpoint adaptation
    - Enhanced theming integration with EnhancedThemeManager
    - Modern card-based layout with improved visual hierarchy
    - Adaptive layouts for different screen sizes
    - Performance optimizations and smooth animations
    """

    # Configurable auto-refresh interval (milliseconds)
    AUTO_REFRESH_INTERVAL_MS = 30 * 1000  # Default 30 seconds

    # Signal definitions
    task_action_requested = Signal(str, str)  # task_id, action

    def __init__(self, scheduler, theme_manager=None, parent=None):
        super().__init__(parent)

        self.scheduler = scheduler
        self.theme_manager = theme_manager
        self.responsive_manager = ResponsiveManager.instance()
        self.current_filter = "all"
        self.refresh_timer = None

        self._create_enhanced_ui()
        self._connect_signals()
        self._apply_enhanced_theming()
        self._populate_tasks()
        self._setup_auto_refresh()

    def _create_enhanced_ui(self):
        """Create enhanced responsive UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        current_bp = self.responsive_manager.get_current_breakpoint()
        if current_bp.value in ['xs', 'sm']:
            layout.setSpacing(12)
        else:
            layout.setSpacing(16)

        # Enhanced header with responsive design
        self._create_enhanced_header(layout)

        # Enhanced toolbar
        self._create_enhanced_toolbar(layout)

        # Responsive main content area
        self._create_responsive_content(layout)

    def _create_enhanced_header(self, parent_layout):
        """Create enhanced header with gradient and responsive design"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        header_card = HeaderCardWidget()
        if current_bp.value in ['xs', 'sm']:
            header_card.setFixedHeight(60)
        else:
            header_card.setFixedHeight(80)

        header_layout = QHBoxLayout(header_card)
        if current_bp.value in ['xs', 'sm']:
            header_layout.setContentsMargins(16, 12, 16, 12)
            header_layout.setSpacing(12)
        else:
            header_layout.setContentsMargins(24, 16, 24, 16)
            header_layout.setSpacing(16)

        # Title section with responsive typography
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        self.title_label = SubtitleLabel(tr("schedule_manager.title"))
        if current_bp.value in ['xs', 'sm']:
            self.title_label.setStyleSheet(f"""
                font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
                color: {VidTaniumTheme.TEXT_PRIMARY};
                margin: 0;
            """)
        else:
            self.title_label.setStyleSheet(f"""
                font-size: {VidTaniumTheme.FONT_SIZE_HEADING};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD};
                color: {VidTaniumTheme.TEXT_PRIMARY};
                margin: 0;
            """)
        title_layout.addWidget(self.title_label)

        if current_bp.value not in ['xs', 'sm']:
            subtitle_label = CaptionLabel(tr("schedule_manager.subtitle"))
            subtitle_label.setStyleSheet(f"""
                color: {VidTaniumTheme.TEXT_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_CAPTION};
                margin: 0;
            """)
            title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Auto-refresh toggle with enhanced styling
        self.auto_refresh = ToggleButton(tr("schedule_manager.auto_refresh"))
        self.auto_refresh.setChecked(True)
        if current_bp.value in ['xs', 'sm']:
            self.auto_refresh.setFixedSize(80, 32)
        else:
            self.auto_refresh.setFixedSize(120, 36)
        header_layout.addWidget(self.auto_refresh)

        parent_layout.addWidget(header_card)

    def _create_enhanced_toolbar(self, parent_layout):
        """Create enhanced responsive toolbar"""
        toolbar_card = ElevatedCardWidget()
        toolbar_layout = QVBoxLayout(toolbar_card)
        
        current_bp = self.responsive_manager.get_current_breakpoint()
        if current_bp.value in ['xs', 'sm']:
            toolbar_layout.setContentsMargins(12, 12, 12, 12)
            toolbar_layout.setSpacing(12)
        else:
            toolbar_layout.setContentsMargins(16, 16, 16, 16)
            toolbar_layout.setSpacing(16)

        # Toolbar with responsive behavior
        self.toolbar = ScheduleToolbar(self)
        toolbar_layout.addWidget(self.toolbar)

        # Search and filter section with responsive layout
        filter_section = QWidget()
        if current_bp.value in ['xs', 'sm']:
            # Vertical layout for small screens
            filter_layout: Union[QVBoxLayout, QHBoxLayout] = QVBoxLayout(filter_section)
            filter_layout.setSpacing(8)
        else:
            # Horizontal layout for larger screens
            filter_layout = QHBoxLayout(filter_section)
            filter_layout.setSpacing(12)
        
        filter_layout.setContentsMargins(0, 0, 0, 0)

        # Enhanced search input
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText(tr("schedule_manager.search.placeholder"))
        if current_bp.value in ['xs', 'sm']:
            self.search_input.setMinimumHeight(36)
        else:
            self.search_input.setMinimumHeight(40)
        filter_layout.addWidget(self.search_input, 2)

        # Enhanced filter combo
        self.filter_combo = ComboBox()
        self.filter_combo.addItems([
            tr("schedule_manager.filters.all"),
            tr("schedule_manager.filters.enabled"),
            tr("schedule_manager.filters.disabled"),
            tr("schedule_manager.filters.one_time"),
            tr("schedule_manager.filters.recurring")
        ])
        if current_bp.value in ['xs', 'sm']:
            self.filter_combo.setMinimumHeight(36)
        else:
            self.filter_combo.setMinimumHeight(40)
        filter_layout.addWidget(self.filter_combo, 1)

        toolbar_layout.addWidget(filter_section)
        parent_layout.addWidget(toolbar_card)

    def _create_responsive_content(self, parent_layout):
        """Create responsive main content area"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Responsive splitter configuration
        if current_bp.value in ['xs', 'sm']:
            # Vertical layout for small screens
            self.splitter = QSplitter(Qt.Orientation.Vertical)
        else:
            # Horizontal layout for larger screens
            self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.splitter.setChildrenCollapsible(False)

        # Enhanced table card
        self._create_enhanced_table_card()

        # Enhanced details panel
        self._create_enhanced_details_panel()

        # Responsive splitter sizing
        if current_bp.value in ['xs', 'sm']:
            self.splitter.setStretchFactor(0, 3)
            self.splitter.setStretchFactor(1, 1)
        else:
            self.splitter.setStretchFactor(0, 2)
            self.splitter.setStretchFactor(1, 1)

        parent_layout.addWidget(self.splitter)

    def _create_enhanced_table_card(self):
        """Create enhanced table card with modern styling"""
        table_card = ElevatedCardWidget()
        table_layout = QVBoxLayout(table_card)
        
        current_bp = self.responsive_manager.get_current_breakpoint()
        if current_bp.value in ['xs', 'sm']:
            table_layout.setContentsMargins(12, 12, 12, 12)
            table_layout.setSpacing(12)
        else:
            table_layout.setContentsMargins(16, 16, 16, 16)
            table_layout.setSpacing(16)

        # Enhanced table header
        table_header = StrongBodyLabel(tr("schedule_manager.table.title"))
        table_header.setStyleSheet(f"""
            font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
            color: {VidTaniumTheme.TEXT_PRIMARY};
            margin-bottom: 8px;
        """)
        table_layout.addWidget(table_header)

        # Enhanced task table
        self.task_table = TaskTable()
        table_layout.addWidget(self.task_table)

        # Enhanced status bar
        self._create_enhanced_status_bar(table_layout)

        self.splitter.addWidget(table_card)

    def _create_enhanced_status_bar(self, parent_layout):
        """Create enhanced status bar with modern styling"""
        status_container = ResponsiveContainer()
        status_layout = QHBoxLayout(status_container)
        
        current_bp = self.responsive_manager.get_current_breakpoint()
        if current_bp.value in ['xs', 'sm']:
            status_layout.setContentsMargins(8, 8, 8, 8)
            status_layout.setSpacing(8)
        else:
            status_layout.setContentsMargins(12, 12, 12, 12)
            status_layout.setSpacing(12)

        # Enhanced status label
        self.status_label = BodyLabel(tr("schedule_manager.loading"))
        self.status_label.setStyleSheet(f"""
            color: {VidTaniumTheme.TEXT_SECONDARY};
            font-size: {VidTaniumTheme.FONT_SIZE_CAPTION};
        """)
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        # Enhanced refresh countdown
        self.next_update_label = CaptionLabel()
        self.next_update_label.setStyleSheet(f"""
            color: {VidTaniumTheme.TEXT_TERTIARY};
            font-size: {VidTaniumTheme.FONT_SIZE_MICRO};
        """)
        status_layout.addWidget(self.next_update_label)

        parent_layout.addWidget(status_container)

    def _create_enhanced_details_panel(self):
        """Create enhanced details panel"""
        # Enhanced task details widget
        self.task_details = TaskDetailsWidget()
        self.splitter.addWidget(self.task_details)
        # Initially hidden
        self.task_details.setVisible(False)

    def _apply_enhanced_theming(self):
        """Apply enhanced theming to the schedule manager"""
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            accent_color = self.theme_manager.ACCENT_COLORS.get(
                self.theme_manager.get_current_accent(), '#0078D4'
            )
            
            # Apply enhanced styling
            self.setStyleSheet(f"""
                ScheduleManager {{
                    background-color: {colors.get('background', VidTaniumTheme.BG_PRIMARY)};
                }}
                ElevatedCardWidget {{
                    background-color: {colors.get('surface', VidTaniumTheme.BG_SURFACE)};
                    border: 1px solid {colors.get('border', VidTaniumTheme.BORDER_LIGHT)};
                    border-radius: 8px;
                    box-shadow: 0 2px 8px {colors.get('shadow', 'rgba(0, 0, 0, 0.1)')};
                }}
                HeaderCardWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {accent_color}, stop:1 rgba(255, 255, 255, 0.1));
                    border: none;
                    border-radius: 8px;
                }}
                SearchLineEdit, ComboBox {{
                    background-color: {colors.get('surface', VidTaniumTheme.BG_SURFACE)};
                    border: 2px solid {colors.get('border', VidTaniumTheme.BORDER_LIGHT)};
                    border-radius: 6px;
                    padding: 8px 12px;
                }}
                SearchLineEdit:focus, ComboBox:focus {{
                    border-color: {accent_color};
                }}
                QSplitter::handle {{
                    background-color: {colors.get('border', VidTaniumTheme.BORDER_LIGHT)};
                }}
                QSplitter::handle:horizontal {{
                    width: 2px;
                }}
                QSplitter::handle:vertical {{
                    height: 2px;
                }}
            """)

    def on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        logger.debug(f"Schedule manager adapting to breakpoint: {breakpoint}")
        # Recreate UI with new breakpoint
        self._create_enhanced_ui()
        self._apply_enhanced_theming()

    def update_theme(self, theme_manager: Optional[EnhancedThemeManager] = None):
        """Update theme styling"""
        if theme_manager:
            self.theme_manager = theme_manager
        self._apply_enhanced_theming()

    def _connect_signals(self):
        """连接信号与槽"""
        # 自动刷新开关
        self.auto_refresh.toggled.connect(self._toggle_auto_refresh)

        # 表格过滤信号
        self.search_input.textChanged.connect(self._filter_tasks)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)

        # 表格上下文菜单
        self.task_table.customContextMenuRequested.connect(
            self._show_context_menu)
        self.task_table.task_clicked.connect(self._show_task_details)

        # 设置操作处理函数
        self.task_table.set_action_handlers({
            'enable': lambda task_id: self.task_action_requested.emit(task_id, "enable"),
            'disable': lambda task_id: self.task_action_requested.emit(task_id, "disable"),
            'run_now': lambda task_id: self.task_action_requested.emit(task_id, "run_now"),
            'show_details': self._show_task_details,
            'remove': lambda task_id: self.task_action_requested.emit(task_id, "remove")
        })

        # 详情面板按钮
        self.task_details.enable_button.clicked.connect(self._on_toggle_task)
        self.task_details.run_now_button.clicked.connect(self._on_run_now)
        self.task_details.delete_button.clicked.connect(self._on_delete_task)

        # 工具栏按钮
        self.toolbar.new_task_clicked.connect(
            lambda: self.task_action_requested.emit("", "new"))
        self.toolbar.refresh_clicked.connect(self._populate_tasks)
        self.toolbar.enable_all_clicked.connect(self._on_enable_all)
        self.toolbar.disable_all_clicked.connect(self._on_disable_all)
        self.toolbar.view_details_toggled.connect(
            self.task_details.setVisible)        # 初始隐藏详情面板
        self.task_details.setVisible(False)

    def _setup_auto_refresh(self):
        """设置自动刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(self.AUTO_REFRESH_INTERVAL_MS)  # 使用可配置间隔
        self._update_refresh_countdown()

    def _update_refresh_countdown(self):
        """更新刷新倒计时"""
        if self.refresh_timer and self.refresh_timer.isActive():
            seconds = self.refresh_timer.remainingTime() // 1000
            self.next_update_label.setText(
                tr("schedule_manager.status_bar.refresh_in", seconds=seconds))

            # 每秒更新倒计时
            QTimer.singleShot(1000, self._update_refresh_countdown)
        else:
            self.next_update_label.setText(
                tr("schedule_manager.auto_refresh_off"))

    def _toggle_auto_refresh(self, enabled):
        """切换自动刷新"""
        if enabled and self.refresh_timer:
            self.refresh_timer.start(self.AUTO_REFRESH_INTERVAL_MS)
            self._update_refresh_countdown()
        elif self.refresh_timer:
            self.refresh_timer.stop()
            self.next_update_label.setText(
                tr("schedule_manager.auto_refresh_off"))

    def _auto_refresh(self):
        """自动刷新"""
        self._populate_tasks()

    def _on_filter_changed(self, index):
        """处理过滤器变化"""
        filters = ["all", "enabled", "disabled", "one_time", "recurring"]
        if index >= 0 and index < len(filters):
            self.current_filter = filters[index]
            self._filter_tasks()

    def _filter_tasks(self):
        """过滤任务"""
        search_text = self.search_input.text()
        self.task_table.filter_tasks(search_text, self.current_filter)

        # 更新状态栏信息
        visible_rows = self.task_table.get_visible_rows_count()
        total_rows = self.task_table.get_total_rows_count()
        self.status_label.setText(
            tr("schedule_manager.status_bar.showing", visible=visible_rows, total=total_rows))

    def _populate_tasks(self):
        """填充任务列表"""
        tasks = self.scheduler.get_all_tasks()
        self.task_table.populate_tasks(tasks)

        # 应用当前过滤器
        self._filter_tasks()

    def _show_task_details(self, task_id):
        """显示任务详情"""
        task = self.scheduler.get_task(task_id)
        if task:
            self.toolbar.set_details_checked(True)
            self.task_details.update_task(task)

    def _on_toggle_task(self):
        """切换任务状态"""
        if not self.task_details.current_task:
            return

        task_id = self.task_details.current_task.task_id
        action = "disable" if self.task_details.current_task.enabled else "enable"
        self.task_action_requested.emit(task_id, action)

    def _on_run_now(self):
        """立即执行任务"""
        if not self.task_details.current_task:
            return

        self.task_action_requested.emit(
            self.task_details.current_task.task_id, "run_now")

    def _on_delete_task(self):
        """删除任务"""
        if not self.task_details.current_task:
            return

        self.task_action_requested.emit(
            self.task_details.current_task.task_id, "remove")

    def _show_context_menu(self, position):
        """显示上下文菜单"""
        index = self.task_table.indexAt(position)
        if not index.isValid():
            return

        row = index.row()
        name_item = self.task_table.item(row, 0)
        if not name_item:
            return

        task_id = name_item.data(Qt.ItemDataRole.UserRole)
        task = self.scheduler.get_task(task_id)
        if not task:
            return

        # 创建上下文菜单
        menu = RoundMenu(
            tr("schedule_manager.context_menu.task_actions"), self)

        # 添加不同操作基于任务状态
        if task.enabled:
            disable_action = Action(FIF.PAUSE, tr(
                "schedule_manager.actions.disable"))
            disable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "disable"))
            menu.addAction(disable_action)
        else:
            enable_action = Action(FIF.PLAY, tr(
                "schedule_manager.actions.enable"))
            enable_action.triggered.connect(
                lambda: self.task_action_requested.emit(task_id, "enable"))
            menu.addAction(enable_action)

        # 立即执行
        run_now_action = Action(FIF.PLAY_SOLID, tr(
            "schedule_manager.actions.run_now"))
        run_now_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "run_now"))
        menu.addAction(run_now_action)

        # 查看详情
        view_details_action = Action(FIF.INFO, tr(
            "schedule_manager.actions.view_details"))
        view_details_action.triggered.connect(
            lambda: self._show_task_details(task_id))
        menu.addAction(view_details_action)

        menu.addSeparator()

        # 删除操作
        remove_action = Action(FIF.DELETE, tr(
            "schedule_manager.actions.delete"))
        remove_action.triggered.connect(
            lambda: self.task_action_requested.emit(task_id, "remove"))
        menu.addAction(remove_action)

        # 显示菜单
        menu.exec(QCursor.pos())

    def _on_enable_all(self):
        """启用所有任务"""
        result = MessageBox(tr("schedule_manager.batch_operations.title"),
                            tr("schedule_manager.messages.confirm_enable_all"), self).exec()
        if not result:
            return

        tasks = self.scheduler.get_all_tasks()
        enabled_count = 0

        for task in tasks:
            if not task.enabled:
                self.task_action_requested.emit(task.task_id, "enable")
                enabled_count += 1

        if enabled_count > 0:
            self.show_message(tr("schedule_manager.batch_operations.title"),
                              tr("schedule_manager.messages.batch_enabled", count=enabled_count))
        else:
            self.show_message(tr("schedule_manager.batch_operations.title"),
                              tr("schedule_manager.messages.no_tasks_to_enable"), type_="info")

    def _on_disable_all(self):
        """禁用所有任务"""
        result = MessageBox(tr("schedule_manager.batch_operations.title"),
                            tr("schedule_manager.messages.confirm_disable_all"), self).exec()
        if not result:
            return

        tasks = self.scheduler.get_all_tasks()
        disabled_count = 0

        for task in tasks:
            if task.enabled:
                self.task_action_requested.emit(task.task_id, "disable")
                disabled_count += 1

        if disabled_count > 0:
            self.show_message(tr("schedule_manager.batch_operations.title"),
                              tr("schedule_manager.messages.batch_disabled", count=disabled_count))
        else:
            self.show_message(tr("schedule_manager.batch_operations.title"),
                              tr("schedule_manager.messages.no_tasks_to_disable"), type_="info")

    def show_message(self, title, content, type_="success"):
        """显示消息通知"""
        if type_ == "success":
            InfoBar.success(title, content, parent=self,
                            position=InfoBarPosition.TOP)
        elif type_ == "warning":
            InfoBar.warning(title, content, parent=self,
                            position=InfoBarPosition.TOP)
        elif type_ == "error":
            InfoBar.error(title, content, parent=self,
                          position=InfoBarPosition.TOP)
        else:
            InfoBar.info(title, content, parent=self,
                         position=InfoBarPosition.TOP)

    def update_task(self, task_id):
        """更新特定任务"""
        task = self.scheduler.get_task(task_id)
        if task:
            # 更新表格中的任务行
            self.task_table.update_task_row(task_id, task)

            # 如果是当前显示的任务，更新详情面板
            if (self.task_details.isVisible() and
                    self.task_details.current_task and
                    self.task_details.current_task.task_id == task_id):
                self.task_details.update_task(task)

    def update_locale(self):
        """更新界面语言"""
        # 更新标题和按钮文本
        self.title_label.setText(tr("schedule_manager.title"))
        self.auto_refresh.setText(tr("schedule_manager.auto_refresh"))

        # 更新搜索框占位符
        self.search_input.setPlaceholderText(
            tr("schedule_manager.search.placeholder"))

        # 更新过滤器选项
        self.filter_combo.clear()
        self.filter_combo.addItems([
            tr("schedule_manager.filters.all"),
            tr("schedule_manager.filters.enabled"),
            tr("schedule_manager.filters.disabled"),
            tr("schedule_manager.filters.one_time"),
            tr("schedule_manager.filters.recurring")
        ])

        # 更新状态标签
        if hasattr(self, 'task_table'):
            visible_rows = self.task_table.get_visible_rows_count()
            total_rows = self.task_table.get_total_rows_count()
            self.status_label.setText(
                tr("schedule_manager.status_bar.showing", visible=visible_rows, total=total_rows))

        # 更新刷新状态文本
        if self.refresh_timer and self.refresh_timer.isActive():
            self._update_refresh_countdown()
        else:
            self.next_update_label.setText(
                tr("schedule_manager.auto_refresh_off"))


# Backward compatibility alias
ScheduleManager = EnhancedScheduleManager

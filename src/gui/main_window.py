"""
Main window for VidTanium application - Enhanced with responsive design
"""
from typing import Any, Dict, List, Optional, Union, Callable
from src.core.downloader import ProgressDict, TaskStatus as CoreTaskStatus
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSplitter, QApplication,
    QFormLayout, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import (
    QPixmap, QColor, QPainter, QCloseEvent
)
from src.core.downloader import DownloadManager
from loguru import logger

from qfluentwidgets import (
    FluentIcon as FIF, InfoBar, InfoBarPosition,
    FluentWindow, NavigationItemPosition,
    TitleLabel, BodyLabel, PrimaryPushButton, StrongBodyLabel,
    SmoothScrollArea, ElevatedCardWidget,
    LineEdit, TextEdit, TransparentToolButton,
    CheckBox, ComboBox,
    SystemThemeListener, setTheme, Theme
)

# UI components
from .widgets.navigation import NavigationPanel, ModernBreadcrumb
from .widgets import dashboard
Dashboard = dashboard.Dashboard  # type: ignore
from .widgets.progress import ProgressCard, ProgressSummaryCard
from .utils.design_system import DesignSystem

from .widgets.task_manager import TaskManager
from .widgets.log.log_viewer import LogViewer
from .widgets.dashboard.dashboard_interface import DashboardInterface
# Settings interfaces
from .widgets.settings import SettingsInterface, SettingsDialog
from .widgets.help import HelpInterface
from .theme_manager import ThemeManager
from .utils.responsive import ResponsiveWidget, ResponsiveManager, ResponsiveContainer
from .dialogs.task_dialog import TaskDialog
from .dialogs.about_dialog import AboutDialog
from .dialogs.batch_url_dialog import BatchURLDialog
from src.core.downloader import DownloadTask
from .utils.formatters import format_speed
from .utils.i18n import tr


class AppType(QApplication):
    tray_icon: Any

    def send_notification(self, title: str, message: str, icon: Optional[FIF] = None, duration: int = 5000) -> None:
        """Send system notification"""
        # Implementation would be handled by the application
        pass

    def _apply_theme(self) -> None:
        """Apply theme settings"""
        # Implementation would be handled by the application
        pass


class SettingsType:
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get setting value"""
        # Implementation would be handled by settings manager
        return default

    def set(self, section: str, key: str, value: Any) -> None:
        """Set setting value"""
        # Implementation would be handled by settings manager
        pass

    def save_settings(self) -> None:
        """Save settings to file"""
        # Implementation would be handled by settings manager
        pass


class StatusInfoWidget(QWidget):
    """Status information widget with icon and text"""

    def __init__(self, icon: Union[FIF, QPixmap], text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.icon: Union[FIF, QPixmap] = icon
        self.text: str = text
        self.icon_color: Optional[QColor] = None
        self.icon_label: QLabel
        self.text_label: QLabel
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(4)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(self.text)
        layout.addWidget(self.text_label)

        self._update_icon()

    def setContent(self, icon: Union[FIF, QPixmap], text: str) -> None:
        """Update widget content"""
        self.icon = icon
        self.text = text
        self.text_label.setText(text)
        self._update_icon()

    def setIconColor(self, color: QColor) -> None:
        """Set icon color"""
        self.icon_color = color
        self._update_icon()

    def _update_icon(self) -> None:
        """Update icon display"""
        if isinstance(self.icon, FIF):
            pixmap = self._create_colored_pixmap(self.icon, self.icon_color)
            self.icon_label.setPixmap(pixmap)
        elif isinstance(self.icon, QPixmap):
            self.icon_label.setPixmap(self.icon.scaled(
                16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _create_colored_pixmap(self, fluent_icon: FIF, color: Optional[QColor] = None) -> QPixmap:
        """Create colored version of FluentIcon"""
        original_pixmap: QPixmap = fluent_icon.icon().pixmap(16, 16)

        if color is None:
            return original_pixmap

        colored_pixmap = QPixmap(original_pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawPixmap(0, 0, original_pixmap)
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), color)
        painter.end()

        return colored_pixmap


class MainWindow(FluentWindow):
    """Enhanced main application window with responsive design"""

    def __init__(self, app: AppType, download_manager: "DownloadManager", settings: SettingsType, theme_manager=None):
        super().__init__()
        self.app: AppType = app
        self.download_manager: "DownloadManager" = download_manager
        self.settings: SettingsType = settings
        self.theme_manager: ThemeManager = theme_manager
        self._force_close: bool = False
        
        # Initialize responsive manager
        self.responsive_manager = ResponsiveManager.instance()
        
        # Initialize interface components
        self.dashboard_component: Optional[DashboardInterface] = None
        self.task_manager: Optional[TaskManager] = None
        self.log_viewer: Optional[LogViewer] = None
        self.mini_log_viewer: Optional[TextEdit] = None

        # Initialize interfaces
        self.home_interface: QWidget
        self.download_interface: QWidget
        self.log_interface: QWidget
        self.settings_interface: QWidget
        
        # Timers for real-time updates
        self.auto_save_timer: QTimer

        # Performance optimization: adaptive stats update timer
        self.stats_update_timer: QTimer = QTimer(self)
        self.stats_update_timer.timeout.connect(self._update_statistics)
        self._last_active_tasks = 0
        self._adaptive_update_interval()  # Start with adaptive interval

        # Task refresh timer for syncing with download manager
        self.task_refresh_timer: QTimer = QTimer(self)
        self.task_refresh_timer.timeout.connect(self._refresh_task_list)
        # Reduced frequency: refresh every 5 seconds
        self.task_refresh_timer.start(5000)

        # Connect download manager signals if available
        if self.download_manager:
            self.download_manager.on_task_progress = self.on_task_progress
            self.download_manager.on_task_status_changed = self.on_task_status_changed
            self.download_manager.on_task_completed = self.on_task_completed
            self.download_manager.on_task_failed = self.on_task_failed

        # Setup responsive window sizing
        self._setup_responsive_window()
        
        # Connect responsive callbacks
        self.responsive_manager.add_breakpoint_callback(self._on_breakpoint_changed)
        self.responsive_manager.add_orientation_callback(self._on_orientation_changed)
        
        # Setup UI and interfaces
        self._setup_interfaces()
        
        # Apply theme enhancements
        if self.theme_manager:
            self.theme_manager.apply_widget_enhancement(self, "main-window")

    def _setup_responsive_window(self):
        """Setup responsive window sizing and behavior"""
        self.setWindowTitle(tr("app.title"))
        
        # Set responsive minimum sizes based on breakpoints
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.availableGeometry()
            screen_width = screen_size.width()
            
            # Determine minimum size based on screen size
            if screen_width < 768:  # Small screens
                self.setMinimumSize(600, 500)
            elif screen_width < 1200:  # Medium screens
                self.setMinimumSize(800, 600)
            else:  # Large screens
                self.setMinimumSize(1000, 700)
            
            # Set initial size as percentage of screen
            width = min(max(int(screen_width * 0.8), self.minimumWidth()), 1600)
            height = min(max(int(screen_size.height() * 0.8), self.minimumHeight()), 1000)
            self.resize(width, height)
            
            # Update responsive manager with current size
            self.responsive_manager.update_for_size(self.size())

    def _on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        logger.debug(f"Main window adapting to breakpoint: {breakpoint}")
        
        # Adjust navigation panel based on breakpoint
        if hasattr(self, 'navigationInterface'):
            if breakpoint in ['xs', 'sm']:
                # Collapse navigation on small screens
                self.navigationInterface.setCollapsed(True)
            else:
                # Expand navigation on larger screens
                self.navigationInterface.setCollapsed(False)
        
        # Adjust content layout
        self._adjust_content_layout(breakpoint)
        
        # Update theme styling for new breakpoint
        if self.theme_manager:
            self.theme_manager._apply_custom_styling()

    def _on_orientation_changed(self, orientation: Qt.Orientation):
        """Handle orientation changes"""
        logger.debug(f"Main window orientation changed: {orientation}")
        # Additional orientation-specific adjustments can be added here

    def _on_help_error(self, error_message: str):
        """Handle help system errors"""
        logger.warning(f"Help system error: {error_message}")
        # Error is already displayed by the help interface, just log it

    def _adjust_content_layout(self, breakpoint: str):
        """Adjust content layout based on breakpoint"""
        if not hasattr(self, 'dashboard_component') or not self.dashboard_component:
            return
            
        # Adjust dashboard layout based on screen size
        if breakpoint in ['xs', 'sm']:
            # Stack components vertically on small screens
            self.dashboard_component.set_layout_mode('vertical')
        else:
            # Use horizontal layout on larger screens
            self.dashboard_component.set_layout_mode('horizontal')

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        self.responsive_manager.update_for_size(event.size())

        self.setWindowIcon(FIF.VIDEO.icon())

        # Initialize UI
        self._create_interfaces()
        self._init_navigation()
        self._connect_signals()
        self._setup_auto_save()
        self._update_ui()

        # Apply theme and add theme listener
        self._setup_theme_system()

        logger.info("Main window initialized")

    def _create_interfaces(self) -> None:
        """Create all application interfaces"""
        # Dashboard interface
        self.dashboard_component = Dashboard(self)  # EnhancedDashboardInterface alias
        self.home_interface = self.dashboard_component.create_interface()
        self.home_interface.setObjectName("home_interface")

        # Download management interface
        self.download_interface = self._create_download_interface()
        self.download_interface.setObjectName("download_interface")

        # Log viewing interface
        self.log_interface = self._create_log_interface()
        self.log_interface.setObjectName("log_interface")

        # Settings interface
        self.settings_interface = self._create_settings_interface()
        self.settings_interface.setObjectName("settings_interface")

        # Help interface
        self.help_interface = self._create_help_interface()
        self.help_interface.setObjectName("help_interface")

    def _init_navigation(self) -> None:
        """Initialize navigation menu with enhanced styling"""
        # Apply styling to navigation
        self.navigationInterface.setStyleSheet(f"""
            NavigationInterface {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border-right: 1px solid {DesignSystem.get_color('border_adaptive')};
            }}
        """)

        # Dashboard
        self.addSubInterface(
            self.home_interface,
            FIF.HOME,
            tr('navigation.dashboard'),
            NavigationItemPosition.TOP
        )

        # Download management
        self.addSubInterface(
            self.download_interface,
            FIF.DOWNLOAD,
            tr('navigation.download'),
            NavigationItemPosition.TOP
        )

        # Activity logs
        self.addSubInterface(
            self.log_interface,
            FIF.HISTORY,
            tr('navigation.logs'),
            NavigationItemPosition.TOP
        )

        # Help
        self.addSubInterface(
            self.help_interface,
            FIF.HELP,
            tr('navigation.help'),
            NavigationItemPosition.BOTTOM
        )

        # Settings
        self.addSubInterface(
            self.settings_interface,
            FIF.SETTING,
            tr('navigation.settings'),
            NavigationItemPosition.BOTTOM
        )

        # Apply enhanced navigation styling
        self._apply_enhanced_styling()

    def _apply_enhanced_styling(self):
        """Apply styling to the main window"""
        # Main window styling
        self.setStyleSheet(f"""
            FluentWindow {{
                background: {DesignSystem.get_color('surface_adaptive')};
            }}

            /* Navigation item styling */
            NavigationTreeWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}

            NavigationTreeWidget::item {{
                padding: 8px 12px;
                margin: 2px 8px;
                border-radius: {DesignSystem.RADIUS['md']}px;
                color: {DesignSystem.get_color('text_primary_adaptive')};
            }}

            NavigationTreeWidget::item:hover {{
                background: {DesignSystem.get_color('surface_secondary_adaptive')};
            }}

            NavigationTreeWidget::item:selected {{
                background: {DesignSystem.get_color('primary')};
                color: white;
                font-weight: 600;
            }}
        """)

    def _create_download_interface(self) -> QWidget:
        """Create download management interface with responsive design"""
        interface = QWidget()
        main_layout = QVBoxLayout(interface)
        # Reduced margins for better space usage
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)  # Reduced spacing

        # Top toolbar with responsive layout
        toolbar_layout = QHBoxLayout()

        # Title
        title = TitleLabel(tr("download.title"))
        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch()

        # Search box with responsive sizing
        search_box = LineEdit()
        search_box.setPlaceholderText(tr("download.search_placeholder"))
        search_box.setMinimumWidth(150)  # Use minimum width instead of fixed
        # Set maximum to prevent excessive growth
        search_box.setMaximumWidth(250)
        search_box.setFixedHeight(35)
        toolbar_layout.addWidget(search_box)

        # Filter dropdown with responsive sizing
        filter_combo = ComboBox()
        filter_combo.addItems([
            tr("download.filter.all"),
            tr("download.filter.running"),
            tr("download.filter.paused"),
            tr("download.filter.completed"),
            tr("download.filter.failed")
        ])
        filter_combo.setMinimumWidth(100)  # Use minimum width
        filter_combo.setMaximumWidth(140)  # Set maximum width
        filter_combo.setFixedHeight(35)
        toolbar_layout.addWidget(filter_combo)

        # Refresh button
        refresh_btn = TransparentToolButton(FIF.SYNC)
        refresh_btn.setToolTip(tr("download.buttons.refresh"))
        refresh_btn.setFixedSize(35, 35)
        toolbar_layout.addWidget(refresh_btn)

        main_layout.addLayout(toolbar_layout)

        # Action buttons bar
        actions_layout = QHBoxLayout()

        # New task button
        new_task_btn = PrimaryPushButton(tr("download.buttons.new_task"))
        new_task_btn.setIcon(FIF.ADD)
        new_task_btn.clicked.connect(self.show_new_task_dialog)
        actions_layout.addWidget(new_task_btn)

        # Batch import button
        batch_btn = PrimaryPushButton(tr("download.buttons.batch_import"))
        batch_btn.setIcon(FIF.FOLDER_ADD)
        batch_btn.clicked.connect(self.import_batch_urls)
        actions_layout.addWidget(batch_btn)

        actions_layout.addWidget(QWidget())  # Separator

        # Start all button
        start_all_btn = PrimaryPushButton(tr("download.buttons.start_all"))
        start_all_btn.setIcon(FIF.PLAY)
        start_all_btn.clicked.connect(self.start_all_tasks)
        actions_layout.addWidget(start_all_btn)

        # Pause all button
        pause_all_btn = PrimaryPushButton(tr("download.buttons.pause_all"))
        pause_all_btn.setIcon(FIF.PAUSE)
        pause_all_btn.clicked.connect(self.pause_all_tasks)
        actions_layout.addWidget(pause_all_btn)

        # Clear completed button
        clear_btn = PrimaryPushButton(tr("download.buttons.clear_completed"))
        clear_btn.setIcon(FIF.DELETE)
        clear_btn.clicked.connect(self.clear_completed_tasks)
        actions_layout.addWidget(clear_btn)

        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)

        # Task list area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: task list
        task_container = QWidget()
        task_layout = QVBoxLayout(task_container)
        task_layout.setContentsMargins(0, 0, 0, 0)

        # Create task manager
        self.task_manager = TaskManager(self.download_manager)
        task_layout.addWidget(self.task_manager)

        # Connect signals
        if hasattr(self.task_manager, 'task_action_requested'):
            self.task_manager.task_action_requested.connect(
                self.handle_task_action)

        content_splitter.addWidget(task_container)

        # Right: task details and log panel (collapsible)
        details_panel = self._create_task_details_panel()
        content_splitter.addWidget(details_panel)

        # Set split ratios
        content_splitter.setStretchFactor(0, 3)  # Task list takes 3/4
        content_splitter.setStretchFactor(1, 1)  # Details panel takes 1/4

        main_layout.addWidget(content_splitter)

        return interface

    def _create_task_details_panel(self) -> QWidget:
        """Create task details panel with responsive design"""
        panel = QWidget()
        # Use minimum and maximum widths instead of fixed width
        panel.setMinimumWidth(250)
        panel.setMaximumWidth(400)

        # Set size policy for responsive behavior
        from PySide6.QtWidgets import QSizePolicy
        panel.setSizePolicy(QSizePolicy.Policy.Preferred,
                            QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(12)  # Reduced spacing

        # Panel title
        title = StrongBodyLabel(tr("download.task_details.title"))
        layout.addWidget(title)

        # Details card
        details_card = ElevatedCardWidget()
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(12, 12, 12, 12)  # Reduced margins
        details_layout.setSpacing(8)  # Reduced spacing

        # Task information
        info_label = BodyLabel(tr("download.task_details.select_task"))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666;")
        details_layout.addWidget(info_label)

        layout.addWidget(details_card)

        # Real-time log card
        log_card = ElevatedCardWidget()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(12, 12, 12, 12)  # Reduced margins
        log_layout.setSpacing(8)  # Reduced spacing

        log_title = StrongBodyLabel(tr("download.real_time_logs.title"))
        log_layout.addWidget(log_title)

        # Create simplified log viewer
        self.mini_log_viewer = TextEdit()
        self.mini_log_viewer.setReadOnly(True)
        self.mini_log_viewer.setMaximumHeight(200)
        self.mini_log_viewer.setPlainText(
            tr("download.real_time_logs.waiting"))
        log_layout.addWidget(self.mini_log_viewer)

        layout.addWidget(log_card)
        layout.addStretch()

        return panel

    def _create_log_interface(self) -> QWidget:
        """Create enhanced log viewing interface"""
        interface = QWidget()
        main_layout = QVBoxLayout(interface)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        # Title
        title = TitleLabel(tr("logs.title"))
        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch()

        # Log level filter
        level_combo = ComboBox()
        level_combo.addItems([
            tr("logs.levels.all"),
            tr("logs.levels.debug"),
            tr("logs.levels.info"),
            tr("logs.levels.warning"),
            tr("logs.levels.error")
        ])
        level_combo.setFixedWidth(100)
        toolbar_layout.addWidget(level_combo)

        # Clear logs button
        clear_btn = PrimaryPushButton(tr("logs.buttons.clear"))
        clear_btn.setIcon(FIF.DELETE)
        toolbar_layout.addWidget(clear_btn)

        # Export logs button
        export_btn = PrimaryPushButton(tr("logs.buttons.export"))
        export_btn.setIcon(FIF.SAVE)
        toolbar_layout.addWidget(export_btn)

        main_layout.addLayout(toolbar_layout)        # Create log viewer
        try:
            self.log_viewer = LogViewer(self)
            main_layout.addWidget(self.log_viewer)
        except Exception as e:
            # Fallback to simple text widget
            fallback_log = TextEdit()
            fallback_log.setReadOnly(True)
            fallback_log.setPlainText(tr("logs.init_failed") + f": {e}")
            main_layout.addWidget(fallback_log)

        return interface

    def _create_settings_interface(self) -> QWidget:
        """Create settings interface using the unified settings component"""
        # Create the unified settings interface
        settings_interface = SettingsInterface(self.settings, self)
        settings_interface.settings_applied.connect(
            self._apply_settings_changes)

        # Hide action buttons for embedded use
        settings_interface.hide_action_buttons()

        # Settings methods have been moved to the unified SettingsInterface component
        return settings_interface

    def _create_help_interface(self) -> QWidget:
        """Create help documentation interface"""
        try:
            help_interface = HelpInterface(self)

            # Connect help interface signals if needed
            help_interface.error_occurred.connect(self._on_help_error)

            logger.debug("Help interface created successfully")
            return help_interface

        except Exception as e:
            logger.error(f"Failed to create help interface: {e}")
            # Return a fallback widget
            fallback = QWidget()
            layout = QVBoxLayout(fallback)
            layout.setContentsMargins(24, 24, 24, 24)

            error_label = BodyLabel(tr("help.error.load_failed"))
            error_label.setStyleSheet(f"color: {DesignSystem.get_color('text_secondary_adaptive')};")
            layout.addWidget(error_label)
            layout.addStretch()

            return fallback
    # in src/gui/widgets/settings/settings_interface.py

    def _browse_output_directory(self, line_edit: LineEdit):
        """Browse for output directory"""
        from PySide6.QtWidgets import QFileDialog

        current_dir = line_edit.text() or ""
        directory = QFileDialog.getExistingDirectory(
            self, tr("dialogs.browse_directory"), current_dir
        )
        if directory:
            line_edit.setText(directory)

    def _refresh_task_list(self) -> None:
        """Refresh task list from download manager"""
        try:
            if hasattr(self, 'task_manager') and self.task_manager:
                if hasattr(self.task_manager, 'refresh_from_manager'):
                    self.task_manager.refresh_from_manager()
        except Exception as e:
            logger.error(f"Error refreshing task list: {e}")

    def _adaptive_update_interval(self) -> None:
        """Adaptive stats update interval based on task activity"""
        try:
            # Check if there are active tasks
            has_active_tasks = False
            if self.download_manager and hasattr(self.download_manager, 'tasks'):
                tasks = getattr(self.download_manager, 'tasks', {})
                active_tasks = sum(1 for task in tasks.values()
                                   if getattr(task, 'status', '') == 'downloading')
                has_active_tasks = active_tasks > 0
                self._last_active_tasks = active_tasks

            # Adaptive interval: frequent updates when active, slower when idle
            if has_active_tasks:
                interval = 2000  # 2 seconds when active
            else:
                interval = 10000  # 10 seconds when idle

            self.stats_update_timer.start(interval)
            logger.debug(
                f"Stats update interval set to {interval}ms (active tasks: {has_active_tasks})")
        except Exception as e:
            logger.error(f"Error setting adaptive update interval: {e}")
            # Fallback to default interval
            self.stats_update_timer.start(5000)

    def _update_statistics(self) -> None:
        """Update dashboard statistics with adaptive interval adjustment"""
        try:
            # Check if we need to adjust update frequency
            current_active_tasks = 0
            if self.download_manager and hasattr(self.download_manager, 'tasks'):
                tasks = getattr(self.download_manager, 'tasks', {})
                current_active_tasks = sum(1 for task in tasks.values()
                                           if getattr(task, 'status', '') == 'downloading')

            # Adjust interval if task activity changed
            if current_active_tasks != self._last_active_tasks:
                self._last_active_tasks = current_active_tasks
                self._adaptive_update_interval()

            # Update statistics
            if self.dashboard_component and hasattr(self.dashboard_component, 'update_statistics'):
                self.dashboard_component.update_statistics()
            if self.dashboard_component and hasattr(self.dashboard_component, 'update_task_preview'):
                self.dashboard_component.update_task_preview()
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")

    def _save_settings(self) -> None:
        """Save settings"""
        try:
            self.settings.save_settings()
            InfoBar.success(
                title=tr("dialogs.settings_saved"), content=tr("dialogs.settings_saved_message"),
                orient=Qt.Orientation.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=2000, parent=self
            )
        except Exception as e:
            InfoBar.error(
                title=tr("dialogs.save_failed"), content=tr("dialogs.save_failed_message", error=e),
                orient=Qt.Orientation.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self
            )

    def auto_save(self) -> None:
        """Auto save functionality"""
        if self.download_manager:
            try:
                # Auto save download tasks and settings
                self.settings.save_settings()
            except Exception as e:
                logger.error(f"Auto save failed: {e}")

    def closeEvent(self, e: QCloseEvent) -> None:
        """Handle window close event"""
        if self.app.tray_icon and self.settings.get("ui", "minimize_to_tray", False) and not self._force_close:
            e.ignore()
            self.hide()
            return

        # Check for active tasks
        active_tasks_list: List[DownloadTask] = []
        if self.download_manager and hasattr(self.download_manager, 'tasks'):
            try:
                # Safely get active tasks
                all_tasks = getattr(self.download_manager, 'tasks', [])
                active_tasks_list = [
                    t for t in all_tasks
                    if hasattr(t, 'status') and str(getattr(t, 'status', '')).lower() in ['running', 'paused']
                ]
            except Exception as ex:
                logger.error(f"Error checking active tasks: {ex}")

        if active_tasks_list and self.settings.get("ui", "confirm_on_exit", True):
            # Use a simpler message box approach
            try:
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(self, tr("dialogs.confirm_exit"),
                                             tr("dialogs.confirm_exit_message",
                                                count=len(active_tasks_list)),
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No
                                             )
                if reply == QMessageBox.StandardButton.No:
                    e.ignore()
                    return
            except ImportError:
                # Fallback if QMessageBox not available
                # Clean up
                logger.warning("Could not show exit confirmation dialog")
        # Cleanup theme listener if it exists
        if hasattr(self, 'theme_listener'):
            try:
                self.theme_listener.terminate()
                self.theme_listener.deleteLater()
                logger.info("Theme listener cleaned up")
            except Exception as ex:
                logger.error(f"Error cleaning up theme listener: {ex}")

        # Cleanup log viewer if it exists
        if hasattr(self, 'log_viewer') and self.log_viewer:
            try:
                if hasattr(self.log_viewer, 'cleanup'):
                    self.log_viewer.cleanup()
                    logger.info("Log viewer cleaned up")
            except Exception as ex:
                logger.error(f"Error cleaning up log viewer: {ex}")

        if self.download_manager and active_tasks_list:
            try:
                # Stop all tasks before closing
                for task in active_tasks_list:
                    task_id = getattr(
                        task, 'id', getattr(task, 'task_id', None))
                    if task_id and hasattr(self.download_manager, 'pause_task'):
                        self.download_manager.pause_task(task_id)
            except Exception as ex:
                logger.error(f"Error stopping tasks on exit: {ex}")

        # Clean up singleton components
        try:
            if hasattr(self.app, 'cleanup_singleton_components'):
                self.app.cleanup_singleton_components()
                logger.debug("Singleton components cleaned up on exit")
        except Exception as ex:
            logger.error(f"Error cleaning up singleton components: {ex}")

        self.settings.save_settings()
        e.accept()

    # Slot methods

    @Slot()
    def show_new_task_dialog(self) -> None:
        """Show new task dialog"""
        try:
            dialog = TaskDialog(self.settings, self)
            if dialog.exec() == TaskDialog.DialogCode.Accepted:
                # Get task data from dialog
                task_data = dialog.get_task_data()

                # Validate task data
                if not task_data.get("base_url") or not task_data.get("output_file"):
                    InfoBar.warning(
                        title=tr("dialogs.task_error"),
                        content=tr("dialogs.validation_error",
                                   message="Base URL and output file are required"),
                        orient=Qt.Orientation.Horizontal, isClosable=True,
                        position=InfoBarPosition.TOP, duration=3000, parent=self
                    )
                    return

                # Create download task
                from src.core.downloader import DownloadTask, TaskPriority

                # Map priority string to enum
                priority_map = {
                    "high": TaskPriority.HIGH,
                    "normal": TaskPriority.NORMAL,
                    "low": TaskPriority.LOW
                }
                priority = priority_map.get(task_data.get(
                    "priority", "normal"), TaskPriority.NORMAL)

                task = DownloadTask(
                    name=task_data.get("name") or "Download Task",
                    base_url=task_data.get("base_url"),
                    key_url=task_data.get("key_url"),
                    segments=task_data.get("segments", 200),
                    output_file=task_data.get("output_file"),
                    settings=self.settings,
                    priority=priority
                )

                # Add task to download manager
                if self.download_manager:
                    task_id = self.download_manager.add_task(task)

                    # Auto-start if requested
                    if task_data.get("auto_start", False):
                        self.download_manager.start_task(task_id)

                    # Show success message
                    InfoBar.success(
                        title=tr("dialogs.task_created"),
                        content=tr("dialogs.task_created_message",
                                   name=task.name),
                        orient=Qt.Orientation.Horizontal, isClosable=True,
                        position=InfoBarPosition.TOP, duration=3000, parent=self
                    )

                    # Update task manager display
                    if hasattr(self, 'task_manager') and self.task_manager:
                        self.task_manager.refresh_from_manager()
                else:
                    InfoBar.error(
                        title=tr("dialogs.task_error"),
                        content=tr("dialogs.download_manager_error"),
                        orient=Qt.Orientation.Horizontal, isClosable=True,
                        position=InfoBarPosition.TOP, duration=3000, parent=self
                    )

        except Exception as e:
            logger.error(f"Error creating new task: {e}")
            InfoBar.error(
                title=tr("dialogs.task_error"),
                content=tr("dialogs.task_error_message", error=str(e)),
                orient=Qt.Orientation.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self
            )

    @Slot()
    def import_from_url(self) -> None:
        """Import from URL"""
        # Implementation would handle URL import
        pass

    @Slot()
    def import_batch_urls(self) -> None:
        """Import batch URLs"""
        try:
            dialog = BatchURLDialog(self)
            dialog.exec()
        except Exception as e:
            InfoBar.error(
                title=tr("dialogs.batch_import_error"), content=tr("dialogs.batch_import_error_message", error=e),
                orient=Qt.Orientation.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self
            )

    @Slot()
    def show_settings(self) -> None:
        """Show unified settings dialog"""
        try:
            # Use the new unified settings dialog
            dialog = SettingsDialog(self.settings, self)
            dialog.settings_applied.connect(self._apply_settings_changes)
            dialog.exec()

        except Exception as e:
            logger.error(f"Error opening settings dialog: {e}", exc_info=True)
            InfoBar.error(
                title=tr("dialogs.settings_error"), content=tr("dialogs.settings_error_message", error=e),
                orient=Qt.Orientation.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self
            )

    @Slot()
    def show_about(self) -> None:
        """Show about dialog"""
        try:
            dialog = AboutDialog(self)
            dialog.exec()
        except Exception as e:
            InfoBar.error(
                title=tr("dialogs.about_error"), content=tr("dialogs.about_error_message", error=e),
                orient=Qt.Orientation.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self
            )

    @Slot()
    def show_media_processing(self) -> None:
        """Show media processing dialog"""
        InfoBar.info(
            title=tr("dialogs.media_processing"), content=tr("dialogs.media_processing_message"),
            orient=Qt.Orientation.Horizontal, isClosable=True,
            position=InfoBarPosition.TOP, duration=2000, parent=self
        )

    @Slot()
    def show_batch_conversion(self) -> None:
        """Show batch conversion dialog"""
        InfoBar.info(
            title=tr("dialogs.batch_convert"), content=tr("dialogs.batch_convert_message"),
            orient=Qt.Orientation.Horizontal, isClosable=True,
            position=InfoBarPosition.TOP, duration=2000, parent=self
        )

    def handle_task_action(self, action: str, task_id: str) -> None:
        """Handle task actions"""
        def _wrap_none(func):
            try:
                return func(task_id)
            except Exception as e:
                logger.error(f"Task action {action} failed for {task_id}: {e}")
                return None

        if not self.download_manager:
            return

        action_map: Dict[str, Callable[[str], None]] = {
            "start": lambda tid: getattr(self.download_manager, 'start_task', lambda _: None)(tid),
            "pause": lambda tid: getattr(self.download_manager, 'pause_task', lambda _: None)(tid),
            "resume": lambda tid: getattr(self.download_manager, 'resume_task', lambda _: None)(tid),
            "cancel": lambda tid: getattr(self.download_manager, 'cancel_task', lambda _: None)(tid),
            "remove": lambda tid: getattr(self.download_manager, 'remove_task', lambda _: None)(tid),
        }

        action_func = action_map.get(action)
        if action_func:
            _wrap_none(action_func)

        self._update_ui()

    def start_all_tasks(self) -> None:
        """Start all tasks"""
        if self.download_manager:
            try:
                # Start tasks individually - checking if methods exist first
                if hasattr(self.download_manager, 'tasks'):
                    tasks = getattr(self.download_manager, 'tasks', {})
                    if isinstance(tasks, dict):
                        # If tasks is a dict (task_id -> task)
                        for task_id, task in tasks.items():
                            if hasattr(self.download_manager, 'start_task') and hasattr(task, 'status'):
                                if str(getattr(task, 'status', '')).lower() in ['pending', 'paused']:
                                    self.download_manager.start_task(task_id)
                    elif hasattr(tasks, '__iter__'):
                        # If tasks is a list/iterable
                        for task in tasks:
                            task_id = getattr(
                                task, 'id', getattr(task, 'task_id', None))
                            if task_id and hasattr(self.download_manager, 'start_task'):
                                if str(getattr(task, 'status', '')).lower() in ['pending', 'paused']:
                                    self.download_manager.start_task(task_id)
            except Exception as e:
                logger.error(f"Error starting all tasks: {e}")
        self._update_ui()

    def pause_all_tasks(self) -> None:
        """Pause all tasks"""
        if self.download_manager:
            try:
                # Pause tasks individually - checking if methods exist first
                if hasattr(self.download_manager, 'tasks'):
                    tasks = getattr(self.download_manager, 'tasks', {})
                    if isinstance(tasks, dict):
                        # If tasks is a dict (task_id -> task)
                        for task_id, task in tasks.items():
                            if hasattr(self.download_manager, 'pause_task') and hasattr(task, 'status'):
                                if str(getattr(task, 'status', '')).lower() == 'running':
                                    self.download_manager.pause_task(task_id)
                    elif hasattr(tasks, '__iter__'):
                        # If tasks is a list/iterable
                        for task in tasks:
                            task_id = getattr(
                                task, 'id', getattr(task, 'task_id', None))
                            if task_id and hasattr(self.download_manager, 'pause_task'):
                                if str(getattr(task, 'status', '')).lower() == 'running':
                                    self.download_manager.pause_task(task_id)
            except Exception as e:
                logger.error(f"Error pausing all tasks: {e}")
        self._update_ui()

    def clear_completed_tasks(self) -> None:
        """Clear completed tasks"""
        if self.download_manager:
            try:
                # Remove completed tasks individually - checking if methods exist first
                if hasattr(self.download_manager, 'tasks'):
                    tasks = getattr(self.download_manager, 'tasks', {})
                    completed_task_ids = []

                    if isinstance(tasks, dict):
                        # If tasks is a dict (task_id -> task)
                        for task_id, task in tasks.items():
                            if hasattr(task, 'status'):
                                if str(getattr(task, 'status', '')).lower() == 'completed':
                                    completed_task_ids.append(task_id)
                    elif hasattr(tasks, '__iter__'):
                        # If tasks is a list/iterable
                        for task in tasks:
                            task_id = getattr(
                                task, 'id', getattr(task, 'task_id', None))
                            if task_id and hasattr(task, 'status'):
                                if str(getattr(task, 'status', '')).lower() == 'completed':
                                    completed_task_ids.append(task_id)

                    # Remove completed tasks
                    for task_id in completed_task_ids:
                        if hasattr(self.download_manager, 'remove_task'):
                            self.download_manager.remove_task(task_id)
            except Exception as e:
                logger.error(f"Error clearing completed tasks: {e}")
        self._update_ui()

    # Event handlers
    def on_task_progress(self, task_id: str, progress_data: "ProgressDict") -> None:
        """Handle task progress updates with better error handling and speed calculation"""
        try:
            if hasattr(self, 'task_manager') and self.task_manager:
                # Convert ProgressDict to standard dict for UI compatibility
                progress_dict: dict = dict(progress_data)

                # Calculate actual progress percentage
                if 'completed' in progress_dict and 'total' in progress_dict:
                    total = progress_dict.get('total', 1)
                    completed = progress_dict.get('completed', 0)
                    if total > 0:
                        progress_dict['progress'] = (completed / total) * 100
                    else:
                        progress_dict['progress'] = 0

                # Format speed for display
                if 'speed' in progress_dict and isinstance(progress_dict['speed'], (int, float)):
                    speed = progress_dict['speed']
                    if speed > 0:
                        progress_dict['speed_formatted'] = format_speed(speed)
                    else:
                        progress_dict['speed_formatted'] = "0 B/s"

                # Update the task manager
                if hasattr(self.task_manager, 'update_task_progress'):
                    self.task_manager.update_task_progress(
                        task_id, progress_dict)

                # Update dashboard if available
                if self.dashboard_component and hasattr(self.dashboard_component, 'update_statistics'):
                    self.dashboard_component.update_statistics()

        except Exception as e:
            logger.error(f"Error updating task progress for {task_id}: {e}")

    def on_task_status_changed(self, task_id: str, old_status: Optional[CoreTaskStatus], new_status: CoreTaskStatus) -> None:
        """Handle task status changes"""
        self._update_ui()

    def on_task_completed(self, task_id: str, message: str) -> None:
        """Handle task completion"""
        if self.settings.get("ui", "show_notifications", True):
            self.app.send_notification("任务完成", message, FIF.COMPLETED)

        if self.mini_log_viewer:
            self.mini_log_viewer.append(f"任务完成: {message}")

    def on_task_failed(self, task_id: str, message: str) -> None:
        """Handle task failure"""
        if self.settings.get("ui", "show_notifications", True):
            self.app.send_notification("任务失败", message, FIF.CANCEL)

        if self.mini_log_viewer:
            self.mini_log_viewer.append(f"任务失败: {message}")

    def _connect_signals(self) -> None:
        """Connect all signals and slots"""
        # Connect task manager signals
        if hasattr(self, 'task_manager') and self.task_manager:
            if hasattr(self.task_manager, 'task_action_requested'):
                self.task_manager.task_action_requested.connect(
                    self.handle_task_action)

        # Connect download manager signals
        if self.download_manager:
            # Signals would be connected here if available
            pass

    def _setup_auto_save(self) -> None:
        """Setup auto save functionality"""
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(
            self.auto_save)        # Auto save every 5 minutes
        auto_save_interval = self.settings.get(
            "ui", "auto_save_interval", 300) * 1000
        self.auto_save_timer.start(auto_save_interval)

    def _update_ui(self) -> None:
        """Update UI state"""
        try:
            # Update dashboard if available
            if self.dashboard_component:
                self.dashboard_component.update_statistics()
                self.dashboard_component.update_task_preview()

        except Exception as e:
            logger.error(f"Error updating UI: {e}")

    def _apply_settings_changes(self) -> None:
        """Apply any settings changes that require immediate effect"""
        try:
            # Apply theme changes
            theme = self.settings.get("general", "theme", "system")
            self.app._apply_theme()

            # Save settings to disk
            self.settings.save_settings()

            # Show success message
            InfoBar.success(
                title="设置已保存", content="设置已成功保存并应用",
                orient=Qt.Orientation.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=2000, parent=self
            )

            logger.info("Settings changes applied successfully")

        except Exception as e:
            logger.error(
                f"Error applying settings changes: {e}", exc_info=True)
            InfoBar.error(
                title="应用设置失败", content=f"无法应用设置更改: {e}",
                orient=Qt.Orientation.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self
            )

    def _setup_theme_system(self) -> None:
        """Setup automatic theme switching system"""
        try:


            # Create theme listener if system theme mode is selected
            theme_mode = self.settings.get("general", "theme", "system")

            if theme_mode == "system":
                self.theme_listener = SystemThemeListener(self)
                self.theme_listener.start()
            else:
                # Apply the selected theme
                if theme_mode == "light":
                    setTheme(Theme.LIGHT)
                elif theme_mode == "dark":
                    setTheme(Theme.DARK)

            logger.info(
                f"Theme system setup completed with mode: {theme_mode}")

        except Exception as e:
            logger.error(f"Error setting up theme system: {e}", exc_info=True)
            # Fallback to default theme
            try:

                setTheme(Theme.AUTO)
            except:
                pass

    def show_log_viewer(self) -> None:
        """Switch to the log interface"""
        try:
            self.switchTo(self.log_interface)
        except Exception as e:
            logger.error(f"Error switching to log interface: {e}")

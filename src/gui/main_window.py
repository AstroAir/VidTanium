import logging
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenu, QStatusBar,
    QLabel, QSplitter, QFileDialog, QApplication
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, Slot
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QColor, QPainter

from qfluentwidgets import (
    MessageBox, Action, RoundMenu,
    FluentIcon, InfoBar, InfoBarPosition
)

from .widgets.task_manager import TaskManager
from .widgets.log_viewer import LogViewer
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.task_dialog import TaskDialog
from .dialogs.about_dialog import AboutDialog

logger = logging.getLogger(__name__)


class StatusInfoWidget(QWidget):
    """
    Status information widget for status bar
    Shows an icon and a status text
    """

    def __init__(self, icon, text, parent=None):
        """
        Initialize the status info widget

        Args:
            icon: FluentIcon or QIcon to display
            text: Status text to display
            parent: Parent widget
        """
        super().__init__(parent)

        self.icon = icon
        self.text = text
        self.icon_color = None

        self._create_ui()

    def _create_ui(self):
        """Create user interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(4)

        # Create icon label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        layout.addWidget(self.icon_label)

        # Create text label
        self.text_label = QLabel(self.text)
        layout.addWidget(self.text_label)

        # Update icon
        self._update_icon()

    def setContent(self, icon, text):
        """
        Update widget content

        Args:
            icon: FluentIcon or QIcon to display
            text: Status text to display
        """
        self.icon = icon
        self.text = text

        self.text_label.setText(text)
        self._update_icon()

    def setIconColor(self, color):
        """
        Set the icon color

        Args:
            color: QColor to apply to icon
        """
        self.icon_color = color
        self._update_icon()

    def _update_icon(self):
        """Update the icon with current settings"""
        if isinstance(self.icon, FluentIcon):
            pixmap = self._create_colored_pixmap(self.icon, self.icon_color)
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setPixmap(self.icon.pixmap(16, 16))

    def _create_colored_pixmap(self, fluent_icon, color=None):
        """
        Create a colored pixmap from a FluentIcon

        Args:
            fluent_icon: FluentIcon to convert
            color: Optional QColor to apply (if None, uses original color)

        Returns:
            QPixmap: The colored icon
        """
        # Get base pixmap
        pixmap = fluent_icon.icon().pixmap(16, 16)

        # If no color specified, return original
        if color is None:
            return pixmap

        # Create colored version
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.transparent)

        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Use QPainter's composition mode to apply color
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.drawPixmap(0, 0, pixmap)

        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), color)

        painter.end()
        return colored_pixmap


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, app, download_manager, settings):
        super().__init__()

        self.app = app
        self.download_manager = download_manager
        self.settings = settings

        self._force_close = False

        # Set download manager callbacks
        self.download_manager.on_task_progress = self.on_task_progress
        self.download_manager.on_task_status_changed = self.on_task_status_changed
        self.download_manager.on_task_completed = self.on_task_completed
        self.download_manager.on_task_failed = self.on_task_failed

        # Set window properties
        self.setWindowTitle("Encrypted Video Downloader")
        self.setMinimumSize(1000, 700)

        # Create interface
        self._create_ui()
        self._create_menu()
        self._create_statusbar()

        # Connect signals
        self._connect_signals()

        # Initialize auto-save timer
        self._setup_auto_save()

        # Update UI
        self._update_ui()

        logger.info("Main window initialized")

    def _create_ui(self):
        """Create main window interface"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)  # Reduce margins
        main_layout.setSpacing(4)  # Reduce spacing for more compact layout

        # Create splitter
        self.main_splitter = QSplitter(Qt.Vertical)
        # Increase splitter handle width for easier dragging
        self.main_splitter.setHandleWidth(8)
        # Prevent child widgets from completely collapsing
        self.main_splitter.setChildrenCollapsible(False)

        # Download panel
        self.task_manager = TaskManager(self.settings)
        self.main_splitter.addWidget(self.task_manager)

        # Log viewer
        self.log_viewer = LogViewer()
        self.main_splitter.addWidget(self.log_viewer)

        # Set split ratio (70% tasks, 30% logs)
        self.main_splitter.setSizes(
            [int(self.height() * 0.7), int(self.height() * 0.3)])

        # Add to main layout
        main_layout.addWidget(self.main_splitter)

        # Connect task manager signals
        self.task_manager.task_action_requested.connect(
            self.handle_task_action)

        # Window state restoration
        geometry = self.settings.get("ui", "window_geometry", None)
        state = self.settings.get("ui", "window_state", None)

        if geometry:
            try:
                from PySide6.QtCore import QByteArray
                self.restoreGeometry(QByteArray.fromBase64(geometry.encode()))
            except Exception:
                pass

        if state:
            try:
                from PySide6.QtCore import QByteArray
                self.restoreState(QByteArray.fromBase64(state.encode()))
            except Exception:
                pass

    def _create_menu(self):
        """Create menu bar with Fluent design"""
        # File menu
        file_menu = self.menuBar().addMenu("File(&F)")

        new_task_action = Action(FluentIcon.ADD, "New Task(&N)", self)
        new_task_action.setShortcut(QKeySequence.New)
        new_task_action.triggered.connect(self.show_new_task_dialog)
        file_menu.addAction(new_task_action)

        import_url_action = Action(
            FluentIcon.LINK, "Import from URL(&I)", self)
        import_url_action.setShortcut("Ctrl+I")
        import_url_action.triggered.connect(self.import_from_url)
        file_menu.addAction(import_url_action)

        file_menu.addSeparator()

        settings_action = Action(FluentIcon.SETTING, "Settings(&S)", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        import_menu = RoundMenu("Import", self)

        import_url_submenu_action = Action(
            FluentIcon.LINK, "Import from URL", self)
        import_url_submenu_action.setShortcut("Ctrl+I")
        import_url_submenu_action.triggered.connect(self.import_from_url)
        import_menu.addAction(import_url_submenu_action)

        import_batch_action = Action(
            FluentIcon.FOLDER_ADD, "Batch Import URLs", self)
        import_batch_action.setShortcut("Ctrl+B")
        import_batch_action.triggered.connect(self.import_batch_urls)
        import_menu.addAction(import_batch_action)

        file_menu.addMenu(import_menu)

        file_menu.addSeparator()

        exit_action = Action(FluentIcon.CLOSE, "Exit(&Q)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Media menu
        media_menu = self.menuBar().addMenu("Media(&M)")

        process_media_action = Action(
            FluentIcon.EDIT, "Process Media Files(&P)", self)
        process_media_action.setShortcut("Ctrl+P")
        process_media_action.triggered.connect(self.show_media_processing)
        media_menu.addAction(process_media_action)

        media_menu.addSeparator()

        batch_convert_action = Action(
            FluentIcon.TILES, "Batch Convert(&B)", self)
        batch_convert_action.triggered.connect(self.show_batch_conversion)
        media_menu.addAction(batch_convert_action)

        # Task menu
        task_menu = self.menuBar().addMenu("Tasks(&T)")

        start_all_action = Action(FluentIcon.PLAY, "Start All(&S)", self)
        start_all_action.triggered.connect(self.start_all_tasks)
        task_menu.addAction(start_all_action)

        pause_all_action = Action(FluentIcon.PAUSE, "Pause All(&P)", self)
        pause_all_action.triggered.connect(self.pause_all_tasks)
        task_menu.addAction(pause_all_action)

        task_menu.addSeparator()

        clear_completed_action = Action(
            FluentIcon.DELETE, "Clear Completed Tasks(&C)", self)
        clear_completed_action.triggered.connect(self.clear_completed_tasks)
        task_menu.addAction(clear_completed_action)

        # Help menu
        help_menu = self.menuBar().addMenu("Help(&H)")

        about_action = Action(FluentIcon.INFO, "About(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_statusbar(self):
        """Create status bar with Fluent design"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Create status frame
        from PySide6.QtWidgets import QFrame

        # Create task status panel
        task_frame = QFrame()
        task_layout = QHBoxLayout(task_frame)
        task_layout.setContentsMargins(2, 0, 2, 0)
        task_layout.setSpacing(10)

        # Status indicator
        self.status_info_widget = StatusInfoWidget(
            FluentIcon.DATE_TIME, "Ready", self)
        task_layout.addWidget(self.status_info_widget)

        # Add to status bar
        self.status_bar.addWidget(task_frame)

        # Add separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setFixedWidth(1)
        separator1.setFixedHeight(16)
        self.status_bar.addWidget(separator1)

        # Active tasks info
        self.active_tasks_label = QLabel("Active Tasks: 0/0")
        self.status_bar.addWidget(self.active_tasks_label)

        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setFixedWidth(1)
        separator2.setFixedHeight(16)
        self.status_bar.addWidget(separator2)

        # CPU usage
        self.cpu_usage_label = QLabel("CPU: 0%")
        self.status_bar.addWidget(self.cpu_usage_label)

        # Memory usage
        self.memory_usage_label = QLabel("Memory: 0MB")
        self.status_bar.addWidget(self.memory_usage_label)

        # Add spring
        self.status_bar.addPermanentWidget(QFrame(), 1)  # Spring

        # Total download speed panel
        speed_frame = QFrame()
        speed_layout = QHBoxLayout(speed_frame)
        speed_layout.setContentsMargins(6, 0, 6, 0)
        speed_layout.setSpacing(6)

        # Speed icon
        speed_icon = QLabel()
        speed_icon.setPixmap(FluentIcon.DOWNLOAD.icon().pixmap(16, 16))
        speed_layout.addWidget(speed_icon)

        # Speed label
        self.speed_label = QLabel("0 B/s")
        self.speed_label.setStyleSheet("font-weight: bold;")
        speed_layout.addWidget(self.speed_label)

        # Add to status bar
        self.status_bar.addPermanentWidget(speed_frame)

        # Set timer to update CPU and memory usage
        self.system_info_timer = QTimer(self)
        self.system_info_timer.timeout.connect(self._update_system_info)
        self.system_info_timer.start(5000)  # Update every 5 seconds

    def _update_system_info(self):
        """Update system information display"""
        try:
            import psutil

            # Update CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage_label.setText(f"CPU: {cpu_percent:.1f}%")

            # Update memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.memory_usage_label.setText(f"Memory: {memory_mb:.1f}MB")

        except ImportError:
            # Hide these labels if psutil is not available
            self.cpu_usage_label.hide()
            self.memory_usage_label.hide()
        except Exception:
            # Hide these labels if error occurs
            self.cpu_usage_label.hide()
            self.memory_usage_label.hide()

    def _connect_signals(self):
        """Connect signals and slots"""
        # Task manager signals
        pass

    def _setup_auto_save(self):
        """Set up auto-save timer"""
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(60000)  # Save every minute

    def _update_ui(self):
        """Update UI state"""
        # Update task list
        self.task_manager.update_tasks(self.download_manager.tasks)

        # Update status bar
        active_count = len(self.download_manager.active_tasks)
        total_count = len(self.download_manager.tasks)

        # Update active tasks label
        self.active_tasks_label.setText(
            f"Active Tasks: {active_count}/{total_count}")

        # Update status indicator
        if active_count > 0:
            # Blue when there are active tasks
            self.status_info_widget.setContent(
                FluentIcon.DOWNLOAD, "Downloading")
        elif total_count > 0:
            # Yellow when there are tasks but none active
            self.status_info_widget.setContent(FluentIcon.PAUSE, "Paused")
        else:
            # Green when no tasks
            self.status_info_widget.setContent(FluentIcon.DATE_TIME, "Ready")

    def auto_save(self):
        """Auto save state"""
        # Save all task progress
        for task in self.download_manager.tasks.values():
            task.save_progress()

    def closeEvent(self, event):
        """Window close event handler"""
        if self.app.tray_icon and self.settings.get("ui", "minimize_to_tray", False) and not self._force_close:
            event.ignore()
            self.hide()

            # Show notification
            if self.settings.get("ui", "show_notifications", True):
                self.app.tray_icon.show_notification(
                    "Encrypted Video Downloader",
                    "Application minimized to system tray. Click icon to restore."
                )
            return

        # Check if there are active tasks
        active_tasks = []
        for task in self.download_manager.tasks.values():
            if task.status in [task.status.RUNNING, task.status.PAUSED]:
                active_tasks.append(task)

        if active_tasks and self.settings.get("ui", "confirm_on_exit", True):
            result = MessageBox(
                "Confirm Exit",
                f"There are still {len(active_tasks)} tasks in progress. Are you sure you want to exit?\n(Tasks will be paused and progress saved)",
                self
            ).exec()

            if not result:
                event.ignore()
                return

        # Stop download manager
        self.download_manager.stop()

        # Save window state
        self.settings.set("ui", "window_geometry",
                          self.saveGeometry().toBase64().data().decode())
        self.settings.set("ui", "window_state",
                          self.saveState().toBase64().data().decode())
        self.settings.save_settings()

        # Continue closing window
        event.accept()

    @Slot()
    def show_new_task_dialog(self):
        """Show new task dialog"""
        dialog = TaskDialog(self.settings, parent=self)

        if dialog.exec():
            # Get task parameters
            task_data = dialog.get_task_data()

            # Create download task
            from src.core.downloader import DownloadTask, TaskPriority

            priority_map = {
                "high": TaskPriority.HIGH,
                "normal": TaskPriority.NORMAL,
                "low": TaskPriority.LOW
            }

            task = DownloadTask(
                name=task_data["name"],
                base_url=task_data["base_url"],
                key_url=task_data["key_url"],
                segments=task_data["segments"],
                output_file=task_data["output_file"],
                settings=self.settings,
                priority=priority_map.get(
                    task_data["priority"], TaskPriority.NORMAL)
            )

            # Add to download manager
            self.download_manager.add_task(task)

            # Start task immediately if auto-start is set
            if task_data["auto_start"]:
                self.download_manager.start_task(task.task_id)

            # Update UI
            self._update_ui()

    @Slot()
    def import_from_url(self):
        """Import task from URL"""
        # Simplified handling, actual implementation should parse URL to extract M3U8 and key information
        # URL can be recognized after selection or manually entered
        InfoBar.info(
            title="Information",
            content="This feature is not yet implemented",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    @Slot()
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.settings, parent=self)

        if dialog.exec():
            # Settings updated, refresh UI
            self._update_ui()

    @Slot()
    def show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(parent=self)
        dialog.exec()

    @Slot(str, str)
    def handle_task_action(self, task_id, action):
        """Handle task actions"""
        if action == "start":
            self.download_manager.start_task(task_id)
        elif action == "pause":
            self.download_manager.pause_task(task_id)
        elif action == "resume":
            self.download_manager.resume_task(task_id)
        elif action == "cancel":
            self.download_manager.cancel_task(task_id)
        elif action == "remove":
            self.download_manager.remove_task(task_id)
        elif action == "remove_with_file":
            self.download_manager.remove_task(task_id, delete_files=True)

        # Update UI
        self._update_ui()

    @Slot()
    def start_all_tasks(self):
        """Start all pending tasks"""
        for task_id, task in self.download_manager.tasks.items():
            if task.status in [task.status.PENDING, task.status.PAUSED]:
                self.download_manager.start_task(task_id)

        # Update UI
        self._update_ui()

    @Slot()
    def pause_all_tasks(self):
        """Pause all running tasks"""
        for task_id, task in self.download_manager.tasks.items():
            if task.status == task.status.RUNNING:
                self.download_manager.pause_task(task_id)

        # Update UI
        self._update_ui()

    @Slot()
    def clear_completed_tasks(self):
        """Clear all completed tasks"""
        task_ids = list(self.download_manager.tasks.keys())

        for task_id in task_ids:
            task = self.download_manager.tasks.get(task_id)
            if task and task.status in [task.status.COMPLETED, task.status.FAILED, task.status.CANCELED]:
                self.download_manager.remove_task(task_id)

        # Update UI
        self._update_ui()

    @Slot(str, dict)
    def on_task_progress(self, task_id, progress):
        """Handle task progress updates"""
        # Update task manager UI
        self.task_manager.update_task_progress(task_id, progress)

        # Update status bar
        total_speed = sum(task.progress.get("speed", 0) for task in self.download_manager.tasks.values(
        ) if task.status == task.status.RUNNING)
        self.speed_label.setText(self._format_speed(total_speed))

    @Slot(str, object, object)
    def on_task_status_changed(self, task_id, old_status, new_status):
        """Handle task status changes"""
        # Update task manager UI
        self.task_manager.update_task_status(task_id, new_status)

        # Update status bar
        active_count = len(self.download_manager.active_tasks)
        total_count = len(self.download_manager.tasks)
        self.active_tasks_label.setText(
            f"Active Tasks: {active_count}/{total_count}")

        # Send system notifications
        if self.settings.get("ui", "show_notifications", True):
            task = self.download_manager.get_task(task_id)
            if task:
                if new_status == task.status.RUNNING and old_status != task.status.PAUSED:
                    self.app.send_notification(
                        "Task Started", f"Task \"{task.name}\" has started downloading")
                elif new_status == task.status.PAUSED:
                    self.app.send_notification(
                        "Task Paused", f"Task \"{task.name}\" has been paused")
                elif new_status == task.status.COMPLETED:
                    self.app.send_notification(
                        "Task Completed", f"Task \"{task.name}\" has completed successfully")
                elif new_status == task.status.FAILED:
                    self.app.send_notification(
                        "Task Failed", f"Task \"{task.name}\" has failed")
                elif new_status == task.status.CANCELED:
                    self.app.send_notification(
                        "Task Canceled", f"Task \"{task.name}\" has been canceled")

    @Slot(str, str)
    def on_task_completed(self, task_id, message):
        """Handle task completion"""
        # Log message
        logger.info(f"Task completed: {message}")
        self.log_viewer.add_log_entry(f"Task completed: {message}")

        # Update UI
        self._update_ui()

    @Slot(str, str)
    def on_task_failed(self, task_id, message):
        """Handle task failure"""
        # Log message
        logger.error(f"Task failed: {message}")
        self.log_viewer.add_log_entry(f"Task failed: {message}", error=True)

        # Update UI
        self._update_ui()

    def _format_speed(self, bytes_per_second):
        """Format speed display"""
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.1f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024):.2f} MB/s"

    @Slot()
    def import_batch_urls(self):
        """Batch import URLs"""
        from src.gui.dialogs.batch_url_dialog import BatchURLDialog

        dialog = BatchURLDialog(self.settings, parent=self)
        dialog.urls_imported.connect(self._handle_batch_urls)

        dialog.exec()

    @Slot(list)
    def _handle_batch_urls(self, urls):
        """Handle batch imported URLs"""
        if not urls:
            return

        # Ask whether to automatically parse
        result = MessageBox(
            "URL Processing",
            f"Imported {len(urls)} URLs. Would you like to try auto-parsing them into download tasks?",
            self
        ).exec()

        if result:
            # Show progress dialog
            from PySide6.QtWidgets import QProgressDialog
            progress = QProgressDialog(
                "Parsing URLs...", "Cancel", 0, len(urls), self)
            progress.setWindowTitle("Parsing")
            progress.setMinimumDuration(0)
            progress.setModal(True)
            progress.show()

            # Parse URLs and create tasks
            successful = 0
            for i, url in enumerate(urls):
                progress.setValue(i)
                progress.setLabelText(f"Parsing URL {i+1}/{len(urls)}")

                if progress.wasCanceled():
                    break

                try:
                    # Try to parse URL
                    from src.core.m3u8_parser import extract_m3u8_info

                    # Get user agent setting
                    user_agent = self.settings.get(
                        "advanced", "user_agent", "")
                    headers = {
                        "User-Agent": user_agent} if user_agent else None

                    # Extract information
                    result = extract_m3u8_info(url, headers)

                    if result["success"]:
                        # Create download task
                        from src.core.downloader import DownloadTask, TaskPriority

                        # Generate task name
                        from urllib.parse import urlparse
                        from os.path import basename, join

                        parsed_url = urlparse(url)
                        path = parsed_url.path
                        name = basename(path)
                        if name:
                            name = name.split(".")[0]  # Remove extension
                        else:
                            name = f"Task-{i+1}"

                        # Generate output filename
                        output_dir = self.settings.get(
                            "general", "output_directory", "")
                        output_file = join(output_dir, f"{name}.mp4")

                        # Create task
                        task = DownloadTask(
                            name=name,
                            base_url=result["base_url"],
                            key_url=result["key_url"],
                            segments=result["segments"],
                            output_file=output_file,
                            settings=self.settings,
                            priority=TaskPriority.NORMAL
                        )

                        # Add to download manager
                        self.download_manager.add_task(task)

                        # Auto-start task
                        self.download_manager.start_task(task.task_id)

                        successful += 1

                except Exception as e:
                    logger.error(f"Error parsing URL: {url}, error: {e}")
                    continue

            progress.setValue(len(urls))

            # Update UI
            self._update_ui()

            # Show result
            InfoBar.success(
                title="Import Results",
                content=f"Successfully imported {successful} tasks, failed {len(urls) - successful}.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

        else:
            # Copy URLs to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(urls))

            InfoBar.info(
                title="URLs Copied",
                content=f"{len(urls)} URLs copied to clipboard.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    @Slot()
    def show_media_processing(self):
        """Show media processing dialog"""
        from src.gui.dialogs.media_processing_dialog import MediaProcessingDialog

        # Get selected task
        selected_file = None
        selected_rows = self.task_manager.get_selected_rows()
        if selected_rows:
            task_id = selected_rows[0]
            task = self.download_manager.get_task(task_id)
            if task and task.status == task.status.COMPLETED and task.output_file:
                selected_file = task.output_file

        # Create and show dialog
        dialog = MediaProcessingDialog(
            self.settings, selected_file, parent=self)
        dialog.processing_completed.connect(
            self._on_media_processing_completed)

        dialog.exec()

    @Slot()
    def show_batch_conversion(self):
        """Show batch conversion dialog"""
        from src.gui.dialogs.batch_conversion_dialog import BatchConversionDialog

        dialog = BatchConversionDialog(self.settings, parent=self)
        dialog.processing_completed.connect(self._on_batch_conversion_completed)
        dialog.exec()

    @Slot(bool, str)
    def _on_batch_conversion_completed(self, success, message):
        """Batch conversion completion callback"""
        if success:
            self.log_viewer.add_log_entry(message)
            
            # Send notification
            if self.settings.get("ui", "show_notifications", True):
                self.app.send_notification("Batch Conversion", "Media batch conversion completed")
        else:
            self.log_viewer.add_log_entry(message, error=True)

    @Slot(bool, str)
    def _on_media_processing_completed(self, success, message):
        """Media processing completion callback"""
        if success:
            self.log_viewer.add_log_entry(message)

            # Send notification
            if self.settings.get("ui", "show_notifications", True):
                self.app.send_notification(
                    "Media Processing", "Media processing completed")
        else:
            self.log_viewer.add_log_entry(message, error=True)

import logging
# import os # Unused
from typing import Any, Dict, List, Optional, Union
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar,
    QLabel, QSplitter, QApplication, QFrame,
    QProgressDialog
)
from PySide6.QtCore import Qt, QTimer, Slot, QByteArray
from PySide6.QtGui import (
    QKeySequence, QPixmap, QColor, QPainter, QCloseEvent
)
from urllib.parse import urlparse, ParseResult
from os.path import basename, join


# Assuming qfluentwidgets components are individually typed,
# but if the package itself lacks stubs, a '# type: ignore' might be needed on this line
# depending on your type checker's behavior regarding the "找不到 Stub 文件" error.
from qfluentwidgets import (
    MessageBox, Action, RoundMenu,
    FluentIcon, InfoBar, InfoBarPosition
)

from .widgets.task_manager import TaskManager
from .widgets.log_viewer import LogViewer
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.task_dialog import TaskDialog
from .dialogs.about_dialog import AboutDialog
from .dialogs.batch_url_dialog import BatchURLDialog
from .dialogs.media_processing_dialog import MediaProcessingDialog
from .dialogs.batch_conversion_dialog import BatchConversionDialog
from src.core.downloader import DownloadTask, TaskPriority # Assuming DownloadTask and TaskPriority are well-typed
from src.core.m3u8_parser import extract_m3u8_info # Assuming this function is well-typed


logger = logging.getLogger(__name__)

# --- Placeholder/Helper Types (Replace with actual imports or more detailed Protocols if available) ---
# It's assumed that DownloadTask has a 'status' attribute which is an enum.
# For example:
# class TaskStatus(Enum):
#     PENDING = "PENDING"
#     RUNNING = "RUNNING"
#     PAUSED = "PAUSED"
#     COMPLETED = "COMPLETED"
#     FAILED = "FAILED"
#     CANCELED = "CANCELED"
# And DownloadTask.status would be of type TaskStatus.
# Since this enum is not provided, 'Any' will be used for status comparisons,
# or direct string comparisons if the original code implied that.
# Users should replace these with their actual TaskStatus enum.

class AppType(QApplication): # Assuming app is a QApplication or subclass
    tray_icon: Any # Should be QSystemTrayIcon or a custom typed class
    def send_notification(self, title: str, message: str, icon: Optional[FluentIcon] = None, duration: int = 5000) -> None:
        # This is a placeholder signature
        ...

class SettingsType: # Placeholder for your settings class
    def get(self, section: str, key: str, default: Any = None) -> Any: ...
    def set(self, section: str, key: str, value: Any) -> None: ...
    def save_settings(self) -> None: ...

class DownloadManagerType: # Placeholder for your download manager
    tasks: Dict[str, DownloadTask]
    active_tasks: List[DownloadTask] # Or Dict[str, DownloadTask]
    on_task_progress: Optional[callable[[str, Dict[str, Any]], None]]
    on_task_status_changed: Optional[callable[[str, Any, Any], None]] # Status types are Any
    on_task_completed: Optional[callable[[str, str], None]]
    on_task_failed: Optional[callable[[str, str], None]]

    def stop(self) -> None: ...
    def add_task(self, task: DownloadTask) -> None: ...
    def start_task(self, task_id: str) -> None: ...
    def pause_task(self, task_id: str) -> None: ...
    def resume_task(self, task_id: str) -> None: ...
    def cancel_task(self, task_id: str) -> None: ...
    def remove_task(self, task_id: str, delete_files: bool = False) -> None: ...
    def get_task(self, task_id: str) -> Optional[DownloadTask]: ...
# --- End Placeholder Types ---


class StatusInfoWidget(QWidget):
    def __init__(self, icon: Union[FluentIcon, QPixmap], text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.icon: Union[FluentIcon, QPixmap] = icon
        self.text: str = text
        self.icon_color: Optional[QColor] = None
        self.icon_label: QLabel
        self.text_label: QLabel
        self._create_ui()

    def _create_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(4)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        layout.addWidget(self.icon_label)
        self.text_label = QLabel(self.text)
        layout.addWidget(self.text_label)
        self._update_icon()

    def setContent(self, icon: Union[FluentIcon, QPixmap], text: str) -> None:
        self.icon = icon
        self.text = text
        self.text_label.setText(text)
        self._update_icon()

    def setIconColor(self, color: QColor) -> None:
        self.icon_color = color
        self._update_icon()

    def _update_icon(self) -> None:
        pixmap: QPixmap
        if isinstance(self.icon, FluentIcon):
            pixmap = self._create_colored_pixmap(self.icon, self.icon_color)
            self.icon_label.setPixmap(pixmap)
        elif isinstance(self.icon, QPixmap): # If icon can be a QPixmap
             # Scale pixmap if necessary, original code used fixed size
            self.icon_label.setPixmap(self.icon.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        # If self.icon could be QIcon (FluentIcon.icon() returns QIcon):
        # elif isinstance(self.icon, QIcon):
        #     pixmap = self.icon.pixmap(16,16)
        #     if self.icon_color: # Apply color if QIcon doesn't handle it
        #        # Manual coloring for QIcon's pixmap would be similar to _create_colored_pixmap
        #        pass # Placeholder for QIcon coloring
        #     self.icon_label.setPixmap(pixmap)


    def _create_colored_pixmap(self, fluent_icon: FluentIcon, color: Optional[QColor] = None) -> QPixmap:
        # FluentIcon might handle coloring directly: fluent_icon.icon(color_if_any).pixmap(16,16)
        # The original code implies manual coloring.
        original_pixmap: QPixmap = fluent_icon.icon().pixmap(16, 16)

        if color is None:
            return original_pixmap

        colored_pixmap = QPixmap(original_pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawPixmap(0, 0, original_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), color)
        painter.end()
        return colored_pixmap


class MainWindow(QMainWindow):
    def __init__(self, app: AppType, download_manager: DownloadManagerType, settings: SettingsType):
        super().__init__()
        self.app: AppType = app
        self.download_manager: DownloadManagerType = download_manager
        self.settings: SettingsType = settings
        self._force_close: bool = False

        # Initialize attributes that will be defined in methods
        self.task_manager: TaskManager
        self.log_viewer: LogViewer
        self.main_splitter: QSplitter
        self.status_bar: QStatusBar
        self.status_info_widget: StatusInfoWidget
        self.active_tasks_label: QLabel
        self.cpu_usage_label: QLabel
        self.memory_usage_label: QLabel
        self.speed_label: QLabel
        self.system_info_timer: QTimer
        self.auto_save_timer: QTimer

        if self.download_manager: # Ensure download_manager is not None
            self.download_manager.on_task_progress = self.on_task_progress
            self.download_manager.on_task_status_changed = self.on_task_status_changed
            self.download_manager.on_task_completed = self.on_task_completed
            self.download_manager.on_task_failed = self.on_task_failed

        self.setWindowTitle("Encrypted Video Downloader")
        self.setMinimumSize(1000, 700)
        self._create_ui()
        self._create_menu()
        self._create_statusbar()
        self._connect_signals()
        self._setup_auto_save()
        self._update_ui()
        logger.info("Main window initialized")

    def _create_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setHandleWidth(8)
        self.main_splitter.setChildrenCollapsible(False)

        self.task_manager = TaskManager(self.settings) # type: ignore[arg-type] # If SettingsType is not what TaskManager expects
        self.main_splitter.addWidget(self.task_manager)
        self.log_viewer = LogViewer()
        self.main_splitter.addWidget(self.log_viewer)
        self.main_splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])
        main_layout.addWidget(self.main_splitter)

        if hasattr(self.task_manager, 'task_action_requested'):
            self.task_manager.task_action_requested.connect(self.handle_task_action)

        geometry_data: Optional[Any] = self.settings.get("ui", "window_geometry", None)
        state_data: Optional[Any] = self.settings.get("ui", "window_state", None)

        if isinstance(geometry_data, (str, bytes)):
            try:
                encoded_geom = geometry_data.encode() if isinstance(geometry_data, str) else geometry_data
                self.restoreGeometry(QByteArray.fromBase64(encoded_geom))
            except Exception as e:
                logger.warning(f"Failed to restore geometry: {e}")
        if isinstance(state_data, (str, bytes)):
            try:
                encoded_state = state_data.encode() if isinstance(state_data, str) else state_data
                self.restoreState(QByteArray.fromBase64(encoded_state))
            except Exception as e:
                logger.warning(f"Failed to restore state: {e}")


    def _create_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File(&F)")
        new_task_action = Action(FluentIcon.ADD, "New Task(&N)", self)
        new_task_action.setShortcut(QKeySequence(QKeySequence.StandardKey.New))
        new_task_action.triggered.connect(self.show_new_task_dialog)
        file_menu.addAction(new_task_action)

        import_url_action = Action(FluentIcon.LINK, "Import from URL(&I)", self)
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
        import_url_submenu_action = Action(FluentIcon.LINK, "Import from URL", self)
        import_url_submenu_action.setShortcut("Ctrl+I")
        import_url_submenu_action.triggered.connect(self.import_from_url)
        import_menu.addAction(import_url_submenu_action)
        import_batch_action = Action(FluentIcon.FOLDER_ADD, "Batch Import URLs", self)
        import_batch_action.setShortcut("Ctrl+B")
        import_batch_action.triggered.connect(self.import_batch_urls)
        import_menu.addAction(import_batch_action)
        file_menu.addMenu(import_menu)
        file_menu.addSeparator()

        exit_action = Action(FluentIcon.CLOSE, "Exit(&Q)", self)
        exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))
        exit_action.triggered.connect(self.close) # QMainWindow.close, not self.app.quit
        file_menu.addAction(exit_action)

        media_menu = self.menuBar().addMenu("Media(&M)")
        process_media_action = Action(FluentIcon.EDIT, "Process Media Files(&P)", self)
        process_media_action.setShortcut("Ctrl+P")
        process_media_action.triggered.connect(self.show_media_processing)
        media_menu.addAction(process_media_action)
        media_menu.addSeparator()
        batch_convert_action = Action(FluentIcon.TILES, "Batch Convert(&B)", self)
        batch_convert_action.triggered.connect(self.show_batch_conversion)
        media_menu.addAction(batch_convert_action)

        task_menu = self.menuBar().addMenu("Tasks(&T)")
        start_all_action = Action(FluentIcon.PLAY, "Start All(&S)", self)
        start_all_action.triggered.connect(self.start_all_tasks)
        task_menu.addAction(start_all_action)
        pause_all_action = Action(FluentIcon.PAUSE, "Pause All(&P)", self)
        pause_all_action.triggered.connect(self.pause_all_tasks)
        task_menu.addAction(pause_all_action)
        task_menu.addSeparator()
        clear_completed_action = Action(FluentIcon.DELETE, "Clear Completed Tasks(&C)", self)
        clear_completed_action.triggered.connect(self.clear_completed_tasks)
        task_menu.addAction(clear_completed_action)

        help_menu = self.menuBar().addMenu("Help(&H)")
        about_action = Action(FluentIcon.INFO, "About(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_statusbar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        task_frame = QFrame()
        task_layout = QHBoxLayout(task_frame)
        task_layout.setContentsMargins(2, 0, 2, 0)
        task_layout.setSpacing(10)
        self.status_info_widget = StatusInfoWidget(FluentIcon.DATE_TIME, "Ready", self)
        task_layout.addWidget(self.status_info_widget)
        self.status_bar.addWidget(task_frame)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        separator1.setFixedWidth(1); separator1.setFixedHeight(16)
        self.status_bar.addWidget(separator1)
        self.active_tasks_label = QLabel("Active Tasks: 0/0")
        self.status_bar.addWidget(self.active_tasks_label)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setFixedWidth(1); separator2.setFixedHeight(16)
        self.status_bar.addWidget(separator2)

        self.cpu_usage_label = QLabel("CPU: 0%")
        self.status_bar.addWidget(self.cpu_usage_label)
        self.memory_usage_label = QLabel("Memory: 0MB")
        self.status_bar.addWidget(self.memory_usage_label)
        self.status_bar.addPermanentWidget(QFrame(), 1)

        speed_frame = QFrame()
        speed_layout = QHBoxLayout(speed_frame)
        speed_layout.setContentsMargins(6, 0, 6, 0); speed_layout.setSpacing(6)
        speed_icon_label = QLabel()
        speed_icon_label.setPixmap(FluentIcon.DOWNLOAD.icon().pixmap(16, 16))
        speed_layout.addWidget(speed_icon_label)
        self.speed_label = QLabel("0 B/s")
        self.speed_label.setStyleSheet("font-weight: bold;")
        speed_layout.addWidget(self.speed_label)
        self.status_bar.addPermanentWidget(speed_frame)

        self.system_info_timer = QTimer(self)
        self.system_info_timer.timeout.connect(self._update_system_info)
        self.system_info_timer.start(5000)

    def _update_system_info(self) -> None:
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage_label.setText(f"CPU: {cpu_percent:.1f}%")
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.memory_usage_label.setText(f"Memory: {memory_mb:.1f}MB")
        except ImportError:
            self.cpu_usage_label.hide(); self.memory_usage_label.hide()
        except Exception:
            self.cpu_usage_label.hide(); self.memory_usage_label.hide()

    def _connect_signals(self) -> None:
        pass

    def _setup_auto_save(self) -> None:
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(60000)

    def _update_ui(self) -> None:
        if hasattr(self, 'task_manager') and self.download_manager:
            self.task_manager.update_tasks(self.download_manager.tasks)
            active_count = len(self.download_manager.active_tasks)
            total_count = len(self.download_manager.tasks)
            self.active_tasks_label.setText(f"Active Tasks: {active_count}/{total_count}")
            if active_count > 0:
                self.status_info_widget.setContent(FluentIcon.DOWNLOAD, "Downloading")
            elif total_count > 0:
                self.status_info_widget.setContent(FluentIcon.PAUSE, "Paused")
            else:
                self.status_info_widget.setContent(FluentIcon.DATE_TIME, "Ready")

    def auto_save(self) -> None:
        if self.download_manager:
            for task in self.download_manager.tasks.values():
                if hasattr(task, 'save_progress'):
                    task.save_progress()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.app.tray_icon and self.settings.get("ui", "minimize_to_tray", False) and not self._force_close:
            event.ignore()
            self.hide()
            if self.settings.get("ui", "show_notifications", True):
                # Standard QSystemTrayIcon uses showMessage
                if hasattr(self.app.tray_icon, "showMessage"):
                    self.app.tray_icon.showMessage(
                        "Encrypted Video Downloader",
                        "Application minimized to system tray. Click icon to restore."
                    )
                elif hasattr(self.app.tray_icon, "show_notification"): # Custom method
                     self.app.tray_icon.show_notification( # type: ignore
                        "Encrypted Video Downloader",
                        "Application minimized to system tray. Click icon to restore."
                    )
            return

        active_tasks_list: List[DownloadTask] = []
        if self.download_manager:
            for task in self.download_manager.tasks.values():
                # Replace with actual TaskStatus enum checks, e.g., task.status == TaskStatus.RUNNING
                if hasattr(task, 'status') and task.status in ["RUNNING", "PAUSED"]: # Placeholder string comparison
                    active_tasks_list.append(task)

        if active_tasks_list and self.settings.get("ui", "confirm_on_exit", True):
            msg_box = MessageBox(
                "Confirm Exit",
                f"There are still {len(active_tasks_list)} tasks in progress. Are you sure you want to exit?\n(Tasks will be paused and progress saved)",
                self
            )
            if not msg_box.exec(): # exec() returns bool for MessageBox in some contexts or int for QDialog
                event.ignore()
                return

        if self.download_manager:
            self.download_manager.stop()

        # QByteArray.data() returns memoryview, so .tobytes().decode()
        geom_bytes = self.saveGeometry().toBase64().data().tobytes()
        self.settings.set("ui", "window_geometry", geom_bytes.decode('utf-8'))
        state_bytes = self.saveState().toBase64().data().tobytes()
        self.settings.set("ui", "window_state", state_bytes.decode('utf-8'))
        self.settings.save_settings()
        event.accept()

    @Slot()
    def show_new_task_dialog(self) -> None:
        dialog = TaskDialog(self.settings, parent=self) # type: ignore[arg-type]
        if dialog.exec():
            task_data: Dict[str, Any] = dialog.get_task_data()
            priority_map: Dict[str, TaskPriority] = {
                "high": TaskPriority.HIGH, "normal": TaskPriority.NORMAL, "low": TaskPriority.LOW
            }
            task = DownloadTask(
                name=str(task_data.get("name", "Untitled Task")),
                base_url=str(task_data.get("base_url","")),
                key_url=str(task_data.get("key_url")) if task_data.get("key_url") else None,
                segments=list(task_data.get("segments", [])),
                output_file=str(task_data.get("output_file", "")),
                settings=self.settings, # type: ignore[arg-type]
                priority=priority_map.get(str(task_data.get("priority", "normal")), TaskPriority.NORMAL)
            )
            if self.download_manager:
                self.download_manager.add_task(task)
                if task_data.get("auto_start", False):
                    self.download_manager.start_task(task.task_id)
            self._update_ui()

    @Slot()
    def import_from_url(self) -> None:
        InfoBar.info( # type: ignore[attr-defined] # If InfoBarPosition is not found
            title="Information", content="This feature is not yet implemented",
            orient=Qt.Orientation.Horizontal, isClosable=True,
            position=InfoBarPosition.TOP, duration=2000, parent=self
        )

    @Slot()
    def show_settings(self) -> None:
        dialog = SettingsDialog(self.settings, parent=self) # type: ignore[arg-type]
        if dialog.exec(): self._update_ui()

    @Slot()
    def show_about(self) -> None:
        dialog = AboutDialog(parent=self)
        dialog.exec()

    @Slot(str, str)
    def handle_task_action(self, task_id: str, action: str) -> None:
        if not self.download_manager: return
        actions = {
            "start": self.download_manager.start_task,
            "pause": self.download_manager.pause_task,
            "resume": self.download_manager.resume_task,
            "cancel": self.download_manager.cancel_task,
            "remove": lambda tid: self.download_manager.remove_task(tid),
            "remove_with_file": lambda tid: self.download_manager.remove_task(tid, delete_files=True)
        }
        if action_func := actions.get(action):
            action_func(task_id)
        self._update_ui()

    @Slot()
    def start_all_tasks(self) -> None:
        if not self.download_manager: return
        for task_id, task_item in self.download_manager.tasks.items():
            # Replace with actual TaskStatus enum
            if hasattr(task_item, 'status') and task_item.status in ["PENDING", "PAUSED"]: # Placeholder
                self.download_manager.start_task(task_id)
        self._update_ui()

    @Slot()
    def pause_all_tasks(self) -> None:
        if not self.download_manager: return
        for task_id, task_item in self.download_manager.tasks.items():
            if hasattr(task_item, 'status') and task_item.status == "RUNNING": # Placeholder
                self.download_manager.pause_task(task_id)
        self._update_ui()

    @Slot()
    def clear_completed_tasks(self) -> None:
        if not self.download_manager: return
        task_ids_to_remove = [
            tid for tid, t in self.download_manager.tasks.items()
            if hasattr(t, 'status') and t.status in ["COMPLETED", "FAILED", "CANCELED"] # Placeholder
        ]
        for task_id in task_ids_to_remove:
            self.download_manager.remove_task(task_id)
        self._update_ui()

    @Slot(str, dict)
    def on_task_progress(self, task_id: str, progress_data: Dict[str, Any]) -> None:
        if hasattr(self, 'task_manager'):
            self.task_manager.update_task_progress(task_id, progress_data)
        if self.download_manager:
            total_speed: float = sum(
                task.progress.get("speed", 0.0) for task in self.download_manager.tasks.values()
                if hasattr(task, 'status') and task.status == "RUNNING" # Placeholder
            )
            self.speed_label.setText(self._format_speed(total_speed))

    @Slot(str, object, object)
    def on_task_status_changed(self, task_id: str, old_status: Any, new_status: Any) -> None:
        if hasattr(self, 'task_manager'):
            self.task_manager.update_task_status(task_id, new_status)
        if self.download_manager:
            active_count = len(self.download_manager.active_tasks)
            total_count = len(self.download_manager.tasks)
            self.active_tasks_label.setText(f"Active Tasks: {active_count}/{total_count}")

            if self.settings.get("ui", "show_notifications", True):
                task = self.download_manager.get_task(task_id)
                if task and hasattr(task, 'name') and hasattr(task, 'status'):
                    # Replace string status with actual TaskStatus enum
                    status_map = {
                        "RUNNING": (f"Task \"{task.name}\" has started downloading", "Task Started"),
                        "PAUSED": (f"Task \"{task.name}\" has been paused", "Task Paused"),
                        "COMPLETED": (f"Task \"{task.name}\" has completed successfully", "Task Completed"),
                        "FAILED": (f"Task \"{task.name}\" has failed", "Task Failed"),
                        "CANCELED": (f"Task \"{task.name}\" has been canceled", "Task Canceled"),
                    }
                    # Special condition for RUNNING notification (only if not resuming from PAUSED)
                    if new_status == "RUNNING" and old_status != "PAUSED":
                        msg, title = status_map["RUNNING"]
                        self.app.send_notification(title, msg)
                    elif new_status != "RUNNING" and new_status in status_map:
                        msg, title = status_map[new_status]
                        self.app.send_notification(title, msg)
        self._update_ui()


    @Slot(str, str)
    def on_task_completed(self, task_id: str, message: str) -> None: # task_id is unused by this impl
        logger.info(f"Task completed: {message}")
        if hasattr(self, 'log_viewer'): self.log_viewer.add_log_entry(f"Task completed: {message}", level="info")
        self._update_ui()

    @Slot(str, str)
    def on_task_failed(self, task_id: str, message: str) -> None: # task_id is unused by this impl
        logger.error(f"Task failed: {message}")
        if hasattr(self, 'log_viewer'): self.log_viewer.add_log_entry(f"Task failed: {message}", level="error")
        self._update_ui()

    def _format_speed(self, bytes_per_second: float) -> str:
        if bytes_per_second < 1024: return f"{bytes_per_second:.1f} B/s"
        if bytes_per_second < 1024 * 1024: return f"{bytes_per_second / 1024:.1f} KB/s"
        return f"{bytes_per_second / (1024 * 1024):.2f} MB/s"

    @Slot()
    def import_batch_urls(self) -> None:
        dialog = BatchURLDialog(self.settings, parent=self) # type: ignore[arg-type]
        if hasattr(dialog, 'urls_imported'):
            dialog.urls_imported.connect(self._handle_batch_urls)
        dialog.exec()

    @Slot(list)
    def _handle_batch_urls(self, urls: List[str]) -> None:
        if not urls: return
        msg_box = MessageBox(
            "URL Processing",
            f"Imported {len(urls)} URLs. Would you like to try auto-parsing them into download tasks?", self
        )
        if msg_box.exec():
            progress = QProgressDialog("Parsing URLs...", "Cancel", 0, len(urls), self)
            progress.setWindowTitle("Parsing"); progress.setMinimumDuration(0); progress.setModal(True); progress.show()
            successful_imports = 0
            for i, url_str in enumerate(urls):
                progress.setValue(i); progress.setLabelText(f"Parsing URL {i+1}/{len(urls)}")
                if progress.wasCanceled(): break
                try:
                    ua_setting: str = self.settings.get("advanced", "user_agent", "")
                    req_headers: Optional[Dict[str, str]] = {"User-Agent": ua_setting} if ua_setting else None
                    m3u8_data: Dict[str, Any] = extract_m3u8_info(url_str, req_headers) # type: ignore[arg-type]
                    if m3u8_data.get("success"):
                        parsed_url_obj: ParseResult = urlparse(url_str)
                        url_path: str = parsed_url_obj.path
                        file_name_base: str = basename(url_path).split(".")[0] if basename(url_path) else f"Task-{i+1}"
                        output_dir_path: str = self.settings.get("general", "output_directory", ".")
                        final_output_file: str = join(output_dir_path, f"{file_name_base}.mp4")
                        new_task = DownloadTask(
                            name=file_name_base, base_url=str(m3u8_data["base_url"]),
                            key_url=str(m3u8_data.get("key_url")) if m3u8_data.get("key_url") else None,
                            segments(list(m3u8_data.get("segments",[])), output_file=final_output_file,
                            settings=self.settings, priority=TaskPriority.NORMAL # type: ignore[arg-type]
                        )
                        if self.download_manager:
                            self.download_manager.add_task(new_task)
                            self.download_manager.start_task(new_task.task_id)
                        successful_imports += 1
                except Exception as e: logger.error(f"Error parsing URL {url_str}: {e}")
            progress.setValue(len(urls))
            self._update_ui()
            InfoBar.success( # type: ignore[attr-defined]
                title="Import Results", content=f"Successfully imported {successful_imports} tasks, failed {len(urls) - successful_imports}.",
                orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=self
            )
        else:
            q_clipboard = QApplication.clipboard()
            if q_clipboard: q_clipboard.setText("\n".join(urls))
            InfoBar.info( # type: ignore[attr-defined]
                title="URLs Copied", content=f"{len(urls)} URLs copied to clipboard.",
                orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=self
            )

    @Slot()
    def show_media_processing(self) -> None:
        output_file_path: Optional[str] = None
        if hasattr(self, 'task_manager') and self.download_manager:
            selected_ids: List[str] = self.task_manager.get_selected_rows()
            if selected_ids:
                task_obj = self.download_manager.get_task(selected_ids[0])
                if task_obj and hasattr(task_obj, 'status') and task_obj.status == "COMPLETED" and task_obj.output_file: # Placeholder
                    output_file_path = task_obj.output_file
        dialog = MediaProcessingDialog(self.settings, output_file_path, parent=self) # type: ignore[arg-type]
        if hasattr(dialog, 'processing_completed'):
            dialog.processing_completed.connect(self._on_media_processing_completed)
        dialog.exec()

    @Slot()
    def show_batch_conversion(self) -> None:
        dialog = BatchConversionDialog(self.settings, parent=self) # type: ignore[arg-type]
        if hasattr(dialog, 'processing_completed'):
            dialog.processing_completed.connect(self._on_batch_conversion_completed)
        dialog.exec()

    @Slot(bool, str)
    def _on_batch_conversion_completed(self, op_success: bool, result_message: str) -> None:
        log_level = "info" if op_success else "error"
        if hasattr(self, 'log_viewer'): self.log_viewer.add_log_entry(result_message, level=log_level)
        if op_success and self.settings.get("ui", "show_notifications", True):
            self.app.send_notification("Batch Conversion", "Media batch conversion completed")

    @Slot(bool, str)
    def _on_media_processing_completed(self, op_success: bool, result_message: str) -> None:
        log_level = "info" if op_success else "error"
        if hasattr(self, 'log_viewer'): self.log_viewer.add_log_entry(result_message, level=log_level)
        if op_success and self.settings.get("ui", "show_notifications", True):
            self.app.send_notification("Media Processing", "Media processing completed")

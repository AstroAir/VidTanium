import sys
import os
from loguru import logger
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTranslator, QLocale

from .settings import Settings
from src.core.downloader import DownloadManager
from src.gui.main_window import MainWindow
from src.core.scheduler import TaskScheduler
from src.gui.utils.i18n import init_i18n, set_locale


class Application(QApplication):
    """Application class"""

    def __init__(self, config_dir=None):
        super().__init__(sys.argv)

        # Initialize settings
        self.settings = Settings(config_dir)

        # Set application properties
        self.setApplicationName("Video Downloader")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Development Team")
        self.setOrganizationDomain("example.com")

        # Initialize i18n system first
        init_i18n()
        self._i18n_initialized = True

        # Apply language
        self._apply_language()

        # Apply pending locale if any
        if hasattr(self, '_pending_locale'):
            set_locale(self._pending_locale)

        # Initialize theme manager
        from src.gui.theme_manager import ThemeManager
        self.theme_manager = ThemeManager(self.settings, self)

        # Initialize download manager
        self.download_manager = DownloadManager(self.settings)

        # Initialize task scheduler
        self.task_scheduler = TaskScheduler(config_dir)

        self._init_system_tray()

        # Register task handler
        self.task_scheduler.register_handler(
            "download", self._handle_download_task)        # Create main window
        self.main_window = MainWindow(
            self, self.download_manager, self.settings, self.theme_manager)  # type: ignore

        # Check initial settings
        self._check_initial_settings()

    def run(self):
        """Run the application"""
        # Start download manager
        logger.info("Starting download manager")
        self.download_manager.start()

        logger.info("Starting task scheduler")
        self.task_scheduler.start()

        # Show main window
        logger.debug("Displaying main window")
        self.main_window.show()

        # Check for updates
        if self.settings.get("general", "check_updates", True):
            self._check_updates()

        # Run application
        logger.info("Application started, entering main event loop")
        return self.exec()

    def send_notification(self, title: str, message: str, icon=None, duration=5000):
        """Send system notification

        Args:
            title (str): Notification title
            message (str): Notification message
            icon: Notification icon (optional)
            duration: Notification duration in ms (default: 5000)
        """
        if not self.settings.get("ui", "show_notifications", True):
            logger.debug("Notifications are disabled, skipping")
            return

        # Check if system tray is available
        if hasattr(self, "tray_icon") and self.tray_icon:
            logger.debug(f"Sending notification: {title} - {message}")
            self.tray_icon.show_notification(title, message, icon, duration)
        else:
            logger.debug("System tray not available, notification not shown")

    def add_task_from_url(self, url):
        """Automatically create task from URL

        Args:
            url (str): URL to process
        """        # Simplified handling, actual implementation should parse URL to extract M3U8 and key information
        # TODO: Implement URL parsing
        logger.info(f"Attempting to create task from URL: {url}")
        self.main_window.import_from_url()

    def _apply_theme(self):
        """Apply theme settings using QFluentWidgets"""
        from qfluentwidgets import setTheme, Theme, qconfig
        
        theme = self.settings.get("general", "theme", "system")
        logger.debug(f"Applying theme: {theme}")

        try:
            if theme == "light":
                # Set light theme
                setTheme(Theme.LIGHT)
                logger.debug("Applied light theme")
            elif theme == "dark":
                # Set dark theme
                setTheme(Theme.DARK)
                logger.debug("Applied dark theme")
            else:
                # Follow system theme
                setTheme(Theme.AUTO)
                logger.debug("Applied system theme")
                
            # Save theme configuration
            qconfig.save()
            
        except Exception as e:
            logger.error(f"Error applying theme: {e}", exc_info=True)

    def _apply_language(self):
        """Apply language settings"""
        language = self.settings.get("general", "language", "auto")
        logger.debug(f"Setting application language: {language}")        # Determine locale
        if language == "auto":
            # Use system language
            system_locale = QLocale.system().name()
            logger.debug(f"Using system locale: {system_locale}")
            # Map system locale to our supported locales
            if system_locale.startswith("zh"):
                locale = "zh_CN"
            else:
                locale = "en"
        else:
            locale = language if language else "zh_CN"
            logger.debug(f"Using specified locale: {locale}")

        # Set i18n locale
        if hasattr(self, '_i18n_initialized'):
            set_locale(locale)
        else:
            # Store for later initialization
            self._pending_locale = locale

        # Create Qt translator (for Qt built-in strings)
        translator = QTranslator()
        # Load translation file (requires .qm files in actual application)
        # translator.load(f":/translations/{locale}.qm")
        # Install translator
        # self.installTranslator(translator)

    def _check_initial_settings(self):
        """Check initial settings"""
        # Check FFmpeg path
        from src.core.merger import is_ffmpeg_available

        ffmpeg_path = self.settings.get("advanced", "ffmpeg_path", "")
        if ffmpeg_path:
            logger.debug(f"Verifying FFmpeg path: {ffmpeg_path}")
            if not is_ffmpeg_available(ffmpeg_path):
                logger.warning(
                    f"Specified FFmpeg path is invalid: {ffmpeg_path}")
                self.settings.set("advanced", "ffmpeg_path", "")
                self.settings.save_settings()
                logger.debug("FFmpeg path has been reset")

        # Check output directory
        output_dir = self.settings.get("general", "output_directory", "")
        if output_dir:
            logger.debug(f"Checking output directory: {output_dir}")
            if not os.path.exists(output_dir):
                try:
                    logger.info(
                        f"Output directory does not exist, creating: {output_dir}")
                    os.makedirs(output_dir, exist_ok=True)
                    logger.success(
                        f"Successfully created output directory: {output_dir}")
                except Exception as e:
                    logger.warning(
                        f"Cannot create output directory: {output_dir}, error: {e}", exc_info=True)
                    default_dir = str(os.path.expanduser("~"))
                    logger.debug(
                        f"Setting output directory to user home: {default_dir}")
                    self.settings.set(
                        "general", "output_directory", default_dir)
                    self.settings.save_settings()

    def _check_updates(self):
        """Check for updates"""
        # In an actual application, connect to a server to check for updates
        # Simplified handling here
        logger.info("Checking for updates...")

    def _handle_download_task(self, task_data):
        """Handle download task

        Args:
            task_data (dict): Task configuration data
        """
        try:
            # Create download task
            from src.core.downloader import DownloadTask, TaskPriority

            priority_map = {
                "high": TaskPriority.HIGH,
                "normal": TaskPriority.NORMAL,
                "low": TaskPriority.LOW
            }

            priority = priority_map.get(
                task_data.get("priority"), TaskPriority.NORMAL)
            logger.info(
                f"Creating scheduled download task with priority: {priority}")

            task = DownloadTask(
                name=task_data.get("name", "Scheduled Task"),
                base_url=task_data.get("base_url"),
                key_url=task_data.get("key_url"),
                segments=task_data.get("segments"),
                output_file=task_data.get("output_file"),
                settings=self.settings,
                priority=priority
            )

            # Add to download manager
            task_id = self.download_manager.add_task(task)
            logger.debug(f"Created task with ID: {task_id}")

            # Start task immediately
            logger.info(f"Starting scheduled task: {task.name}")
            self.download_manager.start_task(task_id)

            # Send notification
            if task_data.get("notify", True):
                self.send_notification(
                    "Scheduled Task Started", f"Started scheduled download task: {task.name}")

            logger.success(
                f"Successfully created and started scheduled task: {task.name}")
        except Exception as e:
            logger.error(f"Error processing download task: {e}", exc_info=True)
            # Send notification on error if enabled
            if task_data.get("notify", True):
                self.send_notification(
                    "Scheduled Task Failed",
                    f"Failed to start scheduled task: {task_data.get('name', 'Unknown')}"
                )

    def _init_system_tray(self):
        """Initialize system tray"""
        from src.gui.widgets.system_tray import SystemTrayIcon

        # Check if tray feature is enabled
        enable_tray = self.settings.get("ui", "minimize_to_tray", False)
        logger.debug(f"System tray integration enabled: {enable_tray}")

        if enable_tray:
            self.tray_icon = SystemTrayIcon(
                self, self.settings, self.main_window)

            # Connect signals
            self.tray_icon.action_triggered.connect(self._handle_tray_action)

            # Check if system supports tray
            if self.tray_icon.is_supported():
                logger.debug("System tray is supported, showing icon")
                self.tray_icon.show()
            else:
                logger.warning("System tray is not supported by the platform")
                self.tray_icon = None
        else:
            logger.debug("System tray integration disabled in settings")
            self.tray_icon = None

    def _handle_tray_action(self, action):
        """Handle tray actions

        Args:
            action (str): Action identifier
        """
        logger.debug(f"System tray action received: {action}")
        if action == "show":
            logger.debug("Showing and activating main window")
            self.main_window.show()
            self.main_window.activateWindow()
        elif action == "hide":
            logger.debug("Hiding main window")
            self.main_window.hide()
        elif action == "start_all":
            logger.info("Starting all tasks from tray menu")
            self.main_window.start_all_tasks()
        elif action == "pause_all":
            logger.info("Pausing all tasks from tray menu")
            self.main_window.pause_all_tasks()
        elif action == "exit":
            logger.info("Exiting application from tray menu")
            self.main_window.close()

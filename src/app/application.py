from src.gui.utils.i18n import init_i18n, set_locale
from src.core.scheduler import TaskScheduler
from src.gui.main_window import MainWindow
from src.core.downloader import DownloadManager
from src.core.singleton_manager import get_singleton_manager
from src.core.ipc_server import IPCServer
from src.core.window_activator import get_window_activator
from .settings import Settings
import sys
import os
from .logging_config import ensure_logging_configured
from loguru import logger
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTranslator, QLocale, QMutex
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.gui.widgets.system_tray import EnhancedSystemTrayIcon
from dataclasses import dataclass
from enum import Enum

# Ensure logging is configured first
ensure_logging_configured()


@dataclass
class InitializationStep:
    """Represents a single initialization step"""
    name: str
    function: Callable
    dependencies: Optional[list] = None
    critical: bool = True  # If False, failure won't stop initialization

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class InitializationPhase(Enum):
    """Initialization phases in order"""
    CORE_SYSTEMS = "core_systems"
    MANAGERS = "managers"
    UI_COMPONENTS = "ui_components"
    FINALIZATION = "finalization"


class CentralizedInitializer:
    """Centralized initialization system for the application"""

    def __init__(self, app_instance):
        self.app = app_instance
        self.completed_steps = set()
        self.failed_steps = set()
        self.initialization_data = {}
        self._steps: Dict[InitializationPhase, list[InitializationStep]] = {
            phase: [] for phase in InitializationPhase
        }

    def register_step(self, phase: InitializationPhase, step: InitializationStep):
        """Register an initialization step"""
        self._steps[phase].append(step)

    def initialize_all(self) -> bool:
        """Execute all initialization phases"""
        try:
            for phase in InitializationPhase:
                if not self._execute_phase(phase):
                    logger.error(f"Initialization failed at phase: {phase.value}")
                    return False
            logger.info("Application initialization completed successfully")
            return True
        except Exception as e:
            logger.error(f"Critical error during initialization: {e}", exc_info=True)
            return False

    def _execute_phase(self, phase: InitializationPhase) -> bool:
        """Execute a single initialization phase"""
        if phase not in self._steps:
            return True

        logger.debug(f"Executing initialization phase: {phase.value}")

        for step in self._steps[phase]:
            if not self._execute_step(step):
                if step.critical:
                    logger.error(f"Critical step failed: {step.name}")
                    return False
                else:
                    logger.warning(f"Non-critical step failed: {step.name}")

        return True

    def _execute_step(self, step: InitializationStep) -> bool:
        """Execute a single initialization step"""
        # Check dependencies
        if step.dependencies:
            for dep in step.dependencies:
                if dep not in self.completed_steps:
                    logger.error(f"Step '{step.name}' dependency '{dep}' not completed")
                    return False

        try:
            logger.debug(f"Executing initialization step: {step.name}")
            result = step.function()
            if result is not None:
                self.initialization_data[step.name] = result
            self.completed_steps.add(step.name)
            return True
        except Exception as e:
            logger.error(f"Step '{step.name}' failed: {e}", exc_info=True)
            self.failed_steps.add(step.name)
            return False


class Application(QApplication):
    """Singleton Application class with enhanced interface management"""
    _instance: Optional['Application'] = None
    _mutex = QMutex()
    _initialized: bool

    # Instance variables
    tray_icon: Optional['EnhancedSystemTrayIcon'] = None
    ipc_server: Optional[IPCServer] = None
    singleton_manager = None
    window_activator = None

    def __new__(cls, config_dir=None, cli_args=None):
        """Ensure singleton pattern"""
        cls._mutex.lock()
        try:
            if cls._instance is None:
                logger.debug("Creating new Application instance")
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            else:
                logger.debug("Returning existing Application instance")
            return cls._instance
        finally:
            cls._mutex.unlock()

    @classmethod
    def instance(cls) -> Optional['Application']:
        """Get the singleton instance"""
        return cls._instance

    def __init__(self, config_dir=None, cli_args=None):
        if hasattr(self, '_initialized') and self._initialized:
            logger.debug("Application already initialized, skipping")
            return

        super().__init__(sys.argv)
        self._initialized = True
        self._config_dir = config_dir
        self._cli_args = cli_args

        # Initialize singleton and IPC components
        self._init_singleton_components()

        # Use centralized initialization system
        self._initializer = CentralizedInitializer(self)
        self._register_initialization_steps()

        if not self._initializer.initialize_all():
            logger.error("Application initialization failed")
            raise RuntimeError("Failed to initialize application")

    def _register_initialization_steps(self):
        """Register all initialization steps with the centralizer"""
        # Core systems phase
        self._initializer.register_step(
            InitializationPhase.CORE_SYSTEMS,
            InitializationStep("app_properties", self._set_app_properties)
        )
        self._initializer.register_step(
            InitializationPhase.CORE_SYSTEMS,
            InitializationStep("settings", self._init_settings, ["app_properties"])
        )
        self._initializer.register_step(
            InitializationPhase.CORE_SYSTEMS,
            InitializationStep("i18n", self._init_i18n_system, ["settings"])
        )

        # Managers phase
        self._initializer.register_step(
            InitializationPhase.MANAGERS,
            InitializationStep("theme_manager", self._init_theme_manager, ["settings", "i18n"])
        )
        self._initializer.register_step(
            InitializationPhase.MANAGERS,
            InitializationStep("download_manager", self._init_download_manager, ["settings"])
        )
        self._initializer.register_step(
            InitializationPhase.MANAGERS,
            InitializationStep("task_scheduler", self._init_task_scheduler, ["settings"])
        )

        # UI components phase
        self._initializer.register_step(
            InitializationPhase.UI_COMPONENTS,
            InitializationStep("system_tray", self._init_system_tray, ["theme_manager"])
        )
        self._initializer.register_step(
            InitializationPhase.UI_COMPONENTS,
            InitializationStep("main_window", self._init_main_window,
                             ["theme_manager", "download_manager", "task_scheduler"])
        )

        # Finalization phase
        self._initializer.register_step(
            InitializationPhase.FINALIZATION,
            InitializationStep("cleanup", self._finalize_initialization, ["main_window"])
        )

        # Singleton and IPC phase
        self._initializer.register_step(
            InitializationPhase.FINALIZATION,
            InitializationStep("ipc_server", self._start_ipc_server, ["main_window"])
        )

    def _set_app_properties(self):
        """Set application properties"""
        self.setApplicationName("VidTanium")
        self.setApplicationVersion("0.1.0")
        self.setOrganizationName("VidTanium Team")
        self.setOrganizationDomain("vidtanium.com")

    def _init_settings(self):
        """Initialize settings and validate them"""
        self.settings = Settings(self._config_dir, cli_args=self._cli_args)
        self._validate_and_fix_settings()

    def _init_i18n_system(self):
        """Initialize internationalization system"""
        init_i18n()
        self._i18n_initialized = True
        self._apply_language()

    def _init_theme_manager(self):
        """Initialize theme manager"""
        from src.gui.theme_manager import EnhancedThemeManager
        self.theme_manager = EnhancedThemeManager(self.settings, self)

    def _init_download_manager(self):
        """Initialize download manager"""
        self.download_manager = DownloadManager(self.settings)

    def _init_task_scheduler(self):
        """Initialize task scheduler"""
        self.task_scheduler = TaskScheduler(self._config_dir)
        self.task_scheduler.register_handler("download", self._handle_download_task)

    def _init_main_window(self):
        """Initialize main window"""
        from typing import cast
        from src.gui.main_window import SettingsType, AppType
        self.main_window = MainWindow(
            cast(AppType, self), self.download_manager, cast(SettingsType, self.settings), self.theme_manager)

    def _init_core_systems(self):
        """Initialize core application systems"""
        # Set application properties (only once)
        self.setApplicationName("VidTanium")
        self.setApplicationVersion("0.1.0")
        self.setOrganizationName("VidTanium Team")
        self.setOrganizationDomain("vidtanium.com")

        # Initialize settings and validate/fix them immediately
        self.settings = Settings(self._config_dir, cli_args=self._cli_args)
        self._validate_and_fix_settings()

        # Initialize i18n system and apply language in one step
        init_i18n()
        self._i18n_initialized = True
        self._apply_language()

    def _init_managers(self):
        """Initialize application managers"""
        # Initialize theme manager
        from src.gui.theme_manager import EnhancedThemeManager
        self.theme_manager = EnhancedThemeManager(self.settings, self)

        # Initialize download manager
        self.download_manager = DownloadManager(self.settings)

        # Initialize task scheduler and register handlers immediately
        self.task_scheduler = TaskScheduler(self._config_dir)
        self.task_scheduler.register_handler("download", self._handle_download_task)

    def _init_ui_components(self):
        """Initialize UI components"""
        self._init_system_tray()

        # Create main window with all dependencies ready
        from typing import cast
        from src.gui.main_window import SettingsType, AppType
        self.main_window = MainWindow(
            cast(AppType, self), self.download_manager, cast(SettingsType, self.settings), self.theme_manager)

    def _finalize_initialization(self):
        """Finalize initialization process"""
        # Apply any pending locale settings
        if hasattr(self, '_pending_locale'):
            set_locale(self._pending_locale)
            delattr(self, '_pending_locale')  # Clean up temporary attribute

        # Start the resource manager for automatic cleanup
        from src.core.resource_manager import resource_manager
        resource_manager.start()

        logger.info("Application initialization completed successfully")

    def _init_singleton_components(self):
        """Initialize singleton and IPC components"""
        try:
            # Get singleton manager and window activator
            self.singleton_manager = get_singleton_manager()
            self.window_activator = get_window_activator()

            # Create IPC server
            self.ipc_server = IPCServer()

            logger.debug("Singleton components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize singleton components: {e}")
            # Don't fail the entire application if singleton features fail
            self.singleton_manager = None
            self.window_activator = None
            self.ipc_server = None

    def _start_ipc_server(self):
        """Start the IPC server for inter-process communication"""
        if not self.ipc_server:
            logger.warning("IPC server not initialized, skipping startup")
            return

        try:
            # Start the IPC server
            if self.ipc_server.start():
                # Register this instance with the singleton manager
                if self.singleton_manager:
                    port = self.ipc_server.get_port()
                    if self.singleton_manager.register_instance(port):
                        logger.info(f"Registered singleton instance with IPC port {port}")
                    else:
                        logger.warning("Failed to register singleton instance")

                # Connect IPC signals to window activation
                self.ipc_server.activation_requested.connect(self._handle_activation_request)
                self.ipc_server.message_received.connect(self._handle_ipc_message)

                logger.info("IPC server started successfully")
            else:
                logger.warning("Failed to start IPC server")
        except Exception as e:
            logger.error(f"Error starting IPC server: {e}")

    def _handle_activation_request(self):
        """Handle window activation request from another instance"""
        logger.info("Received window activation request")

        try:
            if self.window_activator and hasattr(self, 'main_window'):
                # Use a small delay to ensure Qt event processing
                self.window_activator.activate_with_delay(self.main_window, 100)
                logger.info("Window activation request processed")
            else:
                logger.warning("Cannot activate window: components not available")
        except Exception as e:
            logger.error(f"Error handling activation request: {e}")

    def _handle_ipc_message(self, action: str, data: dict):
        """Handle IPC messages from other instances"""
        logger.debug(f"Received IPC message: {action} with data: {data}")

        if action == "activate":
            self._handle_activation_request()
        # Add more message handlers as needed

    def run(self) -> int:
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
        exit_code: int = self.exec()
        return exit_code

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
            self.tray_icon.show_enhanced_notification(title, message, "info", duration)
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
        """Apply language settings with optimized locale detection"""
        language = self.settings.get("general", "language", "auto")

        # Determine locale efficiently
        if language == "auto":
            system_locale = QLocale.system().name()
            locale = "zh_CN" if system_locale.startswith("zh") else "en"
            logger.debug(f"Auto-detected locale: {locale} (from {system_locale})")
        else:
            locale = language or "zh_CN"
            logger.debug(f"Using configured locale: {locale}")

        # Apply locale immediately since i18n is already initialized
        set_locale(locale)

        # TODO: Implement Qt translator when translation files are available
        # self._setup_qt_translator(locale)

    def _validate_and_fix_settings(self):
        """Validate and fix settings during initialization"""
        settings_changed = False

        # Validate FFmpeg path
        settings_changed |= self._validate_ffmpeg_path()

        # Validate output directory
        settings_changed |= self._validate_output_directory()

        # Save settings only once if any changes were made
        if settings_changed:
            self.settings.save_settings()
            logger.debug("Settings validated and saved")

    def _validate_ffmpeg_path(self) -> bool:
        """Validate FFmpeg path and fix if invalid"""
        from src.core.merger import is_ffmpeg_available

        ffmpeg_path = self.settings.get("advanced", "ffmpeg_path", "")
        if ffmpeg_path and not is_ffmpeg_available(ffmpeg_path):
            logger.warning(f"Invalid FFmpeg path '{ffmpeg_path}', resetting")
            self.settings.set("advanced", "ffmpeg_path", "")
            return True
        return False

    def _validate_output_directory(self) -> bool:
        """Validate output directory and create/fix if needed"""
        output_dir = self.settings.get("general", "output_directory", "")
        if not output_dir:
            return False

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")
                return False  # Directory created, no settings change needed
            except Exception as e:
                logger.warning(f"Cannot create output directory '{output_dir}': {e}")
                default_dir = str(os.path.expanduser("~"))
                self.settings.set("general", "output_directory", default_dir)
                logger.debug(f"Reset output directory to: {default_dir}")
                return True
        return False

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

    def cleanup_singleton_components(self):
        """Clean up singleton and IPC components"""
        try:
            # Stop IPC server
            if self.ipc_server:
                logger.debug("Stopping IPC server")
                self.ipc_server.stop()
                self.ipc_server = None

            # Clean up singleton manager
            if self.singleton_manager:
                logger.debug("Cleaning up singleton manager")
                self.singleton_manager.cleanup()
                self.singleton_manager = None

            self.window_activator = None
            logger.debug("Singleton components cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up singleton components: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup_singleton_components()
        except Exception:
            pass  # Ignore errors during destruction

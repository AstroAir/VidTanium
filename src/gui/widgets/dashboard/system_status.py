"""
Dashboard System Status Component
"""
from typing import TYPE_CHECKING, Optional, Dict, Union
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Slot
from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, SubtitleLabel, PrimaryPushButton,
    IconWidget, CardWidget, FluentIcon as FIF, InfoBar, InfoBarPosition
)

from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme
from src.core.thread_pool import submit_task
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class DashboardSystemStatus(QWidget):
    """System status component with quick actions"""
    
    def __init__(self, main_window: "MainWindow", parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.system_status_labels: Dict[str, Union[BodyLabel, StrongBodyLabel]] = {}
        self.clear_cache_btn: Optional[PrimaryPushButton] = None
        self.open_settings_btn: Optional[PrimaryPushButton] = None
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the system status UI with responsive design"""
        # Main card container with responsive sizing
        card = CardWidget()
        card.setMinimumHeight(280)
        card.setMaximumHeight(500)  # Prevent excessive growth
        
        # Set responsive size policy
        from PySide6.QtWidgets import QSizePolicy
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        card.setStyleSheet(VidTaniumTheme.get_card_style())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)  # Slightly reduced margins
        layout.setSpacing(12)  # Reduced spacing

        # Header
        header_layout = self._create_header()
        layout.addLayout(header_layout)

        # System info items
        self._create_system_items(layout)

        layout.addStretch()

        # Quick actions
        actions_layout = self._create_actions()
        layout.addLayout(actions_layout)
        
        # Set up main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card)

    def _create_header(self) -> QHBoxLayout:
        """Create the header section"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        icon = IconWidget(FIF.SETTING)
        icon.setFixedSize(20, 20)
        icon.setStyleSheet(f"color: {VidTaniumTheme.SUCCESS_GREEN};")

        title = SubtitleLabel(tr("dashboard.system_status.title"))
        title.setStyleSheet(f"""
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD}; 
            color: {VidTaniumTheme.TEXT_PRIMARY};
            font-size: {VidTaniumTheme.FONT_SIZE_HEADING};
        """)

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        return header_layout

    def _create_system_items(self, layout: QVBoxLayout):
        """Create system information items"""
        system_items = [
            ("dashboard.system_status.download_threads", "download_threads", "4 threads"),
            ("dashboard.system_status.temp_files", "temp_files", "12 MB"),
            ("dashboard.system_status.cache_size", "cache_size", "45 MB"),
            ("dashboard.system_status.network_usage", "network_usage", "2.1 MB/s")
        ]

        for key, label_key, default_value in system_items:
            item = self._create_status_item(tr(key), default_value)
            # Store reference to the value label for updates
            value_label = item.findChild(StrongBodyLabel)
            if value_label:
                self.system_status_labels[label_key] = value_label
            layout.addWidget(item)

    def _create_status_item(self, label: str, value: str) -> QWidget:
        """Create a system status item"""
        item = QWidget()
        item.setFixedHeight(32)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label_widget = BodyLabel(label)
        label_widget.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")

        value_widget = StrongBodyLabel(value)
        value_widget.setStyleSheet(f"""
            color: {VidTaniumTheme.TEXT_PRIMARY}; 
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
        """)

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)

        return item

    def _create_actions(self) -> QVBoxLayout:
        """Create quick action buttons"""
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self.clear_cache_btn = PrimaryPushButton(tr("dashboard.actions.clear_cache"))
        self.clear_cache_btn.setIcon(FIF.BROOM)
        self.clear_cache_btn.setStyleSheet(VidTaniumTheme.get_button_style("secondary"))

        self.open_settings_btn = PrimaryPushButton(tr("dashboard.actions.open_settings"))
        self.open_settings_btn.setIcon(FIF.SETTING)
        self.open_settings_btn.setStyleSheet(VidTaniumTheme.get_button_style("primary"))

        actions_layout.addWidget(self.clear_cache_btn)
        actions_layout.addWidget(self.open_settings_btn)

        return actions_layout

    def _connect_signals(self):
        """Connect button signals"""
        if self.clear_cache_btn:
            self.clear_cache_btn.clicked.connect(self._handle_clear_cache_clicked)
        if self.open_settings_btn:
            self.open_settings_btn.clicked.connect(self._handle_settings_clicked)

    @Slot()
    def _handle_clear_cache_clicked(self):
        """Handle clear cache button click"""
        try:
            logger.info("Clear cache button clicked")

            # Disable button temporarily to prevent multiple clicks
            if self.clear_cache_btn:
                self.clear_cache_btn.setEnabled(False)

            # Use thread pool for cache clearing (background work)
            submit_task(
                self._execute_clear_cache_action,
                callback=self._on_clear_cache_success,
                error_callback=self._on_action_error
            )

        except Exception as e:
            logger.error(f"Error handling clear cache click: {e}")
            self._show_error_notification(tr("dashboard.error.clear_cache_failed"), str(e))
            # Re-enable button on error
            if self.clear_cache_btn:
                self.clear_cache_btn.setEnabled(True)

    @Slot()
    def _handle_settings_clicked(self):
        """Handle settings button click"""
        try:
            logger.info("Settings button clicked")

            # Disable button temporarily to prevent multiple clicks
            if self.open_settings_btn:
                self.open_settings_btn.setEnabled(False)

            # Execute dialog directly on main thread
            if hasattr(self.main_window, 'show_settings'):
                self.main_window.show_settings()
            else:
                logger.warning("Main window does not have show_settings method")
                self._show_error_notification(
                    tr("dashboard.error.settings_failed"),
                    "Settings method not found"
                )

        except Exception as e:
            logger.error(f"Error handling settings click: {e}")
            self._show_error_notification(tr("dashboard.error.settings_failed"), str(e))
        finally:
            # Re-enable button after a short delay
            if self.open_settings_btn:
                QTimer.singleShot(1000, lambda: self.open_settings_btn.setEnabled(True) if self.open_settings_btn else None)

    def _execute_clear_cache_action(self):
        """Execute clear cache action in thread pool"""
        try:
            logger.info("Executing clear cache action")
            import tempfile
            import shutil
            import os

            # Clear temporary files
            temp_dir = tempfile.gettempdir()
            vidtanium_temp = os.path.join(temp_dir, "vidtanium")
            if os.path.exists(vidtanium_temp):
                shutil.rmtree(vidtanium_temp, ignore_errors=True)

            # Clear application cache directories
            cache_dirs = [
                os.path.join(os.path.expanduser("~"), ".vidtanium", "cache"),
                os.path.join(os.path.expanduser("~"), ".cache", "vidtanium")
            ]

            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    try:
                        shutil.rmtree(cache_dir, ignore_errors=True)
                        logger.info(f"Cleared cache directory: {cache_dir}")
                    except Exception as e:
                        logger.warning(f"Failed to clear cache directory {cache_dir}: {e}")

            return "cache_cleared"
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise

    @Slot()
    def _on_clear_cache_success(self, result):
        """Handle successful clear cache action"""
        try:
            self._show_success_notification(
                tr("dashboard.success.cache_cleared"),
                tr("dashboard.success.cache_cleared_message")
            )
            # Update system status to reflect cache clearing
            self.update_system_status()
        except Exception as e:
            logger.error(f"Error in clear cache success callback: {e}")
        finally:
            # Re-enable cache button
            if self.clear_cache_btn:
                self.clear_cache_btn.setEnabled(True)

    @Slot()
    def _on_action_error(self, error_tuple):
        """Handle action errors"""
        try:
            exctype, value, tb = error_tuple
            error_message = str(value) if value else "Unknown error"
            logger.error(f"Dashboard action error: {error_message}")

            self._show_error_notification(
                tr("dashboard.error.action_failed"),
                error_message
            )
        except Exception as e:
            logger.error(f"Error in error callback: {e}")
        finally:
            # Re-enable buttons after error
            if self.clear_cache_btn:
                self.clear_cache_btn.setEnabled(True)

    def _show_success_notification(self, title: str, message: str):
        """Show success notification"""
        try:
            InfoBar.success(
                title=title,
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.main_window
            )
        except Exception as e:
            logger.error(f"Error showing success notification: {e}")

    def _show_error_notification(self, title: str, message: str):
        """Show error notification"""
        try:
            InfoBar.error(
                title=title,
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self.main_window
            )
        except Exception as e:
            logger.error(f"Error showing error notification: {e}")

    def update_system_status(self):
        """Update system status information"""
        try:
            import psutil

            # Update CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if 'cpu' in self.system_status_labels:
                self.system_status_labels['cpu'].setText(f"{cpu_percent:.1f}%")

            # Update memory usage
            memory = psutil.virtual_memory()
            memory_gb = memory.used / (1024**3)
            if 'memory' in self.system_status_labels:
                self.system_status_labels['memory'].setText(f"{memory_gb:.1f} GB")

            # Update cache size
            if 'cache_size' in self.system_status_labels:
                cache_size = self._calculate_cache_size()
                self.system_status_labels['cache_size'].setText(f"{cache_size:.1f} MB")

        except ImportError:
            # psutil not available, use placeholder values
            logger.info("psutil not available, using placeholder values")
        except Exception as e:
            logger.error(f"Error updating system status: {e}")

    def _calculate_cache_size(self) -> float:
        """Calculate total cache size in MB"""
        try:
            import os
            total_size = 0
            
            cache_dirs = [
                os.path.join(os.path.expanduser("~"), ".vidtanium", "cache"),
                os.path.join(os.path.expanduser("~"), ".cache", "vidtanium")
            ]
            
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    for dirpath, dirnames, filenames in os.walk(cache_dir):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                total_size += os.path.getsize(filepath)
                            except (OSError, IOError):
                                continue
            
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")
            return 0.0

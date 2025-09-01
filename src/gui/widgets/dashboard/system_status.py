"""
Enhanced Dashboard System Status Component with responsive design and modern theming
"""
from typing import TYPE_CHECKING, Optional, Dict, Union
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Slot
from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, SubtitleLabel, PrimaryPushButton,
    IconWidget, FluentIcon as FIF, InfoBar, InfoBarPosition,
    ElevatedCardWidget, HeaderCardWidget, CaptionLabel,
    VBoxLayout, setTheme, Theme, isDarkTheme
)

from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme
from ...utils.responsive import ResponsiveWidget, ResponsiveManager, ResponsiveContainer
from ...theme_manager import EnhancedThemeManager
from src.core.thread_pool import submit_task
from loguru import logger

if TYPE_CHECKING:
    from ...main_window import MainWindow


class EnhancedDashboardSystemStatus(ResponsiveWidget):
    """Enhanced system status component with responsive design and modern theming
    
    Features:
    - Responsive design that adapts to different screen sizes
    - Enhanced theming integration with EnhancedThemeManager
    - Modern card-based layout with gradient headers
    - Adaptive button layouts and spacing
    - Performance optimizations and smooth animations
    """
    
    def __init__(self, main_window: "MainWindow", theme_manager=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.theme_manager = theme_manager
        self.responsive_manager = ResponsiveManager.instance()
        self.system_status_labels: Dict[str, Union[BodyLabel, StrongBodyLabel]] = {}
        self.clear_cache_btn: Optional[PrimaryPushButton] = None
        self.open_settings_btn: Optional[PrimaryPushButton] = None
        
        self._setup_enhanced_ui()
        self._connect_signals()
        self._apply_enhanced_theming()
    
    def _setup_enhanced_ui(self):
        """Setup enhanced responsive UI"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Enhanced main card with responsive sizing
        card = ElevatedCardWidget()
        if current_bp.value in ['xs', 'sm']:
            card.setMinimumHeight(240)
            card.setMaximumHeight(400)
        else:
            card.setMinimumHeight(280)
            card.setMaximumHeight(500)
        
        # Set responsive size policy
        from PySide6.QtWidgets import QSizePolicy
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = VBoxLayout(card)
        if current_bp.value in ['xs', 'sm']:
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)
        else:
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(16)

        # Enhanced header with gradient background
        header_layout = self._create_enhanced_header()
        layout.addLayout(header_layout)

        # Responsive system info items
        self._create_responsive_system_items(layout)

        layout.addStretch()

        # Responsive quick actions
        actions_layout = self._create_responsive_actions()
        layout.addLayout(actions_layout)
        
        # Set up main layout using QFluentWidgets
        main_layout = VBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card)

    def _create_enhanced_header(self) -> QVBoxLayout:
        """Create enhanced header with gradient and responsive design"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        header_layout = VBoxLayout()
        header_layout.setSpacing(8)

        # Header card with gradient background
        header_card = HeaderCardWidget()
        if current_bp.value in ['xs', 'sm']:
            header_card.setFixedHeight(50)
        else:
            header_card.setFixedHeight(60)

        header_content = QHBoxLayout(header_card)
        if current_bp.value in ['xs', 'sm']:
            header_content.setContentsMargins(12, 8, 12, 8)
            header_content.setSpacing(8)
        else:
            header_content.setContentsMargins(16, 12, 16, 12)
            header_content.setSpacing(12)

        # Responsive icon
        icon = IconWidget(FIF.SETTING)
        if current_bp.value in ['xs', 'sm']:
            icon.setFixedSize(16, 16)
        else:
            icon.setFixedSize(20, 20)
        icon.setStyleSheet("color: white;")

        # Responsive title
        title = SubtitleLabel(tr("dashboard.system_status.title"))
        if current_bp.value in ['xs', 'sm']:
            title.setStyleSheet(f"""
                font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD}; 
                color: white;
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
                margin: 0;
            """)
        else:
            title.setStyleSheet(f"""
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD}; 
                color: white;
                font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
                margin: 0;
            """)

        header_content.addWidget(icon)
        header_content.addWidget(title)
        header_content.addStretch()

        header_layout.addWidget(header_card)
        return header_layout

    def _create_responsive_system_items(self, layout: QVBoxLayout):
        """Create responsive system information items"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        system_items = [
            ("dashboard.system_status.download_threads", "download_threads", "4 threads"),
            ("dashboard.system_status.temp_files", "temp_files", "12 MB"),
            ("dashboard.system_status.cache_size", "cache_size", "45 MB"),
            ("dashboard.system_status.network_usage", "network_usage", "2.1 MB/s")
        ]

        # Responsive container for items using QFluentWidgets
        items_container = ResponsiveContainer()
        items_layout = VBoxLayout(items_container)
        items_layout.setContentsMargins(0, 0, 0, 0)
        if current_bp.value in ['xs', 'sm']:
            items_layout.setSpacing(8)
        else:
            items_layout.setSpacing(12)

        for key, label_key, default_value in system_items:
            item = self._create_responsive_status_item(tr(key), default_value)
            # Store reference to the value label for updates
            value_label = item.findChild(StrongBodyLabel)
            if value_label:
                self.system_status_labels[label_key] = value_label
            items_layout.addWidget(item)

        layout.addWidget(items_container)

    def _create_responsive_status_item(self, label: str, value: str) -> QWidget:
        """Create a responsive system status item"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        item = QWidget()
        if current_bp.value in ['xs', 'sm']:
            item.setFixedHeight(28)
        else:
            item.setFixedHeight(32)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        if current_bp.value in ['xs', 'sm']:
            layout.setSpacing(6)
        else:
            layout.setSpacing(8)

        # Enhanced label styling using QFluentWidgets automatic theming
        label_widget = BodyLabel(label)
        # Let QFluentWidgets handle the styling automatically

        # Enhanced value styling using QFluentWidgets automatic theming
        value_widget = StrongBodyLabel(value)
        # Let QFluentWidgets handle the styling automatically

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)

        return item

    def _create_responsive_actions(self) -> QVBoxLayout:
        """Create responsive quick action buttons"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        actions_layout = VBoxLayout()
        if current_bp.value in ['xs', 'sm']:
            actions_layout.setSpacing(6)
        else:
            actions_layout.setSpacing(8)

        # Responsive button heights
        button_height = 32 if current_bp.value in ['xs', 'sm'] else 36

        # Enhanced clear cache button
        self.clear_cache_btn = PrimaryPushButton(tr("dashboard.actions.clear_cache"))
        self.clear_cache_btn.setIcon(FIF.BROOM)
        self.clear_cache_btn.setFixedHeight(button_height)

        # Enhanced settings button
        self.open_settings_btn = PrimaryPushButton(tr("dashboard.actions.open_settings"))
        self.open_settings_btn.setIcon(FIF.SETTING)
        self.open_settings_btn.setFixedHeight(button_height)

        actions_layout.addWidget(self.clear_cache_btn)
        actions_layout.addWidget(self.open_settings_btn)

        return actions_layout

    def _apply_enhanced_theming(self):
        """Apply enhanced theming to the system status component"""
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            accent_color = self.theme_manager.ACCENT_COLORS.get(
                self.theme_manager.get_current_accent(), '#0078D4'
            )
            
            # Apply enhanced styling
            self.setStyleSheet(f"""
                ElevatedCardWidget {{
                    background-color: {colors.get('surface', VidTaniumTheme.BG_SURFACE)};
                    border: 1px solid {colors.get('border', VidTaniumTheme.BORDER_LIGHT)};
                    border-radius: 12px;
                    box-shadow: 0 4px 12px {colors.get('shadow', 'rgba(0, 0, 0, 0.1)')};
                }}
                HeaderCardWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {accent_color}, stop:1 rgba(255, 255, 255, 0.1));
                    border: none;
                    border-radius: 8px;
                }}
                PrimaryPushButton {{
                    background-color: {colors.get('surface', VidTaniumTheme.BG_SURFACE)};
                    border: 2px solid {colors.get('border', VidTaniumTheme.BORDER_LIGHT)};
                    border-radius: 6px;
                    color: {colors.get('text_primary', VidTaniumTheme.TEXT_PRIMARY)};
                    font-weight: {VidTaniumTheme.FONT_WEIGHT_MEDIUM};
                    padding: 8px 16px;
                }}
                PrimaryPushButton:hover {{
                    background-color: {accent_color}15;
                    border-color: {accent_color};
                    color: {accent_color};
                }}
                PrimaryPushButton:pressed {{
                    background-color: {accent_color}25;
                }}
            """)
            
            # Special styling for settings button
            if self.open_settings_btn:
                self.open_settings_btn.setStyleSheet(f"""
                    PrimaryPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 {accent_color}, stop:1 rgba(255, 255, 255, 0.2));
                        border: none;
                        border-radius: 6px;
                        color: white;
                        font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
                        padding: 8px 16px;
                    }}
                    PrimaryPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 {accent_color}dd, stop:1 rgba(255, 255, 255, 0.3));
                    }}
                    PrimaryPushButton:pressed {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 {accent_color}aa, stop:1 rgba(255, 255, 255, 0.1));
                    }}
                """)

    def on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        logger.debug(f"System status adapting to breakpoint: {breakpoint}")
        # Recreate UI with new breakpoint
        self._setup_enhanced_ui()
        self._apply_enhanced_theming()

    def update_theme(self, theme_manager: Optional[EnhancedThemeManager] = None):
        """Update theme styling"""
        if theme_manager:
            self.theme_manager = theme_manager
        self._apply_enhanced_theming()

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


# Backward compatibility alias
DashboardSystemStatus = EnhancedDashboardSystemStatus

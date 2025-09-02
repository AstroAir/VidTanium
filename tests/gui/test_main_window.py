import pytest
import sys
from unittest.mock import patch, Mock, MagicMock
from typing import Any, Dict, Optional

# Mock PySide6 components for testing
class MockQWidget:
    def __init__(self):
        self.object_name = ""
        self.minimum_size = (0, 0)
        self.size_value = (800, 600)
        self.visible = False
        
    def setObjectName(self, name):
        self.object_name = name
        
    def setMinimumSize(self, width, height):
        self.minimum_size = (width, height)
        
    def minimumWidth(self):
        return self.minimum_size[0]
        
    def minimumHeight(self):
        return self.minimum_size[1]
        
    def resize(self, width, height):
        self.size_value = (width, height)
        
    def size(self):
        mock_size = Mock()
        mock_size.width.return_value = self.size_value[0]
        mock_size.height.return_value = self.size_value[1]
        return mock_size
        
    def show(self):
        self.visible = True

class MockQApplication:
    @staticmethod
    def primaryScreen():
        mock_screen = Mock()
        mock_geometry = Mock()
        mock_geometry.width.return_value = 1920
        mock_geometry.height.return_value = 1080
        mock_screen.availableGeometry.return_value = mock_geometry
        return mock_screen

class MockQTimer:
    def __init__(self):
        self.timeout = Mock()
        self.interval = 0
        self.running = False
        
    def start(self, interval=None):
        if interval:
            self.interval = interval
        self.running = True
        
    def stop(self):
        self.running = False

class MockFluentWindow(MockQWidget):
    def __init__(self):
        super().__init__()
        self.navigationInterface = Mock()
        self.sub_interfaces = []
        
    def addSubInterface(self, interface, icon, text, position):
        self.sub_interfaces.append({
            'interface': interface,
            'icon': icon,
            'text': text,
            'position': position
        })
        
    def setWindowIcon(self, icon):
        pass
        
    def resizeEvent(self, event):
        pass

class MockDownloadManager:
    def __init__(self):
        self.on_task_progress = None
        self.on_task_status_changed = None
        self.on_task_completed = None
        self.on_task_failed = None
        self.tasks = {}
        
    def get_all_tasks(self):
        return self.tasks
        
    def start_task(self, task_id):
        pass
        
    def pause_task(self, task_id):
        pass
        
    def resume_task(self, task_id):
        pass
        
    def cancel_task(self, task_id):
        pass
        
    def remove_task(self, task_id):
        if task_id in self.tasks:
            del self.tasks[task_id]

class MockSettings:
    def __init__(self):
        self.data = {
            "ui": {
                "show_notifications": True,
                "auto_save_interval": 300
            }
        }
        
    def get(self, section, key, default=None):
        return self.data.get(section, {}).get(key, default)

class MockApp:
    def __init__(self):
        self.tray_icon = Mock()
        
    def send_notification(self, title, message, icon=None, duration=5000):
        pass

# Mock the PySide6 imports
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()
sys.modules['PySide6.QtWidgets'].QWidget = MockQWidget
sys.modules['PySide6.QtWidgets'].QApplication = MockQApplication
sys.modules['PySide6.QtCore'].QTimer = MockQTimer
sys.modules['PySide6.QtCore'].Qt = Mock()
sys.modules['PySide6.QtCore'].Slot = lambda: lambda f: f

# Mock qfluentwidgets
sys.modules['qfluentwidgets'] = Mock()
sys.modules['qfluentwidgets'].FluentWindow = MockFluentWindow
sys.modules['qfluentwidgets'].FluentIcon = Mock()
sys.modules['qfluentwidgets'].NavigationItemPosition = Mock()

# Mock GUI components
sys.modules['src.gui.widgets.navigation'] = Mock()
sys.modules['src.gui.widgets.dashboard'] = Mock()
sys.modules['src.gui.widgets.progress'] = Mock()
sys.modules['src.gui.widgets.task_manager'] = Mock()
sys.modules['src.gui.widgets.log.log_viewer'] = Mock()
sys.modules['src.gui.widgets.dashboard.dashboard_interface'] = Mock()
sys.modules['src.gui.widgets.settings'] = Mock()
sys.modules['src.gui.theme_manager'] = Mock()
sys.modules['src.gui.utils.responsive'] = Mock()
sys.modules['src.gui.dialogs.task_dialog'] = Mock()
sys.modules['src.gui.dialogs.about_dialog'] = Mock()
sys.modules['src.gui.dialogs.batch_url_dialog'] = Mock()
sys.modules['src.gui.utils.design_system'] = Mock()
sys.modules['src.gui.utils.formatters'] = Mock()
sys.modules['src.gui.utils.i18n'] = Mock()

# Mock core components
sys.modules['src.core.downloader'] = Mock()

# Now import the actual module
from src.gui.main_window import MainWindow


class TestMainWindow:
    """Test suite for MainWindow class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_app = MockApp()
        self.mock_download_manager = MockDownloadManager()
        self.mock_settings = MockSettings()
        self.mock_theme_manager = Mock()

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    @patch('src.gui.main_window.TaskManager')
    @patch('src.gui.main_window.LogViewer')
    @patch('src.gui.main_window.SettingsInterface')
    def test_initialization(self, mock_settings_interface, mock_log_viewer, 
                           mock_task_manager, mock_dashboard, mock_responsive_manager):
        """Test MainWindow initialization."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Check basic initialization
        assert window.app == self.mock_app
        assert window.download_manager == self.mock_download_manager
        assert window.settings == self.mock_settings
        assert window.theme_manager == self.mock_theme_manager
        assert window._force_close is False

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    @patch('src.gui.main_window.QApplication.primaryScreen')
    def test_responsive_window_setup(self, mock_primary_screen, mock_dashboard, mock_responsive_manager):
        """Test responsive window setup."""
        # Mock screen
        mock_screen = Mock()
        mock_geometry = Mock()
        mock_geometry.width.return_value = 1920
        mock_geometry.height.return_value = 1080
        mock_screen.availableGeometry.return_value = mock_geometry
        mock_primary_screen.return_value = mock_screen
        
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Check that responsive manager methods were called
        mock_responsive_instance.add_breakpoint_callback.assert_called()
        mock_responsive_instance.add_orientation_callback.assert_called()
        mock_responsive_instance.update_for_size.assert_called()

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_breakpoint_changed_callback(self, mock_dashboard, mock_responsive_manager):
        """Test breakpoint change handling."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Test small breakpoint
        window._on_breakpoint_changed('xs')
        
        # Test large breakpoint
        window._on_breakpoint_changed('lg')
        
        # Should not raise exceptions
        assert True

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_orientation_changed_callback(self, mock_dashboard, mock_responsive_manager):
        """Test orientation change handling."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Test orientation changes
        window._on_orientation_changed('portrait')
        window._on_orientation_changed('landscape')
        
        # Should not raise exceptions
        assert True

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    @patch('src.gui.main_window.TaskManager')
    def test_download_manager_signal_connections(self, mock_task_manager, mock_dashboard, mock_responsive_manager):
        """Test download manager signal connections."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Check that callbacks are assigned
        assert self.mock_download_manager.on_task_progress == window.on_task_progress
        assert self.mock_download_manager.on_task_status_changed == window.on_task_status_changed
        assert self.mock_download_manager.on_task_completed == window.on_task_completed
        assert self.mock_download_manager.on_task_failed == window.on_task_failed

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_task_progress_callback(self, mock_dashboard, mock_responsive_manager):
        """Test task progress callback."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Test progress callback
        progress_data = {
            "completed": 50,
            "total": 100,
            "speed": 1024.0
        }
        
        # Should not raise exception
        window.on_task_progress("test_task", progress_data)

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_task_completed_callback(self, mock_dashboard, mock_responsive_manager):
        """Test task completion callback."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Test completion callback
        window.on_task_completed("test_task", "Task completed successfully")
        
        # Should not raise exception
        assert True

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_task_failed_callback(self, mock_dashboard, mock_responsive_manager):
        """Test task failure callback."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Test failure callback
        window.on_task_failed("test_task", "Task failed with error")
        
        # Should not raise exception
        assert True

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_handle_task_action(self, mock_dashboard, mock_responsive_manager):
        """Test task action handling."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Test various actions
        window.handle_task_action("start", "test_task")
        window.handle_task_action("pause", "test_task")
        window.handle_task_action("resume", "test_task")
        window.handle_task_action("cancel", "test_task")
        window.handle_task_action("remove", "test_task")
        
        # Should not raise exceptions
        assert True

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_auto_save_setup(self, mock_dashboard, mock_responsive_manager):
        """Test auto save timer setup."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Check that auto save timer is set up
        assert hasattr(window, 'auto_save_timer')
        assert window.auto_save_timer.running

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_statistics_update_timer(self, mock_dashboard, mock_responsive_manager):
        """Test statistics update timer."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Check that stats update timer is set up
        assert hasattr(window, 'stats_update_timer')

    @patch('src.gui.main_window.ResponsiveManager')
    @patch('src.gui.main_window.Dashboard')
    def test_task_refresh_timer(self, mock_dashboard, mock_responsive_manager):
        """Test task refresh timer."""
        # Mock responsive manager
        mock_responsive_instance = Mock()
        mock_responsive_manager.instance.return_value = mock_responsive_instance
        
        # Mock dashboard
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_interface.return_value = MockQWidget()
        mock_dashboard.return_value = mock_dashboard_instance
        
        window = MainWindow(
            self.mock_app,
            self.mock_download_manager,
            self.mock_settings,
            self.mock_theme_manager
        )
        
        # Check that task refresh timer is set up
        assert hasattr(window, 'task_refresh_timer')
        assert window.task_refresh_timer.running


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

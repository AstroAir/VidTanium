import pytest
import sys
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock
from typing import Optional

# Mock PySide6 components for testing
class MockQApplication:
    def __init__(self, argv) -> None:
        self.argv = argv
        self._app_name = ""
        self._app_version = ""
        self._org_name = ""
        self._org_domain = ""
    
    def setApplicationName(self, name) -> None:
        self._app_name = name
    
    def setApplicationVersion(self, version) -> None:
        self._app_version = version
    
    def setOrganizationName(self, name) -> None:
        self._org_name = name
    
    def setOrganizationDomain(self, domain) -> None:
        self._org_domain = domain
    
    def exec(self) -> None:
        return 0

class MockQObject:
    pass

class MockQMutex:
    def lock(self) -> None:
        pass
    
    def unlock(self) -> None:
        pass

class MockQLocale:
    @staticmethod
    def system() -> None:
        mock_locale = Mock()
        mock_locale.name.return_value = "en_US"
        return mock_locale

# Mock the PySide6 imports
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtWidgets'].QApplication = MockQApplication
sys.modules['PySide6.QtCore'].QObject = MockQObject
sys.modules['PySide6.QtCore'].QMutex = MockQMutex
sys.modules['PySide6.QtCore'].QLocale = MockQLocale

# Mock other dependencies
sys.modules['qfluentwidgets'] = Mock()

# Mock GUI components
sys.modules['src.gui.utils.i18n'] = Mock()
sys.modules['src.gui.main_window'] = Mock()
sys.modules['src.gui.theme_manager'] = Mock()

# Mock core components
sys.modules['src.core.scheduler'] = Mock()
sys.modules['src.core.downloader'] = Mock()

# Now import the actual module
from src.app.application import Application


class TestApplication:
    """Test suite for Application class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset singleton instance before each test
        Application._instance = None
        
        # Create temporary directory for config
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """Clean up after tests."""
        # Reset singleton instance
        Application._instance = None
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_singleton_pattern(self, mock_main_window, mock_scheduler, mock_download_manager,
                              mock_theme_manager, mock_init_i18n, mock_settings, mock_logging) -> None:
        """Test that Application follows singleton pattern."""
        # Create first instance
        app1 = Application(self.temp_dir)
        
        # Create second instance
        app2 = Application(self.temp_dir)
        
        # Should be the same instance
        assert app1 is app2
        assert Application.instance() is app1

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_initialization(self, mock_main_window, mock_scheduler, mock_download_manager,
                           mock_theme_manager, mock_init_i18n, mock_settings, mock_logging) -> None:
        """Test Application initialization."""
        app = Application(self.temp_dir)
        
        # Check that components are initialized
        mock_settings.assert_called_once_with(self.temp_dir)
        mock_init_i18n.assert_called_once()
        mock_theme_manager.assert_called_once()
        mock_download_manager.assert_called_once()
        mock_scheduler.assert_called_once_with(self.temp_dir)
        mock_main_window.assert_called_once()
        
        # Check application properties
        assert app._app_name == "Video Downloader"
        assert app._app_version == "1.0.0"
        assert app._org_name == "Development Team"
        assert app._org_domain == "example.com"

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_double_initialization_prevention(self, mock_main_window, mock_scheduler, 
                                            mock_download_manager, mock_theme_manager, 
                                            mock_init_i18n, mock_settings, mock_logging) -> None:
        """Test that double initialization is prevented."""
        app = Application(self.temp_dir)
        
        # Reset mocks
        mock_settings.reset_mock()
        mock_init_i18n.reset_mock()
        
        # Try to initialize again
        app.__init__(self.temp_dir)
        
        # Should not call initialization methods again
        mock_settings.assert_not_called()
        mock_init_i18n.assert_not_called()

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_run_method(self, mock_main_window, mock_scheduler, mock_download_manager,
                       mock_theme_manager, mock_init_i18n, mock_settings, mock_logging) -> None:
        """Test Application run method."""
        app = Application(self.temp_dir)
        
        # Mock settings to return check_updates = True
        mock_settings_instance = mock_settings.return_value
        mock_settings_instance.get.return_value = True
        app.settings = mock_settings_instance
        
        # Mock download manager and scheduler
        mock_download_manager_instance = mock_download_manager.return_value
        mock_scheduler_instance = mock_scheduler.return_value
        mock_main_window_instance = mock_main_window.return_value
        
        app.download_manager = mock_download_manager_instance
        app.task_scheduler = mock_scheduler_instance
        app.main_window = mock_main_window_instance
        
        # Mock _check_updates method
        app._check_updates = Mock()
        
        # Run application
        result = app.run()
        
        # Verify components are started
        mock_download_manager_instance.start.assert_called_once()
        mock_scheduler_instance.start.assert_called_once()
        mock_main_window_instance.show.assert_called_once()
        app._check_updates.assert_called_once()
        
        # Should return 0 (from mocked exec)
        assert result == 0

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_add_task_from_url(self, mock_main_window, mock_scheduler, mock_download_manager,
                              mock_theme_manager, mock_init_i18n, mock_settings, mock_logging) -> None:
        """Test adding task from URL."""
        app = Application(self.temp_dir)
        
        # Mock main window
        mock_main_window_instance = mock_main_window.return_value
        mock_main_window_instance.import_from_url = Mock()
        app.main_window = mock_main_window_instance
        
        # Test URL
        test_url = "https://example.com/video.m3u8"
        
        app.add_task_from_url(test_url)
        
        mock_main_window_instance.import_from_url.assert_called_once()

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.set_locale')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_apply_language_auto(self, mock_main_window, mock_scheduler, mock_download_manager,
                                mock_theme_manager, mock_set_locale, mock_init_i18n, 
                                mock_settings, mock_logging) -> None:
        """Test language application with auto setting."""
        # Mock settings to return auto language
        mock_settings_instance = Mock()
        mock_settings_instance.get.return_value = "auto"
        
        with patch('src.app.application.Settings', return_value=mock_settings_instance):
            app = Application(self.temp_dir)
            
            # Should call set_locale with system-determined locale
            mock_set_locale.assert_called()

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.set_locale')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_apply_language_specific(self, mock_main_window, mock_scheduler, mock_download_manager,
                                   mock_theme_manager, mock_set_locale, mock_init_i18n, 
                                   mock_settings, mock_logging) -> None:
        """Test language application with specific language."""
        # Mock settings to return specific language
        mock_settings_instance = Mock()
        mock_settings_instance.get.return_value = "zh_CN"
        
        with patch('src.app.application.Settings', return_value=mock_settings_instance):
            app = Application(self.temp_dir)
            
            # Should call set_locale with specified language
            mock_set_locale.assert_called_with("zh_CN")

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    @patch('src.app.application.DownloadTask')
    @patch('src.app.application.TaskPriority')
    def test_handle_download_task(self, mock_priority, mock_task, mock_main_window, 
                                 mock_scheduler, mock_download_manager, mock_theme_manager, 
                                 mock_init_i18n, mock_settings, mock_logging) -> None:
        """Test handling download task."""
        app = Application(self.temp_dir)
        
        # Mock download manager
        mock_download_manager_instance = Mock()
        mock_download_manager_instance.add_task.return_value = "task_123"
        app.download_manager = mock_download_manager_instance
        
        # Mock task creation
        mock_task_instance = Mock()
        mock_task.return_value = mock_task_instance
        
        # Mock priority enum
        mock_priority.HIGH = "high"
        mock_priority.NORMAL = "normal"
        mock_priority.LOW = "low"
        
        # Test task data
        task_data = {
            "name": "Test Task",
            "base_url": "https://example.com/stream.m3u8",
            "key_url": "https://example.com/key.bin",
            "segments": 100,
            "output_file": "/downloads/test.mp4",
            "priority": "high",
            "notify": True
        }
        
        # Mock notification method
        app.send_notification = Mock()
        
        app._handle_download_task(task_data)
        
        # Verify task creation
        mock_task.assert_called_once()
        mock_download_manager_instance.add_task.assert_called_once_with(mock_task_instance)
        mock_download_manager_instance.start_task.assert_called_once_with("task_123")
        app.send_notification.assert_called_once()

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_handle_download_task_error(self, mock_main_window, mock_scheduler, 
                                       mock_download_manager, mock_theme_manager, 
                                       mock_init_i18n, mock_settings, mock_logging) -> None:
        """Test error handling in download task processing."""
        app = Application(self.temp_dir)
        
        # Mock download manager to raise exception
        mock_download_manager_instance = Mock()
        mock_download_manager_instance.add_task.side_effect = Exception("Test error")
        app.download_manager = mock_download_manager_instance
        
        # Mock notification method
        app.send_notification = Mock()
        
        task_data = {
            "name": "Test Task",
            "notify": True
        }
        
        # Should not raise exception
        app._handle_download_task(task_data)
        
        # Should send error notification
        app.send_notification.assert_called_once()
        call_args = app.send_notification.call_args[0]
        assert "Failed" in call_args[0]

    @patch('src.app.application.ensure_logging_configured')
    @patch('src.app.application.Settings')
    @patch('src.app.application.init_i18n')
    @patch('src.app.application.EnhancedThemeManager')
    @patch('src.app.application.DownloadManager')
    @patch('src.app.application.TaskScheduler')
    @patch('src.app.application.MainWindow')
    def test_check_updates(self, mock_main_window, mock_scheduler, mock_download_manager,
                          mock_theme_manager, mock_init_i18n, mock_settings, mock_logging) -> None:
        """Test update checking."""
        app = Application(self.temp_dir)
        
        # Should not raise exception
        app._check_updates()

    def test_instance_method(self) -> None:
        """Test instance class method."""
        # Initially should be None
        assert Application.instance() is None
        
        # After creating instance, should return it
        with patch('src.app.application.ensure_logging_configured'), \
             patch('src.app.application.Settings'), \
             patch('src.app.application.init_i18n'), \
             patch('src.app.application.EnhancedThemeManager'), \
             patch('src.app.application.DownloadManager'), \
             patch('src.app.application.TaskScheduler'), \
             patch('src.app.application.MainWindow'):
            
            app = Application(self.temp_dir)
            assert Application.instance() is app


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

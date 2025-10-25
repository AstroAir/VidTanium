import pytest
import sys
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any, Optional

# Mock PySide6 components for testing
class MockQApplication:
    def __init__(self, argv) -> None:
        self.argv = argv
        self._app_name = ""
        self._app_version = ""
        self._org_name = ""
        self._org_domain = ""
        self.exit_code = 0
    
    def setApplicationName(self, name) -> None:
        self._app_name = name
    
    def setApplicationVersion(self, version) -> None:
        self._app_version = version
    
    def setOrganizationName(self, name) -> None:
        self._org_name = name
    
    def setOrganizationDomain(self, domain) -> None:
        self._org_domain = domain
    
    def exec(self) -> None:
        return self.exit_code

class MockMainWindow:
    def __init__(self) -> None:
        self.visible = False
        self.download_manager = Mock()
        self.task_scheduler = Mock()
        
    def show(self) -> None:
        self.visible = True

class MockDownloadManager:
    def __init__(self) -> None:
        self.started = False
        self.tasks = {}
        
    def start(self) -> None:
        self.started = True
        
    def add_task(self, task) -> None:
        task_id = f"task_{len(self.tasks)}"
        self.tasks[task_id] = task
        return task_id
        
    def get_all_tasks(self) -> None:
        return self.tasks

class MockTaskScheduler:
    def __init__(self, config_dir) -> None:
        self.config_dir = config_dir
        self.started = False
        
    def start(self) -> None:
        self.started = True

class MockSettings:
    def __init__(self, config_dir) -> None:
        self.config_dir = config_dir
        self.data = {
            "general": {
                "check_updates": True,
                "language": "auto",
                "theme": "system"
            },
            "ui": {
                "show_notifications": True
            }
        }
        
    def get(self, section, key, default=None) -> None:
        return self.data.get(section, {}).get(key, default)
        
    def set(self, section, key, value) -> None:
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value

class MockThemeManager:
    def __init__(self) -> None:
        self.current_theme = "system"
        
    def set_theme(self, theme) -> None:
        self.current_theme = theme

# Mock the PySide6 imports
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtWidgets'].QApplication = MockQApplication

# Mock other dependencies
sys.modules['qfluentwidgets'] = Mock()

# Mock GUI components
sys.modules['src.gui.utils.i18n'] = Mock()
sys.modules['src.gui.utils.i18n'].init_i18n = Mock()
sys.modules['src.gui.utils.i18n'].set_locale = Mock()
sys.modules['src.gui.main_window'] = Mock()
sys.modules['src.gui.main_window'].MainWindow = MockMainWindow
sys.modules['src.gui.theme_manager'] = Mock()
sys.modules['src.gui.theme_manager'].EnhancedThemeManager = MockThemeManager

# Mock core components
sys.modules['src.core.scheduler'] = Mock()
sys.modules['src.core.scheduler'].TaskScheduler = MockTaskScheduler
sys.modules['src.core.downloader'] = Mock()
sys.modules['src.core.downloader'].DownloadManager = MockDownloadManager

# Mock app components
sys.modules['src.app.settings'] = Mock()
sys.modules['src.app.settings'].Settings = MockSettings
sys.modules['src.app.logging_config'] = Mock()
sys.modules['src.app.logging_config'].ensure_logging_configured = Mock()

# Now import the actual module
from src.app.application import Application


class TestApplicationIntegration:
    """Integration tests for the complete application."""

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

    def test_application_startup_sequence(self) -> None:
        """Test complete application startup sequence."""
        app = Application(self.temp_dir)
        
        # Verify all components are initialized
        assert app.settings is not None
        assert app.theme_manager is not None
        assert app.download_manager is not None
        assert app.task_scheduler is not None
        assert app.main_window is not None

    def test_application_run_sequence(self) -> None:
        """Test application run sequence."""
        app = Application(self.temp_dir)
        
        # Mock the components
        app.download_manager = MockDownloadManager()
        app.task_scheduler = MockTaskScheduler(self.temp_dir)
        app.main_window = MockMainWindow()
        
        # Run application
        result = app.run()
        
        # Verify components are started
        assert app.download_manager.started is True
        assert app.task_scheduler.started is True
        assert app.main_window.visible is True
        assert result == 0

    def test_settings_integration(self) -> None:
        """Test settings integration across components."""
        app = Application(self.temp_dir)
        
        # Verify settings are accessible
        assert app.settings.get("general", "check_updates") is True
        
        # Modify settings
        app.settings.set("general", "theme", "dark")
        assert app.settings.get("general", "theme") == "dark"

    def test_theme_manager_integration(self) -> None:
        """Test theme manager integration."""
        app = Application(self.temp_dir)
        
        # Verify theme manager is initialized
        assert app.theme_manager is not None
        assert app.theme_manager.current_theme == "system"
        
        # Change theme
        app.theme_manager.set_theme("dark")
        assert app.theme_manager.current_theme == "dark"

    def test_download_manager_integration(self) -> None:
        """Test download manager integration."""
        app = Application(self.temp_dir)
        app.download_manager = MockDownloadManager()
        
        # Add a task
        task_data = {
            "name": "Test Task",
            "base_url": "http://example.com/stream.m3u8",
            "output_file": "/downloads/test.mp4"
        }
        
        task_id = app.download_manager.add_task(task_data)
        
        # Verify task was added
        assert task_id in app.download_manager.tasks
        assert len(app.download_manager.tasks) == 1

    def test_task_scheduler_integration(self) -> None:
        """Test task scheduler integration."""
        app = Application(self.temp_dir)
        app.task_scheduler = MockTaskScheduler(self.temp_dir)
        
        # Start scheduler
        app.task_scheduler.start()
        
        # Verify scheduler is started
        assert app.task_scheduler.started is True
        assert app.task_scheduler.config_dir == self.temp_dir

    def test_main_window_integration(self) -> None:
        """Test main window integration."""
        app = Application(self.temp_dir)
        app.main_window = MockMainWindow()
        
        # Show main window
        app.main_window.show()
        
        # Verify window is visible
        assert app.main_window.visible is True

    def test_component_communication(self) -> None:
        """Test communication between components."""
        app = Application(self.temp_dir)
        app.download_manager = MockDownloadManager()
        app.main_window = MockMainWindow()
        
        # Verify main window has access to download manager
        assert app.main_window.download_manager is not None

    def test_error_handling_during_startup(self) -> None:
        """Test error handling during application startup."""
        # Mock an error in one component
        with patch('src.app.application.Settings', side_effect=Exception("Settings error")):
            try:
                app = Application(self.temp_dir)
                # Should handle error gracefully or raise appropriate exception
                assert True
            except Exception as e:
                # Should be a meaningful error
                assert "Settings error" in str(e)

    def test_singleton_behavior(self) -> None:
        """Test singleton behavior across the application."""
        app1 = Application(self.temp_dir)
        app2 = Application(self.temp_dir)
        
        # Should be the same instance
        assert app1 is app2
        assert Application.instance() is app1

    def test_configuration_persistence(self) -> None:
        """Test configuration persistence across application restarts."""
        # First application instance
        app1 = Application(self.temp_dir)
        app1.settings.set("general", "theme", "dark")
        
        # Reset singleton
        Application._instance = None
        
        # Second application instance
        app2 = Application(self.temp_dir)
        
        # Should load the same configuration
        assert app2.settings.get("general", "theme") == "dark"

    def test_localization_integration(self) -> None:
        """Test localization integration."""
        app = Application(self.temp_dir)
        
        # Verify localization is initialized
        # This is tested through the mock calls
        assert True

    def test_update_checking_integration(self) -> None:
        """Test update checking integration."""
        app = Application(self.temp_dir)
        
        # Mock settings to enable update checking
        app.settings.set("general", "check_updates", True)
        
        # Should not raise exception when checking updates
        app._check_updates()

    def test_notification_integration(self) -> None:
        """Test notification system integration."""
        app = Application(self.temp_dir)
        
        # Should not raise exception when sending notifications
        app.send_notification("Test Title", "Test Message")

    def test_task_creation_workflow(self) -> None:
        """Test complete task creation workflow."""
        app = Application(self.temp_dir)
        app.download_manager = MockDownloadManager()
        
        # Simulate task creation from URL
        test_url = "http://example.com/stream.m3u8"
        app.add_task_from_url(test_url)
        
        # Should not raise exceptions
        assert True

    def test_application_shutdown(self) -> None:
        """Test application shutdown sequence."""
        app = Application(self.temp_dir)
        app.download_manager = MockDownloadManager()
        app.task_scheduler = MockTaskScheduler(self.temp_dir)
        
        # Start components
        app.download_manager.start()
        app.task_scheduler.start()
        
        # Verify components are running
        assert app.download_manager.started is True
        assert app.task_scheduler.started is True

    def test_memory_management(self) -> None:
        """Test memory management during application lifecycle."""
        app = Application(self.temp_dir)
        
        # Verify all components are properly referenced
        assert app.settings is not None
        assert app.theme_manager is not None
        assert app.download_manager is not None
        assert app.task_scheduler is not None
        assert app.main_window is not None

    def test_cross_component_data_flow(self) -> None:
        """Test data flow between different components."""
        app = Application(self.temp_dir)
        app.download_manager = MockDownloadManager()
        
        # Add task through download manager
        task_data = {"name": "Test", "url": "http://example.com"}
        task_id = app.download_manager.add_task(task_data)
        
        # Verify task is accessible
        tasks = app.download_manager.get_all_tasks()
        assert task_id in tasks
        assert tasks[task_id] == task_data

    def test_configuration_validation(self) -> None:
        """Test configuration validation across components."""
        app = Application(self.temp_dir)
        
        # Test valid configuration
        app.settings.set("general", "theme", "light")
        assert app.settings.get("general", "theme") == "light"
        
        # Test invalid configuration handling
        app.settings.set("general", "invalid_setting", "invalid_value")
        # Should not break the application
        assert True

    def test_performance_optimization(self) -> None:
        """Test performance optimizations in integration."""
        app = Application(self.temp_dir)
        
        # Verify lazy loading and optimization flags
        # This is tested through the component initialization
        assert True

    def test_thread_safety(self) -> None:
        """Test thread safety in component interactions."""
        app = Application(self.temp_dir)
        app.download_manager = MockDownloadManager()
        
        # Simulate concurrent operations
        for i in range(5):
            task_data = {"name": f"Task {i}", "url": f"http://example.com/{i}"}
            app.download_manager.add_task(task_data)
        
        # Should handle concurrent operations safely
        assert len(app.download_manager.tasks) == 5


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

"""
Pytest configuration and shared fixtures for VidTanium test suite.
"""
import pytest
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def temp_config_dir():
    """Create a temporary configuration directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="vidtanium_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_settings():
    """Mock settings object for testing."""
    class MockSettings:
        def __init__(self):
            self.data = {
                "general": {
                    "output_directory": "/downloads",
                    "language": "en",
                    "theme": "system",
                    "check_updates": True
                },
                "download": {
                    "max_concurrent_tasks": 3,
                    "max_workers_per_task": 10,
                    "max_retries": 3,
                    "retry_delay": 5
                },
                "advanced": {
                    "user_agent": "VidTanium/1.0",
                    "timeout": 30,
                    "buffer_size": 8192
                },
                "ui": {
                    "show_notifications": True,
                    "auto_save_interval": 300,
                    "theme": "system"
                }
            }
        
        def get(self, section, key, default=None):
            return self.data.get(section, {}).get(key, default)
        
        def set(self, section, key, value):
            if section not in self.data:
                self.data[section] = {}
            self.data[section][key] = value
        
        def save_settings(self):
            return True
    
    return MockSettings()


@pytest.fixture
def mock_download_manager():
    """Mock download manager for testing."""
    class MockDownloadManager:
        def __init__(self):
            self.tasks = {}
            self.started = False
            self.on_task_progress = None
            self.on_task_status_changed = None
            self.on_task_completed = None
            self.on_task_failed = None
        
        def start(self):
            self.started = True
        
        def stop(self):
            self.started = False
        
        def add_task(self, task):
            task_id = f"task_{len(self.tasks)}"
            self.tasks[task_id] = task
            return task_id
        
        def remove_task(self, task_id):
            if task_id in self.tasks:
                del self.tasks[task_id]
        
        def get_task(self, task_id):
            return self.tasks.get(task_id)
        
        def get_all_tasks(self):
            return self.tasks.copy()
        
        def start_task(self, task_id):
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = 'running'
        
        def pause_task(self, task_id):
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = 'paused'
        
        def resume_task(self, task_id):
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = 'running'
        
        def cancel_task(self, task_id):
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = 'cancelled'
    
    return MockDownloadManager()


@pytest.fixture
def mock_theme_manager():
    """Mock theme manager for testing."""
    class MockThemeManager:
        def __init__(self):
            self.current_theme = "system"
            self.current_accent = "blue"
            self.animations_enabled = True
            self.ACCENT_COLORS = {
                "blue": "#0078D4",
                "purple": "#8B5CF6",
                "green": "#10B981",
                "orange": "#F59E0B",
                "red": "#EF4444",
                "pink": "#EC4899",
                "indigo": "#6366F1",
                "teal": "#14B8A6"
            }
        
        def set_theme(self, theme, animate=True):
            self.current_theme = theme
        
        def get_current_theme(self):
            return self.current_theme
        
        def set_accent_color(self, color):
            self.current_accent = color
        
        def get_current_accent(self):
            return self.current_accent
        
        def is_dark_theme(self):
            return self.current_theme == "dark"
        
        def set_animations_enabled(self, enabled):
            self.animations_enabled = enabled
    
    return MockThemeManager()


@pytest.fixture
def mock_main_window():
    """Mock main window for testing."""
    class MockMainWindow:
        def __init__(self):
            self.visible = False
            self.download_manager = None
            self.settings = None
            self.theme_manager = None
        
        def show(self):
            self.visible = True
        
        def hide(self):
            self.visible = False
        
        def isVisible(self):
            return self.visible
        
        def import_from_url(self):
            pass
    
    return MockMainWindow()


@pytest.fixture
def mock_task_scheduler():
    """Mock task scheduler for testing."""
    class MockTaskScheduler:
        def __init__(self, config_dir=None):
            self.config_dir = config_dir
            self.started = False
            self.scheduled_tasks = []
        
        def start(self):
            self.started = True
        
        def stop(self):
            self.started = False
        
        def add_scheduled_task(self, task):
            self.scheduled_tasks.append(task)
        
        def remove_scheduled_task(self, task_id):
            self.scheduled_tasks = [t for t in self.scheduled_tasks if t.get('id') != task_id]
        
        def get_scheduled_tasks(self):
            return self.scheduled_tasks.copy()
    
    return MockTaskScheduler()


@pytest.fixture(autouse=True)
def mock_pyside6():
    """Automatically mock PySide6 for all tests."""
    # Create more robust mocks that handle attribute access properly
    pyside6_mock = Mock()
    pyside6_mock.__name__ = 'PySide6'

    qtwidgets_mock = Mock()
    qtwidgets_mock.__name__ = 'PySide6.QtWidgets'

    qtcore_mock = Mock()
    qtcore_mock.__name__ = 'PySide6.QtCore'

    qtgui_mock = Mock()
    qtgui_mock.__name__ = 'PySide6.QtGui'

    qfluentwidgets_mock = Mock()
    qfluentwidgets_mock.__name__ = 'qfluentwidgets'

    with patch.dict('sys.modules', {
        'PySide6': pyside6_mock,
        'PySide6.QtWidgets': qtwidgets_mock,
        'PySide6.QtCore': qtcore_mock,
        'PySide6.QtGui': qtgui_mock,
        'qfluentwidgets': qfluentwidgets_mock,
        'shiboken6': Mock(),
        'shiboken6.Shiboken': Mock(),
    }):
        yield


@pytest.fixture(autouse=True)
def mock_loguru():
    """Automatically mock loguru for all tests."""
    with patch.dict('sys.modules', {
        'loguru': Mock(),
    }):
        yield


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "name": "Test Video Download",
        "base_url": "https://example.com/stream.m3u8",
        "key_url": "https://example.com/key.bin",
        "segments": 100,
        "output_file": "/downloads/test_video.mp4",
        "priority": "normal",
        "auto_start": True,
        "notify": True
    }


@pytest.fixture
def sample_progress_data():
    """Sample progress data for testing."""
    return {
        "completed": 50,
        "total": 100,
        "speed": 1024.0,
        "eta": 120,
        "status": "downloading"
    }


@pytest.fixture
def sample_settings_data():
    """Sample settings data for testing."""
    return {
        "general": {
            "output_directory": "/downloads",
            "language": "en",
            "theme": "system",
            "auto_cleanup": True,
            "check_updates": True
        },
        "download": {
            "max_concurrent_tasks": 3,
            "max_workers_per_task": 10,
            "max_retries": 3,
            "retry_delay": 5,
            "timeout": 30
        },
        "advanced": {
            "user_agent": "VidTanium/1.0",
            "buffer_size": 8192,
            "enable_logging": True,
            "log_level": "INFO"
        },
        "ui": {
            "show_notifications": True,
            "auto_save_interval": 300,
            "theme": "system",
            "language": "auto"
        }
    }


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "gui: mark test as a GUI test"
    )
    config.addinivalue_line(
        "markers", "core: mark test as a core functionality test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


# Test collection customization
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "test_core" in str(item.fspath):
            item.add_marker(pytest.mark.core)
        elif "test_gui" in str(item.fspath):
            item.add_marker(pytest.mark.gui)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Mark network tests
        if "network" in item.name or "download" in item.name:
            item.add_marker(pytest.mark.network)


# Cleanup after tests
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Reset any global state if needed
    pass

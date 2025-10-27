"""
Pytest configuration and fixtures for CLI tests.
"""
import pytest
import sys
import os
import tempfile
import argparse
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


@pytest.fixture
def mock_cli_args():
    """Mock command-line arguments for CLI testing."""
    args = argparse.Namespace()
    args.no_gui = True
    args.debug = False
    args.url = None
    args.output_dir = None
    args.config_dir = None
    args.log_level = None
    return args


@pytest.fixture
def mock_settings():
    """Mock Settings object for CLI testing."""
    settings = Mock()
    settings.settings = {
        "general": {
            "output_directory": "/downloads",
            "language": "en",
            "theme": "system"
        },
        "download": {
            "max_concurrent_tasks": 3,
            "max_workers_per_task": 10,
            "max_retries": 3,
            "retry_delay": 5,
            "output_dir": "/downloads"
        },
        "advanced": {
            "user_agent": "VidTanium/1.0",
            "timeout": 30,
            "buffer_size": 8192
        }
    }
    settings.get = Mock(side_effect=lambda section, key, default=None: 
                       settings.settings.get(section, {}).get(key, default))
    settings.set = Mock()
    settings.save_settings = Mock(return_value=True)
    settings.config_dir = Path(tempfile.gettempdir()) / "vidtanium_test"
    return settings


@pytest.fixture
def mock_download_manager():
    """Mock DownloadManager for CLI testing."""
    manager = Mock()
    manager.tasks = {}
    manager.add_task = Mock(return_value="test-task-id-123")
    manager.cancel_task = Mock(return_value=True)
    manager.pause_task = Mock(return_value=True)
    manager.resume_task = Mock(return_value=True)
    manager.get_task = Mock(return_value=None)
    manager.stop = Mock()
    return manager


@pytest.fixture
def mock_download_task():
    """Mock DownloadTask for CLI testing."""
    # Import inside fixture to avoid module load time errors
    try:
        from src.core.downloader import TaskStatus
    except ImportError:
        # Fallback if import fails
        class TaskStatus:
            PENDING = "pending"
            RUNNING = "running"
            PAUSED = "paused"
            COMPLETED = "completed"
            FAILED = "failed"
            CANCELED = "canceled"

    task = Mock()
    task.task_id = "test-task-id-123"
    task.name = "Test Download Task"
    task.base_url = "https://example.com/video.m3u8"
    task.key_url = None
    task.segments = 100
    task.output_file = "/downloads/test_video.mp4"
    task.status = TaskStatus.PENDING
    task.progress = {
        "total": 100,
        "completed": 0,
        "failed": 0,
        "current_file": None,
        "speed": 0.0,
        "estimated_time": None,
        "downloaded_bytes": 0
    }
    return task


@pytest.fixture
def mock_media_analyzer():
    """Mock MediaAnalyzer for CLI testing."""
    analyzer = Mock()
    analyzer.analyze_url = Mock(return_value={
        "success": True,
        "base_url": "https://example.com/video.m3u8",
        "key_url": None,
        "segment_count": 100,
        "total_duration": 300.0,
        "encryption": "none",
        "segments": []
    })
    return analyzer


@pytest.fixture
def mock_terminal_ui():
    """Mock TerminalUI for CLI testing."""
    ui = Mock()
    ui.console = Mock()
    ui.supports_color = True
    ui.supports_unicode = True
    ui.width = 80
    ui.height = 24
    ui.icons = {
        "info": "i",
        "success": "+",
        "warning": "!",
        "error": "x"
    }
    ui.display_welcome = Mock()
    ui.display_info = Mock()
    ui.display_success = Mock()
    ui.display_warning = Mock()
    ui.display_error = Mock()
    ui.display_error_panel = Mock()
    return ui


@pytest.fixture
def mock_progress_display():
    """Mock ProgressDisplay for CLI testing."""
    display = Mock()
    display.progress = Mock()
    display.tasks = {}
    display.add_task = Mock(return_value="progress-task-id")
    display.update_task = Mock()
    display.remove_task = Mock()
    display.start = Mock()
    display.stop = Mock()
    return display


@pytest.fixture
def sample_analysis_result():
    """Sample URL analysis result for testing."""
    return {
        "success": True,
        "base_url": "https://example.com/video.m3u8",
        "key_url": "https://example.com/key.bin",
        "segment_count": 150,
        "total_duration": 450.0,
        "encryption": "AES-128",
        "segments": [
            {"url": "https://example.com/segment0.ts", "duration": 3.0},
            {"url": "https://example.com/segment1.ts", "duration": 3.0},
        ]
    }


@pytest.fixture
def sample_task_list():
    """Sample task list for testing."""
    return [
        {
            "id": "task-1",
            "name": "Video 1",
            "status": "running",
            "progress": 45.5,
            "speed": 2.5
        },
        {
            "id": "task-2",
            "name": "Video 2",
            "status": "pending",
            "progress": 0.0,
            "speed": 0.0
        },
        {
            "id": "task-3",
            "name": "Video 3",
            "status": "completed",
            "progress": 100.0,
            "speed": 0.0
        }
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for testing."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_i18n_manager():
    """Mock I18nManager for CLI testing."""
    manager = Mock()
    manager.current_locale = "en"
    manager.tr = Mock(side_effect=lambda key, **kwargs: key.split('.')[-1])
    manager.set_locale = Mock(return_value=True)
    manager.get_available_locales = Mock(return_value=["en", "zh_CN"])
    return manager


@pytest.fixture
def mock_loguru_for_cli():
    """Mock loguru logger for CLI tests."""
    # Don't use autouse - let tests import modules first
    return Mock()


@pytest.fixture
def mock_console():
    """Mock rich Console for testing."""
    console = Mock()
    console.is_terminal = True
    console.width = 80
    console.height = 24
    console.print = Mock()
    return console


@pytest.fixture
def cli_test_env(monkeypatch, tmp_path):
    """Set up complete CLI test environment."""
    # Set environment variables
    monkeypatch.setenv("VIDTANIUM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("VIDTANIUM_OUTPUT_DIR", str(tmp_path / "downloads"))
    
    # Create directories
    (tmp_path / "config").mkdir()
    (tmp_path / "downloads").mkdir()
    
    return {
        "config_dir": tmp_path / "config",
        "output_dir": tmp_path / "downloads",
        "tmp_path": tmp_path
    }


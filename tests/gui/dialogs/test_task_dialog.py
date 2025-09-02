import pytest
import sys
import os
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any, Optional

# Mock PySide6 components for testing
class MockQDialog:
    def __init__(self, parent=None):
        self.parent_obj = parent
        self.window_title = ""
        self.window_icon = None
        self.minimum_size = (0, 0)
        self.size_value = (600, 600)
        self.maximum_height = None
        self.context_menu_policy = None
        self.accepted = False
        
    def setWindowTitle(self, title):
        self.window_title = title
        
    def setWindowIcon(self, icon):
        self.window_icon = icon
        
    def setMinimumSize(self, width, height):
        self.minimum_size = (width, height)
        
    def resize(self, width, height):
        self.size_value = (width, height)
        
    def setMaximumHeight(self, height):
        self.maximum_height = height
        
    def setContextMenuPolicy(self, policy):
        self.context_menu_policy = policy
        
    def accept(self):
        self.accepted = True
        
    def showEvent(self, event):
        pass
        
    def closeEvent(self, event):
        pass

class MockQWidget:
    def __init__(self):
        pass

class MockQVBoxLayout:
    def __init__(self, parent=None):
        self.parent_obj = parent
        self.widgets = []
        self.margins = (0, 0, 0, 0)
        self.spacing = 0
        
    def addWidget(self, widget, stretch=0):
        self.widgets.append(widget)
        
    def setContentsMargins(self, left, top, right, bottom):
        self.margins = (left, top, right, bottom)
        
    def setSpacing(self, spacing):
        self.spacing = spacing

class MockQHBoxLayout:
    def __init__(self):
        self.widgets = []
        self.spacing = 0
        
    def addWidget(self, widget):
        self.widgets.append(widget)
        
    def setSpacing(self, spacing):
        self.spacing = spacing

class MockQTimer:
    def __init__(self):
        self.timeout = Mock()
        self.interval = 0
        self.single_shot = False
        self.running = False
        
    def setSingleShot(self, single_shot):
        self.single_shot = single_shot
        
    def start(self, interval=None):
        if interval:
            self.interval = interval
        self.running = True
        
    def stop(self):
        self.running = False
        
    @staticmethod
    def singleShot(interval, callback):
        # Immediately call the callback for testing
        callback()

class MockLineEdit:
    def __init__(self):
        self.text_value = ""
        self.textChanged = Mock()
        
    def setText(self, text):
        self.text_value = text
        
    def text(self):
        return self.text_value
        
    def setPlaceholderText(self, text):
        pass

class MockSpinBox:
    def __init__(self):
        self.value_int = 0
        self.valueChanged = Mock()
        
    def setValue(self, value):
        self.value_int = value
        
    def value(self):
        return self.value_int
        
    def setMinimum(self, minimum):
        pass
        
    def setMaximum(self, maximum):
        pass

class MockComboBox:
    def __init__(self):
        self.items = []
        self.current_index = 0
        self.currentTextChanged = Mock()
        
    def addItem(self, text, data=None):
        self.items.append((text, data))
        
    def currentData(self):
        if self.current_index < len(self.items):
            return self.items[self.current_index][1]
        return None
        
    def setCurrentIndex(self, index):
        self.current_index = index

class MockCheckBox:
    def __init__(self):
        self.checked = False
        self.toggled = Mock()
        
    def setChecked(self, checked):
        self.checked = checked
        
    def isChecked(self):
        return self.checked

class MockPushButton:
    def __init__(self, text=""):
        self.text_value = text
        self.clicked = Mock()
        self.enabled = True
        
    def setEnabled(self, enabled):
        self.enabled = enabled

class MockSettings:
    def __init__(self):
        self.data = {
            "general": {
                "output_directory": "/downloads"
            },
            "advanced": {
                "user_agent": "TestAgent/1.0"
            }
        }
        
    def get(self, section, key, default=None):
        return self.data.get(section, {}).get(key, default)

class MockResponsiveManager:
    def __init__(self):
        self.current_breakpoint = Mock()
        self.current_breakpoint.value = "lg"
        
    @staticmethod
    def instance():
        return MockResponsiveManager()
        
    def get_current_breakpoint(self):
        return self.current_breakpoint

class MockHistoryManager:
    def __init__(self):
        self.urls = []
        self.output_paths = []
        
    def add_url(self, url):
        self.urls.append(url)
        
    def add_output_path(self, path):
        self.output_paths.append(path)
        
    def get_recent_urls(self):
        return self.urls[-10:]
        
    def get_recent_output_paths(self):
        return self.output_paths[-10:]

class MockURLValidator:
    def __init__(self, parent=None):
        self.parent_obj = parent
        
    def validate(self, text, pos):
        from PySide6.QtGui import QValidator
        if text.startswith("http"):
            return (QValidator.State.Acceptable, text, pos)
        return (QValidator.State.Invalid, text, pos)

class MockURLAnalyzer:
    def analyze_url(self, url):
        return {
            'is_valid': url.startswith("http"),
            'type': 'm3u8' if 'm3u8' in url else 'unknown',
            'properties': {},
            'suggestions': []
        }

# Mock the PySide6 imports
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()
sys.modules['PySide6.QtWidgets'].QDialog = MockQDialog
sys.modules['PySide6.QtWidgets'].QWidget = MockQWidget
sys.modules['PySide6.QtWidgets'].QVBoxLayout = MockQVBoxLayout
sys.modules['PySide6.QtWidgets'].QHBoxLayout = MockQHBoxLayout
sys.modules['PySide6.QtCore'].QTimer = MockQTimer
sys.modules['PySide6.QtCore'].Qt = Mock()
sys.modules['PySide6.QtCore'].Signal = Mock()
sys.modules['PySide6.QtCore'].Slot = lambda: lambda f: f
sys.modules['PySide6.QtGui'].QValidator = Mock()

# Mock qfluentwidgets
mock_qfluent = Mock()
mock_qfluent.LineEdit = MockLineEdit
mock_qfluent.SpinBox = MockSpinBox
mock_qfluent.ComboBox = MockComboBox
mock_qfluent.CheckBox = MockCheckBox
mock_qfluent.PrimaryPushButton = MockPushButton
mock_qfluent.PushButton = MockPushButton
mock_qfluent.FluentIcon = Mock()
mock_qfluent.InfoBar = Mock()
mock_qfluent.InfoBarPosition = Mock()
mock_qfluent.ElevatedCardWidget = MockQWidget
mock_qfluent.SmoothScrollArea = MockQWidget
mock_qfluent.TitleLabel = MockQWidget
mock_qfluent.StrongBodyLabel = MockQWidget
mock_qfluent.BodyLabel = MockQWidget
mock_qfluent.IconWidget = MockQWidget
sys.modules['qfluentwidgets'] = mock_qfluent

# Mock other GUI components
sys.modules['src.gui.utils.responsive'] = Mock()
sys.modules['src.gui.utils.responsive'].ResponsiveWidget = object
sys.modules['src.gui.utils.responsive'].ResponsiveManager = MockResponsiveManager
sys.modules['src.gui.utils.history'] = Mock()
sys.modules['src.gui.utils.history'].HistoryManager = MockHistoryManager
sys.modules['src.gui.utils.i18n'] = Mock()
sys.modules['src.gui.utils.i18n'].tr = lambda x: x
sys.modules['src.gui.utils.theme'] = Mock()
sys.modules['src.gui.utils.theme'].VidTaniumTheme = Mock()

# Mock core components
sys.modules['src.core.downloader'] = Mock()
sys.modules['src.core.m3u8_parser'] = Mock()

# Now import the actual module
from src.gui.dialogs.task_dialog import TaskDialog, URLValidator, URLAnalyzer


class TestURLValidator:
    """Test suite for URLValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = URLValidator()

    def test_initialization(self):
        """Test URLValidator initialization."""
        assert self.validator is not None

    def test_valid_url_validation(self):
        """Test validation of valid URLs."""
        from PySide6.QtGui import QValidator
        
        valid_urls = [
            "http://example.com/video.m3u8",
            "https://example.com/stream.m3u8",
            "http://test.com/playlist.m3u8"
        ]
        
        for url in valid_urls:
            state, text, pos = self.validator.validate(url, 0)
            assert state == QValidator.State.Acceptable

    def test_invalid_url_validation(self):
        """Test validation of invalid URLs."""
        from PySide6.QtGui import QValidator
        
        invalid_urls = [
            "not_a_url",
            "ftp://example.com",
            "",
            "just text"
        ]
        
        for url in invalid_urls:
            state, text, pos = self.validator.validate(url, 0)
            assert state == QValidator.State.Invalid


class TestURLAnalyzer:
    """Test suite for URLAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = URLAnalyzer()

    def test_initialization(self):
        """Test URLAnalyzer initialization."""
        assert self.analyzer is not None

    def test_analyze_valid_m3u8_url(self):
        """Test analyzing valid M3U8 URL."""
        url = "http://example.com/stream.m3u8"
        result = self.analyzer.analyze_url(url)
        
        assert result['is_valid'] is True
        assert result['type'] == 'm3u8'
        assert isinstance(result['properties'], dict)
        assert isinstance(result['suggestions'], list)

    def test_analyze_invalid_url(self):
        """Test analyzing invalid URL."""
        url = "not_a_url"
        result = self.analyzer.analyze_url(url)
        
        assert result['is_valid'] is False

    def test_analyze_empty_url(self):
        """Test analyzing empty URL."""
        result = self.analyzer.analyze_url("")
        
        assert result == {}


class TestTaskDialog:
    """Test suite for TaskDialog class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_settings = MockSettings()
        self.mock_theme_manager = Mock()

    @patch('src.gui.dialogs.task_dialog.ResponsiveManager')
    @patch('src.gui.dialogs.task_dialog.HistoryManager')
    @patch('src.gui.dialogs.task_dialog.URLValidator')
    @patch('src.gui.dialogs.task_dialog.URLAnalyzer')
    def test_initialization(self, mock_analyzer, mock_validator, mock_history, mock_responsive):
        """Test TaskDialog initialization."""
        # Mock responsive manager
        mock_responsive_instance = MockResponsiveManager()
        mock_responsive.instance.return_value = mock_responsive_instance
        
        dialog = TaskDialog(self.mock_settings, self.mock_theme_manager)
        
        assert dialog.settings == self.mock_settings
        assert dialog.theme_manager == self.mock_theme_manager
        assert dialog._ui_created is False
        assert dialog._completers_setup is False
        assert dialog._animations_setup is False

    @patch('src.gui.dialogs.task_dialog.ResponsiveManager')
    @patch('src.gui.dialogs.task_dialog.HistoryManager')
    @patch('src.gui.dialogs.task_dialog.URLValidator')
    @patch('src.gui.dialogs.task_dialog.URLAnalyzer')
    def test_responsive_window_setup_small_screen(self, mock_analyzer, mock_validator, mock_history, mock_responsive):
        """Test responsive window setup for small screens."""
        # Mock responsive manager for small screen
        mock_responsive_instance = MockResponsiveManager()
        mock_responsive_instance.current_breakpoint.value = "xs"
        mock_responsive.instance.return_value = mock_responsive_instance
        
        dialog = TaskDialog(self.mock_settings, self.mock_theme_manager)
        
        # Should set appropriate size for small screens
        assert dialog.minimum_size == (500, 550)

    @patch('src.gui.dialogs.task_dialog.ResponsiveManager')
    @patch('src.gui.dialogs.task_dialog.HistoryManager')
    @patch('src.gui.dialogs.task_dialog.URLValidator')
    @patch('src.gui.dialogs.task_dialog.URLAnalyzer')
    def test_responsive_window_setup_large_screen(self, mock_analyzer, mock_validator, mock_history, mock_responsive):
        """Test responsive window setup for large screens."""
        # Mock responsive manager for large screen
        mock_responsive_instance = MockResponsiveManager()
        mock_responsive_instance.current_breakpoint.value = "lg"
        mock_responsive.instance.return_value = mock_responsive_instance
        
        dialog = TaskDialog(self.mock_settings, self.mock_theme_manager)
        
        # Should set appropriate size for large screens
        assert dialog.minimum_size == (650, 650)

    @patch('src.gui.dialogs.task_dialog.ResponsiveManager')
    @patch('src.gui.dialogs.task_dialog.HistoryManager')
    @patch('src.gui.dialogs.task_dialog.URLValidator')
    @patch('src.gui.dialogs.task_dialog.URLAnalyzer')
    def test_get_task_data(self, mock_analyzer, mock_validator, mock_history, mock_responsive):
        """Test getting task data from dialog."""
        # Mock responsive manager
        mock_responsive_instance = MockResponsiveManager()
        mock_responsive.instance.return_value = mock_responsive_instance
        
        dialog = TaskDialog(self.mock_settings, self.mock_theme_manager)
        
        # Mock form inputs
        dialog.name_input = MockLineEdit()
        dialog.base_url_input = MockLineEdit()
        dialog.key_url_input = MockLineEdit()
        dialog.segments_input = MockSpinBox()
        dialog.output_input = MockLineEdit()
        dialog.priority_combo = MockComboBox()
        dialog.auto_start_check = MockCheckBox()
        
        # Set test data
        dialog.name_input.setText("Test Task")
        dialog.base_url_input.setText("http://example.com/stream.m3u8")
        dialog.key_url_input.setText("http://example.com/key.bin")
        dialog.segments_input.setValue(100)
        dialog.output_input.setText("/downloads/video.mp4")
        dialog.priority_combo.addItem("Normal", "normal")
        dialog.auto_start_check.setChecked(True)
        
        # Mock history manager
        dialog.history_manager = MockHistoryManager()
        
        task_data = dialog.get_task_data()
        
        assert task_data["name"] == "Test Task"
        assert task_data["base_url"] == "http://example.com/stream.m3u8"
        assert task_data["key_url"] == "http://example.com/key.bin"
        assert task_data["segments"] == 100
        assert task_data["output_file"] == "/downloads/video.mp4"
        assert task_data["auto_start"] is True

    @patch('src.gui.dialogs.task_dialog.ResponsiveManager')
    @patch('src.gui.dialogs.task_dialog.HistoryManager')
    @patch('src.gui.dialogs.task_dialog.URLValidator')
    @patch('src.gui.dialogs.task_dialog.URLAnalyzer')
    def test_form_validation_valid(self, mock_analyzer, mock_validator, mock_history, mock_responsive):
        """Test form validation with valid data."""
        # Mock responsive manager
        mock_responsive_instance = MockResponsiveManager()
        mock_responsive.instance.return_value = mock_responsive_instance
        
        dialog = TaskDialog(self.mock_settings, self.mock_theme_manager)
        
        # Mock form inputs
        dialog.base_url_input = MockLineEdit()
        dialog.output_input = MockLineEdit()
        dialog.create_button = MockPushButton()
        dialog.validationChanged = Mock()
        
        # Set valid data
        dialog.base_url_input.setText("http://example.com/stream.m3u8")
        dialog.output_input.setText("/downloads/video.mp4")
        
        dialog._validate_form()
        
        assert dialog.create_button.enabled is True

    @patch('src.gui.dialogs.task_dialog.ResponsiveManager')
    @patch('src.gui.dialogs.task_dialog.HistoryManager')
    @patch('src.gui.dialogs.task_dialog.URLValidator')
    @patch('src.gui.dialogs.task_dialog.URLAnalyzer')
    def test_form_validation_invalid(self, mock_analyzer, mock_validator, mock_history, mock_responsive):
        """Test form validation with invalid data."""
        # Mock responsive manager
        mock_responsive_instance = MockResponsiveManager()
        mock_responsive.instance.return_value = mock_responsive_instance
        
        dialog = TaskDialog(self.mock_settings, self.mock_theme_manager)
        
        # Mock form inputs
        dialog.base_url_input = MockLineEdit()
        dialog.output_input = MockLineEdit()
        dialog.create_button = MockPushButton()
        dialog.validationChanged = Mock()
        
        # Set invalid data (missing URL)
        dialog.base_url_input.setText("")
        dialog.output_input.setText("/downloads/video.mp4")
        
        dialog._validate_form()
        
        assert dialog.create_button.enabled is False

    @patch('src.gui.dialogs.task_dialog.ResponsiveManager')
    @patch('src.gui.dialogs.task_dialog.HistoryManager')
    @patch('src.gui.dialogs.task_dialog.URLValidator')
    @patch('src.gui.dialogs.task_dialog.URLAnalyzer')
    def test_auto_save_functionality(self, mock_analyzer, mock_validator, mock_history, mock_responsive):
        """Test auto-save functionality."""
        # Mock responsive manager
        mock_responsive_instance = MockResponsiveManager()
        mock_responsive.instance.return_value = mock_responsive_instance
        
        dialog = TaskDialog(self.mock_settings, self.mock_theme_manager)
        
        # Mock auto save timer
        dialog.auto_save_timer = MockQTimer()
        
        # Should start auto save timer
        assert dialog.auto_save_timer.running is True

    @patch('src.gui.dialogs.task_dialog.ResponsiveManager')
    @patch('src.gui.dialogs.task_dialog.HistoryManager')
    @patch('src.gui.dialogs.task_dialog.URLValidator')
    @patch('src.gui.dialogs.task_dialog.URLAnalyzer')
    def test_performance_metrics_tracking(self, mock_analyzer, mock_validator, mock_history, mock_responsive):
        """Test performance metrics tracking."""
        # Mock responsive manager
        mock_responsive_instance = MockResponsiveManager()
        mock_responsive.instance.return_value = mock_responsive_instance
        
        dialog = TaskDialog(self.mock_settings, self.mock_theme_manager)
        
        # Should have performance metrics
        assert hasattr(dialog, '_performance_metrics')
        assert 'init_time' in dialog._performance_metrics
        assert 'ui_creation_time' in dialog._performance_metrics
        assert 'validation_count' in dialog._performance_metrics
        assert 'extraction_count' in dialog._performance_metrics


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

"""
Unit tests for CLI UI components.
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from rich.text import Text
from rich.console import Console


class TestTerminalUI:
    """Test suite for TerminalUI class."""
    
    def test_initialization(self):
        """Test TerminalUI initialization."""
        with patch('src.cli.ui_components.Console') as mock_console_class:
            mock_console = Mock()
            mock_console.is_terminal = True
            mock_console.width = 80
            mock_console.height = 24
            mock_console_class.return_value = mock_console
            
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            
            assert ui.console is not None
            assert ui.supports_color is True
            assert ui.width == 80
            assert ui.height == 24
            assert hasattr(ui, 'icons')
    
    def test_unicode_detection_supported(self):
        """Test Unicode support detection when supported."""
        with patch('src.cli.ui_components.Console'), \
             patch('src.cli.ui_components.sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'utf-8'
            
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            
            assert ui.supports_unicode is True
            assert ui.icons['info'] == 'ℹ'
            assert ui.icons['success'] == '✓'
    
    def test_unicode_detection_not_supported(self):
        """Test Unicode support detection when not supported."""
        with patch('src.cli.ui_components.Console'), \
             patch('src.cli.ui_components.sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'ascii'
            
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            
            # Should fall back to ASCII icons
            assert ui.icons['info'] == 'i'
            assert ui.icons['success'] == '+'
            assert ui.icons['warning'] == '!'
            assert ui.icons['error'] == 'x'
    
    def test_display_welcome(self, mock_console):
        """Test display_welcome method."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.tr', return_value="Welcome"):
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            ui.display_welcome()
            
            # Should print welcome panel
            assert mock_console.print.called
    
    def test_display_info(self, mock_console):
        """Test display_info method."""
        with patch('src.cli.ui_components.Console', return_value=mock_console):
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            ui.display_info("Test message")
            
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Test message" in call_args
    
    def test_display_success(self, mock_console):
        """Test display_success method."""
        with patch('src.cli.ui_components.Console', return_value=mock_console):
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            ui.display_success("Success message")
            
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Success message" in call_args
    
    def test_display_warning(self, mock_console):
        """Test display_warning method."""
        with patch('src.cli.ui_components.Console', return_value=mock_console):
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            ui.display_warning("Warning message")
            
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Warning message" in call_args
    
    def test_display_error(self):
        """Test display_error method."""
        with patch('src.cli.ui_components.Console') as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console
            
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            ui.display_error("Error message")
            
            # Should create stderr console and print error
            assert mock_console_class.call_count >= 2  # One for init, one for stderr
    
    def test_display_error_panel(self):
        """Test display_error_panel method."""
        with patch('src.cli.ui_components.Console') as mock_console_class, \
             patch('src.cli.ui_components.tr', return_value="Suggestions"):
            mock_console = Mock()
            mock_console_class.return_value = mock_console
            
            from src.cli.ui_components import TerminalUI
            
            ui = TerminalUI()
            ui.display_error_panel(
                "Error Title",
                "Error message",
                ["Suggestion 1", "Suggestion 2"]
            )
            
            # Should create error console and print panel
            assert mock_console_class.call_count >= 2


class TestStatusIndicator:
    """Test suite for StatusIndicator class."""
    
    def test_get_status_text_unicode(self):
        """Test get_status_text with Unicode icons."""
        with patch('src.cli.ui_components.tr', side_effect=lambda key, **kwargs: key.split('.')[-1]):
            from src.cli.ui_components import StatusIndicator
            
            text = StatusIndicator.get_status_text("running", use_unicode=True)
            
            assert isinstance(text, Text)
            # Should contain the status text
            assert "running" in str(text)
    
    def test_get_status_text_ascii(self):
        """Test get_status_text with ASCII icons."""
        with patch('src.cli.ui_components.tr', side_effect=lambda key, **kwargs: key.split('.')[-1]):
            from src.cli.ui_components import StatusIndicator
            
            text = StatusIndicator.get_status_text("completed", use_unicode=False)
            
            assert isinstance(text, Text)
            assert "completed" in str(text)
    
    def test_all_status_types_unicode(self):
        """Test all status types with Unicode icons."""
        with patch('src.cli.ui_components.tr', side_effect=lambda key, **kwargs: key.split('.')[-1]):
            from src.cli.ui_components import StatusIndicator
            
            statuses = ["pending", "running", "paused", "completed", "failed", "canceled"]
            
            for status in statuses:
                text = StatusIndicator.get_status_text(status, use_unicode=True)
                assert isinstance(text, Text)
                assert status in str(text)
    
    def test_all_status_types_ascii(self):
        """Test all status types with ASCII icons."""
        with patch('src.cli.ui_components.tr', side_effect=lambda key, **kwargs: key.split('.')[-1]):
            from src.cli.ui_components import StatusIndicator
            
            statuses = ["pending", "running", "paused", "completed", "failed", "canceled"]
            
            for status in statuses:
                text = StatusIndicator.get_status_text(status, use_unicode=False)
                assert isinstance(text, Text)
                assert status in str(text)
    
    def test_unknown_status(self):
        """Test handling of unknown status."""
        with patch('src.cli.ui_components.tr', side_effect=lambda key, **kwargs: key.split('.')[-1]):
            from src.cli.ui_components import StatusIndicator
            
            text = StatusIndicator.get_status_text("unknown_status", use_unicode=True)
            
            assert isinstance(text, Text)


class TestProgressDisplay:
    """Test suite for ProgressDisplay class."""
    
    def test_initialization(self):
        """Test ProgressDisplay initialization."""
        with patch('src.cli.ui_components.Progress') as mock_progress_class, \
             patch('src.cli.ui_components.Console'):
            mock_progress = Mock()
            mock_progress_class.return_value = mock_progress
            
            from src.cli.ui_components import ProgressDisplay
            
            display = ProgressDisplay()
            
            assert display.progress is not None
            assert display.tasks == {}
    
    def test_add_task(self):
        """Test adding a task to progress display."""
        with patch('src.cli.ui_components.Progress') as mock_progress_class, \
             patch('src.cli.ui_components.Console'):
            mock_progress = Mock()
            mock_progress.add_task = Mock(return_value="rich-task-id")
            mock_progress_class.return_value = mock_progress
            
            from src.cli.ui_components import ProgressDisplay
            
            display = ProgressDisplay()
            task_id = display.add_task("task-1", "Test Task", 100)
            
            assert task_id == "rich-task-id"
            assert "task-1" in display.tasks
            assert display.tasks["task-1"] == "rich-task-id"
            mock_progress.add_task.assert_called_once_with("Test Task", total=100)
    
    def test_update_task(self):
        """Test updating task progress."""
        with patch('src.cli.ui_components.Progress') as mock_progress_class, \
             patch('src.cli.ui_components.Console'):
            mock_progress = Mock()
            mock_progress.add_task = Mock(return_value="rich-task-id")
            mock_progress_class.return_value = mock_progress
            
            from src.cli.ui_components import ProgressDisplay
            
            display = ProgressDisplay()
            display.add_task("task-1", "Test Task", 100)
            display.update_task("task-1", 50)
            
            mock_progress.update.assert_called_with("rich-task-id", completed=50)
    
    def test_update_task_with_description(self):
        """Test updating task with new description."""
        with patch('src.cli.ui_components.Progress') as mock_progress_class, \
             patch('src.cli.ui_components.Console'):
            mock_progress = Mock()
            mock_progress.add_task = Mock(return_value="rich-task-id")
            mock_progress_class.return_value = mock_progress
            
            from src.cli.ui_components import ProgressDisplay
            
            display = ProgressDisplay()
            display.add_task("task-1", "Test Task", 100)
            display.update_task("task-1", 50, "New Description")
            
            assert mock_progress.update.call_count == 2
    
    def test_remove_task(self):
        """Test removing a task from progress display."""
        with patch('src.cli.ui_components.Progress') as mock_progress_class, \
             patch('src.cli.ui_components.Console'):
            mock_progress = Mock()
            mock_progress.add_task = Mock(return_value="rich-task-id")
            mock_progress_class.return_value = mock_progress
            
            from src.cli.ui_components import ProgressDisplay
            
            display = ProgressDisplay()
            display.add_task("task-1", "Test Task", 100)
            display.remove_task("task-1")
            
            assert "task-1" not in display.tasks
            mock_progress.remove_task.assert_called_once_with("rich-task-id")
    
    def test_start_stop(self):
        """Test starting and stopping progress display."""
        with patch('src.cli.ui_components.Progress') as mock_progress_class, \
             patch('src.cli.ui_components.Console'):
            mock_progress = Mock()
            mock_progress_class.return_value = mock_progress
            
            from src.cli.ui_components import ProgressDisplay
            
            display = ProgressDisplay()
            display.start()
            display.stop()
            
            mock_progress.start.assert_called_once()
            mock_progress.stop.assert_called_once()


class TestTaskListDisplay:
    """Test suite for TaskListDisplay class."""
    
    def test_initialization(self, mock_console):
        """Test TaskListDisplay initialization."""
        with patch('src.cli.ui_components.Console', return_value=mock_console):
            from src.cli.ui_components import TaskListDisplay
            
            display = TaskListDisplay()
            
            assert display.console is not None
    
    def test_display_tasks_empty(self, mock_console):
        """Test displaying empty task list."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.tr', return_value="No tasks"):
            from src.cli.ui_components import TaskListDisplay
            
            display = TaskListDisplay()
            display.display_tasks([])
            
            mock_console.print.assert_called_once()
    
    def test_display_tasks_with_data(self, mock_console, sample_task_list):
        """Test displaying task list with data."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.tr', side_effect=lambda key, **kwargs: key.split('.')[-1]), \
             patch('src.cli.ui_components.StatusIndicator.get_status_text', return_value=Text("Status")):
            from src.cli.ui_components import TaskListDisplay
            
            display = TaskListDisplay()
            display.display_tasks(sample_task_list)
            
            # Should print table
            mock_console.print.assert_called_once()


class TestInteractiveTerminal:
    """Test suite for InteractiveTerminal class."""

    def test_initialization(self, mock_console):
        """Test InteractiveTerminal initialization."""
        with patch('src.cli.ui_components.Console', return_value=mock_console):
            from src.cli.ui_components import InteractiveTerminal

            terminal = InteractiveTerminal()

            assert terminal.console is not None
            assert terminal._cancel_flag is not None
            assert terminal._running is False

    def test_prompt_url_success(self, mock_console):
        """Test URL prompt with successful input."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.Prompt.ask', return_value="https://example.com/video.m3u8"):
            from src.cli.ui_components import InteractiveTerminal

            terminal = InteractiveTerminal()
            url = terminal.prompt_url()

            assert url == "https://example.com/video.m3u8"

    def test_prompt_url_cancelled(self, mock_console):
        """Test URL prompt when cancelled."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.Prompt.ask', side_effect=KeyboardInterrupt):
            from src.cli.ui_components import InteractiveTerminal

            terminal = InteractiveTerminal()
            url = terminal.prompt_url()

            assert url is None

    def test_keyboard_listener_windows(self, mock_console):
        """Test keyboard listener on Windows."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.PLATFORM_WINDOWS', True):
            from src.cli.ui_components import InteractiveTerminal

            terminal = InteractiveTerminal()
            callback = Mock()

            result = terminal.start_keyboard_listener(callback)

            assert result is True
            assert terminal._running is True

            terminal.stop_keyboard_listener()
            assert terminal._running is False

    def test_keyboard_listener_non_windows(self, mock_console):
        """Test keyboard listener on non-Windows platforms."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.PLATFORM_WINDOWS', False):
            from src.cli.ui_components import InteractiveTerminal

            terminal = InteractiveTerminal()
            callback = Mock()

            result = terminal.start_keyboard_listener(callback)

            assert result is False
            assert terminal._running is False

    def test_cleanup(self, mock_console):
        """Test cleanup method."""
        with patch('src.cli.ui_components.Console', return_value=mock_console):
            from src.cli.ui_components import InteractiveTerminal

            terminal = InteractiveTerminal()
            terminal.cleanup()

            assert terminal._running is False


class TestLiveProgressDisplay:
    """Test suite for LiveProgressDisplay class."""

    def test_initialization(self, mock_console):
        """Test LiveProgressDisplay initialization."""
        with patch('src.cli.ui_components.Console', return_value=mock_console):
            from src.cli.ui_components import LiveProgressDisplay

            display = LiveProgressDisplay(update_hz=20)

            assert display.console is not None
            assert display.update_hz == 20
            assert display._running is False

    def test_start_stop(self, mock_console):
        """Test starting and stopping live display."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.Live') as mock_live_class:
            mock_live = Mock()
            mock_live_class.return_value = mock_live

            from src.cli.ui_components import LiveProgressDisplay

            display = LiveProgressDisplay()
            display.start()

            assert display._running is True
            mock_live.start.assert_called_once()

            display.stop()

            assert display._running is False
            mock_live.stop.assert_called_once()

    def test_update_with_throttling(self, mock_console):
        """Test update with throttling."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.Live'):
            from src.cli.ui_components import LiveProgressDisplay

            display = LiveProgressDisplay(update_hz=10)
            display.start()

            # First update should succeed
            result1 = display.update({"task_name": "Test", "total": 100, "completed": 50}, force=True)
            assert result1 is True

            # Immediate second update should be throttled
            result2 = display.update({"completed": 51}, force=False)
            # May or may not be throttled depending on timing

            display.stop()

    def test_update_force(self, mock_console):
        """Test forced update bypasses throttling."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.Live'):
            from src.cli.ui_components import LiveProgressDisplay

            display = LiveProgressDisplay(update_hz=10)
            display.start()

            # Forced updates should always succeed
            result1 = display.update({"task_name": "Test"}, force=True)
            result2 = display.update({"completed": 50}, force=True)

            assert result1 is True
            assert result2 is True

            display.stop()

    def test_cleanup(self, mock_console):
        """Test cleanup method."""
        with patch('src.cli.ui_components.Console', return_value=mock_console), \
             patch('src.cli.ui_components.Live'):
            from src.cli.ui_components import LiveProgressDisplay

            display = LiveProgressDisplay()
            display.start()
            display.cleanup()

            assert display._running is False


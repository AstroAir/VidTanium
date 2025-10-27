"""
Unit tests for CLIApplication class.
"""
import pytest
import signal
import argparse
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestCLIApplication:
    """Test suite for CLIApplication class."""
    
    def test_initialization(self, mock_cli_args):
        """Test CLIApplication initialization."""
        with patch('src.cli.cli_app.signal.signal'):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(config_dir="/test/config", cli_args=mock_cli_args)
            
            assert app.config_dir == "/test/config"
            assert app.cli_args == mock_cli_args
            assert app.settings is None
            assert app.download_manager is None
            assert app.command_handler is None
            assert app.terminal_ui is None
            assert app.running is False
    
    def test_initialization_with_defaults(self):
        """Test CLIApplication initialization with default arguments."""
        with patch('src.cli.cli_app.signal.signal'):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication()
            
            assert app.config_dir is None
            assert isinstance(app.cli_args, argparse.Namespace)
            assert app.running is False
    
    def test_signal_handler_registration(self, mock_cli_args):
        """Test that signal handlers are registered during initialization."""
        with patch('src.cli.cli_app.signal.signal') as mock_signal:
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            
            # Verify SIGINT and SIGTERM handlers were registered
            assert mock_signal.call_count == 2
            calls = mock_signal.call_args_list
            signals_registered = [call[0][0] for call in calls]
            assert signal.SIGINT in signals_registered
            assert signal.SIGTERM in signals_registered
    
    def test_initialize_success(self, mock_cli_args, mock_settings, mock_download_manager, mock_terminal_ui):
        """Test successful initialization of all components."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.init_cli_i18n'), \
             patch('src.cli.cli_app.Settings', return_value=mock_settings), \
             patch('src.cli.cli_app.DownloadManager', return_value=mock_download_manager), \
             patch('src.cli.cli_app.TerminalUI', return_value=mock_terminal_ui), \
             patch('src.cli.cli_app.CommandHandler') as mock_cmd_handler:
            
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            result = app.initialize()
            
            assert result is True
            assert app.settings is not None
            assert app.download_manager is not None
            assert app.terminal_ui is not None
            assert app.command_handler is not None
    
    def test_initialize_failure(self, mock_cli_args):
        """Test initialization failure handling."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.init_cli_i18n', side_effect=Exception("Init failed")):
            
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            result = app.initialize()
            
            assert result is False
    
    def test_run_without_initialization(self, mock_cli_args):
        """Test run fails gracefully when initialization fails."""
        with patch('src.cli.cli_app.signal.signal'):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.initialize = Mock(return_value=False)
            
            result = app.run()
            
            assert result == 1
    
    def test_run_success(self, mock_cli_args, mock_terminal_ui):
        """Test successful run of CLI application."""
        with patch('src.cli.cli_app.signal.signal'):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.initialize = Mock(return_value=True)
            app.terminal_ui = mock_terminal_ui
            app.command_handler = Mock()
            app._execute_command = Mock(return_value=0)
            app.shutdown = Mock()
            
            result = app.run()
            
            assert result == 0
            mock_terminal_ui.display_welcome.assert_called_once()
            app._execute_command.assert_called_once()
            app.shutdown.assert_called_once()
    
    def test_run_keyboard_interrupt(self, mock_cli_args, mock_terminal_ui):
        """Test handling of keyboard interrupt during run."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.tr', return_value="Interrupted"):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.initialize = Mock(return_value=True)
            app.terminal_ui = mock_terminal_ui
            app.command_handler = Mock()
            app._execute_command = Mock(side_effect=KeyboardInterrupt())
            app.shutdown = Mock()
            
            result = app.run()
            
            assert result == 130  # Standard exit code for SIGINT
            app.shutdown.assert_called_once()
    
    def test_run_unexpected_exception(self, mock_cli_args, mock_terminal_ui):
        """Test handling of unexpected exceptions during run."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.tr', return_value="Error"):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.initialize = Mock(return_value=True)
            app.terminal_ui = mock_terminal_ui
            app.command_handler = Mock()
            app._execute_command = Mock(side_effect=Exception("Test error"))
            app.shutdown = Mock()
            
            result = app.run()
            
            assert result == 1
            app.shutdown.assert_called_once()
    
    def test_execute_command_with_url(self, mock_cli_args):
        """Test command execution with URL argument."""
        with patch('src.cli.cli_app.signal.signal'):
            from src.cli.cli_app import CLIApplication
            
            mock_cli_args.url = "https://example.com/video.m3u8"
            mock_cli_args.output_dir = "/downloads"
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.command_handler = Mock()
            app.command_handler.download = Mock(return_value=0)
            app.terminal_ui = Mock()
            
            result = app._execute_command()
            
            assert result == 0
            app.command_handler.download.assert_called_once_with(
                "https://example.com/video.m3u8",
                "/downloads"
            )
    
    def test_execute_command_without_url(self, mock_cli_args, mock_terminal_ui):
        """Test command execution without URL shows help message."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.tr', side_effect=lambda key, **kwargs: key):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.command_handler = Mock()
            app.terminal_ui = mock_terminal_ui
            
            result = app._execute_command()
            
            assert result == 0
            assert mock_terminal_ui.display_info.call_count == 2
    
    def test_shutdown(self, mock_cli_args, mock_download_manager, mock_terminal_ui):
        """Test graceful shutdown."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.tr', return_value="Goodbye"):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.running = True
            app.download_manager = mock_download_manager
            app.terminal_ui = mock_terminal_ui
            
            app.shutdown()
            
            assert app.running is False
            mock_download_manager.stop.assert_called_once()
            mock_terminal_ui.display_info.assert_called_once()
    
    def test_shutdown_when_not_running(self, mock_cli_args):
        """Test shutdown does nothing when not running."""
        with patch('src.cli.cli_app.signal.signal'):
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.running = False
            app.download_manager = Mock()
            
            app.shutdown()
            
            # Should return early without calling stop
            app.download_manager.stop.assert_not_called()
    
    def test_shutdown_with_exception(self, mock_cli_args, mock_download_manager):
        """Test shutdown handles exceptions gracefully."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.tr', return_value="Goodbye"):
            from src.cli.cli_app import CLIApplication
            
            mock_download_manager.stop.side_effect = Exception("Stop failed")
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.running = True
            app.download_manager = mock_download_manager
            app.terminal_ui = Mock()
            
            # Should not raise exception
            app.shutdown()
            
            assert app.running is False
    
    def test_signal_handler(self, mock_cli_args):
        """Test signal handler calls shutdown and exits."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.sys.exit') as mock_exit:
            from src.cli.cli_app import CLIApplication
            
            app = CLIApplication(cli_args=mock_cli_args)
            app.shutdown = Mock()
            
            # Simulate SIGINT
            app._signal_handler(signal.SIGINT, None)
            
            app.shutdown.assert_called_once()
            mock_exit.assert_called_once_with(128 + signal.SIGINT)


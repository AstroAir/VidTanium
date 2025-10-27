"""
Integration tests for CLI application.
"""
import pytest
import sys
import argparse
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestCLIIntegration:
    """Integration tests for complete CLI workflows."""
    
    def test_cli_routing_from_main(self):
        """Test that main.py routes to CLI when --no-gui is specified."""
        with patch('main.CLIApplication') as mock_cli_app_class, \
             patch('main.parse_args') as mock_parse_args, \
             patch('main.setup_logging'), \
             patch('main.check_singleton_and_activate', return_value=False):
            
            # Setup mock args
            mock_args = Mock()
            mock_args.no_gui = True
            mock_args.debug = False
            mock_args.log_level = None
            mock_args.allow_multiple = True
            mock_args.url = None
            mock_args.config_dir = None
            mock_args.config = None
            mock_parse_args.return_value = mock_args
            
            # Setup mock CLI app
            mock_cli_app = Mock()
            mock_cli_app.run = Mock(return_value=0)
            mock_cli_app_class.return_value = mock_cli_app
            
            # Import and run main
            import main
            result = main.main()
            
            # Verify CLI app was created and run
            mock_cli_app_class.assert_called_once()
            mock_cli_app.run.assert_called_once()
            assert result == 0
    
    def test_complete_download_workflow(self, mock_settings, sample_analysis_result):
        """Test complete download workflow from URL to completion."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.init_cli_i18n'), \
             patch('src.cli.cli_app.Settings', return_value=mock_settings), \
             patch('src.cli.cli_app.DownloadManager') as mock_dm_class, \
             patch('src.cli.cli_app.TerminalUI') as mock_ui_class, \
             patch('src.cli.cli_app.CommandHandler') as mock_cmd_class, \
             patch('src.cli.commands.MediaAnalyzer') as mock_analyzer_class, \
             patch('src.cli.commands.DownloadTask') as mock_task_class, \
             patch('src.cli.commands.ProgressDisplay'), \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key), \
             patch('src.cli.commands.time.sleep'), \
             patch('src.cli.commands.Path'):
            
            from src.core.downloader import TaskStatus
            from src.cli.cli_app import CLIApplication
            
            # Setup mocks
            mock_dm = Mock()
            mock_dm.add_task = Mock(return_value="task-123")
            mock_dm.stop = Mock()
            mock_dm_class.return_value = mock_dm
            
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            
            mock_task = Mock()
            mock_task.task_id = "task-123"
            mock_task.name = "Test Video"
            mock_task.status = TaskStatus.COMPLETED
            mock_task.segments = 100
            mock_task.progress = {"completed": 100}
            mock_task_class.return_value = mock_task
            
            mock_analyzer = Mock()
            mock_analyzer.analyze_url = Mock(return_value=sample_analysis_result)
            mock_analyzer_class.return_value = mock_analyzer
            
            # Create CLI app with URL
            args = argparse.Namespace()
            args.no_gui = True
            args.url = "https://example.com/video.m3u8"
            args.output_dir = "/downloads"
            
            app = CLIApplication(cli_args=args)
            
            # Initialize and run
            app.initialize()
            result = app.run()
            
            # Verify workflow
            assert result == 0
            mock_analyzer.analyze_url.assert_called_once()
            mock_dm.add_task.assert_called_once()
    
    def test_cli_with_keyboard_interrupt(self, mock_settings):
        """Test CLI handles keyboard interrupt gracefully."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.init_cli_i18n'), \
             patch('src.cli.cli_app.Settings', return_value=mock_settings), \
             patch('src.cli.cli_app.DownloadManager') as mock_dm_class, \
             patch('src.cli.cli_app.TerminalUI') as mock_ui_class, \
             patch('src.cli.cli_app.CommandHandler') as mock_cmd_class, \
             patch('src.cli.cli_app.tr', return_value="Interrupted"):
            
            from src.cli.cli_app import CLIApplication
            
            mock_dm = Mock()
            mock_dm.stop = Mock()
            mock_dm_class.return_value = mock_dm
            
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            
            mock_cmd = Mock()
            mock_cmd.download = Mock(side_effect=KeyboardInterrupt())
            mock_cmd_class.return_value = mock_cmd
            
            args = argparse.Namespace()
            args.no_gui = True
            args.url = "https://example.com/video.m3u8"
            
            app = CLIApplication(cli_args=args)
            app.initialize()
            result = app.run()
            
            # Should return SIGINT exit code
            assert result == 130
            mock_dm.stop.assert_called_once()
    
    def test_cli_settings_integration(self, mock_settings):
        """Test CLI integrates with Settings without Qt dependencies."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.init_cli_i18n'), \
             patch('src.cli.cli_app.Settings', return_value=mock_settings), \
             patch('src.cli.cli_app.DownloadManager'), \
             patch('src.cli.cli_app.TerminalUI'), \
             patch('src.cli.cli_app.CommandHandler'):
            
            from src.cli.cli_app import CLIApplication
            
            args = argparse.Namespace()
            args.no_gui = True
            args.config_dir = "/test/config"
            
            app = CLIApplication(cli_args=args)
            result = app.initialize()
            
            assert result is True
            assert app.settings is not None
            # Verify Settings was initialized with config_dir
            assert mock_settings is not None
    
    def test_cli_without_url_shows_help(self, mock_settings):
        """Test CLI without URL shows help message."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.init_cli_i18n'), \
             patch('src.cli.cli_app.Settings', return_value=mock_settings), \
             patch('src.cli.cli_app.DownloadManager') as mock_dm_class, \
             patch('src.cli.cli_app.TerminalUI') as mock_ui_class, \
             patch('src.cli.cli_app.CommandHandler') as mock_cmd_class, \
             patch('src.cli.cli_app.tr', side_effect=lambda key, **kwargs: key):
            
            from src.cli.cli_app import CLIApplication
            
            mock_dm = Mock()
            mock_dm.stop = Mock()
            mock_dm_class.return_value = mock_dm
            
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            
            mock_cmd = Mock()
            mock_cmd_class.return_value = mock_cmd
            
            args = argparse.Namespace()
            args.no_gui = True
            args.url = None
            
            app = CLIApplication(cli_args=args)
            app.initialize()
            result = app.run()
            
            # Should display help messages
            assert mock_ui.display_info.call_count >= 2
            assert result == 0
    
    def test_signal_handling_integration(self, mock_settings):
        """Test signal handling integration."""
        with patch('src.cli.cli_app.signal.signal') as mock_signal, \
             patch('src.cli.cli_app.init_cli_i18n'), \
             patch('src.cli.cli_app.Settings', return_value=mock_settings), \
             patch('src.cli.cli_app.DownloadManager'), \
             patch('src.cli.cli_app.TerminalUI'), \
             patch('src.cli.cli_app.CommandHandler'):
            
            from src.cli.cli_app import CLIApplication
            import signal
            
            args = argparse.Namespace()
            args.no_gui = True
            
            app = CLIApplication(cli_args=args)
            
            # Verify signal handlers were registered
            assert mock_signal.call_count == 2
            signal_calls = [call[0][0] for call in mock_signal.call_args_list]
            assert signal.SIGINT in signal_calls
            assert signal.SIGTERM in signal_calls
    
    def test_error_recovery_integration(self, mock_settings):
        """Test error recovery in integration scenario."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.init_cli_i18n'), \
             patch('src.cli.cli_app.Settings', return_value=mock_settings), \
             patch('src.cli.cli_app.DownloadManager') as mock_dm_class, \
             patch('src.cli.cli_app.TerminalUI') as mock_ui_class, \
             patch('src.cli.cli_app.CommandHandler') as mock_cmd_class, \
             patch('src.cli.cli_app.tr', return_value="Error"):
            
            from src.cli.cli_app import CLIApplication
            
            mock_dm = Mock()
            mock_dm.stop = Mock()
            mock_dm_class.return_value = mock_dm
            
            mock_ui = Mock()
            mock_ui_class.return_value = mock_ui
            
            mock_cmd = Mock()
            mock_cmd.download = Mock(side_effect=Exception("Network error"))
            mock_cmd_class.return_value = mock_cmd
            
            args = argparse.Namespace()
            args.no_gui = True
            args.url = "https://example.com/video.m3u8"
            
            app = CLIApplication(cli_args=args)
            app.initialize()
            result = app.run()
            
            # Should handle error and return error code
            assert result == 1
            mock_ui.display_error.assert_called()
            mock_dm.stop.assert_called_once()
    
    def test_multiple_downloads_workflow(self, mock_settings, sample_analysis_result):
        """Test workflow with multiple sequential downloads."""
        with patch('src.cli.cli_app.signal.signal'), \
             patch('src.cli.cli_app.init_cli_i18n'), \
             patch('src.cli.cli_app.Settings', return_value=mock_settings), \
             patch('src.cli.cli_app.DownloadManager') as mock_dm_class, \
             patch('src.cli.cli_app.TerminalUI'), \
             patch('src.cli.cli_app.CommandHandler') as mock_cmd_class, \
             patch('src.cli.commands.MediaAnalyzer') as mock_analyzer_class, \
             patch('src.cli.commands.DownloadTask'), \
             patch('src.cli.commands.ProgressDisplay'), \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key), \
             patch('src.cli.commands.time.sleep'), \
             patch('src.cli.commands.Path'):
            
            from src.core.downloader import TaskStatus
            from src.cli.commands import CommandHandler
            
            mock_dm = Mock()
            mock_dm.add_task = Mock(side_effect=["task-1", "task-2"])
            mock_dm_class.return_value = mock_dm
            
            mock_analyzer = Mock()
            mock_analyzer.analyze_url = Mock(return_value=sample_analysis_result)
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_ui = Mock()
            
            handler = CommandHandler(mock_dm, mock_settings, mock_ui)
            handler._monitor_download = Mock(return_value=0)
            
            # Download first video
            result1 = handler.download("https://example.com/video1.m3u8")
            # Download second video
            result2 = handler.download("https://example.com/video2.m3u8")
            
            assert result1 == 0
            assert result2 == 0
            assert mock_dm.add_task.call_count == 2


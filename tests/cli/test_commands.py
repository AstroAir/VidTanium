"""
Unit tests for CLI CommandHandler.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path


class TestCommandHandler:
    """Test suite for CommandHandler class."""
    
    def test_initialization(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test CommandHandler initialization."""
        from src.cli.commands import CommandHandler
        
        handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
        
        assert handler.download_manager == mock_download_manager
        assert handler.settings == mock_settings
        assert handler.ui == mock_terminal_ui
    
    def test_download_command_success(self, mock_download_manager, mock_settings, 
                                     mock_terminal_ui, mock_download_task, sample_analysis_result):
        """Test successful download command execution."""
        with patch('src.cli.commands.MediaAnalyzer') as mock_analyzer_class, \
             patch('src.cli.commands.DownloadTask', return_value=mock_download_task), \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key), \
             patch('src.cli.commands.Path'):
            
            # Setup mock analyzer
            mock_analyzer = Mock()
            mock_analyzer.analyze_url = Mock(return_value=sample_analysis_result)
            mock_analyzer_class.return_value = mock_analyzer
            
            # Setup download manager
            mock_download_manager.add_task = Mock(return_value="task-123")
            
            from src.cli.commands import CommandHandler
            
            handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
            handler._monitor_download = Mock(return_value=0)
            
            result = handler.download("https://example.com/video.m3u8", "/output/video.mp4")
            
            assert result == 0
            mock_analyzer.analyze_url.assert_called_once_with("https://example.com/video.m3u8")
            mock_download_manager.add_task.assert_called_once()
            handler._monitor_download.assert_called_once()
    
    def test_download_command_analysis_failure(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test download command when URL analysis fails."""
        with patch('src.cli.commands.MediaAnalyzer') as mock_analyzer_class, \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key):
            
            # Setup mock analyzer to return failure
            mock_analyzer = Mock()
            mock_analyzer.analyze_url = Mock(return_value={
                "success": False,
                "error": "Invalid URL"
            })
            mock_analyzer_class.return_value = mock_analyzer
            
            from src.cli.commands import CommandHandler
            
            handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
            
            result = handler.download("https://invalid.com/video.m3u8")
            
            assert result == 1
            mock_terminal_ui.display_error.assert_called()
    
    def test_download_command_with_exception(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test download command handles exceptions."""
        with patch('src.cli.commands.MediaAnalyzer', side_effect=Exception("Network error")), \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key):
            
            from src.cli.commands import CommandHandler
            
            handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
            
            result = handler.download("https://example.com/video.m3u8")
            
            assert result == 1
            mock_terminal_ui.display_error.assert_called()
    
    def test_monitor_download_completed(self, mock_download_manager, mock_settings, 
                                       mock_terminal_ui, mock_download_task):
        """Test monitoring download that completes successfully."""
        with patch('src.cli.commands.ProgressDisplay') as mock_progress_class, \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key), \
             patch('src.cli.commands.time.sleep'):
            
            from src.core.downloader import TaskStatus
            
            # Setup progress display
            mock_progress = Mock()
            mock_progress.add_task = Mock(return_value="progress-id")
            mock_progress_class.return_value = mock_progress
            
            # Setup task to be completed
            mock_download_task.status = TaskStatus.COMPLETED
            mock_download_task.segments = 100
            
            from src.cli.commands import CommandHandler
            
            handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
            
            result = handler._monitor_download("task-123", mock_download_task)
            
            assert result == 0
            mock_progress.start.assert_called_once()
            mock_progress.stop.assert_called_once()
            mock_terminal_ui.display_success.assert_called()
    
    def test_monitor_download_failed(self, mock_download_manager, mock_settings, 
                                    mock_terminal_ui, mock_download_task):
        """Test monitoring download that fails."""
        with patch('src.cli.commands.ProgressDisplay') as mock_progress_class, \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key), \
             patch('src.cli.commands.time.sleep'):
            
            from src.core.downloader import TaskStatus
            
            mock_progress = Mock()
            mock_progress.add_task = Mock(return_value="progress-id")
            mock_progress_class.return_value = mock_progress
            
            # Setup task to be failed
            mock_download_task.status = TaskStatus.FAILED
            
            from src.cli.commands import CommandHandler
            
            handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
            
            result = handler._monitor_download("task-123", mock_download_task)
            
            assert result == 1
            mock_terminal_ui.display_error.assert_called()
    
    def test_monitor_download_canceled(self, mock_download_manager, mock_settings, 
                                      mock_terminal_ui, mock_download_task):
        """Test monitoring download that is canceled."""
        with patch('src.cli.commands.ProgressDisplay') as mock_progress_class, \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key), \
             patch('src.cli.commands.time.sleep'):
            
            from src.core.downloader import TaskStatus
            
            mock_progress = Mock()
            mock_progress.add_task = Mock(return_value="progress-id")
            mock_progress_class.return_value = mock_progress
            
            # Setup task to be canceled
            mock_download_task.status = TaskStatus.CANCELED
            
            from src.cli.commands import CommandHandler
            
            handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
            
            result = handler._monitor_download("task-123", mock_download_task)
            
            assert result == 130
            mock_terminal_ui.display_warning.assert_called()
    
    def test_monitor_download_keyboard_interrupt(self, mock_download_manager, mock_settings, 
                                                 mock_terminal_ui, mock_download_task):
        """Test monitoring download handles keyboard interrupt."""
        with patch('src.cli.commands.ProgressDisplay') as mock_progress_class, \
             patch('src.cli.commands.tr', side_effect=lambda key, **kwargs: key), \
             patch('src.cli.commands.time.sleep', side_effect=KeyboardInterrupt()):
            
            from src.core.downloader import TaskStatus
            
            mock_progress = Mock()
            mock_progress.add_task = Mock(return_value="progress-id")
            mock_progress_class.return_value = mock_progress
            
            mock_download_task.status = TaskStatus.RUNNING
            
            from src.cli.commands import CommandHandler
            
            handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
            
            result = handler._monitor_download("task-123", mock_download_task)
            
            assert result == 130
            mock_download_manager.cancel_task.assert_called_once_with("task-123")
    
    def test_analyze_url_placeholder(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test analyze_url command (placeholder implementation)."""
        from src.cli.commands import CommandHandler
        
        handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
        
        result = handler.analyze_url("https://example.com/video.m3u8")
        
        # Placeholder should return 0
        assert result == 0
    
    def test_list_tasks_placeholder(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test list_tasks command (placeholder implementation)."""
        from src.cli.commands import CommandHandler
        
        handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
        
        result = handler.list_tasks()
        
        # Placeholder should return 0
        assert result == 0
    
    def test_pause_task_placeholder(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test pause_task command (placeholder implementation)."""
        from src.cli.commands import CommandHandler
        
        handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
        
        result = handler.pause_task("task-123")
        
        # Placeholder should return 0
        assert result == 0
    
    def test_resume_task_placeholder(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test resume_task command (placeholder implementation)."""
        from src.cli.commands import CommandHandler
        
        handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
        
        result = handler.resume_task("task-123")
        
        # Placeholder should return 0
        assert result == 0
    
    def test_cancel_task_placeholder(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test cancel_task command (placeholder implementation)."""
        from src.cli.commands import CommandHandler
        
        handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
        
        result = handler.cancel_task("task-123")
        
        # Placeholder should return 0
        assert result == 0
    
    def test_show_settings_placeholder(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test show_settings command (placeholder implementation)."""
        from src.cli.commands import CommandHandler
        
        handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
        
        result = handler.show_settings()
        
        # Placeholder should return 0
        assert result == 0
    
    def test_update_setting_placeholder(self, mock_download_manager, mock_settings, mock_terminal_ui):
        """Test update_setting command (placeholder implementation)."""
        from src.cli.commands import CommandHandler
        
        handler = CommandHandler(mock_download_manager, mock_settings, mock_terminal_ui)
        
        result = handler.update_setting("key", "value")
        
        # Placeholder should return 0
        assert result == 0


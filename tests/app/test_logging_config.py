import pytest
import sys
import logging
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock, call
from pathlib import Path
from io import StringIO

from src.app.logging_config import (
    configure_logging, get_logger, InterceptHandler, 
    setup_standard_logging_intercept, ensure_logging_configured,
    LOGURU_FORMAT
)


class TestLoggingConfiguration:
    """Test suite for logging configuration functions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset logging configuration state
        import src.app.logging_config
        src.app.logging_config._logging_configured = False
        
        # Create temporary directory for log files
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """Clean up after tests."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.app.logging_config.logger')
    def test_configure_logging_console_only(self, mock_logger) -> None:
        """Test configuring logging with console output only."""
        configure_logging(log_level="INFO", enable_console=True)
        
        # Should remove default handler and add console handler
        mock_logger.remove.assert_called_once()
        mock_logger.add.assert_called_once()
        
        # Check console handler configuration
        call_args = mock_logger.add.call_args
        assert call_args[0][0] == sys.stderr
        assert call_args[1]['format'] == LOGURU_FORMAT
        assert call_args[1]['level'] == "INFO"
        assert call_args[1]['colorize'] is True
        assert call_args[1]['backtrace'] is True
        assert call_args[1]['diagnose'] is True

    @patch('src.app.logging_config.logger')
    def test_configure_logging_file_only(self, mock_logger) -> None:
        """Test configuring logging with file output only."""
        log_file = os.path.join(self.temp_dir, "test.log")
        
        configure_logging(log_file=log_file, log_level="DEBUG", enable_console=False)
        
        # Should remove default handler and add file handler
        mock_logger.remove.assert_called_once()
        mock_logger.add.assert_called_once()
        
        # Check file handler configuration
        call_args = mock_logger.add.call_args
        assert call_args[0][0] == log_file
        assert call_args[1]['format'] == LOGURU_FORMAT
        assert call_args[1]['level'] == "DEBUG"
        assert call_args[1]['rotation'] == "10 MB"
        assert call_args[1]['retention'] == "7 days"
        assert call_args[1]['compression'] == "zip"

    @patch('src.app.logging_config.logger')
    def test_configure_logging_both_console_and_file(self, mock_logger) -> None:
        """Test configuring logging with both console and file output."""
        log_file = os.path.join(self.temp_dir, "test.log")
        
        configure_logging(log_file=log_file, log_level="WARNING", enable_console=True)
        
        # Should remove default handler and add both handlers
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2
        
        # Check that both console and file handlers are added
        call_args_list = mock_logger.add.call_args_list
        console_call = call_args_list[0]
        file_call = call_args_list[1]
        
        assert console_call[0][0] == sys.stderr
        assert file_call[0][0] == log_file

    @patch('src.app.logging_config.logger')
    def test_configure_logging_creates_log_directory(self, mock_logger) -> None:
        """Test that log directory is created if it doesn't exist."""
        log_dir = os.path.join(self.temp_dir, "nested", "log", "dir")
        log_file = os.path.join(log_dir, "test.log")
        
        # Directory shouldn't exist initially
        assert not os.path.exists(log_dir)
        
        configure_logging(log_file=log_file, enable_console=False)
        
        # Directory should be created
        assert os.path.exists(log_dir)

    @patch('src.app.logging_config.logger')
    def test_get_logger_with_name(self, mock_logger) -> None:
        """Test getting logger with specific name."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger
        
        result = get_logger("test_module")
        
        mock_logger.bind.assert_called_once_with(name="test_module")
        assert result == mock_bound_logger

    @patch('src.app.logging_config.logger')
    def test_get_logger_without_name(self, mock_logger) -> None:
        """Test getting logger without name."""
        result = get_logger()
        
        mock_logger.bind.assert_not_called()
        assert result == mock_logger

    @patch('src.app.logging_config.logger')
    def test_get_logger_with_none_name(self, mock_logger) -> None:
        """Test getting logger with None name."""
        result = get_logger(None)
        
        mock_logger.bind.assert_not_called()
        assert result == mock_logger


class TestInterceptHandler:
    """Test suite for InterceptHandler class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.handler = InterceptHandler()

    @patch('src.app.logging_config.logger')
    @patch('sys._getframe')
    def test_emit_with_valid_level(self, mock_getframe, mock_logger) -> None:
        """Test emit method with valid log level."""
        # Mock log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.levelname = "INFO"
        
        # Mock frame
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "other_file.py"
        mock_frame.f_back = None
        mock_getframe.return_value = mock_frame
        
        # Mock logger level
        mock_level = Mock()
        mock_level.name = "INFO"
        mock_logger.level.return_value = mock_level
        
        # Mock logger.opt
        mock_opt = Mock()
        mock_logger.opt.return_value = mock_opt
        
        self.handler.emit(record)
        
        # Verify logger methods called
        mock_logger.level.assert_called_once_with("INFO")
        mock_logger.opt.assert_called_once_with(depth=6, exception=None)
        mock_opt.log.assert_called_once_with("INFO", "Test message")

    @patch('src.app.logging_config.logger')
    @patch('sys._getframe')
    def test_emit_with_invalid_level(self, mock_getframe, mock_logger) -> None:
        """Test emit method with invalid log level."""
        # Mock log record
        record = logging.LogRecord(
            name="test_logger",
            level=99,  # Custom level
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.levelname = "CUSTOM"
        record.levelno = 99
        
        # Mock frame
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "other_file.py"
        mock_frame.f_back = None
        mock_getframe.return_value = mock_frame
        
        # Mock logger level to raise ValueError
        mock_logger.level.side_effect = ValueError("Invalid level")
        
        # Mock logger.opt
        mock_opt = Mock()
        mock_logger.opt.return_value = mock_opt
        
        self.handler.emit(record)
        
        # Should use levelno as string when level name is invalid
        mock_logger.opt.assert_called_once_with(depth=6, exception=None)
        mock_opt.log.assert_called_once_with("99", "Test message")

    @patch('src.app.logging_config.logger')
    @patch('sys._getframe')
    def test_emit_with_exception_info(self, mock_getframe, mock_logger) -> None:
        """Test emit method with exception information."""
        # Create exception info
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
        
        # Mock log record with exception
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        record.levelname = "ERROR"
        
        # Mock frame
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "other_file.py"
        mock_frame.f_back = None
        mock_getframe.return_value = mock_frame
        
        # Mock logger level
        mock_level = Mock()
        mock_level.name = "ERROR"
        mock_logger.level.return_value = mock_level
        
        # Mock logger.opt
        mock_opt = Mock()
        mock_logger.opt.return_value = mock_opt
        
        self.handler.emit(record)
        
        # Verify exception info is passed
        mock_logger.opt.assert_called_once_with(depth=6, exception=exc_info)
        mock_opt.log.assert_called_once_with("ERROR", "Error occurred")

    @patch('src.app.logging_config.logger')
    def test_emit_frame_traversal(self, mock_logger) -> None:
        """Test frame traversal in emit method."""
        # This test is complex due to frame manipulation
        # We'll test the basic functionality
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.levelname = "INFO"
        
        # Mock logger level
        mock_level = Mock()
        mock_level.name = "INFO"
        mock_logger.level.return_value = mock_level
        
        # Mock logger.opt
        mock_opt = Mock()
        mock_logger.opt.return_value = mock_opt
        
        # Should not raise exception
        self.handler.emit(record)
        
        mock_logger.opt.assert_called_once()
        mock_opt.log.assert_called_once()


class TestStandardLoggingIntercept:
    """Test suite for standard logging interception."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Store original handlers
        self.original_handlers = logging.getLogger().handlers.copy()
        self.original_level = logging.getLogger().level

    def teardown_method(self) -> None:
        """Clean up after tests."""
        # Restore original handlers
        logging.getLogger().handlers = self.original_handlers
        logging.getLogger().setLevel(self.original_level)

    def test_setup_standard_logging_intercept(self) -> None:
        """Test setting up standard logging interception."""
        # Add some dummy handlers first
        dummy_handler = logging.StreamHandler()
        logging.getLogger().addHandler(dummy_handler)
        
        setup_standard_logging_intercept()
        
        # Should have exactly one handler (our InterceptHandler)
        handlers = logging.getLogger().handlers
        assert len(handlers) == 1
        assert isinstance(handlers[0], InterceptHandler)
        
        # Should set DEBUG level
        assert logging.getLogger().level == logging.DEBUG

    def test_third_party_logger_levels(self) -> None:
        """Test that third-party loggers are set to WARNING level."""
        setup_standard_logging_intercept()
        
        # Check that specific loggers are set to WARNING
        assert logging.getLogger("requests").level == logging.WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("asyncio").level == logging.WARNING


class TestEnsureLoggingConfigured:
    """Test suite for ensure_logging_configured function."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset configuration state
        import src.app.logging_config
        src.app.logging_config._logging_configured = False

    @patch('src.app.logging_config.setup_standard_logging_intercept')
    @patch('src.app.logging_config.configure_logging')
    def test_ensure_logging_configured_first_call(self, mock_configure, mock_setup) -> None:
        """Test ensure_logging_configured on first call."""
        ensure_logging_configured()
        
        # Should call both configuration functions
        mock_configure.assert_called_once()
        mock_setup.assert_called_once()
        
        # Should set flag to True
        import src.app.logging_config
        assert src.app.logging_config._logging_configured is True

    @patch('src.app.logging_config.setup_standard_logging_intercept')
    @patch('src.app.logging_config.configure_logging')
    def test_ensure_logging_configured_subsequent_calls(self, mock_configure, mock_setup) -> None:
        """Test ensure_logging_configured on subsequent calls."""
        # Call once
        ensure_logging_configured()
        
        # Reset mocks
        mock_configure.reset_mock()
        mock_setup.reset_mock()
        
        # Call again
        ensure_logging_configured()
        
        # Should not call configuration functions again
        mock_configure.assert_not_called()
        mock_setup.assert_not_called()


class TestLoguruFormat:
    """Test suite for LOGURU_FORMAT constant."""

    def test_format_contains_required_elements(self) -> None:
        """Test that LOGURU_FORMAT contains required elements."""
        assert "{time:YYYY-MM-DD HH:mm:ss.SSS}" in LOGURU_FORMAT
        assert "{level: <8}" in LOGURU_FORMAT
        assert "{name}" in LOGURU_FORMAT
        assert "{function}" in LOGURU_FORMAT
        assert "{line}" in LOGURU_FORMAT
        assert "{message}" in LOGURU_FORMAT

    def test_format_has_colors(self) -> None:
        """Test that LOGURU_FORMAT includes color tags."""
        assert "<green>" in LOGURU_FORMAT
        assert "</green>" in LOGURU_FORMAT
        assert "<level>" in LOGURU_FORMAT
        assert "</level>" in LOGURU_FORMAT
        assert "<cyan>" in LOGURU_FORMAT
        assert "</cyan>" in LOGURU_FORMAT


class TestIntegration:
    """Integration tests for logging configuration."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset configuration state
        import src.app.logging_config
        src.app.logging_config._logging_configured = False
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """Clean up after tests."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.app.logging_config.logger')
    def test_full_logging_setup(self, mock_logger) -> None:
        """Test complete logging setup process."""
        log_file = os.path.join(self.temp_dir, "app.log")
        
        # Configure logging
        configure_logging(log_file=log_file, log_level="INFO", enable_console=True)
        
        # Setup interception
        setup_standard_logging_intercept()
        
        # Get logger
        app_logger = get_logger("test_app")
        
        # Verify configuration
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count == 2  # Console + file
        mock_logger.bind.assert_called_once_with(name="test_app")

    def test_standard_logging_integration(self) -> None:
        """Test that standard logging integrates with loguru."""
        # Setup interception
        setup_standard_logging_intercept()
        
        # Get standard logger
        std_logger = logging.getLogger("test_integration")
        
        # Should have InterceptHandler
        root_handlers = logging.getLogger().handlers
        assert len(root_handlers) == 1
        assert isinstance(root_handlers[0], InterceptHandler)
        
        # Should not raise exception when logging
        std_logger.info("Test message")
        std_logger.error("Test error")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

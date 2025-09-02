import pytest
import time
import random
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, List, Optional, Any

from src.core.error_handler import (
    EnhancedErrorHandler, RetryStrategy, RetryConfig, ErrorReport,
    error_handler
)
from src.core.exceptions import (
    VidTaniumException, ErrorCategory, ErrorSeverity, ErrorContext,
    NetworkException, ConnectionTimeoutException, HTTPException,
    FilesystemException, EncryptionException, ValidationException,
    ResourceException, SystemException, UserAction,
    PermissionException, InsufficientSpaceException, DecryptionKeyException,
    MemoryException
)


class TestRetryStrategy:
    """Test suite for RetryStrategy enum."""

    def test_strategy_values(self):
        """Test enum values."""
        assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"
        assert RetryStrategy.LINEAR_BACKOFF.value == "linear_backoff"
        assert RetryStrategy.FIXED_DELAY.value == "fixed_delay"
        assert RetryStrategy.IMMEDIATE.value == "immediate"
        assert RetryStrategy.NO_RETRY.value == "no_retry"


class TestRetryConfig:
    """Test suite for RetryConfig dataclass."""

    def test_config_creation(self):
        """Test RetryConfig creation with all fields."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            jitter=True,
            backoff_multiplier=3.0
        )
        
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.jitter is True
        assert config.backoff_multiplier == 3.0

    def test_config_defaults(self):
        """Test RetryConfig with default values."""
        config = RetryConfig()
        
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter is True
        assert config.backoff_multiplier == 2.0


class TestErrorReport:
    """Test suite for ErrorReport dataclass."""

    def test_report_creation(self):
        """Test ErrorReport creation with all fields."""
        context = ErrorContext(task_id="test_task", url="https://example.com")
        
        report = ErrorReport(
            title="Network Error",
            message="Connection failed",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK,
            suggested_actions=[UserAction.RETRY, UserAction.CHECK_NETWORK],
            technical_details={"status_code": 404},
            is_retryable=True,
            retry_count=2,
            context=context
        )
        
        assert report.title == "Network Error"
        assert report.message == "Connection failed"
        assert report.severity == ErrorSeverity.HIGH
        assert report.category == ErrorCategory.NETWORK
        assert UserAction.RETRY in report.suggested_actions
        assert report.technical_details["status_code"] == 404
        assert report.is_retryable is True
        assert report.retry_count == 2
        assert report.context == context


class TestEnhancedErrorHandler:
    """Test suite for EnhancedErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = EnhancedErrorHandler()

    def test_initialization(self):
        """Test EnhancedErrorHandler initialization."""
        assert isinstance(self.handler.retry_configs, dict)
        assert isinstance(self.handler.error_history, list)
        assert self.handler.max_history_size == 1000
        
        # Check default retry configs exist for all categories
        for category in ErrorCategory:
            assert category in self.handler.retry_configs

    def test_get_default_retry_configs(self):
        """Test default retry configuration setup."""
        configs = self.handler._get_default_retry_configs()
        
        assert ErrorCategory.NETWORK in configs
        assert ErrorCategory.FILESYSTEM in configs
        assert ErrorCategory.ENCRYPTION in configs
        
        # Network should have exponential backoff
        network_config = configs[ErrorCategory.NETWORK]
        assert network_config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert network_config.max_retries > 0

    def test_handle_exception_vidtanium_exception(self):
        """Test handling VidTaniumException (should return as-is with context update)."""
        context = ErrorContext(task_id="test_task")
        original_exception = NetworkException("Network error")
        
        result = self.handler.handle_exception(original_exception, context, "test_op")
        
        assert result == original_exception
        assert result.context == context

    def test_handle_exception_generic_exception(self):
        """Test handling generic exception (should convert to VidTaniumException)."""
        context = ErrorContext(task_id="test_task", url="https://example.com")
        generic_exception = Exception("Generic error")
        
        result = self.handler.handle_exception(generic_exception, context, "test_op")
        
        assert isinstance(result, VidTaniumException)
        assert result.context == context

    def test_convert_exception_timeout(self):
        """Test conversion of timeout exceptions."""
        context = ErrorContext(url="https://example.com")
        timeout_exception = Exception("Connection timed out")
        
        result = self.handler._convert_exception(timeout_exception, context, "download")
        
        assert isinstance(result, ConnectionTimeoutException)
        assert result.url == "https://example.com"
        assert result.context == context

    def test_convert_exception_http_error(self):
        """Test conversion of HTTP exceptions."""
        context = ErrorContext(url="https://example.com")
        http_exception = Exception("HTTP 404 Not Found")
        
        result = self.handler._convert_exception(http_exception, context, "download")
        
        assert isinstance(result, HTTPException)
        assert result.status_code == 404
        assert result.url == "https://example.com"

    def test_convert_exception_network_error(self):
        """Test conversion of network exceptions."""
        context = ErrorContext(url="https://example.com")
        network_exception = Exception("Connection refused")
        
        result = self.handler._convert_exception(network_exception, context, "download")
        
        assert isinstance(result, NetworkException)
        assert "Connection refused" in result.message

    def test_convert_exception_permission_error(self):
        """Test conversion of permission exceptions."""
        context = ErrorContext(file_path="/protected/file.mp4")
        permission_exception = Exception("Permission denied")
        
        result = self.handler._convert_exception(permission_exception, context, "save_file")
        
        assert isinstance(result, PermissionException)
        assert result.file_path == "/protected/file.mp4"

    def test_convert_exception_filesystem_error(self):
        """Test conversion of filesystem exceptions."""
        context = ErrorContext(file_path="/missing/file.mp4")
        fs_exception = Exception("File not found")
        
        result = self.handler._convert_exception(fs_exception, context, "read_file")
        
        assert isinstance(result, FilesystemException)

    def test_convert_exception_encryption_error(self):
        """Test conversion of encryption exceptions."""
        context = ErrorContext(url="https://example.com/key.bin")
        encryption_exception = Exception("Decryption failed")
        
        result = self.handler._convert_exception(encryption_exception, context, "decrypt")
        
        assert isinstance(result, DecryptionKeyException)
        assert result.key_url == "https://example.com/key.bin"

    def test_convert_exception_memory_error(self):
        """Test conversion of memory exceptions."""
        context = ErrorContext(task_id="test_task")
        memory_exception = Exception("Out of memory")
        
        result = self.handler._convert_exception(memory_exception, context, "process_video")
        
        assert isinstance(result, MemoryException)
        assert result.operation == "process_video"

    def test_convert_exception_fallback(self):
        """Test fallback conversion for unknown exceptions."""
        context = ErrorContext(task_id="test_task")
        unknown_exception = Exception("Unknown error")
        
        result = self.handler._convert_exception(unknown_exception, context, "unknown_op")
        
        assert isinstance(result, SystemException)
        assert "Unknown error" in result.message

    def test_should_retry(self):
        """Test retry decision logic."""
        # Retryable exception
        network_exception = NetworkException("Connection failed")
        assert self.handler.should_retry(network_exception, 1) is True
        
        # Non-retryable exception
        validation_exception = ValidationException("Invalid input")
        assert self.handler.should_retry(validation_exception, 1) is False
        
        # Max retries exceeded
        assert self.handler.should_retry(network_exception, 10) is False

    def test_calculate_retry_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False
        )
        
        delay1 = self.handler.calculate_retry_delay(config, 1)
        delay2 = self.handler.calculate_retry_delay(config, 2)
        delay3 = self.handler.calculate_retry_delay(config, 3)
        
        assert delay1 == 2.0  # base_delay * multiplier^1
        assert delay2 == 4.0  # base_delay * multiplier^2
        assert delay3 == 8.0  # base_delay * multiplier^3

    def test_calculate_retry_delay_linear(self):
        """Test linear backoff delay calculation."""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=1.0,
            jitter=False
        )
        
        delay1 = self.handler.calculate_retry_delay(config, 1)
        delay2 = self.handler.calculate_retry_delay(config, 2)
        delay3 = self.handler.calculate_retry_delay(config, 3)
        
        assert delay1 == 1.0  # base_delay * 1
        assert delay2 == 2.0  # base_delay * 2
        assert delay3 == 3.0  # base_delay * 3

    def test_calculate_retry_delay_fixed(self):
        """Test fixed delay calculation."""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=5.0,
            jitter=False
        )
        
        delay1 = self.handler.calculate_retry_delay(config, 1)
        delay2 = self.handler.calculate_retry_delay(config, 5)
        
        assert delay1 == 5.0
        assert delay2 == 5.0

    def test_calculate_retry_delay_immediate(self):
        """Test immediate retry (no delay)."""
        config = RetryConfig(strategy=RetryStrategy.IMMEDIATE)
        
        delay = self.handler.calculate_retry_delay(config, 1)
        assert delay == 0.0

    def test_calculate_retry_delay_no_retry(self):
        """Test no retry strategy."""
        config = RetryConfig(strategy=RetryStrategy.NO_RETRY)
        
        delay = self.handler.calculate_retry_delay(config, 1)
        assert delay == 0.0

    def test_calculate_retry_delay_max_limit(self):
        """Test maximum delay limit enforcement."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=10.0,
            max_delay=30.0,
            backoff_multiplier=5.0,
            jitter=False
        )
        
        delay = self.handler.calculate_retry_delay(config, 5)  # Would be 10 * 5^5 = 31250
        assert delay == 30.0  # Should be capped at max_delay

    @patch('random.random')
    def test_calculate_retry_delay_jitter(self, mock_random):
        """Test jitter application."""
        mock_random.return_value = 0.5  # Fixed random value
        
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=10.0,
            jitter=True
        )
        
        delay = self.handler.calculate_retry_delay(config, 1)
        expected_jitter = 10.0 * 0.1 * 0.5  # delay * 0.1 * random
        expected_delay = 10.0 + expected_jitter
        
        assert delay == expected_delay

    def test_create_error_report(self):
        """Test error report creation."""
        exception = NetworkException("Connection failed")
        exception.context = ErrorContext(task_id="test_task")
        
        report = self.handler.create_error_report(exception, retry_count=2)
        
        assert isinstance(report, ErrorReport)
        assert report.category == ErrorCategory.NETWORK
        assert report.retry_count == 2
        assert report.context == exception.context

    def test_get_error_title(self):
        """Test error title generation."""
        network_exception = NetworkException("Connection failed")
        title = self.handler._get_error_title(network_exception)
        
        assert "Network" in title

    def test_log_error(self):
        """Test error logging."""
        exception = NetworkException("Test error")
        
        # Should not raise exception
        self.handler._log_error(exception)

    def test_add_to_history(self):
        """Test adding errors to history."""
        exception = NetworkException("Test error")
        
        self.handler._add_to_history("test_operation", exception)
        
        assert len(self.handler.error_history) == 1
        assert self.handler.error_history[0][0] == "test_operation"
        assert self.handler.error_history[0][1] == exception

    def test_history_size_limit(self):
        """Test error history size limit."""
        # Set small limit for testing
        self.handler.max_history_size = 3
        
        # Add more errors than limit
        for i in range(5):
            exception = NetworkException(f"Error {i}")
            self.handler._add_to_history(f"operation_{i}", exception)
        
        # Should only keep the most recent errors
        assert len(self.handler.error_history) == 3
        assert self.handler.error_history[0][0] == "operation_2"  # Oldest kept
        assert self.handler.error_history[-1][0] == "operation_4"  # Most recent

    def test_get_error_statistics_empty(self):
        """Test error statistics with no errors."""
        stats = self.handler.get_error_statistics()
        assert stats == {}

    def test_get_error_statistics_with_errors(self):
        """Test error statistics with errors."""
        # Add some errors
        network_error = NetworkException("Network error")
        fs_error = FilesystemException("File error")
        
        self.handler._add_to_history("op1", network_error)
        self.handler._add_to_history("op2", fs_error)
        self.handler._add_to_history("op3", network_error)
        
        stats = self.handler.get_error_statistics()
        
        assert stats["total_errors_last_hour"] == 3
        assert stats["category_breakdown"]["network"] == 2
        assert stats["category_breakdown"]["filesystem"] == 1
        assert stats["most_common_category"] == "network"

    def test_set_retry_config(self):
        """Test setting custom retry configuration."""
        custom_config = RetryConfig(
            strategy=RetryStrategy.LINEAR_BACKOFF,
            max_retries=10,
            base_delay=0.5
        )
        
        self.handler.set_retry_config(ErrorCategory.NETWORK, custom_config)
        
        assert self.handler.retry_configs[ErrorCategory.NETWORK] == custom_config

    def test_get_retry_config(self):
        """Test getting retry configuration."""
        config = self.handler.get_retry_config(ErrorCategory.NETWORK)
        
        assert isinstance(config, RetryConfig)
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF

    def test_clear_error_history(self):
        """Test clearing error history."""
        # Add some errors
        exception = NetworkException("Test error")
        self.handler._add_to_history("test_op", exception)
        
        assert len(self.handler.error_history) > 0
        
        self.handler.clear_error_history()
        
        assert len(self.handler.error_history) == 0

    def test_global_error_handler_instance(self):
        """Test global error handler instance."""
        assert error_handler is not None
        assert isinstance(error_handler, EnhancedErrorHandler)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

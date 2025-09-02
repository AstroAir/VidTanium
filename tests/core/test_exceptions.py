import pytest
from typing import Dict, Any, List, Optional

from src.core.exceptions import (
    ErrorSeverity, ErrorCategory, ErrorContext, UserAction,
    VidTaniumException, NetworkException, ConnectionTimeoutException,
    HTTPException, FilesystemException, PermissionException,
    InsufficientSpaceException, EncryptionException, DecryptionKeyException,
    ValidationException, InvalidURLException, InvalidSegmentException,
    ResourceException, MemoryException, SystemException,
    ConfigurationException
)


class TestErrorSeverity:
    """Test suite for ErrorSeverity enum."""

    def test_severity_values(self):
        """Test enum values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorCategory:
    """Test suite for ErrorCategory enum."""

    def test_category_values(self):
        """Test enum values."""
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.FILESYSTEM.value == "filesystem"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.RESOURCE.value == "resource"
        assert ErrorCategory.ENCRYPTION.value == "encryption"
        assert ErrorCategory.PARSING.value == "parsing"
        assert ErrorCategory.SYSTEM.value == "system"


class TestErrorContext:
    """Test suite for ErrorContext dataclass."""

    def test_context_creation(self):
        """Test ErrorContext creation with all fields."""
        context = ErrorContext(
            task_id="test_task",
            task_name="Test Task",
            url="https://example.com",
            file_path="/downloads/video.mp4",
            segment_index=5,
            retry_count=2,
            additional_info={"key": "value"}
        )
        
        assert context.task_id == "test_task"
        assert context.task_name == "Test Task"
        assert context.url == "https://example.com"
        assert context.file_path == "/downloads/video.mp4"
        assert context.segment_index == 5
        assert context.retry_count == 2
        assert context.additional_info == {"key": "value"}

    def test_context_defaults(self):
        """Test ErrorContext with default values."""
        context = ErrorContext()
        
        assert context.task_id is None
        assert context.task_name is None
        assert context.url is None
        assert context.file_path is None
        assert context.segment_index is None
        assert context.retry_count is None
        assert context.additional_info is None


class TestUserAction:
    """Test suite for UserAction dataclass."""

    def test_action_creation(self):
        """Test UserAction creation with all fields."""
        action = UserAction(
            action_type="retry",
            description="Retry the download",
            is_automatic=True,
            priority=1
        )
        
        assert action.action_type == "retry"
        assert action.description == "Retry the download"
        assert action.is_automatic is True
        assert action.priority == 1

    def test_action_defaults(self):
        """Test UserAction with default values."""
        action = UserAction(
            action_type="check_connection",
            description="Check your internet connection"
        )
        
        assert action.is_automatic is False
        assert action.priority == 1


class TestVidTaniumException:
    """Test suite for VidTaniumException base class."""

    def test_exception_creation_minimal(self):
        """Test VidTaniumException creation with minimal parameters."""
        exception = VidTaniumException(
            message="Test error",
            category=ErrorCategory.NETWORK
        )
        
        assert exception.message == "Test error"
        assert exception.category == ErrorCategory.NETWORK
        assert exception.severity == ErrorSeverity.MEDIUM
        assert isinstance(exception.context, ErrorContext)
        assert exception.suggested_actions == []
        assert exception.is_retryable is False
        assert exception.max_retries == 3
        assert exception.original_exception is None

    def test_exception_creation_full(self):
        """Test VidTaniumException creation with all parameters."""
        context = ErrorContext(task_id="test_task")
        actions = [UserAction("retry", "Retry operation")]
        original_exc = Exception("Original error")
        
        exception = VidTaniumException(
            message="Test error",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            context=context,
            suggested_actions=actions,
            is_retryable=True,
            max_retries=5,
            original_exception=original_exc
        )
        
        assert exception.message == "Test error"
        assert exception.category == ErrorCategory.NETWORK
        assert exception.severity == ErrorSeverity.HIGH
        assert exception.context == context
        assert exception.suggested_actions == actions
        assert exception.is_retryable is True
        assert exception.max_retries == 5
        assert exception.original_exception == original_exc

    def test_get_user_friendly_message_no_context(self):
        """Test user-friendly message without context."""
        exception = VidTaniumException(
            message="Test error",
            category=ErrorCategory.NETWORK
        )
        
        message = exception.get_user_friendly_message()
        assert message == "Test error"

    def test_get_user_friendly_message_with_task_name(self):
        """Test user-friendly message with task name in context."""
        context = ErrorContext(task_name="Download Video")
        exception = VidTaniumException(
            message="Connection failed",
            category=ErrorCategory.NETWORK,
            context=context
        )
        
        message = exception.get_user_friendly_message()
        assert message == "Task 'Download Video': Connection failed"

    def test_get_technical_details(self):
        """Test technical details generation."""
        context = ErrorContext(
            task_id="test_task",
            url="https://example.com",
            retry_count=2
        )
        original_exc = ValueError("Original error")
        
        exception = VidTaniumException(
            message="Test error",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            context=context,
            is_retryable=True,
            max_retries=5,
            original_exception=original_exc
        )
        
        details = exception.get_technical_details()
        
        assert details["category"] == "network"
        assert details["severity"] == "high"
        assert details["is_retryable"] is True
        assert details["max_retries"] == 5
        assert details["context"]["task_id"] == "test_task"
        assert details["context"]["url"] == "https://example.com"
        assert details["context"]["retry_count"] == 2
        assert details["original_exception"]["type"] == "ValueError"
        assert details["original_exception"]["message"] == "Original error"


class TestNetworkExceptions:
    """Test suite for network-related exceptions."""

    def test_network_exception(self):
        """Test NetworkException creation."""
        exception = NetworkException("Network error")
        
        assert exception.category == ErrorCategory.NETWORK
        assert exception.severity == ErrorSeverity.MEDIUM
        assert exception.is_retryable is True
        assert exception.max_retries == 3

    def test_connection_timeout_exception(self):
        """Test ConnectionTimeoutException creation."""
        exception = ConnectionTimeoutException(
            url="https://example.com",
            timeout_seconds=30
        )
        
        assert "Connection timeout after 30s" in exception.message
        assert "https://example.com" in exception.message
        assert exception.category == ErrorCategory.NETWORK
        assert exception.is_retryable is True
        assert exception.max_retries == 5
        assert len(exception.suggested_actions) > 0

    def test_http_exception_404(self):
        """Test HTTPException with 404 status."""
        exception = HTTPException(
            status_code=404,
            url="https://example.com/missing"
        )
        
        assert exception.status_code == 404
        assert "404" in exception.message
        assert "https://example.com/missing" in exception.message
        assert exception.is_retryable is False
        assert any("check_url" in action.action_type for action in exception.suggested_actions)

    def test_http_exception_403(self):
        """Test HTTPException with 403 status."""
        exception = HTTPException(
            status_code=403,
            url="https://example.com/forbidden"
        )
        
        assert exception.status_code == 403
        assert "403" in exception.message
        assert exception.is_retryable is False
        assert any("check_auth" in action.action_type for action in exception.suggested_actions)

    def test_http_exception_500(self):
        """Test HTTPException with 500 status."""
        exception = HTTPException(
            status_code=500,
            url="https://example.com/error"
        )
        
        assert exception.status_code == 500
        assert "500" in exception.message
        assert exception.is_retryable is True
        assert exception.severity == ErrorSeverity.HIGH


class TestFilesystemExceptions:
    """Test suite for filesystem-related exceptions."""

    def test_filesystem_exception(self):
        """Test FilesystemException creation."""
        exception = FilesystemException("File error")
        
        assert exception.category == ErrorCategory.FILESYSTEM
        assert exception.severity == ErrorSeverity.MEDIUM

    def test_permission_exception(self):
        """Test PermissionException creation."""
        exception = PermissionException(
            path="/protected/file.mp4",
            operation="write"
        )
        
        assert "Permission denied" in exception.message
        assert "/protected/file.mp4" in exception.message
        assert "write" in exception.message
        assert exception.severity == ErrorSeverity.HIGH
        assert any("check_permissions" in action.action_type for action in exception.suggested_actions)

    def test_insufficient_space_exception(self):
        """Test InsufficientSpaceException creation."""
        exception = InsufficientSpaceException(
            required_bytes=1048576,
            available_bytes=524288,
            path="/downloads"
        )
        
        assert "Insufficient disk space" in exception.message
        assert "/downloads" in exception.message
        assert exception.severity == ErrorSeverity.HIGH


class TestEncryptionExceptions:
    """Test suite for encryption-related exceptions."""

    def test_encryption_exception(self):
        """Test EncryptionException creation."""
        exception = EncryptionException("Encryption error")
        
        assert exception.category == ErrorCategory.ENCRYPTION
        assert exception.severity == ErrorSeverity.HIGH

    def test_decryption_key_exception_with_url(self):
        """Test DecryptionKeyException with key URL."""
        exception = DecryptionKeyException(
            key_url="https://example.com/key.bin"
        )
        
        assert "https://example.com/key.bin" in exception.message
        assert exception.is_retryable is True
        assert exception.max_retries == 3
        assert any("check_key_url" in action.action_type for action in exception.suggested_actions)

    def test_decryption_key_exception_without_url(self):
        """Test DecryptionKeyException without key URL."""
        exception = DecryptionKeyException()
        
        assert "missing or invalid" in exception.message
        assert exception.is_retryable is True


class TestValidationExceptions:
    """Test suite for validation-related exceptions."""

    def test_validation_exception(self):
        """Test ValidationException creation."""
        exception = ValidationException("Validation error")
        
        assert exception.category == ErrorCategory.VALIDATION
        assert exception.severity == ErrorSeverity.MEDIUM

    def test_invalid_url_exception(self):
        """Test InvalidURLException creation."""
        exception = InvalidURLException("invalid-url")
        
        assert "Invalid URL format" in exception.message
        assert "invalid-url" in exception.message
        assert any("check_url" in action.action_type for action in exception.suggested_actions)

    def test_invalid_segment_exception(self):
        """Test InvalidSegmentException creation."""
        exception = InvalidSegmentException(
            segment_index=5,
            reason="corrupted data"
        )
        
        assert "Invalid segment 5" in exception.message
        assert "corrupted data" in exception.message
        assert exception.is_retryable is True
        assert any("retry_segment" in action.action_type for action in exception.suggested_actions)


class TestResourceExceptions:
    """Test suite for resource-related exceptions."""

    def test_resource_exception(self):
        """Test ResourceException creation."""
        exception = ResourceException("Resource error")
        
        assert exception.category == ErrorCategory.RESOURCE

    def test_memory_exception(self):
        """Test MemoryException creation."""
        exception = MemoryException("video_processing")
        
        assert "Insufficient memory" in exception.message
        assert "video_processing" in exception.message
        assert exception.severity == ErrorSeverity.HIGH
        assert any("close_apps" in action.action_type for action in exception.suggested_actions)


class TestSystemExceptions:
    """Test suite for system-related exceptions."""

    def test_system_exception(self):
        """Test SystemException creation."""
        exception = SystemException("System error")
        
        assert exception.category == ErrorCategory.SYSTEM
        assert exception.severity == ErrorSeverity.CRITICAL

    def test_configuration_exception(self):
        """Test ConfigurationException creation."""
        exception = ConfigurationException(
            setting="max_concurrent_downloads",
            value=-1
        )
        
        assert "Invalid configuration" in exception.message
        assert "max_concurrent_downloads" in exception.message
        assert "-1" in exception.message
        assert any("reset_settings" in action.action_type for action in exception.suggested_actions)


class TestExceptionInheritance:
    """Test suite for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_vidtanium_exception(self):
        """Test that all custom exceptions inherit from VidTaniumException."""
        exceptions_to_test = [
            NetworkException("test"),
            ConnectionTimeoutException("http://test.com", 30),
            HTTPException(404, "http://test.com"),
            FilesystemException("test"),
            PermissionException("/test", "read"),
            InsufficientSpaceException(1000, 500, "/test"),
            EncryptionException("test"),
            DecryptionKeyException(),
            ValidationException("test"),
            InvalidURLException("invalid"),
            InvalidSegmentException(1, "test"),
            ResourceException("test"),
            MemoryException("test"),
            SystemException("test"),
            ConfigurationException("test", "value")
        ]
        
        for exception in exceptions_to_test:
            assert isinstance(exception, VidTaniumException)
            assert isinstance(exception, Exception)

    def test_exception_categories_are_correct(self):
        """Test that exceptions have correct categories."""
        test_cases = [
            (NetworkException("test"), ErrorCategory.NETWORK),
            (FilesystemException("test"), ErrorCategory.FILESYSTEM),
            (EncryptionException("test"), ErrorCategory.ENCRYPTION),
            (ValidationException("test"), ErrorCategory.VALIDATION),
            (ResourceException("test"), ErrorCategory.RESOURCE),
            (SystemException("test"), ErrorCategory.SYSTEM)
        ]
        
        for exception, expected_category in test_cases:
            assert exception.category == expected_category


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

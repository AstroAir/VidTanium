"""
Enhanced Exception System for VidTanium Download Operations
Provides comprehensive error classification and user-friendly error handling
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RESOURCE = "resource"
    ENCRYPTION = "encryption"
    PARSING = "parsing"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Additional context information for errors"""
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    segment_index: Optional[int] = None
    retry_count: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = None


@dataclass
class UserAction:
    """Suggested user action for error resolution"""
    action_type: str  # "retry", "check_connection", "check_permissions", etc.
    description: str
    is_automatic: bool = False
    priority: int = 1  # 1 = highest priority


class VidTaniumException(Exception):
    """Base exception class for VidTanium with enhanced error information"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        suggested_actions: Optional[List[UserAction]] = None,
        is_retryable: bool = False,
        max_retries: int = 3,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context: ErrorContext = context or ErrorContext()
        self.suggested_actions = suggested_actions or []
        self.is_retryable = is_retryable
        self.max_retries = max_retries
        self.original_exception = original_exception
        
    def get_user_friendly_message(self) -> str:
        """Get user-friendly error message"""
        base_message = self.message
        
        if self.context and self.context.task_name:
            base_message = f"Task '{self.context.task_name}': {base_message}"
            
        return base_message
    
    def get_technical_details(self) -> Dict[str, Any]:
        """Get technical details for debugging"""
        details: Dict[str, Any] = {
            "category": self.category.value,
            "severity": self.severity.value,
            "is_retryable": self.is_retryable,
            "max_retries": self.max_retries
        }
        
        if self.context:
            details["context"] = {
                "task_id": self.context.task_id,
                "task_name": self.context.task_name,
                "url": self.context.url,
                "file_path": self.context.file_path,
                "segment_index": self.context.segment_index,
                "retry_count": self.context.retry_count,
                "additional_info": self.context.additional_info
            }
            
        if self.original_exception:
            details["original_exception"] = {
                "type": type(self.original_exception).__name__,
                "message": str(self.original_exception)
            }
            
        return details


# Network-related exceptions
class NetworkException(VidTaniumException):
    """Base class for network-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            is_retryable=True,
            **kwargs
        )


class ConnectionTimeoutException(NetworkException):
    """Connection timeout error"""
    
    def __init__(self, url: str, timeout_seconds: int, **kwargs):
        message = f"Connection timeout after {timeout_seconds}s while accessing {url}"
        suggested_actions = [
            UserAction("check_connection", "Check your internet connection", priority=1),
            UserAction("retry", "Retry the download", is_automatic=True, priority=2),
            UserAction("increase_timeout", "Increase timeout in settings", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            max_retries=5,
            **kwargs
        )


class HTTPException(NetworkException):
    """HTTP error responses"""
    
    def __init__(self, status_code: int, url: str, **kwargs):
        self.status_code = status_code
        message = f"HTTP {status_code} error while accessing {url}"
        
        # Customize message and actions based on status code
        if status_code == 404:
            message = f"Resource not found (404): {url}"
            suggested_actions = [
                UserAction("check_url", "Verify the URL is correct", priority=1),
                UserAction("contact_support", "Contact content provider", priority=2)
            ]
            is_retryable = False
        elif status_code == 403:
            message = f"Access forbidden (403): {url}"
            suggested_actions = [
                UserAction("check_auth", "Check authentication credentials", priority=1),
                UserAction("check_permissions", "Verify access permissions", priority=2)
            ]
            is_retryable = False
        elif status_code >= 500:
            message = f"Server error ({status_code}): {url}"
            suggested_actions = [
                UserAction("retry", "Retry after server recovery", is_automatic=True, priority=1),
                UserAction("wait", "Wait and try again later", priority=2)
            ]
            is_retryable = True
        else:
            suggested_actions = [
                UserAction("retry", "Retry the request", is_automatic=True, priority=1)
            ]
            is_retryable = status_code >= 500
            
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            is_retryable=is_retryable,
            severity=ErrorSeverity.HIGH if status_code >= 500 else ErrorSeverity.MEDIUM,
            **kwargs
        )


# Filesystem-related exceptions
class FilesystemException(VidTaniumException):
    """Base class for filesystem-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.FILESYSTEM,
            **kwargs
        )


class InsufficientSpaceException(FilesystemException):
    """Insufficient disk space error"""
    
    def __init__(self, required_space: int, available_space: int, path: str, **kwargs):
        message = f"Insufficient disk space. Required: {required_space} bytes, Available: {available_space} bytes at {path}"
        suggested_actions = [
            UserAction("free_space", "Free up disk space", priority=1),
            UserAction("change_location", "Choose a different download location", priority=2),
            UserAction("cleanup", "Run disk cleanup", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class PermissionException(FilesystemException):
    """File permission error"""
    
    def __init__(self, path: str, operation: str, **kwargs):
        message = f"Permission denied: Cannot {operation} file/directory at {path}"
        suggested_actions = [
            UserAction("check_permissions", "Check file/folder permissions", priority=1),
            UserAction("run_as_admin", "Run application as administrator", priority=2),
            UserAction("change_location", "Choose a different location", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


# Encryption-related exceptions
class EncryptionException(VidTaniumException):
    """Base class for encryption-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.ENCRYPTION,
            **kwargs
        )


class DecryptionKeyException(EncryptionException):
    """Decryption key error"""
    
    def __init__(self, key_url: Optional[str] = None, **kwargs):
        if key_url:
            message = f"Failed to obtain or use decryption key from {key_url}"
        else:
            message = "Decryption key is missing or invalid"
            
        suggested_actions = [
            UserAction("check_key_url", "Verify the encryption key URL", priority=1),
            UserAction("check_auth", "Check authentication for key access", priority=2),
            UserAction("retry", "Retry key download", is_automatic=True, priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            is_retryable=True,
            max_retries=3,
            **kwargs
        )


# Validation-related exceptions
class ValidationException(VidTaniumException):
    """Base class for validation errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class InvalidURLException(ValidationException):
    """Invalid URL format error"""
    
    def __init__(self, url: str, **kwargs):
        message = f"Invalid URL format: {url}"
        suggested_actions = [
            UserAction("check_url", "Verify the URL format is correct", priority=1),
            UserAction("copy_url", "Copy URL from source again", priority=2)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            **kwargs
        )


class InvalidSegmentException(ValidationException):
    """Invalid segment data error"""
    
    def __init__(self, segment_index: int, reason: str, **kwargs):
        message = f"Invalid segment {segment_index}: {reason}"
        suggested_actions = [
            UserAction("retry_segment", "Retry downloading this segment", is_automatic=True, priority=1),
            UserAction("skip_segment", "Skip corrupted segment", priority=2)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            is_retryable=True,
            **kwargs
        )


# Resource-related exceptions
class ResourceException(VidTaniumException):
    """Base class for resource-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RESOURCE,
            **kwargs
        )


class MemoryException(ResourceException):
    """Memory-related error"""
    
    def __init__(self, operation: str, **kwargs):
        message = f"Insufficient memory for operation: {operation}"
        suggested_actions = [
            UserAction("close_apps", "Close other applications", priority=1),
            UserAction("reduce_concurrent", "Reduce concurrent downloads", priority=2),
            UserAction("restart_app", "Restart the application", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


# System-related exceptions
class SystemException(VidTaniumException):
    """Base class for system-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )


class ConfigurationException(SystemException):
    """Configuration error"""
    
    def __init__(self, setting: str, value: Any, **kwargs):
        message = f"Invalid configuration: {setting} = {value}"
        suggested_actions = [
            UserAction("reset_settings", "Reset to default settings", priority=1),
            UserAction("check_config", "Check configuration file", priority=2)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            **kwargs
        )

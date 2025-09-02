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

    # Common action constants
    RETRY: Optional['UserAction'] = None  # Will be set after class definition
    CHECK_NETWORK: Optional['UserAction'] = None
    CHECK_PERMISSIONS: Optional['UserAction'] = None
    CHECK_URL: Optional['UserAction'] = None


# Initialize common action constants
UserAction.RETRY = UserAction("retry", "Retry the operation", is_automatic=True, priority=1)
UserAction.CHECK_NETWORK = UserAction("check_network", "Check network connection", priority=1)
UserAction.CHECK_PERMISSIONS = UserAction("check_permissions", "Check file permissions", priority=2)
UserAction.CHECK_URL = UserAction("check_url", "Verify the URL is correct", priority=1)


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
        self.url = url
        self.timeout_seconds = timeout_seconds
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
        # Remove is_retryable from kwargs to avoid conflict
        kwargs.pop('is_retryable', None)
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
        self.file_path = path
        self.operation = operation
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


# Enhanced Network Exception Types

class NetworkTimeoutException(NetworkException):
    """Network timeout specific exception"""

    def __init__(self, url: str, timeout_duration: float, **kwargs):
        self.url = url
        self.timeout_duration = timeout_duration
        message = f"Network timeout after {timeout_duration}s for URL: {url}"
        suggested_actions = [
            UserAction("retry_request", "Retry the request", priority=1),
            UserAction("check_connection", "Check internet connection", priority=2),
            UserAction("increase_timeout", "Increase timeout duration", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class DNSResolutionException(NetworkException):
    """DNS resolution failure"""

    def __init__(self, hostname: str, **kwargs):
        self.hostname = hostname
        message = f"Failed to resolve hostname: {hostname}"
        suggested_actions = [
            UserAction("check_dns", "Check DNS settings", priority=1),
            UserAction("try_different_dns", "Try different DNS server", priority=2),
            UserAction("check_hostname", "Verify hostname is correct", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class SSLCertificateException(NetworkException):
    """SSL certificate validation error"""

    def __init__(self, hostname: str, cert_error: str, **kwargs):
        self.hostname = hostname
        self.cert_error = cert_error
        message = f"SSL certificate error for {hostname}: {cert_error}"
        suggested_actions = [
            UserAction("check_certificate", "Verify server certificate", priority=1),
            UserAction("update_ca_bundle", "Update certificate authority bundle", priority=2),
            UserAction("bypass_ssl", "Bypass SSL verification (not recommended)", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ProxyException(NetworkException):
    """Proxy connection error"""

    def __init__(self, proxy_url: str, **kwargs):
        self.proxy_url = proxy_url
        message = f"Proxy connection failed: {proxy_url}"
        suggested_actions = [
            UserAction("check_proxy", "Verify proxy settings", priority=1),
            UserAction("test_proxy", "Test proxy connectivity", priority=2),
            UserAction("disable_proxy", "Try without proxy", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class RateLimitException(NetworkException):
    """Rate limiting error"""

    def __init__(self, url: str, retry_after: Optional[int] = None, **kwargs):
        self.url = url
        self.retry_after = retry_after
        message = f"Rate limited for URL: {url}"
        if retry_after:
            message += f" (retry after {retry_after} seconds)"

        suggested_actions = [
            UserAction("wait_retry", f"Wait {retry_after or 60} seconds before retrying", priority=1),
            UserAction("reduce_concurrency", "Reduce concurrent requests", priority=2),
            UserAction("implement_backoff", "Use exponential backoff", priority=3)
        ]
        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.MEDIUM,
            is_retryable=True,
            **kwargs
        )


# Enhanced HTTP Exception Types

class HTTPClientException(HTTPException):
    """HTTP 4xx client error"""

    def __init__(self, status_code: int, url: str, response_text: str = "", **kwargs):
        self.status_code = status_code
        self.url = url
        self.response_text = response_text
        message = f"HTTP {status_code} client error for {url}"

        suggested_actions = []
        if status_code == 401:
            suggested_actions = [
                UserAction("check_auth", "Check authentication credentials", priority=1),
                UserAction("refresh_token", "Refresh authentication token", priority=2)
            ]
        elif status_code == 403:
            suggested_actions = [
                UserAction("check_permissions", "Check access permissions", priority=1),
                UserAction("verify_account", "Verify account status", priority=2)
            ]
        elif status_code == 404:
            suggested_actions = [
                UserAction("check_url", "Verify URL is correct", priority=1),
                UserAction("check_resource", "Check if resource exists", priority=2)
            ]
        else:
            suggested_actions = [
                UserAction("check_request", "Verify request parameters", priority=1),
                UserAction("contact_support", "Contact support if issue persists", priority=2)
            ]

        super().__init__(
            status_code,
            url,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class HTTPServerException(HTTPException):
    """HTTP 5xx server error"""

    def __init__(self, status_code: int, url: str, response_text: str = "", **kwargs):
        self.status_code = status_code
        self.url = url
        self.response_text = response_text
        message = f"HTTP {status_code} server error for {url}"

        suggested_actions = [
            UserAction("retry_request", "Retry the request", priority=1),
            UserAction("wait_retry", "Wait before retrying", priority=2),
            UserAction("contact_admin", "Contact server administrator", priority=3)
        ]

        super().__init__(
            status_code,
            url,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.MEDIUM,
            is_retryable=True,
            **kwargs
        )


# Enhanced Download-Specific Exception Types

class SegmentDownloadException(VidTaniumException):
    """Segment download specific error"""

    def __init__(self, segment_index: int, segment_url: str, reason: str, **kwargs):
        self.segment_index = segment_index
        self.segment_url = segment_url
        self.reason = reason
        message = f"Failed to download segment {segment_index}: {reason}"

        suggested_actions = [
            UserAction("retry_segment", f"Retry downloading segment {segment_index}", priority=1),
            UserAction("check_segment_url", "Verify segment URL is accessible", priority=2),
            UserAction("skip_segment", "Skip this segment and continue", priority=3)
        ]

        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.MEDIUM,
            is_retryable=True,
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
            is_retryable=False,
            **kwargs
        )


class M3U8ParseException(ValidationException):
    """M3U8 playlist parsing error"""

    def __init__(self, playlist_url: str, parse_error: str, **kwargs):
        self.playlist_url = playlist_url
        self.parse_error = parse_error
        message = f"Failed to parse M3U8 playlist from {playlist_url}: {parse_error}"

        suggested_actions = [
            UserAction("verify_playlist", "Verify playlist format is valid", priority=1),
            UserAction("check_encoding", "Check playlist encoding", priority=2),
            UserAction("manual_download", "Try manual download", priority=3)
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


class EncryptionKeyException(EncryptionException):
    """Encryption key specific error"""

    def __init__(self, key_url: str, key_error: str, **kwargs):
        self.key_url = key_url
        self.key_error = key_error
        message = f"Failed to obtain encryption key from {key_url}: {key_error}"

        suggested_actions = [
            UserAction("retry_key", "Retry downloading encryption key", priority=1),
            UserAction("check_key_url", "Verify key URL is accessible", priority=2),
            UserAction("check_auth", "Check authentication for key access", priority=3)
        ]

        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ContentIntegrityException(ValidationException):
    """Content integrity validation error"""

    def __init__(self, file_path: str, expected_hash: str, actual_hash: str, **kwargs):
        self.file_path = file_path
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        message = f"Content integrity check failed for {file_path}: expected {expected_hash}, got {actual_hash}"

        suggested_actions = [
            UserAction("redownload", "Re-download the file", priority=1),
            UserAction("verify_source", "Verify source integrity", priority=2),
            UserAction("check_network", "Check for network corruption", priority=3)
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


# Resource-related exceptions
class ResourceException(VidTaniumException):
    """Base class for resource-related errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RESOURCE,
            **kwargs
        )


class ConcurrencyException(SystemException):
    """Concurrency and threading related error"""

    def __init__(self, operation: str, thread_info: str, **kwargs):
        self.operation = operation
        self.thread_info = thread_info
        message = f"Concurrency error during {operation}: {thread_info}"

        suggested_actions = [
            UserAction("reduce_concurrency", "Reduce concurrent operations", priority=1),
            UserAction("retry_operation", "Retry the operation", priority=2),
            UserAction("check_resources", "Check system resources", priority=3)
        ]

        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class CircuitBreakerException(SystemException):
    """Circuit breaker is open"""

    def __init__(self, host: str, failure_count: int, **kwargs):
        self.host = host
        self.failure_count = failure_count
        message = f"Circuit breaker is OPEN for {host} after {failure_count} failures"

        suggested_actions = [
            UserAction("wait_recovery", "Wait for automatic recovery", priority=1),
            UserAction("check_host", "Check host availability", priority=2),
            UserAction("force_reset", "Force reset circuit breaker", priority=3)
        ]

        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.MEDIUM,
            is_retryable=True,
            **kwargs
        )


class ResourceExhaustionException(ResourceException):
    """System resource exhaustion"""

    def __init__(self, resource_type: str, current_usage: str, limit: str, **kwargs):
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit
        message = f"{resource_type} exhausted: {current_usage} / {limit}"

        suggested_actions = [
            UserAction("free_resources", f"Free up {resource_type.lower()}", priority=1),
            UserAction("reduce_load", "Reduce system load", priority=2),
            UserAction("increase_limits", f"Increase {resource_type.lower()} limits", priority=3)
        ]

        super().__init__(
            message,
            suggested_actions=suggested_actions,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class DecryptionKeyException(EncryptionException):
    """Decryption key error"""
    
    def __init__(self, key_url: Optional[str] = None, **kwargs):
        self.key_url = key_url
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


class MemoryException(ResourceException):
    """Memory-related error"""
    
    def __init__(self, operation: str, **kwargs):
        self.operation = operation
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

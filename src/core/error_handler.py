"""
Enhanced Error Handler for VidTanium
Provides intelligent error handling, retry strategies, and user-friendly error reporting
"""

import time
import random
from typing import Optional, Callable, Any, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from .exceptions import (
    VidTaniumException, ErrorCategory, ErrorSeverity,
    NetworkException, ConnectionTimeoutException, HTTPException,
    FilesystemException, EncryptionException, ValidationException,
    ResourceException, SystemException, ErrorContext, UserAction,
    PermissionException, InsufficientSpaceException, DecryptionKeyException, MemoryException
)


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"
    NO_RETRY = "no_retry"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    backoff_multiplier: float = 2.0


@dataclass
class ErrorReport:
    """Comprehensive error report for UI display"""
    title: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    suggested_actions: List[UserAction]
    technical_details: Dict[str, Any]
    is_retryable: bool
    retry_count: int
    context: Optional[ErrorContext] = None


class EnhancedErrorHandler:
    """Enhanced error handler with intelligent retry strategies"""
    
    def __init__(self):
        self.retry_configs: Dict[ErrorCategory, RetryConfig] = self._get_default_retry_configs()
        self.error_history: List[Tuple[str, VidTaniumException, float]] = []
        self.max_history_size = 1000
        
    def _get_default_retry_configs(self) -> Dict[ErrorCategory, RetryConfig]:
        """Get default retry configurations for different error categories"""
        return {
            ErrorCategory.NETWORK: RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=5,
                base_delay=2.0,
                max_delay=30.0,
                backoff_multiplier=2.0
            ),
            ErrorCategory.FILESYSTEM: RetryConfig(
                strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retries=3,
                base_delay=1.0,
                max_delay=10.0
            ),
            ErrorCategory.AUTHENTICATION: RetryConfig(
                strategy=RetryStrategy.NO_RETRY,
                max_retries=0
            ),
            ErrorCategory.VALIDATION: RetryConfig(
                strategy=RetryStrategy.NO_RETRY,
                max_retries=0
            ),
            ErrorCategory.RESOURCE: RetryConfig(
                strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retries=2,
                base_delay=5.0,
                max_delay=15.0
            ),
            ErrorCategory.ENCRYPTION: RetryConfig(
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retries=3,
                base_delay=1.0,
                max_delay=10.0
            ),
            ErrorCategory.PARSING: RetryConfig(
                strategy=RetryStrategy.FIXED_DELAY,
                max_retries=2,
                base_delay=0.5
            ),
            ErrorCategory.SYSTEM: RetryConfig(
                strategy=RetryStrategy.NO_RETRY,
                max_retries=0
            )
        }
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[ErrorContext] = None,
        operation_name: str = "operation"
    ) -> VidTaniumException:
        """Convert generic exception to VidTaniumException with enhanced information"""
        
        # If already a VidTaniumException, update context if provided
        if isinstance(exception, VidTaniumException):
            if context:
                exception.context = context
            return exception
        
        # Convert common exceptions to VidTaniumException
        enhanced_exception = self._convert_exception(exception, context, operation_name)
        
        # Log the error
        self._log_error(enhanced_exception)
        
        # Add to error history
        self._add_to_history(operation_name, enhanced_exception)
        
        return enhanced_exception
    
    def _convert_exception(
        self,
        exception: Exception,
        context: Optional[ErrorContext],
        operation_name: str
    ) -> VidTaniumException:
        """Convert generic exception to appropriate VidTaniumException"""
        
        exception_type = type(exception).__name__
        exception_message = str(exception)
        
        # Network-related exceptions
        if "timeout" in exception_message.lower() or "timed out" in exception_message.lower():
            return ConnectionTimeoutException(
                url=context.url if context and context.url else "unknown",
                timeout_seconds=30,  # Default timeout
                context=context,
                original_exception=exception
            )
        
        if "http" in exception_message.lower() and any(code in exception_message for code in ["404", "403", "500", "502", "503"]):
            # Extract status code
            status_code = 500  # Default
            for code in [404, 403, 500, 502, 503]:
                if str(code) in exception_message:
                    status_code = code
                    break
            
            return HTTPException(
                status_code=status_code,
                url=context.url if context and context.url else "unknown",
                context=context,
                original_exception=exception
            )
        
        if any(keyword in exception_message.lower() for keyword in ["connection", "network", "dns", "resolve"]):
            return NetworkException(
                message=f"Network error during {operation_name}: {exception_message}",
                context=context,
                original_exception=exception
            )
        
        # Filesystem-related exceptions
        if any(keyword in exception_message.lower() for keyword in ["permission", "access denied", "forbidden"]):
            return PermissionException(
                path=context.file_path if context and context.file_path else "unknown",
                operation=operation_name,
                context=context,
                original_exception=exception
            )
        
        if any(keyword in exception_message.lower() for keyword in ["no space", "disk full", "insufficient space"]):
            return InsufficientSpaceException(
                required_space=0,  # Unknown
                available_space=0,  # Unknown
                path=context.file_path if context and context.file_path else "unknown",
                context=context,
                original_exception=exception
            )
        
        if any(keyword in exception_message.lower() for keyword in ["file not found", "directory not found", "path"]):
            return FilesystemException(
                message=f"File system error during {operation_name}: {exception_message}",
                context=context,
                original_exception=exception
            )
        
        # Encryption-related exceptions
        if any(keyword in exception_message.lower() for keyword in ["decrypt", "key", "cipher", "encryption"]):
            return DecryptionKeyException(
                key_url=context.url if context else None,
                context=context,
                original_exception=exception
            )
        
        # Memory-related exceptions
        if any(keyword in exception_message.lower() for keyword in ["memory", "out of memory", "malloc"]):
            return MemoryException(
                operation=operation_name,
                context=context,
                original_exception=exception
            )
        
        # Default: Generic VidTaniumException
        return VidTaniumException(
            message=f"Unexpected error during {operation_name}: {exception_message}",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            context=context,
            suggested_actions=[
                UserAction("retry", "Retry the operation", is_automatic=True, priority=1),
                UserAction("report", "Report this issue", priority=2)
            ],
            is_retryable=True,
            original_exception=exception
        )
    
    def should_retry(self, exception: VidTaniumException, current_retry: int) -> bool:
        """Determine if operation should be retried"""
        if not exception.is_retryable:
            return False
        
        config = self.retry_configs.get(exception.category)
        if not config or config.strategy == RetryStrategy.NO_RETRY:
            return False
        
        return current_retry < min(exception.max_retries, config.max_retries)
    
    def get_retry_delay(self, exception: VidTaniumException, retry_count: int) -> float:
        """Calculate delay before next retry"""
        config = self.retry_configs.get(exception.category)
        if not config:
            return 1.0
        
        if config.strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (retry_count + 1)
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** retry_count)
        else:
            delay = config.base_delay
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_amount = delay * 0.1 * random.random()
            delay += jitter_amount
        
        return delay
    
    def create_error_report(self, exception: VidTaniumException, retry_count: int = 0) -> ErrorReport:
        """Create comprehensive error report for UI display"""
        return ErrorReport(
            title=self._get_error_title(exception),
            message=exception.get_user_friendly_message(),
            severity=exception.severity,
            category=exception.category,
            suggested_actions=exception.suggested_actions,
            technical_details=exception.get_technical_details(),
            is_retryable=exception.is_retryable,
            retry_count=retry_count,
            context=exception.context
        )
    
    def _get_error_title(self, exception: VidTaniumException) -> str:
        """Generate appropriate error title"""
        category_titles = {
            ErrorCategory.NETWORK: "Network Error",
            ErrorCategory.FILESYSTEM: "File System Error",
            ErrorCategory.AUTHENTICATION: "Authentication Error",
            ErrorCategory.VALIDATION: "Validation Error",
            ErrorCategory.RESOURCE: "Resource Error",
            ErrorCategory.ENCRYPTION: "Encryption Error",
            ErrorCategory.PARSING: "Parsing Error",
            ErrorCategory.SYSTEM: "System Error"
        }
        
        base_title = category_titles.get(exception.category, "Error")
        
        if exception.severity == ErrorSeverity.CRITICAL:
            return f"Critical {base_title}"
        elif exception.severity == ErrorSeverity.HIGH:
            return f"Serious {base_title}"
        else:
            return base_title
    
    def _log_error(self, exception: VidTaniumException):
        """Log error with appropriate level"""
        log_message = f"{exception.category.value.title()} Error: {exception.message}"
        
        if exception.context:
            if exception.context.task_name:
                log_message = f"[{exception.context.task_name}] {log_message}"
            if exception.context.task_id:
                log_message = f"[{exception.context.task_id}] {log_message}"
        
        if exception.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif exception.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif exception.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _add_to_history(self, operation: str, exception: VidTaniumException):
        """Add error to history for analysis"""
        self.error_history.append((operation, exception, time.time()))
        
        # Trim history if too large
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        if not self.error_history:
            return {}
        
        recent_errors = [
            (op, exc, ts) for op, exc, ts in self.error_history
            if time.time() - ts < 3600  # Last hour
        ]
        
        category_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}
        
        for _, exception, _ in recent_errors:
            category = exception.category.value
            severity = exception.severity.value
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors_last_hour": len(recent_errors),
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        }


# Global error handler instance
error_handler = EnhancedErrorHandler()

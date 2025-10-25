"""
Enhanced Error Handler for VidTanium
Provides intelligent error handling, retry strategies, and user-friendly error reporting
"""

import time
import random
import re
from typing import Optional, Callable, Any, Dict, List, Tuple, Pattern
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


@dataclass
class ExceptionPattern:
    """Pattern for matching and converting exceptions"""
    patterns: List[str]
    exception_class: type
    priority: int = 0  # Higher priority patterns are checked first

    def __post_init__(self) -> None:
        # Compile regex patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.patterns]


class ExceptionConverter:
    """Optimized exception converter using lookup tables and compiled regex"""

    def __init__(self) -> None:
        self._initialize_conversion_tables()

    def _initialize_conversion_tables(self) -> None:
        """Initialize optimized conversion lookup tables"""
        # Network-related patterns (highest priority)
        self.network_patterns = [
            ExceptionPattern(
                patterns=[r'\btimeout\b', r'\btimed out\b'],
                exception_class=ConnectionTimeoutException,
                priority=10
            ),
            ExceptionPattern(
                patterns=[r'\bhttp\b.*\b(404|403|500|502|503)\b'],
                exception_class=HTTPException,
                priority=9
            ),
            ExceptionPattern(
                patterns=[r'\bconnection\b', r'\bnetwork\b', r'\bdns\b', r'\bresolve\b'],
                exception_class=NetworkException,
                priority=8
            )
        ]

        # Filesystem patterns
        self.filesystem_patterns = [
            ExceptionPattern(
                patterns=[r'\bpermission\b', r'\baccess denied\b', r'\bforbidden\b'],
                exception_class=PermissionException,
                priority=7
            ),
            ExceptionPattern(
                patterns=[r'\bno space\b', r'\bdisk full\b', r'\binsufficient space\b'],
                exception_class=InsufficientSpaceException,
                priority=7
            ),
            ExceptionPattern(
                patterns=[r'\bfile not found\b', r'\bdirectory not found\b', r'\bpath\b'],
                exception_class=FilesystemException,
                priority=6
            )
        ]

        # Encryption patterns
        self.encryption_patterns = [
            ExceptionPattern(
                patterns=[r'\bdecrypt\b', r'\bkey\b', r'\bcipher\b', r'\bencryption\b'],
                exception_class=DecryptionKeyException,
                priority=6
            )
        ]

        # Memory patterns
        self.memory_patterns = [
            ExceptionPattern(
                patterns=[r'\bmemory\b', r'\bout of memory\b', r'\bmalloc\b'],
                exception_class=MemoryException,
                priority=5
            )
        ]

        # Combine all patterns and sort by priority
        self.all_patterns = (
            self.network_patterns +
            self.filesystem_patterns +
            self.encryption_patterns +
            self.memory_patterns
        )
        self.all_patterns.sort(key=lambda x: x.priority, reverse=True)

        # HTTP status code extraction pattern
        self.http_status_pattern = re.compile(r'\b(404|403|500|502|503)\b')

    def convert_exception(
        self,
        exception: Exception,
        context: Optional[ErrorContext],
        operation_name: str
    ) -> VidTaniumException:
        """Convert exception using optimized lookup tables"""
        exception_message = str(exception).lower()

        # Check each pattern in priority order
        for pattern_group in self.all_patterns:
            for compiled_pattern in pattern_group.compiled_patterns:
                if compiled_pattern.search(exception_message):
                    return self._create_exception(
                        pattern_group.exception_class,
                        exception,
                        context,
                        operation_name,
                        exception_message
                    )

        # Default fallback
        return SystemException(
            message=f"Unhandled error during {operation_name}: {str(exception)}",
            context=context,
            original_exception=exception
        )

    def _create_exception(
        self,
        exception_class: type,
        original_exception: Exception,
        context: Optional[ErrorContext],
        operation_name: str,
        exception_message: str
    ) -> VidTaniumException:
        """Create specific exception instance with appropriate parameters"""

        if exception_class == ConnectionTimeoutException:
            return ConnectionTimeoutException(
                url=context.url if context and context.url else "unknown",
                timeout_seconds=30,
                context=context,
                original_exception=original_exception
            )

        elif exception_class == HTTPException:
            # Extract status code efficiently
            status_match = self.http_status_pattern.search(exception_message)
            status_code = int(status_match.group(1)) if status_match else 500

            return HTTPException(
                status_code=status_code,
                url=context.url if context and context.url else "unknown",
                context=context,
                original_exception=original_exception
            )

        elif exception_class == DecryptionKeyException:
            return DecryptionKeyException(
                key_url=context.url if context else None,
                context=context,
                original_exception=original_exception
            )

        elif exception_class == MemoryException:
            return MemoryException(
                operation=operation_name,
                context=context,
                original_exception=original_exception
            )

        elif exception_class == PermissionException:
            return PermissionException(
                path=context.file_path if context and context.file_path else "unknown",
                operation=operation_name,
                context=context,
                original_exception=original_exception
            )

        elif exception_class == InsufficientSpaceException:
            return InsufficientSpaceException(
                required_space=0,  # Default values since we don't have actual space info
                available_space=0,
                path=context.file_path if context and context.file_path else "unknown",
                context=context,
                original_exception=original_exception
            )

        else:
            # Generic creation for other exception types
            try:
                result = exception_class(
                    message=f"{exception_class.__name__} during {operation_name}: {str(original_exception)}",
                    context=context,
                    original_exception=original_exception
                )
                # Ensure we return a VidTaniumException
                if isinstance(result, VidTaniumException):
                    return result
                else:
                    raise TypeError(f"Exception class {exception_class} did not return VidTaniumException")
            except Exception:
                # Fallback to SystemException if the specific exception class fails
                return SystemException(
                    message=f"{exception_class.__name__} during {operation_name}: {str(original_exception)}",
                    context=context,
                    original_exception=original_exception
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


class ErrorHandler:
    """Error handler with intelligent retry strategies"""

    def __init__(self) -> None:
        self.retry_configs: Dict[ErrorCategory, RetryConfig] = self._get_default_retry_configs()
        self.error_history: List[Tuple[str, VidTaniumException, float]] = []
        self.max_history_size = 100

        # Initialize exception converter
        self.exception_converter = ExceptionConverter()
        
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
        """Convert generic exception to appropriate VidTaniumException using exception converter"""

        # Use the exception converter
        return self.exception_converter.convert_exception(exception, context, operation_name)

    
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
    
    def _log_error(self, exception: VidTaniumException) -> None:
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
    
    def _add_to_history(self, operation: str, exception: VidTaniumException) -> None:
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
error_handler = ErrorHandler()

# Backward compatibility alias
EnhancedErrorHandler = ErrorHandler

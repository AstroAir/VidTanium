"""
Adaptive Retry Strategy for VidTanium

This module provides intelligent retry mechanisms that adapt intervals based on
error types, network conditions, and server response patterns.
"""

import time
import random
import threading
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class RetryReason(Enum):
    """Reasons for retry attempts"""
    NETWORK_TIMEOUT = "network_timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    SERVER_ERROR = "server_error"
    RATE_LIMITED = "rate_limited"
    TEMPORARY_FAILURE = "temporary_failure"
    UNKNOWN_ERROR = "unknown_error"


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    ADAPTIVE_BACKOFF = "adaptive_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    JITTERED_BACKOFF = "jittered_backoff"


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    timestamp: float
    reason: RetryReason
    delay: float
    success: bool = False
    response_time: float = 0.0
    error_message: str = ""


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 300.0
    strategy: RetryStrategy = RetryStrategy.ADAPTIVE_BACKOFF
    jitter_factor: float = 0.1
    backoff_multiplier: float = 2.0
    
    # Network-aware parameters
    network_quality_factor: float = 1.0
    server_load_factor: float = 1.0
    error_type_multipliers: Dict[RetryReason, float] = field(default_factory=lambda: {
        RetryReason.NETWORK_TIMEOUT: 2.0,
        RetryReason.CONNECTION_ERROR: 1.5,
        RetryReason.HTTP_ERROR: 1.0,
        RetryReason.SERVER_ERROR: 3.0,
        RetryReason.RATE_LIMITED: 5.0,
        RetryReason.TEMPORARY_FAILURE: 1.2,
        RetryReason.UNKNOWN_ERROR: 1.0
    })


@dataclass
class HostRetryMetrics:
    """Retry metrics for a specific host"""
    host: str
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    recent_attempts: deque = field(default_factory=lambda: deque(maxlen=50))
    error_patterns: Dict[RetryReason, int] = field(default_factory=lambda: defaultdict(int))
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    last_success_time: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    
    def record_attempt(self, attempt: RetryAttempt):
        """Record a retry attempt"""
        self.total_attempts += 1
        self.recent_attempts.append(attempt)
        
        if attempt.success:
            self.successful_attempts += 1
            self.last_success_time = attempt.timestamp
            self.consecutive_failures = 0
            
            # Update average response time
            if self.avg_response_time == 0:
                self.avg_response_time = attempt.response_time
            else:
                self.avg_response_time = (self.avg_response_time * 0.8 + attempt.response_time * 0.2)
        else:
            self.failed_attempts += 1
            self.consecutive_failures += 1
            self.error_patterns[attempt.reason] += 1
        
        # Update success rate
        self.success_rate = self.successful_attempts / self.total_attempts if self.total_attempts > 0 else 1.0
    
    def get_dominant_error_type(self) -> Optional[RetryReason]:
        """Get the most common error type"""
        if not self.error_patterns:
            return None
        return max(self.error_patterns.items(), key=lambda x: x[1])[0]
    
    def is_healthy(self) -> bool:
        """Check if host is considered healthy"""
        return (self.success_rate >= 0.7 and 
                self.consecutive_failures < 5 and
                time.time() - self.last_success_time < 3600)  # 1 hour


class AdaptiveRetryManager:
    """Intelligent retry manager with network-aware strategies"""
    
    def __init__(self, default_config: Optional[RetryConfig] = None):
        self.default_config = default_config or RetryConfig()
        self.host_configs: Dict[str, RetryConfig] = {}
        self.host_metrics: Dict[str, HostRetryMetrics] = {}
        self.lock = threading.RLock()
        
        # Global network conditions
        self.global_network_quality = 1.0  # 0.0 = poor, 1.0 = excellent
        self.global_server_load = 1.0      # 0.0 = overloaded, 1.0 = normal
        
        # Fibonacci sequence for fibonacci backoff
        self.fibonacci_cache = [1, 1]
        
        logger.info("Adaptive retry manager initialized")
    
    def configure_host(self, host: str, config: RetryConfig):
        """Configure retry settings for a specific host"""
        with self.lock:
            self.host_configs[host] = config
            logger.debug(f"Configured retry settings for host: {host}")
    
    def get_retry_delay(self, host: str, attempt_number: int, reason: RetryReason,
                       last_response_time: float = 0.0) -> float:
        """Calculate adaptive retry delay"""
        with self.lock:
            config = self.host_configs.get(host, self.default_config)
            metrics = self.host_metrics.get(host)
            
            # Base delay calculation
            base_delay = self._calculate_base_delay(config, attempt_number, reason)
            
            # Apply network-aware adjustments
            adjusted_delay = self._apply_network_adjustments(
                base_delay, config, metrics, reason, last_response_time
            )
            
            # Apply jitter to prevent thundering herd
            final_delay = self._apply_jitter(adjusted_delay, config.jitter_factor)
            
            # Ensure within bounds
            final_delay = max(0.1, min(final_delay, config.max_delay))
            
            logger.debug(f"Calculated retry delay for {host}: {final_delay:.2f}s "
                        f"(attempt {attempt_number}, reason: {reason.value})")
            
            return final_delay
    
    def _calculate_base_delay(self, config: RetryConfig, attempt_number: int, 
                             reason: RetryReason) -> float:
        """Calculate base delay using configured strategy"""
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt_number - 1))
        
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt_number
        
        elif config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            fib_value = self._get_fibonacci(attempt_number)
            delay = config.base_delay * fib_value
        
        elif config.strategy == RetryStrategy.ADAPTIVE_BACKOFF:
            # Adaptive strategy considers error type and recent patterns
            base = config.base_delay * (config.backoff_multiplier ** (attempt_number - 1))
            error_multiplier = config.error_type_multipliers.get(reason, 1.0)
            delay = base * error_multiplier
        
        else:  # JITTERED_BACKOFF
            base = config.base_delay * (config.backoff_multiplier ** (attempt_number - 1))
            jitter = random.uniform(0.5, 1.5)
            delay = base * jitter
        
        return delay
    
    def _apply_network_adjustments(self, base_delay: float, config: RetryConfig,
                                  metrics: Optional[HostRetryMetrics], reason: RetryReason,
                                  last_response_time: float) -> float:
        """Apply network-aware adjustments to delay"""
        adjusted_delay = base_delay
        
        # Global network quality adjustment
        if self.global_network_quality < 0.8:
            # Poor network quality - increase delays
            quality_factor = 2.0 - self.global_network_quality
            adjusted_delay *= quality_factor
        
        # Server load adjustment
        if self.global_server_load < 0.8:
            # High server load - increase delays
            load_factor = 2.0 - self.global_server_load
            adjusted_delay *= load_factor
        
        # Host-specific adjustments
        if metrics:
            # Success rate adjustment
            if metrics.success_rate < 0.5:
                # Low success rate - increase delays significantly
                adjusted_delay *= (2.0 - metrics.success_rate)
            
            # Consecutive failures adjustment
            if metrics.consecutive_failures > 3:
                failure_multiplier = 1.0 + (metrics.consecutive_failures - 3) * 0.5
                adjusted_delay *= failure_multiplier
            
            # Response time adjustment
            if metrics.avg_response_time > 0 and last_response_time > metrics.avg_response_time * 2:
                # Much slower than average - increase delay
                adjusted_delay *= 1.5
            
            # Error pattern adjustment
            dominant_error = metrics.get_dominant_error_type()
            if dominant_error == reason and dominant_error in [
                RetryReason.RATE_LIMITED, RetryReason.SERVER_ERROR
            ]:
                # Persistent server-side issues - increase delay more
                adjusted_delay *= 2.0
        
        # Rate limiting specific adjustment
        if reason == RetryReason.RATE_LIMITED:
            # For rate limiting, use exponential backoff with higher base
            adjusted_delay = max(adjusted_delay, 30.0)  # Minimum 30 seconds for rate limits
        
        return adjusted_delay
    
    def _apply_jitter(self, delay: float, jitter_factor: float) -> float:
        """Apply jitter to prevent thundering herd effect"""
        if jitter_factor <= 0:
            return delay
        
        jitter_range = delay * jitter_factor
        jitter = random.uniform(-jitter_range, jitter_range)
        return delay + jitter
    
    def _get_fibonacci(self, n: int) -> int:
        """Get nth Fibonacci number with caching"""
        while len(self.fibonacci_cache) <= n:
            next_fib = self.fibonacci_cache[-1] + self.fibonacci_cache[-2]
            self.fibonacci_cache.append(next_fib)
        
        return self.fibonacci_cache[n] if n < len(self.fibonacci_cache) else self.fibonacci_cache[-1]
    
    def should_retry(self, host: str, attempt_number: int, reason: RetryReason,
                   error_message: str = "") -> bool:
        """Determine if operation should be retried"""
        with self.lock:
            config = self.host_configs.get(host, self.default_config)
            metrics = self.host_metrics.get(host)
            
            # Basic attempt limit check
            if attempt_number >= config.max_attempts:
                return False
            
            # Non-retryable errors
            non_retryable_patterns = [
                "authentication", "authorization", "forbidden", "not found",
                "bad request", "invalid", "malformed"
            ]
            
            error_lower = error_message.lower()
            if any(pattern in error_lower for pattern in non_retryable_patterns):
                logger.debug(f"Non-retryable error detected: {error_message}")
                return False
            
            # Host health check
            if metrics and not metrics.is_healthy():
                # Host is unhealthy, but allow limited retries for recovery
                if attempt_number > 2:
                    logger.warning(f"Host {host} is unhealthy, limiting retries")
                    return False
            
            # Reason-specific logic
            if reason == RetryReason.RATE_LIMITED:
                # Always retry rate limits (with appropriate delays)
                return True
            
            if reason in [RetryReason.NETWORK_TIMEOUT, RetryReason.CONNECTION_ERROR]:
                # Network issues are usually retryable
                return True
            
            if reason == RetryReason.SERVER_ERROR:
                # Server errors are retryable but with limits
                return attempt_number <= 3
            
            # Default: retry for most errors
            return True
    
    def record_attempt(self, host: str, attempt_number: int, reason: RetryReason,
                      success: bool, response_time: float = 0.0, 
                      error_message: str = ""):
        """Record retry attempt for learning"""
        with self.lock:
            if host not in self.host_metrics:
                self.host_metrics[host] = HostRetryMetrics(host)
            
            attempt = RetryAttempt(
                attempt_number=attempt_number,
                timestamp=time.time(),
                reason=reason,
                delay=0.0,  # Will be filled by caller if needed
                success=success,
                response_time=response_time,
                error_message=error_message
            )
            
            self.host_metrics[host].record_attempt(attempt)
            
            # Update global network conditions based on patterns
            self._update_global_conditions()
    
    def _update_global_conditions(self):
        """Update global network quality and server load estimates"""
        if not self.host_metrics:
            return
        
        # Calculate global success rate
        total_attempts = sum(m.total_attempts for m in self.host_metrics.values())
        total_successes = sum(m.successful_attempts for m in self.host_metrics.values())
        
        if total_attempts > 0:
            global_success_rate = total_successes / total_attempts
            self.global_network_quality = global_success_rate
        
        # Estimate server load based on response times and error patterns
        avg_response_times = [m.avg_response_time for m in self.host_metrics.values() 
                             if m.avg_response_time > 0]
        
        if avg_response_times:
            avg_global_response = sum(avg_response_times) / len(avg_response_times)
            # Normalize response time to load factor (higher response time = higher load)
            self.global_server_load = max(0.1, min(1.0, 5.0 / max(avg_global_response, 1.0)))
    
    def get_host_stats(self, host: str) -> Dict[str, Any]:
        """Get retry statistics for a host"""
        with self.lock:
            metrics = self.host_metrics.get(host)
            if not metrics:
                return {"host": host, "no_data": True}
            
            return {
                "host": host,
                "total_attempts": metrics.total_attempts,
                "success_rate": metrics.success_rate,
                "consecutive_failures": metrics.consecutive_failures,
                "avg_response_time": metrics.avg_response_time,
                "is_healthy": metrics.is_healthy(),
                "dominant_error": (dominant_error := metrics.get_dominant_error_type()) and dominant_error.value,
                "error_patterns": dict(metrics.error_patterns),
                "last_success": time.time() - metrics.last_success_time
            }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global retry statistics"""
        with self.lock:
            return {
                "global_network_quality": self.global_network_quality,
                "global_server_load": self.global_server_load,
                "tracked_hosts": len(self.host_metrics),
                "total_hosts_healthy": sum(1 for m in self.host_metrics.values() if m.is_healthy()),
                "fibonacci_cache_size": len(self.fibonacci_cache)
            }
    
    def reset_host_metrics(self, host: str):
        """Reset metrics for a specific host"""
        with self.lock:
            if host in self.host_metrics:
                del self.host_metrics[host]
                logger.info(f"Reset retry metrics for host: {host}")


# Global adaptive retry manager instance
adaptive_retry_manager = AdaptiveRetryManager()

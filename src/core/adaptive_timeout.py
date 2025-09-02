"""
Adaptive Timeout Manager for VidTanium

This module provides intelligent timeout management that adapts to network conditions,
connection latency, and historical performance data to optimize download reliability.
"""

import time
import threading
import statistics
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class NetworkMetrics:
    """Network performance metrics for a host"""
    host: str
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    success_rate: float = 1.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_updated: float = field(default_factory=time.time)
    connection_failures: int = 0
    timeout_failures: int = 0
    
    def add_response_time(self, response_time: float, success: bool):
        """Add a response time measurement"""
        self.response_times.append(response_time)
        self.total_requests += 1
        self.last_updated = time.time()
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            
        self.success_rate = self.successful_requests / self.total_requests if self.total_requests > 0 else 1.0
    
    def get_avg_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return float(statistics.mean(self.response_times))
    
    def get_percentile_response_time(self, percentile: float = 95.0) -> float:
        """Get percentile response time"""
        if not self.response_times:
            return 0.0

        sorted_times = sorted(self.response_times)
        index = int((percentile / 100.0) * len(sorted_times))
        return float(sorted_times[min(index, len(sorted_times) - 1)])
    
    def is_stable(self) -> bool:
        """Check if connection is stable"""
        return (self.success_rate >= 0.8 and 
                self.connection_failures < 3 and 
                len(self.response_times) >= 5)


@dataclass
class TimeoutConfig:
    """Timeout configuration for different scenarios"""
    base_connection_timeout: float = 30.0
    base_read_timeout: float = 60.0
    min_timeout: float = 5.0
    max_timeout: float = 300.0
    timeout_multiplier: float = 1.5
    stability_threshold: float = 0.8
    adaptation_factor: float = 0.2


class AdaptiveTimeoutManager:
    """Manages adaptive timeouts based on network conditions and performance"""
    
    def __init__(self, config: Optional[TimeoutConfig] = None):
        self.config = config or TimeoutConfig()
        self.host_metrics: Dict[str, NetworkMetrics] = {}
        self.lock = threading.RLock()
        
        # Global network condition tracking
        self.global_metrics = NetworkMetrics("global")
        self.network_quality_score = 1.0  # 0.0 = poor, 1.0 = excellent
        
        # Adaptive parameters
        self.learning_rate = 0.1
        self.stability_window = 50  # Number of requests to consider for stability
        
        logger.info("Adaptive timeout manager initialized")
    
    def get_host_from_url(self, url: str) -> str:
        """Extract host from URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def get_timeouts(self, url: str) -> Tuple[float, float]:
        """Get adaptive timeouts for connection and read operations"""
        host = self.get_host_from_url(url)
        
        with self.lock:
            metrics = self.host_metrics.get(host)
            
            if not metrics or len(metrics.response_times) < 3:
                # Use base timeouts for new or insufficient data
                return (self.config.base_connection_timeout, self.config.base_read_timeout)
            
            # Calculate adaptive timeouts based on performance
            avg_response_time = metrics.get_avg_response_time()
            p95_response_time = metrics.get_percentile_response_time(95.0)
            
            # Base timeout calculation on 95th percentile + buffer
            adaptive_read_timeout = p95_response_time * self.config.timeout_multiplier
            
            # Adjust based on success rate
            if metrics.success_rate < self.config.stability_threshold:
                # Increase timeout for unstable connections
                adaptive_read_timeout *= (2.0 - metrics.success_rate)
            
            # Adjust based on global network quality
            adaptive_read_timeout *= (2.0 - self.network_quality_score)
            
            # Apply bounds
            adaptive_read_timeout = max(self.config.min_timeout, 
                                      min(self.config.max_timeout, adaptive_read_timeout))
            
            # Connection timeout is typically shorter
            adaptive_connection_timeout = min(adaptive_read_timeout * 0.5, 
                                            self.config.base_connection_timeout)
            adaptive_connection_timeout = max(self.config.min_timeout, adaptive_connection_timeout)
            
            logger.debug(f"Adaptive timeouts for {host}: conn={adaptive_connection_timeout:.1f}s, "
                        f"read={adaptive_read_timeout:.1f}s (avg_rt={avg_response_time:.2f}s, "
                        f"success_rate={metrics.success_rate:.2f})")
            
            return (adaptive_connection_timeout, adaptive_read_timeout)
    
    def record_request(self, url: str, response_time: float, success: bool, 
                      error_type: Optional[str] = None):
        """Record request performance for adaptive learning"""
        host = self.get_host_from_url(url)
        
        with self.lock:
            # Get or create host metrics
            if host not in self.host_metrics:
                self.host_metrics[host] = NetworkMetrics(host)
            
            metrics = self.host_metrics[host]
            metrics.add_response_time(response_time, success)
            
            # Track specific error types
            if not success and error_type:
                if "timeout" in error_type.lower():
                    metrics.timeout_failures += 1
                elif "connection" in error_type.lower():
                    metrics.connection_failures += 1
            
            # Update global metrics
            self.global_metrics.add_response_time(response_time, success)
            
            # Update network quality score
            self._update_network_quality()
            
            logger.debug(f"Recorded request for {host}: {response_time:.2f}s, "
                        f"success={success}, total_requests={metrics.total_requests}")
    
    def _update_network_quality(self):
        """Update global network quality score"""
        if self.global_metrics.total_requests < 10:
            return
        
        # Base score on success rate and response time stability
        success_component = self.global_metrics.success_rate
        
        # Response time component (lower variance = better quality)
        if len(self.global_metrics.response_times) >= 10:
            response_times = list(self.global_metrics.response_times)
            avg_time = statistics.mean(response_times)
            std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
            
            # Normalize standard deviation (lower is better)
            time_stability = max(0.0, 1.0 - (std_dev / max(avg_time, 1.0)))
        else:
            time_stability = 1.0
        
        # Combine components
        new_quality = (success_component * 0.7 + time_stability * 0.3)
        
        # Apply learning rate for smooth transitions
        self.network_quality_score = (
            self.network_quality_score * (1 - self.learning_rate) + 
            new_quality * self.learning_rate
        )
        
        logger.debug(f"Network quality updated: {self.network_quality_score:.3f} "
                    f"(success={success_component:.3f}, stability={time_stability:.3f})")
    
    def get_host_stats(self, url: str) -> Dict[str, Any]:
        """Get statistics for a specific host"""
        host = self.get_host_from_url(url)
        
        with self.lock:
            metrics = self.host_metrics.get(host)
            if not metrics:
                return {"host": host, "requests": 0}
            
            return {
                "host": host,
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate,
                "avg_response_time": metrics.get_avg_response_time(),
                "p95_response_time": metrics.get_percentile_response_time(95.0),
                "connection_failures": metrics.connection_failures,
                "timeout_failures": metrics.timeout_failures,
                "is_stable": metrics.is_stable(),
                "last_updated": metrics.last_updated
            }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global network statistics"""
        with self.lock:
            return {
                "network_quality_score": self.network_quality_score,
                "total_requests": self.global_metrics.total_requests,
                "global_success_rate": self.global_metrics.success_rate,
                "global_avg_response_time": self.global_metrics.get_avg_response_time(),
                "tracked_hosts": len(self.host_metrics),
                "stable_hosts": sum(1 for m in self.host_metrics.values() if m.is_stable())
            }
    
    def reset_host_metrics(self, url: str):
        """Reset metrics for a specific host"""
        host = self.get_host_from_url(url)
        
        with self.lock:
            if host in self.host_metrics:
                del self.host_metrics[host]
                logger.info(f"Reset metrics for host: {host}")
    
    def cleanup_old_metrics(self, max_age_hours: float = 24.0):
        """Clean up old metrics that haven't been updated recently"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        with self.lock:
            old_hosts = [
                host for host, metrics in self.host_metrics.items()
                if metrics.last_updated < cutoff_time
            ]
            
            for host in old_hosts:
                del self.host_metrics[host]
            
            if old_hosts:
                logger.info(f"Cleaned up metrics for {len(old_hosts)} old hosts")


# Global adaptive timeout manager instance
adaptive_timeout_manager = AdaptiveTimeoutManager()

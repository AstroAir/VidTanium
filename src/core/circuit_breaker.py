"""
Circuit Breaker Implementation for VidTanium

This module provides per-host circuit breakers with health monitoring,
automatic recovery, and failure threshold management for robust download operations.
"""

import time
import threading
from typing import Dict, Optional, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5          # Number of failures to open circuit
    success_threshold: int = 3          # Number of successes to close circuit
    timeout: float = 60.0               # Seconds to wait before trying half-open
    rolling_window_size: int = 20       # Size of rolling window for failure tracking
    min_requests: int = 10              # Minimum requests before considering failure rate
    failure_rate_threshold: float = 0.5 # Failure rate threshold (0.0-1.0)
    health_check_interval: float = 30.0 # Health check interval in seconds
    recovery_timeout: float = 300.0     # Maximum time to stay in half-open state


@dataclass
class RequestResult:
    """Result of a request through circuit breaker"""
    timestamp: float
    success: bool
    response_time: float = 0.0
    error_message: str = ""


class CircuitBreakerMetrics:
    """Metrics tracking for circuit breaker"""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.requests: deque = deque(maxlen=window_size)
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_failure_time = 0.0
        self.last_success_time = 0.0
        self.avg_response_time = 0.0
        
    def record_request(self, result: RequestResult):
        """Record a request result"""
        self.requests.append(result)
        self.total_requests += 1
        
        if result.success:
            self.total_successes += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.last_success_time = result.timestamp
            
            # Update average response time
            if self.avg_response_time == 0:
                self.avg_response_time = result.response_time
            else:
                self.avg_response_time = (self.avg_response_time * 0.8 + result.response_time * 0.2)
        else:
            self.total_failures += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.last_failure_time = result.timestamp
    
    def get_failure_rate(self) -> float:
        """Get current failure rate in rolling window"""
        if not self.requests:
            return 0.0
        
        failures = sum(1 for r in self.requests if not r.success)
        return failures / len(self.requests)
    
    def get_recent_failure_rate(self, seconds: float = 60.0) -> float:
        """Get failure rate for recent time period"""
        cutoff_time = time.time() - seconds
        recent_requests = [r for r in self.requests if r.timestamp >= cutoff_time]
        
        if not recent_requests:
            return 0.0
        
        failures = sum(1 for r in recent_requests if not r.success)
        return failures / len(recent_requests)
    
    def is_healthy(self) -> bool:
        """Check if the service appears healthy"""
        return (self.consecutive_failures < 3 and 
                self.get_failure_rate() < 0.3 and
                time.time() - self.last_success_time < 300)  # 5 minutes


class CircuitBreaker:
    """Circuit breaker implementation for a specific host"""
    
    def __init__(self, host: str, config: Optional[CircuitBreakerConfig] = None):
        self.host = host
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics(self.config.rolling_window_size)
        self.lock = threading.RLock()
        
        # State transition tracking
        self.state_changed_at = time.time()
        self.last_attempt_time = 0.0
        self.half_open_attempts = 0
        
        # Health monitoring
        self.health_check_callback: Optional[Callable[[], bool]] = None
        self.last_health_check = 0.0
        
        logger.debug(f"Circuit breaker created for host: {host}")
    
    def can_execute(self) -> bool:
        """Check if requests can be executed"""
        with self.lock:
            current_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # Check if timeout has passed to try half-open
                if current_time - self.state_changed_at >= self.config.timeout:
                    self._transition_to_half_open()
                    return True
                return False
            
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open state
                return self.half_open_attempts < self.config.success_threshold
    
    def record_success(self, response_time: float = 0.0):
        """Record a successful request"""
        with self.lock:
            result = RequestResult(
                timestamp=time.time(),
                success=True,
                response_time=response_time
            )
            
            self.metrics.record_request(result)
            self.last_attempt_time = result.timestamp
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_attempts += 1
                if self.metrics.consecutive_successes >= self.config.success_threshold:
                    self._transition_to_closed()
            
            elif self.state == CircuitState.OPEN:
                # Shouldn't happen, but handle gracefully
                self._transition_to_half_open()
    
    def record_failure(self, error_message: str = ""):
        """Record a failed request"""
        with self.lock:
            result = RequestResult(
                timestamp=time.time(),
                success=False,
                error_message=error_message
            )
            
            self.metrics.record_request(result)
            self.last_attempt_time = result.timestamp
            
            if self.state == CircuitState.CLOSED:
                if self._should_open_circuit():
                    self._transition_to_open()
            
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._transition_to_open()
    
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened"""
        # Check consecutive failures
        if self.metrics.consecutive_failures >= self.config.failure_threshold:
            return True
        
        # Check failure rate if we have enough requests
        if (len(self.metrics.requests) >= self.config.min_requests and
            self.metrics.get_failure_rate() >= self.config.failure_rate_threshold):
            return True
        
        return False
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.state_changed_at = time.time()
        self.half_open_attempts = 0
        
        logger.warning(f"Circuit breaker OPENED for {self.host} "
                      f"(failures: {self.metrics.consecutive_failures}, "
                      f"failure_rate: {self.metrics.get_failure_rate():.2f})")
        
        self._log_state_transition(old_state, self.state)
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.state_changed_at = time.time()
        self.half_open_attempts = 0
        
        logger.info(f"Circuit breaker HALF-OPEN for {self.host} - testing recovery")
        self._log_state_transition(old_state, self.state)
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.state_changed_at = time.time()
        self.half_open_attempts = 0
        
        logger.info(f"Circuit breaker CLOSED for {self.host} - service recovered")
        self._log_state_transition(old_state, self.state)
    
    def _log_state_transition(self, old_state: CircuitState, new_state: CircuitState):
        """Log state transition with metrics"""
        logger.debug(f"Circuit breaker for {self.host}: {old_state.value} -> {new_state.value} "
                    f"(consecutive_failures: {self.metrics.consecutive_failures}, "
                    f"consecutive_successes: {self.metrics.consecutive_successes}, "
                    f"failure_rate: {self.metrics.get_failure_rate():.2f})")
    
    def force_open(self):
        """Force circuit breaker to open state"""
        with self.lock:
            if self.state != CircuitState.OPEN:
                self._transition_to_open()
                logger.warning(f"Circuit breaker for {self.host} forced OPEN")
    
    def force_close(self):
        """Force circuit breaker to closed state"""
        with self.lock:
            if self.state != CircuitState.CLOSED:
                self._transition_to_closed()
                logger.info(f"Circuit breaker for {self.host} forced CLOSED")
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.metrics = CircuitBreakerMetrics(self.config.rolling_window_size)
            self.state_changed_at = time.time()
            self.half_open_attempts = 0
            logger.info(f"Circuit breaker for {self.host} reset")
    
    def perform_health_check(self) -> bool:
        """Perform health check if callback is available"""
        current_time = time.time()
        
        if (self.health_check_callback and 
            current_time - self.last_health_check >= self.config.health_check_interval):
            
            try:
                is_healthy = self.health_check_callback()
                self.last_health_check = current_time
                
                if is_healthy and self.state == CircuitState.OPEN:
                    logger.info(f"Health check passed for {self.host}, transitioning to half-open")
                    self._transition_to_half_open()
                
                return is_healthy
                
            except Exception as e:
                logger.error(f"Health check failed for {self.host}: {e}")
                return False
        
        return self.metrics.is_healthy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            return {
                "host": self.host,
                "state": self.state.value,
                "state_duration": time.time() - self.state_changed_at,
                "total_requests": self.metrics.total_requests,
                "total_failures": self.metrics.total_failures,
                "total_successes": self.metrics.total_successes,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "failure_rate": self.metrics.get_failure_rate(),
                "recent_failure_rate": self.metrics.get_recent_failure_rate(),
                "avg_response_time": self.metrics.avg_response_time,
                "is_healthy": self.metrics.is_healthy(),
                "last_attempt": self.last_attempt_time,
                "half_open_attempts": self.half_open_attempts
            }


class CircuitBreakerManager:
    """Manager for multiple circuit breakers"""
    
    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        self.default_config = default_config or CircuitBreakerConfig()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.host_configs: Dict[str, CircuitBreakerConfig] = {}
        self.lock = threading.RLock()
        
        # Health monitoring
        self.health_monitor_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        logger.info("Circuit breaker manager initialized")
    
    def get_circuit_breaker(self, host: str) -> CircuitBreaker:
        """Get or create circuit breaker for host"""
        with self.lock:
            if host not in self.circuit_breakers:
                config = self.host_configs.get(host, self.default_config)
                self.circuit_breakers[host] = CircuitBreaker(host, config)
            
            return self.circuit_breakers[host]
    
    def configure_host(self, host: str, config: CircuitBreakerConfig):
        """Configure circuit breaker for specific host"""
        with self.lock:
            self.host_configs[host] = config
            
            # Update existing circuit breaker if it exists
            if host in self.circuit_breakers:
                self.circuit_breakers[host].config = config
            
            logger.debug(f"Configured circuit breaker for host: {host}")
    
    def can_execute(self, host: str) -> bool:
        """Check if requests can be executed for host"""
        circuit_breaker = self.get_circuit_breaker(host)
        return circuit_breaker.can_execute()
    
    def record_success(self, host: str, response_time: float = 0.0):
        """Record successful request for host"""
        circuit_breaker = self.get_circuit_breaker(host)
        circuit_breaker.record_success(response_time)
    
    def record_failure(self, host: str, error_message: str = ""):
        """Record failed request for host"""
        circuit_breaker = self.get_circuit_breaker(host)
        circuit_breaker.record_failure(error_message)
    
    def start_health_monitoring(self):
        """Start health monitoring for all circuit breakers"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self.health_monitor_thread.start()
        logger.info("Circuit breaker health monitoring started")
    
    def stop_health_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.health_monitor_thread:
            self.health_monitor_thread.join(timeout=5.0)
        logger.info("Circuit breaker health monitoring stopped")
    
    def _health_monitor_loop(self):
        """Health monitoring loop"""
        while self.monitoring_active:
            try:
                with self.lock:
                    for circuit_breaker in self.circuit_breakers.values():
                        circuit_breaker.perform_health_check()
                
                time.sleep(30.0)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in circuit breaker health monitoring: {e}")
                time.sleep(30.0)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuit breakers"""
        with self.lock:
            stats = {
                "total_circuit_breakers": len(self.circuit_breakers),
                "circuit_breakers": {}
            }
            
            state_counts = {"closed": 0, "open": 0, "half_open": 0}
            
            for host, circuit_breaker in self.circuit_breakers.items():
                cb_stats = circuit_breaker.get_stats()
                if isinstance(stats["circuit_breakers"], dict):
                    stats["circuit_breakers"][host] = cb_stats
                state = cb_stats.get("state", "unknown")
                if state in state_counts:
                    state_counts[state] += 1
            
            stats["state_summary"] = state_counts
            return stats
    
    def reset_all(self):
        """Reset all circuit breakers"""
        with self.lock:
            for circuit_breaker in self.circuit_breakers.values():
                circuit_breaker.reset()
            logger.info("All circuit breakers reset")


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()

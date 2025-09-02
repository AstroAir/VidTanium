"""
Enhanced HTTP Connection Pool Manager for VidTanium

This module provides sophisticated connection pooling with per-host limits,
connection reuse, health monitoring, and automatic cleanup capabilities.
"""

import time
import threading
import weakref
import logging
from typing import Dict, Optional, Set, Tuple, Any, List
from dataclasses import dataclass, field
from urllib.parse import urlparse
from collections import defaultdict, deque
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager
from urllib3.exceptions import MaxRetryError, TimeoutError as UrllibTimeoutError

from .exceptions import NetworkException, ConnectionTimeoutException, ErrorContext
from .resource_manager import register_for_cleanup, ResourceType

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Statistics for a connection"""
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    requests_count: int = 0
    bytes_transferred: int = 0
    errors_count: int = 0
    avg_response_time: float = 0.0
    is_healthy: bool = True


@dataclass
class HostPoolConfig:
    """Configuration for per-host connection pool"""
    max_connections: int = 10
    max_connections_per_host: int = 5
    connection_timeout: float = 30.0
    read_timeout: float = 60.0
    max_retries: int = 3
    backoff_factor: float = 0.3
    keep_alive_timeout: float = 300.0  # 5 minutes
    health_check_interval: float = 60.0  # 1 minute


@dataclass
class ConnectionInfo:
    """Information about a pooled connection"""
    session: requests.Session
    stats: ConnectionStats
    host: str
    pool_config: HostPoolConfig
    last_health_check: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if connection has expired"""
        return (time.time() - self.stats.last_used) > self.pool_config.keep_alive_timeout
    
    def needs_health_check(self) -> bool:
        """Check if connection needs health check"""
        return (time.time() - self.last_health_check) > self.pool_config.health_check_interval

    def __hash__(self) -> int:
        """Make ConnectionInfo hashable for use in sets"""
        return hash((id(self.session), self.host))

    def __eq__(self, other) -> bool:
        """Check equality based on session and host"""
        if not isinstance(other, ConnectionInfo):
            return False
        return self.session is other.session and self.host == other.host


class EnhancedHTTPAdapter(HTTPAdapter):
    """Enhanced HTTP adapter with better connection management"""
    
    def __init__(self, pool_config: HostPoolConfig, **kwargs):
        self.pool_config = pool_config

        # Configure retry strategy
        retry_strategy = Retry(
            total=pool_config.max_retries,
            backoff_factor=pool_config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        # Remove max_retries from kwargs if it exists to avoid conflict
        kwargs.pop('max_retries', None)
        super().__init__(max_retries=retry_strategy, **kwargs)
    
    def init_poolmanager(self, *args, **kwargs):
        """Initialize pool manager with custom settings"""
        # Override the maxsize parameter
        if len(args) >= 2:
            # Replace the second argument (pool_maxsize) with our config
            args_list = list(args)
            args_list[1] = self.pool_config.max_connections
            args = tuple(args_list)
        else:
            kwargs['maxsize'] = self.pool_config.max_connections

        kwargs['block'] = False
        kwargs['timeout'] = self.pool_config.connection_timeout
        return super().init_poolmanager(*args, **kwargs)


class ConnectionPoolManager:
    """Enhanced connection pool manager with per-host limits and health monitoring"""
    
    def __init__(self, default_config: Optional[HostPoolConfig] = None):
        self.default_config = default_config or HostPoolConfig()
        self.host_configs: Dict[str, HostPoolConfig] = {}
        self.connection_pools: Dict[str, List[ConnectionInfo]] = defaultdict(list)
        self.active_connections: Dict[str, Set[ConnectionInfo]] = defaultdict(set)
        self.connection_stats: Dict[str, ConnectionStats] = defaultdict(ConnectionStats)
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Health monitoring
        self.health_monitor_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # Cleanup tracking
        self.cleanup_interval = 60.0  # 1 minute
        self.last_cleanup = time.time()
        
        # Register for resource management
        register_for_cleanup(
            self,
            ResourceType.NETWORK,
            cleanup_callback=self.cleanup_all_connections,
            metadata={"component": "ConnectionPoolManager"}
        )
        
        logger.info("Enhanced connection pool manager initialized")
    
    def start_monitoring(self):
        """Start health monitoring thread"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self.health_monitor_thread.start()
        logger.info("Connection health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.health_monitor_thread:
            self.health_monitor_thread.join(timeout=5.0)
        logger.info("Connection health monitoring stopped")
    
    def configure_host(self, host: str, config: HostPoolConfig):
        """Configure specific settings for a host"""
        with self.lock:
            self.host_configs[host] = config
            logger.debug(f"Configured connection pool for host: {host}")
    
    def get_session(self, url: str, context: Optional[ErrorContext] = None) -> requests.Session:
        """Get a session for the specified URL with connection pooling"""
        parsed_url = urlparse(url)
        host = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        with self.lock:
            # Get or create connection
            connection_info = self._get_or_create_connection(host, context)
            
            # Update usage statistics
            connection_info.stats.last_used = time.time()
            connection_info.stats.requests_count += 1
            
            # Add to active connections
            self.active_connections[host].add(connection_info)
            
            return connection_info.session
    
    def release_session(self, session: requests.Session, url: str, 
                       success: bool = True, bytes_transferred: int = 0,
                       response_time: float = 0.0):
        """Release a session back to the pool"""
        parsed_url = urlparse(url)
        host = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        with self.lock:
            # Find the connection info
            connection_info = None
            for conn in self.active_connections[host]:
                if conn.session is session:
                    connection_info = conn
                    break
            
            if connection_info:
                # Update statistics
                connection_info.stats.bytes_transferred += bytes_transferred
                if not success:
                    connection_info.stats.errors_count += 1
                    connection_info.stats.is_healthy = False
                
                # Update average response time
                if response_time > 0:
                    current_avg = connection_info.stats.avg_response_time
                    count = connection_info.stats.requests_count
                    connection_info.stats.avg_response_time = (
                        (current_avg * (count - 1) + response_time) / count
                    )
                
                # Remove from active connections
                self.active_connections[host].discard(connection_info)
                
                # Return to pool if healthy and not expired
                if connection_info.stats.is_healthy and not connection_info.is_expired():
                    self.connection_pools[host].append(connection_info)
                else:
                    self._close_connection(connection_info)
    
    def _get_or_create_connection(self, host: str, context: Optional[ErrorContext]) -> ConnectionInfo:
        """Get existing connection or create new one"""
        # Try to get from pool first
        pool = self.connection_pools[host]
        while pool:
            connection_info = pool.pop(0)
            if not connection_info.is_expired() and connection_info.stats.is_healthy:
                return connection_info
            else:
                self._close_connection(connection_info)
        
        # Check connection limits
        config = self.host_configs.get(host, self.default_config)
        active_count = len(self.active_connections[host])
        total_count = active_count + len(pool)
        
        if total_count >= config.max_connections_per_host:
            # Wait for a connection to become available or reuse oldest
            if pool:
                return pool.pop(0)
            elif self.active_connections[host]:
                # Force reuse of an active connection (not ideal but prevents deadlock)
                logger.warning(f"Connection limit reached for {host}, reusing active connection")
                return next(iter(self.active_connections[host]))
        
        # Create new connection
        return self._create_new_connection(host, config, context)
    
    def _create_new_connection(self, host: str, config: HostPoolConfig, 
                             context: Optional[ErrorContext]) -> ConnectionInfo:
        """Create a new connection for the host"""
        try:
            session = requests.Session()
            
            # Configure session with enhanced adapter
            adapter = EnhancedHTTPAdapter(config)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            # Set timeouts (sessions don't have timeout attribute, it's passed to requests)
            # Store timeout in connection info for later use
            
            # Create connection info
            connection_info = ConnectionInfo(
                session=session,
                stats=ConnectionStats(),
                host=host,
                pool_config=config
            )
            
            logger.debug(f"Created new connection for host: {host}")
            return connection_info
            
        except Exception as e:
            error_msg = f"Failed to create connection for {host}: {str(e)}"
            logger.error(error_msg)
            raise NetworkException(
                message=error_msg,
                context=context or ErrorContext(),
                original_exception=e
            )
    
    def _close_connection(self, connection_info: ConnectionInfo):
        """Close and cleanup a connection"""
        try:
            connection_info.session.close()
            logger.debug(f"Closed connection for host: {connection_info.host}")
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
    
    def _health_monitor_loop(self):
        """Health monitoring loop"""
        while self.monitoring_active:
            try:
                self._perform_health_checks()
                self._cleanup_expired_connections()
                time.sleep(30.0)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(30.0)
    
    def _perform_health_checks(self):
        """Perform health checks on connections"""
        with self.lock:
            for host, pool in self.connection_pools.items():
                for connection_info in pool[:]:  # Copy to avoid modification during iteration
                    if connection_info.needs_health_check():
                        if self._check_connection_health(connection_info):
                            connection_info.last_health_check = time.time()
                        else:
                            pool.remove(connection_info)
                            self._close_connection(connection_info)
    
    def _check_connection_health(self, connection_info: ConnectionInfo) -> bool:
        """Check if a connection is healthy"""
        try:
            # Simple health check - could be enhanced with actual HTTP request
            return connection_info.stats.is_healthy and not connection_info.is_expired()
        except Exception:
            return False
    
    def _cleanup_expired_connections(self):
        """Clean up expired connections"""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return
        
        with self.lock:
            for host, pool in self.connection_pools.items():
                expired = [conn for conn in pool if conn.is_expired()]
                for conn in expired:
                    pool.remove(conn)
                    self._close_connection(conn)
                
                if expired:
                    logger.debug(f"Cleaned up {len(expired)} expired connections for {host}")
        
        self.last_cleanup = time.time()
    
    def cleanup_all_connections(self):
        """Clean up all connections"""
        with self.lock:
            # Close all pooled connections
            for host, pool in self.connection_pools.items():
                for connection_info in pool:
                    self._close_connection(connection_info)
                pool.clear()
            
            # Close all active connections
            for host, active_set in self.active_connections.items():
                for connection_info in active_set:
                    self._close_connection(connection_info)
                active_set.clear()
        
        logger.info("All connections cleaned up")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self.lock:
            stats = {
                "total_hosts": len(self.connection_pools),
                "hosts": {}
            }
            
            for host in self.connection_pools:
                pool_size = len(self.connection_pools[host])
                active_size = len(self.active_connections[host])

                if isinstance(stats["hosts"], dict):
                    stats["hosts"][host] = {
                        "pooled_connections": pool_size,
                        "active_connections": active_size,
                        "total_connections": pool_size + active_size
                    }
            
            return stats


# Global connection pool manager instance
connection_pool_manager = ConnectionPoolManager()

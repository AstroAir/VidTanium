"""
Bandwidth Monitor and Analytics for VidTanium
Provides real-time bandwidth monitoring, usage analytics, and optimization suggestions
"""

import time
import threading
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import statistics
import psutil

from loguru import logger


class BandwidthUsageType(Enum):
    """Types of bandwidth usage"""
    DOWNLOAD = "download"
    UPLOAD = "upload"
    SYSTEM = "system"
    OTHER = "other"


class OptimizationSuggestion(Enum):
    """Bandwidth optimization suggestions"""
    REDUCE_CONCURRENT_TASKS = "reduce_concurrent_tasks"
    INCREASE_CONCURRENT_TASKS = "increase_concurrent_tasks"
    ADJUST_CHUNK_SIZE = "adjust_chunk_size"
    ENABLE_BANDWIDTH_LIMITING = "enable_bandwidth_limiting"
    DISABLE_BANDWIDTH_LIMITING = "disable_bandwidth_limiting"
    PAUSE_OTHER_APPLICATIONS = "pause_other_applications"
    OPTIMIZE_NETWORK_SETTINGS = "optimize_network_settings"


@dataclass
class BandwidthSample:
    """Single bandwidth measurement sample"""
    timestamp: float
    download_speed: float  # bytes per second
    upload_speed: float    # bytes per second
    total_downloaded: int  # cumulative bytes
    total_uploaded: int    # cumulative bytes
    active_connections: int = 0
    task_id: Optional[str] = None


@dataclass
class BandwidthStats:
    """Comprehensive bandwidth statistics"""
    current_download_speed: float
    current_upload_speed: float
    average_download_speed: float
    average_upload_speed: float
    peak_download_speed: float
    peak_upload_speed: float
    total_downloaded: int
    total_uploaded: int
    efficiency_ratio: float  # actual vs theoretical max
    utilization_percentage: float
    active_tasks: int
    sample_count: int
    monitoring_duration: float


@dataclass
class OptimizationRecommendation:
    """Bandwidth optimization recommendation"""
    suggestion: OptimizationSuggestion
    priority: int  # 1 = highest priority
    description: str
    expected_improvement: float  # percentage improvement expected
    implementation_difficulty: str  # "easy", "medium", "hard"
    metadata: Dict = field(default_factory=dict)


class BandwidthMonitor:
    """Real-time bandwidth monitor with analytics and optimization"""
    
    def __init__(self, sample_interval: float = 1.0, max_samples: int = 3600) -> None:
        self.sample_interval = sample_interval
        self.max_samples = max_samples
        
        # Data storage
        self.samples: deque = deque(maxlen=max_samples)
        self.task_bandwidth: Dict[str, deque] = {}
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        
        # Network interface tracking
        self.network_interface = self._detect_primary_interface()
        self.baseline_stats = self._get_network_stats()
        
        # Callbacks
        self.bandwidth_callbacks: List[Callable[[BandwidthSample], None]] = []
        self.optimization_callbacks: List[Callable[[List[OptimizationRecommendation]], None]] = []
        
        # Configuration
        self.theoretical_max_speed = self._estimate_max_bandwidth()
        self.optimization_check_interval = 30.0  # seconds
        self.last_optimization_check = 0.0
        
        # Analytics
        self.usage_patterns: Dict[str, List[float]] = {
            "hourly": [0.0] * 24,
            "daily": [0.0] * 7,
            "peak_hours": []
        }
    
    def start_monitoring(self) -> None:
        """Start bandwidth monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Bandwidth monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop bandwidth monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Bandwidth monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring:
            try:
                sample = self._collect_sample()
                if sample:
                    with self.lock:
                        self.samples.append(sample)
                        self._update_task_bandwidth(sample)
                        self._trigger_callbacks(sample)
                    
                    # Check for optimization opportunities
                    if (time.time() - self.last_optimization_check > 
                        self.optimization_check_interval):
                        self._check_optimization_opportunities()
                        self.last_optimization_check = time.time()
                
                time.sleep(self.sample_interval)
                
            except Exception as e:
                logger.error(f"Error in bandwidth monitoring loop: {e}")
                time.sleep(self.sample_interval)
    
    def _collect_sample(self) -> Optional[BandwidthSample]:
        """Collect a bandwidth sample"""
        try:
            current_stats = self._get_network_stats()
            if not current_stats or not self.baseline_stats:
                return None
            
            # Calculate speeds
            time_diff = time.time() - getattr(self, '_last_sample_time', time.time() - 1)
            
            download_bytes = current_stats['bytes_recv'] - self.baseline_stats['bytes_recv']
            upload_bytes = current_stats['bytes_sent'] - self.baseline_stats['bytes_sent']
            
            download_speed = download_bytes / time_diff if time_diff > 0 else 0
            upload_speed = upload_bytes / time_diff if time_diff > 0 else 0
            
            sample = BandwidthSample(
                timestamp=time.time(),
                download_speed=max(0, download_speed),
                upload_speed=max(0, upload_speed),
                total_downloaded=download_bytes,
                total_uploaded=upload_bytes,
                active_connections=self._count_active_connections()
            )
            
            self._last_sample_time = time.time()
            self.baseline_stats = current_stats
            
            return sample
            
        except Exception as e:
            logger.error(f"Error collecting bandwidth sample: {e}")
            return None
    
    def _get_network_stats(self) -> Optional[Dict]:
        """Get network interface statistics"""
        try:
            if self.network_interface:
                stats = psutil.net_io_counters(pernic=True).get(self.network_interface)
                if stats:
                    return {
                        'bytes_sent': stats.bytes_sent,
                        'bytes_recv': stats.bytes_recv,
                        'packets_sent': stats.packets_sent,
                        'packets_recv': stats.packets_recv
                    }
            
            # Fallback to total stats
            stats = psutil.net_io_counters()
            return {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv
            }
            
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
            return None
    
    def _detect_primary_interface(self) -> Optional[str]:
        """Detect primary network interface"""
        try:
            # Get interface with highest traffic
            interfaces = psutil.net_io_counters(pernic=True)
            if not interfaces:
                return None
            
            # Find interface with most bytes received (likely primary)
            primary = max(interfaces.items(), key=lambda x: x[1].bytes_recv)
            return primary[0]
            
        except Exception as e:
            logger.error(f"Error detecting primary interface: {e}")
            return None
    
    def _estimate_max_bandwidth(self) -> float:
        """Estimate theoretical maximum bandwidth"""
        try:
            # Try to get from system or use reasonable default
            # This is a simplified estimation
            return 100 * 1024 * 1024  # 100 Mbps default
        except Exception:
            return 100 * 1024 * 1024
    
    def _count_active_connections(self) -> int:
        """Count active network connections"""
        try:
            connections = psutil.net_connections()
            return len([c for c in connections if c.status == 'ESTABLISHED'])
        except Exception:
            return 0
    
    def _update_task_bandwidth(self, sample: BandwidthSample) -> None:
        """Update per-task bandwidth tracking"""
        if sample.task_id:
            if sample.task_id not in self.task_bandwidth:
                self.task_bandwidth[sample.task_id] = deque(maxlen=300)  # 5 minutes at 1s intervals
            
            self.task_bandwidth[sample.task_id].append(sample)
    
    def get_current_stats(self) -> Optional[BandwidthStats]:
        """Get current bandwidth statistics"""
        with self.lock:
            if not self.samples:
                return None
            
            recent_samples = list(self.samples)[-60:]  # Last minute
            all_samples = list(self.samples)
            
            if not recent_samples:
                return None
            
            # Current speeds (average of last few samples)
            current_download = statistics.mean(s.download_speed for s in recent_samples[-5:])
            current_upload = statistics.mean(s.upload_speed for s in recent_samples[-5:])
            
            # Average speeds
            avg_download = statistics.mean(s.download_speed for s in all_samples)
            avg_upload = statistics.mean(s.upload_speed for s in all_samples)
            
            # Peak speeds
            peak_download = max(s.download_speed for s in all_samples)
            peak_upload = max(s.upload_speed for s in all_samples)
            
            # Totals
            total_downloaded = sum(s.total_downloaded for s in all_samples)
            total_uploaded = sum(s.total_uploaded for s in all_samples)
            
            # Efficiency and utilization
            efficiency = (avg_download / self.theoretical_max_speed) if self.theoretical_max_speed > 0 else 0
            utilization = (current_download / self.theoretical_max_speed * 100) if self.theoretical_max_speed > 0 else 0
            
            # Active tasks
            active_tasks = len([tid for tid, samples in self.task_bandwidth.items() 
                              if samples and time.time() - samples[-1].timestamp < 30])
            
            return BandwidthStats(
                current_download_speed=current_download,
                current_upload_speed=current_upload,
                average_download_speed=avg_download,
                average_upload_speed=avg_upload,
                peak_download_speed=peak_download,
                peak_upload_speed=peak_upload,
                total_downloaded=total_downloaded,
                total_uploaded=total_uploaded,
                efficiency_ratio=efficiency,
                utilization_percentage=utilization,
                active_tasks=active_tasks,
                sample_count=len(all_samples),
                monitoring_duration=all_samples[-1].timestamp - all_samples[0].timestamp if len(all_samples) > 1 else 0
            )
    
    def get_task_stats(self, task_id: str) -> Optional[Dict]:
        """Get bandwidth statistics for specific task"""
        with self.lock:
            if task_id not in self.task_bandwidth or not self.task_bandwidth[task_id]:
                return None
            
            samples = list(self.task_bandwidth[task_id])
            
            return {
                "current_speed": samples[-1].download_speed if samples else 0,
                "average_speed": statistics.mean(s.download_speed for s in samples),
                "peak_speed": max(s.download_speed for s in samples),
                "total_downloaded": sum(s.total_downloaded for s in samples),
                "duration": samples[-1].timestamp - samples[0].timestamp if len(samples) > 1 else 0,
                "sample_count": len(samples)
            }
    
    def _check_optimization_opportunities(self) -> None:
        """Check for bandwidth optimization opportunities"""
        stats = self.get_current_stats()
        if not stats:
            return
        
        recommendations = []
        
        # Low utilization - could increase concurrent tasks
        if stats.utilization_percentage < 30 and stats.active_tasks < 5:
            recommendations.append(OptimizationRecommendation(
                suggestion=OptimizationSuggestion.INCREASE_CONCURRENT_TASKS,
                priority=2,
                description="Low bandwidth utilization detected. Consider increasing concurrent downloads.",
                expected_improvement=25.0,
                implementation_difficulty="easy",
                metadata={"current_utilization": stats.utilization_percentage}
            ))
        
        # High utilization - might need to reduce load
        elif stats.utilization_percentage > 90:
            recommendations.append(OptimizationRecommendation(
                suggestion=OptimizationSuggestion.REDUCE_CONCURRENT_TASKS,
                priority=1,
                description="High bandwidth utilization. Consider reducing concurrent downloads.",
                expected_improvement=15.0,
                implementation_difficulty="easy",
                metadata={"current_utilization": stats.utilization_percentage}
            ))
        
        # Low efficiency - network optimization needed
        if stats.efficiency_ratio < 0.5:
            recommendations.append(OptimizationRecommendation(
                suggestion=OptimizationSuggestion.OPTIMIZE_NETWORK_SETTINGS,
                priority=2,
                description="Low network efficiency detected. Check network settings and connection quality.",
                expected_improvement=30.0,
                implementation_difficulty="medium",
                metadata={"efficiency_ratio": stats.efficiency_ratio}
            ))
        
        # Bandwidth limiting suggestions
        if stats.utilization_percentage > 80 and stats.active_tasks > 3:
            recommendations.append(OptimizationRecommendation(
                suggestion=OptimizationSuggestion.ENABLE_BANDWIDTH_LIMITING,
                priority=3,
                description="Consider enabling bandwidth limiting to prevent network congestion.",
                expected_improvement=10.0,
                implementation_difficulty="easy"
            ))
        
        if recommendations:
            self._trigger_optimization_callbacks(recommendations)
    
    def register_bandwidth_callback(self, callback: Callable[[BandwidthSample], None]) -> None:
        """Register callback for bandwidth updates"""
        self.bandwidth_callbacks.append(callback)
    
    def register_optimization_callback(self, callback: Callable[[List[OptimizationRecommendation]], None]) -> None:
        """Register callback for optimization recommendations"""
        self.optimization_callbacks.append(callback)
    
    def _trigger_callbacks(self, sample: BandwidthSample) -> None:
        """Trigger bandwidth update callbacks"""
        for callback in self.bandwidth_callbacks:
            try:
                callback(sample)
            except Exception as e:
                logger.error(f"Error in bandwidth callback: {e}")
    
    def _trigger_optimization_callbacks(self, recommendations: List[OptimizationRecommendation]) -> None:
        """Trigger optimization recommendation callbacks"""
        for callback in self.optimization_callbacks:
            try:
                callback(recommendations)
            except Exception as e:
                logger.error(f"Error in optimization callback: {e}")
    
    def get_usage_patterns(self) -> Dict[str, List[float]]:
        """Get bandwidth usage patterns"""
        return self.usage_patterns.copy()
    
    def export_data(self, duration_hours: int = 24) -> List[Dict]:
        """Export bandwidth data for analysis"""
        with self.lock:
            cutoff_time = time.time() - (duration_hours * 3600)
            recent_samples = [s for s in self.samples if s.timestamp >= cutoff_time]
            
            return [
                {
                    "timestamp": s.timestamp,
                    "download_speed": s.download_speed,
                    "upload_speed": s.upload_speed,
                    "total_downloaded": s.total_downloaded,
                    "total_uploaded": s.total_uploaded,
                    "active_connections": s.active_connections,
                    "task_id": s.task_id
                }
                for s in recent_samples
            ]
    
    def reset_statistics(self) -> None:
        """Reset all bandwidth statistics"""
        with self.lock:
            self.samples.clear()
            self.task_bandwidth.clear()
            self.baseline_stats = self._get_network_stats()
            logger.info("Bandwidth statistics reset")


# Global bandwidth monitor instance
bandwidth_monitor = BandwidthMonitor()

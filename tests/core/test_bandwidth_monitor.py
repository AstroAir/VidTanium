import pytest
import time
import threading
from unittest.mock import patch, Mock, MagicMock
from collections import deque
from typing import Dict, Any, List

from src.core.bandwidth_monitor import (
    BandwidthMonitor, BandwidthSample, BandwidthStats,
    OptimizationRecommendation, OptimizationSuggestion,
    bandwidth_monitor
)


class TestBandwidthSample:
    """Test suite for BandwidthSample dataclass."""

    def test_bandwidth_sample_creation(self):
        """Test BandwidthSample creation with all fields."""
        sample = BandwidthSample(
            timestamp=1234567890.0,
            download_speed=1024.0,
            upload_speed=512.0,
            total_downloaded=1048576,
            total_uploaded=524288,
            active_connections=5,
            task_id="test_task"
        )
        
        assert sample.timestamp == 1234567890.0
        assert sample.download_speed == 1024.0
        assert sample.upload_speed == 512.0
        assert sample.total_downloaded == 1048576
        assert sample.total_uploaded == 524288
        assert sample.active_connections == 5
        assert sample.task_id == "test_task"

    def test_bandwidth_sample_defaults(self):
        """Test BandwidthSample with default values."""
        sample = BandwidthSample(
            timestamp=1234567890.0,
            download_speed=1024.0,
            upload_speed=512.0,
            total_downloaded=1048576,
            total_uploaded=524288
        )
        
        assert sample.active_connections == 0
        assert sample.task_id is None


class TestBandwidthStats:
    """Test suite for BandwidthStats dataclass."""

    def test_bandwidth_stats_creation(self):
        """Test BandwidthStats creation with all fields."""
        stats = BandwidthStats(
            current_download_speed=1024.0,
            current_upload_speed=512.0,
            average_download_speed=800.0,
            average_upload_speed=400.0,
            peak_download_speed=2048.0,
            peak_upload_speed=1024.0,
            total_downloaded=1048576,
            total_uploaded=524288,
            efficiency_ratio=0.8,
            utilization_percentage=75.0,
            active_tasks=3,
            sample_count=100,
            monitoring_duration=300.0
        )
        
        assert stats.current_download_speed == 1024.0
        assert stats.efficiency_ratio == 0.8
        assert stats.active_tasks == 3


class TestBandwidthMonitor:
    """Test suite for BandwidthMonitor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = BandwidthMonitor(sample_interval=0.1, max_samples=100)

    def teardown_method(self):
        """Clean up after tests."""
        if self.monitor.monitoring:
            self.monitor.stop_monitoring()

    def test_initialization(self):
        """Test BandwidthMonitor initialization."""
        assert self.monitor.sample_interval == 0.1
        assert self.monitor.max_samples == 100
        assert not self.monitor.monitoring
        assert self.monitor.monitor_thread is None
        assert isinstance(self.monitor.samples, deque)
        assert isinstance(self.monitor.task_bandwidth, dict)

    @patch('src.core.bandwidth_monitor.psutil.net_io_counters')
    def test_detect_primary_interface(self, mock_net_io):
        """Test primary network interface detection."""
        # Mock network interfaces
        mock_interface1 = Mock()
        mock_interface1.bytes_recv = 1000000
        mock_interface2 = Mock()
        mock_interface2.bytes_recv = 5000000
        
        mock_net_io.return_value = {
            'eth0': mock_interface1,
            'wlan0': mock_interface2
        }
        
        interface = self.monitor._detect_primary_interface()
        assert interface == 'wlan0'  # Should pick the one with more bytes_recv

    @patch('src.core.bandwidth_monitor.psutil.net_io_counters')
    def test_detect_primary_interface_error(self, mock_net_io):
        """Test primary interface detection with error."""
        mock_net_io.side_effect = Exception("Network error")
        
        interface = self.monitor._detect_primary_interface()
        assert interface is None

    @patch('src.core.bandwidth_monitor.psutil.net_io_counters')
    def test_get_network_stats(self, mock_net_io):
        """Test network statistics collection."""
        # Mock specific interface stats
        mock_stats = Mock()
        mock_stats.bytes_sent = 1000
        mock_stats.bytes_recv = 2000
        mock_stats.packets_sent = 10
        mock_stats.packets_recv = 20
        
        mock_net_io.return_value = {'eth0': mock_stats}
        self.monitor.network_interface = 'eth0'
        
        stats = self.monitor._get_network_stats()
        
        assert stats['bytes_sent'] == 1000
        assert stats['bytes_recv'] == 2000
        assert stats['packets_sent'] == 10
        assert stats['packets_recv'] == 20

    @patch('src.core.bandwidth_monitor.psutil.net_io_counters')
    def test_get_network_stats_fallback(self, mock_net_io):
        """Test network stats fallback to total stats."""
        # Mock total stats when per-interface fails
        mock_total_stats = Mock()
        mock_total_stats.bytes_sent = 5000
        mock_total_stats.bytes_recv = 10000
        mock_total_stats.packets_sent = 50
        mock_total_stats.packets_recv = 100
        
        # First call returns empty dict (no per-interface), second returns total
        mock_net_io.side_effect = [{}, mock_total_stats]
        self.monitor.network_interface = 'nonexistent'
        
        stats = self.monitor._get_network_stats()
        
        assert stats['bytes_sent'] == 5000
        assert stats['bytes_recv'] == 10000

    @patch('src.core.bandwidth_monitor.psutil.net_connections')
    def test_count_active_connections(self, mock_connections):
        """Test active connection counting."""
        # Mock connections
        conn1 = Mock()
        conn1.status = 'ESTABLISHED'
        conn2 = Mock()
        conn2.status = 'LISTEN'
        conn3 = Mock()
        conn3.status = 'ESTABLISHED'
        
        mock_connections.return_value = [conn1, conn2, conn3]
        
        count = self.monitor._count_active_connections()
        assert count == 2  # Only ESTABLISHED connections

    @patch('src.core.bandwidth_monitor.psutil.net_connections')
    def test_count_active_connections_error(self, mock_connections):
        """Test connection counting with error."""
        mock_connections.side_effect = Exception("Connection error")
        
        count = self.monitor._count_active_connections()
        assert count == 0

    def test_estimate_max_bandwidth(self):
        """Test bandwidth estimation."""
        max_bandwidth = self.monitor._estimate_max_bandwidth()
        assert max_bandwidth == 100 * 1024 * 1024  # 100 Mbps default

    @patch.object(BandwidthMonitor, '_get_network_stats')
    def test_collect_sample(self, mock_get_stats):
        """Test bandwidth sample collection."""
        # Setup baseline
        self.monitor.baseline_stats = {
            'bytes_recv': 1000,
            'bytes_sent': 500,
            'packets_recv': 10,
            'packets_sent': 5
        }
        
        # Mock current stats
        mock_get_stats.return_value = {
            'bytes_recv': 2000,
            'bytes_sent': 1000,
            'packets_recv': 20,
            'packets_sent': 10
        }
        
        # Set last sample time
        self.monitor._last_sample_time = time.time() - 1.0
        
        sample = self.monitor._collect_sample()
        
        assert sample is not None
        assert sample.download_speed >= 0
        assert sample.upload_speed >= 0
        assert sample.total_downloaded == 1000
        assert sample.total_uploaded == 500

    @patch.object(BandwidthMonitor, '_get_network_stats')
    def test_collect_sample_no_baseline(self, mock_get_stats):
        """Test sample collection without baseline."""
        self.monitor.baseline_stats = None
        mock_get_stats.return_value = {'bytes_recv': 1000, 'bytes_sent': 500}
        
        sample = self.monitor._collect_sample()
        assert sample is None

    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        assert not self.monitor.monitoring
        
        self.monitor.start_monitoring()
        assert self.monitor.monitoring
        assert self.monitor.monitor_thread is not None
        
        self.monitor.stop_monitoring()
        assert not self.monitor.monitoring

    def test_start_monitoring_already_running(self):
        """Test starting monitoring when already running."""
        self.monitor.monitoring = True
        original_thread = Mock()
        self.monitor.monitor_thread = original_thread
        
        self.monitor.start_monitoring()
        
        # Should not create new thread
        assert self.monitor.monitor_thread == original_thread

    def test_update_task_bandwidth(self):
        """Test per-task bandwidth tracking."""
        sample = BandwidthSample(
            timestamp=time.time(),
            download_speed=1024.0,
            upload_speed=512.0,
            total_downloaded=1000,
            total_uploaded=500,
            task_id="test_task"
        )
        
        self.monitor._update_task_bandwidth(sample)
        
        assert "test_task" in self.monitor.task_bandwidth
        assert len(self.monitor.task_bandwidth["test_task"]) == 1
        assert self.monitor.task_bandwidth["test_task"][0] == sample

    def test_update_task_bandwidth_no_task_id(self):
        """Test bandwidth update without task ID."""
        sample = BandwidthSample(
            timestamp=time.time(),
            download_speed=1024.0,
            upload_speed=512.0,
            total_downloaded=1000,
            total_uploaded=500
        )
        
        initial_count = len(self.monitor.task_bandwidth)
        self.monitor._update_task_bandwidth(sample)
        
        # Should not add any new task entries
        assert len(self.monitor.task_bandwidth) == initial_count

    def test_get_current_stats_no_samples(self):
        """Test getting stats with no samples."""
        stats = self.monitor.get_current_stats()
        assert stats is None

    def test_get_current_stats_with_samples(self):
        """Test getting current statistics with samples."""
        # Add test samples
        samples = [
            BandwidthSample(time.time() - 10, 1000, 500, 1000, 500),
            BandwidthSample(time.time() - 5, 1500, 750, 1500, 750),
            BandwidthSample(time.time(), 2000, 1000, 2000, 1000)
        ]
        
        for sample in samples:
            self.monitor.samples.append(sample)
        
        stats = self.monitor.get_current_stats()
        
        assert stats is not None
        assert stats.sample_count == 3
        assert stats.peak_download_speed == 2000
        assert stats.peak_upload_speed == 1000

    def test_get_task_stats(self):
        """Test getting task-specific statistics."""
        task_id = "test_task"
        samples = [
            BandwidthSample(time.time() - 10, 1000, 500, 1000, 500, task_id=task_id),
            BandwidthSample(time.time() - 5, 1500, 750, 1500, 750, task_id=task_id),
            BandwidthSample(time.time(), 2000, 1000, 2000, 1000, task_id=task_id)
        ]
        
        self.monitor.task_bandwidth[task_id] = deque(samples)
        
        stats = self.monitor.get_task_stats(task_id)
        
        assert stats is not None
        assert stats["current_speed"] == 2000
        assert stats["peak_speed"] == 2000
        assert stats["sample_count"] == 3

    def test_get_task_stats_nonexistent(self):
        """Test getting stats for nonexistent task."""
        stats = self.monitor.get_task_stats("nonexistent_task")
        assert stats is None

    def test_register_callbacks(self):
        """Test callback registration."""
        bandwidth_callback = Mock()
        optimization_callback = Mock()
        
        self.monitor.register_bandwidth_callback(bandwidth_callback)
        self.monitor.register_optimization_callback(optimization_callback)
        
        assert bandwidth_callback in self.monitor.bandwidth_callbacks
        assert optimization_callback in self.monitor.optimization_callbacks

    def test_trigger_callbacks(self):
        """Test callback triggering."""
        callback = Mock()
        self.monitor.register_bandwidth_callback(callback)
        
        sample = BandwidthSample(time.time(), 1000, 500, 1000, 500)
        self.monitor._trigger_callbacks(sample)
        
        callback.assert_called_once_with(sample)

    def test_trigger_callbacks_with_error(self):
        """Test callback triggering with error handling."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()
        
        self.monitor.register_bandwidth_callback(error_callback)
        self.monitor.register_bandwidth_callback(good_callback)
        
        sample = BandwidthSample(time.time(), 1000, 500, 1000, 500)
        self.monitor._trigger_callbacks(sample)
        
        # Both callbacks should be called despite error in first
        error_callback.assert_called_once_with(sample)
        good_callback.assert_called_once_with(sample)

    def test_export_data(self):
        """Test data export functionality."""
        current_time = time.time()
        samples = [
            BandwidthSample(current_time - 3601, 1000, 500, 1000, 500),  # 1 hour + 1 sec ago
            BandwidthSample(current_time - 1800, 1500, 750, 1500, 750),  # 30 min ago
            BandwidthSample(current_time, 2000, 1000, 2000, 1000)        # now
        ]
        
        for sample in samples:
            self.monitor.samples.append(sample)
        
        exported = self.monitor.export_data(duration_hours=1)
        
        assert len(exported) == 2  # Should exclude sample from 1 hour ago
        assert exported[0]["download_speed"] == 1500
        assert exported[1]["download_speed"] == 2000

    def test_reset_statistics(self):
        """Test statistics reset."""
        # Add some data
        sample = BandwidthSample(time.time(), 1000, 500, 1000, 500, task_id="test")
        self.monitor.samples.append(sample)
        self.monitor.task_bandwidth["test"] = deque([sample])
        
        self.monitor.reset_statistics()
        
        assert len(self.monitor.samples) == 0
        assert len(self.monitor.task_bandwidth) == 0

    def test_global_bandwidth_monitor_instance(self):
        """Test global bandwidth monitor instance."""
        assert bandwidth_monitor is not None
        assert isinstance(bandwidth_monitor, BandwidthMonitor)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

import pytest
import time
import statistics
import math
from unittest.mock import patch, Mock
from collections import deque
from typing import List, Dict, Any

from src.core.eta_calculator import (
    ETACalculator, ETAAlgorithm, ETAResult, SpeedSample
)


class TestETAAlgorithm:
    """Test suite for ETAAlgorithm enum."""

    def test_algorithm_values(self) -> None:
        """Test enum values."""
        assert ETAAlgorithm.SIMPLE_LINEAR.value == "simple_linear"
        assert ETAAlgorithm.EXPONENTIAL_SMOOTHING.value == "exponential_smoothing"
        assert ETAAlgorithm.WEIGHTED_AVERAGE.value == "weighted_average"
        assert ETAAlgorithm.ADAPTIVE_HYBRID.value == "adaptive_hybrid"
        assert ETAAlgorithm.REGRESSION_BASED.value == "regression_based"


class TestSpeedSample:
    """Test suite for SpeedSample dataclass."""

    def test_speed_sample_creation(self) -> None:
        """Test SpeedSample creation with all fields."""
        sample = SpeedSample(
            timestamp=1234567890.0,
            speed=1024.0,
            bytes_downloaded=1048576,
            segment_index=5
        )
        
        assert sample.timestamp == 1234567890.0
        assert sample.speed == 1024.0
        assert sample.bytes_downloaded == 1048576
        assert sample.segment_index == 5

    def test_speed_sample_defaults(self) -> None:
        """Test SpeedSample with default values."""
        sample = SpeedSample(
            timestamp=1234567890.0,
            speed=1024.0,
            bytes_downloaded=1048576
        )
        
        assert sample.segment_index is None


class TestETAResult:
    """Test suite for ETAResult dataclass."""

    def test_eta_result_creation(self) -> None:
        """Test ETAResult creation with all fields."""
        result = ETAResult(
            eta_seconds=120.0,
            confidence=0.85,
            algorithm_used=ETAAlgorithm.EXPONENTIAL_SMOOTHING,
            speed_trend="increasing",
            metadata={"avg_speed": 1024.0}
        )
        
        assert result.eta_seconds == 120.0
        assert result.confidence == 0.85
        assert result.algorithm_used == ETAAlgorithm.EXPONENTIAL_SMOOTHING
        assert result.speed_trend == "increasing"
        assert result.metadata["avg_speed"] == 1024.0

    def test_eta_result_defaults(self) -> None:
        """Test ETAResult with default values."""
        result = ETAResult(
            eta_seconds=120.0,
            confidence=0.85,
            algorithm_used=ETAAlgorithm.SIMPLE_LINEAR,
            speed_trend="stable"
        )
        
        assert result.metadata == {}


class TestETACalculator:
    """Test suite for ETACalculator class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.calculator = ETACalculator(max_samples=50)

    def test_initialization(self) -> None:
        """Test ETACalculator initialization."""
        assert self.calculator.max_samples == 50
        assert isinstance(self.calculator.speed_samples, deque)
        assert self.calculator.speed_samples.maxlen == 50
        assert isinstance(self.calculator.historical_data, dict)
        assert "speeds" in self.calculator.historical_data
        assert "completion_times" in self.calculator.historical_data
        assert "file_sizes" in self.calculator.historical_data

    def test_add_speed_sample(self) -> None:
        """Test adding speed samples."""
        self.calculator.add_speed_sample(1024.0, 1048576, 1)
        
        assert len(self.calculator.speed_samples) == 1
        sample = self.calculator.speed_samples[0]
        assert sample.speed == 1024.0
        assert sample.bytes_downloaded == 1048576
        assert sample.segment_index == 1
        assert sample.timestamp > 0

    def test_add_speed_sample_without_segment(self) -> None:
        """Test adding speed sample without segment index."""
        self.calculator.add_speed_sample(1024.0, 1048576)
        
        assert len(self.calculator.speed_samples) == 1
        sample = self.calculator.speed_samples[0]
        assert sample.segment_index is None

    def test_add_speed_sample_cleanup_old(self) -> None:
        """Test cleanup of old samples."""
        current_time = time.time()
        
        # Add old sample (older than 5 minutes)
        old_sample = SpeedSample(
            timestamp=current_time - 400,  # 6 minutes ago
            speed=512.0,
            bytes_downloaded=524288
        )
        self.calculator.speed_samples.append(old_sample)
        
        # Add new sample
        self.calculator.add_speed_sample(1024.0, 1048576)
        
        # Old sample should be removed
        assert len(self.calculator.speed_samples) == 1
        assert self.calculator.speed_samples[0].speed == 1024.0

    def test_calculate_eta_no_samples(self) -> None:
        """Test ETA calculation with no samples."""
        result = self.calculator.calculate_eta(1048576, 524288)
        assert result is None

    def test_calculate_eta_already_complete(self) -> None:
        """Test ETA calculation when download is already complete."""
        self.calculator.add_speed_sample(1024.0, 1048576)
        result = self.calculator.calculate_eta(1048576, 1048576)
        assert result is None

    def test_calculate_simple_linear(self) -> None:
        """Test simple linear ETA calculation."""
        # Add some speed samples
        for i in range(5):
            self.calculator.add_speed_sample(1024.0, (i + 1) * 1024)
        
        result = self.calculator.calculate_eta(
            total_bytes=10240,
            bytes_downloaded=5120,
            algorithm=ETAAlgorithm.SIMPLE_LINEAR
        )
        
        assert result is not None
        assert result.algorithm_used == ETAAlgorithm.SIMPLE_LINEAR
        assert result.eta_seconds == 5.0  # 5120 remaining / 1024 speed
        assert result.confidence > 0
        assert "avg_speed" in result.metadata

    def test_calculate_simple_linear_no_samples(self) -> None:
        """Test simple linear with no samples."""
        result = self.calculator._calculate_simple_linear(1024)
        
        assert result.eta_seconds == float('inf')
        assert result.confidence == 0.0
        assert result.speed_trend == "unknown"

    def test_calculate_simple_linear_zero_speed(self) -> None:
        """Test simple linear with zero speed."""
        self.calculator.add_speed_sample(0.0, 1024)
        result = self.calculator._calculate_simple_linear(1024)
        
        assert result.eta_seconds == float('inf')
        assert result.confidence == 0.0

    def test_calculate_exponential_smoothing(self) -> None:
        """Test exponential smoothing ETA calculation."""
        # Add samples with varying speeds
        speeds = [500.0, 750.0, 1000.0, 1250.0, 1500.0]
        for i, speed in enumerate(speeds):
            self.calculator.add_speed_sample(speed, (i + 1) * 1024)
        
        result = self.calculator.calculate_eta(
            total_bytes=10240,
            bytes_downloaded=5120,
            algorithm=ETAAlgorithm.EXPONENTIAL_SMOOTHING
        )
        
        assert result is not None
        assert result.algorithm_used == ETAAlgorithm.EXPONENTIAL_SMOOTHING
        assert result.eta_seconds > 0
        assert "smoothed_speed" in result.metadata

    def test_calculate_exponential_smoothing_insufficient_samples(self) -> None:
        """Test exponential smoothing with insufficient samples."""
        self.calculator.add_speed_sample(1024.0, 1024)
        
        # Should fallback to simple linear
        result = self.calculator._calculate_exponential_smoothing(1024)
        assert result.algorithm_used == ETAAlgorithm.SIMPLE_LINEAR

    def test_calculate_weighted_average(self) -> None:
        """Test weighted average ETA calculation."""
        current_time = time.time()
        
        # Add samples with different timestamps
        for i in range(5):
            sample = SpeedSample(
                timestamp=current_time - (4 - i) * 30,  # 30 seconds apart
                speed=1000.0 + i * 100,  # Increasing speed
                bytes_downloaded=(i + 1) * 1024
            )
            self.calculator.speed_samples.append(sample)
        
        result = self.calculator._calculate_weighted_average(1024)
        
        assert result.algorithm_used == ETAAlgorithm.WEIGHTED_AVERAGE
        assert result.eta_seconds > 0
        assert "weighted_avg_speed" in result.metadata

    def test_calculate_weighted_average_no_samples(self) -> None:
        """Test weighted average with no samples."""
        result = self.calculator._calculate_weighted_average(1024)
        
        assert result.eta_seconds == float('inf')
        assert result.confidence == 0.0

    def test_calculate_regression_based(self) -> None:
        """Test regression-based ETA calculation."""
        current_time = time.time()
        
        # Add samples with linear progression
        for i in range(10):
            sample = SpeedSample(
                timestamp=current_time + i * 10,  # 10 seconds apart
                speed=1000.0,
                bytes_downloaded=i * 1024  # Linear progression
            )
            self.calculator.speed_samples.append(sample)
        
        result = self.calculator._calculate_regression_based(1024, 9 * 1024)
        
        assert result.algorithm_used == ETAAlgorithm.REGRESSION_BASED
        assert result.eta_seconds > 0
        assert "slope" in result.metadata
        assert "r_squared" in result.metadata

    def test_calculate_regression_based_insufficient_samples(self) -> None:
        """Test regression with insufficient samples."""
        self.calculator.add_speed_sample(1024.0, 1024)
        
        # Should fallback to weighted average
        result = self.calculator._calculate_regression_based(1024, 1024)
        assert result.algorithm_used == ETAAlgorithm.WEIGHTED_AVERAGE

    def test_calculate_adaptive_hybrid(self) -> None:
        """Test adaptive hybrid ETA calculation."""
        # Add sufficient samples for all algorithms
        for i in range(10):
            self.calculator.add_speed_sample(1000.0 + i * 10, (i + 1) * 1024)
        
        result = self.calculator.calculate_eta(
            total_bytes=20480,
            bytes_downloaded=10240,
            algorithm=ETAAlgorithm.ADAPTIVE_HYBRID
        )
        
        assert result is not None
        assert result.algorithm_used == ETAAlgorithm.ADAPTIVE_HYBRID
        assert result.eta_seconds > 0
        assert result.confidence > 0

    def test_detect_speed_trend_increasing(self) -> None:
        """Test speed trend detection - increasing."""
        samples = [
            SpeedSample(time.time(), 500.0, 1024),
            SpeedSample(time.time(), 750.0, 2048),
            SpeedSample(time.time(), 1000.0, 3072),
            SpeedSample(time.time(), 1250.0, 4096),
            SpeedSample(time.time(), 1500.0, 5120)
        ]
        
        trend = self.calculator._detect_speed_trend(samples)
        assert trend == "increasing"

    def test_detect_speed_trend_decreasing(self) -> None:
        """Test speed trend detection - decreasing."""
        samples = [
            SpeedSample(time.time(), 1500.0, 1024),
            SpeedSample(time.time(), 1250.0, 2048),
            SpeedSample(time.time(), 1000.0, 3072),
            SpeedSample(time.time(), 750.0, 4096),
            SpeedSample(time.time(), 500.0, 5120)
        ]
        
        trend = self.calculator._detect_speed_trend(samples)
        assert trend == "decreasing"

    def test_detect_speed_trend_stable(self) -> None:
        """Test speed trend detection - stable."""
        samples = [
            SpeedSample(time.time(), 1000.0, 1024),
            SpeedSample(time.time(), 1010.0, 2048),
            SpeedSample(time.time(), 990.0, 3072),
            SpeedSample(time.time(), 1005.0, 4096),
            SpeedSample(time.time(), 995.0, 5120)
        ]
        
        trend = self.calculator._detect_speed_trend(samples)
        assert trend == "stable"

    def test_detect_speed_trend_insufficient_samples(self) -> None:
        """Test speed trend detection with insufficient samples."""
        samples = [SpeedSample(time.time(), 1000.0, 1024)]
        
        trend = self.calculator._detect_speed_trend(samples)
        assert trend == "unknown"

    def test_assess_data_quality(self) -> None:
        """Test data quality assessment."""
        # Add consistent samples
        for i in range(20):
            self.calculator.add_speed_sample(1000.0, (i + 1) * 1024)
        
        quality = self.calculator._assess_data_quality()
        
        assert 0.0 <= quality <= 1.0
        assert quality > 0.5  # Should be high quality due to consistency

    def test_assess_data_quality_no_samples(self) -> None:
        """Test data quality with no samples."""
        quality = self.calculator._assess_data_quality()
        assert quality == 0.0

    def test_get_speed_statistics(self) -> None:
        """Test speed statistics calculation."""
        speeds = [500.0, 750.0, 1000.0, 1250.0, 1500.0]
        for i, speed in enumerate(speeds):
            self.calculator.add_speed_sample(speed, (i + 1) * 1024)
        
        stats = self.calculator.get_speed_statistics()
        
        assert "current_speed" in stats
        assert "average_speed" in stats
        assert "median_speed" in stats
        assert "min_speed" in stats
        assert "max_speed" in stats
        assert "speed_variance" in stats
        assert "sample_count" in stats
        assert "data_quality" in stats
        
        assert stats["current_speed"] == 1500.0
        assert stats["average_speed"] == 1000.0
        assert stats["min_speed"] == 500.0
        assert stats["max_speed"] == 1500.0
        assert stats["sample_count"] == 5

    def test_get_speed_statistics_no_samples(self) -> None:
        """Test speed statistics with no samples."""
        stats = self.calculator.get_speed_statistics()
        assert stats == {}

    def test_reset(self) -> None:
        """Test calculator reset."""
        # Add some samples
        for i in range(5):
            self.calculator.add_speed_sample(1000.0, (i + 1) * 1024)
        
        assert len(self.calculator.speed_samples) > 0
        
        self.calculator.reset()
        
        assert len(self.calculator.speed_samples) == 0

    def test_add_historical_completion(self) -> None:
        """Test adding historical completion data."""
        self.calculator.add_historical_completion(1048576, 120.0, 8738.13)
        
        assert len(self.calculator.historical_data["file_sizes"]) == 1
        assert len(self.calculator.historical_data["completion_times"]) == 1
        assert len(self.calculator.historical_data["speeds"]) == 1
        
        assert self.calculator.historical_data["file_sizes"][0] == 1048576
        assert self.calculator.historical_data["completion_times"][0] == 120.0
        assert self.calculator.historical_data["speeds"][0] == 8738.13

    def test_historical_data_limit(self) -> None:
        """Test historical data size limit."""
        # Add more than 100 entries
        for i in range(105):
            self.calculator.add_historical_completion(1024 * i, 60.0 + i, 1000.0 + i)
        
        # Should keep only last 100
        for key in self.calculator.historical_data:
            assert len(self.calculator.historical_data[key]) == 100

    def test_maxlen_enforcement(self) -> None:
        """Test that deque maxlen is enforced."""
        # Add more samples than max_samples
        for i in range(60):  # More than max_samples (50)
            self.calculator.add_speed_sample(1000.0, (i + 1) * 1024)
        
        # Should only keep the most recent 50
        assert len(self.calculator.speed_samples) == 50

    def test_algorithm_parameter_adjustment(self) -> None:
        """Test algorithm parameter adjustment."""
        original_smoothing = self.calculator.smoothing_factor
        original_threshold = self.calculator.confidence_threshold
        
        self.calculator.smoothing_factor = 0.5
        self.calculator.confidence_threshold = 0.8
        
        assert self.calculator.smoothing_factor == 0.5
        assert self.calculator.confidence_threshold == 0.8
        
        # Restore original values
        self.calculator.smoothing_factor = original_smoothing
        self.calculator.confidence_threshold = original_threshold


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

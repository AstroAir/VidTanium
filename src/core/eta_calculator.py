"""
Enhanced ETA Calculator for VidTanium
Provides sophisticated estimated time of arrival calculations using multiple algorithms
"""

import time
import statistics
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import math

from loguru import logger


class ETAAlgorithm(Enum):
    """Different ETA calculation algorithms"""
    SIMPLE_LINEAR = "simple_linear"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    WEIGHTED_AVERAGE = "weighted_average"
    ADAPTIVE_HYBRID = "adaptive_hybrid"
    REGRESSION_BASED = "regression_based"


@dataclass
class SpeedSample:
    """Speed measurement sample"""
    timestamp: float
    speed: float  # bytes per second
    bytes_downloaded: int
    segment_index: Optional[int] = None


@dataclass
class ETAResult:
    """ETA calculation result"""
    eta_seconds: float
    confidence: float  # 0.0 to 1.0
    algorithm_used: ETAAlgorithm
    speed_trend: str  # "increasing", "decreasing", "stable"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ETACalculator:
    """Advanced ETA calculator with multiple algorithms"""
    
    def __init__(self, max_samples: int = 100) -> None:
        self.max_samples = max_samples
        self.speed_samples: deque = deque(maxlen=max_samples)
        self.historical_data: Dict[str, List[float]] = {
            "speeds": [],
            "completion_times": [],
            "file_sizes": []
        }
        
        # Algorithm parameters
        self.smoothing_factor = 0.3  # For exponential smoothing
        self.confidence_threshold = 0.7
        self.min_samples_for_confidence = 5
        
        # Trend detection parameters
        self.trend_window = 10
        self.trend_threshold = 0.1  # 10% change to consider significant
    
    def add_speed_sample(
        self,
        speed: float,
        bytes_downloaded: int,
        segment_index: Optional[int] = None
    ) -> None:
        """Add a new speed sample"""
        sample = SpeedSample(
            timestamp=time.time(),
            speed=speed,
            bytes_downloaded=bytes_downloaded,
            segment_index=segment_index
        )
        
        self.speed_samples.append(sample)
        
        # Clean old samples (older than 5 minutes)
        current_time = time.time()
        while (self.speed_samples and 
               current_time - self.speed_samples[0].timestamp > 300):
            self.speed_samples.popleft()
    
    def calculate_eta(
        self,
        total_bytes: int,
        bytes_downloaded: int,
        algorithm: ETAAlgorithm = ETAAlgorithm.ADAPTIVE_HYBRID
    ) -> Optional[ETAResult]:
        """Calculate ETA using specified algorithm"""
        
        if not self.speed_samples or bytes_downloaded >= total_bytes:
            return None
        
        remaining_bytes = total_bytes - bytes_downloaded
        
        if algorithm == ETAAlgorithm.SIMPLE_LINEAR:
            return self._calculate_simple_linear(remaining_bytes)
        elif algorithm == ETAAlgorithm.EXPONENTIAL_SMOOTHING:
            return self._calculate_exponential_smoothing(remaining_bytes)
        elif algorithm == ETAAlgorithm.WEIGHTED_AVERAGE:
            return self._calculate_weighted_average(remaining_bytes)
        elif algorithm == ETAAlgorithm.REGRESSION_BASED:
            return self._calculate_regression_based(remaining_bytes, bytes_downloaded)
        elif algorithm == ETAAlgorithm.ADAPTIVE_HYBRID:
            return self._calculate_adaptive_hybrid(remaining_bytes, bytes_downloaded)
    
    def _calculate_simple_linear(self, remaining_bytes: int) -> ETAResult:
        """Simple linear ETA based on recent average speed"""
        recent_samples = list(self.speed_samples)[-10:]  # Last 10 samples
        if not recent_samples:
            return ETAResult(
                eta_seconds=float('inf'),
                confidence=0.0,
                algorithm_used=ETAAlgorithm.SIMPLE_LINEAR,
                speed_trend="unknown"
            )
        
        avg_speed = statistics.mean(sample.speed for sample in recent_samples)
        if avg_speed <= 0:
            return ETAResult(
                eta_seconds=float('inf'),
                confidence=0.0,
                algorithm_used=ETAAlgorithm.SIMPLE_LINEAR,
                speed_trend="unknown"
            )
        
        eta_seconds = remaining_bytes / avg_speed
        confidence = min(len(recent_samples) / 10.0, 1.0)
        speed_trend = self._detect_speed_trend(recent_samples)
        
        return ETAResult(
            eta_seconds=eta_seconds,
            confidence=confidence,
            algorithm_used=ETAAlgorithm.SIMPLE_LINEAR,
            speed_trend=speed_trend,
            metadata={"avg_speed": avg_speed, "samples_used": len(recent_samples)}
        )
    
    def _calculate_exponential_smoothing(self, remaining_bytes: int) -> ETAResult:
        """ETA using exponential smoothing for speed prediction"""
        if len(self.speed_samples) < 2:
            return self._calculate_simple_linear(remaining_bytes)
        
        # Initialize with first sample
        smoothed_speed = self.speed_samples[0].speed
        
        # Apply exponential smoothing
        for sample in list(self.speed_samples)[1:]:
            smoothed_speed = (self.smoothing_factor * sample.speed + 
                            (1 - self.smoothing_factor) * smoothed_speed)
        
        if smoothed_speed <= 0:
            return ETAResult(
                eta_seconds=float('inf'),
                confidence=0.0,
                algorithm_used=ETAAlgorithm.EXPONENTIAL_SMOOTHING,
                speed_trend="unknown"
            )
        
        eta_seconds = remaining_bytes / smoothed_speed
        confidence = min(len(self.speed_samples) / self.min_samples_for_confidence, 1.0)
        speed_trend = self._detect_speed_trend(list(self.speed_samples)[-self.trend_window:])
        
        return ETAResult(
            eta_seconds=eta_seconds,
            confidence=confidence,
            algorithm_used=ETAAlgorithm.EXPONENTIAL_SMOOTHING,
            speed_trend=speed_trend,
            metadata={"smoothed_speed": smoothed_speed}
        )
    
    def _calculate_weighted_average(self, remaining_bytes: int) -> ETAResult:
        """ETA using time-weighted average (recent samples have more weight)"""
        if not self.speed_samples:
            return ETAResult(
                eta_seconds=float('inf'),
                confidence=0.0,
                algorithm_used=ETAAlgorithm.WEIGHTED_AVERAGE,
                speed_trend="unknown"
            )
        
        current_time = time.time()
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for sample in self.speed_samples:
            # Weight decreases exponentially with age
            age = current_time - sample.timestamp
            weight = math.exp(-age / 60.0)  # Half-life of 1 minute
            
            weighted_sum += sample.speed * weight
            weight_sum += weight
        
        if weight_sum == 0:
            return ETAResult(
                eta_seconds=float('inf'),
                confidence=0.0,
                algorithm_used=ETAAlgorithm.WEIGHTED_AVERAGE,
                speed_trend="unknown"
            )
        
        weighted_avg_speed = weighted_sum / weight_sum
        
        if weighted_avg_speed <= 0:
            return ETAResult(
                eta_seconds=float('inf'),
                confidence=0.0,
                algorithm_used=ETAAlgorithm.WEIGHTED_AVERAGE,
                speed_trend="unknown"
            )
        
        eta_seconds = remaining_bytes / weighted_avg_speed
        confidence = min(len(self.speed_samples) / self.min_samples_for_confidence, 1.0)
        speed_trend = self._detect_speed_trend(list(self.speed_samples)[-self.trend_window:])
        
        return ETAResult(
            eta_seconds=eta_seconds,
            confidence=confidence,
            algorithm_used=ETAAlgorithm.WEIGHTED_AVERAGE,
            speed_trend=speed_trend,
            metadata={"weighted_avg_speed": weighted_avg_speed}
        )
    
    def _calculate_regression_based(self, remaining_bytes: int, bytes_downloaded: int) -> ETAResult:
        """ETA using linear regression on download progress"""
        if len(self.speed_samples) < 3:
            return self._calculate_weighted_average(remaining_bytes)
        
        # Prepare data for regression
        samples = list(self.speed_samples)
        start_time = samples[0].timestamp
        
        x_values = []  # Time elapsed
        y_values = []  # Bytes downloaded
        
        for sample in samples:
            x_values.append(sample.timestamp - start_time)
            y_values.append(sample.bytes_downloaded)
        
        # Simple linear regression
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        # Calculate slope (download rate)
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return self._calculate_weighted_average(remaining_bytes)
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        if slope <= 0:
            return ETAResult(
                eta_seconds=float('inf'),
                confidence=0.0,
                algorithm_used=ETAAlgorithm.REGRESSION_BASED,
                speed_trend="decreasing"
            )
        
        eta_seconds = remaining_bytes / slope
        
        # Calculate R-squared for confidence
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        intercept = (sum_y - slope * sum_x) / n
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence = max(0, min(r_squared, 1.0))
        
        speed_trend = self._detect_speed_trend(samples)
        
        return ETAResult(
            eta_seconds=eta_seconds,
            confidence=confidence,
            algorithm_used=ETAAlgorithm.REGRESSION_BASED,
            speed_trend=speed_trend,
            metadata={"slope": slope, "r_squared": r_squared}
        )
    
    def _calculate_adaptive_hybrid(self, remaining_bytes: int, bytes_downloaded: int) -> ETAResult:
        """Adaptive hybrid algorithm that chooses best method based on conditions"""
        
        # Try multiple algorithms
        algorithms_to_try = [
            ETAAlgorithm.REGRESSION_BASED,
            ETAAlgorithm.EXPONENTIAL_SMOOTHING,
            ETAAlgorithm.WEIGHTED_AVERAGE,
            ETAAlgorithm.SIMPLE_LINEAR
        ]
        
        results = []
        for algorithm in algorithms_to_try:
            try:
                result = self.calculate_eta(remaining_bytes + bytes_downloaded, bytes_downloaded, algorithm)
                if result and result.confidence > 0:
                    results.append(result)
            except Exception as e:
                logger.debug(f"Algorithm {algorithm.value} failed: {e}")
                continue
        
        if not results:
            return ETAResult(
                eta_seconds=float('inf'),
                confidence=0.0,
                algorithm_used=ETAAlgorithm.ADAPTIVE_HYBRID,
                speed_trend="unknown"
            )
        
        # Choose best result based on confidence and reasonableness
        best_result = max(results, key=lambda r: r.confidence)
        
        # Adjust confidence based on data quality
        data_quality_factor = self._assess_data_quality()
        best_result.confidence *= data_quality_factor
        best_result.algorithm_used = ETAAlgorithm.ADAPTIVE_HYBRID
        
        return best_result
    
    def _detect_speed_trend(self, samples: List[SpeedSample]) -> str:
        """Detect if speed is increasing, decreasing, or stable"""
        if len(samples) < 3:
            return "unknown"
        
        # Compare first half with second half
        mid_point = len(samples) // 2
        first_half_avg = statistics.mean(sample.speed for sample in samples[:mid_point])
        second_half_avg = statistics.mean(sample.speed for sample in samples[mid_point:])
        
        if first_half_avg == 0:
            return "unknown"
        
        change_ratio = (second_half_avg - first_half_avg) / first_half_avg
        
        if change_ratio > self.trend_threshold:
            return "increasing"
        elif change_ratio < -self.trend_threshold:
            return "decreasing"
        else:
            return "stable"
    
    def _assess_data_quality(self) -> float:
        """Assess quality of speed data for confidence adjustment"""
        if not self.speed_samples:
            return 0.0
        
        # Factors affecting data quality
        sample_count_factor = min(len(self.speed_samples) / 20.0, 1.0)
        
        # Speed consistency (lower variance = higher quality)
        speeds = [sample.speed for sample in self.speed_samples]
        if len(speeds) > 1:
            speed_variance = statistics.variance(speeds)
            speed_mean = statistics.mean(speeds)
            cv = speed_variance / (speed_mean ** 2) if speed_mean > 0 else float('inf')
            consistency_factor = max(0, 1 - cv)
        else:
            consistency_factor = 0.5
        
        # Recency factor (more recent data = higher quality)
        current_time = time.time()
        if self.speed_samples:
            latest_sample_age = current_time - self.speed_samples[-1].timestamp
            recency_factor = max(0, 1 - latest_sample_age / 300.0)  # 5 minutes max age
        else:
            recency_factor = 0.0
        
        # Combine factors
        overall_quality = (sample_count_factor * 0.4 + 
                          consistency_factor * 0.4 + 
                          recency_factor * 0.2)
        
        return float(max(0.1, min(1.0, overall_quality)))
    
    def get_speed_statistics(self) -> Dict[str, float]:
        """Get comprehensive speed statistics"""
        if not self.speed_samples:
            return {}
        
        speeds = [sample.speed for sample in self.speed_samples]
        
        return {
            "current_speed": speeds[-1] if speeds else 0,
            "average_speed": statistics.mean(speeds),
            "median_speed": statistics.median(speeds),
            "min_speed": min(speeds),
            "max_speed": max(speeds),
            "speed_variance": statistics.variance(speeds) if len(speeds) > 1 else 0,
            "sample_count": len(speeds),
            "data_quality": self._assess_data_quality()
        }
    
    def reset(self) -> None:
        """Reset calculator state"""
        self.speed_samples.clear()
    
    def add_historical_completion(self, file_size: int, completion_time: float, avg_speed: float) -> None:
        """Add historical completion data for future predictions"""
        self.historical_data["file_sizes"].append(file_size)
        self.historical_data["completion_times"].append(completion_time)
        self.historical_data["speeds"].append(avg_speed)
        
        # Keep only recent history (last 100 completions)
        for key in self.historical_data:
            if len(self.historical_data[key]) > 100:
                self.historical_data[key] = self.historical_data[key][-100:]

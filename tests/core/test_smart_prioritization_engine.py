import pytest
import time
import threading
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, List, Optional, Any

from src.core.smart_prioritization_engine import (
    SmartPrioritizationEngine, PrioritizationFactor, PrioritizationWeights,
    TaskMetrics, PrioritizationResult, smart_prioritization_engine
)


class TestPrioritizationFactor:
    """Test suite for PrioritizationFactor enum."""

    def test_factor_values(self) -> None:
        """Test enum values."""
        assert PrioritizationFactor.FILE_SIZE.value == "file_size"
        assert PrioritizationFactor.USER_PREFERENCE.value == "user_preference"
        assert PrioritizationFactor.SYSTEM_RESOURCES.value == "system_resources"
        assert PrioritizationFactor.HISTORICAL_PERFORMANCE.value == "historical_performance"
        assert PrioritizationFactor.TIME_SENSITIVITY.value == "time_sensitivity"
        assert PrioritizationFactor.DEPENDENCY_CHAIN.value == "dependency_chain"
        assert PrioritizationFactor.BANDWIDTH_EFFICIENCY.value == "bandwidth_efficiency"
        assert PrioritizationFactor.COMPLETION_PROBABILITY.value == "completion_probability"


class TestPrioritizationWeights:
    """Test suite for PrioritizationWeights dataclass."""

    def test_weights_creation(self) -> None:
        """Test PrioritizationWeights creation with all fields."""
        weights = PrioritizationWeights(
            file_size=0.25,
            user_preference=0.35,
            system_resources=0.2,
            historical_performance=0.1,
            time_sensitivity=0.05,
            dependency_chain=0.02,
            bandwidth_efficiency=0.02,
            completion_probability=0.01
        )
        
        assert weights.file_size == 0.25
        assert weights.user_preference == 0.35
        assert weights.system_resources == 0.2
        assert weights.historical_performance == 0.1
        assert weights.time_sensitivity == 0.05
        assert weights.dependency_chain == 0.02
        assert weights.bandwidth_efficiency == 0.02
        assert weights.completion_probability == 0.01

    def test_weights_defaults(self) -> None:
        """Test PrioritizationWeights with default values."""
        weights = PrioritizationWeights()
        
        assert weights.file_size == 0.2
        assert weights.user_preference == 0.3
        assert weights.system_resources == 0.15
        assert weights.historical_performance == 0.1
        assert weights.time_sensitivity == 0.1
        assert weights.dependency_chain == 0.05
        assert weights.bandwidth_efficiency == 0.05
        assert weights.completion_probability == 0.05

    def test_normalize_weights(self) -> None:
        """Test weight normalization."""
        weights = PrioritizationWeights(
            file_size=2.0,
            user_preference=3.0,
            system_resources=1.0,
            historical_performance=1.0,
            time_sensitivity=1.0,
            dependency_chain=1.0,
            bandwidth_efficiency=1.0,
            completion_probability=0.0
        )
        
        weights.normalize()
        
        # Total should be 1.0
        total = (weights.file_size + weights.user_preference + weights.system_resources +
                weights.historical_performance + weights.time_sensitivity + 
                weights.dependency_chain + weights.bandwidth_efficiency + 
                weights.completion_probability)
        
        assert abs(total - 1.0) < 0.001  # Allow for floating point precision


class TestTaskMetrics:
    """Test suite for TaskMetrics dataclass."""

    def test_task_metrics_creation(self) -> None:
        """Test TaskMetrics creation with all fields."""
        current_time = time.time()
        deadline = current_time + 3600  # 1 hour from now
        
        metrics = TaskMetrics(
            task_id="test_task",
            file_size=1048576,
            estimated_duration=120.0,
            user_priority=4,
            created_at=current_time,
            deadline=deadline,
            dependencies=["dep1", "dep2"],
            historical_success_rate=0.85,
            bandwidth_requirement=1024.0,
            resource_intensity=0.7,
            metadata={"quality": "720p"}
        )
        
        assert metrics.task_id == "test_task"
        assert metrics.file_size == 1048576
        assert metrics.estimated_duration == 120.0
        assert metrics.user_priority == 4
        assert metrics.created_at == current_time
        assert metrics.deadline == deadline
        assert metrics.dependencies == ["dep1", "dep2"]
        assert metrics.historical_success_rate == 0.85
        assert metrics.bandwidth_requirement == 1024.0
        assert metrics.resource_intensity == 0.7
        assert metrics.metadata == {"quality": "720p"}

    def test_task_metrics_defaults(self) -> None:
        """Test TaskMetrics with default values."""
        metrics = TaskMetrics(
            task_id="test_task",
            file_size=1048576,
            estimated_duration=120.0,
            user_priority=3,
            created_at=time.time()
        )
        
        assert metrics.deadline is None
        assert metrics.dependencies == []
        assert metrics.historical_success_rate == 1.0
        assert metrics.bandwidth_requirement == 0.0
        assert metrics.resource_intensity == 0.5
        assert metrics.metadata == {}


class TestPrioritizationResult:
    """Test suite for PrioritizationResult dataclass."""

    def test_result_creation(self) -> None:
        """Test PrioritizationResult creation."""
        factor_scores = {
            "file_size": 0.8,
            "user_preference": 0.9,
            "system_resources": 0.6
        }
        reasoning = ["Small file size", "High user priority"]
        
        result = PrioritizationResult(
            task_id="test_task",
            priority_score=0.75,
            factor_scores=factor_scores,
            recommended_order=2,
            reasoning=reasoning,
            confidence=0.85
        )
        
        assert result.task_id == "test_task"
        assert result.priority_score == 0.75
        assert result.factor_scores == factor_scores
        assert result.recommended_order == 2
        assert result.reasoning == reasoning
        assert result.confidence == 0.85


class TestSmartPrioritizationEngine:
    """Test suite for SmartPrioritizationEngine class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = SmartPrioritizationEngine()

    def test_initialization(self) -> None:
        """Test SmartPrioritizationEngine initialization."""
        assert isinstance(self.engine.weights, PrioritizationWeights)
        assert isinstance(self.engine.lock, threading.RLock)
        assert isinstance(self.engine.completion_history, dict)
        assert isinstance(self.engine.performance_metrics, dict)
        assert isinstance(self.engine.user_behavior_patterns, dict)
        assert isinstance(self.engine.current_system_load, dict)
        assert self.engine.bandwidth_availability == 1.0
        assert self.engine.learning_enabled is True
        assert self.engine.adaptive_weights is True
        assert self.engine.max_history_size == 1000

    def test_prioritize_tasks_single_task(self) -> None:
        """Test prioritizing a single task."""
        task = TaskMetrics(
            task_id="task1",
            file_size=1024 * 1024,  # 1MB
            estimated_duration=60.0,
            user_priority=3,
            created_at=time.time()
        )
        
        results = self.engine.prioritize_tasks([task])
        
        assert len(results) == 1
        result = results[0]
        assert result.task_id == "task1"
        assert result.priority_score > 0
        assert result.recommended_order == 1
        assert isinstance(result.factor_scores, dict)
        assert isinstance(result.reasoning, list)
        assert 0 <= result.confidence <= 1

    def test_prioritize_tasks_multiple_tasks(self) -> None:
        """Test prioritizing multiple tasks."""
        tasks = [
            TaskMetrics("task1", 10 * 1024 * 1024, 300.0, 2, time.time()),  # Large, low priority
            TaskMetrics("task2", 1024 * 1024, 60.0, 5, time.time()),        # Small, high priority
            TaskMetrics("task3", 5 * 1024 * 1024, 150.0, 3, time.time())    # Medium
        ]
        
        results = self.engine.prioritize_tasks(tasks)
        
        assert len(results) == 3
        
        # Results should be sorted by priority score
        for i in range(len(results) - 1):
            assert results[i].priority_score >= results[i + 1].priority_score
        
        # Check recommended order
        for i, result in enumerate(results):
            assert result.recommended_order == i + 1

    def test_calculate_size_score(self) -> None:
        """Test file size score calculation."""
        # Test different file sizes
        small_task = TaskMetrics("small", 500 * 1024, 30.0, 3, time.time())  # 500KB
        medium_task = TaskMetrics("medium", 50 * 1024 * 1024, 300.0, 3, time.time())  # 50MB
        large_task = TaskMetrics("large", 2 * 1024 * 1024 * 1024, 1800.0, 3, time.time())  # 2GB
        
        small_score = self.engine._calculate_size_score(small_task)
        medium_score = self.engine._calculate_size_score(medium_task)
        large_score = self.engine._calculate_size_score(large_task)
        
        # Smaller files should get higher scores
        assert small_score > medium_score > large_score
        assert small_score == 1.0  # < 1MB should get max score
        assert large_score == 0.3   # 1-5GB range

    def test_calculate_user_preference_score(self) -> None:
        """Test user preference score calculation."""
        low_priority = TaskMetrics("low", 1024, 60.0, 1, time.time())
        high_priority = TaskMetrics("high", 1024, 60.0, 5, time.time())
        
        low_score = self.engine._calculate_user_preference_score(low_priority)
        high_score = self.engine._calculate_user_preference_score(high_priority)
        
        assert high_score > low_score
        assert low_score == 0.2   # Priority 1 -> 0.2
        assert high_score == 1.0  # Priority 5 -> 1.0

    def test_calculate_system_resource_score(self) -> None:
        """Test system resource score calculation."""
        # Test with different system loads
        light_task = TaskMetrics("light", 1024, 60.0, 3, time.time(), resource_intensity=0.2)
        heavy_task = TaskMetrics("heavy", 1024, 60.0, 3, time.time(), resource_intensity=0.9)
        
        # Set high system load
        self.engine.current_system_load = {"cpu": 0.8, "memory": 0.7, "disk": 0.6}
        
        light_score = self.engine._calculate_system_resource_score(light_task)
        heavy_score = self.engine._calculate_system_resource_score(heavy_task)
        
        # Light tasks should score better when system is loaded
        assert light_score > heavy_score

    def test_calculate_time_sensitivity_score(self) -> None:
        """Test time sensitivity score calculation."""
        current_time = time.time()
        
        # Task with no deadline (uses age)
        old_task = TaskMetrics("old", 1024, 60.0, 3, current_time - 86400)  # 1 day old
        new_task = TaskMetrics("new", 1024, 60.0, 3, current_time)
        
        old_score = self.engine._calculate_time_sensitivity_score(old_task)
        new_score = self.engine._calculate_time_sensitivity_score(new_task)
        
        assert old_score > new_score  # Older tasks get higher priority
        
        # Task with urgent deadline
        urgent_task = TaskMetrics("urgent", 1024, 60.0, 3, current_time, deadline=current_time + 1800)  # 30 min
        distant_task = TaskMetrics("distant", 1024, 60.0, 3, current_time, deadline=current_time + 86400)  # 1 day
        
        urgent_score = self.engine._calculate_time_sensitivity_score(urgent_task)
        distant_score = self.engine._calculate_time_sensitivity_score(distant_task)
        
        assert urgent_score > distant_score

    def test_calculate_dependency_score(self) -> None:
        """Test dependency chain score calculation."""
        independent_task = TaskMetrics("independent", 1024, 60.0, 3, time.time())
        blocking_task = TaskMetrics("blocking", 1024, 60.0, 3, time.time())
        
        # Mock dependency checking
        with patch.object(self.engine, '_count_dependent_tasks', return_value=3):
            blocking_score = self.engine._calculate_dependency_score(blocking_task)
        
        with patch.object(self.engine, '_count_dependent_tasks', return_value=0):
            independent_score = self.engine._calculate_dependency_score(independent_task)
        
        assert blocking_score > independent_score

    def test_calculate_completion_probability_score(self) -> None:
        """Test completion probability score calculation."""
        reliable_task = TaskMetrics("reliable", 1024, 60.0, 3, time.time(), historical_success_rate=0.95)
        unreliable_task = TaskMetrics("unreliable", 1024, 60.0, 3, time.time(), historical_success_rate=0.6)
        
        reliable_score = self.engine._calculate_completion_probability_score(reliable_task)
        unreliable_score = self.engine._calculate_completion_probability_score(unreliable_task)
        
        assert reliable_score > unreliable_score

    def test_calculate_confidence(self) -> None:
        """Test confidence calculation."""
        task = TaskMetrics(
            "test", 1024, 60.0, 3, time.time(),
            deadline=time.time() + 3600,
            dependencies=["dep1"],
            historical_success_rate=0.8
        )
        
        factor_scores = {
            "file_size": 0.8,
            "user_preference": 0.6,
            "system_resources": 0.7
        }
        
        confidence = self.engine._calculate_confidence(task, factor_scores)
        
        assert 0 <= confidence <= 1
        # Task with complete information should have reasonable confidence
        assert confidence > 0.5

    def test_learn_from_completion_success(self) -> None:
        """Test learning from successful completion."""
        initial_history_size = len(self.engine.completion_history.get("test_task", []))
        
        self.engine.learn_from_completion(
            task_id="test_task",
            success=True,
            actual_duration=120.0,
            final_size=1048576,
            metadata={"quality": "720p"}
        )
        
        # Should have added to completion history
        assert "test_task" in self.engine.completion_history
        assert len(self.engine.completion_history["test_task"]) == initial_history_size + 1
        
        # Check completion record
        record = self.engine.completion_history["test_task"][-1]
        assert record["success"] is True
        assert record["duration"] == 120.0
        assert record["size"] == 1048576

    def test_learn_from_completion_failure(self) -> None:
        """Test learning from failed completion."""
        self.engine.learn_from_completion(
            task_id="failed_task",
            success=False,
            actual_duration=60.0,
            final_size=0
        )
        
        assert "failed_task" in self.engine.completion_history
        record = self.engine.completion_history["failed_task"][-1]
        assert record["success"] is False

    def test_learn_from_completion_disabled(self) -> None:
        """Test learning when disabled."""
        self.engine.learning_enabled = False
        initial_history_size = len(self.engine.completion_history)
        
        self.engine.learn_from_completion("test", True, 60.0, 1024)
        
        # Should not have added anything
        assert len(self.engine.completion_history) == initial_history_size

    def test_update_system_state(self) -> None:
        """Test updating system state."""
        system_state = {
            "cpu": 0.7,
            "memory": 0.6,
            "disk": 0.5,
            "network": 0.8
        }
        
        self.engine.update_system_state(system_state)
        
        assert self.engine.current_system_load == system_state

    def test_set_prioritization_weights(self) -> None:
        """Test setting custom prioritization weights."""
        custom_weights = PrioritizationWeights(
            file_size=0.5,
            user_preference=0.3,
            system_resources=0.1,
            historical_performance=0.05,
            time_sensitivity=0.03,
            dependency_chain=0.01,
            bandwidth_efficiency=0.01,
            completion_probability=0.0
        )
        
        self.engine.set_prioritization_weights(custom_weights)
        
        # Weights should be normalized
        total = (self.engine.weights.file_size + self.engine.weights.user_preference +
                self.engine.weights.system_resources + self.engine.weights.historical_performance +
                self.engine.weights.time_sensitivity + self.engine.weights.dependency_chain +
                self.engine.weights.bandwidth_efficiency + self.engine.weights.completion_probability)
        
        assert abs(total - 1.0) < 0.001

    def test_register_prioritization_callback(self) -> None:
        """Test registering prioritization callback."""
        callback = Mock()
        
        self.engine.register_prioritization_callback(callback)
        
        assert callback in self.engine.prioritization_callbacks

    def test_trigger_prioritization_callbacks(self) -> None:
        """Test triggering prioritization callbacks."""
        callback = Mock()
        self.engine.register_prioritization_callback(callback)
        
        results = [
            PrioritizationResult("task1", 0.8, {}, 1, [], 0.9)
        ]
        
        self.engine._trigger_prioritization_callbacks(results)
        
        callback.assert_called_once_with(results)

    def test_callback_error_handling(self) -> None:
        """Test error handling in callbacks."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()
        
        self.engine.register_prioritization_callback(error_callback)
        self.engine.register_prioritization_callback(good_callback)
        
        results = [PrioritizationResult("task1", 0.8, {}, 1, [], 0.9)]
        
        # Should not raise exception
        self.engine._trigger_prioritization_callbacks(results)
        
        # Both callbacks should be called
        error_callback.assert_called_once()
        good_callback.assert_called_once()

    def test_get_engine_statistics(self) -> None:
        """Test getting engine statistics."""
        # Add some completion history
        self.engine.learn_from_completion("task1", True, 60.0, 1024)
        self.engine.learn_from_completion("task2", False, 30.0, 0)
        self.engine.learn_from_completion("task3", True, 90.0, 2048)
        
        stats = self.engine.get_engine_statistics()
        
        assert stats["total_completions"] == 3
        assert stats["success_rate"] == 2/3  # 2 successes out of 3
        assert stats["learning_enabled"] is True
        assert stats["adaptive_weights"] is True
        assert "current_weights" in stats
        assert len(stats["task_types"]) == 3

    def test_history_size_limit(self) -> None:
        """Test completion history size limit."""
        # Set small limit for testing
        self.engine.max_history_size = 3
        
        # Add more completions than limit
        for i in range(5):
            self.engine.learn_from_completion(f"task_{i}", True, 60.0, 1024)
        
        # Should only keep the most recent completions
        total_records = sum(len(records) for records in self.engine.completion_history.values())
        assert total_records <= 3

    def test_global_prioritization_engine_instance(self) -> None:
        """Test global prioritization engine instance."""
        assert smart_prioritization_engine is not None
        assert isinstance(smart_prioritization_engine, SmartPrioritizationEngine)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

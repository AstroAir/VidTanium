"""
Smart Prioritization Engine for VidTanium
Provides intelligent task prioritization based on multiple factors including file size,
user preferences, system resources, and historical data
"""

import time
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics
import math

from loguru import logger


class PrioritizationFactor(Enum):
    """Factors that influence task prioritization"""
    FILE_SIZE = "file_size"
    USER_PREFERENCE = "user_preference"
    SYSTEM_RESOURCES = "system_resources"
    HISTORICAL_PERFORMANCE = "historical_performance"
    TIME_SENSITIVITY = "time_sensitivity"
    DEPENDENCY_CHAIN = "dependency_chain"
    BANDWIDTH_EFFICIENCY = "bandwidth_efficiency"
    COMPLETION_PROBABILITY = "completion_probability"


@dataclass
class PrioritizationWeights:
    """Weights for different prioritization factors"""
    file_size: float = 0.2
    user_preference: float = 0.3
    system_resources: float = 0.15
    historical_performance: float = 0.1
    time_sensitivity: float = 0.1
    dependency_chain: float = 0.05
    bandwidth_efficiency: float = 0.05
    completion_probability: float = 0.05
    
    def normalize(self) -> None:
        """Normalize weights to sum to 1.0"""
        total = (self.file_size + self.user_preference + self.system_resources +
                self.historical_performance + self.time_sensitivity + 
                self.dependency_chain + self.bandwidth_efficiency + 
                self.completion_probability)
        
        if total > 0:
            self.file_size /= total
            self.user_preference /= total
            self.system_resources /= total
            self.historical_performance /= total
            self.time_sensitivity /= total
            self.dependency_chain /= total
            self.bandwidth_efficiency /= total
            self.completion_probability /= total


@dataclass
class TaskMetrics:
    """Metrics for a task used in prioritization"""
    task_id: str
    file_size: int
    estimated_duration: float
    user_priority: int  # 1-5 scale
    created_at: float
    deadline: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    historical_success_rate: float = 1.0
    bandwidth_requirement: float = 0.0
    resource_intensity: float = 0.5  # 0-1 scale
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrioritizationResult:
    """Result of task prioritization"""
    task_id: str
    priority_score: float
    factor_scores: Dict[str, float]
    recommended_order: int
    reasoning: List[str]
    confidence: float


class SmartPrioritizationEngine:
    """Intelligent task prioritization engine"""
    
    def __init__(self) -> None:
        self.weights = PrioritizationWeights()
        self.weights.normalize()
        
        self.lock = threading.RLock()
        
        # Historical data for learning
        self.completion_history: Dict[str, List[Dict]] = {}
        self.performance_metrics: Dict[str, Dict] = {}
        self.user_behavior_patterns: Dict[str, Any] = {}
        
        # System state
        self.current_system_load: Dict[str, float] = {}
        self.bandwidth_availability: float = 1.0
        
        # Configuration
        self.learning_enabled = True
        self.adaptive_weights = True
        self.max_history_size = 1000
        
        # Callbacks
        self.prioritization_callbacks: List[Callable[[List[PrioritizationResult]], None]] = []
    
    def prioritize_tasks(
        self,
        tasks: List[TaskMetrics],
        system_state: Optional[Dict[str, float]] = None
    ) -> List[PrioritizationResult]:
        """Prioritize a list of tasks and return ordered results"""
        
        with self.lock:
            if system_state:
                self.current_system_load = system_state
            
            results = []
            
            for task in tasks:
                priority_score, factor_scores, reasoning = self._calculate_priority_score(task)
                confidence = self._calculate_confidence(task, factor_scores)
                
                result = PrioritizationResult(
                    task_id=task.task_id,
                    priority_score=priority_score,
                    factor_scores=factor_scores,
                    recommended_order=0,  # Will be set after sorting
                    reasoning=reasoning,
                    confidence=confidence
                )
                results.append(result)
            
            # Sort by priority score (higher = more important)
            results.sort(key=lambda r: r.priority_score, reverse=True)
            
            # Set recommended order
            for i, result in enumerate(results):
                result.recommended_order = i + 1
            
            # Trigger callbacks
            self._trigger_prioritization_callbacks(results)
            
            return results
    
    def _calculate_priority_score(self, task: TaskMetrics) -> Tuple[float, Dict[str, float], List[str]]:
        """Calculate priority score for a task"""
        
        factor_scores = {}
        reasoning = []
        
        # File size factor (smaller files get higher priority for quick wins)
        size_score = self._calculate_size_score(task)
        factor_scores[PrioritizationFactor.FILE_SIZE.value] = size_score
        if size_score > 0.7:
            reasoning.append("Small file size allows for quick completion")
        elif size_score < 0.3:
            reasoning.append("Large file size may require significant resources")
        
        # User preference factor
        user_score = self._calculate_user_preference_score(task)
        factor_scores[PrioritizationFactor.USER_PREFERENCE.value] = user_score
        if user_score > 0.8:
            reasoning.append("High user priority")
        
        # System resources factor
        resource_score = self._calculate_system_resource_score(task)
        factor_scores[PrioritizationFactor.SYSTEM_RESOURCES.value] = resource_score
        if resource_score < 0.4:
            reasoning.append("System resources may be constrained")
        
        # Historical performance factor
        history_score = self._calculate_historical_score(task)
        factor_scores[PrioritizationFactor.HISTORICAL_PERFORMANCE.value] = history_score
        if history_score < 0.5:
            reasoning.append("Similar tasks have had mixed success rates")
        
        # Time sensitivity factor
        time_score = self._calculate_time_sensitivity_score(task)
        factor_scores[PrioritizationFactor.TIME_SENSITIVITY.value] = time_score
        if time_score > 0.8:
            reasoning.append("Time-sensitive task approaching deadline")
        
        # Dependency chain factor
        dependency_score = self._calculate_dependency_score(task)
        factor_scores[PrioritizationFactor.DEPENDENCY_CHAIN.value] = dependency_score
        if dependency_score > 0.7:
            reasoning.append("Task blocks other dependent tasks")
        
        # Bandwidth efficiency factor
        bandwidth_score = self._calculate_bandwidth_efficiency_score(task)
        factor_scores[PrioritizationFactor.BANDWIDTH_EFFICIENCY.value] = bandwidth_score
        
        # Completion probability factor
        completion_score = self._calculate_completion_probability_score(task)
        factor_scores[PrioritizationFactor.COMPLETION_PROBABILITY.value] = completion_score
        if completion_score < 0.4:
            reasoning.append("Task has lower probability of successful completion")
        
        # Calculate weighted total score
        total_score = (
            factor_scores[PrioritizationFactor.FILE_SIZE.value] * self.weights.file_size +
            factor_scores[PrioritizationFactor.USER_PREFERENCE.value] * self.weights.user_preference +
            factor_scores[PrioritizationFactor.SYSTEM_RESOURCES.value] * self.weights.system_resources +
            factor_scores[PrioritizationFactor.HISTORICAL_PERFORMANCE.value] * self.weights.historical_performance +
            factor_scores[PrioritizationFactor.TIME_SENSITIVITY.value] * self.weights.time_sensitivity +
            factor_scores[PrioritizationFactor.DEPENDENCY_CHAIN.value] * self.weights.dependency_chain +
            factor_scores[PrioritizationFactor.BANDWIDTH_EFFICIENCY.value] * self.weights.bandwidth_efficiency +
            factor_scores[PrioritizationFactor.COMPLETION_PROBABILITY.value] * self.weights.completion_probability
        )
        
        return total_score, factor_scores, reasoning
    
    def _calculate_size_score(self, task: TaskMetrics) -> float:
        """Calculate score based on file size (smaller = higher score)"""
        if task.file_size <= 0:
            return 0.5  # Unknown size
        
        # Use logarithmic scale to handle wide range of file sizes
        # Normalize to 0-1 range where smaller files get higher scores
        size_mb = task.file_size / (1024 * 1024)
        
        if size_mb < 1:  # < 1MB
            return 1.0
        elif size_mb < 10:  # 1-10MB
            return 0.9
        elif size_mb < 100:  # 10-100MB
            return 0.7
        elif size_mb < 1000:  # 100MB-1GB
            return 0.5
        elif size_mb < 5000:  # 1-5GB
            return 0.3
        else:  # > 5GB
            return 0.1
    
    def _calculate_user_preference_score(self, task: TaskMetrics) -> float:
        """Calculate score based on user-assigned priority"""
        # Convert 1-5 scale to 0-1 score
        return (task.user_priority - 1) / 4.0
    
    def _calculate_system_resource_score(self, task: TaskMetrics) -> float:
        """Calculate score based on system resource availability"""
        cpu_load = self.current_system_load.get('cpu_percent', 50) / 100.0
        memory_load = self.current_system_load.get('memory_percent', 50) / 100.0
        
        # Higher resource availability = higher score
        # Adjust based on task's resource intensity
        available_resources = (2.0 - cpu_load - memory_load) / 2.0
        resource_match = 1.0 - abs(available_resources - task.resource_intensity)
        
        return max(0.0, min(1.0, resource_match))
    
    def _calculate_historical_score(self, task: TaskMetrics) -> float:
        """Calculate score based on historical performance of similar tasks"""
        # Look for similar tasks in history
        similar_tasks = self._find_similar_tasks(task)
        
        if not similar_tasks:
            return 0.7  # Neutral score for unknown tasks
        
        # Calculate average success rate
        success_rates = [t.get('success_rate', 0.5) for t in similar_tasks]
        avg_success_rate = statistics.mean(success_rates)
        
        return float(avg_success_rate)
    
    def _calculate_time_sensitivity_score(self, task: TaskMetrics) -> float:
        """Calculate score based on time sensitivity and deadlines"""
        current_time = time.time()
        
        # If no deadline, use age of task
        if not task.deadline:
            age_hours = (current_time - task.created_at) / 3600
            # Older tasks get slightly higher priority
            return min(1.0, 0.5 + (age_hours / 168))  # 168 hours = 1 week
        
        # Calculate urgency based on deadline
        time_to_deadline = task.deadline - current_time
        
        if time_to_deadline <= 0:
            return 1.0  # Overdue - highest priority
        elif time_to_deadline < 3600:  # < 1 hour
            return 0.95
        elif time_to_deadline < 86400:  # < 1 day
            return 0.8
        elif time_to_deadline < 604800:  # < 1 week
            return 0.6
        else:
            return 0.4
    
    def _calculate_dependency_score(self, task: TaskMetrics) -> float:
        """Calculate score based on dependency chain impact"""
        if not task.dependencies:
            return 0.5  # No dependencies
        
        # Tasks with more dependencies or that block others get higher priority
        dependency_count = len(task.dependencies)
        
        # Simple scoring based on dependency count
        if dependency_count == 0:
            return 0.5
        elif dependency_count <= 2:
            return 0.7
        elif dependency_count <= 5:
            return 0.8
        else:
            return 0.9
    
    def _calculate_bandwidth_efficiency_score(self, task: TaskMetrics) -> float:
        """Calculate score based on bandwidth efficiency"""
        if task.bandwidth_requirement <= 0:
            return 0.5  # Unknown requirement
        
        # Higher efficiency when bandwidth requirement matches availability
        efficiency = min(1.0, self.bandwidth_availability / task.bandwidth_requirement)
        return efficiency
    
    def _calculate_completion_probability_score(self, task: TaskMetrics) -> float:
        """Calculate score based on probability of successful completion"""
        # Base probability on historical success rate and task characteristics
        base_probability = task.historical_success_rate
        
        # Adjust based on file size (very large files are riskier)
        size_factor = 1.0
        if task.file_size > 5 * 1024 * 1024 * 1024:  # > 5GB
            size_factor = 0.8
        elif task.file_size > 1024 * 1024 * 1024:  # > 1GB
            size_factor = 0.9
        
        # Adjust based on system resources
        resource_factor = self._calculate_system_resource_score(task)
        
        return base_probability * size_factor * resource_factor
    
    def _find_similar_tasks(self, task: TaskMetrics) -> List[Dict]:
        """Find similar tasks in completion history"""
        similar_tasks = []
        
        for task_type, history in self.completion_history.items():
            for historical_task in history:
                # Simple similarity based on file size range
                hist_size = historical_task.get('file_size', 0)
                size_ratio = min(task.file_size, hist_size) / max(task.file_size, hist_size, 1)
                
                if size_ratio > 0.5:  # Similar size
                    similar_tasks.append(historical_task)
        
        return similar_tasks[-10:]  # Return recent similar tasks
    
    def _calculate_confidence(self, task: TaskMetrics, factor_scores: Dict[str, float]) -> float:
        """Calculate confidence in the prioritization decision"""
        # Confidence based on:
        # 1. Availability of historical data
        # 2. Consistency of factor scores
        # 3. Amount of available information
        
        historical_data_confidence = 0.5
        if task.task_id in self.performance_metrics:
            historical_data_confidence = 0.8
        
        # Score consistency (lower variance = higher confidence)
        scores = list(factor_scores.values())
        if len(scores) > 1:
            score_variance = statistics.variance(scores)
            consistency_confidence = max(0.3, 1.0 - score_variance)
        else:
            consistency_confidence = 0.5
        
        # Information completeness
        info_completeness = 0.5
        if task.file_size > 0:
            info_completeness += 0.1
        if task.estimated_duration > 0:
            info_completeness += 0.1
        if task.deadline:
            info_completeness += 0.1
        if task.dependencies:
            info_completeness += 0.1
        if task.historical_success_rate != 1.0:  # Has historical data
            info_completeness += 0.2
        
        # Combine confidence factors
        overall_confidence = (
            historical_data_confidence * 0.4 +
            consistency_confidence * 0.4 +
            info_completeness * 0.2
        )
        
        return max(0.1, min(1.0, overall_confidence))
    
    def learn_from_completion(
        self,
        task_id: str,
        success: bool,
        actual_duration: float,
        final_size: int,
        metadata: Optional[Dict] = None
    ) -> None:
        """Learn from completed task to improve future prioritization"""
        if not self.learning_enabled:
            return
        
        with self.lock:
            # Update completion history
            task_type = self._classify_task_type(final_size, metadata or {})
            
            if task_type not in self.completion_history:
                self.completion_history[task_type] = []
            
            completion_record = {
                'task_id': task_id,
                'success': success,
                'success_rate': 1.0 if success else 0.0,
                'duration': actual_duration,
                'file_size': final_size,
                'timestamp': time.time(),
                'metadata': metadata or {}
            }
            
            self.completion_history[task_type].append(completion_record)
            
            # Trim history if too large
            if len(self.completion_history[task_type]) > self.max_history_size:
                self.completion_history[task_type] = self.completion_history[task_type][-self.max_history_size:]
            
            # Update performance metrics
            self._update_performance_metrics(task_id, completion_record)
            
            # Adapt weights if enabled
            if self.adaptive_weights:
                self._adapt_weights_from_feedback(completion_record)
    
    def _classify_task_type(self, file_size: int, metadata: Dict) -> str:
        """Classify task type for historical learning"""
        # Simple classification based on file size
        if file_size < 10 * 1024 * 1024:  # < 10MB
            return "small"
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return "medium"
        elif file_size < 1024 * 1024 * 1024:  # < 1GB
            return "large"
        else:
            return "very_large"
    
    def _update_performance_metrics(self, task_id: str, completion_record: Dict) -> None:
        """Update performance metrics for the task"""
        if task_id not in self.performance_metrics:
            self.performance_metrics[task_id] = {
                'attempts': 0,
                'successes': 0,
                'total_duration': 0,
                'average_duration': 0
            }
        
        metrics = self.performance_metrics[task_id]
        metrics['attempts'] += 1
        
        if completion_record['success']:
            metrics['successes'] += 1
        
        metrics['total_duration'] += completion_record['duration']
        metrics['average_duration'] = metrics['total_duration'] / metrics['attempts']
        metrics['success_rate'] = metrics['successes'] / metrics['attempts']
    
    def _adapt_weights_from_feedback(self, completion_record: Dict) -> None:
        """Adapt prioritization weights based on completion feedback"""
        # Simple adaptive mechanism - could be more sophisticated
        if completion_record['success']:
            # Successful completion - slightly increase weight of factors that predicted success
            pass  # Implementation would analyze which factors contributed to success
        else:
            # Failed completion - slightly decrease weight of factors that predicted success
            pass  # Implementation would analyze which factors led to failure
    
    def update_system_state(self, system_state: Dict[str, float]) -> None:
        """Update current system state for prioritization"""
        with self.lock:
            self.current_system_load = system_state
    
    def set_prioritization_weights(self, weights: PrioritizationWeights) -> None:
        """Set custom prioritization weights"""
        with self.lock:
            self.weights = weights
            self.weights.normalize()
    
    def register_prioritization_callback(self, callback: Callable[[List[PrioritizationResult]], None]) -> None:
        """Register callback for prioritization results"""
        self.prioritization_callbacks.append(callback)
    
    def _trigger_prioritization_callbacks(self, results: List[PrioritizationResult]) -> None:
        """Trigger prioritization callbacks"""
        for callback in self.prioritization_callbacks:
            try:
                callback(results)
            except Exception as e:
                logger.error(f"Error in prioritization callback: {e}")
    
    def get_prioritization_statistics(self) -> Dict[str, Any]:
        """Get statistics about prioritization performance"""
        with self.lock:
            total_completions = sum(len(history) for history in self.completion_history.values())
            successful_completions = sum(
                sum(1 for record in history if record['success'])
                for history in self.completion_history.values()
            )
            
            success_rate = (successful_completions / total_completions) if total_completions > 0 else 0
            
            return {
                'total_completions': total_completions,
                'success_rate': success_rate,
                'task_types': list(self.completion_history.keys()),
                'learning_enabled': self.learning_enabled,
                'adaptive_weights': self.adaptive_weights,
                'current_weights': {
                    'file_size': self.weights.file_size,
                    'user_preference': self.weights.user_preference,
                    'system_resources': self.weights.system_resources,
                    'historical_performance': self.weights.historical_performance,
                    'time_sensitivity': self.weights.time_sensitivity,
                    'dependency_chain': self.weights.dependency_chain,
                    'bandwidth_efficiency': self.weights.bandwidth_efficiency,
                    'completion_probability': self.weights.completion_probability
                }
            }


# Global smart prioritization engine instance
smart_prioritization_engine = SmartPrioritizationEngine()

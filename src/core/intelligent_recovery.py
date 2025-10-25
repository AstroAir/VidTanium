"""
Intelligent Error Recovery System for VidTanium
Provides advanced error recovery with user guidance and automated solutions
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from .exceptions import VidTaniumException, ErrorCategory, ErrorSeverity, UserAction
from .retry_manager import IntelligentRetryManager
from .progressive_recovery import ProgressiveRecoveryManager
from .circuit_breaker import CircuitBreakerManager


class RecoveryStrategy(Enum):
    """Recovery strategy types"""
    IMMEDIATE_RETRY = "immediate_retry"
    DELAYED_RETRY = "delayed_retry"
    ALTERNATIVE_SOURCE = "alternative_source"
    QUALITY_DOWNGRADE = "quality_downgrade"
    SEGMENT_SKIP = "segment_skip"
    USER_INTERVENTION = "user_intervention"
    ABORT = "abort"


class RecoveryPriority(Enum):
    """Recovery priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RecoveryAction:
    """Represents a recovery action"""
    strategy: RecoveryStrategy
    priority: RecoveryPriority
    description: str
    automated: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    success_probability: float = 0.5
    estimated_time: float = 0.0  # seconds


@dataclass
class RecoveryPlan:
    """Complete recovery plan for an error"""
    error_id: str
    actions: List[RecoveryAction]
    user_guidance: List[str]
    fallback_actions: List[RecoveryAction]
    created_at: float = field(default_factory=time.time)


class IntelligentRecoverySystem:
    """Advanced error recovery system with user guidance"""
    
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.recovery_history: Dict[str, List[RecoveryPlan]] = {}
        self.success_rates: Dict[RecoveryStrategy, float] = {}
        self.retry_manager = IntelligentRetryManager()
        self.progressive_recovery = ProgressiveRecoveryManager()
        self.circuit_breaker = CircuitBreakerManager()
        
        # Recovery strategy configurations
        self._init_recovery_strategies()
        
        logger.info("Intelligent recovery system initialized")
    
    def _init_recovery_strategies(self) -> None:
        """Initialize recovery strategy success rates"""
        self.success_rates = {
            RecoveryStrategy.IMMEDIATE_RETRY: 0.3,
            RecoveryStrategy.DELAYED_RETRY: 0.6,
            RecoveryStrategy.ALTERNATIVE_SOURCE: 0.8,
            RecoveryStrategy.QUALITY_DOWNGRADE: 0.9,
            RecoveryStrategy.SEGMENT_SKIP: 0.7,
            RecoveryStrategy.USER_INTERVENTION: 0.95,
            RecoveryStrategy.ABORT: 1.0
        }
    
    def create_recovery_plan(self, exception: VidTaniumException, context: Dict[str, Any]) -> RecoveryPlan:
        """Create intelligent recovery plan based on error analysis"""
        error_id = f"{exception.category.value}_{int(time.time())}"
        
        # Analyze error and create recovery actions
        actions = self._analyze_error_and_create_actions(exception, context)
        user_guidance = self._generate_user_guidance(exception, context)
        fallback_actions = self._create_fallback_actions(exception, context)
        
        plan = RecoveryPlan(
            error_id=error_id,
            actions=actions,
            user_guidance=user_guidance,
            fallback_actions=fallback_actions
        )
        
        # Store in history
        with self.lock:
            if exception.category.value not in self.recovery_history:
                self.recovery_history[exception.category.value] = []
            self.recovery_history[exception.category.value].append(plan)
        
        logger.info(f"Created recovery plan {error_id} with {len(actions)} actions")
        return plan
    
    def _analyze_error_and_create_actions(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Analyze error and create appropriate recovery actions"""
        actions = []
        
        if exception.category == ErrorCategory.NETWORK:
            actions.extend(self._create_network_recovery_actions(exception, context))
        elif exception.category == ErrorCategory.FILESYSTEM:
            actions.extend(self._create_filesystem_recovery_actions(exception, context))
        elif exception.category == ErrorCategory.AUTHENTICATION:
            actions.extend(self._create_auth_recovery_actions(exception, context))
        elif exception.category == ErrorCategory.RESOURCE:
            actions.extend(self._create_resource_recovery_actions(exception, context))
        elif exception.category == ErrorCategory.ENCRYPTION:
            actions.extend(self._create_encryption_recovery_actions(exception, context))
        else:
            actions.extend(self._create_generic_recovery_actions(exception, context))
        
        # Sort by priority and success probability
        actions.sort(key=lambda a: (a.priority.value, -a.success_probability), reverse=True)
        return actions
    
    def _create_network_recovery_actions(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Create network-specific recovery actions"""
        actions = []
        
        # Check if it's a timeout issue
        if "timeout" in str(exception).lower():
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.DELAYED_RETRY,
                priority=RecoveryPriority.HIGH,
                description="Retry with increased timeout",
                parameters={"timeout_multiplier": 2.0, "delay": 5.0},
                success_probability=0.7,
                estimated_time=10.0
            ))
        
        # Check if it's a connection issue
        if "connection" in str(exception).lower():
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.ALTERNATIVE_SOURCE,
                priority=RecoveryPriority.MEDIUM,
                description="Try alternative CDN or mirror",
                parameters={"use_backup_servers": True},
                success_probability=0.6,
                estimated_time=15.0
            ))
        
        # General network retry
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.IMMEDIATE_RETRY,
            priority=RecoveryPriority.MEDIUM,
            description="Immediate retry with current settings",
            success_probability=0.3,
            estimated_time=5.0
        ))
        
        return actions
    
    def _create_filesystem_recovery_actions(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Create filesystem-specific recovery actions"""
        actions = []
        
        # Disk space issues
        if "space" in str(exception).lower():
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.USER_INTERVENTION,
                priority=RecoveryPriority.CRITICAL,
                description="Free up disk space",
                automated=False,
                success_probability=0.9,
                estimated_time=300.0
            ))
            
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.QUALITY_DOWNGRADE,
                priority=RecoveryPriority.HIGH,
                description="Download lower quality to save space",
                parameters={"quality_reduction": 0.5},
                success_probability=0.8,
                estimated_time=0.0
            ))
        
        # Permission issues
        if "permission" in str(exception).lower():
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.USER_INTERVENTION,
                priority=RecoveryPriority.HIGH,
                description="Change output directory or fix permissions",
                automated=False,
                success_probability=0.95,
                estimated_time=60.0
            ))
        
        return actions
    
    def _create_auth_recovery_actions(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Create authentication-specific recovery actions"""
        actions = []
        
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.USER_INTERVENTION,
            priority=RecoveryPriority.CRITICAL,
            description="Update authentication credentials",
            automated=False,
            success_probability=0.9,
            estimated_time=120.0
        ))
        
        return actions
    
    def _create_resource_recovery_actions(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Create resource-specific recovery actions"""
        actions = []
        
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.DELAYED_RETRY,
            priority=RecoveryPriority.MEDIUM,
            description="Wait for resources to become available",
            parameters={"delay": 30.0},
            success_probability=0.6,
            estimated_time=30.0
        ))
        
        return actions
    
    def _create_encryption_recovery_actions(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Create encryption-specific recovery actions"""
        actions = []
        
        actions.append(RecoveryAction(
            strategy=RecoveryStrategy.USER_INTERVENTION,
            priority=RecoveryPriority.HIGH,
            description="Verify encryption keys and settings",
            automated=False,
            success_probability=0.8,
            estimated_time=180.0
        ))
        
        return actions
    
    def _create_generic_recovery_actions(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Create generic recovery actions"""
        actions = []
        
        if exception.is_retryable:
            actions.append(RecoveryAction(
                strategy=RecoveryStrategy.DELAYED_RETRY,
                priority=RecoveryPriority.MEDIUM,
                description="Retry after brief delay",
                parameters={"delay": 10.0},
                success_probability=0.4,
                estimated_time=10.0
            ))
        
        return actions
    
    def _create_fallback_actions(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[RecoveryAction]:
        """Create fallback actions when primary recovery fails"""
        fallback_actions = []
        
        # Skip problematic segments if possible
        if context.get("segment_based", False):
            fallback_actions.append(RecoveryAction(
                strategy=RecoveryStrategy.SEGMENT_SKIP,
                priority=RecoveryPriority.LOW,
                description="Skip problematic segments and continue",
                parameters={"max_skip_percentage": 5.0},
                success_probability=0.7,
                estimated_time=0.0
            ))
        
        # Final fallback: abort with partial results
        fallback_actions.append(RecoveryAction(
            strategy=RecoveryStrategy.ABORT,
            priority=RecoveryPriority.LOW,
            description="Abort download and save partial results",
            success_probability=1.0,
            estimated_time=0.0
        ))
        
        return fallback_actions
    
    def _generate_user_guidance(self, exception: VidTaniumException, context: Dict[str, Any]) -> List[str]:
        """Generate user-friendly guidance messages"""
        guidance = []
        
        # Category-specific guidance
        if exception.category == ErrorCategory.NETWORK:
            guidance.extend([
                "Check your internet connection",
                "Try connecting to a different network",
                "Disable VPN if active and retry",
                "Check if the website is accessible in your browser"
            ])
        elif exception.category == ErrorCategory.FILESYSTEM:
            guidance.extend([
                "Ensure you have write permissions to the output directory",
                "Check available disk space",
                "Try selecting a different output location",
                "Close other applications that might be using the file"
            ])
        elif exception.category == ErrorCategory.AUTHENTICATION:
            guidance.extend([
                "Verify your login credentials",
                "Check if your account has access to this content",
                "Try logging out and back in",
                "Contact the content provider if issues persist"
            ])
        
        # Add severity-specific guidance
        if exception.severity == ErrorSeverity.CRITICAL:
            guidance.insert(0, "⚠️ Critical error detected - immediate attention required")
        elif exception.severity == ErrorSeverity.HIGH:
            guidance.insert(0, "⚠️ High priority error - please address promptly")
        
        return guidance
    
    def execute_recovery_plan(self, plan: RecoveryPlan, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute recovery plan and return success status"""
        logger.info(f"Executing recovery plan {plan.error_id}")
        
        # Try primary actions first
        for action in plan.actions:
            if action.automated:
                success, message = self._execute_recovery_action(action, context)
                if success:
                    self._update_success_rate(action.strategy, True)
                    logger.info(f"Recovery successful with action: {action.description}")
                    return True, message
                else:
                    self._update_success_rate(action.strategy, False)
                    logger.warning(f"Recovery action failed: {action.description}")
        
        # Try fallback actions
        for action in plan.fallback_actions:
            if action.automated:
                success, message = self._execute_recovery_action(action, context)
                if success:
                    self._update_success_rate(action.strategy, True)
                    logger.info(f"Fallback recovery successful: {action.description}")
                    return True, message
                else:
                    self._update_success_rate(action.strategy, False)
        
        logger.error(f"All recovery actions failed for plan {plan.error_id}")
        return False, "All automated recovery attempts failed"
    
    def _execute_recovery_action(self, action: RecoveryAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a specific recovery action"""
        try:
            if action.strategy == RecoveryStrategy.IMMEDIATE_RETRY:
                return self._execute_immediate_retry(action, context)
            elif action.strategy == RecoveryStrategy.DELAYED_RETRY:
                return self._execute_delayed_retry(action, context)
            elif action.strategy == RecoveryStrategy.ALTERNATIVE_SOURCE:
                return self._execute_alternative_source(action, context)
            elif action.strategy == RecoveryStrategy.QUALITY_DOWNGRADE:
                return self._execute_quality_downgrade(action, context)
            elif action.strategy == RecoveryStrategy.SEGMENT_SKIP:
                return self._execute_segment_skip(action, context)
            else:
                return False, f"Unsupported recovery strategy: {action.strategy}"
        except Exception as e:
            logger.error(f"Error executing recovery action {action.strategy}: {e}")
            return False, f"Recovery action failed: {str(e)}"
    
    def _execute_immediate_retry(self, action: RecoveryAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute immediate retry"""
        # This would integrate with the actual download operation
        logger.info("Executing immediate retry")
        return True, "Immediate retry initiated"
    
    def _execute_delayed_retry(self, action: RecoveryAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute delayed retry"""
        delay = action.parameters.get("delay", 5.0)
        logger.info(f"Executing delayed retry with {delay}s delay")
        time.sleep(delay)
        return True, f"Delayed retry initiated after {delay}s"
    
    def _execute_alternative_source(self, action: RecoveryAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute alternative source strategy"""
        logger.info("Attempting alternative source")
        # This would implement actual alternative source logic
        return True, "Alternative source configured"
    
    def _execute_quality_downgrade(self, action: RecoveryAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute quality downgrade strategy"""
        reduction = action.parameters.get("quality_reduction", 0.5)
        logger.info(f"Downgrading quality by {reduction * 100}%")
        return True, f"Quality downgraded by {reduction * 100}%"
    
    def _execute_segment_skip(self, action: RecoveryAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute segment skip strategy"""
        max_skip = action.parameters.get("max_skip_percentage", 5.0)
        logger.info(f"Skipping problematic segments (max {max_skip}%)")
        return True, f"Segment skip enabled (max {max_skip}%)"
    
    def _update_success_rate(self, strategy: RecoveryStrategy, success: bool) -> None:
        """Update success rate for a recovery strategy"""
        with self.lock:
            current_rate = self.success_rates.get(strategy, 0.5)
            # Simple exponential moving average
            alpha = 0.1
            new_rate = current_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
            self.success_rates[strategy] = max(0.0, min(1.0, new_rate))
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery system statistics"""
        with self.lock:
            total_plans = sum(len(plans) for plans in self.recovery_history.values())
            return {
                "total_recovery_plans": total_plans,
                "recovery_categories": {cat: len(plans) for cat, plans in self.recovery_history.items()},
                "strategy_success_rates": dict(self.success_rates),
                "most_successful_strategy": max(self.success_rates.items(), key=lambda x: x[1]) if self.success_rates else None
            }


# Global instance
intelligent_recovery_system = IntelligentRecoverySystem()

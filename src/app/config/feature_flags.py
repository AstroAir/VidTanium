"""
Feature Flag Management System

Provides centralized control over application features and modules,
allowing for runtime enable/disable of functionality.
"""

from typing import Dict, Any, Set, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class FeatureState(Enum):
    """Feature state options"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


@dataclass
class FeatureFlag:
    """Feature flag definition"""
    name: str
    description: str
    state: FeatureState
    default_enabled: bool = False
    requires_restart: bool = False
    dependencies: Set[str] = field(default_factory=set)
    conflicts: Set[str] = field(default_factory=set)
    minimum_version: str = "1.0.0"
    deprecation_version: Optional[str] = None
    removal_version: Optional[str] = None
    validation_function: Optional[Callable[[], bool]] = None


class FeatureFlagManager:
    """Manages application feature flags"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.flags: Dict[str, FeatureFlag] = {}
        self.enabled_features: Set[str] = set()
        self.config = config or {}
        
        # Register default feature flags
        self._register_default_flags()
        
        # Load feature states from configuration
        self._load_feature_states()
    
    def _register_default_flags(self) -> None:
        """Register default application feature flags"""
        
        # Core features
        self.register_flag(FeatureFlag(
            name="adaptive_retry",
            description="Adaptive retry mechanism with intelligent backoff",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="adaptive_timeout",
            description="Adaptive timeout adjustment based on network conditions",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="integrity_verification",
            description="Advanced file integrity verification",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="memory_optimization",
            description="Advanced memory optimization and garbage collection",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="connection_pooling",
            description="Advanced connection pooling and management",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        # UI features
        self.register_flag(FeatureFlag(
            name="enhanced_theme_system",
            description="Enhanced theme system with advanced customization",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="system_tray",
            description="System tray integration",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="notifications",
            description="Desktop notifications",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="dark_mode",
            description="Dark mode theme support",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        # Performance features
        self.register_flag(FeatureFlag(
            name="parallel_downloads",
            description="Parallel segment downloading",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="bandwidth_limiting",
            description="Bandwidth limiting and throttling",
            state=FeatureState.ENABLED,
            default_enabled=False
        ))
        
        self.register_flag(FeatureFlag(
            name="resume_downloads",
            description="Resume interrupted downloads",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        # Experimental features
        self.register_flag(FeatureFlag(
            name="ai_optimization",
            description="AI-powered download optimization",
            state=FeatureState.EXPERIMENTAL,
            default_enabled=False,
            requires_restart=True
        ))
        
        self.register_flag(FeatureFlag(
            name="advanced_analytics",
            description="Advanced download analytics and reporting",
            state=FeatureState.EXPERIMENTAL,
            default_enabled=False
        ))
        
        self.register_flag(FeatureFlag(
            name="cloud_sync",
            description="Cloud synchronization of settings and history",
            state=FeatureState.EXPERIMENTAL,
            default_enabled=False,
            requires_restart=True
        ))
        
        # Debug and development features
        self.register_flag(FeatureFlag(
            name="debug_mode",
            description="Enhanced debug mode with detailed logging",
            state=FeatureState.ENABLED,
            default_enabled=False
        ))
        
        self.register_flag(FeatureFlag(
            name="performance_profiling",
            description="Performance profiling and metrics collection",
            state=FeatureState.ENABLED,
            default_enabled=False
        ))
        
        self.register_flag(FeatureFlag(
            name="mock_downloads",
            description="Mock downloads for testing (development only)",
            state=FeatureState.ENABLED,
            default_enabled=False
        ))
        
        # Security features
        self.register_flag(FeatureFlag(
            name="enhanced_ssl_verification",
            description="Enhanced SSL certificate verification",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        self.register_flag(FeatureFlag(
            name="secure_temp_files",
            description="Secure temporary file handling",
            state=FeatureState.ENABLED,
            default_enabled=True
        ))
        
        # Deprecated features (for backward compatibility)
        self.register_flag(FeatureFlag(
            name="legacy_ui_mode",
            description="Legacy UI compatibility mode",
            state=FeatureState.DEPRECATED,
            default_enabled=False,
            deprecation_version="2.0.0",
            removal_version="3.0.0"
        ))
    
    def register_flag(self, flag: FeatureFlag) -> None:
        """Register a feature flag"""
        self.flags[flag.name] = flag
        
        # Set initial state based on default
        if flag.default_enabled and flag.state != FeatureState.DISABLED:
            self.enabled_features.add(flag.name)
        
        logger.debug(f"Registered feature flag: {flag.name} (state: {flag.state.value})")
    
    def _load_feature_states(self) -> None:
        """Load feature states from configuration"""
        features_config = self.config.get("features", {})
        
        for feature_name, enabled in features_config.items():
            if feature_name in self.flags:
                if enabled:
                    self.enable_feature(feature_name)
                else:
                    self.disable_feature(feature_name)
    
    def is_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        if feature_name not in self.flags:
            logger.warning(f"Unknown feature flag: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        
        # Disabled features are never enabled
        if flag.state == FeatureState.DISABLED:
            return False
        
        # Check if feature is in enabled set
        return feature_name in self.enabled_features
    
    def enable_feature(self, feature_name: str) -> bool:
        """Enable a feature"""
        if feature_name not in self.flags:
            logger.error(f"Cannot enable unknown feature: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        
        # Cannot enable disabled features
        if flag.state == FeatureState.DISABLED:
            logger.warning(f"Cannot enable disabled feature: {feature_name}")
            return False
        
        # Check dependencies
        for dependency in flag.dependencies:
            if not self.is_enabled(dependency):
                logger.error(f"Cannot enable {feature_name}: dependency {dependency} is not enabled")
                return False
        
        # Check conflicts
        for conflict in flag.conflicts:
            if self.is_enabled(conflict):
                logger.error(f"Cannot enable {feature_name}: conflicts with enabled feature {conflict}")
                return False
        
        # Validate feature if validation function exists
        if flag.validation_function and not flag.validation_function():
            logger.error(f"Cannot enable {feature_name}: validation failed")
            return False
        
        self.enabled_features.add(feature_name)
        logger.info(f"Enabled feature: {feature_name}")
        
        if flag.requires_restart:
            logger.warning(f"Feature {feature_name} requires application restart to take effect")
        
        return True
    
    def disable_feature(self, feature_name: str) -> bool:
        """Disable a feature"""
        if feature_name not in self.flags:
            logger.error(f"Cannot disable unknown feature: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        
        # Check if other enabled features depend on this one
        dependent_features = [
            name for name, other_flag in self.flags.items()
            if feature_name in other_flag.dependencies and self.is_enabled(name)
        ]
        
        if dependent_features:
            logger.error(f"Cannot disable {feature_name}: required by {', '.join(dependent_features)}")
            return False
        
        self.enabled_features.discard(feature_name)
        logger.info(f"Disabled feature: {feature_name}")
        
        if flag.requires_restart:
            logger.warning(f"Feature {feature_name} requires application restart to take effect")
        
        return True
    
    def get_feature_info(self, feature_name: str) -> Optional[FeatureFlag]:
        """Get feature flag information"""
        return self.flags.get(feature_name)
    
    def list_features(self, 
                     state_filter: Optional[FeatureState] = None,
                     enabled_only: bool = False) -> List[FeatureFlag]:
        """List features with optional filtering"""
        features = list(self.flags.values())
        
        if state_filter:
            features = [f for f in features if f.state == state_filter]
        
        if enabled_only:
            features = [f for f in features if self.is_enabled(f.name)]
        
        return sorted(features, key=lambda f: f.name)
    
    def get_enabled_features(self) -> Set[str]:
        """Get set of enabled feature names"""
        return self.enabled_features.copy()
    
    def validate_configuration(self) -> List[str]:
        """Validate current feature configuration"""
        issues = []
        
        for feature_name in self.enabled_features:
            if feature_name not in self.flags:
                issues.append(f"Unknown enabled feature: {feature_name}")
                continue
            
            flag = self.flags[feature_name]
            
            # Check if disabled feature is somehow enabled
            if flag.state == FeatureState.DISABLED:
                issues.append(f"Disabled feature is enabled: {feature_name}")
            
            # Check dependencies
            for dependency in flag.dependencies:
                if not self.is_enabled(dependency):
                    issues.append(f"Feature {feature_name} requires {dependency} to be enabled")
            
            # Check conflicts
            for conflict in flag.conflicts:
                if self.is_enabled(conflict):
                    issues.append(f"Feature {feature_name} conflicts with {conflict}")
        
        return issues
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export current feature configuration"""
        return {
            "features": {
                name: self.is_enabled(name)
                for name in self.flags.keys()
            }
        }
    
    def import_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Import feature configuration"""
        errors = []
        features_config = config.get("features", {})
        
        for feature_name, enabled in features_config.items():
            if enabled:
                if not self.enable_feature(feature_name):
                    errors.append(f"Failed to enable feature: {feature_name}")
            else:
                if not self.disable_feature(feature_name):
                    errors.append(f"Failed to disable feature: {feature_name}")
        
        return errors

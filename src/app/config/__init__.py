"""
Enhanced Configuration System for VidTanium

This module provides a comprehensive configuration management system with:
- JSON Schema-based validation
- Multi-source configuration loading (CLI, env vars, files, defaults)
- Configuration presets and templates
- Feature flag management
- Configuration versioning and migration
- Comprehensive validation and error handling
"""

from .schema import ConfigurationSchema, ConfigurationValidator
from .loader import ConfigurationLoader, ConfigurationSource
from .presets import PresetManager, ConfigurationPreset
from .feature_flags import FeatureFlagManager
from .migration import ConfigurationMigrator
from .tools import ConfigurationTools

__all__ = [
    'ConfigurationSchema',
    'ConfigurationValidator', 
    'ConfigurationLoader',
    'ConfigurationSource',
    'PresetManager',
    'ConfigurationPreset',
    'FeatureFlagManager',
    'ConfigurationMigrator',
    'ConfigurationTools'
]

__version__ = '2.0.0'

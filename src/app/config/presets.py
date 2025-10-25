"""
Configuration Presets System

Provides predefined configuration templates for common use cases and
allows users to create and manage custom presets.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from .schema import ConfigurationSchema, ConfigurationValidator


class PresetType(Enum):
    """Types of configuration presets"""
    SYSTEM = "system"        # Built-in presets
    USER = "user"           # User-created presets
    TEMPLATE = "template"   # Template presets for customization


@dataclass
class ConfigurationPreset:
    """Configuration preset definition"""
    name: str
    description: str
    preset_type: PresetType
    config: Dict[str, Any]
    tags: Set[str] = field(default_factory=set)
    author: str = ""
    version: str = "1.0.0"
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    file_path: Optional[Path] = None


class PresetManager:
    """Manages configuration presets and templates"""
    
    def __init__(self, 
                 schema: ConfigurationSchema,
                 presets_dir: Optional[Path] = None,
                 user_presets_dir: Optional[Path] = None) -> None:
        self.schema = schema
        self.validator = ConfigurationValidator(schema)
        
        # Set up directories
        if presets_dir:
            self.presets_dir = presets_dir
        else:
            self.presets_dir = Path(__file__).parent.parent.parent.parent / "config" / "presets"
        
        if user_presets_dir:
            self.user_presets_dir = user_presets_dir
        else:
            self.user_presets_dir = Path.home() / ".vidtanium" / "presets"
        
        # Ensure directories exist
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.user_presets_dir.mkdir(parents=True, exist_ok=True)
        
        # Load presets
        self.presets: Dict[str, ConfigurationPreset] = {}
        self._load_system_presets()
        self._load_user_presets()
    
    def _load_system_presets(self) -> None:
        """Load built-in system presets"""
        
        # High Performance preset
        high_performance = ConfigurationPreset(
            name="high_performance",
            description="Optimized for maximum download speed and performance",
            preset_type=PresetType.SYSTEM,
            config={
                "general": {
                    "output_directory": str(Path.home() / "Downloads"),
                    "auto_cleanup": True,
                    "language": "auto",
                    "theme": "dark",
                    "check_updates": True,
                    "max_recent_files": 20,
                    "temp_directory": "",
                    "cache_directory": "",
                    "config_auto_save": True,
                    "config_backup_count": 3
                },
                "download": {
                    "max_concurrent_tasks": 8,
                    "max_workers_per_task": 20,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "request_timeout": 30,
                    "chunk_size": 65536,
                    "bandwidth_limit": 0
                },
                "network": {
                    "connection_pool_size": 50,
                    "max_connections_per_host": 15,
                    "connection_timeout": 15.0,
                    "read_timeout": 60.0,
                    "dns_cache_timeout": 600,
                    "keep_alive_timeout": 600.0,
                    "proxy": "",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "verify_ssl": True
                },
                "performance": {
                    "memory_limit_mb": 2048,
                    "cpu_usage_limit": 90,
                    "buffer_size_min": 16384,
                    "buffer_size_max": 2097152,
                    "buffer_size_default": 131072,
                    "gc_threshold_mb": 200,
                    "optimization_level": "maximum"
                },
                "logging": {
                    "log_level": "WARNING",
                    "debug_logging": False,
                    "log_to_file": True,
                    "log_to_console": False,
                    "log_file_path": "",
                    "log_rotation_size": "50 MB",
                    "log_retention": "3 days",
                    "log_compression": "zip"
                }
            },
            tags={"performance", "speed", "advanced"},
            author="VidTanium Team"
        )
        
        # Low Resource preset
        low_resource = ConfigurationPreset(
            name="low_resource",
            description="Optimized for systems with limited resources",
            preset_type=PresetType.SYSTEM,
            config={
                "general": {
                    "output_directory": str(Path.home() / "Downloads"),
                    "auto_cleanup": True,
                    "language": "auto",
                    "theme": "light",
                    "check_updates": False,
                    "max_recent_files": 5,
                    "temp_directory": "",
                    "cache_directory": "",
                    "config_auto_save": True,
                    "config_backup_count": 2
                },
                "download": {
                    "max_concurrent_tasks": 1,
                    "max_workers_per_task": 3,
                    "max_retries": 5,
                    "retry_delay": 3.0,
                    "request_timeout": 120,
                    "chunk_size": 4096,
                    "bandwidth_limit": 0
                },
                "network": {
                    "connection_pool_size": 5,
                    "max_connections_per_host": 2,
                    "connection_timeout": 45.0,
                    "read_timeout": 180.0,
                    "dns_cache_timeout": 60,
                    "keep_alive_timeout": 120.0,
                    "proxy": "",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "verify_ssl": True
                },
                "performance": {
                    "memory_limit_mb": 256,
                    "cpu_usage_limit": 50,
                    "buffer_size_min": 4096,
                    "buffer_size_max": 65536,
                    "buffer_size_default": 16384,
                    "gc_threshold_mb": 50,
                    "optimization_level": "low"
                },
                "logging": {
                    "log_level": "ERROR",
                    "debug_logging": False,
                    "log_to_file": True,
                    "log_to_console": False,
                    "log_file_path": "",
                    "log_rotation_size": "5 MB",
                    "log_retention": "1 day",
                    "log_compression": "zip"
                }
            },
            tags={"resource-efficient", "minimal", "basic"},
            author="VidTanium Team"
        )
        
        # Development preset
        development = ConfigurationPreset(
            name="development",
            description="Optimized for development and debugging",
            preset_type=PresetType.SYSTEM,
            config={
                "general": {
                    "output_directory": str(Path.home() / "Downloads" / "VidTanium_Dev"),
                    "auto_cleanup": False,
                    "language": "auto",
                    "theme": "dark",
                    "check_updates": False,
                    "max_recent_files": 50,
                    "temp_directory": "",
                    "cache_directory": "",
                    "config_auto_save": True,
                    "config_backup_count": 10
                },
                "download": {
                    "max_concurrent_tasks": 2,
                    "max_workers_per_task": 5,
                    "max_retries": 2,
                    "retry_delay": 1.0,
                    "request_timeout": 60,
                    "chunk_size": 8192,
                    "bandwidth_limit": 0
                },
                "network": {
                    "connection_pool_size": 10,
                    "max_connections_per_host": 4,
                    "connection_timeout": 30.0,
                    "read_timeout": 120.0,
                    "dns_cache_timeout": 300,
                    "keep_alive_timeout": 300.0,
                    "proxy": "",
                    "user_agent": "VidTanium-Dev/2.0.0",
                    "verify_ssl": True
                },
                "performance": {
                    "memory_limit_mb": 512,
                    "cpu_usage_limit": 70,
                    "buffer_size_min": 8192,
                    "buffer_size_max": 262144,
                    "buffer_size_default": 32768,
                    "gc_threshold_mb": 100,
                    "optimization_level": "balanced"
                },
                "logging": {
                    "log_level": "DEBUG",
                    "debug_logging": True,
                    "log_to_file": True,
                    "log_to_console": True,
                    "log_file_path": "",
                    "log_rotation_size": "100 MB",
                    "log_retention": "30 days",
                    "log_compression": "none"
                }
            },
            tags={"development", "debug", "testing"},
            author="VidTanium Team"
        )
        
        # Production preset
        production = ConfigurationPreset(
            name="production",
            description="Stable configuration for production use",
            preset_type=PresetType.SYSTEM,
            config={
                "general": {
                    "output_directory": str(Path.home() / "Downloads"),
                    "auto_cleanup": True,
                    "language": "auto",
                    "theme": "system",
                    "check_updates": True,
                    "max_recent_files": 10,
                    "temp_directory": "",
                    "cache_directory": "",
                    "config_auto_save": True,
                    "config_backup_count": 5
                },
                "download": {
                    "max_concurrent_tasks": 3,
                    "max_workers_per_task": 10,
                    "max_retries": 5,
                    "retry_delay": 2.0,
                    "request_timeout": 60,
                    "chunk_size": 8192,
                    "bandwidth_limit": 0
                },
                "network": {
                    "connection_pool_size": 20,
                    "max_connections_per_host": 8,
                    "connection_timeout": 30.0,
                    "read_timeout": 120.0,
                    "dns_cache_timeout": 300,
                    "keep_alive_timeout": 300.0,
                    "proxy": "",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "verify_ssl": True
                },
                "performance": {
                    "memory_limit_mb": 1024,
                    "cpu_usage_limit": 80,
                    "buffer_size_min": 8192,
                    "buffer_size_max": 1048576,
                    "buffer_size_default": 65536,
                    "gc_threshold_mb": 100,
                    "optimization_level": "balanced"
                },
                "logging": {
                    "log_level": "INFO",
                    "debug_logging": False,
                    "log_to_file": True,
                    "log_to_console": True,
                    "log_file_path": "",
                    "log_rotation_size": "10 MB",
                    "log_retention": "7 days",
                    "log_compression": "zip"
                }
            },
            tags={"production", "stable", "default"},
            author="VidTanium Team"
        )
        
        # Register system presets
        self.presets[high_performance.name] = high_performance
        self.presets[low_resource.name] = low_resource
        self.presets[development.name] = development
        self.presets[production.name] = production
        
        logger.info(f"Loaded {len([p for p in self.presets.values() if p.preset_type == PresetType.SYSTEM])} system presets")
    
    def _load_user_presets(self) -> None:
        """Load user-created presets from files"""
        if not self.user_presets_dir.exists():
            return
        
        preset_files = list(self.user_presets_dir.glob("*.json")) + list(self.user_presets_dir.glob("*.yaml"))
        
        for preset_file in preset_files:
            try:
                preset = self._load_preset_file(preset_file)
                if preset:
                    self.presets[preset.name] = preset
                    logger.debug(f"Loaded user preset: {preset.name}")
            except Exception as e:
                logger.error(f"Failed to load preset from {preset_file}: {e}")
        
        user_preset_count = len([p for p in self.presets.values() if p.preset_type == PresetType.USER])
        if user_preset_count > 0:
            logger.info(f"Loaded {user_preset_count} user presets")
    
    def _load_preset_file(self, file_path: Path) -> Optional[ConfigurationPreset]:
        """Load preset from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
            
            preset = ConfigurationPreset(
                name=data.get("name", file_path.stem),
                description=data.get("description", ""),
                preset_type=PresetType(data.get("preset_type", "user")),
                config=data.get("config", {}),
                tags=set(data.get("tags", [])),
                author=data.get("author", ""),
                version=data.get("version", "1.0.0"),
                created_at=data.get("created_at"),
                modified_at=data.get("modified_at"),
                file_path=file_path
            )
            
            return preset
            
        except Exception as e:
            logger.error(f"Failed to load preset from {file_path}: {e}")
            return None
    
    def get_preset(self, name: str) -> Optional[ConfigurationPreset]:
        """Get preset by name"""
        return self.presets.get(name)
    
    def list_presets(self, preset_type: Optional[PresetType] = None, tags: Optional[Set[str]] = None) -> List[ConfigurationPreset]:
        """List presets with optional filtering"""
        presets = list(self.presets.values())
        
        if preset_type:
            presets = [p for p in presets if p.preset_type == preset_type]
        
        if tags:
            presets = [p for p in presets if tags.intersection(p.tags)]
        
        return sorted(presets, key=lambda p: (p.preset_type.value, p.name))
    
    def apply_preset(self, preset_name: str, base_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply preset to base configuration"""
        preset = self.get_preset(preset_name)
        if not preset:
            raise ValueError(f"Preset '{preset_name}' not found")
        
        if base_config:
            # Merge preset with base configuration
            return self._merge_configs(base_config, preset.config)
        else:
            return preset.config.copy()
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result

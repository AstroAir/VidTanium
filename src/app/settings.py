import json
import os
import argparse
from pathlib import Path
import copy
from loguru import logger
from typing import Any, Dict, Optional, Union, List, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import new configuration system components
try:
    from .config import (
        ConfigurationSchema, ConfigurationLoader, ConfigurationValidator,
        PresetManager, FeatureFlagManager, ConfigurationMigrator, ConfigurationTools
    )
    from .config.schema import ValidationLevel
    from .config.loader import LoadResult
    NEW_CONFIG_SYSTEM_AVAILABLE = True
except ImportError:
    logger.warning("New configuration system not available, using legacy system")
    NEW_CONFIG_SYSTEM_AVAILABLE = False


class SettingType(Enum):
    """Types of settings for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PATH = "path"
    LIST = "list"


@dataclass
class SettingDefinition:
    """Definition of a setting with validation rules"""
    key: str
    default_value: Any
    setting_type: SettingType
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None


class ConfigurationUtilities:
    """Unified configuration utilities to reduce code duplication"""

    @staticmethod
    def validate_setting(value: Any, definition: SettingDefinition) -> tuple[bool, Any]:
        """Validate a setting value against its definition"""
        try:
            # Type validation
            validated_value: Any
            if definition.setting_type == SettingType.STRING:
                validated_value = str(value)
            elif definition.setting_type == SettingType.INTEGER:
                validated_value = int(value)
                if definition.min_value is not None and validated_value < definition.min_value:
                    return False, definition.default_value
                if definition.max_value is not None and validated_value > definition.max_value:
                    return False, definition.default_value
            elif definition.setting_type == SettingType.FLOAT:
                validated_value = float(value)
                if definition.min_value is not None and validated_value < definition.min_value:
                    return False, definition.default_value
                if definition.max_value is not None and validated_value > definition.max_value:
                    return False, definition.default_value
            elif definition.setting_type == SettingType.BOOLEAN:
                validated_value = bool(value)
            elif definition.setting_type == SettingType.PATH:
                validated_value = str(value)
                # Basic path validation
                if validated_value and not Path(validated_value).is_absolute():
                    validated_value = str(Path(validated_value).resolve())
            elif definition.setting_type == SettingType.LIST:
                validated_value = list(value) if not isinstance(value, list) else value

            # Custom validator
            if definition.validator and not definition.validator(validated_value):
                return False, definition.default_value

            return True, validated_value

        except (ValueError, TypeError) as e:
            logger.warning(f"Setting validation failed for {definition.key}: {e}")
            return False, definition.default_value

    @staticmethod
    def safe_get_nested(data: Dict, path: str, default: Any = None) -> Any:
        """Safely get nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @staticmethod
    def safe_set_nested(data: Dict, path: str, value: Any) -> None:
        """Safely set nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    @staticmethod
    def merge_settings_efficiently(base: Dict, updates: Dict) -> Dict:
        """Efficiently merge settings dictionaries"""
        result = base.copy()

        for section, section_data in updates.items():
            if section not in result:
                # Handle both dict and non-dict values
                result[section] = section_data.copy() if isinstance(section_data, dict) else section_data
            else:
                # Only call update() if both are dictionaries
                if isinstance(result[section], dict) and isinstance(section_data, dict):
                    result[section].update(section_data)
                else:
                    # For non-dict values (like lists), just replace
                    result[section] = section_data

        return result


class Settings:
    """Application settings management class"""

    # Type annotations for configuration system components
    schema: Optional['ConfigurationSchema']
    loader: Optional['ConfigurationLoader']
    preset_manager: Optional['PresetManager']
    feature_manager: Optional['FeatureFlagManager']
    migrator: Optional['ConfigurationMigrator']
    tools: Optional['ConfigurationTools']
    cli_args: Optional[argparse.Namespace]

    def __init__(self, config_dir=None, cli_args=None, use_new_system=None) -> None:
        """Initialize settings manager

        Args:
            config_dir: Configuration directory path
            cli_args: Command-line arguments
            use_new_system: Force use of new/old configuration system (None for auto-detect)
        """
        # Determine configuration directory
        if config_dir is None:
            self.config_dir = Path.home() / ".vidtanium"  # Updated directory name
        else:
            self.config_dir = Path(config_dir)

        # Ensure configuration directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Configuration file paths
        self.config_file = self.config_dir / "config.json"  # Updated filename
        self.presets_dir = self.config_dir / "presets"
        self.presets_dir.mkdir(exist_ok=True)

        # Determine which configuration system to use
        if use_new_system is None:
            self.use_new_system = NEW_CONFIG_SYSTEM_AVAILABLE
        else:
            self.use_new_system = use_new_system and NEW_CONFIG_SYSTEM_AVAILABLE

        # Initialize configuration system components
        if self.use_new_system:
            self._init_new_config_system(cli_args)
        else:
            self._init_legacy_config_system()

        # Default settings
        self.default_settings = {
            "general": {
                "output_directory": str(Path.home() / "Downloads"),
                "auto_cleanup": True,
                "language": "auto",
                "theme": "system",
                "check_updates": True,
                "max_recent_files": 10
            },
            "download": {
                "max_concurrent_tasks": 3,
                "max_workers_per_task": 10,
                "max_retries": 5,
                "retry_delay": 2,
                "request_timeout": 60,
                "chunk_size": 8192,
                "bandwidth_limit": 0
            },
            "advanced": {
                "proxy": "",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "verify_ssl": True,
                "ffmpeg_path": "",
                "keep_temp_files": False,
                "debug_logging": False
            },
            "ui": {
                "show_detailed_progress": True,
                "minimize_to_tray": False,
                "show_notifications": True,
                "confirm_on_exit": True,
                "window_geometry": "",
                "window_state": ""
            },
            "recent_tasks": []
        }

        # Load settings
        self.settings = self.load_settings()

        logger.info(f"Settings initialized with config directory: {self.config_dir}")
        if self.use_new_system:
            logger.info("Using enhanced configuration system")
        else:
            logger.info("Using legacy configuration system")

    def _init_new_config_system(self, cli_args=None) -> None:
        """Initialize the new enhanced configuration system"""
        try:
            # Create configuration schema
            self.schema = ConfigurationSchema()

            # Create configuration loader
            self.loader = ConfigurationLoader(self.schema, config_dir=self.config_dir)

            # Create preset manager
            self.preset_manager = PresetManager(self.schema, user_presets_dir=self.presets_dir)

            # Create feature flag manager
            self.feature_manager = FeatureFlagManager()

            # Create configuration migrator
            self.migrator = ConfigurationMigrator()

            # Create configuration tools
            self.tools = ConfigurationTools(self.schema, self.preset_manager, self.feature_manager)

            # Store CLI args for loading
            self.cli_args = cli_args

            logger.info("Enhanced configuration system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize enhanced configuration system: {e}")
            logger.warning("Falling back to legacy configuration system")
            self.use_new_system = False
            self._init_legacy_config_system()

    def _init_legacy_config_system(self) -> None:
        """Initialize the legacy configuration system"""
        # Set up legacy system attributes (reset to None for legacy mode)
        if hasattr(self, 'schema'):
            self.schema = None
        if hasattr(self, 'loader'):
            self.loader = None
        if hasattr(self, 'preset_manager'):
            self.preset_manager = None
        if hasattr(self, 'feature_manager'):
            self.feature_manager = None
        if hasattr(self, 'migrator'):
            self.migrator = None
        if hasattr(self, 'tools'):
            self.tools = None
        if hasattr(self, 'cli_args'):
            self.cli_args = None

        logger.info("Legacy configuration system initialized")

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from configuration file using appropriate system"""
        if self.use_new_system and self.loader:
            return self._load_settings_new_system()
        else:
            return self._load_settings_legacy()

    def _load_settings_new_system(self) -> Dict[str, Any]:
        """Load settings using the new configuration system"""
        try:
            # Load configuration from all sources
            if self.loader is None:
                logger.error("Configuration loader not initialized")
                return {}

            load_result = self.loader.load_configuration(cli_args=self.cli_args)

            if not load_result.success:
                logger.error(f"Configuration loading failed: {'; '.join(load_result.errors)}")
                if load_result.warnings:
                    logger.warning(f"Configuration warnings: {'; '.join(load_result.warnings)}")

                # Fall back to default configuration
                logger.warning("Using default configuration due to loading errors")
                return self.loader._get_default_config()

            # Check if migration is needed
            if self.migrator and self.migrator.needs_migration(load_result.config):
                logger.info("Configuration migration required")
                migration_result = self.migrator.migrate_configuration(
                    load_result.config,
                    self.config_file if self.config_file.exists() else None
                )

                if migration_result.success:
                    logger.info(f"Configuration migrated successfully from {migration_result.from_version} to {migration_result.to_version}")
                    if migration_result.changes_made:
                        logger.info(f"Migration changes: {'; '.join(migration_result.changes_made)}")

                    # Save migrated configuration
                    if migration_result.migrated_config:
                        self.save_settings(migration_result.migrated_config)
                        load_result.config = migration_result.migrated_config
                else:
                    logger.error(f"Configuration migration failed: {'; '.join(migration_result.errors)}")

            # Update feature manager with loaded configuration
            if self.feature_manager:
                self.feature_manager.config = load_result.config
                self.feature_manager._load_feature_states()

            logger.info(f"Configuration loaded successfully from sources: {[s.value for s in load_result.sources_used]}")
            if load_result.files_loaded:
                logger.info(f"Configuration files loaded: {[str(f) for f in load_result.files_loaded]}")

            return load_result.config

        except Exception as e:
            logger.error(f"Error in new configuration system: {e}", exc_info=True)
            logger.warning("Falling back to legacy configuration loading")
            return self._load_settings_legacy()

    def _load_settings_legacy(self) -> Dict[str, Any]:
        """Load settings using the legacy system"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Merge loaded settings with default settings using optimized utility
                merged_settings = ConfigurationUtilities.merge_settings_efficiently(
                    self.default_settings, settings)
                logger.info(f"Settings loaded from {self.config_file}")
                return merged_settings
            except Exception as e:
                logger.error(f"Error loading settings: {e}", exc_info=True)
                logger.warning("Using default settings due to load failure")
                return self.default_settings.copy()
        else:
            # First run, create default settings
            logger.info("No settings file found, creating default settings")
            self.save_settings(self.default_settings)
            return self.default_settings.copy()

    def save_settings(self, settings: Optional[Dict] = None) -> bool:
        """Save settings to configuration file with optimized I/O

        Args:
            settings: Settings dictionary to save, uses instance settings if None

        Returns:
            bool: True if save was successful, False otherwise
        """
        if settings is None:
            settings = self.settings

        # Create backup before saving
        backup_created = self._create_settings_backup()

        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first for atomic operation
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2, sort_keys=True)

            # Atomic rename
            temp_file.replace(self.config_file)
            logger.info(f"Settings saved to {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            # Restore backup if available
            if backup_created:
                self._restore_settings_backup()
            return False
        finally:
            # Clean up temporary file if it exists
            temp_file = self.config_file.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass

    def _create_settings_backup(self) -> bool:
        """Create backup of current settings file"""
        if not self.config_file.exists():
            return False

        try:
            backup_file = self.config_file.with_suffix('.bak')
            backup_file.write_bytes(self.config_file.read_bytes())
            return True
        except Exception as e:
            logger.warning(f"Failed to create settings backup: {e}")
            return False

    def _restore_settings_backup(self) -> bool:
        """Restore settings from backup"""
        backup_file = self.config_file.with_suffix('.bak')
        if not backup_file.exists():
            return False

        try:
            self.config_file.write_bytes(backup_file.read_bytes())
            logger.info("Settings restored from backup")
            return True
        except Exception as e:
            logger.error(f"Failed to restore settings backup: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values

        Returns:
            bool: True if reset was successful, False otherwise
        """
        logger.info("Resetting all settings to default values")
        self.settings = copy.deepcopy(self.default_settings)
        return self.save_settings()

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get setting value with optimized lookup

        Args:
            section: Settings section name
            key: Setting key name
            default: Default value to return if setting not found

        Returns:
            Setting value or default if not found
        """
        # Use efficient nested lookup
        path = f"{section}.{key}"
        value = ConfigurationUtilities.safe_get_nested(self.settings, path)

        if value is not None:
            return value

        # Fallback to default settings
        default_value = ConfigurationUtilities.safe_get_nested(self.default_settings, path)
        if default_value is not None:
            logger.debug(f"Using default value for {section}.{key}")
            return default_value

        logger.debug(f"Setting {section}.{key} not found, using provided default")
        return default

    def set(self, section: str, key: str, value: Any) -> None:
        """Set setting value with optimized nested assignment

        Args:
            section: Settings section name
            key: Setting key name
            value: Value to set
        """
        path = f"{section}.{key}"
        ConfigurationUtilities.safe_set_nested(self.settings, path, value)
        logger.debug(f"Setting {section}.{key} = {value}")

    # New enhanced configuration methods
    def apply_preset(self, preset_name: str) -> bool:
        """Apply a configuration preset"""
        if not self.use_new_system or not self.preset_manager:
            logger.warning("Presets are only available with the enhanced configuration system")
            return False

        try:
            preset_config = self.preset_manager.apply_preset(preset_name, self.settings)
            self.settings = preset_config
            self.save_settings(self.settings)
            logger.info(f"Applied preset: {preset_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply preset {preset_name}: {e}")
            return False

    def list_presets(self) -> List[str]:
        """List available configuration presets"""
        if not self.use_new_system or not self.preset_manager:
            return []

        presets = self.preset_manager.list_presets()
        return [preset.name for preset in presets]

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        if not self.use_new_system or not self.feature_manager:
            # For legacy system, check some basic features
            if feature_name == "debug_mode":
                return bool(self.get("advanced", "debug_logging", False))
            return True  # Assume features are enabled in legacy mode

        return self.feature_manager.is_enabled(feature_name)

    def enable_feature(self, feature_name: str) -> bool:
        """Enable a feature"""
        if not self.use_new_system or not self.feature_manager:
            logger.warning("Feature flags are only available with the enhanced configuration system")
            return False

        return self.feature_manager.enable_feature(feature_name)

    def disable_feature(self, feature_name: str) -> bool:
        """Disable a feature"""
        if not self.use_new_system or not self.feature_manager:
            logger.warning("Feature flags are only available with the enhanced configuration system")
            return False

        return self.feature_manager.disable_feature(feature_name)

    def validate_configuration(self) -> Tuple[bool, List[str], List[str]]:
        """Validate current configuration"""
        if not self.use_new_system or not self.tools:
            # Basic validation for legacy system
            return True, [], []

        return self.tools.validate_configuration(self.settings)

    def export_configuration(self, output_path: Path, format: str = "json") -> bool:
        """Export configuration to file"""
        if not self.use_new_system or not self.tools:
            # Legacy export
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                logger.error(f"Failed to export configuration: {e}")
                return False

        return self.tools.export_configuration(self.settings, output_path, format)

    def create_backup(self, description: str = "") -> bool:
        """Create a configuration backup"""
        if not self.use_new_system or not self.tools:
            # Legacy backup
            try:
                backup_dir = self.config_dir / "backups"
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"settings_backup_{timestamp}.json"

                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=2, ensure_ascii=False)

                logger.info(f"Configuration backup created: {backup_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to create backup: {e}")
                return False

        backup_dir = self.config_dir / "backups"
        backup_info = self.tools.create_backup(self.settings, backup_dir, description)
        return backup_info is not None

    def add_recent_task(self, task_info) -> None:
        """Add recent task

        Args:
            task_info (dict): Task information to add
        """
        # Get recent tasks list
        recent_tasks = self.settings.get("recent_tasks", [])

        # Remove tasks with the same ID
        task_id = task_info.get("task_id")
        recent_tasks = [
            task for task in recent_tasks if task.get("task_id") != task_id]

        # Add to the beginning of the list
        logger.debug(
            f"Adding task to recent list: {task_info.get('name', task_id)}")
        recent_tasks.insert(0, task_info)

        # Limit list length
        max_recent = self.get("general", "max_recent_files", 10)
        if len(recent_tasks) > max_recent:
            logger.debug(f"Trimming recent tasks list to {max_recent} items")
            recent_tasks = recent_tasks[:max_recent]

        # Update settings
        self.settings["recent_tasks"] = recent_tasks

    def get_recent_tasks(self) -> None:
        """Get list of recent tasks

        Returns:
            list: List of recent tasks
        """
        tasks = self.settings.get("recent_tasks", [])
        logger.debug(f"Retrieved {len(tasks)} recent tasks")
        return tasks

    def save_preset(self, name, preset_data) -> None:
        """Save preset

        Args:
            name (str): Preset name
            preset_data (dict): Preset data to save

        Returns:
            bool: True if save was successful, False otherwise
        """
        preset_file = self.presets_dir / f"{name}.json"

        try:
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Preset saved: {name}")
            return True
        except Exception as e:
            logger.error(f"Error saving preset {name}: {e}", exc_info=True)
            return False

    def load_preset(self, name) -> None:
        """Load preset

        Args:
            name (str): Preset name

        Returns:
            dict: Preset data or None if loading failed
        """
        preset_file = self.presets_dir / f"{name}.json"

        if not preset_file.exists():
            logger.warning(f"Preset does not exist: {name}")
            return None

        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
            logger.info(f"Preset loaded: {name}")
            return preset_data
        except Exception as e:
            logger.error(f"Error loading preset {name}: {e}", exc_info=True)
            return None

    def get_presets(self) -> None:
        """Get all presets

        Returns:
            list: List of preset names
        """
        presets = []

        for preset_file in self.presets_dir.glob("*.json"):
            presets.append(preset_file.stem)

        logger.debug(
            f"Found {len(presets)} presets: {', '.join(presets) if presets else 'none'}")
        return presets

    def delete_preset(self, name) -> None:
        """Delete preset

        Args:
            name (str): Preset name

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        preset_file = self.presets_dir / f"{name}.json"

        if not preset_file.exists():
            logger.warning(f"Preset does not exist: {name}")
            return False

        try:
            os.remove(preset_file)
            logger.info(f"Preset deleted: {name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting preset {name}: {e}", exc_info=True)
            return False

    def get_with_validation(self, section: str, key: str, setting_type: SettingType = SettingType.STRING, default: Any = None) -> Any:
        """Get setting value with type validation and automatic correction

        Args:
            section: Settings section name
            key: Setting key name
            setting_type: Expected type of the setting
            default: Default value if not found or invalid

        Returns:
            Validated setting value
        """
        raw_value = self.get(section, key, default)

        # Create a temporary definition for validation
        definition = SettingDefinition(
            key=f"{section}.{key}",
            default_value=default or self.get_default_for_type(setting_type),
            setting_type=setting_type
        )

        is_valid, validated_value = ConfigurationUtilities.validate_setting(raw_value, definition)

        if not is_valid:
            logger.warning(f"Invalid value for {section}.{key}, using default: {validated_value}")
            # Auto-correct the invalid value
            self.set(section, key, validated_value)

        return validated_value

    def get_default_for_type(self, setting_type: SettingType) -> Any:
        """Get appropriate default value for a setting type"""
        defaults = {
            SettingType.STRING: "",
            SettingType.INTEGER: 0,
            SettingType.FLOAT: 0.0,
            SettingType.BOOLEAN: False,
            SettingType.PATH: "",
            SettingType.LIST: []
        }
        return defaults.get(setting_type, None)

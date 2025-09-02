import json
import os
from pathlib import Path
import copy
from loguru import logger
from typing import Any, Dict, Optional, Union, List, Callable
from dataclasses import dataclass
from enum import Enum


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
                result[section] = section_data.copy()
            else:
                result[section].update(section_data)

        return result


class Settings:
    """Application settings management class"""

    def __init__(self, config_dir=None):
        """Initialize settings manager"""
        # Determine configuration directory
        if config_dir is None:
            self.config_dir = Path.home() / ".encrypted_video_downloader"
        else:
            self.config_dir = Path(config_dir)

        # Ensure configuration directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Configuration file paths
        self.config_file = self.config_dir / "settings.json"
        self.presets_dir = self.config_dir / "presets"
        self.presets_dir.mkdir(exist_ok=True)

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

    def load_settings(self):
        """Load settings from configuration file"""
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

    def reset_to_defaults(self):
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

    def add_recent_task(self, task_info):
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

    def get_recent_tasks(self):
        """Get list of recent tasks

        Returns:
            list: List of recent tasks
        """
        tasks = self.settings.get("recent_tasks", [])
        logger.debug(f"Retrieved {len(tasks)} recent tasks")
        return tasks

    def save_preset(self, name, preset_data):
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

    def load_preset(self, name):
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

    def get_presets(self):
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

    def delete_preset(self, name):
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

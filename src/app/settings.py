import json
import os
from pathlib import Path
import copy
from loguru import logger


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

                # Merge loaded settings with default settings
                merged_settings = self.default_settings.copy()
                self._deep_update(merged_settings, settings)
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

    def save_settings(self, settings=None):
        """Save settings to configuration file

        Args:
            settings: Settings dictionary to save, uses instance settings if None

        Returns:
            bool: True if save was successful, False otherwise
        """
        if settings is None:
            settings = self.settings

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            logger.info(f"Settings saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            return False

    def reset_to_defaults(self):
        """Reset all settings to default values

        Returns:
            bool: True if reset was successful, False otherwise
        """
        logger.info("Resetting all settings to default values")
        self.settings = copy.deepcopy(self.default_settings)
        return self.save_settings()

    def get(self, section, key, default=None):
        """Get setting value

        Args:
            section (str): Settings section name
            key (str): Setting key name
            default: Default value to return if setting not found

        Returns:
            Setting value or default if not found
        """
        if section in self.settings and key in self.settings[section]:
            return self.settings[section][key]
        elif section in self.default_settings and key in self.default_settings[section]:
            logger.debug(f"Using default value for {section}.{key}")
            return self.default_settings[section][key]
        else:
            logger.debug(
                f"Setting {section}.{key} not found, using provided default")
            return default

    def set(self, section, key, value):
        """Set setting value

        Args:
            section (str): Settings section name
            key (str): Setting key name
            value: Value to set
        """
        if section not in self.settings:
            logger.debug(f"Creating new settings section: {section}")
            self.settings[section] = {}

        logger.debug(f"Setting {section}.{key} = {value}")
        self.settings[section][key] = value

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

    def _deep_update(self, d, u):
        """Deep update dictionary

        Args:
            d (dict): Target dictionary
            u (dict): Source dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v

import pytest
import json
import tempfile
import os
import copy
from unittest.mock import patch, Mock, mock_open
from pathlib import Path

from src.app.settings import Settings


class TestSettings:
    """Test suite for Settings class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for config
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "test_config"

    def teardown_method(self):
        """Clean up after tests."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization_default_config_dir(self):
        """Test Settings initialization with default config directory."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path(self.temp_dir)
            
            settings = Settings()
            
            expected_dir = Path(self.temp_dir) / ".encrypted_video_downloader"
            assert settings.config_dir == expected_dir
            assert settings.config_file == expected_dir / "settings.json"
            assert settings.presets_dir == expected_dir / "presets"

    def test_initialization_custom_config_dir(self):
        """Test Settings initialization with custom config directory."""
        settings = Settings(self.config_dir)
        
        assert settings.config_dir == self.config_dir
        assert settings.config_file == self.config_dir / "settings.json"
        assert settings.presets_dir == self.config_dir / "presets"

    def test_initialization_creates_directories(self):
        """Test that initialization creates necessary directories."""
        # Directory shouldn't exist initially
        assert not self.config_dir.exists()
        
        settings = Settings(self.config_dir)
        
        # Directories should be created
        assert self.config_dir.exists()
        assert settings.presets_dir.exists()

    def test_default_settings_structure(self):
        """Test that default settings have correct structure."""
        settings = Settings(self.config_dir)
        
        # Check main sections exist
        assert "general" in settings.default_settings
        assert "download" in settings.default_settings
        assert "advanced" in settings.default_settings
        assert "ui" in settings.default_settings
        
        # Check some key settings
        general = settings.default_settings["general"]
        assert "output_directory" in general
        assert "auto_cleanup" in general
        assert "language" in general
        assert "theme" in general
        
        download = settings.default_settings["download"]
        assert "max_concurrent_tasks" in download
        assert "max_workers_per_task" in download
        assert "max_retries" in download

    def test_load_settings_first_run(self):
        """Test loading settings on first run (no config file)."""
        settings = Settings(self.config_dir)
        
        # Should use default settings
        assert settings.settings == settings.default_settings
        
        # Should create config file
        assert settings.config_file.exists()

    def test_load_settings_existing_file(self):
        """Test loading settings from existing file."""
        # Create config file with custom settings
        custom_settings = {
            "general": {
                "output_directory": "/custom/downloads",
                "language": "en"
            },
            "download": {
                "max_concurrent_tasks": 5
            }
        }
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_dir / "settings.json", 'w') as f:
            json.dump(custom_settings, f)
        
        settings = Settings(self.config_dir)
        
        # Should merge with defaults
        assert settings.get("general", "output_directory") == "/custom/downloads"
        assert settings.get("general", "language") == "en"
        assert settings.get("download", "max_concurrent_tasks") == 5
        
        # Should still have default values for missing keys
        assert settings.get("general", "auto_cleanup") is True
        assert settings.get("download", "max_workers_per_task") == 10

    def test_load_settings_corrupted_file(self):
        """Test loading settings from corrupted file."""
        # Create corrupted config file
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_dir / "settings.json", 'w') as f:
            f.write("invalid json content")
        
        settings = Settings(self.config_dir)
        
        # Should fall back to default settings
        assert settings.settings == settings.default_settings

    def test_save_settings_success(self):
        """Test successful settings save."""
        settings = Settings(self.config_dir)
        
        # Modify some settings
        settings.set("general", "language", "zh_CN")
        settings.set("download", "max_concurrent_tasks", 8)
        
        result = settings.save_settings()
        
        assert result is True
        assert settings.config_file.exists()
        
        # Verify saved content
        with open(settings.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["general"]["language"] == "zh_CN"
        assert saved_data["download"]["max_concurrent_tasks"] == 8

    def test_save_settings_with_custom_data(self):
        """Test saving custom settings data."""
        settings = Settings(self.config_dir)
        
        custom_data = {
            "test_section": {
                "test_key": "test_value"
            }
        }
        
        result = settings.save_settings(custom_data)
        
        assert result is True
        
        # Verify saved content
        with open(settings.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == custom_data

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_settings_permission_error(self, mock_open):
        """Test save settings with permission error."""
        settings = Settings(self.config_dir)
        
        result = settings.save_settings()
        
        assert result is False

    def test_reset_to_defaults(self):
        """Test resetting settings to defaults."""
        settings = Settings(self.config_dir)
        
        # Modify some settings
        settings.set("general", "language", "custom")
        settings.set("download", "max_concurrent_tasks", 99)
        
        # Reset to defaults
        result = settings.reset_to_defaults()
        
        assert result is True
        assert settings.settings == settings.default_settings
        
        # Verify file was updated
        with open(settings.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == settings.default_settings

    def test_get_existing_setting(self):
        """Test getting existing setting value."""
        settings = Settings(self.config_dir)
        
        # Get from current settings
        value = settings.get("general", "auto_cleanup")
        assert value is True
        
        # Get from download section
        value = settings.get("download", "max_concurrent_tasks")
        assert value == 3

    def test_get_setting_from_defaults(self):
        """Test getting setting value from defaults when not in current settings."""
        settings = Settings(self.config_dir)
        
        # Remove a setting from current settings
        del settings.settings["general"]["auto_cleanup"]
        
        # Should get from defaults
        value = settings.get("general", "auto_cleanup")
        assert value is True

    def test_get_nonexistent_setting_with_default(self):
        """Test getting nonexistent setting with provided default."""
        settings = Settings(self.config_dir)
        
        value = settings.get("nonexistent", "key", "default_value")
        assert value == "default_value"

    def test_get_nonexistent_setting_without_default(self):
        """Test getting nonexistent setting without provided default."""
        settings = Settings(self.config_dir)
        
        value = settings.get("nonexistent", "key")
        assert value is None

    def test_set_existing_section(self):
        """Test setting value in existing section."""
        settings = Settings(self.config_dir)
        
        settings.set("general", "language", "fr")
        
        assert settings.settings["general"]["language"] == "fr"

    def test_set_new_section(self):
        """Test setting value in new section."""
        settings = Settings(self.config_dir)
        
        settings.set("new_section", "new_key", "new_value")
        
        assert "new_section" in settings.settings
        assert settings.settings["new_section"]["new_key"] == "new_value"

    def test_set_new_key_in_existing_section(self):
        """Test setting new key in existing section."""
        settings = Settings(self.config_dir)
        
        settings.set("general", "new_key", "new_value")
        
        assert settings.settings["general"]["new_key"] == "new_value"

    def test_deep_update_simple(self):
        """Test deep update with simple values."""
        settings = Settings(self.config_dir)
        
        target = {"a": 1, "b": 2}
        source = {"b": 3, "c": 4}
        
        settings._deep_update(target, source)
        
        assert target == {"a": 1, "b": 3, "c": 4}

    def test_deep_update_nested_dicts(self):
        """Test deep update with nested dictionaries."""
        settings = Settings(self.config_dir)
        
        target = {
            "section1": {"key1": "value1", "key2": "value2"},
            "section2": {"key3": "value3"}
        }
        source = {
            "section1": {"key2": "new_value2", "key4": "value4"},
            "section3": {"key5": "value5"}
        }
        
        settings._deep_update(target, source)
        
        expected = {
            "section1": {"key1": "value1", "key2": "new_value2", "key4": "value4"},
            "section2": {"key3": "value3"},
            "section3": {"key5": "value5"}
        }
        
        assert target == expected

    def test_deep_update_mixed_types(self):
        """Test deep update with mixed types."""
        settings = Settings(self.config_dir)
        
        target = {
            "section1": {"key1": "value1"},
            "section2": "string_value"
        }
        source = {
            "section1": {"key2": "value2"},
            "section2": {"key3": "value3"}  # Replace string with dict
        }
        
        settings._deep_update(target, source)
        
        expected = {
            "section1": {"key1": "value1", "key2": "value2"},
            "section2": {"key3": "value3"}
        }
        
        assert target == expected

    def test_settings_isolation(self):
        """Test that settings instances are isolated."""
        settings1 = Settings(self.config_dir)
        settings2 = Settings(self.config_dir)
        
        # Modify settings1
        settings1.set("general", "language", "en")
        
        # settings2 should not be affected
        assert settings2.get("general", "language") == "auto"

    def test_settings_persistence(self):
        """Test that settings persist across instances."""
        # Create first instance and modify settings
        settings1 = Settings(self.config_dir)
        settings1.set("general", "language", "zh_CN")
        settings1.save_settings()
        
        # Create second instance
        settings2 = Settings(self.config_dir)
        
        # Should load the modified settings
        assert settings2.get("general", "language") == "zh_CN"

    def test_unicode_handling(self):
        """Test handling of unicode characters in settings."""
        settings = Settings(self.config_dir)
        
        # Set unicode values
        settings.set("general", "unicode_test", "测试中文")
        settings.set("general", "emoji_test", "🎉📁")
        
        # Save and reload
        settings.save_settings()
        settings2 = Settings(self.config_dir)
        
        assert settings2.get("general", "unicode_test") == "测试中文"
        assert settings2.get("general", "emoji_test") == "🎉📁"

    def test_large_settings_data(self):
        """Test handling of large settings data."""
        settings = Settings(self.config_dir)
        
        # Create large data structure
        large_data = {}
        for i in range(100):
            large_data[f"section_{i}"] = {
                f"key_{j}": f"value_{i}_{j}" for j in range(50)
            }
        
        # Set and save
        for section, data in large_data.items():
            for key, value in data.items():
                settings.set(section, key, value)
        
        result = settings.save_settings()
        assert result is True
        
        # Verify data integrity
        settings2 = Settings(self.config_dir)
        for section, data in large_data.items():
            for key, value in data.items():
                assert settings2.get(section, key) == value


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

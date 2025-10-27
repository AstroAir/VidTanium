"""
Tests for CLI internationalization (i18n).
"""
import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Ensure src is in path (should be done by conftest, but be explicit)
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Now import CLI modules
import src.cli.i18n_cli


class TestCLII18n:
    """Test suite for CLI i18n functionality."""

    def test_init_cli_i18n(self):
        """Test CLI i18n initialization."""
        with patch.object(src.cli.i18n_cli, 'get_i18n_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.current_locale = "zh_CN"
            mock_manager.set_locale = Mock(return_value=True)
            mock_get_manager.return_value = mock_manager

            result = src.cli.i18n_cli.init_cli_i18n("zh_CN")

            assert result == mock_manager
            mock_manager.set_locale.assert_called_once_with("zh_CN")

    def test_get_cli_i18n_manager(self):
        """Test getting CLI i18n manager."""
        # Reset the cached manager
        src.cli.i18n_cli._cli_i18n_manager = None

        with patch.object(src.cli.i18n_cli, 'get_i18n_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager

            result = src.cli.i18n_cli.get_cli_i18n_manager()

            assert result == mock_manager
            # Verify it was cached
            assert src.cli.i18n_cli._cli_i18n_manager == mock_manager

    def test_tr_function(self):
        """Test translation function."""
        with patch.object(src.cli.i18n_cli, 'get_cli_i18n_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.tr = Mock(return_value="Translated text")
            mock_get_manager.return_value = mock_manager

            result = src.cli.i18n_cli.tr("cli.messages.welcome")

            assert result == "Translated text"
            mock_manager.tr.assert_called_once_with("cli.messages.welcome")

    def test_tr_with_variables(self):
        """Test translation function with variable substitution."""
        with patch.object(src.cli.i18n_cli, 'get_cli_i18n_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.tr = Mock(return_value="Hello, World")
            mock_get_manager.return_value = mock_manager

            result = src.cli.i18n_cli.tr("cli.messages.greeting", name="World")

            assert result == "Hello, World"
            mock_manager.tr.assert_called_once_with("cli.messages.greeting", name="World")

    def test_tr_error_handling(self):
        """Test translation function error handling."""
        with patch.object(src.cli.i18n_cli, 'get_cli_i18n_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.tr = Mock(side_effect=Exception("Translation error"))
            mock_get_manager.return_value = mock_manager

            # Should return fallback (last part of key, title-cased)
            result = src.cli.i18n_cli.tr("cli.messages.welcome")

            assert result == "Welcome"

    def test_set_cli_locale(self):
        """Test setting CLI locale."""
        with patch.object(src.cli.i18n_cli, 'get_cli_i18n_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.set_locale = Mock(return_value=True)
            mock_get_manager.return_value = mock_manager

            result = src.cli.i18n_cli.set_cli_locale("en")

            assert result is True
            mock_manager.set_locale.assert_called_once_with("en")

    def test_get_available_cli_locales(self):
        """Test getting available CLI locales."""
        with patch.object(src.cli.i18n_cli, 'get_cli_i18n_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_available_locales = Mock(return_value=["en", "zh_CN"])
            mock_get_manager.return_value = mock_manager

            result = src.cli.i18n_cli.get_available_cli_locales()

            assert result == ["en", "zh_CN"]


class TestCLITranslationKeys:
    """Test that all CLI translation keys exist in locale files."""
    
    def test_english_translation_keys_exist(self):
        """Test that all required English translation keys exist."""
        locale_file = Path("src/locales/en.json")
        
        with open(locale_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # Check CLI section exists
        assert "cli" in translations
        
        # Check main sections
        assert "welcome" in translations["cli"]
        assert "messages" in translations["cli"]
        assert "errors" in translations["cli"]
        assert "status" in translations["cli"]
        assert "commands" in translations["cli"]
        assert "task_list" in translations["cli"]
        assert "progress" in translations["cli"]
        assert "settings" in translations["cli"]
        assert "interactive" in translations["cli"]
        assert "monitoring" in translations["cli"]
    
    def test_chinese_translation_keys_exist(self):
        """Test that all required Chinese translation keys exist."""
        locale_file = Path("src/locales/zh_CN.json")
        
        with open(locale_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # Check CLI section exists
        assert "cli" in translations
        
        # Check main sections
        assert "welcome" in translations["cli"]
        assert "messages" in translations["cli"]
        assert "errors" in translations["cli"]
        assert "status" in translations["cli"]
        assert "commands" in translations["cli"]
        assert "task_list" in translations["cli"]
        assert "progress" in translations["cli"]
        assert "settings" in translations["cli"]
        assert "interactive" in translations["cli"]
        assert "monitoring" in translations["cli"]
    
    def test_translation_key_parity(self):
        """Test that English and Chinese have the same keys."""
        en_file = Path("src/locales/en.json")
        zh_file = Path("src/locales/zh_CN.json")
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_translations = json.load(f)
        
        with open(zh_file, 'r', encoding='utf-8') as f:
            zh_translations = json.load(f)
        
        # Get CLI keys
        en_cli_keys = set(self._get_all_keys(en_translations.get("cli", {})))
        zh_cli_keys = set(self._get_all_keys(zh_translations.get("cli", {})))
        
        # Check for missing keys
        missing_in_zh = en_cli_keys - zh_cli_keys
        missing_in_en = zh_cli_keys - en_cli_keys
        
        assert len(missing_in_zh) == 0, f"Missing in Chinese: {missing_in_zh}"
        assert len(missing_in_en) == 0, f"Missing in English: {missing_in_en}"
    
    def _get_all_keys(self, d, prefix=""):
        """Recursively get all keys from nested dict."""
        keys = []
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                keys.extend(self._get_all_keys(value, full_key))
            else:
                keys.append(full_key)
        return keys
    
    def test_welcome_messages(self):
        """Test welcome message translations."""
        en_file = Path("src/locales/en.json")
        zh_file = Path("src/locales/zh_CN.json")
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_translations = json.load(f)
        
        with open(zh_file, 'r', encoding='utf-8') as f:
            zh_translations = json.load(f)
        
        # Check welcome messages exist
        assert "title" in en_translations["cli"]["welcome"]
        assert "subtitle" in en_translations["cli"]["welcome"]
        assert "title" in zh_translations["cli"]["welcome"]
        assert "subtitle" in zh_translations["cli"]["welcome"]
        
        # Check they're not empty
        assert len(en_translations["cli"]["welcome"]["title"]) > 0
        assert len(zh_translations["cli"]["welcome"]["title"]) > 0
    
    def test_status_translations(self):
        """Test status translations for all task states."""
        en_file = Path("src/locales/en.json")
        zh_file = Path("src/locales/zh_CN.json")
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_translations = json.load(f)
        
        with open(zh_file, 'r', encoding='utf-8') as f:
            zh_translations = json.load(f)
        
        required_statuses = ["pending", "running", "paused", "completed", "failed", "canceled"]
        
        for status in required_statuses:
            assert status in en_translations["cli"]["status"], f"Missing English status: {status}"
            assert status in zh_translations["cli"]["status"], f"Missing Chinese status: {status}"
    
    def test_command_translations(self):
        """Test command translations."""
        en_file = Path("src/locales/en.json")
        zh_file = Path("src/locales/zh_CN.json")
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_translations = json.load(f)
        
        with open(zh_file, 'r', encoding='utf-8') as f:
            zh_translations = json.load(f)
        
        required_commands = ["analyze", "download", "list", "pause", "resume", "cancel"]
        
        for command in required_commands:
            assert command in en_translations["cli"]["commands"], f"Missing English command: {command}"
            assert command in zh_translations["cli"]["commands"], f"Missing Chinese command: {command}"
    
    def test_error_message_translations(self):
        """Test error message translations."""
        en_file = Path("src/locales/en.json")
        zh_file = Path("src/locales/zh_CN.json")
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_translations = json.load(f)
        
        with open(zh_file, 'r', encoding='utf-8') as f:
            zh_translations = json.load(f)
        
        required_errors = ["unexpected", "suggestions", "invalid_url", "task_not_found", "download_failed"]
        
        for error in required_errors:
            assert error in en_translations["cli"]["errors"], f"Missing English error: {error}"
            assert error in zh_translations["cli"]["errors"], f"Missing Chinese error: {error}"
    
    def test_no_empty_translations(self):
        """Test that no CLI translations are empty strings."""
        en_file = Path("src/locales/en.json")
        zh_file = Path("src/locales/zh_CN.json")
        
        with open(en_file, 'r', encoding='utf-8') as f:
            en_translations = json.load(f)
        
        with open(zh_file, 'r', encoding='utf-8') as f:
            zh_translations = json.load(f)
        
        # Check English
        empty_en = self._find_empty_values(en_translations.get("cli", {}))
        assert len(empty_en) == 0, f"Empty English translations: {empty_en}"
        
        # Check Chinese
        empty_zh = self._find_empty_values(zh_translations.get("cli", {}))
        assert len(empty_zh) == 0, f"Empty Chinese translations: {empty_zh}"
    
    def _find_empty_values(self, d, prefix=""):
        """Recursively find empty string values."""
        empty = []
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                empty.extend(self._find_empty_values(value, full_key))
            elif isinstance(value, str) and len(value.strip()) == 0:
                empty.append(full_key)
        return empty


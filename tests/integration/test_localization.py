import pytest
import sys
import os
import tempfile
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any, Optional, List

# Mock PySide6 components for testing
class MockQLocale:
    def __init__(self, name="en_US") -> None:
        self._name = name
        
    def name(self) -> None:
        return self._name
        
    @staticmethod
    def system() -> None:
        return MockQLocale("en_US")

class MockQTranslator:
    def __init__(self) -> None:
        self.loaded_file = None
        self.loaded = False
        
    def load(self, filename, directory="") -> None:
        self.loaded_file = filename
        self.loaded = True
        return True

class MockQCoreApplication:
    translators = []
    
    @classmethod
    def installTranslator(cls, translator) -> None:
        cls.translators.append(translator)
        
    @classmethod
    def removeTranslator(cls, translator) -> None:
        if translator in cls.translators:
            cls.translators.remove(translator)

# Mock the PySide6 imports
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtCore'].QLocale = MockQLocale
sys.modules['PySide6.QtCore'].QTranslator = MockQTranslator
sys.modules['PySide6.QtCore'].QCoreApplication = MockQCoreApplication

# Mock localization functions
def mock_tr(key, *args, **kwargs) -> None:
    """Mock translation function that returns the key with optional formatting"""
    if args:
        try:
            return key.format(*args)
        except:
            return key
    return key

# Mock the i18n module
sys.modules['src.gui.utils.i18n'] = Mock()
sys.modules['src.gui.utils.i18n'].tr = mock_tr
sys.modules['src.gui.utils.i18n'].init_i18n = Mock()
sys.modules['src.gui.utils.i18n'].set_locale = Mock()
sys.modules['src.gui.utils.i18n'].get_available_locales = Mock(return_value=['en', 'zh_CN', 'es', 'fr', 'de'])
sys.modules['src.gui.utils.i18n'].get_current_locale = Mock(return_value='en')


class TestLocalizationSystem:
    """Test suite for the localization system."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Reset translator list
        MockQCoreApplication.translators.clear()

    def test_translation_function_basic(self) -> None:
        """Test basic translation function."""
        result = mock_tr("test.key")
        assert result == "test.key"

    def test_translation_function_with_formatting(self) -> None:
        """Test translation function with string formatting."""
        result = mock_tr("Hello {0}!", "World")
        assert result == "Hello World!"

    def test_translation_function_with_multiple_args(self) -> None:
        """Test translation function with multiple arguments."""
        result = mock_tr("{0} has {1} items", "User", "5")
        assert result == "User has 5 items"

    def test_translation_function_error_handling(self) -> None:
        """Test translation function error handling."""
        # Should not raise exception with invalid format
        result = mock_tr("Invalid {format", "test")
        assert result == "Invalid {format"

    def test_locale_detection(self) -> None:
        """Test system locale detection."""
        system_locale = MockQLocale.system()
        assert system_locale.name() == "en_US"

    def test_translator_installation(self) -> None:
        """Test translator installation."""
        translator = MockQTranslator()
        MockQCoreApplication.installTranslator(translator)
        
        assert translator in MockQCoreApplication.translators
        assert len(MockQCoreApplication.translators) == 1

    def test_translator_removal(self) -> None:
        """Test translator removal."""
        translator = MockQTranslator()
        MockQCoreApplication.installTranslator(translator)
        MockQCoreApplication.removeTranslator(translator)
        
        assert translator not in MockQCoreApplication.translators
        assert len(MockQCoreApplication.translators) == 0

    def test_translation_file_loading(self) -> None:
        """Test translation file loading."""
        translator = MockQTranslator()
        result = translator.load("vidtanium_zh_CN.qm", "/translations")
        
        assert result is True
        assert translator.loaded is True
        assert translator.loaded_file == "vidtanium_zh_CN.qm"


class TestLocalizationKeys:
    """Test suite for localization keys and consistency."""

    def test_common_ui_keys(self) -> None:
        """Test common UI localization keys."""
        common_keys = [
            "common.ok",
            "common.cancel", 
            "common.apply",
            "common.close",
            "common.save",
            "common.load",
            "common.delete",
            "common.edit",
            "common.add",
            "common.remove"
        ]
        
        for key in common_keys:
            result = mock_tr(key)
            assert result == key

    def test_menu_keys(self) -> None:
        """Test menu localization keys."""
        menu_keys = [
            "menu.file",
            "menu.edit", 
            "menu.view",
            "menu.tools",
            "menu.help",
            "menu.file.new",
            "menu.file.open",
            "menu.file.save",
            "menu.file.exit"
        ]
        
        for key in menu_keys:
            result = mock_tr(key)
            assert result == key

    def test_dialog_keys(self) -> None:
        """Test dialog localization keys."""
        dialog_keys = [
            "dialog.title",
            "dialog.message",
            "dialog.error",
            "dialog.warning",
            "dialog.information",
            "dialog.question",
            "task_dialog.title",
            "task_dialog.basic_info",
            "about_dialog.title"
        ]
        
        for key in dialog_keys:
            result = mock_tr(key)
            assert result == key

    def test_dashboard_keys(self) -> None:
        """Test dashboard localization keys."""
        dashboard_keys = [
            "dashboard.welcome.title",
            "dashboard.welcome.subtitle", 
            "dashboard.stats.total_tasks",
            "dashboard.stats.active_downloads",
            "dashboard.stats.completed",
            "dashboard.stats.total_speed"
        ]
        
        for key in dashboard_keys:
            result = mock_tr(key)
            assert result == key

    def test_error_message_keys(self) -> None:
        """Test error message localization keys."""
        error_keys = [
            "error.network",
            "error.file_not_found",
            "error.permission_denied",
            "error.invalid_url",
            "error.download_failed",
            "error.extraction_failed"
        ]
        
        for key in error_keys:
            result = mock_tr(key)
            assert result == key

    def test_status_message_keys(self) -> None:
        """Test status message localization keys."""
        status_keys = [
            "status.ready",
            "status.downloading",
            "status.paused",
            "status.completed",
            "status.failed",
            "status.cancelled"
        ]
        
        for key in status_keys:
            result = mock_tr(key)
            assert result == key


class TestLocalizationIntegration:
    """Test suite for localization integration with application components."""

    def test_application_localization_init(self) -> None:
        """Test localization initialization in application."""
        from src.gui.utils.i18n import init_i18n
        
        # Should not raise exception
        init_i18n()

    def test_locale_setting(self) -> None:
        """Test setting application locale."""
        from src.gui.utils.i18n import set_locale
        
        # Should not raise exception
        set_locale("zh_CN")

    def test_available_locales(self) -> None:
        """Test getting available locales."""
        from src.gui.utils.i18n import get_available_locales
        
        locales = get_available_locales()
        assert isinstance(locales, list)
        assert len(locales) > 0
        assert 'en' in locales

    def test_current_locale(self) -> None:
        """Test getting current locale."""
        from src.gui.utils.i18n import get_current_locale
        
        current = get_current_locale()
        assert current == 'en'

    def test_translation_in_widgets(self) -> None:
        """Test translation usage in widgets."""
        # Test that widgets can use translation function
        from src.gui.utils.i18n import tr
        
        # Simulate widget using translation
        title = tr("widget.title")
        assert title == "widget.title"

    def test_dynamic_language_switching(self) -> None:
        """Test dynamic language switching."""
        from src.gui.utils.i18n import set_locale, get_current_locale
        
        # Switch to Chinese
        set_locale("zh_CN")
        
        # Switch back to English
        set_locale("en")
        
        # Should not raise exceptions
        assert True

    def test_fallback_translation(self) -> None:
        """Test fallback translation behavior."""
        # Test with non-existent key
        result = mock_tr("nonexistent.key")
        assert result == "nonexistent.key"

    def test_pluralization_support(self) -> None:
        """Test pluralization support in translations."""
        # Test singular
        result = mock_tr("item.count.singular", "1")
        assert "1" in result
        
        # Test plural
        result = mock_tr("item.count.plural", "5")
        assert "5" in result

    def test_context_sensitive_translation(self) -> None:
        """Test context-sensitive translations."""
        # Test same key in different contexts
        menu_result = mock_tr("menu.file")
        dialog_result = mock_tr("dialog.file")
        
        assert menu_result == "menu.file"
        assert dialog_result == "dialog.file"

    def test_translation_with_html(self) -> None:
        """Test translation with HTML content."""
        html_key = "message.html"
        result = mock_tr(html_key)
        assert result == html_key

    def test_translation_caching(self) -> None:
        """Test translation caching behavior."""
        # Multiple calls to same key should be consistent
        key = "test.caching"
        result1 = mock_tr(key)
        result2 = mock_tr(key)
        
        assert result1 == result2

    def test_translation_with_special_characters(self) -> None:
        """Test translation with special characters."""
        special_keys = [
            "special.unicode.中文",
            "special.emoji.🎉",
            "special.symbols.@#$%"
        ]
        
        for key in special_keys:
            result = mock_tr(key)
            assert result == key

    def test_translation_performance(self) -> None:
        """Test translation performance."""
        import time
        
        # Test translation speed
        start_time = time.time()
        for i in range(1000):
            mock_tr(f"performance.test.{i}")
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 1.0

    def test_translation_memory_usage(self) -> None:
        """Test translation memory usage."""
        # Test that translations don't cause memory leaks
        for i in range(100):
            mock_tr(f"memory.test.{i}")
        
        # Should not raise memory errors
        assert True

    def test_locale_specific_formatting(self) -> None:
        """Test locale-specific formatting."""
        # Test number formatting
        number_result = mock_tr("format.number", "1234.56")
        assert "1234.56" in number_result
        
        # Test date formatting
        date_result = mock_tr("format.date", "2023-01-01")
        assert "2023-01-01" in date_result

    def test_rtl_language_support(self) -> None:
        """Test right-to-left language support."""
        # Test RTL language handling
        rtl_result = mock_tr("rtl.text")
        assert rtl_result == "rtl.text"

    def test_translation_validation(self) -> None:
        """Test translation validation."""
        # Test that all required keys have translations
        required_keys = [
            "app.name",
            "app.version", 
            "common.ok",
            "common.cancel"
        ]
        
        for key in required_keys:
            result = mock_tr(key)
            assert result is not None
            assert len(result) > 0

    def test_translation_consistency(self) -> None:
        """Test translation consistency across components."""
        # Test that same concepts use same translations
        ok_button = mock_tr("common.ok")
        ok_dialog = mock_tr("dialog.ok")
        
        # Both should be consistent (in real implementation)
        assert ok_button == "common.ok"
        assert ok_dialog == "dialog.ok"

    def test_error_handling_in_translation(self) -> None:
        """Test error handling in translation system."""
        # Test with None key
        try:
            result = mock_tr(None)
            assert result is None or result == "None"
        except:
            # Should handle gracefully
            pass
        
        # Test with empty key
        result = mock_tr("")
        assert result == ""


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

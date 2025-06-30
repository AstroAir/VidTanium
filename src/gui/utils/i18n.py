"""
Internationalization (i18n) module for VidTanium application.
Provides translation functions and language management.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class I18nManager:
    """Internationalization manager for handling translations."""
    
    def __init__(self, default_locale: str = "zh_CN"):
        """
        Initialize i18n manager.
        
        Args:
            default_locale: Default locale to use (e.g., 'zh_CN', 'en')
        """
        self.default_locale = default_locale
        self.current_locale = default_locale
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.locales_dir = Path(__file__).parent.parent.parent / "locales"
        self._is_initialized = False
        
        # Load all available translations
        self._load_translations()
        self._validate_translations()
    
    def _validate_translations(self) -> None:
        """Validate that essential translations are available"""
        if not self.translations:
            logger.error("No translations loaded! Application may not function properly.")
            return
            
        # Check if default locale exists
        if self.default_locale not in self.translations:
            logger.warning(f"Default locale '{self.default_locale}' not found. Available: {list(self.translations.keys())}")
            # Fall back to any available locale
            if self.translations:
                self.default_locale = list(self.translations.keys())[0]
                self.current_locale = self.default_locale
                logger.info(f"Using fallback locale: {self.default_locale}")
        
        self._is_initialized = True
        logger.info(f"I18n initialized with {len(self.translations)} locales: {list(self.translations.keys())}")
    
    def is_initialized(self) -> bool:
        """Check if i18n system is properly initialized"""
        return self._is_initialized
    
    def _load_translations(self) -> None:
        """Load all translation files from the locales directory."""
        try:
            if not self.locales_dir.exists():
                logger.warning(f"Locales directory not found: {self.locales_dir}")
                return
            
            for locale_file in self.locales_dir.glob("*.json"):
                locale_code = locale_file.stem
                try:
                    with open(locale_file, 'r', encoding='utf-8') as f:
                        self.translations[locale_code] = json.load(f)
                    logger.debug(f"Loaded translations for locale: {locale_code}")
                except Exception as e:
                    logger.error(f"Failed to load translation file {locale_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
    
    def set_locale(self, locale: str) -> bool:
        """
        Set the current locale.
        
        Args:
            locale: Locale code (e.g., 'zh_CN', 'en')
            
        Returns:
            bool: True if locale was set successfully, False otherwise
        """
        if locale in self.translations:
            self.current_locale = locale
            logger.info(f"Locale set to: {locale}")
            return True
        else:
            logger.warning(f"Locale '{locale}' not available. Available locales: {list(self.translations.keys())}")
            return False
    
    def get_available_locales(self) -> list[str]:
        """Get list of available locales."""
        return list(self.translations.keys())
    
    def get_locale_name(self, locale: str) -> str:
        """Get human-readable name for a locale."""
        locale_names = {
            "zh_CN": "简体中文",
            "en": "English",
            "zh_TW": "繁體中文",
            "ja": "日本語",
            "ko": "한국어",
            "fr": "Français",
            "de": "Deutsch",
            "es": "Español",
            "ru": "Русский"
        }
        return locale_names.get(locale, locale)
    
    def tr(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current locale.
        
        Args:
            key: Translation key in dot notation (e.g., 'dashboard.title')
            **kwargs: Variables to substitute in the translation
            
        Returns:
            str: Translated string, or the key itself if translation not found
        """
        return self._get_translation(key, self.current_locale, **kwargs)
    
    def tr_locale(self, key: str, locale: str, **kwargs) -> str:
        """
        Translate a key to a specific locale.
        
        Args:
            key: Translation key in dot notation
            locale: Target locale code
            **kwargs: Variables to substitute in the translation
            
        Returns:
            str: Translated string, or the key itself if translation not found
        """
        return self._get_translation(key, locale, **kwargs)
    
    def _get_translation(self, key: str, locale: str, **kwargs) -> str:
        """
        Get translation for a key in the specified locale.
        
        Args:
            key: Translation key in dot notation
            locale: Locale code
            **kwargs: Variables to substitute in the translation
            
        Returns:
            str: Translated string
        """
        try:
            # Try to get translation from the specified locale
            translation = self._get_nested_value(self.translations.get(locale, {}), key)
            
            # Fallback to default locale if not found
            if translation is None and locale != self.default_locale:
                translation = self._get_nested_value(self.translations.get(self.default_locale, {}), key)
            
            # Fallback to English if still not found and current locale is not English
            if translation is None and locale != "en" and self.default_locale != "en":
                translation = self._get_nested_value(self.translations.get("en", {}), key)
            
            # Fallback to key itself if still not found
            if translation is None:
                logger.warning(f"Translation not found for key: {key} in any available locale")
                # Return the last part of the key as fallback (e.g., "title" from "dashboard.welcome.title")
                return key.split('.')[-1].replace('_', ' ').title()
            
            # Substitute variables if provided
            if kwargs:
                try:
                    translation = translation.format(**kwargs)
                except KeyError as e:
                    logger.warning(f"Missing variable {e} for translation key: {key}")
                except Exception as e:
                    logger.warning(f"Error formatting translation for key {key}: {e}")
            
            return translation
            
        except Exception as e:
            logger.error(f"Error getting translation for key {key}: {e}")
            # Return a more user-friendly fallback
            return key.split('.')[-1].replace('_', ' ').title()
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """
        Get a nested value from a dictionary using dot notation.
        
        Args:
            data: Dictionary to search in
            key: Dot-separated key (e.g., 'dashboard.title')
            
        Returns:
            Optional[str]: Value if found, None otherwise
        """
        try:
            keys = key.split('.')
            value = data
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return None
            return value if isinstance(value, str) else None
        except Exception:
            return None


# Global i18n manager instance
_i18n_manager: Optional[I18nManager] = None


def init_i18n(default_locale: str = "zh_CN") -> I18nManager:
    """
    Initialize the global i18n manager.
    
    Args:
        default_locale: Default locale to use
        
    Returns:
        I18nManager: The initialized i18n manager
    """
    global _i18n_manager
    _i18n_manager = I18nManager(default_locale)
    return _i18n_manager


def get_i18n_manager() -> I18nManager:
    """
    Get the global i18n manager instance.
    
    Returns:
        I18nManager: The i18n manager instance
        
    Raises:
        RuntimeError: If i18n has not been initialized
    """
    global _i18n_manager
    if _i18n_manager is None:
        # Auto-initialize with default settings
        _i18n_manager = I18nManager()
    return _i18n_manager


def tr(key: str, **kwargs) -> str:
    """
    Convenience function to translate a key.
    
    Args:
        key: Translation key in dot notation
        **kwargs: Variables to substitute in the translation
        
    Returns:
        str: Translated string
    """
    try:
        manager = get_i18n_manager()
        if not manager.is_initialized():
            logger.warning("I18n manager not properly initialized, returning fallback")
            return key.split('.')[-1].replace('_', ' ').title()
        return manager.tr(key, **kwargs)
    except Exception as e:
        logger.error(f"Error in tr() function for key {key}: {e}")
        return key.split('.')[-1].replace('_', ' ').title()


def set_locale(locale: str) -> bool:
    """
    Convenience function to set the current locale.
    
    Args:
        locale: Locale code
        
    Returns:
        bool: True if locale was set successfully
    """
    return get_i18n_manager().set_locale(locale)


def get_available_locales() -> list[str]:
    """
    Convenience function to get available locales.
    
    Returns:
        list[str]: List of available locale codes
    """
    return get_i18n_manager().get_available_locales()


def get_locale_name(locale: str) -> str:
    """
    Convenience function to get human-readable locale name.
    
    Args:
        locale: Locale code
        
    Returns:
        str: Human-readable locale name
    """
    return get_i18n_manager().get_locale_name(locale)

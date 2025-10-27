"""
CLI Internationalization Module
i18n utilities for CLI context
"""

from typing import Optional
from loguru import logger

# Import the existing i18n system
from src.gui.utils.i18n import get_i18n_manager, I18nManager


_cli_i18n_manager: Optional[I18nManager] = None


def init_cli_i18n(default_locale: str = "zh_CN") -> I18nManager:
    """
    Initialize CLI i18n system
    
    Args:
        default_locale: Default locale to use
        
    Returns:
        I18nManager: The i18n manager instance
    """
    global _cli_i18n_manager
    _cli_i18n_manager = get_i18n_manager()
    
    # Set locale if specified
    if default_locale:
        _cli_i18n_manager.set_locale(default_locale)
    
    logger.debug(f"CLI i18n initialized with locale: {_cli_i18n_manager.current_locale}")
    return _cli_i18n_manager


def get_cli_i18n_manager() -> I18nManager:
    """
    Get the CLI i18n manager instance
    
    Returns:
        I18nManager: The i18n manager instance
    """
    global _cli_i18n_manager
    if _cli_i18n_manager is None:
        _cli_i18n_manager = get_i18n_manager()
    return _cli_i18n_manager


def tr(key: str, **kwargs) -> str:
    """
    Translate a key for CLI context
    
    Args:
        key: Translation key in dot notation
        **kwargs: Variables to substitute in the translation
        
    Returns:
        str: Translated string
    """
    try:
        manager = get_cli_i18n_manager()
        return manager.tr(key, **kwargs)
    except Exception as e:
        logger.error(f"Translation error for key {key}: {e}")
        # Return fallback
        return key.split('.')[-1].replace('_', ' ').title()


def set_cli_locale(locale: str) -> bool:
    """
    Set the CLI locale
    
    Args:
        locale: Locale code (e.g., 'en', 'zh_CN')
        
    Returns:
        bool: True if locale was set successfully
    """
    manager = get_cli_i18n_manager()
    return manager.set_locale(locale)


def get_available_cli_locales() -> list[str]:
    """
    Get available locales for CLI
    
    Returns:
        list[str]: List of available locale codes
    """
    manager = get_cli_i18n_manager()
    return manager.get_available_locales()


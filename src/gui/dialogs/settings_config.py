"""
Shared settings configuration and utilities for all settings dialogs
"""

from pathlib import Path
from PySide6.QtCore import QObject, Signal
from qfluentwidgets import (
    ConfigItem, OptionsConfigItem, BoolValidator, 
    RangeConfigItem, RangeValidator, ConfigValidator
)


class OptionsValidator(ConfigValidator):
    """Validator for options"""
    def __init__(self, options):
        self.options = options
    
    def validate(self, value):
        return True  # Always return True as required by base class
    
    def correct(self, value):
        return value if value in self.options else self.options[0]


class SettingsConfig(QObject):
    """Unified configuration items for settings"""
    
    # Signals
    settings_changed = Signal()
    theme_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # General settings
        self.output_directory = ConfigItem("General", "OutputDirectory", str(Path.home() / "Downloads"))
        self.auto_cleanup = ConfigItem("General", "AutoCleanup", True, BoolValidator())
        self.auto_start_downloads = ConfigItem("General", "AutoStartDownloads", True, BoolValidator())
        self.check_updates = ConfigItem("General", "CheckUpdates", True, BoolValidator())
        self.enable_notifications = ConfigItem("General", "EnableNotifications", True, BoolValidator())
        self.max_recent_files = RangeConfigItem("General", "MaxRecentFiles", 10, RangeValidator(0, 50))
        self.max_concurrent_downloads = RangeConfigItem("General", "MaxConcurrentDownloads", 3, RangeValidator(1, 10))
        self.retry_attempts = RangeConfigItem("General", "RetryAttempts", 3, RangeValidator(0, 10))
        
        # Maximum concurrent downloads as OptionsConfigItem for UI compatibility
        self.max_concurrent_downloads_ui = OptionsConfigItem(
            "General", "MaxConcurrentDownloadsUI", "3",
            OptionsValidator(SettingsConstants.CONCURRENT_OPTIONS)
        )
        
        # Retry attempts as OptionsConfigItem for UI compatibility  
        self.retry_attempts_ui = OptionsConfigItem(
            "General", "RetryAttemptsUI", "3",
            OptionsValidator(SettingsConstants.RETRY_OPTIONS)
        )
        
        # Appearance settings
        self.theme = OptionsConfigItem(
            "General", "Theme", "system",
            OptionsValidator(["system", "light", "dark"])
        )
        self.language = OptionsConfigItem(
            "General", "Language", "auto", 
            OptionsValidator(["auto", "zh_CN", "en_US"])
        )
        
        # Network settings
        self.use_proxy = ConfigItem("Network", "UseProxy", False, BoolValidator())
        self.proxy_host = ConfigItem("Network", "ProxyHost", "")
        self.proxy_port = RangeConfigItem("Network", "ProxyPort", 8080, RangeValidator(1, 65535))
        self.timeout = RangeConfigItem("Network", "Timeout", 30, RangeValidator(10, 300))
        self.user_agent = OptionsConfigItem(
            "Network", "UserAgent", "default",
            OptionsValidator(["default", "chrome", "firefox", "safari", "custom"])
        )
        self.custom_user_agent = ConfigItem("Network", "CustomUserAgent", "")


class SettingsConstants:
    """Constants used across settings dialogs"""
    
    # Theme mappings
    THEME_OPTIONS = ["跟随系统设置", "浅色", "深色"]
    THEME_VALUES = ["system", "light", "dark"]
    THEME_MAP = dict(zip(THEME_OPTIONS, THEME_VALUES))
    THEME_REVERSE_MAP = dict(zip(THEME_VALUES, THEME_OPTIONS))
    
    # Language mappings
    LANGUAGE_OPTIONS = ["自动检测", "简体中文", "English"]
    LANGUAGE_VALUES = ["auto", "zh_CN", "en_US"]
    LANGUAGE_MAP = dict(zip(LANGUAGE_OPTIONS, LANGUAGE_VALUES))
    LANGUAGE_REVERSE_MAP = dict(zip(LANGUAGE_VALUES, LANGUAGE_OPTIONS))
    
    # Download options
    CONCURRENT_OPTIONS = ["1", "2", "3", "4", "5", "6", "8", "10"]
    RETRY_OPTIONS = ["0", "1", "2", "3", "5", "10"]
    TIMEOUT_OPTIONS = ["10", "15", "30", "60", "120"]
    
    # User agent options
    USER_AGENT_OPTIONS = [
        "默认 (VidTanium)",
        "Chrome (Windows)",
        "Firefox (Windows)",
        "Safari (macOS)",
        "自定义"
    ]
    USER_AGENT_VALUES = ["default", "chrome", "firefox", "safari", "custom"]
    USER_AGENT_MAP = dict(zip(USER_AGENT_OPTIONS, USER_AGENT_VALUES))
    USER_AGENT_REVERSE_MAP = dict(zip(USER_AGENT_VALUES, USER_AGENT_OPTIONS))


class SettingsManager:
    """Utility class for managing settings operations"""
    
    @staticmethod
    def load_from_settings(config: SettingsConfig, settings):
        """Load configuration from settings object"""
        try:
            # General settings
            config.output_directory.value = settings.get("general", "output_directory", str(Path.home() / "Downloads"))
            config.auto_cleanup.value = settings.get("general", "auto_cleanup", True)
            config.auto_start_downloads.value = settings.get("general", "auto_start_downloads", True)
            config.check_updates.value = settings.get("general", "check_updates", True)
            config.enable_notifications.value = settings.get("general", "enable_notifications", True)
            config.max_recent_files.value = settings.get("general", "max_recent_files", 10)
            config.max_concurrent_downloads.value = settings.get("general", "max_concurrent_downloads", 3)
            config.retry_attempts.value = settings.get("general", "retry_attempts", 3)
            
            # Sync UI versions
            config.max_concurrent_downloads_ui.value = str(config.max_concurrent_downloads.value)
            config.retry_attempts_ui.value = str(config.retry_attempts.value)
            
            # Appearance settings
            config.theme.value = settings.get("general", "theme", "system")
            config.language.value = settings.get("general", "language", "auto")
            
            # Network settings
            config.use_proxy.value = settings.get("network", "use_proxy", False)
            config.proxy_host.value = settings.get("network", "proxy_host", "")
            config.proxy_port.value = settings.get("network", "proxy_port", 8080)
            config.timeout.value = settings.get("network", "timeout", 30)
            config.user_agent.value = settings.get("network", "user_agent", "default")
            config.custom_user_agent.value = settings.get("network", "custom_user_agent", "")
            
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    @staticmethod
    def save_to_settings(config: SettingsConfig, settings):
        """Save configuration to settings object"""
        try:
            # General settings
            settings.set("general", "output_directory", config.output_directory.value)
            settings.set("general", "auto_cleanup", config.auto_cleanup.value)
            settings.set("general", "auto_start_downloads", config.auto_start_downloads.value)
            settings.set("general", "check_updates", config.check_updates.value)
            settings.set("general", "enable_notifications", config.enable_notifications.value)
            settings.set("general", "max_recent_files", config.max_recent_files.value)
            settings.set("general", "max_concurrent_downloads", config.max_concurrent_downloads.value)
            settings.set("general", "retry_attempts", config.retry_attempts.value)
            
            # Sync from UI versions
            config.max_concurrent_downloads.value = int(config.max_concurrent_downloads_ui.value)
            config.retry_attempts.value = int(config.retry_attempts_ui.value)
            
            # Appearance settings
            settings.set("general", "theme", config.theme.value)
            settings.set("general", "language", config.language.value)
            
            # Network settings
            settings.set("network", "use_proxy", config.use_proxy.value)
            settings.set("network", "proxy_host", config.proxy_host.value)
            settings.set("network", "proxy_port", config.proxy_port.value)
            settings.set("network", "timeout", config.timeout.value)
            settings.set("network", "user_agent", config.user_agent.value)
            settings.set("network", "custom_user_agent", config.custom_user_agent.value)
            
            # Save to file
            settings.save_settings()
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            raise
    
    @staticmethod
    def reset_to_defaults(config: SettingsConfig):
        """Reset configuration to default values"""
        # General settings
        config.output_directory.value = str(Path.home() / "Downloads")
        config.auto_cleanup.value = True
        config.auto_start_downloads.value = True
        config.check_updates.value = True
        config.enable_notifications.value = True
        config.max_recent_files.value = 10
        config.max_concurrent_downloads.value = 3
        config.retry_attempts.value = 3
        
        # Appearance settings
        config.theme.value = "system"
        config.language.value = "auto"
        
        # Network settings
        config.use_proxy.value = False
        config.proxy_host.value = ""
        config.proxy_port.value = 8080
        config.timeout.value = 30
        config.user_agent.value = "default"
        config.custom_user_agent.value = ""

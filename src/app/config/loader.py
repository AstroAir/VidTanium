"""
Multi-Source Configuration Loader

Supports loading configuration from multiple sources with priority-based merging:
1. Command-line arguments (highest priority)
2. Environment variables
3. User configuration files
4. System configuration files
5. Default values (lowest priority)
"""

import os
import json
import yaml
import toml
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from .schema import ConfigurationSchema, ConfigurationValidator, ValidationLevel


class ConfigurationSource(Enum):
    """Configuration source types"""
    DEFAULTS = "defaults"
    SYSTEM_CONFIG = "system_config"
    USER_CONFIG = "user_config"
    ENVIRONMENT = "environment"
    COMMAND_LINE = "command_line"


class ConfigurationFormat(Enum):
    """Supported configuration file formats"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


@dataclass
class ConfigurationFile:
    """Configuration file information"""
    path: Path
    format: ConfigurationFormat
    source: ConfigurationSource
    exists: bool = False
    readable: bool = False
    data: Optional[Dict[str, Any]] = None


@dataclass
class LoadResult:
    """Configuration loading result"""
    success: bool
    config: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    sources_used: List[ConfigurationSource]
    files_loaded: List[Path]


class EnvironmentVariableMapper:
    """Maps environment variables to configuration paths"""
    
    def __init__(self, prefix: str = "VIDTANIUM_") -> None:
        self.prefix = prefix
        self.mappings = self._create_default_mappings()
    
    def _create_default_mappings(self) -> Dict[str, str]:
        """Create default environment variable mappings"""
        return {
            f"{self.prefix}OUTPUT_DIR": "general.output_directory",
            f"{self.prefix}DEBUG": "logging.debug_logging",
            f"{self.prefix}LOG_LEVEL": "logging.log_level",
            f"{self.prefix}MAX_CONCURRENT": "download.max_concurrent_tasks",
            f"{self.prefix}MAX_WORKERS": "download.max_workers_per_task",
            f"{self.prefix}MAX_RETRIES": "download.max_retries",
            f"{self.prefix}RETRY_DELAY": "download.retry_delay",
            f"{self.prefix}REQUEST_TIMEOUT": "download.request_timeout",
            f"{self.prefix}CHUNK_SIZE": "download.chunk_size",
            f"{self.prefix}BANDWIDTH_LIMIT": "download.bandwidth_limit",
            f"{self.prefix}PROXY": "network.proxy",
            f"{self.prefix}USER_AGENT": "network.user_agent",
            f"{self.prefix}VERIFY_SSL": "network.verify_ssl",
            f"{self.prefix}CONNECTION_TIMEOUT": "network.connection_timeout",
            f"{self.prefix}READ_TIMEOUT": "network.read_timeout",
            f"{self.prefix}THEME": "general.theme",
            f"{self.prefix}LANGUAGE": "general.language",
            f"{self.prefix}AUTO_CLEANUP": "general.auto_cleanup",
            f"{self.prefix}CHECK_UPDATES": "general.check_updates",
            f"{self.prefix}TEMP_DIR": "general.temp_directory",
            f"{self.prefix}CACHE_DIR": "general.cache_directory",
            f"{self.prefix}MEMORY_LIMIT": "performance.memory_limit_mb",
            f"{self.prefix}CPU_LIMIT": "performance.cpu_usage_limit",
            f"{self.prefix}OPTIMIZATION": "performance.optimization_level",
        }
    
    def add_mapping(self, env_var: str, config_path: str) -> None:
        """Add custom environment variable mapping"""
        self.mappings[env_var] = config_path
    
    def get_env_config(self) -> Dict[str, Any]:
        """Extract configuration from environment variables"""
        config: Dict[str, Any] = {}
        
        for env_var, config_path in self.mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(value)
                self._set_nested_value(config, config_path, converted_value)
                logger.debug(f"Environment variable {env_var} -> {config_path} = {converted_value}")
        
        return config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        
        # Number conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested configuration value using dot notation"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


class ConfigurationLoader:
    """Multi-source configuration loader with priority-based merging"""
    
    def __init__(self, 
                 schema: ConfigurationSchema,
                 validation_level: ValidationLevel = ValidationLevel.NORMAL,
                 config_dir: Optional[Path] = None) -> None:
        self.schema = schema
        self.validator = ConfigurationValidator(schema, validation_level)
        self.env_mapper = EnvironmentVariableMapper()
        
        # Configuration directories
        if config_dir:
            self.user_config_dir = Path(config_dir)
        else:
            self.user_config_dir = Path.home() / ".vidtanium"
        
        self.system_config_dir = Path(__file__).parent.parent.parent.parent / "config"
        
        # Ensure user config directory exists
        self.user_config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_configuration(self, 
                          cli_args: Optional[argparse.Namespace] = None,
                          config_files: Optional[List[Path]] = None) -> LoadResult:
        """
        Load configuration from all sources with priority-based merging
        
        Args:
            cli_args: Parsed command-line arguments
            config_files: Additional configuration files to load
            
        Returns:
            LoadResult with merged configuration and metadata
        """
        errors = []
        warnings = []
        sources_used = []
        files_loaded = []
        
        # Start with default configuration
        config = self._get_default_config()
        sources_used.append(ConfigurationSource.DEFAULTS)
        
        # Load system configuration files
        system_files = self._discover_config_files(self.system_config_dir, ConfigurationSource.SYSTEM_CONFIG)
        for config_file in system_files:
            if self._load_config_file(config_file) and config_file.data is not None:
                config = self._merge_configs(config, config_file.data)
                files_loaded.append(config_file.path)
                if ConfigurationSource.SYSTEM_CONFIG not in sources_used:
                    sources_used.append(ConfigurationSource.SYSTEM_CONFIG)
        
        # Load user configuration files
        user_files = self._discover_config_files(self.user_config_dir, ConfigurationSource.USER_CONFIG)
        for config_file in user_files:
            if self._load_config_file(config_file) and config_file.data is not None:
                config = self._merge_configs(config, config_file.data)
                files_loaded.append(config_file.path)
                if ConfigurationSource.USER_CONFIG not in sources_used:
                    sources_used.append(ConfigurationSource.USER_CONFIG)
        
        # Load additional configuration files
        if config_files:
            for file_path in config_files:
                config_file = ConfigurationFile(
                    path=file_path,
                    format=self._detect_format(file_path),
                    source=ConfigurationSource.USER_CONFIG
                )
                if self._load_config_file(config_file) and config_file.data is not None:
                    config = self._merge_configs(config, config_file.data)
                    files_loaded.append(config_file.path)
                    if ConfigurationSource.USER_CONFIG not in sources_used:
                        sources_used.append(ConfigurationSource.USER_CONFIG)
        
        # Load environment variables
        env_config = self.env_mapper.get_env_config()
        if env_config:
            config = self._merge_configs(config, env_config)
            sources_used.append(ConfigurationSource.ENVIRONMENT)
        
        # Apply command-line arguments
        if cli_args:
            cli_config = self._extract_cli_config(cli_args)
            if cli_config:
                config = self._merge_configs(config, cli_config)
                sources_used.append(ConfigurationSource.COMMAND_LINE)
        
        # Validate final configuration
        is_valid, validation_errors, validation_warnings = self.validator.validate(config)
        errors.extend(validation_errors)
        warnings.extend(validation_warnings)
        
        return LoadResult(
            success=is_valid,
            config=config,
            errors=errors,
            warnings=warnings,
            sources_used=sources_used,
            files_loaded=files_loaded
        )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration from schema"""
        config: Dict[str, Any] = {}
        
        for section_name, section in self.schema.sections.items():
            section_config: Dict[str, Any] = {}
            
            for field_name, field in section.fields.items():
                section_config[field_name] = field.default
            
            config[section_name] = section_config
        
        return config
    
    def _discover_config_files(self, directory: Path, source: ConfigurationSource) -> List[ConfigurationFile]:
        """Discover configuration files in a directory"""
        config_files: List[ConfigurationFile] = []
        
        if not directory.exists():
            return config_files
        
        # Look for configuration files in order of preference
        file_patterns = [
            ("config.json", ConfigurationFormat.JSON),
            ("config.yaml", ConfigurationFormat.YAML),
            ("config.yml", ConfigurationFormat.YAML),
            ("config.toml", ConfigurationFormat.TOML),
        ]
        
        for filename, format_type in file_patterns:
            file_path = directory / filename
            config_file = ConfigurationFile(
                path=file_path,
                format=format_type,
                source=source,
                exists=file_path.exists(),
                readable=file_path.exists() and os.access(file_path, os.R_OK)
            )
            config_files.append(config_file)
        
        return config_files
    
    def _detect_format(self, file_path: Path) -> ConfigurationFormat:
        """Detect configuration file format from extension"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.json':
            return ConfigurationFormat.JSON
        elif suffix in ['.yaml', '.yml']:
            return ConfigurationFormat.YAML
        elif suffix == '.toml':
            return ConfigurationFormat.TOML
        else:
            # Default to JSON
            return ConfigurationFormat.JSON
    
    def _load_config_file(self, config_file: ConfigurationFile) -> bool:
        """Load configuration from file"""
        if not config_file.exists or not config_file.readable:
            return False
        
        try:
            with open(config_file.path, 'r', encoding='utf-8') as f:
                if config_file.format == ConfigurationFormat.JSON:
                    config_file.data = json.load(f)
                elif config_file.format == ConfigurationFormat.YAML:
                    config_file.data = yaml.safe_load(f)
                elif config_file.format == ConfigurationFormat.TOML:
                    config_file.data = toml.load(f)
            
            logger.info(f"Loaded configuration from {config_file.path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file.path}: {e}")
            return False
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries with override taking precedence"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _extract_cli_config(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Extract configuration overrides from command-line arguments"""
        config: Dict[str, Any] = {}
        
        # Map command-line arguments to configuration paths
        if hasattr(args, 'debug') and args.debug:
            self._set_nested_config(config, 'logging.debug_logging', True)
            self._set_nested_config(config, 'logging.log_level', 'DEBUG')
        
        if hasattr(args, 'output_dir') and args.output_dir:
            self._set_nested_config(config, 'general.output_directory', args.output_dir)
        
        if hasattr(args, 'max_concurrent') and args.max_concurrent:
            self._set_nested_config(config, 'download.max_concurrent_tasks', args.max_concurrent)
        
        if hasattr(args, 'proxy') and args.proxy:
            self._set_nested_config(config, 'network.proxy', args.proxy)
        
        if hasattr(args, 'theme') and args.theme:
            self._set_nested_config(config, 'general.theme', args.theme)
        
        return config
    
    def _set_nested_config(self, config: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested configuration value using dot notation"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value

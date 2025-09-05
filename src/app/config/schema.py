"""
Configuration Schema System

Provides JSON Schema-based validation and configuration structure definitions.
"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class ConfigurationType(Enum):
    """Types of configuration values"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    PATH = "path"
    URL = "url"
    EMAIL = "email"


class ValidationLevel(Enum):
    """Configuration validation levels"""
    STRICT = "strict"      # All validation errors are fatal
    NORMAL = "normal"      # Most validation errors are fatal, some warnings
    PERMISSIVE = "permissive"  # Only critical errors are fatal, many warnings


@dataclass
class ConfigurationField:
    """Definition of a configuration field"""
    name: str
    type: ConfigurationType
    default: Any
    description: str = ""
    required: bool = False
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    deprecated: bool = False
    migration_path: Optional[str] = None
    validation_function: Optional[Callable[[Any], bool]] = None


@dataclass
class ConfigurationSection:
    """Definition of a configuration section"""
    name: str
    description: str
    fields: Dict[str, ConfigurationField] = field(default_factory=dict)
    subsections: Dict[str, 'ConfigurationSection'] = field(default_factory=dict)
    required: bool = False
    deprecated: bool = False


class ConfigurationSchema:
    """Enhanced configuration schema with JSON Schema validation"""
    
    def __init__(self, schema_version: str = "2.0.0"):
        self.schema_version = schema_version
        self.sections: Dict[str, ConfigurationSection] = {}
        self._json_schema: Optional[Dict[str, Any]] = None
        self._validator: Optional[jsonschema.Draft7Validator] = None
        
        # Initialize default schema
        self._initialize_default_schema()
    
    def _initialize_default_schema(self) -> None:
        """Initialize the default configuration schema"""
        
        # General section
        general_section = ConfigurationSection(
            name="general",
            description="General application settings",
            required=True
        )
        
        general_section.fields.update({
            "output_directory": ConfigurationField(
                name="output_directory",
                type=ConfigurationType.PATH,
                default=str(Path.home() / "Downloads"),
                description="Default download directory",
                required=True
            ),
            "auto_cleanup": ConfigurationField(
                name="auto_cleanup",
                type=ConfigurationType.BOOLEAN,
                default=True,
                description="Automatically clean up temporary files"
            ),
            "language": ConfigurationField(
                name="language",
                type=ConfigurationType.STRING,
                default="auto",
                description="Application language",
                enum_values=["auto", "en_US", "zh_CN"]
            ),
            "theme": ConfigurationField(
                name="theme",
                type=ConfigurationType.STRING,
                default="system",
                description="Application theme",
                enum_values=["system", "light", "dark"]
            ),
            "check_updates": ConfigurationField(
                name="check_updates",
                type=ConfigurationType.BOOLEAN,
                default=True,
                description="Check for application updates on startup"
            ),
            "max_recent_files": ConfigurationField(
                name="max_recent_files",
                type=ConfigurationType.INTEGER,
                default=10,
                description="Maximum number of recent files to remember",
                min_value=0,
                max_value=100
            ),
            "temp_directory": ConfigurationField(
                name="temp_directory",
                type=ConfigurationType.PATH,
                default="",
                description="Temporary files directory (empty for system default)"
            ),
            "cache_directory": ConfigurationField(
                name="cache_directory",
                type=ConfigurationType.PATH,
                default="",
                description="Cache directory (empty for default)"
            ),
            "backup_directory": ConfigurationField(
                name="backup_directory",
                type=ConfigurationType.PATH,
                default="",
                description="Configuration backup directory"
            ),
            "config_auto_save": ConfigurationField(
                name="config_auto_save",
                type=ConfigurationType.BOOLEAN,
                default=True,
                description="Automatically save configuration changes"
            ),
            "config_backup_count": ConfigurationField(
                name="config_backup_count",
                type=ConfigurationType.INTEGER,
                default=5,
                description="Number of configuration backups to keep",
                min_value=0,
                max_value=50
            )
        })
        
        self.sections["general"] = general_section
        
        # Download section
        download_section = ConfigurationSection(
            name="download",
            description="Download behavior settings",
            required=True
        )
        
        download_section.fields.update({
            "max_concurrent_tasks": ConfigurationField(
                name="max_concurrent_tasks",
                type=ConfigurationType.INTEGER,
                default=3,
                description="Maximum number of concurrent download tasks",
                min_value=1,
                max_value=20
            ),
            "max_workers_per_task": ConfigurationField(
                name="max_workers_per_task",
                type=ConfigurationType.INTEGER,
                default=10,
                description="Maximum number of workers per download task",
                min_value=1,
                max_value=50
            ),
            "max_retries": ConfigurationField(
                name="max_retries",
                type=ConfigurationType.INTEGER,
                default=5,
                description="Maximum number of retry attempts",
                min_value=0,
                max_value=20
            ),
            "retry_delay": ConfigurationField(
                name="retry_delay",
                type=ConfigurationType.NUMBER,
                default=2.0,
                description="Base delay between retry attempts (seconds)",
                min_value=0.1,
                max_value=60.0
            ),
            "request_timeout": ConfigurationField(
                name="request_timeout",
                type=ConfigurationType.INTEGER,
                default=60,
                description="HTTP request timeout (seconds)",
                min_value=5,
                max_value=300
            ),
            "chunk_size": ConfigurationField(
                name="chunk_size",
                type=ConfigurationType.INTEGER,
                default=8192,
                description="Download chunk size (bytes)",
                min_value=1024,
                max_value=1048576
            ),
            "bandwidth_limit": ConfigurationField(
                name="bandwidth_limit",
                type=ConfigurationType.INTEGER,
                default=0,
                description="Bandwidth limit in KB/s (0 for unlimited)",
                min_value=0
            )
        })
        
        self.sections["download"] = download_section

        # Network section
        network_section = ConfigurationSection(
            name="network",
            description="Network and connection settings"
        )

        network_section.fields.update({
            "connection_pool_size": ConfigurationField(
                name="connection_pool_size",
                type=ConfigurationType.INTEGER,
                default=20,
                description="Maximum connections in pool",
                min_value=5,
                max_value=100
            ),
            "max_connections_per_host": ConfigurationField(
                name="max_connections_per_host",
                type=ConfigurationType.INTEGER,
                default=8,
                description="Maximum connections per host",
                min_value=1,
                max_value=20
            ),
            "connection_timeout": ConfigurationField(
                name="connection_timeout",
                type=ConfigurationType.NUMBER,
                default=30.0,
                description="Connection timeout (seconds)",
                min_value=1.0,
                max_value=120.0
            ),
            "read_timeout": ConfigurationField(
                name="read_timeout",
                type=ConfigurationType.NUMBER,
                default=120.0,
                description="Read timeout (seconds)",
                min_value=5.0,
                max_value=600.0
            ),
            "dns_cache_timeout": ConfigurationField(
                name="dns_cache_timeout",
                type=ConfigurationType.INTEGER,
                default=300,
                description="DNS cache timeout (seconds)",
                min_value=0,
                max_value=3600
            ),
            "keep_alive_timeout": ConfigurationField(
                name="keep_alive_timeout",
                type=ConfigurationType.NUMBER,
                default=300.0,
                description="Keep-alive timeout (seconds)",
                min_value=10.0,
                max_value=1800.0
            ),
            "proxy": ConfigurationField(
                name="proxy",
                type=ConfigurationType.STRING,
                default="",
                description="Proxy server URL (empty for no proxy)"
            ),
            "user_agent": ConfigurationField(
                name="user_agent",
                type=ConfigurationType.STRING,
                default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                description="HTTP User-Agent string"
            ),
            "verify_ssl": ConfigurationField(
                name="verify_ssl",
                type=ConfigurationType.BOOLEAN,
                default=True,
                description="Verify SSL certificates"
            )
        })

        self.sections["network"] = network_section

        # Performance section
        performance_section = ConfigurationSection(
            name="performance",
            description="Performance optimization settings"
        )

        performance_section.fields.update({
            "memory_limit_mb": ConfigurationField(
                name="memory_limit_mb",
                type=ConfigurationType.INTEGER,
                default=1024,
                description="Memory usage limit in MB (0 for unlimited)",
                min_value=0,
                max_value=16384
            ),
            "cpu_usage_limit": ConfigurationField(
                name="cpu_usage_limit",
                type=ConfigurationType.INTEGER,
                default=80,
                description="CPU usage limit percentage",
                min_value=10,
                max_value=100
            ),
            "buffer_size_min": ConfigurationField(
                name="buffer_size_min",
                type=ConfigurationType.INTEGER,
                default=8192,
                description="Minimum buffer size (bytes)",
                min_value=1024,
                max_value=65536
            ),
            "buffer_size_max": ConfigurationField(
                name="buffer_size_max",
                type=ConfigurationType.INTEGER,
                default=1048576,
                description="Maximum buffer size (bytes)",
                min_value=65536,
                max_value=10485760
            ),
            "buffer_size_default": ConfigurationField(
                name="buffer_size_default",
                type=ConfigurationType.INTEGER,
                default=65536,
                description="Default buffer size (bytes)",
                min_value=8192,
                max_value=1048576
            ),
            "gc_threshold_mb": ConfigurationField(
                name="gc_threshold_mb",
                type=ConfigurationType.INTEGER,
                default=100,
                description="Garbage collection threshold (MB)",
                min_value=10,
                max_value=1000
            ),
            "optimization_level": ConfigurationField(
                name="optimization_level",
                type=ConfigurationType.STRING,
                default="balanced",
                description="Performance optimization level",
                enum_values=["low", "balanced", "high", "maximum"]
            )
        })

        self.sections["performance"] = performance_section

        # Logging section
        logging_section = ConfigurationSection(
            name="logging",
            description="Logging and debug settings"
        )

        logging_section.fields.update({
            "log_level": ConfigurationField(
                name="log_level",
                type=ConfigurationType.STRING,
                default="INFO",
                description="Global log level",
                enum_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            ),
            "debug_logging": ConfigurationField(
                name="debug_logging",
                type=ConfigurationType.BOOLEAN,
                default=False,
                description="Enable debug logging"
            ),
            "log_to_file": ConfigurationField(
                name="log_to_file",
                type=ConfigurationType.BOOLEAN,
                default=True,
                description="Enable logging to file"
            ),
            "log_to_console": ConfigurationField(
                name="log_to_console",
                type=ConfigurationType.BOOLEAN,
                default=True,
                description="Enable logging to console"
            ),
            "log_file_path": ConfigurationField(
                name="log_file_path",
                type=ConfigurationType.PATH,
                default="",
                description="Log file path (empty for default)"
            ),
            "log_rotation_size": ConfigurationField(
                name="log_rotation_size",
                type=ConfigurationType.STRING,
                default="10 MB",
                description="Log file rotation size"
            ),
            "log_retention": ConfigurationField(
                name="log_retention",
                type=ConfigurationType.STRING,
                default="7 days",
                description="Log file retention period"
            ),
            "log_compression": ConfigurationField(
                name="log_compression",
                type=ConfigurationType.STRING,
                default="zip",
                description="Log file compression format",
                enum_values=["none", "zip", "gz"]
            )
        })

        self.sections["logging"] = logging_section

    def add_section(self, section: ConfigurationSection) -> None:
        """Add a configuration section"""
        self.sections[section.name] = section
        self._json_schema = None  # Reset cached schema
        self._validator = None
    
    def get_json_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema from configuration definition"""
        if self._json_schema is None:
            self._json_schema = self._generate_json_schema()
        return self._json_schema
    
    def _generate_json_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema dictionary"""
        schema: Dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "VidTanium Configuration",
            "description": "Configuration schema for VidTanium application",
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for section_name, section in self.sections.items():
            section_schema = self._generate_section_schema(section)
            schema["properties"][section_name] = section_schema
            
            if section.required:
                schema["required"].append(section_name)
        
        return schema
    
    def _generate_section_schema(self, section: ConfigurationSection) -> Dict[str, Any]:
        """Generate schema for a configuration section"""
        section_schema: Dict[str, Any] = {
            "type": "object",
            "description": section.description,
            "properties": {},
            "required": []
        }
        
        for field_name, field in section.fields.items():
            field_schema = self._generate_field_schema(field)
            section_schema["properties"][field_name] = field_schema
            
            if field.required:
                section_schema["required"].append(field_name)
        
        for subsection_name, subsection in section.subsections.items():
            subsection_schema = self._generate_section_schema(subsection)
            section_schema["properties"][subsection_name] = subsection_schema
            
            if subsection.required:
                section_schema["required"].append(subsection_name)
        
        return section_schema
    
    def _generate_field_schema(self, field: ConfigurationField) -> Dict[str, Any]:
        """Generate schema for a configuration field"""
        field_schema = {
            "description": field.description,
            "default": field.default
        }
        
        # Set type
        if field.type == ConfigurationType.STRING:
            field_schema["type"] = "string"
        elif field.type == ConfigurationType.INTEGER:
            field_schema["type"] = "integer"
        elif field.type == ConfigurationType.NUMBER:
            field_schema["type"] = "number"
        elif field.type == ConfigurationType.BOOLEAN:
            field_schema["type"] = "boolean"
        elif field.type == ConfigurationType.ARRAY:
            field_schema["type"] = "array"
        elif field.type == ConfigurationType.OBJECT:
            field_schema["type"] = "object"
        elif field.type == ConfigurationType.PATH:
            field_schema["type"] = "string"
            field_schema["format"] = "path"
        elif field.type == ConfigurationType.URL:
            field_schema["type"] = "string"
            field_schema["format"] = "uri"
        elif field.type == ConfigurationType.EMAIL:
            field_schema["type"] = "string"
            field_schema["format"] = "email"
        
        # Add constraints
        if field.min_value is not None:
            field_schema["minimum"] = field.min_value
        if field.max_value is not None:
            field_schema["maximum"] = field.max_value
        if field.min_length is not None:
            field_schema["minLength"] = field.min_length
        if field.max_length is not None:
            field_schema["maxLength"] = field.max_length
        if field.pattern is not None:
            field_schema["pattern"] = field.pattern
        if field.enum_values is not None:
            field_schema["enum"] = field.enum_values
        
        return field_schema


class ConfigurationValidator:
    """Configuration validator using JSON Schema"""
    
    def __init__(self, schema: ConfigurationSchema, validation_level: ValidationLevel = ValidationLevel.NORMAL):
        self.schema = schema
        self.validation_level = validation_level
        self._validator: Optional[jsonschema.Draft7Validator] = None
    
    def get_validator(self) -> jsonschema.Draft7Validator:
        """Get JSON Schema validator"""
        if self._validator is None:
            json_schema = self.schema.get_json_schema()
            self._validator = jsonschema.Draft7Validator(json_schema)
        return self._validator
    
    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate configuration
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        validator = self.get_validator()
        errors = []
        warnings = []
        
        # JSON Schema validation
        schema_errors = list(validator.iter_errors(config))
        for error in schema_errors:
            error_msg = f"Schema validation error at {'.'.join(str(p) for p in error.absolute_path)}: {error.message}"
            
            if self.validation_level == ValidationLevel.PERMISSIVE:
                warnings.append(error_msg)
            else:
                errors.append(error_msg)
        
        # Custom field validation
        custom_errors, custom_warnings = self._validate_custom_fields(config)
        errors.extend(custom_errors)
        warnings.extend(custom_warnings)
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def _validate_custom_fields(self, config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate fields with custom validation functions"""
        errors: List[str] = []
        warnings: List[str] = []
        
        for section_name, section in self.schema.sections.items():
            if section_name not in config:
                continue
                
            section_config = config[section_name]
            for field_name, field in section.fields.items():
                if field.validation_function and field_name in section_config:
                    try:
                        if not field.validation_function(section_config[field_name]):
                            error_msg = f"Custom validation failed for {section_name}.{field_name}"
                            errors.append(error_msg)
                    except Exception as e:
                        error_msg = f"Custom validation error for {section_name}.{field_name}: {e}"
                        errors.append(error_msg)
        
        return errors, warnings

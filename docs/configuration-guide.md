# VidTanium Configuration Guide

This guide covers the enhanced configuration system in VidTanium 2.0, which provides comprehensive customization options, configuration presets, feature flags, and advanced management tools.

## Overview

VidTanium's enhanced configuration system supports:

- **Multi-source configuration loading** with priority-based merging
- **Configuration presets** for common use cases
- **Feature flags** for enabling/disabling functionality
- **Environment variable support** for deployment scenarios
- **Command-line overrides** for runtime customization
- **Configuration validation** and error handling
- **Automatic migration** from older configuration formats
- **Backup and restore** capabilities

## Configuration Sources

Configuration is loaded from multiple sources in the following priority order (highest to lowest):

1. **Command-line arguments** (highest priority)
2. **Environment variables** (with `VIDTANIUM_` prefix)
3. **User configuration files** (`~/.vidtanium/config.json`)
4. **System configuration files** (`config/config.json`)
5. **Default values** (lowest priority)

## Configuration File Locations

### User Configuration
- **Windows**: `%USERPROFILE%\.vidtanium\config.json`
- **macOS**: `~/.vidtanium/config.json`
- **Linux**: `~/.vidtanium/config.json`

### System Configuration
- Located in the application's `config/` directory
- Used for system-wide defaults and presets

## Configuration Sections

### General Settings (`general`)

Basic application settings:

```json
{
  "general": {
    "output_directory": "~/Downloads",
    "auto_cleanup": true,
    "language": "auto",
    "theme": "system",
    "check_updates": true,
    "max_recent_files": 10,
    "temp_directory": "",
    "cache_directory": "",
    "backup_directory": "",
    "config_auto_save": true,
    "config_backup_count": 5
  }
}
```

### Download Settings (`download`)

Download behavior configuration:

```json
{
  "download": {
    "max_concurrent_tasks": 3,
    "max_workers_per_task": 10,
    "max_retries": 5,
    "retry_delay": 2.0,
    "request_timeout": 60,
    "chunk_size": 8192,
    "bandwidth_limit": 0
  }
}
```

### Network Settings (`network`)

Network and connection configuration:

```json
{
  "network": {
    "connection_pool_size": 20,
    "max_connections_per_host": 8,
    "connection_timeout": 30.0,
    "read_timeout": 120.0,
    "dns_cache_timeout": 300,
    "keep_alive_timeout": 300.0,
    "proxy": "",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "verify_ssl": true
  }
}
```

### Performance Settings (`performance`)

Performance optimization configuration:

```json
{
  "performance": {
    "memory_limit_mb": 1024,
    "cpu_usage_limit": 80,
    "buffer_size_min": 8192,
    "buffer_size_max": 1048576,
    "buffer_size_default": 65536,
    "gc_threshold_mb": 100,
    "optimization_level": "balanced"
  }
}
```

### Logging Settings (`logging`)

Logging and debug configuration:

```json
{
  "logging": {
    "log_level": "INFO",
    "debug_logging": false,
    "log_to_file": true,
    "log_to_console": true,
    "log_file_path": "",
    "log_rotation_size": "10 MB",
    "log_retention": "7 days",
    "log_compression": "zip"
  }
}
```

### Feature Flags (`features`)

Feature enable/disable configuration:

```json
{
  "features": {
    "adaptive_retry": true,
    "adaptive_timeout": true,
    "integrity_verification": true,
    "memory_optimization": true,
    "connection_pooling": true,
    "enhanced_theme_system": true,
    "system_tray": true,
    "notifications": true,
    "dark_mode": true,
    "parallel_downloads": true,
    "bandwidth_limiting": false,
    "resume_downloads": true
  }
}
```

### UI Settings (`ui`)

User interface configuration:

```json
{
  "ui": {
    "show_detailed_progress": true,
    "minimize_to_tray": false,
    "show_notifications": true,
    "confirm_on_exit": true,
    "window_geometry": "",
    "window_state": "",
    "accent_color": "#0078d4",
    "animations_enabled": true
  }
}
```

## Environment Variables

All configuration options can be overridden using environment variables with the `VIDTANIUM_` prefix:

```bash
# General settings
export VIDTANIUM_OUTPUT_DIR="/path/to/downloads"
export VIDTANIUM_THEME="dark"
export VIDTANIUM_LANGUAGE="en_US"

# Download settings
export VIDTANIUM_MAX_CONCURRENT="5"
export VIDTANIUM_MAX_WORKERS="15"
export VIDTANIUM_CHUNK_SIZE="16384"

# Network settings
export VIDTANIUM_PROXY="http://proxy.example.com:8080"
export VIDTANIUM_USER_AGENT="Custom-Agent/1.0"
export VIDTANIUM_CONNECTION_TIMEOUT="45"

# Performance settings
export VIDTANIUM_MEMORY_LIMIT="2048"
export VIDTANIUM_CPU_LIMIT="90"
export VIDTANIUM_OPTIMIZATION="high"

# Logging settings
export VIDTANIUM_LOG_LEVEL="DEBUG"
export VIDTANIUM_DEBUG="true"

# Feature flags
export VIDTANIUM_FEATURES="adaptive_retry,parallel_downloads,notifications"
```

## Command-Line Arguments

Override configuration options at runtime:

```bash
# Basic options
python main.py --debug --log-level DEBUG
python main.py --output-dir "/custom/path"
python main.py --theme dark --max-concurrent 5

# Configuration management
python main.py --list-presets
python main.py --preset high_performance
python main.py --validate-config
python main.py --export-config config_backup.json
python main.py --import-config custom_config.json
python main.py --reset-config
python main.py --backup-config

# Feature management
python main.py --list-features
python main.py --enable-features adaptive_retry parallel_downloads
python main.py --disable-features system_tray notifications

# Debug and development
python main.py --debug-modules downloader network
python main.py --performance-profile
python main.py --config-report
```

## Configuration Presets

VidTanium includes several built-in presets for common use cases:

### Available Presets

1. **production** - Stable configuration for production use
2. **high_performance** - Optimized for maximum speed and performance
3. **low_resource** - Optimized for systems with limited resources
4. **development** - Optimized for development and debugging

### Using Presets

```bash
# List available presets
python main.py --list-presets

# Apply a preset
python main.py --preset high_performance

# Apply preset programmatically
from src.app.settings import Settings
settings = Settings()
settings.apply_preset("high_performance")
```

### Creating Custom Presets

Create custom presets in `~/.vidtanium/presets/`:

```json
{
  "name": "my_custom_preset",
  "description": "My custom configuration",
  "preset_type": "user",
  "author": "Your Name",
  "version": "1.0.0",
  "tags": ["custom", "personal"],
  "config": {
    "_version": "2.0.0",
    "general": {
      "output_directory": "/my/custom/path",
      "theme": "dark"
    },
    "download": {
      "max_concurrent_tasks": 5,
      "chunk_size": 16384
    }
  }
}
```

## Feature Flags

Control application functionality with feature flags:

### Core Features
- `adaptive_retry` - Intelligent retry mechanism
- `adaptive_timeout` - Dynamic timeout adjustment
- `integrity_verification` - File integrity checking
- `memory_optimization` - Advanced memory management
- `connection_pooling` - Connection pool management

### UI Features
- `enhanced_theme_system` - Advanced theming
- `system_tray` - System tray integration
- `notifications` - Desktop notifications
- `dark_mode` - Dark theme support

### Performance Features
- `parallel_downloads` - Parallel segment downloading
- `bandwidth_limiting` - Bandwidth throttling
- `resume_downloads` - Resume interrupted downloads

### Managing Features

```bash
# List all features
python main.py --list-features

# Enable specific features
python main.py --enable-features adaptive_retry parallel_downloads

# Disable specific features
python main.py --disable-features system_tray notifications
```

## Configuration Validation

VidTanium validates configuration automatically:

```bash
# Validate current configuration
python main.py --validate-config

# Generate configuration report
python main.py --config-report
```

## Backup and Restore

### Creating Backups

```bash
# Create manual backup
python main.py --backup-config

# Programmatic backup
from src.app.settings import Settings
settings = Settings()
settings.create_backup("Before major changes")
```

### Automatic Backups

- Automatic backups are created before configuration migration
- Configurable backup retention (default: 5 backups)
- Backups stored in `~/.vidtanium/backups/`

## Migration

VidTanium automatically migrates older configuration formats:

- Detects configuration version
- Creates backup before migration
- Applies necessary transformations
- Validates migrated configuration
- Reports migration results

## Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check file permissions
   - Validate JSON syntax
   - Review error logs

2. **Environment variables not working**
   - Verify variable names (case-sensitive)
   - Check variable values and types
   - Ensure proper export in shell

3. **Preset not applying**
   - Verify preset file exists
   - Check preset file format
   - Review preset validation errors

### Debug Configuration

```bash
# Enable debug logging
python main.py --debug --log-level DEBUG

# Generate configuration report
python main.py --config-report

# Validate configuration
python main.py --validate-config
```

## Best Practices

1. **Use presets** for common configurations
2. **Create backups** before major changes
3. **Validate configuration** after modifications
4. **Use environment variables** for deployment-specific settings
5. **Test configuration changes** in development first
6. **Monitor logs** for configuration-related issues
7. **Keep backups** of working configurations

## Advanced Usage

### Programmatic Configuration Management

```python
from src.app.settings import Settings
from src.app.config import ConfigurationTools, PresetManager

# Initialize settings with enhanced system
settings = Settings(use_new_system=True)

# Apply preset
settings.apply_preset("high_performance")

# Enable/disable features
settings.enable_feature("parallel_downloads")
settings.disable_feature("system_tray")

# Validate configuration
is_valid, errors, warnings = settings.validate_configuration()

# Create backup
settings.create_backup("Before performance tuning")

# Export configuration
settings.export_configuration(Path("my_config.json"), format="json")
```

### Custom Configuration Validation

```python
from src.app.config.schema import ConfigurationField, ConfigurationType

# Define custom field
custom_field = ConfigurationField(
    name="custom_timeout",
    type=ConfigurationType.INTEGER,
    default=30,
    description="Custom timeout value",
    min_value=5,
    max_value=300,
    validation_function=lambda x: x % 5 == 0  # Must be multiple of 5
)

# Add to schema
settings.schema.sections["network"].fields["custom_timeout"] = custom_field
```

### Environment-Specific Configuration

```bash
# Development environment
export VIDTANIUM_PRESET="development"
export VIDTANIUM_LOG_LEVEL="DEBUG"
export VIDTANIUM_DEBUG="true"

# Production environment
export VIDTANIUM_PRESET="production"
export VIDTANIUM_LOG_LEVEL="INFO"
export VIDTANIUM_DEBUG="false"
export VIDTANIUM_OUTPUT_DIR="/var/downloads"

# High-performance environment
export VIDTANIUM_PRESET="high_performance"
export VIDTANIUM_MAX_CONCURRENT="8"
export VIDTANIUM_MEMORY_LIMIT="4096"
export VIDTANIUM_OPTIMIZATION="maximum"
```

## Configuration Schema Reference

The complete configuration schema is available in `config/schema/base_schema.json`. Key validation rules:

- **String fields**: Support pattern matching and length constraints
- **Integer fields**: Support min/max value constraints
- **Boolean fields**: Accept true/false or 1/0 values
- **Path fields**: Automatically resolve relative paths
- **Enum fields**: Restrict values to predefined options

## Migration Guide

### From Version 1.x to 2.0

The enhanced configuration system automatically migrates 1.x configurations:

1. **Backup creation**: Automatic backup before migration
2. **Section restructuring**: Settings reorganized into logical sections
3. **New features**: Feature flags and performance settings added
4. **Validation**: Migrated configuration validated against new schema

### Manual Migration Steps

If automatic migration fails:

1. **Export old configuration**:
   ```bash
   python main.py --export-config old_config_backup.json
   ```

2. **Reset to defaults**:
   ```bash
   python main.py --reset-config
   ```

3. **Apply appropriate preset**:
   ```bash
   python main.py --preset production
   ```

4. **Customize as needed** using the new configuration options

## Performance Tuning

### High-Performance Configuration

```json
{
  "download": {
    "max_concurrent_tasks": 8,
    "max_workers_per_task": 20,
    "chunk_size": 65536
  },
  "network": {
    "connection_pool_size": 50,
    "max_connections_per_host": 15,
    "connection_timeout": 15.0
  },
  "performance": {
    "memory_limit_mb": 2048,
    "cpu_usage_limit": 90,
    "optimization_level": "maximum"
  }
}
```

### Low-Resource Configuration

```json
{
  "download": {
    "max_concurrent_tasks": 1,
    "max_workers_per_task": 3,
    "chunk_size": 4096
  },
  "network": {
    "connection_pool_size": 5,
    "max_connections_per_host": 2
  },
  "performance": {
    "memory_limit_mb": 256,
    "cpu_usage_limit": 50,
    "optimization_level": "low"
  }
}
```

## Security Considerations

1. **SSL Verification**: Keep `verify_ssl` enabled in production
2. **Proxy Settings**: Secure proxy credentials properly
3. **File Permissions**: Restrict configuration file access
4. **Backup Security**: Secure configuration backups
5. **Environment Variables**: Avoid sensitive data in environment variables

## Support and Troubleshooting

For configuration-related issues:

1. **Check logs** for detailed error messages
2. **Validate configuration** using built-in tools
3. **Test with default settings** to isolate issues
4. **Review documentation** for correct syntax and options
5. **Create minimal reproduction** for complex issues

## Configuration Validation

VidTanium validates configuration automatically:

```bash
# Validate current configuration
python main.py --validate-config

# Generate configuration report
python main.py --config-report
```

## Backup and Restore

### Creating Backups

```bash
# Create manual backup
python main.py --backup-config

# Programmatic backup
from src.app.settings import Settings
settings = Settings()
settings.create_backup("Before major changes")
```

### Automatic Backups

- Automatic backups are created before configuration migration
- Configurable backup retention (default: 5 backups)
- Backups stored in `~/.vidtanium/backups/`

## Migration

VidTanium automatically migrates older configuration formats:

- Detects configuration version
- Creates backup before migration
- Applies necessary transformations
- Validates migrated configuration
- Reports migration results

## Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check file permissions
   - Validate JSON syntax
   - Review error logs

2. **Environment variables not working**
   - Verify variable names (case-sensitive)
   - Check variable values and types
   - Ensure proper export in shell

3. **Preset not applying**
   - Verify preset file exists
   - Check preset file format
   - Review preset validation errors

### Debug Configuration

```bash
# Enable debug logging
python main.py --debug --log-level DEBUG

# Generate configuration report
python main.py --config-report

# Validate configuration
python main.py --validate-config
```

## Best Practices

1. **Use presets** for common configurations
2. **Create backups** before major changes
3. **Validate configuration** after modifications
4. **Use environment variables** for deployment-specific settings
5. **Test configuration changes** in development first
6. **Monitor logs** for configuration-related issues
7. **Keep backups** of working configurations

# VidTanium Enhanced Configuration System

## Overview

VidTanium 2.0 introduces a comprehensive configuration system that provides unprecedented flexibility and control over application behavior. This system is designed to support various deployment scenarios, from personal use to enterprise environments.

## Key Features

### 🔧 Multi-Source Configuration Loading
- **Priority-based merging** from multiple sources
- **Command-line arguments** (highest priority)
- **Environment variables** with `VIDTANIUM_` prefix
- **User configuration files** (`~/.vidtanium/config.json`)
- **System configuration files** (`config/config.json`)
- **Default values** (lowest priority)

### 📋 Configuration Presets
- **Built-in presets** for common use cases:
  - `production` - Stable, balanced settings
  - `high_performance` - Maximum speed optimization
  - `low_resource` - Minimal resource usage
  - `development` - Debug and development features
- **Custom presets** support
- **Easy preset switching** via CLI or API

### 🚩 Feature Flags System
- **Centralized feature control** for all application functionality
- **Runtime enable/disable** of features
- **Dependency management** between features
- **Experimental feature support**
- **Graceful degradation** when features are disabled

### ✅ Advanced Validation
- **JSON Schema-based validation** with detailed error reporting
- **Custom validation functions** for complex rules
- **Configuration health checks**
- **Automatic error recovery** with fallback to defaults

### 🔄 Configuration Migration
- **Automatic migration** from older configuration formats
- **Version tracking** and compatibility handling
- **Backup creation** before migration
- **Rollback support** if migration fails

### 🛠️ Management Tools
- **Export/Import** configurations in multiple formats (JSON, YAML)
- **Configuration comparison** and diff tools
- **Backup and restore** functionality
- **Configuration reporting** and diagnostics

## Quick Start

### 1. Using Presets

```bash
# List available presets
python main.py --list-presets

# Apply a preset
python main.py --preset high_performance
```

### 2. Environment Variables

```bash
# Set common configuration via environment
export VIDTANIUM_OUTPUT_DIR="/downloads"
export VIDTANIUM_MAX_CONCURRENT="5"
export VIDTANIUM_THEME="dark"
export VIDTANIUM_LOG_LEVEL="INFO"

# Run application
python main.py
```

### 3. Command-Line Overrides

```bash
# Override specific settings
python main.py --output-dir "/custom/path" --max-concurrent 8 --theme dark
```

### 4. Feature Management

```bash
# List all features
python main.py --list-features

# Enable/disable features
python main.py --enable-features parallel_downloads adaptive_retry
python main.py --disable-features system_tray notifications
```

## Configuration Sections

### General Settings
- Application-wide settings like output directory, language, theme
- Cleanup and maintenance options
- Update checking and file history

### Download Settings
- Concurrent task limits and worker configuration
- Retry behavior and timeout settings
- Chunk sizes and bandwidth limiting

### Network Settings
- Connection pooling and timeout configuration
- Proxy and SSL settings
- DNS caching and keep-alive options

### Performance Settings
- Memory and CPU usage limits
- Buffer size optimization
- Garbage collection tuning
- Performance optimization levels

### Logging Settings
- Log levels and output destinations
- File rotation and retention policies
- Debug logging configuration

### Feature Flags
- Enable/disable application features
- Experimental feature access
- Module-specific controls

### UI Settings
- Interface behavior and appearance
- Window state and geometry
- Notification preferences
- Theme and animation settings

## Advanced Usage

### Programmatic Configuration

```python
from src.app.settings import Settings

# Initialize with enhanced system
settings = Settings(use_new_system=True)

# Apply preset
settings.apply_preset("high_performance")

# Manage features
settings.enable_feature("parallel_downloads")
settings.disable_feature("system_tray")

# Validate configuration
is_valid, errors, warnings = settings.validate_configuration()

# Create backup
settings.create_backup("Before performance tuning")
```

### Custom Presets

Create custom presets in `~/.vidtanium/presets/my_preset.json`:

```json
{
  "name": "my_custom_preset",
  "description": "My optimized configuration",
  "preset_type": "user",
  "config": {
    "_version": "2.0.0",
    "general": {
      "output_directory": "/my/downloads",
      "theme": "dark"
    },
    "download": {
      "max_concurrent_tasks": 6,
      "chunk_size": 32768
    },
    "features": {
      "parallel_downloads": true,
      "adaptive_retry": true,
      "system_tray": false
    }
  }
}
```

### Environment-Specific Deployment

```bash
# Development
export VIDTANIUM_PRESET="development"
export VIDTANIUM_LOG_LEVEL="DEBUG"
export VIDTANIUM_DEBUG="true"

# Production
export VIDTANIUM_PRESET="production"
export VIDTANIUM_OUTPUT_DIR="/var/downloads"
export VIDTANIUM_LOG_LEVEL="INFO"

# High-performance server
export VIDTANIUM_PRESET="high_performance"
export VIDTANIUM_MAX_CONCURRENT="12"
export VIDTANIUM_MEMORY_LIMIT="4096"
```

## Configuration Management

### Backup and Restore

```bash
# Create backup
python main.py --backup-config

# Export configuration
python main.py --export-config my_config.json

# Import configuration
python main.py --import-config my_config.json

# Reset to defaults
python main.py --reset-config
```

### Validation and Diagnostics

```bash
# Validate current configuration
python main.py --validate-config

# Generate detailed report
python main.py --config-report
```

## Migration from Version 1.x

The system automatically detects and migrates older configurations:

1. **Automatic detection** of configuration version
2. **Backup creation** before migration
3. **Schema transformation** to new format
4. **Validation** of migrated configuration
5. **Error reporting** if migration fails

## Best Practices

### 1. Use Presets for Base Configuration
Start with a preset that matches your use case, then customize as needed.

### 2. Environment Variables for Deployment
Use environment variables for deployment-specific settings like paths and limits.

### 3. Feature Flags for Gradual Rollouts
Use feature flags to gradually enable new functionality or disable problematic features.

### 4. Regular Backups
Create backups before making significant configuration changes.

### 5. Validation After Changes
Always validate configuration after manual edits.

### 6. Monitor Logs
Watch application logs for configuration-related warnings or errors.

## Troubleshooting

### Common Issues

1. **Configuration not loading**: Check file permissions and JSON syntax
2. **Environment variables ignored**: Verify variable names and export
3. **Preset not found**: Check preset file location and format
4. **Feature not working**: Verify feature is enabled and dependencies met

### Debug Steps

1. Enable debug logging: `--debug --log-level DEBUG`
2. Validate configuration: `--validate-config`
3. Generate report: `--config-report`
4. Check feature status: `--list-features`

## Architecture

The configuration system consists of several key components:

- **ConfigurationSchema**: Defines structure and validation rules
- **ConfigurationLoader**: Handles multi-source loading and merging
- **PresetManager**: Manages configuration presets and templates
- **FeatureFlagManager**: Controls feature enable/disable state
- **ConfigurationMigrator**: Handles version migration
- **ConfigurationTools**: Provides management utilities

## Future Enhancements

- **Web-based configuration interface**
- **Configuration templates for specific use cases**
- **Integration with external configuration management systems**
- **Real-time configuration updates without restart**
- **Configuration change notifications and webhooks**

## Support

For configuration-related issues:

1. Check the [Configuration Guide](configuration-guide.md)
2. Review application logs for error details
3. Use built-in validation and diagnostic tools
4. Create minimal reproduction cases for complex issues

The enhanced configuration system makes VidTanium highly adaptable to different environments and use cases while maintaining ease of use for basic scenarios.

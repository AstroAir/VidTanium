# Configuration Migration Guide

This guide helps you migrate from VidTanium 1.x configuration to the enhanced 2.0 configuration system.

## Overview

VidTanium 2.0 introduces a completely redesigned configuration system with:

- **Enhanced structure** with logical sections
- **New configuration options** for performance and features
- **Automatic migration** from 1.x configurations
- **Backward compatibility** for existing setups
- **Improved validation** and error handling

## Automatic Migration

### What Happens Automatically

When you first run VidTanium 2.0 with an existing 1.x configuration:

1. **Detection**: System detects old configuration format
2. **Backup**: Creates automatic backup of existing configuration
3. **Migration**: Transforms configuration to new format
4. **Validation**: Validates migrated configuration
5. **Reporting**: Shows migration results and any issues

### Migration Process

```bash
# First run with existing 1.x config
python main.py

# Output example:
# INFO: Configuration migration required
# INFO: Created configuration backup at ~/.vidtanium/backups/config_backup_20240101_120000.json
# INFO: Configuration migrated successfully from 1.0.0 to 2.0.0
# INFO: Migration changes: Added network section, Added performance section, ...
```

## Configuration Structure Changes

### Old Structure (1.x)

```json
{
  "general": {
    "output_directory": "~/Downloads",
    "auto_cleanup": true,
    "language": "auto",
    "theme": "system",
    "check_updates": true,
    "max_recent_files": 10
  },
  "download": {
    "max_concurrent_tasks": 3,
    "max_workers_per_task": 10,
    "max_retries": 5,
    "retry_delay": 2,
    "request_timeout": 60,
    "chunk_size": 8192,
    "bandwidth_limit": 0
  },
  "advanced": {
    "proxy": "",
    "user_agent": "Mozilla/5.0...",
    "verify_ssl": true,
    "ffmpeg_path": "",
    "keep_temp_files": false,
    "debug_logging": false
  },
  "ui": {
    "show_detailed_progress": true,
    "minimize_to_tray": false,
    "show_notifications": true,
    "confirm_on_exit": true,
    "window_geometry": "",
    "window_state": ""
  }
}
```

### New Structure (2.0)

```json
{
  "_version": "2.0.0",
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
  },
  "download": {
    "max_concurrent_tasks": 3,
    "max_workers_per_task": 10,
    "max_retries": 5,
    "retry_delay": 2.0,
    "request_timeout": 60,
    "chunk_size": 8192,
    "bandwidth_limit": 0
  },
  "network": {
    "connection_pool_size": 20,
    "max_connections_per_host": 8,
    "connection_timeout": 30.0,
    "read_timeout": 120.0,
    "dns_cache_timeout": 300,
    "keep_alive_timeout": 300.0,
    "proxy": "",
    "user_agent": "Mozilla/5.0...",
    "verify_ssl": true
  },
  "performance": {
    "memory_limit_mb": 1024,
    "cpu_usage_limit": 80,
    "buffer_size_min": 8192,
    "buffer_size_max": 1048576,
    "buffer_size_default": 65536,
    "gc_threshold_mb": 100,
    "optimization_level": "balanced"
  },
  "logging": {
    "log_level": "INFO",
    "debug_logging": false,
    "log_to_file": true,
    "log_to_console": true,
    "log_file_path": "",
    "log_rotation_size": "10 MB",
    "log_retention": "7 days",
    "log_compression": "zip"
  },
  "features": {
    "adaptive_retry": true,
    "adaptive_timeout": true,
    "integrity_verification": true,
    "memory_optimization": true,
    "connection_pooling": true,
    "enhanced_theme_system": true,
    "system_tray": true,
    "notifications": true,
    "parallel_downloads": true,
    "resume_downloads": true
  },
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

## Key Changes

### 1. New Sections Added

- **`network`**: Network and connection settings (moved from `advanced`)
- **`performance`**: Performance optimization settings (new)
- **`logging`**: Logging configuration (expanded from `advanced.debug_logging`)
- **`features`**: Feature flags for enabling/disabling functionality (new)

### 2. Settings Moved

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `advanced.proxy` | `network.proxy` | Moved to network section |
| `advanced.user_agent` | `network.user_agent` | Moved to network section |
| `advanced.verify_ssl` | `network.verify_ssl` | Moved to network section |
| `advanced.debug_logging` | `logging.debug_logging` | Expanded logging section |

### 3. Settings Removed

- `advanced.ffmpeg_path` → Moved to separate tool configuration
- `advanced.keep_temp_files` → Replaced by `general.auto_cleanup`

### 4. New Settings Added

#### General Section
- `temp_directory`: Custom temporary directory
- `cache_directory`: Custom cache directory
- `backup_directory`: Configuration backup directory
- `config_auto_save`: Automatic configuration saving
- `config_backup_count`: Number of backups to keep

#### Network Section
- `connection_pool_size`: Connection pool size
- `max_connections_per_host`: Per-host connection limit
- `connection_timeout`: Connection timeout
- `read_timeout`: Read timeout
- `dns_cache_timeout`: DNS cache duration
- `keep_alive_timeout`: Keep-alive timeout

#### Performance Section (All New)
- `memory_limit_mb`: Memory usage limit
- `cpu_usage_limit`: CPU usage limit
- `buffer_size_min/max/default`: Buffer size configuration
- `gc_threshold_mb`: Garbage collection threshold
- `optimization_level`: Performance optimization level

#### Logging Section
- `log_level`: Global log level
- `log_to_file/console`: Output destinations
- `log_file_path`: Custom log file path
- `log_rotation_size`: Log rotation size
- `log_retention`: Log retention period
- `log_compression`: Log compression format

#### Features Section (All New)
- Various feature flags for controlling functionality

#### UI Section
- `accent_color`: UI accent color
- `animations_enabled`: UI animations toggle

## Manual Migration Steps

If automatic migration fails or you want to migrate manually:

### 1. Backup Current Configuration

```bash
# Create backup of current config
cp ~/.vidtanium/config.json ~/.vidtanium/config_1x_backup.json
```

### 2. Export Current Settings

```bash
# Export current configuration
python main.py --export-config current_config_backup.json
```

### 3. Reset to Defaults

```bash
# Reset to 2.0 defaults
python main.py --reset-config
```

### 4. Apply Appropriate Preset

```bash
# Choose a preset that matches your usage
python main.py --preset production  # or high_performance, low_resource, development
```

### 5. Customize Settings

Manually adjust settings based on your old configuration:

```bash
# Set basic options
python main.py --output-dir "/your/download/path"
python main.py --max-concurrent 5
python main.py --theme dark

# Or edit config file directly
nano ~/.vidtanium/config.json
```

### 6. Validate Configuration

```bash
# Validate the new configuration
python main.py --validate-config
```

## Environment Variables Migration

### Old Environment Variables (1.x)

```bash
export VDT_OUTPUT_DIR="/downloads"
export VDT_MAX_CONCURRENT="3"
export VDT_DEBUG="true"
```

### New Environment Variables (2.0)

```bash
export VIDTANIUM_OUTPUT_DIR="/downloads"
export VIDTANIUM_MAX_CONCURRENT="3"
export VIDTANIUM_DEBUG="true"
export VIDTANIUM_LOG_LEVEL="DEBUG"
export VIDTANIUM_THEME="dark"
```

## Command-Line Arguments Migration

### Old Arguments (1.x)

```bash
python main.py --debug --config /path/to/config --url "https://example.com/video.m3u8"
```

### New Arguments (2.0)

```bash
python main.py --debug --config-dir /path/to/config --url "https://example.com/video.m3u8"

# Additional new options
python main.py --preset high_performance --log-level DEBUG --theme dark
```

## Feature Flags Migration

In 2.0, many features can be controlled via feature flags:

```bash
# Enable/disable features
python main.py --enable-features parallel_downloads adaptive_retry
python main.py --disable-features system_tray notifications

# List all available features
python main.py --list-features
```

## Troubleshooting Migration Issues

### Migration Fails

1. **Check logs** for detailed error messages
2. **Validate old config** syntax
3. **Try manual migration** steps
4. **Reset and reconfigure** if necessary

```bash
# Check migration logs
python main.py --debug --log-level DEBUG

# Validate old configuration
python -m json.tool ~/.vidtanium/config.json

# Manual reset if needed
python main.py --reset-config
```

### Settings Not Working

1. **Verify section names** match new structure
2. **Check data types** (some changed from int to float)
3. **Validate configuration** after changes

```bash
# Validate current configuration
python main.py --validate-config

# Generate configuration report
python main.py --config-report
```

### Performance Issues After Migration

1. **Check performance settings** in new section
2. **Adjust optimization level**
3. **Review feature flags**

```bash
# Apply high-performance preset
python main.py --preset high_performance

# Or adjust specific settings
export VIDTANIUM_OPTIMIZATION="maximum"
export VIDTANIUM_MEMORY_LIMIT="2048"
```

## Post-Migration Recommendations

### 1. Review New Features

Explore new configuration options:
- Performance optimization levels
- Feature flags for controlling functionality
- Enhanced logging configuration
- Network connection tuning

### 2. Create Custom Preset

Save your customized configuration as a preset:

```json
{
  "name": "my_migrated_config",
  "description": "My customized configuration after migration",
  "preset_type": "user",
  "config": {
    // Your customized settings
  }
}
```

### 3. Set Up Environment Variables

Use environment variables for deployment-specific settings:

```bash
export VIDTANIUM_OUTPUT_DIR="/production/downloads"
export VIDTANIUM_LOG_LEVEL="INFO"
export VIDTANIUM_MAX_CONCURRENT="8"
```

### 4. Enable Useful Features

Consider enabling new features:

```bash
python main.py --enable-features adaptive_retry parallel_downloads integrity_verification
```

### 5. Regular Backups

Set up regular configuration backups:

```bash
# Manual backup
python main.py --backup-config

# Or configure automatic backups
# Set config_backup_count in general section
```

## Getting Help

If you encounter issues during migration:

1. **Check documentation**: [Configuration Guide](configuration-guide.md)
2. **Use diagnostic tools**: `--validate-config`, `--config-report`
3. **Enable debug logging**: `--debug --log-level DEBUG`
4. **Create minimal reproduction** for complex issues

The migration process is designed to be safe and reversible. Your original configuration is always backed up before any changes are made.

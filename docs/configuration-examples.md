# Configuration Examples

This document provides practical configuration examples for different use cases and deployment scenarios.

## Basic Configurations

### Home User Configuration

Balanced settings for personal use:

```json
{
  "_version": "2.0.0",
  "general": {
    "output_directory": "~/Downloads/VidTanium",
    "auto_cleanup": true,
    "language": "auto",
    "theme": "system",
    "check_updates": true,
    "max_recent_files": 15,
    "config_auto_save": true,
    "config_backup_count": 5
  },
  "download": {
    "max_concurrent_tasks": 3,
    "max_workers_per_task": 8,
    "max_retries": 5,
    "retry_delay": 2.0,
    "request_timeout": 60,
    "chunk_size": 16384,
    "bandwidth_limit": 0
  },
  "network": {
    "connection_pool_size": 15,
    "max_connections_per_host": 6,
    "connection_timeout": 30.0,
    "read_timeout": 120.0,
    "verify_ssl": true
  },
  "features": {
    "adaptive_retry": true,
    "parallel_downloads": true,
    "system_tray": true,
    "notifications": true,
    "resume_downloads": true
  },
  "ui": {
    "show_detailed_progress": true,
    "show_notifications": true,
    "confirm_on_exit": true,
    "animations_enabled": true
  }
}
```

### Power User Configuration

High-performance settings for advanced users:

```json
{
  "_version": "2.0.0",
  "general": {
    "output_directory": "/media/downloads",
    "auto_cleanup": false,
    "theme": "dark",
    "max_recent_files": 50,
    "config_backup_count": 10
  },
  "download": {
    "max_concurrent_tasks": 8,
    "max_workers_per_task": 20,
    "max_retries": 3,
    "retry_delay": 1.0,
    "request_timeout": 30,
    "chunk_size": 65536,
    "bandwidth_limit": 0
  },
  "network": {
    "connection_pool_size": 50,
    "max_connections_per_host": 15,
    "connection_timeout": 15.0,
    "read_timeout": 60.0,
    "dns_cache_timeout": 600
  },
  "performance": {
    "memory_limit_mb": 4096,
    "cpu_usage_limit": 95,
    "buffer_size_max": 2097152,
    "optimization_level": "maximum"
  },
  "logging": {
    "log_level": "WARNING",
    "log_to_console": false,
    "log_rotation_size": "100 MB"
  },
  "features": {
    "adaptive_retry": true,
    "adaptive_timeout": true,
    "parallel_downloads": true,
    "memory_optimization": true,
    "connection_pooling": true
  }
}
```

## Deployment Scenarios

### Server/Headless Configuration

For server deployments without GUI:

```json
{
  "_version": "2.0.0",
  "general": {
    "output_directory": "/var/downloads",
    "auto_cleanup": true,
    "check_updates": false,
    "config_auto_save": true
  },
  "download": {
    "max_concurrent_tasks": 6,
    "max_workers_per_task": 12,
    "max_retries": 10,
    "retry_delay": 5.0,
    "request_timeout": 120
  },
  "network": {
    "connection_pool_size": 30,
    "connection_timeout": 45.0,
    "read_timeout": 300.0
  },
  "performance": {
    "memory_limit_mb": 2048,
    "cpu_usage_limit": 80,
    "optimization_level": "high"
  },
  "logging": {
    "log_level": "INFO",
    "log_to_console": false,
    "log_to_file": true,
    "log_rotation_size": "50 MB",
    "log_retention": "30 days"
  },
  "features": {
    "adaptive_retry": true,
    "parallel_downloads": true,
    "system_tray": false,
    "notifications": false,
    "enhanced_theme_system": false
  },
  "ui": {
    "show_notifications": false,
    "confirm_on_exit": false,
    "animations_enabled": false
  }
}
```

### Docker Container Configuration

Optimized for containerized environments:

```json
{
  "_version": "2.0.0",
  "general": {
    "output_directory": "/downloads",
    "temp_directory": "/tmp/vidtanium",
    "cache_directory": "/cache",
    "auto_cleanup": true,
    "check_updates": false
  },
  "download": {
    "max_concurrent_tasks": 4,
    "max_workers_per_task": 8,
    "request_timeout": 60
  },
  "network": {
    "connection_pool_size": 20,
    "connection_timeout": 30.0,
    "read_timeout": 120.0
  },
  "performance": {
    "memory_limit_mb": 1024,
    "cpu_usage_limit": 90,
    "optimization_level": "balanced"
  },
  "logging": {
    "log_level": "INFO",
    "log_to_console": true,
    "log_to_file": false
  },
  "features": {
    "adaptive_retry": true,
    "parallel_downloads": true,
    "system_tray": false,
    "notifications": false
  }
}
```

## Resource-Constrained Environments

### Low-Memory Configuration

For systems with limited RAM:

```json
{
  "_version": "2.0.0",
  "general": {
    "auto_cleanup": true,
    "max_recent_files": 5,
    "config_backup_count": 2
  },
  "download": {
    "max_concurrent_tasks": 1,
    "max_workers_per_task": 2,
    "chunk_size": 4096
  },
  "network": {
    "connection_pool_size": 3,
    "max_connections_per_host": 1
  },
  "performance": {
    "memory_limit_mb": 128,
    "cpu_usage_limit": 50,
    "buffer_size_min": 4096,
    "buffer_size_max": 32768,
    "buffer_size_default": 8192,
    "gc_threshold_mb": 25,
    "optimization_level": "low"
  },
  "logging": {
    "log_level": "ERROR",
    "log_rotation_size": "1 MB",
    "log_retention": "1 day"
  },
  "features": {
    "adaptive_retry": false,
    "memory_optimization": true,
    "connection_pooling": false,
    "parallel_downloads": false
  }
}
```

### Bandwidth-Limited Configuration

For slow or metered connections:

```json
{
  "_version": "2.0.0",
  "download": {
    "max_concurrent_tasks": 1,
    "max_workers_per_task": 1,
    "max_retries": 10,
    "retry_delay": 10.0,
    "request_timeout": 300,
    "chunk_size": 2048,
    "bandwidth_limit": 100
  },
  "network": {
    "connection_pool_size": 2,
    "max_connections_per_host": 1,
    "connection_timeout": 60.0,
    "read_timeout": 600.0
  },
  "features": {
    "adaptive_timeout": true,
    "bandwidth_limiting": true,
    "resume_downloads": true
  }
}
```

## Development and Testing

### Development Configuration

For developers and debugging:

```json
{
  "_version": "2.0.0",
  "general": {
    "output_directory": "./dev_downloads",
    "auto_cleanup": false,
    "check_updates": false,
    "config_backup_count": 20
  },
  "download": {
    "max_concurrent_tasks": 2,
    "max_workers_per_task": 3,
    "max_retries": 1,
    "retry_delay": 0.5
  },
  "logging": {
    "log_level": "DEBUG",
    "debug_logging": true,
    "log_to_console": true,
    "log_to_file": true,
    "log_rotation_size": "500 MB",
    "log_retention": "90 days",
    "log_compression": "none"
  },
  "features": {
    "adaptive_retry": true,
    "parallel_downloads": true,
    "debug_mode": true,
    "performance_profiling": true
  }
}
```

### Testing Configuration

For automated testing:

```json
{
  "_version": "2.0.0",
  "general": {
    "output_directory": "./test_output",
    "auto_cleanup": true,
    "check_updates": false
  },
  "download": {
    "max_concurrent_tasks": 1,
    "max_workers_per_task": 1,
    "max_retries": 0,
    "request_timeout": 10
  },
  "logging": {
    "log_level": "DEBUG",
    "log_to_console": true,
    "log_to_file": false
  },
  "features": {
    "mock_downloads": true,
    "system_tray": false,
    "notifications": false
  },
  "ui": {
    "confirm_on_exit": false,
    "animations_enabled": false
  }
}
```

## Environment Variable Examples

### Production Environment

```bash
#!/bin/bash
# Production environment variables

export VIDTANIUM_OUTPUT_DIR="/var/downloads"
export VIDTANIUM_LOG_LEVEL="INFO"
export VIDTANIUM_MAX_CONCURRENT="6"
export VIDTANIUM_MEMORY_LIMIT="2048"
export VIDTANIUM_OPTIMIZATION="high"
export VIDTANIUM_AUTO_CLEANUP="true"
export VIDTANIUM_CHECK_UPDATES="false"
export VIDTANIUM_VERIFY_SSL="true"
```

### Development Environment

```bash
#!/bin/bash
# Development environment variables

export VIDTANIUM_OUTPUT_DIR="./dev_downloads"
export VIDTANIUM_LOG_LEVEL="DEBUG"
export VIDTANIUM_DEBUG="true"
export VIDTANIUM_MAX_CONCURRENT="2"
export VIDTANIUM_AUTO_CLEANUP="false"
export VIDTANIUM_THEME="dark"
export VIDTANIUM_FEATURES="debug_mode,performance_profiling"
```

### Docker Environment

```bash
#!/bin/bash
# Docker container environment variables

export VIDTANIUM_OUTPUT_DIR="/downloads"
export VIDTANIUM_TEMP_DIR="/tmp/vidtanium"
export VIDTANIUM_CACHE_DIR="/cache"
export VIDTANIUM_LOG_LEVEL="INFO"
export VIDTANIUM_MAX_CONCURRENT="4"
export VIDTANIUM_MEMORY_LIMIT="1024"
export VIDTANIUM_CHECK_UPDATES="false"
```

## Command-Line Usage Examples

### Quick Start Commands

```bash
# Use high-performance preset
python main.py --preset high_performance

# Custom output directory with specific settings
python main.py --output-dir "/custom/path" --max-concurrent 8 --theme dark

# Enable debug mode with specific features
python main.py --debug --enable-features parallel_downloads adaptive_retry
```

### Configuration Management

```bash
# Validate current configuration
python main.py --validate-config

# Create configuration backup
python main.py --backup-config

# Export configuration for sharing
python main.py --export-config my_config.json

# Import configuration from file
python main.py --import-config shared_config.json

# Reset to defaults and apply preset
python main.py --reset-config && python main.py --preset production
```

### Feature Management

```bash
# List all available features
python main.py --list-features

# Enable specific features for this session
python main.py --enable-features adaptive_retry parallel_downloads notifications

# Disable problematic features
python main.py --disable-features system_tray enhanced_theme_system
```

## Custom Preset Examples

### Media Server Preset

```json
{
  "name": "media_server",
  "description": "Optimized for media server environments",
  "preset_type": "user",
  "tags": ["server", "media", "automated"],
  "config": {
    "_version": "2.0.0",
    "general": {
      "output_directory": "/media/downloads",
      "auto_cleanup": true,
      "check_updates": false
    },
    "download": {
      "max_concurrent_tasks": 10,
      "max_workers_per_task": 15,
      "chunk_size": 131072
    },
    "performance": {
      "memory_limit_mb": 3072,
      "optimization_level": "high"
    },
    "features": {
      "parallel_downloads": true,
      "adaptive_retry": true,
      "system_tray": false,
      "notifications": false
    }
  }
}
```

### Educational Institution Preset

```json
{
  "name": "educational",
  "description": "Safe settings for educational environments",
  "preset_type": "user",
  "tags": ["education", "safe", "monitored"],
  "config": {
    "_version": "2.0.0",
    "general": {
      "output_directory": "/shared/downloads",
      "auto_cleanup": true,
      "check_updates": true
    },
    "download": {
      "max_concurrent_tasks": 2,
      "max_workers_per_task": 5,
      "bandwidth_limit": 500
    },
    "logging": {
      "log_level": "INFO",
      "log_to_file": true,
      "log_retention": "90 days"
    },
    "features": {
      "bandwidth_limiting": true,
      "integrity_verification": true,
      "enhanced_ssl_verification": true
    }
  }
}
```

These examples provide starting points for various use cases. Customize them based on your specific requirements and environment constraints.

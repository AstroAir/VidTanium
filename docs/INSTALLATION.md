---
title: Installation Guide
description: Complete installation guide for VidTanium video download tool
---

# Installation Guide

Complete installation guide for VidTanium video download tool.

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: Version 3.11 or higher
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB for application, additional space for downloads
- **Network**: Internet connection required for downloads

### Recommended Requirements

- **RAM**: 16 GB for optimal performance with large files
- **Storage**: SSD for better performance
- **CPU**: Multi-core processor for concurrent downloads
- **Graphics**: Hardware acceleration support for media processing

## Installation Methods

### Method 1: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager.

1. **Install uv**

   ```bash
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and install VidTanium**

   ```bash
   git clone https://github.com/yourusername/VidTanium.git
   cd VidTanium
   uv sync
   ```

3. **Run the application**

   ```bash
   uv run python main.py
   ```

### Method 2: Using pip

1. **Create virtual environment**

   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   git clone https://github.com/yourusername/VidTanium.git
   cd VidTanium
   pip install -e .
   ```

3. **Run the application**

   ```bash
   python main.py
   ```

### Method 3: Development Installation

For contributors and developers:

1. **Clone with development dependencies**

   ```bash
   git clone https://github.com/yourusername/VidTanium.git
   cd VidTanium
   uv sync --dev
   ```

2. **Install pre-commit hooks**

   ```bash
   uv run pre-commit install
   ```

3. **Run tests to verify installation**

   ```bash
   uv run pytest
   ```

## Optional Dependencies

### FFmpeg (Recommended)

FFmpeg is required for media processing features.

#### Windows

```bash
# Using Chocolatey
choco install ffmpeg

# Using Scoop
scoop install ffmpeg

# Manual installation
# Download from https://ffmpeg.org/download.html
# Add to PATH environment variable
```

#### macOS

```bash
# Using Homebrew
brew install ffmpeg

# Using MacPorts
sudo port install ffmpeg
```

#### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

### Additional Tools

```bash
# Git (for cloning repository)
# Windows: Download from https://git-scm.com/
# macOS: xcode-select --install
# Linux: sudo apt install git

# Optional: Qt Designer for UI development
pip install pyside6-tools
```

## Configuration

### Initial Setup

1. **Launch VidTanium**

   ```bash
   python main.py
   ```

2. **Configure settings**
   - Set download directory
   - Configure concurrent downloads
   - Set up proxy if needed
   - Configure FFmpeg path if not in PATH

3. **Test installation**
   - Try downloading a test M3U8 file
   - Verify all features work correctly

### Configuration Files

VidTanium stores configuration in:

- **Windows**: `%APPDATA%\VidTanium\`
- **macOS**: `~/Library/Application Support/VidTanium/`
- **Linux**: `~/.config/VidTanium/`

#### Main Configuration

Edit `config/config.json` with comprehensive settings:

```json
{
    "general": {
        "output_directory": "~/Downloads/VidTanium",
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
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
    },
    "monitoring": {
        "enable_bandwidth_monitoring": true,
        "bandwidth_sample_interval": 1.0,
        "max_bandwidth_samples": 3600,
        "enable_performance_analytics": true,
        "eta_algorithm": "adaptive"
    },
    "error_handling": {
        "enable_circuit_breaker": true,
        "circuit_breaker_threshold": 5,
        "circuit_breaker_timeout": 60,
        "max_error_history": 1000,
        "enable_intelligent_retry": true
    },
    "queue_management": {
        "enable_smart_prioritization": true,
        "queue_optimization_interval": 30,
        "max_queue_size": 100,
        "priority_boost_factor": 1.5
    }
}
```

#### Configuration Categories

**General Settings**:
- `output_directory`: Default download location
- `auto_cleanup`: Automatic temporary file cleanup
- `language`: Interface language (auto, en, zh)
- `theme`: UI theme (system, light, dark)
- `check_updates`: Automatic update checking

**Download Settings**:
- `max_concurrent_tasks`: Maximum simultaneous downloads
- `max_workers_per_task`: Threads per download task
- `max_retries`: Maximum retry attempts for failed segments
- `retry_delay`: Base delay between retry attempts
- `request_timeout`: HTTP request timeout in seconds
- `chunk_size`: Download chunk size in bytes
- `bandwidth_limit`: Maximum bandwidth usage (0 = unlimited)

**Advanced Settings**:
- `proxy`: HTTP/HTTPS proxy configuration
- `user_agent`: Custom user agent string
- `verify_ssl`: SSL certificate verification
- `ffmpeg_path`: Custom FFmpeg executable path
- `keep_temp_files`: Preserve temporary files for debugging
- `debug_logging`: Enable detailed debug logging

**UI Settings**:
- `show_detailed_progress`: Display detailed progress information
- `minimize_to_tray`: Minimize to system tray instead of taskbar
- `show_notifications`: Enable desktop notifications
- `confirm_on_exit`: Show confirmation dialog when closing

**Monitoring Settings**:
- `enable_bandwidth_monitoring`: Real-time bandwidth tracking
- `bandwidth_sample_interval`: Monitoring sample frequency
- `max_bandwidth_samples`: Maximum stored bandwidth samples
- `enable_performance_analytics`: Performance metrics collection
- `eta_algorithm`: ETA calculation method (linear, exponential, adaptive)

**Error Handling Settings**:
- `enable_circuit_breaker`: Circuit breaker pattern protection
- `circuit_breaker_threshold`: Failure threshold for circuit breaker
- `circuit_breaker_timeout`: Recovery timeout in seconds
- `max_error_history`: Maximum stored error records
- `enable_intelligent_retry`: Context-aware retry strategies

**Queue Management Settings**:
- `enable_smart_prioritization`: Intelligent task prioritization
- `queue_optimization_interval`: Queue optimization frequency
- `max_queue_size`: Maximum queued tasks
- `priority_boost_factor`: Priority adjustment factor

## Troubleshooting Installation

### Common Issues

#### Python Version Issues

```bash
# Check Python version
python --version

# If Python 3.11+ not found, install it:
# Windows: Download from python.org
# macOS: brew install python@3.11
# Linux: sudo apt install python3.11
```

#### Permission Errors

```bash
# Windows: Run as Administrator
# macOS/Linux: Check file permissions
chmod +x main.py
```

#### Dependency Conflicts

```bash
# Clear pip cache
pip cache purge

# Update pip
python -m pip install --upgrade pip

# Reinstall in clean environment
python -m venv fresh_env
source fresh_env/bin/activate  # Linux/macOS
fresh_env\Scripts\activate     # Windows
pip install -e .
```

#### Network Issues

```bash
# Configure proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Or use pip proxy
pip install --proxy http://proxy.company.com:8080 -e .
```

### Verification Steps

1. **Check Python installation**

   ```bash
   python --version
   # Should show 3.11 or higher
   ```

2. **Verify dependencies**

   ```bash
   python -c "import PySide6; print('PySide6 OK')"
   python -c "import aiofiles; print('aiofiles OK')"
   python -c "import requests; print('requests OK')"
   ```

3. **Test FFmpeg**

   ```bash
   ffmpeg -version
   # Should show FFmpeg version info
   ```

4. **Run application**

   ```bash
   python main.py --debug
   # Should launch without errors
   ```

## Performance Optimization

### System Tuning

1. **Increase file descriptor limits** (Linux/macOS)

   ```bash
   ulimit -n 4096
   ```

2. **Configure network settings**

   ```bash
   # Increase network buffer sizes
   echo 'net.core.rmem_max = 26214400' | sudo tee -a /etc/sysctl.conf
   echo 'net.core.wmem_max = 26214400' | sudo tee -a /etc/sysctl.conf
   ```

3. **SSD optimization**
   - Use SSD for download directory
   - Enable write caching
   - Disable indexing on download folder

### Application Settings

```json
{
    "performance": {
        "concurrent_tasks": 10,
        "buffer_size": 8192,
        "connection_pool_size": 100,
        "timeout_settings": {
            "connect": 10,
            "read": 30,
            "total": 300
        }
    }
}
```

## Security Considerations

### Network Security

- VidTanium respects robots.txt
- Use HTTPS when available
- Configure proxy for corporate networks
- Monitor network usage

### File Security

- Downloads are scanned for malware (if antivirus available)
- Temporary files are securely cleaned
- Download directory permissions are restricted

### Privacy

- No telemetry or tracking
- Local configuration only
- No data sent to external servers except for downloads

## Uninstallation

### Complete Removal

1. **Remove application files**

   ```bash
   # If installed with git
   rm -rf VidTanium/
   
   # If installed with pip
   pip uninstall vidtanium
   ```

2. **Remove configuration**

   ```bash
   # Windows
   rmdir /s "%APPDATA%\VidTanium"
   
   # macOS
   rm -rf "~/Library/Application Support/VidTanium"
   
   # Linux
   rm -rf ~/.config/VidTanium
   ```

3. **Remove virtual environment** (if used)

   ```bash
   # Remove environment directory
   rm -rf venv/  # or whatever you named it
   ```

## Support

### Getting Help

- 📖 Check the [User Manual](user-manual.md)
- 🐛 Report issues on [GitHub](https://github.com/yourusername/VidTanium/issues)
- 💬 Join discussions on [GitHub Discussions](https://github.com/yourusername/VidTanium/discussions)
- 📧 Email: [support@vidtanium.com](mailto:support@vidtanium.com)

### Before Seeking Help

1. Check this installation guide
2. Review error messages carefully
3. Search existing GitHub issues
4. Try basic troubleshooting steps
5. Gather system information

### Information to Include

When reporting installation issues:

- Operating system and version
- Python version
- Installation method used
- Complete error messages
- Steps that led to the problem
- What you've already tried

---

**Success!** 🎉 You should now have VidTanium installed and ready to use. See the [User Manual](user-manual.md) for usage instructions.


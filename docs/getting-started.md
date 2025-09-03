---
title: Getting Started
description: Quick start guide for VidTanium - from installation to your first download
---

# Getting Started

Welcome to VidTanium! This guide will help you get up and running quickly with your first video download.

!!! info "Complete Guide Available"
    For comprehensive instructions, see the [Complete Workflow Guide](workflow-guide.md).

## Prerequisites

Before installing VidTanium, ensure your system meets these requirements:

- **Python 3.11+** - [Download here](https://python.org/downloads/)
- **FFmpeg** - Required for media processing
- **4GB RAM minimum** (8GB recommended)
- **Stable internet connection**

## Step 1: Install FFmpeg

FFmpeg is required for media processing. Choose your platform:

=== "Windows"

    ```bash
    # Using Chocolatey (recommended)
    choco install ffmpeg

    # Or download from https://ffmpeg.org/download.html
    ```

=== "macOS"

    ```bash
    # Using Homebrew
    brew install ffmpeg
    ```

=== "Linux"

    ```bash
    # Ubuntu/Debian
    sudo apt update && sudo apt install ffmpeg

    # CentOS/RHEL
    sudo yum install ffmpeg
    ```

## Step 2: Install VidTanium

Choose your preferred installation method:

=== "Using uv (Recommended)"

    ```bash
    # Install uv package manager
    curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
    # or
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

    # Clone and install VidTanium
    git clone https://github.com/AstroAir/VidTanium.git
    cd VidTanium
    uv sync
    ```

=== "Using pip"

    ```bash
    git clone https://github.com/AstroAir/VidTanium.git
    cd VidTanium
    pip install -e .
    ```

## Step 3: Verify Installation

Test that everything is working correctly:

```bash
# Test the installation
python main.py --help

# Expected output:
# usage: main.py [-h] [--debug] [--config CONFIG] [--url URL]
# 加密视频下载工具
```

The GUI should launch successfully showing the VidTanium interface.

## Step 4: Your First Download

### GUI Method (Recommended)

1. **Launch VidTanium**:
   ```bash
   python main.py
   ```

2. **Navigate the Interface**:
   - **Dashboard**: Overview of download activity
   - **Download Manager**: Add and manage tasks
   - **Analytics**: Performance monitoring
   - **Settings**: Configure preferences

3. **Add Your First Download**:
   - Click "Add Task" or use the URL input field
   - Paste your M3U8 URL: `https://example.com/video.m3u8`
   - Choose output directory (optional)
   - Click "Start Download"

4. **Monitor Progress**:
   - Real-time progress bar
   - Download speed and ETA
   - Error notifications (if any)

### Command Line Method

```bash
# Direct download
python main.py --url "https://example.com/video.m3u8"

# With debug output
python main.py --debug --url "https://example.com/video.m3u8"
```

## Understanding the Interface

### Dashboard
- **Active Downloads**: Current download status
- **System Status**: CPU, memory, network usage
- **Recent Activity**: Download history
- **Quick Actions**: Common tasks

### Download Manager
- **Task Queue**: Pending downloads
- **Active Tasks**: Currently downloading
- **Completed**: Finished downloads
- **Failed**: Error diagnostics

### Settings Categories
- **General**: Basic preferences
- **Network**: Connection settings
- **Advanced**: Performance tuning
- **Appearance**: Theme and UI options

## Supported URL Formats

VidTanium supports various video URL formats:

!!! example "Supported Formats"
    - **Direct M3U8 playlist URLs**
    - **Encrypted M3U8 streams** (AES-128)
    - **Standard video URLs** (MP4, AVI, etc.)
    - **Batch URL lists**

## Basic Configuration

### Output Directory

Set your default download location:

1. Open **Settings** → **General**
2. Set **Output Directory** to your preferred location
3. Enable **Auto Cleanup** for temporary files

### Network Settings

Optimize for your connection:

1. Open **Settings** → **Network**
2. Adjust **Max Concurrent Downloads** (default: 4)
3. Set **Bandwidth Limit** if needed
4. Configure **Timeout** settings

## Common First-Time Issues

!!! warning "Troubleshooting"

    === "FFmpeg Not Found"
        ```bash
        # Install FFmpeg or specify custom path in settings
        {
            "media": {
                "ffmpeg_path": "/custom/path/to/ffmpeg"
            }
        }
        ```

    === "SSL Certificate Errors"
        ```bash
        # Disable SSL verification (not recommended for production)
        python main.py --no-ssl-verify

        # Or update certificates
        pip install --upgrade certifi
        ```

    === "Permission Errors"
        ```bash
        # Check directory permissions
        ls -la /path/to/downloads/

        # Create directory with proper permissions
        mkdir -p ~/Downloads/VidTanium
        chmod 755 ~/Downloads/VidTanium
        ```

## Next Steps

Once you've completed your first download, explore these resources:

!!! tip "Continue Learning"
    - **[Complete Workflow Guide](workflow-guide.md)** - Comprehensive documentation
    - **[Examples](examples.md)** - Real-world usage scenarios
    - **[User Manual](user-manual.md)** - Detailed feature documentation
    - **[API Reference](api-reference.md)** - For developers and integrators

## Quick Tips

!!! success "Pro Tips"
    1. **Use descriptive names** for your downloads
    2. **Monitor system resources** during large downloads
    3. **Enable debug mode** if you encounter issues
    4. **Check the logs** for detailed error information
    5. **Update regularly** for the latest features and fixes

## Getting Help

If you need assistance:

1. **Check the logs** with `--debug` flag
2. **Review documentation** in the [User Manual](user-manual.md)
3. **Visit our [GitHub Issues](https://github.com/AstroAir/VidTanium/issues)**
4. **Join the community** discussions

---

!!! question "Need more help?"
    Visit our [Help System](help-system.md) for comprehensive troubleshooting guides and FAQ.

---
title: Complete Workflow Guide
description: Your comprehensive guide to mastering VidTanium from installation to advanced usage
---

# Complete Workflow Guide

!!! abstract "Overview"
    Your comprehensive guide to mastering VidTanium from installation to advanced usage

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Getting Started](#getting-started)
3. [Core Features](#core-features)
4. [Complete Workflow](#complete-workflow)
5. [API Reference](#api-reference)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## Installation and Setup

### Prerequisites

Before installing VidTanium, ensure your system meets these requirements:

- **Python 3.11 or higher** - [Download Python](https://python.org/downloads/)
- **FFmpeg** - Required for media processing
- **4GB RAM minimum** (8GB recommended for large downloads)
- **Stable internet connection**

### Step 1: Install FFmpeg

=== "Windows"

    ```bash
    # Using Chocolatey
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

### Step 2: Install VidTanium

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

### Step 3: Verify Installation

```bash
# Test the installation
python main.py --help

# Expected output:
# usage: main.py [-h] [--debug] [--config CONFIG] [--url URL]
# 加密视频下载工具
```

### Step 4: Initial Configuration

1. **Create config directory** (optional):
   ```bash
   mkdir -p ~/.vidtanium/config
   ```

2. **First run** to generate default configuration:
   ```bash
   python main.py
   ```

3. **Verify GUI startup** - The application should open with the Fluent Design interface.

---

## Getting Started

### Your First Download

#### GUI Method (Recommended for Beginners)

1. **Launch VidTanium:**
   ```bash
   python main.py
   ```

2. **Navigate the Interface:**
   - **Dashboard**: Overview of download activity
   - **Download Manager**: Add and manage tasks
   - **Analytics**: Performance monitoring
   - **Settings**: Configure preferences

3. **Add Your First Download:**
   - Click "Add Task" or use the URL input field
   - Paste your M3U8 URL: `https://example.com/video.m3u8`
   - Choose output directory (optional)
   - Click "Start Download"

4. **Monitor Progress:**
   - Real-time progress bar
   - Download speed and ETA
   - Error notifications (if any)

#### Command Line Method

```bash
# Direct download
python main.py --url "https://example.com/video.m3u8"

# With debug output
python main.py --debug --url "https://example.com/video.m3u8"
```

### Understanding the Interface

#### Dashboard
- **Active Downloads**: Current download status
- **System Status**: CPU, memory, network usage
- **Recent Activity**: Download history
- **Quick Actions**: Common tasks

#### Download Manager
- **Task Queue**: Pending downloads
- **Active Tasks**: Currently downloading
- **Completed**: Finished downloads
- **Failed**: Error diagnostics

#### Settings Categories
- **General**: Basic preferences
- **Network**: Connection settings
- **Advanced**: Performance tuning
- **Appearance**: Theme and UI options

---

## Core Features

### 1. M3U8 Download with Encryption Support

VidTanium excels at downloading encrypted M3U8 streams:

```python
from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings

# Initialize components
settings = Settings()
downloader = DownloadManager(settings)
downloader.start()

# Create encrypted download task
task = DownloadTask(
    name="Encrypted Video",
    base_url="https://example.com/encrypted-stream.m3u8",
    key_url="https://example.com/encryption.key",
    segments=150,
    output_file="/downloads/video.mp4",
    priority=TaskPriority.HIGH
)

task_id = downloader.add_task(task)
```

**Supported Encryption:**
- AES-128 encryption
- Automatic key retrieval
- Multiple key formats
- Custom decryption parameters

### 2. Multi-threaded Performance

Configure concurrent downloads for optimal speed:

```python
# In settings or config
{
    "download": {
        "max_concurrent_downloads": 4,
        "max_concurrent_segments": 8,
        "chunk_size": 1048576,  # 1MB chunks
        "timeout": 30
    }
}
```

### 3. Advanced Error Handling

Intelligent error recovery with categorized handling:

```python
from src.core.exceptions import VidTaniumException, ErrorCategory

try:
    task_id = downloader.add_task(task)
except VidTaniumException as e:
    if e.category == ErrorCategory.NETWORK:
        print(f"Network error: {e.message}")
        print(f"Suggested actions: {e.suggested_actions}")
    elif e.category == ErrorCategory.ENCRYPTION:
        print(f"Decryption error: {e.message}")
        # Handle encryption-specific errors
```

**Error Categories:**
- Network errors (timeouts, connectivity)
- Encryption errors (key issues, decryption failures)
- Filesystem errors (permissions, disk space)
- System errors (memory, CPU constraints)

---

## Complete Workflow

### End-to-End Download Process

#### Phase 1: Input and Validation

1. **URL Input:**
   ```python
   from src.core.url_extractor import URLExtractor
   
   extractor = URLExtractor()
   url_info = extractor.extract_info("https://example.com/video.m3u8")
   
   print(f"Video title: {url_info.title}")
   print(f"Duration: {url_info.duration}")
   print(f"Quality options: {url_info.formats}")
   ```

2. **Format Selection:**
   - Automatic best quality selection
   - Manual quality override
   - Custom resolution preferences

3. **Output Configuration:**
   - Default download directory
   - Custom file naming patterns
   - Format conversion options

#### Phase 2: Task Creation and Queuing

```python
# Create task with full configuration
task = DownloadTask(
    name="My Video",
    base_url=url_info.best_format.url,
    key_url=url_info.best_format.key_url,
    segments=url_info.best_format.segment_count,
    output_file="/downloads/my_video.mp4",
    priority=TaskPriority.NORMAL,
    max_retries=3,
    retry_delay=2.0,
    headers={"User-Agent": "VidTanium/1.0"}
)

# Add to queue with smart prioritization
task_id = downloader.add_task(task)
```

#### Phase 3: Download Execution

1. **Segment Processing:**
   - Parallel segment downloads
   - Real-time progress tracking
   - Automatic retry on failures

2. **Decryption (if needed):**
   - Key retrieval and validation
   - AES-128 decryption
   - Integrity verification

3. **Progress Monitoring:**
   ```python
   from src.core.bandwidth_monitor import bandwidth_monitor
   
   # Get real-time statistics
   stats = bandwidth_monitor.get_current_stats()
   print(f"Speed: {stats.download_speed:.2f} MB/s")
   print(f"ETA: {stats.estimated_time_remaining}")
   ```

#### Phase 4: Post-Processing

1. **File Merging:**
   - Segment concatenation
   - Metadata preservation
   - Quality verification

2. **Format Conversion (optional):**
   ```python
   from src.core.media_processor import MediaProcessor
   
   processor = MediaProcessor()
   processor.convert_video(
       input_file="/downloads/video.ts",
       output_file="/downloads/video.mp4",
       format_options={"codec": "h264", "quality": "high"}
   )
   ```

3. **Cleanup:**
   - Temporary file removal
   - Cache management
   - Resource cleanup

### Expected Outputs

#### Successful Download
```
✅ Download completed successfully
📁 Output file: /downloads/my_video.mp4
📊 File size: 1.2 GB
⏱️ Duration: 1h 23m 45s
🚀 Average speed: 5.2 MB/s
```

#### Download with Issues
```
⚠️ Download completed with warnings
📁 Output file: /downloads/my_video.mp4
🔄 Retried segments: 3
⚠️ Quality degradation: 2 segments
📋 See logs for details
```

---

## API Reference

### Core Classes

#### DownloadManager
```python
class DownloadManager:
    def __init__(self, settings: Settings)
    def start(self) -> None
    def add_task(self, task: DownloadTask) -> str
    def get_task_status(self, task_id: str) -> TaskStatus
    def pause_task(self, task_id: str) -> bool
    def resume_task(self, task_id: str) -> bool
    def cancel_task(self, task_id: str) -> bool
```

#### DownloadTask
```python
@dataclass
class DownloadTask:
    name: str
    base_url: str
    key_url: Optional[str] = None
    segments: int = 0
    output_file: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 1.0
    headers: Dict[str, str] = field(default_factory=dict)
```

### Monitoring APIs

#### Bandwidth Monitor
```python
from src.core.bandwidth_monitor import bandwidth_monitor

# Get current statistics
stats = bandwidth_monitor.get_current_stats()
print(f"Download speed: {stats.download_speed}")
print(f"Upload speed: {stats.upload_speed}")
print(f"Network utilization: {stats.utilization}")
```

#### Progress Tracking
```python
from src.core.batch_progress_aggregator import batch_progress_aggregator

# Get batch progress
progress = batch_progress_aggregator.get_batch_progress()
print(f"Overall progress: {progress.overall_percentage}%")
print(f"Active tasks: {progress.active_tasks}")
print(f"ETA: {progress.estimated_time_remaining}")
```

---

## Examples

### Example 1: Basic M3U8 Download

```python
#!/usr/bin/env python3
"""Basic M3U8 download example"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings
import time

def basic_download():
    # Initialize
    settings = Settings()
    downloader = DownloadManager(settings)
    downloader.start()
    
    # Create task
    task = DownloadTask(
        name="Sample Video",
        base_url="https://example.com/video.m3u8",
        output_file="./downloads/sample.mp4",
        priority=TaskPriority.HIGH
    )
    
    # Start download
    task_id = downloader.add_task(task)
    print(f"Started download: {task_id}")
    
    # Monitor progress
    while True:
        status = downloader.get_task_status(task_id)
        if status.state in ["completed", "failed", "cancelled"]:
            break
        print(f"Progress: {status.progress:.1f}%")
        time.sleep(1)
    
    print(f"Download {status.state}")

if __name__ == "__main__":
    basic_download()
```

### Example 2: Batch Download with Error Handling

```python
#!/usr/bin/env python3
"""Batch download with comprehensive error handling"""

from src.core import DownloadManager, DownloadTask, TaskPriority
from src.core.exceptions import VidTaniumException, ErrorCategory
from src.app.settings import Settings
import asyncio

async def batch_download_with_error_handling():
    settings = Settings()
    downloader = DownloadManager(settings)
    downloader.start()
    
    urls = [
        "https://example.com/video1.m3u8",
        "https://example.com/video2.m3u8",
        "https://example.com/video3.m3u8"
    ]
    
    tasks = []
    for i, url in enumerate(urls):
        try:
            task = DownloadTask(
                name=f"Video {i+1}",
                base_url=url,
                output_file=f"./downloads/video_{i+1}.mp4",
                priority=TaskPriority.NORMAL,
                max_retries=5
            )
            
            task_id = downloader.add_task(task)
            tasks.append(task_id)
            print(f"✅ Added task: {task.name}")
            
        except VidTaniumException as e:
            print(f"❌ Failed to add task for {url}")
            print(f"   Error: {e.message}")
            if e.category == ErrorCategory.NETWORK:
                print(f"   Suggestion: {e.suggested_actions}")
    
    # Monitor all tasks
    print(f"\n📊 Monitoring {len(tasks)} downloads...")
    # Implementation continues...

if __name__ == "__main__":
    asyncio.run(batch_download_with_error_handling())
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. SSL Certificate Errors

**Problem:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution:**
```bash
# Option 1: Disable SSL verification (not recommended for production)
python main.py --no-ssl-verify

# Option 2: Update certificates
pip install --upgrade certifi

# Option 3: Configure custom certificates in settings
```

#### 2. Network Timeout Issues

**Problem:** Downloads fail with timeout errors

**Solutions:**
```python
# Increase timeout in settings
{
    "network": {
        "timeout": 60,  # Increase from default 30
        "max_retries": 5,
        "retry_delay": 3.0
    }
}
```

#### 3. Memory Issues with Large Files

**Problem:** Application crashes or becomes unresponsive

**Solutions:**
```python
# Enable memory optimization
{
    "advanced": {
        "memory_optimization": true,
        "max_concurrent_segments": 4,  # Reduce from default 8
        "chunk_size": 524288  # Reduce chunk size to 512KB
    }
}
```

#### 4. FFmpeg Not Found

**Problem:** `FFmpeg executable not found`

**Solutions:**
```bash
# Install FFmpeg
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg  
# Linux: sudo apt install ffmpeg

# Or specify custom path in config
{
    "media": {
        "ffmpeg_path": "/custom/path/to/ffmpeg"
    }
}
```

#### 5. Permission Denied Errors

**Problem:** Cannot write to output directory

**Solutions:**
```bash
# Check directory permissions
ls -la /path/to/downloads/

# Create directory with proper permissions
mkdir -p ~/Downloads/VidTanium
chmod 755 ~/Downloads/VidTanium

# Or run with elevated permissions (Windows)
# Right-click -> "Run as administrator"
```

### Getting Help

1. **Check Logs:** Enable debug mode with `--debug` flag
2. **Review Documentation:** See [User Manual](user-manual.md) for detailed guides
3. **Community Support:** Visit our [GitHub Issues](https://github.com/AstroAir/VidTanium/issues)
4. **Developer Resources:** See [Developer Guide](developer-guide.md)

---

**Next Steps:** Ready to dive deeper? Check out our [Examples Collection](examples.md) for more advanced use cases and integration patterns.

# VidTanium

> A powerful video download tool with built-in player and editor capabilities

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-blue.svg)](https://doc.qt.io/qtforpython/)
[![Fluent UI](https://img.shields.io/badge/Design-Fluent-lightblue.svg)](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)

## 🚀 Overview

VidTanium is a modern, feature-rich video download tool specifically designed for downloading encrypted M3U8 video streams. Built with Python and PySide6, it offers a beautiful Fluent Design interface combined with powerful download capabilities and integrated media processing tools.

### ✨ Key Features

#### Core Download Engine

- 🔐 **Encrypted M3U8 Support** - Full AES-128 encryption support with automatic key handling
- 🚀 **Multi-threaded Downloads** - High-speed parallel downloading with configurable concurrency
- 🎯 **Intelligent Retry System** - Advanced retry management with circuit breaker pattern
- 📊 **Smart Queue Management** - Priority-based task scheduling with dynamic optimization
- 🔄 **Batch Processing** - Support for batch downloads and URL imports with bulk operations

#### Advanced Monitoring & Analytics

- 📈 **Bandwidth Monitoring** - Real-time network performance tracking and optimization
- ⏱️ **ETA Calculation** - Multiple algorithms (Linear, Exponential, Adaptive) for accurate time estimates
- 📋 **Download History** - Comprehensive tracking and analytics of completed downloads
- 🎯 **Progress Aggregation** - Multi-task progress monitoring with detailed statistics
- 🔍 **Performance Analytics** - Network interface detection and baseline performance metrics

#### Enhanced Error Handling

- 🛡️ **Intelligent Error Recovery** - Categorized error handling with severity levels and context
- 🔧 **User-Friendly Diagnostics** - Clear error messages with suggested actions
- 🔄 **Circuit Breaker Protection** - Automatic fault tolerance and system protection
- 📝 **Error Context Tracking** - Detailed diagnostic information for troubleshooting

#### Modern User Interface

- 🎨 **Fluent Design UI** - Beautiful, responsive interface built with PySide6
- 📱 **Responsive Layout** - Adaptive UI that works across different screen sizes
- 🎭 **Advanced Theme System** - Enhanced theming with system integration
- 📊 **Analytics Dashboard** - Comprehensive metrics and performance visualization
- 🔧 **Bulk Operations** - Efficient management of multiple download tasks

#### Media Processing & Tools

- 🎬 **Media Processing** - Built-in video conversion, editing, and compression
- ⏰ **Task Scheduling** - Automated download management and scheduling
- 🌍 **Internationalization** - Multi-language support (English/Chinese)
- 🎛️ **Advanced Configuration** - Comprehensive settings with bandwidth limiting and optimization

### 🏗️ Architecture

```text
VidTanium/
├── src/
│   ├── app/                    # Application lifecycle & startup
│   │   ├── application.py      # Main application class
│   │   └── settings.py         # Settings management
│   ├── core/                   # Core business logic
│   │   ├── downloader.py       # Download management
│   │   ├── url_extractor.py    # URL extraction and validation
│   │   ├── media_processor.py  # Video processing
│   │   ├── scheduler.py        # Task scheduling
│   │   ├── thread_pool.py      # Thread pool management
│   │   ├── error_handler.py    # Enhanced error handling
│   │   ├── retry_manager.py    # Intelligent retry management
│   │   ├── bandwidth_monitor.py # Network performance monitoring
│   │   ├── eta_calculator.py   # ETA calculation algorithms
│   │   ├── task_state_manager.py # Task state persistence
│   │   ├── queue_manager.py    # Advanced queue management
│   │   ├── smart_prioritization_engine.py # Task prioritization
│   │   ├── download_history_manager.py # Download history tracking
│   │   ├── batch_progress_aggregator.py # Multi-task progress
│   │   └── exceptions.py       # Custom exception hierarchy
│   ├── gui/                    # User interface
│   │   ├── main_window.py      # Main application window
│   │   ├── theme_manager.py    # Enhanced theme management
│   │   ├── widgets/            # Custom UI components
│   │   │   ├── dashboard/      # Analytics dashboard
│   │   │   ├── task_manager.py # Task management interface
│   │   │   ├── log/            # Log viewing components
│   │   │   ├── settings/       # Settings interfaces
│   │   │   ├── error_dialog.py # Error handling UI
│   │   │   ├── analytics_dashboard.py # Performance analytics
│   │   │   └── bulk_operations_manager.py # Bulk operations
│   │   ├── dialogs/            # Dialog windows
│   │   └── utils/              # UI utilities and responsive design
│   └── locales/                # Translation files
├── config/                     # Configuration files
├── tests/                      # Test suites
└── docs/                       # Documentation
```

## 🚀 Quick Start

> **📋 For detailed step-by-step instructions, see the [Complete Workflow Guide](docs/workflow-guide.md)**

### Prerequisites

- **Python 3.11+** - [Download here](https://python.org/downloads/)
- **FFmpeg** - Required for media processing ([Installation guide](docs/workflow-guide.md#step-1-install-ffmpeg))
- **4GB RAM minimum** (8GB recommended)
- **Stable internet connection**

### Installation (3 Steps)

1. **Install FFmpeg** (see [detailed guide](docs/workflow-guide.md#step-1-install-ffmpeg))

   ```bash
   # Windows: choco install ffmpeg
   # macOS: brew install ffmpeg
   # Linux: sudo apt install ffmpeg
   ```

2. **Clone and install VidTanium**

   ```bash
   git clone https://github.com/AstroAir/VidTanium.git
   cd VidTanium

   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -e .
   ```

3. **Launch and start downloading**

   ```bash
   # Start GUI
   python main.py

   # Or download directly
   python main.py --url "https://example.com/video.m3u8"
   ```

### Your First Download

1. **Launch VidTanium**: `python main.py`
2. **Paste M3U8 URL** in the input field
3. **Click "Add Task"** to start downloading
4. **Monitor progress** in real-time

**Need help?** → [Complete Workflow Guide](docs/workflow-guide.md#your-first-download) | [Examples](docs/examples.md#basic-examples)

### Command Line Options

```bash
# Basic usage
python main.py

# With debug logging
python main.py --debug

# Direct URL download
python main.py --url "https://example.com/video.m3u8"

# Custom config directory
python main.py --config "/path/to/config"
```

## 📖 Documentation

### 🎯 **Start Here: Complete Workflow Guide**

**[📋 Complete Workflow Guide](docs/workflow-guide.md)** - Your comprehensive guide from installation to advanced usage

### 🎨 Design System Documentation

VidTanium uses a modern, unified design system for consistent and beautiful UI. For developers working on the GUI:

| Document | Purpose | Best For |
|----------|---------|----------|
| [🎨 **Design System Reference**](DESIGN_SYSTEM.md) | **Complete design system specification** | **GUI developers - start here!** |
| [🔄 Migration Guide](MIGRATION_GUIDE.md) | Migrating to the new design system | Updating existing code |
| [💻 Code Examples](CODE_EXAMPLES.md) | Practical implementation examples | Learning by example |
| [📐 Design Patterns](DESIGN_PATTERNS.md) | Common UI patterns and layouts | Implementing standard components |
| [✅ Testing Guide](TESTING_GUIDE.md) | Testing and verification procedures | Ensuring design consistency |

### 📚 User Documentation

| Document | Purpose | Best For |
|----------|---------|----------|
| [🚀 **Workflow Guide**](docs/workflow-guide.md) | **Complete end-to-end guide** | **All users - start here!** |
| [⚙️ Installation Guide](docs/installation.md) | Setup and configuration | New users, system administrators |
| [📋 User Manual](docs/user-manual.md) | Complete user guide with advanced features | End users, power users |
| [💡 Examples](docs/examples.md) | Practical examples and use cases | Users wanting real-world scenarios |
| [🐛 Troubleshooting](docs/user-manual.md#troubleshooting) | Problem solving and diagnostics | Users experiencing issues |

### 👨‍💻 Developer Documentation

| Document | Purpose | Best For |
|----------|---------|----------|
| [🔧 Developer Guide](docs/developer-guide.md) | Development setup and architecture | Contributors, maintainers |
| [📚 API Reference](docs/api-reference.md) | Comprehensive API documentation | Developers, integrators |
| [🏗️ Project Structure](docs/project-structure.md) | Project organization and components | New contributors, architects |
| [📖 Technical Documentation](docs/documentation.md) | In-depth technical details | Advanced developers, researchers |

### 🚀 Quick Start Paths

**🆕 New Users** → [**Workflow Guide**](docs/workflow-guide.md) → [Installation](docs/installation.md) → [First Download](docs/workflow-guide.md#your-first-download)

**👨‍💻 Developers** → [**Workflow Guide**](docs/workflow-guide.md) → [API Examples](docs/examples.md#integration-examples) → [API Reference](docs/api-reference.md)

**⚡ Power Users** → [**Workflow Guide**](docs/workflow-guide.md) → [Advanced Examples](docs/examples.md#advanced-workflows) → [Performance Optimization](docs/examples.md#performance-optimization)

**🔧 Troubleshooting** → [**Workflow Guide Troubleshooting**](docs/workflow-guide.md#troubleshooting) → [Examples](docs/examples.md#error-handling-patterns) → [User Manual](docs/user-manual.md#troubleshooting)

## 🎯 Usage Examples

### Basic Download

```python
from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.core.url_extractor import URLExtractor
from src.app.settings import Settings

# Initialize components
settings = Settings()
downloader = DownloadManager(settings)
url_extractor = URLExtractor()

# Start the download manager
downloader.start()

# Create and add download task
task = DownloadTask(
    name="Sample Video",
    base_url="https://example.com/stream",
    key_url="https://example.com/key.bin",
    segments=100,
    output_file="/path/to/output.mp4",
    priority=TaskPriority.HIGH
)

task_id = downloader.add_task(task)
```

### Advanced Download with Error Handling

```python
from src.core import error_handler, retry_manager, bandwidth_monitor
from src.core.exceptions import VidTaniumException, ErrorCategory

# Initialize enhanced components
error_handler.start()
retry_manager.start()
bandwidth_monitor.start()

try:
    # Create task with advanced error handling
    task = DownloadTask(
        name="Protected Video",
        base_url="https://example.com/encrypted-stream",
        key_url="https://example.com/encryption.key",
        segments=200,
        output_file="/downloads/video.mp4",
        priority=TaskPriority.HIGH,
        max_retries=5,
        retry_delay=2.0
    )

    # Add task with monitoring
    task_id = downloader.add_task(task)

    # Monitor bandwidth during download
    bandwidth_stats = bandwidth_monitor.get_current_stats()
    print(f"Download speed: {bandwidth_stats.download_speed:.2f} MB/s")

except VidTaniumException as e:
    if e.category == ErrorCategory.NETWORK:
        print(f"Network error: {e.message}")
        print(f"Suggested actions: {e.suggested_actions}")
    else:
        print(f"Error: {e.message}")
```

### Batch Processing with Analytics

```python
from src.core import batch_progress_aggregator, queue_manager
from src.core.smart_prioritization_engine import SmartPrioritizationEngine

# Initialize batch processing components
batch_aggregator = batch_progress_aggregator
queue_mgr = queue_manager
prioritization_engine = SmartPrioritizationEngine()

# Batch download multiple URLs with smart prioritization
urls = [
    "https://example.com/video1.m3u8",
    "https://example.com/video2.m3u8",
    "https://example.com/video3.m3u8"
]

tasks = []
for i, url in enumerate(urls):
    task = DownloadTask(
        name=f"Video {i+1}",
        base_url=url,
        segments=100,
        output_file=f"/downloads/video_{i+1}.mp4",
        priority=TaskPriority.NORMAL
    )
    tasks.append(task)

# Apply smart prioritization
prioritized_tasks = prioritization_engine.prioritize_tasks(tasks)

# Add tasks to queue
for task in prioritized_tasks:
    queue_mgr.add_task(task)

# Monitor batch progress
batch_progress = batch_aggregator.get_batch_progress()
print(f"Overall progress: {batch_progress.overall_percentage:.1f}%")
print(f"ETA: {batch_progress.estimated_time_remaining}")
```

## 🛠️ Development

### Setting up Development Environment

1. **Clone and setup**

   ```bash
   git clone https://github.com/yourusername/VidTanium.git
   cd VidTanium
   uv sync --dev
   ```

2. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

3. **Run tests**

   ```bash
   pytest tests/
   ```

### Project Structure

- **Core Logic** (`src/core/`): Download engine, media processing, and business logic
- **GUI Components** (`src/gui/`): User interface built with PySide6 and Fluent Widgets
- **Application Layer** (`src/app/`): Application startup and lifecycle management
- **Configuration** (`config/`): Settings and configuration management
- **Tests** (`tests/`): Comprehensive test suites for all components

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test module
pytest tests/core/test_downloader.py

# Run with debug output
pytest -v -s
```

## 📊 Performance & Monitoring

VidTanium is optimized for performance with advanced monitoring capabilities:

### Core Performance Features

- **Async/Await**: Non-blocking I/O operations for maximum efficiency
- **Intelligent Thread Pool**: Dynamic thread management with configurable concurrency
- **Memory Management**: Efficient handling of large files with memory optimization
- **Smart Caching**: Intelligent caching of metadata, configurations, and network data
- **Progress Optimization**: Minimal overhead progress tracking with real-time updates

### Advanced Monitoring System

- **Bandwidth Monitoring**: Real-time network performance tracking with historical data
- **ETA Calculation**: Multiple algorithms (Linear, Exponential, Adaptive) for accurate predictions
- **Performance Analytics**: Network interface detection and baseline performance metrics
- **Resource Monitoring**: CPU, memory, and disk usage tracking during downloads
- **Circuit Breaker Protection**: Automatic fault detection and system protection

### Optimization Features

- **Smart Prioritization**: Intelligent task ordering based on size, priority, and network conditions
- **Adaptive Retry Logic**: Context-aware retry strategies with exponential backoff
- **Bandwidth Limiting**: Configurable bandwidth throttling to prevent network congestion
- **Queue Optimization**: Dynamic queue management with load balancing
- **Connection Pooling**: Efficient HTTP connection reuse and management

### Performance Metrics

- **Download Speed**: Real-time and average download speeds with trend analysis
- **Success Rate**: Task completion rates with error categorization
- **Resource Utilization**: System resource usage monitoring and optimization
- **Network Efficiency**: Connection success rates and retry statistics
- **Time Estimates**: Accurate ETA calculations with confidence intervals

## 🤝 Contributing

We welcome contributions! Please see our [Developer Guide](DEVELOPER_GUIDE.md) for details on:

- Code style and conventions
- Testing requirements
- Submission process
- Development workflow

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Troubleshooting

VidTanium includes an advanced error handling system that provides detailed diagnostics and suggested solutions.

### Intelligent Error Diagnosis

The application automatically categorizes errors and provides context-specific solutions:

- **Network Errors**: Connection timeouts, SSL issues, HTTP errors
- **Filesystem Errors**: Permission issues, disk space, file access
- **Encryption Errors**: Key retrieval failures, decryption issues
- **Resource Errors**: Memory limitations, CPU constraints
- **System Errors**: Platform-specific issues, dependency problems

### Common Issues & Solutions

#### Download fails with SSL errors

```bash
# Solution 1: Update certificates or disable SSL verification
python main.py --no-ssl-verify

# Solution 2: Configure SSL settings in advanced configuration
# Edit config/config.json:
{
    "advanced": {
        "verify_ssl": false,
        "ssl_cert_path": "/path/to/certificates"
    }
}
```

#### Network connection issues

```bash
# Check bandwidth monitoring for network diagnostics
# The application will automatically suggest:
# - Retry with different timeout settings
# - Use alternative network interfaces
# - Enable circuit breaker protection
```

#### FFmpeg not found

```bash
# Install FFmpeg
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg

# Or specify custom FFmpeg path in settings:
{
    "advanced": {
        "ffmpeg_path": "/custom/path/to/ffmpeg"
    }
}
```

#### Memory or performance issues

```bash
# The application provides automatic optimization suggestions:
# - Reduce concurrent downloads
# - Enable memory optimization mode
# - Adjust chunk size for large files
# - Use bandwidth limiting to reduce system load
```

#### Permission errors on Windows

```bash
# Run as administrator or check antivirus settings
# The error handler will provide specific suggestions based on the error context
```

### Advanced Diagnostics

Access detailed error information through:

- **Error Dialog**: User-friendly error messages with suggested actions
- **Analytics Dashboard**: Performance metrics and error trends
- **Log Viewer**: Detailed technical logs with error context
- **Status Widget**: Real-time system status and health monitoring

For comprehensive troubleshooting, see the [User Manual](docs/user-manual.md#troubleshooting).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PySide6](https://doc.qt.io/qtforpython/) - Cross-platform GUI toolkit
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - Modern Fluent Design components
- [FFmpeg](https://ffmpeg.org/) - Multimedia processing framework
- [aiofiles](https://github.com/Tinche/aiofiles) - Async file operations
- [PyCryptodome](https://pycryptodome.readthedocs.io/) - Cryptographic library
- [Loguru](https://github.com/Delgan/loguru) - Advanced logging with structured output
- [Playwright](https://playwright.dev/python/) - Web automation for dynamic content extraction
- [psutil](https://github.com/giampaolo/psutil) - System and process monitoring
- [aiosqlite](https://github.com/omnilib/aiosqlite) - Async SQLite database operations

## 📞 Support

- 📖 [Documentation](DOCUMENTATION.md)
- 🐛 [Issue Tracker](https://github.com/yourusername/VidTanium/issues)
- 💬 [Discussions](https://github.com/yourusername/VidTanium/discussions)
- 📧 Email: [support@vidtanium.com](mailto:support@vidtanium.com)

---

## 🎯 Complete User Journey

### For New Users
1. **📋 [Start with Workflow Guide](docs/workflow-guide.md)** - Complete step-by-step guide
2. **⚙️ [Follow Installation](docs/installation.md)** - Detailed setup instructions
3. **🚀 [Try First Download](docs/workflow-guide.md#your-first-download)** - Get started immediately
4. **💡 [Explore Examples](docs/examples.md)** - Learn from practical scenarios

### For Developers
1. **📋 [Review Workflow Guide](docs/workflow-guide.md)** - Understand the complete system
2. **💡 [Study Integration Examples](docs/examples.md#integration-examples)** - See real implementations
3. **📚 [Reference API Docs](docs/api-reference.md)** - Detailed technical documentation
4. **🔧 [Setup Development](docs/developer-guide.md)** - Contribute to the project

### For Advanced Users
1. **⚡ [Performance Optimization](docs/examples.md#performance-optimization)** - Maximize efficiency
2. **🔧 [Advanced Configuration](docs/installation.md#configuration-categories)** - Fine-tune settings
3. **🤖 [Automation Scripts](docs/examples.md#automation-scripts)** - Automate workflows
4. **🛠️ [Custom Integration](docs/examples.md#integration-examples)** - Build custom solutions

---

⭐ **Star this repo if you find it helpful!** ⭐

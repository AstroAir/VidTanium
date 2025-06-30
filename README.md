# VidTanium

> A powerful video download tool with built-in player and editor capabilities

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-blue.svg)](https://doc.qt.io/qtforpython/)
[![Fluent UI](https://img.shields.io/badge/Design-Fluent-lightblue.svg)](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)

## 🚀 Overview

VidTanium is a modern, feature-rich video download tool specifically designed for downloading encrypted M3U8 video streams. Built with Python and PySide6, it offers a beautiful Fluent Design interface combined with powerful download capabilities and integrated media processing tools.

### ✨ Key Features

- 🔐 **Encrypted M3U8 Support** - Full AES-128 encryption support with automatic key handling
- 🚀 **Multi-threaded Downloads** - High-speed parallel downloading with configurable concurrency
- 🎯 **Smart Retry Logic** - Intelligent error recovery and exponential backoff
- 🎨 **Modern UI** - Beautiful Fluent Design interface built with PySide6
- 📦 **Batch Processing** - Support for batch downloads and URL imports
- 🎬 **Media Processing** - Built-in video conversion, editing, and compression
- 📊 **Real-time Monitoring** - Live progress tracking and download statistics
- ⏰ **Task Scheduling** - Automated download management and scheduling
- 🌍 **Internationalization** - Multi-language support (English/Chinese)
- 🎛️ **Advanced Configuration** - Comprehensive settings and preferences

### 🏗️ Architecture

```text
VidTanium/
├── src/
│   ├── app/                    # Application lifecycle & startup
│   ├── core/                   # Core business logic
│   │   ├── analyzer.py         # Media content analysis
│   │   ├── downloader.py       # Download management
│   │   ├── media_processor.py  # Video processing
│   │   ├── m3u8_parser.py     # Playlist parsing
│   │   └── ...
│   ├── gui/                    # User interface
│   │   ├── main_window.py      # Main application window
│   │   ├── widgets/            # Custom UI components
│   │   └── dialogs/            # Dialog windows
│   └── locales/                # Translation files
├── config/                     # Configuration files
├── tests/                      # Test suites
└── docs/                       # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Windows, macOS, or Linux
- FFmpeg (for media processing features)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/VidTanium.git
   cd VidTanium
   ```

2. **Install dependencies**

   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -r requirements.txt
   ```

3. **Run the application**

   ```bash
   python main.py
   ```

### Command Line Usage

```bash
# Basic usage
python main.py

# With debug mode
python main.py --debug

# Download a specific URL
python main.py --url "https://example.com/video.m3u8"

# Use custom config directory
python main.py --config "/path/to/config"
```

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [📋 User Manual](USER_MANUAL.md) | Step-by-step guide for end users |
| [🔧 Developer Guide](DEVELOPER_GUIDE.md) | Development setup and contribution guide |
| [📚 API Reference](API_REFERENCE.md) | Detailed API documentation |
| [📖 Complete Documentation](DOCUMENTATION.md) | Comprehensive project documentation |

## 🎯 Usage Examples

### Basic Download

```python
from src.core.downloader import DownloadManager
from src.core.analyzer import MediaAnalyzer

# Initialize components
analyzer = MediaAnalyzer()
downloader = DownloadManager()

# Analyze and download
url = "https://example.com/video.m3u8"
media_info = await analyzer.analyze_url(url)
task = await downloader.create_task(media_info)
await downloader.start_download(task)
```

### Batch Processing

```python
# Batch download multiple URLs
urls = [
    "https://example.com/video1.m3u8",
    "https://example.com/video2.m3u8",
    "https://example.com/video3.m3u8"
]

for url in urls:
    media_info = await analyzer.analyze_url(url)
    task = await downloader.create_task(media_info)
    await downloader.queue_task(task)

await downloader.process_queue()
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

## 📊 Performance

VidTanium is optimized for performance with:

- **Async/Await**: Non-blocking I/O operations
- **Thread Pool**: Configurable concurrent downloads
- **Memory Management**: Efficient handling of large files
- **Caching**: Smart caching of metadata and configurations
- **Progress Optimization**: Minimal overhead progress tracking

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

### Common Issues

#### Download fails with SSL errors

```bash
# Solution: Update certificates or disable SSL verification
python main.py --no-ssl-verify
```

#### FFmpeg not found

```bash
# Install FFmpeg
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

#### Permission errors on Windows

```bash
# Run as administrator or check antivirus settings
```

For more troubleshooting tips, see the [User Manual](USER_MANUAL.md#troubleshooting).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PySide6](https://doc.qt.io/qtforpython/) - Cross-platform GUI toolkit
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - Modern Fluent Design components
- [FFmpeg](https://ffmpeg.org/) - Multimedia processing framework
- [aiofiles](https://github.com/Tinche/aiofiles) - Async file operations
- [PyCryptodome](https://pycryptodome.readthedocs.io/) - Cryptographic library

## 📞 Support

- 📖 [Documentation](DOCUMENTATION.md)
- 🐛 [Issue Tracker](https://github.com/yourusername/VidTanium/issues)
- 💬 [Discussions](https://github.com/yourusername/VidTanium/discussions)
- 📧 Email: [support@vidtanium.com](mailto:support@vidtanium.com)

---

⭐ **Star this repo if you find it helpful!** ⭐

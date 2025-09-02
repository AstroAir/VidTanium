# VidTanium - Video Download Tool Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
   - [Download Manager](#1-download-manager-srccoredloaderpy)
   - [Enhanced Error Handling](#enhanced-error-handling)
   - [Monitoring & Analytics](#monitoring--analytics)
   - [Queue Management](#queue-management)
   - [Task State Management](#task-state-management)
4. [User Interface](#user-interface)
   - [Main Window](#main-window)
   - [Analytics Dashboard](#analytics-dashboard)
   - [Responsive Design](#responsive-design)
5. [Installation & Setup](#installation--setup)
6. [Usage Guide](#usage-guide)
7. [Configuration](#configuration)
8. [Development](#development)
9. [Testing](#testing)
10. [API Reference](#api-reference)

## Quick Navigation

- **🚀 Getting Started**: [Installation Guide](INSTALLATION.md) → [User Manual](USER_MANUAL.md#getting-started)
- **👨‍💻 Development**: [Developer Guide](DEVELOPER_GUIDE.md) → [Project Structure](PROJECT_STRUCTURE.md)
- **📚 API Documentation**: [API Reference](API_REFERENCE.md) → [Error Handling API](API_REFERENCE.md#enhanced-error-handling-api)
- **🔧 Configuration**: [Installation Guide](INSTALLATION.md#configuration) → [Advanced Settings](INSTALLATION.md#configuration-categories)
- **🐛 Troubleshooting**: [User Manual](USER_MANUAL.md#troubleshooting) → [Error Diagnostics](USER_MANUAL.md#advanced-error-handling--diagnostics)

## Project Overview

**VidTanium** is a powerful and efficient video download tool specifically designed for downloading encrypted M3U8 video streams. Built with modern technology and a focus on user experience, VidTanium provides a comprehensive solution for video content management and processing.

### Key Features

- **Encrypted M3U8 Support**: Full support for AES-128 encrypted video stream downloads
- **Multi-threaded Downloads**: High-speed parallel downloading with configurable concurrent tasks
- **Smart Retry Mechanism**: Intelligent error recovery and retry logic for failed downloads
- **Modern User Interface**: Beautiful Fluent Design interface built with PySide6
- **Batch Processing**: Support for batch downloads and URL imports
- **Media Processing**: Built-in video conversion, editing, and compression tools
- **Real-time Monitoring**: Live progress tracking and download statistics
- **Schedule Management**: Task scheduling and automated download management
- **Internationalization**: Multi-language support (English/Chinese)

### Technical Specifications

- **Framework**: PySide6 (Qt6) with Fluent Design widgets
- **Language**: Python 3.11+
- **Architecture**: Modular component-based design
- **Threading**: Advanced thread pool management for optimal performance
- **Encryption**: Support for AES-128 decryption using PyCryptodome
- **Media Processing**: FFmpeg integration for video operations
- **Configuration**: JSON-based configuration management

## Architecture

VidTanium follows a modular architecture with clear separation of concerns:

```text
VidTanium/
├── src/
│   ├── app/           # Application layer
│   ├── core/          # Core business logic
│   ├── gui/           # User interface components
│   └── locales/       # Internationalization files
├── config/            # Configuration files
├── tests/             # Test suites
└── docs/              # Documentation
```

### Architecture Layers

1. **Application Layer** (`src/app/`): Entry point and application lifecycle management
2. **Core Layer** (`src/core/`): Business logic and data processing
3. **GUI Layer** (`src/gui/`): User interface and presentation logic
4. **Configuration Layer**: Settings and preferences management

## Core Components

For complete API reference, see [API Reference](API_REFERENCE.md).

### 1. Download Manager (`src/core/downloader.py`)

**Related Components**: [Error Handler](#enhanced-error-handling), [Queue Manager](#queue-management), [Bandwidth Monitor](#bandwidth-monitoring)
**User Guide**: [Download Manager Interface](USER_MANUAL.md#download-manager)
**Developer Guide**: [Download Manager Architecture](DEVELOPER_GUIDE.md#download-manager)

The heart of VidTanium's download functionality, responsible for:

- **Task Management**: Creating, queuing, and executing download tasks
- **Multi-threading**: Concurrent segment downloads with configurable limits
- **Progress Tracking**: Real-time progress updates and speed calculations
- **Error Handling**: Robust retry mechanisms and failure recovery
- **Encryption Support**: Automatic key retrieval and segment decryption

#### Key Classes

- `DownloadManager`: Main download orchestrator
- `DownloadTask`: Individual download task representation
- `TaskStatus`: Enumeration of task states
- `TaskPriority`: Priority system for task queuing

#### Features

- Priority-based task scheduling
- Configurable retry logic with exponential backoff
- Automatic cleanup of temporary files
- Progress persistence for download resumption
- Event-driven status updates

### 2. Media Analyzer (`src/core/analyzer.py`)

Intelligent media content analysis and URL processing:

- **URL Analysis**: Automatic detection of direct M3U8 links vs. web pages
- **Playlist Parsing**: Master and media playlist interpretation
- **Stream Selection**: Automatic best quality stream selection
- **Encryption Detection**: Identification of encryption methods and key URLs
- **Metadata Extraction**: Duration, resolution, and codec information

#### Supported Formats

- M3U8 playlists (HLS)
- AES-128 encrypted streams
- Multiple quality variants
- Relative and absolute URL resolution

### 3. M3U8 Parser (`src/core/m3u8_parser.py`)

Specialized parser for HLS (HTTP Live Streaming) manifests:

- **Master Playlist Parsing**: Stream variant extraction with quality information
- **Media Playlist Processing**: Segment URL and timing information
- **Encryption Handling**: Key URI and IV extraction
- **URL Pattern Recognition**: Segment URL pattern detection for batch processing

#### Core Classes

- `M3U8Parser`: Main parsing engine
- `M3U8Stream`: Stream representation with metadata
- `M3U8Segment`: Individual segment information
- `EncryptionMethod`: Encryption type enumeration

### 4. Media Processor (`src/core/media_processor.py`)

Comprehensive media processing capabilities:

- **Format Conversion**: Video/audio format transformation
- **Video Editing**: Clipping, trimming, and segment extraction
- **Audio Extraction**: Audio track isolation and conversion
- **Compression**: Quality-based and size-based video compression
- **Metadata Editing**: Media file metadata manipulation

#### Supported Operations

- Video format conversion (MP4, AVI, MKV, etc.)
- Audio extraction (MP3, AAC, WAV)
- Video compression with CRF or target size
- Metadata editing and preservation
- Batch processing capabilities

### 5. URL Extractor (`src/core/url_extractor.py`)

Advanced URL extraction and processing:

- **Text Processing**: URL extraction from various text sources
- **Web Scraping**: Media URL extraction from web pages
- **Pattern Matching**: Configurable URL pattern recognition
- **URL Validation**: Format validation and normalization
- **Filter System**: Include/exclude pattern filtering

### 6. Decryptor (`src/core/decryptor.py`)

Security and encryption handling:

- **AES-128 Decryption**: Standard HLS encryption support
- **Key Management**: Encryption key retrieval and caching
- **IV Handling**: Initialization vector processing
- **Stream Decryption**: Real-time segment decryption during download

### 7. File Merger (`src/core/merger.py`)

Video segment combination and optimization:

- **Segment Merging**: Efficient concatenation of video segments
- **Format Optimization**: Output format selection and optimization
- **Progress Tracking**: Merge operation progress monitoring
- **Error Recovery**: Handling of corrupted or missing segments

### 8. Task Scheduler (`src/core/scheduler.py`)

Advanced scheduling and automation:

- **Task Queuing**: Priority-based task queue management
- **Schedule Management**: Time-based task execution
- **Resource Management**: System resource optimization
- **Event Handling**: Task lifecycle event processing

### 9. Thread Pool Manager (`src/core/thread_pool.py`)

Centralized thread management:

- **Worker Threads**: Managed worker thread creation and lifecycle
- **Signal System**: Qt-based signal/slot communication
- **Error Handling**: Thread-safe error reporting and recovery
- **Resource Optimization**: Efficient thread pool utilization

## User Interface

VidTanium features a modern, responsive user interface built with PySide6 and Fluent Design principles.

### Main Window (`src/gui/main_window.py`)

Central application interface with navigation and content management:

- **Navigation System**: Sidebar navigation with categorized sections
- **Dashboard**: Overview of download statistics and quick actions
- **Download Manager**: Task list with real-time progress updates
- **Activity Logs**: Comprehensive logging with filtering and export
- **Settings**: Unified settings management interface

### Dashboard Interface (`src/gui/widgets/dashboard/`)

Modern dashboard with animated components:

#### Components

- **Hero Section**: Welcome message and quick actions
- **Statistics Section**: Real-time download statistics and system metrics
- **Task Preview**: Recent and active task overview
- **System Status**: Resource utilization and system health

#### Features

- Gradient backgrounds and smooth animations
- Real-time data updates
- Responsive design
- Quick action buttons

### Task Manager (`src/gui/widgets/task_manager.py`)

Comprehensive task management interface:

- **Task List**: Sortable and filterable task overview
- **Progress Visualization**: Modern progress bars with fluent design
- **Status Indicators**: Color-coded status badges with animations
- **Action Controls**: Start, pause, cancel, and retry operations
- **Bulk Operations**: Multi-task selection and batch actions

### Log Viewer (`src/gui/widgets/log/log_viewer.py`)

Advanced logging interface with enterprise features:

#### Features

- **Real-time Updates**: Live log streaming with auto-refresh
- **Advanced Filtering**: Multi-criteria filtering system
- **Export Capabilities**: Multiple export formats (JSON, CSV, TXT)
- **Search Functionality**: Text search with regex support
- **Pagination**: Efficient handling of large log volumes
- **Statistics**: Log level distribution and summary

### Settings Interface (`src/gui/widgets/settings/`)

Unified settings management:

#### Categories

- **General Settings**: Basic application preferences
- **Download Settings**: Concurrent limits, retry configuration
- **Network Settings**: Proxy, timeout, and SSL verification
- **Interface Settings**: Theme, language, and UI preferences
- **Advanced Settings**: Debug options and experimental features

### Dialogs

Specialized dialog interfaces:

- **Task Dialog**: New download task creation
- **Batch URL Dialog**: Bulk URL import and management
- **Media Processing Dialog**: Video editing and conversion
- **About Dialog**: Application information and credits
- **Settings Dialog**: Standalone settings management

### Theme Management (`src/gui/theme_manager.py`)

Comprehensive theming system:

- **Fluent Design**: Microsoft Fluent Design implementation
- **Dark/Light Modes**: Automatic and manual theme switching
- **Color Schemes**: Customizable accent colors
- **Component Styling**: Consistent styling across all components

## Installation & Setup

### Prerequisites

- Python 3.11 or higher
- FFmpeg (for media processing)
- Git (for development)

### Dependencies

Key dependencies are managed through `pyproject.toml`:

```toml
dependencies = [
    "aiofiles>=24.1.0",           # Async file operations
    "aiosqlite>=0.21.0",          # Async SQLite support
    "bs4>=0.0.2",                 # HTML parsing
    "loguru>=0.7.3",              # Advanced logging
    "playwright>=1.52.0",         # Web automation
    "psutil>=7.0.0",              # System monitoring
    "pycryptodome>=3.22.0",       # Encryption support
    "pyside6>=6.9.0",             # Qt6 framework
    "pyside6-fluent-widgets[full]>=1.8.7",  # Fluent Design widgets
    "pytest>=8.3.5",             # Testing framework
    "requests>=2.32.3",           # HTTP client
]
```

### Installation Steps

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/your-org/vidtanium.git
   cd vidtanium
   ```

2. **Set up Virtual Environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install -e .
   ```

4. **Install FFmpeg**:
   - Download from [FFmpeg official site](https://ffmpeg.org/download.html)
   - Add to system PATH
   - Verify installation: `ffmpeg -version`

5. **Run the Application**:

   ```bash
   python main.py
   ```

### Configuration

The application uses JSON-based configuration stored in `config/config.json`:

```json
{
    "QFluentWidgets": {
        "ThemeColor": "#ff009faa",
        "ThemeMode": "Auto"
    }
}
```

## Usage Guide

### Basic Usage

1. **Launch Application**: Run `python main.py`
2. **Navigate to Dashboard**: Overview of system status and quick actions
3. **Add Download Task**: Click "New Download" and enter M3U8 URL
4. **Monitor Progress**: Switch to "Download Manager" to track progress
5. **View Logs**: Check "Activity Logs" for detailed operation history

### Advanced Features

#### Batch Downloads

1. Navigate to "Download Manager"
2. Click "Batch Import"
3. Upload text file with URLs (one per line)
4. Configure batch settings
5. Start batch processing

#### Media Processing

1. Access "Media Processing" from dashboard
2. Select input video file
3. Choose operation (convert, clip, compress, extract audio)
4. Configure output settings
5. Process and save

#### Scheduled Downloads

1. Create download task
2. Access task options
3. Set schedule parameters
4. Enable automatic execution

### Keyboard Shortcuts

- `Ctrl+N`: New download task
- `Ctrl+R`: Refresh task list
- `Ctrl+P`: Pause all tasks
- `Ctrl+S`: Start all tasks
- `F5`: Refresh logs
- `Ctrl+,`: Open settings

## Configuration

### Settings Categories

#### General Settings

- **Auto Cleanup**: Automatic temporary file cleanup
- **Check Updates**: Automatic update checking
- **Startup Behavior**: Application launch preferences

#### Download Settings

- **Max Concurrent Tasks**: Number of simultaneous downloads (1-10)
- **Retry Attempts**: Maximum retry count for failed segments
- **Retry Delay**: Delay between retry attempts
- **Request Timeout**: HTTP request timeout duration
- **Chunk Size**: Download chunk size for optimization

#### Network Settings

- **Proxy Configuration**: HTTP/HTTPS proxy settings
- **User Agent**: Custom user agent string
- **SSL Verification**: Certificate verification options
- **Connection Timeout**: Network connection timeout

#### Interface Settings

- **Theme Mode**: Light, Dark, or Auto
- **Language**: Interface language selection
- **Notifications**: System notification preferences
- **Auto Refresh**: Automatic UI refresh intervals

### Configuration Files

#### Main Configuration (`config/config.json`)

Application-wide settings including theme and UI preferences.

#### Localization Files (`src/locales/`)

- `en.json`: English translations
- `zh_CN.json`: Chinese (Simplified) translations

## Development

### Project Structure

```
src/
├── app/
│   ├── application.py      # Main application class
│   └── settings.py         # Settings management
├── core/
│   ├── analyzer.py         # Media analysis
│   ├── decryptor.py        # Encryption handling
│   ├── downloader.py       # Download management
│   ├── m3u8_parser.py      # M3U8 parsing
│   ├── media_processor.py  # Media processing
│   ├── merger.py           # File merging
│   ├── scheduler.py        # Task scheduling
│   ├── thread_pool.py      # Thread management
│   └── url_extractor.py    # URL extraction
└── gui/
    ├── main_window.py      # Main interface
    ├── theme_manager.py    # Theme system
    ├── dialogs/            # Dialog components
    ├── widgets/            # Custom widgets
    └── utils/              # UI utilities
```

### Development Setup

1. **Clone and Install**:

   ```bash
   git clone https://github.com/your-org/vidtanium.git
   cd vidtanium
   pip install -e ".[dev]"
   ```

2. **Development Dependencies**:

   ```bash
   pip install pytest black flake8 mypy
   ```

3. **Code Quality Tools**:

   ```bash
   black src/                    # Code formatting
   flake8 src/                   # Linting
   mypy src/                     # Type checking
   ```

### Coding Standards

- **Python Version**: 3.11+
- **Type Hints**: Required for all public APIs
- **Docstrings**: Google style for all classes and functions
- **Code Formatting**: Black with 88-character line limit
- **Import Organization**: isort with profile black

### Architecture Guidelines

1. **Separation of Concerns**: Clear distinction between UI, business logic, and data layers
2. **Event-Driven Design**: Use Qt signals/slots for component communication
3. **Error Handling**: Comprehensive exception handling with logging
4. **Resource Management**: Proper cleanup of threads and file handles
5. **Testability**: Design for unit testing with dependency injection

## Testing

### Test Structure

```
tests/
├── core/
│   ├── test_analyzer.py
│   ├── test_decryptor.py
│   ├── test_downloader.py
│   ├── test_m3u8_parser.py
│   ├── test_media_processor.py
│   ├── test_merger.py
│   ├── test_scheduler.py
│   └── test_url_extractor.py
└── gui/
    └── test_components.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/core/test_downloader.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_download"
```

### Test Categories

#### Unit Tests

- Core component functionality
- Algorithm correctness
- Error handling scenarios

#### Integration Tests

- Component interaction
- End-to-end workflows
- External service integration

#### UI Tests

- Widget behavior
- User interaction flows
- Theme and styling

### Continuous Integration

The project uses GitHub Actions for CI/CD:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest --cov=src
```

## API Reference

### Core Classes

#### DownloadManager

```python
class DownloadManager:
    """Main download orchestrator"""
    
    def __init__(self, settings: Optional[SettingsProvider] = None):
        """Initialize download manager with optional settings"""
    
    def add_task(self, task: DownloadTask) -> str:
        """Add new download task"""
    
    def start_task(self, task_id: str) -> bool:
        """Start specific task"""
    
    def pause_task(self, task_id: str) -> bool:
        """Pause specific task"""
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel specific task"""
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get current task status"""
```

#### MediaAnalyzer

```python
class MediaAnalyzer:
    """Media content analysis and URL processing"""
    
    def analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyze URL and return media information"""
    
    def analyze_m3u8(self, url: str) -> Dict[str, Any]:
        """Analyze M3U8 file content"""
    
    def extract_media_from_page(self, url: str) -> List[str]:
        """Extract media URLs from web page"""
```

#### MediaProcessor

```python
class MediaProcessor:
    """Media processing and conversion"""
    
    def convert_format(self, input_file: str, output_file: str, 
                      format_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert media file format"""
    
    def clip_video(self, input_file: str, output_file: str,
                   start_time: Optional[str] = None, 
                   duration: Optional[str] = None) -> Dict[str, Any]:
        """Clip video segment"""
    
    def compress_video(self, input_file: str, output_file: str,
                       target_size_mb: Optional[int] = None,
                       quality: Optional[int] = None) -> Dict[str, Any]:
        """Compress video file"""
```

### Events and Signals

#### Download Events

```python
# Task status changed
on_task_status_changed(task_id: str, old_status: TaskStatus, new_status: TaskStatus)

# Progress update
on_task_progress(task_id: str, progress_data: ProgressDict)

# Task completed
on_task_completed(task_id: str, success: bool, message: str)

# Task failed
on_task_failed(task_id: str, error_message: str)
```

#### UI Signals

```python
# From TaskManager
task_action_requested(action: str, task_id: str)
task_selection_changed(task_id: str)

# From LogViewer
log_entry_selected(entry: LogEntry)
log_cleared()
log_exported(file_path: str)
```

### Configuration API

```python
class Settings:
    """Application settings management"""
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value"""
    
    def save_settings(self) -> None:
        """Persist settings to disk"""
    
    def load_settings(self) -> None:
        """Load settings from disk"""
```

## Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found

**Error**: "FFmpeg executable not found"
**Solution**:

- Install FFmpeg and add to system PATH
- Or specify FFmpeg path in settings

#### 2. Download Failures

**Error**: "All segments failed to download"
**Solutions**:

- Check network connectivity
- Verify URL validity
- Adjust retry settings
- Check proxy configuration

#### 3. Encryption Errors

**Error**: "Failed to download encryption key"
**Solutions**:

- Verify key URL accessibility
- Check SSL verification settings
- Ensure proper user agent

#### 4. Memory Issues

**Error**: High memory usage during downloads
**Solutions**:

- Reduce concurrent downloads
- Adjust chunk size
- Enable auto cleanup
- Monitor system resources

### Debug Mode

Enable debug logging:

```bash
python main.py --debug
```

Debug features:

- Verbose logging output
- Detailed error traces
- Performance metrics
- Network request details

### Log Files

Log files are stored in:

- Windows: `%USERPROFILE%\.encrypted_video_downloader\logs\`
- Linux/Mac: `~/.encrypted_video_downloader/logs/`

Log levels:

- `DEBUG`: Detailed debugging information
- `INFO`: General information messages
- `WARNING`: Warning conditions
- `ERROR`: Error conditions
- `CRITICAL`: Critical failures

## Contributing

### Getting Started

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Ensure code quality: `black src/ && flake8 src/ && mypy src/`
5. Run tests: `pytest`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open Pull Request

### Contribution Guidelines

- Follow coding standards and conventions
- Add tests for new functionality
- Update documentation as needed
- Ensure backward compatibility
- Write clear commit messages

### Development Workflow

1. **Issue Creation**: Create issue for bugs or feature requests
2. **Branch Creation**: Create feature branch from main
3. **Development**: Implement changes with tests
4. **Code Review**: Submit PR for review
5. **Integration**: Merge after approval

## License

VidTanium is released under the MIT License. See [LICENSE](LICENSE) file for details.

## Acknowledgments

- **PySide6**: Qt6 framework for Python
- **QFluentWidgets**: Fluent Design component library
- **FFmpeg**: Media processing engine
- **Loguru**: Modern logging library
- **Requests**: HTTP library for Python

## Support

For support and questions:

- GitHub Issues: <https://github.com/your-org/vidtanium/issues>
- Documentation: <https://vidtanium.readthedocs.io>
- Email: <support@vidtanium.dev>

---

*Last updated: January 2025*

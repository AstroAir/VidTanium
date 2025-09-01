# Project Structure

Detailed overview of VidTanium's codebase organization and architecture.

## Overview

VidTanium follows a modular, layered architecture with clear separation of concerns. The project structure is designed for maintainability, scalability, and ease of development.

## Directory Structure

```text
VidTanium/
├── src/                        # Source code
│   ├── app/                    # Application layer
│   ├── core/                   # Core business logic
│   ├── gui/                    # User interface
│   └── locales/                # Internationalization
├── config/                     # Configuration files
├── tests/                      # Test suites
├── docs/                       # Documentation
├── main.py                     # Application entry point
├── pyproject.toml             # Project configuration
├── README.md                  # Project overview
├── DOCUMENTATION.md           # Comprehensive documentation
├── API_REFERENCE.md           # API documentation
├── DEVELOPER_GUIDE.md         # Development guide
├── USER_MANUAL.md             # User instructions
├── INSTALLATION.md            # Installation guide
├── CONTRIBUTING.md            # Contribution guidelines
├── CHANGELOG.md               # Version history
└── LICENSE                    # MIT License
```

## Source Code Organization (`src/`)

### Application Layer (`src/app/`)

Entry point and application lifecycle management.

```text
src/app/
├── application.py             # Main application class
├── settings.py                # Application settings
└── __pycache__/              # Python cache files
```

**Key Components:**

- `Application`: Main application controller
- `Settings`: Configuration management
- Application startup and shutdown logic
- Global error handling

### Core Layer (`src/core/`)

Business logic and data processing components.

```text
src/core/
├── __init__.py                      # Package initialization and exports
├── downloader.py                    # Download management and orchestration
├── url_extractor.py                 # URL extraction and validation
├── media_processor.py               # Video processing and conversion
├── scheduler.py                     # Task scheduling and automation
├── thread_pool.py                   # Thread pool management
├── exceptions.py                    # Custom exception hierarchy
├── error_handler.py                 # Enhanced error handling system
├── retry_manager.py                 # Intelligent retry management
├── task_state_manager.py            # Task state persistence
├── bandwidth_monitor.py             # Network performance monitoring
├── eta_calculator.py                # ETA calculation algorithms
├── download_history_manager.py      # Download history tracking
├── batch_progress_aggregator.py     # Multi-task progress aggregation
├── queue_manager.py                 # Advanced queue management
├── smart_prioritization_engine.py   # Task prioritization system
├── utils/                           # Core utilities
│   ├── version_checker.py           # Version checking
│   └── __pycache__/                # Python cache files
└── __pycache__/                    # Python cache files
```

**Key Components:**

#### Download System

- `DownloadManager`: Core download orchestration with multi-threading
- `DownloadTask`: Individual download task representation with state management
- `ThreadPoolManager`: Advanced concurrent execution management
- `QueueManager`: Intelligent task queuing and prioritization
- `SmartPrioritizationEngine`: Dynamic task ordering based on multiple factors

#### Enhanced Error Handling & Recovery

- `EnhancedErrorHandler`: Intelligent error categorization and handling
- `VidTaniumException`: Custom exception hierarchy with context information
- `IntelligentRetryManager`: Context-aware retry strategies with circuit breaker
- `TaskStateManager`: Persistent task state tracking and recovery

#### Monitoring & Analytics

- `BandwidthMonitor`: Real-time network performance tracking
- `ETACalculator`: Advanced time estimation with multiple algorithms
- `DownloadHistoryManager`: Comprehensive download tracking and analytics
- `BatchProgressAggregator`: Multi-task progress monitoring and aggregation

#### Media Processing

- `MediaProcessor`: Video conversion, editing, and compression
- `URLExtractor`: URL validation, extraction, and processing
- `TaskScheduler`: Task automation, timing, and scheduling

#### Utilities & Support

- Version checking and update management
- Configuration management and validation
- Logging and diagnostic utilities

### GUI Layer (`src/gui/`)

User interface components built with PySide6.

```text
src/gui/
├── __init__.py                      # Package initialization with enhanced components
├── main_window.py                   # Primary application window with responsive design
├── theme_manager.py                 # Enhanced theme management system
├── dialogs/                         # Dialog windows
│   ├── __init__.py
│   ├── about_dialog.py              # About application dialog
│   ├── batch_url_dialog.py          # Batch URL input dialog
│   ├── task_dialog.py               # Task management dialog
│   ├── confirmation_dialog.py       # Smart confirmation dialogs
│   ├── media_processing_dialog.py   # Media processing options
│   ├── schedule_dialog.py           # Task scheduling dialog
│   ├── settings_config.py           # Settings configuration
│   ├── batch_conversion/            # Batch conversion dialogs
│   ├── batch_url/                   # Batch URL dialogs
│   ├── schedule/                    # Scheduling dialogs
│   └── settings/                    # Settings dialogs
├── utils/                           # GUI utilities
│   ├── design_system.py             # Design system and styling
│   ├── formatters.py                # Data formatting utilities
│   ├── i18n.py                      # Internationalization support
│   ├── responsive.py                # Responsive design system
│   ├── theme.py                     # Theme definitions
│   └── __pycache__/                # Python cache files
├── widgets/                         # Custom UI widgets
│   ├── __init__.py
│   ├── task_manager.py              # Advanced task management widget
│   ├── error_dialog.py              # Enhanced error presentation
│   ├── status_widget.py             # Real-time status monitoring
│   ├── tooltip.py                   # Smart tooltip system
│   ├── analytics_dashboard.py       # Performance analytics dashboard
│   ├── bulk_operations_manager.py   # Bulk operations interface
│   ├── navigation.py                # Navigation components
│   ├── progress.py                  # Advanced progress widgets
│   ├── dashboard/                   # Dashboard components
│   │   ├── dashboard_interface.py   # Main dashboard interface
│   │   └── metric_cards.py          # Performance metric cards
│   ├── log/                         # Log-related widgets
│   │   ├── log_viewer.py            # Enhanced log display
│   │   └── log_filters.py           # Log filtering system
│   ├── schedule/                    # Schedule widgets
│   └── settings/                    # Settings widgets
│       ├── settings_interface.py    # Main settings interface
│       └── advanced_settings.py    # Advanced configuration options
└── __pycache__/                    # Python cache files
```

**Key Components:**

#### Main Interface

- `MainWindow`: Primary application interface with responsive design and navigation
- `DashboardInterface`: Enhanced download management dashboard with analytics
- `EnhancedThemeManager`: Advanced theme management with system integration
- `ResponsiveManager`: Adaptive UI system for different screen sizes

#### Advanced Widgets

- `TaskManager`: Comprehensive task management with bulk operations support
- `AnalyticsDashboard`: Performance metrics and visualization dashboard
- `BulkOperationsManager`: Efficient multi-task management interface
- `ErrorDialog`: User-friendly error presentation with suggested solutions
- `StatusWidget`: Real-time system status and health monitoring
- `LogViewer`: Enhanced log display with filtering and search capabilities

#### Specialized Dialogs

- `BatchURLDialog`: Bulk URL processing
- `MediaProcessingDialog`: Video conversion options
- `ScheduleDialog`: Task automation setup
- `TaskDialog`: Download task configuration

#### Custom Widgets

- `TaskManager`: Download queue management
- `LogViewer`: Real-time log display
- `ScheduleManager`: Automated task handling
- `SystemTray`: Background operation support

#### UI Utilities

- `FluentProgress`: Modern progress indicators
- `ProgressReporter`: Progress tracking system
- `Formatters`: Data display formatting
- `I18n`: Multi-language support

### Localization (`src/locales/`)

Internationalization and language support.

```text
src/locales/
├── en.json                  # English translations
└── zh_CN.json              # Simplified Chinese translations
```

**Supported Languages:**

- English (default)
- Simplified Chinese
- Extensible for additional languages

## Configuration (`config/`)

Application configuration and settings.

```text
config/
└── config.json             # Main configuration file
```

**Configuration Areas:**

- UI theme and appearance
- Download settings
- Network configuration
- Performance tuning
- Feature toggles

## Testing (`tests/`)

Comprehensive test suites for all components.

```text
tests/
├── core/                   # Core module tests
│   ├── test_analyzer.py    # Media analyzer tests
│   ├── test_decryptor.py   # Decryption tests
│   ├── test_m3u8_parser.py # Playlist parser tests
│   ├── test_media_processor.py  # Media processing tests
│   ├── test_merger.py      # File merger tests
│   ├── test_scheduler.py   # Scheduler tests
│   ├── test_url_extractor.py   # URL extractor tests
│   └── utils/              # Core utility tests
│       └── test_version_checker.py
└── test/                   # Additional test files
    ├── auto.py             # Automated testing scripts
    ├── test_url.py         # URL testing utilities
    └── url.py              # URL test data
```

**Test Coverage:**

- Unit tests for individual components
- Integration tests for component interaction
- End-to-end tests for complete workflows
- Performance and stress testing

## Documentation (`docs/`)

Project documentation and guides.

```text
docs/
├── PROJECT_STRUCTURE.md    # This file
└── [Generated API docs]    # Auto-generated documentation
```

## Key Design Patterns

### 1. Layered Architecture

```text
┌─────────────────┐
│   GUI Layer     │  ← User Interface (PySide6)
├─────────────────┤
│ Application     │  ← Application Logic & Lifecycle
├─────────────────┤
│   Core Layer    │  ← Business Logic & Processing
├─────────────────┤
│ Configuration   │  ← Settings & Preferences
└─────────────────┘
```

### 2. Component Interaction

```text
MainWindow ──→ DownloadManager ──→ ThreadPool
    │               │                  │
    ├─→ TaskManager ├─→ MediaAnalyzer ─┘
    │               │
    └─→ LogViewer   └─→ M3U8Parser
```

### 3. Data Flow

```text
URL Input → Analysis → Task Creation → Download → Processing → Completion
    │          │           │             │           │            │
    │          │           │             │           │            └─→ UI Update
    │          │           │             │           └─→ File Merger
    │          │           │             └─→ Progress Tracking
    │          │           └─→ Queue Management
    │          └─→ Metadata Extraction
    └─→ Validation
```

## Development Guidelines

### File Naming Conventions

- **Snake case** for Python files: `download_manager.py`
- **Pascal case** for classes: `DownloadManager`
- **Lowercase** with underscores for packages: `gui_widgets`

### Import Organization

```python
# Standard library
import asyncio
import json
from pathlib import Path

# Third-party libraries
import aiofiles
from PySide6.QtWidgets import QWidget

# Local imports
from src.core.downloader import DownloadManager
from src.gui.widgets import TaskWidget
```

### Code Organization Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Dependency Injection**: Avoid tight coupling between components
3. **Interface Segregation**: Small, focused interfaces
4. **Open/Closed**: Open for extension, closed for modification

### Testing Strategy

```text
tests/
├── unit/           # Test individual functions/methods
├── integration/    # Test component interactions
├── e2e/           # Test complete user workflows
└── fixtures/      # Test data and mock objects
```

## Extension Points

### Adding New Features

1. **Core Logic**: Extend `src/core/` with new processors
2. **UI Components**: Add widgets to `src/gui/widgets/`
3. **Dialogs**: Create new dialogs in `src/gui/dialogs/`
4. **Configuration**: Extend `config/config.json`

### Plugin Architecture

The codebase is designed to support plugins:

```python
# Example plugin structure
class DownloadPlugin:
    def pre_download(self, task): pass
    def post_download(self, task): pass
    def process_segment(self, segment): pass
```

### Internationalization

Add new languages by:

1. Creating new JSON files in `src/locales/`
2. Following existing translation key structure
3. Testing UI layout with translated text

## Performance Considerations

### Memory Management

- Streaming file operations for large downloads
- Efficient buffer management in download threads
- Cleanup of temporary files and resources

### Concurrency

- Thread pool limits to prevent resource exhaustion
- Async/await for I/O operations
- Queue management for task prioritization

### Storage

- Temporary file handling
- Download resume capabilities
- Efficient file merging operations

---

This structure supports VidTanium's goals of maintainability, performance, and extensibility while providing clear boundaries between different aspects of the application.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Run the main application
python main.py

# Run with debug logging
python main.py --debug

# Run with specific URL for download
python main.py --url "https://example.com/video.m3u8"

# Run with custom config directory
python main.py --config "/path/to/config"
```

### Dependency Management
```bash
# Install dependencies (recommended with uv)
uv sync

# Install dependencies with pip
pip install -e .

# Install development dependencies
uv sync --dev
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test module
pytest tests/core/test_downloader.py

# Run with debug output
pytest -v -s
```

### Code Quality
```bash
# Run pre-commit hooks (if configured)
pre-commit install
pre-commit run --all-files
```

## Architecture Overview

VidTanium is a Python-based video downloader with a PySide6 GUI, specifically designed for encrypted M3U8 video streams. The application follows a modular architecture:

### Core Components

- **Application Layer** (`src/app/`): Application lifecycle, settings management, and logging configuration
- **Core Engine** (`src/core/`): Business logic for downloading, parsing, encryption/decryption, and media processing
- **GUI Layer** (`src/gui/`): PySide6-based user interface with Fluent Design components
- **Localization** (`src/locales/`): Multi-language support (English/Chinese)

### Key Design Patterns

1. **Async/Await Architecture**: Core download operations use async patterns for non-blocking I/O
2. **Thread Pool Management**: Configurable concurrent downloads via `src/core/thread_pool.py`
3. **Event-Driven UI**: GUI components communicate through Qt signals/slots
4. **Plugin-Style Architecture**: Modular components can be extended independently

### Critical Files

- `main.py`: Application entry point with CLI argument parsing
- `src/app/application.py`: Main application class, coordinates all subsystems
- `src/core/downloader.py`: Core download manager with task queuing and progress tracking
- `src/core/m3u8_parser.py`: M3U8 playlist parsing and segment extraction
- `src/core/decryptor.py`: AES-128 decryption for encrypted segments
- `src/gui/main_window.py`: Primary application window and UI coordination

### Data Flow

1. **URL Analysis**: URLs are parsed by `analyzer.py` to extract metadata
2. **Task Creation**: Download tasks are created and queued in `downloader.py`
3. **Segment Processing**: M3U8 playlists are parsed, segments downloaded and decrypted
4. **Progress Tracking**: Real-time progress updates flow from core to GUI via signals
5. **File Assembly**: Downloaded segments are merged by `merger.py`

### State Management

- **Settings**: Persistent configuration managed by `src/app/settings.py`
- **Task State**: Download tasks maintain state via `TaskStatus` enum in `downloader.py`
- **UI State**: GUI state managed by individual widgets with theme support

### Threading Model

- **Main Thread**: GUI and event handling
- **Download Threads**: Managed by `ThreadPoolManager` in `src/core/thread_pool.py`
- **Background Tasks**: Scheduling and monitoring via `src/core/scheduler.py`

## Development Guidelines

### Code Organization

- Follow the existing module structure when adding new features
- Keep GUI components in `src/gui/` separate from business logic in `src/core/`
- Use type hints consistently (project uses extensive typing)
- Maintain async/await patterns for I/O operations

### Testing Strategy

- Core business logic tests in `tests/core/`
- GUI tests should mock core components
- Use pytest fixtures for complex setup
- Test both success and failure scenarios for download operations

### Internationalization

- All user-facing strings should use the i18n system via `src/gui/utils/i18n.py`
- Add new strings to both `src/locales/en.json` and `src/locales/zh_CN.json`
- Use `tr()` function for translatable strings in GUI components

### Error Handling

- Use loguru for logging (`from loguru import logger`)
- Implement proper error recovery in download operations
- Provide meaningful error messages to users via the GUI
- Log detailed error information for debugging

### Performance Considerations

- Downloads use configurable thread pools - respect user settings
- Implement proper memory management for large files
- Use async operations for network I/O
- Cache metadata when possible to reduce repeated parsing
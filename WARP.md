# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

VidTanium is a modern Python-based video downloader specifically designed for encrypted M3U8 video streams. It features a PySide6 GUI with Fluent Design components and a sophisticated download engine with advanced error handling, retry mechanisms, and performance optimization.

## Development Commands

### Running the Application
```bash
# Start GUI application
python main.py

# Run with debug logging
python main.py --debug

# Download specific URL directly
python main.py --url "https://example.com/video.m3u8"

# Run with custom configuration directory
python main.py --config-dir "/path/to/config"

# List available configuration presets
python main.py --list-presets

# Validate current configuration
python main.py --validate-config
```

### Dependency Management
```bash
# Install dependencies (recommended - uses uv for fast package management)
uv sync

# Install development dependencies
uv sync --dev

# Alternative with pip
pip install -e .
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src

# Run specific test file
pytest tests/core/test_downloader.py

# Run tests by marker
pytest -m unit  # Unit tests only
pytest -m gui   # GUI tests only
pytest -m integration  # Integration tests only

# Run with verbose output
pytest -v -s
```

### Code Quality
```bash
# Run linting and formatting with ruff
ruff check src/
ruff format src/

# Run type checking
mypy src/

# Run security analysis
bandit -r src/
```

### Building and Packaging
```bash
# Build executable with PyInstaller (various profiles available)
python build_config.py --profile release

# Build development version
python build_config.py --profile development

# Create platform-specific packages
python scripts/build_all.py

# Build Docker image
python scripts/build_docker.py
```

### Documentation
```bash
# Build documentation with MkDocs
mkdocs serve  # Development server
mkdocs build  # Build static documentation

# Install documentation dependencies
pip install -r requirements-docs.txt
```

## Architecture Overview

### Core Components

**Application Layer** (`src/app/`)
- `application.py`: Main application class with centralized initialization system
- `settings.py`: Enhanced configuration management with multiple backends
- `logging_config.py`: Structured logging configuration with loguru

**Core Engine** (`src/core/`)
- `downloader.py`: Main download manager with task queue and progress tracking
- `m3u8_parser.py`: M3U8 playlist parsing and stream extraction
- `decryptor.py`: AES-128 decryption for encrypted video segments
- `error_handler.py`: Comprehensive error categorization and recovery
- `retry_manager.py`: Intelligent retry logic with circuit breaker pattern
- `bandwidth_monitor.py`: Real-time network performance tracking
- `queue_manager.py`: Advanced task queue with priority management

**GUI Layer** (`src/gui/`)
- `main_window.py`: Primary application window with component orchestration
- `theme_manager.py`: Enhanced theme system with Fluent Design integration
- `widgets/`: Custom UI components including dashboard and task management
- `dialogs/`: Modal dialogs for various user interactions

**Enhanced Systems**
- Advanced error handling with categorized exceptions and suggested actions
- Circuit breaker pattern for network resilience
- Intelligent recovery mechanisms with progressive retry strategies
- Performance optimization with memory management and connection pooling
- Comprehensive progress tracking with multiple ETA calculation algorithms

### Key Design Patterns

1. **Async/Await Architecture**: Core download operations use asyncio for non-blocking I/O
2. **Centralized Initialization**: Application startup uses a dependency-aware initialization system
3. **Component Registry**: GUI components are registered and managed through a centralized registry
4. **Event-Driven Communication**: Components communicate through Qt signals/slots and custom event system
5. **Resource Management**: Automatic cleanup and optimization of system resources
6. **Plugin-Style Architecture**: Modular components can be extended independently

### Data Flow

1. **URL Processing**: URLs are analyzed and validated through `analyzer.py`
2. **Task Creation**: Download tasks are created with priority and queued in `downloader.py`
3. **M3U8 Processing**: Playlists are parsed, segments extracted and validated
4. **Download Execution**: Segments are downloaded with encryption handling and progress tracking
5. **Error Handling**: Comprehensive error categorization with intelligent recovery strategies
6. **Progress Updates**: Real-time progress flows from core to GUI via signal system

### State Management

- **Configuration**: Multi-backend settings system with validation and migration support
- **Task State**: Download tasks maintain persistent state with resume capability
- **Error Context**: Detailed error tracking with suggested recovery actions
- **Performance Metrics**: Real-time monitoring of bandwidth, resource usage, and system health

## Development Guidelines

### Code Organization
- Follow the existing modular architecture when adding features
- Keep GUI logic separate from business logic (core vs gui separation)
- Use comprehensive type hints throughout the codebase
- Maintain async/await patterns for I/O operations
- Leverage the centralized error handling and resource management systems

### Testing Strategy
- Unit tests in `tests/core/` for business logic
- GUI tests in `tests/gui/` using mock components
- Integration tests in `tests/integration/` for end-to-end scenarios
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.gui`, `@pytest.mark.integration`
- Mock external dependencies and network calls
- Test both success and failure scenarios extensively

### Error Handling
- Use the centralized error handling system via `error_handler.py`
- Categorize errors appropriately using `ErrorCategory` enum
- Provide actionable error messages with suggested solutions
- Leverage intelligent retry mechanisms for transient failures
- Use circuit breaker pattern for network operations

### Performance Considerations
- Respect user-configured concurrency limits
- Use connection pooling for HTTP requests
- Implement proper memory management for large files
- Leverage bandwidth monitoring for optimization
- Use adaptive timeout mechanisms
- Implement progressive recovery for failed operations

### Internationalization
- All user-facing strings must use the i18n system via `src/gui/utils/i18n.py`
- Add strings to both `src/locales/en.json` and `src/locales/zh_CN.json`
- Use `tr()` function for translatable strings in GUI components

### Configuration Management
- Use the enhanced settings system with validation
- Support multiple configuration backends (JSON, YAML, TOML)
- Implement configuration migration for version updates
- Validate configuration changes before applying
- Support configuration presets for different use cases

## Important Files and Their Purposes

- `main.py`: Application entry point with comprehensive CLI argument handling
- `build_config.py`: Advanced PyInstaller configuration with multiple build profiles
- `pyproject.toml`: Modern Python project configuration with dependency groups
- `ruff.toml`: Comprehensive code quality configuration
- `pytest.ini`: Test configuration with markers and coverage settings
- `docker-compose.yml`: Container orchestration for development and deployment
- `CLAUDE.md`: Contains important architecture details and development patterns

## Common Development Patterns

### Adding New Download Features
1. Extend the `DownloadTask` class in `src/core/downloader.py`
2. Add corresponding UI elements in `src/gui/widgets/`
3. Update the settings schema if new configuration options are needed
4. Add comprehensive tests covering success and failure scenarios
5. Update error handling categories if new error types are introduced

### Implementing Error Recovery
1. Use the existing error categorization system
2. Implement recovery strategies in the appropriate manager classes
3. Add circuit breaker protection for external services
4. Update the intelligent recovery system with new patterns
5. Provide clear user feedback through the error dialog system

### Performance Optimization
1. Leverage existing monitoring systems (`bandwidth_monitor.py`, `resource_manager.py`)
2. Use connection pooling and adaptive timeouts
3. Implement memory optimization strategies
4. Add performance metrics to the analytics dashboard
5. Test under various network and system conditions

This repository represents a sophisticated video downloading application with extensive error handling, performance optimization, and user experience features. The architecture is designed for extensibility while maintaining high reliability and performance standards.

# VidTanium Developer Guide

## Development Environment Setup

### Prerequisites

Before starting development on VidTanium, ensure you have the following installed:

- **Python 3.11+**: Latest Python version for optimal performance
- **Git**: Version control system
- **FFmpeg**: Media processing engine
- **Qt6**: GUI framework (installed with PySide6)

### Development Tools

Recommended development tools:

- **IDE**: VS Code, PyCharm, or similar with Python support
- **Code Formatting**: Black, isort
- **Linting**: flake8, pylint
- **Type Checking**: mypy
- **Testing**: pytest
- **Documentation**: Sphinx (optional)

### Environment Setup

1. **Clone Repository**:

   ```bash
   git clone https://github.com/your-org/vidtanium.git
   cd vidtanium
   ```

2. **Create Virtual Environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**:

   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Pre-commit Hooks** (recommended):

   ```bash
   pre-commit install
   ```

5. **Verify Installation**:

   ```bash
   python main.py --version
   pytest tests/
   ```

## Project Architecture

### Architectural Principles

VidTanium follows several key architectural principles:

1. **Separation of Concerns**: Clear boundaries between UI, business logic, and data layers
2. **Event-Driven Design**: Loose coupling through Qt's signal/slot mechanism
3. **Modularity**: Pluggable components with well-defined interfaces
4. **Testability**: Dependency injection and mock-friendly design
5. **Extensibility**: Plugin-like architecture for future enhancements

### Layer Architecture

```
┌─────────────────────────────────────┐
│           Presentation Layer         │
│         (GUI Components)            │
├─────────────────────────────────────┤
│           Application Layer          │
│       (Coordination & Events)       │
├─────────────────────────────────────┤
│            Business Layer           │
│        (Core Components)            │
├─────────────────────────────────────┤
│            Data Layer               │
│     (Storage & Configuration)       │
└─────────────────────────────────────┘
```

#### Presentation Layer (`src/gui/`)

Handles all user interface concerns:

- **Main Window**: Central application interface
- **Widgets**: Reusable UI components
- **Dialogs**: Modal interaction windows
- **Theme Management**: Visual styling and themes
- **Internationalization**: Multi-language support

#### Application Layer (`src/app/`)

Coordinates between layers:

- **Application Class**: Main application lifecycle
- **Settings Management**: Configuration persistence
- **Event Coordination**: Cross-component communication
- **Resource Management**: Application-wide resources

#### Business Layer (`src/core/`)

Core application logic:

- **Download Management**: Video download orchestration
- **Media Processing**: Video/audio manipulation
- **Analysis**: URL and content analysis
- **Scheduling**: Task queue and timing
- **Thread Management**: Concurrent operation handling

#### Data Layer

Data persistence and configuration:

- **Configuration Files**: JSON-based settings
- **Progress Tracking**: Download state persistence
- **Logging**: Structured application logging
- **Temporary Files**: Download segment management

### Component Communication

Components communicate through well-defined interfaces:

```python
# Signal/Slot Pattern (Qt-based)
class DownloadManager(QObject):
    task_progress = Signal(str, dict)  # task_id, progress_data
    task_completed = Signal(str, bool)  # task_id, success

# Observer Pattern (Callback-based)
class TaskManager:
    def __init__(self):
        self.on_task_action = None  # Callback for task actions
    
    def handle_action(self, action, task_id):
        if self.on_task_action:
            self.on_task_action(action, task_id)

# Dependency Injection
class MediaProcessor:
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
```

## Core Components Deep Dive

### Download Manager

The `DownloadManager` is the heart of VidTanium's download functionality.

#### Design Patterns

**Producer-Consumer Pattern**:

```python
class DownloadManager:
    def __init__(self):
        self.tasks_queue = PriorityQueue()  # Producer adds tasks
        self.scheduler_thread = Thread(target=self._scheduler_loop)  # Consumer processes tasks
```

**State Machine Pattern**:

```python
class DownloadTask:
    def transition_to(self, new_status: TaskStatus):
        # Validate state transitions
        valid_transitions = {
            TaskStatus.PENDING: [TaskStatus.RUNNING, TaskStatus.CANCELED],
            TaskStatus.RUNNING: [TaskStatus.PAUSED, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED],
            TaskStatus.PAUSED: [TaskStatus.RUNNING, TaskStatus.CANCELED],
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            raise InvalidStateTransition(f"Cannot transition from {self.status} to {new_status}")
        
        old_status = self.status
        self.status = new_status
        self.notify_status_change(old_status, new_status)
```

#### Thread Safety

The DownloadManager uses several synchronization mechanisms:

```python
class DownloadManager:
    def __init__(self):
        self.lock = threading.RLock()  # Reentrant lock for nested calls
        self.tasks = {}  # Protected by lock
        self.active_tasks = set()  # Protected by lock
        self.event_queue = Queue()  # Thread-safe queue
    
    def add_task(self, task: DownloadTask) -> str:
        with self.lock:
            task_id = task.task_id
            self.tasks[task_id] = task
            self.tasks_queue.put((task.priority.value, time.time(), task_id))
            return task_id
```

### Media Analyzer

The `MediaAnalyzer` provides intelligent content analysis.

#### Strategy Pattern Implementation

```python
class MediaAnalyzer:
    def __init__(self):
        self.analyzers = {
            'direct_m3u8': DirectM3U8Analyzer(),
            'webpage': WebpageAnalyzer(),
            'api_endpoint': APIEndpointAnalyzer()
        }
    
    def analyze_url(self, url: str) -> Dict[str, Any]:
        # Determine appropriate strategy
        strategy = self._select_strategy(url)
        return self.analyzers[strategy].analyze(url)
```

#### Chain of Responsibility

```python
class AnalysisChain:
    def __init__(self):
        self.handlers = [
            DirectM3U8Handler(),
            WebpageM3U8Handler(),
            APIEndpointHandler(),
            FallbackHandler()
        ]
    
    def handle(self, url: str) -> Dict[str, Any]:
        for handler in self.handlers:
            if handler.can_handle(url):
                return handler.handle(url)
        
        return {"success": False, "error": "No suitable handler found"}
```

### GUI Architecture

The GUI follows the Model-View-Controller (MVC) pattern with Qt's signal/slot mechanism.

#### Component Hierarchy

```python
# Main Window (Controller)
class MainWindow(FluentWindow):
    def __init__(self):
        self.download_manager = DownloadManager()  # Model
        self.task_manager = TaskManager()  # View
        
        # Connect Model to View
        self.download_manager.task_progress.connect(
            self.task_manager.update_progress
        )

# Task Manager (View)
class TaskManager(QWidget):
    task_action_requested = Signal(str, str)  # action, task_id
    
    def update_progress(self, task_id: str, progress: dict):
        # Update UI elements
        task_widget = self.task_widgets[task_id]
        task_widget.set_progress(progress)

# Download Manager (Model)
class DownloadManager(QObject):
    task_progress = Signal(str, dict)
    
    def _emit_progress(self, task_id: str, progress: dict):
        self.task_progress.emit(task_id, progress)
```

#### Custom Widget Development

Creating custom widgets follows Qt best practices:

```python
class ModernProgressBar(QWidget):
    value_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._maximum = 100
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        # Initialize UI elements
        self.setMinimumHeight(8)
        self.setAttribute(Qt.WA_StyledBackground, True)
    
    def _setup_animations(self):
        # Setup property animations
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setValue(self, value: int):
        if value != self._value:
            old_value = self._value
            self._value = value
            self.value_changed.emit(value)
            self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        # Custom drawing code
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        bg_rect = self.rect()
        painter.fillRect(bg_rect, QColor("#E0E0E0"))
        
        # Draw progress
        progress_width = (self._value / self._maximum) * bg_rect.width()
        progress_rect = QRect(0, 0, int(progress_width), bg_rect.height())
        painter.fillRect(progress_rect, QColor("#0078D4"))
```

## Development Workflow

### Git Workflow

VidTanium uses a modified GitFlow workflow:

```
main branch
├── develop branch
│   ├── feature/new-download-engine
│   ├── feature/improved-ui
│   └── feature/batch-processing
├── release/v1.2.0
└── hotfix/critical-bug-fix
```

#### Branch Types

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: New features and enhancements
- **release/***: Release preparation
- **hotfix/***: Critical bug fixes

#### Commit Conventions

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `chore`: Build/tooling changes

Examples:

```
feat(downloader): add support for DASH streams

Add basic DASH manifest parsing and segment downloading.
Supports both live and on-demand streams.

Closes #123
```

### Code Style Guidelines

#### Python Style

Follow PEP 8 with these specific conventions:

```python
# Imports
import os
import sys
from typing import Dict, List, Optional, Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from .components import BaseComponent

# Class definitions
class DownloadManager(QObject):
    """Download manager with comprehensive task handling.
    
    This class provides centralized download management including
    task queuing, progress tracking, and error recovery.
    
    Attributes:
        tasks: Dictionary of active download tasks
        queue: Priority queue for task scheduling
    """
    
    # Signals
    task_started = Signal(str)
    task_completed = Signal(str, bool)
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None) -> None:
        """Initialize download manager.
        
        Args:
            settings: Optional configuration dictionary
        """
        super().__init__()
        self._settings = settings or {}
        self._tasks: Dict[str, DownloadTask] = {}
    
    def add_task(self, task: DownloadTask) -> str:
        """Add new download task.
        
        Args:
            task: Download task to add
            
        Returns:
            Unique task identifier
            
        Raises:
            ValueError: If task is invalid
        """
        if not task.is_valid():
            raise ValueError("Invalid task configuration")
        
        task_id = self._generate_task_id()
        self._tasks[task_id] = task
        return task_id
```

#### Type Hints

Use comprehensive type hints:

```python
from typing import Dict, List, Optional, Union, Callable, Any, Protocol

# Protocol for duck typing
class SettingsProvider(Protocol):
    def get(self, section: str, key: str, default: Any = None) -> Any: ...
    def set(self, section: str, key: str, value: Any) -> None: ...

# Generic types
T = TypeVar('T')
DataDict = Dict[str, Any]
ProgressCallback = Callable[[str, Dict[str, Any]], None]

# Complex type annotations
def process_tasks(
    tasks: List[DownloadTask],
    callback: Optional[ProgressCallback] = None,
    settings: Optional[SettingsProvider] = None
) -> Dict[str, Union[bool, str]]:
    """Process multiple download tasks."""
    pass
```

#### Error Handling

Implement comprehensive error handling:

```python
class DownloadError(Exception):
    """Base class for download-related errors."""
    pass

class NetworkError(DownloadError):
    """Network-related download errors."""
    pass

class DecryptionError(DownloadError):
    """Encryption/decryption errors."""
    pass

def download_segment(url: str, key: Optional[bytes] = None) -> bytes:
    """Download and optionally decrypt a video segment.
    
    Args:
        url: Segment URL
        key: Optional decryption key
        
    Returns:
        Raw segment data
        
    Raises:
        NetworkError: If download fails
        DecryptionError: If decryption fails
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.content
        
        if key:
            try:
                data = decrypt_segment(data, key)
            except Exception as e:
                raise DecryptionError(f"Failed to decrypt segment: {e}") from e
        
        return data
        
    except requests.RequestException as e:
        raise NetworkError(f"Failed to download segment {url}: {e}") from e
```

### Testing Strategy

#### Test Categories

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **UI Tests**: Test user interface behavior
4. **End-to-End Tests**: Test complete workflows

#### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.core.downloader import DownloadManager, DownloadTask, TaskStatus

class TestDownloadManager:
    @pytest.fixture
    def manager(self):
        return DownloadManager()
    
    @pytest.fixture
    def sample_task(self):
        return DownloadTask(
            name="Test Task",
            base_url="https://example.com/stream",
            segments=10,
            output_file="test.mp4"
        )
    
    def test_add_task_success(self, manager, sample_task):
        """Test successful task addition."""
        task_id = manager.add_task(sample_task)
        
        assert task_id is not None
        assert task_id in manager.tasks
        assert manager.tasks[task_id] == sample_task
    
    def test_add_invalid_task(self, manager):
        """Test adding invalid task raises error."""
        invalid_task = DownloadTask(name="Invalid")  # Missing required fields
        
        with pytest.raises(ValueError):
            manager.add_task(invalid_task)
    
    @patch('src.core.downloader.requests.Session')
    def test_download_segment(self, mock_session, manager):
        """Test segment download with mocked network."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"video_data"
        mock_session.return_value.get.return_value = mock_response
        
        # Test
        result = manager._download_segment("https://example.com/seg1.ts")
        
        assert result == b"video_data"
        mock_session.return_value.get.assert_called_once()
```

#### Integration Testing

```python
class TestDownloadIntegration:
    @pytest.fixture
    def app_with_manager(self):
        """Create application with download manager."""
        app = QApplication([])
        settings = MockSettings()
        manager = DownloadManager(settings)
        return app, manager
    
    def test_task_lifecycle(self, app_with_manager):
        """Test complete task lifecycle."""
        app, manager = app_with_manager
        
        # Create task
        task = DownloadTask(
            name="Integration Test",
            base_url="https://httpbin.org/stream",
            segments=5,
            output_file="integration_test.mp4"
        )
        
        # Add and start task
        task_id = manager.add_task(task)
        manager.start_task(task_id)
        
        # Wait for completion (with timeout)
        timeout = time.time() + 30
        while time.time() < timeout:
            if manager.get_task_status(task_id) in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                break
            time.sleep(0.1)
        
        # Verify result
        status = manager.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED
```

#### UI Testing

```python
class TestMainWindow:
    @pytest.fixture
    def main_window(self, qtbot):
        """Create main window for testing."""
        app = Mock()
        manager = Mock()
        settings = Mock()
        
        window = MainWindow(app, manager, settings)
        qtbot.addWidget(window)
        return window
    
    def test_new_task_dialog(self, main_window, qtbot):
        """Test new task dialog creation."""
        # Trigger new task action
        qtbot.mouseClick(main_window.new_task_btn, Qt.LeftButton)
        
        # Verify dialog appears
        assert main_window.task_dialog is not None
        assert main_window.task_dialog.isVisible()
    
    def test_task_list_update(self, main_window, qtbot):
        """Test task list updates when tasks are added."""
        initial_count = main_window.task_manager.task_count()
        
        # Simulate task addition
        task = Mock()
        task.task_id = "test-123"
        task.name = "Test Task"
        
        main_window.task_manager.add_task_widget(task)
        
        assert main_window.task_manager.task_count() == initial_count + 1
```

### Performance Optimization

#### Profiling

Use profiling tools to identify bottlenecks:

```python
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """Decorator to profile function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper

@profile_function
def download_playlist(url: str):
    """Download and parse M3U8 playlist."""
    # Implementation here
    pass
```

#### Memory Management

```python
import gc
import weakref
from typing import WeakSet

class ResourceManager:
    """Manage application resources and prevent memory leaks."""
    
    def __init__(self):
        self._active_downloads: WeakSet[DownloadTask] = WeakSet()
        self._temp_files: List[str] = []
    
    def register_download(self, task: DownloadTask):
        """Register active download for tracking."""
        self._active_downloads.add(task)
    
    def cleanup_completed_tasks(self):
        """Clean up completed tasks and temporary files."""
        # Remove completed tasks
        completed_tasks = [
            task for task in self._active_downloads 
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]
        
        for task in completed_tasks:
            self._cleanup_task(task)
        
        # Force garbage collection
        gc.collect()
    
    def _cleanup_task(self, task: DownloadTask):
        """Clean up individual task resources."""
        if task.temp_dir and os.path.exists(task.temp_dir):
            shutil.rmtree(task.temp_dir, ignore_errors=True)
```

#### Threading Optimization

```python
class OptimizedThreadPool:
    """Custom thread pool with dynamic sizing."""
    
    def __init__(self, min_threads: int = 2, max_threads: int = 10):
        self.min_threads = min_threads
        self.max_threads = max_threads
        self.current_threads = min_threads
        self.task_queue = Queue()
        self.threads: List[threading.Thread] = []
        
        # Start minimum threads
        for _ in range(min_threads):
            self._start_worker_thread()
    
    def submit_task(self, task: Callable):
        """Submit task for execution."""
        self.task_queue.put(task)
        
        # Scale up if needed
        if (self.task_queue.qsize() > self.current_threads and 
            self.current_threads < self.max_threads):
            self._start_worker_thread()
    
    def _start_worker_thread(self):
        """Start new worker thread."""
        worker = threading.Thread(target=self._worker_loop)
        worker.daemon = True
        worker.start()
        self.threads.append(worker)
        self.current_threads += 1
```

## Debugging and Diagnostics

### Logging Strategy

VidTanium uses structured logging with loguru:

```python
from loguru import logger

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    "logs/vidtanium_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)

# Development logging
if DEBUG_MODE:
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}"
    )

# Usage in code
class DownloadManager:
    def __init__(self):
        self.logger = logger.bind(component="DownloadManager")
    
    def add_task(self, task: DownloadTask) -> str:
        self.logger.info("Adding new task: {task_name}", task_name=task.name)
        
        try:
            task_id = self._generate_task_id()
            self.tasks[task_id] = task
            
            self.logger.debug(
                "Task added successfully: {task_id} with {segment_count} segments",
                task_id=task_id,
                segment_count=task.segments
            )
            
            return task_id
            
        except Exception as e:
            self.logger.error(
                "Failed to add task {task_name}: {error}",
                task_name=task.name,
                error=str(e)
            )
            raise
```

### Debug Tools

#### Debug Console

```python
class DebugConsole(QWidget):
    """In-application debug console for development."""
    
    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Command input
        self.command_input = QLineEdit()
        self.command_input.returnPressed.connect(self.execute_command)
        layout.addWidget(self.command_input)
        
        # Output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)
    
    def execute_command(self):
        """Execute debug command."""
        command = self.command_input.text()
        self.command_input.clear()
        
        try:
            # Create safe execution context
            context = {
                'app': self.app_context,
                'manager': self.app_context.download_manager,
                'tasks': self.app_context.download_manager.tasks,
                'logger': logger,
            }
            
            result = eval(command, {"__builtins__": {}}, context)
            self.output_area.append(f">>> {command}")
            self.output_area.append(f"{result}")
            
        except Exception as e:
            self.output_area.append(f">>> {command}")
            self.output_area.append(f"Error: {e}")
```

#### Performance Monitor

```python
class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
    
    def track_operation(self, operation_name: str):
        """Context manager for tracking operation duration."""
        return OperationTimer(self, operation_name)
    
    def record_metric(self, name: str, value: float):
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'value': value,
            'timestamp': time.time()
        })
    
    def get_average(self, metric_name: str, window_size: int = 100) -> float:
        """Get average value for metric over window."""
        if metric_name not in self.metrics:
            return 0.0
        
        recent_values = self.metrics[metric_name][-window_size:]
        return sum(m['value'] for m in recent_values) / len(recent_values)

class OperationTimer:
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        self.monitor.record_metric(self.operation_name, duration)

# Usage
monitor = PerformanceMonitor()

with monitor.track_operation("segment_download"):
    download_segment(url)

avg_download_time = monitor.get_average("segment_download")
```

## Documentation Standards

### Code Documentation

Use Google-style docstrings:

```python
def analyze_m3u8_playlist(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Analyze M3U8 playlist and extract stream information.
    
    This function downloads and parses an M3U8 playlist file, extracting
    information about available streams, segments, and encryption details.
    
    Args:
        url: The URL of the M3U8 playlist to analyze
        headers: Optional HTTP headers to include in the request
    
    Returns:
        A dictionary containing the analysis results with the following structure:
        {
            'success': bool,           # Whether analysis was successful
            'streams': List[dict],     # List of available streams
            'encryption': str,         # Encryption type ('none', 'aes-128', etc.)
            'duration': float,         # Total duration in seconds
            'segments': int            # Number of segments
        }
    
    Raises:
        NetworkError: If the playlist cannot be downloaded
        ParseError: If the playlist format is invalid
    
    Example:
        >>> result = analyze_m3u8_playlist('https://example.com/playlist.m3u8')
        >>> if result['success']:
        ...     print(f"Found {result['segments']} segments")
    """
    pass
```

### API Documentation

Generate API documentation using Sphinx:

```python
# conf.py for Sphinx
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',  # Google-style docstrings
    'sphinx.ext.intersphinx',
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
```

## Release Process

### Version Management

Use semantic versioning (SemVer):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update Version Numbers**:

   ```python
   # src/app/application.py
   __version__ = "1.2.3"
   
   # pyproject.toml
   version = "1.2.3"
   ```

2. **Update Changelog**:

   ```markdown
   # Changelog
   
   ## [1.2.3] - 2024-01-15
   
   ### Added
   - New batch download feature
   - Support for DASH streams
   
   ### Fixed
   - Memory leak in download manager
   - UI responsiveness issues
   
   ### Changed
   - Improved error handling
   ```

3. **Run Full Test Suite**:

   ```bash
   pytest tests/ --cov=src --cov-report=html
   mypy src/
   flake8 src/
   ```

4. **Build Distribution**:

   ```bash
   python -m build
   ```

5. **Create Release Tag**:

   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

### Continuous Integration

GitHub Actions workflow:

```yaml
name: CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
  
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.11
    
    - name: Build distribution
      run: |
        python -m pip install build
        python -m build
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: distributions
        path: dist/
```

This developer guide provides comprehensive information for contributing to VidTanium development. For user-facing documentation, see the main documentation and user manual.

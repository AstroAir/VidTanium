# VidTanium API Reference

## Core API Documentation

This document provides comprehensive API reference for VidTanium's core components, including advanced error handling, monitoring, analytics, and user interface systems.

## Table of Contents

1. [Download Manager API](#download-manager-api)
2. [Enhanced Error Handling API](#enhanced-error-handling-api)
3. [Monitoring & Analytics API](#monitoring--analytics-api)
4. [Task Management API](#task-management-api)
5. [Queue Management API](#queue-management-api)
6. [User Interface API](#user-interface-api)
7. [Configuration API](#configuration-api)

## Download Manager API

### DownloadManager Class

The `DownloadManager` is the central orchestrator for all download operations.

```python
from src.core.downloader import DownloadManager, DownloadTask, TaskPriority

# Initialize manager
manager = DownloadManager(settings=app_settings)

# Start the manager
manager.start()

# Create and add task
task = DownloadTask(
    name="Sample Video",
    base_url="https://example.com/stream",
    key_url="https://example.com/key.bin",
    segments=100,
    output_file="/path/to/output.mp4",
    priority=TaskPriority.HIGH
)

task_id = manager.add_task(task)

# Control task execution
manager.start_task(task_id)
manager.pause_task(task_id)
manager.cancel_task(task_id)

# Get task information
status = manager.get_task_status(task_id)
tasks = manager.get_all_tasks()
```

#### Methods

##### `__init__(settings: Optional[SettingsProvider] = None)`

Initialize the download manager with optional settings provider.

**Parameters:**

- `settings`: Settings provider for configuration

##### `start() -> None`

Start the download manager's background threads.

##### `stop() -> None`

Stop the download manager and cleanup resources.

##### `add_task(task: DownloadTask) -> str`

Add a new download task to the queue.

**Parameters:**

- `task`: DownloadTask instance to add

**Returns:**

- `str`: Unique task identifier

##### `start_task(task_id: str) -> bool`

Start execution of a specific task.

**Parameters:**

- `task_id`: Unique task identifier

**Returns:**

- `bool`: True if task was started successfully

##### `pause_task(task_id: str) -> bool`

Pause execution of a running task.

**Parameters:**

- `task_id`: Unique task identifier

**Returns:**

- `bool`: True if task was paused successfully

##### `cancel_task(task_id: str) -> bool`

Cancel a task and cleanup its resources.

**Parameters:**

- `task_id`: Unique task identifier

**Returns:**

- `bool`: True if task was cancelled successfully

##### `get_task_status(task_id: str) -> Optional[TaskStatus]`

Get the current status of a task.

**Parameters:**

- `task_id`: Unique task identifier

**Returns:**

- `Optional[TaskStatus]`: Current task status or None if not found

##### `get_all_tasks() -> Dict[str, DownloadTask]`

Get all tasks managed by this download manager.

**Returns:**

- `Dict[str, DownloadTask]`: Dictionary mapping task IDs to tasks

#### Events

The DownloadManager provides callback hooks for monitoring:

```python
def on_progress(task_id: str, progress: ProgressDict):
    print(f"Task {task_id}: {progress['completed']}/{progress['total']} segments")

def on_status_change(task_id: str, old_status: TaskStatus, new_status: TaskStatus):
    print(f"Task {task_id} changed from {old_status} to {new_status}")

def on_completed(task_id: str, success: bool, message: str):
    if success:
        print(f"Task {task_id} completed: {message}")
    else:
        print(f"Task {task_id} failed: {message}")

manager.on_task_progress = on_progress
manager.on_task_status_changed = on_status_change
manager.on_task_completed = on_completed
```

### DownloadTask Class

Represents an individual download task.

```python
from src.core.downloader import DownloadTask, TaskPriority

task = DownloadTask(
    task_id="unique-id",  # Optional, auto-generated if not provided
    name="Video Title",
    base_url="https://example.com/stream",
    key_url="https://example.com/key.bin",  # Optional for unencrypted streams
    segments=150,
    output_file="/path/to/output.mp4",
    priority=TaskPriority.NORMAL
)

# Check progress
percentage = task.get_progress_percentage()
print(f"Progress: {percentage}%")

# Save/load progress
task.save_progress()
task.load_progress()
```

#### Properties

- `task_id: str` - Unique task identifier
- `name: str` - Human-readable task name
- `base_url: Optional[str]` - Base URL for segment downloads
- `key_url: Optional[str]` - URL for encryption key
- `segments: Optional[int]` - Number of segments to download
- `output_file: Optional[str]` - Output file path
- `status: TaskStatus` - Current task status
- `priority: TaskPriority` - Task priority level
- `progress: ProgressDict` - Progress information

#### Methods

##### `get_progress_percentage() -> float`

Calculate completion percentage.

**Returns:**

- `float`: Percentage complete (0.0 to 100.0)

##### `save_progress() -> None`

Save current progress to disk for resumption.

##### `load_progress() -> None`

Load previously saved progress from disk.

### TaskStatus Enumeration

```python
from src.core.downloader import TaskStatus

# Available status values
TaskStatus.PENDING     # Task created but not started
TaskStatus.RUNNING     # Task currently executing
TaskStatus.PAUSED      # Task paused by user
TaskStatus.COMPLETED   # Task finished successfully
TaskStatus.FAILED      # Task failed with error
TaskStatus.CANCELED    # Task cancelled by user
```

### ProgressDict Type

Progress information structure:

```python
from src.core.downloader import ProgressDict

progress: ProgressDict = {
    "total": 150,                    # Total segments
    "completed": 75,                 # Completed segments
    "failed": 2,                     # Failed segments
    "current_file": "segment_75.ts", # Current file being downloaded
    "current_file_progress": 0.65,   # Progress of current file (0.0-1.0)
    "start_time": 1640995200.0,      # Start timestamp
    "end_time": None,                # End timestamp (None if not finished)
    "speed": 2048000.0,              # Current speed in bytes/second
    "estimated_time": 300.0,         # Estimated time remaining in seconds
    "downloaded_bytes": 157286400    # Total bytes downloaded
}
```

## Media Analyzer API

### MediaAnalyzer Class

Provides intelligent analysis of media URLs and content.

```python
from src.core.analyzer import MediaAnalyzer

analyzer = MediaAnalyzer(settings={
    "user_agent": "Custom User Agent",
    "timeout": 30,
    "verify_ssl": True,
    "proxy": "http://proxy:8080"
})

# Analyze any URL
result = analyzer.analyze_url("https://example.com/video.m3u8")
if result["success"]:
    print(f"Found {result['segments']} segments")
    print(f"Duration: {result['duration']} seconds")
    print(f"Encryption: {result['encryption']}")

# Extract media URLs from web page
media_urls = analyzer.extract_media_from_page("https://example.com/video-page")
for url in media_urls:
    print(f"Found media URL: {url}")
```

#### Methods

##### `__init__(settings: Optional[Dict[str, Any]] = None)`

Initialize analyzer with optional settings.

**Parameters:**

- `settings`: Configuration dictionary

##### `analyze_url(url: str) -> Dict[str, Any]`

Analyze any URL and return media information.

**Parameters:**

- `url`: URL to analyze (can be direct M3U8 or web page)

**Returns:**

- `Dict[str, Any]`: Analysis results with success status

##### `analyze_m3u8(url: str) -> Dict[str, Any]`

Analyze M3U8 playlist specifically.

**Parameters:**

- `url`: Direct M3U8 URL

**Returns:**

- `Dict[str, Any]`: M3U8 analysis results

##### `extract_media_from_page(url: str) -> List[str]`

Extract media URLs from a web page.

**Parameters:**

- `url`: Web page URL to analyze

**Returns:**

- `List[str]`: List of discovered media URLs

#### Response Format

Successful analysis returns:

```python
{
    "success": True,
    "type": "media",  # "master" or "media"
    "segments": 150,
    "duration": 3600.0,
    "encryption": "aes-128",  # "none", "aes-128", "sample-aes", "custom"
    "key_url": "https://example.com/key.bin",
    "iv": "0x12345678901234567890123456789012",
    "base_url": "https://example.com/stream",
    "variants": [  # For master playlists
        {
            "resolution": "1920x1080",
            "bandwidth": 5000000,
            "url": "https://example.com/stream/high.m3u8",
            "codec": "avc1.4d0028"
        }
    ]
}
```

## Media Processor API

### MediaProcessor Class

Handles video/audio processing operations using FFmpeg.

```python
from src.core.media_processor import MediaProcessor

processor = MediaProcessor(ffmpeg_path="/usr/local/bin/ffmpeg")

# Convert video format
result = processor.convert_format(
    input_file="input.ts",
    output_file="output.mp4",
    format_options={
        "codec": "libx264",
        "bitrate": "2M",
        "resolution": "1920x1080",
        "fps": 30
    }
)

# Clip video segment
result = processor.clip_video(
    input_file="input.mp4",
    output_file="clip.mp4",
    start_time="00:01:30",
    duration="00:02:00"
)

# Extract audio
result = processor.extract_audio(
    input_file="input.mp4",
    output_file="audio.mp3",
    audio_format="mp3",
    audio_bitrate="192k"
)

# Compress video
result = processor.compress_video(
    input_file="input.mp4",
    output_file="compressed.mp4",
    quality=23  # CRF value (lower = higher quality)
)
```

#### Methods

##### `convert_format(input_file: str, output_file: str, format_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

Convert video/audio format.

**Parameters:**

- `input_file`: Input file path
- `output_file`: Output file path
- `format_options`: Conversion options

**Returns:**

- `Dict[str, Any]`: Operation result with success status

##### `clip_video(input_file: str, output_file: str, start_time: Optional[str] = None, duration: Optional[str] = None) -> Dict[str, Any]`

Extract video segment.

**Parameters:**

- `input_file`: Input video file
- `output_file`: Output file path
- `start_time`: Start time (HH:MM:SS format)
- `duration`: Duration (HH:MM:SS format)

**Returns:**

- `Dict[str, Any]`: Operation result

##### `extract_audio(input_file: str, output_file: str, audio_format: str = "mp3", audio_bitrate: Optional[str] = None) -> Dict[str, Any]`

Extract audio track from video.

**Parameters:**

- `input_file`: Input video file
- `output_file`: Output audio file
- `audio_format`: Output audio format
- `audio_bitrate`: Audio bitrate (e.g., "192k")

**Returns:**

- `Dict[str, Any]`: Operation result

##### `compress_video(input_file: str, output_file: str, target_size_mb: Optional[int] = None, quality: Optional[int] = None) -> Dict[str, Any]`

Compress video file.

**Parameters:**

- `input_file`: Input video file
- `output_file`: Output file path
- `target_size_mb`: Target file size in MB
- `quality`: CRF quality value (0-51, lower = better)

**Returns:**

- `Dict[str, Any]`: Operation result

## M3U8 Parser API

### M3U8Parser Class

Specialized parser for HLS manifests.

```python
from src.core.m3u8_parser import M3U8Parser

parser = M3U8Parser()
streams = parser.parse_url("https://example.com/playlist.m3u8")

for stream in streams:
    print(f"Resolution: {stream.resolution}")
    print(f"Bandwidth: {stream.bandwidth}")
    print(f"Segments: {len(stream.segments)}")
    print(f"Duration: {stream.duration}")

# Get best quality stream
best_stream = parser.get_best_quality_stream()
if best_stream:
    print(f"Best quality: {best_stream.resolution}")
```

#### Methods

##### `parse_url(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> List[M3U8Stream]`

Parse M3U8 playlist from URL.

**Parameters:**

- `url`: M3U8 playlist URL
- `headers`: Optional HTTP headers
- `timeout`: Request timeout in seconds

**Returns:**

- `List[M3U8Stream]`: List of parsed streams

##### `get_best_quality_stream() -> Optional[M3U8Stream]`

Get the highest quality stream from last parse operation.

**Returns:**

- `Optional[M3U8Stream]`: Best quality stream or None

### M3U8Stream Class

Represents a single stream from M3U8 playlist.

#### Properties

- `url: str` - Stream URL
- `resolution: str` - Video resolution (e.g., "1920x1080")
- `bandwidth: int` - Stream bandwidth in bits per second
- `duration: float` - Total duration in seconds
- `segments: List[M3U8Segment]` - List of segments
- `encryption: EncryptionMethod` - Encryption type
- `key_url: Optional[str]` - Encryption key URL
- `key_iv: Optional[str]` - Initialization vector

## URL Extractor API

### URLExtractor Class

Utility class for URL extraction and processing.

```python
from src.core.url_extractor import URLExtractor

# Extract URLs from text
text = "Visit https://example.com and http://test.com for more info"
urls = URLExtractor.extract_urls_from_text(text)

# Extract media URLs from webpage
media_urls = URLExtractor.extract_media_urls_from_webpage(
    "https://example.com/video-page",
    headers={"User-Agent": "Custom Agent"},
    media_extensions=['.mp4', '.m3u8', '.ts']
)

# Filter URLs
filtered = URLExtractor.filter_urls(
    urls,
    include_pattern=r".*\.m3u8.*",
    exclude_pattern=r".*ads.*"
)

# Validate URL
is_valid = URLExtractor.validate_url("https://example.com")
```

#### Static Methods

##### `extract_urls_from_text(text: str, pattern: Optional[str] = None) -> List[str]`

Extract URLs from text using regex patterns.

##### `extract_media_urls_from_webpage(url: str, headers: Optional[Dict[str, str]] = None, media_extensions: Optional[List[str]] = None) -> List[str]`

Extract media URLs from webpage HTML.

##### `filter_urls(urls: List[str], include_pattern: Optional[str] = None, exclude_pattern: Optional[str] = None) -> List[str]`

Filter URL list using regex patterns.

##### `normalize_url(url: str) -> str`

Normalize URL format (add protocol, etc.).

##### `validate_url(url: str) -> bool`

Validate URL format and accessibility.

## Error Handling

All API methods follow consistent error handling patterns:

### Success Response

```python
{
    "success": True,
    "data": {...},      # Method-specific data
    "message": "Operation completed successfully"
}
```

### Error Response

```python
{
    "success": False,
    "error": "Error description",
    "error_code": "ERROR_CODE",  # Optional
    "details": {...}             # Optional additional details
}
```

### Exception Handling

```python
try:
    result = analyzer.analyze_url(url)
    if result["success"]:
        # Handle success
        process_result(result)
    else:
        # Handle failure
        print(f"Error: {result['error']}")
except Exception as e:
    # Handle unexpected exceptions
    print(f"Unexpected error: {e}")
```

## Thread Safety

### Thread-Safe Components

- `DownloadManager`: Thread-safe for all public methods
- `TaskScheduler`: Internal synchronization for queue operations
- `ThreadPoolManager`: Qt-based thread pool with signal safety

### Thread-Unsafe Components

- `MediaAnalyzer`: Create separate instances per thread
- `MediaProcessor`: Not thread-safe for concurrent operations on same instance
- `URLExtractor`: Static methods are thread-safe

### Best Practices

```python
# Good: Separate instances per thread
def worker_thread():
    analyzer = MediaAnalyzer()
    result = analyzer.analyze_url(url)

# Good: Use download manager's thread safety
manager.add_task(task)  # Safe from any thread

# Bad: Sharing instances across threads
# Don't do this without external synchronization
global_analyzer = MediaAnalyzer()
```

## Performance Considerations

### Download Optimization

- Adjust `max_concurrent_tasks` based on network capacity
- Use appropriate `chunk_size` for download chunks
- Enable `auto_cleanup` to manage disk space
- Monitor memory usage with large segment counts

### UI Responsiveness

- Use thread pool for long-running operations
- Implement progress callbacks for user feedback
- Batch UI updates to avoid excessive redraws
- Use QTimer for periodic updates instead of tight loops

### Memory Management

- Enable automatic cleanup of completed tasks
- Limit log retention with cleanup timers
- Use streaming for large file operations
- Monitor resource usage in production

## Configuration Integration

All core components integrate with the application's settings system:

```python
# Settings are automatically passed to core components
manager = DownloadManager(settings=app.settings)

# Common settings sections:
# - "download": Download-related settings
# - "network": Network and proxy settings
# - "advanced": Advanced configuration
# - "ui": User interface preferences

## Enhanced Error Handling API

### EnhancedErrorHandler Class

The `EnhancedErrorHandler` provides intelligent error categorization, handling, and user-friendly error reporting.

```python
from src.core.error_handler import EnhancedErrorHandler, error_handler
from src.core.exceptions import VidTaniumException, ErrorCategory, ErrorSeverity

# Initialize error handler
handler = EnhancedErrorHandler()

# Handle exceptions with context
try:
    # Some operation that might fail
    pass
except Exception as e:
    enhanced_exception = handler.handle_exception(
        e,
        context=ErrorContext(url="https://example.com", task_id="task_123"),
        operation_name="download_segment"
    )
    print(f"Error: {enhanced_exception.message}")
    print(f"Category: {enhanced_exception.category}")
    print(f"Suggested actions: {enhanced_exception.suggested_actions}")
```

#### Methods

##### `handle_exception(exception: Exception, context: Optional[ErrorContext] = None, operation_name: str = "operation") -> VidTaniumException`

Convert generic exception to VidTaniumException with enhanced information.

**Parameters:**
- `exception`: The original exception to handle
- `context`: Optional error context with additional information
- `operation_name`: Name of the operation that failed

**Returns:**
- `VidTaniumException`: Enhanced exception with categorization and suggested actions

### VidTaniumException Hierarchy

#### Base Exception Classes

```python
from src.core.exceptions import (
    VidTaniumException, ErrorCategory, ErrorSeverity, ErrorContext,
    NetworkException, ConnectionTimeoutException, HTTPException,
    FilesystemException, EncryptionException, ValidationException,
    ResourceException, SystemException, PermissionException
)

# Network-related exceptions
try:
    # Network operation
    pass
except ConnectionTimeoutException as e:
    print(f"Connection timeout: {e.url} after {e.timeout_seconds}s")
except HTTPException as e:
    print(f"HTTP error {e.status_code}: {e.message}")

# Filesystem exceptions
except PermissionException as e:
    print(f"Permission denied: {e.path}")
    print(f"Required permissions: {e.required_permissions}")

# Resource exceptions
except MemoryException as e:
    print(f"Memory error: {e.message}")
    print(f"Required memory: {e.required_memory_mb}MB")
```

### IntelligentRetryManager Class

The `IntelligentRetryManager` provides context-aware retry strategies with circuit breaker protection.

```python
from src.core.retry_manager import IntelligentRetryManager, retry_manager

# Use global retry manager instance
result = retry_manager.execute_with_retry(
    operation=lambda: download_segment(url),
    operation_id="download_segment_123",
    context=ErrorContext(url=url, task_id="task_123"),
    max_retries=5
)

# Async version
result = await retry_manager.execute_with_retry_async(
    operation=lambda: async_download_segment(url),
    operation_id="async_download_123",
    context=ErrorContext(url=url),
    max_retries=3
)
```

#### Methods

##### `execute_with_retry(operation: Callable, operation_id: str, context: Optional[ErrorContext] = None, max_retries: Optional[int] = None) -> Any`

Execute operation with intelligent retry logic.

**Parameters:**
- `operation`: Function to execute with retry logic
- `operation_id`: Unique identifier for the operation
- `context`: Optional error context for better retry decisions
- `max_retries`: Maximum number of retry attempts (overrides default)

**Returns:**
- `Any`: Result of the successful operation

**Raises:**
- `VidTaniumException`: If operation fails after all retry attempts

## Monitoring & Analytics API

### BandwidthMonitor Class

The `BandwidthMonitor` provides real-time network performance tracking and optimization recommendations.

```python
from src.core.bandwidth_monitor import BandwidthMonitor, bandwidth_monitor

# Use global bandwidth monitor instance
bandwidth_monitor.start()

# Get current bandwidth statistics
stats = bandwidth_monitor.get_current_stats()
print(f"Download speed: {stats.download_speed:.2f} MB/s")
print(f"Upload speed: {stats.upload_speed:.2f} MB/s")
print(f"Active connections: {stats.active_connections}")

# Get historical data
history = bandwidth_monitor.get_bandwidth_history(duration_minutes=30)
for sample in history:
    print(f"Time: {sample.timestamp}, Speed: {sample.download_speed:.2f} MB/s")

# Register callback for real-time updates
def on_bandwidth_update(sample):
    print(f"Current speed: {sample.download_speed:.2f} MB/s")

bandwidth_monitor.register_callback(on_bandwidth_update)
```

### ETACalculator Class

The `ETACalculator` provides accurate time estimation using multiple algorithms.

```python
from src.core.eta_calculator import ETACalculator, ETAAlgorithm, ETAResult

# Initialize ETA calculator
eta_calc = ETACalculator()

# Calculate ETA using different algorithms
linear_eta = eta_calc.calculate_eta(
    completed_bytes=1024*1024*50,  # 50MB completed
    total_bytes=1024*1024*200,     # 200MB total
    algorithm=ETAAlgorithm.LINEAR
)

adaptive_eta = eta_calc.calculate_eta(
    completed_bytes=1024*1024*50,
    total_bytes=1024*1024*200,
    algorithm=ETAAlgorithm.ADAPTIVE
)

print(f"Linear ETA: {linear_eta.estimated_seconds}s")
print(f"Adaptive ETA: {adaptive_eta.estimated_seconds}s")
print(f"Confidence: {adaptive_eta.confidence:.2f}")
```

### TaskStateManager Class

The `TaskStateManager` provides persistent task state tracking and recovery.

```python
from src.core.task_state_manager import TaskStateManager, task_state_manager

# Save task state
task_state_manager.save_task_state(task_id, {
    'progress': 0.75,
    'downloaded_segments': 150,
    'total_segments': 200,
    'current_speed': 5.2,
    'eta_seconds': 120
})

# Load task state for recovery
state = task_state_manager.load_task_state(task_id)
if state:
    print(f"Resuming task at {state['progress']*100:.1f}% completion")

# Get all task states
all_states = task_state_manager.get_all_task_states()
```

### DownloadHistoryManager Class

The `DownloadHistoryManager` provides comprehensive download tracking and analytics.

```python
from src.core.download_history_manager import DownloadHistoryManager, download_history_manager

# Record completed download
download_history_manager.record_download({
    'task_id': 'task_123',
    'name': 'Sample Video',
    'url': 'https://example.com/video.m3u8',
    'file_size': 1024*1024*200,  # 200MB
    'duration_seconds': 300,
    'average_speed': 0.67,  # MB/s
    'completion_time': time.time(),
    'success': True
})

# Get download history
history = download_history_manager.get_download_history(limit=50)
for download in history:
    print(f"{download['name']}: {download['file_size']} bytes in {download['duration_seconds']}s")

# Get analytics
analytics = download_history_manager.get_analytics()
print(f"Total downloads: {analytics['total_downloads']}")
print(f"Success rate: {analytics['success_rate']:.2f}%")
print(f"Average speed: {analytics['average_speed']:.2f} MB/s")
```

# Access settings in custom code
max_concurrent = app.settings.get("download", "max_concurrent_tasks", 3)
proxy_url = app.settings.get("network", "proxy_url", "")
debug_mode = app.settings.get("advanced", "debug_mode", False)
```

---

This API reference provides comprehensive coverage of VidTanium's core functionality. For UI components and advanced usage, see the main documentation.

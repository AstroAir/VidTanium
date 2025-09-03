---
title: Practical Examples
description: Real-world examples and use cases for VidTanium
---

# Practical Examples

!!! abstract "Overview"
    Real-world examples and use cases for VidTanium

## Table of Contents

1. [Basic Examples](#basic-examples)
2. [Advanced Workflows](#advanced-workflows)
3. [Integration Examples](#integration-examples)
4. [Performance Optimization](#performance-optimization)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Automation Scripts](#automation-scripts)

---

## Basic Examples

### Example 1: Simple M3U8 Download

**Scenario:** Download a single M3U8 video stream

```python
#!/usr/bin/env python3
"""Simple M3U8 download example"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings
import time

def simple_download():
    # Initialize components
    settings = Settings()
    downloader = DownloadManager(settings)
    downloader.start()
    
    # Create download task
    task = DownloadTask(
        name="My Video",
        base_url="https://example.com/playlist.m3u8",
        output_file="./downloads/my_video.mp4",
        priority=TaskPriority.NORMAL
    )
    
    # Add task and get ID
    task_id = downloader.add_task(task)
    print(f"🚀 Started download: {task.name} (ID: {task_id})")
    
    # Monitor progress
    while True:
        status = downloader.get_task_status(task_id)
        print(f"📊 Progress: {status.progress:.1f}% | Speed: {status.speed:.2f} MB/s")
        
        if status.state == "completed":
            print("�?Download completed successfully!")
            break
        elif status.state == "failed":
            print(f"�?Download failed: {status.error}")
            break
        elif status.state == "cancelled":
            print("⏹️ Download cancelled")
            break
            
        time.sleep(2)

if __name__ == "__main__":
    simple_download()
```

### Example 2: Encrypted Stream Download

**Scenario:** Download an AES-128 encrypted M3U8 stream

```python
#!/usr/bin/env python3
"""Encrypted stream download example"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings

def encrypted_download():
    settings = Settings()
    downloader = DownloadManager(settings)
    downloader.start()
    
    # Create task for encrypted stream
    task = DownloadTask(
        name="Encrypted Video",
        base_url="https://example.com/encrypted/playlist.m3u8",
        key_url="https://example.com/keys/video.key",  # Encryption key URL
        output_file="./downloads/encrypted_video.mp4",
        priority=TaskPriority.HIGH,
        headers={
            "User-Agent": "VidTanium/1.0",
            "Referer": "https://example.com"
        }
    )
    
    task_id = downloader.add_task(task)
    print(f"🔐 Started encrypted download: {task_id}")
    
    # The downloader will automatically handle:
    # - Key retrieval from key_url
    # - AES-128 decryption of segments
    # - Integrity verification

if __name__ == "__main__":
    encrypted_download()
```

### Example 3: Batch URL Processing

**Scenario:** Download multiple videos from a list of URLs

```python
#!/usr/bin/env python3
"""Batch download example"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.core.batch_progress_aggregator import batch_progress_aggregator
from src.app.settings import Settings
import time

def batch_download():
    settings = Settings()
    downloader = DownloadManager(settings)
    downloader.start()
    
    # List of URLs to download
    urls = [
        "https://example.com/video1.m3u8",
        "https://example.com/video2.m3u8", 
        "https://example.com/video3.m3u8",
        "https://example.com/video4.m3u8"
    ]
    
    task_ids = []
    
    # Create tasks for all URLs
    for i, url in enumerate(urls, 1):
        task = DownloadTask(
            name=f"Video {i}",
            base_url=url,
            output_file=f"./downloads/batch_video_{i}.mp4",
            priority=TaskPriority.NORMAL
        )
        
        task_id = downloader.add_task(task)
        task_ids.append(task_id)
        print(f"📝 Added task {i}: {task_id}")
    
    print(f"\n🚀 Starting batch download of {len(task_ids)} videos...")
    
    # Monitor batch progress
    while True:
        batch_progress = batch_progress_aggregator.get_batch_progress()
        
        print(f"📊 Overall Progress: {batch_progress.overall_percentage:.1f}%")
        print(f"⏱️ ETA: {batch_progress.estimated_time_remaining}")
        print(f"🔄 Active: {batch_progress.active_tasks} | Completed: {batch_progress.completed_tasks}")
        
        if batch_progress.completed_tasks == len(task_ids):
            print("�?All downloads completed!")
            break
            
        time.sleep(5)

if __name__ == "__main__":
    batch_download()
```

---

## Advanced Workflows

### Example 4: Custom Headers and Authentication

**Scenario:** Download from a site requiring authentication headers

```python
#!/usr/bin/env python3
"""Download with custom headers and authentication"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings

def authenticated_download():
    settings = Settings()
    downloader = DownloadManager(settings)
    downloader.start()
    
    # Custom headers for authentication
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://streaming-site.com/",
        "Authorization": "Bearer your-auth-token-here",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/vnd.apple.mpegurl, application/x-mpegURL, application/octet-stream",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    task = DownloadTask(
        name="Authenticated Stream",
        base_url="https://protected-site.com/stream/playlist.m3u8",
        output_file="./downloads/authenticated_video.mp4",
        priority=TaskPriority.HIGH,
        headers=custom_headers,
        max_retries=5,
        retry_delay=3.0
    )
    
    task_id = downloader.add_task(task)
    print(f"🔐 Started authenticated download: {task_id}")

if __name__ == "__main__":
    authenticated_download()
```

### Example 5: Bandwidth-Limited Download

**Scenario:** Download with bandwidth limiting to avoid network congestion

```python
#!/usr/bin/env python3
"""Bandwidth-limited download example"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings

def bandwidth_limited_download():
    # Configure settings with bandwidth limits
    settings = Settings()
    settings.set("network", "bandwidth_limit", 5.0)  # 5 MB/s limit
    settings.set("network", "max_concurrent_segments", 3)  # Reduce concurrency
    
    downloader = DownloadManager(settings)
    downloader.start()
    
    task = DownloadTask(
        name="Bandwidth Limited Video",
        base_url="https://example.com/large-video.m3u8",
        output_file="./downloads/limited_speed_video.mp4",
        priority=TaskPriority.LOW  # Lower priority for background downloads
    )
    
    task_id = downloader.add_task(task)
    print(f"🐌 Started bandwidth-limited download: {task_id}")
    print("📊 Download will respect 5 MB/s speed limit")

if __name__ == "__main__":
    bandwidth_limited_download()
```

### Example 6: Scheduled Download

**Scenario:** Schedule downloads for off-peak hours

```python
#!/usr/bin/env python3
"""Scheduled download example"""

from src.core.scheduler import TaskScheduler
from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings
from datetime import datetime, timedelta

def scheduled_download():
    settings = Settings()
    downloader = DownloadManager(settings)
    scheduler = TaskScheduler()
    
    downloader.start()
    scheduler.start()
    
    # Create download task
    task = DownloadTask(
        name="Scheduled Video",
        base_url="https://example.com/video.m3u8",
        output_file="./downloads/scheduled_video.mp4",
        priority=TaskPriority.NORMAL
    )
    
    # Schedule for 2 AM tomorrow
    schedule_time = datetime.now().replace(hour=2, minute=0, second=0) + timedelta(days=1)
    
    scheduler.schedule_task(
        task=task,
        scheduled_time=schedule_time,
        task_type="download"
    )
    
    print(f"�?Scheduled download for: {schedule_time}")
    print("💤 Download will start automatically at scheduled time")

if __name__ == "__main__":
    scheduled_download()
```

---

## Integration Examples

### Example 7: GUI Integration

**Scenario:** Integrate download functionality into a custom GUI

```python
#!/usr/bin/env python3
"""GUI integration example"""

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QProgressBar, QLabel
from PySide6.QtCore import QTimer, QThread, Signal
from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings

class DownloadWorker(QThread):
    progress_updated = Signal(float)
    status_updated = Signal(str)
    
    def __init__(self, url, output_path):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.task_id = None
        
    def run(self):
        settings = Settings()
        downloader = DownloadManager(settings)
        downloader.start()
        
        task = DownloadTask(
            name="GUI Download",
            base_url=self.url,
            output_file=self.output_path,
            priority=TaskPriority.NORMAL
        )
        
        self.task_id = downloader.add_task(task)
        
        # Monitor progress
        while True:
            status = downloader.get_task_status(self.task_id)
            self.progress_updated.emit(status.progress)
            self.status_updated.emit(status.state)
            
            if status.state in ["completed", "failed", "cancelled"]:
                break
                
            self.msleep(1000)  # Update every second

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VidTanium GUI Example")
        self.setGeometry(100, 100, 600, 200)
        
        # Create UI elements
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter M3U8 URL...")
        
        self.download_button = QPushButton("Start Download")
        self.download_button.clicked.connect(self.start_download)
        
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready")
        
        layout.addWidget(self.url_input)
        layout.addWidget(self.download_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        
    def start_download(self):
        url = self.url_input.text()
        if not url:
            return
            
        self.download_button.setEnabled(False)
        self.worker = DownloadWorker(url, "./downloads/gui_download.mp4")
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.status_updated.connect(self.update_status)
        self.worker.start()
        
    def update_progress(self, progress):
        self.progress_bar.setValue(int(progress))
        
    def update_status(self, status):
        self.status_label.setText(f"Status: {status}")
        if status in ["completed", "failed", "cancelled"]:
            self.download_button.setEnabled(True)

def gui_integration_example():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    gui_integration_example()
```

### Example 8: Web API Integration

**Scenario:** Create a REST API for download management

```python
#!/usr/bin/env python3
"""Web API integration example using Flask"""

from flask import Flask, request, jsonify
from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings
import threading
import uuid

app = Flask(__name__)

# Global download manager
settings = Settings()
downloader = DownloadManager(settings)
downloader.start()

@app.route('/api/download', methods=['POST'])
def create_download():
    """Create a new download task"""
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    task = DownloadTask(
        name=data.get('name', 'API Download'),
        base_url=data['url'],
        output_file=data.get('output_file', f'./downloads/{uuid.uuid4()}.mp4'),
        priority=TaskPriority[data.get('priority', 'NORMAL')]
    )
    
    task_id = downloader.add_task(task)
    
    return jsonify({
        'task_id': task_id,
        'status': 'created',
        'message': 'Download task created successfully'
    })

@app.route('/api/download/<task_id>', methods=['GET'])
def get_download_status(task_id):
    """Get download task status"""
    try:
        status = downloader.get_task_status(task_id)
        return jsonify({
            'task_id': task_id,
            'state': status.state,
            'progress': status.progress,
            'speed': status.speed,
            'eta': status.eta
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/download/<task_id>', methods=['DELETE'])
def cancel_download(task_id):
    """Cancel a download task"""
    try:
        success = downloader.cancel_task(task_id)
        if success:
            return jsonify({'message': 'Task cancelled successfully'})
        else:
            return jsonify({'error': 'Failed to cancel task'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## Performance Optimization

### Example 9: High-Performance Configuration

**Scenario:** Optimize settings for maximum download performance

```python
#!/usr/bin/env python3
"""High-performance download configuration"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings

def high_performance_download():
    # Create optimized settings
    settings = Settings()
    
    # Network optimization
    settings.set("network", "max_concurrent_downloads", 6)
    settings.set("network", "max_concurrent_segments", 12)
    settings.set("network", "timeout", 45)
    settings.set("network", "chunk_size", 2097152)  # 2MB chunks
    
    # Memory optimization
    settings.set("advanced", "memory_optimization", True)
    settings.set("advanced", "buffer_size", 8388608)  # 8MB buffer
    
    # Retry optimization
    settings.set("retry", "max_retries", 3)
    settings.set("retry", "retry_delay", 1.0)
    settings.set("retry", "exponential_backoff", True)
    
    downloader = DownloadManager(settings)
    downloader.start()
    
    # Create high-priority task
    task = DownloadTask(
        name="High Performance Download",
        base_url="https://example.com/large-video.m3u8",
        output_file="./downloads/high_perf_video.mp4",
        priority=TaskPriority.URGENT,  # Highest priority
        max_retries=3,
        retry_delay=1.0
    )
    
    task_id = downloader.add_task(task)
    print(f"🚀 Started high-performance download: {task_id}")
    print("�?Optimized for maximum speed and reliability")

if __name__ == "__main__":
    high_performance_download()
```

### Example 10: Memory-Efficient Configuration

**Scenario:** Configure for low-memory environments

```python
#!/usr/bin/env python3
"""Memory-efficient download configuration"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.app.settings import Settings

def memory_efficient_download():
    settings = Settings()
    
    # Memory-conservative settings
    settings.set("network", "max_concurrent_downloads", 2)
    settings.set("network", "max_concurrent_segments", 4)
    settings.set("network", "chunk_size", 262144)  # 256KB chunks
    
    # Enable aggressive memory optimization
    settings.set("advanced", "memory_optimization", True)
    settings.set("advanced", "buffer_size", 1048576)  # 1MB buffer
    settings.set("advanced", "cleanup_interval", 30)  # Cleanup every 30s
    
    downloader = DownloadManager(settings)
    downloader.start()
    
    task = DownloadTask(
        name="Memory Efficient Download",
        base_url="https://example.com/video.m3u8",
        output_file="./downloads/memory_efficient_video.mp4",
        priority=TaskPriority.LOW
    )
    
    task_id = downloader.add_task(task)
    print(f"💾 Started memory-efficient download: {task_id}")
    print("🔧 Optimized for low-memory environments")

if __name__ == "__main__":
    memory_efficient_download()
```

---

## Error Handling Patterns

### Example 11: Comprehensive Error Handling

**Scenario:** Handle all types of errors gracefully

```python
#!/usr/bin/env python3
"""Comprehensive error handling example"""

from src.core.downloader import DownloadManager, DownloadTask, TaskPriority
from src.core.exceptions import VidTaniumException, ErrorCategory, ErrorSeverity
from src.core.error_handler import error_handler
from src.app.settings import Settings
import logging

def comprehensive_error_handling():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    settings = Settings()
    downloader = DownloadManager(settings)
    downloader.start()
    
    # Start error handler
    error_handler.start()
    
    urls_to_try = [
        "https://example.com/working-video.m3u8",
        "https://invalid-domain.com/video.m3u8",  # Will fail
        "https://example.com/protected-video.m3u8",  # May need auth
        "https://example.com/large-video.m3u8"  # May timeout
    ]
    
    for i, url in enumerate(urls_to_try, 1):
        try:
            logger.info(f"Attempting download {i}: {url}")
            
            task = DownloadTask(
                name=f"Test Video {i}",
                base_url=url,
                output_file=f"./downloads/test_video_{i}.mp4",
                priority=TaskPriority.NORMAL,
                max_retries=3,
                retry_delay=2.0
            )
            
            task_id = downloader.add_task(task)
            logger.info(f"�?Task created: {task_id}")
            
        except VidTaniumException as e:
            logger.error(f"�?VidTanium error for {url}")
            logger.error(f"   Category: {e.category}")
            logger.error(f"   Severity: {e.severity}")
            logger.error(f"   Message: {e.message}")
            
            if e.suggested_actions:
                logger.info("💡 Suggested actions:")
                for action in e.suggested_actions:
                    logger.info(f"   - {action}")
            
            # Handle specific error categories
            if e.category == ErrorCategory.NETWORK:
                logger.info("🔄 Network error - will retry with different settings")
                # Implement network-specific recovery
                
            elif e.category == ErrorCategory.AUTHENTICATION:
                logger.info("🔐 Authentication error - check credentials")
                # Implement auth-specific recovery
                
            elif e.category == ErrorCategory.FILESYSTEM:
                logger.info("📁 Filesystem error - check permissions and space")
                # Implement filesystem-specific recovery
                
        except Exception as e:
            logger.error(f"💥 Unexpected error for {url}: {str(e)}")
            # Handle unexpected errors
            
    logger.info("🏁 Error handling demonstration completed")

if __name__ == "__main__":
    comprehensive_error_handling()
```

---

## Automation Scripts

### Example 12: Automated Monitoring Script

**Scenario:** Monitor downloads and send notifications

```python
#!/usr/bin/env python3
"""Automated download monitoring script"""

from src.core.downloader import DownloadManager
from src.core.batch_progress_aggregator import batch_progress_aggregator
from src.app.settings import Settings
import time
import smtplib
from email.mime.text import MIMEText

class DownloadMonitor:
    def __init__(self, email_config=None):
        self.settings = Settings()
        self.downloader = DownloadManager(self.settings)
        self.email_config = email_config
        self.monitoring = False
        
    def send_notification(self, subject, message):
        """Send email notification"""
        if not self.email_config:
            print(f"📧 {subject}: {message}")
            return
            
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.email_config['from']
            msg['To'] = self.email_config['to']
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['port']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
                
            print(f"📧 Notification sent: {subject}")
        except Exception as e:
            print(f"�?Failed to send notification: {e}")
    
    def start_monitoring(self):
        """Start monitoring downloads"""
        self.monitoring = True
        print("👁�?Starting download monitoring...")
        
        while self.monitoring:
            try:
                progress = batch_progress_aggregator.get_batch_progress()
                
                # Check for completed downloads
                if progress.completed_tasks > 0:
                    self.send_notification(
                        "VidTanium: Downloads Completed",
                        f"�?{progress.completed_tasks} downloads completed successfully!"
                    )
                
                # Check for failed downloads
                if progress.failed_tasks > 0:
                    self.send_notification(
                        "VidTanium: Download Failures",
                        f"�?{progress.failed_tasks} downloads failed. Please check logs."
                    )
                
                # Check for stalled downloads
                if progress.stalled_tasks > 0:
                    self.send_notification(
                        "VidTanium: Stalled Downloads",
                        f"⚠️ {progress.stalled_tasks} downloads appear stalled."
                    )
                
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"�?Monitoring error: {e}")
                time.sleep(30)  # Wait before retrying

def automated_monitoring():
    # Optional email configuration
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'from': 'your-email@gmail.com',
        'to': 'notifications@example.com'
    }
    
    monitor = DownloadMonitor(email_config)
    monitor.start_monitoring()

if __name__ == "__main__":
    automated_monitoring()
```

---

**Ready for more?** Check out the [Complete Workflow Guide](workflow-guide.md) for comprehensive documentation, or visit the [API Reference](api-reference.md) for detailed technical information.


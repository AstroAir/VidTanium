import pytest
import time
import json
import sqlite3
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, List, Optional

from src.core.download_history_manager import (
    DownloadHistoryManager, DownloadHistoryEntry, HistoryEntryStatus,
    HistoryFilter, SortOrder, HistoryStatistics, download_history_manager
)


class TestHistoryEntryStatus:
    """Test suite for HistoryEntryStatus enum."""

    def test_status_values(self):
        """Test enum values."""
        assert HistoryEntryStatus.COMPLETED.value == "completed"
        assert HistoryEntryStatus.FAILED.value == "failed"
        assert HistoryEntryStatus.CANCELED.value == "canceled"
        assert HistoryEntryStatus.PARTIAL.value == "partial"


class TestDownloadHistoryEntry:
    """Test suite for DownloadHistoryEntry dataclass."""

    def test_entry_creation(self):
        """Test DownloadHistoryEntry creation with all fields."""
        entry = DownloadHistoryEntry(
            entry_id="test_entry",
            task_name="Test Task",
            original_url="https://example.com/video.m3u8",
            output_file="/downloads/video.mp4",
            file_size=1048576,
            status=HistoryEntryStatus.COMPLETED,
            start_time=1234567890.0,
            end_time=1234567950.0,
            duration=60.0,
            average_speed=17476.27,
            peak_speed=20000.0,
            segments_total=100,
            segments_completed=100,
            retry_count=2,
            error_message=None,
            metadata={"quality": "720p"},
            tags=["video", "entertainment"]
        )
        
        assert entry.entry_id == "test_entry"
        assert entry.task_name == "Test Task"
        assert entry.original_url == "https://example.com/video.m3u8"
        assert entry.output_file == "/downloads/video.mp4"
        assert entry.file_size == 1048576
        assert entry.status == HistoryEntryStatus.COMPLETED
        assert entry.start_time == 1234567890.0
        assert entry.end_time == 1234567950.0
        assert entry.duration == 60.0
        assert entry.average_speed == 17476.27
        assert entry.peak_speed == 20000.0
        assert entry.segments_total == 100
        assert entry.segments_completed == 100
        assert entry.retry_count == 2
        assert entry.error_message is None
        assert entry.metadata == {"quality": "720p"}
        assert entry.tags == ["video", "entertainment"]

    def test_entry_defaults(self):
        """Test DownloadHistoryEntry with default values."""
        entry = DownloadHistoryEntry(
            entry_id="test_entry",
            task_name="Test Task",
            original_url="https://example.com/video.m3u8",
            output_file="/downloads/video.mp4",
            file_size=1048576,
            status=HistoryEntryStatus.COMPLETED,
            start_time=1234567890.0,
            end_time=1234567950.0,
            duration=60.0,
            average_speed=17476.27,
            peak_speed=20000.0,
            segments_total=100,
            segments_completed=100,
            retry_count=2
        )
        
        assert entry.error_message is None
        assert entry.metadata == {}
        assert entry.tags == []

    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        # Complete download
        entry = DownloadHistoryEntry(
            entry_id="test1", task_name="Test", original_url="url", output_file="file",
            file_size=1000, status=HistoryEntryStatus.COMPLETED, start_time=0, end_time=0,
            duration=0, average_speed=0, peak_speed=0, segments_total=100,
            segments_completed=100, retry_count=0
        )
        assert entry.completion_percentage == 100.0
        
        # Partial download
        entry.segments_completed = 50
        assert entry.completion_percentage == 50.0
        
        # No segments
        entry.segments_total = 0
        entry.status = HistoryEntryStatus.COMPLETED
        assert entry.completion_percentage == 100.0
        
        entry.status = HistoryEntryStatus.FAILED
        assert entry.completion_percentage == 0.0

    def test_is_successful(self):
        """Test success status check."""
        entry = DownloadHistoryEntry(
            entry_id="test1", task_name="Test", original_url="url", output_file="file",
            file_size=1000, status=HistoryEntryStatus.COMPLETED, start_time=0, end_time=0,
            duration=0, average_speed=0, peak_speed=0, segments_total=100,
            segments_completed=100, retry_count=0
        )
        
        assert entry.is_successful() is True
        
        entry.status = HistoryEntryStatus.FAILED
        assert entry.is_successful() is False
        
        entry.status = HistoryEntryStatus.CANCELED
        assert entry.is_successful() is False

    def test_format_file_size(self):
        """Test file size formatting."""
        entry = DownloadHistoryEntry(
            entry_id="test1", task_name="Test", original_url="url", output_file="file",
            file_size=1048576, status=HistoryEntryStatus.COMPLETED, start_time=0, end_time=0,
            duration=0, average_speed=0, peak_speed=0, segments_total=100,
            segments_completed=100, retry_count=0
        )
        
        formatted = entry.format_file_size()
        assert "MB" in formatted or "1.0" in formatted


class TestHistoryFilter:
    """Test suite for HistoryFilter dataclass."""

    def test_filter_creation(self):
        """Test HistoryFilter creation."""
        filter_obj = HistoryFilter(
            status=HistoryEntryStatus.COMPLETED,
            date_from=1234567890.0,
            date_to=1234567950.0,
            min_file_size=1000,
            max_file_size=10000,
            search_text="video",
            tags=["entertainment"]
        )
        
        assert filter_obj.status == HistoryEntryStatus.COMPLETED
        assert filter_obj.date_from == 1234567890.0
        assert filter_obj.date_to == 1234567950.0
        assert filter_obj.min_file_size == 1000
        assert filter_obj.max_file_size == 10000
        assert filter_obj.search_text == "video"
        assert filter_obj.tags == ["entertainment"]


class TestDownloadHistoryManager:
    """Test suite for DownloadHistoryManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary database for testing with unique name
        import uuid
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{uuid.uuid4().hex[:8]}.db')
        self.temp_db.close()
        self.manager = DownloadHistoryManager(db_path=self.temp_db.name)

    def teardown_method(self):
        """Clean up after tests."""
        # Close any open connections and remove temporary database
        if hasattr(self, 'manager') and self.manager:
            # Close any open database connections
            if hasattr(self.manager, '_connection') and self.manager._connection:
                self.manager._connection.close()

        # Remove temporary database file
        if hasattr(self, 'temp_db') and os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except (OSError, PermissionError):
                # If file is still locked, try again after a short delay
                import time
                time.sleep(0.1)
                try:
                    os.unlink(self.temp_db.name)
                except (OSError, PermissionError):
                    pass  # Ignore if still can't delete

    def test_initialization(self):
        """Test DownloadHistoryManager initialization."""
        assert self.manager.db_path == self.temp_db.name
        assert isinstance(self.manager.callbacks, list)
        assert self.manager._stats_cache is None
        assert self.manager._cache_ttl == 300.0

    def test_database_initialization(self):
        """Test database table creation."""
        # Check if database file exists
        assert os.path.exists(self.temp_db.name)
        
        # Check if tables exist
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='download_history'
            """)
            assert cursor.fetchone() is not None

    def test_add_entry(self):
        """Test adding history entry."""
        entry = DownloadHistoryEntry(
            entry_id="test_entry",
            task_name="Test Task",
            original_url="https://example.com/video.m3u8",
            output_file="/downloads/video.mp4",
            file_size=1048576,
            status=HistoryEntryStatus.COMPLETED,
            start_time=1234567890.0,
            end_time=1234567950.0,
            duration=60.0,
            average_speed=17476.27,
            peak_speed=20000.0,
            segments_total=100,
            segments_completed=100,
            retry_count=2,
            metadata={"quality": "720p"},
            tags=["video"]
        )
        
        result = self.manager.add_entry(entry)
        assert result is True
        
        # Verify entry was added
        entries = self.manager.get_entries()
        assert len(entries) == 1
        assert entries[0].entry_id == "test_entry"
        assert entries[0].task_name == "Test Task"

    def test_add_entry_duplicate(self):
        """Test adding duplicate entry (should replace)."""
        entry1 = DownloadHistoryEntry(
            entry_id="test_entry", task_name="Task 1", original_url="url1",
            output_file="file1", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=0, end_time=0, duration=0, average_speed=0, peak_speed=0,
            segments_total=100, segments_completed=100, retry_count=0
        )
        
        entry2 = DownloadHistoryEntry(
            entry_id="test_entry", task_name="Task 2", original_url="url2",
            output_file="file2", file_size=2000, status=HistoryEntryStatus.FAILED,
            start_time=0, end_time=0, duration=0, average_speed=0, peak_speed=0,
            segments_total=100, segments_completed=50, retry_count=1
        )
        
        self.manager.add_entry(entry1)
        self.manager.add_entry(entry2)
        
        entries = self.manager.get_entries()
        assert len(entries) == 1
        assert entries[0].task_name == "Task 2"  # Should be replaced

    def test_get_entries_no_filter(self):
        """Test getting all entries without filter."""
        # Add test entries
        for i in range(3):
            entry = DownloadHistoryEntry(
                entry_id=f"entry_{i}", task_name=f"Task {i}", original_url=f"url{i}",
                output_file=f"file{i}", file_size=1000 * (i + 1),
                status=HistoryEntryStatus.COMPLETED, start_time=i, end_time=i + 1,
                duration=1, average_speed=1000, peak_speed=1500,
                segments_total=100, segments_completed=100, retry_count=0
            )
            self.manager.add_entry(entry)
        
        entries = self.manager.get_entries()
        assert len(entries) == 3

    def test_get_entries_with_filter(self):
        """Test getting entries with filter."""
        # Add test entries with different statuses
        completed_entry = DownloadHistoryEntry(
            entry_id="completed", task_name="Completed Task", original_url="url1",
            output_file="file1", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=0, end_time=1, duration=1, average_speed=1000, peak_speed=1500,
            segments_total=100, segments_completed=100, retry_count=0
        )
        
        failed_entry = DownloadHistoryEntry(
            entry_id="failed", task_name="Failed Task", original_url="url2",
            output_file="file2", file_size=2000, status=HistoryEntryStatus.FAILED,
            start_time=0, end_time=1, duration=1, average_speed=0, peak_speed=0,
            segments_total=100, segments_completed=50, retry_count=3
        )
        
        self.manager.add_entry(completed_entry)
        self.manager.add_entry(failed_entry)
        
        # Filter by status
        filter_criteria = HistoryFilter(status=HistoryEntryStatus.COMPLETED)
        entries = self.manager.get_entries(filter_criteria=filter_criteria)
        
        assert len(entries) == 1
        assert entries[0].status == HistoryEntryStatus.COMPLETED

    def test_get_entries_with_limit(self):
        """Test getting entries with limit."""
        # Add multiple entries
        for i in range(5):
            entry = DownloadHistoryEntry(
                entry_id=f"entry_{i}", task_name=f"Task {i}", original_url=f"url{i}",
                output_file=f"file{i}", file_size=1000, status=HistoryEntryStatus.COMPLETED,
                start_time=i, end_time=i + 1, duration=1, average_speed=1000, peak_speed=1500,
                segments_total=100, segments_completed=100, retry_count=0
            )
            self.manager.add_entry(entry)
        
        entries = self.manager.get_entries(limit=3)
        assert len(entries) == 3

    def test_get_entry_by_id(self):
        """Test getting entry by ID."""
        entry = DownloadHistoryEntry(
            entry_id="test_entry", task_name="Test Task", original_url="url",
            output_file="file", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=0, end_time=1, duration=1, average_speed=1000, peak_speed=1500,
            segments_total=100, segments_completed=100, retry_count=0
        )

        self.manager.add_entry(entry)

        retrieved = self.manager.get_entry("test_entry")
        assert retrieved is not None
        assert retrieved.entry_id == "test_entry"

        # Test nonexistent entry
        assert self.manager.get_entry("nonexistent") is None

    def test_update_entry(self):
        """Test updating existing entry."""
        entry = DownloadHistoryEntry(
            entry_id="test_entry", task_name="Original Task", original_url="url",
            output_file="file", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=0, end_time=1, duration=1, average_speed=1000, peak_speed=1500,
            segments_total=100, segments_completed=100, retry_count=0
        )
        
        self.manager.add_entry(entry)
        
        # Update entry
        entry.task_name = "Updated Task"
        result = self.manager.update_entry(entry)
        
        assert result is True
        
        retrieved = self.manager.get_entry("test_entry")
        assert retrieved.task_name == "Updated Task"

    def test_delete_entry(self):
        """Test deleting entry."""
        entry = DownloadHistoryEntry(
            entry_id="test_entry", task_name="Test Task", original_url="url",
            output_file="file", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=0, end_time=1, duration=1, average_speed=1000, peak_speed=1500,
            segments_total=100, segments_completed=100, retry_count=0
        )
        
        self.manager.add_entry(entry)
        
        result = self.manager.delete_entry("test_entry")
        assert result is True
        
        # Verify deletion
        assert self.manager.get_entry("test_entry") is None

    def test_delete_nonexistent_entry(self):
        """Test deleting nonexistent entry."""
        result = self.manager.delete_entry("nonexistent")
        assert result is False

    def test_register_callback(self):
        """Test callback registration."""
        callback = Mock()
        self.manager.register_callback(callback)
        
        assert callback in self.manager.callbacks

    def test_trigger_callbacks(self):
        """Test callback triggering."""
        callback = Mock()
        self.manager.register_callback(callback)
        
        entry = DownloadHistoryEntry(
            entry_id="test_entry", task_name="Test Task", original_url="url",
            output_file="file", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=0, end_time=1, duration=1, average_speed=1000, peak_speed=1500,
            segments_total=100, segments_completed=100, retry_count=0
        )
        
        self.manager.add_entry(entry)
        
        callback.assert_called_once_with(entry)

    def test_callback_error_handling(self):
        """Test error handling in callbacks."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()
        
        self.manager.register_callback(error_callback)
        self.manager.register_callback(good_callback)
        
        entry = DownloadHistoryEntry(
            entry_id="test_entry", task_name="Test Task", original_url="url",
            output_file="file", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=0, end_time=1, duration=1, average_speed=1000, peak_speed=1500,
            segments_total=100, segments_completed=100, retry_count=0
        )
        
        self.manager.add_entry(entry)
        
        # Both callbacks should be called despite error
        error_callback.assert_called_once()
        good_callback.assert_called_once()

    def test_export_data(self):
        """Test data export."""
        entry = DownloadHistoryEntry(
            entry_id="test_entry", task_name="Test Task", original_url="url",
            output_file="file", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=0, end_time=1, duration=1, average_speed=1000, peak_speed=1500,
            segments_total=100, segments_completed=100, retry_count=0
        )
        
        self.manager.add_entry(entry)
        
        exported = self.manager.export_data("json")
        data = json.loads(exported)
        
        assert len(data) == 1
        assert data[0]["entry_id"] == "test_entry"

    def test_export_unsupported_format(self):
        """Test export with unsupported format."""
        with pytest.raises(ValueError):
            self.manager.export_data("xml")

    def test_cleanup_old_entries(self):
        """Test cleanup of old entries."""
        # Add old entry
        old_entry = DownloadHistoryEntry(
            entry_id="old_entry", task_name="Old Task", original_url="url",
            output_file="file", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=time.time() - (100 * 24 * 3600), end_time=0, duration=1,
            average_speed=1000, peak_speed=1500, segments_total=100,
            segments_completed=100, retry_count=0
        )
        
        # Add recent entry
        recent_entry = DownloadHistoryEntry(
            entry_id="recent_entry", task_name="Recent Task", original_url="url",
            output_file="file", file_size=1000, status=HistoryEntryStatus.COMPLETED,
            start_time=time.time(), end_time=0, duration=1, average_speed=1000,
            peak_speed=1500, segments_total=100, segments_completed=100, retry_count=0
        )
        
        self.manager.add_entry(old_entry)
        self.manager.add_entry(recent_entry)
        
        # Cleanup entries older than 90 days
        deleted_count = self.manager.cleanup_old_entries(days_to_keep=90)
        
        assert deleted_count == 1
        assert self.manager.get_entry("old_entry") is None
        assert self.manager.get_entry("recent_entry") is not None

    def test_global_history_manager_instance(self):
        """Test global history manager instance."""
        assert download_history_manager is not None
        assert isinstance(download_history_manager, DownloadHistoryManager)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-v", __file__])

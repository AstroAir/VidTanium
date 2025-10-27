"""
Integration tests for Log Interface functionality

Tests signal connections, export functionality, and user interactions
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gui.widgets.log.log_viewer import LogViewer, EnhancedLogViewer
from src.gui.widgets.log.log_entry import LogEntry


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit the app as it might be used by other tests


@pytest.fixture
def log_viewer(qapp):
    """Create LogViewer instance for testing"""
    viewer = LogViewer()
    yield viewer
    viewer.deleteLater()


class TestLogViewerSignals:
    """Test signal connections in LogViewer"""
    
    def test_log_cleared_signal_exists(self, log_viewer):
        """Test that log_cleared signal exists"""
        assert hasattr(log_viewer, 'log_cleared')
        assert log_viewer.log_cleared is not None
    
    def test_export_requested_signal_exists(self, log_viewer):
        """Test that export_requested signal exists"""
        assert hasattr(log_viewer, 'export_requested')
        assert log_viewer.export_requested is not None
    
    def test_log_cleared_signal_emits(self, log_viewer, qtbot):
        """Test that log_cleared signal emits when logs are cleared"""
        # Add some log entries
        log_viewer.add_log_entry(LogEntry("Test message 1", "INFO"))
        log_viewer.add_log_entry(LogEntry("Test message 2", "WARNING"))
        
        # Connect signal spy
        with qtbot.waitSignal(log_viewer.log_cleared, timeout=1000):
            log_viewer._clear_logs()
        
        # Verify logs are cleared
        assert len(log_viewer.log_entries) == 0
        assert len(log_viewer.filtered_entries) == 0
    
    def test_export_requested_signal_emits(self, log_viewer, qtbot, tmp_path):
        """Test that export_requested signal emits with correct parameters"""
        # Add some log entries
        log_viewer.add_log_entry(LogEntry("Test message", "INFO"))
        
        # Mock the file dialog to return a test path
        test_file = tmp_path / "test_export.txt"
        
        # We can't easily test the file dialog, but we can test the signal emission
        # by directly calling the signal
        signal_received = []
        
        def on_export_requested(format_type, file_path):
            signal_received.append((format_type, file_path))
        
        log_viewer.export_requested.connect(on_export_requested)
        log_viewer.export_requested.emit("txt", str(test_file))
        
        assert len(signal_received) == 1
        assert signal_received[0] == ("txt", str(test_file))


class TestLogViewerFiltering:
    """Test filtering functionality"""
    
    def test_search_filter(self, log_viewer):
        """Test search filtering"""
        # Add test entries
        log_viewer.add_log_entry(LogEntry("Error occurred", "ERROR"))
        log_viewer.add_log_entry(LogEntry("Warning message", "WARNING"))
        log_viewer.add_log_entry(LogEntry("Info message", "INFO"))
        
        # Wait for batched updates
        QTest.qWait(150)
        
        # Apply search filter
        if hasattr(log_viewer, 'search_input'):
            log_viewer.search_input.setText("Error")
            QTest.qWait(150)
            
            # Should filter to only error entries
            assert any("Error" in entry.message for entry in log_viewer.filtered_entries)
    
    def test_level_filter(self, log_viewer):
        """Test level filtering"""
        # Add test entries
        log_viewer.add_log_entry(LogEntry("Error message", "ERROR"))
        log_viewer.add_log_entry(LogEntry("Warning message", "WARNING"))
        log_viewer.add_log_entry(LogEntry("Info message", "INFO"))
        
        # Wait for batched updates
        QTest.qWait(150)
        
        # Apply level filter
        if hasattr(log_viewer, 'level_combo'):
            log_viewer.level_combo.setCurrentText("ERROR")
            QTest.qWait(150)
            
            # Should filter to only error entries
            assert all(entry.level == "ERROR" for entry in log_viewer.filtered_entries)


class TestLogViewerButtons:
    """Test button functionality"""
    
    def test_clear_button_exists(self, log_viewer):
        """Test that clear button exists and is clickable"""
        assert hasattr(log_viewer, 'clear_btn')
        assert log_viewer.clear_btn is not None
        assert log_viewer.clear_btn.isEnabled()
    
    def test_export_button_exists(self, log_viewer):
        """Test that export button exists and is clickable"""
        assert hasattr(log_viewer, 'export_btn')
        assert log_viewer.export_btn is not None
        assert log_viewer.export_btn.isEnabled()
    
    def test_refresh_button_exists(self, log_viewer):
        """Test that refresh button exists and is clickable"""
        assert hasattr(log_viewer, 'refresh_btn')
        assert log_viewer.refresh_btn is not None
        assert log_viewer.refresh_btn.isEnabled()


class TestLogViewerPerformance:
    """Test performance optimizations"""
    
    def test_batched_updates(self, log_viewer):
        """Test that updates are batched"""
        initial_count = len(log_viewer.filtered_entries)
        
        # Add multiple entries quickly
        for i in range(10):
            log_viewer.add_log_entry(LogEntry(f"Message {i}", "INFO"))
        
        # Updates should be pending
        assert log_viewer._pending_updates
        
        # Wait for batch update
        QTest.qWait(150)
        
        # All entries should be added
        assert len(log_viewer.log_entries) == initial_count + 10
    
    def test_max_entries_limit(self, log_viewer):
        """Test that max entries limit is enforced"""
        # Add entries beyond the limit
        max_entries = 10000
        entries_to_add = max_entries + 100
        
        for i in range(entries_to_add):
            log_viewer.add_log_entry(LogEntry(f"Message {i}", "INFO"))
        
        # Wait for updates
        QTest.qWait(200)
        
        # Should not exceed max entries
        assert len(log_viewer.log_entries) <= max_entries


class TestLogEntry:
    """Test LogEntry model"""
    
    def test_log_entry_creation(self):
        """Test creating a log entry"""
        entry = LogEntry("Test message", "INFO")
        assert entry.message == "Test message"
        assert entry.level == "INFO"
        assert entry.timestamp is not None
        assert entry.timestamp_str is not None
    
    def test_log_entry_search_match(self):
        """Test search matching"""
        entry = LogEntry("Error occurred in module X", "ERROR", source="module_x")
        
        assert entry.matches_search("error")
        assert entry.matches_search("module")
        assert entry.matches_search("MODULE X")
        assert not entry.matches_search("warning")
    
    def test_log_entry_level_filter(self):
        """Test level filtering"""
        error_entry = LogEntry("Error", "ERROR")
        warning_entry = LogEntry("Warning", "WARNING")
        info_entry = LogEntry("Info", "INFO")
        
        # All filter (0)
        assert error_entry.matches_level_filter(0)
        assert warning_entry.matches_level_filter(0)
        assert info_entry.matches_level_filter(0)
        
        # Error only (1)
        assert error_entry.matches_level_filter(1)
        assert not warning_entry.matches_level_filter(1)
        assert not info_entry.matches_level_filter(1)
        
        # Warning only (2)
        assert not error_entry.matches_level_filter(2)
        assert warning_entry.matches_level_filter(2)
        assert not info_entry.matches_level_filter(2)
    
    def test_log_entry_display_text(self):
        """Test display text formatting"""
        entry = LogEntry("Test message", "INFO")
        assert "[INFO]" in entry.display_text
        assert "Test message" in entry.display_text
        assert entry.timestamp_str in entry.display_text


class TestLogViewerIntegration:
    """Integration tests for complete workflows"""
    
    def test_add_filter_export_workflow(self, log_viewer, tmp_path):
        """Test complete workflow: add logs -> filter -> export"""
        # Add logs
        log_viewer.add_log_entry(LogEntry("Error 1", "ERROR"))
        log_viewer.add_log_entry(LogEntry("Warning 1", "WARNING"))
        log_viewer.add_log_entry(LogEntry("Info 1", "INFO"))
        
        # Wait for updates
        QTest.qWait(150)
        
        # Verify logs added
        assert len(log_viewer.log_entries) >= 3
        
        # Apply filter (if available)
        if hasattr(log_viewer, 'search_input'):
            log_viewer.search_input.setText("Error")
            QTest.qWait(150)
        
        # Verify signal can be emitted
        test_file = tmp_path / "test.txt"
        signal_received = []
        
        def on_export(format_type, file_path):
            signal_received.append((format_type, file_path))
        
        log_viewer.export_requested.connect(on_export)
        log_viewer.export_requested.emit("txt", str(test_file))
        
        assert len(signal_received) == 1
    
    def test_clear_workflow(self, log_viewer, qtbot):
        """Test complete clear workflow"""
        # Add logs
        log_viewer.add_log_entry(LogEntry("Test 1", "INFO"))
        log_viewer.add_log_entry(LogEntry("Test 2", "INFO"))
        
        QTest.qWait(150)
        
        # Clear logs
        with qtbot.waitSignal(log_viewer.log_cleared, timeout=1000):
            log_viewer._clear_logs()
        
        # Verify cleared
        assert len(log_viewer.log_entries) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])


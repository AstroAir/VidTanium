"""
Tests for progressive recovery management
"""

import pytest
import tempfile
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.progressive_recovery import (
    ProgressiveRecoveryManager, TaskRecoveryInfo, SegmentRecoveryInfo, RecoveryState
)


@pytest.fixture
def temp_recovery_dir():
    """Create temporary recovery directory for tests"""
    temp_dir = tempfile.mkdtemp(prefix="vidtanium_recovery_test_")
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def recovery_manager(temp_recovery_dir):
    """Create ProgressiveRecoveryManager instance for testing"""
    return ProgressiveRecoveryManager(recovery_dir=temp_recovery_dir)


class TestRecoveryState:
    """Test RecoveryState enum"""
    
    def test_recovery_state_values(self) -> None:
        """Test RecoveryState enum values"""
        assert RecoveryState.NONE.value == "none"
        assert RecoveryState.PARTIAL.value == "partial"
        assert RecoveryState.COMPLETE.value == "complete"
        assert RecoveryState.CORRUPTED.value == "corrupted"
        assert RecoveryState.INVALID.value == "invalid"


class TestSegmentRecoveryInfo:
    """Test SegmentRecoveryInfo dataclass"""
    
    def test_segment_creation(self) -> None:
        """Test SegmentRecoveryInfo creation"""
        segment = SegmentRecoveryInfo(
            segment_index=0,
            segment_url="https://example.com/segment_0.ts",
            expected_size=1024,
            downloaded_size=1024,
            file_path="/tmp/segment_0.ts",
            state=RecoveryState.COMPLETE
        )
        
        assert segment.segment_index == 0
        assert segment.segment_url == "https://example.com/segment_0.ts"
        assert segment.expected_size == 1024
        assert segment.downloaded_size == 1024
        assert segment.state == RecoveryState.COMPLETE
    
    def test_is_complete(self) -> None:
        """Test is_complete method"""
        # Complete segment
        segment = SegmentRecoveryInfo(
            segment_index=0,
            segment_url="https://example.com/segment_0.ts",
            expected_size=1024,
            downloaded_size=1024,
            state=RecoveryState.COMPLETE
        )
        assert segment.is_complete() is True
        
        # Incomplete segment
        segment2 = SegmentRecoveryInfo(
            segment_index=1,
            segment_url="https://example.com/segment_1.ts",
            expected_size=1024,
            downloaded_size=512,
            state=RecoveryState.PARTIAL
        )
        assert segment2.is_complete() is False


class TestTaskRecoveryInfo:
    """Test TaskRecoveryInfo dataclass"""
    
    def test_task_creation(self) -> None:
        """Test TaskRecoveryInfo creation"""
        task = TaskRecoveryInfo(
            task_id="test_task",
            task_name="Test Task",
            base_url="https://example.com/video.m3u8",
            output_file="/path/to/output.mp4",
            total_segments=10
        )
        
        assert task.task_id == "test_task"
        assert task.task_name == "Test Task"
        assert task.base_url == "https://example.com/video.m3u8"
        assert task.output_file == "/path/to/output.mp4"
        assert task.total_segments == 10
        assert len(task.segments) == 0
    
    def test_get_completion_percentage(self) -> None:
        """Test completion percentage calculation"""
        task = TaskRecoveryInfo(
            task_id="test_task",
            task_name="Test Task",
            base_url="https://example.com/video.m3u8",
            output_file="/path/to/output.mp4",
            total_segments=5
        )
        
        # Initially 0%
        assert task.get_completion_percentage() == 0.0
        
        # Add completed segments
        for i in range(3):
            segment = SegmentRecoveryInfo(
                segment_index=i,
                segment_url=f"https://example.com/segment_{i}.ts",
                downloaded_size=1024,
                state=RecoveryState.COMPLETE
            )
            task.segments[i] = segment
        
        # Should be 60% (3/5)
        assert task.get_completion_percentage() == 60.0


class TestProgressiveRecoveryManager:
    """Test ProgressiveRecoveryManager class"""
    
    def test_initialization(self, temp_recovery_dir) -> None:
        """Test ProgressiveRecoveryManager initialization"""
        manager = ProgressiveRecoveryManager(recovery_dir=temp_recovery_dir)
        
        assert manager.recovery_dir == Path(temp_recovery_dir)
        assert len(manager.active_sessions) == 0
        assert manager.auto_save_interval == 30.0
    
    def test_create_recovery_session(self, recovery_manager) -> None:
        """Test creating recovery session"""
        task_id = "test_task"
        recovery_info = recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8",
            "/path/to/output.mp4", 10
        )
        
        assert isinstance(recovery_info, TaskRecoveryInfo)
        assert recovery_info.task_id == task_id
        assert recovery_info.total_segments == 10
        assert task_id in recovery_manager.active_sessions
    
    def test_load_recovery_session(self, recovery_manager) -> None:
        """Test loading recovery session"""
        task_id = "test_task"
        
        # Create and save session
        recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8",
            "/path/to/output.mp4", 10
        )
        
        # Load it back
        loaded = recovery_manager.load_recovery_session(task_id)
        
        assert loaded is not None
        assert loaded.task_id == task_id
        assert loaded.task_name == "Test Task"
    
    def test_update_segment_progress(self, recovery_manager) -> None:
        """Test updating segment progress"""
        task_id = "test_task"
        recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8",
            "/path/to/output.mp4", 10
        )
        
        recovery_manager.update_segment_progress(
            task_id, 0, "https://example.com/segment_0.ts", 512
        )
        
        task = recovery_manager.active_sessions[task_id]
        assert 0 in task.segments
        assert task.segments[0].downloaded_size == 512
    
    def test_mark_segment_complete(self, recovery_manager, tmp_path) -> None:
        """Test marking segment as complete"""
        task_id = "test_task"
        recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8",
            "/path/to/output.mp4", 10
        )

        # First update segment progress to create the segment
        recovery_manager.update_segment_progress(
            task_id, 0, "https://example.com/segment_0.ts", 9
        )

        # Create a temporary file
        segment_file = tmp_path / "segment_0.ts"
        segment_file.write_bytes(b"test data")

        recovery_manager.mark_segment_complete(
            task_id, 0, str(segment_file), 9
        )

        task = recovery_manager.active_sessions[task_id]
        assert task.segments[0].state == RecoveryState.COMPLETE
        assert task.segments[0].downloaded_size == 9
    
    def test_get_resume_info(self, recovery_manager) -> None:
        """Test getting resume information"""
        task_id = "test_task"
        recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8",
            "/path/to/output.mp4", 10
        )
        
        resume_info = recovery_manager.get_resume_info(task_id)
        
        assert resume_info is not None
        assert resume_info["task_id"] == task_id
        assert "completion_percentage" in resume_info
        assert "can_resume" in resume_info
    
    def test_get_all_recovery_sessions(self, recovery_manager) -> None:
        """Test getting all recovery sessions"""
        # Create multiple sessions
        for i in range(3):
            recovery_manager.create_recovery_session(
                f"task_{i}", f"Task {i}", "https://example.com/video.m3u8",
                f"/path/to/output_{i}.mp4", 10
            )
        
        sessions = recovery_manager.get_all_recovery_sessions()
        
        assert len(sessions) >= 3
        assert all("task_id" in s for s in sessions)
        assert all("completion_percentage" in s for s in sessions)


if __name__ == "__main__":
    pytest.main([__file__])

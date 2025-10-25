"""
Tests for progressive recovery management
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch

from src.core.progressive_recovery import (
    ProgressiveRecoveryManager, RecoverySession, progressive_recovery_manager
)


class TestRecoverySession:
    """Test RecoverySession dataclass"""
    
    def test_recovery_session_creation(self) -> None:
        """Test RecoverySession creation"""
        session = RecoverySession(
            task_id="test_task",
            task_name="Test Task",
            url="https://example.com/video.m3u8",
            output_file="/path/to/output.mp4",
            total_segments=100
        )
        
        assert session.task_id == "test_task"
        assert session.task_name == "Test Task"
        assert session.url == "https://example.com/video.m3u8"
        assert session.output_file == "/path/to/output.mp4"
        assert session.total_segments == 100
        assert session.completed_segments == []
        assert session.failed_segments == []
        assert session.segment_files == {}
        assert session.created_at > 0
        assert session.last_updated > 0
        assert session.can_resume is True
    
    def test_mark_segment_complete(self) -> None:
        """Test marking segment as complete"""
        session = RecoverySession(
            task_id="test_task",
            task_name="Test Task",
            url="https://example.com/video.m3u8",
            output_file="/path/to/output.mp4",
            total_segments=10
        )
        
        segment_id = 5
        file_path = "/tmp/segment_5.ts"
        file_size = 1024
        
        session.mark_segment_complete(segment_id, file_path, file_size)
        
        assert segment_id in session.completed_segments
        assert segment_id not in session.failed_segments
        assert session.segment_files[segment_id] == {
            "file_path": file_path,
            "file_size": file_size,
            "completed_at": session.last_updated
        }
    
    def test_mark_segment_failed(self) -> None:
        """Test marking segment as failed"""
        session = RecoverySession(
            task_id="test_task",
            task_name="Test Task",
            url="https://example.com/video.m3u8",
            output_file="/path/to/output.mp4",
            total_segments=10
        )
        
        segment_id = 3
        error_message = "Connection timeout"
        
        session.mark_segment_failed(segment_id, error_message)
        
        assert segment_id in session.failed_segments
        assert segment_id not in session.completed_segments
        assert session.failure_reasons[segment_id] == error_message
    
    def test_get_completion_percentage(self) -> None:
        """Test completion percentage calculation"""
        session = RecoverySession(
            task_id="test_task",
            task_name="Test Task",
            url="https://example.com/video.m3u8",
            output_file="/path/to/output.mp4",
            total_segments=10
        )
        
        # Initially 0%
        assert session.get_completion_percentage() == 0.0
        
        # Mark some segments complete
        session.mark_segment_complete(0, "/tmp/segment_0.ts", 1024)
        session.mark_segment_complete(1, "/tmp/segment_1.ts", 1024)
        session.mark_segment_complete(2, "/tmp/segment_2.ts", 1024)
        
        # Should be 30%
        assert session.get_completion_percentage() == 30.0
        
        # Mark all segments complete
        for i in range(3, 10):
            session.mark_segment_complete(i, f"/tmp/segment_{i}.ts", 1024)
        
        # Should be 100%
        assert session.get_completion_percentage() == 100.0
    
    def test_get_remaining_segments(self) -> None:
        """Test getting remaining segments"""
        session = RecoverySession(
            task_id="test_task",
            task_name="Test Task",
            url="https://example.com/video.m3u8",
            output_file="/path/to/output.mp4",
            total_segments=5
        )
        
        # Initially all segments remaining
        remaining = session.get_remaining_segments()
        assert remaining == [0, 1, 2, 3, 4]
        
        # Mark some segments complete
        session.mark_segment_complete(1, "/tmp/segment_1.ts", 1024)
        session.mark_segment_complete(3, "/tmp/segment_3.ts", 1024)
        
        # Should exclude completed segments
        remaining = session.get_remaining_segments()
        assert remaining == [0, 2, 4]
    
    def test_to_dict(self) -> None:
        """Test converting session to dictionary"""
        session = RecoverySession(
            task_id="test_task",
            task_name="Test Task",
            url="https://example.com/video.m3u8",
            output_file="/path/to/output.mp4",
            total_segments=5
        )
        
        session.mark_segment_complete(0, "/tmp/segment_0.ts", 1024)
        session.mark_segment_failed(1, "Network error")
        
        data = session.to_dict()
        
        assert data["task_id"] == "test_task"
        assert data["task_name"] == "Test Task"
        assert data["url"] == "https://example.com/video.m3u8"
        assert data["output_file"] == "/path/to/output.mp4"
        assert data["total_segments"] == 5
        assert data["completed_segments"] == [0]
        assert data["failed_segments"] == [1]
        assert 0 in data["segment_files"]
        assert data["failure_reasons"]["1"] == "Network error"
    
    def test_from_dict(self) -> None:
        """Test creating session from dictionary"""
        data = {
            "task_id": "test_task",
            "task_name": "Test Task",
            "url": "https://example.com/video.m3u8",
            "output_file": "/path/to/output.mp4",
            "total_segments": 5,
            "completed_segments": [0, 2],
            "failed_segments": [1],
            "segment_files": {
                "0": {"file_path": "/tmp/segment_0.ts", "file_size": 1024, "completed_at": 1234567890},
                "2": {"file_path": "/tmp/segment_2.ts", "file_size": 2048, "completed_at": 1234567891}
            },
            "failure_reasons": {"1": "Network error"},
            "created_at": 1234567800,
            "last_updated": 1234567900,
            "can_resume": True
        }
        
        session = RecoverySession.from_dict(data)
        
        assert session.task_id == "test_task"
        assert session.task_name == "Test Task"
        assert session.completed_segments == [0, 2]
        assert session.failed_segments == [1]
        assert len(session.segment_files) == 2
        assert session.failure_reasons["1"] == "Network error"


class TestProgressiveRecoveryManager:
    """Test ProgressiveRecoveryManager class"""
    
    @pytest.fixture
    def temp_dir(self) -> None:
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def recovery_manager(self, temp_dir) -> None:
        """Create a fresh ProgressiveRecoveryManager for testing"""
        return ProgressiveRecoveryManager(recovery_dir=temp_dir)
    
    def test_initialization(self, recovery_manager, temp_dir) -> None:
        """Test ProgressiveRecoveryManager initialization"""
        assert recovery_manager.recovery_dir == temp_dir
        assert recovery_manager.active_sessions == {}
        assert recovery_manager.max_session_age == 86400 * 7  # 7 days
        assert recovery_manager.auto_cleanup_enabled is True
    
    def test_create_recovery_session(self, recovery_manager) -> None:
        """Test creating recovery session"""
        task_id = "test_task"
        task_name = "Test Task"
        url = "https://example.com/video.m3u8"
        output_file = "/path/to/output.mp4"
        total_segments = 100
        
        session = recovery_manager.create_recovery_session(
            task_id, task_name, url, output_file, total_segments
        )
        
        assert isinstance(session, RecoverySession)
        assert session.task_id == task_id
        assert session.task_name == task_name
        assert session.url == url
        assert session.output_file == output_file
        assert session.total_segments == total_segments
        assert task_id in recovery_manager.active_sessions
    
    def test_get_recovery_session_existing(self, recovery_manager) -> None:
        """Test getting existing recovery session"""
        task_id = "test_task"
        session = recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8", 
            "/path/to/output.mp4", 100
        )
        
        retrieved_session = recovery_manager.get_recovery_session(task_id)
        
        assert retrieved_session is session
    
    def test_get_recovery_session_nonexistent(self, recovery_manager) -> None:
        """Test getting non-existent recovery session"""
        retrieved_session = recovery_manager.get_recovery_session("nonexistent_task")
        
        assert retrieved_session is None
    
    def test_mark_segment_complete(self, recovery_manager) -> None:
        """Test marking segment as complete"""
        task_id = "test_task"
        session = recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8", 
            "/path/to/output.mp4", 10
        )
        
        segment_id = 5
        file_path = "/tmp/segment_5.ts"
        file_size = 1024
        
        recovery_manager.mark_segment_complete(task_id, segment_id, file_path, file_size)
        
        assert segment_id in session.completed_segments
        assert session.segment_files[segment_id]["file_path"] == file_path
        assert session.segment_files[segment_id]["file_size"] == file_size
    
    def test_mark_segment_failed(self, recovery_manager) -> None:
        """Test marking segment as failed"""
        task_id = "test_task"
        session = recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8", 
            "/path/to/output.mp4", 10
        )
        
        segment_id = 3
        error_message = "Connection timeout"
        
        recovery_manager.mark_segment_failed(task_id, segment_id, error_message)
        
        assert segment_id in session.failed_segments
        assert session.failure_reasons[segment_id] == error_message
    
    def test_get_resume_info_existing_session(self, recovery_manager) -> None:
        """Test getting resume info for existing session"""
        task_id = "test_task"
        session = recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8", 
            "/path/to/output.mp4", 10
        )
        
        # Mark some segments complete
        recovery_manager.mark_segment_complete(task_id, 0, "/tmp/segment_0.ts", 1024)
        recovery_manager.mark_segment_complete(task_id, 1, "/tmp/segment_1.ts", 1024)
        
        resume_info = recovery_manager.get_resume_info(task_id)
        
        assert resume_info is not None
        assert resume_info["can_resume"] is True
        assert resume_info["completion_percentage"] == 20.0
        assert resume_info["completed_segments"] == [0, 1]
        assert resume_info["remaining_segments"] == [2, 3, 4, 5, 6, 7, 8, 9]
    
    def test_get_resume_info_nonexistent_session(self, recovery_manager) -> None:
        """Test getting resume info for non-existent session"""
        resume_info = recovery_manager.get_resume_info("nonexistent_task")
        
        assert resume_info is None
    
    def test_save_session(self, recovery_manager) -> None:
        """Test saving session to disk"""
        task_id = "test_task"
        session = recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8", 
            "/path/to/output.mp4", 10
        )
        
        recovery_manager.mark_segment_complete(task_id, 0, "/tmp/segment_0.ts", 1024)
        
        recovery_manager.save_session(task_id)
        
        # Check that file was created
        session_file = os.path.join(recovery_manager.recovery_dir, f"{task_id}.json")
        assert os.path.exists(session_file)
        
        # Check file content
        with open(session_file, 'r') as f:
            data = json.load(f)
        
        assert data["task_id"] == task_id
        assert data["completed_segments"] == [0]
    
    def test_load_session(self, recovery_manager) -> None:
        """Test loading session from disk"""
        task_id = "test_task"
        session_data = {
            "task_id": task_id,
            "task_name": "Test Task",
            "url": "https://example.com/video.m3u8",
            "output_file": "/path/to/output.mp4",
            "total_segments": 10,
            "completed_segments": [0, 1],
            "failed_segments": [],
            "segment_files": {
                "0": {"file_path": "/tmp/segment_0.ts", "file_size": 1024, "completed_at": 1234567890},
                "1": {"file_path": "/tmp/segment_1.ts", "file_size": 2048, "completed_at": 1234567891}
            },
            "failure_reasons": {},
            "created_at": 1234567800,
            "last_updated": 1234567900,
            "can_resume": True
        }
        
        # Save session file
        session_file = os.path.join(recovery_manager.recovery_dir, f"{task_id}.json")
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Load session
        session = recovery_manager.load_session(task_id)
        
        assert session is not None
        assert session.task_id == task_id
        assert session.completed_segments == [0, 1]
        assert len(session.segment_files) == 2
        assert task_id in recovery_manager.active_sessions
    
    def test_load_session_nonexistent(self, recovery_manager) -> None:
        """Test loading non-existent session"""
        session = recovery_manager.load_session("nonexistent_task")
        
        assert session is None
    
    def test_remove_session(self, recovery_manager) -> None:
        """Test removing session"""
        task_id = "test_task"
        session = recovery_manager.create_recovery_session(
            task_id, "Test Task", "https://example.com/video.m3u8", 
            "/path/to/output.mp4", 10
        )
        
        recovery_manager.save_session(task_id)
        session_file = os.path.join(recovery_manager.recovery_dir, f"{task_id}.json")
        assert os.path.exists(session_file)
        
        recovery_manager.remove_session(task_id)
        
        assert task_id not in recovery_manager.active_sessions
        assert not os.path.exists(session_file)
    
    def test_cleanup_old_sessions(self, recovery_manager) -> None:
        """Test cleanup of old sessions"""
        task_id = "old_task"
        session = recovery_manager.create_recovery_session(
            task_id, "Old Task", "https://example.com/video.m3u8", 
            "/path/to/output.mp4", 10
        )
        
        # Mock old timestamp
        session.created_at = 1234567890  # Very old timestamp
        recovery_manager.save_session(task_id)
        
        recovery_manager.cleanup_old_sessions()
        
        # Old session should be removed
        assert task_id not in recovery_manager.active_sessions
        session_file = os.path.join(recovery_manager.recovery_dir, f"{task_id}.json")
        assert not os.path.exists(session_file)
    
    def test_get_all_sessions(self, recovery_manager) -> None:
        """Test getting all sessions"""
        # Initially empty
        sessions = recovery_manager.get_all_sessions()
        assert len(sessions) == 0
        
        # Create some sessions
        recovery_manager.create_recovery_session(
            "task1", "Task 1", "https://example.com/video1.m3u8", 
            "/path/to/output1.mp4", 10
        )
        recovery_manager.create_recovery_session(
            "task2", "Task 2", "https://example.com/video2.m3u8", 
            "/path/to/output2.mp4", 20
        )
        
        sessions = recovery_manager.get_all_sessions()
        assert len(sessions) == 2
        assert "task1" in sessions
        assert "task2" in sessions


class TestGlobalProgressiveRecoveryManager:
    """Test global progressive recovery manager instance"""
    
    def test_global_instance_exists(self) -> None:
        """Test that global instance exists and is properly initialized"""
        assert progressive_recovery_manager is not None
        assert isinstance(progressive_recovery_manager, ProgressiveRecoveryManager)
    
    def test_global_instance_functionality(self) -> None:
        """Test basic functionality of global instance"""
        task_id = "global_test_task"
        
        # Should be able to create and manage sessions
        session = progressive_recovery_manager.create_recovery_session(
            task_id, "Global Test Task", "https://example.com/video.m3u8", 
            "/path/to/output.mp4", 10
        )
        
        assert isinstance(session, RecoverySession)
        assert task_id in progressive_recovery_manager.active_sessions
        
        # Cleanup
        progressive_recovery_manager.remove_session(task_id)


if __name__ == "__main__":
    pytest.main([__file__])

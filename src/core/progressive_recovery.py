"""
Progressive Download Recovery for VidTanium

This module provides sophisticated resume functionality that can recover from any
interruption point with byte-level precision and integrity verification.
"""

import os
import json
import hashlib
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RecoveryState(Enum):
    """Recovery state enumeration"""
    NONE = "none"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CORRUPTED = "corrupted"
    INVALID = "invalid"


@dataclass
class SegmentRecoveryInfo:
    """Recovery information for a single segment"""
    segment_index: int
    segment_url: str
    expected_size: int = 0
    downloaded_size: int = 0
    file_path: str = ""
    checksum: str = ""
    last_modified: float = 0.0
    download_start_time: float = 0.0
    download_end_time: float = 0.0
    retry_count: int = 0
    state: RecoveryState = RecoveryState.NONE
    
    def is_complete(self) -> bool:
        """Check if segment is completely downloaded"""
        return (self.state == RecoveryState.COMPLETE and 
                self.downloaded_size > 0 and
                (self.expected_size == 0 or self.downloaded_size == self.expected_size))
    
    def is_valid(self) -> bool:
        """Check if segment data is valid"""
        if not self.file_path or not os.path.exists(self.file_path):
            return False
        
        actual_size = os.path.getsize(self.file_path)
        return (actual_size == self.downloaded_size and 
                self.state not in [RecoveryState.CORRUPTED, RecoveryState.INVALID])
    
    def calculate_checksum(self) -> str:
        """Calculate checksum of downloaded segment"""
        if not self.file_path or not os.path.exists(self.file_path):
            return ""
        
        try:
            hasher = hashlib.sha256()
            with open(self.file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {self.file_path}: {e}")
            return ""


@dataclass
class TaskRecoveryInfo:
    """Recovery information for an entire download task"""
    task_id: str
    task_name: str
    base_url: str
    output_file: str
    total_segments: int
    segments: Dict[int, SegmentRecoveryInfo] = field(default_factory=dict)
    total_size: int = 0
    downloaded_size: int = 0
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    recovery_version: str = "1.0"
    
    def get_completion_percentage(self) -> float:
        """Get download completion percentage"""
        if self.total_segments == 0:
            return 0.0
        
        completed_segments = sum(1 for seg in self.segments.values() if seg.is_complete())
        return (completed_segments / self.total_segments) * 100.0
    
    def get_resumable_segments(self) -> List[int]:
        """Get list of segments that need to be downloaded or resumed"""
        resumable = []
        for i in range(self.total_segments):
            if i not in self.segments:
                resumable.append(i)
            elif not self.segments[i].is_complete():
                resumable.append(i)
        return resumable
    
    def get_completed_segments(self) -> List[int]:
        """Get list of completed segments"""
        return [i for i, seg in self.segments.items() if seg.is_complete()]
    
    def validate_integrity(self) -> Tuple[bool, List[int]]:
        """Validate integrity of all downloaded segments"""
        corrupted_segments = []
        
        for segment_index, segment_info in self.segments.items():
            if segment_info.is_complete():
                if not segment_info.is_valid():
                    corrupted_segments.append(segment_index)
                    segment_info.state = RecoveryState.CORRUPTED
                    logger.warning(f"Segment {segment_index} is corrupted")
        
        return len(corrupted_segments) == 0, corrupted_segments


class ProgressiveRecoveryManager:
    """Manager for progressive download recovery"""
    
    def __init__(self, recovery_dir: str = ".vidtanium_recovery"):
        self.recovery_dir = Path(recovery_dir)
        self.recovery_dir.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        
        # Active recovery sessions
        self.active_sessions: Dict[str, TaskRecoveryInfo] = {}
        
        # Configuration
        self.auto_save_interval = 30.0  # Save every 30 seconds
        self.integrity_check_interval = 300.0  # Check integrity every 5 minutes
        self.max_recovery_age_days = 7  # Keep recovery files for 7 days
        
        logger.info(f"Progressive recovery manager initialized with recovery dir: {self.recovery_dir}")
    
    def create_recovery_session(self, task_id: str, task_name: str, base_url: str,
                               output_file: str, total_segments: int) -> TaskRecoveryInfo:
        """Create a new recovery session"""
        with self.lock:
            recovery_info = TaskRecoveryInfo(
                task_id=task_id,
                task_name=task_name,
                base_url=base_url,
                output_file=output_file,
                total_segments=total_segments
            )
            
            self.active_sessions[task_id] = recovery_info
            self._save_recovery_info(recovery_info)
            
            logger.info(f"Created recovery session for task: {task_id}")
            return recovery_info
    
    def load_recovery_session(self, task_id: str) -> Optional[TaskRecoveryInfo]:
        """Load existing recovery session"""
        recovery_file = self.recovery_dir / f"{task_id}.json"
        
        if not recovery_file.exists():
            return None
        
        try:
            with open(recovery_file, 'r') as f:
                data = json.load(f)
            
            # Convert segments data back to SegmentRecoveryInfo objects
            segments = {}
            for seg_idx, seg_data in data.get('segments', {}).items():
                segments[int(seg_idx)] = SegmentRecoveryInfo(**seg_data)
            
            recovery_info = TaskRecoveryInfo(
                task_id=data['task_id'],
                task_name=data['task_name'],
                base_url=data['base_url'],
                output_file=data['output_file'],
                total_segments=data['total_segments'],
                segments=segments,
                total_size=data.get('total_size', 0),
                downloaded_size=data.get('downloaded_size', 0),
                created_at=data.get('created_at', time.time()),
                last_updated=data.get('last_updated', time.time()),
                recovery_version=data.get('recovery_version', '1.0')
            )
            
            # Validate loaded data
            is_valid, corrupted = recovery_info.validate_integrity()
            if corrupted:
                logger.warning(f"Found {len(corrupted)} corrupted segments in recovery session {task_id}")
            
            self.active_sessions[task_id] = recovery_info
            logger.info(f"Loaded recovery session for task: {task_id} "
                       f"({recovery_info.get_completion_percentage():.1f}% complete)")
            
            return recovery_info
            
        except Exception as e:
            logger.error(f"Error loading recovery session {task_id}: {e}")
            return None
    
    def update_segment_progress(self, task_id: str, segment_index: int, 
                              segment_url: str, downloaded_size: int,
                              file_path: str = "", expected_size: int = 0):
        """Update progress for a specific segment"""
        with self.lock:
            if task_id not in self.active_sessions:
                logger.warning(f"No active recovery session for task: {task_id}")
                return
            
            recovery_info = self.active_sessions[task_id]
            
            if segment_index not in recovery_info.segments:
                recovery_info.segments[segment_index] = SegmentRecoveryInfo(
                    segment_index=segment_index,
                    segment_url=segment_url,
                    download_start_time=time.time()
                )
            
            segment_info = recovery_info.segments[segment_index]
            segment_info.downloaded_size = downloaded_size
            segment_info.file_path = file_path
            segment_info.expected_size = expected_size
            segment_info.last_modified = time.time()
            
            # Update state based on progress
            if expected_size > 0 and downloaded_size >= expected_size:
                segment_info.state = RecoveryState.COMPLETE
                segment_info.download_end_time = time.time()
                segment_info.checksum = segment_info.calculate_checksum()
            elif downloaded_size > 0:
                segment_info.state = RecoveryState.PARTIAL
            
            # Update task totals
            recovery_info.downloaded_size = sum(
                seg.downloaded_size for seg in recovery_info.segments.values()
            )
            recovery_info.last_updated = time.time()
            
            # Auto-save periodically
            if (time.time() - getattr(self, '_last_save_time', 0) > self.auto_save_interval):
                self._save_recovery_info(recovery_info)
                self._last_save_time = time.time()
    
    def mark_segment_complete(self, task_id: str, segment_index: int, 
                            file_path: str, final_size: int):
        """Mark a segment as completely downloaded"""
        with self.lock:
            if task_id not in self.active_sessions:
                return
            
            recovery_info = self.active_sessions[task_id]
            
            if segment_index in recovery_info.segments:
                segment_info = recovery_info.segments[segment_index]
                segment_info.state = RecoveryState.COMPLETE
                segment_info.downloaded_size = final_size
                segment_info.file_path = file_path
                segment_info.download_end_time = time.time()
                segment_info.checksum = segment_info.calculate_checksum()
                
                recovery_info.last_updated = time.time()
                
                logger.debug(f"Marked segment {segment_index} as complete for task {task_id}")
    
    def mark_segment_failed(self, task_id: str, segment_index: int, error_message: str):
        """Mark a segment as failed"""
        with self.lock:
            if task_id not in self.active_sessions:
                return
            
            recovery_info = self.active_sessions[task_id]
            
            if segment_index in recovery_info.segments:
                segment_info = recovery_info.segments[segment_index]
                segment_info.retry_count += 1
                segment_info.state = RecoveryState.INVALID
                
                logger.warning(f"Segment {segment_index} failed for task {task_id}: {error_message}")
    
    def can_resume_download(self, task_id: str) -> bool:
        """Check if download can be resumed"""
        recovery_info = self.load_recovery_session(task_id)
        if not recovery_info:
            return False
        
        # Check if we have any completed segments
        completed_segments = recovery_info.get_completed_segments()
        return len(completed_segments) > 0
    
    def get_resume_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get information needed to resume download"""
        recovery_info = self.load_recovery_session(task_id)
        if not recovery_info:
            return None
        
        resumable_segments = recovery_info.get_resumable_segments()
        completed_segments = recovery_info.get_completed_segments()
        
        return {
            "task_id": task_id,
            "completion_percentage": recovery_info.get_completion_percentage(),
            "total_segments": recovery_info.total_segments,
            "completed_segments": completed_segments,
            "resumable_segments": resumable_segments,
            "downloaded_size": recovery_info.downloaded_size,
            "total_size": recovery_info.total_size,
            "can_resume": len(completed_segments) > 0
        }
    
    def complete_recovery_session(self, task_id: str):
        """Mark recovery session as complete and clean up"""
        with self.lock:
            if task_id in self.active_sessions:
                recovery_info = self.active_sessions[task_id]
                
                # Final save
                self._save_recovery_info(recovery_info)
                
                # Remove from active sessions
                del self.active_sessions[task_id]
                
                logger.info(f"Completed recovery session for task: {task_id}")
    
    def cleanup_recovery_session(self, task_id: str):
        """Clean up recovery session and files"""
        with self.lock:
            # Remove from active sessions
            if task_id in self.active_sessions:
                del self.active_sessions[task_id]
            
            # Remove recovery file
            recovery_file = self.recovery_dir / f"{task_id}.json"
            if recovery_file.exists():
                try:
                    recovery_file.unlink()
                    logger.info(f"Cleaned up recovery session for task: {task_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up recovery session {task_id}: {e}")
    
    def _save_recovery_info(self, recovery_info: TaskRecoveryInfo):
        """Save recovery information to disk"""
        recovery_file = self.recovery_dir / f"{recovery_info.task_id}.json"
        
        try:
            # Convert to serializable format
            data = asdict(recovery_info)
            
            # Convert segments to serializable format
            data['segments'] = {
                str(idx): asdict(seg) for idx, seg in recovery_info.segments.items()
            }
            
            with open(recovery_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving recovery info for {recovery_info.task_id}: {e}")
    
    def cleanup_old_recovery_files(self):
        """Clean up old recovery files"""
        cutoff_time = time.time() - (self.max_recovery_age_days * 24 * 3600)
        
        try:
            for recovery_file in self.recovery_dir.glob("*.json"):
                if recovery_file.stat().st_mtime < cutoff_time:
                    recovery_file.unlink()
                    logger.debug(f"Cleaned up old recovery file: {recovery_file}")
        except Exception as e:
            logger.error(f"Error cleaning up old recovery files: {e}")
    
    def get_all_recovery_sessions(self) -> List[Dict[str, Any]]:
        """Get information about all recovery sessions"""
        sessions = []
        
        try:
            for recovery_file in self.recovery_dir.glob("*.json"):
                task_id = recovery_file.stem
                recovery_info = self.load_recovery_session(task_id)
                
                if recovery_info:
                    sessions.append({
                        "task_id": task_id,
                        "task_name": recovery_info.task_name,
                        "completion_percentage": recovery_info.get_completion_percentage(),
                        "total_segments": recovery_info.total_segments,
                        "downloaded_size": recovery_info.downloaded_size,
                        "created_at": recovery_info.created_at,
                        "last_updated": recovery_info.last_updated
                    })
        except Exception as e:
            logger.error(f"Error getting recovery sessions: {e}")
        
        return sessions


# Global progressive recovery manager instance
progressive_recovery_manager = ProgressiveRecoveryManager()

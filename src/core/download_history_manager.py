"""
Download History Manager for VidTanium
Provides comprehensive download history tracking with search, filtering, and management
"""

import time
import json
import sqlite3
import threading
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import hashlib
from datetime import datetime, timedelta

from loguru import logger


class HistoryEntryStatus(Enum):
    """Status of history entries"""
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    PARTIAL = "partial"


class SortOrder(Enum):
    """Sort order options"""
    NEWEST_FIRST = "newest_first"
    OLDEST_FIRST = "oldest_first"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    SIZE_ASC = "size_asc"
    SIZE_DESC = "size_desc"
    DURATION_ASC = "duration_asc"
    DURATION_DESC = "duration_desc"


@dataclass
class DownloadHistoryEntry:
    """Single download history entry"""
    entry_id: str
    task_name: str
    original_url: str
    output_file: str
    file_size: int
    status: HistoryEntryStatus
    start_time: float
    end_time: float
    duration: float
    average_speed: float
    peak_speed: float
    segments_total: int
    segments_completed: int
    retry_count: int
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.segments_total == 0:
            return 100.0 if self.status == HistoryEntryStatus.COMPLETED else 0.0
        return (self.segments_completed / self.segments_total) * 100.0
    
    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score (0-100)"""
        if self.duration == 0:
            return 0.0
        
        # Base score on speed vs theoretical optimal
        theoretical_time = self.file_size / (10 * 1024 * 1024)  # Assume 10MB/s optimal
        efficiency = min(theoretical_time / self.duration, 1.0) * 100
        
        # Adjust for retry count
        retry_penalty = min(self.retry_count * 5, 30)  # Max 30% penalty
        
        return max(0, efficiency - retry_penalty)


@dataclass
class HistoryFilter:
    """Filter criteria for history queries"""
    status: Optional[HistoryEntryStatus] = None
    date_from: Optional[float] = None
    date_to: Optional[float] = None
    min_file_size: Optional[int] = None
    max_file_size: Optional[int] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    search_text: Optional[str] = None
    tags: Optional[List[str]] = None
    has_errors: Optional[bool] = None


@dataclass
class HistoryStatistics:
    """Comprehensive history statistics"""
    total_downloads: int
    successful_downloads: int
    failed_downloads: int
    canceled_downloads: int
    total_data_downloaded: int
    total_time_spent: float
    average_download_speed: float
    most_active_day: str
    most_active_hour: int
    success_rate: float
    average_file_size: int
    largest_download: int
    fastest_download_speed: float
    common_failure_reasons: List[Tuple[str, int]]


class DownloadHistoryManager:
    """Comprehensive download history management system"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "download_history.db"
        self.lock = threading.RLock()
        self.callbacks: List[Callable[[DownloadHistoryEntry], None]] = []
        
        # Initialize database
        self._init_database()
        
        # Cache for frequent queries
        self._stats_cache: Optional[HistoryStatistics] = None
        self._cache_timestamp = 0.0
        self._cache_ttl = 300.0  # 5 minutes
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS download_history (
                        entry_id TEXT PRIMARY KEY,
                        task_name TEXT NOT NULL,
                        original_url TEXT NOT NULL,
                        output_file TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        duration REAL NOT NULL,
                        average_speed REAL NOT NULL,
                        peak_speed REAL NOT NULL,
                        segments_total INTEGER NOT NULL,
                        segments_completed INTEGER NOT NULL,
                        retry_count INTEGER NOT NULL,
                        error_message TEXT,
                        metadata TEXT,
                        tags TEXT,
                        created_at REAL NOT NULL DEFAULT (julianday('now'))
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON download_history(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_start_time ON download_history(start_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_task_name ON download_history(task_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_file_size ON download_history(file_size)")
                
                conn.commit()
                logger.info(f"Download history database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize history database: {e}")
            raise
    
    def add_entry(self, entry: DownloadHistoryEntry) -> bool:
        """Add new history entry"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO download_history (
                            entry_id, task_name, original_url, output_file, file_size,
                            status, start_time, end_time, duration, average_speed,
                            peak_speed, segments_total, segments_completed, retry_count,
                            error_message, metadata, tags
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.entry_id, entry.task_name, entry.original_url,
                        entry.output_file, entry.file_size, entry.status.value,
                        entry.start_time, entry.end_time, entry.duration,
                        entry.average_speed, entry.peak_speed, entry.segments_total,
                        entry.segments_completed, entry.retry_count, entry.error_message,
                        json.dumps(entry.metadata), json.dumps(entry.tags)
                    ))
                    conn.commit()
                
                # Invalidate cache
                self._stats_cache = None
                
                # Trigger callbacks
                self._trigger_callbacks(entry)
                
                logger.debug(f"Added history entry: {entry.task_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add history entry: {e}")
            return False
    
    def get_entries(
        self,
        filter_criteria: Optional[HistoryFilter] = None,
        sort_order: SortOrder = SortOrder.NEWEST_FIRST,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[DownloadHistoryEntry]:
        """Get history entries with filtering and sorting"""
        try:
            with self.lock:
                query = "SELECT * FROM download_history"
                params = []
                conditions = []
                
                # Apply filters
                if filter_criteria:
                    if filter_criteria.status:
                        conditions.append("status = ?")
                        params.append(filter_criteria.status.value)
                    
                    if filter_criteria.date_from:
                        conditions.append("start_time >= ?")
                        params.append(str(filter_criteria.date_from))
                    
                    if filter_criteria.date_to:
                        conditions.append("start_time <= ?")
                        params.append(str(filter_criteria.date_to))
                    
                    if filter_criteria.min_file_size:
                        conditions.append("file_size >= ?")
                        params.append(str(filter_criteria.min_file_size))

                    if filter_criteria.max_file_size:
                        conditions.append("file_size <= ?")
                        params.append(str(filter_criteria.max_file_size))

                    if filter_criteria.min_duration:
                        conditions.append("duration >= ?")
                        params.append(str(filter_criteria.min_duration))

                    if filter_criteria.max_duration:
                        conditions.append("duration <= ?")
                        params.append(str(filter_criteria.max_duration))
                    
                    if filter_criteria.search_text:
                        conditions.append("(task_name LIKE ? OR original_url LIKE ?)")
                        search_pattern = f"%{filter_criteria.search_text}%"
                        params.extend([search_pattern, search_pattern])
                    
                    if filter_criteria.has_errors is not None:
                        if filter_criteria.has_errors:
                            conditions.append("error_message IS NOT NULL")
                        else:
                            conditions.append("error_message IS NULL")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # Apply sorting
                sort_mapping = {
                    SortOrder.NEWEST_FIRST: "start_time DESC",
                    SortOrder.OLDEST_FIRST: "start_time ASC",
                    SortOrder.NAME_ASC: "task_name ASC",
                    SortOrder.NAME_DESC: "task_name DESC",
                    SortOrder.SIZE_ASC: "file_size ASC",
                    SortOrder.SIZE_DESC: "file_size DESC",
                    SortOrder.DURATION_ASC: "duration ASC",
                    SortOrder.DURATION_DESC: "duration DESC"
                }
                query += f" ORDER BY {sort_mapping[sort_order]}"
                
                # Apply limit and offset
                if limit:
                    query += f" LIMIT {limit}"
                if offset:
                    query += f" OFFSET {offset}"
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()
                
                return [self._row_to_entry(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get history entries: {e}")
            return []
    
    def get_entry(self, entry_id: str) -> Optional[DownloadHistoryEntry]:
        """Get specific history entry by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM download_history WHERE entry_id = ?",
                    (entry_id,)
                )
                row = cursor.fetchone()
                
                return self._row_to_entry(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get history entry {entry_id}: {e}")
            return None
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete history entry"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "DELETE FROM download_history WHERE entry_id = ?",
                        (entry_id,)
                    )
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        self._stats_cache = None  # Invalidate cache
                        logger.debug(f"Deleted history entry: {entry_id}")
                        return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete history entry {entry_id}: {e}")
            return False
    
    def delete_entries(self, filter_criteria: HistoryFilter) -> int:
        """Delete multiple entries matching criteria"""
        try:
            with self.lock:
                # First get entries to delete
                entries_to_delete = self.get_entries(filter_criteria)
                
                if not entries_to_delete:
                    return 0
                
                entry_ids = [entry.entry_id for entry in entries_to_delete]
                placeholders = ",".join("?" * len(entry_ids))
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        f"DELETE FROM download_history WHERE entry_id IN ({placeholders})",
                        entry_ids
                    )
                    conn.commit()
                    
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        self._stats_cache = None  # Invalidate cache
                        logger.info(f"Deleted {deleted_count} history entries")
                    
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"Failed to delete history entries: {e}")
            return 0
    
    def get_statistics(self, force_refresh: bool = False) -> HistoryStatistics:
        """Get comprehensive history statistics"""
        current_time = time.time()
        
        # Return cached stats if available and fresh
        if (not force_refresh and 
            self._stats_cache and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._stats_cache
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Basic counts
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status = 'canceled' THEN 1 ELSE 0 END) as canceled,
                        SUM(file_size) as total_data,
                        SUM(duration) as total_time,
                        AVG(average_speed) as avg_speed,
                        AVG(file_size) as avg_file_size,
                        MAX(file_size) as largest_download,
                        MAX(peak_speed) as fastest_speed
                    FROM download_history
                """)
                stats_row = cursor.fetchone()
                
                # Most active day and hour
                cursor = conn.execute("""
                    SELECT strftime('%w', datetime(start_time, 'unixepoch')) as day_of_week,
                           COUNT(*) as count
                    FROM download_history
                    GROUP BY day_of_week
                    ORDER BY count DESC
                    LIMIT 1
                """)
                most_active_day_row = cursor.fetchone()
                
                cursor = conn.execute("""
                    SELECT strftime('%H', datetime(start_time, 'unixepoch')) as hour,
                           COUNT(*) as count
                    FROM download_history
                    GROUP BY hour
                    ORDER BY count DESC
                    LIMIT 1
                """)
                most_active_hour_row = cursor.fetchone()
                
                # Common failure reasons
                cursor = conn.execute("""
                    SELECT error_message, COUNT(*) as count
                    FROM download_history
                    WHERE error_message IS NOT NULL
                    GROUP BY error_message
                    ORDER BY count DESC
                    LIMIT 5
                """)
                failure_reasons = [(row['error_message'], row['count']) for row in cursor.fetchall()]
                
                # Calculate derived statistics
                total = stats_row['total'] or 0
                successful = stats_row['successful'] or 0
                success_rate = (successful / total * 100) if total > 0 else 0
                
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                most_active_day = day_names[int(most_active_day_row['day_of_week'])] if most_active_day_row else 'Unknown'
                most_active_hour = int(most_active_hour_row['hour']) if most_active_hour_row else 0
                
                stats = HistoryStatistics(
                    total_downloads=total,
                    successful_downloads=successful,
                    failed_downloads=stats_row['failed'] or 0,
                    canceled_downloads=stats_row['canceled'] or 0,
                    total_data_downloaded=stats_row['total_data'] or 0,
                    total_time_spent=stats_row['total_time'] or 0,
                    average_download_speed=stats_row['avg_speed'] or 0,
                    most_active_day=most_active_day,
                    most_active_hour=most_active_hour,
                    success_rate=success_rate,
                    average_file_size=int(stats_row['avg_file_size'] or 0),
                    largest_download=stats_row['largest_download'] or 0,
                    fastest_download_speed=stats_row['fastest_speed'] or 0,
                    common_failure_reasons=failure_reasons
                )
                
                # Cache the results
                self._stats_cache = stats
                self._cache_timestamp = current_time
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get history statistics: {e}")
            return HistoryStatistics(
                total_downloads=0, successful_downloads=0, failed_downloads=0,
                canceled_downloads=0, total_data_downloaded=0, total_time_spent=0,
                average_download_speed=0, most_active_day='Unknown', most_active_hour=0,
                success_rate=0, average_file_size=0, largest_download=0,
                fastest_download_speed=0, common_failure_reasons=[]
            )
    
    def _row_to_entry(self, row: sqlite3.Row) -> DownloadHistoryEntry:
        """Convert database row to HistoryEntry"""
        return DownloadHistoryEntry(
            entry_id=row['entry_id'],
            task_name=row['task_name'],
            original_url=row['original_url'],
            output_file=row['output_file'],
            file_size=row['file_size'],
            status=HistoryEntryStatus(row['status']),
            start_time=row['start_time'],
            end_time=row['end_time'],
            duration=row['duration'],
            average_speed=row['average_speed'],
            peak_speed=row['peak_speed'],
            segments_total=row['segments_total'],
            segments_completed=row['segments_completed'],
            retry_count=row['retry_count'],
            error_message=row['error_message'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            tags=json.loads(row['tags']) if row['tags'] else []
        )
    
    def register_callback(self, callback: Callable[[DownloadHistoryEntry], None]):
        """Register callback for new history entries"""
        self.callbacks.append(callback)
    
    def _trigger_callbacks(self, entry: DownloadHistoryEntry):
        """Trigger registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(entry)
            except Exception as e:
                logger.error(f"Error in history callback: {e}")
    
    def export_data(self, format_type: str = "json") -> str:
        """Export history data"""
        entries = self.get_entries()
        
        if format_type.lower() == "json":
            return json.dumps([asdict(entry) for entry in entries], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def cleanup_old_entries(self, days_to_keep: int = 90) -> int:
        """Clean up old history entries"""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        filter_criteria = HistoryFilter(date_to=cutoff_time)
        return self.delete_entries(filter_criteria)


# Global history manager instance
download_history_manager = DownloadHistoryManager()

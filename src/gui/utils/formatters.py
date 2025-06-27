"""
Utility functions for formatting data in the UI
"""

def format_speed(speed_bytes_per_sec: float) -> str:
    """
    Format download speed in human-readable format
    
    Args:
        speed_bytes_per_sec: Speed in bytes per second
        
    Returns:
        Formatted speed string (e.g., "1.5 MB/s")
    """
    try:
        if speed_bytes_per_sec < 0:
            return "0 B/s"
        elif speed_bytes_per_sec < 1024:
            return f"{speed_bytes_per_sec:.0f} B/s"
        elif speed_bytes_per_sec < 1024 * 1024:
            return f"{speed_bytes_per_sec / 1024:.1f} KB/s"
        elif speed_bytes_per_sec < 1024 * 1024 * 1024:
            return f"{speed_bytes_per_sec / (1024 * 1024):.1f} MB/s"
        else:
            return f"{speed_bytes_per_sec / (1024 * 1024 * 1024):.1f} GB/s"
    except (ValueError, TypeError, ZeroDivisionError):
        return "0 B/s"


def format_bytes(bytes_count: int) -> str:
    """
    Format byte count in human-readable format
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    try:
        if bytes_count < 0:
            return "0 B"
        elif bytes_count < 1024:
            return f"{bytes_count} B"
        elif bytes_count < 1024 * 1024:
            return f"{bytes_count / 1024:.1f} KB"
        elif bytes_count < 1024 * 1024 * 1024:
            return f"{bytes_count / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_count / (1024 * 1024 * 1024):.1f} GB"
    except (ValueError, TypeError, ZeroDivisionError):
        return "0 B"


def format_time(seconds: float) -> str:
    """
    Format time duration in human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted time string (e.g., "1h 23m 45s")
    """
    try:
        if seconds < 0:
            return "0s"
        elif seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            remaining_seconds = seconds % 60
            if remaining_seconds < 1:
                return f"{minutes:.0f}m"
            else:
                return f"{minutes:.0f}m {remaining_seconds:.0f}s"
        else:
            hours = seconds / 3600
            remaining_minutes = (seconds % 3600) / 60
            if remaining_minutes < 1:
                return f"{hours:.0f}h"
            else:
                return f"{hours:.0f}h {remaining_minutes:.0f}m"
    except (ValueError, TypeError, ZeroDivisionError):
        return "0s"


def format_percentage(completed: int, total: int, decimals: int = 1) -> str:
    """
    Format percentage with proper error handling
    
    Args:
        completed: Number of completed items
        total: Total number of items
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string (e.g., "75.5%")
    """
    try:
        if total <= 0:
            return "0%"
        percentage = (completed / total) * 100
        percentage = max(0, min(100, percentage))  # Clamp between 0 and 100
        return f"{percentage:.{decimals}f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "0%"


def format_eta(estimated_seconds: float) -> str:
    """
    Format estimated time of arrival
    
    Args:
        estimated_seconds: Estimated seconds remaining
        
    Returns:
        Formatted ETA string (e.g., "ETA: 5m 32s", "ETA: calculating...")
    """
    try:
        if estimated_seconds is None or estimated_seconds <= 0:
            return "ETA: calculating..."
        
        time_str = format_time(estimated_seconds)
        return f"ETA: {time_str}"
    except (ValueError, TypeError):
        return "ETA: calculating..."


def format_task_status(status: str) -> str:
    """
    Format task status for display
    
    Args:
        status: Raw status string
        
    Returns:
        Formatted status string
    """
    status_map = {
        'pending': '等待中',
        'running': '下载中',
        'downloading': '下载中',
        'paused': '已暂停',
        'completed': '已完成',
        'failed': '失败',
        'error': '错误',
        'cancelled': '已取消',
        'canceled': '已取消'
    }
    
    return status_map.get(status.lower(), status.title())


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division with default fallback
    
    Args:
        numerator: The dividend
        denominator: The divisor
        default: Default value if division fails
        
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (ValueError, TypeError, ZeroDivisionError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between minimum and maximum bounds
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped value
    """
    try:
        return max(min_val, min(max_val, value))
    except (ValueError, TypeError):
        return min_val

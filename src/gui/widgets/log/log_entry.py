"""
Log Entry Model Class

Defines the data structure and utility methods for log entries.
"""

from datetime import datetime


class LogEntry:
    """Data model for a single log entry."""

    def __init__(self, message: str, level: str = "info", details: str | None = None, timestamp: datetime | None = None, source: str | None = None) -> None:
        """
        Create a log entry.

        Args:
            message (str): The content of the log message.
            level (str): Log level ('info', 'warning', 'error').
            details (str, optional): Additional details for the log entry.
            timestamp (datetime, optional): Timestamp for the log entry (defaults to now).
            source (str, optional): Source of the log entry.
        """
        self.message = message
        self.level = level.upper()
        self.timestamp = timestamp or datetime.now()
        self.timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self.details = details or ""
        self.source = source or ""
        self.display_text = f"[{self.timestamp_str}] [{self.level}] {self.message}"

    def matches_search(self, search_text: str) -> bool:
        """
        Check if the log entry matches the search text.

        Args:
            search_text (str): The text to search for.

        Returns:
            bool: True if the log entry matches the search text, False otherwise.
        """
        if not search_text:
            return True

        search_text = search_text.lower()
        return (search_text in self.message.lower() or
                search_text in self.level.lower() or
                search_text in self.details.lower() or
                search_text in self.source.lower())

    def matches_level_filter(self, level_filter: int) -> bool:
        """
        Check if the log entry matches the level filter.

        Args:
            level_filter (int): Level filter index (0=All, 1=Error only, 2=Warning only, 3=Info only, 4=No Error).

        Returns:
            bool: True if the log entry matches the level filter, False otherwise.
        """
        if level_filter == 0:  # All
            return True
        elif level_filter == 1:  # Error only
            return self.level == "ERROR"
        elif level_filter == 2:  # Warning only
            return self.level == "WARNING"
        elif level_filter == 3:  # Info only
            return self.level == "INFO"
        elif level_filter == 4:  # No Error
            return self.level != "ERROR"
        return True

    def matches_date_filter(self, date_filter: int) -> bool:
        """
        Check if the log entry matches the date filter.

        Args:
            date_filter (int): Date filter index (0=All, 1=Today, 2=Within 1 hour, 3=Within 10 minutes).

        Returns:
            bool: True if the log entry matches the date filter, False otherwise.
        """
        if date_filter == 0:  # All
            return True

        now = datetime.now()

        if date_filter == 1:  # Today
            return self.timestamp.date() == now.date()
        elif date_filter == 2:  # Within 1 hour
            return (now - self.timestamp).total_seconds() <= 3600
        elif date_filter == 3:  # Within 10 minutes
            return (now - self.timestamp).total_seconds() <= 600

        return True

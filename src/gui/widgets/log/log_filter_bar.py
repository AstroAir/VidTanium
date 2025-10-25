"""
Log Filter Bar Component

Provides log search and filtering functionality.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal

from qfluentwidgets import ComboBox, SearchLineEdit


class LogFilterBar(QWidget):
    """Log filter bar component."""

    # Signal definition
    filterChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)

        # Search box
        self.search_input = SearchLineEdit(self)
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.textChanged.connect(self.filterChanged.emit)
        layout.addWidget(self.search_input, 3)

        # Log level filter
        layout.addWidget(QLabel("Show Level:"), 0)
        self.level_combo = ComboBox(self)
        self.level_combo.addItems(
            ["All", "Error Only", "Warning Only", "Info Only", "No Error"])
        self.level_combo.setToolTip("Select the log level to display")
        self.level_combo.currentIndexChanged.connect(self.filterChanged.emit)
        layout.addWidget(self.level_combo, 1)

        # Date filter
        layout.addWidget(QLabel("Time Range:"), 0)
        self.date_combo = ComboBox(self)
        self.date_combo.addItems(
            ["All", "Today", "Within 1 Hour", "Within 10 Minutes"])
        self.date_combo.currentIndexChanged.connect(self.filterChanged.emit)
        layout.addWidget(self.date_combo, 1)

    def get_search_text(self) -> str:
        """Get the search text."""
        return self.search_input.text()

    def get_level_filter(self) -> int:
        """Get the level filter index."""
        return self.level_combo.currentIndex()

    def get_date_filter(self) -> int:
        """Get the date filter index."""
        return self.date_combo.currentIndex()

    def reset_filters(self) -> None:
        """Reset all filters."""
        self.search_input.clear()
        self.level_combo.setCurrentIndex(0)
        self.date_combo.setCurrentIndex(0)

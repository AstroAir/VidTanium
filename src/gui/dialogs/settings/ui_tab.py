from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout
)
from PySide6.QtCore import Qt, Signal

from qfluentwidgets import (
    CheckBox
)


class UITab(QWidget):
    """UI settings tab"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        """Create user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # UI settings
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setSpacing(12)

        # Show detailed progress
        self.show_detailed_progress_check = CheckBox(
            "Show detailed download progress")
        form_layout.addRow("", self.show_detailed_progress_check)

        # Minimize to tray
        self.minimize_to_tray_check = CheckBox("Minimize to system tray")
        form_layout.addRow("", self.minimize_to_tray_check)

        # Show notifications
        self.show_notifications_check = CheckBox("Show desktop notifications")
        form_layout.addRow("", self.show_notifications_check)

        # Exit confirmation
        self.confirm_on_exit_check = CheckBox("Confirm on exit")
        form_layout.addRow("", self.confirm_on_exit_check)

        layout.addLayout(form_layout)
        layout.addStretch()

    def load_settings(self, settings):
        """Load settings to UI"""
        # UI settings
        self.show_detailed_progress_check.setChecked(
            settings.get("ui", "show_detailed_progress", True))
        self.minimize_to_tray_check.setChecked(
            settings.get("ui", "minimize_to_tray", False))
        self.show_notifications_check.setChecked(
            settings.get("ui", "show_notifications", True))
        self.confirm_on_exit_check.setChecked(
            settings.get("ui", "confirm_on_exit", True))

    def save_settings(self, settings):
        """Save settings"""
        # UI settings
        settings.set("ui", "show_detailed_progress",
                     self.show_detailed_progress_check.isChecked())
        settings.set("ui", "minimize_to_tray",
                     self.minimize_to_tray_check.isChecked())
        settings.set("ui", "show_notifications",
                     self.show_notifications_check.isChecked())
        settings.set("ui", "confirm_on_exit",
                     self.confirm_on_exit_check.isChecked())

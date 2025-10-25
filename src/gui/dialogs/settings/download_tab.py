from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel
)
from PySide6.QtCore import Qt, Signal

from qfluentwidgets import (
    SpinBox, Slider
)


class DownloadTab(QWidget):
    """Download settings tab"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self) -> None:
        """Create user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Download settings
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setSpacing(12)

        # Max concurrent tasks
        self.max_tasks_spin = SpinBox()
        self.max_tasks_spin.setRange(1, 10)
        form_layout.addRow("Max concurrent tasks:", self.max_tasks_spin)

        # Max workers per task
        self.max_workers_spin = SpinBox()
        self.max_workers_spin.setRange(1, 32)
        form_layout.addRow("Max workers per task:", self.max_workers_spin)

        # Max retries
        self.max_retries_spin = SpinBox()
        self.max_retries_spin.setRange(1, 10)
        form_layout.addRow("Max retry attempts:", self.max_retries_spin)

        # Retry delay
        self.retry_delay_spin = SpinBox()
        self.retry_delay_spin.setRange(1, 30)
        self.retry_delay_spin.setSuffix(" seconds")
        form_layout.addRow("Retry delay:", self.retry_delay_spin)

        # Request timeout
        self.request_timeout_spin = SpinBox()
        self.request_timeout_spin.setRange(10, 300)
        self.request_timeout_spin.setSuffix(" seconds")
        form_layout.addRow("Request timeout:", self.request_timeout_spin)

        # Chunk size
        self.chunk_size_spin = SpinBox()
        self.chunk_size_spin.setRange(4096, 65536)
        self.chunk_size_spin.setSingleStep(4096)
        self.chunk_size_spin.setSuffix(" bytes")
        form_layout.addRow("Download chunk size:", self.chunk_size_spin)

        # Bandwidth limit
        bandwidth_layout = QHBoxLayout()
        self.bandwidth_slider = Slider(Qt.Orientation.Horizontal)
        self.bandwidth_slider.setRange(0, 10)
        self.bandwidth_slider.setTickPosition(Slider.TickPosition.TicksBelow)
        self.bandwidth_slider.setTickInterval(1)
        bandwidth_layout.addWidget(self.bandwidth_slider)

        self.bandwidth_label = QLabel("No limit")
        bandwidth_layout.addWidget(self.bandwidth_label)

        self.bandwidth_slider.valueChanged.connect(
            self._update_bandwidth_label)

        form_layout.addRow("Bandwidth limit:", bandwidth_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _update_bandwidth_label(self, value) -> None:
        """Update bandwidth limit label"""
        if value == 0:
            self.bandwidth_label.setText("No limit")
        else:
            speeds = ["512KB/s", "1MB/s", "2MB/s", "5MB/s", "10MB/s",
                      "20MB/s", "50MB/s", "100MB/s", "200MB/s", "Unlimited"]
            self.bandwidth_label.setText(speeds[value - 1])

    def load_settings(self, settings) -> None:
        """Load settings to UI"""
        # Download settings
        self.max_tasks_spin.setValue(settings.get(
            "download", "max_concurrent_tasks", 3))
        self.max_workers_spin.setValue(settings.get(
            "download", "max_workers_per_task", 10))
        self.max_retries_spin.setValue(
            settings.get("download", "max_retries", 5))
        self.retry_delay_spin.setValue(
            settings.get("download", "retry_delay", 2))
        self.request_timeout_spin.setValue(
            settings.get("download", "request_timeout", 60))
        self.chunk_size_spin.setValue(
            settings.get("download", "chunk_size", 8192))

        bandwidth_limit = settings.get("download", "bandwidth_limit", 0)
        bandwidth_value = 0
        if bandwidth_limit > 0:
            # Convert bandwidth limit to slider value
            if bandwidth_limit <= 512 * 1024:
                bandwidth_value = 1
            elif bandwidth_limit <= 1024 * 1024:
                bandwidth_value = 2
            elif bandwidth_limit <= 2 * 1024 * 1024:
                bandwidth_value = 3
            elif bandwidth_limit <= 5 * 1024 * 1024:
                bandwidth_value = 4
            elif bandwidth_limit <= 10 * 1024 * 1024:
                bandwidth_value = 5
            elif bandwidth_limit <= 20 * 1024 * 1024:
                bandwidth_value = 6
            elif bandwidth_limit <= 50 * 1024 * 1024:
                bandwidth_value = 7
            elif bandwidth_limit <= 100 * 1024 * 1024:
                bandwidth_value = 8
            else:
                bandwidth_value = 9

        self.bandwidth_slider.setValue(bandwidth_value)

    def save_settings(self, settings) -> None:
        """Save settings"""
        # Download settings
        settings.set("download", "max_concurrent_tasks",
                     self.max_tasks_spin.value())
        settings.set("download", "max_workers_per_task",
                     self.max_workers_spin.value())
        settings.set("download", "max_retries",
                     self.max_retries_spin.value())
        settings.set("download", "retry_delay",
                     self.retry_delay_spin.value())
        settings.set("download", "request_timeout",
                     self.request_timeout_spin.value())
        settings.set("download", "chunk_size",
                     self.chunk_size_spin.value())

        # Bandwidth limit
        bandwidth_value = self.bandwidth_slider.value()
        bandwidth_limit = 0
        if bandwidth_value > 0:
            # Convert slider value to bandwidth limit
            limits = [
                512 * 1024,           # 512KB/s
                1024 * 1024,          # 1MB/s
                2 * 1024 * 1024,      # 2MB/s
                5 * 1024 * 1024,      # 5MB/s
                10 * 1024 * 1024,     # 10MB/s
                20 * 1024 * 1024,     # 20MB/s
                50 * 1024 * 1024,     # 50MB/s
                100 * 1024 * 1024,    # 100MB/s
                200 * 1024 * 1024,    # 200MB/s
                0                     # Unlimited
            ]
            bandwidth_limit = limits[bandwidth_value - 1]

        settings.set("download", "bandwidth_limit", bandwidth_limit)

"""
Settings Dialog wrapper for the unified settings interface
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtCore import Qt, Signal

from qfluentwidgets import FluentIcon

from .settings_interface import SettingsInterface


class SettingsDialog(QDialog):
    """Modern settings dialog using the unified settings interface"""
    
    settings_applied = Signal()
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        
        self.setWindowTitle("VidTanium 设置")
        self.resize(900, 700)
        self.setMinimumSize(800, 600)
        self.setWindowIcon(FIF.SETTING.icon())
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the settings interface
        self.settings_interface = SettingsInterface(self.settings, self)
        self.settings_interface.settings_applied.connect(self.settings_applied)
        self.settings_interface.settings_applied.connect(self.accept)
        
        layout.addWidget(self.settings_interface)

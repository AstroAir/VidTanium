#!/usr/bin/env python3
"""
Test script to verify that the "Create New Task" button works correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.app.application import Application
from src.app.settings import Settings
from src.core.downloader import DownloadManager

import pytest

def test_create_task_dialog(qtbot):
    """Test that the create task dialog can be opened and works correctly using pytest and pytest-qt."""
    vid_app = Application()
    main_window = vid_app.main_window

    assert hasattr(main_window, 'show_new_task_dialog'), "main_window does not have show_new_task_dialog method"
    assert hasattr(main_window, 'settings') and main_window.settings, "Settings not available in main_window"
    assert hasattr(main_window, 'download_manager') and main_window.download_manager, "Download manager not available in main_window"

    from src.gui.dialogs.task_dialog import TaskDialog

    dialog = TaskDialog(main_window.settings, main_window)
    qtbot.addWidget(dialog)
    assert dialog is not None, "TaskDialog could not be instantiated"
    dialog.close()

# To run this test, use: pytest --qt-api=pyqt6 test_task_dialog.py

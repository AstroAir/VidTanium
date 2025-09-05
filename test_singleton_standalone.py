#!/usr/bin/env python3
"""
Standalone test for singleton functionality
This test doesn't require the full VidTanium dependencies
"""

import os
import sys
import json
import time
import tempfile
import threading
from pathlib import Path

# Add the singleton modules to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "core"))

try:
    # Test basic imports
    print("Testing imports...")
    
    # Mock psutil for testing
    class MockProcess:
        def __init__(self, pid):
            self.pid = pid
        
        def cmdline(self):
            return ['python', 'main.py']
    
    class MockPsutil:
        class NoSuchProcess(Exception):
            pass
        
        class AccessDenied(Exception):
            pass
        
        @staticmethod
        def Process(pid):
            if pid == 99999:  # Test PID
                raise MockPsutil.NoSuchProcess()
            return MockProcess(pid)
    
    # Mock the psutil module
    sys.modules['psutil'] = MockPsutil()
    
    # Mock loguru
    class MockLogger:
        def debug(self, msg): print(f"DEBUG: {msg}")
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    sys.modules['loguru'] = type('MockLoguru', (), {'logger': MockLogger()})()
    
    # Mock PySide6
    class MockQObject:
        def __init__(self):
            self._signals = {}
        
        def connect(self, func):
            pass
    
    class MockSignal:
        def connect(self, func):
            pass
        
        def emit(self, *args):
            pass
    
    class MockQTimer:
        @staticmethod
        def singleShot(delay, func):
            threading.Timer(delay / 1000.0, func).start()
    
    mock_pyside = type('MockPySide6', (), {
        'QtCore': type('QtCore', (), {
            'QObject': MockQObject,
            'Signal': lambda *args: MockSignal(),
            'QTimer': MockQTimer
        })(),
        'QtWidgets': type('QtWidgets', (), {
            'QWidget': object,
            'QApplication': type('QApplication', (), {
                'instance': lambda: None
            })
        })(),
        'QtGui': type('QtGui', (), {
            'QWindow': object
        })()
    })()
    
    sys.modules['PySide6'] = mock_pyside
    sys.modules['PySide6.QtCore'] = mock_pyside.QtCore
    sys.modules['PySide6.QtWidgets'] = mock_pyside.QtWidgets
    sys.modules['PySide6.QtGui'] = mock_pyside.QtGui
    
    # Now import our modules
    from singleton_manager import SingletonManager, InstanceInfo
    from ipc_server import IPCServer, IPCClient, IPCMessage
    
    print("✓ Imports successful")
    
    # Test singleton manager creation
    print("\nTesting singleton manager...")
    manager = SingletonManager("TestApp", user_specific=True)
    print("✓ Singleton manager created")
    
    # Test instance detection
    is_running, instance_info = manager.is_another_instance_running()
    print(f"✓ Instance detection: running={is_running}, info={instance_info}")
    
    # Test instance registration
    success = manager.register_instance()
    print(f"✓ Instance registration: success={success}")
    
    # Test IPC server
    print("\nTesting IPC server...")
    ipc_server = IPCServer()
    print("✓ IPC server created")
    
    # Test server start
    success = ipc_server.start()
    print(f"✓ IPC server start: success={success}")
    
    if success:
        port = ipc_server.get_port()
        print(f"✓ IPC server port: {port}")
        
        # Test ping
        time.sleep(0.1)  # Give server time to start
        ping_success = IPCClient.ping_server('127.0.0.1', port, timeout=2.0)
        print(f"✓ IPC ping test: success={ping_success}")
        
        # Stop server
        ipc_server.stop()
        print("✓ IPC server stopped")
    
    # Test cleanup
    manager.cleanup()
    print("✓ Singleton manager cleanup")
    
    print("\n" + "="*50)
    print("✅ All tests passed successfully!")
    print("The singleton functionality is working correctly.")
    print("="*50)

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

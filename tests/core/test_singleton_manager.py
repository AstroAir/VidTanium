"""
Tests for the singleton manager functionality
"""

import os
import sys
import time
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from src.core.singleton_manager import SingletonManager, InstanceInfo, get_singleton_manager
from src.core.ipc_server import IPCServer, IPCClient, IPCMessage


class TestSingletonManager:
    """Test cases for SingletonManager"""
    
    def setup_method(self) -> None:
        """Set up test environment"""
        self.test_app_name = "TestVidTanium"
        self.singleton_manager = SingletonManager(self.test_app_name, user_specific=True)
    
    def teardown_method(self) -> None:
        """Clean up test environment"""
        if self.singleton_manager:
            self.singleton_manager.cleanup()
    
    def test_singleton_creation(self) -> None:
        """Test singleton manager creation"""
        assert self.singleton_manager is not None
        assert self.singleton_manager.app_name == self.test_app_name
        assert self.singleton_manager.user_specific is True
    
    def test_no_existing_instance(self) -> None:
        """Test when no existing instance is running"""
        is_running, instance_info = self.singleton_manager.is_another_instance_running()
        assert is_running is False
        assert instance_info is None
    
    def test_register_instance(self) -> None:
        """Test registering an instance"""
        success = self.singleton_manager.register_instance()
        assert success is True
        
        # Check that we can detect our own instance
        is_running, instance_info = self.singleton_manager.is_another_instance_running()
        # Should return False because it's the same process
        assert is_running is False
    
    def test_cleanup(self) -> None:
        """Test cleanup functionality"""
        # Register instance first
        success = self.singleton_manager.register_instance()
        assert success is True
        
        # Clean up
        self.singleton_manager.cleanup()
        
        # Should be able to register again after cleanup
        success = self.singleton_manager.register_instance()
        assert success is True
    
    @patch('src.core.singleton_manager.psutil.Process')
    def test_stale_lock_file_cleanup(self, mock_process) -> None:
        """Test cleanup of stale lock files"""
        # Mock a non-existent process
        mock_process.side_effect = Exception("Process not found")
        
        # Create a fake lock file with a non-existent PID
        lock_file_path = self.singleton_manager._implementation.lock_file_path
        lock_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        fake_instance_data = {
            'pid': 99999,  # Non-existent PID
            'start_time': time.time(),
            'app_name': self.test_app_name
        }
        
        import json
        with open(lock_file_path, 'w') as f:
            json.dump(fake_instance_data, f)
        
        # Check for existing instance - should clean up stale lock
        is_running, instance_info = self.singleton_manager.is_another_instance_running()
        assert is_running is False
        assert instance_info is None
        
        # Lock file should be removed
        assert not lock_file_path.exists()
    
    def test_global_singleton_manager(self) -> None:
        """Test global singleton manager function"""
        manager1 = get_singleton_manager("TestApp")
        manager2 = get_singleton_manager("TestApp")
        
        # Should return the same instance
        assert manager1 is manager2
        
        # Clean up
        manager1.cleanup()


class TestIPCServer:
    """Test cases for IPC Server"""
    
    def setup_method(self) -> None:
        """Set up test environment"""
        self.ipc_server = IPCServer()
    
    def teardown_method(self) -> None:
        """Clean up test environment"""
        if self.ipc_server:
            self.ipc_server.stop()
    
    def test_ipc_server_creation(self) -> None:
        """Test IPC server creation"""
        assert self.ipc_server is not None
        assert self.ipc_server.host == '127.0.0.1'
        assert self.ipc_server.port > 0
    
    def test_ipc_server_start_stop(self) -> None:
        """Test starting and stopping IPC server"""
        # Start server
        success = self.ipc_server.start()
        assert success is True
        assert self.ipc_server.running is True
        
        # Stop server
        self.ipc_server.stop()
        assert self.ipc_server.running is False
    
    def test_ipc_ping_message(self) -> None:
        """Test ping message handling"""
        # Start server
        success = self.ipc_server.start()
        assert success is True
        
        # Give server time to start
        time.sleep(0.1)
        
        # Send ping message
        success = IPCClient.ping_server('127.0.0.1', self.ipc_server.get_port())
        assert success is True
    
    def test_ipc_activation_message(self) -> None:
        """Test activation message handling"""
        # Start server
        success = self.ipc_server.start()
        assert success is True
        
        # Give server time to start
        time.sleep(0.1)
        
        # Track activation requests
        activation_received = threading.Event()
        
        def on_activation() -> None:
            activation_received.set()
        
        self.ipc_server.activation_requested.connect(on_activation)
        
        # Send activation message
        success = IPCClient.send_activation_request('127.0.0.1', self.ipc_server.get_port())
        assert success is True
        
        # Wait for activation signal
        assert activation_received.wait(timeout=2.0)
    
    def test_ipc_custom_message_handler(self) -> None:
        """Test custom message handler"""
        # Add custom handler
        def custom_handler(message) -> None:
            return {'success': True, 'custom_response': 'test_data'}
        
        self.ipc_server.add_message_handler('custom_action', custom_handler)
        
        # Start server
        success = self.ipc_server.start()
        assert success is True
        
        # Give server time to start
        time.sleep(0.1)
        
        # Send custom message
        message = IPCMessage('custom_action', {'test': 'data'})
        response = IPCClient.send_message('127.0.0.1', self.ipc_server.get_port(), message)
        
        assert response is not None
        assert response['success'] is True
        assert response['custom_response'] == 'test_data'


class TestIntegration:
    """Integration tests for singleton functionality"""
    
    def test_full_singleton_workflow(self) -> None:
        """Test complete singleton workflow"""
        app_name = "IntegrationTestApp"
        
        # Create first instance
        manager1 = SingletonManager(app_name, user_specific=True)
        ipc_server1 = IPCServer()
        
        try:
            # Start IPC server
            assert ipc_server1.start() is True
            
            # Register first instance
            port1 = ipc_server1.get_port()
            assert manager1.register_instance(port1) is True
            
            # Create second instance
            manager2 = SingletonManager(app_name, user_specific=True)
            
            # Check if another instance is running
            is_running, instance_info = manager2.is_another_instance_running()
            assert is_running is True
            assert instance_info is not None
            assert instance_info.ipc_port == port1
            
            # Try to activate existing instance
            activation_received = threading.Event()
            
            def on_activation() -> None:
                activation_received.set()
            
            ipc_server1.activation_requested.connect(on_activation)
            
            # Activate existing instance
            success = manager2.try_activate_existing(instance_info)
            assert success is True
            
            # Wait for activation signal
            assert activation_received.wait(timeout=2.0)
            
        finally:
            # Clean up
            ipc_server1.stop()
            manager1.cleanup()
            manager2.cleanup()
    
    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
    def test_file_locking_mechanism(self) -> None:
        """Test file locking mechanism on Unix systems"""
        app_name = "FileLockTestApp"
        
        manager1 = SingletonManager(app_name, user_specific=True)
        manager2 = SingletonManager(app_name, user_specific=True)
        
        try:
            # Register first instance
            assert manager1.register_instance() is True
            
            # Try to register second instance (should fail due to file lock)
            assert manager2.register_instance() is False
            
        finally:
            manager1.cleanup()
            manager2.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])

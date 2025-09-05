#!/usr/bin/env python3
"""
Demonstration script for VidTanium singleton functionality

This script demonstrates how the singleton process management works.
Run this script multiple times to see the singleton behavior in action.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.singleton_manager import get_singleton_manager
from src.core.ipc_server import IPCServer, IPCClient
from src.core.window_activator import get_window_activator


def simulate_application():
    """Simulate a simple application with singleton behavior"""
    print("VidTanium Singleton Demo")
    print("=" * 40)
    
    # Get singleton manager
    singleton_manager = get_singleton_manager("VidTaniumDemo", user_specific=True)
    
    # Check if another instance is running
    print("Checking for existing instances...")
    is_running, instance_info = singleton_manager.is_another_instance_running()
    
    if is_running and instance_info:
        print(f"✓ Found existing instance (PID: {instance_info.pid})")
        
        if instance_info.ipc_port:
            print(f"  IPC Port: {instance_info.ipc_port}")
            print("  Attempting to activate existing instance...")
            
            # Try to activate the existing instance
            success = singleton_manager.try_activate_existing(instance_info)
            
            if success:
                print("✓ Successfully activated existing instance")
                print("  The existing window should now be brought to the foreground")
            else:
                print("✗ Failed to activate existing instance")
                print("  The existing instance may not be responding")
        else:
            print("  No IPC port available for activation")
        
        print("\nExiting - another instance is already running")
        return 0
    
    print("✓ No existing instance found")
    print("Starting new instance...")
    
    # Create and start IPC server
    ipc_server = IPCServer()
    
    if not ipc_server.start():
        print("✗ Failed to start IPC server")
        return 1
    
    print(f"✓ IPC server started on port {ipc_server.get_port()}")
    
    # Register this instance
    port = ipc_server.get_port()
    if singleton_manager.register_instance(port):
        print(f"✓ Registered singleton instance with IPC port {port}")
    else:
        print("✗ Failed to register singleton instance")
        ipc_server.stop()
        return 1
    
    # Set up activation handler
    activation_count = [0]  # Use list for mutable reference
    
    def handle_activation():
        activation_count[0] += 1
        print(f"\n🔔 Activation request #{activation_count[0]} received!")
        print("   In a real application, this would bring the window to the foreground")
        
        # Simulate window activation
        window_activator = get_window_activator()
        print("   Window activator ready:", window_activator is not None)
    
    # Connect activation handler
    ipc_server.activation_requested.connect(handle_activation)
    
    print("\n" + "=" * 40)
    print("Application is now running!")
    print("Try running this script again in another terminal")
    print("to see the singleton behavior in action.")
    print("Press Ctrl+C to exit")
    print("=" * 40)
    
    try:
        # Keep the application running
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    
    finally:
        # Clean up
        print("Cleaning up...")
        ipc_server.stop()
        singleton_manager.cleanup()
        print("✓ Cleanup completed")
    
    return 0


def test_ipc_communication():
    """Test IPC communication functionality"""
    print("\nTesting IPC Communication")
    print("-" * 30)
    
    # Start a test server
    server = IPCServer()
    if not server.start():
        print("✗ Failed to start test server")
        return
    
    port = server.get_port()
    print(f"✓ Test server started on port {port}")
    
    try:
        # Test ping
        print("Testing ping...")
        success = IPCClient.ping_server('127.0.0.1', port, timeout=2.0)
        print(f"  Ping result: {'✓ Success' if success else '✗ Failed'}")
        
        # Test activation request
        print("Testing activation request...")
        success = IPCClient.send_activation_request('127.0.0.1', port, timeout=2.0)
        print(f"  Activation result: {'✓ Success' if success else '✗ Failed'}")
        
    finally:
        server.stop()
        print("✓ Test server stopped")


def show_help():
    """Show help information"""
    print("VidTanium Singleton Demo")
    print("=" * 40)
    print("Usage:")
    print("  python demo_singleton.py [command]")
    print()
    print("Commands:")
    print("  run     - Run the singleton demo (default)")
    print("  test    - Test IPC communication")
    print("  help    - Show this help message")
    print()
    print("Examples:")
    print("  python demo_singleton.py")
    print("  python demo_singleton.py run")
    print("  python demo_singleton.py test")


def main():
    """Main function"""
    command = sys.argv[1] if len(sys.argv) > 1 else "run"
    
    if command == "help":
        show_help()
        return 0
    elif command == "test":
        test_ipc_communication()
        return 0
    elif command == "run":
        return simulate_application()
    else:
        print(f"Unknown command: {command}")
        print("Use 'python demo_singleton.py help' for usage information")
        return 1


if __name__ == "__main__":
    sys.exit(main())

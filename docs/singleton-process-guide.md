# Singleton Process Management Guide

VidTanium includes robust singleton process functionality that prevents multiple instances of the application from running simultaneously. When a user attempts to launch the application while another instance is already running, the existing window is automatically brought to the foreground.

## Overview

The singleton system consists of several components working together:

- **Singleton Manager**: Core detection and management of application instances
- **IPC Server**: Inter-process communication for activation requests
- **Window Activator**: Platform-specific window activation functionality
- **Integration Layer**: Seamless integration with the main application

## Features

### ✅ Multi-Platform Support
- **Windows**: Uses named mutexes and Win32 API for window activation
- **macOS**: Uses file locking and AppleScript for application activation
- **Linux**: Uses file locking with wmctrl/xdotool for window management

### ✅ Robust Detection
- File-based locking with process validation
- Automatic cleanup of stale lock files from crashed processes
- Multiple detection mechanisms for reliability

### ✅ Window Activation
- Brings existing window to foreground when duplicate launch is attempted
- Handles minimized, hidden, and background windows
- Platform-specific activation methods with fallbacks

### ✅ Inter-Process Communication
- Socket-based IPC for activation requests
- Configurable timeouts and error handling
- Extensible message system for future features

### ✅ Edge Case Handling
- Crashed process detection and cleanup
- Permission issues and fallback behaviors
- Network drive compatibility
- User session isolation options

## How It Works

### 1. Application Startup
```
User launches VidTanium
         ↓
Check for existing instances
         ↓
    ┌─────────────┐         ┌─────────────┐
    │ No instance │         │ Instance    │
    │ found       │         │ found       │
    └─────────────┘         └─────────────┘
         ↓                       ↓
Register new instance    Send activation request
         ↓                       ↓
Start IPC server        Activate existing window
         ↓                       ↓
Continue startup             Exit gracefully
```

### 2. Instance Detection
The system uses multiple detection methods:

1. **File Lock**: Creates a lock file with process information
2. **Process Validation**: Verifies the process is still running
3. **IPC Check**: Tests if the instance responds to communication

### 3. Window Activation
When an existing instance is found:

1. **IPC Request**: Send activation message to existing instance
2. **Signal Processing**: Existing instance receives activation signal
3. **Window Management**: Platform-specific window activation
4. **User Feedback**: Confirmation of successful activation

## Configuration

### Command Line Options

```bash
# Allow multiple instances (disable singleton)
python main.py --allow-multiple

# Normal operation (singleton enabled)
python main.py
```

### Settings Configuration

The singleton behavior can be configured through the application settings:

```json
{
  "singleton": {
    "enabled": true,
    "user_specific": true,
    "ipc_timeout": 5.0,
    "activation_delay": 100
  }
}
```

## API Reference

### SingletonManager

Main class for singleton functionality:

```python
from src.core.singleton_manager import get_singleton_manager

# Get singleton manager
manager = get_singleton_manager("VidTanium", user_specific=True)

# Check for existing instances
is_running, instance_info = manager.is_another_instance_running()

# Register this instance
success = manager.register_instance(ipc_port=45000)

# Try to activate existing instance
if instance_info:
    success = manager.try_activate_existing(instance_info)

# Clean up
manager.cleanup()
```

### IPCServer

Inter-process communication server:

```python
from src.core.ipc_server import IPCServer

# Create and start server
server = IPCServer()
server.start()

# Connect to activation signals
server.activation_requested.connect(handle_activation)

# Stop server
server.stop()
```

### WindowActivator

Platform-specific window activation:

```python
from src.core.window_activator import get_window_activator

# Get window activator
activator = get_window_activator()

# Activate main window
success = activator.show_and_raise_window(main_window)

# Activate with delay (useful for Qt applications)
activator.activate_with_delay(main_window, delay_ms=100)
```

## Testing

### Running Tests

```bash
# Run singleton tests
python -m pytest tests/core/test_singleton_manager.py -v

# Run all tests
python -m pytest tests/ -v
```

### Manual Testing

Use the demonstration script to test singleton behavior:

```bash
# Run the demo
python demo_singleton.py

# In another terminal, run again to see singleton behavior
python demo_singleton.py

# Test IPC communication
python demo_singleton.py test
```

## Troubleshooting

### Common Issues

#### 1. Multiple Instances Still Starting
**Symptoms**: Multiple VidTanium windows open despite singleton
**Solutions**:
- Check if `--allow-multiple` flag is being used
- Verify file permissions in lock directory
- Check system logs for singleton errors

#### 2. Window Not Activating
**Symptoms**: Existing instance detected but window doesn't come to front
**Solutions**:
- Check platform-specific dependencies (wmctrl, xdotool on Linux)
- Verify window manager compatibility
- Check application logs for activation errors

#### 3. Stale Lock Files
**Symptoms**: Cannot start application after crash
**Solutions**:
- Lock files are automatically cleaned up
- Manually remove `~/.vidtanium/locks/` if needed
- Check process permissions

### Debug Mode

Enable debug logging to troubleshoot singleton issues:

```bash
python main.py --debug
```

Look for log entries containing:
- "Singleton"
- "IPC"
- "Window activation"

### Platform-Specific Notes

#### Windows
- Requires appropriate permissions for named mutex creation
- UAC may affect cross-session singleton behavior
- Windows Defender may interfere with IPC communication

#### macOS
- May require accessibility permissions for window activation
- Sandboxed applications have limited IPC capabilities
- AppleScript execution may be restricted

#### Linux
- Requires X11 or Wayland display server
- Install `wmctrl` or `xdotool` for better window management
- Different desktop environments may behave differently

## Security Considerations

### IPC Security
- IPC server only listens on localhost (127.0.0.1)
- No sensitive data transmitted over IPC
- Timeout mechanisms prevent hanging connections

### File System Security
- Lock files created with appropriate permissions
- User-specific lock directories by default
- No sensitive information stored in lock files

### Process Security
- Process validation prevents PID reuse attacks
- Safe cleanup of resources on exit
- No elevation of privileges required

## Future Enhancements

Planned improvements for the singleton system:

1. **Enhanced IPC**: Support for more message types and data transfer
2. **Better Integration**: Deeper integration with system tray and notifications
3. **Configuration UI**: Graphical configuration of singleton behavior
4. **Advanced Activation**: Support for bringing specific windows to front
5. **Session Management**: Better handling of multiple user sessions

## Contributing

When contributing to the singleton functionality:

1. **Test Thoroughly**: Test on all supported platforms
2. **Handle Errors**: Provide graceful fallbacks for all error conditions
3. **Document Changes**: Update this guide and code documentation
4. **Maintain Compatibility**: Ensure backward compatibility with existing behavior

## License

The singleton process management system is part of VidTanium and is subject to the same license terms as the main application.

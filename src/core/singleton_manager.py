"""
Singleton Process Manager for VidTanium

Provides robust singleton process functionality to prevent multiple instances
of the application from running simultaneously. Includes cross-platform
support and inter-process communication for window activation.
"""

import os
import sys
import time
import json
import socket
import psutil
import platform
import tempfile
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from loguru import logger

# Import fcntl only on Unix systems
def _try_fcntl_lock(fd: int, operation: str) -> bool:
    """Try to apply fcntl lock, return True if successful"""
    try:
        import fcntl
        if operation == "exclusive":
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # 
        elif operation == "unlock":
            fcntl.flock(fd, fcntl.LOCK_UN)  # 
        return True
    except ImportError:
        # fcntl not available on Windows
        return False
    except (OSError, IOError):
        # Lock operation failed
        return False


@dataclass
class InstanceInfo:
    """Information about a running application instance"""
    pid: int
    start_time: float
    ipc_port: Optional[int] = None
    user: Optional[str] = None
    lock_file: Optional[str] = None


class SingletonError(Exception):
    """Base exception for singleton-related errors"""
    pass


class SingletonBase(ABC):
    """Abstract base class for platform-specific singleton implementations"""
    
    @abstractmethod
    def is_another_instance_running(self) -> Tuple[bool, Optional[InstanceInfo]]:
        """Check if another instance is running"""
        pass
    
    @abstractmethod
    def register_instance(self, ipc_port: Optional[int] = None) -> bool:
        """Register this instance as the active one"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up singleton resources"""
        pass
    
    @abstractmethod
    def try_activate_existing(self, instance_info: InstanceInfo) -> bool:
        """Try to activate an existing instance"""
        pass


class UnixSingleton(SingletonBase):
    """Unix-based singleton implementation using file locks"""
    
    def __init__(self, app_name: str, user_specific: bool = True) -> None:
        self.app_name = app_name
        self.user_specific = user_specific
        self.lock_file_path = self._get_lock_file_path()
        self.lock_file_handle: Optional[int] = None
        self.instance_info: Optional[InstanceInfo] = None
        
    def _get_lock_file_path(self) -> Path:
        """Get the path for the lock file"""
        if self.user_specific:
            # User-specific lock file
            lock_dir = Path.home() / ".vidtanium" / "locks"
        else:
            # System-wide lock file
            lock_dir = Path(tempfile.gettempdir()) / "vidtanium"
        
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir / f"{self.app_name}.lock"
    
    def _read_lock_file(self) -> Optional[InstanceInfo]:
        """Read instance information from lock file"""
        try:
            if not self.lock_file_path.exists():
                return None
                
            with open(self.lock_file_path, 'r') as f:
                data = json.load(f)
                
            return InstanceInfo(
                pid=data['pid'],
                start_time=data['start_time'],
                ipc_port=data.get('ipc_port'),
                user=data.get('user'),
                lock_file=str(self.lock_file_path)
            )
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Failed to read lock file: {e}")
            return None
    
    def _write_lock_file(self, ipc_port: Optional[int] = None) -> None:
        """Write instance information to lock file"""
        data = {
            'pid': os.getpid(),
            'start_time': time.time(),
            'ipc_port': ipc_port,
            'user': os.getenv('USER') or os.getenv('USERNAME'),
            'app_name': self.app_name
        }
        
        with open(self.lock_file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        try:
            process = psutil.Process(pid)
            # Check if it's actually our application
            cmdline = process.cmdline()
            return any('vidtanium' in arg.lower() or 'main.py' in arg for arg in cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def is_another_instance_running(self) -> Tuple[bool, Optional[InstanceInfo]]:
        """Check if another instance is running"""
        instance_info = self._read_lock_file()
        
        if not instance_info:
            return False, None
        
        # Check if the process is still running
        if not self._is_process_running(instance_info.pid):
            logger.info(f"Found stale lock file for PID {instance_info.pid}, cleaning up")
            try:
                self.lock_file_path.unlink()
            except OSError as e:
                logger.warning(f"Failed to remove stale lock file: {e}")
            return False, None
        
        # Check if it's not ourselves (in case of restart)
        if instance_info.pid == os.getpid():
            return False, None
        
        logger.info(f"Found running instance: PID {instance_info.pid}")
        return True, instance_info
    
    def register_instance(self, ipc_port: Optional[int] = None) -> bool:
        """Register this instance as the active one"""
        try:
            # Try to acquire exclusive lock
            self.lock_file_handle = os.open(self.lock_file_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)

            # Use fcntl locking if available (Unix systems)
            if not _try_fcntl_lock(self.lock_file_handle, "exclusive"):
                # If fcntl locking failed, we might be on Windows or lock is held
                # On Windows, we rely on the file creation for basic locking
                pass

            # Write instance information
            self._write_lock_file(ipc_port)

            self.instance_info = InstanceInfo(
                pid=os.getpid(),
                start_time=time.time(),
                ipc_port=ipc_port,
                lock_file=str(self.lock_file_path)
            )

            logger.info(f"Successfully registered instance with PID {os.getpid()}")
            return True

        except (OSError, IOError) as e:
            logger.error(f"Failed to register instance: {e}")
            if self.lock_file_handle:
                try:
                    os.close(self.lock_file_handle)
                except OSError:
                    pass
                self.lock_file_handle = None
            return False
    
    def cleanup(self) -> None:
        """Clean up singleton resources"""
        if self.lock_file_handle:
            try:
                # Try to unlock using fcntl if available
                _try_fcntl_lock(self.lock_file_handle, "unlock")
                os.close(self.lock_file_handle)
            except OSError as e:
                logger.warning(f"Error releasing lock: {e}")
            finally:
                self.lock_file_handle = None
        
        try:
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
                logger.debug("Removed lock file")
        except OSError as e:
            logger.warning(f"Failed to remove lock file: {e}")
    
    def try_activate_existing(self, instance_info: InstanceInfo) -> bool:
        """Try to activate an existing instance via IPC"""
        if not instance_info.ipc_port:
            logger.warning("No IPC port available for existing instance")
            return False
        
        try:
            # Try to connect to the existing instance
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)  # 5 second timeout
            sock.connect(('127.0.0.1', instance_info.ipc_port))
            
            # Send activation message
            message = json.dumps({'action': 'activate', 'timestamp': time.time()})
            sock.send(message.encode('utf-8'))
            
            # Wait for response
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            
            result = json.loads(response)
            success = result.get('success', False)
            
            if success:
                logger.info("Successfully activated existing instance")
            else:
                logger.warning(f"Failed to activate existing instance: {result.get('error', 'Unknown error')}")
            
            return bool(success)
            
        except (socket.error, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to communicate with existing instance: {e}")
            return False


class WindowsSingleton(UnixSingleton):
    """Windows-specific singleton implementation"""
    
    def __init__(self, app_name: str, user_specific: bool = True) -> None:
        super().__init__(app_name, user_specific)
        self.mutex_name = f"Global\\VidTanium_{app_name}" if not user_specific else f"Local\\VidTanium_{app_name}_{os.getenv('USERNAME', 'user')}"
        self.mutex_handle = None
    
    def register_instance(self, ipc_port: Optional[int] = None) -> bool:
        """Register instance using both mutex and file lock"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Try to create named mutex
            kernel32 = ctypes.windll.kernel32
            self.mutex_handle = kernel32.CreateMutexW(None, True, self.mutex_name)
            
            if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                logger.info("Mutex already exists, another instance is running")
                return False
            
            # Also use file-based locking as backup
            return super().register_instance(ipc_port)
            
        except ImportError:
            logger.warning("Windows-specific APIs not available, falling back to file locking")
            return super().register_instance(ipc_port)
        except Exception as e:
            logger.error(f"Failed to create Windows mutex: {e}")
            return super().register_instance(ipc_port)
    
    def cleanup(self) -> None:
        """Clean up Windows-specific resources"""
        if self.mutex_handle:
            self._cleanup_mutex()
        
        super().cleanup()
    
    def _cleanup_mutex(self) -> None:
        """Clean up Windows mutex handle"""
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.ReleaseMutex(self.mutex_handle)
            kernel32.CloseHandle(self.mutex_handle)
        except ImportError:
            logger.warning("Windows-specific APIs not available for cleanup")
        except Exception as e:
            logger.warning(f"Error releasing Windows mutex: {e}")
        finally:
            self.mutex_handle = None


class SingletonManager:
    """Main singleton manager that provides a unified interface"""
    
    def __init__(self, app_name: str = "VidTanium", user_specific: bool = True) -> None:
        self.app_name = app_name
        self.user_specific = user_specific
        self._implementation = self._create_implementation()
        self._cleanup_registered = False
    
    def _create_implementation(self) -> SingletonBase:
        """Create platform-specific singleton implementation"""
        system = platform.system().lower()
        
        if system == "windows":
            return WindowsSingleton(self.app_name, self.user_specific)
        else:
            # Unix-like systems (Linux, macOS)
            return UnixSingleton(self.app_name, self.user_specific)
    
    def is_another_instance_running(self) -> Tuple[bool, Optional[InstanceInfo]]:
        """Check if another instance is running"""
        return self._implementation.is_another_instance_running()
    
    def register_instance(self, ipc_port: Optional[int] = None) -> bool:
        """Register this instance as the active one"""
        success = self._implementation.register_instance(ipc_port)
        
        if success and not self._cleanup_registered:
            # Register cleanup handler
            import atexit
            atexit.register(self.cleanup)
            self._cleanup_registered = True
        
        return success
    
    def try_activate_existing(self, instance_info: InstanceInfo) -> bool:
        """Try to activate an existing instance"""
        return self._implementation.try_activate_existing(instance_info)
    
    def cleanup(self) -> None:
        """Clean up singleton resources"""
        self._implementation.cleanup()


# Global singleton manager instance
_singleton_manager: Optional[SingletonManager] = None


def get_singleton_manager(app_name: str = "VidTanium", user_specific: bool = True) -> SingletonManager:
    """Get the global singleton manager instance"""
    global _singleton_manager
    if _singleton_manager is None:
        _singleton_manager = SingletonManager(app_name, user_specific)
    return _singleton_manager

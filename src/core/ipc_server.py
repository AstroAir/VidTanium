"""
Inter-Process Communication Server for VidTanium

Handles communication between multiple application instances for
window activation and other singleton-related operations.
"""

import json
import socket
import threading
import time
from typing import Optional, Callable, Dict, Any
from loguru import logger
from PySide6.QtCore import QObject, Signal, QTimer


class IPCMessage:
    """Represents an IPC message"""
    
    def __init__(self, action: str, data: Optional[Dict[str, Any]] = None, timestamp: Optional[float] = None):
        self.action = action
        self.data = data or {}
        self.timestamp = timestamp or time.time()
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps({
            'action': self.action,
            'data': self.data,
            'timestamp': self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'IPCMessage':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls(
            action=data['action'],
            data=data.get('data', {}),
            timestamp=data.get('timestamp', time.time())
        )


class IPCServer(QObject):
    """IPC server for handling inter-process communication"""
    
    # Qt signals for thread-safe communication with main thread
    activation_requested = Signal()
    message_received = Signal(str, dict)  # action, data
    
    def __init__(self, port: Optional[int] = None, host: str = '127.0.0.1'):
        super().__init__()
        self.host = host
        self.port = port or self._find_available_port()
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.server_thread: Optional[threading.Thread] = None
        self.client_handlers: list = []
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {
            'activate': self._handle_activate_message,
            'ping': self._handle_ping_message,
        }
    
    def _find_available_port(self, start_port: int = 45000, max_attempts: int = 100) -> int:
        """Find an available port for the IPC server"""
        for port in range(start_port, start_port + max_attempts):
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.bind((self.host, port))
                test_socket.close()
                return port
            except OSError:
                continue
        
        raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")
    
    def start(self) -> bool:
        """Start the IPC server"""
        if self.running:
            logger.warning("IPC server is already running")
            return True
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            logger.info(f"IPC server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}")
            self.cleanup()
            return False
    
    def stop(self) -> None:
        """Stop the IPC server"""
        if not self.running:
            return
        
        self.running = False
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.warning(f"Error closing server socket: {e}")
        
        # Wait for server thread to finish
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2.0)
        
        # Close client connections
        for handler in self.client_handlers[:]:
            try:
                handler.join(timeout=1.0)
            except Exception:
                pass
        
        self.client_handlers.clear()
        logger.info("IPC server stopped")
    
    def cleanup(self) -> None:
        """Clean up server resources"""
        self.stop()
    
    def _server_loop(self) -> None:
        """Main server loop"""
        logger.debug("IPC server loop started")
        
        while self.running:
            try:
                if not self.server_socket:
                    break
                
                # Set timeout to allow periodic checks of running flag
                self.server_socket.settimeout(1.0)
                client_socket, address = self.server_socket.accept()
                
                if not self.running:
                    client_socket.close()
                    break
                
                logger.debug(f"New IPC client connected from {address}")
                
                # Handle client in separate thread
                client_handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_handler.start()
                self.client_handlers.append(client_handler)
                
                # Clean up finished handlers
                self.client_handlers = [h for h in self.client_handlers if h.is_alive()]
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error in server loop: {e}")
                break
        
        logger.debug("IPC server loop ended")
    
    def _handle_client(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle individual client connection"""
        try:
            client_socket.settimeout(10.0)  # 10 second timeout for client operations
            
            # Receive message
            data = client_socket.recv(4096)
            if not data:
                return
            
            message_str = data.decode('utf-8')
            logger.debug(f"Received IPC message from {address}: {message_str}")
            
            try:
                message = IPCMessage.from_json(message_str)
                response = self._process_message(message)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Invalid IPC message from {address}: {e}")
                response = {'success': False, 'error': 'Invalid message format'}
            
            # Send response
            response_str = json.dumps(response)
            client_socket.send(response_str.encode('utf-8'))
            
        except socket.timeout:
            logger.warning(f"Client {address} timed out")
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
    
    def _process_message(self, message: IPCMessage) -> Dict[str, Any]:
        """Process incoming IPC message"""
        handler = self.message_handlers.get(message.action)
        
        if not handler:
            logger.warning(f"Unknown IPC action: {message.action}")
            return {'success': False, 'error': f'Unknown action: {message.action}'}
        
        try:
            return handler(message)
        except Exception as e:
            logger.error(f"Error processing IPC message {message.action}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_activate_message(self, message: IPCMessage) -> Dict[str, Any]:
        """Handle window activation request"""
        logger.info("Received window activation request")
        
        # Emit signal to main thread (thread-safe)
        self.activation_requested.emit()
        self.message_received.emit('activate', message.data)
        
        return {'success': True, 'message': 'Activation request processed'}
    
    def _handle_ping_message(self, message: IPCMessage) -> Dict[str, Any]:
        """Handle ping request"""
        return {'success': True, 'message': 'pong', 'timestamp': time.time()}
    
    def add_message_handler(self, action: str, handler: Callable[[IPCMessage], Dict[str, Any]]) -> None:
        """Add custom message handler"""
        self.message_handlers[action] = handler
        logger.debug(f"Added IPC message handler for action: {action}")
    
    def remove_message_handler(self, action: str) -> None:
        """Remove message handler"""
        if action in self.message_handlers:
            del self.message_handlers[action]
            logger.debug(f"Removed IPC message handler for action: {action}")
    
    def get_port(self) -> int:
        """Get the port the server is listening on"""
        return self.port


class IPCClient:
    """IPC client for sending messages to running instances"""
    
    @staticmethod
    def send_message(host: str, port: int, message: IPCMessage, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Send message to IPC server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            
            # Send message
            message_str = message.to_json()
            sock.send(message_str.encode('utf-8'))
            
            # Receive response
            response_data = sock.recv(4096)
            response_str = response_data.decode('utf-8')
            
            sock.close()
            
            return json.loads(response_str)
            
        except Exception as e:
            logger.error(f"Failed to send IPC message: {e}")
            return None
    
    @staticmethod
    def send_activation_request(host: str, port: int, timeout: float = 5.0) -> bool:
        """Send window activation request"""
        message = IPCMessage('activate')
        response = IPCClient.send_message(host, port, message, timeout)
        
        if response and response.get('success'):
            logger.info("Successfully sent activation request")
            return True
        else:
            logger.warning(f"Failed to send activation request: {response}")
            return False
    
    @staticmethod
    def ping_server(host: str, port: int, timeout: float = 2.0) -> bool:
        """Ping IPC server to check if it's responsive"""
        message = IPCMessage('ping')
        response = IPCClient.send_message(host, port, message, timeout)
        
        return response is not None and response.get('success', False)

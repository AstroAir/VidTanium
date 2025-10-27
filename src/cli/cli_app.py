"""
CLI Application Module
Main CLI application class for VidTanium
"""

import sys
import signal
import argparse
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from src.app.settings import Settings
from src.core.downloader import DownloadManager
from .commands import CommandHandler
from .ui_components import TerminalUI, InteractiveTerminal
from .i18n_cli import init_cli_i18n, tr


class CLIApplication:
    """Main CLI application class"""
    
    def __init__(self, config_dir: Optional[str] = None, cli_args: Optional[argparse.Namespace] = None) -> None:
        """
        Initialize CLI application

        Args:
            config_dir: Configuration directory path
            cli_args: Parsed command-line arguments
        """
        self.config_dir = config_dir
        self.cli_args = cli_args or argparse.Namespace()
        self.settings: Optional[Settings] = None
        self.download_manager: Optional[DownloadManager] = None
        self.command_handler: Optional[CommandHandler] = None
        self.terminal_ui: Optional[TerminalUI] = None
        self.interactive_terminal: Optional[InteractiveTerminal] = None
        self.running = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("CLI Application initialized")
    
    def initialize(self) -> bool:
        """
        Initialize all components
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize i18n
            init_cli_i18n()
            
            # Initialize settings
            self.settings = Settings(self.config_dir, cli_args=self.cli_args)
            
            # Initialize download manager
            self.download_manager = DownloadManager(self.settings)

            # Start the download manager
            self.download_manager.start()
            logger.debug("Download manager started")

            # Initialize terminal UI
            self.terminal_ui = TerminalUI()

            # Initialize interactive terminal
            self.interactive_terminal = InteractiveTerminal()

            # Initialize command handler
            self.command_handler = CommandHandler(
                self.download_manager,
                self.settings,
                self.terminal_ui
            )

            logger.info("CLI Application components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize CLI application: {e}", exc_info=True)
            return False
    
    def run(self) -> int:
        """
        Run the CLI application

        Returns:
            int: Exit code
        """
        if not self.initialize():
            logger.error("Initialization failed")
            return 1

        # Ensure components are initialized
        if not self.terminal_ui or not self.command_handler:
            logger.error("Required components not initialized")
            return 1

        self.running = True

        try:
            # Display welcome message
            self.terminal_ui.display_welcome()

            # Execute command based on CLI arguments
            return self._execute_command()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            if self.terminal_ui:
                self.terminal_ui.display_info(tr("cli.messages.interrupted"))
            return 130  # Standard exit code for SIGINT

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            if self.terminal_ui:
                self.terminal_ui.display_error(tr("cli.errors.unexpected", error=str(e)))
            return 1

        finally:
            self.shutdown()
    
    def _execute_command(self) -> int:
        """
        Execute command based on CLI arguments

        Returns:
            int: Exit code
        """
        # Ensure components are available
        if not self.command_handler or not self.terminal_ui or not self.interactive_terminal:
            logger.error("Required components not initialized")
            return 1

        # Check if URL is provided for direct download
        if hasattr(self.cli_args, 'url') and self.cli_args.url:
            output = getattr(self.cli_args, 'output_dir', None)
            return self.command_handler.download(self.cli_args.url, output)

        # Interactive mode - prompt for URL
        self.terminal_ui.display_info(tr("cli.messages.no_command"))
        self.terminal_ui.display_info("Enter a video URL to download, or press Ctrl+C to exit.")

        try:
            url = self.interactive_terminal.prompt_url()

            if url:
                output = getattr(self.cli_args, 'output_dir', None)
                return self.command_handler.download(url, output)
            else:
                self.terminal_ui.display_info("No URL provided. Exiting.")
                return 0

        except KeyboardInterrupt:
            self.terminal_ui.display_info("\nExiting...")
            return 0
    
    def shutdown(self) -> None:
        """Shutdown the application gracefully"""
        if not self.running:
            return

        logger.info("Shutting down CLI application")
        self.running = False

        try:
            # Cleanup interactive terminal
            if self.interactive_terminal:
                self.interactive_terminal.cleanup()

            # Stop download manager
            if self.download_manager:
                self.download_manager.stop()

            # Display goodbye message
            if self.terminal_ui:
                self.terminal_ui.display_info(tr("cli.messages.goodbye"))

            logger.info("CLI Application shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """
        Handle system signals
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}")
        self.shutdown()
        sys.exit(128 + signum)


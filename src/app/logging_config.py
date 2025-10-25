"""
Unified logging configuration for VidTanium application.
This module ensures all logging uses loguru with consistent formatting.
"""

import logging
import sys
from loguru import logger
from pathlib import Path
from typing import Optional

# Configure loguru with consistent format
LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def configure_logging(log_file: Optional[str] = None,
                      log_level: str = "DEBUG",
                      enable_console: bool = True) -> None:
    """
    Configure loguru logging for the entire application.

    Args:
        log_file: Path to log file (optional)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_console: Whether to log to console
    """
    # Remove default handler
    logger.remove()

    # Add console handler if enabled
    if enable_console:
        logger.add(
            sys.stderr,
            format=LOGURU_FORMAT,
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format=LOGURU_FORMAT,
            level=log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )

    logger.info(f"Logging configured with level: {log_level}")


def get_logger(name: Optional[str] = None) -> None:
    """
    Get a logger instance with the specified name.
    This ensures all modules use the same loguru configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        loguru.Logger: Configured logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger


# Configure standard library logging to use loguru


class InterceptHandler(logging.Handler):
    """
    Intercepts standard library logging and routes to loguru.
    This ensures all logging (including third-party libraries) uses consistent format.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level: str = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame = sys._getframe(6)
        depth = 6
        while frame and frame.f_code.co_filename == __file__:
            next_frame = frame.f_back
            if next_frame is None:
                break
            frame = next_frame
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage())


def setup_standard_logging_intercept() -> None:
    """Setup interception of standard library logging."""

    # Remove all existing handlers
    logging.getLogger().handlers = []

    # Add our custom handler
    logging.getLogger().addHandler(InterceptHandler())
    logging.getLogger().setLevel(logging.DEBUG)

    # Set level for common third-party loggers
    for name in ["requests", "urllib3", "asyncio"]:
        logging.getLogger(name).setLevel(logging.WARNING)


# Auto-configure when imported
_logging_configured = False


def ensure_logging_configured() -> None:
    """Ensure logging is configured exactly once."""
    global _logging_configured
    if not _logging_configured:
        configure_logging()
        setup_standard_logging_intercept()
        _logging_configured = True


# Configure on import
ensure_logging_configured()

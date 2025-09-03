"""
VidTanium Core Module
Core functionality for video downloading and processing with enhanced error handling
"""

from .downloader import DownloadManager
from .url_extractor import URLExtractor
from .media_processor import MediaProcessor
from .scheduler import TaskScheduler
from .thread_pool import ThreadPoolManager

# Enhanced error handling and analytics
from .exceptions import VidTaniumException, ErrorCategory, ErrorSeverity, ErrorContext
from .error_handler import EnhancedErrorHandler, error_handler
from .retry_manager import IntelligentRetryManager, retry_manager
from .task_state_manager import TaskStateManager, task_state_manager
from .eta_calculator import ETACalculator, ETAResult, ETAAlgorithm
from .bandwidth_monitor import BandwidthMonitor, bandwidth_monitor
from .download_history_manager import DownloadHistoryManager, download_history_manager
from .batch_progress_aggregator import BatchProgressAggregator, batch_progress_aggregator
from .queue_manager import QueueManager, queue_manager
from .smart_prioritization_engine import SmartPrioritizationEngine, smart_prioritization_engine

__all__ = [
    # Core components
    'DownloadManager',
    'URLExtractor',
    'MediaProcessor',
    'TaskScheduler',
    'ThreadPoolManager',

    # Enhanced error handling
    'VidTaniumException',
    'ErrorCategory',
    'ErrorSeverity',
    'ErrorContext',
    'EnhancedErrorHandler',
    'error_handler',
    'IntelligentRetryManager',
    'retry_manager',
    'TaskStateManager',
    'task_state_manager',

    # Analytics and monitoring
    'ETACalculator',
    'ETAResult',
    'ETAAlgorithm',
    'BandwidthMonitor',
    'bandwidth_monitor',
    'DownloadHistoryManager',
    'download_history_manager',
    'BatchProgressAggregator',
    'batch_progress_aggregator',
    'QueueManager',
    'queue_manager',
    'SmartPrioritizationEngine',
    'smart_prioritization_engine'
]


def initialize_systems() -> dict:
    """Initialize all systems with proper dependencies"""
    # Initialize error handler with retry manager
    retry_manager.error_handler = error_handler

    # Start bandwidth monitoring
    bandwidth_monitor.start_monitoring()

    # Initialize global instances
    return {
        'error_handler': error_handler,
        'retry_manager': retry_manager,
        'task_state_manager': task_state_manager,
        'bandwidth_monitor': bandwidth_monitor,
        'download_history_manager': download_history_manager,
        'batch_progress_aggregator': batch_progress_aggregator,
        'queue_manager': queue_manager,
        'smart_prioritization_engine': smart_prioritization_engine
    }
"""
CLI Commands Module
Command handlers for CLI operations
"""

import time
import threading
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from src.core.downloader import DownloadManager, DownloadTask, TaskStatus, TaskPriority
from src.core.analyzer import MediaAnalyzer
from src.core.event_dispatcher import EventType, Event
from src.app.settings import Settings
from .ui_components import TerminalUI, ProgressDisplay, LiveProgressDisplay, InteractiveTerminal
from .i18n_cli import tr


class CommandHandler:
    """Handler for CLI commands"""
    
    def __init__(
        self,
        download_manager: DownloadManager,
        settings: Settings,
        terminal_ui: TerminalUI
    ) -> None:
        """
        Initialize command handler
        
        Args:
            download_manager: Download manager instance
            settings: Settings instance
            terminal_ui: Terminal UI instance
        """
        self.download_manager = download_manager
        self.settings = settings
        self.ui = terminal_ui
        
        logger.debug("CommandHandler initialized")
    
    def analyze_url(self, url: str) -> int:
        """
        Analyze URL and display metadata
        
        Args:
            url: URL to analyze
            
        Returns:
            int: Exit code
        """
        # Placeholder - will be implemented in Phase 5
        logger.info(f"Analyzing URL: {url}")
        self.ui.display_info(tr("cli.commands.analyze.started", url=url))
        return 0
    
    def download(self, url: str, output: Optional[str] = None) -> int:
        """
        Download video from URL

        Args:
            url: Video URL
            output: Optional output file path

        Returns:
            int: Exit code
        """
        try:
            logger.info(f"Starting download from URL: {url}")
            self.ui.display_info(tr("cli.commands.download.started", url=url))

            # Step 1: Analyze URL
            self.ui.display_info(tr("cli.commands.analyze.started", url=url))
            analyzer = MediaAnalyzer(settings=self.settings.settings)
            analysis_result = analyzer.analyze_url(url)

            if not analysis_result.get("success"):
                error_msg = analysis_result.get("error", "Unknown error")
                self.ui.display_error(tr("cli.commands.analyze.failed", error=error_msg))
                return 1

            self.ui.display_success(tr("cli.commands.analyze.completed"))

            # Display analysis info
            segment_count = analysis_result.get("segment_count", 0)
            duration = analysis_result.get("total_duration", 0)
            encryption = analysis_result.get("encryption", "none")

            self.ui.display_info(f"  Segments: {segment_count}")
            self.ui.display_info(f"  Duration: {duration:.2f}s")
            self.ui.display_info(f"  Encryption: {encryption}")

            # Step 2: Determine output path
            if not output:
                output_dir = self.settings.get("download", "output_dir", str(Path.home() / "Downloads"))
                output = str(Path(output_dir) / f"video_{int(time.time())}.mp4")

            self.ui.display_info(f"  Output: {output}")

            # Step 3: Create download task
            task = DownloadTask(
                name=f"CLI Download - {url[:50]}...",
                base_url=analysis_result.get("base_url", url),
                key_url=analysis_result.get("key_url"),
                segments=segment_count,
                output_file=output,
                settings=self.settings,
                priority=TaskPriority.HIGH
            )

            # Step 4: Add task to download manager
            task_id = self.download_manager.add_task(task)
            logger.info(f"Created download task: {task_id}")

            # Step 5: Monitor progress
            return self._monitor_download(task_id, task)

        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            self.ui.display_error(tr("cli.commands.download.failed", error=str(e)))
            return 1
    
    def list_tasks(self, filter_status: Optional[str] = None) -> int:
        """
        List download tasks
        
        Args:
            filter_status: Optional status filter
            
        Returns:
            int: Exit code
        """
        # Placeholder - will be implemented in Phase 5
        logger.info(f"Listing tasks with filter: {filter_status}")
        self.ui.display_info(tr("cli.commands.list.started"))
        return 0
    
    def pause_task(self, task_id: str) -> int:
        """
        Pause a download task
        
        Args:
            task_id: Task identifier
            
        Returns:
            int: Exit code
        """
        # Placeholder - will be implemented in Phase 5
        logger.info(f"Pausing task: {task_id}")
        return 0
    
    def resume_task(self, task_id: str) -> int:
        """
        Resume a paused task
        
        Args:
            task_id: Task identifier
            
        Returns:
            int: Exit code
        """
        # Placeholder - will be implemented in Phase 5
        logger.info(f"Resuming task: {task_id}")
        return 0
    
    def cancel_task(self, task_id: str) -> int:
        """
        Cancel a download task
        
        Args:
            task_id: Task identifier
            
        Returns:
            int: Exit code
        """
        # Placeholder - will be implemented in Phase 5
        logger.info(f"Canceling task: {task_id}")
        return 0
    
    def show_settings(self) -> int:
        """
        Display current settings
        
        Returns:
            int: Exit code
        """
        # Placeholder - will be implemented in Phase 5
        logger.info("Displaying settings")
        return 0
    
    def update_setting(self, key: str, value: Any) -> int:
        """
        Update a setting value

        Args:
            key: Setting key
            value: New value

        Returns:
            int: Exit code
        """
        # Placeholder - will be implemented in Phase 5
        logger.info(f"Updating setting {key} = {value}")
        return 0

    def _monitor_download(self, task_id: str, task: DownloadTask) -> int:
        """
        Monitor download progress with real-time updates and ESC cancellation

        Args:
            task_id: Task identifier
            task: Download task object

        Returns:
            int: Exit code
        """
        live_display: Optional[LiveProgressDisplay] = None
        interactive_terminal: Optional[InteractiveTerminal] = None
        event_subscribed = False

        try:
            # Create live progress display
            live_display = LiveProgressDisplay(update_hz=20)
            live_display.start()

            # Create interactive terminal for keyboard detection
            interactive_terminal = InteractiveTerminal()

            # Flag to track completion
            completion_event = threading.Event()
            final_status = {"code": 0, "status": TaskStatus.RUNNING}

            # Event callback for progress updates
            def on_progress_update(event: Event) -> None:
                """Handle progress update events"""
                if event.data.get("task_id") != task_id:
                    return

                progress_data = event.data.get("progress", {})

                # Update live display
                live_display.update({
                    "task_name": task.name,
                    "total": task.segments or 100,
                    "completed": progress_data.get("completed", 0),
                    "speed": progress_data.get("speed", 0),
                    "downloaded_bytes": progress_data.get("downloaded_bytes", 0),
                    "eta": progress_data.get("estimated_time")
                })

            # Event callback for status changes
            def on_status_changed(event: Event) -> None:
                """Handle status change events"""
                if event.data.get("task_id") != task_id:
                    return

                new_status = event.data.get("new_status")

                if new_status == TaskStatus.COMPLETED:
                    final_status["code"] = 0
                    final_status["status"] = TaskStatus.COMPLETED
                    completion_event.set()
                elif new_status == TaskStatus.FAILED:
                    final_status["code"] = 1
                    final_status["status"] = TaskStatus.FAILED
                    completion_event.set()
                elif new_status == TaskStatus.CANCELED:
                    final_status["code"] = 130
                    final_status["status"] = TaskStatus.CANCELED
                    completion_event.set()

            # ESC key callback
            def on_esc_pressed() -> None:
                """Handle ESC key press"""
                logger.info("ESC key pressed, cancelling download")
                self.download_manager.cancel_task(task_id)

            # Subscribe to events
            self.download_manager.subscribe(EventType.TASK_PROGRESS, on_progress_update, weak=False)
            self.download_manager.subscribe(EventType.TASK_STATUS_CHANGED, on_status_changed, weak=False)
            event_subscribed = True

            # Start keyboard listener
            interactive_terminal.start_keyboard_listener(on_esc_pressed)

            # Initial progress update
            live_display.update({
                "task_name": task.name,
                "total": task.segments or 100,
                "completed": task.progress.get("completed", 0),
                "speed": task.progress.get("speed", 0),
                "downloaded_bytes": task.progress.get("downloaded_bytes", 0),
                "eta": task.progress.get("estimated_time")
            }, force=True)

            # Wait for completion or cancellation
            completion_event.wait()

            # Stop displays
            if live_display:
                live_display.stop()
            if interactive_terminal:
                interactive_terminal.stop_keyboard_listener()

            # Unsubscribe from events
            if event_subscribed:
                self.download_manager.unsubscribe(EventType.TASK_PROGRESS, on_progress_update)
                self.download_manager.unsubscribe(EventType.TASK_STATUS_CHANGED, on_status_changed)

            # Display final message
            if final_status["status"] == TaskStatus.COMPLETED:
                self.ui.display_success(tr("cli.commands.download.completed", name=task.name))
            elif final_status["status"] == TaskStatus.FAILED:
                self.ui.display_error(tr("cli.commands.download.failed", error="Task failed"))
            elif final_status["status"] == TaskStatus.CANCELED:
                self.ui.display_warning(tr("cli.commands.cancel.success", task_id=task_id))

            return final_status["code"]

        except KeyboardInterrupt:
            logger.info("Download interrupted by user (Ctrl+C)")
            self.download_manager.cancel_task(task_id)
            self.ui.display_warning(tr("cli.messages.interrupted"))
            return 130

        except Exception as e:
            logger.error(f"Error monitoring download: {e}", exc_info=True)
            self.ui.display_error(tr("cli.errors.unexpected", error=str(e)))
            return 1

        finally:
            # Cleanup
            if live_display:
                live_display.cleanup()
            if interactive_terminal:
                interactive_terminal.cleanup()


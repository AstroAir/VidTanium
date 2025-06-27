"""
Beautiful Dashboard interface with modern Fluent Design and unified theme
"""
from typing import Dict, Optional, TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QLabel
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPixmap, QPainter, QLinearGradient, QBrush
from qfluentwidgets import (
    ScrollArea, TitleLabel, BodyLabel, StrongBodyLabel,
    ElevatedCardWidget, LineEdit, TextEdit, PrimaryPushButton,
    TransparentToolButton, FluentIcon as FIF, IconWidget, CardWidget,
    SubtitleLabel, CaptionLabel, ProgressRing, InfoBar, InfoBarPosition
)

from ...utils.formatters import format_speed, format_bytes
from ...utils.i18n import tr
from ...utils.theme import VidTaniumTheme, ThemeManager

if TYPE_CHECKING:
    from ...main_window import MainWindow


class DashboardInterface:
    """Beautiful Dashboard interface with modern animations and gradients"""
    
    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.total_tasks_card: Optional[CardWidget] = None
        self.running_tasks_card: Optional[CardWidget] = None
        self.completed_tasks_card: Optional[CardWidget] = None
        self.speed_card: Optional[CardWidget] = None
        self.task_preview_content: Optional[QWidget] = None
        self.main_log_preview: Optional[TextEdit] = None
        self.system_status_labels: Dict[str, BodyLabel] = {}
        
        # Animation timer for dynamic effects
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(2000)  # Update every 2 seconds
    
    def create_interface(self) -> QWidget:
        """Create the beautiful dashboard interface"""
        interface = ScrollArea()
        interface.setWidgetResizable(True)
        interface.setObjectName("dashboard_scroll_area")
        interface.setStyleSheet(f"""
            ScrollArea {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {VidTaniumTheme.BG_SECONDARY}, stop:1 {VidTaniumTheme.BG_PRIMARY});
                border: none;
            }}
        """)

        # Main container with beautiful styling
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)

        # Beautiful hero header
        hero_section = self._create_hero_section()
        main_layout.addWidget(hero_section)

        # Statistics dashboard
        stats_section = self._create_stats_section()
        main_layout.addLayout(stats_section)

        # Content cards section
        content_section = self._create_content_section()
        main_layout.addLayout(content_section)

        interface.setWidget(main_container)
        return interface

    def _create_hero_section(self) -> QWidget:
        """Create beautiful hero section with gradient background"""
        hero_card = CardWidget()
        hero_card.setFixedHeight(160)
        hero_card.setStyleSheet(f"""
            CardWidget {{
                background: {VidTaniumTheme.GRADIENT_HERO};
                border: none;
                border-radius: {VidTaniumTheme.RADIUS_XLARGE};
            }}
        """)
        
        # Add themed shadow effect
        hero_card.setGraphicsEffect(ThemeManager.get_colored_shadow_effect(
            VidTaniumTheme.PRIMARY_BLUE, 50
        ))
        
        layout = QHBoxLayout(hero_card)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)

        # Welcome content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        
        welcome_label = TitleLabel(tr("dashboard.welcome.title"))
        welcome_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE};
                font-size: {VidTaniumTheme.FONT_SIZE_HERO};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD};
                background: transparent;
            }}
        """)
        
        subtitle_label = SubtitleLabel(tr("dashboard.welcome.subtitle"))
        subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
                background: transparent;
            }}
        """)
        
        description_label = BodyLabel(tr("dashboard.welcome.description"))
        description_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE_TERTIARY};
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
                background: transparent;
            }}
        """)
        
        content_layout.addWidget(welcome_label)
        content_layout.addWidget(subtitle_label)
        content_layout.addWidget(description_label)
        content_layout.addStretch()

        # Action buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(12)
        
        new_task_btn = PrimaryPushButton(tr("dashboard.actions.new_download"))
        new_task_btn.setIcon(FIF.ADD)
        new_task_btn.setStyleSheet(f"""
            PrimaryPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: {VidTaniumTheme.RADIUS_MEDIUM};
                color: {VidTaniumTheme.TEXT_WHITE};
                padding: {VidTaniumTheme.SPACE_MD} {VidTaniumTheme.SPACE_XXL};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
            }}
            PrimaryPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
            PrimaryPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.35);
            }}
        """)
        
        batch_btn = PrimaryPushButton(tr("dashboard.actions.batch_import"))
        batch_btn.setIcon(FIF.FOLDER_ADD)
        batch_btn.setStyleSheet(new_task_btn.styleSheet())
        
        buttons_layout.addWidget(new_task_btn)
        buttons_layout.addWidget(batch_btn)
        buttons_layout.addStretch()

        # App icon/logo area
        icon_container = QWidget()
        icon_container.setFixedSize(100, 100)
        icon_container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 50px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        app_icon = IconWidget(FIF.VIDEO)
        app_icon.setFixedSize(60, 60)
        app_icon.setStyleSheet(f"background: transparent; color: {VidTaniumTheme.TEXT_WHITE};")
        icon_layout.addWidget(app_icon, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(content_layout)
        layout.addLayout(buttons_layout)
        layout.addStretch()
        layout.addWidget(icon_container)
        
        return hero_card

    def _create_stats_section(self) -> QHBoxLayout:
        """Create beautiful statistics cards section"""
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        # Create enhanced stats cards with gradients and animations
        self.total_tasks_card = self._create_animated_stats_card(
            tr("dashboard.stats.total_tasks"),
            "0",
            FIF.MENU,
            [VidTaniumTheme.PRIMARY_BLUE, VidTaniumTheme.PRIMARY_PURPLE]
        )
        
        self.running_tasks_card = self._create_animated_stats_card(
            tr("dashboard.stats.active_downloads"),
            "0",
            FIF.DOWNLOAD,
            [VidTaniumTheme.SUCCESS_GREEN, VidTaniumTheme.SUCCESS_LIGHT]
        )
        
        self.completed_tasks_card = self._create_animated_stats_card(
            tr("dashboard.stats.completed"),
            "0",
            FIF.ACCEPT,
            [VidTaniumTheme.ACCENT_CYAN, VidTaniumTheme.ACCENT_GREEN]
        )
        
        self.speed_card = self._create_animated_stats_card(
            tr("dashboard.stats.total_speed"),
            "0 MB/s",
            FIF.SPEED_HIGH,
            [VidTaniumTheme.WARNING_ORANGE, VidTaniumTheme.WARNING_LIGHT]
        )

        stats_layout.addWidget(self.total_tasks_card)
        stats_layout.addWidget(self.running_tasks_card)
        stats_layout.addWidget(self.completed_tasks_card)
        stats_layout.addWidget(self.speed_card)
        
        return stats_layout

    def _create_animated_stats_card(self, title: str, value: str, icon: FIF, gradient_colors: list) -> CardWidget:
        """Create beautiful animated statistics card"""
        card = CardWidget()
        card.setFixedSize(200, 120)
        
        # Apply themed gradient background
        card.setStyleSheet(f"""
            CardWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {gradient_colors[0]}, stop:1 {gradient_colors[1]});
                border: none;
                border-radius: {VidTaniumTheme.RADIUS_LARGE};
            }}
        """)
        
        # Add themed shadow
        card.setGraphicsEffect(ThemeManager.get_shadow_effect(20, 4, 30))
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # Icon and value row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(24, 24)
        icon_widget.setStyleSheet(f"color: {VidTaniumTheme.TEXT_WHITE}; background: transparent;")
        
        value_label = TitleLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE};
                font-size: {VidTaniumTheme.FONT_SIZE_SUBTITLE};
                font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD};
                background: transparent;
            }}
        """)
        
        header_layout.addWidget(icon_widget)
        header_layout.addWidget(value_label)
        header_layout.addStretch()

        # Title label
        title_label = BodyLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {VidTaniumTheme.TEXT_WHITE_SECONDARY};
                font-size: {VidTaniumTheme.FONT_SIZE_BODY};
                background: transparent;
            }}
        """)

        layout.addLayout(header_layout)
        layout.addWidget(title_label)
        layout.addStretch()
        
        # Store reference to value label for updates
        setattr(card, 'value_label', value_label)
        setattr(card, 'title_label', title_label)
        
        return card

    def _create_content_section(self) -> QHBoxLayout:
        """Create content section with task preview and system info"""
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        # Task preview card
        task_preview_card = self._create_task_preview_card()
        content_layout.addWidget(task_preview_card, 2)

        # System status card
        system_card = self._create_system_status_card()
        content_layout.addWidget(system_card, 1)

        return content_layout

    def _create_task_preview_card(self) -> CardWidget:
        """Create beautiful task preview card"""
        card = CardWidget()
        card.setMinimumHeight(300)
        card.setStyleSheet(VidTaniumTheme.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        icon = IconWidget(FIF.HISTORY)
        icon.setFixedSize(20, 20)
        icon.setStyleSheet(f"color: {VidTaniumTheme.PRIMARY_BLUE};")
        
        title = SubtitleLabel(tr("dashboard.recent_tasks.title"))
        title.setStyleSheet(f"""
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD}; 
            color: {VidTaniumTheme.TEXT_PRIMARY};
            font-size: {VidTaniumTheme.FONT_SIZE_HEADING};
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Task preview content
        self.task_preview_content = QWidget()
        preview_layout = QVBoxLayout(self.task_preview_content)
        preview_layout.setSpacing(8)

        # Sample recent tasks (placeholder)
        for i in range(3):
            task_item = self._create_preview_task_item(
                f"Sample Task {i+1}",
                "downloading" if i == 0 else "completed",
                75 if i == 0 else 100
            )
            preview_layout.addWidget(task_item)

        preview_layout.addStretch()
        layout.addWidget(self.task_preview_content)

        return card

    def _create_preview_task_item(self, name: str, status: str, progress: int) -> QWidget:
        """Create a preview task item"""
        item = QWidget()
        item.setFixedHeight(60)
        item.setStyleSheet(f"""
            QWidget {{
                background-color: {VidTaniumTheme.BG_CARD};
                border-radius: {VidTaniumTheme.RADIUS_MEDIUM};
                border: 1px solid {VidTaniumTheme.BORDER_LIGHT};
            }}
            QWidget:hover {{
                background-color: {VidTaniumTheme.BG_CARD_HOVER};
                border-color: {VidTaniumTheme.BORDER_ACCENT};
            }}
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Status icon with themed colors
        status_icons = {
            "downloading": FIF.DOWNLOAD,
            "completed": FIF.ACCEPT,
            "paused": FIF.PAUSE,
            "error": FIF.CLOSE
        }
        
        status_colors = {
            "downloading": VidTaniumTheme.INFO_BLUE,
            "completed": VidTaniumTheme.SUCCESS_GREEN, 
            "paused": VidTaniumTheme.WARNING_ORANGE,
            "error": VidTaniumTheme.ERROR_RED
        }
        
        icon = IconWidget(status_icons.get(status, FIF.INFO))
        icon.setFixedSize(16, 16)
        icon.setStyleSheet(f"color: {status_colors.get(status, VidTaniumTheme.TEXT_SECONDARY)};")

        # Task info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = BodyLabel(name)
        name_label.setStyleSheet(f"""
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD}; 
            color: {VidTaniumTheme.TEXT_PRIMARY};
        """)
        
        status_label = CaptionLabel(f"{status.title()} - {progress}%")
        status_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(status_label)

        # Progress ring for active downloads
        if status == "downloading":
            progress_ring = ProgressRing()
            progress_ring.setFixedSize(24, 24)
            progress_ring.setValue(progress)
            layout.addWidget(progress_ring)

        layout.addWidget(icon)
        layout.addLayout(info_layout)
        layout.addStretch()

        return item

    def _create_system_status_card(self) -> CardWidget:
        """Create beautiful system status card"""
        card = CardWidget()
        card.setMinimumHeight(300)
        card.setStyleSheet(VidTaniumTheme.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        icon = IconWidget(FIF.SETTING)
        icon.setFixedSize(20, 20)
        icon.setStyleSheet(f"color: {VidTaniumTheme.SUCCESS_GREEN};")
        
        title = SubtitleLabel(tr("dashboard.system_status.title"))
        title.setStyleSheet(f"""
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD}; 
            color: {VidTaniumTheme.TEXT_PRIMARY};
            font-size: {VidTaniumTheme.FONT_SIZE_HEADING};
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # System info items
        system_items = [
            ("dashboard.system_status.download_threads", "4 threads"),
            ("dashboard.system_status.temp_files", "12 MB"),
            ("dashboard.system_status.cache_size", "45 MB"),
            ("dashboard.system_status.network_usage", "2.1 MB/s")
        ]

        for key, value in system_items:
            item = self._create_status_item(tr(key), value)
            layout.addWidget(item)

        layout.addStretch()
        
        # Quick actions with themed buttons
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)
        
        clear_cache_btn = PrimaryPushButton(tr("dashboard.actions.clear_cache"))
        clear_cache_btn.setIcon(FIF.BROOM)
        clear_cache_btn.setStyleSheet(VidTaniumTheme.get_button_style("secondary"))
        
        open_settings_btn = PrimaryPushButton(tr("dashboard.actions.open_settings"))
        open_settings_btn.setIcon(FIF.SETTING)
        open_settings_btn.setStyleSheet(VidTaniumTheme.get_button_style("primary"))
        
        actions_layout.addWidget(clear_cache_btn)
        actions_layout.addWidget(open_settings_btn)
        
        layout.addLayout(actions_layout)

        return card

    def _create_status_item(self, label: str, value: str) -> QWidget:
        """Create a system status item"""
        item = QWidget()
        item.setFixedHeight(32)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label_widget = BodyLabel(label)
        label_widget.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY};")
        
        value_widget = StrongBodyLabel(value)
        value_widget.setStyleSheet(f"""
            color: {VidTaniumTheme.TEXT_PRIMARY}; 
            font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};
        """)

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)

        return item

    def _update_animations(self):
        """Update dashboard animations and data"""
        # This method can be used to update real-time data and animations
        # For now, we'll just update some demo values
        pass

    def update_stats(self):
        """Update statistics cards with real data"""
        if not self.main_window or not self.main_window.download_manager:
            return

        try:
            # Get real data from download manager
            tasks = getattr(self.main_window.download_manager, 'tasks', {})
            
            total_tasks = len(tasks)
            running_tasks = sum(1 for task in tasks.values() 
                              if getattr(task, 'status', '') == 'downloading')
            completed_tasks = sum(1 for task in tasks.values() 
                                if getattr(task, 'status', '') == 'completed')

            # Update stats cards using getattr to avoid type issues
            if self.total_tasks_card:
                value_label = getattr(self.total_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(total_tasks))
            
            if self.running_tasks_card:
                value_label = getattr(self.running_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(running_tasks))
            
            if self.completed_tasks_card:
                value_label = getattr(self.completed_tasks_card, 'value_label', None)
                if value_label:
                    value_label.setText(str(completed_tasks))
            
            if self.speed_card:
                value_label = getattr(self.speed_card, 'value_label', None)
                if value_label:
                    # Calculate total speed (placeholder for now)
                    value_label.setText("2.5 MB/s")

        except Exception as e:
            print(f"Error updating dashboard stats: {e}")

    def update_statistics(self) -> None:
        """Update statistics information"""
        if not self.main_window.download_manager:
            return
            
        try:
            download_manager = self.main_window.download_manager
            all_tasks = getattr(download_manager, 'tasks', [])
            
            # Ensure all_tasks is a list
            if not isinstance(all_tasks, list):
                all_tasks = []
            
            total_tasks = len(all_tasks)
            running_tasks = len([t for t in all_tasks if hasattr(t, 'status') and getattr(t, 'status', None) == 'running'])
            completed_tasks = len([t for t in all_tasks if hasattr(t, 'status') and getattr(t, 'status', None) == 'completed'])
            
            # Update cards
            if self.total_tasks_card:
                getattr(self.total_tasks_card, 'value_label').setText(str(total_tasks))
            if self.running_tasks_card:
                getattr(self.running_tasks_card, 'value_label').setText(str(running_tasks))
            if self.completed_tasks_card:
                getattr(self.completed_tasks_card, 'value_label').setText(str(completed_tasks))
            if self.speed_card:
                # Calculate average speed (placeholder)
                getattr(self.speed_card, 'value_label').setText("2.5 MB/s")
                
        except Exception as e:
            print(f"Error updating statistics: {e}")
    def _format_speed(self, speed_bytes_per_sec: float) -> str:
        """Format speed in human-readable format"""
        return format_speed(speed_bytes_per_sec)

    def update_task_preview_original(self) -> None:
        """Update task preview - replaced by newer version"""
        pass
    def update_task_preview(self):
        """Update task preview panel with recent activity - fixed version"""
        try:
            if not self.main_window.download_manager:
                return

            # Get recent tasks
            tasks = getattr(self.main_window.download_manager, 'tasks', {})
            if not isinstance(tasks, dict):
                return

            # Sort tasks by status priority (running first, then recent)
            sorted_tasks = []
            for task_id, task in tasks.items():
                try:
                    status = str(getattr(task, 'status', 'unknown')).lower()
                    priority = 0
                    if status in ['running', 'downloading']:
                        priority = 3
                    elif status == 'paused':
                        priority = 2
                    elif status == 'completed':
                        priority = 1
                    
                    sorted_tasks.append((priority, task_id, task))
                except Exception:
                    continue

            sorted_tasks.sort(key=lambda x: x[0], reverse=True)
            
            # Create preview text (show top 5 tasks)
            preview_text = ""
            for i, (_, task_id, task) in enumerate(sorted_tasks[:5]):
                try:
                    name = getattr(task, 'name', f'Task {task_id[:8]}')
                    status = str(getattr(task, 'status', 'unknown')).lower()
                    
                    # Get progress if available
                    progress_text = ""
                    if hasattr(task, 'progress'):
                        progress = getattr(task, 'progress', {})
                        if isinstance(progress, dict):
                            completed = progress.get('completed', 0)
                            total = progress.get('total', 0)
                            if total > 0:
                                percentage = (completed / total) * 100
                                progress_text = f" ({percentage:.1f}%)"
                    
                    preview_text += f"• {name} - {status.title()}{progress_text}\n"
                except Exception:
                    continue

            # Update main log preview if available
            if self.main_log_preview and preview_text:
                self.main_log_preview.setPlainText(preview_text.strip())

        except Exception as e:
            print(f"Error updating task preview: {e}")
    
    def _create_task_preview_widget(self, task) -> QWidget:
        """Create task preview widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Task status icon
        try:
            task_status = getattr(task, 'status', None)
            if task_status == 'running':
                status_icon = IconWidget(FIF.PLAY)
            else:
                status_icon = IconWidget(FIF.PAUSE)
        except:
            status_icon = IconWidget(FIF.PAUSE)
            
        status_icon.setFixedSize(16, 16)
        layout.addWidget(status_icon)
        
        # Task name
        name_label = BodyLabel(getattr(task, 'name', 'Unknown Task'))
        name_label.setFixedWidth(150)
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Progress info
        if hasattr(task, 'progress'):
            progress_text = f"{task.progress:.1f}%"
        else:
            progress_text = tr("dashboard.task_status.waiting")
        progress_label = BodyLabel(progress_text)
        progress_label.setStyleSheet("color: #666666;")
        layout.addWidget(progress_label)
        
        return widget
    
    def update_system_status(self) -> None:
        """Update system status information"""
        try:
            import psutil
            
            # Update CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if 'cpu' in self.system_status_labels:
                self.system_status_labels['cpu'].setText(f"{cpu_percent:.1f}%")
            
            # Update memory usage
            memory = psutil.virtual_memory()
            memory_gb = memory.used / (1024**3)
            if 'memory' in self.system_status_labels:
                self.system_status_labels['memory'].setText(f"{memory_gb:.1f} GB")
                
        except ImportError:
            # psutil not available, use placeholder values
            pass
        except Exception as e:
            print(f"Error updating system status: {e}")

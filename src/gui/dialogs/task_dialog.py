from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFileDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QProgressDialog, QWidget, QSpacerItem, QSizePolicy,
    QScrollArea, QMenu, QApplication, QCompleter, QSystemTrayIcon, QGraphicsOpacityEffect,
    QButtonGroup, QFrame, QSplitter, QTabWidget, QTextEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QObject, QSettings, QStandardPaths, QStringListModel, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QRect, QPoint, QSize
from PySide6.QtGui import QIcon, QAction, QKeySequence, QValidator, QRegularExpressionValidator, QPixmap, QPainter, QColor, QFont, QFontMetrics, QClipboard
import os
import re
import json
import sys
import threading
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse

from qfluentwidgets import (
    # Buttons
    PushButton, PrimaryPushButton, HyperlinkButton,
    ToolButton, TransparentToolButton,
    # Input Components
    LineEdit, SearchLineEdit, CheckBox, SpinBox, ComboBox, SwitchButton,
    # Cards and Layout
    ElevatedCardWidget, SmoothScrollArea, VBoxLayout,
    # Labels and Text
    TitleLabel, SubtitleLabel, BodyLabel, StrongBodyLabel, CaptionLabel,
    # Icons and Media
    FluentIcon as FIF, IconWidget, PixmapLabel,
    # Navigation and Tabs
    Pivot, PivotItem,
    # Feedback and Progress
    InfoBar, InfoBarPosition, ProgressBar, StateToolTip,
    # Flyouts and Dialogs
    FlyoutView, Flyout, FlyoutAnimationType,
    # Theme and Styling
    Theme, isDarkTheme, setTheme
)

from src.gui.utils.i18n import tr
from src.gui.utils.responsive import ResponsiveWidget, ResponsiveManager
from src.gui.utils.theme import VidTaniumTheme
from src.gui.theme_manager import EnhancedThemeManager
from loguru import logger


class URLValidator(QValidator):
    """Custom URL validator for input fields"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Pattern for basic URL validation
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    def validate(self, input_text: str, pos: int) -> tuple:
        if not input_text:
            return QValidator.State.Intermediate, input_text, pos
        
        if self.url_pattern.match(input_text):
            return QValidator.State.Acceptable, input_text, pos
        elif input_text.startswith(('http', 'https')):
            return QValidator.State.Intermediate, input_text, pos
        else:
            return QValidator.State.Invalid, input_text, pos


class HistoryManager:
    """Manages URL history and auto-completion with enhanced caching"""
    
    def __init__(self):
        self.settings = QSettings("VidTanium", "TaskDialog")
        self.max_history = 50
        self._url_cache = None
        self._output_cache = None
        self._cache_dirty = {"url": True, "output": True}
        
    def get_url_history(self) -> List[str]:
        """Get URL history list with caching"""
        if self._url_cache is None or self._cache_dirty["url"]:
            history = self.settings.value("url_history", [])
            self._url_cache = history if isinstance(history, list) else []
            self._cache_dirty["url"] = False
        return list(self._url_cache.copy())
    
    def add_url(self, url: str):
        """Add URL to history with smart deduplication"""
        if not url or not url.strip():
            return
            
        url = url.strip()
        # Skip if URL is too short or invalid
        if len(url) < 10 or not url.startswith(('http://', 'https://')):
            return
            
        history = self.get_url_history()
        
        # Remove if already exists (case-insensitive)
        for existing_url in history[:]:
            if existing_url.lower() == url.lower():
                history.remove(existing_url)
        
        # Add to beginning
        history.insert(0, url)
        
        # Limit history size
        if len(history) > self.max_history:
            history = history[:self.max_history]
        
        self.settings.setValue("url_history", history)
        self._url_cache = history
        self._cache_dirty["url"] = False
    
    def get_output_history(self) -> List[str]:
        """Get output path history with caching"""
        if self._output_cache is None or self._cache_dirty["output"]:
            history = self.settings.value("output_history", [])
            self._output_cache = history if isinstance(history, list) else []
            self._cache_dirty["output"] = False
        return list(self._output_cache.copy())
    
    def add_output_path(self, path: str):
        """Add output path to history with directory validation"""
        if not path or not path.strip():
            return
            
        path = path.strip()
        # Validate directory exists
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            return
            
        history = self.get_output_history()
        
        if path in history:
            history.remove(path)
        
        history.insert(0, path)
        
        if len(history) > self.max_history:
            history = history[:self.max_history]
        
        self.settings.setValue("output_history", history)
        self._output_cache = history
        self._cache_dirty["output"] = False
    
    def clear_history(self, history_type: str = "all"):
        """Clear history of specified type"""
        if history_type in ("all", "url"):
            self.settings.remove("url_history")
            self._url_cache = []
            self._cache_dirty["url"] = False
            
        if history_type in ("all", "output"):
            self.settings.remove("output_history")
            self._output_cache = []
            self._cache_dirty["output"] = False
    
    def get_frequent_urls(self, limit: int = 5) -> List[str]:
        """Get most frequently used URLs"""
        history = self.get_url_history()
        # For now, return most recent as "frequent"
        # Could be enhanced to track actual usage frequency
        return history[:limit]


class URLAnalyzer:
    """Advanced URL analysis and suggestion system"""
    
    def __init__(self):
        self.common_patterns = {
            'quality': re.compile(r'(\d{3,4}p)', re.IGNORECASE),
            'resolution': re.compile(r'(\d{3,4}x\d{3,4})', re.IGNORECASE),
            'fps': re.compile(r'(\d{2,3})fps', re.IGNORECASE),
            'bitrate': re.compile(r'(\d+)k', re.IGNORECASE),
            'codec': re.compile(r'(h264|h265|vp9|av1)', re.IGNORECASE)
        }
    
    def analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyze URL for video properties and suggestions"""
        if not url:
            return {}
        
        suggestions: List[str] = []
        analysis: Dict[str, Any] = {
            'is_valid': self._is_valid_url(url),
            'type': self._detect_url_type(url),
            'properties': self._extract_properties(url),
            'suggestions': suggestions
        }
        
        # Add suggestions based on analysis
        if analysis['type'] == 'm3u8':
            analysis['suggestions'].append("This appears to be an M3U8 stream. Use auto-extract for best results.")
        elif analysis['type'] == 'mp4':
            analysis['suggestions'].append("Direct MP4 link detected. Consider checking for higher quality versions.")
        
        return analysis
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def _detect_url_type(self, url: str) -> str:
        """Detect URL content type"""
        url_lower = url.lower()
        if '.m3u8' in url_lower:
            return 'm3u8'
        elif '.mp4' in url_lower:
            return 'mp4'
        elif '.ts' in url_lower:
            return 'ts'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'vimeo.com' in url_lower:
            return 'vimeo'
        else:
            return 'unknown'
    
    def _extract_properties(self, url: str) -> Dict[str, str]:
        """Extract video properties from URL"""
        properties = {}
        
        for prop_name, pattern in self.common_patterns.items():
            match = pattern.search(url)
            if match:
                properties[prop_name] = match.group(1)
        
        return properties


class EnhancedTaskDialog(ResponsiveWidget, QDialog):
    """Enhanced Task Creation Dialog with responsive design, modern theming, and performance optimizations"""

    # Signals for better performance
    dataChanged = Signal()
    validationChanged = Signal(bool)

    def __init__(self, settings, theme_manager=None, parent=None):
        QDialog.__init__(self, parent)
        ResponsiveWidget.__init__(self)

        self.settings = settings
        self.theme_manager = theme_manager
        self.responsive_manager = ResponsiveManager.instance()
        self.history_manager = HistoryManager()
        self.url_validator = URLValidator(self)
        self.url_analyzer = URLAnalyzer()
        
        # Performance optimization: Lazy loading flags
        self._ui_created = False
        self._completers_setup = False
        self._animations_setup = False
        
        # Enhanced caching for better performance
        self._validation_cache = {}
        self._last_validation_time = 0
        self._validation_debounce_interval = 300  # ms
        
        # Auto-save timer for draft functionality
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_draft)
        self.auto_save_timer.setSingleShot(False)
        self.auto_save_timer.setInterval(30000)  # 30 seconds
        
        # Validation timer to reduce validation frequency
        self.validation_timer = QTimer()
        self.validation_timer.timeout.connect(self._validate_form)
        self.validation_timer.setSingleShot(True)
        self.validation_timer.setInterval(500)  # 500ms delay
        
        # URL analysis timer
        self.url_analysis_timer = QTimer()
        self.url_analysis_timer.timeout.connect(self._analyze_current_url)
        self.url_analysis_timer.setSingleShot(True)
        self.url_analysis_timer.setInterval(1000)  # 1 second delay
        
        # Context menus (lazy loaded)
        self._url_context_menu: Optional[QMenu] = None
        self._output_context_menu: Optional[QMenu] = None
        self._window_context_menu: Optional[QMenu] = None
        
        # Animation objects
        self._fade_animation: Optional[QPropertyAnimation] = None
        self._slide_animation: Optional[QPropertyAnimation] = None
        
        # Performance monitoring
        self._performance_metrics = {
            'init_time': 0.0,
            'ui_creation_time': 0.0,
            'validation_count': 0,
            'extraction_count': 0
        }
        
        import time
        start_time = time.time()
        
        # Setup responsive window properties
        self._setup_responsive_window()
        
        # Apply enhanced theme styles
        self._apply_enhanced_theme_styles()
        
        # Enable window right-click context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_window_context_menu)

        ui_start = time.time()
        self._create_enhanced_ui()
        self._performance_metrics['ui_creation_time'] = float(time.time() - ui_start)
        
        self._setup_keyboard_shortcuts()
        self._setup_animations()
        self._load_draft()
        
        # Start auto-save timer
        self.auto_save_timer.start()
        
        self._performance_metrics['init_time'] = float(time.time() - start_time)

    def _setup_responsive_window(self):
        """Setup responsive window properties"""
        self.setWindowTitle(tr("task_dialog.title"))
        self.setWindowIcon(FIF.DOWNLOAD.icon())

        # Responsive sizing
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        if current_bp.value in ['xs', 'sm']:
            # Compact size for small screens
            self.setMinimumSize(500, 550)
            self.resize(550, 600)
            self.setMaximumHeight(700)
        elif current_bp.value == 'md':
            # Medium size for medium screens
            self.setMinimumSize(600, 600)
            self.resize(650, 650)
            self.setMaximumHeight(750)
        else:
            # Full size for large screens
            self.setMinimumSize(650, 650)
            self.resize(700, 700)
            self.setMaximumHeight(800)

        # Enhanced window flags
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowContextHelpButtonHint
        )

    def _apply_enhanced_theme_styles(self):
        """Apply enhanced theme-aware styles using QFluentWidgets theming"""
        # Let QFluentWidgets handle most of the theming automatically
        # Only apply minimal custom styling where absolutely necessary
        
        if self.theme_manager:
            accent_color = self.theme_manager.ACCENT_COLORS.get(
                self.theme_manager.get_current_accent(), '#0078D4'
            )
        else:
            accent_color = '#0078D4'

        # Minimal custom styling - let QFluentWidgets handle the rest
        self.setStyleSheet(f"""
            QDialog {{
                border-radius: 12px;
            }}
            PrimaryPushButton:focus {{
                border-color: {accent_color};
            }}
        """)

    def on_breakpoint_changed(self, breakpoint: str):
        """Handle responsive breakpoint changes"""
        logger.debug(f"Task dialog adapting to breakpoint: {breakpoint}")
        self._setup_responsive_window()

    def _create_enhanced_ui(self):
        """Create enhanced responsive user interface"""
        # Main layout with responsive spacing
        main_layout = QVBoxLayout(self)
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        if current_bp.value in ['xs', 'sm']:
            main_layout.setContentsMargins(16, 16, 16, 16)
            main_layout.setSpacing(16)
        else:
            main_layout.setContentsMargins(24, 20, 24, 20)
            main_layout.setSpacing(24)

        # Enhanced header with responsive design
        self._create_enhanced_header(main_layout)

        # Content section with responsive scroll area
        scroll_area = SmoothScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(0)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        if current_bp.value in ['xs', 'sm']:
            content_layout.setSpacing(16)
        else:
            content_layout.setSpacing(20)
        
        self._create_responsive_content(content_layout)
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area, 1)

        # Responsive action buttons
        self._create_responsive_actions(main_layout)

        # Fill default values
        self._fill_defaults()

    def _create_enhanced_header(self, parent_layout):
        """Create enhanced header with responsive design"""
        header_layout = QHBoxLayout()
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        if current_bp.value in ['xs', 'sm']:
            header_layout.setSpacing(8)
        else:
            header_layout.setSpacing(12)

        # Responsive icon
        icon_widget = IconWidget(FIF.DOWNLOAD)
        if current_bp.value in ['xs', 'sm']:
            icon_widget.setFixedSize(24, 24)
        else:
            icon_widget.setFixedSize(32, 32)
        header_layout.addWidget(icon_widget)

        # Title and subtitle with responsive typography
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_label = SubtitleLabel(tr("task_dialog.basic_info.title"))
        title_label.setObjectName("titleLabel")
        if current_bp.value in ['xs', 'sm']:
            title_label.setStyleSheet(f"font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING}; font-weight: {VidTaniumTheme.FONT_WEIGHT_SEMIBOLD};")
        text_layout.addWidget(title_label)

        subtitle_label = BodyLabel(tr("task_dialog.basic_info.subtitle"))
        subtitle_label.setStyleSheet(f"color: {VidTaniumTheme.TEXT_SECONDARY}; font-size: {VidTaniumTheme.FONT_SIZE_CAPTION};")
        text_layout.addWidget(subtitle_label)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        parent_layout.addLayout(header_layout)

    def _create_responsive_content(self, parent_layout):
        """Create responsive content section with adaptive cards"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Basic Information Card with responsive sizing
        self.basic_card = ElevatedCardWidget()
        if current_bp.value in ['xs', 'sm']:
            self.basic_card.setMinimumHeight(280)
        else:
            self.basic_card.setMinimumHeight(320)
            
        basic_card_layout = QVBoxLayout(self.basic_card)
        
        # Responsive card margins
        if current_bp.value in ['xs', 'sm']:
            basic_card_layout.setContentsMargins(16, 16, 16, 16)
            basic_card_layout.setSpacing(16)
        else:
            basic_card_layout.setContentsMargins(24, 20, 24, 24)
            basic_card_layout.setSpacing(20)

        # Enhanced card title
        basic_title = StrongBodyLabel(tr("task_dialog.basic_info.card_title"))
        basic_title.setStyleSheet(f"""
            font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD}; 
            font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
            color: {VidTaniumTheme.TEXT_PRIMARY};
            margin-bottom: 8px;
        """)
        basic_card_layout.addWidget(basic_title)

        # Responsive form layout
        self._create_responsive_basic_form(basic_card_layout, current_bp)
        parent_layout.addWidget(self.basic_card)

        # Advanced Options Card with responsive design
        self.advanced_card = ElevatedCardWidget()
        if current_bp.value in ['xs', 'sm']:
            self.advanced_card.setMinimumHeight(160)
        else:
            self.advanced_card.setMinimumHeight(180)
            
        advanced_card_layout = QVBoxLayout(self.advanced_card)
        
        # Responsive card margins
        if current_bp.value in ['xs', 'sm']:
            advanced_card_layout.setContentsMargins(16, 16, 16, 16)
            advanced_card_layout.setSpacing(16)
        else:
            advanced_card_layout.setContentsMargins(24, 20, 24, 24)
            advanced_card_layout.setSpacing(20)

        # Enhanced card title
        advanced_title = StrongBodyLabel(tr("task_dialog.advanced_options.title"))
        advanced_title.setStyleSheet(f"""
            font-weight: {VidTaniumTheme.FONT_WEIGHT_BOLD}; 
            font-size: {VidTaniumTheme.FONT_SIZE_SUBHEADING};
            color: {VidTaniumTheme.TEXT_PRIMARY};
            margin-bottom: 8px;
        """)
        advanced_card_layout.addWidget(advanced_title)

        # Responsive advanced form
        self._create_responsive_advanced_form(advanced_card_layout, current_bp)
        parent_layout.addWidget(self.advanced_card)

    def _create_responsive_basic_form(self, parent_layout, current_bp):
        """Create responsive basic form layout"""
        # Form layout with responsive spacing
        basic_layout = QFormLayout()
        basic_layout.setContentsMargins(0, 0, 0, 0)
        
        if current_bp.value in ['xs', 'sm']:
            basic_layout.setVerticalSpacing(16)
            basic_layout.setHorizontalSpacing(12)
        else:
            basic_layout.setVerticalSpacing(20)
            basic_layout.setHorizontalSpacing(16)
            
        basic_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        basic_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Responsive input heights
        input_height = 36 if current_bp.value in ['xs', 'sm'] else 40

        # Task name
        self.name_input = LineEdit()
        self.name_input.setPlaceholderText(tr("task_dialog.basic_info.name_placeholder"))
        self.name_input.setMinimumHeight(input_height)
        self.name_input.textChanged.connect(self._on_input_changed)
        basic_layout.addRow(tr("task_dialog.basic_info.task_name"), self.name_input)

        # Video URL with extract button
        url_layout = QHBoxLayout()
        url_layout.setSpacing(8)
        url_layout.setContentsMargins(0, 0, 0, 0)
        
        self.base_url_input = SearchLineEdit()
        self.base_url_input.setPlaceholderText(tr("task_dialog.basic_info.url_placeholder"))
        self.base_url_input.setMinimumHeight(input_height)
        self.base_url_input.setValidator(self.url_validator)
        self.base_url_input.textChanged.connect(self._on_input_changed)
        self.base_url_input.textChanged.connect(self._on_url_changed)
        url_layout.addWidget(self.base_url_input, 1)

        # Responsive extract button
        self.extract_button = PrimaryPushButton(tr("task_dialog.basic_info.auto_extract"))
        self.extract_button.setIcon(FIF.SEARCH)
        if current_bp.value in ['xs', 'sm']:
            self.extract_button.setFixedSize(80, input_height)
        else:
            self.extract_button.setFixedSize(100, input_height)
        self.extract_button.setToolTip(tr("task_dialog.basic_info.extract_tooltip") + " (F5)")
        self.extract_button.clicked.connect(self._extract_m3u8_info)
        url_layout.addWidget(self.extract_button)

        basic_layout.addRow(tr("task_dialog.basic_info.video_url"), url_layout)

        # Key URL
        self.key_url_input = LineEdit()
        self.key_url_input.setPlaceholderText(tr("task_dialog.basic_info.key_placeholder"))
        self.key_url_input.setMinimumHeight(input_height)
        self.key_url_input.textChanged.connect(self._on_input_changed)
        basic_layout.addRow(tr("task_dialog.basic_info.key_url"), self.key_url_input)

        # Segments count
        self.segments_input = SpinBox()
        self.segments_input.setRange(1, 10000)
        self.segments_input.setValue(200)
        self.segments_input.setMinimumHeight(input_height)
        self.segments_input.valueChanged.connect(self._on_input_changed)
        basic_layout.addRow(tr("task_dialog.basic_info.segments"), self.segments_input)

        # Output file
        output_layout = QHBoxLayout()
        output_layout.setSpacing(8)
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        self.output_input = LineEdit()
        self.output_input.setPlaceholderText(tr("task_dialog.basic_info.output_placeholder"))
        self.output_input.setMinimumHeight(input_height)
        self.output_input.textChanged.connect(self._on_input_changed)
        output_layout.addWidget(self.output_input, 1)

        self.browse_button = ToolButton(FIF.FOLDER)
        self.browse_button.setFixedSize(input_height, input_height)
        self.browse_button.setToolTip(tr("task_dialog.basic_info.browse_tooltip"))
        self.browse_button.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_button)

        basic_layout.addRow(tr("task_dialog.basic_info.output_file"), output_layout)
        parent_layout.addLayout(basic_layout)

    def _create_responsive_advanced_form(self, parent_layout, current_bp):
        """Create responsive advanced form layout"""
        # Form layout with responsive spacing
        advanced_layout = QFormLayout()
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        
        if current_bp.value in ['xs', 'sm']:
            advanced_layout.setVerticalSpacing(16)
            advanced_layout.setHorizontalSpacing(12)
        else:
            advanced_layout.setVerticalSpacing(20)
            advanced_layout.setHorizontalSpacing(16)
            
        advanced_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        advanced_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Responsive input heights
        input_height = 36 if current_bp.value in ['xs', 'sm'] else 40

        # Priority
        self.priority_combo = ComboBox()
        self.priority_combo.addItem(tr("task_dialog.advanced_options.priority_high"), "high")
        self.priority_combo.addItem(tr("task_dialog.advanced_options.priority_normal"), "normal")
        self.priority_combo.addItem(tr("task_dialog.advanced_options.priority_low"), "low")
        self.priority_combo.setCurrentIndex(1)
        self.priority_combo.setMinimumHeight(input_height)
        advanced_layout.addRow(tr("task_dialog.advanced_options.priority"), self.priority_combo)

        # Options with responsive layout
        options_widget = QWidget()
        if current_bp.value in ['xs', 'sm']:
            # Vertical layout for small screens
            options_layout: Union[QVBoxLayout, QHBoxLayout] = QVBoxLayout(options_widget)
            options_layout.setSpacing(8)
        else:
            # Horizontal layout for larger screens
            options_layout = QHBoxLayout(options_widget)
            options_layout.setSpacing(16)
            
        options_layout.setContentsMargins(0, 0, 0, 0)

        self.auto_start_check = CheckBox(tr("task_dialog.advanced_options.auto_start"))
        self.auto_start_check.setChecked(True)
        options_layout.addWidget(self.auto_start_check)

        self.notify_check = CheckBox(tr("task_dialog.advanced_options.notify_completion"))
        self.notify_check.setChecked(True)
        options_layout.addWidget(self.notify_check)

        if current_bp.value not in ['xs', 'sm']:
            options_layout.addStretch()

        advanced_layout.addRow(tr("task_dialog.advanced_options.options"), options_widget)
        parent_layout.addLayout(advanced_layout)

    def _create_responsive_actions(self, parent_layout):
        """Create responsive action buttons"""
        current_bp = self.responsive_manager.get_current_breakpoint()
        
        # Add spacer
        parent_layout.addItem(QSpacerItem(20, 16, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Button layout with responsive behavior
        if current_bp.value in ['xs', 'sm']:
            # Vertical button layout for small screens
            button_layout: Union[QVBoxLayout, QHBoxLayout] = QVBoxLayout()
            button_layout.setSpacing(12)
            button_size = (120, 36)
        else:
            # Horizontal button layout for larger screens
            button_layout = QHBoxLayout()
            button_layout.setSpacing(16)
            button_layout.addStretch()
            button_size = (140, 40)
            
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Cancel button
        self.cancel_button = PushButton(tr("task_dialog.buttons.cancel"))
        self.cancel_button.setIcon(FIF.CANCEL)
        self.cancel_button.setFixedSize(*button_size)
        self.cancel_button.setToolTip(tr("task_dialog.buttons.cancel_tooltip") + " (Esc)")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        # Create button
        self.create_button = PrimaryPushButton(tr("task_dialog.buttons.create"))
        self.create_button.setIcon(FIF.ACCEPT)
        self.create_button.setFixedSize(*button_size)
        self.create_button.setToolTip(tr("task_dialog.buttons.create_tooltip") + " (Ctrl+Enter)")
        self.create_button.clicked.connect(self._on_ok)
        self.create_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.create_button)

        parent_layout.addLayout(button_layout)

    def _fill_defaults(self):
        """填充默认值"""
        # 设置默认的输出目录
        output_dir = self.settings.get("general", "output_directory", "")
        if output_dir and os.path.exists(output_dir):
            self.output_input.setText(os.path.join(output_dir, "output.mp4"))

    def _browse_output(self):
        """浏览输出文件"""
        output_dir = self.settings.get("general", "output_directory", "")
        filename, _ = QFileDialog.getSaveFileName(
            self, tr("task_dialog.file_dialog.save_title"), output_dir, tr(
                "task_dialog.file_dialog.video_filter")
        )

        if filename:
            self.output_input.setText(filename)            # 更新默认输出目录
            self.settings.set("general", "output_directory",
                              os.path.dirname(filename))

    def _on_ok(self):
        """确定按钮点击"""
        # 验证输入
        if not self.base_url_input.text():
            self._show_error(tr("task_dialog.errors.no_url"))
            return

        # 密钥URL不是必需的，注释掉这个检查
        # if not self.key_url_input.text():
        #     self._show_error("请输入密钥URL")
        #     return

        if not self.output_input.text():
            self._show_error(tr("task_dialog.errors.no_output"))
            return

        # 创建任务名称（如果未提供）
        if not self.name_input.text():
            filename = os.path.basename(self.output_input.text())
            name = os.path.splitext(filename)[0]
            self.name_input.setText(name)

        # 接受对话框
        self.accept()

    def _show_error(self, message):
        """显示错误消息"""
        InfoBar.error(
            title=tr("task_dialog.errors.input_error"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _extract_m3u8_info(self):
        """从M3U8 URL自动提取信息"""
        url = self.base_url_input.text().strip()
        if not url:
            self._show_error(tr("task_dialog.errors.no_url"))
            return

        # 显示加载对话框
        progress = QProgressDialog(tr("task_dialog.extraction.progress"), tr(
            "task_dialog.extraction.cancel"), 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle(tr("task_dialog.extraction.title"))
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        try:
            # 导入M3U8解析器
            from src.core.m3u8_parser import extract_m3u8_info

            # 获取用户代理设置
            user_agent = self.settings.get("advanced", "user_agent", "")
            headers = {"User-Agent": user_agent} if user_agent else None

            # 提取信息
            result = extract_m3u8_info(url, headers)            # 关闭进度对话框
            progress.close()

            if not result["success"]:
                self._show_error(tr("task_dialog.errors.extract_failed").format(
                    message=result['message']))
                return

            # 填充表单
            if result["base_url"]:
                self.base_url_input.setText(result["base_url"])

            if result["key_url"]:
                self.key_url_input.setText(result["key_url"])

            if result["segments"]:
                self.segments_input.setValue(result["segments"])

            # 如果没有提供任务名称，从URL创建一个
            if not self.name_input.text():
                from urllib.parse import urlparse
                from os.path import basename

                parsed_url = urlparse(url)
                path = parsed_url.path
                name = basename(path)
                if name:
                    name = name.split(".")[0]  # 移除扩展名
                    self.name_input.setText(name)            # 显示提取结果
            resolution = result['selected_stream']['resolution'] if 'resolution' in result['selected_stream'] else tr(
                "common.unknown")
            QMessageBox.information(
                self,
                tr("task_dialog.extraction.success"),
                tr("task_dialog.extraction.success_message").format(
                    resolution=resolution,
                    segments=result['segments'],
                    duration=int(result['duration']),
                    encryption=result['encryption']
                )
            )

        except Exception as e:
            progress.close()
            import traceback
            self._show_error(
                tr("task_dialog.errors.extract_error").format(error=str(e)))

    def get_task_data(self):
        """获取任务数据"""
        # Save to history when task is created
        url = self.base_url_input.text().strip()
        output = self.output_input.text().strip()
        
        if url:
            self.history_manager.add_url(url)
        if output:
            self.history_manager.add_output_path(output)
            
        return {
            "name": self.name_input.text(),
            "base_url": url,
            "key_url": self.key_url_input.text(),
            "segments": self.segments_input.value(),
            "output_file": output,
            "priority": self.priority_combo.currentData(),
            "auto_start": self.auto_start_check.isChecked()
        }

    # ====== New Performance and Feature Methods ======
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better UX"""
        # Ctrl+Enter to create task
        create_shortcut = QAction(self)
        create_shortcut.setShortcut(QKeySequence("Ctrl+Return"))
        create_shortcut.triggered.connect(self._on_ok)
        self.addAction(create_shortcut)
        
        # Ctrl+D to clear all fields
        clear_shortcut = QAction(self)
        clear_shortcut.setShortcut(QKeySequence("Ctrl+D"))
        clear_shortcut.triggered.connect(self._clear_all_fields)
        self.addAction(clear_shortcut)
        
        # F5 to refresh/extract
        extract_shortcut = QAction(self)
        extract_shortcut.setShortcut(QKeySequence("F5"))
        extract_shortcut.triggered.connect(self._extract_m3u8_info)
        self.addAction(extract_shortcut)
        
        # Ctrl+S to save draft
        save_shortcut = QAction(self)
        save_shortcut.setShortcut(QKeySequence("Ctrl+S"))
        save_shortcut.triggered.connect(self._save_draft)
        self.addAction(save_shortcut)
        
        # Ctrl+H to show/hide history
        history_shortcut = QAction(self)
        history_shortcut.setShortcut(QKeySequence("Ctrl+H"))
        history_shortcut.triggered.connect(self._toggle_history_panel)
        self.addAction(history_shortcut)
        
        # Ctrl+Shift+C to clear cache
        clear_cache_shortcut = QAction(self)
        clear_cache_shortcut.setShortcut(QKeySequence("Ctrl+Shift+C"))
        clear_cache_shortcut.triggered.connect(self._clear_cache)
        self.addAction(clear_cache_shortcut)
        
        # Alt+P to show performance metrics
        perf_shortcut = QAction(self)
        perf_shortcut.setShortcut(QKeySequence("Alt+P"))
        perf_shortcut.triggered.connect(self._show_performance_metrics)
        self.addAction(perf_shortcut)

    def _setup_animations(self):
        """Setup smooth animations for better UX"""
        if self._animations_setup:
            return
            
        # Fade animation for validation feedback
        from PySide6.QtCore import QByteArray
        self._fade_animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self._fade_animation.setDuration(300)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self._animations_setup = True

    def _create_window_context_menu(self) -> QMenu:
        """Create context menu for window right-click"""
        if self._window_context_menu is None:
            menu = QMenu(self)
            
            # Window actions
            minimize_action = menu.addAction(tr("window.minimize"), self.showMinimized)
            minimize_action.setIcon(FIF.MINIMIZE.icon())

            menu.addSeparator()

            # Task actions
            clear_action = menu.addAction(tr("window.clear_all"), self._clear_all_fields)
            clear_action.setIcon(FIF.CLEAR_SELECTION.icon())

            save_draft_action = menu.addAction(tr("window.save_draft"), self._save_draft)
            save_draft_action.setIcon(FIF.SAVE.icon())
            
            menu.addSeparator()
            
            # History actions
            history_submenu = menu.addMenu(tr("window.history"))
            history_submenu.setIcon(FIF.HISTORY.icon())
            
            show_url_history = history_submenu.addAction(tr("window.show_url_history"), self._show_url_history)
            show_output_history = history_submenu.addAction(tr("window.show_output_history"), self._show_output_history)
            history_submenu.addSeparator()
            clear_url_history = history_submenu.addAction(tr("window.clear_url_history"), lambda: self.history_manager.clear_history("url"))
            clear_output_history = history_submenu.addAction(tr("window.clear_output_history"), lambda: self.history_manager.clear_history("output"))
            clear_all_history = history_submenu.addAction(tr("window.clear_all_history"), lambda: self.history_manager.clear_history("all"))
            
            menu.addSeparator()
            
            # Performance actions
            perf_submenu = menu.addMenu(tr("window.performance"))
            perf_submenu.setIcon(FIF.SPEED_HIGH.icon())

            show_metrics = perf_submenu.addAction(tr("window.show_metrics"), self._show_performance_metrics)
            clear_cache = perf_submenu.addAction(tr("window.clear_cache"), self._clear_cache)

            menu.addSeparator()

            # Help actions
            help_action = menu.addAction(tr("window.help"), self._show_help)
            help_action.setIcon(FIF.HELP.icon())

            about_action = menu.addAction(tr("window.about"), self._show_about)
            about_action.setIcon(FIF.INFO.icon())
            
            self._window_context_menu = menu
        
        return self._window_context_menu

    @Slot()
    def _show_window_context_menu(self, pos):
        """Show window context menu"""
        menu = self._create_window_context_menu()
        menu.exec(self.mapToGlobal(pos))

    def _setup_completers(self):
        """Setup auto-completion for input fields (lazy loaded)"""
        if self._completers_setup:
            return
            
        # URL completer
        url_history = self.history_manager.get_url_history()
        if url_history:
            url_completer = QCompleter(url_history, self)
            url_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            url_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.base_url_input.setCompleter(url_completer)
        
        # Output path completer
        output_history = self.history_manager.get_output_history()
        if output_history:
            output_completer = QCompleter(output_history, self)
            output_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            output_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.output_input.setCompleter(output_completer)
        
        self._completers_setup = True

    def _setup_context_menus(self):
        """Setup context menus for input fields"""
        # URL context menu
        self.base_url_input.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.base_url_input.customContextMenuRequested.connect(self._show_url_context_menu)
        
        # Output context menu
        self.output_input.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.output_input.customContextMenuRequested.connect(self._show_output_context_menu)
        
        # Key URL context menu
        self.key_url_input.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.key_url_input.customContextMenuRequested.connect(self._show_key_context_menu)

    def _create_url_context_menu(self) -> QMenu:
        """Create context menu for URL input field"""
        if self._url_context_menu is None:
            menu = QMenu(self)
            
            # Standard actions
            menu.addAction(tr("context.cut"), self.base_url_input.cut, QKeySequence.StandardKey.Cut)
            menu.addAction(tr("context.copy"), self.base_url_input.copy, QKeySequence.StandardKey.Copy)
            menu.addAction(tr("context.paste"), self.base_url_input.paste, QKeySequence.StandardKey.Paste)
            menu.addSeparator()
            
            # Clear action
            clear_action = menu.addAction(tr("context.clear"), self.base_url_input.clear)
            clear_action.setIcon(FIF.CLEAR_SELECTION.icon())

            # Select all
            menu.addAction(tr("context.select_all"), self.base_url_input.selectAll, QKeySequence.StandardKey.SelectAll)
            menu.addSeparator()

            # URL specific actions
            validate_action = menu.addAction(tr("context.validate_url"), self._validate_current_url)
            validate_action.setIcon(FIF.ACCEPT.icon())

            extract_action = menu.addAction(tr("context.extract_info"), self._extract_m3u8_info)
            extract_action.setIcon(FIF.SEARCH.icon())
            
            self._url_context_menu = menu
        
        return self._url_context_menu

    def _create_output_context_menu(self) -> QMenu:
        """Create context menu for output input field"""
        if self._output_context_menu is None:
            menu = QMenu(self)
            
            # Standard actions
            menu.addAction(tr("context.cut"), self.output_input.cut, QKeySequence.StandardKey.Cut)
            menu.addAction(tr("context.copy"), self.output_input.copy, QKeySequence.StandardKey.Copy)
            menu.addAction(tr("context.paste"), self.output_input.paste, QKeySequence.StandardKey.Paste)
            menu.addSeparator()
            
            # Clear action
            clear_action = menu.addAction(tr("context.clear"), self.output_input.clear)
            clear_action.setIcon(FIF.CLEAR_SELECTION.icon())

            # Select all
            menu.addAction(tr("context.select_all"), self.output_input.selectAll, QKeySequence.StandardKey.SelectAll)
            menu.addSeparator()

            # Browse action
            browse_action = menu.addAction(tr("context.browse"), self._browse_output)
            browse_action.setIcon(FIF.FOLDER.icon())

            # Open folder action
            open_folder_action = menu.addAction(tr("context.open_folder"), self._open_output_folder)
            open_folder_action.setIcon(FIF.FOLDER_ADD.icon())
            
            self._output_context_menu = menu
            
        return self._output_context_menu

    @Slot()
    def _show_url_context_menu(self, pos):
        """Show context menu for URL input"""
        menu = self._create_url_context_menu()
        menu.exec(self.base_url_input.mapToGlobal(pos))

    @Slot()
    def _show_output_context_menu(self, pos):
        """Show context menu for output input"""
        menu = self._create_output_context_menu()
        menu.exec(self.output_input.mapToGlobal(pos))

    @Slot()
    def _show_key_context_menu(self, pos):
        """Show context menu for key URL input"""
        menu = QMenu(self)
        
        # Standard actions
        menu.addAction(tr("context.cut"), self.key_url_input.cut, QKeySequence.StandardKey.Cut)
        menu.addAction(tr("context.copy"), self.key_url_input.copy, QKeySequence.StandardKey.Copy)
        menu.addAction(tr("context.paste"), self.key_url_input.paste, QKeySequence.StandardKey.Paste)
        menu.addSeparator()
        
        # Clear action
        clear_action = menu.addAction(tr("context.clear"), self.key_url_input.clear)
        clear_action.setIcon(FIF.CLEAR_SELECTION.icon())
        
        # Select all
        menu.addAction(tr("context.select_all"), self.key_url_input.selectAll, QKeySequence.StandardKey.SelectAll)
        
        menu.exec(self.key_url_input.mapToGlobal(pos))

    @Slot()
    def _validate_current_url(self):
        """Validate the current URL"""
        url = self.base_url_input.text().strip()
        if not url:
            self._show_error(tr("task_dialog.errors.no_url"))
            return
            
        validator = URLValidator()
        state, _, _ = validator.validate(url, 0)
        
        if state == QValidator.State.Acceptable:
            InfoBar.success(
                title=tr("validation.url_valid"),
                content=tr("validation.url_valid_message"),
                duration=2000,
                parent=self
            )
        else:
            self._show_error(tr("validation.url_invalid"))

    @Slot()
    def _open_output_folder(self):
        """Open output folder in file explorer"""
        path = self.output_input.text().strip()
        if not path:
            return
            
        folder = os.path.dirname(path)
        if os.path.exists(folder):
            if os.name == 'nt':  # Windows
                os.startfile(folder)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{folder}"' if sys.platform == 'darwin' else f'xdg-open "{folder}"')

    @Slot()
    def _clear_all_fields(self):
        """Clear all input fields"""
        reply = QMessageBox.question(
            self,
            tr("dialog.clear_confirm"),
            tr("dialog.clear_confirm_message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.name_input.clear()
            self.base_url_input.clear()
            self.key_url_input.clear()
            self.segments_input.setValue(200)
            self.output_input.clear()
            self.priority_combo.setCurrentIndex(1)
            self.auto_start_check.setChecked(True)
            self.notify_check.setChecked(True)

    @Slot()
    def _auto_save_draft(self):
        """Auto-save current form data as draft"""
        self._save_draft()

    def _save_draft(self):
        """Save current form data as draft"""
        draft_data = {
            "name": self.name_input.text(),
            "base_url": self.base_url_input.text(),
            "key_url": self.key_url_input.text(),
            "segments": self.segments_input.value(),
            "output_file": self.output_input.text(),
            "priority": self.priority_combo.currentIndex(),
            "auto_start": self.auto_start_check.isChecked(),
            "notify": self.notify_check.isChecked()
        }
        
        draft_file = os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation), "task_draft.json")
        os.makedirs(os.path.dirname(draft_file), exist_ok=True)
        
        try:
            with open(draft_file, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, indent=2)
        except Exception as e:
            # Silent fail for auto-save
            pass

    def _load_draft(self):
        """Load draft data if available"""
        draft_file = os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation), "task_draft.json")
        
        if not os.path.exists(draft_file):
            return
            
        try:
            with open(draft_file, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            # Only load if fields are empty (don't override explicit data)
            if not self.name_input.text() and draft_data.get("name"):
                self.name_input.setText(draft_data["name"])
            
            if not self.base_url_input.text() and draft_data.get("base_url"):
                self.base_url_input.setText(draft_data["base_url"])
            
            if not self.key_url_input.text() and draft_data.get("key_url"):
                self.key_url_input.setText(draft_data["key_url"])
            
            if draft_data.get("segments"):
                self.segments_input.setValue(draft_data["segments"])
            
            if not self.output_input.text() and draft_data.get("output_file"):
                self.output_input.setText(draft_data["output_file"])
            
            if draft_data.get("priority") is not None:
                self.priority_combo.setCurrentIndex(draft_data["priority"])
            
            if draft_data.get("auto_start") is not None:
                self.auto_start_check.setChecked(draft_data["auto_start"])
            
            if draft_data.get("notify") is not None:
                self.notify_check.setChecked(draft_data["notify"])
                
        except Exception as e:
            # Silent fail for draft loading
            pass

    @Slot()
    def _validate_form(self):
        """Validate form and emit signal"""
        url = self.base_url_input.text().strip()
        output = self.output_input.text().strip()
        
        is_valid = bool(url and output)
        
        # Enable/disable create button based on validation
        if hasattr(self, 'create_button'):
            self.create_button.setEnabled(is_valid)
        
        self.validationChanged.emit(is_valid)

    def _on_input_changed(self):
        """Handle input changes with delayed validation"""
        self.dataChanged.emit()
        self.validation_timer.start()  # Restart timer

    def showEvent(self, event):
        """Override show event for performance optimizations"""
        super().showEvent(event)
        
        # Setup completers when dialog is shown (lazy loading)
        QTimer.singleShot(100, self._setup_completers)
        QTimer.singleShot(200, self._setup_context_menus)

    def closeEvent(self, event):
        """Override close event to save draft and cleanup"""
        self._save_draft()
        self.auto_save_timer.stop()
        super().closeEvent(event)

    def accept(self):
        """Override accept to save final data"""
        # Clear draft when task is created successfully
        draft_file = os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation), "task_draft.json")
        if os.path.exists(draft_file):
            try:
                os.remove(draft_file)
            except:
                pass
        
        super().accept()

    # ====== Enhanced Performance and Feature Methods ======
    
    @Slot()
    def _on_url_changed(self):
        """Handle URL changes with analysis"""
        self.url_analysis_timer.start()  # Restart analysis timer
        self._performance_metrics['validation_count'] += 1
    
    @Slot()
    def _analyze_current_url(self):
        """Analyze current URL and provide suggestions"""
        url = self.base_url_input.text().strip()
        if not url:
            return
            
        analysis = self.url_analyzer.analyze_url(url)
        
        if analysis.get('suggestions'):
            # Show suggestions as a flyout
            self._show_url_suggestions(analysis['suggestions'])
        
        # Auto-fill name based on URL analysis
        if not self.name_input.text() and analysis.get('properties'):
            self._auto_generate_name(url, analysis['properties'])
    
    def _show_url_suggestions(self, suggestions: List[str]):
        """Show URL analysis suggestions"""
        if not suggestions:
            return
            
        suggestion_text = "\n".join(f"• {s}" for s in suggestions)
        
        InfoBar.info(
            title=tr("analysis.suggestions"),
            content=suggestion_text,
            duration=5000,
            parent=self
        )
    
    def _auto_generate_name(self, url: str, properties: Dict[str, str]):
        """Auto-generate task name from URL and properties"""
        try:
            parsed_url = urlparse(url)
            base_name = os.path.basename(parsed_url.path)
            
            if base_name:
                name = os.path.splitext(base_name)[0]
                
                # Add quality info if available
                if 'quality' in properties:
                    name += f"_{properties['quality']}"
                elif 'resolution' in properties:
                    name += f"_{properties['resolution']}"
                
                self.name_input.setText(name)
        except:
            pass
    
    @Slot()
    def _toggle_history_panel(self):
        """Toggle history panel visibility"""
        # Create a simple history dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("history.title"))
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Create tabs for URL and output history
        tab_widget = QTabWidget()
        
        # URL history tab
        url_tab = QWidget()
        url_layout = QVBoxLayout(url_tab)
        url_list = QListWidget()
        
        for url in self.history_manager.get_url_history():
            item = QListWidgetItem(url)
            item.setToolTip(url)
            url_list.addItem(item)
        
        url_list.itemDoubleClicked.connect(lambda item: self._use_history_item(item.text(), "url"))
        url_layout.addWidget(url_list)
        
        tab_widget.addTab(url_tab, tr("history.urls"))
        
        # Output history tab
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)
        output_list = QListWidget()
        
        for path in self.history_manager.get_output_history():
            item = QListWidgetItem(path)
            item.setToolTip(path)
            output_list.addItem(item)
        
        output_list.itemDoubleClicked.connect(lambda item: self._use_history_item(item.text(), "output"))
        output_layout.addWidget(output_list)
        
        tab_widget.addTab(output_tab, tr("history.outputs"))
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = PushButton(tr("common.close"))
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _use_history_item(self, text: str, item_type: str):
        """Use selected history item"""
        if item_type == "url":
            self.base_url_input.setText(text)
        elif item_type == "output":
            self.output_input.setText(text)
    
    @Slot()
    def _show_url_history(self):
        """Show URL history in a flyout"""
        urls = self.history_manager.get_frequent_urls(10)
        if not urls:
            InfoBar.warning(
                title=tr("history.empty"),
                content=tr("history.no_urls"),
                duration=2000,
                parent=self
            )
            return
        
        # Create a simple info display
        url_text = "\n".join(f"{i+1}. {url[:50]}..." if len(url) > 50 else f"{i+1}. {url}" 
                            for i, url in enumerate(urls))
        
        InfoBar.info(
            title=tr("history.recent_urls"),
            content=url_text,
            duration=8000,
            parent=self
        )
    
    @Slot()
    def _show_output_history(self):
        """Show output history"""
        paths = self.history_manager.get_output_history()[:10]
        if not paths:
            InfoBar.warning(
                title=tr("history.empty"),
                content=tr("history.no_outputs"),
                duration=2000,
                parent=self
            )
            return
        
        path_text = "\n".join(f"{i+1}. {os.path.basename(path)}" 
                             for i, path in enumerate(paths))
        
        InfoBar.info(
            title=tr("history.recent_outputs"),
            content=path_text,
            duration=8000,
            parent=self
        )
    
    @Slot()
    def _clear_cache(self):
        """Clear performance cache"""
        self._validation_cache.clear()
        self.history_manager._url_cache = None
        self.history_manager._output_cache = None
        self.history_manager._cache_dirty = {"url": True, "output": True}
        
        InfoBar.success(
            title=tr("cache.cleared"),
            content=tr("cache.cleared_message"),
            duration=2000,
            parent=self
        )
    
    @Slot()
    def _show_performance_metrics(self):
        """Show performance metrics"""
        metrics = self._performance_metrics.copy()
        
        metrics_text = f"""
Initialization Time: {metrics['init_time']:.3f}s
UI Creation Time: {metrics['ui_creation_time']:.3f}s
Validation Count: {metrics['validation_count']}
Extraction Count: {metrics['extraction_count']}
        """.strip()
        
        QMessageBox.information(
            self,
            tr("performance.metrics"),
            metrics_text
        )
    
    @Slot()
    def _show_help(self):
        """Show help information"""
        help_text = tr("help.task_dialog_content")
        
        QMessageBox.information(
            self,
            tr("help.task_dialog"),
            help_text
        )
    
    @Slot()
    def _show_about(self):
        """Show about information"""
        about_text = tr("about.task_dialog_content")
        
        QMessageBox.about(
            self,
            tr("about.task_dialog"),
            about_text
        )
    
    def _extract_m3u8_info_with_perf(self):
        """Enhanced M3U8 extraction with performance tracking (renamed to avoid duplicate)"""
        self._performance_metrics['extraction_count'] += 1
        
        url = self.base_url_input.text().strip()
        if not url:
            self._show_error(tr("task_dialog.errors.no_url"))
            return

        # Show enhanced loading dialog with cancel support
        progress = QProgressDialog(tr("task_dialog.extraction.progress"), tr(
            "task_dialog.extraction.cancel"), 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle(tr("task_dialog.extraction.title"))
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        # Add progress animation
        progress_timer = QTimer()
        progress_value = 0
        
        def update_progress():
            nonlocal progress_value
            progress_value = (progress_value + 1) % 100
            progress.setValue(progress_value)
        
        progress_timer.timeout.connect(update_progress)
        progress_timer.start(50)

        try:
            # Import M3U8 parser
            from src.core.m3u8_parser import extract_m3u8_info

            # Get user agent setting
            user_agent = self.settings.get("advanced", "user_agent", "")
            headers = {"User-Agent": user_agent} if user_agent else None

            # Extract information
            result = extract_m3u8_info(url, headers)
            
            # Stop progress animation
            progress_timer.stop()
            progress.close()

            if not result["success"]:
                self._show_error(tr("task_dialog.errors.extract_failed").format(
                    message=result['message']))
                return

            # Fill form with extracted data
            if result["base_url"]:
                self.base_url_input.setText(result["base_url"])

            if result["key_url"]:
                self.key_url_input.setText(result["key_url"])

            if result["segments"]:
                self.segments_input.setValue(result["segments"])

            # Auto-generate task name if empty
            if not self.name_input.text():
                parsed_url = urlparse(url)
                path = parsed_url.path
                name = os.path.basename(path)
                if name:
                    name = name.split(".")[0]  # Remove extension
                    self.name_input.setText(name)

            # Show extraction results with enhanced info
            resolution = result['selected_stream']['resolution'] if 'resolution' in result['selected_stream'] else tr("common.unknown")
            
            success_msg = tr("task_dialog.extraction.success_message").format(
                resolution=resolution,
                segments=result['segments'],
                duration=int(result['duration']),
                encryption=result['encryption']
            )
            
            InfoBar.success(
                title=tr("task_dialog.extraction.success"),
                content=success_msg,
                duration=5000,
                parent=self
            )

        except Exception as e:
            progress_timer.stop()
            progress.close()
            self._show_error(
                tr("task_dialog.errors.extract_error").format(error=str(e)))


# Backward compatibility alias
TaskDialog = EnhancedTaskDialog

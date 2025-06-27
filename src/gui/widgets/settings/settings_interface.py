"""
Unified Settings Interface - Consolidates all settings functionality into a single widget
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QSplitter,
    QFormLayout, QLabel, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer

from qfluentwidgets import (
    ScrollArea, SettingCardGroup, 
    SwitchSettingCard, OptionsSettingCard, PushSettingCard, 
    ComboBoxSettingCard, FluentIcon, Theme, setTheme, qconfig,
    PrimaryPushButton, PushButton, MessageBox,
    TitleLabel, SubtitleLabel, BodyLabel, StrongBodyLabel,
    ElevatedCardWidget, CardWidget, Pivot, IconWidget,
    LineEdit, CheckBox, ComboBox, SpinBox, Slider, TextEdit,
    TransparentToolButton, isDarkTheme
)

import os
from pathlib import Path
from ...dialogs.settings_config import SettingsConfig, SettingsConstants, SettingsManager
from ...utils.i18n import tr


class SettingsInterface(QWidget):
    """Unified settings interface that can be used both as a standalone interface and embedded in main window"""
    
    settings_applied = Signal()
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        
        # Initialize configuration
        self.config = SettingsConfig()
        SettingsManager.load_from_settings(self.config, self.settings)
        
        self._create_ui()
        self._load_settings()
        
        # Apply theme
        self._apply_current_theme()
        
        # Connect config signals
        self.config.theme_changed.connect(self._apply_current_theme)
    
    def _create_ui(self):
        """Create the unified settings interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)
        
        # Content area with navigation
        content_layout = self._create_content_area()
        main_layout.addLayout(content_layout)
        
        # Action buttons (optional, can be hidden for embedded use)
        self.action_layout = self._create_action_buttons()
        main_layout.addLayout(self.action_layout)
    
    def _create_header(self):
        """Create header section"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        title = TitleLabel(tr("settings.title"))
        subtitle = BodyLabel(tr("settings.subtitle"))
        subtitle.setStyleSheet("color: rgba(0, 0, 0, 0.6);")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        return header_layout
    
    def _create_content_area(self):
        """Create main content area with navigation"""
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left: Category navigation
        nav_widget = self._create_navigation()
        content_layout.addWidget(nav_widget, 1)
        
        # Right: Settings content
        self.settings_content = self._create_settings_content()
        content_layout.addWidget(self.settings_content, 3)
        
        return content_layout
    
    def _create_navigation(self):
        """Create navigation panel"""
        nav_container = QWidget()
        nav_container.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setSpacing(8)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation title
        nav_title = StrongBodyLabel(tr("settings.nav_title"))
        nav_layout.addWidget(nav_title)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        categories = [
            ("general", tr("settings.categories.general"), FluentIcon.HOME),
            ("download", tr("settings.categories.download"), FluentIcon.DOWNLOAD),
            ("appearance", tr("settings.categories.appearance"), FluentIcon.PALETTE),
            ("network", tr("settings.categories.network"), FluentIcon.WIFI),
            ("advanced", tr("settings.categories.advanced"), FluentIcon.SETTING)
        ]
        
        for key, name, icon in categories:
            btn = PrimaryPushButton(name)
            btn.setIcon(icon)
            btn.setObjectName(f"nav_{key}")
            btn.clicked.connect(lambda checked, k=key: self._switch_category(k))
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)
        
        nav_layout.addStretch()
        
        # Set initial selection
        self.current_category = "general"
        self.nav_buttons["general"].setEnabled(False)
        
        return nav_container
    
    def _create_settings_content(self):
        """Create settings content area"""
        # Create scroll area
        scroll_area = ScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(20)
        
        # Initialize with general settings
        self._create_general_settings()
        
        scroll_area.setWidget(content_widget)
        return scroll_area
    
    def _switch_category(self, category):
        """Switch to a different settings category"""
        if category == self.current_category:
            return
        
        # Reset previous button
        self.nav_buttons[self.current_category].setEnabled(True)
        
        # Set new button
        self.nav_buttons[category].setEnabled(False)
        self.current_category = category
        
        # Clear current content
        self._clear_content()
        
        # Load new content
        if category == "general":
            self._create_general_settings()
        elif category == "download":
            self._create_download_settings()
        elif category == "appearance":
            self._create_appearance_settings()
        elif category == "network":
            self._create_network_settings()
        elif category == "advanced":
            self._create_advanced_settings()
    
    def _clear_content(self):
        """Clear current content"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _create_general_settings(self):
        """Create general settings group"""
        # Output directory card
        output_card = self._create_output_directory_card()
        self.content_layout.addWidget(output_card)
        
        # Behavior settings card
        behavior_card = self._create_behavior_settings_card()
        self.content_layout.addWidget(behavior_card)
        
        # Update settings card
        update_card = self._create_update_settings_card()
        self.content_layout.addWidget(update_card)
        
        self.content_layout.addStretch()
    
    def _create_download_settings(self):
        """Create download settings group"""
        download_card = self._create_download_card()
        self.content_layout.addWidget(download_card)
        self.content_layout.addStretch()
    
    def _create_appearance_settings(self):
        """Create appearance settings group"""
        appearance_card = self._create_appearance_card()
        self.content_layout.addWidget(appearance_card)
        self.content_layout.addStretch()
    
    def _create_network_settings(self):
        """Create network settings group"""
        network_card = self._create_network_card()
        self.content_layout.addWidget(network_card)
        self.content_layout.addStretch()
    
    def _create_advanced_settings(self):
        """Create advanced settings group"""
        advanced_card = self._create_advanced_card()
        self.content_layout.addWidget(advanced_card)
        self.content_layout.addStretch()
    
    def _create_output_directory_card(self):
        """Create output directory settings card"""
        card = ElevatedCardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
          # Title
        title = StrongBodyLabel(tr("settings.general.download_dir.title"))
        layout.addWidget(title)
        
        # Output directory setting
        output_layout = QFormLayout()
        output_label = BodyLabel(tr("settings.general.download_dir.label"))
        
        output_container = QWidget()
        output_h_layout = QHBoxLayout(output_container)
        output_h_layout.setContentsMargins(0, 0, 0, 0)
        
        self.output_dir_input = LineEdit()
        self.output_dir_input.setText(self.config.output_directory.value)
        self.output_dir_input.textChanged.connect(self._on_output_dir_changed)
        output_h_layout.addWidget(self.output_dir_input)
        
        browse_btn = PrimaryPushButton(tr("settings.general.download_dir.browse"))
        browse_btn.setIcon(FluentIcon.FOLDER)
        browse_btn.clicked.connect(self._browse_output_directory)
        output_h_layout.addWidget(browse_btn)
        
        output_layout.addRow(output_label, output_container)
        layout.addLayout(output_layout)
        
        return card
    
    def _create_behavior_settings_card(self):
        """Create behavior settings card"""
        card = ElevatedCardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title = StrongBodyLabel(tr("settings.general.behavior.title"))
        layout.addWidget(title)
        
        # Auto cleanup
        cleanup_layout = QHBoxLayout()
        cleanup_label = BodyLabel(tr("settings.general.behavior.auto_cleanup"))
        cleanup_layout.addWidget(cleanup_label)
        cleanup_layout.addStretch()
        
        self.auto_cleanup_check = CheckBox()
        self.auto_cleanup_check.setChecked(self.config.auto_cleanup.value)
        self.auto_cleanup_check.toggled.connect(self._on_auto_cleanup_changed)
        cleanup_layout.addWidget(self.auto_cleanup_check)
        
        layout.addLayout(cleanup_layout)
        
        # Auto start downloads
        auto_start_layout = QHBoxLayout()
        auto_start_label = BodyLabel(tr("settings.general.behavior.auto_start"))
        auto_start_layout.addWidget(auto_start_label)
        auto_start_layout.addStretch()
        
        self.auto_start_check = CheckBox()
        self.auto_start_check.setChecked(self.config.auto_start_downloads.value)
        self.auto_start_check.toggled.connect(self._on_auto_start_changed)
        auto_start_layout.addWidget(self.auto_start_check)
        
        layout.addLayout(auto_start_layout)
        
        # Enable notifications
        notifications_layout = QHBoxLayout()
        notifications_label = BodyLabel(tr("settings.general.behavior.notifications"))
        notifications_layout.addWidget(notifications_label)
        notifications_layout.addStretch()
        
        self.notifications_check = CheckBox()
        self.notifications_check.setChecked(self.config.enable_notifications.value)
        self.notifications_check.toggled.connect(self._on_notifications_changed)
        notifications_layout.addWidget(self.notifications_check)
        
        layout.addLayout(notifications_layout)
        
        return card
    
    def _create_update_settings_card(self):
        """Create update settings card"""
        card = ElevatedCardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
          # Title
        title = StrongBodyLabel(tr("settings.general.updates.title"))
        layout.addWidget(title)
        
        # Check updates
        update_layout = QHBoxLayout()
        update_label = BodyLabel(tr("settings.general.updates.check_updates"))
        update_layout.addWidget(update_label)
        update_layout.addStretch()
        
        self.check_updates_check = CheckBox()
        self.check_updates_check.setChecked(self.config.check_updates.value)
        self.check_updates_check.toggled.connect(self._on_updates_changed)
        update_layout.addWidget(self.check_updates_check)
        
        layout.addLayout(update_layout)
        
        # Max recent files
        recent_layout = QFormLayout()
        recent_label = BodyLabel(tr("settings.general.updates.max_recent_files"))
        self.max_recent_files_spin = SpinBox()
        self.max_recent_files_spin.setRange(0, 50)
        self.max_recent_files_spin.setValue(self.config.max_recent_files.value)
        self.max_recent_files_spin.valueChanged.connect(self._on_max_recent_files_changed)
        recent_layout.addRow(recent_label, self.max_recent_files_spin)
        layout.addLayout(recent_layout)
        
        return card
    
    def _create_download_card(self):
        """Create download settings card"""
        card = ElevatedCardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
          # Title
        title = StrongBodyLabel(tr("settings.download.title"))
        layout.addWidget(title)
        
        # Form layout for settings
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
          # Max concurrent downloads
        self.max_downloads_combo = ComboBox()
        self.max_downloads_combo.addItems(SettingsConstants.CONCURRENT_OPTIONS)
        current_concurrent = str(self.config.max_concurrent_downloads.value)
        if current_concurrent in SettingsConstants.CONCURRENT_OPTIONS:
            self.max_downloads_combo.setCurrentText(current_concurrent)
        self.max_downloads_combo.currentTextChanged.connect(self._on_max_downloads_changed)
        form_layout.addRow(tr("settings.download.max_concurrent"), self.max_downloads_combo)
        
        # Retry attempts
        self.retry_combo = ComboBox()
        self.retry_combo.addItems(SettingsConstants.RETRY_OPTIONS)
        current_retry = str(self.config.retry_attempts.value)
        if current_retry in SettingsConstants.RETRY_OPTIONS:
            self.retry_combo.setCurrentText(current_retry)
        self.retry_combo.currentTextChanged.connect(self._on_retry_changed)
        form_layout.addRow(tr("settings.download.retry_attempts"), self.retry_combo)
        
        # Timeout
        self.timeout_spin = SpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSuffix(tr("settings.download.timeout_suffix"))
        self.timeout_spin.setValue(self.config.timeout.value)
        self.timeout_spin.valueChanged.connect(self._on_timeout_changed)
        form_layout.addRow(tr("settings.download.timeout"), self.timeout_spin)
        
        layout.addLayout(form_layout)
        return card
    
    def _create_appearance_card(self):
        """Create appearance settings card"""
        card = ElevatedCardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
          # Title
        title = StrongBodyLabel(tr("settings.appearance.title"))
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Theme
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(SettingsConstants.THEME_OPTIONS)
        current_theme = self.config.theme.value
        if current_theme in SettingsConstants.THEME_REVERSE_MAP:
            theme_text = SettingsConstants.THEME_REVERSE_MAP[current_theme]
            index = self.theme_combo.findText(theme_text)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        form_layout.addRow(tr("settings.appearance.theme"), self.theme_combo)
        
        # Language
        self.language_combo = ComboBox()
        self.language_combo.addItems(SettingsConstants.LANGUAGE_OPTIONS)
        current_language = self.config.language.value
        if current_language in SettingsConstants.LANGUAGE_REVERSE_MAP:
            language_text = SettingsConstants.LANGUAGE_REVERSE_MAP[current_language]
            index = self.language_combo.findText(language_text)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        form_layout.addRow(tr("settings.appearance.language"), self.language_combo)
        
        layout.addLayout(form_layout)
        return card
    
    def _create_network_card(self):
        """Create network settings card"""
        card = ElevatedCardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
          # Title
        title = StrongBodyLabel(tr("settings.network.title"))
        layout.addWidget(title)
        
        # Use proxy
        proxy_layout = QHBoxLayout()
        proxy_label = BodyLabel(tr("settings.network.use_proxy"))
        proxy_layout.addWidget(proxy_label)
        proxy_layout.addStretch()
        
        self.proxy_check = CheckBox()
        self.proxy_check.setChecked(self.config.use_proxy.value)
        self.proxy_check.toggled.connect(self._on_proxy_changed)
        proxy_layout.addWidget(self.proxy_check)
        
        layout.addLayout(proxy_layout)
        
        # Proxy settings
        proxy_form = QFormLayout()
        
        self.proxy_host_input = LineEdit()
        self.proxy_host_input.setText(self.config.proxy_host.value)
        self.proxy_host_input.setPlaceholderText("proxy.example.com")
        self.proxy_host_input.textChanged.connect(self._on_proxy_host_changed)
        proxy_form.addRow(tr("settings.network.proxy_address"), self.proxy_host_input)
        
        self.proxy_port_spin = SpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(self.config.proxy_port.value)
        self.proxy_port_spin.valueChanged.connect(self._on_proxy_port_changed)
        proxy_form.addRow(tr("settings.network.proxy_port"), self.proxy_port_spin)
        
        layout.addLayout(proxy_form)
        return card
    
    def _create_advanced_card(self):
        """Create advanced settings card"""
        card = ElevatedCardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
          # Title
        title = StrongBodyLabel(tr("settings.advanced.title"))
        layout.addWidget(title)
        
        # User agent
        ua_form = QFormLayout()
        
        self.user_agent_combo = ComboBox()
        self.user_agent_combo.addItems(SettingsConstants.USER_AGENT_OPTIONS)
        current_ua = self.config.user_agent.value
        if current_ua in SettingsConstants.USER_AGENT_REVERSE_MAP:
            ua_text = SettingsConstants.USER_AGENT_REVERSE_MAP[current_ua]
            index = self.user_agent_combo.findText(ua_text)
            if index >= 0:
                self.user_agent_combo.setCurrentIndex(index)
        self.user_agent_combo.currentTextChanged.connect(self._on_user_agent_changed)
        ua_form.addRow(tr("settings.advanced.user_agent"), self.user_agent_combo)
        
        # Custom user agent (shown when "custom" is selected)
        self.custom_ua_input = LineEdit()
        self.custom_ua_input.setText(self.config.custom_user_agent.value)
        self.custom_ua_input.setPlaceholderText(tr("settings.advanced.custom_ua_placeholder"))
        self.custom_ua_input.textChanged.connect(self._on_custom_ua_changed)
        self.custom_ua_input.setVisible(current_ua == "custom")
        ua_form.addRow(tr("settings.advanced.custom_ua_label"), self.custom_ua_input)
        
        layout.addLayout(ua_form)
        return card
    
    def _create_action_buttons(self):
        """Create action buttons"""
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)
          # Reset to defaults
        self.reset_button = PushButton(tr("settings.buttons.reset"))
        self.reset_button.clicked.connect(self._reset_to_defaults)
        
        # Apply
        self.apply_button = PrimaryPushButton(tr("settings.buttons.apply"))
        self.apply_button.clicked.connect(self._apply_settings)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        
        return button_layout
    
    def hide_action_buttons(self):
        """Hide action buttons for embedded use"""
        for i in range(self.action_layout.count()):
            item = self.action_layout.itemAt(i)
            if item.widget():
                item.widget().hide()
    
    def show_action_buttons(self):
        """Show action buttons for standalone use"""
        for i in range(self.action_layout.count()):
            item = self.action_layout.itemAt(i)
            if item.widget():
                item.widget().show()
    def _load_settings(self):
        """Load settings into the UI"""
        # Settings are loaded during UI creation
        pass
    
    def _apply_current_theme(self):
        """Apply the current theme to the UI"""
        theme_value = self.config.theme.value
        if theme_value == "light":
            setTheme(Theme.LIGHT)
        elif theme_value == "dark":
            setTheme(Theme.DARK)
        else:  # system
            setTheme(Theme.AUTO)
    
    def _apply_settings(self):
        """Apply all settings"""
        try:
            SettingsManager.save_to_settings(self.config, self.settings)
            self.settings_applied.emit()
            # Auto-apply theme changes
            self._apply_current_theme()
            
            MessageBox(tr("settings.messages.success"), tr("settings.messages.saved"), self).exec()
            return True
        except Exception as e:
            MessageBox(tr("settings.messages.error"), tr("settings.messages.save_failed").format(error=str(e)), self).exec()
            return False
    
    # Event handlers
    def _browse_output_directory(self):
        """Browse for output directory"""
        from PySide6.QtWidgets import QFileDialog
        
        current_dir = self.config.output_directory.value
        if not os.path.exists(current_dir):
            current_dir = str(Path.home())
        
        folder = QFileDialog.getExistingDirectory(
            self, tr("settings.messages.select_dir"), current_dir
        )
        
        if folder:
            self.config.output_directory.value = folder
            self.output_dir_input.setText(folder)
    
    def _on_output_dir_changed(self, text):
        """Handle output directory change"""
        self.config.output_directory.value = text
    
    def _on_auto_cleanup_changed(self, checked):
        """Handle auto cleanup change"""
        self.config.auto_cleanup.value = checked
    
    def _on_auto_start_changed(self, checked):
        """Handle auto start change"""
        self.config.auto_start_downloads.value = checked
    
    def _on_notifications_changed(self, checked):
        """Handle notifications change"""
        self.config.enable_notifications.value = checked
    
    def _on_updates_changed(self, checked):
        """Handle updates change"""
        self.config.check_updates.value = checked
    
    def _on_max_recent_files_changed(self, value):
        """Handle max recent files change"""
        self.config.max_recent_files.value = value
    
    def _on_max_downloads_changed(self, text):
        """Handle max downloads change"""
        try:
            value = int(text)
            self.config.max_concurrent_downloads.value = value
            self.config.max_concurrent_downloads_ui.value = text
        except ValueError:
            pass
    
    def _on_retry_changed(self, text):
        """Handle retry attempts change"""
        try:
            value = int(text)
            self.config.retry_attempts.value = value
            self.config.retry_attempts_ui.value = text
        except ValueError:
            pass
    
    def _on_timeout_changed(self, value):
        """Handle timeout change"""
        self.config.timeout.value = value
    
    def _on_theme_changed(self, text):
        """Handle theme change"""
        if text in SettingsConstants.THEME_MAP:
            theme_value = SettingsConstants.THEME_MAP[text]
            self.config.theme.value = theme_value
            # Apply theme immediately for preview
            self._apply_current_theme()
    
    def _on_language_changed(self, text):
        """Handle language change"""
        if text in SettingsConstants.LANGUAGE_MAP:
            language_value = SettingsConstants.LANGUAGE_MAP[text]
            self.config.language.value = language_value
    
    def _on_proxy_changed(self, checked):
        """Handle proxy change"""
        self.config.use_proxy.value = checked
    
    def _on_proxy_host_changed(self, text):
        """Handle proxy host change"""
        self.config.proxy_host.value = text
    
    def _on_proxy_port_changed(self, value):
        """Handle proxy port change"""
        self.config.proxy_port.value = value
    def _on_user_agent_changed(self, text):
        """Handle user agent change"""
        if text in SettingsConstants.USER_AGENT_MAP:
            ua_value = SettingsConstants.USER_AGENT_MAP[text]
            self.config.user_agent.value = ua_value
            # Show/hide custom input
            self.custom_ua_input.setVisible(ua_value == "custom")
    
    def _on_custom_ua_changed(self, text):
        """Handle custom user agent change"""
        self.config.custom_user_agent.value = text
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            tr("settings.messages.reset_confirm"),
            tr("settings.messages.reset_message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            SettingsManager.reset_to_defaults(self.config)
            
            # Refresh the current category to show reset values
            current = self.current_category
            self._clear_content()
            if current == "general":
                self._create_general_settings()
            elif current == "download":
                self._create_download_settings()
            elif current == "appearance":
                self._create_appearance_settings()
            elif current == "network":
                self._create_network_settings()
            elif current == "advanced":
                self._create_advanced_settings()

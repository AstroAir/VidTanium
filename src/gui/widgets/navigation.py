"""
Navigation System for VidTanium
Modern navigation patterns with smooth animations and improved UX
"""

from typing import Dict, List, Optional, Callable
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, QByteArray
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QFont, QPainter, QPainterPath, QColor

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, FluentIcon as FIF,
    ElevatedCardWidget, TransparentToolButton, BodyLabel, TitleLabel,
    Theme, isDarkTheme
)

from ..utils.design_system import DesignSystem, AnimatedCard


class NavigationItem(AnimatedCard):
    """Navigation item with modern styling and animations"""
    
    clicked = Signal(str)
    
    def __init__(self, route_key: str, icon: FIF, text: str, badge_count: int = 0, parent=None) -> None:
        super().__init__(parent)
        self.route_key = route_key
        self.icon = icon
        self.text = text
        self.badge_count = badge_count
        self.is_active = False
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self) -> None:
        """Setup the navigation item UI"""
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setPixmap(self.icon.icon().pixmap(24, 24))
        layout.addWidget(self.icon_label)
        
        # Text
        self.text_label = BodyLabel(self.text)
        self.text_label.setStyleSheet(DesignSystem.get_typography_style('body'))
        layout.addWidget(self.text_label)

        layout.addStretch()

        # Badge (if count > 0)
        if self.badge_count > 0:
            self.badge_label = self._create_badge()
            layout.addWidget(self.badge_label)

        self._update_styling()

    def _create_badge(self) -> QLabel:
        """Create notification badge"""
        badge = QLabel(str(self.badge_count))
        badge.setFixedSize(20, 20)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background: {DesignSystem.get_color('error')};
                color: white;
                border-radius: 10px;
                font-size: 10px;
                font-weight: 600;
            }}
        """)
        return badge
    
    def _setup_animations(self) -> None:
        """Setup smooth animations"""
        self.slide_animation = QPropertyAnimation(self, QByteArray(b"geometry"))
        self.slide_animation.setDuration(250)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def _update_styling(self) -> None:
        """Update styling based on active state"""
        if self.is_active:
            self.setStyleSheet(f"""
                NavigationItem {{
                    background: {DesignSystem.get_color('primary')};
                    border: 1px solid {DesignSystem.get_color('primary')};
                    border-radius: {DesignSystem.RADIUS['lg']}px;
                }}
            """)
            self.text_label.setStyleSheet("color: white; font-weight: 600;")
        else:
            self.setStyleSheet(f"""
                NavigationItem {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: {DesignSystem.RADIUS['lg']}px;
                }}
                NavigationItem:hover {{
                    background: {DesignSystem.get_color('surface_secondary_adaptive')};
                    border-color: {DesignSystem.get_color('border_adaptive')};
                }}
            """)
            color = DesignSystem.get_color('text_primary_adaptive')
            self.text_label.setStyleSheet(f"color: {color};")
    
    def set_active(self, active: bool) -> None:
        """Set active state with animation"""
        if self.is_active != active:
            self.is_active = active
            self._update_styling()
    
    def update_badge(self, count: int) -> None:
        """Update badge count"""
        self.badge_count = count
        if hasattr(self, 'badge_label'):
            if count > 0:
                self.badge_label.setText(str(count))
                self.badge_label.show()
            else:
                self.badge_label.hide()
    
    def mousePressEvent(self, event) -> None:
        """Handle click event"""
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.route_key)


class NavigationPanel(ElevatedCardWidget):
    """Navigation panel with modern design"""

    route_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.navigation_items: Dict[str, NavigationItem] = {}
        self.current_route = ""

        self._setup_ui()
        self._setup_styling()
    
    def _setup_ui(self) -> None:
        """Setup the navigation panel UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 16, 12, 16)
        self.main_layout.setSpacing(8)
        
        # Header
        self.header = self._create_header()
        self.main_layout.addWidget(self.header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"""
            QFrame {{
                color: {DesignSystem.get_color('border_adaptive')};
                margin: 8px 0px;
            }}
        """)
        self.main_layout.addWidget(separator)
        
        # Navigation items container
        self.nav_container = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(4)
        
        self.main_layout.addWidget(self.nav_container)
        self.main_layout.addStretch()
    
    def _create_header(self) -> QWidget:
        """Create navigation header"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 0, 8, 0)
        
        # App icon and title
        title = TitleLabel("VidTanium")
        title.setStyleSheet(f"""
            {DesignSystem.get_typography_style('title')}
            color: {DesignSystem.get_color('text_primary_adaptive')};
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Settings button
        settings_btn = TransparentToolButton(FIF.SETTING)
        settings_btn.setFixedSize(32, 32)
        settings_btn.clicked.connect(lambda: self.route_changed.emit('settings'))
        layout.addWidget(settings_btn)
        
        return header
    
    def _setup_styling(self) -> None:
        """Setup panel styling"""
        self.setFixedWidth(280)
        self.setStyleSheet(f"""
            NavigationPanel {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['xl']}px;
            }}
        """)

        # Add shadow effect
        shadow = DesignSystem.create_shadow_effect('lg')
        self.setGraphicsEffect(shadow)

    def add_navigation_item(self, route_key: str, icon: FIF, text: str, badge_count: int = 0) -> None:
        """Add navigation item"""
        item = NavigationItem(route_key, icon, text, badge_count)
        item.clicked.connect(self._on_item_clicked)

        self.navigation_items[route_key] = item
        self.nav_layout.addWidget(item)
    
    def add_separator(self) -> None:
        """Add separator between navigation groups"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"""
            QFrame {{
                color: {DesignSystem.get_color('border_adaptive')};
                margin: 8px 16px;
            }}
        """)
        self.nav_layout.addWidget(separator)
    
    def set_active_route(self, route_key: str) -> None:
        """Set active navigation route"""
        if self.current_route == route_key:
            return
        
        # Deactivate current item
        if self.current_route in self.navigation_items:
            self.navigation_items[self.current_route].set_active(False)
        
        # Activate new item
        if route_key in self.navigation_items:
            self.navigation_items[route_key].set_active(True)
            self.current_route = route_key
    
    def update_badge(self, route_key: str, count: int) -> None:
        """Update badge count for navigation item"""
        if route_key in self.navigation_items:
            self.navigation_items[route_key].update_badge(count)
    
    def _on_item_clicked(self, route_key: str) -> None:
        """Handle navigation item click"""
        self.set_active_route(route_key)
        self.route_changed.emit(route_key)


class ModernBreadcrumb(QWidget):
    """Modern breadcrumb navigation"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.breadcrumb_items: List[str] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup breadcrumb UI"""
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
    
    def set_breadcrumb(self, items: List[str]) -> None:
        """Set breadcrumb items"""
        # Clear existing items
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.breadcrumb_items = items
        
        for i, item in enumerate(items):
            # Add item label
            label = BodyLabel(item)
            if i == len(items) - 1:  # Last item (current page)
                label.setStyleSheet(f"""
                    color: {DesignSystem.get_color('text_primary_adaptive')};
                    font-weight: 600;
                """)
            else:
                label.setStyleSheet(f"""
                    color: {DesignSystem.get_color('text_secondary_adaptive')};
                """)
                label.setCursor(Qt.CursorShape.PointingHandCursor)

            self._layout.addWidget(label)

            # Add separator (except for last item)
            if i < len(items) - 1:
                separator = BodyLabel("/")
                separator.setStyleSheet(f"""
                    color: {DesignSystem.get_color('text_secondary_adaptive')};
                """)
                self._layout.addWidget(separator)

        self._layout.addStretch()

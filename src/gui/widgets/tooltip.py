"""
Tooltip Widget for VidTanium
Provides rich, interactive tooltips with detailed information and actions
"""

from typing import Optional, List, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QByteArray
from PySide6.QtGui import QFont, QPainter, QPainterPath, QColor, QPixmap

from qfluentwidgets import (
    FluentIcon as FIF, PushButton, TransparentToolButton,
    TitleLabel, BodyLabel, CaptionLabel, HyperlinkButton
)

from ..utils.i18n import tr


class Tooltip(QWidget):
    """Tooltip with rich content and interactive elements"""
    
    closed = Signal()
    action_clicked = Signal(str)  # action_id
    learn_more_clicked = Signal(str)  # url
    
    def __init__(
        self,
        title: str,
        description: str,
        detailed_info: Optional[str] = None,
        learn_more_url: Optional[str] = None,
        actions: Optional[List[dict]] = None,
        parent=None
    ) -> None:
        super().__init__(parent)
        
        self.title = title
        self.description = description
        self.detailed_info = detailed_info
        self.learn_more_url = learn_more_url
        self._actions = actions or []
        
        self.setWindowFlags(
            Qt.WindowType.ToolTip | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMaximumWidth(400)
        
        self._setup_ui()
        self._setup_animations()
        
        # Auto-hide timer
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.hide_with_animation)
        
        # Start auto-hide timer (10 seconds)
        self.auto_hide_timer.start(10000)
    
    def _setup_ui(self) -> None:
        """Setup the UI components"""
        # Main container with shadow effect
        self.container = QFrame()
        self.container.setObjectName("tooltip-container")
        self.container.setStyleSheet("""
            QFrame#tooltip-container {
                border-radius: 12px;
                padding: 0px;
            }
        """)
        
        # Layout for the entire tooltip
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.addWidget(self.container)
        
        # Container layout
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(16, 12, 16, 12)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Title
        title_label = BodyLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Close button
        close_button = TransparentToolButton(FIF.CLOSE)
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.hide_with_animation)
        header_layout.addWidget(close_button)
        
        container_layout.addLayout(header_layout)
        
        # Description
        desc_label = BodyLabel(self.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                line-height: 1.4;
            }
        """)
        container_layout.addWidget(desc_label)
        
        # Detailed information (collapsible)
        if self.detailed_info:
            self._add_detailed_info(container_layout)
        
        # Actions
        if self._actions:
            self._add_actions(container_layout)
        
        # Learn more link
        if self.learn_more_url:
            learn_more_link = HyperlinkButton(
                url=self.learn_more_url,
                text=tr("tooltip.learn_more")
            )
            learn_more_link.clicked.connect(
                lambda: self.learn_more_clicked.emit(self.learn_more_url)
            )
            container_layout.addWidget(learn_more_link)
    
    def _add_detailed_info(self, layout: QVBoxLayout) -> None:
        """Add detailed information section"""
        # Expandable section
        self.details_expanded = False
        
        # Toggle button
        self.details_toggle = PushButton(tr("tooltip.show_details"))
        self.details_toggle.setIcon(FIF.CHEVRON_DOWN)
        self.details_toggle.clicked.connect(self._toggle_details)
        self.details_toggle.setObjectName("details-toggle")
        self.details_toggle.setStyleSheet("""
            QPushButton#details-toggle {
                background: transparent;
                border-radius: 6px;
                padding: 4px 8px;
                text-align: left;
            }
        """)
        layout.addWidget(self.details_toggle)
        
        # Details content (initially hidden)
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = BodyLabel(self.detailed_info)
        details_label.setWordWrap(True)
        details_label.setObjectName("details-label")
        details_label.setStyleSheet("""
            QLabel#details-label {
                border-radius: 6px;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        details_layout.addWidget(details_label)
        
        self.details_widget.setVisible(False)
        layout.addWidget(self.details_widget)
    
    def _add_actions(self, layout: QVBoxLayout) -> None:
        """Add action buttons"""
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        for action in self._actions:
            action_button = PushButton(action.get("title", "Action"))
            
            # Set icon if provided
            icon_name = action.get("icon")
            if icon_name and hasattr(FIF, icon_name.upper()):
                action_button.setIcon(getattr(FIF, icon_name.upper()))
            
            # Set style based on priority
            priority = action.get("priority", "medium")
            if priority == "high":
                action_button.setObjectName("action-button-high")
                action_button.setStyleSheet("""
                    QPushButton#action-button-high {
                        border: none;
                        border-radius: 6px;
                        font-weight: bold;
                        padding: 6px 12px;
                    }
                """)
            else:
                action_button.setObjectName("action-button-normal")
                action_button.setStyleSheet("""
                    QPushButton#action-button-normal {
                        background: transparent;
                        border-radius: 6px;
                        padding: 6px 12px;
                    }
                """)
            
            # Connect click handler
            action_id = action.get("id", "")
            action_button.clicked.connect(
                lambda checked, aid=action_id: self.action_clicked.emit(aid)
            )
            
            actions_layout.addWidget(action_button)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
    
    def _setup_animations(self) -> None:
        """Setup show/hide animations"""
        self.fade_animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.scale_animation = QPropertyAnimation(self, QByteArray(b"geometry"))
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutBack)
    
    def _toggle_details(self) -> None:
        """Toggle detailed information visibility"""
        self.details_expanded = not self.details_expanded
        
        if self.details_expanded:
            self.details_widget.setVisible(True)
            self.details_toggle.setText(tr("tooltip.hide_details"))
            self.details_toggle.setIcon(FIF.CHEVRON_UP)
        else:
            self.details_widget.setVisible(False)
            self.details_toggle.setText(tr("tooltip.show_details"))
            self.details_toggle.setIcon(FIF.CHEVRON_DOWN)
        
        # Adjust size
        self.adjustSize()
    
    def show_at_position(self, position: QPoint) -> None:
        """Show tooltip at specific position with animation"""
        # Calculate optimal position to stay within screen bounds
        screen = QApplication.primaryScreen().geometry()
        tooltip_size = self.sizeHint()
        
        x = position.x()
        y = position.y() - tooltip_size.height() - 10  # Show above cursor
        
        # Adjust if tooltip would go off screen
        if x + tooltip_size.width() > screen.right():
            x = screen.right() - tooltip_size.width() - 10
        if x < screen.left():
            x = screen.left() + 10
        if y < screen.top():
            y = position.y() + 20  # Show below cursor instead
        
        # Set initial state for animation
        self.setWindowOpacity(0.0)
        self.move(x, y)
        self.show()
        
        # Animate appearance
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        # Reset auto-hide timer
        self.auto_hide_timer.start(10000)
    
    def hide_with_animation(self) -> None:
        """Hide tooltip with fade animation"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self._on_hide_finished)
        self.fade_animation.start()
    
    def _on_hide_finished(self) -> None:
        """Handle hide animation completion"""
        self.hide()
        self.closed.emit()
        self.fade_animation.finished.disconnect()
    
    def enterEvent(self, event) -> None:
        """Handle mouse enter - stop auto-hide timer"""
        self.auto_hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave - restart auto-hide timer"""
        self.auto_hide_timer.start(3000)  # Shorter delay after mouse leave
        super().leaveEvent(event)
    
    def paintEvent(self, event) -> None:
        """Custom paint event for shadow effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw shadow
        shadow_rect = self.container.geometry().adjusted(-4, -4, 4, 4)
        shadow_color = QColor(0, 0, 0, 30)
        
        for i in range(4):
            painter.setPen(QColor(0, 0, 0, 30 - i * 7))
            painter.drawRoundedRect(
                shadow_rect.adjusted(i, i, -i, -i),
                12 - i, 12 - i
            )
        
        super().paintEvent(event)


class SmartTooltipMixin:
    """Mixin class to add smart tooltip functionality to widgets"""
    
    def __init__(self) -> None:
        self.tooltip_manager = None
        self.help_context = None
        self.help_key = None
    
    def set_contextual_help(
        self,
        tooltip_manager,
        context: str,
        help_key: str
    ) -> None:
        """Set contextual help for this widget"""
        self.tooltip_manager = tooltip_manager
        self.help_context = context
        self.help_key = help_key
    
    def enterEvent(self, event) -> None:
        """Show contextual help on mouse enter"""
        if (self.tooltip_manager and 
            self.help_context and 
            self.help_key and
            self.tooltip_manager.should_show_help(self.help_key)):
            
            self.tooltip_manager.show_contextual_help(
                self, self.help_context, self.help_key
            )
        
        # Call parent implementation if available
        pass
    
    def leaveEvent(self, event) -> None:
        """Hide contextual help on mouse leave"""
        if self.tooltip_manager:
            self.tooltip_manager.hide_contextual_help(self)
        
        # Call parent implementation if available
        pass


# Factory function for creating quick tooltips
# Backward compatibility alias
EnhancedTooltip = Tooltip


def create_quick_tooltip(
    title: str,
    description: str,
    position: QPoint,
    parent=None
) -> EnhancedTooltip:
    """Create and show a quick tooltip"""
    tooltip = EnhancedTooltip(
        title=title,
        description=description,
        parent=parent
    )
    tooltip.show_at_position(position)
    return tooltip

"""
Design System for VidTanium
Modern design patterns and components using QFluentWidgets 1.8.7
"""

from typing import Dict, Any, Optional, Union
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient

from qfluentwidgets import (
    ElevatedCardWidget, HeaderCardWidget, FluentIcon as FIF,
    Theme, isDarkTheme, qconfig
)


class DesignSystem:
    """Design system with modern patterns"""

    # Color Palette
    COLORS = {
        # Primary Colors
        'primary': '#0078D4',
        'primary_light': '#106EBE',
        'primary_dark': '#005A9E',
        
        # Accent Colors
        'accent_blue': '#0078D4',
        'accent_purple': '#8764B8',
        'accent_teal': '#00BCF2',
        'accent_green': '#107C10',
        
        # Semantic Colors
        'success': '#107C10',
        'warning': '#FF8C00',
        'error': '#D13438',
        'info': '#0078D4',
        
        # Neutral Colors (Light Theme)
        'surface_light': '#FFFFFF',
        'surface_secondary_light': '#F9F9F9',
        'surface_tertiary_light': '#F3F3F3',
        'border_light': '#E5E5E5',
        'text_primary_light': '#323130',
        'text_secondary_light': '#605E5C',
        
        # Neutral Colors (Dark Theme)
        'surface_dark': '#1E1E1E',
        'surface_secondary_dark': '#2D2D2D',
        'surface_tertiary_dark': '#3C3C3C',
        'border_dark': '#484644',
        'text_primary_dark': '#FFFFFF',
        'text_secondary_dark': '#C8C6C4',
    }
    
    # Typography Scale
    TYPOGRAPHY = {
        'display': {'size': 28, 'weight': 600, 'line_height': 1.2},
        'title_large': {'size': 22, 'weight': 600, 'line_height': 1.3},
        'title': {'size': 18, 'weight': 600, 'line_height': 1.4},
        'subtitle': {'size': 16, 'weight': 500, 'line_height': 1.4},
        'body_large': {'size': 14, 'weight': 400, 'line_height': 1.5},
        'body': {'size': 13, 'weight': 400, 'line_height': 1.5},
        'caption': {'size': 11, 'weight': 400, 'line_height': 1.4},
    }

    # Spacing System
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 12,
        'lg': 16,
        'xl': 20,
        'xxl': 24,
        'xxxl': 32,
    }

    # Border Radius
    RADIUS = {
        'sm': 4,
        'md': 6,
        'lg': 8,
        'xl': 12,
        'xxl': 16,
        'round': 50,
    }
    
    # Shadows
    SHADOWS = {
        'sm': {'blur': 4, 'offset': 2, 'alpha': 0.1},
        'md': {'blur': 8, 'offset': 4, 'alpha': 0.15},
        'lg': {'blur': 16, 'offset': 8, 'alpha': 0.2},
        'xl': {'blur': 24, 'offset': 12, 'alpha': 0.25},
    }
    
    @classmethod
    def get_color(cls, color_key: str) -> str:
        """Get color based on current theme"""
        if color_key in cls.COLORS:
            return cls.COLORS[color_key]
        
        # Handle theme-specific colors
        is_dark = isDarkTheme()
        if color_key.endswith('_adaptive'):
            base_key = color_key.replace('_adaptive', '')
            suffix = '_dark' if is_dark else '_light'
            return cls.COLORS.get(f"{base_key}{suffix}", cls.COLORS.get(base_key, '#000000'))
        
        return '#000000'
    
    @classmethod
    def get_typography_style(cls, style_key: str) -> str:
        """Get typography CSS style"""
        if style_key not in cls.TYPOGRAPHY:
            style_key = 'body'
        
        style = cls.TYPOGRAPHY[style_key]
        return f"""
            font-size: {style['size']}px;
            font-weight: {style['weight']};
            line-height: {style['line_height']};
        """
    
    @classmethod
    def create_shadow_effect(cls, shadow_key: str = 'md') -> QGraphicsDropShadowEffect:
        """Create enhanced shadow effect"""
        shadow_config = cls.SHADOWS.get(shadow_key, cls.SHADOWS['md'])
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config['blur'])
        shadow.setOffset(0, shadow_config['offset'])
        shadow.setColor(QColor(0, 0, 0, int(255 * shadow_config['alpha'])))
        
        return shadow


class AnimatedCard(ElevatedCardWidget):
    """Enhanced card with smooth animations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_animations()
        self._setup_enhanced_styling()
    
    def _setup_animations(self):
        """Setup hover animations"""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.hover_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.scale_timer = QTimer()
        self.scale_timer.setSingleShot(True)
        self.scale_timer.timeout.connect(self._apply_hover_scale)
    
    def _setup_enhanced_styling(self):
        """Apply enhanced styling"""
        self.setStyleSheet(f"""
            AnimatedCard {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['lg']}px;
                padding: {DesignSystem.SPACING['lg']}px;
            }}
            AnimatedCard:hover {{
                border-color: {DesignSystem.get_color('primary')};
                background: {DesignSystem.get_color('surface_secondary_adaptive')};
            }}
        """)

        # Add shadow effect
        shadow = DesignSystem.create_shadow_effect('md')
        self.setGraphicsEffect(shadow)
    
    def enterEvent(self, event):
        """Enhanced hover enter effect"""
        super().enterEvent(event)
        self.hover_animation.setStartValue(1.0)
        self.hover_animation.setEndValue(0.95)
        self.hover_animation.start()
        
        self.scale_timer.start(50)
    
    def leaveEvent(self, event):
        """Enhanced hover leave effect"""
        super().leaveEvent(event)
        self.hover_animation.setStartValue(0.95)
        self.hover_animation.setEndValue(1.0)
        self.hover_animation.start()
    
    def _apply_hover_scale(self):
        """Apply subtle scale effect"""
        # This would be implemented with a custom scale animation
        pass


class GradientCard(ElevatedCardWidget):
    """Card with gradient background"""
    
    def __init__(self, gradient_colors: Optional[list] = None, parent=None):
        super().__init__(parent)
        self.gradient_colors = gradient_colors or [
            DesignSystem.get_color('primary'),
            DesignSystem.get_color('accent_purple')
        ]
        self._setup_gradient_styling()

    def _setup_gradient_styling(self):
        """Setup gradient background"""
        gradient_css = f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {self.gradient_colors[0]},
                stop:1 {self.gradient_colors[1]});
        """

        self.setStyleSheet(f"""
            GradientCard {{
                {gradient_css}
                border: none;
                border-radius: {DesignSystem.RADIUS['xl']}px;
                color: white;
            }}
        """)


class ModernProgressCard(ElevatedCardWidget):
    """Modern progress card with enhanced visuals"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self._setup_modern_styling()
    
    def _setup_modern_styling(self):
        """Setup modern progress card styling"""
        self.setStyleSheet(f"""
            ModernProgressCard {{
                background: {DesignSystem.get_color('surface_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['xl']}px;
                padding: {DesignSystem.SPACING['xl']}px;
            }}
        """)

        # Add enhanced shadow
        shadow = DesignSystem.create_shadow_effect('lg')
        self.setGraphicsEffect(shadow)


class IconButton(ElevatedCardWidget):
    """Icon button with modern styling"""

    def __init__(self, icon: FIF, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.icon = icon
        self.tooltip_text = tooltip
        self._setup_icon_button()

    def _setup_icon_button(self):
        """Setup enhanced icon button"""
        self.setFixedSize(48, 48)
        self.setToolTip(self.tooltip_text)

        self.setStyleSheet(f"""
            IconButton {{
                background: {DesignSystem.get_color('surface_secondary_adaptive')};
                border: 1px solid {DesignSystem.get_color('border_adaptive')};
                border-radius: {DesignSystem.RADIUS['round']}px;
            }}
            IconButton:hover {{
                background: {DesignSystem.get_color('primary')};
                border-color: {DesignSystem.get_color('primary')};
            }}
        """)


# Backward compatibility aliases
EnhancedDesignSystem = DesignSystem

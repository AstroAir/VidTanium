"""
VidTanium Unified Design System
Modern Fluent Design theme with consistent styling across all components
"""

from typing import Dict, Any, List, Optional


class VidTaniumTheme:
    """Unified design system for VidTanium application"""

    # ========================================
    # COLOR PALETTE
    # ========================================

    # Primary Colors
    PRIMARY_BLUE = "#667eea"
    PRIMARY_PURPLE = "#764ba2"
    ACCENT_CYAN = "#4facfe"
    ACCENT_GREEN = "#00f2fe"

    # Status Colors
    SUCCESS_GREEN = "#11998e"
    SUCCESS_LIGHT = "#38ef7d"
    WARNING_ORANGE = "#ffa726"
    WARNING_LIGHT = "#fb8c00"
    ERROR_RED = "#ff416c"
    ERROR_DARK = "#ff4757"
    INFO_BLUE = "#0078d4"
    PENDING_BLUE = "#74b9ff"

    # Neutral Colors
    TEXT_PRIMARY = "#323130"
    TEXT_SECONDARY = "#605e5c"
    TEXT_TERTIARY = "#8a8886"
    TEXT_WHITE = "#ffffff"
    TEXT_WHITE_SECONDARY = "#f0f0f0"  # Changed from rgba to solid light gray
    TEXT_WHITE_TERTIARY = "#e0e0e0"   # Changed from rgba to solid light gray
    TEXT_DISABLED = "#a19f9d"  # Disabled text color

    # Background Colors
    BG_PRIMARY = "#ffffff"
    BG_SECONDARY = "#faf9f8"
    BG_CARD = "#ffffff"  # Changed from rgba to solid white
    BG_CARD_HOVER = "#f5f5f5"  # Changed from rgba to solid light gray
    BG_OVERLAY = "#fefefe"  # Changed from rgba to very light gray
    BG_SURFACE = "#fdfdfd"  # Changed from rgba to very light gray

    # Border Colors
    BORDER_LIGHT = "#e5e5e5"  # Changed from rgba to solid light gray
    BORDER_MEDIUM = "#d0d0d0"  # Changed from rgba to solid gray
    BORDER_ACCENT = "#0078d4"  # Changed from rgba to solid blue
    BORDER_COLOR = "#d0d0d0"  # Alias for BORDER_MEDIUM

    # ========================================
    # GRADIENTS
    # ========================================

    GRADIENT_PRIMARY = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {PRIMARY_BLUE}, stop:1 {PRIMARY_PURPLE})"
    GRADIENT_SUCCESS = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {SUCCESS_GREEN}, stop:1 {SUCCESS_LIGHT})"
    GRADIENT_WARNING = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {WARNING_ORANGE}, stop:1 {WARNING_LIGHT})"
    GRADIENT_ERROR = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ERROR_RED}, stop:1 {ERROR_DARK})"
    GRADIENT_INFO = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_CYAN}, stop:1 {ACCENT_GREEN})"

    # Hero Section Gradients
    GRADIENT_HERO = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PRIMARY_BLUE}, stop:0.5 {PRIMARY_PURPLE}, stop:1 {ACCENT_CYAN})"
    GRADIENT_HERO_OVERLAY = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(102, 126, 234, 0.9), stop:1 rgba(118, 75, 162, 0.95))"

    # ========================================
    # TYPOGRAPHY
    # ========================================

    # Font Families
    FONT_PRIMARY = "'Segoe UI', 'Microsoft YaHei', sans-serif"
    FONT_MONOSPACE = "'Cascadia Code', 'Consolas', 'Monaco', monospace"

    # Font Sizes
    FONT_SIZE_HERO = "28px"
    FONT_SIZE_TITLE = "24px"
    FONT_SIZE_SUBTITLE = "20px"
    FONT_SIZE_HEADING = "18px"
    FONT_SIZE_SUBHEADING = "16px"
    FONT_SIZE_BODY = "14px"
    FONT_SIZE_CAPTION = "12px"
    FONT_SIZE_SMALL = "11px"
    FONT_SIZE_MICRO = "10px"

    # Font Weights
    FONT_WEIGHT_LIGHT = "300"
    FONT_WEIGHT_REGULAR = "400"
    FONT_WEIGHT_MEDIUM = "500"
    FONT_WEIGHT_SEMIBOLD = "600"
    FONT_WEIGHT_BOLD = "700"

    # ========================================
    # SPACING & SIZING
    # ========================================

    # Spacing Scale
    SPACE_XS = "4px"
    SPACE_SM = "8px"
    SPACE_MD = "12px"
    SPACE_LG = "16px"
    SPACE_XL = "20px"
    SPACE_XXL = "24px"
    SPACE_XXXL = "32px"

    # Border Radius
    RADIUS_SMALL = "6px"
    RADIUS_MEDIUM = "8px"
    RADIUS_LARGE = "12px"
    RADIUS_XLARGE = "16px"

    # Card Dimensions
    CARD_STAT_WIDTH = "80px"
    CARD_STAT_HEIGHT = "50px"
    CARD_ACTION_HEIGHT = "32px"
    CARD_MIN_HEIGHT = "120px"

    # ========================================
    # SHADOWS & EFFECTS
    # ========================================

    SHADOW_LIGHT = "0 2px 8px rgba(0, 0, 0, 0.1)"
    SHADOW_MEDIUM = "0 4px 16px rgba(0, 0, 0, 0.15)"
    SHADOW_HEAVY = "0 8px 32px rgba(0, 0, 0, 0.2)"
    SHADOW_COLORED = "0 4px 20px rgba(102, 126, 234, 0.3)"

    # ========================================
    # COMPONENT STYLES
    # ========================================

    @classmethod
    def get_card_style(cls, hover_enabled: bool = True) -> str:
        """Get unified card styling"""
        hover_style = f"""
            CardWidget:hover {{
                background-color: {cls.BG_CARD_HOVER};
                border: 1px solid {cls.BORDER_ACCENT};
            }}
        """ if hover_enabled else ""

        return f"""
            CardWidget {{
                background-color: {cls.BG_CARD};
                border: 1px solid {cls.BORDER_LIGHT};
                border-radius: {cls.RADIUS_LARGE};
                padding: 0px;
            }}
            {hover_style}
        """

    @classmethod
    def get_stat_card_style(cls, gradient_colors: Optional[List[str]] = None) -> str:
        """Get unified stats card styling"""
        if gradient_colors:
            background = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {gradient_colors[0]}, stop:1 {gradient_colors[1]})"
        else:
            background = cls.GRADIENT_PRIMARY

        return f"""
            CardWidget {{
                background: {background};
                border: none;
                border-radius: {cls.RADIUS_LARGE};
            }}
        """

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> str:
        """Get unified button styling"""
        if variant == "primary":
            return f"""
                PushButton {{
                    background: {cls.GRADIENT_PRIMARY};
                    border: none;
                    border-radius: {cls.RADIUS_MEDIUM};
                    color: {cls.TEXT_WHITE};
                    font-weight: {cls.FONT_WEIGHT_SEMIBOLD};
                    padding: {cls.SPACE_SM} {cls.SPACE_LG};
                    font-size: {cls.FONT_SIZE_BODY};
                }}
                PushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #5a6fd8, stop:1 #6a4190);
                }}
                PushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #4a5fc8, stop:1 #5a3180);
                }}
            """
        elif variant == "secondary":
            return f"""
                PushButton {{
                    background-color: {cls.BG_CARD};
                    border: 1px solid {cls.BORDER_MEDIUM};
                    border-radius: {cls.RADIUS_MEDIUM};
                    color: {cls.TEXT_PRIMARY};
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                    padding: {cls.SPACE_SM} {cls.SPACE_LG};
                    font-size: {cls.FONT_SIZE_BODY};
                }}
                PushButton:hover {{
                    background-color: {cls.BG_CARD_HOVER};
                    border-color: {cls.BORDER_ACCENT};
                }}
            """
        else:  # minimal
            return f"""
                PushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: {cls.RADIUS_MEDIUM};
                    color: {cls.TEXT_SECONDARY};
                    font-weight: {cls.FONT_WEIGHT_MEDIUM};
                    padding: {cls.SPACE_SM} {cls.SPACE_MD};
                    font-size: {cls.FONT_SIZE_BODY};
                }}
                PushButton:hover {{
                    background-color: {cls.BG_OVERLAY};
                    color: {cls.TEXT_PRIMARY};
                }}
            """

    @classmethod
    def get_header_style(cls) -> str:
        """Get unified header styling"""
        return f"""
            CardWidget {{
                background: {cls.GRADIENT_PRIMARY};
                border: none;
                border-radius: {cls.RADIUS_LARGE};
                color: {cls.TEXT_WHITE};
            }}
        """

    @classmethod
    def get_progress_bar_style(cls) -> str:
        """Get unified progress bar styling"""
        return f"""
            ProgressBar {{
                background-color: {cls.BG_OVERLAY};
                border-radius: 3px;
                text-align: center;
            }}
            ProgressBar::chunk {{
                background: {cls.GRADIENT_PRIMARY};
                border-radius: 3px;
            }}
        """

    @classmethod
    def get_status_badge_style(cls, status: str) -> str:
        """Get status badge styling by status type"""
        status_gradients = {
            "downloading": cls.GRADIENT_INFO,
            "completed": cls.GRADIENT_SUCCESS,
            "failed": cls.GRADIENT_ERROR,
            "paused": cls.GRADIENT_WARNING,
            "pending": f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.PENDING_BLUE}, stop:1 {cls.INFO_BLUE})",
            "cancelled": f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #636e72, stop:1 #2d3436)",
            "default": cls.GRADIENT_PRIMARY
        }

        gradient = status_gradients.get(status, status_gradients["default"])

        return f"""
            QLabel {{
                background: {gradient};
                color: {cls.TEXT_WHITE};
                border-radius: {cls.RADIUS_LARGE};
                padding: {cls.SPACE_XS} {cls.SPACE_MD};
                font-size: {cls.FONT_SIZE_SMALL};
                font-weight: {cls.FONT_WEIGHT_SEMIBOLD};
            }}
        """

    @classmethod
    def get_empty_state_style(cls) -> str:
        """Get unified empty state styling"""
        return f"""
            QWidget {{
                background-color: {cls.BG_CARD};
                border-radius: {cls.RADIUS_LARGE};
                border: 2px dashed {cls.BORDER_MEDIUM};
            }}
        """

    @classmethod
    def get_search_box_style(cls, for_header: bool = False) -> str:
        """Get unified search box styling"""
        if for_header:
            return f"""
                SearchLineEdit {{
                    background-color: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: {cls.RADIUS_MEDIUM};
                    padding: {cls.SPACE_SM} {cls.SPACE_MD};
                    color: {cls.TEXT_WHITE};
                    font-size: {cls.FONT_SIZE_BODY};
                }}
                SearchLineEdit::placeholder {{
                    color: {cls.TEXT_WHITE_TERTIARY};
                }}
            """
        else:
            return f"""
                SearchLineEdit {{
                    background-color: {cls.BG_CARD};
                    border: 1px solid {cls.BORDER_LIGHT};
                    border-radius: {cls.RADIUS_MEDIUM};
                    padding: {cls.SPACE_SM} {cls.SPACE_MD};
                    color: {cls.TEXT_PRIMARY};
                    font-size: {cls.FONT_SIZE_BODY};
                }}
                SearchLineEdit:focus {{
                    border-color: {cls.BORDER_ACCENT};
                }}
            """

    # ========================================
    # RESPONSIVE DESIGN UTILITIES
    # ========================================

    @classmethod
    def get_responsive_font_size(cls, base_size: str, scale_factor: float = 1.0) -> str:
        """Get responsive font size based on scale factor"""
        base_value = int(base_size.replace('px', ''))
        scaled_value = max(8, int(base_value * scale_factor))  # Minimum 8px
        return f"{scaled_value}px"

    @classmethod
    def get_responsive_spacing(cls, base_spacing: str, scale_factor: float = 1.0) -> str:
        """Get responsive spacing based on scale factor"""
        base_value = int(base_spacing.replace('px', ''))
        scaled_value = max(2, int(base_value * scale_factor))  # Minimum 2px
        return f"{scaled_value}px"

    @classmethod
    def get_responsive_card_style(cls, hover_enabled: bool = True, scale_factor: float = 1.0) -> str:
        """Get responsive card styling with scaling"""
        padding = cls.get_responsive_spacing(cls.SPACE_LG, scale_factor)
        border_radius = cls.get_responsive_spacing(
            cls.RADIUS_LARGE, scale_factor)

        hover_style = f"""
            CardWidget:hover {{
                background-color: {cls.BG_CARD_HOVER};
                border: 1px solid {cls.BORDER_ACCENT};
            }}
        """ if hover_enabled else ""

        return f"""
            CardWidget {{
                background-color: {cls.BG_CARD};
                border: 1px solid {cls.BORDER_LIGHT};
                border-radius: {border_radius};
                padding: {padding};
            }}
            {hover_style}
        """

    @classmethod
    def get_adaptive_margins(cls, container_width: int) -> tuple:
        """Get adaptive margins based on container width"""
        if container_width < 800:
            return (12, 12, 12, 12)  # Small margins for narrow screens
        elif container_width < 1200:
            return (16, 16, 16, 16)  # Medium margins
        else:
            return (24, 24, 24, 24)  # Large margins for wide screens

    @classmethod
    def get_adaptive_spacing(cls, container_width: int) -> int:
        """Get adaptive spacing based on container width"""
        if container_width < 800:
            return 8   # Tight spacing for narrow screens
        elif container_width < 1200:
            return 12  # Medium spacing
        else:
            return 16  # Generous spacing for wide screens


class ThemeManager:
    """Helper class for applying unified theme across components"""

    @staticmethod
    def apply_theme_to_widget(widget, theme_method: str, **kwargs) -> None:
        """Apply theme styling to a widget"""
        try:
            style_method = getattr(VidTaniumTheme, theme_method)
            style = style_method(**kwargs)
            widget.setStyleSheet(style)
        except Exception as e:
            print(f"Error applying theme: {e}")

    @staticmethod
    def get_shadow_effect(blur_radius: int = 12, offset_y: int = 2, color_alpha: int = 50):
        """Create shadow effects for elevation"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(0, offset_y)
        shadow.setColor(QColor(0, 0, 0, color_alpha))
        return shadow

    @staticmethod
    def get_colored_shadow_effect(color: str = VidTaniumTheme.PRIMARY_BLUE, alpha: int = 50):
        """Create colored shadow effects for accent elements"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        color_obj = QColor(color)
        color_obj.setAlpha(alpha)
        shadow.setColor(color_obj)
        return shadow
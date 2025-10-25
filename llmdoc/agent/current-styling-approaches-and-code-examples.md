# Current Styling Approaches and Code Examples

## Overview

VidTanium uses multiple styling approaches across the codebase. This document catalogs all current patterns with complete code examples for reference during design system implementation.

## Part 1: Evidence - Styling Approach Examples

### Approach 1: Inline Stylesheet with DesignSystem Utilities

**Location:** `d:\Project\VidTanium\src\gui\widgets\progress.py` (lines 49-112)
**Pattern:** F-string stylesheet generation using DesignSystem helper methods
**Frequency:** Most common approach across newer components

```python
class ProgressCard(AnimatedCard):
    def _setup_ui(self) -> None:
        # Title label styling
        self.title_label = BodyLabel(self.title)
        self.title_label.setStyleSheet(f"""
            {DesignSystem.get_typography_style('body')}
            color: {DesignSystem.get_color('text_primary_adaptive')};
            font-weight: 600;
        """)
        layout.addWidget(self.title_label)

        # Progress bar with gradient
        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(f"""
            ProgressBar {{
                background: {DesignSystem.get_color('surface_tertiary_adaptive')};
                border-radius: 4px;
            }}
            ProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {DesignSystem.get_color('primary')},
                    stop:1 {DesignSystem.get_color('accent_blue')});
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Progress info labels
        self.progress_label = CaptionLabel("0%")
        self.progress_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_secondary_adaptive')};
            font-weight: 500;
        """)

        self.speed_label = CaptionLabel(self.speed)
        self.speed_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_secondary_adaptive')};
        """)

        self.eta_label = CaptionLabel(f"ETA: {self.eta}")
        self.eta_label.setStyleSheet(f"""
            color: {DesignSystem.get_color('text_secondary_adaptive')};
        """)
```

**Advantages:**
- Centralized color management via DesignSystem.get_color()
- Adaptive colors handle light/dark themes
- Readable f-string format
- Reusable typography styles via get_typography_style()

**Disadvantages:**
- Stylesheet strings scattered throughout code
- Hard to maintain complex stylesheets
- Performance cost of generating strings repeatedly
- No CSS syntax highlighting in Python files

### Approach 2: VidTaniumTheme Class Constants

**Location:** `d:\Project\VidTanium\src\gui\widgets\task_manager.py` (lines 48-64)
**Pattern:** Reference VidTaniumTheme class constants directly
**Frequency:** Older/legacy components

```python
class ModernStatusBadge(QLabel):
    def _setup_style(self) -> None:
        """Setup style based on status type"""
        colors = {
            'running': f'background: {VidTaniumTheme.SUCCESS_GREEN}; color: white;',
            'paused': f'background: {VidTaniumTheme.WARNING_ORANGE}; color: white;',
            'completed': f'background: {VidTaniumTheme.ACCENT_CYAN}; color: white;',
            'failed': f'background: {VidTaniumTheme.ERROR_RED}; color: white;',
            'default': f'background: {VidTaniumTheme.BG_SURFACE}; '
                      f'color: {VidTaniumTheme.TEXT_PRIMARY};'
        }
        base_style = f"""
            QLabel {{
                {colors.get(self.status_type, colors['default'])}
                border-radius: 12px;
                padding: 4px 8px;
                font-weight: 600;
                font-size: 11px;
            }}
        """
        self.setStyleSheet(base_style)

    def update_status(self, status_type: str, text: str) -> None:
        if self.status_type != status_type:
            self.status_type = status_type
            self.setText(text)
            self._setup_style()
```

**Advantages:**
- Clear semantic naming (SUCCESS_GREEN, WARNING_ORANGE)
- Static class constants discoverable
- Direct RGB values visible in code

**Disadvantages:**
- No theme adaptation (always uses preset colors)
- Duplicate color definitions vs DesignSystem
- Different from DesignSystem pattern causes confusion
- No support for theme switching

### Approach 3: Direct isDarkTheme() Checks

**Location:** `d:\Project\VidTanium\src\gui\widgets\status_widget.py` (lines 64-97)
**Pattern:** Runtime theme detection in widget code
**Frequency:** Less common, but present in some components

```python
from qfluentwidgets import isDarkTheme

class StatusBadge(QWidget):
    def _setup_style(self) -> None:
        """Setup styling"""
        # Direct theme-aware colors
        if isDarkTheme():
            bg_color = VidTaniumTheme.DARK_THEME_COLORS.get("surface", "#1E293B")
            text_color = VidTaniumTheme.DARK_THEME_COLORS.get("text_primary", "#F8FAFC")
            border_color = VidTaniumTheme.DARK_THEME_COLORS.get("border", "#475569")
        else:
            bg_color = VidTaniumTheme.LIGHT_THEME_COLORS.get("surface", "#FFFFFF")
            text_color = VidTaniumTheme.LIGHT_THEME_COLORS.get("text_primary", "#323130")
            border_color = VidTaniumTheme.LIGHT_THEME_COLORS.get("border", "#E5E5E5")

        self.setStyleSheet(f"""
            QWidget {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 4px 12px;
                color: {text_color};
            }}
        """)

    def update_status(self, status: str, animated: bool = False):
        """Update status with color mapping"""
        status_colors = {
            "downloading": VidTaniumTheme.SUCCESS_GREEN,
            "paused": VidTaniumTheme.WARNING_ORANGE,
            "completed": VidTaniumTheme.ACCENT_CYAN,
            "failed": VidTaniumTheme.ERROR_RED,
        }

        self.status_color = status_colors.get(
            status.lower(), VidTaniumTheme.TEXT_SECONDARY)
        self.update()
```

**Advantages:**
- Explicit theme handling
- Easy to understand what colors apply to which theme
- Fine-grained control

**Disadvantages:**
- Theme logic scattered throughout widget code
- Difficult to refactor theme handling
- isDarkTheme() called at runtime in widgets
- Not responsive to theme changes unless update() called

### Approach 4: Graphics Effects and Animations

**Location:** `d:\Project\VidTanium\src\gui\widgets\progress.py` (lines 114-120)
**Pattern:** Animated progress with QPropertyAnimation
**Frequency:** Used for all animations

```python
class ProgressCard(AnimatedCard):
    def _setup_animations(self) -> None:
        """Setup progress animations"""
        if hasattr(self, 'progress_bar'):
            self.progress_animation = QPropertyAnimation(
                self.progress_bar, QByteArray(b"value"))
            self.progress_animation.setDuration(500)
            self.progress_animation.setEasingCurve(
                QEasingCurve.Type.OutCubic)

    def update_progress(self, value: int, speed: Optional[str] = None,
                       eta: Optional[str] = None) -> None:
        """Update progress with animation"""
        if hasattr(self, 'progress_animation'):
            self.progress_animation.setStartValue(self.progress_value)
            self.progress_animation.setEndValue(value)
            self.progress_animation.start()

        self.progress_value = value
        if hasattr(self, 'progress_label'):
            self.progress_label.setText(f"{value}%")
```

**Used in:**
- Progress value animations (OutCubic, 500ms)
- Opacity/fade transitions (200ms)
- Pulsing effects (InOutSine, 1000ms)
- Slide animations (250ms)

**Animation Parameters:**
| Animation Type | Duration | Easing Curve | Target |
|---|---|---|---|
| Progress bar | 500ms | OutCubic | value property |
| Fade in/out | 200ms | Linear | windowOpacity |
| Pulse | 1000ms | InOutSine | geometry |
| Slide | 250ms | OutCubic | position |
| Status change | 200ms | Linear | opacity |

### Approach 5: DesignSystem Shadow Factory

**Location:** `d:\Project\VidTanium\src\gui\utils\design_system.py` (lines 88-134)
**Pattern:** QGraphicsDropShadowEffect created from factory method
**Frequency:** Used for card and elevated widgets

```python
class DesignSystem:
    SHADOWS = {
        'sm': {'blur': 4, 'offset': 2, 'alpha': 0.1},
        'md': {'blur': 8, 'offset': 4, 'alpha': 0.15},
        'lg': {'blur': 16, 'offset': 8, 'alpha': 0.2},
        'xl': {'blur': 24, 'offset': 12, 'alpha': 0.25},
    }

    @classmethod
    def create_shadow_effect(cls, shadow_key: str = 'md'
                            ) -> QGraphicsDropShadowEffect:
        """Create enhanced shadow effect"""
        shadow_config = cls.SHADOWS.get(shadow_key, cls.SHADOWS['md'])

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config['blur'])
        shadow.setOffset(0, shadow_config['offset'])
        shadow.setColor(QColor(0, 0, 0,
                              int(255 * shadow_config['alpha'])))

        return shadow

# Widget usage
class AnimatedCard(ElevatedCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        shadow = DesignSystem.create_shadow_effect('md')
        self.setGraphicsEffect(shadow)
```

**Shadow Levels:**
| Level | Blur | Offset | Alpha |
|-------|------|--------|-------|
| sm | 4px | 2px | 0.1 (26%) |
| md | 8px | 4px | 0.15 (38%) |
| lg | 16px | 8px | 0.2 (51%) |
| xl | 24px | 12px | 0.25 (64%) |

### Approach 6: Responsive Widget Base Class

**Location:** `d:\Project\VidTanium\src\gui\utils\responsive.py`
**Pattern:** Components inherit ResponsiveWidget for breakpoint awareness
**Frequency:** Used in dashboard and major components

```python
class EnhancedDashboardHeroSection(ResponsiveWidget):
    """Enhanced hero section with responsive design"""

    def __init__(self, main_window, theme_manager=None, parent=None):
        super().__init__(parent)
        self.responsive_manager = ResponsiveManager.instance()

    def _setup_enhanced_ui(self) -> None:
        """Setup responsive hero section UI"""
        current_bp = self.responsive_manager.get_current_breakpoint()

        # Responsive height based on breakpoint
        if current_bp.value in ['xs', 'sm']:
            # Small screens: 140-200px
            self.hero_card.setMinimumHeight(140)
            self.hero_card.setMaximumHeight(200)
            layout = QVBoxLayout(self.hero_card)
            layout.setContentsMargins(16, 16, 16, 16)
        elif current_bp.value == 'md':
            # Medium screens: 160-220px
            self.hero_card.setMinimumHeight(160)
            self.hero_card.setMaximumHeight(220)
            layout = QVBoxLayout(self.hero_card)
            layout.setContentsMargins(20, 20, 20, 20)
        else:
            # Large screens: 180-240px
            self.hero_card.setMinimumHeight(180)
            self.hero_card.setMaximumHeight(240)
            layout = QHBoxLayout(self.hero_card)
            layout.setContentsMargins(24, 24, 24, 24)

        layout.setSpacing(16)
        # Layout adjusts based on breakpoint
```

**Breakpoints Supported:**
| Name | Range | Use Case |
|------|-------|----------|
| xs | <576px | Mobile |
| sm | 576-767px | Tablet portrait |
| md | 768-991px | Tablet landscape |
| lg | 992-1199px | Desktop |
| xl | 1200-1399px | Large desktop |
| xxl | ≥1400px | Ultra-wide |

### Approach 7: QFluentWidgets Native Components

**Location:** Various widget files
**Pattern:** Use built-in QFluentWidgets components with preset styling
**Frequency:** Most common for text labels, buttons, cards

```python
from qfluentwidgets import (
    TitleLabel,              # Title text (built-in sizing)
    BodyLabel,               # Body text (built-in sizing)
    CaptionLabel,            # Small text (built-in sizing)
    ElevatedCardWidget,      # Card container
    ProgressBar,             # Progress bar component
    ProgressRing,            # Circular progress
    FluentIcon as FIF,       # Fluent Design icons
)

# Usage
self.title = TitleLabel("Main Title")           # Uses preset sizing
self.body = BodyLabel("Body text here")         # Uses preset sizing
self.caption = CaptionLabel("Small text")       # Uses preset sizing
self.card = ElevatedCardWidget()                # Fluent elevation
self.progress = ProgressBar()                   # Fluent progress bar
```

**Advantages:**
- Consistent with Fluent Design System
- Automatic theme integration
- Built-in sizing and styling
- No custom stylesheet needed

**Disadvantages:**
- Can't easily customize sizing/font
- Can't override with DesignSystem scale
- Limited font weight/line-height control

### Approach 8: Responsive CSS File

**Location:** `d:\Project\VidTanium\src\gui\styles\responsive.css`
**Pattern:** Media queries for responsive breakpoints
**Frequency:** Applied globally to main window

```css
/* Extra small screens (< 576px) */
@media (max-width: 575px) {
    .ResponsiveContainer {
        padding: 8px;
    }

    NavigationInterface {
        max-width: 48px !important;
        min-width: 48px !important;
    }

    TitleLabel {
        font-size: 18px;
    }

    PrimaryPushButton {
        padding: 6px 12px;
        min-height: 32px;
    }

    .optional-info {
        display: none;
    }
}

/* Small screens (576px - 767px) */
@media (min-width: 576px) and (max-width: 767px) {
    NavigationInterface {
        max-width: 48px !important;
    }

    TitleLabel {
        font-size: 20px;
    }
}

/* Medium screens (768px - 991px) */
@media (min-width: 768px) and (max-width: 991px) {
    NavigationInterface {
        max-width: 200px !important;
    }

    .dashboard-cards {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Large screens (992px+) */
@media (min-width: 992px) {
    NavigationInterface {
        max-width: 250px !important;
    }

    .dashboard-cards {
        grid-template-columns: repeat(4, 1fr);
    }
}

/* Touch-friendly controls for mobile */
@media (pointer: coarse) {
    QPushButton {
        min-height: 44px;
        min-width: 44px;
    }

    QLineEdit, QComboBox {
        min-height: 44px;
    }
}

/* Smooth transitions */
* {
    transition-property: padding, margin, font-size;
    transition-duration: 0.3s;
    transition-timing-function: ease;
}
```

**Coverage:**
- Navigation width adjustments
- Card grid layout changes
- Font size scaling
- Touch target sizing
- Spacing adjustments
- Display/hide utilities

## Part 2: Styling Approach Summary

### By Component Type

**Text Components:**
- TitleLabel, BodyLabel, CaptionLabel (QFluentWidgets)
- Use DesignSystem.get_typography_style() for custom sizing
- Fallback to VidTaniumTheme constants

**Button Components:**
- PrimaryPushButton, TransparentToolButton (QFluentWidgets)
- Styled via stylesheet for custom appearance
- Icons use FluentIcon (FIF)

**Card Components:**
- ElevatedCardWidget, HeaderCardWidget (QFluentWidgets)
- Apply DesignSystem shadow effects
- Use inline stylesheets for custom colors

**Progress Components:**
- ProgressBar, ProgressRing (QFluentWidgets)
- Gradient background for progress chunks
- QPropertyAnimation for smooth updates

**Layout Components:**
- ResponsiveWidget base class for breakpoint awareness
- Responsive CSS for global adjustments
- QVBoxLayout/QHBoxLayout with DesignSystem spacing

### By Styling Scope

**Global:**
- responsive.css (applied to main window)
- QFluentWidgets theme (via setTheme())
- System theme listener (OS integration)

**Component-Level:**
- Inline f-string stylesheets
- QGraphicsDropShadowEffect
- QPropertyAnimation
- VidTaniumTheme constants

**Widget-Level:**
- setStyleSheet() with custom CSS
- setGraphicsEffect() for effects
- Property animation setup
- Font/color customization


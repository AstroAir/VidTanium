"""VidTanium Unified Design System - Clean, minimalist design"""
from qfluentwidgets import isDarkTheme
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from typing import Dict

class UnifiedDesignSystem:
    LIGHT_THEME = {"primary": "#0078D4", "primary_hover": "#1080E0", "primary_active": "#005A9E", "surface": "#FFFFFF", "surface_container": "#F5F5F5", "surface_variant": "#EBEBEB", "on_surface": "#1F1F1F", "on_surface_variant": "#616161", "outline": "#E0E0E0", "outline_variant": "#ECECEC", "success": "#107C10", "success_hover": "#1B8E1F", "warning": "#CA5010", "warning_hover": "#DA6018", "error": "#D13438", "error_hover": "#E81B23", "info": "#0078D4", "disabled": "#D0D0D0", "disabled_text": "#AEAEAE"}
    DARK_THEME = {"primary": "#4CC2FF", "primary_hover": "#63CAFF", "primary_active": "#35B0F0", "surface": "#1E1E1E", "surface_container": "#2D2D2D", "surface_variant": "#3C3C3C", "on_surface": "#FFFFFF", "on_surface_variant": "#C8C8C8", "outline": "#484848", "outline_variant": "#424242", "success": "#6CCB5F", "success_hover": "#7DD66F", "warning": "#F7630C", "warning_hover": "#FF7D1B", "error": "#F1707B", "error_hover": "#F6B5BC", "info": "#4CC2FF", "disabled": "#424242", "disabled_text": "#696969"}
    SPACING = {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32, "xxl": 48, "xxxl": 64}
    RADIUS = {"xs": 4, "sm": 6, "md": 8, "lg": 12, "round": 9999}
    TYPOGRAPHY = {"display": {"size": 28, "weight": 600, "line_height": 1.2}, "headline": {"size": 22, "weight": 600, "line_height": 1.3}, "title": {"size": 16, "weight": 600, "line_height": 1.4}, "body": {"size": 13, "weight": 400, "line_height": 1.5}, "label": {"size": 13, "weight": 500, "line_height": 1.4}, "caption": {"size": 11, "weight": 400, "line_height": 1.4}}
    @classmethod
    def color(cls, key: str) -> str:
        theme = cls.DARK_THEME if isDarkTheme() else cls.LIGHT_THEME
        return theme.get(key, "#000000")
    @classmethod
    def spacing(cls, key: str) -> int:
        return cls.SPACING.get(key, 8)
    @classmethod
    def radius(cls, key: str) -> int:
        return cls.RADIUS.get(key, 8)
    @classmethod
    def typography_style(cls, variant: str) -> str:
        if variant not in cls.TYPOGRAPHY:
            variant = "body"
        typo = cls.TYPOGRAPHY[variant]
        return f"font-size: {typo["size"]}px; font-weight: {typo["weight"]}; line-height: {typo["line_height"]};"
    @classmethod
    def card_style(cls, elevated: bool = False, interactive: bool = False) -> str:
        bg = cls.color("surface")
        border = cls.color("outline")
        radius_val = cls.radius("md")
        spacing_val = cls.spacing("md")
        hover = f"CardWidget:hover {{ background: {cls.color("surface_container")}; border-color: {cls.color("primary")}; }}" if interactive else ""
        shadow = "box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);" if elevated else ""
        return f"CardWidget {{ background: {bg}; border: 1px solid {border}; border-radius: {radius_val}px; padding: {spacing_val}px; {shadow} }} {hover}"
    @classmethod
    def button_style(cls, variant: str) -> str:
        if variant == "primary":
            return f"PushButton {{ background-color: {cls.color("primary")}; border: none; border-radius: {cls.radius("xs")}px; color: {cls.color("surface")}; font-weight: 500; padding: {cls.spacing("sm")}px {cls.spacing("md")}px; font-size: 13px; }} PushButton:hover {{ background-color: {cls.color("primary_hover")}; }} PushButton:pressed {{ background-color: {cls.color("primary_active")}; }} PushButton:disabled {{ background-color: {cls.color("disabled")}; color: {cls.color("disabled_text")}; }}"
        elif variant == "secondary":
            return f"PushButton {{ background-color: {cls.color("surface_container")}; border: 1px solid {cls.color("outline")}; border-radius: {cls.radius("xs")}px; color: {cls.color("on_surface")}; font-weight: 500; padding: {cls.spacing("sm")}px {cls.spacing("md")}px; font-size: 13px; }} PushButton:hover {{ background-color: {cls.color("surface_variant")}; border-color: {cls.color("primary")}; }} PushButton:disabled {{ background-color: {cls.color("disabled")}; color: {cls.color("disabled_text")}; border-color: {cls.color("disabled")}; }}"
        else:
            return f"PushButton {{ background-color: transparent; border: none; border-radius: {cls.radius("xs")}px; color: {cls.color("on_surface")}; font-weight: 500; padding: {cls.spacing("sm")}px {cls.spacing("md")}px; font-size: 13px; }} PushButton:hover {{ background-color: {cls.color("surface_container")}; color: {cls.color("primary")}; }} PushButton:disabled {{ color: {cls.color("disabled_text")}; }}"
    @classmethod
    def input_style(cls) -> str:
        return f"LineEdit, TextEdit {{ background-color: {cls.color("surface_container")}; border: 1px solid {cls.color("outline")}; border-radius: {cls.radius("xs")}px; color: {cls.color("on_surface")}; padding: {cls.spacing("sm")}px {cls.spacing("md")}px; font-size: 13px; }} LineEdit:focus, TextEdit:focus {{ border: 2px solid {cls.color("primary")}; }} LineEdit:disabled, TextEdit:disabled {{ background-color: {cls.color("disabled")}; color: {cls.color("disabled_text")}; border-color: {cls.color("disabled")}; }}"
    @classmethod
    def status_badge_style(cls, status: str) -> str:
        status_map = {"success": "success", "warning": "warning", "error": "error", "info": "info", "pending": "on_surface_variant", "downloading": "primary", "completed": "success", "failed": "error", "paused": "warning", "cancelled": "on_surface_variant"}
        color_key = status_map.get(status, "primary")
        color = cls.color(color_key)
        return f"QLabel {{ background-color: {color}; color: white; border-radius: {cls.radius("sm")}px; padding: {cls.spacing("xs")}px {cls.spacing("sm")}px; font-size: 11px; font-weight: 500; }}"
    @classmethod
    def create_elevation(cls, level: int = 2) -> QGraphicsDropShadowEffect:
        config = {1: {"blur": 3, "offset": 1, "alpha": 0.08}, 2: {"blur": 6, "offset": 2, "alpha": 0.12}, 3: {"blur": 12, "offset": 4, "alpha": 0.15}, 4: {"blur": 16, "offset": 6, "alpha": 0.18}, 5: {"blur": 24, "offset": 8, "alpha": 0.20}}
        cfg = config.get(level, config[2])
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(cfg["blur"])
        shadow.setOffset(0, cfg["offset"])
        shadow.setColor(QColor(0, 0, 0, int(255 * cfg["alpha"])))
        return shadow
    @classmethod
    def get_padding(cls, variant: str = "normal") -> Dict[str, int]:
        presets = {"compact": {"top": cls.spacing("sm"), "right": cls.spacing("sm"), "bottom": cls.spacing("sm"), "left": cls.spacing("sm")}, "normal": {"top": cls.spacing("md"), "right": cls.spacing("md"), "bottom": cls.spacing("md"), "left": cls.spacing("md")}, "spacious": {"top": cls.spacing("lg"), "right": cls.spacing("lg"), "bottom": cls.spacing("lg"), "left": cls.spacing("lg")}}
        return presets.get(variant, presets["normal"])
    @classmethod
    def get_gap(cls, variant: str = "normal") -> int:
        gaps = {"compact": cls.spacing("sm"), "normal": cls.spacing("md"), "spacious": cls.spacing("lg")}
        return gaps.get(variant, cls.spacing("md"))
    @classmethod
    def is_dark_theme(cls) -> bool:
        return isDarkTheme()
    @classmethod
    def get_theme_name(cls) -> str:
        return "dark" if isDarkTheme() else "light"

DS = UnifiedDesignSystem

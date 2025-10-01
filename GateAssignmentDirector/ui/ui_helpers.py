"""UI helper functions for creating consistent widgets"""

# Licensed under GPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import customtkinter as ctk
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class Color:
    """Color definition with hex code and usage tracking"""
    hex: str
    hover: Optional[str] = None
    usage: list[str] = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = []


# Color palette - harmonized progressive UI colors
COLORS = {
    "sage": Color("#9dc4a8", "#8aad95", ["start_monitoring_bg", "primary_action"]),
    "sage_lighter": Color("#c4dccb", "#adc2b5", ["sage_light_variant"]),
    "sage_darker": Color("#6f9d7e", "#5e8b6a", ["sage_dark_variant"]),
    "sage_dark": Color("#2d4035", "#253528", ["start_monitoring_text_active"]),
    "sage_light": Color("#c5d9cc", "#adc2b5", ["start_monitoring_text_inactive"]),
    "periwinkle": Color("#a8b8d4", "#95a2bb", ["assign_gate_bg", "tab_selected_bg", "secondary_action"]),
    "periwinkle_lighter": Color("#d1daf0", "#b4bdcf", ["periwinkle_light_variant"]),
    "periwinkle_darker": Color("#7689ab", "#5e8b6a", ["periwinkle_dark_variant"]),
    "periwinkle_dark": Color("#30384a", "#283040", ["assign_gate_text_active", "tab_selected_text"]),
    "periwinkle_light": Color("#cbd4e6", "#b4bdcf", ["assign_gate_text_inactive", "tab_unselected_text"]),
    "lilac": Color("#c5b8d4", "#d5c8e4", ["apply_override_bg", "tertiary_action"]),
    "lilac_lighter": Color("#e4daf0", "#c9c2cf", ["lilac_light_variant"]),
    "lilac_darker": Color("#9d87ab", "#8993bf", ["lilac_dark_variant"]),
    "lilac_light": Color("#dfd9e6", "#c9c2cf", ["lilac_text_inactive"]),
    "salmon": Color("#d4a5a0", "#bb918d", ["stop_monitoring_bg", "clear_override_bg", "destructive_action"]),
    "salmon_lighter": Color("#ecc9c5", "#cfc2bf", ["salmon_light_variant"]),
    "salmon_darker": Color("#ab7771", "#af6c6c", ["salmon_dark_variant"]),
    "salmon_light": Color("#e8d9d6", "#cfc2bf", ["stop_monitoring_text_inactive"]),
    "purple_gray": Color("#4a4050", "#403846", ["lilac_text", "salmon_text", "override_buttons_text"]),
    "purple_gray_lighter": Color("#685c75", "#5a4f66", ["purple_gray_light_variant"]),
    "purple_gray_darker": Color("#332b3c", "#2a2431", ["purple_gray_dark_variant"]),
    "muted_sage": Color("#6B9E78", "#5e8b6a", ["status_success", "status_monitoring"]),
    "muted_sage_lighter": Color("#95c4a5", "#82b090", ["muted_sage_light_variant"]),
    "muted_sage_darker": Color("#4d7a58", "#3f6847", ["muted_sage_dark_variant"]),
    "dusty_rose": Color("#C67B7B", "#af6c6c", ["status_error", "status_stopped", "border_error"]),
    "dusty_rose_lighter": Color("#e5a8a8", "#cf9595", ["dusty_rose_light_variant"]),
    "dusty_rose_darker": Color("#9d5454", "#854545", ["dusty_rose_dark_variant"]),
    "mustard": Color("#D4A574", "#bb9166", ["status_warning", "airport_manual_override"]),
    "mustard_lighter": Color("#eac5a0", "#d4b090", ["mustard_light_variant"]),
    "mustard_darker": Color("#a8804f", "#8f6d42", ["mustard_dark_variant"]),
    "charcoal": Color("#1a1a1a", "#171717", ["bg_dark", "textbox_bg"]),
    "charcoal_light": Color("#2a2a2a", "#252525", ["bg_panel", "override_panel_bg", "tab_bg"]),
    "charcoal_lighter": Color("#3a3a3a", "#333333", ["border_default", "tab_unselected_hover"]),
    "charcoal_lightest": Color("#4a4a4a", "#414141", ["tab_bg"]),
    "gray": Color("#4a4a4a", "#414141", ["bg_neutral", "edit_gates_button"]),
    "gray_light": Color("#5a5a5a", "#4f4f4f", ["bg_neutral_hover"]),
    "gray_lighter": Color("#6a6a6a", "#5f5f5f", ["gray_light_variant"]),
    "gray_darker": Color("#2a2a2a", "#1f1f1f", ["gray_dark_variant"]),
    "slate": Color("#707a8a", "#5f6978", ["slate_base"]),
    "slate_lighter": Color("#9aa5b5", "#8893a3", ["slate_light_variant"]),
    "slate_darker": Color("#4f5862", "#3f474f", ["slate_dark_variant"]),
    "periwinkle_tint": Color("#9BA8D9", "#8993bf", ["tab_selected_hover", "border_focus"]),
}

# Convenience function for shorter access
def c(color_name: str, hover: bool = False) -> str:
    """Get color hex code. Usage: c('sage') or c('sage', hover=True)"""
    color = COLORS[color_name]
    return color.hover if hover and color.hover else color.hex


def _label(
    frame: ctk,
    text: str = "Default Label",
    size: int = 14,
    padx: tuple[int, int] = (10, 0),
    pady: tuple[int, int] = (15, 5),
    color: str = "#ffffff",
    width: Optional[int] = None,
    side: Optional[str] = None,
    bold: bool = True
) -> None:
    """Create a text label for the current frame"""
    label_kwargs = {
        "text": text,
        "font": ("Arial", size, "bold" if bold else "normal"),
        "text_color": color,
        "anchor": "w"
    }
    if width is not None:
        label_kwargs["width"] = width

    label = ctk.CTkLabel(frame, **label_kwargs)
    if side:
        label.pack(side=side, padx=padx, pady=pady)
    else:
        label.pack(anchor="w", pady=pady, padx=padx)


def _button(
    frame: ctk,
    command: Callable[[], None],
    text: str = "Default Text",
    height: int = 35,
    width: Optional[int] = None,
    fg_color: str = "#4a4a4a",
    hover_color: str = "#5a5a5a",
    text_color: Optional[str] = None,
    corner_radius: int = 6,
    side: Optional[str] = None,
    expand: bool = True,
    fill: str = "x",
    padx: tuple[int, int] = (0, 0),
    pady: tuple[int, int] = (0, 0),
    state: str = "normal",
    size: int = 16
) -> ctk.CTkButton:
    """Create a button and return it"""
    btn_kwargs = {
        "text": text,
        "command": command,
        "height": height,
        "fg_color": fg_color,
        "hover_color": hover_color,
        "state": state,
        "font": ("Arial", size, "bold"),
        "corner_radius": corner_radius
    }
    if width is not None:
        btn_kwargs["width"] = width
    if text_color is not None:
        btn_kwargs["text_color"] = text_color

    btn = ctk.CTkButton(frame, **btn_kwargs)
    btn.pack(side=side, expand=expand, fill=fill, padx=padx, pady=pady)
    return btn
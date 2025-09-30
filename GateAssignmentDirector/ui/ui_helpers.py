"""UI helper functions for creating consistent widgets"""

import customtkinter as ctk
from typing import Optional, Callable


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
    fg_color: str = "#4a4a4a",
    hover_color: str = "#5a5a5a",
    side: Optional[str] = None,
    expand: bool = True,
    fill: str = "x",
    padx: tuple[int, int] = (0, 0),
    pady: tuple[int, int] = (0, 0),
    state: str = "normal",
    size: int = 16
) -> ctk.CTkButton:
    """Create a button and return it"""
    btn = ctk.CTkButton(
        frame,
        text=text,
        command=command,
        height=height,
        fg_color=fg_color,
        hover_color=hover_color,
        state=state,
        font=("Arial", size, "bold")
    )
    btn.pack(side=side, expand=expand, fill=fill, padx=padx, pady=pady)
    return btn
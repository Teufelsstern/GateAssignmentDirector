"""Logs tab UI setup for the Gate Assignment Director"""

import customtkinter as ctk
from GateAssignmentDirector.ui.ui_helpers import _button


def setup_logs_tab(parent_ui, tab):
    """
    Setup the Logs tab UI

    Args:
        parent_ui: The DirectorUI instance
        tab: The tab widget to setup
    """
    parent_ui.log_text = ctk.CTkTextbox(tab, font=("Consolas", 12), fg_color="#1a1a1a")
    parent_ui.log_text.pack(fill="both", expand=True, padx=20, pady=(20, 10))

    _button(
        tab,
        command=lambda: parent_ui.log_text.delete("1.0", "end"),
        text="Clear Logs",
        height=30,
        fg_color="#4a4a4a",
        hover_color="#5a5a5a",
        pady=(0, 20)
    )
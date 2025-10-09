"""Disclaimer dialog shown on first launch"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import customtkinter as ctk
import sys
from typing import Callable


DISCLAIMER_TEXT = """Gate Assignment Director - User Agreement

This software stands against discrimination.

This is a free, open-source program created and maintained by one person.

Important points:
• Licensed under AGPL-3.0 (see LICENSE file)
• Provided as-is with no warranties or guarantees
• This is a personal project with bugs and limitations
• I cannot guarantee maintaining this codebase for any length of time
• Please keep bug reports and feature requests to a minimum

If you find the value statement above or the nature of open-source
development problematic, this software is not for you.

By clicking "Accept", you acknowledge these terms and agree to use
the software accordingly."""


class DisclaimerDialog:
    def __init__(self, parent, on_accept: Callable):
        self.on_accept = on_accept
        self.accepted = False

        # Create modal window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("User Agreement")
        self.window.geometry("600x500")
        self.window.resizable(False, False)

        # Make it modal
        self.window.transient(parent)
        self.window.grab_set()

        # Center on screen
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Text frame
        text_frame = ctk.CTkFrame(main_frame, fg_color="#2b2b2b")
        text_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Disclaimer text
        text_label = ctk.CTkLabel(
            text_frame,
            text=DISCLAIMER_TEXT,
            font=("Arial", 12),
            justify="left",
            anchor="w"
        )
        text_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Checkbox frame
        checkbox_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x", pady=(0, 15))

        self.accept_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="I have read and accept these terms",
            variable=self.accept_var,
            font=("Arial", 12),
            command=self._on_checkbox_toggle,
            corner_radius=6,
            border_width=2
        )
        self.checkbox.pack(anchor="w")

        # Button frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        self.decline_btn = ctk.CTkButton(
            button_frame,
            text="Decline",
            command=self._on_decline,
            fg_color="#8b0000",
            hover_color="#a00000",
            font=("Arial", 13, "bold"),
            corner_radius=6,
            height=35,
            width=120
        )
        self.decline_btn.pack(side="left")

        self.accept_btn = ctk.CTkButton(
            button_frame,
            text="Accept",
            command=self._on_accept,
            fg_color="#2d5016",
            hover_color="#3d6622",
            font=("Arial", 13, "bold"),
            corner_radius=6,
            height=35,
            width=120,
            state="disabled"
        )
        self.accept_btn.pack(side="right")

        # Handle window close button (X)
        self.window.protocol("WM_DELETE_WINDOW", self._on_decline)

    def _on_checkbox_toggle(self):
        """Enable/disable accept button based on checkbox"""
        if self.accept_var.get():
            self.accept_btn.configure(state="normal")
        else:
            self.accept_btn.configure(state="disabled")

    def _on_accept(self):
        """User accepted the disclaimer"""
        self.accepted = True
        self.window.destroy()
        self.on_accept()

    def _on_decline(self):
        """User declined the disclaimer"""
        self.window.destroy()
        sys.exit(0)

    def wait_window(self):
        """Wait for the dialog to close"""
        self.window.wait_window()

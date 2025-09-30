"""Config tab UI setup for the Gate Assignment Director"""

import customtkinter as ctk
from GateAssignmentDirector.ui.ui_helpers import _label, _button


def setup_config_tab(parent_ui, tab):
    """
    Setup the Config tab UI

    Args:
        parent_ui: The DirectorUI instance
        tab: The tab widget to setup
    """
    # Scrollable frame
    scroll_frame = ctk.CTkScrollableFrame(tab)
    scroll_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))

    # Store references to entry widgets
    parent_ui.config_entries = {}

    # API Settings
    _label(frame=scroll_frame, text="API Settings", size=14, pady=(15, 5))
    create_config_field(
        parent_ui, scroll_frame, field_name="SI_API_KEY", label_text="Say Intentions API Key"
    )

    _label(
        frame=scroll_frame,
        text="Everything below shouldn't be touched unless you know what you're doing.",
        size=14,
        color="#d97440",
        pady=(30, 5),
    )

    # Timing Settings
    _label(frame=scroll_frame, text="Timing Settings", size=14, pady=(10, 5))

    timing_fields = [
        ("sleep_short", "Sleep Short (seconds)"),
        ("sleep_long", "Sleep Long (seconds)"),
    ]

    for field, label in timing_fields:
        create_config_field(parent_ui, scroll_frame, field, label)

    # Interval Settings
    _label(frame=scroll_frame, text="Interval Settings", size=14, pady=(15, 5))
    interval_fields = [
        ("ground_check_interval", "Ground Check Interval (ms)"),
        ("aircraft_request_interval", "Aircraft Request Interval (ms)"),
        ("ground_timeout_default", "Ground Timeout Default (s)"),
    ]

    for field, label in interval_fields:
        create_config_field(parent_ui, scroll_frame, field, label)

    # Menu Settings
    _label(frame=scroll_frame, text="Menu Settings", size=14, pady=(15, 5))
    create_config_field(
        parent_ui, scroll_frame, "max_menu_check_attempts", "Max Menu Check Attempts"
    )

    # Logging Settings
    _label(frame=scroll_frame, text="Logging Settings", size=14, pady=(15, 5))

    logging_fields = [
        ("logging_level", "Logging Level"),
        ("logging_format", "Logging Format"),
        ("logging_datefmt", "Logging Date Format"),
    ]

    for field, label in logging_fields:
        create_config_field(parent_ui, scroll_frame, field, label)

    # Info about computed fields
    _label(
        frame=scroll_frame,
        text="Note: Username and flight_json_path are computed automatically",
        size=9,
        pady=(15, 5),
        color="#808080",
    )

    # Button frame
    btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 20))

    # Load button
    _button(
        btn_frame,
        parent_ui.load_config_values,
        text="Reload Config",
        side="left",
        padx=(0, 5)
    )

    # Save button
    _button(
        btn_frame,
        parent_ui.save_config_values,
        text="Save Config",
        fg_color="#2d5016",
        hover_color="#3d6622",
        side="right",
        padx=(5, 0),
    )

    # Load current values
    parent_ui.load_config_values()


def create_config_field(parent_ui, parent, field_name, label_text):
    """Create a labeled entry field for configuration"""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=3)

    # Keep inline labels as direct CTkLabel (needs side="left")
    ctk.CTkLabel(
        frame, text=label_text + ":", font=("Arial", 14), width=250, anchor="w"
    ).pack(side="left", padx=(0, 10))

    entry = ctk.CTkEntry(frame)
    entry.pack(side="left", fill="x", expand=True)

    parent_ui.config_entries[field_name] = entry
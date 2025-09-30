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
    scroll_frame = ctk.CTkScrollableFrame(tab)
    scroll_frame.pack(fill="both", expand=True, padx=5, pady=(5, 10))

    parent_ui.config_entries = {}

    _label(frame=scroll_frame, text="API Settings", size=16, pady=(0, 0), padx=(5,0))
    create_config_field(
        parent_ui, scroll_frame, field_name="SI_API_KEY", label_text="SI API Key", padx=(5,0), entry_width=100
    )

    _label(frame=scroll_frame, text="GSX Settings", size=16, pady=(10, 0), padx=(5,0))
    create_config_field(
        parent_ui, scroll_frame, field_name="default_airline", label_text="Default Airline", padx=(5,0), entry_width=100
    )

    _label(
        frame=scroll_frame,
        text="_________ Advanced Settings ___________",
        size=14,
        color="#d97440",
        pady=(20, 10)
    )

    _label(frame=scroll_frame, text="Timing Settings", size=16, pady=(10, 0), padx=(5,0))

    timing_fields = [
        ("sleep_short", "Short delay (s). Never shorter than 0.1"),
        ("sleep_long", "Longer delay (s). Never shorter than 0.2"),
    ]

    for field, label in timing_fields:
        create_config_field(parent_ui, scroll_frame, field, label, padx=(5,0), entry_width=30)

    _label(frame=scroll_frame, text="Interval Settings", size=16, pady=(10, 0), padx=(5,0))
    interval_fields = [
        ("ground_check_interval", "Delay (s) between ground checks. Never lower than 0.5"),
        ("aircraft_request_interval", "Delay (s) between aircraft requests. Never lower than 0.5"),
    ]

    for field, label in interval_fields:
        create_config_field(parent_ui, scroll_frame, field, label, padx=(5,0), entry_width=50)

    _label(frame=scroll_frame, text="Menu Settings", size=16, pady=(10, 0), padx=(5,0))
    create_config_field(
        parent_ui, scroll_frame, "max_menu_check_attempts", "Max Menu Check Attempts", padx=(5,0), entry_width=30
    )

    _label(frame=scroll_frame, text="Logging Settings", size=16, pady=(10, 0), padx=(5,0))

    logging_fields = [
        ("logging_level", "Logging Level", 60),
        ("logging_format", "Logging Format", 300),
        ("logging_datefmt", "Logging Date Format", 90),
    ]

    for field, label, width in logging_fields:
        create_config_field(parent_ui, scroll_frame, field, label, padx=(5,0), entry_width=width)

    # Info about computed fields
    _label(
        frame=scroll_frame,
        text="Note: Username and flight_json_path are computed automatically",
        size=9,
        pady=(15, 5),
        color="#808080",
    )

    btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 20))

    _button(
        btn_frame,
        parent_ui.load_config_values,
        text="Reload Config",
        side="left",
        padx=(0, 5)
    )

    _button(
        btn_frame,
        parent_ui.save_config_values,
        text="Save Config",
        fg_color="#2d5016",
        hover_color="#3d6622",
        side="right",
        padx=(5, 0),
    )

    parent_ui.load_config_values()


def create_config_field(parent_ui, parent, field_name:str, label_text:str, label_width:int = 60, entry_width:int = 60, padx:tuple[int,int]=(0,10), size:int = 14, side:str = "left"):
    """Create a labeled entry field for configuration"""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", expand=False)
    _label(frame, text=label_text + ":", size=size, padx=(10,10), pady=(0,5), side=side, width=label_width, bold=False)
    entry = ctk.CTkEntry(frame, width=entry_width, height=5, corner_radius=6, border_width=3, border_color="#3a3a3a")
    entry.pack(expand=False, side=side)

    parent_ui.config_entries[field_name] = entry
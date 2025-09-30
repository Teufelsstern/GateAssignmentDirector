"""Monitor tab UI setup for the Gate Assignment Director"""

import customtkinter as ctk
from GateAssignmentDirector.ui.ui_helpers import _label, _button


def setup_monitor_tab(parent_ui, tab):
    """
    Setup the Monitor tab UI

    Args:
        parent_ui: The DirectorUI instance
        tab: The tab widget to setup
    """
    status_frame = ctk.CTkFrame(tab, fg_color="transparent")
    status_frame.pack(fill="x", padx=20, pady=(20, 10))

    status_row = ctk.CTkFrame(status_frame, fg_color="transparent")
    status_row.pack(fill="x", pady=(0, 5), anchor="w")

    _label(
        status_row,
        text="Status:",
        width=70,
        padx=(0, 5),
        pady=(0, 0),
        side="left"
    )

    parent_ui.status_label = ctk.CTkLabel(
        status_row, text="Idle", font=("Arial", 14), text_color="#808080"
    )
    parent_ui.status_label.pack(side="left")

    # Airport row
    airport_row = ctk.CTkFrame(status_frame, fg_color="transparent")
    airport_row.pack(fill="x", anchor="w")

    _label(
        airport_row,
        text="Airport:",
        width=70,
        padx=(0, 5),
        pady=(0, 0),
        side="left"
    )

    parent_ui.airport_label = ctk.CTkLabel(
        airport_row, text="None", font=("Arial", 14), text_color="#808080"
    )
    parent_ui.airport_label.pack(side="left")

    override_toggle_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
    override_toggle_frame.pack(fill="x")

    parent_ui.override_toggle_btn = _button(
        override_toggle_frame,
        parent_ui.toggle_override_section,
        text="▼ Manual Override",
        fg_color="#2b2b2b",
        size=12,
        hover_color="#2b2b2b",
        height=30,
        pady=(0, 0),
        side="left",
        expand=False
    )

    parent_ui.override_panel = ctk.CTkFrame(status_frame, fg_color="#2a2a2a")

    override_content = ctk.CTkFrame(parent_ui.override_panel, fg_color="transparent")
    override_content.pack(fill="x", padx=10, pady=(0,10))

    _label(override_content, text="Airport:", size=12, pady=(0, 5), width=40, side="left")
    parent_ui.override_airport_entry = ctk.CTkEntry(override_content, placeholder_text="ICAO", width=45)
    parent_ui.override_airport_entry.pack(side="left", padx=(5, 5))

    _label(override_content, text="Terminal:", size=12, pady=(0, 5), width=50, side="left")
    parent_ui.override_terminal_entry = ctk.CTkEntry(override_content, placeholder_text="e.g., 2", width=80)
    parent_ui.override_terminal_entry.pack(side="left", padx=(5, 10))

    _label(override_content, text="Gate:", size=12, pady=(0, 5), width=30, side="left")
    parent_ui.override_gate_entry = ctk.CTkEntry(override_content, placeholder_text="e.g., 24A", width=60)
    parent_ui.override_gate_entry.pack(side="left", padx=(5, 0))

    override_btn_frame = ctk.CTkFrame(parent_ui.override_panel, fg_color="transparent")
    override_btn_frame.pack(fill="x", padx=10, pady=(0, 0))

    _button(
        override_btn_frame,
        parent_ui.apply_override,
        text="Apply Override",
        fg_color="#2d5016",
        hover_color="#3d6622",
        height=14,
        size=12,
        side="left",
        expand=False,
        fill="none",
        padx=(0, 5)
    )

    _button(
        override_btn_frame,
        parent_ui.clear_override,
        text="Clear Override",
        fg_color="#5a1a1a",
        hover_color="#6e2828",
        height=14,
        size=12,
        side="left",
        expand=False,
        fill="none"
    )

    start_stop_btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
    start_stop_btn_frame.pack(fill="x", padx=20, pady=0)

    parent_ui.start_btn = _button(
        start_stop_btn_frame,
        parent_ui.start_monitoring,
        text="Start Monitoring",
        fg_color="#2d5016",
        hover_color="#3d6622",
        pady=(0, 5),
        padx=(0, 10),
        side="left"
    )

    parent_ui.stop_btn = _button(
        start_stop_btn_frame,
        parent_ui.stop_monitoring,
        text="Stop Monitoring",
        fg_color="#5a1a1a",
        hover_color="#6e2828",
        pady=(0, 5),
        state="disabled",
        side="right"
    )

    btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
    parent_ui.assign_gate_btn = _button(
        btn_frame,
        parent_ui.assign_gate_manual,
        text="Assign Gate",
        fg_color="#1a4a1a",
        hover_color="#2a5a2a",
        pady=(5, 5),
        state="disabled"
    )
    _button(
        btn_frame,
        parent_ui.edit_gates,
        text="Edit gates at current airport",
        fg_color="#4a4a4a",
        hover_color="#5a5a5a",
        height=14,
        pady=(5, 5)
    )
    btn_frame.pack(fill="x", padx=20, pady=(0,10))

    activity_frame = ctk.CTkFrame(tab)
    activity_frame.pack(fill="both", expand=True, padx=10, pady=0)

    _label(
        activity_frame,
        text="Recent Activity",
        pady=(0, 5),
        padx=(10, 0)
    )

    parent_ui.activity_text = ctk.CTkTextbox(
        activity_frame, font=("Consolas", 12), fg_color="#1a1a1a"
    )
    parent_ui.activity_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))
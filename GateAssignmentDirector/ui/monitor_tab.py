"""Monitor tab UI setup for the Gate Assignment Director"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import customtkinter as ctk
from GateAssignmentDirector.ui.ui_helpers import _label, _button, c
from GateAssignmentDirector.ui.tooltips import attach_tooltip


def setup_monitor_tab(parent_ui, tab):
    """
    Setup the Monitor tab UI

    Args:
        parent_ui: The DirectorUI instance
        tab: The tab widget to setup
    """
    status_frame = ctk.CTkFrame(tab, fg_color="transparent")
    status_frame.pack(fill="x", padx=20, pady=(20, 10))

    # Airport row
    airport_row = ctk.CTkFrame(status_frame, fg_color="transparent")
    airport_row.pack(fill="x", pady=(0, 5), anchor="w")

    airport_label_text = _label(
        airport_row,
        text="Airport:",
        width=70,
        padx=(0, 5),
        pady=(0, 0),
        side="left"
    )
    attach_tooltip(airport_label_text, 'airport_label')

    parent_ui.airport_label = ctk.CTkLabel(
        airport_row, text="None", font=("Arial", 14), text_color="#808080"
    )
    parent_ui.airport_label.pack(side="left")

    status_row = ctk.CTkFrame(status_frame, fg_color="transparent")
    status_row.pack(fill="x", anchor="w")

    status_label_text = _label(
        status_row,
        text="Status:",
        width=70,
        padx=(0, 5),
        pady=(0, 0),
        side="left"
    )
    attach_tooltip(status_label_text, 'status_label')

    parent_ui.status_label = ctk.CTkLabel(
        status_row, text="Idle", font=("Arial", 14), text_color="#808080"
    )
    parent_ui.status_label.pack(side="left")

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
    attach_tooltip(parent_ui.override_toggle_btn, 'override_toggle_btn')

    parent_ui.override_panel = ctk.CTkFrame(status_frame, fg_color=c('charcoal_light'), corner_radius=6)

    override_content = ctk.CTkFrame(parent_ui.override_panel, fg_color="transparent")
    override_content.pack(fill="x", padx=10, pady=(0,10))

    override_airport_label = _label(override_content, text="Airport:", size=12, pady=(0, 5), width=40, side="left", padx=(0, 5))
    attach_tooltip(override_airport_label, 'override_airport_entry')
    parent_ui.override_airport_entry = ctk.CTkEntry(override_content, placeholder_text="ICAO", width=45, corner_radius=6, border_width=1, border_color=c('charcoal_lighter'))
    parent_ui.override_airport_entry.pack(side="left", padx=(0, 5))

    override_terminal_label = _label(override_content, text="Terminal:", size=12, pady=(0, 5), width=50, side="left")
    attach_tooltip(override_terminal_label, 'override_terminal_entry')
    parent_ui.override_terminal_entry = ctk.CTkEntry(override_content, placeholder_text="e.g., 2", width=80, corner_radius=6, border_width=1, border_color=c('charcoal_lighter'))
    parent_ui.override_terminal_entry.pack(side="left", padx=(5, 10))

    override_gate_label = _label(override_content, text="Gate:", size=12, pady=(0, 5), width=30, side="left")
    attach_tooltip(override_gate_label, 'override_gate_entry')
    parent_ui.override_gate_entry = ctk.CTkEntry(override_content, placeholder_text="e.g., 24A", width=60, corner_radius=6, border_width=1, border_color=c('charcoal_lighter'))
    parent_ui.override_gate_entry.pack(side="left", padx=(5, 0))

    override_btn_frame = ctk.CTkFrame(parent_ui.override_panel, fg_color="transparent")
    override_btn_frame.pack(fill="x", padx=10, pady=(0, 0))

    parent_ui.apply_override_btn = _button(
        override_btn_frame,
        parent_ui.apply_override,
        text="Apply Override",
        fg_color=c('lilac'),
        hover_color=c('lilac', hover=True),
        height=14,
        size=12,
        side="left",
        expand=False,
        fill="none",
        padx=(0, 5),
        width=175,
        text_color=c('purple_gray')
    )
    attach_tooltip(parent_ui.apply_override_btn, 'apply_override_btn')

    parent_ui.clear_override_btn = _button(
        override_btn_frame,
        parent_ui.clear_override,
        text="Clear Override",
        fg_color=c('salmon'),
        hover_color=c('salmon', hover=True),
        height=14,
        size=12,
        side="left",
        expand=False,
        fill="none",
        width=175,
        text_color=c('purple_gray')
    )
    attach_tooltip(parent_ui.clear_override_btn, 'clear_override_btn')

    start_stop_btn_frame = ctk.CTkFrame(tab, fg_color="transparent")

    parent_ui.start_btn = _button(
        start_stop_btn_frame,
        parent_ui.start_monitoring,
        text="Start Monitoring",
        fg_color=c('sage'),
        hover_color=c('sage', hover=True),
        text_color=c('sage_dark'),
        pady=(0, 0),
        padx=(0, 5),
        side="left"
    )
    attach_tooltip(parent_ui.start_btn, 'start_monitoring_btn')

    parent_ui.stop_btn = _button(
        start_stop_btn_frame,
        parent_ui.stop_monitoring,
        text="Stop Monitoring",
        fg_color=c('salmon'),
        hover_color=c('salmon', hover=True),
        text_color=c('salmon_light'),
        pady=(0, 0),
        state="disabled",
        side="right"
    )
    attach_tooltip(parent_ui.stop_btn, 'stop_monitoring_btn')
    start_stop_btn_frame.pack(fill="x", padx=20, pady=(0,5))

    btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
    parent_ui.assign_gate_btn = _button(
        btn_frame,
        parent_ui.assign_gate_manual,
        text="Assign Gate",
        fg_color=c('periwinkle'),
        hover_color=c('periwinkle', hover=True),
        text_color=c('periwinkle_light'),
        pady=(0, 5),
        state="disabled"
    )
    attach_tooltip(parent_ui.assign_gate_btn, 'assign_gate_btn')

    edit_gates_btn = _button(
        btn_frame,
        parent_ui.edit_gates,
        text="Edit gates at current airport",
        fg_color=c('gray'),
        hover_color=c('gray_light'),
        height=14,
        pady=(0, 5)
    )
    attach_tooltip(edit_gates_btn, 'edit_gates_btn')

    btn_frame.pack(fill="x", padx=20, pady=(0,10))

    activity_frame = ctk.CTkFrame(tab, corner_radius=6)
    activity_frame.pack(fill="both", expand=True, padx=10, pady=0)

    activity_label = _label(
        activity_frame,
        text="Recent Activity",
        pady=(0, 5),
        padx=(10, 0)
    )
    attach_tooltip(activity_label, 'activity_text')

    parent_ui.activity_text = ctk.CTkTextbox(
        activity_frame, font=("Consolas", 12), fg_color="#1a1a1a", state="disabled"
    )
    parent_ui.activity_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))
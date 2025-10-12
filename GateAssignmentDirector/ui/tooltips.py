"""Tooltip definitions for Gate Assignment Director UI"""

try:
    from CTkToolTip import CTkToolTip

    TOOLTIPS_AVAILABLE = True
except ImportError:
    TOOLTIPS_AVAILABLE = False
    import logging

    logging.warning("CTkToolTip not available - tooltips will be disabled")


class TopMostToolTip(CTkToolTip):
    """Custom tooltip that inherits topmost status from parent window"""

    def on_enter(self, event=None):
        """Override to apply topmost attribute when tooltip appears"""
        super().on_enter(event)

        # Check if tooltip window was created and apply topmost if parent has it
        if hasattr(self, "tip_window") and self.tip_window:
            try:
                parent_toplevel = self.widget.winfo_toplevel()
                parent_topmost = parent_toplevel.attributes("-topmost")
                if parent_topmost:
                    self.tip_window.attributes("-topmost", True)
            except (AttributeError, RuntimeError):
                pass  # Fallback if check fails


# Monitor Tab Tooltips
MONITOR_TAB = {
    "airport_label": "Shows departure → destination airport (yellow=estimating, green=confirmed)",
    "status_label": "Current monitoring state: Idle (not started), Monitoring (active), Stopped (manually stopped)",
    "override_toggle_btn": "Show/hide manual airport and gate override controls",
    "override_airport_entry": "4-letter ICAO airport code (e.g., EDDF, KJFK, KLAX)",
    "override_terminal_entry": "Terminal number or letter (e.g., 2, B, Terminal 3)",
    "override_gate_entry": "Gate identifier (e.g., 24A, C12, B28)",
    "apply_override_btn": "Force specific airport and gate for the next assignment (bypasses automatic detection)",
    "clear_override_btn": "Remove manual override and return to automatic airport detection",
    "start_monitoring_btn": "Begin monitoring flight data and automatically assigning gates when aircraft lands",
    "stop_monitoring_btn": "Stop automatic monitoring and gate assignments",
    "assign_gate_btn": "Manually trigger gate assignment now (requires gate information from override or monitoring)",
    "edit_gates_btn": "Open gate management window to view/modify parking positions at current airport",
    "activity_text": "Live status updates showing gate assignments and system events",
}

# Config Tab Tooltips
CONFIG_TAB = {
    "SI_API_KEY": "SayIntentions API key for enhanced gate matching (optional, contact support for key)",
    "default_airline": "Default airline to select in GSX menu (e.g., 'United_2000', 'GSX', 'Delta_4000')",
    "minimize_to_tray": "When enabled, closing the window minimizes to system tray instead of quitting",
    "always_on_top": "Keep the application window on top of other windows",
    "sleep_short": "Short delay between GSX operations in seconds (minimum 0.1, default 0.1)",
    "sleep_long": "Longer delay for GSX menu transitions in seconds (minimum 0.2, default 0.3)",
    "ground_check_interval": "Interval between checks if aircraft is on ground in seconds (minimum 0.5)",
    "aircraft_request_interval": "Interval between polling aircraft data in seconds (minimum 0.5)",
    "max_menu_check_attempts": "Maximum retries when waiting for GSX menu changes (default 20)",
    "logging_level": "Python logging level: DEBUG (verbose), INFO (normal), WARNING, ERROR, CRITICAL",
    "logging_format": "Python logging format string (advanced users only)",
    "logging_datefmt": "Python logging date format string (advanced users only)",
    "reload_config_btn": "Discard current changes and reload all settings from config.yaml file",
    "save_config_btn": "Save all current settings to config.yaml file",
}

# Logs Tab Tooltips
LOGS_TAB = {
    "save_logs_btn": "Export all log entries to a timestamped text file",
    "clear_logs_btn": "Clear all log entries from display (does not delete saved logs)",
}


def attach_tooltip(widget, tooltip_key: str, delay: float = 0.6):
    """
    Attach tooltip to widget by looking up key in all tooltip dicts

    Args:
        widget: CTk widget to attach tooltip to
        tooltip_key: Key to lookup in tooltip dicts
        delay: Delay before showing tooltip in seconds (default 0.2)
    """
    if not TOOLTIPS_AVAILABLE:
        return

    # Search all tooltip dictionaries
    for tooltip_dict in [MONITOR_TAB, CONFIG_TAB, LOGS_TAB]:
        if tooltip_key in tooltip_dict:
            TopMostToolTip(widget, message=tooltip_dict[tooltip_key], delay=delay)
            return

    # If not found, warn developer
    import logging

    logging.warning(f"No tooltip defined for key '{tooltip_key}'")

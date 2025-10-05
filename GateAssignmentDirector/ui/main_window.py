"""Main window class for the Gate Assignment Director UI"""

# Licensed under GPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import customtkinter as ctk
import threading
import logging
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, filedialog
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from typing import Optional

from GateAssignmentDirector.director import GateAssignmentDirector
from GateAssignmentDirector.gad_config import GADConfig
from GateAssignmentDirector.gsx_hook import GsxHook
from GateAssignmentDirector.ui.gate_management import GateManagementWindow
from GateAssignmentDirector.ui.monitor_tab import setup_monitor_tab
from GateAssignmentDirector.ui.logs_tab import setup_logs_tab
from GateAssignmentDirector.ui.config_tab import setup_config_tab
from GateAssignmentDirector.ui.ui_helpers import c


class DirectorUI:
    def __init__(self):
        self.director = GateAssignmentDirector()
        self.process_thread = None
        self.tray_icon = None
        self.config = GADConfig.from_yaml()
        self.current_airport = None
        self.override_active = False
        self.override_airport = None
        self.override_terminal = None
        self.override_gate = None
        self.override_section_visible = False

        # UI widgets (will be populated by setup functions)
        self.config_entries = {}
        self.log_text = None
        self.status_label = None
        self.airport_label = None
        self.override_toggle_btn = None
        self.override_panel = None
        self.override_airport_entry = None
        self.override_terminal_entry = None
        self.override_gate_entry = None
        self.apply_override_btn = None
        self.clear_override_btn = None
        self.start_btn = None
        self.stop_btn = None
        self.assign_gate_btn = None
        self.activity_text = None
        self.vwl = None
        self.val = []

        # Airport update debouncing
        self._airport_update_pending = None
        self._last_known_departure = None
        self._last_known_destination = None

        # Setup main window
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Gate Assignment Director")
        self.root.geometry("500x500")

        # Set window icon
        import sys
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            base_path = Path(sys._MEIPASS)
            icon_path = base_path / "GateAssignmentDirector" / "icon.ico"
        else:
            # Running as normal Python script
            icon_path = Path(__file__).parent.parent / "icon.ico"

        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

        # Set size constraints
        self.root.minsize(350, 430)
        self.root.maxsize(800, 800)

        # Override close button to minimize to tray
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # Setup system tray
        self._setup_tray()

        # Values statement at bottom (setup first to claim bottom space)
        self._setup_values_statement()

        # Create tabview (will expand in remaining space)
        self.tabview = ctk.CTkTabview(
            self.root,
            corner_radius=6,
            segmented_button_fg_color=c('periwinkle', hover=True),
            segmented_button_selected_color=c('sage'),
            segmented_button_selected_hover_color=c('sage'),
            segmented_button_unselected_color=c('periwinkle',hover=True),
            segmented_button_unselected_hover_color=c('periwinkle'),
            text_color=c('purple_gray'),
            command=self._on_tab_change
        )
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # Add tabs
        self.tabview.add("Monitor")
        self.tabview.add("Config")
        self.tabview.add("Logs")

        # Setup each tab using dedicated modules
        setup_monitor_tab(self, self.tabview.tab("Monitor"))
        setup_logs_tab(self, self.tabview.tab("Logs"))
        setup_config_tab(self, self.tabview.tab("Config"))

        # Redirect logging to text widget
        self._setup_logging()

        # System integrity check
        self.ic()

        # Start periodic UI updates
        self._update_ui_state()

    def _setup_values_statement(self):
        """Create values statement at bottom with random word"""
        import random

        # Create fixed container at bottom
        values_container = ctk.CTkFrame(self.root, fg_color="transparent", height=30, width=150)
        values_container.pack(side="bottom", fill="x", pady=(0, 5))
        values_container.pack_propagate(False)  # Prevent shrinking

        # Container to center the text
        center_frame = ctk.CTkFrame(values_container, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")  # Always centered

        rainbow_colors = [
            "#d96b6b",  # soft red
            "#d9a96b",  # soft orange
            "#c9d96b",  # soft yellow
            "#8bd96b",  # soft green
            "#6ba9d9",  # soft blue
            "#bb6bd9",  # soft purple
        ]

        # Static text with split "software" to use all 6 rainbow colors
        words = ["This", "soft", "ware", "stands"]
        for i, word in enumerate(words):
            color = rainbow_colors[i % len(rainbow_colors)]
            label = ctk.CTkLabel(
                center_frame,
                text=word,
                font=("Arial", 11),
                text_color=color
            )
            # No space between "soft" and "ware" using (left, right) padding
            if i == 1:  # "soft"
                padx_val = (2, 0)  # normal left, no right
            elif i == 2:  # "ware"
                padx_val = (0, 2)  # no left, normal right
            else:
                padx_val = 2
            label.pack(side="left", padx=padx_val)

        # Bold "against"
        against_label = ctk.CTkLabel(
            center_frame,
            text="against",
            font=("Arial", 11, "bold"),
            text_color=rainbow_colors[4]  # soft blue
        )
        against_label.pack(side="left", padx=2)

        # List of terms to choose from
        self.val = [
            "fascism",
            "racism",
            "discrimination",
            "transphobia",
            "homophobia",
            "ableism",
            "sexism",
            "bigotry",
            "ageism",
            "terfs",
        ]

        # Pick random word once at startup
        random_word = random.choice(self.val)
        self.vwl = ctk.CTkLabel(
            center_frame,
            text=random_word + ".",
            font=("Arial", 11),
            text_color=rainbow_colors[5]  # soft purple
        )
        self.vwl.pack(side="left", padx=2)

    def _create_tray_icon(self):
        """Create a simple icon for system tray"""
        width = 64
        height = 64
        image = Image.new("RGB", (width, height), (30, 30, 30))
        dc = ImageDraw.Draw(image)

        # Draw a simple "G" shape
        dc.rectangle([16, 16, 48, 48], outline=(100, 150, 200), width=4)
        dc.rectangle([32, 28, 48, 36], fill=(100, 150, 200))

        return image

    def _setup_tray(self):
        """Setup system tray icon"""
        icon_image = self._create_tray_icon()

        menu = Menu(
            MenuItem("Show", self.show_from_tray, default=True),
            MenuItem("Quit", self.quit_app),
        )

        self.tray_icon = Icon(
            "Gate Director", icon_image, "Gate Assignment Director", menu
        )

        # Run tray icon in separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        """Hide window to system tray"""
        self.root.withdraw()

    def show_from_tray(self, icon=None, item=None):
        """Show window from system tray"""
        self.root.after(0, self.root.deiconify)

    def quit_app(self, icon=None, item=None):
        """Completely quit the application"""
        self.director.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def load_config_values(self):
        """Load values from YAML into UI fields"""
        try:
            # Reload config from file
            self.config = GADConfig.from_yaml()

            # Load other fields
            for field_name, entry in self.config_entries.items():
                value = getattr(self.config, field_name, "")
                # Format floats with .1f to always show at least one decimal place
                if isinstance(value, float):
                    value = f"{value:.1f}"
                else:
                    value = str(value)
                entry.delete(0, "end")
                entry.insert(0, value)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration:\n{e}")

    def save_config_values(self):
        """Save values from UI fields to YAML"""
        try:
            # Get other fields
            for field_name, entry in self.config_entries.items():
                value = entry.get().strip()

                # Convert to appropriate type based on config field type
                current_value = getattr(self.config, field_name)
                if isinstance(current_value, bool):
                    value = value.lower() in ('true', '1', 'yes')
                elif isinstance(current_value, int):
                    # For int fields, convert via float first to handle decimal inputs
                    value = int(float(value))
                elif isinstance(current_value, float):
                    value = float(value)

                setattr(self.config, field_name, value)

            # Save to YAML
            self.config.save_yaml()

            messagebox.showinfo("Success", "Configuration saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")

    def ic(self):
        r_e = ["m", "m", "n", "a", "a", "m", "m", "y"]

        if not hasattr(self, 'vwl') or not self.val or not self.vwl:
            messagebox.showerror("Integrity Check Failed", "Check your integrity. Reflect yourself.")
            self.root.destroy()
            import sys
            sys.exit(1)

        # Verify required patterns are present
        for e in r_e:
            if not any(word.rstrip('.').endswith(e) for word in self.val):
                messagebox.showerror("Integrity Check Failed", "Check your integrity. Reflect yourself.")
                self.root.destroy()
                import sys
                sys.exit(1)

    def _setup_logging(self):
        """Redirect logging to the log textbox"""

        class TextBoxHandler(logging.Handler):
            def __init__(self, text_widget, activity_widget):
                super().__init__()
                self.text_widget = text_widget
                self.activity_widget = activity_widget

            def emit(self, record):
                msg = self.format(record) + "\n"
                self.text_widget.after(0, lambda: self._append(msg))

                # Show simplified errors in Recent Activity for user-relevant issues
                if record.levelno >= logging.ERROR:
                    simplified_msg = self._simplify_error_for_activity(record)
                    if simplified_msg:
                        self.activity_widget.after(0, lambda m=simplified_msg: self._append_activity(m + "\n"))

            def _simplify_error_for_activity(self, record):
                """Convert technical errors to user-friendly messages for Recent Activity"""
                msg = record.getMessage().lower()

                # Suppress warnings about uncertain assignments (already shown via callback)
                if "uncertain" in msg or "might have succeeded" in msg:
                    return None

                # Suppress low-level GSX menu errors (they're often transient/expected)
                if "menu" in msg and any(x in msg for x in ["failed to read", "empty", "timeout"]):
                    return "GSX menu issue - check logs if persistent"

                # Connection failures (important)
                if "simconnect" in msg or "connection" in msg:
                    return "Connection issue - check simulator"

                # GSX initialization failures (important)
                if "failed to initialize gsx" in msg:
                    return "GSX initialization failed - check setup"

                # Gate assignment failures (user-relevant)
                if "gate assignment failed" in msg:
                    return None  # Already logged by our success/failure messages

                # API errors (somewhat important)
                if "api" in msg and "error" in msg:
                    return "API communication issue"

                # For other errors, show generic message
                if record.levelno >= logging.ERROR:
                    return "Unexpected issue - check logs for details"

                return None

            def _append(self, msg):
                self.text_widget.configure(state="normal")
                self.text_widget.insert("end", msg)
                self.text_widget.see("end")
                self.text_widget.configure(state="disabled")

            def _append_activity(self, msg):
                self.activity_widget.configure(state="normal")
                self.activity_widget.insert("end", msg)
                self.activity_widget.see("end")
                self.activity_widget.configure(state="disabled")

        handler = TextBoxHandler(self.log_text, self.activity_text)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
            )
        )
        logging.getLogger().addHandler(handler)

    def start_monitoring(self):
        """Start the monitoring process"""
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal", text_color="#4a4050")
        self.status_label.configure(text="Monitoring", text_color=c('sage'))

        if self.apply_override_btn:
            self.apply_override_btn.configure(state="disabled")
        if self.clear_override_btn:
            self.clear_override_btn.configure(state="disabled")

        self._append_activity("Starting monitoring...\n")

        threading.Timer(0.5, self._continue_monitoring_startup).start()

    def _continue_monitoring_startup(self):
        """Continue monitoring startup after initial pause"""
        self._append_activity("Initializing monitoring system...\n")

        # Set up status callback for director to update UI
        self.director.status_callback = self._report_director_status

        # Start director in separate thread
        self.process_thread = threading.Thread(target=self._run_director, daemon=True)
        self.process_thread.start()

        # Schedule airport update with debouncing
        self._schedule_airport_update(
            self.director.departure_airport,
            self.director.current_airport
        )

    def _report_director_status(self, message: str):
        """Handle status updates from director (called from background thread)"""
        # Use after() to safely update UI from background thread
        self.activity_text.after(0, lambda: self._append_activity(f"{message}\n"))

    def _run_director(self):
        """Run the director (called in thread)"""
        try:
            self.director.start_monitoring(self.config.flight_json_path)
            self.director.process_gate_assignments()
        except Exception as e:
            logging.error(f"Director error: {e}")

    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.director.stop()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled", text_color="#e8d9d6")
        self.status_label.configure(text="Stopped", text_color="#C67B7B")

        if self.apply_override_btn:
            self.apply_override_btn.configure(state="normal")
        if self.clear_override_btn:
            self.clear_override_btn.configure(state="normal")

        self._append_activity("Monitoring stopped.\n")

    def toggle_override_section(self):
        """Toggle the manual override section visibility"""
        if self.override_section_visible:
            # Hide the panel
            self.override_panel.pack_forget()
            self.override_toggle_btn.configure(text="▼ Manual Override")
            self.root.minsize(350, 430)
            self.override_section_visible = False
        else:
            # Show the panel
            self.override_panel.pack(fill="x", pady=(5, 0))
            self.override_toggle_btn.configure(text="▲ Manual Override")
            self.root.minsize(470, 500)
            self.override_section_visible = True

    def apply_override(self):
        """Apply manual override values"""
        airport = self.override_airport_entry.get().strip()
        terminal = self.override_terminal_entry.get().strip()
        gate = self.override_gate_entry.get().strip()

        if not airport:
            messagebox.showwarning("Missing Data", "Airport is required for override.")
            return

        self.override_active = True
        self.override_airport = airport
        self.override_terminal = terminal
        self.override_gate = gate
        self.current_airport = airport
        self.director.airport_override = airport

        self.airport_label.configure(
            text=f"{airport} (MANUAL)",
            text_color="#D4A574"
        )

        self._append_activity(f"Manual override applied: {airport} Terminal {terminal} Gate {gate}\n")
        logging.info(f"Manual override: Airport={airport}, Terminal={terminal}, Gate={gate}")

    def clear_override(self):
        """Clear manual override"""
        self.override_active = False
        self.override_airport = None
        self.override_terminal = None
        self.override_gate = None
        self.director.airport_override = None

        self.override_airport_entry.delete(0, "end")
        self.override_terminal_entry.delete(0, "end")
        self.override_gate_entry.delete(0, "end")

        self.current_airport = self.director.current_airport
        self._schedule_airport_update(
            self.director.departure_airport,
            self.director.current_airport
        )

        self._append_activity("Manual override cleared.\n")
        logging.info("Manual override cleared")

    def assign_gate_manual(self):
        """Manually trigger gate assignment"""
        if self.override_active:
            airport = self.override_airport
            terminal = self.override_terminal or ""
            gate = self.override_gate or ""
        else:
            if not self.current_airport:
                messagebox.showerror("Error", "No airport data available. Set manual override or start monitoring.")
                return
            airport = self.director.current_airport
            terminal = ""
            gate = ""

        if not gate:
            messagebox.showwarning("Missing Gate", "No gate information available. Please set manual override with gate details.")
            return

        self._append_activity(f"Assigning gate: {airport} Terminal {terminal} Gate {gate}\n")

        # Initialize GSX if needed and assign
        if not self.director.gsx or not self.director.gsx.is_initialized:
            self.director.gsx = GsxHook(self.director.config, enable_menu_logging=True)
            if not self.director.gsx.is_initialized:
                messagebox.showerror("Error", "Failed to initialize GSX Hook")
                return

        # Trigger assignment
        threading.Thread(
            target=self._assign_gate_thread,
            args=(airport, terminal, gate),
            daemon=True
        ).start()

    def _assign_gate_thread(self, airport, terminal, gate):
        """Run gate assignment in background thread"""
        try:
            success, assigned_gate = self.director.gsx.assign_gate_when_ready(
                airport=airport,
                terminal=terminal,
                gate_number=gate,
                wait_for_ground=True,
            )
            if success and assigned_gate:
                gate_name = assigned_gate.get('gate', 'Unknown')
                success_msg = f"Successfully assigned to gate: {gate_name}\n"
                self.activity_text.after(0, lambda msg=success_msg: self._append_activity(msg))
                logging.info(f"Manual gate assignment succeeded: {gate_name}")
            else:
                self.activity_text.after(0, lambda: self._append_activity("Gate assignment failed\n"))
                logging.info("Manual gate assignment failed")
        except Exception as e:
            error_msg = f"Gate assignment error: {e}"
            logging.error(error_msg)
            self.activity_text.after(0, lambda msg=error_msg: self._append_activity(f"{msg}\n"))

    def edit_gates(self):
        """Open gate management window"""
        if not self.current_airport:
            messagebox.showwarning(
                "No Airport Detected",
                "No airport has been detected yet. Using default EDDS.\n\n"
                "Start monitoring and wait for a gate assignment to automatically detect the airport."
            )

        # Pass gate_assignment reference if available
        gate_assignment = None
        if self.director.gsx and self.director.gsx.is_initialized:
            gate_assignment = self.director.gsx.gate_assignment

        GateManagementWindow(self.root, self.current_airport, gate_assignment)

    def save_logs(self):
        """Save logs to file with date-stamped default filename"""
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"GAD_log_{current_date}.txt"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                log_content = self.log_text.get("1.0", "end-1c")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)
                logging.info(f"Logs saved to {file_path}")
            except Exception as e:
                logging.error(f"Failed to save logs: {e}")
                messagebox.showerror("Save Error", f"Failed to save logs: {e}")

    def clear_logs(self):
        """Clear all logs from the log textbox"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _format_airport_display(self, departure: Optional[str], destination: Optional[str]) -> str:
        """Format airport display text based on departure and destination"""
        if destination:
            if departure:
                return f"{departure} to {destination}"
            else:
                return f"to {destination}"
        else:
            if departure:
                return f"{departure} to ..."
            else:
                return "to ..."

    def _schedule_airport_update(self, departure: Optional[str], destination: Optional[str]):
        """Schedule an airport label update with debouncing to avoid flickering"""
        if self.override_active:
            return

        if self._airport_update_pending:
            self.root.after_cancel(self._airport_update_pending)

        # Store the values we want to display
        self._last_known_departure = departure
        self._last_known_destination = destination

        # Schedule update after 300ms delay (allows multiple rapid changes to settle)
        self._airport_update_pending = self.root.after(300, self._apply_airport_update)

    def _apply_airport_update(self):
        """Apply the pending airport label update"""
        self._airport_update_pending = None
        airport_text = self._format_airport_display(
            self._last_known_departure,
            self._last_known_destination
        )
        color = c('sage') if self._last_known_destination else c('mustard')
        self.airport_label.configure(text=airport_text, text_color=color)

    def _append_activity(self, message: str):
        """Append message to activity text (handles read-only state)"""
        self.activity_text.configure(state="normal")
        self.activity_text.insert("end", message)
        self.activity_text.see("end")
        self.activity_text.configure(state="disabled")

    def _on_tab_change(self):
        """Handle tab change events to adjust window size"""
        current_tab = self.tabview.get()

        if current_tab == "Config":
            # Config tab needs more vertical space for all settings
            self.root.minsize(470, 500)
        elif current_tab == "Monitor" and not self.override_active:
            # Monitor tab without override can be smaller
            self.root.minsize(350, 430)
        elif current_tab == "Monitor" and self.override_active:
            # Monitor tab with override needs more space
            self.root.minsize(470, 500)
        else:
            # Logs and other tabs use default size
            self.root.minsize(350, 430)

    def _update_ui_state(self):
        """Periodically update UI state from director"""
        # Don't update airport from director if override is active
        if not self.override_active:
            if self.director.current_airport != self.current_airport or self.director.departure_airport != self._last_known_departure:
                self.current_airport = self.director.current_airport
                self._schedule_airport_update(
                    self.director.departure_airport,
                    self.director.current_airport
                )

        # Enable/disable Assign Gate button based on available data
        has_data = self.current_airport is not None and (
            self.override_active or self.director.current_airport
        )
        if has_data and self.override_active and self.override_gate:
            self.assign_gate_btn.configure(state="normal", text_color="#30384a")
        elif has_data and not self.override_active:
            # Only enable if we have gate data from monitoring (future: track this in director)
            self.assign_gate_btn.configure(state="disabled", text_color="#cbd4e6")
        else:
            self.assign_gate_btn.configure(state="disabled", text_color="#cbd4e6")

        # Schedule next update (every 500ms)
        self.root.after(500, self._update_ui_state)

    def run(self):
        """Start the UI main loop"""
        self.root.mainloop()
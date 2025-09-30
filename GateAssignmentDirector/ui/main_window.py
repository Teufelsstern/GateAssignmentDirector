"""Main window class for the Gate Assignment Director UI"""

import customtkinter as ctk
import threading
import logging
from tkinter import messagebox
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

from director import GateAssignmentDirector
from GateAssignmentDirector.config import GsxConfig
from GateAssignmentDirector.gsx_hook import GsxHook
from GateAssignmentDirector.ui.gate_management import GateManagementWindow
from GateAssignmentDirector.ui.monitor_tab import setup_monitor_tab
from GateAssignmentDirector.ui.logs_tab import setup_logs_tab
from GateAssignmentDirector.ui.config_tab import setup_config_tab


class DirectorUI:
    def __init__(self):
        self.director = GateAssignmentDirector()
        self.process_thread = None
        self.tray_icon = None
        self.config = GsxConfig.from_yaml()
        self.current_airport = None
        self.override_active = False
        self.override_airport = None
        self.override_terminal = None
        self.override_gate = None
        self.override_section_visible = False

        # Setup main window
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Gate Assignment Director")
        self.root.geometry("700x500")

        # Set size constraints
        self.root.minsize(600, 450)
        self.root.maxsize(900, 700)

        # Override close button to minimize to tray
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # Setup system tray
        self._setup_tray()

        # Create tabview
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Add tabs
        self.tabview.add("Monitor")
        self.tabview.add("Logs")
        self.tabview.add("Config")

        # Setup each tab using dedicated modules
        setup_monitor_tab(self, self.tabview.tab("Monitor"))
        setup_logs_tab(self, self.tabview.tab("Logs"))
        setup_config_tab(self, self.tabview.tab("Config"))

        # Redirect logging to text widget
        self._setup_logging()

        # Start periodic UI updates
        self._update_ui_state()

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
            self.config = GsxConfig.from_yaml()

            # Load other fields
            for field_name, entry in self.config_entries.items():
                value = getattr(self.config, field_name, "")
                entry.delete(0, "end")
                entry.insert(0, str(value))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration:\n{e}")

    def save_config_values(self):
        """Save values from UI fields to YAML"""
        try:
            # Get other fields
            for field_name, entry in self.config_entries.items():
                value = entry.get().strip()

                # Convert to appropriate type
                current_value = getattr(self.config, field_name)
                if isinstance(current_value, float):
                    value = float(value)
                elif isinstance(current_value, int):
                    value = int(value)

                setattr(self.config, field_name, value)

            # Save to YAML
            self.config.save_yaml()

            messagebox.showinfo("Success", "Configuration saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")

    def _setup_logging(self):
        """Redirect logging to the log textbox"""

        class TextBoxHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record) + "\n"
                self.text_widget.after(0, lambda: self._append(msg))

            def _append(self, msg):
                self.text_widget.insert("end", msg)
                self.text_widget.see("end")

        handler = TextBoxHandler(self.log_text)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
            )
        )
        logging.getLogger().addHandler(handler)

    def start_monitoring(self):
        """Start the monitoring process"""
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="Monitoring", text_color="#4a9d2a")

        self.activity_text.insert("end", "Starting monitoring...\n")

        # Start director in separate thread
        self.process_thread = threading.Thread(target=self._run_director, daemon=True)
        self.process_thread.start()

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
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="Stopped", text_color="#a83232")

        self.activity_text.insert("end", "Monitoring stopped.\n")

    def toggle_override_section(self):
        """Toggle the manual override section visibility"""
        if self.override_section_visible:
            # Hide the panel
            self.override_panel.pack_forget()
            self.override_toggle_btn.configure(text="▼ Manual Override")
            self.override_section_visible = False
        else:
            # Show the panel
            self.override_panel.pack(fill="x", pady=(5, 0))
            self.override_toggle_btn.configure(text="▲ Manual Override")
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

        # Update airport display
        self.airport_label.configure(
            text=f"{airport} (MANUAL)",
            text_color="#ff8c00"  # Orange
        )

        self.activity_text.insert("end", f"Manual override applied: {airport} Terminal {terminal} Gate {gate}\n")
        logging.info(f"Manual override: Airport={airport}, Terminal={terminal}, Gate={gate}")

    def clear_override(self):
        """Clear manual override"""
        self.override_active = False
        self.override_airport = None
        self.override_terminal = None
        self.override_gate = None

        # Clear entry fields
        self.override_airport_entry.delete(0, "end")
        self.override_terminal_entry.delete(0, "end")
        self.override_gate_entry.delete(0, "end")

        # Reset current_airport to director's value
        self.current_airport = self.director.current_airport

        self.activity_text.insert("end", "Manual override cleared.\n")
        logging.info("Manual override cleared")

    def assign_gate_manual(self):
        """Manually trigger gate assignment"""
        if not self.current_airport:
            messagebox.showerror("Error", "No airport data available. Set manual override or start monitoring.")
            return

        # Get gate data from override or director
        if self.override_active:
            airport = self.override_airport
            terminal = self.override_terminal or ""
            gate = self.override_gate or ""
        else:
            # Get from director's last gate info
            airport = self.director.current_airport
            # Need to get terminal/gate from director - for now use empty
            terminal = ""
            gate = ""

        if not gate:
            messagebox.showwarning("Missing Gate", "No gate information available. Please set manual override with gate details.")
            return

        self.activity_text.insert("end", f"Assigning gate: {airport} Terminal {terminal} Gate {gate}\n")

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
            success = self.director.gsx.assign_gate_when_ready(
                airport=airport,
                terminal=terminal,
                gate_number=gate,
                wait_for_ground=True,
            )
            result = "completed" if success else "failed"
            self.activity_text.after(0, lambda: self.activity_text.insert("end", f"Gate assignment {result}\n"))
            logging.info(f"Manual gate assignment {result}")
        except Exception as e:
            logging.error(f"Gate assignment error: {e}")
            self.activity_text.after(0, lambda: self.activity_text.insert("end", f"Gate assignment error: {e}\n"))

    def edit_gates(self):
        """Open gate management window"""
        if not self.current_airport:
            messagebox.showwarning(
                "No Airport Detected",
                "No airport has been detected yet. Using default EDDS.\n\n"
                "Start monitoring and wait for a gate assignment to automatically detect the airport."
            )
        GateManagementWindow(self.root, self.current_airport)

    def _update_ui_state(self):
        """Periodically update UI state from director"""
        # Don't update airport from director if override is active
        if not self.override_active:
            if self.director.current_airport != self.current_airport:
                self.current_airport = self.director.current_airport
                if self.current_airport:
                    self.airport_label.configure(
                        text=self.current_airport,
                        text_color="#4a9d2a"
                    )
                else:
                    self.airport_label.configure(
                        text="None",
                        text_color="#808080"
                    )

        # Enable/disable Assign Gate button based on available data
        has_data = self.current_airport is not None and (
            self.override_active or self.director.current_airport
        )
        if has_data and self.override_active and self.override_gate:
            self.assign_gate_btn.configure(state="normal")
        elif has_data and not self.override_active:
            # Only enable if we have gate data from monitoring (future: track this in director)
            self.assign_gate_btn.configure(state="disabled")
        else:
            self.assign_gate_btn.configure(state="disabled")

        # Schedule next update (every 500ms)
        self.root.after(500, self._update_ui_state)

    def run(self):
        """Start the UI main loop"""
        self.root.mainloop()
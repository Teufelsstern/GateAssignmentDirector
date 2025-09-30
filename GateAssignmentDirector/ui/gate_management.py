"""Gate Management Window for editing airport gate configurations"""

import customtkinter as ctk
import json
import logging
import os
import re
from tkinter import ttk

from GateAssignmentDirector.ui.ui_helpers import _label, _button


class GateManagementWindow:
    def __init__(self, parent, airport=None):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Gate Management")
        self.window.geometry("900x600")
        self.window.minsize(800, 500)

        # Use provided airport or default to EDDS
        airport = airport or "EDDS"
        self.json_path = f".\\gsx_menu_logs\\{airport}_interpreted.json"
        self.data = None

        # Main container
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Tree view
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        _label(
            frame=left_frame,
            text="Current Gate Structure",
            size=13,
            pady=(10, 5),
        )

        # Tree view (using tkinter's ttk.Treeview for hierarchical display)
        tree_container = ctk.CTkFrame(left_frame, fg_color="#1a1a1a")
        tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configure tree with columns
        self.tree = ttk.Treeview(
            tree_container,
            selectmode="browse",
            columns=('size', 'jetways', 'terminal', 'type'),
            show='tree headings'
        )

        # Configure column headings and widths
        self.tree.heading('#0', text='Gate')
        self.tree.column('#0', width=150, minwidth=100)

        self.tree.heading('size', text='Size')
        self.tree.column('size', width=80, minwidth=60)

        self.tree.heading('jetways', text='Jetways')
        self.tree.column('jetways', width=70, minwidth=50)

        self.tree.heading('terminal', text='Terminal')
        self.tree.column('terminal', width=100, minwidth=80)

        self.tree.heading('type', text='Type')
        self.tree.column('type', width=80, minwidth=60)

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Reload button
        _button(
            frame=left_frame,
            text="Reload Data",
            command=self.load_data,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            pady=(0, 10)
        )

        # Right side - Controls
        right_frame = ctk.CTkFrame(main_frame, width=350)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)

        # Terminal Management Section
        terminal_frame = ctk.CTkFrame(right_frame)
        terminal_frame.pack(fill="x", padx=10, pady=10)

        _label(terminal_frame, text="Terminal Management", pady=(10, 5))
        _label(
            terminal_frame,
            text="Active terminals (comma-separated):",
            size=10,
            pady=(5, 0),
            padx=(10, 0)
        )

        self.active_terminals_entry = ctk.CTkEntry(
            terminal_frame, placeholder_text="e.g., 1, 2, 3"
        )
        self.active_terminals_entry.pack(fill="x", padx=10, pady=5)

        _button(
            terminal_frame,
            self.convert_to_parking,
            text="Convert Others to Parking",
            height=32,
            fg_color="#2d5016",
            hover_color="#3d6622",
            padx=(10, 10),
            pady=(5, 10)
        )

        # Gate Movement Section
        gate_frame = ctk.CTkFrame(right_frame)
        gate_frame.pack(fill="x", padx=10, pady=10)

        _label(gate_frame, text="Move Gate", pady=(10, 5))
        _label(gate_frame, text="Gate number:", size=10, pady=(5, 0), padx=(10, 0))

        self.gate_entry = ctk.CTkEntry(gate_frame, placeholder_text="e.g., 71")
        self.gate_entry.pack(fill="x", padx=10, pady=5)

        _label(gate_frame, text="From terminal:", size=10, pady=(5, 0), padx=(10, 0))

        self.from_terminal_entry = ctk.CTkEntry(gate_frame, placeholder_text="e.g., 7")
        self.from_terminal_entry.pack(fill="x", padx=10, pady=5)

        _label(gate_frame, text="To terminal:", size=10, pady=(5, 0), padx=(10, 0))

        self.to_terminal_entry = ctk.CTkEntry(gate_frame, placeholder_text="e.g., 8")
        self.to_terminal_entry.pack(fill="x", padx=10, pady=5)

        _button(
            gate_frame,
            self.move_gate,
            text="Move Gate",
            height=32,
            fg_color="#2d5016",
            hover_color="#3d6622",
            padx=(10, 10),
            pady=(5, 10)
        )

        # Status log
        log_frame = ctk.CTkFrame(right_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        _label(log_frame, text="Status", size=10, pady=(5, 0))

        self.status_text = ctk.CTkTextbox(
            log_frame, font=("Consolas", 11), fg_color="#1a1a1a", height=100
        )
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Save button
        _button(
            right_frame,
            self.save_data,
            text="Save Changes",
            height=35,
            fg_color="#5a1a1a",
            hover_color="#6e2828",
            padx=(10, 10),
            pady=(0, 10)
        )

        # Auto-load data if airport is provided
        if airport:
            self.load_data()
        else:
            self.log_status("No airport detected. Start monitoring or manually specify airport in main window.")

    def _parse_gate_size(self, full_text: str) -> str:
        """Extract aircraft size from gate full_text with defensive parsing."""
        if not full_text:
            return "Unknown"
        match = re.search(r'(Small|Medium|Heavy|Ramp GA \w+)', full_text)
        return match.group(1) if match else "Unknown"

    def _parse_jetway_count(self, full_text: str) -> str:
        """Extract jetway configuration from gate full_text with defensive parsing."""
        if not full_text:
            return "-"
        match = re.search(r'(\d+x\s*/J|None)', full_text)
        return match.group(1).strip() if match else "-"

    def load_data(self):
        """Load JSON data and populate tree"""
        # Check if file exists
        if not os.path.exists(self.json_path):
            self.log_status(f"Airport data not found at {self.json_path}")
            self.log_status("Start monitoring to generate data or manually specify airport.")
            return

        try:
            with open(self.json_path, "r") as f:
                self.data = json.load(f)

            # Clear existing tree
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Populate tree
            terminals = self.data.get("terminals", {})
            for terminal_name, gates in terminals.items():
                # Terminal parent node - populate terminal column only
                terminal_node = self.tree.insert(
                    "", "end",
                    text=f"Terminal: {terminal_name}",
                    values=('', '', terminal_name, ''),
                    open=True
                )

                for gate_num, gate_info in gates.items():
                    # Extract gate information with defensive parsing
                    full_text = gate_info.get("raw_info", {}).get("full_text", "")
                    gate_type = gate_info.get("type", "Unknown")

                    # Parse size and jetway info
                    size = self._parse_gate_size(full_text)
                    jetways = self._parse_jetway_count(full_text)

                    # Insert gate with column data
                    self.tree.insert(
                        terminal_node, "end",
                        text=f"Gate {gate_num}",
                        values=(size, jetways, terminal_name, gate_type)
                    )

            self.log_status("Data loaded successfully")

        except Exception as e:
            self.log_status(f"Error loading data: {e}")

    def convert_to_parking(self):
        """Convert non-active terminals to parking"""
        try:
            self.log_status("Starting conversion...")

            if not self.data:
                self.log_status("ERROR: Please load data first")
                return

            active_str = self.active_terminals_entry.get().strip()
            if not active_str:
                self.log_status("ERROR: Please specify active terminals")
                return

            # Parse active terminals
            active_terminals = [t.strip() for t in active_str.split(",")]
            self.log_status(f"Active terminals: {active_terminals}")

            terminals = self.data.get("terminals", {})
            converted_count = 0

            for terminal_name in list(terminals.keys()):
                if terminal_name not in active_terminals:
                    # Convert all gates in this terminal to parking type
                    for gate_num, gate_info in list(terminals[terminal_name].items()):
                        gate_info["type"] = "parking"
                        converted_count += 1
                        # Move the gate
                        gate_data = terminals[terminal_name].pop(gate_num)
                        gate_data["terminal"] = "Parking"

                        # Create destination terminal if it doesn't exist
                        if "Parking" not in terminals:
                            terminals["Parking"] = {}

                        terminals["Parking"][gate_num] = gate_data
                    if len(terminals[terminal_name]) == 0:
                        terminals.pop(terminal_name)

            self.log_status(f"Converted {converted_count} gates to parking")
            self.save_data()
            self.load_data()  # Refresh tree view

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")
            logging.error(f"Conversion error: {e}", exc_info=True)

    def move_gate(self):
        """Move a gate from one terminal to another"""
        try:
            logging.debug("Starting gate move...")

            if not self.data:
                logging.error("ERROR: Please load data first")
                return

            gate_num = self.gate_entry.get().strip()
            from_terminal = self.from_terminal_entry.get().strip()
            to_terminal = self.to_terminal_entry.get().strip()

            if not all([gate_num, from_terminal, to_terminal]):
                logging.error("ERROR: Please fill all fields")
                return

            terminals = self.data.get("terminals", {})

            # Check if source exists
            if from_terminal not in terminals:
                logging.error(f"ERROR: Terminal {from_terminal} not found")
                return

            if gate_num not in terminals[from_terminal]:
                logging.error(
                    f"ERROR: Gate {gate_num} not found in Terminal {from_terminal}"
                )
                return

            # Move the gate
            gate_data = terminals[from_terminal].pop(gate_num)
            gate_data["terminal"] = to_terminal

            # Create destination terminal if it doesn't exist
            if to_terminal not in terminals:
                terminals[to_terminal] = {}

            terminals[to_terminal][gate_num] = gate_data

            self.log_status(
                f"SUCCESS: Moved Gate {gate_num} from Terminal {from_terminal} to {to_terminal}"
            )
            self.save_data()
            self.load_data()  # Refresh tree view

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")
            logging.error(f"Move gate error: {e}", exc_info=True)

    def save_data(self):
        """Save modified data back to JSON"""
        if not self.data:
            self.log_status("No data to save")
            return

        try:
            with open(self.json_path, "w") as f:
                json.dump(self.data, f, indent=2)

            self.log_status("Changes saved successfully!")
            logging.info("Gate configuration saved")

        except Exception as e:
            self.log_status(f"Error saving: {e}")

    def log_status(self, message):
        """Add message to status log"""
        self.status_text.insert("end", f"{message}\n")
        self.status_text.see("end")
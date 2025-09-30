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
        self.window.geometry("1000x700")
        self.window.minsize(1000, 700)

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
            size=20,
            pady=(10, 5),
        )

        # Tree view (using tkinter's ttk.Treeview for hierarchical display)
        tree_container = ctk.CTkFrame(left_frame, fg_color="#1a1a1a")
        tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configure tree with columns
        self.tree = ttk.Treeview(
            tree_container,
            selectmode="browse",
            columns=('size', 'jetways', 'terminal', 'fulltext'),
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

        self.tree.heading('fulltext', text='Full Text')
        self.tree.column('fulltext', width=200, minwidth=150)

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Bottom controls frame (below tree)
        bottom_frame = ctk.CTkFrame(left_frame)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        # Status log (takes most of the width)
        status_frame = ctk.CTkFrame(bottom_frame)
        status_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        _label(status_frame, text="Status", size=14, pady=(5, 0))

        self.status_text = ctk.CTkTextbox(
            status_frame, font=("Consolas", 12), fg_color="#1a1a1a", height=80
        )
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Buttons stacked vertically on the right
        buttons_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        buttons_frame.pack(side="right", fill="x")

        _button(
            buttons_frame,
            self.load_data,
            text="Reload Data",
            height=14,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            pady=(15, 5),
        )

        _button(
            buttons_frame,
            self.save_data,
            text="Save Changes",
            height=14,
            fg_color="#5a1a1a",
            hover_color="#6e2828",
            pady=(0, 0),
        )

        # Right side - Controls
        right_frame = ctk.CTkFrame(main_frame, width=350)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)

        # Terminal Management Section
        terminal_frame = ctk.CTkFrame(right_frame)
        terminal_frame.pack(fill="x", padx=10, pady=10)

        _label(terminal_frame, text="Terminal Management", size=16, pady=(10, 5))
        _label(
            terminal_frame,
            text="Active terminals (comma-separated):",
            size=16,
            pady=(5, 0),
            padx=(10, 0)
        )

        self.active_terminals_entry = ctk.CTkEntry(
            terminal_frame, placeholder_text="e.g., 1, 2, 3", placeholder_text_color="#5a5a5a"
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

        _label(gate_frame, text="Move Gate", size=16, pady=(10, 5))

        # Gate number row
        gate_row = ctk.CTkFrame(gate_frame, fg_color="transparent")
        gate_row.pack(fill="x", padx=10, pady=0)
        _label(gate_row, text="Gate:", size=16, padx=(0, 2), side="left")
        self.gate_entry = ctk.CTkEntry(gate_row, placeholder_text="71", width=50)
        self.gate_entry.pack(side="left", padx=(0, 15))

        # From and To on same row
        from_to_row = ctk.CTkFrame(gate_frame, fg_color="transparent")
        from_to_row.pack(fill="x", padx=10, pady=0)
        _label(from_to_row, text="From:", size=16, padx=(0, 2), side="left")
        self.from_terminal_entry = ctk.CTkEntry(from_to_row, placeholder_text="7", placeholder_text_color="#5a5a5a", width=50)
        self.from_terminal_entry.pack(side="left", padx=(0, 15))
        _label(from_to_row, text="To:", size=16, padx=(0, 2), side="left")
        self.to_terminal_entry = ctk.CTkEntry(from_to_row, placeholder_text="8", placeholder_text_color="#5a5a5a", width=50)
        self.to_terminal_entry.pack(side="left")

        _button(
            gate_frame,
            self.move_gate,
            text="Move Gate",
            height=28,
            fg_color="#2d5016",
            hover_color="#3d6622",
            padx=(10, 10),
            pady=(5, 10)
        )

        # Gate Rename Section
        rename_frame = ctk.CTkFrame(right_frame)
        rename_frame.pack(fill="x", padx=10, pady=10)

        _label(rename_frame, text="Rename Gate", size=16, pady=(10, 5))

        # Gate and Terminal on same row
        gate_terminal_row = ctk.CTkFrame(rename_frame, fg_color="transparent")
        gate_terminal_row.pack(fill="x", padx=10, pady=0)
        _label(gate_terminal_row, text="Gate:", size=16, padx=(0, 2), side="left")
        self.rename_gate_entry = ctk.CTkEntry(gate_terminal_row, placeholder_text="71", placeholder_text_color="#5a5a5a", width=50)
        self.rename_gate_entry.pack(side="left", padx=(0, 15))
        _label(gate_terminal_row, text="Terminal:", size=16, padx=(0, 2), side="left")
        self.rename_terminal_entry = ctk.CTkEntry(gate_terminal_row, placeholder_text="3", placeholder_text_color="#5a5a5a", width=50)
        self.rename_terminal_entry.pack(side="left")

        # Full text row
        _label(rename_frame, text="New full text:", size=16, pady=(5, 0), padx=(10, 0))
        self.new_fulltext_entry = ctk.CTkEntry(rename_frame, placeholder_text="Gate 71 - Medium - 2x  /J", placeholder_text_color="#5a5a5a")
        self.new_fulltext_entry.pack(fill="x", padx=10, pady=(0, 5))

        _button(
            rename_frame,
            self.rename_gate,
            text="Rename Gate",
            height=28,
            fg_color="#2d5016",
            hover_color="#3d6622",
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

                    # Parse size and jetway info
                    size = self._parse_gate_size(full_text)
                    jetways = self._parse_jetway_count(full_text)

                    # Insert gate with column data
                    self.tree.insert(
                        terminal_node, "end",
                        text=f"Gate {gate_num}",
                        values=(size, jetways, terminal_name, full_text or "-")
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

    def rename_gate(self):
        """Rename a gate's full_text information"""
        try:
            logging.debug("Starting gate rename...")

            if not self.data:
                self.log_status("ERROR: Please load data first")
                return

            gate_num = self.rename_gate_entry.get().strip()
            terminal = self.rename_terminal_entry.get().strip()
            new_full_text = self.new_fulltext_entry.get().strip()

            if not all([gate_num, terminal, new_full_text]):
                self.log_status("ERROR: Please fill all fields")
                return

            terminals = self.data.get("terminals", {})

            # Check if terminal exists
            if terminal not in terminals:
                self.log_status(f"ERROR: Terminal {terminal} not found")
                return

            # Check if gate exists in terminal
            if gate_num not in terminals[terminal]:
                self.log_status(
                    f"ERROR: Gate {gate_num} not found in Terminal {terminal}"
                )
                return

            # Update the full_text
            terminals[terminal][gate_num]["raw_info"]["full_text"] = new_full_text

            self.log_status(
                f"SUCCESS: Renamed Gate {gate_num} in Terminal {terminal}"
            )
            self.save_data()
            self.load_data()  # Refresh tree view

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")
            logging.error(f"Rename gate error: {e}", exc_info=True)

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
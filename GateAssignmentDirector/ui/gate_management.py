"""Gate Management Window for editing airport gate configurations"""

# Licensed under GPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import customtkinter as ctk
import json
import logging
import os
import re
import sys
from pathlib import Path
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from GateAssignmentDirector.ui.ui_helpers import _label, _button, c


class GateManagementWindow:
    def __init__(self, parent, airport=None, gate_assignment=None):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Gate Management")
        self.window.geometry("1000x700")
        self.window.minsize(1000, 700)
        self.gate_assignment = gate_assignment

        def set_icon():
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS)
                icon_path = base_path / "GateAssignmentDirector" / "icon.ico"
            else:
                icon_path = Path(__file__).parent.parent / "icon.ico"

            if icon_path.exists():
                try:
                    icon_img = Image.open(str(icon_path))
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.window.iconphoto(False, icon_photo)
                    self.window._icon_photo = icon_photo
                except Exception as e:
                    logging.debug(f"Failed to set icon: {e}")

        self.window.after(200, set_icon)

        self.airport = airport or "EDDS"
        self.json_path = f".\\gsx_menu_logs\\{self.airport}_interpreted.json"
        self.data = None
        self.has_unsaved_changes = False

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        _label(
            frame=left_frame,
            text="Current Gate Structure",
            size=20,
            pady=(10, 5),
        )

        tree_container = ctk.CTkFrame(left_frame, fg_color="#1a1a1a")
        tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            tree_container,
            selectmode="extended",
            columns=('size', 'jetways', 'terminal', 'fulltext'),
            show='tree headings'
        )
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

        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        bottom_frame = ctk.CTkFrame(left_frame)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        status_frame = ctk.CTkFrame(bottom_frame)
        status_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        _label(status_frame, text="Status", size=14, pady=(5, 0))

        self.status_text = ctk.CTkTextbox(
            status_frame, font=("Consolas", 12), fg_color="#1a1a1a", height=80
        )
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)

        buttons_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        buttons_frame.pack(side="right", fill="x")

        _button(
            buttons_frame,
            self.reset_data,
            text="Reset Data",
            height=28,
            fg_color=c('dusty_rose'),
            hover_color=c('dusty_rose', hover=True),
            text_color=c('sage_dark'),
            pady=(15, 2),
        )

        _button(
            buttons_frame,
            self.load_data,
            text="Reload Data",
            height=28,
            fg_color=c('periwinkle'),
            hover_color=c('periwinkle', hover=True),
            text_color=c('sage_dark'),
            pady=(2, 5),
        )

        _button(
            buttons_frame,
            self.save_data,
            text="Save Changes",
            height=28,
            fg_color=c('sage'),
            hover_color=c('sage', hover=True),
            text_color=c('sage_dark'),
            pady=(0, 0),
        )

        right_frame = ctk.CTkFrame(main_frame, width=350)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)

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
            terminal_frame,
            placeholder_text="e.g., 1, 2, 3",
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter')
        )
        self.active_terminals_entry.pack(fill="x", padx=10, pady=5)

        _button(
            terminal_frame,
            self.convert_to_parking,
            text="Convert Others to Parking",
            height=32,
            fg_color=c('sage'),
            hover_color=c('sage', hover=True),
            text_color=c('sage_dark'),
            padx=(10, 10),
            pady=(5, 10)
        )

        gate_frame = ctk.CTkFrame(right_frame)
        gate_frame.pack(fill="x", padx=10, pady=10)

        _label(gate_frame, text="Move Gate(s)", size=16, pady=(10, 5))
        _label(
            gate_frame,
            text="Select gate(s) or terminal in tree, then specify destination:",
            size=12,
            pady=(0, 5),
            padx=(10, 0)
        )

        gate_row = ctk.CTkFrame(gate_frame, fg_color="transparent")
        gate_row.pack(fill="x", padx=10, pady=0)
        _label(gate_row, text="Selected:", size=16, padx=(0, 2), side="left")
        self.gate_entry = ctk.CTkEntry(
            gate_row,
            placeholder_text="Select from tree",
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=120
        )
        self.gate_entry.pack(side="left", padx=(0, 15))

        from_to_row = ctk.CTkFrame(gate_frame, fg_color="transparent")
        from_to_row.pack(fill="x", padx=10, pady=0)
        _label(from_to_row, text="From:", size=16, padx=(0, 2), side="left")
        self.from_terminal_entry = ctk.CTkEntry(
            from_to_row,
            placeholder_text="Auto",
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=50
        )
        self.from_terminal_entry.pack(side="left", padx=(0, 15))
        _label(from_to_row, text="To:", size=16, padx=(0, 2), side="left")
        self.to_terminal_entry = ctk.CTkEntry(
            from_to_row,
            placeholder_text="8",
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=50
        )
        self.to_terminal_entry.pack(side="left")

        _button(
            gate_frame,
            self.move_gate,
            text="Move Selected Gate(s)",
            height=32,
            fg_color=c('sage'),
            hover_color=c('sage', hover=True),
            text_color=c('sage_dark'),
            padx=(10, 10),
            pady=(5, 10)
        )

        rename_frame = ctk.CTkFrame(right_frame)
        rename_frame.pack(fill="x", padx=10, pady=10)

        _label(rename_frame, text="Rename Gate", size=16, pady=(10, 5))

        gate_terminal_row = ctk.CTkFrame(rename_frame, fg_color="transparent")
        gate_terminal_row.pack(fill="x", padx=10, pady=0)
        _label(gate_terminal_row, text="Gate:", size=16, padx=(0, 2), side="left")
        self.rename_gate_entry = ctk.CTkEntry(
            gate_terminal_row,
            placeholder_text="71",
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=50
        )
        self.rename_gate_entry.pack(side="left", padx=(0, 15))
        _label(gate_terminal_row, text="Terminal:", size=16, padx=(0, 2), side="left")
        self.rename_terminal_entry = ctk.CTkEntry(
            gate_terminal_row,
            placeholder_text="3",
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=50
        )
        self.rename_terminal_entry.pack(side="left")

        _label(rename_frame, text="New gate key:", size=16, pady=(5, 0), padx=(10, 0))
        self.new_gate_key_entry = ctk.CTkEntry(
            rename_frame,
            placeholder_text="B28A",
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter')
        )
        self.new_gate_key_entry.pack(fill="x", padx=10, pady=(0, 5))

        _button(
            rename_frame,
            self.rename_gate,
            text="Rename Gate",
            height=32,
            fg_color=c('sage'),
            hover_color=c('sage', hover=True),
            text_color=c('sage_dark'),
            padx=(10, 10),
            pady=(0, 10)
        )

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

    def reset_data(self):
        """Reset airport data by deleting interpreted file and re-parsing"""
        confirm = messagebox.askyesno(
            "Reset Airport Data",
            f"This will delete the interpreted data for {self.airport} and re-parse from raw data.\n\n"
            "Are you sure you want to continue?",
            icon='warning'
        )

        if not confirm:
            self.log_status("Reset cancelled")
            return

        try:
            interpreted_file = f".\\gsx_menu_logs\\{self.airport}_interpreted.json"

            if os.path.exists(interpreted_file):
                os.remove(interpreted_file)
                self.log_status(f"Deleted {interpreted_file}")

                for item in self.tree.get_children():
                    self.tree.delete(item)

                self.data = None

                if self.gate_assignment:
                    self.log_status("Re-parsing airport data...")
                    try:
                        self.gate_assignment.map_available_spots(self.airport)
                        self.log_status("Re-parsing complete")
                        self.load_data()
                    except Exception as e:
                        self.log_status(f"ERROR during re-parsing: {e}")
                        logging.error(f"Re-parsing error: {e}", exc_info=True)
                else:
                    self.log_status("Reset complete - please restart to re-parse")
                    messagebox.showinfo(
                        "Data Reset Complete",
                        f"Interpreted data for {self.airport} has been reset.\n\n"
                        "Please restart the application or re-run monitoring to re-parse the airport.",
                        icon='info'
                    )
            else:
                self.log_status("No interpreted file to delete - already reset")

        except Exception as e:
            self.log_status(f"ERROR during reset: {e}")
            logging.error(f"Reset error: {e}", exc_info=True)

    def refresh_tree(self):
        """Refresh tree view from current self.data (working copy)"""
        if not self.data:
            self.log_status("No data to display")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        terminals = self.data.get("terminals", {})
        for terminal_name, gates in terminals.items():
            terminal_node = self.tree.insert(
                "", "end",
                text=f"Terminal: {terminal_name}",
                values=('', '', terminal_name, ''),
                open=True
            )

            for gate_num, gate_info in gates.items():
                full_text = gate_info.get("raw_info", {}).get("full_text", "")
                size = self._parse_gate_size(full_text)
                jetways = self._parse_jetway_count(full_text)

                self.tree.insert(
                    terminal_node, "end",
                    text=f"Gate {gate_num}",
                    values=(size, jetways, terminal_name, full_text or "-")
                )

    def load_data(self):
        """Load JSON data from file into working copy"""
        if not os.path.exists(self.json_path):
            self.log_status(f"Airport data not found at {self.json_path}")
            self.log_status("Start monitoring to generate data or manually specify airport.")
            return

        try:
            with open(self.json_path, "r") as f:
                self.data = json.load(f)

            self.refresh_tree()
            self.log_status("Data loaded successfully")

        except Exception as e:
            self.log_status(f"Error loading data: {e}")

    def on_tree_select(self, event):
        """Auto-fill input fields when gates or terminals are selected"""
        selection = self.tree.selection()
        if not selection:
            return

        terminal_items = []
        gate_items = []

        for item in selection:
            item_text = self.tree.item(item, 'text')
            if item_text.startswith("Terminal: "):
                terminal_items.append(item)
            elif item_text.startswith("Gate "):
                gate_items.append(item)

        if terminal_items:
            terminal_item = terminal_items[0]
            children = self.tree.get_children(terminal_item)

            if children:
                for item in selection:
                    self.tree.selection_remove(item)

                for child in children:
                    self.tree.selection_add(child)

                terminal_name = self.tree.item(terminal_item, 'values')[2]
                self.log_status(f"Selected {len(children)} gates from Terminal {terminal_name}")
                return self.on_tree_select(event)

        if gate_items:
            if len(gate_items) == 1:
                item = gate_items[0]
                item_text = self.tree.item(item, 'text')
                values = self.tree.item(item, 'values')

                gate_num = item_text.replace("Gate ", "")
                terminal = values[2]
                full_text = values[3]

                self.gate_entry.delete(0, 'end')
                self.gate_entry.insert(0, gate_num)
                self.from_terminal_entry.delete(0, 'end')
                self.from_terminal_entry.insert(0, terminal)

                self.rename_gate_entry.delete(0, 'end')
                self.rename_gate_entry.insert(0, gate_num)
                self.rename_terminal_entry.delete(0, 'end')
                self.rename_terminal_entry.insert(0, terminal)
                self.new_gate_key_entry.delete(0, 'end')
                self.new_gate_key_entry.insert(0, gate_num)

                self.log_status(f"Selected: Gate {gate_num} in Terminal {terminal}")
            else:
                first_item = gate_items[0]
                values = self.tree.item(first_item, 'values')
                terminal = values[2]

                self.gate_entry.delete(0, 'end')
                self.gate_entry.insert(0, f"{len(gate_items)} gates")
                self.from_terminal_entry.delete(0, 'end')
                self.from_terminal_entry.insert(0, terminal)

                self.log_status(f"Selected {len(gate_items)} gates from Terminal {terminal}")

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

            active_terminals = [t.strip() for t in active_str.split(",")]
            self.log_status(f"Active terminals: {active_terminals}")

            terminals = self.data.get("terminals", {})
            converted_count = 0

            for terminal_name in list(terminals.keys()):
                if terminal_name not in active_terminals:
                    for gate_num, gate_info in list(terminals[terminal_name].items()):
                        gate_info["type"] = "parking"
                        converted_count += 1
                        gate_data = terminals[terminal_name].pop(gate_num)
                        gate_data["terminal"] = "Parking"

                        if "Parking" not in terminals:
                            terminals["Parking"] = {}

                        terminals["Parking"][gate_num] = gate_data
                    if len(terminals[terminal_name]) == 0:
                        terminals.pop(terminal_name)

            self.log_status(f"Converted {converted_count} gates to parking")
            self.has_unsaved_changes = True
            self.refresh_tree()

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")
            logging.error(f"Conversion error: {e}", exc_info=True)

    def move_gate(self):
        """Move selected gate(s) from one terminal to another"""
        try:
            logging.debug("Starting gate move...")

            if not self.data:
                self.log_status("ERROR: Please load data first")
                return

            to_terminal = self.to_terminal_entry.get().strip()
            if not to_terminal:
                self.log_status("ERROR: Please specify destination terminal")
                return

            # Get selected items from tree
            selection = self.tree.selection()
            if not selection:
                self.log_status("ERROR: Please select gate(s) to move")
                return

            terminals = self.data.get("terminals", {})

            # Create destination terminal if it doesn't exist
            if to_terminal not in terminals:
                terminals[to_terminal] = {}

            # Check for conflicts first
            conflicts = []
            gates_to_move = []

            for item in selection:
                item_text = self.tree.item(item, 'text')
                if not item_text.startswith("Gate "):
                    continue  # Skip terminal nodes

                values = self.tree.item(item, 'values')
                gate_num = item_text.replace("Gate ", "")
                from_terminal = values[2]

                # Skip same terminal moves
                if from_terminal == to_terminal:
                    continue

                # Check if gate already exists in destination
                if gate_num in terminals.get(to_terminal, {}):
                    conflicts.append(gate_num)

                gates_to_move.append((item, gate_num, from_terminal))

            # If conflicts exist, show dialog
            if conflicts:
                conflict_list = ", ".join(conflicts)
                proceed = messagebox.askyesno(
                    "Gate Conflicts Detected",
                    f"The following gate(s) already exist in Terminal {to_terminal}:\n\n"
                    f"{conflict_list}\n\n"
                    f"Moving will overwrite the existing gate(s).\n\n"
                    f"Do you want to continue?",
                    icon='warning'
                )

                if not proceed:
                    self.log_status("Move cancelled due to conflicts")
                    return

            moved_count = 0
            errors = []
            source_terminals = set()  # Track which terminals we moved gates from

            # Process each gate to move
            for item, gate_num, from_terminal in gates_to_move:
                # Check if source exists
                if from_terminal not in terminals:
                    errors.append(f"Terminal {from_terminal} not found")
                    continue

                if gate_num not in terminals[from_terminal]:
                    errors.append(f"Gate {gate_num} not found in Terminal {from_terminal}")
                    continue

                # Move the gate (will overwrite if conflict exists)
                gate_data = terminals[from_terminal].pop(gate_num)
                gate_data["terminal"] = to_terminal
                terminals[to_terminal][gate_num] = gate_data
                moved_count += 1
                source_terminals.add(from_terminal)

            # Clean up empty terminals
            for terminal in source_terminals:
                if terminal in terminals and len(terminals[terminal]) == 0:
                    terminals.pop(terminal)
                    self.log_status(f"Removed empty Terminal {terminal}")

            # Report results
            if moved_count > 0:
                self.log_status(
                    f"SUCCESS: Moved {moved_count} gate(s) to Terminal {to_terminal}"
                )
                self.has_unsaved_changes = True
                self.refresh_tree()  # Refresh tree view from working copy

            if errors:
                for error in errors:
                    self.log_status(f"ERROR: {error}")

            if moved_count == 0:
                self.log_status("ERROR: No gates were moved")

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

            old_gate_key = self.rename_gate_entry.get().strip()
            terminal = self.rename_terminal_entry.get().strip()
            new_gate_key = self.new_gate_key_entry.get().strip()

            if not all([old_gate_key, terminal, new_gate_key]):
                self.log_status("ERROR: Please fill all fields")
                return

            terminals = self.data.get("terminals", {})

            # Check if terminal exists
            if terminal not in terminals:
                self.log_status(f"ERROR: Terminal {terminal} not found")
                return

            # Check if gate exists in terminal
            if old_gate_key not in terminals[terminal]:
                self.log_status(
                    f"ERROR: Gate {old_gate_key} not found in Terminal {terminal}"
                )
                return

            # Check if new key already exists (and is different from old key)
            if new_gate_key != old_gate_key and new_gate_key in terminals[terminal]:
                proceed = messagebox.askyesno(
                    "Gate Already Exists",
                    f"Gate {new_gate_key} already exists in Terminal {terminal}.\n\n"
                    f"Renaming will overwrite the existing gate.\n\n"
                    f"Do you want to continue?",
                    icon='warning'
                )
                if not proceed:
                    self.log_status("Rename cancelled")
                    return

            # Rename the gate key
            gate_data = terminals[terminal].pop(old_gate_key)
            gate_data["gate"] = new_gate_key
            gate_data["position_id"] = f"Terminal {terminal} Gate {new_gate_key}"
            terminals[terminal][new_gate_key] = gate_data

            self.log_status(
                f"SUCCESS: Renamed Gate {old_gate_key} to {new_gate_key} in Terminal {terminal}"
            )
            self.has_unsaved_changes = True
            self.refresh_tree()  # Refresh tree view from working copy

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")
            logging.error(f"Rename gate error: {e}", exc_info=True)

    def _alphanumeric_key(self, s):
        """Natural sorting key: splits 'A10' into ['A', 10] for proper comparison"""
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split('([0-9]+)', s)]

    def save_data(self):
        """Save modified data back to JSON with alphanumeric sorting"""
        if not self.data:
            self.log_status("No data to save")
            return

        try:
            # Sort gates alphanumerically under each terminal
            sorted_data = {"terminals": {}}
            terminals = self.data.get("terminals", {})

            for terminal_name, gates in terminals.items():
                # Sort gates by their gate number/name
                sorted_gates = dict(sorted(gates.items(), key=lambda x: self._alphanumeric_key(x[0])))
                sorted_data["terminals"][terminal_name] = sorted_gates

            with open(self.json_path, "w") as f:
                json.dump(sorted_data, f, indent=2)

            # Update working copy with sorted data and refresh tree
            self.data = sorted_data
            self.has_unsaved_changes = False
            self.refresh_tree()

            self.log_status("Changes saved successfully (gates sorted alphanumerically)")
            logging.info("Gate configuration saved with alphanumeric sorting")

        except Exception as e:
            self.log_status(f"Error saving: {e}")

    def on_closing(self):
        """Handle window close event with unsaved changes check"""
        if self.has_unsaved_changes:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                icon='warning'
            )

            if response is True:  # Yes - save and close
                self.save_data()
                self.window.destroy()
            elif response is False:  # No - close without saving
                self.window.destroy()
            # None/Cancel - do nothing, keep window open
        else:
            self.window.destroy()

    def log_status(self, message):
        """Add message to status log"""
        self.status_text.insert("end", f"{message}\n")
        self.status_text.see("end")
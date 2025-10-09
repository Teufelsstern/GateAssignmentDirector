"""Gate Management Window for editing airport gate configurations"""

# Licensed under AGPL-3.0-or-later with additional terms
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
            text="Sort & Save",
            height=28,
            fg_color=c('sage'),
            hover_color=c('sage', hover=True),
            text_color=c('sage_dark'),
            pady=(0, 0),
        )

        right_frame = ctk.CTkFrame(main_frame, width=350)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)

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
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=50
        )
        self.from_terminal_entry.pack(side="left", padx=(0, 15))
        _label(from_to_row, text="To:", size=16, padx=(0, 2), side="left")
        self.to_terminal_entry = ctk.CTkEntry(
            from_to_row,
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

        _label(rename_frame, text="Rename", size=16, pady=(10, 5))

        # Radio button toggle for Gate vs Terminal mode
        self.rename_mode = ctk.StringVar(value="gate")
        radio_frame = ctk.CTkFrame(rename_frame, fg_color="transparent")
        radio_frame.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkRadioButton(
            radio_frame,
            text="Gate",
            variable=self.rename_mode,
            value="gate",
            command=self._on_rename_mode_change,
            font=("Arial", 14)
        ).pack(side="left", padx=(0, 15))

        ctk.CTkRadioButton(
            radio_frame,
            text="Terminal",
            variable=self.rename_mode,
            value="terminal",
            command=self._on_rename_mode_change,
            font=("Arial", 14)
        ).pack(side="left")

        # Gate rename fields
        self.gate_rename_row = ctk.CTkFrame(rename_frame, fg_color="transparent")
        self.gate_rename_row.pack(fill="x", padx=10, pady=0)
        self.gate_label = _label(self.gate_rename_row, text="Gate:", size=16, padx=(0, 2), side="left")
        self.rename_gate_entry = ctk.CTkEntry(
            self.gate_rename_row,
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=50
        )
        self.rename_gate_entry.pack(side="left", padx=(0, 15))
        self.terminal_label = _label(self.gate_rename_row, text="Terminal:", size=16, padx=(0, 2), side="left")
        self.rename_terminal_entry = ctk.CTkEntry(
            self.gate_rename_row,
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=50
        )
        self.rename_terminal_entry.pack(side="left")

        # Terminal rename fields
        self.terminal_rename_row = ctk.CTkFrame(rename_frame, fg_color="transparent")
        self.current_terminal_label = _label(self.terminal_rename_row, text="Current:", size=16, padx=(0, 2), side="left")
        self.rename_current_terminal_entry = ctk.CTkEntry(
            self.terminal_rename_row,
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=80
        )
        self.rename_current_terminal_entry.pack(side="left", padx=(0, 15))
        self.new_terminal_label = _label(self.terminal_rename_row, text="New:", size=16, padx=(0, 2), side="left")
        self.rename_new_terminal_entry = ctk.CTkEntry(
            self.terminal_rename_row,
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=80
        )
        self.rename_new_terminal_entry.pack(side="left")

        # New gate key field (only for gate mode)
        self.new_key_label_widget = _label(rename_frame, text="New gate key:", size=16, pady=(5, 0), padx=(10, 0))
        self.new_gate_key_entry = ctk.CTkEntry(
            rename_frame,
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter')
        )
        self.new_gate_key_entry.pack(fill="x", padx=10, pady=(0, 5))

        self.rename_button = _button(
            rename_frame,
            self._on_rename_click,
            text="Rename Gate",
            height=32,
            fg_color=c('sage'),
            hover_color=c('sage', hover=True),
            text_color=c('sage_dark'),
            padx=(10, 10),
            pady=(0, 10)
        )

        # Initialize UI to gate mode
        self._on_rename_mode_change()

        # Prefix/Suffix section
        prefix_suffix_frame = ctk.CTkFrame(right_frame)
        prefix_suffix_frame.pack(fill="x", padx=10, pady=10)

        _label(prefix_suffix_frame, text="Add Prefix/Suffix to Gate(s)", size=16, pady=(10, 5))
        _label(
            prefix_suffix_frame,
            text="Select gate(s) or terminal in tree",
            size=12,
            pady=(0, 5),
            padx=(10, 0)
        )

        prefix_suffix_row = ctk.CTkFrame(prefix_suffix_frame, fg_color="transparent")
        prefix_suffix_row.pack(fill="x", padx=10, pady=0)
        _label(prefix_suffix_row, text="Prefix:", size=16, padx=(0, 2), side="left")
        self.prefix_entry = ctk.CTkEntry(
            prefix_suffix_row,
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=80
        )
        self.prefix_entry.pack(side="left", padx=(0, 15))
        _label(prefix_suffix_row, text="Suffix:", size=16, padx=(0, 2), side="left")
        self.suffix_entry = ctk.CTkEntry(
            prefix_suffix_row,
            corner_radius=6,
            border_width=1,
            border_color=c('charcoal_lighter'),
            width=80
        )
        self.suffix_entry.pack(side="left")

        _button(
            prefix_suffix_frame,
            self.add_prefix_suffix,
            text="Apply to Selected Gate(s)",
            height=32,
            fg_color=c('sage'),
            hover_color=c('sage', hover=True),
            text_color=c('sage_dark'),
            padx=(10, 10),
            pady=(5, 10)
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

                # Also fill terminal rename field
                self.rename_current_terminal_entry.delete(0, 'end')
                self.rename_current_terminal_entry.insert(0, terminal_name)

                self.log_status(f"Selected {len(children)} gates from Terminal {terminal_name}")

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

    def _on_rename_mode_change(self):
        """Toggle UI fields based on rename mode (gate vs terminal)"""
        mode = self.rename_mode.get()

        if mode == "gate":
            # Show gate fields
            self.gate_rename_row.pack(fill="x", padx=10, pady=0)
            self.new_key_label_widget.pack(fill="x", padx=(10, 0), pady=(5, 0))
            self.new_gate_key_entry.pack(fill="x", padx=10, pady=(0, 5))

            # Hide terminal fields
            self.terminal_rename_row.pack_forget()

            # Update button text
            self.rename_button.configure(text="Rename Gate")

        else:  # terminal mode
            # Hide gate fields
            self.gate_rename_row.pack_forget()
            self.new_key_label_widget.pack_forget()
            self.new_gate_key_entry.pack_forget()

            # Show terminal fields
            self.terminal_rename_row.pack(fill="x", padx=10, pady=0)

            # Update button text
            self.rename_button.configure(text="Rename Terminal")

    def _on_rename_click(self):
        """Call appropriate rename method based on mode"""
        mode = self.rename_mode.get()
        if mode == "gate":
            self.rename_gate()
        else:
            self.rename_terminal()

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

    def rename_terminal(self):
        """Rename a terminal and update all gates within it"""
        try:
            logging.debug("Starting terminal rename...")

            if not self.data:
                self.log_status("ERROR: Please load data first")
                return

            old_terminal = self.rename_current_terminal_entry.get().strip()
            new_terminal = self.rename_new_terminal_entry.get().strip()

            if not all([old_terminal, new_terminal]):
                self.log_status("ERROR: Please fill all fields")
                return

            if old_terminal == new_terminal:
                self.log_status("ERROR: Old and new terminal names are the same")
                return

            terminals = self.data.get("terminals", {})

            # Check if old terminal exists
            if old_terminal not in terminals:
                self.log_status(f"ERROR: Terminal {old_terminal} not found")
                return

            # Check if new terminal already exists
            if new_terminal in terminals:
                proceed = messagebox.askyesno(
                    "Terminal Already Exists",
                    f"Terminal {new_terminal} already exists.\n\n"
                    f"Renaming will merge Terminal {old_terminal} into Terminal {new_terminal}.\n"
                    f"Gates with the same number will be overwritten.\n\n"
                    f"Do you want to continue?",
                    icon='warning'
                )
                if not proceed:
                    self.log_status("Rename cancelled")
                    return

                # Merge terminals
                old_gates = terminals[old_terminal]
                for gate_num, gate_data in old_gates.items():
                    gate_data["terminal"] = new_terminal
                    gate_data["position_id"] = f"Terminal {new_terminal} Gate {gate_num}"
                    terminals[new_terminal][gate_num] = gate_data

                # Remove old terminal
                terminals.pop(old_terminal)
                self.log_status(
                    f"SUCCESS: Merged Terminal {old_terminal} into Terminal {new_terminal}"
                )

            else:
                # Simple rename - move all gates to new terminal key
                terminals[new_terminal] = {}
                for gate_num, gate_data in terminals[old_terminal].items():
                    gate_data["terminal"] = new_terminal
                    gate_data["position_id"] = f"Terminal {new_terminal} Gate {gate_num}"
                    terminals[new_terminal][gate_num] = gate_data

                # Remove old terminal
                terminals.pop(old_terminal)
                self.log_status(
                    f"SUCCESS: Renamed Terminal {old_terminal} to {new_terminal}"
                )

            self.has_unsaved_changes = True
            self.refresh_tree()

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")
            logging.error(f"Rename terminal error: {e}", exc_info=True)

    def add_prefix_suffix(self):
        """Add prefix and/or suffix to selected gate(s)"""
        try:
            logging.debug("Starting prefix/suffix addition...")

            if not self.data:
                self.log_status("ERROR: Please load data first")
                return

            prefix = self.prefix_entry.get()  # Allow empty string
            suffix = self.suffix_entry.get()  # Allow empty string

            if not prefix and not suffix:
                self.log_status("ERROR: Please specify at least a prefix or suffix")
                return

            # Get selected items from tree
            selection = self.tree.selection()
            if not selection:
                self.log_status("ERROR: Please select gate(s) to modify")
                return

            terminals = self.data.get("terminals", {})

            # Collect gates to modify
            gates_to_modify = []
            gates_with_existing = []

            for item in selection:
                item_text = self.tree.item(item, 'text')
                if not item_text.startswith("Gate "):
                    continue  # Skip terminal nodes

                values = self.tree.item(item, 'values')
                gate_num = item_text.replace("Gate ", "")
                terminal = values[2]

                new_gate_key = f"{prefix}{gate_num}{suffix}"

                # Check if this gate already appears to have a prefix/suffix
                # (Simple heuristic: if adding prefix/suffix makes it longer or changes letters)
                has_existing = (prefix and gate_num.startswith(prefix)) or (suffix and gate_num.endswith(suffix))

                gates_to_modify.append((item, gate_num, terminal, new_gate_key))
                if has_existing:
                    gates_with_existing.append(gate_num)

            # If gates with existing prefix/suffix found, ask user
            mode = "skip"  # default
            if gates_with_existing:
                # Custom dialog with 3 buttons
                from tkinter import messagebox
                response = messagebox.askquestion(
                    "Gates with Existing Prefix/Suffix",
                    f"Some gates may already have prefix/suffix:\n\n"
                    f"{', '.join(gates_with_existing)}\n\n"
                    f"Click 'Yes' to apply to all (including those with existing)\n"
                    f"Click 'No' to skip those gates and only apply to others\n"
                    f"(Click Cancel in the next dialog to cancel entirely)",
                    icon='warning',
                    type='yesno'
                )

                if response == 'yes':
                    mode = "apply_all"
                else:
                    mode = "skip"

            # Apply prefix/suffix
            modified_count = 0
            skipped_count = 0
            conflicts = []

            for item, gate_num, terminal, new_gate_key in gates_to_modify:
                # Skip if gate has existing prefix/suffix and mode is skip
                has_existing = (prefix and gate_num.startswith(prefix)) or (suffix and gate_num.endswith(suffix))
                if mode == "skip" and has_existing:
                    skipped_count += 1
                    continue

                # Check if terminal exists
                if terminal not in terminals:
                    self.log_status(f"ERROR: Terminal {terminal} not found")
                    continue

                # Check if gate exists
                if gate_num not in terminals[terminal]:
                    self.log_status(f"ERROR: Gate {gate_num} not found in Terminal {terminal}")
                    continue

                # Check if new key already exists
                if new_gate_key != gate_num and new_gate_key in terminals[terminal]:
                    conflicts.append((terminal, gate_num, new_gate_key))
                    continue

                # Apply prefix/suffix
                gate_data = terminals[terminal].pop(gate_num)
                gate_data["gate"] = new_gate_key
                gate_data["position_id"] = f"Terminal {terminal} Gate {new_gate_key}"
                terminals[terminal][new_gate_key] = gate_data
                modified_count += 1

            # Report results
            if modified_count > 0:
                self.log_status(
                    f"SUCCESS: Modified {modified_count} gate(s) with prefix='{prefix}' suffix='{suffix}'"
                )
                self.has_unsaved_changes = True
                self.refresh_tree()

            if skipped_count > 0:
                self.log_status(f"Skipped {skipped_count} gate(s) with existing prefix/suffix")

            if conflicts:
                conflict_msg = ", ".join([f"{t}:{old}→{new}" for t, old, new in conflicts])
                self.log_status(f"Conflicts (gates already exist): {conflict_msg}")

            if modified_count == 0:
                self.log_status("No gates were modified")

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")
            logging.error(f"Add prefix/suffix error: {e}", exc_info=True)

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
            # Sort terminals and gates alphanumerically
            sorted_data = {"terminals": {}}
            terminals = self.data.get("terminals", {})

            # Sort terminals first
            sorted_terminals = sorted(terminals.items(), key=lambda x: self._alphanumeric_key(x[0]))

            for terminal_name, gates in sorted_terminals:
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
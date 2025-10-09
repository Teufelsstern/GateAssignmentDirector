import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

sys.modules['customtkinter'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['PIL'] = MagicMock()


class MockGateManagementWindow:
    """Mock class that replicates logic from GateManagementWindow for testing"""

    def __init__(self):
        self.data = None
        self.tree = Mock()
        self.to_terminal_entry = Mock()
        self.log_status = Mock()
        self.has_unsaved_changes = False
        self.refresh_tree = Mock()

    def rename_gate(self):
        """Rename a gate's key"""
        try:
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

            if terminal not in terminals:
                self.log_status(f"ERROR: Terminal {terminal} not found")
                return

            if old_gate_key not in terminals[terminal]:
                self.log_status(f"ERROR: Gate {old_gate_key} not found in Terminal {terminal}")
                return

            if new_gate_key != old_gate_key and new_gate_key in terminals[terminal]:
                from tkinter import messagebox
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

            gate_data = terminals[terminal].pop(old_gate_key)
            gate_data["gate"] = new_gate_key
            gate_data["position_id"] = f"Terminal {terminal} Gate {new_gate_key}"
            terminals[terminal][new_gate_key] = gate_data

            self.log_status(f"SUCCESS: Renamed Gate {old_gate_key} to {new_gate_key} in Terminal {terminal}")
            self.has_unsaved_changes = True
            self.refresh_tree()

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")

    def rename_terminal(self):
        """Rename a terminal and update all gates within it"""
        try:
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

            if old_terminal not in terminals:
                self.log_status(f"ERROR: Terminal {old_terminal} not found")
                return

            if new_terminal in terminals:
                from tkinter import messagebox
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

                old_gates = terminals[old_terminal]
                for gate_num, gate_data in old_gates.items():
                    gate_data["terminal"] = new_terminal
                    gate_data["position_id"] = f"Terminal {new_terminal} Gate {gate_num}"
                    terminals[new_terminal][gate_num] = gate_data

                terminals.pop(old_terminal)
                self.log_status(f"SUCCESS: Merged Terminal {old_terminal} into Terminal {new_terminal}")

            else:
                terminals[new_terminal] = {}
                for gate_num, gate_data in terminals[old_terminal].items():
                    gate_data["terminal"] = new_terminal
                    gate_data["position_id"] = f"Terminal {new_terminal} Gate {gate_num}"
                    terminals[new_terminal][gate_num] = gate_data

                terminals.pop(old_terminal)
                self.log_status(f"SUCCESS: Renamed Terminal {old_terminal} to {new_terminal}")

            self.has_unsaved_changes = True
            self.refresh_tree()

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")

    def add_prefix_suffix(self):
        """Add prefix and/or suffix to selected gate(s)"""
        try:
            if not self.data:
                self.log_status("ERROR: Please load data first")
                return

            prefix = self.prefix_entry.get()
            suffix = self.suffix_entry.get()

            if not prefix and not suffix:
                self.log_status("ERROR: Please specify at least a prefix or suffix")
                return

            selection = self.tree.selection()
            if not selection:
                self.log_status("ERROR: Please select gate(s) to modify")
                return

            terminals = self.data.get("terminals", {})

            gates_to_modify = []
            gates_with_existing = []

            for item in selection:
                item_text = self.tree.item(item, 'text')
                if not item_text.startswith("Gate "):
                    continue

                values = self.tree.item(item, 'values')
                gate_num = item_text.replace("Gate ", "")
                terminal = values[2]

                new_gate_key = f"{prefix}{gate_num}{suffix}"

                has_existing = (prefix and gate_num.startswith(prefix)) or (suffix and gate_num.endswith(suffix))

                gates_to_modify.append((item, gate_num, terminal, new_gate_key))
                if has_existing:
                    gates_with_existing.append(gate_num)

            mode = "skip"
            if gates_with_existing:
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

            modified_count = 0
            skipped_count = 0
            conflicts = []

            for item, gate_num, terminal, new_gate_key in gates_to_modify:
                has_existing = (prefix and gate_num.startswith(prefix)) or (suffix and gate_num.endswith(suffix))
                if mode == "skip" and has_existing:
                    skipped_count += 1
                    continue

                if terminal not in terminals:
                    self.log_status(f"ERROR: Terminal {terminal} not found")
                    continue

                if gate_num not in terminals[terminal]:
                    self.log_status(f"ERROR: Gate {gate_num} not found in Terminal {terminal}")
                    continue

                if new_gate_key != gate_num and new_gate_key in terminals[terminal]:
                    conflicts.append((terminal, gate_num, new_gate_key))
                    continue

                gate_data = terminals[terminal].pop(gate_num)
                gate_data["gate"] = new_gate_key
                gate_data["position_id"] = f"Terminal {terminal} Gate {new_gate_key}"
                terminals[terminal][new_gate_key] = gate_data
                modified_count += 1

            if modified_count > 0:
                self.log_status(f"SUCCESS: Modified {modified_count} gate(s) with prefix='{prefix}' suffix='{suffix}'")
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

    def move_gate(self):
        """Move selected gate(s) from one terminal to another"""
        try:
            if not self.data:
                self.log_status("ERROR: Please load data first")
                return

            to_terminal = self.to_terminal_entry.get().strip()
            if not to_terminal:
                self.log_status("ERROR: Please specify destination terminal")
                return

            selection = self.tree.selection()
            if not selection:
                self.log_status("ERROR: Please select gate(s) to move")
                return

            terminals = self.data.get("terminals", {})

            if to_terminal not in terminals:
                terminals[to_terminal] = {}

            conflicts = []
            gates_to_move = []

            for item in selection:
                item_text = self.tree.item(item, 'text')
                if not item_text.startswith("Gate "):
                    continue

                values = self.tree.item(item, 'values')
                gate_num = item_text.replace("Gate ", "")
                from_terminal = values[2]

                if from_terminal == to_terminal:
                    continue

                if gate_num in terminals.get(to_terminal, {}):
                    conflicts.append(gate_num)

                gates_to_move.append((item, gate_num, from_terminal))

            if conflicts:
                conflict_list = ", ".join(conflicts)
                from tkinter import messagebox
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
            source_terminals = set()

            for item, gate_num, from_terminal in gates_to_move:
                if from_terminal not in terminals:
                    errors.append(f"Terminal {from_terminal} not found")
                    continue

                if gate_num not in terminals[from_terminal]:
                    errors.append(f"Gate {gate_num} not found in Terminal {from_terminal}")
                    continue

                gate_data = terminals[from_terminal].pop(gate_num)
                gate_data["terminal"] = to_terminal
                terminals[to_terminal][gate_num] = gate_data
                moved_count += 1
                source_terminals.add(from_terminal)

            for terminal in source_terminals:
                if terminal in terminals and len(terminals[terminal]) == 0:
                    terminals.pop(terminal)
                    self.log_status(f"Removed empty Terminal {terminal}")

            if moved_count > 0:
                self.log_status(
                    f"SUCCESS: Moved {moved_count} gate(s) to Terminal {to_terminal}"
                )
                self.has_unsaved_changes = True
                self.refresh_tree()

            if errors:
                for error in errors:
                    self.log_status(f"ERROR: {error}")

            if moved_count == 0:
                self.log_status("ERROR: No gates were moved")

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")


class TestMultiSelectMove(unittest.TestCase):
    """Unit tests for move_gate() with multi-select and conflict detection"""

    def setUp(self) -> None:
        """Set up test fixtures for each test"""
        self.gate_mgmt = MockGateManagementWindow()

        self.gate_mgmt.data = {
            "terminals": {
                "1": {
                    "10": {
                        "raw_info": {"full_text": "Gate 10 - Small - 1x  /J"},
                        "terminal": "1"
                    },
                    "11": {
                        "raw_info": {"full_text": "Gate 11 - Medium - 2x  /J"},
                        "terminal": "1"
                    }
                },
                "2": {
                    "20": {
                        "raw_info": {"full_text": "Gate 20 - Heavy - None"},
                        "terminal": "2"
                    },
                    "21": {
                        "raw_info": {"full_text": "Gate 21 - Medium - 1x  /J"},
                        "terminal": "2"
                    }
                }
            }
        }

        self.gate_mgmt.tree.selection.return_value = []
        self.gate_mgmt.tree.item = Mock()

    def _setup_tree_item_mock(self, items_data: list):
        """
        Helper to set up tree.item() mock for multiple items.
        items_data: list of (item_id, gate_text, values_tuple)
        """
        item_map = {}
        for item_id, gate_text, values in items_data:
            item_map[item_id] = {'text': gate_text, 'values': values}

        def tree_item_side_effect(item, key=None):
            if item not in item_map:
                raise ValueError(f"Item {item} not in mock data")
            if key == 'text':
                return item_map[item]['text']
            elif key == 'values':
                return item_map[item]['values']
            else:
                return item_map[item]

        self.gate_mgmt.tree.item.side_effect = tree_item_side_effect

    def test_move_single_gate_success(self) -> None:
        """Happy path - successfully move a single gate to another terminal"""
        self.gate_mgmt.to_terminal_entry.get.return_value = "3"
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J'))
        ])

        self.gate_mgmt.move_gate()

        self.assertIn("10", self.gate_mgmt.data["terminals"]["3"])
        self.assertNotIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["3"]["10"]["terminal"], "3")
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_called_once()
        self.gate_mgmt.log_status.assert_any_call("SUCCESS: Moved 1 gate(s) to Terminal 3")

    def test_move_multiple_gates_success(self) -> None:
        """Successfully move multiple gates from the same terminal"""
        self.gate_mgmt.to_terminal_entry.get.return_value = "3"
        self.gate_mgmt.tree.selection.return_value = ['item1', 'item2']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J')),
            ('item2', 'Gate 11', ('Medium', '2x  /J', '1', 'Gate 11 - Medium - 2x  /J'))
        ])

        self.gate_mgmt.move_gate()

        self.assertIn("10", self.gate_mgmt.data["terminals"]["3"])
        self.assertIn("11", self.gate_mgmt.data["terminals"]["3"])
        self.assertNotIn("1", self.gate_mgmt.data["terminals"])
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.log_status.assert_any_call("SUCCESS: Moved 2 gate(s) to Terminal 3")

    def test_move_with_conflict_user_proceeds(self) -> None:
        """Gate already exists in destination, user chooses to proceed and overwrite"""
        self.gate_mgmt.data["terminals"]["3"] = {
            "10": {
                "raw_info": {"full_text": "Gate 10 - OLD DATA - None"},
                "terminal": "3"
            }
        }

        self.gate_mgmt.to_terminal_entry.get.return_value = "3"
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J'))
        ])

        with patch('tkinter.messagebox.askyesno', return_value=True):
            self.gate_mgmt.move_gate()

        self.assertEqual(
            self.gate_mgmt.data["terminals"]["3"]["10"]["raw_info"]["full_text"],
            "Gate 10 - Small - 1x  /J"
        )
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.log_status.assert_any_call("SUCCESS: Moved 1 gate(s) to Terminal 3")

    def test_move_with_conflict_user_cancels(self) -> None:
        """Gate already exists in destination, user chooses to cancel"""
        self.gate_mgmt.data["terminals"]["3"] = {
            "10": {
                "raw_info": {"full_text": "Gate 10 - OLD DATA - None"},
                "terminal": "3"
            }
        }

        self.gate_mgmt.to_terminal_entry.get.return_value = "3"
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J'))
        ])

        with patch('tkinter.messagebox.askyesno', return_value=False):
            self.gate_mgmt.move_gate()

        self.assertEqual(
            self.gate_mgmt.data["terminals"]["3"]["10"]["raw_info"]["full_text"],
            "Gate 10 - OLD DATA - None"
        )
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_not_called()
        self.gate_mgmt.log_status.assert_called_with("Move cancelled due to conflicts")

    def test_move_to_same_terminal_skipped(self) -> None:
        """Moving a gate to its current terminal should be skipped"""
        self.gate_mgmt.to_terminal_entry.get.return_value = "1"
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J'))
        ])

        self.gate_mgmt.move_gate()

        self.assertFalse(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_not_called()
        self.gate_mgmt.log_status.assert_called_with("ERROR: No gates were moved")

    def test_move_no_data_loaded(self) -> None:
        """Should error when no data is loaded"""
        self.gate_mgmt.data = None
        self.gate_mgmt.to_terminal_entry.get.return_value = "3"

        self.gate_mgmt.move_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please load data first")
        self.gate_mgmt.refresh_tree.assert_not_called()

    def test_move_no_destination_specified(self) -> None:
        """Should error when destination terminal is not specified"""
        self.gate_mgmt.to_terminal_entry.get.return_value = ""
        self.gate_mgmt.tree.selection.return_value = ['item1']

        self.gate_mgmt.move_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please specify destination terminal")
        self.gate_mgmt.refresh_tree.assert_not_called()

    def test_move_no_selection(self) -> None:
        """Should error when no gates are selected"""
        self.gate_mgmt.to_terminal_entry.get.return_value = "3"
        self.gate_mgmt.tree.selection.return_value = []

        self.gate_mgmt.move_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please select gate(s) to move")
        self.gate_mgmt.refresh_tree.assert_not_called()

    def test_move_creates_destination_terminal(self) -> None:
        """Should create destination terminal if it doesn't exist"""
        self.gate_mgmt.to_terminal_entry.get.return_value = "99"
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J'))
        ])

        self.gate_mgmt.move_gate()

        self.assertIn("99", self.gate_mgmt.data["terminals"])
        self.assertIn("10", self.gate_mgmt.data["terminals"]["99"])
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)

    def test_move_removes_empty_source_terminal(self) -> None:
        """Should remove source terminal if it becomes empty after move"""
        self.gate_mgmt.to_terminal_entry.get.return_value = "3"
        self.gate_mgmt.tree.selection.return_value = ['item1', 'item2']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J')),
            ('item2', 'Gate 11', ('Medium', '2x  /J', '1', 'Gate 11 - Medium - 2x  /J'))
        ])

        self.gate_mgmt.move_gate()

        self.assertNotIn("1", self.gate_mgmt.data["terminals"])
        self.gate_mgmt.log_status.assert_any_call("Removed empty Terminal 1")


class TestWorkingCopyPattern(unittest.TestCase):
    """Test the working copy pattern: load_data(), save_data(), refresh_tree()"""

    def setUp(self) -> None:
        self.mock_parent = Mock()
        self.sample_data = {
            "terminals": {
                "1": {
                    "10": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 10 - Small"}},
                    "2": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 2 - Medium"}}
                }
            }
        }

    def test_load_creates_working_copy(self) -> None:
        """Should load JSON into self.data (working copy)"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open(read_data='{"terminals": {}}')), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()) as mock_json_load:

            window = GateManagementWindow(self.mock_parent, airport="EDDS")

            self.assertIsNotNone(window.data)
            self.assertEqual(window.data, self.sample_data)
            mock_json_load.assert_called_once()

    def test_modifications_dont_affect_json_until_save(self) -> None:
        """Should allow modifications to self.data without touching JSON file until save_data()"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()), \
             patch('GateAssignmentDirector.ui.gate_management.json.dump') as mock_dump:

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.data["terminals"]["1"]["99"] = {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 99"}}

            mock_dump.assert_not_called()

    def test_refresh_tree_uses_working_copy(self) -> None:
        """Should use self.data for refresh_tree(), not re-read from JSON"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()) as mock_file, \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()) as mock_json_load:

            window = GateManagementWindow(self.mock_parent, airport="EDDS")

            initial_load_count = mock_json_load.call_count
            initial_file_open_count = mock_file.call_count
            window.data["terminals"]["1"]["99"] = {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 99"}}

            window.refresh_tree()

            self.assertEqual(mock_json_load.call_count, initial_load_count, "refresh_tree should not call json.load")
            self.assertEqual(mock_file.call_count, initial_file_open_count, "refresh_tree should not open file")

    def test_save_writes_working_copy_to_json(self) -> None:
        """Should write self.data to JSON file when save_data() is called"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()), \
             patch('GateAssignmentDirector.ui.gate_management.json.dump') as mock_dump:

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.data["terminals"]["1"]["99"] = {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 99"}}
            window.save_data()

            mock_dump.assert_called_once()
            saved_data = mock_dump.call_args[0][0]
            self.assertIn("99", saved_data["terminals"]["1"])

    def test_save_sorts_gates_alphanumerically(self) -> None:
        """Should sort gates naturally: '2' before '10', not alphabetically"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        unsorted_data = {
            "terminals": {
                "1": {
                    "10": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 10"}},
                    "2": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 2"}},
                    "20": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 20"}}
                }
            }
        }

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=unsorted_data), \
             patch('GateAssignmentDirector.ui.gate_management.json.dump') as mock_dump:

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.save_data()

            saved_data = mock_dump.call_args[0][0]
            gate_keys = list(saved_data["terminals"]["1"].keys())
            self.assertEqual(gate_keys, ["2", "10", "20"])

    def test_save_clears_unsaved_flag(self) -> None:
        """Should set has_unsaved_changes to False after save_data()"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()), \
             patch('GateAssignmentDirector.ui.gate_management.json.dump'):

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.has_unsaved_changes = True
            window.save_data()

            self.assertFalse(window.has_unsaved_changes)

    def test_save_refreshes_tree(self) -> None:
        """Should call refresh_tree() after saving"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()), \
             patch('GateAssignmentDirector.ui.gate_management.json.dump'):

            window = GateManagementWindow(self.mock_parent, airport="EDDS")

            with patch.object(window, 'refresh_tree', wraps=window.refresh_tree) as mock_refresh:
                window.save_data()
                mock_refresh.assert_called_once()

    def test_save_updates_working_copy_with_sorted_data(self) -> None:
        """Should update self.data with sorted version after save"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        unsorted_data = {
            "terminals": {
                "1": {
                    "10": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 10"}},
                    "2": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 2"}}
                }
            }
        }

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=unsorted_data), \
             patch('GateAssignmentDirector.ui.gate_management.json.dump'):

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.save_data()

            gate_keys_in_memory = list(window.data["terminals"]["1"].keys())
            self.assertEqual(gate_keys_in_memory, ["2", "10"])


class TestUnsavedChanges(unittest.TestCase):
    """Test on_closing() method and has_unsaved_changes flag tracking"""

    def setUp(self) -> None:
        self.mock_parent = Mock()
        self.sample_data = {
            "terminals": {
                "1": {
                    "10": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 10 - Small"}}
                }
            }
        }

    def test_closes_immediately_when_no_changes(self) -> None:
        """Should destroy window without prompting when has_unsaved_changes=False"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()), \
             patch('tkinter.messagebox.askyesnocancel') as mock_dialog:

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.has_unsaved_changes = False

            with patch.object(window.window, 'destroy') as mock_destroy:
                window.on_closing()

                mock_dialog.assert_not_called()
                mock_destroy.assert_called_once()

    def test_saves_and_closes_when_user_confirms(self) -> None:
        """Should call save_data() and destroy() when user clicks Yes"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()), \
             patch('tkinter.messagebox.askyesnocancel', return_value=True):

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.has_unsaved_changes = True

            with patch.object(window, 'save_data') as mock_save, \
                 patch.object(window.window, 'destroy') as mock_destroy:
                window.on_closing()

                mock_save.assert_called_once()
                mock_destroy.assert_called_once()

    def test_closes_without_save_when_user_declines(self) -> None:
        """Should destroy() without save_data() when user clicks No"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()), \
             patch('tkinter.messagebox.askyesnocancel', return_value=False):

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.has_unsaved_changes = True

            with patch.object(window, 'save_data') as mock_save, \
                 patch.object(window.window, 'destroy') as mock_destroy:
                window.on_closing()

                mock_save.assert_not_called()
                mock_destroy.assert_called_once()

    def test_stays_open_when_user_cancels(self) -> None:
        """Should not destroy() when user clicks Cancel (returns None)"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=self.sample_data.copy()), \
             patch('tkinter.messagebox.askyesnocancel', return_value=None):

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.has_unsaved_changes = True

            with patch.object(window, 'save_data') as mock_save, \
                 patch.object(window.window, 'destroy') as mock_destroy:
                window.on_closing()

                mock_save.assert_not_called()
                mock_destroy.assert_not_called()

    def test_move_gate_sets_unsaved_flag(self) -> None:
        """Should set has_unsaved_changes=True after successful move_gate()"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        data = {
            "terminals": {
                "1": {
                    "10": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 10 - Small"}}
                }
            }
        }

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=data):

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.has_unsaved_changes = False

            window.to_terminal_entry.get = Mock(return_value="2")
            window.tree.selection = Mock(return_value=['item1'])
            window.tree.item = Mock(side_effect=lambda item, key:
                'Gate 10' if key == 'text' else ('Small', '1x', '1', 'Gate 10 - Small'))

            window.move_gate()

            self.assertTrue(window.has_unsaved_changes)


class TestRenameGate(unittest.TestCase):
    """Unit tests for rename_gate() method"""

    def setUp(self) -> None:
        self.gate_mgmt = MockGateManagementWindow()
        self.gate_mgmt.data = {
            "terminals": {
                "1": {
                    "10": {
                        "gate": "10",
                        "terminal": "1",
                        "position_id": "Terminal 1 Gate 10",
                        "raw_info": {"full_text": "Gate 10 - Small - 1x  /J"}
                    },
                    "11": {
                        "gate": "11",
                        "terminal": "1",
                        "position_id": "Terminal 1 Gate 11",
                        "raw_info": {"full_text": "Gate 11 - Medium - 2x  /J"}
                    }
                },
                "2": {
                    "20": {
                        "gate": "20",
                        "terminal": "2",
                        "position_id": "Terminal 2 Gate 20",
                        "raw_info": {"full_text": "Gate 20 - Heavy - None"}
                    }
                }
            }
        }

        self.gate_mgmt.rename_gate_entry = Mock()
        self.gate_mgmt.rename_terminal_entry = Mock()
        self.gate_mgmt.new_gate_key_entry = Mock()

    def test_rename_gate_success(self) -> None:
        """Happy path - successfully rename a gate"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_gate_key_entry.get.return_value = "10A"

        self.gate_mgmt.rename_gate()

        self.assertNotIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("10A", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["10A"]["gate"], "10A")
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["10A"]["position_id"], "Terminal 1 Gate 10A")
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_called_once()

    def test_rename_gate_same_key(self) -> None:
        """Renaming gate to same key should still succeed (update in place)"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_gate_key_entry.get.return_value = "10"

        self.gate_mgmt.rename_gate()

        self.assertIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["10"]["gate"], "10")
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)

    def test_rename_gate_conflict_user_proceeds(self) -> None:
        """Gate with new key already exists, user chooses to overwrite"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_gate_key_entry.get.return_value = "11"

        with patch('tkinter.messagebox.askyesno', return_value=True):
            self.gate_mgmt.rename_gate()

        self.assertNotIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("11", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["11"]["raw_info"]["full_text"], "Gate 10 - Small - 1x  /J")
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)

    def test_rename_gate_conflict_user_cancels(self) -> None:
        """Gate with new key already exists, user chooses to cancel"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_gate_key_entry.get.return_value = "11"

        with patch('tkinter.messagebox.askyesno', return_value=False):
            self.gate_mgmt.rename_gate()

        self.assertIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("11", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["11"]["raw_info"]["full_text"], "Gate 11 - Medium - 2x  /J")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_not_called()

    def test_rename_gate_no_data_loaded(self) -> None:
        """Should error when no data is loaded"""
        self.gate_mgmt.data = None
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_gate_key_entry.get.return_value = "10A"

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please load data first")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_rename_gate_missing_fields(self) -> None:
        """Should error when fields are empty"""
        self.gate_mgmt.rename_gate_entry.get.return_value = ""
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_gate_key_entry.get.return_value = "10A"

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please fill all fields")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_rename_gate_terminal_not_found(self) -> None:
        """Should error when terminal doesn't exist"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "99"
        self.gate_mgmt.new_gate_key_entry.get.return_value = "10A"

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Terminal 99 not found")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_rename_gate_gate_not_found(self) -> None:
        """Should error when gate doesn't exist in specified terminal"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "99"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_gate_key_entry.get.return_value = "99A"

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Gate 99 not found in Terminal 1")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)


class TestRenameTerminal(unittest.TestCase):
    """Unit tests for rename_terminal() method"""

    def setUp(self) -> None:
        self.gate_mgmt = MockGateManagementWindow()
        self.gate_mgmt.data = {
            "terminals": {
                "1": {
                    "10": {
                        "gate": "10",
                        "terminal": "1",
                        "position_id": "Terminal 1 Gate 10",
                        "raw_info": {"full_text": "Gate 10 - Small - 1x  /J"}
                    },
                    "11": {
                        "gate": "11",
                        "terminal": "1",
                        "position_id": "Terminal 1 Gate 11",
                        "raw_info": {"full_text": "Gate 11 - Medium - 2x  /J"}
                    }
                },
                "2": {
                    "20": {
                        "gate": "20",
                        "terminal": "2",
                        "position_id": "Terminal 2 Gate 20",
                        "raw_info": {"full_text": "Gate 20 - Heavy - None"}
                    }
                }
            }
        }

        self.gate_mgmt.rename_current_terminal_entry = Mock()
        self.gate_mgmt.rename_new_terminal_entry = Mock()

    def test_rename_terminal_success(self) -> None:
        """Happy path - successfully rename a terminal"""
        self.gate_mgmt.rename_current_terminal_entry.get.return_value = "1"
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "1A"

        self.gate_mgmt.rename_terminal()

        self.assertNotIn("1", self.gate_mgmt.data["terminals"])
        self.assertIn("1A", self.gate_mgmt.data["terminals"])
        self.assertEqual(len(self.gate_mgmt.data["terminals"]["1A"]), 2)
        self.assertEqual(self.gate_mgmt.data["terminals"]["1A"]["10"]["terminal"], "1A")
        self.assertEqual(self.gate_mgmt.data["terminals"]["1A"]["10"]["position_id"], "Terminal 1A Gate 10")
        self.assertEqual(self.gate_mgmt.data["terminals"]["1A"]["11"]["terminal"], "1A")
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_called_once()

    def test_rename_terminal_merge_user_proceeds(self) -> None:
        """Target terminal exists, user chooses to merge"""
        self.gate_mgmt.rename_current_terminal_entry.get.return_value = "1"
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "2"

        with patch('tkinter.messagebox.askyesno', return_value=True):
            self.gate_mgmt.rename_terminal()

        self.assertNotIn("1", self.gate_mgmt.data["terminals"])
        self.assertIn("2", self.gate_mgmt.data["terminals"])
        self.assertEqual(len(self.gate_mgmt.data["terminals"]["2"]), 3)
        self.assertIn("10", self.gate_mgmt.data["terminals"]["2"])
        self.assertIn("20", self.gate_mgmt.data["terminals"]["2"])
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)

    def test_rename_terminal_merge_user_cancels(self) -> None:
        """Target terminal exists, user chooses to cancel"""
        self.gate_mgmt.rename_current_terminal_entry.get.return_value = "1"
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "2"

        with patch('tkinter.messagebox.askyesno', return_value=False):
            self.gate_mgmt.rename_terminal()

        self.assertIn("1", self.gate_mgmt.data["terminals"])
        self.assertIn("2", self.gate_mgmt.data["terminals"])
        self.assertEqual(len(self.gate_mgmt.data["terminals"]["1"]), 2)
        self.assertEqual(len(self.gate_mgmt.data["terminals"]["2"]), 1)
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_not_called()

    def test_rename_terminal_merge_overwrites_gates(self) -> None:
        """Merging terminals should overwrite gates with same number"""
        self.gate_mgmt.data["terminals"]["2"]["10"] = {
            "gate": "10",
            "terminal": "2",
            "position_id": "Terminal 2 Gate 10",
            "raw_info": {"full_text": "Gate 10 - OLD DATA"}
        }

        self.gate_mgmt.rename_current_terminal_entry.get.return_value = "1"
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "2"

        with patch('tkinter.messagebox.askyesno', return_value=True):
            self.gate_mgmt.rename_terminal()

        self.assertEqual(
            self.gate_mgmt.data["terminals"]["2"]["10"]["raw_info"]["full_text"],
            "Gate 10 - Small - 1x  /J"
        )

    def test_rename_terminal_no_data_loaded(self) -> None:
        """Should error when no data is loaded"""
        self.gate_mgmt.data = None
        self.gate_mgmt.rename_current_terminal_entry.get.return_value = "1"
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "1A"

        self.gate_mgmt.rename_terminal()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please load data first")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_rename_terminal_missing_fields(self) -> None:
        """Should error when fields are empty"""
        self.gate_mgmt.rename_current_terminal_entry.get.return_value = ""
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "1A"

        self.gate_mgmt.rename_terminal()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please fill all fields")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_rename_terminal_same_name(self) -> None:
        """Should error when old and new terminal names are the same"""
        self.gate_mgmt.rename_current_terminal_entry.get.return_value = "1"
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "1"

        self.gate_mgmt.rename_terminal()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Old and new terminal names are the same")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_rename_terminal_not_found(self) -> None:
        """Should error when terminal doesn't exist"""
        self.gate_mgmt.rename_current_terminal_entry.get.return_value = "99"
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "99A"

        self.gate_mgmt.rename_terminal()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Terminal 99 not found")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_rename_terminal_updates_all_gate_fields(self) -> None:
        """Should update both terminal and position_id fields for all gates"""
        self.gate_mgmt.rename_current_terminal_entry.get.return_value = "1"
        self.gate_mgmt.rename_new_terminal_entry.get.return_value = "3"

        self.gate_mgmt.rename_terminal()

        for gate_num in ["10", "11"]:
            self.assertEqual(self.gate_mgmt.data["terminals"]["3"][gate_num]["terminal"], "3")
            self.assertEqual(
                self.gate_mgmt.data["terminals"]["3"][gate_num]["position_id"],
                f"Terminal 3 Gate {gate_num}"
            )


class TestAddPrefixSuffix(unittest.TestCase):
    """Unit tests for add_prefix_suffix() method"""

    def setUp(self) -> None:
        self.gate_mgmt = MockGateManagementWindow()
        self.gate_mgmt.data = {
            "terminals": {
                "1": {
                    "10": {
                        "gate": "10",
                        "terminal": "1",
                        "position_id": "Terminal 1 Gate 10",
                        "raw_info": {"full_text": "Gate 10 - Small - 1x  /J"}
                    },
                    "11": {
                        "gate": "11",
                        "terminal": "1",
                        "position_id": "Terminal 1 Gate 11",
                        "raw_info": {"full_text": "Gate 11 - Medium - 2x  /J"}
                    },
                    "A20": {
                        "gate": "A20",
                        "terminal": "1",
                        "position_id": "Terminal 1 Gate A20",
                        "raw_info": {"full_text": "Gate A20 - Heavy - None"}
                    }
                }
            }
        }

        self.gate_mgmt.prefix_entry = Mock()
        self.gate_mgmt.suffix_entry = Mock()
        self.gate_mgmt.tree.selection.return_value = []
        self.gate_mgmt.tree.item = Mock()

    def _setup_tree_item_mock(self, items_data: list):
        """Helper to set up tree.item() mock for multiple items"""
        item_map = {}
        for item_id, gate_text, values in items_data:
            item_map[item_id] = {'text': gate_text, 'values': values}

        def tree_item_side_effect(item, key=None):
            if item not in item_map:
                raise ValueError(f"Item {item} not in mock data")
            if key == 'text':
                return item_map[item]['text']
            elif key == 'values':
                return item_map[item]['values']
            else:
                return item_map[item]

        self.gate_mgmt.tree.item.side_effect = tree_item_side_effect

    def test_add_prefix_success(self) -> None:
        """Happy path - successfully add prefix to gate"""
        self.gate_mgmt.prefix_entry.get.return_value = "A"
        self.gate_mgmt.suffix_entry.get.return_value = ""
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J'))
        ])

        self.gate_mgmt.add_prefix_suffix()

        self.assertNotIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("A10", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["A10"]["gate"], "A10")
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["A10"]["position_id"], "Terminal 1 Gate A10")
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_called_once()

    def test_add_suffix_success(self) -> None:
        """Successfully add suffix to gate"""
        self.gate_mgmt.prefix_entry.get.return_value = ""
        self.gate_mgmt.suffix_entry.get.return_value = "B"
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J'))
        ])

        self.gate_mgmt.add_prefix_suffix()

        self.assertNotIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("10B", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["10B"]["gate"], "10B")
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)

    def test_add_prefix_and_suffix_success(self) -> None:
        """Successfully add both prefix and suffix to gate"""
        self.gate_mgmt.prefix_entry.get.return_value = "A"
        self.gate_mgmt.suffix_entry.get.return_value = "B"
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J'))
        ])

        self.gate_mgmt.add_prefix_suffix()

        self.assertNotIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("A10B", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["A10B"]["gate"], "A10B")
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)

    def test_add_prefix_multiple_gates(self) -> None:
        """Successfully add prefix to multiple gates"""
        self.gate_mgmt.prefix_entry.get.return_value = "A"
        self.gate_mgmt.suffix_entry.get.return_value = ""
        self.gate_mgmt.tree.selection.return_value = ['item1', 'item2']
        self._setup_tree_item_mock([
            ('item1', 'Gate 10', ('Small', '1x  /J', '1', 'Gate 10 - Small - 1x  /J')),
            ('item2', 'Gate 11', ('Medium', '2x  /J', '1', 'Gate 11 - Medium - 2x  /J'))
        ])

        self.gate_mgmt.add_prefix_suffix()

        self.assertIn("A10", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("A11", self.gate_mgmt.data["terminals"]["1"])
        self.assertNotIn("10", self.gate_mgmt.data["terminals"]["1"])
        self.assertNotIn("11", self.gate_mgmt.data["terminals"]["1"])
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)

    def test_add_prefix_skip_existing_user_skips(self) -> None:
        """Gate already has prefix, user chooses to skip"""
        self.gate_mgmt.prefix_entry.get.return_value = "A"
        self.gate_mgmt.suffix_entry.get.return_value = ""
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate A20', ('Heavy', 'None', '1', 'Gate A20 - Heavy - None'))
        ])

        with patch('tkinter.messagebox.askquestion', return_value='no'):
            self.gate_mgmt.add_prefix_suffix()

        self.assertIn("A20", self.gate_mgmt.data["terminals"]["1"])
        self.assertNotIn("AA20", self.gate_mgmt.data["terminals"]["1"])
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)
        self.gate_mgmt.refresh_tree.assert_not_called()

    def test_add_prefix_apply_to_existing_user_proceeds(self) -> None:
        """Gate already has prefix, user chooses to apply anyway"""
        self.gate_mgmt.prefix_entry.get.return_value = "A"
        self.gate_mgmt.suffix_entry.get.return_value = ""
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate A20', ('Heavy', 'None', '1', 'Gate A20 - Heavy - None'))
        ])

        with patch('tkinter.messagebox.askquestion', return_value='yes'):
            self.gate_mgmt.add_prefix_suffix()

        self.assertNotIn("A20", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("AA20", self.gate_mgmt.data["terminals"]["1"])
        self.assertTrue(self.gate_mgmt.has_unsaved_changes)

    def test_add_prefix_no_data_loaded(self) -> None:
        """Should error when no data is loaded"""
        self.gate_mgmt.data = None
        self.gate_mgmt.prefix_entry.get.return_value = "A"
        self.gate_mgmt.suffix_entry.get.return_value = ""

        self.gate_mgmt.add_prefix_suffix()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please load data first")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_add_prefix_no_prefix_or_suffix(self) -> None:
        """Should error when neither prefix nor suffix specified"""
        self.gate_mgmt.prefix_entry.get.return_value = ""
        self.gate_mgmt.suffix_entry.get.return_value = ""

        self.gate_mgmt.add_prefix_suffix()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please specify at least a prefix or suffix")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_add_prefix_no_selection(self) -> None:
        """Should error when no gates are selected"""
        self.gate_mgmt.prefix_entry.get.return_value = "A"
        self.gate_mgmt.suffix_entry.get.return_value = ""
        self.gate_mgmt.tree.selection.return_value = []

        self.gate_mgmt.add_prefix_suffix()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please select gate(s) to modify")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)

    def test_add_prefix_conflict_skipped(self) -> None:
        """Should skip gates where new key already exists"""
        self.gate_mgmt.data["terminals"]["1"]["20"] = {
            "gate": "20",
            "terminal": "1",
            "position_id": "Terminal 1 Gate 20",
            "raw_info": {"full_text": "Gate 20 - Heavy - None"}
        }

        self.gate_mgmt.prefix_entry.get.return_value = "A"
        self.gate_mgmt.suffix_entry.get.return_value = ""
        self.gate_mgmt.tree.selection.return_value = ['item1']
        self._setup_tree_item_mock([
            ('item1', 'Gate 20', ('Heavy', 'None', '1', 'Gate 20 - Heavy - None'))
        ])

        self.gate_mgmt.add_prefix_suffix()

        self.assertIn("20", self.gate_mgmt.data["terminals"]["1"])
        self.assertIn("A20", self.gate_mgmt.data["terminals"]["1"])
        self.assertEqual(self.gate_mgmt.data["terminals"]["1"]["A20"]["raw_info"]["full_text"], "Gate A20 - Heavy - None")
        self.assertFalse(self.gate_mgmt.has_unsaved_changes)


class TestAlphanumericSorting(unittest.TestCase):
    """Test _alphanumeric_key() helper and natural sorting behavior"""

    def setUp(self) -> None:
        self.mock_parent = Mock()

    def test_alphanumeric_key_pure_numeric(self) -> None:
        """Should convert pure numeric strings to integers for sorting"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=False):
            window = GateManagementWindow(self.mock_parent, airport="EDDS")

            result_2 = window._alphanumeric_key("2")
            result_10 = window._alphanumeric_key("10")

            self.assertEqual(result_2, ['', 2, ''])
            self.assertEqual(result_10, ['', 10, ''])
            self.assertTrue(result_2 < result_10)

    def test_alphanumeric_key_alpha_numeric(self) -> None:
        """Should split alphanumeric strings into text and numeric components"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=False):
            window = GateManagementWindow(self.mock_parent, airport="EDDS")

            result_a2 = window._alphanumeric_key("A2")
            result_a10 = window._alphanumeric_key("A10")

            self.assertEqual(result_a2, ['a', 2, ''])
            self.assertEqual(result_a10, ['a', 10, ''])
            self.assertTrue(result_a2 < result_a10)

    def test_alphanumeric_key_complex(self) -> None:
        """Should handle complex alphanumeric patterns like 'A10B2'"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=False):
            window = GateManagementWindow(self.mock_parent, airport="EDDS")

            result = window._alphanumeric_key("A10B2")

            self.assertEqual(result, ['a', 10, 'b', 2, ''])

    def test_sorting_gates_naturally(self) -> None:
        """Should sort gates in natural order: '2' before '10' before '21'"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=False):
            window = GateManagementWindow(self.mock_parent, airport="EDDS")

            unsorted_gates = ["10", "2", "21"]
            sorted_gates = sorted(unsorted_gates, key=window._alphanumeric_key)

            self.assertEqual(sorted_gates, ["2", "10", "21"])

    def test_sorting_preserves_gate_data(self) -> None:
        """Should preserve all gate data when sorting in save_data()"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        unsorted_data = {
            "terminals": {
                "1": {
                    "10": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 10 - Small"}},
                    "2": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 2 - Medium"}},
                    "21": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 21 - Heavy"}}
                }
            }
        }

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=unsorted_data), \
             patch('GateAssignmentDirector.ui.gate_management.json.dump') as mock_dump:

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.save_data()

            saved_data = mock_dump.call_args[0][0]
            gate_keys = list(saved_data["terminals"]["1"].keys())

            self.assertEqual(gate_keys, ["2", "10", "21"])
            self.assertEqual(saved_data["terminals"]["1"]["10"]["raw_info"]["full_text"], "Gate 10 - Small")
            self.assertEqual(saved_data["terminals"]["1"]["2"]["raw_info"]["full_text"], "Gate 2 - Medium")
            self.assertEqual(saved_data["terminals"]["1"]["21"]["raw_info"]["full_text"], "Gate 21 - Heavy")


if __name__ == "__main__":
    unittest.main()

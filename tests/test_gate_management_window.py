import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

sys.modules['customtkinter'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['PIL'] = MagicMock()


class MockGateManagementWindow:
    """Mock class that replicates the move_gate logic from GateManagementWindow"""

    def __init__(self):
        self.data = None
        self.tree = Mock()
        self.to_terminal_entry = Mock()
        self.log_status = Mock()
        self.has_unsaved_changes = False
        self.refresh_tree = Mock()

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

    def test_convert_to_parking_sets_unsaved_flag(self) -> None:
        """Should set has_unsaved_changes=True after successful convert_to_parking()"""
        from GateAssignmentDirector.ui.gate_management import GateManagementWindow

        data = {
            "terminals": {
                "1": {
                    "10": {"type": "gate", "terminal": "1", "raw_info": {"full_text": "Gate 10 - Small"}}
                },
                "2": {
                    "20": {"type": "gate", "terminal": "2", "raw_info": {"full_text": "Gate 20 - Medium"}}
                }
            }
        }

        with patch('GateAssignmentDirector.ui.gate_management.os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('GateAssignmentDirector.ui.gate_management.json.load', return_value=data):

            window = GateManagementWindow(self.mock_parent, airport="EDDS")
            window.has_unsaved_changes = False
            window.active_terminals_entry.get = Mock(return_value="1")

            window.convert_to_parking()

            self.assertTrue(window.has_unsaved_changes)


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

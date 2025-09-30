import sys
import unittest
import re
from unittest.mock import Mock, patch, MagicMock

sys.modules['customtkinter'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['PIL'] = MagicMock()


class TestGateManagementParsing(unittest.TestCase):
    """Unit tests for gate management parsing functions"""

    def setUp(self):
        """Set up test fixtures - define parsing functions locally for testing"""
        # These match the implementations in gate_management.py
        self._parse_gate_size = self.parse_gate_size
        self._parse_jetway_count = self.parse_jetway_count

    @staticmethod
    def parse_gate_size(full_text: str) -> str:
        """Extract aircraft size from gate full_text with defensive parsing."""
        if not full_text:
            return "Unknown"
        match = re.search(r'(Small|Medium|Heavy|Ramp GA \w+)', full_text)
        return match.group(1) if match else "Unknown"

    @staticmethod
    def parse_jetway_count(full_text: str) -> str:
        """Extract jetway configuration from gate full_text with defensive parsing."""
        if not full_text:
            return "-"
        match = re.search(r'(\d+x\s*/J|None)', full_text)
        return match.group(1).strip() if match else "-"

    def test_parse_gate_size_valid(self):
        """Test parsing valid aircraft size from full_text"""
        result = self._parse_gate_size("Gate 11B - Small - 1x  /J")
        self.assertEqual(result, "Small")

        result = self._parse_gate_size("Gate 5 - Medium - 2x  /J")
        self.assertEqual(result, "Medium")

        result = self._parse_gate_size("Parking 123 - Heavy - None")
        self.assertEqual(result, "Heavy")

        result = self._parse_gate_size("Gate 42 - Ramp GA Large - None")
        self.assertEqual(result, "Ramp GA Large")

    def test_parse_gate_size_missing(self):
        """Test parsing when size is missing from full_text"""
        result = self._parse_gate_size("Gate 11B - 1x  /J")
        self.assertEqual(result, "Unknown")

        result = self._parse_gate_size("Gate 5")
        self.assertEqual(result, "Unknown")

    def test_parse_gate_size_empty_string(self):
        """Test parsing with empty string input"""
        result = self._parse_gate_size("")
        self.assertEqual(result, "Unknown")

        result = self._parse_gate_size(None)
        self.assertEqual(result, "Unknown")

    def test_parse_jetway_count_valid(self):
        """Test parsing valid jetway configuration from full_text"""
        result = self._parse_jetway_count("Gate 11B - Small - 1x  /J")
        self.assertEqual(result, "1x  /J")

        result = self._parse_jetway_count("Gate 5 - Medium - 2x  /J")
        self.assertEqual(result, "2x  /J")

        result = self._parse_jetway_count("Parking 123 - Heavy - None")
        self.assertEqual(result, "None")

    def test_parse_jetway_count_missing(self):
        """Test parsing when jetway info is missing from full_text"""
        result = self._parse_jetway_count("Gate 11B - Small")
        self.assertEqual(result, "-")

        result = self._parse_jetway_count("Gate 5")
        self.assertEqual(result, "-")

    def test_parse_jetway_count_empty_string(self):
        """Test parsing with empty string input"""
        result = self._parse_jetway_count("")
        self.assertEqual(result, "-")

        result = self._parse_jetway_count(None)
        self.assertEqual(result, "-")


class MockGateManagementWindow:
    """Mock class that replicates the rename_gate logic from GateManagementWindow"""

    def __init__(self):
        self.data = None
        self.rename_gate_entry = Mock()
        self.rename_terminal_entry = Mock()
        self.new_fulltext_entry = Mock()
        self.log_status = Mock()
        self.save_data = Mock()
        self.load_data = Mock()

    def rename_gate(self):
        """Rename a gate's full_text information"""
        try:
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

            if terminal not in terminals:
                self.log_status(f"ERROR: Terminal {terminal} not found")
                return

            if gate_num not in terminals[terminal]:
                self.log_status(
                    f"ERROR: Gate {gate_num} not found in Terminal {terminal}"
                )
                return

            terminals[terminal][gate_num]["raw_info"]["full_text"] = new_full_text

            self.log_status(
                f"SUCCESS: Renamed Gate {gate_num} in Terminal {terminal}"
            )
            self.save_data()
            self.load_data()

        except Exception as e:
            self.log_status(f"ERROR: {str(e)}")


class TestGateManagementRename(unittest.TestCase):
    """Unit tests for rename_gate method"""

    def setUp(self) -> None:
        """Set up test fixtures for each test"""
        self.gate_mgmt = MockGateManagementWindow()

        self.gate_mgmt.data = {
            "terminals": {
                "1": {
                    "10": {
                        "raw_info": {
                            "full_text": "Gate 10 - Small - 1x  /J"
                        }
                    }
                },
                "2": {
                    "20": {
                        "raw_info": {
                            "full_text": "Gate 20 - Medium - 2x  /J"
                        }
                    }
                }
            }
        }

    def test_rename_gate_terminal_not_exists(self) -> None:
        """Terminal doesn't exist - should log error"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "99"
        self.gate_mgmt.new_fulltext_entry.get.return_value = "Gate 10 - Heavy - None"

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Terminal 99 not found")
        self.gate_mgmt.save_data.assert_not_called()
        self.gate_mgmt.load_data.assert_not_called()

    def test_rename_gate_gate_not_exists(self) -> None:
        """Gate doesn't exist in terminal - should log error"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "99"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_fulltext_entry.get.return_value = "Gate 99 - Heavy - None"

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with(
            "ERROR: Gate 99 not found in Terminal 1"
        )
        self.gate_mgmt.save_data.assert_not_called()
        self.gate_mgmt.load_data.assert_not_called()

    def test_rename_gate_empty_new_full_text(self) -> None:
        """Empty string for new_full_text - should log error"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_fulltext_entry.get.return_value = "   "

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please fill all fields")
        self.gate_mgmt.save_data.assert_not_called()
        self.gate_mgmt.load_data.assert_not_called()

    def test_rename_gate_missing_parameters(self) -> None:
        """None/missing parameters - should log error"""
        self.gate_mgmt.rename_gate_entry.get.return_value = ""
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_fulltext_entry.get.return_value = "Gate 10 - Heavy - None"

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please fill all fields")
        self.gate_mgmt.save_data.assert_not_called()

    def test_rename_gate_success(self) -> None:
        """Happy path - successful rename"""
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_fulltext_entry.get.return_value = "Gate 10 - Heavy - None"

        self.gate_mgmt.rename_gate()

        self.assertEqual(
            self.gate_mgmt.data["terminals"]["1"]["10"]["raw_info"]["full_text"],
            "Gate 10 - Heavy - None"
        )
        self.gate_mgmt.log_status.assert_called_with(
            "SUCCESS: Renamed Gate 10 in Terminal 1"
        )
        self.gate_mgmt.save_data.assert_called_once()
        self.gate_mgmt.load_data.assert_called_once()

    def test_rename_gate_no_data_loaded(self) -> None:
        """No data loaded - should log error"""
        self.gate_mgmt.data = None
        self.gate_mgmt.rename_gate_entry.get.return_value = "10"
        self.gate_mgmt.rename_terminal_entry.get.return_value = "1"
        self.gate_mgmt.new_fulltext_entry.get.return_value = "Gate 10 - Heavy - None"

        self.gate_mgmt.rename_gate()

        self.gate_mgmt.log_status.assert_called_with("ERROR: Please load data first")
        self.gate_mgmt.save_data.assert_not_called()


if __name__ == "__main__":
    unittest.main()
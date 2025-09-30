import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import json
from pathlib import Path
from GateAssignmentDirector.menu_logger import MenuLogger, GateInfo


class TestMenuLogger(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock()
        self.mock_config.logging_level = "INFO"
        self.mock_config.logging_format = "%(message)s"
        self.mock_config.logging_datefmt = "%Y-%m-%d"

        with patch('pathlib.Path.mkdir'):
            self.logger = MenuLogger(self.mock_config, logs_dir="test_logs")

    def test_start_session(self):
        """Test starting a new logging session"""
        gate_info = GateInfo(airport="KLAX")

        self.logger.start_session(gate_info)

        self.assertEqual(self.logger.current_airport, "KLAX")
        self.assertEqual(self.logger.menu_map["airport"], "KLAX")
        self.assertIsNotNone(self.logger.menu_map["last_updated"])

    def test_interpret_position_simple_gate(self):
        """Test interpreting simple gate like '5A'"""
        position_info = {
            "full_text": "Gate 5A - Small",
            "menu_index": 2,
            "level_0_index": 1,
            "next_clicks": 0
        }

        result = self.logger._interpret_position("5A", position_info, "gate")

        self.assertEqual(result["terminal"], "Terminal")  # Single digit defaults
        self.assertEqual(result["gate"], "5A")
        self.assertEqual(result["type"], "gate")

    def test_interpret_position_two_digit_gate(self):
        """Test interpreting two-digit gate like '25B'"""
        position_info = {
            "full_text": "Gate 25B",
            "menu_index": 3
        }

        result = self.logger._interpret_position("25B", position_info, "gate")

        self.assertEqual(result["terminal"], "2")  # First digit is terminal
        self.assertEqual(result["gate"], "25B")

    def test_interpret_position_three_digit_parking(self):
        """Test interpreting three-digit parking spot"""
        position_info = {
            "full_text": "Parking 101",
            "menu_index": 1
        }

        result = self.logger._interpret_position("Parking 101", position_info, "parking")

        self.assertEqual(result["terminal"], "Parking")  # 3 digits = Parking
        self.assertEqual(result["gate"], "101")

    def test_interpret_position_letter_prefix_gate(self):
        """Test interpreting gate with letter prefix like 'A25'"""
        position_info = {
            "full_text": "Gate A25",
            "menu_index": 2
        }

        result = self.logger._interpret_position("A25", position_info, "gate")

        self.assertEqual(result["terminal"], "2")
        self.assertEqual(result["gate"], "25A")  # Letter moved to suffix

    def test_interpret_position_special_terminal_prefix(self):
        """Test interpreting gate with special terminal prefix like 'Z52H'"""
        position_info = {
            "full_text": "Gate Z52H",
            "menu_index": 1
        }

        result = self.logger._interpret_position("Z52H", position_info, "gate")

        self.assertEqual(result["terminal"], "Z")  # Special terminal
        self.assertEqual(result["gate"], "52H")

    def test_interpret_position_with_gate_letter_prefix(self):
        """Test interpreting gate like 'A42B' where A is gate letter"""
        position_info = {
            "full_text": "Gate A42B",
            "menu_index": 3
        }

        result = self.logger._interpret_position("A42B", position_info, "gate")

        # A is a gate letter, so it should be handled specially
        self.assertEqual(result["gate"], "42B")
        self.assertEqual(result["terminal"], "4")

    def test_add_to_terminals(self):
        """Test adding position to terminal structure"""
        interpreted_data = {"terminals": {}}

        result = {
            "terminal": "1",
            "gate": "5A",
            "position_id": "Terminal 1 Gate 5A",
            "type": "gate",
            "raw_info": {}
        }

        self.logger._add_to_terminals(interpreted_data, result)

        self.assertIn("1", interpreted_data["terminals"])
        self.assertIn("5A", interpreted_data["terminals"]["1"])
        self.assertEqual(
            interpreted_data["terminals"]["1"]["5A"]["position_id"],
            "Terminal 1 Gate 5A"
        )

    def test_add_multiple_gates_to_same_terminal(self):
        """Test adding multiple gates to the same terminal"""
        interpreted_data = {"terminals": {}}

        gates = [
            {
                "terminal": "1",
                "gate": "5A",
                "position_id": "Terminal 1 Gate 5A",
                "type": "gate",
                "raw_info": {}
            },
            {
                "terminal": "1",
                "gate": "5B",
                "position_id": "Terminal 1 Gate 5B",
                "type": "gate",
                "raw_info": {}
            }
        ]

        for gate in gates:
            self.logger._add_to_terminals(interpreted_data, gate)

        self.assertEqual(len(interpreted_data["terminals"]["1"]), 2)
        self.assertIn("5A", interpreted_data["terminals"]["1"])
        self.assertIn("5B", interpreted_data["terminals"]["1"])

    def test_extract_gates_and_spots_from_menu(self):
        """Test extracting gates from menu options"""
        options = ["Gate 5A", "Gate 5B", "Next", "Back"]
        menu_title = "Select Gate"
        navigation_info = {"level_0_index": 1, "next_clicks": 0}

        self.logger._extract_gates_and_spots(options, menu_title, navigation_info)

        # Check gates were added
        self.assertIn("5A", self.logger.menu_map["available_gates"])
        self.assertIn("5B", self.logger.menu_map["available_gates"])

    def test_extract_gates_skips_navigation_options(self):
        """Test that navigation options are not extracted as gates"""
        options = ["Next", "Previous", "Back", "Exit", "Cancel"]
        menu_title = "Select Gate"

        self.logger._extract_gates_and_spots(options, menu_title, None)

        # No gates should be added
        self.assertEqual(len(self.logger.menu_map["available_gates"]), 0)

    def test_extract_parking_spots(self):
        """Test extracting parking spots from menu"""
        options = ["Parking 101", "Parking 102", "Stand A"]
        menu_title = "Select Parking"
        navigation_info = {"level_0_index": 2, "next_clicks": 1}

        self.logger._extract_gates_and_spots(options, menu_title, navigation_info)

        # Check spots were added
        self.assertIn("101", self.logger.menu_map["available_spots"])

    def test_log_menu_state_skips_airport_select(self):
        """Test that airport selection menu is skipped"""
        self.logger.log_menu_state(
            title="Select airport",
            options=["KLAX", "KJFK"],
            menu_depth=0
        )

        # Nothing should be added to seen_menus
        self.assertEqual(len(self.logger.seen_menus), 0)

    def test_log_menu_state_tracks_unique_menus(self):
        """Test that identical menus are not logged twice"""
        options = ["Option 1", "Option 2"]

        self.logger.log_menu_state(
            title="Test Menu",
            options=options,
            menu_depth=1
        )

        initial_count = len(self.logger.seen_menus)

        # Log same menu again
        self.logger.log_menu_state(
            title="Test Menu",
            options=options,
            menu_depth=1
        )

        # Count should not increase
        self.assertEqual(len(self.logger.seen_menus), initial_count)

    def test_log_menu_state_different_options_same_title(self):
        """Test that menus with same title but different options are tracked separately"""
        self.logger.log_menu_state(
            title="Test Menu",
            options=["Option 1", "Option 2"],
            menu_depth=1
        )

        first_count = len(self.logger.seen_menus)

        self.logger.log_menu_state(
            title="Test Menu",
            options=["Option 3", "Option 4"],  # Different options
            menu_depth=1
        )

        # Count should increase
        self.assertGreater(len(self.logger.seen_menus), first_count)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_session(self, mock_json_dump, mock_file):
        """Test saving session to file"""
        self.logger.current_airport = "KLAX"
        self.logger.menu_map["available_gates"] = {"5A": {}, "5B": {}}

        with patch.object(Path, 'mkdir'):
            filepath = self.logger.save_session()

        self.assertIn("KLAX", filepath)
        mock_json_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='{"airport": "KLAX"}')
    @patch('json.load')
    @patch('pathlib.Path.exists')
    def test_load_airport_map(self, mock_exists, mock_json_load, mock_file):
        """Test loading airport map from file"""
        mock_exists.return_value = True
        mock_json_load.return_value = {"airport": "KLAX", "terminals": {}}

        result = self.logger.load_airport_map("KLAX")

        self.assertIsNotNone(result)
        self.assertEqual(result["airport"], "KLAX")

    @patch('pathlib.Path.exists')
    def test_load_airport_map_file_not_found(self, mock_exists):
        """Test loading airport map when file doesn't exist"""
        mock_exists.return_value = False

        result = self.logger.load_airport_map("NOTFOUND")

        self.assertIsNone(result)

    def test_gate_info_to_dict(self):
        """Test converting GateInfo to dictionary"""
        gate_info = GateInfo(
            airport="KLAX",
            terminal="1",
            gate_number="5",
            gate_letter="A"
        )

        result = gate_info.to_dict()

        self.assertEqual(result["airport"], "KLAX")
        self.assertEqual(result["terminal"], "1")
        self.assertEqual(result["gate_number"], "5")
        self.assertEqual(result["gate_letter"], "A")


if __name__ == "__main__":
    unittest.main()
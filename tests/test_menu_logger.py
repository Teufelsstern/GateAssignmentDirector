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
        self.mock_config.position_keywords = {
            'gsx_gate': ['Gate', 'Dock'],
            'gsx_parking': ['Parking', 'Stand', 'Remote', 'Ramp', 'Apron'],
            'si_terminal': ['Terminal', 'International', 'Parking', 'Domestic', 'Main', 'Central', 'Pier', 'Concourse', 'Level', 'Apron', 'Stand']
        }
        self.mock_config.matching_weights = {
            'gate_number': 0.6,
            'gate_prefix': 0.3,
            'terminal': 0.1
        }

        with patch('pathlib.Path.mkdir'):
            self.logger = MenuLogger(self.mock_config, logs_dir="test_logs")

    def test_start_session(self):
        """Test starting a new logging session"""
        gate_info = GateInfo(airport="KLAX")

        self.logger.start_session(gate_info)

        self.assertEqual(self.logger.current_airport, "KLAX")
        self.assertEqual(self.logger.menu_map["airport"], "KLAX")
        self.assertIsNotNone(self.logger.menu_map["created"])

    def test_interpret_position_simple_gate(self):
        """Test interpreting simple gate like 'Gate 5A' with terminal context from menu"""
        position_info = {
            "full_text": "Gate 5A - Small",
            "menu_index": 2,
            "found_in_menu": "Terminal - A-Pier (A1-A16)",
            "level_0_page": 1,
            "level_0_option_index": 0,
            "level_1_next_clicks": 0
        }

        result = self.logger._interpret_position("Gate 5A", position_info, "gate")

        self.assertEqual(result["terminal"], "A-Pier")
        self.assertEqual(result["gate"], "5A")
        self.assertEqual(result["type"], "gate")
        self.assertEqual(result["position_id"], "Terminal A-Pier Gate 5A")

    def test_interpret_position_two_digit_gate(self):
        """Test interpreting two-digit gate with terminal context"""
        position_info = {
            "full_text": "Gate 25B",
            "menu_index": 3,
            "found_in_menu": "Terminal - B Concourse (B20-B30)"
        }

        result = self.logger._interpret_position("Gate 25B", position_info, "gate")

        self.assertEqual(result["terminal"], "B Concourse")
        self.assertEqual(result["gate"], "25B")
        self.assertEqual(result["position_id"], "Terminal B Concourse Gate 25B")

    def test_interpret_position_three_digit_parking(self):
        """Test interpreting parking spot with menu context"""
        position_info = {
            "full_text": "Parking 101",
            "menu_index": 1,
            "found_in_menu": "Parking - Long Term (100-200)"
        }

        result = self.logger._interpret_position("Parking 101", position_info, "parking")

        self.assertEqual(result["terminal"], "Long Term")
        self.assertEqual(result["gate"], "101")
        self.assertEqual(result["position_id"], "Terminal Long Term Stand 101")

    def test_interpret_position_stand_with_space(self):
        """Test interpreting stand with space in identifier"""
        position_info = {
            "full_text": "Stand V 20 - Ramp GA",
            "menu_index": 2,
            "found_in_menu": "Apron - West I (V61-V76)"
        }

        result = self.logger._interpret_position("Stand V 20", position_info, "gate")

        self.assertEqual(result["terminal"], "West I")
        self.assertEqual(result["gate"], "V 20")
        self.assertEqual(result["position_id"], "Terminal West I Gate V 20")

    def test_interpret_position_gate_with_menu_fallback(self):
        """Test interpreting gate where menu title has only type keyword"""
        position_info = {
            "full_text": "Gate Z52H",
            "menu_index": 1,
            "found_in_menu": "Select Gate"
        }

        result = self.logger._interpret_position("Gate Z52H", position_info, "gate")

        self.assertEqual(result["terminal"], "Terminal 1")  # Falls back to Terminal 1
        self.assertEqual(result["gate"], "Z52H")
        self.assertEqual(result["position_id"], "Terminal 1 Gate Z52H")

    def test_interpret_position_without_found_in_menu(self):
        """Test interpreting position when found_in_menu is missing"""
        position_info = {
            "full_text": "Gate A42B",
            "menu_index": 3
        }

        result = self.logger._interpret_position("Gate A42B", position_info, "gate")

        # Should fallback to "Terminal 1" when no menu context is available
        self.assertEqual(result["terminal"], "Terminal 1")
        self.assertEqual(result["gate"], "A42B")
        self.assertEqual(result["position_id"], "Terminal 1 Gate A42B")

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
        navigation_info = {"level_0_page": 1, "level_0_option_index": 0, "level_1_next_clicks": 0}

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
        navigation_info = {"level_0_page": 1, "level_0_option_index": 1, "level_1_next_clicks": 1}

        self.logger._extract_gates_and_spots(options, menu_title, navigation_info)

        # Check spots were added (stored with full text as key)
        self.assertIn("Parking 101", self.logger.menu_map["available_spots"])

    def test_parking_menu_does_not_extract_gates(self):
        """Test that parking menu doesn't extract items as gates"""
        options = ["Parking 101", "Gate 5A", "Stand A"]
        menu_title = "Select Parking"
        navigation_info = {"level_0_page": 1, "level_0_option_index": 1, "level_1_next_clicks": 1}

        self.logger._extract_gates_and_spots(options, menu_title, navigation_info)

        # Parking menu should not add to available_gates
        self.assertEqual(len(self.logger.menu_map["available_gates"]), 0)
        # But should add to available_spots
        self.assertGreater(len(self.logger.menu_map["available_spots"]), 0)

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

    def test_extract_terminal_from_menu_with_specific_name(self):
        """Test extracting specific terminal name from menu title"""
        result = self.logger._extract_terminal_from_menu("Terminal - A-Pier (A1-A16)")
        self.assertEqual(result, "A-Pier")

        result = self.logger._extract_terminal_from_menu("Apron - West I (V61-V76)")
        self.assertEqual(result, "West I")

        result = self.logger._extract_terminal_from_menu("Gate - North Wing (N1-N20)")
        self.assertEqual(result, "North Wing")

    def test_extract_terminal_from_menu_fallback_to_type(self):
        """Test falling back based on menu type when specific name is weird"""
        result = self.logger._extract_terminal_from_menu("Terminal - (weird)")
        self.assertEqual(result, "Terminal 1")

        result = self.logger._extract_terminal_from_menu("Apron - ")
        self.assertEqual(result, "Parking")  # Apron menus get "Parking" fallback

    def test_extract_terminal_from_menu_simple_keyword(self):
        """Test falling back based on menu type"""
        result = self.logger._extract_terminal_from_menu("Select Gate")
        self.assertEqual(result, "Terminal 1")

        result = self.logger._extract_terminal_from_menu("Choose Terminal")
        self.assertEqual(result, "Terminal 1")

        result = self.logger._extract_terminal_from_menu("Parking Options")
        self.assertEqual(result, "Parking")  # Parking menus get "Parking" fallback

    def test_extract_terminal_from_menu_unknown_fallback(self):
        """Test fallback to Terminal 1 when no recognizable pattern exists"""
        result = self.logger._extract_terminal_from_menu("Some Random Menu Title")
        self.assertEqual(result, "Terminal 1")

    def test_extract_gate_identifier_removes_gate_keyword(self):
        """Test removing 'Gate' keyword from position ID"""
        result = self.logger._extract_gate_identifier("Gate 11B")
        self.assertEqual(result, "11B")

        result = self.logger._extract_gate_identifier("Gate A25")
        self.assertEqual(result, "A25")

    def test_extract_gate_identifier_removes_stand_keyword(self):
        """Test removing 'Stand' keyword from position ID"""
        result = self.logger._extract_gate_identifier("Stand V20")
        self.assertEqual(result, "V20")

        result = self.logger._extract_gate_identifier("Stand V 20")
        self.assertEqual(result, "V 20")

    def test_extract_gate_identifier_removes_parking_keyword(self):
        """Test removing 'Parking' keyword from position ID"""
        result = self.logger._extract_gate_identifier("Parking 101")
        self.assertEqual(result, "101")

    def test_extract_gate_identifier_removes_dock_keyword(self):
        """Test removing 'Dock' keyword from position ID"""
        result = self.logger._extract_gate_identifier("Dock 5A")
        self.assertEqual(result, "5A")

    def test_extract_gate_identifier_preserves_spaces(self):
        """Test that spaces within identifiers are preserved"""
        result = self.logger._extract_gate_identifier("Stand V 20")
        self.assertEqual(result, "V 20")

        result = self.logger._extract_gate_identifier("Gate 2 B")
        self.assertEqual(result, "2 B")

    def test_extract_gate_identifier_no_keyword(self):
        """Test extracting identifier when no keyword is present"""
        result = self.logger._extract_gate_identifier("A16")
        self.assertEqual(result, "A16")

        result = self.logger._extract_gate_identifier("V20")
        self.assertEqual(result, "V20")

    def test_extract_gate_identifier_case_insensitive(self):
        """Test that keyword removal is case insensitive"""
        result = self.logger._extract_gate_identifier("GATE 11B")
        self.assertEqual(result, "11B")

        result = self.logger._extract_gate_identifier("stand V20")
        self.assertEqual(result, "V20")


if __name__ == "__main__":
    unittest.main()
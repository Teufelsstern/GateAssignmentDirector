import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import json
from GateAssignmentDirector.gate_assignment import GateAssignment
from GateAssignmentDirector.exceptions import GsxMenuError


class TestGateAssignment(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with all mocked dependencies"""
        self.mock_config = Mock()
        self.mock_config.logging_level = "INFO"
        self.mock_config.logging_format = "%(message)s"
        self.mock_config.logging_datefmt = "%Y-%m-%d"
        self.mock_config.SI_API_KEY = "test_key"

        self.mock_menu_logger = Mock()
        self.mock_menu_reader = Mock()
        self.mock_menu_navigator = Mock()
        self.mock_sim_manager = Mock()

        self.gate_assignment = GateAssignment(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_reader,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

    def test_wait_for_ground_success(self):
        """Test waiting for aircraft on ground succeeds"""
        self.mock_sim_manager.is_on_ground.return_value = True

        self.gate_assignment._wait_for_ground()

        self.mock_sim_manager.is_on_ground.assert_called()

    def test_wait_for_ground_infinite_loop(self):
        """Test waiting for aircraft handles infinite waiting"""
        # Simulate a few False checks before landing
        self.mock_sim_manager.is_on_ground.side_effect = [False, False, False, True]

        self.gate_assignment._wait_for_ground()

        # Should have called multiple times
        self.assertGreater(self.mock_sim_manager.is_on_ground.call_count, 3)

    def test_wait_for_ground_eventually_lands(self):
        """Test aircraft lands during wait period"""
        # First 2 calls return False, 3rd returns True
        self.mock_sim_manager.is_on_ground.side_effect = [False, False, True]

        self.gate_assignment._wait_for_ground()

        self.assertEqual(self.mock_sim_manager.is_on_ground.call_count, 3)

    def test_find_gate_exact_match(self):
        """Test finding gate with exact terminal and gate match"""
        airport_data = {
            "terminals": {
                "1": {
                    "5A": {"position_id": "Gate 1-5A", "gate": "5A"}
                }
            }
        }

        result, is_direct = self.gate_assignment.find_gate(airport_data, "1", "5A")

        self.assertTrue(is_direct)
        self.assertEqual(result["position_id"], "Gate 1-5A")

    def test_find_gate_fuzzy_match(self):
        """Test finding gate with fuzzy matching"""
        airport_data = {
            "terminals": {
                "Terminal1": {
                    "Gate5A": {"position_id": "T1-G5A", "gate": "Gate5A"}
                }
            }
        }

        result, is_direct = self.gate_assignment.find_gate(airport_data, "1", "5A")

        self.assertFalse(is_direct)
        self.assertIsNotNone(result)

    def test_find_gate_no_match(self):
        """Test finding gate with no good matches"""
        airport_data = {
            "terminals": {
                "A": {
                    "1": {"position_id": "Gate A1", "gate": "1"}
                }
            }
        }

        # Looking for something very different
        result, is_direct = self.gate_assignment.find_gate(airport_data, "Z", "99")

        self.assertFalse(is_direct)
        # Should still return best match even if score is low
        self.assertIsNotNone(result)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_map_available_spots_file_exists(self, mock_json_load, mock_file, mock_exists):
        """Test mapping spots when interpreted file already exists"""
        mock_exists.side_effect = lambda path: "_interpreted.json" in path
        mock_json_load.return_value = {"terminals": {}}

        result = self.gate_assignment.map_available_spots("KLAX")

        self.assertEqual(result, {"terminals": {}})
        # Should not start a new session if file exists
        self.mock_menu_logger.start_session.assert_not_called()

    @patch('os.path.exists')
    @patch('os.getcwd')
    def test_map_available_spots_creates_new(self, mock_getcwd, mock_exists):
        """Test mapping spots creates new data when files don't exist"""
        mock_exists.return_value = False
        mock_getcwd.return_value = "/test/path"

        self.mock_menu_reader.read_menu.return_value = Mock(
            title="GSX Menu", options=["Option 1", "Option 2"]
        )
        self.mock_menu_navigator.click_by_index.return_value = True

        with patch('builtins.open', mock_open(read_data='{"terminals": {}}')):
            with patch('json.load', return_value={"terminals": {}}):
                result = self.gate_assignment.map_available_spots("KLAX")

        # Should have started a session
        self.mock_menu_logger.start_session.assert_called_once()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('requests.get')
    def test_assign_gate_with_fuzzy_match(self, mock_requests, mock_json_load, mock_file, mock_exists):
        """Test gate assignment with fuzzy matching calls API"""
        mock_exists.side_effect = lambda path: "_interpreted.json" in path
        mock_json_load.return_value = {
            "terminals": {
                "1": {
                    "5A": {"position_id": "Gate 1-5A", "gate": "5A"}
                }
            }
        }

        self.mock_sim_manager.is_on_ground.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response

        # Fuzzy match scenario (terminal "Terminal1" vs "1")
        with patch.object(self.gate_assignment, 'find_gate', return_value=(
            {"position_id": "Gate 1-5A", "gate": "5A"}, False
        )):
            result = self.gate_assignment.assign_gate(
                airport="KLAX",
                terminal="Terminal",
                terminal_number="1",
                gate_number="5",
                gate_letter="A"
            )

        # API should be called for fuzzy match
        mock_requests.assert_called_once()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_assign_gate_not_on_ground_with_wait(self, mock_json_load, mock_file, mock_exists):
        """Test gate assignment waits for ground"""
        mock_exists.side_effect = lambda path: "_interpreted.json" in path
        mock_json_load.return_value = {
            "terminals": {
                "1": {
                    "5": {"position_id": "Gate 1-5", "gate": "5"}
                }
            }
        }

        # First call False (not on ground), second True (on ground)
        self.mock_sim_manager.is_on_ground.side_effect = [False, True]

        result = self.gate_assignment.assign_gate(
            airport="KLAX",
            gate_number="5",
            wait_for_ground=True
        )

        # Should have waited for ground
        self.assertGreater(self.mock_sim_manager.is_on_ground.call_count, 1)


    def test_open_menu(self):
        """Test opening GSX menu sets correct variables"""
        self.gate_assignment._open_menu()

        # Verify the correct SimConnect variables were set
        calls = self.mock_sim_manager.set_variable.call_args_list
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
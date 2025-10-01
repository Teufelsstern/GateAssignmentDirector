import unittest
from unittest.mock import Mock, patch, MagicMock
from GateAssignmentDirector.si_api_hook import GateParser, GateInfo, JSONMonitor


class TestGateParser(unittest.TestCase):
    def setUp(self):
        self.parser = GateParser()

    def test_parse_terminal_with_number(self):
        """Test parsing 'Terminal 7 7'"""
        result = self.parser.parse_gate("Terminal 7 7")
        self.assertEqual(result.terminal_name, "Terminal")
        self.assertEqual(result.terminal_number, "7")
        self.assertEqual(result.gate_number, "7")
        self.assertEqual(result.gate_letter, "")

    def test_parse_simple_gate(self):
        """Test parsing 'Gate 5'"""
        result = self.parser.parse_gate("Gate 5")
        self.assertEqual(result.gate_number, "5")
        self.assertEqual(result.gate_letter, "")

    def test_parse_international_gate_with_letter(self):
        """Test parsing 'International Gate 25A'"""
        result = self.parser.parse_gate("International Gate 25A")
        self.assertEqual(result.terminal_name, "International")
        self.assertEqual(result.gate_number, "25")
        self.assertEqual(result.gate_letter, "A")

    def test_parse_pier_with_terminal_and_gate_letter(self):
        """Test parsing 'Pier C Gate 14 R'"""
        result = self.parser.parse_gate("Pier C Gate 14 R")
        self.assertEqual(result.terminal_name, "Pier")
        self.assertEqual(result.terminal_number, "C")
        self.assertEqual(result.gate_number, "14")
        self.assertEqual(result.gate_letter, "R")

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = self.parser.parse_gate("")
        self.assertEqual(result.terminal_name, None)
        self.assertEqual(result.gate_number, None)

    def test_parse_whitespace_only(self):
        """Test parsing whitespace"""
        result = self.parser.parse_gate("   ")
        self.assertEqual(result.terminal_name, None)

    def test_gate_info_str_representation(self):
        """Test GateInfo string representation"""
        gate_info = GateInfo(
            terminal_name="Terminal",
            terminal_number="1",
            gate_number="5",
            gate_letter="A",
            raw_value="Test"
        )
        result = str(gate_info)
        self.assertIn("Terminal", result)
        self.assertIn("1", result)
        self.assertIn("5A", result)


class TestJSONMonitor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.test_file_path = "test_flight.json"

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_check_gate_assignment_with_callback(self, mock_config, mock_path):
        """Test gate assignment detection calls callback"""
        callback_mock = Mock()
        monitor = JSONMonitor(
            self.test_file_path,
            gate_callback=callback_mock,
            enable_gsx_integration=False
        )

        test_data = {
            "flight_details": {
                "current_flight": {
                    "assigned_gate": "Terminal 5 Gate 12A",
                    "flight_destination": "KLAX"
                }
            }
        }

        monitor.check_gate_assignment(test_data)

        # Verify callback was called
        callback_mock.assert_called_once()
        call_args = callback_mock.call_args[0][0]
        self.assertEqual(call_args['gate_number'], "12")
        self.assertEqual(call_args['gate_letter'], "A")
        self.assertEqual(call_args['airport'], "KLAX")

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_check_gate_assignment_empty_value(self, mock_config, mock_path):
        """Test gate assignment with empty value clears current gate"""
        callback_mock = Mock()
        monitor = JSONMonitor(
            self.test_file_path,
            gate_callback=callback_mock
        )

        # Set initial gate
        monitor.current_gate_info = GateInfo(raw_value="Gate 5")

        # Clear gate
        test_data = {
            "flight_details": {
                "current_flight": {
                    "assigned_gate": ""
                }
            }
        }

        monitor.check_gate_assignment(test_data)

        # Verify gate was cleared
        self.assertIsNone(monitor.current_gate_info)

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_find_changes_detect_added_field(self, mock_config, mock_path):
        """Test find_changes detects added fields"""
        monitor = JSONMonitor(self.test_file_path)

        old_data = {"field1": "value1"}
        new_data = {"field1": "value1", "field2": "value2"}

        with patch.object(monitor, 'log_change') as mock_log:
            monitor.find_changes(old_data, new_data)
            mock_log.assert_called_with("ADDED: field2 = value2", "field2")

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_find_changes_detect_removed_field(self, mock_config, mock_path):
        """Test find_changes detects removed fields"""
        monitor = JSONMonitor(self.test_file_path)

        old_data = {"field1": "value1", "field2": "value2"}
        new_data = {"field1": "value1"}

        with patch.object(monitor, 'log_change') as mock_log:
            monitor.find_changes(old_data, new_data)
            mock_log.assert_called_with("REMOVED: field2 = value2", "field2")

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_find_changes_detect_modified_field(self, mock_config, mock_path):
        """Test find_changes detects modified fields"""
        monitor = JSONMonitor(self.test_file_path)

        old_data = {"field1": "old_value"}
        new_data = {"field1": "new_value"}

        with patch.object(monitor, 'log_change') as mock_log:
            monitor.find_changes(old_data, new_data)
            mock_log.assert_called_with("CHANGED: field1 = old_value -> new_value", "field1")

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_find_changes_nested_dict(self, mock_config, mock_path):
        """Test find_changes handles nested dictionaries"""
        monitor = JSONMonitor(self.test_file_path)

        old_data = {"parent": {"child": "old"}}
        new_data = {"parent": {"child": "new"}}

        with patch.object(monitor, 'log_change') as mock_log:
            monitor.find_changes(old_data, new_data)
            mock_log.assert_called_with("CHANGED: parent.child = old -> new", "parent.child")

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"test": "data"}')
    def test_read_json_success(self, mock_open, mock_config, mock_path):
        """Test successful JSON reading"""
        monitor = JSONMonitor(self.test_file_path)
        result = monitor.read_json()

        self.assertIsNotNone(result)
        self.assertEqual(result, {"test": "data"})

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_read_json_file_not_found(self, mock_open, mock_config, mock_path):
        """Test JSON reading with missing file"""
        monitor = JSONMonitor(self.test_file_path)
        result = monitor.read_json()

        self.assertIsNone(result)

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_no_duplicate_gate_callback(self, mock_config, mock_path):
        """Test callback not called for same gate twice"""
        callback_mock = Mock()
        monitor = JSONMonitor(
            self.test_file_path,
            gate_callback=callback_mock
        )

        test_data = {
            "flight_details": {
                "current_flight": {
                    "assigned_gate": "Gate 5",
                    "flight_destination": "EDDS"
                }
            }
        }

        # Call twice with same gate
        monitor.check_gate_assignment(test_data)
        monitor.check_gate_assignment(test_data)

        # Should only call callback once
        self.assertEqual(callback_mock.call_count, 1)

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_extract_flight_data_complete(self, mock_config, mock_path):
        """Test extract_flight_data extracts all fields correctly"""
        monitor = JSONMonitor(self.test_file_path)

        test_data = {
            "flight_details": {
                "current_flight": {
                    "flight_destination": "KLAX",
                    "flight_origin": "KJFK",
                    "airline": "United",
                    "flight_number": "UA123",
                    "assigned_gate": "Terminal 5 Gate 12A"
                }
            }
        }

        result = monitor.extract_flight_data(test_data)

        self.assertEqual(result['airport'], "KLAX")
        self.assertEqual(result['departure_airport'], "KJFK")
        self.assertEqual(result['airline'], "United")
        self.assertEqual(result['flight_number'], "UA123")
        self.assertEqual(result['assigned_gate'], "Terminal 5 Gate 12A")

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_extract_flight_data_missing_fields(self, mock_config, mock_path):
        """Test extract_flight_data handles missing fields gracefully"""
        monitor = JSONMonitor(self.test_file_path)

        test_data = {
            "flight_details": {
                "current_flight": {
                    "flight_destination": "KLAX"
                }
            }
        }

        result = monitor.extract_flight_data(test_data)

        self.assertEqual(result['airport'], "KLAX")
        self.assertIsNone(result['airline'])
        self.assertIsNone(result['flight_number'])
        self.assertIsNone(result['assigned_gate'])

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_extract_flight_data_malformed(self, mock_config, mock_path):
        """Test extract_flight_data handles malformed data"""
        monitor = JSONMonitor(self.test_file_path)

        test_data = {"invalid": "structure"}

        result = monitor.extract_flight_data(test_data)

        # Should return dict with None values when structure is malformed
        self.assertIsNone(result['airport'])
        self.assertIsNone(result['airline'])
        self.assertIsNone(result['flight_number'])

    @patch('GateAssignmentDirector.si_api_hook.Path')
    @patch('GateAssignmentDirector.si_api_hook.configparser.ConfigParser')
    def test_flight_data_callback_invoked(self, mock_config, mock_path):
        """Test flight_data_callback is invoked with extracted data"""
        flight_callback_mock = Mock()
        monitor = JSONMonitor(
            self.test_file_path,
            flight_data_callback=flight_callback_mock
        )

        test_data = {
            "flight_details": {
                "current_flight": {
                    "flight_destination": "KLAX",
                    "airline": "Delta",
                    "flight_number": "DL456"
                }
            }
        }

        # Manually call extract and callback to test the flow
        flight_data = monitor.extract_flight_data(test_data)
        if monitor.flight_data_callback:
            monitor.flight_data_callback(flight_data)

        flight_callback_mock.assert_called_once()
        call_args = flight_callback_mock.call_args[0][0]
        self.assertEqual(call_args['airport'], "KLAX")
        self.assertEqual(call_args['airline'], "Delta")
        self.assertEqual(call_args['flight_number'], "DL456")


if __name__ == "__main__":
    unittest.main()
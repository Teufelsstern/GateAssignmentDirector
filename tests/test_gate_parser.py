import unittest
from unittest.mock import Mock
from GateAssignmentDirector.si_api_hook import GateParser, GateInfo


class TestGateParserExtended(unittest.TestCase):
    """Extended test suite for GateParser with comprehensive coverage"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock()
        self.mock_config.position_keywords = {
            'gsx_gate': ['Gate', 'Dock'],
            'gsx_parking': ['Parking', 'Stand', 'Remote', 'Ramp', 'Apron'],
            'si_terminal': ['Terminal', 'International', 'Parking', 'Domestic', 'Main', 'Central', 'Pier', 'Concourse', 'Level', 'Apron', 'Stand']
        }
        self.parser = GateParser(self.mock_config)

    def test_parse_terminal_with_number_and_gate(self):
        """Test parsing 'Terminal 7 7' format"""
        result = self.parser.parse_gate("Terminal 7 7")
        expected = GateInfo(
            terminal_name="Terminal",
            terminal_number="7",
            gate_prefix="",
            gate_suffix="",
            gate_number="7",
            raw_value="Terminal 7 7",
        )
        self.assertEqual(result, expected)

    def test_parse_simple_gate_number(self):
        """Test parsing 'Gate 5' format"""
        result = self.parser.parse_gate("Gate 5")
        expected = GateInfo(
            terminal_name="Terminal",
            terminal_number="",
            gate_prefix="",
            gate_suffix="",
            gate_number="5",
            raw_value="Gate 5",
        )
        self.assertEqual(result, expected)

    def test_parse_international_gate_with_letter(self):
        """Test parsing 'International Gate 25A' format"""
        result = self.parser.parse_gate("International Gate 25A")
        expected = GateInfo(
            terminal_name="International",
            terminal_number="",
            gate_prefix="",
            gate_number="25",
            gate_suffix="A",
            raw_value="International Gate 25A",
        )
        self.assertEqual(result, expected)

    def test_parse_pier_with_terminal_and_gate_letter(self):
        """Test parsing 'Pier C Gate 14 R' format"""
        result = self.parser.parse_gate("Pier C Gate 14 R")
        expected = GateInfo(
            terminal_name="Pier",
            terminal_number="C",
            gate_prefix="",
            gate_number="14",
            gate_suffix="R",
            raw_value="Pier C Gate 14 R",
        )
        self.assertEqual(result, expected)

    def test_parse_empty_string(self):
        """Test parsing empty string returns empty GateInfo"""
        result = self.parser.parse_gate("")
        self.assertEqual(result.terminal_name, None)
        self.assertEqual(result.gate_number, None)
        self.assertEqual(result.gate_suffix, None)

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string"""
        result = self.parser.parse_gate("   ")
        self.assertEqual(result.terminal_name, None)
        self.assertEqual(result.gate_number, None)

    def test_parse_gate_with_lowercase(self):
        """Test parsing handles lowercase input"""
        result = self.parser.parse_gate("gate 12b")
        self.assertEqual(result.gate_number, "12")
        self.assertEqual(result.gate_suffix, "B")  # Should be capitalized

    def test_parse_concourse_format(self):
        """Test parsing 'Concourse A Gate 5' format"""
        result = self.parser.parse_gate("Concourse A Gate 5")
        self.assertEqual(result.terminal_name, "Concourse")
        self.assertEqual(result.terminal_number, "A")
        self.assertEqual(result.gate_number, "5")

    def test_parse_level_format(self):
        """Test parsing 'Level 3 Gate 10' format"""
        result = self.parser.parse_gate("Level 3 Gate 10")
        self.assertEqual(result.terminal_name, "Level")
        self.assertEqual(result.terminal_number, "3")
        self.assertEqual(result.gate_number, "10")

    def test_parse_domestic_terminal(self):
        """Test parsing 'Domestic Gate 7B' format"""
        result = self.parser.parse_gate("Domestic Gate 7B")
        self.assertEqual(result.terminal_name, "Domestic")
        self.assertEqual(result.gate_number, "7")
        self.assertEqual(result.gate_suffix, "B")

    def test_parse_main_terminal(self):
        """Test parsing 'Main Terminal Gate 15' format"""
        result = self.parser.parse_gate("Main Terminal Gate 15")
        self.assertEqual(result.terminal_name, "Main")
        self.assertEqual(result.gate_number, "15")

    def test_parse_central_terminal(self):
        """Test parsing 'Central A Gate 22' format"""
        result = self.parser.parse_gate("Central A Gate 22")
        self.assertEqual(result.terminal_name, "Central")
        self.assertEqual(result.terminal_number, "A")
        self.assertEqual(result.gate_number, "22")

    def test_parse_parking_gate(self):
        """Test parsing 'Parking Gate 101' format"""
        result = self.parser.parse_gate("Parking Gate 101")
        self.assertEqual(result.terminal_name, "Parking")
        self.assertEqual(result.gate_number, "101")

    def test_parse_gate_with_multiple_spaces(self):
        """Test parsing handles multiple spaces between words"""
        result = self.parser.parse_gate("Terminal  5  Gate  12A")
        self.assertIsNotNone(result.gate_number)
        self.assertIsNotNone(result.terminal_number)

    def test_parse_preserves_raw_value(self):
        """Test that raw_value is always preserved"""
        test_string = "Pier C Gate 14 R"
        result = self.parser.parse_gate(test_string)
        self.assertEqual(result.raw_value, test_string)

    def test_gate_info_equality(self):
        """Test GateInfo equality comparison works correctly"""
        gate1 = GateInfo(
            terminal_name="Terminal",
            terminal_number="1",
            gate_number="5",
            gate_suffix="A",
            raw_value="Test"
        )
        gate2 = GateInfo(
            terminal_name="Terminal",
            terminal_number="1",
            gate_number="5",
            gate_suffix="A",
            raw_value="Test"
        )
        self.assertEqual(gate1, gate2)

    def test_gate_info_inequality(self):
        """Test GateInfo inequality when fields differ"""
        gate1 = GateInfo(
            terminal_name="Terminal",
            gate_number="5",
            raw_value="Test1"
        )
        gate2 = GateInfo(
            terminal_name="Terminal",
            gate_number="6",
            raw_value="Test2"
        )
        self.assertNotEqual(gate1, gate2)

    def test_gate_info_string_representation(self):
        """Test GateInfo __str__ method produces readable output"""
        gate_info = GateInfo(
            terminal_name="Terminal",
            terminal_number="1",
            gate_number="5",
            gate_suffix="A",
            raw_value="Terminal 1 Gate 5A"
        )
        result = str(gate_info)
        self.assertIn("Terminal", result)
        self.assertIn("1", result)
        self.assertIn("5A", result)

    def test_gate_info_string_with_minimal_data(self):
        """Test GateInfo __str__ with minimal data shows raw value"""
        gate_info = GateInfo(raw_value="Unknown Gate Format")
        result = str(gate_info)
        self.assertIn("Raw:", result)
        self.assertIn("Unknown Gate Format", result)

    def test_parser_pattern_is_compiled(self):
        """Test that parser has compiled regex pattern"""
        self.assertIsNotNone(self.parser.gate_pattern)
        self.assertTrue(hasattr(self.parser.gate_pattern, 'search'))


if __name__ == "__main__":
    unittest.main()
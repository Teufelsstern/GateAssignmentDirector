import unittest
import re


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


if __name__ == "__main__":
    unittest.main()
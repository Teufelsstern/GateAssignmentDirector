import unittest
from GateAssignmentDirector.gate_matcher import GateMatcher


class TestGateMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = GateMatcher()

    def test_parse_gate_components_with_prefix_and_number(self):
        """Test parsing gate with letter prefix and number like 'V19'"""
        result = self.matcher.parse_gate_components("V19")
        self.assertEqual(result["gate_number"], "19")
        self.assertEqual(result["gate_prefix"], "V")
        self.assertEqual(result["gate_suffix"], "")

    def test_parse_gate_components_with_suffix(self):
        """Test parsing gate with number and letter suffix like '5A'"""
        result = self.matcher.parse_gate_components("5A")
        self.assertEqual(result["gate_number"], "5")
        self.assertEqual(result["gate_prefix"], "")
        self.assertEqual(result["gate_suffix"], "A")

    def test_parse_gate_components_with_word_prefix(self):
        """Test parsing gate with word prefix like 'Stand 501'"""
        result = self.matcher.parse_gate_components("Stand 501")
        self.assertEqual(result["gate_number"], "501")
        self.assertEqual(result["gate_prefix"], "STAND")
        self.assertEqual(result["gate_suffix"], "")

    def test_parse_gate_components_complex(self):
        """Test parsing complex gate identifier like 'Gate 25B'"""
        result = self.matcher.parse_gate_components("Gate 25B")
        self.assertEqual(result["gate_number"], "25")
        self.assertEqual(result["gate_prefix"], "GATE")
        self.assertEqual(result["gate_suffix"], "B")

    def test_parse_gate_components_only_number(self):
        """Test parsing gate with only number like '19'"""
        result = self.matcher.parse_gate_components("19")
        self.assertEqual(result["gate_number"], "19")
        self.assertEqual(result["gate_prefix"], "")
        self.assertEqual(result["gate_suffix"], "")

    def test_parse_gate_components_empty(self):
        """Test parsing empty string"""
        result = self.matcher.parse_gate_components("")
        self.assertEqual(result["gate_number"], "")
        self.assertEqual(result["gate_prefix"], "")
        self.assertEqual(result["gate_suffix"], "")

    def test_calculate_match_score_exact_match(self):
        """Test score calculation for exact number match"""
        si = {"gate_number": "19", "gate_prefix": "V", "terminal": "apron"}
        gsx = {"gate_number": "19", "gate_prefix": "V", "terminal": "east"}
        score, components = self.matcher.calculate_match_score(si, gsx)

        self.assertEqual(components["gate_number"], 100.0)
        self.assertGreater(score, 80)  # Should be high score

    def test_calculate_match_score_different_numbers(self):
        """Test score calculation when gate numbers differ"""
        si = {"gate_number": "19", "gate_prefix": "V", "terminal": "apron"}
        gsx = {"gate_number": "9", "gate_prefix": "V", "terminal": "apron"}
        score, components = self.matcher.calculate_match_score(si, gsx)

        self.assertLess(components["gate_number"], 100.0)
        self.assertLess(score, 85)  # Should be relatively low score

    def test_calculate_match_score_same_prefix_different_terminal(self):
        """Test that terminal mismatch doesn't kill the score"""
        si = {"gate_number": "19", "gate_prefix": "V", "terminal": "apron west"}
        gsx = {"gate_number": "19", "gate_prefix": "V", "terminal": "east iii"}
        score, components = self.matcher.calculate_match_score(si, gsx)

        # Number and prefix match should still give good score
        self.assertEqual(components["gate_number"], 100.0)
        self.assertGreater(score, 85)

    def test_calculate_match_score_with_suffix(self):
        """Test score calculation with gate suffixes"""
        si = {"gate_number": "5", "gate_prefix": "", "gate_suffix": "A", "terminal": "terminal"}
        gsx = {"gate_number": "5", "gate_prefix": "", "gate_suffix": "A", "terminal": "terminal"}
        score, components = self.matcher.calculate_match_score(si, gsx)

        self.assertGreater(score, 80)  # Should be high (suffix averaged with prefix)

    def test_find_best_match_exact(self):
        """Test finding exact match"""
        airport_data = {
            "terminals": {
                "1": {
                    "5A": {"position_id": "Gate 1-5A", "gate": "5A"}
                }
            }
        }

        result, is_exact, score = self.matcher.find_best_match(airport_data, "1", "5A")

        self.assertTrue(is_exact)
        self.assertEqual(result["position_id"], "Gate 1-5A")
        self.assertEqual(score, 100.0)

    def test_find_best_match_fuzzy(self):
        """Test finding fuzzy match"""
        airport_data = {
            "terminals": {
                "East III": {
                    "V19": {
                        "position_id": "Terminal East III Stand V19",
                        "gate": "V19",
                        "_parsed": {"gate_number": "19", "gate_prefix": "V", "gate_suffix": ""}
                    }
                }
            }
        }

        # SI says "Apron V" + "Spot 19"
        result, is_exact, score = self.matcher.find_best_match(airport_data, "Apron V", "Spot 19")

        self.assertFalse(is_exact)
        self.assertIsNotNone(result)
        self.assertGreater(score, 50)  # Should match reasonably well

    def test_find_best_match_no_match(self):
        """Test that completely different gates don't match well"""
        airport_data = {
            "terminals": {
                "A": {
                    "1": {
                        "position_id": "Gate A1",
                        "gate": "1",
                        "_parsed": {"gate_number": "1", "gate_prefix": "", "gate_suffix": ""}
                    }
                }
            }
        }

        result, is_exact, score = self.matcher.find_best_match(airport_data, "Z", "99")

        self.assertFalse(is_exact)
        # May still return something but with very low score
        self.assertLess(score, 50)


if __name__ == "__main__":
    unittest.main()

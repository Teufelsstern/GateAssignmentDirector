"""Fuzzy gate matching with component-based weighted scoring"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import re
import logging
from typing import Dict, Tuple, Optional, Any
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class GateMatcher:
    """Handles fuzzy matching between SI and GSX gate formats."""

    def __init__(self, config=None):
        """Initialize with optional config for weights."""
        self.config = config
        self.weights = {
            "gate_number": 0.6,
            "gate_prefix": 0.3,
            "terminal": 0.1,
        }
        if config and hasattr(config, 'matching_weights'):
            self.weights.update(config.matching_weights)

    @staticmethod
    def parse_gate_components(gate_id: str) -> Dict[str, str]:
        """Extract searchable components from gate identifier.

        Examples:
            "V19" → {"gate_number": "19", "gate_prefix": "V", "gate_suffix": ""}
            "5A" → {"gate_number": "5", "gate_prefix": "", "gate_suffix": "A"}
            "Stand 501" → {"gate_number": "501", "gate_prefix": "STAND", "gate_suffix": ""}

        Args:
            gate_id: Gate identifier string

        Returns:
            Dict with gate_number, gate_prefix, and gate_suffix components
        """
        gate_id = gate_id.strip()

        # Extract trailing digits and optional letter suffix
        number_match = re.search(r'(\d+)([A-Z])?$', gate_id, re.IGNORECASE)
        if number_match:
            gate_number = number_match.group(1)
            gate_suffix = (number_match.group(2) or "").upper()
        else:
            gate_number = ""
            gate_suffix = ""

        # Everything before number is prefix
        gate_prefix = re.sub(r'\d+[A-Z]?$', '', gate_id, flags=re.IGNORECASE).strip().upper()

        return {
            "gate_number": gate_number,
            "gate_prefix": gate_prefix,
            "gate_suffix": gate_suffix,
        }

    def calculate_match_score(
        self,
        si_parsed: Dict[str, str],
        gsx_parsed: Dict[str, str]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate weighted similarity score between parsed gate components.

        Args:
            si_parsed: Parsed SI gate data (from parse_gate_components + terminal)
            gsx_parsed: Parsed GSX gate data (from parse_gate_components + terminal)

        Returns:
            Tuple of (final_score, component_scores_dict)
        """
        scores = {}

        # Gate number match (exact match for digits is critical)
        si_num = str(int(si_parsed.get("gate_number", "")))
        gsx_num = str(int(gsx_parsed.get("gate_number", "")))
        if si_num and gsx_num:
            scores["gate_number"] = 100.0 if si_num == gsx_num else fuzz.ratio(si_num, gsx_num)
        else:
            scores["gate_number"] = 0.0

        # Gate prefix match (letters/identifiers like "V", "Stand", etc.)
        si_prefix = si_parsed.get("gate_prefix", "")
        gsx_prefix = gsx_parsed.get("gate_prefix", "")
        scores["gate_prefix"] = fuzz.ratio(si_prefix, gsx_prefix) if (si_prefix or gsx_prefix) else 0.0

        # Gate suffix match (A, B, etc.)
        si_suffix = si_parsed.get("gate_suffix", "")
        gsx_suffix = gsx_parsed.get("gate_suffix", "")
        if si_suffix or gsx_suffix:
            suffix_score = 100.0 if si_suffix == gsx_suffix else 0.0
            # Average suffix into prefix score
            scores["gate_prefix"] = (scores["gate_prefix"] + suffix_score) / 2

        # Terminal match (low weight, use token_set_ratio for word order flexibility)
        si_term = si_parsed.get("terminal", "").lower()
        gsx_term = gsx_parsed.get("terminal", "").lower()
        scores["terminal"] = fuzz.token_set_ratio(si_term, gsx_term)

        # Calculate weighted final score
        final_score = (
            scores["gate_number"] * self.weights["gate_number"] +
            scores["gate_prefix"] * self.weights["gate_prefix"] +
            scores["terminal"] * self.weights["terminal"]
        )

        logger.debug(
            f"Match score of {str(gsx_prefix) + str(gsx_num) + str(gsx_suffix)}: "
            f"number={scores['gate_number']:.1f} (SI:{si_num} vs GSX:{gsx_num}) "
            f"prefix={scores['gate_prefix']:.1f} (SI:'{si_prefix}' vs GSX:'{gsx_prefix}') "
            f"terminal={scores['terminal']:.1f} (SI:'{si_term}' vs GSX:'{gsx_term}') "
            f"→ final={final_score:.1f}"
        )

        return final_score, scores

    def find_best_match(
        self,
        airport_data: Dict[str, Any],
        si_terminal: str,
        si_gate: str
    ) -> Tuple[Optional[Dict[str, Any]], bool, float, Optional[Dict[str, float]]]:
        """Find best matching gate using fuzzy matching.

        Args:
            airport_data: Airport data with terminals/gates structure
            si_terminal: SI terminal name
            si_gate: SI gate identifier

        Returns:
            Tuple of (gate_data, is_exact_match, score)
        """
        # Try exact match first
        for key_terminal, dict_terminal in airport_data["terminals"].items():
            for key_gate, dict_gate in dict_terminal.items():
                if key_terminal == si_terminal and key_gate == si_gate:
                    logger.info(f"Exact match found: {key_terminal} {key_gate}")
                    return dict_gate, True, 100.0, None

        # Parse SI input once
        si_parsed = self.parse_gate_components(si_gate)
        si_parsed["terminal"] = si_terminal

        # Fuzzy matching
        best_match = None
        best_score = -1.0  # Initialize to -1 so any score >= 0 will be accepted
        best_components = {}

        for key_terminal, dict_terminal in airport_data["terminals"].items():
            for key_gate, dict_gate in dict_terminal.items():
                # Get pre-parsed GSX data (or parse on-the-fly if not available)
                gsx_parsed = dict_gate.get("_parsed", self.parse_gate_components(key_gate))
                gsx_parsed["terminal"] = key_terminal

                # Calculate weighted score
                score, component_scores = self.calculate_match_score(si_parsed, gsx_parsed)

                if score > best_score:
                    best_score = score
                    best_match = dict_gate
                    best_components = component_scores

        if best_match:
            logger.info(
                f"Best fuzzy match: {best_match.get('position_id', 'unknown')} "
                f"with score {best_score:.1f}% "
                f"(num={best_components.get('gate_number', 0):.0f}, "
                f"prefix={best_components.get('gate_prefix', 0):.0f}, "
                f"term={best_components.get('terminal', 0):.0f})"
            )

        return best_match, False, best_score, best_components

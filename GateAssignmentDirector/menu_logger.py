"""Menu state logging and persistence for GSX Hook - Simplified Version"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from GateAssignmentDirector.gsx_enums import GsxMenuKeywords
from GateAssignmentDirector.gate_matcher import GateMatcher

logger = logging.getLogger(__name__)

MENU_NAVIGATION_OPTIONS = [
    GsxMenuKeywords.NEXT.value,
    GsxMenuKeywords.PREVIOUS.value,
    GsxMenuKeywords.BACK.value,
    GsxMenuKeywords.EXIT.value,
    GsxMenuKeywords.CANCEL.value,
]

GATE_PATTERNS = [
    re.compile(r"Gate\s+([A-Z]?\s*\d+\s*[A-Z]?\b)", re.IGNORECASE),
    re.compile(r"Dock\s+([A-Z]?\s*\d+\s*[A-Z]?\b)", re.IGNORECASE),
    re.compile(r"^([A-Z]?\s*\d+\s*[A-Z]?)$", re.IGNORECASE),
    re.compile(r"^([A-Z]\s*\d+)$", re.IGNORECASE),
]

PARKING_PATTERNS = [
    re.compile(r"(Stand\s+\w+)", re.IGNORECASE),
    re.compile(r"(\w*\s*Parking\s+\w+)", re.IGNORECASE),
    re.compile(r"(Remote\s+\w+)", re.IGNORECASE),
    re.compile(r"(Ramp\s+\w+)", re.IGNORECASE),
]


@dataclass
class GateInfo:
    """Gate assignment information"""

    airport: str
    terminal: Optional[str] = None
    terminal_number: Optional[str] = None
    gate_number: Optional[str] = None
    gate_letter: Optional[str] = None
    airline: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class MenuLogger:
    """Maps and persists GSX menu structure for airports"""

    def __init__(self, config, logs_dir: str = "gsx_menu_logs") -> None:
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)

        self.current_airport: Optional[str] = None
        self.current_depth: int = 0
        self.navigation_path: List[str] = []
        self.config = config
        self.gate_matcher = GateMatcher(config)

        logging.basicConfig(
            level=config.logging_level,
            format=config.logging_format,
            datefmt=config.logging_datefmt,
        )

        self.menu_map: Dict[str, Any] = {
            "version": "1",
            "airport": None,
            "created": None,
            "available_gates": {},
            "available_spots": {},
        }

        self.seen_menus: Set[Tuple[str, ...]] = set()

    def start_session(self, gate_info: GateInfo) -> None:
        """Start a new mapping session for an airport"""
        self.current_airport = gate_info.airport
        self.menu_map["airport"] = gate_info.airport
        self.menu_map["created"] = datetime.now().isoformat()
        self.navigation_path = []
        self.seen_menus = set()

        logger.info(f"Started menu mapping for {gate_info.airport}")

    def log_menu_state(
        self,
        title: str,
        options: List[str],
        selected_index: Optional[int] = None,
        menu_depth: Optional[int] = None,
        navigation_info: Optional[Dict] = None,
    ) -> None:
        """Log the current menu state into our map"""

        if title == "Select airport":
            logger.debug("Skipped logging - No airport selected yet.")
            return

        menu_signature = (title, tuple(options))

        if menu_signature not in self.seen_menus:
            self.seen_menus.add(menu_signature)
            self._extract_gates_and_spots(options, title, navigation_info)

        if selected_index is not None and selected_index < len(options):
            selected_option = options[selected_index]
            if selected_option not in MENU_NAVIGATION_OPTIONS:
                logger.debug(
                    f"Selected: {selected_option} at depth {self.current_depth}"
                )

    def save_session(self) -> str:
        """Save the menu map to file"""
        if not self.current_airport:
            logger.warning("No airport set, cannot save")
            return ""

        filename = f"{self.current_airport}.json"
        filepath = self.logs_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.menu_map, f, indent=2)
        logger.info(f"Saved menu map to {filepath}")
        logger.info(f"  Found {len(self.menu_map['available_gates'])} gates")
        logger.info(f"  Found {len(self.menu_map['available_spots'])} other spots")
        return str(filepath)

    def load_airport_map(self, airport_icao: str) -> Optional[Dict]:
        """Load the menu map for a specific airport"""
        filepath = self.logs_dir / f"{airport_icao}.json"
        if not filepath.exists():
            logger.warning(f"No map file found for {airport_icao}")
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded menu map for {airport_icao}")
            return data
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load map for {airport_icao}: {e}")
            return None

    def _extract_gates_and_spots(
        self,
        options: List[str],
        menu_title: str,
        navigation_info: Optional[Dict] = None,
    ) -> None:
        """Extract gate and spot information from menu options"""
        spot_type = "gates"
        patterns = None

        for keyword in self.config.position_keywords['gsx_gate']:
            if keyword in menu_title:
                patterns = GATE_PATTERNS
                spot_type = "gates"
                break

        if not patterns:
            for keyword in self.config.position_keywords['gsx_parking']:
                if keyword in menu_title:
                    patterns = PARKING_PATTERNS
                    spot_type = "spots"
                    break

        if not patterns:
            return

        for index, option in enumerate(options):
            if option in MENU_NAVIGATION_OPTIONS:
                continue
            for pattern in patterns:
                match = pattern.search(option)
                if match:
                    spot_id = match.group(1)
                    if spot_id not in self.menu_map["available_gates"]:
                        spot_data = {
                            "full_text": option,
                            "menu_index": index,
                            "found_in_menu": menu_title,
                            "depth": self.current_depth,
                            "_parsed": self.gate_matcher.parse_gate_components(spot_id),
                        }

                        if navigation_info:
                            spot_data["level_0_page"] = navigation_info.get("level_0_page")
                            spot_data["level_0_option_index"] = navigation_info.get("level_0_option_index")
                            spot_data["level_1_next_clicks"] = navigation_info.get("level_1_next_clicks")

                        self.menu_map[f"available_{spot_type}"][spot_id] = spot_data
                    break

    def create_interpreted_airport_data(self, airport_icao: str) -> bool:
        """Create interpreted airport data"""
        # Load raw data
        raw_data = self.load_airport_map(airport_icao)
        if not raw_data:
            return False
        interpreted_data = {
            "version": "1",
            "airport": airport_icao,
            "created": datetime.now().isoformat(),
            "terminals": {},
        }

        # Process gates
        for gate_id, gate_info in raw_data.get("available_gates", {}).items():
            result = self._interpret_position(gate_id, gate_info, "gate")
            self._add_to_terminals(interpreted_data, result)

        # Process parking spots
        for spot_id, spot_info in raw_data.get("available_spots", {}).items():
            result = self._interpret_position(spot_id, spot_info, "parking")
            self._add_to_terminals(interpreted_data, result)

        filepath = self.logs_dir / f"{airport_icao}_interpreted.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(interpreted_data, f, indent=2)

        logger.info(f"Saved interpreted data to {filepath}")
        return True

    def _extract_terminal_from_menu(self, menu_title: str) -> str:
        """
        Extract terminal/area name from menu title.
        Examples:
        - "Terminal - A-Pier (A1-A16)" → "A-Pier" (preferred)
        - "Apron - West I (V61-V76)" → "West I" (preferred)
        - "All Gate positions" (no specific name) → "Terminal 1" (fallback for gates)
        - "All Parking positions" (no specific name) → "Parking" (fallback for parking)
        """
        # Pattern: <Type> - <Specific Name> (<Range>)
        match = re.search(r'(Terminal|Apron|Gate|Parking)\s*-\s*([^(]+)', menu_title, re.IGNORECASE)
        if match:
            specific_name = match.group(2).strip()

            # If specific name exists and looks reasonable (not empty, not too weird)
            if specific_name and len(specific_name) > 0 and len(specific_name) < 50:
                return specific_name
        else:
            # Try "All X Positions" pattern (e.g., "All Gate A Positions")
            match = re.search(r'All (Gate|Ramp|Stand)\s*([A-Za-z0-9]?) Positions', menu_title, re.IGNORECASE)
            if match:
                extracted = match.group(2) or ""
                # Only return if we got something meaningful, otherwise continue to fallback
                if extracted:
                    return extracted

        # No specific terminal name found, check if menu is about parking using config keywords
        for keyword in self.config.position_keywords.get('gsx_parking', []):
            if keyword.lower() in menu_title.lower():
                return "Parking"

        # Default fallback for gates/terminals
        return "Terminal 1"

    def _extract_gate_identifier(self, position_id: str) -> str:
        """
        Extract gate/stand identifier, removing known keywords.
        Examples:
        - "Stand V20" → "V20"
        - "Gate 11B" → "11B"
        - "A16" → "A16"
        """
        # Remove known keywords from config
        clean_id = position_id
        for keyword in self.config.position_keywords.get('gsx_gate', []) + \
                       self.config.position_keywords.get('gsx_parking', []):
            clean_id = re.sub(rf'\b{keyword}\b\s*', '', clean_id, flags=re.IGNORECASE)

        return clean_id.strip()

    def _infer_terminal_from_gate(self, gate_id: str, position_type: str) -> Optional[str]:
        """
        Infer terminal from gate identifier using heuristic rules.
        This is used as fallback when menu title doesn't provide specific terminal info.

        Examples:
            "V19" → "V" (letter prefix becomes terminal)
            "52H" → "5" (first digit becomes terminal)
            "101" → "Parking" (3 digits, parking type)
            "205" → "Miscellaneous" (3 digits, gate type, no prefix)
            "K205" → "K" (3 digits with prefix)

        Args:
            gate_id: Clean gate identifier (e.g., "V19", "52H", "5A")
            position_type: "gate" or "parking"

        Returns:
            Inferred terminal or None if unable to infer
        """
        gate_id_no_spaces = gate_id.replace(" ", "")

        # Parse gate components
        pattern = re.compile(
            r"""
                ([A-Z]+)?       # Optional letter prefix (group 1)
                (\d+)?          # Optional digits (group 2)
                ([A-Z]\b)?      # Optional letter suffix (group 3)
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        match = pattern.search(gate_id_no_spaces)
        if not match:
            return None

        letter_prefix = (match.group(1) or "").upper()
        digits = match.group(2) or ""
        letter_suffix = (match.group(3) or "").upper()

        # Gate letters that are typically suffixes, not terminals
        gate_suffix_letters = ["A", "B", "L", "R", "C"]

        # Start with first digit as default terminal
        assumed_terminal = digits[0] if digits else None

        # Letter prefix logic
        if letter_prefix and letter_prefix not in gate_suffix_letters:
            # Non-gate-suffix letter becomes terminal (e.g., "V19" → terminal="V")
            assumed_terminal = letter_prefix
        elif letter_prefix in gate_suffix_letters and not letter_suffix:
            # Gate suffix letter with no trailing letter (e.g., "A16" could be terminal)
            if digits and len(digits) == 1:
                # Too short to be terminal+gate, assume it's generic
                assumed_terminal = "Terminal"
            # Otherwise use first digit as terminal

        # Handle special digit length cases
        if digits and assumed_terminal == digits[0]:
            if len(digits) == 3 and position_type == "parking":
                # Three-digit parking spots are typically in "Parking" terminal (e.g., "101")
                assumed_terminal = "Parking"
            elif len(digits) == 3 and position_type == "gate":
                # Three-digit gates without letter prefix go to "Miscellaneous" (e.g., "205")
                # Those with letter prefix already have assumed_terminal set above
                if not letter_prefix:
                    assumed_terminal = "Miscellaneous"
                # Otherwise keep the prefix as terminal (e.g., "K205" → "K")
            elif len(digits) == 1:
                # Single digit positions default to terminal "1"
                assumed_terminal = "1"

        return assumed_terminal

    def _interpret_position(
        self, position_id: str, position_info: Dict, position_type: str
    ) -> Dict:
        """
        Parse position using menu structure.

        Available data:
        - position_id: "Stand V20", "Gate 11B", etc. (WITH spaces)
        - position_info["full_text"]: "Stand V20 - Ramp GA Medium"
        - position_info["found_in_menu"]: "Apron - East I (V11-V29)"
        - position_type: "gate" or "parking"
        """
        menu_title = position_info.get("found_in_menu", "")

        # Extract gate identifier first (needed for fallback)
        gate = self._extract_gate_identifier(position_id)

        # Extract terminal from menu title
        terminal = self._extract_terminal_from_menu(menu_title)

        # If we got a generic fallback or empty terminal, use gate identifier heuristic
        if terminal in ["Terminal 1", "Parking", "1", ""]:
            inferred = self._infer_terminal_from_gate(gate, position_type)
            if inferred:
                logger.debug(
                    f"Generic menu fallback '{terminal}' overridden with inferred terminal '{inferred}' from gate '{gate}'"
                )
                terminal = inferred

        # Use appropriate label based on position type
        position_label = "Stand" if position_type == "parking" else "Gate"

        # Build position_id - avoid duplicating "Terminal" or adding it to "Parking"
        if terminal == "Parking":
            # Parking is a valid terminal name, use it as-is
            position_id = f"{terminal} {position_label} {gate}"
        elif terminal.startswith("Terminal"):
            position_id = f"{terminal} {position_label} {gate}"
        else:
            position_id = f"Terminal {terminal} {position_label} {gate}"

        return {
            "terminal": terminal,
            "gate": gate,
            "position_id": position_id,
            "type": position_type,
            "raw_info": position_info,
        }

    def _add_to_terminals(self, interpreted_data: Dict, result: Dict) -> None:
        """Add position to terminal structure"""
        terminal = result["terminal"]
        interpreted_data["terminals"].setdefault(terminal, {})[result["gate"]] = result

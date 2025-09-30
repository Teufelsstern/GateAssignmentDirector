"""Menu state logging and persistence for GSX Hook - Simplified Version"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GateInfo:
    """Gate assignment information"""

    airport: str  # ICAO code"
    terminal: Optional[str] = None
    terminal_number: Optional[str] = None
    gate_number: Optional[str] = None
    gate_letter: Optional[str] = None
    airline: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class MenuLogger:
    """Maps and persists GSX menu structure for airports"""

    def __init__(self, config, logs_dir: str = "gsx_menu_logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)

        # Current mapping session
        self.current_airport: Optional[str] = None
        self.current_depth: int = 0
        self.navigation_path: List[str] = []
        self.config = config

        logging.basicConfig(
            level=config.logging_level,
            format=config.logging_format,
            datefmt=config.logging_datefmt,
        )

        # The actual menu map we're building
        self.menu_map: Dict[str, Any] = {
            "airport": None,
            "last_updated": None,
            #"menu_structure": {},
            "available_gates": {},  # Will store all gates found
            "available_spots": {},  # Parking spots, remote stands, etc.
            #"all_menus_by_depth": {},  # Quick lookup by depth level
        }

        # Track what we've seen to avoid duplicates
        self.seen_menus: Set[str] = set()

    def start_session(self, gate_info: GateInfo):
        """Start a new mapping session for an airport"""
        self.current_airport = gate_info.airport
        self.menu_map["airport"] = gate_info.airport
        self.menu_map["last_updated"] = datetime.now().isoformat()
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
    ):
        """Log the current menu state into our map"""

        # Skip if we're not at an airport yet
        if title == "Select airport":
            logger.debug("Skipped logging - No airport selected yet.")
            return

        # Create unique menu identifier that includes a hash of the options
        # This ensures different pages with same title are treated as unique
        import hashlib

        options_hash = hashlib.md5("|".join(options).encode()).hexdigest()[:8]
        menu_id = f"depth_{self.current_depth}_{title}_{options_hash}"

        # Only process if we haven't seen this exact menu before
        if menu_id not in self.seen_menus:
            self.seen_menus.add(menu_id)

            # Store menu in structure with unique key
            menu_data = {
                "title": title,
                "depth": menu_depth if menu_depth is not None else self.current_depth,
                "options": {i: opt for i, opt in enumerate(options)},
                "navigation_path": self.navigation_path.copy(),
                "has_next": any("Next" in opt for opt in options),
                "has_previous": any(
                    "Previous" in opt or "Back" in opt for opt in options
                ),
                "options_hash": options_hash,  # Store hash for reference
                "navigation_info": navigation_info,  # Store navigation info
            }

            # Extract gates and spots from options
            self._extract_gates_and_spots(options, title, navigation_info)

        # Update navigation path when moving deeper
        if selected_index is not None and selected_index < len(options):
            selected_option = options[selected_index]
            if selected_option not in ["Next", "Previous", "Back"]:
                logger.debug(
                    f"Selected: {selected_option} at depth {self.current_depth}"
                )

    def save_session(self) -> str:
        """Save the menu map to file"""
        if not self.current_airport:
            logger.warning("No airport set, cannot save")
            return ""

        # Create airport-specific file
        filename = f"{self.current_airport}.json"
        filepath = self.logs_dir / filename

        # Only save if we have new data and it's different from existing
        with open(filepath, "w") as f:
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
            with open(filepath, "r") as f:
                data = json.load(f)
            logger.info(f"Loaded menu map for {airport_icao}")
            return data
        except Exception as e:
            logger.error(f"Failed to load map for {airport_icao}: {e}")
            return None

    def _extract_gates_and_spots(
        self,
        options: List[str],
        menu_title: str,
        navigation_info: Optional[Dict] = None,
    ):
        """Extract gate and spot information from menu options"""
        gate_patterns = [
            r"Gate\s+([A-Z]?\s*\d+\s*[A-Z]?)",
            r"^([A-Z]?\s*\d+\s*[A-Z]?)$",
            r"^([A-Z]\s*\d+)$",
        ]
        parking_patterns = [
            #r"Gate\s+([A-Z]?\s*\d+\s*[A-Z]?)",
            r"(Stand\s+\w+)",
            r"(\w*\s*Parking\s+\w+)",
            r"(Remote\s+\w+)",
            r"(Ramp\s+\w+)",
        ]
        spot_type = "gates"
        if "Gate" in menu_title:
            patterns = gate_patterns
        elif "Parking" in menu_title:
            patterns = parking_patterns
            spot_type = "spots"
        else:
            return

        for index, option in enumerate(options):
            # Skip navigation options
            if option in ["Next", "Previous", "Back", "Exit", "Cancel"]:
                continue
            for pattern in patterns:
                match = re.search(pattern, option, re.IGNORECASE)
                if match:
                    spot_id = match.group(1)
                    if spot_id not in self.menu_map["available_gates"]:
                        spot_data = {
                            "full_text": option,
                            "menu_index": index,
                            "found_in_menu": menu_title,
                            "depth": self.current_depth,
                        }

                        # Add navigation info if available
                        if navigation_info:
                            spot_data["level_0_index"] = navigation_info.get(
                                "level_0_index"
                            )
                            spot_data["next_clicks"] = navigation_info.get(
                                "next_clicks"
                            )

                        self.menu_map[f"available_{spot_type}"][spot_id] = spot_data
                    break

    def create_interpreted_airport_data(self, airport_icao: str) -> bool:
        """Create interpreted airport data"""
        # Load raw data
        raw_data = self.load_airport_map(airport_icao)
        if not raw_data:
            return False
        interpreted_data = {
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

        # Save
        filepath = self.logs_dir / f"{airport_icao}_interpreted.json"
        with open(filepath, "w") as f:
            json.dump(interpreted_data, f, indent=2)

        logger.info(f"Saved interpreted data to {filepath}")
        return True

    def _interpret_position(
        self, position_id: str, position_info: Dict, position_type: str
    ) -> Dict:
        """
        Asobo and GSX may put all Terminal Gates into parking. We assume that the first number of each parking
        spot is actually the Terminal and the digits after that are the gate. We clean up the full_text to provide size.
        The Terminals will be both "A" and "1" respectively in their parsing.

        Available data:
        - position_id: "11B", "Parking 1" etc.
        - position_info["full_text"]: "Gate 11B - Small - 1x /J (too small)"
        - position_info["level_0_index"]: Which button to click
        - position_info["next_clicks"]: How many Next clicks
        - position_type: "gate" or "parking"
        """
        position_id_s = position_id.replace(" ", "")
        assumed_terminal = "30"
        pattern_test = re.compile(
            r"""
                (Gate|Parking)?
                ([A-Z]+)?
                (\d+)?
                ([A-Z]+)?
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        gate_letters = ["A", "B", "L", "R", "C"]
        match = pattern_test.search(position_id_s)
        spot_type = match.group(1) if match.group(1) is not None else ""
        number_prefix = match.group(2) if match.group(2) is not None else ""
        number = match.group(3) if match.group(3) is not None else "-1"
        number_suffix = match.group(4) if match.group(4) is not None else ""


        assumed_gate = number + number_suffix # We just have to trust that the suffix is actually viable, otherwise we lose information
        assumed_terminal = number[0] # First number of the gate is the default terminal
        if number_prefix != "" and number_prefix not in gate_letters: # Gate Z52H (special), Gate A42B (ignore)
            assumed_terminal = number_prefix
        elif number_prefix != "" and number_prefix in gate_letters: #ignore the prefix if suffix present, probably GSX-misc
            if len(number) == 1: # too short to also be a terminal
                assumed_terminal = "Terminal"
            elif number_suffix == "": # move prefix to the back
                assumed_gate = number + number_prefix
        elif assumed_terminal == number[0]: # one or three digits aren't normal gates, see if overwritten with special terminal
            if len(number) == 3:
                assumed_terminal = "Parking"
            elif len(number) == 1:
                assumed_terminal = "1"

        return {
            "terminal": assumed_terminal,
            "gate": assumed_gate,
            "position_id": f"Terminal {assumed_terminal} Gate {assumed_gate}",
            "type": position_type,
            "raw_info": position_info,
        }

    def _add_to_terminals(self, interpreted_data: Dict, result: Dict):
        """Add position to terminal structure"""
        terminal = result["terminal"]
        if terminal not in interpreted_data["terminals"]:
            interpreted_data["terminals"][terminal] = {}
        interpreted_data["terminals"][terminal][
            result["gate"]
        ] = result

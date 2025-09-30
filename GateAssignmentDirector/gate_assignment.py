"""Gate assignment automation with logging"""

import os
import time
import logging
import json
from typing import Optional, Dict, Any, Tuple
from rapidfuzz import fuzz
import requests

from GateAssignmentDirector.exceptions import GsxMenuError, GsxTimeoutError
from GateAssignmentDirector.gsx_enums import SearchType, GsxVariable
from GateAssignmentDirector.menu_logger import GateInfo

logger = logging.getLogger(__name__)


class GateAssignment:
    """Handles automated gate assignment process with logging"""

    def __init__(self, config, menu_logger, menu_reader, menu_navigator, sim_manager) -> None:
        self.menu_navigator = menu_navigator
        self.sim_manager = sim_manager
        self.config = config
        self.menu_logger = menu_logger
        self.menu_reader = menu_reader

        logging.basicConfig(
            level=config.logging_level,
            format=config.logging_format,
            datefmt=config.logging_datefmt,
        )

    def map_available_spots(self, airport: str) -> Dict[str, Any]:
        """We map every available parking spot for the airport"""
        file1 = f".\\gsx_menu_logs\\{airport}.json"
        file2 = f".\\gsx_menu_logs\\{airport}_interpreted.json"
        logger.debug(f"Current directory: {os.getcwd()}")
        logger.debug(f"Looking for file: {file1}")
        logger.debug(f"Absolute path: {os.path.abspath(file1)}")
        logger.debug(f"File exists: {os.path.exists(file1)}")
        if not os.path.exists(file1) and not os.path.exists(file2):
            self.menu_logger.start_session(gate_info=GateInfo(airport=airport))
            level_0_index = 0
            self._open_menu()
            current_menu_state = self.menu_reader.read_menu()
            max_index = len(current_menu_state.options) + 1
            logger.debug("Found %s options at current menu and setting maximum to %s", max_index - 1, max_index)
            while level_0_index <= max_index:
                next_clicks = 0

                self._open_menu()
                current_menu_state = self.menu_reader.read_menu()

                navigation_info = {
                    "level_0_index": level_0_index,
                    "next_clicks": next_clicks,
                }

                self.menu_logger.log_menu_state(
                    title=current_menu_state.title,
                    options=current_menu_state.options,
                    menu_depth=0,
                    navigation_info=navigation_info,
                )

                self.menu_navigator.click_by_index(level_0_index)

                while True:
                    current_menu_state = self.menu_reader.read_menu()

                    navigation_info = {
                        "level_0_index": level_0_index,
                        "next_clicks": next_clicks,
                    }

                    self.menu_logger.log_menu_state(
                        title=current_menu_state.title,
                        options=current_menu_state.options,
                        menu_depth=1,
                        navigation_info=navigation_info,
                    )

                    if any("Next" in opt for opt in current_menu_state.options):
                        logger.debug(
                            f"Clicking Next button (click #{next_clicks + 1}) for level_0_index {level_0_index}"
                        )
                        self.menu_navigator.click_next()
                        next_clicks += 1
                    else:
                        logger.debug(
                            f"No more Next button found for level_0_index {level_0_index}. Total Next clicks: {next_clicks}"
                        )
                        break

                level_0_index += 1
            self.menu_logger.save_session()
        if not os.path.exists(file2):
            self.menu_logger.create_interpreted_airport_data(airport)
        with open(file2, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def assign_gate(
        self,
        airport: str,
        terminal: str = "",
        terminal_number: str = "",
        gate_letter: Optional[str] = None,
        gate_number: str = "",
        airline: str = "GSX",
        wait_for_ground: bool = True,
    ) -> bool:
        """
        Complete gate assignment workflow with logging

        Args:
            airport: ICAO code of the airport (e.g., "KLAX")
            terminal: Terminal identifier
            terminal_number: Terminal number (if applicable)
            gate_letter: Gate letter (e.g., "B")
            gate_number: Gate number (e.g., 102)
            airline: Airline code (e.g., "United_2000")
            wait_for_ground: Wait for aircraft on ground

        Returns:
            bool: Success status
        """
        airport_data = self.map_available_spots(airport)
        matching_gsx_gate, direct_match = self.find_gate(
            airport_data,
            (terminal or "") + (terminal_number or ""),
            (gate_number or "") + (gate_letter or "")
        )
        if direct_match is False:
            response = requests.get("https://apipri.sayintentions.ai/sapi/assignGate",
                                    params={"api_key": self.config.SI_API_KEY, "gate": matching_gsx_gate["gate"], "airport": airport})
            if response.status_code != 200:
                logger.error("Error connecting to API.")
            else:
                logger.info("Requested matching gate, assuming it has been set for now.")
        try:
            if wait_for_ground:
                self._wait_for_ground()
            elif not self.sim_manager.is_on_ground():
                logger.warning("Aircraft not on ground - GSX may fail")

            self._open_menu()

            self.menu_navigator.click_planned(matching_gsx_gate)
            self.menu_navigator.find_and_click(["activate"], SearchType.KEYWORD)
            self.menu_navigator.find_and_click([self.config.default_airline or "GSX"], SearchType.AIRLINE)
            logger.info("Gate assignment completed successfully")
            return True

        except (GsxMenuError, GsxTimeoutError, OSError, IOError) as e:
            logger.error(f"Gate assignment failed: {e}")
            return False

    def _wait_for_ground(self) -> None:
        """Wait indefinitely for aircraft to be on ground"""
        logger.info("Waiting for aircraft on ground...")

        while True:
            on_ground = self.sim_manager.is_on_ground()
            if on_ground:
                logger.info("Aircraft on ground - proceeding")
                return
            time.sleep(1)

    def _open_menu(self) -> None:
        """Open GSX menu"""
        self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 1)
        time.sleep(0.1)
        self.sim_manager.set_variable(GsxVariable.MENU_CHOICE.value, -2)
        time.sleep(0.1)

    def find_gate(self, airport_data: Dict[str, Any], terminal: str, gate: str) -> Tuple[Optional[Dict[str, Any]], bool]:
        for key_terminal, dict_terminal in airport_data["terminals"].items():
            for key_gate, dict_gate in dict_terminal.items():
                if key_terminal == terminal and key_gate == gate:
                    return dict_gate, True

        best_match = None
        best_score = 0

        for key_terminal, dict_terminal in airport_data["terminals"].items():
            for key_gate, dict_gate in dict_terminal.items():
                score = fuzz.ratio(key_terminal + key_gate, terminal + gate)
                logger.debug("Looking for Terminal %s Gate %s. Terminal %s and Gate %s reached score of %s", terminal, gate, key_terminal, key_gate, score)
                if score >= best_score:
                    best_score = score
                    best_match = dict_gate

        if best_match:
            logger.debug("Chose best match %s with Score %s", best_match['position_id'], best_score)
        else:
            logger.warning("No gate match found for Terminal %s Gate %s", terminal, gate)

        return best_match, False
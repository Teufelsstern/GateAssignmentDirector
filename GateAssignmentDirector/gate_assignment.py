"""Gate assignment automation with logging"""

import os
import time
import logging
import json
from typing import Optional
from rapidfuzz import fuzz
import requests

from GateAssignmentDirector.exceptions import GsxMenuError, GsxTimeoutError
from GateAssignmentDirector.gsx_enums import SearchType, GsxVariable
from GateAssignmentDirector.menu_logger import GateInfo

logger = logging.getLogger(__name__)


class GateAssignment:
    """Handles automated gate assignment process with logging"""

    def __init__(self, config, menu_logger, menu_reader, menu_navigator, sim_manager):
        self.menu_navigator = menu_navigator
        self.sim_manager = sim_manager
        self.config = config
        self.menu_logger = menu_logger
        self.menu_reader = menu_reader
        self.all_gates = []

        logging.basicConfig(
            level=config.logging_level,
            format=config.logging_format,
            datefmt=config.logging_datefmt,
        )

    def map_available_spots(self, airport: str):
        """We map every available parking spot for the airport"""
        file1 = f".\\gsx_menu_logs\\{airport}.json"
        file2 = f".\\gsx_menu_logs\\{airport}_interpreted.json"
        print(f"Aktuelles Verzeichnis: {os.getcwd()}")
        print(f"Suche Datei: {file1}")
        print(f"Absoluter Pfad: {os.path.abspath(file1)}")
        print(f"Datei existiert: {os.path.exists(file1)}")
        if not os.path.exists(file1) and not os.path.exists(file2):
            self.menu_logger.start_session(gate_info=GateInfo(airport=airport))
            level_0_index = 0
            self._open_menu()
            current_menu_state = self.menu_reader.read_menu()
            max_index = len(current_menu_state.options) + 1
            logger.debug("Found %s options at current menu and setting maximum to %s", max_index - 1, max_index)
            while level_0_index <= max_index:
                next_clicks = 0  # Reset Next clicks counter for each level 0 option

                self._open_menu()
                current_menu_state = self.menu_reader.read_menu()

                # Log level 0 menu with navigation info
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

                # Click the level 0 option
                self.menu_navigator.click_by_index(level_0_index)

                # Navigate through all pages with Next button
                while True:
                    current_menu_state = self.menu_reader.read_menu()

                    # Update navigation info for this submenu
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

                    # Check if Next button is available
                    if any("Next" in opt for opt in current_menu_state.options):
                        logger.debug(
                            f"Clicking Next button (click #{next_clicks + 1}) for level_0_index {level_0_index}"
                        )
                        self.menu_navigator.click_next()
                        next_clicks += 1  # Increment Next clicks counter
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
        ground_timeout: int = None,
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
            ground_timeout: Timeout in seconds

        Returns:
            bool: Success status
        """
        ground_timeout = ground_timeout or self.config.ground_timeout_default

        airport_data = self.map_available_spots(airport)
        matching_gsx_gate, direct_match = self.find_gate(airport_data, terminal + terminal_number, gate_number + gate_letter)
        if direct_match is False:
            response = requests.get("https://apipri.sayintentions.ai/sapi/assignGate",
                                    params={"api_key": self.config.SI_API_KEY, "gate": matching_gsx_gate["gate"], "airport": airport})
            if response.status_code != 200:
                logger.error("Error connecting to API.")
            else:
                logger.info("Requested matching gate, assuming it has been set for now.")
        try:
            # Wait for ground if needed
            if wait_for_ground:
                if not self._wait_for_ground(ground_timeout):
                    if self.menu_logger:
                        self.menu_logger.save_session()
                    return False
            elif not self.sim_manager.is_on_ground():
                logger.warning("Aircraft not on ground - GSX may fail")

            # Open GSX menu
            self._open_menu()

            self.menu_navigator.click_planned(matching_gsx_gate)
            self.menu_navigator.find_and_click(["activate"], SearchType.KEYWORD)
            try:
                self.menu_navigator.find_and_click(["(UA_2000)"], SearchType.AIRLINE)
            except GsxMenuError as e:
                logger.debug("GSX didn't want to show operators today: %s", e)
            logger.info("Gate assignment completed successfully")
            return True

        except Exception as e:
            logger.error(f"Gate assignment failed: {e}")
            return False

    def _wait_for_ground(self, timeout: int) -> bool:
        """Wait for aircraft to be on ground"""
        logger.info("Waiting for aircraft on ground...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            on_ground = self.sim_manager.is_on_ground()
            if on_ground:
                logger.info("Aircraft on ground - proceeding")
                return True
            time.sleep(1)

        logger.warning(f"Timeout after {timeout}s waiting for ground")
        return False

    def _open_menu(self):
        """Open GSX menu"""
        self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 1)
        time.sleep(0.1)
        self.sim_manager.set_variable(GsxVariable.MENU_CHOICE.value, -2)
        time.sleep(0.1)

    def find_gate(self, airport_data, terminal, gate):
        for key_terminal, dict_terminal in airport_data["terminals"].items():
            for key_gate, dict_gate in dict_terminal.items():
                if key_terminal == terminal and key_gate == gate:
                    return dict_gate, True

        # 2. Fuzzy Suche
        best_match = None
        best_score = 33

        for key_terminal, dict_terminal in airport_data["terminals"].items():
            for key_gate, dict_gate in dict_terminal.items():
                score = fuzz.ratio(key_terminal + key_gate, terminal + gate)
                logger.debug("Looking for Terminal %s Gate %s. Terminal %s and Gate %s reached score of %s", terminal, gate, key_terminal, key_gate, score)
                if score > best_score:  # Mindest-Ähnlichkeit
                    best_score = score
                    best_match = dict_gate
        logger.debug("Chose best match %s with Score %s", best_match['position_id'], best_score)
        return best_match, False
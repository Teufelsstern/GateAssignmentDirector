"""Gate assignment automation with logging"""

# Licensed under GPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import os
import time
import logging
import json
import re
from typing import Optional, Dict, Any, Tuple
from rapidfuzz import fuzz
import requests

from GateAssignmentDirector.exceptions import (
    GsxMenuError,
    GsxTimeoutError,
    GsxMenuNotChangedError,
)
from GateAssignmentDirector.gsx_enums import SearchType, GsxVariable
from GateAssignmentDirector.menu_logger import GateInfo

logger = logging.getLogger(__name__)


class GateAssignment:
    """Handles automated gate assignment process with logging"""

    def __init__(
        self, config, menu_logger, menu_reader, menu_navigator, sim_manager
    ) -> None:
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
        _debug1_1 = os.path.abspath(file1)
        _debug1_2 = os.path.exists(file1)
        _debug2_1 = os.path.abspath(file2)
        _debug2_2 = os.path.exists(file2)
        logger.debug("Looking for %s at %s. Exists: %s", file1, _debug1_1, _debug1_2)
        logger.debug("Looking for %s at %s. Exists: %s", file2, _debug2_1, _debug2_2)
        if not os.path.exists(file1) and not os.path.exists(file2):
            logger.debug("Airport %s has not been parsed yet. Starting parsing", airport)
            self.menu_logger.start_session(gate_info=GateInfo(airport=airport))
            self._refresh_menu()
            level_0_page = 0
            current_menu_state = self.menu_reader.read_menu()
            if not current_menu_state.options:
                logger.error(f"Menu is empty for {airport}, cannot map parking spots")
                raise GsxMenuError(f"GSX menu returned no options for {airport}")
            icao_pattern = re.compile(r"\b([A-Z]{4})\b")
            icao_match = icao_pattern.search(current_menu_state.title)
            if icao_match:
                menu_icao = icao_match.group(1)
                if menu_icao != airport:
                    raise GsxMenuError(
                        f"ICAO mismatch: Expected {airport}, but GSX menu shows {menu_icao}"
                    )
                logger.info(
                    f"ICAO verified: {menu_icao} matches expected airport {airport}"
                )
            else:
                logger.warning(
                    f"Could not parse ICAO from menu title: '{current_menu_state.title}'"
                )
            while True:
                current_menu_state = self.menu_reader.read_menu()
                level_0_options = [
                    opt for opt in current_menu_state.options if ("Next" not in opt and "Runway" not in opt)
                ]
                logger.debug(
                    f"Found {len(level_0_options)} options on page {level_0_page}"
                )
                time.sleep(self.config.sleep_short)
                for level_0_option_index, option in enumerate(level_0_options):
                    level_1_next_clicks = 0
                    current_menu_state = self.menu_reader.read_menu()
                    if "Previous" in option[1:].split():
                        continue
                    navigation_info = {
                        "level_0_page": level_0_page,
                        "level_0_option_index": level_0_option_index,
                        "level_1_next_clicks": level_1_next_clicks,
                    }
                    self.menu_logger.log_menu_state(
                        title=current_menu_state.title,
                        options=current_menu_state.options,
                        menu_depth=0,
                        navigation_info=navigation_info,
                    )
                    self.menu_navigator.click_by_index(level_0_option_index)
                    logger.debug("Clicked on level_0 option %s", option)
                    while True:
                        current_menu_state = self.menu_reader.read_menu()
                        navigation_info = {
                            "level_0_page": level_0_page,
                            "level_0_option_index": level_0_option_index,
                            "level_1_next_clicks": level_1_next_clicks,
                        }
                        self.menu_logger.log_menu_state(
                            title=current_menu_state.title,
                            options=current_menu_state.options,
                            menu_depth=1,
                            navigation_info=navigation_info,
                        )
                        for opt in current_menu_state.options:
                            logger.debug("\tFor option \"%s\" logged option %s", option, opt)
                        if any("Next" in opt for opt in current_menu_state.options):
                            logger.debug(
                                f"Clicking Next at level 1 (click #{level_1_next_clicks + 1}) for page {level_0_page}, option {level_0_option_index}"
                            )
                            success, info = self.menu_navigator.click_next()
                            if not success:
                                raise GsxMenuNotChangedError("Failed to click next after 3 attempts at %s with %s", info[0], info[1])
                            level_1_next_clicks += 1
                        else:
                            logger.debug(
                                f"No more Next button at level 1 for page {level_0_page}, option {level_0_option_index}. Total clicks: {level_1_next_clicks}"
                            )
                            self._navigate_to_level_0_page(level_0_page)
                            break
                self._navigate_to_level_0_page(level_0_page)
                time.sleep(1.0)
                current_menu_state = self.menu_reader.read_menu()
                if any("Next" in opt for opt in current_menu_state.options):
                    logger.debug(f"Moving to level 0 page {level_0_page + 1}")
                    level_0_page += 1
                    self.menu_navigator.click_next()
                else:
                    logger.debug(
                        f"No more pages at level 0. Finished on page {level_0_page}"
                    )
                    break
            self.menu_logger.save_session()
            time.sleep(2)
        if not os.path.exists(file2):
            self.menu_logger.create_interpreted_airport_data(airport)
        with open(file2, "r", encoding="utf-8") as file:
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
        status_callback=None,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
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
            status_callback: Optional callback for status updates

        Returns:
            Tuple[bool, Optional[Dict]]: (Success status, Gate info dict or None)
        """
        # Check if airport data needs to be mapped (first time)
        file1 = f".\\gsx_menu_logs\\{airport}.json"
        file2 = f".\\gsx_menu_logs\\{airport}_interpreted.json"

        if not os.path.exists(file1) and not os.path.exists(file2):
            if status_callback:
                status_callback(
                    f"Analyzing airport parking layout for {airport} - this may take a moment..."
                )
            time.sleep(0.5)
        elif not os.path.exists(file2):
            if status_callback:
                status_callback(f"Loading airport parking data for {airport}")
            time.sleep(0.5)

        airport_data = self.map_available_spots(airport)
        matching_gsx_gate, direct_match = self.find_gate(
            airport_data,
            (terminal or "") + (terminal_number or ""),
            (gate_number or "") + (gate_letter or ""),
        )
        if direct_match is False:
            response = requests.get(
                "https://apipri.sayintentions.ai/sapi/assignGate",
                params={
                    "api_key": self.config.SI_API_KEY,
                    "gate": matching_gsx_gate["gate"],
                    "airport": airport,
                },
            )
            if response.status_code != 200:
                logger.error("Error connecting to API.")
            else:
                logger.info(
                    "Requested matching gate, assuming it has been set for now."
                )
        try:
            if wait_for_ground:
                self._wait_for_ground()
            elif not self.sim_manager.is_on_ground():
                logger.warning("Aircraft not on ground - GSX may fail")
            self._refresh_menu()
            self.menu_navigator.click_planned(matching_gsx_gate)
            self.menu_navigator.find_and_click(["activate"], SearchType.MENU_ACTION)
            self.menu_navigator.find_and_click(
                [self.config.default_airline or "GSX"], SearchType.AIRLINE
            )
            logger.info("Gate assignment completed successfully")
            return True, matching_gsx_gate

        except GsxMenuNotChangedError as e:
            # Menu didn't change, but action might have succeeded anyway
            logger.warning(f"Gate assignment uncertain: {e}")
            # Return success with a flag that it's uncertain
            return True, {**matching_gsx_gate, "_uncertain": True}

        except (GsxMenuError, GsxTimeoutError, OSError, IOError) as e:
            logger.error(f"Gate assignment failed: {e}")
            return False, None

    def _wait_for_ground(self) -> None:
        """Wait indefinitely for aircraft to be on ground"""
        logger.info("Waiting for aircraft on ground...")

        while True:
            on_ground = self.sim_manager.is_on_ground()
            if on_ground:
                logger.info("Aircraft on ground - proceeding")
                return
            time.sleep(1)

    def _refresh_menu(self) -> None:
        """Refresh GSX menu (closes submenus but preserves page position)"""
        #self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 0)
        #time.sleep(0.5)
        self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 1)
        time.sleep(0.1)
        self.sim_manager.set_variable(GsxVariable.MENU_CHOICE.value, -2)
        time.sleep(0.1)
        self.menu_reader.read_menu()

    def _navigate_to_level_0_page(self, target_page: int) -> None:
        """Navigate to specific level 0 page"""
        self._refresh_menu()
        clicks_needed = target_page
        for click_num in range(clicks_needed):
            if not self.menu_navigator.click_next():
                raise GsxMenuError(
                    f"Expected Next button to reach page {target_page}, but none found after {click_num} clicks"
                )

    def find_gate(
        self, airport_data: Dict[str, Any], terminal: str, gate: str
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        for key_terminal, dict_terminal in airport_data["terminals"].items():
            for key_gate, dict_gate in dict_terminal.items():
                if key_terminal == terminal and key_gate == gate:
                    return dict_gate, True

        best_match = None
        best_score = 0

        for key_terminal, dict_terminal in airport_data["terminals"].items():
            for key_gate, dict_gate in dict_terminal.items():
                if key_terminal == "Parking":
                    _key_terminal = ""
                else:
                    _key_terminal = key_terminal
                score = fuzz.ratio(_key_terminal + key_gate, terminal + gate)
                logger.debug(
                    "Looking for Terminal %s Gate %s. Terminal %s and Gate %s reached score of %s",
                    terminal,
                    gate,
                    key_terminal,
                    key_gate,
                    score,
                )
                if score >= best_score:
                    best_score = score
                    best_match = dict_gate

        if best_match:
            logger.debug(
                "Chose best match %s with Score %s",
                best_match["position_id"],
                best_score,
            )
        else:
            logger.warning(
                "No gate match found for Terminal %s Gate %s", terminal, gate
            )

        return best_match, False

"""Gate assignment automation with logging"""

# Licensed under AGPL-3.0-or-later with additional terms
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
from GateAssignmentDirector.gate_matcher import GateMatcher
from GateAssignmentDirector.tooltip_reader import TooltipReader

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
        self.gate_matcher = GateMatcher(config)
        self.tooltip_reader = TooltipReader(config)

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
            # Verify ICAO before parsing
            self._refresh_menu()
            current_menu_state = self.menu_reader.read_menu()
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
            logger.debug(
                "Airport %s has not been parsed yet. Starting parsing", airport
            )
            self.menu_logger.start_session(gate_info=GateInfo(airport=airport))
            self._refresh_menu()
            level_0_page = 0
            while True:
                current_menu_state = self.menu_reader.read_menu()
                all_options = current_menu_state.options
                level_0_options = [
                    opt
                    for opt in all_options
                    if ("Next" not in opt and "Runway" not in opt)
                ]
                logger.debug(
                    f"Found {len(level_0_options)} options on page {level_0_page}"
                )
                time.sleep(self.config.sleep_short)
                for option in level_0_options:
                    actual_index = all_options.index(option)
                    level_1_next_clicks = 0
                    if "Previous" in option[1:].split():
                        continue
                    navigation_info = {
                        "level_0_page": level_0_page,
                        "level_0_option_index": actual_index,
                        "level_1_next_clicks": level_1_next_clicks,
                    }
                    self.menu_logger.log_menu_state(
                        title=current_menu_state.title,
                        options=all_options,
                        menu_depth=0,
                        navigation_info=navigation_info,
                    )
                    success = self.menu_navigator.click_by_index(actual_index)
                    if success:
                        logger.debug("Clicked on level_0 option %s", option)
                    else:
                        logger.debug("Failed to click on level_0 option %s", option)
                    while True:
                        current_menu_state = self.menu_reader.read_menu()
                        navigation_info = {
                            "level_0_page": level_0_page,
                            "level_0_option_index": actual_index,
                            "level_1_next_clicks": level_1_next_clicks,
                        }
                        self.menu_logger.log_menu_state(
                            title=current_menu_state.title,
                            options=current_menu_state.options,
                            menu_depth=1,
                            navigation_info=navigation_info,
                        )
                        for opt in current_menu_state.options:
                            logger.debug(
                                '\tFor option "%s" logged option %s', option, opt
                            )
                        if any("Next" in opt for opt in current_menu_state.options):
                            logger.debug(
                                f"Clicking Next at level 1 (click #{level_1_next_clicks + 1}) for page {level_0_page}, option {actual_index}"
                            )
                            success, info = self.menu_navigator.click_next()
                            if not success:
                                raise GsxMenuNotChangedError(
                                    "Failed to click next after 3 attempts at %s with %s",
                                    info[0],
                                    info[1],
                                )
                            level_1_next_clicks += 1
                        else:
                            logger.debug(
                                f"No more Next button at level 1 for page {level_0_page}, option {actual_index}. Total clicks: {level_1_next_clicks}"
                            )
                            self._navigate_to_level_0_page(level_0_page)
                            break
                self._navigate_to_level_0_page(level_0_page)
                time.sleep(1.0)
                current_menu_state = self.menu_reader.read_menu()
                if any("Next" in opt for opt in current_menu_state.options):
                    logger.debug(f"Moving to level 0 page {level_0_page + 1}")
                    level_0_page += 1
                    success, info = self.menu_navigator.click_next()
                    if not success:
                        raise GsxMenuNotChangedError(
                            f"Failed to click Next at level 0 page {level_0_page}. "
                            f"Menu was: {info[0]} with options {info[1]}"
                        )
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
        gate_prefix: Optional[str] = None,
        gate_suffix: Optional[str] = None,
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
            gate_prefix: Gate prefix letter (e.g., "V" in "V5")
            gate_suffix: Gate suffix letter (e.g., "A" in "5A")
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

        terminal_full = " ".join(filter(None, [terminal, terminal_number]))
        gate_full = (gate_prefix or "") + (gate_number or "") + (gate_suffix or "")

        matching_gsx_gate, needs_api_call = self.find_gate(
            airport_data,
            terminal_full,
            gate_full,
        )
        if needs_api_call:
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
        # Retry clicking up to 2 times (GSX navigation can be unreliable)
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                if wait_for_ground:
                    self._wait_for_ground()
                elif not self.sim_manager.is_on_ground():
                    logger.warning("Aircraft not on ground - GSX may fail")

                self._refresh_menu()

                # Verify ICAO before navigating
                current_menu_state = self.menu_reader.read_menu()
                icao_pattern = re.compile(r"\b([A-Z]{4})\b")
                icao_match = icao_pattern.search(current_menu_state.title)
                if icao_match:
                    menu_icao = icao_match.group(1)
                    if menu_icao != airport:
                        raise GsxMenuError(
                            f"ICAO mismatch: Expected {airport}, but GSX menu shows {menu_icao}"
                        )
                    logger.debug(f"ICAO verified before navigation: {menu_icao}")
                else:
                    logger.warning(
                        f"Could not parse ICAO from menu title before navigation: '{current_menu_state.title}'"
                    )

                # Capture baseline tooltip timestamp before action
                time.sleep(self.config.sleep_short)
                baseline_timestamp = self.tooltip_reader.get_file_timestamp()
                time.sleep(self.config.sleep_short)
                self.menu_navigator.click_planned(matching_gsx_gate)
                self.menu_navigator.find_and_click(["activate"], SearchType.KEYWORD)

                if self.tooltip_reader.check_for_success(baseline_timestamp):
                    logger.info("Gate activated successfully (confirmed via tooltip)")
                    if status_callback:
                        gate_name = matching_gsx_gate.get("gate", "Unknown")
                        status_callback(f"Successfully assigned to gate {gate_name}")
                    self._close_menu()
                    return True, matching_gsx_gate

                # Tooltip didn't confirm - try airline selection
                logger.debug("No tooltip confirmation, attempting airline selection")
                self.menu_navigator.find_and_click(
                    [self.config.default_airline or "GSX"], SearchType.AIRLINE
                )

                if self.tooltip_reader.check_for_success(
                    baseline_timestamp, timeout=2.0
                ):
                    logger.info(
                        "Gate assignment completed successfully (confirmed via tooltip)"
                    )
                    if status_callback:
                        gate_name = matching_gsx_gate.get("gate", "Unknown")
                        status_callback(f"Successfully assigned to gate {gate_name}")
                    self._close_menu()
                    return True, matching_gsx_gate
                else:
                    logger.warning(
                        "Gate assignment uncertain - no tooltip confirmation after airline selection"
                    )
                    if status_callback:
                        gate_name = matching_gsx_gate.get("gate", "Unknown")
                        status_callback(
                            f"Assigned to gate {gate_name} (uncertain - verify in GSX)"
                        )
                    self._close_menu()
                    return True, {**matching_gsx_gate, "_uncertain": True}

            except GsxMenuNotChangedError as e:
                if self.tooltip_reader.check_for_success(
                    baseline_timestamp, timeout=0.5
                ):
                    logger.info(
                        "Gate assignment succeeded (tooltip confirmation after menu error)"
                    )
                    if status_callback:
                        gate_name = matching_gsx_gate.get("gate", "Unknown")
                        status_callback(f"Successfully assigned to gate {gate_name}")
                    self._close_menu()
                    return True, matching_gsx_gate

                # Menu didn't change, but action might have succeeded anyway
                logger.warning(f"Gate assignment uncertain: {e}")
                if status_callback:
                    gate_name = matching_gsx_gate.get("gate", "Unknown")
                    status_callback(
                        f"Assigned to gate {gate_name} (uncertain - verify in GSX)"
                    )
                # Leave menu open so user can verify - return success with uncertain flag
                return True, {**matching_gsx_gate, "_uncertain": True}

            except (GsxMenuError, GsxTimeoutError) as e:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"Gate clicking failed (attempt {attempt + 1}/{max_attempts}): {e}"
                    )
                    logger.info(
                        "Retrying gate assignment (already matched gate, skipping re-match)..."
                    )
                    time.sleep(0.5)
                else:
                    logger.error(
                        f"Gate assignment failed after {max_attempts} attempts: {e}"
                    )
                    if status_callback:
                        status_callback(f"Gate assignment failed: {e}")
                    return False, None

            except (OSError, IOError) as e:
                logger.error(f"Gate assignment failed due to I/O error: {e}")
                if status_callback:
                    status_callback(f"Gate assignment failed: I/O error")
                return False, None

        if status_callback:
            status_callback("Gate assignment failed after all attempts")
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
        # self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 0)
        # time.sleep(0.5)
        self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 1)
        time.sleep(0.1)
        self.sim_manager.set_variable(GsxVariable.MENU_CHOICE.value, -2)
        time.sleep(0.1)
        self.menu_reader.read_menu()

    def _close_menu(self) -> None:
        """Close GSX menu"""
        self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 0)
        time.sleep(0.1)

    def _navigate_to_level_0_page(self, target_page: int) -> None:
        """Navigate to specific level 0 page"""
        self._refresh_menu()
        clicks_needed = target_page
        time.sleep(self.config.sleep_short)
        for click_num in range(clicks_needed):
            if not self.menu_navigator.click_next():
                raise GsxMenuError(
                    f"Expected Next button to reach page {target_page}, but none found after {click_num} clicks"
                )

    def find_gate(
        self, airport_data: Dict[str, Any], terminal: str, gate: str
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Find gate in airport data using exact or fuzzy matching.

        Returns:
            Tuple of (gate_data, is_exact_match)
        """
        gate_data, is_exact, score, score_components = (
            self.gate_matcher.find_best_match(airport_data, terminal, gate)
        )
        if gate_data:
            # Exact matches don't need API call
            if is_exact:
                needs_api_call = False
            # For fuzzy matches, check score components if available
            elif (
                score_components
                and score_components["gate_prefix"] > 50.0
                and score_components["gate_number"] > 80.0
            ):
                needs_api_call = False
            else:
                needs_api_call = True
        else:
            logger.warning(
                "No gate match found for Terminal %s Gate %s", terminal, gate
            )
            needs_api_call = True
        return gate_data, needs_api_call

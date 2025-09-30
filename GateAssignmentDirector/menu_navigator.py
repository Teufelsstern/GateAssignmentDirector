"""GSX menu navigation with integrated logging"""

import time
import re
import logging
from typing import List

from GateAssignmentDirector.gsx_enums import SearchType, GsxVariable
from GateAssignmentDirector.exceptions import GsxMenuError

logger = logging.getLogger(__name__)


class MenuNavigator:
    """Handles GSX menu navigation and searching with logging"""

    def __init__(self, config, menu_logger, menu_reader, sim_manager):
        self.config = config
        self.menu_logger = menu_logger
        self.menu_reader = menu_reader
        self.sim_manager = sim_manager

        self.menu_choice = self.sim_manager.create_request(
            GsxVariable.MENU_CHOICE.value, settable=True
        )

        logging.basicConfig(
            level=config.logging_level,
            format=config.logging_format,
            datefmt=config.logging_datefmt,
        )

    def find_and_click(
        self,
        keywords: List[str],
        search_type: SearchType,
    ) -> bool:
        logger.debug(
            "Looking for keywords %s with Search Type %s", *keywords, search_type
        )
        """Find keywords in menu and click the option"""

        attempts = 0
        max_attempts = 20  # Prevent infinite pagination

        while attempts < max_attempts:
            attempts += 1
            menu = self.menu_reader.read_menu()
            if not menu:
                raise GsxMenuError("Failed to read menu")

            found_index = _search_options(keywords, search_type, menu)

            if found_index != -1:
                # Click the found option
                logger.info(
                    f"Found {keywords} at index {found_index}: {menu.options[found_index]}"
                )

                time.sleep(self.config.sleep_long)
                self.menu_choice.value = found_index
                time.sleep(self.config.sleep_long)

                # Verify menu changed and update depth
                if not self._wait_for_change():
                    raise GsxMenuError("Menu did not change after selection")
                return True

            # Try pagination if not found
            if search_type != SearchType.MENU_ACTION and not self.click_next():
                break

        raise GsxMenuError(f"Could not find {keywords} after {attempts} attempts")

    def click_by_index(self, index):
        time.sleep(self.config.sleep_short)
        self.menu_choice.value = index
        time.sleep(self.config.sleep_short)
        return self._wait_for_change()

    def click_next(self) -> bool:
        """Click Next button if available"""
        menu = self.menu_reader.current_state
        for index, option in menu.options_enum:
            if "Next" in option.split():
                logger.debug(f"Clicking Next at index {index}")
                self.menu_choice.value = index
                time.sleep(self.config.sleep_short)
                self._wait_for_change()
                return True
        return False

    def click_planned(self, gate_info):
        raw_info = gate_info["raw_info"]
        first_index = raw_info["level_0_index"]
        next_count = raw_info["next_clicks"]
        second_index = raw_info["menu_index"]
        self.click_by_index(first_index)
        for _ in range(0,next_count):
            self.click_next()
        self.click_by_index(second_index)
        return True

    def _wait_for_change(self) -> bool:
        """Wait for menu to change"""
        attempts = 0
        max_attempts = self.config.max_menu_check_attempts
        while attempts < max_attempts:
            attempts += 1
            time.sleep(0.1)  # Small delay
            try:
                if len(self.menu_reader.previous_state.options) >= 2:
                    check_option = self.menu_reader.previous_state.options[2]
                else:
                    check_option = "Default"
            except IndexError as e:
                logger.debug("IndexError, probably something racing or such %s", e)
                check_option = "Default"
            self.menu_reader.read_menu()
            if self.menu_reader.has_changed(check_option):
                return True
        return False


def _search_options(keywords: List[str], search_type: SearchType, menu) -> int:
    """Search for keywords in menu options"""
    index = 0
    for index, option in menu.options_enum:
        if search_type == SearchType.KEYWORD:
            words = option.split()
            if any(word == keyword for word in words for keyword in keywords):
                break
        else:
            keyword = keywords[0]
            if keyword in option:
                break
    return index
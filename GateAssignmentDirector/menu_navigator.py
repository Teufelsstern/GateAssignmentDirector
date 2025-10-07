"""GSX menu navigation with integrated logging"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import time
import re
import logging
from typing import List, Dict, Any, Tuple

from GateAssignmentDirector.gsx_enums import SearchType, GsxVariable
from GateAssignmentDirector.exceptions import GsxMenuError, GsxMenuNotChangedError

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
            "Looking for keywords %s with Search Type %s", keywords, search_type
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
            if keywords[0] == "activate":
                found_index -= 2
            if found_index != -1:
                logger.info(
                    f"Found {keywords} at index {found_index}: {menu.options[found_index]}"
                )
                time.sleep(self.config.sleep_short)
                self.menu_choice.value = found_index
                time.sleep(self.config.sleep_short)
                self._wait_for_change()
                return True
            if search_type != SearchType.MENU_ACTION and not self.click_next():
                break

        raise GsxMenuError(f"Could not find {keywords} after {attempts} attempts")

    def click_by_index(self, index: int) -> None:
        time.sleep(self.config.sleep_short)
        self.menu_choice.value = index
        time.sleep(self.config.sleep_short)
        self._wait_for_change()

    def click_next(self) -> Tuple[bool, tuple]:
        """Click Next button if available. Returns True if clicked, False if no Next button found."""
        menu = self.menu_reader.current_state
        attempts = 0
        info = (None, None)
        for index, option in menu.options_enum:
            if any("Next" in opt for opt in option.split()):
                while attempts < 3:
                    logger.debug(f"Attempting to click Next at index {index}")
                    self.menu_choice.value = index
                    time.sleep(self.config.sleep_short)
                    success, info = self._wait_for_change()
                    if success:
                        return success, info
                    attempts += 1
                return False, info
        return True, info

    def click_planned(self, gate_info: Dict[str, Any]) -> None:
        raw_info = gate_info["raw_info"]
        level_0_page = raw_info["level_0_page"]
        level_0_option_index = raw_info["level_0_option_index"]
        level_1_next_clicks = raw_info["level_1_next_clicks"]
        second_index = raw_info["menu_index"]
        for _ in range(level_0_page - 1):
            if not self.click_next():
                raise GsxMenuError(f"Expected Next button to reach page {level_0_page}")
        self.click_by_index(level_0_option_index)
        for i in range(level_1_next_clicks):
            if not self.click_next() and i < level_1_next_clicks - 1:
                raise GsxMenuError(f"Expected Next button at level 1 click {i+1}")
        self.click_by_index(second_index)

    def _wait_for_change(self) -> Tuple[bool, tuple[str, list]]:
        """Wait for menu to change, raise exception if timeout"""
        attempts = 0
        max_attempts = self.config.max_menu_check_attempts
        old_title = self.menu_reader.current_state.title
        old_options = self.menu_reader.current_state.options[:]
        while attempts < max_attempts:
            attempts += 1
            time.sleep(0.1)
            self.menu_reader.read_menu()
            if (
                self.menu_reader.current_state.title != old_title
                or self.menu_reader.current_state.options != old_options
            ):
                return True, (old_title, old_options)
        return False, (old_title, old_options)


def _search_options(keywords: List[str], search_type: SearchType, menu) -> int:
    """Search for keywords in menu options"""
    activate_increment = -2 if search_type == SearchType.MENU_ACTION else 0
    for index, option in menu.options_enum:
        if search_type == SearchType.KEYWORD:
            words = option.split()
            if any(word == keyword for word in words for keyword in keywords):
                return index
        else:
            keyword = keywords[0]
            if keyword in option:
                return index + activate_increment
    return -1

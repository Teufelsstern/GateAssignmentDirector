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

    def click_by_index(self, index: int) -> bool:
        """Click menu option by index with GSX refresh retry on failure"""
        self.menu_reader.read_menu()
        time.sleep(self.config.sleep_short)
        self.menu_choice.value = index
        time.sleep(self.config.sleep_short)

        # First attempt to wait for change
        success, _ = self._wait_for_change()
        if success:
            return success

        # If first attempt failed, try GSX refresh command and check again
        logger.warning(f"Menu did not change after clicking index {index}, attempting GSX refresh...")
        self.menu_choice.value = -2  # GSX refresh command
        time.sleep(self.config.sleep_short)

        # Try again after refresh
        success, info = self._wait_for_change()
        if success:
            logger.info(f"Menu changed after GSX refresh for index {index}")
            return success

        # Both attempts failed
        raise GsxMenuNotChangedError(
            f"Menu did not change after clicking index {index} (tried refresh). "
            f"Last menu was: '{info[0]}' with options {info[1]}"
        )

    def click_next(self) -> Tuple[bool, tuple]:
        """Click Next button if available. Returns True if clicked, False if no Next button found."""
        self.menu_reader.read_menu()
        menu = self.menu_reader.current_state
        attempts = 0
        info = (None, None)
        for index, option in menu.options_enum:
            if any("Next" in opt for opt in option.split()):
                while attempts < 3:
                    logger.debug(f"Attempting to click Next at index {index}")
                    pre_value = self.menu_choice.value
                    self.menu_choice.value = index
                    time.sleep(self.config.sleep_short)
                    logger.debug("Menu_Choice value is now %s, was %s", self.menu_choice.value, pre_value)
                    success, info = self._wait_for_change()
                    if success:
                        return success, info
                    attempts += 1
                return False, info
        return True, info

    def click_planned(self, gate_info: Dict[str, Any]) -> None:
        self.menu_reader.read_menu()
        raw_info = gate_info["raw_info"]
        level_0_page = raw_info["level_0_page"]
        level_0_option_index = raw_info["level_0_option_index"]
        level_1_next_clicks = raw_info["level_1_next_clicks"]
        second_index = raw_info["menu_index"]
        # level_0_page is 0-indexed, so we need exactly level_0_page Next clicks
        for _ in range(level_0_page):
            success, _ = self.click_next()
            if not success:
                raise GsxMenuError(f"Expected Next button to reach page {level_0_page}")
        self.click_by_index(level_0_option_index)
        for i in range(level_1_next_clicks):
            success, _ = self.click_next()
            if not success and i < level_1_next_clicks - 1:
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
            new_title = self.menu_reader.current_state.title
            new_options = self.menu_reader.current_state.options
            if (
                new_title != old_title
            ):
                logger.debug("Title changed from %s to %s. Change detected.", old_title, new_title)
                return True, (old_title, old_options)
            elif (
                new_options != old_options
            ):
                logger.debug("Options changed from %s to %s. Change detected.", old_options, new_options)
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

"""GSX menu file reading and parsing"""

import os
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

from GateAssignmentDirector.exceptions import GsxFileNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class MenuState:
    """Represents current GSX menu state"""

    title: str
    options: List[str]
    options_enum: List[Tuple[int, str]]
    raw_lines: List[str]
    file_timestamp: float = 0


class MenuReader:
    """Handles automated gate assignment process with logging"""

    def __init__(self, config, menu_logger, menu_navigator, sim_manager) -> None:
        self.config = config
        self.menu_logger = menu_logger
        self.menu_path = self.find_menu_file()

        logging.basicConfig(
            level=config.logging_level,
            format=config.logging_format,
            datefmt=config.logging_datefmt,
        )

        self.current_state = MenuState(
            title="Initial",
            options=["Initial"],
            options_enum=[(0, "Initial")],
            raw_lines=["Initial"],
        )
        self.previous_state = self.current_state

    def has_changed(self, check_option: str = "Default") -> bool:
        """Check if menu has changed"""
        menu_actions = ["Next", "Back", "Close", "Cancel"]

        if len(self.current_state.options) != len(self.previous_state.options):
            changed = True
        elif check_option == "Default":
            current_opt = next((opt for opt in self.current_state.options if opt not in menu_actions), None)
            previous_opt = next((opt for opt in self.previous_state.options if opt not in menu_actions), None)
            changed = current_opt != previous_opt if current_opt and previous_opt else False
        else:
            check_opt = next((opt for opt in self.current_state.options if opt not in menu_actions), None)
            changed = check_opt != check_option if check_opt else False

        self.previous_state = self.current_state
        return changed

    def read_menu(self) -> MenuState:
        """Read and return current menu state"""
        try:
            current_timestamp = os.path.getmtime(self.menu_path)
            error_count = 0
            max_retries = self.config.max_menu_check_attempts * 25

            while error_count < max_retries:
                try:
                    with open(self.menu_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if not lines:
                            error_count += 1
                            continue
                        title = lines[0].strip().replace("\n", "")
                        options = [line.strip().replace("\n", "") for line in lines[1:]]
                        options_enum = list(enumerate(options))
                        self.current_state = MenuState(
                            title=title,
                            options=options,
                            options_enum=options_enum,
                            raw_lines=lines,
                            file_timestamp=current_timestamp,
                        )
                        break
                except (OSError, IOError) as e:
                    error_count += 1
                    if error_count >= max_retries:
                        raise
        except (OSError, IOError) as e:
            logger.error(f"Failed to read menu file: {e}")
            raise

        return self.current_state

    def find_menu_file(self) -> str:
        """Locate the GSX menu file"""
        for path in self.config.menu_file_paths:
            if os.path.exists(path):
                return path
        error_msg = "GSX menu file not found in configured paths - GSX may not be installed or configured correctly"
        logger.error(error_msg)
        raise GsxFileNotFoundError(error_msg)

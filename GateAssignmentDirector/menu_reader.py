"""GSX menu file reading and parsing"""

import os
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

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

    def __init__(self, config, menu_logger, menu_navigator, sim_manager):
        self.menu_navigator = menu_navigator
        self.sim_manager = sim_manager
        self.config = config
        self.menu_logger: Optional[menu_logger] = None
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
        if len(self.current_state.options) != len(self.previous_state.options):
            self.previous_state = self.current_state
            return True
        elif (
            check_option == "Default"
            and len(self.current_state.options) > 2
            and len(self.previous_state.options) > 2
        ):
            self.previous_state = self.current_state
            return self.current_state.options[2] != self.previous_state.options[2]
        else:
            self.previous_state = self.current_state
            return self.current_state.options[2] != check_option

    def read_menu(self):
        """Read and return current menu state"""
        current_timestamp = os.path.getmtime(self.menu_path)
        error_count = 0
        while error_count < 100:
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
        return self.current_state

    def find_menu_file(self):
        """Locate the GSX menu file"""
        for path in self.config.menu_file_paths:
            if os.path.exists(path):
                menu_path = path
                return menu_path
        logger.warning("GSX menu file not found in configured paths")

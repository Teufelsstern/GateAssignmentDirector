import json
import time
import logging
import configparser
import re
import unittest

from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from GateAssignmentDirector import config
from GateAssignmentDirector.gsx_enums import GateGroups
from GateAssignmentDirector.gsx_hook import GsxHook

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=config.GsxConfig.logging_level,
    format=config.GsxConfig.logging_format,
    datefmt=config.GsxConfig.logging_datefmt,
)


@dataclass
class GateInfo:
    """Parsed gate information"""

    terminal_name: Optional[str] = None
    terminal_number: Optional[str] = None
    gate_number: Optional[str] = None
    gate_letter: Optional[str] = None
    raw_value: str = ""

    def __str__(self):
        parts = []
        if self.terminal_name:
            parts.append(f"Terminal: {self.terminal_name} ")
        if self.terminal_number:
            parts.append(self.terminal_number)
        if self.gate_number:
            gate_str = f"Gate: {self.gate_number}"
            if self.gate_letter:
                gate_str += self.gate_letter
            parts.append(gate_str)
        return " | ".join(parts) if parts else f"Raw: {self.raw_value}"


class GateParser:
    """Intelligent gate information parser"""

    def __init__(self, match: Optional[re.Match[str]] = None):
        self.match: Optional[re.Match[str]] = match
        self.pattern = re.compile(
            r"""
                (?:terminal\s+)?
                (?:(terminal|international|parking|domestic|main|central|pier|concourse|level)\s+)?
                (?:terminal\s+)?
                (?:([A-Z)]|\d+)\s+)?
                (?:(gate)\s+)?
                (?:([A-Z])\s*)?
                (?:(\d+)(?:\s*|$))?
                (?:([A-Z])(?:\s*|$))?
                """,
            re.IGNORECASE | re.VERBOSE,
        )

    def parse_gate(
        self, gate_string: str
    ) -> GateInfo:
        """
        Parse gate string into components using intelligent pattern matching
        """
        if not gate_string or gate_string.strip() == "":
            return GateInfo()

        gate_string = gate_string.strip()
        gate_info = GateInfo(
            raw_value=gate_string,
            gate_letter="",
            gate_number="",
            terminal_name="",
            terminal_number="",
        )

        # Try patterns in order of specificity
        self.match = self.pattern.search(gate_string)
        if self.match:
            gate_info.terminal_name = (
                self.match.group(GateGroups.T_NAME).capitalize()
                if self.match.group(GateGroups.T_NAME) is not None
                else "Terminal"
            )
            gate_info.terminal_number = (
                self.match.group(GateGroups.T_NUMBER).capitalize()
                if self.match.group(GateGroups.T_NUMBER) is not None
                else ""
            )
            gate_info.gate_number = (
                self.match.group(GateGroups.G_NUMBER)
                if self.match.group(GateGroups.G_NUMBER) is not None
                else ""
            )
            gate_info.gate_letter = (
                self.match.group(GateGroups.G_LETTER).capitalize()
                if self.match.group(GateGroups.G_LETTER) is not None
                else ""
            )
        return gate_info


class JSONMonitor:
    def __init__(
        self,
        file_path: str,
        config_path: str = "monitor_config.ini",
        poll_interval: int = 5,
        default_log_level: str = "INFO",
        enable_gsx_integration: bool = False,
        gate_callback: bool = None,
    ):
        self.file_path = Path(file_path)
        self.config_path = Path(config_path)
        self.poll_interval = poll_interval
        self.previous_data: Optional[Dict[str, Any]] = None
        self.default_log_level = default_log_level
        self.gate_parser = GateParser()
        self.current_gate_info: Optional[GateInfo] = None
        self.enable_gsx_integration = enable_gsx_integration
        self.gsx_hook = None
        self.gate_callback = gate_callback

        logging.basicConfig(
            level=config.GsxConfig.logging_level,
            format=config.GsxConfig.logging_format,
            datefmt=config.GsxConfig.logging_datefmt,
        )

        # Load field-specific log levels
        self.field_log_levels = self.load_config()

    def load_config(self) -> Dict[str, str]:
        """Load field-specific log levels from config file"""
        if not self.config_path.exists():
            return {"default": self.default_log_level}

        _config = configparser.ConfigParser()
        _config.read(self.config_path)

        if "LOG_LEVELS" not in config:
            logger.warning("No LOG_LEVELS section in config, using defaults")
            return {"default": self.default_log_level}

        return dict(_config["LOG_LEVELS"])

    def get_log_level_for_field(self, field_path: str) -> str:
        """Get log level for specific field, fall back to default"""
        return self.field_log_levels.get(
            field_path, self.field_log_levels.get("default", self.default_log_level)
        )

    def check_gate_assignment(self, data: Dict[str, Any]) -> None:
        """Check for gate assignment and parse it if found"""
        try:
            gate_value = (
                data.get("flight_details", {})
                .get("current_flight", {})
                .get("assigned_gate")
            )

            airport = (
                data.get("flight_details", {})
                .get("current_flight", {})
                .get("flight_destination")
            )

            if gate_value and str(gate_value).strip():
                gate_info = self.gate_parser.parse_gate(str(gate_value))

                if (
                    self.current_gate_info is None
                    or self.current_gate_info.raw_value != gate_info.raw_value
                ):
                    logger.info(f"GATE ASSIGNED: {gate_info}")
                    # Use callback if provided, otherwise use GSX integration
                    if self.gate_callback:
                        gate_data = gate_info.__dict__.copy()
                        gate_data['airport'] = airport  # Add airport to the dict
                        self.gate_callback(gate_data)  # Send to director
                    elif self.enable_gsx_integration:
                        self.call_gsx_gate_finder(gate_info)

                    self.current_gate_info = gate_info
            else:
                if self.current_gate_info is not None:
                    logger.info("GATE CLEARED")
                    self.current_gate_info = None

        except Exception as e:
            logger.error(f"Error checking gate assignment: {e}")

    def call_gsx_gate_finder(self, gate_info: GateInfo, airline: str = "GSX") -> bool:
        """Call the GSX gate_finder with parsed gate information"""
        if not self.enable_gsx_integration:
            logger.debug("GSX integration is disabled")
            return False

        try:
            # Import GSX module only when needed
            if self.gsx_hook is None:
                try:
                    self.gsx_hook = GsxHook()
                    logger.info("GSX Hook initialized successfully")
                except ImportError as e:
                    logger.error(f"Failed to import GSX module: {e}")
                    return False
                except Exception as e:
                    logger.error(f"Failed to initialize GSX Hook: {e}")
                    return False

            # Convert gate_info to parameters for GSX gate_finder
            gsx_params = {
                "terminal_name": gate_info.terminal_name,
                "gate_number": (gate_info.gate_number if gate_info.gate_number else -1),
                "gate_letter": gate_info.gate_letter if gate_info.gate_letter else None,
                "airline": airline,
            }

            # Add terminal info if available
            if gate_info.terminal_number:
                # Try to determine if terminal is letter or number
                if gate_info.terminal_number.isdigit():
                    gsx_params["terminal_number"] = int(gate_info.terminal_number)
                else:
                    gsx_params["terminal_letter"] = gate_info.terminal_number

            logger.info(f"Calling GSX gate_finder with: {gsx_params}")

            # Call the GSX gate_finder method
            self.gsx_hook.gate_finder(**gsx_params)

            logger.info("GSX gate_finder completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error calling GSX gate_finder: {e}")
            return False

    def display_initial_data(self, data: Dict[str, Any], path: str = "") -> None:
        """Display initial data in readable list format with log levels"""
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            log_level = self.get_log_level_for_field(current_path)

            if isinstance(value, dict):
                logger.info(f"• {current_path}: [OBJECT] - Log Level: {log_level}")
                self.display_initial_data(value, current_path)
            elif isinstance(value, list):
                logger.info(
                    f"• {current_path}: [LIST with {len(value)} items] - Log Level: {log_level}"
                )
            else:
                logger.info(f"• {current_path}: {value} - Log Level: {log_level}")

    def read_json(self) -> Optional[Dict[str, Any]]:
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {self.file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading file: {e}")
            return None

    def log_change(self, message: str, field_path: str):
        """Log change with field-specific log level"""
        log_level = self.get_log_level_for_field(field_path)
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.log(numeric_level, message)

    def find_changes(
        self, old_data: Dict[str, Any], new_data: Dict[str, Any], path: str = ""
    ) -> None:
        for key in new_data:
            current_path = f"{path}.{key}" if path else key

            if key not in old_data:
                self.log_change(
                    f"ADDED: {current_path} = {new_data[key]}", current_path
                )
            elif isinstance(new_data[key], dict) and isinstance(old_data[key], dict):
                self.find_changes(old_data[key], new_data[key], current_path)
            elif new_data[key] != old_data[key]:
                self.log_change(
                    f"CHANGED: {current_path} = {old_data[key]} -> {new_data[key]}",
                    current_path,
                )

        for key in old_data:
            if key not in new_data:
                current_path = f"{path}.{key}" if path else key
                self.log_change(
                    f"REMOVED: {current_path} = {old_data[key]}", current_path
                )

    def monitor(self):
        logger.info(f"Starting monitor for {self.file_path}")
        logger.info(f"Config loaded from {self.config_path}")
        logger.info("=" * 50)

        while True:
            try:
                current_data = self.read_json()

                if current_data is not None:
                    if self.previous_data is None:
                        logger.info("=== INITIAL DATA WITH LOG LEVELS ===")
                        self.display_initial_data(current_data)
                        logger.info("=" * 50)
                        logger.info("=== MONITORING FOR CHANGES ===")
                    elif current_data != self.previous_data:
                        logger.info("--- CHANGES DETECTED ---")
                        self.find_changes(self.previous_data, current_data)
                        logger.info("--- END CHANGES ---")

                    # Always check gate assignment
                    self.check_gate_assignment(current_data)

                    self.previous_data = current_data

                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(self.poll_interval)


if __name__ == "__main__":
    # Configuration
    unittest.main()
    FILE_PATH = "C:\\Users\\mariu\\AppData\\Local\\SayIntentionsAI\\flight.json"
    CONFIG_PATH = "monitor_config.ini"
    POLL_INTERVAL = 1  # seconds
    DEFAULT_LOG_LEVEL = "INFO"
    ENABLE_GSX_INTEGRATION = True  # Set to False to disable GSX integration

    monitor = JSONMonitor(
        FILE_PATH, CONFIG_PATH, POLL_INTERVAL, DEFAULT_LOG_LEVEL, ENABLE_GSX_INTEGRATION
    )
    monitor.monitor()

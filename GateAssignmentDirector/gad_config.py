"""Configuration module for Gate Assignment Director"""

# Licensed under GPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import getpass
import yaml
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path


logger = logging.getLogger(__name__)

@dataclass
class GADConfig:
    """Configuration for Gate Assignment Director"""
    # All configurable fields - loaded from YAML
    menu_file_paths: list[str] = field(default_factory=lambda: [
        r"C:\Program Files (x86)\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu",
        r"C:\Program Files\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu",
    ])
    sleep_short: float = 0.1
    sleep_long: float = 0.3
    ground_check_interval: float = 1.0
    aircraft_request_interval: float = 2.0
    max_menu_check_attempts: int = 4
    logging_level: str = 'DEBUG'
    logging_format: str = '%(asctime)s - %(levelname)s - %(message)s'
    logging_datefmt: str = '%H:%M:%S'
    SI_API_KEY: str = 'YOUR_API_KEY_HERE'
    default_airline: str = 'GSX'

    logging.basicConfig(
        level=logging_level,
        format=logging_format,
        datefmt=logging_datefmt,
    )
    # These are computed at runtime (not in YAML)
    username: str = field(default_factory=getpass.getuser)
    flight_json_path: str = field(init=False)

    def __post_init__(self):
        # Dynamically set flight_json_path based on username
        self.flight_json_path = f"C:\\Users\\{self.username}\\AppData\\Local\\SayIntentionsAI\\flight.json"

    @classmethod
    def _get_defaults(cls):
        """Return default configuration values"""
        return {
            'menu_file_paths': [
                r"C:\Program Files (x86)\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu",
                r"C:\Program Files\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu",
            ],
            'sleep_short': 0.1,
            'sleep_long': 0.3,
            'ground_check_interval': 1.0,
            'aircraft_request_interval': 2.0,
            'max_menu_check_attempts': 4,
            'logging_level': 'DEBUG',
            'logging_format': '%(asctime)s - %(levelname)s - %(message)s',
            'logging_datefmt': '%H:%M:%S',
            'SI_API_KEY': 'YOUR_API_KEY_HERE',
            'default_airline': 'GSX',
        }

    @classmethod
    def from_yaml(cls, yaml_path: str = None):
        """Load configuration from YAML file"""
        if yaml_path is None:
            # Determine config path based on whether we're bundled or not
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller bundle
                base_path = Path(sys._MEIPASS)
                yaml_path = base_path / "GateAssignmentDirector" / "config.yaml"
            else:
                # Running as normal Python script
                yaml_path = Path(".") / "GateAssignmentDirector" / "config.yaml"

        config_file = Path(yaml_path)

        if not config_file.exists():
            # Create default YAML file
            defaults = cls._get_defaults()
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(defaults, f, default_flow_style=False, allow_unicode=True)
            logger.info("Created default config file: %s", yaml_path)

        # Load from YAML
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            logger.info("Read config file: %s", yaml_path)

        # Ensure float fields are always floats (YAML may load 1.0 as int 1)
        float_fields = ['sleep_short', 'sleep_long', 'ground_check_interval', 'aircraft_request_interval']
        for field in float_fields:
            if field in data:
                data[field] = float(data[field])

        # Create instance with YAML data
        return cls(**data)

    def save_yaml(self, yaml_path: str = None):
        """Save configuration to YAML file"""
        if yaml_path is None:
            # Use same logic as from_yaml for consistency
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS)
                yaml_path = base_path / "GateAssignmentDirector" / "config.yaml"
            else:
                yaml_path = Path(".") / "GateAssignmentDirector" / "config.yaml"
        # Only save the configurable fields (exclude computed ones)
        data = {
            'menu_file_paths': self.menu_file_paths,
            'sleep_short': self.sleep_short,
            'sleep_long': self.sleep_long,
            'ground_check_interval': self.ground_check_interval,
            'aircraft_request_interval': self.aircraft_request_interval,
            'max_menu_check_attempts': self.max_menu_check_attempts,
            'logging_level': self.logging_level,
            'logging_format': self.logging_format,
            'logging_datefmt': self.logging_datefmt,
            'SI_API_KEY': self.SI_API_KEY,
        }

        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.info("Saved config file: %s", yaml_path)


# Global config instance (load from YAML)
config = GADConfig.from_yaml()

logging.basicConfig(
    level=config.logging_level,
    format=config.logging_format,
    datefmt=config.logging_datefmt,
)
"""Configuration module for GSX Hook"""
import getpass
import yaml
import logging
from dataclasses import dataclass, field
from pathlib import Path


logger = logging.getLogger(__name__)

@dataclass
class GsxConfig:
    """Configuration for GSX Hook"""
    # All configurable fields - loaded from YAML
    menu_file_paths: list[str] = field(default_factory=list)
    sleep_short: float = None
    sleep_long: float = None
    ground_check_interval: int = None
    aircraft_request_interval: int = None
    ground_timeout_default: int = None
    max_menu_check_attempts: int = None
    logging_level: str = 'DEBUG'
    logging_format: str = '%(asctime)s - %(levelname)s - %(message)s'
    logging_datefmt: str = '%H:%M:%S'
    SI_API_KEY: str = None
    default_airline: str = None

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
            'ground_check_interval': 1000,
            'aircraft_request_interval': 2000,
            'ground_timeout_default': 300,
            'max_menu_check_attempts': 4,
            'logging_level': 'DEBUG',
            'logging_format': '%(asctime)s - %(levelname)s - %(message)s',
            'logging_datefmt': '%H:%M:%S',
            'SI_API_KEY': 'YOUR_API_KEY_HERE',
            'default_airline': 'GSX',
        }

    @classmethod
    def from_yaml(cls, yaml_path: str = ".\\GateAssignmentDirector\\config.yaml"):
        """Load configuration from YAML file"""
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

        # Create instance with YAML data
        return cls(**data)

    def save_yaml(self, yaml_path: str = ".\\GateAssignmentDirector\\config.yaml"):
        """Save configuration to YAML file"""
        # Only save the configurable fields (exclude computed ones)
        data = {
            'menu_file_paths': self.menu_file_paths,
            'sleep_short': self.sleep_short,
            'sleep_long': self.sleep_long,
            'ground_check_interval': self.ground_check_interval,
            'aircraft_request_interval': self.aircraft_request_interval,
            'ground_timeout_default': self.ground_timeout_default,
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
config = GsxConfig.from_yaml()

logging.basicConfig(
    level=config.logging_level,
    format=config.logging_format,
    datefmt=config.logging_datefmt,
)
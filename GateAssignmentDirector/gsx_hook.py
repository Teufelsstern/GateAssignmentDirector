"""Main GSX Hook class with menu logging"""

import logging
from typing import Optional

from GateAssignmentDirector.config import GsxConfig
from GateAssignmentDirector.simconnect_manager import SimConnectManager
from GateAssignmentDirector.menu_reader import MenuReader
from GateAssignmentDirector.menu_navigator import MenuNavigator
from GateAssignmentDirector.gate_assignment import GateAssignment
from GateAssignmentDirector.menu_logger import MenuLogger
from GateAssignmentDirector.gsx_enums import GsxVariable
from GateAssignmentDirector.exceptions import GsxConnectionError, GsxFileNotFoundError

logger = logging.getLogger(__name__)


class GsxHook:
    """Main GSX automation interface with menu logging"""

    def __init__(
        self, config: Optional[GsxConfig] = None, enable_menu_logging: bool = True
    ) -> None:
        """Initialize GSX Hook with optional configuration and menu logging"""
        self.config = config or GsxConfig()
        self.is_initialized = None
        self.enable_menu_logging = enable_menu_logging

        self.sim_manager = SimConnectManager(self.config.from_yaml())
        self.menu_reader = None
        self.menu_logger = None
        self.menu_navigator = None
        self.gate_assignment = None

        logging.basicConfig(
            level=self.config.logging_level,
            format=self.config.logging_format,
            datefmt=self.config.logging_datefmt,
        )

        try:
            self.sim_manager.connect()

            self.menu_logger = MenuLogger(self.config.from_yaml())
            self.menu_reader = MenuReader(
                self.config.from_yaml(), self.menu_logger, self.menu_navigator, self.sim_manager
            )
            self.menu_navigator = MenuNavigator(
                self.config.from_yaml(), self.menu_logger, self.menu_reader, self.sim_manager
            )

            self.gate_assignment = GateAssignment(
                self.config.from_yaml(),
                self.menu_logger,
                self.menu_reader,
                self.menu_navigator,
                self.sim_manager,
            )

            self.is_initialized = True
            logger.info("GSX Hook initialized successfully")

        except (GsxConnectionError, GsxFileNotFoundError, OSError, IOError) as e:
            logger.error(f"Failed to initialize GSX Hook: {e}")
            self.is_initialized = False
            self._cleanup_partial_init()

    def _cleanup_partial_init(self) -> None:
        """Clean up any partially initialized components"""
        if self.sim_manager:
            try:
                self.sim_manager.disconnect()
            except Exception:
                pass
        self.menu_logger = None
        self.menu_reader = None
        self.menu_navigator = None
        self.gate_assignment = None

    def assign_gate_when_ready(self, airport: str, **kwargs) -> bool:
        """
        Public interface for gate assignment with airport logging

        Args:
            airport: ICAO code of the airport (e.g., "KLAX")
            **kwargs: Additional parameters for gate assignment
        """
        if not self.is_initialized:
            logger.error("GSX Hook not initialized")
            return False
        return self.gate_assignment.assign_gate(airport=airport, **kwargs)

    def is_on_ground(self) -> bool:
        """Check if aircraft is on ground"""
        if not self.is_initialized:
            return False
        return self.sim_manager.is_on_ground()

    def close(self) -> None:
        """Clean up connections"""
        if self.sim_manager:
            self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 0)
            self.sim_manager.disconnect()
        self.is_initialized = False

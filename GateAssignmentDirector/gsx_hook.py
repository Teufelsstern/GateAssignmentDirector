"""Main GSX Hook class with menu logging"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import logging
import time
from typing import Optional

from GateAssignmentDirector.gad_config import GADConfig
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
        self, config: Optional[GADConfig] = None, enable_menu_logging: bool = True
    ) -> None:
        """Initialize GSX Hook with optional configuration and menu logging"""
        self.config = config if config is not None else GADConfig.from_yaml()
        self.is_initialized = None
        self.enable_menu_logging = enable_menu_logging

        self.sim_manager = SimConnectManager(self.config)
        self.menu_reader = None
        self.menu_logger = None
        self.menu_navigator = None
        self.gate_assignment = None

        try:
            self.sim_manager.connect()

            self.menu_logger = MenuLogger(self.config)
            self.menu_reader = MenuReader(
                self.config, self.menu_logger, self.menu_navigator, self.sim_manager
            )
            self.menu_navigator = MenuNavigator(
                self.config, self.menu_logger, self.menu_reader, self.sim_manager
            )

            self.gate_assignment = GateAssignment(
                self.config,
                self.menu_logger,
                self.menu_reader,
                self.menu_navigator,
                self.sim_manager,
            )

            self.is_initialized = True
            logger.info("GSX Hook initialized successfully")

        except (GsxConnectionError, GsxFileNotFoundError, OSError, IOError, Exception) as e:
            logger.error(f"Failed to initialize GSX Hook: {e}")
            self.is_initialized = False
            self._cleanup_partial_init()

    def _cleanup_partial_init(self) -> None:
        """Clean up any partially initialized components"""
        if self.sim_manager:
            try:
                self.sim_manager.disconnect()
            except (OSError, RuntimeError, AttributeError):
                pass
        self.menu_logger = None
        self.menu_reader = None
        self.menu_navigator = None
        self.gate_assignment = None

    def _close_menu(self) -> None:
        """Close GSX menu"""
        self.sim_manager.set_variable(GsxVariable.MENU_OPEN.value, 0)
        time.sleep(0.1)

    def assign_gate_when_ready(self, airport: str, status_callback=None, **kwargs) -> tuple[bool, dict | None]:
        """
        Public interface for gate assignment with airport logging

        Args:
            airport: ICAO code of the airport (e.g., "KLAX")
            status_callback: Optional callback for status updates
            **kwargs: Additional parameters for gate assignment

        Returns:
            Tuple[bool, Optional[Dict]]: (Success status, Gate info dict or None)
        """
        if not self.is_initialized:
            logger.error("GSX Hook not initialized")
            return False, None

        # First attempt
        success, gate_info = self.gate_assignment.assign_gate(airport=airport, status_callback=status_callback, **kwargs)

        # Retry once if failed (GSX can be unreliable)
        if not success:
            logger.warning("Gate assignment failed, closing menu and retrying...")
            self._close_menu()
            time.sleep(0.5)
            success, gate_info = self.gate_assignment.assign_gate(airport=airport, status_callback=status_callback, **kwargs)
            if success:
                logger.info("Gate assignment succeeded on retry")
            else:
                logger.error("Gate assignment failed after retry")

        return success, gate_info

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

"""SimConnect connection management"""

import logging
from typing import Optional
from SimConnect import SimConnect, AircraftRequests, Request

from GateAssignmentDirector.exceptions import GsxConnectionError
from GateAssignmentDirector.gsx_enums import AircraftVariable

logger = logging.getLogger(__name__)


class SimConnectManager:
    """Manages SimConnect connection and requests"""

    def __init__(self, config) -> None:
        self.config = config
        self.connection: Optional[SimConnect] = None
        self.aircraft_requests: Optional[AircraftRequests] = None
        self.ground_check_request: Optional[Request] = None

    def connect(self) -> bool:
        """Establish connection to SimConnect"""
        try:
            self.connection = SimConnect()
            self.aircraft_requests = AircraftRequests(
                self.connection, _time=self.config.aircraft_request_interval
            )
            try:
                self.ground_check_request = Request(
                    (AircraftVariable.ON_GROUND.value, b"Bool"),
                    self.connection,
                    _time=self.config.ground_check_interval,
                )
            except Exception as e:
                logger.error(f"Failed to create ground check request with enum: {e}")
                raise GsxConnectionError(
                    "Ground check request failed with AircraftVariable.ON_GROUND enum. "
                    "Revert to hardcoded b'SIM ON GROUND' if this persists. "
                    "The enum value should be identical to the hardcoded string, but SimConnect may behave differently."
                )
            logger.info("SimConnect connection established")
            return True
        except (OSError, ConnectionError, RuntimeError) as e:
            logger.error(f"Failed to connect to SimConnect: {e}")
            raise GsxConnectionError(f"SimConnect connection failed: {e}")

    def disconnect(self) -> None:
        """Close SimConnect connection"""
        if self.connection:
            self.connection = None
            logger.info("SimConnect disconnected")

    def is_on_ground(self) -> bool:
        """Check if aircraft is on ground"""
        try:
            ground_check_value = self.ground_check_request.value
            return bool(ground_check_value)
        except (AttributeError, TypeError):
            return False

    def create_request(
        self, name: bytes, type_: bytes = b"Number", settable: bool = False
    ) -> Request:
        """Create a SimConnect request"""
        return Request((name, type_), self.connection, _settable=settable, _time=1000)

    def set_variable(self, name: bytes, value: float) -> bool:
        """Set a SimConnect variable"""
        try:
            request = self.create_request(name, settable=True)
            request.value = value
            return True
        except (OSError, RuntimeError, AttributeError) as e:
            logger.error(f"Failed to set variable {name}: {e}")
            return False

"""SimConnect connection management"""

import logging
from typing import Optional
from SimConnect import SimConnect, AircraftRequests, Request

from GateAssignmentDirector.exceptions import GsxConnectionError

logger = logging.getLogger(__name__)


class SimConnectManager:
    """Manages SimConnect connection and requests"""

    def __init__(self, config):
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
            self.ground_check_request = Request(
                (b'SIM ON GROUND', b"Bool"),
                self.connection,
                _time=self.config.ground_check_interval,
            )
            logger.info("SimConnect connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SimConnect: {e}")
            raise GsxConnectionError(f"SimConnect connection failed: {e}")

    def disconnect(self):
        """Close SimConnect connection"""
        if self.connection:
            self.connection = None
            logger.info("SimConnect disconnected")

    def is_on_ground(self) -> bool:
        """Check if aircraft is on ground"""
        ground_check_value = self.ground_check_request.value
        return ground_check_value

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
        except Exception as e:
            logger.error(f"Failed to set variable {name}: {e}")
            return False

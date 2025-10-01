"""Example usage with threaded monitoring"""

# Licensed under GPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import threading
import queue
import logging
from typing import Dict, Any, Optional

from GateAssignmentDirector.si_api_hook import JSONMonitor
from GateAssignmentDirector.gsx_hook import GsxHook
from GateAssignmentDirector.gad_config import GADConfig

logger = logging.getLogger(__name__)

class GateAssignmentDirector:
    def __init__(self) -> None:
        self.gate_queue = queue.Queue()
        self.config = GADConfig()
        self.gsx = None
        self.monitor: Optional[JSONMonitor] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.running = False
        self.current_airport: Optional[str] = None
        self.departure_airport: Optional[str] = None
        self.current_flight_data: Dict[str, Any] = {}

    def start_monitoring(self, json_file_path: str) -> None:
        """Start the JSON monitor in a separate thread"""
        self.monitor = JSONMonitor(
            json_file_path,
            enable_gsx_integration=False,
            gate_callback=self._queue_gate_assignment,
            flight_data_callback=self._update_flight_data
        )

        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor.monitor, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitoring started")

    def _update_flight_data(self, flight_data: Dict[str, Any]) -> None:
        """Callback to update flight data on every poll"""
        self.current_flight_data = flight_data
        self.current_airport = flight_data.get('airport')
        self.departure_airport = flight_data.get('departure_airport')

    def _queue_gate_assignment(self, gate_info: Dict[str, Any]) -> None:
        """Callback when gate is detected"""
        # Store current airport
        if 'airport' in gate_info:
            self.current_airport = gate_info['airport']
        self.gate_queue.put(gate_info)
        logger.info(f"Gate detected: {gate_info}")

    def process_gate_assignments(self) -> None:
        """Main loop to process gate assignments"""
        logger.info("Director ready - waiting for gate assignments")

        while self.running:
            try:
                gate_info = self.gate_queue.get(timeout=1.0)
                logger.info(f"Processing gate assignment: {gate_info}")

                # Initialize GSX if needed
                if not self.gsx or not self.gsx.is_initialized:
                    self.gsx = GsxHook(self.config, enable_menu_logging=True)
                    if not self.gsx.is_initialized:
                        logger.error("Failed to initialize GSX Hook")
                        continue

                # Process assignment
                success = self.gsx.assign_gate_when_ready(
                    airport=gate_info.get('airport', 'EDDS'),
                    gate_letter=gate_info.get('gate_letter', ""),
                    gate_number=gate_info.get('gate_number', ""),
                    terminal=gate_info.get('terminal', ""),
                    terminal_number=gate_info.get('terminal_number', ""),
                    airline=gate_info.get('airline', 'GSX'),
                    wait_for_ground=True,
                )

                logger.info(f"Gate assignment {'completed' if success else 'failed'}")

            except queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()
                break

    def stop(self) -> None:
        """Clean shutdown"""
        logger.info("Stopping director")
        self.running = False
        if self.gsx:
            self.gsx.close()

if __name__ == "__main__":
    director = GateAssignmentDirector()
    try:
        director.start_monitoring(director.config.flight_json_path)
        director.process_gate_assignments()
    except KeyboardInterrupt:
        director.stop()
"""Example usage with threaded monitoring"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import threading
import queue
import logging
import time
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
        self.status_callback = None
        self.airport_override: Optional[str] = None
        self.mapped_airports: set = set()

    def start_monitoring(self, json_file_path: str) -> None:
        """Start the JSON monitor in a separate thread"""
        self.monitor = JSONMonitor(
            json_file_path,
            enable_gsx_integration=False,
            gate_callback=self._queue_gate_assignment,
            flight_data_callback=self._update_flight_data,
            gad_config_instance=self.config
        )

        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor.monitor, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitoring started")

        # Notify UI of progress
        if self.status_callback:
            self.status_callback("Connected to flight data source")
        time.sleep(1.0)

    def _update_flight_data(self, flight_data: Dict[str, Any]) -> None:
        """Callback to update flight data on every poll"""
        self.current_flight_data = flight_data
        # Don't override current_airport if manual override is active
        if not self.airport_override:
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

        # Notify UI of progress
        if self.status_callback:
            self.status_callback("Gate assignment system ready")
        time.sleep(0.8)

        while self.running:
            try:
                current_airport = self.airport_override if self.airport_override else self.current_airport

                if (current_airport and current_airport not in self.mapped_airports):

                    if not self.gsx or not self.gsx.is_initialized:
                        if self.status_callback:
                            self.status_callback("Connecting to GSX system...")
                        time.sleep(0.5)

                        self.gsx = GsxHook(self.config, enable_menu_logging=True)
                        if not self.gsx.is_initialized:
                            logger.error("Failed to initialize GSX Hook for pre-mapping - stopping monitoring")
                            if self.status_callback:
                                self.status_callback("GSX connection failed - monitoring stopped")
                            self.stop()
                            return
                        else:
                            if self.status_callback:
                                self.status_callback("GSX connection established")
                            time.sleep(0.5)

                    if self.gsx and self.gsx.is_initialized and self.gsx.sim_manager.is_on_ground():
                        if self.status_callback:
                            self.status_callback(f"Pre-mapping {current_airport} parking layout...")

                        try:
                            self.gsx.gate_assignment.map_available_spots(current_airport)
                            self.mapped_airports.add(current_airport)
                            logger.info(f"Successfully pre-mapped {current_airport}")
                            if self.status_callback:
                                self.status_callback(f"{current_airport} parking layout ready")
                        except Exception as e:
                            logger.error(f"Failed to pre-map {current_airport}: {e}")
                            if self.status_callback:
                                self.status_callback(f"Pre-mapping failed")

                gate_info = self.gate_queue.get(timeout=1.0)
                logger.info(f"Processing gate assignment: {gate_info}")

                # Initialize GSX if needed
                if not self.gsx or not self.gsx.is_initialized:
                    # Notify UI we're connecting to GSX
                    if self.status_callback:
                        self.status_callback("Connecting to GSX system...")
                    time.sleep(0.5)

                    self.gsx = GsxHook(self.config, enable_menu_logging=True)
                    if not self.gsx.is_initialized:
                        logger.error("Failed to initialize GSX Hook - stopping monitoring")
                        if self.status_callback:
                            self.status_callback("GSX connection failed - monitoring stopped")
                        self.stop()
                        return

                    # Notify UI of successful connection
                    if self.status_callback:
                        self.status_callback("GSX connection established")
                    time.sleep(0.5)

                airport = self.airport_override if self.airport_override else gate_info.get('airport', 'EDDS')

                success, assigned_gate = self.gsx.assign_gate_when_ready(
                    airport=airport,
                    gate_letter=gate_info.get('gate_letter', ""),
                    gate_number=gate_info.get('gate_number', ""),
                    terminal=gate_info.get('terminal', ""),
                    terminal_number=gate_info.get('terminal_number', ""),
                    airline=gate_info.get('airline', 'GSX'),
                    wait_for_ground=True,
                    status_callback=self.status_callback,
                )

                if success and assigned_gate:
                    gate_name = assigned_gate.get('gate', 'Unknown')
                    if assigned_gate.get('_uncertain'):
                        logger.info(f"Gate assignment to {gate_name} might have succeeded - verify in GSX")
                        if self.status_callback:
                            self.status_callback(f"Assigned to {gate_name} (uncertain - verify in GSX)")
                    else:
                        logger.info(f"Successfully assigned to gate: {gate_name}")
                else:
                    logger.info("Gate assignment failed")

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
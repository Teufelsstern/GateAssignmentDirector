import unittest
from unittest.mock import Mock, MagicMock, patch
import queue
import threading
from GateAssignmentDirector.director import GateAssignmentDirector


class TestGateAssignmentDirector(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        with patch('GateAssignmentDirector.director.GADConfig'):
            self.director = GateAssignmentDirector()

    def test_initialization(self):
        """Test director initializes with correct state"""
        self.assertIsNotNone(self.director.gate_queue)
        self.assertIsInstance(self.director.gate_queue, queue.Queue)
        self.assertFalse(self.director.running)
        self.assertIsNone(self.director.current_airport)
        self.assertEqual(self.director.mapped_airports, set())

    def test_queue_gate_assignment(self):
        """Test queueing gate assignment puts item in queue"""
        gate_info = {
            "gate_number": "5",
            "gate_letter": "A",
            "terminal": "1",
            "airport": "KLAX"
        }

        self.director._queue_gate_assignment(gate_info)

        self.assertEqual(self.director.gate_queue.qsize(), 1)
        queued_item = self.director.gate_queue.get()
        self.assertEqual(queued_item["gate_number"], "5")
        self.assertEqual(queued_item["airport"], "KLAX")

    def test_queue_gate_assignment_stores_airport(self):
        """Test queueing gate assignment stores current airport"""
        gate_info = {
            "gate_number": "5",
            "airport": "KJFK"
        }

        self.director._queue_gate_assignment(gate_info)

        self.assertEqual(self.director.current_airport, "KJFK")

    def test_queue_multiple_gates(self):
        """Test queueing multiple gate assignments"""
        gates = [
            {"gate_number": "5", "airport": "KLAX"},
            {"gate_number": "6", "airport": "KLAX"},
            {"gate_number": "7", "airport": "KJFK"}
        ]

        for gate in gates:
            self.director._queue_gate_assignment(gate)

        self.assertEqual(self.director.gate_queue.qsize(), 3)
        self.assertEqual(self.director.current_airport, "KJFK")  # Last one

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.JSONMonitor')
    @patch('threading.Thread')
    def test_start_monitoring(self, mock_thread, mock_monitor, mock_sleep):
        """Test starting monitoring creates monitor and thread"""
        test_path = "test_flight.json"

        self.director.start_monitoring(test_path)

        mock_monitor.assert_called_once()
        mock_thread.assert_called_once()
        self.assertTrue(self.director.running)

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.JSONMonitor')
    @patch('threading.Thread')
    def test_start_monitoring_passes_callback(self, mock_thread, mock_monitor, mock_sleep):
        """Test monitoring setup passes correct callback"""
        test_path = "test_flight.json"
        mock_monitor_instance = Mock()
        mock_monitor.return_value = mock_monitor_instance

        self.director.start_monitoring(test_path)

        call_args = mock_monitor.call_args
        self.assertEqual(call_args[0][0], test_path)
        self.assertFalse(call_args[1]["enable_gsx_integration"])
        self.assertIsNotNone(call_args[1]["gate_callback"])

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_initializes_gsx(self, mock_gsx_hook, mock_sleep):
        """Test processing gate assignment initializes GSX when needed"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True

        def assign_gate_and_stop(*args, **kwargs):
            self.director.running = False
            return (True, {'gate': 'A5'})

        mock_gsx_instance.assign_gate_when_ready.side_effect = assign_gate_and_stop
        mock_gsx_hook.return_value = mock_gsx_instance

        # Add gate to queue
        self.director.gate_queue.put({
            "gate_number": "5",
            "gate_letter": "A",
            "airport": "KLAX"
        })

        # Run one iteration
        self.director.running = True
        self.director.process_gate_assignments()

        # GSX should have been initialized
        mock_gsx_hook.assert_called_once()

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_calls_assign_gate(self, mock_gsx_hook, mock_sleep):
        """Test processing calls assign_gate_when_ready with correct params"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True

        def assign_gate_and_stop(*args, **kwargs):
            self.director.running = False
            return (True, {'gate': 'A5'})

        mock_gsx_instance.assign_gate_when_ready.side_effect = assign_gate_and_stop
        mock_gsx_hook.return_value = mock_gsx_instance

        gate_info = {
            "gate_number": "5",
            "gate_letter": "A",
            "terminal": "1",
            "terminal_number": "2",
            "airport": "KLAX",
            "airline": "United"
        }
        self.director.gate_queue.put(gate_info)

        self.director.running = True
        self.director.process_gate_assignments()

        # Check assign_gate_when_ready was called with correct params
        mock_gsx_instance.assign_gate_when_ready.assert_called_once()
        call_kwargs = mock_gsx_instance.assign_gate_when_ready.call_args[1]
        self.assertEqual(call_kwargs["airport"], "KLAX")
        self.assertEqual(call_kwargs["gate_number"], "5")
        self.assertEqual(call_kwargs["gate_letter"], "A")

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_handles_empty_queue(self, mock_gsx_hook, mock_sleep):
        """Test processing handles empty queue gracefully"""
        # Queue is empty, should timeout and continue
        self.director.running = True

        def stop_quickly():
            self.director.running = False

        stop_thread = threading.Thread(target=stop_quickly)
        stop_thread.start()

        # Should not raise exception
        self.director.process_gate_assignments()
        stop_thread.join()

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_gsx_init_failure(self, mock_gsx_hook, mock_sleep):
        """Test processing handles GSX initialization failure"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = False
        mock_gsx_hook.return_value = mock_gsx_instance

        gate_info = {"gate_number": "5", "airport": "KLAX"}
        self.director.gate_queue.put(gate_info)

        self.director.running = True

        def stop_after_one():
            self.director.running = False

        stop_thread = threading.Thread(target=stop_after_one)
        stop_thread.start()

        self.director.process_gate_assignments()
        stop_thread.join()

        # assign_gate_when_ready should not be called if init failed
        mock_gsx_instance.assign_gate_when_ready.assert_not_called()

    def test_stop_sets_running_false(self):
        """Test stop method sets running flag to False"""
        self.director.running = True
        self.director.gsx = Mock()

        self.director.stop()

        self.assertFalse(self.director.running)

    def test_stop_closes_gsx(self):
        """Test stop method closes GSX connection"""
        mock_gsx = Mock()
        self.director.gsx = mock_gsx

        self.director.stop()

        mock_gsx.close.assert_called_once()

    def test_stop_without_gsx(self):
        """Test stop method works when GSX not initialized"""
        self.director.gsx = None
        self.director.running = True

        # Should not raise exception
        self.director.stop()

        self.assertFalse(self.director.running)

    @patch('GateAssignmentDirector.director.time.sleep')
    def test_multiple_gate_assignments_in_sequence(self, mock_sleep):
        """Test processing multiple gate assignments sequentially"""
        mock_gsx = Mock()
        mock_gsx.is_initialized = True

        call_count = [0]

        def assign_gate_and_stop(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 3:
                self.director.running = False
            return (True, {'gate': 'A5'})

        mock_gsx.assign_gate_when_ready.side_effect = assign_gate_and_stop
        self.director.gsx = mock_gsx

        # Queue multiple gates
        gates = [
            {"gate_number": "5", "airport": "KLAX"},
            {"gate_number": "6", "airport": "KLAX"},
            {"gate_number": "7", "airport": "KJFK"}
        ]

        for gate in gates:
            self.director.gate_queue.put(gate)

        self.director.running = True
        self.director.process_gate_assignments()

        # Should have processed all 3 gates
        self.assertEqual(mock_gsx.assign_gate_when_ready.call_count, 3)

    def test_update_flight_data_stores_data(self):
        """Test _update_flight_data stores complete flight data dict"""
        flight_data = {
            'airport': 'KLAX',
            'departure_airport': 'KJFK',
            'airline': 'Delta',
            'flight_number': 'DL456',
            'assigned_gate': 'Terminal 5 Gate 12'
        }

        self.director._update_flight_data(flight_data)

        self.assertEqual(self.director.current_flight_data, flight_data)

    def test_update_flight_data_updates_current_airport(self):
        """Test _update_flight_data updates current_airport from flight data"""
        flight_data = {
            'airport': 'EDDS',
            'airline': 'Lufthansa',
            'flight_number': 'LH123'
        }

        self.director._update_flight_data(flight_data)

        self.assertEqual(self.director.current_airport, 'EDDS')

    def test_update_flight_data_no_airport(self):
        """Test _update_flight_data handles missing airport field gracefully"""
        flight_data = {
            'airline': 'United',
            'flight_number': 'UA789'
        }

        self.director._update_flight_data(flight_data)

        self.assertEqual(self.director.current_flight_data, flight_data)
        self.assertIsNone(self.director.current_airport)

    def test_airport_override_initialization(self):
        """Test director initializes with no airport override"""
        self.assertIsNone(self.director.airport_override)

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_airport_override_takes_precedence_over_gate_info(self, mock_gsx_hook, mock_sleep):
        """Test airport override is used instead of gate_info airport"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True

        def assign_gate_and_stop(*args, **kwargs):
            self.director.running = False
            return (True, {'gate': 'A5'})

        mock_gsx_instance.assign_gate_when_ready.side_effect = assign_gate_and_stop
        mock_gsx_hook.return_value = mock_gsx_instance

        gate_info = {
            "gate_number": "5",
            "gate_letter": "A",
            "airport": "KLAX"
        }
        self.director.gate_queue.put(gate_info)
        self.director.airport_override = "KJFK"

        self.director.running = True
        self.director.process_gate_assignments()

        call_kwargs = mock_gsx_instance.assign_gate_when_ready.call_args[1]
        self.assertEqual(call_kwargs["airport"], "KJFK")

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_gate_info_airport_used_when_no_override(self, mock_gsx_hook, mock_sleep):
        """Test gate_info airport is used when override is None"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True

        def assign_gate_and_stop(*args, **kwargs):
            self.director.running = False
            return (True, {'gate': 'A5'})

        mock_gsx_instance.assign_gate_when_ready.side_effect = assign_gate_and_stop
        mock_gsx_hook.return_value = mock_gsx_instance

        gate_info = {
            "gate_number": "5",
            "gate_letter": "A",
            "airport": "KLAX"
        }
        self.director.gate_queue.put(gate_info)
        self.director.airport_override = None

        self.director.running = True
        self.director.process_gate_assignments()

        call_kwargs = mock_gsx_instance.assign_gate_when_ready.call_args[1]
        self.assertEqual(call_kwargs["airport"], "KLAX")

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_airport_override_with_automatic_detection(self, mock_gsx_hook, mock_sleep):
        """Test override works with automatic gate detection through queue"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True

        call_count = [0]

        def assign_gate_and_stop(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 2:
                self.director.running = False
            return (True, {'gate': 'A5'})

        mock_gsx_instance.assign_gate_when_ready.side_effect = assign_gate_and_stop
        mock_gsx_hook.return_value = mock_gsx_instance

        gates = [
            {"gate_number": "5", "airport": "KLAX"},
            {"gate_number": "6", "airport": "EDDF"}
        ]

        for gate in gates:
            self.director.gate_queue.put(gate)

        self.director.airport_override = "KJFK"
        self.director.running = True
        self.director.process_gate_assignments()

        self.assertEqual(mock_gsx_instance.assign_gate_when_ready.call_count, 2)
        for call in mock_gsx_instance.assign_gate_when_ready.call_args_list:
            self.assertEqual(call[1]["airport"], "KJFK")

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_handles_uncertain_result(self, mock_gsx_hook, mock_sleep):
        """Test processing handles uncertain gate assignment result"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True

        def assign_gate_uncertain(*args, **kwargs):
            self.director.running = False
            return (True, {'gate': 'A5', '_uncertain': True})

        mock_gsx_instance.assign_gate_when_ready.side_effect = assign_gate_uncertain
        mock_gsx_hook.return_value = mock_gsx_instance

        gate_info = {
            "gate_number": "5",
            "gate_letter": "A",
            "airport": "KLAX"
        }
        self.director.gate_queue.put(gate_info)

        self.director.running = True
        self.director.process_gate_assignments()

        mock_gsx_instance.assign_gate_when_ready.assert_called_once()

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_pre_mapping_triggers_when_on_ground_with_airport(self, mock_gsx_hook, mock_sleep):
        """Test pre-mapping triggers when aircraft is on ground with airport set"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.sim_manager.is_on_ground.return_value = True
        mock_gsx_instance.gate_assignment.map_available_spots.return_value = {"terminals": {}}

        def stop_after_mapping(*args, **kwargs):
            self.director.running = False

        mock_gsx_instance.gate_assignment.map_available_spots.side_effect = stop_after_mapping
        mock_gsx_hook.return_value = mock_gsx_instance

        self.director.current_airport = "EDDF"
        self.director.running = True
        self.director.process_gate_assignments()

        mock_gsx_instance.gate_assignment.map_available_spots.assert_called_once_with("EDDF")
        self.assertIn("EDDF", self.director.mapped_airports)

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_pre_mapping_not_triggered_when_not_on_ground(self, mock_gsx_hook, mock_sleep):
        """Test pre-mapping does not trigger when aircraft is not on ground"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.sim_manager.is_on_ground.return_value = False

        def stop_quickly():
            self.director.running = False

        stop_thread = threading.Thread(target=stop_quickly)
        mock_gsx_hook.return_value = mock_gsx_instance

        self.director.current_airport = "EDDF"
        self.director.running = True

        stop_thread.start()
        self.director.process_gate_assignments()
        stop_thread.join()

        mock_gsx_instance.gate_assignment.map_available_spots.assert_not_called()
        self.assertNotIn("EDDF", self.director.mapped_airports)

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_pre_mapping_not_triggered_when_no_airport(self, mock_gsx_hook, mock_sleep):
        """Test pre-mapping does not trigger when airport is not set"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.sim_manager.is_on_ground.return_value = True

        def stop_quickly():
            self.director.running = False

        stop_thread = threading.Thread(target=stop_quickly)
        mock_gsx_hook.return_value = mock_gsx_instance

        self.director.current_airport = None
        self.director.running = True

        stop_thread.start()
        self.director.process_gate_assignments()
        stop_thread.join()

        mock_gsx_instance.gate_assignment.map_available_spots.assert_not_called()

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_pre_mapping_not_triggered_when_already_mapped(self, mock_gsx_hook, mock_sleep):
        """Test pre-mapping does not trigger when airport already mapped"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.sim_manager.is_on_ground.return_value = True

        def stop_quickly():
            self.director.running = False

        stop_thread = threading.Thread(target=stop_quickly)
        mock_gsx_hook.return_value = mock_gsx_instance

        self.director.current_airport = "EDDF"
        self.director.mapped_airports.add("EDDF")
        self.director.running = True

        stop_thread.start()
        self.director.process_gate_assignments()
        stop_thread.join()

        mock_gsx_instance.gate_assignment.map_available_spots.assert_not_called()

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_mapped_airports_prevents_duplicate_mapping(self, mock_gsx_hook, mock_sleep):
        """Test mapped_airports set prevents duplicate pre-mapping"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.sim_manager.is_on_ground.return_value = True

        call_count = [0]

        def count_calls(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 1:
                self.director.running = False

        mock_gsx_instance.gate_assignment.map_available_spots.side_effect = count_calls
        mock_gsx_hook.return_value = mock_gsx_instance

        self.director.current_airport = "EDDF"
        self.director.running = True
        self.director.process_gate_assignments()

        self.assertEqual(mock_gsx_instance.gate_assignment.map_available_spots.call_count, 1)
        self.assertIn("EDDF", self.director.mapped_airports)

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_pre_mapping_initializes_gsx_when_needed(self, mock_gsx_hook, mock_sleep):
        """Test pre-mapping initializes GSX when not yet initialized"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.sim_manager.is_on_ground.return_value = True

        def stop_after_init(*args, **kwargs):
            self.director.running = False

        mock_gsx_instance.gate_assignment.map_available_spots.side_effect = stop_after_init
        mock_gsx_hook.return_value = mock_gsx_instance

        self.director.gsx = None
        self.director.current_airport = "EDDF"
        self.director.running = True
        self.director.process_gate_assignments()

        mock_gsx_hook.assert_called_once()
        mock_gsx_instance.gate_assignment.map_available_spots.assert_called_once_with("EDDF")

    @patch('GateAssignmentDirector.director.time.sleep')
    @patch('GateAssignmentDirector.director.GsxHook')
    def test_pre_mapping_handles_mapping_failure_gracefully(self, mock_gsx_hook, mock_sleep):
        """Test pre-mapping handles errors gracefully and continues"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.sim_manager.is_on_ground.return_value = True
        mock_gsx_instance.gate_assignment.map_available_spots.side_effect = Exception("Mapping failed")

        def stop_quickly():
            self.director.running = False

        stop_thread = threading.Thread(target=stop_quickly)
        mock_gsx_hook.return_value = mock_gsx_instance

        self.director.current_airport = "EDDF"
        self.director.running = True

        stop_thread.start()
        self.director.process_gate_assignments()
        stop_thread.join()

        self.assertNotIn("EDDF", self.director.mapped_airports)

    def test_airport_override_persists_across_flight_data_updates(self):
        """Test airport override persists through multiple _update_flight_data calls"""
        # Set initial airport and override
        self.director.airport_override = "EDDF"
        self.director.current_airport = "EDDF"
        self.director.departure_airport = "EDDF"

        # Simulate multiple polling cycles with different airport data
        polling_data = [
            {'airport': 'KJFK', 'departure_airport': 'KLAX', 'airline': 'United'},
            {'airport': 'KLAX', 'departure_airport': 'KSFO', 'airline': 'Delta'},
            {'airport': 'KSEA', 'departure_airport': 'KPDX', 'airline': 'Alaska'},
        ]

        for flight_data in polling_data:
            self.director._update_flight_data(flight_data)

            # Verify airports remain unchanged despite different flight data
            self.assertEqual(self.director.current_airport, "EDDF")
            self.assertEqual(self.director.departure_airport, "EDDF")
            # But flight data itself should still update
            self.assertEqual(self.director.current_flight_data, flight_data)

    def test_airport_override_when_cleared_allows_updates(self):
        """Test airports update from flight data when override is cleared"""
        # Start with override active
        self.director.airport_override = "EDDF"
        self.director.current_airport = "EDDF"
        self.director.departure_airport = "EDDF"

        # Update with different data - should be ignored
        first_data = {'airport': 'KJFK', 'departure_airport': 'KLAX'}
        self.director._update_flight_data(first_data)

        self.assertEqual(self.director.current_airport, "EDDF")
        self.assertEqual(self.director.departure_airport, "EDDF")

        # Clear the override
        self.director.airport_override = None

        # Now updates should work
        second_data = {'airport': 'KSEA', 'departure_airport': 'KPDX'}
        self.director._update_flight_data(second_data)

        self.assertEqual(self.director.current_airport, "KSEA")
        self.assertEqual(self.director.departure_airport, "KPDX")

    def test_airport_override_updates_departure_airport(self):
        """Test both current_airport and departure_airport protected by override"""
        self.director.airport_override = "EGLL"
        self.director.current_airport = "EGLL"
        self.director.departure_airport = "EGLL"

        # Try to update with completely different airports
        flight_data = {
            'airport': 'RJTT',
            'departure_airport': 'RJAA',
            'airline': 'JAL',
            'flight_number': 'JL123'
        }

        self.director._update_flight_data(flight_data)

        # Both should remain unchanged
        self.assertEqual(self.director.current_airport, "EGLL")
        self.assertEqual(self.director.departure_airport, "EGLL")

    def test_airport_override_none_allows_initial_setting(self):
        """Test that when override is None, airports can be set from flight data"""
        # Start with no override and no airports
        self.director.airport_override = None
        self.director.current_airport = None
        self.director.departure_airport = None

        flight_data = {
            'airport': 'LFPG',
            'departure_airport': 'LFPO',
            'airline': 'Air France'
        }

        self.director._update_flight_data(flight_data)

        self.assertEqual(self.director.current_airport, "LFPG")
        self.assertEqual(self.director.departure_airport, "LFPO")


if __name__ == "__main__":
    unittest.main()
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

    @patch('GateAssignmentDirector.director.JSONMonitor')
    @patch('threading.Thread')
    def test_start_monitoring(self, mock_thread, mock_monitor):
        """Test starting monitoring creates monitor and thread"""
        test_path = "test_flight.json"

        self.director.start_monitoring(test_path)

        mock_monitor.assert_called_once()
        mock_thread.assert_called_once()
        self.assertTrue(self.director.running)

    @patch('GateAssignmentDirector.director.JSONMonitor')
    @patch('threading.Thread')
    def test_start_monitoring_passes_callback(self, mock_thread, mock_monitor):
        """Test monitoring setup passes correct callback"""
        test_path = "test_flight.json"
        mock_monitor_instance = Mock()
        mock_monitor.return_value = mock_monitor_instance

        self.director.start_monitoring(test_path)

        call_args = mock_monitor.call_args
        self.assertEqual(call_args[0][0], test_path)
        self.assertFalse(call_args[1]["enable_gsx_integration"])
        self.assertIsNotNone(call_args[1]["gate_callback"])

    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_initializes_gsx(self, mock_gsx_hook):
        """Test processing gate assignment initializes GSX when needed"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.assign_gate_when_ready.return_value = True
        mock_gsx_hook.return_value = mock_gsx_instance

        # Add gate to queue
        self.director.gate_queue.put({
            "gate_number": "5",
            "gate_letter": "A",
            "airport": "KLAX"
        })

        # Run one iteration
        self.director.running = True

        def stop_after_one():
            # Let it process one item then stop
            import time
            time.sleep(0.2)
            self.director.running = False

        stop_thread = threading.Thread(target=stop_after_one)
        stop_thread.start()

        self.director.process_gate_assignments()
        stop_thread.join()

        # GSX should have been initialized
        mock_gsx_hook.assert_called_once()

    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_calls_assign_gate(self, mock_gsx_hook):
        """Test processing calls assign_gate_when_ready with correct params"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = True
        mock_gsx_instance.assign_gate_when_ready.return_value = True
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

        def stop_after_one():
            import time
            time.sleep(0.2)
            self.director.running = False

        stop_thread = threading.Thread(target=stop_after_one)
        stop_thread.start()

        self.director.process_gate_assignments()
        stop_thread.join()

        # Check assign_gate_when_ready was called with correct params
        mock_gsx_instance.assign_gate_when_ready.assert_called_once()
        call_kwargs = mock_gsx_instance.assign_gate_when_ready.call_args[1]
        self.assertEqual(call_kwargs["airport"], "KLAX")
        self.assertEqual(call_kwargs["gate_number"], "5")
        self.assertEqual(call_kwargs["gate_letter"], "A")

    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_handles_empty_queue(self, mock_gsx_hook):
        """Test processing handles empty queue gracefully"""
        # Queue is empty, should timeout and continue
        self.director.running = True

        def stop_quickly():
            import time
            time.sleep(0.1)
            self.director.running = False

        stop_thread = threading.Thread(target=stop_quickly)
        stop_thread.start()

        # Should not raise exception
        self.director.process_gate_assignments()
        stop_thread.join()

    @patch('GateAssignmentDirector.director.GsxHook')
    def test_process_gate_assignments_gsx_init_failure(self, mock_gsx_hook):
        """Test processing handles GSX initialization failure"""
        mock_gsx_instance = Mock()
        mock_gsx_instance.is_initialized = False
        mock_gsx_hook.return_value = mock_gsx_instance

        gate_info = {"gate_number": "5", "airport": "KLAX"}
        self.director.gate_queue.put(gate_info)

        self.director.running = True

        def stop_after_one():
            import time
            time.sleep(0.2)
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

    def test_multiple_gate_assignments_in_sequence(self):
        """Test processing multiple gate assignments sequentially"""
        mock_gsx = Mock()
        mock_gsx.is_initialized = True
        mock_gsx.assign_gate_when_ready.return_value = True
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

        def stop_after_processing():
            import time
            time.sleep(0.5)  # Give time to process all 3
            self.director.running = False

        stop_thread = threading.Thread(target=stop_after_processing)
        stop_thread.start()

        self.director.process_gate_assignments()
        stop_thread.join()

        # Should have processed all 3 gates
        self.assertEqual(mock_gsx.assign_gate_when_ready.call_count, 3)


if __name__ == "__main__":
    unittest.main()
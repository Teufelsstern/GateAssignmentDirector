import unittest
from unittest.mock import Mock, patch, MagicMock
from GateAssignmentDirector.simconnect_manager import SimConnectManager
from GateAssignmentDirector.exceptions import GsxConnectionError


class TestSimConnectManager(unittest.TestCase):
    """Test suite for SimConnectManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock()
        self.mock_config.aircraft_request_interval = 2000
        self.mock_config.ground_check_interval = 1000

    @patch('GateAssignmentDirector.simconnect_manager.SimConnect')
    @patch('GateAssignmentDirector.simconnect_manager.AircraftRequests')
    @patch('GateAssignmentDirector.simconnect_manager.Request')
    def test_connect_success(self, mock_request, mock_aircraft_requests, mock_simconnect):
        """Test successful SimConnect connection"""
        manager = SimConnectManager(self.mock_config)

        result = manager.connect()

        self.assertTrue(result)
        mock_simconnect.assert_called_once()
        mock_aircraft_requests.assert_called_once()
        mock_request.assert_called_once()
        self.assertIsNotNone(manager.connection)
        self.assertIsNotNone(manager.aircraft_requests)
        self.assertIsNotNone(manager.ground_check_request)

    @patch('GateAssignmentDirector.simconnect_manager.SimConnect')
    def test_connect_failure_raises_exception(self, mock_simconnect):
        """Test connection failure raises GsxConnectionError"""
        mock_simconnect.side_effect = ConnectionError("Connection failed")
        manager = SimConnectManager(self.mock_config)

        with self.assertRaises(GsxConnectionError) as context:
            manager.connect()

        self.assertIn("SimConnect connection failed", str(context.exception))

    @patch('GateAssignmentDirector.simconnect_manager.SimConnect')
    @patch('GateAssignmentDirector.simconnect_manager.AircraftRequests')
    @patch('GateAssignmentDirector.simconnect_manager.Request')
    def test_disconnect(self, mock_request, mock_aircraft_requests, mock_simconnect):
        """Test disconnecting from SimConnect"""
        manager = SimConnectManager(self.mock_config)
        manager.connect()

        manager.disconnect()

        self.assertIsNone(manager.connection)

    @patch('GateAssignmentDirector.simconnect_manager.SimConnect')
    @patch('GateAssignmentDirector.simconnect_manager.AircraftRequests')
    @patch('GateAssignmentDirector.simconnect_manager.Request')
    def test_is_on_ground_true(self, mock_request_class, mock_aircraft_requests, mock_simconnect):
        """Test is_on_ground returns True when aircraft on ground"""
        manager = SimConnectManager(self.mock_config)
        manager.connect()

        # Mock the ground check request's value
        manager.ground_check_request.value = True

        result = manager.is_on_ground()

        self.assertTrue(result)

    @patch('GateAssignmentDirector.simconnect_manager.SimConnect')
    @patch('GateAssignmentDirector.simconnect_manager.AircraftRequests')
    @patch('GateAssignmentDirector.simconnect_manager.Request')
    def test_is_on_ground_false(self, mock_request_class, mock_aircraft_requests, mock_simconnect):
        """Test is_on_ground returns False when aircraft in air"""
        manager = SimConnectManager(self.mock_config)
        manager.connect()

        manager.ground_check_request.value = False

        result = manager.is_on_ground()

        self.assertFalse(result)

    @patch('GateAssignmentDirector.simconnect_manager.SimConnect')
    @patch('GateAssignmentDirector.simconnect_manager.AircraftRequests')
    @patch('GateAssignmentDirector.simconnect_manager.Request')
    def test_create_request(self, mock_request_class, mock_aircraft_requests, mock_simconnect):
        """Test creating a SimConnect request"""
        manager = SimConnectManager(self.mock_config)
        manager.connect()

        mock_request_class.reset_mock()

        result = manager.create_request(b"L:TEST_VAR", b"Number", settable=True)

        mock_request_class.assert_called_once_with(
            (b"L:TEST_VAR", b"Number"),
            manager.connection,
            _settable=True,
            _time=1000
        )

    @patch('GateAssignmentDirector.simconnect_manager.SimConnect')
    @patch('GateAssignmentDirector.simconnect_manager.AircraftRequests')
    @patch('GateAssignmentDirector.simconnect_manager.Request')
    def test_set_variable_success(self, mock_request_class, mock_aircraft_requests, mock_simconnect):
        """Test successfully setting a SimConnect variable"""
        manager = SimConnectManager(self.mock_config)
        manager.connect()

        mock_request = Mock()
        mock_request_class.return_value = mock_request

        result = manager.set_variable(b"L:TEST_VAR", 42.0)

        self.assertTrue(result)
        self.assertEqual(mock_request.value, 42.0)

    @patch('GateAssignmentDirector.simconnect_manager.SimConnect')
    @patch('GateAssignmentDirector.simconnect_manager.AircraftRequests')
    @patch('GateAssignmentDirector.simconnect_manager.Request')
    def test_set_variable_failure(self, mock_request_class, mock_aircraft_requests, mock_simconnect):
        """Test set_variable returns False on failure"""
        manager = SimConnectManager(self.mock_config)
        manager.connect()

        mock_request_class.side_effect = RuntimeError("Request failed")

        result = manager.set_variable(b"L:TEST_VAR", 42.0)

        self.assertFalse(result)

    @patch('GateAssignmentDirector.simconnect_manager.logger')
    def test_set_variable_no_connection_returns_false(self, mock_logger):
        """Test set_variable returns False when connection is None"""
        manager = SimConnectManager(self.mock_config)

        result = manager.set_variable(b"L:TEST_VAR", 42.0)

        self.assertFalse(result)

    @patch('GateAssignmentDirector.simconnect_manager.logger')
    def test_set_variable_no_connection_no_exception(self, mock_logger):
        """Test set_variable does not raise exception when connection is None"""
        manager = SimConnectManager(self.mock_config)

        try:
            manager.set_variable(b"L:TEST_VAR", 42.0)
        except Exception as e:
            self.fail(f"set_variable raised unexpected exception: {e}")

    @patch('GateAssignmentDirector.simconnect_manager.logger')
    def test_set_variable_no_connection_logs_debug(self, mock_logger):
        """Test set_variable logs debug message when connection is None"""
        manager = SimConnectManager(self.mock_config)

        manager.set_variable(b"L:TEST_VAR", 42.0)

        mock_logger.debug.assert_called_once_with(
            "Cannot set variable b'L:TEST_VAR': No SimConnect connection"
        )

    def test_initialization(self):
        """Test manager initializes with correct defaults"""
        manager = SimConnectManager(self.mock_config)

        self.assertIsNone(manager.connection)
        self.assertIsNone(manager.aircraft_requests)
        self.assertIsNone(manager.ground_check_request)
        self.assertEqual(manager.config, self.mock_config)


if __name__ == "__main__":
    unittest.main()
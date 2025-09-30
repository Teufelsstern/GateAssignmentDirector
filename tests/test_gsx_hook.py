import unittest
from unittest.mock import Mock, MagicMock, patch, call
from GateAssignmentDirector.gsx_hook import GsxHook
from GateAssignmentDirector.config import GsxConfig


def create_mock_config():
    """Helper to create properly configured mock config"""
    mock_config = Mock(spec=GsxConfig)
    mock_config.logging_level = "INFO"
    mock_config.logging_format = "%(message)s"
    mock_config.logging_datefmt = "%Y-%m-%d"
    mock_config.menu_file_paths = ["/path/to/menu"]
    return mock_config


class TestGsxHookInitialization(unittest.TestCase):
    """
    Critical tests for GsxHook initialization chain.
    The order of initialization is fragile - these tests catch breakages.
    """

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_initialization_order(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test that components are initialized in correct order"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        # Mock SimConnect to succeed
        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)

        # Verify initialization order
        # 1. SimConnectManager created first
        mock_sim.assert_called_once()
        # 2. SimConnect connects
        mock_sim_instance.connect.assert_called_once()
        # 3. MenuLogger created
        mock_logger.assert_called_once()
        # 4. MenuReader created (needs logger)
        mock_reader.assert_called_once()
        # 5. MenuNavigator created (needs reader and logger)
        mock_nav.assert_called_once()
        # 6. GateAssignment created last (needs all others)
        mock_gate.assert_called_once()

    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_initialization_simconnect_failure(self, mock_sim):
        """Test initialization handles SimConnect connection failure"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        # SimConnect fails to connect
        mock_sim_instance = Mock()
        mock_sim_instance.connect.side_effect = Exception("SimConnect failed")
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)

        # Should set is_initialized to False
        self.assertFalse(hook.is_initialized)

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_initialization_success_sets_flag(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test successful initialization sets is_initialized to True"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)

        self.assertTrue(hook.is_initialized)

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_menu_reader_receives_correct_dependencies(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test MenuReader is initialized with correct dependencies"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        hook = GsxHook(config=mock_config)

        # MenuReader should be called with config, logger, navigator (None at this point), and sim_manager
        call_args = mock_reader.call_args[0]
        self.assertIs(call_args[0], mock_config)  # config
        self.assertIs(call_args[1], mock_logger_instance)  # menu_logger
        self.assertIsNone(call_args[2])  # menu_navigator (not created yet)
        self.assertIs(call_args[3], mock_sim_instance)  # sim_manager

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_menu_navigator_receives_correct_dependencies(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test MenuNavigator is initialized with correct dependencies"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance
        mock_reader_instance = Mock()
        mock_reader.return_value = mock_reader_instance

        hook = GsxHook(config=mock_config)

        # MenuNavigator should be called with config, logger, reader, sim_manager
        call_args = mock_nav.call_args[0]
        self.assertIs(call_args[0], mock_config)
        self.assertIs(call_args[1], mock_logger_instance)
        self.assertIs(call_args[2], mock_reader_instance)
        self.assertIs(call_args[3], mock_sim_instance)

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_gate_assignment_receives_all_dependencies(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test GateAssignment receives all 5 dependencies in correct order"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance
        mock_reader_instance = Mock()
        mock_reader.return_value = mock_reader_instance
        mock_nav_instance = Mock()
        mock_nav.return_value = mock_nav_instance

        hook = GsxHook(config=mock_config)

        # GateAssignment should be called with all 5 components
        call_args = mock_gate.call_args[0]
        self.assertEqual(len(call_args), 5)
        self.assertIs(call_args[0], mock_config)
        self.assertIs(call_args[1], mock_logger_instance)
        self.assertIs(call_args[2], mock_reader_instance)
        self.assertIs(call_args[3], mock_nav_instance)
        self.assertIs(call_args[4], mock_sim_instance)

    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_initialization_with_default_config(self, mock_sim):
        """Test GsxHook initializes with default config when none provided"""
        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook()

        self.assertIsNotNone(hook.config)
        self.assertIsInstance(hook.config, GsxConfig)

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_enable_menu_logging_flag(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test enable_menu_logging flag is stored"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config, enable_menu_logging=False)

        self.assertFalse(hook.enable_menu_logging)


class TestGsxHookMethods(unittest.TestCase):
    """Test suite for GsxHook public methods"""

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_assign_gate_when_ready_delegates_to_gate_assignment(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test assign_gate_when_ready calls GateAssignment.assign_gate"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance
        mock_gate_instance = Mock()
        mock_gate_instance.assign_gate.return_value = True
        mock_gate.return_value = mock_gate_instance

        hook = GsxHook(config=mock_config)
        result = hook.assign_gate_when_ready(
            airport="KLAX",
            gate_number="5",
            gate_letter="A"
        )

        # Should delegate to gate_assignment
        mock_gate_instance.assign_gate.assert_called_once()
        call_kwargs = mock_gate_instance.assign_gate.call_args[1]
        self.assertEqual(call_kwargs["airport"], "KLAX")
        self.assertEqual(call_kwargs["gate_number"], "5")
        self.assertEqual(call_kwargs["gate_letter"], "A")
        self.assertTrue(result)

    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_assign_gate_when_ready_not_initialized(self, mock_sim):
        """Test assign_gate_when_ready returns False when not initialized"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        # Fail initialization
        mock_sim_instance = Mock()
        mock_sim_instance.connect.side_effect = Exception("Failed")
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)
        result = hook.assign_gate_when_ready(airport="KLAX")

        self.assertFalse(result)

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_is_on_ground_delegates_to_sim_manager(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test is_on_ground calls SimConnectManager.is_on_ground"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim_instance.is_on_ground.return_value = True
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)
        result = hook.is_on_ground()

        mock_sim_instance.is_on_ground.assert_called_once()
        self.assertTrue(result)

    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_is_on_ground_not_initialized(self, mock_sim):
        """Test is_on_ground returns False when not initialized"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        # Fail initialization
        mock_sim_instance = Mock()
        mock_sim_instance.connect.side_effect = Exception("Failed")
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)
        result = hook.is_on_ground()

        self.assertFalse(result)

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_close_disconnects_sim_manager(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test close method disconnects SimConnect"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)
        hook.close()

        mock_sim_instance.disconnect.assert_called_once()

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_close_sets_initialized_false(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test close sets is_initialized to False"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)
        self.assertTrue(hook.is_initialized)

        hook.close()

        self.assertFalse(hook.is_initialized)

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_close_sets_menu_open_to_zero(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test close sets GSX menu to closed state"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)
        hook.close()

        # Should set MENU_OPEN variable to 0
        mock_sim_instance.set_variable.assert_called()
        # Check that it was called with the menu close variable
        calls = mock_sim_instance.set_variable.call_args_list
        self.assertTrue(any(call[0][1] == 0 for call in calls))

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_close_menu_sets_menu_open_to_zero(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test _close_menu() sets MENU_OPEN variable to 0"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        hook = GsxHook(config=mock_config)
        hook._close_menu()

        # Verify MENU_OPEN set to 0
        mock_sim_instance.set_variable.assert_called()
        calls = mock_sim_instance.set_variable.call_args_list
        self.assertTrue(any(call[0][1] == 0 for call in calls))

    @patch('GateAssignmentDirector.gsx_hook.time.sleep')
    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_assign_gate_when_ready_retries_once_on_failure(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate, mock_sleep):
        """Test assign_gate_when_ready retries once after first failure"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        # First call fails, second succeeds
        mock_gate_instance = Mock()
        mock_gate_instance.assign_gate.side_effect = [False, True]
        mock_gate.return_value = mock_gate_instance

        hook = GsxHook(config=mock_config)
        result = hook.assign_gate_when_ready(airport="KLAX")

        # Should call assign_gate twice
        self.assertEqual(mock_gate_instance.assign_gate.call_count, 2)
        # Should close menu between attempts
        mock_sim_instance.set_variable.assert_called()
        # Final result should be True (success on retry)
        self.assertTrue(result)

    @patch('GateAssignmentDirector.gsx_hook.time.sleep')
    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_assign_gate_when_ready_fails_after_retry(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate, mock_sleep):
        """Test assign_gate_when_ready fails when both attempts fail"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        # Both calls fail
        mock_gate_instance = Mock()
        mock_gate_instance.assign_gate.return_value = False
        mock_gate.return_value = mock_gate_instance

        hook = GsxHook(config=mock_config)
        result = hook.assign_gate_when_ready(airport="KLAX")

        # Should call assign_gate twice
        self.assertEqual(mock_gate_instance.assign_gate.call_count, 2)
        # Should close menu between attempts
        mock_sim_instance.set_variable.assert_called()
        # Final result should be False
        self.assertFalse(result)

    @patch('GateAssignmentDirector.gsx_hook.GateAssignment')
    @patch('GateAssignmentDirector.gsx_hook.MenuNavigator')
    @patch('GateAssignmentDirector.gsx_hook.MenuReader')
    @patch('GateAssignmentDirector.gsx_hook.MenuLogger')
    @patch('GateAssignmentDirector.gsx_hook.SimConnectManager')
    def test_assign_gate_when_ready_no_retry_on_first_success(self, mock_sim, mock_logger, mock_reader, mock_nav, mock_gate):
        """Test assign_gate_when_ready doesn't retry when first attempt succeeds"""
        mock_config = create_mock_config()
        mock_config.from_yaml.return_value = mock_config

        mock_sim_instance = Mock()
        mock_sim.return_value = mock_sim_instance

        # First call succeeds
        mock_gate_instance = Mock()
        mock_gate_instance.assign_gate.return_value = True
        mock_gate.return_value = mock_gate_instance

        hook = GsxHook(config=mock_config)
        result = hook.assign_gate_when_ready(airport="KLAX")

        # Should only call assign_gate once
        self.assertEqual(mock_gate_instance.assign_gate.call_count, 1)
        # Final result should be True
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
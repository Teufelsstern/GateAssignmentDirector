import unittest
from unittest.mock import Mock, patch, mock_open, call
from pathlib import Path
import yaml
from GateAssignmentDirector.gad_config import GADConfig


class TestGADConfigDefaults(unittest.TestCase):
    """Test suite for GADConfig default values"""

    def test_get_defaults_returns_complete_dict(self):
        """Test _get_defaults returns all expected keys"""
        defaults = GADConfig._get_defaults()

        expected_keys = {
            'menu_file_paths',
            'sleep_short',
            'sleep_long',
            'ground_check_interval',
            'aircraft_request_interval',
            'max_menu_check_attempts',
            'logging_level',
            'logging_format',
            'logging_datefmt',
            'SI_API_KEY',
            'default_airline',
        }

        self.assertEqual(set(defaults.keys()), expected_keys)

    def test_get_defaults_menu_paths(self):
        """Test _get_defaults returns correct menu file paths"""
        defaults = GADConfig._get_defaults()

        self.assertIsInstance(defaults['menu_file_paths'], list)
        self.assertEqual(len(defaults['menu_file_paths']), 2)
        self.assertIn('x86', defaults['menu_file_paths'][0])
        self.assertNotIn('x86', defaults['menu_file_paths'][1])

    def test_get_defaults_timing_values(self):
        """Test _get_defaults returns correct timing values"""
        defaults = GADConfig._get_defaults()

        self.assertEqual(defaults['sleep_short'], 0.1)
        self.assertEqual(defaults['sleep_long'], 0.3)
        self.assertEqual(defaults['ground_check_interval'], 1.0)
        self.assertEqual(defaults['aircraft_request_interval'], 2.0)

    def test_get_defaults_logging_values(self):
        """Test _get_defaults returns correct logging configuration"""
        defaults = GADConfig._get_defaults()

        self.assertEqual(defaults['logging_level'], 'DEBUG')
        self.assertEqual(defaults['logging_format'], '%(asctime)s - %(levelname)s - %(message)s')
        self.assertEqual(defaults['logging_datefmt'], '%H:%M:%S')

    def test_get_defaults_max_attempts(self):
        """Test _get_defaults returns correct max menu check attempts"""
        defaults = GADConfig._get_defaults()

        self.assertEqual(defaults['max_menu_check_attempts'], 4)

    def test_get_defaults_api_key_placeholder(self):
        """Test _get_defaults returns API key placeholder"""
        defaults = GADConfig._get_defaults()

        self.assertEqual(defaults['SI_API_KEY'], 'YOUR_API_KEY_HERE')

    def test_get_defaults_default_airline(self):
        """Test _get_defaults returns default airline"""
        defaults = GADConfig._get_defaults()

        self.assertEqual(defaults['default_airline'], 'GSX')


class TestGADConfigInitialization(unittest.TestCase):
    """Test suite for GADConfig initialization"""

    def test_initialization_with_all_fields(self):
        """Test creating GADConfig with all fields specified"""
        config = GADConfig(
            menu_file_paths=["path1", "path2"],
            sleep_short=0.2,
            sleep_long=0.5,
            ground_check_interval=2000,
            aircraft_request_interval=3000,
            max_menu_check_attempts=5,
            logging_level='INFO',
            logging_format='%(message)s',
            logging_datefmt='%Y-%m-%d',
            SI_API_KEY='test_key',
            default_airline='TEST'
        )

        self.assertEqual(config.menu_file_paths, ["path1", "path2"])
        self.assertEqual(config.sleep_short, 0.2)
        self.assertEqual(config.sleep_long, 0.5)
        self.assertEqual(config.ground_check_interval, 2000)
        self.assertEqual(config.aircraft_request_interval, 3000)
        self.assertEqual(config.max_menu_check_attempts, 5)
        self.assertEqual(config.logging_level, 'INFO')
        self.assertEqual(config.logging_format, '%(message)s')
        self.assertEqual(config.logging_datefmt, '%Y-%m-%d')
        self.assertEqual(config.SI_API_KEY, 'test_key')
        self.assertEqual(config.default_airline, 'TEST')

    def test_initialization_with_defaults(self):
        """Test creating GADConfig with default values"""
        config = GADConfig()

        self.assertEqual(config.menu_file_paths, [
            r"C:\Program Files (x86)\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu",
            r"C:\Program Files\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu",
        ])
        self.assertEqual(config.sleep_short, 0.1)
        self.assertEqual(config.sleep_long, 0.3)
        self.assertEqual(config.ground_check_interval, 1.0)
        self.assertEqual(config.aircraft_request_interval, 2.0)
        self.assertEqual(config.max_menu_check_attempts, 4)
        self.assertEqual(config.logging_level, 'DEBUG')
        self.assertEqual(config.SI_API_KEY, 'YOUR_API_KEY_HERE')
        self.assertEqual(config.default_airline, 'GSX')

    def test_username_field_populated(self):
        """Test username field is populated from getpass.getuser"""
        config = GADConfig()

        # Username should be populated (actual value depends on system)
        self.assertIsNotNone(config.username)
        self.assertIsInstance(config.username, str)
        self.assertGreater(len(config.username), 0)

    def test_flight_json_path_computed_correctly(self):
        """Test flight_json_path is computed based on username"""
        # Create config with explicit username
        config = GADConfig(username="alice")

        expected_path = r"C:\Users\alice\AppData\Local\SayIntentionsAI\flight.json"
        self.assertEqual(config.flight_json_path, expected_path)

    def test_flight_json_path_with_different_username(self):
        """Test flight_json_path computed correctly for different username"""
        # Create config with explicit username
        config = GADConfig(username="bob_smith")

        expected_path = r"C:\Users\bob_smith\AppData\Local\SayIntentionsAI\flight.json"
        self.assertEqual(config.flight_json_path, expected_path)

    def test_flight_json_path_uses_system_username_by_default(self):
        """Test flight_json_path uses actual system username when not specified"""
        config = GADConfig()

        # Should contain the username in the path
        self.assertIn("C:\\Users\\", config.flight_json_path)
        self.assertIn("\\AppData\\Local\\SayIntentionsAI\\flight.json", config.flight_json_path)
        self.assertIn(config.username, config.flight_json_path)


class TestGADConfigFromYaml(unittest.TestCase):
    """Test suite for GADConfig.from_yaml() method"""

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.Path')
    @patch('GateAssignmentDirector.gad_config.yaml.safe_load')
    def test_from_yaml_existing_file(self, mock_yaml_load, mock_path, mock_file):
        """Test loading configuration from existing YAML file"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        yaml_data = {
            'menu_file_paths': [r"C:\test\path"],
            'sleep_short': 0.15,
            'sleep_long': 0.4,
            'ground_check_interval': 1500,
            'aircraft_request_interval': 2500,
            'max_menu_check_attempts': 6,
            'logging_level': 'WARNING',
            'logging_format': '%(levelname)s: %(message)s',
            'logging_datefmt': '%Y-%m-%d %H:%M:%S',
            'SI_API_KEY': 'my_api_key',
            'default_airline': 'UAL',
        }
        mock_yaml_load.return_value = yaml_data

        config = GADConfig.from_yaml("test_config.yaml")

        self.assertEqual(config.menu_file_paths, [r"C:\test\path"])
        self.assertEqual(config.sleep_short, 0.15)
        self.assertEqual(config.sleep_long, 0.4)
        self.assertEqual(config.ground_check_interval, 1500)
        self.assertEqual(config.aircraft_request_interval, 2500)
        self.assertEqual(config.max_menu_check_attempts, 6)
        self.assertEqual(config.logging_level, 'WARNING')
        self.assertEqual(config.logging_format, '%(levelname)s: %(message)s')
        self.assertEqual(config.logging_datefmt, '%Y-%m-%d %H:%M:%S')
        self.assertEqual(config.SI_API_KEY, 'my_api_key')
        self.assertEqual(config.default_airline, 'UAL')

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.Path')
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    @patch('GateAssignmentDirector.gad_config.yaml.safe_load')
    def test_from_yaml_creates_default_file_when_missing(self, mock_yaml_load, mock_yaml_dump, mock_path, mock_file):
        """Test from_yaml creates default config file when it doesn't exist"""
        mock_path_instance = Mock()
        # First call: file doesn't exist, second call onwards: file exists
        mock_path_instance.exists.side_effect = [False, True]
        mock_path.return_value = mock_path_instance

        defaults = GADConfig._get_defaults()
        mock_yaml_load.return_value = defaults

        config = GADConfig.from_yaml("new_config.yaml")

        # Should have called yaml.dump to create the file
        mock_yaml_dump.assert_called_once()
        dump_call_args = mock_yaml_dump.call_args
        self.assertEqual(dump_call_args[0][0], defaults)
        self.assertEqual(dump_call_args[1]['default_flow_style'], False)
        self.assertEqual(dump_call_args[1]['allow_unicode'], True)

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.Path')
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    @patch('GateAssignmentDirector.gad_config.yaml.safe_load')
    def test_from_yaml_default_path(self, mock_yaml_load, mock_yaml_dump, mock_path, mock_file):
        """Test from_yaml uses default path when none specified"""
        # Create a Path-like mock that works with the / operator
        # Create a mock path that supports the / (truediv) operator
        def create_path_mock():
            path_mock = Mock()
            path_mock.exists.return_value = True
            path_mock.__truediv__ = lambda self, other: create_path_mock()
            return path_mock
        
        # Make Path constructor return our mock
        mock_path.return_value = create_path_mock()

        mock_yaml_load.return_value = GADConfig._get_defaults()

        config = GADConfig.from_yaml()

        # Verify that config was loaded properly
        expected_defaults = GADConfig._get_defaults()
        self.assertEqual(config.SI_API_KEY, expected_defaults['SI_API_KEY'])
        self.assertEqual(config.sleep_short, expected_defaults['sleep_short'])

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.Path')
    @patch('GateAssignmentDirector.gad_config.yaml.safe_load')
    def test_from_yaml_reads_with_utf8_encoding(self, mock_yaml_load, mock_path, mock_file):
        """Test from_yaml opens file with UTF-8 encoding"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_yaml_load.return_value = GADConfig._get_defaults()

        config = GADConfig.from_yaml("test.yaml")

        # Verify file was opened with UTF-8 encoding for reading
        read_calls = [call for call in mock_file.call_args_list if 'r' in str(call)]
        self.assertTrue(len(read_calls) > 0)
        # Check that encoding='utf-8' was used
        for call_obj in read_calls:
            if 'encoding' in call_obj[1]:
                self.assertEqual(call_obj[1]['encoding'], 'utf-8')

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.Path')
    @patch('GateAssignmentDirector.gad_config.yaml.safe_load')
    def test_from_yaml_partial_config(self, mock_yaml_load, mock_path, mock_file):
        """Test from_yaml handles partial configuration"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        # Only provide some fields
        partial_data = {
            'sleep_short': 0.2,
            'SI_API_KEY': 'partial_key',
        }
        mock_yaml_load.return_value = partial_data

        config = GADConfig.from_yaml("partial.yaml")

        # Specified fields should be loaded
        self.assertEqual(config.sleep_short, 0.2)
        self.assertEqual(config.SI_API_KEY, 'partial_key')
        # Unspecified fields should use dataclass defaults
        self.assertEqual(config.menu_file_paths, [
            r"C:\Program Files (x86)\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu",
            r"C:\Program Files\Addon Manager\MSFS\fsdreamteam-gsx-pro\html_ui\InGamePanels\FSDT_GSX_Panel\menu",
        ])
        self.assertEqual(config.sleep_long, 0.3)

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.Path')
    @patch('GateAssignmentDirector.gad_config.yaml.safe_load')
    def test_from_yaml_converts_integer_floats_to_float_type(self, mock_yaml_load, mock_path, mock_file):
        """Test from_yaml converts integer representations of float fields to float type"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        yaml_data = {
            'sleep_short': 1,
            'sleep_long': 2,
            'ground_check_interval': 3,
            'aircraft_request_interval': 5,
            'SI_API_KEY': 'test_key',
        }
        mock_yaml_load.return_value = yaml_data

        config = GADConfig.from_yaml("test.yaml")

        self.assertIsInstance(config.sleep_short, float)
        self.assertEqual(config.sleep_short, 1.0)

        self.assertIsInstance(config.sleep_long, float)
        self.assertEqual(config.sleep_long, 2.0)

        self.assertIsInstance(config.ground_check_interval, float)
        self.assertEqual(config.ground_check_interval, 3.0)

        self.assertIsInstance(config.aircraft_request_interval, float)
        self.assertEqual(config.aircraft_request_interval, 5.0)


class TestGADConfigSaveYaml(unittest.TestCase):
    """Test suite for GADConfig.save_yaml() method"""

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    def test_save_yaml_writes_configurable_fields(self, mock_yaml_dump, mock_file):
        """Test save_yaml writes only configurable fields to YAML"""

        config = GADConfig(
            menu_file_paths=["path1"],
            sleep_short=0.2,
            sleep_long=0.5,
            ground_check_interval=2000,
            aircraft_request_interval=3000,
            max_menu_check_attempts=5,
            logging_level='INFO',
            logging_format='%(message)s',
            logging_datefmt='%Y-%m-%d',
            SI_API_KEY='save_test_key',
            default_airline='TEST'
        )

        config.save_yaml("output.yaml")

        # Check yaml.dump was called
        mock_yaml_dump.assert_called_once()
        saved_data = mock_yaml_dump.call_args[0][0]

        # Should contain configurable fields
        self.assertEqual(saved_data['menu_file_paths'], ["path1"])
        self.assertEqual(saved_data['sleep_short'], 0.2)
        self.assertEqual(saved_data['sleep_long'], 0.5)
        self.assertEqual(saved_data['ground_check_interval'], 2000)
        self.assertEqual(saved_data['aircraft_request_interval'], 3000)
        self.assertEqual(saved_data['max_menu_check_attempts'], 5)
        self.assertEqual(saved_data['logging_level'], 'INFO')
        self.assertEqual(saved_data['logging_format'], '%(message)s')
        self.assertEqual(saved_data['logging_datefmt'], '%Y-%m-%d')
        self.assertEqual(saved_data['SI_API_KEY'], 'save_test_key')

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    def test_save_yaml_excludes_computed_fields(self, mock_yaml_dump, mock_file):
        """Test save_yaml does not save computed fields like username and flight_json_path"""

        config = GADConfig()
        config.save_yaml("output.yaml")

        saved_data = mock_yaml_dump.call_args[0][0]

        # Should NOT contain computed fields
        self.assertNotIn('username', saved_data)
        self.assertNotIn('flight_json_path', saved_data)

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    def test_save_yaml_excludes_default_airline(self, mock_yaml_dump, mock_file):
        """Test save_yaml does not save default_airline field"""

        config = GADConfig(default_airline='TEST')
        config.save_yaml("output.yaml")

        saved_data = mock_yaml_dump.call_args[0][0]

        # default_airline should not be saved (not in save_yaml method)
        self.assertNotIn('default_airline', saved_data)

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    def test_save_yaml_default_path(self, mock_yaml_dump, mock_file):
        """Test save_yaml uses default path when none specified"""

        config = GADConfig()
        config.save_yaml()

        # Should open file with default path - Path object will be passed
        # Check that open was called (the specific path format depends on OS)
        mock_file.assert_called()
        # Verify it was called with a path containing the expected elements
        args, kwargs = mock_file.call_args
        path_used = args[0]
        # Check that the path includes expected components
        self.assertTrue("GateAssignmentDirector" in str(path_used))
        self.assertTrue("config.yaml" in str(path_used))
        self.assertEqual(kwargs, {'encoding': 'utf-8'})

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    def test_save_yaml_custom_path(self, mock_yaml_dump, mock_file):
        """Test save_yaml uses custom path when specified"""

        config = GADConfig()
        config.save_yaml("custom_path.yaml")

        # Should open file with custom path
        mock_file.assert_called_with("custom_path.yaml", 'w', encoding='utf-8')

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    def test_save_yaml_formatting_options(self, mock_yaml_dump, mock_file):
        """Test save_yaml uses correct YAML formatting options"""

        config = GADConfig()
        config.save_yaml("output.yaml")

        # Check formatting options
        dump_call_kwargs = mock_yaml_dump.call_args[1]
        self.assertEqual(dump_call_kwargs['default_flow_style'], False)
        self.assertEqual(dump_call_kwargs['allow_unicode'], True)

    @patch('builtins.open', new_callable=mock_open)
    @patch('GateAssignmentDirector.gad_config.yaml.dump')
    def test_save_yaml_writes_with_utf8_encoding(self, mock_yaml_dump, mock_file):
        """Test save_yaml opens file with UTF-8 encoding"""

        config = GADConfig()
        config.save_yaml("output.yaml")

        # Verify file was opened with UTF-8 encoding for writing
        mock_file.assert_called_with("output.yaml", 'w', encoding='utf-8')


class TestGADConfigRoundTrip(unittest.TestCase):
    """Test suite for round-trip save and load operations"""

    @patch('GateAssignmentDirector.gad_config.Path')
    def test_save_and_load_roundtrip(self, mock_path):
        """Test saving and loading config preserves values"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        # Create config with specific values
        original_config = GADConfig(
            menu_file_paths=["path1", "path2"],
            sleep_short=0.25,
            sleep_long=0.6,
            ground_check_interval=1800,
            aircraft_request_interval=2200,
            max_menu_check_attempts=7,
            logging_level='ERROR',
            logging_format='%(name)s: %(message)s',
            logging_datefmt='%Y/%m/%d',
            SI_API_KEY='roundtrip_key',
        )

        # Simulate save and load
        saved_data = {}

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('GateAssignmentDirector.gad_config.yaml.dump') as mock_dump:
                original_config.save_yaml("test.yaml")
                saved_data = mock_dump.call_args[0][0]

        with patch('builtins.open', mock_open()):
            with patch('GateAssignmentDirector.gad_config.yaml.safe_load', return_value=saved_data):
                loaded_config = GADConfig.from_yaml("test.yaml")

        # Verify all configurable fields match
        self.assertEqual(loaded_config.menu_file_paths, original_config.menu_file_paths)
        self.assertEqual(loaded_config.sleep_short, original_config.sleep_short)
        self.assertEqual(loaded_config.sleep_long, original_config.sleep_long)
        self.assertEqual(loaded_config.ground_check_interval, original_config.ground_check_interval)
        self.assertEqual(loaded_config.aircraft_request_interval, original_config.aircraft_request_interval)
        self.assertEqual(loaded_config.max_menu_check_attempts, original_config.max_menu_check_attempts)
        self.assertEqual(loaded_config.logging_level, original_config.logging_level)
        self.assertEqual(loaded_config.logging_format, original_config.logging_format)
        self.assertEqual(loaded_config.logging_datefmt, original_config.logging_datefmt)
        self.assertEqual(loaded_config.SI_API_KEY, original_config.SI_API_KEY)

    @patch('GateAssignmentDirector.gad_config.Path')
    def test_computed_fields_regenerated_after_load(self, mock_path):
        """Test computed fields are regenerated after loading from YAML"""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        yaml_data = {
            'sleep_short': 0.1,
            'SI_API_KEY': 'test',
        }

        with patch('builtins.open', mock_open()):
            with patch('GateAssignmentDirector.gad_config.yaml.safe_load', return_value=yaml_data):
                config = GADConfig.from_yaml("test.yaml")

        # Computed fields should be generated (using system username)
        self.assertIsNotNone(config.username)
        self.assertIsInstance(config.username, str)
        # Flight path should use the username
        expected_path = f"C:\\Users\\{config.username}\\AppData\\Local\\SayIntentionsAI\\flight.json"
        self.assertEqual(config.flight_json_path, expected_path)


if __name__ == "__main__":
    unittest.main()
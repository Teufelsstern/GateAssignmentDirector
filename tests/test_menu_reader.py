import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import os
from GateAssignmentDirector.menu_reader import MenuReader, MenuState
from GateAssignmentDirector.exceptions import GsxFileNotFoundError


class TestMenuReader(unittest.TestCase):
    """Test suite for MenuReader with file operations mocked"""

    def setUp(self):
        """Set up test fixtures with mocked dependencies"""
        self.mock_config = Mock()
        self.mock_config.logging_level = "INFO"
        self.mock_config.logging_format = "%(message)s"
        self.mock_config.logging_datefmt = "%Y-%m-%d"
        self.mock_config.max_menu_check_attempts = 4
        self.mock_config.menu_file_paths = [
            "C:\\path\\to\\menu.txt",
            "C:\\alternate\\menu.txt"
        ]

        self.mock_menu_logger = Mock()
        self.mock_menu_navigator = Mock()
        self.mock_sim_manager = Mock()

    @patch('os.path.exists')
    def test_find_menu_file_first_path(self, mock_exists):
        """Test finding menu file at first configured path"""
        mock_exists.side_effect = lambda path: path == "C:\\path\\to\\menu.txt"

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        self.assertEqual(reader.menu_path, "C:\\path\\to\\menu.txt")

    @patch('os.path.exists')
    def test_find_menu_file_second_path(self, mock_exists):
        """Test finding menu file at alternate path"""
        mock_exists.side_effect = lambda path: path == "C:\\alternate\\menu.txt"

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        self.assertEqual(reader.menu_path, "C:\\alternate\\menu.txt")

    @patch('os.path.exists')
    def test_find_menu_file_not_found(self, mock_exists):
        """Test when menu file not found in any path raises exception"""
        mock_exists.return_value = False

        with self.assertRaises(GsxFileNotFoundError) as context:
            reader = MenuReader(
                self.mock_config,
                self.mock_menu_logger,
                self.mock_menu_navigator,
                self.mock_sim_manager
            )

        self.assertIn("GSX may not be installed", str(context.exception))

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open, read_data="Test Menu\nOption 1\nOption 2\nOption 3")
    def test_read_menu_success(self, mock_file, mock_mtime, mock_exists):
        """Test successfully reading menu from file"""
        mock_exists.return_value = True
        mock_mtime.return_value = 123456.0

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        result = reader.read_menu()

        self.assertEqual(result.title, "Test Menu")
        self.assertEqual(len(result.options), 3)
        self.assertEqual(result.options[0], "Option 1")
        self.assertEqual(result.options[1], "Option 2")
        self.assertEqual(result.options[2], "Option 3")

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open, read_data="GSX Menu\nGate 5A\nGate 5B\nNext")
    def test_read_menu_creates_options_enum(self, mock_file, mock_mtime, mock_exists):
        """Test that options_enum is created correctly"""
        mock_exists.return_value = True
        mock_mtime.return_value = 123456.0

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        result = reader.read_menu()

        self.assertEqual(len(result.options_enum), 3)
        self.assertEqual(result.options_enum[0], (0, "Gate 5A"))
        self.assertEqual(result.options_enum[1], (1, "Gate 5B"))
        self.assertEqual(result.options_enum[2], (2, "Next"))

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open, read_data="Menu\n")
    def test_read_menu_empty_options(self, mock_file, mock_mtime, mock_exists):
        """Test reading menu with only title"""
        mock_exists.return_value = True
        mock_mtime.return_value = 123456.0

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        result = reader.read_menu()

        self.assertEqual(result.title, "Menu")
        self.assertEqual(len(result.options), 0)  # No options after title line

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    def test_read_menu_updates_current_state(self, mock_mtime, mock_exists):
        """Test that reading menu updates current_state"""
        mock_exists.return_value = True
        mock_mtime.return_value = 123456.0

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        # Initial state
        initial_state = reader.current_state

        with patch('builtins.open', mock_open(read_data="New Menu\nNew Option")):
            reader.read_menu()

        # State should be updated
        self.assertNotEqual(reader.current_state.title, initial_state.title)
        self.assertEqual(reader.current_state.title, "New Menu")

    @patch('os.path.exists')
    def test_has_changed_different_option_count(self, mock_exists):
        """Test has_changed detects different number of options"""
        mock_exists.return_value = True

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        reader.current_state = MenuState(
            title="Menu",
            options=["Option 1", "Option 2", "Option 3"],
            options_enum=[(0, "Option 1"), (1, "Option 2"), (2, "Option 3")],
            raw_lines=[]
        )
        reader.previous_state = MenuState(
            title="Menu",
            options=["Option 1", "Option 2"],
            options_enum=[(0, "Option 1"), (1, "Option 2")],
            raw_lines=[]
        )

        result = reader.has_changed()

        self.assertTrue(result)

    @patch('os.path.exists')
    def test_has_changed_same_option_count_different_content(self, mock_exists):
        """Test has_changed detects same count but different first non-menu-action option"""
        mock_exists.return_value = True

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        reader.current_state = MenuState(
            title="Menu",
            options=["New First Option", "Opt 2", "Opt 3"],
            options_enum=[(0, "New First Option"), (1, "Opt 2"), (2, "Opt 3")],
            raw_lines=[]
        )
        reader.previous_state = MenuState(
            title="Menu",
            options=["Old First Option", "Opt 2", "Opt 3"],
            options_enum=[(0, "Old First Option"), (1, "Opt 2"), (2, "Opt 3")],
            raw_lines=[]
        )

        result = reader.has_changed()

        self.assertTrue(result)

    @patch('os.path.exists')
    def test_has_changed_no_change(self, mock_exists):
        """Test has_changed returns true even when content same (updates previous)"""
        mock_exists.return_value = True

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        same_options = ["Opt 1", "Opt 2", "Same"]
        reader.current_state = MenuState(
            title="Menu",
            options=same_options,
            options_enum=[(0, "Opt 1"), (1, "Opt 2"), (2, "Same")],
            raw_lines=[]
        )
        reader.previous_state = MenuState(
            title="Menu",
            options=same_options,
            options_enum=[(0, "Opt 1"), (1, "Opt 2"), (2, "Same")],
            raw_lines=[]
        )

        result = reader.has_changed()

        # Returns false when checking against itself
        self.assertFalse(result)

    @patch('os.path.exists')
    def test_has_changed_with_check_option(self, mock_exists):
        """Test has_changed with specific option to check"""
        mock_exists.return_value = True

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        reader.current_state = MenuState(
            title="Menu",
            options=["Opt 1", "Opt 2", "Different"],
            options_enum=[(0, "Opt 1"), (1, "Opt 2"), (2, "Different")],
            raw_lines=[]
        )
        reader.previous_state = MenuState(
            title="Menu",
            options=["Opt 1", "Opt 2", "Old"],
            options_enum=[(0, "Opt 1"), (1, "Opt 2"), (2, "Old")],
            raw_lines=[]
        )

        result = reader.has_changed(check_option="Old")

        self.assertTrue(result)

    @patch('os.path.exists')
    def test_has_changed_updates_previous_state(self, mock_exists):
        """Test that has_changed updates previous_state"""
        mock_exists.return_value = True

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        new_state = MenuState(
            title="New",
            options=["New Option"],
            options_enum=[(0, "New Option")],
            raw_lines=[]
        )
        reader.current_state = new_state

        reader.has_changed()

        # Previous state should now match current
        self.assertEqual(reader.previous_state, new_state)

    @patch('os.path.exists')
    def test_has_changed_short_menu_no_crash(self, mock_exists):
        """Test has_changed doesn't crash with menus shorter than 3 options"""
        mock_exists.return_value = True

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        reader.current_state = MenuState(
            title="Short Menu",
            options=["Option 1"],
            options_enum=[(0, "Option 1")],
            raw_lines=[]
        )
        reader.previous_state = MenuState(
            title="Short Menu",
            options=["Option 1"],
            options_enum=[(0, "Option 1")],
            raw_lines=[]
        )

        # Should not raise IndexError
        result = reader.has_changed()
        self.assertFalse(result)

    @patch('os.path.exists')
    def test_has_changed_detects_change_in_short_menu(self, mock_exists):
        """Test has_changed detects change even with short menus"""
        mock_exists.return_value = True

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        reader.current_state = MenuState(
            title="Short Menu",
            options=["New Option"],
            options_enum=[(0, "New Option")],
            raw_lines=[]
        )
        reader.previous_state = MenuState(
            title="Short Menu",
            options=["Old Option"],
            options_enum=[(0, "Old Option")],
            raw_lines=[]
        )

        result = reader.has_changed(check_option="Old Option")
        self.assertTrue(result)

    @patch('os.path.exists')
    def test_initialization_creates_initial_state(self, mock_exists):
        """Test that MenuReader initializes with default state"""
        mock_exists.return_value = True

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        self.assertIsNotNone(reader.current_state)
        self.assertEqual(reader.current_state.title, "Initial")
        self.assertEqual(reader.current_state.options, ["Initial"])

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    @patch('builtins.open', new_callable=mock_open, read_data="Menu\nOption with  spaces\n")
    def test_read_menu_strips_whitespace(self, mock_file, mock_mtime, mock_exists):
        """Test that menu reading strips whitespace properly"""
        mock_exists.return_value = True
        mock_mtime.return_value = 123456.0

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        result = reader.read_menu()

        # Should strip newlines but preserve internal spaces
        self.assertEqual(result.options[0], "Option with  spaces")
        self.assertNotIn("\n", result.options[0])

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    def test_read_menu_stores_timestamp(self, mock_mtime, mock_exists):
        """Test that file timestamp is stored"""
        mock_exists.return_value = True
        mock_mtime.return_value = 999999.5

        reader = MenuReader(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )

        with patch('builtins.open', mock_open(read_data="Menu\nOption")):
            result = reader.read_menu()

        self.assertEqual(result.file_timestamp, 999999.5)


class TestMenuState(unittest.TestCase):
    """Test suite for MenuState dataclass"""

    def test_menu_state_creation(self):
        """Test creating MenuState with all fields"""
        state = MenuState(
            title="Test",
            options=["Opt1", "Opt2"],
            options_enum=[(0, "Opt1"), (1, "Opt2")],
            raw_lines=["Test", "Opt1", "Opt2"],
            file_timestamp=123.45
        )

        self.assertEqual(state.title, "Test")
        self.assertEqual(len(state.options), 2)
        self.assertEqual(state.file_timestamp, 123.45)

    def test_menu_state_default_timestamp(self):
        """Test MenuState has default timestamp of 0"""
        state = MenuState(
            title="Test",
            options=[],
            options_enum=[],
            raw_lines=[]
        )

        self.assertEqual(state.file_timestamp, 0)


if __name__ == "__main__":
    unittest.main()
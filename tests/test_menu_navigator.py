import unittest
from unittest.mock import Mock, MagicMock, patch
from GateAssignmentDirector.menu_navigator import MenuNavigator, _search_options
from GateAssignmentDirector.gsx_enums import SearchType
from GateAssignmentDirector.exceptions import GsxMenuError
from GateAssignmentDirector.menu_reader import MenuState


class TestMenuNavigator(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with mocked dependencies"""
        self.mock_config = Mock()
        self.mock_config.sleep_short = 0.01
        self.mock_config.sleep_long = 0.01
        self.mock_config.max_menu_check_attempts = 5
        self.mock_config.logging_level = "INFO"
        self.mock_config.logging_format = "%(message)s"
        self.mock_config.logging_datefmt = "%Y-%m-%d"

        self.mock_menu_logger = Mock()
        self.mock_menu_reader = Mock()
        self.mock_sim_manager = Mock()

        # Mock the menu choice request
        self.mock_menu_choice = Mock()
        self.mock_sim_manager.create_request.return_value = self.mock_menu_choice

        self.navigator = MenuNavigator(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_reader,
            self.mock_sim_manager
        )

    def test_click_by_index(self):
        """Test clicking a menu item by index"""
        self.mock_menu_reader.current_state = MenuState(
            title="Test Menu",
            options=["Option 1", "Option 2"],
            options_enum=[(0, "Option 1"), (1, "Option 2")],
            raw_lines=[]
        )
        self.mock_menu_reader.previous_state = MenuState(
            title="Old Menu",
            options=["Old Option"],
            options_enum=[(0, "Old Option")],
            raw_lines=[]
        )
        self.mock_menu_reader.has_changed.return_value = True

        result = self.navigator.click_by_index(1)

        # Verify the menu choice was set
        self.assertEqual(self.mock_menu_choice.value, 1)
        self.assertTrue(result)

    def test_click_next_found(self):
        """Test clicking Next button when available"""
        menu_state = MenuState(
            title="Test Menu",
            options=["Option 1", "Next", "Option 3"],
            options_enum=[(0, "Option 1"), (1, "Next"), (2, "Option 3")],
            raw_lines=[]
        )
        self.mock_menu_reader.current_state = menu_state
        self.mock_menu_reader.previous_state = MenuState(
            title="Old", options=["Old"], options_enum=[(0, "Old")], raw_lines=[]
        )
        self.mock_menu_reader.has_changed.return_value = True

        result = self.navigator.click_next()

        # Verify Next was clicked at index 1
        self.assertEqual(self.mock_menu_choice.value, 1)
        self.assertTrue(result)

    def test_click_next_not_found(self):
        """Test clicking Next when button not available"""
        menu_state = MenuState(
            title="Test Menu",
            options=["Option 1", "Option 2"],
            options_enum=[(0, "Option 1"), (1, "Option 2")],
            raw_lines=[]
        )
        self.mock_menu_reader.current_state = menu_state

        result = self.navigator.click_next()

        self.assertFalse(result)

    def test_click_planned_gate(self):
        """Test clicking planned gate with navigation info"""
        gate_info = {
            "raw_info": {
                "level_0_index": 2,
                "next_clicks": 3,
                "menu_index": 5
            }
        }

        menu_state = MenuState(
            title="Test Menu",
            options=["Option 1", "Next", "Option 3"],
            options_enum=[(0, "Option 1"), (1, "Next"), (2, "Option 3")],
            raw_lines=[]
        )
        self.mock_menu_reader.read_menu.return_value = menu_state
        self.mock_menu_reader.current_state = menu_state
        self.mock_menu_reader.previous_state = Mock()
        self.mock_menu_reader.previous_state.options = ["Option 1", "Option 2"]
        self.mock_menu_reader.has_changed.return_value = True

        result = self.navigator.click_planned(gate_info)

        # Verify clicks: first_index, then 3x next, then second_index
        self.assertTrue(result)
        self.assertTrue(self.mock_menu_choice.value in [2, 5])  # Called with both indices

    def test_find_and_click_success(self):
        """Test finding and clicking a keyword"""
        menu_state = MenuState(
            title="Test Menu",
            options=["Option 1", "activate", "Option 3"],
            options_enum=[(0, "Option 1"), (1, "activate"), (2, "Option 3")],
            raw_lines=[]
        )
        self.mock_menu_reader.read_menu.return_value = menu_state
        self.mock_menu_reader.previous_state = MenuState(
            title="Old", options=["Old"], options_enum=[(0, "Old")], raw_lines=[]
        )
        self.mock_menu_reader.has_changed.return_value = True

        result = self.navigator.find_and_click(["activate"], SearchType.KEYWORD)

        self.assertTrue(result)
        self.assertEqual(self.mock_menu_choice.value, 1)

    def test_find_and_click_not_found(self):
        """Test finding keyword that doesn't exist"""
        menu_state = MenuState(
            title="Test Menu",
            options=["Option 1", "Option 2"],
            options_enum=[(0, "Option 1"), (1, "Option 2")],
            raw_lines=[]
        )
        self.mock_menu_reader.read_menu.return_value = menu_state
        self.mock_menu_reader.previous_state = Mock()
        self.mock_menu_reader.previous_state.options = ["Option 1", "Option 2"]
        self.mock_menu_reader.has_changed.return_value = False

        with self.assertRaises(GsxMenuError):
            self.navigator.find_and_click(["missing"], SearchType.KEYWORD)

    def test_find_and_click_menu_action(self):
        """Test finding menu action (no pagination)"""
        menu_state = MenuState(
            title="Test Menu",
            options=["Back", "Option 2"],
            options_enum=[(0, "Back"), (1, "Option 2")],
            raw_lines=[]
        )
        self.mock_menu_reader.read_menu.return_value = menu_state
        self.mock_menu_reader.previous_state = MenuState(
            title="Old", options=["Old"], options_enum=[(0, "Old")], raw_lines=[]
        )
        self.mock_menu_reader.has_changed.return_value = True

        result = self.navigator.find_and_click(["Back"], SearchType.MENU_ACTION)

        self.assertTrue(result)

    def test_wait_for_change_success(self):
        """Test waiting for menu change succeeds"""
        self.mock_menu_reader.previous_state = MenuState(
            title="Old",
            options=["Old1", "Old2", "Old3"],
            options_enum=[(0, "Old1"), (1, "Old2"), (2, "Old3")],
            raw_lines=[]
        )
        self.mock_menu_reader.read_menu.return_value = MenuState(
            title="New",
            options=["New1", "New2", "New3"],
            options_enum=[(0, "New1"), (1, "New2"), (2, "New3")],
            raw_lines=[]
        )
        self.mock_menu_reader.has_changed.return_value = True

        result = self.navigator._wait_for_change()

        self.assertTrue(result)

    def test_wait_for_change_timeout(self):
        """Test waiting for menu change times out"""
        self.mock_menu_reader.previous_state = MenuState(
            title="Same",
            options=["Same1", "Same2", "Same3"],
            options_enum=[(0, "Same1"), (1, "Same2"), (2, "Same3")],
            raw_lines=[]
        )
        self.mock_menu_reader.has_changed.return_value = False

        result = self.navigator._wait_for_change()

        self.assertFalse(result)


class TestSearchOptions(unittest.TestCase):
    def test_search_keyword_found(self):
        """Test searching for keyword in options"""
        menu = Mock()
        menu.options_enum = [(0, "Option 1"), (1, "activate now"), (2, "Option 3")]

        result = _search_options(["activate"], SearchType.KEYWORD, menu)

        self.assertEqual(result, 1)

    def test_search_keyword_not_found(self):
        """Test searching for keyword not in options"""
        menu = Mock()
        menu.options_enum = [(0, "Option 1"), (1, "Option 2")]

        result = _search_options(["missing"], SearchType.KEYWORD, menu)

        # Returns last index when not found
        self.assertEqual(result, 1)

    def test_search_airline(self):
        """Test searching for airline code"""
        menu = Mock()
        menu.options_enum = [(0, "Option 1"), (1, "United (UA_2000)"), (2, "Option 3")]

        result = _search_options(["(UA_2000)"], SearchType.AIRLINE, menu)

        self.assertEqual(result, 1)

    def test_search_multiple_keywords(self):
        """Test searching with multiple keywords"""
        menu = Mock()
        menu.options_enum = [(0, "First"), (1, "Second option"), (2, "Third")]

        result = _search_options(["Second", "option"], SearchType.KEYWORD, menu)

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
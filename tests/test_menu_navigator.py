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
        initial_state = MenuState(
            title="Test Menu",
            options=["Option 1", "Option 2"],
            options_enum=[(0, "Option 1"), (1, "Option 2")],
            raw_lines=[]
        )
        changed_state = MenuState(
            title="New Menu",
            options=["New Option"],
            options_enum=[(0, "New Option")],
            raw_lines=[]
        )

        # Set up the sequence of states
        # First call is the initial read_menu before setting value
        # Then _wait_for_change calls read_menu multiple times to check for changes
        self.mock_menu_reader.current_state = initial_state
        call_count = [0]

        def side_effect_read_menu():
            if call_count[0] == 0:
                # First call: return initial state
                call_count[0] += 1
                return initial_state
            else:
                # Subsequent calls: menu has changed
                self.mock_menu_reader.current_state = changed_state
                return changed_state

        self.mock_menu_reader.read_menu.side_effect = side_effect_read_menu

        result = self.navigator.click_by_index(1)

        # Verify the menu choice was set
        self.assertEqual(self.mock_menu_choice.value, 1)
        self.assertTrue(result)

    def test_click_next_found(self):
        """Test clicking Next button when available"""
        initial_state = MenuState(
            title="Test Menu",
            options=["Option 1", "Next", "Option 3"],
            options_enum=[(0, "Option 1"), (1, "Next"), (2, "Option 3")],
            raw_lines=[]
        )
        changed_state = MenuState(
            title="New Menu",
            options=["New1", "New2"],
            options_enum=[(0, "New1"), (1, "New2")],
            raw_lines=[]
        )

        self.mock_menu_reader.current_state = initial_state
        call_count = [0]

        # Need to track the actual value being set
        actual_value = [None]
        def set_value(val):
            actual_value[0] = val

        # Override the value property to track assignments
        type(self.mock_menu_choice).value = property(
            lambda self: actual_value[0],
            lambda self, val: set_value(val)
        )

        # Simulate menu change after clicking Next
        def side_effect_read_menu():
            if call_count[0] == 0:
                # First call: return initial state
                call_count[0] += 1
                return initial_state
            else:
                # Subsequent calls: menu has changed
                self.mock_menu_reader.current_state = changed_state
                return changed_state

        self.mock_menu_reader.read_menu.side_effect = side_effect_read_menu

        result, _ = self.navigator.click_next()

        # Verify Next was clicked at index 1
        self.assertEqual(actual_value[0], 1)
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
        self.mock_menu_reader.read_menu.return_value = menu_state

        result, _ = self.navigator.click_next()

        self.assertTrue(result)

    def test_click_planned_gate(self):
        """Test clicking planned gate with navigation info"""
        gate_info = {
            "raw_info": {
                "level_0_page": 1,
                "level_0_option_index": 2,
                "level_1_next_clicks": 3,
                "menu_index": 5
            }
        }

        # States for navigation sequence
        page_0_state = MenuState(
            title="Page 0",
            options=["Option 1", "Next", "Option 3", "Option 4", "Option 5", "Option 6"],
            options_enum=[(0, "Option 1"), (1, "Next"), (2, "Option 3"), (3, "Option 4"), (4, "Option 5"), (5, "Option 6")],
            raw_lines=[]
        )
        page_1_state = MenuState(
            title="Page 1",
            options=["Page1 Option1", "Next", "Page1 Option3"],
            options_enum=[(0, "Page1 Option1"), (1, "Next"), (2, "Page1 Option3")],
            raw_lines=[]
        )
        level_1_state = MenuState(
            title="Level 1 Menu",
            options=["Level1 Opt1", "Next", "Level1 Opt3", "Level1 Opt4", "Level1 Opt5", "Target Option"],
            options_enum=[(0, "Level1 Opt1"), (1, "Next"), (2, "Level1 Opt3"), (3, "Level1 Opt4"), (4, "Level1 Opt5"), (5, "Target Option")],
            raw_lines=[]
        )
        final_state = MenuState(
            title="Final Menu",
            options=["Final Option"],
            options_enum=[(0, "Final Option")],
            raw_lines=[]
        )

        # Track state transitions with a state machine
        current_state_holder = [page_0_state]
        pending_state_change = [None]

        def side_effect_read_menu():
            # If there's a pending state change, apply it now
            if pending_state_change[0] is not None:
                current_state_holder[0] = pending_state_change[0]
                self.mock_menu_reader.current_state = pending_state_change[0]
                pending_state_change[0] = None
            return current_state_holder[0]

        self.mock_menu_reader.read_menu.side_effect = side_effect_read_menu
        self.mock_menu_reader.current_state = page_0_state

        # Track value changes to schedule state transitions
        actual_value = [None]
        next_click_count = [0]

        def set_value(val):
            actual_value[0] = val
            # Schedule state changes based on what was clicked
            # The state will actually change on the next read_menu() call
            if val == 1:  # Next button
                if current_state_holder[0].title == "Page 0":
                    pending_state_change[0] = page_1_state
                elif current_state_holder[0].title.startswith("Level 1 Menu"):
                    # For level 1, create slight variations to simulate state change
                    # This ensures _wait_for_change detects a change
                    next_click_count[0] += 1
                    modified_state = MenuState(
                        title=f"Level 1 Menu Page {next_click_count[0]}",
                        options=level_1_state.options,
                        options_enum=level_1_state.options_enum,
                        raw_lines=[]
                    )
                    pending_state_change[0] = modified_state
            elif val == 2:  # Level 0 option index
                pending_state_change[0] = level_1_state
            elif val == 5:  # Final menu index
                pending_state_change[0] = final_state

        type(self.mock_menu_choice).value = property(
            lambda self: actual_value[0],
            lambda self, val: set_value(val)
        )

        self.navigator.click_planned(gate_info)

        # Verify final click happened to index 5
        self.assertEqual(actual_value[0], 5)

    def test_find_and_click_success(self):
        """Test finding and clicking a keyword"""
        # Use a menu with enough options so that index adjustment doesn't go negative
        menu_state = MenuState(
            title="Test Menu",
            options=["Option 0", "Option 1", "Option 2", "activate", "Option 4", "Option 5"],
            options_enum=[(0, "Option 0"), (1, "Option 1"), (2, "Option 2"), (3, "activate"), (4, "Option 4"), (5, "Option 5")],
            raw_lines=[]
        )
        changed_state = MenuState(
            title="Changed Menu",
            options=["New Option"],
            options_enum=[(0, "New Option")],
            raw_lines=[]
        )

        # First read_menu returns menu_state, subsequent ones return changed_state
        call_count = [0]
        def side_effect_read_menu():
            if call_count[0] == 0:
                call_count[0] += 1
                self.mock_menu_reader.current_state = menu_state
                return menu_state
            else:
                self.mock_menu_reader.current_state = changed_state
                return changed_state

        self.mock_menu_reader.read_menu.side_effect = side_effect_read_menu
        self.mock_menu_reader.current_state = menu_state

        # Track the actual value being set
        actual_value = [None]
        def set_value(val):
            actual_value[0] = val

        type(self.mock_menu_choice).value = property(
            lambda self: actual_value[0],
            lambda self, val: set_value(val)
        )

        result = self.navigator.find_and_click(["activate"], SearchType.KEYWORD)

        self.assertTrue(result)
        # activate is found at index 3, but find_and_click subtracts 2 for "activate" keyword
        # So final index should be 3 - 2 = 1
        self.assertEqual(actual_value[0], 1)

    def test_find_and_click_not_found(self):
        """Test finding keyword that doesn't exist"""
        menu_state = MenuState(
            title="Test Menu",
            options=["Option 1", "Option 2"],
            options_enum=[(0, "Option 1"), (1, "Option 2")],
            raw_lines=[]
        )
        self.mock_menu_reader.read_menu.return_value = menu_state
        self.mock_menu_reader.current_state = menu_state

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
        changed_state = MenuState(
            title="Changed Menu",
            options=["New Option"],
            options_enum=[(0, "New Option")],
            raw_lines=[]
        )

        # First read returns menu_state, subsequent ones return changed_state
        call_count = [0]
        def side_effect_read_menu():
            if call_count[0] == 0:
                call_count[0] += 1
                self.mock_menu_reader.current_state = menu_state
                return menu_state
            else:
                self.mock_menu_reader.current_state = changed_state
                return changed_state

        self.mock_menu_reader.read_menu.side_effect = side_effect_read_menu
        self.mock_menu_reader.current_state = menu_state

        result = self.navigator.find_and_click(["Back"], SearchType.MENU_ACTION)

        self.assertTrue(result)

    def test_wait_for_change_success(self):
        """Test waiting for menu change succeeds"""
        old_state = MenuState(
            title="Old",
            options=["Old1", "Old2", "Old3"],
            options_enum=[(0, "Old1"), (1, "Old2"), (2, "Old3")],
            raw_lines=[]
        )
        new_state = MenuState(
            title="New",
            options=["New1", "New2", "New3"],
            options_enum=[(0, "New1"), (1, "New2"), (2, "New3")],
            raw_lines=[]
        )

        self.mock_menu_reader.current_state = old_state

        # Simulate state change after first read_menu call
        call_count = [0]
        def side_effect_read_menu():
            if call_count[0] == 0:
                call_count[0] += 1
                return old_state
            else:
                self.mock_menu_reader.current_state = new_state
                return new_state

        self.mock_menu_reader.read_menu.side_effect = side_effect_read_menu

        result, info = self.navigator._wait_for_change()

        self.assertTrue(result)
        self.assertEqual(info[0], "Old")

    def test_wait_for_change_timeout(self):
        """Test waiting for menu change times out"""
        same_state = MenuState(
            title="Same",
            options=["Same1", "Same2", "Same3"],
            options_enum=[(0, "Same1"), (1, "Same2"), (2, "Same3")],
            raw_lines=[]
        )

        self.mock_menu_reader.current_state = same_state
        self.mock_menu_reader.read_menu.return_value = same_state

        result, info = self.navigator._wait_for_change()

        self.assertFalse(result)
        self.assertEqual(info[0], "Same")


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

        # Returns -1 when not found (correct behavior)
        self.assertEqual(result, -1)

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

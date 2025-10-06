# Testing Documentation

**For:** unit-test-expert

This document covers test suite organization, mock patterns, common fixtures, assertion patterns, and testing best practices.

## Table of Contents

- [Test Suite Organization](#test-suite-organization)
- [Import Quick Reference](#import-quick-reference)
- [Common Test Fixtures](#common-test-fixtures)
- [Mock Setup Patterns](#mock-setup-patterns)
- [Assertion Patterns](#assertion-patterns)
- [Running Tests](#running-tests)
- [Test File Index](#test-file-index)
- [Common Pitfalls](#common-pitfalls)

---

## Test Suite Organization

**Test Location:** `tests/` (project root)
**Test Count:** 250 unit tests (as of v0.8.8)
**Framework:** Python `unittest` with `unittest.mock`

### Test File Naming

Tests mirror source file names:
```
GateAssignmentDirector/gate_assignment.py  →  tests/test_gate_assignment.py
GateAssignmentDirector/menu_reader.py     →  tests/test_menu_reader.py
```

### Test Class Naming

```python
# Source: class GateAssignment
# Test:   class TestGateAssignment(unittest.TestCase)
```

### Test Method Naming

Use descriptive names starting with `test_`:
```python
def test_find_gate_exact_match(self):
    """Test finding gate with exact terminal and gate match"""

def test_assign_gate_not_on_ground_with_wait(self):
    """Test gate assignment waits for ground"""
```

---

## Import Quick Reference

### Standard Imports

```python
import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open, call
from typing import Dict, Any, Optional
```

### When to Use What

| Mock Type | Use Case | Example |
|-----------|----------|---------|
| `Mock()` | Simple mock object | `mock_config = Mock()` |
| `MagicMock()` | Need magic methods (__len__, __iter__) | `mock_list = MagicMock()` |
| `patch()` | Patch module/class | `@patch('module.Class')` |
| `mock_open` | Mock file operations | `@patch('builtins.open', new_callable=mock_open)` |
| `call` | Verify call arguments | `mock.assert_has_calls([call(1), call(2)])` |

### Project-Specific Imports

```python
from GateAssignmentDirector.gate_assignment import GateAssignment
from GateAssignmentDirector.gad_config import GADConfig
from GateAssignmentDirector.exceptions import GsxMenuError, GsxTimeoutError
from GateAssignmentDirector.si_api_hook import GateInfo, GateParser
from GateAssignmentDirector.menu_reader import MenuState
from GateAssignmentDirector.gsx_enums import SearchType
```

---

## Common Test Fixtures

### Config Mock Template

**Use this in every test that needs GADConfig:**

```python
def create_mock_config():
    """Reusable mock config with all required attributes"""
    mock_config = Mock(spec=GADConfig)

    # Paths
    mock_config.menu_file_paths = ["/path/to/menu"]

    # Timing (in seconds as of v0.8.4)
    mock_config.sleep_short = 0.01  # Fast for tests
    mock_config.sleep_long = 0.01
    mock_config.ground_check_interval = 0.01
    mock_config.aircraft_request_interval = 0.01
    mock_config.max_menu_check_attempts = 5

    # Logging (REQUIRED - many components use these)
    mock_config.logging_level = "INFO"
    mock_config.logging_format = "%(message)s"
    mock_config.logging_datefmt = "%Y-%m-%d"

    # API
    mock_config.SI_API_KEY = "test_key"
    mock_config.default_airline = "GSX"

    # Computed
    mock_config.username = "testuser"
    mock_config.flight_json_path = "C:\\Users\\testuser\\AppData\\Local\\SayIntentionsAI\\flight.json"

    return mock_config
```

**Usage:**
```python
def setUp(self):
    self.mock_config = create_mock_config()
    self.component = Component(self.mock_config)
```

### MenuState Fixture

```python
def create_mock_menu_state(title="Test Menu", options=None):
    """Create MenuState for testing"""
    if options is None:
        options = ["Option 1", "Option 2", "Next"]

    return MenuState(
        title=title,
        options=options,
        options_enum=[(i, opt) for i, opt in enumerate(options)],
        raw_lines=[title, ""] + options
    )
```

### GateInfo Fixture

```python
def create_gate_info(terminal="1", gate="5", letter="A"):
    """Create GateInfo for testing"""
    return GateInfo(
        terminal_name="Terminal",
        terminal_number=terminal,
        gate_number=gate,
        gate_letter=letter,
        raw_value=f"Terminal {terminal} Gate {gate}{letter}"
    )
```

---

## Mock Setup Patterns

### Pattern 1: Component with Multiple Dependencies

```python
class TestGateAssignment(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with all mocked dependencies"""
        # Config
        self.mock_config = create_mock_config()

        # Dependencies
        self.mock_menu_logger = Mock()
        self.mock_menu_reader = Mock()
        self.mock_menu_navigator = Mock()
        self.mock_sim_manager = Mock()

        # Component under test
        self.gate_assignment = GateAssignment(
            self.mock_config,
            self.mock_menu_logger,
            self.mock_menu_reader,
            self.mock_menu_navigator,
            self.mock_sim_manager
        )
```

### Pattern 2: Side Effects for Sequential Behavior

**Use `side_effect` for methods called multiple times with different results:**

```python
def test_wait_for_ground_eventually_lands(self):
    """Test waiting handles multiple not-on-ground states"""
    # First 3 calls: False, then True on 4th
    self.mock_sim_manager.is_on_ground.side_effect = [False, False, False, True]

    self.gate_assignment._wait_for_ground()

    # Verify called at least 4 times
    self.assertGreaterEqual(self.mock_sim_manager.is_on_ground.call_count, 4)
```

**Side effect with exception:**
```python
def test_simconnect_connection_failure(self):
    """Test handles SimConnect connection failure"""
    self.mock_sim.connect.side_effect = ConnectionError("Failed")

    with self.assertRaises(GsxConnectionError):
        hook = GsxHook(self.mock_config)
```

### Pattern 3: Return Values

```python
def test_find_gate_returns_match(self):
    """Test find_gate returns matched gate"""
    airport_data = {
        "terminals": {
            "1": {
                "5A": {"terminal": "1", "gate": "5A", "position_id": "Gate 1-5A"}
            }
        }
    }

    result, is_direct = self.gate_assignment.find_gate(airport_data, "1", "5A")

    self.assertTrue(is_direct)
    self.assertEqual(result["gate"], "5A")
```

### Pattern 4: Patching Decorators

**Patch external dependencies:**

```python
@patch('GateAssignmentDirector.gate_assignment.requests.get')
@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
def test_assign_gate_with_api_call(self, mock_json, mock_file, mock_exists, mock_requests):
    """Test gate assignment calls API for fuzzy matches"""
    # Setup mocks
    mock_exists.return_value = True
    mock_json.return_value = {...}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_requests.return_value = mock_response

    # Test
    result = self.gate_assignment.assign_gate("KLAX", gate_number="5")

    # Verify API called
    mock_requests.assert_called_once()
```

**Decorator order:** Bottom-up (last decorator = first parameter)

### Pattern 5: Mock with `spec`

**Use `spec` to restrict mock to actual class attributes:**

```python
def test_with_spec(self):
    """Test with spec ensures mock matches real class"""
    mock_config = Mock(spec=GADConfig)
    # mock_config.invalid_attr  # Would raise AttributeError

    mock_config.logging_level = "INFO"  # Valid attribute
```

---

## Assertion Patterns

### Basic Assertions

```python
# Boolean
self.assertTrue(result)
self.assertFalse(result)

# Equality
self.assertEqual(a, b)
self.assertNotEqual(a, b)

# Identity (for mocks)
self.assertIs(obj1, obj2)  # Same object
self.assertIsNot(obj1, obj2)

# Null checks
self.assertIsNone(result)
self.assertIsNotNone(result)

# Numeric comparisons
self.assertGreater(count, 3)
self.assertGreaterEqual(count, 3)
self.assertLess(count, 10)
self.assertLessEqual(count, 10)
```

### String Assertions

```python
# Contains
self.assertIn("substring", full_string)
self.assertNotIn("missing", full_string)

# Regex
self.assertRegex(text, r"pattern")
self.assertNotRegex(text, r"pattern")
```

### Collection Assertions

```python
# List/Dict
self.assertIn(item, collection)
self.assertEqual(len(collection), 5)
self.assertListEqual(list1, list2)
self.assertDictEqual(dict1, dict2)
```

### Exception Assertions

```python
# Expect exception
with self.assertRaises(GsxMenuError):
    self.component.operation()

# With message check
with self.assertRaises(GsxMenuError) as context:
    self.component.operation()
self.assertIn("expected text", str(context.exception))
```

### GsxMenuNotChangedError Pattern

**New in v0.8.8:** Test uncertain gate assignments

```python
def test_menu_not_changed_handling(self):
    """Test handles menu not changing gracefully"""
    with self.assertRaises(GsxMenuNotChangedError) as context:
        gate_assignment.assign_gate("KLAX", gate_number="5")

    # Verify returns uncertain flag
    self.assertIn("may have still succeeded", str(context.exception))
```

### Mock Call Assertions

```python
# Called once
mock.method.assert_called_once()
mock.method.assert_called_once_with(arg1, arg2)

# Called with (any number of times)
mock.method.assert_called_with(arg1, arg2)

# Call count
self.assertEqual(mock.method.call_count, 3)
self.assertGreater(mock.method.call_count, 1)

# Not called
mock.method.assert_not_called()

# Verify specific call exists
mock.method.assert_any_call(arg1, arg2)

# Verify call sequence
mock.assert_has_calls([
    call.method1(arg1),
    call.method2(arg2)
])
```

### Side Effect Verification

```python
def test_side_effect_consumed(self):
    """Test all side effect values consumed"""
    mock.method.side_effect = [1, 2, 3]

    results = [mock.method() for _ in range(3)]

    self.assertListEqual(results, [1, 2, 3])
    self.assertEqual(mock.method.call_count, 3)
```

---

## Running Tests

### Run All Tests

```bash
# Using unittest
python -m unittest discover tests

# Verbose output
python -m unittest discover tests -v

# Using pytest (if installed)
pytest tests/ -v
```

### Run Single File

```bash
python -m unittest tests.test_gate_assignment -v
```

### Run Single Test

```bash
python -m unittest tests.test_gate_assignment.TestGateAssignment.test_find_gate_exact_match -v
```

### Run with Coverage (if coverage.py installed)

```bash
coverage run -m unittest discover tests
coverage report
coverage html  # Generates htmlcov/index.html
```

---

## Test File Index

| Test File | Module Under Test | Test Count | Key Coverage |
|-----------|-------------------|------------|--------------|
| `test_config.py` | `gad_config.py` | 35+ | YAML loading, saving, defaults, computed fields, round-trip, float preservation |
| `test_director.py` | `director.py` | ~10 | Queue processing, threading, gate callbacks |
| `test_gate_assignment.py` | `gate_assignment.py` | 11 | Fuzzy matching, assignment workflow, ground waiting, API calls |
| `test_gate_management_parsing.py` | `ui/gate_management.py` | 6 | Size parsing, jetway parsing, rename/move operations |
| `test_gate_parser.py` | `si_api_hook.py` (GateParser) | 20 | Regex parsing, various gate formats, edge cases |
| `test_gsx_hook.py` | `gsx_hook.py` | 19 | Initialization, dependency order, retry logic, cleanup |
| `test_menu_logger.py` | `menu_logger.py` | ~15 | Gate extraction, mapping, airport data generation |
| `test_menu_navigator.py` | `menu_navigator.py` | 13 | Click operations, search, pagination, planned navigation |
| `test_menu_reader.py` | `menu_reader.py` | ~12 | File reading, change detection, menu state parsing |
| `test_si_api_hook.py` | `si_api_hook.py` (JSONMonitor) | ~20 | File monitoring, change detection, gate callbacks |
| `test_simconnect_manager.py` | `simconnect_manager.py` | 12 | Connection, variable reading/writing, ground detection, disconnection edge cases |

**Total:** 250 tests

---

## Common Pitfalls

### Pitfall 1: Missing Logging Attributes

**Problem:**
```python
mock_config = Mock()
# ... missing logging_level, logging_format, logging_datefmt
component = Component(mock_config)  # Component calls logging.basicConfig → TypeError
```

**Solution:** Use `create_mock_config()` template (includes all attributes)

### Pitfall 2: Mock Comparison with assertEqual

**Problem:**
```python
mock_config = Mock(spec=GsxConfig)
self.assertEqual(call_args[0], mock_config)  # AttributeError: Mock object has no attribute 'username'
```

**Solution:** Use `assertIs` for mock identity checks:
```python
self.assertIs(call_args[0], mock_config)
```

### Pitfall 3: Mock Objects Not Iterable/Len-able

**Problem:**
```python
mock_menu_reader.previous_state.options = Mock()
len(mock_menu_reader.previous_state.options)  # TypeError: object of type 'Mock' has no len()
```

**Solution:** Set as actual list:
```python
mock_menu_reader.previous_state.options = ["Option 1", "Option 2"]
```

### Pitfall 4: Forgetting to Mock HTTP Requests

**Problem:**
```python
# Test makes real HTTP call → slow, network-dependent, may fail
result = gate_assignment.assign_gate("KLAX", gate_number="5")
```

**Solution:** Patch requests:
```python
@patch('GateAssignmentDirector.gate_assignment.requests.get')
def test_assign_gate(self, mock_requests):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_requests.return_value = mock_response
    # ... test
```

### Pitfall 5: Wrong Patch Path

**Problem:**
```python
@patch('requests.get')  # Patches wrong module
def test_api_call(self, mock_requests):
    ...  # Doesn't actually patch the import
```

**Solution:** Patch where it's imported:
```python
@patch('GateAssignmentDirector.gate_assignment.requests.get')  # Patches actual import
```

### Pitfall 6: Not Resetting Mocks Between Tests

**Problem:**
```python
def test_first(self):
    self.mock.method()
    self.assertEqual(self.mock.method.call_count, 1)

def test_second(self):
    self.mock.method()
    self.assertEqual(self.mock.method.call_count, 1)  # FAILS - call_count is 2!
```

**Solution:** Use `setUp()` to create fresh mocks for each test, or manually reset:
```python
def setUp(self):
    self.mock = Mock()  # Fresh for each test
```

### Pitfall 7: Side Effect Exhausted

**Problem:**
```python
mock.method.side_effect = [1, 2]
mock.method()  # Returns 1
mock.method()  # Returns 2
mock.method()  # Raises StopIteration
```

**Solution:** Provide enough values or use infinite iterator:
```python
mock.method.side_effect = itertools.cycle([1, 2])  # Infinite
```

### Pitfall 8: Testing Implementation Instead of Behavior

**Bad:**
```python
def test_uses_specific_algorithm(self):
    """Test calls internal helper method"""
    self.component._internal_method.assert_called()  # Testing implementation
```

**Good:**
```python
def test_returns_correct_result(self):
    """Test produces correct output"""
    result = self.component.public_method(input_data)
    self.assertEqual(result, expected_output)  # Testing behavior
```

---

## Testing Best Practices

### 1. Test One Thing Per Test

```python
# ❌ Bad: Multiple assertions unrelated
def test_everything(self):
    self.assertTrue(component.initialize())
    self.assertEqual(component.count, 0)
    self.assertIsNone(component.find_gate("invalid"))

# ✅ Good: One concept per test
def test_initialize_returns_true_on_success(self):
    self.assertTrue(component.initialize())

def test_initial_count_is_zero(self):
    self.assertEqual(component.count, 0)

def test_find_gate_returns_none_for_invalid_input(self):
    self.assertIsNone(component.find_gate("invalid"))
```

### 2. Use Descriptive Test Names

```python
# ❌ Bad
def test_gate(self):

# ✅ Good
def test_find_gate_returns_none_when_no_match_found(self):
```

### 3. Use Docstrings

```python
def test_fuzzy_matching_threshold(self):
    """Test fuzzy matching returns best match even with low score"""
```

### 4. Arrange-Act-Assert Pattern

```python
def test_example(self):
    # Arrange: Set up test data and mocks
    mock_data = {"terminals": {...}}
    self.mock_reader.read.return_value = mock_data

    # Act: Execute the code under test
    result = self.component.operation()

    # Assert: Verify expected outcome
    self.assertEqual(result, expected_value)
```

### 5. Test Edge Cases

- Empty inputs
- None values
- Maximum/minimum values
- Invalid formats
- Network failures
- File not found

### 6. Don't Test External Libraries

**Don't test:**
- rapidfuzz works correctly
- Python-SimConnect connects

**Do test:**
- Your code calls rapidfuzz with correct parameters
- Your code handles SimConnect connection failures

---

**See also:**
- [architecture.md](./architecture.md) - Component structure for testing
- [data-structures.md](./data-structures.md) - Data models used in tests
- [README.md](./README.md) - General overview

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.9] - 2025-09-30

### Added
- Retry logic for gate assignment at GsxHook boundary level
- `_close_menu()` helper method for proper menu cleanup before retry

### Fixed
- Removed exception swallowing in gate_assignment.py that hid airline selection failures
- Gate assignment now properly reports failures instead of silently continuing

### Changed
- Airline click errors now bubble up to outer exception handler
- Failed gate assignments trigger automatic retry after closing and reopening menu

### Improved
- Gate assignment reliability with automatic retry on failure
- Error visibility for debugging GSX menu issues

## [0.7.8] - 2025-09-30

### Added
- AGENT_KNOWLEDGE.md with comprehensive codebase documentation for AI agents
- Complete unit test suite for config.py (test_config.py) with 27 tests
- Test coverage for YAML loading, saving, default values, and computed fields
- Round-trip configuration testing for save/load operations

### Changed
- Added AGENT_KNOWLEDGE.md to .gitignore to keep it out of version control

### Improved
- Testing coverage with comprehensive config module validation
- Documentation for AI agents working on the codebase

## [0.7.7] - 2024-09-30

### Fixed
- Removed repeated calls to `config.from_yaml()` - now uses `self.config` instance directly throughout
- Changed broad `Exception` catch in `_cleanup_partial_init()` to specific exceptions `(OSError, RuntimeError, AttributeError)`

### Changed
- Removed duplicate `logging.basicConfig` call from `__init__` (already configured in config module)
- Simplified initialization by passing `self.config` instead of `self.config.from_yaml()` to all components

### Improved
- Code efficiency by eliminating unnecessary config reloading
- Exception handling specificity in cleanup method

## [0.7.6] - 2024-09-30

### Added
- Complete type hints for all director.py methods and parameters
- Type annotations for instance variables (`monitor`, `monitor_thread`, `current_airport`)

### Fixed
- Bug in `__main__` block accessing `GsxConfig.flight_json_path` as class attribute instead of instance attribute
- Parameter spacing inconsistency in `assign_gate_when_ready()` call (`terminal =` and `terminal_number =`)
- Changed `except queue.Empty: continue` to `except queue.Empty: pass` for clarity

### Changed
- Removed duplicate `logging.basicConfig` call from `__init__` (already configured in config module)
- Added typing imports (`Dict`, `Any`, `Optional`)

### Improved
- Type safety with proper type hints throughout
- Code consistency with proper parameter spacing

## [0.7.5] - 2024-09-30

### Added
- Module-level `GATE_PATTERN` compiled regex for improved performance
- `Callable` and `asdict` imports from typing and dataclasses

### Fixed
- Critical bug in `load_config()` checking wrong variable (`config` module instead of `_config` ConfigParser instance)
- Type hint for `gate_callback` parameter changed from `Optional[callable]` to `Optional[Callable]`
- Return type hints added for `__str__()`, `__init__()`, `log_change()`, and `monitor()`

### Changed
- Removed `unittest` import and entire `if __name__ == "__main__"` block (lines 6, 345-357)
- Removed unused `self.match` instance variable from `GateParser.__init__`
- Moved regex pattern compilation from instance-level to module-level for performance
- Simplified empty string check from `gate_string.strip() == ""` to `not gate_string.strip()`
- Replaced `gate_info.__dict__` with `asdict(gate_info)` for dataclass conversion
- Simplified ternary expressions using `or` operator in `parse_gate()`
- Simplified ternary expressions in `gsx_params` dictionary construction
- Removed duplicate `logging.basicConfig` call from `JSONMonitor.__init__`
- Simplified nested `.get()` calls with `or` operator in `get_log_level_for_field()`
- Added UTF-8 encoding to file open in `read_json()`
- Removed `ground_timeout_default` from config.yaml

### Improved
- Exception handling specificity with targeted exception types:
  - `check_gate_assignment()`: `Exception` → `(KeyError, AttributeError, TypeError)`
  - `call_gsx_gate_finder()` initialization: `Exception` → `(OSError, RuntimeError)`
  - `call_gsx_gate_finder()` execution: `Exception` → `(OSError, RuntimeError, AttributeError)`
  - `read_json()`: `Exception` → `(OSError, IOError)`
  - `monitor()`: `Exception` → `(OSError, RuntimeError)`
- Code readability with cleaner conditional expressions
- Type safety with proper type hints throughout

## [0.7.4] - 2024-09-30

### Added
- Complete return type hints for all simconnect_manager.py methods
- Unit test suite for simconnect_manager.py with 9 comprehensive test cases
- Defensive try-except in connect() for ground check request with helpful error message
- `bool()` cast and exception handling in is_on_ground() for safe None/invalid value handling

### Fixed
- Broad exception handling in simconnect_manager.py now catches specific exceptions `(OSError, ConnectionError, RuntimeError)` instead of generic `Exception`
- AttributeError/TypeError handling in is_on_ground() to safely return False on invalid values

### Changed
- Updated simconnect_manager.py to use `AircraftVariable.ON_GROUND.value` from enums instead of hardcoded byte string
- Removed `ground_timeout` parameter from gate_assignment.assign_gate()
- Changed `_wait_for_ground()` to poll indefinitely without timeout (infinite loop until touchdown)
- Removed `ground_timeout_default` field from GsxConfig dataclass and all related methods
- Removed `--ground-timeout` argument from CLI parser
- Updated all ground waiting tests to reflect indefinite polling behavior
- Removed `test_assign_gate_timeout_waiting_for_ground()` test (no longer applicable)

### Improved
- Error handling specificity in simconnect_manager.py with targeted exception types
- Ground polling reliability - script now continuously monitors and recovers after landing
- Type safety in SimConnect variable access

## [0.7.3] - 2024-09-30

### Added
- Module-level constants for navigation options using GsxMenuKeywords
- Compiled regex patterns for gate/parking extraction (performance improvement)
- Return type hints for all menu_logger.py methods
- Test case for parking menu not extracting gate patterns
- Explicit UTF-8 encoding for all file operations

### Fixed
- Removed unused menu_data dict and hash calculation overhead
- Removed commented-out code (menu_structure, all_menus_by_depth fields)
- Removed commented-out gate pattern from parking_patterns
- Typo in GateInfo docstring (extra quote)
- Empty line in middle of variable assignments
- Specific exception handling (OSError, IOError, json.JSONDecodeError) in load_airport_map()

### Changed
- Simplified menu deduplication using tuple comparison instead of MD5 hash
- Replaced ternary expressions with cleaner `or` operator for regex group handling
- Used dict.setdefault() for cleaner terminal initialization
- Removed hashlib import (no longer needed)

### Improved
- Code readability and maintainability in menu_logger.py
- Performance by compiling regex patterns once at module level
- Type safety with complete type hints
- Modern Python best practices throughout

## [0.7.2] - 2024-09-30

### Added
- Return type hints for menu_reader.py methods
- GsxFileNotFoundError exception raised when GSX menu file not found
- Test coverage for GsxFileNotFoundError exception handling
- Test cases for short menu handling without IndexError

### Fixed
- IndexError in has_changed() when menu has fewer than 3 options
- has_changed() now checks first non-menu-action option instead of hardcoded index
- find_menu_file() now raises exception instead of silently returning None
- Specific exception handling (OSError, IOError) in read_menu()

### Changed
- Magic number 100 replaced with config-based max retries (max_menu_check_attempts * 25)
- Removed unused parameters menu_navigator and sim_manager from MenuReader.__init__

### Improved
- Menu change detection reliability by skipping menu action buttons
- Error handling for missing GSX installation
- Code quality and type safety in menu_reader.py

## [0.7.1] - 2024-09-30

### Added
- Configurable default airline setting (default_airline in config.yaml)
- UI field for default airline configuration in Config tab under GSX Settings
- Complete type hints for all methods in gate_assignment.py

### Fixed
- Print statements replaced with proper logger.debug calls in map_available_spots()
- Broad exception handling in assign_gate() now catches specific exceptions (GsxMenuError, GsxTimeoutError, OSError, IOError)
- Potential KeyError in find_gate() when best_match is None
- Airline search in menu_navigator.py now uses substring matching instead of word-by-word exact matching

### Changed
- Default airline changed from "(UA_2000)" to "GSX" for universal compatibility
- Fuzzy matching threshold reduced from 33 to 10 for better gate matching with low-quality data
- Removed all unnecessary comments from gate_assignment.py

### Improved
- Code quality and maintainability in gate_assignment.py
- Gate matching accuracy with lower fuzzy threshold
- Airline selection flexibility through configuration

## [0.7.0] - 2024-09-30

### Fixed
- Critical bug in gsx_hook.py logging configuration (config vs self.config)
- Logic error in is_on_ground() that called sim_manager before checking initialization
- Redundant check in close() method
- Broad exception handling now catches specific exceptions (GsxConnectionError, GsxFileNotFoundError, OSError, IOError)

### Added
- Partial initialization cleanup (_cleanup_partial_init) for proper rollback on errors
- Complete type hints for all methods in gsx_hook.py

### Improved
- Code quality and maintainability in gsx_hook.py
- Consistent logging approach across codebase
- Exception handling specificity

## [0.6.1] - 2024-09-30

### Added
- Build script (build.py) for automated PyInstaller packaging
- Icon conversion to .ico format for Windows executable
- Distribution-ready build configuration with --onedir mode

## [0.6.0] - 2024-09-30

### Added
- README.md with project overview and requirements
- Project status section clarifying no maintenance commitment
- GPL-3.0 free software principles documentation
- Disclaimers for SayIntentions AI and GSX trademarks
- MSFS 2020 compatibility specification

## [0.5.0] - 2024-09-30

### Added
- GPL-3.0 license to ensure free software redistribution
- requirements.txt with all project dependencies
- Proper .gitignore for Python projects

## [0.4.0] - 2024-09-27

### Added
- Comprehensive test suite with 106+ unit tests covering all major components
- UI components with CustomTkinter framework
- System tray integration with pystray
- Custom exception classes (GsxMenuError, GsxTimeoutError, GsxConnectionError)
- Enhanced menu logger with gate/spot extraction
- Gate management window for manual control

### Improved
- Error handling across all modules
- Logging configuration and output

## [0.3.0] - 2024-09-23

### Added
- Intelligent gate parser with regex pattern matching
  - Support for Terminal, Concourse, Pier, Parking, International, Domestic, etc.
- Fuzzy gate matching using rapidfuzz library
- Director class for queue-based gate assignment processing
- Configuration management via YAML
- Threading support for JSON monitoring
- Gate callback system for event-driven processing

### Improved
- Gate assignment workflow with wait-for-ground functionality
- Integration between SayIntentions data and GSX gate assignment

## [0.2.0] - 2024-09-20

### Added
- GSX menu navigation automation (click by index, pagination support)
- Menu state tracking and change detection
- Airport gate mapping system
- Menu logger for capturing GSX menu structure
- Gate data persistence to JSON files
- Navigation tracking (level_0_index, next_clicks, menu_index)
- Interpreted airport data generation

### Improved
- Menu reading with enumeration support
- State comparison logic

## [0.1.0] - 2024-09-18

### Added
- Initial SimConnect integration via Python-SimConnect
- Basic GSX menu file reading from local filesystem
- JSON file monitoring for SayIntentions flight data
- Simple gate string parsing (GateInfo dataclass)
- Basic configuration loading
- Core project structure and modules
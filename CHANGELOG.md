# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.2] - 2025-10-08

### Added
- TooltipReader module for GSX success confirmation via tooltip monitoring
- Tooltip-based success detection (marshaller dispatched, follow me car, boarding, safedock activated)
- Automatic menu closing on successful gate assignment
- Terminal inference from gate identifiers using heuristic fallback (_infer_terminal_from_gate)
- GSX refresh retry logic in click_by_index() for improved reliability
- Internal retry loop in assign_gate() that avoids wasteful re-matching on navigation failures
- _close_menu() method in gate_assignment.py

### Changed
- Terminal extraction now combines menu context with gate identifier heuristics
- Generic menu fallbacks ("All Gate positions") now trigger intelligent terminal inference
- 3-digit gates without prefix go to "Miscellaneous" terminal (e.g., "Gate 205")
- 3-digit gates with prefix use prefix as terminal (e.g., "Gate K205" → terminal="K")
- SI gate parser now handles letter-prefixed gates (V118, A20, etc.)
- SI terminal extraction from gate prefix (e.g., "Gate V118" → terminal="V", gate="V118")
- level_0_page navigation fixed: now uses range(level_0_page) instead of range(level_0_page - 1)
- Gate assignment retries navigation failures without re-matching (2 attempts)
- Menu closes automatically on confirmed success, stays open on uncertain/failure
- SI airport extraction fixed: now reads from flight_details.current_airport (not nested in current_flight)

### Fixed
- Empty terminal bug in "All X Positions" menus (was returning "" instead of triggering heuristics)
- SI gate parser missing letter prefixes in gate numbers (V118 was parsed as "" instead of "V118")
- Terminal extraction mismatch between GSX (terminal="V") and SI (terminal="Terminal")
- level_0_page off-by-one error causing wrong page navigation in multi-page menus
- GSX navigation failures causing full re-match including expensive gate matching
- Airport detection stuck in infinite "not yet detected" loop due to wrong JSON path

### Technical
- New tooltip_reader.py module with polling-based file monitoring
- tooltip_success_keyphrases and tooltip_file_paths in config.yaml
- Tooltip checks after "activate" click and in exception handlers
- GSX refresh command (-2) restored in click_by_index() for stuck menu recovery
- Terminal inference uses letter prefix detection, digit analysis, and position type
- SI gate parser regex updated to capture [A-Z]?\d+ instead of just \d+
- click_planned() now correctly navigates multi-page menus with 0-indexed pages

## [0.9.1] - 2025-10-07

### Added
- Position keywords now configurable in config.yaml (gsx_gate, gsx_parking, si_terminal)
- "Apron" keyword support for GSX parking menus
- Intelligent fuzzy gate matching with component-based weighted scoring
- GateMatcher module for matching between SI and GSX gate formats
- Version numbering in JSON files for future format migration support
- Configurable matching weights (gate_number: 60%, gate_prefix: 30%, terminal: 10%)
- Pre-parsed gate components stored in JSON (_parsed field) for fast matching

### Changed
- Position interpretation now uses menu title context for terminal extraction
- Terminal names extracted from menu titles (e.g., "Apron - West I" → terminal="West I")
- position_id format now reflects actual type ("Terminal X Stand Y" for parking, "Terminal X Gate Y" for gates)
- Gate identifiers preserve spaces ("Stand V 20" → gate="V 20")
- Gate matching now uses weighted component scoring instead of simple string comparison
- find_gate() refactored to delegate to GateMatcher.find_best_match()

### Fixed
- Menu mapping index bug: now saves actual menu indices instead of filtered list indices
- Gate/stand clicking now targets correct menu positions
- Space preservation in gate identifiers (no more "StandV20" → "StandV")
- Improved gate matching handles mismatched formats (e.g., "Apron V Spot 19" vs "East III Stand V19")

### Technical
- New gate_matcher.py module with GateMatcher class
- Component parsing: gate_number, gate_prefix, gate_suffix extraction with regex
- Weighted scoring with configurable weights via config.yaml
- 13 new tests in test_gate_matcher.py
- All 60 tests passing (31 menu_logger + 16 gate_assignment + 13 gate_matcher)
- Removed space-stripping and complex digit-based terminal heuristics
- Added helper methods: _extract_terminal_from_menu, _extract_gate_identifier

## [0.8.9] - 2025-10-05

### Added
- Gate Management Window: Multi-select gates/terminals with Ctrl/Shift+Click
- Gate Management Window: Conflict detection when moving gates (warns about overwrites)
- Gate Management Window: Alphanumeric sorting on save (Gate 2 before Gate 10)
- Gate Management Window: Unsaved changes tracking with confirmation dialog on close
- Gate Management Window: Working copy pattern (changes only saved when explicitly requested)
- Gate Management Window: Auto-fill input fields when selecting gates/terminals from tree
- Gate Management Window: Reset Data function to re-parse interpreted airport data
- "Dock" keyword support in menu logger for airports using Dock instead of Gate
- Configurable keyword lists (GATE_KEYWORDS, PARKING_KEYWORDS) for easy extension
- 29 comprehensive unit tests for Gate Management Window features (test_gate_management_window.py)

### Changed
- Gate Management Window: Terminal click now selects all child gates for bulk operations
- Gate Management Window: Move Gate function now processes multiple gates in single operation
- Gate Management Window: Empty source terminals automatically removed after gate moves
- Override buttons (Apply/Clear) now disabled during monitoring to prevent UI blocking
- Menu logger now uses keyword lists instead of hardcoded string checks

### Fixed
- Airport override now persists in UI when monitoring starts (stays as "EDDS (MANUAL)")
- Prevented airport label from being overwritten by monitoring when override is active
- Menu logger now recognizes "Dock" gates in addition to "Gate" gates

### Improved
- Gate Management Window workflow: Click terminal → all gates selected → specify destination → move entire terminal
- Data safety: All operations modify working copy only, changes require explicit save
- User protection: Warns before overwriting gates, confirms before closing with unsaved changes
- Natural sorting ensures gates display in logical order (1, 2, 10 instead of 1, 10, 2)

### Technical
- All 259 tests pass (230 existing + 29 new Gate Management Window tests)
- Gate Management Window uses deep copy pattern for data integrity
- Alphanumeric sorting uses regex-based natural sort key algorithm

## [0.8.8] - 2025-10-02

### Added
- Success messages now shown in Recent Activity when gate is assigned ("Successfully assigned to gate: A23")
- Strategic startup pauses with informative progress messages for smoother UX
- Status callback system for director to push progress updates to UI
- Airport label debouncing (300ms) to prevent flickering through multiple states
- `GsxMenuNotChangedError` exception for uncertain gate assignments (menu didn't update but action may have succeeded)
- Unit test for float type preservation in config loading
- Unit tests for `GsxMenuNotChangedError` handling (2 tests)
- Early exit check for empty GSX menus to prevent loop execution issues

### Changed
- Startup flow now displays incremental progress: "Initializing monitoring system" → "Connected to flight data source" → "Gate assignment system ready"
- GSX initialization messages show "Connecting to GSX system..." and "GSX connection established"
- Airport parking analysis shows contextual message when mapping data
- Error messages in Recent Activity now user-friendly and simplified (e.g., "GSX menu issue - check logs if persistent")
- Menu navigation errors that might not be actual failures now marked as uncertain instead of failed
- Float config values (sleep_short, sleep_long, ground_check_interval, aircraft_request_interval) now explicitly converted to float on load

### Fixed
- Config float values being saved as integers in YAML when whole numbers (1.0 → 1)
- Float fields in config UI now always display with decimal notation (e.g., "1.0" not "1")
- Build script now includes SimConnect.dll in PyInstaller bundle
- Build script unicode errors on Windows console (replaced checkmarks/warnings with [OK]/[WARN])
- Gate assignments no longer marked as failed when menu doesn't change (now uncertain with user prompt to verify)

### Improved
- Startup experience feels more deliberate and informative instead of "everything at once"
- Recent Activity panel shows actionable, concise messages instead of technical error dumps
- User confidence with clear feedback at each initialization step
- Build process robustness with automatic DLL detection and inclusion

### Technical
- All 230 tests pass
- Added `import time` to director.py for startup pauses
- Director tests mock `time.sleep` to avoid actual delays in test execution
- UI tests updated for new `threading.Timer`-based startup flow

## [0.8.7] - 2025-09-30

### Changed
- Renamed configuration file from `config.py` to `gad_config.py` for clarity
- Renamed `GsxConfig` class to `GADConfig` (Gate Assignment Director Config)
- Updated all imports across 10 files to use new naming
- Configuration naming now reflects project-wide scope (not GSX-specific)

### Technical
- All 183 tests pass with new configuration naming
- No functional changes, purely refactoring for better naming consistency

## [0.8.6] - 2025-09-30

### Fixed
- GsxHook now properly uses provided config parameter instead of always loading from YAML
- Gate assignment handles None values in terminal/gate parameters with proper null coalescing
- Fuzzy gate matching now returns best match even with 0% score (changed threshold from 10 to 0)
- Test mocks updated with required logging configuration attributes
- Menu navigator tests properly mock MenuState for navigation operations
- Gate assignment test now mocks API requests to prevent real HTTP calls
- Gate parser test updated to check module-level GATE_PATTERN instead of instance attribute

### Changed
- Improved fuzzy matching score comparison from `>` to `>=` for edge cases with identical scores

## [0.8.5] - 2025-09-30

### Added
- Centralized color palette system with semantic color naming and hover variants
- Unit tests for SimConnect disconnection edge case handling

### Changed
- UI corner radius standardized to 6px across all elements for modern aesthetic
- Color system refactored to use dataclass-based palette with usage tracking
- Tab selector styling updated with harmonized color scheme

### Fixed
- SimConnect crash when attempting to set variables after disconnection
- Config tests updated to reflect timing values now in seconds

## [0.8.4] - 2025-09-30

### Changed
- Restyled UI elements for more uniform appearance with consistent sizing
- Config tab input fields now have variable widths appropriate to their content (API keys wider, numeric fields narrower)
- Label styling updated with optional bold parameter and consistent padding
- Main window size constraints adjusted for better flexibility (350x430 min, 800x800 max)

### Fixed
- Log textboxes now read-only to prevent accidental user edits while still allowing programmatic updates

## [0.8.3] - 2025-09-30

### Added
- Values statement at bottom of main window

## [0.8.2] - 2025-09-30

### Fixed
- _label() helper function chaining - now uses side parameter instead of .pack() return
- Label width issue causing excessive spacing between labels and inputs
- Import path for GateAssignmentDirector in main_window.py
- Missing UI widget initializations in DirectorUI.__init__

### Changed
- _label() width parameter now optional (None by default) for auto-sizing labels
- Gate management UI fonts increased for better readability (titles 16-20px, status 14px)
- Input field spacing optimized - 2px gap to label, 15px between pairs
- Status section moved below tree view with buttons stacked on right
- Reload Data and Save Changes button height reduced to 28px

### Improved
- Gate management window minimum size set to 1000x700
- Label-to-input visual grouping with proper spacing
- UI widget type hints and IDE compatibility

## [0.8.1] - 2025-09-30

### Added
- Rename Gate function in gate management UI to edit gate full_text information
- Compact horizontal layout for gate input controls (Gate/From/To on same row)
- Unit tests for rename_gate() function (6 tests covering edge cases and happy path)

### Changed
- Replaced Type column with Full Text column in tree view to show raw GSX menu data
- Move Gate controls now use compact horizontal rows instead of vertical stacked layout
- Full Text column width increased to 200px for better readability

### Improved
- Gate management UI compactness and space utilization
- Data visibility with full raw GSX text displayed instead of gate type
- User workflow for manual gate data corrections via rename function

## [0.8.0] - 2025-09-30

### Added
- Rich column display in gate management UI tree view
- Aircraft size column (Small/Medium/Heavy) parsed from GSX menu data
- Jetway configuration column (1x /J, None, etc.)
- Terminal and type columns for better data visibility
- Defensive parsing functions (`_parse_gate_size()`, `_parse_jetway_count()`)
- Auto-load feature - gate data loads automatically when window opens
- Unit tests for parsing functions (6 tests in test_gate_management_parsing.py)
- Graceful handling for missing airport data files

### Changed
- Gate management tree view now uses structured columns instead of single text line
- Tree displays "Gate {number}" instead of "Gate {number} (type)" for cleaner layout
- "Load Current Data" button renamed to "Reload Data" (data auto-loads on open)

### Improved
- Gate data visibility - users can see size and jetway info at a glance
- Data parsing with graceful fallbacks (Unknown/- for missing data)
- UI readability with organized column structure
- User experience - no extra click needed to load data

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
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
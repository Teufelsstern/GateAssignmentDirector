# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
# Agent Documentation - GateAssignmentDirector

**Version:** 0.8.8+
**Last Updated:** 2025-10-02

Welcome to the modular agent documentation for the SayIntentionsBridge (GateAssignmentDirector) project. This documentation is split by domain to help specialized AI agents quickly find relevant information.

## Quick Start

**Project Purpose:** Bridge between SayIntentions AI and GSX (Ground Services X) for automatic gate assignment in Microsoft Flight Simulator 2020.

**Language:** Python 3.11+
**License:** GPL-3.0

## Documentation Structure

This documentation is organized by domain. Navigate to the section most relevant to your work:

### 📐 [architecture.md](./architecture.md)
**For:** feature-architect, holistic-code-analyzer
**Contains:** Layered architecture, component relationships, initialization order, threading model, configuration system, exception hierarchy, entry points, data flow patterns

### 📊 [data-structures.md](./data-structures.md)
**For:** gsx-si-data-expert
**Contains:** GateInfo dataclass, MenuState structure, airport JSON formats, SayIntentions flight.json, gate parsing regex, fuzzy matching algorithm, menu mapping, gate management operations

### 🧪 [testing.md](./testing.md)
**For:** unit-test-expert
**Contains:** Test suite organization, mock setup patterns, common fixtures, assertion patterns, test file index, running tests, common pitfalls

### 🎨 [ui-system.md](./ui-system.md)
**For:** color-harmony-expert
**Contains:** UI architecture, centralized color palette system, component hierarchy, helper functions, widget state management, threading for UI updates, styling standards

## High-Level Architecture

```
Director (Orchestrator)
    ↓
SI API Hook (SayIntentions Monitor) → Queue → GSX Hook (Main Interface)
                                                    ↓
                                    ┌───────────────┴───────────────┐
                                    ↓                               ↓
                        SimConnect Manager              Menu System (Reader/Navigator/Logger)
                                    ↓                               ↓
                              MSFS/SimConnect                  GSX Menu Files
```

**Key Flow:**
1. JSONMonitor watches SayIntentions `flight.json` for gate assignments
2. Director queues gate assignment requests
3. GsxHook orchestrates menu navigation via SimConnect
4. GateAssignment performs fuzzy matching and menu navigation
5. MenuNavigator automates GSX menu clicks
6. Result: Aircraft positioned at correct gate in GSX

## Module Index

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `director.py` | Orchestration, queue management | `GateAssignmentDirector` |
| `si_api_hook.py` | SayIntentions integration | `JSONMonitor`, `GateParser`, `GateInfo` |
| `gsx_hook.py` | Main GSX interface | `GsxHook` |
| `gate_assignment.py` | Assignment logic, fuzzy matching | `GateAssignment` |
| `simconnect_manager.py` | SimConnect wrapper | `SimConnectManager` |
| `menu_reader.py` | GSX menu file reading | `MenuReader`, `MenuState` |
| `menu_navigator.py` | Menu automation | `MenuNavigator` |
| `menu_logger.py` | Menu mapping & logging | `MenuLogger` |
| `gad_config.py` | Configuration management | `GADConfig` |
| `gsx_enums.py` | Type-safe constants | `SearchType`, `GsxVariable`, etc. |
| `exceptions.py` | Custom exceptions | `GsxError`, `GsxMenuError`, etc. |

### UI Components (Optional)

| Module | Purpose |
|--------|---------|
| `ui/main_window.py` | CustomTkinter main window, system tray |
| `ui/monitor_tab.py` | Flight monitoring tab |
| `ui/config_tab.py` | Configuration editor |
| `ui/logs_tab.py` | Log viewer |
| `ui/gate_management.py` | Manual gate control window |
| `ui/ui_helpers.py` | Color palette, helper functions |

## Common Patterns

### 1. Exception Handling
```python
# ✅ Good: Specific exceptions
try:
    result = self.operation()
except (OSError, RuntimeError, AttributeError) as e:
    logger.error(f"Operation failed: {e}")

# ❌ Bad: Broad exceptions
except Exception as e:  # Too broad!
```

### 2. Type Hints
```python
# All public methods require type hints
def find_gate(self, airport_data: Dict[str, Any], terminal: str, gate: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    ...
```

### 3. Logging
```python
# Module-level logger
import logging
logger = logging.getLogger(__name__)

# Usage
logger.debug("Detailed info")
logger.info("Status update")
logger.error(f"Failed: {e}")

# Never use print()!
```

### 4. Configuration Access
```python
# Option 1: Global instance
from GateAssignmentDirector.gad_config import config
path = config.flight_json_path

# Option 2: Instance passed in constructor
def __init__(self, config: GADConfig):
    self.config = config
```

### 5. File Operations
```python
# Always UTF-8
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
```

## Version-Specific Notes

### v0.8.8 (Current)
- Status callback system for director → UI updates
- Airport pre-mapping functionality
- Progressive startup with informative messages
- Test count: 250 tests (was 183)
- User-friendly error messages in Recent Activity

### v0.8.7
- Configuration renamed: config.py → gad_config.py
- GsxConfig class → GADConfig
- All imports updated across 10 files

### v0.8.6
- GsxHook now respects provided config parameter
- Fuzzy matching threshold changed from 10 to 0
- Gate assignment handles None values with null coalescing
- SimConnect disconnection crash fixed

### v0.8.5
- Centralized color palette system (dataclass-based)
- UI corner radius standardized to 6px
- Tab styling with harmonized colors

### v0.7.7
- Removed repeated `config.from_yaml()` calls
- Exception handling specificity improvements

### v0.7.4
- Ground timeout removed (infinite polling)
- SimConnect improvements

## Glossary

- **GSX**: Ground Services X - third-party MSFS add-on
- **SI**: SayIntentions AI - AI-powered ATC
- **MSFS**: Microsoft Flight Simulator 2020
- **SimConnect**: Microsoft's flight sim API
- **L:Var**: Local variable in SimConnect (add-on variables)
- **ICAO**: Airport codes (e.g., KLAX)
- **Fuzzy Matching**: Approximate string matching

## Project Standards

**Naming:**
- Classes: `PascalCase`
- Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Code Organization:**
- One class per file (except dataclasses)
- Type hints required
- Docstrings for public methods
- Never use `print()` - use logging

## Entry Points

| Entry Point | File | Purpose |
|-------------|------|---------|
| CLI | `cli_gsx.py` | Command-line gate assignment |
| Director | `director.py` (main block) | Automated monitoring |
| UI | `ui.py` | GUI with system tray |

## Dependencies

| Library | License | Purpose |
|---------|---------|---------|
| PyYAML | MIT | Config parsing |
| rapidfuzz | MIT | Fuzzy gate matching |
| requests | Apache 2.0 | HTTP (SI API) |
| Python-SimConnect | AGPL-3.0 | MSFS interface |
| CustomTkinter | MIT | UI framework |
| pystray | GPL-3.0 | System tray |

## Need More Detail?

Navigate to the specialized documentation files above based on your domain of work. Each file contains deep-dive information relevant to specific agent types.

---

*This modular structure was created in v0.8.6 to improve agent efficiency. The legacy `AGENT_KNOWLEDGE.md` at project root is deprecated.*

**Note:** This file was renamed from `README.md` to `OVERVIEW.md` to avoid conflict with the project root README.

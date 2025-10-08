# Architecture Documentation

**For:** feature-architect, holistic-code-analyzer

This document covers the system architecture, component relationships, initialization patterns, threading model, and integration points.

## Table of Contents

- [Layered Architecture](#layered-architecture)
- [Component Relationships](#component-relationships)
- [Initialization Order](#initialization-order)
- [Threading Model & Data Flow](#threading-model--data-flow)
- [Configuration System](#configuration-system)
- [Exception Hierarchy](#exception-hierarchy)
- [Entry Points](#entry-points)
- [State Management](#state-management)
- [Build & Deployment](#build--deployment)

---

## Layered Architecture

The system follows a clean layered architecture with separation of concerns:

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  (UI, CLI, DirectorUI, System Tray)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Orchestration Layer               │
│  (Director, Queue Management)           │
└──────┬────────────────────┬─────────────┘
       │                    │
┌──────▼───────┐     ┌──────▼──────────────┐
│   SI Hook    │     │     GSX Hook        │
│  (Monitor)   │────▶│ (Main Interface)    │
└──────────────┘     └─────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
┌─────────▼────────┐ ┌──────▼─────┐ ┌────────▼──────┐
│ SimConnect Mgr   │ │ Menu Reader│ │ Menu Navigator│
└─────────┬────────┘ └────────────┘ └───────────────┘
          │
┌─────────▼────────┐
│   MSFS/GSX       │
│  (External)      │
└──────────────────┘
```

### Layer Responsibilities

**Presentation Layer:**
- User interaction (GUI, CLI)
- Status display and logging
- Configuration editing
- No business logic

**Orchestration Layer:**
- Thread management
- Queue-based processing
- Coordinating between SI and GSX
- Error recovery

**Integration Layer:**
- SI API Hook: Monitor flight.json, parse gates
- GSX Hook: Menu navigation, gate assignment

**Infrastructure Layer:**
- SimConnect communication
- File system operations
- Configuration management

---

## Component Relationships

### Core Components

#### **1. Director (Orchestrator)**
**File:** `GateAssignmentDirector/director.py`
**Role:** Top-level orchestrator

**Dependencies:**
- `SIAPIHook` (JSONMonitor) - monitors flight data
- `GsxHook` - executes gate assignments
- `queue.Queue` - thread-safe communication

**Lifecycle:**
```python
director = GateAssignmentDirector()
director.start_monitoring(flight_json_path)  # Starts monitoring thread
director.process_gate_assignments()           # Blocks processing queue
director.stop()                               # Cleanup
```

#### Director State Management

**Status Callback System (v0.8.8):**
- `status_callback: Optional[Callable]` - Callback for UI status updates
- Called from background thread with progress messages
- Enables progressive startup and real-time feedback

**Airport Override (v0.8.8+):**
- `airport_override: Optional[str]` - Manual airport selection
- Bypasses automatic airport detection
- Used for testing and manual control

**Airport Pre-mapping:**
- `mapped_airports: set` - Tracks pre-mapped airports
- Automatically maps parking layout on first airport detection
- Reduces delay on first gate assignment

#### **2. SI API Hook**
**File:** `GateAssignmentDirector/si_api_hook.py`
**Role:** SayIntentions integration

**Components:**
- `JSONMonitor`: File watcher with change detection
- `GateParser`: Regex-based gate string parser
- `GateInfo`: Dataclass for parsed gates

**Key Pattern:** Module-level `GATE_PATTERN` compiled regex

#### **3. GSX Hook**
**File:** `GateAssignmentDirector/gsx_hook.py`
**Role:** Main GSX automation interface

**Dependencies (in initialization order):**
1. `SimConnectManager`
2. `MenuLogger`
3. `MenuReader`
4. `MenuNavigator`
5. `GateAssignment`

**Public Methods:**
- `assign_gate_when_ready()` - Main entry point with retry logic
- `is_on_ground()` - Aircraft status check
- `close()` - Cleanup and disconnection

#### **4. Gate Assignment**
**File:** `GateAssignmentDirector/gate_assignment.py`
**Role:** Core gate assignment logic

**Key Methods:**
- `assign_gate()` - Full workflow with ground wait
- `map_available_spots()` - Generate airport gate mapping
- `find_gate()` - Fuzzy matching algorithm
- `_wait_for_ground()` - Infinite polling until touchdown

**Gate Matching (v0.9.2+):** Uses `GateMatcher` for intelligent fuzzy matching with component-based weighted scoring. Replaced direct rapidfuzz usage.

#### **5. SimConnect Manager**
**File:** `GateAssignmentDirector/simconnect_manager.py`
**Role:** Wrapper around Python-SimConnect

**Responsibilities:**
- Connection lifecycle management
- Variable reading/writing
- Ground detection
- Request creation

**Critical:** Must check `self.connection` before operations (v0.8.5 fix)

#### **6. Menu System**

**MenuReader** (`menu_reader.py`):
- Reads GSX menu file from filesystem
- Detects menu changes
- Polling with configurable retries

**MenuNavigator** (`menu_navigator.py`):
- Automates menu clicks
- Search by keyword/airline/terminal
- Pagination handling

**MenuLogger** (`menu_logger.py`):
- Captures GSX menu structure
- Extracts gates/parking
- Generates airport mappings
- Terminal inference from gate identifiers (v0.9.2+)

#### **7. Gate Matching System**
**File:** `GateAssignmentDirector/gate_matcher.py`
**Role:** Intelligent fuzzy gate matching (v0.9.2+)

**Algorithm:**
Component-based weighted scoring system that parses gate identifiers into:
- `gate_number`: Numeric component (weight: 0.6)
- `gate_prefix`: Letter prefix/identifier like "V", "Stand" (weight: 0.3)
- `gate_suffix`: Letter suffix like "A", "B"
- `terminal`: Terminal name (weight: 0.1)

**Matching Process:**
1. Try exact match first (terminal + gate)
2. If no exact match, parse both SI and GSX gates into components
3. Calculate component similarity scores using rapidfuzz
4. Apply weighted formula: `final_score = (num * 0.6) + (prefix * 0.3) + (terminal * 0.1)`
5. Return best match above minimum threshold (default 70.0)

**Example Parsing:**
- "V19" → {number: "19", prefix: "V", suffix: ""}
- "5A" → {number: "5", prefix: "", suffix: "A"}
- "Stand 501" → {number: "501", prefix: "STAND", suffix: ""}

**Integration:** Used by `GateAssignment.find_gate()` to handle mismatches between SI and GSX gate formats.

#### **8. Success Confirmation**
**File:** `GateAssignmentDirector/tooltip_reader.py`
**Role:** GSX operation success detection (v0.9.2+)

**Purpose:** Confirms gate assignment success by monitoring GSX tooltip file for success messages, eliminating unreliable menu state polling.

**Mechanism:**
1. Capture baseline tooltip file timestamp before assignment
2. Send gate assignment command via SimConnect
3. Poll tooltip file for updates (default 2.0s timeout, 0.2s intervals)
4. Check updated content for success keyphrases:
   - "marshaller has been dispatched"
   - "follow me car"
   - "boarding"
   - "safedock© system activated"
5. Return success if keyphrase found, failure on timeout

**Integration:** Called by `MenuNavigator.navigate_to_gate()` after sending the final selection command. Provides definitive confirmation rather than relying on menu state changes.

**Configuration:**
- `tooltip_file_paths`: Paths to GSX tooltip file
- `tooltip_success_keyphrases`: List of success indicators
- Configurable timeout and check intervals

---

## Initialization Order

### GsxHook Initialization Sequence

**Critical Order:** Dependencies must be initialized in this exact sequence:

```python
def __init__(self, config: Optional[GADConfig] = None, enable_menu_logging: bool = True):
    # 1. Configuration
    self.config = config if config is not None else GADConfig.from_yaml()

    # 2. SimConnect Manager (no dependencies)
    self.sim_manager = SimConnectManager(self.config)
    self.sim_manager.connect()  # Raises GsxConnectionError on failure

    # 3. Menu Logger (depends on config only)
    self.menu_logger = MenuLogger(self.config)

    # 4. Menu Reader (depends on logger, not navigator yet)
    self.menu_reader = MenuReader(
        self.config, self.menu_logger, None, self.sim_manager
    )

    # 5. Menu Navigator (depends on logger and reader)
    self.menu_navigator = MenuNavigator(
        self.config, self.menu_logger, self.menu_reader, self.sim_manager
    )

    # 6. Gate Assignment (depends on all above)
    self.gate_assignment = GateAssignment(
        self.config,
        self.menu_logger,
        self.menu_reader,
        self.menu_navigator,
        self.sim_manager
    )
```

### Cleanup Pattern

**On Initialization Failure:**
```python
def _cleanup_partial_init(self) -> None:
    """Clean up any partially initialized components"""
    try:
        if self.sim_manager:
            self.sim_manager.disconnect()
    except (OSError, RuntimeError, AttributeError):
        pass  # Ignore cleanup errors
```

**Pattern:** Set components to None, attempt disconnect, swallow cleanup errors

---

## Threading Model & Data Flow

### Threading Strategy

**Main Thread:**
- Director queue processing
- GSX Hook operations
- SimConnect communication

**Worker Thread:**
- JSONMonitor file watching
- Gate change detection
- Queue population

### Data Flow Pattern

```
flight.json (Disk)
    ↓ [File Watch]
JSONMonitor (Thread)
    ↓ [Parse & Detect Change]
GateParser
    ↓ [Create GateInfo]
Queue (Thread-Safe)
    ↓ [Director.process_gate_assignments()]
GsxHook.assign_gate_when_ready()
    ↓ [Wait for ground if needed]
GateAssignment.assign_gate()
    ↓ [Fuzzy match & navigate menus]
GSX Menu (via SimConnect)
```

### Synchronization Points

1. **Queue between SI Hook and Director**
   - Thread-safe queue.Queue
   - Non-blocking put, blocking get with timeout

2. **Menu state polling**
   - MenuReader polls file system
   - Configurable retry with sleep intervals

3. **Ground detection polling**
   - Infinite loop checking is_on_ground()
   - Sleeps between checks (ground_check_interval)

### State Management

**is_initialized Flags:**
- `GsxHook.is_initialized` - Boolean tracking successful init
- Set to `True` only after all components initialized
- Set to `False` on any init failure

**Menu State:**
- `MenuReader.current_state` - Most recent menu read
- `MenuReader.previous_state` - For change detection
- Both are `MenuState` dataclasses

**Monitoring State:**
- `JSONMonitor.monitoring` - Boolean flag
- `JSONMonitor.monitor_thread` - Thread instance
- Changed via `start_monitoring()` and `stop()`

### Airport Pre-mapping Flow

**New in v0.8.8+:** Director pre-maps airports before first assignment

```
process_gate_assignments() detects new airport
    ↓
Check if airport in mapped_airports set
    ↓
If not mapped and on ground:
    Initialize GsxHook if needed
    ↓
    map_available_spots(airport)
    ↓
    Add airport to mapped_airports
    ↓
    Status callback: "Parking layout ready"
```

**Purpose:** Front-loads the 10-30 second mapping process, making actual gate assignments instant.

---

## Configuration System

### GADConfig Dataclass

**File:** `GateAssignmentDirector/gad_config.py`

**All Configuration Fields:**
```python
@dataclass
class GADConfig:
    # Paths
    menu_file_paths: List[str]           # GSX menu file search paths
    tooltip_file_paths: List[str]        # GSX tooltip file paths (v0.9.2+)

    # Timing (all in seconds, changed from ms in v0.8.4)
    sleep_short: float = 0.1             # Short pause
    sleep_long: float = 0.3              # Long pause (changed from 0.1 in v0.9.2)
    ground_check_interval: float = 1.0   # Ground polling interval
    aircraft_request_interval: float = 2.0  # SimConnect request interval
    max_menu_check_attempts: int = 15    # Menu change retries

    # Logging
    logging_level: str = "DEBUG"
    logging_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    logging_datefmt: str = "%H:%M:%S"

    # API & Features
    SI_API_KEY: Optional[str] = None
    default_airline: str = "GSX"         # Universal compatibility

    # UI Settings (v0.8.8+)
    minimize_to_tray: bool = True
    always_on_top: bool = False

    # Gate Matching (v0.9.2+)
    position_keywords: Dict[str, List[str]]  # Terminal/gate classification keywords
    matching_weights: Dict[str, float]       # Component weights for fuzzy matching
    matching_minimum_score: float = 70.0     # Minimum match score threshold
    tooltip_success_keyphrases: List[str]    # Success confirmation phrases

    # Computed Fields (set at runtime)
    username: str = field(default_factory=lambda: os.getenv("USERNAME", "Unknown"))
    flight_json_path: str = field(init=False)

    def __post_init__(self):
        self.flight_json_path = f"C:\\Users\\{self.username}\\AppData\\Local\\SayIntentionsAI\\flight.json"
```

### Configuration Field Purposes (v0.9.2+ additions)

**position_keywords:**
- `gsx_gate`: Keywords to identify gate-type positions (e.g., "Gate", "Dock")
- `gsx_parking`: Keywords for parking/stand positions (e.g., "Parking", "Stand", "Remote")
- `si_terminal`: Keywords that indicate terminal names from SI (used for inference)

**matching_weights:**
- Component importance in fuzzy matching algorithm
- Default: gate_number=0.6, gate_prefix=0.3, terminal=0.1
- Adjustable for different airport naming conventions

**matching_minimum_score:**
- Threshold for accepting fuzzy matches (0-100 scale)
- Default 70.0 balances accuracy vs flexibility

**tooltip_file_paths:**
- Locations to search for GSX tooltip file
- Used by TooltipReader for success confirmation

**tooltip_success_keyphrases:**
- Phrases indicating successful gate assignment
- Checked case-insensitively in tooltip content

### Loading Configuration

```python
# Option 1: From YAML
config = GADConfig.from_yaml()  # Reads GateAssignmentDirector/config.yaml

# Option 2: Programmatic
config = GADConfig(
    menu_file_paths=[...],
    SI_API_KEY="your_key"
)
```

### Configuration File Location

**Default:** `GateAssignmentDirector/config.yaml`

**Format:**
```yaml
SI_API_KEY: "YOUR_API_KEY"
aircraft_request_interval: 2.0  # seconds
ground_check_interval: 1.0
logging_level: DEBUG
default_airline: "GSX"
```

---

## Exception Hierarchy

### Custom Exceptions

**File:** `GateAssignmentDirector/exceptions.py`

```
GsxError (BaseException)
├── GsxMenuError          # Menu operation failures
├── GsxConnectionError    # SimConnect failures
├── GsxTimeoutError       # Operation timeouts
├── GsxFileNotFoundError  # Menu file not found
└── GsxInvalidStateError  # Invalid GSX state
```

### Exception Usage Patterns

**Specific Exception Catching (Required):**
```python
# ✅ Good: Specific exceptions
try:
    result = operation()
except (OSError, RuntimeError, AttributeError) as e:
    logger.error(f"Failed: {e}")

# ❌ Bad: Broad exceptions
except Exception as e:  # Too broad!
```

**Common Exception Combinations by Context:**

| Context | Exceptions to Catch |
|---------|---------------------|
| File I/O | `(OSError, IOError)` |
| SimConnect | `(OSError, ConnectionError, RuntimeError)` |
| JSON parsing | `(OSError, IOError, json.JSONDecodeError)` |
| Initialization | `(OSError, RuntimeError, AttributeError)` |
| Cleanup | `(OSError, RuntimeError, AttributeError)` |

---

## Entry Points

### 1. CLI Entry Point

**File:** `GateAssignmentDirector/cli_gsx.py`

**Usage:**
```bash
python -m GateAssignmentDirector.cli_gsx --airport KLAX --gate 5A --terminal 1
```

**Arguments:**
- `--airport`: ICAO code
- `--gate`: Gate number
- `--terminal`: Terminal identifier
- `--airline`: Airline code (default: GSX)

### 2. Director Entry Point

**File:** `GateAssignmentDirector/director.py` (main block)

**Usage:**
```python
if __name__ == "__main__":
    director = GateAssignmentDirector()
    try:
        director.start_monitoring(director.config.flight_json_path)
        director.process_gate_assignments()
    except KeyboardInterrupt:
        director.stop()
```

### 3. UI Entry Point

**File:** `GateAssignmentDirector/ui.py`

**Features:**
- CustomTkinter GUI
- System tray integration (pystray)
- Multi-tab interface
- Configuration editor

---

## Build & Deployment

### Build Script

**File:** `build.py` (project root)

**Purpose:** Automated PyInstaller packaging

**Output:** Windows executable in `dist/` directory

**Configuration:**
- `--onedir` mode for easier debugging
- Icon conversion to .ico format
- Includes all dependencies

### Setup Script

**File:** `setup.py` (project root)

**Purpose:** Package metadata and installation

### Distribution Strategy

**Current:** Standalone executable via PyInstaller
**Target Platform:** Windows (MSFS/GSX requirement)

---

## Integration Points

### External Dependencies

**MSFS (via SimConnect):**
- Connection required before any GSX operations
- Variables: L:FSDT_GSX_*, SIM ON GROUND
- Failure mode: GsxConnectionError

**GSX (via menu file):**
- File location: `C:\Program Files...\menu`
- Read-only file access
- Failure mode: GsxFileNotFoundError

**SayIntentions (via flight.json):**
- File location: `%LOCALAPPDATA%\SayIntentionsAI\flight.json`
- Polling with change detection
- Failure mode: Silent (retry on next change)

### API Integration

**SayIntentions API:**
- Endpoint: `https://apipri.sayintentions.ai/sapi/assignGate`
- Called when fuzzy match (not direct match)
- Failure mode: Logged but doesn't block assignment

---

## Design Patterns

### 1. Dependency Injection
All components receive dependencies via constructor:
```python
def __init__(self, config: GADConfig, logger: MenuLogger, ...):
    self.config = config
    self.logger = logger
```

### 2. Dataclass for Data Transfer
Use dataclasses for structured data:
```python
@dataclass
class GateInfo:
    terminal_name: Optional[str] = None
    ...
```

### 3. Enum for Constants
Type-safe constants via enums:
```python
class GsxVariable(Enum):
    MENU_OPEN = b"L:FSDT_GSX_MENU_OPEN"
```

### 4. Module-Level Compiled Regex
Performance optimization:
```python
GATE_PATTERN = re.compile(r"...", re.IGNORECASE | re.VERBOSE)
```

### 5. Callback Pattern
Event-driven processing:
```python
monitor = JSONMonitor(config, gate_callback=director.enqueue_gate_assignment)
```

---

## Version-Specific Architectural Changes

### v0.8.8
- Status callback system
- Airport pre-mapping
- max_menu_check_attempts: 4→15
- Progressive startup UX

### v0.8.7
- Config renamed: config.py → gad_config.py, GsxConfig → GADConfig

### v0.8.6
- GsxHook now accepts optional config parameter (was ignored before)
- Null coalescing for parameter concatenation in find_gate()

### v0.8.5
- SimConnect disconnection crash fix (check connection before operations)

### v0.7.7
- Removed repeated config.from_yaml() calls
- Components now use passed config instance

### v0.7.4
- Ground timeout removed
- Infinite polling until aircraft lands

---

**See also:**
- [data-structures.md](./data-structures.md) - Data models and algorithms
- [testing.md](./testing.md) - Testing architecture and patterns
- [README.md](./README.md) - General overview

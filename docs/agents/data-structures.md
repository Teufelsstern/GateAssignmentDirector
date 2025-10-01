# Data Structures Documentation

**For:** gsx-si-data-expert

This document covers all data structures, formats, parsing algorithms, and transformation pipelines in the system.

## Table of Contents

- [GateInfo Dataclass](#gateinfo-dataclass)
- [MenuState Structure](#menustate-structure)
- [Airport Data Formats](#airport-data-formats)
- [SayIntentions flight.json](#sayintentions-flightjson)
- [Gate Parsing Regex](#gate-parsing-regex)
- [Fuzzy Matching Algorithm](#fuzzy-matching-algorithm)
- [Menu Mapping Algorithm](#menu-mapping-algorithm)
- [Gate Management Operations](#gate-management-operations)
- [Data Transformation Pipeline](#data-transformation-pipeline)
- [Edge Cases & Validation](#edge-cases--validation)

---

## GateInfo Dataclass

**File:** `GateAssignmentDirector/si_api_hook.py`

### Definition

```python
@dataclass
class GateInfo:
    """Structured gate information parsed from strings"""
    terminal_name: Optional[str] = None      # "Terminal", "International", "Parking", etc.
    terminal_number: Optional[str] = None    # "1", "A", "B", etc.
    gate_number: Optional[str] = None        # "5", "15", "102", etc.
    gate_letter: Optional[str] = None        # "A", "B", "C", etc. (suffix)
    raw_value: str = ""                      # Original unparsed string

    def __eq__(self, other):
        """Equality comparison"""
        if not isinstance(other, GateInfo):
            return False
        return (
            self.terminal_name == other.terminal_name
            and self.terminal_number == other.terminal_number
            and self.gate_number == other.gate_number
            and self.gate_letter == other.gate_letter
        )

    def __str__(self):
        """Human-readable representation"""
        if not any([self.terminal_name, self.terminal_number, self.gate_number]):
            return f"Raw: {self.raw_value} (Unknown Gate Format)"
        parts = []
        if self.terminal_name:
            parts.append(self.terminal_name)
        if self.terminal_number:
            parts.append(self.terminal_number)
        if self.gate_number:
            parts.append(f"Gate {self.gate_number}")
        if self.gate_letter:
            parts[-1] += self.gate_letter
        return " ".join(parts)
```

### Field Semantics

| Field | Meaning | Examples | Nullable |
|-------|---------|----------|----------|
| `terminal_name` | Terminal type/name | "Terminal", "International", "Parking", "Domestic", "Main", "Pier", "Concourse", "Level" | Yes |
| `terminal_number` | Terminal identifier | "1", "2", "A", "B", "7" | Yes |
| `gate_number` | Gate numeric part | "5", "15", "102" | Yes |
| `gate_letter` | Gate letter suffix | "A", "B", "C" (follows gate_number) | Yes |
| `raw_value` | Original input | "Terminal 1 Gate 5A", "International B Gate 42" | No (always preserved) |

### Parsing Examples

| Input String | Parsed Fields |
|--------------|---------------|
| "Terminal 1 Gate 5A" | terminal_name="Terminal", terminal_number="1", gate_number="5", gate_letter="A" |
| "International B Gate 42" | terminal_name="International", terminal_number="B", gate_number="42" |
| "Parking 123" | terminal_name="Parking", gate_number="123" |
| "Gate 7B" | gate_number="7", gate_letter="B" |
| "Pier C Gate 14 R" | terminal_name="Pier", terminal_number="C", gate_number="14", gate_letter="R" |
| "Domestic Gate 25A" | terminal_name="Domestic", gate_number="25", gate_letter="A" |

---

## MenuState Structure

**File:** `GateAssignmentDirector/menu_reader.py`

### Definition

```python
@dataclass
class MenuState:
    """GSX menu state snapshot"""
    title: str                      # Menu title (e.g., "Select Gate Position")
    options: List[str]              # Menu options as strings
    options_enum: List[Tuple[int, str]]  # Enumerated options (index, text)
    raw_lines: List[str]            # Raw menu file lines
```

### Field Semantics

| Field | Meaning | Example |
|-------|---------|---------|
| `title` | Menu header text | "Select Gate Position" |
| `options` | List of clickable options | ["Gate 1-5A", "Gate 1-7", "Next"] |
| `options_enum` | Options with indices | [(0, "Gate 1-5A"), (1, "Gate 1-7"), (2, "Next")] |
| `raw_lines` | Unprocessed file content | ["Select Gate Position", "", "Gate 1-5A", ...] |

### Menu Actions (Special Options)

These keywords are menu controls, not data:
- "Back"
- "Cancel"
- "Next"
- "Previous"
- "Confirm"
- "OK"

**Important:** Menu change detection skips these when comparing states.

---

## Airport Data Formats

Gate data is stored in two formats in `gsx_menu_logs/` directory.

### Raw Format: `{ICAO}.json`

**Purpose:** Exact capture of GSX menu structure

**Structure:**
```json
{
  "airport": "KLAX",
  "last_updated": "2025-09-27T23:50:22.669505",
  "menus": [
    {
      "menu_depth": 0,
      "title": "Select Gate Position",
      "options": [
        "Gate 1-5A - Medium - 2x /J",
        "Gate 1-7 - Heavy - 1x /J",
        "Next"
      ],
      "navigation_info": {
        "level_0_index": 0,
        "next_clicks": 0,
        "menu_index": 0
      }
    },
    {
      "menu_depth": 0,
      "title": "Select Gate Position",
      "options": [
        "Gate 2-10B - Small - None",
        "Previous",
        "Next"
      ],
      "navigation_info": {
        "level_0_index": 0,
        "next_clicks": 1,
        "menu_index": 0
      }
    }
  ]
}
```

**Field Meanings:**
- `airport`: ICAO code (e.g., "KLAX")
- `last_updated`: ISO 8601 timestamp of mapping
- `menus`: Array of menu pages visited
  - `menu_depth`: Nesting level (0 = top, 1 = submenu)
  - `title`: GSX menu title
  - `options`: Raw menu text as displayed in GSX
  - `navigation_info`: How to reach this menu
    - `level_0_index`: Top-level menu selection
    - `next_clicks`: Number of "Next" button clicks
    - `menu_index`: Option index within current page

### Interpreted Format: `{ICAO}_interpreted.json`

**Purpose:** Structured, searchable gate database

**Structure:**
```json
{
  "airport": "KLAX",
  "last_updated": "2025-09-27T23:50:22.669505",
  "terminals": {
    "1": {
      "5A": {
        "terminal": "1",
        "gate": "5A",
        "position_id": "Terminal 1 Gate 5A",
        "type": "gate",
        "size": "Medium",
        "jetways": "2x /J",
        "raw_info": {
          "full_text": "Gate 1-5A - Medium - 2x /J",
          "menu_index": 0,
          "found_in_menu": "Select Gate Position",
          "depth": 0,
          "level_0_index": 0,
          "next_clicks": 0
        }
      },
      "7": {
        "terminal": "1",
        "gate": "7",
        "position_id": "Terminal 1 Gate 7",
        "type": "gate",
        "size": "Heavy",
        "jetways": "1x /J",
        "raw_info": {
          "full_text": "Gate 1-7 - Heavy - 1x /J",
          "menu_index": 1,
          "found_in_menu": "Select Gate Position",
          "depth": 0,
          "level_0_index": 0,
          "next_clicks": 0
        }
      }
    },
    "2": {
      "10B": {
        "terminal": "2",
        "gate": "10B",
        "position_id": "Terminal 2 Gate 10B",
        "type": "gate",
        "size": "Small",
        "jetways": "None",
        "raw_info": {
          "full_text": "Gate 2-10B - Small - None",
          "menu_index": 0,
          "found_in_menu": "Select Gate Position",
          "depth": 0,
          "level_0_index": 0,
          "next_clicks": 1
        }
      }
    }
  }
}
```

**Field Meanings:**
- `terminals`: Dictionary keyed by terminal identifier (string)
  - Each terminal key: "1", "2", "A", "B", "International", etc.
  - Each terminal value: Dictionary of gates keyed by gate identifier
    - `terminal`: Terminal identifier (matches parent key)
    - `gate`: Gate identifier (e.g., "5A", "7", "10B")
    - `position_id`: Full descriptive string for GSX (used in logs/UI)
    - `type`: "gate" or "parking"
    - `size`: Aircraft size ("Small", "Medium", "Heavy", or "Unknown")
    - `jetways`: Jetway configuration ("1x /J", "2x /J", "None", or "-")
    - `raw_info`: Original menu data
      - `full_text`: Exact menu option text
      - `menu_index`: Position in menu
      - `found_in_menu`: Menu title where found
      - `depth`: Menu nesting level
      - `level_0_index`: Top-level selection
      - `next_clicks`: Pagination count to reach this gate

### Transformation: Raw → Interpreted

**File:** `GateAssignmentDirector/menu_logger.py`

**Algorithm:**
1. Parse each menu option with regex (gate patterns, parking patterns)
2. Extract terminal and gate identifiers
3. Parse aircraft size (Small/Medium/Heavy)
4. Parse jetway count (1x /J, 2x /J, None)
5. Organize into hierarchical structure by terminal
6. Store navigation path in raw_info

**Parsing Functions:**
- `_parse_gate_size(full_text: str) -> str` - Extract size or "Unknown"
- `_parse_jetway_count(full_text: str) -> str` - Extract jetways or "-"

---

## SayIntentions flight.json

**File Location:** `C:\Users\{username}\AppData\Local\SayIntentionsAI\flight.json`

**Monitored By:** `JSONMonitor` in `si_api_hook.py`

### Structure

```json
{
  "flight_details": {
    "current_flight": {
      "assigned_gate": "Terminal 1 Gate 5A",
      "flight_destination": "KLAX",
      "flight_origin": "KORD",
      "flight_number": "UA123",
      "aircraft_type": "B738"
    }
  },
  "other_fields": "..."
}
```

### Monitored Fields

| Field Path | Purpose | Example |
|------------|---------|---------|
| `flight_details.current_flight.assigned_gate` | Gate string to parse | "Terminal 1 Gate 5A" |
| `flight_details.current_flight.flight_destination` | Destination ICAO | "KLAX" |

**Change Detection:**
- Monitors `assigned_gate` field
- Triggers callback when value changes
- Parses gate string with GateParser
- Enqueues GateInfo for assignment

### Validation Rules

**Valid assigned_gate:**
- Non-empty string
- Changes from previous value
- Successfully parses with GateParser (may have empty fields)

**Edge Cases:**
- Empty string: Ignored
- Null/missing field: Ignored
- Unparseable format: Still captured with raw_value only

---

## Gate Parsing Regex

**File:** `GateAssignmentDirector/si_api_hook.py`
**Constant:** `GATE_PATTERN` (module-level compiled regex)

### Pattern Definition

```python
GATE_PATTERN = re.compile(
    r"""
        (?:terminal\s+)?                     # Optional "terminal" prefix
        (?:(terminal|international|parking|domestic|main|central|pier|concourse|level)\s+)?  # Terminal type
        (?:terminal\s+)?                     # Optional repeated "terminal"
        (?:([A-Z]|\d+)\s+)?                  # Terminal number/letter
        (?:(gate)\s+)?                       # Optional "gate" keyword
        (?:([A-Z])\s*)?                      # Optional gate letter prefix
        (?:(\d+)(?:\s*|$))?                  # Gate number
        (?:([A-Z])(?:\s*|$))?                # Optional gate letter suffix
        """,
    re.IGNORECASE | re.VERBOSE,
)
```

### Capture Groups

| Group Index | Meaning | Examples |
|-------------|---------|----------|
| 0 | Full match | (entire string) |
| 1 | Terminal type | "terminal", "international", "parking" |
| 2 | Terminal identifier | "1", "A", "B", "7" |
| 3 | "gate" keyword | "gate" (if present) |
| 4 | Gate letter prefix | "A", "B" (before number) |
| 5 | Gate number | "5", "15", "102" |
| 6 | Gate letter suffix | "A", "B" (after number) |

### Parsing Logic

**File:** `GateParser.parse_gate()` in `si_api_hook.py`

```python
def parse_gate(self, gate_string: str) -> GateInfo:
    if not gate_string or not gate_string.strip():
        return GateInfo()  # Empty info

    gate_string = gate_string.strip()
    gate_info = GateInfo(raw_value=gate_string, ...)

    match = GATE_PATTERN.search(gate_string)
    if not match:
        return gate_info  # Only raw_value set

    # Extract groups
    terminal_name = match.group(1) or ""
    terminal_number = match.group(2) or ""
    gate_letter_prefix = match.group(4) or ""
    gate_number = match.group(5) or ""
    gate_letter_suffix = match.group(6) or ""

    # Prioritize suffix over prefix for gate letter
    gate_letter = gate_letter_suffix or gate_letter_prefix

    # Populate GateInfo
    gate_info.terminal_name = terminal_name.capitalize() if terminal_name else ""
    gate_info.terminal_number = terminal_number.upper() if terminal_number else ""
    gate_info.gate_number = gate_number
    gate_info.gate_letter = gate_letter.upper() if gate_letter else ""

    return gate_info
```

---

## Fuzzy Matching Algorithm

**File:** `GateAssignmentDirector/gate_assignment.py`
**Method:** `find_gate()`

### Purpose

Match SayIntentions gate strings to GSX menu options when exact match fails.

### Algorithm

```python
def find_gate(self, airport_data: Dict[str, Any], terminal: str, gate: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    # Step 1: Try exact match
    for key_terminal, dict_terminal in airport_data["terminals"].items():
        for key_gate, dict_gate in dict_terminal.items():
            if key_terminal == terminal and key_gate == gate:
                return dict_gate, True  # Direct match

    # Step 2: Fuzzy matching
    best_match = None
    best_score = 0  # Changed from 10 to 0 in v0.8.6

    for key_terminal, dict_terminal in airport_data["terminals"].items():
        for key_gate, dict_gate in dict_terminal.items():
            # Concatenate terminal + gate for comparison
            search_string = key_terminal + key_gate
            target_string = terminal + gate

            # Use rapidfuzz for similarity score
            score = fuzz.ratio(search_string, target_string)

            if score >= best_score:  # >= instead of > for edge cases
                best_score = score
                best_match = dict_gate

    if best_match:
        logger.debug(f"Chose best match {best_match['position_id']} with Score {best_score}")
    else:
        logger.warning(f"No gate match found for Terminal {terminal} Gate {gate}")

    return best_match, False  # Fuzzy match (not direct)
```

### Scoring

**Library:** rapidfuzz (`from rapidfuzz import fuzz`)
**Method:** `fuzz.ratio()` (Levenshtein distance ratio)

**Score Range:** 0-100
- 100 = identical strings
- 0 = completely different

**Threshold:** 0 (return best match even if score is 0)
- Changed from 10 in v0.8.6
- Ensures at least one gate is always returned (if any exist)

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| No gates in terminal | Returns None, False |
| Multiple gates with same score | Returns last one found (dict iteration order) |
| Score of 0 | Returns gate (changed in v0.8.6) |
| Empty terminal/gate strings | Concatenates as "" + "", score likely 0 |

---

## Menu Mapping Algorithm

**File:** `GateAssignmentDirector/gate_assignment.py`
**Method:** `map_available_spots()`

### Purpose

Generate comprehensive gate/parking database for an airport by exhaustively navigating GSX menus.

### Algorithm

```python
def map_available_spots(self, airport: str) -> Dict[str, Any]:
    # Step 1: Open GSX menu
    self.menu_navigator.open_menu()

    # Step 2: Navigate to gate selection
    self.menu_navigator.find_and_click(["Customize", "position"], SearchType.KEYWORD)

    # Step 3: Iterate through all top-level options
    current_menu = self.menu_reader.read_menu()
    for index, option in enumerate(current_menu.options_enum):
        # Skip menu actions (Back, Cancel, etc.)
        if option in GsxMenuKeywords:
            continue

        # Log this menu state
        navigation_info = {
            "level_0_index": index,
            "next_clicks": 0,
            "menu_index": index
        }
        self.menu_logger.log_menu_state(current_menu, navigation_info)

        # Click this option to enter submenu
        self.menu_navigator.click_by_index(index)

        # Step 4: Paginate through "Next" buttons
        next_clicks = 0
        while self.menu_navigator.click_next():  # Returns False when "Next" not found
            next_clicks += 1
            submenu = self.menu_reader.read_menu()
            navigation_info = {
                "level_0_index": index,
                "next_clicks": next_clicks,
                "menu_index": 0  # Assuming first option in paginated view
            }
            self.menu_logger.log_menu_state(submenu, navigation_info)

        # Return to top level
        self.menu_navigator.click_menu_action(["Back"])

    # Step 5: Save raw session data
    raw_data = self.menu_logger.get_session_data()
    raw_file = f"gsx_menu_logs/{airport}.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2)

    # Step 6: Generate interpreted format
    interpreted_data = self.menu_logger.process_airport_data(raw_data)
    interpreted_file = f"gsx_menu_logs/{airport}_interpreted.json"
    with open(interpreted_file, 'w', encoding='utf-8') as f:
        json.dump(interpreted_data, f, indent=2)

    return interpreted_data
```

### Output Files

1. `gsx_menu_logs/{ICAO}.json` - Raw capture
2. `gsx_menu_logs/{ICAO}_interpreted.json` - Structured database

---

## Gate Management Operations

**File:** `GateAssignmentDirector/ui/gate_management.py`

### Operations

#### 1. Rename Gate
**Purpose:** Edit `full_text` field for manual corrections

**Method:** `rename_gate(airport: str, terminal: str, gate: str, new_full_text: str)`

**Use Case:** Fix malformed gate data in GSX menus

**Example:**
```python
# Before: "Gate 1-5A - Medum - 2x /J" (typo)
# After:  "Gate 1-5A - Medium - 2x /J"
rename_gate("KLAX", "1", "5A", "Gate 1-5A - Medium - 2x /J")
```

#### 2. Move Gate
**Purpose:** Reassign gate to different terminal

**Method:** `move_gate(airport: str, from_terminal: str, gate: str, to_terminal: str)`

**Use Case:** Correct terminal assignment errors

**Example:**
```python
# Move gate 10 from terminal 1 to terminal 2
move_gate("KLAX", "1", "10", "2")
```

### Parsing Functions

#### _parse_gate_size()
```python
def _parse_gate_size(full_text: str) -> str:
    """Extract aircraft size from gate text"""
    full_text_lower = full_text.lower()
    if "small" in full_text_lower:
        return "Small"
    elif "medium" in full_text_lower:
        return "Medium"
    elif "heavy" in full_text_lower:
        return "Heavy"
    else:
        return "Unknown"
```

#### _parse_jetway_count()
```python
def _parse_jetway_count(full_text: str) -> str:
    """Extract jetway configuration from gate text"""
    if "1x /J" in full_text or "1x/J" in full_text:
        return "1x /J"
    elif "2x /J" in full_text or "2x/J" in full_text:
        return "2x /J"
    elif "None" in full_text:
        return "None"
    else:
        return "-"  # Unknown
```

---

## Data Transformation Pipeline

### Complete Flow

```
SayIntentions flight.json
    ↓ [File Watch + Read]
JSONMonitor
    ↓ [Change Detection]
GateParser
    ↓ [Regex Parsing]
GateInfo (terminal_name, terminal_number, gate_number, gate_letter)
    ↓ [Queue]
Director
    ↓ [Dequeue + Enqueue to GSX Hook]
GateAssignment.assign_gate()
    ↓ [Load airport data]
map_available_spots() OR load from gsx_menu_logs/{ICAO}_interpreted.json
    ↓ [Find gate]
find_gate() → Exact match or Fuzzy match
    ↓ [Navigate menus]
MenuNavigator.click_planned() or find_and_click()
    ↓ [SimConnect L:Var writes]
GSX Menu → Gate assigned
```

### Before/After Examples

#### Example 1: Simple Gate
**Input:** "Gate 5A" (from SayIntentions)
**GateInfo:** terminal_name="", terminal_number="", gate_number="5", gate_letter="A"
**Match Target:** Terminal 1, Gate "5A"
**GSX Action:** Navigate to Terminal 1 → Select "Gate 1-5A"

#### Example 2: Complex Terminal
**Input:** "International B Gate 42" (from SayIntentions)
**GateInfo:** terminal_name="International", terminal_number="B", gate_number="42", gate_letter=""
**Match Target:** Terminal "B" (International), Gate "42"
**GSX Action:** Navigate to International B → Select "Gate 42"

#### Example 3: Fuzzy Match
**Input:** "Terminal 1 Gate 5" (from SayIntentions)
**GateInfo:** terminal_name="Terminal", terminal_number="1", gate_number="5", gate_letter=""
**Exact Match:** Not found (GSX has "5A" but not "5")
**Fuzzy Match:** "1" + "5" vs "1" + "5A" → 66% similarity → Returns gate "5A"
**GSX Action:** Navigate to Terminal 1 → Select "Gate 1-5A"

---

## Edge Cases & Validation

### Gate Parsing Edge Cases

| Input | Parsed Result | Notes |
|-------|---------------|-------|
| "" (empty) | GateInfo() with all None | Valid, ignored by monitor |
| "   " (whitespace) | GateInfo() with all None | Stripped, treated as empty |
| "Unknown Format" | raw_value="Unknown Format", all else None | Regex fails, raw preserved |
| "gate" (just keyword) | terminal_name="", gate_number="" | Partial parse |
| "Terminal Terminal 1 Gate 5" | terminal_name="Terminal", terminal_number="1", gate_number="5" | Handles repeated keywords |

### Airport Data Edge Cases

| Scenario | Behavior |
|----------|----------|
| File not found | Creates new mapping via `map_available_spots()` |
| Malformed JSON | Raises JSONDecodeError, logged |
| Missing `terminals` key | Treated as empty airport |
| Empty terminal | Still present in structure, no gates |

### Fuzzy Matching Edge Cases

| Scenario | Result |
|----------|--------|
| No gates in airport | Returns None, False |
| Identical terminal+gate | Score 100, exact match path taken |
| Completely different strings | Score 0, still returns best gate (v0.8.6) |
| Multiple 100% scores | Returns first found (dict order) |

### Null Handling

**v0.8.6 Fix:** Gate assignment now handles None values:
```python
# Before: terminal + terminal_number  # Crashes if None
# After:  (terminal or "") + (terminal_number or "")  # Safe
```

---

**See also:**
- [architecture.md](./architecture.md) - System architecture
- [testing.md](./testing.md) - Data structure testing patterns
- [README.md](./README.md) - General overview

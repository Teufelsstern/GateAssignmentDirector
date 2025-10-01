# UI System Documentation

**For:** color-harmony-expert

This document covers the UI architecture, centralized color palette system, component hierarchy, helper functions, widget state management, and styling standards.

## Table of Contents

- [UI Architecture](#ui-architecture)
- [Color Palette System](#color-palette-system)
- [Component Hierarchy](#component-hierarchy)
- [Helper Functions](#helper-functions)
- [Widget State Management](#widget-state-management)
- [Threading for UI Updates](#threading-for-ui-updates)
- [Styling Standards](#styling-standards)
- [System Tray Integration](#system-tray-integration)

---

## UI Architecture

### Framework

**Library:** CustomTkinter (modern tkinter wrapper)
**Theme:** Dark mode
**Font:** Arial (system default)

### Main Window Structure

**File:** `GateAssignmentDirector/ui/main_window.py`

```
DirectorUI (Main Window)
│
├── Tab View (CTkTabview)
│   ├── Monitor Tab (monitor_tab.py)
│   ├── Config Tab (config_tab.py)
│   └── Logs Tab (logs_tab.py)
│
├── System Tray (pystray)
│   ├── Show/Hide Window
│   ├── Exit
│   └── Status indicator
│
└── Gate Management Window (separate toplevel)
    └── GateManagementWindow (gate_management.py)
```

### Tab Organization

| Tab | File | Purpose |
|-----|------|---------|
| Monitor | `ui/monitor_tab.py` | Start/stop monitoring, gate assignment controls, activity log |
| Config | `ui/config_tab.py` | Edit configuration (paths, timing, API keys) |
| Logs | `ui/logs_tab.py` | View application logs |
| Gate Management | `ui/gate_management.py` | Manual gate control (separate window) |

---

## Color Palette System

**File:** `GateAssignmentDirector/ui/ui_helpers.py`
**Version:** v0.8.5 (centralized dataclass-based system)

### Design Philosophy

**Progressive Liberal Aesthetic:**
- Soft, harmonized colors
- 50-55% saturation
- Warm undertones
- Dark mode optimized
- Accessible contrast ratios

### Color Dataclass

```python
@dataclass
class Color:
    """Color definition with hex code and usage tracking"""
    hex: str                      # Main color hex code
    hover: Optional[str] = None   # Hover state color
    usage: list[str] = None       # Usage notes for documentation

def c(color_name: str, hover: bool = False) -> str:
    """Convenience function: c('sage') or c('sage', hover=True)"""
    color = COLORS[color_name]
    return color.hover if hover and color.hover else color.hex
```

### Complete Color Palette

#### Primary Actions (Sage - Green Tones)

| Name | Hex | Hover | Usage |
|------|-----|-------|-------|
| `sage` | #9dc4a8 | #8aad95 | Start monitoring button background, primary action |
| `sage_lighter` | #c4dccb | #adc2b5 | Sage light variant |
| `sage_darker` | #6f9d7e | #5e8b6a | Sage dark variant |
| `sage_dark` | #2d4035 | #253528 | Start monitoring button text (active) |
| `sage_light` | #c5d9cc | #adc2b5 | Start monitoring button text (inactive) |

**Semantic Meaning:** Start, begin, go, success

#### Secondary Actions (Periwinkle - Blue Tones)

| Name | Hex | Hover | Usage |
|------|-----|-------|-------|
| `periwinkle` | #a8b8d4 | #95a2bb | Assign gate button background, tab selected background |
| `periwinkle_lighter` | #d1daf0 | #b4bdcf | Periwinkle light variant |
| `periwinkle_darker` | #7689ab | #5e8b6a | Periwinkle dark variant |
| `periwinkle_dark` | #30384a | #283040 | Assign gate button text (active), tab selected text |
| `periwinkle_light` | #cbd4e6 | #b4bdcf | Assign gate button text (inactive), tab unselected text |
| `periwinkle_tint` | #9BA8D9 | #8993bf | Tab selected hover, border focus |

**Semantic Meaning:** Action, process, navigate, selected

#### Tertiary Actions (Lilac - Purple Tones)

| Name | Hex | Hover | Usage |
|------|-----|-------|-------|
| `lilac` | #c5b8d4 | #d5c8e4 | Apply override button background |
| `lilac_lighter` | #e4daf0 | #c9c2cf | Lilac light variant |
| `lilac_darker` | #9d87ab | #8993bf | Lilac dark variant |
| `lilac_light` | #dfd9e6 | #c9c2cf | Lilac text inactive |
| `purple_gray` | #4a4050 | #403846 | Lilac/salmon button text, override buttons text |

**Semantic Meaning:** Override, special, tertiary action

#### Destructive Actions (Salmon - Red/Pink Tones)

| Name | Hex | Hover | Usage |
|------|-----|-------|-------|
| `salmon` | #d4a5a0 | #bb918d | Stop monitoring button background, clear override button |
| `salmon_lighter` | #ecc9c5 | #cfc2bf | Salmon light variant |
| `salmon_darker` | #ab7771 | #af6c6c | Salmon dark variant |
| `salmon_light` | #e8d9d6 | #cfc2bf | Stop monitoring button text (inactive) |

**Semantic Meaning:** Stop, cancel, clear, destructive

#### Status Colors

| Name | Hex | Hover | Usage |
|------|-----|-------|-------|
| `muted_sage` | #6B9E78 | #5e8b6a | Status success, monitoring active |
| `dusty_rose` | #C67B7B | #af6c6c | Status error, monitoring stopped, border error |
| `mustard` | #D4A574 | #bb9166 | Status warning, manual airport override indicator |

**Semantic Meaning:** State indicators

#### Backgrounds & Neutrals

| Name | Hex | Hover | Usage |
|------|-----|-------|-------|
| `charcoal` | #1a1a1a | #171717 | Dark background, textbox background |
| `charcoal_light` | #2a2a2a | #252525 | Panel background, override panel, tab background |
| `charcoal_lighter` | #3a3a3a | #333333 | Default border, tab unselected hover |
| `charcoal_lightest` | #4a4a4a | #414141 | Tab background (alternate) |
| `gray` | #4a4a4a | #414141 | Neutral background, edit gates button |
| `gray_light` | #5a5a5a | #4f4f4f | Neutral background hover |

**Semantic Meaning:** Backgrounds, borders, disabled states

### Accessibility Notes

**Contrast Ratios (WCAG AA):**
- Sage (#9dc4a8) on charcoal (#1a1a1a): ~5.2:1 ✓
- Periwinkle (#a8b8d4) on charcoal (#1a1a1a): ~5.8:1 ✓
- Salmon (#d4a5a0) on charcoal (#1a1a1a): ~5.0:1 ✓
- All text colors on dark backgrounds: >4.5:1 ✓

**State Variations:**
- Default: Main hex color
- Hover: Darker variant (10-15% luminosity reduction)
- Active: Dark variant with contrasting text
- Disabled: Light variant with reduced opacity

### Don't Use

**Deprecated Colors:**
- Direct hex codes in component files (use `c()` function)
- Hardcoded #hex values
- Inconsistent hover states

**Anti-Patterns:**
- Using sage for destructive actions
- Using salmon for success states
- Mixing semantic meanings

---

## Component Hierarchy

### DirectorUI (Main Window)

**File:** `GateAssignmentDirector/ui/main_window.py`

```python
class DirectorUI:
    def __init__(self):
        self.root = ctk.CTk()  # Main window
        self.root.title("Gate Assignment Director")
        self.root.geometry("600x680")

        # Components
        self.director = GateAssignmentDirector()
        self.tabview = ctk.CTkTabview(self.root)

        # Tabs
        self.monitor_tab = MonitorTab(self.tabview.tab("Monitor"), self)
        self.config_tab = ConfigTab(self.tabview.tab("Config"), self)
        self.logs_tab = LogsTab(self.tabview.tab("Logs"), self)

        # System tray
        self.tray_icon = None  # pystray.Icon
```

**Window Constraints:**
- Minimum: 350x430
- Maximum: 800x800
- Default: 600x680

### Monitor Tab

**File:** `GateAssignmentDirector/ui/monitor_tab.py`

**Layout:**
```
Monitor Tab Frame
│
├── Control Buttons Row
│   ├── Start Monitoring (sage)
│   ├── Stop Monitoring (salmon)
│   └── Assign Gate (periwinkle)
│
├── Override Panel (charcoal_light)
│   ├── Override Airport Input
│   ├── Override Gate Input
│   ├── Apply Override (lilac)
│   └── Clear Override (salmon)
│
├── Status Section
│   ├── Monitoring Status Label (muted_sage/dusty_rose)
│   └── Current Airport Label (mustard for override)
│
└── Recent Activity Log (charcoal textbox, read-only)
```

**Key Widgets:**
- `start_btn`: Start monitoring (sage/sage_dark)
- `stop_btn`: Stop monitoring (salmon/purple_gray)
- `assign_gate_btn`: Manual assignment (periwinkle/periwinkle_dark)
- `apply_override_btn`: Apply override (lilac/purple_gray)
- `clear_override_btn`: Clear override (salmon/purple_gray)
- `monitoring_status_label`: Status indicator
- `activity_text`: Read-only activity log

### Config Tab

**File:** `GateAssignmentDirector/ui/config_tab.py`

**Layout:**
```
Config Tab Frame (Scrollable)
│
├── GSX Settings Section
│   ├── Menu Paths (wide input)
│   ├── Default Airline (medium input)
│   └── Timing Values (narrow inputs)
│
├── SayIntentions Settings Section
│   └── API Key (wide input)
│
└── Logging Settings Section
    ├── Log Level (medium input)
    ├── Log Format (wide input)
    └── Date Format (medium input)
```

**Input Field Widths:**
- API keys, paths, formats: 400px
- Timing values (numeric): 100px
- Text values (airline, level): 200px

**Styling:**
- Corner radius: 6px
- Border color: `c('charcoal_lighter')`
- Entry height: 5px (compact)

### Logs Tab

**File:** `GateAssignmentDirector/ui/logs_tab.py`

**Layout:**
```
Logs Tab Frame
│
└── Log Textbox (charcoal, read-only, scrollable)
```

### Gate Management Window

**File:** `GateAssignmentDirector/ui/gate_management.py`

**Layout:**
```
Gate Management Window (separate toplevel)
│
├── Tree View (hierarchical gate display)
│   ├── Columns: Gate | Terminal | Size | Jetways | Full Text
│   └── Scrollable
│
├── Control Section
│   ├── Reload Data Button (gray)
│   ├── Save Changes Button (gray)
│   └── Edit Gates Button (gray)
│
├── Move Gate Section (horizontal compact layout)
│   ├── Gate Input | From Input | To Input
│   └── Move Gate Button
│
└── Rename Gate Section
    ├── Gate Input | Terminal Input
    ├── New Full Text Input (wide)
    └── Rename Button
```

**Window Size:**
- Minimum: 1000x700
- Title font: 16-20px
- Status font: 14px
- Button height: 28px (compact)

---

## Helper Functions

**File:** `GateAssignmentDirector/ui/ui_helpers.py`

### c() - Color Access

```python
def c(color_name: str, hover: bool = False) -> str:
    """Get color hex code. Usage: c('sage') or c('sage', hover=True)"""
```

**Usage:**
```python
fg_color=c('sage')
hover_color=c('sage', hover=True)
text_color=c('sage_dark')
```

### _label() - Create Label

```python
def _label(
    frame: ctk,
    text: str = "Default Label",
    size: int = 14,
    padx: tuple[int, int] = (10, 0),
    pady: tuple[int, int] = (15, 5),
    color: str = "#ffffff",
    width: Optional[int] = None,
    side: Optional[str] = None,
    bold: bool = True
) -> None:
    """Create a text label for the current frame"""
```

**Usage:**
```python
_label(frame, text="Status:", size=16, color=c('muted_sage'), bold=True)
```

**Important:** Returns None, uses `side` parameter for pack positioning (don't chain `.pack()`)

### _button() - Create Button

```python
def _button(
    frame: ctk,
    command: Callable[[], None],
    text: str = "Default Text",
    height: int = 35,
    width: Optional[int] = None,
    fg_color: str = "#4a4a4a",
    hover_color: str = "#5a5a5a",
    text_color: Optional[str] = None,
    corner_radius: int = 6,
    side: Optional[str] = None,
    expand: bool = True,
    fill: str = "x",
    padx: tuple[int, int] = (0, 0),
    pady: tuple[int, int] = (0, 0),
    state: str = "normal",
    size: int = 16
) -> ctk.CTkButton:
    """Create a button and return it"""
```

**Usage:**
```python
start_btn = _button(
    frame,
    parent_ui.start_monitoring,
    text="Start Monitoring",
    fg_color=c('sage'),
    hover_color=c('sage', hover=True),
    text_color=c('sage_dark'),
    corner_radius=6
)
```

**Returns:** CTkButton instance for later reference

---

## Widget State Management

### Dynamic Button State Changes

**Pattern: Change button colors based on state**

```python
# When monitoring starts
self.start_btn.configure(
    text_color=c('sage_light'),  # Inactive appearance
    state="disabled"
)
self.stop_btn.configure(
    text_color=c('purple_gray'),  # Active appearance
    state="normal"
)

# When monitoring stops (reverse)
self.start_btn.configure(
    text_color=c('sage_dark'),  # Active appearance
    state="normal"
)
self.stop_btn.configure(
    text_color=c('salmon_light'),  # Inactive appearance
    state="disabled"
)
```

### Dynamic Status Updates

```python
# Success status
self.monitoring_status_label.configure(
    text="● Monitoring Active",
    text_color=c('muted_sage')
)

# Error status
self.monitoring_status_label.configure(
    text="● Stopped",
    text_color=c('dusty_rose')
)

# Warning status (manual override)
self.current_airport_label.configure(
    text=f"Current: {airport}",
    text_color=c('mustard')
)
```

### Read-Only Textboxes

**Pattern: Enable for write, disable for read**

```python
def _append(self, msg: str):
    """Append message to read-only textbox"""
    self.text_widget.configure(state="normal")  # Enable
    self.text_widget.insert("end", msg)
    self.text_widget.see("end")  # Scroll to bottom
    self.text_widget.configure(state="disabled")  # Disable
```

**Purpose:** Prevent user editing while allowing programmatic updates

---

## Threading for UI Updates

### Thread Safety

**Problem:** CustomTkinter is not thread-safe. UI updates from worker threads crash.

**Solution:** Use `after()` to schedule updates on main thread

### Pattern: Queue-Based Updates

```python
import queue

class DirectorUI:
    def __init__(self):
        self.update_queue = queue.Queue()
        self._schedule_ui_updates()

    def _schedule_ui_updates(self):
        """Process queued UI updates on main thread"""
        try:
            while True:
                update_func = self.update_queue.get_nowait()
                update_func()  # Execute on main thread
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self._schedule_ui_updates)

    def update_from_worker_thread(self, message: str):
        """Safe update from worker thread"""
        self.update_queue.put(lambda: self._append_activity(message))
```

### Example: Director Callbacks

```python
# In Director thread
def gate_assigned_callback(airport, gate):
    # DON'T: ui.update_label(text)  # Crashes!
    # DO: Queue the update
    ui.update_queue.put(lambda: ui.update_label(text))
```

---

## Styling Standards

### Corner Radius

**Standard:** 6px (established v0.8.5)
**Applies to:** Buttons, entries, frames, panels

**Rationale:** Modern aesthetic, not "round buttons from 2022"

### Font Standards

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Button text | Arial | 16px | Bold |
| Label text | Arial | 14px | Bold (default) / Normal |
| Section headers | Arial | 16-20px | Bold |
| Status text | Arial | 14px | Normal |
| Tree view | Arial | 12px | Normal |

### Spacing Standards

**Between Label and Input:**
- Gap: 2px vertical

**Between Input Pairs:**
- Gap: 15px vertical

**Panel Padding:**
- Internal: 10px
- External: 15px

**Button Heights:**
- Standard: 35px
- Compact (gate management): 28px

### Tab Styling

**Colors:**
```python
self.tabview = ctk.CTkTabview(
    self.root,
    corner_radius=6,
    segmented_button_fg_color=c('periwinkle', hover=True),  # Background
    segmented_button_selected_color=c('sage'),  # Selected tab
    segmented_button_selected_hover_color=c('sage'),  # Selected hover
    segmented_button_unselected_color=c('periwinkle', hover=True),  # Unselected
    segmented_button_unselected_hover_color=c('periwinkle'),  # Unselected hover
    text_color=c('purple_gray')  # Text (uniform across all tabs)
)
```

**Limitation:** CustomTkinter doesn't support per-tab text colors. Text color is uniform.

---

## System Tray Integration

**Library:** pystray
**File:** `GateAssignmentDirector/ui/main_window.py`

### Features

- Minimize to system tray
- Show/hide window
- Status indicator
- Exit application

### Icon States

- **Active:** Monitoring in progress
- **Inactive:** Monitoring stopped
- **Error:** System error

### Menu Items

```python
menu = (
    pystray.MenuItem("Show", self.show_window),
    pystray.MenuItem("Hide", self.hide_window),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem("Exit", self.exit_application)
)
```

---

## Design Constraints

### Theme

**Mode:** Dark only (no light mode)
**Background:** Charcoal tones (#1a1a1a to #4a4a4a)
**Text:** High contrast white/light colors

### Accessibility

**Minimum Contrast:** WCAG AA (4.5:1 for text, 3:1 for UI components)
**Focus Indicators:** Border color changes to periwinkle_tint (#9BA8D9)
**State Changes:** Visual + text (not color-only)

### Brand Guidelines

**Tone:** Progressive, liberal, antiracist, antifascist, anti-antiqueer
**Values:** Displayed at bottom of main window
**Color Saturation:** 50-55% (warm, soft, harmonized)
**Avoid:** Aggressive colors, harsh contrasts, cold tones

---

## Version History

### v0.8.5
- Centralized color palette system
- Dataclass-based color definitions
- `c()` helper function
- Corner radius standardized to 6px
- Tab styling harmonized

### v0.8.4
- UI element resizing for uniform appearance
- Variable input widths
- Label styling with optional bold
- Window size constraints adjusted

### v0.8.3
- Values statement added to main window

### v0.8.2
- Label width made optional
- Gate management UI font sizes increased
- Button heights reduced for compact look

---

**See also:**
- [architecture.md](./architecture.md) - UI component lifecycle
- [testing.md](./testing.md) - UI testing patterns
- [README.md](./README.md) - General overview

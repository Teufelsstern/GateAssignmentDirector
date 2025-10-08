# Gate Management Window

The Gate Management Window allows you to view and edit airport gate configurations extracted from GSX. Use this tool to rename gates, reorganize terminals, and perform bulk operations on gate data.

## Opening the Gate Management Window

1. Launch GateAssignmentDirector
2. Go to the **Monitor** tab
3. Click **"Gate Management"** button
4. The window opens showing gates for your current airport

## Window Layout

The window is divided into two sections:

### Left Side - Gate Information
- **Tree View**: Hierarchical display of all terminals and gates
- **Status Log**: Feedback messages for all operations
- **Data Controls**: Reset, Reload, and Save buttons

### Right Side - Actions
- **Move Gate(s)**: Transfer gates between terminals
- **Rename**: Change gate or terminal names (toggle mode)
- **Prefix/Suffix**: Add prefixes or suffixes to multiple gates

---

## Basic Operations

### Selecting Gates

**Single Gate:**
- Click a gate in the tree → All fields auto-fill

**Multiple Gates:**
- Hold `Ctrl` and click gates → Shows count
- Click a Terminal → Selects all gates in that terminal

**Tip:** Selecting a terminal automatically selects all its child gates!

---

## Move Gates Between Terminals

**Purpose:** Transfer gates from one terminal to another.

**Steps:**
1. Select gate(s) in the tree
2. The "Selected" and "From" fields auto-fill
3. Enter destination terminal in "To" field
4. Click **"Move Selected Gate(s)"**
5. If conflicts exist, confirm overwrite
6. Click **"Save Changes"**

**Example:**
```
Move gates 1-10 from Terminal 1 to Terminal A:
1. Click "Terminal: 1" in tree
2. Enter "A" in To field
3. Click Move → Save
✓ Done in 4 clicks
```

---

## Rename Gates or Terminals

**Toggle Mode:** Use radio buttons to switch between Gate and Terminal mode.

### Rename a Gate

1. Select **Gate** mode (radio button)
2. Click a gate in the tree
3. Fields auto-fill with current values
4. Enter new name in "New gate key" field
5. Click **"Rename Gate"**
6. Click **"Save Changes"**

**Example:** Rename Gate 71 to B28A in Terminal 3

### Rename a Terminal

1. Select **Terminal** mode (radio button)
2. Enter current terminal name (e.g., "1")
3. Enter new terminal name (e.g., "Terminal A")
4. Click **"Rename Terminal"**
5. Click **"Save Changes"**

**Note:** Renaming a terminal updates all gates within it automatically!

**Merge Terminals:** If the new terminal name already exists, gates will merge into that terminal (with confirmation).

---

## Bulk Add Prefix/Suffix to Gates

**Purpose:** Add letters/numbers before or after multiple gate numbers.

**Steps:**
1. Select gates in tree (single, multi, or terminal)
2. Enter **Prefix** and/or **Suffix**
   - Prefix: Added before gate number
   - Suffix: Added after gate number
3. Click **"Apply to Selected Gate(s)"**
4. If gates already have prefix/suffix:
   - **Apply to all**: Overwrite existing
   - **Skip existing**: Only modify gates without prefix/suffix
5. Click **"Save Changes"**

**Examples:**

| Operation | Input | Result |
|-----------|-------|--------|
| Add prefix "A" to gates 1-20 | Prefix: "A" | A1, A2, ..., A20 |
| Add suffix "L" to gates 1-10 | Suffix: "L" | 1L, 2L, ..., 10L |
| Add both | Prefix: "B", Suffix: "R" | B5R (from gate 5) |

---

## Data Management

### Save Changes
Click **"Save Changes"** to write modifications to disk.
- Gates are automatically sorted alphanumerically
- Tree view updates to show sorted order

### Reload Data
Click **"Reload Data"** to discard unsaved changes and re-read from file.

### Reset Data
Click **"Reset Data"** to delete interpreted data and re-parse from GSX menus.
- **Warning:** This deletes all manual edits
- Requires confirmation
- Useful for fixing corrupted data

---

## Safety Features

### Conflict Detection
Before overwriting gates, you'll see a dialog listing conflicts:
```
Gate Conflicts Detected

The following gates already exist in Terminal 3:
71, 72, 73

Moving will overwrite the existing gates.

Do you want to continue?
[Yes] [No]
```

### Unsaved Changes Warning
If you close the window with unsaved changes:
```
You have unsaved changes. Do you want to save before closing?
[Yes] [No] [Cancel]
```

- **Yes**: Save and close
- **No**: Close without saving
- **Cancel**: Keep window open

### Status Log
Every operation is logged in the status area:
- `SUCCESS:` Operation completed
- `ERROR:` Something went wrong
- `INFO:` General information

---

## Common Workflows

### Scenario 1: Fix Inconsistent Terminal Names

**Problem:** Some gates show "T1", others show "Terminal 1"

**Solution:**
1. Switch to **Terminal** mode
2. Current: "T1"
3. New: "Terminal 1"
4. Click Rename → Confirm merge
5. Save

**Result:** All "T1" gates now in "Terminal 1"

---

### Scenario 2: Add Pier Designators

**Problem:** Need to add "L" (Left) or "R" (Right) to concourse gates

**Solution:**
1. Multi-select gates 11-20
2. Suffix: "L"
3. Click Apply → Save
4. Repeat for gates 21-30 with suffix "R"

**Result:** 11L, 12L, ..., 20L and 21R, 22R, ..., 30R

---

### Scenario 3: Reorganize Terminal Structure

**Problem:** Want to move all "Remote" stands to a dedicated terminal

**Solution:**
1. Create new terminal "Remote" (move any one gate there first)
2. Select all remote stands from various terminals
3. To: "Remote"
4. Click Move → Save

**Result:** All remote stands consolidated in Terminal "Remote"

---

## Tips & Tricks

**Quick Multi-Select:**
- Click terminal name to select all gates at once
- `Shift+Click` for range selection
- `Ctrl+Click` for individual gates

**Auto-Fill is Your Friend:**
- Clicking a gate fills all action panel fields
- No need to type terminal/gate numbers manually

**Alphanumeric Sorting:**
- Gates sort naturally: 1, 2, 3, 10 (not 1, 10, 2, 3)
- Happens automatically on save
- Works with letters: A1, A2, A10, B1

**Performance:**
- Handles 200+ gates without lag
- Bulk operations complete in <1 second
- Tree view remains responsive

---

## Troubleshooting

**Q: My changes aren't showing in GSX**
A: Make sure you clicked "Save Changes". The application re-reads the JSON file after save.

**Q: I made a mistake, how do I undo?**
A: Click "Reload Data" if you haven't saved yet. If you already saved, use "Reset Data" to re-parse from GSX.

**Q: Gates are in wrong order**
A: Save the file - alphanumeric sorting happens automatically on save.

**Q: Can't find a specific gate**
A: Expand all terminals by clicking the arrows. Gates are organized hierarchically by terminal.

**Q: What does "Merge terminals" mean?**
A: When renaming a terminal to one that already exists, all gates from both terminals combine into one.

---

## File Location

**Data File:** `gsx_menu_logs/{AIRPORT}_interpreted.json`

This file is automatically created when you first use the airport. All edits are saved here.

**Backup Recommendation:** Before major restructuring, copy the `_interpreted.json` file as backup.

---

**Need Help?** Check the [Troubleshooting Guide](troubleshooting.md) or [open an issue](https://github.com/Teufelsstern/GateAssignmentDirector/issues).

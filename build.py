"""
Build script for GateAssignmentDirector
Creates standalone executable using PyInstaller
"""

# Licensed under GPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import PyInstaller.__main__
import shutil
import os
from pathlib import Path

print("=" * 50)
print("GateAssignmentDirector Build Script")
print("=" * 50)

# Clean previous builds
print("\n[1/4] Cleaning previous builds...")
shutil.rmtree('dist', ignore_errors=True)
shutil.rmtree('build', ignore_errors=True)
if os.path.exists('GateAssignmentDirector.spec'):
    os.remove('GateAssignmentDirector.spec')
print("[OK] Cleaned")

# Check for icon file
print("\n[2/4] Checking for icon...")
icon_path = Path("GateAssignmentDirector/icon.ico")
if icon_path.exists():
    print(f"[OK] Found icon at {icon_path}")
    icon_arg = f"--icon={icon_path}"
else:
    print("[WARN] No icon found, building without custom icon")
    icon_arg = ""

# Find SimConnect DLL
print("\n[3/5] Locating SimConnect.dll...")
simconnect_dll = None
try:
    import SimConnect
    import os
    simconnect_path = os.path.dirname(SimConnect.__file__)
    dll_path = os.path.join(simconnect_path, 'SimConnect.dll')
    if os.path.exists(dll_path):
        simconnect_dll = dll_path
        print(f"[OK] Found SimConnect.dll at {dll_path}")
    else:
        print("[WARN] SimConnect.dll not found in SimConnect package")
except ImportError:
    print("[WARN] SimConnect package not installed")

# Build with PyInstaller
print("\n[4/5] Building executable...")
args = [
    'GateAssignmentDirector/ui.py',
    '--onedir',
    '--windowed',  # No console window
    '--name=GateAssignmentDirector',
    '-y',  # Overwrite output directory without confirmation
    '--add-data=LICENSE;.',
    '--add-data=README.md;.',
    '--add-data=GateAssignmentDirector/config.yaml;GateAssignmentDirector',
    '--add-data=GateAssignmentDirector/monitor_config.ini;GateAssignmentDirector',
    '--add-data=GateAssignmentDirector/icon.ico;GateAssignmentDirector',
    '--hidden-import=customtkinter',
    '--hidden-import=CTkToolTip',
    '--hidden-import=PIL',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=pystray',
    '--hidden-import=tkinter',
    '--hidden-import=_tkinter',
    '--hidden-import=yaml',
    '--hidden-import=rapidfuzz',
    '--hidden-import=requests',
    '--collect-all=customtkinter',
    '--collect-all=CTkToolTip',
    '--copy-metadata=CTkToolTip',
    '--clean',
]

# Add SimConnect DLL if found
if simconnect_dll:
    args.append(f'--add-binary={simconnect_dll};SimConnect')

# Add icon if available
if icon_arg:
    args.append(icon_arg)

PyInstaller.__main__.run(args)

# Summary
print("\n[5/5] Build complete!")
print("=" * 50)
print("\nOutput location: dist/GateAssignmentDirector/")
print("Main executable: dist/GateAssignmentDirector/GateAssignmentDirector.exe")
print("\nTo distribute:")
print("  1. Zip the entire 'dist/GateAssignmentDirector' folder")
print("  2. Users extract and run GateAssignmentDirector.exe")
print("\n" + "=" * 50)
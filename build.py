"""
Build script for GateAssignmentDirector
Creates standalone executable using PyInstaller
"""
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
print("✓ Cleaned")

# Check for icon file
print("\n[2/4] Checking for icon...")
icon_path = Path("GateAssignmentDirector/icon.ico")
if icon_path.exists():
    print(f"✓ Found icon at {icon_path}")
    icon_arg = f"--icon={icon_path}"
else:
    print("⚠ No icon found, building without custom icon")
    icon_arg = ""

# Build with PyInstaller
print("\n[3/4] Building executable...")
args = [
    'GateAssignmentDirector/ui.py',
    '--onedir',
    '--windowed',  # No console window
    '--name=GateAssignmentDirector',
    '--add-data=LICENSE;.',
    '--add-data=README.md;.',
    '--add-data=GateAssignmentDirector/config.yaml;GateAssignmentDirector',
    '--add-data=GateAssignmentDirector/icon.ico;GateAssignmentDirector',
    '--hidden-import=customtkinter',
    '--hidden-import=PIL',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=pystray',
    '--hidden-import=tkinter',
    '--hidden-import=_tkinter',
    '--collect-all=customtkinter',
    '--clean',
]

# Add icon if available
if icon_arg:
    args.append(icon_arg)

PyInstaller.__main__.run(args)

# Summary
print("\n[4/4] Build complete!")
print("=" * 50)
print("\nOutput location: dist/GateAssignmentDirector/")
print("Main executable: dist/GateAssignmentDirector/GateAssignmentDirector.exe")
print("\nTo distribute:")
print("  1. Zip the entire 'dist/GateAssignmentDirector' folder")
print("  2. Users extract and run GateAssignmentDirector.exe")
print("\n" + "=" * 50)
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

datas = [('LICENSE.txt', '.'), ('README.md', '.'), ('GateAssignmentDirector/config.yaml', 'GateAssignmentDirector'), ('GateAssignmentDirector/monitor_config.ini', 'GateAssignmentDirector'), ('GateAssignmentDirector/icon.ico', 'GateAssignmentDirector')]
binaries = [('C:\\Users\\mariu\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\SimConnect\\SimConnect.dll', 'SimConnect')]
hiddenimports = ['customtkinter', 'CTkToolTip', 'PIL', 'PIL._tkinter_finder', 'pystray', 'tkinter', '_tkinter', 'yaml', 'rapidfuzz', 'requests']
datas += copy_metadata('CTkToolTip')
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('CTkToolTip')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['GateAssignmentDirector\\ui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GateAssignmentDirector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['GateAssignmentDirector\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GateAssignmentDirector',
)

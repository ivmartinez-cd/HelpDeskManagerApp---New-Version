import os
from PyInstaller.utils.hooks import collect_submodules
# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['HelpDeskLauncher.py'],
    pathex=[],
    binaries=[],
    datas=[('pyside_ui/assets/ico.png', 'pyside_ui/assets'), ('version.json', '.')],
    hiddenimports=['pandas', 'numpy', 'openpyxl', 'PIL', 'scipy', 'lxml', 'scapy', 'geopy', 'requests', *collect_submodules('pyside_ui')],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'sympy', 'matplotlib', 'notebook', 'jedi'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HelpDeskLauncher',
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
    icon=os.path.abspath('icon.ico'),
    # version='version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HelpDeskLauncher',
)

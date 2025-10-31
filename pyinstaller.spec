# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Digital Workshop
This file configures how PyInstaller packages the application into a standalone executable.
"""

import sys
from pathlib import Path

block_cipher = None

# Application configuration
APP_NAME = "Digital Workshop"
MAIN_SCRIPT = "src/main.py"
ICON_PATH = "resources/icons/app_icon.ico"

# Data files to include
added_files = [
    ("resources", "resources"),
    ("docs", "docs"),
]

# Hidden imports that PyInstaller might miss
hidden_imports = [
    "PySide6.QtCore",
    "PySide6.QtGui", 
    "PySide6.QtWidgets",
    "vtk",
    "vtk.qt",
    "sqlite3",
    "json",
    "pathlib",
    "datetime",
    "logging",
]

# Analysis configuration
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy.distutils",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unwanted files
a.datas = [x for x in a.datas if not x[0].startswith('matplotlib')]
a.datas = [x for x in a.datas if not x[0].startswith('numpy')]

# PYZ configuration
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH if Path(ICON_PATH).exists() else None,
    version_file=None,
)
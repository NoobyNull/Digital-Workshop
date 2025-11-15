# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Digital Workshop
Builds a standalone EXE for src/main.py (Digital Workshop GUI entry point)
"""

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'vtk',
        'numpy',
        'PIL',
        'cv2',
        'trimesh',
        'scipy',
        'lxml',
        'xxhash',
        'dotenv',
        'qtawesome',
        'qdarkstyle',
        'openai',
        'google.generativeai',
        'anthropic',
        'requests',
        'zhipuai',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Digital Workshop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
)


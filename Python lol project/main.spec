# -*- mode: python ; coding: utf-8 -*-
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath('main.py'))

# Data files to include in the executable
data_files = [
    ('config.json', '.'),
    ('champions.json', '.'),
    ('minion.ico', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        'PIL._tkinter_finder',
        'pystray._win32',
        'requests.packages.urllib3.util.retry',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.ttk'
    ],
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
    a.binaries,
    a.datas,
    [],
    name='LoLMatchAssistant',
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
    icon='minion.ico',
)

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller-Spec für FPX Timetracker (Windows)
#
# Verwendung (im venv, aus dem Projektverzeichnis):
#   pyinstaller windows/fpx_installer.spec
#
# Ergebnis: dist/FPX Timetracker/ (Ordner mit .exe + DLLs)

a = Analysis(
    ['fpx_tray.py'],           # relativ zum Spec-Verzeichnis (windows/)
    pathex=['..'],             # Projektverzeichnis → findet config.py + fpx_timetracker.py
    binaries=[],
    datas=[
        ('../Logo/Windows/tray.ico', 'Logo/Windows'),
        ('../Logo/Windows/app.ico',  'Logo/Windows'),
    ],
    hiddenimports=[
        'fpx_timetracker',     # per --popover-Flag zur Laufzeit importiert
        'config',
        'pystray._win32',
        'tkinter',
        'tkinter.ttk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['AppKit', 'Foundation', 'objc', 'fcntl'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FPX Timetracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='../Logo/Windows/app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='FPX Timetracker',
)

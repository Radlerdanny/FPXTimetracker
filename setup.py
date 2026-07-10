"""
py2app Build-Konfiguration für FPX Timetracker (Mac).

Verwendung (im venv):
    source .venv/bin/activate
    python setup.py py2app

Ergebnis: dist/FPX Timetracker.app
"""
import sys
from pathlib import Path
from setuptools import setup
from py2app.build_app import py2app as _py2app_base


class py2app_fixed(_py2app_base):
    """py2app + Workaround: entfernt fälschlicherweise als .py abgelegte C-Extensions."""

    def run(self):
        super().run()
        py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        lib_dir = Path("dist") / "FPX Timetracker.app" / "Contents" / "Resources" / "lib" / py_ver
        for stub in lib_dir.glob("*.py"):
            # C-Extension Stubs: Mach-O magic \xca\xfe\xba\xbe oder \xcf\xfa\xed\xfe
            data = stub.read_bytes()
            if data[:4] in (b"\xca\xfe\xba\xbe", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"):
                stub.unlink()
                print(f"  ✓ Build-Fix: falsche Binary-Stub entfernt: {stub.name}")

APP_NAME = "FPX Timetracker"
APP      = ["mac/fpx_menubar.py"]
VERSION  = "0.8.2"

OPTIONS = {
    "argv_emulation": False,          # Kein Apple Event Handling nötig
    "semi_standalone": False,         # Python vollständig einbetten
    "site_packages": True,            # alle venv-Packages einbetten
    "packages": [
        "AppKit", "Foundation", "objc",
        "requests", "urllib3", "certifi",
        "tkinter", "_tkinter",
    ],
    "includes": [
        "fpx_timetracker",            # wird als Subprocess (-m) gestartet
        "config",
    ],
    "excludes": [
        "pystray", "PIL",             # Windows-only, nicht einbetten
    ],
    "extra_scripts": [
        "fpx_timetracker.py",         # muss im Bundle als Modul erreichbar sein
        "config.py",
    ],
    "resources": [
        "Logo/Mac/app.icns",
        "Logo/Icon.png",
    ],
    "iconfile": "Logo/Mac/app.icns",
    "plist": {
        "CFBundleName":               APP_NAME,
        "CFBundleDisplayName":        APP_NAME,
        "CFBundleIdentifier":         "de.fourplex.timetracker",
        "CFBundleVersion":            VERSION,
        "CFBundleShortVersionString": VERSION,
        "LSUIElement":                True,   # kein Dock-Icon beim Start
        "LSMinimumSystemVersion":     "12.0",
        "NSHighResolutionCapable":    True,
    },
}

setup(
    name=APP_NAME,
    version=VERSION,
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    cmdclass={"py2app": py2app_fixed},
)

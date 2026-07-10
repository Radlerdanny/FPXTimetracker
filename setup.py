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

import py2app.build_app as _py2app_build_app
from py2app.util import codesign_adhoc as _codesign_adhoc_orig

# py2app signiert die App auf Apple Silicon (arm64) automatisch ad-hoc (notwendig,
# sonst SIGKILL "Code Signature Invalid" beim Start). Manche Python-Distributionen
# (z.B. der von actions/setup-python auf GitHub Actions installierte Build) bündeln
# in Tcl.framework/Tk.framework zusätzlich statische Stub-Libraries (libtclstub.a,
# libtkstub.a) – die werden von codesign fälschlicherweise als "Subkomponente" der
# Tcl/Tk-Binaries gewertet, sind aber keine gültigen Mach-O-Dateien und lassen sich
# nicht signieren, wodurch codesign den kompletten Bundle-Sign-Vorgang abbricht.
# Diese .a-Dateien werden zur Laufzeit nicht gebraucht (nur zum Linken von
# C-Extensions gegen Tcl/Tk) – vor dem Signieren löschen, dann py2apps eigene
# (korrekte) Signierlogik unverändert weiterlaufen lassen.
def _codesign_adhoc_fixed(bundle):
    removed = list(Path(bundle).rglob("*.a"))
    for a_file in removed:
        a_file.unlink()
    if removed:
        print(f"  ✓ Build-Fix: {len(removed)} statische Stub-Library(s) vor dem Signieren entfernt")

    # Nur Tcl/Tk 8.6 wird unterstützt (Tk 9.0 sieht sichtbar anders aus – größere
    # Schrift, andere Buttons). Manche Build-Runner bündeln zusätzlich zur echten
    # 8.6-Version noch eine ungenutzte 9.0 in Tcl.framework/Tk.framework mit (auch
    # wenn "Current" korrekt auf 8.6 zeigt) – diese Ordner konsequent entfernen,
    # damit niemals eine andere Version geladen werden kann, egal was "Current"
    # gerade zeigt oder in Zukunft zeigen könnte.
    import shutil
    for fw in ("Tcl.framework", "Tk.framework"):
        versions_dir = Path(bundle) / "Contents" / "Frameworks" / fw / "Versions"
        if not versions_dir.is_dir():
            continue
        for v_dir in versions_dir.iterdir():
            if v_dir.is_dir() and v_dir.name not in ("Current", "8.6"):
                shutil.rmtree(v_dir)
                print(f"  ✓ Build-Fix: unerwünschte {fw}-Version entfernt: {v_dir.name}")

    _codesign_adhoc_orig(bundle)


_py2app_build_app.codesign_adhoc = _codesign_adhoc_fixed


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

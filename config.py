"""Gemeinsame Konfiguration für FPX Timetracker (Mac + Windows)."""
import json, os, platform, sys, time
from pathlib import Path

APP_VERSION  = "0.8.2"
GITHUB_REPO  = "Radlerdanny/FPXTimetracker"
IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


FONT_MAIN = "Segoe UI"      if IS_WIN else "Helvetica Neue"
FONT_MONO = "Consolas"      if IS_WIN else "Menlo"


def data_dir() -> Path:
    if IS_WIN:
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
        return base / "FPXTimetracker"
    return Path.home() / ".config" / "FPX_Timetracker"


DATA_DIR  = data_dir()
DATA_FILE = DATA_DIR / "timetracker_data.json"
IPC_FILE  = DATA_DIR / "ipc.json"
LOCK_FILE = DATA_DIR / ("fpx_tray.lock" if IS_WIN else "fpx_menubar.lock")

DATA_DIR.mkdir(parents=True, exist_ok=True)


def write_ipc(d: dict):
    try:
        IPC_FILE.write_text(json.dumps({**d, "ts": time.time()}))
    except Exception:
        pass


def read_ipc() -> dict:
    try:
        return json.loads(IPC_FILE.read_text())
    except Exception:
        return {}


def asset_path(name: str) -> Path:
    """Findet Asset-Dateien – funktioniert im Dev-Modus und im PyInstaller-Bundle."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / name
    return Path(__file__).parent / "assets" / name


def _enable_dpi_awareness() -> float:
    """Aktiviert System-DPI-Awareness auf Windows und liefert den Skalierungsfaktor."""
    if not IS_WIN:
        return 1.0
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return max(1.0, dpi / 96.0)
    except Exception:
        return 1.0


def get_work_area() -> tuple:
    """Liefert (left, top, right, bottom, edge) des nutzbaren Bildschirms.
    edge: 'bottom' | 'top' | 'left' | 'right' – wo die Taskleiste sitzt."""
    if not IS_WIN:
        return (0, 0, 1920, 1080, "bottom")
    import ctypes
    from ctypes import wintypes
    rect = wintypes.RECT()
    try:
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
    except Exception:
        return (0, 0, 1920, 1080, "bottom")
    edge = "bottom"
    if rect.top > 0:
        edge = "top"
    elif rect.left > 0:
        edge = "left"
    elif rect.right < sw:
        edge = "right"
    return (rect.left, rect.top, rect.right, rect.bottom, edge)


SCALE = _enable_dpi_awareness()


def s(n) -> int:
    """Skaliert einen Pixel-Wert gemäß Windows-DPI (auf Mac immer 1:1)."""
    return int(round(n * SCALE))

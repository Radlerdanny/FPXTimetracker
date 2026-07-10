"""
FPX TimeTracker – Menüleisten-Icon (Mac)
Direkt pyobjc NSStatusBar, kein rumps.
tkinter Fenster läuft als separater Prozess (fpx_timetracker.py).
Unterstützt Dev-Modus (python mac/fpx_menubar.py) und py2app-Bundle.
"""
import multiprocessing
multiprocessing.freeze_support()

import sys, os, fcntl, subprocess, time, plistlib
from pathlib import Path

# Singleton: nur eine Instanz erlaubt
_LOCK_FILE = os.path.expanduser("~/.config/FPX_Timetracker/fpx_menubar.lock")
os.makedirs(os.path.dirname(_LOCK_FILE), exist_ok=True)
_lock_fh = open(_LOCK_FILE, "w")
try:
    fcntl.flock(_lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    subprocess.run(["osascript", "-e",
        'display notification "FPX TimeTracker läuft bereits." with title "FPX TimeTracker"'])
    sys.exit(0)

HERE = Path(os.path.dirname(os.path.abspath(__file__)))

if getattr(sys, "frozen", False):
    # py2app-Bundle: alle Skripte liegen in Contents/Resources/
    ROOT = Path(os.environ.get("RESOURCEPATH", str(HERE)))
else:
    ROOT = HERE.parent  # Projektverzeichnis (enthält config.py + fpx_timetracker.py)
    sys.path.insert(0, str(ROOT))

PYTHON = sys.executable

from config import APP_VERSION, DATA_DIR, IPC_FILE, write_ipc, read_ipc

# ── Autostart (LaunchAgent) ───────────────────────────────────────────────────
_AGENT_ID    = "de.fourplex.timetracker"
_AGENT_PLIST = Path.home() / "Library" / "LaunchAgents" / f"{_AGENT_ID}.plist"


def _autostart_args():
    if getattr(sys, "frozen", False):
        # py2app-Bundle: App-Launcher in Contents/MacOS/FPX Timetracker
        macos_dir = Path(sys.executable).parent
        launcher = macos_dir / "FPX Timetracker"
        if launcher.exists():
            return [str(launcher)]
        return [sys.executable]
    return [str(PYTHON), str(HERE / "fpx_menubar.py")]


def _autostart_enabled() -> bool:
    return _AGENT_PLIST.exists()


def _autostart_enable():
    _AGENT_PLIST.parent.mkdir(parents=True, exist_ok=True)
    plist = {
        "Label": _AGENT_ID,
        "ProgramArguments": _autostart_args(),
        "RunAtLoad": False,
        "WorkingDirectory": str(ROOT),
    }
    with open(_AGENT_PLIST, "wb") as f:
        plistlib.dump(plist, f)
    subprocess.run(["launchctl", "load", str(_AGENT_PLIST)], check=False)


def _autostart_disable():
    if _AGENT_PLIST.exists():
        subprocess.run(["launchctl", "unload", str(_AGENT_PLIST)], check=False)
        _AGENT_PLIST.unlink(missing_ok=True)


# Im Bundle sind Dependencies bereits eingebettet — kein pip-Install nötig
if not getattr(sys, "frozen", False):
    def _ensure_deps():
        for dep, pkg in [("AppKit", "pyobjc-framework-Cocoa")]:
            try:
                __import__(dep)
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
    _ensure_deps()

import objc
from Foundation import NSObject, NSTimer
from AppKit import (
    NSApplication, NSApp, NSApplicationActivationPolicyAccessory,
    NSStatusBar, NSVariableStatusItemLength,
    NSMenu, NSMenuItem,
    NSEventMaskLeftMouseUp, NSEventMaskRightMouseUp,
    NSEventTypeRightMouseUp, NSEventModifierFlagControl,
)


class AppDelegate(NSObject):

    def applicationDidFinishLaunching_(self, notif):
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        self._proc = None
        self._start_tracker()

        self._bar  = NSStatusBar.systemStatusBar()
        self._item = self._bar.statusItemWithLength_(NSVariableStatusItemLength)
        self._item.setTitle_("⏱")
        self._item.setHighlightMode_(True)

        btn = self._item.button()
        btn.setAction_("iconClicked:")
        btn.setTarget_(self)
        btn.sendActionOn_(NSEventMaskLeftMouseUp | NSEventMaskRightMouseUp)

        self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, "tick:", None, True)

    def iconClicked_(self, sender):
        event    = NSApp.currentEvent()
        is_right = (event and (
            event.type() == NSEventTypeRightMouseUp or
            (event.modifierFlags() & NSEventModifierFlagControl)
        ))
        if is_right:
            self._show_menu()
        else:
            self._toggle()

    def _show_menu(self):
        menu = NSMenu.alloc().init()
        menu.setAutoenablesItems_(False)

        label = "✓  Autostart bei Login" if _autostart_enabled() else "   Autostart bei Login"
        i_auto = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            label, "toggleAutostart:", "")
        i_auto.setTarget_(self)
        menu.addItem_(i_auto)

        menu.addItem_(NSMenuItem.separatorItem())

        i_quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "✕  Beenden", "quitApp:", "q")
        i_quit.setTarget_(self)
        menu.addItem_(i_quit)
        self._item.popUpStatusItemMenu_(menu)

    def toggleAutostart_(self, sender):
        if _autostart_enabled():
            _autostart_disable()
        else:
            _autostart_enable()

    def quitApp_(self, sender):
        write_ipc({"cmd": "quit", "ts": time.time()})
        time.sleep(0.3)
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        NSApp.terminate_(None)

    def _start_tracker(self):
        if getattr(sys, "frozen", False):
            # py2app-Bundle: dedizierten Tracker-Launcher in Contents/MacOS/ verwenden
            macos_dir = Path(sys.executable).parent
            cmd = [str(macos_dir / "fpx_timetracker"), "--popover"]
        else:
            tracker = ROOT / "fpx_timetracker.py"
            if not tracker.exists():
                return
            cmd = [PYTHON, str(tracker), "--popover"]

        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            time.sleep(0.3)
        write_ipc({"state": "start", "visible_state": "hidden"})
        self._proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            env=os.environ.copy(),
            stderr=open(str(DATA_DIR / "fpx_tracker.log"), "w"),
            stdout=subprocess.DEVNULL)
        time.sleep(1.2)

    def _toggle(self):
        d = read_ipc()
        if self._proc is None or self._proc.poll() is not None:
            self._start_tracker()
            write_ipc({"cmd": "show", "ts": time.time()})
            return
        if d.get("visible_state") == "shown":
            write_ipc({"cmd": "hide", "ts": time.time()})
        else:
            write_ipc({"cmd": "show", "ts": time.time()})

    def tick_(self, timer):
        d    = read_ipc()
        if d.get("quit_all") and time.time() - d.get("ts", 0) < 5:
            IPC_FILE.write_text("{}")
            NSApp.terminate_(None)
            return
        txt  = d.get("timer_txt", "")
        proj = d.get("proj_no", "")
        if txt and proj:
            self._item.setTitle_(f"⏱ {proj} {txt}")
        elif txt:
            self._item.setTitle_(f"⏱ {txt}")
        else:
            self._item.setTitle_("⏱")
        if self._proc and self._proc.poll() is not None:
            self._proc = None


if __name__ == "__main__":
    os.chdir(str(ROOT))
    app      = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()

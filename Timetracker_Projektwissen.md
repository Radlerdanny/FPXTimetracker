# FPX Timetracker – Entwicklungsdokumentation

*Stand: Juli 2026 | Version 0.8.1 | Mac + Windows (Monorepo)*

---

## 1. Was ist das?

Internes Tool der Fourplex-Agentur für PROAD-Zeiterfassung direkt aus der Menü-/Taskleiste.  
Offene Todos laden, Timer starten, Zeiten am Tagesende gebündelt nach PROAD buchen — ohne Browser.

**Plattformen:** macOS 12+, Windows 10/11  
**Python:** 3.14.3

---

## 2. Technischer Stack

| Komponente | Mac | Windows |
|---|---|---|
| Tray-Icon | `pyobjc` (NSStatusBar) | `pystray` + `Pillow` |
| Hauptfenster | `tkinter` | `tkinter` |
| PROAD API | `requests` (verify=False) | `requests` (verify=False) |
| IPC | JSON-Datei | JSON-Datei |
| Singleton | `fcntl.flock()` | `msvcrt` Datei-Lock |
| Plattform-Check | `IS_MAC = True` | `IS_WIN = True` |

### Architektur: Zwei separate Prozesse

```
mac/fpx_menubar.py          fpx_timetracker.py
(pyobjc NSStatusBar)        (tkinter Fenster)
         │                         │
         │──── subprocess ────────►│
         │                         │
         │◄──── IPC JSON ──────────┤
              ~/.config/FPX_Timetracker/ipc.json
```

**Warum zwei Prozesse?** `pyobjc` und `tkinter` können auf macOS nicht im gleichen Prozess laufen (Crash: `NSWindow should only be instantiated on the main thread`). Einzige robuste Lösung: getrennte Prozesse.  
Auf Windows gilt das nicht — `pystray` und `tkinter` könnten im selben Prozess laufen, aber die getrennte Architektur wird der Einheitlichkeit halber beibehalten.

---

## 3. Dateistruktur

```
FPXTimetracker/
├── config.py                # Gemeinsame Konfiguration (IS_MAC, IS_WIN, Pfade, IPC, DPI)
├── fpx_timetracker.py       # Hauptfenster — Mac + Windows (IS_MAC/IS_WIN checks)
├── requirements.txt         # Abhängigkeiten
├── README.md                # Nutzer-Dokumentation
├── Timetracker_Projektwissen.md  # Diese Datei
├── Logo/
│   ├── Icon.png             # App-Icon Quelle (600×600 RGBA)
│   ├── Mac/
│   │   └── app.icns         # Mac App-Icon (10 Größen inkl. @2x Retina)
│   └── Windows/
│       ├── app.ico          # Windows App-Icon (7 Größen, HiDPI)
│       └── tray.ico         # Windows Tray-Icon (8 Größen, HiDPI)
├── mac/
│   └── fpx_menubar.py       # Menüleisten-Prozess (macOS, pyobjc)
└── windows/
    └── fpx_tray.py          # Tray-Prozess (Windows, pystray)
```

### Datenspeicherung lokal

```
~/.config/FPX_Timetracker/       (Mac)
%APPDATA%\FPXTimetracker\        (Windows)
├── timetracker_data.json        # Config, Sessions, Beschreibungen
├── ipc.json                     # IPC zwischen den Prozessen
└── fpx_menubar.lock / fpx_tray.lock
```

### timetracker_data.json Struktur

```json
{
  "config": {
    "api_key": "...",
    "person_urno": 1411,
    "person_name": "Daniel Losch",
    "person_kuerzel": "DL"
  },
  "sessions":       { "2026-04-01": { "12345": [{"start_ts":..., "end_ts":..., "minutes":10}] } },
  "booked_today":   { "2026-04-01": [12345, 67890] },
  "descriptions":   { "12345": "Beschreibungstext" },
  "pending_status": { "12345": "erledigt" },
  "quick_hours":    { "12345": 1.5 },
  "last_tracked":   [12345, 67890]
}
```

---

## 4. config.py — Gemeinsame Konfiguration

`config.py` enthält alle plattformübergreifenden Konstanten und Hilfsfunktionen:

```python
APP_VERSION   # aktuelles Versions-String
IS_WIN / IS_MAC       # Plattform-Flags
FONT_MAIN / FONT_MONO # Schriften ("Helvetica Neue" / "Menlo" auf Mac, "Segoe UI" / "Consolas" auf Win)
DATA_DIR / DATA_FILE / IPC_FILE / LOCK_FILE  # Pfade (plattformabhängig)
write_ipc(d) / read_ipc()  # IPC-Hilfsfunktionen
asset_path(name)            # Assets im Dev-Modus + PyInstaller-Bundle
SCALE / s(n)                # DPI-Skalierung (1:1 auf Mac, DPI-aware auf Win)
get_work_area()             # Arbeitsbereich-Dimensionen (Win: Taskleisten-Erkennung)
```

---

## 5. IPC-Protokoll

Datei: `~/.config/FPX_Timetracker/ipc.json`

| Feld | Werte | Bedeutung |
|---|---|---|
| `cmd` | `show`, `hide`, `reload`, `quit` | Befehl an Tracker-Prozess |
| `visible_state` | `shown`, `hidden` | Sichtbarkeitsstatus |
| `timer_txt` | `"02:34"` | Laufende Timer-Zeit |
| `proj_no` | `"FPX-422"` | Aktives Projekt für Menü-/Taskleiste |
| `quit_all` | `true` | Tracker → Menubar: App komplett beenden (beide Prozesse) |
| `ts` | Unix-Timestamp | Verhindert doppelte Ausführung |

---

## 6. PROAD API

- **Base URL:** `https://proad.fourplex.de/api/v5`
- **Auth:** Header `apikey: <KEY>`
- **SSL:** `verify=False` (selbst-signiertes Zertifikat)

### Status-Keys

| Key | Status |
|---|---|
| `100` | Neu |
| `200` | Begonnen |
| `300` | Wartet |
| `400` | Zurückgestellt |
| `500` | Erledigt |
| `600` | Abgebrochen |

### Wichtige Endpoints

```
GET  /tasks?person={urno}&from_date={von}--{bis}  Todos laden
GET  /tasks/{urno}                                Einzelnes Todo
PUT  /tasks/{urno}                                Status/Stunden ändern
POST /tasks                                       Neues Todo anlegen
POST /timeregs                                    Zeit buchen
GET  /service_codes                               Leistungsarten
GET  /projects?projectno={nr}                     Projekt direkt per Nummer suchen
```

**Wichtig `GET /projects`:** Immer `?projectno=` verwenden, nie `?order_date=`.  
Datumslimit + 2000er-Cap würden alte Projekte (z.B. FPX-120 aus 2022) nicht zurückliefern.

### Zeiten buchen (`/timeregs`)

```python
{
  "urno_person":       person_urno,
  "urno_project":      projekt_urno,
  "urno_task":         todo_urno,
  "urno_service_code": leistungsart_urno,
  "from_date":         "2026-04-01",
  "input":             1.5,     # Stunden als float
  "chargeable":        1
}
```

---

## 7. Projektmanager URNOs

| Name | Kürzel | URNO |
|---|---|---|
| Anna Embach | AE | 632 |
| Bastian Brezinski | BB | 21 |
| Daniel Losch | DL | 1411 |
| David Winkler | DW | 8 |
| Goezde Dincgez | GD | 1531 |
| Katharina Schweigert | KJ | 1199 |
| Lea Schuster | LS | 954 |
| Marcus Tischler | MT | 9 |
| Pascal Tischler | PT | 1198 |
| Tatjana Angersbach | TA | 1680 |

---

## 8. Farbschema (Dark Theme)

```python
C = {
    "bg":"#111111","panel":"#181818","card":"#1F1F1F","card2":"#272727",
    "border":"#333333","accent":"#479CC5","accent2":"#2E7A9E","accent_dim":"#1D4D63",
    "text":"#F0EDE8","text_dim":"#999999","text_mid":"#CCCCCC",
    "green":"#4CAF7D","green2":"#3a9e68","green_dim":"#1E4D35",
    "red":"#E05555","orange":"#CC5555","yellow":"#E0C050",
    "gray_btn":"#444444","gray_btn2":"#383838","hover":"#2A2A2A",
}
```

---

## 9. Features v0.8.1

### Plattform
- Unified Codebase: Mac + Windows in einem Repo
- `config.py` als gemeinsame Konfiguration (Plattform-Flags, Pfade, IPC, DPI)
- `fpx_timetracker.py` mit `IS_MAC`/`IS_WIN`-Checks für plattformspezifisches Verhalten

### Mac-spezifisch
- Popover-Fenster: `overrideredirect(False)`, Titelbar 28px hinter Menüleiste versteckt
- Play/Pause-Button: `tk.Frame` + `tk.Label` (28×24px, Text-Icon)
- Footer: fixe Höhe 54px, kein `pack_propagate`
- Dialoge: native macOS `messagebox` (immer vorne, kein z-Order-Problem)
- **Dock-Icon:** `fpx_timetracker.py` zeigt ein Dock-Icon mit `app.icns` — Fallback wenn Menüleiste voll ist
  - Dock-Klick → Popover öffnen/schließen (`::tk::mac::ReopenApplication`)
  - Dock → Beenden oder Cmd+Q → beendet beide Prozesse (`::tk::mac::Quit` schreibt `quit_all` ins IPC)
  - `fpx_menubar.py` bleibt unsichtbar (`NSApplicationActivationPolicyAccessory`), liest `quit_all` im Tick und beendet sich
  - Pattern: etabliert — viele macOS-Apps haben Menüleisten-Icon + Dock-Icon parallel (z.B. Fantastical)
- **Rechtsklick-Menü:** „Autostart bei Login" (Toggle mit Häkchen) + „Beenden" — „Grosses Fenster" wurde entfernt (war defekt + unnötig)
- **Autostart (Mac):** LaunchAgent-Plist in `~/Library/LaunchAgents/de.fourplex.timetracker.plist` — Toggle via `launchctl load/unload`. Im Dev-Modus startet Plist `python fpx_menubar.py`, im Bundle die `.app`-Binary (`sys.executable`).
- **Rotes X:** versteckt Fenster (`_animate_hide`) statt App zu beenden — `WM_DELETE_WINDOW` abgefangen

### Windows-spezifisch
- Popover: `overrideredirect(True)`, Taskleisten-Kanten-Erkennung via `get_work_area()`
- Play/Pause-Button: `tk.Canvas` (34×30px, pixel-gezeichnete Icons)
- Dialoge: custom Dark-Theme `Toplevel`
- `WM_SETREDRAW`-Optimierung gegen Flicker beim Listen-Rendern
- **Multi-DPI Fix (4 Schritte):**
  - `SetProcessDpiAwareness(1)` als absolut erstes in `fpx_timetracker.py` — vor allen Imports, sonst greift es nicht
  - Single `tk.Tk()` Root für gesamte Laufzeit: `SetupWindow` ist `tk.Toplevel`, `FPXTimeTracker` bekommt `shared_root` übergeben
  - `tk.scaling` normalisiert im `__main__`-Block mit `_sys_sc * 72 / 96` (Fourplex-Hub-Formel), danach `config.SCALE` aktualisiert
  - `AppUserModelID = "de.fourplex.timetracker"` → Windows zeigt App-Name statt "Python" in Taskleiste
- **Dunkle Titelleiste:** `DwmSetWindowAttribute(hwnd, 20, 1)` via `_set_dark_titlebar()` — Titelleiste passt zum Dark Theme
- **Icons:** `Logo/Windows/app.ico` (Fenster) + `Logo/Windows/tray.ico` (Tray) — direkte Pfade, nicht `asset_path()`
- **Tray-Menü:** „Autostart bei Login" als Toggle-Item mit `checked=lambda item: _autostart_enabled()` — pystray rendert Häkchen dynamisch
- **Autostart (Windows):** Registry-Eintrag `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` → Key `FPX Timetracker`. Im Dev-Modus `"python.exe" "fpx_tray.py"`, im Bundle direkt `sys.executable`. Lesen/Schreiben via `winreg` (stdlib, kein Extra-Import nötig).

### Allgemein
- `+To-Do` Schnelleingabe: Projekt-Suche jetzt per `?projectno=` (kein Datumslimit, kein 2000er-Cap)
- `+To-Do` Validierung: Fehlermeldung bei leerer, unvollständiger oder ungültiger Eingabe — kein stiller Default mehr
- `+To-Do` Double-Click-Schutz: Button graut ab während API-Aufruf läuft
- Todo-Übertragen-Badge: `✓ übertragen` + gedimmter Text nach Export

---

## 10. Fenster-Positionierung

### Mac (Popover)
```python
self._W, self._H = 380, min(660, int(sh * 0.76))
self._X = sw - self._W - 8
self._Y = 24        # Menüleistenhöhe
self._TBH = 28      # Titelbar-Höhe — Fenster wird 28px nach oben verschoben
```

### Windows (Popover)
```python
left, top, right, bottom, edge = get_work_area()
# Positionierung abhängig davon wo die Taskleiste ist (oben/unten/links/rechts)
```

---

## 11. Code-Architektur (fpx_timetracker.py)

```python
# Hilfsfunktionen (top-level)
_apply_icon(root)          # Setzt app.ico auf Windows
_set_dark_titlebar(window) # DwmSetWindowAttribute Attr 20 — nur Windows

class SetupWindow:
    __init__(shared_root)  # tk.Toplevel, blockiert via shared_root.wait_window()
    _build() / _save()     # UI + Speichern; alle self.root → self.win
    run()                  # gibt self.result zurück (kein mainloop nötig)

class FPXTimeTracker:
    __init__(config, shared_root)  # Config, UI, IPC-Loop
    _build_window(shared_root)     # Popover-Fenster-Setup (Mac + Win)
    _build_ui()                    # Topbar, Timer, Liste, Footer
    _dock_toggle()                 # Mac: Popover öffnen/schließen via Dock-Klick
    _dock_quit()                   # Mac: quit_all ins IPC schreiben, Root zerstören

    # Daten
    _get_parts(urno)          # Zeit-Parts für Todo heute
    _get_minutes(urno)        # Gesamt-Minuten für Todo heute
    _add_part(urno, ...)      # Part hinzufügen
    _get_desc(urno)           # Beschreibung lesen
    _set_desc(urno, text)     # Beschreibung schreiben
    _get_pending(urno)        # Pending-Status lesen
    _set_pending(urno, st)    # Pending-Status schreiben

    # Timer
    _toggle_timer(urno)       # Timer starten/stoppen
    _start_timer / _stop_timer / _start_pulse

    # API
    _load_todos / _fetch_todos / _on_load_done
    _quick_entry              # +To-Do Schnelleingabe

    # UI
    _render_list / _render_row / _render_date_sep / _draw_timer_block

    # Export
    _close_day
```

---

## 12. Bekannte Probleme / Limitations

### Mac: Titelbar im Popover
`overrideredirect(True)` blockiert Tastatur-Input auf macOS Python 3.14.  
Workaround: Fenster 28px nach oben verschoben → Titelbar hinter Menüleiste versteckt.  
Echte Lösung: Apple Developer Account (99€/Jahr) + Code-Signierung.

### Kein Apple-Signing (Mac)
App ist nicht signiert. Installer muss `xattr -dr com.apple.quarantine` setzen.  
In Firmen mit MDM (Jamf etc.) könnte das geblockt sein.

### PyInstaller funktioniert nicht (Mac)
Wegen Zwei-Prozess-Architektur entsteht ein Spawn-Loop. Stattdessen: manuelles `.app`-Bundle im Setup-Skript.

### Intel-Mac: Langsame Installation
`pyobjc` kompiliert ggf. aus Quelltext → kann 5–15 Min dauern. Kein Fix möglich außer spezifische Python-Versionen mit Wheels vorzuschreiben.

---

## 13. Lessons Learned

1. **pyobjc + tkinter = getrennte Prozesse** auf macOS Python 3.14
2. **`overrideredirect(True)`** blockiert Tastatur-Input auf modernem macOS
3. **`os.execv` für Relaunch** funktioniert nicht mit pyobjc/fcntl → stattdessen detached subprocess + `os._exit`
4. **PROAD +To-Do:** NIE direkt `/timeregs` nach `/tasks` POST senden, sonst wird `hours_left` auf 0 gesetzt
5. **PROAD `/projects`:** immer `?projectno=` statt `?order_date=` — sonst fehlen alte Projekte
6. **`fcntl` Singleton** ist die sauberste Methode für Single-Instance auf macOS
7. **IPC über JSON-Datei** ist einfach und zuverlässig
8. **Mac-Dialoge** müssen native `messagebox` verwenden — custom `Toplevel` mit `-topmost` erscheint trotzdem hinter der Menüleiste
9. **Windows DPI: Reihenfolge ist kritisch** — `SetProcessDpiAwareness` MUSS vor allen Imports stehen. In `config.py` ist es bereits zu spät, weil tkinter beim Import geladen wird.
10. **Automator + Subprocess:** `subprocess.Popen(..., start_new_session=True)` ist die einzige zuverlässige Methode um das Zahnrad nach dem Start verschwinden zu lassen. `nohup` / `& disown` reicht nicht.
11. **Mac + mehrere Python-Versionen:** Homebrew installiert Python unter `/opt/homebrew/opt/python@X.Y/` und überschreibt den `python3`-Symlink. Immer explizit `python3.14` verwenden oder Homebrew-Python entfernen wenn es nicht gebraucht wird.

---

## 14. Roadmap

### Kurzfristig
- [ ] Auto-Updater neu einrichten (nach GitHub-Repo-Migration)
- [ ] Installer neu bauen (Mac `.command` + Windows `.exe`-Wrapper)
- [x] Autostart bei Login (Mac: LaunchAgent, Windows: Registry) — Toggle im Rechtsklick/Tray-Menü
- [x] Windows `fpx_tray.py` auf `config.py` umstellen
- [x] Windows Multi-DPI Fix (SetProcessDpiAwareness, single Tk root, AppUserModelID, dark titlebar)

### Mittelfristig
- [x] Eigenes App-Icon (`app.icns` Mac, `app.ico` + `tray.ico` Windows — HiDPI)
- [ ] Umstieg auf `customtkinter` (modernere UI)
- [ ] Apple Developer Account + Code-Signierung + Notarisierung

---

## 15. Kontakt / Wartung

**Owner:** Daniel Losch (DL) — d.losch@fourplex.de  
**Bei Übergabe an einen neuen Chat:** Diese Datei zuerst lesen lassen.

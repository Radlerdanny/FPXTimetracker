# FPX Timetracker

Internes Tool der Fourplex-Agentur für PROAD-Zeiterfassung direkt aus der Menü- bzw. Taskleiste.  
Offene Todos sehen, Timer starten, Zeiten am Tagesende gebündelt nach PROAD buchen — ohne den Browser zu öffnen.

**Plattformen:** macOS 12+ · Windows 10/11  
**Version:** 0.8.1  
**Python:** 3.14.3

---

## Installation

### macOS

> Installer folgt nach GitHub-Migration.

Manuell starten:
```bash
pip install requests pyobjc-framework-Cocoa
python mac/fpx_menubar.py
```

### Windows

> Installer folgt nach GitHub-Migration.

Manuell starten:
```bash
pip install requests pystray pillow
python windows/fpx_tray.py
```

---

## Bedienung

| Aktion | Mac | Windows |
|---|---|---|
| Fenster öffnen/schließen | Linksklick auf ⏱ oder Dock-Icon | Linksklick auf Tray-Icon |
| Beenden | Rechtsklick → „Beenden" oder Dock → Beenden | Rechtsklick → „Beenden" |
| Autostart bei Login | Rechtsklick → „Autostart bei Login" (Toggle) | Rechtsklick → „Autostart bei Login" (Toggle) |
| Timer starten/stoppen | ▶-Button neben Todo | ▶-Button neben Todo |
| Todo als erledigt markieren | „Erledigt"-Button | „Erledigt"-Button |
| Beschreibung hinzufügen | ✎-Stift neben Todo-Namen | ✎-Stift neben Todo-Namen |
| Stunden manuell tracken | „Tracken"-Button + Stunden eintragen | „Tracken"-Button + Stunden eintragen |
| Schnell-Todo anlegen | `PROJEKTNR LEISTUNG STUNDEN` oben (z.B. `FPX-422 GRA 0.5`) | gleich |
| Tag abschließen | „Tag abschliessen & nach PROAD übertragen" | gleich |

---

## Beim ersten Start

1. **PROAD API-Key** eintragen — zu finden in PROAD → Benutzer → PROAD API → Key kopieren
2. **Eigenen Namen** aus der Liste auswählen

---

## Projektstruktur

```
├── config.py              Gemeinsame Konfiguration (Mac + Windows)
├── fpx_timetracker.py     Hauptfenster (tkinter, Mac + Windows)
├── mac/
│   └── fpx_menubar.py     Menüleisten-Prozess (macOS)
└── windows/
    └── fpx_tray.py        Tray-Prozess (Windows)
```

---

## Entwicklung

Siehe [Timetracker_Projektwissen.md](Timetracker_Projektwissen.md) für technische Details, API-Dokumentation und Architektur.

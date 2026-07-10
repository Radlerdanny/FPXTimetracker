#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# FPX Timetracker – Installer
# Entfernt die macOS-Sicherheitssperre (Quarantäne) von der App.
# Danach kannst du FPX Timetracker.app per Doppelklick starten.
# ──────────────────────────────────────────────────────────────────────────────

APP="$(dirname "$0")/FPX Timetracker.app"

clear
echo "═══════════════════════════════════════════"
echo "  FPX Timetracker – Installation"
echo "═══════════════════════════════════════════"
echo ""

if [ ! -d "$APP" ]; then
    echo "⚠️  FPX Timetracker.app nicht gefunden."
    echo ""
    echo "Stelle sicher, dass sich diese Datei im"
    echo "gleichen Ordner wie FPX Timetracker.app befindet."
    echo ""
    read -p "Enter zum Beenden…"
    exit 1
fi

echo "→ Entferne macOS-Sicherheitssperre…"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null
chmod +x "$APP/Contents/MacOS/"* 2>/dev/null

echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ Fertig!"
echo "═══════════════════════════════════════════"
echo ""
echo "  Du kannst FPX Timetracker.app jetzt"
echo "  per Doppelklick starten."
echo ""
sleep 2

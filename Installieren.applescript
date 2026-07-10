-- FPX Timetracker – Installer
-- Entfernt die macOS-Sicherheitssperre (Quarantäne) von der App.
-- Danach kann FPX Timetracker.app per Doppelklick gestartet werden.

set scriptPath to (path to me as text)
set scriptDirectory to POSIX path of scriptPath
set scriptDirectory to do shell script "dirname " & quoted form of scriptDirectory

set appPath to scriptDirectory & "/FPX Timetracker.app"

do shell script "xattr -c " & quoted form of appPath
do shell script "xattr -r -d com.apple.quarantine " & quoted form of appPath
do shell script "chmod +x " & quoted form of (appPath & "/Contents/MacOS") & "/*"

display dialog "Fertig! Du kannst FPX Timetracker.app jetzt per Doppelklick starten." buttons {"OK"} default button "OK" with title "FPX Timetracker" with icon note

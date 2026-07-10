; FPX Timetracker – Inno Setup Installationsskript
; Aufruf: ISCC /DMyAppVersion=0.8.1 windows\fpx_installer.iss

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

#define MyAppName      "FPX Timetracker"
#define MyAppPublisher "Fourplex GmbH"
#define MyAppURL       "https://github.com/Radlerdanny/FPXTimetracker"
#define MyAppExeName   "FPX Timetracker.exe"

[Setup]
AppId={{DE.FOURPLEX.TIMETRACKER}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; SourceDir = Projektverzeichnis (eine Ebene über windows/)
SourceDir=..
OutputDir=dist
OutputBaseFilename=FPXTimetracker_Win_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Kein UAC-Prompt – Installation im Benutzerverzeichnis
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Gesamten PyInstaller-Ausgabe-Ordner kopieren (inkl. _internal/)
Source: "dist\FPX Timetracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Optionaler Start nach Installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

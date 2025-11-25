; Inno Setup Script for TelemetryIQ Windows Installer
; This installer sets up Python environment, dependencies, and drivers

#define MyAppName "TelemetryIQ"
#define MyAppVersion "2.0"
#define MyAppPublisher "TelemetryIQ"
#define MyAppURL "https://telemetryiq.com"
#define MyAppExeName "telemetryiq.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=dist
OutputBaseFilename=TelemetryIQ-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Application files
Source: "AI-TUNER-AGENT\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Python runtime (if bundled)
Source: "python_runtime\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists("python_runtime")
; Drivers
Source: "drivers\windows\*"; DestDir: "{app}\drivers"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists("drivers\windows")
; Documentation
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Install Python if not present
Filename: "https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe"; Description: "Download Python 3.11 (if not installed)"; Flags: shellexec postinstall skipifsilent; Check: not PythonInstalled
; Install drivers
Filename: "{app}\drivers\FTDI\CDM21228_Setup.exe"; Description: "Install FTDI Drivers"; Flags: shellexec postinstall skipifsilent; Check: FileExists("{app}\drivers\FTDI\CDM21228_Setup.exe")
Filename: "{app}\drivers\CH340\CH341SER.EXE"; Description: "Install CH340 Drivers"; Flags: shellexec postinstall skipifsilent; Check: FileExists("{app}\drivers\CH340\CH341SER.EXE")
; Setup Python environment
Filename: "{app}\setup_windows.bat"; Description: "Setup Python Environment"; Flags: shellexec postinstall; WorkingDir: "{app}"

[Code]
function PythonInstalled: Boolean;
var
  PythonPath: String;
begin
  Result := RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKEY_CURRENT_USER, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath);
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Check for Windows 10 or later
  if not IsWin10OrLater then
  begin
    MsgBox('TelemetryIQ requires Windows 10 or later.', mbError, MB_OK);
    Result := False;
  end;
end;












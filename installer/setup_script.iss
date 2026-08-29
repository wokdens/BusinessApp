; Inno Setup Script for BusinessApp
; Powered by wokdens.com

#define MyAppName "BusinessApp"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Wokdens"
#define MyAppURL "https://wokdens.com"
#define MyAppExeName "BusinessApp.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{D9A3B657-4E2F-4A92-BF38-9B25A7C12F89}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=BusinessApp_Setup_v1.0
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no

; Version Info embedded into Setup.exe
VersionInfoVersion=1.0.0.0
VersionInfoCompany=Wokdens
VersionInfoDescription=BusinessApp Installation Wizard
VersionInfoCopyright=Copyright (C) 2026 Powered by wokdens.com
VersionInfoProductName=BusinessApp

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\BusinessApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\certificates\wokdens_codesign.cer"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent


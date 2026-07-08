; Inno Setup script for Inyfinn Photo Resizer
#define MyAppName "Inyfinn Photo Resizer"
#define MyAppVersion "1.0.11"
#define MyAppPublisher "Inyfinn"
#define MyAppExeName "InyfinnPhotoResizer.exe"
#define MyAppMutex "InyfinnPhotoResizerAppMutex"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\installer-output
OutputBaseFilename=InyfinnPhotoResizer-{#MyAppVersion}-setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
AppMutex={#MyAppMutex}
CloseApplications=force
CloseApplicationsFilter=*.exe,*.dll,*.pyd
RestartApplications=no
MinVersion=10.0

; Podpisywanie (SmartScreen): po zbudowaniu uruchom sign_file.ps1 na setup.exe
; Ustaw INYFINN_CODESIGN_PFX i INYFINN_CODESIGN_PASS
[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\InyfinnPhotoResizer.exe"; DestDir: "{app}"; Flags: ignoreversion restartreplace
Source: "..\..\InyfinnPhotoResizer.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Code]
procedure KillAppProcesses;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{cmd}'), '/C taskkill /F /IM {#MyAppExeName} /T', '', SW_HIDE,
    ewWaitUntilTerminated, ResultCode);
  Sleep(1500);
end;

function InitializeSetup(): Boolean;
begin
  KillAppProcesses;
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  KillAppProcesses;
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if DirExists(ExpandConstant('{app}\_internal')) then
      DelTree(ExpandConstant('{app}\_internal'), True, True, True);
  end;
end;

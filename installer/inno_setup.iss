; 3D-MM (3D Model Manager) - Inno Setup Installer Script
; This script creates a professional Windows installer for the 3D-MM application

#define MyAppName "3D-MM"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "3D-MM Development Team"
#define MyAppURL "https://3dmm.local"
#define MyAppExeName "3D-MM.exe"
#define MyAppAssocName "3D Model Manager"

[Setup]
; Application information
AppId={{8E5F2E3A-1B2C-3D4E-5F6A-7B8C9D0E1F2A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2024 {#MyAppPublisher}

; Default installation directory
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; Installer executable information
OutputBaseFilename=3D-MM-Setup-{#MyAppVersion}
OutputDir=..\dist
SetupIconFile=assets\setup_icon.ico
Compression=lzma2/max
SolidCompression=yes
InternalCompressLevel=max

; Installation options
AllowNoIcons=yes
LicenseFile=assets\license.txt
InfoBeforeFile=assets\readme.txt
WizardImageFile=assets\wizard_image.bmp
WizardSmallImageFile=assets\small_image.bmp
ShowLanguageDialog=yes
Languages=en
MinVersion=6.1sp1

; Architectures
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; OnlyBelowVersion: 6.1; Flags: unchecked

[Files]
; Main application executable
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Application resources
Source: "..\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

; License and readme files
Source: "assets\license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\readme.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Comment: "3D Model Manager"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"; Comment: "3D Model Manager"

; Quick Launch shortcut
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\{#MyAppExeName}"; Comment: "3D Model Manager"

[Registry]
; Application registration
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"

; File associations for 3D model formats
Root: HKCR; Subkey: ".stl"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName}STL"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "{#MyAppName}STL"; ValueType: string; ValueName: ""; ValueData: "{#MyAssocName} STL File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "{#MyAppName}STL\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCR; Subkey: "{#MyAppName}STL\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

Root: HKCR; Subkey: ".obj"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName}OBJ"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "{#MyAppName}OBJ"; ValueType: string; ValueName: ""; ValueData: "{#MyAssocName} OBJ File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "{#MyAppName}OBJ\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCR; Subkey: "{#MyAppName}OBJ\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

Root: HKCR; Subkey: ".3mf"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName}3MF"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "{#MyAppName}3MF"; ValueType: string; ValueName: ""; ValueData: "{#MyAssocName} 3MF File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "{#MyAppName}3MF\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCR; Subkey: "{#MyAppName}3MF\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

Root: HKCR; Subkey: ".step"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName}STEP"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "{#MyAppName}STEP"; ValueType: string; ValueName: ""; ValueData: "{#MyAssocName} STEP File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "{#MyAppName}STEP\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCR; Subkey: "{#MyAppName}STEP\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

Root: HKCR; Subkey: ".stp"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName}STEP"; Flags: uninsdeletevalue

[Run]
; Launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove application data directory (optional - commented out for safety)
; Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

[UninstallRun]
; Close application before uninstall (if running)
Filename: "{cmd}"; Parameters: "/C ""taskkill /F /IM {#MyAppExeName} 2>NUL"""; RunOnceId: "KillApp"; Flags: runhidden waituntilterminated

[Code]
// Custom code for settings migration and enhanced installation

function InitializeSetup(): Boolean;
begin
  // Check if .NET Framework 4.5 or higher is installed (required for some components)
  if not IsDotNetInstalled(4, 0) then
  begin
    MsgBox('3D-MM requires .NET Framework 4.5 or higher to be installed.' + #13#13 +
           'Please install .NET Framework 4.5 or higher and run the setup again.' + #13#13 +
           'You can download it from: https://www.microsoft.com/net/download',
           mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  OldAppPath: string;
  OldVersion: string;
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Check for previous installation and migrate settings
    if RegQueryStringValue(HKLM, 'Software\{#MyAppPublisher}\{#MyAppName}', 'InstallPath', OldAppPath) then
    begin
      if RegQueryStringValue(HKLM, 'Software\{#MyAppPublisher}\{#MyAppName}', 'Version', OldVersion) then
      begin
        // Migrate settings from previous version
        if OldAppPath <> ExpandConstant('{app}') then
        begin
          Log('Migrating settings from previous installation at: ' + OldAppPath);
          
          // Copy user data if it exists
          if DirExists(OldAppPath + '\data') then
          begin
            if not DirExists(ExpandConstant('{app}\data')) then
              CreateDir(ExpandConstant('{app}\data'));
              
            // Use xcopy to preserve directory structure
            Exec(ExpandConstant('{cmd}'), '/C xcopy "' + OldAppPath + '\data\*" "' + 
                 ExpandConstant('{app}\data') + '" /E /I /H /Y', '', SW_HIDE, ewWaitUntilTerminated, 
                 ResultCode);
          end;
          
          // Copy user settings if they exist
          if DirExists(ExpandConstant('{localappdata}\{#MyAppName}')) and
             DirExists(ExpandConstant('{localappdata}\{#MyAppName}_old')) = False then
          begin
            RenameFile(ExpandConstant('{localappdata}\{#MyAppName}'), 
                      ExpandConstant('{localappdata}\{#MyAppName}_old'));
          end;
        end;
      end;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Ask user if they want to remove user data
    if MsgBox('Do you want to remove all user data and settings?' + #13#13 +
              'This will delete your model library and preferences.' + #13#13 +
              'Choose No to keep your data for future installations.',
              mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
    begin
      // Remove application data directory
      if DirExists(ExpandConstant('{localappdata}\{#MyAppName}')) then
        DelTree(ExpandConstant('{localappdata}\{#MyAppName}'), True, True, True);
        
      // Remove backup data directory if it exists
      if DirExists(ExpandConstant('{localappdata}\{#MyAppName}_old')) then
        DelTree(ExpandConstant('{localappdata}\{#MyAppName}_old'), True, True, True);
    end;
  end;
end;

// Function to check if .NET Framework is installed
function IsDotNetInstalled(version: string; service: cardinal): boolean;
var
  key: string;
  install, serviceCount: cardinal;
  success: boolean;
begin
  key := 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v' + version;
  success := RegQueryDWordValue(HKLM, key, 'Install', install);
  
  if success and (install = 1) then
  begin
    success := RegQueryDWordValue(HKLM, key, 'Servicing', serviceCount);
    Result := success and (serviceCount >= service);
  end
  else
    Result := False;
end;
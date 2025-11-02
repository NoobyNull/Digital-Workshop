!include "MUI2.nsh"

; Version information
!define MyAppName "Digital Workshop"
!define MyAppVersion "1.0.0"
!define MyAppPublisher "Digital Workshop Development Team"
!define MyAppURL "https://github.com/NoobyNull/Digital-Workshop"
!define MyAppExeName "Digital Workshop.exe"

; Installer settings
Name "${MyAppName} ${MyAppVersion}"
OutFile "Digital Workshop-Setup-${MyAppVersion}.exe"

; Request admin privileges for system installation
RequestExecutionLevel highest

; Variables for installation type
Var InstallationType
Var RegistryRoot
Var RegistryPath

; Default to user installation
InstallDir "$LOCALAPPDATA\${MyAppName}"
InstallDirRegKey HKCU "Software\${MyAppName}" ""

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "resources\license.txt"
; Custom page for installation type selection
Page custom InstallTypeSelection InstallTypeSelectionLeave
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ============================================================================
; Custom Installation Type Selection Page
; ============================================================================

Function InstallTypeSelection
  !insertmacro MUI_HEADER_TEXT "Installation Type" "Choose how to install Digital Workshop"

  nsDialogs::Create 1018
  Pop $0

  ${If} $0 == error
    Abort
  ${EndIf}

  ; Title
  ${NSD_CreateLabel} 0 0 100% 12u "Select installation type:"
  Pop $0

  ; User installation radio button
  ${NSD_CreateRadioButton} 10 20 90% 12u "User Installation (Recommended)"
  Pop $0
  ${NSD_OnClick} $0 UserInstallSelected
  ${If} $InstallationType == ""
    SendMessage $0 ${BM_SETCHECK} ${BST_CHECKED} 0
  ${EndIf}

  ; User installation description
  ${NSD_CreateLabel} 20 35 85% 20u "Install for current user only.$\nNo admin privileges required.$\nData stored in: %LOCALAPPDATA%\Digital Workshop"
  Pop $0
  SetCtlColors $0 0x666666 transparent

  ; System installation radio button
  ${NSD_CreateRadioButton} 10 60 90% 12u "System Installation"
  Pop $0
  ${NSD_OnClick} $0 SystemInstallSelected

  ; System installation description
  ${NSD_CreateLabel} 20 75 85% 20u "Install for all users.$\nRequires administrator privileges.$\nData stored in: %PROGRAMFILES%\Digital Workshop"
  Pop $0
  SetCtlColors $0 0x666666 transparent

  nsDialogs::Show
FunctionEnd

Function UserInstallSelected
  StrCpy $InstallationType "user"
  StrCpy $RegistryRoot "HKCU"
  StrCpy $INSTDIR "$LOCALAPPDATA\${MyAppName}"
FunctionEnd

Function SystemInstallSelected
  StrCpy $InstallationType "system"
  StrCpy $RegistryRoot "HKLM"
  StrCpy $INSTDIR "$PROGRAMFILES\${MyAppName}"
FunctionEnd

Function InstallTypeSelectionLeave
  ${If} $InstallationType == ""
    StrCpy $InstallationType "user"
    StrCpy $RegistryRoot "HKCU"
    StrCpy $INSTDIR "$LOCALAPPDATA\${MyAppName}"
  ${EndIf}
FunctionEnd

; ============================================================================
; Installer Section
; ============================================================================

Section "Install"
  SetOutPath "$INSTDIR"

  ; Copy executable
  File "dist\Digital Workshop.exe"

  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\${MyAppName}"
  CreateShortcut "$SMPROGRAMS\${MyAppName}\${MyAppName}.lnk" "$INSTDIR\${MyAppExeName}"
  CreateShortcut "$SMPROGRAMS\${MyAppName}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  CreateShortcut "$DESKTOP\${MyAppName}.lnk" "$INSTDIR\${MyAppExeName}"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"

  ; Write registry keys based on installation type
  ${If} $RegistryRoot == "HKLM"
    ; System installation - write to HKEY_LOCAL_MACHINE
    WriteRegStr HKLM "Software\${MyAppName}" "" "$INSTDIR"
    WriteRegStr HKLM "Software\${MyAppName}" "InstallationType" "system"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "DisplayName" "${MyAppName} ${MyAppVersion} (System)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "DisplayVersion" "${MyAppVersion}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "Publisher" "${MyAppPublisher}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "URLInfoAbout" "${MyAppURL}"
  ${Else}
    ; User installation - write to HKEY_CURRENT_USER
    WriteRegStr HKCU "Software\${MyAppName}" "" "$INSTDIR"
    WriteRegStr HKCU "Software\${MyAppName}" "InstallationType" "user"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "DisplayName" "${MyAppName} ${MyAppVersion}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "DisplayVersion" "${MyAppVersion}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "Publisher" "${MyAppPublisher}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "URLInfoAbout" "${MyAppURL}"
  ${EndIf}
SectionEnd

; ============================================================================
; Uninstaller Section
; ============================================================================

Section "Uninstall"
  ; Detect installation type from registry
  ReadRegStr $RegistryRoot HKLM "Software\${MyAppName}" "InstallationType"
  ${If} $RegistryRoot == "system"
    StrCpy $RegistryRoot "HKLM"
  ${Else}
    StrCpy $RegistryRoot "HKCU"
  ${EndIf}

  ; Remove shortcuts
  Delete "$SMPROGRAMS\${MyAppName}\${MyAppName}.lnk"
  Delete "$SMPROGRAMS\${MyAppName}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${MyAppName}"
  Delete "$DESKTOP\${MyAppName}.lnk"

  ; Remove executable and uninstaller
  Delete "$INSTDIR\${MyAppExeName}"
  Delete "$INSTDIR\uninstall.exe"
  RMDir "$INSTDIR"

  ; Remove registry keys based on installation type
  ${If} $RegistryRoot == "HKLM"
    DeleteRegKey HKLM "Software\${MyAppName}"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}"
  ${Else}
    DeleteRegKey HKCU "Software\${MyAppName}"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}"
  ${EndIf}
SectionEnd
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
InstallDir "$PROGRAMFILES\${MyAppName}"
InstallDirRegKey HKCU "Software\${MyAppName}" ""

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "resources\license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Installer section
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

  ; Write registry keys
  WriteRegStr HKCU "Software\${MyAppName}" "" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "DisplayName" "${MyAppName} ${MyAppVersion}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "DisplayVersion" "${MyAppVersion}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "Publisher" "${MyAppPublisher}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}" "URLInfoAbout" "${MyAppURL}"
SectionEnd

; Uninstaller section
Section "Uninstall"
  ; Remove shortcuts
  Delete "$SMPROGRAMS\${MyAppName}\${MyAppName}.lnk"
  Delete "$SMPROGRAMS\${MyAppName}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${MyAppName}"
  Delete "$DESKTOP\${MyAppName}.lnk"

  ; Remove executable
  Delete "$INSTDIR\${MyAppExeName}"
  Delete "$INSTDIR\uninstall.exe"
  RMDir "$INSTDIR"

  ; Remove registry keys
  DeleteRegKey HKCU "Software\${MyAppName}"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MyAppName}"
SectionEnd
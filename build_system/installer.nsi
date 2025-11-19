; NSIS installer for Digital Workshop
; Usage: makensis /DAPP_NAME="Digital Workshop" /DAPP_EXE="Digital Workshop.exe" /DDIST_DIR="..\dist" /DOUTFILE="..\dist\DigitalWorkshop-Setup.exe" installer.nsi

!ifndef APP_NAME
!define APP_NAME "Digital Workshop"
!endif

!ifndef APP_EXE
!define APP_EXE "Digital Workshop.exe"
!endif

!ifndef DIST_DIR
!define DIST_DIR "..\dist"
!endif

!ifndef OUTFILE
!define OUTFILE "..\dist\DigitalWorkshop-Setup.exe"
!endif

!ifndef INSTALL_DIR
!define INSTALL_DIR "$PROGRAMFILES64\${APP_NAME}"
!endif

OutFile "${OUTFILE}"
InstallDir "${INSTALL_DIR}"
RequestExecutionLevel admin
SetCompress auto

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "${DIST_DIR}\${APP_EXE}"

  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\${APP_EXE}"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  RMDir "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd

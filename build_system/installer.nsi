; NSIS installer for Digital Workshop
; Usage: makensis /DAPP_NAME="Digital Workshop" /DAPP_EXE="Digital Workshop.exe" /DAPP_DIR="..\dist\Digital Workshop" /DDIST_DIR="..\dist" /DOUTFILE="..\dist\DigitalWorkshop-Setup.exe" installer.nsi

!ifndef APP_NAME
!define APP_NAME "Digital Workshop"
!endif

!ifndef APP_EXE
!define APP_EXE "Digital Workshop.exe"
!endif

!ifndef APP_DIR
!define APP_DIR "..\dist\${APP_NAME}"
endif

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
  File /r "${APP_DIR}\*.*"

  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd

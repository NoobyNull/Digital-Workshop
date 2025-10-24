!include "MUI2.nsh"

Name "Digital Workshop"

OutFile "Digital Workshop-Setup-1.0.0.exe"

InstallDir "$PROGRAMFILES\Digital Workshop"

Page directory

Page instfiles

Section

  SetOutPath $INSTDIR

  File "dist\Digital Workshop.exe"

  CreateShortcut "$DESKTOP\Digital Workshop.lnk" "$INSTDIR\Digital Workshop.exe"

  CreateShortcut "$SMPROGRAMS\Digital Workshop.lnk" "$INSTDIR\Digital Workshop.exe"

SectionEnd
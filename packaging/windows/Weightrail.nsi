Unicode True

!ifndef VERSION
  !define VERSION "0.3.1"
!endif
!ifndef SOURCE_DIR
  !define SOURCE_DIR "build-windows"
!endif
!ifndef OUTPUT_DIR
  !define OUTPUT_DIR "dist-windows"
!endif

Name "Weightrail ${VERSION}"
OutFile "${OUTPUT_DIR}\Weightrail-${VERSION}-windows-x86_64.exe"
InstallDir "$LOCALAPPDATA\Programs\Weightrail"
RequestExecutionLevel user
SetCompressor /SOLID lzma

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1033 "ProductName" "Weightrail"
VIAddVersionKey /LANG=1033 "FileDescription" "Weightrail installer"
VIAddVersionKey /LANG=1033 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1033 "ProductVersion" "${VERSION}"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Weightrail" SEC_MAIN
  SetOutPath "$INSTDIR"
  File "${SOURCE_DIR}\Weightrail.exe"
  File "${SOURCE_DIR}\Weightrail-CLI.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateDirectory "$SMPROGRAMS\Weightrail"
  CreateShortcut "$SMPROGRAMS\Weightrail\Weightrail.lnk" "$INSTDIR\Weightrail.exe"
  CreateShortcut "$SMPROGRAMS\Weightrail\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\Weightrail.lnk" "$INSTDIR\Weightrail.exe"

  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Weightrail" "DisplayName" "Weightrail"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Weightrail" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Weightrail" "Publisher" "SleepyMario"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Weightrail" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Weightrail" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Weightrail" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Weightrail.lnk"
  Delete "$SMPROGRAMS\Weightrail\Weightrail.lnk"
  Delete "$SMPROGRAMS\Weightrail\Uninstall.lnk"
  RMDir "$SMPROGRAMS\Weightrail"
  Delete "$INSTDIR\Weightrail.exe"
  Delete "$INSTDIR\Weightrail-CLI.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Weightrail"
SectionEnd

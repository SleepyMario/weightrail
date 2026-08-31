# Windows package

The Windows release is built on Windows and contains two self-contained
executables:

- `Weightrail.exe`: native desktop interface.
- `Weightrail-CLI.exe`: command-line interface.

Neither executable requires a separate Python installation. User data is kept
outside the installation directory at `%LOCALAPPDATA%\weightrail\weights.sqlite`,
so upgrades and uninstallation do not remove measurements.

From PowerShell with Python 3.11 or newer and NSIS available:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
```

The final installer and portable ZIP are written to `dist-windows`. The build
script creates an isolated virtual environment, installs only declared build
requirements, runs the complete test suite, builds both executables, performs
CLI smoke tests, and invokes NSIS.

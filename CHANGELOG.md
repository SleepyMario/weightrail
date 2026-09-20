# Changelog

## 0.3.1 - 2026-09-20

- Define Docker, Debian/Ubuntu, Gentoo, and Windows as the maintained package
  targets, and retire the unfinished RPM, Arch, Flatpak, and Snap candidates.
- Build Debian packages in a disposable Ubuntu 24.04 container instead of
  requiring Debian packaging tools on the Gentoo build worker.
- Pin and validate the Docker base image and record the application version and
  source revision in the resulting image metadata.
- Validate the Windows installer and portable package from the same source
  version used by the Linux build worker.

## 0.3.0 - 2026-08-31

- Add an expanding Matplotlib weight-history chart to the GTK 3 GUI, including
  an empty state, real calendar spacing, measurement markers, and a linear
  trend line.
- Keep Matplotlib optional for CLI-only installations and update GUI-enabled
  distribution packaging.
- Add shared, shape-preserving ISO-weekly and monthly-mean trends to the
  terminal and GTK charts. Delay each until its second represented period is
  complete, then draw it retroactively from the first represented period.
- Recognize `weightrail graph` as a graph-only CLI command, exit the GTK main
  loop cleanly on Ctrl+C, and add session-only GUI line visibility controls.
- Modernize the GTK interface with a native header, theme-aware card styling,
  touch-friendly controls, a more prominent graph, and quieter recent entries.
- Add a Windows-native desktop frontend and reproducible PyInstaller/NSIS
  packaging while keeping the same local database and statistics core.

## 0.2.0 - 2026-07-13

- Rename the project, distribution, import package, and command to Weightrail.
- Move default data to the Weightrail XDG data directory with a safe one-time
  copy from the former default path.
- Make terminal graph support optional when `plotext` is unavailable.
- Update source, Gentoo, Docker, documentation, tests, and release tooling
  for the canonical identity.

## 0.1.0 - 2026-07-05

Initial release.

- Local SQLite storage.
- Positional daily weight entry.
- Asia/Taipei date defaults.
- CSV import from `date,weight_kg` files.
- Terminal graph rendering with `plotext`.
- Linear-regression trend summary with NumPy.
- Alternate database paths with `--db-path`.
- Clear error handling for invalid weights, malformed CSV files, and corrupt SQLite databases.
- Gentoo packaging skeleton for `app-misc/weight-tracker-cli`.

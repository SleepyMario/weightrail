# Changelog

## 0.2.0 - 2026-07-13

- Rename the project, distribution, import package, and command to Weightrail.
- Move default data to the Weightrail XDG data directory with a safe one-time
  copy from the former default path.
- Make terminal graph support optional when `plotext` is unavailable.
- Update source, RPM, Gentoo, Docker, documentation, tests, and release tooling
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

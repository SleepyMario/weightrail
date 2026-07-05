# Changelog

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

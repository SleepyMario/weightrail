# weight-tracker-cli

`weight-tracker-cli` is a small, local-first command-line weight tracker.

It stores measurements in a local SQLite database, prints recorded rows, draws a terminal chart, and reports a simple linear trend summary. No account is required, no network service is used, and missing dates stay missing instead of being filled or interpolated automatically.

## Features

- Daily weight recording from the terminal.
- `Asia/Taipei` date default for positional entries.
- CSV import for seed or migrated data.
- Full record display in date order.
- Terminal chart using `plotext`.
- Linear trend summary using NumPy.
- Alternate database paths with `--db-path`.
- Local SQLite storage.

## Installation

### Development or source installation

```bash
git clone git@github.com:SleepyMario/weight-tracker-cli.git
cd weight-tracker-cli
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

From an already checked-out source tree:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

### Editable development installation

```bash
python -m pip install -e .
```

For test and build tools:

```bash
python -m pip install -e ".[dev]"
```

### pipx

Install directly from GitHub with `pipx`:

```bash
pipx install git+https://github.com/SleepyMario/weight-tracker-cli.git
```

From a local checkout:

```bash
pipx install .
```

### Gentoo

An ebuild skeleton is present at:

```text
gentoo/app-misc/weight-tracker-cli/weight-tracker-cli-0.1.0.ebuild
```

Current Gentoo status:

- The ebuild is prepared for `app-misc/weight-tracker-cli`.
- It depends on `dev-python/numpy` and `dev-python/plotext`.
- On this machine, `dev-python/plotext` is available through Guru.
- Systems without Guru may need Guru enabled or a local `plotext` ebuild.
- The versioned ebuild uses the GitHub release tarball after the release is published.
- `Manifest` must be regenerated with Gentoo tooling after release assets exist.

## Usage

```bash
weight-tracker --help
weight-tracker --version
weight-tracker 122.8
weight-tracker --show
weight-tracker --summary
weight-tracker --import data/seed.csv
weight-tracker --db-path /path/to/weights.sqlite --show
```

A positional weight records or updates the current `Asia/Taipei` date:

```bash
weight-tracker 122.8
```

After adding or updating the row, the command prints the full table, graph, and trend summary.

## Date Behaviour

When you pass a positional weight, the CLI uses the current date in:

```text
Asia/Taipei
```

The date is stored as `YYYY-MM-DD`. If a row already exists for that date, the existing row is updated. Duplicate rows for the same date are not created.

Imported CSV dates are used exactly as supplied after `YYYY-MM-DD` validation.

## Database

The default database path is:

```text
~/.local/share/weight-tracker-cli/weights.sqlite
```

Parent directories are created automatically when the database is opened.

Use an alternate path with:

```bash
weight-tracker --db-path /path/to/weights.sqlite --show
```

Back up the database by copying the SQLite file:

```bash
cp ~/.local/share/weight-tracker-cli/weights.sqlite weights.sqlite.backup
```

Deleting the database file deletes the recorded data. The CLI will create a new empty database the next time it runs.

## CSV Format

The importer requires this exact header:

```csv
date,weight_kg
2026-06-20,122.8
2026-06-21,121.8
```

Rules:

- `date` must use `YYYY-MM-DD`.
- `weight_kg` must be a positive decimal number.
- Blank rows are ignored.
- Duplicate dates update the existing row; the later imported row wins.
- The importer parses and validates all rows before writing, so malformed dates or weights leave the database unchanged.
- Missing required columns fail with a clear error.

## Summary Calculation

The summary uses NumPy linear regression over recorded measurements only. Missing dates are not filled in.

The output includes:

- first date;
- latest date;
- number of measurements;
- start weight;
- latest weight;
- net change;
- slope in kg/day;
- slope in kg/week;
- approximate equation `w(d) ≈ md + b`, where `d` is days since the first recorded entry.

This is a simple numerical trend summary, not a medical prediction.

## Errors

Common errors are reported with a nonzero exit status:

- invalid weight values, including zero and negative values;
- missing CSV files;
- malformed CSV headers or rows;
- unwritable database locations;
- corrupt SQLite database files.

## Privacy

- All data is local.
- No telemetry is collected.
- Nothing is uploaded automatically.
- No remote service is contacted by the application.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
python -m build
```

The release helper runs the local validation flow:

```bash
scripts/check-release.sh
```

It builds artifacts and smoke-tests them in temporary virtual environments. It does not push, publish, tag, or touch the real default database.

## Release Process

See [docs/RELEASING.md](docs/RELEASING.md) for the local release checklist.

## GitHub Setup

The public repository is:

```text
https://github.com/SleepyMario/weight-tracker-cli
```

The configured SSH remote should be:

```bash
git remote add origin git@github.com:SleepyMario/weight-tracker-cli.git
git push -u origin main
git push origin v0.1.0
```

## Licence

MIT. See [LICENSE](LICENSE).

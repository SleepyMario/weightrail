# Weightrail

`weightrail` is a small, local-first command-line weight tracker.

It stores measurements in a local SQLite database, prints recorded rows, draws a terminal chart, and reports a simple linear trend summary. No account is required, no network service is used, and missing dates stay missing instead of being filled or interpolated automatically.

## Features

- Daily weight recording from the terminal.
- `Asia/Taipei` date default for positional entries.
- CSV import for seed or migrated data.
- Full record display in date order.
- Terminal chart using optional `plotext`.
- Basic plain-text statistics.
- Linear trend summary using NumPy.
- Optional GTK Linux GUI with a graphical measurement and trend chart.
- Alternate database paths with `--db-path`.
- Local SQLite storage.

## Installation

### Development or source installation

```bash
git clone git@github.com:SleepyMario/weightrail.git
cd weightrail
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

For the optional GTK Linux GUI:

```bash
python -m pip install -e ".[gui]"
```

The `gui` extra installs PyGObject and Matplotlib; GTK 3 itself is normally
installed through the Linux distribution's package manager. CLI-only installs
do not pull in Matplotlib. If the GUI dependencies are absent,
`weightrail-gui` reports the missing requirement and exits cleanly.

### pipx

Install directly from GitHub with `pipx`:

```bash
pipx install git+https://github.com/SleepyMario/weightrail.git
```

From a local checkout:

```bash
pipx install .
```

### Ubuntu and Debian package (local build)

Weightrail has an initial Debian package definition for locally built packages;
it is not published in the Ubuntu or Debian archives. Build it with normal
Debian tooling, then install the resulting artifact:

```bash
sudo apt install ./weightrail_0.2.0-1_all.deb \
  ./weightrail-gui_0.2.0-1_all.deb
```

The base package installs `/usr/bin/weightrail`. Install the separate
`weightrail-gui` package for the GTK launcher and its GTK/Matplotlib
dependencies. Upgrading either package does not change existing records.
Removing or purging the packages does not delete user data, which remains at
`~/.local/share/weightrail/weights.sqlite` by default.

This package is currently intended for local validation and distribution; it
does not imply archive inclusion. Ubuntu 26.04 does not package `plotext`, so
terminal graphs show a clear availability message unless that optional
dependency is supplied by the user outside the Debian package.

### Docker

The published Docker image is CLI-only, targets Linux amd64, and runs
`weightrail` as its entry point. Pull either the fixed version or the current
latest tag from Docker Hub:

```bash
docker pull sleepiestmario/weightrail:0.2.0
docker pull sleepiestmario/weightrail:latest
```

Mount a host directory at `/data` and select the database file with
`--db-path` to keep measurements between container runs:

```bash
mkdir -p data
docker run --rm -v "$PWD/data:/data" sleepiestmario/weightrail:latest \
  --db-path /data/weights.sqlite stats
```

The final image runs as non-root UID/GID 1000, and the mounted directory must
be writable by that identity. The image contains NumPy and SQLite support but
does not include GTK or the optional `plotext` graph dependency. Commands that
would draw a graph instead report that `plotext` is unavailable; statistics
and summaries remain fully functional.

### Additional Linux packaging candidates

Local, validated packaging instructions are available for
[Arch Linux/AUR](packaging/arch/README.md),
[Flatpak](packaging/flatpak/README.md), and [Snap](packaging/snap/README.md).
These candidates are not published to AUR, Flathub, or the Snap Store.

### Gentoo

An ebuild skeleton is present at:

```text
gentoo/app-misc/weightrail/weightrail-0.2.0.ebuild
```

Current Gentoo status:

- The ebuild is prepared for `app-misc/weightrail`.
- It always depends on `dev-python/numpy`.
- Its default-enabled `graph` USE flag installs `dev-python/plotext`.
- Its optional `gui` USE flag installs GTK 3, PyGObject, and
  `dev-python/matplotlib[gtk3]`.
- On this machine, `dev-python/plotext` is available through Guru.
- Systems without Guru may need Guru enabled or a local `plotext` ebuild.
- The versioned ebuild uses the GitHub v0.2.0 tag archive.
- `Manifest` records the validated release archive hashes.

## Usage

```bash
weightrail --help
weightrail --version
weightrail 122.8
weightrail stats
weightrail graph
weightrail --show
weightrail --stats
weightrail --summary
weightrail --import data/seed.csv
weightrail --db-path /path/to/weights.sqlite --show
weightrail-gui
```

A positional weight records or updates the current `Asia/Taipei` date:

```bash
weightrail 122.8
```

After adding or updating the row, the command prints the full table, graph, and trend summary.

Show the basic stats without the graph:

```bash
weightrail stats
```

Show only the terminal graph and its legend:

```bash
weightrail graph
```

Launch the small GTK frontend:

```bash
weightrail-gui
```

The GUI displays the same statistics and recent entries as the CLI-backed
database, plus a graphical history chart. Measurements use their actual dates
on the x-axis, and two or more measurements add a dashed linear trend line.
Both graphical and terminal charts also show conservative smoothed weekly and
monthly trends. Each trend remains hidden until its second represented period
reaches its final day, then appears retroactively from the first represented
period. Weekly means use ISO Monday-through-Sunday weeks and completed periods
are placed on Sunday; completed monthly means are placed at calendar
month-end. An eligible incomplete current period stops at its latest recorded
date. The GUI chart refreshes after every record or same-day replacement.
Its compact, collapsed `Lines` control can show or hide measurements and the
linear, weekly, and monthly trends for the current GUI session. Lines become
enabled and selected automatically when enough data makes them available;
lines explicitly hidden by the user stay hidden across ordinary refreshes.

The CLI and GUI use the same SQLite database by default. The GUI also accepts an alternate database path:

```bash
weightrail-gui --db-path /path/to/weights.sqlite
```

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
~/.local/share/weightrail/weights.sqlite
```

Parent directories are created automatically when the database is opened.

On the first default-path startup after upgrading from the former project name,
Weightrail atomically copies
`~/.local/share/weight-tracker-cli/weights.sqlite` to the new location when the
legacy file is present and the new file is absent. The legacy file remains
untouched as a rollback copy. If the new database already exists, it always
wins. Explicit `--db-path` values are never migrated.

Use an alternate path with:

```bash
weightrail --db-path /path/to/weights.sqlite --show
```

Back up the database by copying the SQLite file:

```bash
cp ~/.local/share/weightrail/weights.sqlite weights.sqlite.backup
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

`weightrail stats` reports:

- entry count;
- first and latest entry dates;
- latest weight;
- change since the previous entry;
- total change since the first entry;
- 7-day and 30-day averages when at least two entries exist in the window;
- highest and lowest recorded weights;
- missing days between the first and latest entry;
- simple trend slope in kg/day and kg/week.

`weightrail --summary` keeps the older linear-regression-focused output. The summary uses NumPy linear regression over recorded measurements only. Missing dates are not filled in.

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
https://github.com/SleepyMario/weightrail
```

The configured SSH remote should be:

```bash
git remote add origin git@github.com:SleepyMario/weightrail.git
git push -u origin main
git push origin v0.2.0
```

## Licence

MIT. See [LICENSE](LICENSE).

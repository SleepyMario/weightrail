# weight-tracker-cli

Simple SQLite-backed terminal weight tracker.

The CLI stores daily weight measurements, prints a table, renders a terminal graph with `plotext`, and summarizes the linear trend with `numpy`.

## Features

- SQLite primary data store.
- Default database path: `~/.local/share/weight-tracker-cli/weights.sqlite`.
- CLI command: `weight-tracker`.
- Uses the Asia/Taipei local date by default when adding today's weight.
- Missing dates are absent rows. They are not blank rows and are not interpolated.
- Imports seed data from CSV.
- No pandas dependency.

## Install For Development

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

## Usage

Add or update today's Asia/Taipei weight, then print the table, graph, and trend:

```sh
weight-tracker 123.4
```

Show all recorded data:

```sh
weight-tracker --show
```

Print only the numeric summary and trend:

```sh
weight-tracker --summary
```

Import seed data:

```sh
weight-tracker --import data/seed.csv
```

Use a custom database:

```sh
weight-tracker --db-path /path/to/weights.sqlite --show
```

## CSV Format

```csv
date,weight_kg
2026-07-05,123.4
```

Dates must use `YYYY-MM-DD`. Weights must be positive numbers.

## Trend Output

The summary includes:

- first date;
- latest date;
- number of measurements;
- start weight;
- latest weight;
- net change;
- slope in kg/day;
- slope in kg/week;
- approximate equation `w(d) ≈ md + b`, where `d` is days since the first recorded entry.

Missing days are ignored by the regression. Only recorded measurements are used.

## Gentoo

An example ebuild is included at:

```text
gentoo/app-misc/weight-tracker-cli/weight-tracker-cli-0.1.0.ebuild
```

It assumes these runtime dependencies:

- `dev-python/numpy`
- `dev-python/plotext`

On this system, `dev-python/plotext` is available from the Guru repository. If `dev-python/plotext` is unavailable in your enabled Gentoo repositories, a local overlay ebuild for `plotext` may be required.

## GitHub Setup

This directory is ready to become a separate public GitHub repository:

```sh
git init
git add .
git commit -m "Initial weight tracker CLI"
git branch -M main
git remote add origin git@github.com:<USER>/weight-tracker-cli.git
git push -u origin main
```

Do not push until you have created the remote repository and configured credentials.

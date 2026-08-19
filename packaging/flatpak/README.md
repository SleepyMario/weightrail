# Local Flatpak candidate

This directory contains a local-only Flatpak candidate for Weightrail 0.2.0.
It has not been submitted to Flathub or published as a repository or bundle.

The application ID is `io.github.SleepyMario.weightrail`. The primary command
is the GTK 3 application `weightrail-gui`; the same Flatpak also installs the
CLI as `weightrail`.

## Runtime and dependencies

The manifest targets `org.gnome.Platform` and `org.gnome.Sdk` branch 50. In the
validated Flathub environment, branch 50 was the newest stable GNOME branch,
while branch 48 was explicitly marked end-of-life. The runtime supplies Python
3.13, GTK 3, and PyGObject. It does not supply NumPy or Matplotlib, so
checksum-pinned NumPy 2.5.1 and Matplotlib 3.10.5 (with its Python
dependencies) are built from source with pinned meson-python build support.
Build-only Python tooling is removed from the final application.

The optional `plotext` dependency is not bundled. CLI operations that would
draw a graph report the upstream availability message; statistics and trend
summaries remain available.

## Containerized build

Validation uses this established Flathub CI builder image by immutable digest:

```text
ghcr.io/flathub-infra/flatpak-github-actions:gnome-50@sha256:b270d0044182e436c872e4450815fe7de7e2730bf6d238ad35a3f5469b3c4871
```

Nested bubblewrap requires a privileged disposable Docker container on the
validated host. Host sudo and host Flatpak installations or remotes are not
used. Create an unprivileged user inside the container and run
`flatpak-builder` as that user.

Prepare downloads while the container is online, then disconnect its network
and build with downloads disabled:

```bash
flatpak-builder --download-only --disable-rofiles-fuse \
  --state-dir=packaging/flatpak/out/state \
  packaging/flatpak/out/build \
  packaging/flatpak/io.github.SleepyMario.weightrail.yml

flatpak-builder --force-clean --disable-download --disable-rofiles-fuse \
  --user --default-branch=stable \
  --state-dir=packaging/flatpak/out/state \
  --repo=packaging/flatpak/out/repo \
  packaging/flatpak/out/build \
  packaging/flatpak/io.github.SleepyMario.weightrail.yml
```

The pinned builder image already contains the branch 50 runtime and SDK. If a
different clean image is used, install those refs from Flathub before the
download-only step. Do not leave `--install-deps-from=flathub` on the offline
build command.

Create the unsigned local bundle:

```bash
flatpak build-bundle packaging/flatpak/out/repo \
  packaging/flatpak/out/io.github.SleepyMario.weightrail-0.2.0.flatpak \
  io.github.SleepyMario.weightrail stable
```

## Local installation and validation

Use an isolated user home or a second clean disposable container:

```bash
flatpak install --user --noninteractive \
  packaging/flatpak/out/io.github.SleepyMario.weightrail-0.2.0.flatpak
flatpak info io.github.SleepyMario.weightrail
flatpak info --show-permissions io.github.SleepyMario.weightrail
flatpak run io.github.SleepyMario.weightrail
flatpak run --command=weightrail io.github.SleepyMario.weightrail --version
flatpak uninstall --user --noninteractive io.github.SleepyMario.weightrail
flatpak uninstall --user --delete-data --noninteractive io.github.SleepyMario.weightrail
```

The only finish permissions are Wayland, fallback X11, and shared IPC. There
is no network, host filesystem, home, device, or bus permission. The default
database is private to the application at:

```text
~/.var/app/io.github.SleepyMario.weightrail/data/weightrail/weights.sqlite
```

The Flatpak intentionally cannot see the legacy host database. A future host
import or migration feature should use a portal or explicitly selected file,
not broad home-directory access.

The local validation installed the bundle in a second networkless container.
The CLI help, version, record, show, stats, and summary operations succeeded;
the optional graph reported that `plotext` was unavailable. A GTK window
initialized under Xvfb, opened the private database, and remained running until
it was intentionally terminated. Ordinary uninstall preserved the private
data, reinstall recovered it, and uninstall with `--delete-data` removed it.

`appstreamcli`, `desktop-file-validate`, and the manifest linter passed. The
Flathub build-directory and repository lints report missing screenshots. That
is acceptable for this local candidate but must be addressed and reviewed
before any public submission.

## Public-submission limitations

The SVG icon is original but provisional and needs human design review before
any store submission. A future public submission also requires separate human
review of desktop presentation, AppStream metadata, runtime choice, dependency
source policy, permissions, screenshots, and then-current Flathub requirements.
This local validation does not claim that the package is Flathub-ready, and no
Flathub repository or submission was created.

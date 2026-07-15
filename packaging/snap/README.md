# Local Snap candidate

This directory contains the local-only Snap candidate for Weightrail 0.2.0.
It has not been registered, uploaded, or published to the Snap Store.

The Snap is named `weightrail`, uses `core24`, `grade: devel`, and strict
confinement, and is built and tested only for amd64. It exposes the CLI as
`weightrail` and the GTK application as `weightrail.weightrail-gui`.

## Build

The validated build used Snapcraft 8.11.1 from Canonical's core24 Snapcraft
rock, pinned for amd64 as:

```text
ghcr.io/canonical/snapcraft:8_core24@sha256:615b979408f55a4c7839d13f49e39bc3c01185417026a28c30917f6d1652e861
```

The build ran in a disposable privileged container because Snapcraft's
destructive-mode lifecycle needs mount and namespace operations. Source files
were edited only by the normal host user. A representative clean build is:

```sh
docker run --rm --privileged \
  -v "$PWD/packaging/snap:/project" \
  -w /project \
  --entrypoint sh \
  ghcr.io/canonical/snapcraft:8_core24@sha256:615b979408f55a4c7839d13f49e39bc3c01185417026a28c30917f6d1652e861 \
  -lc 'apt-get update && snapcraft clean --destructive-mode && snapcraft pack --destructive-mode --platform amd64'
```

Move the resulting `weightrail_0.2.0_amd64.snap` to `out/`. The manifest uses
the immutable v0.2.0 GitHub archive and verifies SHA-256
`68d67f7f7b071ba2ff5dcd63bb4fbaefc5c2aafb0c35a2e9442e0c88812164b9`.

## Dependencies and desktop integration

The Python plugin installs Weightrail and pins NumPy to 2.5.1. GTK 3 and
PyGObject come from the Ubuntu core24 packages `libgtk-3-0t64`,
`gir1.2-gtk-3.0`, and `python3-gi`. Plotext is intentionally omitted; the CLI
prints its normal optional-graph message.

The GNOME extension was expanded and audited during validation. It adds theme,
platform, GPU content snaps, command chains, and additional desktop plumbing.
The candidate instead uses a manual GTK integration with only `desktop`,
`desktop-legacy`, `wayland`, and `x11`. It requests no network, home, device,
observation, removable-media, or system-service interface.

The desktop file and original SVG icon are under `snap/gui/`. The icon is
provisional and requires human design review before any store submission.

## Install and run

Install the unsigned local artifact in a disposable Ubuntu 24.04 test system
with functioning snapd and AppArmor:

```sh
sudo snap install out/weightrail_0.2.0_amd64.snap --dangerous
weightrail --help
weightrail --version
weightrail.weightrail-gui --help
```

Do not use `--devmode`; the candidate is designed for strict confinement. The
GUI was smoke-tested under Xvfb in an Ubuntu 24.04 VM with AppArmor enforcing.

`XDG_DATA_HOME` is set to `$SNAP_USER_COMMON/.local/share`, so the default
database is revision-independent at:

```text
$SNAP_USER_COMMON/.local/share/weightrail/weights.sqlite
```

The Snap does not have access to ordinary home files and does not migrate the
legacy host database. A future explicit import workflow is required for host
data migration.

Inspect and remove the candidate with:

```sh
snap info --verbose weightrail
snap connections weightrail
sudo snap remove weightrail
snap saved
sudo snap remove weightrail --purge
```

Ordinary removal may create an automatic data snapshot. Use `snap forget ID`
only for the Weightrail snapshot if it must also be deleted.

## Validation status and public-release limits

The local artifact passed CLI, database persistence, GTK/PyGObject import,
Xvfb launch, read-only payload, AppArmor home denial, network denial,
snapshot/restore, uninstall, and purge checks. Snapcraft's pack-time classic
and library linters ran. Four GTK-stack libraries were conservatively retained
despite unused-library warnings because they support dynamic GTK, Pango,
GObject, and internationalization code paths.

Before a future Snap Store submission, separately review the provisional icon
and desktop presentation, store metadata, dependency-source policy,
interfaces, confinement behavior, current Snap Store requirements, and a
store-grade build (`grade: stable` only after approval). No store registration
or upload was performed here.

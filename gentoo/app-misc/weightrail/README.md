# Gentoo Packaging Notes

This directory contains a preparation ebuild for:

```text
app-misc/weightrail
```

The ebuild targets the public `v0.2.0` GitHub release archive:

```text
https://github.com/SleepyMario/weightrail/archive/refs/tags/v0.2.0.tar.gz
```

The current `Manifest` was generated from the locally validated deterministic
`weightrail-0.2.0.tar.gz`. Regenerate it against the eventual published v0.2.0
archive if that artifact differs, then run a clean emerge test in a Gentoo
environment before using the ebuild in a real overlay.

Dependencies:

- `dev-python/numpy`
- `dev-python/plotext` with the default-enabled `graph` USE flag
- `dev-python/matplotlib[gtk3]`, `dev-python/pygobject`, and GTK 3 with the
  optional `gui` USE flag

On this machine, `dev-python/plotext` is available from Guru. Systems without Guru may need Guru enabled or a local `dev-python/plotext` ebuild.

Enable the graphical application with:

```text
app-misc/weightrail gui
```

# Gentoo Packaging Notes

This directory contains a preparation ebuild for:

```text
app-misc/weightrail
```

The current ebuild targets the public `v0.3.0` GitHub release archive:

```text
https://github.com/SleepyMario/weightrail/archive/refs/tags/v0.3.0.tar.gz
```

The `Manifest` must match the final published `v0.3.0` tag archive. Run a clean
emerge test in a Gentoo environment before installing the versioned package.

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

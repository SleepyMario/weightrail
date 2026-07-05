# Gentoo Packaging Notes

This directory contains a preparation ebuild for:

```text
app-misc/weight-tracker-cli
```

The ebuild targets the public `v0.1.0` GitHub release archive:

```text
https://github.com/SleepyMario/weight-tracker-cli/archive/refs/tags/v0.1.0.tar.gz
```

Before using the ebuild in a real overlay, regenerate `Manifest` with Gentoo tooling and run a clean emerge test in a Gentoo environment.

Dependencies:

- `dev-python/numpy`
- `dev-python/plotext`

On this machine, `dev-python/plotext` is available from Guru. Systems without Guru may need Guru enabled or a local `dev-python/plotext` ebuild.

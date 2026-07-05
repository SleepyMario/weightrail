# Gentoo Packaging Notes

This directory contains a preparation ebuild for:

```text
app-misc/weight-tracker-cli
```

The ebuild is not fully release-testable yet because this repository has no configured public remote and no published `v0.1.0` release archive.

Before using the ebuild in a real overlay:

1. Create the public repository.
2. Push the `v0.1.0` tag.
3. Create or identify the final release archive URL.
4. Replace the placeholder `SRC_URI` comment in `weight-tracker-cli-0.1.0.ebuild` with the real URL.
5. Regenerate `Manifest`.

Dependencies:

- `dev-python/numpy`
- `dev-python/plotext`

On this machine, `dev-python/plotext` is available from Guru. Systems without Guru may need Guru enabled or a local `dev-python/plotext` ebuild.

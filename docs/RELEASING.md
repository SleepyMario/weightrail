# Releasing

This project is prepared for local release validation and GitHub release publication at:

```text
https://github.com/SleepyMario/weightrail
```

Do not publish to PyPI unless that is requested separately.

## Local Release Checklist

1. Ensure the Git worktree is clean:

   ```bash
   git status --short
   ```

2. Run tests:

   ```bash
   python -m pytest
   ```

3. Remove old build artifacts and build source and wheel distributions:

   ```bash
   rm -rf dist build *.egg-info src/*.egg-info
   python -m build
   ```

4. Validate package metadata:

   ```bash
   python -m twine check dist/*
   ```

5. Install and test the wheel in a clean virtual environment:

   ```bash
   python -m venv /tmp/weightrail-wheel-test
   /tmp/weightrail-wheel-test/bin/python -m pip install dist/weightrail-0.3.1-py3-none-any.whl
   /tmp/weightrail-wheel-test/bin/weightrail --version
   /tmp/weightrail-wheel-test/bin/weightrail --db-path /tmp/wheel-weights.sqlite 123.4
   /tmp/weightrail-wheel-test/bin/weightrail --db-path /tmp/wheel-weights.sqlite --show
   /tmp/weightrail-wheel-test/bin/weightrail --db-path /tmp/wheel-weights.sqlite --summary
   ```

6. Install and test the source distribution in a separate clean virtual environment:

   ```bash
   python -m venv /tmp/weightrail-sdist-test
   /tmp/weightrail-sdist-test/bin/python -m pip install dist/weightrail-0.3.1.tar.gz
   /tmp/weightrail-sdist-test/bin/weightrail --version
   /tmp/weightrail-sdist-test/bin/weightrail --db-path /tmp/sdist-weights.sqlite 123.4
   /tmp/weightrail-sdist-test/bin/weightrail --db-path /tmp/sdist-weights.sqlite --summary
   ```

7. Review archive contents:

   ```bash
   tar -tzf dist/weightrail-0.3.1.tar.gz
   python -m zipfile -l dist/weightrail-0.3.1-py3-none-any.whl
   ```

8. Create the local annotated tag:

   ```bash
   git tag -a v0.3.1 -m "weightrail 0.3.1"
   ```

9. Push commit and tag:

   ```bash
   git push -u origin main
   git push origin v0.3.1
   ```

10. Create a GitHub release and upload `dist/weightrail-0.3.1.tar.gz`, `dist/weightrail-0.3.1-py3-none-any.whl`, and `dist/SHA256SUMS`.

11. Update the Gentoo ebuild `SRC_URI` and regenerate `Manifest` after the final release archive URL exists.

12. Build Debian packages in the canonical Ubuntu 24.04 environment:

   ```bash
   scripts/build-deb-container.sh
   ```

   The disposable container installs the Debian build dependencies, runs the
   package tests through `dpkg-buildpackage`, and writes artifacts under
   `dist/debian/` by default. The Gentoo build VM does not need host-installed
   Debian packaging tools.

## Helper Script

The local helper script runs the validation flow without publishing:

```bash
scripts/check-release.sh
```

Run it from a dedicated build virtual environment. It refreshes that
environment's editable Weightrail installation before testing so stale package
metadata cannot supply an older version number. It does not tag, push, publish,
require root, or touch the default user database.

# Releasing

This project is prepared for local release validation. Do not push, publish, upload release artifacts, or create a remote release unless that is requested separately.

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
   python -m venv /tmp/weight-tracker-wheel-test
   /tmp/weight-tracker-wheel-test/bin/python -m pip install dist/weight_tracker_cli-0.1.0-py3-none-any.whl
   /tmp/weight-tracker-wheel-test/bin/weight-tracker --version
   /tmp/weight-tracker-wheel-test/bin/weight-tracker --db-path /tmp/wheel-weights.sqlite 123.4
   /tmp/weight-tracker-wheel-test/bin/weight-tracker --db-path /tmp/wheel-weights.sqlite --show
   /tmp/weight-tracker-wheel-test/bin/weight-tracker --db-path /tmp/wheel-weights.sqlite --summary
   ```

6. Install and test the source distribution in a separate clean virtual environment:

   ```bash
   python -m venv /tmp/weight-tracker-sdist-test
   /tmp/weight-tracker-sdist-test/bin/python -m pip install dist/weight_tracker_cli-0.1.0.tar.gz
   /tmp/weight-tracker-sdist-test/bin/weight-tracker --version
   /tmp/weight-tracker-sdist-test/bin/weight-tracker --db-path /tmp/sdist-weights.sqlite 123.4
   /tmp/weight-tracker-sdist-test/bin/weight-tracker --db-path /tmp/sdist-weights.sqlite --summary
   ```

7. Review archive contents:

   ```bash
   tar -tzf dist/weight_tracker_cli-0.1.0.tar.gz
   python -m zipfile -l dist/weight_tracker_cli-0.1.0-py3-none-any.whl
   ```

8. Create the local annotated tag:

   ```bash
   git tag -a v0.1.0 -m "weight-tracker-cli 0.1.0"
   ```

9. Push commit and tag only after a remote exists:

   ```bash
   git push -u origin main
   git push origin v0.1.0
   ```

10. Create a GitHub release or publish to PyPI only as a separate explicit action.

11. Update the Gentoo ebuild `SRC_URI` and regenerate `Manifest` after the final release archive URL exists.

## Helper Script

The local helper script runs the validation flow without publishing:

```bash
scripts/check-release.sh
```

It does not tag, push, publish, require root, or touch the default user database.

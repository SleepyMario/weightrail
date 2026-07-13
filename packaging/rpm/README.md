# RPM packaging

This directory contains the initial Fedora-family RPM definition for the
command-line application. The RPM, Python distribution, import package, and
command are all named `weightrail`; the default database path is
`~/.local/share/weightrail/weights.sqlite`.
The optional GTK command and module are not included.

## Dependencies

The build uses the standard Fedora pyproject macros with setuptools. Its build
requirements are `python3-devel`, `pyproject-rpm-macros`, setuptools 69 or
newer, wheel, pytest, and NumPy (generated from `pyproject.toml`). The installed
package requires Python and NumPy. `plotext` remains an optional upstream graph
extra and is not required by this RPM; without it, the CLI reports that the
terminal graph is unavailable.

Install all build requirements before starting the build. The source archive,
RPM build, `%check`, installation, and CLI do not need network access.

## Source archive

Create the source archive directly in the RPM source directory:

```bash
packaging/rpm/make-source.sh "$HOME/rpmbuild/SOURCES"
```

The helper copies only the application sources, tests, packaging definition,
licence, and relevant documentation. It excludes Git metadata, caches, virtual
environments, prior build output, distribution-specific packaging outside this
directory, sample data, and SQLite databases. Archive ordering, ownership,
timestamps, and gzip metadata are normalized. `SOURCE_DATE_EPOCH` may be set;
otherwise the timestamp of the current Git commit is used. The archive reflects
the current worktree, including intentional uncommitted application changes.

## Build and inspect

After installing the build dependencies, an unprivileged native build is:

```bash
rpmdev-setuptree
cp packaging/rpm/weightrail.spec "$HOME/rpmbuild/SPECS/"
packaging/rpm/make-source.sh "$HOME/rpmbuild/SOURCES"
rpmspec --parse "$HOME/rpmbuild/SPECS/weightrail.spec" >/dev/null
rpmbuild -ba "$HOME/rpmbuild/SPECS/weightrail.spec"
rpmlint "$HOME/rpmbuild/SRPMS/"*.src.rpm "$HOME/rpmbuild/RPMS/noarch/"*.rpm
rpm -qpi "$HOME/rpmbuild/RPMS/noarch/"*.rpm
rpm -qpl "$HOME/rpmbuild/RPMS/noarch/"*.rpm
```

Build dependencies must be installed before disconnecting from the network.
No command in the source, build, install, or check phases downloads anything.

## User data

The RPM owns no user data and has no removal script. Installing, upgrading,
reinstalling, or removing it does not inspect or delete the per-user SQLite
database. For validation, always set `HOME` and `--db-path` to a disposable
temporary directory; never run package tests against a real database.

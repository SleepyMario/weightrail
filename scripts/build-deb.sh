#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

version="$(python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
revision="${REVISION:-1}"
package_version="${version}-${revision}"
output="$root/dist-deb"
work="$(mktemp -d /tmp/weightrail-deb-build-XXXXXX)"
trap 'rm -rf "$work"' EXIT

wheel="$root/dist/weightrail-${version}-py3-none-any.whl"
[[ -f "$wheel" ]] || {
  printf 'Missing wheel: %s\nRun python -m build first.\n' "$wheel" >&2
  exit 1
}

rm -rf "$output"
mkdir -p "$output"

base="$work/weightrail"
gui="$work/weightrail-gui"
mkdir -p \
  "$base/DEBIAN" \
  "$base/usr/bin" \
  "$base/usr/lib/python3/dist-packages" \
  "$base/usr/share/doc/weightrail" \
  "$base/usr/share/man/man1" \
  "$gui/DEBIAN" \
  "$gui/usr/bin" \
  "$gui/usr/share/doc/weightrail-gui"

python -m zipfile -e "$wheel" "$base/usr/lib/python3/dist-packages"

cat >"$base/usr/bin/weightrail" <<'EOF'
#!/usr/bin/python3
from weightrail.cli import main

raise SystemExit(main())
EOF

cat >"$gui/usr/bin/weightrail-gui" <<'EOF'
#!/usr/bin/python3
from weightrail.gui import main

raise SystemExit(main())
EOF

chmod 0755 "$base/usr/bin/weightrail" "$gui/usr/bin/weightrail-gui"
gzip -9n -c debian/weightrail.1 >"$base/usr/share/man/man1/weightrail.1.gz"
install -m 0644 README.md "$base/usr/share/doc/weightrail/README.md"
install -m 0644 CHANGELOG.md "$base/usr/share/doc/weightrail/changelog"
gzip -9n "$base/usr/share/doc/weightrail/changelog"
install -m 0644 LICENSE "$base/usr/share/doc/weightrail/copyright"
install -m 0644 LICENSE "$gui/usr/share/doc/weightrail-gui/copyright"

cat >"$base/DEBIAN/control" <<EOF
Package: weightrail
Version: $package_version
Section: utils
Priority: optional
Architecture: all
Maintainer: Ashwin <ashwin@users.noreply.github.com>
Depends: python3 (>= 3.10), python3-numpy
Suggests: weightrail-gui
Homepage: https://github.com/SleepyMario/weightrail
Description: local-first weight tracker command-line interface
 Weightrail records daily weights in a per-user SQLite database and provides
 statistical and trend summaries without a network account or system daemon.
EOF

cat >"$gui/DEBIAN/control" <<EOF
Package: weightrail-gui
Version: $package_version
Section: utils
Priority: optional
Architecture: all
Maintainer: Ashwin <ashwin@users.noreply.github.com>
Depends: weightrail (= $package_version), gir1.2-gtk-3.0, python3-gi, python3-gi-cairo, python3-matplotlib
Homepage: https://github.com/SleepyMario/weightrail
Description: local-first weight tracker GTK interface
 This package adds Weightrail's GTK 3 interface with Matplotlib measurement,
 linear, weekly, and monthly trend charts.
EOF

dpkg-deb --root-owner-group --build "$base" "$output/weightrail_${package_version}_all.deb"
dpkg-deb --root-owner-group --build "$gui" "$output/weightrail-gui_${package_version}_all.deb"

(
  cd "$output"
  sha256sum ./*.deb >SHA256SUMS
)

printf 'Ubuntu .deb packages created in %s\n' "$output"

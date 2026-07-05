# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

DISTUTILS_USE_PEP517=setuptools
PYTHON_COMPAT=( python3_{10..14} )

inherit distutils-r1

DESCRIPTION="Simple SQLite-backed terminal weight tracker"
HOMEPAGE=""
# No public release archive exists yet. After creating the first GitHub release,
# set SRC_URI to the real archive URL, for example:
# SRC_URI="https://github.com/<USER>/${PN}/archive/refs/tags/v${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="MIT"
SLOT="0"
KEYWORDS="~amd64"
RESTRICT="fetch"

RDEPEND="
	dev-python/numpy[${PYTHON_USEDEP}]
	dev-python/plotext[${PYTHON_USEDEP}]
"
DEPEND="${RDEPEND}"
BDEPEND="
	test? (
		dev-python/pytest[${PYTHON_USEDEP}]
	)
"

distutils_enable_tests pytest

pkg_nofetch() {
	einfo "No public ${P} release distfile exists yet."
	einfo "Create the upstream release, update SRC_URI, then regenerate Manifest."
}

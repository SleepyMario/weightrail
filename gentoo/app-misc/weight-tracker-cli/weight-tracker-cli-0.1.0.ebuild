# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

DISTUTILS_USE_PEP517=setuptools
PYTHON_COMPAT=( python3_{11..14} )

inherit distutils-r1

DESCRIPTION="Simple SQLite-backed terminal weight tracker"
HOMEPAGE="https://github.com/SleepyMario/weight-tracker-cli"
SRC_URI="https://github.com/SleepyMario/${PN}/archive/refs/tags/v${PV}.tar.gz -> ${P}.tar.gz"

LICENSE="MIT"
SLOT="0"
KEYWORDS="~amd64"

RDEPEND="
	dev-python/numpy[${PYTHON_USEDEP}]
	dev-python/plotext[${PYTHON_USEDEP}]
"
DEPEND="${RDEPEND}"
BDEPEND=""

distutils_enable_tests unittest

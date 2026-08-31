# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

DISTUTILS_USE_PEP517=setuptools
PYTHON_COMPAT=( python3_{11..14} )

inherit distutils-r1

DESCRIPTION="Local-first SQLite-backed weight tracker with optional GTK interface"
HOMEPAGE="https://github.com/SleepyMario/weightrail"
SRC_URI="https://github.com/SleepyMario/${PN}/archive/refs/tags/v${PV}.tar.gz -> ${P}.tar.gz"
S="${WORKDIR}/${P}"

LICENSE="MIT"
SLOT="0"
KEYWORDS="~amd64"
IUSE="+graph gui"

RDEPEND="
	dev-python/numpy[${PYTHON_USEDEP}]
	graph? ( dev-python/plotext[${PYTHON_USEDEP}] )
	gui? (
		dev-python/matplotlib[gtk3,${PYTHON_USEDEP}]
		dev-python/pygobject:3[${PYTHON_USEDEP}]
		x11-libs/gtk+:3[introspection]
	)
"

BDEPEND="
	test? ( dev-python/pytest[${PYTHON_USEDEP}] )
"

EPYTEST_PLUGINS=()
distutils_enable_tests pytest

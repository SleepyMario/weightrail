%global upstream_name weight-tracker-cli

Name:           weightrail
Version:        0.1.0
Release:        1%{?dist}
Summary:        Local-first terminal weight tracker

License:        MIT
URL:            https://github.com/SleepyMario/weight-tracker-cli
Source0:        %{upstream_name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3dist(pytest)
BuildRequires:  python3dist(setuptools) >= 69
BuildRequires:  python3dist(wheel)
BuildRequires:  pyproject-rpm-macros
Requires:       python3dist(numpy)

%description
Weightrail records daily weights in a per-user SQLite database, displays
records, and provides statistical and trend summaries. It is a command-line
application and does not require a network service or system daemon.

%generate_buildrequires
%pyproject_buildrequires -r

%prep
%autosetup -n %{upstream_name}-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
install -Dpm 0644 packaging/rpm/README.md \
    %{buildroot}%{_docdir}/%{name}/README.rpm.md
rm -f %{buildroot}%{_bindir}/weightrail
rm -f %{buildroot}%{_bindir}/weight-tracker-gui
rm -f %{buildroot}%{python3_sitelib}/weight_tracker_cli/gui.py
rm -f %{buildroot}%{python3_sitelib}/weight_tracker_cli/__pycache__/gui.*.pyc
sed -i '/^weightrail = /d; /^weight-tracker-gui = /d' \
    %{buildroot}%{python3_sitelib}/weight_tracker_cli-%{version}.dist-info/entry_points.txt
%pyproject_save_files -l weight_tracker_cli
sed -i '/weight_tracker_cli\/gui\.py/d; /weight_tracker_cli\/__pycache__\/gui\./d' %{pyproject_files}

%check
export HOME="%{_builddir}/weightrail-test-home"
export XDG_DATA_HOME="$HOME/.local/share"
mkdir -p "$XDG_DATA_HOME"
%pytest --ignore=tests/test_gui.py
%pyproject_check_import -e weight_tracker_cli.gui

%files -f %{pyproject_files}
%doc CHANGELOG.md README.md
%{_docdir}/%{name}/README.rpm.md
%{_bindir}/weight-tracker

%changelog
* Mon Jul 13 2026 Ashwin <ashwin@users.noreply.github.com> - 0.1.0-1
- Add the initial RPM package

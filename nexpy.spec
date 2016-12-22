%global srcname nexpy

%define debug_package %{nil}

Name:           %{srcname}
Version:        0.8.1
Release:        1%{?dist}
Summary:        NeXpy Application

License:        BSD
URL:            https://nexpy.github.io/nexpy/
Source0:        https://github.com/nexpy/nexpy/archive/v%{version}.zip

Requires:       python-nexusformat
Requires:	python-matplotlib >= 1.4.0


%description
NeXpy provides a high-level python interface to NeXus data contained within a simple GUI. It is designed to provide an intuitive interactive toolbox allowing users both to access existing NeXus files and to create new NeXus-conforming data structures without expert knowledge of the file format. 

%prep
%autosetup -n %{srcname}-%{version}

%build
python setup.py build

%install
python setup.py install --skip-build --root %{buildroot}

%files
%doc README.rst README.md README
%{python2_sitelib}/nexpy/*
%{python2_sitelib}/NeXpy-%{version}-py2*.egg-info/*
%{_bindir}/nexpy

%changelog
* Thu Apr  7 2016 Stuart Campbell <campbellsi@ornl.gov> - 0.2.2-1
- Initial package

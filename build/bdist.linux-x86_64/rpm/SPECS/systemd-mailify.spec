%define name systemd-mailify
%define version 1.0
%define unmangled_version 1.0
%define release 1

Summary: systemd related mail notifications
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: GPL-3.0
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: George Karakougioumtzis <gkarakou> <gkarakou@gmail.com>
Requires: python systemd-python systemd systemd-libs 
Url: https://github.com/gkarakou/systemd-mailify
BuildRequires: python-setuptools

%description
A python based app that notifies for failed systemd services

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

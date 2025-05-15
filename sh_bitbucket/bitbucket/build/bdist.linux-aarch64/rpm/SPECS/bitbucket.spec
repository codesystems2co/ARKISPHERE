%define name bitbucket
%define version 1.0.110
%define unmangled_version 1.0.110
%define release 1

Summary: Bitbucket Integration with OAuth Support
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: @arkiphere <codesystems.co@gmail.com>
Url: https://arkiphere.cloud

%description

    A Python library for Bitbucket Cloud integration with OAuth support.
    Built on top of atlassian-python-api for enhanced functionality.
    

%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

# Fedora's igvm spec (rawhide, 0.4.0) moved to 0.5.0, the version the
# coconut-svsm QEMU patches are developed against. All five Fedora patches are
# upstream in 0.5.0. Rust dependencies are vendored (Source1) instead of taken
# from Fedora's crate packages, which do not cover 0.5.0 yet.

%global __brp_strip_static_archive %{nil}

Name:           igvm
Version:        0.5.0
Release:        1%{?dist}
Summary:        IGVM library

License:        MIT
URL:            https://github.com/microsoft/igvm
Source0:        https://github.com/microsoft/igvm/archive/refs/tags/igvm-v%{version}.tar.gz
# Generated with ./vendor.sh from Source2 (upstream ships no lock file)
Source1:        igvm-v%{version}-vendor.tar.xz
Source2:        Cargo.lock

ExcludeArch: %{ix86}

BuildRequires:  cargo-rpm-macros >= 24
BuildRequires:  CUnit-devel cbindgen cargo-c make gcc

%description
Igvm is an implementation of a parser for the Independent Guest Virtual Machine

%package libs
Summary: IGVM shared library

%description libs
Contains a shared library that applications that use %{name} will link to

%package devel
Provides: igvm-static = %{version}-%{release}
Requires: igvm-libs = %{version}-%{release}
Summary: IGVM library header files

%description devel
Contains header files and a static library for developing applications that use %{name}

%package tools
Requires: igvm-libs = %{version}-%{release}
Summary: IGVM tools

%description tools
The %{name}-tools package contains tools for
developing applications that use %{name}

%prep
%autosetup -n igvm-igvm-v%{version} -p1
cp -p %{SOURCE2} Cargo.lock
tar -xf %{SOURCE1}
%cargo_prep -v vendor

%define igvm_makeflags EXTRA_PARAMS="--profile rpm" TARGET_DIR="target" PROFILE=rpm
%define igvm_makeenv CARGO_HOME='.cargo' RUSTFLAGS='%{build_rustflags} -Csymbol-mangling-version=v0'

%build
%cargo_license_summary
%cargo_vendor_manifest

# -Csymbol-mangling-version=v0 is from the upstream .cargo/config.toml.
# Enable v0 symbols to get better output from `perf` and related tools.
%{igvm_makeenv} %make_build -C igvm_c build %{igvm_makeflags}

%check
%{igvm_makeenv} %make_build -C igvm_c test %{igvm_makeflags}

%install
%{igvm_makeenv} %make_install -C igvm_c PREFIX=/usr DESTDIR=%{buildroot} %{igvm_makeflags}

%files libs
%license LICENSE
%license cargo-vendor.txt
%{_libdir}/libigvm.so.*

%files devel
%{_includedir}/igvm
%license LICENSE
%license cargo-vendor.txt
%doc README.md
%{_libdir}/libigvm.a
%{_libdir}/libigvm.so
%{_libdir}/pkgconfig/igvm.pc

%files tools
%{_bindir}/dump_igvm
%doc README.md
%license LICENSE
%license cargo-vendor.txt

%changelog
* Tue Nov 10 2026 Paul Meyer <katexochen0@gmail.com> - 0.5.0-1
- Update to 0.5.0 for COPR, with vendored Rust dependencies

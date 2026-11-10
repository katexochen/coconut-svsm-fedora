%global date 2026.09
%global version_name v%{date}-devel
%global debug_package %{nil}
# Upstream's test suite is not run here; this mirrors the coconut-svsm-nix
# flake build, which does not run it either.
%bcond check 0
# The embedded OVMF is Fedora's OVMF.amdsev.fd (OvmfPkg/AmdSev), as in the
# Fedora review (bz#2541015) and the coconut-svsm-nix flake. It is built with
# the TPM stack (TPM2_ENABLE), through which the SVSM vTPM reaches the guest
# firmware (Tpm2InstanceLibDTpmSvsm). It verifies a kernel, initrd and command
# line loaded via fw_cfg against the SEV hashes table, which QEMU doesn't fill
# for IGVM firmware, so a kernel passed with -kernel is refused and the guest
# boots from disk. It has no Secure Boot, which suits stateless firmware: keys
# enrolled at runtime (e.g. by sd-boot's auto-enrollment) would be lost on the
# reset that follows, and the guest would loop.
%global OVMF_DIR /usr/share/edk2/ovmf
# The OVMF binary is embedded directly into the shipped igvm image, so its
# exact build version is queried here from whatever edk2-ovmf is actually
# installed in the buildroot.
%global EDK2_OVMF_VER %(rpm -qa --qf '%%{VERSION}-%%{RELEASE}' edk2-ovmf 2>/dev/null)

# Git submodules of the svsm tree; the GitHub release archive does not
# contain them, so they are shipped as separate sources.
%global PACKIT_COMMIT 98411fde7ddb76061159b4abbf0487a9adba469b
%global OPENSSL_VER 3.5.5
%global TPM_COMMIT 3b1f0e623f244abe2015df9e3ba86de5c9118524
# Git dependencies in Cargo.lock. They are vendored into Source4 like the
# crates.io ones, but cargo needs an explicit source replacement for each.
%global VIRTIO_DRIVERS_COMMIT c8786e83e6a64e46ed5cab301048dbaf3aab1444
%global CPUFEATURE_COMMIT 0182d61954372552fe2a40477340e949471a49ee

Name: coconut-svsm
Version: v%{date}.devel
Release: 4%{?dist}
Summary: The Coconut Secure VM Service Module for AMD SEV-SNP

License: MIT AND Apache-2.0 AND BSD-2-Clause AND BSD-2-Clause-Patent AND BSD-3-Clause AND Unicode-3.0
URL: https://github.com/coconut-svsm/svsm

Source0: https://github.com/coconut-svsm/svsm/archive/refs/tags/%{version_name}.tar.gz
Source1: https://github.com/coconut-svsm/packit/archive/%{PACKIT_COMMIT}/packit-%{PACKIT_COMMIT}.tar.gz
Source2: https://github.com/openssl/openssl/releases/download/openssl-%{OPENSSL_VER}/openssl-%{OPENSSL_VER}.tar.gz
Source3: https://github.com/TrustedComputingGroup/TPM/archive/%{TPM_COMMIT}/TPM-%{TPM_COMMIT}.tar.gz
# Generated with ./vendor.sh
Source4: coconut-svsm-%{version_name}-vendor.tar.xz
# QEMU firmware descriptor (qemu docs/interop/firmware.json). Numbered after
# edk2-ovmf's descriptors on purpose: it needs a QEMU with KVM planes support,
# so tools that pick firmware automatically for an SEV-SNP guest must keep
# choosing edk2's, and the SVSM image is only used when selected explicitly.
Source5: 80-coconut-svsm-x86_64.json

# Build fix for LLVM 23 (Rust 1.99): the 16-bit lgdt displacement overflowed
# and used to be silently truncated. Sent upstream.
Patch: 0001-bldr-drop-the-0x10000-offset-from-the-SIPI-GDT-load.patch

Provides: bundled(openssl) = %{OPENSSL_VER}
Provides: bundled(tpm2-reference-implementation) = %{TPM_COMMIT}
Provides: bundled(crate(packit)) = 0.1.1
# Empty while the src.rpm is built (edk2-ovmf is not installed in that chroot);
# the binary rpm is always built with edk2-ovmf pulled in via BuildRequires.
%if "%{EDK2_OVMF_VER}" != ""
Provides: bundled(edk2-ovmf) = %{EDK2_OVMF_VER}
%endif

ExclusiveArch: x86_64

BuildRequires: cargo-rpm-macros >= 24
BuildRequires: binutils >= 2.39
BuildRequires: rust-std-static-x86_64-unknown-none
BuildRequires: gcc clang
BuildRequires: clang-libs
BuildRequires: glibc-static
BuildRequires: openssl-devel
BuildRequires: cmake
BuildRequires: make
BuildRequires: perl
BuildRequires: edk2-ovmf >= 20260812

%description
coconut-svsm is an implementation of a Secure VM Service Module (SVSM) for
AMD SEV-SNP confidential virtual machines. It runs at VMPL0 inside the guest
and provides services to the guest OS, such as a virtual TPM.

QEMU with IGVM and KVM planes support is required to run it. The shipped
firmware file bundles the SVSM together with OVMF; the matching QEMU firmware
descriptor lets tools such as libvirt or systemd-vmspawn find it.

%prep
%autosetup -n svsm-%{date}-devel -p1
tar -xf %{SOURCE1} --strip-components=1 --directory packit
tar -xf %{SOURCE2} --strip-components=1 --directory libtcgtpm/deps/openssl
tar -xf %{SOURCE3} --strip-components=1 --directory libtcgtpm/deps/tpm-20-ref

tar -xf %{SOURCE4}
%cargo_prep -v vendor

# %%cargo_prep regenerates .cargo/config.toml from scratch, so re-add the
# target rustflags, the "xbuild" alias, and the source replacements for the
# git dependencies (these are what `cargo vendor` prints at the end).
cat >> .cargo/config.toml << EOC
[target.x86_64-unknown-none]
rustflags = [
    "-C", "force-frame-pointers",
    "--cfg", "aes_force_soft",
    "--cfg", 'aes_backend="soft"',
    "--cfg", "polyval_force_soft",
]

[target.x86_64-unknown-linux-gnu]
rustflags = [
    "-C", "code-model=kernel",
]

[alias]
xbuild = "run --package xbuild --release --"

[source."git+https://github.com/coconut-svsm/cpufeature.git?rev=%{CPUFEATURE_COMMIT}"]
git = "https://github.com/coconut-svsm/cpufeature.git"
rev = "%{CPUFEATURE_COMMIT}"
replace-with = "vendored-sources"

[source."git+https://github.com/rcore-os/virtio-drivers.git?rev=%{VIRTIO_DRIVERS_COMMIT}"]
git = "https://github.com/rcore-os/virtio-drivers.git"
rev = "%{VIRTIO_DRIVERS_COMMIT}"
replace-with = "vendored-sources"
EOC

%build
%cargo_license_summary
%cargo_vendor_manifest

# The Fedora RUSTFLAGS are meant for the host target and break the
# x86_64-unknown-none kernel build.
unset RUSTFLAGS

# Same targets and knobs as the coconut-svsm-nix flake: the QEMU-flavoured
# IGVM image plus the host-side helpers, release build, no network. The igvm
# rule does not depend on the "bin" target, so create the directory here.
mkdir -p bin
%make_build RELEASE=1 OFFLINE=1 FW_FILE=%{OVMF_DIR}/OVMF.amdsev.fd \
  bin/coconut-qemu.igvm bin/igvmbld bin/igvmmeasure aproxy

%if %{with check}
%check
make test
%endif

%install
# Collect the license texts of the third-party code compiled into, or embedded
# in, the shipped igvm image, renamed so it stays obvious which bundle each one
# belongs to. openssl, tpm-20-ref and packit are unpacked from our own Sources;
# edk2 is not, so its text is taken from the edk2-ovmf package in the buildroot,
# which is where the embedded OVMF binary comes from too. The vendored Rust
# crates are covered by cargo-vendor.txt instead.
cp -p libtcgtpm/deps/openssl/LICENSE.txt LICENSE.openssl.txt
cp -p libtcgtpm/deps/tpm-20-ref/LICENSE LICENSE.tpm-20-ref.txt
cp -p packit/LICENSE.APACHE-2.0.txt LICENSE.packit.APACHE-2.0.txt
# packit/LICENSE.MIT is identical to LICENSE-MIT, which is already shipped
cp -p %{_defaultlicensedir}/edk2-ovmf/License.txt LICENSE.edk2-ovmf.txt
cp -p %{_defaultlicensedir}/edk2-ovmf/License.OvmfPkg.txt LICENSE.edk2-ovmf.OvmfPkg.txt

install -D -m 444 bin/coconut-qemu.igvm %{buildroot}%{_datadir}/%{name}/coconut-qemu.igvm
install -D -m 644 %{SOURCE5} %{buildroot}%{_datadir}/qemu/firmware/80-coconut-svsm-x86_64.json
install -D -m 755 bin/igvmbld %{buildroot}%{_bindir}/igvmbld
install -D -m 755 bin/igvmmeasure %{buildroot}%{_bindir}/igvmmeasure
install -D -m 755 bin/aproxy %{buildroot}%{_bindir}/aproxy
install -D -m 755 scripts/launch_guest.sh %{buildroot}%{_bindir}/svsm-launch-guest

%files
%license LICENSE-MIT
%license cargo-vendor.txt
%license LICENSE.openssl.txt
%license LICENSE.tpm-20-ref.txt
%license LICENSE.packit.APACHE-2.0.txt
%license LICENSE.edk2-ovmf.txt
%license LICENSE.edk2-ovmf.OvmfPkg.txt
%dir %{_datadir}/%{name}/
%{_datadir}/%{name}/coconut-qemu.igvm
%{_datadir}/qemu/firmware/80-coconut-svsm-x86_64.json
%{_bindir}/igvmbld
%{_bindir}/igvmmeasure
%{_bindir}/aproxy
%{_bindir}/svsm-launch-guest

%changelog
* Tue Nov 10 2026 Paul Meyer <katexochen0@gmail.com> - v2026.09.devel-4
- Package v2026.09-devel for COPR, based on the Fedora review spec (bz#2541015)

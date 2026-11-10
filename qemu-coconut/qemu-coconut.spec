# QEMU for COCONUT-SVSM guests: upstream 11.1.0 plus the 20 commits the
# coconut-svsm/qemu svsm-v7.2 branch carries on top of it (KVM planes, direct
# IGVM VMSA launch for SEV-SNP, device tree generation for the PC machine, q35
# virtio-mmio slots). Identical to the patch series of the coconut-svsm-nix
# flake (pkgs/qemu/patches). Regenerate with:
#   git format-patch v11.1.0..coconut-svsm/svsm-v7.2
#
# This is deliberately not a replacement for Fedora's qemu: only the x86_64
# system emulator is built, into its own prefix, so both can be installed and
# systemd-vmspawn picks this one when %{coconut_prefix}/bin comes first in PATH
# (it looks for "qemu-kvm" before "qemu-system-x86_64", hence the symlink).

%global coconut_prefix %{_prefix}/lib/%{name}

# libigvm is linked statically (see %%build), so this is what ends up inside.
%global igvm_version 0.5.0

# As in Fedora's qemu: LTO and QEMU do not get along.
%global _lto_cflags %{nil}

Name: qemu-coconut
Version: 11.1.0
Release: 2%{?dist}
Summary: QEMU with KVM planes support for COCONUT-SVSM guests
License: %{shrink:
    Apache-2.0 AND
    BSD-2-Clause AND
    BSD-3-Clause AND
    FSFAP AND
    GPL-1.0-or-later AND
    GPL-2.0-only AND
    GPL-2.0-or-later AND
    GPL-2.0-or-later WITH GCC-exception-2.0 AND
    LGPL-2.0-only AND
    LGPL-2.0-or-later AND
    LGPL-2.1-only AND
    LGPL-2.1-or-later AND
    MIT AND
    LicenseRef-Fedora-Public-Domain AND
    CC-BY-3.0
}
URL: https://github.com/coconut-svsm/qemu

Source0: https://download.qemu.org/qemu-%{version}.tar.xz
Source1: https://download.qemu.org/qemu-%{version}.tar.xz.sig
Source2: gpgkey-CEACC9E15534EBABB82D3FA03353C9CEF108B584.gpg

Provides: bundled(igvm) = %{igvm_version}

Patch: 0001-Update-Linux-headers-for-KVM-planes-support.patch
Patch: 0002-accel-Expose-supported-and-requested-planes.patch
Patch: 0003-accel-kvm-Add-QOM-objects-for-plane-state.patch
Patch: 0004-accel-kvm-Create-and-manage-nonzero-planes.patch
Patch: 0005-accel-kvm-Handle-plane-vCPU-creation-events.patch
Patch: 0006-qdev-Add-inherited-IRQ-plane-properties.patch
Patch: 0007-accel-kvm-Route-legacy-interrupts-to-the-default-pla.patch
Patch: 0008-accel-kvm-Route-device-interrupts-by-plane.patch
Patch: 0009-docs-Document-KVM-plane-configuration.patch
Patch: 0010-hw-i386-add-device-tree-generation-for-PC-machine.patch
Patch: 0011-hw-i386-add-ISA-serial-devices-to-x86-device-tree.patch
Patch: 0012-hw-i386-add-fw-cfg-and-isa-debug-exit-to-x86-device-.patch
Patch: 0013-microvm-add-plane-property-to-device-tree.patch
Patch: 0014-igvm-add-device-tree-parameter-support.patch
Patch: 0015-backends-igvm-Materialize-confidential-VP-contexts-i.patch
Patch: 0016-target-i386-sev-Launch-IGVM-VMSAs-directly-for-SNP-g.patch
Patch: 0017-target-i386-sev-Restrict-legacy-VMSA-GPA-sentinel.patch
Patch: 0018-hw-uefi-Add-hardware-info-ID-for-virtio-mmio-devices.patch
Patch: 0019-q35-add-virtio-mmio-slots.patch
Patch: 0020-backends-igvm-Ignore-IGVM-command-line-directives.patch

ExclusiveArch: x86_64

BuildRequires: gcc
BuildRequires: make
BuildRequires: meson
BuildRequires: ninja-build
BuildRequires: python3-devel
# configure sets up a Python venv and wants these importable, otherwise it
# tries PyPI (no network in the buildroot); same set as Fedora's qemu
BuildRequires: python3-setuptools
BuildRequires: python3-pip
BuildRequires: python3-wheel
BuildRequires: python3-qemu-qmp
BuildRequires: gnupg2
BuildRequires: glib2-devel
BuildRequires: pixman-devel
BuildRequires: zlib-devel
BuildRequires: libzstd-devel
# device tree generation (--enable-fdt=system)
BuildRequires: libfdt-devel
# IGVM loading; 0.5.0 is what the planes branch is developed against. Only the
# static archive from igvm-devel is used.
BuildRequires: igvm-devel >= %{igvm_version}
BuildRequires: libslirp-devel
BuildRequires: libseccomp-devel
BuildRequires: libcap-ng-devel
BuildRequires: libattr-devel
BuildRequires: libaio-devel
BuildRequires: liburing-devel

%description
QEMU 11.1.0 with the coconut-svsm/qemu svsm-v7.2 patch series: KVM planes
support, direct launch of the IGVM VMSAs for SEV-SNP guests and device tree
generation for the PC machine. Together with the coconut-svsm firmware and a
host kernel with KVM planes support it runs COCONUT-SVSM guests.

Only the x86_64 system emulator is built. It is installed under
%{coconut_prefix} and does not replace the qemu packages.

%prep
%{gpgverify} --keyring=%{SOURCE2} --signature=%{SOURCE1} --data=%{SOURCE0}
%autosetup -n qemu-%{version} -p1

%build
# Link libigvm statically. Fedora's qemu needs igvm-libs 0.4 (libigvm.so.0.4),
# this build needs 0.5, and both are the same package, so a shared library
# dependency would make the two QEMUs mutually exclusive. Point pkg-config at
# a directory that only holds the static archive, with the private libraries
# the Rust staticlib needs folded into Libs.
mkdir -p igvm-static
cp -p %{_libdir}/libigvm.a igvm-static/
cat > igvm-static/igvm.pc << EOC
Name: igvm
Description: IGVM library, static archive only
Version: $(pkg-config --modversion igvm)
Cflags: $(pkg-config --cflags igvm)
Libs: -L$PWD/igvm-static $(pkg-config --libs --static igvm) -lgcc_s -lutil -lrt -lpthread -lm -ldl
EOC
export PKG_CONFIG_PATH=$PWD/igvm-static

./configure \
  --prefix=%{coconut_prefix} \
  --localstatedir=%{_localstatedir} \
  --sysconfdir=%{_sysconfdir}/%{name} \
  --cc=%{__cc} \
  --cxx=/bin/false \
  --extra-cflags="%{build_cflags}" \
  --extra-ldflags="%{build_ldflags}" \
  --with-pkgversion="%{name}-%{version}-%{release}" \
  --target-list=x86_64-softmmu \
  --enable-trace-backends=log \
  --enable-pie \
  --enable-kvm \
  --enable-igvm \
  --enable-fdt=system \
  --enable-slirp \
  --enable-tpm \
  --enable-vhost-user \
  --enable-seccomp \
  --enable-cap-ng \
  --enable-attr \
  --enable-zstd \
  --enable-linux-aio \
  --enable-linux-io-uring \
  --disable-modules \
  --disable-docs \
  --disable-user \
  --disable-tools \
  --disable-guest-agent \
  --disable-gtk \
  --disable-sdl \
  --disable-spice \
  --disable-opengl \
  --disable-virglrenderer \
  --disable-dbus-display \
  --disable-xen \
  --disable-usb-redir \
  --disable-libusb \
  --disable-smartcard \
  --disable-curl \
  --disable-rbd \
  --disable-libnfs \
  --disable-libssh \
  --disable-libiscsi \
  --disable-gnutls \
  --disable-nettle \
  --disable-gcrypt \
  --disable-curses \
  --disable-brlapi \
  --disable-alsa \
  --disable-pa \
  --disable-jack \
  --disable-pipewire \
  --disable-oss \
  --disable-sndio
%make_build

%install
%make_install

# systemd-vmspawn tries "qemu-kvm" before "qemu-system-x86_64".
ln -s qemu-system-x86_64 %{buildroot}%{coconut_prefix}/bin/qemu-kvm

# The option ROMs and BIOS blobs stay (they are looked up relative to this
# prefix), but QEMU's bundled edk2 images and the firmware descriptors pointing
# at them are not useful here: the firmware for SVSM guests comes from
# coconut-svsm, which installs its descriptor into /usr/share/qemu/firmware.
rm -f %{buildroot}%{coconut_prefix}/share/qemu/edk2-*
rm -rf %{buildroot}%{coconut_prefix}/share/qemu/firmware
rm -rf %{buildroot}%{coconut_prefix}/share/applications
rm -rf %{buildroot}%{coconut_prefix}/share/icons

%files
%license COPYING COPYING.LIB LICENSE
%{coconut_prefix}/

%changelog
* Tue Nov 10 2026 Paul Meyer <katexochen0@gmail.com> - 11.1.0-2
- Package QEMU 11.1.0 with the KVM planes patches of coconut-svsm/qemu svsm-v7.2

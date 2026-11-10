# COCONUT-SVSM host packages for Fedora

> [!WARNING]
> These packages are for development and testing only. They carry unreleased
> patches, follow development versions and come without security support. Don't
> use them in production.

Packaging of the host side needed to run COCONUT-SVSM guests with
`systemd-vmspawn --coco=sev-snp` on Fedora, built in the COPR
[katexochen/coconut-svsm](https://copr.fedorainfracloud.org/coprs/katexochen/coconut-svsm/).

- `igvm`: the IGVM library 0.5.0, which QEMU's IGVM support needs.
- `qemu-coconut`: QEMU 11.1.0 with the KVM planes patches of coconut-svsm/qemu
  `svsm-v7.2`, installed under `/usr/lib/qemu-coconut`, next to Fedora's QEMU.
- `coconut-svsm`: the SVSM with Fedora's `OVMF.amdsev.fd` as IGVM image, its
  QEMU firmware descriptor and the host tools. Based on the Fedora review spec
  ([bz#2541015](https://bugzilla.redhat.com/show_bug.cgi?id=2541015)).

COPR builds the SRPMs from this repository with `.copr/Makefile`, which
downloads the sources and generates the vendored Rust dependencies with the
package's `vendor.sh`. Bump `Release:` with every change.

#!/usr/bin/env nix
#! nix shell nixpkgs#rpm nixpkgs#curl nixpkgs#cargo nixpkgs#gnutar nixpkgs#gzip nixpkgs#xz --command bash
#
# Generate Source4, the vendored Rust dependencies. Unpacks Source0 to Source3
# as %prep does, downloading those not present yet, and vendors the crates as
# locked by upstream's Cargo.lock.

set -euo pipefail
cd "$(dirname "$0")"

spec=coconut-svsm.spec
source_url() { rpmspec -P "$spec" | sed -n "s/^Source$1:[[:space:]]*//p"; }
# Prints the path of SourceN, downloading it into the work directory unless it
# is present already, e.g. from spectool -g.
source_file() {
	local url file
	url=$(source_url "$1")
	file=$(basename "$url")
	if [[ ! -e "$file" ]]; then
		curl -fsSL -o "$work/$file" "$url"
		file="$work/$file"
	fi
	echo "$file"
}
date=$(sed -n 's/^%global date //p' "$spec")
out="$PWD/$(basename "$(source_url 4)")"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
# Keep cargo's registry and git caches out of ~/.cargo unless the caller
# points CARGO_HOME somewhere explicitly.
: "${CARGO_HOME:=$work/cargo-home}"
export CARGO_HOME

src="$work/svsm-${date}-devel"
tar -xzf "$(source_file 0)" -C "$work"
tar -xzf "$(source_file 1)" --strip-components=1 -C "$src/packit"
tar -xzf "$(source_file 2)" --strip-components=1 -C "$src/libtcgtpm/deps/openssl"
tar -xzf "$(source_file 3)" --strip-components=1 -C "$src/libtcgtpm/deps/tpm-20-ref"

(cd "$src" && cargo vendor --locked vendor > "$work/vendor-config.toml")

# Normalized archive so that reruns give the same bytes.
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime='1970-01-01 00:00:00Z' \
	-C "$src" -cf - vendor | xz > "$out"

echo "wrote $out"
echo "git sources reported by cargo vendor; the spec must carry a matching [source] section for each:"
sed -n 's/^\[source."git+\(.*\)"\]$/  \1/p' "$work/vendor-config.toml"

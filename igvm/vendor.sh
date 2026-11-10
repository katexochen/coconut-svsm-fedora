#!/usr/bin/env nix
#! nix shell nixpkgs#rpm nixpkgs#curl nixpkgs#cargo nixpkgs#gnutar nixpkgs#gzip nixpkgs#xz --command bash
#
# Generate Source1, the vendored Rust dependencies. Unpacks Source0, downloading
# it if not present yet. Upstream ships no lock file, so Source2 (Cargo.lock) is
# kept next to the spec and the crates are vendored as locked there. With
# REFRESH_LOCK=1, or without a Cargo.lock, cargo resolves a new one, which is
# copied back.

set -euo pipefail
cd "$(dirname "$0")"

spec=igvm.spec
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
version=$(rpmspec -q --srpm --qf '%{version}' "$spec")
out="$PWD/$(basename "$(source_url 1)")"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
# Keep cargo's registry and git caches out of ~/.cargo unless the caller
# points CARGO_HOME somewhere explicitly.
: "${CARGO_HOME:=$work/cargo-home}"
export CARGO_HOME

src="$work/igvm-igvm-v${version}"
tar -xzf "$(source_file 0)" -C "$work"

if [[ -e Cargo.lock && "${REFRESH_LOCK:-0}" != 1 ]]; then
	cp -p Cargo.lock "$src/Cargo.lock"
	(cd "$src" && cargo vendor --locked vendor > "$work/vendor-config.toml")
else
	(cd "$src" && cargo vendor vendor > "$work/vendor-config.toml")
	cp -p "$src/Cargo.lock" Cargo.lock
fi

# Normalized archive so that reruns give the same bytes.
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime='1970-01-01 00:00:00Z' \
	-C "$src" -cf - vendor | xz > "$out"

echo "wrote $out"
echo "git sources reported by cargo vendor (the spec needs a [source] section for each):"
sed -n 's/^\[source."git+\(.*\)"\]$/  \1/p' "$work/vendor-config.toml"

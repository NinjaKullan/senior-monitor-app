#!/usr/bin/env bash
# Sign the forge's unsigned shortcuts (spec 005e). macOS only.
#
#   ./product/scripts/forge-sign.sh out/shortcuts [out/signed]
#
# `shortcuts` ships with macOS and has no Linux equivalent, so this is the one
# step of the pipeline the container cannot run or test. Everything up to the
# signature is proved by `python -m scripts.forge --verify` and by
# product/tests/test_forge.py, on every push; this script is deliberately thin
# so that there is almost nothing here left to be wrong.
#
# The guard below is not ceremony. Running this on Linux fails anyway, but it
# fails with `shortcuts: command not found` — which reads like a missing package
# and invites someone to go looking for one. Saying so plainly is the difference
# between a clear boundary and a wasted afternoon.
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "forge-sign.sh: macOS only — 'shortcuts sign' has no Linux equivalent." >&2
    echo "Generate anywhere (python -m scripts.forge …), sign on a Mac." >&2
    exit 2
fi

if ! command -v shortcuts >/dev/null 2>&1; then
    echo "forge-sign.sh: the 'shortcuts' CLI is missing (macOS 12+)." >&2
    exit 2
fi

IN="${1:-}"
OUT="${2:-${IN%/}-signed}"

if [[ -z "$IN" || ! -d "$IN" ]]; then
    echo "usage: forge-sign.sh <unsigned-dir> [signed-dir]" >&2
    exit 64
fi

mkdir -p "$OUT"
# 0700: the token is inside every one of these files, signed or not.
chmod 700 "$OUT"

shopt -s nullglob
count=0
for file in "$IN"/*.shortcut; do
    # --mode anyone: the recipient is not in the signer's contacts. See
    # product/README.md for what that asks of the receiving phone.
    shortcuts sign --mode anyone --input "$file" --output "$OUT/$(basename "$file")"
    chmod 600 "$OUT/$(basename "$file")"
    echo "signed $(basename "$file")"
    count=$((count + 1))
done

if [[ "$count" -eq 0 ]]; then
    echo "forge-sign.sh: no .shortcut files in $IN" >&2
    exit 1
fi

echo
echo "$count signed shortcut(s) in $OUT."
echo "Every one carries the device token. Send them the way you would send a password,"
echo "and delete both directories when the phone is set up."

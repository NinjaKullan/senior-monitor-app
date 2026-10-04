#!/usr/bin/env bash
# Builds the ChatGPT plugin package (DECISIONS 358, docs/chatgpt-plugin-brief.md §2):
# dist/kettle-plugin-<version>.zip holding the kettle/ folder and nothing beside it.
# The version is read from kettle/plugin.json so the file name cannot drift from
# the manifest. dist/ is gitignored; the PM uploads the zip by hand.
#
#   tools/chatgpt-plugin/make-zip.sh            -> tools/chatgpt-plugin/dist/...
#   tools/chatgpt-plugin/make-zip.sh /some/dir  -> /some/dir/kettle-plugin-<version>.zip
set -euo pipefail
# The output directory is the caller's, resolved before leaving their cwd.
out_dir="$(realpath -m "${1:-$(dirname "$0")/dist}")"
cd "$(dirname "$0")"
version="$(python3 -c 'import json; print(json.load(open("kettle/plugin.json"))["version"])')"
mkdir -p "$out_dir"
out="$out_dir/kettle-plugin-${version}.zip"
rm -f "$out"
# -X: no extra file attributes; -x: what macOS and Python leave behind. Anything
# else under kettle/ is packaged, and the tests pin the folder to its three files.
zip -q -r -X "$out" kettle -x '*.DS_Store' '*/__pycache__/*' '*.pyc'
echo "$out"

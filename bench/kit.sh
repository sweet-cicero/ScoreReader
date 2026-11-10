#!/usr/bin/env bash
# Reads every page of the test kit with scoreread and scores the result with the kit's score.py.
# The kit is the folder in SCOREREAD_KIT (see the README).
# usage: bash bench/kit.sh <name> [scoreread options]        output: out/kit/<name>/ and out/kit/summary.md
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIT="${SCOREREAD_KIT:-$HOME/Projects/LitChoir/tmp/omr-test}"
source "$KIT/env.sh"
NAME="$1"; shift
export ROOT KIT NAME
export OPTIONS="$*"
mkdir -p "$ROOT/out/kit/$NAME/logs"
one() {
  local stem
  stem="$(basename "$1" .png)"
  (cd "$ROOT" && OMP_NUM_THREADS=4 nice -n 10 "$KIT/tools/copisteria/.venv/bin/python" -m scoreread read "$1" \
    --out "$ROOT/out/kit/$NAME" $OPTIONS > "$ROOT/out/kit/$NAME/logs/$stem.log" 2>&1) || echo "$stem failed"
}
export -f one
START=$(date +%s)
ls "$KIT"/pages/*.png | xargs -P 6 -I{} bash -c 'one "$@"' _ {}
echo "$NAME: $(ls "$ROOT/out/kit/$NAME"/*.musicxml 2>/dev/null | wc -l) pages in $(( $(date +%s) - START )) s"

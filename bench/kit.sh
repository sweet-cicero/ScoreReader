#!/usr/bin/env bash
# Reads every page of the test kit with scoreread, for the kit's score.py to score.
# The kit is the folder in SCOREREAD_KIT (see the README). The Python is the one in SCOREREAD_PYTHON, or the kit's
# copisteria environment. SCOREREAD_JOBS pages are read at a time (6 without it).
# usage: bash bench/kit.sh <name> [scoreread options]        output: out/kit/<name>/
#   bash bench/kit.sh own                     the engine (rules only, no model)
#   bash bench/kit.sh v04 --yardstick         the yardstick: the engine's clean pages, read with copisteria's network
#                                             (bench/yardstick; --ledger after it turns its ledger rule on)
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIT="${SCOREREAD_KIT:-$HOME/Projects/LitChoir/tmp/omr-test}"
[ -f "$KIT/env.sh" ] && source "$KIT/env.sh"
PY="${SCOREREAD_PYTHON:-$KIT/tools/copisteria/.venv/bin/python}"
[ $# -ge 1 ] || { echo "usage: bash bench/kit.sh <name> [scoreread options]" >&2; exit 2; }
NAME="$1"; shift
COMMAND=read; YARDSTICK=""
if [ "${1:-}" = "--yardstick" ]; then COMMAND=layout; YARDSTICK=yes; shift; fi
export ROOT KIT NAME PY COMMAND YARDSTICK
export OPTIONS="$*"
mkdir -p "$ROOT/out/kit/$NAME/logs"
one() {
  local stem
  stem="$(basename "$1" .png)"
  if [ -n "$YARDSTICK" ]; then
    (cd "$ROOT" && OMP_NUM_THREADS=4 nice -n 10 "$PY" -m scoreread layout "$1" --out "$ROOT/out/kit/$NAME" \
      > "$ROOT/out/kit/$NAME/logs/$stem.log" 2>&1 && OMP_NUM_THREADS=4 nice -n 10 "$PY" bench/yardstick/read.py \
      "$ROOT/out/kit/$NAME" --name "$stem" $OPTIONS >> "$ROOT/out/kit/$NAME/logs/$stem.log" 2>&1) || echo "$stem failed"
  else
    (cd "$ROOT" && OMP_NUM_THREADS=4 nice -n 10 "$PY" -m scoreread read "$1" \
      --out "$ROOT/out/kit/$NAME" $OPTIONS > "$ROOT/out/kit/$NAME/logs/$stem.log" 2>&1) || echo "$stem failed"
  fi
}
export -f one
START=$(date +%s)
ls "$KIT"/pages/*.png | xargs -P "${SCOREREAD_JOBS:-6}" -I{} bash -c 'one "$@"' _ {}
echo "$NAME: $(ls "$ROOT/out/kit/$NAME"/*.musicxml 2>/dev/null | wc -l) pages in $(( $(date +%s) - START )) s"

#!/usr/bin/env bash
# Runs a copisteria variant on every page of the kit: bash all.sh <name> [cop.py options, without --per-system]
# The staves of each system come from ../cases.json. Output: all/<name>/<page>.musicxml
set -uo pipefail
EXP="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$EXP/../env.sh"
NAME="$1"; shift
SOURCE="${PAGES:-$EXP/../pages}"
mkdir -p "$EXP/all/$NAME/logs"
python3 - "$EXP/../cases.json" <<'PY' > "$EXP/all/pages.tsv"
import json, sys
for case in json.load(open(sys.argv[1]))['cases']:
    for page in case['pages']:
        print(f"{case['id']}-p{page}\t{len(case['layout'])}")
PY
export EXP NAME SOURCE
export OPTIONS="$*"
one() {
  local stem="$1" per="$2"
  [ -f "$SOURCE/$stem.png" ] || { echo "no image for $stem"; return; }
  OMP_NUM_THREADS=4 nice -n 10 "$EXP/../tools/copisteria/.venv/bin/python" "$EXP/cop.py" "$SOURCE/$stem.png" "$EXP/all/$NAME" \
    --per-system "$per" $OPTIONS > "$EXP/all/$NAME/logs/$stem.log" 2>&1 || echo "$stem failed"
}
export -f one
START=$(date +%s)
xargs -P 6 -L 1 bash -c 'one "$@"' _ < "$EXP/all/pages.tsv"
echo "$NAME: $(ls "$EXP/all/$NAME"/*.musicxml | wc -l) pages in $(( $(date +%s) - START )) s"

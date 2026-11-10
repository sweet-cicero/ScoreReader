#!/usr/bin/env bash
# Runs one reader on every image of an input set: bash run.sh <reader> <set> [jobs]
# Images: in/<set>/*.png. Output: results/<reader>-<set>/, in the form that ../score.py reads.
set -uo pipefail
EXP="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT="$(dirname "$EXP")"
TOOLS="$KIT/tools"
source "$KIT/env.sh"
READER="$1"; SET="$2"; JOBS="${3:-4}"
OUT="$EXP/results/$READER-$SET"
mkdir -p "$OUT/logs" "$OUT/work"
export OUT TOOLS READER
one() {
  local image="$1" stem
  stem="$(basename "$image" .png)"
  case "$READER" in
    homr)
      cp "$image" "$OUT/$stem.png"
      OMP_NUM_THREADS=4 timeout 600 nice -n 10 "$TOOLS/homr/bin/homr" "$OUT/$stem.png" > "$OUT/logs/$stem.log" 2>&1
      rm -f "$OUT/$stem.png" "$OUT/${stem}_teaser.png" ;;
    copisteria)
      cp "$image" "$OUT/work/$stem.png"
      (cd "$TOOLS/copisteria" && OMP_NUM_THREADS=4 timeout 600 nice -n 10 "$TOOLS/copisteria/.venv/bin/python" -m copisteria.pipeline \
        "$OUT/work/$stem.png" --out "$OUT" > "$OUT/logs/$stem.log" 2>&1)
      rm -f "$OUT/work/$stem.png" ;;
    audiveris)
      LAUNCHER="$(find "$TOOLS/audiveris" -path '*/bin/Audiveris' -type f | head -1)"
      timeout 600 nice -n 10 "$LAUNCHER" -batch -export -output "$OUT" \
        -constant org.audiveris.omr.sheet.BookManager.useCompression=false -- "$image" > "$OUT/logs/$stem.log" 2>&1 ;;
  esac
  echo "$READER $SET $stem: exit $?"
}
export -f one
START=$(date +%s)
ls "$EXP/in/$SET"/*.png | xargs -P "$JOBS" -I{} bash -c 'one "$@"' _ {}
echo "$READER-$SET: $(( $(date +%s) - START )) s"

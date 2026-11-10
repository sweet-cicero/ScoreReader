# ScoreReader

## Goal

Build a product that reads scanned choir scores accurately on the owner's own computer. No assistant and no cloud
model may be in the loop: a page goes in, the notes come out. Take what is good from existing readers and replace
what fails. The result must go into the LitChoir app as a typed hymn.

"Accurate" is not reached yet. Version 0.4 gets 81 % of the notes right on the test kit. Report each result with its
limits.

## State

- `scoreread/` is the reader. `README.md` lists its steps, the results and the next steps.
- `bench/` holds the tests. Measure each change with `bash bench/kit.sh <name>` and the kit's `score.py`.
- `experiments/` holds the record of the first tests.

## Rules

- This repository is public. Do not add scans, typed hymns, recordings or keys. They stay in the test kit, outside git.
- The test kit is in `~/Projects/LitChoir/tmp/omr-test` (`SCOREREAD_KIT`). Do not change the kit's own files.
- Run Python with the kit's copisteria environment (`$SCOREREAD_KIT/tools/copisteria/.venv/bin/python`), after
  `source "$SCOREREAD_KIT/env.sh"`. That environment has OpenCV, NumPy, Pillow and PyTorch.
- homr and Audiveris have the AGPL-3.0 licence. Do not copy their code into this repository. copisteria's code has
  the Apache-2.0 licence; the reader imports it and does not copy it.
- The limits in `staves.py` and `systems.py` were set on the kit's 38 pages. Check a change on all 38 pages.
- A written score wins over a recording.

# ScoreReader

## Goal

The end goal is a local engine of our own that reads scanned choir scores consistently, with creative new and old
methods. A page goes in and the notes come out, on the owner's own computer, with no assistant and no cloud model in
the loop. The result must go into the LitChoir app as a typed hymn.

The goal is not a better wrapper for the existing readers. An existing reader can be a part for a time, and it is
a yardstick for each own step. Each step that the engine does itself replaces a step of an existing reader.

"Consistent" is not reached yet. Version 0.5 gets 86.9 % of the notes right on the test kit with no model at all (0.4
got 81 % with copisteria's network). The target is 95 %. Report each result with its limits.

## Direction

Every step is the engine's own now: staves, systems, the clean page, the layers, the symbols and the music rules.
The engine must stay free of neural networks: rules and classical image processing only. copisteria, homr and
Audiveris are yardsticks. The own symbol step is behind copisteria's network on old copies (83 % against 88 %) and
on poor pages (72 % against 95 %); that is the next work. Ideas, each to test against the kit:

- Layers: process a hard page through a series of low-level steps that make it easier to read. Split the ink into
  staff lines, note heads, stems and beams, ledger lines and words, and give each layer its own strong colour. Rules
  read one layer at a time, and the colour picture lets a person check a page at a glance. (The owner asked for
  this: "processes it through a series of things to make it easier to read, either with different contrasting
  colors or other methods of scanning the image at a lower level".) Measured so far: a cleaner picture alone corrects
  layout mistakes (the test hymn went from 34 % to 85 %), but it does not make homr or Audiveris read hand-drawn notes.
- Note heads from the ink itself: take the staff lines away, find the blobs, and tell filled from hollow by the
  hole. A hand-drawn head is a slanted stroke: its shape and its place on the known staff lines give the pitch.
- The page teaches its own symbols: group the shapes that repeat on a page (one copyist draws one kind of clef, rest
  and head), and name each group once by rules.
- Lengths from stems, flags, beams and dots. Two voices from the stem direction.
- Music checks that need no model: the voices of a bar have the same length, the staves of a system line up in
  columns, the key signature holds for the whole hymn.
- A second look where two methods or two sizes disagree.

## State

- `scoreread/` is the reader. `README.md` lists its steps, the results and the next steps.
- `scoreread/reader.py` is the own symbol step (`layers.py`, `symbols.py`, `starts.py`, `signs.py`, `ties.py`, `music.py`).
  `scoreread/engine.py` is copisteria's step, kept as a yardstick (`read --symbols copisteria`).
- `bench/` holds the tests. Measure each change with `bash bench/kit.sh <name>` and the kit's `score.py`.
- Switch one rule at a time and score it alone on all 38 pages. Rules scored together hide a rule that costs notes.
- `experiments/` holds the record of the first tests.

## Rules

- This repository is public. Do not add scans, typed hymns, recordings or keys. They stay in the test kit, outside git.
- The test kit is in `~/Projects/LitChoir/tmp/omr-test` (`SCOREREAD_KIT`). Do not change the kit's own files.
- Run Python with the kit's copisteria environment (`$SCOREREAD_KIT/tools/copisteria/.venv/bin/python`), after
  `source "$SCOREREAD_KIT/env.sh"`. That environment has OpenCV, NumPy, Pillow and PyTorch. The own symbol step needs
  only OpenCV and NumPy, and it must not import PyTorch or copisteria.
- homr and Audiveris have the AGPL-3.0 licence. Do not copy their code into this repository. copisteria's code has
  the Apache-2.0 licence; the reader imports it and does not copy it.
- The limits in `staves.py` and `systems.py` were set on the kit's 38 pages. Check a change on all 38 pages.
- A written score wins over a recording.

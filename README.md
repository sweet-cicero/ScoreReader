# scoreread: a local reader for choir scores

Version 0.5, 10 November 2026. One command reads a page of a score and writes its notes. Everything runs on this
computer: no network, no assistant, no cloud model, and from this version on no neural network. Every step is rules
on the ink of the page, written in this repository, with OpenCV and NumPy.

```
python -m scoreread read "path/to/score.pdf" --page 1 --out out/my-hymn
python -m scoreread read page.png --out out/my-hymn
python -m scoreread layers page.png --out out/check       # the page with each layer of ink in its own colour
python -m scoreread layout page.png --out out/check       # only staves and systems, 2 seconds
```

`read` writes `<name>.musicxml` (the notes), `<name>.notes.json` (each note, its place and what it was read from),
`<name>.layout.json` (the staves and systems), `<name>.clean.png` (the page that was read), `<name>.staves.png` (the
scan with the staves drawn on it, as a check) and `<name>.layers.png` (the layers picture). One page takes about 14
seconds on one processor core. Python needs `opencv-python` and `numpy`; a PDF also needs `pdftoppm` (poppler).

`read --symbols copisteria` reads the symbols with copisteria's network as version 0.4 did. It is kept as a
yardstick and needs the test kit (see "The test kit" below).

## What the reader does

| Step | File | Model used? | What it does |
|---|---|---|---|
| 1. Staves | `scoreread/staves.py` | No | Finds each staff and follows its five lines along the page, also where the page bends, tilts or the lines are weak. Drops blank staves. |
| 2. Systems | `scoreread/systems.py` | No | Puts the staves into systems from the page's ink: the opening line, bar lines through the gap, and bar lines at the same places. Ink in the margin does not count. Finds a staff whose lines the copy lost. |
| 3. Clean page | `scoreread/page.py` | No | Makes each system level and puts the systems on a white page. The shadow of the binding and the page number stay behind. |
| 4. Layers | `scoreread/layers.py` | No | Splits the ink into staff lines, upright strokes (stems and bar lines), thick marks (note heads, beams, flags), the holes of hollow heads, and the rest. `layers` draws them in colours. |
| 5. Symbols | `scoreread/symbols.py`, `starts.py`, `signs.py`, `ties.py` | No | Reads the note heads (filled, hollow, and the thin slanted heads of a hand), their stems, flags, beams and dots, the ledger lines, the bar lines, the clef and key signature of each staff, the sharps, flats and naturals before a note, and the ties. |
| 6. Music | `scoreread/music.py`, `reader.py` | No | Pitch from the clef, the key and the signs of the bar. Two voices on a staff from the stem direction. Notes that begin together stand in one column. The voices of a system must agree on the length of each step, and a note that disagrees is changed. Choir rule: a treble staff over the bass staff is the tenors'. Writes MusicXML. |

Steps 4 to 6 are the own symbol step. They replace copisteria's network of version 0.4.

## Results on the reader test (31 typed hymns, 38 pages, 6901 notes)

Notes right means pitch and length both right, counted by the kit's `score.py` against the typed hymns.

| Kind of score | Hymns | copisteria alone | homr alone | scoreread 0.4 (copisteria's network) | scoreread 0.5 (no model) |
|---|---:|---:|---:|---:|---:|
| Printed | 12 | 67 % | 82 % | 76 % | 89 % |
| Old copy (notes drawn by hand) | 9 | 76 % | 37 % | 88 % | 82 % |
| By hand | 5 | 65 % | 70 % | 79 % | 84 % |
| Poor (faded or broken) | 2 | 93 % | 49 % | 95 % | 72 % |
| Digital PDF | 3 | 81 % | 72 % | 81 % | 99 % |
| All 31 hymns | 31 | 71 % | 66 % | 81 % | 86.6 % (5978 notes) |

- Over all hymns the own symbol step reads more notes right than the network it replaces: 86.6 % against 81 %.
- It is behind the network on two kinds: old copies (82 % against 88 %) and the two poor pages (72 % against 95 %).
  These are the next work.
- 7 of the 31 hymns are at 95 % or more, and 15 are at 90 % or more. 7 are under 80 %. The lowest are a hand copy
  (Kontakion of the Nativity of the Forerunner, 71 %), two old copies (68 % and 69 %), a poor page (66 %) and two
  Trisagion hymns with recitation notes (61 % and 70 %, see the limits).
- The target is 95 % of all notes. It is not reached.

## Limits

- The reader is not accurate enough yet to put a hymn into the app without a check. Most hymns still have 5 % to 35 %
  wrong notes.
- The rules and their limits were set on the same 38 pages that test them, in 28 rounds of measuring. The figures
  above are therefore the best case. New pages will read worse until they are measured too.
- 164 typed notes (2.4 %) are recitation notes that the page does not print: the singers repeat a note for each
  syllable. A reader of the page cannot find them, so a perfect reader gets about 97.6 % on this kit.
- The score counts each part. A staff of two parts is split by the stem direction (stem up is the upper part). One
  stem read wrong, or one head of a chord missed, gives the note to the wrong part.
- Not read yet: rests, time signatures, slurs, triplets, and the words. A rest or the digits of a time signature
  can be read as a note. A tie is read when its bow runs from head to head on one line of the page (11 notes of the
  kit; about as many tied notes are still read as two): a tie over a line break, a thick straight bow and a bow at
  the far ends of the stems are not read.
- Most of the wrong notes are of these kinds: a note read one step off, mostly on old copies and hand copies (about
  240 notes; some 30 of them are a sharp or a flat of a hand that was not read), the note of the staff's other part
  (about 120; in 88 of them the second head was not found), a half note read as a quarter because the copy filled
  its hole (about 90), and an eighth note read as a quarter because its flag or beam was not seen (about 70).
- A few typed notes are doubtful against the page (about ten were found). They count as wrong here, because the kit
  is not changed.
- The output is MusicXML for one page. The reader does not join pages or write the app's hymn format yet.

## Next steps

The end goal is an engine of our own that reads these scores consistently. Every step is our own now, and the
target of 95 % is still 8 points away.

1. Old copies and poor pages: read the lengths and the heads that the network still reads better.
2. Rests and time signatures. With them, a check of each bar's length against the time signature.
3. Read each page in two ways and look again at the places that disagree.
4. Read the words.
5. Join the pages of a hymn and write the app's hymn format.

## Tests

```
export SCOREREAD_KIT="$HOME/Projects/LitChoir/tmp/omr-test"     # the test kit, see below
PY="$SCOREREAD_KIT/tools/copisteria/.venv/bin/python"           # or any Python with opencv-python and numpy
$PY bench/drawn_check.py                                      # the whole reader on a page the script draws; needs no kit
$PY bench/staves_check.py "$SCOREREAD_KIT/pages" out/staves   # 38 of 38 pages right
$PY bench/systems_check.py "$SCOREREAD_KIT"                   # 37 of 38; on the other page the copy lost a staff
bash bench/kit.sh own                                         # reads all 38 pages with the own symbol step
bash bench/kit.sh v04 --symbols copisteria                    # the same with copisteria's network
python3 "$SCOREREAD_KIT/score.py" --results out/kit --tools own v04
```

`bench/kit.sh` takes its Python from `SCOREREAD_PYTHON`, or the kit's copisteria environment without it.

## The test kit

The tests need the test kit, which is not in this repository. The reader itself does not need it, except for
`--symbols copisteria`.

- `pages/`: 38 page images of 31 hymns. They are scans of the choir's scores, so they stay out of git.
- `truth/`: the same hymns typed by hand, as the answer key.
- `score.py`, `cases.json`, `env.sh`: the scoring script, the list of hymns and the settings of the tools.
- `tools/copisteria`: copisteria with its own Python and its model files (about 4 GB with the other readers), for
  `--symbols copisteria`.

`SCOREREAD_KIT` names the kit's folder. Without it, the tests look in `~/Projects/LitChoir/tmp/omr-test`.
`SCOREREAD_COPISTERIA` names another copy of copisteria.

## History

`experiments/2026-11-09-hard-scans/` holds the first tests on one difficult hymn, with a report. They found the three
causes that this reader removes: wrong systems from ink in the margin, staves found twice on bent pages, and the
ledger lines of one copyist.

Version 0.5 replaced copisteria's network with the own symbol step (layers, symbols, music). Each rule was switched
on alone and scored on all 38 pages, and a rule that did not gain notes was dropped.

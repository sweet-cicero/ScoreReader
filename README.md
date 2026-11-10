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
| 5. Symbols | `scoreread/symbols.py`, `starts.py`, `signs.py`, `ties.py`, `words.py` | No | Reads the note heads (filled, hollow, and the thin slanted heads of a hand), their stems, flags, beams and dots, the ledger lines, the bar lines, the clef and key signature of each staff, the sharps, flats and naturals before a note, and the ties. Finds the rows of the words, so that a stem ends where they begin and a letter is no note. |
| 6. Music | `scoreread/music.py`, `reader.py` | No | Pitch from the clef, the key and the signs of the bar. Two voices on a staff from the stem direction. Notes that begin together stand in one column. The voices of a system must agree on the length of each step, and a note that disagrees is changed. Choir rule: a treble staff over the bass staff is the tenors'. Writes MusicXML. |

Steps 4 to 6 are the own symbol step. They replace copisteria's network of version 0.4.

## Results on the reader test (31 typed hymns, 38 pages, 6901 notes)

Notes right means pitch and length both right, counted by the kit's `score.py` against the typed hymns.

| Kind of score | Hymns | copisteria alone | homr alone | scoreread 0.4 (copisteria's network) | scoreread 0.5 (no model) |
|---|---:|---:|---:|---:|---:|
| Printed | 12 | 67 % | 82 % | 76 % | 91 % |
| Old copy (notes drawn by hand) | 9 | 76 % | 37 % | 88 % | 86 % |
| By hand | 5 | 65 % | 70 % | 79 % | 86 % |
| Poor (faded or broken) | 2 | 93 % | 49 % | 95 % | 77 % |
| Digital PDF | 3 | 81 % | 72 % | 81 % | 99 % |
| All 31 hymns | 31 | 71 % | 66 % | 81 % | 88.8 % (6129 notes) |

- Over all hymns the own symbol step reads more notes right than the network it replaces: 88.8 % against 81 %.
- It is behind the network on two kinds: old copies (86 % against 88 %) and the two poor pages (77 % against 95 %).
  These are the next work.
- 8 of the 31 hymns are at 95 % or more, and 19 are at 90 % or more. 6 are under 80 %. The lowest are two Trisagion
  hymns with recitation notes (62 % and 70 %, see the limits), two old copies (71 % and 75 %), a hand copy (Kontakion
  of the Nativity of the Forerunner, 74 %) and a poor page (75 %).
- The target is 95 % of all notes. It is not reached: 427 more notes must be right. The last nine rounds of measuring
  brought 132 notes together (1.9 points).

## Limits

- The reader is not accurate enough yet to put a hymn into the app without a check. 23 of the 31 hymns have more than
  5 % wrong notes, and the six lowest have about a quarter or more.
- The rules and their limits were set on the same 38 pages that test them, in 40 rounds of measuring. The figures
  above are therefore the best case. New pages will read worse until they are measured too.
- 164 typed notes (2.4 %) are recitation notes that the page does not print: the singers repeat a note for each
  syllable. A reader of the page cannot find them, so a perfect reader gets about 97.6 % on this kit.
- The score counts each part. A staff of two parts is split by the stem direction (stem up is the upper part). One
  stem read wrong, or one head of a chord missed, gives the note to the wrong part.
- Not read yet: rests, time signatures, slurs, triplets, and the words. A rest or the digits of a time signature
  can be read as a note. A tie is read when its bow runs from head to head on one line of the page (11 notes of the
  kit; about as many tied notes are still read as two): a tie over a line break, a thick straight bow and a bow at
  the far ends of the stems are not read.
- 772 typed notes are wrong: 281 in pitch, 184 in length, 107 in both, and 200 not read (164 of them the recitation
  notes). Most are of these kinds: a note read a step or a half step off, mostly on old copies and hand copies
  (about 230 notes), the note of the staff's other part (about 75; the second voice's own head was not read, and
  for 41 of them its stem stands on the page with no head), a half note read as a quarter because the copy filled
  its hole or a hand left its oval open (about 75), and an eighth note read as a quarter because its flag or beam
  was not seen (about 45).
- Some typed notes differ from the page. On one hand copy (the Koinonikon of Palm Sunday) about 15 notes that
  count as wrong are read as the page shows them. They count as wrong here, because the kit is not changed.
- For scale: copisteria's own output and this reader have 93.4 % of the notes right between them (a note counts
  when one of the two has it right). 458 notes are wrong in both, 164 of them the recitation notes, and 314 are
  right only in copisteria's output. So the notes that only a network reads today would not bring the kit to 95 %
  either.
- The reader also writes notes that are not there: about 260 on the kit, from time signatures, rests, letters of the
  words, ornaments and slurs. They are counted apart and do not lower notes right (without them it would rise by
  4 notes), but a singer would see them.
- The output is MusicXML for one page. The reader does not join pages or write the app's hymn format yet.

## Next steps

The end goal is an engine of our own that reads these scores consistently. Every step is our own now, and the
target of 95 % is still 6 points away.

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

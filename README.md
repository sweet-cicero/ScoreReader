# scoreread: a local reader for choir scores

Version 0.4, 9 November 2026. One command reads a page of a score and writes its notes. Everything runs on this
computer: no network, no assistant and no cloud model. The reader takes the good part of an existing product
(copisteria's symbol reader, Apache-2.0 licence) and replaces the parts that fail on the choir's scans with code of
its own.

```
export SCOREREAD_KIT="$HOME/Projects/LitChoir/tmp/omr-test"     # the test kit, see "The test kit" below
source "$SCOREREAD_KIT/env.sh"
PY="$SCOREREAD_KIT/tools/copisteria/.venv/bin/python"
$PY -m scoreread read "path/to/score.pdf" --page 1 --out out/my-hymn
$PY -m scoreread read page.png --out out/my-hymn --ledger
$PY -m scoreread layout page.png --out out/check          # only staves and systems, 2 seconds
```

`read` writes `<name>.musicxml` (the notes), `<name>.notes.json` (each note head and its place), `<name>.layout.json`
(the staves and systems), `<name>.clean.png` (the page that was read) and `<name>.staves.png` (the scan with the
staves drawn on it, as a check). One page takes about 14 seconds on the PC's processor.

## What the reader does

| Step | File | Model used? | What it does |
|---|---|---|---|
| 1. Staves | `scoreread/staves.py` | No | Finds each staff and follows its five lines along the page, also where the page bends, tilts or the lines are weak. Drops blank staves. |
| 2. Systems | `scoreread/systems.py` | No | Puts the staves into systems from the page's ink: the opening line, bar lines through the gap, and bar lines at the same places. Ink in the margin does not count. |
| 3. Clean page | `scoreread/page.py` | No | Makes each system level and puts the systems on a white page. The shadow of the binding and the page number stay behind. |
| 4. Symbols | `scoreread/engine.py` | copisteria's local network | Reads the note heads, stems, rests, clefs and bar lines. It gets the staves and systems of steps 1 and 2 as facts. |
| 5. Choir rules | `scoreread/choir.py`, `scoreread/ledger.py` | No | Tenor staff: a treble clef over the bass staff sounds an octave lower. Ledger rule (option `--ledger`): a line through a note head puts the note on the ledger line. |

Step 4 is the only step with a neural network. That network is part of copisteria and runs on this computer.

## Results on the reader test (31 typed hymns, 38 pages, 6901 notes)

Notes right means pitch and length both right, counted by the kit's `score.py` against the typed hymns.

| Kind of score | Hymns | copisteria alone | homr alone | scoreread 0.4 |
|---|---:|---:|---:|---:|
| Printed | 12 | 67 % | 82 % | 76 % |
| Old copy (notes drawn by hand) | 9 | 76 % | 37 % | 88 % |
| By hand | 5 | 65 % | 70 % | 79 % |
| Poor (faded or broken) | 2 | 93 % | 49 % | 95 % |
| Digital PDF | 3 | 81 % | 72 % | 81 % |
| All 31 hymns | 31 | 71 % | 66 % | 81 % |

- 9 of the 31 hymns are at 95 % or more, and 14 are at 90 % or more. With copisteria alone, 4 and 7 were.
- The test hymn "O only Creator" goes from 34 % to 85 %, and to 90 % with `--ledger`.
- Largest gains: wedding Alleluia 49 % to 98 %, "It is truly meet" (Zakkak) 65 % to 99 %, "Pious Joseph" 37 % to 94 %,
  Troparion of the Synaxis of the Forerunner 55 % to 88 %.
- 6 hymns are a little under copisteria alone (1 to 10 notes each).

## Limits

- The reader is not accurate enough yet to put a hymn into the app without a check. Most hymns still have 5 % to 25 %
  wrong notes.
- homr reads some printed pages better (Bulgarian "It is truly meet": 89 % against 55 %). Audiveris reads digital PDFs
  at 99 %. The reader does not use them yet. A perfect choice between homr and this reader for each hymn gives 86 %.
- The limits in steps 1 and 2 were set on the same 38 pages that test them. New pages can need new limits.
- The reader writes no words yet.
- The output is MusicXML for one page. The reader does not join pages or write the app's hymn format yet.

## Next steps

1. Use homr for the staves that it reads better, and Audiveris for digital PDFs. The reader must make the choice from
   the page itself.
2. Correct the frequent mistakes of step 4 with rules: two note heads that touch, a quarter note read as a half note,
   a reciting tone, a key signature.
3. Read each page at several sizes and compare the results place by place. The places that disagree are the doubtful
   places.
4. Read the words.
5. Join the pages of a hymn and write the app's hymn format.

## Tests

```
$PY bench/staves_check.py "$SCOREREAD_KIT/pages" out/staves   # 38 of 38 pages right
$PY bench/systems_check.py "$SCOREREAD_KIT"                   # 36 of 38; the 2 others have a staff that the copy lost
bash bench/kit.sh v04                                         # reads all 38 pages, about 200 seconds
python3 "$SCOREREAD_KIT/score.py" --results out/kit --tools v04
```

## The test kit

The reader needs the test kit, which is not in this repository:

- `tools/copisteria`: copisteria with its own Python and its model files (about 4 GB with the other readers).
- `pages/`: 38 page images of 31 hymns. They are scans of the choir's scores, so they stay out of git.
- `truth/`: the same hymns typed by hand, as the answer key.
- `score.py`, `cases.json`, `env.sh`: the scoring script, the list of hymns and the settings of the tools.

`SCOREREAD_KIT` names the kit's folder. Without it, the reader looks in `~/Projects/LitChoir/tmp/omr-test`.
`SCOREREAD_COPISTERIA` names another copy of copisteria.

## History

`experiments/2026-11-09-hard-scans/` holds the first tests on one difficult hymn, with a report. They found the three
causes that this reader removes: wrong systems from ink in the margin, staves found twice on bent pages, and the
ledger lines of one copyist.

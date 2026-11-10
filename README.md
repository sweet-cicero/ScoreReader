# scoreread: a local reader for choir scores

Version 0.6 (in work), 10 November 2026. One command reads a page of a score and writes its notes. Everything runs
on this computer: no network, no assistant, no cloud model and no neural network. Every step is rules on the ink of
the page, written in this repository, with OpenCV and NumPy. No other reader is a part of it.

```
python -m scoreread read "path/to/score.pdf" --page 1 --out out/my-hymn
python -m scoreread read page.png --out out/my-hymn
python -m scoreread layers page.png --out out/check       # the page with each layer of ink in its own colour
python -m scoreread layout page.png --out out/check       # only staves and systems, 2 seconds
```

`read` writes `<name>.musicxml` (the notes), `<name>.notes.json` (each note, its place and what it was read from),
`<name>.layout.json` (the staves and systems), `<name>.clean.png` (the page that was read), `<name>.staves.png` (the
scan with the staves drawn on it, as a check) and `<name>.layers.png` (the layers picture). One page takes about 14
seconds on one processor core. Python needs `opencv-python` and `numpy`; a PDF also needs `pdftoppm` (poppler), and
a PDF that notation software wrote is read from its own drawing with `pdfplumber`.

## The goal

Every score of the choir's app (LitChoir) must be read on this computer, with no AI in the reader, and none of them
under 99 % of the notes that its pages show. The words under the notes belong to the result. This is not reached:
see the results and the limits below.

## What the reader does

| Step | File | Model used? | What it does |
|---|---|---|---|
| 1. Staves | `scoreread/staves.py` | No | Finds each staff and follows its five lines along the page, also where the page bends, tilts or the lines are weak. Looks twice, with the dark ink alone and with pale level lines too (some copies print the staff in grey hair lines), and keeps the better staff at each place. Drops blank staves. |
| 2. Systems | `scoreread/systems.py` | No | Puts the staves into systems from the page's ink: the opening line, bar lines through the gap, and bar lines at the same places. Ink in the margin does not count. Finds a staff whose lines the copy lost. |
| 3. Clean page | `scoreread/page.py` | No | Makes each system level and puts the systems on a white page. The shadow of the binding and the page number stay behind. |
| 4. Layers | `scoreread/layers.py` | No | Splits the ink into staff lines, upright strokes (stems and bar lines), thick marks (note heads, beams, flags), the holes of hollow heads, and the rest. `layers` draws them in colours. |
| 5. Symbols | `scoreread/symbols.py`, `starts.py`, `meter.py`, `signs.py`, `ties.py`, `words.py` | No | Reads the note heads (filled, hollow, and the thin slanted heads of a hand), their stems, flags, beams and dots, the ledger lines, the bar lines, the clef and key signature of each staff, the sharps, flats and naturals before a note, and the ties. The key of a page is a vote of its staves (a copy loses signs more easily than it gains them), and a page without a key signature has the key of the page before. Finds the time signatures, so that their numbers are no notes and no sharps. Finds the rows of the words, so that a stem ends where they begin and a letter is no note. |
| 6. Music | `scoreread/music.py`, `reader.py` | No | Pitch from the clef, the key and the signs of the bar. Two voices on a staff from the stem direction. Notes that begin together stand in one column. The voices of a system must agree on the length of each step, and a note that disagrees is changed. Choir rule: a treble staff over the bass staff is the tenors'. Writes MusicXML. |
| Drawing | `scoreread/vector.py` | No | A PDF that notation software wrote holds each sign as a character of a music font at its exact place, and its words as text. Such a page is read from that drawing, with its words; no image is read. |

Steps 4 to 6 are the own symbol step. They replaced copisteria's network of version 0.4, which is only a yardstick
now: it lives in `bench/yardstick`, outside the reader (see "Tests").

## How the reader works, in diagrams

The diagrams show the logic of the reader as the code runs it. No box holds a model: each one is a rule on the ink,
or on the signs of a PDF. The yardstick in `bench/yardstick` is a test tool, not a part of the reader, and is not
shown. GitHub draws the diagrams from the text below (Mermaid).

### The whole reader

```mermaid
flowchart TD
    source["A page of a score: a PNG image or a page of a PDF"]
    source --> kind{{"Is it a PDF with the signs of a music font, and with a staff?"}}
    kind -- "Yes: notation software wrote it" --> drawing["<b>The PDF's own drawing</b><br/>vector.py<br/>No image is read. The words are read too."]
    kind -- "No: a scan, a photo or an image" --> grey["<b>Grey image</b><br/>A PDF page is made at 300 dpi. The grey paper of a photo is made white."]
    grey --> staves["<b>Step 1: staves</b><br/>staves.py"]
    staves --> systems["<b>Step 2: systems</b><br/>systems.py"]
    systems --> clean["<b>Step 3: clean page</b><br/>page.py"]
    clean --> layers["<b>Step 4: layers of the ink</b><br/>layers.py"]
    layers --> symbols["<b>Step 5: symbols</b><br/>words.py, symbols.py, starts.py, meter.py, signs.py, ties.py"]
    symbols --> music["<b>Step 6: music rules</b><br/>music.py"]
    drawing -------> music
    music --> notes["<b>The notes</b><br/>name.musicxml and name.notes.json"]
    clean -.-> layout["name.layout.json, name.clean.png and name.staves.png. The command layout stops here."]
    layers -.-> picture["name.layers.png. The command layers stops here."]
```

### Steps 1 to 3: staves, systems and the clean page

```mermaid
flowchart LR
    subgraph one["Step 1: staves"]
        direction TB
        s1["Keep only the long level runs of ink. Staff lines stay. Heads, stems and letters go."]
        s2["Staff space: the most frequent distance between two neighbour lines."]
        s3["In each upright band of the page, slide a comb of five teeth over the rows. A staff stands where all five teeth meet ink."]
        s4["Link the bands along the staff's own slope. A page that tilts or bends is no problem."]
        s5["Follow each staff past its ends where the lines are weak. Four of the five lines are enough."]
        s6["Drop a staff that was found twice, and a blank staff."]
        s7["Look twice: with the dark ink alone, and with pale level lines too. Where both looks find a staff, keep the one whose weakest line has the most ink. The dark look wins unless the other is clearly better."]
        s1 --> s2 --> s3 --> s4 --> s5 --> s6 --> s7
    end
    subgraph two["Step 2: systems"]
        direction TB
        y1["For each two staves that follow each other, measure what joins them: the opening line at the left end, bar lines through the gap, their own bar lines at the same places, and their notes in the same columns."]
        y2["A line that goes on over the first staff or under the last staff is a shadow. It joins nothing."]
        y3["Weigh all the links of the page together. The number of staves in a system is the one that agrees best with them."]
        y4["Find a staff that the copy lost. The whole systems show where it stands, and what is left of its lines proves it."]
        y1 --> y2 --> y3 --> y4
    end
    subgraph three["Step 3: clean page"]
        direction TB
        c1["Make each system level: in each column, every staff line moves to its mean height."]
        c2["Cut each system from the emptiest row over it to the emptiest row under it. The words under a staff stay with their staff."]
        c3["Put the systems on a white page. The shadow of the binding and the page number stay behind."]
        c4["The result: the clean page, and the row of every staff line on it."]
        c1 --> c2 --> c3 --> c4
    end
    one --> two --> three
```

### Step 4: the layers of the ink

On the clean page the row of every staff line is known, so each layer comes from a plain measure of the ink. The
colours are those of `name.layers.png`.

```mermaid
flowchart TD
    page["Clean page"] --> ink["<b>Ink</b><br/>The dark pixels, without the blots: a punch hole, the shadow of a binding."]
    ink --> holes["<b>Holes</b> (orange)<br/>Small round paper that ink closes in: the inside of a hollow note head."]
    ink --> solid["<b>Solid ink</b><br/>The ink with its holes filled. A hollow head and a filled head are both one solid mark."]
    holes --> solid
    solid --> lines["<b>Staff lines</b> (light grey)<br/>The ink in the row of a line, where nothing stands on the line."]
    solid --> free["<b>Free ink</b><br/>The solid ink without the staff lines. The dashes of a weak copy are joined."]
    lines --> free
    free --> strokes["<b>Upright strokes</b> (blue)<br/>Ink that stands high in one column. The slim ones are stems and bar lines."]
    free --> marks["<b>Marks</b><br/>The free ink without the stems."]
    strokes --> marks
    marks --> thick["<b>Thick marks</b> (black)<br/>Where a round brush a third of a staff space wide still fits: note heads, beams, flags, the heavy parts of clefs."]
    marks --> rest["<b>The rest</b> (dark grey)<br/>Words, slurs, ledger lines."]
```

### Step 5: from the layers to the symbols

```mermaid
flowchart LR
    subgraph find["Find the heads"]
        direction TB
        f0["Rows of the words (words.py): a row of the page that crosses many small pieces of ink."]
        f1["Thick marks (symbols.py), cut where two heads touch. The page shows the size of its own heads."]
        f2["Name each mark by the upright ink that leaves it (see the next diagram)."]
        f3["Pitch place: the height of the head between the known rows of the staff lines. For a hollow head, the middle of its hole. Beside the staff, the ledger lines are counted."]
        f0 --> f1 --> f2 --> f3
    end
    subgraph more["Correct the heads"]
        direction TB
        m1["Clef, key signature and time signature at the start of each staff (starts.py, meter.py). The notes of a staff begin after them."]
        m2["Bar lines: bare upright lines from the top line to the bottom line, with no head on them."]
        m3["Heads that the thick marks do not show: a thin slanted head of a hand, found from its stem; a hollow head, found from its hole; a head whose stem the copy cut off."]
        m4["Taken away: the joint of a slanted head with its stem, the loop of a printed flag, and the numbers of a time signature in the middle of a staff."]
        m1 --> m2 --> m3 --> m4
    end
    subgraph around["Read around the heads"]
        direction TB
        a1["A stem ends where the words begin."]
        a2["Flags and beams at the far end of each stem. The page shows the thickness of its own beams."]
        a3["Dots at the right of a head."]
        a4["Sharps, flats and naturals before a head (signs.py)."]
        a5["Ties (ties.py): a thin bow from a head to the next head of its pitch."]
        a6["The result: heads with place, stems, flags or beams, dots, signs and ties, in bars."]
        a1 --> a2 --> a3 --> a4 --> a5 --> a6
    end
    find --> more --> around
```

What a thick mark is. Each mark is asked where upright ink leaves it.

```mermaid
flowchart TD
    mark["A thick mark as large as a head can be"] --> letter{{"Does it stand in a row of the words?"}}
    letter -- "yes" --> no1["A letter: no note"]
    letter -- "no" --> strokes{{"Do strokes leave it as the strokes of a sign do?"}}
    strokes -- "yes" --> sign["<b>A sharp:</b> slim strokes up and down at both sides. <b>A flat:</b> a small bowl with a stroke up from its left side. <b>A natural:</b> a stroke up at the left and a stroke down at the right."]
    strokes -- "no" --> far{{"Does it hang on two stems side by side, or at the far end of another head's stem?"}}
    far -- "yes" --> tail["A beam or a flag of that note"]
    far -- "no" --> stem{{"Does slim ink climb from its right half, or fall from its left half, for more than a staff space?"}}
    stem -- "yes" --> head["<b>A note head with its stem.</b> A stem up is the upper voice, a stem down the lower voice."]
    stem -- "no" --> oval{{"Is it a hollow oval on its side, as large as the heads of the page?"}}
    oval -- "yes" --> whole["<b>A whole note</b>"]
    oval -- "no" --> orphan["No note, unless it is as large as a head and a stem that the copy cut off ends at it."]
```

### The clef, the key signature and the time signature

```mermaid
flowchart TD
    start["The first columns of each staff (starts.py)"]
    start --> shape["<b>The clef from its shape</b><br/>A treble clef begins far over the top line and ends under the bottom line. A bass clef stays inside the staff."]
    start --> signs["<b>The signs after the clef</b><br/>From their upright strokes: a sharp has two strokes side by side, a flat has one stroke with a bowl. The strokes of a time signature are no signs."]
    signs --> chain["<b>Chain</b><br/>Each next sign must stand where the fixed order of a key signature puts it, under a treble or a bass clef. A rest or the first note ends the chain. On a thick copy, where the first signs ran together, two later signs stand for the whole signature."]
    chain --> key["<b>Key of the page</b><br/>The staves vote. A copy loses signs more easily than it gains them: a key that some staves show well wins over the staves that show none, and more signs win over fewer signs of their sort."]
    key --> before["A page that shows no key has the key of the page before (--key-before). A system whose staves all show another key has that key."]
    chain --> witness["The heights of the chain show the clef too: a second witness."]
    shape --> clef
    witness --> clef["<b>Clef</b><br/>The same staff of every system votes for its clef. Without a witness, the lowest staff of a system of two or more is a bass staff, and the others are treble staves."]
    before --> ends["Where the notes begin on each staff: after its clef, its key signature and its time signature."]
    clef --> ends
```

A time signature is found so that its numbers are not read as notes or as sharps. The numbers themselves are not
read yet.

```mermaid
flowchart TD
    mark["A mark in a staff, with the staff lines taken away (meter.py)"] --> halves{{"Is it two numbers, one over the other: one fills the staff from the top line to the middle line, and one from the middle line to the bottom line?"}}
    halves -- "no" --> other["Not a time signature"]
    halves -- "yes" --> note{{"Is it a bar line, the thick blot of a head, or one thin stem across the middle line?"}}
    note -- "yes" --> other
    note -- "no" --> where{{"Where does it stand?"}}
    where -- "at the start of the staff" --> time["<b>A time signature</b><br/>Its numbers are no key signs, no sharps and no notes. The notes of the staff begin after it."]
    where -- "in the middle of the staff" --> agree{{"Do two staves of the system show it at one place? In a system of one staff: does a bar line stand right before it?"}}
    agree -- "yes" --> time
    agree -- "no" --> other
```

### Step 6: the music rules

How long a note is:

```mermaid
flowchart TD
    head{{"Is the head hollow?"}}
    head -- "yes" --> stem{{"Has it a stem?"}}
    stem -- "no" --> whole["Whole note"]
    stem -- "yes" --> half["Half note"]
    head -- "no" --> tails{{"How many flags or beams at the far end of its stem?"}}
    tails -- "0" --> quarter["Quarter note"]
    tails -- "1" --> eighth["Eighth note"]
    tails -- "2" --> sixteenth["Sixteenth note"]
    whole & half & quarter & eighth & sixteenth --> dot{{"Does a dot stand at its right?"}}
    dot -- "yes" --> longer["Half as long again"]
    dot -- "no" --> same["As it is"]
```

From the symbols to the notes:

```mermaid
flowchart TD
    heads["Heads of a staff, with their lengths"] --> voices["<b>Voices</b><br/>A stem up is voice 1, a stem down is voice 2. A head with both stems is in both voices."]
    voices --> columns["<b>Bars and columns</b><br/>The notes between two bar lines are a bar. Notes that begin together stand in one column."]
    columns --> check["<b>Music check</b><br/>For the staves of one system: from one column to the next, every voice says how long the step is. Where two or more voices agree and outnumber the others, a note that says something else is changed."]
    check --> onsets["<b>Onsets</b><br/>In a bar, each column begins when the voices that sing in it are free."]
    onsets --> pitch["<b>Pitch</b><br/>The clef names each pitch place. The key of the staff and the signs of the bar give its sharp or flat."]
    clefs["Clefs and key of the page"] --> tenor["<b>Choir rule</b><br/>In a system of three or more staves, a treble staff over the bass staff is the tenors'. It sounds an octave lower."]
    tenor --> pitch
    pitch --> xml["<b>MusicXML</b><br/>The same staff of every system is one part."]
```

### A PDF that notation software wrote

Such a PDF holds each sign as a character of a music font at its exact place (Maestro, Petrucci, Anastasia, Leland,
Bravura and fonts like them), so nothing has to be recognised.

```mermaid
flowchart LR
    subgraph lay["Find the staves"]
        direction TB
        p1["The characters, the drawn lines and the filled shapes of the page (vector.py)."]
        p2["The page counts when characters of a music font show note heads, and a staff is found. Any other page is read as an image."]
        p3["<b>Staves</b><br/>Five long level lines at even distances."]
        p4["<b>Systems</b><br/>An upright stroke at the left that runs from one staff to the next joins them."]
        p5["<b>Bar lines and stems</b><br/>An upright stroke over the whole height of a staff is a bar line. The others are stems."]
        p1 --> p2 --> p3 --> p4 --> p5
    end
    subgraph signs["Look each sign up"]
        direction TB
        q1["<b>Heads</b><br/>Each head sign on the line or the space of the staff that it fits."]
        q2["<b>Lengths</b><br/>Stems at the edge of a head. Flag signs and beam shapes at the free end of a stem. Dots."]
        q3["<b>Clef, key and signs</b><br/>The clef sign and the key signature after it. Sharps, flats and naturals before a head."]
        q4["<b>Ties</b><br/>A bow from a head to the next head at the same height, also over the end of a line."]
        q5["<b>Words</b><br/>Each syllable under its note."]
        q1 --> q2 --> q3 --> q4 --> q5
    end
    subgraph write["Write the notes"]
        direction TB
        r1["<b>Ison</b><br/>Only on a chant page, with one staff in each system: the open heads without a stem and without a syllable become a part of their own, held in time with the melody."]
        r2["<b>Music rules of step 6</b><br/>Voices, columns, onsets, pitch and the choir rule."]
        r3["MusicXML with the words, and name.notes.json"]
        r1 --> r2 --> r3
    end
    lay --> signs --> write
```

Not in the diagrams, because the reader of scans does not do it yet: the words of a scan, rests, slurs, triplets,
and the numbers of a time signature (see "Limits").

## Results on every score of LitChoir (the wide test)

The wide test reads every score of the app that has a typed hymn to compare with: 366 scores on 657 pages, 516 of
them scans. Notes right means pitch and length both right. The count is of the notes that the pages show: 5,836
typed notes that no page prints (mostly recited syllables) are listed apart.

| Kind of score | Scores | Notes right | At 99 % or more | At 90 % or more | Under 50 % |
|---|---:|---:|---:|---:|---:|
| PDFs that notation software wrote (read from their drawing) | 70 | 99.1 % (19,916 of 20,104) | 51 | 68 | 0 |
| Scans | 296 | 74.6 % (52,194 of 69,934) | 8 | 67 | 34 |
| All | 366 | 80.1 % (72,110 of 90,038) | 59 | 135 | 34 |

- Words: 5,586 of 28,976 syllables are right (19 %). All of them come from the software-made PDFs, where 92 % of
  the syllables are right. No word is read from a scan yet.
- The last rounds on the scans: new rules for the systems brought 1,511 notes, and the rules for keys and time
  signatures 713 (4 lost).
- 4 more scans are not counted: their page holds another version than the typed hymn.

## Results on the reader test (31 typed hymns, 38 pages, 6901 notes)

The kit is the small test that each rule is checked on. Notes right is counted by the kit's `score.py` against the
typed hymns, of all typed notes.

| Kind of score | Hymns | copisteria alone | homr alone | scoreread 0.4 (copisteria's network) | scoreread now (no model) |
|---|---:|---:|---:|---:|---:|
| Printed | 12 | 67 % | 82 % | 76 % | 91 % |
| Old copy (notes drawn by hand) | 9 | 76 % | 37 % | 88 % | 86 % |
| By hand | 5 | 65 % | 70 % | 79 % | 86 % |
| Poor (faded or broken) | 2 | 93 % | 49 % | 95 % | 79 % |
| Digital PDF | 3 | 81 % | 72 % | 81 % | 99 % |
| All 31 hymns | 31 | 71 % | 66 % | 81 % | 88.9 % (6132 notes) |

- Over all hymns the own rules read more notes right than the network they replaced: 88.9 % against 81 %.
- They are behind the network on two kinds: old copies (86 % against 88 %) and the two poor pages (79 % against 95 %).
- 8 of the 31 hymns are at 95 % or more, and 19 are at 90 % or more. 6 are under 80 %.

## Limits

- The reader is not accurate enough yet to put a scanned hymn into the app without a check. Only 8 of the 296
  scanned scores are at 99 %, and 34 are under 50 %: thick copies where signs and heads ran together, pages with
  pale staff lines, and pages where a clef is hidden.
- The rules and their limits were set on the same pages that test them. The figures above are therefore the best
  case. New pages will read worse until they are measured too.
- The wide test compares with typed hymns that were made for singing, not for testing. Some differ from the page
  (another key, an octave, a repeat written out). Known cases are told to the scorer; others count as wrong.
- About 17,700 drawn notes of the scans are wrong. Counted one round earlier (of about 18,700 then; a note can be
  wrong in two ways): about 7,300 are not read at all, about 6,900 have a wrong pitch (a wrong key or clef, or one
  place off), and about 6,100 a wrong length (a half note read as a quarter because the copy filled its hole, an
  eighth read as a quarter because its flag or beam was not seen, dots).
- The score counts each part. A staff of two parts is split by the stem direction (stem up is the upper part). One
  stem read wrong, or one head of a chord missed, gives the note to the wrong part.
- Not read yet on scans: the words, rests, slurs and triplets. A rest can be read as a note. Time signatures are
  found so that they are no notes, but their numbers are not read. A tie is read when its bow runs from head to
  head on one line of the page.
- The reader also writes notes that are not there (about 260 on the kit), from rests, letters of the words,
  ornaments and slurs. They are counted apart and do not lower notes right, but a singer would see them.
- The output is MusicXML for one page. The reader does not join pages or write the app's hymn format yet (the wide
  test joins the pages with a script of its own).

## Next steps

1. One command for a whole hymn: all pages, the key carried from page to page, the pages joined.
2. Pale staff lines, clefs hidden behind a bracket, and the pages where almost nothing is read.
3. Half notes whose hole the copy filled, by the notes that sound with them. Flags and beams that are not seen.
4. The words on scans, with no model.
5. Rests, with a check of each bar's length.
6. The app's hymn format.

## Tests

```
export SCOREREAD_KIT="$HOME/Projects/LitChoir/tmp/omr-test"     # the test kit, see below
PY="$SCOREREAD_KIT/tools/copisteria/.venv/bin/python"           # or any Python with opencv-python and numpy
$PY bench/drawn_check.py                                      # the whole reader on a page the script draws; needs no kit
$PY bench/staves_check.py "$SCOREREAD_KIT/pages" out/staves   # 38 of 38 pages right
$PY bench/systems_check.py "$SCOREREAD_KIT"                   # 37 of 38; on the other page the copy lost a staff
bash bench/kit.sh own                                         # reads all 38 pages (rules only)
bash bench/kit.sh v04 --yardstick                             # the yardstick: the same clean pages with copisteria's network
python3 "$SCOREREAD_KIT/score.py" --results out/kit --tools own v04
```

`bench/kit.sh` takes its Python from `SCOREREAD_PYTHON`, or the kit's copisteria environment without it.

The yardstick (`bench/yardstick`) reads the reader's clean pages with copisteria's network, to measure the own rules
against it. It is a test tool: the reader does not load it, and nothing of it ships with the reader.

The wide test (every score of LitChoir) is run with scripts outside this repository, because it needs the app's
scans and typed hymns.

## The test kit

The tests need the test kit, which is not in this repository. The reader itself does not need it.

- `pages/`: 38 page images of 31 hymns. They are scans of the choir's scores, so they stay out of git.
- `truth/`: the same hymns typed by hand, as the answer key.
- `score.py`, `cases.json`, `env.sh`: the scoring script, the list of hymns and the settings of the tools.
- `tools/copisteria`: copisteria with its own Python and its model files (about 4 GB with the other readers), for
  the yardstick (`bench/yardstick`).

`SCOREREAD_KIT` names the kit's folder. Without it, the tests look in `~/Projects/LitChoir/tmp/omr-test`.
`SCOREREAD_COPISTERIA` names another copy of copisteria.

## History

`experiments/2026-11-09-hard-scans/` holds the first tests on one difficult hymn, with a report. They found the three
causes that this reader removes: wrong systems from ink in the margin, staves found twice on bent pages, and the
ledger lines of one copyist.

Version 0.5 replaced copisteria's network with the own symbol step (layers, symbols, music). Each rule was switched
on alone and scored on all 38 pages, and a rule that did not gain notes was dropped.

Version 0.6 (in work) reads software-made PDFs from their drawing with their words, groups the staves of scans by
three more checks, votes for the key of a page, finds time signatures, and moved the yardstick out of the reader.

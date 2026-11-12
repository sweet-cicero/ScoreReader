# ScoreReader

## Goal

The end goal is a local engine of our own that reads scanned choir scores consistently, with creative new and old
methods. A page goes in and the notes come out, on the owner's own computer, with no assistant, no cloud model and
no neural network in the loop. The result must go into the LitChoir app as a typed hymn.

The target (the owner, 10 November 2026): every score of LitChoir is read locally, without AI, and none of them is
under 99 % of the notes that its pages show. The words under the notes belong to the result: music without its
words is of no use. Recited syllables that no page prints are counted apart, and the reader must mark a reciting
note. The work does not stop at a partial result. Report each result with its limits.

First milestone (the owner, 11 November 2026): 99 % on clean copies, the 81 scan scores with printed notes and
words and crisp ink. Work on these first, notes and words. The thick copies (26) and the copies by hand (189) come
after it. The owner decided against a local language model. The owner allowed Tesseract for the words of a scan
(11 November 2026: "we can use tesseract, if it will help, but may eventually have to improve upon it"): it is an
optional step (`--tesseract`, `scoreread/ocr.py`), the reader works without it, and the own letter reader stays and
must catch up with it. The notes are read by rules alone, with no model.

Not reached yet: 84.4 % of the drawn notes over all 364 counted scores (99.3 % on software-made PDFs, 80.1 % on
scans; 65 scores at 99 % or more), 93.8 % of the notes on the clean copies (20,907 of 22,299; 11 of the 78 counted
scores at 99 %), and of their syllables 49.9 % with the own letter reader and 83.3 % with Tesseract (78.7 % of the
whole words); 77.8 % of all syllables with Tesseract (73.9 % on scans), and 88.9 % on the kit (6136 of 6901).
On the fresh test set, which no rule was set on: 92.3 % of the notes (37,772 of 40,906; 70 of 214 pieces at 99 %),
54.6 % of the syllables and 64.7 % of the whole words.

## Direction

Every step is the engine's own: staves, systems, the clean page, the layers, the symbols, the music rules, and the
drawing of a software-made PDF. The engine is rules and classical image processing only, and it is ours to design:
it is no wrapper of another reader. copisteria, homr and Audiveris are yardsticks only; copisteria's step lives in
`bench/yardstick`, outside the package, and nothing in `scoreread/` may import it. Ideas, each to test:

- Layers: process a hard page through a series of low-level steps that make it easier to read. Split the ink into
  staff lines, note heads, stems and beams, ledger lines and words, and give each layer its own strong colour. Rules
  read one layer at a time, and the colour picture lets a person check a page at a glance. (The owner asked for
  this: "processes it through a series of things to make it easier to read, either with different contrasting
  colors or other methods of scanning the image at a lower level".)
- The page teaches its own symbols: group the shapes that repeat on a page (one copyist draws one kind of clef, rest
  and head), and name each group once by rules.
- The hymn teaches the page: the key, the clefs and the parts hold from page to page.
- Notes that sound together agree: a half note whose hole the copy filled stands in a column of half notes.
- Music checks that need no model: the voices of a bar have the same length, the staves of a system line up in
  columns, the key signature holds for the whole hymn.
- A second look where two methods or two sizes disagree.
- Words on scans without a model: the page's own letter shapes, grouped, and a word list from the typed text of
  the app's hymns (kept outside git).

## State

- `scoreread/` is the reader. `README.md` lists its steps, the results and the next steps.
- `scoreread/reader.py` reads a clean page (`layers.py`, `words.py`, `symbols.py`, `starts.py`, `meter.py`,
  `signs.py`, `ties.py`, `triplets.py`, `drone.py`, `music.py`). `letters.py` and `lyrics.py` read the words of a scan, and
  `ocr.py` reads them with Tesseract when asked.
  `scoreread/vector.py` reads a software-made PDF from its drawing.
- `bench/` holds the tests. Measure each change with `bash bench/kit.sh <name>` and the kit's `score.py`.
  `bench/yardstick/` is copisteria's step (`bash bench/kit.sh <name> --yardstick`).
- The wide test (every score of LitChoir) runs with scripts outside git, because it needs the app's scans. It reads
  each score as `hymn` does: the pages in order, the key and the clefs carried, one vote for the hymn's key.
- The clean copies are a fixed list of 81 scores (outside git, with the wide test); 78 are counted (one was sorted
  wrongly, the page of two holds another version than the typed hymn). Report them first after each round, and
  change the list only with a reason.
- Switch one rule at a time and score it alone on all 38 pages, and on the wide test's pages that it changes.
  Rules scored together hide a rule that costs notes.
- `experiments/` holds the record of the first tests.

## Rules

- This repository is public. Do not add scans, typed hymns, recordings or keys. They stay in the test kit, outside git.
- The test kit is in `~/Projects/LitChoir/tmp/omr-test` (`SCOREREAD_KIT`). Do not change the kit's own files.
- The reader needs only OpenCV and NumPy (and pdfplumber for software-made PDFs). Nothing in `scoreread/` may
  import PyTorch, copisteria or any other model. The one exception is `scoreread/ocr.py`: it calls the Tesseract
  program for the rows of the words, only when it is asked for, and no note may depend on it. The kit's
  copisteria environment (`$SCOREREAD_KIT/tools/copisteria/.venv/bin/python`, after
  `source "$SCOREREAD_KIT/env.sh"`) has all of it and runs the yardstick too.
- homr and Audiveris have the AGPL-3.0 licence. Do not copy their code into this repository. copisteria's code has
  the Apache-2.0 licence; the yardstick imports it and does not copy it.
- The limits in `staves.py` and `systems.py` were set on the kit's 38 pages. Check a change on all 38 pages
  (`bench/staves_check.py`, `bench/systems_check.py`).
- A written score wins over a recording.
- The fresh test set (228 choir pieces with exact answers, in the project's files, outside git) is for measuring
  only. Do not set a rule or a limit on its pages, and do not add it to this repository. A cause that it shows is
  worked on with LitChoir's pages and then measured on it. Report its figures beside the clean copies.
  Read it before a round of rules is committed: a rule that loses notes on it is switched off, and narrowed on
  LitChoir's pages.

# New methods for hard scans (2026-11-09)

These scripts are a record of the first tests. They ran inside the test kit (in its folder `exp/`), so their paths
(`../pages`, `../tools`, `../score.py`) point into the kit. The reader in `scoreread/` replaces them.

This folder holds the experiments that followed the reader test. The test hymn is "O only Creator" (Saturday of Souls
Troparion, `saturday-of-souls-troparion`): an old copy with hand-drawn notes, one staff of two voices, 162 typed notes.
In the reader test, no reader got more than 34 % of its notes right. Nothing here changes the app or the kit's own files.

## Why the readers fall short on this page

- **copisteria** reads the notes well, but it puts them in the wrong systems. It decides the systems from the ink at
  the left of the staves. On this page the shadow of the binding stands there, so copisteria joins the 7 staves into
  3 systems and writes 5 parts side by side. When the left margin is white, or when the layout is given, it gets 86 %.
- **copisteria** also takes 11 notes on the first ledger line (C) for the note beside the staff (D). The copyist drew
  the ledger line too near the staff, and the reader takes the pitch from the distance.
- **homr** cannot read this hand: note lengths 50 % right, pitches 61 %. Cut staves, level staves, new staff lines and
  clean margins change nothing (30 % to 35 %).
- **Audiveris** cannot read this hand at all: pitches 7 % to 14 % right with every preparation.
- The staves bend near the binding (42 px, 1.4 staff spaces, on the top staff). Level staves alone did not help any
  reader much.

## Results on the test hymn (notes right, of 162)

| Method | Notes right |
|---|---:|
| homr, as in the reader test | 33 % |
| homr, with each preparation below | 30 % to 35 % |
| Audiveris, as in the reader test | 10 % |
| Audiveris, with each preparation below | 4 % to 7 % |
| copisteria, as in the reader test | 34 % |
| copisteria, one staff for each image (plain cuts) | 75 % |
| copisteria, one level staff for each image | 77 % |
| copisteria, left margin made white | 86 % |
| copisteria, layout given (`--per-system 1`) | 86 % |
| copisteria, layout given + ledger rule | 91 % |
| copisteria, level staves stacked into a clean page + ledger rule | 94 % |

The 10 notes that stay wrong are reader mistakes at 9 places on the staff: 5 notes missed where two heads touch or a
head hides in a beam, and 4 quarter notes read as half notes (one is a unison, so it counts in both parts). The typed
hymn is right at each of these places (checked on the scan).

## Results on all 31 hymns of the kit (6901 typed notes)

| Kind of score | copisteria before | Layout given | Layout given + ledger rule |
|---|---:|---:|---:|
| printed | 67 % | 68 % | 68 % |
| old copy | 76 % | 86 % | 86 % |
| by hand | 65 % | 66 % | 66 % |
| poor | 93 % | 93 % | 93 % |
| all scans | 70 % | 74 % | 74 % |

- Layout given: 4899 to 5123 notes right. No hymn gets worse. myrrh-pious-joseph goes from 37 % to 94 %, this hymn
  from 34 % to 86 %, wedding-alleluia-grechaninov from 49 % to 77 %.
- The layout is not used on a page where copisteria finds one staff twice or a number of staves that the layout does
  not divide. Without that guard, forerunner-synaxis-troparion fell from 55 % to 41 %.
- Ledger rule (only the direction "onto the ledger line"): +13 notes on three old copies (this hymn +9), -2 notes
  on each of three other hymns. It is good for this copyist's hand. It is not safe for every page yet.
- Level stacked pages on 7 one-staff old copies: 87 % with and without (4 hymns better, 2 worse). No clear gain.
- The same reader at 5 other sizes: the sizes disagree at 44 of 153 note places, and 7 of the 9 wrong places of the
  best reading are among them. That list can tell a proofreader where to look.

## Files

| File | What it does |
|---|---|
| `staves.py` | Finds each staff and the height of its five lines along the page (also where the page bends) |
| `strips.py` | Cuts the page into one image for each staff: plain or level, with new staff lines, or stacked into a page |
| `flatten.py` | Makes every staff level and keeps the page's layout |
| `cop.py` | Runs copisteria with options: `--per-system N`, `--ledger out`, `--imgsz N`; writes MusicXML and `notes.json` |
| `ledger.py` | The ledger rule |
| `run.sh` | Runs homr, copisteria or Audiveris on an input set in `in/` |
| `all.sh` | Runs a `cop.py` variant on all 38 pages (`all/<name>/`), with the layout from `../cases.json` |
| `report.py` | Scores the methods in `results/` on the test hymn with the kit's `score.py` |
| `overlay.py`, `zoom.py` | Pictures: the reading drawn over the staves, and enlarged pieces |

Commands (from this folder, after `source ../env.sh`):

```
PY=../tools/copisteria/.venv/bin/python
$PY staves.py ../pages/saturday-of-souls-troparion-p1.png staves.json staves-debug.png
$PY strips.py ../pages/saturday-of-souls-troparion-p1.png staves.json in/straight-page saturday-of-souls-troparion-p1 --straight --stack
$PY cop.py in/straight-page/saturday-of-souls-troparion-p1.png results/t-out --ledger out
$PY cop.py ../pages/saturday-of-souls-troparion-p1.png results/u-out --per-system 1 --ledger out
python3 report.py t-out u-out
bash all.sh v4 --ledger none,out && python3 ../score.py --results all --tools base v4 v4-out
```

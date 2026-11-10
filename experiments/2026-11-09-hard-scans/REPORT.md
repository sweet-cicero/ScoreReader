# New methods for hard scans: test on "O only Creator"

9 November 2026

## Result in short

- The best new method reads 94 % of the notes of the test hymn right (152 of 162). Before the test, the best reader got 34 %.
- The main cause is a layout mistake, not a reading mistake. The reader copisteria read the notes well, but it put the staves into the wrong systems.
- One fix works on the whole test set: tell copisteria how many staves each system has. Old copies go from 76 % to 86 %, and no hymn gets worse.
- The app did not change. The typed hymn is right at each place where the best reading differs from it.

## The test hymn

The test hymn is "O only Creator", the Troparion of the Saturday of Souls (Byzantine Tone 8). The page is an old copy: the notes are drawn by hand, the words are typed, and one staff holds two voices. The typed hymn in the app has 162 notes and is the answer key. In the reader test of 5 November, homr got 33 %, copisteria 34 % and Audiveris 10 % of these notes right.

## Why each reader falls short on this page

| Reader | Cause | How I measured the cause |
|---|---|---|
| copisteria | It joins staves that do not belong together. It decides the systems from the ink at the left of the staves, and the shadow of the binding stands there. It made 3 systems from 7 staves and wrote 5 parts side by side. | With the left margin made white, copisteria finds 7 systems and gets 86 %. With the layout given, it also gets 86 %. |
| copisteria | It takes 11 notes on the first ledger line (C) for the note beside the staff (D). This copyist draws the ledger line too near the staff, and the reader takes the pitch from the distance. | A rule that looks for the line through the note head corrects these notes. |
| homr | It cannot read this hand. Its note lengths are 50 % right and its pitches 61 %. | Cut staves, level staves, new staff lines and clean margins leave homr at 30 % to 35 %. |
| Audiveris | It cannot read this hand at all. Its pitches are 7 % to 14 % right. | The same preparations leave Audiveris at 4 % to 7 %. |

The staves also bend near the binding. The top staff bends 42 px, which is 1.4 staff spaces. Level staves alone gave no reader a clear gain, so the bend is not a main cause.

## Methods and results on the hymn

| Method | Notes right |
|---|---:|
| homr, as in the reader test | 33 % |
| homr, with each preparation below | 30 % to 35 % |
| Audiveris, as in the reader test | 10 % |
| Audiveris, with each preparation below | 4 % to 7 % |
| copisteria, as in the reader test | 34 % |
| copisteria, one image for each staff | 75 % |
| copisteria, one image for each staff, staves made level | 77 % |
| copisteria, left margin made white | 86 % |
| copisteria, layout given (one staff in each system) | 86 % |
| copisteria, layout given, with the ledger rule | 91 % |
| copisteria, level staves put together as a clean page, with the ledger rule | 94 % |

The three new methods:

1. **Layout given.** A person or a model tells the reader the number of staves in each system. For this hymn, the number is 1. The reader then does not look at the left margin.
2. **Ledger rule.** A note beside the staff is on a ledger line when a short level line goes through its head. The rule does not use the distance from the staff.
3. **Level stacked page.** A script finds each staff line along the page, also where the page bends. It makes each staff level and puts the staves together as a clean page without margins.

## Check on all 31 hymns of the test set

One hymn can mislead. Thus I ran the two main methods on all 38 pages of the reader test (6901 typed notes).

| Kind of score | copisteria before | Layout given | Layout given, with the ledger rule |
|---|---:|---:|---:|
| Printed | 67 % | 68 % | 68 % |
| Old copy | 76 % | 86 % | 86 % |
| By hand | 65 % | 66 % | 66 % |
| Poor | 93 % | 93 % | 93 % |
| All scans | 70 % | 74 % | 74 % |

- **Layout given:** 4899 notes right become 5123. No hymn gets worse. "Pious Joseph" goes from 37 % to 94 %, and the wedding Alleluia (Grechaninov) goes from 49 % to 77 %.
- **Ledger rule:** it adds 13 right notes on three old copies (9 of them on the test hymn). It takes 2 right notes from each of three other hymns. The rule is good for this copyist's hand. The rule is not safe for every page.
- **Level stacked page:** on 7 old copies with one staff in each system, the result is 87 % with and without this method. Four hymns get better and two get worse. There is no clear gain.

## What stays wrong

The best reading has 10 wrong notes at 9 places on the staff. I looked at each place on the scan. Each one is a mistake of the reader, and the typed hymn is right.

- 5 notes are missing. Four are in places where two note heads touch. One is a half note that hides in a beam.
- 4 quarter notes are read as half notes. One of them is a unison, so it counts in both parts.

A second look can find most of these places. I ran copisteria at five other sizes of the image. Each other size is worse than the usual size. But the sizes disagree at 44 of the 153 note places, and 7 of the 9 wrong places are among these 44. A proofreader can thus look at 44 places first.

## Limits

- The layout method does not work on a page where copisteria finds one hand-drawn staff twice. A guard sees this condition and lets copisteria decide as before. Without the guard, one hymn fell from 55 % to 41 %. With the guard, four hymns lose a possible gain. The largest is "It is truly meet" by Zakkak, from 65 % to 74 %.
- The 94 % comes from one hymn. Only the layout method has a result on the full test set.
- These methods do not read the words. Only Audiveris reads words, and it read 16 % of the words on old copies in the reader test.

## Recommendation

1. Use copisteria with the layout given for the draft of each old copy. This step needs one number for each hymn.
2. Use the ledger rule and the list of places where the sizes disagree as marks for the proofreader. Do not let them change notes without a check.
3. Do not prepare images for homr or Audiveris on hand-drawn pages.

A possible next step is a script that removes the staff that copisteria finds twice. It can give the layout method to the pages that the guard stops now.

## Where the work is

All files are in `tmp/omr-test/exp/` in the project folder on the PC. That folder is not in git. `README.md` there lists each script and the commands.

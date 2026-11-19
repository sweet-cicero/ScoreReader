# ScoreReader worklog

This file is the record of the work, round by round: what was measured on each set of test pages, what the reader
cannot do yet, and what comes next. A round is one pull request of rules, and it has the number of its pull
request. [README.md](../README.md) says what ScoreReader is and how it works; the figures of each round are written
down here.

## Results on every score of LitChoir (the wide test)

The wide test reads every score of the app that has a typed hymn to compare with: 369 scores on 657 pages, 516 of
them scans. 364 are counted: the page of 5 scans holds another version than the typed hymn. Notes right means pitch
and length both right. The count is of the notes that the pages show: 5,934 typed notes that no page prints are
listed apart. Most are recited syllables and the held notes of an ison that the page does not mark; 343 are a
refrain or a repeat that the page prints once and the typed hymn writes out again, and 12 more stand in a
system that one scan shows only in part (see round 37). 218 typed notes that a part
sings from another part's staff are not compared. Each score is read as the `hymn` command reads it: its pages in
order, with one vote for its key. Where a typed hymn gives a note otherwise than its page prints, the note counts as
the page prints it (since 15 November 2026, see below; 77 notes so far, 73 of them on the clean copies).

| Kind of score | Scores | Notes right | At 99 % or more | At 90 % or more | Under 50 % |
|---|---:|---:|---:|---:|---:|
| PDFs that notation software wrote (read from their drawing) | 70 | 99.3 % (20,016 of 20,163) | 53 | 70 | 0 |
| Scans | 294 | 83.7 % (58,251 of 69,556) | 36 | 115 | 20 |
| All | 364 | 87.2 % (78,267 of 89,719) | 89 | 185 | 20 |

The first milestone was 99 % on clean copies until 17 November 2026; since then it is clean copies that are read
whole, every note and every syllable of each score, with no note that is not there (the owner: "the clean copies
should be consistently perfect"). The copies by hand keep 99 %. After round 60, 25 of the 78 counted clean scores
read every printed note, 35 every syllable, 18 every note and syllable, 21 have no note that is not there, and 13 are whole
in all three (as after rounds 57 to 59; 24, 35, 18, 21 and 13 after round 56; 24, 35, 18, 19 and 13 after round 55; 24, 35, 18, 18 and 13 after round 54; 23, 35, 17, 18 and 12 after round 53; 22, 35, 16, 18 and 12 after round 52; 21, 35, 15, 16 and 11 after round 51; 20, 32, 12, 16 and 10 after round 50; 19, 31, 10, 15 and 8 after round 49; 17, 31, 9, 13 and 5 after rounds 47 and 48; 15, 30, 9, 10 and 3 after round 46). 668 printed notes and 195 syllables are lacking, and 682 notes are read that are not there (671, 195 and 686 after round 59; 675, 195 and 689 after round 58; 679, 195 and 690 after round 57; 681, 195 and 692 after round 56, by the list of the notes by the page of its time; 681, 195 and 726 after round 55; 697, 195 and 736 after round 54; 699, 195 and 738 after round 53; 706, 196 and 742 after round 52; 709, 197 and 769 after round 51; 712, 206 and 783 after round 50; 713, 209 and 784 after round 49; 719, 209 and 794 after round 48; 707, 209 and 837 after round 47, by a count that hid 15 lost notes: see round 48). The clean copies are the scan scores with printed notes and words and crisp ink. 81 were
sorted as clean and 78 are counted: one has words lettered by hand, was sorted wrongly and counts with the copies
by hand now, and the page of two holds another version than the typed hymn. The other scans come after the
milestone: 26 printed but thick, blurred or grey copies, and 190 with notes or words by hand.

| Scans by copy | Scores | Notes right | At 99 % or more | At 90 % or more | Syllables right, own letter reader | Syllables right, with Tesseract and a list of words | Whole words right, with Tesseract and a list of words |
|---|---:|---:|---:|---:|---:|---:|---:|
| Clean print | 78 | 97.0 % (21,915 of 22,585) | 35 | 74 | 49.9 % (3,286 of 6,584) | 96.9 % (6,044 of 6,239) | 94.8 % (4,280 of 4,515) |
| Thick or grey print | 26 | 82.0 % (6,919 of 8,440) | 0 | 10 | 32.9 % (658 of 2,000) | 88.8 % (1,759 of 1,980) | 87.2 % (1,196 of 1,371) |
| By hand | 190 | 76.3 % (29,417 of 38,531) | 1 | 31 | 37.7 % (5,401 of 14,345) | 84.0 % (12,066 of 14,356) | 81.3 % (8,413 of 10,343) |

- A round is one pull request of rules, and it has the number of its pull request. The figures count every typed note of a part since round 18, the notes of a chord too; until
  then one note of a chord was counted for each part of a staff. The rounds below it give their figures by the
  count of their time, and as typed (see the count by the page below). Of the clean scores, 65 are at 95 % or more. 522 more notes are needed
  for 99 % of each clean copy and 668 for every printed note; 13 scores lack one to three notes (525, 671 and 13 after round 59; 529, 675 and 13 after round 58; 533, 679 and 12 after round 57; 533, 681 and 13 after round 56; 533, 681 and 13 after round 55; 548, 697 and 13 after round 54; 549, 699 and 14 after round 53; 555, 706 and 15 after round 52; 561, 719 and 19 after round 48, by the count of round 48, which no longer sets a lost note of a clean copy apart as recited; 550, 707 and 18 by the count before). The syllables of the own letter reader were last counted before round 47. The mistakes that are left are many small causes;
  the largest that were found
  since: two voices a second apart that the print sets as one blot of ink brought 41 notes on the clean copies
  in round 19, and a fault of one pixel in the thin ink of the layers brought 32 (42 gained, 10 lost) in round 24.
  Round 25, on the two clean scores that lack most, brought 21; round 26
  brought 45 (sixteenths under two beams that a staff line joins, a second dot, and a bow from syllable to syllable); round 27
  brought 18: a whole note beside a half note a second away, a head on top of a ledger line near the staff, and a flag that is no flat; round 28
  brought 11: a tie that lies in a staff line, and the end of a bold slur that is no second stem; round 29
  brought 12: a half note and a whole note on a line whose hole the print filled but for one speck, and a bow that ends in a staff line; round 30
  brought 4: a tie over the end of a page; and round 31
  brought 11: a bow that lies on a beam, one dot between two heads, a slur between two stem ends, and the slit of a half note on a ledger line;
  and round 33 brought 8: a dash beside a head that is its dot, and a bold bow that is one piece of ink with its whole notes;
  and round 41 brought 8: two half notes a third apart that touch on their lines, and two heads a second apart that overlap across their stems;
  and round 42 brought 12: a filled head whose stem the scan lost;
  and round 43 brought 4: the tip of a tie that was read as a dot;
  and round 44 brought 21: the inside of a printed half note that is a ragged slit;
  and round 45 brought 5: a head of a chord that was left without the stem that it shares;
  and round 46 brought 12: the pale speck in the filled heads of one engraving (10), and two half notes of that score that the page prints and the hymn types as quarters;
  and round 47 brought 53 (59 gained and 6 lost): four rules for the notes (a pale stem, closed paper that stands upright and is no head, the loop of a flag, a ledger line of two dashes), staves that are followed past the ends that the comb gives them, and the stored pages built anew with the code of today;
  and round 48 brought 3, by a sign of common time that is no longer read as two notes;
  and round 49 brought 6: two specks in the rows of a staff line that are no slit of a half note, a line of the scan through a system, and a short tie that stands free;
  and round 50 brought 1: a slur that passes the end of a stem;
  and round 51 brought 3: the curl of a flag that was read as a small note;
  and round 52 brought 1 (3 gained and 2 lost): a cell between a staff line and a slanted stroke that was read as a hollow head;
  and round 53 brought 7: a cell between the stem of the note before and a filled head (6), and a bow that swells in its middle;
  and round 54 brought 2: a half note whose ledger line is faint inside its head;
  and round 55 brought 8: 9 by the list of the notes that the page holds where the typed hymn strikes them again, and the rules lost 1 that had counted by chance;
  and round 56 brought none: 2 by the list (two notes of a chord that the typed hymn leaves out), and the rules lost 2 that false notes had held in place;
  and round 57 brought 4: the quarter note of one voice on the head of another voice's beamed eighth (its list of the notes by the page took 4 notes of the clean copies from the reading before it, and the rule brings 2 of them back);
  and round 58 brought 4: the middle head of a column on one stem line that goes with the neighbour of its own kind (1), and a half note on a line whose inside lies flat (3);
  and round 59 brought 4: printed signs that touch their head or a staff line (a flat whose foot runs into a line, a heavy sharp whose stroke runs into a line, a heavy sharp whose middle was read as a note);
  and round 60 brought 3: a natural whose closed middle was read as a half note with the natural's right stroke as its stem.
  The reader also writes 684 notes on the clean copies that are not there (5,039 on
  all scores; 682 with the two at the place that a hand changed counted apart; round 60 took 4 of them away, the middles of naturals, round 59 took 3 of them away, the middles of heavy sharps, round 58 took 1 of them away, round 57 took 4 of them away, and its list of the notes by the page counts 2 more that the reading before it wrote (an alto's second eighth that the page does not print); round 56 took 34 of them away, 32 by its rules (two whole notes side by side, a beam or a slur at the end of another note's stem, the pieces of a time signature) and 2 by the list, round 55 took 10 of them away, the loops of long flags and a half note on a ledger line that was read as two, round 54 2, round 53 4); rounds 20 to 24 took 49, 67, 35, 3 and 19 of them away on the clean copies, rounds 25 and 26 none (round 26 counts 6 more, in one score), round 27 3, round 28 13, round 29 12, round 30 5, round 31 1, and round 33 2 (round 41 counts 1 more: a note that is read with a wrong length now and was not read before; round 42 counts 4 more, of the same kind; round 43 took 7 away, the second halves of four ties that are joined now; round 44 took 5 away, pieces of the rim of a half note that were read as notes; round 45 left the count as it was; round 46 counts 1 fewer, a note that the checked list holds now; round 47 took 45 away, most of them closed paper that had been read as a half note; round 48 took 43 away, the pieces of a thick bar line and of the bold sign of common time; round 49 took 10 away, the pieces of a line of the scan and three quarter rests; round 50 took 1 away; round 51 took 14 away, the curls of flags and the marks at the bar line that ends a staff; round 52 took 27 away, most of them cells between a staff line and a stroke that had been read as half notes). Of 30 mistakes drawn by lot and looked at
  on the page in round 12,
  8 are a hollow head and a filled head mixed up, 4 a dot, 4 a tie or a slur, 4 a beam, 4 a sign, and 6 one of a
  kind (a note that a pencil crossed out, a typed hymn that differs from its page). Two fine engravings held about
  240 of the 1,269 notes that were lost then (1,017 now, with the notes of chords counted). An earlier count said that a quarter of the mistakes are
  the scorer lining a staff up with the wrong part: the tool behind that count lined the notes up in its own way,
  and it is not held any more.
- Words with the optional Tesseract step, its larger language files as further opinions (since round 39) and a
  list of words: 25,522 of 28,680 syllables are right (89.0 %,
  counted by the page since round 35; 25,352 of 28,700 as typed):
  92.6 % on the software-made PDFs (their words are text in the PDF; Tesseract is not used there), and 88.0 % on
  the scans (19,869 of 22,575; rounds 54 and 55 changed no syllable, round 53 took 3: a rule for a stray word under the clef gains 1 syllable on the clean copies and loses 3 on one copy by hand, and 1 goes with a note; round 52 brought 3, by the word O beside a bracket and with the notes, round 51 brought 27, by a word that every reading of its row holds alike and with the notes, round 50 brought 10 by two rules for the words and 1 by the list of the words by the page, round 48 brought 1 with the notes, round 47 brought 167 with the notes, by the staves and the systems of copies by hand that it reads now, round 44 lost 6 of them with the notes of one copy by hand, round 40 brought 68, round 39 brought 196, the rules of round 37 brought 25 and its count by the page 26, the
  rules of round 36 brought 471, the rules of round 35 brought 138 and
  the count by the page 139, round 34 brought 63). Before round 34 these were 21 syllables fewer than in round 17 with the same words read: the
  words are compared in the layout that the count of the notes chooses for a score, and the scorer sets a few
  scores in another layout or on another part of their pages now. On the clean copies 96.7 % of the syllables and 94.5 % of the whole words are
  right, and 32 of the 78 scores have 99 % of their syllables (31 before round 47, 28 before round 39, 25 before round 36, 20 before round 35, 15 in round 10, 4 in round 9); 191 syllables
  are lacking for 99 % of each clean score (195 before round 47, 200 before round 40, 227 before round 39, 285 before round 37, 366 before round 36). The
  list of words is made from the typed hymns of the app without the hymn that is read and its other scores, so no
  score is read with its own text. Without a list the scans have about 910 fewer of these syllables and
  about 1,170 fewer whole words (quick count, see the rounds of the words below).
  With the own letter reader, which uses no model, the scans have about 40 %; its column in the table was measured
  in round 7 and not again since.
- The count of the syllables changed in round 10, and that alone moved the figures: the syllables of a refrain
  that the page prints once and the typed hymn writes out again are listed apart now, as the notes of such a
  refrain already were (150 syllables on 2 scores). Counted the new way, the clean copies stood at 85.0 % before
  that round (5,302 of 6,240; 83.3 % by the old count) and all scores at 78.2 % (22,449 of 28,697).
- The words are counted in three ways. Syllables right: the typed syllables that the reader wrote, in the typed
  order. Whole words right: the same for words, each joined from its syllables at the hyphens that the reader
  read; a word counts only when all of it is right, and a word that the page prints with no hyphen over two notes
  is still one word. Letters in order (90 % on the scans with Tesseract, 96 % on the clean copies): a lenient
  count, since two unlike hymn texts of one length share two fifths of their letters in order. Under which note a syllable stands is not
  scored yet.
- A note can hold several syllables (a reciting note, or a syllable whose note was not read), and the words of
  such a note are counted one by one, in the reading and in the typed hymn. The figures of the own letter reader
  on the thick copies and the copies by hand are from before this count.
- Some typed syllables stand on no page: a refrain that the page prints once and the typed hymn writes out after
  each verse. The two clean scores that miss the most syllables are of this kind. Such syllables are not counted
  apart yet, as the notes of a repeat are.
- The sorting into clean, thick and by hand was done by eye from the first system of each score. Some typed hymns
  differ from their page in ways that the scorer was not told, and count as wrong: a tie that the page prints and
  the typed hymn does not, a refrain, a note that a pencil changed.
- The scorer gives each staff of a page the typed parts that it lines up with best. A small change in the reading
  can turn that choice: one hymn lost 16 notes in an earlier round because one wrong note was no longer
  read, and the scorer then took its staff for one part and not for two.
- The figures count parts, not staves. A staff that holds two parts is split: the top note of each chord goes to
  the upper part and the bottom note to the lower. Until round 17 that was all: of a typed part that
  divides only the top or the bottom note was counted, and a false note in a chord took the place of the true
  one. Now the other notes of a chord are counted after that line-up (see the round of the count below). The line-up itself
  has no sense of time: it compares the notes of a part in their order.
- Round 60 (19 November 2026): a natural whose closed middle is read as a half note.

  Round 59 left a natural before a chord in two prints of pascha-angel-cried: the paper that the natural's
  strokes and bars close in was read as a hollow head with the natural's right stroke as its stem, that head lay
  on the sign and the natural was not read, and the whole note after the sign took the same stroke as its stem
  and was read as a half note. Two halves of one rule for the signs of notes (notes gained and lost):

  | Rule | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | A hollow head whose middle lies between the two strokes of a natural, and each of whose stems is one of them, is the natural's middle and no head (`signs.NATURAL_OWN`) | 1 and 0 | 1 and 1 | no page differs |
  | ... and the right stroke of such a natural is no stem of a hollow head after it where it is that head's only stem and another head of its column has a stem (`signs.NATURAL_LONE`; before, only where the head had a second stem) | 3 and 0 | 3 and 1 | no page differs |

  - The second half alone changes no page: it acts only on a natural that the first half lets the signs read.
  - Each of the 3 new naturals was looked at on the page (pascha-angel-cried, second scan, twice, and
    pascha-angel-cried-believers): all are true, and the false head in each went. The note that the rule loses
    in pascha-angel-cried-believers was a false note that had counted by chance: the middle of the natural was
    read as the soprano's F sharp, and the soprano's true half note beside it is read as a quarter note a step
    off. That print draws the alto's D as a whole note with no stem where the hymn types two half notes; the
    rule reads the D now (an E flat before), and its length is the page's whole note.

  The full reading of the 3 pages that the round changes, with the words (`w284v1`, against `w283v1`): clean
  copies 21,915 of 22,585 notes (97.0 %; 3 gained, none lost; 21,858 of 22,606 as typed), 35 scores at 99 %, 65
  at 95 %; all scores 78,267 of 89,719 (3 gained, 1 lost; 89 at 99 %), staff by staff 3 gained and none lost (3
  and none on the clean copies); 684 notes that are not there on the clean copies (682 with the place that a hand
  changed apart) and 5,039 on all scores. No syllable changed. 25 clean scores read every printed note, 35 every
  syllable, 18 both, 21 have no note that is not there, 13 are whole in all three, and 13 lack one to three
  notes. No page of the fresh set differs (39,879 of 41,761 notes). The kit reads as before (6224 by parts).

  Counted and left: the dots of the clean copies (25 printed dots not read and 15 read where none is printed,
  each looked at): a dot that a print sets on one head of a chord of half notes and the rule that makes the heads
  of a chord as long as each other, a dot that touches the head, two dots one over the other beside two heads, a
  bump of a staff line read as a dot, a dot that one print sets high in the space over its head, and a page
  that prints no dot where the hymn types a dotted note (two prints); none of them comes to more than three notes.
- Round 59 (19 November 2026): printed signs that touch their head or a staff line.

  Of the 55 notes that the clean copies read a semitone off after round 58 (pairs that the sheets line up
  crosswise left out), each was looked at on the page: about 22 have a printed sign that is not read or is read
  as another sign (8 sharps, 7 flats, 4 naturals, 3 misread), and most of those signs touch their head or a
  staff line. The others are heads read a place off between E and F or B and C, and signs of a bar that were not
  carried. Three rules for the signs of notes, each alone (notes gained and lost):

  | Rule | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | A flat whose lowest rows hold no ink of its own is cut at its last row of ink, and is a flat where it is still 1.5 staff spaces high (`starts.FLAT_FOOT`) | 2 and 0 | 10 and 0 | no page differs |
  | The ends of a heavy sharp whose two strokes are one mark are its first and its last row of ink without the staff lines (`signs.JOINED_ENDS`, first form) | 1 and 0 | 1 and 2 | no page differs |
  | ... and such a sign lies before its head, not in its box (the rule as it is) | 1 and 0 | 1 and 1 | no page differs |
  | The middle of a heavy sharp that was read as a head, with one of the sharp's strokes as its stem, is no head (`signs.JOINED_HEAD`) | 1 and 0 | 5 and 0, 10 notes that are not there fewer | no page differs |

  - The stroke of a sign is followed past its own ink into a staff line, over a gap of paper, and the tests of
    its ends then read paper there: the foot of a flat holds no ink of its own, and the top of a heavy sharp shows
    no stroke at either side. The census of the clean pages (the flats of the notes, cut at the last row of their
    ink) gave 8 new flats: 4 true ones, 2 flats of a key signature that stand before the first note, and 2 filled
    heads with ink over them, about 1.2 staff spaces high where a flat is two. Each of the 9 new flats of the rule
    on all pages was looked at: all are true.
  - The first form of the sharp's ends gave 4 true sharps (pascha-angel-cried in its second scan twice,
    pascha-angel-cried-lady, trisagion-tchaikovsky in its second scan) and one false one: two faint hollow heads
    one over the other on a copy by hand (orthros-today-is-salvation, second scan). A sign whose ends were cut
    must stand before its head, not in its box: the older test for a breve (`SHARP_JOINED[4]`) holds for a head
    with a stem too then. The one note that the rule still loses is right by the sign: in
    pascha-angel-cried-lady (and in pascha-angel-cried, second scan, where it is hidden by a gain) the sharp
    holds for the bar, and a natural later in the bar is not read, because its closed middle is read as a half
    note with its right stroke as the stem (the next round).
  - A heavy sharp whose middle closed is read as a filled head, and one of its strokes as that head's stem: the
    stem hides the stroke from the signs. The guard for a sharp of two strokes (`SHARP_HEAD`) does not see a
    sharp whose two strokes are one mark. Each of the 6 new signs was looked at: 5 sharps of heavy prints and a
    flat whose bowl had been read as a head, all true; the false heads went with them.

  The full reading of the 18 pages that the round changes, with the words (`w283v1`, against `w278v1`): clean
  copies 21,912 of 22,585 notes (97.0 %; 4 gained, none lost; 21,855 of 22,606 as typed), 35 scores at 99 %, 65
  at 95 %; all scores 78,265 of 89,719 (15 gained, none lost; 89 at 99 %), staff by staff 16 gained and 1 lost (4
  and none on the clean copies); 688 notes that are not there on the clean copies (686 with the place that a hand
  changed apart) and 5,045 on all scores. No syllable changed. 25 clean scores read every printed note, 35 every
  syllable, 18 both, 21 have no note that is not there, 13 are whole in all three, and 13 lack one to three
  notes. No page of the fresh set differs (39,879 of 41,761 notes). The kit reads 6224 notes by parts (6222
  before) and 5794 staff by staff (5792): forerunner-synaxis-troparion and lamentations-troparia gain a flat.

  Counted and left: the natural whose closed middle is read as a half note (above); a sharp whose stroke is
  followed into a slur (cherubic-lvovsky); a flat whose bowl is cut from its stroke and glued to its head
  (orthros-apichima); a flat whose stroke is as thick as a heavy print's stem (wedding-psalm-128); the small
  naturals of nativity-kontakion, joined with the stem before them; and naturals glued to their heads that are read
  as flats (pascha-hypakoe, cherubic-znamenny).
- Round 58 (18 November 2026): the middle head of a column on one stem line, and a half note on a line whose
  inside lies flat.

  The round took up two causes of the clean scores that lack one to three notes. Each rule alone (notes gained
  and lost); the forms of the first rule in order:

  | Rule | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | The middle head of a column on one stem line goes with the neighbour of its own kind (`symbols.MIDDLE_KIND`) | 1 and 1 | 5 and 1 | none and none, 8 eighth notes that are not there |
  | ... where the neighbour of the other kind holds a stem that leaves the column on its side and ends 1.8 staff spaces from it or more (`MIDDLE_LEAVES`) | 1 and 0 | 2 and 0 | no page differs |
  | ... where each of the three heads is surely filled or surely hollow (`MIDDLE_SURE`: a share of paper under 0.08, or 0.16 or more) | 1 and 0 | 2 and 0 | no page differs |
  | ... and not where the neighbour of its own kind holds a stem on that side that ends within 1.8 staff spaces (`MIDDLE_OWN`; the rule as it is) | 1 and 0 | 1 and 0 | no page differs |
  | A half note on a line whose inside lies flat (`symbols.LINE_HALVES`) | 3 and 0 | 8 and 2 | no page differs |

  - The middle head. Heads of two voices that stand close share one line of ink: the upper voice's stem goes
    up, the lower voice's stem goes down. A head in the middle of such a column went up or down by its place
    against the column's centre, a few pixels. One stem carries heads of one length, so where no other head of
    the column stands within 0.4 staff spaces of its height, the middle head goes with the neighbour of its own
    kind (a filled head between a hollow head over it and a filled head under it is the lower voice's). On the
    fresh set the first form made 8 eighth notes that are not there: the loop of a flag at the end of a stem is
    a hollow mark too, with a stem down, and the middle head took its flag. The stem of the other kind must
    leave the column. On a worn print a filled head holds a speck of paper (one of 0.11), so only kinds that
    are sure count. The gain is a note of extra-rejoice-o-virgin-rachmaninov.
  - The third form gained a note of palm-hosanna (second scan) by the count by parts, and lost 4 there staff by
    staff. On the page it was wrong: the end of a tie that runs into the chord is a short stroke at its side,
    read as a stem down, the cell at the tie's end is a hollow mark, and the quarter note took the flag of that
    stroke. The head goes to a stem only where that stem leaves the column as the other one does.
  - The flat half note. A filled head with a stem and a staff line through it is a half note where a speck of
    paper of at least 0.012 square staff spaces is closed in over the line and one under it, the middle of each
    out of the rows of the line and at most 0.35 staff spaces from it, the two over each other: the inside of a
    half note that lies flat, cut in two by the line. The slit of a half note that leans was read before
    (`LINE_SLIT`), and the specks of a worn filled head lie in the rows of the line (`LINE_OUT`).
  - Each of the 19 heads where it acts was looked at. They are true half notes but three: the paper inside the
    4 of a time signature of theophany-kontakion (both scans), read as notes that are not there before and not
    read now. The 2 notes that ascension-antiphon-moderato loses come from a typewritten half note that is
    read right now: the scorer's line-up slipped on misread notes before it. A true half note of
    theophany-troparion (second scan) is then taken for the loop of a flag, because the stem of the note above
    it passes through it on one line (`LOOP_NEAR`), and no count moves: left. The count of the page's worn
    heads (`slit_page`) does not part these heads from worn filled heads.

  The full reading of the 18 pages that the round changes, with the words (`w278v1`, against `w271v1`): clean
  copies 21,908 of 22,585 notes (97.0 %; 4 gained, none lost; 21,851 of 22,606 as typed), 35 scores at 99 %, 64
  at 95 %; all scores 78,250 of 89,719 (9 gained, 2 lost; 89 at 99 %), staff by staff 8 gained and 1 lost (4 and
  none on the clean copies); 691 notes that are not there on the clean copies (689 with the place that a hand
  changed apart) and 5,058 on all scores. No syllable changed. 25 clean scores read every printed note, 35 every
  syllable, 18 both, 21 have no note that is not there, 13 are whole in all three, and 13 lack one to three
  notes (12 before). No page of the fresh set differs (39,879 of 41,761 notes). The kit is as it was (6222 by
  parts, 5792 staff by staff).

  Counted and left: whole notes read as half notes (64 places on the clean copies, with strokes of many kinds);
  20 ties that the clean copies do not read, each a cause of its own (bows of communion-lords-prayer into a
  staff line across a bar line, long bows of pascha-angel-cried in its second scan to the end of a stem); the
  11 clean scores with one note that is not there, six of them at a place of the page, all different (a whole
  note that touches its twin, an arrow by hand, a word, the end of a bracket, the joint of a chord); and 56
  notes of the clean copies read a semitone off, of which about 11 of the 40 looked at have a printed sign
  before the head that is not read (flats whose foot stands on a staff line).
- Round 57 (18 November 2026): a head that two voices share, with a beam at one stem and a stem without a flag
  at the other.

  The round took up the rule that round 56 counted and left. Since round 19 a head with two stems gives the
  flags of its one stem to the other stem too, because a hand draws the flag of a note that two voices sing at
  one stem only. Where one stem is beamed and the other ends in paper, the page prints two notes: the beamed
  voice's eighth and the other voice's quarter. One print sets the alto's quarter note so, on the head of the
  soprano's first eighth. `symbols.SHARED_TAILS = 'flags'` keeps the beam at its own stem there. Each form alone
  (notes gained and lost, by the list of the notes by the page of this round):

  | Form | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | The beam stays at its own stem (the form of round 56, by the list of its time) | 4 and 6 | 25 and 23 | 64 and 0 |
  | ... where the other stem ends in paper (`SHARED_FREE`: at most 0.02 ink beside its end, 1.5 staff spaces to each side, from 0.4 staff spaces before the end to 0.6 past it; the staff lines count) | 6 and 0 | 13 and 1 | 62 and 0 |
  | ... and where the beam goes on from the shared head to the next note (the rule as it is) | 4 and 0 | 11 and 0, 4 notes that are not there fewer | 62 and 0, 4 notes that are not there fewer |

  - Each of the 77 places of the first form was looked at. At the true ones the free stem ends in paper. At
    the false ones ink stands beside its end: a hand's beam drawn as a box that the reader misses at that stem,
    a slanted beam, or a flag.
  - The list of the notes by the page knows a typed note that the page does not print for a part now (`drop`:
    the part holds the note before it, and the list gives that note the page's length). wedding-isaiah and
    hierarchical-ye-holy-martyrs (one print, a clean copy and a thick copy) print the alto twice as a quarter
    note under the soprano's two eighths, and their typed hymns sing the eighths in unison: 8 notes on the
    list, each looked at four times the size. `AS_TYPED=1` gives the figures of round 56 exactly. By the page
    the reading before the round loses 8 notes (4 on the clean copies), and the rule brings 3 of them back
    (wedding-isaiah 2, hierarchical-ye-holy-martyrs 1: both of its places are read right, and the alto's note
    before the second one is read with a false dot, which moves its line-up).
  - The beam that goes on: a copy by hand (resurrection-troparion-5, third scan) draws the ison's eighth on the
    last head of the melody's beam with a stem and no flag. The next head is both voices' again, so a quarter
    does not fit there: the hand left the flag out. Where the shared head ends its beam, the rule does not act.
    holy-saturday-koinonikon's 2 notes (a clean copy) went with that guard: a slur at the end of the up stem
    was read there as a beam that comes from the left, the rule was right by chance (both voices sing a quarter
    note in unison, and neither stem has a beam), and that page needs a rule of its own.
  - The rule acts on 16 heads of LitChoir's pages, each looked at: the gains are the alto's quarter notes of
    wedding-isaiah, memorial-troparia (second scan), dormition-koinonikon, presentation-theotokos-koinonikon and
    hierarchical-ye-holy-martyrs, and a typewritten copy (palm-hosanna, third scan), whose upper staff then reads
    two quarter notes by the column. Two pages whose scores are not counted (blessed-be-zakkak, and
    lent-thy-pure-image in its second scan) read the alto's quarter note as their page prints it, and the
    kit's megalynarion-zakkak a soprano's quarter note (see the kit below). On a copy by hand of pascha-al-masih-qam the free stem has a small flag
    0.7 staff spaces before its end, outside the window: the rule reads a quarter note there, and no count
    moves. memorial-memory-eternal counts 1 more note that is not there: a thick stroke before a head was read
    as the head's stem down, and that false note had the length of the true one before. On the fresh set one
    piece prints triplets with a beam at both stems of a head: each stem keeps its own beams now (eighths, where
    a slur under the lower beam had made sixteenths), and the triplet is not read either way.

  The full reading of the 14 pages that the round changes, with the words (`w271v1`, against `w269v1` scored
  with the list of this round): clean copies 21,904 of 22,585 notes (97.0 %; 4 gained, none lost; 21,847 of
  22,606 as typed, 2 fewer: the typed hymn of wedding-isaiah sings the eighths), 35 scores at 99 %, 64 at 95 %;
  all scores 78,243 of 89,719 (11 gained, none lost; 89 at 99 %); 692 notes that are not there on the clean
  copies (690 with the place that a hand changed apart) and 5,061 on all scores. No syllable changed. 25 clean
  scores read every printed note (memorial-troparia, second scan, is new), 35 every syllable, 18 both, 21 have
  no note that is not there, 13 are whole in all three, and 12 lack one to three notes. The fresh set reads
  39,879 of 41,761 notes (95.5 %; 62 gained, none lost; 95 pieces at 99 %), with the words as before. The kit
  is as it was (6222 by parts, 5792 staff by staff).
- Round 56 (18 November 2026): two whole notes side by side, a beam or a slur at the end of another note's stem,
  and the pieces of a time signature, read as notes that are not there.

  The round went on with the notes that the clean copies read and do not print. Three rules for the notes are
  in, one was counted and left for the next round, and the list of the notes by the page learned a new kind of
  note. Each rule alone (notes gained and lost):

  | Rule | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | `music.WHOLE_TWIN`: two whole notes without stems side by side, on one pitch or a second apart, their middles at most 1.9 staff spaces apart and at most 0.3 staff spaces of paper between them, begin together | 0 and 2, 26 notes that are not there fewer | 0 and 2, 42 notes that are not there fewer | 0 and 0, 5 notes that are not there fewer |
  | `symbols.STEM_END_MARK`: a filled mark that holds the end of the stem of another head (1.5 staff spaces away or more), at least 1.4 times as wide as the page's heads and at most 0.85 times as high, is that stem's beam or a slur over its end | 0 and 0, 4 notes that are not there fewer | 0 and 0, 8 notes that are not there fewer | 2 and 6 by parts (staff by staff as before), 6 notes that are not there fewer |
  | `meter.TIME_STACK`: the stem of the lower of two numbers that touch may stand at up to 0.85 of their width (0.81 before) | 0 and 0, 2 notes that are not there fewer | 0 and 0, 10 notes that are not there fewer | no page differs |

  - Several prints set the whole notes of two voices in unison or a second apart side by side (10 clean scores,
    among them pascha-christ-is-risen-appalachian and extra-come-bless, and cherubic-kastorsky in two scans). The reader took the second
    for a note that begins after the first, and the count had it as a note that is not there: one voice cannot
    hold two whole notes in one bar. Such a pair is one column now. The 2 notes that the clean copies lose are
    mistakes that the second note had hidden: in liturgy-one-is-holy (second scan) the second note of a pair is
    read a step off, and in extra-beatitudes a joint between two whole notes that touch is read as a third head
    and becomes the top of the chord. trisagion-jerusalem sets 2 more typed notes of its recitation apart (36 to
    38): the second whole note of a pair at the start of a recited line had stood for one of them, and its page
    holds an empty staff with the words over it there.
  - A thick beam that slants across a staff line, and a slur that passes the end of a stem, are cut out as one
    piece with the line and were read as filled heads. A census of every filled mark of LitChoir's pages that
    holds the end of another note's stem parted them by their height: the true heads are 1.3 times as high as
    the page's heads or more, the beams and slurs 0.85 or less. On LitChoir the rule took exactly the marks of
    the census, on 8 pages, each looked at. On the fresh set it took 9 marks, all pieces of beams; one piece
    (ro-lit-ca-pe-imparatul) loses 6 notes by parts and none staff by staff. Two false notes of wrong pitch had
    held the line-up of its two upper parts, and without them the count lines up three notes of each part
    otherwise: its line-up weighs a wrong pitch at half a missed note. No note of the page is new and every
    mark that went is a piece of a beam, so the rule stays, as `meter.COMMON_BOLD` did in round 48.
  - One engraving sets the stem of the 4 of a time signature at 0.83 of the width of the two numbers where
    they touch, past the limit that keeps a bar line and the stem of a note out (forerunner-nativity-apolytikion
    and 7 more pages). Each of the 8 pages that change loses a piece of a time signature, and nothing
    else.
  - The list of the notes by the page knows a note that the page prints and the typed hymn leaves out (a note
    of a chord) now: the last chord of the second system of trisagion-vitoshinsky prints six whole notes where
    the hymn types four, and the same cadence is typed with its six notes twice on the same pages. The scorer
    counts such a note as printed; `AS_TYPED=1` gives the figures of the round before exactly. Both notes are
    read: 2 notes more on the clean copies, 2 gained.
  - Counted and left for the next round: a shared head whose beam stays at its own stem
    (`symbols.SHARED_TAILS = 'flags'`: the other voice's stem ends free and is a quarter note). It gained 64
    notes on the fresh set and lost none; on LitChoir it gained 25 and lost 23 (4 and 6 on the clean copies).
    Where it loses on a clean copy, the page mostly agrees with it: wedding-isaiah and
    hierarchical-ye-holy-martyrs (one print) print the alto as a quarter note under the soprano's eighths, and
    their typed hymns sing the eighths in unison. Elsewhere the reader misses the beam of the second stem (a
    copy by hand that draws its beams as boxes, and one clean page). The rule waits for a look at each of its
    77 places and for a kind of the list for a typed note that the page does not print for its part.
  - Also looked at and left: the paper between a bar line and a chord of two whole notes, closed in by two
    staff lines and read as part of the head (communion-lords-prayer; `symbols.CELL_OUT` takes such paper only
    beside a filled head, and a census of the clean pages found one such place), and a chord of quarter notes
    that the end of a tie and a bar line join into one piece too wide for a head.

  The pages were read again with Tesseract where a rule changes them: 38 pages of LitChoir and 9 of the fresh
  set. The full reading agrees with the readings of the rules alone: the clean copies gain no note and lose 2,
  all scores gain none and lose 2 (staff by staff none and none on the clean copies, none and 2 on all scores),
  and no syllable changes. No score changes its layout; ascension-troparion (second scan) moves its window
  with no note changed, and trisagion-jerusalem sets 2 notes apart. The notes that are not there fall by 32 on
  the clean copies (726 to 694, after the 2 that the list took), by 66 on all scores (5,127 to 5,061) and by 13
  on the fresh set (4,221 to 4,208).

  Figures after the round, by the page: clean copies 21,904 of 22,587 notes (97.0 %; 2 gained by the list and 2
  lost, and 2 typed notes set apart; as typed 21,849 of 22,606), 35 scores at 99 % and 64 at 95 %, 533 notes to
  go for 99 % of each score; 6,044 of 6,239 syllables as before (as typed 5,995 of 6,259). 24 scores read every
  printed note (24), 35 every syllable (35), 18 both (18), 21 have no note that is not there (19:
  pascha-christ-is-risen-appalachian and pascha-receive-long are new) and 13 are whole in all three (13); 13
  scores lack one to three notes; 681 printed notes are lacking and 2 that a hand changed, and 195 syllables;
  694 notes are read that are not there (692 with the place that a hand changed apart; 728 and 726 before). All
  scores: 78,240 of 89,723 notes (87.2 %; as typed 78,185 of 89,742), 89 at 99 %, 5,061 notes that are not
  there; 25,522 of 28,680 syllables (89.0 %; as typed 25,352 of 28,700). The kit is 6222 of 6901 by parts and
  5792 of 6419 staff by staff, as before. Fresh set: 39,817 of 41,761 notes (95.3 %; 2 gained and 6 lost by the
  line-up above; 92 pieces at 99 %; 4,208 notes that are not there), syllables and whole words as before.

  Limits: the rule for a pair asks for whole notes without stems, so two half notes side by side and a whole
  note beside a half note stay as they were. The rule for a mark at the end of a stem asks for a flat mark: a
  piece of a beam as high as a head stays a head. The limit of the time signature was moved for one engraving.
  The count by parts can lose notes where a false note had held its line-up, on the fresh set too. The clean
  copies still lack 681 printed notes and 195 syllables and read 692 notes that are not there.

- Round 55 (18 November 2026): the trail of a long flag, a half note on a thick ledger line whose inside leans in
  two halves, and notes that the page holds where the typed hymn strikes them again.

  The round went on with the clean scores nearest to whole. Two rules for the notes are in, and the list of the
  notes by the page grew by 8 notes in 3 scores. Each rule alone (notes gained and lost):

  | Rule | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | `symbols.FLAG_TRAIL`: a hollow mark at a stem that goes down from its left side is the loop of a flag where its closed paper goes on from the mark's own inside along the right of the stem, in small cells, for 0.9 staff spaces or more, to within 1.5 staff spaces of the stem's end | 0 and 1, 10 notes that are not there fewer | 0 and 2, 21 notes that are not there fewer | 0 and 0, 4 notes that are not there fewer |
  | `symbols.HALVES_LEAN`: the two halves of the inside of a head on a ledger line are one inside where the upper half leans to the right of the lower one, both at most 1.2 staff spaces wide together | 0 and 0, 1 note that is not there fewer | 1 and 0, 3 notes that are not there fewer | 1 and 0, 1 note that is not there more |

  - A long flag that runs along its stem closes a row of small cells with it, and the first of them, at the
    head, was read as the inside of a half note: an eighth note was read twice, once as a half note. The trail
    of cells that goes on down the stem tells the flag. The first form took any piece of paper in the rows of
    the head as the start of the trail, also the paper between a staff line and the top of the lower of two
    stacked half notes, and took true half notes: 0 notes gained and 3 lost on the clean copies, 0 and 7 on all
    scores, 0 and 9 on the fresh set. The trail begins at the mark's own inside now.
  - The rule's note lost on the clean copies (trisagion-arabic) is a false mark that had counted by chance; its
    sheet staff by staff shows only 2 false notes gone. The other note lost on all scores is in
    transfiguration-antiphon, a score whose page holds more music than its hymn: a mark that is gone had stood
    at a sharp, the sharp now acts on its note, and the window of the count moved (46 to 44).
  - Two half notes side by side on a thick ledger line (lazarus-koinonikon) have insides that the line cuts in
    two halves each, and the halves lean apart: each half was read as a head. Round 54 counted a rule that joins
    such halves on every line and left it out (0 and 3 on the clean copies, 7 and 11 on all scores). On the
    lines of the staff the same shape is two heads a third apart as often; the rule acts at ledger lines only
    now, and sets the head on the line between its halves. lazarus-koinonikon reads one note that is not there
    fewer (4 to 3); the other halves of its pair do not lean.
  - The fresh set reads one note that is not there more by it (ro-cor-magnify): the larger inside changes what
    `hole_heads` learns of the page's holes, and a cell between a slur and the staff lines then passes as a
    head. A guard for the rows of the ledger lines did not take it away.
  - The list of the notes by the page holds 8 notes more, each looked at on the page: in
    non-liturgical-o-pure-virgin (second scan) the page ties a note under one held syllable to the same pitch
    after it, in the melody and in the ison (6 notes), and in extra-rejoice-o-virgin-rachmaninov and
    extra-come-bless a voice holds its note over or under the other voice of its staff where the typed chord
    strikes it again (2 notes). They bring 9 notes on the clean copies, and 8 typed notes are no longer counted.
    The finder for such places looks at both line-ups of a held run now: the long note lined up with its first
    typed note, and with its last.
  - Looked at and left: megalynarion-bulgarian's last lacking note, a tie from a whole note into the next page
    whose page prints no leaving half; the loose long ties of pascha-angel-cried (second scan), whose bows end
    far over their heads or run into a staff line before them; and two whole notes stacked in two spaces of
    extra-beatitudes, where the rim of the upper one is taken as the stem of the lower one.

  The pages were read again with Tesseract where a rule changes them: 28 pages of LitChoir and 11 of the fresh
  set. The full reading agrees with the readings of the rules alone: the clean copies gain no note and lose 1,
  all scores gain 1 and lose 2 (staff by staff none and none on the clean copies, 1 and 3 on all scores), and no
  syllable changes. No score changes its layout or the notes that it sets apart; transfiguration-antiphon moves
  its window. The notes that are not there fall by 10 on the clean copies (738 to 728), by 23 on all scores
  (5,152 to 5,129) and by 3 on the fresh set (4,224 to 4,221).

  Figures after the round, by the page: clean copies 21,904 of 22,587 notes (97.0 %; 9 gained by the list and 1
  lost; as typed 21,851 of 22,608), 35 scores at 99 % and 64 at 95 %, 533 notes to go for 99 % of each score;
  6,044 of 6,239 syllables as before (as typed 5,995 of 6,259). 24 scores read every printed note (24), 35 every
  syllable (35), 18 both (18), 19 have no note that is not there (18: carol-great-rejoicing is new) and 13 are
  whole in all three (13); 13 scores lack one to three notes; 681 printed notes are lacking and 2 that a hand
  changed, and 195 syllables; 728 notes are read that are not there (726 with the place that a hand changed
  apart; 738 and 736 before). All scores: 78,240 of 89,723 notes (87.2 %; as typed 78,187 of 89,744), 89 at
  99 %, 5,129 notes that are not there; 25,522 of 28,680 syllables (89.0 %; as typed 25,352 of 28,700). The kit
  is 6222 of 6901 by parts and 5792 of 6419 staff by staff, as before. Fresh set: 39,821 of 41,761 notes (95.4 %;
  1 gained and none lost; 92 pieces at 99 %; 4,221 notes that are not there), syllables and whole words as
  before.

  Limits: the rule for the trail of a flag asks for the trail at the right of a stem that goes down; a flag of a
  stem that goes up, and a loop that closes no trail, stay as they were. The rule for the halves acts at ledger
  lines only and reads one false note more on one fresh page by what a later step learns of the page. The clean
  copies still lack 681 printed notes and 195 syllables and read 726 notes that are not there.

- Round 54 (18 November 2026): a half note on a faint ledger line, and two voices with their stems back to back.

  The round went on with the clean scores nearest to whole. Two rules for the notes are in, and one was counted
  and left out. Each rule alone (notes gained and lost):

  | Rule | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | `layers.HOLE_LEDGER`: the rows of three ledger lines over and under each staff count as lines for the neck of an inside, where the ledger line is seen as a thin level stroke at both sides of the head | 2 and 0 | 3 and 0 | no page differs |
  | `music.ONE_LINE_BACK`: two voices whose stems stand back to back, up to 0.7 staff spaces apart, begin together, unless the second note stands in the column of another note of the other voice | 0 and 0, 2 notes that are not there fewer | 0 and 3, 7 notes that are not there fewer | 0 and 0, 3 notes that are not there fewer |

  - A half note on a ledger line whose line is faint inside the head (pascha-christ-is-risen-ch178, which reads
    every printed note now) has one inside with a neck where the line runs; the rule for such a neck knew only
    the rows of the staff lines, so the inside counted as ragged and leaned a little too far for a slit. The
    first form took every row where a ledger line can run: 2 notes gained and 1 lost on the clean copies, 4 and
    2 on all scores, no fresh page changed. What it took wrongly were the bowls of a bold letter of a title and
    the paper between a slur and a head, which have a neck in such a row too and no line past them. The rule
    asks for the line at both sides of the head now; it acts on 4 pages, and the clefs and keys of each stay.
  - Two voices a second apart or on one pitch stand side by side with their stems on one line, and a column
    reads them as notes that begin together. One print sets two such voices back to back (the first head at the
    left of its stem, the second at the right of its own), 13 pixels apart where the limit was 12: the notes
    followed each other, and megalynarion-bulgarian read 2 notes that are not there. A wider limit alone took
    about 35 notes that are not there away on LitChoir, gained 1 note and lost 3, and lost 1 note on the fresh
    set; where it lost, the second note stood in the column of a note of the other voice and sounds with that
    one. The guard is that column.
  - The rule's 3 notes lost on all scores are in one copy by hand (baptism-as-many). A hand's arrow at the top
    of the staff was read as a note and a bar line as the stem of the note after it: the two stand back to
    back, the note begins with the arrow, and the run of equal notes after it that the scorer sets apart as
    recited grows by 3 (70 to 73). Its note before the rule had counted as right by chance.
  - Left out: the two halves of the inside of a head on a thick line that lean apart, as one inside
    (`symbols.HALVES_LEAN`; lazarus-koinonikon reads 4 notes that are not there for two half notes side by side
    on a ledger line). First form 0 notes gained and 3 lost on the clean copies, 7 and 11 on all scores; with
    the head set on the line between its halves, the same. It acts on 39 pages, also on pairs of half notes a
    third apart that were read as two marks each, and needs a second look of its own.

  The pages were read again with Tesseract where a rule changes them: 8 pages of LitChoir and 1 of the fresh
  set. The full reading agrees with the readings of the rules alone: the clean copies gain 2 notes and lose
  none, all scores gain 3 and lose 3 (staff by staff 5 and 1), and no syllable changes. No score changes its
  layout or its window; baptism-as-many sets 3 notes more apart. The notes that are not there fall in three
  scores (5,158 to 5,152 on all scores), and on the fresh set by 3 in one piece.

  Figures after the round, by the page: clean copies 21,896 of 22,595 notes (96.9 %; 2 gained and none lost; as
  typed 21,852 of 22,608), 35 scores at 99 %, 548 notes to go for 99 % of each score; 6,044 of 6,239 syllables
  as before (as typed 5,995 of 6,259). 24 scores read every printed note (23 before:
  pascha-christ-is-risen-ch178 is new), 35 every syllable (35), 18 both (17), 18 have no note that is not there
  (18) and 13 are whole in all three (12); 13 scores lack one to three notes; 697 printed notes are lacking and
  2 that a hand changed, and 195 syllables; 738 notes are read that are not there (736 with the place that a
  hand changed apart; 740 and 738 before). All scores: 78,232 of 89,731 notes (87.2 %; as typed 78,188 of
  89,744), 89 at 99 %, 5,152 notes that are not there; 25,522 of 28,680 syllables (89.0 %; as typed 25,352 of
  28,700). The kit by parts is 6222 of 6901, and 5792 of 6419 by its own count staff by staff (5790). Fresh
  set: 39,820 of 41,761 notes (95.4 %; none gained or lost; 92 pieces at 99 %; 4,224 notes that are not there,
  4,227 before), syllables and whole words as before.

  Limits: the rule for the ledger line asks for the line at both sides of the head, so a head whose line a
  hand drew at one side only stays as it was (one note of a copy by hand that the first form gained). The rule
  for the stems back to back lost one note of a copy by hand that had counted by chance, and takes away no
  note that is not there of lazarus-koinonikon, whose cause is left. The clean copies still lack 697 printed
  notes and 195 syllables and read 736 notes that are not there.

- Round 53 (18 November 2026): a cell beside a filled head, a small note beside a chord, a bow that swells, and a
  stray word under the clef.

  The round went on with the clean scores nearest to whole, mark by mark: the cause that round 52 left (a filled
  head that is read as a hollow one), three false notes of one score, one tie, and two syllables. Three rules for
  the notes and one for the words are in; one rule for the notes and four for the words were counted and left
  out. Each rule alone (notes or syllables gained and lost):

  | Rule | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | `symbols.CELL_OUT`: a cell along a staff line between a thin stroke and a filled head is paper, and the head is read anew (notes) | 6 and 0 | 13 and 1 | 11 and 0 |
  | `music.STACKED_NEAR`: a small note set to the left of a chord, with a stem of its own, sounds with the chord (notes) | 0 and 0, and 3 notes that are not there fewer | 0 and 0, and 5 fewer | no page differs |
  | `ties.TIE_SWELL`: a bow that swells in its middle is followed in ink that may be fatter (notes) | 1 and 0 | 2 and 0 | no page differs |
  | `ocr.CLEF`: a word in the columns of the clef that Tesseract is not sure of is no word (syllables, by the replay) | 3 and 0 | 3 and 4 | 0 and 0 |
  | Two whole notes alone in their bar, the lower one for the second voice (notes; not in the code) | | 5 and 11 in its third form | |

  `CELL_OUT`: round 52 left the filled head that is read as a hollow one. A head and the stem of the note
  before it, or a head and its sign, close in a cell of paper with the staff lines; the layer of the insides
  holds the cell, the whole piece is one mark with a hole, and it was read as one half note. Round 52 showed
  that the layer must stay as it is, because the older rules read a flag and a time signature from it. The rule
  works in the step that makes the marks (`symbols.thick_marks`): a cell with a level side along a staff line,
  as `FLAT_CELL` measures it, is taken out of its piece as paper, and the piece is made anew with the brush that
  made the marks of the page, so that the head becomes a filled mark of its own. The first form took every such
  cell in a mark that holds a filled head. It gained 10 notes on the clean copies and lost 10, and 25 and 31 on
  all scores (43 pages), and it stopped on one page: the pieces that it made were not cut to their own boxes. A
  census of the 170 such cells of 485 scan pages, 34 of them with a changed note, gave the shape of the true
  ones: the cell stands between a thin stroke and a head. In its middle rows the ink at one side is at most 0.4
  staff spaces wide (a stem, the stroke of a sign) and at the other side 0.55 or more. The loop of a flag has
  thin ink at both sides, and a cell under a beam has its heads below it. Left out on purpose: a cell whose head
  stands below it (2 notes of memorial-troparia). The rule changes 15 pages of LitChoir. The clean copies gain 6
  notes and lose none, all in forerunner-troparion (502 to 508 of 513). All scores gain 13 and lose 1, a note of
  a copy by hand (the second scan of pascha-praises-t5). On one thick copy (liturgy-entrance-hymn) it reads
  three more notes, a chord of two heads beside a bar line and a hollow mark, and none of them counts as right:
  two notes that were missed there are read with a wrong length or pitch now, and 2 notes more are read that are
  not there. The fresh set gains 11 notes and loses none on 10 pages.

  `STACKED_NEAR`: ascension-koinonikon-farrow read every printed note and 4 notes that are not there. Its
  engraver sets a small note of a further voice to the left of a chord, with a stem of its own, so close that
  the chord's upper head stands where the stem of the small note is looked for; the small note was a column of
  its own and came out a second time. `music.STACKED` joins a third voice to its column where the heads are
  stacked; the new half of that rule joins a note that stands a little to the left. The first form asked only
  for two near heads (the middles at most 1.3 staff spaces apart, a quarter of a staff space of paper between
  them at most, at most two places apart). On the clean copies it lost 1 note and took 7 false notes away; on
  all scores it gained 9 and lost 19 on 34 pages, most of them by a window that moved (pentecost-koinonikon lost
  13, the second scan of theophany-megalynarion gained 7), and one loss was the rule's own: a false twin of a
  head and a true note became one chord at the twin's moment (megalynarion-zakkak). A census of the 65 close
  pairs of those pages showed the print's sign: the small head is 0.72 to 0.8 times as wide as the head beside
  it, where two marks of one head are 0.96 to 1.0. The rule asks for two filled heads, the small one at most
  0.85 times as wide as the other and 0.8 staff spaces wide or more. It changes 2 pages now: farrow reads 1 note
  that is not there (4 before), and a copy by hand reads 2 fewer (a blot at the end of a staff; the second scan
  of st-basil-champion-leader). No note is gained or lost, no page of the fresh set differs, and none of the 139
  pages of software-made PDFs. A rule for one engraving.

  `TIE_SWELL`: lazarus-koinonikon lacked one note, the second half of a tie whose bow was not read. A bow is
  followed in the thin ink of the page (ink at most 0.4 staff spaces thick), and this engraver's bow swells in
  its middle: it is 10 to 15 pixels thick in a tenth of its columns where the limit is 9, so the way showed 0.89
  of its columns where 0.9 are asked. Where a way shows thin ink in 0.6 of its columns and fails, it is followed
  again in ink up to 0.65 staff spaces thick. The first form gained 3 notes on all scores and lost 3 on 11
  pages, and it lost on the fresh set: no note gained and 29 lost on 5 pages, where a short fat stroke between
  two heads (a hand's slur, a piece of a beam) was joined as a tie. The 15 ways that the first form took on
  LitChoir's pages were measured and looked at: the 6 false ones are at most 3.3 staff spaces long, and 7 of the
  9 true ones are 4.4 or more. The rule asks for a way of 4 staff spaces or more. It changes 5 pages; every new
  tie was looked at and is true. All scores gain 2 notes and lose none (lazarus-koinonikon reads every printed
  note, 139 of 139, and 4 notes that are not there in the place of 5; pascha-angel-cried-lady gains 1), and no
  page of the fresh set differs. Two true short ties of a thick copy stay unread by the length.

  `CLEF`: presentation-christ-apolytikion reads every note and lacked two syllables. In one row a grey smudge
  under the clef is read as a short word, at one size as letters that the list of words holds, so the second
  look of that row held more letters of the list than the reading with the true first syllable, which
  Tesseract was not sure of and which was left out. The words of a row begin under its first note; what
  Tesseract reads in the columns of the clef is the tail of the clef, the brace, a bar line or a smudge at the
  edge of the page, unless the row goes on there, and then it is read surely. The rule: a word of two letters or
  more that ends within 3 staff spaces of the left end of the staff over its row, begins at most 1.5 staff
  spaces before it, and that Tesseract is less sure of than 50 of 100 is no word. A census of the words that are
  read in those columns (387 on 184 scan pages of 127 scores) gave the limits. Forms, by the replay: any word
  and any start gained 3 syllables on the clean copies and lost none, gained 4 and lost 13 on all scan pages and
  lost 3 on the fresh set (words of one letter, and words far to the left of the staff, on copies by hand);
  with a start near the staff 4 and 11, and 3 lost on the fresh set; with two letters or more 3 and 5, and no
  page of the fresh set counts otherwise.

  The first full reading of that form lost what the replay had not: 4 syllables on two copies by hand and 2 on
  one piece of the fresh set, though every word that the rule dropped there was stray ink. Two causes, both in
  what the rule changes beside its word. The word went before the row was judged, so a row that the stray word
  had marked as unsure was a sure row without it, and how sure Tesseract is of a reading rose where the word
  went: on the fresh piece a whole row of words was dropped by it. And a first reading that holds only words of
  the list beside the stray word was whole without it, so the other sizes were not read, and a syllable that
  the first size misread stayed lost (round 35 met the same with a mended word, `ocr.MEND_WHOLE`). The row is
  judged with the stray word now and the word goes after it, and a reading that lost such a word is not whole
  (`ocr.CLEF_WHOLE`: alone 1 syllable gained and none lost on all scan pages). By the replay the rule gains 3
  syllables on the clean copies and loses none, gains 3 and loses 4 on all scan pages, and changes no count of
  the fresh set. The 4 lost are on two copies by hand: in pascha-angel-cried-believers a stray word had been
  joined to the end of a true word and made a word of the list by chance, and without it a reading of a further
  language file wins that misreads two syllables; in pascha-canon-ode-8 a stray word had been mended to a word
  of the hymn and had counted. Trials that did not help: counting the letters of the dropped word as letters
  that the list lacks where a further file is weighed (clean copies 2 and 0, all scan pages 2 and 5).

  Counted and left without a rule:
  - Two whole notes that stand alone in their bar, one over the other, where the column before holds both
    voices: the lower one as the second voice (the false note of palm-megalynarion). Three forms, on all scores:
    21 notes gained and 13 lost, 16 and 11, 5 and 11. A chord after a note that both voices share got its parts
    swapped (non-liturgical-jesus-prayer), a lone note of the second voice was taken to fill a bar of six beats
    (palm-entrance), and layouts and windows moved. The false note itself comes from the count: the kit parts a
    staff's notes by their voices, and a tie into one note of a chord leaves the other note alone in its column.
  - A reading of a further language file that leaves out a word which the first file read at the same place
    (clean copies 0 and 1, all scan pages 2 and 1, fresh set 0 and 3): the reading that dropped the syllable was
    a second look of the first file, not a further file.
  - A syllable at the start of a row that ends a word of the row before is not mended into another word where
    the list holds the whole word: no case, because the hymn that is read is left out of the list, and the
    whole word of the case is a word of that hymn alone.
  - Ink that is paler than the words of its row is no word (the smudge under the clef is grey). By the palest
    twentieth of a word's box small capitals in a high row failed, whose ink is under a twentieth of the box;
    by the darkest spot of a word true thin letters are 30 to 110 levels paler than their row too. Clean copies
    4 gained and 18 lost, all scan pages 22 and 59, fresh set 0 and 6.
  - An unsure short piece that every plain reading of its row holds stays: alone 1 syllable gained on the clean
    copies, and nothing beside `CLEF`.
  - The grey of the filled heads under the marker line of wedding-alleluia-grechaninov: a census of 49,329 read
    notes gave no limit.
  - Looked at and left: one head that two flagged stems share, where both loops of the flags are read as half
    notes and the head is lost (extra-rejoice-o-virgin); the last chord of whole notes of
    transfiguration-troparion, missed in all four parts on a blotted print; a slanted time signature after the
    bass clef that is read as notes (pascha-christ-is-risen-romanian); and the second syllable of
    presentation-christ-apolytikion, a piece at the start of a row that is mended into another word.

  The pages were read again with Tesseract where a rule changes them: 79 pages of LitChoir and 19 of the fresh
  set. For the notes the full reading agrees with the readings of the rules alone: all scores gain 15 notes and
  lose 1, the clean copies 7 and none (forerunner-troparion 6, lazarus-koinonikon 1); staff by staff all scores
  gain 44 and lose 1, the clean copies 26 and none. The clean copies gain 1 syllable (presentation-christ-
  apolytikion) and lose none, and 3 whole words; the replay's 3 syllables count as the kit does. All scores gain
  1 syllable and lose 4: 3 in pascha-angel-cried-believers, and 1 in the second scan of pascha-praises-t5 with
  its note. No score changes its layout, its window or the notes that are set apart. The notes that are not
  there fall in eight scores and rise in one (5,170 to 5,158 on all scores).

  Figures after the round, by the page: clean copies 21,894 of 22,595 notes (96.9 %; 7 gained and none lost; as
  typed 21,850 of 22,608), 34 scores at 99 %, 549 notes to go for 99 % of each score; 6,044 of 6,239 syllables
  (96.9 %; 1 gained and none lost; as typed 5,995 of 6,259), 36 scores at 99 % of the syllables. 23 scores read
  every printed note (22 before: lazarus-koinonikon is new), 35 every syllable (35), 17 both (16), 18 have no
  note that is not there (18) and 12 are whole in all three (12); 14 scores lack one to three notes; 699 printed
  notes are lacking and 2 that a hand changed, and 195 syllables; 740 notes are read that are not there (738
  with the place that a hand changed apart; 744 and 742 before). All scores: 78,232 of 89,734 notes (87.2 %; as
  typed 78,188 of 89,747), 88 at 99 %, 5,158 notes that are not there; 25,522 of 28,680 syllables (89.0 %; as
  typed 25,352 of 28,700). The kit by parts is 6222 of 6901 (6218 before), and 5790 of 6419 by its own count
  staff by staff (5786): lazarus-koinonikon, forerunner-synaxis-troparion and transfiguration-kontakion gain.
  Fresh set: 39,820 of 41,761 notes (95.4 %; 11 gained, none lost; 92 pieces at 99 %; 4,227 notes that are not
  there, 4,228 before), 8,299 of 11,341 syllables and 5,898 of 6,647 whole words, as before.

  Limits: the rule for the cell asks for a thin stroke at one side of the cell and a head at the other; a cell
  whose head stands below it stays a hollow note, one note of a copy by hand is lost, and one thick copy reads 2
  notes more that are not there. The rule for the small note beside a chord is a rule for one engraving. The
  rule for the bow leaves two short true ties of a thick copy unread. The rule for the word under the clef
  gains 1 syllable on the clean copies in the full reading and loses 3 on one copy by hand by the count, where
  every word that it drops is stray ink; the second syllable of presentation-christ-apolytikion stays lost. The
  clean copies still lack 699 printed notes and 195 syllables and read 738 notes that are not there.

- Round 52 (18 November 2026): notes that are not there on the clean copies, and the word O beside a bracket.

  The clean scores that are whole but for a note that is not there were looked at, mark by mark. Two causes of
  such notes got a rule, the words got one, and one rule for the words was counted and left out. Each rule
  alone (notes or syllables gained and lost):

  | Rule | Clean copies | All scores | Fresh set |
  |---|---|---|---|
  | `symbols.END_PAST`: a mark past the end of a staff whose last columns are nearly solid ink is no head (notes) | 0 and 0, and 4 notes that are not there fewer | 0 and 1 | no page differs |
  | `symbols.FLAT_CELL`: a cell between a staff line and a slanted stroke is no hollow head (notes) | 3 and 2, and 23 notes that are not there fewer | 21 and 7 (17 and 4 without two scores whose windows move) | 80 and 0 |
  | `ocr.ROUND_SIDE`: the word O that is read as a zero or a sign with a bracket at one side (syllables, by the replay) | 1 and 0 | 5 and 0 | 0 and 0 |
  | A word that one reading holds whole is parted as two other readings part it (syllables, by the replay; not in the code) | 0 and 5 | 0 and 5 | 3 and 0 |

  `END_PAST`: round 51 left the notes that nativity-canon-ode-1 and ode-4 read in the black of a binder hole:
  the scan cuts one staff at its last line, and the other staff is followed past its final bar line, so
  neither ends with a whole bar line for `END_MARK`. Each staff now keeps how much of its darkest column near
  its end is ink (`end_ink`, the measure that `layers.END_BAR` asks). A census of the read notes of every scan
  page that stand past the end of a staff with no whole bar line: 18 notes. The 7 whose staff ends with a
  column that is ink in 0.6 of its rows or more are no notes, and the 4 true notes have 0.43 at most; the limit
  is 0.55, and two false notes at 0.48 and 0.53 stay. Read on every page, 5 pages differ and 7 marks are gone,
  each looked at and each false. The clean copies gain and lose no note and read 4 notes fewer that are not
  there (ode-1 and ode-4 have none now). All scores lose 1 note: in liturgy-litanies a true half note is
  voted to a quarter by its column where the false mark is gone, and the window of that score moves by two
  beats. No page of the fresh set differs. A census of tall solid ink anywhere on a page (815 pieces on 60
  pages) gave no rule for the edge of a scan, tape or a hole elsewhere.

  `FLAT_CELL`: the notes that are not there on the clean scores nearest to whole are mostly hollow marks: a
  pencil ring that crosses the staff, a slur over a staff line, the loop of a flag, a piece of a rest or of a
  clef. Each closes in paper against a staff line, and the closed paper is read as the inside of a half note.
  A census from the reader's own layer of the insides: 15,109 pieces of closed paper at the read hollow notes
  of every scan page, each with the scorer's verdict. The inside of a printed head is an oval that touches a
  staff line at a point; a cell between a line and a stroke has a level side along the line. 93 pieces are
  0.6 staff spaces high or more with a top or a bottom that is level in 0.95 of its columns at a staff line,
  and each was looked at: none is a printed hollow head.

  The first form refused such a cell in the layer of the insides (`layers.head_holes`), so that every later
  step saw the mark as filled. It gained 21 notes on the clean copies and lost 4, and 102 and 46 on all
  scores (192 pages differ), and it lost on the fresh set: 108 notes gained and 117 lost. The older rules for
  flags read a flag from the room that it closes, so eighth notes became quarters; the number 4 of a time
  signature has such a cell; and measures of the page that come from its hollow heads moved. That form is
  out. The rule is a late step on the read heads now, after the flags are counted and after the rules for
  the loops of flags: it takes the mark away and leaves the layers as they are. Without a guard that step
  took 95 marks on 70 pages (clean copies 4 gained and 2 lost, all scores 22 and 13, fresh set 80 and 2), and
  16 of them were real filled heads: a sharp or a natural close before a head closes in a cell with it, and a
  hand draws a head as a thick stroke along a line. The guard is the fattest ink of the mark, the widest disc
  that fits into it, against 0.85 times the usual one of the page's filled heads: on a clean print the false
  cells have 0.75 at most and the real heads 0.93 or more. With the guard 56 marks are gone on 46 pages (18
  marks on clean copies). By the scorer's verdict 25 were not there, 10 wrong in pitch and length, 4 wrong in
  pitch, 3 in length, 9 stood at no moment of the hymn, and 5 had counted as right. The guard alone gains 6
  notes on all scores and loses 1 (the clean copies lose 1 by it, in forerunner-troparion), and it keeps
  about 27 false notes of copies by hand, whose every stroke is as fat as a head: the rule is a rule for a
  print, and it stays mostly off on a copy by hand.

  The clean copies gain 3 notes and lose 2, and read 23 notes fewer that are not there; staff by staff they
  gain 3 and lose none. The two lost notes are in trisagion-jerusalem, and both marks were false: a cell at
  the loop of a flag that was read as a whole note, and the cell beside two half notes whose stems cross,
  which counted by chance. The page prints that pair with the upper note's stem down and the lower note's
  stem up, and the hymn is typed otherwise there: a candidate for the list of the notes by the page. All
  scores gain 21 and lose 7; two copies by hand move their windows (4 gained, 3 lost). The other losses were
  looked at: a piece of a clef that had counted by chance (the second scan of transfiguration-kontakion), and
  one real note, a head that a hand drew as a stroke at the end of a staff (the second scan of
  trisagion-soroka). Of the 56 marks that are gone, four hold a real note of a copy by hand. The fresh set
  gains 80 notes and loses none on 54 pages, and reads 159 notes fewer that are not there.

  `ROUND_SIDE`: the second scan of non-liturgical-o-pure-virgin lacks the word O where Tesseract reads the
  letter as a zero or as a sign with a bracket at one side. The rule for the word O in round brackets
  (`ocr.ROUND`) asked for both brackets. With one bracket the same signs are the word O, where the reading
  does not hold the sign in whole brackets elsewhere. By the replay it gains 1 syllable on the clean copies
  and 5 on all scan pages and loses none; with the zero alone it gains 1 and 3. It changes 5 rows on 5 pages
  of LitChoir, and each added O is true. On the fresh set it changes 3 rows and no count: one of them is a
  row of expression marks, where the O is false.

  A word that is read whole: the same score reads a word of two syllables whole at the size that is chosen,
  and two other readings of the row part it. Parting such a word as the other readings do lost 5 syllables
  on the clean copies and gained none: one clean score prints words of one syllable spread under two notes
  with a line, and readings part them there. The fresh set gained 3. No rule.

  Counted and left without a rule:
  - The pencil ring of nativity-canon-ode-5 (2 notes that are not there now, 3 before): the size of the
    closed paper, its grey, the thickness of the stroke and the share of the paper that an oval covers do not
    part a ring from a half note on every page.
  - The two filled heads with a cell between them that are read as one hollow head: the form in the layers
    read 18 such notes on the clean copies. A second look at such a mark that leaves the rules for the flags
    as they are is the next form.
  - The other syllables that the second scan of non-liturgical-o-pure-virgin lacks are scattered: a word of
    the refrain that the page prints between the rows of the verses, and misreads.

  The pages were read again with Tesseract where a rule changes them: 56 pages of LitChoir and 55 of the
  fresh set. The full reading agrees with the readings of the rules alone: all scores gain 21 notes and lose
  8, the clean copies 3 and 2. All scores gain 4 syllables and lose 1 (the copy by hand whose window moves),
  the clean copies gain 1 and lose none; the full reading counts 3 of the 5 syllables of the replay, which
  counts as the kit does. No score changes its layout; three copies change their window (liturgy-litanies,
  transfiguration-antiphon, pentecost-antiphon). The notes that are set apart move in three scores, so the
  count of the drawn notes is 7 lower (89,734): liturgy-what-shall-i-render from 34 to 36, a clean score of
  the list whose pages show a recitation. The false mark at the end of a staff had stood for a recited note
  there; looked at on the page, the staff is empty after a double bar line and the words are printed over it.
  The others are two copies by hand (3 and 2 notes).

  Figures after the round, by the page: clean copies 21,887 of 22,595 notes (96.9 %; 3 gained and 2 lost; as
  typed 21,843 of 22,608), 33 scores at 99 %, 555 notes to go for 99 % of each score; 6,043 of 6,239
  syllables (96.9 %; 1 gained and none lost; as typed 5,994 of 6,259), 36 scores at 99 % of the syllables.
  22 scores read every printed note (21 before: ascension-koinonikon-farrow is new), 35 every syllable (35),
  16 both (15), 18 have no note that is not there (16) and 12 are whole in all three (11:
  nativity-canon-ode-4 is new); 15 scores lack one to three notes; 706 printed notes are lacking and 2 that
  a hand changed, and 196 syllables; 744 notes are read that are not there (742 with the place that a hand
  changed apart; 771 and 769 before). All scores: 78,218 of 89,734 notes (87.2 %; as typed 78,174 of
  89,747), 87 at 99 %, 5,170 notes that are not there (5,216 before); 25,525 of 28,680 syllables (89.0 %; as
  typed 25,355 of 28,700). The kit by parts is 6218 of 6901 (6220 before: the two false marks of
  trisagion-jerusalem that had counted; the kit's own count staff by staff is as it was). Fresh set: 39,809
  of 41,761 notes (95.3 %; 80 gained, none lost; 92 pieces at 99 %, 90 before; 4,228 notes that are not
  there, 4,387 before), 8,299 of 11,341 syllables and 5,898 of 6,647 whole words, as before.

  Limits: both rules for the notes take marks away, and each loses notes by the count where a false mark had
  counted; every such mark was looked at, and one of them was a real note of a copy by hand. The rule for the
  cell is a rule for a print: its guard keeps about 27 false notes of copies by hand, and a ring whose paper
  has no level side stays a note. The end rule needs a nearly solid column at the end of the staff: two false
  notes under its limit stay. The rule for the word O adds a false O in a row of expression marks. The clean
  copies still lack 706 printed notes and 196 syllables and read 742 notes that are not there.

- Round 51 (18 November 2026): the clean scores nearest to whole, words and notes that are not there.

  The clean scores that lack least after round 50 were looked at again, each lost syllable and each note that
  is not there. Three causes got a rule and one rule was counted and left out. Each rule alone (notes or
  syllables gained and lost):

  | Rule | Clean copies | All scans | Fresh set |
  |---|---|---|---|
  | `ocr.MEND_ALIKE`: a word that every reading of a row holds alike counts as a word that Tesseract is sure of (syllables, by the replay) | 8 and 0 | 27 and 3 | 0 and 1 |
  | `symbols.FLAG_CURL`: the curl of a flag is no head (notes) | 3 and 0 | 32 and 7 (13 and 7 without one score whose layout moves) | 9 and 0 |
  | `symbols.END_MARK`: a mark at or past the bar line that ends a staff is no head (notes) | 0 and 0, and 11 notes that are not there fewer | 6 and 2 | no page differs |
  | The first word of a row is not mended where the row before ends with a hyphen (syllables, by the replay; not in the code) | 0 and 1 | 4 and 8 | 0 and 0 |

  `MEND_ALIKE`: nativity-canon-ode-6 lacked one syllable. Every one of the 18 stored readings of its row has
  the true word, the list lacks it (the list leaves out the hymn that is read), and the word was mended to a
  word of the list one letter away, because Tesseract was not sure of it at the size that was chosen. A row
  is read at three sizes by three language files, and a word that all of them hold with the same letters has
  been read. The first form never mended such a word: 8 syllables gained and none lost on the clean copies,
  19 and 4 on all scan pages, none and 1 on the fresh set. A census of the 33 words that it keeps on all scan
  pages, each labelled by the typed hymn: about 20 are true words and 10 are misreads that every reading
  shares, on copies by hand, and no measure of the word parts the two. The second form counts such a word as
  a word that Tesseract is sure of: the rules for a sure word (two runs of three letters that no word of the
  list holds, a word one letter from one of the list's commonest) still mend it. It gains 27 syllables on all
  scan pages and loses 3, and is the form in the code. With the readings of the first language file alone the
  rule keeps more misreads (38 gained and 10 lost on all scan pages, 2 lost on the fresh set). The three lost
  syllables of LitChoir are on copies by hand: a misread that every reading shares, and a row where another
  reading wins now. The one of the fresh set is a true word that the list lacks: it keeps its letters now, and
  the list then does not part it into its syllables.

  The first word of a row: presentation-christ-apolytikion ends a row with the hyphen of a word and begins
  the next row with the end of that word, which was mended to a word of the list. Not mending the first word
  of a row after such a hyphen lost 1 syllable on the clean copies and gained none, and gained 4 and lost 8
  on all scan pages: the last sign of a row is a hyphen in many readings where the page prints none. No rule.

  `FLAG_CURL`: wedding-georgian read the curl at the end of an eighth note's flag as a small filled head with
  a stem of its own, and the bass lacked its note in that column. A census from the stored notes of every
  scan page (no page is read for it): 620 read notes stand in the row of a flag that was counted at another
  stem, at the flag's side of that stem. The 83 filled ones under 0.6 of the area of the page's filled heads
  were each looked at, and none is a note: curls and tips of flags, the ends of beams, pieces of rests and of
  numbers. From 0.6 on true heads stand there, the notes of another voice. Read on every page of LitChoir, 55
  pages differ. The clean copies gain 3 notes and lose none (wedding-georgian reads every note; two notes of
  the second scan of cherubic-georgian). All scores gain 32 and lose 7; 19 of the gain are one copy by hand whose layout and
  window move. The 11 notes that are gone in the four scores that lose were looked at, and each was a false
  mark that had counted by chance or held a line-up; so were the three notes that are gone on pages whose
  count does not move (a drawn ornament, the tip of a flag, a quarter rest). The fresh set gains 9 notes and
  loses none, and reads 148 notes fewer that are not there.

  `END_MARK`: nativity-canon-ode-4 and ode-1 read notes in the black of a binder hole beside the end of a
  staff. A census of every read note of the scan pages that stands at the end of its staff or past it: 194
  notes. The distance to the end does not tell: where a staff ends without a bar line, 18 of 27 such notes
  are true (a copy by hand whose lines fade before the last note, a note beside a punch hole that hides the
  lines). Where a bar line ends the staff, nothing of the music stands at it or past it: 65 notes, each
  looked at, and none is a note. They are the thick stroke of a final bar line that a hole or the wear of the
  print broke (`THICK_BAR` asks for whole columns), punch holes, paperclips, tape and the black edge of the
  scan, with the bar line as their stem; six of them counted as right by chance. Whether a staff ends with a
  bar line is asked of the ink as it is scanned (`layers.END_BAR`), because the rim of a blot takes the line
  beside a punch hole away. The first form ran before the other finders of heads and lost a true whole note:
  the closed paper between the two strokes of a final bar line was gone early, and a later step no longer
  read the whole note of that staff. The rule runs after every finder now: 6 notes gained and 2 lost on all
  scores (one grey speck at a bar line that had counted in both voices of a copy by hand), 37 pages differ,
  and 64 of the 65 notes of the census are gone. The clean copies gain and lose no note and read 11 notes
  fewer that are not there (extra-beatitudes 4, extra-come-bless 2, the second scan of liturgy-mercy-of-peace
  2, liturgy-what-shall-i-render 2, the second scan of transfiguration-troparion 1). No page of the fresh set differs. The rule does
  not reach the two scores that it was looked for: the staff of ode-4 ends at the cut of the scan and the
  rim of a hole bites its last line (0.74 of the rows), and the staff of ode-1 is followed past its final bar
  line into the black of the hole.

  Counted and left without a rule:
  - Solid ink over and under a mark (its columns are ink in 0.9 of the rows within 1.5 staff spaces): 3 notes
    on all scan pages. The stacked heads of a chord reach 0.8.
  - Small filled notes (under 0.4 of the area of the page's heads): on the clean copies 10 are not there, 3
    are wrong and 5 are right. Size alone gives no rule.
  - wedding-georgian keeps one note that is not there, a printed arrow over a note with a tick by a pen. A
    census of the notes whose stem stands under the middle of the head: 3,134, most of them right.
  - nativity-canon-ode-5 reads three notes from a pencil ring around two notes, and
    wedding-alleluia-grechaninov two from a line of a marker over the staff.
  - liturgy-mercy-of-peace lacks 18 syllables (16 in its second scan): in the first scan one system is
    written by hand on a slip that is pasted on the page (notes and words), a hand wrote over a printed word,
    and the words are set in capitals. Words that a hand wrote on a clean copy wait for the owner's decision on the words that a
    hand crossed out.

  The pages were read again with Tesseract where a rule changes them: 115 pages of LitChoir (39 whose rows
  the rule for the words picks otherwise, 55 where the curl rule and 37 where the end rule changes a note)
  and 35 of the fresh set. The full reading agrees with the readings of the rules alone: the clean copies
  gain 3 notes and 9 syllables and lose none (the replay counted 8 for the rule for the words). All scores
  gain 38 notes and lose 9, and gain 32 syllables and lose 5, none of them on a clean copy: the replay
  counted three for the rule for the words, and the others stand on pages where the curl rule takes a note. One
  copy by hand changes its layout and its window (carol-heaven-and-earth, 19 notes) and three change their
  window with no note moved; the notes set apart move by one or two in three copies by hand, so the count of
  the drawn notes is 2 lower (89,741). No clean score changes its layout, its window or its notes apart.

  Figures after the round, by the page: clean copies 21,886 of 22,597 notes (96.9 %; 3 gained and none lost;
  as typed 21,842 of 22,611), 33 scores at 99 %, 557 notes to go for 99 % of each score; 6,042 of 6,239
  syllables (96.8 %; 9 gained and none lost; as typed 5,993 of 6,259), 36 scores at 99 % of the syllables.
  21 scores read every printed note (20 before), 35 every syllable (32), 15 both (12), 16 have no note that
  is not there (16) and 11 are whole in all three (10: nativity-canon-ode-6 is new); 16 scores lack one to
  three notes; 709 printed notes are lacking and 2 that a hand changed, and 197 syllables; 771 notes are read
  that are not there (769 with the place that a hand changed apart; 785 and 783 before). All scores: 78,205
  of 89,741 notes (87.1 %; as typed 78,161 of 89,755), 87 at 99 %, 5,216 notes that are not there (5,309
  before); 25,522 of 28,680 syllables (89.0 %; as typed 25,350 of 28,700). The kit is as it was (6220). Fresh
  set: 39,729 of 41,761 notes (9 gained, none lost; 4,387 notes that are not there, 4,535 before), 8,299 of
  11,341 syllables (1 lost), 5,898 of 6,647 whole words (1 gained).

  Limits: the rule for a word that every reading holds alike keeps a misread that every reading shares, and
  on a page whose words the list lacks it leaves a word unparted. The rule for the curl of a flag and the rule
  for the end of a staff take marks away, and each loses notes by the count where a false mark had counted;
  every such mark was looked at. The end rule needs the bar line: a staff that the scan cuts or that is
  followed past its bar line keeps its false notes. The clean copies still read 197 syllables wrongly and
  769 notes that are not there.

- Round 50 (18 November 2026): the clean scores nearest to whole again, notes and words.

  The 12 clean scores that lack at most three things after round 49 (notes, syllables and notes that are not
  there together) and five more that lack up to seven were looked at on the page, every lost note, every
  note that is not there and every lost syllable. Three causes got a rule, one word went on the list of the
  words by the page, and one rule was dropped after it was read. Each rule alone (notes or syllables gained
  and lost):

  | Rule | Clean copies | All scans | Fresh set |
  |---|---|---|---|
  | `symbols.BEAM_CROSS`: a slur that passes the end of a stem is no beam (notes) | 1 and 0 | 1 and 0 | no note changes |
  | `ocr.SURE_JOIN`: an unsure syllable beside its hyphen stays where the list holds the whole word (syllables, by the replay) | 1 and 0 | 12 and 3 | 1 and 0 |
  | `ocr.SOLID`: a word whose box is solid ink is no word (syllables, by the replay) | 1 and 0 | 3 and 0 | 0 and 0 |
  | The black edge painted out of the pictures that Tesseract gets (syllables, read with Tesseract on 42 pages; off) | 0 and 2 | 3 and 2 | not read |

  `BEAM_CROSS`: a level of ink that hangs on both sides of a stem's end is the beam of a middle note, and the
  flag of the note before can be its witness. A slur that passes under the ends of two stems hangs on both
  sides of each in the same way: a quarter note of transfiguration-hymn-theotokos was read as an eighth. The
  slur is slim against the beams of its own page (0.28 staff spaces where the page's beams are 0.69). A
  census of every page of LitChoir lists the stems with such a level that is at most 0.8 times as thick as
  the page's sure beams: 56 stems. The 32 slimmest were looked at: all 20 that are at most half as thick are
  slurs and ties, and the slimmest true beam (a blurred eighth note) stands at 0.52. Such a level is no beam
  and no witness now where both its pieces are at most half as thick as the page's beams and stand at one
  height (0.35 staff spaces). The margin is thin (0.50 against 0.52), and between 0.5 and 0.6 slurs and one
  true beam stand mixed: the rule takes only the part of the census that holds no beam. Of the 11 pages
  where it acts, one note changes its length, the one that it was written for; the other pages differ only
  in the marks of their stems. On the fresh set two stems pass, and no note changes.

  `SURE_JOIN`: nativity-canon-ode-7 lost the second syllable of a word whose hyphen was read. Every one of
  the 18 stored readings of the row (three sizes, with and without the crossing ink, three language files)
  holds the syllable; at one size the small file is not sure of it (12 of 100), `ocr.SURE` leaves a short
  word that Tesseract is not sure of out, the hyphen then joins nothing, the list of words parts the two
  neighbours, and that reading holds only words of the list and wins. Which rule drops a syllable was found
  by replaying the one row with each rule off. A short word that Tesseract is not sure of stays now where
  the list holds the word that it makes with the pieces beside its hyphens, before it or after it: the
  hyphen was read, so a syllable stands there. On all scan pages the replay counts 12 syllables gained and 3
  lost. The three lost ones are on two copies by hand: the rule keeps a true syllable there too (the end of
  a word after its hyphen), the row then fits the list better at another size, and that reading has two
  other words wrong. An unsure piece before a hyphen stays lost where the list lacks the whole word (the
  list leaves out the hymn that is read: one syllable of presentation-christ-apolytikion).

  `SOLID`: the black edge of a scan beside a row of words is read as a word (nativity-canon-ode-6, ode-4,
  ode-1), and so is a bar line or a brace that crosses a row. The first form painted the blots of the page
  (`layers.blots`) white in the pictures that Tesseract gets. Read with Tesseract on the 42 pages where a
  blot stands in such a picture, the false words were gone and the clean copies lost 2 syllables and gained
  none: a change of the picture moves the reading of words that the change did not touch, as round 36
  showed. That form is not in the code. The second form leaves the picture as it is and asks the box of each
  word that was read: a word of two letters or more is no word where 0.3 of the columns of its box or more
  are ink from half a row's height over the row to half a row's height under it. A letter fills its column
  over the row or under it, not both. Measured in the rows of the row alone, the stems of a bold "ni" filled
  half of its box, and the first replay lost that syllable. A census of the 29,600 stored words of every
  scan page: 51 words of two letters or more on 0.3 or more; those from 0.25 on that are not read as "ll" or
  "ff" (29) were looked at, and every one is a bar line, a brace, a black edge or the shadow of a spine. The
  replay hands a rule the columns of a row, not the page; it hands this rule the page, as it does for the
  lone stroke.

  The list of the words by the page has one place more (26 places in 9 scores): nativity-canon-ode-7 prints
  one word in an older form than the hymn is typed with, and a hand wrote the next word beside it. The
  reading of round 49 scored with the new list: 1 syllable more (6,031 of 6,239); as typed it gives the
  figures of round 49 exactly.

  Counted and left without a rule:
  - A half note on a ledger line that touches the line under it (pascha-christ-is-risen-ch178): its inside
    is ragged paper (`layers.RAGGED`), it rises by 40.5 degrees where the rule for such a slit allows 40, and
    with a wider limit the rim test fails, because the row of its middle is the ledger line. A census of
    3,000 ragged pieces of every scan page: 231 lean by 40 to 60 degrees on 150 pages, most of them in
    flats, clefs, sharps and letters. Read with a limit of 50 degrees: 2 notes gained and 1 lost on all
    pages, none on the clean copies, and the note itself is not gained. No rule.
  - palm-megalynarion counts one note that is not there by parts (the tenor: 66 read, 65 typed) and none
    staff by staff; four notes are given to both voices, each with two stems on the page. Not found.
  - Words that a hand changed on a clean copy: nativity-canon-ode-1 has two printed words crossed out by
    hand with other words written under them, and the hymn is typed with the printed ones; ode-9 has a
    pencil loop through a printed word. Both stay counted as lost syllables for now. The owner's decision
    of 17 November is about notes that a hand changed; whether printed words that a hand crossed out count
    apart in the same way is asked.
  - Single words that Tesseract misreads or that a rule mends wrongly, one in each score: a true word that
    the list lacks is mended to a word of the list one letter away (nativity-canon-ode-6, where every
    reading has the true word), the first syllable of a row is mended although the row before ends with the
    hyphen of its word (presentation-christ-apolytikion), a word under a pencil loop (ode-9), one letter of
    a word (ode-4), and a word that the page prints with one hyphen where the list parts it twice (ode-9).
  - Seen on the page and left: worn hollow seconds on ledger lines (pascha-receive-short), thin open half
    notes a second apart with dashed stems (trisagion-obleschuk), a whole note read as a half note at a tie
    (lazarus-koinonikon), a half note read a third lower with a note that is not there over it
    (wedding-georgian).

  The pages were read again with Tesseract where a rule changes them: the 80 pages of LitChoir whose rows the
  two rules for the words pick otherwise or where the rule for the slur acts, and the 4 such pages of the
  fresh set. The full reading agrees with the replay on the clean copies (2 syllables gained, none lost: one
  each in nativity-canon-ode-7 and nativity-kontakion). On all scores it counts 14 syllables gained and 4
  lost. The four lost ones are on three copies by hand: the three that the replay showed, and one syllable
  that is set under the next note where words of solid ink are gone from its row. On the fresh set one
  syllable is gained and none is lost, and no note changes. Between the two readings of LitChoir no score
  changes its layout, its window or its notes apart.

  Figures after the round, by the page: clean copies 21,883 of 22,597 notes (96.8 %; 1 gained and none lost;
  as typed 21,839 of 22,613), 32 scores at 99 %, 558 notes to go for 99 % of each score; 6,033 of 6,239
  syllables (96.7 %; 2 gained by the rules and 1 by the list, none lost; as typed 5,984 of 6,259), 33 scores
  at 99 % of the syllables. 20 scores read every printed note (19 before), 32 every syllable (31), 12 both
  (10), 16 have no note that is not there (15) and 10 are whole in all three (8: nativity-canon-ode-7 and
  transfiguration-hymn-theotokos are new); 16 scores lack one to three notes; 712 printed notes are lacking
  and 2 that a hand changed, and 206 syllables; 785 notes are read that are not there (783 with the place
  that a hand changed apart). All scores: 78,176 of 89,743 notes (87.1 %; as typed 78,132 of 89,759), 86 at
  99 %, 5,309 notes that are not there; 25,495 of 28,680 syllables (88.9 %; as typed 25,321 of 28,700). The
  kit is as it was (6220). Fresh set: 39,720 of 41,761 notes as before, 8,300 of 11,341 syllables.

  Limits: the rule for the slur has a thin margin and acts on 20 stems of LitChoir's pages and two of the
  fresh set. The rule for a word of solid ink takes false words away that no count sees (a syllable too many
  costs nothing), and its gain in the count is small. The clean copies still read 206 syllables wrongly, and
  no cause among those looked at holds more than one or two.

- Round 49 (18 November 2026): the clean scores nearest to whole, score by score.

  The 13 clean scores that lack at most three things (notes, syllables and notes that are not there together)
  were looked at on the page, every lost note and every note that is not there. Four causes got a rule. Each
  rule has a census of every page of LitChoir, every reading that it changes was looked at, and each is
  counted alone on the 46 pages where a census finds one of them (notes gained and lost):

  | Rule | Clean copies | All scores | Notes that are not there, clean and all | Pages that change |
  |---|---|---|---|---|
  | `symbols.LINE_OUT`: two specks in the rows of a staff line are no slit of a half note | 3 and 0 | 5 and 0 | as before | 11 |
  | `layers.STRAY`: a line of the scan that runs upright past a system is no ink | 2 and 0 | 4 and 0 | 6 and 6 fewer | 4 |
  | `ties.TIE_APART`: a short tie that stands free between its two heads | 1 and 0 | 1 and 0 | 1 and 1 fewer | 1 |
  | `rests.HOOK`: a quarter rest whose hook closes in paper | 0 and 0 | 0 and 0 | 3 and 3 fewer | 2 |

  `LINE_OUT`: a filled head on a staff line is a half note where a speck of paper is closed in over the line
  and one under it (`LINE_SLIT`, round 29: the slit of a half note that a heavy print nearly closed). A worn
  filled head holds two specks too, in the rows of the line itself, where no paper can show under a line that
  runs through a head. The first form asked both specks to lie outside the line, 0.4 thicknesses of a staff
  line from its row: on the clean copies it parted 55 true half notes from five of six filled heads. Read on
  every page it gained 3 notes and lost 30, on thick copies and copies by hand: their lines are 7 or 8 pixels
  thick, the row that the staff gives for a line misses the ink by a few pixels, and the lower half of a true
  slit lies within that distance. A census of every scan page (471 heads that pass `LINE_SLIT`, each labelled
  by its typed length) showed the measure that separates: how far the farther of the two specks lies from the
  line, in staff spaces. The 348 true half notes begin at 0.134, eleven filled heads end at 0.112, and one of
  the two specks must lie 0.12 staff spaces or more from the line now. The twelve heads that are refused were
  looked at (three of them in one engraving whose flagged notes hold such specks too: they are no half notes). A
  limit in thicknesses of the staff line was a limit of the prints that it was set on.

  `STRAY`: a scan shows lines that are no music: a fold, the edge of a slip that was pasted on, the edge of
  the page. Where such a line runs through a system, a head beside it was one mark with it and no note (two
  notes of nativity-canon-ode-3), and where it crosses the staff lines its pieces were read as notes (six
  notes of nativity-canon-ode-4 that are not there). A bar line ends at its staff; a line that runs upright
  without a break from two staff spaces over a system to two under it, at most 0.3 staff spaces wide, is
  taken out of the ink where it stands alone in its row, so that a staff line, a head and a letter that it
  crosses stay whole. A line of a scan leans by a pixel, and its ink is looked for in the next column too. On
  LitChoir's pages 11 lines of 8 pages pass, each looked at: eight lines of five clean pages, and three lines
  of three other copies (long opening lines that a hand drew, and one long line where a bar line stands: 2
  notes gained there, the heads beside it). The clefs and the keys of these pages are as they were.

  `TIE_APART`: a bow counts as a tie where its ink leads from the first head to the second. A short tie
  between two eighth notes on a ledger line stands free: paper shows between its end and the second head,
  and what follows is the ledger line of that head. Such a way is a tie where its ink shows without a break
  for a staff space or more, then paper, then at most 0.7 staff spaces of ink at the second head; the bow
  stands in the middle between the heads and is a bow by the older measures. Three ways pass on all pages,
  each looked at. One of them was a slur between two eighth notes a step apart on a copy by hand, where the
  reader has one head a step off: joined as a tie it lost a note. The two heads of such a tie stand at one
  height on the page (a quarter of a staff space), whatever their read pitches say; the slur stands 0.57 apart.

  `HOOK`: a quarter rest is read by its shape, and a shape that closes in paper is no rest (`rests.HOLE`).
  On a heavy print the hook at the lower end of the rest closes: one piece of paper of 0.024 to 0.043 square
  staff spaces, four fifths of the way down. Such a rest was read as a note. A census of every rest shape of
  LitChoir's pages: 360 rests are read, and four are refused by the closed paper alone, each looked at, all
  quarter rests. One piece of at most 0.06 square staff spaces that lies 0.7 of the height down or further
  is allowed now. Three notes that are not there are gone in two clean scores.

  On the fresh set every page was read with the round's rules: no page differs. Between the two readings of
  LitChoir no score changes its layout, its window or its notes apart.

  Figures after the round, by the page: clean copies 21,882 of 22,597 notes (96.8 %; 6 gained and none lost;
  as typed 21,838 of 22,612), 32 scores at 99 %, 558 notes to go for 99 % of each score; 19 scores read every
  printed note (17 before), 31 every syllable, 10 both (9), 15 have no note that is not there (13) and 8 are
  whole in all three (5: all-saints-troparion, forerunner-nativity-apolytikion-carpatho and
  nativity-canon-ode-3 are new); 17 scores lack one to three notes; 713 printed notes are lacking and 2 that
  a hand changed; 786 notes are read that are not there (796 before; 784 with the place that a hand changed
  apart). All scores: 78,175 of 89,743 notes (87.1 %; 10 gained and none lost; as typed 78,131 of 89,758), 86
  at 99 %, 5,310 notes that are not there. Syllables: as before (clean copies 6,030 of 6,239, all scores
  25,484 of 28,680). The kit gained 1 note (6220, in thomas-troparion). The fresh set is as it was. (The table
  of the scans by copy gave 12,044 syllables and 8,394 whole words for the copies by hand since round 48;
  the figures of that round were 12,045 and 8,395.)

  Seen on these scores and left: two half notes a third apart that touch, one on a ledger line and one on
  the top line, with four holes where `LINE_PAIR` asks for three (1 note of pascha-christ-is-risen-ch178,
  which lacks nothing else); a quarter note under two ledger lines that the vote of its column makes an
  eighth; pencil rings and the pale stroke of a marker that are read as notes (5 notes in two scores); a
  blot at the edge of a page; worn hollow seconds on ledger lines. The syllables that the near scores lack
  are single words that Tesseract misreads, one or two in a score.

  Limits: the rules of this round are small, 6 notes and 10 notes that are not there on the clean copies;
  59 clean scores still lack a printed note. `LINE_OUT` stands 0.014 staff spaces under the lowest true half
  note of the census, a third of a pixel. `STRAY` takes only a line that runs past a whole system at both
  ends: the two notes that are not there at the black edge of nativity-canon-ode-4 stay. `TIE_APART` and
  `HOOK` have three and four cases on LitChoir's pages and none on the fresh set.

- Round 48 (17 November 2026): the count first, then the notes that are not there.

  A gap of the count is mended. The scorer sets a typed note apart as recited where the reader has no note for
  it in a run of five equal pitches: so the recited syllables of a chant that the page prints as one note are
  not counted against the reader. On a clean copy a printed note that the reader lost hid there: 15 notes of
  nine clean scores were set apart so, counted neither as drawn nor as lacking, and the total of the drawn
  notes moved with the reading (22,575 after round 46, 22,582 after round 47). A clean copy is read whole,
  so what its pages do not draw is a matter of the page now: the clean scores whose pages show a reciting
  note or a held ison are a list with the wide test, outside git (9 scores, each looked at on the page: one
  chord under several syllables, a breve or a whole note that recites, the whole notes of an ison), and on
  every other clean score a typed note that is not read is missed. By this count the reading of round 47 is
  21,873 of 22,597 notes on the clean copies (96.8 %, not 96.9 %), 31 scores at 99 % (not 32), 722 printed
  notes lacking (not 707) and 564 notes to go for 99 % of each score; all scores 78,161 of 89,746. The notes
  that were read are the same. The count as typed (`AS_TYPED=1`) stays as it was.

  A correction of round 47: its figures as typed gave the totals of round 46 (21,829 of 22,591 on the clean
  copies and 78,117 of 89,752 on all scores). The notes right were as reported; the totals were 22,612 and
  89,761, moved by the same gap with the pages that round 47 built anew.

  Eighty of the notes that are not there were looked at on the page, drawn by lot from the sheets of the
  clean copies. No kind holds more than a tenth of them: the pieces of a thick bar line, the bold sign of
  common time, the letters of a dynamic under the staff, the end of a slur at a bar line, a pencil ring, the
  black edge of a page, the numbers of a time signature, a second in a chord of half notes. The figure by
  parts (839 on the clean copies) holds more than marks that are no notes: the notes of a page that prints
  more than its hymn types (57 in one score that is typed as a unison), the breves of a printed ison that is
  counted by its letters, and a note that is given to both voices of a staff. The sheets staff by staff show
  470 marks.

  Two rules, each counted alone on every page of LitChoir (notes gained and lost):

  | Rule | Clean copies | All scores | Notes that are not there, clean and all | Pages that change |
  |---|---|---|---|---|
  | `symbols.THICK_BAR`: the pieces of a thick bar line between the staff lines are no heads | 0 and 0 | 2 and 0 | 14 and 17 fewer | 7 |
  | `meter.COMMON_BOLD`: the bold C of common time is a sign, not two notes | 3 and 0 | 8 and 6 | 29 and 150 fewer | 81 |

  `THICK_BAR`: the thick stroke of a final bar line or of a repeat sign is wider than a stem, so it is no
  slim ink; the staff lines cut it into pieces as high as a staff space, and each was read as a filled head
  with the thin line beside it as its stem. A filled mark whose columns are ink over the whole height of the
  staff (nine tenths of the rows from the top line to the bottom line, over four fifths of its width) is such
  a piece. The heads of a chord taper towards the lines between them: of 15,057 true notes of the clean
  copies none has such columns. The 20 notes that the rule takes stand at 11 places, and each was looked at:
  all are final bar lines and repeat signs. On the fresh set no page differs.

  `COMMON_BOLD`: the reader knew the thin C of common time at the start of a staff. The bold C of a print
  is as high as two heads, stands on the middle line and was read as two notes a third apart, most often as
  the first notes of a line. Its height and its place also fit an eighth rest, a double sharp, a large flat
  and two whole notes one over the other. A census of every such piece gave the shape. On the clean pages
  (61 pieces, each looked at) only the 39 signs have a bow: the left edge stands furthest left in the middle
  rows, where the others have a waist. On the other scan pages 149 more pieces have a bow, and 14 of them are
  flats that a hand draws large, with the stroke at the left over the bowl: the two ends of a C both turn to
  the right (`COMMON_ARM`). One print parts the two ends from the bow, and they count with it
  (`COMMON_ENDS`: 44 more signs, each looked at, all true). A sign stands where a time signature stands,
  after the clef and the key or after a bar line (`COMMON_AT`); two pieces with the shape in the middle of a
  bar are left. 206 signs pass on LitChoir's pages.

  The first form of `COMMON_BOLD` lost 7 notes on five scores of one print that are no clean copies, and each
  was looked at.
  One was a true note: that print sets the held note of the ison under the staff, and under the sign at the
  start of a line the note stood in the sign's columns and went with it. A sign takes the heads in its
  columns only in the rows of the staff now (`COMMON_ROWS`). The other six are typed notes that a piece of
  the C had counted for by chance (a C whose ends touch was a half note at the pitch of the first note) or
  whose line-up it held: no note of these pages is new, and every note that is gone is a piece of a sign. The
  rule stays as it is there. A thin C by hand with one short end does not pass and is left out on purpose.
  On the fresh set no piece passes (the C of its engravings has a short lower end) and no page reads one as a
  note, so no page differs.

  Figures after the round, by the page: clean copies 21,876 of 22,597 notes (96.8 %; 3 gained and none lost;
  as typed 21,832 of 22,612), 31 scores at 99 %, 561 notes to go for 99 % of each score; 17 scores read every
  printed note, 31 every syllable, 9 both, 13 have no note that is not there and 5 are whole in all three, as
  after round 47; 19 scores lack one to three notes; 719 printed notes are lacking and 2 that a hand changed;
  796 notes are read that are not there (839 before; 794 with the place that a hand changed apart). All
  scores: 78,165 of 89,743 notes (87.1 %; 10 gained and 6 lost; as typed 78,121 of 89,758), 85 at 99 %, 5,320
  notes that are not there (5,487 before). Syllables: clean copies 6,030 of 6,239 as before (as typed 5,982 of
  6,259), all scores 25,484 of 28,680 (1 gained; as typed 25,310 of 28,700). The kit and the fresh set are as
  they were.

  Limits: no clean score became whole by this round; the 43 false notes that are gone leave one to six in
  each of their scores. The nine clean scores with a recitation still set a note apart by the run of equal
  pitches, so a lost note can still hide there. The figure of the notes that are not there holds the notes
  that a page prints and its hymn does not type. `COMMON_BOLD` is set on the prints of LitChoir.

- Round 47 (17 November 2026): the first round under the raised bar, score by score. The owner raised the first
  milestone on this day: a clean copy is read whole, every note and every syllable, with no note that is not
  there ("No one wants a 99% product"; "the clean copies should be consistently perfect"). So the round began
  with the clean scores that lack one to three notes, each lost note looked at on the page, and it ended
  at the staves: the largest gains were pages whose staff the reader had cut short, and pages of the wide test
  that were older than the code.

  The count has a second column since this round: the notes that a hand changed on a clean copy (the owner:
  "Count hand-changed notes apart"). A printed head that is crossed out, drawn over or written in by hand is
  listed by its place on the page, outside git, and held to the 99 % of the copies by hand; everything printed
  must be read, also under a pencil ring. At least 28 of the 78 clean scores carry marks by hand (14 on or at
  the notes, 8 beside the music only, 6 a paperclip, punch holes or a stamp), and one place changes notes: a
  note crossed out in pen with a new head beside it (2 typed notes). Two further places that looked like a
  hand at two and a half times the size are worn and rough print at four times: a mark is called handwriting
  only after it was looked at four times the size and in the scan itself.

  Four rules for the notes, each counted alone on every page of LitChoir (notes gained and lost; the stored
  pages of the wide test, see below):

  | Rule | Clean copies | All scores | Pages that change |
  |---|---|---|---|
  | `symbols.PALE_STEM`: the stem of a head beside the staff goes on as pale grey where the copy lost it | 3 and 0 | 9 and 1 | 5 |
  | `symbols.HOLE_UPRIGHT`: a hollow mark whose inside stands upright is no head (first form, without its two guards) | 8 and 3 | 61 and 30 | 158 |
  | `symbols.LOOP_UNDER`: the loop of a flag right under the head of its note | 0 and 0 | 5 and 0 | 9 |
  | `symbols.LEDGER_DASH`: a first ledger line that the print sets as two dashes beside the head | 2 and 0 | 2 and 0 | 2 |
  | The four together, with the guards of `HOLE_UPRIGHT` | 13 and 3 | 76 and 27 | |
  | The step for the hollow marks after the flags are counted | 0 and 0 | 1 and 0 | 10 |

  `HOLE_UPRIGHT` is the rule of the round for the notes that are not there. The inside of a printed half
  note lies on its side and rises to the right; closed paper that stands upright is the loop of a flag, the
  room of a double bar line, the bowl of a letter, the C of the time or the box of a natural, and each was
  read as a half note. The rule measures the largest piece of closed paper in a hollow mark with one stem:
  how many times as long as wide it is along its own axis (1.6 or more) and where that axis points (outside
  -15 to 60 degrees). A census of every such mark gave two guards: a hole that a thick copy all but closed
  has no direction (smaller than 0.05 staff spaces squared: not taken), and one print sets the half note
  of a space with an upright inside between two thick sides (ink 0.5 staff spaces thick at both sides: not
  taken). Its first form lost true half notes of both kinds.

  The rule loses notes by the count, and every mark that it took in a score that loses was looked at: a
  number of a time signature, the room of a double bar line, the box of a natural, a clef, a "6" and a
  pencil ring, each read as a half note before, and each either counted as a right note by chance or held
  a line-up or a vote of its column (liturgy-litanies moves its window by it and loses 6, a copy by hand
  moves its layout and loses 4). Four notes change their length by the vote of their column once the false
  note beside them is gone (a quarter that takes the half of the other voice, on two clean scores; an
  eighth whose flag touches a bar line and was an eighth by that vote only). That vote is a cause of its
  own and is left for a later round. The hollow marks are taken away after the flags are counted: the loop
  of a flag is a mark on the stem of its note, and two eighth notes had become quarters without it.

  `LEDGER_DASH` is a rule for one print, and says so: it reads the two notes of pascha-receive-long that
  stand on a first ledger line drawn as two short dashes, and with them that score reads every printed
  note. `PALE_STEM` reads 11 heads beside the staff whose stem the scan kept as pale grey only; all 11 are
  true heads, and one score loses a note by the line-up of a true one.

  The staves. A pencil ring, a paperclip or a binder ring over the start of a staff, a faded stretch, or a
  page that bends at its spine hides the lines from the comb that finds the staves, and the staff then began
  after its clef or ended before its last bar: the notes there were not read at all. `staves.ENDS_ON` follows
  each of the five lines past the end that the comb gives, window by window (half a staff space wide), at
  the row where the window before puts it. A window counts where three of the five lines are there, each
  filled and thin; a chord, a bar line or a brace is dark for a few windows and is passed; the end moves
  where the lines go on for one and a half staff spaces or more. What the first forms met, each on a page:

  - A brace, a punch hole and the black edge of a page are filled at the rows of the lines too. A line is
    thin: paper half a staff space over or under it.
  - Two pieces of one staff were followed into each other and stood as two staves: the longer one stays.
  - A page that bends at its spine spreads the lines unevenly, 0.8 to 1.35 staff spaces apart. A fit of the
    found rows to five evenly spaced lines refused true staves on clean copies, so the rows only have to
    stand in order, 0.65 to 1.5 staff spaces apart (`staves.ENDS_GAPS`). Without that, two lines were
    followed onto one and the staff came out 88 pixels high where it is 112.
  - The last bar of a system can be a slip of paper from another copy, pasted on with its staff at other
    rows. The nearest rows are then one line off. A staff has five lines: where the first is missing in most
    windows and a sixth one stands under the last (or the other way round), the five lines are the other
    four and the sixth (`staves.ENDS_SIXTH`).

  The rule moves staves on 39 pages of LitChoir and on no page of the fresh set. Rule off against rule on,
  on the pages as the code builds them: 15 notes gained and 3 lost on the clean copies, 216 gained and 12
  lost on all scores (one copy by hand gains 112: two of its staves began a third of the page late). The
  five scores that lose (5, 2, 2, 2 and 1 notes) were each looked at: every staff end is right now (a final
  bar line, a punch hole at the end of a staff, a faded start), and the lost notes stand elsewhere on the
  page. A staff that grows moves the cuts of its system by a row of pixels, the straightened page shifts
  by that row, and a few notes across the page are read otherwise. The rule is not narrowed for them.

  The stored pages. The wide test reads each scan from a clean page that was built once, on 10 November.
  The staves and the systems of the code changed after that day, and the stored pages were not built
  again. All 657 were built anew in this round and compared (staves, systems, places and the picture; blank
  columns at the right do not count): 20 differ. Read from the pages that the code builds, without the staff
  rule, the clean copies gain 31 notes and lose 46, and all scores gain 55 and lose 66:

  - cherubic-georgian--s2 gains 19 (477 of 482) and cherubic-voronkoff--s2 15: the code finds their staves
    better than the stored pages had them.
  - pascha-receive-short, a clean score, loses 46 of its 150 notes: the code joins the first two systems
    of its page into one. The first system is set in, the next one stands close under it, and the bracket
    and the clef of the next system cover 0.60 of the narrow gap between them, which is the limit for a
    line that opens a system. No round had seen it, because the stored page was older than that limit.
  - liturgy-gospel-alleluia--s2, a copy by hand, loses 19: on a staff that rises steeply to the edge of
    the photo the comb jumps to the next line, and the staff is one line off from there on. Not solved in
    this round (the rule for the staff ends gives 7 of the notes back).

  So the figures of the rounds before held 46 notes of the clean copies that the code did not read, and
  lacked 31 that it did. The wide test's pages are those of the code now, and after a change of
  `staves.py`, `systems.py` or `page.py` every page is built anew and compared.

  The systems. A census of what joins two staves on every page of LitChoir (1,560 sure links, 1,046 of them
  by the opening line alone) shows the line of pascha-receive-short for what it is: 18 opening lines cover
  less than 0.75 of their gap, with no bar line through the gap. Of the 15 whose staves can be compared, 6
  join staves whose notes stand in the same columns (in step from 0.52 on) and 9 do not (up to 0.13).
  `systems.OPEN_WEAK` takes such a line for none at 0.3 or less. It changes the systems of 7 pages, each
  looked at: systems of four and six staves that are systems of two (two scans of one hymn by hand, 38 and
  69 notes), chant on single staves that two set-in lines had joined (73 and 40 notes), an "Amen" drawn
  by hand beside the text at the foot of a page, which is a system of its own, a page whose first system
  is set in as on pascha-receive-short (four systems of two now, the count as before), and
  pascha-receive-short, which reads 150 of 153 again. 46 notes gained on the clean copies and none lost, 266 and none on all
  scores. The kit's 38 pages keep their systems (37 of 38 right, as before; the staves 38 of 38).

  The round together, against round 46. Clean copies: 21,873 of 22,582 notes by the page (96.9 %, from
  21,820 of 22,575; 59 gained and 6 lost; as typed 21,829 of 22,591, from 21,762), 32 scores at 99 % (29),
  550 notes lacking for 99 % of each (595). Printed notes, with the two by hand apart: 21,873 of 22,580, and
  0 of 2 by hand. 17 scores read every printed note (15), 31 every syllable (30), 9 both, 13 have no note
  that is not there (10), and 5 are whole in all three (3; new: trisagion-zakkak and wedding-prokeimenon).
  839 notes that are not there (884). All scores: 78,161 of 89,731 (87.1 %, from 77,653 of 89,736; 547
  gained and 39 lost; as typed 78,117 of 89,752, from 77,595), 86 at 99 % (83); 194 pages differ. The six
  notes lost on the clean copies: three scores lose one each where the mark that was taken away was false
  and a length beside it then changes by the vote of its column (holy-saturday-koinonikon,
  liturgy-mercy-of-peace, nativity-kontakion), and two lose 3 by the staves (nativity-troparion--s2 and
  pascha-hypakoe--s2: their staff ends are right, the cuts of the system move by a row). Limits
  of the count: the count of the drawn notes moved by 7 on the clean copies, because the scorer sets a note
  apart as recited where the reader has none in a run of five equal pitches. cherubic-georgian--s2 reads 4
  such notes now and liturgy-what-shall-i-render 6; three scores each have one printed note more that is not
  read and stands apart (extra-come-bless, nativity-troparion--s2, pascha-christos-voskrese): three lost
  notes that the figures above do not show. Words with Tesseract (read again on the 198 pages that differ or
  were built anew): clean 6,030 of 6,239 syllables (from 6,026; 9 gained and 5 lost; as typed 5,982 of
  6,259), 32 scores at 99 % (31); all scores 25,483 of 28,680 (from 25,316; 178 gained, 11 lost). The 5
  syllables lost stand on three pages that were built anew (nativity-troparion--s3, liturgy-mercy-of-peace--s2,
  hierarchical-xenia-prokeimenon--s2): no rule of the words changed, the picture of a row moved by a row of
  pixels and Tesseract reads a word of it otherwise. Fresh set: 39,720 of 41,761 notes (95.1 %, from 39,650;
  73 gained and 3 lost, each of the 3 looked at: false marks that had counted, and a length by the vote of
  a column), about 500 fewer notes that are not there, 57 pages differ; the syllables did not change (8,299
  of 11,341). Kit 6219 of 6901 (from 6214).

- Round 46 (17 November 2026): the pale speck in the filled heads of one engraving. The two clean scores
  that lack most are two fine engravings (`cherubic-lvovsky`, 104 notes, and
  `extra-rejoice-o-virgin-rachmaninov`, 60). In the first the print pressed the ink out of the middle of its
  filled heads: a quarter note holds a pale speck of paper, and 27 such heads were read as half notes. The
  page's limit for a hole (`symbols.HOLLOW_WORN`, 0.4 of the usual hole of the page's hollow heads) lies at
  0.13 of the head on these pages, most of the specks stay under 0.2, and the true holes begin at 0.21.

  A census first: every read note of the 459 scan pages that the scorer lines up with a typed note (57,557
  notes), with the hole of its head, the page's limit and the typed length. No one limit works. Each general
  limit loses more than it gains: with 0.6 of the usual hole in the place of 0.4 the clean copies would gain
  17 notes and lose 83 by that census, because other prints hold true half notes with a hole of half the
  usual one. The
  share of pale ink in the middle of a head, which parts the heads on these four pages, does not part them
  on other prints (round 32 counted the same).

  So the page has to show the print by itself (`symbols.HOLLOW_PALE`), and it does, by three signs. The
  rule was read in two forms.

  - First form: of the page's heads with a stem that are not hollow, a fifth or more hold a speck (a hole of
    0.015 of the head or more). On such a page a head is hollow only from 0.6 of the usual hole. Read on
    every page of LitChoir it changed 13 pages: 10 notes gained and none lost on the clean copies, 17 gained
    and 6 lost on all scores, and none gained and 1 lost on the fresh set (2 pages). The lost notes stand on
    two scans of a copy by hand and on a thick copy. On the copy by hand the filled heads hold a tiny speck
    (at most 0.2 of the usual hole) and nothing lies between the specks and the holes: the three heads
    with a hole of 0.56 to 0.6 of the usual one are half notes. On the thick copy the usual hole is
    small (0.2 of the head), and the holes of its half notes go down to the limit without a gap. A count of
    the holes from the read notes had not named these pages: the sign is counted from the marks of the page
    before the notes are made, and the tool for it now reads the page as the reader does.
  - Second form, kept: two more signs. The usual hole of the page's hollow heads is 0.3 of the head or more
    (the print's half notes are wide open), and the specks come in every size up to the limit: 5 heads or
    more, and one in twenty of the heads that are not hollow, hold a speck from half the limit on. On the
    four pages of the engraving 9 to 15 heads do; on the copy by hand none does. Each of the two signs alone
    still loses: the usual hole alone 11 gained and 4 lost on all scores, the specks up to the limit alone
    10 and 2. Together they act on the four pages of the one score and on no other page of LitChoir or of
    the fresh set. That is the limit of this rule: it is a rule for one print, with signs that another pale
    print would have to show too.

  Three more trials on the four pages gave nothing. The older rule for two specks in a filled head
  (`LINE_SLIT`) switched off on a pale page: 2 notes right and 2 wrong. The limit at 0.65 of the usual
  hole: none gained or lost, and one more note that is not there. At 0.55: 4 lost.

  The count by the page gained eight notes in four scores. All 47 notes of the clean copies that the reader
  reads longer than they are typed were looked at on the page, each with the columns around it, and the
  typed notes beside them.

  - `cherubic-lvovsky`, two notes. A half note of the sopranos under which the altos strike the same pitch on
    the second beat (the hymn is typed with the soprano striking it again), and a half note of the first
    basses over two quarter notes of the second basses (a typed chord has one length). Both are read, so the
    score gains 2 notes.
  - One print in three scans (`liturgy-holy-holy`, `liturgy-we-praise-thee` and its second scan), two notes
    each. The second altos hold a dotted half note under a half note and a second half note of the first
    altos, and then move under the held second half note. The typed hymn strikes each held note again. The
    reader reads the second half note and not the dot of the dotted one (a chord on one stem has one length
    for the reader), so each scan gains a note and loses a note, and has 2 typed notes fewer.

  The scorer can now take one note out of its typed chord with the length that the page prints. Five of the
  47 led to these eight notes. The other 42 are the reader's mistakes or a line-up of the count: a natural or a sharp read as a hollow head, a
  circle and a stroke by hand, pale heads of the engraving whose speck is as large as a hole (0.24 to 0.31
  of the head), a column whose vote makes a filled head a half note, the whole note of a recitation, and a
  page that holds a response more often than the hymn is typed with, where the count lined a dotted half
  note up with another typed note. The list holds 59 notes in 18 scores now, the count as typed is
  unchanged, and the reading before the round gives the same figures with the changed scorer and the list as
  it was.

  The clean copies went from 21,808 of 22,582 notes to 21,820 of 22,575 (96.7 %; as typed from 21,752 to
  21,762 of 22,591): 10 notes by the rule and 2 by the list, none lost, all in `cherubic-lvovsky`, which
  lacks 91 notes now. 29 scores are at 99 % and 63 at 95 % as before, and 595 notes are lacking for 99 % of
  each score (614 before; 11 scores lack one to three notes). All scores went from 77,641 of 89,743 to
  77,653 of 89,736 (86.5 %; as typed from 77,585 to 77,595 of 89,752); the thick copies and the copies by
  hand did not change. The reader writes 884 notes on the clean copies that are not there (885 before; the
  one is a note of the list) and 5,639 on all scores. No score changed its layout or its window, no key,
  clef or time signature changed, and no syllable changed (6,026 of 6,239 on the clean copies, 25,316 of
  28,680 on all scores). The kit did not change (6214), and no page of the fresh set differs (39,650 of
  41,761). Notes gained and lost, by parts:

  | Rule | Pages of LitChoir that differ | Clean copies | All scores | Fresh test set |
  |---|---:|---:|---:|---:|
  | First form: a fifth of the filled heads hold a speck, not kept | 13 | 10 and 0 | 17 and 6 | 0 and 1 |
  | With the usual hole of 0.3 or more only, not kept | 13 read | 10 and 0 | 11 and 4 | not read |
  | With the specks up to the limit only, not kept | 13 read | 10 and 0 | 10 and 2 | not read |
  | The rule (`symbols.HOLLOW_PALE`, the three signs) | 4 | 10 and 0 | 10 and 0 | 0 and 0 |
  | The eight notes of the list (no rule of the reader; 7 typed notes fewer) | none | 2 and 0 | 2 and 0 | not counted so |

- Looked at on the page, round 46: the 9 heads that change on the four pages (all filled heads with a speck,
  read as quarter and eighth notes now; one column of four notes turned with its head). What the score
  still loses after the round: 12 eighth notes read as quarters under hairline beams and flags (round 43),
  pale heads whose speck is as large as a true hole, a ring that the print sets where a dot stands, a whole
  note whose hairline stem the scan lost, and a natural sign whose box was read as the hole of the head
  beside it.

- Counted in round 46 and left without a rule. The wrong lengths of the clean copies by typed and read
  length: 40 eighth notes read as quarters (25 of them in the two engravings), 30 quarters read as half
  notes, 26 quarters read as eighths, 17 half notes read as quarters, 14 whole notes read as half notes and
  14 dotted half notes read as half notes. Of the 8 quarters that the second engraving reads as eighths,
  three are a note of the lower voice with its own stem down under the beamed notes of the upper voice (the
  beam's vote reaches it), two stand under a hairpin or a slur that touches the end of the stem, two are
  crossed by a grey stroke of a marker, and one is a line-up of the sheet.

- Round 45 (17 November 2026): a head of a chord that was left without the stem that it shares. The round
  began with the 779 notes that the clean copies still lose, sorted by kind: 267 have only a wrong length, 177
  only a wrong pitch, 78 both, and about 260 are not read at all. The wrong lengths and pitches are scattered
  (see below). For the notes that are not read, a census took every filled mark as large as a head that the
  reader leaves without a stem and that is no note: 328 on the clean pages, 116 of them with a read head
  with a stem in their column, each looked at. Most are no heads (the dot of a fermata, a letter, a piece of
  a sharp or of a clef, an ornament), 11 are the whole notes of a recitation that one print sets under the
  staff, and about 20 are heads. Half of those stand in one thick old print (`transfiguration-troparion`, two
  scans): its heads fill the space between two staff lines to the corners, so they are no slanted ovals for
  the rule of round 42, and the lower head of a chord has lost the short piece of stem that joins it to the
  head over it. No word of the reader changed in this round.

  The rule (`symbols.CHORD_STEM`, `symbols.chord_stems`) takes such a mark for the next head of the chord of
  a read head. It stands past the read head at the end where a stem begins (under the head of a stem up, over
  the head of a stem down), the stem's column lies at its edge as at the heads of a chord (the right edge at a
  stem up, the left edge at a stem down; 0.3 staff spaces inside it to 0.25 past it), at most 1.25 staff
  spaces of paper lie between the two, and the mark closes in no paper. It gets that stem, and so the flags and
  the beams of that stem. The rule runs after the rule for a head whose stem the scan lost, so that rule
  keeps the heads that it read before. It was narrowed three times, each time by a census of the heads that
  the form before it made, with the scorer's verdict for each (right, only a wrong length, another mistake or
  a note that is not there):

  - The first form also took a mark that stands along the stem. Of its 183 new heads, a mark past the end of
    a stem was right 74 times, had only a wrong length 24 times and was otherwise wrong 10 times; a mark
    along the stem was right 20 times and was not 55 times (21 notes that are not there, 13 that the
    scorer's sheet does not hold, 18 with a wrong pitch, 3 with only a wrong length): a sharp, the bowl of a
    flat, a letter, a beam and a clef stand at a stem as a head does, and no measure of the mark (its size,
    how full it is, its corners, the paper around it) parted them. The marks along a stem were taken out.
    Two true heads of the old print stand there and are still not read.
  - Wider limits (the stem's column up to 0.5 staff spaces from the edge, up to 2 staff spaces of paper
    between) brought 33 right heads and 24 wrong ones beyond the first limits, against 79 and 12 inside
    them (7 and 23 more have only a wrong length): the first limits stayed.
  - Of the heads inside the limits, 9 close in more than 0.02 staff spaces squared of paper: 1 is right, 2
    have only a wrong length and 6 are wrong. Most are a whole note on a ledger line under the staff, which
    some copies set in brackets or between two strokes: the ledger line cuts the inside into two slivers, so
    the mark is not hollow for the reader. A mark that closes in that much paper is not taken.
  - A guard "a filled mark is no head of the chord of a hollow head" was counted alone and taken out: with
    it all scores gain 2 notes and lose 4. On a staff of two voices a half note and a quarter note stand in
    one column, and the mark is often the other voice's note whose own hairline stem is lost. One of the
    notes that the guard saved was looked at: on a copy by hand with short stems, the new head beside a half
    note made the half note vanish, because a hollow mark near the far end of a stem that it shares with
    another head is taken for the loop of a flag (`without_flag_loops`), and the new head became an eighth
    note. Only that case is guarded now: a mark is not given the stem of a hollow head that stands within
    the reach of that older rule (`LOOP_NEAR`) from the stem's end. Alone it gains 2 notes and loses 1, on
    3 pages.

  The clean copies went from 21,803 to 21,808 of 22,582 notes (96.6 %; as typed from 21,747 to 21,752 of
  22,591): 5 gained and none lost, 3 and 2 in the two scans of the old print. 29 scores are at 99 % and 63 at
  95 % as before, and 614 notes are lacking for 99 % of each score (619 before). All scores went from 77,593
  to 77,641 of 89,743 (86.5 %; as typed from 77,537 to 77,585 of 89,752): 50 gained and 2 lost, in 29 and 2
  scores, 15 net on the thick copies (81.4 % to 81.6 %) and 28 net on the copies by hand, where a stem is a
  hairline under the limit of the ink or a hand sets a head down without one. The reader writes 885 notes on
  the clean copies that are not there, as before, and 5,640 on all scores (5,632 before, in the reading with
  the words; round 44 gave the figure of the reading without them, 5,627). No score changed the layout or
  the window that the count chooses for it. No syllable changed
  (6,026 of 6,239 on the clean copies, 25,316 of 28,680 on all scores). The kit gained 2 notes (6212 to
  6214), and the fresh set did not change (39,650 of 41,761; no page differs: its engraved pages hold no
  such mark). Each part alone, switched off against the round, and the forms before it (notes gained and
  lost, by parts):

  | Rule | Pages of LitChoir that differ | Clean copies | All scores | Fresh test set |
  |---|---:|---:|---:|---:|
  | First form: a mark past the end of a stem or along it, not kept | 88 | 7 and 0 | 62 and 14 | 0 and 0 |
  | Past the end only, with wider limits (0.5, 0.5 and 2 staff spaces), not kept | 78 | 6 and 0 | 74 and 24 | not read |
  | The first limits, no paper inside, before the rule of round 42, not kept | 44 | 5 and 0 | 47 and 9 | not read |
  | After the rule of round 42 instead of before it, alone | 105 read | 0 and 0 | 3 and 0 | not read |
  | No paper inside the mark, alone (3 notes fewer that are not there) | 105 read | 0 and 0 | 0 and 0 | not read |
  | No head in the chord of a hollow head, alone, not kept | 105 read | 0 and 0 | 2 and 4 | not read |
  | No head at a hollow head near the end of its stem, alone | 3 | 0 and 0 | 2 and 1 | not read |
  | The round (`symbols.CHORD_STEM`) | 40 | 5 and 0 | 50 and 2 | 0 and 0 |

- Looked at on the page, round 45: the 68 notes that only the fourth form has and the 9 that the guard for a
  hollow head took away, on their pages. All are heads but one, a scribble beside a hollow head on a copy by
  hand, which the last guard takes out again. About one new head in five is read with a wrong length: it is
  the other voice's note, with a flag or a length of its own, and takes the length of the head whose stem it
  was given. Such a note was not read before, so no count falls by it. The 2 notes that are lost stand in two
  scores that are no clean copies (`theophany-troparion` and `liturgy-first-antiphon`, 1 each; counted staff
  by staff the second gains 3). In the first a hand sets the upper voice's head down without a stem over a
  head with a stem down, and the 5 new heads of its page, all true, are read into the lower voice's chord.
  No key, clef or time signature changed on any page.

- Counted in round 45 and left without a rule. The 267 wrong lengths of the clean copies hold no cause of
  more than 5 notes; the largest is one print whose dots are slanted ticks, higher than a dot may be (5
  notes). Of the 255 notes with a wrong pitch (78 of them with a wrong length too) 98 are a step off, and
  many of the rest are chords that the sheet lines up crosswise. A staff that bends at the edge of a
  photographed page is followed only in part: on one clean page a staff is found for a third of its width
  (11 notes), a census that follows the five lines past the found end of each staff shows 3 more staves on
  the clean pages, and 13 staves on 11 pages among all 657. A whole note over or under the heads of another voice
  takes their stem and is read as a half note (5 to 8 notes; no measure parts it from a true half note in a
  chord). One clean score has a response written in by hand and the notes of a tenor part pencilled into
  the rows of its words, which costs it about 10 syllables. One print sets the whole notes of a
  recitation under the staff over the words; the reader reads none of them, and their typed notes are
  counted apart. 23 ties of the clean copies are not read, each by a cause of its own.

- Round 44 (17 November 2026): the ragged inside of a printed half note. The round began with a tally of the
  272 notes of the clean copies that have only a wrong length: an eighth note read as a quarter 39 times, a
  quarter as a half note 38, a quarter as an eighth 27, a half note as a quarter 22, a dotted half note as a
  half note 16, a whole note as a half note 14. One cause stood behind several of the half notes that are read
  as quarters. A typewriter print (`nativity-troparion`, three scans) sets two half notes a third apart, each
  in a space, so that they touch. The inside of each head is closed paper, but it is small and its edge is
  ragged: it fills 0.83 of its hull, and the inside of a head must fill 0.85 (`layers.ROUND`). So the head is
  not hollow for the reader. The bold upper rim is read as a small filled head, a quarter note; the ink where
  the two heads touch is read as a sharp; and the false quarter, which two voices share, outvotes the true
  half note of another voice in its column. No word of the reader changed in this round.

  A milder limit for a round inside moves a border: at 0.8 the clean copies gain 37 notes and lose 62,
  because the bowl of a flat and the paper in a natural are filled as heads too (one score loses 15). A census
  gave the shape instead: every piece of closed paper on the clean pages that fills 0.75 to 0.85 of its hull
  and lies in a mark that was read as a filled head, 93 pieces, each looked at. The 29 true insides are slits:
  1.5 times as long as wide or more along their own axis, which rises to the right by -8 to 45 degrees, and
  most are no larger than 0.34 staff spaces squared. The bowl of a flat, the paper in a natural, and the
  paper between a sign and a head or between two heads stand upright (47 to 90 degrees) or are large. The
  rule has three parts. Closed paper that fills 0.75 of its hull and not 0.85 is kept in a layer of its own
  (`layers.RAGGED`, the layer `ragged`). It is not filled: the holes, the solid shapes, the clefs and the keys
  are as before. Such paper is the inside of a head where it is a slit of that shape (`symbols.RAGGED_SLIT`:
  a rise of -10 to 40 degrees, at most 0.35 staff spaces squared), and it is asked as an open hole is: it
  needs a stem, and the pieces of rim in its box are no heads. The third part (`symbols.OPEN_BESIDE`) is for
  the pieces: a piece of the rim whose middle lies just over or under the box of the hole is a piece too; a
  piece that one head replaced owns no stem any more, and ink in the columns of such a head that was read as
  a sign is no sign, so the second head of the chord is asked without them; and two such heads, one over the
  other, that found the same stem up and the same stem down keep one each.

  The clean copies went from 21,782 to 21,803 of 22,582 notes (96.6 %; as typed from 21,727 to 21,747 of
  22,591): 21 gained and none lost, in 7 scores (`nativity-troparion--s2` 8, `nativity-troparion` 4,
  `wedding-psalm-128` 4, `communion-lords-prayer` 2, three scores 1 each). 29 scores are at 99 % as before,
  63 at 95 % (61 before), and 619 notes are lacking for 99 % of each score (640 before). All scores went from
  77,443 of 89,745 to 77,593 of 89,743 (86.5 %; as typed from 77,388 of 89,754 to 77,537 of 89,752): 153
  gained and 3 lost, 26 of the gained on the thick copies and 106 on the copies by hand, where a hand draws
  a half note as a slanted slit and its rim falls into pieces. Two typed notes of one copy by hand are
  counted apart now (`pascha-entrance`, which gains 8). The reader writes 885 notes on the clean copies that
  are not there (890 before) and 5,627 on all scores (5,662). No score changed the layout that the count
  chooses for it. The syllables of the clean copies are as after round 40 (6,026 of 6,239); all scores have
  25,316 of 28,680 (25,322 before): 6 lost, in the two scans of one copy by hand (see below). The kit
  gained 5 notes (6207 to 6212), and the fresh set did not change (39,650 of 41,761; no page differs). Each
  part alone, switched off against the round, and what was tried before it (notes gained and lost, by parts):

  | Rule | Pages of LitChoir that differ | Clean copies | All scores | Fresh test set |
  |---|---:|---:|---:|---:|
  | A milder limit for a round inside (`layers.ROUND` 0.8), not kept | clean pages only | 37 and 62 | not read | not read |
  | The pieces of rim beside an open hole, without the layer (a first trial) | clean pages only | 13 and 0 | not read | not read |
  | The slit in its own layer (`layers.RAGGED`, `symbols.RAGGED_SLIT`) | 60 | 16 and 0 | 132 and 2 | 0 and 0 |
  | The pieces of rim beside the hole, and their stems and signs (`symbols.OPEN_BESIDE`) | 35 | 5 and 0 | 67 and 1 | 0 and 0 |
  | The round | 71 | 21 and 0 | 153 and 3 | 0 and 0 |

- Looked at on the page, round 44: all 252 notes that only the new reading has, on its 71 pages, and 20 of
  them that were doubtful at four times the size. 18 of the 20 are true half notes. One is a whole note on a
  line whose inside the line cuts in two; it is read as a half note. One is false: the paper between a thick
  stroke and a filled head on a copy by hand, where a false quarter note stood before. 65 of the new heads are
  read in both voices, most of them with another head close over or under them: the way up from the lower head
  of two voices goes through the upper head. A split of such stems gained nothing and lost 1 note, and was
  not kept. The three scores that lose a note are copies by hand. Two are the scans of one page
  (`ascension-antiphon`): the new reading holds hollow heads there that the page shows and that were read
  as filled heads before, the lengths around them moved, and the count set its window on the page (which
  holds more music than the typed hymn) shorter, 47 against 53: 1 note and 3 syllables are lost in each scan. The third (`trisagion-tchaikovsky--s2`)
  is a half note on a line that was read from a piece of its rim at the right pitch and is read from its
  open hole now, a step low. No key, clef or time signature changed on any page.

- Round 43 (17 November 2026): the tip of a tie that was read as a dot. The round began with four counts on
  the clean copies that gave no rule (see below). The next scores by notes lacking then showed 27 ties that the
  reader does not read, and one cause behind several of them. A long tie begins beside its whole note in a
  space and runs flat into the staff line under or over it. The line hides a stretch of the bow, and the tip
  that is left before it is as small and as full as a dot: the whole note was read with a dot, six beats long,
  and a tie joins two notes only where the first ends as the second begins. One rule came of it
  (`symbols.DOT_TIP`). No word of the reader changed in this round.

  The clean copies went from 21,778 to 21,782 of 22,582 notes (96.5 %; as typed from 21,723 to 21,727 of
  22,591): 4 gained and none lost, in one score (`extra-come-bless`, one page of whole notes under long ties).
  29 scores are at 99 % as before, and 640 notes are lacking for 99 % of each score (644 before). All scores
  went from 77,440 to 77,443 of 89,745 (86.3 %; as typed from 77,385 to 77,388 of 89,754): 4 gained and 1
  lost. The lost note is a whole note on a thick copy that is tied to a half note. Its false dot gave it the
  six beats of the two together; now it is read as the whole note that it is, and the tie is not joined,
  because the half note at the end of the bow is not read (see below). The reader writes 890 notes on the
  clean copies that are not there (897 before) and 5,662 on all scores (5,669): the second halves of the four
  ties are joined now. No score changed the layout that the count chooses for it. The syllables are as after
  round 40 (6,026 of 6,239 on the clean copies, 25,322 of 28,680 on all scores), the kit did not change (6207
  notes), and the fresh set did not change (39,650 of 41,761; no page differs). The three forms of the rule,
  each against the reading before (notes gained and lost, by parts):

  | Form of the rule | Pages of LitChoir that differ | Clean copies | All scores | Fresh test set |
  |---|---:|---:|---:|---:|
  | A small mark in the rows of a staff line is no dot | 214 | 8 and 5 | 51 and 171 | 0 and 0 |
  | Such a mark with a long, low piece of ink past the line beside it | 15 | 5 and 0 | 13 and 1 | 0 and 0 |
  | Such a mark where the bow comes out of the line again at its right (`symbols.DOT_TIP`, the round) | 2 | 4 and 0 | 4 and 1 | 0 and 0 |
- How the rule was narrowed, round 43. The first form asked only where the mark lies. A hand sets its true
  dots on the staff lines, and a thick copy prints them into the lines: 166 of the 171 lost notes are on the
  thick copies and the copies by hand. A
  census of the 301 notes whose dot the first form takes away (52 gained, 122 lost, 127 unchanged in the
  count) measured the mark, the line beside it, the stems and the tie of its note: none of them parts the tips
  from the dots. Only the ink that goes on past the line does. The second form asked for any long, low piece
  there. It changed 19 notes on 15 pages: 5 whole notes at the tips of ties, and 14 notes with a mark beside a
  beam, a slur, a repeat sign or the stroke of a hand, where the piece past the line was that beam or slur, or
  one large blot of joined ink. Most of those marks are no dots either, and the form gained 13 notes; but it
  took them by a shape that is not the tie's, and one of them looks like a true dot that stands over a line.
  The third form asks for the whole shape of the tie: the bow comes out
  of the line again from half a staff space to two staff spaces right of the tip, it is five staff spaces long
  or more, and where it begins it lies within 0.6 of a staff space of the line and is no thicker than that.
  The true tips measure 1.0 to 1.6 staff spaces, 7 to 15, and at most 0.51 and 0.54; the pieces of the marks
  by accident begin left of the tip, or thick, or far from the line. The third form is not a part of the
  second, so it was read on the 214 pages of the first form: 2 pages differ, and on them it takes 6 marks,
  each the tip of a bow beside a whole note.
- Looked at on the page, round 43: the notes that the second form changes and the 6 marks of the third. The
  unread ties, as the sheets of the count show them (a note that is too short, and a note too many of the same
  pitch with the rest of its length): 27 on the clean copies before the round and 23 after it (`communion-lords-prayer` 4, `pascha-angel-cried`
  3, `liturgy-we-have-seen`, `extra-come-bless` and `non-liturgical-jesus-prayer` 2 each, ten scores 1 each).
  Where the bow was traced, it is found and both heads are marked, and the first note has a wrong length; or
  the bow ends more than the allowed way from the second head (a bow to the end of a stem); or the bow is
  hidden in the lines for most of its way. Two more ties, which that list cannot show, end at a hollow half
  note that the bow runs into, and that head is not read: one on the page of the rule, and the one behind the
  lost note.
- Counted in round 43 and left without a rule. A second reading of each clean page with another limit of the
  ink, as in round 42 and now note by note (against the reading of round 42 the lighter limit gains 63 notes
  and loses 250, the darker one 25 and 276). The
  notes that only the other reading has are false twice as often as true (lighter: 50 true and 108 false;
  darker: 50 and 159), also where the first reading has nothing at that place and a column of notes. Of 262
  notes with only a wrong length, 66 are right in another reading, but where the readings differ the first is
  right three to four times as often; where both others agree against it, they are right 17 times and wrong
  12. The bar cannot choose between them: a wrong length fits its voice (the next note begins where it ends)
  in 190 of the 262 cases, and the typed length fits in 44. Only where the first reading does not fit and
  another one does is the other right more often (18 and 4), which is three readings of each page for about
  14 notes: not built. The tied votes of a column (one vote for a half note or for an eighth against one for a
  quarter): the reader's choice is right 57 times and wrong 13. The two clean scores that lack most
  (`cherubic-lvovsky` 104 notes, `extra-rejoice-o-virgin-rachmaninov` 60): 27 eighth notes are read as
  quarters. Both prints have hairline beams. Such a beam lies in a staff line or runs into one, or the scan
  lost it whole (two stems and nothing between them; the scan itself shows the same). Of 55 pairs of stems
  whose ends are joined by ink or by a staff line, the slurs between two stem ends are five times as many as
  such beams, and the share of the line that is ink does not part them (59.6 % against 60 %). In
  `communion-lords-prayer` (33 lacking) quarter chords are typed five and six beats long (ties, or a note that
  is held); not resolved.
- Round 42 (17 November 2026): a filled head whose stem the scan lost. The round began with a tally of the 816
  notes that the clean copies lose (about 280 with a wrong length, 190 with a wrong pitch, 90 with both, and
  260 that are not read) and with three counts that gave no rule (see below). The notes that are not read
  showed one kind that is larger than the rest: a mark as large as a head with no stem. The reader keeps a
  filled mark only with a stem, because a rest, a dot, the end of a slur and a blot are filled marks too. One
  rule in two halves came of it. No word of the reader changed in this round.

  The clean copies went from 21,766 to 21,778 of 22,582 notes (96.4 %; as typed from 21,710 to 21,723 of
  22,591): 12 gained and none lost, in two scores (`extra-rejoice-o-virgin-rachmaninov` 8, `cherubic-lvovsky`
  4). 29 scores are at 99 % as before, and 644 notes are lacking for 99 % of each score (656 before). All
  scores went from 77,359 of 89,723 to 77,440 of 89,745 (86.3 %; as typed from 77,303 of 89,732 to 77,385 of
  89,754): 81 gained and none lost, 33 of them on the thick and grey copies and 36 on the copies by hand. The
  count of the drawn notes grows by 22: a chant page draws the notes of a recitation as filled heads without
  stems, and the typed notes of such a run that the reader had no note for were counted apart. No score
  changed the layout that the count chooses for it. The reader writes 897 notes on the clean copies that are
  not there (893 before) and 5,669 on all scores (5,643): most of the new ones are true notes with a wrong
  length (see below). The syllables are as after round 40 (6,026 of 6,239 on the clean copies, 25,322 of
  28,680 on all scores), and the kit did not change (6207 notes). Each half alone on the pages that the round
  changes (notes gained and lost, by parts):

  | Rule | Clean copies | All scores | Fresh test set |
  |---|---:|---:|---:|
  | The head by its shape (`symbols.STEM_GONE`), with the second half off, against the reading before | 10 and 0 | 71 and 2 | 0 and 0 |
  | The stem from the pieces that the scan left (`symbols.GONE_STEM`), off against on | 2 and 0 | 12 and 0 | 0 and 0 |
  | The round | 12 and 0 | 81 and 0 | 0 and 0 |

  The round changes 27 pages of LitChoir and no page of the fresh set, whose pages are crisp and lost no
  stem.
- A head with no stem at all (`symbols.STEM_GONE`), round 42. A census listed every filled mark as large as a
  head that the reader leaves without a stem, on 23 clean pages: 69 marks, of which 14 are heads of the print
  (in two engravings whose hairline stems the scan lost in places) and 55 are halves of quarter rests, pieces
  of numbers and letters, ornaments and blots. Three measures of the mark part them, and none alone. The head
  of a print is a slanted oval: of the four corners of its box, the upper left and the lower right are nearly
  empty and the other two are filled. It is as large as the heads of its page (the two halves of a quarter
  rest are a little higher, and one piece of ink with each other). And it has paper around it: a frame of
  three tenths of a staff space around the box holds almost no ink, staff lines apart, so that a ledger line
  fits in and an ornament does not. Such a head is a note without a stem: a quarter note, in the voice that
  the notes of its column leave free. Off the clean copies the rule reads grey scans whose stems fall under
  the limit of the ink, chant prints that draw their notes without stems, a typewriter print whose stems
  stand apart from the heads, and one copy by hand with short stems. With the second half off it gains 71
  notes on all scores and loses 2, both in one score: a head without a stem stands a little beside the note
  that it sounds with, and was read as a column of its own, which moved the notes after it. The second half
  gives that head its stem, and the 2 notes come back.
- The stem of such a head from its pieces (`symbols.GONE_STEM`), round 42. A scan seldom loses a stem whole:
  dashes of it are left, or its upper part with the beam or the flag. The rule walks from the head along the
  column of its right edge upwards and of its left edge downwards, a quarter of a staff space to both sides,
  for four and a half staff spaces and not into the words. A stem is slim ink that begins near the head and
  reaches far enough, or slim ink with wide ink after it (a beam, a flag), where the stem ends; its flags and
  beams are then counted as those of any stem. Three forms were dropped while it was written: a column inside
  the head missed stems that stand a few pixels outside its edge, a test for the end of a beam row by row
  failed on beams that slant, and a walk without limits ran into the letters of the words and into the stem
  of a note of the staff above. In its first full reading the half gained 12 notes and lost 1, on a copy by
  hand whose stems are short and thick: such a head keeps a short stem that is too short to count, and the
  stem of the next note stands in its other column, so the head got a false stem and once a false flag. A
  first guard (no stem where the wide ink is a mark of another head) took 8 right eighth notes away again:
  the flag of a stem that stands apart from its head is itself a mark as large as a head. The guard that
  stands asks the head: pieces at one side only, and no slim ink that hangs on the head at the other side.
  With it the half gains 12 notes and loses none (8 eighth notes of the typewriter print, 3 notes of the two
  engravings and 1 more).
- Looked at on the page, round 42: all 103 notes that the first form changes. One is false (a sign by hand
  under a staff that is shaped as a head), and one length changed on a blot. Several new notes are eighth
  notes read as quarter notes, because the stem and its beam are gone whole: they count as notes that are not
  there (26 more on all scores, 4 more on the clean copies). Two notes of one engraving changed their length
  through the agreement of the notes that sound together (an eighth read as a quarter beside a new quarter).
- Counted in round 42 and left without a rule. The limit of the ink: read with a lighter limit the clean
  copies gain 62 notes and lose 258, with a darker one 25 and 280; 267 of the lost notes are right in one of
  the other readings, but nothing that the page shows tells which reading to take for a note. The 16 clean
  scores that lack one to four notes: each note is a case of its own. Whole notes that are taken for the tail
  of another mark: one page. Hollow marks without a stem (69 on the clean pages): a few round whole notes in
  the staff and one half note whose stem the scan lost; the rule for a whole note in the staff
  (`symbols.WHOLE_STAFF`) stays off. An eighth note whose stem and beam the scan lost whole could take its
  length from the notes of its column; not counted yet.
- Round 41 (17 November 2026): the notes that the clean copies still lose, sorted by where they stand. The 840
  lost notes are scattered: 49 scores lose notes, no long stretch of a page has one cause, and the kinds that
  were found hold 2 to 6 notes each. The three scores that lack most after `cherubic-lvovsky` were looked at
  note by note (`nativity-kontakion`, `extra-rejoice-o-virgin-rachmaninov`, `communion-lords-prayer`: 161 lost
  notes together). Two rules came of it, and four places where the page holds a note that the hymn is typed
  with struck again (see below). No word of the reader changed in this round.

  The clean copies went from 21,751 of 22,591 notes to 21,766 of 22,582 (96.4 %; as typed from 21,702 to 21,710
  of 22,591): the two rules gained 8 notes and lost none, and the four places by the page count 7 notes more
  as right and 9 typed notes fewer. 29 scores are at 99 % as before, and 656 notes are lacking for 99 % of
  each score (679 before: 15 by the four places, 8 by the rules). All scores went from 77,339 of 89,732 to
  77,359 of 89,723 (86.2 %; as typed from 77,290 to 77,303 of 89,732), 13 gained and none lost by the rules;
  the thick copies gained 4 notes and the copies by hand 1. No score changed the layout that the count
  chooses for it. The reader writes 893 notes on the clean copies that are not there (892 before) and 5,643
  on all scores (5,644). The syllables are as after round 40 (6,026 of 6,239 on the clean copies, 25,322 of
  28,680 on all scores), and the kit did not change (6207 notes). Each rule alone, switched off against the
  other on, on the pages that the round changes (notes gained and lost, by parts):

  | Rule | Clean copies | All scores | Fresh test set |
  |---|---:|---:|---:|
  | Two half notes a third apart, each on a line, that touch (`symbols.LINE_PAIR`) | 5 and 0 | 5 and 0 | 0 and 0 |
  | Two filled heads a second apart that overlap across their stems (`symbols.PAIR_OVER`) | 3 and 0 | 8 and 0 | 0 and 0 |
  | The round | 8 and 0 | 13 and 0 | 0 and 0 |

  The round changes 18 pages of LitChoir and no page of the fresh set.
- Two half notes a third apart on lines (`symbols.LINE_PAIR`), round 41. Two voices sing a third, both notes
  stand on a line, and the print lets the two hollow heads touch. The staff line cuts the inside of each head
  in two, so the mark has four small holes, and the half at the upper or the lower rim is often too slim to be
  a hole. Three holes were read as three heads in one column: the two true notes came out a step off, or one
  of them twice. A hollow mark one head wide and about two heads high holds two heads and no more, and its
  middle lies between them: the heads are set a step over and a step under the middle of the mark, not at the
  middles of the holes. In its first form (the size of the mark, three holes, and insides that are a fifth of
  a head's box or more: two filled heads with specks of paper between them have less) the rule gained 5 notes
  on the clean copies and lost none, and gained 1 and lost 5 on three copies that are not clean. It acted at 36 marks, and 27 were such
  pairs. The other 9 were two half notes a second apart with their two stems (two of the three holes stand
  side by side), a half note and the room between it and its sign, the leaves of an ornament in a title, and
  a scribble by hand at the start of a staff. The shape of the true pair parts them: its three holes stand one
  over the other, each a quarter of a head or more under the one before, and in a zigzag, because the inside
  of a head leans (the upper half of a hole lies right of its lower half); and the two heads are half notes,
  so a stem goes a staff space or more past the mark. The scribble had the holes of a pair, and no stem. All
  27 true pairs stay with the narrowed rule, and none of the 9 others changes any more. The one note that the
  first form gained off the clean copies stood on a page where it acted at a mark that is no such pair; it is
  not gained now. The 27 pairs stand in five scores.
- Two heads that overlap across their stems (`symbols.PAIR_OVER`), round 41. The rule of round 19 for two
  voices a second apart cuts the blot of the two heads at the stem: the upper head at the left, the lower one
  at the right. Some prints set the two heads closer: the stem of the upper voice goes up at the right of its
  head, the stem of the lower voice goes down at the left of its head, and the heads lie over each other for
  half their width. The cut at the stem then leaves one part narrower than a head can be, and that part was
  dropped: one voice was missing. Where a part is that narrow, each head is as wide as a head from its own
  side of the piece, and how the piece leans is read from the columns that only one head has. A first limit
  (a part under three quarters of a head) changed a cut that had worked and lost a tie; the limit is the least
  width of a head now. In its first reading the rule also wrote 2 notes that are not there: the stem up and
  the stem down of such a pair are one upright stroke through both heads, each head had followed its own stem
  from its own side, the stroke between the two was taken for a stem without a head, and the beam at its end
  was read as the thin head of a third voice. A stroke that goes through a head of such a pair is the pair's
  stem now (`symbols._across`). Alone the rule gains 3 notes on the clean copies and 8 on all scores and loses
  none; it changes 9 pages (two of them are a second copy of one hymn), and each of its 10 places was looked
  at on the page: all are two heads a second apart, and at two of them both heads were read before and only
  the cut moved. One of the new notes is read as an eighth where the page prints a quarter (its stem is broken on the
  scan): it counts as a note that is not there. The fresh set holds no such pair.
- A note that the page holds, by the page (round 41). The count by the page knew a note that is typed with
  another pitch or another length than the page prints. A third kind: the page prints one long note, or a
  note tied over a bar line, and the hymn is typed with that note struck again with each chord of the other
  voices of the part. The reader reads the page's one note, and the typed notes after it counted as missed.
  The list of the notes by the page can now say that a typed note is held (the moments at which the page does
  not strike it again, and the length that the page gives it). A typed chord has one length, so the scorer
  takes the held note out of its chord and counts it as a note of its own. Four places went on the list, each
  looked at on the page: a whole note tied to a whole note under three chords, a dotted whole note under two,
  a half note tied to an eighth, and a whole note tied to a half note. 9 typed notes are no notes of their own
  any more, and 7 notes more count as right. The count as typed is unchanged, and the reading before the round
  gives the same figures with the changed scorer and the list as it was. The candidates were named by a
  finder (a read note that is longer than its typed note, with the typed pitch struck again while it sounds):
  7 places, of which 3 were left off the list, because their bows may be slurs. The finder sees only places
  where the reader reads the long note; the list holds 51 notes in 15 scores now.
- Counted in round 41 and left without a rule. A whole-note chord whose notes are tied on: the print draws one
  bow for the chord, the lower whole note takes the rim of the upper one and the start of the bow for a stem
  and is read as a half note; the cause of the stem holds one place on the clean copies. Whole notes of one
  worn print that are left as two crescents. A dotted chord without stems before a quarter rest, which the
  hymn is typed with at half its length (a misprint or another edition). 60 notes of the clean copies are a
  semitone off: about 15 are a flat, a sharp or a natural that touches its head or a ledger line, and each of
  the four that were traced has another cause (a flat that is named a natural by the stem of the next note, a
  flat and its head as one mark, a flat that is read and not given to its note, a flat, a head and two ledger
  lines that are named a beam). A head between two others on one stem that is named a sharp because the stem
  runs through it.
- Round 40 (17 November 2026): the words that follow each other in the list. No note of the reader changed in
  this round, on LitChoir, on the fresh set and on the kit. The 218 syllables that the clean copies lacked
  after round 39 were sorted by what the reader wrote in their place: about 50 are one or two misread letters
  of one word, about 95 a row or a part of a row that was read as other words (30 of them a response lettered
  by hand on two scans), about 60 a word that was not read at all (among them "Al - le - lu - ia" under a
  long melody on four scores), and 17 a word that was read with its letters but parted otherwise. No cause holds more than
  a dozen. Many of the misread words are short, and a short word is not mended by the list: too many words
  are one letter away. But the hymns of one church say the same phrases again and again. A list of words
  that is plain text now also tells which words follow each other (`lex.pairs`; `bench/wordlist.py --text`
  writes such a list), and three rules use it. The hymn that is read and its other scans are left out of
  the list as before, so no score is read with its own text.

  The clean copies went from 6,021 to 6,026 of 6,239 syllables (96.6 %; 5 gained, none lost; as typed 5,973
  of 6,259), their whole words from 4,259 to 4,264 of 4,515 (94.4 %). 31 scores have 99 % of their
  syllables, as before, and 195 syllables are lacking for 99 % of each score (200 before; 213 are missing in
  all). All scores went from 25,254 to 25,322 of 28,680 syllables (88.3 %; 69 gained, 1 lost; as typed
  25,144 of 28,700), the thick copies from 1,742 to 1,746 of 1,980 and the copies by hand from 11,838 to
  11,897 of 14,356; the whole words of all scores from 16,605 to 16,673 of 20,578. Each rule alone, switched
  off against the others on, counted from the stored rows (syllables gained and lost):

  | Rule | Clean copies | All scan pages | Fresh test set |
  |---|---:|---:|---:|
  | A word of three letters or fewer that the list lacks is the list's word one letter away that stands between the same two neighbours (`ocr.PAIR`) | 2 and 0 | 30 and 0 | 0 and 0 |
  | A word that does not stand with both neighbours is taken from another reading of the row where that one does (`ocr.PAIR_OTHER`) | 2 and 0 | 34 and 1 | 0 and 0 |
  | Two words side by side are one word although the list holds one of them as a rare word (`ocr.MEND_PAIR_RARE`) | 1 and 0 | 3 and 0 | 1 and 0 |
  | The round, by this count | 5 and 0 | 67 and 1 | 1 and 0 |
  | The round, on the pages that it changes, read with Tesseract | 5 and 0 | 69 and 1 | 1 and 0 |
  | the same, in whole words | 5 and 0 | 69 and 1 | 0 and 1 |

  The rules choose among stored readings and mend words, so the count from the stored rows names the pages
  that they change exactly: 73 pages of LitChoir and 1 of the fresh set, which were read again with Tesseract
  against the full runs of round 39.
- A short word by its two neighbours (`ocr.PAIR`), round 40. "Lord tq have mercy": the list does not hold
  "tq", and "to", "ty", "tr" are all one letter away. The list's text holds "Lord to" and "to have", and no
  other word one letter away stands between those two. The rule asks for both neighbours, as they were
  read, and for one such word only. A census of every word that such a rule would change, labelled by the
  typed hymn, set these limits. With both neighbours, a short word that the list lacks: 31 right and none
  wrong on all scan pages. With one neighbour: 23 right and 3 wrong in the census, and in the count 27
  syllables gained and 37 lost, because a piece that is changed into a word is no longer joined to the word
  that it is a piece of. A word that the list holds is not changed by its neighbours (with one neighbour on
  its own side: 8 right and 85 wrong), and a longer word that the list lacks is a true word of the hymn as
  often as a misread (18 and 16). Choosing all words of a row together, so that most pairs hold, changed
  more words wrongly (5 of 44) than one word at a time.
- A word from another reading by its neighbours (`ocr.PAIR_OTHER`), round 40. A row is read at three sizes,
  without the ink that crosses it and with the larger files, and one reading is kept. A word of it that
  does not stand with both of its neighbours in the list's text becomes the word that another reading holds
  at the same place, where that word stands with both and the other readings hold one such word only. The
  word that goes can be a word of the list here ("at thy night hand" where another reading has "right"): the
  other reading has read it from the page. With the kept word standing with neither neighbour the rule
  gained 26 syllables on all scan pages and lost none; with one neighbour allowed, 34 and 1.
- A rare piece in the list (`ocr.MEND_PAIR_RARE`), round 40. Two words side by side that the list does not
  hold are mended into the one word that they are with one letter read otherwise ("Al-le-lu la", round 37).
  The list, made from typed hymns, held "la" three times and "allelu" once as words, and such a pair stayed.
  It is mended now where the list holds the whole twenty times as often as the piece. On the fresh set this
  joins two words on one page: a syllable more and a whole word fewer.
- Counted in round 40 and dropped. Pairs in the choice among the readings of a row (a reading counts higher
  for each pair that it holds): 10 syllables gained and 7 lost on all scan pages. Pairs as the choice among
  several words of the list that are one letter away from a longer misread word: 2 gained on the clean
  copies, 12 and 4 on all scan pages, and 4 lost on the fresh set, on a carol whose words are not the list's.
  A number or a sign alone between two words as the word of one letter that stands between them in the
  list ("by 4 star", the a of a typewriter): no row changes, because that phrase stands in this hymn only,
  and a census found one such a on the clean copies. Looked at and left: a typewriter print whose i is read
  as l or as an exclamation mark at every size and with every file ("Na - ti - vi - ty" in three scans of
  one print, 5 syllables each); that is a matter for the page's own letter shapes.
- Round 39 (17 November 2026): Tesseract's larger language files as further opinions. No note of the reader
  changed in this round, on LitChoir, on the fresh set and on the kit. (Round 38 was the new name of the
  project and the short README, and held no rule.) Tesseract comes with a small English file. Its own
  repositories hold two larger ones, the standard file (23 MB) and the "best" file (15 MB), both under the
  Apache-2.0 licence. The owner allowed them (16 November 2026: "use the big one"). Neither is added to this
  repository: `--second <folder>` (or `SCOREREADER_OCR_SECOND`) names the folder of such a file, and two
  folders are named with a colon between them.

  First the standard file was put in the place of the small one, in a full run of the clean copies: 26
  syllables gained and 81 lost. The limits of how sure Tesseract must be were set with the small file, and
  the larger network reads a stroke as the word I and a faint row as words. So the small file stays the first
  reader, and the larger files are further opinions (`ocr.SECOND`): a row of which no reading with the small
  file holds only words of the list, at its three sizes and in the second look, is read with the "best" file
  and then with the standard file, at the three sizes each. The two misread different words, and both
  together read more than either alone.

  The clean copies went from 5,994 to 6,021 of 6,239 syllables (96.5 %; 28 gained, 1 lost; as typed 5,968
  of 6,259), their whole words from 4,228 to 4,259 of 4,515 (94.3 %; 32 gained, 1 lost). 31 scores have 99 %
  of their syllables (28 before), and 200 syllables are lacking for 99 % of each score (227 before; 218 are
  missing in all). The one syllable lost is in a score that prints only "Al - le - lu - ia": a reading of a
  larger file has "a" for "al" in one row. All scores went from 25,058 to 25,254 of 28,680 syllables
  (88.1 %; 217 gained, 21 lost; as typed 25,076 of 28,700), the thick copies from 1,733 to 1,742 of 1,980
  and the copies by hand from 11,678 to 11,838 of 14,356; the whole words of all scores from 16,404 to
  16,605 of 20,578 (212 gained, 11 lost). The reader writes 62 syllables more than before on all scores
  (27,907), and 196 more of them are right. Each rule alone, switched off against the others on, counted
  from the stored rows (syllables gained and lost; the rows of each larger file were stored once for every
  scan page and for the fresh set):

  | Rule | Clean copies | All scan pages | Fresh test set |
  |---|---:|---:|---:|
  | An s at the end of a word is neither taken away nor added by the mending (`ocr.MEND_S`) | 6 and 1 | 12 and 8 | 1 and 0 |
  | A stroke alone between two words is the word I by its ink (`ocr.LONE_I`) | 3 and 0 | 4 and 0 | 0 and 0 |
  | The two larger files as further opinions, with their guards (`ocr.SECOND`) | 21 and 2 | 212 and 20 | 45 and 0 |
  | the "best" file alone | 15 and 2 | 189 and 22 | 42 and 0 |
  | the standard file alone | 17 and 2 | 138 and 14 | 38 and 0 |
  | Guard: a word that the small file read with the same letters is not mended in a further reading (`ocr.SECOND_MEND`), against no mending there | 9 and 1 | 58 and 20 | 2 and 1 |
  | Guard: a further reading that lacks a word which the small file read alike at each size, and has fewer letters, is not kept (`ocr.SECOND_FIRM`) | 4 and 0 | 29 and 12 | 1 and 0 |
  | Guard: words of one letter do not count as words of the list in a further reading (`ocr.SECOND_MORE`) | 2 and 2 | 7 and 12 | 0 and 6 |
  | The round, by this count | 29 and 1 | 223 and 18 | 45 and 0 |
  | The round, in the full runs | 28 and 1 | 217 and 21 | 44 and 0 |
  | the same, in whole words | 32 and 1 | 212 and 11 | 39 and 0 |

  The full runs read every scan page of LitChoir and the fresh set with Tesseract; after the last change of a
  guard, the 41 pages of LitChoir and the 2 of the fresh set whose rows it moves were read again.
- A further reading is kept by the list alone (`ocr.SECOND`), round 39. How sure two readers are does not
  compare: the "best" file is sure of a row that it misreads. A reading of a larger file takes the place of
  the reading that stands only where it leaves fewer letters in words that the list lacks, and no fewer
  letters in words of the list. The first form of this gained 22 syllables on the clean copies and lost 10,
  and the lost ones showed three ways in which the count is fooled; each has its guard.
  A word of the hymn that the list lacks is mended to a word of the list in the reading that is less sure
  of it ("cries" became "cried"). A word that the small file read with the same letters is not mended in a
  further reading: two readers that agree have read the page (`ocr.SECOND_MEND`).
  A misread that makes such a word shorter leaves fewer letters outside the list ("patience" as "patence",
  the label "Ison" as "son"). A further reading that lacks a word which the small file read alike at each
  of its sizes, and that has fewer letters than the reading that stands, is not kept (`ocr.SECOND_FIRM`).
  A second half of this guard (no new word outside the list in the place of such a word) gained 6 syllables
  and lost 15 on all scan pages when it was counted alone, and lost 3 on the fresh set: it was taken out.
  A stroke that a larger file reads as the word I, or a blot as "a", adds a letter of the list. Words of
  one letter do not count as words of the list there (`ocr.SECOND_MORE`). This guard costs syllables in the
  count: level on the clean copies, 5 more lost than gained on all scan pages, and 6 lost on the fresh set
  with none gained. It is kept for what the count does not see: without it the reader writes 27 more false
  words of one letter on all scan pages (16 of them the word I; 6 of the 27 on the clean copies, 20 on the
  copies by hand), in rows like three strokes read as "I I I". The fresh set, crisp pages with no stray
  strokes, has no such word either way. Three milder forms were counted and gave the fresh set nothing back:
  a word of one letter counts as often as the small file read it too (5 gained and 2 lost on all scan
  pages, nothing on the clean copies and on the fresh set), it counts neither for nor against a reading (6
  and 12, and 13 lost on the fresh set), it counts where the reading has no more words than the one that
  stands (6 and 4, nothing on the fresh set).
- An s at the end of a word (`ocr.MEND_S`), round 39. The mending takes a letter away, adds one or changes
  one to reach a word of the list. The list holds the singular of nearly every plural and the plural of
  many words, so it cannot choose between them: of the words that lost a last s by the mending on all scan
  pages 26 were wrong and 12 right. An s at the end is neither taken away nor added now. With the larger
  files on, 4 of the 8 syllables that the rule loses on all scan pages are one row of a copy by hand where
  the s was rightly taken away before and another reading stands now.
- A stroke alone between two words (`ocr.LONE_I`), round 39. Tesseract writes the sign "|" for a bar line
  that crosses the words, for a line by hand and for the letter I, and the word alone cannot tell them
  apart: of the strokes that stand alone on LitChoir's scan pages few are the letter. The ink tells. The
  letter is as high as the capitals of its row and stands on the row's line, and it is as thick as the
  strokes of the row's letters (0.8 to 1.25 times on LitChoir's pages; the limits are 0.7 and 1.5). A bar
  line goes on over the row, and a line by hand or a dashed bar line is a hairline (0.3 to 0.4 times). The
  count from the stored rows hands the page itself to this rule.
- Counted in round 39 and dropped. Single words taken from a larger file's reading into the reading that
  stands (the list's word at the same place): 6 syllables gained and 5 lost on the clean copies; the
  commonest word wins there, and a rare true word loses. A further reading only where it is whole: 8
  gained and none lost, too few. No further reading where the small file read no row of words at all: it
  loses 5 of the gains. A guard that keeps every word of the list that the standing reading has: fewer
  gains and the same losses. Counted and left without a rule: digits of a verse number that are read as a
  part of the first word (7 places of the clean copies), and the rows under the two staves of a system
  that print the same words (14 syllables at most).
- A folder with only a language file, round 39. Such a folder holds no config files of Tesseract. Asked for
  its table of words by the config file `tsv`, Tesseract printed nothing, and a first run with the standard
  file read no word at all. The table is asked for by its setting now (`-c tessedit_create_tsv=1`).
- Round 37 (16 November 2026): the words by the page, for every kind of difference. No note of the reader
  changed in this round, on LitChoir, on the fresh set and on the kit. The owner's rule of that day: where the
  page says one thing and the typed hymn another, the page is the source of truth. The typed syllables of the
  clean copies that the reader does not have were set against what it read at their place (293 places), and
  each place where the reading could be the page's own word was looked at on the page: 45 candidates. 25 places
  in 8 scores are the page's, and stand on a list outside git with their place on the page:

  | What the page prints otherwise than the hymn is typed | Places |
  |---|---:|
  | A hymn of exercises is typed with the heading over each staff ("Tone 1") as the first word under the notes; the page prints the label "Ison:" there | 10 |
  | A word that the page spells otherwise: at each of its six places in one hymn, and once in three other scores | 9 |
  | A word that the page prints whole under two or three notes, typed in syllables | 3 |
  | A syllable that the page prints in two pieces under its notes ("sea-t"), typed as one | 3 |

  About 20 candidates were the reader's mistakes and stay as typed: a word that the list parts further than
  the page prints it ("hal - lowed" under two notes, read in three pieces), a letter that was read wrongly,
  a word at the end of a row. The count of the syllables moves with the list, because the page can print
  another number of syllables than the hymn is typed with: the clean copies have 15 fewer. A word that the
  page parts in two ways (the typed way in one line, another way in the next) is counted place by place now;
  the count of the hyphens of round 35 left such a word as typed (2 syllables on the clean copies, 10 on all
  scores). And one clean scan shows its first system only as far as the second note after the first bar
  line: the rest of the system is white, a sheet lay over it when the page was copied. The 12 typed notes
  there were listed apart already, as a repeat that the page prints once; they are listed as what the scan
  does not show now, and their 5 syllables with them (2 more notes of that score line up as right). With the
  reading of round 36 the count alone moves the clean copies from 5,956 of 6,259 to 5,974 of 6,239 syllables,
  and all scores from 25,007 of 28,700 to 25,033 of 28,680. Counted as typed (`AS_TYPED=1`), the reading of
  round 36 gives the figures of round 36 exactly.

  The reader got three rules for the words. The clean copies went from 5,974 to 5,994 of 6,239 syllables
  (96.1 %; 20 gained, none lost; as typed 5,940 of 6,259), their whole words from 4,210 to 4,228 of 4,515
  (93.6 %). 28 scores have 99 % of their syllables, as before, and 227 syllables are lacking for 99 % of each
  score (285 before the round, 247 by the count alone). All scores went from 25,033 to 25,058 of 28,680
  syllables (87.4 %; 26 gained and 1 lost; as typed 24,877). Each rule alone, switched off against the others
  on, counted from the stored rows (syllables gained and lost):

  | Rule | Clean copies | All scan pages | Fresh test set |
  |---|---:|---:|---:|
  | The first word of a row with a colon behind it is a label and stays whole (`ocr.LABEL`) | ten rows of one hymn change | no other row changes | no row changes |
  | A stray first row under a staff (`ocr.FIRST`) | 7 and 0 | 7 and 0 | 28 and 0 |
  | Two words side by side that are one word of the list with one letter read otherwise (`ocr.MEND_PAIR`) | 2 and 0 | 8 and 1 | 0 and 0 |
  | All three, in the full runs | 20 and 0 | 26 and 1 | 29 and 0 |
  | the same, in whole words | 18 and 0 | 26 and 3 | 13 and 0 |

  The quick count from the stored rows counts as the kit does, without the list of the words by the page, so
  it cannot count the label: the hymn of exercises gains 18 syllables in the full run, 10 labels and 8
  syllables of a row that a stray row hid.
- A label (`ocr.LABEL`), round 37. A word that the list does not hold is parted where the list holds the words
  on both sides, and the label "Ison:" under the first note of a line came out as "Is on:". The first word of
  a row that begins with a capital and has a colon behind it stays whole. On all scan pages and on the fresh
  set no other row changes.
- A stray first row under a staff (`ocr.FIRST`), round 37. The first row under a staff holds the first verse,
  and only that row is set under the notes. On three pages a note by hand or a scribble stands close under
  the staff, Tesseract reads it as a row of short words ("a", "I", "on", "as" are words of the list), and the
  row of the words under it was left out whole. Where Tesseract is less sure of the letters of the first row
  than 50 of 100 and is sure of the next row under the staff (80), the first row is stray. A first form with
  a limit of 60, for rows where the next row holds as many syllables or more, lost 9 syllables on LitChoir's
  pages and gained none: true first rows begin at 51 there. On the fresh set the rule finds two pages
  of the same kind (29 syllables).
- Two words that are one (`ocr.MEND_PAIR`), round 37. The end of a word under a long melody stands far from
  its start, and no hyphen is read between them. Two words side by side that the list does not hold, of seven
  letters or more together, become the one word of the list that they are with one letter read otherwise;
  the last letter is never the one that changes (the end of a word changes in the language itself).
- Counted in round 37 and dropped. A word that the page parts with a hyphen of its own is not parted further
  by the list: 4 syllables gained and 6 lost on the clean copies, 7 and 28 on all scan pages, none and 115 on
  the fresh set. A scan loses a hyphen far more often than a page sets two syllables under one note. Counted
  and left: a lone "Al - le - lu - i - a" under a long melody whose syllables stand so far apart that
  Tesseract reads three of the five as signs (the row is found since round 36, and its reading must hold only
  words of the list); pages of a service with the priest's lines between the staves; and the hand-lettered
  response of two scans.
- Round 36 (16 November 2026): rows of words that ink crosses, and rows of few words. No note changed in this
  round, on LitChoir, on the fresh set and on the kit. After round 35 five clean scores lacked 21 to 33
  syllables each. One of them prints its bar lines through the rows of the words, and slurs and stems hang into
  them. And a census of the stretches between staves that hold no row of words showed rows that were no rows
  at all: a word that is held over a long melody ("A - men", "Al - le - lu - i - a") crosses fewer letters than
  a row of words must. Two rules and a guard were kept. The clean copies went from 5,856 of 6,240 to 5,956 of
  6,259 syllables (95.2 %): 108 gained and 8 lost, and 19 syllables that were counted apart before, as words
  that no page prints, stand in such rows and are counted now; counted as typed they are 5,930. The whole words
  went from 4,148 of 4,531 to 4,202 of 4,534 (92.7 %). 28 scores have 99 % of their syllables (25 before; four
  came, one with 20 syllables lost one and went), and 285 syllables are lacking for 99 % of each score (366
  before). All scores went from 24,536 of 28,692 to 25,007 of 28,700 syllables (87.1 %): 500 gained and 29
  lost; as typed they are 24,862. The scans went from 83.6 % to 85.7 %, the thick copies from 83.6 % to 87.5 %
  and the copies by hand from 79.1 % to 81.3 %. Each rule alone, switched off against the others on, counted
  from the stored rows, which hold the second look and the rows of few words since this round (syllables
  gained and lost):

  | Rule | Clean copies | All scan pages | Fresh test set |
  |---|---:|---:|---:|
  | A second look at a row without the ink that crosses it (`ocr.CROSS`) | 60 and 11 | 372 and 34 | 19 and 10 |
  | On a page whose words do not fit the list, the second look must hold more letters in words of the list (`ocr.CROSS_LIST`) | 0 and 0 | 3 and 1 | 18 and 19 |
  | A row of few words between two staves (`words.SPARSE`) | 52 and 0 | 144 and 0 | 24 and 0 |
  | All three, from the stored rows | 108 and 10 | 498 and 31 | 43 and 10 |
  | All three, in the full runs | 108 and 8 | 500 and 29 | 44 and 10 |
  | the same, in whole words | 61 and 7 | 346 and 19 | 39 and 12 |

  The syllables lost are single ones in 22 scores: a word that the second look reads otherwise than the picture
  as it is, in a row where it reads another word rightly. No cause holds more than three of them.
- A second look at a row that ink crosses (`ocr.CROSS`), round 36. On one clean score the bar lines of the
  system run through the rows of the words, slurs hang into them and stems end in them, and Tesseract read
  such a row as a row of signs. The ink that crosses the row is taken out of the picture. An upright stroke
  that is longer than a letter (1.8 staff spaces and 1.3 row heights), or that comes in over the edge of the
  page around the row, goes outside the letters; between the letters it goes where it runs on past them at
  both sides (a bar line) or where no ink hangs on it (a stem that ends in the row). A stem that touches a
  letter keeps its part in the row, so the letter keeps every stroke. A slur goes where it is one thin stroke
  in each column over three row heights or more, and rises or falls by 0.4 of a row height: the line of a held
  syllable and a row of dashes are level, and stay. Each form was read with Tesseract on the 155 clean pages
  (syllables gained and lost). All ink that touches the edge of the picture: 65 and 170, the tails of the
  letters at the edge went too. All ink that comes from two staff spaces away, but for the wide columns of a
  letter: 72 and 71, a letter that a stem touches lost its thin strokes. Upright strokes and long pieces of
  ink: 63 and 55, because the line of a held syllable joins its letters into one long piece, and because the
  tops of d and h are longer than a row is high where the row holds small letters only. With the slur as one
  thin stroke that rises, and the height of a letter taken from the staff space: 59 and 40. These 40 were words
  that the rule had not touched: with one bar line gone at the left of a row, Tesseract read a word in the
  middle of it otherwise. So the picture without the crossing ink is a second look, as the two other sizes are.
  It is read, at the three sizes, only where no reading of the picture as it is holds only words of the list,
  and the reading that fits the list best is kept: 63 and 19. Ten of the 19 were one row of stems and marks
  over a row of words, which the second look read as two short words. Where no reading of the picture as it is
  was a row of words, the second look is tested as a row that Tesseract is not sure of (the list holds the
  words of half its letters): 57 and 9.
- The second look on a page in another language (`ocr.CROSS_LIST`), round 36. The fresh set was read with the
  rule before it was kept: 38 syllables gained and 28 lost, in English 18 and 1, in Romanian 12 and 24. The
  list of words is made of LitChoir's hymns and holds few Romanian words, so it cannot choose between two
  readings there, and how sure Tesseract is chose instead. LitChoir shows the same on its three hymns in Arabic
  and Greek, which lost two syllables each. The guard was set on LitChoir's pages, in three forms. No second
  look on a page whose words do not fit the list (the share of `ocr.MEND`): 9 syllables gained and 21 lost,
  because a page whose rows are read as stray ink does not fit the list either, and those rows are what the
  rule is for. The second look is kept only where it holds more letters in words of the list, on every page:
  level on all scans (25 and 27) and 3 lost on the clean copies. That test on the pages that do not fit the
  list alone: 3 and 1, and the clean copies as without it. On the fresh set it gains and loses 18 and 19
  syllables and brings 11 whole words; the Romanian pieces still lose some (see the fresh set below).
- A row of few words (`words.SPARSE`), round 36. A row of words is a row of the page that crosses eight letters
  or more. "A - men." under a long melody crosses four, and the last "Al - le - lu - i - a" of a communion hymn
  six: such a row was no row, and its syllables were lost before Tesseract saw them (about 25 rows on the clean
  pages; the typed syllables of some were counted apart, as words that no page prints). A stretch between two
  staves, or under the last staff, that holds no row of words now gives its best row of four letters or more to
  the step that reads the words. The notes are read with the rows as they were. Such a stretch also holds
  tempo marks, bar numbers, the letters of a rehearsal mark and the names of the parts, so the reading of a
  row of few words counts only when the list holds every word of it, with no word mended, and when it is not
  one word with a colon ("Refrain:", "Women:"). On the clean copies it adds 54 syllables under the notes and 52
  of them are right; on all scans it gains 144 syllables and loses none, on the fresh set 24 and none. The own
  letter reader does not read these rows: it has no such test yet.
- Counted in round 36 and left. A response that is lettered by hand on a printed page, with the stems drawn
  through its letters (two clean scores, about 20 syllables). A piece of a word with no vowel that stands as a
  syllable of its own ("sea- t", 5 on the clean copies): the list joins such a piece only where it holds the
  word. And words that a hymn is typed otherwise than its page prints: "Ison:" under the first note of each
  line where the hymn is typed "Tone 1:" (33 syllables of one score), "wed-ded" typed "wed-ed", "lu-ia" under
  two notes typed "lu-i-a". The owner decided on 16 November 2026 that the page is the source of truth for
  these too; the next round makes the list of them, each looked at on the page, as round 32 did for the notes.
- Round 35 (16 November 2026): single misread words on the clean copies, and the hyphens counted by the page.
  No note changed in this round, on LitChoir, on the fresh set and on the kit. After round 34, 27 clean scores
  lacked 1 to 4 syllables for 99 %. What they lacked were single words that Tesseract misread ("thov" for
  "thou", the word O read as Q, as © or as a 0), and hyphens that the page sets at another place than the
  typed hymn. Six rules were kept, and the scorer counts such a hyphen by the page. The clean copies went from
  5,814 to 5,856 of 6,240 syllables (93.8 %): 24 by the count and 18 by the rules, none lost; counted as typed
  they are 5,832. The whole words went from 4,132 to 4,148 of 4,531 (91.5 %). 25 scores have 99 % of their
  syllables (20 before; 22 as typed), and 366 syllables are lacking for 99 % of each score (408 before). All
  scores went from 24,259 to 24,536 of 28,692 syllables (85.5 %): 139 by the count, and 143 gained and 5 lost
  by the rules; as typed they are 24,395. Each rule alone, switched off against the five others on, counted
  from the stored rows (syllables gained and lost):

  | Rule | Clean copies | All scan pages | Fresh test set |
  |---|---:|---:|---:|
  | A sure word with two runs of three letters that no word of the list holds is mended (`ocr.MEND_ODD`) | 0 and 0 | 7 and 2 | 0 and 0 |
  | A sure word that is one letter from one of the list's commonest words is mended (`ocr.MEND_OFTEN`) | 3 and 0 | 17 and 3 | 4 and 3 |
  | A reading with a mended word is not whole: the other sizes are read too (`ocr.MEND_WHOLE`) | 3 and 0 | 8 and 0 | 0 and 1 |
  | A word that the list does not hold becomes the word that another size read at its place (`ocr.OTHER_SIZE`) | 1 and 0 | 64 and 2 | 0 and 0 |
  | A 0 with a hyphen beside it is the syllable o (`ocr.DIGIT_JOIN`) | 3 and 0 | 5 and 0 | 0 and 0 |
  | The word O read as Q, QO or © (`ocr.ROUND`) | 8 and 0 | 26 and 0 | 0 and 0 |
  | All six, from the stored rows | 18 and 0 | 144 and 5 | 4 and 3 |
  | All six, in the full runs | 18 and 0 | 143 and 5 | 4 and 3 |
  | the same, in whole words | 16 and 0 | 133 and 0 | 4 and 2 |

- Hyphens by the page, round 35 (the owner, 16 November 2026: "Count by the page"). The wide test counts a
  syllable as right when its letters are those of the typed syllable. A page that prints "scend-ed" where the
  hymn is typed "scen-ded" then loses two syllables that it reads exactly as they are printed: 14 words on the
  clean copies, each from the page's own hyphens. A typed word that was read with the same
  letters in the same number of syllables now counts as the page parts it. The scorer tries this staff by
  staff and keeps it only where the staff counts higher; the typed hymns stay as they are. It brings 139
  syllables on all scores (24 on the clean copies) and loses none; whole words and notes do not change.
  Counted as typed (`AS_TYPED=1`) the reading of round 34 gives its figures exactly. The fresh set is not
  counted so: its answers are the engraver's own files, and they stay exact. Not counted so either: a word
  that the page parts into more syllables than the typed hymn has (12 on the clean copies).
- Sure words that are misread (`ocr.MEND_ODD`, `ocr.MEND_OFTEN`), round 35. The list of words mends a word
  that is one letter from a word of the list, but only where Tesseract was not sure of it: a sure word that
  the list lacks is most often a true word ("banner" beside "manner"). Mending every sure word gained 42
  syllables on all scans and lost 32. A census of every word that this would change, each labelled by the
  typed hymn (the new word is typed and the read one is not: right; the read word is typed: wrong), showed two
  things that separate. A word with two runs of three letters that no word of the list holds, its beginning
  and its end counted, is no word of the list's language: 71 right and none wrong, where one such run gave 34
  and 21. And a word that becomes one of the list's commonest words (held 6 % as often as the commonest one)
  is right at the end of the word too, where the language itself changes a word ("stones", "stone"): 38 right
  and none wrong among the words that were not mended before. Two guards came from the pages: a piece of a
  word whose hyphen was not read is no misread word ("glori ous" is no "glory"), and a word that goes on in
  the next row is not whole. What the second rule loses on LitChoir (3 syllables): the last syllable of a
  word whose first syllable was misread too (the "thor" of "au-thor" is "thou" now), and two rows of which
  another reading is kept now. The fresh set showed its limit: LitChoir's hymns share their words, so the list
  lacks few true words there, and the pieces of the fresh set have words of their own. Of the 9 words that
  the rule changes there, 6 are right, 2 are true words that the list lacks, each one letter from a common
  word, and 1 is a syllable that the page spreads under its notes with its vowel doubled. A narrower form
  (only a word with a run of three letters that the list does not hold) did not part them, because the runs
  come from the same list, and it gained 9 syllables on LitChoir where the kept form gains 17: not kept.
- A mended reading is not whole (`ocr.MEND_WHOLE`), round 35. The first form of the rule before changed 60
  words on all scans, all of them rightly, and lost 6 syllables all the same. A row is read at 40 px first,
  and at 32 and 50 px only when the list does not hold each of its words. With one more word mended, the first
  reading held every word, the other sizes were not read, and a syllable that only they had read stayed lost
  beside the mended word. A reading with a mended word is a reading with a mistake in it, so the other sizes
  are read as well and the one that fits the list best is kept. It costs no time that the full run shows (22
  minutes for LitChoir, as before). Taking letters off the fit of a reading for each mended word was counted
  too and lost more than it gained (24 and 14 on all scans): not kept. On the fresh set this rule and the
  rule before lose one syllable together that neither loses alone.
- A word from another size (`ocr.OTHER_SIZE`), round 35. One reading of the three is kept whole, and each
  reading has its own misread words. A word of the kept reading that the list does not hold becomes the word
  that another size read at the same place (the two share 70 % of their width), when the list holds that word
  and it is as long, or a letter longer or shorter. Of 129 words that this changes on all scans, 85 are right
  by the typed hymn, 40 are neither, and 4 were right before. Two of the 4 were a word of the list with an "s"
  behind it, a form that the list need not hold: such a word stays, and the clean copies lose nothing.
- The word O (`ocr.DIGIT_JOIN`, `ocr.ROUND`), round 35. 15 times the clean copies lost the word O, which the
  hymns begin many lines with. A 0 with a hyphen beside it was thrown out as a number: it is the syllable o
  ("The-0-to-kos"). And Tesseract reads the round letter as Q, as QO or Oo, or as the sign ©. With a list that
  holds the word O, such a word that stands alone is O. The signs were counted one by one by the line-up with
  the typed hymn: QO, OQ and Oo are an O 16 times of 16, a lone Q 2 of 8 (it was a wrong syllable before, and
  is one now), @ once in 11 (not taken). The sign © was right 17 times of 50: none of the 21 that are narrower
  than 0.7 of the row's height (a dot, a piece of a note), and two of the others stood before the year of a
  copyright line. So a © counts when it is as wide as a letter and no number follows it: 15 right, 10 not
  confirmed (a note head that hangs into the row is as round as an O). The count of right syllables cannot see
  a syllable too many; these 10 on all scans are the cost of the rule.
- Counted in round 35 and left. A typed word of one syllable that the page parts in two with a vowel in each
  piece ("low-ed", "bless-ed"; 12 on the clean copies), a misread word of three letters or fewer (the mending
  starts at four letters), a syllable that the page spreads under its notes with its vowel doubled (the fresh
  set showed one that the mending shortens; LitChoir's pages hold no such case, so no guard was written), and
  the mended word that counts as a read one when the three sizes are compared.
- Round 34 (16 November 2026): the words of the clean copies. No note changed in this round, on LitChoir, on
  the fresh set and on the kit: three causes of lost notes were counted first and gave no rule (see below), and
  the round turned to the words, which lack more. Three rules were kept. The clean copies went from 5,781 to
  5,814 of 6,240 syllables (93.2 %; 33 gained, none lost) and from 4,119 to 4,132 of 4,531 whole words (91.2 %);
  20 scores have 99 % of their syllables (19 before), and 408 syllables are lacking for 99 % of each score (441
  before). All scores went from 24,196 to 24,259 of 28,692 syllables (84.5 %; 64 gained, 1 lost). Each rule
  alone (syllables gained and lost):

  | Rule | Clean copies | All scan pages | Fresh test set |
  |---|---:|---:|---:|
  | Pieces of one word of the list are that word (`ocr.ONE`), counted from the stored rows | 7 and 0 | 14 and 1 | 3 and 0 |
  | Rows of words that stand staggered are parted by the lines that the letters stand on (`words.STAGGER`), read with Tesseract | 3 and 0 | 10 and 0 | 0 and 0 |
  | A row beside the first row under the staff goes on it (`words.BESIDE`, on top of the rule before), read with Tesseract | 23 and 0 | 40 and 0 | 0 and 0 |
  | All three, in the full runs | 33 and 0 | 64 and 1 | 3 and 0 |
  | the same, in whole words | 13 and 0 | 31 and 0 | 0 and 0 |

- Pieces of one word (`ocr.ONE`), round 34. Two things cut a word that the list of words holds. A page spreads
  one syllable under its notes with a hyphen ("wi-th", "sha-ll", "a-nd", "ki-ng"): the typed hymn has one
  syllable there, and the reader gave two. And a wide gap parts a word ("mer ciful", "a postles"). The first is
  told by the piece itself: a piece that holds no vowel is no syllable, so its hyphen stands inside a syllable.
  Such a word is one syllable when the list holds it and never parts it. The second joins two or three read
  words side by side when together they are a word of the list and one of them is no word; the list then parts
  it its own way. The first forms were read on every scan page from the stored rows: the hyphen rule gained 20
  syllables and lost 16, the rule for the gap none and 2 (with 5 whole words gained and 2 lost), where the clean
  copies had shown 9 gained and none lost. What was joined wrongly were the pieces that a misread leaves: "ma-n
  i" for "ma-ni" became "man", "pas-s on" for "pas-sion" became "pass", and a stray "t" beside "o" became "to".
  So a piece of one letter that is no vowel is never joined. A word whose pieces all hold a vowel is left as the
  page parts it ("lo-ved" is sung on two notes on one page, "tho-u" on another: the pieces do not tell them
  apart, and 5 true ones are left unread for it). A piece with a hyphen after it at the end of a row goes on in
  the next row, and a piece that is a word with its other neighbour belongs there ("the se-" before "raphim" is
  no "these": the fresh set showed this one, 2 syllables, and the guard is the hyphen that the page prints). What
  it still loses: one syllable on a copy by hand ("bur-i-al" read as "bur-st" is "burst" now).
- Rows of words that stand staggered (`words.STAGGER`, `words.BESIDE`), round 34. The rows of the words are the
  rows of the page that cross many letters. A hymn with four verses prints its refrain once, at the middle of
  the four rows and beside them; then the rows of the page never fall free of letters between the rows of the
  words, the stretch is too high for one row, and it was dropped whole: 32 pages of LitChoir (6 of clean
  copies) and 2 of the fresh set hold such a stretch. It is parted now by the lines that its letters stand on
  (five letters or more whose feet lie on one line), and each such row is as wide as its own letters, so that
  Tesseract sees nothing of the rows beside it. A row that stands beside the first row under the staff, with no
  letter over or under a letter of it, goes on that row: the refrain belongs to the first verse as to every
  other. The clean score with the refrain went from 79 to 105 of its 132 syllables, and two typewritten
  antiphons whose words change their height in the middle of a system gained 12 and 11. The new rows are for
  the words only. In the first reading they were given to the notes as well (a stem ends where a row of words
  begins), and one typewritten copy lost 4 notes: the notes are read with the rows as they were, and every note
  of the 32 pages is the same, field by field. Not read yet: the first syllable of that refrain where it
  stands alone at the end of a system between two rows (two letters are no row), about 4 syllables; and the
  typed hymn writes "wed-ed" where the page prints "wed-ded" (4 syllables that the page has right). The own
  letter reader (no Tesseract) was read on the 32 pages with the rule off and on: 15 syllables gained and 6
  lost (6 and none on the clean copies). The 6 are on two copies by hand; why was not looked at. Its figure in
  the table above is older and was not made again.
- Counted in round 34 and left without a rule. A bar with two or three notes whose length is not sure, on a
  page with full bars, takes the one choice of the lengths that fills it (`music.BAR_SEVERAL`, not kept): 3
  notes gained and 4 lost on the clean copies (a whole note became an eighth), and 1 and 1 when a length may
  only double, halve or take a dot. The census behind it, 1,898 bars on 144 clean pages: a bar that is too
  long or too short seldom holds the wrong length (26 wrong lengths in 106 such bars whose notes are all
  sure), the bars with a note that is not sure hold them (about 125 in 248). A whole note that is read with a
  stem (two whole notes one over the other, or a tie that begins at it; about 9 on the clean copies): neither
  the free length of the stem past the head, nor its width, nor a bow at its end parts them from 46 true
  half notes with a short stem. An eighth read as a quarter under a hairline beam (43, most on two
  engravings with faded stems): each has its own cause, a line that shows 0.596 of the 0.6 that is asked where a
  staff line hides it, a flag 0.72 spaces from the end of its stem where 0.7 is the limit; a limit moved there
  loses as much as it gains. A dotted half note read without its dot (14): pencil over the dots, two dots that
  one bar smeared together.
- Round 33 (16 November 2026): the notes that the clean copies still lose, sorted again. Of the 850 lost notes,
  281 have only a wrong length and 230 only a wrong pitch; the others are missed or wrong in both. No cause holds
  more than about a dozen notes. Six rules were written from the pages. Each was read alone on every page of
  LitChoir: three were kept and three switched off. The clean copies went from 21,741 to 21,749 notes of 22,591
  (96.3 %; as typed 21,702), 8 gained and none lost; 29 scores are at 99 % as before, and 681 notes are
  lacking for 99 % of each score (689 before). All scores went from 77,313 to 77,337 of 89,732 (86.2 %; as
  typed 77,290), 28 gained and 4 lost. The reader writes 892 notes on the clean copies that are not there
  (894 before). The kit did not change (6207 notes).
- A dot beside the dot of another head (`symbols.DOT_BESIDE`), round 33. One print draws the dots of its half
  notes as short dashes, and a hand draws a dot as a slanted stroke or as a blot larger than a dot. A wider limit
  for the shape of a dot gains and loses alike (round 32 counted it: 3 gained, 2 or 3 lost), and in a chord the
  two heads with a dash outvoted the one head whose dot was read. Notes that sound together agree: a mark that is
  nearly a dot, beside a head without a dot, is its dot where another head of the column has a dot at the same
  distance and is a note of the same kind. The column is one staff or two staves next to each other. Alone it
  gains 24 notes on all scores and loses 4 (4 and none on the clean copies, all 4 in the print with the
  dashes). It changes 23 pages, and each of its 26 places was looked at on the page: 23 are dots, and three are
  doubtful (a tick on a staff line, a small mark beside an eighth note); two of the three change no length. Of
  the 4 lost notes, 3 stand in one copy by hand whose dot is on the page: the notes after it line up otherwise
  in the count. The fourth stands where the page prints two dotted whole notes and the typed hymn gives them
  without a dot.
- A bold bow that is one piece of ink with its notes (`symbols.ARM`), round 33. One print draws its ties as thick
  as a head's rim. Where such a bow touches two whole notes of a chord, the notes and their two bows are one mark
  of thick ink ten staff spaces wide, and no head was read from it. The mark is opened with a disc three quarters
  of a head high: a head with its hole holds the disc, a bow does not. The bow is taken off the mark and stays on
  the page for the ties step, which finds it as it is. In its first form the rule took every long slim piece off
  a mark with a hole: it changed 100 pages, gained 27 notes and lost 41, because a beam, a flag and the stroke of
  a hand are such pieces too. Now the piece must be the bow of a tie: five staff spaces long or more, at most a
  quarter as high as long, at most 0.65 staff spaces thick on the whole, bent (its middle 0.3 staff spaces off
  the straight way between its ends), and with its two ends at one height (0.4 staff spaces). A beam on a copy by
  hand was the last false case: it is straight and it leans. Alone the rule gains 4 notes and loses none, on 4
  pages: the three pages of that print, and one page of another print, where the two heads of a tied chord are
  found that were not read before, but as quarter notes: they are dotted half notes, and they count as two notes
  that are not there. A first count said 11 notes: it was made against a score file older than the list of the
  notes that count by the page. Two more ties of the print are not read: their bows cross a staff line and are
  cut there.
- Paper that is closed in is no whole note (`symbols.CELL`), round 33. A bar line, the stem of the next note and
  two staff lines close in a cell of paper, and so do the strokes of a 4 in a time signature beside a bar line.
  The cell was read as a whole note. At both sides of a whole note's hole the ink is thick; here it is as thin
  as a stroke (0.27 staff spaces at most), and both strokes go on for a staff space past the hole. Alone the rule
  gains and loses no note; it takes away 2 notes that are not there (1 on the clean copies) on 3 pages, each
  looked at, and one on the fresh set.
- Switched off in round 33, each after its count. The side of a whole note with a bow that leaves it, read as the
  stem of the whole note under it (`symbols.RIM_BOW`): it mends one page, and in its first form it changed 51
  pages, gained 37 notes and lost 35 (3 lost on the fresh set); narrowed to two hollow heads it still changed 15
  pages, 13 of them at a sharp beside a head, a rest drawn by hand or a letter. A bow as thick as a bold tie
  counted as a tie (`ties.TIE_BOLD`): 12 gained and 10 lost on all scores, 1 and none on the clean copies. A dot
  over the end of a ledger line that the mark of its head holds (`symbols.DOT_BODY`): 6 gained, 32 lost.
- Counted in round 33 and left without a rule. One bow for a tied chord: 14 chords of the clean copies have a tie
  at one note and none at another that the next chord holds too, and the typed hymn ties both in one. A whole
  note under a half note that stands on the half note's stem: of 1,049 pairs of hollow heads one over the other,
  neither the width of the oval nor how far it sticks out past the stem parts a whole note from the second half
  note of a chord. A hollow head on a beamed stem (a rule would gain 7 and lose 9). How thick a whole note is at
  its sides: every true whole note of most prints is thicker than 0.286 staff spaces there, but one thin print
  draws them at 0.23 to 0.27. A list of 71 notes that look like unread ties (typed as long as the note and the
  next note of its pitch together) holds mostly missed dots, pencil marks and slurs; the true ties among them
  are one of a kind each. Two scores lose their notes where the page holds another ending than the typed hymn.
- The fresh test set after round 33: no note gained or lost (39,650 of 41,761), one note that is not there fewer.
  None of the three rules was set on its pages; the bow rule and the dot rule change no page there.
- The count by the page (15 November 2026). Some notes that counted as lost on the clean copies are read as the
  page prints them: the typed hymn gives another note there. They were found in three ways. The scans of one hymn
  were compared: a mistake that every scan of a hymn shares is a mistake of the print, of the reader on that
  print, or of the typed hymn. Every column of the clean copies where a typed note is not read as typed (about
  630) was laid out with the typed notes and the read notes beside the ink, and about 450 of them were looked at.
  And a census of every head beside the staff (11,459, each with the distance of its ledger line from the staff
  and of its middle from that line) showed how a print sets each note. On the print of a music typewriter one
  dash is the first ledger line wherever it stands (1.2 to 1.65 staff spaces from the staff): the dash runs
  through a head on that line and lies under a head over it. On one engraving the middle of a head on the first
  ledger line lies at most 0.2 staff space past the line (51 heads) and that of a head over the line 0.36 to 0.5
  past it (34 heads).
- What goes on the list. A note is counted by the page only when its head is unmistakable at four times the size
  (on the line or in the space, a ledger line through it or under it), or stands exactly as the same note stands
  elsewhere on its pages, and when the notes before it and after it line up as right. A line-up that has slipped
  shows the column of a neighbour, and five candidates were dropped for it: in each the reader was wrong (a chord
  that was missed, a sharp of the key that was read as a note, a natural that was read as a half note). So far
  47 notes in 14 scans of 10 hymns are on the list. 42 have another pitch, most of them a step off beside the
  staff: a head on top of a ledger line that is typed as on the line, or the other way. 9 are tenor notes of the
  typewriter print, and 6 are tenor notes of the engraving that stand as its notes over the line do; three of
  these are the first eighth of a step down where the typed hymn holds one pitch. 5 are a last chord of whole
  notes under a fermata that is typed three quarters long.
- The decision. The owner was asked and answered: trust the page. The reader is asked to read the page, so these
  notes count as the page prints them, and the typed hymns stay as they are. The list is kept with the wide test,
  outside this repository, with the place on the page for each note, so that the typed hymns can be mended from
  it. By the page the clean copies stand at 21,741 of 22,591 notes (96.2 %; as typed 21,694, 96.0 %), with 61
  scores at 95 % or more (as typed 59) and 689 notes lacking for 99 % of each score (as typed 734); 29 scores are
  at 99 %, as before. All scores stand at 77,313 of 89,732 (86.2 %; as typed 77,266). No rule of the reader
  changed: the notes that are not there, the words, the kit and the fresh test set stand as after round 31,
  and the fresh set has exact answers and no such list. Asked to count as typed, the scorer gives the figures of
  round 31 exactly. The rounds below give their figures as typed.
- What was measured and got no rule. The print of one cherubic hymn (cherubic-lvovsky, 109 notes lacking by the page) left
  the middle of its filled heads pale, and 20 quarters and eighths are read as half notes. Every hollow head with
  a stem on the clean copies was listed (5,234). The share of the hole does not part them: a higher limit for a
  print with large holes gains 6 notes there and loses 32 true half notes on other prints. The grey of the middle
  of the head does part them on its four pages (every one of 233 true half notes is paler than 14 of the false
  ones), but other prints hold true half notes on both sides of that limit, and the page shows no sure sign that
  it is such a print. These notes need the music: the lengths of the other voices of the bar. A second print draws
  the dot of five dotted half notes as a short dash. The 288 marks of the clean copies that stand where a dot
  stands and are no dot were listed: beside notes without a dot there are dashes of the same shape, and a wider
  limit gains 3 notes and loses 2 or 3. A tie's bow that is read as a short stem at a whole note costs 2 notes.
  One print draws its ledger lines no longer than its heads, and one head on the second line is lost for it.
- Round 31: the clean scores that lack few notes for 99 %, a second time. After the round before it the clean
  copies lacked 744 notes for 99 % of each score, and 13 of the 78 scores lacked one to three. The five scores
  that lack most (240 notes together) were lined up by part again and show many small causes each, as before. The
  37 mistakes of the 13 near scores were looked at on the page, and four causes stand in more than one score: a
  dot between two heads that both heads take, a bow that lies on a beam and is read as a second beam, a slur from
  the end of one stem to the end of the next that is read as a beam, and a half note on a ledger line whose slit
  the line nearly closes. Each was counted on all clean copies before a rule was written. The clean copies went
  from 21,683 of 22,591 notes to 21,694 of 22,591 (96.0 %; 11 notes gained, none lost; 29
  scores at 99 %, four more; 59 at 95 %, 73 at 90 %), all scores from 77,236 to
  77,266 of 89,732 (86.1 %; 30 gained, none lost; 83 scores at 99 %, four more), and the
  fresh test set stays at 39,650 of 41,761 (94.9 %; no note gained, none lost; 90 pieces at 99 %).
  The reader writes one note fewer that is not there on LitChoir (894 on the clean copies, 5,647 on all
  scores), and as many as before on the fresh test set (4,980). The clean copies lack 734 notes for 99 % of each
  score now. Four more scores are at 99 %: carol-great-rejoicing (336 of 339), memorial-troparia in its second
  scan (384 of 386), nativity-canon-ode-8 (181 of 182) and pascha-christ-is-risen-romanian (112 of 113). 9 scores
  lack one to three notes. The kit gains one note, in pascha-receive-long (6206 to 6207; read page by page, 6204
  to 6205).

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | One dot between two heads of a column is the dot of the lower head (`symbols.DOT_UPPER`) | 2, 0 | 3, 0 | 0, 0 |
  | A slim second beam or flag beside a full one is a bow that lies on the beam (`symbols.BEAM_SECOND`) | 5, 0 | 22, 0 | 0, 0 |
  | On a print with thick beams, a line between two stem ends whose two ends are bows is a slur (`symbols.THIN_PRINT`) | 2, 0 | 2, 0 | 0, 0 |
  | The slit of a half note on a ledger line is measured from the line that the ink shows (`symbols.SLIT_LEDGER`) | 2, 0 | 3, 0 | 0, 0 |

  Counted staff by staff the round gains the same 11 notes on the clean copies and the same 30 on all scores,
  and loses none; on the fresh set nothing moves. 28 pages of LitChoir change and one of the fresh set.
- One dot between two heads (`symbols.DOT_UPPER`). Where two voices stand a third apart in one column, a dot in the
  space between them stands at the right of both heads, and both took it. The 1,220 dots of the clean copies were
  listed with the heads that take them: 83 are taken by two heads. Where the upper head has another dot of its
  own, it is typed with a dot 56 times of 59, and the rule leaves it. Where the dot between the heads is its only
  one (0.3 staff space or more under its middle, and as much over the middle of the head below), it is typed
  without a dot 5 times and with one 3 times, and in those 3 the two notes are of one kind: both hollow or both
  filled, with as many flags or beams. There one dot can stand for both. So the dot is the lower head's, and the
  upper head keeps it only beside a note of its own kind. In the final reading 3 notes
  change on 3 pages, each from a dotted note to a plain one, and all three are gained: in nativity-canon-ode-8 and
  pascha-receive-long on the clean copies, and in a second scan of dormition-troparion.
- A bow that lies on a beam (`symbols.BEAM_SECOND`). A slur over two beamed eighths can touch their beam. The stem
  is then followed into the slur, the slur is ink that hangs on the end of the stem as a beam does, and the note
  was a sixteenth. Every lined-up note of the clean copies with two flags or beams was listed with the thickness
  of each: 39 notes. The 14 typed sixteenths are all read right, and each of their beams is 0.49 staff space
  thick or more. Of the 19 typed eighths 6 are read as sixteenths, and their second mark is at most 0.35 thick. The
  page knows its usual beam already (the middle of the beams that two stems show, where it has four or more). A second level of flags or
  beams at a stem now counts when its thickest piece, at either side of the stem, is 0.6 of that or more; where
  no level of a stem is that thick, nothing changes. The first form measured the side of the bow only and missed
  one of the six, whose beam is 0.35 thick at that side and 0.52 at the other. In the final reading 21
  pages of LitChoir change, and every one was looked at: 22 notes are gained and none is lost, 5 on the clean
  copies (carol-great-rejoicing 2, transfiguration-troparion in two scans, orthros-doxology-t6) and 17 on other
  scans, where a slur over or under a beamed pair of eighths is common (palm-hosanna in one scan, 7;
  non-liturgical-praise-ye, 3). In palm-hosanna four notes change and the score gains 7: the scorer lines up
  three more notes once the four are right, and the layout of the score is the same. On three pages only the
  count of beams at a stem changes, where the music had mended the length already, and on one a clef that is read
  as a note changes its length. The sixth of the six, in the Rachmaninov, is not mended: its beam and the bow on
  it are both 0.23 staff space thick, on a print whose beams are that thin.
- A slur between the ends of two stems on a print with thick beams (`symbols.THIN_PRINT`). A hand draws a beam as
  one thin line, and the reader takes a thin line from the end of a stem to the end of the next for a beam. On the
  clean copies 245 stems have their flag from such a line alone, and 237 of them are read as typed: most stand on prints
  whose own beams are thin. On the pages whose usual beam is 0.45 staff space thick or more there are 5, and two
  of them are a printed slur over two quarter notes. The rule had three forms. The first took every such line on
  such a page for a slur and lost a note on a trial page: the stem of a beamed note that was followed into a slur
  over its beam shows no beam of its own, and the thin line was all that told of its beam. The second form left a
  line alone where a stem of it shows a beam. Read on all of LitChoir it gained 4 notes and lost none; read on the
  fresh set it gained 4 and lost 4, on 23 pages: a thick beam that no stem shows as its own is found as such a
  line too. The third form asks for the shape of a slur, with the measure that a beam without a witness already
  passes (`symbols.BEAM_STRAIGHT`): the ink that leaves each of the two stem ends is a bow of 1.5 staff spaces or
  more that bends 0.25 or more away from the heads. The printed slur bends 0.65 at both ends. Of the 7
  pages that the second form changed on LitChoir one is left, with the printed slur (memorial-troparia in its
  second scan, 2 notes gained), and no page of the fresh set changes.
- The slit of a half note on a ledger line (`symbols.SLIT_LEDGER`). Two rounds before, a filled head on a line with
  one speck of paper where a half note's slit lies became a half note where the music has room for it. The speck is
  measured from the line through the head, and for a head beside the staff that line was the place of a ledger
  line, counted from the staff. The 1,657 filled heads with a stem at such a place on the clean copies were listed
  with their specks and with the ledger line as the ink shows it: the row that sticks out 0.45 staff space at both
  sides of the head. It lies up to a quarter of a staff space from its counted place. Three half notes that are
  read as quarters hold a speck 0.16 to 0.2 staff space over the line that the ink shows, in the right part of the
  head, where the slit of a half note lies; from the counted place two of the three specks lay too near the line.
  The rule measures the speck from the line that the ink shows. The music then makes
  the note longer where it has room, as for every such speck. Two of the three are mended
  (pascha-christ-is-risen-romanian, pascha-angel-cried in its second scan), and the same note of the same print
  in pascha-angel-cried-believers. The third holds a speck that either measure reads as a slit, and the music
  does not make it longer.
- The count of a page is not moved by a new measure. The speck rule is off on a page of a worn print, where more
  than 0.02 of the asked heads hold a speck that is no slit. In its first form the new measure went into that
  count too. On one worn page of a copy by hand (liturgy-litanies) two specks became slits, the share fell under
  the limit, the speck rule came on for the whole page, and the score lost 8 notes by parts. Three notes of other
  scores were gained the same way, by chance. The page is now counted with each ledger line at its place, as
  before, and the rule changes only the heads on ledger lines: 3 notes gained, none lost.
- What the fresh test set showed. The round was read there in full twice before it was committed. The first
  reading had the first three rules, the slur rule in its second form. The dot rule changed no page there and the
  beam rule one page, with no count. The slur rule changed 23 pages, gained 4 notes and lost 4 (3 in one Romanian
  piece, 1 in an English one): beamed eighths whose thick beam no stem shows as its own, which the thin line alone
  had read. The rule was switched off and narrowed on LitChoir's pages, by the shape of the printed slur there
  and not by a limit from these pages. The second reading had all four rules in their final forms: one page
  changes, by the beam rule (a sixteenth becomes an eighth, and no count moves), no note is gained and none is
  lost, and the rule for the ledger line changes no page. The figures are those of the round before: 39,650 of
  41,761 notes, 4,980 notes that are not there, 90 pieces at 99 %.
- What the round loses on LitChoir: no score has fewer notes than before, counted by parts or staff by staff, and no layout of
  a copy by hand changes. The two losses of the round were found before the final reading: 4 notes of the fresh
  set by the second form of the slur rule, and 8 notes of one worn page by the first form of the rule for the
  ledger line.
- The words. No syllable changes, on LitChoir (5,781 of 6,240 on the clean copies, 24,196 of 28,692 over all scores) and
  on the fresh set.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 116 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 77, where beams have gaps and chords lose their stems;
  nativity-kontakion 47, a print of a music typewriter). Nine clean scores still lack one to three notes, each by causes
  of its own: hollow heads that are read as quarters (trisagion-obleschuk), dots that are not there
  (memorial-troparia), the three notes of a chord (ascension-koinonikon-farrow). Of the causes of this round: a bow on
  a beam where the page's beams are thin themselves (one eighth in the Rachmaninov), and a half note on a ledger
  line whose speck is read and that the music does not make longer (one). And as before: a tie over the end of a
  page whose leaving bow can be followed for less than one staff space from its head, two whole notes a third
  apart in one column, a natural that is read as a flat, a note of two whole notes' length (on the fresh set), a
  tie that ends at a chord of whole notes, and the rests that are no printed quarter rest.
- The round before it: a tie over the end of a page. After the round before it the clean copies lacked 748 notes for
  99 % of each score. The 912 notes that the clean copies still miss were sorted again from the line-up by part:
  about 253 have a wrong pitch, 237 a wrong length, 218 are not read, and 119 are wrong in both. Of 140 notes one
  or two semitones off, 65 stand beside the staff at ledger lines and 75 in the staff, where a sign was not read
  (a flat that touches its head, a sign on a ledger note, a sign that holds for its bar) or a chord of hollow heads
  a third apart was read one place off. No kind has one large cause: 40 notes one place off and 40 notes in the staff a tone
  off were looked at on the page, and no rule came of them. One cause was whole: the reader tied two notes within a page only, and a
  note that is held over the end of a page was two notes. The clean copies went from 21,679 of 22,591 notes to
  21,683 of 22,591 (96.0 %; 4 notes gained, none lost; 25 scores at 99 %, as before;
  58 at 95 %, 73 at 90 %), all scores from 77,232 to 77,236 of 89,732
  (86.1 %; the same 4; 79 scores at 99 %, as before), and the fresh test set from 39,647 to
  39,650 of 41,761 (94.9 %; 3 gained, none lost; 90 pieces at 99 %, as before).
  The reader writes 5 fewer notes that are not there on LitChoir, all on the clean copies (895 there, 5,648 on
  all scores), and 3 fewer on the fresh test set (4,980): the second note of each tie. The clean copies lack 744
  notes for 99 % of each score now, and 13 scores lack one to three. The kit does not change (6206 notes).

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A tie over the end of a page: a bow leaves the last note of a staff, and a bow comes to the first note of that staff on the next page (`ties.TIE_PAGE`) | 4, 0 | 4, 0 | 3, 0 |

  Counted staff by staff the round gains 2 notes and loses none on the clean copies, the same 2 on all scores, and
  3 and loses none on the fresh set. 9 pages of LitChoir change and 8 of the fresh set. The count staff by staff leaves one score out:
  in non-liturgical-jesus-prayer the scorer lines up each of the four voices as a staff of its own once the ties
  are joined (two staves of two parts before), so its count staff by staff is of another line-up (190 of 208 notes
  before, 252 of 271 after). By parts the score gains 2 notes (252 of 271), and the Rachmaninov "Rejoice, O
  Virgin" gains the other 2 (424 of 506).
- A tie over the end of a page (`ties.TIE_PAGE`). On the last system of a page the last note of its voice on a
  staff is the leaving half of such a tie when one bow leaves it and runs to the end of the staff: 3 staff spaces
  long or more, with ink in 0.45 of its columns, ending at most 1.8 spaces before the end, and smooth as the bow of
  a tie within a page is. The note gets the start of a tie, and the reader hands the staff and the place of the note
  on to the next page of the hymn (`ties_out` of a page, `ties_before` of the next). There the first note of that
  staff at that place is the coming half when a bow of 0.9 spaces or more comes to it, looked for over the 3 spaces
  before the note, behind the time signature. The joined hymn keeps the tie where both pages mark it and takes a
  half without its other half away, and the command line reader hands the ties from page to page as it hands the
  key and the clefs.
- Why the page before tells the next one. The first form marked each half on its own page. It was read on every
  page of LitChoir, and all its 74 halves were looked at on the page. Of the 62 coming halves 7 are true. The
  other 55 are ink before a first note: a stroke of the clef, a flat of the key signature, a number of the time
  signature, the bar of a ledger line, and time signatures that are read as notes. Three measures of the bow were
  counted on them (thick ink beside the bow, free paper at its far end, the curve of a bow), and none separates
  the 7 from the 55: a short bow behind a clef is a short stroke behind a clef. What separates them is the page
  before. All 55 stand on pages whose page before leaves no tie at that staff and place, so the coming half is
  looked for only where the page before left one, and a page that is read alone marks no coming half at all.
  In the final reading LitChoir has 5 coming halves, all true, each beside its leaving half: three notes
  in non-liturgical-jesus-prayer and two in the Rachmaninov. Two true coming halves of the first form are not
  read now: the bow that leaves their note on the page before can be followed for less than one staff space.
- The leaving half must be one bow. Of the 12 leaving halves of the first form 5 are true. Two of the 7 others
  are no bow (a staff line that was followed from a whole note, and the bracket of a second ending drawn by hand)
  and are gone with the test that the ties within a page pass. The other 5 stay in the final reading: two slurs
  that run on to the end of the last staff, a bow that passes over a whole note to the end of its staff, and two
  strokes by hand (a crossing-out, and a bow of a copy by hand). Each stands alone and moves no count. The
  joined hymn takes it away; a page that is read alone keeps it.
- The wide test joins such a tie as the kit's scorer does. The kit's scorer reads a score in one piece and joins
  two tied notes into one. The wide test reads page by page, and a note that was tied over the end of a page
  counted as two notes there: one too short, and one that is not in the typed hymn. Its scorer now joins the last
  note of a part with an open tie and the first note of that part on the next page that a tie comes to, at one
  pitch, where the tied note ends at most two quarter notes before the last note of its part on the page (another
  voice may go on). The change alone moves no figure of the reading before the round, on LitChoir or on the fresh
  set: no page marked such a half. The first form of the scorer's change measured the end of the tied note against
  the longest staff of its page, and the staves of a reading end at different times; the fresh set showed it, and
  it was mended in the scorer, not in the reader.
- What the fresh test set showed. The round was read there in full in both forms before it was committed. The first
  form changed no count: it marked 5 leaving halves and 56 coming halves on 40 pages, and no tie was joined,
  by the fault of the scorer that is told above. In the second form 8 pages change, four pairs of pages in four
  pieces: 5 leaving halves, and a coming half for each of them on the next page. Three of the ties are joined
  and bring 3 notes, one each in three Romanian pieces (230 of 246, 611 of 703 and 734 of 748). In the fourth
  piece the two pages read the tied note a semitone apart (their keys differ in the reading), so its halves
  are not joined and move no count. No note is lost, and no limit was set on these pages. The reader writes 3 notes fewer that are not there (4,980). Counted staff by staff the
  round gains 3 notes and loses none. No more piece is at 99 % (90).
- What the round loses on LitChoir: no score has fewer notes than before, counted by parts or staff by staff, and no layout of
  a copy by hand changes. The first form lost no note either: its 55 false coming halves stood alone, and no
  count showed them. They were found by looking at every page that the rule changed.
- The words. No syllable changes, on LitChoir (5,781 of 6,240 on the clean copies, 24,196 of 28,692 over all scores) and
  on the fresh set.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 116 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 77, where beams have gaps and chords lose their stems;
  nativity-kontakion 47, a print of a music typewriter), a tie over the end of a page whose leaving bow can
  be followed for less than one staff space from its head (two on the clean copies), two whole notes a third
  apart in one column, a natural that is read as a flat, a note of two whole notes' length (an oval between two
  upright strokes, on the fresh set), a tie that ends at a chord of whole notes, a half note that is read as a
  quarter with a second note, and the rests that are no printed quarter rest.
  The figures of this round are of its time.
- Two rounds before: a half note and a whole note on a line whose hole the print has all but filled, and a bow that
  ends in a staff line. After the round before it the clean copies lacked 760 notes for 99 % of each score. The
  mistakes that are left were sorted by kind from the line-up by part: a note one place off (78), a note a semitone
  off (71), a half note and a quarter taken for each other (55), a quarter and an eighth (50). The two largest
  kinds were counted and gave no rule, as told below. The third gave two rules, and the ties that were left gave
  two more. The clean copies went from 21,667 of 22,591 notes to 21,679 of 22,591
  (96.0 %; 12 notes gained, none lost; 25 scores at 99 %, as before; 58 at 95 %, 73
  at 90 %), all scores from 77,173 to 77,232 of 89,732 (86.1 %; 59 gained, none lost; 79 scores
  at 99 %, as before), and the fresh test set from 39,644 to 39,647 of 41,761 (94.9 %;
  3 gained, none lost; 90 pieces at 99 %, as before). The reader writes 12 fewer notes that are not there on the clean copies (900), 7 fewer on all
  scores (5,653), and 1 fewer on the fresh test set (4,983). The clean copies lack 748 notes for 99 % of each
  score now, and 13 scores lack one to three.

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A filled head on a line with one speck where a half note's slit lies, where the music has room for a half note (`symbols.SLIT_ONE`, `symbols.SLIT_PAGE`, `music.SLIT_SPAN`) | 10, 0 | 17, 0 | 0, 0 |
  | An oval without a stem on a line with one speck in its middle is a whole note (`symbols.WHOLE_SLIT`) | 1, 0 | 40, 0 | 0, 0 |
  | A bow ends in a staff line before its head (`ties.TIE_TO_LINE`) | 1, 0 | 2, 0 | 3, 0 |
  | A tie to a head that two voices share (`ties.TIE_SHARED`) | 0, 0 | 0, 0 | 0, 0 |

  Counted staff by staff the round gains 12 notes and loses none on the clean copies, 51 and loses none on all scores, and
  3 and loses none on the fresh set. 42 pages of LitChoir change and 3 of the fresh set.
- The notes a semitone off, counted and left without a rule: 71 notes in 31 clean scores. Each cause holds a few
  notes: a tie that runs through a heavy sharp, a sharp that is read as a head, a sharp on ledger lines, a natural,
  a sign that is forgotten later in its bar. A wider limit for how level a sign stands with its head mends 1 note.
- The notes one place off at ledger lines, counted and left without a rule. For 4,921 heads beside the staff on
  the clean copies the reader wrote down how far the head lies past its ledger line and where its height puts it.
  Neither measure separates the wrong heads from the right ones within one print. On three scores
  (cherubic-lvovsky, nativity-kontakion, nativity-troparion) the same drawing is typed as two pitches: the typed
  hymn differs from the page there, or the line-up of the two is shifted.
- A half note on a line with one speck (`symbols.SLIT_ONE`, `music.SLIT_SPAN`). The hole of a half note on a staff
  line is two slits, one over the line at the right and one under it at the left. A print can fill both but for
  specks, and an older rule reads the head as hollow where two specks are left. Where one is left the head was
  read as a quarter. Counted on 30,345 marks of the clean copies: a filled head on a line with one speck where a
  slit lies is typed as a half note 14 times and as a quarter 10 times, so the speck alone says nothing. The
  music does: where the voice goes on two steps or more after the note, every step between has a vote for its
  length, and the votes add up to twice the note's length, the count is 10 and 0. The rule sets the head apart
  in the symbols, and the music makes it a half note (or a dotted one) only where the bar has that room.
- A page of a worn print (`symbols.SLIT_PAGE`). The first reading of that rule on every page of LitChoir gained
  37 notes and lost 9, the 9 on five scores (cherubic-lvovsky lost 3) with a worn print: there a filled head
  holds specks of paper anywhere, and one of them lies where a slit would. One of the lost notes also showed that
  the tally before the reading was wrong: two steps with one vote each add up to the length as well. So the
  specks of a page are counted. Of the page's filled notes with a stem, the share that holds a speck near the
  middle that is no slit is 0 to 0.011 on the pages of the clean copies where the rule gained, and 0.044 to 0.21
  on the pages where it lost; over 0.02 the rule is off for the page. That takes back every lost note. It also
  takes back 20 notes that the first form gained outside the clean copies, on pages whose shares are 0.020 to
  0.17: they lie among the pages that lose, and no limit separates them. The count is of the notes of the page.
  Its first form counted every mark, the flats of a key signature too, which have a stroke and a hole, and one
  true note of a clean copy went back by it. The 10 new half notes outside the clean copies were looked at on the
  page, and all are half notes. In the final reading the rule gains 10 notes on the clean copies and loses none (2 each in the third scan of nativity-troparion, in
  the second score of pascha-angel-cried and in pascha-christ-is-risen-romanian, which has 111 of its 113 notes
  now), and 17 on all scores; it writes 7
  fewer notes that are not there on the clean copies.
- A whole note on a line with one speck (`symbols.WHOLE_SLIT`). The same print fills a whole note on a line, and an
  oval without a stem that is not hollow was no note at all. The rule reads a lying oval without a stem, 1.2 to 1.5
  times as wide as the page's heads, with its middle on a staff line and one speck in the middle of its width over
  or under the line. The first form was read on every page of LitChoir, and each of its 54 new whole notes was
  looked at on the page: 45 are whole notes and 9 are not (three sharps, four numbers of a time signature, a
  scribble and a smudge). Two measures set them apart. The middle three fifths of a whole note's box are ink in 0.85
  to 0.94 of their cells, and those of the sharps, the numbers and the scribble in 0.79 at most; and a whole note is
  at most 1.16 times as high as the page's heads, the smudge 1.52. The rule asks for 0.83 and 1.3 now. The 9 are
  gone, and so are three true whole notes on ledger lines, whose boxes hold the paper beside the ledger line (0.73
  to 0.80). In the final reading the rule gains 1 note on the clean
  copies and loses none (the second score of pascha-angel-cried, 536 of 565), and 40 on all scores, 18 of them
  in st-basil-in-thee-rejoiceth, a thick print that fills its whole notes on a line (212 to 230 of 503). It
  writes 11 more notes that are not there in seven scores outside the clean copies that it gains notes in, and
  3 fewer on the clean copies.
- A bow that ends in a staff line (`ties.TIE_TO_LINE`). A bow is followed from its first head, and it had to come
  within 0.9 staff spaces of the second. Where the last part of a bow lies in a staff line the thin ink ends
  earlier. Such a way counts now when a staff line goes on from its end to the head and the ink ends at most 1.5
  staff spaces before the head. On LitChoir the first form read four new ties, and all four are on the page (2 notes
  by parts; the other two do not move the count). On the fresh set it gained 3 notes and lost 12: a short stroke
  beside a head that runs into a staff line was read as a bow. So the rule was switched off and narrowed on
  LitChoir's pages, as the rules of this work say. On the four true ties the way that was followed is 3.6 to 15
  times as long as the part that the line hides, and the rule asks for 3.5 times. The four ties stay. In the final
  reading the rule gains 1 note on the clean copies and loses none (communion-lords-prayer, 356 of 392), 2 on all scores, and 3
  on the fresh set.
- A tie to a head that two voices share (`ties.TIE_SHARED`). A chord is tied note by note: the other head in
  the column of a tie's second head is no note between the two heads when it is of the same voice. In
  extra-come-bless the second head has a stem up and a stem down, two voices share it, the head beside it is of
  one of them, and the tie was not read. Such a column counts as a chord now. It is one tie on one page: no
  other page of LitChoir and no page of the fresh set changes. Its count by parts does not
  move; one note fewer is written that is not there.
- Seen and left without a rule: two whole notes a third apart in one column, where the lower one gets the rim of
  the upper as its stem or the pair is not read at all (communion-lords-prayer, wedding-psalm-128,
  extra-beatitudes); the cell between the end of a bow, a bar line and two staff lines that is read as a whole
  note; and a whole note under the staff whose ledger line lies inside its box.
- Where the typed hymn differs from the page. In wedding-service the responses stand in another order in the
  typed hymn than on the page, and 18 notes count as mistakes that no reading can mend. In the three scans of
  nativity-troparion a note is typed a semitone from the place that the page draws. Of 30 mistakes of the clean
  copies that were drawn by lot and looked at on the page, about 6 are such differences or a shifted line-up, 6
  are worn print, 5 are marks by hand, smudges or the shadow of a paper clip, 3 are heads at ledger lines that
  the print itself draws two ways, and the rest are single causes of the reading.
- What the fresh test set showed. The round was read there in full before it was committed, in its first form
  and in the second, and its changed pages again in the final one. The first form lost notes there: the bow that
  ends in a staff line gained 3 notes and lost 12, in four pieces (5, 4, 2 and 1), where a short stroke beside a
  head runs into a staff line. No limit was set on these pages. The rule was narrowed on the four true ties of
  LitChoir, as told above, and read again: it gains the same 3 notes (2 in one Romanian piece, 733 of 748, and 1
  in a carol) and loses none. The two rules for a speck and the rule for a shared head change no note there in
  either form. The reader writes 1 note fewer that is not there (4,983). Counted staff by staff the round gains 3
  notes and loses none. Three pages change. No more piece is at 99 % (90).
- What the round loses on LitChoir: no score has fewer notes than before, counted by parts or staff by staff, and no layout of
  a copy by hand changes. The first forms lost 10 notes on LitChoir (9 by the half note with one speck on worn
  prints, 1 by two sharps that were read as whole notes) and 12 on the fresh set, and each rule that lost was
  narrowed by them, as told above.
- The words. No syllable changes, on LitChoir (5,781 of 6,240 on the clean copies, 24,196 of 28,692 over all scores) and
  on the fresh set.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 116 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 79, where beams have gaps and chords lose their stems;
  nativity-kontakion 47, a print of a music typewriter), two whole notes a third apart in one column, a
  natural that is read as a flat, a note of two whole notes' length (an oval between two upright strokes, on the
  fresh set), a tie over the end of a page, a tie that ends at a chord of whole notes, a half note that is read
  as a quarter with a second note, and the rests that are no printed quarter rest.
  The figures of this round are of its time.
- Three rounds before: a tie that lies in a staff line, and the end of a bold slur that is no second stem. After the
  round before it the clean copies lacked 769 notes for 99 % of each score. The mistakes that are left were
  sorted by kind from the line-up by part, and no kind is large. So the 13 clean scores that lack one to three
  notes were read mistake by mistake, on the page. Two causes repeat there: a tie that is not read, and the end
  of a bold slur at a head that is read as a second stem. Four rules stand. The clean copies went from 21,656
  of 22,591 notes to 21,667 of 22,591 (95.9 %; 11 notes gained, none lost; 25 scores at 99 %,
  one more: trisagion-vitoshinsky has 372 of its 373 notes; 57 at 95 %, 73 at 90 %), all scores from 77,151 to 77,173 of
  89,727 (86.0 %; 22 gained, none lost; 79 scores at 99 %, one more), and the fresh test set
  from 39,633 to 39,644 of 41,761 (94.9 %; 11 gained, none lost; 90 pieces at 99 %,
  as before). The reader writes 13 fewer notes that are not there on the clean copies (912), 18 fewer on all
  scores (5,660), and 9 fewer on the fresh test set (4,984): a tie that is not read leaves its second note as a
  note of its own, and a slur's end that is read as a stem makes a second note of its head. The clean copies lack
  760 notes for 99 % of each score now, and 12 scores lack one to three.

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A long bow that lies in a staff line for a part of its way (`ties.TIE_DIP`) | 2, 0 | 3, 0 | 8, 0 |
  | The bow over the end of a line begins inside a staff line (`ties.TIE_BREAK_LINE`) | 3, 0 | 3, 0 | 3, 0 |
  | The end of a bold slur at a head is no second stem (`symbols.SLUR_STEM`) | 5, 0 | 12, 0 | 0, 0 |
  | A head keeps the stroke that runs on through its edge into a slur (`symbols.LOST_THROUGH`) | 2, 0 | 5, 0 | 0, 0 |

  Counted staff by staff the round gains 10 notes and loses 1 on the clean copies, 22 and loses 1 on all scores, and
  5 and loses none on the fresh set. The one note is of triodion-meatfare, on the page where the long
  bow in a staff line reads a tie of the upper heads of two chords: the bow is on the page, the count by parts
  does not move, and the count staff by staff lines the notes of these chords up otherwise. Forty-nine pages of
  LitChoir change, and eleven pages of the fresh set. Every note that the first forms lost was looked at on the
  page, and so were the new ties and the taken strokes on the pages outside the scores that the rules were
  written for.
- The ties that are not read. 35 ties of the clean copies were not read, and each was looked at on the page. The
  largest cause is a bow that lies inside a staff line: the reader follows the thin ink of a bow and counts the
  columns where a staff line can hide it, and it asked that the ink shows in 0.6 of the columns. A flat bow
  between two heads in a space touches the line over a long part, and less than that shows.
- A long bow in a staff line (`ties.TIE_DIP`). Counted on every pair of heads of the clean copies between which
  a way of thin ink shows in 0.3 to 0.6 of its columns (7,600 pairs were measured for it): a curve is laid through
  the ink that shows, and over the longest part without ink its distance to the staff line is taken. For the true
  ties the curve lies 0.01 to 0.08 staff spaces from the line there, the bow is in the line; for the ways that are
  no tie (other ink at two heads, on two pages) it lies 0.33 to 0.53 away. The first form, with that test alone,
  was read on every page of LitChoir: it read 14 new ties, 7 of them true and 7 false, all 7 on scans outside the
  clean copies, most of them copies by hand. There the way between two near heads runs along a staff line through a number of the time signature, a flat or
  the stroke of a stem, and a flat curve through such ink stays at the line as well. Two things of the true bows
  were missing on every false one: the true bows are 3.1 staff spaces long or more (the false ones 1.0 to 2.5,
  and one of 10 that runs along a line from a head through a flat and a bar line), and their ink shows at both
  sides of the hidden part, because a bow goes into the line and comes out of it. The rule asks for both now
  (2.8 staff spaces; 0.15 staff spaces of ink at each side). The 7 true ties stay and the 7 false ones are gone.
  In the final reading the rule gains 2 notes on the clean copies and loses none (cherubic-znamenny, 494 of 508), 3 on all
  scores, and 8 on the fresh set.
- The bow over the end of a line that begins in a staff line (`ties.TIE_BREAK_LINE`). In communion-lords-prayer
  four ties go over the end of a line, and each bow leaves its head inside a staff line. The long bow at the end
  of a line was followed only from thin ink beside the head; it is followed from the staff lines beside the head
  too, after the usual start, so that a bow that is read stays as it is (mixed in with the usual starts, the
  longest way won and one read tie was lost). All four ties are read. On LitChoir one more page has such a tie
  read, on a thick copy, and one read a false one: a photograph on which a pen lies across the end of a staff, and the way ran on
  into the pen. A bow that a line hid ends where the staff ends, so a way that goes on more than half a staff
  space past the lines is none. In the final reading the rule gains 3 notes on the clean copies and
  loses none (communion-lords-prayer, 355 of 392), no other on LitChoir, and 3 on the fresh set.
- The end of a bold slur (`symbols.SLUR_STEM`). Some prints draw a slur with a bold, steep end that meets the
  head, and the reader followed that end as a stem: the head had a stem up and a stem down, and it was read as
  the notes of two voices. Counted on the 947 heads of the clean copies with two stems: how far a stem leans
  sideways does not separate alone (true stems lean up to 0.42 staff spaces on a slanted scan). The slur's end is
  short (at most 1.7 staff spaces past the head), it leans 0.28 staff spaces or more away from the head, and the
  head's other stem is long (2.5 staff spaces or more) and leans less by 0.2: 8 heads of the clean copies, all
  true ends of a slur, in trisagion-vitoshinsky and in the second score of o-pure-virgin. The first form was read
  on every page of LitChoir: it took 31 strokes on 16 pages, and on three scans outside the clean copies it lost
  3 notes. A hand draws the stem
  of a second voice with a bend where it leaves the head, the reader follows it only to the bend, and it measures
  short and leaning like a slur's end. Past the bend that stroke goes on upright, and the end of a slur has turned
  to the side there. So the rule looks at the next staff space past the followed end: ink within half a staff
  space of the end's column in 0.6 of the rows is a stem, and it stays (on the pages of the first form the ends
  of printed slurs have ink in under half of these rows, the bent stems of the hand in all of them). And the mark is a
  whole head, 0.7 staff spaces high: on one of these pages the stem at the upper half of a head in a beam was
  taken. In the
  final reading the rule gains 5 notes on the clean copies and loses none (trisagion-vitoshinsky, which has 372
  of its 373 notes now), and 12 on all scores (3 each in two scores outside the clean copies whose slurs are bold, 1 in a third).
- A stem that runs on into a slur (`symbols.LOST_THROUGH`). The rule before this one showed a second fault at
  the same slurs. A head that has no stem gets the thin stroke beside it as its stem, where the stroke ends at
  the head. Where a bold slur begins at the head, the stroke of the stem and the slur are one piece of thin ink
  that runs on past the head's middle, and the head stayed without a stem. With the slur's end no longer a stem,
  the eighth beside it in the same beam was read as a quarter: its beam had no second stem as a witness. A mark
  with no stem takes a stroke now that runs on up to 0.6 staff spaces past it. It changes 33 pages of LitChoir, most
  of them copies by hand, where the stem of a note is drawn through its head; the changed notes that were looked
  at on the page (four pages) are true notes of the page. In the final reading the rule gains 2 notes on the clean copies and loses none (the second
  score of o-pure-virgin, 282 of 298), and 5 on all scores.
- The ties that are left without a rule, each looked at on the page: a tie over the end of a page (two pairs of
  pages; the reader ties within a page only), a bow that stops at a head of a chord of whole notes (three), a bow
  far under its notes, ties of a triplet that lie over the stems, and two places where the typed hymn has a tie
  and the page has none.
- Other causes on the scores that lack one to three notes, without a rule: a half note that is read as a quarter
  with a note after it that is not there (five notes in two scores), a thick beam that is read as two beams (two
  notes), the end of a slur at the top of a stem that is read as a flag (two), a dot of the lower voice that the
  upper voice takes, and a group of hollow heads on ledger lines.
- What the fresh test set showed. The round was read there in full before it was committed, in its first form
  and in the final one. No rule loses a note there. The round gains 11 notes, all in Romanian pieces, and all are
  ties: the long bow that lies in a staff line gains 8 in one piece (183 to 191 of 255 notes; 9 in the first form,
  before the rule asked for ink at both sides of the hidden part), and the bow over the end of a line that begins
  inside a staff line gains 1 in each of three pieces, of which one has 508 of its 509 notes now. The rule for the
  end of a bold slur and the rule for the stem that runs on change no note there. The reader writes 9 fewer notes
  that are not there (4,984): the second note of a tie that was not read. Counted staff by staff the round gains 5
  notes and loses none. Eleven pages change. No more piece is at 99 % (90).
- What the round loses on LitChoir: no score has fewer notes than before, counted by parts. The first forms lost 7 notes on
  six scans outside the clean copies, and each of the three rules that lost was narrowed by them, as told above. Two notes that
  the first form of the slur rule gained went with the narrowing (one in liturgy-what-shall-i-render, a clean
  copy, one on a copy by hand): there the stroke that it took is the true stem of a second voice, which goes on
  upright, and the count had moved for another reason than the rule's.
- The words. No syllable changes, on LitChoir (5,781 of 6,240 on the clean copies, 24,196 of 28,692 over all scores) and
  on the fresh set.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 116 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 79, where beams have gaps and chords lose their stems;
  nativity-kontakion 47, a print of a music typewriter), a natural that is read as a flat, a note of two
  whole notes' length (an oval between two upright strokes, on the fresh set), a tie over the end of a page, a
  tie that ends at a chord of whole notes, a half note that is read as a quarter with a second note, and the
  rests that are no printed quarter rest.
  The figures of this round are of its time.
- Four rounds before: a whole note beside a half note a second away, a head on top of a ledger line that stands near
  the staff, and a flag that is no flat. After the round before it the clean copies lacked 787 notes for 99 % of
  each score. The mistakes that are left were sorted by kind from the line-up by part, and each kind was counted
  against a census before a rule was written. Eight ideas were counted and dropped. Four rules stand, each for a
  thing that one or two prints do. The clean copies went from 21,638 of 22,591 notes to
  21,656 of 22,591 (95.9 %; 18 notes gained, none lost; 24 scores at 99 %, as before; 57 at 95 %, 72 at
  90 %), all scores from 77,123 to 77,151 of 89,726 (86.0 %; 31 gained, 3 lost; 78 scores at
  99 %, as before), and the fresh test set from 39,630 to 39,633 of 41,761 (94.9 %; 3 gained, none lost;
  90 pieces at 99 %, as before). The reader writes 3 fewer notes that are not there on the clean copies (925), 6 fewer on all
  scores (5,678), and 2 more on the fresh test set (4,993). The clean copies lack 769 notes for 99 % of each score now.

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A whole note a second from a note with a stem, in the order that no chord has (`symbols.WHOLE_SECOND`) | 4, 0 | 8, 1 | 0, 0 |
  | Paper between a near ledger line and the staff: the head sits on top of the line (`symbols.LEDGER_PAPER`) | 6, 0 | 12, 1 | 0, 0 |
  | The same where the line is short and is not found as a line (`symbols.LEDGER_SHORT`) | 4, 0 | 7, 1 | 0, 0 |
  | The flag of an eighth is no flat for the next note (`signs.FLAT_FLAG`) | 4, 0 | 4, 0 | 3, 0 |

  Counted staff by staff the round gains 17 notes and loses none on the clean copies, 29 and loses 2 on all scores, and
  3 and loses none on the fresh set. Thirty-six pages of LitChoir change, 14 of them of clean copies,
  and four pages of the fresh set. The changed pages outside the scores that the rules were written for were looked at one by
  one: where no count moves, the mark that changed is no note at all (a letter, a blot, a rest drawn by hand, each
  read as a note either way), or the new reading is what the page shows.
- A whole note a second from a half note. Where two voices of a staff sing a second apart and one of them holds
  a whole note, the print sets the oval close beside the head of the other voice, and the reader gave the oval
  the stem of its neighbour: a half note. In a chord at one stem the lower head of a second stands left of the
  stem and the upper head right of it. An oval that stands the other way round (left of a stem that goes down
  and higher than that stem's own head, or right of a stem that goes up and lower) is no head of that chord: it
  is the whole note of the other voice (`symbols.WHOLE_SECOND`). Counted before on every pair of heads a second
  apart at one stem of the clean copies: 3 pairs stand in that order, all 3 typed as a whole note and read as a
  half note, and no right note stands so. In the reading the rule gains 4 notes on the clean
  copies and loses none (3 in the second score of pascha-angel-cried, 1 in jesus-prayer), and 8 on all scores, where it
  loses 1 on a copy by hand.
- A head on top of a near ledger line. One print (liturgy-mercy-of-peace in both scores, liturgy-holy-holy,
  liturgy-we-praise-thee) sets the first ledger line over the bass staff about half a staff space from the
  staff, where a whole one is usual; nativity-troparion has such a line too. A head past that line has little
  room: it is a half moon on top of the line, its middle lies less than a quarter of a staff space past the
  line, and the reader took it for a head on the line, one place low. The paper tells them apart: a head on the line has its
  near half between the line and the staff, and a head past the line leaves paper there. Counted on every head
  of the clean copies that is read on a first ledger line up to 0.75 staff spaces from the staff, by the share
  of ink in a thin band at the line's near edge under the head: 7 heads have 0.29 or less, and all 7 are typed
  one place higher; 26 have 0.77 or more, 23 of them right as they are read and 3 wrong in another way. No head
  lies between. On a line farther from the staff the count does not separate (5 right heads have little ink
  there), so the rule holds for a near line only (`symbols.LEDGER_PAPER`).
  The first form was read on every page of LitChoir, as every rule from a census of the clean copies is. The
  clean copies gained 6 notes and lost none; the other scans, thick copies and copies by hand, gained 6 and
  lost 11. On their pages a stem alone stands on the line, where the head is one blot with the line, or the line that was
  found is the upper rim of a wide hollow oval that hangs under the staff with no ledger line at all. So the rule
  asks for the shape of the print: the line is the first one, 0.3 staff spaces past it the mark is as wide as a
  head (0.7 to 1.3 of the page's head width), and the line is 0.3 staff spaces longer than the mark is there.
  A try before that, a line that sticks out past the head at both sides, lost two of the print's own heads,
  which stand at one end of their line. And a whole note on its line that the copy glued to the words under it
  was read as a head past the line: the hole of a hollow head counts as ink at the line's near edge now, and a
  mark that is wider than 1.3 heads is no single head. In the final reading the rule gains 6 notes on the clean copies and loses
  none (2 in each score of liturgy-mercy-of-peace, 1 in liturgy-holy-holy, 1 in nativity-troparion), and 12 on all
  scores, where it loses 1: on one page of liturgy-gospel-alleluia the head stands on top of its line as the rule
  reads it, and the typed hymn has the note one place lower.
- The same head where its line is short. On five heads of that print no ledger line is found: the line is
  shorter than a ledger line is asked to be, and the mark, head and line in one, measures as a head on the first
  ledger place. The rows of such a mark where the ink runs on through its middle for longer than a head is wide
  are the line's, and where nothing of the mark lies between them and the staff, the head sits on the line
  (`symbols.LEDGER_SHORT`). The first form took rows of 1.4 staff spaces. On all of LitChoir it gained 11 notes
  and lost 10: a hand draws a note under the staff as a wide oval with no ledger line, and every row of that
  oval is as long as a line. The rule now asks for a level foot: rows 0.3 staff spaces longer than a head of
  the page, at most 0.65 staff spaces thick together, that stick out at both sides past the mark over them. In
  the final reading the rule gains 4 notes on the clean copies and loses none (2 in the second score of
  liturgy-mercy-of-peace, 1 in liturgy-holy-holy, 1 in liturgy-we-praise-thee), and 7 on all scores, where it loses 1
  on a thick copy: a head on its line that is worn to a cross.
- A flag that is no flat. 10 notes of the clean copies are read with a flat that is not there. 4 of them follow
  an eighth with a flag: the stroke of the flag and its hook were read as the stroke and the bowl of a flat
  before the next head. A flat whose stroke begins inside the reach of a stem's flag, between the end of that
  stem and its head, is the flag itself (`signs.FLAT_FLAG`). 4 more of the 10 are naturals that are read as
  flats, each of another shape; they are left. The first form asked for any mark at the right of the stem. On
  the fresh set it gained 3 notes and lost 3: in one piece a true flat stands close behind a stem that carries a
  beam, under the beam. A stem in a beam has no flag, so the rule holds for a stem with a flag and no beam; that
  is a reason of the notation and no limit, and LitChoir reads the same with it. In the reading the rule gains
  4 notes on LitChoir, all on clean copies, and loses none (3 in the two scores of liturgy-mercy-of-peace, 1 in
  pascha-receive-short, which has 150 of its 153 notes now), and 3 on the fresh set.
- Counted against a census and dropped, no rule. The bow of a printed slur between two stem ends, against a
  thin beam: 236 eighths of the clean copies are read from a thin beam and 13 of them are wrong, but the bow of
  the ink between the stems is the same for both (9 of the wrong ones bow less than 0.05 staff spaces, and right
  ones bow up to 0.74). A smaller mark as a dot, for the voices of a step to ask about: in a column where every
  voice has the dot every voice misses it, and no voice asks. A short bar that asks for a dot: the pages with
  these dots have no bar length that holds (one has 24 bars and no full one). The rest of a hole in a filled
  head, page by page: on two pages every such head is a half note, on others they are quarters, and the voices
  mend most of them already. A head of a chord whose place lies between two places, set a third from its
  neighbour: 2 mended, 1 broken. A stem that does not reach the head beside it, for a pair that is no chord: the
  stroke of the print runs through both heads. The ledger heads of the tenor in nativity-troparion that are read one
  place off: the letters of a music typewriter, each of its own shape. And 321 heads of the clean copies lie between two places by 0.3 or more, 59 of
  them with a wrong pitch; the rule that weighs the mark for such a head stays off, as it was measured before.
- What the fresh test set showed. The round was read there in full before it was committed, and one rule was
  narrowed by it (the flag, above). The round gains 3 notes and loses none, by parts and staff by staff: the flag
  that is no flat, in one Church Slavonic piece (235 to 238 of 257 notes). The two rules for a head on top of a
  near ledger line change no note there. The whole note a second from a stem changes two notes, and neither is
  right before or after: both are notes of two whole notes' length, an oval between two upright strokes, which
  were read as half notes and are read as whole notes now. The scorer counts 2 more notes that are not there
  with them (4,993). Four pages change. No more piece is at 99 % (90).
- What the round loses on LitChoir: three scores have one note fewer than before, and each is named above:
  megalynarion-bortniansky in its second score (a copy by hand, the whole note a second from a stem),
  liturgy-gospel-alleluia (the page shows the head on top of its line, as the rule reads it), and
  ascension-antiphon-moderato (a thick copy, a head on its line that is worn to a cross). No score changes its layout.
- The words. No syllable changes, on LitChoir (5,781 of 6,240 on the clean copies, 24,196 of 28,692 over all scores) and
  on the fresh set.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 116 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 79, where beams have gaps and chords lose their stems;
  nativity-kontakion 47, a print of a music typewriter), a natural that is read as a flat, a note of two
  whole notes' length (an oval between two upright strokes, on the fresh set), a rule of its own for the bold
  tie, a tie of whole notes over a bar line, the end of a slur under two notes that is read as a second stem,
  and the rests that are no printed quarter rest.
  The figures of this round are of its time.
- Five rounds before: sixteenths under two beams that a staff line joins, a second dot, and a bow from syllable to
  syllable. After the round before it the clean copies lacked 830 notes for 99 % of each score. The clean scores
  were ranked by the notes that each still needs, and the scores after the first two were read by part, mistake
  by mistake. Three causes came of it, each a thing that the print does and the reader did not know, and each on
  one to four scores. The clean copies went from 21,593 of 22,589 notes to
  21,638 of 22,591 (95.8 %; 45 notes gained, none lost; 24 scores at 99 %, one more; 56 at 95 %, 72 at
  90 %), all scores from 77,078 to 77,123 of 89,726 (86.0 %; 45 gained, none lost; 78 scores at
  99 %, one more), and the fresh test set from 39,618 to 39,630 of 41,761 (94.9 %; 12 gained, none lost;
  90 pieces at 99 %, as before). The count of the notes that are not there rises by 6 on LitChoir, all in one score (928 on the clean
  copies, 5,684 on all scores; see the bow below), and falls by one on the fresh test set (4,991).

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | Two printed beams that a staff line joins are two beams (`symbols.BEAM_TWO`) | 12, 0 | 12, 0 | 8, 0 |
  | A second dot at the right of the first (`symbols.DOT_TWO`) | 11, 0 | 11, 0 | 4, 0 |
  | On a page whose bows go from syllable to syllable, such a bow is no tie (`ties.TIE_WORD`) | 22, 0 | 22, 0 | 0, 0 |

  Counted staff by staff the round gains 44 notes and loses none on the clean copies, 44 and loses none on all scores, and
  11 and loses none on the fresh set. Seven pages of LitChoir change their notes, all of clean copies.
  On six more only the written music changes: a note that is held for seven quarters is written as a whole
  note with two dots now. On one more a sixteenth that the voices of its step had mended is read from its two beams.
- Two beams that a staff line joins. The two beams of a sixteenth lie a little apart, and where they lie level
  a staff line can run in the gap between them: the two beams and the line are then one block of ink, and the
  reader counted one beam. Four clean scores of one engraver have such blocks (cherubic-georgian, both scores,
  wedding-georgian and communion-give-thanks). The block shows at the stem where the sixteenths meet an eighth:
  the beam's piece at one side of the stem is a full flat block, 1.0 to 1.55 staff spaces thick, and its piece
  at the other side is one beam, 0.45 to 0.85 thick. There the thick piece is two beams (`symbols.BEAM_TWO`),
  and the stem at its other end, which shows the same ink, has two beams too. Counted from the stored measures
  of every stem before a page was read: 9 typed sixteenths to gain on the clean copies. A first form of the
  count took 22 true eighths of the copies by hand with it, where a hand drew its beam fat and slanted; so a
  block fills 80 % of its box, and the thick one leans at most 0.04. In the reading the rule gains 12 notes and loses none: 7 in the
  second score of cherubic-georgian, 2 in the first (which lacks one note for 99 % now), 2 in wedding-georgian and 1 in
  communion-give-thanks.
- The second dot. wedding-georgian prints half notes with two dots, before an eighth, seven of them on two
  pages; the reader knew one dot. A second dot is now read (`symbols.DOT_TWO`), the note is one and three
  quarters as long as its head says, and the written music has two dots. The first form took any dot from 0.4
  to 1.1 staff spaces right of the first. Read on every page of LitChoir it gained its notes and lost none in
  the count, and the list of the pages that it changed showed eight more pages with a second dot that is none:
  the two dots of a repeat sign after a dotted half note, specks beside a dotted quarter on thick copies, and
  the stray marks of a hand. The count of their scores did not move, so only the list of pages showed them.
  Measured on the page, the seven true pairs stand 0.95 to 1.0 staff spaces apart, the
  smaller dot has 87 % or more of the larger one's ink, and paper lies between them. So the rule asks for that
  now: two dots that are alike and round, 0.7 to 1.25 staff spaces apart, with paper between, and no dot over
  or under the second one. The eight pages read as before, and the seven dots are kept: 8 notes change in
  wedding-georgian (the seven half notes and an eighth beside one of them), and its count rises by 11: the scorer lines
  up a voice anew when its lengths change. The score has 278 of its 280 notes now and is at 99 %.
- A bow from syllable to syllable. triodion-meatfare prints a small bow between two notes that sing the two
  syllables of one word ("glo-ry"), also where both notes have the same pitch. The reader took such a
  bow for a tie and made one long note of the two. Counted on every read tie that the scorer lines up: on the
  clean copies 117 are typed as one held note and 16 as two notes (8 of these on that page), on all scores 186
  and 30. One tie alone cannot be asked whether a syllable begins under its second note: where one voice holds
  its note the others sing on, and the words under the staff are theirs too. So the rule is one of the page
  (`ties.TIE_WORD`): where five bows or more of a page end over the beginning of a syllable, and these are at
  least half of the bows that have words under their staff, these bows are no ties. A syllable begins where a
  word of the row under the staff starts from two staff spaces left of the head to a little right of it.
  The first form took the words over a staff too, where none stand under it. It gained 22 notes and lost 1, in
  extra-beatitudes: a chord of whole notes is held in the bottom staff there, and the words over that staff are
  those of the staff over it, where the others sing on. So only the words under a staff are asked, and the ties
  of a chord count as one bow. In the reading the rule gains 22 notes and loses none: triodion-meatfare goes from 155 of 193
  notes to 177 of 195. The scorer counts 6 more notes that are not there in that score (12 to 18), and two typed notes
  that it listed apart are lined up now (so the clean copies count 22,591 drawn notes). The page reads the same heads as
  before: the second notes of nine bows are notes of their own now (201 read notes became 210, for 196 typed),
  and soprano and alto, which share the one staff, are lined up otherwise. Why the count of the notes that are not
  there rises with it was not looked into further.
- Looked at by part and left without a rule. wedding-service: its pages print repeats and verses in another
  order than the typed hymn has them. pascha-angel-cried (second score): ties of whole notes over a bar line
  that are not read, and dotted half notes at the end of a line that are read as half notes. communion-lords-prayer:
  the bold bows that run into the head that they tie (about 14 notes, as counted before).
  transfiguration-troparion (third score): a thick print where two heads a third apart are one blot.
- What the fresh test set showed. The round was read there in full before it was committed. It gains 12 notes and
  loses none (11 and none staff by staff), and the reader writes one note fewer that is not there (4,991). The
  two beams gain 8: 6 in one English piece and 1 each in two Romanian ones. The second dot gains 4, in one
  Romanian piece that prints quarters with two dots. The bow between syllables changes no note there. Nine
  pages change, four of them in no note. 15 notes change and 12 are gained; no piece has fewer right notes
  than before. No more piece is at 99 % (90).
- What the round loses on LitChoir: no score has fewer right notes than before, by parts and staff by
  staff, and no score changes its layout. The count of the notes that are not there rises by 6 in the score with the bows (see above).
- The words. Two more syllables are right on LitChoir, both on clean copies (5,781 of 6,240 there, 24,196 of 28,692 over all
  scores; 4 more whole words). On the fresh set the words did not change.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 116 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 79, where beams have gaps and chords lose their stems;
  nativity-kontakion 47, a print of a music typewriter), a rule of its own
  for the bold tie, a tie of whole notes over a bar line, the end of a slur under two notes that is read as a
  second stem, and the rests that are no printed quarter rest.
  The figures of this round are of its time.
- Six rounds before: the two clean scores that lack most, and a sharp that touches its head. After the round before
  it the clean copies lacked 850 notes for 99 % of each score, and two scores held a quarter of them:
  cherubic-lvovsky (123 notes, a photocopy that burnt out its filled heads) and the Rachmaninov "Rejoice, O
  Virgin" (85, a heavy worn print). The mistakes of the two were sorted by kind, and then the mistakes of the 23
  clean scores that lack one to six notes were looked at on the page, one by one. Three rules came of it, and
  each mends one cause on one or two scores: the round is small. The clean copies went from 21,572 to
  21,593 of 22,589 notes (95.6 %; 21 notes gained, none lost; 23 scores at 99 %, as before; 54 at 95 %, 71 at
  90 %), all scores from 77,057 to 77,078 of 89,724 (85.9 %; 21 gained, none lost; 77 scores at
  99 %, as before), and the fresh test set from 39,619 to 39,618 of 41,761 (94.9 %; no note gained; one fewer in the count by parts, see below;
  90 pieces at 99 %, as before). The reader writes as many notes that are not there as before: 922 on the clean copies, 5,678 on all scores
  and 4,992 on the fresh test set.

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A ring with a printed flag is an eighth where another voice says so (`symbols.RING_FLAG`) | 9, 0 | 9, 0 | 0, 1 |
  | The end of a thin beam beside a letter of the dynamics is no slur (`symbols.PAST_SLIM`) | 6, 0 | 6, 0 | 0, 0 |
  | A sharp that touches its head is cut from it (`symbols.SIGN_GLUED`) | 6, 0 | 6, 0 | 0, 0 |

  Counted staff by staff the round gains 21 and loses none on the clean copies, 21 and loses none on all scores, and
  changes nothing on the fresh set. Six pages of LitChoir change, all of clean copies.
- The ring with a flag. cherubic-lvovsky is a photocopy that burnt the middle out of its filled heads: a quarter
  is a ring like a half note, and an eighth is a ring with a flag. A half note has no flag. So the ink of a
  printed flag at the stem of a hollow head (one piece at the right of the stem's end and none at its left, as
  far and as thick as a flag, leaning, and no beam) says that the copy burnt the head out. Counted on all scans
  before the rule was written: 8 rings with such ink are typed eighths, all on clean copies, and 5 on the other
  scans are true half notes with a stroke beside their stem. So the ink alone changes nothing. The head is
  marked (`symbols.RING_FLAG`), and the note is an eighth only where another voice of its step says an eighth
  (`music.agree_lengths`): 7 notes to gain and none to lose in the count, and 9 gained and none lost in the reading (7 in
  cherubic-lvovsky, 2 in trisagion-arabic, where a quarter of the lower staff follows its step). The flag is
  asked of the stem of the note's own voice: the fresh test set showed a head of two voices that took the flag
  of the other voice's stem (see below). A rule for every hollow head with a tail would gain 15 notes and lose
  12, and was not written.
- The thin beam beside a letter. A thin beam is slim straight ink from the end of one stem to the end of the
  next, and where that ink goes on past the last stem it is a slur. On a page of the Rachmaninov the "mp" of the
  dynamics stands at the end of a beam: the beam's own end sticks out a little past the stem and runs into the
  p, and the rule took the two for a slur that goes on. Counted on the clean copies first: 1,942 thin beams that
  the reader keeps are right and 37 wrong, and of the 23 that it turns down for ink past a stem, 3 are turned
  down wrongly. Now a stroke that ends in a blob is the end of the beam (`symbols.PAST_SLIM`): slim in the first
  columns past the stem, and as high as a letter in the last. It stays a slur where the two stems bend and turn
  toward each other. 6 notes are gained on that page, two voices and the bass that follows their step.
- The first form of that rule, and why it was narrowed. It said that any thick ink past the stem is no stroke
  that goes on. Read on every page of LitChoir it gained 6 notes on the clean copies and lost none, and on the
  copies by hand it gained 8 and lost 7. Looked at on the page, both were chance: a hand draws its slurs 0.36 to
  0.67 staff spaces thick, and the stem of the next note or a bar line stands in the columns that the rule
  looks at. The limit moved a border and did not separate a slur from a beam there. In the narrow form no copy
  by hand changes.
- The sharp that touches its head. In memorial-troparia (second score) a sharp stands before two voices a
  second apart, and its right stroke touches the upper head. The two were one mark with strokes up and down at
  both sides, which is a sharp. So the upper head was not read, the sharp went to the head under it, and it
  held for the bar: 5 notes wrong by one sign. Such a mark is cut now (`symbols.SIGN_GLUED`): a stroke of a
  sign goes through its left third, the other stroke of the sharp stands left of it, and what is left of the
  mark at the right is as large as a head and has a long stem at its right side. The room that the stroke and
  the round side of the head close in is no hole of the head. Counted on all 657 scan pages, three marks are
  cut: two are a sharp and its head (6 notes: 5 in memorial-troparia, 1 in all-saints-troparion, which
  has every note now), the third is a beam that a word in pencil crosses, where no note changes. A first form made a
  half note of a quarter rest beside a pen stroke; since then the rule asks for the sharp's other stroke.
- Counted or looked at, and left without a rule.
  The ledger notes of nativity-kontakion: its print, of a music typewriter, sets a tenor's D and E over the
  bass staff alike, as a head that sits on one ledger line, and the line stands 1.3 to 1.7 staff spaces from the
  staff. The typed hymn has E for 7 of these heads and D for the others, and nothing on the page tells them
  apart: the reader reads D, as a singer would. Two more heads that the line goes through, like the C's beside
  them, are typed D.
  The pale quarters of cherubic-lvovsky that are read as half notes (15): the length of the bar mends 2 of them.
  Eighths that are read as quarters (44 on the clean copies, 18 in the Rachmaninov and 11 in cherubic-lvovsky):
  half of them have no ink at the end of their stem that a rule could read, a beam with gaps or a beam that
  lies in a staff line.
  Ties that are not read (32 on the clean copies): a cause each. In communion-lords-prayer the bold bows lie in
  the bottom line of the staff and run into the head that they tie, which is then not read either.
  Half notes that are read as quarters (52): the share of the hole does not separate them. Of the heads of the
  clean copies that are read as filled and have a hole under 8 % of the head, 382 are typed quarters and 24
  typed half notes, and no size of hole holds more half notes than quarters.
  Chords of the Rachmaninov whose stem and beam the worn print lost: two filled heads a third apart with no
  stem are no note.
  A sharp that touches a small head whose stem goes down along the sharp (cherubic-lvovsky, 3 notes).
  The 23 clean scores that lack one to six notes: 24 of their mistakes were looked at on the page, and no two
  share a cause.
- What the fresh test set showed. The round was read there in full before it was committed. The beam beside a
  letter and the sharp that touches its head change no note there. The ring with a flag, as it was first
  written, gained no note and lost 2 (1 staff by staff), and the reader wrote 3 more notes that are not there.
  The cause, on the page: a head that two voices share has two stems, and the rule took the flag at one stem
  for the voice of the other stem; the false eighth then outvoted a sixteenth of the staff under it. Since
  then the flag is asked of the stem of the note's own voice. LitChoir reads the same with it, note for note.
  In this form the rule changes four notes of the fresh set, and all four are notes that are not there: under a
  head that two voices share, the stem that goes down, the head and a staff line or a ledger line close in a
  room, and the
  reader takes the room for a ring beside the head. The flag at that stem is the voice's own, so the eighth is
  the voice's true length, at a pitch that is one place off as before. No note is gained and none is lost staff
  by staff, and the reader writes as many notes that are not there as before (4,992). By parts the count is one
  lower (39,618): in one Romanian piece the scorer lines the same read notes up otherwise, and an eighth that
  was read right before and is read the same now stands beside a typed sixteenth. The rule stays on. The room
  that is read as a ring is a cause for LitChoir's pages. As many pieces at 99 % (90) and at 90 % (178).
- What the round loses on LitChoir: nothing. No note that was right before is wrong now, by parts and staff by
  staff, and the reader writes as many notes that are not there as before.
- The words. They did not change: 5,779 of 6,240 syllables on the clean copies, 24,194 of 28,692 over all scores. On the fresh set they did not change either.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 116 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 79, where beams have gaps and chords lose their stems), the end of a
  slur under two notes that is read as a second stem of the second head (the half note of the other voice is
  then cut to a quarter), a rule of its own for the bold tie, and the rests that are no printed quarter rest.
  The figures of this round are of its time.
- Seven rounds before: an old fault in the thin ink, and the lengths that the voices change. The round before it found
  that OpenCV's opening lies one pixel off where its kernel has an even size, and that the tie reader had lived
  with it since ties were first read. The same step stands at four more places of the reader, and a closing with
  the same fault at 16. Each place was mended alone and read. One of them gains, and it gains more than any rule
  of the last rounds: the thin ink of the page. Then every length that the voices of a step change was counted
  against the typed hymns, and four rules for lengths came of the counts. The clean copies went from 21,517 to
  21,572 of 22,589 notes (95.5 %; 63 notes gained, 8 lost; 23 scores at 99 %, 22 before; 54 at 95 %, 71 at
  90 %), all scores from 76,916 to 77,057 of 89,724 (85.9 %; 282 gained, 141 lost; 77 scores at
  99 %, 76 before), and the fresh test set from 39,600 to 39,619 of 41,761 (94.9 %; 21 gained, 2 lost;
  90 pieces at 99 %, 90 before). The reader writes 922 notes that are not there on the clean copies (941 before), 5,678 on all scores
  (5,742 before) and 4,992 on the fresh test set (5,019 before).

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | The thin ink to the pixel (`layers.THIN_EXACT`; read alone, without the four rules under it) | 42, 10 | 242, 137 | 6, 2 |
  | A long note is no longer cut to the steps under it (`music.SPAN_CUT`, off) | 8, 0 | 14, 15 | 8, 0 |
  | A bar that is too long, on a page whose bars keep their length (`music.BAR_OVER`) | 3, 0 | 9, 1 | 2, 0 |
  | The heads of a chord on one stem are as long as each other (`music.CHORD_ONE`) | 7, 0 | 12, 22 | 5, 0 |
  | A mark that is nearly a dot, where the steps under the note ask for a dot (`symbols.DOT_ASK`) | 5, 0 | 23, 0 | 0, 0 |

  Counted staff by staff the round gains 58 and loses 10 on the clean copies, 280 and loses 114 on all scores, and
  15 and loses 2 on the fresh set.
- The fault in the thin ink. A weak copy breaks a stem into dashes, so the layers join a thin stroke over small
  gaps in its own column, up to half a staff space. Thin ink is the ink that no run of 0.3 staff space goes
  through from left to right. It is found by an opening, and where that run is an even number of pixels (on
  250 of the 482 scan pages, by their size) the opening of OpenCV lies one pixel to the right: the left column of
  every head, beam and letter was left over as thin ink. That column was then joined to what stood over or
  under it: the heads of a chord to each other, a head to the beam over it, a head to a letter of the words.
  Mended (`layers.THIN_EXACT`: thin ink is the ink that the opening does not hold, to the pixel) and read alone
  on every page of LitChoir, it gains 242 notes and loses 137 (42 and 10 on the clean copies; 227 and 109 staff by staff), and the reader writes 59 fewer notes that are
  not there. It gains on all three kinds of copy: heads that the false column had joined are two heads again,
  and a stem is no longer made of the edges of what stands under it.
- What the mended thin ink loses. Of the 137 notes, 62 are two scores by hand, and neither is a mistake of 31 notes.
  In lamentations-canon-ode-7 four more notes are read on the page, and the scorer then takes the melody and
  the ison for two staves where it took them for one: 31 notes fewer are counted right. In
  orthros-today-is-salvation (second score) five notes change (two their voice, two their length, one is lost),
  and the notes that the scorer counts with a right pitch fall from 54 to 27; this was not traced further. No
  other score loses more than 5 notes; 54 scores gain and 37 lose. On the clean copies the Rachmaninov "Rejoice,
  O Virgin" loses 4 notes (eighths under a beam that are read as quarters), cherubic-lvovsky 2, and four scores
  one note each. No key and no clef moved on any of the 482 scan pages.
- The other places stay as they are. Each was mended alone and read on the clean pages: the staff lines that
  are taken away under a mark (12 notes gained, 17 lost), the wide ink that shows a stroke through a staff line
  (5 and 13), the thin ink at the start of a staff (5 and 68: 57 of the 68 in one hymn whose worn key signature is
  read with the fault), and every closing of the reader at once (19 and 28). The limits of these steps were set
  on pages that were read with the fault, so the fault is a part of them, as in the tie reader. For the ties the
  other way was read too in this round, the fault on every page (`ties.TIE_RIM = 'all'`): it gains 1 note on
  LitChoir and loses 9, so a bold tie still needs a rule of its own. A stem that is broken at its head was tried
  as a rule in place of the fault (a thin stroke is joined to any ink over or under it): 10 notes gained and
  153 lost on the clean pages.
- The count of the lengths that are changed. The voices of a step vote on its length, and a note that says
  something else is changed. Every such change on the clean copies was set beside the typed length: 224 are
  right and about 50 are wrong. Most kinds are right four times of five or more. One kind is not: a note that
  reaches over several steps and is made as short as the steps under it. Of 9 such cuts 1 is right and 7 are
  wrong (a dotted half cut to a half where a voice under it lacks a note, a whole note cut to three quarters).
  The cut is switched off (`music.SPAN_CUT`); a note over one step is still made as short as its step. A rule of
  the round before, which kept such a note where it fills the bar, has less to do now. Without the
  cut 8 notes are gained on the clean copies and none lost, 14 and 15 on all scores. Of the 15, 13 are one
  score by hand, carol-heaven-and-earth (second score), where the scorer changes its layout (told below).
- The bar that is too long. Of the bars of the clean copies whose steps are all sure, 180 are not as long as the
  full bar of their page. Most of them are right as they are: a first bar, a last bar, a bar with a rest that
  is not read. A mend of any one step of such a bar would mend 10 notes and break 193. One narrow form holds:
  the bar is too long, and one step alone has a voice that says another length, with which the bar is full.
  Then that voice is right and the larger side is wrong (a hollow head that the print left pale, in two
  voices at once): 7 notes mended and none broken on the clean copies. A bar that is too short has no such
  form (1 and 3). Read on every page of LitChoir the rule first gained 9 notes and lost 13. The losses stand on
  pages whose bars change their length: half of the bars are four quarters long, and a true bar of five is cut.
  The gains stand on pages where 77 to 92 % of the sure bars are as long as each other, the losses but one on
  pages where 50 to 60 % are. The rule now asks for three quarters (`music.BAR_OVER`). With that it gains 9 notes on all scores
  and loses 1 (3 and none on the clean copies: 2 in cherubic-lvovsky, 1 in nativity-kontakion).
- The heads of a chord. Two heads on one stem are as long as each other, but the reader gives each head its
  own length: one head with a speck beside it is dotted, one head is hollow. The voices then vote with the
  shortest head, and the other head kept its length even where the step was sure. On the clean copies 15 such
  heads would be mended and 4 broken, if each took the length of the sure step. Read on every page, the rule
  lost notes on the copies by hand in two ways. A note without a stem that stands in the column of another voice is no head of
  its chord: the rule now holds for heads on one stem. And a hollow head beside a filled head on one stem was
  made a quarter 33 times, 21 of them on scores that lose by it: by hand the hollow head is the one that is
  read right. The rule now settles only heads of one kind, hollow or filled: a dot that is none and a flag
  that was missed (`music.CHORD_ONE`). A dotted head does not win over the head without a dot: of 7 such pairs
  on the clean copies the dot is false in 5. In this form it gains 7 notes on the clean
  copies and loses none, and 12 and 22 on all scores. Of the 22, 19 are two scores by hand where the scorer
  changes its layout (carol-heaven-and-earth, second score, 16; transfiguration-koinonikon-voronkoff 3); three
  scores lose one note each.
- A mark that is nearly a dot. Of the 30 dotted half notes of the clean copies that are read as half notes,
  each has a cause of its own: a dot that fills 0.51 of its box where 0.55 is asked, a dot 0.72 staff space
  over the middle of its head where 0.7 is the limit, a dot that a hand drew as a dash. Wider limits were counted
  three times in earlier rounds and lose as much as they gain. The bar can ask instead. Every mark at the right
  of a head that fails the tests of a dot by a little was listed with the steps under its note. Where the sure
  steps add up to one and a half of the note, the note is typed with a dot in 5 cases of 5; where they add up to
  the note as it was read, in 9 of 164. Without such a mark the steps alone are wrong: 1 of 15. So a mark that
  is nearly a dot (at most 0.75 staff space wide, 0.45 of its box filled, up to 0.8 over the middle of the
  head, of any shape) is taken for a dot where the steps under the note ask for one (`symbols.DOT_ASK`).
  It gains 5 notes on the clean copies and 23 on all scores, and loses none. Of the 23, 16 are one score by
  hand, theophany-megalynarion (second score), where a few notes change and the scorer changes its layout, to the
  good this time: the rule itself gains 7 notes in 6 scores.
- What the fresh test set showed. The round was read there in full before it was committed: 21 notes gained and
  2 lost (15 and 2 staff by staff), and 27 fewer notes that are not there (4,992). The exact thin ink gains 6
  notes and loses 2: one quarter in each of two English pieces is read as an eighth. The four rules for lengths
  gain 15 and lose none: the long note that is no longer cut 8, the heads of a chord 5, the bar that is too
  long 2, the mark that is nearly a dot none. No more piece is at 99 % (90); one more is at 90 % (178).
- What the round loses on LitChoir: 141 notes; 40 scores lose by the round and 70 gain. 62 of the 141 are the two
  scores by hand that are told under the thin ink. On the clean copies 8 notes are lost in 5 scores, all by the
  thin ink: 4 in the Rachmaninov, one each in communion-lords-prayer, non-liturgical-jesus-prayer,
  non-liturgical-o-pure-virgin (second score) and trisagion-arabic.
- The scorer's layout. On a copy by hand the scorer chooses how the staves of the page stand for the parts of
  the typed hymn (soprano and alto on one staff or on two), and a few changed notes can move that choice. It did
  so on four scores of this round: lamentations-canon-ode-7 (31 notes fewer), transfiguration-koinonikon-voronkoff
  (3 fewer), theophany-megalynarion, second score (16 more), and carol-heaven-and-earth, second score, which
  gains 25 notes by the thin ink and loses 13 of them again when the rules for lengths change a few of its
  notes. Such a figure says little about the rule that moved it, in either direction. With these four scores
  the round is 141 notes better on all scores, without them 147.
- Counted and left without a rule. Of the notes of the clean copies that are read a semitone off (99), about
  four in ten are heads on or beside a ledger line that are read one place off, a third are signs that are not
  read (a flat that touches its head, a sharp that a hand slanted), and the rest one of a kind. A step whose
  larger side is wrong where the bar is too short. A dotted head of a chord that wins over the others.
- The words. On the clean copies they did not change (5,779 of 6,240 syllables). Over all scores 14 syllables
  fewer are right (24,194 of 28,692), on copies by hand: five scores lose 19 and three gain 5. 12 of the 19 are
  orthros-today-is-salvation (second score), which is told above. On the fresh set they did not change.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 123 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 85, where beams and slurs run together), a rule of its own for the
  bold tie, the rests that are no printed quarter rest, and what the exact thin ink loses: the notes that change
  their voice on copies by hand, and a quarter that is read as an eighth.
  The figures of this round are of its time.
- Eight rounds before: the length of a full bar, the short tie, and an old fault of the tie reader. Of the 1,099 notes that the clean copies
  lacked after the round before it, 428 had only a wrong length, 257 only a wrong pitch and 99 both. The wrong
  lengths were listed by how the voices of their step had voted: 133 are notes over several steps, 157 stand
  where only the note itself says a length, 43 where one voice says one length and one voice another, 26 where
  two stand against two, and 36 where the larger side is wrong. The voices cannot decide these among
  themselves. Four rules were written and stand, and an old fault of the tie reader was found. The clean copies went from 21,490 to
  21,517 of 22,589 notes (95.3 %; 28 notes gained, 1 lost; 22 scores at 99 %, 22 before; 49 at 95 %, 72 at
  90 %), all scores from 76,815 to 76,916 of 89,742 (85.7 %; 113 gained, 12 lost; 76 scores at
  99 %, 76 before), and the fresh test set from 39,576 to 39,600 of 41,761 (94.8 %; 24 gained, none lost;
  90 pieces at 99 %, 86 before). The reader writes 941 notes that are not there on the clean copies (944 before), 5,742 on all scores
  (5,726 before: 7 more on each of the two scores of ascension-antiphon, which gain 8 notes each, and 8 on
  wedding-come-bless, which gains 15) and 5,019 on the fresh test set (5,032 before).

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A bar with one open step is as long as the full bars of its page (`music.BAR_FULL`, with the rule under it) | 23, 1 | 107, 12 | 11, 0 |
  | ... and the last note of a voice that ends where a full bar ends is not cut short (`music.BAR_KEEP`) | 4, 1 | 21, 6 | 4, 0 |
  | A beam that is thick at one stem and slim at the next (`symbols.BEAM_EDGE`) | 2, 0 | 3, 0 | 0, 0 |
  | A short tie whose ends lie under the heads (`ties.TIE_FLAT`) | 4, 1 | 4, 1 | 13, 0 |

  Counted staff by staff the round gains 28 and loses 1 on the clean copies, 106 and loses 18 on all scores, and
  22 and loses none on the fresh set.
- The first rule: the full bar. Most pages have no time signature that the reader could trust (the chant
  pages have none at all), but the bars of one page are mostly as long as each other. Every bar whose steps
  are all sure has a sum. Where half of these bars of a page or more, and four at least, have the same sum,
  that sum is the full bar of the page. A bar with one open step is then as long, and the open step is what is
  left of the sum, if a voice of that step says that length. The census of the clean copies, with the typed
  length of every note: with one open step the rule mends 14 notes and breaks 1; with two or more open steps it
  would mend 6 more and break 8, so it stops at one. The share of bars that must agree changes nothing between
  0.4 and 0.6, and the sum of the page serves as well as a sum of the whole hymn. The rule is asked twice: when
  the voices have voted, and again before a tie of quarters against halves is settled for the halves (a rule of
  an earlier round for heads whose hole the copy filled). At a tie the full bar decides first: on the census
  that only gains. Read with and without it, that order gains 13 notes on LitChoir (7 on the clean copies,
  most on one print whose filled heads are pale) and loses 4, all in one bar: the last bar of a hymn holds three
  half notes on a page whose bars hold two, and the full bar makes one of them a quarter.
- The second rule: a note that fills the bar. A long note over several sure steps was made shorter where the
  steps add up to less than it. But at the end of a bar the other voices often rest, the rest is not read, and
  the long note is right. A note that ends where the full bar ends is left as it is. On the census 5 notes that
  were cut wrongly are kept, and 1 right cut is lost. Read on every page the rule first gained 22 notes and lost
  26 on LitChoir, most on copies by hand (4 and 2 on the clean copies; 9 and none on the fresh set). The lost
  notes were looked at on the page: an eighth before two sixteenths whose second beam is not read, an eighth
  with a flag read as a quarter, a natural sign read as a hollow head. Each has another note of its voice
  after it in the same bar, so it cannot reach the end of the bar. The rule now holds for the last note of a
  voice in its bar only, and for a whole note whatever follows: a whole note has no stem to show its voice,
  and a note that comes after it on its staff need not be of its voice (on a clean page a speck at the end of
  a slur is read as a note after two whole notes of the basses, and cut them to dotted halves). In this form
  the rule gains 21 notes on LitChoir and loses 6 (4 and 1 on the clean copies), and 4 and none on the fresh set.
- The third rule: the edge of a beam. A beam is told from a slur between two stems by its thickness, taken at
  each stem. One beam can be just thick enough at one stem and slimmer at the next, and was then no beam at the
  second, and its notes were quarters. A beam under 0.3 staff space that the next stem does not show as a thick
  beam is now looked at as a slim beam too, with the tests that a slim beam has to pass.
- The fourth rule: the short tie. Two eighths of one pitch under one beam stand so close that the ends of their
  tie lie under the heads, and the part that shows is flatter than a bow had to be (0.2 staff space). Every
  pair of heads of the clean copies that could be tied was listed again with the ways that the reader follows
  from head to head: 7,594 pairs. A way whose ink shows in 0.9 of its columns or more and that is 0.15 to 0.2
  high stands at three pairs, all three of them ties; the flat ways between notes that are not tied (lines
  under words, the edge of a beam) are under 0.06, or show in under 0.7 of their columns. Such a way is a bow
  from 0.15 on. Read on every page of LitChoir that gained the 3 ties and made 2 false ones, on a thick print
  and on a copy by hand: the ledger lines of two neighbours touch and sag, and the way runs from head to head
  at the height of the heads (0.3 and 0.4 staff space from their middles; the ends of the three ties lie 0.8
  to 1.3 from them). The flat bow now has to begin and end 0.6 staff space or more over or under the middles
  of the heads.
- What the fresh test set showed. There the rule for the short tie first gained 13 notes and lost 4, all 4 in
  one piece: eighths with flags, two voices a second apart, and a tie from each lower head to the next. The way
  that was followed is the upper edge of the next upper head. The tie reader follows thin ink: the ink without
  its thick blobs (every run of ink higher than 0.4 staff space, column by column). The blobs are found by an
  opening of OpenCV, and where the limit is an even number of pixels its result lies one pixel low: the top row
  of every head, beam and stem is left over as thin ink. That holds on about half of the pages, by their size,
  since ties were first read. A way along the top of a head is short and curved like a flat bow. Mended for
  every bow (thin ink is the ink that is no blob, to the pixel) and read on every page of LitChoir, it gained
  5 notes and lost 5, 4 of them on the clean copies: a bold tie is thicker than the limit in its middle, and it
  was followed along that top row. The fault is also a rule that nobody wrote. So it stays as it is for the
  bows that were read before (`ties.TIE_RIM`: on those pages, on every page, or on none), and the flat bow of
  the new rule is followed on thin ink without that row. With that the rule gains 13 notes on the fresh set and loses none, and 13 notes that are not there are
  gone. On LitChoir the exact thin ink shows three more bows of the old height: one is a tie, one is not, and
  one changes no count. Left for a next round: a rule of its own
  for the bold tie, on every page.
- What the round loses on LitChoir: 12 notes in 8 scores, 6 of them second scores of their
  hymn. Four in the last bar of liturgy-holy-holy (second score), told above. Two in koinonikon-black-long,
  where a bar of one open step is filled and its eighths are made whole notes. Two whole notes that are kept at their
  length where the typed hymn has them shorter (megalynarion-bortniansky and pascha-thy-resurrection, second
  scores). One on the clean copies (non-liturgical-o-pure-virgin, second score: an eighth in an open step is
  made a quarter). The other three were not traced. The two counts part on one score by hand,
  wedding-come-bless: its whole notes are kept now, as the page shows them; by parts it gains 15 notes, and
  staff by staff it loses 7, because the scorer then takes its other layout. That is why the round gains 106
  and loses 18 on all scores staff by staff, and why the rule for the note that fills the bar, which gains 21
  notes and loses 6 by parts, reads 11 gained and 16 lost staff by staff.
- Counted and left without a rule. The 37 ties of the clean copies that are not read have a cause each (a bow
  over the end of a line, a bow that a stem cuts, a bow in a staff line). A hollow head with a flag or a beam
  is no half note: 11 notes would be mended and 17 broken, because one print (cherubic-lvovsky) leaves its
  filled heads pale. The heads on ledger lines that are read a step off on three scores have the same
  measures as the right ones of their page: there the typed hymn seems to differ from the print. Making a long
  note as long as its sure steps: 14 notes to gain and 25 to lose. Making the last note of a voice fill the
  bar: 26 and 565.
- The words. On the clean copies they did not change (5,779 of 6,240 syllables). Over all scores 2 more syllables
  are right (24,208 of 28,692), on thick prints. On the fresh set they did not change.
- Left for the next rounds: the scores that lack most (cherubic-lvovsky 129 notes, with pale filled heads;
  the Rachmaninov "Rejoice, O Virgin" 84, where beams and slurs run together), the rests that are no printed
  quarter rest, and a bar with two open steps.
  The figures of this round are of its time.
- Nine rounds before: the lengths that the voices say to each other, and the printed quarter rest. Of the 1,124
  notes that the clean copies lacked after the round before it, 452 had only a wrong length, 259 only a wrong
  pitch and 101 both. The largest kinds of wrong lengths: an eighth read as a quarter (55), a quarter read as an
  eighth (42), a quarter read as a half (40), a half read as a quarter (36), a dotted half read as a half (34)
  and a whole note read as a half (20). Five rules were written and stand. The clean copies went from 21,465 to
  21,490 of 22,589 notes (95.1 %; 26 gained, 1 lost; 22 scores at 99 %, 21 before; 48 at 95 %, 70 at
  90 %), all scores from 76,758 to 76,815 of 89,742 (85.6 %; 63 gained, 6 lost; 76 scores at
  99 %, 75 before), and the fresh test set from 39,559 to 39,576 of 41,761 (94.8 %; 18 gained, 1 lost;
  86 pieces at 99 %, 85 before). The reader writes 35 fewer notes that are not there on the clean copies
  (944), 44 fewer on all scores (5,726) and 83 fewer on the fresh test set (5,032).

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A long note is a witness for the steps under it (`music.SPAN_VOTE`, with the two rules under it) | 27, 1 | 62, 6 | 15, 1 |
  | ... where it can say the lengths of several open steps at once (`music.SPAN_SUM`) | 2, 0 | 4, 0 | 0, 0 |
  | ... and only a length that a voice of the step says too (`music.SPAN_SIDE`) | 0, 2 | 0, 3 | 6, 0 |
  | A printed quarter rest is no note (`rests.QUARTER`, with the rule under it) | 0, 1 | 2, 1 | 4, 1 |
  | A voice with a rest after its note makes no voice that sings on shorter (`music.REST_SPAN`, read off on every page) | 0, 0 | 1, 0 | 0, 0 |

  Counted staff by staff the round gains 29 notes and loses 1 on the clean copies, 70 and loses 5 on all scores, and
  15 and loses 1 on the fresh set. By staves the long note as a witness gains 61 notes and loses 5 on all scores, the rule for
  several steps 4 and none, the rule for the length that a voice says none and loses 3, the reader of rests 4 and loses 1 and the
  rule for the voice that rests 3 and none.
- The music check before this round. The columns of the staves of a system are lined up, and from one column
  to the next every voice that has a note in both says how long that step is. Where two or more voices agree
  and outnumber the others, a note that says something else is changed. A note that reaches over several
  columns said nothing, and was only made shorter. The length mistakes of the clean copies were listed by how
  the voices had voted: 133 are notes over several steps (beside 2,641 such notes that are right), 66 stand
  where one voice says one length and one voice another (115 right notes stand there too), 58 where the note is
  the only voice of its step, and 26 where two voices stand against two.
- The first rule: a long note is a witness. A half note in the bass under two quarters of the tenor says
  nothing about either quarter. But where one of the two steps is sure, the half note says that the other
  step is what is left of it. Such a note counts as one more voice of that step; two or more voices must still
  agree and outnumber the others. When a step has become sure, the long notes are asked again. The second
  rule: where several steps under a long note are open, each has one length said, and these lengths and the sure
  steps add up to the long note, it says each of them.
- The third rule came from the fresh test set. The first two rules gained 14 notes there and lost 6. The
  cause was read on its pages: a staff with one line of melody draws its stems up and down with the height of
  the notes, the reader takes each direction for a voice, and a quarter with its stem down then seems to last
  until the next stem down. And where another step under a long note is sure but wrong (the second beam of a
  sixteenth is not read), what is left of the long note is no length at all. Both give a length that no voice
  of the step says. So the long note only takes a side now: its length for a step counts when a voice of that
  step says the same. On LitChoir that costs 3 of the gained notes (2 on the clean copies, in the two scores
  of one hymn); on the fresh set it gains 6 notes and loses none. One note of the fresh set is still lost: a
  dotted eighth before a sixteenth is made an eighth, and a voice of its step says so too.
  A second guard was written for the first cause and dropped: the long note had to be a voice of its own (its
  staff shows two voices in its column, or in its bar). With the third rule on, it changed nothing on the
  fresh set, and on LitChoir it cost 2 more gained notes in its first form and 1 note in its second.
- What the long note loses on LitChoir: 6 notes, each in another score. On the clean copies one: a pencil
  circle around three notes is read as a half note, and as a long note it is a false witness
  (nativity-god-is-with-us, which falls from 95.0 % to 94.2 %). The other five are single notes on other scans
  (a half note cut to a quarter, a dotted half to a half, an eighth made a quarter); their votes were not
  traced.
- The fourth rule: the printed quarter rest. The reader of scans knew no rest. The thick middle of a quarter
  rest is as fat as a head and its thin strokes stand like a stem, so the rest was read as a quarter note, and
  that note was a false voice in the music check. Every piece of ink without the staff lines that is 2.0 to
  4.0 staff spaces high and 0.5 to 1.8 wide and lies in a staff was listed on the clean copies with its
  measures and with the note that was read there: 6,968 pieces. The height, the width and the thickness of its
  strokes do not tell a rest: 33 quarter notes with short stems and slanted heads pass such a test beside the
  rests, and so do the pairs of sharps of a key signature. Three measures of the shape do. The piece closes in
  no paper (a pair of sharps, a natural at its head and a clef do). Neither its left nor its right edge is
  straight (the stem of a note is: one edge stays within 0.15 staff space over more than 0.85 of the rows). And
  the middle of its ink, taken in eight parts from top to bottom, swings to the right, back to the left, to the
  right again, and to the left at the hook (by 0.12, 0.12, 0.03 and 0.08 staff space at least; the rests of the
  list have 0.13, 0.14, 0.04 and 0.10 at least). The rule takes a piece that is 2.0 to 3.6 staff spaces high
  and 0.7 to 1.3 wide. 91 pieces pass: 62 that were read as nothing, 29 that were
  read as a note that is not there, and none with a right note. A head whose middle lies in such a piece is no
  note. Rests that stand over or under the staff, where two voices share it, are found too. On LitChoir the
  reader of rests, with the fifth rule, gains 2 notes and loses 1 and takes away 38 notes that are not there (30
  on the clean copies). The lost note is on a clean copy (wedding-isaiah): the faint, bent stem of a quarter
  reads as a flag, and the rest in the staff under it, read as a quarter note, had voted for a quarter and
  mended it by chance. On the fresh set it takes away 85 notes that are not there of about 5,100: it finds few
  of the rests of those pages. Its limits were set on LitChoir's prints, and it was not looked at which rests
  it misses there.
- The fifth rule: what a rest says about lengths. It took three forms. A note with a rest after it is shorter
  than the step to the next note of its voice. First form: such a note does not vote. It gained 1 note and lost
  2 on LitChoir: on two pages every voice has a dotted half and a quarter rest, one dotted half is read as a
  dotted quarter, and the votes of the other voices had mended it; the rest of its own staff touches the bar
  line and is not found. Second form: it votes, and is only not made longer. It changed no count, and with the
  rest no longer read as a note, two resting voices on one page cut a whole note of the basses to their own
  length (2 notes lost staff by staff). Third form, which stands: the voices that rest together are as long as
  each other, so they vote; but a length that fewer than two voices without a rest say is the length of the
  resting voices and not of the step. It makes no note without a rest shorter (that voice sings on), it can
  make one longer (its own rest was not found), and it is no part of the sum of a long note. A long note with a
  rest after it is no witness. On a staff of two voices a rest that stands a staff space or more over the middle
  line is the upper voice's, and one as far under it the lower voice's.
- A rule that guards is in no list of changed pages: where it stops a wrong change, its page reads as on main.
  The fifth rule was therefore read off on every page of LitChoir and of the fresh set, not only on the pages
  that the round changes: 2 pages of LitChoir differ (a whole note and a half note that are no longer cut
  short), and none of the fresh set. That reading was made before the third rule was written; with it the
  rule was read off on the pages that the round changes, with the same counts.
- Counted and dropped. The width of a step as a witness for its length: on the clean copies an eighth takes
  0.69 of the width of a quarter in the middle of the list, but a quarter takes 0.68 to 1.63 of it; as a
  tie-break between two voices it mends 15 to 18 notes and breaks 7 to 9. And making a long note longer where
  the sure steps under it add up to more than it: 16 notes of the clean copies would gain, and 114 right notes
  stand in the same case, because a rest follows them; that needs every rest read first.
- The words. No word is read differently, and no score changes its count of syllables: 24,206 syllables are right
  on all scores and 5,779 on the clean copies, as before. The kit gained 3 notes (6196 to 6199), in two hymns
  where a long note is a witness.
- Left for the next rounds: a quarter rest that touches a bar line or a slur (it is no piece of ink of its
  own), eighth, half and whole rests, the rests of a hand, a letter of the dynamics and a pencil mark that are
  read as notes and then vote on lengths, and the long note that could be made longer where no rest follows.
  The figures of this round are of its time.
- Ten rounds before: the clean scores that lack one to three notes. After the round before it, 14 of the 78 clean
  scores lacked one to three notes for 99 % (5 lacked one, 4 two, 5 three). Their mistakes were looked at on the
  page, one by one. Five rules were written, and all five stand. 21 clean scores are at 99 % now (16 before), and
  9 lack one to three notes. The clean copies went from 21,432 to 21,465 of 22,589 notes (95.0 %; 38 gained, 5
  lost; 49 scores at 95 %, 70 at 90 %), all scores from 76,577 to 76,758 of 89,748 (85.5 %; 239 gained, 58 lost;
  75 scores at 99 %, 70 before), and the fresh test set from 39,500 to 39,559 of 41,761 (94.7 %; 60 gained, 1
  lost; 85 pieces at 99 %, 83 before). The reader writes 67 fewer notes that are not there on the clean copies
  (979), 196 fewer on all scores (5,770) and 159 fewer on the fresh test set (5,115).

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A cell of the staff with a straight end at a bar line or a stem is no inside of a head (`layers.HOLE_SIDE`) | 29, 5 | 224, 57 | 60, 1 |
  | The inside of a whole note of a heavy print has a little more paper in its corners (`layers.WHOLE_INSIDE`, 0.3 to 0.33) | 2, 0 | 7, 1 | 0, 0 |
  | A head that two voices share is tied to both heads of the next moment (`ties.TIE_BOTH`) | 2, 0 | 2, 0 | 0, 0 |
  | The lower head of a chord with its stem down is no flat (`symbols.FLAT_STEM`) | 1, 0 | 4, 1 | 0, 0 |
  | After "Un." the held part sings one line through the notes of both voices (`music.UNISON_LINE`) | 4, 0 | 4, 0 | 0, 0 |

  Counted staff by staff the round gains 34 notes and loses 5 on the clean copies, gains 249 and loses 71 on all
  scores, and gains 47 and loses 2 on the fresh set. By staves the first rule gains 228 and loses 72 on all
  scores, the second 8 and 1, the third 2 and 0, the fourth 5 and 0, and the fifth 4 and 0. On the fresh set the
  first rule changes 69 pages and the second one page; the other three change none.
- The first rule and its census. The layer of the holes fills small paper that ink closes in: the inside of a
  hollow head. The paper between two staff lines is closed in too, where a bar line or a stem stands at one of
  its ends and the round side of a head, a second stem or the end of a beam at the other. Such a cell was filled
  like the inside of a head. A filled head beside it became one mark with a hole and was read as a half note, and
  the cell under a beam between two stems was read as a hollow head of its own. Every filled hole of the clean
  copies was listed with its measures and with the note that was read there: 21,346 holes, 7,147 of them with a
  right note (most of the others are letters of the words). The inside of a right hollow note is 0.62 staff
  spaces wide in the middle of the list, 0.89 at 90 of 100, 1.05 at 99 of 100 and 1.63 at most. 279 holes are
  1.1 staff spaces wide or more and have a straight end (the outer tenth of their columns is 0.7 of their height
  or more) that lies against an upright stroke 2.0 staff spaces long or more. None of the 279 holds a right
  hollow note, 6 stand beside a right filled note, and 32 hold a note that is not there. With a stroke of 1.2 to
  1.6 staff spaces there are 2 right hollow notes, so the stroke must be 2.0 long. The rule: such paper is a cell
  of the staff, and it is not filled.
- The first form of that rule lost 115 notes on the clean copies beside 30 gained, 100 of them in one score. The
  clef and the end of the key signature are read from the solid shapes at the start of a staff, and a clef
  closes cells in against the line at the left end of the staff. On one page four such cells were no longer
  filled, the found end of the clef moved in two staves, and the hymn's key was voted with 2 flats where it has
  4. The rule now leaves the first 4.5 staff spaces of every staff alone. That page has the key and the ends of
  main again, and two holes differ.
- What the first rule loses. It was kept with these losses, because it gains about four times as many notes and takes
  away most of the round's notes that are not there. On the clean copies 4 notes of one score
  (communion-lords-prayer, which falls from 90.8 % to 89.8 %): half notes of a heavy print whose own inside has
  a speck of ink and is not found as a hole. They were read as half notes only because the cell beside them was
  filled; they are quarters now. And 1 whole note on a ledger line: the page measures the usual hole of its
  hollow heads, four cells under beams no longer count among them, the limit for a hollow head rose from
  0.057 to 0.084 of the mark, and that whole note has 0.08. On the other scores: 20 notes of one copy by hand
  that is half right (the rule changes 11 notes on its two pages; of seven places looked at, four are cells or
  scribbles that were read as notes; the scorer then lines its staves up with other parts, and staff by staff
  it loses 31); 4 notes
  of a copy by hand that draws its flags as closed loops (the loop was filled as a hole and known as a flag; now
  it is open and is read as a thin hollow head); and one to three notes in 18 scores. Six of these were looked
  at on the page: the numbers of a time signature in the middle of a staff close to a bar line (two scores), a
  large flat, the signs of a thick copy and two copies by hand are read with other false notes than before.
  Which note was right before, and why, was not traced there, nor in the other twelve.
- The second rule. A whole note between two staff lines is as high as a cell of the staff, and a rule tells its
  inside from a cell by its four corners: paper fills less than 0.3 of them, because the inside is an oval. All
  8,209 pieces of paper of the clean copies that are as high as a cell were listed. 153 pass the rule, 97 of
  them with a right whole note (their corners are 0.25 at most). 13 narrow pieces fail at the corners alone: 7
  have 0.31, which is 5 of 16 corner pixels (four whole notes of two heavy prints, two of them a third from
  another whole note, and the letters P, B and g of the words, which are no notes in either case), the flats
  of two key signatures have 0.36 and 0.58, and a treble clef has 0.47. The limit is 0.33 now. One pair of whole
  notes a third apart is still not read: two heavy ties run into it.
- The third rule. A head with a stem up and a stem down is the note of two voices. When it is tied and the next
  moment prints the two voices as two heads side by side (a half note and a quarter of the same pitch), the
  print draws a bow over and a bow under. The reader tied the first of the two heads only, and the other was a
  new note. Now a head of the other voice that stands at most half a staff space to the right of the tied one,
  at the same place, is tied too when a bow reaches it. One printed score has this (megalynarion-bulgarian, 2
  notes, now at 99 %). A tie of this kind over the end of a line is not read.
- The fourth rule. A chord with its stem down has the stem at the left of its heads. The lower head, with the
  stem going up from its left side to the upper head, is the shape of a flat: a bowl with a stroke up from its
  left. The rule for a flat by hand named it one. Now a filled mark as large as a head that is named a flat is a
  head when a head over it has a stem down in the column of that stroke (0.35 staff space at most apart), the
  stroke ends at that head, and the head's stem was followed down to the mark. On LitChoir it gains 4 notes (5
  staff by staff) and loses 1 by parts, none by staves: on a copy by hand a scribble under a whole note is a
  note now, and the scorer lines the staff up otherwise.
- The fifth rule. On a chant page the letters over the staff name the held note of the ison, and "Un." ends it:
  from there the held part sings the melody. The reader copied the notes of the first voice of the staff. But
  the melody is one line whose stems go up and down with its height, and a note with its stem down is read as a
  second voice: the held part had gaps. Now the held part takes the notes in the order of their beginning, each
  one that begins when the one before has ended: one line through both voices. One clean score gains 4 notes and is at 100 % (hierarchical-xenia-apolytikion). The held notes are
  written into the music of a page and are not among the notes of the page that the tools compare, so the list
  of pages that a round changes did not hold this page; the list compares the written music too now.
- The words. 24,206 syllables are right on all scores (24,200 before) and 5,779 on the clean copies (5,780). The
  rules do not touch the reading of the words. A syllable hangs on a note, and where a note that is not there
  is gone, or a note is new, a syllable can hang on another note or count for another part. Nine scores change by one to three
  syllables (six gain, three lose). The one syllable of the clean copies is the last of a hymn whose final
  chord lost two notes that are not there. The kit gained 21 notes (6175 to 6196): 19 by the first rule, 15 of
  them on one copy by hand (11 staff by staff), and 2 by the third. The figures of this round are of its time.
- Looked at in this round and left without a rule. A score whose page crosses two voices by their stems where
  the typed hymn does not (megalynarion-bulgarian, 2 notes). Pencil marks that are read as notes (two scores).
  Half notes with an open rim that are read as quarters (trisagion-obleschuk). A dash after a note that is read
  as a dot (memorial-troparia). Filled heads of a speckled print that are read as hollow
  (forerunner-nativity-apolytikion). The lengths of a bold print (transfiguration-hymn-theotokos). The letter of
  an ison that stands right at the clef, with a breve that is not read (pascha-hypakoe; 16 marks of an ison are
  missed on the clean copies). A typed hymn in four parts with divided voices against a page of two staves
  (liturgy-what-shall-i-render, 13 notes).
- Eleven rounds before: notes that are not there. The reader wrote 1,095 notes on the clean copies that the typed
  hymns do not hold. 80 of them were drawn by lot and looked at on the page. About 4 of 10 are true notes that
  the count cannot place: the second half of a long note whose tie is not read, or a note that the scorer lines
  up with another. Of the rest the numbers and signs of time signatures are the largest kind (12 to 22 of 100),
  then the letters p and f between the staves (10), quarter rests (8) and paper closed in by a slur (8). Two rules were written and both stand. The reader writes 49 fewer notes that are not
  there on the clean copies (1,046), 107 fewer on all scores (5,966, from 6,073) and 212 fewer on the fresh test
  set (5,274, from 5,486). The notes right moved little: the clean copies went from 21,427 to 21,432 of 22,589
  (94.9 %; 5 gained, none lost; 16 scores at 99 %, 47 at 95 %, 71 at 90 %), all scores from 76,563 to 76,577 of
  89,747 (85.3 %; 15 gained, 1 lost; 70 scores at 99 %), and the fresh test set from 39,494 to 39,500 of 41,761
  (8 gained, 2 lost).

  | Rule, switched off alone in the final reading; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | The two numbers of a time signature that touch, or that a bold print sets (`meter.TIME_STACK`) | 2, 0 | 12, 1 | 8, 2 |
  | A bracket of a triplet that is made of the hyphens of the words (`triplets.IN_WORDS`) | 3, 0 | 3, 0 | 0, 0 |

  All of the fall of the notes that are not there is the first rule's. Counted staff by staff the round gains 6
  notes and loses none on the clean copies, gains 22 and loses 1 on all scores, and gains none and loses 2 on
  the fresh set. The scorer lists 8 more typed notes apart than before (1 on the clean copies), so the notes
  drawn are 89,747 now. The notes gained by the first rule were not traced one by one.
- The census behind the first rule. A time signature was found as two numbers, one over the other, that are no
  bar line (no column of ink along the whole height of the staff) and no thick blot of a head. A close print
  sets the two numbers so that they touch: a 4 over a 4 has a column of ink from the top line to the bottom
  line, like a bar line. A bold print makes blots as thick as heads of them. Every piece of ink on the clean
  copies that is two halves of the right size was listed with its measures: 270, of which the old rule found 23.
  The new rule takes 44 more, and each is a time signature on its page (4/4, 3/4, 2/4, 6/4, 3/2). What separates:
  the two numbers are 1.30 to 1.81 staff spaces wide together, their full columns lie between 0.10 and 0.81 of
  the width, and 0.50 to 0.85 of their inked columns are ink along a part of the staff only. A bar line with what
  stands beside it has its full columns at 0.04 to 0.17 or at 0.83 to 0.93 of the width, is 1.21 wide at most and
  has few such part columns (0.36 at most, but for a few). An eighth note with its stem down and a flag has its
  longest column in the first 0.13 of the width, and with its stem up it is 2.05 wide or more. The rule: two
  halves that are 1.25 to 1.9 staff spaces wide together, each 1.1 wide or more, whose columns of ink along 0.85
  of the staff's height or more all lie between 0.08 and 0.81 of the width (from 0.25 where no column runs the
  whole height), and of whose inked columns 0.45 or more are ink along a part of the staff only, are numbers.
  Two time signatures of the clean copies are still not found: one stands a quarter of a staff space off the
  lines, and one has its full column at 0.83 of the width.
- The second rule. One hymn of the clean copies sings "Al-le-lu-i-a" under a staff. The two hyphens with the
  syllable between them, and an l at each outer end, look like the bracket of a triplet: two flat arms, a hook
  at each outer end and something in the break. Three true notes were read as a triplet. LitChoir's pages have
  30 brackets, and this is the only false one. Three forms were counted. The first: a bracket whose row lies in
  a band of the words and that has ink at both of its sides is a piece of the words (17 true brackets lie in
  such a band, and none has ink at both sides). It gained the 3 notes and lost none on LitChoir, and lost 2
  notes on the fresh test set: a true bracket there stands between two syllables. The second form added that
  less than 0.8 of the row of the arms is ink (0.66 in the false bracket, 0.88 to 0.94 in the true ones). It
  still lost the 2 notes: that bracket is narrow, and the break for its number is a large share of its width.
  The third form stands: beside its two widest gaps (the break, which the number divides in two), 0.08 or more
  of the row of the arms is bare. The 29 true brackets of LitChoir have 0.02 at most there, and the false one
  has 0.16. It gains the 3 notes on LitChoir, and no page of the fresh set is read differently with it. The
  limit of each form was set on LitChoir's 30 brackets alone, but the fresh page showed why two forms failed, so
  for this rule that page is no longer unseen. One false bracket is thin ground for a rule; it stays because it
  loses nothing on any page that was read, and because it brings that hymn to 99 %.
- What the round loses. On LitChoir one note of a copy by hand: its time signature was not found before, the
  notes of the staff began too early, and the flat of the key signature was read as the flat of one note, which
  was right by chance. Now the time signature is found, the flat stands before the notes, and the hymn's key is
  still voted to have no flat. On the fresh test set 2 notes of one piece: the 2 of the time signature had been
  read as a half note on the middle line, and the typed first note of that part is a half note on the middle
  line, in two staves. The true first note is read with a wrong length, and that shows now. The words did not
  change (24,200 syllables right on all scores, 5,780 on the clean copies). The kit gained 3 notes (6172 to
  6175): the false triplet. The figures of this round are of its time.
- Looked at in this round and left without a rule. The letters p and f between the staves, read as notes with
  short stems outside the staff (14 on the clean copies with a hollow head): the length of the stem, the ledger
  lines and the size of the piece of ink do not tell them from true notes. The printed C of common time (about
  30 on the clean pages, 1 found): a bold C fails three checks of the rule for the thin C of a hand, and two new
  measures of its opening failed, because the layer that they read shows the C partly filled. A quarter rest
  read as a thin head: of the thin heads that stand 0.3 of a place or more off the grid, 12 are right, 5 have a
  wrong pitch and 23 are not there, too close for a limit. A
  slur that ends at the end of a stem and is read as a flag (43 notes on the clean copies), a slur between two
  beamed stems that is read as a hollow head and takes the stem, filled heads of a speckled print that are read
  as hollow, and a dot of the lower voice that is given to the upper head.
- Twelve rounds before: notes of a chord that are not read on the clean copies. A new tool lists every typed note that
  the reader has no note for while it has another note of the same moment on that staff: 160 on the clean
  copies. The largest shape among them is two voices a second apart with their stems back to back on one line.
  The head of the upper voice stands at the left of the stem and the head of the lower voice at its right, half
  a staff space lower, and the print makes one blot of ink of the two heads and the stem between them. The old
  cut for touching heads asks for a blot that is clearly made of two heads on a diagonal; these blots are too
  full for it. Many were read as one note, and some as no note at all, so the rule gains more notes than the
  list holds for this shape. Four rules were written. Three stand, and one is switched off with its counts. The
  clean copies went from 94.7 % to 94.9 % of the notes (45 gained, none lost: 21,427 of 22,590; 15 scores at
  99 %, 47 at 95 %, 71 at 90 %), all scores from 85.2 % to 85.3 % (76,563 of 89,755; 103 gained,
  1 lost; 69 scores at 99 %). The fresh test set did not change: 39,494 of 41,761 notes as before, and
  no page of it is read differently.

  | Rule, switched off alone with the other three on; notes gained, lost by parts | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | Two heads a second apart at the two sides of a stem are cut at the stem (`symbols.PAIR_STEM`) | 41, 0 | 99, 1 | 0, 0 |
  | The lower of two heads that touch was named a flat: it is a head (`symbols.FLAT_HEAD`) | 3, 0 | 3, 0 | 0, 0 |
  | A head that gets back the stem it lost shares it with the stemless head of its blot (`symbols.LOST_SHARED`) | 4, 0 | 4, 0 | 0, 0 |
  | Off: a stemless head takes the stem that runs through the head it touches (`symbols.STEM_THROUGH`) | 1, 2 | 11, 5 | 0, 0 |

  The fresh set was read in full with all four rules on, and then with each rule off on the 4 pages that differed:
  the rule that is off wrote 2 notes there that are not there, and the other three change no page. Counted staff
  by staff the three rules that stand gain 44 notes and lose none on the clean copies, and gain 110 and lose 5
  on all scores. The notes that are not there go from 1,099 to 1,095 on the clean copies and from 6,072 to 6,073
  on all scores.
- The census behind the first rule. Every filled blot of the clean copies that is wider or higher than one head
  and no larger than two was listed with its measures and with the notes that were read from it: 179 blots on
  151 pages. 17 hide a second of which one note is missed, and about 20 more are seconds that were read as one
  pitch twice or not at all. In the true pairs the stem stands at 0.36 to 0.62 of the width, each side holds
  0.43 of a head or more, the ink at the left of the stem lies 0.11 to 0.41 staff spaces higher than the ink at
  its right, and the blot is 0.33 to 0.69 staff spaces higher than a head. The rule: a filled blot 1.3 to 2.3
  heads wide with a slim stroke in its middle third, 0.4 of a head or more at each side, and the ink at the left
  higher by 0.08 staff spaces or more. A blot that is more than 0.65 staff spaces higher than a head must lean
  by 0.25 or more and may be 1.85 heads high at most: a third is a whole space higher than a head, and a unison
  of a heavy print leans a little too.
- Forms of the first rule that were counted and dropped. Either direction of the lean (the lower voice at the
  left as well): 40 gained and none lost on the clean copies, 101 and 5 on all scores, but 3 notes lost for none
  on the fresh test set and three false cuts seen on LitChoir's pages (a third and a unison of a heavy print,
  a hollow head drawn by hand). The falling form with the one limit of 0.65 staff spaces over a head: 38 and
  none on the clean copies, 89 and 1 on all scores; it left 12 true pairs that are 0.67 to 0.69 higher, which
  the second limit takes back.
- The two small rules. A heavy print sets two heads a third apart on one stem as one blot. The rows cut parts
  them, and then the lower head was named a flat, because the head over it looks like the stroke of a flat. A
  filled mark of the size of a head with a head of its width right over it, in a blot of these two marks only,
  is a head now. Without the last condition the rule made a note of a piece of the heavy end bar of a hymn. And
  where the stem of such a pair is found again only by the rule for lost stems, the stemless mark of the same
  blot shares it.
- The rule that is off. A stemless mark of the size of a head that touches a head takes the stem that runs
  through both. Three forms were counted, and each loses on the clean copies or on all scores: the first gained
  24 and lost 34 on all scores (the flag of an eighth drawn by hand, sharps, quarter rests, the sign of cut
  time and two whole notes that touch became notes with stems), the second lost about as many, and the third,
  for a blot of two marks only, gains 1 and loses 2 on the clean copies, gains 11 and loses 5 on all scores and
  writes 31 more notes that are not there.
- What the round loses. One note on all scores: a blot that the page prints like a second where the typed hymn
  has a unison. Counted staff by staff, 5 notes are lost on all scores beside 110 gained; they were not traced.
  The words did not change (24,200 syllables right on all scores, 5,780 on the clean copies). The kit gained 13
  notes (6159 to 6172). The figures of this round are of its time.
- Seen in this round and not solved: the first note of a line that stands close against the key signature and
  is cut away with it, a whole note on a ledger line whose sides the print made fat (two small marks and no
  head), two whole notes a third apart that touch and look like an 8, a head under a faint ledger line, and
  one heavy print whose half notes have nearly closed holes and are read as quarters (44 notes are missing for
  99 % of that score).
- Thirteen rounds before: the count itself, and a third voice on a staff. The round before that one wrote a rule
  that reads two notes on two stems side by side as notes that begin together, and the count of parts hid what
  the rule does. Since this round every typed note of a part is counted, and the rule is on.

  | The same reading, before the rule | One note of a chord for each part (as before) | Every typed note of a chord (from now on) |
  |---|---:|---:|
  | Clean copies | 94.7 % (21,110 of 22,293), 14 scores at 99 %, 48 at 95 % | 94.6 % (21,377 of 22,586), 14 at 99 %, 46 at 95 % |
  | All of LitChoir | 85.1 % (75,898 of 89,147), 68 at 99 % | 85.2 % (76,448 of 89,756), 68 at 99 % |
  | Fresh test set | 94.2 % (38,548 of 40,906), 79 pieces at 99 % | 94.6 % (39,491 of 41,761), 83 at 99 % |

  No score has fewer notes right by the new count. The clean copies have 293 more typed notes in the count and
  267 more notes right, so their share falls a little.

  | The rule for a third voice, alone | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | Notes gained, lost, by the new count of parts | 7, 2 | 43, 30 | 8, 5 |
  | Notes gained, lost, staff by staff | 57, 2 | 153, 40 | 95, 0 |
  | Notes that are not there | 1,172 to 1,099 | 6,389 to 6,072 | 5,607 to 5,486 |

  With the rule the clean copies are at 94.7 % (21,382 of 22,585; 14 scores at 99 %, 46 at 95 %, 70 at 90 %), all
  scores at 85.2 % (76,461 of 89,747) and the fresh test set at 94.6 % (39,494 of 41,761; 83 pieces at 99 %).
- How the new count works. The line-up of a part stays as it was: on a staff of two parts the top note of each
  typed chord of the upper part and the bottom note of the lower part are lined up with the reader's notes of
  that part. After it, each other typed note of a chord is counted. It is right when the reader has its pitch and
  length at the moment of the note of its chord that was lined up: as a note of the staff that the split gave to
  no part, as a note that the other part of the staff has too (one head for two parts, as a unison is), as a
  note of the part that stands beside it and was lined up with no typed note, or as the note that was lined up
  with the other note of the chord and is not its like. It is counted apart when its chord is (a recited chord
  that the page draws once), and it is a missed note otherwise. Two more cases follow from the notes that no
  part takes. A false note that took the place of a true one: a typed note is lined up with a note of another
  pitch or length, and the staff has the typed pitch and length at that same moment. The typed note is right
  then, and the note that was lined up is a note that is not there. And a note of a staff that no part takes
  and that stands for no typed note was not counted at all: it is a note that is not there now. A score whose
  pages are laid out one by one gets the same notes for its parts.
- What the new count adds, on the same reading. Clean copies: 289 typed notes of chords on staves of two parts
  (221 of them right), 31 true notes whose place a false note had taken, 21 notes of chords on pages that are
  laid out one by one, and 75 notes that no part takes and that are not there (the notes that are not there go
  from 1,082 to 1,172). All scores: 609 more typed notes, 550 more notes right. Fresh test set: 855 typed notes
  of chords, 829 right; 451 of them are heads that two voices share.
- The rule for a third voice. Two notes of one voice, each on its own stem, with their heads at most 0.6 staff
  spaces apart along the staff, begin together: a part that divides with a stem for each note, or the basses in
  octaves under the tenors. One cannot follow the other there, since a note that follows stands a head's width
  or more after it. Before, the second note began after the first, the bar grew too long, and every note after
  it stood at a later moment than the notes of the other staves.
- What the rule loses. On the clean copies 2 notes in one score, at one chord under a fermata whose two notes
  begin together now. On all scores 30 notes in 14 scores. Looked at on the page: in three scores (11 notes) the
  notes that the rule sets together do sound together (a divided soprano with a stem for each note, two voices a
  second apart), and the page-by-page layout of the scorer gives one of them to another part. In one score a
  false dot stays that the agreement of the staves took away before: the column of the two notes moved a little
  and is no longer set beside the column of the other staff. The other 16 notes were not traced. On the fresh test set 5 notes in three pieces; they were not looked at, as no rule may be set there.
- The words. The words that are read did not change (the clean copies stay at 5,780 of 6,240). 17 fewer
  syllables are counted right on the other scans: 9 in 4 scores that the new count sets in the other layout
  (page by page, or as a whole), and 8 in one score whose typed hymn covers a part of its twelve pages, where
  the scorer picks another part of the pages with the rule on.
- Limits of the new count. One head can stand for a typed note of each of two parts, as a unison always did.
  The line-up still compares the notes of a part in their order and not their moments, so a note at a wrong
  moment costs nothing by itself; counted staff by staff, where the notes of two parts are one row in the order
  of their moments, the rule gains far more than by parts. The kit's own scorer, which compares the reader with
  the network on 31 hymns, counts as before: there the rule costs 3 notes (6159, from 6162).
- Fourteen rounds before: notes of the clean copies with a wrong pitch. Six rules were written. Four stand, and two are
  switched off with their counts. The clean copies stay at 94.7 % of the notes (5 gained, none lost: 21,110 of
  22,293; 14 scores at 99 % and 48 at 95 % as before) and have 8 fewer notes that are not there (1,082, from 1,090).
  All scores stay at 85.1 % (14 gained, none lost: 75,898 of 89,147). The fresh test set has 38,548 of 40,906
  notes (38,547 before; 1 gained and none lost by the scorer's count). The words did not change. The gain
  is small because three of the four rules mend one faint engraving and a few heavy sharps; the larger cause
  that the round found, a third voice on a staff, is read right now by a rule that the count of parts cannot
  show, and that rule waits switched off.

  | Rule | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | The sharp of a faint print, of which only the two bars are left | 5, 0 | 5, 0 | 0, 0 |
  | The bar line of a faint print, broken into dashes | 4, 0 | 4, 0 | 0, 0 |
  | The two strokes of a heavy sharp that touch are a pair | 0, 0 | 3, 0 | 0, 0 |
  | The closed middle of a sharp is no head when its stems are the sharp's strokes | 0, 0 | 7, 0 | 1, 0 |
  | Off: a head at the border of two places takes the place of the middle of its ink | 8, 0 | 28, 10 | 0, 6 |
  | Off: two notes of one voice on two stems close together begin together | 5, 7 | 37, 53 | 7, 20 |

  Notes gained, notes lost, by the count of parts. Each rule that stands was switched off alone in the final code,
  on the pages that the round changes, in runs without the words (the full run with the words gains 14 on all
  scores). The 4 notes of the faint bar line are among the 5 of the faded sharp: without the bar line a sharp that
  is read now would hold through the next bar. Each rule that is off was switched on alone.
- How the round began. The scorer's own comparison lines up 414 notes of the clean copies with a typed note of
  another pitch. 229 of them are one place or one sign off: 112 a semitone and 117 a whole tone. They were sorted
  by what the page shows at the note: a sign that is not read, a sign that is not there, a head that is measured
  at the border of two places, and a note of a chord that begins at the wrong moment and so is compared with
  another note.
- The faded sharp. One faint engraving prints its sharps so weakly that the two upright strokes are gone. The two
  slanting bars are left, as two small marks of one width, one over the other, before the head. The reader found
  no sign there, or read one bar as a small note. The rule: two such marks in the room before a head, the head at
  the height of the paper between them, each mark thin (the middle one of its columns holds at most 0.47 staff
  spaces of ink; a bar has 0.42 at most and a head 0.52 or more), and at most one of them read as a note.
- The faded sharp was narrowed twice. Its first form lost 167 notes for 1: the two heads of a chord a third apart
  were its two bars. The thickness of the marks ended that. Then two thin marks on one stem were taken, the worn
  heads of a chord: a mark with a stem is no bar. The first form of that guard (the mark touches the layer of
  the upright strokes) took 6 true sharps away, because the stubs that are left of a faded stroke lie in that
  layer. Now no column of the sign's box may hold a piece of a stem 0.9 staff spaces long: the stubs are 0.58 at
  most, and the stem of the worn chord is 1.18. That limit stands between one case at each side, on one score.
- The faint bar line. The same print breaks its bar lines into dashes, and the reader found none. A sharp then
  held through the next bar: with the faded sharps read, 4 notes after them were a semitone too high. The rule: an
  upright line with ink in 0.38 of the rows of the staff, bare paper at both sides (a stem has its head there),
  no stem and no head on it, and on at least half of the other staves of its system a bar line or such a line at
  the same place. Its first form made bar lines of the crease of a page and of a dotted guide line (2 notes
  lost). A bar line goes on toward the next staff of its system (ink in 0.38 or more of the rows from 1 to 4 staff
  spaces past the staff); the crease and the dotted line have none there. The limit is 0.3.
- The heavy sharp. Where the bars of a heavy sharp fill the room between its two strokes, the strokes touch, and
  the test for a pair had no column between them to look at: two strokes that touch are a pair now (3 notes on
  all scores). The first form lost 2 notes on one page, where a heavy stem through a head on a ledger line was
  cut in two strokes that touch: a touching pair that lies on a full head is no sign. And the closed middle of a
  heavy sharp, which was read as a hollow head with one of the strokes as its stem, was dropped only up to a
  size: now it is no head at any size when its middle lies between the two strokes and each of its stems is one
  of them (7 notes on all scores, 1 on the fresh test set).
- Off: the head at the border of two places. A head whose middle is measured 0.35 of a place or more from the
  middle of its place would take the place of the middle of all its ink, when that lies clearly in the next
  place. On LitChoir it gains 8 notes on the clean copies and loses none (28 and 10 on all scores). On the fresh
  test set it gains nothing and loses 6 notes in one piece (an E flat read as D). A count of every such head of
  the scans shows no measure that tells the mended heads from the broken ones, so the rule is off.
- Off: the third voice. Where a staff holds three voices (the basses in octaves under the tenors), two notes of
  one voice stand on two stems close together, and the reader let the second begin after the first. With the
  rule, two notes of one voice on two stems at most 0.6 staff spaces apart begin together. Counted staff by staff
  against all typed notes of the staff, the rule gains 51 notes on the clean copies and loses 3 (144 and 44 on all
  scores), and on the fresh test set, whose answers are exact, 95 and none. Counted part by part, as every figure of this
  project is, it loses more than it gains (see the table). The cause is the count, not the reading: the count
  keeps one note of a chord for each part, the third note is not counted, and where the chord also holds a false
  note, that note now takes the true note's place. The rule was off until the count of parts held such chords
  (the round after this one). Three mends of the count were tried and
  taken back: the whole chord to its part (29 gained, 19 lost on the clean copies: the added notes upset the
  line-up of the part), a typed chord note credited when the reader has it at the same moment (36 gained, but
  scores then turn to another layout of their staves and their totals grow), and a part that is holding its note
  (0 and 8).
- Not solved: whole notes on a staff line whose hole a heavy print nearly closed (2 clear cases; the hole is 0.03
  of the head against a limit of 0.04), heavy sharps that are one blot (three pages), the upper head of two
  touching heads a second apart, the middle of a sharp read as a head with the true stem of its note, and false
  notes inside chords.
- Fifteen rounds before: long notes of the clean copies that are read in two parts, because their tie is not read. Two
  rules stand. The clean copies went from 94.6 % to 94.7 % of the notes (10 gained, none lost: 21,105 of 22,293;
  14 scores at 99 % and 48 at 95 % as before) and have 36 fewer notes that are not there (1,090, from 1,126). All
  scores stay at 85.1 % (17 gained, 2 lost: 75,884 of 89,147). The fresh test set has 38,547 of 40,906 notes
  (38,539 before; 19 gained and 11 lost by the scorer's count), 79 pieces at 99 % (78 before) and 97 fewer notes
  that are not there. One syllable more is right on a copy by hand; the other words did not change.

  | Rule | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | The paper that a tie closes in at a bar line is no note | 5, 0 | 11, 1 | 6, 7 |
  | A chord is tied note by note | 5, 0 | 6, 1 | 13, 4 |

- How the round began. The scorer's own comparison shows 45 ties of the clean copies that are not read: the typed
  note is long, and the reader has its first part and a second note of the same pitch. By cause: 11 ties are read
  but their notes are not joined, because a false note or a false dot in the bar moves the second note away from
  the end of the first. About 20 bows are not found: the tie is one piece of ink with a slur under it, it lies
  in a staff line and too little of it is seen, or it ends at the top of a stem. 8 go over the end of a line,
  two of them over a page break, and most of the others lie in a staff line. In two places the search stopped at
  the other head of a tied chord.
- The first rule. Where a tie crosses a bar line, the tie, the bar line and a staff line close in a little paper.
  The reader took it for a low hollow head with the bar line as its stem: a half note that is not there, and a
  bar line lost. In one hymn two ties cross each bar line, and the false half note between them kept both ties
  from being joined. Such a mark is at most 0.7 times as high as the heads of its page, it lies in the staff,
  the column of its stem has ink in 0.9 of the rows from the top line of the staff to the bottom line, and the
  line goes on above the mark and below it. A stem ends at its head. Counted on every scan: 33 of 11,385 hollow
  notes with one stem are that low on a line through the whole staff. Half a staff space past the head a stem has
  no ink, and a line that goes on has ink in 0.64 of the rows or more; the limit is 0.5. The mark is no head,
  and its line is a bar line.
- The first rule was narrowed three times. Its first form (13 gained, 4 lost on all scores; 5 and 3 on the clean
  copies) took a true half note under the staff of a copy by hand, whose stem crosses the whole staff: the mark
  must lie in the staff, and the line must go on at both sides. A guard that the mark lies a staff space inside
  the staff lost 7 of the gained notes with it (6 gained, 2 lost) and was dropped for the count of the ink at
  both sides. Then a clean copy lost a half note that has the head of the other voice a third under it, on one
  line with its stem: the rows of another head do not count as ink of the line. On the fresh test set the rule
  lost 10 notes for 6 at first. There the loop of a flag closes in paper at the stem of an eighth note, the false
  head went as it should, but the stem became a bar line, and the sharp of the bar ended there (5 notes of two
  pieces, counted staff by staff). The line is a bar line now only where no head stands on it. LitChoir has such
  a loop on one page, with no false bar line; the guard was tried on the two fresh pages that showed the mistake,
  so for this guard those pages are no longer unseen.
- What the first rule loses. On LitChoir one half note of a heavy copy, whose stem runs through the whole staff
  and past its head to a second head. On the fresh test set the scorer counts 6 gained and 7 lost. Of the 7, 5 are
  in one piece whose staves read 2 more notes right than before (a tie over a bar line is joined now): the
  scorer lines the parts of that piece up in another way. Counted staff by staff, the rule gains 4 notes there
  and loses 2. Those 2 are a bow between two equal notes over a bar line, which the answer writes as a slur: the
  false head had stood between the two notes and kept the bow from being read as a tie.
- The second rule. A tied chord is tied note by note. The search for the second head of a tie stopped at any
  head of the same voice between the two, and the other head of the second chord can stand a little before the
  head that is looked for: chords of whole notes have no stem that holds their heads in one column. A head whose
  middle is at most a staff space from the middle of the second head, and that is of its voice, is not between
  the two now.
- The second rule was narrowed once. Its first form did not ask for the voice (8 gained, 7 lost on all scores; 6
  and 2 on the clean copies): it tied the tenor's note to the same note of the bass under the bass's slur.
- What the second rule loses. On LitChoir one note of a heavy copy: the numbers of a time signature in the
  middle of a line are read as a chord there, and a tie along a staff line is found to it. On the fresh test set
  4 notes, two bows from a note to the same note in the next chord that the answer writes as slurs.
- Counted and dropped: whole notes that are read as half notes by a false stem at the middle of the head (two
  whole notes on ledger lines over each other). 872 hollow heads of the scans have a stem near the middle. A
  stem within 0.15 staff spaces of the middle and at most a staff space of slim ink: 4 gained, 2 lost on the
  clean copies, 22 and 22 on the other scans.
- Not solved: the bows that are not found (about 20, each cause 1 to 4 ties), the ties over the end of a line
  whose bow lies in a staff line, and a false dot on one whole note of a tied chord, which makes its bar too long.
- Sixteen rounds before: the lengths of the notes of the clean copies. Seven ideas were counted and one rule stands. The
  clean copies stay at 94.6 % of the notes (8 gained, none lost: 21,095 of 22,293; 14 scores at 99 % as before, 48
  at 95 %, 47 before), all scores at 85.1 % (16 gained, 2 lost), and the fresh test set does not change: none of
  its pages reads differently. The words did not change.

  | Rule | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A thin beam that leaves a stem before the end that was found for it | 8, 0 | 16, 2 | 0, 0 |

- The rule. A fine engraving draws a slur that begins at the end of a stem. The reader follows the ink of the stem
  into the slur, so the end that it finds lies up to a staff space past the place where the beam leaves the stem.
  The rule for a thin beam looked for straight ink from the end of one stem to the end of the next and found the
  slur or nothing: the eighths were quarters. It tries first now the long ink that hangs on the stem at the side
  of the other stem, 0.35 to 1.3 staff spaces before the found end and at least a staff space long. The look past
  the last stem of a run (a beam ends there, a slur goes on) starts at that ink too.
- The rule was narrowed twice. The first form gained 23 notes and lost 3 by the scorer's count. One lost note was
  a quarter under a slur that begins at the side of a stem: that slur is 0.22 staff spaces thick on a page whose
  beams are 0.56 thick, and the true beams at the side of a stem have 0.63 of their page's beam or more. Where
  the page shows the thickness of its beams, the ink at the side must have half of it. Then 7 of the gained
  notes, all in one hymn of a copy by hand, were looked at on the page, and the reading there was wrong: the flag
  of a stem touches the next stem 0.8 staff spaces away, the two stems were joined by a line that rises 3 for
  each step to the side, and the rule for a slur between two stems then took both flags off. The scorer counted
  7 more notes right all the same, because it lined the parts up in another way and set 3 typed notes apart.
  Counted staff by staff, that hymn had lost 2 notes. A beam at the side of a stem may rise or fall 0.6 for each
  step to the side now; the hymn reads as before the round, and the 7 notes are no gain.
- The 2 notes that are lost stand on one copy by hand, where a pencil stroke crosses a stem (the reader has 58 of
  that score's 393 notes).
- Counted and dropped, the slur that arcs over the ends of two stems (the round before counted it on the clean
  copies and found a border). On all 516 scan pages the thin-beam rule joins 4,039 stems that line up with a typed
  note. By the bend of the ink alone, at 0.4 staff spaces or more: 4 true eighths against 3 quarters on the clean
  copies, 20 against 13 on the other scans. With the share of the ink that lies on the straight line as well: 2
  gained and none lost on the clean copies, 2 and 2 on the others. The border of the first count was too few
  places.
- Counted and dropped, a beam that hangs alone at its own height while a slur hangs at the stem's end: 4 gained,
  5 lost on every page.
- Counted and no rule: dotted half notes read as half notes (33). Of 116 dots that are missed on the clean copies,
  95 have no free ink beside the head: a tie is not read there, or the typed hymn differs from the page. Dots
  drawn as dashes fail on one page only.
- Counted and no rule yet: filled heads that faded and are read as hollow (about 110 on the clean copies, 38 of
  them in one faint engraving that has 273 true hollow heads). A hollow head with a flag or a beam as an eighth:
  15 gained, 19 lost on the clean copies. The light of the head's middle against the page's usual light, alone and
  with the size of the hole: 19 gained and 8 lost on the clean copies at best, 14 and 16 on the other scans. A
  hollow and a filled head on one stem (184 stems): 7 gained, 2 lost on the clean copies, about even on the others.
- Counted and no rule: half notes read as quarters (38). Most are filled on the page: a tie or a typed hymn that
  differs. On the worn pages, where the limit of a hollow head is raised, 2 could be gained for 3 lost. And
  missed ties: 17 notes whose second half is read as a note of its own, 15 at the end of a staff (a later round
  counted the ties from the scorer's own comparison and found 45).
- A caution from that round: a gain on a copy by hand is checked staff by staff on the scorer's comparison before
  it is counted.
- Seventeen rounds before: the sharps, flats and naturals before the notes of the clean copies, with four rules. The
  clean copies went from 94.5 % to 94.6 % of the notes (29 gained, none lost; 14 scores at 99 % as before, 47 at
  95 %, 46 before), all scores from 85.0 % to 85.1 % (44 gained, none lost), the fresh test set from 93.7 % to
  94.2 % (208 gained, 1 lost). The words did not change. Each rule was counted alone, switched off with the
  others on, on the pages that the round changes (notes gained and lost by the rule):

  | Rule | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A flat or a natural that stands against a bar line | 14, 0 | 14, 0 | 0, 0 |
  | A tall natural | 13, 0 | 26, 0 | 208, 1 |
  | A natural with nearly level strokes is no sharp | 1, 0 | 2, 0 | 0, 0 |
  | A natural with broad strokes | 2, 0 | 3, 0 | 0, 0 |
  | All four together | 29, 0 | 44, 0 | 208, 1 |

  One note needs two of the rules, so the rows add up to one more than the last row.
- How that round began. Of the 1,235 notes that were lost on the clean copies, 486 had a wrong length only, 346 a
  wrong pitch only (118 of them a semitone off), 108 both, and about 300 were not read. 36 of the notes a
  semitone off were drawn by lot and looked at on their pages.
- The sign against a bar line. An engraver can set the flat or the natural of the first note of a bar so close
  to the bar line that the two are one piece of ink. The box of the natural or the bowl of the flat was then a
  small hollow head and the bar line its stem: a half note that is not there, a bar line lost, and the note after
  it without its sign. What tells it: a stem begins at its head, and this line goes through from the top line of
  the staff to the bottom line; the mark is at most 0.8 times as wide as the heads of the page; and a head of
  full width follows within 0.6 staff spaces at the same place. With a slim stroke that goes on 0.4 staff spaces
  under the mark it is a natural, without one a flat. The first form took a stroke of a letter in the words under
  the staff for the stroke of the natural; the stroke must begin over the middle of the mark. All 14 notes
  stand in one hymn.
- The tall natural. The two strokes of a natural had to stand side by side for at most 1.5 staff spaces. A count
  of every pair of strokes before a note on the clean copies (22,721 read notes with their typed pitch) has 6
  pairs between 1.51 and 1.85, and all 6 are naturals in the typed hymn. The limit is 1.9 now. On the fresh test
  set this rule is the whole gain: its engraved pages draw the natural taller than most of LitChoir's prints.
- The natural that was read as a sharp. A heavy print draws the natural with a high box and short free ends, so
  its two strokes are nearly level, as the strokes of a sharp are. The count: 37 true sharps have a right stroke
  that begins and ends within 0.04 staff spaces of the left one; the 5 naturals that were read as sharps have a
  right stroke that begins 0.22 staff spaces lower or more and does not end higher, and no ink sticks out at the
  left of the left stroke, as the bars of a sharp do. The first form stood before the test for a flat and turned
  10 flats into naturals (41 gained, 10 lost on the pages that changed); it stands after that test now, and loses
  none. Only 2 notes are gained by this rule alone: the others are also read by the tall natural, or stay wrong
  for another cause.
- The natural with broad strokes. A stroke of a flat or a natural could be 0.45 staff spaces wide, so that the
  rim of a large hollow head is no flat. A small heavy print has naturals with strokes of 0.46 and 0.47; a
  natural may have strokes of 0.5 now, a flat as before. This limit stands on few places: one pair of strokes
  0.52 wide in the same print is a flat.
- The one note lost on the fresh test set. A natural was read as an eighth note before the round and is read as
  a natural now, which is right. A half note in the staff under it is read as a quarter since then; the letters
  "mf" under that staff are read as a thin head in the same bar. The rule was kept: it gains 208 notes there, and
  the cause of the lost one is not the natural. It is on the list below, to be worked on with LitChoir's pages.
- Looked at and no rule: about 40 notes of three clean hymns are a place off where a ledger line stands over the
  bass staff. A count of 1,640 filled heads with one ledger line shows two groups that do not meet: a head on the
  line reaches 0.2 staff spaces before it to 0.15 past it, a head that sits on the line 0.2 to 0.5 past it. The
  wrong notes lie inside their group: the reader reads what the page draws, and the typed hymn has another note.
- Counted in that round for the next: 46 quarters of the clean copies are read as eighths. Some have a beam on the page
  (the typed hymn differs). Others have a slur that arcs over the ends of two stems and is taken for a thin
  beam. A count of the 61 pairs of stems that the thin-beam rule joins on the clean copies: the ink between true
  eighths leaves the straight line by 0.19 staff spaces at most (three pairs aside, where the ink was followed
  far past the next stem), the slurs over quarters by 0.48 to 0.65.
- Seen in that round and not solved: the sharp of a sloppy print that is read as a head; a flat glued to its
  head; the sharps of one faint engraving; a sharp before two heads a second apart that is given to the wrong
  head (4 notes); the letters of a dynamic mark under a staff read as a thin head.
- Eighteen rounds before: the notes of the clean copies again, with four rules for lengths that were read wrongly. The
  clean copies went from 94.3 % to 94.5 % of the notes (28 gained, none lost; 14 scores at 99 % as before, 46 at
  95 %, 44 before), all scores from 84.8 % to 85.0 % (203 gained, none lost), the fresh test set from 93.3 % to
  93.7 % (157 gained, none lost). The words did not change. Most of the gain stands on one thick copy
  (two scans of one hymn, 167 notes): its slurs from stem to stem were read as beams. Each rule was counted alone,
  switched off with the others on, on the pages that the round changes (notes gained and lost by the rule):

  | Rule | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | The flag of a stem down that is drawn as a bow | 11, 0 | 16, 0 | 157, 0 |
  | The bow of such a flag is no head | 7, 0 | 7, 0 | 7, 0 |
  | A slur between the ends of two stems is no beam | 10, 0 | 179, 0 | 0, 0 |
  | A whole note a third from a note with a stem | 7, 0 | 8, 0 | 0, 0 |
  | All four together | 28, 0 | 203, 0 | 157, 0 |

  The second rule works only where the first found a bow, so the count of the first holds the count of the second.
- How that round began. The lost notes of the clean copies were sorted by the typed and the read length: 504 had a
  wrong length only, and of these 71 are an eighth read as a quarter, 54 a quarter read as an eighth, 38 a half
  read as a quarter and 38 the other way, 33 a dotted half read as a half and 26 a whole note read as a half.
  Each kind was looked at on the pages, with a sheet of its places.
- The bow. Some engravers draw the flag of an eighth with its stem down as a bow: it leaves the head or the
  stem beside it, bulges to the right and comes back to the stem before its end. The flag rule looked for a hook
  that leaves the end of the stem, and found none. Now, where a stem down has no flag and no beam, the ink at
  its right side is looked at from under the head to the end: a piece that touches the stem, is 1.8 staff spaces
  high or more, reaches 0.7 to 1.3 staff spaces from the stem and has paper between itself and the stem is a
  flag. The count before the rule: 10 stems of the clean copies have such a bow and no flag, and all 10 are an
  eighth in the typed hymn.
- The bow as a head. The bow is thin ink around paper, as a hollow head by hand is, and the search for thin
  heads from a stem found a head in it. Such a thin head at the right of a stem whose flag is a bow, in the far
  half of that stem, is the bow. The first form took a thin head beside any stem with a flag or a beam and took
  4 real heads away. The second form (a stem with a bow, anywhere under the head) gained 9 notes and lost 1: the
  lower head of two eighths a third apart, which the thick marks show as one. A count of the 10 places told
  them apart: the 7 bows lie 2.5 to 2.7 staff spaces under the head and 1 from the end of the stem, the 3 real
  heads 1.0 to 1.3 under the head. With the far half the rule gains 7 and loses none; 2 of the 9 notes were such
  real heads taken away, whose note is read wrongly either way.
- The slur. On a page without thick beams, slim straight ink from the end of one stem to the end of the next is
  a beam. A slur that an engraver sets from stem end to stem end is such ink, and two quarters were read as
  eighths. What tells the slur: it meets each stem in a curve, so both stems bend toward each other at their ends
  (0.2 staff spaces each, and they turn there), the stroke is thin (0.4 staff spaces at most), and its outer edge
  is round at both stems, where a beam has square corners. The first form asked for the bend and a stroke under
  0.3 staff spaces: 166 gained, 5 lost, thin beams by hand whose stems lean toward each other. The turn of the
  stems tells those apart: a leaning stem is straight. A limit of 0.4 for the heavy copy then lost square beams
  0.32 to 0.39 thick on three pages, and the round ends were added. The count before the last form: on the
  clean copies it finds 8 pairs, all longer than an eighth in the typed hymn.
- The whole note. A whole note a third over or under a note with a stem stands close beside that stem, and the
  stem was given to the oval: a half note. The rule for an oval that touches the other head was there; now the
  two may be 0.7 staff spaces apart when the oval is wider than the head, the stem stands inside the oval's
  width and paper lies between the oval and the stem. The first form lost 3 notes on a copy by hand whose heads
  are split in small pieces; the head with the stem must be as wide as the heads of the page.
- Seen in that round and not solved: thin beams of a fine engraving where the stem is followed over a gap to a
  slur, so that the beam lies a staff space before the found end (19 eighths read as quarters in one hymn);
  quarter heads that faded and look hollow (22 in one hymn); half notes whose hole is nearly filled (three scans
  of one hymn); a dot drawn as a slanted dash; a deep slur at one stem that is counted as a beam; a beam and a
  slur that are counted as two beams; the short second beam of a sixteenth; two eighths a third apart with
  their flags, which are one blot (the upper head gets the lower stem); a final bar line read as a note.
- Nineteen rounds before: the notes of the clean copies, with three rules. The clean copies went from 94.2 % to 94.3 %
  of the notes (31 gained, 1 lost; 14 scores at 99 %, 12 before), all scores from 84.7 % to 84.8 % (118 gained, 16
  lost), the fresh test set from 93.2 % to 93.3 % (50 gained, 2 lost). The words did not change, but for 3
  syllables of one copy by hand whose notes moved. Each rule was counted alone, switched off with the others on,
  on the pages that the round changes (notes gained and lost by the rule):

  | Rule | Clean copies | All of LitChoir | Fresh test set |
  |---|---:|---:|---:|
  | A staff line that is faint inside a hollow head | 8, 0 | 57, 7 | 0, 0 |
  | A hollow head with a thin rim whose inside shows when a small break is closed | 5, 1 | 24, 12 | 0, 0 |
  | A beam that goes on past a stem is one beam | 15, 0 | 35, 0 | 50, 2 |
  | All three together | 31, 1 | 118, 16 | 50, 2 |

- How that round began. The 1,299 lost notes of the clean copies were sorted with a new tool, which takes each
  mistake from the scorer's own comparison and finds its note on the page: 528 had a wrong length only, 347 a
  wrong pitch only, 110 both, and about 310 were not read. Of the wrong pitches 139 are a semitone off (a sharp, a
  flat or a natural) and 123 a step. The vote of the voices on a length is nearly used up: 129 of the wrong lengths
  have no other voice to vote, and about 100 are wrong in every voice alike.
- The faint line. A hollow head on a staff line has its inside cut in two by the line, and the layers join the
  two pieces. But a copy can leave the line faint inside the head: its ink comes in from both sides and does not
  meet. The inside is then one piece of paper with a neck, the neck is a dent, and paper with a dent was no hole:
  the head was found later as a thin stroke and read as filled. Now the neck is filled where a staff line runs,
  when a part of the paper lies over the line and a part under it, and the piece counts when it is round with
  that. The first form filled a neck anywhere: it gained 136 notes and lost 110, because the paper between two
  staff lines beside a stem or in a clef has such necks on copies by hand.
- The thin rim. A printed half note with a thin rim is found from its stem, as a thin piece of ink, and it is
  hollow when its ink goes around paper. That was measured after closing the breaks of the rim with a wide
  brush, which also fills a narrow inside. Now the open holes of the layers count too (paper that is closed in
  when a break of a fifth of a staff space is closed): the pieces over and under a line are taken together, and
  they must be as large as the inside of a head and have the head's own ink around them. The head keeps the place
  that its ink gave it. The first form took any such paper in the box of the piece: 26 gained, 20 lost on copies
  by hand, where the paper between a slanted stroke, its stem and a staff line is closed in too. The narrowed
  form still loses 12 notes for 24 on all scores, one or two a score on copies by hand.
- The beam. A beam that goes on past a stem is one piece of ink at each side of the stem. Two pieces more than
  0.35 staff spaces apart were two beams; a slanted or fat beam has its two pieces that far apart, and an eighth
  note was read as a sixteenth. Now a piece at the left and a piece at the right are one beam when they lie less
  than four fifths of the beam's thickness apart: two beams lie a thickness and a gap apart. The count before
  the rule: of the stems with two such pieces 0.35 to 0.45 staff spaces apart, 14 are an eighth in the typed
  hymn and 1 a sixteenth on the clean copies, 46 and 4 on all scans.
- Measured and switched off: paper that a slur closes in with a stem and a staff line. Filled as a hole, it is a
  thick mark that hides the stem, and the real head beside it loses its stem (two eighths read as quarters in
  one clean score that lacks one note to 99 %). The rule took a hole 2.5 times as large as the usual hole of the
  page for such paper and read the page again without it. It gained 87 notes and lost 229: a page has two usual
  holes, the small one of its half notes and the large one of its whole notes, 5 to 9 times apart in a thick
  print, and a clef closes in large paper too. Counted by the largest piece of paper of each head and only after
  the clefs, it gained 65 and lost 271. The size alone does not tell such paper; the switch (`HOLE_BIG`) says so.
- Seen in that round and not solved: a tied chord after a bar line that is one blot with the end of its tie
  (the Lord's Prayer, 4 times); the end of a tie that closes in paper at a head with its stem down and is read as
  a flag; a dot of the lower voice that is given to the head over it; plain eighths read as a triplet; 236 single
  notes that are not read, with no one cause.
- Twenty rounds before: the words with Tesseract again, six rules with the list of words and no note rule. The clean
  copies went from 90.6 % to 92.6 % of the syllables (131 gained, 2 lost) and from 89.6 % to 90.8 % of the
  whole words (57 gained, none lost); all scores from 82.7 % to 84.4 % (510 gained, 9 lost). No note
  changed. Each rule was counted alone, switched off with all others on (syllables gained and lost by the rule):

  | Rule | Clean copies | All scan pages | Fresh test set |
  |---|---:|---:|---:|
  | The list parts a word into syllables where the scan shows no hyphen | 67 and 3 | 203 and 4 | 493 and 0 |
  | A short word that Tesseract is not sure of stays when the list holds it | 27 and 0 | 94 and 10 | 8 and 0 |
  | A 0 or a 1 among letters is the letter that it stands for | 19 and 0 | 164 and 0 | 10 and 2 |
  | A row that Tesseract is not sure of stays when the list holds its words | 21 and 0 | 68 and 1 | 0 and 0 |
  | A word of one letter and a word that were read as one are parted ("odrink") | 6 and 0 | 14 and 6 | 31 and 1 |
  | Three words that were read as one are parted ("mercyonus") | 6 and 0 | 11 and 6 | 20 and 1 |
  | All six together | 136 and 2 | 516 and 10 | 560 and 2 |
  | the same, in whole words | 68 and 1 | 311 and 4 | 64 and 3 |

  A quick count as in the round before it, made from the stored rows.
- The largest of the six is the parting into syllables. An engraver sets "mercy" whole under two notes where the
  syllables stand close, and a scan loses thin hyphens: the letters were right and the syllables were not. The
  list of words is made from typed hymns, which write each word in its syllables ("mer-cy"), so the list knows
  how a word is parted. A word that was read in fewer syllables than the list parts it into is parted the list's
  way, when the list parts it so in half of the times or more. It never joins syllables that the page parts. What
  it loses: a word that this hymn sings on fewer notes than most hymns do ("glo-rious" in two, "bless-ed" in
  one): 3 syllables on the clean copies, 4 on all scan pages, none on the fresh set. The limit was set on LitChoir's pages (a stricter one, twice or more and in three fifths of the
  times, gained 62 on the clean copies where this one gains 67, with the same 3 lost).
- What the full runs showed that the quick count could not. The quick count reads one row for each staff; where
  stray ink over the real row is taken for a row of words, it hides the real row in every state, so a rule that
  lets such a row through looks free. The first form of the row rule counted every word of the list, and stray
  ink that Tesseract read as "a nus Me a t i le We" passed, because the list holds a, me, i and we: one clean
  score lost 9 syllables in the full run. Only words of three letters or more count now (68 gained on the scan
  pages in place of 84, and the 9 are back).
- What the two cuts by the list lose, and how they were narrowed. A list holds stray letters too (a "t" and a "w"
  from typed hymns), and with them the cut made "t her" and "t able": a word of one letter counts only when it is
  one word in a thousand of the list or more (o, a, I). Three words in one were cut wrongly at first ("inherit"
  into "in her it", "beareth" into "be are th"), since a list also holds rare short pieces: each of the three
  must be a common word of the list, a short one a very common one. On the fresh set an English list cut
  Romanian words (whole words 20 gained, 38 lost by the cut into three): both cuts are made only on a page whose
  language the list holds, the test that the mending by the list already used. On LitChoir's pages that test
  changes two syllables, one for the better (a Spanish hymn) and one for the worse (an Arabic one).
- Twenty-one rounds before: the words with Tesseract. Five rules of our own stand around Tesseract since then, three of them with
  the list of words, and one new note rule. Each word rule was counted alone, switched off with all others on, on
  the clean copies, on all 482 scan pages and on the fresh test set (syllables gained and lost by the rule):

  | Rule | Clean copies | All scan pages | Fresh test set |
  |---|---:|---:|---:|
  | Two words that Tesseract read as one are cut at a wide gap | 41 and 5 | 60 and 36 | 1,029 and 1 |
  | The lines of held syllables are taken out of the row (counted at one size) | 56 and 9 | 115 and 21 | 3 and 0 |
  | A second look: the row is read at two more sizes and the best reading stays | 118 and 5 | 734 and 23 | 109 and 29 |
  | The list sets where a word ends | 34 and 9 | 99 and 34 | 67 and 14 |
  | the same rule, in whole words | 86 and 8 | 322 and 42 | 80 and 28 |
  | The list mends one wrong letter | 34 and 9 | 256 and 45 | 11 and 7 |
  | All three uses of the list together | 113 and 9 | 614 and 43 | 120 and 24 |

  This table is a quick count: what Tesseract read in each row is stored once, at each size, and the words step is
  read again from it with one rule off. The syllables are compared with the typed ones as one stream for each
  part, not set under notes, so the sums differ a little from the full runs. Where both were made on the clean
  copies they agree: the cut 120 gained and 2 lost in both, the mending 48 and 6 against 48 and 5, the word ends
  32 and 3 against 32 and 4.
- What the word rules lose, and how two were narrowed. The cut lost 141 syllables on the scan pages at first,
  most of them on typewriter pages: a typewriter sets a thin letter (i, l) in a box as wide as all others, so the gap beside it is wide in any word
  ("wi th", "thi rd"). A row whose letters stand evenly apart, centre to centre, is from a typewriter now, and
  there two words are parted only where their letters stand further apart than a letter's box (109 syllables
  back, 4 lost). The mending lost on the fresh set at first (13 gained, 34 lost), because a list of English words
  mended Romanian words into English ones ("stea" into "sea"): the list mends only on a page of whose letters a
  fifth or more stands in words that it holds (27 back on the fresh set, 5 lost; LitChoir 3 and 4). It still
  turns a rare real word into a common one when Tesseract was unsure of it ("stones" into "stone", "pray" into
  "pay"). The list parts a word that it lacks into two that it holds ("thanksgiving" into "thanks giving").
  Taking out the held lines lost as much as it gained at first (67 and 56): the feet of typewriter letters touch
  and look like a line, so a line that letters stand on stays.
- The new note rule: the flag of an eighth note with a short stem covers most of the stem, so that little of the
  stem is slim; such a stem counts where the flag's loop was read as a head over the note. 3 notes gained on the
  clean copies and none lost on any page; one page has one more note that is not there.
- Measured in that round and dropped: the form of a dash (short, long, after a line) does not tell a hyphen from
  the line of a held syllable; one other size alone gains about 80 syllables and loses about 80 (the gain comes
  from choosing between the sizes); a limit on the distance of the letters at every cut cost 389 syllables on the
  fresh set; a test of the list's language row by row cost 84 on LitChoir's pages.
- Twenty-two rounds before: 5 rules for signs, ledger lines and ties, each scored alone on the clean copies, then alone on
  all pages, and then together. Together they gain 24 notes on the clean copies and lose none (94.1 % to 94.2 %),
  and gain 78 and lose 11 over all pages. Each alone, on the clean copies and on all pages: a heavy sharp whose
  middle closed, which was read as a hollow head with a stem, 7 and 26 (none lost); a tie over the end of a line 7
  (1 lost) and 7 (7 lost); a natural whose right stroke stands against the stem of its note, which was read as a
  flat, 5 and 5 (none lost); a head that sits on a ledger line set close to the staff 3 and 11 (2 lost); the
  strokes of a heavy sharp, which are half a staff space wide, 1 and 43 (8 lost, and 3 after it was narrowed).
- What that round loses. The tie rule: on a clean copy one bow over the end of a line that the typed hymn writes
  as two notes, and on two copies by hand a slur that passes under the last note of a line and a pencilled arrow
  at the end of a staff (6 notes). The wide strokes: a short double bar drawn by hand that is read as a sharp
  (2 notes: that score, a page with a few lines of music, fell under 50 %, 34 of its 71 drawn notes, before 36),
  and one more false sharp. The ledger rule moves two heads on copies by hand. The wide strokes lost 5 more notes
  at first, with the rim of a whole note read as a sharp glued to its head: two heavy strokes that lie on a head
  are a part of that head now.
- Measured in that round and dropped: a second form of the ledger rule (3 notes gained, 2 lost, and no measure
  tells them apart), a looser limit for sharps with uneven strokes (3 and 1), wide strokes for flats and naturals
  too (6 and 4: the rim of a large hollow half note became a flat), and two looser limits for a flat tie (2 and
  2, 3 and 3). About 20 ties inside a line are still not read on the clean copies: a bow far under its heads, or a
  bow that lies along a staff line.
- Twenty-three rounds before: 8 rules for dots, flags, beams and signs, each scored alone on the clean copies and then
  together on all pages. Together they gain 67 notes on the clean copies and lose 1 (93.8 % to 94.1 %), and gain
  164 and lose 16 over all pages (one copy by hand fell under 50 %: 29 of its 59 notes, before 31). Each alone on
  the clean copies: a printed flag that reaches a little over half a staff space from its stem 16; the slim beams
  of a fine engraving 15; the cut end of a clef that was read as a flat before the first note, and held for the
  whole line, 9; a speck, or the cut end of a ledger line, that was read as a dot 7; a natural that was read as a
  flat 7; a thin beam at stems that the rows of the words cut 5; a stem that ended inside a letter 5 (2 lost: one
  is an eighth note on its page that the typed hymn writes as a quarter, the other a slur at the edge of the
  words that is read as a thin beam now); a full dot that stands close against its head 4. An eighth note read
  as a quarter stood 117 times on the clean copies and stands 78 times now.
- The limits of that round were counted before a run was spent on them. For a kind of mistake a census is taken:
  every read note of the clean copies that the scorer lines up with a typed note (22,725), with the measures that
  the rule looks at (the pieces of ink beside the head, or at the end of the stem) and the typed length. A limit
  is counted against the census in a second, and the counts met the runs. The census also showed what does not
  pay: a dot nearer to its head, a flatter dot and a paler dot each lose as many notes as they gain when the limit
  is only moved (4 for 8, 2 for 6, 9 for 7), and the size of the page's own dots does not tell a dot from a speck.
- The census showed more of the typed hymns too. Of 49 places where a typed dotted half note was read as a half
  note, about 20 are dots on the page. The others show no dot: a tie that was not read, or a typed hymn that
  differs from its page. Some half notes that count as read as quarters are two tied quarter notes on the page
  whose tie was not read.
- The rounds before that: 23 rules, each scored alone on the clean copies and then together on all pages. Together
  they gained 310 notes on the clean copies and lost 4 (92.2 % to 93.8 %), and gained 541 and lost 97 over all pages.
  The largest, each alone on the clean copies: key signs that the copy wore down to marks, told by their places,
  61 notes; the heads of two voices of flagged eighth notes, closed in by their flags, 61; a filled head with a
  pale middle on a page of large holes 45 (8 lost); the ison of chant scans from the letters over the staff 42; two
  strokes that are a flat with a high bowl 35; a half note with a thin rim 24 (2 lost); the mended bracket of a
  triplet 18 (2 lost); a head that sits on top of a ledger line 13 (1 lost); a small heavy sharp 12 (1 lost); a
  flat between two beamed notes whose stroke runs up into the beam 4.
- Two of these rules lost notes on the fresh test set (see below). They were switched off, narrowed with
  LitChoir's pages, and switched on again. A half note with a thin rim is read from its open hole and its stem: the
  rule took the paper between a head, its stem and its flag for such a note, and on LitChoir's pages the paper
  between a bar line, the end of a tie and a staff line. Now the stem must be the note's own: no bar line, no
  stroke of a sharp, and not the stem of a filled head. A small heavy sharp is one mark with two strokes: the rule
  took the stroke at the side of a breve (the long reciting note) for one. Now a sign must stand before its head:
  a mark that lies in a head without a stem is a part of that head. Before, the two rules lost 285 and 29 notes on
  the fresh set; now they gain 8 and lose 5 there.
- Two voices a second apart stand side by side. Some prints set the lower voice at the left, with the stems at
  the outer sides; the reader took such a pair for two notes, one after the other. Now they begin together when
  their heads touch (11 pairs on one page of a wedding hymn). The count of right notes does not show it, because
  it is taken part by part: it changes no note on the clean copies, loses 4 on copies by hand, and takes away
  about 55 notes that are not there.
- Five more of these rules lost notes on pages they were not made for and were narrowed. The worn key signature read
  the numbers of a time signature as two sharps of the other clef (142 notes on one hymn): it counts only
  under the clef that the staff shows. The ison rule read a section letter far over the staff as an ison (125
  notes). The ledger rule moved heads on a print that draws its ledger lines a full space from the staff (4). The
  rule for flagged eighth notes took chords of two half notes and a whole note under a quarter note for a flag's
  loop (12), and cut "heads" out of treble clefs: it tells a flag's loop from the hole of a hollow head by the
  ink at the two sides of the loop, and keeps off the start of a staff. The rule for a flat under a beam changed
  the key signature of two copies by hand (19 notes): it reads the signs of notes only. Two rules for whole notes
  gained nothing and are switched off.
- Before them: two staves with no bar line through their gap are two systems, 176 notes (none lost); six
  rules for a clef on the opening line, half notes, and heads that a flag or a beam closes in, 527 (38 lost).
- The small 8 under a treble clef is read. On LitChoir it changes no figure: two hymns show
  it, one was read as the tenors' staff already, and the other is typed an octave above what its page sounds (the
  scorer was told). On the fresh test set it is the largest single gain so far (see below).
- Earlier, each rule scored alone: a narrow printed flag that hugs its stem 96 notes on the clean copies
  (7 lost) and 112 on the other scans (43 lost); two heads one over the other on a stem, which were read as a
  stem, 209 on the clean copies (5 lost) and 207 on the other scans (15 lost).
- Before that, on the clean copies, each rule scored alone: half-note chords on staff lines 11 notes (none
  lost), the column of a stem that ends in a letter 10 (1 lost), a letter beside a stem's end that was taken for a
  slur 7, a false staff in an ornament 33 (4 lost on a photo page), and the brackets of triplets 98 (none lost).
  A rule for beams inside the rows of the words lost 3 notes to slurs and is off.
- The last rounds on the scans: new rules for the systems brought 1,511 notes, the rules for keys and time
  signatures 713 (4 lost), staves in pale lines 695 (6 lost), and a flat that a staff line cut off 105 (27 lost).
  Then, with none lost: the rule for the tenors' staff 402, and one key for the whole hymn 121. The sign of common
  time is found now: about 40 notes that were read from it are gone.

## Results on a fresh test set (pages that no rule was set on)

The rules above were set on LitChoir's own pages, so its figures are the best case. The fresh test set measures
what the reader does on pages it has never seen: 228 choir pieces from four open collections (English Orthodox
music, the Romanian liturgy, Romanian choral pieces, Church Slavonic pieces), each engraved with LilyPond together
with an exact list of every note and syllable on the page. The set is outside git. The pages are read as images
at 300 dpi, never from the PDF's drawing, and the words by Tesseract in the language of the piece. 214 pieces
are scored (258 pages, 40,906 notes); 14 have a staff with three voices or more, which the scorer cannot split yet.

| | Pieces | Notes right | At 99 % or more | At 90 % or more | Syllables right | Whole words right | Letters in order |
|---|---:|---:|---:|---:|---:|---:|---:|
| First reading, with the rules as LitChoir left them | 214 | 86.8 % (35,486 of 40,906) | 63 | 152 | 54 % | | |
| With the small 8 under a treble clef | 214 | 91.9 % (37,612 of 40,906) | 65 | 161 | 54.6 % (6,194 of 11,341) | 64.7 % (4,303 of 6,647) | 97.1 % |
| After two rounds of 23 rules | 214 | 92.3 % (37,772 of 40,906) | 70 | 162 | 54.6 % (6,194 of 11,341) | 64.7 % (4,302 of 6,647) | 97.0 % |
| After the round of dots, flags, beams and signs (8 rules) | 214 | 92.6 % (37,861 of 40,906) | 70 | 164 | 54.6 % (6,194 of 11,341) | 64.7 % (4,302 of 6,647) | 97.0 % |
| After the round of signs, ledger lines and ties (5 rules) | 214 | 93.2 % (38,127 of 40,906) | 73 | 165 | 54.6 % (6,194 of 11,341) | 64.7 % (4,303 of 6,647) | 97.1 % |
| After the round of the words (5 word rules, 1 note rule), with LitChoir's list of words | 214 | 93.2 % (38,127 of 40,906) | 73 | 165 | 67.4 % (7,643 of 11,341) | 86.6 % (5,753 of 6,647) | 97.3 % |
| After the second round of the words (6 rules with the list) | 214 | 93.2 % (38,127 of 40,906) | 73 | 165 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of hollow heads on a line and beams past a stem (3 rules) | 214 | 93.3 % (38,175 of 40,906) | 73 | 166 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of bows and slurs (4 rules) | 214 | 93.7 % (38,332 of 40,906) | 77 | 168 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of signs at bar lines and naturals (4 rules) | 214 | 94.2 % (38,539 of 40,906) | 78 | 170 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the beam at the side of a stem (1 rule) | 214 | 94.2 % (38,539 of 40,906) | 78 | 170 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of ties at bar lines and in chords (2 rules) | 214 | 94.2 % (38,547 of 40,906) | 79 | 173 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of wrong pitches (4 rules) | 214 | 94.2 % (38,548 of 40,906) | 79 | 173 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| The same reading, every typed note of a chord counted | 214 | 94.6 % (39,491 of 41,761) | 83 | 173 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the third voice (1 rule) | 214 | 94.6 % (39,494 of 41,761) | 83 | 172 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the chord notes that are not read (3 rules) | 214 | 94.6 % (39,494 of 41,761) | 83 | 172 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of notes that are not there (2 rules) | 214 | 94.6 % (39,500 of 41,761) | 83 | 173 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the clean scores that lack one to three notes (5 rules) | 214 | 94.7 % (39,559 of 41,761) | 85 | 176 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the long note as a witness and the quarter rest (5 rules) | 214 | 94.8 % (39,576 of 41,761) | 86 | 177 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the full bar and the short tie (4 rules) | 214 | 94.8 % (39,600 of 41,761) | 90 | 177 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the thin ink and the lengths (5 rules) | 214 | 94.9 % (39,619 of 41,761) | 90 | 178 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the ring, the beam beside a letter and the sharp (3 rules) | 214 | 94.9 % (39,618 of 41,761) | 90 | 178 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the two beams, the second dot and the bow between syllables (3 rules) | 214 | 94.9 % (39,630 of 41,761) | 90 | 178 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the whole note a second from a stem, the head on top of a near ledger line and the flag that is no flat (4 rules) | 214 | 94.9 % (39,633 of 41,761) | 90 | 178 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the tie that lies in a staff line and the end of a bold slur (4 rules) | 214 | 94.9 % (39,644 of 41,761) | 90 | 178 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the half note and the whole note with one speck and the bow that ends in a staff line (4 rules) | 214 | 94.9 % (39,647 of 41,761) | 90 | 178 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the tie over the end of a page (1 rule) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After the round of the clean scores that lack few notes, a second time (4 rules) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 72.2 % (8,187 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After round 34 (3 rules for the words) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 72.2 % (8,190 of 11,341) | 87.5 % (5,816 of 6,647) | 97.4 % |
| After round 35 (6 rules for the words) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 72.2 % (8,191 of 11,341) | 87.5 % (5,818 of 6,647) | 97.4 % |
| After round 36 (2 rules for the words and a guard) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 72.5 % (8,225 of 11,341) | 87.9 % (5,845 of 6,647) | 97.6 % |
| After round 37 (3 rules for the words) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 72.8 % (8,254 of 11,341) | 88.1 % (5,858 of 6,647) | 97.9 % |
| After round 39 (2 rules for the words, and Tesseract's larger files as further opinions) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 73.2 % (8,298 of 11,341) | 88.7 % (5,897 of 6,647) | 97.9 % |
| After round 40 (3 rules for the words, by the words that follow each other in the list) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 41 (2 rules for heads that touch) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 42 (a head whose stem the scan lost) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 43 (the tip of a tie that is no dot) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 44 (the ragged inside of a printed half note) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 45 (a head of a chord without its stem) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 46 (the pale speck of one engraving) | 214 | 94.9 % (39,650 of 41,761) | 90 | 178 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 47 (4 rules for the notes; the rules for the staves and the systems change no page here) | 214 | 95.1 % (39,720 of 41,761) | 90 | 180 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 48 (a thick bar line and the bold sign of common time: no page differs here) | 214 | 95.1 % (39,720 of 41,761) | 90 | 180 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 49 (specks in a staff line, a line of the scan, a short free tie, the hook of a rest: no page differs here) | 214 | 95.1 % (39,720 of 41,761) | 90 | 180 | 73.2 % (8,299 of 11,341) | 88.7 % (5,896 of 6,647) | 97.9 % |
| After round 50 (a slur past the end of a stem, an unsure syllable beside its hyphen, a word of solid ink: no note changes here) | 214 | 95.1 % (39,720 of 41,761) | 90 | 180 | 73.2 % (8,300 of 11,341) | 88.7 % (5,897 of 6,647) | 97.9 % |
| After round 51 (the curl of a flag, a mark at the bar line that ends a staff, a word that every reading of its row holds alike) | 214 | 95.1 % (39,729 of 41,761) | 90 | 181 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 52 (a mark past the end of a staff, a cell between a staff line and a slanted stroke, the word O beside a bracket) | 214 | 95.3 % (39,809 of 41,761) | 92 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 53 (a cell between a thin stroke and a filled head, a small note beside a chord, a bow that swells, a stray word under the clef) | 214 | 95.4 % (39,820 of 41,761) | 92 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 54 (a half note on a faint ledger line, two voices with their stems back to back: 3 notes that are not there fewer) | 214 | 95.4 % (39,820 of 41,761) | 92 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 55 (the trail of a long flag, a half note on a thick ledger line in two halves: 3 notes that are not there fewer) | 214 | 95.4 % (39,821 of 41,761) | 92 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 56 (two whole notes side by side, a beam at the end of another stem, a time signature: 13 notes that are not there fewer, and 4 notes fewer by the line-up of one piece's parts) | 214 | 95.3 % (39,817 of 41,761) | 92 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 57 (the quarter note of one voice on the head of another voice's beamed eighth: 62 notes gained, none lost, and 4 notes that are not there fewer) | 214 | 95.5 % (39,879 of 41,761) | 95 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 58 (the middle head of a column, a half note on a line whose inside lies flat: no page differs) | 214 | 95.5 % (39,879 of 41,761) | 95 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 59 (printed signs that touch their head or a staff line: no page differs) | 214 | 95.5 % (39,879 of 41,761) | 95 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| After round 60 (a natural whose closed middle is read as a half note: no page differs) | 214 | 95.5 % (39,879 of 41,761) | 95 | 182 | 73.2 % (8,299 of 11,341) | 88.7 % (5,898 of 6,647) | 97.9 % |
| of these, English (Orthodox Liturgics) | 109 | 95.6 % (13,779 of 14,415) | 49 | 87 | 92.3 % | 94.2 % | 98.0 % |
| Romanian | 88 | 93.7 % (17,144 of 18,288) | 37 | 77 | 66.6 % | 87.2 % | 98.6 % |
| Church Slavonic | 17 | 97.1 % (8,797 of 9,058) | 4 | 16 | 43.2 % | 71.2 % | 95.6 % |

- These are crisp engraved pages, not scans: they say how well the rules hold on print they were not made for,
  and nothing about thick or faded copies.
- The first reading found a rule that LitChoir's pages could not teach: 63 pieces set the tenors under a treble
  clef with a small 8, and 2,178 notes were right but an octave too high. The rule for the 8 was written with
  LitChoir's two hymns that show one; on the fresh set it gained 2,126 notes and lost none.
- The round of 21 rules shows why the set is read. The rules gained notes on LitChoir's pages, but with all of
  them the fresh set fell from 91.9 % to 91.6 % (37,455 notes). The rules were then switched off one by one on the
  pieces that fell: a half note with a thin rim cost 285 notes here, and a small heavy sharp 29. The pages showed
  the causes (the paper between a head and its flag, the stroke at the side of a breve). Each rule was narrowed
  with LitChoir's pages, where the same kind of mistake stands, and then read here again: together the rules of
  the two rounds now gain 147 notes on this set. One limit of this figure: these two rules were switched off and
  on again by this set, so for that one choice its pages are no longer unseen.
- The round of 8 rules for dots, flags, beams and signs was read here before it was committed, with no rule
  switched by it: 89 notes gained, and no piece lost a note. 86 of them are on the Romanian pieces.
- The round of 5 rules for signs, ledger lines and ties was read here before it was committed: 270 notes gained
  and 29 lost. Each rule was then read alone. The heavy sharp whose middle closed gains 248 notes and loses 1: the
  Church Slavonic pieces and many Romanian ones are engraved with heavy sharps. The wide strokes of a sharp gained
  34 and lost 26: these pages draw a stroke at each side of a breve, and the stroke with the rim of the hollow
  head was read as a sharp glued to the head. LitChoir's copies by hand show the same mistake at the rim of a
  whole note, and the rule was narrowed with them (two heavy strokes that lie on a head are a part of that head).
  Read again, the round gains 270 notes and loses 4. Two of the 4 are a bow over the end of a line between two
  equal notes: the answer writes a slur, and the page cannot tell it from a tie. One limit of this figure: the
  narrowing was made after this set showed the loss, so for that one choice its pages are no longer unseen.
- The round of the words was read here before it was committed: 1,453 syllables gained and 4 lost, 1,465 whole
  words gained and 15 lost; the new note rule changes no note here. The list of words is LitChoir's (the typed
  hymns of the app): it holds no text of this set. Each rule alone is in the table of that round above. Most of
  the gain is the cut of two words that Tesseract read as one (1,029 syllables), the largest cause that this set
  had shown. Two limits of these figures. The mending by the list lost here at first, and so did the first
  narrowing of the cut for typewriter pages (389 syllables); both were made again on LitChoir's pages, but after
  this set showed the loss, so for those two choices its pages are no longer unseen. And an English list does
  little for the Romanian and Church Slavonic pieces: their gain is the cut and the second look.
- The second round of the words was read here before it was committed: 548 syllables gained and 4 lost,
  67 whole words gained and 4 lost, and no note changed. Nearly all of the gain is the parting into syllables
  by the list (493 in the quick count), and all of that on the English pieces, which went from 78.1 % to 89.8 % of
  their syllables: these pages print many words whole over two notes, and LitChoir's list is English. Three
  limits of these figures. The cut of three words in one lost whole words on the Romanian pieces at first, and
  the cut beside a word of one letter lost 4 syllables there; both were put under the test of the page's language
  with LitChoir's pages, but after this set showed the loss, so for those two choices its pages are no longer
  unseen. The limit of the parting was read here at two values; the looser one was taken because it gains more on
  LitChoir's pages and loses the same there. And the Romanian and Church Slavonic pieces gain almost nothing: the list
  holds no word of theirs, and a list of their own would be needed to part their words.
- The round of hollow heads on a line and beams past a stem was read here before it was committed: 50 notes
  gained and 2 lost, with no rule switched by this set. Each rule was then read alone on the 24 pages that the
  round changes: all of it is the beam that goes on past a stem and was counted twice (34 of the notes on the
  Romanian pieces, 14 on the English ones). The two rules for hollow heads change no note here: these pages are
  crisp, and no staff line is faint inside a head. The words did not change.
- The round of bows and slurs was read here before it was committed: 157 notes gained and none lost, with no
  rule switched by this set. Each rule was then read alone on the 62 pages that the round changes: all 157 are the
  flag of a stem down that is drawn as a bow (135 on the Romanian pieces, 17 on the Church Slavonic ones, 5 on
  the English ones), which is how this engraving draws that flag at some sizes. The rule was written with 10 such
  stems of LitChoir's clean copies. The bow that was read as a thin head stands behind 7 of these notes. The
  reader also writes 283 fewer notes that are not there (5,606, from 5,889): ink of a bow that was read as a
  head, 214 by the first rule and 69 by the second. The rules for a slur between two stems and for a whole note
  change no note here. 77 pieces were at 99 % then, 73 before. The words did not change.
- The round of signs at bar lines and naturals was read here before it was committed: 208 notes gained and 1
  lost. Each rule was then read alone on the 47 pages that the round changes: the tall natural is all of it (95
  notes on the Romanian pieces, 81 on the Church Slavonic ones, 32 on the English ones), and the other three
  rules change no note here. The limit of the tall natural was set with 6 naturals of LitChoir's clean copies.
  The lost note is a half note that is read as a quarter since the natural beside it is read rightly (see the
  round of the signs above); the rule was kept with that loss. The reader writes 90 fewer notes that are not there
  (5,516, from 5,606): naturals that were read as heads. 78 pieces are at 99 % now. The words did not change.
- The round of the beam at the side of a stem was read here before it was committed: no page reads differently.
  These engraved pages have no stem that was followed into a slur.
- The round of ties at bar lines and in chords was read here before it was committed, and each rule alone on the
  32 pages that the round changes: 19 notes gained and 11 lost by the scorer's count (38,547). The first reading
  showed a mistake of the rule for a tie at a bar line: it made a bar line of the stem of an eighth note, which
  ended a sharp. The guard against it was tried on the two pages that showed it (see the round of ties above), so
  for that guard they are no longer unseen. Of the 11 notes that are still
  lost, 6 stand at three bows between two equal notes that the answer writes as slurs, and 5 in one piece whose
  staves read 2 more notes right than before. The reader writes 97 fewer notes that are not there (5,419, from
  5,516): paper closed in by a tie or a flag at an upright line. 79 pieces are at 99 % now. The words did not
  change.
- The round of wrong pitches was read here in full before it was committed, and each rule alone on the pages
  that the round changes. The four rules that stand change little on engraved pages: 1 gained and none lost
  (38,548). The note gained is in one piece, where the closed middle of a heavy sharp is no head now; 2 fewer notes are written that are not there (5,417). Two rules were switched off after this reading. The head at the border of two places
  lost 6 notes for none. The third voice on a second stem gains 95 notes and loses none counted staff by staff, and
  lost by the count of parts as it was then (7 gained, 20 lost): see the round of wrong pitches above.
- The round of the third voice changed the count: every typed note of a chord is counted from now on (855 more
  notes here; 829 of them are right, and 451 of those are heads that two voices share). The rows of the table
  above that row are by the old count. The rule itself was read here in full, off and on: 8 notes gained and 5
  lost by parts, 95 and none staff by staff, and 121 fewer notes that are not there (5,486, from 5,607 by the
  new count). One piece falls under 90 %. The words did not change.
- The round of the chord notes that are not read changed nothing that is counted here: no note gained and none
  lost with its three rules, 5,486 notes that are not there as before, and no page of the set is read
  differently in any field of a note: these engravings do not print two heads at a stem as one blot. A first
  form of the rule lost 3 notes here for none (2 pieces), and was narrowed on LitChoir's pages.
- The round of notes that are not there was read here in full before it was committed, and each rule alone on
  the 38 pages that the round changes. The rule for the numbers of a time signature that touch is all of the
  change: 212 fewer notes that are not there (5,274, from 5,486), 8 notes gained and 2 lost by parts, none
  gained and 2 lost staff by staff. The 2 lost notes are the numbers of a time signature that had been lined up
  with typed notes by chance (see the round above); the rule was kept with that loss. All 8 notes gained are in
  5 Romanian pieces. The rule for a false triplet in the words lost 2 notes here in its first two forms (a true
  bracket between two syllables) and changes no page in its third. The cause was read on that page, and the
  limits were set on LitChoir's brackets. One more piece is at 90 %. The words did not change.
- The round of the clean scores that lack one to three notes was read here in full before it was committed, and
  each of its five rules alone on the 70 pages that the round changes. The rule for a cell of the staff is all of
  the change: 60 notes gained and 1 lost by parts (47 and 2 staff by staff), and 159 fewer notes that are not
  there (5,115, from 5,274). The net gain is 27 notes in the English pieces, 29 in the Romanian and 3 in the Church
  Slavonic. The 2 notes lost staff by staff are in two Romanian pieces and were not traced. The rule for the
  whole note changes one page and no count, and the other three rules change no page. Two more pieces are at
  99 % and three more at 90 %. The words
  did not change. The first form of the rule for a cell, without the start of the staff left alone, was not
  read here.
- The round of the long note and the quarter rest was read here in full before it was committed, and that
  changed the round. Without its third rule it gained 17 notes here and lost 6 (the first two rules 14 and 6). The causes were read on these
  pages and are told in the round above; the third rule was written for them, and with it the round gains 18
  notes and loses 1 by parts (15 and 1 staff by staff), with 83 fewer notes that are not there (5,032, from
  5,115). Each rule was then read alone on the pages that the round changes. The long note as a witness gains
  15 notes and loses 1 (a dotted eighth before a sixteenth is made an eighth). The rule for several steps
  changes no count. The rule for the length that a voice says gains 6 and loses none. The reader of rests gains
  4 and loses 1 by parts (1 and 1 staff by staff) and takes away 85 notes that are not there; the lost note was
  not traced. The rule for the voice that rests changes no page. The net gain is 6 notes in the English pieces,
  10 in the Romanian and 1 in the Church Slavonic. One more piece is at 99 % and one more at 90 %. The words
  did not change.
- The round of the full bar and the short tie was read here in full before it was committed, and that
  changed the round twice. The rule for the note that fills a bar gained 9 notes here and lost none in its
  first form, which lost notes on LitChoir's copies by hand; narrowed on LitChoir's pages it gains 4 here. The
  rule for the short tie gained 13 notes here and lost 4, in one piece, and the cause was an old fault of the
  tie reader that is told in the round above; with the flat bow followed on exact thin ink it gains 13 and
  loses none, and 13 notes that are not there are gone (5,019, from 5,032): most are in the short pieces of
  the Romanian liturgy, where a tied pair of eighths was read as two notes. In its final form the round gains
  24 notes and loses none (22 and none staff by staff): the rule for the full bar with the rule under it 11,
  the tie rule 13, the beam rule none. The net gain is 23 notes in the Romanian pieces and 1 in the Church
  Slavonic; the English pieces did not change. Four more pieces are at 99 %. The words did not change.
- The round of the thin ink and the lengths was read here in full before it was committed. It gains 21
  notes and loses 2 (15 and 2 staff by staff): the exact thin ink 6 and 2, the four rules for lengths 15 and
  none (the long note that is no longer cut 8, the heads of a chord 5, the bar that is too long 2, the mark
  that is nearly a dot none). The two lost notes are quarters that are read as eighths with the exact thin
  ink, one in each of two English pieces; the cause is left for LitChoir's pages. 27 notes that are not there
  are gone (4,992, from 5,019). The net gain is 12 notes in the Romanian pieces, 4 in the English and 3 in the
  Church Slavonic. No more piece is at 99 %, one more is at 90 %. The words did not change.
- The round of the ring, the beam beside a letter and the sharp was read here in full before it was committed.
  The beam and the sharp change no note. The ring with a flag first lost 2 notes and gained none: a head of two
  voices took the flag of the other voice's stem. It was narrowed to the stem of the note's own voice, which
  changes nothing on LitChoir. It then changes four notes that are not there (a room under a head of two
  voices, read as a ring) to the true length of their voice. No note is gained, none is lost staff by staff,
  and as many notes are not there as before (4,992). The count by parts is one lower (39,618), in one Romanian
  piece, where the scorer lines up the same read notes otherwise. The words did not change.
- The round of the two beams, the second dot and the bow between syllables was read here in full before it was
  committed. It gains 12 notes and loses none (11 and none staff by staff): the two beams 8, in one English
  piece and two Romanian ones, and the second dot 4, in one Romanian piece that prints quarters with two dots.
  The bow between syllables changes no note. One note fewer is written that is not there (4,991). No more piece
  is at 99 % (90). The words did not change.
- The round of the whole note a second from a stem, the head on top of a near ledger line and the flag that is no flat
  was read here in full before it was committed. The flag rule gained 3 notes and lost 3 in its first form: in one
  piece a true flat stands close behind a stem in a beam. It holds for a stem with a flag and no beam now, and the
  round gains 3 notes and loses none, in one Church Slavonic piece. The rules for the ledger line change no note.
  Two notes of two whole notes' length are read as whole notes and no longer as half notes, neither right, and
  2 more notes are written that are not there (4,993). No more piece is at 99 % (90). The words did not change.
- The round of the tie that lies in a staff line and the end of a bold slur
  was read here in full before it was committed, in its first form and in its final one. No rule loses a note. The
  round gains 11 notes, all of them ties in Romanian pieces: 8 by the long bow that lies in a staff line, in one
  piece, and 3 by the bow over the end of a line that begins inside a staff line. The two rules for the slur's end
  change no note. 9 fewer notes are written that are not there (4,984). No more piece is at 99 % (90). The words
  did not change.
- The round of the half note and the whole note with one speck and the bow that ends in a staff line
  was read here in full before it was committed. Its first form lost notes here: the bow that ends in a staff line
  gained 3 notes and lost 12, where a short stroke beside a head runs into a line. The rule was narrowed on
  LitChoir's pages (the bow is 3.5 times as long as its hidden end) and read again: 3 notes gained, none lost.
  The other three rules change no note. 1 note fewer is written that is not there (4,983). No more piece is at
  99 % (90). The words did not change.
- The round of the tie over the end of a page was read here in full before it was committed, in both
  forms. The first form marked 56 coming halves on 40 pages and joined no tie. In the second form the page
  before tells the next page where a tie leaves: 8 pages change, 3 ties are joined, 3 notes are gained and none
  lost. 3 notes fewer are written that are not there (4,980). No more piece is at 99 % (90). The words did not
  change.
- The round of the clean scores that lack few notes, a second time was read here in full twice before it was
  committed. The first reading showed that a rule for a slur between two stem ends lost as many notes as it gained
  (4 and 4, on 23 pages): it was narrowed on LitChoir's pages. In the second reading one page changes and no
  count moves: no note gained, none lost, 4,980 notes that are not there, 90 pieces at 99 %. The words did not
  change.
- Round 33 was read here in full twice before it was committed. In the first reading the rule for the side of a
  whole note lost 3 notes: it is switched off. In the second reading, with the three rules that were kept, one
  page changes: no note gained, none lost, 4,979 notes that are not there (one fewer: paper closed in beside a
  bar line), 90 pieces at 99 %. The words did not change.
- Round 34 was read here in full before it was committed: no note changes, 3 syllables gained and none lost
  (8,190 of 11,341), the whole words as before. The quick count from the stored rows had shown 3 gained and 2
  lost for an earlier form of the rule that joins the pieces of a word: "the se-" at the end of a row, before
  "raphim" in the next, became "these". A piece with a hyphen after it is joined to nothing now; the guard is
  what the page prints, not a limit, and LitChoir's pages read the same with it. Two pages of the set hold rows
  of words that stand staggered; the rule for them changes no syllable here.
- Round 37 was read here in full: no note changes, 29 syllables gained and none lost (8,254 of 11,341), 13
  whole words gained and none lost (5,858 of 6,647). All of it is the rule for a stray first row under a
  staff, on two English pieces; the label and the two words that are one change no row here. The words that a
  hymn is typed otherwise than its page prints are a matter of LitChoir alone: the answers of this set are
  exact, and it is counted as before.
- Round 39 was read here in full, and the pages that its last change moved a second time: no note changes, 44
  syllables gained and none lost (8,298 of 11,341), 39 whole words gained and none lost (5,897 of 6,647). 38 of
  the syllables are on the English pieces (92.3 % of their syllables now, 94.2 % of their whole words) and 6 on
  Romanian ones. Nearly all of it is the larger files of Tesseract as further opinions (45 gained and none lost
  by the count from the stored rows). The language files are English: the Romanian and the Church Slavonic
  pieces get no further opinion that knows their letters. One guard of the round costs 6 syllables here and
  gains none (a reading of a larger file is not kept for its words of one letter); it is kept for LitChoir's
  worn pages, where it keeps 27 false words of one letter out, and three milder forms of it gave these pages
  nothing back.
- Round 40 changes one page here (read again with Tesseract): no note changes, 1 syllable gained and none lost
  (8,299 of 11,341), 1 whole word lost and none gained (5,896 of 6,647). Two words side by side were joined
  into one word of the list. The rules that use the words that follow each other change nothing here: the
  crisp pages of this set hold few misread short words, and the pieces in Romanian and Church Slavonic are
  not in the list. A further use of those pairs, as the choice among several words one letter away, lost 4
  syllables on a carol of this set whose words are not the list's, and is off.
- Round 36 was read here twice. The first reading, with the second look at a row that ink crosses, gained 38
  syllables and lost 28, and lost 33 whole words for 28: English gained 18 syllables and lost 1, Romanian
  gained 12 and lost 24. The list of words holds few Romanian words and cannot choose between two readings of
  a row. The rule was narrowed on LitChoir's pages, which show the same on three hymns in Arabic and Greek (see
  the round): on a page whose words do not fit the list, the second look must hold more letters in words of
  the list. The final reading, with the rows of few words too: no note changes, 44 syllables gained and 10 lost
  (8,225 of 11,341), 39 whole words gained and 12 lost (5,845 of 6,647). Nine of the ten lost syllables
  are Romanian: a word of the list that stands in the second look by chance is enough to choose it. A list of
  words in the language of the piece is what these pages lack.
- Round 35 was read here in full before it was committed: no note changes, 4 syllables gained and 3 lost
  (8,191 of 11,341), 4 whole words gained and 2 lost (5,818 of 6,647). The rule for a sure word that is one
  letter from one of the list's commonest words makes all seven: it mends 6 misread words here (4 syllables by
  the count), turns 2 true
  words that LitChoir's list lacks into common ones, and shortens a syllable that a page spreads under its
  notes with its vowel doubled. The rule gains more than it loses here and stays; the limit is the list, which
  knows the words of LitChoir's hymns and not those of a new one. The five other rules change nothing here but
  for one syllable (see the round). The hyphens are not counted by the page here.
- Almost no note is missed (166 of 40,906 by the old count). What is lost, counted on the comparison of each piece in round 9: a sixteenth
  note read as an eighth (about 420: the second beam or flag), an eighth read as a quarter or a half (about 360;
  the rule for a flag drawn as a bow mended 157 of these since then),
  the long reciting note (a breve) read as a whole note (about 240), a triplet with no bracket (about 60), and
  about 1,200 notes with a wrong pitch.
- The reader writes 4,979 notes that are not there, most of them rests: these pages have many rests, and the
  reader of scans knows only the printed quarter rest, by a shape whose limits were set on LitChoir's prints.
- The words: Tesseract reads the letters (97 % in order), and since the rounds of the words most whole words are
  right (87 %). The syllables stay behind (72.2 %), because the engraving prints a word whole where its syllables
  stand close, with no hyphen. Such a word is parted now where the list of words knows how (91.3 % on the English
  pieces); the Romanian pieces (66.6 %) wait for a list in their language. The Church Slavonic pieces are in the
  old spelling, which Tesseract's Russian does not know.
- The set is for measuring. No rule or limit is set on one of its pages; a cause that it shows is worked on with
  LitChoir's pages and then measured here.

## Results on the reader test (31 typed hymns, 38 pages, 6901 notes)

The kit is the small test that each rule is checked on. Notes right is counted by the kit's `score.py` against the
typed hymns, of all typed notes.

| Kind of score | Hymns | copisteria alone | homr alone | ScoreReader 0.4 (copisteria's network) | ScoreReader now (no model) |
|---|---:|---:|---:|---:|---:|
| Printed | 12 | 67 % | 82 % | 76 % | 93 % |
| Old copy (notes drawn by hand) | 9 | 76 % | 37 % | 88 % | 86 % |
| By hand | 5 | 65 % | 70 % | 79 % | 87 % |
| Poor (faded or broken) | 2 | 93 % | 49 % | 95 % | 80 % |
| Digital PDF | 3 | 81 % | 72 % | 81 % | 100 % |
| All 31 hymns | 31 | 71 % | 66 % | 81 % | 90.2 % (6224 notes) |

- Over all hymns the own rules read more notes right than the network they replaced: 90.2 % against 81 %.
- They are behind the network on two kinds: old copies (86 % against 88 %) and the two poor pages (80 % against 95 %).
- 12 of the 31 hymns are at 95 % or more, and 18 are at 90 % or more. 6 are under 80 %.
- Round 60 moves no note of the kit (6224 by parts, 5794 staff by staff): no page of its hymns changes.
- Round 59 brought 2 notes by parts (6222 to 6224) and 2 staff by staff (5792 to 5794): a flat whose foot runs into a staff line in forerunner-synaxis-troparion and lamentations-troparia; holy-saturday-megalynarion reads 2 notes that are not there fewer (the middle of a heavy sharp).
- Round 58 moves no note of the kit (6222 by parts, 5792 staff by staff): no page of its hymns changes.
- Round 57 moves no note of the kit (6222 by parts, 5792 staff by staff). In megalynarion-zakkak it reads a soprano note on a shared head as the quarter note that the page prints (an eighth before), but a slur from the syllable before is still read as a tie into it, so the note is as wrong as before; in myrrh-pious-joseph the page reads as before.
- Round 56 moves no note of the kit (6222 by parts, 5792 staff by staff): in its two hymns that change (trisagion-jerusalem and pascha-receive-long), only notes that are not there go.
- Round 55 moves no note of the kit (6222 by parts, 5792 staff by staff): on its two pages that change, only notes that are not there go.
- Round 54 moves no note by parts (6222) and brings 2 by the kit's own count staff by staff (5790 to 5792).
- Round 53 brought 4 notes by parts (6218 to 6222) and 4 by the kit's own count staff by staff (5786 to 5790): the bow that swells in lazarus-koinonikon, and the cell beside a filled head in forerunner-synaxis-troparion and transfiguration-kontakion. Round 52 took 2 notes from the kit's count by parts (6220 to 6218): two false marks of trisagion-jerusalem that had counted, a cell at the loop of a flag and a cell beside two half notes whose stems cross; the kit's own count staff by staff is as it was. Rounds 50 and 51 left the kit as it was (6220). The kit gained 1 note in round 49 (6219 to 6220): a filled head with two specks in the rows of its staff line, in thomas-troparion. Round 48 left the kit as it was (6219). The kit gained 5 notes in round 47 (6214 to 6219): 2 in megalynarion-zakkak and 1 each in megalynarion-bulgarian, nativity-troparion and pascha-receive-long (a ledger line of two dashes, closed paper that is no head, and a staff that is followed to its end). It did not change in round 46. It gained 2 notes in round 45 (6212 to 6214): a head of a chord that was left without its stem, 1 each in all-saints-koinonikon and pascha-christ-is-risen-stomp. It gained 5 notes in round 44 (6207 to 6212): half notes whose inside is a ragged slit, 3 in nativity-troparion and 1 each in saturday-of-souls-troparion and palm-koinonikon. It did not change in rounds 33 to 43 (6207 notes). It gained 1 note in round 31 (6206 to 6207 notes): a dot between two heads that is the lower head's, in pascha-receive-long. It did not change in the round before it: no hymn of the kit holds a note over the end of a page. It gained 2 notes in round 29 (6204 to 6206): a half note on a line whose hole holds one speck, in pascha-receive-long and in nativity-troparion. It did not change in round 28. It gained 1 note in round 27 (6203 to 6204): a head on top of a near ledger line, in nativity-troparion. It did not change in round 26. It gained 1 note in round 25 (6202 to 6203): the head that a sharp touched, in all-saints-troparion,
  which has all its 142 notes now. It lost 1 note in round 24 (6203 to 6202): two hymns gain a note each by the rules for lengths,
  and two lose 3 by the exact thin ink (lamentations-troparia 2, all-saints-koinonikon 1). It gained 4 notes in round 23 (6199 to 6203), in two hymns, where a bar with one open step is
  as long as the full bars of its page. It gained 3 notes in round 22 (6196 to 6199), in two hymns, where a long note is a witness for
  the length of a short one. It gained 21 notes in round 21 (6175 to 6196): 19 where a cell of the staff was read as the inside
  of a head (15 of them on one copy by hand), and 2 where a head of two voices is tied to two heads. It gained 3
  notes in round 20 (6172 to 6175): three notes of one hymn that were read as a triplet
  because the hyphens of the words under them look like a bracket. It gained 13 notes in round 19
  (6159 to 6172), most of them where two voices a second apart are one blot at a stem. It lost 3 notes in round 18 (6162 to 6159): its scorer counts one note of a chord for each part of a staff, and the rule of
  that round sets notes into chords; the wide test, which counts every note of a chord since then, gained 13
  notes more than it lost with that rule.

## Limits

- The reader is not accurate enough yet to put a scanned hymn into the app without a check. Only 30 of the 294
  scanned scores are at 99 % (29 of the 78 clean ones), and 22 are under 50 %: thick copies where signs and heads ran together, pages
  where a clef is hidden, and pages of a service book with a few lines of music among the text.
- The rules and their limits were set on the same pages that test them. Those figures are therefore the best
  case. On the fresh test set, crisp engraved pages that no rule was set on, the reader has 94.9 % of the notes.
- The wide test compares with typed hymns that were made for singing, not for testing. Some differ from the page
  (another key, an octave, a repeat written out). Known cases are told to the scorer; others count as wrong. A single
  note that a typed hymn gives otherwise than its page counts by the page where it was found and looked at (51 notes
  of the clean copies; since round 41 also a note that the page holds and the hymn is typed with struck again), and so does a word (25 places of the clean copies, since round 37). The thick copies and the copies by hand were not searched, and a place where the reader and
  the typed hymn are both off stays a lost note.
- About 12,300 drawn notes of the scans are wrong (a note can be wrong in two ways; the parts were counted some
  rounds ago, when 13,700 were wrong): about 4,800 are not read at all, about 5,100 have a wrong pitch (a wrong key or clef, or one or two places off; no single cause stands out),
  and about 5,500 a wrong length (a half note read as a quarter because the copy filled its hole, an eighth read as
  a quarter because its flag or beam was not seen, dots). A rule of the bar length does not mend the filled half
  notes: most of them stand in hymns with no steady bar, and tested on all scans it lost 656 notes for 57.
- Some scores cannot reach the typed hymn by reading the notes alone: a psalm that gives a treble staff to the men
  by a word ("Men:"), and a typed hymn that sets a part an octave from the page.
- The score counts each part. A staff of two parts is split by the stem direction (stem up is the upper part). One
  stem read wrong, or one head of a chord missed, gives the note to the wrong part.
- The ison of a chant scan is read only where the page names it with a letter over the staff, and it is scored by
  its marks: one note for each letter, with its pitch. How long each held note lasts is not scored. Where the
  page does not mark the ison, the typed ison is listed apart.
- Not read yet on scans: slurs, and every rest but the printed quarter rest that is a piece of ink of its own. A rest can be read as a note (about 5,000 notes that are not there on the fresh test set,
  beside 40,906 true ones). A reciting note drawn as a breve is read as a whole note. A triplet is read from its bracket only: a
  3 over a beam without a bracket is not seen, and the number in the bracket is not read (it is taken for a 3).
- The words of a scan are right for 4 syllables of 10 with the own letter reader. On clean type its limit is the
  grouping of the letter shapes (n and u, h and b fall into one group), not the list of words. With the optional
  Tesseract step and a list of words they are right for 8 of 10 (9 of 10 on the clean copies). What it still
  loses there: letters that Tesseract reads wrongly on heavy or pale pages (doubled letters, a word run into its
  neighbour), a row of words that the reader does not find or reads only from its second word on, stray ink that
  is taken for a row of words, words under another staff than the one that is scored, and a refrain that the
  page does not print. A word that the page prints without a hyphen over two notes is parted only when the list
  knows how, and as most hymns part it, which is not always how this hymn sings it. The list of words is the
  user's: with the texts of another church or another language fewer words are mended and parted, and none on a
  page that the list does not fit. Each row is read up to
  three times, which takes 3 to 4 seconds for a page. Tesseract is not our own step and
  it holds a small neural network: the own letter reader must catch up with it before the goal is met.
- The larger language files of Tesseract are not part of ScoreReader and are not in this repository: the user
  fetches them and names their folder. They were measured for English only; a page in another language gets a
  further opinion that does not know its letters, and the reading is kept only where it fits the list better.
  A row in doubt is read six times more with the two files: the run of every page of LitChoir took 2,055
  seconds with them and 1,388 without, on four cores. A further reading is chosen by the list of words, so
  without a list the larger files are not asked. And the guard for words of one letter costs right syllables
  on crisp pages (6 on the fresh set): a stroke and a true letter I are not told apart in a further reading
  yet, as they are in a reading of the small file.
- Time signatures are
  found so that they are no notes (the numbers, and the C of common time; not the sign of cut time, and not a small
  C), but they are not read into the result. A tie is read when its bow runs from head to
  head on one line of the page, or over the end of a line to the next line of the same page. The length of a
  full bar is taken from the bars of the page itself, where half of the bars that the voices agree on are as
  long as each other; on a page of chant with bars of many lengths it says nothing. A bold tie, thicker
  than 0.4 staff space in its middle, is read only on the pages where that limit is an even number of pixels
  (its upper edge is followed there, by a fault of the first tie reader that was found in round 23); a rule
  of its own for the bold tie is not written yet. The same fault of one pixel stands in three more steps
  (the staff lines that are taken away under a mark, the wide ink of a stroke through a staff line, the thin
  ink at the start of a staff) and in the closings of the reader: their limits were set with it, and mending
  them loses notes, so they keep it. A long note is no longer made as short as the steps under it: where a
  voice under it has a wrong length, the long note is right more often. The heads of a chord on one stem are
  made as long as each other only where they are of one kind; a hollow head beside a filled one is left as it
  was read. A print of a music typewriter sets two notes over the staff alike, as a head on one ledger line
  that stands between the rows of the first and the second: the page does not tell a D from an E there, and
  the reader reads the lower. A tie over a page
  break is not read, and a slur between two equal notes cannot be told from a tie. A bow from syllable to
  syllable between two equal notes is told from a tie only on a page that has five such bows or more over its words.
- The reader also writes notes that are not there (about 490 on the kit), from rests, letters of the words,
  ornaments and slurs. They are counted apart and do not lower notes right, but a singer would see them.
- `hymn` joins the pages of a score into one MusicXML file, staff by staff. It does not know repeats, its joined
  file is not scored as a whole yet (the wide test reads the pages as `hymn` does and joins them itself), and the
  reader does not write the app's hymn format yet.

## Next steps

1. The clean copies to 99 %, notes and words. The count holds the notes of a chord now; what it does not hold
   yet is the moment of a note, and the page-by-page layout of a score whose soprano divides. Notes: the chord
   notes that are still not read (the first note of a line cut away with the key signature, a whole note on a
   ledger line with fat sides, a bold tie that crosses a staff line and is cut there, a head under a faint
   ledger line), half notes of a heavy print with nearly closed holes or with a speck of ink in the hole, an eighth note read as a quarter (about 60 on the clean
   copies: a short stem with a small hook for a flag, a flag or a beam that lies in the rows of the words, a thin
   beam that lies before the found end of its stem and that the rule for a beam at the side of a stem does not find), two eighths a third apart that are one blot, a quarter head
   that faded and looks hollow, a half note whose hole is nearly filled, a dot drawn as a dash where no other head of its column has a dot, a tie inside a
   line that is not read (about 20 pairs: a bow that is one piece with a slur under it, a bow along a staff line, a bow that ends at the top of a stem), a slur at the edge of the words or over the ends of two stems that is read as
   a thin beam (counted on all scans: the bend of the ink does not tell such a slur from a beam), a whole note beside a bar line or under another voice's stem that is read as a half note, a pale
   filled head that is read as a half note (one faint engraving loses 159 notes), a sign glued to its head, a
   heavy tie that runs into a head, dots that touch a tie or a head, the printed C of common time, the letters p
   and f between the staves, pencil marks, the numbers of a time signature in the middle of a
   staff and the rests that are no printed quarter rest of their own piece of ink (a quarter rest that touches a
   bar line, the rests of a hand, eighth rests) that are read as notes (about 890 notes that
   are not there on the clean copies, of which about 4 of 10 are true notes that the count cannot place), a flag
   that a hand draws as a closed loop, a whole note on a ledger line whose hole is small beside its mark, the holes of clefs in the page's measure of a hollow head, a tied chord
   after a bar line that is one blot with the end of its tie, the end of a tie that closes a room at a head and
   is read as a flag, a dot of the lower voice that is given to the upper head, and paper closed in by a slur, a
   stem and a staff line that is read as a hollow head where it is narrower than 1.1 staff spaces or has no
   straight end (a limit on the size of a hole alone lost more than it gained).
   Round 41 found no cause of more than 6 notes among the 816 notes that the clean copies still lose; the kinds
   that it left are a tied chord of whole notes with one bow, whole notes worn to two crescents, and a sign that
   touches its head (about 15 notes, each by another cause).
   Round 42 left an eighth note whose stem and beam the scan lost whole (read as a quarter note now; its
   column could give the length), a hollow head whose stem the scan lost, and the hairline stems of grey scans
   that lie under the limit of the ink (a second look at the grey of the column over a head).
   Round 43 left 23 ties that are not read on the clean copies, each by a cause of its own; two of them end at
   a hollow head that the bow runs into and that is not read. It also left the eighth notes of two engravings
   whose hairline beams lie in a staff line, which nothing on the page tells from a slur between two stems.
   Round 45 left the heads that stand along a stem (two in the old print with square heads; a sharp, a flat
   and a letter stand there as often), the new heads that take a wrong length from the head whose stem they
   were given, the ticks that one print sets for dots, and the staves that bend at the edge of a photographed
   page.
   Round 46 left the pale heads of one engraving whose speck is as large as a true hole, a note of the lower
   voice that takes the beam of the upper voice's notes over it, and a hairpin or a slur at the end of a
   stem that is read as a beam.
   Round 47 left the comb that jumps a line on a steeply bent staff (the lines are followed from its wrong
   points there), the strokes of a pencil that count as ink, a flag that touches a bar line, the lengths
   that a column votes otherwise once a false note beside it is gone, and a gap of the count: a printed
   note that is not read in a run of five equal pitches is set apart as recited (about 15 notes of nine
   clean scores stand so and are to be looked at; the recitations of a clean copy belong on a list by the
   page).
   Round 48 made that list and left the notes that are not there, kind by kind: the letters of a dynamic
   under the staff, the end of a slur at a bar line, a pencil ring, the black edge of a page, the numbers of
   a time signature in a score of one staff, and a second in a chord of half notes. The figure of the notes
   that are not there still holds notes that a page prints and its hymn does not type (57 in one score) and
   the breves of a printed ison: they belong on a list by the page, as the notes and the words do. The nine
   clean scores with a recitation still set a note apart by the run of equal pitches.
   Round 60 left: a whole note that touches the head of another voice's half note and is read with that note's
   stem (about 10 places on the clean copies), the dots of the clean copies (40 places, about ten causes), and a
   natural glued to the chord after it in pascha-angel-cried-lady.
   Round 59 left: a natural whose closed middle is read as a half note with the natural's right stroke as its
   stem (pascha-angel-cried, two prints; round 60 reads it), a sharp whose stroke is followed into a slur, flats whose bowl is cut
   from the stroke or whose stroke is as thick as a stem, the small naturals of nativity-kontakion, and naturals
   glued to their heads that are read as flats.
   Round 58 left: whole notes read as half notes (64 places on the clean copies), a true half note that is
   taken for the loop of a flag where the stem of the note above passes through it (theophany-troparion,
   second scan), the unread ties of the clean copies (20, each a cause of its own), and a printed flat whose
   foot stands on a staff line, which is not read before its head (about 11 of the 56 notes of the clean copies
   that are read a semitone off).
   Round 57 left: the unison quarter note of holy-saturday-koinonikon whose up stem ends under a slur that is
   read as a beam from the left, a small flag that a hand draws before the end of a free stem
   (pascha-al-masih-qam), and the causes that round 56 left beside its shared head.
   Round 56 left: the shared head whose beam stays at its own stem (see the round: right by the page in most
   places, and two typed hymns sing the eighths in unison where the page prints a quarter note), the paper
   between a bar line and a chord of whole notes that two staff lines close in (communion-lords-prayer), a
   chord of quarter notes joined to the end of a tie and a bar line, and the count by parts, whose line-up
   can lose notes where a false note had held it.
   Round 55 left: the loose long ties of pascha-angel-cried (second scan), a whole note on a ledger line that
   sticks out at one side only, the half notes of a heavy print that is filled but for two specks, two whole
   notes stacked in two spaces and a whole note under a chord of half notes that takes the chord's stem
   (extra-beatitudes), the tie into the next page that megalynarion-bulgarian does not print, a bow from one
   syllable to the next that is read as a tie, and many lengths of one or two notes each (38 eighth notes read
   as quarters and 17 lost dots on the clean copies).
   Round 54 left: two half notes side by side on a thick ledger line whose insides lean apart in two halves
   each (lazarus-koinonikon: a rule that joins such halves lost 3 notes on the clean copies in both of its
   forms), the blots of a heavy print at a ledger line (pascha-receive-short), the tie from a whole note into
   a note of the next page (megalynarion-bulgarian), and two printed words that a hand struck out and wrote
   again (nativity-canon-ode-1: it waits for the owner's word on how they count).
   Round 53 left: a cell whose head stands below it (memorial-troparia), one head that two flagged stems
   share (extra-rejoice-o-virgin), a slanted time signature after the bass clef that is read as notes, a piece
   at the start of a row that ends a word of the row before and is mended into another word, the false note
   that the count makes where a tie goes into one note of a chord (palm-megalynarion), and a list by the page
   of the printed notes that a hymn does not type.
   Round 52 left: two filled heads with a cell between them that are read as one hollow head (a second look
   that leaves the rules for the flags as they are), the pair of half notes with crossed stems that
   trisagion-jerusalem prints otherwise than it is typed (a candidate for the list by the page), the cell in
   the number 4 of a time signature, a pencil ring whose paper has no level side (nativity-canon-ode-5), a
   line of a marker over a staff, and the false notes of copies by hand that the guard for a real head keeps.
   Round 51 left: the notes that are read in the black of a binder hole where the scan cuts a staff or the
   staff is followed past its final bar line (nativity-canon-ode-4, ode-1), a pencil ring and a line of a
   marker that are read as notes, a printed arrow with a tick by a pen, and the words that a hand wrote or
   wrote over on a clean copy (liturgy-mercy-of-peace), which wait for the owner's decision.
   Round 50 looked at the 17 clean scores nearest to whole and left: a half note with a ragged inside on a
   ledger line, printed words that a hand crossed out or drew through, a true word that the list lacks and
   that is mended to a word of the list, the first syllable of a row that is mended although the row before
   ends with the hyphen of its word, and one note by parts that no sheet shows (palm-megalynarion).
   Round 49 looked at the 13 clean scores nearest to whole and left: two half notes a third apart that touch
   with four holes (`LINE_PAIR` asks for three), a quarter note under two ledger lines that its column votes
   into an eighth, pencil rings and a marker stroke that are read as notes, the black edge of a page that
   does not run past its system, and worn hollow seconds on ledger lines.
   Round 44 left the three scans of the typewriter print at 317 or 318 of 327 notes each (the third scan was
   there before and did not change); a hollow head that is read in both voices where another head hangs
   over or under it (65 new heads; a first split of their stems gained nothing); a whole note on a line whose
   inside is read as a half note; and one head by hand that is read from its open hole a step low.
   Of the notes lost on the clean copies in round 13, 486 had only a wrong length, 346 only a wrong
   pitch (118 a semitone off, by a sign) and about 300 were not read. Words
   (213 syllables are missing on the clean copies after round 40, 195 for 99 % of each score; no cause holds
   more than a dozen: a response lettered by hand on two scans, single letters that Tesseract reads wrongly
   in words that are other words of the list, a lone O, a or I that is left out, a word under a long melody
   whose syllables are read as signs): the first syllable of a refrain that stands alone between two rows, a one-syllable word
   that the page parts with a hyphen and whose pieces each hold a vowel ("tho-u"), a misread word of three
   letters or fewer, a true word that the list lacks beside a common one, a row that is read only from its second word on, stray ink
   read as a row, the letters that Tesseract reads wrongly on heavy pages, score under which note a syllable
   stands, and bring the own letter reader up to Tesseract (name each letter by its nearest known shape, taught
   by hymns whose text is typed).
   The fresh test set is read beside the clean copies after each round. What it shows first: rests (the reader
   of printed quarter rests finds few of its rests), a letter of the dynamics that is read as a note, the second
   beam or flag of a sixteenth note, the breve of a reciting note, and a list of words for the Romanian pieces.
2. Then the thick copies and the copies by hand: clefs hidden behind a bracket, and the pages where almost nothing
   is read.
3. Score the joined hymn of the `hymn` command, and let the hymn teach the page more (parts, time).
4. Half notes whose hole the copy filled, by the notes that sound with them. Flags and beams that are not seen.
5. The other rests (a quarter rest that touches a bar line, eighth, half and whole rests, the rests of a hand).
   The length of a full bar is known from the page since round 23 and fills a bar with one open step; with
   the rests read it can fill a bar with two (counted: 6 notes to gain on the clean copies and 8 to lose
   without them). A long note can then be made longer where the steps under it are sure
   and no rest follows it (counted in round 21: 16 notes to gain on the clean copies, and 114 right notes
   that only a rest protects).
6. The app's hymn format.

## History

`experiments/2026-11-09-hard-scans/` holds the first tests on one difficult hymn, with a report. They found the three
causes that this reader removes: wrong systems from ink in the margin, staves found twice on bent pages, and the
ledger lines of one copyist.

Version 0.5 replaced copisteria's network with the own symbol step (layers, symbols, music). Each rule was switched
on alone and scored on all 38 pages, and a rule that did not gain notes was dropped.

Version 0.6 (in work) reads software-made PDFs from their drawing with their words, groups the staves of scans by
three more checks, votes for the key of a page and of a whole hymn, finds time signatures and staves in pale
lines, tells the altos' staff from the tenors' by its place over the bass staff, joins the pages of a hymn
(`hymn`), and moved the yardstick out of the reader. It reads the words of a scan with no model, the brackets of
triplets, and drops false staves; the clean copies are scored apart since then. The words of a scan can be read
by Tesseract instead (`--tesseract`), as an optional step that the owner allowed on 11 November 2026; rules
of our own stand around it (held lines, a second look at other sizes, words cut at a wide gap, and with a list of
words the ends of the words, one wrong letter, short words and unsure rows kept, and the parting of a word into
its syllables). The mistakes in the notes of the clean copies are sorted by a tool that takes each from the
scorer's own comparison; from it came the rules for a hollow head on a faint staff line or with a thin rim, and
for a beam that goes on past a stem. Sorted by the typed and the read length, the mistakes gave the rules for
a flag drawn as a bow, a slur between the ends of two stems and a whole note close beside another note's stem.
The notes a semitone off gave the rules for a sign that stands against a bar line and for three kinds of
naturals. A thin beam is found where it leaves a stem that was followed into a slur. The ties that were not
read gave the rules for a tie that crosses a bar line and for a tied chord. The notes with a wrong pitch gave
the rules for the sharp and the bar line of a faint print and for heavy sharps, and showed that the count of
parts does not hold a third voice on a staff. Since then the count holds every typed note of a chord, and two
notes on two stems side by side begin together. A list of the chord notes that are not read gave the rule for two
voices a second apart that the print sets as one blot at the two sides of a stem. The notes that are not there,
looked at on the page, gave the rule for the numbers of a time signature that touch or are bold, and the rule
for a bracket that is made of the hyphens of the words. The clean scores that lacked one to three notes, looked
at one by one, gave five rules; the largest says that a cell of the staff beside a bar line or a stem is no
inside of a hollow head. Then the lengths: a long note became a witness for the short notes that sound under
it, and the first rest was read, the printed quarter rest. The page then gave the length of its own full bar,
which settles a step that the voices leave open. A fault of one pixel was then found in the thin ink of the
layers and mended, and the lengths that the voices change were counted against the typed hymns. The two clean
scores that lack most were then sorted mistake by mistake: a ring with a printed flag is an eighth on a copy that
burnt out its heads, the end of a thin beam beside a letter is no slur, and a sharp that touches its head is cut
from it. The clean scores after these two were read by part: two beams that a staff line joins are two beams, a
note can have two dots, and a bow from one syllable of a word to the next is no tie. Then the mistakes that are left
were sorted by kind: a whole note beside a half note a second away keeps no stem, a head on top of a ledger line
that a print sets near the staff is known by the paper under that line, and the flag of an eighth is no flat. The
scores that lack one to three notes showed two causes more than once: a long bow that lies in a staff line is a tie
where its ink comes out of the line at both sides, and the bold end of a slur at a head is no second stem. A print
that fills the hole of a note on a line leaves a speck of paper there: one speck where a half note's slit lies makes
a half note where the bar has room for it, and one in the middle of an oval without a stem makes a whole note. A note
that is held over the end of a page is tied where the page before shows the bow that leaves it: that page tells the
next one where to look, because the ink before a first note looks like a short bow on every page. A slur that lies on
a beam is no second beam, since the page knows how thick its beams are; one dot between two heads of a column is the
lower head's; and the slit of a half note on a ledger line is measured from the line that the ink shows. Since
15 November 2026 the wide test counts a note as its page prints it where the typed hymn gives it otherwise (the owner:
"trust the page"); each such note was looked at on the page first. In round 33 a dash beside a head became its dot
where another head of the chord has a dot, a bold tie that is one piece of ink with its whole notes is taken off
them, and paper closed in between a bar line and a stem is no whole note. Round 34 was for the words: a syllable that
the page spreads under its notes with a hyphen is one syllable again, and a refrain that is printed once beside
the rows of four verses is read with the first verse. Round 35 was for single misread words: a word that Tesseract
was sure of is mended where it cannot be a word of the list or is one letter from one of its commonest words, the
word O is read where it came out as Q or ©, and a hyphen that the page sets at another place than the typed hymn
counts as the page sets it (the owner, 16 November 2026). Round 36 was for whole rows: a row that bar lines, stems
or slurs cross is read a second time without that ink, and a row of few words under a long melody ("A - men") is a
row of words now. Round 37 followed the owner's rule that the page is the source of truth: the words that a hymn
is typed otherwise than its page prints were looked at on the page and count as the page prints them (25 places
on the clean copies), a label under the first note stays whole, and a stray row close under a staff no longer
hides the row of the words. Round 38 gave the project its one name, ScoreReader, and a short README; it held no
rule. Round 39 brought Tesseract's larger language files in (the owner, 16 November 2026: "use the big one"): in
the place of the small file the standard file read fewer words right, so the small file stays the first reader,
and a row that it leaves in doubt is read with the "best" file and the standard file as further opinions.
Round 40 taught the list of words which words follow each other: a short misread word is mended by its two
neighbours, and a word that does not stand with its neighbours is taken from another reading of the row.
Round 41 went back to the notes of the clean copies, whose lost notes are scattered in kinds of a few notes
each: two rules for heads that touch (two half notes a third apart on lines, two heads a second apart that lie
across their stems), and a note that the page holds while the hymn is typed with it struck again counts by the
page.
Round 42 read a filled head whose stem the scan lost: the head by its shape (a slanted oval as large as the
heads of the page with paper around it), and its stem from the pieces that the scan left.
Round 43 read the tip of a tie that a staff line cuts from its bow as what it is, and no longer as the dot of
its whole note; a second reading of each page at another limit of the ink was counted and gave no rule.
Round 44 read the inside of a printed half note that is too ragged to count as round: it is kept in a layer
of its own and is a head only as a slanted slit with a stem, and the pieces of its bold rim are no notes.
Round 45 read a filled head that was left without a stem where it stands as the next head of the chord of a
read head, past the end where that head's stem begins; a mark along a stem is a sign or a letter as often as
a head and is not taken.
Round 46 took the pale speck in the filled heads of one engraving for what it is: the page shows the print
by its specks, which come in every size up to the limit, and by its wide half notes, and there a hole counts
only nearer to the usual hole. Eight notes of four scores count by the page.
Round 47 was the first under the raised bar (the clean copies read whole): notes that a hand changed count
apart, four rules for the notes came from the scores that lack few, each of the five lines of a staff is
followed past the end that the comb gives it, and the stored pages of the wide test, a week older than the
code, were built anew, which showed two systems that an opening line of the next system had joined.
Round 48 mended the count first: a printed note of a clean copy that is not read can no longer hide as a
recited one (15 notes of nine scores had). Then it took two kinds of notes that are not there: the pieces of
a thick bar line between the staff lines, and the bold sign of common time.
Round 49 went through the 13 clean scores nearest to whole: specks in the rows of a staff line, a line of the
scan through a system, a short tie that stands free and the closed hook of a quarter rest; three more clean
scores are whole (8).
Round 50 went on with the scores nearest to whole, notes and words: a slur that passes the end of a stem, a
syllable beside its hyphen that Tesseract is not sure of, and the black edge of a scan that is read as a
word; two more clean scores are whole (10).
Round 51 took notes away that are not there, the curl of a flag and the marks at the bar line that ends a
staff, and counts a word that every reading of its row holds alike as a word that Tesseract is sure of; one
more clean score is whole (11).
Round 52 took more such notes away: a mark past the end of a staff that ends in solid ink, and the cell
between a staff line and a slanted stroke that was read as a hollow head (27 on the clean copies, 159 on the
fresh set, which gained 80 notes); the word O is read beside a bracket; one more clean score is whole (12).
Round 53 read the filled head that closes in a cell with the stem of the note before it, a small note that one
engraver sets beside a chord, and a tie whose bow swells in its middle, and takes a stray word under the clef
for no word; one more clean score reads every printed note (23).
Round 54 read a half note whose ledger line is faint inside its head, and two voices whose stems stand back to
back as two notes that begin together; one more clean score is whole (13).
Round 55 read the trail of a long flag as the flag and the halves of a half note on a thick ledger line as one
head, and the list by the page took 8 notes that the page holds where the hymn strikes them again; one more
clean score has no note that is not there (19).
Round 56 read two whole notes side by side as two voices that begin together, and took a beam or a slur at the
end of another note's stem and the pieces of one engraving's time signature for no notes; the clean copies read
32 notes that are not there fewer, and two more clean scores have none (21).
Round 57 read the quarter note of one voice on the head of another voice's beamed eighth, where the other stem
ends in paper and the beam goes on to the next note, and the list by the page learned a typed note that the page
does not print for its part; the fresh set gained 62 notes, and one more clean score reads every printed note (25).
Round 58 sent the middle head of a column on one stem line with the neighbour of its own kind, and read a half
note on a line whose inside the line cuts in two flat halves; the clean copies gained 4 notes, and one more clean
score lacks only one to three notes (13).
Round 59 read printed signs that touch their head or a staff line: a flat whose foot runs into a line, a heavy sharp
whose stroke runs into a line, and a heavy sharp whose middle was read as a note; all scores gained 15 notes and lost
none, and the clean copies 4.
Round 60 read a natural whose closed middle had been taken for a half note with the natural's right stroke as its
stem; the clean copies gained 3 notes and 4 notes that are not there went.

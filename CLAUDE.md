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
optional step (`--tesseract`, `scorereader/ocr.py`), the reader works without it, and the own letter reader stays and
must catch up with it. The notes are read by rules alone, with no model.

Not reached yet: 86.2 % of the drawn notes over all 364 counted scores (99.3 % on software-made PDFs, 82.4 % on
scans; 83 scores at 99 % or more), 96.3 % of the notes on the clean copies (21,751 of 22,591, counted by the page;
21,702 as typed; 29 of the 78 counted scores at 99 %), and of their syllables 49.9 % with the own letter reader and 96.1 % with Tesseract and a list of
words (5,994 of 6,239, counted by the page; 5,940 of 6,259 as typed; 93.6 % of the whole words; 28 scores at 99 % of the syllables);
87.4 % of all syllables with Tesseract (86.0 % on scans), and 89.9 % on the kit (6207 of 6901).
On the fresh test set, which no rule was set on: 94.9 % of the notes (39,650 of 41,761; 90 of 214 pieces at 99 %),
72.8 % of the syllables and 88.1 % of the whole words.

## Direction

Every step is the engine's own: staves, systems, the clean page, the layers, the symbols, the music rules, and the
drawing of a software-made PDF. The engine is rules and classical image processing only, and it is ours to design:
it is no wrapper of another reader. copisteria, homr and Audiveris are yardsticks only; copisteria's step lives in
`bench/yardstick`, outside the package, and nothing in `scorereader/` may import it. Ideas, each to test:

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

- `scorereader/` is the reader. The project is called ScoreReader everywhere (the owner, 17 November 2026): the
  package and the command are `scorereader`, and a setting is `SCOREREADER_<NAME>` (`scorereader.setting`; a
  setting under its name from before the rename, `SCOREREAD_<NAME>`, still counts where the new one is not set).
- `README.md` lists its steps, the results and the next steps.
- `scorereader/reader.py` reads a clean page (`layers.py`, `words.py`, `symbols.py`, `starts.py`, `meter.py`,
  `signs.py`, `ties.py`, `triplets.py`, `drone.py`, `rests.py`, `music.py`). `letters.py` and `lyrics.py` read the
  words of a scan, and `ocr.py` reads them with Tesseract when asked, with rules of its own around it; the list of
  words (`--words`) serves both.
  `scorereader/vector.py` reads a software-made PDF from its drawing.
- `bench/` holds the tests. Measure each change with `bash bench/kit.sh <name>` and the kit's `score.py`.
  `bench/yardstick/` is copisteria's step (`bash bench/kit.sh <name> --yardstick`).
- The wide test (every score of LitChoir) runs with scripts outside git, because it needs the app's scans. It reads
  each score as `hymn` does: the pages in order, the key, the clefs and the leaving ties carried, one vote for the
  hymn's key. Its scorer joins a tie over the end of a page where both pages mark it at one pitch.
- The figures count every typed note of a part, the notes of a chord too (since 13 November 2026; before, one note
  of a chord for each part of a staff). The kit's own `score.py` counts as before. A rule that moves notes into
  or out of chords is read by both counts and staff by staff.
- The clean copies are a fixed list of 81 scores (outside git, with the wide test); 78 are counted (one was sorted
  wrongly, the page of two holds another version than the typed hymn). Report them first after each round, and
  change the list only with a reason.
- Switch one rule at a time and score it alone on all 38 pages, and on the wide test's pages that it changes.
  Rules scored together hide a rule that costs notes. The pages that a round changes are listed by the notes of
  the page and by its written music: a held note of an ison is written into the music only.
- A rule that guards is in no list of changed pages: where it stops a wrong change, its page reads as on main.
  Read such a rule off on every page, with the rest of the round on.
- A rule whose limits come from a census of the clean copies is read on every page of LitChoir and of the fresh
  set before the final reading: the copies by hand and the fresh set show what the clean copies do not (a rule
  for a note that fills its bar, and a rule for a flat tie, each lost more than it gained there in its first form;
  a rule for the heads of a chord and a rule for a bar that is too long were each narrowed twice by the copies by hand).
- On a copy by hand the wide scorer chooses how the staves stand for the parts, and a few changed notes can move
  that choice: a score then gains or loses 15 to 30 notes that no rule read otherwise. Before a rule is judged by
  such a score, compare its `layout` in the two results, and count the rule without it.
- A rule that asks how thick the ink is at a place reads whatever stands there on a copy by hand: a slur that is
  drawn thick, the stem of the next note, a bar line. Its first reading gains and loses alike there (a rule for
  the end of a thin beam: 8 and 7). Look at both on the page, and narrow the rule to the shape that the census
  showed, not to a limit.
- A rule for a head asks its measure of the stem of the note's own voice. A head that two voices share has two
  stems, and a flag at one of them says nothing of the other voice (the fresh set showed it, 14 November 2026).
  A stem in a beam has no flag: a mark at its right is the beam, and a flat can stand close behind it.
- The sheets of mistakes compare staff by staff, and they can line up the notes of a chord crosswise: a score showed
  10 mistakes where 3 were real. Count a score's lost notes by parts before a rule is written from its sheet. The
  count by parts can move by a note too where only a note that is not there changed its length: look at the read
  notes before a rule is blamed for it.
- A copy of the code that writes a new field into the notes for a census makes every page differ from the run
  before it. Compare the pages without that field.
- The notes gained and lost are the net of each score. A rule can read wrongly on a score whose count does not
  move: a second dot was read from a speck or from a repeat sign on eight pages, and no count showed it
  (14 November 2026). Look at every page that a rule changes outside the scores that it was written for.
- The words under a staff are those of every voice of the staff, and the words over a staff are those of the
  staff over it. Where one voice holds its note the others sing on, so a rule that asks the words about a note is
  a rule of the page (a bow from syllable to syllable: five such bows or more, and half of the page's bows).
- A rule for a head beside the staff is read on the thick copies and the copies by hand before it is trusted. A
  hand draws a note under the staff as a wide oval with no ledger line, and the rim of that oval is as level and
  as long as a line; on a thick copy a stem alone stands on a ledger line where the head is one blot with it. Two
  rules for a head on top of a near ledger line gained 12 and 11 notes on all of LitChoir in their first forms
  and lost 11 and 10, on such copies (14 November 2026). Ask for the shape of the print: one head as wide as the
  page's heads past the line, and a line that is longer than the head.
- The clean list holds some hymns in two or three scans of one print. A cause on such a page counts two or three
  times, in the notes that a rule gains and in the notes that a score lacks.
- OpenCV's opening and closing with a kernel of an even size are one pixel off: `ink & (1 - open(ink))` then
  keeps one edge of every blob (the top row for a kernel that stands, the left column for one that lies). Each
  place of the reader was mended alone and read (14 November 2026). Only the thin ink of the layers gains and is
  exact now (`layers.THIN_EXACT`, `layers._opened`). The ties (`TIE_RIM`), the staff lines under a mark, the wide
  ink, the thin ink at the start of a staff and every closing lose notes when they are mended: their limits were
  set with the fault, so they keep it. Write a new opening or closing exact, with a kernel of an odd size or as
  `_opened` does.
- A change of the layers is read at the clefs first: the clef, the end of the key signature and the hymn's key
  come from the solid shapes at the start of a staff, and one cell there that is no longer filled can move the
  key of a whole hymn.
- Before a run is spent on a limit, count it against a census: every read note of the clean copies that the scorer
  lines up with a typed note, with the measures that the rule looks at and the typed length (scripts outside git,
  with the wide test). A limit that only moves a border loses as much as it gains; the census shows what separates.
- A rule for the words with Tesseract is counted without Tesseract: its raw rows are stored once for a set of
  pages, at each size, and the words step is read again from them in half a minute with one rule off (scripts
  outside git, with the wide test). Count each such rule alone on the clean copies, on all scan pages and on the
  fresh set, and make the full runs at the end of the round. The quick count reads one row for each staff: it
  cannot see a rule that lets stray ink through as a row of words, so read the full runs score by score for
  syllables lost.
- A rule that makes an older limit milder (a bow that shows less of its ink, a stem that leans) reads, on a copy
  by hand, whatever stands between two near heads: a number of the time signature, a flat, the bent stroke of a
  stem. Look at every new reading of its first form on the page, true and false, and measure both: the shape that
  only the true ones have is the second half of the rule (a bow comes out of the line at both sides; the end of a
  slur does not go on upright). A narrowed rule acts only where its first form did, so the second reading needs
  only the pages that the first one changed.
- Before a helper is added to a module, search the module for its name: a second `def` of one name further down
  wins without a word (14 November 2026, `symbols._goes_on`).
- A rule that reads a speck of paper in a head is a rule of the page: on a worn print a filled head holds specks
  anywhere, and one lies where the rule looks (a half note with one speck: 37 gained and 9 lost in its first
  form, 14 November 2026). Count the page's notes that hold such a speck elsewhere, and switch the rule off for
  the page over a small share. Count the notes of the page, after the clef and the key signature are taken away:
  a flat of the key signature has a stroke and a hole and was counted as a head.
- A tally from a census is made with the rule's own arithmetic (two steps with one vote each add up to a length
  as well as one step with two), and every new reading of a rule for a whole class of marks (an oval without a
  stem) is looked at on the page: sharps, the numbers of a time signature and a scribble were among 54.
- A rule that lets a bow end earlier is read on the fresh set in its first form: LitChoir showed four true ties
  and no false one, the fresh set 3 notes gained and 12 lost (a short stroke beside a head that runs into a
  staff line). It was narrowed by the measures of LitChoir's true ties (the way that shows against the part
  that the line hides), not by the pages of the fresh set, and read there again.
- A mark that is read from the ink before the first note of a staff cannot be told from the clef, the key and
  the time signature by its measures: of 62 coming halves of a tie over the end of a page, 55 were such ink in
  the first form (14 November 2026). The page before tells the next page where to look (`ties_out` of a page,
  `ties_before` of the next), as the key and the clefs go on. A page that is read alone marks no coming half.
- A half that stands alone moves no count: the 55 false halves gained and lost nothing, on LitChoir and on the
  fresh set. A rule that marks something for a later step (the hymn, the scorer) is judged by looking at every
  mark on the page.
- The wide test counts by the page (the owner, 15 November 2026: "trust the page"). Where a typed hymn gives a
  note otherwise than its page prints, the note counts as the page prints it; the typed hymns stay as they are. The
  list of such notes is kept with the wide test, outside git, with the place on the page for each. A note goes on
  it only when its head is unmistakable at four times the size, or stands exactly as the same note stands elsewhere
  on its pages, and when the notes before and after it line up as right. A line-up that has slipped shows the
  column of a neighbour: there the reader is wrong, not the typed hymn (5 of the first 24 candidates). The scorer
  counts as typed when asked (`AS_TYPED=1`) and must then give the figures of the round before exactly; report
  the figure as typed once beside the figure by the page.
- A mistake that every scan of one hymn shares is a mistake of the print, of the reader on that print, or of the
  typed hymn. Compare the scans of a hymn before a rule is written from one of them.
- A print has its own way to set a note beside the staff: the dash of a music typewriter is the first ledger line
  wherever it stands, and one engraver sets the line low in the head. Before a rule is written from heads that are
  typed a step off, list every such head of the print with its distance from the staff and from its ledger line,
  by typed pitch. Heads that stand exactly as another note of the print stands are the typed hymn's, not the reader's.
- A measure that separates on the pages of one print is counted on every clean page before a rule: the grey of the
  middle of a head parts the filled heads of a pale print from its half notes, and other prints hold true half
  notes on both sides of that limit. Such a print needs a sign of its own that the page shows (its flagged notes
  with a hole did not give one: 16 % on a pale page, 12 to 14 % on pages of two other prints). Without one, no rule.
- When the wide scorer is changed, the reading before the round is scored again with it and must give the same
  figures. A change of the scorer that the fresh set shows to be wrong is mended in the scorer, never by a limit
  of the reader. The count staff by staff can move by the line-up of a clean copy too (two staves of two parts,
  then four voices, in non-liturgical-jesus-prayer: 62 notes that no rule read otherwise).
- A count of the page that switches a rule off (the share of heads with a speck that is no slit) is made as it
  was when a new measure changes what is counted. A new measure for the slit on a ledger line turned two specks
  of one worn page into slits, the share fell under the limit, the older speck rule came on for that page, and 8
  notes were lost (15 November 2026). Keep the old verdict for the count, and let the new one act on its heads.
- The thin line between the ends of two stems is also what reads a thick beam that no stem shows as its own (a
  stem that was followed into a slur over its beam). A rule that takes such a line for a slur asks for the shape
  of the slur, a bow at both stem ends that bends away from the heads, and not for the kind of the page: by the
  kind of the page it gained 4 notes on the fresh set and lost 4.
- A level of flags or beams at a stem is as thick as its thickest piece, at either side of the stem. Measured at
  one side, a beam under a bow was as slim as the bow.
- A rule that takes ink off a mark by its shape meets that shape in a beam, a flag and the stroke of a hand: a bold
  bow taken off a hollow head changed 100 pages in its first form and lost more than it gained (27 and 41, 15
  November 2026). Ask for the whole shape of the one thing: the bow of a tie is long, slim, bent, and its two ends
  stand at one height. A beam on a copy by hand was long and slim too.
- OpenCV takes what lies past the edge of a picture for ink when it opens it: a shape at the edge of a small mask
  stays where it should go. Set paper around a mask before an opening or a closing (`np.pad`).
- The score file of the reading before a round is made again before a rule is compared with it, whenever the list
  of the notes that count by the page or the scorer has changed since: an older file showed notes of the list as
  the gain of a rule (a first count of 11 notes was 4).
- Notes that sound together agree on a dot too. A mark that is nearly a dot is a dot where another head of its
  column has one at the same distance; a wider limit for the shape of a dot alone gains and loses alike.
- A bar whose lengths do not add up seldom holds the wrong length (26 wrong lengths in 106 such bars of the clean
  copies whose notes are all sure); the bars with a note that is not sure hold them. A rule that fills a bar with
  two or three open steps by the one choice that fits gained 3 notes and lost 4 (16 November 2026).
- A rule that joins the pieces of a word by the list of words is read on every scan page from the stored rows
  before it is trusted: its first form gained 9 syllables on the clean copies and lost none, and gained 20 and
  lost 18 on all scan pages. What it joined wrongly were the pieces that a misread leaves: a piece of one letter
  that is no vowel ("ma-n i" for "ma-ni"), a piece with a hyphen after it at the end of a row, a piece that is a
  word with its other neighbour. A piece that holds no vowel is no syllable: that tells a syllable that the page
  spreads under its notes ("wi-th") from a word that the page parts. The page's own hyphens win over the list
  wherever both pieces can be syllables ("lo-ved").
- The rows of the words are the rows of the page that cross many letters. Where rows stand staggered (a refrain
  printed once beside the rows of the verses) the stretch is too high for one row and was dropped whole, on 32
  pages of LitChoir. Such a stretch is parted by the lines that its letters stand on (`words.word_rows`). These
  rows are for the words only: the notes are read with the rows as they were (`words.word_bands`), because a
  stem ends where a row of words begins, and the first reading lost 4 notes on one copy. A change of the rows of
  the words is compared on its pages note by note, field by field, before the words are counted.
- The replay of the words from stored rows cannot count a rule that changes which rows there are. A census
  names the pages that such a rule changes, and they are read with Tesseract, with the rule off and on.
- The words count by the page too (the owner, 16 November 2026). A typed word that was read with the same
  letters in the same number of syllables, with its hyphen at another place, counts as the page parts it. The
  scorer tries this staff by staff and keeps it only where the staff counts higher; `AS_TYPED=1` gives the
  figures of the round before exactly, and the fresh set stays exact. A word that the page parts into more
  syllables than the typed hymn has is not counted so by itself: it goes on the checked list of the words that
  are typed otherwise than the page prints (see below).
- A word that Tesseract is sure of can still be misread. Mending every such word loses as much as it gains. A
  census of every word that a mending rule would change, each labelled by the typed hymn (the new word is typed
  and the read one is not: right; the read word is typed: wrong), finds what separates: two runs of three
  letters that no word of the list holds, or a new word that is one of the list's commonest. The list leaves out
  the hymn that is read, but LitChoir's hymns share their words, so LitChoir shows few true words that the list
  lacks. The fresh set shows them: the rule for the commonest words changed 9 words there, and 2 were true words
  one letter from a common one. A limit by the unseen runs of letters does not part them (the runs come from the
  same list). A guard for a case that only a fresh page shows, with no case on LitChoir's pages, is not written.
- A mending rule changes more than its words. A row is read at three sizes, the reading that fits the list best
  is kept, and a mended word counts as held. A rule that mended 60 words rightly and none wrongly lost 6
  syllables: the first reading was whole with the mended word, the other sizes were not read, and a syllable
  beside the word stayed lost. Trace a lost syllable to its row at each size before a guard is added to the
  rule. A reading with a mended word is not whole now (`ocr.MEND_WHOLE`); taking letters off its fit as well
  lost more than it gained.
- A rule that brings in a syllable that was left out before (a sign that is read as the word O) is not judged by
  the right syllables alone: a syllable too many costs nothing in the count. Count what the rule adds against
  what it gains, sign by sign, by the line-up with the typed hymn, and look at the ones that the hymn does not
  confirm on the page (the sign of a copyright line, a note head, a dot).
- The replay of the words runs the clean copies, all scan pages and the fresh set side by side in two minutes.
  Each rule of a round is counted with that rule off against all rules on, and the full runs are read at the end.
- A change of the picture that Tesseract gets moves its reading of words that the change did not touch: with one
  bar line taken out at the left of a row, a word in the middle of the row was read otherwise. Taking the ink that
  crosses a row out of every picture gained 59 syllables on the clean copies and lost 40. Such a picture is a
  second look: it is read only where no reading of the picture as it is holds only words of the list, and the
  reading that fits the list best is kept (57 gained and 9 lost).
- A second look gives stray ink a second chance to be read as a row of words. Where no reading of the picture as
  it is was a row of words, the second look is tested as a row that Tesseract is not sure of.
- A rule that chooses by the list of words cannot choose on a page in another language than the list. The fresh
  set showed it (Romanian: 12 syllables gained and 24 lost by the second look), and LitChoir's three hymns in
  Arabic and Greek lost two syllables each. The guard was set on LitChoir's pages, in three forms. No second look
  on a page whose words do not fit the list: 9 gained and 21 lost, because a page whose rows are read as stray
  ink does not fit the list either. The second look is kept only where it holds more letters in words of the
  list, on every page: level on all scans (25 and 27) and 3 lost on the clean copies, because on a page in the
  list's language how sure Tesseract is chooses as well as it does among the three sizes. That test on the pages
  that do not fit the list alone: 3 gained and 1 lost, and the clean copies as without it. Count a guard alone
  on every page, not only on the pages that it was written for.
- The band of a row of words is as high as its small letters where few letters have tops or tails. A measure of
  how high a letter can be comes from the staff space, not from the band: a first form took the tops of d, h and
  H for stems.
- The line of a held syllable joins letters into one long piece of ink. A rule for a slur asks for the stroke
  itself (one thin stroke in each column, over a long way, that rises or falls), not for a long piece of ink.
- A row of few words under a long melody ("A - men", "Al - le - lu - i - a") crosses fewer letters than a row of
  words must, and was no row at all. A stretch between two staves with no row gives its best row of four letters
  or more to the step of the words alone (`words.SPARSE`); its reading must hold only words of the list and be
  no label (one word with a colon). The typed syllables of such a row were counted apart before, as words that
  no page prints: the count of the syllables grows with the rule. Before a score's lost syllables are blamed on
  Tesseract, look whether the row is a row at all.
- The stored rows hold the readings of the second look too (the sizes under 0) and the mark of a row of few
  words. A rule that chooses among the stored readings is counted by the replay; a rule that changes the picture
  or the rows needs a new census of the rows.
- The page is the source of truth for the words too, for every kind of difference (the owner, 16 November 2026:
  "If you find the page says one thing but the litchoir says another, then the page is the source of truth"). A
  word that a hymn is typed otherwise than its page prints goes on a list with the wide test, outside git, with
  its place on the page: a heading that is typed as a word under the notes where the page prints a label there,
  a spelling, a word that the page prints whole under two notes, a syllable that the page prints in two pieces.
  The page can print another number of syllables than the hymn is typed with, so the count of the syllables
  moves with the list. The typed hymns stay as they are, `AS_TYPED=1` gives the figures of the round before
  exactly, and the fresh set stays exact.
- A word goes on that list only after it was looked at on the page. The difference between the typed and the
  read syllables names the candidates, and about half of them are the reader's mistakes: of 45 candidates on the
  clean copies 25 places in 8 scores were the page's, and about 20 were words that the reader read wrongly or
  that the list parts further than the page ("hal - lowed" under two notes, read in three pieces). A place
  where the reader is wrong is never put on the list.
- The tool that shows the typed against the read syllables shows the words as they are typed. A hyphen that
  the scorer already counts by the page looks like a mistake there (11 such places were taken for a fault of the
  scorer, and were counted rightly). Ask the scorer's own count before the scorer is changed.
- A page can part one word in two ways (the typed way in one line, another way in the next). The count of
  the hyphens by the page tries each place of such a word alone and keeps the page's way where the staff then
  counts higher.
- The first row under a staff holds the first verse, and only that row is set under the notes. A stray row
  there (a note by hand under the staff, read as short words) hides the row of the words. Where Tesseract is
  less sure of the first row than 50 of 100 and sure of the next row under the staff, the first row is stray
  (`ocr.FIRST`). True rows begin at 51 on LitChoir's pages: a limit of 60 lost 9 syllables and gained none.
- A word that the page parts with a hyphen of its own is still parted further by the list: a scan loses a
  hyphen far more often than a page sets two syllables under one note (keeping the page's parting gained 7
  syllables on all scan pages and lost 28, and lost 115 on the fresh set).
- The quick count of the words from stored rows counts as the kit does: the words of a typed note are one
  syllable there, and the list of words by the page is not in it. A rule whose gain shows only with that list
  (a label that stays whole) is judged by the rows that it changes on the three sets, and by the full runs.
- A stretch of a typed hymn that the scan does not show (a part of a system that the copy left white) is told to
  the scorer with its place on the page, as the other relations of a score and its typed hymn are: its notes and
  words are listed apart. Before a score's lost syllables at the end of a row are blamed on the reader, look
  whether the scan shows them.
- The kit's own scorer writes its sheets of mistakes into the folder of a run, over the wide scorer's sheets of
  the kit's hymns. The count staff by staff is read from those sheets: count it before the kit's scorer runs,
  or score the run again first (a count that moved by 18 notes between two scorings of one reading was this).
- `experiments/` holds the record of the first tests.

## Rules

- This repository is public. Do not add scans, typed hymns, recordings or keys. They stay in the test kit, outside git.
- The test kit is in `~/Projects/LitChoir/tmp/omr-test` (`SCOREREADER_KIT`). Do not change the kit's own files.
- The reader needs only OpenCV and NumPy (and pdfplumber for software-made PDFs). Nothing in `scorereader/` may
  import PyTorch, copisteria or any other model. The one exception is `scorereader/ocr.py`: it calls the Tesseract
  program for the rows of the words, only when it is asked for, and no note may depend on it. The kit's
  copisteria environment (`$SCOREREADER_KIT/tools/copisteria/.venv/bin/python`, after
  `source "$SCOREREADER_KIT/env.sh"`) has all of it and runs the yardstick too.
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

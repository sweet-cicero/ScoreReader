# ScoreReader

## Goal

The end goal is a local engine of our own that reads scanned choir scores consistently, with creative new and old
methods. A page goes in and the notes come out, on the owner's own computer, with no assistant, no cloud model and
no neural network in the loop. The result must go into the LitChoir app as a typed hymn.

The target (the owner, 10 November 2026): every score of LitChoir is read locally, without AI, and none of them is
under 99 % of the notes that its pages show. The words under the notes belong to the result: music without its
words is of no use. Recited syllables that no page prints are counted apart, and the reader must mark a reciting
note. The work does not stop at a partial result. Report each result with its limits.

First milestone (the owner, 11 November 2026, raised on 17 November 2026): the clean copies are read perfectly, the
81 scan scores with printed notes and words and crisp ink ("No one wants a 99% product. the clean copies need to be
100%, or maybe 99.9%"; "the clean copies should be consistently perfect"). Each clean score reads every note and
every syllable that its pages show, with no note that is not there; no clean score has a thousand notes, so 99.9 %
of a score is all of it. The copies by hand keep the target of 99 %. Work on the clean copies first, notes and words.
Report them by the scores that are read whole (every note; every note and syllable; no note that is not there)
beside the share of the notes. The thick copies (26) and the copies by hand (189) come
after it. The owner decided against a local language model. The owner allowed Tesseract for the words of a scan
(11 November 2026: "we can use tesseract, if it will help, but may eventually have to improve upon it"; 16 November
2026, of its larger language files: "use the big one"): it is an
optional step (`--tesseract`, `scorereader/ocr.py`), the reader works without it, and the own letter reader stays and
must catch up with it. The notes are read by rules alone, with no model.

Not reached yet: 87.9 % of the drawn notes over all 364 counted scores (99.3 % on software-made PDFs, 84.5 % on
scans; 103 scores at 99 % or more), 97.8 % of the notes on the clean copies (22,162 of 22,655, counted by the page;
22,018 of 22,605 as typed; 49 of the 78 counted scores at 99 %; 45 scores read every printed note, 48 every
syllable, 41 both, 47 have no note that is not there, 41 are whole in all three; 488 printed notes and 145 syllables
are lacking and 174 notes are read that are not there, each printed head counted once since round 78), and of their syllables 49.9 % with the own letter reader and 97.7 % with Tesseract, its larger
files and a list of words (6,110 of 6,255, counted by the page; 6,045 of 6,260 as typed; 95.7 % of the whole words; 49 scores at 99 % of the syllables);
89.4 % of all syllables with Tesseract (88.5 % on scans), and 90.5 % on the kit (6247 of 6901).
On the fresh test set, which no rule was set on: 95.7 % of the notes (39,980 of 41,761; 102 of 214 pieces at 99 %),
73.6 % of the syllables and 89.0 % of the whole words.

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
- `README.md` says what ScoreReader does and how, for a person who reads it for the first time: short and high
  level, with a plain list of the modules and one small diagram (the owner, 17 November 2026: no round-by-round
  updates, no lists of results or of rules, no diagram of each function or file). Do not write the results of a
  round into it. `docs/worklog.md` is the record: the results of each round on each set of pages, the limits, the
  next steps and the history. The README's status is one paragraph of rounded figures (about 96 %): change it
  only when a rounded figure changes.
- `scorereader/reader.py` reads a clean page (`layers.py`, `words.py`, `symbols.py`, `starts.py`, `meter.py`,
  `signs.py`, `ties.py`, `triplets.py`, `drone.py`, `rests.py`, `fermatas.py`, `music.py`). `letters.py` and `lyrics.py` read the
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
- A note that a hand changed on a clean copy counts apart (the owner, 17 November 2026: "Count hand-changed notes
  apart"): a printed head that is crossed out, drawn over or written in by hand is listed by its place on the page
  (outside git, with the wide test), counted apart from the print and held to the 99 % of the copies by hand. Every
  printed note must be read, also under a pencil ring, a marker or a paperclip: marks around the print are no
  excuse. A mark is called handwriting only after it was looked at four times the size and in the scan itself: two
  of the first three such places were worn print (17 November 2026).
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
- Tesseract's larger language files are further opinions, not the reader of first resort (the owner, 16 November
  2026: "use the big one"; `ocr.SECOND`, `--second`, `SCOREREADER_OCR_SECOND`). In the place of the small file
  the standard file read 26 syllables more and 81 fewer on the clean copies: the limits of how sure Tesseract is
  were set with the small file, and the larger network reads a stroke as the word I and a faint row as words. A
  row that the small file does not read as words of the list alone is read with the larger files too, the "best"
  file first and then the standard one: the two misread different words.
- How sure two readers are does not compare, so a reading of a further file is kept by the list alone: where it
  leaves fewer letters in words that the list lacks. That count is fooled in three ways, which the first form
  showed (22 gained and 10 lost on the clean copies). A stroke that is read as a word of one letter adds a letter
  of the list: words of one letter do not count there. A word of the hymn that the list lacks is mended to a
  word of the list in the reading that is less sure of it: a word that the first file read with the same letters
  is not mended, because two readers that agree have read the page. A misread that makes such a word shorter
  leaves fewer letters outside the list ("patience" as "patence", the label "Ison" as "son"): a reading that
  lacks a word which the first file read alike at each of its sizes, and that has fewer letters, is not kept.
- Single words taken from the other reader (the list's word at the same place) gained 6 syllables and lost 5:
  the commonest word wins there, and a rare true word loses. A second reader is judged by the whole row.
- A guard is counted alone with the rest on, as a rule is, and a guard of two halves half by half. The guard
  for a word that the first file read alike had a second half (no new word outside the list in its place): alone
  it gained 6 syllables and lost 15 on all scan pages and lost 3 on the fresh set, behind a first half that
  gained 29 and lost 12. It was taken out. Another guard (words of one letter do not count as words of
  the list) costs syllables in the count: 2 and 2 on the clean copies, 7 gained and 12 lost on all scan pages, none
  and 6 on the fresh set. It stays for what the count does not see: 27 false words of one letter on all scan pages,
  6 of them on the clean copies and none on the fresh set, whose pages hold no stray strokes. Three milder forms
  gave the fresh set nothing back. Say so where such a guard is kept.
- A rule that chooses among the stored readings names its pages exactly: the rows that the words step picks are
  written out for two copies of the code, and the pages whose rows differ are read again with Tesseract against
  the full run before (41 pages of LitChoir and 2 of the fresh set for a narrowed guard, not an hour of runs).
- A folder with only a language file holds no config files of Tesseract. Asked for its table of words by the
  config file, Tesseract printed nothing, and a run read no word at all. The table is asked for by its setting
  now. A run whose words are all gone is a fault of the setup, not a result.
- A stroke that stands alone between two words is a bar line, a line by hand or the letter I, and the word alone
  cannot tell (31 right of 1,739). The ink tells: the letter is as high as the capitals of its row and as thick
  as the strokes of the row's letters (0.8 to 1.25 times on LitChoir's pages), a bar line goes on over the row,
  and a line by hand or a dashed bar line is a hairline (`ocr.LONE_I`). The replay from stored rows hands the
  page itself to a rule that looks at the ink.
- An s at the end of a word is neither taken away nor added by the mending (`ocr.MEND_S`). The list holds the
  singular of nearly every plural, so it cannot choose between them: of the words that lost a last s on all scan
  pages 26 were wrong and 12 right.
- The stored rows hold one census for each language file (the sizes from 1000 on are the second file, from 2000
  on the third). A new file needs its own census of every scan page and of the fresh set before the replay can
  count it.
- When another thread changes main in the middle of a round (the package was renamed), the branch starts from
  main again and the round's changes are carried over as a patch. The working copy of the wide test keeps the
  old package name as a link, so the tools outside git run as they are.
- The list of words also tells which words follow each other (`lex.pairs`, from a list that is plain text;
  `bench/wordlist.py --text`). The hymn that is read and its other scans are left out of the list, so a phrase
  that only this hymn has gives no pair. A pair is used strictly: a word of three letters or fewer that the list
  lacks becomes the list's word one letter away that stands between the same two neighbours in the list's text
  (`ocr.PAIR`), and a word that does not stand with both neighbours is taken from another reading of the row
  where that one does (`ocr.PAIR_OTHER`). A census of every word that such a rule would change, labelled by the
  typed hymn, showed where pairs must not be used: a word of the list with one neighbour on its side is right
  far more often than the word that the pair would put there (8 right and 85 wrong), and a longer word that the
  list lacks is a true word of the hymn as often as a misread (18 and 16).
- Choosing all words of a row together, each word or its neighbour in the list so that most pairs hold, changed
  more words wrongly than one word at a time with the neighbours as they were read (5 wrong of 44 against none
  of 31). A misread neighbour gives no pair, and that is the safer side.
- A census of words is not the count of syllables. One neighbour in the place of two looked nearly free in the
  census (23 right, 3 wrong, 139 where the typed hymn has another word) and lost in the count (27 syllables
  gained, 37 lost): a piece that is changed into a word is no longer joined to the word that it is a piece of.
  A change that the census calls neither right nor wrong is not free.
- Pairs in the choice among the readings of a row gained 10 syllables and lost 7 on all scan pages: a border
  that moves. Pairs as the choice among several words one letter away gained 12 and lost 4 there and lost 4 on
  the fresh set, on a carol whose words are not the list's: it is off.
- Two words side by side are mended into one although the list holds one of them, where it holds the whole
  twenty times as often (`ocr.MEND_PAIR_RARE`): the list held a piece of "Al-le-lu-ia" three times as a word.
  A list made from typed hymns holds stray pieces as rare words.
- The notes that the clean copies still lose are scattered (round 41: 816 notes in 49 scores, no cause of more
  than 6 notes). Sort the lost notes by where they stand before a score is read for a rule: a long stretch of
  one cause would show there, and none did.
- A rule that reads a mark by the number of its holes meets that number in other things: two half notes a second
  apart with their stems, a head and the room between it and its sign, an ornament, a scribble by hand. List
  every mark where the first form acts, with the middles of its holes, and look at each: the true ones share a
  shape (for two half notes a third apart on lines: three holes one over the other in a zigzag, and a stem),
  and each half of that shape had a false mark of its own.
- A rule that cuts one mark into two heads gives each head its own stem, followed from its own side. A stroke
  that no head owns any more is asked for a head of its own (`symbols.lost_stems`, `symbols.thin_heads`), and a
  beam at its end was read as a thin head. Count the notes that are not there for each rule that makes heads,
  and look at the new ones.
- The list of the notes by the page also knows a note that the page holds where the hymn is typed with it struck
  again (`held`: the moments at which the page does not strike it, and the page's length). The scorer takes
  such a note out of its typed chord. The finder for these places sees only a place where the reader reads the
  long note, and a bow that may be a slur stays off the list.
- A chain of runs loads the code copy anew for each run. Change a copy only when no chain reads it, or make a new
  copy for the next form of a rule.
- A filled mark with no stem is a note only by the whole shape of a printed head (`symbols.STEM_GONE`: a
  slanted oval as large as the heads of the page, with paper around it): a rest, a dot, the end of a slur and
  the half of a quarter rest are filled marks too, and no one measure parts them. A census of every such mark
  of the clean pages, each looked at, gave the three measures.
- Ink in the column of a stem can be the next note's. A stem that is put together from pieces
  (`symbols.GONE_STEM`) is taken at one side only, and not where a short stem still hangs on the head at the
  other side: a hand that draws short stems sets the next note's stem into that column.
- The flag of a stem that stands apart from its head is itself a mark as large as a head. A guard that asks
  whether wide ink "is another head" took true flags away (8 eighth notes).
- A head without a stem stands a little beside the notes that it sounds with and can be read as a column of
  its own, which moves the notes after it. A rule in two halves is read with each half off: the first half
  alone lost 2 notes that the second half (the stem) brings back.
- A new kind of note that is read moves the count of the drawn notes: the typed notes of a recitation that the
  reader has no note for are counted apart, and a chant page draws them as heads without stems (22 notes).
- A small mark in the rows of a staff line is the tip of a tie only by the whole shape of the tie
  (`symbols.DOT_TIP`): the bow comes out of the line again at the right of the mark, long, and slim and near
  the line where it begins. A hand sets its true dots on the staff lines, and a thick copy prints them into
  the lines: the mark's place alone gained 51 notes on all scores and lost 171 (17 November 2026).
- A piece of ink beside a mark is measured where it begins, not by its box: a bow that is joined to a stem or a
  bar line has any box, and "a long, low piece past the line" was a beam, a slur and a blot of joined ink.
- A next form of a rule that is not a part of the form before it is read on the pages of the widest form.
- A wrong reading can be counted as right: a whole note that is tied to a half note was read with a false dot
  and had the six beats of the two together. Look at a note that a rule loses on the page before the rule is
  narrowed for it.
- A tie is joined only where the first note ends as the second begins. Where a bow is found and its tie is
  not counted, look at the length of the first note and at the head at the end of the bow before the bow.
- A second reading of a page at another limit of the ink gives no rule: the notes that only the other reading
  has are false twice as often as true, and where two readings give a note two lengths the first is right
  three to four times as often. The bar does not choose either: a wrong length fits its voice in most cases.
- A limit for how round the inside of a head is refuses a small inside with a ragged edge (0.83 of its hull
  against 0.85), and a milder limit fills the bowl of a flat and the paper in a natural (37 notes gained and 62
  lost). Paper that misses such a limit by a little is kept in a layer of its own that is not filled
  (`layers.RAGGED`), and is asked by its own shape where a head is missing (`symbols.RAGGED_SLIT`: a slit that
  rises to the right, with a stem). A census of every such piece in a mark that was read as a filled head gave
  the shape. A layer that is not filled leaves the clefs and the keys as they were.
- A hollow head that is not read leaves the pieces of its rim as small filled heads and the ink where two
  heads touch as a sign, and a false quarter note that two voices share outvotes the true half note of
  another voice. Before a wrong length is taken for a matter of the bar, look at the heads of its column. A
  piece that a head replaced owns no stem, and a sign in the columns of such a head is no sign
  (`symbols.OPEN_BESIDE`).
- A page that holds more music than its typed hymn is counted in a window, and changed lengths can move the
  window as they move a layout: a score then loses notes and syllables that no rule read wrongly. Compare
  `window` with `layout` in the two results.
- A new head that is read in both voices costs nothing in the count: a split of its two stems gained nothing.
- A filled mark with no stem that stands past a read head, at the end where that head's stem begins, with the
  stem's column at its edge, is the next head of that chord or the other voice's note whose own stem is lost
  (`symbols.CHORD_STEM`). A mark along a stem is a sharp, the bowl of a flat or a letter as often as a head (20
  right of 75), and no measure of the mark parts them: the place past the end of the stem does. A whole note on
  a ledger line is no hollow mark for the reader (the line cuts its inside into slivers): a mark that closes
  in paper is not taken.
- The heads that the first form of a rule makes are listed with the scorer's verdict for each note (right, only
  a wrong length, wrong, not there) and with the rule's measures: one reading of every page with wide limits
  then shows which part of the rule and which limits bring wrong heads, without a run for each.
- A new head changes what the older rules see beside it. A hollow head near the far end of a stem that it
  shares with another head is the loop of a flag for `without_flag_loops`: a true half note vanished beside a
  new head, and the new head became an eighth note. A wide guard for it (no head at a hollow head) cost 2
  notes; the guard for the one case (a hollow head within `LOOP_NEAR` of the stem's end) gained 2 and lost 1.
  Before a guard that costs notes is dropped, look at a note that it saves on the page and find the step that
  loses it.
- A rule for marks that an older rule also reads runs after the older rule: the heads that
  `symbols.gone_stems` reads by their shape keep their own voice (before it, 3 notes fewer).
- The figure of the notes that are not there is taken from the reading with the words, as the other figures
  are; the reading without the words gives a few fewer.
- A print that pressed the ink out of the middle of its filled heads leaves a pale speck there, and no limit for
  the hole parts such a head from a half note on every print (0.6 of the usual hole in the place of 0.4: 17 notes
  gained and 83 lost on the clean copies by a census). The page shows the print (`symbols.HOLLOW_PALE`): its
  specks come in every size up to the limit, and its half notes are wide open. The share of the filled heads
  with a speck alone also named a copy by hand, whose specks are tiny and far under its holes, and a thick copy
  whose holes are small: 17 gained and 6 lost on all scores, and each of the two further signs alone still lost 2
  to 4. The rule acts on the four pages of one engraving. Say so where a rule is a rule for one print.
- A sign of the page is counted as the reader counts it, from the marks of the page before the notes are made.
  A count from the read notes named other pages than the rule then acted on.
- A note that is read longer than it is typed is looked at with the columns around it and with the typed notes
  of every voice of the staff. The page's are: a half note under which another voice strikes the same pitch, one
  note of a typed chord that the page prints longer than the others (the list's `alone`), and a note that one
  voice holds while the other moves. Such a place goes on the list whole, with the note that the reader then
  loses too (a dot at one head of a chord). A page that prints a response more often than the hymn is typed
  lines a note up with another typed note: that is the count's line-up, not the page (of 47 such notes 5 were
  the page's).
- The clean pages of the wide test are built once and read by every run. After a change of `staves.py`,
  `systems.py` or `page.py`, every page is built anew and compared with the stored one (staves, systems, places
  and the picture; blank columns at the right do not count; a script outside git, with the wide test): in round
  47, 20 of the 657 stored pages were a week older than the code. Read as the code builds them, one clean score
  lost 46 notes (two systems joined into one) and another gained 19, and no round had seen either. The change of
  the pages is reported apart from the rules of the round.
- A staff is followed past the end that the comb gives it, each of its five lines by itself, window by window
  (`staves.ENDS_ON`): a pencil ring, a paperclip, a faded stretch or a bend hides the lines from the comb. What
  the first forms met: a brace, a punch hole and the black edge of a page are filled at the rows of the lines too
  (a line is thin, with paper half a staff space over or under it); a chord and a bar line are dark for a few
  windows only; two pieces of one staff are followed into each other (the longer stays). A page that bends at
  its spine spreads the lines unevenly, 0.8 to 1.35 staff spaces apart: a fit to five evenly spaced lines refused
  true staves, so the rows only have to stand in order, 0.65 to 1.5 staff spaces apart (`staves.ENDS_GAPS`;
  without it two lines were followed onto one). A slip of paper that is pasted on carries its staff at other
  rows, and the nearest rows are then one line off: a staff has five lines, and a sixth one where the first is
  missing tells (`staves.ENDS_SIXTH`).
- A staff that grows moves the cuts of its system by a row of pixels, and notes anywhere on the page change with
  it. A rule for the staves is judged by its staff ends, each looked at on the page; the notes that a score
  loses are looked for across the page before the rule is narrowed for them (five scores lost 12 notes, and
  each of their staff ends was right).
- A mark that is no note can count as one, hold a line-up or carry a vote of its column. A rule that takes false
  marks away (the loop of a flag, the room of a double bar line, the box of a natural, read as half notes by
  their closed paper: `symbols.HOLE_UPRIGHT`) loses notes by the count where every mark that it took was false.
  Look at each mark that is gone in a score that loses, and say so. The lengths that then change by the vote of
  a column are another cause, listed apart.
- A step that takes marks away runs after the flags are counted (`count_tails`): the loop of a flag is a mark
  on the stem of its note, and older rules read the flag from it. Taken away before, two eighth notes became
  quarters.
- The inside of a printed half note lies on its side and rises to the right; closed paper that stands upright
  is something else. Two guards came from a census of every hollow mark with one stem: a hole that a thick copy
  all but closed has no direction (the area of the inside), and one print sets an upright inside between two
  thick sides (the ink at both sides of the hole).
- An opening line joins two staves at one left end. Where the first system of a page is set in and the next one
  stands close under it, the bracket and the clef of the next system cover the narrow gap as a weak line: such
  a line counts only where the notes of the two staves stand in the same columns (`systems.OPEN_WEAK`; the weak
  lines of LitChoir's pages are in step from 0.52 on where they join a system and up to 0.13 where they do not).
- The scorer sets a typed note apart as recited where the reader has no note for it in a run of five equal
  pitches. On a clean copy a printed note that is not read hid there (15 notes of nine scores, and the count of the
  drawn notes moved with the reading). Since round 48 the notes that a clean copy does not draw are a matter of the
  page: the clean scores whose pages show a reciting note or a held ison are a list with the wide test, outside
  git, each looked at on the page (9 scores), and on every other clean score such a note is missed. Compare
  `apart` of each clean score in two results beside the notes gained and lost.
- The count of the notes that are not there, by parts, holds more than marks that are no notes: the notes of a
  page that prints more than its hymn types (one clean score that is typed as a unison: 57), the breves of an
  ison that is counted by its letters, and a note that is given to both voices of a staff (since round 78 such a
  head counts once, see below). The sheets staff by staff show the marks (470 of 839 after round 47). Look at the page before a figure of false notes is taken
  for the reader's, and sort them by sight before a rule: of 80 looked at, no kind held more than a tenth.
- The thick stroke of a final bar line or of a repeat sign is wider than a stem, so it is no slim ink: the staff
  lines cut it into pieces as high as a staff space, which were read as filled heads, with the thin line beside
  it as their stem (`symbols.THICK_BAR`: the columns of the mark are ink over the whole height of the staff).
  The heads of a chord taper towards the lines between them: of 15,057 true notes of the clean copies none had
  such columns.
- A sign that is read as a note is told by its whole shape and by where it stands (`meter.COMMON_BOLD`,
  `COMMON_AT`: the bold C of common time). Its height and its place on the middle line also fit an eighth rest,
  a double sharp and two whole notes one over the other; each of the 61 such pieces of the clean pages was looked
  at, and what only the 39 signs share is the bow: the left edge stands furthest left in the middle rows, where
  the others have a waist. The two other pieces with a bow stood in the middle of a bar: a time signature stands
  after the clef and the key or after a bar line. The copies by hand showed what the clean pages did not: of 149
  further pieces with a bow, 14 were flats that a hand draws large (the stroke stands at the left over the bowl),
  so the two ends of the C must both turn to the right (`COMMON_ARM`). A thin C by hand with one short end is left
  out on purpose. One print parts the two ends of the C from its bow (`COMMON_ENDS`: 44 further signs, each looked
  at). A sign takes the heads in its columns only in the rows of the staff (`COMMON_ROWS`): one print sets a held
  note under the staff below the sign, and the first form took that note with it. The C of the fresh set's
  engravings has a short lower end and does not pass; no page of the fresh set reads it as a note.
- A rule that takes a false note away loses notes by the count where the false note had counted by chance (a piece
  of a C that stands at the pitch of the first note) or had held a line-up: six notes on four scores of one print.
  List the typed notes whose verdict changes and the notes of the page that are gone and new; where no note of the
  page is new and every gone note is a piece of the sign, the rule stays as it is.
- A limit that is counted in thicknesses of the staff line is a limit of the prints that it was set on. A guard for
  two specks in the rows of a line (`symbols.LINE_OUT`) parted the half notes of the clean copies from worn filled
  heads at 0.4 thicknesses and lost 30 half notes of thick copies and copies by hand: their lines are 7 or 8 pixels
  thick, and the row that the staff gives for a line misses the ink by a few pixels. A census of every scan page
  (348 true half notes, each head labelled by its typed length) gave the measure: the farther speck, in staff spaces.
- A line of the scan (a fold, the edge of a pasted slip, the edge of the page) runs upright past a system at both
  ends; a bar line ends at its staff (`layers.STRAY`). It is taken out only where it stands alone in its row, so a
  head, a staff line and a letter that it crosses stay whole, and its ink is looked for in the next column too: a
  line of a scan leans by a pixel.
- The two heads of a tie stand at one height on the page. A rule that joins a bow which stands free between its
  heads (`ties.TIE_APART`) asks the rows of the heads, not their read pitches: a slur between two notes a step
  apart was joined where the reader had one head a step off.
- The hook of a quarter rest closes in paper on a heavy print (`rests.HOOK`): a guard against closed paper allows
  the one small piece low in the shape that the census of every rest showed (4 of 364).
- A census that spies on a function of the reader keeps the function as it was in one place of the module. Wrapped
  anew for each page, each call ran the one before it too, and a census of 14 minutes ran for 40.
- A slur that passes the ends of two stems hangs on both sides of each at one level, as the beam of a middle
  note does, and the flag of the note before is its witness. It is slim against the beams of its own page
  (`symbols.BEAM_CROSS`: both pieces at most half as thick; 20 such stems of LitChoir's pages, each looked at,
  the slimmest true beam at 0.52). Between 0.5 and 0.6 slurs and a true beam stand mixed: the rule takes the
  part of the census that holds no beam.
- Before a lost syllable is blamed on Tesseract, look at its stored readings at every size and file, and
  replay the one row with each rule off (a script outside git, with the wide test): every one of 18 readings
  held a syllable that the words step dropped. A short word that Tesseract is not sure of is left out
  (`ocr.SURE`); beside a hyphen that was read it stays where the list holds the whole word
  (`ocr.SURE_JOIN`). A reading that drops a syllable can hold only words of the list, and it wins.
- The black edge of a scan beside a row is read as a word. Painted out of the picture that Tesseract gets, the
  false words went and 2 true syllables of the clean copies with them (none gained): the picture stays as it
  is, and the word is refused by its own box (`ocr.SOLID`). A letter fills its column over the row or under
  it, not both: measured in the rows of the row alone, the stems of a bold "ni" filled half of its box.
- The replay of the words hands a rule the columns of a row, not the page. A rule that looks at the ink gets
  the page there by a wrapper of its own; without it the rule for solid ink dropped nearly every word.
- A ragged inside of a half note on a ledger line fails two tests at once (how far it leans, and the rim in
  the row of its middle, which is the ledger line). A wider limit for the lean alone gains 2 notes and loses
  1 on all pages, and not the note that it was tried for.
- A word that every reading of a row holds with the same letters, at each size and by each language file, has
  been read: it is a true word that the list lacks twice as often as a misread (about 20 and 10 of 33 on all
  scan pages), and no measure of the word parts the two. Never mending such a word gained 19 syllables and
  lost 4; counting it as a word that Tesseract is sure of, which the rules for a sure word still mend, gained
  27 and lost 3 (`ocr.MEND_ALIKE`). The sizes of the first file alone agree on more misreads (38 and 10).
- A hyphen at the end of a row does not tell that the next row begins inside a word: many readings end a row
  with a hyphen that the page does not print. Not mending the first word of such a row gained 4 syllables and
  lost 8.
- The curl at the end of a flag is read as a small filled head with a stem of its own. It is told by its place
  and its size together (`symbols.FLAG_CURL`: in the row of a flag that was counted at another stem, at the
  flag's side, and under 0.6 of the area of the page's filled heads); a true head of another voice stands at
  the same place from 0.6 on. Where a rule asks only measures that the stored notes keep, its census is made
  from the stored notes of a run with the scorer's verdicts, and no page is read for it.
- Nothing of the music stands at or past the bar line that ends a staff (`symbols.END_MARK`,
  `layers.END_BAR`): the pieces of a final bar line that a hole or the wear broke, a punch hole, a paperclip
  and the black edge of a scan were read there, with the bar line as their stem. The distance to the end of
  the staff alone does not tell: where a staff ends without a bar line (lines that fade on a copy by hand,
  lines that a punch hole hides) two of three notes at its end are true. The census of 65 such notes named
  the pages that the rule changes (38 by the census, 37 changed).
- A rule that takes marks away runs after every finder of heads. Run before them, the end rule took the
  closed paper between the two strokes of a final bar line early, and a true whole note of that staff was no
  longer read. Look at each note that the first reading loses before the rule is narrowed: the fault was the
  place of the step, not a limit.
- A rule that does not reach the scores that it was looked for can still be right for what its census
  shows. Say so: two clean scores keep the notes that are read in the black of a binder hole, because the scan
  cuts one staff at its last line and the other staff is followed past its final bar line.
- The layer of the insides of heads is read by older rules for other things: a flag is read from the room that
  it closes, a time signature from its cells, and measures of the page come from its hollow heads. Refusing a
  cell between a staff line and a slanted stroke in that layer gained on LitChoir (102 notes and 46) and lost
  on the fresh set (108 and 117). The rule is a late step on the read heads (`symbols.FLAT_CELL`), after the
  flags are counted and after the rules for the loops of flags, and the layers stay as they are. A census of
  closed paper is made from the reader's own layer, not from the ink: the first census took other pieces.
- The inside of a printed hollow head touches a staff line at a point; a cell between a line and a stroke (a
  pencil ring, a slur, the loop of a flag, a piece of a rest or of a clef) has a level side along the line. A
  sharp or a natural close before a filled head closes in such a cell too, and a hand draws a head as a stroke
  along a line: the guard is the fattest ink of the mark against the page's filled heads. It parts on a print
  (0.75 at most against 0.93 or more) and not on a copy by hand, where every stroke is as fat as a head: the
  rule is a rule for a print, and its guard keeps about 27 false notes of copies by hand.
- A staff that the scan cuts or that is followed past its bar line ends in nearly solid ink without a whole
  bar line. A mark past the end of such a staff is no note (`symbols.END_PAST`, by the staff's `end_ink`): of
  18 such notes of LitChoir's scan pages the 7 from 0.6 on are false and the 4 true ones have 0.43 at most.
- A false mark that goes can free a run of recited notes: the notes set apart of a clean score with a
  recitation grew by 2 where a mark at the end of a staff had stood for one of them. Look at the page (an
  empty staff with the words printed over it) before the count of the drawn notes is taken as moved by a rule.
- A word that one reading of a row holds whole is not parted as other readings part it: one clean score
  prints words of one syllable spread under two notes with a line (5 syllables lost on the clean copies, none
  gained).
- The kit's count by parts and its own count staff by staff can differ in what a round moves: two false marks
  that had counted by parts went, and the count staff by staff stayed (6220 to 6218 by parts).
- A filled head and the stem of the note before it, or a head and its sign, close a cell of paper with the staff
  lines, and the whole piece was read as one half note. The layer of the insides stays as it is (round 52); the
  cell is taken out where the marks are made, and the piece is made anew with the brush of the page
  (`symbols.CELL_OUT`). Every such cell in a mark with a filled head gained 10 notes on the clean copies and lost
  10; a census of the 170 cells gave the shape: a thin stroke at one side of the cell and a head at the other.
  A step that makes pieces anew cuts each piece to its own box: the first form stopped on one page.
- Two heads that stand close side by side are a small note beside a chord on one engraving, and two marks of one
  head or a sign beside a head elsewhere. A false twin that is joined to a true note takes the note to its own
  moment. The print's sign is the small head (`music.STACKED_NEAR`): say so where a rule is a rule for one
  engraving, and read it on the PDFs too, because it is a rule of `music.py`.
- An engraved bow swells in its middle and is no thin ink there. Followed in fatter ink, a short fat stroke
  between two heads is a tie too (a hand's slur, a piece of a beam): 3 notes gained and 3 lost on LitChoir, none
  and 29 on the fresh set. The ways of the first form on LitChoir's pages were measured, true and false: the
  length parts them (`ties.TIE_SWELL`).
- Stray ink under the clef is read as a short word, and such a word can hold letters of the list: a reading
  with it then wins over the reading with a true syllable that Tesseract was not sure of (`ocr.CLEF`). A rule
  that takes a word out of a reading changes what the reading is beside that word: whether the row is a row of
  words, how sure Tesseract is of it, and whether it is whole, so that the other sizes are not read. The word
  goes after the row is judged, and a reading that lost it is not whole (`ocr.CLEF_WHOLE`). The replay did not
  show this on the fresh set: the full reading lost a whole row of one piece there. Trace a lost syllable
  through every reading of its row with their fits (a script outside git, with the wide test) before a guard.
- The hymn that is read is left out of the list of words, so a guard that asks the list for a whole word cannot
  act on a word that only this hymn has.
- How dark a word is does not part a smudge from words: true thin letters are far paler than their row too
  (4 syllables gained and 18 lost on the clean copies).
- A rule that gives a note to another voice meets the kit's split of a staff by its voices and the rules of the
  bar. Two whole notes alone in a bar, the lower one for the second voice, lost in three forms; the false note
  that it was tried for comes from the count (a tie into one note of a chord leaves the other alone in its
  column).
- The neck of an inside is asked in the rows of the lines that run through heads. A ledger line that is faint
  inside its head leaves such a neck too, so the rows of the ledger lines count (`layers.HOLE_LEDGER`), but only
  where the line is seen at both sides of the head: the bowls of a bold letter of a title and the paper between
  a slur and a head have a neck in such a row, and no line past them.
- A wider limit for notes that begin together meets a note that sounds with another note of the other voice:
  two stems back to back are one column (`music.ONE_LINE_BACK`) unless the second note already stands in the
  column of a note of the other voice. A note that a column moves can free a run of recited notes on a copy by
  hand: compare `apart` too.
- A rule that follows closed paper from a mark begins at the mark's own inside. A long flag closes a trail of
  small cells along its stem, and the first cell was read as a half note (`symbols.FLAG_TRAIL`); taken from any
  paper in the rows of the head, the trail began at the paper between a staff line and the top of the lower of
  two stacked half notes, and the first form took true half notes (3 notes lost on the clean copies, 9 on the
  fresh set).
- A rule that makes the insides of heads larger changes what later steps learn of the page: `hole_heads` takes
  the page's size of a hole from its read half notes. The halves of an inside that a thick ledger line cuts are
  one inside where they lean (`symbols.HALVES_LEAN`, at ledger lines only: on the staff lines the same shape is
  two heads a third apart as often), and on one fresh page the larger inside let a cell between a slur and the
  lines pass as a head.
- A bow from a head to the same pitch under one held syllable is a tie by the page, and goes on the list of the
  notes by the page with the moments that it holds (`held`). The finder for such places sees both line-ups of a
  held run: the read long note lined up with the first typed note of the run, and with its last. A bow from one
  syllable to the next is a slur, and where it is read as a tie the reader is wrong.
- Two whole notes side by side on one pitch or a second apart are two voices that begin together
  (`music.WHOLE_TWIN`): a print sets a unison of two voices so, and one voice holds no two whole notes in one bar.
  A false note that goes can show a mistake that it hid (a pitch read a step off, a joint between two touching
  whole notes read as a head) and can free a typed note of a recitation: look at both before a rule is narrowed.
- A flat, wide filled mark at the end of another note's stem is that stem's beam or a slur over its end
  (`symbols.STEM_END_MARK`): a printed head is round. The count by parts weighs a wrong pitch at half a missed
  note, so a false note of wrong pitch can hold the line-up of a part: on the fresh set a rule that took only
  pieces of beams lost 6 notes by parts and none staff by staff. Compare the sheets staff by staff before such
  a loss is taken for the rule's.
- A head that two voices share, with a beamed stem one way and a stem without a flag the other way, is a quarter
  note in the free voice by the page (`symbols.SHARED_TAILS = 'flags'`: 62 notes gained and none lost on the fresh
  set). Typed hymns of LitChoir sing such a place as eighths in unison, and a copy by hand draws its beams as boxes
  that the reader misses at one stem: the rule was read place by place on LitChoir, with the list of the notes by
  the page. The free stem must end in paper (`SHARED_FREE`; a box beam, a slanted beam and a flag leave ink there),
  and the beam must go on from the shared head to the next note: the free voice holds its quarter under that
  note. Where the shared head ends its beam the next head is both voices' again, a quarter does not fit, and a
  hand left the flag out. A rule can gain by a misreading that it does not know: a slur at a stem's end read as a
  beam from the left gave 2 true notes of a clean copy by chance, and the guard took them. Look at what a gain
  stands on before a guard is judged by it.
- The list of the notes by the page also knows a note of a chord that the page prints and the typed hymn leaves
  out (`add`), and a typed note that the page does not print for a part (`drop`: the part holds the note before
  it, which the list gives the page's length).
- A rule that moves a head from one stem of a column to the other reads the stems that the column shows. The end
  of a tie that runs into a chord is a short stroke at its side, read as a stem, and the cell at the tie's end is
  a hollow mark: one place of the first forms of `symbols.MIDDLE_KIND` gave a quarter note the flag of that stroke.
  The count by parts called it a gain, and the count staff by staff (4 lost) and the page did not. A stem that the
  head takes must leave the column as the other stem does (`MIDDLE_OWN`). Count staff by staff for every rule
  before the kit's scorer runs, and look at a gain by parts on the page too.
- Two specks that a line cuts out of a filled mark, one over the line and one under it, are the inside of a half
  note that lies flat (`symbols.LINE_HALVES`), and also the paper inside the 4 of a time signature: those were
  read as notes that are not there before, and the rule took them away. Where a page's worn heads hold specks, the
  specks lie in the rows of the line; the count of the page (`slit_page`) did not part these heads.
- Of the notes that the clean copies read a semitone off, about two in five have a printed sign that is not read,
  and most of those signs touch their head or a staff line. The stroke of a sign is followed past its own ink into
  a staff line, over a gap of paper, and the measures of its ends then read paper: a flat whose lowest rows hold no
  ink of its own (`starts.FLAT_FOOT`, cut at its last row of ink, and still a flat's height) and a heavy sharp whose
  strokes are one mark (`signs.JOINED_ENDS`, measured from its first to its last row of ink). Cut so, two faint
  hollow heads one over the other passed as a sharp: a sign whose ends were cut stands before its head, not in its
  box. A filled head with ink over it passed as a flat in the first census: a flat is about two staff spaces high.
- A heavy sharp whose middle closed is read as a filled head, with one of its strokes as that head's stem, and the
  stem hides the stroke from the signs. The guard for a sharp of two strokes (`SHARP_HEAD`) does not see a sharp
  whose two strokes are one mark: such a head is no head where it lies in the columns of the one stroke and the
  stroke has the ends and the closed paper of a sharp (`signs.JOINED_HEAD`).
- A natural closes paper between its strokes and bars, and that paper was read as a hollow head with the right
  stroke as its stem, which lay on the sign and hid it: a head stands beside its sign, not between its strokes
  (`signs.NATURAL_OWN`). The right stroke reaches down past the head after the sign and was that head's only
  stem; where another head of its column has a stem, it is no stem (`signs.NATURAL_LONE`). A half of a rule that
  acts only on what the other half finds changes no page alone, and is counted with the other half on.
- A whole note that touches the half note of another voice on one stem line is read with that note's stem. Of the
  hollow heads that share a stem it stands at the far end from the stem's end, and its inside leans back, where a
  printed half note's inside rises to the right (`symbols.CHORD_WHOLE`, by `symbols._hole_axis`). The angle alone
  took a round inside by hand, a letter d and a stroke by hand: a round inside has no direction, so the inside is
  also asked how long it is against its width. Such a whole note was one head of a chord for the rule that makes
  the heads of a chord as long as each other, which then cut a printed dot from the chord's lowest head.
- An entry that takes typed notes out of the count (a stretch that a scan does not show) is a claim about the page,
  and it is looked at again on the page as the lists by the page are: a stretch of one clean score that round 37
  listed as a system that the scan shows only in part is printed whole, and its 12 notes had been read right.
- A page that a hand wrote whole inside a clean score (responses written in pen on blank staves after the printed
  pages) is a page by hand: its notes go on the list of the notes that a hand changed, for every staff of the
  page, and the typed hymn does not hold them.
- A beam is straight and a slur arches. A thin line between two stem ends that both stand on staff lines is hidden
  in the lines at both of its ends, and a tie that arches over a half note between two such stem ends looks the
  same by its ends: the way between is a beam only where its ink is straight (`symbols.THIN_BEAM_HIDDEN`; the
  rows of the tie bent by 0.22 staff spaces from a straight line, those of the true beam by 0.01). A slim beam is
  slim at both of its stems: where the piece at one stem was taken as a beam, the slim piece that faces it at the
  next stem is that beam (`symbols.SLIM_BOTH`).
- Notes that sound together agree on a dot that the print wore smaller than a dot too: such a speck is a dot where
  a dot of another head of its column stands in the same column (`symbols.DOT_SPECK`).
- Notes begin after the clef and the key signature, but the end of the key signature that the reader finds can
  overshoot a first note that stands close to it, and only a finder that reads a head from its stem
  (`symbols.thin_heads`) then reads that note: of 13 heads inside the start on all scan pages 5 were true, and
  the bowl of a flat of the key with a pencil line beside it was one of the false. No rule by the place alone.
- A filled mark half again as long as the page's filled heads and under 0.7 of their fatness is a piece of a slur
  or a beam, a fermata or a letter on a print, and a head on a ledger dash on a copy by hand: no rule without a
  sign of the print.
- A combined copy of the code is made from main's own files, not from the copy of the round before: a change that
  went into main with the review was missing from two copies, and patches made against them carried it.
- A mark that the reader leaves without a head, because it is too high or because a neighbour's stem leaves it too,
  can be two heads of two voices that touch (`symbols.GLUED_TWO`). Such a cut meets what any large mark with stems
  at its sides is: on a thick copy a bar line or a stem runs through a box of staff lines and leaves it up and down
  in one column, and a bar line, a clef, two whole notes and a thick head were cut too (10 of 23 cuts in the first
  form, each looked at). A head holds a circle of ink half as high as the page's heads, and the pieces of lines
  and signs do not; a half note whose rim is thin does not either, so the guard costs such a pair. Paper that two
  heads close between them with a line, a stem or a sign reaches the cut, and is no hole of either head.
- A limit of a rule for one engraving that misses its next case by a little is widened only after a census of
  every pair that the rule's other limits take, on all clean pages: `music.STACKED_NEAR`'s paper from 0.25 to 0.3
  staff spaces took one more pair there, the true one, and changed one page.
- A staff count against a base run whose sheets the kit's scorer wrote over shows the kit's hymns as gained or
  lost: round 63 read 43 notes gained staff by staff where 24 were. Score both runs again before every count
  staff by staff, also the base of the round before.
- A print can set the ison's note as a breve under its letter (`drone.BREVE`): a hollow head between two short
  bars. The bars are no sign without the letter: 153 hollow heads of LitChoir's chant pages and 108 of the fresh
  set have them, and are notes. Taken under any letter of the page, the breve that restates the ison at the start
  of a staff went too, and 4 true notes with it: a hand draws the melody's half note between the ison's bars.
- A printed whole or half rest is written into the music for the voice that it silences (`reader.REST_VOICE`), and
  the wide scorer then gives a note under which the other voice rests to its own part only, not to both as a
  unison. The stems say nothing of a part that sings alone: a print and a hand stem it by its place on the staff,
  and taken from the stems the rest went to the singing alto (8 notes lost). The singer of a bar of one voice is
  the voice whose notes stand nearer on the page in the bars of two voices.
- The reader's onsets do not count a rest: where both voices rest for half a bar, the notes beside the rest close
  the gap and the bar looks like one of one voice. A whole rest hangs from a line and says that one voice rests
  the whole bar; a half rest says so only where a note stands in its columns or the notes beside it stand as close
  as the bar's notes do (3 notes lost where a shared half rest was given to one voice).
- On a thick copy the bow of a tie that lies along a staff line between beamed notes is as solid and as square as
  a rest, and a hand's bold start of a slur on a line passes as a half rest. A rest stands apart from the stems
  (`reader.REST_APART`: no stem within 2 staff spaces at both ends; no true rest of 480 blocks has one). A false
  rest can gain notes by chance in the count: the first form gained 1 there, and 2 by a slur still stand (say so).
- A fixed order of the parts of a fresh piece can stand crosswise to the voices of a staff that divides for a few
  bars, and a lone note that the count gave to both parts held its line-up. Score the piece with the parts the
  other way round before a loss there is taken for the reader's.
- A printed quarter rest names its voice by its place on the staff, the upper voice's high and the lower voice's
  low (`reader.REST_QUARTER`). A gap in a voice's notes does not name it: the other voice can leave a gap at the
  same place, and the first form gave a lower rest to the upper voice (2 notes lost). The rest is one beat, the last
  before the voice's next note: the reader's onsets do not count a rest, and a gap is as long as the notes that
  were not read.
- A form of a rule that acts where no form before it acted is read on every page. Round 65 read its later forms on
  the pages of its first form, and main read on every page changed 5 pages more (9 notes that are not there
  fewer). Two of those stand on false rests: the flat base of the 2 of a time signature (3/2) is as solid and as
  wide as a half rest that sits on the bottom line, and no measure of the block parts them.
- A rule of the scorer that gives a chord of one voice to its own part where the other part holds a long note
  loses where the reader misreads that long note (50 notes on all scores, 4 on the clean copies): the misread note
  takes the tops of the chords with it.
- A word that a hyphen leaves open at the end of a row is not whole: the rest of it stands in the next row. Not
  mending such a word at all lost on all scans (3 syllables gained and 8 lost): a misread letter inside the open
  piece is mended rightly as often as not, and a row that keeps an unmended word is no longer whole, so another
  size wins. A census of every mend of an open piece in every reading parted the kinds: a letter added at its end
  makes the word that the next row goes on from ("foun" to "found"), and only that mend is held back
  (`ocr.MEND_OPEN`).
- Two whole notes one over the other with no stem near them are the two voices of their staff (`music.WHOLE_PAIR`),
  and each votes on its length. Set after the vote, the voices alone gained 1 note and lost 4: the gain is in the
  votes, where two voices count twice. A pair that votes twice carries a misread dot twice too, and the losses of
  the first form were one engraving's last chord of dotted whole notes, typed as whole notes: the page was right.
- The count splits a staff by its voices: the voice that sings higher on the whole is the upper part, and a voice
  counts from a tenth of the staff's notes. A print stems a part that sings alone by its place, so voice 1 of a
  lower staff can be the bass, and a new voice label then crosses the split (a clean score lost a note and a
  syllable). A page's staff holds too few notes to choose the voice by its mean (4 notes of a clean score lost).
- A sign that the reader finds and does not use is traced through the step that gives signs to their notes
  (`signs.note_signs`): one reading of the clean pages that writes down every sign of the pairing with the place
  where it is dropped, set beside the notes that are read a semitone off, named the causes (a census outside git,
  with the wide test). The column of a stem is that of its far end, and a stem that was followed into a slur ends
  beside its own ink there: a stroke is asked against the stem's middle column, and it is no part of the stem
  where a column of paper parts the two (`signs.STEM_APART`).
- A wrong sign costs every later note of its pitch in the bar. A rule that took a head read from its stem
  (`symbols.thin_heads`) where that stem is a stroke of a sign gained 2 notes on LitChoir and lost none, and lost 6
  on one piece of the fresh set by one true head (`signs.THIN_SIGN`, off). Its first form asked only the columns
  of the sign and took a true head over a natural that stands lower on the staff: a sign is asked in its own rows.
- The staves of a system begin in the same columns. A staff that shows no clef and no key of its own is given the
  room that the page's other staves take from their left ends, and where a scan cuts the left end of a system that
  room reaches past the first notes. Such a staff begins where a staff of its own system begins that shows its start
  (`starts.SYSTEM_START`): only earlier, and only by a staff with the same left end. A later start takes notes
  away (72 staves when each page is read alone) and was not taken. A census of the starts that reads each page
  alone names more pages than the reading of the hymns changes (six and two): the key and the clefs of the page
  before go into a start. A page whose staves are found at odd places gave the limit for the left end.
- A word that a row leaves open goes on in the first row under the same part's staff in the next system, and the
  words step hands that row the open letters (`ocr.MEND_BEFORE`): the rest of the word is no word of the list
  alone, and was mended into one or lost to another reading. A piece of one letter is a stray stroke as often as
  a letter (5 syllables gained and 2 lost on all scan pages with it, 5 and none without). A first word that is
  taken from another reading can be longer than the word that it replaces, and the words of the row in its columns
  go with it. A syllable too many costs nothing in the count: the replay prints every row that such a rule changes
  (`CARRYSEE`), and each is looked at.
- Two stems that meet end to end in one column, one going down from the upper head and one going up from the lower,
  are one stroke with a head at each end, and no chord has one. The head with the short stem is a mark at the end
  of the other note's stem (`symbols.STEM_MEET`: a tick by pen, the end of a bow; four such pairs on LitChoir's
  pages by a count from the stored notes, none on the fresh set).
- Two half notes a second apart at one stem are one mark, and only one of the two insides is round enough to be
  filled; the other is a ragged slit in the box of the head that was read (`symbols.SLIT_BESIDE`: of 15 such slits
  of the clean pages 2 are a second head, far beside the head's own inside in a wide box). A chord that a hand drew
  over holds more pieces of inside in that box, and the new head there took a syllable from its note: only the
  full reading with the words showed it. A head that a rule should make and does not is traced in a copy of the
  code that numbers every way out of the loop.
- A head that two voices share at the end of a line is tied twice where the next line sets the two voices side by
  side (`ties.TIE_BREAK_BOTH`, a rule for one case). The list of the notes by the page also knows a note that the
  page prints for a part at a moment where the typed hymn gives the part none (`own`).
- A rule that takes a stem back from an oval because the side of another oval was followed as that stem asks the
  other oval for the shape of a whole note, and the stem for ink of its own (`symbols.WHOLE_STACK`). A hollow mark
  without a stem, with its edges in line, is also the paper that a slur, a stem and the staff lines close in, a cell
  of a sharp, and a whole note of the next staff: of the 32 stems that the first form took back, 4 were such stacks,
  2 the stems of true half notes, 11 the strokes of sharps and 7 the stems of the 4s of a time signature by hand. A
  stroke of a sharp goes on past its cells; the side of an oval does not. The stem's own ink is counted outside the
  ovals and outside the staff lines.
- A cell that is nearly the inside of a whole note is one only beside the inside of a whole note (`layers.WHOLE_OVER`).
  Beside any inside that was taken, 9 of 10 such cells were loops of a clef by hand, and each moved notes far from
  the clef: the page's measure of a hole comes from its read insides. A new inside of the layers is listed cell by
  cell, with the cell beside it, before the notes are counted.
- A rule that leads a stem on over a gap of paper reads whatever stands past the end of any stem: a second beam,
  the line of a bracket, a bold slur over two stems (26 notes gained and 272 lost in its first form; of 88 stems
  that were led on over a gap in their own column, 3 were right). The cause on the page was a strip that the copy
  left white across the whole staff, and the rule asks for the strip (`symbols.STEM_BROKEN`). Ask for the cause
  that the page shows, not for the look of the stem.
- Two strokes whose ends were cut out of the staff lines are a sharp only before a head (`signs.PAIR_LINE`), as a
  joined sign whose ends were cut is: on a thick copy the two sides of a hollow head's rim stood as the strokes of
  a sharp do, inside the head.
- A new head that shares two stems with the head over or under it takes the stem that does not pass that head:
  the upper head goes up and the lower one down (`symbols.HALVES_ACROSS`). Given the other stem, a true new half
  note cost a note in the count of a score with one part.
- A rule that compares the heads of one stem meets one head that was read twice, which is its own neighbour: the
  heads stand a third apart or more. On a ledger line the line and a dot at its end are one mark with the head,
  and the width of that mark says nothing (`symbols.WHOLE_DOTLESS`).
- The counts hide most of what a first form does wrongly. Every note that differs between two readings is cut out
  of its page and set on a sheet with the notes before and after (scripts outside git, with the wide test): of the
  79 places that the first forms of round 71 changed, 25 were right for the rule's own reason, and the counts
  showed 20 notes gained and 5 lost. The page is then read alone with each rule of the round off, to name the rule
  of a place.
- A print of its own needs its own reading: four clean scores are one music typewriter's, and their pages lost
  notes in four ways that no limit of the other prints covers (`symbols.SIDE_TWO`, `WHOLE_FOOT`, `LEDGER_CLOSE`,
  `DASH_PAIR`). Each way is a shape of that print: a ledger line no wider than its note and set 0.7 of a staff
  space from the staff, two voices' heads side by side at one stem line, and the head on the dash glued to the
  head on the first line. Read the pages of such a print together, and say in the code that a rule is a rule for
  one print.
- The shapes of such rules meet other things on pages that were never like them: the bowl of the letter p of a
  dynamic mark is a hollow oval with a level line under it, and the strokes of a tremolo across a stem are two
  parts at one stem line. The fresh set showed both (35 notes lost by the first forms, 1 gained). The guard comes
  from the true cases of LitChoir, not from the pages of the fresh set: the eleven true whole notes stand alone in
  paper, and the true pairs are as fat as the page's heads.
- A rule that cuts one mark into two leaves two heads where the reader's other rules expect one mark. Keep the
  box of the whole piece on each part (`symbols.DASH_OWN`): the page's measure of a hollow head's inside is taken
  from the read heads and counted the pair twice, the rule for a whole note beside a stemmed head took the stem
  from the part that carries the ledger line (which makes it wider), and the rule for a whole note that touches a
  chord took the stem of a part whose inside the ledger line cuts into slivers. Each cost notes or made false
  ones, and none of them showed in the first counts.
- A census of the pieces that such a rule cuts is measured on the whole piece, not on the halves that the cut
  makes: the cut ran through the inside of a half note, the inside leaked to the edge of its half, and the
  measure read 0 where the shape was plain. Measured on the whole piece, the paper that the ink shuts in parts a
  true pair (0.09 staff spaces squared at most) from a chord of half notes (0.28).
- A step that is written for a case and changes no note on any page is switched off, with a line that says what
  it was for (`symbols.DASH_STEM`, `SIDE_WHOLE`). Read it off on every page the round touches before saying so:
  a guard's own page reads as main while the guard is on, so it is only in the list of the round's pages.
- A run of notes a step off on a sheet of mistakes is compared across the scans of its hymn and with the scorer's
  count before a rule is written for the pitches: one note that is not there pushes the sheet's line-up, and
  every note after it shows as a wrong pitch (19 mistakes on a score that the count holds at 322 of 326, and 10
  without the false note). Find the note that is not there first.
- A long flat mark between the ends of two stems is their slur or their beam and no head
  (`symbols.STEM_END_SPAN`). Its census needed no page read: every read note whose mark is long and flat, from
  the stored notes, with the nearest stem end of another note at each side. A note that is not there and that
  both voices of a staff were given counts twice among the notes that are not there.
- No ledger line of a head lies past the head (`symbols.LEDGER_OWN`). The rule was written for one chord, which
  it does not mend, and its first runs gained notes elsewhere. A rule that gains where it was not aimed is not
  kept unread and not dropped unread: every head whose rows it cuts was listed and looked at, and the comment in
  the code says what the rule was measured to do (a chord on two ledger lines, and a hollow head whose rim one
  print draws as level and as long as its ledger line).
- A reading that was right by a wrong count is lost when the count is mended: a half note by hand on top of its
  dash was read right because its rim counted as a second ledger line. Such a note is said in the worklog and
  goes on the list of what is left; the rule is not bent for it.
- A chain of scoring that a restart cuts leaves its earlier files whole and its log without the last line. Look
  for the last line of a script's log before its figures are used, and run the steps after the cut again.
- A stem that is as long as its system is high is a line of the system: a bar line through the staves, or the line
  that opens or ends them. A mark that hangs on it is a head only by its own shape (`symbols.LINE_MARK`): a slur
  across the line, the tail of a hairpin, a letter of the dynamics and a number of the time signature were read
  as notes there, and the cell that the line closes with a staff line and a stroke as a half note. A hand draws
  a true half note whose rim is the bar line itself. The direction of its inside did not part it from the cells;
  its size did. The line of a mark that goes is a bar line again, and the lengths of its bar change with it: look
  at those too.
- The letters of the dynamics are told by the shape of the letter (`symbols.F_SIGN`, `P_BOWL`): the stroke of an
  f is short, leans and has a crossbar; the bowl of a p is the top of its letter, with the letter's bold stroke
  under its left half. A step for the paper between the two letters of an ff asked, in its first form, for one
  stroke of the shape of an f at the mark, and took 38 marks on 30 pages, nearly all of them true notes of copies
  by hand: a short stem by hand leans, and the ledger line lies across it. The step had been added after the
  rule's census and tried on a few pages only. A step that is added to a rule gets a census of its own on every
  page before the full reading, and it asks for the whole shape of its one thing (two letters on one crossbar).
- A change that lets more pieces into an older finder changes what the finder does with the pieces that it had.
  The sign of cut time is higher than the C of common time; with the higher limit a flat of the key came in, was
  grouped with the C beside it, and the C was no longer tested alone (a new note that is not there, on a page
  that the rule was not written for). The new pieces stand alone, and the old ones are grouped as before.
- A note that is not there and goes can show the weakness of another step. On the fresh set eighth notes at the
  end of a bar became quarter notes where the letters under the staff went: `music.BAR_FULL` fills a bar whose
  eighth rest it does not count. On a copy by hand a dotted half note lost its dot in the vote of its column,
  where the other staff's dot by hand is not read. Say such a note in the worklog, find the step that loses it,
  and leave the rule as it is where every mark that it took was no note.
- A gain by parts on a copy by hand is set beside the sheet staff by staff too: a score gained 8 notes by parts
  where its sheet shows 1 lost, by the line-up of the count; and where the recited notes set apart grow with a
  gain, the gain is the count's.
- A hand's change of a clean copy is listed by what the print shows. Where a hand crossed out the printed rest
  after a printed dotted half note, the page prints the dotted half note, and the list of the notes by the page
  holds its length. Where a hand crossed out the printed dots themselves, the notes go on the list of the notes
  that a hand changed.
- A census at the reader's own step costs one line (a list of the module that the step fills where it is set)
  and gives the measures as the rule will see them. Of 246 hollow marks that lie on a sharp of two strokes
  nearly all are hollow heads whose own two sides pass for the strokes; the one whose closed paper goes on to
  the mark's edge is the paper between a heavy sharp and its note (`signs.SHARP_ROOM`, a rule for one case).
- The fresh set's reading with the words is a chain of readings of the pages that each round changed, and the
  reading of its notes reads every page. Set the two beside each other piece by piece at the end of a round:
  five pieces held pages that were older than main (round 74), and they were read again.
- A page that prints a stretch of its hymn once more than the hymn is typed (a refrain that the page draws with
  its notes after a verse, where a hand's remark made the typed hymn leave it out) is told to the scorer with its
  place (`more`), as a stretch that a scan does not show is. Counted in a window, such a page showed 53 notes that
  are not there on one clean score, and 5 with the relation. The count of the printed notes and syllables grows
  with it, `AS_TYPED=1` gives the figures of the round before exactly, and the reading before the round is
  scored again before a rule is compared with it.
- A rule that says where a key signature ends moves the start of the notes of its staff. The first form of the
  rule for a bold key signature (`starts.KEY_PLACES`: the page's key and the staff's clef say where each sign
  stands) moved the starts of 185 staves. It is a guard now: it acts only where the notes would begin before the
  last sign of the key, and only moves their start later (21 staves on 18 pages). Other marks stand as a sign
  does: a quarter rest after a flat, and the dots of a bass clef at the place of its first sharp.
- A wider limit of an older finder is not set in the place of the closer one. The numbers of a time signature
  that begin 0.3 staff spaces from their lines in the place of 0.2 (`meter.TIME_LOOSE`) read 44 true signatures
  and 8 false ones, and lost a true one: two flats of a bass staff's key, one over the other, and a heavy sharp
  fill the two halves of a staff as two numbers do, and a sharp beside true numbers passed the wider limit, was
  grouped with them, and the group was no signature. The closer limit is read first and keeps what it finds;
  the wider one adds numbers in other columns, and at the start of a staff only after the key signature (the 7
  signs of a key began 1.2 staff spaces or more before its end, the 16 true signatures after it).
- No count shows a false time signature that takes no note. The stored pages of a run hold the time signatures
  and the ends of the starts of each staff: two runs are set beside each other, and each changed signature is
  looked at on a tile that is centred on its own staff (scripts outside git, with the wide test). A tile that is
  centred on the notes of the staff shows the wrong rows.
- A time signature that is read is the time of the bars after it until the next one that is read. Where the
  page changes the time back with a sign that the reader does not read (a thin C by hand at the start of a
  later staff), a tie of the votes in such a bar is decided by the old time: 1 note lost on a copy by hand by
  a true signature. Say so and leave the rule.
- On a page that marks the ison by breves alone, with no letters, the breves are the ison's only notes: the
  count sets such a page as a melody and an ison on one staff, and a rule that takes every breve lost them. A
  breve under no letter is taken only on a page that names the ison by letters (`drone.BREVE_BARE`). Its sign is
  an upright stroke of its own at each side: measured from the edge of the inside, the head's own rim passed as
  a stroke on 15 to 33 true whole notes, so a column of paper must stand between the rim and the stroke.
- The marks of a census are stored once with a crop of the page around each (outside git, with the wide test),
  and the measures of a rule are tried on the crops in seconds, without a page read.
- A trial in the count (a lone note that is not given to both parts where the other part has a gap) is made on
  a copy of the scorer and scored on the stored runs: it gained 1 note on the clean copies and lost 42, and the
  scorer was put back from its copy.
- A rule of the columns that is written for a whole note acts on every head without a stem, and on a copy by hand
  such a head is a mark that is no whole note as often as not: a worn head, a box of two beamed notes, a pencil
  ring, the letters of a heading. The first form of the rule for a whole note that a print sets at the left of the
  other voice's note (`music.BESIDE_OVER`: the two heads stand over each other along the staff) acted at 15 places.
  The one on a clean copy was the print's; the 14 others lost 7 notes and gained 2, by parts and staff by staff
  alike, inside a round whose count showed 13 gained and 5 lost. The rule alone showed it, and a list of every place
  where the first form acts, with its measures, gave the print's whole shape: the whole note of the upper voice at
  the left of the stem line of the lower voice's note, a third over it.
- The software-made PDFs are read with a round's code whenever a rule of `music.py` changes, and compared page
  by page with main's reading of them (139 pages, a few minutes). The stored reading of the PDFs that the notes
  runs are joined with is older than the count's lists; the figures of the PDFs are those of the reading with
  the words.
- What Tesseract reads of a line is kept by the picture of the line (a cache outside git, with the wide test).
  One pass of every scan page with main's code fills it and must score exactly as the reading before; after it a
  full reading of the words costs only the reader's time, half an hour for LitChoir's scan pages and eight minutes
  for the fresh set. A rule of the words that asks the notes (`lyrics.set_under`), which the replay from stored
  rows cannot count, is counted on every page so, and such a rule off alone is one more pass. Read the fresh set's
  words with every round of words rules: the replay had called two rules level there, and the third was not in it.
- A stray word that a rule takes out of a row goes after the reading of the row is chosen (`ocr.SMALL_I`, as
  `ocr.CLEF`): taken out of each reading, a reading without it was whole, the other sizes were not read, and 8
  syllables were lost for 1. A stray word that goes can lose a whole word in the count where it had stood for a
  true one (a small i for the word I); the syllables do not move.
- A rule that joins or parts syllables by their notes meets the notes that the reader lacks. Two syllables that
  the list made of one read piece, with one note for the two, are a piece that the page sets under one note
  ("glo-rious"), or a word that the page prints whole under two notes, one of which was not read. LitChoir's
  count showed the rule 8 syllables gained and none lost; the fresh set, whose engravings leave the hyphen out
  where two syllables stand close, 2 gained and 7 lost. The measure came from LitChoir's own places: a syllable
  stands with its middle under its note, and the note of one syllable of a longer word stands beside the middle
  of the piece (`lyrics.ONE_NOTE`). A piece is one piece only as it was read: a letter that the mending added has
  no ink.
- A cell between two staff lines is closed by a bar line or a sign close before a head, and by a flag: the flag
  of the head's own note stands at the cell's right, and the flag of the note before at its left. LitChoir's
  pages showed the first and the fresh set the second. Three measures of the stroke did not part a flag from a
  bar line or a sign (whether it goes on past both lines, the share of the staff's rows that it fills, how
  straight the cell's edge is); how far the stroke goes on upright does (`symbols.CELL_BETWEEN`): measure each
  kind of stroke on LitChoir's own pages before a limit is set.
- A stem is straight. The arc of a pencil ring, of a bracket by hand or of an arrow goes on upright for a few
  staff spaces and was read as a stem with a small head at its end (`symbols.STEM_ARC`). The stem as the reader
  has it, from its end to the head, is too short to tell: an arc and the stem of a hand differ there by less than
  the trace wanders. The stroke is followed past the stem's end as far as slim ink goes, without the rows at the
  head (a way that is followed into the head reads the rim of the head, a rest or a number beside it), and it is
  an arc where the way is one bow: a parabola fits it, and each half bends to the same side as the whole. Of
  3,217 heads read from a stem on LitChoir's scan pages 22 ways bend so, each looked at; one is a true note whose
  stem a hand bent.
- Two filled heads a third apart at one stem close a speck of paper between them and the stem. The piece is cut
  evenly into its heads, the speck falls to one of them, and that head was read as a half note a step off
  (`symbols.HEADS_MEET`). The speck lies at the cut of the piece and beside the stem; the inside of a half note
  lies in the middle of its head. It is a rule for prints: on the copies by hand no part passes all of it.
- A limit in staff spaces for a mark is measured with the space of the mark's own staff. A page holds staves of
  two sizes, and by the page's staff space two half notes by hand passed a limit of 0.85 by a hair (0.853 by the
  page, 0.82 by their staff). A limit that a mark passes by a hair is the wrong measure: look for what the
  looked-at marks share.
- A census from the stored notes shows a mark as the later steps left it. At a rule's own step a stem that a
  later step finds is not there yet, and the parts of a sharp, of a flat and of the numbers of a time signature
  are marks of the kind of a head: 17 insides near a cut by the stored notes, 55 at the step. A spy on a step of
  the reader measures inside the step: the list of a mark's stems is shared, and read after the page it holds
  the stems of the later steps too. A rule that asks for a stem leaves the one true pair whose stem comes later;
  without the stem it took three numbers of time signatures, a clip, a blot and a stack of whole notes by hand.
- A hollow part between two filled parts of its piece is the cell of a sharp or of a flat's bowl far more often
  than a speck between two heads (12 of 13 on LitChoir's pages). The one speck hangs on a stem with both
  neighbours, whose middles are a third apart.
- A false mark that goes can free typed notes of a recitation on a copy by hand too: the brackets around a "3",
  read as notes, had been lined up with three typed notes of a recitation, and the count of the drawn notes fell
  by 3 with them. Compare `apart` of every score that a rule changes, not only of the clean ones.
- The notes that are not there on the sheets of the clean copies were sorted by kind once more (238 marks, round
  77): no kind is one cause. The kinds by the kind of note (hollow with a stem, filled, whole, read from a stem)
  say nothing of the cause; the page does.
- One printed head counts once among the notes that are not there (the wide scorer since round 78; `LENT=0`
  counts as before). The count splits a staff of two parts by the top and the bottom note of each chord and gives
  a lone note to both parts. A head that is lined up with a typed note in one part and stands loose in the other
  (the top note of the bass's octave under a note that the tenor holds; a note that one voice sings alone while
  the other rests or holds) had counted as a note that is not there, and a mark that lines up in neither part had
  counted twice: nearly half of the figure (4,699 to 2,577 on all scores; 3,918 to 807 on the fresh set, whose
  answers are exact). The count takes such heads off after the line-ups are made and chooses the way to set a
  score on its staves as before: with them off in that choice, one copy by hand changed its way and lost 2 notes
  and 2 syllables. A change of the count leaves every right note, syllable, layout and window of the reading
  before as it was, on LitChoir and on the fresh set, or it is no change of the count alone.
- A thin beam that slants runs into a staff line before the next stem and is hidden there on more of its way
  than a beam may be (`symbols.THIN_BEAM_HALF`). The slant is the sign: two stems that end at one staff line
  have that line between their ends, and a tie or a ledger line at one of them is the ink of a level line. A
  thin line that goes on past the last stem of its run is a slur over three notes as often as a beam (counted
  as beams, 17 notes gained and 56 lost by a census: no rule).
- A census that is labelled by the typed lengths gives no label to a pair with a note that is not there, and the
  first form of a rule acts there unseen: beside a note by hand a blot was read as a head with a short stem,
  and the line from that stem's end to the end of the note's own stem runs along the stem (1 note lost). A limit
  at both sides of what the true cases measure leaves such a pair out (the true beams rise by 0.11 to 0.21 of
  their length; no beam of the clean copies by more than 0.65). The reading of every page showed it.
- A flat mark on the line between the ends of two stems that both carry a flag or a beam is a piece of that
  beam, of a flag or of a slur over the two stem ends, and no head (`symbols.BEAM_PIECE`), unless it has a stem
  of its own that goes the pair's way: a hand sets a small head of the other voice there. Its census was made at
  the reader's own step: from the stored notes the stems pair wrongly, because the upper head of a chord stores
  its stem with an early end. A thick piece of a slur that went had held the line-up of the bass on a copy by
  hand (4 notes lost by parts, 1 gained on the sheet staff by staff): the rule stays, and the worklog says so.
- A heavy sharp whose bars are as thick as a head is one mark with the head that it touches, the whole sharp, and
  the note was lost (`symbols.SIGN_WHOLE`: the mark is cut at the head's stem). The paper that the sharp closes in
  with the stem and the head lies in the box of the head: with it the head was a half note, and its middle lay a
  step low. Such paper reaches the cut and is no part of the head. The sharps of a key signature that touch each
  other have the same strokes and the same share of ink in their box: a head holds a circle of ink, and they do
  not. A cut that knows its sign hands it on (`signs.WHOLE_SIGN`): the bars of such a sharp hide the top of a
  stroke, and the step that reads the signs then finds no pair of strokes. Read a new head on every page of its
  census with its sign and its pitch beside it, not only with the count of its cuts.
- The quarter rest of one older print is an X on the middle line with a short upright through its crossing
  (`rests.CROSS`), and the staff lines close the paper between its arms: its cells were read as whole notes. A
  census of every piece of ink with a waist gave what parts it from two whole notes one over the other and from
  the C of common time: where the ink stands in the rows around the middle, not the closed paper (the pieces of
  the staff lines between the arms close three cells). A rule for one print: say so.
- A rest that is read stops the note before it from being made longer. A half note whose hole a heavy copy
  nearly closed had been read as a quarter note and made a half note by the way to the false note in the rest: it
  is a quarter note again where the rest is read (1 note lost on a clean scan). The rule stays, the worklog says
  so, and the head goes on the list of what is left.
- A fermata is an arc with a dot in its hollow, and the thick middle of the arc was read as a flat head with an arm
  of the arc as its stem (`fermatas.py`). It is told by its whole shape: one stroke from end to end, an outer edge
  that has dropped little a quarter of the way in and much at both ends alike, its top near its middle, both arms
  down to its open side, and the dot under its top. A census of every arc with a dot on LitChoir's scan pages (452
  of 9,990 arcs) gave the limits, and each of the 214 that pass was looked at. A bracket by hand drops at once at
  its ends, a word by hand is no single stroke, a slur with a dot under it is longer and flatter. The module's own
  arithmetic takes one arc fewer than the census counted with rounded measures: count a rule with its own code.
- A piece of closed paper is no speck by its size alone: half of the inside of a hollow head on a line is as
  small on a small print (a speck in a filled head beside the room of its flag: 12 notes gained and 30 lost in
  the first form, on 60 pages). The census of every mark where the first form acted gave the shape of the one
  true case (`symbols.SOLID_SPECK`: two pieces, the speck inside the head and far from the room). A rule for one
  case: say so.
- A rule of the music step that mends misreads takes true readings too (`music.CHORD_ONE` took the printed dot
  of a dotted half note at the stem of another voice's half note). Read every scan page with such a rule off:
  the count says what the rule is worth (6 notes gained and 13 lost without it), and the pages name every head
  where it acts. What the rule distrusts is then measured at those heads, each looked at, and a guard keeps the
  sure ones (`symbols.DOT_SURE`, `music.CHORD_DOT`).
- The scans of one hymn measure a limit: the first limit for a sure dot (a side of 0.28 staff spaces) kept the
  dot in one scan, and the same printed dot has a side of 0.27 in the other. Where the true and the false cases
  stand a hair apart by one measure (0.23 and 0.27), look for the measure that parts them widely (the ink of the
  dot, among the marks that are round: 0.043 and 0.067 staff spaces squared).
- A new head changes what an older rule does beside it: a half note that is read anew between two heads of one
  stem (`symbols.SLIT_BETWEEN`) made the chord rule take the dot of the head under it, and the rule alone gained
  nothing. A rule whose gain needs another rule of the round is counted alone and with that rule, and the
  worklog says so. A new head can also read what stands beside it wrongly (the dark edge of a smear as its
  dot): look at the length of every new head, not only at its place.
- A score counts for the milestone only when it is whole. The scores that lack one to three notes are looked at
  place by place, each with its other scans: four notes on three such scores made two of them whole and gave a
  third every note (round 80).
- A census of the heads that reach the notes shows a rule only those heads. A rule that changes a head where it
  is made meets more: the heads that a later step replaces, and the pieces whose own head is refused. A head
  from a stem that is one arc of an open ring (`symbols.THIN_RING`) was made hollow at once in its first form:
  it stood in the way of the step that reads hollow heads from their insides (three pages of LitChoir, where a
  head kept one of its two stems), and on the fresh set a ring gave a head where the piece alone gives none (2
  notes lost). Set such a rule where its census was taken: the head is made as before, and the change acts after
  the steps that take heads away or replace them (`symbols.ring_heads`).
- A census from the stored notes measures a mark by the note's middle and its stored size; a rule measures the
  head's box at its own step. The arm of a bow, counted from the stored notes, stood at one mark of 422, and the
  rule's own code took three notes on those pages, two of them true (`symbols.BOW_MIDDLE`). Read the first form
  on the pages of its census before a full run, and take the second census at the reader's own step with the
  rule's own function: it showed what parts a bow from a head (the stem of a bow stands at the end of its
  middle, the stem of a head in it).
- Two measures that an older rule joins into one can make a wrong reading right. Two level rows less than half
  a staff space apart are one ledger line, at their mean; parted where paper lies between them
  (`symbols.LEDGER_TWIN`), a head by hand that is read from its upper half lost its pitch, which it had only by
  the mean of the ledger line and its own rim. List every pair with what each half is before the pair is parted,
  and leave the pairs whose other half is the head's own ink.
- A measure that is wrong in principle can be right in what it gives. The first and the last cell of a chord on
  lines hold half an inside each and were weighed like whole cells; weighed twice in every mark, they change
  what 119 marks give, pairs of half notes that are read today among them. The mend is made only where the
  census shows the fault (`symbols.LINE_CHORD_ENDS`: from four cells on, one chord). Say where a rule is a rule
  for one case.
- An entry of the list of the notes that a hand changed can name one system of a page: a slip that a hand wrote
  and pasted over the print is a page by hand for that system.
- A note that is not there can stand unseen in the count, and a rule that changes its length shows it (a letter
  of a heading on the fresh set: 3 to 4 notes that are not there in its piece, and no note lost). Look at the
  note on the page before the rule is blamed: it was read before the round too.
- A low cell of paper along a staff line is the half of an inside that the line cuts off a head, or a wedge between
  the line, an upright stroke and a slanted one (a beam, a slur, a pencil ring at a stem or a bar line). What lies
  across the line tells: the other half of the head, ink or closed paper, or open paper (`symbols.FLAT_WEDGE`; a
  census at the reader's own step parted the true heads at 0.47 from the others at 0.54, and the rule takes from 0.7
  on). LitChoir's pages showed 17 such notes that are not there; on the fresh set the same wedge lies under the flag
  of every note with its stem down, and 138 went.
- A mark that is no note can make a true note right: an eighth note whose flag is not read was made short by the sum
  of a bar with half notes that are not there, and is a quarter note where they go (the fresh set, 1 note lost by 138
  marks that are no notes). And on a copy by hand a mark that goes moved the voice of the note beside it, and the
  count's split of the staff into melody and ison with it (4 notes lost). Look at every mark that the rule took; where
  each is no note the rule stays, and the worklog names the note.
- Ink that is no part of the music can cost a note that is lacking: the faint line that a scanner drew down a page ran
  along a half note as a second stem, and a mark with a stem at each side is a piece of a beam for the reader. Such a
  line is told by the system (it passes two staves or more at both ends, leaning, in the grey picture:
  `layers.SCAN_LINE`), and what stands on it stays: a true stem stood exactly on the line and went with it in the
  first form. A row's piece goes only where it is no heavier than the line. The census of every such stroke named what
  else passes a system at both ends: the stroke of a clef on a system of one staff, the line that opens a system, the
  shadow of a page's edge.
- A limit that is set between two cases of LitChoir is the wrong measure. The stroke of an engraved flag, kept to two
  staff spaces or more between LitChoir's 3.1 and 1.1, no longer acted at any place of the fresh set where its first
  form had acted rightly. The fresh set shows that such a limit is wrong and gives no measure; the page of LitChoir
  that the first form read wrongly gave the shape (the flag hangs on the stem of a head that is a head by its own ink:
  `symbols.FLAG_STROKE`).
- The row before the first row of a page is the last row of the page before it: what the reader carries from system to
  system (the key, a tie, a word that a hyphen leaves open) the hymn carries over the page (`ocr.MEND_PAGE`). A pass
  of the words on the pages that a round changed hands the words step only those pages, so a rule that carries
  something from page to page is counted by the replay and by a full pass of every page.
- A rule that calls a piece unsure, so that a later step may mend it, changes every step that asks how sure a piece
  is: a 1 that was read for a letter, counted as unsure, took short pieces that had been read right and the reading of
  their row with them (2 syllables gained and 4 lost). The rule decides by the list itself, and the piece stays as
  sure as Tesseract was (`ocr.DIGIT_LIST`: a 1 among small letters is an i where the list holds the word with an i and
  not with an l).
- A test for a piece of a word with no vowel judges the letters of the plain alphabet only, on a page whose words fit
  the list. A letter with a sign of its own and a letter of another alphabet are in no list of vowels: the first form
  took every such piece for one with no vowel and lost 56 syllables and 90 whole words on the fresh set. And in
  another language a consonant beside a hyphen is a word ("s-a", "n-am"): there the test says nothing.
- A guard that sorts out the ways to part a word before the test for one way makes new cuts: of two ways one was left,
  and a word that had stayed whole was parted ("in-tru"). The guard looks at the one way that was found and only
  takes its cut away (`ocr.ENDS_VOWEL`).
- The pieces of ink of a word are counted against the signs that Tesseract read, and stand a sign off where two letters
  touch: a wide gap inside a word then cuts it a letter early ("An-g" and "els"). A piece with no vowel between the
  cut and the next hyphen is no syllable, and the cut is not made (`ocr.CUT_VOWEL`).
- A rule that takes letters off a word by the shape of the stroke behind it meets stray ink that was read as a short
  word: the hook of a clef by hand, a hyphen over a slur, a slur alone, the tail of a letter by hand. The first form of
  the rule for a slur that touches a word (`ocr.BOW`) trimmed 30 words on LitChoir's scan pages, 5 of them rightly,
  and made words of one letter of the list out of the rest. Measured at each place, the ink before the stroke tells:
  letters fill the rows of their row (0.84 or more of them against 0.61 at most), and as many stand there as were
  read (within 0.15 of a letter against 0.49 or more). Say where a rule is a rule for one print: three of the five
  words are one carol's.
- What a rule takes out of a row is taken out for every test that sets the readings of the row beside each other. The
  test for a word that every reading holds (`ocr.MEND_ALIKE`) saw the rows with the dash that a slur had been read as,
  found "praisingthes" at every size, and the mending then left it.
- Tesseract gives one box to a true hyphen and the piece of a slur that comes close to it. A dash is a piece of a bow
  only where its box holds no other ink: of the 114 dashes that the first form dropped, 57 hold other ink, and 10 of
  the 16 of those that were looked at hold a true hyphen. One of them had made a right word by chance ("shep-" at the
  end of a row was mended to "she-", and without its hyphen it stayed "shep"): look at what a gain stands on, and mend
  the step that lost the word (`ocr.MEND_HEAD`).
- A word that a hyphen leaves open at the end of a row is the beginning of a word, and the list is asked how often it
  parts a word after these letters, not whether it holds them as a word. Both the piece that was read and the word
  that would take its place are asked the same: holding back every such piece lost "up-" (read "op-", which begins a
  parted word 3 times, and "up-" 85 times). A credit for such a piece in the choice among the readings of a row gained
  10 syllables and lost 7 on all scan pages: a border that moves, and it is not in the rule.
- The stored rows of the replay are a census of the pages as they were built then. 39 scan pages of LitChoir were
  built anew since, and their rows stand at other rows of the picture now: a rule of the replay that looks at the ink
  looked at the music over the row there, and dropped a true hyphen. The replay leaves such a rule off on those pages
  (a list with the wide test, outside git), and the full pass shows them. Compare the columns of each stored row with
  the page before a rule that looks at the ink is counted by the replay.
- The quick count of the words does not join a word over the end of a row, and it takes one row for each staff. A
  hyphen at the end of a row that a rule takes, and a row that the count does not take, show only where the words
  of the two full passes are set beside each other page by page (a script outside git, with the wide test). Read
  that list for the clean copies before a round of words rules is closed: a piece of a slur that had been read as
  a hyphen stood for the true hyphens beside it, which Tesseract read with a stray sign ("=———=—+"), and an
  "Al-le-lu-ia" over the end of a system was no whole word any more. The rule that took the piece stays, the
  worklog says so, and the step that loses the true hyphen is on the list of what is left.
- A piece of ink that is higher than a head is cut at the valley of its rows, and a thick ledger dash is the
  heaviest row of its piece: a half note on such a dash, glued to a half note on the first line of the staff, was
  cut through the inside of the lower head, and neither note was read. Never cutting through closed paper is no
  rule: 909 cuts of the scan pages run through closed paper, and for most pieces it is the only cut. The rule asks
  for the whole shape of the one thing (`symbols.DASH_HOLLOW`: one thick level bar beside the staff, a head's height
  to each side of the middle between the dash and the staff's line, closed paper in both halves, and a cut of today
  through that paper). A census whose bar was 1.6 heads wide missed the piece that it was made for: a row with the
  stem in it is 1.71 heads wide. Try a census on its own case first. A rule for one case: say so.
- The wire of a paperclip is grey where the print is black, and it lies on the print: nothing shows under it. A
  census of every thick grey piece of the scan pages (2 px inside the ink, between the page's ink and its paper)
  named the clips, the rings of a binder, the shadows at a page's edge, pale staff lines and a slur of a pale
  print. The slur is a long band of one width that bends, as a wire is: the wire is thicker (`layers.CLIP`).
- Ink that is foreign to the page is not simply taken out of the picture. With the wire of a clip taken out, the
  false note that it had made was gone, the count showed no note gained and none lost, and on another page a sharp
  of the key signature, which the wire had cut from its neighbour, stood free and was read as two notes: the staff's
  key signature is not found under a clip, and the count lined the two up with notes that the clip hides. The
  pages were set beside each other note by note, not only score by score. The wire stays in the ink, its mask is a
  layer, and a later step asks it one thing (`symbols.CLIP_CELL`: a cell whose rim is mostly wire is no head).
- A reading of a row that holds only words of the list ends the row, and the other sizes are not read. A lone
  capital O between two words stood in no word of such a reading, and the syllable was lost. The ink tells: a
  piece between two words that is as wide and as high as a letter, apart from both, with the row's strokes
  (`ocr.UNREAD`); the reading is then not whole. Reading every size although one is whole gained 22 syllables and
  lost 8 on all scan pages and brought about 45 stray words of one or two letters: no rule. A bar line that was
  read as a stroke has a box that begins in the letter beside it: such a token covers no letter.
- A digit behind the letters of a word is a stroke beside the word on a print (a bar line through the last
  letter, a full stop, the end of a slur: a 4 or a 7) and a letter on a copy by hand (a 5 is an s, a 2 an a or
  an e). Taking every digit off turned "a5" into "a" in four rows of copies by hand: level in the count, and
  wrong on the page. The census by the digit, with a tile of each kind, gave the two halves (`ocr.DIGIT_END`).
- A hyphen that Tesseract reads with a stray sign beside it is a true hyphen at 34 of 390 such places and wrong at
  26; the others change nothing. The token alone does not tell: no rule.
- The stored measure of how pale the core of a head is (`mark.core.pale`) counts the paper in the box of a note
  with a flag: of the clean notes from 0.2 on, 129 are right and 6 are not there. It is no measure of grey ink; a
  rule for a grey streak across a staff needs the grey of the mark's own ink, measured at the reader's step.
- Ink by the page's limit is not all print: a word or a ring in pencil, a marker, the shadow of a pasted slip and a
  grey streak are ink too, and they hold no black. Black is measured by the page's own ink (`layers.BLACK`, the layer
  `black`), so a pale print is black by its own measure. A mark with no black ink is no head only where the print
  around it is black (`symbols.GREY_MARK`): a stretch that the print left pale holds pale heads on pale lines, and
  on a grey copy the notes in pencil stand among grey lines. The first census, from the stored notes, showed 13 such
  marks and no note; the census at the reader's own step showed one more kind, the pale middle of a worn head that
  is read as a small mark of its own inside the head's black ink. The ink close around the mark tells it.
- A census script that leaves scores out says which. The census of round 84 for the grey of a note's core, and the
  first one of round 85, asked for the scores of the kind 'scan' and left out the kit's 28 scan scores, the score
  that the census was made for among them. Look for the census's own case in its result before the result is read.
- A bow in pencil between two printed heads is no tie (`ties.TIE_SOFT`): the ink along the bow holds no black, and
  the lines of the staff beside it do. On a grey copy the true ties hold no black either, and neither do the staff
  lines: a measure of grey is always set beside the print next to it. A rule for one case.
- The second half of a tie is no note of its own, so a false tie hides what is read at its end. The head at the end
  of the pencil bow was read for both voices, with the stem of the head under it as a second stem, and counted as a
  note that is not there once the tie was gone (2 to 3 on that score, beside 2 notes gained). Look at the second
  note of a tie that a rule takes away in every voice that it is read for, and say what the tie hid.
- A cell that a line in pencil closes with a bar line or a printed head is not told from a head that a hand drew in
  pencil on printed staves by the grey at its rim: both mix pencil and print. Counted at the reader's own step, a
  rule by the share of soft ink at the rim took 12 true notes of copies by hand and 11 that are not there: no rule.
- A block of code that is set before a function by a search for its name can land inside the comment of the constant
  over that function: the constant of round 84's clip rule stood in the middle of an older rule's comment in main.
  Read the place of an insertion once it is made.
- A background job is done when its own last line stands in its log. A date that the look at the log prints itself
  is not the job's: a second census was started over the first one, which was still running.
- The column that a stem is stored with is that of its far end. A stem that was followed into its beam, or that leans,
  ends beside its own stroke there, and by that column the stroke looked like a stem that no head has: the head past
  the stem's own head got it as a second stem, and was read for the other voice too (`symbols.LOST_OWN`). The first
  form (no stroke at the middle column of a stem is a lost stem) was wrong in three ways that its census of 102
  strokes and its pages showed. A stroke that one finder refuses is handed to the next one: `thin_heads` read new
  heads from three of them, so the refused stroke is marked. A mark with no stem past the end of a stem is the next
  head of a chord on that stem (2 notes lost on two scans of one print). And where a stroke has a head at each of
  its ends (a flag that was read as a head) the stem does not tell which one is the head. The rule takes the one
  shape of its case: a head that has a stem of its own, and a stroke that leaves the head between the same way.
- A head that is read for both voices costs nothing in the count, which splits a staff by the top and the bottom
  note of each column: 84 such copies went on 35 pages, and the count moved by 4 notes, where a copy had taken the
  beam of the other voice's stem. A rule for the written music is judged by its pages set beside each other note
  by note, sorted by kind (a copy in another voice that is gone, a note that is gone, a new note, a changed length;
  a script outside git, with the wide test).
- The second note of a tie sings no new syllable. The words of a column were set under its top note, and where
  that note is the second note of a tie, the count joined the tie and the syllable went with it
  (`lyrics.TIED_NOT`: the words are those of a voice that strikes its note there). Such a rule cannot lose in the
  count for the voice that holds; look at each word that moves on the page.
- The seam of two scans that were joined into one page cuts the letters of a row in half, and no reading of the
  row holds the word. The word that the row before leaves open frames it: the list holds one word only that begins
  with the open piece and ends with the last syllable that was read (`ocr.MEND_FRAME`, a rule for one case). The
  tools that show the readings of one row do not hand the row the open word of the row before; the full replay
  does. And a pass of the words on a plan of pages does not read the page before a planned page: a first syllable
  that such a pass loses there is the pass's, not the rule's.
- The replay of the words compares letters. A rule that acts where an older step had reached the same letters
  shows no row there, and the full pass showed one as a word whose capitals changed ("ev-ER" to "ev-er": the frame
  of "FOR-" and "MORE" gives the "ever" that a letter added to "VER" had given). A spy in the rule's own function,
  in the replay, lists every row where it acts; and the two full passes are compared file by file, also where no
  count moves. A syllable that a rule writes keeps the capitals of its row.
- Black ink alone is no second look for a word under a loop in pencil: where the pencil crosses the letters and
  where the hand pressed, it is as black as the print (the "in" of one clean score reads "im" and "Ir}" so), and
  the list's pairs hold no phrase that only the hymn itself has. No rule.
- `thin_heads` asks 4,395 strokes of LitChoir's scan pages that stand at the middle column of a stem that a head
  has, and 416 of them have a head that was read from a stem beside them. The wider form of the stem rule (such a
  stroke is that stem for every finder) needs a census of its own with the scorer's verdicts before it is tried.
- One print draws the rim of a whole note bold at its two sides and as a hairline over and under them, and a scan
  loses the hairline: a whole note that hangs under the staff is two bold arcs there, with no closed paper and no
  stem, and no finder of heads has a way to it (`symbols.arc_wholes`, a rule for one print). Two arcs side by side
  under a staff are letters far more often (37 of the first 40, and 139 of 142 by the wider census): the whole
  note's near side is closed by the line of the staff over every column between the arcs, its outline grows narrow
  to the far end, where the two arcs end at one height, and it stands alone in paper. The first census missed one
  of its three cases by a limit of its own (an arc 0.82 staff spaces wide): a census is widened until it holds
  every case that it was made for, and the rule's limits are then set on the second census.
- A false note that stands at the end of a score is lined up with whatever typed note is free: a ring that a hand
  drew in pen under the last printed note was read as a note, and the count set it beside the unread whole note at
  the start of the next page. Read as "the last note is typed otherwise", the place looked like a hand's change of
  the print. Find the typed note on its own page before a place is called the hand's or the typed hymn's. Ink by a
  pen is as black as the print (`layers.black`), so `symbols.GREY_MARK` does not see it: such a ring goes on the
  list of the notes by hand, after it was looked at in the scan itself.
- A limit that a true case misses by a hundredth of a staff space is not moved. The limit of 0.45 staff spaces for
  the strokes of a flat is for the two sides of a large hollow head's rim, which are as heavy as each other; a flat
  whose long stroke the print left faint has a hairline and a bold wall (`signs.FLAT_BOLD`: the long stroke at most
  half as wide as the wall). The census of every pair that the limit refuses (139 on LitChoir's scan pages, at the
  reader's own step) named what the limit is right for: 137 with a heavy long stroke, and the wire of a paperclip
  across a stem.
- A rule of the words that is tied to the mending (`mend`: the page's words fit the list) does not act on a page
  in another language or on a page of the names of the notes, and the first forms of the rule for a short word
  that every reading holds (`ocr.SURE_ALIKE`) never acted on the row that they were written for. Look for the
  rule's own row in the replay's changed rows before its count is read.
- A word that a rule lets stay changes which reading of its row wins: its letters count in the fit of a reading,
  it can make a word of the list with the piece beside it, and a reading with it can be whole. A short word that
  every reading holds speaks for no reading. Its letters taken off the fit were not enough (a spared "Ma-" made a
  word of the list with the next piece, and a reading with a stray word won by it): how well a reading fits,
  whether it is whole and whether it is a row at all is asked without the word, and the reading that is kept has
  it. Then the rule can act in the readings of the further files too, where its first form lost 2 syllables (12
  syllables gained and none lost on all scan pages, against 7 in the readings of the first file alone).
- Two readings of a row by two language files are set beside each other by their letters (`ocr.SECOND_FIRM`), and
  a word that the first file drops as unsure and the further files keep decides there: the reading with a misread
  label won because the standing one lacked a name of a note that both had read. Before a lost word is blamed on
  the choice among the files, look at what each reading had dropped.
- A hand's change of printed words can undo itself: on one clean score the printed words are struck through, a
  replacement is written under them and scribbled out again, and the printed words are written back over the
  staff. A pencil loop that runs through a word crosses nothing out: such a word is print, as a note under a pencil
  ring is. Look at what the hand wrote beside a crossed-out word before the place is counted. A word that the page
  ends with is a word that the reader must read (the owner, 22 November 2026: "it is what needs to be counted").
- A rule that keeps a new kind of inside keeps it out of what the page learns of its insides. The page's measure of a
  hole comes from its read half notes (`symbols.HOLLOW_PAGE`), and an inside that a faint staff line parts into two
  staggered halves, taken whole (`layers.HOLE_LEAN`), stood where the page's other such insides were halves: the
  measure rose, and a dotted half note at the limit became a quarter note. Such insides are a layer of their own
  (`lean`). A new inside also moves the cut between two heads of one piece: a head that was read right by a border can
  go, and the worklog names it.
- A step that takes a stem from a head for the flag at the stem's far end asks whether the head has a stem of its own
  the other way. A second stem down from a head with its stem up runs to where a box beam by hand or a slur meets the
  stem of another voice, and the low flat mark there was read as a head with that voice's stem (`symbols.TAIL_FLAT`).
  The census at the step, with the scorer's verdicts at both marks, gave the height that parts such ends from a true
  quarter note under a U.
- Two voices a second apart whose heads touch, with the stems back to back between them, are not cut at the column
  of the stems: the cut parts the insides of two hollow heads, and a pair that was read right through its holes is
  read as one pitch (1 note gained and 4 lost). A dot that a pencil stroke joins is a blot of a dot's size joined to
  other ink at 6 missed dots and at 20 heads that rightly have none: no rule by the blot.
- A stroke with a mark at each of its ends is the stem of one of them. The beginning of a beam on a staff line over a
  chord was read as a filled head that took the chord's stem up as its own stem down, and the chord's top head kept no
  stem toward it (`symbols.FAR_MARK`). A census at the step, with the scorer's verdicts at both marks, gave the height
  that parts such marks (the false ones up to 0.72 of the page's heads, the first true note at 0.77). A false mark that
  goes can move the vote of its column: on a copy by hand two bass eighth notes became quarter notes beside a treble
  eighth whose flag is not read. Say so, and leave the rule where every mark that it took was no note.
- A small head that the page prints on a voice's stem (a divisi in small notes) is a printed note where the typed hymn
  leaves it out, and goes on the list of the notes by the page as `add`, after it was looked at four times the size.
  The list is made by its script: an entry that is written into the list by hand is lost at its next making.
- A mark that an earlier round called the hand's is looked at in the scan before it is counted so: the "time signature
  by hand" of one clean score is the printed 2/4, which a pen stroke joins.
- A digit that stands alone between two words can be a letter that the stem of a note runs into: where a stem of
  the staff over the row joins the top of an a, Tesseract reads a 4 (`ocr.FOUR_A`). The paper of the letter tells:
  the small bowl of the a is closed, low in the band, in a box one letter wide. A census of every lone 4 in the stored
  rows (50 places, a tile of each) gave the shape: a stem through a hyphen or through an i, a tie and a number by hand
  close no such paper, and the number of a verse stands first in its row or carries a full stop.
- A mark that one print draws in one shape can be misread in a different step at each of its places: the head on top
  of the loop that an eighth's flag closes with its stem was read as a sharp, as the loop of a flag, as a fat stem and
  as a half note at four places of two scans. Count what each step would take before a rule for one of them: of the 84
  marks of the clean pages that are read as sharps because their strokes at one end are another head, one is a head.
- A line of words that does not fit under its notes is set at two heights, and the finder of the rows takes each
  half for a row as wide as the staves: the first row under the staff then holds one half and the other half's
  letters cut in two. The halves stand in columns apart, no letter of one over or under a letter of the other
  (`words.HEIGHTS`). A slur over the lower half lies in the rows of the higher one as a free piece of a letter's size,
  and kept the first form from the case it was made for: such a piece is one thin stroke that crosses each of its
  columns once, and all 40 of them in the first two rows under every staff of LitChoir and the fresh set were slurs.
- A word whose letter touches a stem is no free letter, and a reading that is cut to the columns of the free letters
  loses it (the first word of a row on two scans); a reading as wide as the staves gives a word a box that runs into
  the other half's letters beside it. The two halves are read each from its letters outward, and their readings are
  joined by columns, and past both halves' letters by the rows that hold a syllable's ink (`ocr.TWIN`): a printed
  word stood past the words that a hand wrote in the lower row. Try such a rule's ways of reading on its pages with
  Tesseract before a full pass: a pass of the planned pages takes three minutes.
- Two half notes side by side, the one at the right with its stem up and the one at the left with its stem down, are
  two voices that cross: the voice whose stem goes up sings the lower note. Two voices that do not cross stand in one
  column. Where the typed hymn gives the higher note to the higher part there, it is typed otherwise than its page
  prints, and the place goes on the list of the notes by the page.
- The way of a stem is followed across small gaps of paper at the staff lines, so it can follow the round edges of
  marks that stand one over the other: three printed dots in a column were read as a head with the two dots under it
  as its stem. A printed stem is ink of its own that leaves its head (`symbols.DOT_COLUMN`, a rule for one case).
- A list that a script makes is compared with the stored list before the script makes it anew: the list of the notes
  that a hand changed held two entries that had been written into it by hand and were not in its script.
- A test that cannot hold at a place refuses every head that reaches it there. A hollow head that the step of the
  insides reads in the first space beside the staff needed a ledger line, and no ledger line belongs to that space
  (`symbols.HOLE_FIVE`). A census of every head that this one test alone refused (121 on 72 pages of LitChoir, none on
  the fresh set), each looked at, held the true heads that the clean copies lacked there and the shapes of the false
  ones: a mark between two strokes (a letter, a letter p between brackets, the ison's breve between its bars) and a
  wedge between the line and a pencil ring or a flag.
- A head that a step makes beside another head can meet a head that the same step made before it: that head stands
  in the step's output, not in its input. Two touching heads share their stems where both are known: the first
  sharing looked at the input only, and both heads kept the stem down.
- A guard by the widest row of an inside meets the slit of a half note by hand, whose rows are two to eight pixels
  wide: its widest row lies anywhere by chance. Ask for the whole shape: the widest row of a wedge spans its box.
- A mark that a step names wrongly can be told by its neighbour. The lower head of two voices that touch, whose flag
  a print draws back up to the head, was called a sharp (its four ways leave it), and the head over it held the
  mark's stem down as its own second stem (`symbols.PAIR_SHARP`). The neighbour is asked for its own shape too: a
  sliver of a half note's rim, a punch hole and a small mark by hand stood over the false marks, and the heads that
  the staff lines cut out of one blot all hold both stems, so the crossbar of a letter under such a column passed.
- A rule for a pair is read in each direction alone. The same shape the other way round (the upper head read as a
  sharp, its stem up taken by the head under it) was the flag over a head, a sharp of a key or a mark by hand at
  every place where the first form took it, and cost a clean score 5 notes. Places at the start of a staff (clefs,
  the sharps of a key) cost no note, because the start of the notes drops their heads, but a census lists them:
  count the places inside the music before a rule is judged by how often it acts.
- The layer of the stems can hold whole heads. Where a print draws the flag of an eighth with its stem down back up
  to its head, the head, the closed flag and a touching head of the other voice are one upright piece over a short
  stem, four times as wide as the page's stems, and the older rule for such a stroke wants a quarter of its rows thin
  (`layers.STEM_OWN`; the stroke had 0.245). A census of every slim stroke that stays much wider than the page's stems
  (1,605 on LitChoir's pages, 761 in the music, each kind looked at on tiles) gave the shape: the thin rows are one run
  at one end, and the wide rows stand beside that run's column (`layers.STEM_BESIDE`); a quarter rest, a sharp, a clef
  and the numbers of a time signature stand around their stroke. Ink that a rule moves from one layer to another is
  only the ink that the rule is about: released whole, the closed flag went to the marks with its head, the cut of the
  piece at a staff line parted its paper into two insides, and a false half note stood where the eighth stayed lost.
- A whole note whose hairlines the scan lost is two short bold strokes that face each other, and in the staff the
  staff lines join their ends and a ledger line runs through both (`symbols.arc_pairs`). Such pairs are counted in
  the ink without its level lines, and a ledger line is joined back to a stroke only across the gap that it leaves in
  the stroke's own columns. The shape of the pair is also that of letters, of words that a hand wrote on a staff and
  of a line through struck-out words: the height of one whole note or of two a third apart, and a ledger line as
  short as one note's, part them. A print can set its first ledger line closer to the staff than a staff space
  (0.8): a note that a ledger line crosses stands on that line, whatever its distance.
- The layer of the staff lines keeps a line where closed paper touches it, so paper that two signs close with two lines
  joins the signs: a time signature set close after the key was one piece with the sharp, and its numbers were read as
  notes. The ink without the lines that the ink alone shows parts them, and parts numbers that touch along the middle
  line too: it is a second look where the first finds nothing (`meter.TIME_LINES`). A rule for the time signatures is
  judged by the signatures and the starts of every staff of two runs, each change on a tile centred on it: a new
  signature that takes no note shows in no count (the flat of a key that a page's reading misses passed as one).
- A guard that asks for a mark in its own way misses the form of it that another step reads. A thin head is kept off a
  stem that carries a flag (`thin_heads`), and the guard asked only for a flag as thick as a beam: one print draws the
  flag of an eighth with its stem down as a hairline that curls back up to the head, and where it meets the stem again
  it closes paper that was read as a head of the other voice. `count_tails` had counted that hook as the flag; the
  guard asks for the hook as `count_tails` reads it (`symbols.ALONG_HOOK`).
- A dot that sits on a staff line keeps a hair of the line where the line was taken away around it, and is no dot by
  its shape. Measured without the rows of a line that runs on at its left or its right it is one (`symbols.DOT_LINE`),
  and so is a short stroke across a line: the first form changed 175 heads of LitChoir's pages (dots gained at 43, lost
  at 41) by a dashed bar line, the bars of an ison's breve, the tick of a hand and stems. A dot on a line has its other
  ink at one side of the line only, its ink in the line's rows is a hair, and it holds as much ink as the printed dots
  of `DOT_SURE`'s census. A dot that is found so is kept to that one step: let into the steps for a dot close to
  another head (`DOT_CLOSE`, `DOT_TWO`, a dot at a ledger line) it gave a head near it a false dot.
- A rule that asks how black a mark is asks the page's own print of that mark. A grey speck is no dot of a black head
  (`symbols.DOT_GREY`), and the first form, which asked the head alone, took the true dot of a pale print whose dots
  are all grey, beside a head that is black by chance: the measure of black is the page's own. The count called it a
  gain, by a line-up with the place where the hymn sings the same words in quarter notes. The page's other dots tell
  (`DOT_GREY_PAGE`). A dot that goes is a gain only where the page prints none: look at each gain on the page too.
- A blot of a dot's size inside other ink is a dot where the column says so: notes that sound together agree on a dot,
  and the printed dot of the other voice gives the column and the size (`symbols.DOT_JOIN`; of 18 such blots on
  LitChoir's pages, 10 were printed dots that a pen line, a slur, a staff line or the head's rim joined, and none a
  head that has no dot). A hand's dashed bar line through two voices gives both a dash: a print's dot is round. A dot
  that is read right makes more bars of a page add up, and the page's full bar (`music.full_sum`) then settles the
  tied vote of a bar whose bar line a copy by hand faded: 2 notes lost by no wrong dot. Name such a note in the
  worklog.
- A grace note is no note of the bar, and the scorer leaves `<grace/>` out of the typed hymn and of the reading alike:
  a small note that is written as one is neither lacking nor false, and the notes after it keep their moments. One
  print draws it as a small head on a stem down whose foot is a knot of the flag and a slash (`symbols.GRACE`); the
  reader read the knot as a head with the stem up, and the paper under the slur as a half note. A stroke is measured
  at both of its tips, and the top of a stem up has a knob as well (its beam or its flag): the knot reaches less far
  from the stem than a head at the foot of a stem up, and the small head stands in paper where a beam or a flag leaves
  its knob. The stroke is followed from the middle of the read stem, both ways: a head that was read from the knot is
  no middle of the stroke.
- The staves of a system show their time signature in the same columns, and a staff whose own signature is not read
  shows its numbers there as notes (`reader.TIME_COLUMN`): another staff tells where to look, as the page before tells
  the next page. Ask that staff only where its sign is sure: a thin C that `meter.common_signs` reads can be a head
  with its stem, and on a slanted page the columns drift by half a staff space from staff to staff, so a staff three
  staves away named a true chord (only the nearest staves that show a sign are asked). A false mark that goes can
  undo a line-up that it held with another false mark: a false 4 in the bass had pushed the bass's notes a beat late
  as a false note over the treble pushed the treble's, and the two staves stood in step by chance (2 notes lost by
  the count, none by the rule). And a false mark that goes can let the count set a run of typed notes apart as
  recited: a bold C read as two whole notes had held 13 typed notes of a carol in the count of the drawn notes.
- Two voices a second apart that a print sets side by side, the upper voice at the left with its stem up and the
  lower at the right with its stem down, are read as one head and given to both voices at the one pitch. A hollow
  such mark (the lower voice a half note) holds one hole that no cut parts, and the filled upper voice sits to the
  left of the hole and a second over it, on the upper-left-to-lower-right diagonal (`symbols.DIAG_PAIR`); a filled
  such mark (both voices quarters) is read as one head whose stem up and stem down are one line through its middle,
  which `symbols.SIDE_TWO` leaves because the mark's four ways make no sharp, and `symbols.SIDE_HEAD` cuts it as
  `SIDE_TWO` does. Both ask that the right head stand a second lower, so neither reads the unison form of the pair
  (two voices on one pitch, the head read for both: pascha-christ-is-risen-romanian x417 stays lacking). The rules
  acted at five marks of LitChoir, each looked at, and at none of the fresh set: four were the pair, and the fifth a
  piece of a word that is read as no note before or after. A cut that fires but changes no note shows in no diff of
  the notes: the census of every firing (`SIDE_SEEN`, `DIAG_SEEN`) names it, and it too is looked at on the page.
- One print draws a whole note with bold sides and a hairline over and under its inside, and a copy breaks the
  hairline: the inside is open paper, and `symbols.hole_heads` reads an open inside only with a stem
  (`symbols.open_wholes`, `OPEN_WHOLE`). The shape of the inside alone (round or a little upright, no wider than a
  head's inside, ink around it in nearly every way, a ring as high as a head) read the cells of letters, printed and by
  hand, the cell of a bold head or of a dark dot on a thick copy, a pencil ring and half notes whose stem it did not
  see: 21 notes gained and 20 lost on all scores. A printed whole note is wider than the page's heads and holds with
  another voice (a hollow head of its system in its column): a rule for the print, and it leaves lone whole notes
  that the first form read rightly on copies that are not clean. A new head changes what its neighbour was: where two
  whole notes stand as an 8, the head over the broken one had taken the broken one's side for a short stem, and with
  the new head beside it that stem crossed the voices (the count by parts lost 2 notes where the staff count held).
  Such a stem ends in the new head's box and goes (`OPEN_SIDE`).
- A mark that a rule takes by the line that goes on at both sides of it (`symbols.BAR_MARK`: the paper that a tie
  closes where it crosses a bar line) is missed at an end of the line. A bar line begins and ends at the staff's
  outer lines, and a slur that meets an outer line at a bar line closes its paper there, with the bar line as the
  stem of a half note. The end of the line tells (`symbols.BAR_END`): the mark touches the outer line, nothing goes on
  past it, and the line fills the staff to the other outer line and ends there; a stem ends at its head. A clean score
  that reads every note and syllable and has one note that is not there is the nearest whole score: count such scores
  (`wholecount`) beside the scores that lack one to three notes.
- A mark that replaced other marks gives them back when a rule refuses it. An open hole of `hole_heads` takes the heads
  in its box as pieces of its broken rim; where `symbols.OPEN_FLAT` refuses the hole (open paper level at a staff
  line, with open paper across the line), true filled heads came back (two scores), and so did the pieces of what had
  closed the cell: the bowl of a flat with its stroke, the bar of a natural, the ends of a bold C. List what each
  refused mark had replaced, with the note that each piece becomes, before the rule is judged by the marks that go.
- A limit that a census of the clean pages set is read again on every page when a new rule leans on it. The bold C
  of one print is 2.46 to 2.57 staff spaces high, over `meter.COMMON_BOLD`'s 2.45, and its ends were read as notes
  once the cell in its bowl was refused. A census of every page of LitChoir with a wider limit (2.8, by the rule's own
  code), each piece looked at, put the limit at 2.6: the first false piece (a head with its stem) stands at 2.70, and
  two true signs past it stay out.
- A limit that a true sign misses by a little is moved to where a census of every mark that the rule's other limits
  take parts the signs, not to the one case. A heavy print draws its natural short: the right stroke goes 0.41 staff
  spaces past the foot of the left one, under `signs.FLAT_LEG`'s 0.6. Of the 57 flats with a stroke at the right of
  their bowl on LitChoir's scan pages, the true flats end at 0.0 or before, a slash and a bold C reach 0.11 and 0.28,
  and from 0.35 to 0.6 stood the natural, a bracket by hand and a rest by hand: the limit is 0.35. A mark that is no
  sign and is read as a natural in the place of a flat makes its note right where the key gives the pitch: a gain by
  chance, which the worklog names.
- A mark that a later step takes away was read by the steps before it. The ison's breve under the staff is taken from
  the notes (`drone.without_breves`), and its oval had stood at the side of the stem of the melody's note over it as that
  note's flag: a stem that ends in the box of a breve that was taken has no flag there (`drone.BREVE_TAIL`). A breve
  that a print sets close under the staff has bars 1.09 staff spaces long; of the 28 hollow heads that the breve test is
  asked about on LitChoir's chant pages, the other breves have 1.2 or more and a head that fails at one side only 0.82
  at most, so the limit moved into that gap. The letter of a hymn's last note stands over its fermata, past the note
  (`music.ISON_LAST`). Rules for one case: say so.
- One old engraving draws the flag of an eighth as a thin straight stroke that leaves the stem steeply before its end,
  back toward the head, and the older rules look for a flag at the stem's very end (`symbols.STEEP_FLAG`). The first
  form, with no limit for where the stroke leaves the stem and for how long it hugs it, gained 24 notes and lost 41,
  nearly all on copies by hand: a stroke that hugs a stem all its way, a thin flag at the very end and a slash across a
  stem pass as such a flag there. The census of every stem that the first form took, labelled by the typed hymn, gave
  the print's shape (the stroke leaves the stem 0.48 staff spaces from its end or more and touches it on 0.77 of its
  height at most), and a slash is a stroke that goes on straight at the other side of the stem. A rule for one print.
- A rule that reads one side of a mark by its shape asks the other side for its shape too. The flag of an eighth that
  comes back to its head meets the stem again, and past the loop the two are one stroke as high as the rim of a hollow
  head (`symbols.LOOP_FOOT`: of that foot only the rows as wide as a rim count). A foot no wider than a head still
  passed at a copy's final double bar line, whose cells the staff lines close, and the page lost a whole note on another
  staff: the side across the loop must hold a head (rows 0.75 of a head wide on 0.3 of its height; the true heads 0.35
  or more, the bar line none, the sharps of a key 0.2 at most). Two whole notes of a unison that touch close a small
  cell where their rims meet (`symbols.JOINT_CELL`). A cell half as large as the holes at both sides took 132 marks in
  its first form, and the cell between two half notes of a chord took both notes with it: the pair is one head high,
  its insides are those of whole notes, and the cell stands within 0.4 staff spaces of both.
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

## Agent skills

### Issue tracker

Issues live in the repo's GitHub Issues (`sweet-cicero/ScoreReader`). See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root, made when they are first needed. See `docs/agents/domain.md`.

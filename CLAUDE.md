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

Not reached yet: 87.2 % of the drawn notes over all 364 counted scores (99.3 % on software-made PDFs, 83.7 % on
scans; 89 scores at 99 % or more), 97.0 % of the notes on the clean copies (21,904 of 22,585, counted by the page;
21,847 of 22,606 as typed; 35 of the 78 counted scores at 99 %; 25 scores read every printed note, 35 every
syllable, 18 both, 21 have no note that is not there, 13 are whole in all three; 679 printed notes and 195 syllables
are lacking and 690 notes are read that are not there), and of their syllables 49.9 % with the own letter reader and 96.9 % with Tesseract, its larger
files and a list of words (6,044 of 6,239, counted by the page; 5,995 of 6,259 as typed; 94.8 % of the whole words; 36 scores at 99 % of the syllables);
89.0 % of all syllables with Tesseract (88.0 % on scans), and 90.2 % on the kit (6222 of 6901).
On the fresh test set, which no rule was set on: 95.5 % of the notes (39,879 of 41,761; 95 of 214 pieces at 99 %),
73.2 % of the syllables and 88.7 % of the whole words.

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
  ison that is counted by its letters, and a note that is given to both voices of a staff. The sheets staff by
  staff show the marks (470 of 839 after round 47). Look at the page before a figure of false notes is taken
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

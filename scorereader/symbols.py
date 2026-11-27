"""Reads the symbols of a clean page from its layers (scorereader.layers): note heads with their pitch place and their
stems. No model is used: every decision is a rule on the ink.

How a note is found. A note head is a thick mark with a stem. Printed music and almost every copyist follow one
custom: a stem that goes up leaves the head at its right half, and a stem that goes down leaves it at its left half.
So each thick mark is asked two questions: does ink climb from its right half, and does ink fall from its left half,
for more than a staff space past the mark? A mark with a "yes" is a head. A mark at the far end of another head's stem
is that note's flag or beam. A hollow mark without a stem is a whole note.

How its pitch place is found. On the clean page every staff line is level and its row is known. The place of a head
is the height of its middle between those rows: 0 is the middle line, +4 the top line, -4 the bottom line, and one
step is half a staff space. For a hollow head, the middle of its hole is used: a hole is the same on a clean and on a
smudged copy. A head beside the staff needs its ledger lines.
"""
from __future__ import annotations

import cv2
import numpy as np

SMALL = 0.12         # a thick mark under this area (staff spaces squared) is not a head
TALL = 1.35          # a thick mark higher than this many staff spaces is looked at for two heads, one over the other
STEM = 1.15          # a stem reaches at least this many staff spaces from the middle of its head
PAST = 0.55          # and at least this many staff spaces past the head's edge
SLIM_PAST = 0.44     # and it is slim for at least this many staff spaces past the head
INKED = 0.5          # and it has ink in at least this share of its rows past the head
GAP = 0.45           # a stem of a weak copy may break for this many staff spaces
SLIM_STEM = 0.62     # a stem is at most this wide, in staff spaces
REACH = 3.6          # a head stands at most this many staff spaces over or under its staff (three ledger lines)
CORE = 0.6           # the core of a head: an oval of this share of its width and height
HOLLOW = 0.08        # a head is hollow when this share of it was a hole
TAIL_FLAT = (0.45, 1.5, 0.3)   # a low flat mark at the end of the stem down of a head with its own stem up is no head
#   (at most this share of the page's head height, at least this many times as wide as high, the stem's end within its
#   rows and this many staff spaces): the end of the stem where a box beam by hand or a slur meets it. The step for the
#   flag at the far end of a stem took the stem from the head and read the mark as a note with that stem up. A census at
#   that step on every scan page of LitChoir (908 stems taken, each with the scorer's verdicts at both marks): of the 17
#   whose head has its own stem up and whose mark is at most 0.6 of a head high, the 8 marks under 0.45 are such ends
#   (the corner of a box beam or the curl at the end of a stem at five places on four pages, one of them a clean copy;
#   the crossing of a slur; the tail of a clef twice, where no note was read). A true quarter note under a U stands at
#   0.50; a mark at 0.46 is the corner of a box beam where no note was read, and is left as it is. The full reading
#   changed those five pages only. None: off.
HOLLOW_PAGE = (0.3, 0.03)   # on a page whose hollow heads have small holes: from this share of their usual hole, and
                            # never under the second number (None: off)
HOLLOW_WORN = (0.4, 0.2)    # on a page whose hollow heads have large holes (their usual hole is the second share or
#                    more): a head is hollow from the first share of that usual hole (None: off)
HOLLOW_PALE = (0.2, 0.015, 0.6, 10, 0.3, 0.5, 0.05, 5)   # ... and on such a page of a pale print a head is hollow only
#                    from the third share of the usual hole. The page shows the print by three signs. Of its heads
#                    with a stem that are not hollow (the fourth number of them or more), the first share hold a hole
#                    of the second share of the head or more. The usual hole of its hollow heads is the fifth share
#                    of the head or more. And its specks come in every size up to the limit: from the sixth share of
#                    the limit on in the seventh share of those heads, and in the last number of them or more.
#                    (None: off)
LINE_SLIT = (0.3, 2, 0.15)   # a filled head with a stem and a staff line or a ledger line through it (its middle at
#                     most this many staff spaces from the line) is a half note when a speck of paper of this many
#                     px or more is closed in over the line and one under it, the upper one this many staff spaces
#                     further right: the slit of a half note that a heavy print nearly closed (None: off)
LINE_OUT = 0.12      # ... and one of the two specks lies outside the line: its middle this many staff spaces or more
#                     from the row of the line. Paper cannot show in the rows of a line that runs through a head: two
#                     specks of a worn filled head lay there (a census of every scan page: 348 true half notes from
#                     0.134 on, eleven filled heads up to 0.112). Both specks outside the line by the thickness of a
#                     staff line lost 30 half notes of thick copies and copies by hand. 0: off
RIM = 0.8            # a note without a stem has its own ink at this share of the rim of its hole
JOINT_CELL = (0.5, 0.4, 0.25, 1.4)   # two whole notes of a unison that touch side by side close a small cell of paper
#                     between their rims and a staff line, over or under the place where they touch: a cell at most
#                     this share of each inside, within this many staff spaces of both, between two insides of at least
#                     this many square staff spaces, in a mark at most this many staff spaces high, is no hole of a head
#                     (a census of every mark where a cell is half as large as the holes at its two sides, on LitChoir's
#                     pages: the three such pairs of liturgy-one-is-holy and extra-beatitudes; the other cells were in
#                     clefs, beams, chords and letters, and the paper inside a d stands farther from the e beside it)
#                     (None: off)
FLAG_END = 0.7       # the flag of such a note begins at most this many staff spaces from the end of the stem
FLAG_LOOP = True     # a hollow mark beside the stem of a note with a printed flag is the flag's loop, not a head
FLAG_STEM = 0.3      # the stem of a note with such a flag may be slim for this many staff spaces only, when the loop
#                      was read as a head whose stem comes down to the note (0: off)
DIAG_PAIR = (1.6, 1.45, 2.4, 0.55, 0.45, 0.4, 0.3, 0.55, 0.9)   # a mark with a stem up and a stem down and one hole that no cut parts, at least the first number
#                     of times as wide as the page's heads, the second number of times as high, and at most the third number
#                     of times either, is a half note and a quarter note of two voices a second apart, side by side: the
#                     hollow head is the box of a head around the hole (the fourth number of a head to each side), and the
#                     rest of the mark is the filled head (the upper voice, at the left and a second over the lower): it
#                     holds ink of the fifth number of a head's box, its middle lies the sixth number of a head's width
#                     LEFT of the hole and from the seventh to the ninth number of staff spaces OVER it (a second, not a
#                     third), and a circle of ink the eighth number of a head's height fits in it. The two stems say that
#                     two voices sing one note: a filled note whose slur or flag closes a loop of paper has but one stem,
#                     and the upper-left-to-lower-right diagonal tells the pair from a head with a slur on the other side
#                     (4 marks on 4 pages of LitChoir, each looked at, and none on the fresh set: three are the pair,
#                     on liturgy-one-is-holy and its second scan and on communion-lords-prayer; the fourth is a piece
#                     of a word near the foot of a page of wedding-service, cut but read as no note before and after)
DIAG_SEEN = None     # a list: every mark that DIAG_PAIR cuts, for a census
SOLID_LOOP = 0.7     # ink this share of a head's height over or under a hole is a filled head beside a flag's loop (0: off)
LOOP_FOOT = (0.75, 1.0, 1.2, 0.3)   # the flag of an eighth that comes back to its head meets the stem again, and the
#                     two are one stroke for a while past the loop, at the side away from the head: of such a foot only
#                     the rows at least this share of a head wide are the rim of a hollow head (SOLID_LOOP's 0.4 of a
#                     head), where the foot is at most this share of a head wide in every row, the ink at the other side
#                     of the loop is at most this many heads high, and it holds rows that wide on at least this share of
#                     a head's height: a head. A census of every mark that a form without the last three limits took, on
#                     LitChoir's pages, each looked at: the eighths of liturgy-one-is-holy--s2, cherubic-lvovsky,
#                     trisagion-arabic and nativity-exapostilarion--s2 have such a head side; the double bar line at the
#                     end of a copy's staff, the sharps of a key and the piece of a clef have none, and a chord or a
#                     beam has a wider foot. The fresh set changed no page with the widest form. (None: off)
LOOP_SEEN = None     # a list: every mark whose foot LOOP_FOOT takes for the stroke of a flag, for a census
ROOM_HEADS = (0.75, 4.0, 3)   # a mark larger than a head with a room that a large flag or a short beam closes with
#                     the staff lines: its heads are the pieces that are left when an oval of this share of a head
#                     is pushed through its ink; the mark is at most this many heads wide and high, and holds at
#                     most this many heads (None: off)
ROOM_CHORD = (1.5, 2.3, 0.9, 0.3)   # (ROOM_HEADS) two heads a third apart, one over the other, that the oval leaves as one
#                     core: as wide as a head, from the first to the second number of heads high, with ink on at least
#                     the third share of a head's box; it is cut evenly into its two heads. A core of a head's size in
#                     the same mark that ends before such a chord (within the last share of a head's width past the
#                     chord's left edge) is the chord's sign, no head, and the room is closed by that sign, not by a
#                     flag. A sharp and a chord close a cell with the staff lines: the core of the chord was too high for
#                     one head and was dropped, and the core of two heavy sharps was read as a head (nativity-troparion
#                     and its --s3 scan, triodion-meatfare). (A census at this step on every page of LitChoir and of the
#                     fresh set: 20 and 33 such cores. The cut changes notes at 7 of LitChoir's and 3 of the fresh
#                     set's, each a chord of two voices or of one stem; the 3 sign cores beside a chord are two heavy
#                     sharps (two scans of one print) and a sign by hand. Two such cores in one mark, chords under one
#                     beam, make more heads than the mark may hold and stay as they were.) None: off
ROOM_SOLID = (1.6, 1.5, 0.9, 0.55, 0.5, 0.4, 0.4, 0.6, 1.3, 4.5)   # a mark this many heads high or more with the room of a flag:
#                     the solid ink over or under the room is its head, cut out of the mark (the stem runs along the
#                     room, inside the mark); solid ink this many heads high or more is two heads of two voices that
#                     touch; a room higher than this share of a head and at most this share of a head wide is a
#                     flag's loop and no hole of a hollow head, in a mark that is this share of a head higher than
#                     the room; a room this share of a head or more beside the head's column is a flag's room; in
#                     the column, the ink at the two sides of a flag's loop is at most this share of a head wide
#                     together; a room beside the column that is wider than a head and under this many times as
#                     high as wide is the hole of a hollow head; a loop in the column is this many times as high as
#                     wide or more; a mark with two rooms is cut only this many staff spaces or more after the start
#                     of its staff, where no clef stands (None: off)
SOLID_ROOMS = True   # also when the mark has two holes or more: a staff line cuts the room of a flag's loop in two
SOLID_FLAG = True    # a filled head beside a flag's loop has a flag: with no flag found, the mark is a hollow head
WHOLE = (1.12, 0.98, 0.8, 1.7)   # a whole note: its width over its height, its width over the page's head width, and
                                 # its height over the page's head height (least, most)
HEAD_WIDE = (0.65, 3.0)   # the width of a head, in staff spaces: from a small slanted stroke to a large hand-drawn oval
HEAD_HIGH = (0.3, 2.0)    # and its height
SHORT_STEM = (0.9, 0.45)   # a head on a ledger line may have a stem this short: from its middle, and past its edge
SHORT_SLIM = 0.15    # such a short stem is slim for this share of its way past the head
RIM_WINGS = (0.25, 0.3)  # a ledger line at the rim of a hollow head: in this many staff spaces past the head, at both
                         # sides, it has ink in at least this share of the columns
LEDGER_BESIDE = (0.3, 0.7, 1.4, 0.6, 1.6, 0.5, 0.7)
#   A level run that ledger_lines finds through the middle of a filled head beside the staff can be the ink of another
#   head that touches it at one side at the same height (two voices a second apart, set side by side), and the head is
#   then read as sitting on a ledger line that is not there. Such a row is no ledger line where it lies within (0) of
#   the head's height from the head's middle, the head is a head's size (at least (1) of the page's head height, at
#   most (2) of its width), the row has ink in less than RIM_WINGS[1] of the columns past the head at one side, and at
#   the other side, in one head width past the head, at least (5) of the columns hold solid ink ((6) of the column's
#   run or more) from (3) to (4) of the head's height, one of them among the first three. Two ledger lines one over the
#   other are as high as a head and not solid. A census of every such row of LitChoir's pages (5,402 rows of filled
#   heads on 420 pages; 2,345 on the fresh set) took 44 rows on 36 pages and 5 on the fresh set; without the solid ink
#   it took two stacked ledger lines beside a head of samaritan-megalynarion and pencil, words and a hand's marks.
LEDGER_BESIDE_SEEN = None    # a list: a census of every row that LEDGER_BESIDE asks
RING_SIDE = True
#   A pencil ring, or a long arc by hand, that passes the side of a filled head leaves the head's mark upward and downward
#   at that side, and the test for a beam took its upper half with the head's own stem for the two stems of a beam: the
#   head was no head. The two ways at one side are one ring where both are stems, both lean the same way from the mark
#   (the stroke bows past it), one of them is the arc of a ring (STEM_ARC), and the test for a beam would take one of
#   them: then neither is a stem. A census at the reader's own step of every side of a head's mark whose ways up and down
#   are both stems (9,891 on LitChoir's pages, 8,699 on the fresh set): 3,312 and 2,840 lean the same way, 177 of those on
#   LitChoir have an arc and none on the fresh set, and the test for a beam takes one of them at 11: the belly of 8 treble
#   clefs, the curl of a flag, and 3 heads that a ring or an arc by hand passes (an F4 of holy-saturday-koinonikon and a
#   chord of st-basil-in-thee-rejoiceth). The clefs and the curl stand where no note is read, and their pages read as before.
RING_SIDE_SEEN = None    # a list: a census of every side that RING_SIDE takes
PLACE_MASS = None    # off. (0.35, 0.08): a head in the staff whose middle was measured this far or more from the middle
#   of its place (in places: the border of two places lies at 0.5) takes the place of the middle of all its ink, when
#   that lies in the place next to it at that side, this far or more past the border. The middle of a hollow head is
#   the middle of its hole. With no margin the rule gained 8 notes on the clean copies and lost 2, and 27 and 24 on the
#   other scans; with the margin 8 and 0, 28 and 10 on all scores, but 0 and 6 on the fresh test set, and no measure
#   of the head separates the mended notes from the broken ones
NO_LEDGER_FIVE = 5.75# and up to this place it stands in the first space; past it, its measured place stays
NO_LEDGER = 6.3      # a head with no ledger line, up to this place beside the staff, stands in the first space (0: off)
FAR_STEM = (2.0, 8.4, 0.75, 1.35)   # a head past NO_LEDGER with no ledger line is a note when its stem goes on this many
#                      staff spaces past it, up to this place, and its box is from this to this share of the page's head (None: off)
PALE_STEM = (25, 0.5, 0.25)   # the stem of such a head goes on as pale ink where the copy lost it: a column that is
#                    darker than the paper at both sides of it by this many grey levels (the paper this many staff
#                    spaces away), over gaps of at most the last share of a staff space. The pale part counts for
#                    FAR_STEM (None: off)
WORD_STEM = (0.35, 2.0, 0.7, 1.4, 1.0)   # a mark at most 2.0 staff spaces before the words is a note when its upright
#                    ink goes on this many staff spaces past it and into the words (or it is slim and ends at most
#                    1.0 staff spaces before them), and the mark is from this to this share as high as the heads of
#                    the page (None: off)
WORD_MARKS = True    # a thick mark in a band of words is a letter: no head and no sign
LEDGER_WORDS = True  # a ledger line is looked for up to the words, not in them
HEAD_NEAR = 1.5      # the page's head size comes from the marks at most this many staff spaces over or under a staff
HOLE_PLACE = True    # the place of a hollow head is the middle of its hole; else the middle of its ink
LINE_HOLE = (0.38, 0.3)   # a hollow head whose hole stands this near the border of two places (from this share of a
#                    place to one less it) and whose box has its middle at most this many places from a staff line sits
#                    on that line: the line hides the half of the inside that it crosses, so the hole that is left has
#                    its middle half a step off. A census of the stored notes of every page of LitChoir: 30 such heads,
#                    8 read a step off by the typed hymn (2 on the clean copies) and 2 read right (a thick copy and a head
#                    by hand); the other 20 are marks that are no notes (the paper that a beam or a slur closes with a
#                    line) or a pitch far from the typed one. (None: off)
LEDGER_INK = True    # a ledger line is ink: the filled inside of a hollow head does not count for it
HAND_FLAT = 1.25     # the bowl of a flat that a hand drew is at most this wide, in staff spaces (0: off)
SHARP_SLIM = 0.3     # the strokes of a sharp are slim for this many staff spaces where they leave its mark
PAIR_STEM = (1.3, 2.3, 1.25, 0.65, 0.4, 0.08, 1.85, 0.25)   # two filled heads a second apart at the two sides of a
#                     stem, as one piece of ink (two voices with their stems back to back, the upper head at the
#                     left): the piece is this many heads wide (least, most), this many heads high or more and at
#                     most this many staff spaces higher than a head (a third is a whole space higher), the stem
#                     cuts it into two parts of this share of a head or more each, and the ink at the left of the
#                     stem lies this many staff spaces or more higher than the ink at its right; a piece up to this
#                     many heads high is such a pair too when the ink at the left lies this much higher: large
#                     heads a second apart, where two voices on one note or a third lean less (None: off)
PAIR_OVER = True     # where the stem leaves one of the two parts of such a piece narrower than a head can be
#                     (HEAD_WIDE), the two heads lie across the stem (the stem of the upper voice goes up at the right
#                     of its head, the stem of the lower voice down at the left of its head, and the heads overlap):
#                     each head is as wide as a head from its own side of the piece, and how the piece leans is read
#                     from the columns that only one of the two heads has
STUB = 0.3           # a thick stem that is this long (staff spaces) at the top or the bottom of a mark is cut off (0: off)
STUB_HIGH = 1.25     # when the mark is this many times as high as the heads of the page
ARM = (0.75, 5.0, 2.3, 0.25, 0.65, 0.3, 0.4)   # a bold bow that touches a hollow head is one piece of thick ink with it, far too
#                    wide for a head. In a mark with a hole that is over [2] times as wide as the heads of the page, the
#                    ink that holds no disc of [0] times the height of the page's heads (a head with its hole does, a
#                    bow that lies on a staff line does not) is such a bow where it goes on for [1] staff spaces or
#                    more, is at most [3] times as high as it is long and at most [4] staff spaces thick on the
#                    whole, and it is the bow of a tie: its middle lies [5] staff spaces or more off the straight way
#                    between its ends, and its ends are at most [6] apart in height. It is taken off the mark, with
#                    the crumbs of it that hold no such disc. A flag and the stroke of a hand are shorter or
#                    thicker, and a beam is straight and leans. The ink stays on the page, for the ties (None: off).
WINGS = 0.25         # a ledger line shows this far at both sides of a head's body, in staff spaces (0: off)
WHOLE_BESIDE = (0.35, 0.2, 0.2, 0.2)   # a whole note that touches the head of the other voice has no stem: the stem
#                    of a filled head, at most this many staff spaces from the stem the hollow oval was given, is not its
#                    own when the two boxes are at most this far apart, their left edges are this near, and the oval is
#                    wider than the filled head by this much (None: off)
PAIR_SHARP = (0.3, 0.3, 0.5, 0.35, 0.7, 1.4, 0.7, 0.5)   # the lower head of two voices that touch, read as a sharp: a
#                    filled mark that _kind calls a sharp is a head where a head over it with a stem up and a stem down
#                    stands within the first number of staff spaces at its sides, reaches into the mark's rows by the
#                    second number at most and stands the third number over them at most, the stem down of that head
#                    is the mark's own way down at its left to within the fourth number, the mark is the fifth to the
#                    sixth number of the page's heads wide and high, the head over it at least the seventh, and no
#                    other head on that head's stem up shares the last number of its columns (None: off)
RIM_STEM = 0.3       # upright ink that ends in the box of another head of its piece of ink, or this many staff spaces
#                    past it, is the rim of that head and no stem (0: off)
RIM_BOW = None       # (0.7, 0.2): ... or the first number past it where both heads are hollow, that head has no stem and the ink
#                    runs inside its box, the second number or more from its edges: the side of a whole note is thick,
#                    and a bow that leaves the note goes on from it. A stem that two heads share runs along their
#                    edge. Off: it mends one page of the clean copies (1 note), and on 13 other pages it takes the
#                    stem from a head beside a sharp, from a rest drawn by hand and from a letter.
CELL = (0.27, 1.0)   # paper that is closed in between two upright strokes and two staff lines is no whole note: at both
#                    sides of the hole the ink is at most the first number wide (staff spaces; a whole note is thick at
#                    its sides), and both strokes go on for the second number or more past the hole, up or down (a bar
#                    line, the stem of another note) (None: off)
LEDGER_DOT = (2.0, 0.9, 0.6, 0.8)   # the dot of a head on a ledger line stands at the end of the line or past it: the
#                    line is followed for this many staff spaces to the right of the head, the dot is at most this far
#                    past its end, the line is at least this long past the head (a shorter one that thickens is the end
#                    of a pen's stroke), and a dot that touches the line has no ink this far over or under the line (a
#                    stroke that goes on is a stem or a beam) (None: off)
LEDGER_THROUGH = 0.25   # a ledger line that crosses a hollow head between this share of its height and one less this share runs
#                    through it: the head's middle is then the middle of its box, not of its paper (0: off)
LEDGER_SIT = (0.2, 0.9)  # a filled head whose middle lies this many staff spaces past its last ledger line sits on
#                    top of the line, when the line stands at most this many staff spaces from the line before it (a
#                    print that draws its ledger lines near the staff) (None: the wider limit of 0.27)
LEDGER_SIT_FOOT = None   # (0.7, 0.1): when that line lies in the lowest part of the mark (from this share of its height on,
#                          counted from the far edge), the head sits on it from this many staff spaces on. Off: 3
#                          notes gained and 2 lost on the clean pages, and the measures do not tell them apart.
LEDGER_FOOT = (0.7, 0.3, 1.2, 0.3, 0.45)   # a head beside the staff with no ledger line found, but with thin level ink at one
#                          side of its foot (from this share of its height on), this many to this many staff spaces from
#                          the staff, at least this long and at most this thick: it sits on its ledger line (None: off).
#                          The second number was 0.4 until round 73. A census of every head beside the staff with no
#                          ledger line, on all 657 pages (11,616, of them 460 with a wing at their foot), gave 0.3: the
#                          true heads of the first space have their wing at most 0.28 staff spaces from the staff and
#                          the four true heads on a dash of their own stand at 0.33 to 0.36, where a hand or a worn
#                          print sets the dash close to the staff.
LEDGER_OWN = True   # no ledger line of a head lies past the head: where a level row of ink stands in the head's box,
#                     the rows further from the staff than the last such row are not counted. They are the ledger line
#                     of the next head of a chord on two ledger lines (the head nearer the staff was read a step off,
#                     between the two lines), the rim of a hollow head that one print draws as level and as long as
#                     its ledger line (joined with the line it moved the line off the head's middle, and the head was
#                     read as sitting between the staff and the line), a slur over the head or a row of words. Each
#                     of the 35 heads of LitChoir's pages whose rows it cuts was looked at, and 4 of the 41 of the
#                     fresh set. Alone: no note of the clean copies, 11 gained and 3 lost on all scores, 39 gained on
#                     the fresh set (two pieces of one engraving whose tenor and bass stand a third apart on two
#                     ledger lines). The 3 lost are two heads by hand that have no line of their own to count, a half
#                     note that sits on its dash and a head that hangs under the staff: their reading before stood on
#                     the rim of the head, counted as a line. False: off
LEDGER_CLOSE = (0.85, 6, 0.15, 1.0, 1.7, 0.35)   # a print (a music typewriter) sets its ledger lines closer to each other
#                      than its staff lines, so a head on its third line measures a third too low and the count of its lines
#                      was not trusted. The page shows its own gap: the median gap from the staff to the first ledger line
#                      and from line to line, over its filled heads with a stem whose count holds, where that is at most
#                      the first number of staff spaces, from the second number of gaps on. A count of two lines or more
#                      that was not trusted holds there where each of its own gaps is within the third number of the
#                      page's gap, the place measured with that gap is within the fourth number of the count, and the
#                      lines are dashes of one length (each end at most the fifth number of staff spaces from the head's
#                      middle, the ends within the sixth number of each other: a slur runs on) (None: off)
WHOLE_FOOT = (0.9, 0.4, 1.2, 7.5, 0.3, 0.15, 0.7)   # a hollow oval with no stem (a whole note by its shape) whose edge toward the staff is a
#                      level line at least this share of the mark wide, from this to this many staff spaces from the
#                      staff, is a whole note that sits on its first ledger line, up to this measured place: one print
#                      sets that line no wider than the note, so it shows at neither side, and a head beside the staff
#                      with no ledger line needs a long stem otherwise. The line is looked for in this many staff
#                      spaces at the edge of the mark. The note and its line stand alone in paper: the piece of ink
#                      that holds the mark goes on at most the sixth number of staff spaces over and under the
#                      mark and the seventh number at its sides (the ends of the line). The bowl of the letter p of
#                      a dynamic mark is such an oval with a level top too, and its stroke goes on under it: the
#                      fresh set showed it, and the eleven notes of LitChoir's pages gave the measure (None: off)
LEDGER_FROM = 0.5    # a ledger line lies at least this many staff spaces from the staff
LEDGER_TWIN = (0.3, 3)   # two rows of level ink less than half a staff space apart are one ledger line that leans or
#                      that is thick, unless paper parts them: where they stand this many staff spaces apart or more
#                      and this many rows between them are paper at both sides of the head, they are two strokes, a
#                      ledger line and the arc of a pencil ring or a stroke of the pen. The ledger line is the one
#                      that stands nearer to a whole number of staff spaces from the staff, and the other one goes
#                      where it lies outside the head's box. A row of the head's own ink is left to the older rules:
#                      with it the first form gained 3 notes and lost 1 on LitChoir's scan pages (a head by hand that
#                      is read from its upper half, right only by the row between the two). A census of every head
#                      with two such rows (105 on the scan pages, 26 of them parted by paper; round 81): two have
#                      the stray row outside the box, a printed head in a pencil ring on a clean copy and a half
#                      note by hand whose upper rim stands apart, both read a step low before. None: off
LEDGER_PAPER = (0.75, 0.3, 0.15, 0.8, 0.7, 1.3, 0.3)   # a print that sets its first ledger line near the staff (up to this
#                      many staff spaces from it) has little room for a head past that line: the head is a half moon on
#                      top of the line, and its middle lies hardly past it. But a head ON the line has its near half
#                      between the line and the staff. Where at most this share of a band at the line's near edge
#                      (this many staff spaces high, this many wide, under the head's middle) is ink, the head sits
#                      past the line. One head stands there, no stem alone and no oval with the words under it:
#                      0.3 staff spaces past the line the mark is from this to this share of a head of the page
#                      wide. And the line is a line, no rim of a wide oval: it is this many staff spaces longer
#                      than the mark is wide there (None: off)
ORPHANS = (0.7, 1.5) # a thick mark with no stem, from this to this many times as wide and as high as the heads of the
#                    page, is a head when an upright stroke that no head has ends at its edge (None: off)
WHOLE_HALF = 0.3     # the same over or under a half note, when the oval is wider than it by this many staff spaces (0: off)
WHOLE_APART = (0.7, 0.2, 0.2, 0.2, 0.8)   # a whole note a third under or over a note with a stem: the two boxes are at
#                      most this many staff spaces apart, the oval is wider than the head by this much, the stem
#                      stands this far inside the oval's far edge, the way from the oval to the stem crosses this
#                      much paper, and the head with the stem is this share as wide as the page's heads with stems
#                      (a smaller mark is a piece of a head) (None: off)
WHOLE_OVER = 0.4     # the oval may begin this many staff spaces left of the head it touches (it is set in the middle
#                      under it); 0: only as far as WHOLE_BESIDE says
WHOLE_STAFF = 0      # in the staff a whole note is at least this many times as wide as it is high (0: as WHOLE says).
#                    Off: with 1.0 it gained 1 note on the clean copies, lost 1 and wrote 8 notes that are not there.
WHOLE_FILLED = 0     # a filled oval without a stem, as large as a whole note, that touches a whole note over or under
#                    it (their middles at most this many staff spaces apart sideways) is a whole note whose hole
#                    the print filled (0: off). Off: with 0.5 it gained no note on the clean copies and lost 4.
WHOLE_STACK = (0.15, 0.75, 0.25)   # whole notes one over the other, in line: on a weak copy the sides of the upper ones
#                      are followed from the lowest one as its stem, over the staff lines between them. A stem of a
#                      hollow oval is none where it ends in the rows of another hollow oval that has no stem of its own
#                      (or at most the second number of staff spaces past it), that is as wide against its height as
#                      a whole note, and whose two edges stand within the first number of staff spaces of the oval's
#                      own: the stem of a chord goes on past its last head, and that head has it too. Such a stem has
#                      no ink of its own: outside the ovals and the staff lines its column holds ink in at most the
#                      third number of staff spaces. (A census of the 32 stems of the first form on LitChoir's pages:
#                      the closed paper between a slur, a stem and the lines, and a whole note of the next staff, are
#                      no ovals of that shape (2 true half notes lost their stems), and the strokes of a sharp go on
#                      past its cells, 0.35 staff spaces or more; the four true stacks have 0.17 at most.) None: off
WHOLE_UNISON = 0.25  # two voices on one note, a half note and a whole note side by side: the oval at the far side of
#                      the stem, its middle at most this many staff spaces from the height of the stem's own head,
#                      has no stem (0: off)
WHOLE_SECOND = (0.25, 0.85)   # a whole note a second from a note with a stem, in the order that no chord has. In a
#                      chord the lower head of a second stands left of the stem and the upper head right of it. An oval
#                      left of a stem down and from this to this many staff spaces over the stem's own head, or
#                      right of a stem up and as far under it, is the whole note of the other voice (None: off)
SLIT_ONE = (0.3, 0.01, 0.1, 0.32, 0.5, 0.47)   # a filled head with a stem and a line through it (its middle at most
#                      this many staff spaces from the line) that holds one speck of paper where the slit of a half
#                      note lies: the speck is this many square staff spaces or more, its middle from this to this
#                      many staff spaces over or under the line, over the line in the right part of the head (from
#                      this share of its width on) or under the line in the left part (up to this share). The head
#                      may be a half note whose slit the print closed but for the speck: the music decides
#                      (music.SLIT_SPAN) (None: off)
SLIT_LEDGER = (0.3, 0.45, 0.4)   # the line through a head beside the staff is the ledger line as the ink shows it: within
#                     this many staff spaces of its place, the row that sticks out this far at both sides of the head, with
#                     ink on this share of that way. The speck of SLIT_ONE is measured from it (None: from the place)
SLIT_PAGE = (0.02, 0.35, 0.2, 0.8)   # ... but not on a page of a worn print, whose filled heads hold specks of paper
#                      anywhere: where more than this share of the page's filled notes with a stem hold a speck that
#                      is no slit (its middle at most this many staff spaces over or under the middle of the head, and
#                      from this to this share of its width), a speck says nothing (see slit_page; None: off)
WHOLE_SLIT = (1.2, 1.5, 0.15, 0.01, 0.1, 0.32, 0.4, 0.6, 0.83, 1.3)   # an oval without a stem on a line, from this to
#                      this many times as wide as the page's heads, its middle at most this many staff spaces from
#                      the line: a whole note whose hole the print closed but for a speck of paper of this many
#                      square staff spaces or more, its middle from this to this many staff spaces over or under the
#                      line and from this to this share of the oval's width. The oval is full: its ink fills this
#                      share or more of the middle part of its box (three fifths of its width), and it is at most
#                      this many times as high as the page's heads. A sharp and a number of the time signature on
#                      a thick copy close in such specks too, but their strokes leave paper open at the sides and
#                      fill 0.8 of that part at most (None: off)
LINE_CHORD = 0.75    # hollow heads that touch, each on a line: the first and the last cell of their insides lie this
#                      many staff spaces further apart than as many heads less two in the spaces would (0: off)
LINE_CHORD_ENDS = 4   # in a mark with this many cells or more (three heads on lines), the first and the last cell count
#                      twice against the largest cell: they hold half an inside each, and a smudge at the lowest head
#                      left the last cell of one final chord a hair under a quarter of the largest (five heads were
#                      cut where three stand). With three cells (two heads) the same count changes 119 marks of
#                      LitChoir's scan pages that are read right today, and it is not made there. A rule for one
#                      case: of the 136 marks where the count changes, 17 have four cells or more, 15 of them clefs
#                      and one the numbers of a time signature, which give no heads either way; the notes of one
#                      page change, the chord's (round 81). 0: off
LINE_PAIR = (0.9, 1.4, 1.6, 2.1, 0.22, 0.25, 1.0)   # a hollow mark that is from this to this many heads wide and from this to
#                      this many heads high holds two heads a third apart, one over the other, and no more: where
#                      its insides give three holes, a staff line has cut the inside of a head in two, and a half of
#                      it can be lost at the rim. The two heads stand a step over and a step under the middle of the
#                      mark. The insides are together this share of the box of a head or more: the specks of paper
#                      between two filled heads are less (None: off). The three holes stand one over the other, each
#                      this share of a head's height or more under the one before, and in a zigzag: the middle one
#                      lies to one side of both others (the inside of a head leans, so its upper half lies right of
#                      its lower half). Two holes side by side are the two heads of a second, or a head and the room
#                      between it and its sign. And the two heads are half notes: a stem goes this many staff spaces
#                      or more past the mark, up or down. A scribble by hand at the start of a staff had the three
#                      holes of such a pair, and no stem
SIGN_GLUED = (1.25, 2.3, 1.5, 0.3, 1.4, 0.5, 0.8, 1.3, 0.6, 2.0, 0.95)   # a sharp whose right stroke touches its head is one mark
#                      with the head (None: off). The mark is from this to this many times as wide as the heads of the page
#                      and at most this many times as high; a stroke goes through its left third, up and down, from
#                      this to this many staff spaces past the mark (the stroke of a sign: a stem is longer); the mark
#                      is cut at most this many staff spaces right of that stroke, where it is narrowest; what is left
#                      of it at the right is from this to this many times as large as a head, has ink in this
#                      share of its box, and a stem at its right side that goes this many staff spaces past it; the
#                      other stroke of the sharp stands at most this many staff spaces left of the first
SLUR_STEM = (1.7, 0.28, 2.5, 0.2, 1.0, 0.5, 0.6, 0.7)   # the end of a bold slur that meets a head is no second stem
#                       (None: off). Of a stem up and a stem down at one head, the one that goes at most 1.7 staff spaces
#                       past the head and leans 0.28 staff spaces or more away from the head on that way, where the other
#                       goes 2.5 staff spaces past the head or more and leans less by 0.2. A printed stem stands upright;
#                       the slur is steep where it meets the head and bends away. The stroke of a hand bends too, and
#                       then it goes on upright: over the next 1.0 staff space past the followed end, ink within 0.5
#                       staff spaces of the end's column in 0.6 of the rows or more is a stem, and it stays. The mark
#                       is 0.7 staff spaces high or more: a whole head.
CHORD_STEM = (0.7, 1.3, 0.75, 1.3, 0.3, 0.25, 1.25, 0.02)   # a filled mark with no stem, from this to this many
                         # heads wide and from this to this many heads high, is the next head of the chord of a
                         # read head, past the end where that head's stem begins: the stem's column lies at most
                         # this many staff spaces inside the mark's edge or this many past it, at most this many
                         # staff spaces of paper lie between the two, and the mark closes in at most this much
                         # paper (staff spaces squared; a whole note on a ledger line closes in two slivers)
                         # (None: off)
CHORD_GONE = True     # CHORD_STEM gives a mark the stem of a head that gone_stems() or thin_heads() read, as it gives
                      # the stem of any other head. The first form left such heads out: a printed C4 with no stem under
                      # an F4 whose stem gone_stems() put together from its pieces stayed lost (transfiguration-troparion
                      # --s2). 7 marks on LitChoir's pages, each looked at: 5 true heads of a chord (5 notes gained), a
                      # printed G3 that the count lines up with no typed note, and a head by hand read a step low;
                      # none on the fresh set (False: off)
MIDDLE_KIND = 0.4     # the middle head of a column on one stem line, with no head of the column within this many staff
                      # spaces of its height, goes with the neighbour of its own kind (filled or hollow) (None: off)
MIDDLE_LEAVES = 1.8   # ... where that neighbour's stem leaves the column on its side and ends this many staff spaces from it
MIDDLE_SURE = (0.08, 0.16)   # ... and where each of the three is surely filled (a share of paper under the first number) or
#                     surely hollow (the second number or more)
MIDDLE_OWN = True     # ... and not where the neighbour of its own kind holds a stem on that side that ends within MIDDLE_LEAVES
#                     of it: the end of a bow that runs into the column is no stem of a note (False: off)
TWO_HEADS = (1.5, 1.35)   # a filled mark with a stem up and a stem down is two heads when it is this many times as wide
                     # as the heads of the page (side by side), or this many times as high (one over the other); (): off
GLUED_TWO = (1.7, 0.6, 1.6, 0.6)   # a mark that is no head only because it is too high, or that is a beam only
#                     because the stem of a neighbour leaves it, is the two heads of two voices a third apart that touch,
#                     where a stem goes up at its right and a stem goes down at its left: it is cut as TWO_HEADS cuts, where
#                     it is at least the first number times the box of the page's heads, each part from the second to the
#                     third number times that box, and each part at least the fourth number times as high as the page's
#                     heads (a clef cut so leaves a large part and a thin one) (): off
SIDE_TWO = (1.5, 2.4, 1.3, 0.25, 0.3, 0.45, 0.55)   # a mark with one stem line through its middle, up and down, is the two heads
#                     of two voices on one note, side by side (the upper voice at the left with its stem up, the lower
#                     one at the right with its stem down: a half note beside a quarter note): the mark is from the
#                     first to the second number times as wide as the heads of the page and at most the third number
#                     times as high, the four ways of upright ink that leave it stand within the fourth number of staff
#                     spaces of one column, that column lies in the mark at least the fifth number of its width from
#                     each side, and each part holds ink of at least the sixth number times the box of a head and a
#                     circle of ink at least the seventh number of the page's heads high (its hole counts as ink:
#                     the strokes across the stem of a tremolo are slim). Two voices a second apart stand so too,
#                     the upper head at the left (None: off)
SIDE_HEAD = (0.35, 0.3, 0.2, 0.15)   # a mark that is read as one head, with a stem up and a stem down that are one line through its
#                     middle, is the same pair of two voices side by side (the upper voice at the left with its stem up,
#                     the lower one at the right with its stem down), cut as SIDE_TWO cuts it, with SIDE_TWO's limits: the
#                     two stems stand within the first number of staff spaces of each other (the heads of such a pair
#                     overlap by a stem's width, so the stem up stands a little right of the stem down), and the rows
#                     of a part that hold at most the second number of staff spaces of ink are the root of the other
#                     head's stem, not its own head; the right head stands lower than the left one, a second: its top
#                     and its bottom each at least the third number of staff spaces under those of the left one (None:
#                     any); and closed paper of a part whose middle lies the fourth number of staff spaces or more from
#                     the middle of its head, toward the other head, is the paper that the two heads close with the
#                     stem line, no inside (1 mark of LitChoir, on the second scan of liturgy-one-is-holy, and none
#                     on the fresh set)
SIDE_SEEN = None     # a list: every mark that SIDE_HEAD cuts, for a census
SIDE_WHOLE = False   # off: such a mark would have to be the whole piece of ink, because on a thick copy the staff
#                     line joins the two heads of a second with the piece under them, and the lower head was read
#                     twice. With the limits above as they are it changes no note on any page
SIDE_CELL = True     # the paper between the stem line of such a pair, the staff line over it and the head beside it
#                     is open paper with a stem, and no head: its stem is the pair's (False: off)
SIDE_LEDGER = True   # the ledger lines of such a pair are looked for past the pair, not past each head: the rim
#                     of the hollow head beside a filled one is level ink at its side (False: off)
GLUED_THROUGH = (0.5, 0.4)   # ... but not where upright ink leaves the mark up and down, each at least the first number
#                     of staff spaces, in columns at most the second number apart: a bar line or a stem through a box of
#                     staff lines on a thick copy
GLUED_FAT = 0.5      # ... and each part holds a circle of ink at least this share of the page's heads high (a half note
#                     whose rim is thin is refused too: two pairs of glued half notes on a copy by hand)


def pitch_place(staff: dict, y: float) -> float:
    """The place of a height on a staff, in half staff spaces from the middle line (up is positive)."""
    rows, space = staff['rows'], staff['space']
    if y < rows[0]:
        return 4 + (rows[0] - y) * 2 / space
    if y > rows[4]:
        return -4 - (y - rows[4]) * 2 / space
    return float(np.interp(y, rows, [4, 2, 0, -2, -4]))


def place_row(staff: dict, place: float) -> float:
    """The height (row) of a pitch place on a staff."""
    rows, space = staff['rows'], staff['space']
    if place > 4:
        return rows[0] - (place - 4) * space / 2
    if place < -4:
        return rows[4] + (-4 - place) * space / 2
    return float(np.interp(-place, [-4, -2, 0, 2, 4], rows))


def _cut_rows(mask: np.ndarray, holes: np.ndarray, space: float) -> list[tuple[int, int]]:
    """Cuts a thick mark into the parts that stand one over the other, at the narrow places: (first row, last row)
    of each. Two heads of a chord touch at a narrow place, so the ink of the rows has a valley between them. A mark
    is never cut through a hole: one large hollow head stays whole."""
    height = mask.shape[0]
    if height <= TALL * space:
        return [(0, height - 1)]
    mass = mask.sum(axis=1).astype(float)
    window = max(3, int(round(0.2 * space)) | 1)
    smooth = np.convolve(mass, np.ones(window) / window, mode='same')
    edge = int(round(0.3 * space))
    if height - 2 * edge < 3:
        return [(0, height - 1)]
    cut = edge + int(np.argmin(smooth[edge:height - edge]))
    hole_rows = (mask & holes).sum(axis=1)
    if hole_rows[max(0, cut - 1):cut + 2].max() > 0:
        return [(0, height - 1)]
    if smooth[cut] <= 0.7 * min(smooth[:cut].max(), smooth[cut:].max()):
        upper = _cut_rows(mask[:cut], holes[:cut], space)
        lower = _cut_rows(mask[cut:], holes[cut:], space)
        return upper + [(first + cut, last + cut) for first, last in lower]
    return [(0, height - 1)]


def _without_stub(mask: np.ndarray, space: float, usual: float = 0.0) -> np.ndarray:
    """A thick pen draws a short stem as thick as a head, so the stem is a part of the head's mark: the mark is too
    high, and no stem leaves it. The rows at the top or the bottom of a mark that are as narrow as a stem are taken
    off the mark. The ink stays on the page: it is found again as the stem that leaves the head."""
    widths = mask.sum(axis=1)
    height = len(widths)
    if not STUB or height < STUB_HIGH * usual or widths.max() < 0.9 * space:
        return mask
    limit = min(SLIM_STEM * space, 0.5 * widths.max())
    under = 0
    while under < height and widths[height - 1 - under] <= limit:
        under += 1
    over = 0
    while over < height and widths[over] <= limit:
        over += 1
    least = STUB * space

    def upright(rows: np.ndarray) -> bool:
        # A stem stands in the same columns in all of its rows. The end of a slanted stroke is narrow too, but it
        # moves sideways from row to row.
        columns = np.nonzero(rows.any(axis=0))[0]
        return len(rows) >= least and columns[-1] - columns[0] + 1 <= SLIM_STEM * space \
            and np.median(rows.sum(axis=1)) >= 0.6 * (columns[-1] - columns[0] + 1)

    under = under if under and upright(mask[height - under:]) else 0
    over = over if over and upright(mask[:over]) else 0
    if not (under or over) or height - under - over < HEAD_HIGH[0] * space:
        return mask
    mask = mask.copy()
    mask[:over] = False
    mask[height - under:] = False
    return mask


def _line_specks(layers: dict, mark: dict, staff: dict) -> tuple[float, list[tuple[int, float, float]], int]:
    """The specks of paper that the ink closes in within the box of a mark: the row of the nearest line (a staff
    line, or the place of a ledger line), the specks as (area, column of the middle from the left edge of the box,
    rows of the middle under the line), and the width of the box."""
    space, rows = staff['space'], staff['rows']
    lines = list(rows) + [rows[0] - step * space for step in (1, 2, 3)] + [rows[4] + step * space for step in (1, 2, 3)]
    line = min(lines, key=lambda row: abs(row - mark['cy']))
    ink = layers['ink']
    x0, y0 = max(0, mark['x0'] - 1), max(0, mark['y0'] - 1)
    x1, y1 = min(ink.shape[1], mark['x1'] + 2), min(ink.shape[0], mark['y1'] + 2)
    paper = (1 - ink[y0:y1, x0:x1]).astype(np.uint8)
    count, _, stats, middles = cv2.connectedComponentsWithStats(paper, connectivity=4)
    specks = []
    for label in range(1, count):
        x, y, wide, high, area = (int(value) for value in stats[label])
        if x == 0 or y == 0 or x + wide == paper.shape[1] or y + high == paper.shape[0]:
            continue        # the paper around the head
        specks.append((area, float(middles[label][0]), float(y0 + middles[label][1] - line)))
    return line, specks, x1 - x0


def _line_slit(layers: dict, mark: dict, staff: dict) -> bool:
    """A half note on a line whose slit a heavy print nearly closed: the staff line (or a ledger line) runs through
    the head, and of the slit two specks of paper are left, one over the line and one under it. The slit leans as the
    head does, so the upper speck stands to the right of the lower one. A filled head holds no paper at all."""
    space = staff['space']
    line, specks, _ = _line_specks(layers, mark, staff)
    if abs(line - mark['cy']) > LINE_SLIT[0] * space:
        return False
    over = max(((area, x, -row) for area, x, row in specks if area >= LINE_SLIT[1] and row < 0), default=None)
    under = max(((area, x, row) for area, x, row in specks if area >= LINE_SLIT[1] and row >= 0), default=None)
    return bool(over and under and over[1] - under[1] >= LINE_SLIT[2] * space
                and max(over[2], under[2]) >= LINE_OUT * space)


LINE_HALVES = (0.012, 0.35, 0.15)   # a filled head with a stem and a line through it (as LINE_SLIT) is a half note
#   when a speck of paper of at least this many square staff spaces is closed in over the line and one under it, the
#   middle of each out of the rows of the line (LINE_OUT) and at most the second number of staff spaces from it, the two
#   over each other (their middles at most this share of the box apart): the inside of a half note that lies flat, cut
#   in two by the line and a little smaller than a hole (None: off)


def _line_halves(layers: dict, mark: dict, staff: dict) -> bool:
    """A half note on a line whose inside lies flat: the line cuts it into two halves that stand over each other, one
    over the line and one under it, each out of the rows of the line. (The slit of a half note that leans is
    _line_slit(); specks of a worn filled head lie in the rows of the line.)"""
    space = staff['space']
    line, specks, wide = _line_specks(layers, mark, staff)
    if abs(line - mark['cy']) > LINE_SLIT[0] * space:
        return False
    halves = [(area, x, row) for area, x, row in specks
              if area >= LINE_HALVES[0] * space * space and LINE_OUT * space <= abs(row) <= LINE_HALVES[1] * space]
    over = max((half for half in halves if half[2] < 0), default=None)
    under = max((half for half in halves if half[2] > 0), default=None)
    return bool(over and under and abs(over[1] - under[1]) <= LINE_HALVES[2] * wide)


def _ledger_seen(layers: dict, mark: dict, line: float, space: float) -> float | None:
    """The row of the ledger line through a head, as the ink shows it at both sides of the head (see SLIT_LEDGER), or
    None where no line sticks out there."""
    ink = layers['ink']
    reach = int(SLIT_LEDGER[1] * space)
    first, last = max(0, int(line - SLIT_LEDGER[0] * space)), min(ink.shape[0] - 1, int(line + SLIT_LEDGER[0] * space))
    shown = {row: min(int(ink[row, max(0, mark['x0'] - reach):max(0, mark['x0'] - 1)].sum()),
                      int(ink[row, mark['x1'] + 2:mark['x1'] + reach + 1].sum())) for row in range(first, last + 1)}
    most = max(shown.values(), default=0)
    if most < SLIT_LEDGER[2] * reach:
        return None
    return float(np.mean([row for row, count in shown.items() if count >= 0.5 * most]))


def _slit_one(layers: dict, mark: dict, staff: dict, ledger: bool = True) -> str | None:
    """One speck of paper in a filled head: 'slit' when the head is on a line and the speck lies where the slit of a
    half note does (see SLIT_ONE: over the line in the right part of the head, or under the line in the left part),
    'other' when a speck lies elsewhere in the middle of the head (see SLIT_PAGE), or None. With `ledger` False a
    ledger line is taken at its place, as the count of the page takes it."""
    space = staff['space']
    line, specks, wide = _line_specks(layers, mark, staff)
    if ledger and SLIT_LEDGER and specks and not staff['rows'][0] - 0.5 * space <= line <= staff['rows'][4] + 0.5 * space:
        # The place of a ledger line is counted from the staff; the line itself is seen beside the head.
        seen = _ledger_seen(layers, mark, line, space)
        if seen is not None:
            specks = [(area, x, row + line - seen) for area, x, row in specks]
            line = seen
    other = False
    for area, x, row in specks:
        if area < SLIT_ONE[1] * space * space:
            continue
        if abs(line - mark['cy']) <= SLIT_ONE[0] * space and SLIT_ONE[2] * space <= abs(row) <= SLIT_ONE[3] * space \
                and (x >= SLIT_ONE[4] * wide if row < 0 else x <= SLIT_ONE[5] * wide):
            return 'slit'
        if SLIT_PAGE and abs(line + row - mark['cy']) <= SLIT_PAGE[1] * space \
                and SLIT_PAGE[2] * wide <= x <= SLIT_PAGE[3] * wide:
            other = True
    return 'other' if other else None


def _whole_slit(layers: dict, mark: dict, staff: dict) -> bool:
    """A speck of paper in the middle of a full oval on a line, over the line or under it: what a heavy print left
    of the hole of a whole note (see WHOLE_SLIT)."""
    space = staff['space']
    line, specks, wide = _line_specks(layers, mark, staff)
    if abs(line - mark['cy']) > WHOLE_SLIT[2] * space:
        return False
    if not any(area >= WHOLE_SLIT[3] * space * space and WHOLE_SLIT[4] * space <= abs(row) <= WHOLE_SLIT[5] * space
               and WHOLE_SLIT[6] * wide <= x <= WHOLE_SLIT[7] * wide for area, x, row in specks):
        return False
    box = layers['bare'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1]
    return float(box[:, int(0.2 * box.shape[1]):int(0.8 * box.shape[1]) + 1].mean()) >= WHOLE_SLIT[8]


def _mark(mask: np.ndarray, holes: np.ndarray, x: int, y: int, blob: int) -> dict | None:
    """A thick mark from a part of a mask (at x, y on the page)."""
    size = int(mask.sum())
    if size == 0:
        return None
    ys, xs = np.nonzero(mask)
    inside = mask & holes
    return {'x0': int(x + xs.min()), 'x1': int(x + xs.max()), 'y0': int(y + ys.min()), 'y1': int(y + ys.max()),
            'area': size, 'cx': float(x + xs.mean()), 'cy': float(y + ys.mean()), 'hole': float(inside.sum()) / size,
            'hole_cy': float(y + np.nonzero(inside)[0].mean()) if inside.any() else None, 'blob': blob,
            'profile': mask[ys.min():ys.max() + 1].sum(axis=1)}


HALVES_LEAN = 1.2    # the two half holes of a head on a ledger line need not stand over each other where the inside
#   leans: the upper half lies right of the lower one, they share a column, both together are at most this many staff
#   spaces wide, and the line between them is a ledger line, not a line of the staff. One engraver's half notes on a
#   thick ledger line were cut into two heads each; on the lines of the staff the same shape is two heads a third
#   apart as often (0: off)


def _hole_centres(layers: dict, inside: np.ndarray, x: int, y: int) -> list[tuple[float, float]]:
    """The middles (column, row in the mask) of the holes of a hollow mark, one for each head. A head on a staff
    line or a ledger line has two half holes, one over the line and one under it: they are one hole."""
    space = layers['space']
    count, labels, stats, centres = cv2.connectedComponentsWithStats(inside.astype(np.uint8), connectivity=8)
    found = [{'x0': stats[k][0], 'x1': stats[k][0] + stats[k][2] - 1, 'y0': stats[k][1], 'y1': stats[k][1] + stats[k][3] - 1,
              'area': float(stats[k][4]), 'cx': float(centres[k][0]), 'cy': float(centres[k][1])}
             for k in range(1, count) if stats[k][4] >= 0.02 * space * space]
    found.sort(key=lambda hole: hole['cy'])
    staff = layers['staves'][_staff_of(layers, x + inside.shape[1] / 2, y + inside.shape[0] / 2) or 0]
    step = staff['space']
    lines = list(staff['rows']) + [staff['rows'][0] - k * step for k in range(1, 5)] + [staff['rows'][4] + k * step for k in range(1, 5)]
    if LINE_CHORD and len(found) >= 3:
        # Hollow heads a third apart, each on a line: the lines cut their insides into cells, one more than the
        # heads. The first and the last cell are half holes at the rims, so they lie nearer to each other than the
        # holes of as many heads in the spaces would.
        ordered = sorted(lines)
        cells = {}
        for hole in found:
            cells.setdefault(sum(1 for line in ordered if line < y + hole['cy']), []).append(hole)
        # The first and the last cell hold half an inside each, the cells between them two halves.
        ends = (min(cells), max(cells)) if LINE_CHORD_ENDS and len(cells) >= LINE_CHORD_ENDS else ()
        size = {gap: sum(hole['area'] for hole in cell) * (2 if gap in ends else 1) for gap, cell in cells.items()}
        largest = max(size.values())
        gaps = sorted(gap for gap in cells if size[gap] >= 0.25 * largest)
        if len(gaps) >= 3 and gaps[-1] - gaps[0] == len(gaps) - 1 and len(gaps) == len(cells):
            middle = lambda gap, axis: sum(hole[axis] * hole['area'] for hole in cells[gap]) / sum(hole['area'] for hole in cells[gap])
            if middle(gaps[-1], 'cy') - middle(gaps[0], 'cy') <= (len(gaps) - 2 + LINE_CHORD) * step:
                return [((middle(gap, 'cx') + middle(gap + 1, 'cx')) / 2, ordered[gap] - y) for gap in gaps[:-1]]
    merged = []
    for hole in found:
        for other in merged:
            shared = min(hole['x1'], other['x1']) - max(hole['x0'], other['x0']) + 1
            gap = hole['y0'] - other['y1']
            between = any(y + other['y1'] - 2 <= line <= y + hole['y0'] + 2 for line in lines)
            ledger = [line for line in lines[5:] if y + other['y1'] - 2 <= line <= y + hole['y0'] + 2]
            leans = HALVES_LEAN and ledger and shared >= 1 and other['cx'] > hole['cx'] \
                and max(hole['x1'], other['x1']) - min(hole['x0'], other['x0']) + 1 <= HALVES_LEAN * space
            # Two half holes are together as high as the inside of one head. The holes of two heads a third apart
            # have a staff line between them too, but together they are much higher.
            if 0 <= gap <= 0.4 * space and between and hole['y1'] - other['y0'] + 1 <= 1.0 * space \
                    and (shared >= 0.5 * min(hole['x1'] - hole['x0'] + 1, other['x1'] - other['x0'] + 1) or leans):
                total = other['area'] + hole['area']
                other['cx'] = (other['cx'] * other['area'] + hole['cx'] * hole['area']) / total
                other['cy'] = (other['cy'] * other['area'] + hole['cy'] * hole['area']) / total
                if leans and shared < 0.5 * min(hole['x1'] - hole['x0'] + 1, other['x1'] - other['x0'] + 1):
                    # Two halves that lean apart: the head stands on the ledger line between them.
                    other['cy'] = min(ledger, key=lambda line: abs(line - y - other['cy'])) - y
                other.update(x0=min(other['x0'], hole['x0']), x1=max(other['x1'], hole['x1']), y1=hole['y1'], area=total)
                break
        else:
            merged.append(dict(hole))
    # A sliver of paper at the rim of a head is no hole of its own.
    largest = max((hole['area'] for hole in merged), default=0.0)
    kept = [hole for hole in merged if hole['area'] >= 0.25 * largest]
    if JOINT_CELL and len(kept) >= 3 and inside.shape[0] <= JOINT_CELL[3] * step:
        # Two whole notes that touch side by side (see JOINT_CELL): the cell where they touch is no head.
        joints = [hole for hole in kept
                  if any(left['x1'] < hole['x0'] and hole['x1'] < right['x0'] and hole['x0'] - left['x1'] <= JOINT_CELL[1] * step
                         and right['x0'] - hole['x1'] <= JOINT_CELL[1] * step
                         and min(left['area'], right['area']) >= JOINT_CELL[2] * step * step
                         and hole['area'] <= JOINT_CELL[0] * min(left['area'], right['area'])
                         for left in kept for right in kept)]
        kept = [hole for hole in kept if not any(hole is joint for joint in joints)]
    return [(hole['cx'], hole['cy']) for hole in kept]


def head_size(marks: list[dict], space: float) -> tuple[float, float]:
    """The width and the height of a note head on this page, in px: the middle of the marks that have the size of
    one head. A copyist draws every head alike, and a printer does too, so the page shows its own head."""
    alone = [mark for mark in marks if 0.8 * space <= mark['x1'] - mark['x0'] + 1 <= 2.2 * space
             and 0.6 * space <= mark['y1'] - mark['y0'] + 1 <= 1.45 * space]
    if len(alone) < 8:
        return 1.3 * space, 1.0 * space
    return (float(np.median([mark['x1'] - mark['x0'] + 1 for mark in alone])),
            float(np.median([mark['y1'] - mark['y0'] + 1 for mark in alone])))


def _stem_between(layers: dict, x: int, y: int, wide: int, high: int) -> bool:
    """True when an upright stroke stands in the middle third of a mark's box (at x, y) and reaches it."""
    space = layers['space']
    return any(x + wide / 3 <= stroke['x'] <= x + 2 * wide / 3
               and stroke['y0'] <= y + high + 0.3 * space and stroke['y1'] >= y - 0.3 * space
               for stroke in layers['strokes'] if stroke['slim'])


def _line_pair(layers: dict, centres: list[tuple[float, float]], x: int, y: int, own_wide: int, own_high: int,
               wide: float, high: float) -> bool:
    """Whether the three holes of a hollow mark are those of two half notes a third apart on lines (LINE_PAIR): they
    stand one over the other in a zigzag, and a stem goes past the mark."""
    space = layers['space']
    (x0, y0), (x1, y1), (x2, y2) = sorted(centres, key=lambda centre: centre[1])
    if min(y1 - y0, y2 - y1) < LINE_PAIR[5] * high:
        return False
    if (x0 - x1) * (x2 - x1) <= 0:
        return False
    return any(stroke['slim'] and x - 0.3 * space <= stroke['x'] <= x + own_wide + 0.3 * space
               and (stroke['y0'] <= y - LINE_PAIR[6] * space and stroke['y1'] >= y
                    or stroke['y1'] >= y + own_high + LINE_PAIR[6] * space and stroke['y0'] <= y + own_high)
               for stroke in layers['strokes'])


DASH_PAIR = (1.35, 1.95, 0.3, 0.85, 0.3, 0.4, 0.45, 0.25, 1.9)   # a filled head on the first ledger line and a filled head on the
#                     first line of the staff, a third apart, as one piece of ink: a print that sets its ledger line near
#                     the staff (a music typewriter) lets the two heads run into each other, and the piece is too low
#                     to be cut as two heads of a chord. The piece is this many heads high (least, most); it ends half
#                     a head past the staff's line (within the fifth number of heads); the middle of its other head
#                     lies from the third to the fourth number of staff spaces beside that line; and the ledger line
#                     shows there: thin level ink that leaves the head at a side, this many staff spaces long or more,
#                     at most this thick, within this many staff spaces of the head's middle row. The piece is at most
#                     the last number of heads wide with its line (None: off)
DASH_STEM = False    # off: the two heads of such a piece hang on one stem, and the head that shows none would take
#                     the other's. It changes no note on any page: the stem of the pair runs along both heads, and
#                     each of them was followed into it already
DASH_OWN = True      # the two heads of such a piece are the one mark that they were, where the page is measured
#                     (the usual inside of a hollow head: counted twice, a hand's pair moved the measure and a sign
#                     at a clef was read as a half note), for the rule for a whole note beside a stemmed head of
#                     the other voice (WHOLE_BESIDE: the lower head of a pair is wider, because it holds its ledger
#                     line, and it gave its stem away) and for the rule for a whole note that touches a chord
#                     (CHORD_WHOLE: the ledger line cuts the inside of such a head into slivers)
DASH_SHUT = 0.15     # such a piece is two filled heads and the ledger line between them: it closes no paper of a
#                     head's inside size. Two half notes a third apart, with the staff line between them for the
#                     ledger line, are the same shape, and their insides tell. Measured in staff spaces squared on
#                     the piece's whole box, as the paper that the ink shuts in (no piece that reaches the box's
#                     edge): of the 37 pieces that the other limits take on LitChoir's pages, the one chord of half
#                     notes holds 0.28 and every true pair 0.09 at most. A page whose own hollow heads have insides
#                     under this measure (a small print: 0.14) is no safer for it. 0: off


def _dash_wing(layers: dict, x0: int, x1: int, top: int, bottom: int) -> float | None:
    """The row of the thin level ink that leaves a head at a side, in the rows from top to bottom: the end of a ledger
    line that goes through the head (see DASH_PAIR). The longer side counts. None without such ink."""
    free, space = layers['free'], layers['space']
    reach = int(round(0.9 * space))
    top, bottom = max(0, top), min(free.shape[0] - 1, bottom)
    first, last = max(0, x0 - reach), min(free.shape[1], x1 + reach + 1)
    window = free[top:bottom + 1, first:last] > 0
    own = window[:, x0 - first:x1 - first + 1].sum(axis=0)
    if own.size == 0 or own.max() == 0:
        return None
    body = np.nonzero(own >= 0.6 * own.max())[0]
    left, right = x0 - first + int(body[0]), x0 - first + int(body[-1])
    best = None
    for side in (window[:, :left][:, ::-1], window[:, right + 1:]):
        # How far the ink of each row goes on past the body, without a gap.
        gaps = np.argmin(side, axis=1)
        far = np.where(side.all(axis=1), side.shape[1], gaps) if side.shape[1] else np.zeros(side.shape[0], int)
        rows = np.nonzero(far >= DASH_PAIR[5] * space)[0]
        if len(rows) == 0 or rows[-1] - rows[0] + 1 != len(rows) or len(rows) > DASH_PAIR[6] * space:
            continue
        if best is None or far[rows].max() > best[0]:
            best = (int(far[rows].max()), top + float(rows.mean()))
    return best[1] if best else None


def _dash_pair(layers: dict, mask: np.ndarray, holes: np.ndarray, x: int, y: int, wide: float, high: float, blob: int) -> list:
    """The two heads of a piece of ink that is a head on the first ledger line and a head on the first line of the
    staff (DASH_PAIR), each with its place ('line_place'); an empty list when the piece is no such pair."""
    own_high, own_wide = mask.shape
    if not (DASH_PAIR[0] * high <= own_high <= DASH_PAIR[1] * high and own_wide <= DASH_PAIR[8] * wide):
        return []
    index = _staff_of(layers, x + own_wide / 2, y + own_high / 2)
    if index is None:
        return []
    staff = layers['staves'][index]
    half = high / 2
    for above in (True, False):
        edge = staff['rows'][0] if above else staff['rows'][-1]
        inner, outer = (y + own_high - 1, y) if above else (y, y + own_high - 1)
        middle = outer + half if above else outer - half          # the middle row of the head on the ledger line
        gap = (edge - middle) if above else (middle - edge)
        if abs(inner - (edge + half if above else edge - half)) > DASH_PAIR[4] * high \
                or not DASH_PAIR[2] * staff['space'] <= gap <= DASH_PAIR[3] * staff['space']:
            continue
        rows = (y - int(0.3 * staff['space']), int(middle + half)) if above else (int(middle - half), y + own_high - 1 + int(0.3 * staff['space']))
        row = _dash_wing(layers, x, x + own_wide - 1, rows[0], rows[1])
        if row is None or abs(row - middle) > DASH_PAIR[7] * staff['space']:
            continue
        cut = int(round((middle + edge) / 2)) - y
        if not 0 < cut < own_high:
            continue
        # Paper that the two heads close in between them reaches the cut, and is no inside of either head.
        count, labels = cv2.connectedComponents((mask & holes).astype(np.uint8), connectivity=8)
        between = [label for label in range(1, count) if (labels[max(0, cut - 2):cut + 2] == label).any()]
        inside = holes & ~np.isin(labels, between) if between else holes
        pair = [_mark(mask[:cut], inside[:cut], x, y, blob), _mark(mask[cut:], inside[cut:], x, y + cut, blob)]
        if not all(pair):
            continue
        if DASH_SHUT:
            # Two half notes a third apart are such a piece too, and their insides tell (see DASH_SHUT).
            paper = (layers['ink'][y:y + own_high, x:x + own_wide] == 0).astype(np.uint8)
            number, labels, sizes, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
            edge = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
            shut = max([int(sizes[label][4]) for label in range(1, number) if label not in edge], default=0)
            if shut >= DASH_SHUT * staff['space'] * staff['space']:
                continue
        places = (6.0, 4.0) if above else (-4.0, -6.0)
        for part, place in zip(pair, places):
            part['line_place'] = place
            part['pair_box'] = (x, y, x + own_wide - 1, y + own_high - 1)
            if abs(place) == 6.0:
                part['dash'] = row
        return pair
    return []


DASH_HOLLOW = (1.8, 0.45, 0.85, 1.3, 0.3, 1.9, 2.4, 0.05)   # a half note on a thick ledger dash and a half note on the
#                     first line of the staff, a third apart, as one piece of ink (a rule for one case, on the print
#                     of DASH_PAIR). The dash is thick ink and longer than its head, so the rows of the piece are
#                     widest there, and the valley of the rows lies in the inside of the head on the staff's line,
#                     which the line cuts into slivers that are no holes: the piece was cut through that head, the
#                     head on the dash was too wide for a head with its dash, and the pieces of the other were read
#                     a step low. Such a piece is cut between its dash and the staff's line. The dash: rows whose
#                     ink goes on for the first number of heads or more without a gap, one run of rows, at most the
#                     second number of staff spaces thick, from the third to the fourth number of staff spaces
#                     beside the staff's first line. The piece ends half a head past the dash and half a head past
#                     the staff's line (within the fifth number of heads), so it is from the sixth to the seventh
#                     number of heads high; each half shuts in paper (the last number of staff spaces squared or
#                     more); and the cut by the valley of its rows goes through paper that the half at the staff's
#                     line shuts in. Of the 111 pieces of LitChoir's scan pages with such a dash beside the staff,
#                     7 have the two heads' shape (two pairs of whole notes, three pairs that are cut rightly at
#                     their valley, a sharp before a pair) and one is cut through a head (None: off)


def _dash_hollow(layers: dict, mask: np.ndarray, holes: np.ndarray, x: int, y: int, wide: float, high: float, blob: int) -> list:
    """The two hollow heads of a piece of ink that is a head on a thick ledger dash and a head on the first line of
    the staff, where the valley of its rows lies in a head (DASH_HOLLOW): the head on the dash without the ends of
    its dash, and the other, each with its place ('line_place'); an empty list when the piece is no such pair."""
    own_high, own_wide = mask.shape
    bar, thick, near, far, ends, least, most, paper_least = DASH_HOLLOW
    if not (least * high <= own_high <= most * high and own_wide >= bar * wide):
        return []
    index = _staff_of(layers, x + own_wide / 2, y + own_high / 2)
    if index is None:
        return []
    staff = layers['staves'][index]
    # The longest run of ink of each row.
    padded = np.zeros((own_high, own_wide + 2), np.int8)
    padded[:, 1:-1] = mask
    runs = np.zeros(own_high, int)
    for row in range(own_high):
        edges = np.flatnonzero(np.diff(padded[row]))
        runs[row] = int((edges[1::2] - edges[::2]).max()) if len(edges) else 0
    rows = np.nonzero(runs >= bar * wide)[0]
    if len(rows) == 0 or rows[-1] - rows[0] + 1 != len(rows) or len(rows) > thick * staff['space']:
        return []
    dash = y + float(rows.mean())
    half = high / 2
    for above in (True, False):
        edge = staff['rows'][0] if above else staff['rows'][-1]
        gap = (edge - dash) if above else (dash - edge)
        if not near * staff['space'] <= gap <= far * staff['space']:
            continue
        outer, inner = (y, y + own_high - 1) if above else (y + own_high - 1, y)
        if abs(outer - (dash - half if above else dash + half)) > ends * high \
                or abs(inner - (edge + half if above else edge - half)) > ends * high:
            continue
        cut = int(round((dash + edge) / 2)) - y
        if not 0 < cut < own_high:
            continue
        paper = (layers['ink'][y:y + own_high, x:x + own_wide] == 0).astype(np.uint8)
        number, labels, _, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
        rim = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
        shut = np.isin(labels, [label for label in range(1, number) if label not in rim])
        if min(shut[:cut].sum(), shut[cut:].sum()) < paper_least * staff['space'] * staff['space']:
            continue
        first, last = (cut, own_high) if above else (0, cut)          # the rows of the head on the staff's line
        slivers = shut & ~holes
        if not any(first <= row < last and slivers[max(0, row - 1):row + 2].any()
                   for row, _ in _cut_rows(mask, holes, layers['space'])[1:]):
            continue
        on_dash, on_line = np.zeros_like(mask), np.zeros_like(mask)
        on_line[first:last] = mask[first:last]
        if above:
            on_dash[:cut] = mask[:cut]
        else:
            on_dash[cut:] = mask[cut:]
        # The head on the dash without the ends of its dash: the columns that hold most of its ink.
        columns = on_dash.sum(axis=0)
        body = np.nonzero(columns >= 0.6 * columns.max())[0]
        on_dash[:, :body[0]] = False
        on_dash[:, body[-1] + 1:] = False
        pair = [_mark(on_dash, holes, x, y, blob), _mark(on_line, holes, x, y, blob)]
        if not all(pair):
            continue
        pair[0]['line_place'], pair[1]['line_place'] = (6.0, 4.0) if above else (-6.0, -4.0)
        pair[0]['dash'] = dash
        for part in pair:
            part['pair_box'] = (x, y, x + own_wide - 1, y + own_high - 1)
        return pair if above else pair[::-1]
    return []


def _pair_at_stem(layers: dict, mask: np.ndarray, holes: np.ndarray, x: int, y: int, wide: float, high: float,
                  blob: int) -> list:
    """The two heads of a piece of ink that a stem cuts into a higher part at the left and a lower part at the right
    (PAIR_STEM), the upper head first; an empty list when the piece is no such pair. Two voices that sing a second
    stand with their stems back to back, the upper head at the left of the stems and the lower one at the right,
    and the print lets the two heads run together. The lower head may begin under the upper one, at the left of the
    stems: so the two parts are less apart than the two heads, and the height of the piece says that they are a
    second apart and not a third. Two voices on one note stand side by side at one height."""
    space = layers['space']
    own_high, own_wide = mask.shape
    least_wide, most_wide, least_high, most_over, least, apart, most_high, clear = PAIR_STEM
    if not (least_wide * wide <= own_wide <= most_wide * wide and least_high * high <= own_high <= most_high * high):
        return []
    stems = [stroke['x'] for stroke in layers['strokes'] if stroke['slim'] and x + own_wide / 3 <= stroke['x'] <= x + 2 * own_wide / 3
             and stroke['y0'] <= y + own_high + 0.3 * space and stroke['y1'] >= y - 0.3 * space]
    if not stems:
        return []
    column = int(round(min(stems, key=lambda stem: abs(stem - (x + own_wide / 2))) - x))
    first, last = column, column          # the upper head ends at the column 'first', the lower head begins at 'last'
    left, right = mask[:, :column], mask[:, column:]
    cut = int(round(wide))
    if PAIR_OVER and min(column, own_wide - column) < HEAD_WIDE[0] * space and cut < own_wide:
        # The two heads overlap, and the stem stands in one of them: see PAIR_OVER.
        first, last = cut, own_wide - cut
        if min(mask[:, :first].sum(), mask[:, last:].sum()) < least * wide * high:
            return []
        left, right = mask[:, :last], mask[:, first:]
        if not left.any() or not right.any():
            return []
    elif min(left.sum(), right.sum()) < least * wide * high:
        return []
    lean = (np.nonzero(right)[0].mean() - np.nonzero(left)[0].mean()) / space
    step = int(round(0.5 * space))
    if lean < (apart if own_high <= high + most_over * space else clear) or step >= own_high:
        return []
    upper, lower = np.zeros_like(mask), np.zeros_like(mask)
    upper[:own_high - step, :first] = mask[:own_high - step, :first]
    lower[step:, last:] = mask[step:, last:]
    pair = [_mark(upper, holes, x, y, blob), _mark(lower, holes, x, y, blob)]
    if first != last:
        for part in pair:
            if part:
                part['across'] = True      # the head lies across the stem of the pair: see _across()
    return pair


def _without_arm(mask: np.ndarray, holes: np.ndarray, space: float, usual: float, tall: float) -> np.ndarray:
    """A mark without the bold bows that touch it (see ARM). A bow is slim along its whole way; a head with its hole
    is as high as a head in all of its columns but the outermost."""
    if not ARM or not usual or not tall or mask.shape[1] <= ARM[2] * usual or not (mask & holes).any():
        return mask
    size = max(3, int(round(ARM[0] * tall)) | 1)        # an odd size: the opening is exact
    # A round kernel: a bow that rises is as high as a head in its columns, but no disc of that size lies in it.
    # The mask ends at the edge of the mark, and OpenCV takes what lies past the edge of a picture for ink: paper is
    # set around the mask first.
    solid = cv2.morphologyEx(np.pad(mask.astype(np.uint8), size), cv2.MORPH_OPEN,
                             cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))[size:-size, size:-size] > 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats((mask & ~solid).astype(np.uint8), connectivity=8)
    def bends(index: int) -> bool:
        # The bow of a tie bends and ends at the height where it began. A beam is straight, and it leans.
        x, wide = stats[index][0], stats[index][2]
        rows = []
        for share in (0.0, 0.5, 1.0):
            column = x + int(share * (wide - 1))
            inked = np.nonzero(labels[:, max(x, column - 2):column + 3] == index)[0]
            if not len(inked):
                return False
            rows.append(float(inked.mean()))
        return abs(rows[1] - (rows[0] + rows[2]) / 2) >= ARM[5] * space and abs(rows[0] - rows[2]) <= ARM[6] * space

    bows = [index for index in range(1, count) if stats[index][2] >= ARM[1] * space
            and stats[index][3] <= ARM[3] * stats[index][2] and stats[index][4] <= ARM[4] * space * stats[index][2]
            and bends(index)]
    if not bows:
        return mask
    # What is left of the mark are its pieces that hold such a disc: a crumb of the bow beside a head is no head.
    left = mask & ~np.isin(labels, bows)
    count, labels, _, _ = cv2.connectedComponentsWithStats(left.astype(np.uint8), connectivity=8)
    kept = np.unique(labels[solid & left])
    left &= np.isin(labels, kept[kept > 0])
    return left if (left & holes).any() else mask


CELL_OUT = (0.6, 0.95, 2.0, 0.75, 0.4, 0.55)   # a cell along a staff line in a thick mark that also holds a filled head
#   (see FLAT_CELL for the first three numbers) is paper, not the inside of a head: a head and the stem of the note
#   before it, or a head and its sign, close such a cell with the staff lines, and the mark was read as one hollow
#   head. The mark holds a filled head where an oval of the fourth share of a head goes through its ink. The cell
#   stands between a thin stroke and a head: in its middle rows the ink at one side is at most the fifth number of
#   staff spaces wide (a stem, the stroke of a sign) and at the other side the sixth number or more (the head). The
#   loop of a flag has thin ink at both sides, and older rules read the flag from it; a cell under a beam has its
#   heads below it. (None: off)


CELL_BETWEEN = (0.65, 2.7)   # and a cell that fills the room between two staff lines, level along both for the first
#   share of its columns each, is such a cell too where the thin stroke stands at its left and goes on upright for
#   the second number of staff spaces or more: a bar line or the stroke of a sharp close before a head closes one
#   with the lines and the head. A flag closes such a cell too, and older rules read the flag from it (the first
#   form took it, and two eighth notes went): a flag hangs at the right of its stem, so the loop that it closes
#   with its own head has the thin stroke at the right, and it bends, where a bar line and the stroke of a sign are
#   straight (the flags of LitChoir's pages go on upright for 1.3 to 2.3 staff spaces, the stroke of the sharp for
#   3.1 and the bar lines for 3.8 or more). The arc of a pencil ring around a head passes where it stands upright
#   beside the head (3.2 on one clean page). (None: off)


CELL_UNDER = (0.5, 0.6)   # and a cell along a staff line with thin ink at both sides is such a cell too where its other
#   edge is a head: across the cell from the line, in the middle 0.6 of its columns, the ink holds a circle at least half
#   as high as the page's heads. Two eighths a second apart whose heads touch close a cell with their two stems and the
#   line over them, and the piece was one hollow mark that no step read (memorial-troparia: 3 notes). The loop of a flag
#   has thin ink at both sides too, and its other edge is the flag's slim stroke. Such a cell is taken out only where
#   the piece's own reading does not cut it into two marks or more (thick_marks): a print whose touching heads a second
#   apart are cut at the room between them was one head without the cell, and 3 notes were lost (wedding-isaiah). 137
#   cells on 82 pages of LitChoir pass, most of them in the clefs at the start of a staff, where no note is read, and the
#   notes change at the one place; one cell on the fresh set, where no note changes. A rule for one case. (None: off)


def _upright(layers: dict, column: int, run: int, row: int) -> float:
    """How far the thin stroke at the left of a cell goes on upright, in staff spaces: the rows above and below `row`,
    one after the other, that hold ink in the stroke's columns (`run` columns that end at `column`, and one more at
    each side)."""
    ink = layers['ink']
    band = ink[:, max(0, column - max(1, run)):column + 2].any(axis=1)
    if not band[row]:
        return 0.0
    first = last = row
    while first > 0 and band[first - 1]:
        first -= 1
    while last + 1 < len(band) and band[last + 1]:
        last += 1
    return (last - first + 1) / layers['space']


def _cells_out(layers: dict, whole: np.ndarray, holes: np.ndarray, x: int, y: int, wide: float, high: float) -> tuple:
    """The closed paper of a thick piece that is a cell along a staff line (CELL_OUT), as a mask of the piece's box,
    and whether every such cell is one under a head with thin ink at both sides (CELL_UNDER); None where there is
    none or where the piece holds no filled head. A piece with both kinds gives its CELL_OUT cells only."""
    space = layers['space']
    inside = (whole & holes).astype(np.uint8)
    if not inside.any():
        return None, False
    rows = np.array(sorted(row for staff in layers['staves'] for row in staff['rows']), float)
    thick = max(staff['thick'] for staff in layers['staves'])
    half, slack = thick / 2, max(CELL_OUT[2], thick / 2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(inside, connectivity=4)
    cells, under = np.zeros(whole.shape, bool), np.zeros(whole.shape, bool)
    for index in range(1, count):
        left, top, width, height, _ = (int(value) for value in stats[index])
        if height < CELL_OUT[0] * space:
            continue
        part = labels[top:top + height, left:left + width] == index
        first, last = part.argmax(axis=0), height - 1 - part[::-1].argmax(axis=0)
        level = float((first <= 1).mean()), float((last >= height - 2).mean())
        lines = (float(np.abs(rows - (y + top - 0.5 - half)).min()), float(np.abs(rows - (y + top + height - 0.5 + half)).min()))
        along = (level[0] >= CELL_OUT[1] and lines[0] <= slack) or (level[1] >= CELL_OUT[1] and lines[1] <= slack)
        between = bool(CELL_BETWEEN) and max(lines) <= slack and min(level) >= CELL_BETWEEN[0]
        if not (along or between):
            continue
        # The ink at the two sides of the cell, in its middle rows: a thin stroke at one side, a head at the other.
        sides = []
        for column, step in ((x + left - 1, -1), (x + left + width, 1)):
            runs = []
            for row in range(y + top + height // 4, y + top + max(height // 4 + 1, 3 * height // 4)):
                at, run = column, 0
                while 0 <= at < layers['ink'].shape[1] and layers['ink'][row, at]:
                    at, run = at + step, run + 1
                runs.append(run)
            sides.append(float(np.median(runs)) / space)
        if min(sides) <= CELL_OUT[4] and max(sides) >= CELL_OUT[5] and (
                along or (sides[0] < sides[1] and _upright(layers, x + left - 1, int(round(sides[0] * space)),
                                                           y + top + height // 2) >= CELL_BETWEEN[1])):
            cells |= labels == index
        elif CELL_UNDER and along and max(sides) <= CELL_OUT[4]:
            # Thin ink at both sides: the ink across the cell from the line, in its middle columns, is a head.
            at_top = level[0] >= CELL_OUT[1] and lines[0] <= slack
            margin = int(width * (1 - CELL_UNDER[1]) / 2)
            if at_top:
                band = slice(y + top + height // 2, y + top + height + int(round(high)))
            else:
                band = slice(max(0, y + top - int(round(high))), y + top + height // 2 + 1)
            region = np.ascontiguousarray(layers['ink'][band, x + left + margin:x + left + width - margin] > 0).astype(np.uint8)
            fat = 2 * float(cv2.distanceTransform(np.pad(region, 1), cv2.DIST_L2, 5).max()) if region.size else 0.0
            if fat >= CELL_UNDER[0] * high:
                under |= labels == index
    if not (cells | under).any():
        return None, False
    ink = (whole & ~holes).astype(np.uint8)
    oval = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(CELL_OUT[3] * wide) | 1, int(CELL_OUT[3] * high) | 1))
    if not cv2.morphologyEx(np.pad(ink, max(oval.shape)), cv2.MORPH_OPEN, oval).any():
        return None, False
    return (cells, False) if cells.any() else (under, True)


def thick_marks(layers: dict) -> list[dict]:
    """The thick marks of the page, cut where two heads touch. Each: its box (x0, y0, x1, y1), area, the middle
    (cx, cy), 'hole' (the share of its area that was the inside of a hollow shape), 'hole_cy' and 'blob' (the
    number of the piece of ink that it was cut from).

    Heads that touch are one piece of ink. Heads a third apart stand one over the other: the piece is as high as
    two heads (or three), and it is cut evenly. Heads a second apart stand at the two sides of the stem, the lower
    one at the left: the piece is as wide as two heads and as high as one and a half, and it is cut into its lower
    left and its upper right part."""
    space = layers['space']
    count, labels, stats, _ = cv2.connectedComponentsWithStats(layers['thick'], connectivity=8)
    pieces = []
    for index in range(1, count):
        x, y, wide, high, area = stats[index]
        if area < SMALL * space * space:
            continue
        whole = labels[y:y + high, x:x + wide] == index
        holes = layers['holes'][y:y + high, x:x + wide] > 0
        for first, last in _cut_rows(whole, holes, space):
            mark = _mark(whole[first:last + 1], holes[first:last + 1], x, y + first, index)
            if mark and mark['area'] >= SMALL * space * space:
                pieces.append((mark, whole[first:last + 1], holes[first:last + 1], x, y + first))
    own = [piece[0] for piece in pieces]
    if HEAD_NEAR:
        # The words under the staves have thick marks too: the letters of a typewriter are small and round. Only the
        # marks in and near the staves show the size of the page's heads.
        own = [mark for mark in own if any(staff['rows'][0] - HEAD_NEAR * space <= mark['cy'] <= staff['rows'][4] + HEAD_NEAR * space
                                           and staff['x0'] <= mark['cx'] <= staff['x1'] for staff in layers['staves'])]
    wide, high = head_size(own, space)
    layers['head'] = (wide, high)
    later = {}   # the pieces of a blob without its cells under a head (CELL_UNDER), read where the blob is not cut
    if CELL_OUT:
        # A cell along a staff line beside a filled head is taken out of its piece, and the piece is made anew: the
        # brush goes through what is left, as it went through the marks of the page.
        from .layers import BRUSH
        brush = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(max(5, round(BRUSH * space))) | 1,) * 2)
        again, extra = [], count
        for index in sorted({piece[0]['blob'] for piece in pieces if piece[0]['hole'] >= HOLLOW}):
            x, y, own_wide, own_high, _ = (int(value) for value in stats[index])
            whole = labels[y:y + own_high, x:x + own_wide] == index
            holes = layers['holes'][y:y + own_high, x:x + own_wide] > 0
            cells, under = _cells_out(layers, whole, holes, x, y, wide, high)
            if cells is None:
                continue
            pad = brush.shape[0]
            left = cv2.morphologyEx(np.pad((whole & ~cells).astype(np.uint8), pad), cv2.MORPH_OPEN, brush)[pad:-pad, pad:-pad]
            number, parts, sizes, _ = cv2.connectedComponentsWithStats(left, connectivity=8)
            made = []
            for label in range(1, number):
                if sizes[label, cv2.CC_STAT_AREA] < SMALL * space * space:
                    continue
                left_x, top, part_wide, part_high = (int(value) for value in sizes[label, :4])
                part = parts[top:top + part_high, left_x:left_x + part_wide] == label
                inside = (holes & ~cells)[top:top + part_high, left_x:left_x + part_wide]
                blob = index if not made else (extra := extra + 1)
                for first, last in _cut_rows(part, inside, space):
                    mark = _mark(part[first:last + 1], inside[first:last + 1], x + left_x, y + top + first, blob)
                    if mark and mark['area'] >= SMALL * space * space:
                        made.append((mark, part[first:last + 1], inside[first:last + 1], x + left_x, y + top + first))
            if made and not under:
                again.append((index, made))
            elif made and sum(1 for piece in pieces if piece[0]['blob'] == index) == 1:
                later[index] = made
        for index, made in again:
            pieces = [piece for piece in pieces if piece[0]['blob'] != index] + made
    marks = []
    if DASH_HOLLOW:
        # A pair of hollow heads at a thick ledger dash whose rows were cut through a head is cut anew, as a whole.
        for index in sorted({piece[0]['blob'] for piece in pieces}):
            if index >= count or sum(1 for piece in pieces if piece[0]['blob'] == index) < 2:
                continue
            x, y, own_wide, own_high, _ = (int(value) for value in stats[index])
            pair = _dash_hollow(layers, labels[y:y + own_high, x:x + own_wide] == index,
                                layers['holes'][y:y + own_high, x:x + own_wide] > 0, x, y, wide, high, index)
            if pair:
                pieces = [piece for piece in pieces if piece[0]['blob'] != index]
                marks += pair
    for mark, mask, holes, x, y in pieces:
        if STUB:
            part = _without_stub(mask, space, high)
            if part is not mask:
                mask, mark = part, _mark(part, holes, x, y, mark['blob']) or mark
        if ARM:
            part = _without_arm(mask, holes, space, wide, high)
            if part is not mask:
                mask, mark = part, _mark(part, holes, x, y, mark['blob']) or mark
        own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
        rows, columns = np.nonzero(mask)
        mask = mask[rows.min():rows.max() + 1, columns.min():columns.max() + 1]
        holes = holes[rows.min():rows.max() + 1, columns.min():columns.max() + 1]
        x, y = x + int(columns.min()), y + int(rows.min())
        parts = []
        by_holes = False
        if mark['hole'] >= HOLLOW and (own_high >= 1.5 * high or own_wide >= 1.6 * wide):
            # Hollow heads that touch: each has its own hole, and each part of the mark goes to the nearest hole.
            centres = _hole_centres(layers, mask & holes, x, y)
            pair = False
            if LINE_PAIR and len(centres) == 3 and LINE_PAIR[0] * wide <= own_wide <= LINE_PAIR[1] * wide \
                    and LINE_PAIR[2] * high <= own_high <= LINE_PAIR[3] * high and (mask & holes).sum() >= LINE_PAIR[4] * wide * high \
                    and _line_pair(layers, centres, x, y, own_wide, own_high, wide, high):
                # Two heads a third apart, each on a line, in one column: the mark is too low for three heads, and
                # heads a second apart stand side by side. The lines cut the insides in two, and the half at the
                # upper or the lower rim can be too slim to be a hole, so the middles of the holes do not say where
                # the heads stand. The mark does: its middle lies between the two heads.
                pair = True
                step = layers['staves'][_staff_of(layers, x + own_wide / 2, y + own_high / 2) or 0]['space'] / 2
                middle = sum(cx for cx, _ in centres) / 3
                centres = [(middle, (own_high - 1) / 2 - step), (middle, (own_high - 1) / 2 + step)]
            if len(centres) >= 2:
                by_holes = True
                rows, columns = np.nonzero(mask)
                nearest = np.argmin([(rows - cy) ** 2 + (columns - cx) ** 2 for cx, cy in centres], axis=0)
                for number in range(len(centres)):
                    part = np.zeros_like(mask)
                    part[rows[nearest == number], columns[nearest == number]] = True
                    parts.append(_mark(part, holes, x, y, mark['blob']))
                    if pair and parts[-1]:
                        parts[-1]['hole_cy'] = float(y + centres[number][1])
            elif len(centres) == 1:
                # A half note and a quarter note of two voices that touch: the hollow head lies around the hole, and
                # what is left over it, under it or beside it is the filled head.
                cx, cy = centres[0]
                cut = None
                line = int(round(layers["staves"][0]["thick"]))
                if ROOM_SOLID and _loop_room(mask & holes, line, wide, high) and _flag_room(mask, mask & holes, line, wide, high):
                    pass      # a room higher than a head's hole is the loop of a flag: see SOLID_LOOP below
                elif own_high >= 1.6 * high and own_wide < 1.6 * wide:
                    over, under = cy - 0.55 * high, own_high - (cy + 0.55 * high)
                    row = int(round(cy - 0.55 * high)) if over >= 0.6 * high else int(round(cy + 0.55 * high)) if under >= 0.6 * high else None
                    if row is not None:
                        cut = (mask[:row], holes[:row], x, y), (mask[row:], holes[row:], x, y + row)
                elif own_wide >= 1.6 * wide and own_high < 1.6 * high:
                    left, right = cx - 0.55 * wide, own_wide - (cx + 0.55 * wide)
                    column = int(round(cx - 0.55 * wide)) if left >= 0.6 * wide else int(round(cx + 0.55 * wide)) if right >= 0.6 * wide else None
                    if column is not None:
                        cut = (mask[:, :column], holes[:, :column], x, y), (mask[:, column:], holes[:, column:], x + column, y)
                diag_ways = {name: _way(layers, mark, up, right) for name, up, right in
                             (('up_right', True, True), ('up_left', True, False), ('down_right', False, True), ('down_left', False, False))} \
                    if DIAG_PAIR and cut is None else {}
                if cut is None and DIAG_PAIR and own_wide >= DIAG_PAIR[0] * wide and own_high >= DIAG_PAIR[1] * high \
                        and own_wide <= DIAG_PAIR[2] * wide and own_high <= DIAG_PAIR[2] * high \
                        and any(is_stem(diag_ways[name], space) for name in ('up_right', 'up_left')) \
                        and any(is_stem(diag_ways[name], space) for name in ('down_right', 'down_left')):
                    # A half note and a quarter note of two voices a second apart stand side by side and a step apart:
                    # the pair is wider and higher than one head. The hollow head is a head's box around the hole, and
                    # the rest is the filled head, beside it and a step over or under it.
                    box = np.zeros_like(mask)
                    box[max(0, int(round(cy - DIAG_PAIR[3] * high))):int(round(cy + DIAG_PAIR[3] * high)) + 1,
                        max(0, int(round(cx - DIAG_PAIR[3] * wide))):int(round(cx + DIAG_PAIR[3] * wide)) + 1] = True
                    rest = mask & ~box
                    if rest.any():
                        rows, columns = np.nonzero(rest)
                        own = np.pad(rest[rows.min():rows.max() + 1, columns.min():columns.max() + 1], 1).astype(np.uint8)
                        if rest.sum() >= DIAG_PAIR[4] * wide * high and cx - columns.mean() >= DIAG_PAIR[5] * wide \
                                and DIAG_PAIR[6] * space <= cy - rows.mean() <= DIAG_PAIR[8] * space \
                                and 2 * float(cv2.distanceTransform(own, cv2.DIST_L2, 5).max()) >= DIAG_PAIR[7] * high:
                            cut = (mask & box, holes & box, x, y), (rest, holes & ~box, x, y)
                            if DIAG_SEEN is not None:
                                DIAG_SEEN.append({'box': [x, y, x + own_wide - 1, y + own_high - 1], 'hole': [x + cx, y + cy],
                                                  'rest': [x + float(columns.mean()), y + float(rows.mean())], 'space': space})
                if cut:
                    parts = [_mark(part, inside, px, py, mark['blob']) for part, inside, px, py in cut]
        elif PAIR_STEM and mark['hole'] < HOLLOW and (pair := _pair_at_stem(layers, mask, holes, x, y, wide, high, mark['blob'])):
            parts = pair
        elif DASH_PAIR and mark['hole'] < HOLLOW and (pair := _dash_pair(layers, mask, holes, x, y, wide, high, mark['blob'])):
            parts = pair
        elif mark['hole'] < HOLLOW and own_wide <= 1.5 * wide and 1.6 * high <= own_high <= 4.4 * high:
            number = int(round(own_high / high))
            step = own_high / number
            for k in range(number):
                first, last = int(round(k * step)), int(round((k + 1) * step))
                parts.append(_mark(mask[first:last], holes[first:last], x, y + first, mark['blob']))
        elif mark['hole'] < HOLLOW and 1.55 * wide <= own_wide <= 2.3 * wide and 1.25 * high <= own_high <= 1.9 * high \
                and _stem_between(layers, x, y, own_wide, own_high):
            # Two heads a second apart, side by side. On one stem the lower head is at the left. Heads of two voices
            # stand the other way round, with their stems back to back between them. Either way a stem stands
            # between the two heads: one long slanted stroke of a hand has its stem at its end.
            middle_x, middle_y = own_wide // 2, own_high // 2
            rising = mask[middle_y:, :middle_x].sum() + mask[:middle_y, middle_x:].sum()      # lower left and upper right
            falling = mask[:middle_y, :middle_x].sum() + mask[middle_y:, middle_x:].sum()     # upper left and lower right
            cut, tall = int(round(wide)), int(round(high))
            left, right = np.zeros_like(mask), np.zeros_like(mask)
            if falling <= 0.35 * rising:
                left[own_high - tall:, :cut] = mask[own_high - tall:, :cut]
                right[:tall, own_wide - cut:] = mask[:tall, own_wide - cut:]
                parts = [_mark(right, holes, x, y, mark['blob']), _mark(left, holes, x, y, mark['blob'])]
            elif rising <= 0.35 * falling:
                left[:tall, :cut] = mask[:tall, :cut]
                right[own_high - tall:, own_wide - cut:] = mask[own_high - tall:, own_wide - cut:]
                parts = [_mark(left, holes, x, y, mark['blob']), _mark(right, holes, x, y, mark['blob'])]
        parts = [part for part in parts if part and part['area'] >= SMALL * space * space]
        if (len(parts) < 2 or (SOLID_ROOMS and by_holes)) and SOLID_LOOP and mark['hole'] >= HOLLOW:
            # A filled head with paper closed in beside it: the flag of a printed eighth note comes back to its head,
            # and the head, the stem, the flag and a staff line close in a small room. The ink over that room (or
            # under it) is as high as a whole head, and no rim of a hollow head is: the mark is that filled head.
            inside = np.nonzero(_room_alone(mask & holes, wide, high).any(axis=1))[0]
            over, under = int(inside[0]), own_high - 1 - int(inside[-1])
            named = False
            span = None
            # The loop of a flag is higher than the hole of a head, and the flag's end may hang under it as a tail.
            line = int(round(layers["staves"][0]["thick"]))
            tail = ROOM_SOLID and not by_holes and _loop_room(mask & holes, line, wide, high) \
                and _flag_room(mask, mask & holes, line, wide, high) and max(over, under) >= 1.5 * min(over, under)
            near = min(over, under)
            if LOOP_FOOT and near > 0.4 * high and LOOP_FOOT[2] * high >= max(over, under) >= SOLID_LOOP * high and not tail:
                # An eighth whose flag comes back to its head: the foot past the loop is the flag's stroke and the
                # stem, and no rim (see LOOP_FOOT).
                foot = mask[:int(inside[0])] if over < under else mask[int(inside[-1]) + 1:]
                solid = mask[int(inside[-1]) + 1:] if over < under else mask[:int(inside[0])]
                widths = foot.sum(axis=1)
                if widths.max() <= LOOP_FOOT[1] * wide \
                        and int((solid.sum(axis=1) >= LOOP_FOOT[0] * wide).sum()) >= LOOP_FOOT[3] * high:
                    near = int((widths >= LOOP_FOOT[0] * wide).sum())
                    if LOOP_SEEN is not None and near <= 0.4 * high:
                        LOOP_SEEN.append({'box': [int(x), int(y), int(x + own_wide - 1), int(y + own_high - 1)], 'over': over,
                                          'under': under, 'foot': float(widths.max() / wide), 'space': float(space)})
            if max(over, under) >= SOLID_LOOP * high and (near <= 0.4 * high or tail):
                span = (0, int(inside[0])) if over > under else (int(inside[-1]) + 1, own_high)
            own_staff = _staff_of(layers, x + own_wide / 2, y + own_high / 2) if ROOM_SOLID and by_holes else None
            if own_staff is not None and x >= layers['staves'][own_staff]['x0'] + ROOM_SOLID[9] * space:
                # Two voices, each with its flag: a room at the top and a room at the foot, and the heads between.
                # A treble clef closes in rooms too: it stands at the start of its staff.
                free = np.flatnonzero(np.diff(inside) > 1)
                if len(free):
                    widest = max(free, key=lambda index: inside[index + 1] - inside[index])
                    between = (int(inside[widest]) + 1, int(inside[widest + 1]))
                    if between[1] - between[0] >= max(SOLID_LOOP * high, over, under) and _flag_room(mask, mask & holes, line, wide, high):
                        span = between
            if span:
                part = mask[span[0]:span[1]]
                # The filled head is solid. A hollow head that a hand drew on a staff line can have one half of its
                # inside open to the paper: the ink around that half is as high as a head too, but it is a ring.
                first = span[0]
                own = np.ascontiguousarray(layers['ink'][y + first:y + first + part.shape[0], x:x + part.shape[1]])
                outline, _ = cv2.findContours(own, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                full = cv2.drawContours(np.zeros(own.shape, np.uint8), outline, -1, 1, cv2.FILLED)
                if part.sum() >= 0.45 * wide * high and own.sum() >= 0.9 * full.sum():
                    flag = ROOM_SOLID and _flag_room(mask, mask & holes, line, wide, high)
                    if len(parts) >= 2 and not (flag and part.shape[0] >= ROOM_SOLID[1] * high):
                        # The staff lines cut the room of the loop in two or three: the rooms are no heads. The
                        # mark is the filled head alone, and it knows where its loop lies.
                        solid = _mark(part, np.zeros_like(part), x, y + first, mark['blob'])
                        if solid:
                            solid['loop'] = (mark['x0'], mark['y0'], mark['x1'], mark['y1'])
                            mark, parts = solid, []
                            named = True
                    elif flag and own_high >= ROOM_SOLID[0] * high:
                        count = 2 if part.shape[0] >= ROOM_SOLID[1] * high else 1
                        cut = []
                        for number in range(count):
                            piece = np.zeros_like(part)
                            band = slice(int(round(number * part.shape[0] / count)), int(round((number + 1) * part.shape[0] / count)))
                            piece[band] = part[band]
                            cut.append(_mark(piece, np.zeros_like(piece), x, y + first, mark['blob']))
                        if all(cut):
                            for piece in cut:
                                piece['loop'] = (mark['x0'], mark['y0'], mark['x1'], mark['y1'])
                            if count == 1:
                                mark = cut[0]
                            else:
                                parts = cut
                            named = True
                    if not named and len(parts) < 2:
                        mark['solid_cy'] = float(first + y + np.nonzero(part)[0].mean())
                        named = True
            if ROOM_HEADS and not named and len(parts) < 2:
                cores, signed = _heads_at_room(mask, mask & holes, wide, high)
                found = [_mark(part, np.zeros_like(part), x, y, mark['blob']) for part in cores]
                found = [part for part in found if part]
                for number, part in enumerate(found):
                    part['loop'] = (mark['x0'], mark['y0'], mark['x1'], mark['y1'])
                    part['room'] = True
                    if signed:
                        part['room_sign'] = True    # the room is closed by the chord's sign, not by a flag (ROOM_CHORD)
                    if number:
                        # Two notes under one beam are no heads of two voices on one line of ink: each is a blob of its own.
                        part['blob'] = -(1000 * len(marks) + number)
                if len(found) == 1:
                    mark = found[0]
                parts = found
        if len(parts) < 2 and mark['blob'] in later:
            # A piece that its own reading does not cut is read again without its cells under a head (CELL_UNDER).
            pieces.extend(later.pop(mark['blob']))
            continue
        marks += parts if len(parts) >= 2 else [mark]
    return marks


def _largest_room(room: np.ndarray, line: int) -> tuple[int, int, float] | None:
    """(width, height, middle column) of the largest room (closed-in paper) of a mark. A staff line cuts a room in
    two: rooms that lie at most `line` px over each other are one."""
    room = cv2.morphologyEx(room.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((line + 2, 1), np.uint8))
    count, _, stats, middles = cv2.connectedComponentsWithStats(room, connectivity=8)
    if count < 2:
        return None
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return int(stats[largest, cv2.CC_STAT_WIDTH]), int(stats[largest, cv2.CC_STAT_HEIGHT]), float(middles[largest][0])


def _loop_room(room: np.ndarray, line: int, wide: float, high: float) -> bool:
    """True when the largest room of a mark is the loop of a flag: higher than the hole of a head, and narrow. The
    mark is higher than its loop by half a head or more: a ring as high as its mark is a hollow head that a hand
    drew upright."""
    found = _largest_room(room, line)
    return bool(found) and found[1] > ROOM_SOLID[2] * high and found[0] <= ROOM_SOLID[3] * wide \
        and room.shape[0] - found[1] >= ROOM_SOLID[4] * high


def _flag_room(mask: np.ndarray, room: np.ndarray, line: int, wide: float, high: float) -> bool:
    """True when the largest room of a mark can be the room of a flag beside its head, and is not the hole of a
    hollow head that touches a filled head. The head is the solid ink of the mark: its highest band of rows without
    a room. The mark is higher than the room by half a head. A room beside the head's column is a flag's room,
    unless it is a lying oval wider than a head. A room in the head's column is the loop of a flag when the ink at
    its two sides is thin (a stem and the flag's stroke: 0.14 to 0.33 of a head together) and the room is upright;
    the rim of a hollow head is 0.5 of a head or more, and the hole of a head with a thin rim lies on its side."""
    found = _largest_room(room, line)
    if not found or room.shape[0] - found[1] < ROOM_SOLID[4] * high:
        return False
    rows = np.flatnonzero(room.any(axis=1))
    edges = np.concatenate(([-1], rows, [room.shape[0]]))
    widest = int(np.argmax(np.diff(edges)))
    part = mask[edges[widest] + 1:edges[widest + 1]]
    if not part.any():
        return True
    if abs(found[2] - np.nonzero(part)[1].mean()) > ROOM_SOLID[5] * wide:
        return not (found[0] > wide and found[1] < ROOM_SOLID[7] * found[0])
    spans = [np.flatnonzero(mask[row]) for row in rows if mask[row].any()]
    reach = float(np.median([span[-1] - span[0] + 1 for span in spans])) if spans else 0.0
    return reach - found[0] <= ROOM_SOLID[6] * wide and found[1] >= ROOM_SOLID[8] * found[0]


def _heads_at_room(mask: np.ndarray, room: np.ndarray, wide: float, high: float) -> tuple[list[np.ndarray], bool]:
    """The filled heads in a mark that a large flag or a short beam makes with them: on a short stem the flag comes
    back to a staff line at the head, and the head, the stem, the flag and the staff lines close in a room; two heads,
    their stems, a beam and a staff line do the same. The mark is larger than a head, and it is no hollow head. An
    oval nearly as large as a head goes through the ink of a head, and not through a stem, a flag or a beam: what it
    leaves are the heads. Returns the part of the mask of each head, and whether a sign of a chord closes the room
    (ROOM_CHORD)."""
    if mask.shape[1] > ROOM_HEADS[1] * wide or mask.shape[0] > ROOM_HEADS[1] * high:
        return [], False
    ink = (mask.astype(bool) & ~room.astype(bool)).astype(np.uint8)
    oval = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(ROOM_HEADS[0] * wide) | 1, int(ROOM_HEADS[0] * high) | 1))
    cores = cv2.morphologyEx(np.pad(ink, 1), cv2.MORPH_OPEN, oval)[1:-1, 1:-1]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(cores, connectivity=8)
    found, ones, chords = [], [], []
    for label in range(1, count):
        left, top, own_wide, own_high, area = (int(value) for value in stats[label])
        if ROOM_HEADS[0] * wide <= own_wide <= 1.3 * wide and own_high <= 1.3 * high and area >= 0.45 * wide * high:
            found.append(labels == label)
            ones.append((len(found) - 1, left + own_wide))
        elif ROOM_CHORD and ROOM_HEADS[0] * wide <= own_wide <= 1.3 * wide \
                and ROOM_CHORD[0] * high <= own_high <= ROOM_CHORD[1] * high and area >= ROOM_CHORD[2] * wide * high:
            # Two heads a third apart, one over the other: the core is as wide as a head and two heads high, and it is
            # cut evenly into its heads (ROOM_CHORD).
            upper, lower = labels == label, labels == label
            upper[top + own_high // 2:] = False
            lower[:top + own_high // 2] = False
            found += [upper, lower]
            chords.append(left)
    signs = set()
    if chords and ROOM_CHORD:
        # The core of a head's size that ends before such a chord is the chord's sign, no head.
        signs = {index for index, right in ones if right <= min(chords) + ROOM_CHORD[3] * wide}
        found = [part for index, part in enumerate(found) if index not in signs]
    return (found, bool(signs)) if len(found) <= ROOM_HEADS[2] else ([], False)


def _staff_of(layers: dict, x: float, y: float) -> int | None:
    """The staff that a height belongs to: the nearest staff whose columns hold x."""
    best, best_far = None, None
    for index, staff in enumerate(layers['staves']):
        if not staff['x0'] - 2 * staff['space'] <= x <= staff['x1'] + 2 * staff['space']:
            continue
        far = max(staff['rows'][0] - y, y - staff['rows'][4], 0.0)
        if best_far is None or far < best_far:
            best, best_far = index, far
    return best


def follow(ink: np.ndarray, x: int, y: int, step: int, space: float, least: int = 0, most: int = 10 ** 9,
           bridge: float = 1.0) -> tuple[int, int, list]:
    """Follows ink from (x, y) up (step -1) or down (step 1), in a band of a quarter staff space to each side of x
    (and inside the columns least..most). Returns (the last row with ink, its column, the rows with ink on the way:
    (row, column) of each). A weak copy breaks a stem: a gap of up to GAP staff spaces does not end the way, when
    the ink goes on in the same columns; `bridge` is the share of that gap that this page may have (layers['bridge'])."""
    height, width = ink.shape
    half = max(2, int(round(0.22 * space)))
    first, last = max(0, x - half, least), min(width, x + half + 1, most + 1)
    if last - first < 1 or not first <= x < last:
        return y, x, []
    reach = np.zeros(last - first, bool)
    reach[max(0, x - 1 - first):x + 2 - first] = ink[y, max(first, x - 1):min(last, x + 2)] > 0
    if not reach.any():
        return y, x, []
    limit = max(2, int(GAP * bridge * space))
    end, end_x, gap = y, x, 0
    path = []
    row = y + step
    while 0 <= row < height:
        spread = reach.copy()
        spread[1:] |= reach[:-1]
        spread[:-1] |= reach[1:]
        here = (ink[row, first:last] > 0) & spread
        if here.any():
            reach, gap = here, 0
            end, end_x = row, first + int(np.nonzero(here)[0].mean())
            path.append((end, end_x))
        else:
            gap += 1
            if gap > limit:
                break
        row += step
    return end, end_x, path


def _run(ink: np.ndarray, row: int, column: int) -> int:
    """The length of the level run of ink through a pixel."""
    line = ink[row]
    first = column
    while first > 0 and line[first - 1]:
        first -= 1
    last = column
    while last + 1 < len(line) and line[last + 1]:
        last += 1
    return last - first + 1


def _on_upright(layers: dict, mark: dict, way: dict) -> bool:
    """Does the ink of the way go on upright past the end to which it was followed (see SLUR_STEM)? A stem that a hand
    drew with a bend does; the end of a slur has turned to the side there."""
    ink, space = layers['bare' if mark.get('room') else 'joined'], layers['space']
    step = -1 if way['direction'] == 'up' else 1
    reach, side = int(SLUR_STEM[4] * space), int(SLUR_STEM[5] * space)
    rows = [way['end'] + step * number for number in range(1, reach + 1)]
    found = sum(1 for row in rows
                if 0 <= row < ink.shape[0] and ink[row, max(0, way['x'] - side):way['x'] + side + 1].any())
    return found >= SLUR_STEM[6] * max(1, reach)


def _way(layers: dict, mark: dict, up: bool, right: bool) -> dict | None:
    """The upright ink that leaves a thick mark: up or down, from its right half or its left half. Returns
    {'direction', 'x' (the column of its far end), 'mid' (its middle column), 'end' (the row of its far end),
    'length' (px from the mark's middle), 'past' (px past the mark's edge), 'slim' (the rows past the mark's edge where the ink is as slim as a stem), 'inked' (the rows past
    the edge that have ink)}, or None when no ink leaves the mark there."""
    # (The room at a head that a flag or a beam closes is filled in 'joined': its stem is followed in the bare ink.)
    ink, space = layers['bare' if mark.get('room') else 'joined'], layers['space']
    y = int(round(mark['cy']))
    edge = int(0.15 * space)
    first, last = (int(mark['cx']), mark['x1'] + edge) if right else (mark['x0'] - edge, int(mark['cx']))
    best = None
    for x in range(max(1, first), min(ink.shape[1] - 1, last + 1), 2):
        # The way starts in the mark or at its side, at the height of its middle or nearer to the end it goes to.
        start = None
        for row in ((y, y - 2, y - 4, mark['y0']) if up else (y, y + 2, y + 4, mark['y1'])):
            if ink[row, x - 1:x + 2].any():
                start = row
                break
        if start is None:
            continue
        # The way keeps to its half of the mark, so a stroke at the left side is not taken for one at the right.
        middle = int(mark['cx'])
        end, end_x, path = follow(ink, x, start, -1 if up else 1, space,
                                  least=middle - 1 if right else 0, most=10 ** 9 if right else middle + 1,
                                  bridge=layers.get('bridge', 1.0))
        length = (y - end) if up else (end - y)
        if best is None or length > best['length']:
            best = {'direction': 'up' if up else 'down', 'x': end_x, 'end': end, 'length': length, 'path': path}
    if best is None:
        return None
    best['past'] = (mark['y0'] - best['end']) if up else (best['end'] - mark['y1'])
    outside = [(row, column) for row, column in best.pop('path') if (row < mark['y0'] if up else row > mark['y1'])]
    best['inked'] = len(outside)
    best['mid'] = int(np.median([column for row, column in outside])) if outside else best['x']
    best['slim'] = sum(1 for row, column in outside if _run(ink, row, column) <= SLIM_STEM * space)
    # How much the way bends in its last part: a straight stem, slanted or not, has 0; a stem that was followed
    # into the end of a slur turns there (staff spaces; positive: to the right).
    step = int(round(STEM_TURN * space))
    best['turn'] = 0.0
    if step and len(outside) > 2 * step + 2:
        columns = [column for row, column in outside]
        one, two = float(np.median(columns[-step - 3:-step + 2])), float(np.median(columns[-2 * step - 3:-2 * step + 2]))
        best['turn'] = (columns[-1] - 2 * one + two) / space
    # How far the way moves sideways from where it leaves the mark to its end (staff spaces; positive: to the right).
    # A printed stem stands upright; the end of a slur that meets a head is steep there, and it leans.
    best['lean'] = 0.0
    if len(outside) >= 6:
        columns = [column for row, column in outside]
        best['lean'] = (float(np.median(columns[-3:])) - float(np.median(columns[:3]))) / space
    return best


def _pale_on(layers: dict, way: dict) -> int:
    """How many px the upright ink of a way goes on past its end as pale ink (see PALE_STEM): the scan kept a thin
    stem as grey that is no ink for the page's limit."""
    grey, space = layers['grey'], layers['space']
    height, width = grey.shape
    step = -1 if way['direction'] == 'up' else 1
    side, most = max(3, int(round(PALE_STEM[1] * space))), max(3, int(round(PALE_STEM[2] * space)))
    x, end = int(way['x']), int(way['end'])
    row, gap, last = end + step, 0, end
    while 0 <= row < height and side + 2 <= x < width - side - 2:
        here = grey[row, x - 1:x + 2]
        at = int(here.argmin())
        paper = min(int(grey[row, x - side - 1:x - side + 2].min()), int(grey[row, x + side - 1:x + side + 2].min()))
        if int(here[at]) + PALE_STEM[0] <= paper:
            last, gap, x = row, 0, x + at - 1
        else:
            gap += 1
            if gap > most:
                break
        row += step
    return abs(last - end)


def _at_staff(layers: dict, mark: dict) -> bool:
    """True when a mark stands where a head needs no ledger line (in the staff or in the first space beside it), or
    on a ledger line."""
    index = _staff_of(layers, mark['cx'], mark['cy'])
    if index is None:
        return False
    return abs(pitch_place(layers['staves'][index], mark['cy'])) <= 5.6 or _on_ledger(layers, mark)


def _in_words(layers: dict, mark: dict) -> bool:
    """True when a mark stands in a band of words (scorereader.words): it is a letter."""
    space = layers['space']
    return any(band['x0'] <= mark['cx'] <= band['x1'] and band['top'] <= mark['cy'] <= band['bottom']
               and mark['y0'] >= band['top'] - 0.3 * space and mark['y1'] <= band['bottom'] + 0.5 * space
               for band in layers.get('words') or [])


def _into_words(layers: dict, mark: dict, way: dict | None, before: float = 0.3) -> dict | None:
    """The band of words (scorereader.words) that the upright ink of a mark runs into, or ends at most `before` staff
    spaces before, when the mark stands clear of the band and near it; else None."""
    if not way:
        return None
    space = layers['space']
    for band in layers.get('words') or []:
        if not band['x0'] <= way['x'] <= band['x1']:
            continue
        if way['direction'] == 'down':
            if mark['cy'] < band['top'] - 0.2 * space and band['top'] <= mark['y1'] + WORD_STEM[1] * space \
                    and way['end'] >= band['top'] - before * space:
                return band
        elif mark['cy'] > band['bottom'] + 0.2 * space and band['bottom'] >= mark['y0'] - WORD_STEM[1] * space \
                and way['end'] <= band['bottom'] + before * space:
            return band
    return None


def is_stem(way: dict | None, space: float) -> bool:
    """True when the upright ink that leaves a mark is a stem: long enough, and slim where it is past the mark.
    The head of a chord over or under a head is upright ink too, but it is not slim."""
    return bool(way) and way['length'] >= STEM * space and way['past'] >= PAST * space \
        and way['slim'] >= SLIM_PAST * space and way['inked'] >= INKED * way['past']


def _kind(mark: dict, space: float) -> str | None:
    """What a thick mark is, from the upright ink that leaves it: 'head', 'sharp', 'flat', 'natural' or None.

    A stem goes up from the right half of a head or down from its left half. A flat is a small bowl with a stroke
    that goes up from its left side. A sharp has strokes that go up and down at both sides. A natural has one stroke
    up at the left and one down at the right."""
    ways = mark['ways']
    past = {name: (way['past'] / space if way else 0.0) for name, way in ways.items()}
    slim = {name: (way['slim'] / space if way else 0.0) for name, way in ways.items()}
    wide, high = (mark['x1'] - mark['x0'] + 1) / space, (mark['y1'] - mark['y0'] + 1) / space
    # The strokes of a sharp are slim where they leave the mark. A head over or under a head leaves it wide.
    if min(past.values()) >= 0.3 and min(slim.values()) >= SHARP_SLIM and high <= 2.4:
        return 'sharp'
    if wide <= 1.1 and high <= 1.6:
        if past['up_left'] >= 0.45 and past['down_right'] >= 0.45 and past['up_right'] < 0.3 and past['down_left'] < 0.3:
            return 'natural'
        if past['up_left'] >= 0.7 and max(past['up_right'], past['down_left'], past['down_right']) < 0.3:
            return 'flat'
    if HAND_FLAT and wide <= HAND_FLAT and high <= 1.6 and past['up_left'] >= 0.7 and max(past['down_left'], past['down_right']) < 0.6:
        # A flat that a hand drew: its stroke leans, so it goes up from the left half of the bowl and from the right
        # half as one stroke. The stem of a note goes up from the right edge of its head.
        left, right = ways['up_left'], ways['up_right']
        one = right is None or past['up_right'] < 0.3 or (abs(right['x'] - left['x']) <= 0.2 * space
                                                         and abs(right['end'] - left['end']) <= 0.2 * space)
        if one and left['x'] <= mark['cx']:
            return 'flat'
    if HEAD_WIDE[0] <= wide <= HEAD_WIDE[1] and HEAD_HIGH[0] <= high <= HEAD_HIGH[1]:
        return 'head'
    return None


def _wings(layers: dict, mark: dict) -> float | None:
    """The row of a ledger line that goes through a head, read from its two ends. A large head hides its ledger
    line, and a thick ledger line is a part of the head's mark. But at both sides of the head's body the ink is
    suddenly thin, level and of one thickness: the two ends of the line. None when the head has no such ends."""
    free, space = layers['free'], layers['space']
    reach = int(round(0.9 * space))
    top, bottom = max(0, int(mark['y0'] - 0.3 * space)), min(free.shape[0], int(mark['y1'] + 0.3 * space) + 1)
    first, last = max(0, mark['x0'] - reach), min(free.shape[1], mark['x1'] + reach + 1)
    window = free[top:bottom, first:last]
    heights = window.sum(axis=0)
    own = heights[mark['x0'] - first:mark['x1'] - first + 1]
    if own.size == 0 or own.max() == 0:
        return None
    thin = min(0.45 * own.max(), 0.6 * space)
    body = np.nonzero(own >= 0.6 * own.max())[0]
    ends = []
    for step, column in ((-1, mark['x0'] - first + int(body[0]) - 1), (1, mark['x0'] - first + int(body[-1]) + 1)):
        while 0 <= column < len(heights) and heights[column] > thin:
            column += step        # the round end of the head
        wing = []
        while 0 <= column < len(heights) and 0 < heights[column] <= thin:
            rows = np.nonzero(window[:, column])[0]
            if rows[-1] - rows[0] + 1 != len(rows):
                break             # two lines, one over the other: not the end of one line
            wing.append((heights[column], top + float(rows.mean())))
            column += step
        if not wing:
            return None
        usual = float(np.median([high for high, _ in wing]))
        even = [row for high, row in wing if abs(high - usual) <= max(2.0, 0.08 * space)]
        if len(even) < WINGS * space or max(even) - min(even) > 0.2 * space:
            return None
        ends.append(float(np.median(even)))
    if abs(ends[0] - ends[1]) > 0.25 * space:
        return None
    return (ends[0] + ends[1]) / 2


def _whole_foot(layers: dict, staff: dict, mark: dict, above: bool) -> bool:
    """True when the edge of a mark toward its staff is a level line as wide as the mark, at the height of the first
    ledger line (see WHOLE_FOOT)."""
    free, space = layers['free'], staff['space']
    reach = max(2, int(round(WHOLE_FOOT[4] * space)))
    rows = range(mark['y1'] - reach + 1, mark['y1'] + 1) if above else range(mark['y0'], mark['y0'] + reach)
    edge = staff['rows'][0] if above else staff['rows'][-1]
    wide = mark['x1'] - mark['x0'] + 1
    for row in rows:
        if not (0 <= row < free.shape[0] and WHOLE_FOOT[1] * space <= abs(row - edge) <= WHOLE_FOOT[2] * space):
            continue
        if free[row, mark['x0']:mark['x1'] + 1].sum() >= WHOLE_FOOT[0] * wide \
                and not layers['holes'][row, mark['x0']:mark['x1'] + 1].any():
            return _alone(layers, mark, WHOLE_FOOT[5] * space, WHOLE_FOOT[6] * space)
    return False


def _alone(layers: dict, mark: dict, high: float, wide: float) -> bool:
    """True when the piece of ink that holds a mark goes on at most `high` pixels over and under the mark's box and
    at most `wide` pixels at its sides: the mark stands alone in paper."""
    ink = layers['ink']
    up, side = int(np.ceil(high)) + 2, int(np.ceil(wide)) + 2
    top, left = max(0, mark['y0'] - up), max(0, mark['x0'] - side)
    window = (ink[top:mark['y1'] + up + 1, left:mark['x1'] + side + 1] > 0).astype(np.uint8)
    count, labels = cv2.connectedComponents(window, connectivity=8)
    own = labels[mark['y0'] - top:mark['y1'] - top + 1, mark['x0'] - left:mark['x1'] - left + 1]
    held = np.bincount(own[own > 0], minlength=count)
    if not held.any():
        return False
    rows, columns = np.nonzero(labels == int(np.argmax(held)))
    return mark['y0'] - (top + rows.min()) <= high and top + rows.max() - mark['y1'] <= high \
        and mark['x0'] - (left + columns.min()) <= wide and left + columns.max() - mark['x1'] <= wide


def _foot_wing(layers: dict, mark: dict) -> float | None:
    """The row of the thin level ink that leaves the body of a mark at one side (the longer one, at least
    LEDGER_FOOT[3] staff spaces long and at most LEDGER_FOOT[4] thick): one end of a ledger line. None without it."""
    free, space = layers['free'], layers['space']
    reach = int(round(0.9 * space))
    top, bottom = max(0, int(mark['y0'] - 0.3 * space)), min(free.shape[0], int(mark['y1'] + 0.3 * space) + 1)
    first, last = max(0, mark['x0'] - reach), min(free.shape[1], mark['x1'] + reach + 1)
    window = free[top:bottom, first:last]
    heights = window.sum(axis=0)
    own = heights[mark['x0'] - first:mark['x1'] - first + 1]
    if own.size == 0 or own.max() == 0:
        return None
    thin = min(0.45 * own.max(), 0.6 * space)
    body = np.nonzero(own >= 0.6 * own.max())[0]
    best = None
    for step, column in ((-1, mark['x0'] - first + int(body[0]) - 1), (1, mark['x0'] - first + int(body[-1]) + 1)):
        while 0 <= column < len(heights) and heights[column] > thin:
            column += step
        wing = []
        while 0 <= column < len(heights) and 0 < heights[column] <= thin:
            rows = np.nonzero(window[:, column])[0]
            if rows[-1] - rows[0] + 1 != len(rows):
                break
            wing.append((heights[column], top + float(rows.mean())))
            column += step
        if not wing:
            continue
        usual = float(np.median([high for high, _ in wing]))
        even = [row for high, row in wing if abs(high - usual) <= max(2.0, 0.08 * space)]
        if len(even) < LEDGER_FOOT[3] * space or max(even) - min(even) > 0.2 * space or usual > LEDGER_FOOT[4] * space:
            continue
        if best is None or len(even) > best[0]:
            best = (len(even), float(np.median(even)))
    return best[1] if best else None


LEDGER_DASH = (0.15, 0.6, 0.25, (0.7, 1.3), 0.6, 1.5)   # a print whose first ledger line is two short dashes beside the
#   head that sits on it: thin level ink (at most the third number of staff spaces thick) in this many staff spaces
#   of columns or more at each side of the foot of the mark, within the second number of it, the two at one row, that
#   row from this to this many staff spaces from the staff. The mark is a head on that line where it is at least the
#   fifth number of the page's head high and its stem goes on the last number of staff spaces past it (None: off)


def _foot_dashes(layers: dict, staff: dict, mark: dict, up: bool) -> bool:
    """True when a mark beside the staff has the end of a ledger line at each side of its foot (see LEDGER_DASH)."""
    free, space = layers['free'], staff['space']
    foot = mark['y1'] if up else mark['y0']
    top, bottom = (foot - 0.2 * space, foot + 0.3 * space) if up else (foot - 0.3 * space, foot + 0.2 * space)
    top, bottom = max(0, int(top)), min(free.shape[0], int(bottom) + 1)
    reach = int(LEDGER_DASH[1] * space)
    rows = []
    for first, last in ((mark['x0'] - reach, mark['x0']), (mark['x1'] + 1, mark['x1'] + 1 + reach)):
        window = free[top:bottom, max(0, first):min(free.shape[1], last)]
        heights = window.sum(axis=0)
        thin = np.nonzero((heights > 0) & (heights <= LEDGER_DASH[2] * space))[0]
        if len(thin) < LEDGER_DASH[0] * space:
            return False
        rows.append(float(np.median([np.nonzero(window[:, column])[0].mean() for column in thin])) + top)
    edge = staff['rows'][0] if up else staff['rows'][-1]
    return abs(rows[0] - rows[1]) <= 0.15 * space \
        and LEDGER_DASH[3][0] * space <= abs((rows[0] + rows[1]) / 2 - edge) <= LEDGER_DASH[3][1] * space


def _ledger_beside(layers: dict, head: dict, row: float, space: float) -> bool:
    """Whether the level row through a filled head is the ink of another head that touches it at one side
    (LEDGER_BESIDE)."""
    rule, free = LEDGER_BESIDE, layers['free']
    wide, high = head['x1'] - head['x0'] + 1, head['y1'] - head['y0'] + 1
    if abs(row - (head['y0'] + head['y1']) / 2) > rule[0] * high:
        return False
    head_wide, head_high = layers.get('head') or (space, space)
    fits = rule[1] * head_high <= high and wide <= rule[2] * head_wide
    reach = int(round(RIM_WINGS[0] * space))
    band = free[max(0, int(row) - 2):int(row) + 3]
    wings = (band[:, max(0, head['x0'] - reach):max(0, head['x0'] - 1)].max(axis=0, initial=0),
             band[:, head['x1'] + 2:head['x1'] + reach + 1].max(axis=0, initial=0))
    shares = [float(wing.mean()) if wing.size else 1.0 for wing in wings]
    window = free[max(0, int(head['y0'] - 0.5 * space)):int(head['y1'] + 0.5 * space) + 1]
    span = int(round(head_wide))
    sides = (window[:, max(0, head['x0'] - span):head['x0']][:, ::-1], window[:, head['x1'] + 1:head['x1'] + 1 + span])
    same, glued = [], []
    for side in sides:
        columns = []
        for column in side.T:
            ink = np.nonzero(column)[0]
            extent = int(ink[-1] - ink[0] + 1) if ink.size else 0
            columns.append((extent, ink.size / extent if extent else 0.0))
        same.append(sum(1 for extent, fill in columns
                        if rule[3] * high <= extent <= rule[4] * high and fill >= rule[6]) / max(1, span))
        glued.append(any(extent >= rule[3] * high for extent, _ in columns[:3]))
    drop = fits and any(shares[1 - side] < RIM_WINGS[1] and same[side] >= rule[5] and glued[side] for side in (0, 1))
    if LEDGER_BESIDE_SEEN is not None:
        LEDGER_BESIDE_SEEN.append({'box': [int(head['x0']), int(head['y0']), int(head['x1']), int(head['y1'])],
                                   'row': float(row), 'place': head.get('place'), 'wings': shares, 'same': same,
                                   'glued': glued, 'size': [wide / head_wide, high / head_high], 'drop': bool(drop)})
    return drop


LEDGER_NARROW = (0.25, 0.25, 2)   # a print that draws its ledger lines short (extra-come-bless: a line 1.3 heads wide, 0.77
#   of the window that ledger_lines asks): where no ledger line was found 0.95 staff spaces to each side of a head far
#   beside the staff, the lines are looked for again in the head's own width and this many staff spaces at each side,
#   and the head is a note where every line between the staff and the head is found there, each within this many staff
#   spaces of its step from the staff, and there are at least this many of them. One line alone is any level stroke
#   beside a mark: the census of the one-line form named the end of a slur, a smudge over a word and the crossbar of a
#   sharp among its new heads. (None: off)
LEDGER_NARROW_SEEN = None   # census: a dict for each head that LEDGER_NARROW gives its ledger lines


def _step_rows(staff: dict, head: dict, rows: list[float], fewest: int) -> list[float]:
    """The rows when they are every ledger line between the staff and the head, each within LEDGER_NARROW[1] staff
    spaces of its step from the staff, and at least the fewest; else []."""
    space = staff['space']
    rows = sorted(rows)
    count = int((abs(head['place']) - 4 + 0.5) // 2)
    up = head['cy'] < staff['rows'][0]
    steps = sorted(staff['rows'][0] - k * space if up else staff['rows'][4] + k * space for k in range(1, count + 1))
    if count < fewest or len(rows) != count or any(abs(row - step) > LEDGER_NARROW[1] * space for row, step in zip(rows, steps)):
        return []
    return rows


def _narrow_ledgers(layers: dict, staff: dict, head: dict, fewest: int | None = None) -> list[float]:
    """The ledger lines of a head far beside the staff whose print draws them short (LEDGER_NARROW), or [] where not
    every line between the staff and the head is found at its step."""
    rows = ledger_lines(layers, staff, head, (head['x1'] - head['x0'] + 1) / 2 + LEDGER_NARROW[0] * staff['space'])
    return _step_rows(staff, head, rows, LEDGER_NARROW[2] if fewest is None else fewest)


def ledger_lines(layers: dict, staff: dict, head: dict, half: float | None = None) -> list[float]:
    """The rows of the ledger lines between a staff and a head beside it, the line through the head too. A ledger
    line is a level run of ink that reaches past the head on both sides and is thinner than a head."""
    free, space = layers['free'], staff['space']
    above = head['cy'] < staff['rows'][0]
    first, last = int(head['cx'] - (half or 0.95 * space)), int(head['cx'] + (half or 0.95 * space))
    if first < 0 or last >= free.shape[1]:
        return []
    if above:
        top, bottom = int(head['y0'] - 0.3 * space), int(staff['rows'][0] - LEDGER_FROM * space)
    else:
        top, bottom = int(staff['rows'][4] + LEDGER_FROM * space), int(head['y1'] + 0.3 * space)
    top, bottom = max(0, top), min(free.shape[0] - 1, bottom)
    if LEDGER_WORDS:
        # The level strokes of the letters are no ledger lines.
        for band in layers.get('words') or []:
            if band['x0'] <= head['cx'] <= band['x1']:
                if not above and head['cy'] < band['top'] <= bottom:
                    bottom = band['top'] - 1
                if above and head['cy'] > band['bottom'] >= top:
                    top = band['bottom'] + 1
    if bottom <= top:
        return []
    window = free[top:bottom + 1, first:last + 1]
    if LEDGER_INK:
        # The filling of a hollow head is no ink: a wide half note beside the staff is not its own ledger line.
        window = window & (1 - layers['holes'][top:bottom + 1, first:last + 1])
    cover = window.mean(axis=1)
    cover[1:] = np.maximum(cover[1:], window[:-1].mean(axis=1))    # a line that leans a little
    rows, run = [], []
    for step, value in enumerate(list(cover) + [0.0]):
        if value >= 0.8:
            run.append(step)
        elif run:
            if len(run) <= 0.6 * space:
                rows.append(top + (run[0] + run[-1]) / 2)
            run = []
    if LEDGER_BESIDE and not (head.get('hollow') or head.get('hole', 0.0) >= HOLLOW):
        rows = [row for row in rows if not _ledger_beside(layers, head, row, space)]
    if RIM_WINGS and (head.get('hollow') or head.get('hole', 0.0) >= HOLLOW):
        # The upper and the lower rim of a wide hollow head are level ink too. A ledger line at the edge of such a
        # head goes on past the head at both sides.
        high = head['y1'] - head['y0'] + 1
        reach = int(round(RIM_WINGS[0] * space))
        kept = []
        for row in rows:
            at_rim = head['y0'] - 1 <= row <= head['y0'] + 0.3 * high or head['y1'] - 0.3 * high <= row <= head['y1'] + 1
            if at_rim:
                band = free[max(0, int(row) - 2):int(row) + 3]
                left = band[:, max(0, head['x0'] - reach):max(0, head['x0'] - 1)].max(axis=0, initial=0)
                right = band[:, head['x1'] + 2:head['x1'] + reach + 1].max(axis=0, initial=0)
                if not (left.size and right.size and left.mean() >= RIM_WINGS[1] and right.mean() >= RIM_WINGS[1]):
                    continue
            kept.append(row)
        rows = kept
    if WINGS:
        row = _wings(layers, head)
        if row is not None and top <= row <= bottom and all(abs(row - other) >= 0.3 * space for other in rows):
            rows = sorted(rows + [row])
    return rows


LEDGER_SHORT = (5.5, 6.5, 0.3, 0.15, 0.65, 0.1)   # the same print draws that line short, and no ledger line is found: a mark
#                      beside the staff whose measured place lies from this to this. The rows where the ink runs on
#                      through the mark's middle this many staff spaces longer than a head of the page is wide are a
#                      line's. They are the foot of a head that sits on the line where at most this many staff spaces
#                      of the mark lie between them and the staff, where they are at most this thick together (the
#                      rim of a wide oval that a hand drew is as thick as the oval), and where the line sticks out at
#                      both sides, by this much, past the mark's ink 0.3 staff spaces farther from the staff (None: off)


def _short_line(layers: dict, head: dict, up: bool, space: float) -> bool:
    """True when a mark holds a short ledger line as its foot: nothing of the mark lies between that line and the
    staff, and the head stands on it (see LEDGER_SHORT)."""
    free, cx = layers['free'], int(round(head['cx']))
    reach, slack = int(1.3 * space), int(0.3 * space)
    first = max(0, cx - reach)
    long = layers['head'][0] + LEDGER_SHORT[2] * space
    line = []
    for y in range(head['y0'], head['y1'] + 1):
        row = free[y, first:cx + reach + 1]
        at = cx - first
        if not row[at]:
            near = np.nonzero(row[max(0, at - slack):at + slack + 1])[0]
            if not near.size:
                continue
            at = max(0, at - slack) + int(near[np.argmin(np.abs(near - min(at, slack)))])
        left = right = at
        while left > 0 and row[left - 1]:
            left -= 1
        while right < len(row) - 1 and row[right + 1]:
            right += 1
        if right - left + 1 >= long:
            line.append((y, first + left, first + right))
    if not line or len(line) > LEDGER_SHORT[4] * space:
        return False
    if (head['y1'] - line[-1][0] if up else line[0][0] - head['y0']) > LEDGER_SHORT[3] * space:
        return False
    begin, end = min(left for _, left, _ in line), max(right for _, _, right in line)
    body = (line[0][0] - slack) if up else (line[-1][0] + slack)
    if not head['y0'] <= body <= head['y1']:
        return False
    ink = np.nonzero(free[body, begin:end + 1])[0]
    return bool(ink.size) and ink[0] >= LEDGER_SHORT[5] * space and (end - begin) - ink[-1] >= LEDGER_SHORT[5] * space


def _near_ink(layers: dict, head: dict, last: float, up: bool, space: float) -> float:
    """The share of ink right at the near edge of a head's last ledger line, toward the staff, under the head's
    middle (see LEDGER_PAPER). The edge of the line is measured at its wings, beside the head. The hole of a hollow
    head counts as ink: a whole note on the line has its hole there."""
    free, cx = layers['free'], head['cx']
    wings = [column for column in list(range(int(cx - 0.95 * space), int(cx - 0.7 * space) + 1))
             + list(range(int(cx + 0.7 * space), int(cx + 0.95 * space) + 1)) if 0 <= column < free.shape[1]]
    row = edge = int(round(last))
    step = 1 if up else -1
    while wings and 0 < edge + step < free.shape[0] - 1 and abs(edge + step - row) <= 0.4 * space \
            and free[edge + step, wings].mean() >= 0.5:
        edge += step
    first, other = edge + step, edge + step * max(2, int(round(LEDGER_PAPER[2] * space)))
    half = LEDGER_PAPER[3] / 2 * space
    rows, columns = slice(max(0, min(first, other)), max(first, other) + 1), slice(max(0, int(cx - half)), int(cx + half) + 1)
    band = free[rows, columns] | layers['holes'][rows, columns]      # the inside of a hollow head on the line is no paper
    return float(band.mean()) if band.size else 1.0


def _line_out(layers: dict, head: dict, last: float, up: bool, space: float) -> bool:
    """True when a head stands on its last ledger line, past it: 0.3 staff spaces past the line the mark is as wide
    as a head, and the line is longer than that (see LEDGER_PAPER)."""
    free, cx = layers['free'], int(round(head['cx']))
    row = int(round(last))
    if not 0 < row < free.shape[0] - 1 or not 0 <= cx < free.shape[1]:
        return False
    if not free[row, cx]:
        row += 1 if free[row + 1, cx] else -1 if free[row - 1, cx] else 0
    if not free[row, cx]:
        return False
    begin = end = cx
    while begin > 0 and free[row, begin - 1]:
        begin -= 1
    while end < free.shape[1] - 1 and free[row, end + 1]:
        end += 1
    wings = [column for column in list(range(int(cx - 0.95 * space), int(cx - 0.7 * space) + 1))
             + list(range(int(cx + 0.7 * space), int(cx + 0.95 * space) + 1)) if 0 <= column < free.shape[1]]
    edge, step = row, -1 if up else 1
    while wings and 0 < edge + step < free.shape[0] - 1 and abs(edge + step - row) <= 0.4 * space \
            and free[edge + step, wings].mean() >= 0.5:
        edge += step
    body = edge + step * int(0.3 * space)
    if not 0 <= body < free.shape[0]:
        return False
    ink = np.nonzero(free[body, begin:end + 1])[0]
    if not ink.size:
        return False
    wide = int(ink[-1] - ink[0] + 1)
    return LEDGER_PAPER[4] * layers['head'][0] <= wide <= LEDGER_PAPER[5] * layers['head'][0] \
        and (end - begin + 1) - wide >= LEDGER_PAPER[6] * space


def ledger_place(layers: dict, staff: dict, head: dict) -> float | None:
    """The place of a head beside the staff, read from its ledger lines as a singer reads it: the lines are counted,
    and the head stands on the last one or past it. A hand often draws the ledger lines nearer to each other than the
    staff lines, so the measured height alone names such a head a step off. Without a ledger line, and when the count
    and the measured height are a little apart, the measured place stays. None when the head is far from the staff
    and too few ledger lines lead to it: then it is no note."""
    rows, space = sorted(head.get('ledgers') or []), staff['space']
    place = head['place']
    if not rows:
        if LEDGER_FOOT and 4.6 < abs(place) < 7.5:
            # A ledger line that an engraver set close to the staff, with the head on top of it: the line is the foot
            # of the mark, and it shows at one side of the head only (the stem stands at the other).
            row = _foot_wing(layers, head)
            if row is not None:
                edge = staff['rows'][0] if place > 0 else staff['rows'][-1]
                foot = ((row - head['y0']) if place > 0 else (head['y1'] - row)) / max(1, head['y1'] - head['y0'])
                if foot >= LEDGER_FOOT[0] and LEDGER_FOOT[1] * space <= abs(row - edge) <= LEDGER_FOOT[2] * space:
                    return 7.0 if place > 0 else -7.0
        if LEDGER_SHORT and LEDGER_SHORT[0] <= abs(place) < LEDGER_SHORT[1] and _short_line(layers, head, place > 0, space):
            return 7.0 if place > 0 else -7.0
        if NO_LEDGER and 4.6 < abs(place) <= NO_LEDGER_FIVE:
            return 5.0 if place > 0 else -5.0     # a head beside the staff with no ledger line stands in the first space
        return place
    up = place > 0
    if LEDGER_OWN:
        # No ledger line lies past its head: a row further from the staff than the last row in the head's box is
        # the next head's line, the head's own rim, a slur or a word.
        inside = [row for row in rows if head['y0'] <= row <= head['y1']]
        if inside:
            own = min(inside) if up else max(inside)
            rows = [row for row in rows if (row >= own - 0.5 if up else row <= own + 0.5)]
    if LEDGER_TWIN:
        edge = staff['rows'][0] if up else staff['rows'][-1]
        free = layers['free']
        first, last = int(head['cx'] - 0.95 * space), int(head['cx'] + 0.95 * space)
        index = 0
        while index + 1 < len(rows) and first >= 0:
            one, two = rows[index], rows[index + 1]
            if LEDGER_TWIN[0] * space <= two - one < 0.5 * space:
                band = free[int(round(one)) + 1:int(round(two)), first:last + 1]
                sides = (band[:, :max(0, head['x0'] - first)], band[:, max(0, head['x1'] + 1 - first):])
                if all(side.size and int(((1 - side).mean(axis=1) >= 0.8).sum()) >= LEDGER_TWIN[1] for side in sides):
                    # Paper between the two rows at both sides of the head: one of them is no ledger line.
                    off = [abs(abs(row - edge) / space - round(abs(row - edge) / space)) for row in (one, two)]
                    stray = index if off[0] > off[1] else index + 1
                    if not head['y0'] <= rows[stray] <= head['y1']:
                        del rows[stray]
                        continue
            index += 1
    merged = []
    for row in rows:
        if merged and row - merged[-1] < 0.5 * space:
            merged[-1] = (merged[-1] + row) / 2
        else:
            merged.append(row)
    last = merged[0] if up else merged[-1]
    if head['hollow']:
        centre = head['cy']
        high = head['y1'] - head['y0'] + 1
        if LEDGER_THROUGH and head['y0'] + LEDGER_THROUGH * high <= last <= head['y1'] - LEDGER_THROUGH * high:
            # The line through a hollow head cuts its inside in two, and a print fills one half: the middle of the
            # paper that is left lies off the middle of the head.
            centre = (head['y0'] + head['y1']) / 2
    else:
        # A thick ledger line under a head is a part of its mark: the middle is measured from the head's far edge.
        high = min(layers['head'][1], head['y1'] - head['y0'] + 1)
        centre = head['y0'] + high / 2 if up else head['y1'] - high / 2
    past = (last - centre) if up else (centre - last)      # how far the head's middle is past its last ledger line
    limit = 0.27
    if LEDGER_SIT and not head['hollow']:
        before = (merged[1] if up else merged[-2]) if len(merged) > 1 else staff['rows'][0 if up else -1]
        if abs(last - before) <= LEDGER_SIT[1] * space:
            limit = LEDGER_SIT[0]
            foot = ((last - head['y0']) if up else (head['y1'] - last)) / max(1, head['y1'] - head['y0'])
            if LEDGER_SIT_FOOT and foot >= LEDGER_SIT_FOOT[0]:
                limit = LEDGER_SIT_FOOT[1]     # the line is the foot of the mark: the head sits on it
    sits, reach = past > limit * space, 1.6
    if LEDGER_PAPER and not sits and past >= -0.27 * space:
        before = staff['rows'][0 if up else -1]
        if len(merged) == 1 and abs(last - before) <= LEDGER_PAPER[0] * space \
                and _near_ink(layers, head, last, up, space) <= LEDGER_PAPER[1] and _line_out(layers, head, last, up, space):
            # Paper between the line and the staff: the head is no head on the line. Its mark is the half moon and
            # the line under it, so its measured place lies near the line.
            sits, reach = True, 2.0
    steps = 2 * len(merged) + (1 if sits else 0 if past >= -0.27 * space else -1)
    found = float(4 + steps) if up else float(-4 - steps)
    if abs(found) < abs(place) - 2.2:
        return None       # too few ledger lines for a head this far from the staff: a letter over a hyphen
    held = abs(found - place) <= reach
    head['counted'] = (found, merged, held)       # for the page's own gap between its ledger lines: see LEDGER_CLOSE
    return found if held else place


def _ledger_gaps(staff: dict, above: bool, rows: list[float]) -> list[float]:
    """The gaps from the staff to its first ledger line and from each ledger line to the next, in staff spaces."""
    gaps, before = [], staff['rows'][0 if above else -1]
    for row in sorted(rows, reverse=above):
        gaps.append(abs(row - before) / staff['space'])
        before = row
    return gaps


def _dashes(layers: dict, head: dict, rows: list[float], space: float) -> bool:
    """True when the ledger lines of a head are dashes of one length, one over the other: each ends from 0.5 to
    LEDGER_CLOSE[4] staff spaces from the middle of the head at both sides, and their ends stand within LEDGER_CLOSE[5]
    staff spaces of each other. A slur or the line of a held syllable that was counted as a ledger line runs on."""
    free = layers['free']
    column = int(round(head['cx']))
    ends = []
    for row in rows:
        band = free[max(0, int(round(row)) - 2):int(round(row)) + 3].max(axis=0)
        sides = []
        for step in (-1, 1):
            at, gap = column, 0
            last = column
            while 0 <= at + step < len(band) and gap <= 2:
                at += step
                if band[at]:
                    last, gap = at, 0
                else:
                    gap += 1
            sides.append(abs(last - column) / space)
        if not all(0.5 <= side <= LEDGER_CLOSE[4] for side in sides):
            return False
        ends.append(sides)
    return all(max(side[index] for side in ends) - min(side[index] for side in ends) <= LEDGER_CLOSE[5] for index in (0, 1))


def close_ledgers(layers: dict, heads: list[dict]) -> None:
    """The heads beside the staff of a page whose ledger lines stand closer than its staff lines (see LEDGER_CLOSE): where
    the count of the lines was not trusted because the measured place is far from it, the count holds when the place is
    measured with the page's own gap."""
    if not LEDGER_CLOSE:
        return
    gaps = []
    for head in heads:
        counted = head.get('counted')
        if counted and counted[2] and not head['hollow'] and head['stems']:
            gaps += _ledger_gaps(layers['staves'][head['staff']], counted[0] > 0, counted[1])
    if len(gaps) < LEDGER_CLOSE[1]:
        return
    usual = float(np.median(gaps))
    if usual > LEDGER_CLOSE[0]:
        return
    for head in heads:
        counted = head.get('counted')
        if not counted or counted[2] or len(counted[1]) < 2:
            continue
        found, rows, _ = counted
        staff = layers['staves'][head['staff']]
        if any(abs(gap - usual) > LEDGER_CLOSE[2] for gap in _ledger_gaps(staff, found > 0, rows)):
            continue
        if abs(abs(found) - (4 + (abs(head['place']) - 4) / usual)) > LEDGER_CLOSE[3]:
            continue
        if _dashes(layers, head, rows, staff['space']):
            head['place'] = found


def _on_ledger(layers: dict, mark: dict) -> bool:
    """True when a mark beside the staff lies on a ledger line or hangs on one."""
    index = _staff_of(layers, mark['cx'], mark['cy'])
    if index is None:
        return False
    staff = layers['staves'][index]
    if abs(pitch_place(staff, mark['cy'])) <= 4.6:
        return False
    free, space = layers['free'], staff['space']
    reach = int(round(0.35 * space))
    if WINGS:
        row = _wings(layers, mark)
        if row is not None and mark['y0'] - 0.2 * space <= row <= mark['y1'] + 0.2 * space:
            return True
    for row in ledger_lines(layers, staff, mark):
        if not mark['y0'] - 0.2 * space <= row <= mark['y1'] + 0.2 * space:
            continue
        # The line goes on past the mark at both sides: the arc of a fermata is thick ink too, but it ends there.
        top, bottom = max(0, int(row) - 2), int(row) + 3
        left = free[top:bottom, max(0, mark['x0'] - reach):max(0, mark['x0'] - 1)].max(axis=0, initial=0)
        right = free[top:bottom, mark['x1'] + 2:mark['x1'] + reach + 1].max(axis=0, initial=0)
        if left.size and right.size and left.mean() >= 0.7 and right.mean() >= 0.7:
            return True
    return False


def _stem_leaves(mark: dict, way: str, far: float) -> bool:
    """Whether a head holds a stem that goes this way and ends at least this many pixels from its middle (see
    MIDDLE_LEAVES)."""
    return any(stem['direction'] == way and abs(stem['end'] - mark['cy']) >= far for stem in mark['stems'])


def _stem_stays(mark: dict, way: str, far: float) -> bool:
    """Whether a head holds a stem that goes this way and each such stem ends within this many pixels of its middle
    (see MIDDLE_OWN)."""
    ends = [abs(stem['end'] - mark['cy']) for stem in mark['stems'] if stem['direction'] == way]
    return bool(ends) and max(ends) < far


def _pair_sharp(layers: dict, marks: list[dict], space: float) -> None:
    """Two heads of two voices that touch, the upper one with its stem up at its right and the lower one with its
    stem down at its left. Several prints draw the flag of the lower note back up to its head, and the stem and the
    flag close a narrow wedge of paper under it: the four ways that leave the lower head then made it a sharp, and the
    head over it took the stem down through it as a second stem. Such a mark is the lower voice's head, with that stem;
    the head over it keeps its stem up (`_share_stems` parts the two).

    The lower head is filled and as large as the page's heads, and the head over it is a whole head with no head over
    it in its own columns: a piece of the rim of a half note, of a punch hole and of a mark by hand stood over such
    marks, and the crossbar of a letter under a chord whose heads the staff lines cut into pieces. (The flag of the
    upper note is read as a head at the end of its stem, beside it.) The heads the other way round (the upper head
    read as a sharp, its stem up taken by the head under it) were the flag over a head, a sharp of a key and a mark
    by hand on LitChoir's pages, and are not read."""
    side, over, apart, near, least, most, whole, column = PAIR_SHARP
    head_wide, head_high = layers['head']
    heads = [mark for mark in marks if mark['kind'] == 'head'
             and sorted(stem['direction'] for stem in mark['stems']) == ['down', 'up']
             and mark['x1'] - mark['x0'] + 1 >= whole * head_wide and mark['y1'] - mark['y0'] + 1 >= whole * head_high]
    for mark in marks:
        if mark['kind'] != 'sharp' or mark.get('whole_sign') or mark['hole'] >= HOLLOW:
            continue
        wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
        if not (least * head_wide <= wide <= most * head_wide and least * head_high <= high <= most * head_high):
            continue
        way = mark['ways'].get('down_left')
        if not way:
            continue
        for head in heads:
            if not (head['x0'] - side * space <= mark['x1'] and head['x1'] + side * space >= mark['x0']
                    and mark['y0'] - apart * space <= head['y1'] <= mark['y0'] + over * space and head['y0'] < mark['y0']):
                continue
            stem = next(stem for stem in head['stems'] if stem['direction'] == 'down')
            if abs(way['x'] - stem['x']) > near * space or abs(way['end'] - stem['end']) > near * space:
                continue
            up = next(stem for stem in head['stems'] if stem['direction'] == 'up')
            if any(other is not head and other['kind'] == 'head' and up['end'] < other['cy'] < head['cy']
                   and min(other['x1'], head['x1']) - max(other['x0'], head['x0']) + 1 >= column * (head['x1'] - head['x0'] + 1)
                   for other in marks):
                continue        # a head over it in its own columns, on its stem up: a piece of a column of heads
            mark['kind'] = 'head'
            mark['stems'] = [dict(stem, length=abs(mark['cy'] - stem['end']))]
            mark['pair_sharp'] = tuple(head[key] for key in ('x0', 'y0', 'x1', 'y1'))
            break


def _share_stems(marks: list[dict], space: float) -> None:
    """Heads of two voices that stand close share one line of ink: the stem of the upper voice goes up from the
    upper head, the stem of the lower voice goes down from the lower head. Followed from either head, the ink leads
    through the other head to both stems. So in a group of heads on one such line, with a stem up and a stem down,
    the upper heads keep the stem that goes up and the lower heads keep the stem that goes down. One head alone
    with two stems is a note that both voices sing: it keeps both."""
    heads = [mark for mark in marks if mark['kind'] == 'head' and mark['stems']]
    group = {id(mark): id(mark) for mark in heads}

    def find(key):
        while group[key] != key:
            group[key] = group[group[key]]
            key = group[key]
        return key

    blobs = {}
    for mark in heads:
        if mark['blob'] in blobs:
            group[find(id(mark))] = find(id(blobs[mark['blob']]))
        blobs[mark['blob']] = mark
    for mark in heads:
        for stem in mark['stems']:
            first, last = sorted((mark['cy'], stem['end']))
            for other in heads:
                if other is not mark and first < other['cy'] < last \
                        and other['x0'] - 0.3 * space <= stem['x'] <= other['x1'] + 0.3 * space:
                    group[find(id(mark))] = find(id(other))
    groups = {}
    for mark in heads:
        groups.setdefault(find(id(mark)), []).append(mark)
    for members in groups.values():
        if len(members) < 2 or {stem['direction'] for mark in members for stem in mark['stems']} != {'up', 'down'}:
            continue
        members.sort(key=lambda mark: mark['cy'])
        middle = (members[0]['cy'] + members[-1]['cy']) / 2
        centre = sum(mark['cx'] for mark in members) / len(members)
        for index, mark in enumerate(members):
            if abs(mark['cy'] - middle) <= 0.2 * space:
                # Two voices on one note stand side by side, with their stems on one line between them: the left
                # head has the stem that goes up, the right head the stem that goes down.
                keep = 'up' if mark['cx'] < centre else 'down'
                if MIDDLE_KIND and 0 < index < len(members) - 1 and not any(
                        other is not mark and abs(other['cy'] - mark['cy']) <= MIDDLE_KIND * space for other in members):
                    # The middle head of a column, with no head beside it, is no such note: a few pixels chose its
                    # stem. One stem carries heads of one length, so the head goes with the neighbour of its own kind
                    # (a filled head between a hollow head over it and a filled head under it is the lower voice's).
                    # The head of the other kind is a note with a stem of its own that leaves the column on its
                    # side: the loop of a flag at the end of a stem is a hollow mark too, and its stem is the other.
                    # Only kinds that are sure count: a worn filled head holds a speck of paper, and on such a print
                    # the share of paper does not part the heads (one of three filled heads had a speck of 0.11).
                    kinds = [True if other['hole'] >= MIDDLE_SURE[1] else False if other['hole'] < MIDDLE_SURE[0] else None
                             for other in (members[index - 1], mark, members[index + 1])]
                    if None not in kinds:
                        # The stem that the head takes leaves the column too: a short stroke at the neighbour of its
                        # own kind is the end of a bow that runs into the column (a tie into a chord read as its stem).
                        far = MIDDLE_LEAVES * space
                        if kinds[0] != kinds[1] == kinds[2] and _stem_leaves(members[index - 1], 'up', far) \
                                and not (MIDDLE_OWN and _stem_stays(members[index + 1], 'down', far)):
                            keep = 'down'
                        elif kinds[0] == kinds[1] != kinds[2] and _stem_leaves(members[index + 1], 'down', far) \
                                and not (MIDDLE_OWN and _stem_stays(members[index - 1], 'up', far)):
                            keep = 'up'
            else:
                keep = 'up' if mark['cy'] < middle else 'down'
            kept = [stem for stem in mark['stems'] if stem['direction'] == keep]
            # A head keeps a stem of the other direction when it has no stem of its own.
            mark['stems'] = kept or mark['stems']


def core_light(layers: dict, mark: dict) -> dict:
    """How light the middle of a mark is: {'light' (the share of its core that is paper in the ink mask), 'pale' (the
    grey of its core, from 0 for the page's ink to 1 for its paper)}. The core is an oval in the middle of the
    mark's box, CORE of its width and height; the rows of the staff lines are left out."""
    x0, x1, y0, y1 = mark['x0'], mark['x1'], mark['y0'], mark['y1']
    wide, high = x1 - x0 + 1, y1 - y0 + 1
    ys, xs = np.mgrid[0:high, 0:wide]
    core = ((xs - (wide - 1) / 2) / (CORE * wide / 2)) ** 2 + ((ys - (high - 1) / 2) / (CORE * high / 2)) ** 2 <= 1
    core &= layers['lines'][y0:y1 + 1, x0:x1 + 1] == 0
    staff = _staff_of(layers, mark['cx'], mark['cy'])
    if staff is not None:
        half = layers['staves'][staff]['thick'] / 2 + 1
        for row in layers['staves'][staff]['rows']:
            core[max(0, int(row - half) - y0):max(0, int(row + half) + 1 - y0)] = False
    if core.sum() < 4:
        return {'light': 0.0, 'pale': 0.0}
    if 'levels' not in layers:
        grey, ink = layers['grey'], layers['ink']
        layers['levels'] = (float(np.percentile(grey[ink > 0][::7], 25)), float(np.median(grey[::9, ::9])))
    dark, paper = layers['levels']
    grey = layers['grey'][y0:y1 + 1, x0:x1 + 1][core].astype(float)
    return {'light': float((layers['ink'][y0:y1 + 1, x0:x1 + 1][core] == 0).mean()),
            'pale': float(np.clip((grey.mean() - dark) / max(1.0, paper - dark), 0, 1)),
            'pale90': float(np.clip((np.percentile(grey, 90) - dark) / max(1.0, paper - dark), 0, 1))}


def _rim(layers: dict, mark: dict) -> float:
    """The share of the rim of a mark's hole that is the mark's own ink. A hollow head has its own ink all around its
    hole. Paper that is closed in between a beam, a stem and a staff line has the staff line at one side, and the
    staff line is not the mark's ink."""
    y0, y1, x0, x1 = max(0, mark['y0'] - 2), mark['y1'] + 3, max(0, mark['x0'] - 2), mark['x1'] + 3
    hole = layers['holes'][y0:y1, x0:x1]
    if not hole.any():
        return 0.0
    ring = cv2.dilate(hole, np.ones((3, 3), np.uint8)) & (1 - hole)
    own = layers['ink'][y0:y1, x0:x1] & (1 - layers['lines'][y0:y1, x0:x1])
    return float((ring & own).sum()) / max(1, int(ring.sum()))


def _cell(layers: dict, mark: dict) -> bool:
    """Is the hole of a mark paper between two upright strokes (see CELL)? At the left and at the right of the hole, in
    its middle rows, the ink is thin, and each of the two strokes goes on past the hole, upward or downward."""
    space = layers['space']
    y0, y1, x0, x1 = max(0, mark['y0'] - 2), mark['y1'] + 3, max(0, mark['x0'] - 2), mark['x1'] + 3
    hole = layers['holes'][y0:y1, x0:x1]
    if not hole.any():
        return False
    ink = layers['ink']
    rows = np.nonzero(hole.any(axis=1))[0]
    top, bottom = int(rows.min()), int(rows.max())
    most, on = CELL[0] * space, int(round(CELL[1] * space))
    sides = {-1: [], 1: []}
    for row in range(int(top + 0.3 * (bottom - top)), int(top + 0.7 * (bottom - top)) + 1):
        columns = np.nonzero(hole[row])[0]
        if not len(columns):
            continue
        for way, column in ((-1, x0 + int(columns.min()) - 1), (1, x0 + int(columns.max()) + 1)):
            wide = 0
            while 0 <= column + way * wide < ink.shape[1] and ink[y0 + row, column + way * wide] and wide <= 2 * most:
                wide += 1
            sides[way].append((wide, column + way * (wide // 2)))
    for way in (-1, 1):
        if not sides[way]:
            return False
        wide, column = sorted(sides[way])[len(sides[way]) // 2]
        if wide == 0 or wide > most:
            return False
        # The stroke goes on past the hole: ink in its column for all of the rows over the hole, or under it.
        over = ink[max(0, y0 + top - on):y0 + top, max(0, column - 1):column + 2].any(axis=1)
        under = ink[y0 + bottom + 1:y0 + bottom + 1 + on, max(0, column - 1):column + 2].any(axis=1)
        if not ((len(over) == on and over.all()) or (len(under) == on and under.all())):
            return False
    return True


def _places(staff: dict, mark: dict) -> dict:
    """Other measures of a mark's place on its staff, for the record: 'mass' (the middle of its ink), 'bare' (the
    middle of its ink outside the rows of the staff lines), 'box' (the middle of its box), 'top' and 'bottom' (its
    edges)."""
    profile = np.asarray(mark['profile'], float)
    rows = mark['y0'] + np.arange(len(profile))
    half = staff['thick'] / 2 + 0.5
    off = np.ones(len(profile), bool)
    for line in staff['rows']:
        off &= np.abs(rows - line) > half
    bare = float((rows[off] * profile[off]).sum() / profile[off].sum()) if profile[off].sum() > 0 else mark['cy']
    return {'mass': pitch_place(staff, mark['cy']), 'bare': pitch_place(staff, bare),
            'box': pitch_place(staff, (mark['y0'] + mark['y1']) / 2), 'top': pitch_place(staff, mark['y0']),
            'bottom': pitch_place(staff, mark['y1']), 'thick': staff['thick'] / staff['space']}


def _fat(layers: dict, mark: dict) -> dict:
    """How fat the stroke of a mark is, for the record: 'fat' (the widest disc that fits in its thick ink, as a
    diameter in staff spaces), 'area' (its thick ink in staff spaces squared) and 'long' (the length of its box's
    diagonal in staff spaces)."""
    space = layers['space']
    y0, y1, x0, x1 = max(0, mark['y0'] - 1), mark['y1'] + 2, max(0, mark['x0'] - 1), mark['x1'] + 2
    part = np.ascontiguousarray(layers['thick'][y0:y1, x0:x1])
    if not part.any():
        return {'fat': 0.0, 'area': 0.0, 'long': 0.0}
    far = cv2.distanceTransform(np.pad(part, 1), cv2.DIST_L2, 3)
    return {'fat': float(2 * far.max() / space), 'area': float(part.sum() / space ** 2),
            'long': float(np.hypot(mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1) / space)}


SOLID_SPECK = (0.03, 0.12, 0.15, 1.2, 0.33)
#                      a print that pressed the ink out of a filled head leaves a speck of closed paper in it, and the
#                      rows of the speck were taken for rows of the room of the flag's loop beside the head
#                      (SOLID_LOOP): the solid ink was then no head high. The closed paper of such a mark is two
#                      pieces, a speck under the first number of the box of a head of the page and at most the second
#                      number of the room, and a room of at least the third number of that box; the mark is at most
#                      the fourth number of a head wide, and the speck lies the fifth number of a head's height or
#                      more from the rows of the room, inside the head (a speck between a head, its stem and a staff
#                      line lies at the room: 0.21 at most). A rule for one case, one head of a clean score. None: off


def _room_alone(paper: np.ndarray, wide: float, high: float) -> np.ndarray:
    """The closed paper of a mark without the speck of a filled head beside the room of its flag (SOLID_SPECK)."""
    if not SOLID_SPECK or paper.shape[1] > SOLID_SPECK[3] * wide:
        return paper
    count, labels, stats, _ = cv2.connectedComponentsWithStats(paper.astype(np.uint8), connectivity=4)
    if count != 3:
        return paper
    speck, room = sorted((1, 2), key=lambda number: stats[number][4])
    if stats[speck][4] >= SOLID_SPECK[0] * wide * high or stats[speck][4] > SOLID_SPECK[1] * stats[room][4] \
            or stats[room][4] < SOLID_SPECK[2] * wide * high:
        return paper
    apart = max(stats[room][1] - (stats[speck][1] + stats[speck][3]), stats[speck][1] - (stats[room][1] + stats[room][3]))
    if apart < SOLID_SPECK[4] * high:
        return paper
    return paper & (labels == room)


def _flag_loop(layers: dict, marks: list[dict], mark: dict) -> bool:
    """True when a hollow mark is the loop of a printed flag, not a head. The flag of a printed eighth note comes back
    toward its head, and the flag, the stem and the staff lines close in small rooms at the right side of the stem.
    The note itself is a filled head as large as the heads of the page, its stem has the flag at its far end, and
    the room has no stem of its own: the upright ink that leaves it is that stem, or it goes to that head."""
    space = layers['space']
    wide, high = layers['head']
    for other in marks:
        if other is mark or other['kind'] != 'head' or (other['hole'] >= HOLLOW and other.get('solid_cy') is None):
            continue
        if abs(other['cx'] - mark['cx']) > 2 * space or abs(other['cy'] - mark['cy']) > 6 * space:
            continue
        if other['x1'] - other['x0'] + 1 < 0.75 * wide or other['y1'] - other['y0'] + 1 < 0.75 * high:
            continue
        for stem in other['stems']:
            side = -1 if stem['direction'] == 'up' else 1
            if abs(stem['x'] - mark['x0']) > 0.35 * space or (mark['cy'] - other['cy']) * side < 0.7 * space \
                    or (mark['cy'] - stem['end']) * side > 0.8 * space:
                continue
            own = True
            for way in mark['stems']:
                same = way['direction'] == stem['direction'] and abs(way['x'] - stem['x']) <= 0.35 * space \
                    and abs(way['end'] - stem['end']) <= 0.5 * space
                first, last = sorted((mark['cy'], way['end']))
                to_head = other['x0'] - 0.35 * space <= way['x'] <= other['x1'] + 0.35 * space \
                    and first - 0.3 * space <= other['cy'] <= last + 0.3 * space
                own = own and (same or to_head)
            if not own:
                continue
            staff = _staff_of(layers, other['cx'], other['cy'])
            if staff is None:
                continue
            pieces = tail_marks(layers, dict(other, staff_ref=layers['staves'][staff]), stem)
            # A printed flag is thick where it begins, at the very end of its stem. A hollow head beside the stem of
            # another voice is ink at the right side of that stem too, but it lies before the end.
            if any(piece['right'] and piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6 and piece['back'] >= FLAG_BACK
                   and piece['from_end'] <= FLAG_END for piece in pieces):
                return True
    return False


def _two_heads(layers: dict, mark: dict, stacked: bool = False) -> list[dict] | None:
    """The two heads of a mark that has a stem up at its right and a stem down at its left, when the mark is too
    large for one head. Two voices a second apart: a hand draws the lower head at the left with its stem down and
    the upper head at the right with its stem up, and the two strokes run into each other. Two voices a third
    apart: the two strokes touch, one over the other. The mark is cut at its narrowest place, across or down, and
    each head keeps its own stem. A head of the usual size with two stems is one note that both voices sing."""
    space = layers['space']
    wide, high = layers['head']
    ups = [stem for stem in mark['stems'] if stem['direction'] == 'up']
    downs = [stem for stem in mark['stems'] if stem['direction'] == 'down']
    if len(ups) != 1 or len(downs) != 1 or mark['hole'] >= HOLLOW:
        return None
    own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
    mask = layers['thick'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1] > 0
    holes = layers['holes'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1] > 0
    window = max(3, int(round(0.2 * space)) | 1)
    if own_wide >= TWO_HEADS[0] * wide and not (stacked and own_high >= TWO_HEADS[1] * high):
        if not (downs[0]['x'] <= mark['x0'] + 0.35 * own_wide and ups[0]['x'] >= mark['x1'] - 0.35 * own_wide):
            return None
        smooth = np.convolve(mask.sum(axis=0).astype(float), np.ones(window) / window, mode='same')
        first, last = int(0.3 * own_wide), int(0.7 * own_wide)
        cut = first + int(np.argmin(smooth[first:last + 1]))
        parts = [(_mark(mask[:, :cut], holes[:, :cut], mark['x0'], mark['y0'], mark['blob']), downs),
                 (_mark(mask[:, cut:], holes[:, cut:], mark['x0'] + cut, mark['y0'], mark['blob']), ups)]
    elif own_high >= TWO_HEADS[1] * high:
        smooth = np.convolve(mask.sum(axis=1).astype(float), np.ones(window) / window, mode='same')
        first, last = int(0.3 * own_high), int(0.7 * own_high)
        cut = first + int(np.argmin(smooth[first:last + 1]))
        parts = [(_mark(mask[:cut], holes[:cut], mark['x0'], mark['y0'], mark['blob']), ups),
                 (_mark(mask[cut:], holes[cut:], mark['x0'], mark['y0'] + cut, mark['blob']), downs)]
    else:
        return None
    out = []
    for part, stems in parts:
        if part is None or part['area'] < SMALL * space * space or part['x1'] - part['x0'] + 1 < HEAD_WIDE[0] * space \
                or part['y1'] - part['y0'] + 1 < HEAD_HIGH[0] * space:
            return None
        out.append(dict(part, stems=stems, kind='head', ways=mark['ways']))
    return out


def _side_two(layers: dict, mark: dict) -> list[dict] | None:
    """The two heads of a mark that one stem line goes through, up and down (see SIDE_TWO): [the left head with the
    stem up, the right head with the stem down]. Two voices that sing one note with different lengths stand side by
    side, the upper voice at the left, and their stems are one line between the two heads: the strokes that leave
    the mark at all four corners made it a sharp. None when the mark is no such mark."""
    space = layers['space']
    wide, high = layers['head']
    ways = mark.get('ways')
    if not ways or not all(is_stem(way, space) for way in ways.values()):
        return None
    own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
    if not (SIDE_TWO[0] * wide <= own_wide <= SIDE_TWO[1] * wide and own_high <= SIDE_TWO[2] * high):
        return None
    columns = [way['mid'] for way in ways.values()]
    if max(columns) - min(columns) > SIDE_TWO[3] * space:
        return None
    column = float(np.mean(columns))
    if not mark['x0'] + SIDE_TWO[4] * own_wide <= column <= mark['x1'] - SIDE_TWO[4] * own_wide:
        return None
    up = max((ways['up_left'], ways['up_right']), key=lambda way: way['length'])
    down = max((ways['down_left'], ways['down_right']), key=lambda way: way['length'])
    return _side_parts(layers, mark, column, up, down)


def _side_parts(layers: dict, mark: dict, column: float, up: dict, down: dict, trim: bool = False, **tag) -> list[dict] | None:
    """The two heads of a pair at one stem line (see SIDE_TWO), cut at the column of the stem line: [the left head
    with the stem up, the right head with the stem down], or None where a part holds no head. With trim, the rows of
    a part that hold only the root of the other head's stem (at the top of the right part, at the bottom of the left
    one) are taken off it: the two heads of a second stand at two heights."""
    space = layers['space']
    wide, high = layers['head']
    cut = int(round(column)) - mark['x0']
    mask = layers['thick'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1] > 0
    holes = layers['holes'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1] > 0
    top, bottom = 0, mask.shape[0]
    if trim:
        rows = mask[:, cut:].sum(axis=1)
        while top < bottom and rows[top] <= SIDE_HEAD[1] * space:
            top += 1
        rows = mask[:, :cut].sum(axis=1)
        while bottom > 0 and rows[bottom - 1] <= SIDE_HEAD[1] * space:
            bottom -= 1
    trimmed = (_mark(mask[:bottom, :cut], holes[:bottom, :cut], mark['x0'], mark['y0'], mark['blob']),
               _mark(mask[top:, cut:], holes[top:, cut:], mark['x0'] + cut, mark['y0'] + top, mark['blob']))
    out = []
    for side, (part, stem) in enumerate(((_mark(mask[:, :cut], holes[:, :cut], mark['x0'], mark['y0'], mark['blob']), up),
                                         (_mark(mask[:, cut:], holes[:, cut:], mark['x0'] + cut, mark['y0'], mark['blob']), down))):
        if part is None or part['area'] < SIDE_TWO[5] * wide * high or part['x1'] - part['x0'] + 1 < HEAD_WIDE[0] * space \
                or part['y1'] - part['y0'] + 1 < HEAD_HIGH[0] * space:
            return None
        own = np.pad(mask[part['y0'] - mark['y0']:part['y1'] - mark['y0'] + 1, part['x0'] - mark['x0']:part['x1'] - mark['x0'] + 1], 1)
        if 2 * float(cv2.distanceTransform(own.astype(np.uint8), cv2.DIST_L2, 5).max()) < SIDE_TWO[6] * high:
            return None
        if trim and trimmed[side] is not None:
            part = dict(trimmed[side])
            # The paper that the two heads close with the stem line lies where the two heads meet: over the middle
            # of the lower head at the right, under the middle of the upper head at the left. The inside of a head
            # lies in its middle.
            box = (slice(part['y0'] - mark['y0'], part['y1'] - mark['y0'] + 1), slice(part['x0'] - mark['x0'], part['x1'] - mark['x0'] + 1))
            inside = (mask[box] & holes[box]).astype(np.uint8)
            count, labels = cv2.connectedComponents(inside, connectivity=8)
            keep = np.zeros(inside.shape, dtype=bool)
            for label in range(1, count):
                cell = labels == label
                away = (part['cy'] - (part['y0'] + float(np.nonzero(cell)[0].mean()))) * (1 if side else -1)
                if away < SIDE_HEAD[3] * space:
                    keep |= cell
            part['hole'] = float(keep.sum()) / part['area']
            part['hole_cy'] = float(part['y0'] + np.nonzero(keep)[0].mean()) if keep.any() else None
        out.append(dict(part, stems=[stem], kind='head', ways=mark['ways'], side_two=True, **tag))
    pair = {'x0': mark['x0'], 'x1': mark['x1'], 'y0': mark['y0'], 'y1': mark['y1'], 'cx': (mark['x0'] + mark['x1']) / 2,
            'hole': max(part['hole'] for part in out)}
    for part in out:
        part['pair'] = pair
    return out


def _side_head(layers: dict, mark: dict) -> list[dict] | None:
    """The two heads of a mark that was read as one head, where its stem up and its stem down are one line through
    its middle (see SIDE_HEAD): [the left head with the stem up, the right head with the stem down], or None."""
    space = layers['space']
    wide, high = layers['head']
    ways = mark.get('ways') or {}
    up = ways.get('up_right')
    if not is_stem(up, space):
        return None
    downs = [ways[name] for name in ('down_left', 'down_right')
             if is_stem(ways.get(name), space) and abs(ways[name]['mid'] - up['mid']) <= SIDE_HEAD[0] * space]
    if not downs:
        return None
    down = max(downs, key=lambda way: way['length'])
    own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
    if not (SIDE_TWO[0] * wide <= own_wide <= SIDE_TWO[1] * wide and own_high <= SIDE_TWO[2] * high):
        return None
    column = (up['mid'] + down['mid']) / 2
    if not mark['x0'] + SIDE_TWO[4] * own_wide <= column <= mark['x1'] - SIDE_TWO[4] * own_wide:
        return None
    parts = _side_parts(layers, mark, column, up, down, trim=True, side_head=True)
    if parts is not None and SIDE_HEAD[2] is not None and not (
            parts[1]['y0'] - parts[0]['y0'] >= SIDE_HEAD[2] * space and parts[1]['y1'] - parts[0]['y1'] >= SIDE_HEAD[2] * space):
        parts = None
    if parts is not None and SIDE_SEEN is not None:
        SIDE_SEEN.append({'box': [mark['x0'], mark['y0'], mark['x1'], mark['y1']], 'column': column, 'hole': mark['hole'],
                          'parts': [[part['x0'], part['y0'], part['x1'], part['y1'], part['cx'], part['cy'], part['hole']]
                                    for part in parts], 'space': space, 'head': [wide, high]})
    return parts


def _glued_two(layers: dict, mark: dict) -> list[dict] | None:
    """The two heads of a mark that read_symbols left without a head (see GLUED_TWO). Two voices a third apart print
    their heads one over the other, the upper head with its stem up at the right and the lower one with its stem down
    at the left, and on a heavy print the two touch: the mark is then higher than a head, or the stem of the next note
    that stands close leaves it too, and it was read as a beam. Paper that the two heads close with a staff line is no
    hole of either head. None when the mark is no such mark."""
    space = layers['space']
    wide, high = layers['head']
    ways = mark.get('ways')
    if not ways or not (is_stem(ways['up_right'], space) and is_stem(ways['down_left'], space)):
        return None
    own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
    if mark['kind'] is None and not (HEAD_WIDE[0] * space <= own_wide <= HEAD_WIDE[1] * space
                                     and own_high > HEAD_HIGH[1] * space and not (WORD_MARKS and _in_words(layers, mark))):
        return None
    if mark['area'] < GLUED_TWO[0] * wide * high:
        return None
    # A bar line or a stem that runs through the mark makes a box with the staff lines, and the box is no head: the
    # upright ink leaves the mark up and down in one column.
    for up, down in (('up_right', 'down_right'), ('up_left', 'down_left')):
        if ways[up] and ways[down] and min(ways[up]['past'], ways[down]['past']) >= GLUED_THROUGH[0] * space \
                and abs(ways[up]['x'] - ways[down]['x']) <= GLUED_THROUGH[1] * space:
            return None
    # One over the other first: the stem of a neighbour can make the mark as wide as it is high.
    parts = _two_heads(layers, dict(mark, kind='head', stems=[ways['up_right'], ways['down_left']], hole=0.0), True)
    if not parts or any(not GLUED_TWO[1] * wide * high <= part['area'] <= GLUED_TWO[2] * wide * high
                        or part['y1'] - part['y0'] + 1 < GLUED_TWO[3] * high for part in parts):
        return None
    # The paper that the two heads close between them (with a staff line, a stem or a sign) reaches the cut.
    box = (slice(mark['y0'], mark['y1'] + 1), slice(mark['x0'], mark['x1'] + 1))
    inside = ((layers['thick'][box] > 0) & (layers['holes'][box] > 0)).astype(np.uint8)
    count, labels = cv2.connectedComponents(inside, connectivity=8)
    upper, lower = parts      # cut across: the upper and the lower head; cut down: the left and the right head
    across = lower['x0'] <= upper['x1']
    for part in parts:
        own = np.zeros_like(inside, dtype=bool)
        own[part['y0'] - mark['y0']:part['y1'] - mark['y0'] + 1, part['x0'] - mark['x0']:part['x1'] - mark['x0'] + 1] = True
        keep = np.zeros_like(own)
        for label in range(1, count):
            cell = labels == label
            ys, xs = np.nonzero(cell)
            if across:
                meets = ys.min() <= upper['y1'] - mark['y0'] + 1 and ys.max() >= lower['y0'] - mark['y0'] - 1
            else:
                meets = xs.min() <= upper['x1'] - mark['x0'] + 1 and xs.max() >= lower['x0'] - mark['x0'] - 1
            if not meets:
                keep |= cell
        hole = keep & own
        # A head is round and full: a circle of ink half as high as the page's heads fits in it. The pieces of staff
        # lines, of a sharp or of a clef are thin.
        ink = (layers['thick'][part['y0']:part['y1'] + 1, part['x0']:part['x1'] + 1] > 0) \
            & ~(layers['holes'][part['y0']:part['y1'] + 1, part['x0']:part['x1'] + 1] > 0)
        if 2 * float(cv2.distanceTransform(np.pad(ink, 1).astype(np.uint8), cv2.DIST_L2, 5).max()) < GLUED_FAT * high:
            return None
        part['hole'] = float(hole.sum()) / part['area']
        part['hole_cy'] = float(mark['y0'] + np.nonzero(hole)[0].mean()) if hole.any() else None
        part['glued_two'] = True
    return parts


def _glued_sign(layers: dict, mark: dict) -> list[dict] | None:
    """The two parts of a mark that is the right stroke of a sharp and the head that the sharp touches (see
    SIGN_GLUED): [what is left of the sign, the head]. None when the mark is no such mark."""
    space = layers['space']
    wide, high = layers['head']
    own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
    if not (SIGN_GLUED[0] * wide <= own_wide <= SIGN_GLUED[1] * wide and own_high <= SIGN_GLUED[2] * high):
        return None
    ways = {name: _way(layers, mark, name == 'up', False) for name in ('up', 'down')}
    if not all(way and SIGN_GLUED[3] * space <= way['past'] <= SIGN_GLUED[4] * space
               and way['slim'] >= SHARP_SLIM * space for way in ways.values()):
        return None
    stroke = (ways['up']['mid'] + ways['down']['mid']) / 2
    if abs(ways['up']['mid'] - ways['down']['mid']) > 0.25 * space or stroke > mark['x0'] + 0.35 * own_wide:
        return None
    # A sharp has two strokes: the other one stands at the left of this one, as high as the mark, and it ends as
    # this one does (a bar line goes on).
    ink = layers['bare']
    top, bottom = max(0, mark['y0'] - int(SIGN_GLUED[4] * space) - 2), min(ink.shape[0], mark['y1'] + int(SIGN_GLUED[4] * space) + 3)
    other = False
    for x in range(max(0, int(stroke - SIGN_GLUED[10] * space)), max(0, int(stroke - SIGN_GLUED[3] * space))):
        column = ink[top:bottom, x] > 0
        if not column[0] and not column[-1] and column[mark['y0'] - top:mark['y1'] + 1 - top].mean() >= 0.9:
            other = True
            break
    if not other:
        return None
    mask = layers['thick'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1] > 0
    holes = layers['holes'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1] > 0
    first = max(1, int(round(stroke - mark['x0'])) + 1)
    last = min(own_wide - 2, first + int(round(SIGN_GLUED[5] * space)))
    if last <= first:
        return None
    cut = first + int(np.argmin(mask[:, first:last + 1].sum(axis=0)))
    # The room between the stroke and the round side of the head is closed in: it is no hole of the head.
    inside = holes[:, cut:].copy()
    inside[:, :int(0.35 * (own_wide - cut))] = False
    head = _mark(mask[:, cut:], inside, mark['x0'] + cut, mark['y0'], mark['blob'])
    sign = _mark(mask[:, :cut], holes[:, :cut], mark['x0'], mark['y0'], mark['blob'])
    if head is None or sign is None:
        return None
    part_wide, part_high = head['x1'] - head['x0'] + 1, head['y1'] - head['y0'] + 1
    if not (SIGN_GLUED[6] * wide <= part_wide <= SIGN_GLUED[7] * wide and SIGN_GLUED[6] * high <= part_high <= SIGN_GLUED[7] * high
            and head['area'] >= SIGN_GLUED[8] * part_wide * part_high):
        return None
    stems = [_way(layers, head, up, True) for up in (True, False)]
    if not any(is_stem(way, space) and way['past'] >= SIGN_GLUED[9] * space for way in stems):
        return None
    head['glued'] = True
    return [sign, head]


SIGN_WHOLE = ((1.85, 2.6, 1.2, 2.7), (0.2, 1.0), (0.4, 0.85), (0.3, 0.95, 0.35), (1.0, 4.0), (0.8, 1.3, 0.7, 0.5))
#   a heavy sharp whose bars are as thick as a head is one mark with the head that it touches, the whole of it, and
#   such a mark is no head for its size: it was read as a beam, for the stroke and the stem that leave it downwards at
#   its two ends, or as nothing, and the note was lost (SIGN_GLUED cuts the mark that the right stroke alone makes
#   with the head). None: off. The mark is [0][0] to [0][1] times as wide as the heads of the page and [0][2] to
#   [0][3] times as high. From its left half one stroke leaves it upwards and another downwards, each [1][0] to
#   [1][1] staff spaces past the mark and slim there: the two strokes of a sharp, of which the right one stands
#   higher (a stem is longer, and the strokes of a natural stand the other way round). The stroke that goes up stands
#   [2][0] to [2][1] staff spaces right of the other. The head has a stem that goes [4][0] to [4][1] staff spaces past
#   the mark (a bar line goes further): down, [3][0] to [3][1] staff spaces right of the sharp's right stroke, and
#   the head begins at that stem; or up, in the last [3][2] staff spaces of the mark, with no stem down, and the head
#   begins where the mark is narrowest between the stroke and the stem. The paper that the sharp closes in with the
#   stem and the head reaches the cut and is no part of the head. The head is [5][0] to [5][1] times as wide as the
#   heads of the page, [5][2] to [5][1] times as high, has ink in [5][3] of its box and holds a circle of ink as a head
#   does (GLUED_FAT). The head keeps the box of its sharp ('sharp'), and scorereader.signs gives it that sharp
#   (signs.WHOLE_SIGN): the bars can hide the top of a stroke, and the two strokes then make no pair.
#   The census, at the reader's own step: 243 marks of LitChoir's scan pages are larger than a head with such two
#   strokes at the left; the 132 with a stem at the right were looked at. Eleven are a sharp and its head, on five
#   prints (their strokes stand 0.48 to 0.78 staff spaces apart and go 0.24 to 0.71 past the mark; the marks are 2.0 to
#   2.4 heads wide), and the rule cuts these eleven and no other mark. The others: a treble clef (its strokes stand
#   0.34 apart), the sharps of a key signature that touch each other (thin: a circle of 0.46 of a head's height
#   fits, against 0.62 or more in the eleven heads; the share of the box does not part them, 0.57 against 0.58), the
#   end of a staff with its bar lines (a "stem" of 13 staff spaces), hatching and letters by hand. The eleven
#   heads are filled, and the circle of ink refuses a hollow one: a rule for filled heads.

def _glued_whole(layers: dict, mark: dict) -> list[dict] | None:
    """The two parts of a mark that is a heavy sharp, the whole of it, and the head that the sharp touches (see
    SIGN_WHOLE): [the sharp, the head]. None when the mark is no such mark."""
    if mark.get('glued'):
        return None
    space = layers['space']
    wide, high = layers['head']
    size, past, apart, at, long, part = SIGN_WHOLE
    own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
    if not (size[0] * wide <= own_wide <= size[1] * wide and size[2] * high <= own_high <= size[3] * high):
        return None
    up, down = _way(layers, mark, True, False), _way(layers, mark, False, False)
    if not all(way and past[0] * space <= way['past'] <= past[1] * space and way['slim'] >= past[0] * space
               for way in (up, down)):
        return None
    if not apart[0] * space <= up['mid'] - down['mid'] <= apart[1] * space:
        return None
    stems = {name: _way(layers, mark, name == 'up', True) for name in ('up', 'down')}
    fits = {name: bool(is_stem(way, space) and long[0] * space <= way['past'] <= long[1] * space)
            for name, way in stems.items()}
    mask = layers['thick'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1] > 0
    holes = layers['holes'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1] > 0
    if fits['down'] and at[0] * space <= stems['down']['mid'] - up['mid'] <= at[1] * space:
        # The head begins at its stem. The bars of the sharp reach over the stem: the rows of the head are those
        # of the mark past them.
        cut = int(stems['down']['mid']) - mark['x0'] - max(1, int(round(0.08 * space)))
        clear = cut + int(round(0.45 * space))
        way = 'down'
    elif fits['up'] and not is_stem(stems['down'], space) and stems['up']['mid'] >= mark['x1'] - at[2] * space:
        first, last = int(up['mid']) - mark['x0'] + 2, int(stems['up']['mid'] - mark['x0'] - 0.6 * wide)
        if last <= first:
            return None
        cut = clear = first + int(np.argmin(mask[:, first:last + 1].sum(axis=0)))
        way = 'up'
    else:
        return None
    if cut < 1 or clear >= own_wide - 2:
        return None
    # The paper that the sharp closes in with the stem and the head reaches the cut: it is no part of the head and
    # no hole of it.
    count, labels = cv2.connectedComponents((mask & holes).astype(np.uint8), connectivity=8)
    room = np.zeros_like(mask)
    for label in range(1, count):
        cell = labels == label
        if int(np.nonzero(cell.any(axis=0))[0][0]) <= cut + 1:
            room |= cell
    own = mask & ~room
    rows = np.nonzero(own[:, clear:].any(axis=1))[0]
    if not len(rows):
        return None
    top, bottom = int(rows[0]), int(rows[-1])
    inside = (holes & ~room)[top:bottom + 1, cut:]
    if way == 'up':
        # The room between the stroke and the round side of the head is closed in: it is no hole of the head.
        inside[:, :int(0.35 * (own_wide - cut))] = False
    head = _mark(own[top:bottom + 1, cut:], inside, mark['x0'] + cut, mark['y0'] + top, mark['blob'])
    sign = _mark(mask[:, :cut], holes[:, :cut], mark['x0'], mark['y0'], mark['blob'])
    if head is None or sign is None:
        return None
    part_wide, part_high = head['x1'] - head['x0'] + 1, head['y1'] - head['y0'] + 1
    if not (part[0] * wide <= part_wide <= part[1] * wide and part[2] * high <= part_high <= part[1] * high
            and head['area'] >= part[3] * part_wide * part_high):
        return None
    # A head is round and full (see GLUED_FAT): the strokes and the bars of a second sharp are thin.
    ink = (own & ~holes)[top:bottom + 1, cut:]
    if 2 * float(cv2.distanceTransform(np.pad(ink, 1).astype(np.uint8), cv2.DIST_L2, 5).max()) < GLUED_FAT * high:
        return None
    head['glued'] = way
    head['sharp'] = [sign['x0'], sign['y0'], sign['x1'], sign['y1']]
    sign['whole_sign'] = True
    return [sign, head]


def _stem_ink(layers: dict, stem: dict, ovals: list[dict]) -> int:
    """How many rows of a stem hold ink of its own: the rows from the first oval (the stem's own head) to the stem's
    end, outside every oval and outside the staff lines, with ink in the stem's column (see WHOLE_STACK)."""
    ink, space = layers['ink'], layers['space']
    reach = max(2, int(round(0.08 * space)))
    lines = [row for staff in layers['staves'] for row in staff['rows']]
    thick = max(staff['thick'] for staff in layers['staves'])
    up = stem['direction'] == 'up'
    first, last = sorted((int(round(stem['end'])), int(ovals[0]['y0'] if up else ovals[0]['y1'])))
    column = int(round(stem['x']))
    count = 0
    for row in range(max(0, first), min(ink.shape[0] - 1, last) + 1):
        if any(oval['y0'] - 1 <= row <= oval['y1'] + 1 for oval in ovals) \
                or any(abs(row - line) <= thick / 2 + 1.5 for line in lines):
            continue
        count += bool(ink[row, max(0, column - reach):column + reach + 1].any())
    return count


HEADS_MEET = (0.2, 0.15, 0.85, 1.25)   # two filled heads a third apart at one stem close a speck of paper where they
#                    meet, between the heads and the stem, and the speck was read as the inside of a half note. The piece
#                    of ink is cut evenly into its heads, so the speck lies at the cut and beside the stem: a part whose
#                    inside has its middle at most [0] staff spaces from the edge where the next part of its piece begins,
#                    a filled one, and [1] of the part's width or more beside the part's middle, at the side of a stem of
#                    the part, is filled too. The inside of a half note lies in the middle of its head. (A census of every
#                    hollow part with a filled part of its piece that begins where it ends, at this step, on LitChoir's
#                    scan pages, 1,103: the insides of 55 lie that near the cut, and 14 of them that far beside the
#                    middle. Seven of the 14 have a stem at that side, all on clean copies and each the speck of such a
#                    pair; the others are three numbers of time signatures, a clip, a blot and a stack of whole notes
#                    by hand, and one such pair whose stem the reader finds only later. The insides in the middle are
#                    half notes by hand and on a thick copy whose piece was cut at a wrong row, and signs.) And where the
#                    speck was made a part of its own: a hollow part between two filled parts of its piece, in its
#                    column and at its stem, whose middles are [2] to [3] staff spaces apart with the inside midway, is
#                    no head. Three heads a second apart do not stand in one column (one place on LitChoir's pages; the
#                    cell of a sharp and the bowl of a flat have such neighbours and no stem). None: off


def _heads_meet(layers: dict, marks: list[dict], limit: float) -> dict[int, bool]:
    """The hollow parts whose inside is the paper where two filled heads of their piece meet (HEADS_MEET), by id():
    True where the part is a filled head itself, False where it is no head."""
    pieces: dict[int, list[dict]] = {}
    for mark in marks:
        if mark['kind'] == 'head':
            pieces.setdefault(mark['blob'], []).append(mark)
    found = {}
    for parts in pieces.values():
        if len(parts) < 2:
            continue
        for mark in parts:
            if mark['hole'] < limit or mark['hole_cy'] is None or not mark['stems']:
                continue
            staff = _staff_of(layers, mark['cx'], mark['cy'])
            space = layers['staves'][staff]['space'] if staff is not None else layers['space']
            row, wide = mark['hole_cy'], mark['x1'] - mark['x0'] + 1
            filled = [other for other in parts if other is not mark and other['hole'] < limit
                      and min(other['x1'], mark['x1']) - max(other['x0'], mark['x0']) + 1
                      >= 0.5 * min(other['x1'] - other['x0'] + 1, wide)]
            shared = [other for other in filled if any(own['direction'] == stem['direction'] and abs(own['x'] - stem['x']) <= 2
                                                       for own in mark['stems'] for stem in other['stems'])]
            if any(HEADS_MEET[2] * space <= under['cy'] - over['cy'] <= HEADS_MEET[3] * space
                   and abs(row - (over['cy'] + under['cy']) / 2) <= (under['cy'] - over['cy']) / 4
                   for over in shared for under in shared):
                found[id(mark)] = False
                continue
            if not any((abs(other['y1'] + 1 - mark['y0']) <= 1 and row - mark['y0'] <= HEADS_MEET[0] * space)
                       or (abs(mark['y1'] + 1 - other['y0']) <= 1 and mark['y1'] - row <= HEADS_MEET[0] * space)
                       for other in filled):
                continue
            columns = np.nonzero(layers['holes'][mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1])[1]
            if len(columns) == 0:
                continue
            aside = (float(columns.mean()) - (wide - 1) / 2) / wide
            if abs(aside) >= HEADS_MEET[1] and any((stem['x'] - (mark['x0'] + mark['x1']) / 2) * aside > 0
                                                   for stem in mark['stems']):
                found[id(mark)] = True
    return found


def _whole_beside(layers: dict, marks: list[dict], limit: float) -> int:
    """A stem carries heads of one kind: all filled or all hollow. A print sets a whole note of one voice in the
    column of a stemmed note of the other voice, with their left edges in line; the two heads touch, and followed
    from the whole note the ink leads through the filled head to its stem. The whole note is wider than a head with
    a stem, so it shows past the filled head at the right. Such a hollow oval gives the stem back. Returns how many."""
    space = layers['space']
    near, apart, edge, wider = (value * space for value in WHOLE_BESIDE)
    heads = [mark for mark in marks if mark['kind'] == 'head' and mark['stems']]
    # The usual width of a head with a stem on this page.
    usual = float(np.median([mark['x1'] - mark['x0'] + 1 for mark in heads])) if heads else space
    count = 0
    for mark in heads:
        wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
        if mark['hole'] < limit or mark.get('solid_cy') is not None or wide < WHOLE[0] * high:
            continue
        for stem in list(mark['stems']):
            up = stem['direction'] == 'up'
            # The whole notes that stand in line with this one, toward the stem's end (see WHOLE_STACK).
            stack = [other for other in marks
                     if other is not mark and other['kind'] == 'head' and not other['stems'] and other['hole'] >= limit
                     and (other['cy'] < mark['cy']) == up
                     and other['x1'] - other['x0'] + 1 >= WHOLE[0] * (other['y1'] - other['y0'] + 1)
                     and abs(other['x0'] - mark['x0']) <= WHOLE_STACK[0] * space
                     and abs(other['x1'] - mark['x1']) <= WHOLE_STACK[0] * space] if WHOLE_STACK else []
            if any(other['y0'] - WHOLE_STACK[1] * space <= stem['end'] <= other['y1'] if up
                   else other['y0'] <= stem['end'] <= other['y1'] + WHOLE_STACK[1] * space for other in stack) \
                    and _stem_ink(layers, stem, [mark] + stack) <= WHOLE_STACK[2] * space:
                mark['stems'].remove(stem)
                for other in stack:
                    if other.get('tail_of') is mark:
                        del other['tail_of']      # no flag at the end of a stem that is none
                count += 1
                continue
            # A stem has its head at the left when it goes up, at the right when it goes down, and one head at a
            # height. A second oval at that height on the other side is the whole note of the other voice.
            if WHOLE_UNISON and (mark['x0'] >= stem['x'] - edge if up else mark['x1'] <= stem['x'] + edge) \
                    and any(other is not mark and abs(other['cy'] - mark['cy']) <= WHOLE_UNISON * space
                            and (other['x1'] <= stem['x'] + near if up else other['x0'] >= stem['x'] - near)
                            and any(own['direction'] == stem['direction'] and abs(own['x'] - stem['x']) <= near
                                    for own in other['stems']) for other in heads):
                mark['stems'].remove(stem)
                count += 1
                continue
            if WHOLE_SECOND and (mark['cx'] > stem['x'] if up else mark['cx'] < stem['x']) \
                    and any(other is not mark and (other['cx'] < stem['x'] if up else other['cx'] > stem['x'])
                            and WHOLE_SECOND[0] * space <= (mark['cy'] - other['cy'] if up else other['cy'] - mark['cy'])
                            <= WHOLE_SECOND[1] * space
                            and any(own['direction'] == stem['direction'] and abs(own['x'] - stem['x']) <= near
                                    for own in other['stems']) for other in heads):
                # The two heads of a second stand in the order that no chord has (see WHOLE_SECOND).
                mark['stems'].remove(stem)
                count += 1
                continue
            for other in heads:
                if other is mark or (other['cy'] > mark['cy']) == up:
                    continue      # the other head stands between the oval and the far end of the stem
                if DASH_OWN and mark.get('pair_box') is not None and other.get('pair_box') == mark['pair_box']:
                    continue      # the two heads of one piece that DASH_PAIR cut: the lower one holds its ledger line
                more = wider if other['hole'] < limit else WHOLE_HALF * space if WHOLE_HALF else None
                if more is None:
                    continue
                gap = (mark['y0'] - other['y1']) if up else (other['y0'] - mark['y1'])
                if gap <= apart and -max(edge, WHOLE_OVER * space) <= mark['x0'] - other['x0'] <= edge \
                        and wide - (other['x1'] - other['x0'] + 1) >= more \
                        and any(own['direction'] == stem['direction'] and abs(own['x'] - stem['x']) <= near
                                for own in other['stems']):
                    mark['stems'].remove(stem)
                    count += 1
                    break
                # A third apart the two heads do not touch. The stem of a chord runs along the edge of both its
                # heads without a break; the way from a whole note to the other voice's stem crosses paper, and the
                # stem stands inside the oval's width.
                inside = (mark['x1'] - stem['x']) if up else (stem['x'] - mark['x0'])
                if WHOLE_APART and apart < gap <= WHOLE_APART[0] * space \
                        and -max(edge, WHOLE_OVER * space) <= mark['x0'] - other['x0'] <= edge \
                        and wide - (other['x1'] - other['x0'] + 1) >= WHOLE_APART[1] * space \
                        and other['x1'] - other['x0'] + 1 >= WHOLE_APART[4] * usual \
                        and inside >= WHOLE_APART[2] * space \
                        and stem.get('past', 0) - stem.get('inked', 0) >= WHOLE_APART[3] * space \
                        and any(own['direction'] == stem['direction'] and abs(own['x'] - stem['x']) <= near
                                for own in other['stems']):
                    mark['stems'].remove(stem)
                    count += 1
                    break
    return count


def _ring_side(layers: dict, mark: dict, space: float) -> None:
    """Takes the two ways at one side of a head's mark out of its ways where they are one ring that passes that side
    and the test for a beam would take one of them for a beam's stem (RING_SIDE)."""
    ways = mark['ways']
    pairs = (('down_left', 'down_right'), ('up_left', 'up_right'))
    for side in ('left', 'right'):
        up, down = ways['up_' + side], ways['down_' + side]
        if not (is_stem(up, space) and is_stem(down, space) and up['lean'] * down['lean'] > 0):
            continue
        if not any(is_stem(ways[left], space) and is_stem(ways[right], space) and ways[right]['x'] - ways[left]['x'] >= space
                   and side in (left.split('_')[1], right.split('_')[1]) for left, right in pairs):
            continue
        if not (_stem_arc(layers, up['mid'], up['end'], mark['cy']) or _stem_arc(layers, down['mid'], down['end'], mark['cy'])):
            continue
        if RING_SIDE_SEEN is not None:
            RING_SIDE_SEEN.append({'box': [int(mark['x0']), int(mark['y0']), int(mark['x1']), int(mark['y1'])], 'side': side,
                                   'leans': [up['lean'], down['lean']]})
        ways['up_' + side] = ways['down_' + side] = None
        mark['ring_side'] = side


def read_symbols(layers: dict) -> dict:
    """The symbols of the page: {'heads': [...], 'signs': [...], 'marks': [...]}.

    Each head: its box and middle, 'staff' (index into layers['staves']), 'place' (pitch place, a number with a
    fraction), 'hollow', and 'stems': one for each stem that it has (two for a head that two voices share, none for a
    whole note), each {'direction', 'x', 'end', 'length'}. Each sign is a sharp, a flat or a natural: its box,
    'kind', 'staff', 'place' and 'count' (two sharps that touch are one mark)."""
    space = layers['space']
    marks = thick_marks(layers)
    if SIGN_GLUED:
        # A sharp that touches its head: the right stroke of the sharp and the head are one mark, and no head.
        marks = [part for mark in marks for part in (_glued_sign(layers, mark) or [mark])]
    if SIGN_WHOLE:
        # A heavy sharp that touches its head: the whole sharp and the head are one mark.
        marks = [part for mark in marks for part in (_glued_whole(layers, mark) or [mark])]
    for mark in marks:
        wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
        mark['stems'] = []
        mark['kind'] = None
        if not (0.3 * space <= wide <= HEAD_WIDE[1] * space and HEAD_HIGH[0] * space <= high <= 2.4 * space):
            continue
        mark['ways'] = {f"{'up' if up else 'down'}_{'right' if right else 'left'}": _way(layers, mark, up, right)
                        for up in (True, False) for right in (True, False)}
        mark['kind'] = _kind(mark, space)
        if mark.get('whole_sign'):
            mark['kind'] = 'sharp'    # the sharp that was cut off its head (SIGN_WHOLE): no head, whatever leaves it
        if mark.get('glued'):
            # The head that a sharp touches: the upright ink at its left side is the stroke of the sharp. (Not the
            # stem down of a head that was cut at that stem, see SIGN_WHOLE.)
            mark['ways']['up_left'] = None
            if mark['glued'] != 'down':
                mark['ways']['down_left'] = None
            mark['kind'] = 'head'
        if FLAT_HEAD and mark['kind'] == 'flat' and mark['hole'] < HOLLOW \
                and wide >= FLAT_HEAD * layers['head'][0] and high >= FLAT_HEAD * layers['head'][1] \
                and sum(1 for other in marks if other['blob'] == mark['blob']) == 2 \
                and any(other is not mark and other['blob'] == mark['blob'] and abs(other['y1'] + 1 - mark['y0']) <= 2
                        and abs(other['cx'] - mark['cx']) <= 0.3 * space
                        and other['x1'] - other['x0'] + 1 >= FLAT_HEAD * wide for other in marks):
            mark['kind'] = 'head'     # the lower of two heads that were one piece of ink: the upper head is no stroke of a flat
        if WORD_MARKS and mark['kind'] and _in_words(layers, mark):
            mark['kind'] = None       # a letter of the words
        # A beam hangs on two stems that leave it the same way, one at each end. (Right over the words, the two are
        # letters under a head. Under the words a slur hangs on two letters, and that is no head.)
        ways = mark['ways']
        if RING_SIDE and mark['kind'] == 'head':
            _ring_side(layers, mark, space)
        for left, right in (('down_left', 'down_right'), ('up_left', 'up_right')):
            if is_stem(ways[left], space) and is_stem(ways[right], space) and ways[right]['x'] - ways[left]['x'] >= space \
                    and not (WORD_STEM and left == 'down_left' and _into_words(layers, mark, ways[left])
                             and _into_words(layers, mark, ways[right]) and _at_staff(layers, mark)):
                mark['kind'] = 'beam' if mark['kind'] == 'head' else mark['kind']
        if mark['kind'] == 'head':
            for name in ('up_right', 'down_left'):
                if is_stem(mark['ways'][name], space):
                    mark['stems'].append(mark['ways'][name])
            if SLUR_STEM and len(mark['stems']) == 2:
                for own, other in (mark['stems'], mark['stems'][::-1]):
                    # The end of a bold slur at a head is steep, and it was followed as a second stem: it is short,
                    # it leans away from the head, and the head's own stem is long and stands upright.
                    away = own['lean'] if own['direction'] == 'up' else -own['lean']
                    if own['past'] <= SLUR_STEM[0] * space and away >= SLUR_STEM[1] \
                            and other['past'] >= SLUR_STEM[2] * space and abs(other['lean']) <= away - SLUR_STEM[3] \
                            and mark['y1'] - mark['y0'] >= SLUR_STEM[7] * space and not _on_upright(layers, mark, own):
                        mark['stems'].remove(own)
                        break
            if not mark['stems'] and SHORT_STEM:
                # A note on a ledger line under the staff has little room over the words: its stem is short. The
                # ledger line shows that the mark is a note.
                for name in ('up_right', 'down_left'):
                    way = mark['ways'][name]
                    if way and way['length'] >= SHORT_STEM[0] * space and way['past'] >= SHORT_STEM[1] * space \
                            and way['slim'] >= SHORT_SLIM * way['past'] and way['inked'] >= INKED * way['past'] \
                            and _on_ledger(layers, mark):
                        mark['stems'].append(way)
            if not mark['stems'] and WORD_STEM:
                # A note right over the words has no room for its stem: the stem is a short slim stub that ends
                # before the words, or it runs into a letter. A mark as high as the heads of the page with such
                # upright ink is that note. (Under the words a slur is such a mark too.)
                high = mark['y1'] - mark['y0'] + 1
                for name in ('down_left',):
                    way = mark['ways'][name]
                    if way and way['past'] >= WORD_STEM[0] * space and _at_staff(layers, mark) \
                            and WORD_STEM[2] * layers['head'][1] <= high <= WORD_STEM[3] * layers['head'][1] \
                            and (_into_words(layers, mark, way) or (WORD_STEM[4] and way['slim'] >= 0.8 * way['past']
                                                                    and _into_words(layers, mark, way, WORD_STEM[4]))):
                        mark['stems'].append(way)
                        mark['word_stem'] = True
    if FLAT_STEM and FLAT_HEAD:
        for mark in marks:
            way = mark.get('ways', {}).get('up_left') if mark['kind'] == 'flat' and mark['hole'] < HOLLOW else None
            if not way or mark['x1'] - mark['x0'] + 1 < FLAT_HEAD * layers['head'][0] \
                    or mark['y1'] - mark['y0'] + 1 < FLAT_HEAD * layers['head'][1]:
                continue
            for other in marks:
                stem = next((stem for stem in other['stems'] if stem['direction'] == 'down'), None) \
                    if other is not mark and other['kind'] == 'head' and other['y1'] < mark['y0'] else None
                if stem and abs(stem['x'] - way['mid']) <= FLAT_STEM * space and abs(way['end'] - other['cy']) <= 1.0 * space \
                        and mark['y0'] - 0.3 * space <= stem['end'] <= mark['y1'] + 0.5 * space:
                    mark['kind'] = 'head'
                    mark['stems'].append(dict(stem))
                    break
    if FLAG_STEM:
        # The flag of an eighth note with a short stem covers most of the stem, and little of the stem is slim. The
        # loop of the flag was then taken for a hollow head, with the piece of stem between the flag and the head as
        # its own stem down. A stem down that ends in the box of a head with no stem, along that head's own upright
        # ink, is the stem of that head.
        for mark in marks:
            way = mark['ways']['up_right'] if mark['kind'] == 'head' and not mark['stems'] else None
            if not way or way['length'] < STEM * space or way['past'] < PAST * space \
                    or way['inked'] < INKED * way['past'] or way['slim'] < FLAG_STEM * space:
                continue
            if any(other is not mark and other['kind'] == 'head' and other['hole'] >= HOLLOW and other['y1'] < mark['y0']
                   and any(stem['direction'] == 'down' and abs(stem['x'] - way['x']) <= 0.35 * space
                           and mark['y0'] - 0.3 * space <= stem['end'] <= mark['y1'] + 0.3 * space for stem in other['stems'])
                   for other in marks):
                mark['stems'].append(way)
    if FLAG_LOOP:
        for mark in marks:
            if mark['kind'] == 'head' and mark['hole'] >= HOLLOW and mark.get('solid_cy') is None \
                    and _flag_loop(layers, marks, mark):
                mark['kind'] = 'loop'
    if TAIL_FLAT and layers.get('head'):
        # A head with a stem of its own going up is no flag. Where its stem down ends at a low, flat mark that
        # has a stem up to it, the mark is the end of that stem, where a beam or a slur meets it, and no head.
        for mark in marks:
            if mark['kind'] != 'head' or not is_stem(mark['ways']['up_right'], space):
                continue
            for stem in mark['stems']:
                for other in (marks if stem['direction'] == 'down' else ()):
                    high, wide = other['y1'] - other['y0'] + 1, other['x1'] - other['x0'] + 1
                    if other is mark or other['kind'] != 'head' or other['cy'] - mark['cy'] < 1.5 * space \
                            or high > TAIL_FLAT[0] * layers['head'][1] or wide < TAIL_FLAT[1] * high \
                            or not other['y0'] - TAIL_FLAT[2] * space <= stem['end'] <= other['y1'] + TAIL_FLAT[2] * space:
                        continue
                    if any(own['direction'] == 'up' and abs(own['x'] - stem['x']) <= 0.35 * space
                           and own['end'] <= mark['y1'] + 0.3 * space for own in other['stems']):
                        other['kind'] = 'beam'
    # A mark at the far end of another head's stem is that note's flag or beam: at the top right of a stem that goes
    # up from a head, or at the bottom right of a stem that goes down from a head.
    for mark in marks:
        for stem in list(mark['stems']):
            if stem['direction'] != 'down':
                continue
            for other in marks:
                if other is mark or other['kind'] != 'head' or other['cy'] - mark['cy'] < 1.5 * space:
                    continue
                if any(own['direction'] == 'up' and abs(own['x'] - stem['x']) <= 0.35 * space
                       and own['end'] <= mark['y1'] + 0.3 * space for own in other['stems']) \
                        and stem['end'] <= other['y1'] + 0.6 * space:
                    mark['stems'].remove(stem)
                    mark['tail_of'] = other
                    break
    # Two heads a second apart stand at the two sides of one stem: one of them has the stem at its other side.
    for mark in marks:
        if mark['kind'] != 'head' or mark['stems']:
            continue
        for name in ('up_left', 'down_right'):
            way = mark['ways'][name]
            if is_stem(way, space) and any(other is not mark and other['blob'] == mark['blob'] and other['kind'] == 'head'
                                           and any(stem['direction'] == way['direction'] and abs(stem['x'] - way['x']) <= 0.35 * space
                                                   for stem in other['stems']) for other in marks):
                mark['stems'].append(way)
    if STEM_THROUGH:
        # Two heads a third apart that were one piece of ink and were cut into an upper and a lower mark: the stem of
        # the one runs along the other, which lies between that head and the stem's end. Seen from the near head the
        # stem is too short, or the far head hides where it is slim.
        wide, high = layers['head']
        for mark in marks:
            if mark['kind'] != 'head' or mark['stems'] \
                    or not STEM_THROUGH[0] * wide <= mark['x1'] - mark['x0'] + 1 <= STEM_THROUGH[1] * wide \
                    or not STEM_THROUGH[0] * high <= mark['y1'] - mark['y0'] + 1 <= STEM_THROUGH[1] * high:
                continue
            same = [other for other in marks if other is not mark and other['blob'] == mark['blob']]
            if len(same) != 1 or same[0]['kind'] != 'head':
                continue
            other = same[0]
            if min(abs(other['y1'] + 1 - mark['y0']), abs(mark['y1'] + 1 - other['y0'])) > 2 \
                    or abs(other['cx'] - mark['cx']) > 0.3 * space:
                continue
            # The stroke of the sign of cut time and the strokes of a sharp go through both marks and on past them.
            back = {'up': ('down_left', 'down_right'), 'down': ('up_left', 'up_right')}
            through = [stem for stem in other['stems'] if min(other['cy'], stem['end']) < mark['cy'] < max(other['cy'], stem['end'])
                       and mark['x0'] - 0.3 * space <= stem['x'] <= mark['x1'] + 0.3 * space
                       and not any(other['ways'][name] and other['ways'][name]['past'] >= STEM_THROUGH[2] * space
                                   and abs(other['ways'][name]['x'] - stem['x']) <= 0.35 * space for name in back[stem['direction']])]
            if through:
                mark['stems'].append(dict(through[0], length=abs(mark['cy'] - through[0]['end'])))
    if DASH_PAIR and DASH_STEM:
        # The two heads of a piece that DASH_PAIR cut hang on one stem. Where the stem leaves the middle of the one
        # head, away from the other, the other head shows no stem of its own.
        for mark in marks:
            if mark['kind'] != 'head' or mark['stems'] or not mark.get('pair_box'):
                continue
            for other in marks:
                if other is mark or other.get('pair_box') != mark['pair_box'] or other['kind'] != 'head':
                    continue
                away = [stem for stem in other['stems'] if (stem['end'] < other['cy']) == (other['cy'] < mark['cy'])]
                if away:
                    mark['stems'].append(dict(away[0], length=abs(mark['cy'] - away[0]['end'])))
    if RIM_STEM:
        # Two whole notes a third apart touch, and the side of the one is upright ink that leaves the other. But a
        # stem goes on past the heads that hang on it: upright ink that ends in the box of another head is its rim.
        heads = [mark for mark in marks if mark['kind'] == 'head']
        whole = {id(mark) for mark in heads if not mark['stems'] and mark['hole'] >= HOLLOW}
        for mark in heads:
            for stem in list(mark['stems']):
                def reach(other: dict) -> float:
                    # The side of a whole note with a bow that leaves it: the ink goes on a little past the note.
                    if RIM_BOW and id(other) in whole and mark['hole'] >= HOLLOW \
                            and other['x0'] + RIM_BOW[1] * space <= stem['x'] <= other['x1'] - RIM_BOW[1] * space:
                        return RIM_BOW[0] * space
                    return RIM_STEM * space
                if any(other is not mark and other['blob'] == mark['blob']
                       and other['x0'] - 2 <= stem['x'] <= other['x1'] + 2
                       and other['y0'] - reach(other) <= stem['end'] <= other['y1'] + reach(other)
                       and (other['cy'] < mark['cy']) == (stem['direction'] == 'up') for other in heads):
                    mark['stems'].remove(stem)
    if PAIR_SHARP:
        _pair_sharp(layers, marks, space)
    _share_stems(marks, space)
    if TWO_HEADS:
        split = []
        for mark in marks:
            parts = _two_heads(layers, mark) if mark['kind'] == 'head' and len(mark['stems']) == 2 else None
            if SIDE_HEAD and parts is None and mark['kind'] == 'head':
                parts = _side_head(layers, mark)
            if GLUED_TWO and parts is None and mark['kind'] in (None, 'beam'):
                parts = _glued_two(layers, mark)
            if SIDE_TWO and parts is None and mark['kind'] == 'sharp' \
                    and (not SIDE_WHOLE or sum(1 for other in marks if other['blob'] == mark['blob']) == 1):
                parts = _side_two(layers, mark)
            split += parts or [mark]
        marks = split
    # The page teaches how large the holes of its hollow heads are. A heavy print leaves a slit of a hole, and there
    # a smaller hole is a hole too.
    limit = HOLLOW
    if HOLLOW_PAGE:
        # An inside that only HOLE_LEAN keeps (layers' `lean`) is a whole inside where the page's other insides of
        # such heads were halves: it does not teach the page its holes.
        lean = layers.get('lean')
        sure = [mark['hole'] for mark in marks if mark['kind'] == 'head' and mark['stems'] and mark['hole'] >= HOLLOW
                and (lean is None or not lean[mark['y0']:mark['y1'] + 1, mark['x0']:mark['x1'] + 1].any())]
        if len(sure) >= 5:
            limit = min(HOLLOW, max(HOLLOW_PAGE[1], HOLLOW_PAGE[0] * float(np.median(sure))))
            if HOLLOW_WORN and float(np.median(sure)) >= HOLLOW_WORN[1]:
                # A print that pressed the ink out of the middle of its filled heads leaves a pale speck there. On a
                # page whose hollow heads have large holes, such a speck is no hole.
                limit = max(limit, HOLLOW_WORN[0] * float(np.median(sure)))
                # A pale print leaves such a speck in many of its filled heads, and the specks come in every size up
                # to the limit and past it. The page shows it (see HOLLOW_PALE). A page whose filled heads hold a
                # small speck and whose holes begin far above it is no such print, and a small hole there is a hole.
                low = [mark['hole'] for mark in marks if mark['kind'] == 'head' and mark['stems'] and mark['hole'] < limit]
                near = sum(1 for hole in low if hole >= HOLLOW_PALE[5] * limit) if HOLLOW_PALE else 0
                if HOLLOW_PALE and len(low) >= HOLLOW_PALE[3] and float(np.median(sure)) >= HOLLOW_PALE[4] \
                        and sum(1 for hole in low if hole >= HOLLOW_PALE[1]) >= HOLLOW_PALE[0] * len(low) \
                        and near >= HOLLOW_PALE[7] and near >= HOLLOW_PALE[6] * len(low):
                    limit = max(limit, HOLLOW_PALE[2] * float(np.median(sure)))
    layers['hollow'] = limit
    if WHOLE_BESIDE:
        _whole_beside(layers, marks, limit)
    meet = _heads_meet(layers, marks, limit) if HEADS_MEET else {}
    heads, signs, orphans = [], [], []
    for number, mark in enumerate(marks):
        if mark['kind'] is None or mark['kind'] == 'beam':
            continue
        staff = _staff_of(layers, mark['cx'], mark['cy'])
        if staff is None:
            continue
        if meet.get(id(mark)) is False:
            continue        # the paper where two filled heads meet: see HEADS_MEET
        hollow = mark['hole'] >= limit and id(mark) not in meet
        cy = mark['hole_cy'] if HOLE_PLACE and hollow and mark['hole_cy'] is not None else mark['cy']
        or_hollow = None
        orphan = False
        if hollow and mark.get('solid_cy') is not None and mark['stems']:
            or_hollow = cy
            hollow, cy = False, mark['solid_cy']
        if LINE_SLIT and not hollow and or_hollow is None and mark['kind'] == 'head' and mark['stems'] \
                and (_line_slit(layers, mark, layers['staves'][staff])
                     or (LINE_HALVES and _line_halves(layers, mark, layers['staves'][staff]))):
            hollow = True
        slit = slit_place = None
        if SLIT_ONE and not hollow and or_hollow is None and mark['kind'] == 'head' and mark['stems']:
            slit = _slit_one(layers, mark, layers['staves'][staff]) or 'none'
            slit_place = (_slit_one(layers, mark, layers['staves'][staff], False) or 'none') if SLIT_LEDGER else slit
        place = pitch_place(layers['staves'][staff], cy)
        if mark.get('line_place') is not None and mark['kind'] == 'head':
            place = mark['line_place']      # a head whose line the cut of its piece knows: see DASH_PAIR
        if mark['kind'] != 'head':
            if abs(place) <= 7.5:
                signs.append({'x0': mark['x0'], 'y0': mark['y0'], 'x1': mark['x1'], 'y1': mark['y1'], 'cx': mark['cx'],
                              'cy': cy, 'staff': staff, 'place': place, 'kind': mark['kind'],
                              'count': max(1, int(round((mark['x1'] - mark['x0'] + 1) / (1.05 * space))))
                              if mark['kind'] == 'sharp' else 1})
            continue
        if not mark['stems'] and mark.get('room'):
            continue        # a piece of a clef or of a number is no head
        if not mark['stems']:
            # A whole note is an oval that lies on its side, as large as the heads of the page. The letter o of the
            # words is small and round, and a capital O of a title stands upright.
            wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
            def lying(other: dict, least: float = WHOLE[0]) -> bool:
                wide, high = other['x1'] - other['x0'] + 1, other['y1'] - other['y0'] + 1
                return wide >= least * high and wide >= WHOLE[1] * layers['head'][0] \
                    and WHOLE[2] * layers['head'][1] <= high <= WHOLE[3] * layers['head'][1]
            # No word stands in the staff: there a whole note may be as round as the letter o.
            oval = lying(mark, WHOLE_STAFF if WHOLE_STAFF and abs(place) <= 4.6 else WHOLE[0])
            if WHOLE_SLIT and not hollow and oval and 'tail_of' not in mark \
                    and WHOLE_SLIT[0] * layers['head'][0] <= wide <= WHOLE_SLIT[1] * layers['head'][0] \
                    and high <= WHOLE_SLIT[9] * layers['head'][1] \
                    and _whole_slit(layers, mark, layers['staves'][staff]):
                hollow = True       # the print closed the hole of a whole note on a line but for a speck
            if WHOLE_FILLED and not hollow and oval and 'tail_of' not in mark and any(
                    other is not mark and other['blob'] == mark['blob'] and other['kind'] == 'head' and not other['stems']
                    and other['hole'] >= limit and lying(other) and abs(other['cx'] - mark['cx']) <= WHOLE_FILLED * space
                    and min(abs(other['y0'] - mark['y1']), abs(mark['y0'] - other['y1'])) <= 0.3 * space for other in marks):
                hollow = True       # the print filled the hole of a whole note that touches the whole note of the other voice
            elif not (hollow and oval and 'tail_of' not in mark and _rim(layers, mark) >= RIM
                      and not (CELL and _cell(layers, mark))):
                # A mark as large as a head with no stem: the copy may have cut its stem off (see lost_stems()).
                if not (ORPHANS and 'tail_of' not in mark
                        and ORPHANS[0] * layers['head'][0] <= wide <= ORPHANS[1] * layers['head'][0]
                        and ORPHANS[0] * layers['head'][1] <= high <= ORPHANS[1] * layers['head'][1]):
                    continue
                orphan = True
        head = {'x0': mark['x0'], 'y0': mark['y0'], 'x1': mark['x1'], 'y1': mark['y1'], 'cx': mark['cx'], 'cy': cy,
                'staff': staff, 'place': place, 'hollow': hollow, 'hole': mark['hole'], 'stems': mark['stems'],
                'mark': number, 'blob': mark['blob'], 'core': core_light(layers, mark),
                'alt': dict(_places(layers['staves'][staff], mark), **_fat(layers, mark))}
        if PLACE_MASS and abs(place) <= 4.6:
            # A second look at a head that was measured at the border of two places.
            mass, near = head['alt']['mass'], round(place)
            if abs(place - near) >= PLACE_MASS[0] and round(mass) == near + (1 if place > near else -1) \
                    and abs(mass - round(mass)) <= 0.5 - PLACE_MASS[1]:
                head['place'] = place = mass
        if LINE_HOLE and hollow and HOLE_PLACE and abs(place) <= 4.6 and mark.get('line_place') is None:
            # A staff line through the middle of a hollow head: the head sits on the line, and the line hides one half
            # of its inside, so that the middle of the hole stands at the border of the next place (LINE_HOLE).
            box, part = head['alt']['box'], abs(place) - int(abs(place))
            line = 2 * round(box / 2)
            if LINE_HOLE[0] <= part <= 1 - LINE_HOLE[0] and abs(box - line) <= LINE_HOLE[1] and round(place) != line:
                head['place'] = place = float(line)
        if slit:
            head['speck'], head['speck_place'] = slit, slit_place
        if mark.get('loop'):
            head['loop'] = mark['loop']
        if mark.get('room'):
            head['room'] = True
        if mark.get('room_sign'):
            head['room_sign'] = True
        if mark.get('across'):
            head['across'] = True
        if mark.get('side_two'):
            head['side_two'] = True
        if mark.get('sharp'):
            head['sharp'] = mark['sharp']     # the box of the sharp that was cut off this head (SIGN_WHOLE)
        if mark.get('pair_box'):
            head['pair_box'] = mark['pair_box']
        if or_hollow is not None:
            head['or_hollow'] = or_hollow
        if abs(place) > 4 + 2 * REACH:
            continue
        if mark.get('line_place') is not None:
            head['ledgers'] = [mark['dash']] if 'dash' in mark else []
        elif abs(place) > 4.6:
            if SIDE_LEDGER and mark.get('pair'):
                # The two heads of a pair at one stem line are one wide head for a ledger line: see SIDE_LEDGER.
                pair = mark['pair']
                head['ledgers'] = ledger_lines(layers, layers['staves'][staff],
                                               dict(head, **pair, hollow=pair['hole'] >= limit),
                                               (pair['x1'] - pair['x0'] + 1) / 2 + 0.3 * space)
            else:
                head['ledgers'] = ledger_lines(layers, layers['staves'][staff], head)
            found = ledger_place(layers, layers['staves'][staff], head)
            if LEDGER_NARROW and found is not None and not head['ledgers'] and abs(place) > max(5.6, NO_LEDGER):
                lines = _narrow_ledgers(layers, layers['staves'][staff], head)
                if lines:
                    head['ledgers'] = lines
                    found = ledger_place(layers, layers['staves'][staff], head)
                    if LEDGER_NARROW_SEEN is not None:
                        LEDGER_NARROW_SEEN.append({'cx': head['cx'], 'cy': head['cy'], 'staff': staff, 'place': place, 'found': found,
                                                   'lines': lines, 'hollow': hollow, 'wide': head['x1'] - head['x0'] + 1,
                                                   'high': head['y1'] - head['y0'] + 1, 'orphan': orphan,
                                                   'stems': [(stem['direction'], stem['x'], stem['end']) for stem in mark['stems']]})
            if found is None or (not head['ledgers'] and abs(place) > max(5.6, NO_LEDGER)):
                # A faint ledger line is lost in the copy. A letter of the words has a bowl and a stem too, but its
                # stem is short: a head as large as the heads of the page on a long stem is a note.
                wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
                if LEDGER_DASH and found is not None and not mark.get('word_stem') \
                        and FAR_STEM[2] * layers['head'][0] <= wide <= FAR_STEM[3] * layers['head'][0] \
                        and LEDGER_DASH[4] * layers['head'][1] <= high <= FAR_STEM[3] * layers['head'][1] \
                        and any(stem['past'] >= LEDGER_DASH[5] * space for stem in mark['stems']) \
                        and _foot_dashes(layers, layers['staves'][staff], mark, place > 0):
                    found = 7.0 if place > 0 else -7.0
                elif WHOLE_FOOT and found is not None and hollow and not mark['stems'] and not orphan \
                        and abs(place) <= WHOLE_FOOT[3] and _whole_foot(layers, layers['staves'][staff], mark, place > 0):
                    found = 7.0 if place > 0 else -7.0     # a whole note that sits on its ledger line
                elif not (FAR_STEM and found is not None and abs(place) <= FAR_STEM[1] and not mark.get('word_stem')
                        and any(stem['past'] + (_pale_on(layers, stem) if PALE_STEM else 0) >= FAR_STEM[0] * space
                                for stem in mark['stems'])
                        and FAR_STEM[2] * layers['head'][0] <= wide <= FAR_STEM[3] * layers['head'][0]
                        and FAR_STEM[2] * layers['head'][1] <= high <= FAR_STEM[3] * layers['head'][1]):
                    continue
            head['place'] = found
        (orphans if orphan else heads).append(head)
    close_ledgers(layers, heads + orphans)
    return {'heads': heads, 'signs': signs, 'marks': marks, 'orphans': orphans}


def slit_page(heads: list[dict]) -> None:
    """The heads that hold the slit of a half note (see SLIT_ONE) get `slit`, counted over the notes of the page: on
    a page of a worn print the filled heads hold specks anywhere, and no speck is a slit there (see SLIT_PAGE). The
    marks before the notes begin are not counted: a flat of the key signature has a stroke and a hole too."""
    asked = [head for head in heads if head.get('speck')]
    # (The page is counted with each ledger line at its place: SLIT_LEDGER moves no page over the limit or under it.)
    other = sum(head.pop('speck_place', head['speck']) == 'other' for head in asked)
    worn = SLIT_PAGE and other > SLIT_PAGE[0] * len(asked)
    for head in asked:
        if head.pop('speck') == 'slit' and not worn:
            head['slit'] = True


# ----------------------------------------------------------------------------------------------------------------
# A second look: hollow heads from their holes

HOLE_HEADS = (0.6, 2.2, 1.2, 0.55, 0.9, 6.5)   # a hole that no head owns is a hollow head when its area is from this to
#                    this many times the usual hole of the page's hollow heads, it is this many times as wide as
#                    high, it fills from this to this share of its box (an oval fills 0.79, a cell of the staff all
#                    of it), and it lies up to this place (None: off)
OPEN_HEADS = 0.85    # an open hole (the rim of the head has a small break) with a stem is a hollow head too, when pieces of
#                    its rim were read as heads; its area is at most this many staff spaces squared, as a room between
#                    a slanted head, its stem and two staff lines is larger (0: off)
OPEN_ROUND = 0.82    # such an open hole may be as high as the gap between two staff lines when it fills at most this share of its box
OPEN_ALONE = 0.5     # an open hole with a stem and no piece of rim that was read as a head is a hollow head when ink of
#                    its own (no staff line) stands at this share of the ring around it: the thin rim of a printed
#                    half note is no thick mark at all (0: off)
OPEN_STEM = (0.4, 0.3, 0.5)   # ... and its stem is its own: no bar line (within this many staff spaces), no stroke
#                    of a sign, and not the stem of a filled head (the same column within this, the same end within
#                    this): the paper between a head, its stem and its flag is open too, and so is the paper
#                    between a bar line or a sharp, the end of a tie and a staff line. (None: off. Without it the rule gained 29 notes on LitChoir's
#                    clean copies and lost 5, but lost 285 on the fresh test set.)
OPEN_SLANT = (0.8, 0.75)   # such a hole may be as high as wide (from this share) when it fills at most this share of its box
RAGGED_SLIT = (1.5, -10.0, 40.0, 0.35)   # closed paper that is not quite round (layers.RAGGED) is the inside of a hollow
#                      head, asked as an open hole is, when it is a slit: this many times as long as wide along its own
#                      axis, which rises to the right by this to this many degrees, and at most this large (staff
#                      spaces squared). The inside of a printed half note lies so. The bowl of a flat, a natural and
#                      the paper between a sign and a head stand upright (None: off).
SLIT_BETWEEN = (0.3, 0.6, 0.6, 1.4)   # such a slit between two hollow heads that were read, one over it and one under it in
#                      its column (their middles at most [1] head widths beside its middle, and from [2] to [3] staff
#                      spaces from it), is the inside of the head between them from [0] of the usual hole of the page
#                      on: the middle head of three at one stem, whose inside a grey smear of the scan or a thick rim
#                      half filled. No ink but a head closes paper in between two heads of one stem. The slit may lie
#                      in the boxes of the two heads, which were cut out of one mark. Three such slits on LitChoir's
#                      scan pages, each a head (0.37, 0.48 and 0.88 of the usual hole); the other closed paper between
#                      two such heads is no slit: the insides of the whole notes of a thick copy, and a clef (None: off)
SLIT_BESIDE = (1.5, 0.6, 2)   # such a slit in the box of a hollow head that was read is the inside of a second head, a
#                      second away at the other side of the stem, where that box is at least the first number of head
#                      widths wide and the middle of the slit lies at least the second number of head widths beside
#                      the middle of that head's own inside: two half notes a second apart are one mark, and only one
#                      of the two insides is round enough to be filled. The box holds at most the third number of
#                      pieces of filled inside (the head's own, which a staff line can cut in two): a chord that a
#                      hand drew over holds more. The new head takes a stem of its own (and the other head leaves
#                      it that stem where it has two), or hangs on the other head's stem
#                      (None: a slit in a hollow head is that head's)
OPEN_BESIDE = 0.25   # a piece of the rim can lie just outside the box of an open hole: a filled head lower than
#                      OPEN_PIECE whose box reaches into that box and whose middle lies up to this many staff spaces
#                      over or under it (0: off). A print with a bold rim leaves the rim as such a piece. A piece
#                      that one open head replaced owns no stem any more, and ink in the columns of an open head that
#                      was read as a sign is no sign: the second head of a chord, which hangs on the same stem, is
#                      asked without them.
OPEN_PIECE = 0.75    # a piece of a broken rim is lower than this share of the height of the page's heads
OPEN_ORDER = True    # an open hole whose stem a filled mark holds (OPEN_STEM) is asked again after every other open hole:
#                      the mark can be a piece of the broken rim of a head that a later open hole makes, and such a piece
#                      owns no stem (two half notes of a chord a third apart, both rims broken, the upper head asked
#                      first). Four such chords on LitChoir's pages (trisagion-obleschuk, nativity-kontakion,
#                      nativity-troparion--s2, triodion-publican), none on the fresh set. (False: off)
OPEN_ORDER_SEEN = None   # a census: the open holes that OPEN_STEM refuses, with whether they were asked again (None: none)
UNISON_SLIT = (0.35, 0.3)   # a slit (RAGGED_SLIT) beside a whole filled head is the inside of a second head, of the other
#                      voice on the same pitch, where the filled head has a stem up at its right and the slit has a stem
#                      down in that column at its left (within the first number of staff spaces), the filled head at the
#                      left of that column and the slit at its right, their middles at most the second number of staff
#                      spaces apart: a print sets a quarter note and a half note of two voices on one pitch side by side,
#                      and one print joins them into one blot whose half note keeps only a slit of its inside. A rule for
#                      one print (None: off)
UNISON_LOG = None
OPEN_FLAT = (0.85, 0.7)   # an open hole is no inside of a head where its top or its bottom is level at a staff line in the
#                      first share of its columns or more (as FLAT_CELL asks of closed paper) and the paper that mirrors it
#                      across that line is open in the second share or more (as FLAT_WEDGE asks): the paper over a half
#                      note that a staff line, the bar of the ison's breve beside it and the note's own stem close (one
#                      print sets the melody's note against the breve so), the paper between a slur or a beam, a stem and
#                      a line, between a pencil ring and a head, and in the bowl of a C or of a number of a time signature.
#                      The inside of a head whose rim broke touches a line at a point; where a line runs through a head,
#                      the other half of the head lies across it. The heads that were read in the box of a refused
#                      cell stay as they were read: a filled head that the cell had taken for a piece of its rim is a
#                      head again, and so are the pieces of what closed the cell (the bar of a natural, the bowl of a
#                      flat). A whole note on a line whose upper rim is open at one end is refused too, where the lower
#                      half of its inside is not in the layer of the insides (one place on LitChoir's pages, read as a
#                      half note before). (None: off)
HOLE_FIVE = (0.75, 0.12, 0.4, 0.85)   # a hollow head in the first space beside the staff (no ledger line belongs there)
#                      is a head without a ledger line. A head of a chord that touches the head on the staff's outer
#                      line is lost so: the other head keeps the stem that goes past this one, and this one takes the
#                      stem at its own side (the upper head goes up, the lower one down). A head without a stem is no
#                      head where ink stands at both sides of its rim within the first number of staff spaces: a mark
#                      between two strokes is a letter of a word, a letter p between brackets, or the ison's breve
#                      between its bars. And the inside of a head hangs from the line with its rim between them, as an
#                      oval: an inside whose widest row lies next to the staff (within the second number of its height,
#                      where it is the third number of staff spaces high or more) and spans the fourth share of its box
#                      or more is a wedge between the line and a stroke, a pencil ring or a flag that bends back. (The
#                      slit of a half note by hand leans, and none of its rows spans its box.) A census of every such
#                      head on LitChoir's pages (121, on 72 pages; none on the fresh set), each looked at: the strokes
#                      take 3 letters and 13 breves, the wedge 5 cells of pencil rings and flags, and 3 false heads stay
#                      (the room of a flag whose inside is no wedge, a circle by hand with a line through it, a chord
#                      drawn over by hand). A test of the stems (a stem that ends in the head that owns it, a stem that
#                      is an arc) took nothing that the wedge had not taken, and is not in the rule. (None: only the
#                      second head of a read mark)
HOLE_BIG = None      # (2.5, 4): the hole of a mark that is this many times the usual hole of the page's hollow heads (the
#                    median of this many or more) is no inside of a head, and the page is read again without it.
#                    Off: a slur does close in paper with a stem and a staff line, and filled it hides the stem of
#                    the real note; but the size alone does not tell it. A page has two usual holes, the small one of
#                    its half notes and the large one of its whole notes (5 to 9 times apart in a thick print). On
#                    LitChoir the rule gained 87 notes and lost 229; counted by the largest piece of paper of each
#                    head and only after the clefs, it gained 65 and lost 271.
HOLE_THROUGH = True  # a hollow head on a staff line: the two halves of its inside, over and under the line, are one hole
HOLE_FAR = 8.5       # a hole past HOLE_HEADS[5], the space past the first ledger line, up to this place, is a hollow head
#                    where it has a stem, every ledger line between the staff and the head is found at its step (by
#                    ledger_lines, or in LEDGER_NARROW's narrow window, where one line is enough), the head stands beside
#                    its last line (an odd place, not on a line), and its middle lies in no row of the words. A half note
#                    over a bass staff sits on its first ledger line and the line cuts the lower rim: its inside lies past
#                    6.5, and the pieces of the rim were read as a filled C#4 or C4 under the true D4, or not at all. A
#                    census of every such hole at the reader's step (54 on LitChoir's pages, none on the fresh set), each
#                    looked at: 42 D4 half notes over a bass staff on 19 scores, 9 B3 half notes under a treble staff and
#                    an F#4 over two ledger lines; and two that the guards take, the bowl of a g in a word that stands on
#                    the first ledger line of a head under it (on the second line, an even place), and the paper that the
#                    closing of the ink shuts in between a head that hangs under the staff and the letters under it (in
#                    the row of the words). A typewriter print of the pascha canon sets its B3 under the dash, and the
#                    rule reads two heads there as B3 that are typed as C4 at one place and were lacking at another: the
#                    heads stand as the print's typed B3s stand. (None: off)
HOLE_FAR_SEEN = None   # census: a dict for each head that HOLE_FAR reads
HOLE_SHARE = 1.0     # two voices a third apart, one over the other, the upper with its stem up and the lower with its stem
#                    down: the strokes run along the sides of both heads, and a hollow head read from its hole found both
#                    stems. Where another hollow head 0.7 to 1.3 staff spaces over or under it has one of those stems
#                    only (the same way, within 0.2 staff spaces), the two share them: where the other head's stem passes
#                    this head on its way, it is this head's, and the other head takes this head's other stem; else this
#                    head leaves the other head's stem to it. On extra-come-bless a G3 under a B3 whose stems cross
#                    (pg0630) was a head of both voices, and a B3 under a D4 (pg0631) a head of the upper voice. 36 acts
#                    on LitChoir's pages and none on the fresh set; most take away the copy of a head that both voices had
#                    been given. The other head is a hollow head of its own and no piece of this head's rim: a filled
#                    piece of a worn chord took the head's stem down, and the head that kept its stem up passed as a mark
#                    at a bar line, whose test asks only the heads read from holes for the other voice (bar_marks; one
#                    note of pascha-angel-cried-believers). The number is the most ink, in staff spaces, that stands
#                    straight past this head's inside at the side away from the other head: a hollow head has its rim
#                    there (0.10 to 0.48 at the 36 true acts), and the cell that two filled heads close with their stem
#                    down, the flag that the print draws back up to the stem and a staff line has the two heads there
#                    (1.81 and 1.90: a false half note of triodion-meatfare pg0424, and pg0169); the cell of that flag
#                    under the line was the other head. (None: off)
HOLE_SHARE_SEEN = None
OPEN_THROUGH = True  # the two halves that a staff line cuts out of the open inside of a half note whose rim the copy broke
#                    are one inside too, as HALVES_ACROSS joins closed halves that lean apart. The ink between the
#                    halves is asked with the small breaks of the rim closed, as the open insides are found
#                    (layers.HOLE_GAP): a break at the line left 0.89 of the line's columns as ink, where 0.9 is asked.
#                    A G4 half note of extra-come-bless (pg0629); the census at the step found no other place on
#                    LitChoir's pages (False: off)
OPEN_THROUGH_LOG = None   # a list: (cx, cy, area, wide, high, staff) of each head that OPEN_THROUGH reads
HOLE_RIM = 0.2       # the rim of such a head is this thick, in staff spaces
HOLE_CELL = 0.85     # a hole in a space of the staff that is this share of the gap between two staff lines high is a cell
HOLE_CLOSED = 0.6    # past its rim, paper shows at the left and at the right within this many staff spaces


def big_holes(layers: dict, heads: list[dict]) -> np.ndarray | None:
    """The closed-in paper at the marks whose hole is far larger than the usual hole of the page's hollow heads
    (HOLE_BIG): a slur closes in paper with a stem and a staff line, and so does a tie with two heads. Filled, such
    paper is a thick mark that hides the stem it lies on, and the real head beside it loses that stem. The page
    teaches how large the holes of its heads are: each hollow head shows its largest piece of closed-in paper (two
    heads of a chord that touch are one mark with two holes). `heads` are the heads after the clefs: a clef closes
    in large paper too. None when the page shows no such paper, or too few hollow heads."""
    if not HOLE_BIG:
        return None
    count, labels, stats, _ = cv2.connectedComponentsWithStats(layers['holes'], connectivity=4)
    own = []
    for head in heads:
        if head['hollow'] and not head.get('thin') and not head.get('from_hole'):
            inside = np.unique(labels[head['y0']:head['y1'] + 1, head['x0']:head['x1'] + 1])
            inside = inside[inside > 0]
            if len(inside):
                own.append(max(inside, key=lambda index: stats[index][4]))
    if len(own) < HOLE_BIG[1]:
        return None
    usual = float(np.median([stats[index][4] for index in own]))
    big = sorted({int(index) for index in own if stats[index][4] >= HOLE_BIG[0] * usual})
    return np.isin(labels, big).astype(np.uint8) if big else None


def _slit(part: np.ndarray) -> bool:
    """Whether a piece of paper lies on its side as the inside of a printed half note does (RAGGED_SLIT): a slit along
    its own axis, which rises to the right."""
    ys, xs = np.nonzero(part)
    if len(xs) < 6:
        return False
    spread = np.cov(np.vstack((xs, -ys)).astype(float))
    values, vectors = np.linalg.eigh(spread)
    if values[0] <= 0 or values[1] < RAGGED_SLIT[0] ** 2 * values[0]:
        return False
    along = vectors[:, 1] if vectors[0, 1] >= 0 else -vectors[:, 1]
    rise = float(np.degrees(np.arctan2(along[1], along[0])))
    return RAGGED_SLIT[1] <= rise <= RAGGED_SLIT[2]


def _in_head(sign: dict, heads: list[dict]) -> bool:
    """Whether the middle of a sign lies in the columns of an open head and its box reaches into that head's box: the
    ink where two half notes of a chord touch was read as a sign (see OPEN_BESIDE)."""
    middle = (sign['x0'] + sign['x1']) / 2
    return any(head.get('open') and head['x0'] <= middle <= head['x1']
               and sign['y0'] <= head['y1'] and sign['y1'] >= head['y0'] for head in heads)


HALVES_ACROSS = (1.2, 1.0, 0.5)   # a half note on a staff line whose inside leans: the line cuts the inside into a half
#   over it at the right and a half under it at the left, which share few columns, so that they are neither one
#   round inside for the layers nor one over the other (HOLE_THROUGH). Two pieces of closed paper, round or ragged, at
#   the two sides of one line are the inside of a head on that line where the upper one lies right of the lower one,
#   they share a column, both together are at most the first number of staff spaces wide and the second number high,
#   and the line between them is ink. (Pieces that share the third number of the narrower one's columns or more are
#   one over the other: those are read as they were.) Such a head takes its own stem. A head right over or under it
#   that was read with two stems, one up and one down, shares them with it: the upper head keeps the stem that goes
#   up and the lower head the one that goes down. (None: off)


def _lean_halves(layers: dict, holes: np.ndarray, ragged: np.ndarray | None,
                 ink: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """The insides that a staff line or a ledger line cut into two halves that lean apart (HALVES_ACROSS): the paper
    of both halves with the ink of the line between them, and that ink alone. The halves of open insides are asked
    in the ink as the open insides were found, with the small breaks of the rim closed (OPEN_THROUGH)."""
    space = layers['space']
    if ink is None:
        ink = layers['ink']
    paper = (holes > 0).astype(np.uint8)
    if ragged is not None:
        paper |= (ragged > 0).astype(np.uint8)
    count, labels, stats, centres = cv2.connectedComponentsWithStats(paper, connectivity=4)
    both, through = np.zeros_like(paper), np.zeros_like(paper)
    wide_most, high_most, over = HALVES_ACROSS
    small = [index for index in range(1, count)
             if stats[index][4] >= 0.02 * space * space and stats[index][3] <= 0.6 * space]
    ends = {}           # the pieces by the row under their last one
    for index in small:
        ends.setdefault(int(stats[index][1] + stats[index][3]), []).append(index)
    for lower in small:
        lx, ly, lw, lh, la = (int(value) for value in stats[lower])
        index = _staff_of(layers, lx + lw / 2, ly + lh / 2)
        if index is None:
            continue
        staff = layers['staves'][index]
        step, thick = staff['space'], staff['thick']
        lines = list(staff['rows']) + [staff['rows'][0] - k * step for k in range(1, 5)] \
            + [staff['rows'][4] + k * step for k in range(1, 5)]
        for gap in range(1, int(thick + 3) + 1):
            for upper in ends.get(ly - gap, []):
                ux, uy, uw, uh, ua = (int(value) for value in stats[upper])
                first, last = max(ux, lx), min(ux + uw, lx + lw) - 1
                if last < first or last - first + 1 >= over * min(uw, lw) or centres[upper][0] <= centres[lower][0]:
                    continue
                if max(ux + uw, lx + lw) - min(ux, lx) > wide_most * space or ly + lh - uy > high_most * space:
                    continue
                if not any(uy + uh - 2 <= line <= ly + 1 for line in lines) or ink[uy + uh:ly, first:last + 1].mean() < 0.9:
                    continue
                both[uy:uy + uh, ux:ux + uw] |= (labels[uy:uy + uh, ux:ux + uw] == upper).astype(np.uint8)
                both[ly:ly + lh, lx:lx + lw] |= (labels[ly:ly + lh, lx:lx + lw] == lower).astype(np.uint8)
                both[uy + uh:ly, first:last + 1] = 1
                through[uy + uh:ly, first:last + 1] = 1
    return both, through


def _open_flat(layers: dict, part: np.ndarray, left: int, top: int) -> bool:
    """(OPEN_FLAT) Whether open paper (its piece in its box, whose corner is at column left and row top) is level at a
    staff line at its top or at its bottom, with open paper across that line, as FLAT_CELL and FLAT_WEDGE measure
    closed paper."""
    rows = np.array(sorted(row for staff in layers['staves'] for row in staff['rows']), float)
    half = max(staff['thick'] for staff in layers['staves']) / 2
    slack = max(FLAT_CELL[2], half)
    high = part.shape[0]
    first, last = part.argmax(axis=0), high - 1 - part[::-1].argmax(axis=0)
    above = float((first <= 1).mean()) if np.abs(rows - (top - 0.5 - half)).min() <= slack else 0.0
    below = float((last >= high - 2).mean()) if np.abs(rows - (top + high - 0.5 + half)).min() <= slack else 0.0
    if max(above, below) < OPEN_FLAT[0]:
        return False
    edge = top - 0.5 - half if above >= below else top + high - 0.5 + half
    line = float(rows[np.abs(rows - edge).argmin()])
    ys, xs = np.nonzero(part)
    across = np.round(2 * line - (ys + top)).astype(int)
    inside = (across >= 0) & (across < layers['ink'].shape[0])
    across, xs = across[inside], xs[inside] + left
    if not len(across):
        return False
    paper = (layers['ink'][across, xs] == 0) & (layers['lines'][across, xs] == 0) & (layers['holes'][across, xs] == 0)
    return float(paper.mean()) >= OPEN_FLAT[1]


def _ink_past(ink: np.ndarray, x: int, y: int, wide: int, high: int, up: bool) -> int:
    """The ink that stands straight over (up) or under a hole whose box is x, y, wide, high: the middle one of the runs of
    ink in the hole's three middle columns, in pixels (HOLE_SHARE)."""
    runs = []
    for column in range(max(0, x + wide // 2 - 1), min(ink.shape[1], x + wide // 2 + 2)):
        row, step, run = (y - 1, -1, 0) if up else (y + high, 1, 0)
        while 0 <= row < ink.shape[0] and ink[row, column]:
            row += step
            run += 1
        runs.append(run)
    return sorted(runs)[len(runs) // 2]


def hole_heads(layers: dict, heads: list[dict], ends: list[float], bars: dict[int, list[float]] | None = None,
               signs: list[dict] | None = None) -> list[dict]:
    """Hollow heads that the marks did not give: two half notes or whole notes, one over the other, grow together
    into one mark that is too large for a head, and so does a head with the sign before it. But the hole of each
    head is still there. The page teaches how large the holes of its hollow heads are; a hole of that size that lies
    on its side as an oval, with its own rim at both sides, in no head that was read, is a hollow head.

    The flag of a printed note, a natural, a flat and the digit 4 close in paper too, but that paper stands upright
    or has corners. A cell between two staff lines and two strokes fills its whole box.

    A copy breaks the thin rim of a hollow head, and its inside is then open to the paper (layers['open_holes']):
    the head falls into pieces of rim, which are read as small filled heads at the wrong places. Such an open hole
    of the usual size with a stem is a hollow head too (OPEN_HEADS), and the pieces of its rim are no heads: each
    head of the result that replaces others names them in 'replaces'."""
    if not HOLE_HEADS:
        return []
    space = layers['space']
    holes, ink = layers['holes'], layers['ink']
    own, pairs = [], set()
    for head in heads:
        if head['hollow'] and not head.get('thin'):
            # The two heads of a piece that DASH_PAIR cut count as the one mark that they were: the page's measure
            # of a hole stays as it was.
            x0, y0, x1, y1 = (head.get('pair_box') if DASH_OWN else None) or (head['x0'], head['y0'], head['x1'], head['y1'])
            if (x0, y0, x1, y1) in pairs:
                continue
            if head.get('pair_box') and DASH_OWN:
                pairs.add((x0, y0, x1, y1))
            own.append(float((holes[y0:y1 + 1, x0:x1 + 1] > 0).sum()))
    if len(own) < 3:
        return []
    usual = float(np.median(own))
    rim = max(2, int(round(HOLE_RIM * space)))
    far = int(round(HOLE_CLOSED * space))
    out = []
    pieces = set()      # the heads that a head of the result replaces: pieces of its rim, which own no stem
    passes = [(False, holes, None)]
    if HOLE_THROUGH:
        # A hollow head on a staff line or on a ledger line: the line cuts its inside in two. The ink of the line
        # between two pieces of closed-in paper, one right over the other, is inside the head too.
        near = int(round(max(staff['thick'] for staff in layers['staves']) + 1))
        over, under = np.zeros_like(holes), np.zeros_like(holes)
        for step in range(1, near + 1):
            over[step:] |= holes[:-step]
            under[:-step] |= holes[step:]
        through = ink & over & under
        passes.append((False, holes | through, through))
    ragged = layers.get('ragged') if RAGGED_SLIT else None
    lean = None
    if HALVES_ACROSS:
        lean, across = _lean_halves(layers, holes, layers.get('ragged'))
        passes.append((False, lean, across))
    if OPEN_HEADS and ragged is not None:
        passes.append((True, ragged, None))
    if OPEN_HEADS and layers.get('open_holes') is not None:
        passes.append((True, layers['open_holes'], None))
    open_lean = None
    if OPEN_THROUGH and HALVES_ACROSS and OPEN_HEADS and layers.get('open_holes') is not None:
        # A hollow head on a staff line whose rim the copy broke: the line cuts its open inside into two halves that
        # lean apart, each too small for a head (OPEN_THROUGH). They are one inside as HALVES_ACROSS joins closed ones.
        from .layers import HOLE_GAP
        size = int(max(3, round(HOLE_GAP * space))) | 1
        closed = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((size, 1), np.uint8)) \
            | cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((1, size), np.uint8))
        open_lean, open_across = _lean_halves(layers, layers['open_holes'], None, closed)
        passes.append((True, open_lean, open_across))
    again = {}      # the open holes whose stem a filled mark held, by their paper: asked again at the end (OPEN_ORDER)
    if OPEN_ORDER:
        passes.append(None)
    for entry in passes:
        if entry is None:
            passes += [(True, paper, None, indexes) for paper, indexes in again.values()]
            continue
        is_open, paper, through, only = entry if len(entry) == 4 else entry + (None,)
        count, labels, stats, centres = cv2.connectedComponentsWithStats((paper > 0).astype(np.uint8), connectivity=4)
        for index in range(1, count):
            if only is not None and index not in only:
                continue
            x, y, wide, high, area = (int(value) for value in stats[index])
            cx, cy = float(centres[index][0]), float(centres[index][1])
            if through is not None and not through[y:y + high, x:x + wide][labels[y:y + high, x:x + wide] == index].any():
                continue      # a hole that no line cuts was looked at before
            most = HOLE_HEADS[1] * usual
            if is_open:
                # A head whose rim broke is often one that a hand drew large: its hole may be larger than the usual
                # hole of the page.
                most = OPEN_HEADS * space * space
            between = ()
            if paper is ragged and SLIT_BETWEEN and layers.get('head'):
                # A slit between two read hollow heads of one column: the head between them (SLIT_BETWEEN).
                beside = [other for other in heads if other['hollow'] and not other.get('thin')
                          and abs(other['cx'] - cx) <= SLIT_BETWEEN[1] * layers['head'][0]]
                over = [other for other in beside if SLIT_BETWEEN[2] * space <= cy - other['cy'] <= SLIT_BETWEEN[3] * space]
                under = [other for other in beside if SLIT_BETWEEN[2] * space <= other['cy'] - cy <= SLIT_BETWEEN[3] * space]
                if over and under and not any(abs(other['cy'] - cy) < SLIT_BETWEEN[2] * space for other in beside):
                    between = (over[0], under[0])
            if not (SLIT_BETWEEN[0] if between else HOLE_HEADS[0]) * usual <= area <= most:
                continue
            if paper is ragged:
                # Paper that is not quite round: the inside of a head by its own shape only (RAGGED_SLIT).
                if area > RAGGED_SLIT[3] * space * space or not _slit(labels[y:y + high, x:x + wide] == index):
                    continue
            elif paper is lean or paper is open_lean:
                pass          # two halves that lean apart: their shape was asked (HALVES_ACROSS)
            elif wide < HOLE_HEADS[2] * high:
                # A printed half note with a thin rim fills the gap between two staff lines: its inside is a slanted
                # oval that is as high as wide, and fills little of its box.
                if not (is_open and OPEN_ALONE and wide >= OPEN_SLANT[0] * high and area <= OPEN_SLANT[1] * wide * high):
                    continue
            if paper is not ragged and paper is not lean and paper is not open_lean and not HOLE_HEADS[3] <= area / (wide * high) <= HOLE_HEADS[4]:
                continue
            inside = [head for head in heads + out
                      if head['x0'] - 2 <= cx <= head['x1'] + 2 and head['y0'] - 2 <= cy <= head['y1'] + 2]
            if any(head.get('loop') and head['loop'][0] - 2 <= cx <= head['loop'][2] + 2
                   and head['loop'][1] - 2 <= cy <= head['loop'][3] + 2 for head in heads):
                continue      # a room of the loop of a flag
            second, toward = None, 0
            if paper is ragged and SLIT_BESIDE and layers.get('head'):
                # A slit far beside the inside of the hollow head that holds it: the second head of the mark (SLIT_BESIDE).
                for other in inside:
                    if other['hollow'] and not other.get('thin') and not other.get('from_hole') \
                            and other['x1'] - other['x0'] + 1 >= SLIT_BESIDE[0] * layers['head'][0]:
                        filled = (holes[other['y0']:other['y1'] + 1, other['x0']:other['x1'] + 1] > 0).astype(np.uint8)
                        own = np.nonzero(filled)[1]
                        if len(own) and abs(cx - other['x0'] - own.mean()) >= SLIT_BESIDE[1] * layers['head'][0] \
                                and cv2.connectedComponents(filled, connectivity=8)[0] - 1 <= SLIT_BESIDE[2]:
                            second, toward = other, (1 if other['x0'] + own.mean() > cx else -1)
            if inside if not is_open else any(head['hollow'] and head is not second and not any(head is other for other in between)
                                              for head in inside):
                continue
            staff = _staff_of(layers, cx, cy)
            if staff is None or cx < ends[staff] + 0.3 * space:
                continue
            place = pitch_place(layers['staves'][staff], cy)
            beyond = abs(place) > HOLE_HEADS[5]
            if beyond and not (HOLE_FAR and abs(place) <= HOLE_FAR):
                continue
            # A cell of the staff is as high as the gap between two staff lines. The hole of a head has its own rim there.
            # (A broken head that fills the gap has its hole open and round: the test of its box is enough for it.)
            gap = space - layers['staves'][staff]['thick']
            if high >= HOLE_CELL * gap and abs(place - (2 * round((place - 1) / 2) + 1)) <= 0.3 \
                    and not (is_open and area / (wide * high) <= OPEN_ROUND):
                continue
            # The paper between a flag and its stem lies at the far end of a stem. No head stands there.
            if any(abs(stem['x'] - cx) <= (wide / 2 + 0.5 * space) and abs(stem['end'] - cy) <= LOOP_NEAR * space
                   and abs(head['cy'] - cy) >= 1.5 * space for head in heads for stem in head['stems']):
                continue
            # The rim: at the left and at the right of the hole there is ink, and past it paper again.
            row = int(round(cy))
            band = ink[max(0, row - 1):row + 2].max(axis=0)
            if through is not None:
                # The middle of this hole lies in a line: its rim is the ink that is no staff line.
                band = layers['bare'][max(0, row - 1):row + 2].max(axis=0)
            closed = True
            for step, start in ((-1, x - 1), (1, x + wide)):
                column, seen = start, 0
                while 0 <= column < len(band) and band[column] and seen <= far:
                    column += step
                    seen += 1
                if seen == 0 or (seen > far and step != toward):      # (towards the other head of the mark the ink goes on)
                    closed = False
            if not closed:
                continue
            mark = {'x0': max(0, x - rim), 'x1': min(ink.shape[1] - 1, x + wide - 1 + rim), 'y0': max(0, y - rim),
                    'y1': min(ink.shape[0] - 1, y + high - 1 + rim), 'cx': cx, 'cy': cy}
            stems = [way for way in (_way(layers, mark, True, True), _way(layers, mark, False, False)) if is_stem(way, space)]
            head = {'x0': mark['x0'], 'y0': mark['y0'], 'x1': mark['x1'], 'y1': mark['y1'], 'cx': cx, 'cy': cy,
                    'staff': staff, 'place': place, 'hollow': True, 'hole': area / ((wide + 2 * rim) * (high + 2 * rim)),
                    'stems': stems, 'mark': None, 'from_hole': True, 'core': None, 'alt': None}
            if beyond and not stems:
                continue      # past the first ledger line only a head with a stem (HOLE_FAR)
            if is_open and OPEN_FLAT is not None and _open_flat(layers, labels[y:y + high, x:x + wide] == index, x, y):
                continue      # a cell along a staff line (see OPEN_FLAT)
            if is_open:
                # The pieces of the broken rim: the heads that were read in the box of this one. An open hole with
                # no such piece is the hook of a rest, or the paper between two signs.
                head['replaces'] = [other for other in heads if other is not second
                                    and mark['x0'] <= other['cx'] <= mark['x1'] and mark['y0'] <= other['cy'] <= mark['y1']]
                if OPEN_BESIDE:
                    # A piece of the rim whose middle lies just over or under that box (see OPEN_BESIDE).
                    beside = OPEN_BESIDE * space
                    head['replaces'] += [
                        other for other in heads
                        if other not in head['replaces'] and not other['hollow'] and not other.get('thin')
                        and other['y1'] - other['y0'] + 1 < OPEN_PIECE * layers['head'][1]
                        and mark['x0'] <= other['cx'] <= mark['x1']
                        and mark['y0'] - beside <= other['cy'] <= mark['y1'] + beside
                        and other['y0'] <= mark['y1'] and other['y1'] >= mark['y0']]
                head['open'] = True
                unison = False
                if UNISON_SLIT and paper is ragged and second is None and len(stems) == 1 and stems[0]['direction'] == 'down':
                    # A quarter note and a half note of two voices on one pitch, side by side (UNISON_SLIT).
                    whole = [other for other in head['replaces']
                             if other['y1'] - other['y0'] + 1 >= OPEN_PIECE * layers['head'][1] and not other.get('thin')]
                    if len(whole) == 1 and len(head['replaces']) == 1 and not whole[0]['hollow'] \
                            and abs(whole[0]['cy'] - cy) <= UNISON_SLIT[1] * space \
                            and whole[0]['cx'] < stems[0]['x'] < cx \
                            and [stem['direction'] for stem in whole[0]['stems']] == ['up'] \
                            and abs(whole[0]['stems'][0]['x'] - stems[0]['x']) <= UNISON_SLIT[0] * space:
                        unison = True
                    if UNISON_LOG is not None and whole:
                        UNISON_LOG.append({'cx': cx, 'cy': cy, 'area': area, 'wide': wide, 'high': high, 'fired': unison,
                                           'stem': (stems[0]['x'], stems[0]['end']),
                                           'whole': [(other['cx'], other['cy'], other['hollow'], other['x0'], other['x1'],
                                                      other['y0'], other['y1'],
                                                      [(stem['direction'], stem['x'], stem['end']) for stem in other['stems']])
                                                     for other in head['replaces']]})
                    if unison:
                        head['replaces'] = []
                        head['unison'] = True
                if second is not None:
                    if not stems:
                        stems = head['stems'] = [dict(stem) for stem in second['stems']]
                    elif len(second['stems']) > 1:
                        second['stems'] = [stem for stem in second['stems']
                                           if not any(stem['direction'] == way['direction'] and abs(stem['x'] - way['x']) <= 0.2 * space
                                                      for way in stems)] or second['stems']
                if not stems:
                    continue
                if not head['replaces'] and not unison:
                    if not OPEN_ALONE:
                        continue
                    y0, x0 = max(0, y - 3), max(0, x - 3)
                    own = (labels[y0:y + high + 3, x0:x + wide + 3] == index).astype(np.uint8)
                    ring = cv2.dilate(own, np.ones((7, 7), np.uint8)) & (1 - own)
                    if (ring & layers['bare'][y0:y + high + 3, x0:x + wide + 3]).sum() < OPEN_ALONE * ring.sum():
                        continue
                    if OPEN_STEM and any(
                            any(abs(way['x'] - bar) <= OPEN_STEM[0] * space for bar in (bars or {}).get(staff, []))
                            or any(sign['x0'] - 2 <= way['x'] <= sign['x1'] + 2
                                   and sign['y0'] - space <= cy <= sign['y1'] + space for sign in signs or []
                                   if not (OPEN_BESIDE and _in_head(sign, out)))
                            or any((not other['hollow'] or (SIDE_CELL and other.get('side_two')))
                                   and abs(stem['x'] - way['x']) <= OPEN_STEM[1] * space
                                   and abs(stem['end'] - way['end']) <= OPEN_STEM[2] * space
                                   for other in heads if not (OPEN_BESIDE and id(other) in pieces)
                                   for stem in other['stems'])
                            for way in stems):
                        if OPEN_ORDER and only is None:
                            again.setdefault(id(paper), (paper, set()))[1].add(index)
                        if OPEN_ORDER_SEEN is not None:
                            OPEN_ORDER_SEEN.append({'cx': cx, 'cy': cy, 'again': only is not None})
                        continue      # a stem that is not its own
                # A piece of rim is lower than a head. A whole head beside the paper is a note of its own: the paper
                # is closed in between two heads a second apart.
                if any(other['y1'] - other['y0'] + 1 >= OPEN_PIECE * layers['head'][1] and not other.get('thin')
                       for other in head['replaces']):
                    continue
            five = False
            if abs(place) > 4.6:
                # Beside the staff a head lies on its ledger lines. The letter p of the words has a bowl and a stem too.
                head['ledgers'] = ledger_lines(layers, layers['staves'][staff], head)
                if beyond:
                    # Every line between the staff and the head, at its step (HOLE_FAR).
                    lines = _step_rows(layers['staves'][staff], head, head['ledgers'], 1) \
                        or _narrow_ledgers(layers, layers['staves'][staff], head, 1)
                    if not lines:
                        continue
                    head['ledgers'] = lines
                found = ledger_place(layers, layers['staves'][staff], head)
                if beyond and found is not None and (round(found) % 2 == 0 or any(
                        band['x0'] <= cx <= band['x1'] and band['top'] <= cy <= band['bottom'] for band in layers.get('words') or [])):
                    continue      # on its second ledger line, or in the row of the words (see HOLE_FAR)
                if beyond and HOLE_FAR_SEEN is not None and found is not None:
                    HOLE_FAR_SEEN.append({'cx': cx, 'cy': cy, 'place': place, 'found': found, 'lines': head['ledgers'], 'open': is_open,
                                          'area': area, 'wide': wide, 'high': high, 'staff': staff,
                                          'stems': [(way['direction'], way['x'], way['end']) for way in stems],
                                          'replaces': [(o['cx'], o['cy']) for o in head.get('replaces', [])]})
                if found is None or not head['ledgers']:
                    if abs(place) > 5.5:
                        continue
                    if second is None:
                        if not HOLE_FIVE:
                            continue      # (the second head of a read mark is no letter, and needs no line next to the staff)
                        five = True
                    found = float(round(place)) if not five else (5.0 if place > 0 else -5.0)
                head['place'] = found
            if five:
                if high >= HOLE_FIVE[2] * space:
                    widths = (labels[y:y + high, x:x + wide] == index).sum(axis=1)
                    widths = widths if found < 0 else widths[::-1]
                    if int(np.argmax(widths)) <= HOLE_FIVE[1] * (high - 1) and widths.max() >= HOLE_FIVE[3] * wide:
                        continue
                if not stems and _between_strokes(layers, x, wide, cy, space):
                    continue
            if paper is lean or (five and stems):
                if not stems:
                    continue
                # A head right over or under this one that found the same stems: of two stems, one up and one down,
                # the upper head keeps the one that goes up and the lower head the one that goes down; a head with
                # two stems leaves this one the only stem that it found.
                same = lambda stem, way: stem['direction'] == way['direction'] and abs(stem['x'] - way['x']) <= 0.2 * space
                for other in heads:
                    if len(other['stems']) < 2 or abs(other['cx'] - cx) > 0.5 * space or abs(other['cy'] - cy) > 1.3 * space:
                        continue
                    if len(stems) == 1:
                        spare = [stem for stem in other['stems'] if stem['direction'] != stems[0]['direction']]
                        if spare and (other['cy'] < cy) == (stems[0]['direction'] == 'up') \
                                and any(same(stem, stems[0]) for stem in other['stems']):
                            # The one stem passes the other head on its way: it is that head's, and this one's is
                            # the stem at the other side (the upper head goes up, the lower one down).
                            other['stems'] = [stem for stem in other['stems'] if stem['direction'] == stems[0]['direction']]
                            stems = head['stems'] = spare[:1]
                        else:
                            other['stems'] = [stem for stem in other['stems'] if not same(stem, stems[0])]
                    elif {way['direction'] for way in stems} == {'up', 'down'} \
                            and all(any(same(stem, way) for stem in other['stems']) for way in stems):
                        upper = cy < other['cy']
                        stems = head['stems'] = [way for way in stems if (way['direction'] == 'up') == upper]
                        other['stems'] = [stem for stem in other['stems'] if (stem['direction'] == 'up') != upper]
                if five and {way['direction'] for way in stems} == {'up', 'down'}:
                    # A head of the staff that this one touches, read before or in this step, has a stem that passes
                    # this head: this head keeps the stem at its own side, away from the staff, and the other head
                    # leaves it that stem.
                    outer = 'up' if found > 0 else 'down'
                    touching = [other for other in heads + out if abs(other['cx'] - cx) <= 0.5 * space
                                and 0 < (other['cy'] - cy) * (1 if found > 0 else -1) <= 1.3 * space
                                and any(same(stem, way) for stem in other['stems'] for way in stems)]
                    if touching:
                        stems = head['stems'] = [way for way in stems if way['direction'] == outer]
                        for other in touching:
                            if len(other['stems']) >= 2:
                                other['stems'] = [stem for stem in other['stems'] if stem['direction'] != outer]
            if HOLE_SHARE and {way['direction'] for way in stems} == {'up', 'down'}:
                # Two voices a third apart, one over the other: the upper with its stem up at its right, the lower with
                # its stem down at its left. A stroke runs along the sides of both heads, so each head finds the other's
                # stem too, and a head that was read first kept the wrong one (HOLE_SHARE).
                same = lambda stem, way: stem['direction'] == way['direction'] and abs(stem['x'] - way['x']) <= 0.2 * space
                rim_pieces = {id(piece) for piece in head.get('replaces', [])} | pieces
                for other in heads + out:
                    if other is head or id(other) in rim_pieces or not other.get('hollow') or len(other['stems']) != 1 \
                            or abs(other['cx'] - cx) > 0.5 * space \
                            or not 0.7 * space <= abs(other['cy'] - cy) <= 1.3 * space:
                        continue
                    one = other['stems'][0]
                    if not any(same(one, way) for way in stems):
                        continue
                    if _ink_past(ink, x, y, wide, high, other['cy'] > cy) > HOLE_SHARE * space:
                        break      # paper under a filled head, closed by a flag (see HOLE_SHARE)
                    if one['direction'] == ('down' if other['cy'] < cy else 'up'):
                        # The other head's one stem passes this head on its way: it is this head's, and the other way
                        # is the other head's.
                        other['stems'] = [dict(way) for way in stems if way['direction'] != one['direction']]
                        stems = head['stems'] = [way for way in stems if way['direction'] == one['direction']]
                    else:
                        # The other head's one stem leaves it away from this head: this head passed it on its way.
                        stems = head['stems'] = [way for way in stems if way['direction'] != one['direction']]
                    if HOLE_SHARE_SEEN is not None:
                        HOLE_SHARE_SEEN.append({'cx': cx, 'cy': cy, 'other': (other['cx'], other['cy'], other.get('thin', False),
                                                bool(other.get('from_hole'))), 'staff': staff})
                    break
            out.append(head)
            if paper is open_lean and OPEN_THROUGH_LOG is not None:
                OPEN_THROUGH_LOG.append((round(cx), round(cy), area, wide, high, staff))
            pieces.update(id(other) for other in head.get('replaces', []))
    if OPEN_BESIDE:
        # Two open heads of a chord, one over the other, found the same two stems, one that goes up and one that
        # goes down: the upper head keeps the stem that goes up, the lower one the stem that goes down.
        found = [head for head in out if head.get('open') and len(head['stems']) == 2]
        for upper, lower in ((upper, lower) for upper in found for lower in found):
            if 0 < lower['cy'] - upper['cy'] <= 1.3 * space and abs(lower['cx'] - upper['cx']) <= 0.5 * space \
                    and len(lower['stems']) == 2 and len(upper['stems']) == 2 \
                    and {stem['direction'] for stem in upper['stems']} == {'up', 'down'} \
                    and all(any(stem['direction'] == other['direction'] and abs(stem['x'] - other['x']) <= 0.2 * space
                                for other in lower['stems']) for stem in upper['stems']):
                upper['stems'] = [stem for stem in upper['stems'] if stem['direction'] == 'up']
                lower['stems'] = [stem for stem in lower['stems'] if stem['direction'] == 'down']
    return out


def _between_strokes(layers: dict, x: int, wide: int, cy: float, space: float) -> bool:
    """Whether ink stands at both sides of the rim of a head without a stem whose inside spans the columns from x on
    (wide columns), within HOLE_FIVE[0] staff spaces past the rim, in the rows of the head's middle (no staff line)."""
    free = layers['free']
    rows = free[max(0, int(cy - 0.15 * space)):int(cy + 0.15 * space) + 1]
    for way, edge in ((-1, x), (1, x + wide - 1)):
        column, rim, paper, found = edge + way, True, 0, False
        while 0 <= column < rows.shape[1]:
            dark = bool(rows[:, column].any())
            if rim and dark:
                column += way
                continue
            rim = False
            if dark:
                found = True
                break
            paper += 1
            if paper > HOLE_FIVE[0] * space:
                break
            column += way
        if not found:
            return False
    return True


# ----------------------------------------------------------------------------------------------------------------
# Heads that a hand drew as one thin stroke

THIN_WIDE = (0.55, 2.6)    # the width of a head drawn as one stroke, in staff spaces
THIN_HIGH = (0.2, 1.3)     # and its height
THIN_NEAR = 1.3            # the head lies at most this many staff spaces from the end of its stem
THIN_HOLLOW = 0.15         # such a head is hollow when its ink goes around this share of its box
THIN_OPEN = True           # the paper that the rim of such a head closes in when a small break of the rim is closed (the
                           # open holes of the layers; with the line through the head as large as OPEN_HOLE, and
                           # with the rim of OPEN_RIM) is its inside too, from the same share: a printed oval whose
                           # inside is too narrow for the loop, on a ledger line that is faint in it
LOOP_LINE = True           # an open oval may have a staff line as its upper or lower side
OPEN_HOLE = 0.12           # the open hole of such a head has at least this area, in staff spaces squared (0: off)
TWO_STEMS = True           # a thick head with two stems may give one of them to a thin head of the other voice
TWO_ALONG = 1.0            # that thin head hangs anywhere on the stem, up to this many staff spaces before its far end (0: off)
TWO_APART = True           # and it may touch the thick head: the thick head's own ink is no part of it
THIN_LEDGER = 0.3          # a ledger line is at most this thick, in staff spaces: a thin head on it is higher (0: off)
LINE_REST = 0.6            # a piece no higher than a staff line is a rest of the line when less than this share is its own ink (0: off)
ONE_ALONG = 1.0            # on the one stem of a thick head too, when it lies this many staff spaces from that head (0: off)
ALONG_HIGH = 0.4           # such a thin head is at least this high, in staff spaces: the rest of a staff line is flat
ALONG_HOOK = True          # a hairline flag at the stem's end (a hook, see count_tails) keeps such a head off that stem too
OPEN_RIM = 0.5             # an open hole has the head's own ink at this share of its rim (0: off)
THIN_RING = (0.05, 0.2, 0.6, 1.2, 0.85, 0.85, 0.8, 1.25)   # a head that is read from its stem and whose ink shows no inside: a
#                            pale print leaves the ring of a half note open in two places, and the piece at the stem's end
#                            is one arc of it. The paper that the thin ink and the stems close in around the piece, when
#                            breaks of 0.35 staff spaces are closed, is the inside of a printed half note: this much of it,
#                            in staff spaces squared, stays paper after the closing; it is this large at least; from this
#                            to this wide and high, in staff spaces; this share of its hull; ink at this share of its
#                            rim; and its width is from this to this of its height (a hand's stroke beside a line and
#                            the cell between two staff lines are long and low). The head is hollow then, and it stands
#                            where the ring stands. A census of every head read from a stem on LitChoir's scan pages
#                            (3,189, round 81): five pass that the scorer lines up with a typed half note, none with a
#                            typed quarter or eighth note. The head becomes the ring only after the hollow heads were
#                            read from their insides (ring_heads): made hollow at once, it stood in the way of that
#                            step on three pages, where a head that is read from its inside kept one of its two stems.
#                            None: off
LOOP_STEM = True           # an open oval may have its stem as one of its sides
THROUGH_SLANT = (0.5, 1.0) # a thin head that crosses a staff line at a low slant: its part over the line stands up to this
#                            many staff spaces right of its part under the line, and each part is at most this wide and
#                            high (None: off)
THIN_INSIDE = 0.5          # when the stem runs inside the piece of ink of a thin head, the head's middle lies up to this
#                            share of the piece's height before the stem's end (0: off)
THIN_BACK = 0.25           # the middle of a thin head lies at most this many staff spaces before the end of its stem
LOOP_BACK = 0.5            # the middle of an open oval lies up to this share of its height before the end of its stem
LINE_HALF = (0.25, 0.05, 1.5)   # a printed half note on a staff line whose rim the copy broke where the line crosses
#                            it and once more at that side: the inside under (or over) the line is open to the paper,
#                            and only the half at the other side is an open hole, too small for OPEN_HOLE. The piece of
#                            the rim reaches this many staff spaces past the line at each side; the open paper in its
#                            box lies at one side of the line only and along it, is this many staff spaces squared at
#                            least, and is this many times as wide as high; and the stem stands beside the piece, not
#                            in it. The piece is then an open oval (LOOP_BACK) and hollow. A census of every head that
#                            the rule's first form gave on LitChoir's pages (22, each looked at): the hook of a quarter
#                            rest, whose own stroke runs through the piece (9), a hand's flag beside its stem, whose
#                            paper lies along the next line, filled heads with a stem through them, and a worn filled
#                            head of a grey copy whose speck stands upright (0.88 as wide as high; the true insides
#                            1.6 and 1.86, and 1.0 at a half note that a later step reads hollow anyway). The rule acts
#                            at the one printed half note that no finder read (memorial-troparia pg0284) and at one
#                            half note that a later step read hollow too. A rule for one case. (None: off)
LINE_HALF_SEEN = None      # a list: each head that a piece of LINE_HALF gives
THIN_STEM = 1.6            # the stem of such a head is at least this many staff spaces long
THIN_SPECKS = 0.3          # and it has ink of its own in at least this share of its rows outside the staff lines and the
#                            rows of the head: a weak copy joins a thin stroke over small gaps, and so a column of ink
#                            specks over a printed mark, which was read as a head with a stem (a flat block in the bass
#                            staff of a scan of nativity-troparion, 0.24). Of the 2,908 thin heads of LitChoir's pages
#                            that a stroke of its own gives, that one is under 0.4, the next two have 0.41 (no note) and
#                            0.43 (a true note); the fresh set's 166 have 0.8 or more. A rule for one case (None: off)
STEM_THROUGH = None        # off. (0.7, 1.5, 0.2): a mark with no stem, from this to this many times as wide and as high as the
#                            heads of the page, has the stem of the head right over or under it that was cut from the
#                            same piece of ink (a piece of two marks, one column), when it lies between that head and
#                            the stem's end and the stroke does not go on this many staff spaces past the other side
#                            of that head. Off: counted in three forms on LitChoir. For any mark of the piece it gained
#                            24 notes and lost 34 (the head of an eighth note that a hand drew takes the stem of its
#                            flag and is a quarter, a rest, a sharp and the sign of cut time become notes); for a stem
#                            too short to be found from the mark itself it lost as many; in this form it gained 11 and
#                            lost 5 (on the clean copies 1 and 2) and wrote 31 notes that are not there: two whole
#                            notes that touch are read as half notes, the sharps of a key signature as notes.
FLAT_HEAD = 0.8            # a filled mark with upright ink over its left half is no flat when that ink is the other mark of
#                            its piece of ink (a piece of two marks: the end bar of a hymn is cut into more), right
#                            over it and this share of its width or more, and the mark is this share of the page's head
#                            or more: two heads a third apart that the print let run together (0: off)
FLAT_STEM = 0.35           # a filled mark as large as a head (FLAT_HEAD of the page's head) is no flat either when the
#                            upright ink over its left half is the stem that comes down from a head over it: that stem
#                            stands at most this many staff spaces from the stroke and ends at the mark. The lower head
#                            of a chord whose stem a faint print breaks under it; it shares that stem. (0: off)
LOST_STEM = (0.3, 0.45)    # a stem that the copy cut from its thick head stands at most this far past the head's edge
                           # (staff spaces, sideways) and ends at most this far from the head (None: off)
LOST_ALONE = (0.4, 0.6)    # the same for a mark with no stem at all: it lost its only stem, and the cut may be wider
LOST_THROUGH = 0.6         # the stroke of a mark with no stem at all may run on for this many staff spaces past the far
#                            edge of the mark, when it is as long as a stem (THIN_STEM) before the mark: a bold slur begins
#                            at the head, and the stroke goes on into it (0: off)
LOST_SHARED = 0.5          # a head that gets such a stem shares it with a mark of its own piece of ink that has no stem
#                            and stands at the far side of it from the stem, its middle at most this many staff spaces
#                            sideways: two heads a third apart that the print let run together (0: off)
STEM_GONE = (0.85, 1.1, 0.8, 1.08, 0.25, 0.5, 0.6, 0.87, 0.1)   # a filled mark with no stem at all is still a
#                            note where it is the head of the print alone: from this to this many times as wide and
#                            from this to this many times as high as the heads of the page; a slanted oval (of its
#                            four corners, each three tenths of its box, the upper left and the lower right hold thick
#                            ink in at most this share and the other two in at least this share, and the box from
#                            this to this share); with paper around it (ink in at most the last share of a frame of
#                            0.3 staff spaces around the box, staff lines apart: a ledger line fits in). A scan that
#                            lost the hairline stems of a print. A rest is a box, a dot is round, the end of a slur
#                            is slim, and the two halves of a quarter rest are one piece of ink. (None: off)
GONE_SPACE = (0.35, 2.6)   # a filled mark with no stem that is higher than STEM_GONE allows is still such a head where it
#                            fills its space: its top and its bottom lie in the rows of the two staff lines of the space
#                            (half a line's thickness and 2 pixels). One print draws its heads in a space from line to
#                            line, and its box reaches through both lines (1.25 to 1.39 of the page's heads, as the
#                            page's read heads in a space with stems are). A heavy sharp or natural fills its space in
#                            the same way and stands before its head: no read head stands at its right within the second
#                            number of staff spaces with its middle within the first number of the mark's middle. A
#                            census of every stemless filled mark of LitChoir's pages that only the height refused (21,
#                            each looked at): the 6 of the Rachmaninov print and a head of a copy by hand fill their
#                            space; the 3 signs do too and stand 1.2 to 2.28 staff spaces before their heads, their
#                            middles 0.14 to 0.23 apart; the true heads have no head within 2.98 staff spaces at their
#                            height, and the nearer ones stand 0.46 staff spaces or more higher or lower. A rule for one
#                            print. (None: off)
GONE_SPACE_SEEN = None     # a list: each mark that GONE_SPACE lets through
GONE_STEM = (0.25, 4.5, 1.5, 0.9, 1.6, 1.2, 0.3, 0.2, 1.0)   # the pieces that the scan left of such a stem, in the column
#                            of the head's right edge over it or of its left edge under it (this many staff spaces to
#                            both sides), up to this many staff spaces from the head and not into the words: slim ink
#                            that begins at most the third number from the head, in rows that add up to the fourth
#                            number at least, the farthest of them the fifth number from the head or more (a stem in
#                            dashes, a stem that begins after a gap); or wide ink from the sixth number on (a beam, a
#                            flag) with slim rows of the seventh number before it. The stem ends there, and its flags
#                            and beams are counted as those of any stem. Pieces at one side only, and at the other
#                            side no slim ink on the head itself (it begins at most the eighth number from the head and
#                            has rows of the seventh number in the first staff spaces of the last number): the hand
#                            that draws short stems leaves the stem of the next note in the other column. (None: such
#                            a head has no stem and is a quarter note)
THROUGH_SIDE = 0.05        # a thin head that crosses a staff line is one piece: its ink over and under the line is joined
                           # through the line, up to this many staff spaces sideways
LEAN_END = 0.4             # a stem that leans toward its thin head: the head's distance is counted from the stem's end, when
#                            that end lies at most this many staff spaces from the stem's middle column (0: off)
THIN_PAIR = 1.3            # two thin heads, one over the other: the stem of the one runs on into the other, so its own
                           # head lies up to this many staff spaces before the stroke's end (0: off)
LOST_OWN = 0.35            # a stroke is another head's own stem where it stands within this many staff spaces of that stem's
#                            middle column and leaves that head the same way. The column that a stem is stored with is
#                            that of its far end, and a stem that was followed into a beam or that leans ends beside its
#                            own stroke there: the stroke then looked like a stem that no head has, and the head past
#                            the stem's own head got it as the stem that the copy cut from it (two voices a third apart
#                            in one column: the upper head with its stem up was read for the lower voice too, with the
#                            stem down of the head under it). Only for a head that has a stem: a mark with no stem at
#                            all is the next head of a chord on that stem as often as not, and where the stroke has a
#                            head at each of its ends (a flag that was read as a head) the stem says nothing. (0: off)


LOST_PAST = 0.25           # a stroke that no head has is the stem of the head whose rows hold its near end, where it passes that
#                            head on its way to the head that lost_stems() chose: two voices a third apart whose heads touch,
#                            the upper with its stem up at its right and the lower with its stem down at its left. Each head
#                            followed the other's stem through the ink of both, and the stroke that was left went to the
#                            head past it, so that the two voices crossed. The stroke stands within this many staff spaces
#                            of the head's sides, and the head has no stem that way. A census at the step on every page of
#                            LitChoir and of the fresh set: 7 strokes and 4, each looked at, all of that shape. (None: off)


def _across(heads: list[dict], x: float, top: float, bottom: float, space: float) -> bool:
    """Whether an upright stroke is the stem of two heads that overlap across their stems (PAIR_OVER). The stem up
    and the stem down of such a pair are one stroke through both heads, and each head followed its own stem from
    its own side: the stroke stands between the two stems that were followed, and it is no stem without a head."""
    return any(head.get('across') and head['x0'] - 0.15 * space <= x <= head['x1'] + 0.15 * space
               and min(head['cy'], stem['end']) - 0.5 * space <= bottom and top <= max(head['cy'], stem['end']) + 0.5 * space
               for head in heads for stem in head['stems'])


def lost_stems(layers: dict, heads: list[dict], bars: dict[int, list[float]], ends: list[float],
               orphans: list[dict] | None = None) -> int:
    """Gives a thick head the stem that the copy cut from it: an upright stroke that no head has, and that ends
    close over the head at its right edge (a stem up) or close under it at its left edge (a stem down). A head that
    already has a stem to the other side becomes the head of both voices; thin_heads() then looks along its stems
    for the other voice's own head. `orphans` are marks as large as a head that have no stem at all: one that gets
    a stem here is a head, and it is added to `heads`. Returns how many stems were given."""
    if not LOST_STEM:
        return 0
    space = layers['space']
    used = [(stem['x'], min(head['cy'], stem['end']), max(head['cy'], stem['end'])) for head in heads for stem in head['stems']]
    # The stems whose middle column is not the column that they are stored with (LOST_OWN).
    own = [(stem['mid'], min(head['cy'], stem['end']), max(head['cy'], stem['end']), stem['direction'])
           for head in heads for stem in head['stems'] if stem.get('mid') is not None and stem['mid'] != stem['x']] if LOST_OWN else []
    strokes = [stroke for stroke in layers['strokes'] if stroke['slim'] and stroke['y1'] - stroke['y0'] + 1 >= THIN_STEM * space]
    given = 0
    for stroke in strokes:
        x, top, bottom = stroke['x'], stroke['y0'], stroke['y1']
        staff = _staff_of(layers, x, (top + bottom) / 2)
        if staff is None or x <= ends[staff] + 0.3 * space:
            continue
        if any(abs(x - bar) <= 0.4 * space for bar in bars.get(staff, [])):
            continue
        if any(abs(x - other) <= 0.35 * space and first - 0.5 * space <= bottom and top <= last + 0.5 * space
               for other, first, last in used):
            continue
        if _across(heads, x, top, bottom, space):
            continue
        # A sharp and a natural have two upright strokes side by side.
        if any(other is not stroke and abs(other['x'] - x) <= 0.9 * space
               and min(other['y1'], bottom) - max(other['y0'], top) >= 0.5 * min(other['y1'] - other['y0'], bottom - top)
               for other in strokes):
            continue
        best = None
        for head in heads + [orphan for orphan in orphans or [] if not orphan['stems']]:
            if head['staff'] != staff or head.get('thin'):
                continue
            ways = []
            # The stroke of a mark with no stem at all may run on past the mark for a little: a slur or a tie begins
            # at the head there, and the stroke was followed into it (LOST_THROUGH).
            on = LOST_THROUGH * space if LOST_THROUGH and not head['stems'] else None
            if not any(stem['direction'] == 'up' for stem in head['stems']) \
                    and (bottom <= head['cy'] or (on is not None and bottom <= head['y1'] + on
                                                 and top <= head['y0'] - THIN_STEM * space)):
                ways.append(('up', x - head['x1'], head['y0'] - bottom, top))
            if not any(stem['direction'] == 'down' for stem in head['stems']) \
                    and (top >= head['cy'] or (on is not None and top >= head['y0'] - on
                                               and bottom >= head['y1'] + THIN_STEM * space)):
                ways.append(('down', head['x0'] - x, top - head['y1'], bottom))
            # A mark with no stem at all has lost its only stem: the cut may be wider there.
            reach = LOST_ALONE if LOST_ALONE and not head['stems'] else LOST_STEM
            for direction, aside, apart, end in ways:
                if -0.25 * space <= aside <= reach[0] * space and apart <= reach[1] * space:
                    far = abs(aside) + max(0.0, apart)
                    if best is None or far < best[0]:
                        best = (far, head, direction, end)
        if best and LOST_PAST:
            _, head, direction, end = best
            past = [other for other in heads if other is not head and other['staff'] == staff and not other.get('thin')
                    and not any(stem['direction'] == direction for stem in other['stems'])
                    and other['x0'] - LOST_PAST * space <= x <= other['x1'] + LOST_PAST * space
                    and ((direction == 'up' and other['cy'] < head['cy'] and top < other['y0'] <= bottom <= other['y1'])
                         or (direction == 'down' and other['cy'] > head['cy'] and other['y0'] <= top <= other['y1'] < bottom))]
            if len(past) == 1:
                best = (best[0], past[0], direction, end)
        if best and best[1]['stems'] and any(abs(x - other) <= LOST_OWN * space and first - 0.5 * space <= bottom
                                             and top <= last + 0.5 * space and way == best[2] for other, first, last, way in own):
            stroke['owned'] = True                     # the stem of the head between: thin_heads() leaves it too
            continue
        if best:
            _, head, direction, end = best
            if not any(head is other for other in heads):
                heads.append(head)
            head['stems'].append({'direction': direction, 'x': int(round(x)), 'end': int(end), 'length': abs(head['cy'] - end),
                                  'lost': True})
            used.append((x, min(head['cy'], end), max(head['cy'], end)))
            given += 1
            for other in orphans or [] if LOST_SHARED else []:
                # The two heads of a chord were one piece of ink, and the stem that the copy cut off is the stem of both.
                if other is not head and not other['stems'] and other['staff'] == staff and other.get('blob') is not None \
                        and other.get('blob') == head.get('blob') and abs(other['cx'] - head['cx']) <= LOST_SHARED * space \
                        and (other['cy'] > head['cy']) == (direction == 'up') and not any(other is known for known in heads):
                    heads.append(other)
                    other['stems'].append({'direction': direction, 'x': int(round(x)), 'end': int(end),
                                           'length': abs(other['cy'] - end), 'lost': True})
                    used.append((x, min(other['cy'], end), max(other['cy'], end)))
                    given += 1
    return given


def _gone_stem(layers: dict, head: dict, up: bool) -> tuple[dict | None, bool]:
    """The stem of a head whose stem the scan lost, from the pieces that it left (GONE_STEM): a stem as lost_stems()
    gives it, or None; and whether slim ink hangs on the head at this side (a short stem that is still there)."""
    space = layers['space']
    free = layers['free']
    height, width = free.shape
    x = int(round(head['x1'] if up else head['x0']))
    band = int(round(GONE_STEM[0] * space))
    first, last = max(0, x - band), min(width - 1, x + band)
    edge = head['y0'] - 1 if up else head['y1'] + 1
    def run(row: int) -> tuple[int, int] | None:
        cells = np.nonzero(free[row, first:last + 1])[0]
        if not len(cells):
            return None
        left, right = first + int(cells[0]), first + int(cells[-1])
        while left > 0 and free[row, left - 1]:
            left -= 1
        while right < width - 1 and free[row, right + 1]:
            right += 1
        return left, right
    bands = [band for band in layers.get('words') or [] if band['x0'] <= x <= band['x1']]
    slim, near, far, end, close = 0, None, None, None, 0
    for step in range(int(round(GONE_STEM[1] * space))):
        row = edge - step if up else edge + step
        if not 0 <= row < height or any(band['top'] - 0.3 * space <= row <= band['bottom'] + 0.3 * space for band in bands):
            break
        found = run(row)
        if found is None:
            continue
        if found[1] - found[0] + 1 <= SLIM_STEM * space:
            slim += 1
            near, far = step if near is None else near, step
            if near > GONE_STEM[2] * space:
                break
            close += step <= GONE_STEM[8] * space
            continue
        if step < GONE_STEM[5] * space:
            continue        # the rim of the head itself, a ledger line
        if slim >= GONE_STEM[6] * space:
            end = row
        break
    if near is None or near > GONE_STEM[2] * space:
        return None, False
    attached = near <= GONE_STEM[7] * space and close >= GONE_STEM[6] * space
    if end is None and slim >= GONE_STEM[3] * space and far >= GONE_STEM[4] * space:
        end = edge - far if up else edge + far
    if end is None:
        return None, attached
    return {'direction': 'up' if up else 'down', 'x': x, 'end': int(end), 'length': abs(head['cy'] - end), 'lost': True,
            'gone': True}, attached


def _fills_space(layers: dict, head: dict, heads: list[dict]) -> bool:
    """GONE_SPACE: the mark's top and bottom lie in the rows of the two staff lines of its space, and no read head
    stands close at its right at its height, as the head of a sign does."""
    if not GONE_SPACE:
        return False
    staff = _staff_of(layers, head['cx'], head['cy'])
    if staff is None:
        return False
    rows, edge = layers['staves'][staff]['rows'], layers['staves'][staff]['thick'] / 2 + 2
    if not any(abs(head['y0'] - over) <= edge and abs(head['y1'] - under) <= edge for over, under in zip(rows, rows[1:])):
        return False
    space = layers['space']
    level, reach = GONE_SPACE
    return not any(other is not head and 0 < other['cx'] - head['cx'] <= reach * space
                   and abs(other['cy'] - head['cy']) <= level * space for other in heads)


def gone_stems(layers: dict, heads: list[dict], orphans: list[dict], marks: list[dict]) -> list[dict]:
    """The marks as large as a head that have no stem at all and that are heads of the print all the same
    (STEM_GONE): the scan lost their stems. They are notes without a stem: a quarter note, in the voice that the
    notes of their column leave free."""
    if not STEM_GONE:
        return []
    space = layers['space']
    wide, high = layers['head']
    reach = int(round(0.3 * space))
    found = []
    for head in orphans:
        if head['stems'] or head['hollow'] or any(head is other for other in heads):
            continue
        own_wide, own_high = head['x1'] - head['x0'] + 1, head['y1'] - head['y0'] + 1
        if not STEM_GONE[0] * wide <= own_wide <= STEM_GONE[1] * wide or own_high < STEM_GONE[2] * high:
            continue
        filling = own_high > STEM_GONE[3] * high
        if filling and not _fills_space(layers, head, heads):
            continue
        if any(other['x0'] <= head['cx'] <= other['x1'] and other['y0'] <= head['cy'] <= other['y1'] for other in heads):
            continue
        # One piece of ink with another mark: the halves of a quarter rest, a number, a letter.
        if any(number != head['mark'] and other['blob'] == head['blob'] and other['kind'] is not None
               for number, other in enumerate(marks)):
            continue
        part = layers['thick'][head['y0']:head['y1'] + 1, head['x0']:head['x1'] + 1] > 0
        rows, columns = max(1, int(round(0.3 * own_high))), max(1, int(round(0.3 * own_wide)))
        if max(part[:rows, :columns].mean(), part[-rows:, -columns:].mean()) > STEM_GONE[4] \
                or min(part[:rows, -columns:].mean(), part[-rows:, :columns].mean()) < STEM_GONE[5] \
                or not STEM_GONE[6] <= part.mean() <= STEM_GONE[7]:
            continue
        free = layers['free']
        around = free[max(0, head['y0'] - reach):head['y1'] + 1 + reach, max(0, head['x0'] - reach):head['x1'] + 1 + reach]
        inside = free[head['y0']:head['y1'] + 1, head['x0']:head['x1'] + 1]
        if (float(around.sum()) - float(inside.sum())) > STEM_GONE[8] * max(1, around.size - inside.size):
            continue
        head['gone'] = True
        if filling and GONE_SPACE_SEEN is not None:
            GONE_SPACE_SEEN.append({'cx': head['cx'], 'cy': head['cy'], 'high': own_high, 'page_high': high})
        if GONE_STEM:
            (over, on_top), (under, on_foot) = _gone_stem(layers, head, True), _gone_stem(layers, head, False)
            # Pieces at one side only, and no short stem at the other side: the ink in a column can be another note's.
            if over and not under and not on_foot:
                head['stems'].append(over)
            elif under and not over and not on_top:
                head['stems'].append(under)
        found.append(head)
    return found


def chord_stems(layers: dict, heads: list[dict], orphans: list[dict]) -> list[dict]:
    """The filled marks as large as a head that have no stem and stand where the stem of a read head begins, as the
    next head of its chord stands (CHORD_STEM): past the read head at the end that its stem does not leave from
    (under the head of a stem up, over the head of a stem down), with the stem's column at the mark's edge (the
    right edge at a stem up, the left edge at a stem down) and little paper between the two. The scan cut the
    stem between them, the mark's ink hides it, or the mark is the other voice's note and its own hairline stem
    is lost: the notes of one column sound together. Such a mark is a head of that stem. A mark along the stem
    is not taken: a sharp, the bowl of a flat and a letter stand there as often as a head. Called after
    gone_stems(), which keeps the heads that it reads by their own shape."""
    if not CHORD_STEM:
        return []
    space = layers['space']
    wide, high = layers['head']
    found = []
    for mark in orphans:
        if mark['stems'] or mark['hollow'] or any(mark is other for other in heads):
            continue
        own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
        if not (CHORD_STEM[0] * wide <= own_wide <= CHORD_STEM[1] * wide
                and CHORD_STEM[2] * high <= own_high <= CHORD_STEM[3] * high):
            continue
        if any(other['x0'] <= mark['cx'] <= other['x1'] and other['y0'] <= mark['cy'] <= other['y1']
               for other in heads):
            continue
        # Paper that the mark closes in: a whole note on a ledger line, whose inside the line cuts into two slivers.
        paper = (layers['ink'][max(0, mark['y0'] - 2):mark['y1'] + 3,
                               max(0, mark['x0'] - 2):mark['x1'] + 3] == 0).astype(np.uint8)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
        open_ = set(labels[0]) | set(labels[-1]) | set(labels[:, 0]) | set(labels[:, -1])
        closed = sum(int(stats[index][4]) for index in range(1, count) if index not in open_)
        if closed > CHORD_STEM[7] * space * space:
            continue
        best = None
        for head in heads:
            if head['staff'] != mark['staff'] or (not CHORD_GONE and (head.get('thin') or head.get('gone'))):
                continue
            for stem in head['stems']:
                up = stem['direction'] == 'up'
                aside = stem['x'] - mark['x1'] if up else mark['x0'] - stem['x']
                if not -CHORD_STEM[4] * space <= aside <= CHORD_STEM[5] * space:
                    continue
                # A hollow head near the far end of a stem that it shares is taken for the loop of a flag
                # (without_flag_loops): on so short a stem a filled mark is not given the stem of a hollow head.
                if head['hollow'] and abs(head['cy'] - stem['end']) <= LOOP_NEAR * space:
                    continue
                if up and mark['cy'] > head['cy']:
                    apart = max(0.0, mark['y0'] - head['y1'])
                elif not up and mark['cy'] < head['cy']:
                    apart = max(0.0, head['y0'] - mark['y1'])
                else:
                    continue
                if apart <= CHORD_STEM[6] * space and (best is None or apart + abs(aside) < best[0]):
                    best = (apart + abs(aside), stem)
        if best:
            stem = best[1]
            mark['stems'].append({'direction': stem['direction'], 'x': stem['x'], 'end': stem['end'],
                                  'length': abs(mark['cy'] - stem['end']), 'lost': True})
            mark['chord_stem'] = True
            found.append(mark)
    return found


def _loop(part: np.ndarray, space: float) -> float:
    """The share of a thin piece's box that its ink goes around. A hand draws a half note as a thin oval, and the
    copy or the staff line breaks the oval, so its inside is no closed hole. The breaks are closed first; then the
    paper that the ink closes in is counted. A stroke closes in nothing."""
    size = int(max(3, round(0.35 * space))) | 1
    pad = size
    mask = np.pad(part.astype(np.uint8), pad)
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    outside = (1 - closed).astype(np.uint8)
    cv2.floodFill(outside, None, (0, 0), 2)
    return float((outside == 1).sum()) / max(1, part.shape[0] * part.shape[1])


F_SIGN = (0.15, 2.7, 0.3, 1.5)   # the letter f of the dynamics (f, ff, mf) or of words in italics is no stem with a head: its
#   stroke leans (its top stands this many staff spaces or more to the right of its foot), is at most the second number
#   of staff spaces high, and has a crossbar (ink that reaches the third number of staff spaces to both sides, in a row
#   of its middle three fifths). The hook at its end was read as a thin head beside the staff, where it stands close
#   to the outer line. A note there with no ledger line has nothing across its stem. (A census of every head read from
#   a stroke on LitChoir's pages, 3,448: the 12 strokes of this shape beside the staff are all such letters, 11 of the
#   dynamics on two clean scores and one of the words; they lean from 0.21 and the other short strokes with ink across
#   them up to 0.11, and the stems that lean with ink across them are 3.8 staff spaces high or more.) Two such letters
#   side by side, at most the last number of staff spaces apart and with one crossbar, close paper in between them
#   (without_f_marks). One stroke of this shape at a head on a ledger line is the short stem of a note by hand: it
#   leans, and the ledger line lies across it. None: off


def _f_cross(stroke: dict, space: float) -> list[int]:
    """The rows of the crossbar of an upright stroke of the layers that has the shape of the letter f (F_SIGN); none
    where it has not."""
    if not F_SIGN:
        return []
    xs = stroke['xs']
    high = len(xs)
    if high > F_SIGN[1] * space or high < 5:
        return []
    fifth = max(1, high // 5)
    if float(np.mean(xs[:fifth]) - np.mean(xs[-fifth:])) < F_SIGN[0] * space:
        return []
    rows = np.nonzero((stroke['left'] >= F_SIGN[2] * space) & (stroke['right'] >= F_SIGN[2] * space))[0]
    return [int(stroke['y0'] + row) for row in rows if 0.2 * high <= row <= 0.8 * high]


def _f_stroke(stroke: dict, space: float) -> bool:
    """Whether an upright stroke of the layers has the shape of the letter f (F_SIGN)."""
    return bool(_f_cross(stroke, space))


STEM_ARC = (0.35, 0.5)      # a stem is straight. The stroke of a head that is read from its stem (thin_heads) is followed
#   row by row from its middle, as far as slim ink goes, past its end too, and without the rows at its head. Where that
#   way bends off a straight line by the first number of staff spaces or more as one bow (a parabola fits it within the
#   second number, as a share of the bend, and each half of the way bends as the whole does), the stroke is the arc of
#   a ring, of a bracket or of a slur, and no stem: a pencil ring around a note or a number, a bracket by hand before a
#   remark, an arrow. (A census of every head read from its stem on LitChoir's scan pages, 3,217, with the count's
#   verdict for each: 22 ways bend so, 7 on the clean copies and 15 on copies by hand, each looked at. One is a
#   true note, whose stem a hand bent; the true notes whose way is a bow at all bend by 0.31 staff spaces at most, and
#   on the clean copies by 0.17.) The stem as the reader has it, from its end to the head, is too short to tell: an arc
#   and the stem of a hand differ by less than the trace wanders there. None: off


def _slim_way(ink: np.ndarray, row: int, middle: float, step: int, space: float, gap: int, far: int) -> list[tuple[int, float]]:
    """The rows of a slim stroke from a row on, up (step -1) or down (1): in each row the run of ink nearest to the
    middle of the row before, with its middle. A gap of paper of a few rows is passed (a staff line that was taken
    out); wide ink (a head, a beam) is passed for less than a staff space."""
    way = []
    missed = wide = 0
    reach = max(2, int(round(0.12 * space)))
    for _ in range(far):
        row += step
        if not 0 <= row < ink.shape[0]:
            break
        x0, x1 = max(0, int(round(middle)) - reach - 1), min(ink.shape[1], int(round(middle)) + reach + 2)
        at = np.flatnonzero(ink[row, x0:x1])
        if len(at) == 0:
            missed += 1
            if missed > gap:
                break
            continue
        first = last = int(at[np.argmin(np.abs(at + x0 - middle))]) + x0
        while first - 1 >= 0 and ink[row, first - 1]:
            first -= 1
        while last + 1 < ink.shape[1] and ink[row, last + 1]:
            last += 1
        if last - first + 1 > 0.45 * space:
            wide += 1
            missed += 1
            if wide > 0.9 * space or missed > max(gap, 0.9 * space):
                break
            continue
        missed = 0
        middle = (first + last) / 2
        way.append((row, middle))
    return way


def _way_bow(way: list[tuple[int, float]], space: float) -> tuple[float, float]:
    """How far a way of rows and middles bends off a straight line, in staff spaces (with its side as the sign), by
    the parabola that fits it best, and how far the way leaves that parabola at most."""
    if len(way) < 5:
        return 0.0, 0.0
    rows = np.array([row for row, _ in way], float)
    middles = np.array([middle for _, middle in way], float)
    span = rows.max() - rows.min()
    fit = np.polyfit(rows - rows.mean(), middles, 2)
    return float(fit[0] * (span / 2) ** 2 / space), float(np.abs(middles - np.polyval(fit, rows - rows.mean())).max() / space)


def _stem_arc(layers: dict, x: float, end: float, head: float) -> bool:
    """Whether the stroke of a stem at column x, from its end to the row of its head, is an arc (STEM_ARC)."""
    if not STEM_ARC:
        return False
    space = layers['space']
    ink = layers['bare'] > 0
    gap = int(round(max(staff['thick'] for staff in layers['staves']) + 3))
    start = None
    middle = int(round((end + head) / 2))
    aside = int(0.3 * space)
    for off in range(int(space)):
        for row in (middle + off, middle - off):
            if not 0 <= row < ink.shape[0]:
                continue
            x0, x1 = max(0, int(x) - aside), min(ink.shape[1], int(x) + aside + 1)
            at = np.flatnonzero(ink[row, x0:x1])
            if len(at):
                first = last = int(at[np.argmin(np.abs(at + x0 - x))]) + x0
                while first - 1 >= 0 and ink[row, first - 1]:
                    first -= 1
                while last + 1 < ink.shape[1] and ink[row, last + 1]:
                    last += 1
                if last - first + 1 <= 0.45 * space:
                    start = (row, (first + last) / 2)
                    break
        if start:
            break
    if start is None:
        return False
    far = int(6 * space)
    way = (_slim_way(ink, start[0], start[1], -1, space, gap, far)[::-1] + [start]
           + _slim_way(ink, start[0], start[1], 1, space, gap, far))
    side = 1 if end > head else -1
    way = [(row, at) for row, at in way if (row - head) * side >= 0.5 * space]
    if len(way) < space:
        return False
    bend, off = _way_bow(way, space)
    if abs(bend) < STEM_ARC[0] or off > STEM_ARC[1] * abs(bend):
        return False
    half = (way[0][0] + way[-1][0]) / 2
    return all(_way_bow(part, space)[0] / bend >= 0 for part in ([p for p in way if p[0] <= half], [p for p in way if p[0] > half]))


def _thin_ring(layers: dict, ink: np.ndarray, piece: dict, space: float) -> dict | None:
    """The inside of a hollow head whose rim is open, around a piece of thin ink (THIN_RING): its box and its middle,
    or None. The paper that the thin ink and the stems shut in when small breaks are closed, of the shape of the
    inside of a printed half note."""
    grow = int(round(0.7 * space))
    y0, y1 = max(0, piece['y0'] - grow), min(ink.shape[0], piece['y1'] + 1 + grow)
    x0, x1 = max(0, piece['x0'] - grow), min(ink.shape[1], piece['x1'] + 1 + grow)
    window = ((ink[y0:y1, x0:x1] > 0) | (layers['stems'][y0:y1, x0:x1] > 0)).astype(np.uint8)
    size = int(max(3, round(0.35 * space))) | 1
    mask = np.pad(window, size)        # paper around the window: OpenCV takes what lies past an edge for ink
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    outside = (1 - closed).astype(np.uint8)
    cv2.floodFill(outside, None, (0, 0), 2)
    core = (outside == 1)[size:-size, size:-size]
    inside = ((outside != 2)[size:-size, size:-size] & (window == 0)).astype(np.uint8)
    own = np.zeros_like(window)
    box = (slice(piece['y0'] - y0, piece['y1'] + 1 - y0), slice(piece['x0'] - x0, piece['x1'] + 1 - x0))
    own[box] = window[box]
    beside = cv2.dilate(own, np.ones((5, 5), np.uint8))
    count, labelled, stats, centres = cv2.connectedComponentsWithStats(inside, connectivity=4)
    best = None
    for number in range(1, count):
        if (beside & (labelled == number)).any() and (best is None or stats[number][4] > stats[best][4]):
            best = number
    if best is None:
        return None
    left, top, wide, high, area = (int(value) for value in stats[best])
    if left == 0 or top == 0 or left + wide == window.shape[1] or top + high == window.shape[0]:
        return None
    part = (labelled == best).astype(np.uint8)
    hull = cv2.convexHull(np.argwhere(part)[:, ::-1].astype(np.int32))
    rim = cv2.dilate(part, np.ones((5, 5), np.uint8)) & (1 - part)
    measures = (int((part.astype(bool) & core).sum()) / (space * space), area / (space * space), wide / space, high / space,
                area / max(1.0, cv2.contourArea(hull) + len(hull) / 2), float((rim & window).sum()) / max(1, int(rim.sum())))
    if not (measures[0] >= THIN_RING[0] and measures[1] >= THIN_RING[1] and THIN_RING[2] <= measures[2] <= THIN_RING[3]
            and THIN_RING[2] <= measures[3] <= THIN_RING[3] and measures[4] >= THIN_RING[4] and measures[5] >= THIN_RING[5]
            and THIN_RING[6] <= measures[2] / measures[3] <= THIN_RING[7]):
        return None
    ring = {'x0': x0 + left, 'y0': y0 + top, 'x1': x0 + left + wide - 1, 'y1': y0 + top + high - 1,
            'cx': x0 + float(centres[best][0]), 'cy': y0 + float(centres[best][1]), 'area': area}
    return ring


def _line_half(layers: dict, piece: dict) -> float:
    """(LINE_HALF) The share of open paper in the box of a piece of ink that a staff line crosses in its middle rows, when
    that paper lies at one side of the line only; 0.0 otherwise."""
    space = layers['space']
    staff = _staff_of(layers, piece['cx'], piece['cy'])
    if staff is None:
        return 0.0
    reach, least, flat = LINE_HALF
    lines = [row for row in layers['staves'][staff]['rows']
             if row - piece['y0'] >= reach * space and piece['y1'] - row >= reach * space]
    if len(lines) != 1:
        return 0.0
    line = lines[0]
    box = layers['open_holes'][piece['y0']:piece['y1'] + 1, piece['x0']:piece['x1'] + 1] > 0
    rows = np.nonzero(box.any(axis=1))[0] + piece['y0']
    if not len(rows) or box.sum() < least * space * space or (rows[0] < line < rows[-1]):
        return 0.0
    if min(abs(line - rows[-1]), abs(rows[0] - line)) > layers['staves'][staff]['thick'] / 2 + 2:
        return 0.0      # the paper is the half that this line leaves: it lies along the line
    columns = np.nonzero(box.any(axis=0))[0]
    if columns[-1] - columns[0] + 1 < flat * (rows[-1] - rows[0] + 1):
        return 0.0      # and lies on its side, as the inside of a printed half note does
    return float(box.sum()) / (piece['area'] + float(box.sum()))


def thin_heads(layers: dict, heads: list[dict], bars: dict[int, list[float]], ends: list[float]) -> list[dict]:
    """The heads that the thick marks do not show: a quick hand draws a head as one thin slanted stroke, and a weak
    copy loses the place where the stem meets it. Such a head is found from its stem. Every upright stroke that is
    no bar line and that no head hangs on is asked: is there a small piece of ink under its lower end at the left
    (a stem that goes up), or over its upper end at the right (a stem that goes down)? The nearer one is its head.
    A flag hangs at the far end too, but it falls away from the end; a head lies past the end."""
    space = layers['space']
    staves = layers['staves']
    thick = max(staff['thick'] for staff in staves)
    near = int(round(thick + 1))
    # A stroke that crosses a staff line was cut there when the line was taken away: the line under it is its ink.
    marks = layers['marks']
    two = [head for head in heads if TWO_STEMS and len({stem['direction'] for stem in head['stems']}) == 2]
    if two and TWO_APART:
        # A thin head that touches a thick head is one piece of ink with it. The thick ink of a head with two stems
        # is taken away, so that the thin head beside it is a piece of its own.
        marks = marks.copy()
        grown = cv2.dilate(layers['thick'], np.ones((3, 3), np.uint8))
        taken = np.zeros_like(marks)
        for head in two:
            box = (slice(max(0, head['y0'] - 1), head['y1'] + 2), slice(max(0, head['x0'] - 1), head['x1'] + 2))
            taken[box] = grown[box]
        marks &= 1 - taken
        size = 2 * int(round(0.3 * space)) + 1
        beside = cv2.dilate(taken, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    ink = marks | (layers['lines'] & cv2.dilate(marks, np.ones((2 * near + 1, 1), np.uint8)))
    if THROUGH_SIDE:
        # A slanted stroke that crosses a staff line: slivers of the line stay between its parts. A sliver that has
        # the stroke's ink close at its left and at its right in the same row is ink of the stroke.
        aside = np.ones((1, 2 * int(round(THROUGH_SIDE * space)) + 1), np.uint8)
        ink |= layers['lines'] & cv2.morphologyEx(ink, cv2.MORPH_CLOSE, aside)
    if THROUGH_SLANT:
        # A stroke that crosses a staff line at a low slant: its part over the line stands at the right of its part
        # under the line, and the line hides what joins the two. Both parts are small pieces of ink.
        count, labels, stats, centres = cv2.connectedComponentsWithStats(ink, connectivity=8)
        most = THROUGH_SLANT[1] * space
        small = np.isin(labels, [index for index in range(1, count) if stats[index][2] <= most and stats[index][3] <= most])
        small = (small & (marks > 0)).astype(np.uint8)
        # In the rows of the line, the upper part has its ink over the line and none under it; the lower part
        # has it the other way round. (A head that lies on the line has ink at both sides.)
        over, under = np.zeros_like(small), np.zeros_like(small)
        over[near:] = small[:-near]
        under[:-near] = small[near:]
        reach = int(round(THROUGH_SLANT[0] * space))
        after = cv2.dilate(small & under & (1 - over), np.ones((1, reach + 1), np.uint8), anchor=(reach, 0))
        before = cv2.dilate(small & over & (1 - under), np.ones((1, reach + 1), np.uint8), anchor=(0, 0))
        ink |= layers['lines'] & after & before
    rimmed = None
    if THIN_OPEN and OPEN_HOLE:
        # The insides of heads whose rim has a small break: paper that is closed in when the break is closed. A line
        # through the head cuts its inside in two, and the two pieces of a slanted oval do not stand right over each
        # other: pieces that a line's thickness parts, upright, and a third of a staff space, sideways, are one
        # inside. It is as large as OPEN_HOLE and has the head's own ink around it (OPEN_RIM): the paper between
        # two staff lines beside a stem has staff lines around it.
        paper = ((layers['open_holes'] > 0) | (layers['holes'] > 0)).astype(np.uint8)
        grown = cv2.dilate(paper, np.ones((near + 1, int(round(0.3 * space)) | 1), np.uint8))
        rimmed = np.zeros_like(paper)
        count, labelled, stats, _ = cv2.connectedComponentsWithStats(grown, connectivity=8)
        for index in range(1, count):
            x, y, wide, high, _ = stats[index]
            box = (slice(y, y + high), slice(x, x + wide))
            inside = paper[box] & (labelled[box] == index).astype(np.uint8)
            columns = np.nonzero(inside.any(axis=0))[0]
            if inside.sum() < OPEN_HOLE * space * space or columns[-1] - columns[0] + 1 < 0.4 * space \
                    or high > THIN_HIGH[1] * space + near or wide > THIN_WIDE[1] * space:
                continue
            if OPEN_RIM:
                ring = cv2.dilate(inside, np.ones((7, 7), np.uint8)) & (1 - inside)
                if (ring & layers['bare'][box]).sum() < OPEN_RIM * ring.sum():
                    continue
            rimmed[box] |= inside & (layers['open_holes'][box] > 0)
    count, labels, stats, centres = cv2.connectedComponentsWithStats(ink, connectivity=8)
    pieces = []
    for index in range(1, count):
        x, y, wide, high, area = stats[index]
        cx, cy = float(centres[index][0]), float(centres[index][1])
        if THIN_LEDGER and THIN_WIDE[1] * space < wide <= 6 * space and THIN_HIGH[0] * space <= high <= THIN_HIGH[1] * space:
            # A thin head on a ledger line or under it is one piece of ink with the line, and the line is longer than
            # a head. The line is the level ink that goes through most of the piece; the head is where the piece has
            # ink over or under that line.
            staff = _staff_of(layers, cx, cy)
            whole = labels[y:y + high, x:x + wide] == index
            line = np.nonzero(whole.sum(axis=1) >= 0.6 * wide)[0]
            if staff is not None and not staves[staff]['rows'][0] - 0.6 * space <= cy <= staves[staff]['rows'][4] + 0.6 * space:
                rest = whole.copy()
                if len(line) and line[-1] - line[0] + 1 <= max(3.0, THIN_LEDGER * space):
                    rest[max(0, line[0] - 1):line[-1] + 2] = False
                    body = np.nonzero(rest.sum(axis=0) >= max(2.0, 0.08 * space))[0]
                else:
                    # No one level line: the head is where the ink is higher than a line is thick.
                    body = np.nonzero(whole.sum(axis=0) > max(3.0, THIN_LEDGER * space))[0]
                if len(body) and THIN_WIDE[0] * space <= body[-1] - body[0] + 1 <= THIN_WIDE[1] * space \
                        and max(body[0], wide - 1 - body[-1]) >= 0.3 * space:
                    ys, xs = np.nonzero(rest[:, body[0]:body[-1] + 1])
                    cx, cy = float(x + body[0] + xs.mean()), float(y + ys.mean())
                    rows = np.nonzero(whole[:, body[0]:body[-1] + 1].any(axis=1))[0]
                    x, y, wide, high = x + int(body[0]), y + int(rows[0]), int(body[-1] - body[0] + 1), int(rows[-1] - rows[0] + 1)
                    area = int((labels[y:y + high, x:x + wide] == index).sum())
        if not (THIN_WIDE[0] * space <= wide <= THIN_WIDE[1] * space and THIN_HIGH[0] * space <= high <= THIN_HIGH[1] * space):
            continue
        if area < 0.06 * space * space:
            continue
        part = labels[y:y + high, x:x + wide] == index
        # A piece that lies along a staff line is a rest of the line, not a head.
        own = part & (marks[y:y + high, x:x + wide] > 0)
        if own.sum() < 0.35 * area or (LINE_REST and high <= thick + 2 and own.sum() < LINE_REST * area):
            continue
        # What is left of a thick head at its edge when its thick ink was taken away is no head of its own.
        if two and TWO_APART and (part & (beside[y:y + high, x:x + wide] > 0)).sum() >= 0.7 * area:
            continue
        loop = _loop(part, space)
        if LOOP_STEM and loop < THIN_HOLLOW:
            # The stem was taken out of the marks: an oval that has its stem as one side is open there.
            edge = int(round(0.25 * space))
            first, last = max(0, x - edge), min(ink.shape[1], x + wide + edge)
            with_stem = (labels[y:y + high, first:last] == index) | (layers['stems'][y:y + high, first:last] > 0)
            loop = max(loop, _loop(with_stem, space) * with_stem.shape[1] / wide)
            if LOOP_LINE and loop < THIN_HOLLOW:
                # A printed half note that hangs under a staff line has the line as its upper side.
                over = int(round(thick + 2))
                y0 = max(0, y - over)
                box = (labels[y0:y + high + over, first:last] == index) | (layers['stems'][y0:y + high + over, first:last] > 0) \
                    | (layers['lines'][y0:y + high + over, first:last] > 0)
                loop = max(loop, _loop(box, space) * box.shape[0] * box.shape[1] / (wide * high))
        opened = 0.0
        if rimmed is not None:
            inside = float(rimmed[y:y + high, x:x + wide].sum())
            opened = inside / (area + inside)
        pieces.append({'x0': int(x), 'y0': int(y), 'x1': int(x + wide - 1), 'y1': int(y + high - 1), 'area': int(area),
                       'cx': cx, 'cy': cy,
                       'hole': max(float((layers['holes'][y:y + high, x:x + wide] > 0)[part].sum()) / area, loop),
                       'opened': opened})
        if LINE_HALF and max(pieces[-1]['hole'], opened) < THIN_HOLLOW:
            pieces[-1]['half'] = _line_half(layers, pieces[-1])
    # A thick head with a stem up and a stem down can be two notes: a thin head of the other voice lies right over
    # it or under it, and its stem passed through the thick head. So the stems of such a head are asked too.
    if two and OPEN_HOLE:
        # The other head can also be a hollow head whose rim has a break: its inside is an open hole.
        count, labelled, stats, centres = cv2.connectedComponentsWithStats(layers['open_holes'], connectivity=8)
        for index in range(1, count):
            x, y, wide, high, area = stats[index]
            if area >= OPEN_HOLE * space * space and wide >= 0.4 * space:
                if OPEN_RIM:
                    # The paper between two staff lines beside a stem is closed in too. A head's inside has the
                    # head's own ink around it, not staff lines.
                    y0, x0 = max(0, y - 3), max(0, x - 3)
                    inside = (labelled[y0:y + high + 3, x0:x + wide + 3] == index).astype(np.uint8)
                    ring = cv2.dilate(inside, np.ones((7, 7), np.uint8)) & (1 - inside)
                    if (ring & layers['bare'][y0:y + high + 3, x0:x + wide + 3]).sum() < OPEN_RIM * ring.sum():
                        continue
                pieces.append({'x0': int(x), 'y0': int(y), 'x1': int(x + wide - 1), 'y1': int(y + high - 1), 'area': int(area),
                               'cx': float(centres[index][0]), 'cy': float(centres[index][1]), 'hole': 1.0, 'open': True})
    used = [(stem['x'], min(head['cy'], stem['end']), max(head['cy'], stem['end'])) for head in heads for stem in head['stems']
            if not any(head is other for other in two)]
    strokes = [stroke for stroke in layers['strokes'] if stroke['slim'] and stroke['y1'] - stroke['y0'] + 1 >= THIN_STEM * space]
    asks = []
    matched = set()
    for stroke in strokes:
        x, top, bottom = stroke['x'], stroke['y0'], stroke['y1']
        staff = _staff_of(layers, x, (top + bottom) / 2)
        if staff is None or x <= ends[staff] + 0.3 * space:
            continue
        rows = staves[staff]['rows']
        if bottom < rows[0] - 3.5 * space or top > rows[4] + 3.5 * space:
            continue
        if any(abs(x - bar) <= 0.4 * space for bar in bars.get(staff, [])):
            continue
        if any(abs(x - other) <= 0.35 * space and first - 0.5 * space <= bottom and top <= last + 0.5 * space
               for other, first, last in used):
            continue
        if _across(heads, x, top, bottom, space):
            continue
        if stroke.get('owned'):
            continue                                   # another head's own stem (see LOST_OWN)
        # A sharp and a natural have two upright strokes side by side.
        if any(other is not stroke and abs(other['x'] - x) <= 0.9 * space
               and min(other['y1'], bottom) - max(other['y0'], top) >= 0.5 * min(other['y1'] - other['y0'], bottom - top)
               for other in strokes):
            continue
        # The stem of a head with two stems: a thin head lies between that head and the far end of this stem.
        owners = [(head, stem) for head in two for stem in head['stems']
                  if abs(x - stem['x']) <= 0.35 * space and min(head['cy'], stem['end']) - 0.5 * space <= bottom
                  and top <= max(head['cy'], stem['end']) + 0.5 * space]
        matched |= {id(stem) for _, stem in owners}
        asks.append((x, top, bottom, staff, owners, False, (float(stroke['xs'][0]), float(stroke['xs'][-1])), stroke))
    if TWO_ALONG:
        # The stems of a head with two stems that are no stroke of their own: the stem up, the head and the stem
        # down were one long stroke, or the ink that leaves the head is the thin head itself.
        for head in two:
            for stem in head['stems']:
                if id(stem) not in matched:
                    asks.append((stem['x'], min(head['cy'], stem['end']), max(head['cy'], stem['end']), head['staff'],
                                 [(head, stem)], True, None, None))
        if ONE_ALONG:
            # A head with one stem: the thin head of the other voice can hang on that same stem, farther along. The
            # ink that leaves the thick head is then the other voice's stem, and the two heads share it as a chord.
            for head in heads:
                if len(head['stems']) == 1 and not any(head is other for other in two):
                    stem = head['stems'][0]
                    asks.append((stem['x'], min(head['cy'], stem['end']), max(head['cy'], stem['end']), head['staff'],
                                 [(head, stem)], True, None, None))
    found = []
    flags = {}

    def flagged(owner: dict, stem: dict) -> bool:
        # A printed flag comes back along its stem and closes in paper there: that is no head of another voice.
        if id(stem) not in flags:
            hung = tail_marks(layers, dict(owner, staff_ref=staves[owner['staff']]), stem)
            flags[id(stem)] = any(piece['right'] and piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6
                                  and piece['from_end'] <= FLAG_END for piece in hung)
            if ALONG_HOOK and not flags[id(stem)]:
                # A hairline flag is a hook at the very end of the stem, as count_tails reads it: one print curls it
                # back up to its head, and where it meets the stem again it closes paper that was read as a head.
                thin = [piece for piece in hung if not (piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6)]
                left = [piece['row'] for piece in thin if not piece['right']]
                flags[id(stem)] = any(piece['right'] and piece['from_end'] <= TAIL_START and piece['back'] >= 0.12
                                      and all(abs(piece['row'] - row) > 0.25 * space for row in left) for piece in thin)
        return flags[id(stem)]

    def make_head(piece: dict, direction: str, x: float, end: float, staff: int, arc: bool = True) -> dict | None:
        place = pitch_place(staves[staff], piece['cy'])
        head = {'x0': piece['x0'], 'y0': piece['y0'], 'x1': piece['x1'], 'y1': piece['y1'], 'cx': piece['cx'], 'cy': piece['cy'],
                'staff': staff, 'place': place, 'hollow': piece['hole'] >= THIN_HOLLOW, 'hole': piece['hole'], 'thin': True,
                'stems': [{'direction': direction, 'x': int(round(x)), 'end': int(end), 'length': abs(piece['cy'] - end)}]}
        if abs(place) > 4 + 2 * REACH:
            return None
        if _stem_arc(layers, int(round(x)), int(end), piece['cy']):
            return None         # the arc of a ring or of a bracket
        if abs(place) > 4.6:
            head['ledgers'] = ledger_lines(layers, staves[staff], head)
            place = ledger_place(layers, staves[staff], head)
            if place is None or (not head['ledgers'] and abs(head['place']) > max(5.6, NO_LEDGER)):
                return None
            head['place'] = place
        if piece.get('opened', 0.0) >= THIN_HOLLOW > piece['hole']:
            # The same head, with the place that its ink gave it: only its inside was not seen before.
            head['hollow'], head['hole'] = True, piece['opened']
        if piece.get('half') and not piece['x0'] <= x <= piece['x1']:
            # The half of an inside that a staff line leaves, with the stem beside the rim (LINE_HALF).
            head['hollow'], head['hole'] = True, piece['half']
            if LINE_HALF_SEEN is not None:
                LINE_HALF_SEEN.append({'cx': piece['cx'], 'cy': piece['cy'], 'box': (piece['x0'], piece['x1'], piece['y0'], piece['y1']),
                                       'half': piece['half'], 'dir': direction, 'x': x, 'end': end, 'staff': staff})
        if THIN_RING and arc and not piece.get('open') and max(piece['hole'], piece.get('opened', 0.0)) < THIN_HOLLOW:
            if 'ring' not in piece:
                piece['ring'] = _thin_ring(layers, ink, piece, space)
            ring = piece['ring']
            if ring is not None:
                # One arc of an open ring: the head of the whole ring, a rim's width around its inside, is kept
                # beside this one until the hollow heads were read from their insides (ring_heads).
                edge = int(round(thick + 1))
                whole = dict(piece, x0=min(piece['x0'], ring['x0'] - edge), y0=min(piece['y0'], ring['y0'] - edge),
                             x1=max(piece['x1'], ring['x1'] + edge), y1=max(piece['y1'], ring['y1'] + edge), cx=ring['cx'],
                             cy=ring['cy'], hole=max(THIN_HOLLOW, ring['area'] / (ring['area'] + piece['area'])))
                head['ring'] = make_head(whole, direction, x, end, staff, False)
        return head

    def other_piece(x: float, top: float, bottom: float, direction: str, held: dict) -> dict | None:
        """Another piece that hangs on a stem before the stroke's end: over the held piece for a stem up, under it
        for a stem down. It reaches the stem."""
        best = None
        for piece in pieces:
            if piece is held or piece.get('open'):
                continue
            if direction == 'up':
                past, side, reach, apart = piece['cy'] - bottom, x - piece['cx'], x - piece['x1'], held['cy'] - piece['cy']
            else:
                past, side, reach, apart = top - piece['cy'], piece['cx'] - x, piece['x0'] - x, piece['cy'] - held['cy']
            if apart < 0.3 * space or not (-0.15 * space <= side <= 1.6 * space and reach <= 0.2 * space):
                continue
            if not -THIN_PAIR * space <= past <= THIN_NEAR * space:
                continue
            if any(abs(head['cx'] - piece['cx']) <= 0.7 * space and abs(head['cy'] - piece['cy']) <= 0.45 * space
                   for head in heads + found):
                continue
            far = abs(past) + max(0.0, reach)
            if best is None or far < best[0]:
                best = (far, piece)
        return best[1] if best else None

    asked = {}       # the stroke of each thin head that was found from a stroke of its own: (x, top, bottom, direction)
    for x, top, bottom, staff, owners, whole, leans, stroke in asks:
        best = None
        for piece in pieces:
            if piece.get('open') and not owners:
                continue
            for direction in ('up', 'down'):
                if direction == 'up':       # the head lies under the lower end, at the left
                    past = piece['cy'] - bottom
                    side = x - piece['cx']
                    reach = x - piece['x1']
                else:                        # the head lies over the upper end, at the right
                    past = top - piece['cy']
                    side = piece['cx'] - x
                    reach = piece['x0'] - x
                if LEAN_END and leans and not owners and reach > 0.7 * space:
                    # A stem that leans: its end is nearer to the head than its middle.
                    lean = (x - leans[1]) if direction == 'up' else (leans[0] - x)
                    if 0 < lean <= LEAN_END * space:
                        side, reach = side - lean, reach - lean
                if not (-0.15 * space <= side <= 1.6 * space and reach <= 0.7 * space):
                    continue
                along = None
                if TWO_ALONG and len(owners) == 1 and owners[0][1]['direction'] == direction \
                        and (len(owners[0][0]['stems']) == 2 or (whole and len(owners[0][0]['stems']) == 1 and ONE_ALONG
                                                                 and -0.6 * space <= reach <= 0.2 * space)):
                    # The thin head of the other voice hangs on this stem anywhere between the thick head and the
                    # stem's far end, at its own side of the stem. A flag hangs at the far end.
                    owner, stem = owners[0]
                    between = (owner['cy'] - piece['cy']) if direction == 'up' else (piece['cy'] - owner['cy'])
                    to_end = (piece['y0'] - stem['end']) if direction == 'up' else (stem['end'] - piece['y1'])
                    alone = len(owner['stems']) == 1
                    # Beside the staff the words are near: there only an oval counts on a stem that a head has alone.
                    rows = staves[staff]['rows']
                    if alone and piece['hole'] < THIN_HOLLOW and not rows[0] - 0.6 * space <= piece['cy'] <= rows[4] + 0.6 * space:
                        continue
                    if between >= (ONE_ALONG if alone else 0.3) * space and to_end >= TWO_ALONG * space \
                            and side >= 0.15 * space \
                            and piece['y1'] - piece['y0'] + 1 >= ALONG_HIGH * space and not flagged(owner, stem) \
                            and not any(abs(head['cx'] - piece['cx']) <= 0.7 * space and abs(head['cy'] - piece['cy']) <= 0.45 * space
                                        for head in heads + found):
                        along = between
                if along is None:
                    if whole:
                        continue
                    # The stem of an open oval runs along its side, so the oval's middle lies before the stem's end.
                    half = piece.get('half') and not piece['x0'] <= x <= piece['x1']
                    back = THIN_BACK * space + (LOOP_BACK * (piece['y1'] - piece['y0'] + 1)
                                                if piece['hole'] >= THIN_HOLLOW or half else 0.0)
                    if THIN_INSIDE and reach <= 0 and piece['hole'] < THIN_HOLLOW:
                        # The stem runs along the side of the head, inside its piece of ink: the middle of the
                        # head lies before the stem's end, as with a thick head.
                        back = max(back, THIN_INSIDE * (piece['y1'] - piece['y0'] + 1))
                    if not -back <= past <= THIN_NEAR * space:
                        continue
                far = along if along is not None else abs(past) + max(0.0, reach)
                if best is None or far < best[0]:
                    best = (far, piece, direction)
        if best is None:
            continue
        _, piece, direction = best
        if piece.get('open') and OPEN_RIM:
            # The open hole is the inside of a thin oval: the oval's own ink is the head, the hole shows its middle.
            rim = [other for other in pieces if not other.get('open') and other['x0'] <= piece['cx'] <= other['x1']
                   and other['y0'] <= piece['cy'] <= other['y1']]
            if rim:
                piece = dict(min(rim, key=lambda other: other['area']), hole=1.0, cy=piece['cy'])
        if any(abs(head['cx'] - piece['cx']) <= 0.7 * space and abs(head['cy'] - piece['cy']) <= 0.45 * space for head in heads):
            continue
        holder = next((head for head in found if abs(head['cx'] - piece['cx']) <= 0.7 * space
                       and abs(head['cy'] - piece['cy']) <= 0.45 * space), None)
        if holder is not None:
            # Another stem has this piece as its head. Two voices, each a thin stroke, one right over the other: the
            # stem up of the upper head runs on into the lower head (or the stem down into the upper one), so the
            # stroke seems to end at the wrong head. The stem up has the upper piece, the stem down the lower one.
            theirs = asked.get(id(holder))
            if THIN_PAIR and not owners and theirs is not None and theirs[3] != direction:
                moved = other_piece(theirs[0], theirs[1], theirs[2], theirs[3], piece)
                if moved is not None:
                    first = make_head(moved, theirs[3], theirs[0], theirs[1] if theirs[3] == 'up' else theirs[2], holder['staff'])
                    second = make_head(piece, direction, x, top if direction == 'up' else bottom, staff)
                    if first is not None and second is not None:
                        found[next(number for number, head in enumerate(found) if head is holder)] = first
                        found.append(second)
                        asked[id(first)] = theirs
                        asked[id(second)] = (x, top, bottom, direction)
                else:
                    own = other_piece(x, top, bottom, direction, piece)
                    head = make_head(own, direction, x, top if direction == 'up' else bottom, staff) if own is not None else None
                    if head is not None:
                        found.append(head)
                        asked[id(head)] = (x, top, bottom, direction)
            continue
        end = top if direction == 'up' else bottom
        if owners:
            owner, stem = owners[0]
            between = (owner['cy'] - piece['cy']) if direction == 'up' else (piece['cy'] - owner['cy'])
            shared = whole and len(owner['stems']) == 1 and not any(owner is other for other in two)
            if len(owners) > 1 or stem['direction'] != direction or between < 0.3 * space or (len(owner['stems']) < 2 and not shared):
                continue
            if not shared:
                owner['stems'].remove(stem)
            end = stem['end'] if whole else end
        elif TWO_ALONG:
            # A thick head under or over this thin head took the thin head's own ink for a stem: it is none.
            for owner in two:
                for stem in list(owner['stems']):
                    if stem['direction'] == direction and len(owner['stems']) == 2 \
                            and piece['x0'] - 0.2 * space <= stem['x'] <= piece['x1'] + 0.2 * space \
                            and piece['y0'] - 0.3 * space <= stem['end'] <= piece['y1'] + 0.3 * space:
                        owner['stems'].remove(stem)
        head = make_head(piece, direction, x, end, staff)
        if head is not None and stroke is not None and not owners and abs(head['place']) > 4.6 and not head.get('ledgers') \
                and _f_stroke(stroke, space):
            continue        # the hook of the letter f
        if head is not None and THIN_SPECKS and stroke is not None and not owners \
                and _own_ink(stroke, head, staves[staff]) < THIN_SPECKS:
            continue        # a column of specks is no stem
        if head is not None:
            found.append(head)
            if not owners:
                asked[id(head)] = (x, top, bottom, direction)
    return found


def _own_ink(stroke: dict, head: dict, staff: dict) -> float:
    """The share of a stroke's rows, outside the staff lines and the rows of its head, where the stroke has ink of its
    own (see THIN_SPECKS)."""
    half = staff['thick'] / 2 + 1
    own = [bool(stroke['left'][step] > 0 or stroke['right'][step] > 0) for step in range(stroke['y1'] - stroke['y0'] + 1)
           if all(abs(stroke['y0'] + step - row) > half for row in staff['rows'])
           and not head['y0'] <= stroke['y0'] + step <= head['y1']]
    return float(np.mean(own)) if own else 1.0


def ring_heads(heads: list[dict]) -> list[dict]:
    """The heads that were read from a stem at one arc of an open ring stand as the whole ring: hollow, and where the
    ring stands (THIN_RING). This runs after the hollow heads were read from their insides (hole_heads): an inside
    that is closed, or open by a small break, is read there, and the arc is then a piece of its rim that went. Where
    the ring gives no head (its place has no ledger line, its stem is an arc), the head stays as it was read."""
    for head in heads:
        ring = head.pop('ring', None)
        if ring is None or not head.get('thin') or head['hollow']:
            continue
        if any(other is not head and other['hollow'] and other['x0'] - 2 <= ring['cx'] <= other['x1'] + 2
               and other['y0'] - 2 <= ring['cy'] <= other['y1'] + 2 for other in heads):
            continue        # the inside is another hollow head's
        for name in ('x0', 'y0', 'x1', 'y1', 'cx', 'cy', 'place', 'hollow', 'hole'):
            head[name] = ring[name]
        head.pop('ledgers', None)
        if 'ledgers' in ring:
            head['ledgers'] = ring['ledgers']
        for stem in head['stems']:
            stem['length'] = abs(head['cy'] - stem['end'])
    return heads


# ----------------------------------------------------------------------------------------------------------------
# A whole note in the space next to the staff whose thin rim the scan lost

ARC_WHOLE = (1.4, 1.9, 0.9, 1.25)   # one print draws the rim of a whole note bold at its two sides and as a hairline over
#   and under them. In the space next to the staff, the staff's outer line hides one hairline and the scan lost the
#   other: two bold arcs are left side by side, they close no paper (or the break is closed and the open hole has no
#   stem), and no head was read. The two arcs are a whole note where their whole shape is that of the oval: together
#   this wide (the first two numbers) and this high (the next two), in staff spaces of their staff, hanging on the
#   outer line (ARC_NEAR), narrowing to their far end with their tips turned to each other (ARC_FAR), and alone in
#   paper (ARC_ALONE). A rule for one print: of the 142 such pairs at a staff's outer line on LitChoir's scan pages,
#   three are whole notes, all of one hymn and all three lacking before, and only those three pass. The others are
#   two letters of the words that stand against the staff: the nearest pair (the letters I and A, alone under a
#   staff) fails only the outline, which is widest at its far end (0.94 of the widest row against 0.45 at most),
#   and every other pair fails two tests or more. None: off
ARC_PIECE = (0.25, 1.1, 0.6, 1.5, 0.35, 0.05, 0.9, 0.6)   # each arc is this wide (the first two numbers) and this high (the
#   next two), in staff spaces of the page, and fills this share of its box; the paper between their boxes is this
#   wide (the next two), and they stand side by side in this share of the rows of the lower one
ARC_NEAR = (0.2, 0.1, 0.2, 0.8)     # the pair begins at the staff's outer line: at most the first number of staff spaces
#   into the line and the second away from it; within the third number of staff spaces there, the line closes this
#   share of the columns between the arcs
ARC_FAR = (0.6, 0.2, 0.4, 0.2)      # the outline of the pair in the last fifth of its rows is at most this share of its
#   widest row, the two arcs end at most this many staff spaces apart in height, and within the third number of staff
#   spaces past them at most this share of the columns between the arcs holds ink; and their tips stand closer than
#   the paper between them is wide in the middle third of its rows
ARC_ALONE = (0.7, 0.02)             # within this many staff spaces at each side, in the rows of the pair, and past its far
#   end, in its columns, there is at most this much ink that is no staff line, in staff spaces squared


def arc_wholes(layers: dict, heads: list[dict], ends: list[float]) -> list[dict]:
    """The whole notes that were left as two bold arcs at the outer line of a staff (ARC_WHOLE): hollow heads with
    no stem, in the space next to the staff. No head was read where they stand."""
    if not ARC_WHOLE:
        return []
    space = layers['space']
    bare, ink = (layers['bare'] > 0).astype(np.uint8), layers['ink']
    count, labels, stats, _ = cv2.connectedComponentsWithStats(bare, connectivity=8)
    arcs = []
    for index in range(1, count):
        x, y, wide, high, area = (int(value) for value in stats[index])
        if ARC_PIECE[0] * space <= wide <= ARC_PIECE[1] * space \
                and ARC_PIECE[2] * space <= high <= ARC_PIECE[3] * space and area >= ARC_PIECE[4] * wide * high:
            arcs.append((x, y, wide, high, index))
    arcs.sort()
    out = []
    for first, left in enumerate(arcs):
        for right in arcs[first + 1:]:
            gap = right[0] - (left[0] + left[2])
            if gap > ARC_PIECE[6] * space:
                break
            top, bottom = max(left[1], right[1]), min(left[1] + left[3], right[1] + right[3])
            if gap < ARC_PIECE[5] * space or bottom - top < ARC_PIECE[7] * min(left[3], right[3]):
                continue
            x0, x1 = left[0], right[0] + right[2] - 1
            y0, y1 = min(left[1], right[1]), max(left[1] + left[3], right[1] + right[3]) - 1
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            staff = _staff_of(layers, cx, cy)
            if staff is None or cx < ends[staff] + 0.3 * space:
                continue
            lines = layers['staves'][staff]
            own = lines['space']
            if not (ARC_WHOLE[0] * own <= x1 - x0 + 1 <= ARC_WHOLE[1] * own
                    and ARC_WHOLE[2] * own <= y1 - y0 + 1 <= ARC_WHOLE[3] * own):
                continue
            under = cy > lines['rows'][4]
            if not under and not cy < lines['rows'][0]:
                continue
            touch = (y0 - lines['rows'][4]) / own if under else (lines['rows'][0] - y1) / own
            if not -ARC_NEAR[0] <= touch <= ARC_NEAR[1]:
                continue
            if any(other['x0'] <= x1 and other['x1'] >= x0 and other['y0'] <= y1 and other['y1'] >= y0
                   for other in heads + out):
                continue
            # The rows of the pair from the staff's line to the far end: the paper between the arcs and their outline.
            one, two = (labels[y0:y1 + 1, x0:x1 + 1] == arc[4] for arc in (left, right))
            if not under:
                one, two = one[::-1], two[::-1]
            paper, outline = [], []
            for row in range(one.shape[0]):
                a, b = np.nonzero(one[row])[0], np.nonzero(two[row])[0]
                if len(a) and len(b):
                    paper.append(int(b[0] - a[-1] - 1))
                columns = np.nonzero(one[row] | two[row])[0]
                outline.append(int(columns[-1] - columns[0] + 1) if len(columns) else 0)
            if len(paper) < 0.5 * len(outline):
                continue
            fifth = max(2, len(outline) // 5)
            if float(np.mean(outline[-fifth:])) > ARC_FAR[0] * max(outline):
                continue
            last = [int(np.nonzero(arc.any(axis=1))[0][-1]) for arc in (one, two)]
            if abs(last[0] - last[1]) > ARC_FAR[1] * own:
                continue
            third = max(1, len(paper) // 3)
            tips = int(np.nonzero(two[last[1]])[0][0]) - int(np.nonzero(one[last[0]])[0][-1]) - 1
            if tips >= float(np.mean(paper[third:-third] or paper)):
                continue
            # The line closes the paper at the near end, and nothing closes it at the far end.
            c0, c1 = left[0] + left[2], right[0] - 1
            near, far = max(2, int(round(ARC_NEAR[2] * own))), int(ARC_FAR[2] * own)
            closed = ink[max(0, y0 - near):y0 + 2, c0:c1 + 1] if under else ink[y1 - 1:y1 + near + 1, c0:c1 + 1]
            opened = ink[y1 - 1:y1 + far + 1, c0:c1 + 1] if under else ink[max(0, y0 - far):y0 + 2, c0:c1 + 1]
            if not closed.size or closed.any(axis=0).mean() < ARC_NEAR[3] \
                    or (opened.size and opened.any(axis=0).mean() > ARC_FAR[3]):
                continue
            # Alone in paper: no letter stands beside the pair, and nothing past its far end.
            side = int(round(ARC_ALONE[0] * own))
            past = bare[y1 + 2:y1 + 2 + side, x0:x1 + 1] if under \
                else bare[max(0, y0 - 1 - side):max(0, y0 - 1), x0:x1 + 1]
            beside = (bare[y0:y1 + 1, max(0, x0 - side):max(0, x0 - 1)], bare[y0:y1 + 1, x1 + 2:x1 + 1 + side], past)
            if max(int(part.sum()) for part in beside) > ARC_ALONE[1] * own * own:
                continue
            out.append({'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'cx': cx, 'cy': cy, 'staff': staff,
                        'place': -5.0 if under else 5.0, 'hollow': True,
                        'hole': sum(paper) / ((x1 - x0 + 1) * (y1 - y0 + 1)), 'stems': [], 'mark': None,
                        'from_hole': True, 'core': None, 'alt': None, 'ledgers': [], 'arcs': True})
    return out


# ----------------------------------------------------------------------------------------------------------------
# A whole note in the staff or on a ledger line whose thin rim the scan lost

ARC_PAIR = (1.2, 1.8, 0.25, 0.9, 0.2, 0.36)   # the print of ARC_WHOLE, in the staff and on a ledger line: the scan lost
#   the hairlines over and under the bold sides of a whole note, and the two sides are left as two short bold strokes
#   that face each other, with paper between them and no head read there. Such a pair is a whole note by its whole
#   shape: together this wide (the first two numbers, in staff spaces of its staff, without the rows of a ledger
#   line), this much paper between the strokes (the next two), each stroke at least this thick in its usual row (the
#   next number), and its middle within the last number of a half staff space of a place of the staff. A rule for one
#   print, and for a whole note of another whose hairlines lie on the staff lines: of the pairs of short strokes that
#   face each other on LitChoir's scan pages, the last chord of both scans of one hymn and one whole note of another
#   pass, and none else (letters and the brackets around them, letters that a hand wrote on a staff, the bold C of
#   common time, a breve between its bars, a short double bar between two whole notes, words struck out with a line,
#   the strokes of a noisy picture). None: off
ARC_PAIR_HIGH = (0.85, 1.2, 0.25, 2.5, 0.85, 1.0)   # the pair is this high in staff spaces of its staff (one whole
#   note), or one staff space more (two whole notes a third apart), and the tops and the bottoms of its two strokes are
#   at most the third number of staff spaces apart. In the staff the middle gives the place; out of it a ledger line
#   runs through the middle and the note stands on the first ledger line (a print can set that line closer to the staff
#   than a staff space), and the ledger line is at most the fourth number of staff spaces long (a longer line strikes
#   out words). Each stroke is one run of ink in at least this share of its rows (an A is two strokes) and stands
#   upright, its two ends at most the last number of staff spaces apart in their columns. It stands after a head of its
#   staff, with no ink between its strokes, and alone in paper (ARC_ALONE)
ARC_SEEN = None   # a list: every pair that is asked, with its measures (a census at the reader's own step)


def _arc_morph(mask: np.ndarray, wide: int, high: int, close: bool) -> np.ndarray:
    """An exact opening or closing of a mask with a kernel of an odd size, with paper around the mask."""
    wide, high = max(1, wide | 1), max(1, high | 1)
    pad = max(wide, high)
    padded = np.pad(mask.astype(np.uint8), pad)
    done = cv2.morphologyEx(padded, cv2.MORPH_CLOSE if close else cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (wide, high)))
    return done[pad:-pad, pad:-pad] > 0


def arc_pairs(layers: dict, heads: list[dict], ends: list[float]) -> list[dict]:
    """The whole notes in the staff or on a ledger line that were left as two short bold strokes that face each other
    (ARC_PAIR): hollow heads with no stem. No head was read where they stand."""
    if not ARC_PAIR:
        return []
    space = layers['space']
    bare = layers['bare'] > 0
    level = _arc_morph(bare, int(round(space)), 1, False)
    ledger = level & ~_arc_morph(level, 1, int(round(0.3 * space)), False)
    strokes = bare & ~ledger
    joined = strokes | (ledger & _arc_morph(strokes, 1, int(round(0.35 * space)), True))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(joined.astype(np.uint8), connectivity=8)
    parts = []
    for index in range(1, count):
        x, y, wide, high, _area = (int(value) for value in stats[index])
        if ARC_PAIR_HIGH[0] * space <= high <= (ARC_PAIR_HIGH[1] + 1) * space and wide <= 1.3 * space:
            parts.append((x, y, wide, high, index))
    parts.sort()
    out = []
    for first, left in enumerate(parts):
        for right in parts[first + 1:]:
            gap = right[0] - (left[0] + left[2])
            if gap > 1.3 * space:
                break
            if gap <= 0 or abs(left[1] - right[1]) > ARC_PAIR_HIGH[2] * space \
                    or abs(left[1] + left[3] - right[1] - right[3]) > ARC_PAIR_HIGH[2] * space:
                continue
            x0, x1 = left[0], right[0] + right[2] - 1
            y0, y1 = min(left[1], right[1]), max(left[1] + left[3], right[1] + right[3]) - 1
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            staff = _staff_of(layers, cx, cy)
            if staff is None:
                continue
            lines = layers['staves'][staff]
            own, rows = lines['space'], lines['rows']
            top, bottom = (rows[2] - y0 + 0.5) / (own / 2), (rows[2] - y1 - 0.5) / (own / 2)
            high = (y1 - y0 + 1) / own
            notes = 1 if ARC_PAIR_HIGH[0] <= high <= ARC_PAIR_HIGH[1] else \
                2 if ARC_PAIR_HIGH[0] + 1 <= high <= ARC_PAIR_HIGH[1] + 1 else 0
            mid = (top + bottom) / 2
            # The rows of the pair without a ledger line and the row at each side of it.
            band = ledger[y0:y1 + 1, max(0, x0 - int(space)):x1 + int(space) + 1].any(axis=1)
            band = band | np.r_[False, band[:-1]] | np.r_[band[1:], False]
            one, two = (labels[y0:y1 + 1, x0:x1 + 1] == part[4] for part in (left, right))
            free = [row for row in range(y1 - y0 + 1) if not band[row] and one[row].any() and two[row].any()]
            if not free:
                continue
            outer = (max(int(np.nonzero(two[row])[0][-1]) for row in free)
                     - min(int(np.nonzero(one[row])[0][0]) for row in free) + 1) / own
            paper = min(int(np.nonzero(two[row])[0][0]) - int(np.nonzero(one[row])[0][-1]) - 1 for row in free) / own
            usual = [float(np.median([part[row].sum() for row in free])) / own for part in (one, two)]
            # Each part is one stroke: one run of ink in its rows.
            single = min(float(np.mean([np.count_nonzero(np.diff(np.r_[0, part[row].astype(np.int8), 0]) == 1) == 1
                                         for row in free])) for part in (one, two))
            # Each stroke stands upright: its two ends in one column (the stroke of a Z leans).
            lean = 0.0
            for part in (one, two):
                rows_of = [row for row in free if part[row].any()]
                fifth = max(1, len(rows_of) // 5)
                ends_at = [float(np.mean([np.nonzero(part[row])[0].mean() for row in chosen]))
                           for chosen in (rows_of[:fifth], rows_of[-fifth:])]
                lean = max(lean, abs(ends_at[0] - ends_at[1]) / own)
            between = strokes[y0:y1 + 1, left[0] + left[2]:right[0]]
            middle = int(round(cy))
            crossed = False
            low = max(0, middle - int(0.25 * own))
            across = ledger[low:middle + int(0.25 * own) + 1, x0:x1 + 1]
            if across.any():
                # A ledger line belongs to its note and is short; a line that runs on past it strikes out words.
                at = low + int(np.argmax(across.sum(axis=1)))
                row = ledger[at]
                start = x0 + int(np.argmax(row[x0:x1 + 1]))
                left_end, right_end = start, start
                while left_end > 0 and row[left_end - 1]:
                    left_end -= 1
                while right_end + 1 < len(row) and row[right_end + 1]:
                    right_end += 1
                if right_end - left_end + 1 <= ARC_PAIR_HIGH[3] * own:
                    crossed = True
                    mid = (rows[2] - at) / (own / 2)
            # A ledger line through the middle is the first one past the staff (a print can set it closer to the
            # staff than a staff space): the note stands on it.
            place = (6 if mid > 0 else -6) if crossed and 5 <= abs(mid) <= 7 else round(mid)
            inside = abs(place) + notes - 1 <= 4
            after = any(head['staff'] == staff and head['cx'] < x0 for head in heads)
            side = int(round(ARC_ALONE[0] * own))
            beside = max(int(strokes[y0:y1 + 1, max(0, x0 - side):max(0, x0 - 1)].sum()),
                         int(strokes[y0:y1 + 1, x1 + 2:x1 + 1 + side].sum()))
            m = 0.2 * space
            covered = any(other['x0'] <= x1 + m and other['x1'] >= x0 - m and other['y0'] <= y1 + m
                          and other['y1'] >= y0 - m for other in heads)
            ok = (ARC_PAIR[0] <= outer <= ARC_PAIR[1] and ARC_PAIR[2] <= paper <= ARC_PAIR[3]
                  and min(usual) >= ARC_PAIR[4] and single >= ARC_PAIR_HIGH[4] and lean <= ARC_PAIR_HIGH[5]
                  and notes and (abs(mid - place) <= ARC_PAIR[5] and inside
                                 or crossed and notes == 1 and abs(place) == 6)
                  and between.sum() <= ARC_ALONE[1] * own * own and after and cx > ends[staff] + 0.3 * space
                  and beside <= ARC_ALONE[1] * own * own and not covered)
            if ARC_SEEN is not None:
                ARC_SEEN.append({'box': [x0, y0, x1, y1], 'staff': staff, 'top': top, 'bottom': bottom,
                                 'outer': outer, 'paper': paper, 'usual': usual, 'high': high, 'mid': mid,
                                 'notes': notes, 'single': single, 'lean': lean, 'between': int(between.sum()),
                                 'crossed': crossed, 'inside': inside, 'after': after, 'beside': beside / own / own,
                                 'covered': covered, 'ok': bool(ok)})
            if not ok:
                continue
            for at_place in ([place] if notes == 1 else [place + 1, place - 1]):
                y = rows[2] - at_place * own / 2
                out.append({'x0': x0, 'y0': int(round(y - own / 2)), 'x1': x1, 'y1': int(round(y + own / 2)),
                            'cx': cx, 'cy': y, 'staff': staff, 'place': float(at_place), 'hollow': True,
                            'hole': 0.0, 'stems': [], 'mark': None, 'from_hole': True, 'core': None, 'alt': None,
                            'ledgers': [], 'arcs': True})
    return out


OPEN_WHOLE = (0.8, 0.9, 0.6, 1.2, 15, 0.8, 1.2, 0.5, 1.2)   # a whole note whose thin rim broke (see open_wholes): its
#   inside holds at least this share of the page's usual hole and is at most this many staff spaces wide, its width is
#   from this to this share of its height, ink closes it in at least this many of 16 ways, its ring of ink without the
#   staff lines is from this to this many staff spaces high, a hollow head of its system stands within this many staff
#   spaces of its column, and its ring is at least this many times as wide as the page's heads
OPEN_WHOLE_SEEN = None   # a list: every inside that open_wholes asks, with its measures (a census at the reader's own step)
OPEN_SIDE = (2.0, 0.5, 1.2)   # the side of such a whole note that the hollow head a third over or under it took for its
#   stem (the two heads stand as an 8): a stem shorter than this many staff spaces that ends in the whole note's box,
#   of a hollow head at most this many staff spaces beside its column and this many over or under its middle (None: off)
OPEN_SIDE_SEEN = None    # a list: every stem that OPEN_SIDE takes


def _ring_ink(layers: dict, heads: list[dict], x: int, y: int, wide: int, high: int, inside: np.ndarray,
              space: float) -> tuple[float, float]:
    """How high the ink around an inside is, without the staff lines and without the heads that were read near it:
    in the columns of the inside, and over the whole piece of ink."""
    ink, lines = layers['ink'], layers['lines']
    pad = int(2.5 * space)
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(ink.shape[1], x + wide + pad), min(ink.shape[0], y + high + pad)
    free = (ink[y0:y1, x0:x1] > 0) & ~(lines[y0:y1, x0:x1] > 0)
    for head in heads:
        if head['x1'] >= x0 and head['x0'] < x1 and head['y1'] >= y0 and head['y0'] < y1:
            free[max(0, head['y0'] - y0):max(0, head['y1'] - y0 + 1), max(0, head['x0'] - x0):max(0, head['x1'] - x0 + 1)] = False
    own = np.zeros(free.shape, np.uint8)
    own[y - y0:y - y0 + high, x - x0:x - x0 + wide] = inside
    ring = cv2.dilate(own, np.ones((3, 3), np.uint8)) > 0
    count, labels = cv2.connectedComponents(free.astype(np.uint8), connectivity=8)
    near = set(np.unique(labels[ring & free])) - {0}
    if not near:
        return 0.0, 0.0
    piece = np.isin(labels, list(near))
    rows = np.nonzero(piece.any(axis=1))[0]
    columns = np.nonzero(piece[:, x - x0:x - x0 + wide].any(axis=1))[0]
    return ((columns[-1] - columns[0] + 1) / space if len(columns) else 0.0), (rows[-1] - rows[0] + 1) / space


def _level_free(layers: dict, space: float) -> np.ndarray:
    """The ink without the staff lines and without the ledger lines (level, thin and a staff space long or more)."""
    bare = layers['bare'] > 0
    level = _arc_morph(bare, int(round(space)), 1, False)
    return bare & ~(level & ~_arc_morph(level, 1, int(round(0.3 * space)), False))


def _ring_wide(strokes: np.ndarray, x: int, y: int, wide: int, high: int, inside: np.ndarray, rim: int,
               space: float) -> int:
    """How wide the ink around an inside is in the rows of the head, without the staff lines and the ledger lines."""
    y0, y1 = max(0, y - rim), min(strokes.shape[0], y + high + rim)
    x0, x1 = max(0, x - int(1.5 * space)), min(strokes.shape[1], x + wide + int(1.5 * space))
    window = strokes[y0:y1, x0:x1].astype(np.uint8)
    own = np.zeros_like(window)
    own[y - y0:y - y0 + high, x - x0:x - x0 + wide] = inside
    ring = cv2.dilate(own, np.ones((5, 5), np.uint8)) > 0
    count, labels = cv2.connectedComponents(window, connectivity=8)
    near = set(np.unique(labels[ring & (window > 0)])) - {0}
    if not near:
        return 0
    columns = np.nonzero(np.isin(labels, list(near)).any(axis=0))[0]
    return int(columns[-1] - columns[0] + 1)


def _closed_round(ink: np.ndarray, cx: float, cy: float, reach: float) -> int:
    """In how many of 16 ways from a middle ink stands within reach."""
    count = 0
    for way in range(16):
        dx, dy = np.cos(way * np.pi / 8), np.sin(way * np.pi / 8)
        for step in np.arange(0.5, reach, 0.5):
            px, py = int(round(cx + step * dx)), int(round(cy + step * dy))
            if not (0 <= px < ink.shape[1] and 0 <= py < ink.shape[0]):
                break
            if ink[py, px]:
                count += 1
                break
    return count


def open_wholes(layers: dict, heads: list[dict], ends: list[float]) -> list[dict]:
    """The whole notes whose thin rim broke (OPEN_WHOLE): hollow heads with no stem, read from their inside where no
    head was read. A print draws a whole note with bold sides and a hairline over and under its inside, and a copy
    breaks the hairline: the inside is open paper then (layers['open_holes']), and a ledger line or a staff line
    through the head cuts it into two halves, which the line's own ink joins again. hole_heads() reads such an inside
    only with a stem, and only as wide as a half note's lies on its side.

    A census of every such inside of the clean pages, each looked at, gave the shape. A whole note's inside is round
    or stands a little upright, and is no wider than a head's inside: the paper under a fermata, the C of common time
    and the cells of beams and slurs are wider. The ink closes it in nearly every way, and the ring of ink around it
    without the staff lines is as high as a head: the cell between a flag and its stem goes on along the stem. Past
    the staff the head stands on the ledger lines that lead to it, and never in a row of words: the bowls of the
    letters over and under a staff have the same shape, and a beam or the strokes of the letters can pass for a
    ledger line.

    A rule for the print. In its first form the shape alone read 36 heads on 25 pages of LitChoir and one of the fresh
    set (21 notes gained and 20 lost): the bowls and cells of letters, printed and by hand (KONTAKION, a C of a title,
    an R), the cell of a bold head or of a dark dot on a thick copy, a pencil ring, and half notes whose stem it did
    not see. A printed whole note is wider than the page's heads (its ring without the staff lines and the ledger
    lines), and it holds with the other voices: a hollow head of its system stands in its column. That leaves lone
    whole notes that the first form read rightly on copies that are not clean, and it reads 16 heads on 13 pages and
    none of the fresh set.

    Where two whole notes stand as an 8, the head over or under the broken one had taken the broken one's side for a
    short stem that ends in its box (OPEN_SIDE). With the new head beside it, that stem made it a half note and
    crossed the two voices, so the stem goes (3 heads, each looked at)."""
    if not OPEN_WHOLE or layers.get('open_holes') is None:
        return []
    space = layers['space']
    holes, ink, open_holes = layers['holes'], layers['ink'], layers['open_holes']
    own = [float((holes[head['y0']:head['y1'] + 1, head['x0']:head['x1'] + 1] > 0).sum()) for head in heads
           if head['hollow'] and not head.get('thin') and not head.get('from_hole')]
    if len(own) < 3:
        return []
    usual = float(np.median(own))
    rim = max(2, int(round(HOLE_RIM * space)))
    # The halves of an inside that a line cuts: the line's ink between two pieces of paper, one right over the
    # other, where one of them at least is open.
    paper = ((holes > 0) | (open_holes > 0)).astype(np.uint8)
    near = int(round(max(staff['thick'] for staff in layers['staves']) + 1))
    over, under = np.zeros_like(paper), np.zeros_like(paper)
    for step in range(1, near + 1):
        over[step:] |= paper[:-step]
        under[:-step] |= paper[step:]
    through = ink & over & under
    out = []
    strokes = None
    for joined in (False, True):
        found = (paper | through) if joined else (open_holes > 0).astype(np.uint8)
        count, labels, stats, centres = cv2.connectedComponentsWithStats(found, connectivity=4)
        for index in range(1, count):
            x, y, wide, high, area = (int(value) for value in stats[index])
            if not OPEN_WHOLE[0] * usual <= area <= OPEN_HEADS * space * space or wide > OPEN_WHOLE[1] * space \
                    or not OPEN_WHOLE[2] * high <= wide <= OPEN_WHOLE[3] * high:
                continue
            inside = (labels[y:y + high, x:x + wide] == index).astype(np.uint8)
            if joined and not (through[y:y + high, x:x + wide][inside > 0].any() and open_holes[y:y + high, x:x + wide][inside > 0].any()):
                continue      # a hole that no line cuts, or two closed halves (hole_heads asked them)
            cx, cy = float(centres[index][0]), float(centres[index][1])
            if any(head['x0'] - 2 <= cx <= head['x1'] + 2 and head['y0'] - 2 <= cy <= head['y1'] + 2 for head in heads + out):
                continue
            staff = _staff_of(layers, cx, cy)
            if staff is None or cx < ends[staff] + 0.3 * space:
                continue
            lines = layers['staves'][staff]
            place = pitch_place(lines, cy)
            mark = {'x0': max(0, x - rim), 'x1': min(ink.shape[1] - 1, x + wide - 1 + rim), 'y0': max(0, y - rim),
                    'y1': min(ink.shape[0] - 1, y + high - 1 + rim), 'cx': cx, 'cy': cy}
            ways = _closed_round(ink, cx, cy, 1.6 * lines['space'])
            column, piece = _ring_ink(layers, heads, x, y, wide, high, inside, lines['space'])
            stems = [way for way in (_way(layers, mark, True, True), _way(layers, mark, False, False)) if is_stem(way, space)]
            head = {'x0': mark['x0'], 'y0': mark['y0'], 'x1': mark['x1'], 'y1': mark['y1'], 'cx': cx, 'cy': cy,
                    'staff': staff, 'place': place, 'hollow': True, 'hole': area / ((wide + 2 * rim) * (high + 2 * rim)),
                    'stems': [], 'mark': None, 'from_hole': True, 'core': None, 'alt': None, 'open': True,
                    'open_whole': True, 'ledgers': []}
            words = any(band['x0'] <= cx <= band['x1'] and band['top'] - 0.3 * space <= cy <= band['bottom'] + 0.3 * space
                        for band in layers.get('words') or [])
            found_place = place
            if abs(place) > 4.6:
                head['ledgers'] = ledger_lines(layers, lines, head)
                found_place = ledger_place(layers, lines, head)
            system = lines['system']
            partner = any(other['hollow'] and layers['staves'][other['staff']]['system'] == system
                          and abs(other['cx'] - cx) <= OPEN_WHOLE[7] * space for other in heads)
            ok = (not stems and ways >= OPEN_WHOLE[4] and OPEN_WHOLE[5] <= column <= OPEN_WHOLE[6]
                  and piece <= OPEN_WHOLE[6] and partner)
            outer = 0.0
            if ok:
                if strokes is None:
                    strokes = _level_free(layers, space)
                outer = _ring_wide(strokes, x, y, wide, high, inside, rim, space) / (layers.get('head') or (space, space))[0]
                ok = outer >= OPEN_WHOLE[8]
            if abs(place) > 4.6:
                ok = ok and not words and found_place is not None
            if abs(place) > 5.5:
                # The ledger lines lead to the head: one for a head on the first line past the staff or in the space
                # past it, two for the next line and space.
                ok = ok and found_place is not None and len(head['ledgers']) >= np.ceil((abs(found_place) - 5.5) / 2)
            if OPEN_WHOLE_SEEN is not None:
                OPEN_WHOLE_SEEN.append({'x': cx, 'y': cy, 'staff': staff, 'place': place, 'found': found_place,
                                        'joined': joined, 'wide': wide / space, 'high': high / space, 'area': area / usual,
                                        'ways': ways, 'column': column, 'piece': piece, 'stems': len(stems),
                                        'words': words, 'ledgers': len(head['ledgers']), 'partner': partner,
                                        'outer': outer, 'ok': bool(ok)})
            if not ok:
                continue
            head['place'] = float(found_place)
            # The pieces of the broken rim that were read as small heads with no stem.
            head['replaces'] = [other for other in heads if not other['hollow'] and not other['stems']
                                and mark['x0'] <= other['cx'] <= mark['x1'] and mark['y0'] <= other['cy'] <= mark['y1']
                                and other['y1'] - other['y0'] + 1 < OPEN_PIECE * (layers.get('head') or (space, space))[1]]
            out.append(head)
            if OPEN_SIDE is None:
                continue
            for other in heads:
                if not other['hollow'] or abs(other['cx'] - cx) > OPEN_SIDE[1] * space \
                        or abs(other['cy'] - cy) > OPEN_SIDE[2] * space:
                    continue
                side = [stem for stem in other['stems'] if stem['length'] < OPEN_SIDE[0] * space
                        and mark['x0'] - 2 <= stem['x'] <= mark['x1'] + 2 and mark['y0'] - 2 <= stem['end'] <= mark['y1'] + 2]
                if side:
                    other['stems'] = [stem for stem in other['stems'] if all(stem is not one for one in side)]
                    if OPEN_SIDE_SEEN is not None:
                        OPEN_SIDE_SEEN.append({'x': other['cx'], 'y': other['cy'], 'whole': (cx, cy),
                                               'stems': [(stem['direction'], stem['length'] / space) for stem in side]})
    return out


# ----------------------------------------------------------------------------------------------------------------
# Lengths: flags, beams and dots

TAIL_ZONE = 1.3      # flags and beams stand in this many staff spaces from the far end of a stem
TAIL_WIDE = 0.45     # there the ink reaches at least this many staff spaces from the stem, to one side
TAIL_HIGH = 0.12     # for at least this many staff spaces of the stem's rows
TAIL_THICK = 0.22    # a beam or a printed flag is this thick; thinner ink is a flag only when it is a hook (see tails)
BEAM_FAR = 1.2       # a beam reaches at least this many staff spaces from its stem; a flag is shorter
BEAM_NEXT = 7.0      # the next stem of a beam stands at most this many staff spaces away
BEAM_STRAIGHT = (1.5, 0.25)   # a beam without a witness at the next stem is straight: ink that leaves the stem's end for
#                      this many staff spaces or more and bends this far from the line between its two ends is a slur
#                      (None: off)
BEAM_USUAL = 0.8     # a beam without a witness at the next stem is at least this share as thick as the page's beams
BEAM_CROSS = 0.5     # a slur that passes the end of a stem hangs on both sides of it at one level, as the beam of a
#                      middle note does, and the flag of the next note can be its witness. At both sides it is at
#                      most this share as thick as the page's beams (20 such stems of LitChoir's pages, each looked
#                      at, all slurs and ties; the slimmest true beam that hangs so is 0.52) (0: off)
BEAM_PAST = 0.5      # a beam ends at the outer stems of its run. Where the ink that joins a run of stems also hangs on
#                      past both of its outer stems, at the level where it joins them, and ends free at both sides (no
#                      stem within this many staff spaces of its end), it is a slur under or over the run, and no beam:
#                      a slur that touches the ends of two stems was read as their beam, and a dotted quarter as a
#                      dotted eighth (nativity-troparion, two scans). By the hanging ink alone, the first form took 16
#                      runs on LitChoir's pages, each looked at: 11 slurs, the ledger dashes of a copy by hand, two true
#                      beams that lie along a staff line and go on to stems that the reader did not read (4 notes
#                      lost), the band of a marker over a label and a staff line under the stem ends of flagged notes.
#                      The last four end at a stem or a bar line. None on the fresh set (0: off)
BEAM_SECOND = 0.6    # a second beam or flag at a stem is one of its own when it is at least this share as thick as the
#                    page's usual beam (None: off): slimmer ink beside a beam is a bow that lies on the beam
BEAM_SIDES = 0.8     # a piece of a beam at the left of a stem and one at its right are one beam when their rows are
#                      less than this share of the thicker one's thickness apart (0: off; before: 0.35 staff spaces)
BEAM_PAIR = (0.14, 0.6, 0.65, 0.75)   # a slim beam of a fine engraving: long ink under TAIL_THICK but this thick, at most
#                      this high where it hangs on the stem, at most this far from the stem's end (staff spaces),
#                      straight, the next stem shows such ink or a beam from its other side, and it is this share
#                      as thick as the page's own beams, when the page has thick beams (None: off)
BEAM_TWO = (1.0, 1.55, 0.45, 0.85, 1.75, 0.8, 0.04, 0.15)   # two printed beams that a staff line joins are one block of ink
#                      (None: off). At a stem with one beam counted, the beam's piece at one side is a full flat block
#                      from [0] to [1] staff spaces thick, its piece at the other side one from [2] to [3], and the thick
#                      one is at least [4] times the other: the thick piece is two beams, and the note a sixteenth. A
#                      block fills this share [5] of its box, and the thick one leans at most [6]: a beam that a
#                      hand drew fat is neither. The stem at the other end of the thick piece has the same ink, as thick within this
#                      share [7], and two beams too
BEAM_EDGE = 0.3      # one beam can be TAIL_THICK at one stem and slimmer at the next: a beam under this thickness that the
#                      next stem does not show as a thick beam is looked at as a slim beam too (see BEAM_PAIR; None: off)
SLIM_BOTH = True     # one slim beam joins two stems: where the piece at one stem was taken as a slim beam (BEAM_PAIR), the
#                      slim piece that faces it at the other stem is that beam too, though it is slimmer than the page
#                      takes a beam alone (a hairline beam swells and thins along its way; False: off)
LOOP_NEAR = 1.8      # the loop of a flag lies at most this many staff spaces from the far end of the stem
FLAG_BACK = 0.08     # a printed flag comes back toward the head by this many staff spaces while it leaves the stem
FLAG_HOLE = (0.7, 0.75, 0.3, 0.7)   # a printed flag that reaches 0.6 staff spaces or a little more (under this) shows no
#                            way back yet: it is a flag when it is this high and leans from this to this much toward
#                            the head (None: off)
FLAG_NARROW = (0.6, 0.2)   # a narrow printed flag hugs its stem: it reaches under 0.6 staff spaces from it, but it is
#                            this many staff spaces high and leans this much toward the head (None: off). A limit on
#                            how long it touches the stem was measured too: it lost 11 notes for 4.
BOW_THIN = 1.0       # a thin head this near (staff spaces) at the right of the down stem of a note with a flag, in the
#                      far half of that stem, is the bow of that flag (0: off)
FLAG_BOW = (1.8, 0.7, 1.3, 0.8)   # the flag of a down stem that is a bow: it leaves the head or the stem beside it,
#                            bulges to the right and comes back to the stem before its end. The ink right of the stem
#                            is this many staff spaces high, reaches from this to this far from the stem and no
#                            farther, and paper lies between it and the stem for this many staff spaces (None: off)
STEEP_FLAG = (2.2, 0.45, 0.4, 0.95, 0.25, 0.5, 0.3, 0.8, 0.25)
#                            one old engraving draws the flag of an eighth as a thin straight stroke that leaves the
#                            stem steeply, back toward the head: a Y at the end of a stem down (the stem goes on past
#                            the fork) and a Λ at the top of a stem up (the stroke hugs the stem first), and the older
#                            rules look for a flag at the very end of the stem. The stroke is followed in the first
#                            number of staff spaces from the stem's end; it leaves the stem the second number or more
#                            from the end, reaches from the third to the fourth number to the right and ends in paper,
#                            comes back toward the head by the fifth number and by the sixth share of how far it
#                            reaches, is at most the seventh number wide, touches the stem in one run of rows, on at most
#                            the eighth share of its height, and only goes away from the stem to its tip; no ink crosses
#                            the stem within the ninth number of the rows where it leaves it, and the stroke does not go
#                            on straight at the other side of the stem (a slash across a stem) (None: off). A census of
#                            every stem that the first form (no limits for where the stroke leaves and how long it
#                            touches) gave a flag on LitChoir's pages: 104 stems, 24 notes gained and 41 lost, nearly all
#                            losses on copies by hand, where a stroke that hugs the stem all its way or a thin flag at the
#                            stem's end is a stem or a mark by hand as often as a flag. The print's flags leave the stem
#                            0.48 staff spaces or more from its end and touch it on 0.77 of their height at most. The
#                            rule then takes 21 stems on 13 pages, each looked at: 20 eighths (8 of them were read as
#                            quarter notes) and the wire of a paperclip, which is no note. A rule for one print, with its
#                            likes on two copies by hand.
STEEP_SEEN = None    # a list: every stem that STEEP_FLAG gives a flag, with its measures (a census)
DOT_REACH = 1.3      # a dot stands at most this many staff spaces right of its head
DOT_NEAR = 0.3       # and at least this many
DOT_UNDER = 0.6      # its middle lies at most this many staff spaces under the middle of the head (and 0.7 over it)
DOT_BETWEEN = None   # and not from this to this many staff spaces under it: a dot stands in a space, at the height of
#                    the head or half a staff space from it (None: off)
DOT_UPPER = 0.3      # one dot between two heads of a column (None: off): a dot that stands this many staff spaces or
#                    more under the middle of a head, and as much over the middle of a head below that takes it too, is
#                    the dot of the lower head. The upper head keeps it when it is a note of the same kind (hollow or
#                    filled, as many flags or beams): then one dot can stand for both. A dot of its own it has anyway.
DOT_HIGH = 0.9       # a dot is at most this high, in staff spaces
DOT_SLIM = 0.38      # and at least this wide for its height: a hand draws a dot as a short stroke
DOT_FLAT = 1.7       # and at most this wide for its height
DOT_FILL = 0.55      # and its ink fills at least this share of its box
DOT_SMALL = 0.18     # and each of its sides is at least this many staff spaces: a smaller piece is a speck of the copy
#                    or the cut end of a ledger line (0.14: as it was)
DOT_TWO = (0.7, 1.25, 0.12, 0.7, 0.75, 1.4, 1.6)   # a second dot (None: off): a dot from [0] to [1] staff spaces right of
#                      the first, at most [2] higher or lower, with paper between them: the note is one and three
#                      quarters as long as its head says. The two dots are alike (the smaller has this share [3] of
#                      the larger one's ink) and round (from [4] to [5] as wide as high): a speck of the copy beside
#                      a dot is neither. No dot stands over or under the second one, up to [6] staff spaces away:
#                      these are the two dots of a repeat sign
DOT_ASK = (0.75, 0.45, 0.8)   # a mark at the right of a head that is nearly a dot: at most this many staff spaces wide,
#                    its ink at least this share of its box, its middle at most this far over the middle of the head,
#                    of any shape. It is no dot by itself: music.agree_lengths takes it for one where the sure steps
#                    under the note add up to one and a half of the note (None: off)
DOT_CLOSE = (0.15, 0.25, 0.65, 1.5)   # a dot stands this near to its head (less than DOT_NEAR) when each of its sides is
#                    at least this many staff spaces, it is round (from this to this wide for its height: a piece
#                    of a broken stem is slim) and no other head has it as its dot: a tight engraving (None: off)
DOT_BESIDE = (0.5, 12.0, 0.4, 0.3)   # a dot that a print drew as a short dash or a hand as a stroke: a mark that is nearly a dot (DOT_ASK)
#                    and no dot by its shape, beside a head without a dot, is its dot when another head of the column
#                    has a dot: the right edges of the two heads at most [0] staff spaces apart, their middles at most
#                    [1] (on one staff or on two staves next to each other), the dash and that dot at most [2] apart
#                    sideways, the dash at most [3] over or under the middle of its head, and the two notes of one
#                    kind (hollow or filled, as many flags or beams). Notes that sound together agree (None: off)
DOT_SURE = (0.055, 0.7, 1.5, 0.25)   # a dot that is sure (head['dot_sure']): its ink is at least [0] staff spaces squared, it is
#                      from [1] to [2] times as wide as high, and its middle lies [3] staff spaces or more from every line
#                      of the staff: a round dot of full size in a space. Of the dots at the heads that the chord rule
#                      of the music step made shorter (music.CHORD_ONE) on LitChoir's scan pages, each looked at, the
#                      printed dots hold 0.067 or more and are 0.74 to 1.2 times as wide as high; the specks of a worn
#                      copy hold 0.043 at most or are slim (0.59 at most); a piece of a thick staff line is as large
#                      as a dot and lies in the rows of the line. A dot that a blurred copy ran into a taller blot is
#                      left out (None: off)
DOT_SPECK = (0.14, 0.15)   # a dot that the print wore smaller than a dot (DOT_SMALL) but each of its sides at least [0] staff
#                    spaces, and otherwise of a dot's shape, beside a head without a dot, is its dot where another head
#                    of the column has a dot (as DOT_BESIDE asks) at most [1] staff spaces from it sideways: a column of
#                    dots stands in one line (None: off)
DOT_TIP = (0.5, 5.0, 0.5, 2.0, 0.6)   # the tip of a tie's bow is no dot (None: off). A tie begins beside its head in a
#                      space and runs flat into the staff line under or over it; the line hides a stretch of the bow, and
#                      the tip that is left before it is as small and as full as a dot. The whole shape makes it a tip.
#                      The mark lies in the rows of the staff line: the line goes on at its left or its right in this
#                      share of the line's thickness or more of the mark's own rows. And the bow comes out of the line
#                      again at the right: a piece of ink this many staff spaces wide or more, which begins from the
#                      third to the fourth number of staff spaces right of the mark's left edge, and whose first staff
#                      space lies within the last number of staff spaces of the line and is at most as thick. The first
#                      half alone is true of the dots of a hand, which stand on the staff lines.
DOT_LINE = (0.5, 0.067)   # a dot that sits on a staff line keeps a hair of the line under or over it, where the line was
#                    taken away around it, and is no dot by its shape. Measured without the rows of the line (where the
#                    line runs on at its left or its right) it is one: its other ink is one run at one side of the line,
#                    its ink in the rows of the line is at most [0] of its width, and it holds at least [1] staff spaces
#                    squared of ink, as the printed dots of DOT_SURE's census do. A stroke across a line (a bar line, the
#                    bar of an ison's breve, a stem, the tick of a hand) has ink at both sides of the line; the end of a
#                    flag that runs into a line, a speck of the scan and a short stroke that stands on a line are smaller
#                    (None: off)
DOT_LINE_SEEN = None # a census: a list of the heads that take such a dot (None: none)
DOT_GREY = (0.1, 0.25, 0.6)   # a speck of a grey streak, a pencil mark or a smudge is no dot of a black head: the ink of the
#                    piece off the rows of the staff lines is at least [1] of its ink and at most [0] of it is black
#                    (layers.BLACK), and the ink in the head's box is at least [2] black. A printed dot is as black as its
#                    head; a dot that sits on a staff line has most of its ink in the line's rows, and its rim off the
#                    line is grey. (A census at this step on every scan page of LitChoir: of the 2,861 dots that heads
#                    take, the ones whose ink off the lines holds at most 0.1 black and that stand beside a head at least
#                    0.6 black were looked at, each: grey streaks, the tails of pencil lines, the textured paper of one
#                    copy, the curl at the tip of a heavy head, and one true dot of a pale print beside a head that is
#                    black by chance, which DOT_GREY_PAGE keeps. The true dots of black heads on the other pages hold
#                    0.21 black or more off the lines.) None: off
DOT_GREY_PAGE = 0.3  # ... and only where the page's other dots are black: of the pieces of a dot's shape that stand where
#                    a head's dot stands (DOT_REACH, DOT_UNDER) and that are not that grey, half or more hold this share
#                    of black off the lines or more. One pale print prints its dots grey beside heads that are black at
#                    places, and the measure of black is the page's own: on its two pages every such piece is that grey
#                    (none on the other pages that the rule changes; on every page of LitChoir 384 of the 423 pages with
#                    such pieces have them all black, and the pale print's pages none).
DOT_GREY_SEEN = None # a census: the pieces that DOT_GREY_PAGE measures on each page, and its verdict (None: none)
DOT_JOIN = (0.12, 0.6, 0.7, 1.4, 0.2, 1.3)   # a printed dot that a pen line, a slur, a staff line or its own head
#                    joins is one piece with that ink, and no piece of a dot's shape. Notes that sound together agree on
#                    a dot: where the head of the other voice in the column has a dot, a blot of that dot's size at that
#                    dot's column, in this head's rows, is this head's dot. [0] the blot's middle at most this many staff
#                    spaces from the column of the other dot; [1] the blot is the ink that an ellipse of this share of
#                    the dot's smaller side keeps; [2], [3] its area, width and height this share of the dot's; [4] its
#                    middle at least this many staff spaces from the row of a line (a dot stands in a space, and the
#                    end of a ledger line is no dot); [5] the piece that holds it is more than this many times as large
#                    as the dot (a piece of a dot's size alone was judged by the steps before). A census of every head
#                    without a dot whose column holds a dotted head of its staff (617 on LitChoir's pages): of the 18
#                    blots that are joined, 10 are dots that the typed hymn has and the reader lost, 5 dots that the
#                    music step gave back, 1 a printed dot that the typed hymn leaves out and the vote gave, the dot of
#                    a breve, and a dash of a dashed bar line by hand (DOT_JOIN_ROUND). On every page: 14 pages of
#                    LitChoir change, 9 notes gained and 1 lost by the count (a tied vote on a copy by hand that the
#                    page's full bar settles otherwise once more bars add up), none on the fresh set.
DOT_JOIN_ROUND = 0.5  # ... and the blot and the other dot are each at least this wide for their height and this high
#                    for their width: a print's dot is round. A hand's dashed bar line through two voices' notes gave one
#                    note a dash as its dot and the other note the next dash as a blot (0.42 and 0.39; the printed dots
#                    of the census 0.59 or more)
DOT_JOIN_SEEN = None # a census: every head that DOT_JOIN gives a dot, with its measures
DOT_BODY = 0         # 1.5: a head beside the staff whose mark holds its ledger line is this many times as wide as the
#                    heads of the page or more: the line runs on under the dot. The dot is then measured from the
#                    ink of the head in the dot's own rows, not from the end of the line. Off: alone it gained 6
#                    notes on all of LitChoir and lost 32 (none and 8 on the clean copies).
SHARED_TAILS = 'flags'   # a head with two stems has the flags of its one stem at the other stem too (True); 'flags': a
#                      beam stays at its own stem where the other stem ends in paper (SHARED_FREE). A beam joins the
#                      stems of one voice, and the stem of the other voice that ends free is a quarter note: one print
#                      sets the alto's quarter note under the soprano's beamed eighth, on one head. A hand that draws
#                      the flag at one stem only draws a flag; a hand's beam that the reader does not see at the other
#                      stem leaves ink at its end. The beam goes on from the shared head to the next note: the free
#                      voice holds its quarter note under that note. Where the shared head ends its beam, the next
#                      head is both voices' again, and a hand left the flag out. (False: off)
SHARED_FREE = (1.5, 0.4, 0.6, 0.02)   # the stem ends in paper: beside its end, this many staff spaces to each side and
#                      from the first number of staff spaces before the end to the second past it, at most the last
#                      share is ink (the staff lines count: a stem that ends in the staff does not end free)
RING_FLAG = (0.45, 0.75, 0.25, 0.5, 0.4)   # a hollow head with the ink of a printed flag at its stem: one piece at the right
#                      of the stem's end and none at its left, from this to this many staff spaces far, from this to this
#                      thick, leaning this much, and no beam. A copy that burns out its filled heads leaves such rings: it
#                      is no flag of a half note. The ink is asked of each stem alone: a head that two voices share
#                      is such a ring for the voice whose stem has the flag. music._bar_steps takes the note for an
#                      eighth where another voice of its step says an eighth (None: off)
TAIL_START = 0.55    # the hook of a flag begins this near to the end of its stem, in staff spaces
THIN_BEAM = (0.2, 0.85, 0.6)    # a beam that a hand drew as one thin line from the end of a stem to the end of the next:
                                # ink at most this far (staff spaces) from the straight line, on this share of the way
                                # with the staff lines it crosses, and on this share without them (None: off)
STEM_TURN = 0.6                 # the bend of a stem is measured over twice this many staff spaces before its end
STEM_SLUR = (0.2, 0.4, 0.25, 0.03, 0.2)   # a slur that joins the ends of two stems: both stems bend toward each other at
                                # their ends by this many staff spaces, the stroke is at most this thick, the two stems
                                # turn there by this much together (STEM_TURN; the stems of a hand that lean toward
                                # each other do not turn), and the stroke is round at both stems: its outer edge lies
                                # this far toward the heads at each, and this far at both together, from the straight
                                # line through its middle half (a beam has square corners) (None: off)
THIN_PRINT = 0.45               # a page whose usual beam is this many staff spaces thick or more is a print with thick beams:
#                                 a line from the end of a stem to the end of the next is a slur there when the ink that
#                                 leaves each of the two ends is a bow that bends away from the heads (BEAM_STRAIGHT), and
#                                 none of its stems shows a beam of its own. (A thick beam that no stem shows as its own
#                                 is found as such a line too, and it is straight.) (None: off)
THIN_BEAM_HALF = (0.4, 0.1, 0.16, 0.08, 0.65)   # a slanted beam that runs into a staff line before the next stem: the line
#                                 from the end of one stem to the end of the next is ink from one stem on this share of the
#                                 way or more (less than THIN_BEAM asks) and hidden in a staff line from there to the other
#                                 stem, it rises or falls by this share of its length or more, the middle of its ink stays
#                                 within this many staff spaces of the line, at most this share of the way is hidden
#                                 elsewhere, and it rises or falls by at most this last share of its length. (A census of
#                                 every pair of stems of LitChoir's scan pages whose line is ink or hidden nearly all the way,
#                                 3,449, each with the typed lengths of its notes: 34 are hidden at one stem only on more than
#                                 THIN_BEAM allows. The eleven that pass are beams, and they rise by 0.11 to 0.21. A level
#                                 line says nothing: two stems that end at one staff line have that line between their ends,
#                                 and a tie or a ledger line at one of them is its ink (five such pairs, straight too, none a
#                                 beam). Ink that only touches the edge of the way is a slur or the next staff line. A steep
#                                 line is the stem of the next note itself: beside a note by hand a blot was read as a head
#                                 with a short stem, and the line from that stem's end to the end of the note's own stem rose
#                                 by 2.5. No beam of the clean copies rises by more than 0.65. That pair holds a note that is
#                                 not there, so the typed lengths gave it no label, and the reading of every page showed it.)
#                                 (None: off)
THIN_BEAM_ENDS = 0.3            # and it has its ink in the first and the last part of the way, this long (0: off)
THIN_BEAM_UNDER = True          # at one of its ends the line may be hidden in a staff line
THIN_BEAM_FAT = 0.5             # a staff line that hides the beam is thicker there, by this share of its thickness (0: off)
THIN_BEAM_HIDDEN = (0.6, 0.9, 0.1)   # a fine engraving's beam that runs from a staff line at one stem to a staff line
#                                 at the next is hidden at both ends: each end is in a line for at most this many staff
#                                 spaces, the way between is ink on this share of its columns, and that ink is straight: the
#                                 middle of its rows bends from a straight line by at most the last number of staff spaces
#                                 (a slur that arches between two stem ends on two lines bends by 0.2; None: off)
THIN_BEAM_OVER = 0.6            # a thin beam passes over a stem between its two stems that ends this many staff spaces before it (0: off)
THIN_BEAM_STAFF = True          # the thickness of a staff line that hides a beam is that of the beam's own staff
THIN_BEAM_END = 0.0             # the beam may meet a stem this many staff spaces past the end that was found for it (0: off)
WORD_TAILS = True               # a letter beside the end of a stem that ends at the words is no slur that goes on past a
#                                 thin beam
THIN_FULL = True                # a thin beam meets a stem that was cut at the words at the stem's own end, in the rows of
#                                 the words (False: off)
WORD_BEAMS = False              # a beam in the rows of the words counts when the next stem shows it too (measured on the
#                                 clean copies: a slur over a beam at the words then counts as a second beam; kept off)
LAST_HEAD = 'words'             # the flags of a stem hang past the last head on it: 'words' (for a stem that ends at the
#                                 words), 'all' (for every stem), or None (past the stem's own head only)
THIN_BEAM_SIDE = (0.35, 1.3, 1.0, 0.5, 0.6)  # the beam may leave a stem before the end that was found for it (a slur begins
#                                 at the stem's end, and the stem was followed into it): at ink that hangs on the stem at
#                                 the side of the other stem, from this to this many staff spaces before the end, this
#                                 long, and at least this share of the page's usual beam as thick, where the page has one
#                                 (a slur that begins at the side of a stem is slimmer than the page's beams); such a beam
#                                 rises or falls at most this much for each step to the side (the flag of a stem that
#                                 touches the next stem close by is no beam) (None: off)
BAR_MARK = (0.7, 0.9, 0.5, 0.5)  # a hollow mark with a stem is the place where a tie crosses a bar line, and no head: it is
#   at most this share as high as the heads of the page, the column of its stem has ink in this share of the rows from the
#   top line of the staff to the bottom line, and the line goes on at both sides of the mark, which lies in the staff: over
#   this many staff spaces above the mark and below it the column has ink in this share of the rows, the rows of
#   another head not counted (a stem ends at its head: 0.0 there, 0.64 or more at such a mark) (None: off)
THIN_BEAM_CHORD = True          # the stems of the heads of one chord are one stem for a thin beam (False: stems in fixed columns)
PAST_WORDS = True               # past the last stem of a thin beam, ink in the rows of the words is no slur that goes on
PAST_TWO = (0.3, 1.2, 0.7)      # two strokes one over the other before the last stem (from this far to this far before it, in
#                                 this many staff spaces around the beam's line) are a beam and a slur: the ink past the stem
#                                 is the slur's (None: off)
THIN_BEAM_PAST = (0.4, 1.0, 0.45)   # a slur goes on past the last stem: ink from this far to this far past it, at most
                                    # this far from the line (staff spaces; None: off)
PAST_SLIM = (0.35, 0.4, 0.9, 0.33, 0.6)   # the ink that goes on ends in a blob (None: any ink counts): in the first columns
                                    # past the stem (this share of them, the second number) it is a stroke at most this
                                    # many staff spaces high (the first), and in the last columns (the fourth, a share)
                                    # it is this many staff spaces high or more (the third) in this share of them (the
                                    # fifth). That is the end of the beam beside a letter of the dynamics or a sign,
                                    # and a slur only where the two stems bend and turn toward each other as in a slur
                                    # (STEM_SLUR)


def _last_head(heads: list[dict], head: dict, stem: dict, space: float) -> float:
    """The middle row of the last head on the way of a stem from its head to its end: the other heads of a chord
    hang on the same stem, and a head of the other voice may stand on it."""
    up = stem['direction'] == 'up'
    near, past = 0.2 * space, 0.5 * space
    rows = [other['cy'] for other in heads
            if other['x0'] - near <= stem['x'] <= other['x1'] + near
            and (stem['end'] - past <= other['cy'] <= head['cy'] if up else head['cy'] <= other['cy'] <= stem['end'] + past)]
    rows.append(head['cy'])
    return min(rows) if up else max(rows)


def tail_marks(layers: dict, head: dict, stem: dict, last: float | None = None, words: bool = True) -> list[dict]:
    """The pieces of ink that hang on the far end of a stem, without the stem itself. Each: {'right' (True at the
    right side of the stem), 'row' (where it leaves the stem), 'far' (how far it reaches from the stem), 'thick' (how
    thick it is where it has left the stem), 'from_end' (how far from the stem's end it begins), 'back' (how far it
    comes back toward the head while it goes away from the stem; all in staff spaces)}. `last` is the middle row of
    the last head on the stem, when that is not `head` itself: the pieces hang past it. With `words` False the ink
    in the rows of the words counts too."""
    ink, space = layers['bare'], layers['space']
    height, width = ink.shape
    up = stem['direction'] == 'up'
    x, end = int(stem['x']), int(stem['end'])
    inward = int(min(TAIL_ZONE * space, max(0.0, abs((head['cy'] if last is None else last) - end) - 1.0 * space)))
    outward = int(0.3 * space)
    top, bottom = (end - outward, end + inward) if up else (end - inward, end + outward)
    top, bottom = max(0, top), min(height, bottom + 1)
    reach = int(1.6 * space)
    first, last = max(0, x - reach), min(width, x + reach + 1)
    if bottom - top < 2 or last - first < 3:
        return []
    window = ink[top:bottom, first:last].copy()
    # A flag or a beam that crosses a staff line was cut there with the line: the line comes back where ink stands
    # over it and under it.
    lines = layers['lines'][top:bottom, first:last]
    high = int(np.ceil(head['staff_ref']['thick'])) + 3
    near = cv2.dilate(window, np.ones((1, 5), np.uint8))
    window |= cv2.morphologyEx(near, cv2.MORPH_CLOSE, np.ones((high, 1), np.uint8)) & lines
    if stem.get('words') and words:
        # The stem ends at the words (scorereader.words): the ink of the letters is no flag.
        low, high = int(stem['words'][0]) - top, int(stem['words'][1]) + 1 - top
        window[max(0, low):max(0, high)] = 0
    centre = x - first
    band = max(2, int(round(0.13 * space)))
    stem_rows = window[:, max(0, centre - band):centre + band + 1].any(axis=1)
    window[:, max(0, centre - band):centre + band + 1] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(window, connectivity=8)
    pieces = []
    for index in range(1, count):
        px, py, wide, high, area = stats[index]
        right = px > centre
        edge = centre + band + 1 if right else centre - band - 1
        if not 0 <= edge < window.shape[1]:
            continue
        touch = np.nonzero((labels[:, edge] == index) & stem_rows)[0]
        far = (px + wide - 1 - centre) if right else (centre - px)
        if len(touch) == 0 or far < TAIL_WIDE * space:
            continue
        part = labels == index
        side = 1 if right else -1
        # How thick the piece is where it has left the stem: the ink in each column from 0.3 to 0.9 staff spaces.
        columns = [centre + side * step for step in range(int(0.3 * space), int(min(far, 0.9 * space)) + 1)]
        heights = [int(part[:, column].sum()) for column in columns if 0 <= column < window.shape[1]]
        def rows_at(low: float, high: float) -> np.ndarray:
            one, two = centre + side * int(low * space), centre + side * int(high * space)
            return np.nonzero(part[:, max(0, min(one, two)):max(one, two) + 1])[0]

        near, away = rows_at(0.25, 0.5), rows_at(0.65, 1.0)
        back = ((away.mean() - near.mean()) if up else (near.mean() - away.mean())) / space if len(near) and len(away) else 0.0
        # The lean of the whole piece: how far its far third lies toward the head from its first third, for its length.
        reach = far / space
        first, third = rows_at(0.12, 0.12 + reach / 3), rows_at(reach * 2 / 3, reach)
        lean = ((third.mean() - first.mean()) if up else (first.mean() - third.mean())) / far if len(first) and len(third) else 0.0
        pieces.append({'right': bool(right), 'row': float(touch.mean()) + top, 'far': float(far / space),
                       'thick': (float(np.median(heights)) if heights else 0.0) / space,
                       'from_end': float(np.abs(touch + top - end).min()) / space, 'back': float(back),
                       'touch': len(touch) / space, 'lean': float(lean), 'area': float(area) / space ** 2,
                       'high': float(high) / space})
    return pieces


def _bow_flag(layers: dict, head: dict, stem: dict, low: float) -> bool:
    """True when the ink at the right side of a down stem, from under its last head (row `low`) to its end, is the
    bow of a flag (FLAG_BOW): high, near the stem, with paper between it and the stem. A tie or a beam goes on to
    the right; a head or a blot has no paper between it and the stem."""
    ink, space = layers['bare'], layers['space']
    x, end = int(stem['x']), int(stem['end'])
    top = int(low + 0.1 * space)
    bottom = min(ink.shape[0] - 1, end + int(0.3 * space))
    band = max(2, int(round(0.13 * space)))
    first, last = max(0, x - band), min(ink.shape[1] - 1, x + int(FLAG_BOW[2] * space))
    if bottom - top < FLAG_BOW[0] * space or last - first < 2 * band + 3:
        return False
    window = ink[top:bottom + 1, first:last + 1].copy()
    # (As in tail_marks: a staff line comes back where ink stands over it and under it.)
    lines = layers['lines'][top:bottom + 1, first:last + 1]
    high = int(np.ceil(head['staff_ref']['thick'])) + 3
    near = cv2.dilate(window, np.ones((1, 5), np.uint8))
    window |= cv2.morphologyEx(near, cv2.MORPH_CLOSE, np.ones((high, 1), np.uint8)) & lines
    if stem.get('words'):
        window[max(0, int(stem['words'][0]) - top):max(0, int(stem['words'][1]) + 1 - top)] = 0
    edge = 2 * band + 1
    stem_rows = window[:, :edge].any(axis=1)
    window[:, :edge] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(window, connectivity=8)
    for index in range(1, count):
        px, py, wide, tall, area = stats[index]
        if tall < FLAG_BOW[0] * space or px + wide >= window.shape[1] or px + wide - 1 - band < FLAG_BOW[1] * space:
            continue
        if not ((labels[:, edge] == index) & stem_rows).any():
            continue
        part = labels == index
        room = sum(1 for row in part if row.any() and int(np.argmax(row[edge:])) >= 2)
        if room >= FLAG_BOW[3] * space:
            return True
    return False


def _steep_flag(layers: dict, head: dict, stem: dict, last: float) -> dict | None:
    """The measures of the steep flag at a stem (STEEP_FLAG), or None: a thin straight stroke at the right of the stem
    that leaves it a little before its end and goes back toward the head. `last` is the middle row of the last head
    on the stem."""
    ink, space = layers['bare'], layers['space']
    zone, from_low, far_low, far_high, back_low, slope, wide_high, hug, across = STEEP_FLAG
    height, width = ink.shape
    up = stem['direction'] == 'up'
    x, end = int(stem['x']), int(stem['end'])
    inward = int(min(zone * space, max(0.0, abs(last - end) - 1.0 * space)))
    outward = int(0.3 * space)
    top, bottom = (end - outward, end + inward) if up else (end - inward, end + outward)
    top, bottom = max(0, top), min(height, bottom + 1)
    first, final = max(0, x - int(0.8 * space)), min(width, x + int(1.3 * space) + 1)
    if bottom - top < 0.5 * space or final - first < space:
        return None
    raw = ink[top:bottom, first:final].copy()
    if stem.get('words'):
        raw[max(0, int(stem['words'][0]) - top):max(0, int(stem['words'][1]) + 1 - top)] = 0
    # The stroke is followed as in tail_marks, where a staff line comes back where ink stands over it and under it; what
    # crosses the stem is asked without the staff lines.
    window = raw.copy()
    lines = layers['lines'][top:bottom, first:final]
    high = int(np.ceil(head['staff_ref']['thick'])) + 3
    near = cv2.dilate(window, np.ones((1, 5), np.uint8))
    window |= cv2.morphologyEx(near, cv2.MORPH_CLOSE, np.ones((high, 1), np.uint8)) & lines
    if stem.get('words'):
        window[max(0, int(stem['words'][0]) - top):max(0, int(stem['words'][1]) + 1 - top)] = 0
    centre = x - first
    band = max(2, int(round(0.13 * space)))
    stem_rows = window[:, max(0, centre - band):centre + band + 1].any(axis=1)
    cut = window.copy()
    cut[:, max(0, centre - band):centre + band + 1] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(cut, connectivity=8)
    edge_right, edge_left = centre + band + 1, centre - band - 1
    if edge_left < 0 or edge_right >= window.shape[1]:
        return None
    bare = raw.copy()
    bare[:, max(0, centre - band):centre + band + 1] = 0
    _, left_labels = cv2.connectedComponents(bare, connectivity=8)
    left_rows = np.nonzero((left_labels[:, edge_left] > 0) & stem_rows)[0]
    for index in range(1, count):
        px, py, wide, tall, area = stats[index]
        if px <= centre:
            continue
        touch = np.nonzero((labels[:, edge_right] == index) & stem_rows)[0]
        if len(touch) == 0:
            continue
        from_end = float(np.abs(touch + top - end).min()) / space
        far = (px + wide - 1 - centre) / space
        if from_end < from_low or len(touch) > hug * tall or not far_low <= far <= far_high or px + wide >= window.shape[1]:
            continue
        part = labels == index
        ys, xs = np.nonzero(part)
        tip = float(ys[xs >= xs.max() - 1].mean())
        back = ((tip - touch.mean()) if up else (touch.mean() - tip)) / space
        if back < back_low or back < slope * far:
            continue
        # How wide the stroke is: its ink for its length from the stem to its tip.
        length = float(np.hypot(far, back))
        stroke = area / space ** 2 / max(length, 0.1)
        if stroke > wide_high:
            continue
        # No ink crosses the stem where the stroke leaves it (a slur, the bar of a letter).
        if len(left_rows) and np.abs(left_rows[:, None] - touch[None, :]).min() <= across * space:
            continue
        # A slash across the stem goes on straight at its other side (where it crosses a staff line, the ink without
        # the lines can show no piece that touches the stem there).
        rise = (tip - touch.mean()) / max(1.0, float(px + wide - 1 - edge_right))
        reach = int(0.4 * space)
        hits = 0
        for step in range(1, reach + 1):
            col = edge_left - step
            row = int(round(touch.mean() - rise * (edge_right - col)))
            if col < 0 or not 1 <= row < window.shape[0] - 1:
                break
            hits += bool(window[row - 1:row + 2, col].any())
        if hits >= 0.5 * reach:
            continue
        # The stroke leaves the stem once and goes away from it to its tip: it touches the stem in one run of rows
        # (a staff line that it crosses there does not count), and the paper between it and the stem only widens
        # toward the tip (a letter A comes back to its other leg with its bar).
        line_rows = lines.any(axis=1)
        line_rows = line_rows | np.roll(line_rows, 1) | np.roll(line_rows, -1)
        free = np.array([row for row in touch if not line_rows[row]])
        if not len(free) or np.diff(free).max(initial=0) > 0.2 * space:
            continue
        step = 1 if (tip > free.mean()) else -1
        lefts = []
        for row in range(int(free.max() if step > 0 else free.min()), int(round(tip)) + step, step):
            if 0 <= row < part.shape[0] and not line_rows[row]:
                cols = np.nonzero(part[row])[0]
                if len(cols):
                    lefts.append(int(cols.min()))
        if any(later < earlier - 2 for number, earlier in enumerate(lefts) for later in lefts[number + 1:]):
            continue
        return {'from_end': round(from_end, 2), 'far': round(far, 2), 'back': round(back, 2), 'stroke': round(stroke, 2),
                'touch': round(len(touch) / space, 2), 'tall': round(tall / space, 2)}
    return None


def _is_beam(piece: dict) -> bool:
    return bool(piece['thick'] >= TAIL_THICK and piece['far'] >= BEAM_FAR)


def _is_slim(piece: dict, under: float = TAIL_THICK) -> bool:
    """Long ink a little thinner than a beam (thinner than `under`), where a beam hangs: the slim beam of a fine
    engraving (BEAM_PAIR)."""
    return bool(BEAM_PAIR and piece['far'] >= BEAM_FAR and BEAM_PAIR[0] <= piece['thick'] < under
                and piece['high'] <= BEAM_PAIR[1] and piece['from_end'] <= BEAM_PAIR[2])


STEM_BROKEN = (4.0, 0.3, 1.2, 0.6)   # a stem that breaks off before its beam, where the copy left a strip of the page white,
#   goes on after the strip: in its own column, after at most the first number of staff spaces of paper, upright ink
#   stands that is slim for the second number of staff spaces or more and wider than a stem for at most the third
#   number (the beam itself); where it ends a beam hangs on it, and the next stem at that side shows that beam too. No
#   head stands on the way (within the fourth number of staff spaces of the column). The rows of the gap hold no ink
#   over the whole staff: that is the strip. The stem shows no flag and no beam where it breaks off, and it ends at
#   the beam. (Without the strip the rule read what stands past the end of a stem: a second beam, the line of a
#   bracket, and a bold slur over two stems, which is as thick as a beam. Of the 88 stems that the form before led
#   on over a gap of paper in their own column alone, 3 were right and 81 wrong.) (None: off)


LINE_GAP = True     # a stem that stops a little short of a staff line, where a slur lies along the line or crosses it at the
#   stem, was followed over the gap of paper into the line: the layer of the bare ink keeps a line that a slur thickens,
#   and the line with the slur was read as a beam at the stem's end. Where the way ends in the rows of a staff line, the
#   rows before it from that end are ink that is the line with less than a beam beside it (TAIL_THICK), and paper parts
#   them from the stem in the whole ink as well (at most GAP), the stem ends before the gap. A census of every way that
#   ends in the rows of a line over such a gap (238 on LitChoir's pages), with the stem ended there in a second reading,
#   gave the ink beside the line where the length of a note changes: a beam that a hand drew on the top line hangs 0.23
#   staff spaces past it and the other beams more, the slur along the line of holy-saturday-koinonikon 0.17 and a slur
#   across a line on a page of a software-made PDF 0.12. The rule acts at 62 stems on 49 pages of LitChoir, each looked
#   at (each stem stops short of its line in the scan; a few are the strokes of a time signature, a clef or a letter),
#   and at none of the fresh set; the notes change on two pages. (False: off)
LINE_GAP_LOG = None  # a list: (head's middle, the stem's direction, its old end, its new end) where LINE_GAP acts (a census)


def line_gap_stems(layers: dict, heads: list[dict]) -> int:
    """Ends each stem whose way was led over a gap of paper into a staff line before the gap (see LINE_GAP): sets its
    'end' and 'x'. Returns how many stems were ended."""
    if not LINE_GAP:
        return 0
    bare, ink, space = layers['bare'], layers['ink'], layers['space']
    height, width = bare.shape
    band = max(2, int(round(0.13 * space)))
    count = 0
    for head in heads:
        staff = head.get('staff_ref') or layers['staves'][head['staff']]
        thick = float(staff.get('thick') or 3.0)
        for stem in head['stems']:
            inward = 1 if stem['direction'] == 'up' else -1
            end = int(stem['end'])
            line = min(staff['rows'], key=lambda row: abs(row - end))
            if abs(end - line) > thick / 2 + 1.5:
                continue
            x = int(round(stem.get('mid', stem['x'])))
            first, last = max(0, x - band), min(width, x + band + 1)
            # (The way's last column can lie beside the stem's own column where it ran into the wide ink of the line.)
            row = end
            while 0 <= row < height and not bare[row, first:last].any() and abs(row - end) <= 0.3 * space:
                row += inward
            if not 0 <= row < height or abs(row - end) > 0.3 * space:
                continue
            top = row
            while 0 <= row < height and bare[row, first:last].any() and abs(row - end) <= 0.8 * space:
                row += inward
            if not 0 <= row < height or abs(row - end) > 0.8 * space or row == top:
                continue
            start = row
            while 0 <= row < height and not bare[row, first:last].any() and abs(row - start) <= GAP * space + 1:
                row += inward
            gap = abs(row - start)
            if gap < 1 or gap > GAP * space or not 0 <= row < height:
                continue
            if ink[min(start, row - inward):max(start, row - inward) + 1, first:last].any():
                continue      # the stem reaches the line in the whole ink: the gap is the line that the bare ink left out
            if abs(start - top) - thick >= TAIL_THICK * space:
                continue      # a beam lies along the line
            columns = np.nonzero(bare[row, first:last])[0]
            if LINE_GAP_LOG is not None:
                LINE_GAP_LOG.append(((round(head['cx']), round(head['cy'])), stem['direction'], end, row))
            moved = abs(row - end)
            stem['end'], stem['x'] = row, first + int(round(columns.mean()))
            stem['length'] = stem.get('length', moved) - moved
            stem['past'] = stem.get('past', moved) - moved
            count += 1
    return count


def broken_stems(layers: dict, heads: list[dict]) -> int:
    """Leads each stem that breaks off before its beam on to the beam (see STEM_BROKEN): sets its 'end' and 'x'.
    Returns how many stems were led on."""
    if not STEM_BROKEN:
        return 0
    ink, space = layers['bare'], layers['space']
    height, width = ink.shape
    paper, slim_least, wide_most, clear = STEM_BROKEN
    band = max(2, int(round(0.13 * space)))
    trials: dict[int, tuple] = {}
    for head in heads:
        for stem in head['stems']:
            if stem.get('words'):
                continue
            step = -1 if stem['direction'] == 'up' else 1
            x, end = int(round(stem['x'])), int(stem['end'])
            first, last = max(0, x - band), min(width, x + band + 1)
            row, gap = end + step, 0
            while 0 <= row < height and gap <= paper * space and not ink[row, first:last].any():
                row += step
                gap += 1
            if gap < 1 or gap > paper * space or not 0 <= row < height:
                continue
            if tail_marks(layers, head, stem):
                continue      # a stem that shows a flag or a beam where it ends is not broken
            # The gap is a strip that the copy left white: no ink in its rows over the whole staff.
            staff = layers['staves'][head['staff']]
            rows = slice(min(end + 2 * step, row - 2 * step), max(end + 2 * step, row - 2 * step) + 1)
            if gap < 4 or layers['ink'][rows, max(0, int(staff['x0'])):int(staff['x1']) + 1].any():
                continue
            start = first + int(np.nonzero(ink[row, first:last])[0].mean())
            far, far_x, path = follow(ink, start, row, step, space, bridge=layers.get('bridge', 1.0))
            path = [(row, start)] + path
            slim = sum(1 for at, column in path if _run(ink, at, column) <= SLIM_STEM * space)
            if slim < slim_least * space or len(path) - slim > wide_most * space:
                continue
            low, high = min(end, far), max(end, far)
            if any(other is not head and other['staff'] == head['staff'] and low <= other['cy'] <= high
                   and other['x0'] - clear * space <= x <= other['x1'] + clear * space for other in heads):
                continue
            trial = dict(stem, end=far, x=far_x)
            pieces = [piece for piece in tail_marks(layers, head, trial) if _is_beam(piece)]
            if pieces:
                trials[id(stem)] = (head, stem, trial, pieces)
    count = 0
    for head, stem, trial, pieces in trials.values():
        for piece in pieces:
            side = [(other, own) for other in heads if other['staff'] == head['staff'] for own in other['stems']
                    if own['direction'] == stem['direction']
                    and 0.5 * space < (own['x'] - trial['x'] if piece['right'] else trial['x'] - own['x']) <= BEAM_NEXT * space]
            if not side:
                continue
            other, own = min(side, key=lambda pair: abs(pair[1]['x'] - trial['x']))
            there = trials[id(own)][2] if id(own) in trials else own
            if abs(there['end'] - trial['end']) <= 2.5 * space \
                    and any(_is_beam(back) and back['right'] != piece['right'] for back in tail_marks(layers, other, there)):
                stem['broken'] = stem['end']
                stem['length'] = stem.get('length', 0) + abs(trial['end'] - stem['end'])
                stem['past'] = stem.get('past', 0) + abs(trial['end'] - stem['end'])
                stem['end'], stem['x'] = trial['end'], trial['x']
                count += 1
                break
    return count


def _ends_at(layers: dict, x: float, row: float, right: bool) -> tuple[float, float | None] | None:
    """Follows the ink that leaves a stem at (x, row) to one side as _bow does, as far as it goes: (how far it goes,
    how far its last column lies from the nearest column where the ink is high, a stem that it ends at; None when
    no such column is near), in px. None when the ink cannot be followed at all."""
    ink, space = layers['bare'], layers['space']
    reach, step = max(2, int(round(0.3 * space))), 1 if right else -1
    y, gap, last, highs = float(row), 0, None, []
    column = int(round(x)) + step * int(round(0.3 * space))
    while 0 <= column < ink.shape[1] and abs(column - x) <= 3 * BEAM_NEXT * space:
        top = max(0, int(round(y)) - reach)
        rows = np.nonzero(ink[top:int(round(y)) + reach + 1, column])[0]
        if len(rows) and rows[-1] - rows[0] + 1 == len(rows) and len(rows) <= 2 * reach - 1:
            y = top + (rows[0] + rows[-1]) / 2
            last, gap = column, 0
        elif len(rows) == 0:
            gap += 1
            if gap > 0.3 * space:
                break
        else:
            highs.append(column)
        column += step
    if last is None:
        return None
    near = [abs(high - last) for high in highs if abs(high - last) <= 1.0 * space]
    return float(abs(last - x)), (float(min(near)) if near else None)


def _beam_past(layers: dict, group: list[dict], space: float, usual) -> None:
    """A run of stems that witnessed beams join, whose ink hangs on past both outer stems at its level and ends free at
    both sides, is joined by a slur and not by a beam (BEAM_PAST): its pieces are no beam. The stems of a chord stand
    as one stem at one column."""
    columns: list[list[dict]] = []
    for stem in sorted(group, key=lambda one: one['x']):
        if columns and abs(stem['x'] - columns[-1][0]['x']) <= 0.5 * space and abs(stem['end'] - columns[-1][0]['end']) <= 0.5 * space:
            columns[-1].append(stem)
        else:
            columns.append([stem])

    def pieces(column: list[dict], right: bool, witnessed: bool) -> list[dict]:
        return [piece for stem in column for piece in stem['marks']
                if piece['right'] == right and piece['beam'] and bool(piece['witness']) == witnessed]

    def nearest(index: int, right: bool):
        stem = columns[index][0]
        side = [other for other in range(len(columns))
                if 0.5 * space < (columns[other][0]['x'] - stem['x'] if right else stem['x'] - columns[other][0]['x']) <= BEAM_NEXT * space]
        return min(side, key=lambda other: abs(columns[other][0]['x'] - stem['x'])) if side else None

    after = {}
    for index in range(len(columns)):
        if pieces(columns[index], True, True):
            other = nearest(index, True)
            if other is not None and pieces(columns[other], False, True):
                after[index] = other
    for index in range(len(columns)):
        if index not in after or index in after.values():
            continue
        run = [index]
        while run[-1] in after and len(run) < len(columns):
            run.append(after[run[-1]])
        first, last = columns[run[0]], columns[run[-1]]
        level_first = min(piece['row'] for piece in pieces(first, True, True))
        level_last = min(piece['row'] for piece in pieces(last, False, True))
        before = [piece for piece in pieces(first, False, False) if abs(piece['row'] - level_first) <= 0.35 * space]
        past = [piece for piece in pieces(last, True, False) if abs(piece['row'] - level_last) <= 0.35 * space]
        ends = [_ends_at(layers, first[0]['x'], before[0]['row'], False) if before else None,
                _ends_at(layers, last[0]['x'], past[0]['row'], True) if past else None]
        if CENSUS is not None and (before or past):
            CENSUS.append({'rule': 'PAST', 'run': [(columns[i][0]['x'], columns[i][0]['end']) for i in run],
                           'before': [(piece['thick'], piece['far'], piece['row']) for piece in before],
                           'past': [(piece['thick'], piece['far'], piece['row']) for piece in past],
                           'levels': (level_first, level_last), 'usual': usual, 'space': space,
                           'inner': [piece['thick'] for i in run for piece in pieces(columns[i], True, True) + pieces(columns[i], False, True)],
                           'ends': ends})
        if before and past and all(end is not None and (end[1] is None or end[1] > BEAM_PAST * space) for end in ends):
            for i in run:
                for piece in pieces(columns[i], True, True) + pieces(columns[i], False, True):
                    piece['beam'] = piece['witness'] = False
                    piece['past'] = True
            for piece in before + past:
                piece['beam'] = piece['witness'] = False
                piece['past'] = True


def count_tails(layers: dict, heads: list[dict]) -> None:
    """Sets head['tails'] for every head: for each of its stems ('up', 'down'), the number of flags or beams at the
    far end: 0 for a quarter or half note, 1 for an eighth, 2 for a sixteenth.

    The ink near the stem's end is looked at without the stem: each piece that hangs on the stem is a witness.

    A beam is thick and long, and it joins two stems: the next stem at that side shows the same beam from its other
    side. A slur or a tie that passes the end of a stem is thick and long too. So a beam without that second witness
    counts only when it hangs at one side of the stem and is as thick as the beams of the page that do have their
    second witness. (The page teaches the thickness of its own beams.)

    A flag is short: it hangs at the right side of the stem and comes back toward the head. A printed flag is thick.
    A thin flag is a hook that begins at the very end of the stem; a slur begins there too, but it goes on away
    from the head, and a slur, a tie or a letter of the words that crosses the stem hangs on both sides."""
    space = layers['space']
    groups: dict[tuple[int, str], list[dict]] = {}
    staffs: dict[int, list[dict]] = {}
    for head in heads:
        staffs.setdefault(head['staff'], []).append(head)
    for head in heads:
        for stem in head['stems']:
            last = None
            if LAST_HEAD == 'all' or (LAST_HEAD == 'words' and stem.get('words')):
                last = _last_head(staffs[head['staff']], head, stem, space)
            stem['marks'] = tail_marks(layers, head, stem, last)
            if WORD_BEAMS and stem.get('words'):
                stem['in_words'] = [piece for piece in tail_marks(layers, head, stem, last, False) if _is_beam(piece)]
            groups.setdefault((head['staff'], stem['direction']), []).append(stem)

    def witness(group: list[dict], stem: dict, right: bool, slim: bool = False) -> bool:
        """True when the next stem at that side shows a beam at the side that faces this stem."""
        side = [other for other in group
                if 0.5 * space < (other['x'] - stem['x'] if right else stem['x'] - other['x']) <= BEAM_NEXT * space]
        if not side:
            return False
        near = min(side, key=lambda other: abs(other['x'] - stem['x']))
        return abs(near['end'] - stem['end']) <= 2.5 * space \
            and any((_is_beam(piece) or (slim and _is_slim(piece))) and piece['right'] != right
                    for piece in near['marks'] + near.get('in_words', []))

    def straight(group: list[dict], stem: dict, piece: dict) -> bool:
        """False when the ink that leaves the end of the stem bends away from the head: a slur that begins at the
        end of a stem is thick and long as a beam is, and it can end at the end of the next stem too, but it is a
        bow. (A beam that a hand drew crooked bends less, or toward the heads.)"""
        bow = _bow(layers, stem['x'], piece['row'], piece['right'])
        if bow is None or bow[0] < BEAM_STRAIGHT[0] * space:
            return True
        # A slur bends away from the notes that it joins: up over stems that go up, down under stems that go down.
        return (-bow[1] if stem['direction'] == 'up' else bow[1]) < BEAM_STRAIGHT[1] * space

    sure = []
    for group in groups.values():
        for stem in group:
            for piece in stem.get('in_words', []):
                if witness(group, stem, piece['right']):
                    stem['marks'] = [other for other in stem['marks'] if other['right'] != piece['right']
                                     or abs(other['row'] - piece['row']) > 0.5 * space] + [piece]
            for piece in stem['marks']:
                piece['beam'] = _is_beam(piece)
                piece['witness'] = bool(piece['beam'] and witness(group, stem, piece['right']))
                if piece['witness']:
                    sure.append(piece['thick'])
    usual = float(np.median(sure)) if len(sure) >= 4 else None
    layers['beam'] = usual
    if BEAM_PAIR:
        # The page teaches its beams: beside thick beams, slim ink between two stems is a slur.
        for group in groups.values():
            for stem in group:
                for piece in stem['marks']:
                    # (A beam at the edge of TAIL_THICK without its witness: the next stem can show it slim, see BEAM_EDGE.)
                    slim = _is_slim(piece) if not piece['beam'] else \
                        bool(BEAM_EDGE and not piece['witness'] and _is_slim(piece, BEAM_EDGE))
                    if slim and (usual is None or piece['thick'] >= BEAM_PAIR[3] * usual) \
                            and witness(group, stem, piece['right'], True) and (not BEAM_STRAIGHT or straight(group, stem, piece)):
                        piece['slim'] = True
        if SLIM_BOTH:
            # One slim beam joins two stems (see SLIM_BOTH).
            for group in groups.values():
                for stem in group:
                    for piece in stem['marks']:
                        if piece.get('slim') or piece['beam'] or not _is_slim(piece):
                            continue
                        side = [other for other in group
                                if 0.5 * space < (other['x'] - stem['x'] if piece['right'] else stem['x'] - other['x']) <= BEAM_NEXT * space]
                        if not side:
                            continue
                        near = min(side, key=lambda other: abs(other['x'] - stem['x']))
                        if abs(near['end'] - stem['end']) <= 2.5 * space \
                                and any(other.get('slim') and other['right'] != piece['right'] for other in near['marks']) \
                                and (not BEAM_STRAIGHT or straight(group, stem, piece)):
                            piece['slim_end'] = True
                            if CENSUS is not None:
                                CENSUS.append({'x': stem['x'], 'end': stem['end'], 'thick': piece['thick'], 'usual': usual,
                                               'right': piece['right'], 'far': piece['far']})
            for group in groups.values():
                for stem in group:
                    for piece in stem['marks']:
                        if piece.pop('slim_end', False):
                            piece['slim'] = True
        for group in groups.values():
            for stem in group:
                for piece in stem['marks']:
                    if piece.get('slim'):
                        piece['beam'] = piece['witness'] = True
    if BEAM_CROSS and usual is not None:
        for group in groups.values():
            for stem in group:
                beams = [piece for piece in stem['marks'] if piece['beam']]
                if len({piece['right'] for piece in beams}) == 2 \
                        and max(piece['thick'] for piece in beams) <= BEAM_CROSS * usual \
                        and max(piece['row'] for piece in beams) - min(piece['row'] for piece in beams) <= 0.35 * space:
                    for piece in beams:
                        piece['beam'] = piece['witness'] = False
                        piece['cross'] = True
    if BEAM_PAST:
        for group in groups.values():
            _beam_past(layers, group, space, usual)
    for head in heads:
        head['tails'] = {}
        for stem in head['stems']:
            pieces = stem['marks']
            beams = [piece for piece in pieces if piece['beam']]
            alone = len({piece['right'] for piece in beams}) == 1
            rows = [piece['row'] for piece in beams if not piece.get('slim')
                    and (piece['witness'] or (alone and usual is not None and piece['thick'] >= BEAM_USUAL * usual
                                              and (not BEAM_STRAIGHT or straight(groups[(head['staff'], stem['direction'])], stem, piece))))]
            if not rows:
                # A slim beam is one beam: a staff line that crosses it leaves two slivers of it.
                rows = [piece['row'] for piece in beams if piece.get('slim')][:1]
            stem['beam_only'] = bool(rows)
            short = [piece for piece in pieces if not piece['beam'] and piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6]
            # A printed flag; and beside a beam, the short second beam of a sixteenth.
            flags = [piece['row'] for piece in short if (piece['right'] and piece['back'] >= FLAG_BACK) or rows]
            stem['beam_only'] = stem['beam_only'] and not flags
            rows += flags
            if FLAG_HOLE and not rows:
                rows += [piece['row'] for piece in pieces
                         if piece['right'] and not piece['beam'] and piece['thick'] >= TAIL_THICK and 0.6 <= piece['far'] < FLAG_HOLE[0]
                         and piece['high'] >= FLAG_HOLE[1] and FLAG_HOLE[2] <= piece['lean'] <= FLAG_HOLE[3]
                         and piece['from_end'] <= FLAG_END]
            if FLAG_NARROW and not rows:
                rows += [piece['row'] for piece in pieces
                         if piece['right'] and not piece['beam'] and piece['thick'] >= TAIL_THICK and piece['far'] < 0.6
                         and piece['high'] >= FLAG_NARROW[0] and piece['lean'] >= FLAG_NARROW[1]
                         and piece['from_end'] <= FLAG_END]
            levels = []
            for row in sorted(rows):
                if not levels or row - levels[-1] > 0.35 * space:
                    levels.append(row)
            if BEAM_SIDES and len(levels) > 1:
                # A beam that goes on past the stem is one piece of ink at each side of it. Where the beam slants or
                # the copy made it fat, the two pieces lie a little apart; but two beams lie a beam's thickness
                # and a gap apart.
                sides = {piece['row']: piece for piece in beams}
                kept = [levels[0]]
                for row in levels[1:]:
                    one, two = sides.get(kept[-1]), sides.get(row)
                    if one is not None and two is not None and one['right'] != two['right'] \
                            and row - kept[-1] < BEAM_SIDES * max(one['thick'], two['thick']) * space:
                        continue
                    kept.append(row)
                levels = kept
            if BEAM_SECOND and usual is not None and len(levels) > 1:
                # A bow that lies on a beam is no second beam (see BEAM_SECOND).
                # (A level is as thick as its thickest piece, at either side of the stem.)
                full = [row for row in levels
                        if max(piece['thick'] for piece in pieces if abs(piece['row'] - row) <= 0.35 * space) >= BEAM_SECOND * usual]
                if full:
                    levels = full
            if levels:
                head['tails'][stem['direction']] = min(len(levels), 3)
                if BOW_THIN and FLAG_BOW and stem['direction'] == 'down' and not beams and not head.get('thin'):
                    last = _last_head([other for other in staffs[head['staff']] if not other['hollow'] and not other.get('thin')],
                                      head, stem, space)
                    stem['bow'] = _bow_flag(layers, head, stem, head['y1'] + last - head['cy'])
                continue
            thin = [piece for piece in pieces if not (piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6)]
            thin_left = [piece['row'] for piece in thin if not piece['right']]
            hooks = [piece['row'] for piece in thin if piece['right'] and piece['from_end'] <= TAIL_START and piece['back'] >= 0.12]
            hook = any(all(abs(row - other) > 0.25 * space for other in thin_left) for row in hooks)
            head['tails'][stem['direction']] = 1 if hook else 0
            if FLAG_BOW and not hook and stem['direction'] == 'down' and not any(piece['beam'] for piece in pieces):
                # (The room of the bow can be read as a hollow head on the stem: the bow is looked for past the
                # last filled head, and without_flag_loops then drops the hollow one.)
                last = _last_head([other for other in staffs[head['staff']] if not other['hollow']], head, stem, space)
                if _bow_flag(layers, head, stem, head['y1'] + last - head['cy']):
                    head['tails']['down'] = 1
                    stem['bow'] = True
            if STEEP_FLAG and not head['tails'][stem['direction']] and not any(piece['beam'] for piece in pieces):
                # A thin flag that leaves the stem steeply (see STEEP_FLAG).
                last = _last_head([other for other in staffs[head['staff']] if not other['hollow']], head, stem, space)
                steep = _steep_flag(layers, head, stem, last)
                if steep is not None:
                    head['tails'][stem['direction']] = 1
                    stem['steep'] = True
                    if STEEP_SEEN is not None:
                        STEEP_SEEN.append(dict(steep, staff=head['staff'], x=float(head['cx']), y=float(head['cy']),
                                               direction=stem['direction'], sx=int(stem['x']), end=int(stem['end'])))
        if ROOM_HEADS and head.get('room') and not head.get('room_sign'):
            # The room at such a head is closed by a flag or by a beam: the stem that goes along the room has one.
            x0, y0, x1, y1 = head['loop']
            for stem in head['stems']:
                along = y0 < head['y0'] - 0.5 * space if stem['direction'] == 'up' else y1 > head['y1'] + 0.5 * space
                if along and not head['tails'].get(stem['direction']):
                    head['tails'][stem['direction']] = 1
    if BEAM_TWO:
        # Two beams with a staff line in the gap between them (see BEAM_TWO).
        low, high, slim_low, slim_high, times, fill, lean, same = BEAM_TWO

        def block(piece: dict) -> bool:
            return piece['area'] >= fill * piece['thick'] * piece['far'] and abs(piece['lean']) <= lean

        def side(stem: dict, right: bool) -> dict | None:
            pieces = [piece for piece in stem.get('marks', []) if piece['beam'] and piece['right'] == right]
            return max(pieces, key=lambda piece: piece['thick']) if pieces else None

        owners = [(head, stem) for head in heads for stem in head['stems'] if head['tails'].get(stem['direction']) == 1]
        double: dict[int, bool] = {}     # the stems with two beams, and the side of their thick piece
        for head, stem in owners:
            for right in (True, False):
                big, slim = side(stem, right), side(stem, not right)
                if big is not None and slim is not None and block(big) and slim['area'] >= fill * slim['thick'] * slim['far'] \
                        and low <= big['thick'] <= high \
                        and slim_low <= slim['thick'] <= slim_high and big['thick'] >= times * slim['thick']:
                    double[id(stem)] = right
                    break
        changed = bool(double)
        while changed:
            changed = False
            for head, stem in owners:
                if id(stem) in double:
                    continue
                for right in (True, False):
                    mine = side(stem, right)
                    if mine is None or not block(mine) or not low <= mine['thick'] <= high:
                        continue
                    others = [other for other in groups[(head['staff'], stem['direction'])]
                              if 0.33 * space < (other['x'] - stem['x']) * (1 if right else -1) <= 10 * space
                              and side(other, not right) is not None]
                    if not others:
                        continue
                    near = min(others, key=lambda other: abs(other['x'] - stem['x']))
                    far = side(near, not right)
                    if double.get(id(near)) is not None and block(far) and abs(mine['thick'] - far['thick']) <= same * far['thick'] \
                            and (double[id(near)] == (not right) or low <= far['thick'] <= high):
                        double[id(stem)] = right
                        changed = True
                        break
        for head, stem in owners:
            if id(stem) in double:
                head['tails'][stem['direction']] = 2
    if THIN_BEAM:
        # A hand draws a beam as one thin line. A slur is thin too, but it bends over the notes: only a beam runs
        # straight from the end of one stem to the end of the next.
        for (staff, direction), group in groups.items():
            if THIN_BEAM_CHORD:
                # The heads of a chord hang on one stem, and each head has that stem a pixel or two from the other's:
                # stems closer than a third of a staff space to the first of their group are one stem.
                ordered = []
                for head, stem in sorted(((head, stem) for head in heads for stem in head['stems']
                                          if head['staff'] == staff and stem['direction'] == direction), key=lambda pair: pair[1]['x']):
                    if ordered and stem['x'] - ordered[-1][0][1]['x'] <= 0.3 * space:
                        ordered[-1].append((head, stem))
                    else:
                        ordered.append([(head, stem)])
            else:
                places = {}
                for head in heads:
                    for stem in head['stems']:
                        if head['staff'] == staff and stem['direction'] == direction:
                            places.setdefault(int(round(stem['x'] / (0.3 * space))), []).append((head, stem))
                ordered = [places[key] for key in sorted(places)]
            if THIN_BEAM_OVER:
                # A stem that ends well before the line from the stem at its left to the stem at its right does not
                # reach their beam: the beam passes over it.
                kept = list(ordered)
                for number in range(len(ordered) - 2, 0, -1):
                    one, mid, two = ordered[number - 1][0][1], ordered[number][0][1], ordered[number + 1][0][1]
                    if not (0.8 * space <= two['x'] - one['x'] <= BEAM_NEXT * space and abs(two['end'] - one['end']) <= 2.5 * space):
                        continue
                    at = one['end'] + (two['end'] - one['end']) * (mid['x'] - one['x']) / (two['x'] - one['x'])
                    short = (mid['end'] - at) if direction == 'up' else (at - mid['end'])
                    if short >= THIN_BEAM_OVER * space and _thin_beam(layers, one, two):
                        del kept[number]
                ordered = kept
            joined = []
            for left, right in zip(ordered, ordered[1:]):
                one, two = left[0][1], right[0][1]
                joined.append(0.8 * space <= two['x'] - one['x'] <= BEAM_NEXT * space
                              and abs(two['end'] - one['end']) <= 2.5 * space and _thin_beam(layers, one, two))
            if STEM_SLUR:
                # A slur from the end of one stem to the end of the next: the stems were followed into its two ends,
                # so they bend toward each other and turn there, and the stroke is thin. It is no beam of any kind,
                # whether a straight line joins the two ends or each stem shows the stroke at the side of the other.
                for number, (left, right) in enumerate(zip(ordered, ordered[1:])):
                    one, two = left[0][1], right[0][1]
                    if not (0.8 * space <= two['x'] - one['x'] <= BEAM_NEXT * space and abs(two['end'] - one['end']) <= 2.5 * space):
                        continue
                    bends = ((one['x'] - one.get('mid', one['x'])) / space, (two.get('mid', two['x']) - two['x']) / space)
                    turns = (one.get('turn', 0.0), -two.get('turn', 0.0))
                    if min(bends) < STEM_SLUR[0] or sum(turns) < STEM_SLUR[2]:
                        continue
                    round_ = _round_ends(layers, one, two)
                    if round_ is None or min(round_) < STEM_SLUR[3] or sum(round_) < STEM_SLUR[4]:
                        continue
                    faces = [[piece for head, stem in entry for piece in stem['marks'] if piece['beam']] for entry in (left, right)]
                    if not (joined[number] or (faces[0] and faces[1])) \
                            or any(not piece['right'] for piece in faces[0]) or any(piece['right'] for piece in faces[1]) \
                            or any(piece['thick'] > STEM_SLUR[1] for side in faces for piece in side) \
                            or any(head['tails'].get(direction, 0) > 1 for entry in (left, right) for head, stem in entry):
                        continue
                    joined[number] = False
                    for entry in (left, right):
                        for head, stem in entry:
                            if stem.get('beam_only', True):
                                head['tails'][direction] = 0
                            stem['stem_slur'] = True
                            stem['thin_bends'], stem['thin_turns'] = bends, turns
            # A run of stems that are joined one to the next is one beam, when the line ends at its first and its
            # last stem. A slur goes on past the stems.
            first = 0
            while first < len(joined):
                if not joined[first]:
                    first += 1
                    continue
                last = first
                while last + 1 < len(joined) and joined[last + 1]:
                    last += 1
                run = ordered[first:last + 2]
                # How far the first and the last stem bend toward each other at their ends (staff spaces).
                bends = ((run[0][0][1]['x'] - run[0][0][1].get('mid', run[0][0][1]['x'])) / space,
                         (run[-1][0][1].get('mid', run[-1][0][1]['x']) - run[-1][0][1]['x']) / space)
                turns = (run[0][0][1].get('turn', 0.0), -run[-1][0][1].get('turn', 0.0))
                # (On a print with thick beams a thin line between the ends of two stems is a slur: see THIN_PRINT.)
                printed = False
                if THIN_PRINT and BEAM_STRAIGHT and usual is not None and usual >= THIN_PRINT \
                        and not any(piece['beam'] for entry in run for head, stem in entry for piece in stem['marks']):
                    one, two = run[0][0][1], run[-1][0][1]
                    bows = (_bow(layers, one['x'], one.get('thin_right', one['end']), True),
                            _bow(layers, two['x'], two.get('thin_left', two['end']), False))
                    printed = all(bow is not None and bow[0] >= BEAM_STRAIGHT[0] * space
                                  and (-bow[1] if direction == 'up' else bow[1]) >= BEAM_STRAIGHT[1] * space for bow in bows)
                if not printed and (not THIN_BEAM_PAST or not (_goes_on(layers, run[1][0][1], run[0][0][1])
                                                               or _goes_on(layers, run[-2][0][1], run[-1][0][1]))):
                    for index, entry in enumerate(run):
                        for head, stem in entry:
                            stem['thin_on'] = index < len(run) - 1     # the thin beam goes on to the next stem
                            stem['thin_before'] = head['tails'].get(direction, 0)
                            head['tails'][direction] = max(1, head['tails'].get(direction, 0))
                            stem['thin_beam'] = True
                            stem['thin_bends'] = bends
                            stem['thin_turns'] = turns
                            stem['thin_run'] = len(run)
                first = last + 1
    for head in heads:
        if RING_FLAG:
            # The ink of a printed flag, for a head that is hollow (see RING_FLAG).
            # It is asked of each stem alone: a head of two voices is a ring with a flag for the voice whose stem has it.
            head['flag_ink'] = [
                stem['direction'] for stem in head['stems']
                if head['tails'].get(stem['direction']) and len(stem.get('marks', [])) == 1
                and all(piece['right'] and not piece['beam'] and RING_FLAG[0] <= piece['far'] <= RING_FLAG[1]
                        and RING_FLAG[2] <= piece['thick'] <= RING_FLAG[3] and piece['lean'] >= RING_FLAG[4]
                        for piece in stem['marks'])]
        if SHARED_TAILS and len(head['tails']) == 2:
            # One head with two stems is one note that two voices sing: a hand draws its flag at one stem only.
            beamed = {stem['direction'] for stem in head['stems'] if SHARED_TAILS == 'flags'
                      and (stem.get('beam_only') or stem.get('thin_beam')) and head['tails'].get(stem['direction'])
                      and (any(piece['beam'] and piece['right'] for piece in stem['marks']) or stem.get('thin_on'))}
            if beamed and not all(_ends_free(layers, stem) for stem in head['stems'] if stem['direction'] not in beamed):
                beamed = set()
            most = max([count for direction, count in head['tails'].items() if direction not in beamed] or [0])
            head['tails'] = {direction: count if direction in beamed else most for direction, count in head['tails'].items()}



def _ends_free(layers: dict, stem: dict) -> bool:
    """Whether a stem ends in paper (SHARED_FREE): no beam, flag or line beside its end."""
    ink, space = layers['ink'], layers['space']
    side, before, past, share = SHARED_FREE
    x, end = int(round(stem['x'])), int(round(stem['end']))
    if stem['direction'] == 'down':
        top, bottom = end - int(before * space), end + int(past * space)
    else:
        top, bottom = end - int(past * space), end + int(before * space)
    top, bottom = max(0, top), min(ink.shape[0], bottom + 1)
    for first, last in ((x - int(side * space), x - 3), (x + 4, x + int(side * space))):
        part = ink[top:bottom, max(0, first):max(0, last)]
        if part.size and part.mean() > share:
            return False
    return True

def _round_ends(layers: dict, one: dict, two: dict) -> tuple[float, float] | None:
    """How round the stroke is that joins the far ends of two stems of one direction (`one` at the left): for each
    stem, how far the outer edge of the stroke lies toward the heads there, from the straight line through the
    middle half of the stroke (staff spaces). A beam meets its stems in square corners: about 0. None when no
    stroke is found on four fifths of the way."""
    ink, space = layers['bare'], layers['space']
    down = one['direction'] == 'down'
    band = max(2, int(round(0.13 * space)))
    first = int(max(one['x'], one.get('mid', one['x']))) + band + 1
    last = int(min(two['x'], two.get('mid', two['x']))) - band - 1
    if last - first < 1.0 * space:
        return None
    reach = int(round(0.9 * space))
    edge = []
    for column in range(first, last + 1):
        y = one['end'] + (two['end'] - one['end']) * (column - one['x']) / max(1, two['x'] - one['x'])
        top, bottom = max(0, int(y) - reach), min(ink.shape[0], int(y) + reach + 1)
        rows = np.nonzero(ink[top:bottom, column])[0] + top
        if len(rows) == 0:
            continue
        # The run of ink nearest to the line between the two ends, and its edge away from the heads.
        cuts = np.nonzero(np.diff(rows) > 1)[0]
        runs = [(rows[a], rows[b]) for a, b in zip(np.r_[0, cuts + 1], np.r_[cuts, len(rows) - 1])]
        low, high = min(runs, key=lambda run: 0 if run[0] <= y <= run[1] else min(abs(run[0] - y), abs(run[1] - y)))
        edge.append((column - first, high if down else low))
    count = last - first + 1
    middle = [(at, row) for at, row in edge if 0.25 * count <= at <= 0.75 * count]
    if len(edge) < 0.8 * count or len(middle) < 4:
        return None
    slope, start = np.polyfit([at for at, row in middle], [row for at, row in middle], 1)
    near = max(3, int(round(0.25 * space)))

    def toward(part: list) -> float:
        if not part:
            return 0.0
        away = float(np.median([slope * at + start - row for at, row in part]))
        return (away if down else -away) / space
    return toward([entry for entry in edge if entry[0] < near]), toward([entry for entry in edge if entry[0] >= count - near])


def _beam_rows(inner: dict, outer: dict) -> tuple[float, float]:
    """The rows where the thin beam between two stems meets `outer` and `inner` (see _thin_beam): the ends of the
    stems, or the ink at a stem's side that the beam was found from."""
    if outer['x'] > inner['x']:
        return outer.get('thin_left', outer['end']), inner.get('thin_right', inner['end'])
    return outer.get('thin_right', outer['end']), inner.get('thin_left', inner['end'])


def _goes_on(layers: dict, inner: dict, outer: dict) -> bool:
    """True when the ink that runs from the end of the stem `inner` to the end of the stem `outer` goes on past
    `outer`, along the same line or bending away from it a little."""
    space = layers['space']
    ink = layers['bare']
    height, width = ink.shape
    side = 1 if outer['x'] > inner['x'] else -1
    last, before = _beam_rows(inner, outer)
    slope = (last - before) / (outer['x'] - inner['x'])
    reach = int(round(THIN_BEAM_PAST[2] * space))
    seen = count = 0
    runs = []
    for step in range(int(round(THIN_BEAM_PAST[0] * space)), int(round(THIN_BEAM_PAST[1] * space)) + 1):
        x = int(round(outer['x'])) + side * step
        y = int(round(last + slope * side * step))
        top, bottom = max(0, y - reach), min(height, y + reach + 1)
        if WORD_TAILS and outer.get('words'):
            # The stem ends at the words: a letter beside its end is no ink of a slur.
            if outer['direction'] == 'down':
                bottom = min(bottom, int(outer['words'][0]))
            else:
                top = max(top, int(outer['words'][1]) + 1)
        if PAST_WORDS:
            # The rows of the words: the top of a letter under the end of a beam is no slur.
            for band in layers.get('words') or []:
                if band['x0'] <= x <= band['x1'] and band['top'] <= bottom and band['bottom'] >= top:
                    if band['top'] > y:
                        bottom = min(bottom, int(band['top']))
                    elif band['bottom'] < y:
                        top = max(top, int(band['bottom']) + 1)
        if not 0 <= x < width or bottom <= top:
            continue
        count += 1
        rows = np.nonzero(ink[top:bottom, x])[0]
        if len(rows):
            seen += 1
            # The run of ink nearest to the line, followed past the rows that were looked at.
            first = low = top + int(rows[np.argmin(np.abs(rows + top - y))])
            while first > 0 and ink[first - 1, x]:
                first -= 1
            while low + 1 < height and ink[low + 1, x]:
                low += 1
            runs.append(low - first + 1)
        else:
            runs.append(0)
    if count == 0 or seen < 0.6 * count:
        return False
    near, far = runs[:max(1, int(PAST_SLIM[1] * count))] if PAST_SLIM else [], runs[-max(1, int(PAST_SLIM[3] * count)):] if PAST_SLIM else []
    if PAST_SLIM and all(0 < run <= PAST_SLIM[0] * space for run in near) \
            and sum(1 for run in far if run >= PAST_SLIM[2] * space) >= PAST_SLIM[4] * len(far):
        # A stroke that ends in a blob (a letter of the dynamics, a sign): the end of the beam, and what stands beside
        # it. The stems tell a slur: they were followed into it, and bend and turn toward each other (STEM_SLUR).
        one, two = (inner, outer) if inner['x'] < outer['x'] else (outer, inner)
        bends = ((one['x'] - one.get('mid', one['x'])) / space, (two.get('mid', two['x']) - two['x']) / space)
        if not (STEM_SLUR and min(bends) >= STEM_SLUR[0] and one.get('turn', 0.0) - two.get('turn', 0.0) >= STEM_SLUR[2]):
            return False
    return not (PAST_TWO and _two_strokes(layers, inner, outer))


def _two_strokes(layers: dict, inner: dict, outer: dict) -> bool:
    """True when two strokes, one over the other, run to the end of the stem `outer` from the side of `inner`: a
    beam and a slur beside it. The ink that goes on past the stem is then the slur's, and the beam ends at the stem."""
    space = layers['space']
    ink = layers['bare']
    height, width = ink.shape
    side = 1 if outer['x'] > inner['x'] else -1
    last, before = _beam_rows(inner, outer)
    slope = (last - before) / (outer['x'] - inner['x'])
    reach = int(round(PAST_TWO[2] * space))
    two = count = 0
    for step in range(int(round(PAST_TWO[0] * space)), int(round(PAST_TWO[1] * space)) + 1):
        x = int(round(outer['x'])) - side * step
        y = int(round(last - slope * side * step))
        top, bottom = max(0, y - reach), min(height, y + reach + 1)
        if not 0 <= x < width or bottom <= top:
            continue
        column = ink[top:bottom, x].astype(np.int8)
        runs = int(column[0] > 0) + int((np.diff(column) > 0).sum())
        count += 1
        two += runs >= 2
    return count > 0 and two >= 0.6 * count


def _thin_beam(layers: dict, one: dict, two: dict) -> bool:
    """True when ink runs straight from the far end of one stem to the far end of the next stem."""
    space = layers['space']
    # A weak copy breaks a stem just before its beam: the stem that was found ends too early. The beam may meet
    # the stem a little past that end.
    def ends(stem: dict, right: bool) -> list[tuple[float, bool]]:
        away = -1 if stem['direction'] == 'up' else 1
        found = [stem['end'] + away * step for step in range(0, int(round(THIN_BEAM_END * space)) + 1, 2)]
        if THIN_FULL and stem.get('words') and 'own' in stem and (stem['own'] - stem['end']) * away > 0:
            # The stem was cut where the words begin, and its own ink goes on: the beam meets it at its own end.
            found += [stem['own'] + away * step for step in range(0, int(round(THIN_BEAM_END * space)) + 1, 2)]
        if THIN_BEAM_SIDE:
            # The stem was followed past its end into a slur that begins there: the beam leaves it before the end
            # that was found, as long ink at the side of the other stem. That ink is tried first.
            side = [piece['row'] for piece in stem.get('marks', [])
                    if piece['right'] == right and THIN_BEAM_SIDE[0] <= piece['from_end'] <= THIN_BEAM_SIDE[1]
                    and piece['far'] >= THIN_BEAM_SIDE[2]
                    and piece['thick'] >= THIN_BEAM_SIDE[3] * (layers.get('beam') or 0)]
            return [(row, True) for row in side] + [(row, False) for row in found]
        return [(row, False) for row in found]
    one.pop('thin_right', None)
    two.pop('thin_left', None)
    for first, first_side in ends(one, True):
        for last, last_side in ends(two, False):
            if (first_side or last_side) and abs(last - first) > THIN_BEAM_SIDE[4] * (two['x'] - one['x']):
                continue
            if _beam_line(layers, one['x'], first, two['x'], last):
                # (Where the beam leaves a stem before its end, for the look past the last stem of the run.)
                if first_side:
                    one['thin_right'] = first
                if last_side:
                    two['thin_left'] = last
                return True
    return False


def _bow(layers: dict, x: float, row: float, right: bool) -> tuple[float, float] | None:
    """Follows the ink that leaves a stem at (x, row) to one side, as far as it goes (at most BEAM_NEXT staff spaces):
    (its length, how far its middle line leaves the straight line between its two ends: under it when positive),
    in px. None when the ink cannot be followed. A column where the ink is high (a stem, a head) is passed over."""
    ink, space = layers['bare'], layers['space']
    reach, step = max(2, int(round(0.3 * space))), 1 if right else -1
    points, y, gap = [], float(row), 0
    column = int(round(x)) + step * int(round(0.3 * space))
    while 0 <= column < ink.shape[1] and abs(column - x) <= BEAM_NEXT * space:
        top = max(0, int(round(y)) - reach)
        rows = np.nonzero(ink[top:int(round(y)) + reach + 1, column])[0]
        if len(rows) and rows[-1] - rows[0] + 1 == len(rows) and len(rows) <= 2 * reach - 1:
            y = top + (rows[0] + rows[-1]) / 2
            points.append((column, y))
            gap = 0
        elif len(rows) == 0:
            gap += 1
            if gap > 0.3 * space:
                break
        column += step
    if len(points) < 3:
        return None
    (x0, y0), (x1, y1) = points[0], points[-1]
    if x1 == x0:
        return None
    away = [py - (y0 + (y1 - y0) * (px - x0) / (x1 - x0)) for px, py in points]
    most = max(range(len(away)), key=lambda index: abs(away[index]))
    sag = away[most]
    # A bow has one bend, near its middle: a line that a hand drew crooked goes to both sides, or bends at one end.
    other = max((-value if sag > 0 else value) for value in away)
    if other > 0.1 * space or not 0.2 <= abs(points[most][0] - x0) / abs(x1 - x0) <= 0.8:
        sag = 0.0
    return float(abs(x1 - x0)), float(sag)


def _bend(ink: np.ndarray, one_x: float, one_end: float, two_x: float, two_end: float, x1: int, x2: int,
          reach: int) -> float:
    """How far the ink along the straight line from (one_x, one_end) to (two_x, two_end), between the columns x1 and
    x2, bends from a straight line: the middle of its rows in each column, fitted with a parabola, rises or falls in
    its middle by this many pixels against its ends. A beam is straight; a slur arches."""
    height = ink.shape[0]
    xs, rows = [], []
    for x in range(x1, x2 + 1):
        y = int(round(one_end + (two_end - one_end) * (x - one_x) / (two_x - one_x)))
        top = max(0, y - reach)
        found = np.nonzero(ink[top:min(height, y + reach + 1), x])[0]
        if len(found):
            xs.append(x)
            rows.append(top + found.mean())
    if len(xs) < 5:
        return 0.0
    xs = np.array(xs, float)
    curve = np.polyfit(xs, np.array(rows), 2)[0]
    return float(abs(curve) * (xs.max() - xs.min()) ** 2 / 4)


def _beam_line(layers: dict, one_x: float, one_end: float, two_x: float, two_end: float) -> bool:
    """True when ink runs along the straight line from (one_x, one_end) to (two_x, two_end)."""
    space = layers['space']
    ink, lines, full = layers['bare'], layers['lines'], layers['ink']
    height, width = ink.shape
    reach = max(2, int(round(THIN_BEAM[0] * space)))
    edge = int(round(0.2 * space))
    x1, x2 = int(round(one_x)) + edge, int(round(two_x)) - edge
    if x2 - x1 < 0.4 * space:
        return False
    thick = max(staff['thick'] for staff in layers['staves'])
    if THIN_BEAM_STAFF:
        # The lines of this staff: a faint page has thinner lines at one staff than at another.
        index = _staff_of(layers, (one_x + two_x) / 2, (one_end + two_end) / 2)
        if index is not None:
            thick = layers['staves'][index]['thick']
    fat = (thick + max(1.5, THIN_BEAM_FAT * thick), thick + 0.45 * space) if THIN_BEAM_FAT else None
    seen = hidden = 0
    shown, under = [], []
    for x in range(x1, x2 + 1):
        y = int(round(one_end + (two_end - one_end) * (x - one_x) / (two_x - one_x)))
        top, bottom = max(0, y - reach), min(height, y + reach + 1)
        if not 0 <= x < width or bottom <= top:
            shown.append(False)
            under.append(False)
            continue
        shown.append(bool(ink[top:bottom, x].any()))
        rows = np.nonzero(lines[top:bottom, x])[0] if not shown[-1] else []
        under.append(len(rows) > 0)
        if under[-1] and fat:
            # A beam that lies in a staff line makes the line thicker there.
            first = last = top + int(rows[len(rows) // 2])
            while first > 0 and full[first - 1, x]:
                first -= 1
            while last + 1 < height and full[last + 1, x]:
                last += 1
            if fat[0] <= last - first + 1 <= fat[1]:
                shown[-1], under[-1] = True, False
        if shown[-1]:
            seen += 1
        elif under[-1]:
            hidden += 1
    count = x2 - x1 + 1
    # The line hangs on both stems: a short slur between two stems does not reach them.
    near = max(2, int(round(THIN_BEAM_ENDS * space)))
    ends = (2 * sum(shown[:near]) >= near, 2 * sum(shown[-near:]) >= near)
    if THIN_BEAM_ENDS:
        first, last = ends
        if THIN_BEAM_UNDER:
            # A beam that runs into a staff line at one stem is hidden there: it is seen at the other stem.
            first, last = first or (last and 2 * sum(under[:near]) >= near), last or (first and 2 * sum(under[-near:]) >= near)
        if THIN_BEAM_HIDDEN and not first and not last and 2 * sum(under[:near]) >= near and 2 * sum(under[-near:]) >= near:
            # Hidden at both ends (see THIN_BEAM_HIDDEN): the line takes each end, and the way between is ink.
            lead = next((index for index, value in enumerate(shown) if value), len(shown))
            tail = next((index for index, value in enumerate(reversed(shown)) if value), len(shown))
            middle = shown[lead:len(shown) - tail]
            if max(lead, tail) <= THIN_BEAM_HIDDEN[0] * space and middle \
                    and sum(middle) >= THIN_BEAM_HIDDEN[1] * len(middle) \
                    and _bend(ink, one_x, one_end, two_x, two_end, x1 + lead, x2 - tail, reach) <= THIN_BEAM_HIDDEN[2] * space:
                first = last = True
                if CENSUS is not None:
                    CENSUS.append({'one': (one_x, one_end), 'two': (two_x, two_end), 'lead': lead, 'tail': tail,
                                   'middle': len(middle), 'shown': sum(middle),
                                   'bend': _bend(ink, one_x, one_end, two_x, two_end, x1 + lead, x2 - tail, reach) / space})
        if not (first and last):
            return False
    if seen + hidden < THIN_BEAM[1] * count:
        return False
    if seen >= THIN_BEAM[2] * count:
        return True
    if not THIN_BEAM_HALF or seen < THIN_BEAM_HALF[0] * count or ends[0] == ends[1] \
            or not THIN_BEAM_HALF[1] * (two_x - one_x) <= abs(two_end - one_end) <= THIN_BEAM_HALF[4] * (two_x - one_x):
        return False
    # Hidden at one stem only, on more of the way (see THIN_BEAM_HALF): from the stem where the line is seen.
    order, low = (shown, under) if ends[0] else (shown[::-1], under[::-1])
    border = len(order) - next(index for index, value in enumerate(reversed(order)) if value)
    if sum(low[:border]) > THIN_BEAM_HALF[3] * count:
        return False
    away = []
    for x in range(max(0, x1), min(width, x2 + 1)):
        at = one_end + (two_end - one_end) * (x - one_x) / (two_x - one_x)
        top = max(0, int(round(at)) - reach)
        rows = np.nonzero(ink[top:min(height, int(round(at)) + reach + 1), x])[0]
        if len(rows):
            away.append(abs(top + rows.mean() - at))
    return bool(away) and max(away) <= THIN_BEAM_HALF[2] * space


HOLE_UPRIGHT = (1.6, -15.0, 60.0, 0.05, 0.5)   # the inside of a printed half note lies on its side and rises to the right. A
#   hollow mark on one stem whose inside is this many times as long as wide along its own axis, with that axis outside
#   these degrees (0: level, 90: upright), is no head: the loop of a flag, the room of a double bar line, the bowl of
#   the letter p, a C of the time, the box of a natural. Not where the inside is smaller than the fourth number of
#   staff spaces squared (a hole that a thick copy all but closed has no direction), and not where the ink at both
#   sides of it is the last number of staff spaces thick or more: a loop, a box and the room at a bar line have a thin
#   stroke at one side, and one print's half note in a space has an upright inside between two thick sides (None: off)


LOOP_UNDER = (1.3, 55.0, 0.4, 0.25, 0.3, 0.8)   # the loop of a flag right under the head of its note: a hollow mark on one
#   stem down whose inside is this many times as long as wide, with its axis this steep or steeper, where the ink of
#   its stem's column goes on over the mark for the third number of staff spaces or more (over gaps of the fourth) up
#   to a filled head that stands on that column (within the fifth of its box, its middle at most the last number
#   past the ink's end). The stem is that head's (None: off)


def _hole_axis(layers: dict, head: dict) -> tuple[float, float, int, int]:
    """The largest piece of closed paper in a head: how many times as long as wide it is along its own axis, the
    degrees of that axis, its px, and how thick the ink is at the thinner of its two sides, at its middle row."""
    y0, x0 = max(0, int(head['y0']) - 1), max(0, int(head['x0']) - 1)
    box = layers['holes'][y0:int(head['y1']) + 2, x0:int(head['x1']) + 2]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(box.astype(np.uint8), connectivity=4)
    if count < 2:
        return 0.0, 0.0, 0, 0
    ys, xs = np.nonzero(labels == 1 + int(np.argmax(stats[1:, 4])))
    if len(xs) < 6:
        return 0.0, 0.0, len(xs), 0
    values, vectors = np.linalg.eigh(np.cov(np.vstack((xs, -ys)).astype(float)))
    if values[0] <= 0:
        return 0.0, 0.0, len(xs), 0
    along = vectors[:, 1] if vectors[0, 1] >= 0 else -vectors[:, 1]
    ink, row = layers['ink'], int(round(ys.mean()))
    own = xs[ys == row]
    sides = [0, 0]
    if len(own):
        for side, (column, step) in enumerate(((x0 + int(own.min()) - 1, -1), (x0 + int(own.max()) + 1, 1))):
            while 0 <= column < ink.shape[1] and ink[y0 + row, column]:
                sides[side] += 1
                column += step
    return float(np.sqrt(values[1] / values[0])), float(np.degrees(np.arctan2(along[1], along[0]))), len(xs), min(sides)


THICK_BAR = (0.8, 0.9)  # a filled mark in the staff is a piece of a thick bar line, and no head, where its columns are
#   ink over the whole height of the staff: this share of the mark's width, in this share of the rows from the top
#   line to the bottom line. The thick stroke of a final bar line or of a repeat sign is wider than a stem, the staff
#   lines cut it into pieces as high as a staff space, and the thin line beside it was their stem. (A census of the
#   read notes of the clean copies: 13 notes that are not there at 0.8 of the rows, and no true note of 15,057: the
#   heads of a chord taper towards the lines between them.) None: off


def without_bar_pieces(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the filled marks that are pieces of a thick bar line (THICK_BAR)."""
    if not THICK_BAR:
        return heads
    ink, out = layers['ink'], []
    for head in heads:
        if not head['hollow'] and not head.get('thin'):
            rows = layers['staves'][head['staff']]['rows']
            top, bottom = int(rows[0]), int(rows[4])
            box = ink[top:bottom + 1, max(0, int(head['x0'])):int(head['x1']) + 1] > 0
            if box.size and top <= head['cy'] <= bottom and (box.mean(axis=1) >= THICK_BAR[0]).mean() >= THICK_BAR[1]:
                continue
        out.append(head)
    return out


END_MARK = (0.5, 0.25, 1.5)  # nothing of the music stands at or past the bar line that ends a staff: a mark whose middle
#   is at most this many staff spaces before the end of a staff that ends with a bar line (layers.END_BAR), whose right
#   edge is at most this many before it, and whose middle is at most this many past it, is no head. What is read there
#   is the thick stroke of a final bar line that a hole or the wear of the print broke (THICK_BAR asks for whole
#   columns), a punch hole, a paperclip, tape or the black edge of the scan, with the bar line as its stem. (A census
#   of every read note of the scan pages at the end of its staff: 65 at such a bar line, each looked at, and none is a
#   note; where the staff ends without a bar line, true notes stand there, on copies by hand and beside a punch hole
#   that hides the lines.) The rule runs after every finder of heads: taken away before them, the closed paper between
#   the two strokes of a final bar line took a true whole note of its staff with it. None: off


END_PAST = 0.55   # a mark whose middle is past the end of its staff is no head where a column at that end is ink in
#   this share of the staff's rows (the staff's 'end_ink', see layers.END_BAR): the black of a binder hole or of the
#   edge of the scan stands there, and the hole bit the end line. (Of the read notes past the end of their staff on
#   LitChoir's scan pages, the 7 with such a column from 0.6 on are no notes, and the 4 true ones, on a copy by hand
#   and beside a punch hole, have 0.43 at most.) 1.1: only at a whole bar line


def without_end_marks(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the marks at or past the bar line that ends their staff (END_MARK)."""
    if not END_MARK:
        return heads
    space, out = layers['space'], []
    for head in heads:
        staff = layers['staves'][head['staff']]
        if (staff.get('end_bar') or head['cx'] >= staff['x1'] and staff.get('end_ink', 0.0) >= END_PAST) \
                and head['cx'] >= staff['x1'] - END_MARK[0] * space \
                and head['x1'] >= staff['x1'] - END_MARK[1] * space and head['cx'] <= staff['x1'] + END_MARK[2] * space:
            continue
        out.append(head)
    return out


def without_upright_holes(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the hollow marks whose inside stands upright (HOLE_UPRIGHT)."""
    if not HOLE_UPRIGHT and not LOOP_UNDER:
        return heads
    out, space = [], layers['space']
    for head in heads:
        if head['hollow'] and len(head['stems']) == 1 and not head.get('thin'):
            long, rise, area, side = _hole_axis(layers, head)
            if HOLE_UPRIGHT and long >= HOLE_UPRIGHT[0] and not HOLE_UPRIGHT[1] <= rise <= HOLE_UPRIGHT[2] \
                    and area >= HOLE_UPRIGHT[3] * space * space and side < HOLE_UPRIGHT[4] * space:
                continue
            stem = head['stems'][0]
            if LOOP_UNDER and stem['direction'] == 'down' and long >= LOOP_UNDER[0] and rise >= LOOP_UNDER[1]:
                x = int(round(stem['x']))
                column = layers['ink'][:, max(0, x - 1):x + 2].any(axis=1)
                on, gap = 0, 0
                for row in range(int(head['y0']) - 1, max(0, int(head['y0']) - 1 - int(3 * space)), -1):
                    if column[row]:
                        on, gap = int(head['y0']) - row, 0
                    else:
                        gap += 1
                        if gap > LOOP_UNDER[3] * space:
                            break
                far = head['y0'] - on
                if on >= LOOP_UNDER[2] * space and any(
                        other is not head and other['staff'] == head['staff'] and not other['hollow']
                        and other['x0'] - LOOP_UNDER[4] * space <= x <= other['x1'] + LOOP_UNDER[4] * space
                        and far - LOOP_UNDER[5] * space <= other['cy'] < head['y0'] for other in heads):
                    continue
        out.append(head)
    return out


FLAT_CELL = (0.6, 0.95, 2.0, 0.85)   # a hollow mark is no head where its closed paper is this many staff spaces
#   high or more and has a top or a bottom that is level in this share of its columns (within a pixel of its first or
#   last row) at a staff line (the line's middle within the third number of px, or half its thickness): a cell between
#   the line and a slanted stroke (a pencil ring, a slur that crosses the staff, the loop of a flag, a rest, a piece
#   of a clef). The inside of a printed head is round and stands clear of the lines: of the 95 such marks that were
#   read as notes on LitChoir's scan pages, each looked at, none is a printed hollow head. Not where the mark holds
#   ink as fat as a head (the widest disc in its ink, against the last number times the usual one of the page's
#   filled heads): a filled head with a sharp or a natural close before it closes such a cell too, and so does the
#   stroke that a hand draws for a head; that mark stays as it was read. (None: off)


CLIP_CELL = 0.3          # a hollow mark is no head where the wire of a paperclip (layers.CLIP) closes its inside: of the
#   ink around its closed paper, this share or more is the wire. The bow of a clip that hangs into a staff closes a
#   cell with a staff line, and the cell was read as a half note; the inside of a head is closed by the head's own
#   ink. (At the reader's own step the rule acts at one mark of LitChoir's scan pages, where the wire is 0.69 of the
#   rim: a rule for one case.) None: off


def without_clip_cells(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the hollow marks whose inside the wire of a paperclip closes (CLIP_CELL)."""
    clip = layers.get('clip')
    if not CLIP_CELL or clip is None or not clip.any():
        return heads
    out = []
    for head in heads:
        if head['hollow']:
            y0, x0 = max(0, int(head['y0']) - 2), max(0, int(head['x0']) - 2)
            y1, x1 = int(head['y1']) + 3, int(head['x1']) + 3
            count, labels, stats, _ = cv2.connectedComponentsWithStats(layers['holes'][y0:y1, x0:x1].astype(np.uint8), connectivity=4)
            if count >= 2:
                inside = (labels == 1 + int(np.argmax(stats[1:, 4]))).astype(np.uint8)
                rim = cv2.dilate(inside, np.ones((5, 5), np.uint8)) & (1 - inside) & layers['ink'][y0:y1, x0:x1]
                if rim.any() and float((rim & clip[y0:y1, x0:x1]).sum()) >= CLIP_CELL * float(rim.sum()):
                    continue
        out.append(head)
    return out


GREY_MARK = (0.1, 3.0, 30, 0.5, 0.2, 0.5)   # a mark that holds no black ink where the print around it is black is no
#   head: a word or a ring in pencil, a marker, the shadow of a slip, a smear (layers.BLACK says what black is). Of the
#   ink in the mark's box under the first share is black. The print around it is the ink within the second number of
#   staff spaces of the box (the third number of px or more): the fourth share of it or more is black. A stretch that
#   the print left pale holds pale heads on pale lines, and a note in pencil on a grey copy stands among grey lines:
#   the print around tells. And the mark does not lie in black ink: of the ink within the fifth number of staff spaces
#   of its box under the last share is black (the pale middle of a worn head is a small mark of its own inside the
#   head's black ink). (At the reader's own step on every scan page of LitChoir: of 267 heads whose ink is under 0.3
#   black, 14 pass, each looked at: words and a ring in pencil, a grey streak, a marker, shadows and smears, no note.
#   A rule for the pages whose print is black: on a copy by hand the notes in pencil stand among grey lines.) None: off


def _black_around(layers: dict, head: dict) -> tuple[float, float, int, float]:
    """How black the ink of a mark is, and the ink around it (GREY_MARK): the share of the ink in the head's box that
    is black, the share of the print around the box that is, the px of that print, and the share of the ink close
    around the box that is black."""
    ink, black = layers['ink'], layers['black']
    y0, x0 = max(0, int(head['y0'])), max(0, int(head['x0']))
    y1, x1 = int(head['y1']) + 1, int(head['x1']) + 1
    count, mine = int(ink[y0:y1, x0:x1].sum()), int(black[y0:y1, x0:x1].sum())
    if not count:
        return 1.0, 0.0, 0, 1.0
    space = layers['staves'][head['staff']]['space']
    shares = []
    for far in (int(round(GREY_MARK[1] * space)), max(1, int(round(GREY_MARK[4] * space)))):
        top, left = max(0, y0 - far), max(0, x0 - far)
        stand = int(ink[top:y1 + far, left:x1 + far].sum()) - count
        shares.append((float(int(black[top:y1 + far, left:x1 + far].sum()) - mine) / stand if stand > 0 else 0.0, max(0, stand)))
    return mine / count, shares[0][0], shares[0][1], shares[1][0]


GREY_STEM = (0.2, 0.1)   # a head that was read from a stem (`thin`) is no head where the stem is grey: of the stem's
#   ink (its column and one px at each side, from the head to its end) at most the first share is black, of the head's
#   own ink off the rows of the staff lines at most the second share, and the print around is black as GREY_MARK asks
#   (its third and fourth numbers). The end of a grey streak across a staff was read so, with the streak as its stem;
#   GREY_MARK's test of the ink close around the mark does not hold there, because the head lies on a black staff line.
#   (A census at the step of the dots on every scan page of LitChoir: of 3,147 heads read from a stem, 27 have stems
#   that hold at most 0.2 black, 8 of them stand in black print, and one of those holds no black of its own off the
#   lines: the end of the streak on pascha-exapostilarion's page. The others are heads in pencil or on grey copies,
#   with black ink of their own. A rule for one case.) None: off


def _grey_stem(layers: dict, head: dict, around: float, stand: int) -> bool:
    """Whether a head read from a stem is the end of a grey stroke (GREY_STEM)."""
    if not GREY_STEM or not head.get('thin') or not head.get('stems') or stand < GREY_MARK[2] or around < GREY_MARK[3]:
        return False
    ink, black = layers['ink'], layers['black']
    y0, y1, x0, x1 = max(0, int(head['y0'])), int(head['y1']) + 1, max(0, int(head['x0'])), int(head['x1']) + 1
    rows = ~layers['lines'][y0:y1, max(0, x0 - 3):x1 + 3].any(axis=1)
    part = ink[y0:y1, x0:x1] & rows[:, None]
    count = int(part.sum())
    if not count or int((black[y0:y1, x0:x1] & part).sum()) > GREY_STEM[1] * count:
        return False
    for stem in head['stems']:
        x = int(round(stem['x']))
        lo, hi = (int(head['y1']) + 1, int(stem['end']) + 1) if stem['direction'] == 'down' else (int(stem['end']), int(head['y0']))
        cut = ink[max(0, lo):hi, max(0, x - 1):x + 2]
        if not cut.any() or int((black[max(0, lo):hi, max(0, x - 1):x + 2] & cut).sum()) > GREY_STEM[0] * int(cut.sum()):
            return False
    return True


def without_grey_marks(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the marks that hold no black ink where the print around them is black (GREY_MARK), and
    without the heads read from a grey stem (GREY_STEM)."""
    if not GREY_MARK or not heads or not layers['black'].any():
        return heads
    out = []
    for head in heads:
        own, around, stand, close = _black_around(layers, head)
        if own < GREY_MARK[0] and stand >= GREY_MARK[2] and around >= GREY_MARK[3] and close < GREY_MARK[5]:
            continue
        if _grey_stem(layers, head, around, stand):
            continue
        out.append(head)
    return out


FLAT_WEDGE = (0.85, 0.35, 0.1, 0.7)   # a lower cell along a staff line (under FLAT_CELL's height, level at the line as
#   there) is no inside of a head either where it is a wedge: as high as it gets at one end (the mean of the first or
#   last eighth of its columns, the first number times its highest column or more), a point at the other end (the
#   second number at most), its highest column within the third number of its width of an end, and the paper that
#   mirrors it across the line open in the last share or more. Such a cell lies between the line, an upright stroke
#   and a slanted one: a beam or a slur at a stem or a bar line, the loop of a flag, a pencil ring at a stem. The half
#   of an inside that a staff line cuts off a head on the line has the other half of the head across the line, ink or
#   closed paper. (A census at this step on every scan page of LitChoir: of 3,250 low cells that are level at a line,
#   93 are such wedges in a mark that is no fatter than FLAT_CELL allows; the paper across the line is open in 0.47
#   at most at the 58 true heads among them, which a hand drew as a loop from the stem on a line, and in 0.54 or more
#   at the others. The 24 from 0.7 on were each looked at: cells at beams, slurs, flags, a pencil ring, a sharp and
#   strokes by hand, no head.) None: off
WEDGE_ROUND = (0.6, 0.15, 0.3)   # (FLAT_WEDGE) a wedge whose high end a stroke rounds off where it meets a stem: the end
#   is the first share of its highest column on the mean, and the highest columns end within the second share of its
#   width of that end. The heavy beam of one print meets the stem of the next note so, and the cell that it closes with
#   the stem and the top line was read as a whole note (nativity-troparion--s3). A hand draws a head as such a loop at
#   its own stem: the cell must lie at the far end of the stem of another head, within the last number of staff spaces
#   of its box. (A census at this step on every page of LitChoir: of the 61 cells that the milder shape alone takes,
#   with open paper across the line, 7 are heads by hand that a hand drew as a loop at the stem, and the first form lost
#   8 notes by them; at the end of another note's stem the rule acts at 6 cells of 5 pages, each a mark that is no note:
#   the cell that a beam, a slur or a flag closes with the stem and a line.) None: off


def _flat_wedge(layers: dict, head: dict, left: int, top: int, width: int, height: int, line: float, space: float,
                cut: bool = False, stem_ends: tuple = ()) -> bool:
    """Whether the closed paper of a hollow mark that lies in this box, level at the staff line in this row, is a wedge
    with open paper across the line (FLAT_WEDGE). `cut`: only the rows of the box count (FLAT_RAGGED). `stem_ends`: the
    column and the far end of the stems of the other heads (WEDGE_ROUND)."""
    reach = int(round(1.2 * space))
    y0, x0 = max(0, int(head['y0']) - reach), max(0, int(head['x0']) - reach)
    window = (slice(y0, int(head['y1']) + reach + 1), slice(x0, int(head['x1']) + reach + 1))
    holes = layers['holes'][window] > 0
    _, labels = cv2.connectedComponents(holes.astype(np.uint8), connectivity=4)
    inside = labels[top - y0:top - y0 + height, left - x0:left - x0 + width]
    found = [int(number) for number in np.unique(inside) if number]
    if not found:
        return False
    part = labels == max(found, key=lambda number: int((inside == number).sum()))
    if cut:
        part[:max(0, top - y0)] = False
        part[top - y0 + height:] = False
    ys, xs = np.nonzero(part)
    high = part[ys.min():ys.max() + 1, xs.min():xs.max() + 1].sum(axis=0).astype(float)
    ends = max(1, int(round(0.12 * len(high))))
    first, last = float(high[:ends].mean()) / high.max(), float(high[-ends:].mean()) / high.max()
    most = float(np.argmax(high)) / max(1, len(high) - 1)
    if cut:
        # a cell cut at the edge of the line is as high as it gets along a stretch: the end of that stretch counts
        tops = np.nonzero(high == high.max())[0] / max(1, len(high) - 1)
        most = float(tops[0]) if tops[0] <= 1 - tops[-1] else float(tops[-1])
    if not (max(first, last) >= FLAT_WEDGE[0] and min(first, last) <= FLAT_WEDGE[1]
            and (most <= FLAT_WEDGE[2] or most >= 1 - FLAT_WEDGE[2])):
        # A wedge whose high end a stroke rounds off, at the far end of another note's stem (WEDGE_ROUND).
        tops = np.nonzero(high == high.max())[0] / max(1, len(high) - 1)
        if not (WEDGE_ROUND and max(first, last) >= WEDGE_ROUND[0] and min(first, last) <= FLAT_WEDGE[1]
                and min(tops[0], 1 - tops[-1]) <= WEDGE_ROUND[1]):
            return False
        reach = WEDGE_ROUND[2] * space
        if not any(head['x0'] - reach <= x <= head['x1'] + reach and head['y0'] - reach <= end <= head['y1'] + reach
                   for x, end in stem_ends):
            return False
    across = np.zeros(part.shape, bool)
    for y, x in zip(ys, xs):
        row = int(round(2 * (line - y0) - y))
        if 0 <= row < part.shape[0]:
            across[row, x] = True
    if not across.any():
        return False
    paper = across & ~(layers['ink'][window] > 0) & ~(layers['lines'][window] > 0) & ~holes
    return float(paper.sum()) / float(across.sum()) >= FLAT_WEDGE[3]


FLAT_RAGGED = (0.12, 0.5)   # a cell along a staff line whose edge at the line is ragged: the edge of the line is uneven, and
#   the paper of the cell reaches into the rows of the line in some columns, so that the cell is level there in too few of
#   them for FLAT_CELL. Where the line's edge (its middle row less half the thickest staff line) lies inside the cell, at
#   most the first number of staff spaces from the cell's last row, the cell is measured again without the rows from the
#   line's edge on, and the cell keeps at least the second share of its rows. A cell under a beam at its stem, and a
#   cell between a stroke and the wire of a paperclip, were read so as notes. It took 44 marks on LitChoir's pages, each
#   looked at: 43 cells of beams, slurs, clefs, bar lines and a clip, and one worn quarter note of a pale copy whose head
#   is a slanted stroke at its stem (dormition-koinonikon). None on the fresh set (None: off)
FLAT_RAGGED_SEEN = None   # a census: the cells that pass FLAT_CELL's level test only so (None: none)


def _flat_ragged(part: np.ndarray, top: int, rows: np.ndarray, half: float, space: float):
    """The closed paper `part` (its box begins at the row `top`) without the rows that lie in the ragged edge of a staff
    line at its top or its bottom (FLAT_RAGGED), with the shift of its box (rows, columns); None where no line's edge
    lies so."""
    height = part.shape[0]
    keep = np.ones(height, bool)
    for row in rows:
        under = int(np.ceil(row - half)) - top          # the first row of the line's ink, in the cell's rows
        over = int(np.floor(row + half)) - top          # its last row
        if 0 < under < height and height - under <= FLAT_RAGGED[0] * space + 1:
            keep[under:] = False
        if 0 <= over < height - 1 and over + 1 <= FLAT_RAGGED[0] * space + 1:
            keep[:over + 1] = False
    if keep.all() or keep.sum() < FLAT_RAGGED[1] * height:
        return None
    first = int(np.argmax(keep))
    kept = part[keep]
    columns = np.nonzero(kept.any(axis=0))[0]
    if not len(columns):
        return None
    return kept[:, columns[0]:columns[-1] + 1], (first, int(columns[0]))


def without_flat_cells(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the hollow marks whose inside is a cell along a staff line (FLAT_CELL, FLAT_WEDGE). It runs
    after the flags are counted: the loop of a flag is such a cell, and older rules read the flag from it. The layer
    of the insides stays as it is for the same reason."""
    if not FLAT_CELL:
        return heads
    space = layers['space']
    rows = np.array(sorted(row for staff in layers['staves'] for row in staff['rows']), float)
    thick = max(staff['thick'] for staff in layers['staves'])
    half, slack = thick / 2, max(FLAT_CELL[2], thick / 2)
    fats = [head['alt']['fat'] for head in heads if not head['hollow'] and head.get('alt')]
    usual = float(np.median(fats)) * space if fats else 0.0
    out = []
    for head in heads:
        if head['hollow'] and usual:
            y0, x0 = max(0, int(head['y0']) - 1), max(0, int(head['x0']) - 1)
            box = layers['holes'][y0:int(head['y1']) + 2, x0:int(head['x1']) + 2]
            count, labels, stats, _ = cv2.connectedComponentsWithStats(box.astype(np.uint8), connectivity=4)
            if count >= 2:
                index = 1 + int(np.argmax(stats[1:, 4]))
                x, y, width, height, _ = stats[index]
                if height >= FLAT_CELL[0] * space or FLAT_WEDGE:
                    part = labels[y:y + height, x:x + width] == index
                    first, last = part.argmax(axis=0), height - 1 - part[::-1].argmax(axis=0)
                    top, bottom = y0 + y, y0 + y + height
                    above = float((first <= 1).mean()) if np.abs(rows - (top - 0.5 - half)).min() <= slack else 0.0
                    below = float((last >= height - 2).mean()) if np.abs(rows - (bottom - 0.5 + half)).min() <= slack else 0.0
                    ragged = False
                    if FLAT_RAGGED and max(above, below) < FLAT_CELL[1]:
                        # (see FLAT_RAGGED: the cell without the paper in the ragged edge of a staff line)
                        cut = _flat_ragged(part, top, rows, half, space)
                        if cut is not None:
                            part, shift = cut
                            ragged = True
                            height, width = part.shape
                            y, x = y + shift[0], x + shift[1]
                            first, last = part.argmax(axis=0), height - 1 - part[::-1].argmax(axis=0)
                            top, bottom = y0 + y, y0 + y + height
                            above = float((first <= 1).mean()) if np.abs(rows - (top - 0.5 - half)).min() <= slack else 0.0
                            below = float((last >= height - 2).mean()) if np.abs(rows - (bottom - 0.5 + half)).min() <= slack else 0.0
                            if FLAT_RAGGED_SEEN is not None and max(above, below) >= FLAT_CELL[1]:
                                FLAT_RAGGED_SEEN.append({'head': (head['cx'], head['cy']), 'cell': (int(x0 + x), int(top), int(width), int(height)),
                                                         'above': above, 'below': below})
                    if max(above, below) >= FLAT_CELL[1]:
                        if height < FLAT_CELL[0] * space:
                            # A low cell: only a wedge with open paper across its line (FLAT_WEDGE).
                            edge = top - 0.5 - half if above >= FLAT_CELL[1] and above >= below else bottom - 0.5 + half
                            line = float(rows[np.abs(rows - edge).argmin()])
                            stem_ends = [(stem['x'], stem['end']) for other in heads if other is not head
                                         for stem in other['stems'] if isinstance(stem, dict) and 'end' in stem]
                            if not _flat_wedge(layers, head, x0 + x, top, width, height, line, space, ragged, stem_ends):
                                out.append(head)
                                continue
                        own = np.ascontiguousarray(layers['ink'][y0:int(head['y1']) + 2, x0:int(head['x1']) + 2])
                        fat = 2 * cv2.distanceTransform(np.pad(own.astype(np.uint8), 1), cv2.DIST_L2, 3).max()
                        if fat < FLAT_CELL[3] * usual:
                            continue
        out.append(head)
    return out


def loops_have_flags(layers: dict, heads: list[dict]) -> int:
    """A mark that was read as a filled head beside the loop of its flag (SOLID_LOOP) has a flag. Where count_tails()
    found none, the closed paper is the hole of a hollow head, and the ink beside it is a head of the other voice
    that touches it: the head is hollow again, at the place of its hole. Returns how many."""
    count = 0
    if not SOLID_FLAG:
        return count
    for head in heads:
        if head.get('or_hollow') is None or any(head.get('tails', {}).values()):
            continue
        staff = layers['staves'][head['staff']]
        head['hollow'], head['cy'] = True, head['or_hollow']
        head['place'] = pitch_place(staff, head['cy'])
        if abs(head['place']) > 4.6:
            head['ledgers'] = ledger_lines(layers, staff, head)
            found = ledger_place(layers, staff, head)
            if found is not None:
                head['place'] = found
        count += 1
    return count


def without_flag_loops(heads: list[dict], space: float) -> list[dict]:
    """The heads without the loops of flags. A flag, its stem and a staff line can close a small white room, and that
    room looks like a hollow head at the far end of the stem. But a note with a flag is never hollow, and a head
    never stands that near to the far end of a stem that it shares with another head."""
    gone = set()
    for head in heads:
        if not head['hollow']:
            continue
        for stem in head['stems']:
            near = abs(head['cy'] - stem['end'])
            if near > LOOP_NEAR * space:
                continue
            for other in heads:
                if other is head or other['staff'] != head['staff']:
                    continue
                for far in other['stems']:
                    if far['direction'] == stem['direction'] and abs(far['x'] - stem['x']) <= 0.35 * space \
                            and abs(far['end'] - stem['end']) <= 0.5 * space \
                            and abs(other['cy'] - far['end']) >= near + 0.8 * space \
                            and max(other['tails'].get(far['direction'], 0), head['tails'].get(stem['direction'], 0)) >= 1:
                        gone.add(id(head))
    if BOW_THIN:
        # The bow of a flag at a down stem (FLAG_BOW) is thin ink around paper, as a thin hollow head is: a thin head
        # at the right of the down stem of a note with a flag, between that note's head and the end of its stem, and
        # nearer to the end: the bow hangs at the far half of the stem. (Nearer to the head it is the lower head of
        # two that touch a third apart, which the thick marks show as one.)
        for head in heads:
            if not head.get('thin'):
                continue
            for other in heads:
                if other is head or other['staff'] != head['staff'] or other['tails'].get('down', 0) < 1:
                    continue
                if any(stem['direction'] == 'down' and stem.get('bow') and 0 < head['cx'] - stem['x'] <= BOW_THIN * space
                       and other['cy'] < head['cy'] <= stem['end'] + 0.3 * space
                       and head['cy'] - other['cy'] > stem['end'] - head['cy'] for stem in other['stems']):
                    gone.add(id(head))
    return [head for head in heads if id(head) not in gone]


FLAG_TRAIL = (0.9, 1.2, 1.5, 0.25)   # a hollow mark at the right of a down stem is the loop of a long flag that bends back
#   along the stem to the head: closed paper hugs the stem's right side (its left edge within the last number of staff
#   spaces of the stem), from the mark's inside down, in pieces that the staff lines cut, for this many staff spaces
#   or more in all, in a strip this many staff spaces wide, to at most the third number before the end of the stem.
#   The inside of the mark itself is one such piece: it lies level and passes the older rules for an upright inside.
#   The trail begins in the rows of the mark: the paper between a staff line and the top of the lower of two stacked
#   half notes is a piece too, and taken as the start it took true half notes in its first form (2 on LitChoir's
#   pages, 8 on the fresh set). The inside of a half note on a down stem is half a staff space high, and the paper
#   under it is open (None: off)


def without_flag_trails(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the hollow marks that are the top of the paper that a long flag closes along its stem
    (FLAG_TRAIL). It runs after the flags are counted."""
    if not FLAG_TRAIL:
        return heads
    space, ink, out = layers['space'], layers['ink'], []
    thick = max(staff['thick'] for staff in layers['staves'])
    for head in heads:
        if head['hollow'] and _flag_trail(ink, head, space, thick):
            continue
        out.append(head)
    return out


def _flag_trail(ink: np.ndarray, head: dict, space: float, thick: float) -> bool:
    """True where closed paper runs on from a hollow mark along the right side of its down stem to near the stem's
    end (see FLAG_TRAIL)."""
    stem = next((stem for stem in head['stems'] if stem['direction'] == 'down' and stem['x'] < head['cx']), None)
    if stem is None or stem['end'] <= head['y1'] + FLAG_TRAIL[0] * space:
        return False
    x = int(round(stem['x']))
    top, bottom = max(0, int(head['y0'] - 0.3 * space)), min(ink.shape[0], int(stem['end'] + 0.3 * space) + 1)
    right = min(ink.shape[1], x + int(round(FLAG_TRAIL[1] * space)) + 1)
    box = np.ascontiguousarray(ink[top:bottom, x:right] == 0).astype(np.uint8)
    if box.size == 0:
        return False
    count, _, stats, _ = cv2.connectedComponentsWithStats(box, connectivity=4)
    pieces = sorted((int(stats[i, 1]), int(stats[i, 1] + stats[i, 3])) for i in range(1, count)
                    if 1 <= stats[i, 0] <= FLAG_TRAIL[3] * space and stats[i, 0] + stats[i, 2] < box.shape[1]
                    and stats[i, 1] > 0 and stats[i, 1] + stats[i, 3] < box.shape[0])
    own = [(first, last) for first, last in pieces if int(head['y0']) - top - 1 <= first < int(head['y1']) - top]
    if not own:
        return False
    start, reach = min(first for first, _ in own), max(last for _, last in own)
    for first, last in pieces:
        if first <= reach + thick + 3 and last > reach:
            reach = last
    return reach - start >= FLAG_TRAIL[0] * space and stem['end'] - (top + reach) <= FLAG_TRAIL[2] * space


FLAG_CURL = (0.6, 0.6, 1.6)   # the curl at the end of a flag is a small filled mark: under this share of the area of the
#                               page's filled heads, in the row of a flag that was counted at another stem (at most this
#                               many staff spaces from it) and at the flag's side of that stem (at most this many staff
#                               spaces away). It is no head. Of 83 such notes of LitChoir's pages, each looked at, none
#                               is a note (curls and tips of flags, the ends of beams, pieces of rests and of numbers);
#                               from 0.6 on true heads stand there (None: off)


def without_flag_curls(heads: list[dict], space: float) -> list[dict]:
    """The heads without the curls of flags (see FLAG_CURL). Runs after count_tails(), which marks the flags of a stem."""
    if not FLAG_CURL:
        return heads
    areas = [head['alt']['area'] for head in heads if not head['hollow'] and head.get('alt')]
    if not areas:
        return heads
    usual = float(np.median(areas))
    gone = set()
    for head in heads:
        if head['hollow'] or not head.get('alt') or head['alt']['area'] >= FLAG_CURL[0] * usual:
            continue
        for other in heads:
            if other is head or other['staff'] != head['staff']:
                continue
            for stem in other['stems']:
                for mark in stem.get('marks') or ():
                    apart = head['cx'] - stem['x']
                    if not mark.get('beam') and abs(head['cy'] - mark['row']) <= FLAG_CURL[1] * space \
                            and (0 <= apart <= FLAG_CURL[2] * space if mark['right'] else -FLAG_CURL[2] * space <= apart <= 0):
                        gone.add(id(head))
    return [head for head in heads if id(head) not in gone]


FLAG_STROKE = (0.5, 0.5)   # one engraving draws the flag of a stem that goes down as a wedge at the stem with a thin stroke
#   that comes back up to the head, and the stroke was read as a stem with the wedge as its head. A head that was read
#   from its stem (thin_heads) is that flag where the stem ends in the box of another head that is a head by its own ink
#   (not one read from a stem), that head's own stem comes the other way and goes on past the mark by the second number
#   of staff spaces or more, the mark stands between the two strokes, and a flag was counted at that stem on its side,
#   at most the first number of staff spaces from the mark's row. (From the stored notes of LitChoir's scan pages: of 31
#   heads read from a stem beside a flagged stem, 11 have their own stem end at the other head; the true notes among
#   them stand at the end of the other stem, where the rule does not look. Two heads of one scan of one clean score
#   pass. The first form also took a scribble by hand, two heads read from stems that end in each other: the flag
#   hangs on the stem of a true head. A rule for one print of LitChoir; the engravings of the fresh set draw their
#   flags so too.) None: off


def without_flag_strokes(heads: list[dict], space: float) -> list[dict]:
    """The heads without the strokes of flags that come back to their head (see FLAG_STROKE). Runs after count_tails(),
    which marks the flags of a stem."""
    if not FLAG_STROKE:
        return heads
    gone = set()
    for head in heads:
        if not head.get('thin') or len(head['stems']) != 1:
            continue
        own = head['stems'][0]
        for other in heads:
            if other is head or other['staff'] != head['staff'] or other.get('thin') \
                    or not (other['x0'] - 2 <= own['x'] <= other['x1'] + 2 and other['y0'] - 3 <= own['end'] <= other['y1'] + 3):
                continue
            for stem in other['stems']:
                past = stem['end'] - head['cy'] if stem['direction'] == 'down' else head['cy'] - stem['end']
                if stem['direction'] == own['direction'] or past < FLAG_STROKE[1] * space \
                        or not (min(stem['x'], own['x']) - 2 <= head['cx'] <= max(stem['x'], own['x']) + 2):
                    continue
                if any(not mark.get('beam') and bool(mark['right']) == (own['x'] > stem['x'])
                       and abs(head['cy'] - mark['row']) <= FLAG_STROKE[0] * space for mark in stem.get('marks') or ()):
                    gone.add(id(head))
    return [head for head in heads if id(head) not in gone]


STEM_END_MARK = (1.4, 0.85, 1.5)   # a filled mark that holds the end of another note's stem is that stem's beam or a
#   slur that passes its end, no head, where it is at least the first number times as wide as the page's heads and at
#   most the second number times as high (the other head at least the third number of staff spaces away). A printed
#   head is round: of the filled marks of LitChoir's pages that hold the end of another note's stem, the true heads
#   are 1.3 times as high as the page's heads or more, and the beams and slurs 0.85 or less. (None: off)


def without_stem_end_marks(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the flat filled marks at the end of another head's stem (STEM_END_MARK): a thick beam that
    slants across a staff line, or a slur over the end of a stem, cut out as one piece with the line."""
    if not STEM_END_MARK or not layers.get('head'):
        return heads
    space = layers['space']
    wide, high = layers['head'][0], layers['head'][1]
    gone = set()
    for head in heads:
        if head['hollow'] or head['x1'] - head['x0'] + 1 < STEM_END_MARK[0] * wide \
                or head['y1'] - head['y0'] + 1 > STEM_END_MARK[1] * high:
            continue
        for other in heads:
            if other is head or other['staff'] != head['staff'] or abs(other['cy'] - head['cy']) < STEM_END_MARK[2] * space:
                continue
            if any(head['x0'] - 2 <= stem['x'] <= head['x1'] + 2 and head['y0'] - 3 <= stem['end'] <= head['y1'] + 3
                   for stem in other['stems']):
                gone.add(id(head))
                break
    return [head for head in heads if id(head) not in gone]


FAR_MARK = (0.75, 1.5)   # a low filled mark whose own stem ends in the box of a filled head of its staff (at least the
#   second number of staff spaces away), where that head has no stem that goes toward the mark, is the flag, the beam,
#   the corner of a box beam or the end of a slur at the far end of that head's stem, and no head: at most the first
#   number times as high as the page's heads. The stem is the head's: the reader gave it to the mark, which then counted
#   the head as its own flag. (A census at this step on every scan page of LitChoir: 209 filled marks whose stem ends in
#   another filled head, each with the scorer's verdicts at both. Of the 53 whose head has no stem toward the mark, the
#   notes read at marks up to 0.72 of a head high are all marks that are no notes, each looked at: the beginning of a
#   beam on a staff line over a chord, the top of a flag, the corner of a box beam by hand and a slur at the end of the
#   stem; the first true note stands at 0.77.) None: off

FAR_FLAG = (1.0, 1.5, 1.0)   # and a filled mark is no head where its one stem goes down at most the first number of
#   staff spaces past it and the column of that stem, followed up, is ink into the box of a filled head of its staff (the
#   two middles at least the second number of staff spaces apart, the gap between the boxes at most the third) that has
#   no stem down: the end of that head's own stem down with what hangs on it. One print draws the flag of such a stem as
#   a stroke from the stem's end back up to the head, closing a small triangle of paper; a head that two voices share
#   has a flag at its stem down; an engraving lets a slur leave the stem. The head's own way down stops at the mark, so
#   the mark took the end of the stem as its own. Every mark that it took was looked at: 2 on LitChoir's pages (the
#   two flags) and 17 on the fresh set (slurs and one flag), none a note. None: off
FAR_FLAG_LOG = None


def without_far_marks(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the low marks at the far end of another head's stem that took that stem as their own
    (FAR_MARK)."""
    if not FAR_MARK or not layers.get('head'):
        return heads
    space = layers['space']
    gone = set()
    for head in heads:
        if head['hollow'] or head['y1'] - head['y0'] + 1 > FAR_MARK[0] * layers['head'][1]:
            continue
        for stem in head['stems']:
            toward = 'up' if stem['direction'] == 'down' else 'down'
            if any(other is not head and other['staff'] == head['staff'] and not other['hollow']
                   and abs(other['cy'] - head['cy']) >= FAR_MARK[1] * space
                   and other['x0'] - 2 <= stem['x'] <= other['x1'] + 2 and other['y0'] - 3 <= stem['end'] <= other['y1'] + 3
                   and not any(own['direction'] == toward for own in other['stems']) for other in heads):
                gone.add(id(head))
                break
    if FAR_FLAG:
        ink = layers['ink']
        for head in heads:
            if head['hollow'] or id(head) in gone or len(head['stems']) != 1 or head['stems'][0]['direction'] != 'down' \
                    or head['stems'][0].get('past', 0.0) > FAR_FLAG[0] * space:
                continue
            stem = head['stems'][0]
            column = int(round(stem['x']))
            for other in heads:
                if other is head or other['staff'] != head['staff'] or other['hollow'] or other['y1'] >= head['y0'] \
                        or head['cy'] - other['cy'] < FAR_FLAG[1] * space or head['y0'] - other['y1'] > FAR_FLAG[2] * space + 1 \
                        or not other['x0'] - 2 <= stem['x'] <= other['x1'] + 2:
                    continue
                strip = ink[int(other['y1']):int(head['y0']) + 1, max(0, column - 3):column + 4]
                joined = bool(strip.size) and bool(strip.any(axis=1).all())
                down = any(own['direction'] == 'down' for own in other['stems'])
                if FAR_FLAG_LOG is not None:
                    FAR_FLAG_LOG.append({'x0': head['x0'], 'y0': head['y0'], 'x1': head['x1'], 'y1': head['y1'], 'cx': head['cx'],
                                         'cy': head['cy'], 'high': (head['y1'] - head['y0'] + 1) / layers['head'][1],
                                         'past': stem.get('past', 0.0) / space, 'gap': (head['y0'] - other['y1']) / space,
                                         'joined': joined, 'down': down, 'fired': joined and not down, 'staff': head['staff'],
                                         'other': (other['x0'], other['y0'], other['x1'], other['y1'],
                                                   [(own['direction'], own['x'], own['end']) for own in other['stems']])})
                if joined and not down:
                    gone.add(id(head))
                    break
    return [head for head in heads if id(head) not in gone]


TOP_LOOP = (0.25, 0.5)   # a hollow mark with one stem down at its left, whose stroke runs down into a filled head of
#   its staff and meets that head at its right side (the middle column of the stroke at least the first number of the
#   head's half width right of the head's middle), is the loop that the flag of that head's stem up closes at the stem's
#   top, and no head: a stem up leaves its head at the head's right side, and the flag hangs at its far end; the stem of
#   a chord or of two voices on one stem line leaves the lower head at its left side or its middle. The lower head must
#   be a head: at least the second number times as high as the page's heads (where a hand's stem crosses a ledger
#   line, the crossing is a thin mark), and no letter of the words (the stem of a half note on a ledger line under the
#   staff runs into the h of the word under it). A census at this step on every page of LitChoir (73 hollow marks whose
#   one stem down runs into a filled head under them, each looked at): the 18 true half notes meet their head at 0.10
#   or less, and the marks from 0.25 on are flag loops, the cell of a flag by hand and the d of a "3rd", besides one
#   true half note by hand whose stem crosses a ledger line and one printed head over a letter (the two guards). The
#   fresh set holds one such mark, at 0.05. None: off


TOP_STEM = True   # and where that head has no stem up and its stem down carries a flag, the stroke is its stem up and the
#   loop is that stem's flag: a head that two voices share, each an eighth (the print draws the upper voice's flag back
#   to its stem, and the reader had given the stem to the loop). False: off
TOP_STEM_LOG = None


def without_top_loops(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the hollow marks that are the loop of a flag at the top of another head's stem up
    (TOP_LOOP). It runs after the flags are counted."""
    if not TOP_LOOP or not layers.get('head'):
        return heads
    space, high = layers['space'], layers['head'][1]
    gone = set()
    for head in heads:
        if not head['hollow'] or len(head['stems']) != 1 or head['stems'][0]['direction'] != 'down':
            continue
        stem = head['stems'][0]
        mid = stem.get('mid', stem['x'])
        if mid >= head['cx']:
            continue
        below = [other for other in heads if other is not head and other['staff'] == head['staff'] and not other['hollow']
                 and other['cy'] > head['cy'] + 0.3 * space and other['y0'] <= stem['end'] + 2
                 and other['x0'] - 2 <= mid <= other['x1'] + 2]
        if not below:
            continue
        other = min(below, key=lambda mark: mark['cy'])
        half = max(1.0, (other['x1'] - other['x0']) / 2)
        if (mid - other['cx']) / half >= TOP_LOOP[0] and other['y1'] - other['y0'] + 1 >= TOP_LOOP[1] * high \
                and not _in_words(layers, other):
            gone.add(id(head))
            if TOP_STEM and other['tails'].get('down', 0) >= 1 and not any(own['direction'] == 'up' for own in other['stems']):
                # The stroke is the lower head's stem up, and the loop its flag (TOP_STEM).
                up = dict(stem, direction='up', x=mid, end=float(head['y0']), length=float(other['cy'] - head['y0']), marks=[])
                other['stems'] = other['stems'] + [up]
                other['tails'] = dict(other['tails'], up=1)
                if TOP_STEM_LOG is not None:
                    TOP_STEM_LOG.append((other['staff'], round(other['cx']), round(other['cy'])))
    return [head for head in heads if id(head) not in gone]


STEM_END_SPAN = (1.3, 0.9, 1.2)   # a filled mark that stands between the ends of two stems is the beam or the slur
#   between them and no head: at least the first number times the page's head wide and at most the second times its
#   head high (a bow or a beam by its shape), with another head's stem at each of its two sides, standing within the
#   third number of staff spaces of that side and ending within the same of the mark's middle row. The two stems end
#   at the mark's sides and not inside its box, where STEM_END_MARK reads them: the bow's own ends curve down to the
#   stems, and the beam under it takes them. A census of every long flat mark of all 657 pages of LitChoir (581, each
#   with the scorer's verdict) gave the limit: the 8 marks whose two stems stand within 1.2 staff spaces are slurs
#   over two beamed notes and beams, each looked at (the 7 that the scorer judges are notes that are not there), and
#   the nearest true note stands at 1.43. Alone: 1 note gained on the clean copies, on all scores and on the fresh
#   set, none lost; 10 notes that are not there fewer on LitChoir by the count (a mark that both voices of a staff
#   were given counts twice) and 5 on the fresh set, whose 4 marks are slurs at two beamed notes too. None: off


def without_stem_spans(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the long flat marks that stand between the ends of two stems (STEM_END_SPAN): the bow of a
    slur over two beamed notes, or a beam that no stem of its own shows."""
    if not STEM_END_SPAN or not layers.get('head'):
        return heads
    space = layers['space']
    wide, high = layers['head'][0], layers['head'][1]
    reach = STEM_END_SPAN[2] * space
    gone = set()
    for head in heads:
        if head['hollow'] or head['x1'] - head['x0'] + 1 < STEM_END_SPAN[0] * wide \
                or head['y1'] - head['y0'] + 1 > STEM_END_SPAN[1] * high:
            continue
        sides = [False, False]
        for other in heads:
            if other is head or other['staff'] != head['staff'] \
                    or (abs(other['cx'] - head['cx']) < 2 and abs(other['cy'] - head['cy']) < 2):
                continue
            for stem in other['stems']:
                if abs(stem['end'] - head['cy']) > reach:
                    continue
                if stem['x'] <= head['cx'] and abs(head['x0'] - stem['x']) <= reach:
                    sides[0] = True
                if stem['x'] >= head['cx'] and abs(stem['x'] - head['x1']) <= reach:
                    sides[1] = True
        if all(sides):
            gone.add(id(head))
    return [head for head in heads if id(head) not in gone]


BOW_MIDDLE = (1.8, 0.7, 2.2, 0.4, 0.2)   # the swollen middle of a bold bow, read as a head with the bow's own end as its
#   stem: a filled mark at least the first number times the page's head wide, whose thick ink is at most the second
#   number of staff spaces fat, with one stem that ends within the third number of staff spaces of the mark's middle
#   row and stands within the fifth number of the mark's width of one end of the mark, and with a slim arm at the other
#   end that leaves the mark the stem's way for the fourth number of staff spaces or more: the two ends of a bow turn
#   the same way, one at each end of its middle. A head has one stem, and the stem of another voice goes the other
#   way. A rule for one case: of the 965 wide filled marks with one stem on LitChoir's scan pages (round 81, at the
#   reader's own step), 26 are this wide and slim with a stem this short, most of them true heads on a ledger dash,
#   and 5 have such an arm. The stems of two bows stand 0.11 and 0.12 of the width from the end (the slur under two
#   quarter notes of one clean score, and a bow under two notes that a later step takes); the others are a head on a
#   ledger dash whose stem stands in its middle, a head by hand with its flag, and a fermata (0.39 to 0.48). The first
#   form, without the stem's place, took the two heads. None: off


def _bow_arm(layers: dict, head: dict, stem: dict) -> float:
    """How far a slim piece of ink leaves a mark at its end away from the stem, the stem's way, in staff spaces."""
    space = layers['space']
    bare = layers['bare']
    up = stem['direction'] == 'up'
    end = head['x0'] if abs(stem['x'] - head['x0']) > abs(stem['x'] - head['x1']) else head['x1']
    first, last = int(max(0, end - 0.7 * space)), int(min(bare.shape[1], end + 0.5 * space))
    slim = int(0.45 * space)
    rows = 0
    for step in range(1, int(1.6 * space)):
        row = head['y0'] - step if up else head['y1'] + step
        if not 0 <= row < bare.shape[0]:
            break
        ink = int(bare[row, first:last].sum())
        if 0 < ink <= slim:
            rows += 1
        elif ink == 0 and step > 3 and not layers['lines'][row, first:last].any():
            break
    return rows / space


def without_bow_middles(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the swollen middle of a bold bow whose own end was read as its stem (BOW_MIDDLE)."""
    if not BOW_MIDDLE or not layers.get('head'):
        return heads
    space = layers['space']
    kept = []
    for head in heads:
        if not head['hollow'] and not head.get('thin') and len(head['stems']) == 1 \
                and head['x1'] - head['x0'] + 1 >= BOW_MIDDLE[0] * layers['head'][0] \
                and abs(head['stems'][0]['end'] - head['cy']) <= BOW_MIDDLE[2] * space \
                and min(abs(head['stems'][0]['x'] - head['x0']), abs(head['stems'][0]['x'] - head['x1'])) <= BOW_MIDDLE[4] * (head['x1'] - head['x0'] + 1) \
                and _fat(layers, head)['fat'] <= BOW_MIDDLE[1] and _bow_arm(layers, head, head['stems'][0]) >= BOW_MIDDLE[3]:
            continue
        kept.append(head)
    return kept


BEAM_PIECE = (0.7, 0.75, 0.3)   # a flat mark on the line between the ends of two stems that both carry a flag or a beam is
#   a piece of that beam, of a flag or of a slur over the two stem ends, and no head: at most the first number times as
#   high as the page's heads, with its middle within the second number of staff spaces of the straight line between the
#   ends of two neighbouring stems of one direction (0.8 staff spaces to BEAM_NEXT apart), no further than the third
#   number past either of them, the head of neither, and with no stem of its own that goes their way. A staff line cuts
#   such a piece out of a thick beam, and the piece was read as a small filled head with the stem under the beam as its
#   own, seen from the beam, or the cell between a slanted beam and a staff line as a hollow one. STEM_END_MARK and
#   STEM_END_SPAN take the pieces that are wider than a head. (A census at this step on every scan page of LitChoir: 94
#   marks lie so, and the 44 that are flat were each looked at. 42 have no stem that goes the pair's way: 31 pieces of
#   beams and of flags and cells under them, 7 slurs across two stems, 3 pieces of a sign of common time by hand beside
#   the clef and a letter of a heading; none is a note, and the count had called 2 of them right by chance. Of the two
#   with such a stem one is a small head by hand between two short stems, which stays. The true heads on such a line
#   are 0.74 times as high as the page's heads (one, by hand) and 0.79 or more, and half of them have a stem of their
#   own that goes the pair's way: a hand sets a note of the other voice there. Between 0.7 and 0.9 true and false stand
#   mixed, and the rule leaves them.) None: off


def without_beam_pieces(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the flat marks that lie on the beam between two stems (BEAM_PIECE). Runs after count_tails(),
    which counts the flags and the beams of a stem."""
    if not BEAM_PIECE or not layers.get('head'):
        return heads
    by = {}
    for head in heads:
        for stem in head['stems']:
            by.setdefault((head['staff'], stem['direction']), []).append((head, stem))
    gone = set()
    for (staff, way), pairs in by.items():
        space = layers['staves'][staff]['space'] if staff < len(layers.get('staves', [])) else layers['space']
        flat = BEAM_PIECE[0] * layers['head'][1] * space / layers['space']
        # The stems of the staff that go this way, each once (the heads of a chord share theirs).
        stems = []
        for head, stem in sorted(pairs, key=lambda pair: pair[1]['x']):
            if not stems or abs(stem['x'] - stems[-1]['x']) > 3:
                stems.append({'x': stem['x'], 'end': stem['end'], 'tails': 0, 'heads': []})
            one = stems[-1]
            one['end'] = min(one['end'], stem['end']) if way == 'up' else max(one['end'], stem['end'])
            one['tails'] = max(one['tails'], head.get('tails', {}).get(way, 0))
            one['heads'].append(id(head))
        for one, two in zip(stems, stems[1:]):
            if not 0.8 * space <= two['x'] - one['x'] <= BEAM_NEXT * space or one['tails'] < 1 or two['tails'] < 1:
                continue
            for head in heads:
                if head['staff'] != staff or id(head) in one['heads'] or id(head) in two['heads'] \
                        or head['y1'] - head['y0'] + 1 > flat or any(stem['direction'] == way for stem in head['stems']) \
                        or not one['x'] - BEAM_PIECE[2] * space <= head['cx'] <= two['x'] + BEAM_PIECE[2] * space:
                    continue
                x = min(max(head['cx'], one['x']), two['x'])
                row = one['end'] + (two['end'] - one['end']) * (x - one['x']) / (two['x'] - one['x'])
                if abs(head['cy'] - row) <= BEAM_PIECE[1] * space:
                    gone.add(id(head))
    return [head for head in heads if id(head) not in gone]


LINE_MARK = (10.0, 0.9, 0.85, 0.4)   # a mark whose stems are all this many staff spaces long or more hangs on a line of
#   the system (a bar line through its staves, the line that opens or ends them): no stem goes on through the next
#   staff. Such a mark is a head only by its own shape. A hollow one whose closed paper is level at the line's side in
#   the second number of its rows (within a pixel of its first or last column there) and smaller than the last number
#   (staff spaces squared) is a cell that the line closes with a staff line and a slur or a stroke; the inside of a head
#   is round, with the head's rim between it and the stem. A filled one is a slur that crosses the line or ends at it,
#   the tail of a hairpin, a letter of the dynamics between the staves or a number of the time signature on a bar line.
#   Both only where the widest disc in the mark's ink is under the third number times the usual one of the page's
#   filled heads: a hand draws a head against a bar line, and that head is as fat as its neighbours. (A census of
#   every such stem of LitChoir's pages, 104 marks, each looked at. The cells are 0.25 staff spaces squared at most;
#   a hand's half note whose rim is the last bar line of its staff has 0.55, and so have a natural that is printed
#   against a bar line and a loop of a clef at the opening line, which stay as they were read. Two hollow heads by hand
#   with an open rim, read as filled quarter notes with the bar line as their stem, go with the filled marks.) None: off


def without_line_marks(layers: dict, heads: list[dict], bars: dict[int, list[float]] | None = None) -> list[dict]:
    """The heads without the marks that hang on a line of the system and have no shape of a head (LINE_MARK). The
    line of a mark that goes is a bar line of its staff, where no head hangs on it (`bars` is filled in)."""
    if not LINE_MARK or not layers.get('head'):
        return heads
    space = layers['space']
    long, level, fat, large = LINE_MARK
    fats = [head['alt']['fat'] for head in heads if not head['hollow'] and head.get('alt')]
    usual = float(np.median(fats)) * space if fats else 0.0
    if not usual:
        return heads
    ink, holes = layers['ink'], layers['holes']
    out, lines = [], []
    for head in heads:
        stems = head['stems']
        if not stems or any(stem['length'] < long * space for stem in stems):
            out.append(head)
            continue
        y0, x0 = max(0, int(head['y0']) - 1), max(0, int(head['x0']) - 1)
        box = (slice(y0, int(head['y1']) + 2), slice(x0, int(head['x1']) + 2))
        own = np.ascontiguousarray(ink[box])
        if 2 * cv2.distanceTransform(np.pad(own.astype(np.uint8), 1), cv2.DIST_L2, 3).max() >= fat * usual:
            out.append(head)
            continue
        # The line leans on a scan: its column in the rows of the mark, from the stem's far end through its middle.
        stem = stems[0]
        start = stem['end'] - stem['length'] if stem['direction'] == 'down' else stem['end'] + stem['length']
        half = (start - stem['end']) / 2
        at = stem['x'] + ((stem.get('mid', stem['x']) - stem['x']) / half * (head['cy'] - stem['end']) if abs(half) > 1 else 0.0)
        if head['hollow']:
            count, labels, stats, _ = cv2.connectedComponentsWithStats(holes[box].astype(np.uint8), connectivity=4)
            if count < 2:
                out.append(head)
                continue
            index = 1 + int(np.argmax(stats[1:, 4]))
            x, y, wide, high, _ = stats[index]
            part = labels[y:y + high, x:x + wide] == index
            if at < head['cx']:
                share = float((part.argmax(axis=1) <= 1).mean())
            else:
                share = float((wide - 1 - part[:, ::-1].argmax(axis=1) >= wide - 2).mean())
            if share < level or stats[index, 4] >= large * space * space:
                out.append(head)
                continue
        lines.append((head['staff'], float(at)))
    if bars is not None:
        for staff, at in lines:
            if all(abs(at - x) > 0.4 * space for x in bars.get(staff, [])) and not any(
                    head['staff'] == staff and head['x0'] - 0.2 * space <= at <= head['x1'] + 0.2 * space for head in out):
                bars[staff] = sorted(bars.get(staff, []) + [at])
    return out


def without_f_marks(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the paper that the two letters of an ff close in between them (F_SIGN): it was read as a
    hollow head beside the staff with the stroke of one letter as its stem and their crossbar as its ledger line. The
    mark lies between two strokes of the shape of the letter that share a crossbar; a mark with a ledger line that is
    no crossbar of its stroke stays. (With one such stroke alone the step took 38 marks on 30 pages of LitChoir, most
    of them true notes on a ledger line whose short stem a hand drew leaning.)"""
    if not F_SIGN:
        return heads
    space = layers['space']
    strokes = [(stroke, rows) for stroke in layers['strokes'] if stroke['slim']
               for rows in [_f_cross(stroke, space)] if rows]
    if len(strokes) < 2:
        return heads
    out = []
    for head in heads:
        if head['hollow'] and len(head['stems']) == 1 and abs(head['place']) > 4.6:
            stem = head['stems'][0]
            top, bottom = min(head['cy'], stem['end']), max(head['cy'], stem['end'])
            own = [(stroke, rows) for stroke, rows in strokes if abs(stroke['x'] - stem['x']) <= 0.2 * space
                   and min(bottom, stroke['y1']) - max(top, stroke['y0']) >= 0.5 * (stroke['y1'] - stroke['y0'])
                   and all(any(abs(line - row) <= 2 for row in rows) for line in head.get('ledgers') or [])]
            if any(other is not stroke and (other['x'] - head['cx']) * (stroke['x'] - head['cx']) < 0
                   and abs(other['x'] - stroke['x']) <= F_SIGN[3] * space
                   and any(abs(row - line) <= 2 for row in rows for line in others)
                   for stroke, rows in own for other, others in strokes):
                continue        # the letter at the mark's other side, on the same crossbar
        out.append(head)
    return out


P_BOWL = (0.3, 0.3, 0.9, 1.5, 0.7, 0.15)   # the bowl of the letter p of the dynamics (p, pp, mp) is no whole note: a hollow
#   mark without a stem beside the staff, with no ledger line, whose ink goes on under it in the stroke of the letter.
#   In the first number of staff spaces under the mark (after the last rows of the bowl itself, the last number at
#   most) the ink of its piece stands under its left half and at its left, with paper under the rest of it (but for
#   its last three tenths, where the next letter of a pp begins), in the third number of the rows; the stroke is bold, the
#   fourth number times the page's slim strokes wide or more, and at most the fifth number of the mark's width; and
#   the bowl is the top of the letter: no ink of the piece in the second number of staff spaces over the mark. A half
#   note has a slim stem, and a line by hand through a head goes on over it. The rim of a whole note under a whole
#   note stands as the stroke does, with the inside of that note as the paper: a mark with a head under it stays. (The
#   rule's measures on every page of LitChoir: 9 marks, each looked at, eight letters p and the g of a heading.)
#   None: off


def _p_under(layers: dict, head: dict) -> tuple[int, float, float]:
    """The ink of a mark's own piece (without the staff lines) around it, for P_BOWL: the px over the mark, the share
    of the rows under it that hold a stroke at its left and paper under its right, and the stroke's median width
    (px)."""
    bare, space = layers['bare'], layers['space']
    height, width = bare.shape
    x0, x1, y0, y1 = int(head['x0']), int(head['x1']), int(head['y0']), int(head['y1'])
    wide = x1 - x0 + 1
    reach = int(space)
    bx0, bx1, by0, by1 = max(0, x0 - wide), min(width, x1 + reach + 1), max(0, y0 - reach), min(height, y1 + reach + 1)
    region = np.ascontiguousarray(bare[by0:by1, bx0:bx1]).astype(np.uint8)
    _, labels = cv2.connectedComponents(region, connectivity=8)
    inside = labels[y0 - by0:y1 - by0 + 1, x0 - bx0:x1 - bx0 + 1]
    ids = [index for index in np.unique(inside) if index]
    if not ids:
        return 0, 0.0, 0.0
    piece = labels == max(ids, key=lambda index: int((inside == index).sum()))
    left, middle = max(0, x0 - int(0.6 * wide)) - bx0, x0 + wide // 2 - bx0
    last = x1 - int(0.3 * wide) - bx0
    over = piece[max(0, y0 - int(P_BOWL[1] * space) - by0):max(0, y0 - 1 - by0),
                 max(0, x0 - int(0.3 * wide) - bx0):x1 + int(0.3 * wide) + 1 - bx0]
    under = piece[y1 + 1 - by0:]
    skip = 0
    while skip < min(under.shape[0], int(P_BOWL[5] * space)) and under[skip, middle:last + 1].any():
        skip += 1
    under = under[skip:skip + max(2, int(P_BOWL[0] * space))]
    if not under.shape[0]:
        return int(over.sum()), 0.0, 0.0
    stroke = under[:, left:middle].sum(axis=1)
    rows = (stroke > 0) & ~under[:, middle:last + 1].any(axis=1)
    return int(over.sum()), float(rows.mean()), float(np.median(stroke[rows])) if rows.any() else 0.0


def without_p_bowls(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the bowls of the letter p of the dynamics (P_BOWL)."""
    if not P_BOWL:
        return heads
    space = layers['space']
    widths = [stroke['width'] for stroke in layers['strokes']
              if stroke['slim'] and stroke['y1'] - stroke['y0'] + 1 >= 2.5 * space]
    usual = float(np.median(widths)) if widths else 0.0
    if not usual:
        return heads
    out = []
    for head in heads:
        if head['hollow'] and not head['stems'] and abs(head['place']) > 4.6 and not head.get('ledgers') and not any(
                other is not head and other['staff'] == head['staff'] and head['cy'] < other['y0'] <= head['y1'] + space
                and min(other['x1'], head['x1']) - max(other['x0'], head['x0']) >= 0.5 * (head['x1'] - head['x0'])
                for other in heads):
            over, share, width = _p_under(layers, head)
            if not over and share >= P_BOWL[2] and P_BOWL[3] * usual <= width <= P_BOWL[4] * (head['x1'] - head['x0'] + 1):
                continue
        out.append(head)
    return out


ROW_LETTER = (3, 0.7, 0.5, 1.8)   # a hollow mark without a stem beside the staff is a letter of a row of words (a heading in
#   capitals, a short row of words right over the staff, a word by hand), not a whole note, where marks of a letter's
#   height stand in its rows at both of its sides, one after the other: each at most the second number of the mark's
#   widths from the mark or from the one before it, as high as the third to the fourth number of the mark's height, and
#   overlapping at least half of the mark's rows or of their own; the first number of them or more in all. The marks are
#   counted in the ink opened upright by 0.35 staff spaces, so that the staff lines, the ledger lines and the crossbar of
#   a letter go. A whole note stands alone in its rows, between the bars of a breve of the ison (one mark at each side),
#   beside a sign, a dot or another head (no run of three). A census of every hollow mark without a stem beside the
#   staff on LitChoir's pages (834, with the scorer's verdicts): the 7 with three such marks or more and one at each
#   side are letters (an e of a row "her / their" right over the staff, an o of "Lord", the O of a heading); 3 of the
#   marks with three or more at one side only are true notes. None: off
ROW_LETTER_LOG = None   # a list: (staff, the mark's middle, the marks before it, the marks after it) where ROW_LETTER acts


def _row_marks(layers: dict, head: dict) -> tuple[int, int]:
    """(ROW_LETTER) How many marks of a letter's height stand one after the other in a head's rows, before it and
    after it."""
    ink, space = layers['ink'], layers['space']
    height, width = ink.shape
    wide, high = head['x1'] - head['x0'] + 1, head['y1'] - head['y0'] + 1
    size = max(3, int(round(0.35 * space))) | 1
    left, right = max(0, int(head['cx'] - 12 * space)), min(width, int(head['cx'] + 12 * space) + 1)
    top, bottom = max(0, int(head['cy'] - 3 * space)), min(height, int(head['cy'] + 3 * space) + 1)
    window = np.pad((ink[top:bottom, left:right] > 0).astype(np.uint8), size)
    opened = cv2.morphologyEx(window, cv2.MORPH_OPEN, np.ones((size, 1), np.uint8))[size:-size, size:-size]
    count, _, stats, _ = cv2.connectedComponentsWithStats(np.ascontiguousarray(opened), connectivity=8)
    x0, x1, y0, y1 = head['x0'] - left, head['x1'] + 1 - left, head['y0'] - top, head['y1'] + 1 - top
    marks = []
    for index in range(1, count):
        x, y, w, h = (int(value) for value in stats[index][:4])
        if x < x1 and x + w > x0 and y < y1 and y + h > y0:
            continue      # the mark's own ink
        if min(y + h, y1) - max(y, y0) < 0.5 * min(h, high) or not ROW_LETTER[2] * high <= h <= ROW_LETTER[3] * high:
            continue
        marks.append((x, x + w))
    begin, end, before, after = x0, x1, 0, 0
    used, grew = set(), True
    while grew:
        grew = False
        for number, (a, b) in enumerate(marks):
            if number in used:
                continue
            if b <= begin and begin - b <= ROW_LETTER[1] * wide:
                begin, before, grew = a, before + 1, True
                used.add(number)
            elif a >= end and a - end <= ROW_LETTER[1] * wide:
                end, after, grew = b, after + 1, True
                used.add(number)
    return before, after


def without_row_letters(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the letters of a row of words beside the staff that were read as whole notes (ROW_LETTER)."""
    if not ROW_LETTER:
        return heads
    out = []
    for head in heads:
        if head['hollow'] and not head['stems'] and not head.get('thin') and abs(head['place']) > 4.6:
            before, after = _row_marks(layers, head)
            if before and after and before + after >= ROW_LETTER[0]:
                if ROW_LETTER_LOG is not None:
                    ROW_LETTER_LOG.append((head['staff'], round(head['cx']), round(head['cy']), before, after))
                continue
        out.append(head)
    return out

STEM_MEET = (0.5, 0.5, 2.0, 2.5)   # two stems that meet end to end in one column (at most the first number of staff spaces
#   apart sideways, their ends at most the second number apart), the upper head's stem going down and the lower head's
#   going up, are one stroke with a head at each end. No chord has one: its stem leaves all of its heads at one end. The
#   head whose stem is shorter than the third number of staff spaces, where the other's is at least the fourth number
#   long, is a mark at the end of that note's stem: a tick by pen, the end of a bow, a piece of a beam by hand. (Four
#   such pairs on LitChoir's pages, each looked at, and none on the fresh set.) None: off


def without_stem_meets(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the marks that hang on the end of another head's stem by a short stroke of their own
    (STEM_MEET)."""
    if not STEM_MEET:
        return heads
    space = layers['space']
    side, along, short, long = STEM_MEET
    gone = set()
    for upper in heads:
        for lower in heads:
            if lower is upper or lower['staff'] != upper['staff'] or lower['cy'] <= upper['cy']:
                continue
            for down in (stem for stem in upper['stems'] if stem['direction'] == 'down'):
                for up in (stem for stem in lower['stems'] if stem['direction'] == 'up'):
                    if abs(up['x'] - down['x']) > side * space or abs(up['end'] - down['end']) > along * space:
                        continue
                    over, under = (down['end'] - upper['cy']) / space, (lower['cy'] - up['end']) / space
                    if over < short and under >= long and len(upper['stems']) == 1:
                        gone.add(id(upper))
                    elif under < short and over >= long and len(lower['stems']) == 1:
                        gone.add(id(lower))
    return [head for head in heads if id(head) not in gone]


DOT_COLUMN = (0.75, 2, 0.8, 1.25)   # a column of printed dots, one in each space (a sign before the first chord of one
#   print), was read as a filled head with the dots under it as its stem: the top dot is a mark of its own with no ink
#   that leaves it, under the first number times the width of the page's heads, and the "stem" runs through at least
#   the second number of other such marks, each from the third to the fourth number times the mark's width and
#   height, the last of which ends it. A printed stem is ink of its own that leaves its head. (A census of every head
#   of read_symbols that no ink of its own leaves and whose stem runs through other such marks of about its size: 24
#   places on LitChoir's pages and none on the fresh set; only the column of three dots runs through two or more, and a
#   reading of every page changes that page only.) A rule for one case. None: off


def without_dot_columns(layers: dict, heads: list[dict]) -> list[dict]:
    """The heads without the top dot of a column of printed dots that was read with the dots under it as a stem
    (DOT_COLUMN)."""
    if not DOT_COLUMN:
        return heads
    narrow, least, low, high = DOT_COLUMN
    bare = layers['bare']
    labels = None
    gone = set()
    for head in heads:
        if head.get('hollow') or len(head['stems']) != 1:
            continue
        x0, y0, x1, y1 = int(head['x0']), int(head['y0']), int(head['x1']), int(head['y1'])
        wide, tall = x1 - x0 + 1, y1 - y0 + 1
        if wide >= narrow * layers['head'][0]:
            continue
        if labels is None:
            _, labels, stats, _ = cv2.connectedComponentsWithStats(bare.astype(np.uint8), connectivity=8)
        box = labels[y0:y1 + 1, x0:x1 + 1]
        if not (box > 0).any():
            continue
        own = int(np.bincount(box[box > 0].ravel()).argmax())
        ox, oy, ow, oh, _ = stats[own]
        if ox < x0 - 3 or oy < y0 - 3 or ox + ow > x1 + 4 or oy + oh > y1 + 4:
            continue                    # ink of its own leaves the mark: a stem, a flag, a beam
        stem = head['stems'][0]
        down = stem['direction'] == 'down'
        top, bottom = (y1 + 1, int(stem['end'])) if down else (int(stem['end']), y0 - 1)
        if bottom <= top:
            continue
        column = labels[top:bottom + 1, max(0, int(stem['x']) - 2):int(stem['x']) + 3]
        others = {int(v) for v in column.ravel() if v and v != own}
        if len(others) < least:
            continue
        boxes = [stats[other] for other in others]
        if not all(low * wide <= w <= high * wide and low * tall <= h <= high * tall for _, _, w, h, _ in boxes):
            continue
        last = max(boxes, key=lambda b: b[1] + b[3]) if down else min(boxes, key=lambda b: b[1])
        if (abs(last[1] + last[3] - 1 - stem['end']) if down else abs(last[1] - stem['end'])) <= 3:
            gone.add(id(head))
    return [head for head in heads if id(head) not in gone]


GRACE = (0.25, 0.38, 0.62, 0.15, 0.6, 2.4, 3.4, 0.2, 0.6, 0.15, 0.5, 0.04)
#   a grace note: a small head with a stem down that ends in a knot of its flag and a slash, which one print sets
#   between two notes under a slur. The reader read the knot as a filled head with the stem up to the small head, the
#   paper between the slur and the small head as a half note with the stem down, or the small head as an eighth note.
#   The stroke of the stem is followed in the ink without the staff lines, both ways from the middle of a read stem: at
#   its top tip a knob (the small head) begins within the first number of a head's height, from the second to the third
#   number of the page's heads wide where it is wider than the stroke by 3 pixels and an eighth of a head, from the
#   fourth to the fifth number of a head's height long, and the stroke narrows to the stem under it; the stroke is from
#   the sixth to the seventh number of staff spaces long; within 1.2 staff spaces of its bottom tip ink stands from the
#   eighth to the ninth number of staff spaces left of the stem (the slash) and from the tenth to the eleventh right of
#   it (the flag). The small head stands in paper: other ink within a quarter of a head's width beside it and half a
#   head's height under it is at most the twelfth number of square staff spaces (a beam or a flag that leaves the top of
#   a stem up, the knob of a stem that runs into a word). The marks that were read from such a stroke are no notes; the
#   small head is a grace note, which takes no time and is written before the next note of its staff
#   (scorereader.music.musicxml). (A census of the whole stroke of every stem of LitChoir's scan pages, at this step:
#   the ten grace notes of the two scans of one print measure a knob 0.43 to 0.5 heads wide and 0.18 to 0.4 high, 0.1 to
#   0.21 heads under the tip, a stroke of 2.64 to 3.2 staff spaces, a slash of 0.24 to 0.54 and a flag of 0.19 to 0.42
#   staff spaces, and other ink of 0.025 square staff spaces at most; of the 63 other strokes that pass the first seven
#   limits, 49 reach further than 0.6 staff spaces left at the bottom tip and 8 further than 0.5 right, and the 5 that
#   pass the knot by the rule's own arithmetic (a sixth by rounded measures) have 0.05 square staff spaces of ink or
#   more beside the knob, the 10 grace notes of the census alone pass all limits; none on the fresh set.) A rule for one
#   print: a standard acciaccatura with its stem up and its slash at the flag, and a grace note by hand, are not read.
#   None: off
GRACE_SEEN = None    # a census: every grace stroke with its measures


def _ink_run(bare: np.ndarray, y: int, x: int) -> tuple[int, int] | None:
    """The run of ink in row y that holds column x, or a pixel within 2 of it: (left, right)."""
    height, width = bare.shape
    if not 0 <= y < height:
        return None
    row = bare[y]
    for dx in (0, -1, 1, -2, 2):
        if 0 <= x + dx < width and row[x + dx]:
            start = x + dx
            break
    else:
        return None
    left = right = start
    while left > 0 and row[left - 1]:
        left -= 1
    while right < width - 1 and row[right + 1]:
        right += 1
    return left, right


def _stem_stroke(bare: np.ndarray, head: dict, stem: dict, space: float) -> list[tuple[int, int, int, int]]:
    """The stroke of a stem in the ink without the staff lines, followed both ways from the middle of the stem (over
    gaps of a staff line's height): (row, column, left, right) from its top tip to its bottom tip."""
    tip, middle, end = int(stem['x']), int(stem.get('mid', stem['x'])), int(stem['end'])
    cy = int(round(head['cy']))

    def column(y: int) -> int:
        share = min(max((y - cy) / (end - cy), -1.0), 1.5) if end != cy else 0.0
        return int(round(middle + (tip - middle) * share))

    seed = next((y for y in ((cy + end) // 2 + dy for dy in (0, 1, -1, 2, -2, 3, -3)) if _ink_run(bare, y, column(y))), None)
    if seed is None:
        return []
    rows = {}
    for step in (-1, 1):
        y, gap = seed, 0
        while gap <= max(2, int(0.25 * space)) and abs(y - seed) < 8 * space:
            run = _ink_run(bare, y, column(y))
            if run:
                rows[y] = (column(y),) + run
                gap = 0
            else:
                gap += 1
            y += step
    return [(y,) + rows[y] for y in sorted(rows)]


def grace_notes(layers: dict, heads: list[dict]) -> tuple[list[dict], list[dict]]:
    """The heads without the marks that were read from a grace note, and the grace notes (GRACE): each {'staff', 'cx',
    'cy', 'place'} at its small head."""
    if not GRACE:
        return heads, []
    cap, narrow, wide, short, long, least, most, slash, slash_most, flag, flag_most, alone = GRACE
    bare = layers['bare'] > 0
    space = layers['space']
    head_wide, head_high = layers['head']
    strokes, graces = [], []
    for head in heads:
        for stem in head['stems']:
            rows = _stem_stroke(bare, head, stem, space)
            if len(rows) < 5:
                continue
            if any(abs(rows[0][0] - top) <= 2 and abs(rows[0][1] - x) <= 0.3 * space for top, x, _ in strokes):
                continue
            widths = [right - left + 1 for _, _, left, right in rows]
            n = len(rows)
            ws = float(np.median(widths[n // 4:3 * n // 4 + 1]))
            if not least * space <= rows[-1][0] - rows[0][0] <= most * space:
                continue
            # the knob at the top tip
            knob = [i for i in range(min(int(0.9 * head_high), n)) if widths[i] >= ws + max(3, 0.12 * head_wide)]
            if not knob or knob[0] > cap * head_high:
                continue
            first, last = knob[0], knob[-1]
            if any(widths[i] < ws + 2 for i in range(first, last + 1)):
                continue
            after = widths[last + 1:last + 1 + max(1, int(0.3 * head_high))]
            if not after or min(after) > ws + 2:
                continue
            if not narrow <= max(widths[first:last + 1]) / head_wide <= wide or not short <= (last - first + 1) / head_high <= long:
                continue
            # the slash and the flag within 1.2 spaces of the bottom tip
            near = rows[max(0, n - int(1.2 * space)):]
            left = max(max(0.0, (x - ws / 2) - l) for _, x, l, _ in near) / space
            right = max(max(0.0, r - (x + ws / 2)) for _, x, _, r in near) / space
            if not slash <= left <= slash_most or not flag <= right <= flag_most:
                continue
            # the small head stands in paper: little ink beside it and under it that is no part of the stroke
            y0, y1 = max(0, rows[first][0] - int(0.15 * head_high)), rows[last][0] + int(0.5 * head_high)
            x0 = max(0, min(l for _, _, l, _ in rows[first:last + 1]) - int(0.25 * head_wide))
            x1 = max(r for _, _, _, r in rows[first:last + 1]) + int(0.25 * head_wide)
            near_ink = bare[y0:y1 + 1, x0:x1 + 1].copy()
            for y, _, l, r in rows:
                if y0 <= y <= y1:
                    near_ink[y - y0, max(0, l - x0):max(0, r - x0 + 1)] = False
            if near_ink.sum() > alone * space * space:
                continue
            middle = (first + last) // 2
            cx = float(np.mean([(l + r) / 2 for _, _, l, r in rows[first:last + 1]]))
            cy = float(rows[middle][0])
            strokes.append((rows[0][0], rows[0][1], rows[-1][0]))
            grace = {'staff': head['staff'], 'cx': cx, 'cy': cy, 'place': pitch_place(head['staff_ref'], cy),
                     'x': rows[0][1], 'top': rows[0][0], 'bottom': rows[-1][0]}
            graces.append(grace)
            if GRACE_SEEN is not None:
                GRACE_SEEN.append(dict(grace, staff_ref=None, ws=ws, knob=[first, last], left=left, right=right, near=float(near_ink.sum()) / space ** 2, rows=rows))
    if not graces:
        return heads, []
    # the marks that were read from a grace stroke: a head whose stem is the stroke, or whose middle stands on it
    gone = set()
    for grace in graces:
        for head in heads:
            on = [stem for stem in head['stems'] if abs(stem['x'] - grace['x']) <= 0.3 * space
                  and min(stem['end'], head['cy']) <= grace['bottom'] and max(stem['end'], head['cy']) >= grace['top']]
            inside = abs(head['cx'] - grace['x']) <= 0.4 * space and grace['top'] - 0.2 * space <= head['cy'] <= grace['bottom'] + 0.2 * space
            if (on and len(on) == len(head['stems'])) or (inside and not head['stems']):
                gone.add(id(head))
            elif on:
                head['stems'] = [stem for stem in head['stems'] if stem not in on]
    return [head for head in heads if id(head) not in gone], graces


CHORD_WHOLE = (-85.0, -30.0, 1.1, 2.0)   # a whole note that touches the half note of another voice was read with that
#   note's stem: of the hollow heads that share one stem, the head at the far end from the stem's end (where a stem
#   begins) is a whole note, and leaves the stem to the others, where its inside leans back: the axis of the inside
#   (symbols._hole_axis, 0: level, 90: upright, more rises to the right) stands between the first two numbers of
#   degrees, and the inside is from the third to the fourth number of times as long as wide (a round inside has no
#   direction, and a long slit is no whole note's inside). The inside of a printed half note lies on its side and
#   rises to the right, an engraved whole note's leans back. (A census of the far heads of such chords on every scan
#   page: 11 whole notes at -58 to -80 degrees, 1.16 to 1.66 times as long as wide, and every half note of the clean
#   copies at 0 to 52 degrees; the first form also took a round inside of a half note by hand, a letter d and a
#   stroke by hand, at 1.04, 1.05 and 4.3.) None: off
CENSUS = None      # a list where a rule records what it measured, for a census (None: nothing is kept)


def chord_wholes(layers: dict, heads: list[dict]) -> int:
    """Takes the stem from the whole notes that touch a chord of half notes (CHORD_WHOLE). Returns how many."""
    if not CHORD_WHOLE:
        return 0
    space, count = layers['space'], 0
    for head in heads:
        if not head['hollow'] or len(head['stems']) != 1 or head.get('thin'):
            continue
        if DASH_OWN and head.get('pair_box'):
            continue      # a head that DASH_PAIR cut from its neighbour: the ledger line cuts its inside into slivers
        stem = head['stems'][0]
        down = stem['direction'] == 'down'
        mates = [other for other in heads if other is not head and other['hollow'] and other['staff'] == head['staff']
                 and any(own['direction'] == stem['direction'] and abs(own['x'] - stem['x']) <= 0.35 * space
                         and abs(own['end'] - stem['end']) <= 0.5 * space for own in other['stems'])]
        if not mates or any((other['cy'] < head['cy']) if down else (other['cy'] > head['cy']) for other in mates):
            continue
        long, rise, area, side = _hole_axis(layers, head)
        acts = area >= 6 and CHORD_WHOLE[0] <= rise <= CHORD_WHOLE[1] and CHORD_WHOLE[2] <= long <= CHORD_WHOLE[3]
        if CENSUS is not None:
            CENSUS.append({'cx': head['cx'], 'cy': head['cy'], 'long': long, 'rise': rise, 'area': area, 'side': side,
                           'mates': len(mates), 'down': down, 'acts': acts})
        if acts:
            head['stems'] = []
            head['tails'] = {}
            head['chord_whole'] = True
            count += 1
    return count


WHOLE_DOTLESS = 0.2   # a whole note that touches the dotted half notes of another voice was read with their stem: of
#   the hollow heads that share one stem, the head at the far end from the stem's end is a whole note where it has no
#   dot, every other head of the stem has one, and its oval is wider than each of theirs by this many staff spaces or
#   more. The heads of a chord have their dots together, and a print sets a whole note wider than a half note. (A rule
#   for one case: of 162 such pairs of hollow heads on LitChoir's scan pages 5 have the dot at the other heads only;
#   the whole note is wider by 0.26 staff spaces, the four others by 0.12 at most.) The other heads stand a third
#   away or more: one head that was read twice shares its stem with itself. The head stands in the staff: on a ledger
#   line the line and a dot at its end are one mark with the head, and that mark is wide. None: off


def dotless_wholes(layers: dict, heads: list[dict]) -> int:
    """Takes the stem from a whole note without a dot that touches a chord of dotted half notes (WHOLE_DOTLESS).
    Runs after the dots are read. Returns how many."""
    if not WHOLE_DOTLESS:
        return 0
    space, count = layers['space'], 0
    for head in heads:
        if not head['hollow'] or len(head['stems']) != 1 or head.get('thin') or head.get('dot'):
            continue
        stem = head['stems'][0]
        down = stem['direction'] == 'down'
        mates = [other for other in heads if other is not head and other['hollow'] and other['staff'] == head['staff']
                 and any(own['direction'] == stem['direction'] and abs(own['x'] - stem['x']) <= 0.35 * space
                         and abs(own['end'] - stem['end']) <= 0.5 * space for own in other['stems'])]
        if not mates or any((other['cy'] < head['cy']) if down else (other['cy'] > head['cy']) for other in mates):
            continue
        if abs(head['place']) > 5 or any(abs(other['cy'] - head['cy']) < 0.75 * space for other in mates):
            continue
        wide = head['x1'] - head['x0']
        if all(other.get('dot') and wide - (other['x1'] - other['x0']) >= WHOLE_DOTLESS * space for other in mates):
            head['stems'] = []
            head['tails'] = {}
            head['chord_whole'] = True
            count += 1
    return count


JOINT = (0.45, 1.5, 0.6)   # where a slanted head meets its stem inside a thick staff line: a mark at most this high (staff
#                            spaces), at most this many places from a larger head of that stem at the same side of
#                            the stem, and at most this share of its area (None: off)


def without_joints(heads: list[dict], space: float) -> list[dict]:
    """The heads without the joints of slanted heads. A hand draws a head as a slanted stroke that runs into its
    stem. Where the stroke meets the stem inside a thick staff line, a flat piece of it stays when the line is taken
    away, and that piece looks like a small head on the line. Two heads a step apart on one stem stand at the two
    sides of the stem, so a flat mark beside a larger head at the same side of their stem is no head."""
    if not JOINT:
        return heads
    def size(head: dict) -> float:
        return float(head.get('area') or (head['x1'] - head['x0'] + 1) * (head['y1'] - head['y0'] + 1))

    gone = set()
    for head in heads:
        if head.get('thin') or head['y1'] - head['y0'] + 1 > JOINT[0] * space:
            continue
        # The joint lies in a line of the staff.
        if abs(head['place']) > 4.3 or abs(head['place'] / 2 - round(head['place'] / 2)) > 0.15:
            continue
        for stem in head['stems']:
            for other in heads:
                if other is head or other['staff'] != head['staff'] or id(other) in gone:
                    continue
                if not 0.5 <= abs(other['place'] - head['place']) <= JOINT[1] or size(head) > JOINT[2] * size(other):
                    continue
                shared = any(far['direction'] == stem['direction'] and abs(far['x'] - stem['x']) <= 0.35 * space
                             for far in other['stems'])
                if shared and (head['cx'] - stem['x']) * (other['cx'] - stem['x']) > 0:
                    gone.add(id(head))
    return [head for head in heads if id(head) not in gone]


def _bow_tip(layers: dict, x: int, y: int, wide: int, high: int, labels: np.ndarray, stats: np.ndarray) -> bool:
    """True when the small mark with this box in the ink without the staff lines is the tip of a bow (DOT_TIP).
    labels and stats are the connected pieces of that ink."""
    space, lines = layers['space'], layers['lines']
    width = lines.shape[1]
    index = _staff_of(layers, x, y)
    thick = layers['staves'][index]['thick'] if index is not None else max(staff['thick'] for staff in layers['staves'])
    least = max(2, int(round(DOT_TIP[0] * thick)))
    near = int(round(DOT_TIP[4] * space))
    for first, last in ((x + wide, x + wide + 3), (max(0, x - 3), x)):
        rows = np.nonzero(lines[y:y + high, first:last].any(axis=1))[0]
        if len(rows) < least:
            continue
        row = y + int(rows[len(rows) // 2])
        # The bow comes out of the line where the hidden stretch ends: a piece that begins there, near the line.
        left, right = x + int(round(DOT_TIP[2] * space)), min(width, x + int(round(DOT_TIP[3] * space)) + 1)
        band = labels[max(0, row - near):row + near + 1, left:right]
        for other in np.unique(band):
            if other == 0:
                continue
            start, long = int(stats[other][0]), int(stats[other][2])
            if not left <= start < right or long < DOT_TIP[1] * space:
                continue
            begin = labels[:, start:start + int(round(space))] == other
            inked = np.nonzero(begin.any(axis=1))[0]
            if inked[0] >= row - near and inked[-1] <= row + near and int(begin.sum(axis=0).max()) <= near:
                return True
    return False


def _dot_shade(layers: dict, labels: np.ndarray, index: int, stat):
    """The share of black (layers.BLACK) in the ink of a piece that passes as a dot, in the rows where no staff line
    runs on at its left or its right (DOT_GREY); None where that ink is under DOT_GREY[1] of the piece's ink."""
    x, y, wide, high = int(stat[0]), int(stat[1]), int(stat[2]), int(stat[3])
    piece = labels[y:y + high, x:x + wide] == index
    off = piece & ~layers['lines'][y:y + high, max(0, x - 3):x + wide + 3].any(axis=1)[:, None]
    count = int(off.sum())
    if not count or count < DOT_GREY[1] * int(piece.sum()):
        return None
    return int((layers['black'][y:y + high, x:x + wide] & off).sum()) / count


def _box_black(layers: dict, head: dict) -> float:
    """The share of the ink in a head's box that is black (layers.BLACK)."""
    y0, x0 = max(0, int(head['y0'])), max(0, int(head['x0']))
    y1, x1 = int(head['y1']) + 1, int(head['x1']) + 1
    count = int(layers['ink'][y0:y1, x0:x1].sum())
    return float((layers['black'][y0:y1, x0:x1] & layers['ink'][y0:y1, x0:x1]).sum()) / count if count else 0.0


def _dot_on_line(layers: dict, labels: np.ndarray, index: int, x: int, y: int, wide: int, high: int):
    """A dot that sits on a staff line, with a hair of the line under or over it (DOT_LINE): the box, the ink and the
    middle of the piece without the rows of the line, or None where the piece is no such dot."""
    lines = layers['lines']
    piece = labels[y:y + high, x:x + wide] == index
    inked = piece.any(axis=1)
    # The rows of the line: the line runs on at the left or at the right of the piece.
    line = (lines[y:y + high, max(0, x - 3):x].any(axis=1) | lines[y:y + high, x + wide:x + wide + 3].any(axis=1)) & inked
    rows = np.nonzero(inked & ~line)[0]
    if not line.any() or not len(rows) or rows[-1] - rows[0] + 1 != len(rows):
        return None                     # no line, or ink of the piece at both sides of it: a stroke across the line
    if np.nonzero(line)[0][0] < rows[0] and np.nonzero(line)[0][-1] > rows[-1]:
        return None                     # a line over the piece and a line under it
    part = piece[rows[0]:rows[-1] + 1]
    columns = np.nonzero(part.any(axis=0))[0]
    width = int(columns[-1] - columns[0] + 1)
    if max(int(piece[row].sum()) for row in np.nonzero(line)[0]) > DOT_LINE[0] * width:
        return None                     # the ink in the line is as wide as the mark: no hair
    if part.sum() < DOT_LINE[1] * layers['space'] ** 2:
        return None                     # smaller than a printed dot
    ys, xs = np.nonzero(part)
    return (x + int(columns[0]), y + int(rows[0]), width, len(rows), int(part.sum()),
            (float(x + xs.mean()), float(y + rows[0] + ys.mean())))


DOT_IN_LINE = (0.1, 0.12)   # a piece of a dot's size whose rows all lie within the first number of staff spaces past the
#                    edges of a staff line (its middle row and its thickness), where the line itself goes on at both sides
#                    of the piece in those rows, and that holds less ink than the second number of staff spaces squared,
#                    is a thick stretch of the line or a speck on it, and no dot: the layer of the lines leaves a gap where
#                    a line is thicker than its staff's lines, and the rest of the line there stood as a dot under a half
#                    note. A print with thick lines sets its true dots on the lines, and they are as large as its other
#                    dots. 24 dots went on LitChoir's pages, each looked at, and none was printed (9 lengths that the
#                    typed hymns confirm); none on the fresh set (None: off)
DOT_IN_LINE_SEEN = None   # a census: the pieces that DOT_IN_LINE refuses (None: none)


def _in_line(layers: dict, x: int, y: int, wide: int, high: int) -> bool:
    """Whether the piece in this box lies in the rows of a staff line that goes on at both sides of it (DOT_IN_LINE)."""
    space, lines = layers['space'], layers['lines']
    for staff in layers['staves']:
        if not staff['x0'] <= x <= staff['x1']:
            continue
        for row in staff['rows']:
            reach = staff['thick'] / 2 + DOT_IN_LINE[0] * space
            if row - reach <= y and y + high - 1 <= row + reach:
                band = slice(int(y), int(y + high))
                if lines[band, max(0, x - 3):x].any() and lines[band, x + wide:x + wide + 3].any():
                    return True
    return False


def dots(layers: dict, heads: list[dict]) -> None:
    """Sets head['dot'] to True where a dot stands at the right of a head: a small round mark in the space beside it."""
    space = layers['space']
    # The dots of two voices stand one over the other, and the joining of dashes makes one upright stroke of them:
    # so the dots are looked for in the ink itself, not in the marks that are left without the strokes.
    count, labels, stats, centres = cv2.connectedComponentsWithStats(layers['bare'], connectivity=8)
    haired, grey, shades = set(), set(), []
    found, full, sizes = [], [], []
    for index in range(1, count):
        x, y, wide, high, area = stats[index]
        box, centre, hair = (int(x), int(y), int(wide), int(high)), (float(centres[index][0]), float(centres[index][1])), False
        if not (DOT_SMALL * space <= wide <= 0.6 * space and DOT_SMALL * space <= high <= DOT_HIGH * space) \
                or area < DOT_FILL * wide * high or not DOT_SLIM <= wide / high <= DOT_FLAT:
            # (see DOT_LINE: a dot that keeps a hair of the staff line that it sits on)
            dot = _dot_on_line(layers, labels, index, *box) if DOT_LINE else None
            if dot is None:
                continue
            x, y, wide, high, area, centre = dot
            if not (DOT_SMALL * space <= wide <= 0.6 * space and DOT_SMALL * space <= high <= DOT_HIGH * space) \
                    or area < DOT_FILL * wide * high or not DOT_SLIM <= wide / high <= DOT_FLAT:
                continue
            hair = True
        if DOT_TIP and _bow_tip(layers, *box, labels, stats):
            continue
        if DOT_IN_LINE and not hair and area < DOT_IN_LINE[1] * space * space and _in_line(layers, x, y, wide, high):
            if DOT_IN_LINE_SEEN is not None:
                DOT_IN_LINE_SEEN.append((float(centre[0]), float(centre[1]), int(wide), int(high), int(area)))
            continue
        if hair:
            haired.add(len(found))
        if DOT_GREY:
            shades.append(_dot_shade(layers, labels, index, stats[index]))
        found.append(centre)
        sizes.append((int(x), int(wide), int(high), int(area)))
        full.append(bool(DOT_CLOSE) and not hair and min(wide, high) >= DOT_CLOSE[1] * space and DOT_CLOSE[2] <= wide / high <= DOT_CLOSE[3])
    if DOT_GREY and heads:
        # (see DOT_GREY_PAGE: the page's dots are black)
        rights = np.array([head['x1'] for head in heads], dtype=float)
        middles = np.array([head['cy'] for head in heads], dtype=float)
        near = [shade for place, shade in zip(found, shades) if shade is not None
                and np.any((rights < place[0]) & (place[0] <= rights + DOT_REACH * space + 2)
                           & (middles - 0.7 * space <= place[1]) & (place[1] <= middles + DOT_UNDER * space))]
        others = [shade for shade in near if shade > DOT_GREY[0]]
        page = bool(others) and 2 * sum(shade >= DOT_GREY_PAGE for shade in others) >= len(others)
        if DOT_GREY_SEEN is not None:
            DOT_GREY_SEEN.append({'near': near, 'page': page})
        if page:
            grey = {number for number, shade in enumerate(shades) if shade is not None and shade <= DOT_GREY[0]}
    specks = []
    for index in range(1, count if DOT_SPECK else 1):
        # (see DOT_SPECK: the shape of a dot, a little smaller)
        x, y, wide, high, area = stats[index]
        if not (DOT_SPECK[0] * space <= min(wide, high) and min(wide, high) < DOT_SMALL * space
                and wide <= 0.6 * space and high <= DOT_HIGH * space):
            continue
        if area < DOT_FILL * wide * high or not DOT_SLIM <= wide / high <= DOT_FLAT:
            continue
        if DOT_TIP and _bow_tip(layers, int(x), int(y), int(wide), int(high), labels, stats):
            continue
        specks.append((float(centres[index][0]), float(centres[index][1])))
    nearly = []
    for index in range(1, count if DOT_ASK else 1):
        x, y, wide, high, area = stats[index]
        if DOT_SMALL * space <= wide <= DOT_ASK[0] * space and DOT_SMALL * space <= high <= DOT_HIGH * space \
                and area >= DOT_ASK[1] * wide * high:
            nearly.append((float(centres[index][0]), float(centres[index][1])))
    dashes = [place for place in nearly if place not in found]
    usual = (layers.get('head') or (0, 0))[0]

    def edge(head: dict, x: float, y: float) -> float:
        # The right edge of a head for a dot at (x, y): see DOT_BODY.
        if not (DOT_BODY and usual and abs(head['place']) > 4.6 and head['x1'] - head['x0'] + 1 >= DOT_BODY * usual
                and head['y0'] <= y <= head['y1']):
            return head['x1']
        row = layers['bare'][max(0, int(y) - 1):int(y) + 2, head['x0']:max(head['x0'], int(x - 0.2 * space))].any(axis=0)
        inked = np.nonzero(row)[0]
        return float(head['x0'] + inked[-1]) if len(inked) else head['x1']

    taken = set()
    first = {}
    takers, took = {}, {}
    darks = {}

    def refused(number: int, head: dict) -> bool:
        # A grey piece is no dot of a black head (see DOT_GREY).
        if number not in grey:
            return False
        if id(head) not in darks:
            darks[id(head)] = _box_black(layers, head) >= DOT_GREY[2]
        return darks[id(head)]

    for head in heads:
        head['dot'] = False
        head['dot_sure'] = False
        head['dot_near'] = any(DOT_NEAR * space <= x - head['x1'] <= DOT_REACH * space
                               and -DOT_ASK[2] * space <= y - head['cy'] <= DOT_UNDER * space for x, y in nearly)
        for number, (x, y) in enumerate(found):
            if DOT_NEAR * space <= x - edge(head, x, y) <= DOT_REACH * space and -0.7 * space <= y - head['cy'] <= DOT_UNDER * space \
                    and not (DOT_BETWEEN and DOT_BETWEEN[0] * space <= y - head['cy'] < DOT_BETWEEN[1] * space) \
                    and not refused(number, head):
                head['dot'] = True
                if DOT_SURE and sizes[number][3] >= DOT_SURE[0] * space * space \
                        and DOT_SURE[1] <= sizes[number][1] / sizes[number][2] <= DOT_SURE[2] \
                        and min(abs(y - row) for row in layers['staves'][head['staff']]['rows']) >= DOT_SURE[3] * space:
                    head['dot_sure'] = True
                taken.add(number)
                if number in haired and DOT_LINE_SEEN is not None:
                    DOT_LINE_SEEN.append({'head': (head['cx'], head['cy'], head['x1'], head['staff']), 'dot': found[number], 'size': sizes[number]})
                takers.setdefault(number, []).append(head)
                took.setdefault(id(head), []).append(number)
                if id(head) not in first or x < found[first[id(head)]][0]:
                    first[id(head)] = number
    for number, group in takers.items() if DOT_UPPER else []:
        # One dot between two heads of a column is the dot of the lower one (see DOT_UPPER).
        y = found[number][1]
        for head in group:
            if y - head['cy'] < DOT_UPPER * space or any(found[other][1] - head['cy'] < DOT_UPPER * space for other in took[id(head)]):
                continue
            below = [other for other in group if other is not head and other['cy'] - y >= DOT_UPPER * space]
            kind = (bool(head.get('hollow')), max(head['tails'].values(), default=0))
            if below and not any((bool(other.get('hollow')), max(other['tails'].values(), default=0)) == kind for other in below):
                head['dot'] = head['dot_sure'] = False
                first.pop(id(head), None)
    if DOT_BESIDE:
        # One head of a column has its dot, and a dash stands beside another head of the column (see DOT_BESIDE).
        level, reach, side, high = DOT_BESIDE
        dotted = [head for head in heads if id(head) in first]
        kind = lambda head: (bool(head.get('hollow')), max(head['tails'].values(), default=0))
        for head in heads:
            if head['dot']:
                continue
            for x, y in dashes:
                if not (DOT_NEAR * space <= x - head['x1'] <= DOT_REACH * space and abs(y - head['cy']) <= high * space):
                    continue
                if any(abs(other['x1'] - head['x1']) <= level * space and abs(other['cy'] - head['cy']) <= reach * space
                       and abs(other.get('staff', 0) - head.get('staff', 0)) <= 1 and kind(other) == kind(head)
                       and abs(found[first[id(other)]][0] - x) <= side * space for other in dotted):
                    head['dot'] = True
                    break
    if DOT_SPECK and specks:
        # A dot that the print wore small, in the line of another head's dot of the column (see DOT_SPECK).
        level, reach = DOT_BESIDE[0], DOT_BESIDE[1]
        dotted = [head for head in heads if id(head) in first]
        kind = lambda head: (bool(head.get('hollow')), max(head['tails'].values(), default=0))
        used = set()
        for head in heads:
            if head['dot']:
                continue
            for number, (x, y) in enumerate(specks):
                if number in used or not (DOT_NEAR * space <= x - head['x1'] <= DOT_REACH * space
                                          and -0.7 * space <= y - head['cy'] <= DOT_UNDER * space):
                    continue
                if any(abs(other['x1'] - head['x1']) <= level * space and abs(other['cy'] - head['cy']) <= reach * space
                       and abs(other.get('staff', 0) - head.get('staff', 0)) <= 1 and kind(other) == kind(head)
                       and abs(found[first[id(other)]][0] - x) <= DOT_SPECK[1] * space for other in dotted):
                    head['dot'] = True
                    used.add(number)
                    if CENSUS is not None:
                        CENSUS.append({'head': (head['cx'], head['cy']), 'speck': (x, y)})
                    break
    for head in heads if DOT_TWO else []:
        # A second dot at the right of the first (see DOT_TWO).
        if id(head) not in first:
            continue
        near, far, level, alike, slim, flat, colon = DOT_TWO
        one = first[id(head)]
        x, y = found[one]
        for number, (other, row) in enumerate(found):
            if number in haired or refused(number, head) or not (near * space <= other - x <= far * space and abs(row - y) <= level * space):
                continue        # (a dot that keeps a hair of a line is only the first dot of its head: DOT_LINE)
            if min(sizes[one][3], sizes[number][3]) < alike * max(sizes[one][3], sizes[number][3]) \
                    or not all(slim <= sizes[index][1] / sizes[index][2] <= flat for index in (one, number)):
                continue
            if any(index != number and abs(column - other) <= 0.3 * space and 0.5 * space <= abs(line - row) <= colon * space
                   for index, (column, line) in enumerate(found)):
                continue        # the two dots of a repeat sign stand one over the other
            left, right = sizes[one][0] + sizes[one][1] + 1, sizes[number][0] - 1
            top, bottom = int(min(y, row) - 0.15 * space), int(max(y, row) + 0.15 * space) + 1
            if right > left and layers['bare'][max(0, top):bottom, left:right].any():
                continue        # paper stands between the two dots
            head['dots'] = 2
            taken.add(number)
            break
    for head in heads:
        # A tight engraving sets the dot against the head. One dot is the dot of one head.
        if DOT_CLOSE and not head['dot']:
            head['dot'] = any(full[number] and number not in taken and DOT_CLOSE[0] * space <= x - head['x1'] < DOT_NEAR * space
                              and -0.7 * space <= y - head['cy'] <= DOT_UNDER * space and not refused(number, head)
                              for number, (x, y) in enumerate(found))
        if not head['dot'] and LEDGER_DOT and abs(head['place']) > 4.6:
            # A hand draws the ledger line through the head and on to the right, and sets the dot at its end or
            # past its end.
            end, blob = _ledger_end(layers, head)
            if end >= head['x1'] + LEDGER_DOT[2] * space:
                head['dot'] = blob or any(0.1 * space <= x - end <= LEDGER_DOT[1] * space and number not in haired and not refused(number, head)
                                          and abs(y - head['cy']) <= 0.7 * space for number, (x, y) in enumerate(found))
    if DOT_JOIN:
        level, reach = DOT_BESIDE[0], DOT_BESIDE[1]
        dotted, blots = [head for head in heads if id(head) in first and head['dot']], []
        for head in heads:
            if head['dot']:
                continue
            partners = [other for other in dotted if other is not head and other.get('staff') == head.get('staff')
                        and abs(other['x1'] - head['x1']) <= level * space and abs(other['cy'] - head['cy']) <= reach * space]
            if partners:
                other = min(partners, key=lambda o: abs(o['cy'] - head['cy']))
                blot = _dot_joined(layers, head, found[first[id(other)]], sizes[first[id(other)]])
                # one blot is the dot of one head
                if blot and not any(abs(blot[0] - x) + abs(blot[1] - y) < 0.3 * space for x, y in blots):
                    head['dot'] = True
                    blots.append(blot)


def _dot_joined(layers: dict, head: dict, place: tuple, size: tuple) -> tuple | None:
    """(DOT_JOIN) The middle of a blot of the size of the dot at place (x, y) with size (left, wide, high, area), at
    that dot's column, in the rows of a dot of head, inside a larger piece of ink; None where there is none."""
    bare, space = layers['bare'], layers['space']
    near, share, low, high, apart, joined = DOT_JOIN
    dx, _ = place
    _, wide, tall, area = size
    x0, y0 = max(0, int(dx - 0.35 * space)), max(0, int(head['cy'] - 0.6 * space))
    window = bare[y0:int(head['cy'] + 0.25 * space) + 1, x0:int(dx + 0.35 * space) + 1].astype(np.uint8)
    if not window.any():
        return None
    side = max(3, int(round(share * min(wide, tall))) | 1)
    core = cv2.morphologyEx(np.pad(window, side), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (side, side)))[side:-side, side:-side]
    count, _, stats, centres = cv2.connectedComponentsWithStats(core, connectivity=8)
    if count < 2:
        return None
    best = max(range(1, count), key=lambda index: stats[index][4])
    bw, bh, ba = (int(value) for value in stats[best][2:5])
    cx, cy = x0 + float(centres[best][0]), y0 + float(centres[best][1])
    if not (abs(cx - dx) <= near * space and low <= ba / area <= high and low <= bw / wide <= high and low <= bh / tall <= high):
        return None
    step = round(head['place'])
    rows = [head['cy']] if step % 2 == 0 else [head['cy'] - 0.5 * space, head['cy'] + 0.5 * space]
    if min(abs(cy - row) for row in rows) < apart * space:
        return None
    # the piece of ink that holds the blot, in a window two staff spaces around it
    reach = int(2 * space)
    lx, ly = int(round(cx)), int(round(cy))
    ya, xa = max(0, ly - reach), max(0, lx - reach)
    _, labels, pieces, _ = cv2.connectedComponentsWithStats(bare[ya:ly + reach, xa:lx + reach].astype(np.uint8), connectivity=8)
    label = labels[ly - ya, lx - xa]
    if not label or pieces[label][4] <= joined * area:
        return None
    if DOT_JOIN_SEEN is not None:
        DOT_JOIN_SEEN.append({'head': (head['cx'], head['cy'], head['x1'], head.get('staff'), round(head['place'], 1)),
                              'blot': (cx, cy, bw, bh, ba), 'dot': (dx, wide, tall, area), 'piece': [int(v) for v in pieces[label]],
                              'space': space})
    return (cx, cy) if min(bw / bh, bh / bw, wide / tall, tall / wide) >= DOT_JOIN_ROUND else None


def _ledger_end(layers: dict, head: dict) -> tuple[int, bool]:
    """Where the ledger line of a head ends at its right: (the column, True when the line ends in a blob as large
    as a dot). The line is level ink, thin as a line, that leaves the head; the head's own right edge when no such
    line leaves it."""
    bare, space = layers['bare'], layers['space']
    half = int(0.5 * space)
    top, bottom = max(0, int(head['cy']) - half), min(bare.shape[0], int(head['cy']) + half + 1)
    last = min(bare.shape[1], head['x1'] + 1 + int(LEDGER_DOT[0] * space))
    heights = bare[top:bottom, head['x1'] + 1:last].sum(axis=0)
    thin = 0.25 * space + 2      # a ledger line is at most this thick
    step = 0
    while step < len(heights) and 0 < heights[step] <= thin:
        step += 1
    end = head['x1'] + step
    wide = 0
    while step + wide < len(heights) and thin < heights[step + wide] <= DOT_HIGH * space:
        wide += 1
    # The blob is round: its last columns are as low as the line again, and then the paper begins.
    after = step + wide
    while after < len(heights) and 0 < heights[after] <= thin and after - step - wide < 0.2 * space:
        after += 1
    blob = 0.14 * space <= wide <= 0.7 * space and after < len(heights) and heights[after] == 0
    if blob:
        far, left = int(LEDGER_DOT[3] * space), head['x1'] + 1 + step
        rows = [row for row in (int(head['cy']) - far, int(head['cy']) + far) if 0 <= row < bare.shape[0]]
        blob = not bare[rows, left:left + wide].any()
    return end, bool(blob)


def bar_marks(layers: dict, heads: list[dict]) -> list[dict]:
    """The marks that are no heads but the place where a tie crosses a bar line: the tie, the bar line and a staff
    line close in a little paper, which was read as a low hollow head with the bar line as its stem. The line goes
    through the staff from its top line to its bottom line and goes on above the mark and below it (a stem ends at its
    head), and the mark is lower than a head. A low hollow mark with no stem is asked for a line at its side
    (BAR_SIDE)."""
    if not BAR_MARK:
        return []
    ink, high, out = layers['ink'], layers['head'][1], []
    for mark in heads:
        if BAR_SIDE and mark['hollow'] and not mark.get('thin') and not mark['stems'] \
                and mark['y1'] - mark['y0'] + 1 <= BAR_MARK[0] * high:
            if _bar_side(layers, mark):
                out.append(mark)
            continue
        if not mark['hollow'] or mark.get('thin') or len(mark['stems']) != 1 \
                or mark['y1'] - mark['y0'] + 1 > BAR_MARK[0] * high:
            continue
        staff = layers['staves'][mark['staff']]
        top, bottom = int(staff['rows'][0]), int(staff['rows'][4])
        x = int(round(mark['stems'][0]['x']))
        if not top <= mark['cy'] <= bottom or x < 1 or ink[top:bottom + 1, x - 1:x + 2].any(axis=1).mean() < BAR_MARK[1]:
            continue
        column = ink[:, x - 1:x + 2].any(axis=1)
        for head in heads:      # the head of the other voice, a third away on the same line of stems, is no bar line
            if head is not mark and head['staff'] == mark['staff'] and head['x0'] - 1 <= x <= head['x1'] + 1:
                column[max(0, int(head['y0'])):int(head['y1']) + 1] = False
        reach = max(1, int(round(BAR_MARK[2] * staff['space'])))
        over = column[max(0, int(mark['y0']) - reach):int(mark['y0'])]
        under = column[int(mark['y1']) + 1:int(mark['y1']) + 1 + reach]
        if not len(over) or not len(under) or min(over.mean(), under.mean()) < BAR_MARK[3]:
            if not (BAR_END and _bar_end(layers, mark, column, staff, top, bottom, reach)):
                continue
        out.append(mark)
    return out


BAR_END = (2, 0.2)   # and such a mark is no head either at an end of a bar line, where a slur that crosses the line meets
#   the staff's outer line: the mark touches that line (its edge within half the line's thickness and the first number of
#   px), the column of its stem has no ink beyond that line (at most the second share of the rows over half a staff space
#   past it), fills the staff from the mark to the other outer line (BAR_MARK's second share) and ends there as the
#   staff does (within the same px, and at most the second share past it). A stem ends at its head, not at a staff
#   line: a head in the first space with a stem of three and a half staff spaces reaches the far line too, but it is as
#   high as a head (BAR_MARK's first share). A census of every low hollow mark whose stem fills the staff and that
#   BAR_MARK leaves because the line stops at one side (12 on LitChoir's scan pages and 3 on the fresh set, each looked
#   at): the true notes (the upper or lower head of a chord, a half note on the bottom line) stand off the outer line or
#   their stem leaves the staff, and the rule takes the slur at a bar line of two scans of one hymn and, on the fresh
#   set, a slur that meets a bar line at the bottom line. (None: off)


def _bar_end(layers: dict, mark: dict, column: np.ndarray, staff: dict, top: int, bottom: int, reach: int) -> bool:
    """Whether a low hollow mark with one stem sits at an end of a bar line (BAR_END): at the top line with the line
    going down to the bottom line and ending there, or the other way round."""
    half = staff['thick'] / 2 + BAR_END[0]
    def share(lo: float, hi: float) -> float:
        part = column[max(0, int(round(lo))):max(0, int(round(hi)))]
        return float(part.mean()) if len(part) else 0.0
    if mark['y0'] <= top + half:            # at the top line, the line going down
        return share(top - half - reach, top - half) <= BAR_END[1] \
            and share(mark['y1'] + 1, bottom + 1) >= BAR_MARK[1] \
            and share(bottom + half + 1, bottom + half + 1 + reach) <= BAR_END[1]
    if mark['y1'] >= bottom - half:         # at the bottom line, the line going up
        return share(bottom + half + 1, bottom + half + 1 + reach) <= BAR_END[1] \
            and share(top, mark['y0']) >= BAR_MARK[1] \
            and share(top - half - reach, top - half) <= BAR_END[1]
    return False


BAR_SIDE = (0.3, 0.2)   # a low hollow mark with no stem is no head either at an end of an upright line beside it, at a
#   column within the first number of staff spaces outside the mark's box or the second inside it: the mark touches an
#   outer line of the staff, the column has no ink beyond that line and fills the staff from the mark to the other outer
#   line (BAR_END's measures). The paper that a slur closes with an outer line where it crosses a bar line has no stem
#   where the line stands just past its box, and a bar line through a system goes on past the far line, so the line is
#   not asked to end there as a stem is. A true whole note at an outer line is as high as a head (BAR_MARK's first
#   share). A census of every low hollow mark with no stem at the rule's own step, on every page of LitChoir and of the
#   fresh set: one on LitChoir (a slur over a bar line at the top line, read as a whole note: a rule for one case), and
#   on the fresh set four cells that a tie closes with an outer line beside a stem through the staff, each read as a
#   whole note. (None: off)


def _bar_side(layers: dict, mark: dict) -> bool:
    """Whether a low hollow mark with no stem sits at an end of an upright line at its side (BAR_SIDE)."""
    if not BAR_END:
        return False
    ink, staff = layers['ink'], layers['staves'][mark['staff']]
    space = staff['space']
    top, bottom = int(staff['rows'][0]), int(staff['rows'][4])
    half = staff['thick'] / 2 + BAR_END[0]
    reach = max(1, int(round(BAR_MARK[2] * space)))
    at_top, at_bottom = mark['y0'] <= top + half, mark['y1'] >= bottom - half
    out, inside = int(round(BAR_SIDE[0] * space)), int(round(BAR_SIDE[1] * space))
    best = None
    if at_top or at_bottom:
        x0, x1 = int(mark['x0']), int(mark['x1'])
        for x in list(range(x0 - out, x0 + inside + 1)) + list(range(x1 - inside, x1 + out + 1)):
            if x < 1 or x + 2 > ink.shape[1]:
                continue
            column = ink[:, x - 1:x + 2].any(axis=1)
            def share(lo: float, hi: float) -> float:
                part = column[max(0, int(round(lo))):max(0, int(round(hi)))]
                return float(part.mean()) if len(part) else 0.0
            if at_top:      # the slur at the top line, the line going down
                fill, past = share(mark['y1'] + 1, bottom + 1), share(top - half - reach, top - half)
            else:           # at the bottom line, the line going up
                fill, past = share(top, mark['y0']), share(bottom + half + 1, bottom + half + 1 + reach)
            if best is None or (fill, -past) > (best[0], -best[1]):
                best = (fill, past, x)
    found = best is not None and best[0] >= BAR_MARK[1] and best[1] <= BAR_END[1]
    if CENSUS is not None:
        CENSUS.append({'rule': 'SIDE', 'box': [mark['x0'], mark['y0'], mark['x1'], mark['y1']], 'staff': mark['staff'],
                       'best': best, 'found': bool(found)})
    return bool(found)


BAR_FAINT = (0.38, 0.55, 0.02, 0.6, 0.3)   # a bar line of a faint print, broken into dashes: an upright line with ink
#   in this share of the rows of the staff (three columns together), with at most this share of ink at each side of it
#   over a third of a staff space (a stem has its head there), and on the other staves of its system a bar line or such
#   a line at most this many staff spaces away; one of the two lines has the second share. And it goes on toward the
#   next staff of its system, with ink in the last share of the rows from 1 to 4 staff spaces past the staff: the
#   crease of a page and a dotted guide line stay in the staff or cross the whole page (None: off)


def faint_bars(layers: dict, heads: list[dict], bars: dict[int, list[float]]) -> dict[int, list[float]]:
    """The bar lines that bar_lines() did not read because the print is faint (staff index: the x of each). A sign
    holds up to the next bar line, so a sharp is carried too far where a bar line is lost."""
    from .starts import _free
    out = {index: [] for index in bars}
    if not BAR_FAINT:
        return out
    staves, space = layers['staves'], layers['space']
    wide = cv2.dilate(np.ascontiguousarray(layers['ink']), np.ones((1, 3), np.uint8))
    free = _free(layers)
    side, reach = max(3, int(0.35 * space)), max(2, int(0.3 * space))
    lines = {}
    for index, staff in enumerate(staves):
        top, bottom = int(staff['rows'][0]), int(staff['rows'][4])
        share = wide[top:bottom + 1].mean(axis=0)
        stems = [stem['x'] for head in heads if head['staff'] == index for stem in head['stems']]
        found = []
        for column in np.nonzero(share >= BAR_FAINT[0])[0]:
            column = int(column)
            if not staff['x0'] + 2 * space < column < min(staff['x1'] - space, share.size - side - 5):
                continue
            if share[column] < share[column - reach:column + reach + 1].max() or (found and column - found[-1][0] <= reach):
                continue
            if free[top:bottom + 1, column - 3 - side:column - 3].mean() > BAR_FAINT[2] \
                    or free[top:bottom + 1, column + 4:column + 4 + side].mean() > BAR_FAINT[2]:
                continue
            if any(abs(column - x) <= 0.4 * space for x in stems) or any(
                    head['staff'] == index and head['x0'] - 0.2 * space <= column <= head['x1'] + 0.2 * space for head in heads):
                continue
            numbers = [mate['number'] for mate in staves if mate['system'] == staff['system']]
            spans = []
            if staff['number'] > min(numbers):
                spans.append((max(0, top - int(4 * space)), top - int(space)))
            if staff['number'] < max(numbers):
                spans.append((bottom + int(space), bottom + int(4 * space)))
            if not any(last > first and layers['ink'][first:last, column - 2:column + 3].any(axis=1).mean() >= BAR_FAINT[4]
                       for first, last in spans):
                continue
            found.append((column, float(share[column])))
        lines[index] = found
    for index, staff in enumerate(staves):
        mates = [other for other, mate in enumerate(staves) if other != index and mate['system'] == staff['system']]
        for column, share in lines[index]:
            if not mates or any(abs(column - x) < 0.9 * space for x in bars[index]):
                continue
            agree = 0
            for other in mates:
                if any(abs(column - x) <= BAR_FAINT[3] * space for x in bars[other]) or any(
                        abs(column - x) <= BAR_FAINT[3] * space and max(share, its) >= BAR_FAINT[1] for x, its in lines[other]):
                    agree += 1
            if 2 * agree >= len(mates):
                out[index].append(float(column))
    return out


def bar_lines(layers: dict, heads: list[dict]) -> dict[int, list[float]]:
    """The bar lines of each staff (staff index: the x of each): bare upright lines from the top line to the bottom
    line. A stem can cross the whole staff too, but a head hangs on it."""
    from .starts import bare_lines
    space = layers['space']
    out = {}
    for index, staff in enumerate(layers['staves']):
        merged = []
        for x, _, _ in bare_lines(layers, staff, staff['x0'] - space, staff['x1'] + space):
            if merged and x - merged[-1] < 0.9 * space:
                merged[-1] = (merged[-1] + x) / 2
            else:
                merged.append(x)
        out[index] = merged
    return out


BAR_STEM = (0.2, 0.6, 0.5, 1.1, 0.5, 0.95)   # a bar line that is the stem of a half note: the inside of a head (this many
# staff spaces squared, wide and high) beside it ...
BAR_STEM_AT = (1.0, 0.5, 2, 0.85)   # ... within this many staff spaces of the outer line at its end and of the line,
# the line stopping this many rows of paper short of the other outer line, and filling this share of the staff
BAR_STEM_SEEN = None   # census: (staff, x, the inside's middle, the way of the stem)


def bar_stems(layers: dict, bars: dict[int, list[float]], ends: list[float]) -> dict[int, list[float]]:
    """The bar lines that are the stem of a half note (BAR_STEM; staff index: the x of each). A head in the space at the
    top line with its stem down, or in the space at the bottom line with its stem up, has a stem that crosses the
    staff to the other outer line, and a bare line from line to line was read there as a bar line. The open hole of
    the head was then refused, because its stem was a bar line. A bar line ends at the other outer line; a stem stops
    short of it, and the inside of its head stands at its side: at the right of a stem down near the top line, at the
    left of a stem up near the bottom line (two half notes of extra-come-bless, each looked at; the census of every bar
    line of LitChoir's pages and of the fresh set found no other)."""
    if not BAR_STEM:
        return {}
    ink = layers['ink']
    paper = ((layers['holes'] > 0) | (layers['open_holes'] > 0)).astype(np.uint8)
    count, labels, stats, cents = cv2.connectedComponentsWithStats(paper, connectivity=4)
    space = layers['space']
    insides = [n for n in range(1, count) if 0.1 * space * space <= stats[n][4] <= space * space]
    out = {}
    for index, staff in enumerate(layers['staves']):
        top, bottom = staff['rows'][0], staff['rows'][4]
        sp, thick = staff['space'], staff['thick']
        for x in bars.get(index, []):
            if x <= ends[index] + 0.3 * sp:
                continue
            xi = int(round(x))
            column = ink[int(top):int(bottom) + 1, max(0, xi - 2):xi + 3].any(axis=1)
            if column.mean() < BAR_STEM_AT[3]:
                continue
            narrow = ink[:, max(0, xi - 1):xi + 2].any(axis=1)
            def run(start, step):
                k, y = 0, start
                while 0 <= y < len(narrow) and not narrow[y] and k < int(sp):
                    k += 1
                    y += step
                return k
            gap_top = run(int(np.ceil(top + thick / 2 + 0.5)), 1)
            gap_bottom = run(int(np.floor(bottom - thick / 2 - 0.5)), -1)
            for n in insides:
                bx, by, bw, bh, area = (int(v) for v in stats[n])
                if not (BAR_STEM[0] * sp * sp <= area <= BAR_STEM[1] * sp * sp and BAR_STEM[2] * sp <= bw <= BAR_STEM[3] * sp
                        and BAR_STEM[4] * sp <= bh <= BAR_STEM[5] * sp):
                    continue
                cy = float(cents[n][1])
                if bx > xi:
                    way = 'down' if bx - xi <= BAR_STEM_AT[1] * sp and abs(cy - top) <= BAR_STEM_AT[0] * sp \
                        and gap_bottom >= BAR_STEM_AT[2] else None
                elif bx + bw - 1 < xi:
                    way = 'up' if xi - (bx + bw - 1) <= BAR_STEM_AT[1] * sp and abs(bottom - cy) <= BAR_STEM_AT[0] * sp \
                        and gap_top >= BAR_STEM_AT[2] else None
                else:
                    way = None
                if way is None:
                    continue
                out.setdefault(index, []).append(x)
                if BAR_STEM_SEEN is not None:
                    BAR_STEM_SEEN.append((index, x, (round(float(cents[n][0]), 1), round(cy, 1)), way))
                break
    return out

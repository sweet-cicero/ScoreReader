"""Reads the ties: an arc from one head to the next head of the same pitch. No model is used.

A tie is a thin bow. It begins close beside its first head and ends close before its second head, at their height,
and between them it leaves the straight way to one side only. It is followed column by column on the ink without
the staff lines; where it lies in a staff line it cannot be seen, and it is taken to go on there.

A slur looks the same. Between two heads of one pitch with no other note of their voice between them, a slur is a
tie. A slur over more notes passes its inner notes at a distance and ends farther on: it is no tie.
"""
from __future__ import annotations

import cv2
import numpy as np

TIE_FAR = 40.0          # the two heads of a tie stand at most this many staff spaces apart (0: ties are not read)
TIE_LEAST = 1.3         # and at least this many, from edge to edge: the bow needs room
TIE_THIN = 0.4          # the bow is at most this thick, in staff spaces
TIE_BOLD = 0            # 0.65: a print with bold bows: where no bow of thin ink is found, a bow up to this thick counts.
#                         Off: alone it gained 12 notes on all of LitChoir and lost 10 (1 and 0 on the clean copies); the
#                         bold bows of the print that it was written for are found without it.
TIE_SWELL = (0.65, 0.6, 4.0)   # a bow that swells in its middle (None: off): where the thin ink of a way shows in the second
#                         share of its columns or more and still leaves too many columns open, the way is followed again
#                         with ink up to the first number of staff spaces thick. An engraved bow is thin at its ends and
#                         fat in its middle; a bow that is bold from end to end is not taken (see TIE_BOLD). The way is
#                         the third number of staff spaces long or more: a short bow of a print is thin, and a short
#                         fat stroke between two heads of a copy by hand is the end of a slur, an accent or the bow
#                         under a syllable (of 15 such ways on LitChoir's pages the 6 false ones were at most 3.3
#                         long, and 7 of the 9 true ones 4.4 or more).
TIE_SIDE = 0.9          # it begins and ends at most this many staff spaces from the heads, sideways
TIE_HIGH = 1.4          # and at most this many staff spaces over or under their middle
TIE_GAP = 0.5           # it may break for this many staff spaces
TIE_EDGE = 0.2          # a bow that runs along another stroke (a tie over a slur that touches it): where the thin ink in its
#                         column is thicker by at least this many staff spaces than the bow was in its last column alone,
#                         and the bow comes in at one edge of it, the bow keeps to that edge, as thick as it was alone (a
#                         bow that swells grows by a pixel at a time). Not where a staff line runs in the rows of the band
#                         within half a staff space: a bow that runs into a line goes on in it. Six ties on LitChoir's pages,
#                         none on the fresh set; one of them ends at a false head that the bow and a bar line make
#                         (blessed-be-bortniansky--s2). None: off: the way follows the middle of the band, and the bow is
#                         flattened
TIE_SEEN = (0.6, 0.9)   # its ink shows in this share of the columns; its ink or a staff line that hides it in this share
TIE_BOW = (0.2, 3.5)    # the bow is at least and at most this many staff spaces high
TIE_FLAT = (0.15, 0.9, 0.6)   # a short tie between two heads that stand close hides its ends under the heads, and what
#                         shows of it is flatter: a way whose ink shows in this share of its columns or more is a bow from
#                         this height on, if it begins and ends this many staff spaces or more over or under the middles
#                         of the heads (two ledger lines that touch run on at the height of the heads) (None: off)
TIE_APART = (1.0, 0.15, 0.7, 0.4, 0.25)   # a short bow that stands free between its two heads (None: off): its ink shows
#                         without a break for this many staff spaces or more, then paper shows for this many or more,
#                         and the way goes on for at most this many in the ink at the second head (the end of its
#                         ledger line). The bow stands in the middle: the paper before it and the paper after it differ
#                         by at most this many staff spaces. The two heads stand at one height on the page, at
#                         most this many staff spaces apart: such a bow between two heads a step apart is a slur,
#                         and one of the heads can be read a step off.
TIE_RIM = 'even'        # thin ink is the ink without its thick blobs. The opening that finds the blobs lies one pixel
#                         low where the limit is an even number of pixels, and the top row of every blob is then left
#                         over as thin ink: a bold bow is followed along its upper edge. 'even': on those pages, as it
#                         always was; 'all': on every page; None: on no page. The flat bow of TIE_FLAT is followed on
#                         the thin ink without any such row: the upper edge of a head is a flat bow too
TIE_EVEN = 1.0          # its highest place lies in the middle part: the two ends differ by at most this many bow heights
TIE_SMOOTH = 0.35       # and it leaves the curve of a bow by at most this share of its height
TIE_PARTNER = (0.5, 1.8)  # a whole note has the voice that the note in its column has not: a note with a stem at most
#                         this many staff spaces from it along the staff, or beside it (at most a second away) at most
#                         this many (None: a whole note has no voice)
TIE_COLUMN = 1.0        # a chord is tied note by note: a head in the column of the second head (their middles at most
#                         this many staff spaces apart) and of its voice is not between the two heads of a tie (0: off)
TIE_SHARED = True       # ... and so does a head there that two voices share (a stem up and a stem down), beside a head of
#                         one of them (False: off)
TIE_BOTH = 0.5          # a head that two voices share (a stem up and a stem down) is tied twice, with a bow over and a
#                         bow under: the second bow ends at the other voice's head of the same place, which stands
#                         beside the first bow's second head, at most this many staff spaces from it (0: off)
TIE_UNDER = True        # a bow that runs into a staff line and comes out at its other side: while no ink shows, the staff
#                         line within the reach of the search hides it, not only the line at the bow's last row
TIE_DIP = (0.3, 0.1, 2.8, 0.15)   # a bow that lies in a staff line for a long part (None: off): its ink shows in this share
#                         of its columns or more, under TIE_SEEN, and over the longest part where it does not show, the
#                         curve through the ink that shows lies at most this many staff spaces from the staff line. A bow
#                         dips into the line and comes out of it; other ink at two heads does not point at the line.
#                         Only a bow of this many staff spaces or longer: between two near heads a number of the time
#                         signature, a flat or a stroke of the hand shows as much ink beside a line. And its ink shows
#                         over this many staff spaces or more at each side of that part: the bow comes out of the line.
TIE_ENDS = (0.5, 0.3, 0.45, 3.0, 0.9)   # a bow that begins and ends inside a staff line (None: off): its ink shows only
#                         in its middle, from the first to the last stretch of ink of the second number of staff spaces
#                         or longer, which begins and ends at least the first number of staff spaces from the heads,
#                         takes the third share of the room between the heads or more and the fourth number of staff
#                         spaces or more, and shows in the last share of its columns. Before and after the middle the
#                         lines hide the bow (the way holds as little paper as TIE_SEEN allows), and after it the line
#                         goes on to the second head. TIE_SEEN wants the ink in 60 % of the columns, and TIE_TO_LINE
#                         lets the line hide 1.5 staff spaces before the second head: in pascha-angel-cried--s2 the
#                         lines hide 39 % of one such tie, and the other runs into the line 2.4 staff spaces before its
#                         head. A census of every pair of heads on LitChoir's scan pages whose way is turned down
#                         although a stretch of its ink shows at least half a staff space from each head (363 pairs): 7
#                         have such a middle, 5 of them bows and all ties (3 tied already by another way) and 2 flat
#                         ties that one print breaks at its bar line, which are no bow; every other pair takes 0.43 of
#                         the room at most (0.35 where its middle is longer than 1.3 staff spaces), or shows its ink in
#                         0.85 of its middle or less (a line in pencil from a head to the next chord).
TIE_FROM_LINE = True    # a bow may begin in a staff line beside its head: it is followed from the line (False: off)
TIE_TO_LINE = (1.5, 3.5)   # a bow may end in a staff line beside its head too: where its ink runs into a line and the line
#                         goes on to the head, the bow's last ink may lie this many staff spaces before the head, and the
#                         way that was followed is this many times as long as the part that the line hides: a short
#                         stroke beside a head that ends in a line is no bow (None: off)
TIE_BAR = (1.6, 1.0, 0.35, 0.95, 0.4, 1.7)   # a tie over a bar line that the print ends at the bar line (None: off): an
#                         upright line that fills the staff from its top line to its bottom line (in the fourth share of
#                         those rows or more), at no stem (the last number of staff spaces from each), stands at most the
#                         first number of staff spaces before the second head and at least the second number after the
#                         first head; the way is cut at the bar line, its ink reaches to within the third number of staff
#                         spaces of it, and the part before the bar line is a bow that ends at most the last number of staff
#                         spaces over or under the second head's middle (TIE_BAR_SEEN: a census)
TIE_BAR_SEEN = None
TIE_BAR_PAST = (0.4, 1.0, 0.35, 0.2, 0.15, 0.25)   # the bow of TIE_BAR goes on past the bar line in no column (None: off):
#                         in the columns from the first to the second number of staff spaces past the bar line's right
#                         edge (and the fifth number before the second head), in the rows the third number around the
#                         row where the bow meets the bar line, without the fourth number around each staff line, ink
#                         stands in less than the last share of the columns. One print ends its ties at the bar line
#                         (communion-lords-prayer: 0.0); the slurs that an engraving draws between two notes of one
#                         pitch over a bar line go on to the second head (1.0), and the hymn sings them as two notes.
#                         A bow that goes on in the rows of a staff line is not seen.
TIE_ROUND = True        # a head between the two heads is of another voice by its place on the staff, not by where its ink lies
TIE_LINE = (0.4, 0.07, 0.2, 2.0, 0.7, 1.6)   # a flat tie that lies in a staff line (None: off): the line is fatter in a
#                         run of columns that is this share of the way between the two heads; fatter by this many
#                         staff spaces; at most this share of the columns is crossed by a stem or a bar line; the
#                         run is this many staff spaces long or more; this share of its columns is fat; the line lies
#                         at most this many staff spaces from the middle of the heads
TIE_BESIDE = 2.0         # (TIE_LINE) and the lens is fatter than the same line beside the two heads (this many staff
#                          spaces at each side, the fatter side) by as much as it must be fatter than the staff's lines:
#                          a scan that prints one line thick all along has no lens. Of the 33 flat ties of LitChoir's
#                          pages, the 8 where no bow is printed are no fatter than the line beside them, and the others 3
#                          to 9 pixels fatter; the fresh set's 5 are 3 or 4 (None: off)
TIE_WORD = (5, 0.5, 6.5, 2.0, 0.3, 0.7, 0.45, 0.4)   # a page whose bows join the syllables of a word (None: off). A tied note
#                         takes no syllable. Where at least [0] ties of a page end over the beginning of a syllable (the
#                         ties of a chord count once), and these are at least this share [1] of its ties that have words,
#                         they are no ties: the print draws a bow from syllable to syllable. The words of a staff are the
#                         nearest band of words under it, at most [2] staff spaces away. A syllable begins from [3] staff spaces left of
#                         the middle of the second head to [4] right of it and is at least [5] wide; its letters stand at
#                         most [6] apart, and a letter's column has ink over [7] staff spaces of rows (a hyphen and a
#                         line under the words are flat)
TIE_BREAK = (3.0, 0.45, 1.8, 1.0, 0.4, 0.6, 1.0, 0.9, 0.5)   # a tie over the end of a line (None: off): a bow leaves the last
#                         note of its voice, is this many staff spaces long or more, shows its ink in this share of its
#                         columns, ends at most this far before the end of the staff and moves at most this far up or
#                         down; or a short one (this long, this share of ink, ending this near the end) with a bow
#                         that comes to the first note of the next line (this long, this share of ink). The first note
#                         of that staff in the next system stands at the same place.


TIE_PAGE = (3.0, 0.45, 1.8, 1.0, 0.9, 0.45, 3.0, 2.0)   # a tie over the end of a page (None: off): on the last system of a page one
#                         bow leaves the last note of its voice (this many staff spaces long or more, its ink in this
#                         share of its columns, ending at most this far before the end of the staff, moving at most this
#                         far up or down): the note gets 'tie_start', and the reader hands its staff and place on to
#                         the next page of the hymn. There the first note of that staff at that place gets 'tie_stop'
#                         when a bow comes to it (this long, this share of ink, looked for over this many staff spaces
#                         before the note: the bow begins after the time signature) and the note stands at most this
#                         many staff spaces after the first note of the system. A page that is read alone marks the
#                         leaving half only: the ink before a first note (clef, key, time) looks like a short bow.
TIE_BREAK_BOTH = (0.3, 0.5)   # a head that two voices share (a stem up and a stem down) is tied twice over the end of a line
#                         too (None: off): the next line sets the two voices side by side where their notes differ in
#                         length, and the head of the other voice that begins at most [0] staff spaces inside the first
#                         one's box and [1] after it, at the same place, is tied when a bow comes to it as well
TIE_BREAK_LINE = 0.5     # the long bow over the end of a line may begin in a staff line beside its head: the line hides
#                         its first part (None: off). Such a bow ends at the end of the staff: its way stops this many
#                         staff spaces or more before the column to which it is followed, one staff space past the
#                         staff. Ink that goes on past the lines is no bow that a line hid (a pen lay on one page).


TIE_SOFT = (0.1, 1.0, 0.3, 0.3)   # a bow in pencil between two printed heads is no tie (None: off). Of the columns where the
#                         bow's ink shows and no staff line lies within 3 px, under the first share hold black ink at the
#                         bow (layers.BLACK; 2 px over and under its row), and these columns are the second number of staff
#                         spaces or more. The two heads are print: black in the third share of their ink or more, and so
#                         are the lines of the staff along the bow, in the last share of their ink or more. (Of the 298
#                         bows that LitChoir's scan pages read a tie from, one is such a bow, a phrase mark in pencil
#                         with black in 0.07 of its columns; the others hold black in 0.4 or more, but for the ties of
#                         one grey copy, whose staff lines hold no black either. A rule for one case.)


def _soft_bow(layers: dict, way: dict, x: int, one: dict, two: dict) -> bool:
    """Is the bow `way`, followed from the column x, a line in pencil between two printed heads (TIE_SOFT)?"""
    ink, black, lines = layers['ink'], layers['black'], layers['lines']
    height = ink.shape[0]
    clear = dark = 0
    for number, (row, shown) in enumerate(zip(way['rows'], way['shown'])):
        row, column = int(round(row)), x + number
        if not shown or column >= ink.shape[1] or lines[max(0, row - 3):min(height, row + 4), column].any():
            continue
        clear += 1
        dark += bool(black[max(0, row - 2):min(height, row + 3), column].any())
    staff = layers['staves'][one['staff']]
    if clear < TIE_SOFT[1] * staff['space'] or dark >= TIE_SOFT[0] * clear:
        return False
    for head in (one, two):
        y0, x0, y1, x1 = max(0, int(head['y0'])), max(0, int(head['x0'])), int(head['y1']) + 1, int(head['x1']) + 1
        if float(black[y0:y1, x0:x1].sum()) < TIE_SOFT[2] * float(ink[y0:y1, x0:x1].sum()):
            return False
    top, bottom = max(0, int(staff['rows'][0]) - 3), min(height, int(staff['rows'][4]) + 4)
    line = lines[top:bottom, x:x + len(way['rows'])] > 0
    return float(black[top:bottom, x:x + len(way['rows'])][line].sum()) >= TIE_SOFT[3] * max(1, int(line.sum()))


def _follow(thin: np.ndarray, lines: np.ndarray, x: int, y: float, last: int, space: float,
            thick: float | None = None) -> dict | None:
    """Follows thin ink from (x, y) toward the column `last`, to where it breaks off: {'rows': the bow's row in each
    column, 'shown': whether its ink was seen there, 'seen', 'hidden' (how many columns of each), 'end': the last
    column with ink}, or None when there is no ink to follow."""
    height = thin.shape[0]
    most = int(round((thick or TIE_THIN) * space)) + 1
    rows, kinds, gap, blind = [], [], 0, 0
    own, along, alongs = None, False, 0    # how thick the bow's own ink was in the last column where it ran alone (TIE_EDGE)
    for column in range(x, last + 1):
        reach = int(min(0.8 * space, 3 + 0.5 * blind))
        low, high = max(1, int(round(y)) - reach), min(height - 1, int(round(y)) + reach + 1)
        found = np.nonzero(thin[low:high, column])[0]
        kind = None
        if len(found):
            row = int(found[np.argmin(np.abs(found + low - y))]) + low
            top = bottom = row
            while top > 0 and thin[top - 1, column]:
                top -= 1
            while bottom + 1 < height and thin[bottom + 1, column]:
                bottom += 1
            if bottom - top + 1 <= most:
                size = bottom - top + 1
                side = int(round(0.5 * space))
                if TIE_EDGE and own is not None and (size - own >= TIE_EDGE * space or (along and size > own + 1)) \
                        and not lines[top:bottom + 1, max(0, column - side):column + side + 1].any():
                    # The bow runs along another stroke and is one band of ink with it: the bow keeps to the side of
                    # the band where it came in, as thick as it was alone, until the band is no thicker than the bow.
                    along = True
                    alongs += 1
                    y = top + (own - 1) / 2 if y - top <= bottom - y else bottom - (own - 1) / 2
                else:
                    along = False
                    y = (top + bottom) / 2
                    own = size
                kind = 'seen'
                gap = blind = 0
        if kind is None:
            row = int(round(y))
            blind += 1
            if lines[low:high, column].any() if TIE_UNDER else lines[max(0, row - 1):row + 2, column].any():
                kind = 'hidden'
            else:
                kind = 'gap'
                gap += 1
                if gap > TIE_GAP * space:
                    break
        rows.append(y)
        kinds.append(kind)
    # The way ends where its ink was seen last. After it, a staff line may hide the bow up to the head ('tail': for
    # how many columns, when no paper shows there).
    tail = 0
    while kinds and kinds[-1] != 'seen':
        tail = tail + 1 if kinds[-1] == 'hidden' and tail is not None else None
        kinds.pop()
        rows.pop()
    if kinds.count('seen') < 2:
        return None
    return {'rows': np.array(rows), 'shown': np.array([kind == 'seen' for kind in kinds]), 'seen': kinds.count('seen'),
            'hidden': kinds.count('hidden'), 'end': x + len(kinds) - 1, 'tail': tail or 0, 'along': alongs,
            'hide': np.array([kind == 'hidden' for kind in kinds])}


def _apart(way: dict, x: int, first: int, last: int, space: float) -> bool:
    """Is the way that was followed from the column `x` a short bow that stands free between its heads (TIE_APART)?
    The heads' columns end at `first` and begin again at `last`. The bow is the first part of the way, up to where
    paper shows; what follows the paper is the ink at the second head."""
    shown = way['shown']
    breaks = np.nonzero(~shown)[0]
    if not len(breaks) or way['hidden']:
        return False
    cut = int(breaks[0])
    paper = len(breaks)
    if breaks[-1] - cut + 1 != paper:
        return False            # more than one break
    after = len(shown) - cut - paper
    before_bow, after_bow = x - first, last - (x + cut - 1)
    if cut < TIE_APART[0] * space or paper < TIE_APART[1] * space or after > TIE_APART[2] * space \
            or abs(before_bow - after_bow) > TIE_APART[3] * space:
        return False
    return _is_bow({'rows': way['rows'][:cut], 'shown': shown[:cut], 'seen': cut}, space)


def _thin(bare: np.ndarray, height: int) -> tuple[np.ndarray, np.ndarray]:
    """The thin ink of a page, for the bows: the ink without the blobs that are `height` pixels high or more, column
    by column. Twice: with the top row of the blobs where TIE_RIM asks for it, and without it."""
    kernel = np.ones((height, 1), np.uint8)
    worn = cv2.erode(bare, kernel, anchor=(0, height // 2))
    tall = cv2.dilate(worn, kernel, anchor=(0, height - 1 - height // 2))
    core = bare & (1 - tall)
    if TIE_RIM == 'even':
        # OpenCV's opening, as it always was: with an even height its result lies one pixel low.
        return bare & (1 - cv2.morphologyEx(bare, cv2.MORPH_OPEN, kernel)), core
    if TIE_RIM == 'all':
        rim = tall.copy()
        rim[1:] &= 1 - tall[:-1]
        return core | rim, core
    return core, core


def _is_bow(way: dict, space: float, flat: bool = False) -> bool:
    """Is the way that was followed one smooth bow? The curve of a bow (a parabola) is laid through the rows where
    ink was seen: it is high enough, its highest place is in the middle part, and the ink stays close to it. A
    straight line with a hook at its end, and a line with a mark on it, are no bow. `flat`: the way begins and ends
    under or over the heads, so that it may be flatter where all of it shows (see TIE_FLAT)."""
    count = len(way['rows'])
    if way['seen'] < 8:
        return False
    along = np.linspace(-1.0, 1.0, count)[way['shown']]
    rows = way['rows'][way['shown']]
    bend, lean, level = np.polyfit(along, rows, 2)
    rest = float(np.sqrt(np.mean((rows - (bend * along ** 2 + lean * along + level)) ** 2)))
    high = abs(bend)
    least = TIE_FLAT[0] if TIE_FLAT and flat and way['seen'] >= TIE_FLAT[1] * count else TIE_BOW[0]
    return least * space <= high <= TIE_BOW[1] * space and abs(lean) <= TIE_EVEN * high + 0.2 * space \
        and rest <= TIE_SMOOTH * high + 0.04 * space


def _dips(way: dict, lines: np.ndarray, x: int, space: float) -> bool:
    """Does the way that was followed from the column `x` lie in a staff line where its ink does not show (see
    TIE_DIP)? The curve of a bow is laid through the rows where ink was seen; over the longest part without ink it
    stays at the staff line."""
    shown = way['shown']
    count = len(shown)
    if way['seen'] < 8:
        return False
    best, at = (0, 0), 0
    while at < count:
        if shown[at]:
            at += 1
            continue
        end = at
        while end < count and not shown[end]:
            end += 1
        if end - at > best[1]:
            best = (at, end - at)
        at = end
    if not best[1]:
        return False
    if min(int(np.sum(shown[:best[0]])), int(np.sum(shown[best[0] + best[1]:]))) < TIE_DIP[3] * space:
        return False
    along = np.linspace(-1.0, 1.0, count)
    bend, lean, level = np.polyfit(along[shown], way['rows'][shown], 2)
    away = []
    for number in range(best[0], best[0] + best[1]):
        rows = np.nonzero(lines[:, x + number])[0]
        if not len(rows):
            return False
        away.append(float(np.min(np.abs(rows - (bend * along[number] ** 2 + lean * along[number] + level)))))
    return float(np.mean(away)) <= TIE_DIP[1] * space


def _ends(way: dict, x: int, first: int, last: int, space: float) -> bool:
    """Is the way that was followed from the column `x` a bow that begins and ends inside a staff line (TIE_ENDS)? The
    heads' columns end at `first` and begin again at `last`. Its middle shows as one bow; before it and after it, up to
    the second head, a staff line hides it."""
    shown = way['shown']
    count = len(shown)
    stretches, at = [], 0
    while at < count:
        if not shown[at]:
            at += 1
            continue
        end = at
        while end < count and shown[end]:
            end += 1
        if end - at >= TIE_ENDS[1] * space:
            stretches.append((at, end))
        at = end
    if not stretches or way['end'] + way['tail'] < last - int(round(TIE_SIDE * space)):
        return False
    start, stop = stretches[0][0], stretches[-1][1]
    if min(x - first + start, last - (x + stop) + 1) < TIE_ENDS[0] * space:
        return False
    if stop - start < max(TIE_ENDS[2] * (last - first), TIE_ENDS[3] * space):
        return False
    return float(np.mean(shown[start:stop])) >= TIE_ENDS[4]


def _bar_at(ink: np.ndarray, rows: list[float], low: int, high: int, stems: list[float], space: float) -> int | None:
    """The last column from `low` to `high` where an upright line fills the staff from its top line to its bottom line
    and no stem stands (TIE_BAR): a bar line."""
    top, bottom = int(round(rows[0])), int(round(rows[-1]))
    low, high = max(1, low), min(ink.shape[1] - 2, high)
    if high < low:
        return None
    band = ink[top:bottom + 1, low - 1:high + 2] > 0
    filled = (band[:, :-2] | band[:, 1:-1] | band[:, 2:]).mean(axis=0) >= TIE_BAR[3]
    columns = [low + int(at) for at in np.nonzero(filled)[0]
               if all(abs(low + int(at) - stem) > TIE_BAR[4] * space for stem in stems)]
    return max(columns) if columns else None


def _past_bar(ink: np.ndarray, staff_rows: list[float], bar: int, row: float, end: int, space: float) -> float:
    """The share of the columns past the bar line (TIE_BAR_PAST) that hold ink near the row where the bow meets the bar
    line, outside the rows of the staff lines: a bow that goes on past the bar line to its head. The columns begin the
    first number of staff spaces past the right edge of the bar line and end the second number past it, or the fifth
    number before the second head; the rows are the third number of staff spaces around the bow's row, without the
    fourth number around each staff line."""
    if TIE_BAR_PAST is None:
        return 0.0
    top, bottom = int(round(staff_rows[0])), int(round(staff_rows[-1]))
    edge = bar
    while edge + 1 < ink.shape[1] and (ink[top:bottom + 1, edge + 1] > 0).mean() >= 0.5:
        edge += 1
    left = edge + 1 + int(round(TIE_BAR_PAST[0] * space))
    right = min(edge + 1 + int(round(TIE_BAR_PAST[1] * space)), end - int(round(TIE_BAR_PAST[4] * space)), ink.shape[1])
    if right <= left:
        return 0.0
    near = int(round(TIE_BAR_PAST[3] * space))
    rows = [y for y in range(max(0, int(round(row - TIE_BAR_PAST[2] * space))),
                             min(ink.shape[0], int(round(row + TIE_BAR_PAST[2] * space)) + 1))
            if all(abs(y - line) > near for line in staff_rows)]
    if not rows:
        return 0.0
    return float((ink[rows, left:right] > 0).any(axis=0).mean())


def _to_bar(way: dict, x: int, first: int, last: int, staff_bar: tuple, layers: dict, one: dict, two: dict,
            space: float) -> bool:
    """Is the way that was followed from the column `x` a bow that the print ends at a bar line before the second head
    (TIE_BAR)? The way is cut at the bar line: what it follows past the bar line (the line itself, a staff line, the
    stem of the next note) is no part of the bow."""
    rows_of_staff, stems = staff_bar
    bar = _bar_at(layers['ink'], rows_of_staff, max(first + int(round(TIE_BAR[1] * space)), last - int(round(TIE_BAR[0] * space))),
                  last, stems, space)
    if bar is None:
        return False
    shown, rows, hide = way['shown'], way['rows'], way['hide']
    cut = min(len(shown), bar - x - 1)
    if cut <= 0:
        return False
    seen = np.nonzero(shown[:cut])[0]
    if not len(seen) or bar - (x + int(seen[-1])) > TIE_BAR[2] * space:
        return False
    end = int(seen[-1]) + 1
    part = {'rows': rows[:end], 'shown': shown[:end], 'seen': int(shown[:end].sum()), 'hidden': int(hide[:end].sum())}
    if part['seen'] < TIE_SEEN[0] * end or part['seen'] + part['hidden'] < TIE_SEEN[1] * end:
        return False
    if abs(part['rows'][-1] - two['cy']) > TIE_BAR[5] * space:
        return False
    past = _past_bar(layers['ink'], rows_of_staff, bar, part['rows'][-1], int(two['x0']), space)
    good = _is_bow(part, space) and (TIE_BAR_PAST is None or past < TIE_BAR_PAST[5])
    if TIE_BAR_SEEN is not None:
        TIE_BAR_SEEN.append({'staff': one['staff'], 'one': (round(one['cx']), round(one['cy'])), 'two': (round(two['cx']), round(two['cy'])),
                             'place': round(one['place'], 2), 'bar': bar, 'start': x, 'reach': round((bar - (x + int(seen[-1]))) / space, 2),
                             'long': round(end / space, 2), 'seen': round(part['seen'] / end, 2), 'past': round(past, 2), 'row': round(float(part['rows'][-1])),
                             'bow': bool(good)})
    return good


def _bow(thin: np.ndarray, lines: np.ndarray, one: dict, two: dict, space: float,
         core: np.ndarray | None = None, swell: np.ndarray | None = None, layers: dict | None = None,
         staff_bar: tuple | None = None) -> bool:
    """Is there a bow from the head `one` to the head `two`? `core` is the thin ink for the flat bow (TIE_FLAT).
    With `layers`, a bow in pencil is no bow (TIE_SOFT). `staff_bar`: the staff's rows and the columns of its stems,
    for a bow that ends at a bar line (TIE_BAR)."""
    if _way(thin, lines, one, two, space, False, None, swell, layers):
        return True
    if TIE_BAR and staff_bar is not None and layers is not None \
            and _way(thin, lines, one, two, space, False, None, None, layers, staff_bar):
        return True
    return bool(TIE_FLAT) and core is not None and _way(core, lines, one, two, space, True, None, None, layers)


def _way(thin: np.ndarray, lines: np.ndarray, one: dict, two: dict, space: float, low: bool,
         thick: float | None = None, swell: np.ndarray | None = None, layers: dict | None = None,
         staff_bar: tuple | None = None) -> bool:
    """Is there a way of thin ink from the head `one` to the head `two` that is a bow? `low`: a flat bow counts.
    `thick`: how thick the bow may be, in staff spaces (TIE_THIN when None). With `layers`, a way in pencil is
    left out (TIE_SOFT)."""
    pencil = (lambda way, column: _soft_bow(layers, way, column, one, two)) if TIE_SOFT and layers is not None else (lambda way, column: False)
    first, last = int(one['x1']) + 1, int(two['x0']) - 1
    if last - first < TIE_LEAST * space:
        return False
    side, high = int(round(TIE_SIDE * space)), int(round(TIE_HIGH * space))
    top, bottom = max(0, int(one['cy']) - high), min(thin.shape[0], int(one['cy']) + high + 1)
    tried = set()
    for column in range(first, min(last, first + side), 2):
        found = np.nonzero(thin[top:bottom, column])[0]
        starts, before = [], None
        for row in found:
            if before is None or row != before + 1:
                starts.append(row + top)
            before = row
        hidden = []
        if TIE_FROM_LINE and column == first:
            # A bow that begins in a staff line beside its head: the line hides its first part.
            before = None
            for row in np.nonzero(lines[top:bottom, column])[0]:
                if before is None or row != before + 1:
                    hidden.append(row + top)
                before = row
            hidden = [row for row in hidden if not any(abs(row - other) <= 3 for other in starts)]
            starts += hidden
        for row in starts:
            # A bow that was followed from an earlier column is not followed again.
            if any(abs(row - other) <= 3 for other in tried):
                continue
            way = _follow(thin, lines, column, float(row), last, space, thick)
            if way is None:
                continue
            if row not in hidden:       # a way from a staff line may be another bow's: that bow is still followed from its own start
                tried.add(int(round(way['rows'][min(len(way['rows']) - 1, 2)])))
            count = len(way['rows'])
            if staff_bar is not None:
                # Only the cut at a bar line (TIE_BAR): the other tests were asked without it.
                if _to_bar(way, column, first, last, staff_bar, layers, one, two, space) and not pencil(way, column):
                    return True
                continue
            ends = bool(TIE_ENDS) and not low and _ends(way, column, first, last, space)
            if way['end'] < last - side and not (TIE_TO_LINE and way['end'] + way['tail'] >= last - side
                                                 and way['end'] >= last - TIE_TO_LINE[0] * space
                                                 and count >= TIE_TO_LINE[1] * (last - way['end'])) and not ends:
                continue
            if abs(way['rows'][-1] - two['cy']) > high:
                continue
            if way['seen'] + way['hidden'] < TIE_SEEN[1] * count:
                if TIE_APART and not low and abs(one['cy'] - two['cy']) <= TIE_APART[4] * space \
                        and _apart(way, column, first, last, space) and not pencil(way, column):
                    return True
                if swell is not None and not low and way['seen'] >= TIE_SWELL[1] * count \
                        and (count >= TIE_SWELL[2] * space or (TIE_EDGE and way['along'])):
                    # A bow that swells: the same way in ink that may be fatter. And a bow that runs along another
                    # stroke (TIE_EDGE), where the band of the two is fatter than thin ink.
                    fat = _follow(swell, lines, column, float(row), last, space, TIE_SWELL[0])
                    if fat is not None and (count >= TIE_SWELL[2] * space or fat['along']) \
                            and fat['end'] >= last - side and abs(fat['rows'][-1] - two['cy']) <= high \
                            and fat['seen'] + fat['hidden'] >= TIE_SEEN[1] * len(fat['rows']) \
                            and fat['seen'] >= TIE_SEEN[0] * len(fat['rows']) and _is_bow(fat, space) and not pencil(fat, column):
                        return True
                continue
            if way['seen'] < TIE_SEEN[0] * count and not (TIE_DIP and way['seen'] >= TIE_DIP[0] * count
                                                         and count >= TIE_DIP[2] * space
                                                         and _dips(way, lines, column, space)) and not ends:
                continue
            flat = low and min(abs(way['rows'][0] - one['cy']), abs(way['rows'][-1] - two['cy'])) >= TIE_FLAT[2] * space
            if not _is_bow(way, space, flat) or pencil(way, column):
                continue
            return True
    return False


def _half(thin: np.ndarray, lines: np.ndarray, words: list[dict], head: dict, last: int, space: float,
          in_line: bool = False) -> dict | None:
    """The longest thin way that begins beside a head and goes right, toward the column `last`: {'long' (staff spaces),
    'seen' (the share of its columns with ink), 'togo' (staff spaces from its end to `last`), 'drift' (how far it
    moves up or down)}. None without one, when the ink goes on at the left of the head too (a slur that passes), or
    when it lies in the rows of the words (the line after a syllable). `in_line`: only the ways that begin inside a
    staff line beside the head (see TIE_BREAK_LINE)."""
    first = int(head['x1']) + 1
    side, high = int(round(TIE_SIDE * space)), int(round(TIE_HIGH * space))
    top, bottom = max(0, int(head['cy']) - high), min(thin.shape[0], int(head['cy']) + high + 1)
    best = None
    for column in range(first, min(last, first + side), 2):
        found = np.nonzero(thin[top:bottom, column])[0]
        starts, before = [], None
        for row in found:
            if before is None or row != before + 1:
                starts.append(row + top)
            before = row
        if in_line:
            # A bow that begins in a staff line beside its head: the line hides its first part (as TIE_FROM_LINE).
            before, hidden = None, []
            for row in np.nonzero(lines[top:bottom, column])[0] if column == first else []:
                if before is None or row != before + 1:
                    hidden.append(row + top)
                before = row
            starts = [row for row in hidden if not any(abs(row - other) <= 3 for other in starts)]
        for row in starts:
            way = _follow(thin, lines, column, float(row), last, space)
            if way is None or (best is not None and len(way['rows']) <= best['count']):
                continue
            passing = thin[max(0, int(row - 0.25 * space)):int(row + 0.25 * space) + 1,
                           max(0, int(head['x0'] - 1.0 * space)):max(0, int(head['x0'] - 0.3 * space))]
            if passing.any() or any(band['top'] <= row <= band['bottom'] and band['x0'] <= column <= band['x1'] for band in words):
                continue
            count = len(way['rows'])
            best = {'count': count, 'long': count / space, 'seen': way['seen'] / count, 'togo': (last - way['end']) / space,
                    'drift': abs(float(way['rows'][-1] - way['rows'][0])) / space, 'way': way}
    return best


def _over_break(layers: dict, heads: list[dict], thin: np.ndarray, voices: dict) -> list[tuple[dict, dict]]:
    """The ties over the end of a line: (the last head of its voice on a staff, the first head of that staff in the
    next system, at the same place)."""
    space, lines, words, staves = layers['space'], layers['lines'], layers.get('words') or [], layers['staves']
    width = thin.shape[1]
    flipped, flipped_lines = np.ascontiguousarray(thin[:, ::-1]), np.ascontiguousarray(lines[:, ::-1])
    flipped_words = [dict(band, x0=width - 1 - band['x1'], x1=width - 1 - band['x0']) for band in words]
    found = []
    for index, staff in enumerate(staves):
        target = next((number for number, other in enumerate(staves)
                       if other['system'] == staff['system'] + 1 and other['number'] == staff['number']), None)
        if target is None:
            continue
        mine = sorted((head for head in heads if head['staff'] == index), key=lambda head: head['cx'])
        theirs = sorted((head for head in heads if head['staff'] == target), key=lambda head: head['cx'])
        for number, one in enumerate(mine):
            place, ways = round(one['place']), voices[id(one)]
            if one.get('tie_start') or any(round(other['place']) == place or (voices[id(other)] & ways)
                                           for other in mine[number + 1:] if other['x0'] - one['x1'] >= 0.5 * space):
                continue
            two = next((other for other in theirs if round(other['place']) == place), None)
            if two is None or two.get('tie_stop') or any(voices[id(other)] & voices[id(two)] for other in theirs
                                                         if two['x0'] - other['x1'] >= 0.5 * space):
                continue
            go = _half(thin, lines, words, one, min(width - 1, int(staff['x1'] + space)), space)
            tied = False
            inside = _half(thin, lines, words, one, min(width - 1, int(staff['x1'] + space)), space, True) \
                if TIE_BREAK_LINE else None
            if inside is not None and inside['togo'] < TIE_BREAK_LINE:
                inside = None
            for way in (go, inside):
                tied = tied or (way is not None and way['long'] >= TIE_BREAK[0] and way['seen'] >= TIE_BREAK[1]
                                and way['togo'] <= TIE_BREAK[2] and way['drift'] <= TIE_BREAK[3])
            if go is None and not tied:
                continue
            if not tied and go['long'] >= TIE_BREAK[4] and go['seen'] >= TIE_BREAK[5] and go['togo'] <= TIE_BREAK[6]:
                mirror = dict(two, x0=width - 1 - two['x1'], x1=width - 1 - two['x0'])
                come = _half(flipped, flipped_lines, flipped_words, mirror, width - 1 - int(staves[target]['x0']), space)
                tied = come is not None and come['long'] >= TIE_BREAK[7] and come['seen'] >= TIE_BREAK[8]
            if tied:
                found.append((one, two))
                if TIE_BREAK_BOTH and ways == {'up', 'down'} and len(voices[id(two)]) < 2:
                    for other in theirs:
                        if other is not two and round(other['place']) == place and voices[id(other)] != voices[id(two)] \
                                and -TIE_BREAK_BOTH[0] * space <= other['x0'] - two['x1'] <= TIE_BREAK_BOTH[1] * space \
                                and not other.get('tie_stop'):
                            mirror = dict(other, x0=width - 1 - other['x1'], x1=width - 1 - other['x0'])
                            come = _half(flipped, flipped_lines, flipped_words, mirror, width - 1 - int(staves[target]['x0']), space)
                            if come is not None and come['long'] >= TIE_BREAK[7] and come['seen'] >= TIE_BREAK[8]:
                                found.append((one, other))
                            break
    return found


def _over_page(layers: dict, heads: list[dict], thin: np.ndarray, voices: dict, before: list | None) -> None:
    """The ties over the end of a page (see TIE_PAGE). The last head of its voice on a staff of the last system that
    one long bow leaves toward the end of the staff gets 'tie_start' and 'tie_out'. `before` holds the heads that
    left such a bow on the page before, as (the number of the staff in its system, the place): the first head of
    that staff at that place on the first system gets 'tie_stop' when a bow comes to it."""
    space, lines, words, staves = layers['space'], layers['lines'], layers.get('words') or [], layers['staves']
    width = thin.shape[1]
    systems = [staff['system'] for staff in staves]
    for index, staff in enumerate(staves):
        own = sorted((head for head in heads if head['staff'] == index), key=lambda head: head['cx'])
        if staff['system'] != max(systems):
            continue
        for number, one in enumerate(own):
            place, ways = round(one['place']), voices[id(one)]
            if one.get('tie_start') or any(round(other['place']) == place or (voices[id(other)] & ways)
                                           for other in own[number + 1:] if other['x0'] - one['x1'] >= 0.5 * space):
                continue
            end = min(width - 1, int(staff['x1'] + space))
            ways = [_half(thin, lines, words, one, end, space)]
            if TIE_BREAK_LINE:
                ways.append(_half(thin, lines, words, one, end, space, True))
                if ways[1] is not None and ways[1]['togo'] < TIE_BREAK_LINE:
                    ways[1] = None
            if any(go is not None and go['long'] >= TIE_PAGE[0] and go['seen'] >= TIE_PAGE[1] and go['togo'] <= TIE_PAGE[2]
                   and go['drift'] <= TIE_PAGE[3] and _is_bow(go['way'], space) for go in ways):
                one['tie_start'] = one['tie_out'] = True
    if not before:
        return
    flipped, flipped_lines = np.ascontiguousarray(thin[:, ::-1]), np.ascontiguousarray(lines[:, ::-1])
    flipped_words = [dict(band, x0=width - 1 - band['x1'], x1=width - 1 - band['x0']) for band in words]
    first = min((head['cx'] for head in heads if staves[head['staff']]['system'] == min(systems)), default=0.0)
    for index, staff in enumerate(staves):
        if staff['system'] != min(systems):
            continue
        own = sorted((head for head in heads if head['staff'] == index), key=lambda head: head['cx'])
        for place in sorted({int(item[1]) for item in before if int(item[0]) == staff['number']}):
            two = next((head for head in own if round(head['place']) == place), None)
            if two is None or two.get('tie_stop') or two['cx'] > first + TIE_PAGE[7] * space \
                    or any(voices[id(other)] & voices[id(two)] for other in own if two['x0'] - other['x1'] >= 0.5 * space):
                continue
            mirror = dict(two, x0=width - 1 - two['x1'], x1=width - 1 - two['x0'])
            begin = max(int(staff['x0']), int(two['x0'] - TIE_PAGE[6] * space))
            come = _half(flipped, flipped_lines, flipped_words, mirror, width - 1 - begin, space)
            if come is not None and come['long'] >= TIE_PAGE[4] and come['seen'] >= TIE_PAGE[5]:
                two['tie_stop'] = True


def _in_line(layers: dict, one: dict, two: dict, space: float) -> bool:
    """Is there a flat bow from the head `one` to the head `two` that lies in a staff line? An engraver sets a flat
    tie into the staff line over or under its heads: the line is then fatter between the two heads, like a lens,
    and as thin as ever beside the lens. The ink in a band around the line is counted in each column; a column where
    a stem, a bar line or a head crosses the band does not count. The bow of a note with its stem up lies over the
    head, and the bow of a note with its stem down under it."""
    first, last = int(one['x1']) + 1, int(two['x0']) - 1
    if last - first < max(TIE_LEAST, TIE_LINE[3]) * space:
        return False
    staff = layers['staves'][one['staff']]
    ink, thick = layers['ink'], staff['thick']
    reach = int(round(0.4 * space))
    least = max(2.0, TIE_LINE[1] * space)
    ways = {stem['direction'] for head in (one, two) for stem in head['stems']}
    for line in staff['rows']:
        if not 0.4 * space <= abs(line - one['cy']) <= TIE_LINE[5] * space \
                or not 0.4 * space <= abs(line - two['cy']) <= TIE_LINE[5] * space:
            continue
        if ways == {'up'} and line > one['cy'] or ways == {'down'} and line < one['cy']:
            continue
        row = int(round(line))
        band = (ink[max(0, row - reach):row + reach + 1, first:last + 1] > 0).sum(axis=0)
        free = band < 2 * reach
        if (~free).sum() > TIE_LINE[2] * len(band) or free.sum() < 8:
            continue
        more = (band - thick)[free]
        fat = np.nonzero(more >= least)[0]
        # The lens: the longest run of fat columns, with breaks of a few columns.
        best, begin, before = None, None, None
        for column in list(fat) + [None]:
            if column is None or (before is not None and column - before > 0.25 * space):
                if begin is not None and (best is None or before - begin > best[1] - best[0]):
                    best = (begin, before)
                begin = column
            elif begin is None:
                begin = column
            before = column
        if best is None:
            continue
        inside = more[best[0]:best[1] + 1]
        outside = np.concatenate([more[:best[0]], more[best[1] + 1:]])
        middle = (best[0] + best[1]) / 2 / len(more)
        if best[1] - best[0] + 1 < max(TIE_LINE[0] * len(more), TIE_LINE[3] * space) or not 0.3 <= middle <= 0.7 \
                or (inside >= least).mean() < TIE_LINE[4]:
            continue
        if len(outside) >= 6 and np.median(outside) >= 0.5 * least:
            continue      # a line that is fat all the way is no bow
        if TIE_BESIDE and np.median(inside) - _beside(ink, row, reach, thick, one, two, TIE_BESIDE * space) < least:
            continue      # nor is a line that is as fat beside the two heads
        return True
    return False


def _beside(ink: np.ndarray, row: int, reach: int, thick: float, one: dict, two: dict, wide: float) -> float:
    """How much fatter than its staff's lines a staff line is beside two heads: the median of the ink in a band around
    the line, in the columns at the left of the first head and at the right of the second, the fatter side."""
    sides = []
    for begin, end in ((int(one['x0']) - int(wide), int(one['x0'])), (int(two['x1']) + 1, int(two['x1']) + 1 + int(wide))):
        begin, end = max(0, begin), min(ink.shape[1], end)
        if end - begin >= 4:
            sides.append(float(np.median((ink[max(0, row - reach):row + reach + 1, begin:end] > 0).sum(axis=0))) - thick)
    return max(sides) if sides else 0.0


def _syllable(layers: dict, head: dict) -> bool | None:
    """True where a syllable of the words begins under the head; None where no words stand under the staff of the
    head (see TIE_WORD). The words over a staff are those of the staff over it: a voice under them can hold its note
    while the others sing on."""
    space, bare = layers['space'], layers['bare']
    rows = layers['staves'][head['staff']]['rows']
    bands = layers.get('words') or []
    band = min((band for band in bands if band['top'] > rows[4] - space), key=lambda band: band['top'], default=None)
    if band is None or band['top'] - rows[4] > TIE_WORD[2] * space:
        return None
    middle = head['cx']
    first = max(0, int(middle - (TIE_WORD[3] + 1.0) * space))
    last = min(bare.shape[1], int(middle + (TIE_WORD[4] + TIE_WORD[5] + 1.0) * space))
    part = bare[band['top']:band['bottom'], first:last]
    if part.size == 0:
        return False
    top, bottom = part.argmax(axis=0), part.shape[0] - 1 - part[::-1].argmax(axis=0)
    letters = np.flatnonzero(part.any(axis=0) & (bottom - top + 1 >= TIE_WORD[7] * space)) + first
    start = None
    for number, column in enumerate(letters):
        if number == 0 or column - letters[number - 1] > TIE_WORD[6] * space:
            start = column
        if (number + 1 == len(letters) or letters[number + 1] - column > TIE_WORD[6] * space) \
                and column - start >= TIE_WORD[5] * space and -TIE_WORD[3] * space <= start - middle <= TIE_WORD[4] * space:
            return True
    return False


def read_ties(layers: dict, heads: list[dict], before: list | None = None) -> list[tuple[dict, dict]]:
    """The ties of a page: (first head, second head). Each first head gets 'tie_start' and each second head
    'tie_stop'. A tie over the end of the page marks its head alone ('tie_out' too, where it leaves); `before` are
    such heads of the page before in the same hymn, as (the number of the staff in its system, the place)."""
    if not TIE_FAR:
        return []
    space = layers['space']
    bare, lines = layers['bare'], layers['lines']
    most = int(round(TIE_THIN * space)) + 1
    thin, core = _thin(bare, most + 1)
    bold = _thin(bare, int(round(TIE_BOLD * space)) + 2)[1] if TIE_BOLD else None
    swell = _thin(bare, int(round(TIE_SWELL[0] * space)) + 2)[1] if TIE_SWELL else None
    found = []
    for staff in sorted({head['staff'] for head in heads}):
        own = sorted((head for head in heads if head['staff'] == staff), key=lambda head: head['cx'])
        staff_bar = (layers['staves'][staff]['rows'], [stem['x'] for head in own for stem in head['stems']]) \
            if TIE_BAR and 'staves' in layers else None
        voices = {}
        for one in own:
            voices[id(one)] = {stem['direction'] for stem in one['stems']}
            if TIE_PARTNER and not one['stems']:
                # The whole note of one voice in the column of the other voice's note: its stem would go the other way.
                beside = [(abs(other['cx'] - one['cx']), other) for other in own if len({stem['direction'] for stem in other['stems']}) == 1
                          and (abs(other['cx'] - one['cx']) <= TIE_PARTNER[0] * space
                               or (abs(round(other['place']) - round(one['place'])) <= 1 and abs(other['cx'] - one['cx']) <= TIE_PARTNER[1] * space))]
                if beside:
                    partner = min(beside, key=lambda item: item[0])[1]
                    voices[id(one)] = {'down' if partner['stems'][0]['direction'] == 'up' else 'up'}
        for number, one in enumerate(own):
            place = round(one['place'])
            ways = voices[id(one)]
            two = None
            for other in own[number + 1:]:
                if other['x0'] - one['x1'] > TIE_FAR * space:
                    break
                if other['x0'] - one['x1'] < 0.5 * space:
                    continue
                if round(other['place']) == place:
                    two = other
                    break
                # The other note of a chord stands beside the second head, not between the two: it is in its column
                # and has its stems. (A note of another voice there shows that this voice went on to another place.)
                if TIE_COLUMN and any(round(head['place']) == place and abs(head['cx'] - other['cx']) <= TIE_COLUMN * space
                                      and (voices[id(head)] == voices[id(other)]
                                           or (TIE_SHARED and voices[id(other)] and voices[id(other)] < voices[id(head)]))
                                      for head in own[number + 1:] if head is not other):
                    continue
                # Another note of this voice between the two heads: a bow over it is a slur.
                theirs = voices[id(other)]
                if (ways & theirs) or (not ways and not theirs) or ((not ways or not theirs) and abs((round(other['place']) if TIE_ROUND else other['place']) - place) < 2):
                    break
            if two is None:
                continue
            tied = _bow(thin, lines, one, two, space, core, swell, layers, staff_bar) \
                or bool(TIE_LINE and _in_line(layers, one, two, space)) \
                or (bold is not None and _way(bold, lines, one, two, space, False, TIE_BOLD))
            if tied:
                one['tie_start'] = True
                two['tie_stop'] = True
                found.append((one, two))
                if TIE_BOTH and ways == {'up', 'down'} and len(voices[id(two)]) < 2:
                    for other in own[number + 1:]:
                        if other is not two and round(other['place']) == place and voices[id(other)] != voices[id(two)] \
                                and 0 <= other['x0'] - two['x1'] <= TIE_BOTH * space and not other.get('tie_stop'):
                            if _bow(thin, lines, one, other, space, core, swell, layers):
                                other['tie_stop'] = True
                                found.append((one, other))
                            break
    if TIE_WORD:
        # A page whose bows go from syllable to syllable (see TIE_WORD).
        asked = [(one, two, _syllable(layers, two)) for one, two in found]
        word = [(one, two) for one, two, begins in asked if begins]

        def columns(pairs: list) -> int:
            # The ties of a chord are one bow of the page.
            places = sorted((two['staff'], two['cx']) for _, two in pairs)
            return sum(1 for number, (staff, x) in enumerate(places)
                       if number == 0 or staff != places[number - 1][0] or x - places[number - 1][1] > 0.7 * space)

        if columns(word) >= TIE_WORD[0] \
                and columns(word) >= TIE_WORD[1] * columns([(one, two) for one, two, begins in asked if begins is not None]):
            found = [(one, two) for one, two, begins in asked if not begins]
            for one, two in word:
                one['tie_start'] = any(other is one for other, _ in found)
                two['tie_stop'] = any(other is two for _, other in found)
    if TIE_BREAK:
        every = {}
        for head in heads:
            every[id(head)] = {stem['direction'] for stem in head['stems']}
        for one, two in _over_break(layers, heads, thin, every):
            one['tie_start'] = True
            two['tie_stop'] = True
            found.append((one, two))
    if TIE_PAGE:
        _over_page(layers, heads, thin, {id(head): {stem['direction'] for stem in head['stems']} for head in heads}, before)
    return found

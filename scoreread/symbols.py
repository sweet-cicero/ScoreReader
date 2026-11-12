"""Reads the symbols of a clean page from its layers (scoreread.layers): note heads with their pitch place and their
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
HOLLOW_PAGE = (0.3, 0.03)   # on a page whose hollow heads have small holes: from this share of their usual hole, and
                            # never under the second number (None: off)
HOLLOW_WORN = (0.4, 0.2)    # on a page whose hollow heads have large holes (their usual hole is the second share or
#                    more): a head is hollow from the first share of that usual hole (None: off)
LINE_SLIT = (0.3, 2, 0.15)   # a filled head with a stem and a staff line or a ledger line through it (its middle at
#                     most this many staff spaces from the line) is a half note when a speck of paper of this many
#                     px or more is closed in over the line and one under it, the upper one this many staff spaces
#                     further right: the slit of a half note that a heavy print nearly closed (None: off)
RIM = 0.8            # a note without a stem has its own ink at this share of the rim of its hole
FLAG_END = 0.7       # the flag of such a note begins at most this many staff spaces from the end of the stem
FLAG_LOOP = True     # a hollow mark beside the stem of a note with a printed flag is the flag's loop, not a head
SOLID_LOOP = 0.7     # ink this share of a head's height over or under a hole is a filled head beside a flag's loop (0: off)
ROOM_HEADS = (0.75, 4.0, 3)   # a mark larger than a head with a room that a large flag or a short beam closes with
#                     the staff lines: its heads are the pieces that are left when an oval of this share of a head
#                     is pushed through its ink; the mark is at most this many heads wide and high, and holds at
#                     most this many heads (None: off)
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
NO_LEDGER_FIVE = 5.75# and up to this place it stands in the first space; past it, its measured place stays
NO_LEDGER = 6.3      # a head with no ledger line, up to this place beside the staff, stands in the first space (0: off)
FAR_STEM = (2.0, 8.4, 0.75, 1.35)   # a head past NO_LEDGER with no ledger line is a note when its stem goes on this many
#                      staff spaces past it, up to this place, and its box is from this to this share of the page's head (None: off)
WORD_STEM = (0.35, 2.0, 0.7, 1.4, 1.0)   # a mark at most 2.0 staff spaces before the words is a note when its upright
#                    ink goes on this many staff spaces past it and into the words (or it is slim and ends at most
#                    1.0 staff spaces before them), and the mark is from this to this share as high as the heads of
#                    the page (None: off)
WORD_MARKS = True    # a thick mark in a band of words is a letter: no head and no sign
LEDGER_WORDS = True  # a ledger line is looked for up to the words, not in them
HEAD_NEAR = 1.5      # the page's head size comes from the marks at most this many staff spaces over or under a staff
HOLE_PLACE = True    # the place of a hollow head is the middle of its hole; else the middle of its ink
LEDGER_INK = True    # a ledger line is ink: the filled inside of a hollow head does not count for it
HAND_FLAT = 1.25     # the bowl of a flat that a hand drew is at most this wide, in staff spaces (0: off)
SHARP_SLIM = 0.3     # the strokes of a sharp are slim for this many staff spaces where they leave its mark
STUB = 0.3           # a thick stem that is this long (staff spaces) at the top or the bottom of a mark is cut off (0: off)
STUB_HIGH = 1.25     # when the mark is this many times as high as the heads of the page
WINGS = 0.25         # a ledger line shows this far at both sides of a head's body, in staff spaces (0: off)
WHOLE_BESIDE = (0.35, 0.2, 0.2, 0.2)   # a whole note that touches the head of the other voice has no stem: the stem
#                    of a filled head, at most this many staff spaces from the stem the hollow oval was given, is not its
#                    own when the two boxes are at most this far apart, their left edges are this near, and the oval is
#                    wider than the filled head by this much (None: off)
RIM_STEM = 0.3       # upright ink that ends in the box of another head of its piece of ink, or this many staff spaces
#                    past it, is the rim of that head and no stem (0: off)
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
LEDGER_FROM = 0.5    # a ledger line lies at least this many staff spaces from the staff
ORPHANS = (0.7, 1.5) # a thick mark with no stem, from this to this many times as wide and as high as the heads of the
#                    page, is a head when an upright stroke that no head has ends at its edge (None: off)
WHOLE_HALF = 0.3     # the same over or under a half note, when the oval is wider than it by this many staff spaces (0: off)
WHOLE_OVER = 0.4     # the oval may begin this many staff spaces left of the head it touches (it is set in the middle
#                      under it); 0: only as far as WHOLE_BESIDE says
WHOLE_STAFF = 0      # in the staff a whole note is at least this many times as wide as it is high (0: as WHOLE says).
#                    Off: with 1.0 it gained 1 note on the clean copies, lost 1 and wrote 8 notes that are not there.
WHOLE_FILLED = 0     # a filled oval without a stem, as large as a whole note, that touches a whole note over or under
#                    it (their middles at most this many staff spaces apart sideways) is a whole note whose hole
#                    the print filled (0: off). Off: with 0.5 it gained no note on the clean copies and lost 4.
WHOLE_UNISON = 0.25  # two voices on one note, a half note and a whole note side by side: the oval at the far side of
#                      the stem, its middle at most this many staff spaces from the height of the stem's own head,
#                      has no stem (0: off)
LINE_CHORD = 0.75    # hollow heads that touch, each on a line: the first and the last cell of their insides lie this
#                      many staff spaces further apart than as many heads less two in the spaces would (0: off)
TWO_HEADS = (1.5, 1.35)   # a filled mark with a stem up and a stem down is two heads when it is this many times as wide
                     # as the heads of the page (side by side), or this many times as high (one over the other); (): off


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


def _line_slit(layers: dict, mark: dict, staff: dict) -> bool:
    """A half note on a line whose slit a heavy print nearly closed: the staff line (or a ledger line) runs through
    the head, and of the slit two specks of paper are left, one over the line and one under it. The slit leans as the
    head does, so the upper speck stands to the right of the lower one. A filled head holds no paper at all."""
    space, rows = staff['space'], staff['rows']
    lines = list(rows) + [rows[0] - step * space for step in (1, 2, 3)] + [rows[4] + step * space for step in (1, 2, 3)]
    line = min(lines, key=lambda row: abs(row - mark['cy']))
    if abs(line - mark['cy']) > LINE_SLIT[0] * space:
        return False
    ink = layers['ink']
    x0, y0 = max(0, mark['x0'] - 1), max(0, mark['y0'] - 1)
    x1, y1 = min(ink.shape[1], mark['x1'] + 2), min(ink.shape[0], mark['y1'] + 2)
    paper = (1 - ink[y0:y1, x0:x1]).astype(np.uint8)
    count, _, stats, middles = cv2.connectedComponentsWithStats(paper, connectivity=4)
    over, under = None, None
    for label in range(1, count):
        x, y, wide, high, area = (int(value) for value in stats[label])
        if x == 0 or y == 0 or x + wide == paper.shape[1] or y + high == paper.shape[0] or area < LINE_SLIT[1]:
            continue        # the paper around the head
        speck = (area, float(middles[label][0]))
        if y0 + middles[label][1] < line:
            over = max(over, speck) if over else speck
        else:
            under = max(under, speck) if under else speck
    return bool(over and under and over[1] - under[1] >= LINE_SLIT[2] * space)


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
        largest = max(sum(hole['area'] for hole in cell) for cell in cells.values())
        gaps = sorted(gap for gap, cell in cells.items() if sum(hole['area'] for hole in cell) >= 0.25 * largest)
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
            # Two half holes are together as high as the inside of one head. The holes of two heads a third apart
            # have a staff line between them too, but together they are much higher.
            if 0 <= gap <= 0.4 * space and between and hole['y1'] - other['y0'] + 1 <= 1.0 * space \
                    and shared >= 0.5 * min(hole['x1'] - hole['x0'] + 1, other['x1'] - other['x0'] + 1):
                total = other['area'] + hole['area']
                other['cx'] = (other['cx'] * other['area'] + hole['cx'] * hole['area']) / total
                other['cy'] = (other['cy'] * other['area'] + hole['cy'] * hole['area']) / total
                other.update(x0=min(other['x0'], hole['x0']), x1=max(other['x1'], hole['x1']), y1=hole['y1'], area=total)
                break
        else:
            merged.append(dict(hole))
    # A sliver of paper at the rim of a head is no hole of its own.
    largest = max((hole['area'] for hole in merged), default=0.0)
    return [(hole['cx'], hole['cy']) for hole in merged if hole['area'] >= 0.25 * largest]


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
    marks = []
    for mark, mask, holes, x, y in pieces:
        if STUB:
            part = _without_stub(mask, space, high)
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
            if len(centres) >= 2:
                by_holes = True
                rows, columns = np.nonzero(mask)
                nearest = np.argmin([(rows - cy) ** 2 + (columns - cx) ** 2 for cx, cy in centres], axis=0)
                for number in range(len(centres)):
                    part = np.zeros_like(mask)
                    part[rows[nearest == number], columns[nearest == number]] = True
                    parts.append(_mark(part, holes, x, y, mark['blob']))
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
                if cut:
                    parts = [_mark(part, inside, px, py, mark['blob']) for part, inside, px, py in cut]
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
            inside = np.nonzero((mask & holes).any(axis=1))[0]
            over, under = int(inside[0]), own_high - 1 - int(inside[-1])
            named = False
            span = None
            # The loop of a flag is higher than the hole of a head, and the flag's end may hang under it as a tail.
            line = int(round(layers["staves"][0]["thick"]))
            tail = ROOM_SOLID and not by_holes and _loop_room(mask & holes, line, wide, high) \
                and _flag_room(mask, mask & holes, line, wide, high) and max(over, under) >= 1.5 * min(over, under)
            if max(over, under) >= SOLID_LOOP * high and (min(over, under) <= 0.4 * high or tail):
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
                found = [_mark(part, np.zeros_like(part), x, y, mark['blob']) for part in _heads_at_room(mask, mask & holes, wide, high)]
                found = [part for part in found if part]
                for number, part in enumerate(found):
                    part['loop'] = (mark['x0'], mark['y0'], mark['x1'], mark['y1'])
                    part['room'] = True
                    if number:
                        # Two notes under one beam are no heads of two voices on one line of ink: each is a blob of its own.
                        part['blob'] = -(1000 * len(marks) + number)
                if len(found) == 1:
                    mark = found[0]
                parts = found
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


def _heads_at_room(mask: np.ndarray, room: np.ndarray, wide: float, high: float) -> list[np.ndarray]:
    """The filled heads in a mark that a large flag or a short beam makes with them: on a short stem the flag comes
    back to a staff line at the head, and the head, the stem, the flag and the staff lines close in a room; two heads,
    their stems, a beam and a staff line do the same. The mark is larger than a head, and it is no hollow head. An
    oval nearly as large as a head goes through the ink of a head, and not through a stem, a flag or a beam: what it
    leaves are the heads. Returns the part of the mask of each head."""
    if mask.shape[1] > ROOM_HEADS[1] * wide or mask.shape[0] > ROOM_HEADS[1] * high:
        return []
    ink = (mask.astype(bool) & ~room.astype(bool)).astype(np.uint8)
    oval = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(ROOM_HEADS[0] * wide) | 1, int(ROOM_HEADS[0] * high) | 1))
    cores = cv2.morphologyEx(np.pad(ink, 1), cv2.MORPH_OPEN, oval)[1:-1, 1:-1]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(cores, connectivity=8)
    found = []
    for label in range(1, count):
        _, _, own_wide, own_high, area = (int(value) for value in stats[label])
        if ROOM_HEADS[0] * wide <= own_wide <= 1.3 * wide and own_high <= 1.3 * high and area >= 0.45 * wide * high:
            found.append(labels == label)
    return found if len(found) <= ROOM_HEADS[2] else []


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
    return best


def _at_staff(layers: dict, mark: dict) -> bool:
    """True when a mark stands where a head needs no ledger line (in the staff or in the first space beside it), or
    on a ledger line."""
    index = _staff_of(layers, mark['cx'], mark['cy'])
    if index is None:
        return False
    return abs(pitch_place(layers['staves'][index], mark['cy'])) <= 5.6 or _on_ledger(layers, mark)


def _in_words(layers: dict, mark: dict) -> bool:
    """True when a mark stands in a band of words (scoreread.words): it is a letter."""
    space = layers['space']
    return any(band['x0'] <= mark['cx'] <= band['x1'] and band['top'] <= mark['cy'] <= band['bottom']
               and mark['y0'] >= band['top'] - 0.3 * space and mark['y1'] <= band['bottom'] + 0.5 * space
               for band in layers.get('words') or [])


def _into_words(layers: dict, mark: dict, way: dict | None, before: float = 0.3) -> dict | None:
    """The band of words (scoreread.words) that the upright ink of a mark runs into, or ends at most `before` staff
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


def ledger_lines(layers: dict, staff: dict, head: dict) -> list[float]:
    """The rows of the ledger lines between a staff and a head beside it, the line through the head too. A ledger
    line is a level run of ink that reaches past the head on both sides and is thinner than a head."""
    free, space = layers['free'], staff['space']
    above = head['cy'] < staff['rows'][0]
    first, last = int(head['cx'] - 0.95 * space), int(head['cx'] + 0.95 * space)
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


def ledger_place(layers: dict, staff: dict, head: dict) -> float | None:
    """The place of a head beside the staff, read from its ledger lines as a singer reads it: the lines are counted,
    and the head stands on the last one or past it. A hand often draws the ledger lines nearer to each other than the
    staff lines, so the measured height alone names such a head a step off. Without a ledger line, and when the count
    and the measured height are a little apart, the measured place stays. None when the head is far from the staff
    and too few ledger lines lead to it: then it is no note."""
    rows, space = sorted(head.get('ledgers') or []), staff['space']
    place = head['place']
    if not rows:
        if NO_LEDGER and 4.6 < abs(place) <= NO_LEDGER_FIVE:
            return 5.0 if place > 0 else -5.0     # a head beside the staff with no ledger line stands in the first space
        return place
    up = place > 0
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
    steps = 2 * len(merged) + (1 if past > limit * space else 0 if past >= -0.27 * space else -1)
    found = float(4 + steps) if up else float(-4 - steps)
    if abs(found) < abs(place) - 2.2:
        return None       # too few ledger lines for a head this far from the staff: a letter over a hyphen
    return found if abs(found - place) <= 1.6 else place


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
        for mark in members:
            if abs(mark['cy'] - middle) <= 0.2 * space:
                # Two voices on one note stand side by side, with their stems on one line between them: the left
                # head has the stem that goes up, the right head the stem that goes down.
                keep = 'up' if mark['cx'] < centre else 'down'
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


def _two_heads(layers: dict, mark: dict) -> list[dict] | None:
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
    if own_wide >= TWO_HEADS[0] * wide:
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


def _whole_beside(layers: dict, marks: list[dict], limit: float) -> int:
    """A stem carries heads of one kind: all filled or all hollow. A print sets a whole note of one voice in the
    column of a stemmed note of the other voice, with their left edges in line; the two heads touch, and followed
    from the whole note the ink leads through the filled head to its stem. The whole note is wider than a head with
    a stem, so it shows past the filled head at the right. Such a hollow oval gives the stem back. Returns how many."""
    space = layers['space']
    near, apart, edge, wider = (value * space for value in WHOLE_BESIDE)
    heads = [mark for mark in marks if mark['kind'] == 'head' and mark['stems']]
    count = 0
    for mark in heads:
        wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
        if mark['hole'] < limit or mark.get('solid_cy') is not None or wide < WHOLE[0] * high:
            continue
        for stem in list(mark['stems']):
            up = stem['direction'] == 'up'
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
            for other in heads:
                if other is mark or (other['cy'] > mark['cy']) == up:
                    continue      # the other head stands between the oval and the far end of the stem
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
    return count


def read_symbols(layers: dict) -> dict:
    """The symbols of the page: {'heads': [...], 'signs': [...], 'marks': [...]}.

    Each head: its box and middle, 'staff' (index into layers['staves']), 'place' (pitch place, a number with a
    fraction), 'hollow', and 'stems': one for each stem that it has (two for a head that two voices share, none for a
    whole note), each {'direction', 'x', 'end', 'length'}. Each sign is a sharp, a flat or a natural: its box,
    'kind', 'staff', 'place' and 'count' (two sharps that touch are one mark)."""
    space = layers['space']
    marks = thick_marks(layers)
    for mark in marks:
        wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
        mark['stems'] = []
        mark['kind'] = None
        if not (0.3 * space <= wide <= HEAD_WIDE[1] * space and HEAD_HIGH[0] * space <= high <= 2.4 * space):
            continue
        mark['ways'] = {f"{'up' if up else 'down'}_{'right' if right else 'left'}": _way(layers, mark, up, right)
                        for up in (True, False) for right in (True, False)}
        mark['kind'] = _kind(mark, space)
        if WORD_MARKS and mark['kind'] and _in_words(layers, mark):
            mark['kind'] = None       # a letter of the words
        # A beam hangs on two stems that leave it the same way, one at each end. (Right over the words, the two are
        # letters under a head. Under the words a slur hangs on two letters, and that is no head.)
        ways = mark['ways']
        for left, right in (('down_left', 'down_right'), ('up_left', 'up_right')):
            if is_stem(ways[left], space) and is_stem(ways[right], space) and ways[right]['x'] - ways[left]['x'] >= space \
                    and not (WORD_STEM and left == 'down_left' and _into_words(layers, mark, ways[left])
                             and _into_words(layers, mark, ways[right]) and _at_staff(layers, mark)):
                mark['kind'] = 'beam' if mark['kind'] == 'head' else mark['kind']
        if mark['kind'] == 'head':
            for name in ('up_right', 'down_left'):
                if is_stem(mark['ways'][name], space):
                    mark['stems'].append(mark['ways'][name])
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
    if FLAG_LOOP:
        for mark in marks:
            if mark['kind'] == 'head' and mark['hole'] >= HOLLOW and mark.get('solid_cy') is None \
                    and _flag_loop(layers, marks, mark):
                mark['kind'] = 'loop'
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
    if RIM_STEM:
        # Two whole notes a third apart touch, and the side of the one is upright ink that leaves the other. But a
        # stem goes on past the heads that hang on it: upright ink that ends in the box of another head is its rim.
        heads = [mark for mark in marks if mark['kind'] == 'head']
        for mark in heads:
            for stem in list(mark['stems']):
                if any(other is not mark and other['blob'] == mark['blob']
                       and other['x0'] - 2 <= stem['x'] <= other['x1'] + 2
                       and other['y0'] - RIM_STEM * space <= stem['end'] <= other['y1'] + RIM_STEM * space
                       and (other['cy'] < mark['cy']) == (stem['direction'] == 'up') for other in heads):
                    mark['stems'].remove(stem)
    _share_stems(marks, space)
    if TWO_HEADS:
        split = []
        for mark in marks:
            parts = _two_heads(layers, mark) if mark['kind'] == 'head' and len(mark['stems']) == 2 else None
            split += parts or [mark]
        marks = split
    # The page teaches how large the holes of its hollow heads are. A heavy print leaves a slit of a hole, and there
    # a smaller hole is a hole too.
    limit = HOLLOW
    if HOLLOW_PAGE:
        sure = [mark['hole'] for mark in marks if mark['kind'] == 'head' and mark['stems'] and mark['hole'] >= HOLLOW]
        if len(sure) >= 5:
            limit = min(HOLLOW, max(HOLLOW_PAGE[1], HOLLOW_PAGE[0] * float(np.median(sure))))
            if HOLLOW_WORN and float(np.median(sure)) >= HOLLOW_WORN[1]:
                # A print that pressed the ink out of the middle of its filled heads leaves a pale speck there. On a
                # page whose hollow heads have large holes, such a speck is no hole.
                limit = max(limit, HOLLOW_WORN[0] * float(np.median(sure)))
    layers['hollow'] = limit
    if WHOLE_BESIDE:
        _whole_beside(layers, marks, limit)
    heads, signs, orphans = [], [], []
    for number, mark in enumerate(marks):
        if mark['kind'] is None or mark['kind'] == 'beam':
            continue
        staff = _staff_of(layers, mark['cx'], mark['cy'])
        if staff is None:
            continue
        hollow = mark['hole'] >= limit
        cy = mark['hole_cy'] if HOLE_PLACE and hollow and mark['hole_cy'] is not None else mark['cy']
        or_hollow = None
        orphan = False
        if hollow and mark.get('solid_cy') is not None and mark['stems']:
            or_hollow = cy
            hollow, cy = False, mark['solid_cy']
        if LINE_SLIT and not hollow and or_hollow is None and mark['kind'] == 'head' and mark['stems'] \
                and _line_slit(layers, mark, layers['staves'][staff]):
            hollow = True
        place = pitch_place(layers['staves'][staff], cy)
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
            if WHOLE_FILLED and not hollow and oval and 'tail_of' not in mark and any(
                    other is not mark and other['blob'] == mark['blob'] and other['kind'] == 'head' and not other['stems']
                    and other['hole'] >= limit and lying(other) and abs(other['cx'] - mark['cx']) <= WHOLE_FILLED * space
                    and min(abs(other['y0'] - mark['y1']), abs(mark['y0'] - other['y1'])) <= 0.3 * space for other in marks):
                hollow = True       # the print filled the hole of a whole note that touches the whole note of the other voice
            elif not (hollow and oval and 'tail_of' not in mark and _rim(layers, mark) >= RIM):
                # A mark as large as a head with no stem: the copy may have cut its stem off (see lost_stems()).
                if not (ORPHANS and 'tail_of' not in mark
                        and ORPHANS[0] * layers['head'][0] <= wide <= ORPHANS[1] * layers['head'][0]
                        and ORPHANS[0] * layers['head'][1] <= high <= ORPHANS[1] * layers['head'][1]):
                    continue
                orphan = True
        head = {'x0': mark['x0'], 'y0': mark['y0'], 'x1': mark['x1'], 'y1': mark['y1'], 'cx': mark['cx'], 'cy': cy,
                'staff': staff, 'place': place, 'hollow': hollow, 'hole': mark['hole'], 'stems': mark['stems'],
                'mark': number, 'core': core_light(layers, mark),
                'alt': dict(_places(layers['staves'][staff], mark), **_fat(layers, mark))}
        if mark.get('loop'):
            head['loop'] = mark['loop']
        if mark.get('room'):
            head['room'] = True
        if or_hollow is not None:
            head['or_hollow'] = or_hollow
        if abs(place) > 4 + 2 * REACH:
            continue
        if abs(place) > 4.6:
            head['ledgers'] = ledger_lines(layers, layers['staves'][staff], head)
            found = ledger_place(layers, layers['staves'][staff], head)
            if found is None or (not head['ledgers'] and abs(place) > max(5.6, NO_LEDGER)):
                # A faint ledger line is lost in the copy. A letter of the words has a bowl and a stem too, but its
                # stem is short: a head as large as the heads of the page on a long stem is a note.
                wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
                if not (FAR_STEM and found is not None and abs(place) <= FAR_STEM[1] and not mark.get('word_stem')
                        and any(stem['past'] >= FAR_STEM[0] * space for stem in mark['stems'])
                        and FAR_STEM[2] * layers['head'][0] <= wide <= FAR_STEM[3] * layers['head'][0]
                        and FAR_STEM[2] * layers['head'][1] <= high <= FAR_STEM[3] * layers['head'][1]):
                    continue
            head['place'] = found
        (orphans if orphan else heads).append(head)
    return {'heads': heads, 'signs': signs, 'marks': marks, 'orphans': orphans}


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
OPEN_ALONE = 0       # an open hole with a stem and no piece of rim that was read as a head is a hollow head when ink of
#                    its own (no staff line) stands at this share of the ring around it: the thin rim of a printed
#                    half note is no thick mark at all (0: off). Off: with 0.5 it gained 29 notes on LitChoir's
#                    clean copies and lost 5, but on the fresh test set it lost 285.
OPEN_SLANT = (0.8, 0.75)   # such a hole may be as high as wide (from this share) when it fills at most this share of its box
OPEN_PIECE = 0.75    # a piece of a broken rim is lower than this share of the height of the page's heads
HOLE_THROUGH = True  # a hollow head on a staff line: the two halves of its inside, over and under the line, are one hole
HOLE_RIM = 0.2       # the rim of such a head is this thick, in staff spaces
HOLE_CELL = 0.85     # a hole in a space of the staff that is this share of the gap between two staff lines high is a cell
HOLE_CLOSED = 0.6    # past its rim, paper shows at the left and at the right within this many staff spaces


def hole_heads(layers: dict, heads: list[dict], ends: list[float]) -> list[dict]:
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
    own = []
    for head in heads:
        if head['hollow'] and not head.get('thin'):
            own.append(float((holes[head['y0']:head['y1'] + 1, head['x0']:head['x1'] + 1] > 0).sum()))
    if len(own) < 3:
        return []
    usual = float(np.median(own))
    rim = max(2, int(round(HOLE_RIM * space)))
    far = int(round(HOLE_CLOSED * space))
    out = []
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
    if OPEN_HEADS and layers.get('open_holes') is not None:
        passes.append((True, layers['open_holes'], None))
    for is_open, paper, through in passes:
        count, labels, stats, centres = cv2.connectedComponentsWithStats((paper > 0).astype(np.uint8), connectivity=4)
        for index in range(1, count):
            x, y, wide, high, area = (int(value) for value in stats[index])
            cx, cy = float(centres[index][0]), float(centres[index][1])
            if through is not None and not through[y:y + high, x:x + wide][labels[y:y + high, x:x + wide] == index].any():
                continue      # a hole that no line cuts was looked at before
            most = HOLE_HEADS[1] * usual
            if is_open:
                # A head whose rim broke is often one that a hand drew large: its hole may be larger than the usual
                # hole of the page.
                most = OPEN_HEADS * space * space
            if not HOLE_HEADS[0] * usual <= area <= most:
                continue
            if wide < HOLE_HEADS[2] * high:
                # A printed half note with a thin rim fills the gap between two staff lines: its inside is a slanted
                # oval that is as high as wide, and fills little of its box.
                if not (is_open and OPEN_ALONE and wide >= OPEN_SLANT[0] * high and area <= OPEN_SLANT[1] * wide * high):
                    continue
            if not HOLE_HEADS[3] <= area / (wide * high) <= HOLE_HEADS[4]:
                continue
            inside = [head for head in heads + out
                      if head['x0'] - 2 <= cx <= head['x1'] + 2 and head['y0'] - 2 <= cy <= head['y1'] + 2]
            if any(head.get('loop') and head['loop'][0] - 2 <= cx <= head['loop'][2] + 2
                   and head['loop'][1] - 2 <= cy <= head['loop'][3] + 2 for head in heads):
                continue      # a room of the loop of a flag
            if inside if not is_open else any(head['hollow'] for head in inside):
                continue
            staff = _staff_of(layers, cx, cy)
            if staff is None or cx < ends[staff] + 0.3 * space:
                continue
            place = pitch_place(layers['staves'][staff], cy)
            if abs(place) > HOLE_HEADS[5]:
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
                if seen == 0 or seen > far:
                    closed = False
            if not closed:
                continue
            mark = {'x0': max(0, x - rim), 'x1': min(ink.shape[1] - 1, x + wide - 1 + rim), 'y0': max(0, y - rim),
                    'y1': min(ink.shape[0] - 1, y + high - 1 + rim), 'cx': cx, 'cy': cy}
            stems = [way for way in (_way(layers, mark, True, True), _way(layers, mark, False, False)) if is_stem(way, space)]
            head = {'x0': mark['x0'], 'y0': mark['y0'], 'x1': mark['x1'], 'y1': mark['y1'], 'cx': cx, 'cy': cy,
                    'staff': staff, 'place': place, 'hollow': True, 'hole': area / ((wide + 2 * rim) * (high + 2 * rim)),
                    'stems': stems, 'mark': None, 'from_hole': True, 'core': None, 'alt': None}
            if is_open:
                # The pieces of the broken rim: the heads that were read in the box of this one. An open hole with
                # no such piece is the hook of a rest, or the paper between two signs.
                head['replaces'] = [other for other in heads
                                    if mark['x0'] <= other['cx'] <= mark['x1'] and mark['y0'] <= other['cy'] <= mark['y1']]
                head['open'] = True
                if not stems:
                    continue
                if not head['replaces']:
                    if not OPEN_ALONE:
                        continue
                    y0, x0 = max(0, y - 3), max(0, x - 3)
                    own = (labels[y0:y + high + 3, x0:x + wide + 3] == index).astype(np.uint8)
                    ring = cv2.dilate(own, np.ones((7, 7), np.uint8)) & (1 - own)
                    if (ring & layers['bare'][y0:y + high + 3, x0:x + wide + 3]).sum() < OPEN_ALONE * ring.sum():
                        continue
                # A piece of rim is lower than a head. A whole head beside the paper is a note of its own: the paper
                # is closed in between two heads a second apart.
                if any(other['y1'] - other['y0'] + 1 >= OPEN_PIECE * layers['head'][1] and not other.get('thin')
                       for other in head['replaces']):
                    continue
            if abs(place) > 4.6:
                # Beside the staff a head lies on its ledger lines. The letter p of the words has a bowl and a stem too.
                head['ledgers'] = ledger_lines(layers, layers['staves'][staff], head)
                found = ledger_place(layers, layers['staves'][staff], head)
                if found is None or not head['ledgers']:
                    continue
                head['place'] = found
            out.append(head)
    return out


# ----------------------------------------------------------------------------------------------------------------
# Heads that a hand drew as one thin stroke

THIN_WIDE = (0.55, 2.6)    # the width of a head drawn as one stroke, in staff spaces
THIN_HIGH = (0.2, 1.3)     # and its height
THIN_NEAR = 1.3            # the head lies at most this many staff spaces from the end of its stem
THIN_HOLLOW = 0.15         # such a head is hollow when its ink goes around this share of its box
LOOP_LINE = True           # an open oval may have a staff line as its upper or lower side
OPEN_HOLE = 0.12           # the open hole of such a head has at least this area, in staff spaces squared (0: off)
TWO_STEMS = True           # a thick head with two stems may give one of them to a thin head of the other voice
TWO_ALONG = 1.0            # that thin head hangs anywhere on the stem, up to this many staff spaces before its far end (0: off)
TWO_APART = True           # and it may touch the thick head: the thick head's own ink is no part of it
THIN_LEDGER = 0.3          # a ledger line is at most this thick, in staff spaces: a thin head on it is higher (0: off)
LINE_REST = 0.6            # a piece no higher than a staff line is a rest of the line when less than this share is its own ink (0: off)
ONE_ALONG = 1.0            # on the one stem of a thick head too, when it lies this many staff spaces from that head (0: off)
ALONG_HIGH = 0.4           # such a thin head is at least this high, in staff spaces: the rest of a staff line is flat
OPEN_RIM = 0.5             # an open hole has the head's own ink at this share of its rim (0: off)
LOOP_STEM = True           # an open oval may have its stem as one of its sides
THROUGH_SLANT = (0.5, 1.0) # a thin head that crosses a staff line at a low slant: its part over the line stands up to this
#                            many staff spaces right of its part under the line, and each part is at most this wide and
#                            high (None: off)
THIN_INSIDE = 0.5          # when the stem runs inside the piece of ink of a thin head, the head's middle lies up to this
#                            share of the piece's height before the stem's end (0: off)
THIN_BACK = 0.25           # the middle of a thin head lies at most this many staff spaces before the end of its stem
LOOP_BACK = 0.5            # the middle of an open oval lies up to this share of its height before the end of its stem
THIN_STEM = 1.6            # the stem of such a head is at least this many staff spaces long
LOST_STEM = (0.3, 0.45)    # a stem that the copy cut from its thick head stands at most this far past the head's edge
                           # (staff spaces, sideways) and ends at most this far from the head (None: off)
LOST_ALONE = (0.4, 0.6)    # the same for a mark with no stem at all: it lost its only stem, and the cut may be wider
THROUGH_SIDE = 0.05        # a thin head that crosses a staff line is one piece: its ink over and under the line is joined
                           # through the line, up to this many staff spaces sideways
LEAN_END = 0.4             # a stem that leans toward its thin head: the head's distance is counted from the stem's end, when
#                            that end lies at most this many staff spaces from the stem's middle column (0: off)
THIN_PAIR = 1.3            # two thin heads, one over the other: the stem of the one runs on into the other, so its own
                           # head lies up to this many staff spaces before the stroke's end (0: off)


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
            if not any(stem['direction'] == 'up' for stem in head['stems']) and bottom <= head['cy']:
                ways.append(('up', x - head['x1'], head['y0'] - bottom, top))
            if not any(stem['direction'] == 'down' for stem in head['stems']) and top >= head['cy']:
                ways.append(('down', head['x0'] - x, top - head['y1'], bottom))
            # A mark with no stem at all has lost its only stem: the cut may be wider there.
            reach = LOST_ALONE if LOST_ALONE and not head['stems'] else LOST_STEM
            for direction, aside, apart, end in ways:
                if -0.25 * space <= aside <= reach[0] * space and apart <= reach[1] * space:
                    far = abs(aside) + max(0.0, apart)
                    if best is None or far < best[0]:
                        best = (far, head, direction, end)
        if best:
            _, head, direction, end = best
            if not any(head is other for other in heads):
                heads.append(head)
            head['stems'].append({'direction': direction, 'x': int(round(x)), 'end': int(end), 'length': abs(head['cy'] - end),
                                  'lost': True})
            used.append((x, min(head['cy'], end), max(head['cy'], end)))
            given += 1
    return given


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
        pieces.append({'x0': int(x), 'y0': int(y), 'x1': int(x + wide - 1), 'y1': int(y + high - 1), 'area': int(area),
                       'cx': cx, 'cy': cy,
                       'hole': max(float((layers['holes'][y:y + high, x:x + wide] > 0)[part].sum()) / area, loop)})
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
        asks.append((x, top, bottom, staff, owners, False, (float(stroke['xs'][0]), float(stroke['xs'][-1]))))
    if TWO_ALONG:
        # The stems of a head with two stems that are no stroke of their own: the stem up, the head and the stem
        # down were one long stroke, or the ink that leaves the head is the thin head itself.
        for head in two:
            for stem in head['stems']:
                if id(stem) not in matched:
                    asks.append((stem['x'], min(head['cy'], stem['end']), max(head['cy'], stem['end']), head['staff'],
                                 [(head, stem)], True, None))
        if ONE_ALONG:
            # A head with one stem: the thin head of the other voice can hang on that same stem, farther along. The
            # ink that leaves the thick head is then the other voice's stem, and the two heads share it as a chord.
            for head in heads:
                if len(head['stems']) == 1 and not any(head is other for other in two):
                    stem = head['stems'][0]
                    asks.append((stem['x'], min(head['cy'], stem['end']), max(head['cy'], stem['end']), head['staff'],
                                 [(head, stem)], True, None))
    found = []
    flags = {}

    def flagged(owner: dict, stem: dict) -> bool:
        # A printed flag comes back along its stem and closes in paper there: that is no head of another voice.
        if id(stem) not in flags:
            hung = tail_marks(layers, dict(owner, staff_ref=staves[owner['staff']]), stem)
            flags[id(stem)] = any(piece['right'] and piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6
                                  and piece['from_end'] <= FLAG_END for piece in hung)
        return flags[id(stem)]

    def make_head(piece: dict, direction: str, x: float, end: float, staff: int) -> dict | None:
        place = pitch_place(staves[staff], piece['cy'])
        head = {'x0': piece['x0'], 'y0': piece['y0'], 'x1': piece['x1'], 'y1': piece['y1'], 'cx': piece['cx'], 'cy': piece['cy'],
                'staff': staff, 'place': place, 'hollow': piece['hole'] >= THIN_HOLLOW, 'hole': piece['hole'], 'thin': True,
                'stems': [{'direction': direction, 'x': int(round(x)), 'end': int(end), 'length': abs(piece['cy'] - end)}]}
        if abs(place) > 4 + 2 * REACH:
            return None
        if abs(place) > 4.6:
            head['ledgers'] = ledger_lines(layers, staves[staff], head)
            place = ledger_place(layers, staves[staff], head)
            if place is None or (not head['ledgers'] and abs(head['place']) > max(5.6, NO_LEDGER)):
                return None
            head['place'] = place
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
    for x, top, bottom, staff, owners, whole, leans in asks:
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
                    back = THIN_BACK * space + (LOOP_BACK * (piece['y1'] - piece['y0'] + 1) if piece['hole'] >= THIN_HOLLOW else 0.0)
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
        if head is not None:
            found.append(head)
            if not owners:
                asked[id(head)] = (x, top, bottom, direction)
    return found


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
LOOP_NEAR = 1.8      # the loop of a flag lies at most this many staff spaces from the far end of the stem
FLAG_BACK = 0.08     # a printed flag comes back toward the head by this many staff spaces while it leaves the stem
FLAG_NARROW = (0.6, 0.2)   # a narrow printed flag hugs its stem: it reaches under 0.6 staff spaces from it, but it is
#                            this many staff spaces high and leans this much toward the head (None: off). A limit on
#                            how long it touches the stem was measured too: it lost 11 notes for 4.
DOT_REACH = 1.3      # a dot stands at most this many staff spaces right of its head
DOT_NEAR = 0.3       # and at least this many
DOT_UNDER = 0.6      # its middle lies at most this many staff spaces under the middle of the head (and 0.7 over it)
DOT_BETWEEN = None   # and not from this to this many staff spaces under it: a dot stands in a space, at the height of
#                    the head or half a staff space from it (None: off)
DOT_HIGH = 0.9       # a dot is at most this high, in staff spaces
DOT_SLIM = 0.38      # and at least this wide for its height: a hand draws a dot as a short stroke
SHARED_TAILS = True  # a head with two stems has the flags of its one stem at the other stem too
TAIL_START = 0.55    # the hook of a flag begins this near to the end of its stem, in staff spaces
THIN_BEAM = (0.2, 0.85, 0.6)    # a beam that a hand drew as one thin line from the end of a stem to the end of the next:
                                # ink at most this far (staff spaces) from the straight line, on this share of the way
                                # with the staff lines it crosses, and on this share without them (None: off)
THIN_BEAM_ENDS = 0.3            # and it has its ink in the first and the last part of the way, this long (0: off)
THIN_BEAM_UNDER = True          # at one of its ends the line may be hidden in a staff line
THIN_BEAM_FAT = 0.5             # a staff line that hides the beam is thicker there, by this share of its thickness (0: off)
THIN_BEAM_OVER = 0.6            # a thin beam passes over a stem between its two stems that ends this many staff spaces before it (0: off)
THIN_BEAM_STAFF = True          # the thickness of a staff line that hides a beam is that of the beam's own staff
THIN_BEAM_END = 0.0             # the beam may meet a stem this many staff spaces past the end that was found for it (0: off)
WORD_TAILS = True               # a letter beside the end of a stem that ends at the words is no slur that goes on past a
#                                 thin beam
WORD_BEAMS = False              # a beam in the rows of the words counts when the next stem shows it too (measured on the
#                                 clean copies: a slur over a beam at the words then counts as a second beam; kept off)
LAST_HEAD = 'words'             # the flags of a stem hang past the last head on it: 'words' (for a stem that ends at the
#                                 words), 'all' (for every stem), or None (past the stem's own head only)
THIN_BEAM_CHORD = True          # the stems of the heads of one chord are one stem for a thin beam (False: stems in fixed columns)
PAST_WORDS = True               # past the last stem of a thin beam, ink in the rows of the words is no slur that goes on
PAST_TWO = (0.3, 1.2, 0.7)      # two strokes one over the other before the last stem (from this far to this far before it, in
#                                 this many staff spaces around the beam's line) are a beam and a slur: the ink past the stem
#                                 is the slur's (None: off)
THIN_BEAM_PAST = (0.4, 1.0, 0.45)   # a slur goes on past the last stem: ink from this far to this far past it, at most
                                    # this far from the line (staff spaces; None: off)


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
        # The stem ends at the words (scoreread.words): the ink of the letters is no flag.
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


def _is_beam(piece: dict) -> bool:
    return bool(piece['thick'] >= TAIL_THICK and piece['far'] >= BEAM_FAR)


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

    def witness(group: list[dict], stem: dict, right: bool) -> bool:
        """True when the next stem at that side shows a beam at the side that faces this stem."""
        side = [other for other in group
                if 0.5 * space < (other['x'] - stem['x'] if right else stem['x'] - other['x']) <= BEAM_NEXT * space]
        if not side:
            return False
        near = min(side, key=lambda other: abs(other['x'] - stem['x']))
        return abs(near['end'] - stem['end']) <= 2.5 * space \
            and any(_is_beam(piece) and piece['right'] != right for piece in near['marks'] + near.get('in_words', []))

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
    for head in heads:
        head['tails'] = {}
        for stem in head['stems']:
            pieces = stem['marks']
            beams = [piece for piece in pieces if piece['beam']]
            alone = len({piece['right'] for piece in beams}) == 1
            rows = [piece['row'] for piece in beams
                    if piece['witness'] or (alone and usual is not None and piece['thick'] >= BEAM_USUAL * usual
                                            and (not BEAM_STRAIGHT or straight(groups[(head['staff'], stem['direction'])], stem, piece)))]
            short = [piece for piece in pieces if not piece['beam'] and piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6]
            # A printed flag; and beside a beam, the short second beam of a sixteenth.
            rows += [piece['row'] for piece in short if (piece['right'] and piece['back'] >= FLAG_BACK) or rows]
            if FLAG_NARROW and not rows:
                rows += [piece['row'] for piece in pieces
                         if piece['right'] and not piece['beam'] and piece['thick'] >= TAIL_THICK and piece['far'] < 0.6
                         and piece['high'] >= FLAG_NARROW[0] and piece['lean'] >= FLAG_NARROW[1]
                         and piece['from_end'] <= FLAG_END]
            levels = []
            for row in sorted(rows):
                if not levels or row - levels[-1] > 0.35 * space:
                    levels.append(row)
            if levels:
                head['tails'][stem['direction']] = min(len(levels), 3)
                continue
            thin = [piece for piece in pieces if not (piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6)]
            thin_left = [piece['row'] for piece in thin if not piece['right']]
            hooks = [piece['row'] for piece in thin if piece['right'] and piece['from_end'] <= TAIL_START and piece['back'] >= 0.12]
            hook = any(all(abs(row - other) > 0.25 * space for other in thin_left) for row in hooks)
            head['tails'][stem['direction']] = 1 if hook else 0
        if ROOM_HEADS and head.get('room'):
            # The room at such a head is closed by a flag or by a beam: the stem that goes along the room has one.
            x0, y0, x1, y1 = head['loop']
            for stem in head['stems']:
                along = y0 < head['y0'] - 0.5 * space if stem['direction'] == 'up' else y1 > head['y1'] + 0.5 * space
                if along and not head['tails'].get(stem['direction']):
                    head['tails'][stem['direction']] = 1
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
                if not THIN_BEAM_PAST or not (_goes_on(layers, run[1][0][1], run[0][0][1])
                                              or _goes_on(layers, run[-2][0][1], run[-1][0][1])):
                    for entry in run:
                        for head, stem in entry:
                            head['tails'][direction] = max(1, head['tails'].get(direction, 0))
                            stem['thin_beam'] = True
                first = last + 1
    for head in heads:
        if SHARED_TAILS and len(head['tails']) == 2:
            # One head with two stems is one note that two voices sing: a hand draws its flag at one stem only.
            most = max(head['tails'].values())
            head['tails'] = {direction: most for direction in head['tails']}


def _goes_on(layers: dict, inner: dict, outer: dict) -> bool:
    """True when the ink that runs from the end of the stem `inner` to the end of the stem `outer` goes on past
    `outer`, along the same line or bending away from it a little."""
    space = layers['space']
    ink = layers['bare']
    height, width = ink.shape
    side = 1 if outer['x'] > inner['x'] else -1
    slope = (outer['end'] - inner['end']) / (outer['x'] - inner['x'])
    reach = int(round(THIN_BEAM_PAST[2] * space))
    seen = count = 0
    for step in range(int(round(THIN_BEAM_PAST[0] * space)), int(round(THIN_BEAM_PAST[1] * space)) + 1):
        x = int(round(outer['x'])) + side * step
        y = int(round(outer['end'] + slope * side * step))
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
        seen += bool(ink[top:bottom, x].any())
    if PAST_TWO and count > 0 and seen >= 0.6 * count and _two_strokes(layers, inner, outer):
        return False
    return count > 0 and seen >= 0.6 * count


def _two_strokes(layers: dict, inner: dict, outer: dict) -> bool:
    """True when two strokes, one over the other, run to the end of the stem `outer` from the side of `inner`: a
    beam and a slur beside it. The ink that goes on past the stem is then the slur's, and the beam ends at the stem."""
    space = layers['space']
    ink = layers['bare']
    height, width = ink.shape
    side = 1 if outer['x'] > inner['x'] else -1
    slope = (outer['end'] - inner['end']) / (outer['x'] - inner['x'])
    reach = int(round(PAST_TWO[2] * space))
    two = count = 0
    for step in range(int(round(PAST_TWO[0] * space)), int(round(PAST_TWO[1] * space)) + 1):
        x = int(round(outer['x'])) - side * step
        y = int(round(outer['end'] - slope * side * step))
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
    if not THIN_BEAM_END:
        return _beam_line(layers, one['x'], one['end'], two['x'], two['end'])
    # A weak copy breaks a stem just before its beam: the stem that was found ends too early. The beam may meet
    # the stem a little past that end.
    def ends(stem: dict) -> list[float]:
        away = -1 if stem['direction'] == 'up' else 1
        return [stem['end'] + away * step for step in range(0, int(round(THIN_BEAM_END * space)) + 1, 2)]
    return any(_beam_line(layers, one['x'], first, two['x'], last) for first in ends(one) for last in ends(two))


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
    if THIN_BEAM_ENDS:
        first, last = 2 * sum(shown[:near]) >= near, 2 * sum(shown[-near:]) >= near
        if THIN_BEAM_UNDER:
            # A beam that runs into a staff line at one stem is hidden there: it is seen at the other stem.
            first, last = first or (last and 2 * sum(under[:near]) >= near), last or (first and 2 * sum(under[-near:]) >= near)
        if not (first and last):
            return False
    return seen + hidden >= THIN_BEAM[1] * count and seen >= THIN_BEAM[2] * count


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
    return [head for head in heads if id(head) not in gone]


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


def dots(layers: dict, heads: list[dict]) -> None:
    """Sets head['dot'] to True where a dot stands at the right of a head: a small round mark in the space beside it."""
    space = layers['space']
    # The dots of two voices stand one over the other, and the joining of dashes makes one upright stroke of them:
    # so the dots are looked for in the ink itself, not in the marks that are left without the strokes.
    count, labels, stats, centres = cv2.connectedComponentsWithStats(layers['bare'], connectivity=8)
    found = []
    for index in range(1, count):
        x, y, wide, high, area = stats[index]
        if not (0.14 * space <= wide <= 0.6 * space and 0.14 * space <= high <= DOT_HIGH * space):
            continue
        if area < 0.55 * wide * high or not DOT_SLIM <= wide / high <= 1.7:
            continue
        found.append((float(centres[index][0]), float(centres[index][1])))
    for head in heads:
        head['dot'] = False
        for x, y in found:
            if DOT_NEAR * space <= x - head['x1'] <= DOT_REACH * space and -0.7 * space <= y - head['cy'] <= DOT_UNDER * space \
                    and not (DOT_BETWEEN and DOT_BETWEEN[0] * space <= y - head['cy'] < DOT_BETWEEN[1] * space):
                head['dot'] = True
                break
        if not head['dot'] and LEDGER_DOT and abs(head['place']) > 4.6:
            # A hand draws the ledger line through the head and on to the right, and sets the dot at its end or
            # past its end.
            end, blob = _ledger_end(layers, head)
            if end >= head['x1'] + LEDGER_DOT[2] * space:
                head['dot'] = blob or any(0.1 * space <= x - end <= LEDGER_DOT[1] * space
                                          and abs(y - head['cy']) <= 0.7 * space for x, y in found)


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

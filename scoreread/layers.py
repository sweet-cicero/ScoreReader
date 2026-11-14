"""Splits the ink of a clean page into layers: staff lines, upright strokes, thick marks and the rest. No model is used.

A page is hard to read as one picture and easy to read as layers. On a clean page (scoreread.page) every staff line
is level and its row is known, so each layer comes from a plain measure of the ink:

1. Ink: the dark pixels of the page.
2. Holes: paper that ink closes in, when it is as small as the inside of a hollow note head. A cell between two
   staff lines and two upright strokes has straight sides, and it is left out. The holes are filled, so a hollow head
   and a filled head are both a solid mark from here on, and the hole says later which of the two it was.
3. Staff lines: the ink in the rows of each staff line, where nothing stands on the line. The test is the height of
   the ink in that column: a line alone is as high as the line is thick, and a line with a note on it is higher.
4. Upright strokes: ink that stands at least 1.6 staff spaces high in one column, also when it leans a little or a
   weak copy broke it into dashes. Stems and bar lines are upright strokes.
5. Thick marks: what stays after the staff lines and the thin part of each upright stroke are taken away, and a
   round brush as wide as a third of a staff space still fits in. Note heads, beams and the heavy parts of clefs and
   rests are thick marks; words, slurs and ledger lines are thinner.

picture() gives each layer its own colour, so a person can check a page at a glance.
"""
from __future__ import annotations

import cv2
import numpy as np

from .staves import ink_mask

UPRIGHT = 1.3        # the least height of an upright stroke, in staff spaces
LEAN = (0.0, 0.06, -0.06, 0.12, -0.12)   # the leans (dx/dy) an upright stroke may have
DASH_GAP = 0.5       # a gap of this many staff spaces in a thin upright stroke is bridged
SLIM = 0.62          # an upright stroke at most this wide (in staff spaces) is a stem or a bar line
STEM_USUAL = (2.2, 1.8)   # a stroke under this height (staff spaces) is no stem when it is this many times as wide as
                          # the page's long strokes (None: off)
STEM_OWN = 0.25      # a slim stroke that is much wider than the page's stems, but has this share of rows as thin as
#                      they are: its thin rows are the stem, and its wide rows are heads that stand one over the other
#                      on it (two voices a third apart, each with a short stem to its own beam). None: off
BRUSH = 0.32         # the round brush for thick marks, in staff spaces
HOLE = (1.2, 1.0, 1.7)   # a head's hole: at most this area (spaces squared), height and width (spaces)
HOLE_SIDE = (1.1, 0.7, 2.0, 4.5)   # closed paper this many staff spaces wide or more is a cell of the staff, and no
#                    inside of a head, when one of its ends is straight (the outer tenth of its columns is this share
#                    of its height or more) and lies against an upright stroke this many staff spaces long or more:
#                    the paper between two staff lines, a bar line or a stem, and the round side of a head. Not in
#                    the first staff spaces of a staff (this many): the clef is known with the paper that it closes
#                    in against the line at the left end of the staff. (None: off)
WHOLE_INSIDE = (0.33, 0.3, 0.8, 2.4, 1.5)
#                    The inside of a printed whole note is an upright oval, nearly as high as a cell of the staff in its
#                    middle columns. But paper fills less than this share of its four corners (the whole note of a
#                    heavy print has 5 of 16 corner pixels, 0.31; the flat of a key signature has 0.36 or more); the
#                    sides of the note at its left and at its right are both from this to this many staff spaces
#                    thick, and as upright
#                    ink they are at most this many staff spaces long (two whole notes, one over the other): a stem
#                    or a bar line at the side of a cell is longer. The inside is at most this many times as high as
#                    wide. (None: off)
HOLE_GAP = 0.2       # a break of up to this many staff spaces in the rim of a hollow head is closed for the open holes
ROUND = 0.85         # the inside of a head fills at least this share of its hull: it has no dent
HOLE_LINE = 0.5      # two pieces of an inside that a staff line cut stand over each other for this share of the
                     # smaller one's width (0: off)
LINE_ROUND = 0.6     # and with the line between them they fill this share of their hull
LINE_WIDE = 1.2      # such a piece may be this many times as wide and as large as HOLE allows
HOLE_NECK = 0.05     # a staff line that is faint inside a head leaves the two pieces of the inside joined by a neck
                     # (0: off): with the neck filled in the line's rows (this share of the piece or more) the piece
                     # fills LINE_ROUND of its hull; at least this share of it lies over the line and as much under it
CROSS = 0.2          # a mark goes through a staff line when its ink over and under the line is this near, sideways
WEAK = (0.05, 0.2)   # the share of long strokes with gaps: a whole copy has at most the first, a weak copy the second
WHOLE_GAP = 0.3      # on a whole copy, the gaps that are bridged are this share of the gaps bridged on a weak copy
BLOT = 1.8           # solid ink that a disc of this many staff spaces fits in is a blot, not music


def line_thickness(ink: np.ndarray, rows: list[float], x0: int, x1: int) -> float:
    """The thickness of a staff's lines in px: the median height of the ink in the lines' rows."""
    runs = []
    height = ink.shape[0]
    for row in rows:
        row = int(round(row))
        if row - 12 < 0 or row + 13 > height:
            continue
        for x in range(int(x0) + 20, int(x1) - 20, 7):
            column = ink[row - 12:row + 13, x]
            near = np.where(column[10:15])[0]
            if len(near) == 0:
                continue
            centre = 10 + int(near[np.argmin(np.abs(near - 2))])
            first = centre
            while first > 0 and column[first - 1]:
                first -= 1
            last = centre
            while last < 24 and column[last + 1]:
                last += 1
            runs.append(last - first + 1)
    return float(np.median(runs)) if runs else 3.0


def blots(ink: np.ndarray, space: float) -> np.ndarray:
    """1 on the blots of the page: solid ink that a disc of BLOT staff spaces fits in, with the ink at its rim. A
    punch hole, the shadow of a binding or a torn corner is a blot; no mark of music is that solid."""
    size = int(round(BLOT * space)) | 1
    solid = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    if not solid.any():
        return solid
    rim = int(round(0.5 * space)) | 1
    return cv2.dilate(solid, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (rim, rim)))


def _whole_inside(ink: np.ndarray, part: np.ndarray, x: int, y: int, space: float) -> bool:
    """True when closed paper that is as high as a cell of the staff is the inside of a printed whole note (see
    WHOLE_INSIDE). `part` is the paper in its box, at (x, y) of the page."""
    if not WHOLE_INSIDE:
        return False
    corner, thin, thick, long, tall = WHOLE_INSIDE
    height, width = part.shape
    if height > tall * width:
        return False
    edge = max(2, int(round(0.15 * min(width, height))))
    corners = (part[:edge, :edge].mean() + part[:edge, -edge:].mean()
               + part[-edge:, :edge].mean() + part[-edge:, -edge:].mean()) / 4
    if corners >= corner:
        return False
    middle = y + height // 2
    row = ink[middle]
    columns = np.nonzero(part[height // 2])[0]
    if len(columns) == 0:
        return False
    left, right = x + int(columns[0]) - 1, x + int(columns[-1]) + 1
    first = left
    while first >= 0 and row[first]:
        first -= 1
    last = right
    while last < len(row) and row[last]:
        last += 1
    for side, column in ((left - first, (left + first + 1) // 2), (last - right, (right + last - 1) // 2)):
        if not thin * space <= side <= thick * space:
            return False
        upright = ink[:, column]
        top = bottom = middle
        while top >= 0 and upright[top]:
            top -= 1
        while bottom < len(upright) and upright[bottom]:
            bottom += 1
        if bottom - top - 1 > long * space:
            return False
    return True


def head_holes(ink: np.ndarray, space: float, line: float = 0.0, rows: list[float] | None = None,
               clefs: list[tuple[float, float, float, float]] | None = None) -> np.ndarray:
    """1 where paper is closed in by ink and can be the inside of a hollow note head.

    The inside of a head is round: it has no dent. Paper that is closed in between two marks has one. A sharp or a
    natural before a head closes in the paper between them, and so do two heads side by side: that paper is wide at
    the staff lines and narrow at its middle, where the head bulges into it. A cell between two staff lines and two
    upright strokes has no dent, but it has straight sides, and it is left out too.

    A thick staff line through a head that a hand drew cuts its inside into two pieces, and each piece has a dent
    where the line is. With `line` (the thickness of the staff lines in px), two such pieces, one over the other
    with a band of ink as thick as a line between them, are one inside when the two and the band are round together.
    With `rows` (the rows of the page's staff lines), a line that is faint inside a head is seen too: _necked().
    `clefs` are the boxes (first column, last column, first row, last row) where HOLE_SIDE does not hold."""
    lined = np.array(sorted(rows), float) if rows else None
    count, labels, stats, _ = cv2.connectedComponentsWithStats((1 - ink).astype(np.uint8), connectivity=4)
    keep = np.zeros(count, bool)
    dented = []
    for index in range(1, count):
        x, y, width, height, area = stats[index]
        more = LINE_WIDE if line and HOLE_LINE else 1.0
        if area < 6 or area > more * HOLE[0] * space * space or height > HOLE[1] * space or width > more * HOLE[2] * space:
            continue
        part = (labels[y:y + height, x:x + width] == index).astype(np.uint8)
        if height >= 0.6 * space and area >= 0.7 * width * height:
            # A cell between two staff lines and two upright strokes: it is as high as the gap between the lines in
            # most of its columns. The inside of a head is round, so few of its columns have the full height.
            if (part.sum(axis=0) >= 0.9 * height).mean() >= 0.5 and not _whole_inside(ink, part, x, y, space):
                continue
        if HOLE_SIDE and width >= HOLE_SIDE[0] * space and _straight_side(ink, part, x, y, space) \
                and not any(left <= x + width / 2 <= right and top <= y + height / 2 <= bottom
                            for left, right, top, bottom in clefs or []):
            continue
        dented.append(index)
        if area > HOLE[0] * space * space or width > HOLE[2] * space:
            continue
        if area >= 0.06 * space * space and not _round(part, area):
            if not (line and HOLE_NECK and lined is not None and _necked(part, area, line, y, lined)):
                continue
        keep[index] = True
    if line and HOLE_LINE:
        for upper in dented:
            ux, uy, uw, uh, ua = stats[upper]
            for lower in dented:
                lx, ly, lw, lh, la = stats[lower]
                gap = ly - (uy + uh)
                if lower == upper or (keep[upper] and keep[lower]) or not 1 <= gap <= line + 3:
                    continue
                x0, x1 = max(ux, lx), min(ux + uw, lx + lw)
                if x1 - x0 < HOLE_LINE * min(uw, lw) or ly + lh - uy > HOLE[1] * space \
                        or ua + la > LINE_WIDE * HOLE[0] * space * space:
                    continue
                if ink[uy + uh:ly, x0:x1].mean() < 0.9:
                    continue
                left, right = min(ux, lx), max(ux + uw, lx + lw)
                both = np.isin(labels[uy:ly + lh, left:right], (upper, lower)).astype(np.uint8)
                both[uh:uh + gap, x0 - left:x1 - left] = 1
                # The band takes the two pieces' own columns only: the staff line goes on at both sides.
                columns = both[:uh].any(axis=0) & both[uh + gap:].any(axis=0)
                both[uh:uh + gap] &= columns.astype(np.uint8)
                if _round(both, int(both.sum()), LINE_ROUND):
                    keep[upper] = keep[lower] = True
    return keep[labels].astype(np.uint8)


def _straight_side(ink: np.ndarray, part: np.ndarray, x: int, y: int, space: float) -> bool:
    """True when one end of a piece of closed paper is straight and lies against a long upright stroke (see
    HOLE_SIDE). `part` is the paper in its box, at (x, y) of the page."""
    share, long = HOLE_SIDE[1], HOLE_SIDE[2]
    height, width = part.shape
    columns = part.sum(axis=0)
    edge = max(1, int(round(0.1 * width)))
    middle = y + height // 2
    for straight, start, step in ((columns[:edge].mean() >= share * height, x, -1),
                                  (columns[-edge:].mean() >= share * height, x + width - 1, 1)):
        if not straight:
            continue
        column = next((start + step * far for far in range(1, 5)
                       if 0 <= start + step * far < ink.shape[1] and ink[middle, start + step * far]), None)
        if column is None:
            continue
        top = bottom = middle
        while top > 0 and ink[top - 1, column]:
            top -= 1
        while bottom < ink.shape[0] - 1 and ink[bottom + 1, column]:
            bottom += 1
        if bottom - top + 1 >= long * space:
            return True
    return False


def _necked(part: np.ndarray, area: int, line: float, top: int, rows: np.ndarray) -> bool:
    """True for the inside of a head that a faint staff line cuts nearly in two. The line's ink comes in from both
    sides and does not meet, so the inside is one piece of paper with a neck, and the neck is a dent. `rows` are
    the staff lines of the page and `top` is the row of the piece's first row. Where a staff line runs, the paper
    between two parts of the piece that stand over each other, at most as far apart as a line is thick, is the
    line: with it the piece is round."""
    high = int(round(line + 3))
    at = np.arange(top, top + part.shape[0])
    padded = np.pad(part, ((high, high), (0, 0)))
    closed = cv2.morphologyEx(padded, cv2.MORPH_CLOSE, np.ones((high + 1, 1), np.uint8))[high:-high]
    for row in rows[(rows > top) & (rows < top + part.shape[0] - 1)]:
        lined = np.abs(at - row) <= line / 2 + 2
        # The line goes through the piece: a good part of the paper lies over it and a good part under it.
        if min(part[at < row][~lined[at < row]].sum(), part[at > row][~lined[at > row]].sum()) < HOLE_NECK * area:
            continue
        filled = part | (closed & lined[:, None].astype(np.uint8))
        whole = int(filled.sum())
        if whole - area >= HOLE_NECK * area and _round(filled, whole, LINE_ROUND):
            return True
    return False


def _round(part: np.ndarray, area: int, least: float | None = None) -> bool:
    """True when a piece of paper fills its hull (ROUND of it, or `least`): it has no dent."""
    contours, _ = cv2.findContours(part, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    hull = cv2.convexHull(np.vstack(contours))
    # The hull runs through the middles of the rim's pixels: half a pixel is added all around it.
    full = cv2.contourArea(hull) + cv2.arcLength(hull, True) / 2 + 1
    return area >= (ROUND if least is None else least) * full


def staff_lines(solid: np.ndarray, staves: list[dict]) -> np.ndarray:
    """1 on the pixels of the staff lines that nothing else stands on."""
    out = np.zeros_like(solid)
    width = solid.shape[1]
    for staff in staves:
        thick = staff['thick']
        limit = int(round(thick + max(2.0, 0.5 * thick)))
        tall = cv2.morphologyEx(solid, cv2.MORPH_OPEN, np.ones((limit + 1, 1), np.uint8))
        thin = solid & (1 - tall)
        half = int(np.ceil(thick / 2 + 2))
        first, last = max(0, int(staff['x0'] - 1.5 * staff['space'])), min(width, int(staff['x1'] + 1.5 * staff['space']))
        for row in staff['rows']:
            row = int(round(row))
            out[max(0, row - half):row + half + 1, first:last] |= thin[max(0, row - half):row + half + 1, first:last]
    return out


def upright(ink: np.ndarray, length: int) -> np.ndarray:
    """1 where the ink stands at least `length` px high along a line that is upright or leans a little."""
    out = np.zeros_like(ink)
    for lean in LEAN:
        width = int(np.ceil(abs(lean) * length)) + 1
        kernel = np.zeros((length, width), np.uint8)
        for y in range(length):
            x = int(round(abs(lean) * y))
            kernel[y, x if lean >= 0 else width - 1 - x] = 1
        out |= cv2.morphologyEx(ink, cv2.MORPH_OPEN, kernel)
    return out


def read_layers(grey: np.ndarray, places: list[dict], no_holes: np.ndarray | None = None) -> dict:
    """The layers of a clean page. `places` is what clean_page() returns. The result holds the masks 'ink', 'holes',
    'solid' (ink and holes), 'lines', 'free' (solid without the staff lines), 'joined' (free with the dashes of thin
    strokes joined), 'up', 'stems' (the thin part of the slim upright strokes), 'marks' (free without stems) and
    'thick'; 'bare' (the ink without staff lines and without the filling of the holes); 'strokes' (see _strokes);
    'staves' (each staff: rows, x0, x1, space, thick, system, number, top, bottom) and 'space' (the page's staff
    space in px). `no_holes` is 1 on closed-in paper that a first reading of the page found to be no inside of a head
    (symbols.big_holes): it is not filled."""
    ink = ink_mask(grey)
    staves = []
    for system, place in enumerate(places):
        for number, (rows, (x0, x1)) in enumerate(zip(place['lines'], place['x'])):
            staves.append({'rows': [float(row) for row in rows], 'x0': int(x0), 'x1': int(x1),
                           'space': (rows[4] - rows[0]) / 4, 'thick': line_thickness(ink, rows, x0, x1),
                           'system': system, 'number': number, 'top': place['top'], 'bottom': place['bottom']})
    if not staves:
        raise ValueError('a page without staves has no layers')
    space = float(np.median([staff['space'] for staff in staves]))
    ink = ink & (1 - blots(ink, space))
    clefs = [(staff['x0'] - space, staff['x0'] + HOLE_SIDE[3] * space, staff['rows'][0] - 2 * space, staff['rows'][4] + 2 * space)
             for staff in staves] if HOLE_SIDE else None
    holes = head_holes(ink, space, max(staff['thick'] for staff in staves), [row for staff in staves for row in staff['rows']], clefs)
    # The rim of a hollow head can have a small break, in print and in a copy: the paper inside is closed in again
    # when the break is closed. These open holes are kept apart: they are asked only where a head is missing.
    size = int(max(3, round(HOLE_GAP * space))) | 1
    closed = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((size, 1), np.uint8)) \
        | cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((1, size), np.uint8))
    open_holes = head_holes(closed, space, clefs=clefs) & (1 - ink) & (1 - holes)
    if no_holes is not None:
        count, labels = cv2.connectedComponents(holes, connectivity=4)
        gone = np.isin(labels, np.unique(labels[(no_holes > 0) & (holes > 0)])) & (holes > 0)
        holes = holes & (1 - gone.astype(np.uint8))
        open_holes = open_holes & (1 - gone.astype(np.uint8))
    solid = ink | holes
    lines = staff_lines(solid, staves)
    free = solid & (1 - lines)
    reach = int(max(3, round(0.3 * space)))
    # A head that a hand drew as a slanted stroke across a thick staff line is no higher than the line in any one
    # column, so the line was taken away under it and the head fell into two pieces. Where wide ink touches a staff
    # line from above and, a little to the left, from below, the stroke goes through the line.
    wide_ink = cv2.morphologyEx(free, cv2.MORPH_OPEN, np.ones((1, reach), np.uint8))
    side = int(round(CROSS * space))
    crossing = np.zeros_like(lines)
    height, width = lines.shape
    for staff in staves:
        half = int(np.ceil(staff['thick'] / 2 + 2))
        first, last = max(0, int(staff['x0'] - 1.5 * staff['space'])), min(width, int(staff['x1'] + 1.5 * staff['space']))
        for row in staff['rows']:
            row = int(round(row))
            top, bottom = row - half - 1, row + half + 1
            if top - 1 < 0 or bottom + 2 > height:
                continue
            # The stroke rises to the right: over the line its ink is at the right, under the line at the left.
            over = wide_ink[top - 1:top + 1, first:last].max(axis=0).reshape(1, -1)
            under = wide_ink[bottom:bottom + 2, first:last].max(axis=0).reshape(1, -1)
            kernel = np.ones((1, side + 1), np.uint8)
            both = cv2.dilate(over, kernel, anchor=(0, 0)) & cv2.dilate(under, kernel, anchor=(side, 0))
            crossing[row - half:row + half + 1, first:last] = lines[row - half:row + half + 1, first:last] & both
    lines = lines & (1 - crossing)
    free = free | crossing
    # A weak copy breaks a thin stem into dashes. Thin ink is joined over small gaps in its own column.
    thin_ink = free & (1 - cv2.morphologyEx(free, cv2.MORPH_OPEN, np.ones((1, reach), np.uint8)))
    gap = int(max(4, round(DASH_GAP * space)))
    # A thin stroke that crosses a staff line was cut there when the line was taken away, if the copy had weakened
    # it at the line. Where a staff line has thin ink close over it and close under it, the stroke goes through.
    near = int(round(max(staff['thick'] for staff in staves) + 0.3 * space))
    kernel = np.ones((near + 1, 1), np.uint8)
    over = cv2.dilate(thin_ink, kernel, anchor=(0, near))
    under = cv2.dilate(thin_ink, kernel, anchor=(0, 0))
    through = lines & over & under
    joined = free | cv2.morphologyEx(thin_ink | through, cv2.MORPH_CLOSE, np.ones((gap, 1), np.uint8))
    up = upright(joined, int(round(UPRIGHT * space)))
    strokes, stems = _strokes(up, joined, free, space)
    # The page shows whether it is a weak copy: its long strokes have gaps. On a page whose strokes are whole, a gap
    # ends a stroke, so the ink is joined over small gaps only.
    long = [stroke for stroke in strokes if stroke['slim'] and stroke['y1'] - stroke['y0'] >= 2.5 * space]
    broken = float(np.mean([((stroke['left'] + stroke['right'] - 1) <= 0).mean() > 0.03 for stroke in long])) if long else 0.0
    weak = float(np.clip((broken - WEAK[0]) / (WEAK[1] - WEAK[0]), 0.0, 1.0))
    bridge = WHOLE_GAP + (1.0 - WHOLE_GAP) * weak
    if bridge < 1.0:
        gap = int(max(3, round(DASH_GAP * bridge * space)))
        joined = free | cv2.morphologyEx(thin_ink | through, cv2.MORPH_CLOSE, np.ones((gap, 1), np.uint8))
    marks = free & (1 - stems)
    brush = int(max(5, round(BRUSH * space))) | 1
    thick = cv2.morphologyEx(marks, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (brush, brush)))
    # The ink without the staff lines and without the filling of the holes, with thin strokes going through the lines.
    bare = (ink & (1 - lines)) | through
    return {'grey': grey, 'ink': ink, 'holes': holes, 'open_holes': open_holes, 'solid': solid, 'lines': lines, 'free': free, 'joined': joined, 'up': up,
            'stems': stems, 'marks': marks, 'thick': thick, 'strokes': strokes, 'staves': staves, 'space': space,
            'bare': bare, 'weak': weak, 'bridge': bridge}


def _strokes(up: np.ndarray, joined: np.ndarray, free: np.ndarray, space: float) -> tuple[list[dict], np.ndarray]:
    """The upright strokes, and the mask of the thin part of each slim stroke.

    Each stroke: 'x' (its column at its middle row), 'y0', 'y1', 'width' (px; the median width of the ink that it
    stands in), 'slim' (True for a stem or a bar line), 'xs' (its column in each row from y0) and 'left', 'right' (how
    far the ink reaches from that column in each row, in px; 0 where the stroke has a gap). Where a head, a beam or a
    flag joins a stroke, the ink is much wider than the stroke; there the stroke's own part stays in the page."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(up, connectivity=8)
    height, width = free.shape
    strokes = []
    stems = np.zeros_like(free)
    for index in range(1, count):
        x, y, wide, high, _ = stats[index]
        part = labels[y:y + high, x:x + wide] == index
        columns = np.arange(wide)
        xs = np.rint(x + (part * columns).sum(axis=1) / np.maximum(1, part.sum(axis=1))).astype(int)
        left = np.zeros(high, int)
        right = np.zeros(high, int)
        for step in range(high):
            row = free[y + step]
            centre = xs[step]
            if not row[centre]:
                near = [c for c in (centre - 1, centre + 1, centre - 2, centre + 2) if 0 <= c < width and row[c]]
                if not near:
                    continue
                centre = near[0]
            first = centre
            while first > 0 and row[first - 1]:
                first -= 1
            last = centre
            while last + 1 < width and row[last + 1]:
                last += 1
            left[step], right[step] = xs[step] - first + 1, last - xs[step] + 1
        runs = left + right - 1
        seen = runs[runs > 0]
        own = float(np.median(seen)) if len(seen) else float(np.median(part.sum(axis=1)))
        slim = own <= SLIM * space
        strokes.append({'x': float(np.median(xs)), 'y0': int(y), 'y1': int(y + high - 1), 'width': own, 'slim': bool(slim),
                        'xs': xs, 'left': left, 'right': right, 'runs': runs})
    if STEM_USUAL:
        # The page shows how wide its stems are: the long strokes. A short stroke that is much wider is no stem; it
        # is the ink of two slanted heads, one over the other.
        long = [stroke['width'] for stroke in strokes if stroke['slim'] and stroke['y1'] - stroke['y0'] + 1 >= 2.5 * space]
        if len(long) >= 8:
            usual = float(np.median(long))
            for stroke in strokes:
                if stroke['slim'] and stroke['y1'] - stroke['y0'] + 1 < STEM_USUAL[0] * space \
                        and stroke['width'] > STEM_USUAL[1] * usual + 1:
                    stroke['slim'] = False
            if STEM_OWN:
                thin = 1.6 * usual + 2
                for stroke in strokes:
                    seen = stroke['runs'][stroke['runs'] > 0]
                    if stroke['slim'] and stroke['width'] > STEM_USUAL[1] * usual + 1 and len(seen) \
                            and (seen <= thin).mean() >= STEM_OWN:
                        stroke['width'] = float(np.median(seen[seen <= thin]))
    for stroke in strokes:
        runs, xs, left, right, y = stroke.pop('runs'), stroke['xs'], stroke['left'], stroke['right'], stroke['y0']
        if stroke['slim']:
            limit = 1.6 * stroke['width'] + 2
            for step in range(len(runs)):
                if 0 < runs[step] <= limit:
                    stems[y + step, xs[step] - left[step] + 1:xs[step] + right[step]] = 1
                elif runs[step] == 0:
                    stems[y + step, max(0, xs[step] - 1):xs[step] + 2] |= joined[y + step, max(0, xs[step] - 1):xs[step] + 2]
    return strokes, stems & free


COLOURS = {            # BGR
    'lines': (205, 205, 205),
    'rest': (130, 130, 130),
    'stems': (230, 120, 0),
    'thick': (0, 0, 0),
    'holes': (0, 160, 255),
}


def picture(layers: dict) -> np.ndarray:
    """The layers as one colour picture: staff lines light grey, upright strokes blue, thick marks black, the filled
    inside of hollow heads orange, and all other ink dark grey."""
    height, width = layers['ink'].shape
    out = np.full((height, width, 3), 255, np.uint8)
    out[layers['lines'] > 0] = COLOURS['lines']
    out[layers['marks'] > 0] = COLOURS['rest']
    out[layers['stems'] > 0] = COLOURS['stems']
    out[layers['thick'] > 0] = COLOURS['thick']
    out[(layers['holes'] > 0) & (layers['lines'] == 0)] = COLOURS['holes']
    return out

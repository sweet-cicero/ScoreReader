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
RIM = 0.8            # a note without a stem has its own ink at this share of the rim of its hole
WHOLE = (1.12, 0.98, 0.8, 1.7)   # a whole note: its width over its height, its width over the page's head width, and
                                 # its height over the page's head height (least, most)
HEAD_WIDE = (0.65, 3.0)   # the width of a head, in staff spaces: from a small slanted stroke to a large hand-drawn oval
HEAD_HIGH = (0.3, 2.0)    # and its height
SHARP_SLIM = 0.3     # the strokes of a sharp are slim for this many staff spaces where they leave its mark


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


def _mark(mask: np.ndarray, holes: np.ndarray, x: int, y: int, blob: int) -> dict | None:
    """A thick mark from a part of a mask (at x, y on the page)."""
    size = int(mask.sum())
    if size == 0:
        return None
    ys, xs = np.nonzero(mask)
    inside = mask & holes
    return {'x0': int(x + xs.min()), 'x1': int(x + xs.max()), 'y0': int(y + ys.min()), 'y1': int(y + ys.max()),
            'area': size, 'cx': float(x + xs.mean()), 'cy': float(y + ys.mean()), 'hole': float(inside.sum()) / size,
            'hole_cy': float(y + np.nonzero(inside)[0].mean()) if inside.any() else None, 'blob': blob}


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
    wide, high = head_size([piece[0] for piece in pieces], space)
    layers['head'] = (wide, high)
    marks = []
    for mark, mask, holes, x, y in pieces:
        own_wide, own_high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
        rows, columns = np.nonzero(mask)
        mask = mask[rows.min():rows.max() + 1, columns.min():columns.max() + 1]
        holes = holes[rows.min():rows.max() + 1, columns.min():columns.max() + 1]
        x, y = x + int(columns.min()), y + int(rows.min())
        parts = []
        if mark['hole'] >= HOLLOW and (own_high >= 1.5 * high or own_wide >= 1.6 * wide):
            # Hollow heads that touch: each has its own hole, and each part of the mark goes to the nearest hole.
            centres = _hole_centres(layers, mask & holes, x, y)
            if len(centres) >= 2:
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
                if own_high >= 1.6 * high and own_wide < 1.6 * wide:
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
        marks += parts if len(parts) >= 2 else [mark]
    return marks


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
    {'direction', 'x', 'end' (the row of its far end), 'length' (px from the mark's middle), 'past' (px past the
    mark's edge), 'slim' (the rows past the mark's edge where the ink is as slim as a stem), 'inked' (the rows past
    the edge that have ink)}, or None when no ink leaves the mark there."""
    ink, space = layers['joined'], layers['space']
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
    best['slim'] = sum(1 for row, column in outside if _run(ink, row, column) <= SLIM_STEM * space)
    return best


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
    if HEAD_WIDE[0] <= wide <= HEAD_WIDE[1] and HEAD_HIGH[0] <= high <= HEAD_HIGH[1]:
        return 'head'
    return None


def ledger_lines(layers: dict, staff: dict, head: dict) -> list[float]:
    """The rows of the ledger lines between a staff and a head beside it, the line through the head too. A ledger
    line is a level run of ink that reaches past the head on both sides and is thinner than a head."""
    free, space = layers['free'], staff['space']
    above = head['cy'] < staff['rows'][0]
    first, last = int(head['cx'] - 0.95 * space), int(head['cx'] + 0.95 * space)
    if first < 0 or last >= free.shape[1]:
        return []
    if above:
        top, bottom = int(head['y0'] - 0.3 * space), int(staff['rows'][0] - 0.35 * space)
    else:
        top, bottom = int(staff['rows'][4] + 0.35 * space), int(head['y1'] + 0.3 * space)
    top, bottom = max(0, top), min(free.shape[0] - 1, bottom)
    if bottom <= top:
        return []
    window = free[top:bottom + 1, first:last + 1]
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
        return place
    up = place > 0
    merged = []
    for row in rows:
        if merged and row - merged[-1] < 0.5 * space:
            merged[-1] = (merged[-1] + row) / 2
        else:
            merged.append(row)
    if head['hollow']:
        centre = head['cy']
    else:
        # A thick ledger line under a head is a part of its mark: the middle is measured from the head's far edge.
        high = min(layers['head'][1], head['y1'] - head['y0'] + 1)
        centre = head['y0'] + high / 2 if up else head['y1'] - high / 2
    last = merged[0] if up else merged[-1]
    past = (last - centre) if up else (centre - last)      # how far the head's middle is past its last ledger line
    steps = 2 * len(merged) + (0 if abs(past) <= 0.27 * space else 1 if past > 0 else -1)
    found = float(4 + steps) if up else float(-4 - steps)
    if abs(found) < abs(place) - 2.2:
        return None       # too few ledger lines for a head this far from the staff: a letter over a hyphen
    return found if abs(found - place) <= 1.6 else place


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
        # A beam hangs on two stems that leave it the same way, one at each end.
        ways = mark['ways']
        for left, right in (('down_left', 'down_right'), ('up_left', 'up_right')):
            if is_stem(ways[left], space) and is_stem(ways[right], space) and ways[right]['x'] - ways[left]['x'] >= space:
                mark['kind'] = 'beam' if mark['kind'] == 'head' else mark['kind']
        if mark['kind'] == 'head':
            for name in ('up_right', 'down_left'):
                if is_stem(mark['ways'][name], space):
                    mark['stems'].append(mark['ways'][name])
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
    _share_stems(marks, space)
    heads, signs = [], []
    for number, mark in enumerate(marks):
        if mark['kind'] is None or mark['kind'] == 'beam':
            continue
        staff = _staff_of(layers, mark['cx'], mark['cy'])
        if staff is None:
            continue
        hollow = mark['hole'] >= HOLLOW
        cy = mark['hole_cy'] if hollow and mark['hole_cy'] is not None else mark['cy']
        place = pitch_place(layers['staves'][staff], cy)
        if mark['kind'] != 'head':
            if abs(place) <= 7.5:
                signs.append({'x0': mark['x0'], 'y0': mark['y0'], 'x1': mark['x1'], 'y1': mark['y1'], 'cx': mark['cx'],
                              'cy': cy, 'staff': staff, 'place': place, 'kind': mark['kind'],
                              'count': max(1, int(round((mark['x1'] - mark['x0'] + 1) / (1.05 * space))))
                              if mark['kind'] == 'sharp' else 1})
            continue
        if not mark['stems']:
            # A whole note is an oval that lies on its side, as large as the heads of the page. The letter o of the
            # words is small and round, and a capital O of a title stands upright.
            wide, high = mark['x1'] - mark['x0'] + 1, mark['y1'] - mark['y0'] + 1
            oval = wide >= WHOLE[0] * high and wide >= WHOLE[1] * layers['head'][0] \
                and WHOLE[2] * layers['head'][1] <= high <= WHOLE[3] * layers['head'][1]
            if not (hollow and oval and 'tail_of' not in mark and _rim(layers, mark) >= RIM):
                continue
        head = {'x0': mark['x0'], 'y0': mark['y0'], 'x1': mark['x1'], 'y1': mark['y1'], 'cx': mark['cx'], 'cy': cy,
                'staff': staff, 'place': place, 'hollow': hollow, 'hole': mark['hole'], 'stems': mark['stems'],
                'mark': number, 'core': core_light(layers, mark)}
        if abs(place) > 4 + 2 * REACH:
            continue
        if abs(place) > 4.6:
            head['ledgers'] = ledger_lines(layers, layers['staves'][staff], head)
            found = ledger_place(layers, layers['staves'][staff], head)
            if found is None or (not head['ledgers'] and abs(place) > 5.6):
                continue
            head['place'] = found
        heads.append(head)
    return {'heads': heads, 'signs': signs, 'marks': marks}


# ----------------------------------------------------------------------------------------------------------------
# Heads that a hand drew as one thin stroke

THIN_WIDE = (0.55, 2.2)    # the width of a head drawn as one stroke, in staff spaces
THIN_HIGH = (0.2, 1.3)     # and its height
THIN_NEAR = 1.3            # the head lies at most this many staff spaces from the end of its stem
THIN_HOLLOW = 0.15         # such a head is hollow when its ink goes around this share of its box
THIN_STEM = 1.6            # the stem of such a head is at least this many staff spaces long


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
    ink = marks | (layers['lines'] & cv2.dilate(marks, np.ones((2 * near + 1, 1), np.uint8)))
    count, labels, stats, centres = cv2.connectedComponentsWithStats(ink, connectivity=8)
    pieces = []
    for index in range(1, count):
        x, y, wide, high, area = stats[index]
        if not (THIN_WIDE[0] * space <= wide <= THIN_WIDE[1] * space and THIN_HIGH[0] * space <= high <= THIN_HIGH[1] * space):
            continue
        if area < 0.06 * space * space:
            continue
        part = labels[y:y + high, x:x + wide] == index
        # A piece that lies along a staff line is a rest of the line, not a head.
        own = part & (marks[y:y + high, x:x + wide] > 0)
        if own.sum() < 0.35 * area:
            continue
        pieces.append({'x0': int(x), 'y0': int(y), 'x1': int(x + wide - 1), 'y1': int(y + high - 1), 'area': int(area),
                       'cx': float(centres[index][0]), 'cy': float(centres[index][1]),
                       'hole': max(float((layers['holes'][y:y + high, x:x + wide] > 0)[part].sum()) / area,
                                   _loop(part, space))})
    used = [(stem['x'], min(head['cy'], stem['end']), max(head['cy'], stem['end'])) for head in heads for stem in head['stems']]
    strokes = [stroke for stroke in layers['strokes'] if stroke['slim'] and stroke['y1'] - stroke['y0'] + 1 >= THIN_STEM * space]
    found = []
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
        best = None
        for piece in pieces:
            for direction in ('up', 'down'):
                if direction == 'up':       # the head lies under the lower end, at the left
                    past = piece['cy'] - bottom
                    side = x - piece['cx']
                    reach = x - piece['x1']
                else:                        # the head lies over the upper end, at the right
                    past = top - piece['cy']
                    side = piece['cx'] - x
                    reach = piece['x0'] - x
                if not (-0.25 * space <= past <= THIN_NEAR * space and -0.15 * space <= side <= 1.6 * space
                        and reach <= 0.7 * space):
                    continue
                far = abs(past) + max(0.0, reach)
                if best is None or far < best[0]:
                    best = (far, piece, direction)
        if best is None:
            continue
        _, piece, direction = best
        if any(abs(head['cx'] - piece['cx']) <= 0.7 * space and abs(head['cy'] - piece['cy']) <= 0.45 * space for head in heads + found):
            continue
        end = top if direction == 'up' else bottom
        place = pitch_place(staves[staff], piece['cy'])
        head = {'x0': piece['x0'], 'y0': piece['y0'], 'x1': piece['x1'], 'y1': piece['y1'], 'cx': piece['cx'], 'cy': piece['cy'],
                'staff': staff, 'place': place, 'hollow': piece['hole'] >= THIN_HOLLOW, 'hole': piece['hole'], 'thin': True,
                'stems': [{'direction': direction, 'x': int(round(x)), 'end': int(end), 'length': abs(piece['cy'] - end)}]}
        if abs(place) > 4 + 2 * REACH:
            continue
        if abs(place) > 4.6:
            head['ledgers'] = ledger_lines(layers, staves[staff], head)
            place = ledger_place(layers, staves[staff], head)
            if place is None or (not head['ledgers'] and abs(head['place']) > 5.6):
                continue
            head['place'] = place
        found.append(head)
    return found


# ----------------------------------------------------------------------------------------------------------------
# Lengths: flags, beams and dots

TAIL_ZONE = 1.3      # flags and beams stand in this many staff spaces from the far end of a stem
TAIL_WIDE = 0.45     # there the ink reaches at least this many staff spaces from the stem, to one side
TAIL_HIGH = 0.12     # for at least this many staff spaces of the stem's rows
TAIL_THICK = 0.22    # a beam or a printed flag is this thick; thinner ink is a flag only when it is a hook (see tails)
BEAM_FAR = 1.2       # a beam reaches at least this many staff spaces from its stem; a flag is shorter
BEAM_NEXT = 7.0      # the next stem of a beam stands at most this many staff spaces away
BEAM_USUAL = 0.8     # a beam without a witness at the next stem is at least this share as thick as the page's beams
LOOP_NEAR = 1.8      # the loop of a flag lies at most this many staff spaces from the far end of the stem
FLAG_BACK = 0.08     # a printed flag comes back toward the head by this many staff spaces while it leaves the stem
TAIL_START = 0.4     # the hook of a flag begins this near to the end of its stem, in staff spaces


def tail_marks(layers: dict, head: dict, stem: dict) -> list[dict]:
    """The pieces of ink that hang on the far end of a stem, without the stem itself. Each: {'right' (True at the
    right side of the stem), 'row' (where it leaves the stem), 'far' (how far it reaches from the stem), 'thick' (how
    thick it is where it has left the stem), 'from_end' (how far from the stem's end it begins), 'back' (how far it
    comes back toward the head while it goes away from the stem; all in staff spaces)}."""
    ink, space = layers['bare'], layers['space']
    height, width = ink.shape
    up = stem['direction'] == 'up'
    x, end = int(stem['x']), int(stem['end'])
    inward = int(min(TAIL_ZONE * space, max(0.0, abs(head['cy'] - end) - 1.0 * space)))
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
        pieces.append({'right': bool(right), 'row': float(touch.mean()) + top, 'far': float(far / space),
                       'thick': (float(np.median(heights)) if heights else 0.0) / space,
                       'from_end': float(np.abs(touch + top - end).min()) / space, 'back': float(back),
                       'touch': len(touch) / space})
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
    for head in heads:
        for stem in head['stems']:
            stem['marks'] = tail_marks(layers, head, stem)
            groups.setdefault((head['staff'], stem['direction']), []).append(stem)

    def witness(group: list[dict], stem: dict, right: bool) -> bool:
        """True when the next stem at that side shows a beam at the side that faces this stem."""
        side = [other for other in group
                if 0.5 * space < (other['x'] - stem['x'] if right else stem['x'] - other['x']) <= BEAM_NEXT * space]
        if not side:
            return False
        near = min(side, key=lambda other: abs(other['x'] - stem['x']))
        return abs(near['end'] - stem['end']) <= 2.5 * space \
            and any(_is_beam(piece) and piece['right'] != right for piece in near['marks'])

    sure = []
    for group in groups.values():
        for stem in group:
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
                    if piece['witness'] or (alone and usual is not None and piece['thick'] >= BEAM_USUAL * usual)]
            short = [piece for piece in pieces if not piece['beam'] and piece['thick'] >= TAIL_THICK and piece['far'] >= 0.6]
            # A printed flag; and beside a beam, the short second beam of a sixteenth.
            rows += [piece['row'] for piece in short if (piece['right'] and piece['back'] >= FLAG_BACK) or rows]
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


def dots(layers: dict, heads: list[dict]) -> None:
    """Sets head['dot'] to True where a dot stands at the right of a head: a small round mark in the space beside it."""
    space = layers['space']
    # The dots of two voices stand one over the other, and the joining of dashes makes one upright stroke of them:
    # so the dots are looked for in the ink itself, not in the marks that are left without the strokes.
    count, labels, stats, centres = cv2.connectedComponentsWithStats(layers['bare'], connectivity=8)
    found = []
    for index in range(1, count):
        x, y, wide, high, area = stats[index]
        if not (0.14 * space <= wide <= 0.6 * space and 0.14 * space <= high <= 0.6 * space):
            continue
        if area < 0.55 * wide * high or not 0.6 <= wide / high <= 1.7:
            continue
        found.append((float(centres[index][0]), float(centres[index][1])))
    for head in heads:
        head['dot'] = False
        for x, y in found:
            if 0.1 * space <= x - head['x1'] <= 1.3 * space and abs(y - head['cy']) <= 0.7 * space:
                head['dot'] = True
                break


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

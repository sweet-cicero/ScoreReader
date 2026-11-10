"""Reads the beginning of each staff of a clean page: the clef and the key signature. No model is used.

The clef. A treble clef is the highest mark of a staff: it begins far over the top line and ends under the bottom
line. A bass clef stays inside the staff. So the ink over and under the staff, in the first columns of the staff,
tells the two apart, on a printed page and in a copyist's hand.

The key signature. A sharp has two upright strokes side by side; a flat has one upright stroke with a bowl at its
lower right. Music writes the sharps and the flats of a key in one fixed order and at fixed heights (the first sharp
of a treble staff stands on the top line, the first flat on the middle line; on a bass staff both stand one line
lower). So the signs that follow the clef are read as a chain: each next sign must stand where the order puts it.
A time signature, a rest or the first note does not fit the chain, and ends it. The heights also say which clef
the staff has, and that is a second witness for the clef.
"""
from __future__ import annotations

import cv2
import numpy as np

from .layers import DASH_GAP, upright
from .symbols import pitch_place

SHARP_PLACES = {'G': [4, 1, 5, 2, -1, 3, 0], 'F': [2, -1, 3, 0, -3, 1, -2]}     # the pitch places of the sharps, in order
FLAT_PLACES = {'G': [0, 3, -1, 2, -2, 1, -3], 'F': [-2, 1, -3, 0, -4, -1, -5]}  # and of the bowls of the flats
SIGN_STROKE = (1.1, 3.6)     # the height of an upright stroke of a sharp or a flat, in staff spaces
PAIR = (0.28, 0.85)          # the two strokes of a sharp are this far apart, in staff spaces
FIT = 1.3                    # a sign may stand this many pitch places from its place in the order
FLAT_DRIFT = (-0.5, 0.3)     # the left edge of a flat's stroke moves at most this far to the left and to the right, in staff spaces
STEP = (0.45, 1.7)           # the next sign of a key signature begins this far right of the last, in staff spaces
PRIOR = 1.5                  # the weight of the custom of choir music among the witnesses for a clef (a clef's shape is 1)
FIRST = (1.6, 6.5)           # the first sign begins this far right of the clef's left edge, in staff spaces
USUAL_START = 1.5   # a staff whose notes seem to begin this many staff spaces later than on the page's other staves begins as they do (0: off)
OPENING = 3.0       # a clef begins at most this many staff spaces after the line that opens its system (0: off)
LOST_CLEF = 3.4     # the room of a clef that the copy lost, in staff spaces from the staff's left end
G_TAIL = (0.9, 4.5, 2.4, 1.8)   # a treble clef that does not rise over the top line hangs this far under the
#                         bottom line, is this high in all, hangs at most this far, and begins at most this far after the
#                         staff's left end, in staff spaces: a bass clef ends over the bottom line (None: off)


def start_strokes(layers: dict, staff: dict, first: int, last: int) -> list[dict]:
    """The short upright strokes in the columns first..last of a staff: each {'x', 'x0', 'x1', 'top', 'bottom' (rows),
    'wide', 'high' (staff spaces), 'place' (the pitch place of its middle)}."""
    ink, space = layers['ink'], staff['space']
    height, width = ink.shape
    first, last = max(0, first), min(width, last)
    y0, y1 = max(0, int(staff['rows'][0] - 4.5 * space)), min(height, int(staff['rows'][4] + 4.5 * space))
    if last - first < 3 or y1 - y0 < 3:
        return []
    region = np.ascontiguousarray(ink[y0:y1, first:last])
    # A weak copy breaks a thin stroke into dashes: thin ink is joined over small gaps in its own column.
    reach = int(max(3, round(0.3 * space)))
    thin = region & (1 - cv2.morphologyEx(region, cv2.MORPH_OPEN, np.ones((1, reach), np.uint8)))
    gap = int(max(4, round(DASH_GAP * space)))
    region = region | cv2.morphologyEx(thin, cv2.MORPH_CLOSE, np.ones((gap, 1), np.uint8))
    up = upright(region, int(round(SIGN_STROKE[0] * space)))
    count, _, stats, _ = cv2.connectedComponentsWithStats(up, connectivity=8)
    strokes = []
    for index in range(1, count):
        x, y, wide, high, _ = stats[index]
        top, bottom = y0 + y, y0 + y + high - 1
        strokes.append({'x': first + x + (wide - 1) / 2, 'x0': first + x, 'x1': first + x + wide - 1, 'top': int(top),
                        'bottom': int(bottom), 'wide': wide / space, 'high': high / space,
                        'place': pitch_place(staff, (top + bottom) / 2)})
    return sorted(strokes, key=lambda stroke: stroke['x'])


def _free(layers: dict) -> np.ndarray:
    """The ink without the staff lines (and without the filling of the holes)."""
    if 'unfilled' not in layers:
        layers['unfilled'] = layers['ink'] & (1 - layers['lines'])
    return layers['unfilled']


def _ink(layers: dict, x0: float, x1: float, y0: float, y1: float) -> float:
    """The ink (without the staff lines) in a box, in px."""
    free = _free(layers)
    height, width = free.shape
    x0, x1, y0, y1 = max(0, int(round(x0))), min(width, int(round(x1)) + 1), max(0, int(round(y0))), min(height, int(round(y1)) + 1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return float(free[y0:y1, x0:x1].sum())


def stroke_sides(layers: dict, stroke: dict, space: float) -> dict | None:
    """How the ink that hangs on an upright stroke lies beside it, from the top of the stroke to its bottom. Returns
    (in staff spaces): 'top' (how wide the ink is beside the top fifth of the stroke: a bare stroke is as wide as
    itself), 'thick' (the stroke's own width there), 'bulge' (how far the ink reaches to the right of the stroke's
    top part, beside the lower two thirds), 'drift' (how far the left edge moves to the right there) and 'foot' (the
    same at the stroke's lowest rows), or None for a stroke with too little ink."""
    free = _free(layers)
    height, width = free.shape
    # The stroke is the left edge of the mark: what stands at its left (a clef that touches it) is not looked at.
    x0, x1 = max(0, int(stroke['x0']) - 2), min(width, int(stroke['x1'] + 1.05 * space) + 1)
    y0, y1 = max(0, int(stroke['top'])), min(height, int(stroke['bottom']) + 1)
    region = free[y0:y1, x0:x1]
    count, labels = cv2.connectedComponents(region, connectivity=8)
    own = np.unique(labels[:, stroke['x0'] - x0:stroke['x1'] - x0 + 1])
    kept = np.isin(labels, own[own > 0])
    spans = []
    for row in kept:
        columns = np.nonzero(row)[0]
        spans.append((int(columns[0]), int(columns[-1])) if len(columns) else None)
    high = len(spans)
    top = [span for span in spans[:max(2, int(round(0.22 * high)))] if span]
    body = [span for span in spans[int(round(0.35 * high)):int(round(0.9 * high))] if span]
    foot = [span for span in spans[int(round(0.88 * high)):] if span]
    if len(top) < 2 or len(body) < 0.3 * space or not foot:
        return None
    edge0, edge1 = float(np.median([span[0] for span in top])), float(np.median([span[1] for span in top]))
    # The bowl: the rows where the ink reaches to the right of the stroke.
    bowl = [row for row, span in enumerate(spans) if span and span[1] - edge1 >= 0.25 * space]
    return {'bowl': y0 + (bowl[0] + bowl[-1]) / 2 if bowl else None,
            'top': float(np.median([span[1] - span[0] + 1 for span in top])) / space,
            'thick': (edge1 - edge0 + 1) / space,
            'bulge': (float(np.percentile([span[1] for span in body], 75)) - edge1) / space,
            'drift': (float(np.median([span[0] for span in body])) - edge0) / space,
            'foot': (float(np.median([span[0] for span in foot])) - edge0) / space}


def sign_candidates(layers: dict, staff: dict, strokes: list[dict]) -> list[dict]:
    """The marks that can be a sharp or a flat, from the upright strokes: each {'kind', 'x0', 'x1', 'place'}."""
    space = staff['space']
    signs = []
    used = set()
    slim = [stroke for stroke in strokes if SIGN_STROKE[0] <= stroke['high'] <= SIGN_STROKE[1]]
    for number, left in enumerate(slim):
        if left['wide'] > 0.45 or id(left) in used:
            continue
        for right in slim[number + 1:]:
            if right['wide'] > 0.45 or not PAIR[0] * space <= right['x'] - left['x'] <= PAIR[1] * space:
                continue
            shared = min(left['bottom'], right['bottom']) - max(left['top'], right['top'])
            if shared < 0.5 * max(left['bottom'] - left['top'], right['bottom'] - right['top']):
                continue
            # The two bars of a sharp cross both strokes: ink joins the strokes.
            top, bottom = max(left['top'], right['top']), min(left['bottom'], right['bottom'])
            between = _ink(layers, left['x1'] + 1, right['x0'] - 1, top, bottom)
            gap = max(1.0, right['x0'] - left['x1'] - 1)
            if between < 0.25 * gap * 0.5 * space:
                continue
            signs.append({'kind': 'sharp', 'x0': float(left['x0']), 'x1': float(right['x1']),
                          'place': (left['place'] + right['place']) / 2, 'top': min(left['top'], right['top']),
                          'bottom': max(left['bottom'], right['bottom'])})
            used.add(id(left))
            used.add(id(right))
            break
    for stroke in slim:
        if id(stroke) in used or stroke['wide'] > 1.2:
            continue
        # A flat: a bare stroke at the top, a bowl at the right of its lower part, and a left edge that stays in place
        # down to the foot.
        sides = stroke_sides(layers, stroke, space) if stroke['high'] >= 1.3 else None
        stroke['sides'] = sides
        if sides and sides['top'] <= 0.65 and 0.3 <= sides['bulge'] <= 1.0 and FLAT_DRIFT[0] <= sides['drift'] <= FLAT_DRIFT[1] \
                and sides['foot'] <= 0.3:
            signs.append({'kind': 'flat', 'x0': float(stroke['x0']), 'x1': float(stroke['x0'] + (sides['thick'] + sides['bulge']) * space),
                          'place': pitch_place(staff, stroke['bottom'] - 0.6 * space), 'sides': sides,
                          'bowl_place': pitch_place(staff, sides['bowl']) if sides['bowl'] is not None else None,
                          'top': stroke['top'], 'bottom': stroke['bottom']})
        elif 0.45 < stroke['wide'] and stroke['high'] <= 3.4:
            # Two strokes that the ink of a small hand joined.
            signs.append({'kind': 'sharp', 'x0': float(stroke['x0']), 'x1': float(stroke['x1']), 'place': stroke['place'],
                          'joined': True, 'top': stroke['top'], 'bottom': stroke['bottom']})
    return sorted(signs, key=lambda sign: sign['x0'])


def chain(signs: list[dict], kind: str, clef: str, start: float, least: float, space: float) -> tuple[list[dict], float]:
    """The longest chain of signs of one kind that stand in the order of a key signature under a clef, and how far
    they stand from their places (the mean, in pitch places). `start` is the left edge of the clef and `least` the
    column where the clef ends: no sign begins before it."""
    places = (SHARP_PLACES if kind == 'sharp' else FLAT_PLACES)[clef]
    best, best_miss = [], 0.0
    own = [sign for sign in signs if sign['kind'] == kind]
    for first in own:
        if not FIRST[0] * space <= first['x0'] - start <= FIRST[1] * space or first['x0'] < least \
                or abs(first['place'] - places[0]) > FIT:
            continue
        found, miss = [first], abs(first['place'] - places[0])
        for sign in own:
            if len(found) == len(places):
                break
            if STEP[0] * space <= sign['x0'] - found[-1]['x0'] <= STEP[1] * space \
                    and abs(sign['place'] - places[len(found)]) <= FIT:
                miss += abs(sign['place'] - places[len(found)])
                found.append(sign)
        miss /= len(found)
        if len(found) > len(best) or (len(found) == len(best) and miss < best_miss):
            best, best_miss = found, miss
    return best, best_miss


def bare_lines(layers: dict, staff: dict, first: float, last: float) -> list[tuple[float, int, int]]:
    """The bare upright lines that cross a staff from its top line to its bottom line, in the columns first..last:
    the line that opens a system, and bar lines. Each: (its middle column, its first column, its last column). The
    long stroke of a treble clef or a stem can cross the staff too, but a clef's body or a head hangs on it; a bare
    line has nothing at its sides."""
    ink, free, space = layers['ink'], _free(layers), staff['space']
    top, bottom = int(staff['rows'][0]), int(staff['rows'][4])
    x0, x1 = max(0, int(first)), min(ink.shape[1], int(last))
    if x1 - x0 < 3:
        return []
    full = ink[top:bottom + 1, x0:x1].mean(axis=0) >= 0.9
    groups = []
    for column in np.nonzero(full)[0]:
        if groups and column - groups[-1][1] <= 2:
            groups[-1][1] = int(column)
        else:
            groups.append([int(column), int(column)])
    work = free[top:bottom + 1, x0:x1].copy()
    for begin, end in groups:
        work[:, max(0, begin - 2):end + 3] = 0
    side = max(3, int(0.35 * space))
    found = []
    for begin, end in groups:
        if end - begin + 1 > 0.7 * space:
            continue
        left = work[:, max(0, begin - 2 - side):max(0, begin - 2)]
        right = work[:, end + 3:end + 3 + side]
        if (left.size == 0 or left.mean() < 0.1) and (right.size == 0 or right.mean() < 0.1):
            found.append(((begin + end) / 2 + x0, begin + x0, end + x0))
    return found


def clef_shape(layers: dict, staff: dict) -> dict:
    """The clef of a staff from its shape: {'clef': 'G', 'F' or None, 'x0', 'x1', 'over', 'under', 'wide'}. The clef
    is the first high mark that touches the staff, after the line that opens the system; `over` and `under` say how
    far it reaches past the top line and the bottom line, in staff spaces."""
    space, rows = staff['space'], staff['rows']
    free = _free(layers)
    top, bottom = rows[0], rows[4]
    y0, y1 = max(0, int(top - 3.2 * space)), min(free.shape[0], int(bottom + 2.6 * space))
    x0, x1 = max(0, int(staff['x0'] - 0.3 * space)), min(free.shape[1], int(staff['x0'] + 12 * space))
    region = free[y0:y1, x0:x1].copy()
    opening = bare_lines(layers, staff, x0, x1)
    for _, begin, end in opening:
        region[:, max(0, begin - x0 - 2):max(0, end - x0 + 3)] = 0
    # The staff lines were taken away: a thin mark is joined again over the rows of the lines.
    region = cv2.morphologyEx(region, cv2.MORPH_CLOSE, np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)
    found = []
    for label in range(1, count):
        x, y, wide, high, area = stats[label]
        if y + high - 1 < top - y0 + 0.5 * space or y > bottom - y0 - 0.5 * space or wide < 1.4 * space or high < 2.0 * space:
            continue
        over, under = (top - (y0 + y)) / space, (y0 + y + high - 1 - bottom) / space
        if over >= 0.7 and under >= 0.3 or over >= 1.2:
            clef = 'G'
        elif -0.8 <= over <= 0.7 and -2.2 <= under <= 0.4:
            clef = 'F'          # a bass clef hangs from the top line and ends over the bottom line
        elif G_TAIL and G_TAIL[0] <= under <= G_TAIL[2] and high >= G_TAIL[1] * space and over >= -0.5 \
                and x0 + x - staff['x0'] <= G_TAIL[3] * space:
            clef = 'G'          # a treble clef of a hand that stays under the top line: its tail hangs under the staff
        else:
            continue
        found.append((x, y, wide, high, clef, over, under))
    found.sort()
    if OPENING and len(found) >= 2:
        # The lines of a staff can go on to the left of the line that opens the system, and the shadow of a binding
        # stands there. A mark before that line is no clef when a clef stands right after the line.
        for _, begin, end in opening:
            before = [mark for mark in found if x0 + mark[0] + mark[2] <= begin]
            after = [mark for mark in found if 0 <= x0 + mark[0] - end <= OPENING * space]
            if before and after:
                found = [mark for mark in found if x0 + mark[0] + mark[2] > begin]
                break
    best = found[0] if found else None
    if best is None:
        return {'clef': None, 'x0': float(staff['x0']), 'x1': float(staff['x0']), 'over': 0.0, 'under': 0.0, 'wide': 0.0,
                'left': float(staff['x0'])}
    x, y, wide, high, clef, over, under = best
    # Where the staff begins: at the line that opens the system, when the clef stands right after one.
    left = [end for _, begin, end in opening if 0 <= x0 + x - end <= OPENING * space] if OPENING else []
    return {'clef': clef, 'x0': float(x0 + x), 'x1': float(x0 + x + min(wide, 3.4 * space)), 'over': over, 'under': under,
            'wide': wide / space, 'left': float(max(left)) if left else float(staff['x0'])}


def read_start(layers: dict, index: int) -> dict:
    """The beginning of a staff: {'clef' (from its shape), 'x0', 'x1' (of the clef), 'key' (sharps (+) or flats (-)),
    'key_clef' (the clef that the heights of the key signature show, or None), 'miss' (how far the signs stand from
    their places, in pitch places), 'end' (the x where the clef and the key signature end), 'chains' (every chain
    that was found: (clef, kind) -> (signs, miss))}."""
    staff = layers['staves'][index]
    space = staff['space']
    shape = clef_shape(layers, staff)
    start = shape['x0'] if shape['clef'] else float(staff['x0'])
    strokes = start_strokes(layers, staff, int(start + 0.8 * space), int(start + 13 * space))
    signs = sign_candidates(layers, staff, strokes)
    # A sign stands after the clef. A clef wider than a clef can be has a sign that touches it: then the sign may
    # begin where a narrow clef ends.
    least = shape['x1'] - 0.25 * space if shape['wide'] <= 3.4 else shape['x0'] + 2.0 * space
    chains = {}
    for clef in ('G', 'F'):
        for kind in ('sharp', 'flat'):
            found, miss = chain(signs, kind, clef, start, least, space)
            if found:
                chains[(clef, kind)] = (found, miss)
    out = dict(shape, key=0, key_clef=None, miss=0.0, end=shape['x1'], chains=chains, signs=signs)
    if not chains:
        return out
    # The best chain: the most signs; then the clef of the shape; then the nearest to its places.
    def rank(item):
        (clef, kind), (found, miss) = item
        return (len(found), miss <= 0.7 or clef == shape['clef'], clef == shape['clef'], -miss)
    (clef, kind), (found, miss) = max(chains.items(), key=rank)
    out.update(key=len(found) if kind == 'sharp' else -len(found), key_clef=clef, miss=miss, end=max(shape['x1'], found[-1]['x1']))
    return out


def read_starts(layers: dict) -> dict:
    """The clefs and the key of a page: {'key', 'clefs' (one for each staff: 'G' or 'F'), 'ends' (for each staff, the
    x where its clef and key signature end), 'starts' (what read_start() gave for each staff)}.

    The key signature holds for the whole page, so the staves vote for it. The same staff of every system has the
    same clef, so those staves vote too: each with the shape of its clef, and with the heights of its key signature
    when it shows the page's key. A staff without a witness is a bass staff when it is the lowest of a system of two
    or more, and a treble staff when it is not."""
    staves = layers['staves']
    starts = [read_start(layers, index) for index in range(len(staves))]
    votes = {}
    for start in starts:
        # A staff whose clef the copy lost, and that shows no sign, says nothing about the key.
        if start['clef'] or start['key']:
            votes[start['key']] = votes.get(start['key'], 0) + 1
    key = max(votes, key=lambda value: (votes[value], value != 0)) if votes else 0
    width = max(staff['number'] for staff in staves) + 1
    # Choir music is the weak witness: the lowest staff of a system of two or more is a bass staff, the others are
    # treble staves.
    tally = {number: {'G': 0.0 if width >= 2 and number == width - 1 else PRIOR, 'F': PRIOR if width >= 2 and number == width - 1 else 0.0}
             for number in range(width)}
    for start, staff in zip(starts, staves):
        if start['clef'] and start['over'] < 3.1:
            tally[staff['number']][start['clef']] += 1.0
        if key and start['key'] == key and start['key_clef']:
            tally[staff['number']][start['key_clef']] += 2.0 if start['miss'] <= 0.6 else 1.0
    clefs, ends = [], []
    # A clef that the copy lost still takes its room: as much as the clefs that the page shows, from the staff's left end.
    rooms = [(start['x1'] - start['left']) / staff['space'] for start, staff in zip(starts, staves) if start['clef']]
    room = float(np.median(rooms)) if rooms else LOST_CLEF
    kind = 'sharp' if key > 0 else 'flat'
    seen = []          # for each staff: (where its notes begin, what shows it: 'key', 'clef' or None)
    for start, staff in zip(starts, staves):
        votes = tally[staff['number']]
        clefs.append('G' if votes['G'] > votes['F'] else 'F')
        # Where the notes of this staff begin: after its own key signature when it shows the page's key; if not,
        # after the room that the page's key signature takes.
        own = [found for (clef, sort), (found, _) in start['chains'].items() if sort == kind and len(found) >= abs(key)] if key else []
        if own:
            found = max(own, key=lambda signs: signs[0]['x0'] >= start['x1'] - 0.25 * staff['space'])
            seen.append((max(start['x1'], found[abs(key) - 1]['x1']), 'key'))
        elif start['clef']:
            seen.append((start['x1'] + (abs(key) * 1.1 + 1.0) * staff['space'] if key else start['x1'], 'clef'))
        else:
            seen.append((None, None))
    # The page teaches where the notes begin: every system has the same clef and key signature, so they end equally
    # far from the left end of each staff. The staves that show the key signature say it best. A staff that shows
    # nothing (the copy cut off its clef), or whose "clef" stands far to the right (it is a note), begins there too.
    best = 'key' if any(shown == 'key' for _, shown in seen) else 'clef'
    usual = [(end - start['left']) / staff['space'] for (end, shown), start, staff in zip(seen, starts, staves) if shown == best]
    usual = float(np.median(usual)) if usual and USUAL_START else None
    # A staff without a clef begins where the other staves of its system begin.
    lefts = {}
    for start, staff in zip(starts, staves):
        if start['clef']:
            lefts.setdefault(staff['system'], []).append(start['left'])
    for (end, shown), start, staff in zip(seen, starts, staves):
        left = start['left'] if start['clef'] or staff['system'] not in lefts else float(np.median(lefts[staff['system']]))
        if usual is not None and (end is None or (end - left) / staff['space'] > usual + USUAL_START):
            end = left + usual * staff['space']
        elif end is None:
            end = max(start['x1'], left + min(room, 2 * LOST_CLEF) * staff['space'])
            end += (abs(key) * 1.1 + 1.0) * staff['space'] if key else 0.0
        ends.append(end)
    return {'key': key, 'clefs': clefs, 'ends': ends, 'starts': starts}

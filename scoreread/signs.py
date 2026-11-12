"""Reads the sharps, flats and naturals that stand before notes. No model is used.

A sign is read from its upright strokes, as the signs of a key signature are (scoreread.starts). A flat has one
stroke with a bowl at its lower right. The other signs have two strokes side by side, joined by ink: the strokes of
a sharp stand at one height and are as long as each other; the left stroke of a natural stands higher than the right
one; and the right side of a high bowl of a flat is a short stroke at the foot of the long one.

An upright stroke is also a stem, a bar line or a part of a letter, so a sign must pass two more tests: its stroke
is not the stem of a note, and a note head stands right after it, at its height.

The bowl of a flat can look like a small hollow head, and the blot of a small sharp like a small filled head. Such a
head lies on its sign and is much narrower than the heads of the page: it is taken away with the sign. A hand also
draws a sign so near to its note that the two are one mark: then the mark is much wider than the sign, and the sign
changes that note.
"""
from __future__ import annotations

import cv2
import numpy as np

from .starts import PAIR, SIGN_STROKE, _ink, sign_candidates, start_strokes

BEFORE = (-0.45, 1.7)    # a head begins this far right of the right edge of its sign, in staff spaces
HIGH = 1.2               # and its place is at most this many pitch places from the sign's place
STEP = 0.3               # the left stroke of a natural stands at least this many staff spaces higher than the right
LEVEL = 0.6              # the strokes of a sharp begin and end at most this many staff spaces apart in height
EVEN = 0.72              # and the shorter one has at least this share of the longer one's height
NARROW = 0.62            # a head on a sign is a part of the sign when it is narrower than this share of the page's heads
GLUED = 0.6              # a head that a sign touches reaches this share of a head's width past the sign
BOWL_HEAD = True         # a head without a stem that lies on a flat is the flat's bowl
TANGLE = (1.2, 1.4, 2.4, 0.4)   # a sharp that a quick hand scribbled: at least this wide, from this to this high (staff
                                # spaces), with at least this much ink (staff spaces squared) (None: such sharps are not read)
TANGLE_CROSS = (0.4, 0.15)      # its two bars cross this share of its columns, and its two strokes this share of its rows
TANGLE_NEAR = (2.0, 0.7)        # it begins at most this many staff spaces before its head, and its middle lies at most
                                # this many staff spaces over or under the middle of the head
TANGLE_SPECK = 0.04             # a piece of ink under this area (staff spaces squared) is a speck, no stroke of it
TANGLE_HOLE = 0.08              # the paper that it closes in is at most this share of its box: an oval is a head
SHARP_STEM = True                # the right stroke of a sharp can stand right beside the stem of its note (False: off)
SHARP_JOINED = (1.8, 0.5, 1.1, 0.15)   # a small sharp of a heavy print whose two strokes are one mark: at least this high,
                                # from this to this wide (staff spaces), with ink at both sides in the top and in the
                                # bottom share of its rows, and a piece of paper closed in between its bars (None: off)


JOINED_BARE = True              # the ends of a joined sign are looked at without the staff lines: a line through the top
                                # of a natural is no second stroke; such a mark with its left stroke alone at the top
                                # and its right one alone at the bottom is a natural (False: as before)
SIGN_WORDS = True               # the strokes of a sign are read without the rows of the words (False: with them)
GLUED_CHORD = True              # a sign glued to the heads of a chord: it lies on all of them and changes the one at
                                # its place (False: a sign that lies on a head at another place is none)


def pair_signs(layers: dict, staff: dict, strokes: list[dict]) -> list[dict]:
    """The signs that two upright strokes show: {'kind', 'x0', 'x1', 'place', 'top', 'bottom'}."""
    space, rows = staff['space'], staff['rows']
    slim = [stroke for stroke in strokes if 0.9 <= stroke['high'] <= SIGN_STROKE[1] and stroke['wide'] <= 0.45]
    found, used = [], set()
    for number, left in enumerate(slim):
        if id(left) in used:
            continue
        for right in slim[number + 1:]:
            if id(right) in used or not PAIR[0] * space <= right['x'] - left['x'] <= PAIR[1] * space:
                continue
            top, bottom = max(left['top'], right['top']), min(left['bottom'], right['bottom'])
            if bottom - top < 0.45 * space:
                continue
            # Ink joins the two strokes, in the rows that both have.
            gap = max(1.0, right['x0'] - left['x1'] - 1)
            if _ink(layers, left['x1'] + 1, right['x0'] - 1, top, bottom) < 0.25 * gap * min(0.5 * space, bottom - top):
                continue
            higher, lower = (right['top'] - left['top']) / space, (right['bottom'] - left['bottom']) / space
            even = min(left['high'], right['high']) / max(left['high'], right['high'])
            if higher >= STEP and lower >= STEP and left['high'] <= 2.6 and right['high'] <= 2.6 and bottom - top <= 1.5 * space:
                kind, middle = 'natural', (top + bottom) / 2
            elif higher >= 0.4 and abs(lower) <= 0.45 and even <= 0.75 and left['high'] >= 1.4:
                kind, middle = 'flat', (right['top'] + right['bottom']) / 2
            elif abs(higher) <= LEVEL and abs(lower) <= LEVEL and even >= EVEN and left['high'] >= SIGN_STROKE[0]:
                kind, middle = 'sharp', (min(left['top'], right['top']) + max(left['bottom'], right['bottom'])) / 2
            else:
                continue
            found.append({'kind': kind, 'x0': float(left['x0']), 'x1': float(right['x1']), 'pair': True,
                          'place': 4 - 2 * (middle - rows[0]) / space, 'top': min(left['top'], right['top']),
                          'bottom': max(left['bottom'], right['bottom'])})
            used.add(id(left))
            used.add(id(right))
            break
    return found


def note_signs(layers: dict, index: int, heads: list[dict], first: float) -> list[dict]:
    """The signs of one staff that stand before a head, right of the column `first` (where the key signature ends).
    Each: {'kind': 'sharp', 'flat' or 'natural', 'x0', 'x1', 'place', 'head': the head that it changes, 'drop': the
    small heads that are parts of the sign}."""
    staff = layers['staves'][index]
    space = staff['space']
    wide = layers['head'][0]
    own = [head for head in heads if head['staff'] == index]
    # The heads that a sign cannot be: as wide as the heads of the page, or drawn as one stroke at the end of a stem.
    full = [head for head in own if head.get('thin') or head['x1'] - head['x0'] + 1 >= NARROW * wide]
    small = [head for head in own if not any(head is other for other in full)]

    def stem_of_head(stroke: dict, beside: float = 0.3) -> bool:
        for head in full:
            for stem in head['stems']:
                top, bottom = min(head['cy'], stem['end']), max(head['cy'], stem['end'])
                if stroke['x0'] - beside * space <= stem['x'] <= stroke['x1'] + beside * space \
                        and min(bottom, stroke['bottom']) - max(top, stroke['top']) >= 0.5 * (stroke['bottom'] - stroke['top']):
                    return True
        return False

    def lying(sign: dict, group: list[dict]) -> list[dict]:
        return [head for head in group
                if min(sign['x1'], head['x1']) - max(sign['x0'], head['x0']) >= 0.5 * min(sign['x1'] - sign['x0'] + 1, head['x1'] - head['x0'] + 1)
                and head['y1'] >= sign['top'] and head['y0'] <= sign['bottom']]

    strokes = start_strokes(layers, staff, int(first), int(staff['x1']), layers.get('words') if SIGN_WORDS else None)
    strokes = [stroke for stroke in strokes if 0.9 <= stroke['high'] <= SIGN_STROKE[1]]
    kept = [stroke for stroke in strokes if not stem_of_head(stroke)]
    if SHARP_STEM:
        # A small sharp right before a note with a stem that goes down: its right stroke stands beside the stem,
        # but it is the second stroke of a sharp, and the stem is another stroke.
        for sign in pair_signs(layers, staff, strokes):
            if sign['kind'] != 'sharp':
                continue
            left = next((stroke for stroke in kept if stroke['x0'] == sign['x0']), None)
            right = next((stroke for stroke in strokes if stroke['x1'] == sign['x1'] and stroke['x0'] > sign['x0']), None)
            if left is not None and right is not None and not any(right is stroke for stroke in kept) and not stem_of_head(right, 0.0):
                kept.append(right)
        kept.sort(key=lambda stroke: stroke['x'])
    strokes = kept
    signs = pair_signs(layers, staff, strokes)
    taken = [(sign['x0'], sign['x1']) for sign in signs]
    for sign in sign_candidates(layers, staff, strokes):
        if any(x0 - 2 <= sign['x0'] <= x1 + 2 for x0, x1 in taken):
            continue
        if sign['kind'] == 'flat':
            signs.append(sign)
        elif SHARP_JOINED and sign.get('joined'):
            kind = _joined_sharp(layers, sign, space)
            if kind:
                signs.append(dict(sign, kind=kind))
    out = []
    for sign in signs:
        place = sign['bowl_place'] if sign.get('bowl_place') is not None else sign['place']
        on = lying(sign, full)
        if BOWL_HEAD and sign['kind'] == 'flat':
            # The bowl of a flat that a hand drew large is an oval as wide as a head: a head without a stem that
            # lies on a flat is its bowl.
            bowls = [head for head in on if not head['stems'] and not head.get('thin')]
            on = [head for head in on if not any(head is bowl for bowl in bowls)]
        else:
            bowls = []
        # A head that the sign touches: one mark, much wider than the sign.
        glued = [head for head in on if head['x1'] - sign['x1'] >= GLUED * wide and abs(head['place'] - place) <= HIGH]
        past = [head for head in on if head['x1'] - sign['x1'] >= GLUED * wide]
        if on and (len(past) != len(on) or not glued if GLUED_CHORD else len(glued) != len(on)):
            continue
        drop = lying(sign, small) + bowls
        best = None
        for head in own:
            if any(head is other for other in drop):
                continue
            ahead = (head['x0'] - sign['x1']) / space
            if any(head is other for other in glued) or (BEFORE[0] <= ahead <= BEFORE[1] and abs(head['place'] - place) <= HIGH):
                rank = (not any(head is other for other in glued), abs(head['place'] - place) > 0.8, ahead)
                if best is None or rank < best[0]:
                    best = (rank, head)
        if best:
            out.append(dict(sign, head=best[1], drop=drop))
    if TANGLE:
        signed = {id(sign['head']) for sign in out} | {id(head) for sign in out for head in sign['drop']}
        for head in full:
            if id(head) not in signed and head['x0'] - TANGLE_NEAR[0] * space > first:
                sign = tangle_sign(layers, staff, head, own)
                if sign:
                    out.append(dict(sign, head=head, drop=lying(sign, small)))
    return out


def _joined_sharp(layers: dict, sign: dict, space: float) -> str | None:
    """'sharp' when one wide stroke is a sharp whose two strokes a heavy print joined: both strokes stand out over and
    under the bars, and the strokes and the bars close in a piece of paper. 'natural' when its left stroke stands
    alone at the top and its right one alone at the bottom. None when it is neither."""
    x0, x1, top, bottom = int(sign['x0']), int(sign['x1']) + 1, int(sign['top']), int(sign['bottom']) + 1
    high, wide = bottom - top, x1 - x0
    if not (SHARP_JOINED[0] * space <= high <= SIGN_STROKE[1] * space and SHARP_JOINED[1] * space <= wide <= SHARP_JOINED[2] * space):
        return None
    ink = layers['ink'][top:bottom, x0:x1]
    ends = layers['bare'][top:bottom, x0:x1] if JOINED_BARE else ink
    middle, edge = wide // 2, max(2, int(round(SHARP_JOINED[3] * high)))
    sides = [(bool(part[:, :middle].any()), bool(part[:, middle:].any())) for part in (ends[:edge], ends[-edge:])]
    if sides == [(True, False), (False, True)] and JOINED_BARE:
        kind = 'natural'
    elif sides == [(True, True), (True, True)]:
        kind = 'sharp'
    else:
        return None
    # The paper between the strokes and the bars, in the middle of the sign: closed in on all sides.
    box = np.pad(1 - ink, 1, constant_values=1).astype(np.uint8)
    count, labels, stats, middles = cv2.connectedComponentsWithStats(box, connectivity=4)
    outside = labels[0, 0]
    return kind if any(label != outside and stats[label, cv2.CC_STAT_AREA] >= 2 and 0.25 * high <= middles[label][1] - 1 <= 0.75 * high
                       for label in range(1, count)) else None


def _runs(part: np.ndarray) -> np.ndarray:
    """How many runs of ink each row of a mask has."""
    return (part[:, 1:] > part[:, :-1]).sum(axis=1) + part[:, 0]


def tangle_sign(layers: dict, staff: dict, head: dict, heads: list[dict]) -> dict | None:
    """The sharp that a quick hand scribbled before a head: a small tangle of thin ink, its strokes leaning and
    running into each other, so that no stroke of it is upright. It is told by what a sharp is: two bars that
    cross two strokes. A line down through it meets ink twice (the two bars), and a line across it meets ink twice
    too (the two strokes). A letter, a dot, a slur and the end of a ledger line do not show both. The tangle is all
    the ink that lies whole in the room before the head; ink that goes on out of that room belongs to something else,
    and a speck is no stroke."""
    space = staff['space']
    ink = layers['bare'] & (1 - layers['stems'])
    height, width = ink.shape
    x0, x1 = int(head['x0'] - (TANGLE_NEAR[0] + 0.4) * space), int(head['x0'] + 0.05 * space)
    y0, y1 = int(head['cy'] - 2.0 * space), int(head['cy'] + 2.0 * space)
    if x0 < 1 or y0 < 1 or y1 >= height - 1 or x1 >= width - 1:
        return None
    count, labels, stats, _ = cv2.connectedComponentsWithStats(np.ascontiguousarray(ink[y0:y1 + 1, x0:x1 + 1]), connectivity=8)
    inner = (int(round(0.4 * space)), int(round(0.5 * space)))
    keep = []
    for index in range(1, count):
        x, y, wide, high, area = stats[index]
        whole = x > 0 and y > 0 and x + wide < labels.shape[1] and y + high < labels.shape[0]
        near = x + wide > inner[0] and x < labels.shape[1] - int(round(0.15 * space)) \
            and y + high > inner[1] and y < labels.shape[0] - inner[1]
        if whole and near and area >= TANGLE_SPECK * space * space:
            keep.append(index)
    if not keep:
        return None
    left, right = min(stats[index][0] for index in keep), max(stats[index][0] + stats[index][2] for index in keep)
    top, bottom = min(stats[index][1] for index in keep), max(stats[index][1] + stats[index][3] for index in keep)
    part = np.isin(labels[top:bottom, left:right], keep).astype(np.uint8)
    wide, high, area = (right - left) / space, (bottom - top) / space, float(part.sum()) / space ** 2
    if not (wide >= TANGLE[0] and TANGLE[1] <= high <= TANGLE[2] and area >= TANGLE[3]):
        return None
    middle = y0 + (top + bottom) / 2
    if abs(head['cy'] - middle) > TANGLE_NEAR[1] * space:
        return None
    if float((_runs(part.T) >= 2).mean()) < TANGLE_CROSS[0] or float((_runs(part) >= 2).mean()) < TANGLE_CROSS[1]:
        return None
    # The strokes of a sharp close in a small room of paper at most. An oval closes in a large one: a hollow head.
    paper = (1 - np.pad(part, 1)).astype(np.uint8)
    rooms, _, room_stats, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
    closed = [room_stats[room][4] for room in range(1, rooms)
              if room_stats[room][0] > 0 and room_stats[room][1] > 0 and room_stats[room][0] + room_stats[room][2] < paper.shape[1]
              and room_stats[room][1] + room_stats[room][3] < paper.shape[0]]
    if max(closed, default=0) > TANGLE_HOLE * part.size:
        return None
    sign = {'kind': 'sharp', 'x0': float(x0 + left), 'x1': float(x0 + right - 1), 'top': float(y0 + top),
            'bottom': float(y0 + bottom - 1), 'place': 4 - 2 * (middle - staff['rows'][0]) / space, 'tangle': True}
    # A head that lies on the tangle: the tangle is a part of that note, or the note a part of something else.
    box = (sign['x1'] - sign['x0'] + 1) * (sign['bottom'] - sign['top'] + 1)
    wide_head = layers['head'][0]
    for other in heads:
        if other.get('thin') or other['x1'] - other['x0'] + 1 >= NARROW * wide_head:
            over = min(sign['x1'], other['x1']) - max(sign['x0'], other['x0'])
            tall = min(sign['bottom'], other['y1']) - max(sign['top'], other['y0'])
            if over > 0 and tall > 0 and over * tall >= 0.3 * min(box, (other['x1'] - other['x0'] + 1) * (other['y1'] - other['y0'] + 1)):
                return None
    return sign

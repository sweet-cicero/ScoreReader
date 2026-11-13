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
FLAT_LEG = (0.35, 0.1, 0.4, 0.6)   # a flat whose bowl has a second stroke as its right wall is a natural: the stroke stands
#                    from this far before the sign's right edge to this far past it, begins this far under the sign's
#                    top or lower, and ends this far under its bottom (staff spaces; None: off)
SIGN_START = 0.3     # a stroke in the first columns of the notes (this many staff spaces) whose ink goes on to the left
#                    of them, in this many staff spaces of its rows, is the cut end of the clef or of the key: no sign
#                    of a note (0: off)
PAIR_WIDE = 0.6          # each of the two strokes of a sharp is at most this wide, in staff spaces (0.45: as it was, and
#                          as it is for a flat and a natural; a heavy print draws the strokes of a sharp half a staff
#                          space wide)
PAIR_FREE = True         # a sharp with a stroke wider than 0.45 staff spaces stands free: two heavy strokes that lie on a
#                          head are a part of that head (its rim, or the stroke at the side of a breve). False: off
SHARP_HEAD = (1.7, 0.3, 1.4, 0.95)   # a heavy sharp whose middle closed is no head: a mark with a stem that lies on the two
#                          strokes of a sharp (each this many staff spaces high or more), reaches less than this share of
#                          a head's width past them, and is this many staff spaces high or more, or narrower than this
#                          share of the page's heads (None: off)
NATURAL_STEM = 1.8       # the right stroke of a natural stands beside the stem of its note, or was taken for a second stem
#                          of its head that ends at most this many staff spaces from the head's middle (None: off)
SHARP_STEM = True                # the right stroke of a sharp can stand right beside the stem of its note (False: off)
SHARP_JOINED = (1.8, 0.5, 1.1, 0.15, 0.5)   # a small sharp of a heavy print whose two strokes are one mark: at least
                                # this high, from this to this wide (staff spaces), with ink at both sides in the top
                                # and in the bottom share of its rows, and a piece of paper closed in between its bars.
                                # It stands before its head: a mark that lies in the box of a head without a stem by
                                # more than this share of its width is a part of that head (the stroke at the side of
                                # a breve, the long reciting note). (None: off. Without the last test the rule gained 11 notes on
                                # LitChoir's clean copies and lost 1, but lost 29 on the fresh test set.)


JOINED_BARE = True              # the ends of a joined sign are looked at without the staff lines: a line through the top
                                # of a natural is no second stroke; such a mark with its left stroke alone at the top
                                # and its right one alone at the bottom is a natural (False: as before)
SIGN_WORDS = True               # the strokes of a sign are read without the rows of the words (False: with them)
GLUED_CHORD = True              # a sign glued to the heads of a chord: it lies on all of them and changes the one at
                                # its place (False: a sign that lies on a head at another place is none)


NATURAL_ROWS = 1.9       # the two strokes of a natural stand side by side for at most this many staff spaces (1.5: as it
#                          was; the naturals of a heavy print are higher)
NATURAL_WIDE = 0.5        # each stroke of a natural is at most this wide, in staff spaces (0.45: as it was, and as a flat's
#                          stem; a small heavy print has naturals with strokes of 0.46 and 0.47)
NATURAL_LOW = (0.2, 0.3, 0.1)   # two nearly level strokes are a natural and no sharp: the right one begins this many staff
#                          spaces lower than the left one, begins and ends this much lower together, and at most this
#                          much ink sticks out at the left of the left one (None: off)
SIGN_BAR = (0.8, 0.6, 0.4)      # a flat or a natural that stands against a bar line, read as a hollow head with the
#                                 bar line as its stem: the mark is at most this share as wide as the heads of the page,
#                                 a head begins at most this many staff spaces after it, and the right stroke of a
#                                 natural goes on this far under the mark (None: off)


def bar_signs(layers: dict, heads: list[dict]) -> list[dict]:
    """The signs that stand against a bar line. An engraver can set the sign of the first note of a bar so close to
    the bar line that they are one piece of ink: the box of the natural or the bowl of the flat is then a small hollow
    head, and the bar line its stem. But a stem begins at its head, and this line goes through from the top line of
    the staff to the bottom line; the mark is narrower than a head, and the note that it changes follows at once.
    Each: {'kind', 'staff', 'x0', 'x1', 'top', 'bottom', 'place', 'bar': the column of the bar line, 'mark': the head
    that the sign was read as, 'head': the head that it changes}."""
    if not SIGN_BAR:
        return []
    ink, wide, out = layers['ink'], layers['head'][0], []
    for index, staff in enumerate(layers['staves']):
        space, top, bottom = staff['space'], int(staff['rows'][0]), int(staff['rows'][4])
        own = [head for head in heads if head['staff'] == index]
        for mark in own:
            if not mark['hollow'] or mark.get('thin') or len(mark['stems']) != 1 \
                    or mark['x1'] - mark['x0'] + 1 > SIGN_BAR[0] * wide or not top <= mark['cy'] <= bottom:
                continue
            x = int(round(mark['stems'][0]['x']))
            if x > mark['x0'] + 0.3 * (mark['x1'] - mark['x0']) or x < 1:
                continue
            if ink[top:bottom + 1, x - 1:x + 2].any(axis=1).mean() < 0.9:
                continue
            after = [head for head in own if head is not mark and not head.get('thin')
                     and -0.2 * space <= head['x0'] - mark['x1'] <= SIGN_BAR[1] * space
                     and abs(head['place'] - mark['place']) <= HIGH and head['x1'] - head['x0'] + 1 > SIGN_BAR[0] * wide]
            if not after:
                continue
            strokes = [stroke for stroke in start_strokes(layers, staff, int(mark['x0'] - space), int(mark['x1'] + 0.6 * space))
                       if mark['cx'] - 0.1 * space <= stroke['x'] and stroke['x1'] <= mark['x1'] + 0.15 * space
                       and stroke['wide'] <= 0.45 and stroke['high'] <= SIGN_STROKE[1]
                       and stroke['top'] <= mark['cy'] and stroke['bottom'] >= mark['y1'] + SIGN_BAR[2] * space]
            if any(stroke['top'] < mark['y0'] - 0.3 * space for stroke in strokes):
                continue      # a stroke that goes on over the mark and under it: no natural and no flat
            head = min(after, key=lambda head: (abs(head['place'] - mark['place']) > 0.8, head['x0']))
            out.append({'kind': 'natural' if strokes else 'flat', 'staff': index, 'x0': float(mark['x0']),
                        'x1': float(max([mark['x1']] + [stroke['x1'] for stroke in strokes])), 'top': float(mark['y0']),
                        'bottom': float(mark['y1']), 'place': float(mark['place']), 'bar': float(x), 'mark': mark,
                        'head': head, 'drop': []})
    return out


def _out_left(layers: dict, left: dict, top: float, bottom: float, space: float) -> float:
    """How much ink sticks out at the left of a stroke in the rows top..bottom, without the staff lines: the rows
    that have ink in the quarter of a staff space before the stroke, in staff spaces. The bars of a sharp do."""
    wide = max(2, int(round(0.25 * space)))
    part = layers['bare'][int(top):int(bottom) + 1, max(0, int(left['x0']) - wide):int(left['x0'])]
    return float(part.any(axis=1).sum()) / space if part.size else 0.0


def pair_signs(layers: dict, staff: dict, strokes: list[dict]) -> list[dict]:
    """The signs that two upright strokes show: {'kind', 'x0', 'x1', 'place', 'top', 'bottom'}."""
    space, rows = staff['space'], staff['rows']
    slim = [stroke for stroke in strokes if 0.9 <= stroke['high'] <= SIGN_STROKE[1] and stroke['wide'] <= PAIR_WIDE]
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
            if higher >= STEP and lower >= STEP and left['high'] <= 2.6 and right['high'] <= 2.6 \
                    and bottom - top <= NATURAL_ROWS * space:
                kind, middle = 'natural', (top + bottom) / 2
            elif higher >= 0.4 and abs(lower) <= 0.45 and even <= 0.75 and left['high'] >= 1.4:
                kind, middle = 'flat', (right['top'] + right['bottom']) / 2
            elif abs(higher) <= LEVEL and abs(lower) <= LEVEL and even >= EVEN and left['high'] >= SIGN_STROKE[0]:
                kind, middle = 'sharp', (min(left['top'], right['top']) + max(left['bottom'], right['bottom'])) / 2
                if NATURAL_LOW and higher >= NATURAL_LOW[0] and lower >= 0 and higher + lower >= NATURAL_LOW[1] \
                        and left['high'] <= 2.6 and right['high'] <= 2.6 and bottom - top <= NATURAL_ROWS * space \
                        and max(left['wide'], right['wide']) <= 0.45 \
                        and _out_left(layers, left, top, bottom, space) <= NATURAL_LOW[2]:
                    # The natural of a heavy print: its box is high and the free ends of its strokes are short, so
                    # the strokes are nearly level, as a sharp's are. But its right stroke stands lower at both ends
                    # (a sharp's stands level or higher), and no bar sticks out at the left of its left stroke.
                    kind, middle = 'natural', (top + bottom) / 2
            else:
                continue
            if kind != 'sharp' and max(left['wide'], right['wide']) > (NATURAL_WIDE if kind == 'natural' else 0.45):
                continue      # only a sharp has two heavy strokes: the rim of a large hollow head is no flat
            found.append({'kind': kind, 'x0': float(left['x0']), 'x1': float(right['x1']), 'pair': True,
                          'wide': float(max(left['wide'], right['wide'])),
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
    if SIGN_START:
        # A stroke in the first columns is ink that was cut there, when its ink goes on to the left: the right bow of
        # the clef, or the last sign of the key.
        ink, begin = layers['bare'], int(first)
        def cut(stroke: dict) -> bool:
            if stroke['x0'] > begin + SIGN_START * space or begin < 4:
                return False
            rows = ink[int(stroke['top']):int(stroke['bottom']) + 1, begin - 4:max(begin - 1, int(stroke['x0']))]
            return int(rows.any(axis=1).sum()) >= SIGN_START * space
        strokes = [stroke for stroke in strokes if not cut(stroke)]
    every = strokes
    ghosts = []
    if SHARP_HEAD:
        # The middle of a heavy sharp closes in a print, and the mark is taken for a head with one of the strokes as
        # its stem. A head stands beside its stem; this mark lies between two strokes that are both as long as a
        # sharp's, and it is higher than a head or narrower.
        for sign in pair_signs(layers, staff, strokes):
            if sign['kind'] != 'sharp':
                continue
            parts = [stroke for stroke in strokes if sign['x0'] <= stroke['x'] <= sign['x1']]
            if len(parts) < 2 or min(stroke['high'] for stroke in parts) < SHARP_HEAD[0]:
                continue
            for head in lying(sign, full):
                if head.get('thin') or not head['stems'] or head['x1'] - sign['x1'] >= SHARP_HEAD[1] * wide:
                    continue
                if head['y1'] - head['y0'] + 1 >= SHARP_HEAD[2] * space or head['x1'] - head['x0'] + 1 < SHARP_HEAD[3] * wide:
                    ghosts.append(head)
        full = [head for head in full if not any(head is ghost for ghost in ghosts)]
    kept = [stroke for stroke in strokes if not stem_of_head(stroke)]
    legs = []
    if SHARP_STEM or NATURAL_STEM:
        # A small sharp right before a note with a stem that goes down: its right stroke stands beside the stem,
        # but it is the second stroke of a sharp, and the stem is another stroke. The same holds for a natural. And
        # the right stroke of a natural at the left side of a head was taken for a second, short stem of that head.
        for sign in pair_signs(layers, staff, strokes):
            if not (sign['kind'] == 'sharp' and SHARP_STEM or sign['kind'] == 'natural' and NATURAL_STEM):
                continue
            left = next((stroke for stroke in kept if stroke['x0'] == sign['x0']), None)
            right = next((stroke for stroke in strokes if stroke['x1'] == sign['x1'] and stroke['x0'] > sign['x0']), None)
            if left is None or right is None or any(right is stroke for stroke in kept):
                continue
            if not stem_of_head(right, 0.0):
                kept.append(right)
            elif sign['kind'] == 'natural':
                for head in full:
                    for stem in head['stems']:
                        if len(head['stems']) >= 2 and right['x0'] <= stem['x'] <= right['x1'] \
                                and abs(stem['end'] - head['cy']) <= NATURAL_STEM * space \
                                and right['top'] <= head['cy'] <= right['bottom'] and not any(right is leg[0] for leg in legs):
                            legs.append((right, head, stem))
                            kept.append(right)
        kept.sort(key=lambda stroke: stroke['x'])
    strokes = kept
    signs = pair_signs(layers, staff, strokes)
    taken = [(sign['x0'], sign['x1']) for sign in signs]
    for sign in sign_candidates(layers, staff, strokes, beams=True):
        if any(x0 - 2 <= sign['x0'] <= x1 + 2 for x0, x1 in taken):
            continue
        if sign['kind'] == 'flat':
            if FLAT_LEG and any(sign['x1'] - FLAT_LEG[0] * space <= stroke['x'] <= sign['x1'] + FLAT_LEG[1] * space
                                and sign['top'] + FLAT_LEG[2] * space <= stroke['top'] <= sign['bottom']
                                and stroke['bottom'] >= sign['bottom'] + FLAT_LEG[3] * space
                                and stroke['wide'] <= 0.45 and not stem_of_head(stroke, 0.0) for stroke in every):
                # A stroke that leaves the bowl at its right and goes on down: the second stroke of a natural. (It
                # can stand close beside the stem of the note.)
                sign = dict(sign, kind='natural')
            signs.append(sign)
        elif SHARP_JOINED and sign.get('joined'):
            kind = _joined_sharp(layers, sign, space)
            if kind:
                signs.append(dict(sign, kind=kind))
    out = []
    for sign in signs:
        place = sign['bowl_place'] if sign.get('bowl_place') is not None else sign['place']
        on = lying(sign, full)
        if PAIR_FREE and on and sign.get('wide', 0.0) > 0.45:
            continue      # a heavy stroke and the rim of a hollow head, or the stroke at the side of a breve
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
        drop = lying(sign, small) + bowls + lying(sign, ghosts)
        best = None
        for head in own:
            if any(head is other for other in drop):
                continue
            ahead = (head['x0'] - sign['x1']) / space
            if any(head is other for other in glued) or (BEFORE[0] <= ahead <= BEFORE[1] and abs(head['place'] - place) <= HIGH):
                rank = (not any(head is other for other in glued), abs(head['place'] - place) > 0.8, ahead)
                if best is None or rank < best[0]:
                    best = (rank, head)
        if best and sign.get('joined') and SHARP_JOINED and SHARP_JOINED[4]:
            head = best[1]
            if not head['stems'] and min(sign['x1'], head['x1']) - max(sign['x0'], head['x0']) + 1 > SHARP_JOINED[4] * (sign['x1'] - sign['x0'] + 1):
                continue      # a part of the head, no sign before it
        if best:
            for right, head, stem in legs:
                if sign['kind'] == 'natural' and right['x1'] == sign['x1'] and head is best[1]:
                    head['stems'] = [other for other in head['stems'] if other is not stem]     # no stem: the sign's stroke
                    head.get('tails', {}).pop(stem['direction'], None)
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

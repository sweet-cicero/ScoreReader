"""Finds the brackets of triplets, and the notes that stand under them. No model is used.

Three notes that sound in the time of two stand under a bracket with a number: a flat stroke over or under the
notes, with a short hook at each end that points to them, and broken in the middle for the number. Each half of the
bracket is a free piece of ink of its own: a long thin arm with a hook at its outer end. Two such halves at one
height, with a small piece of ink in the break between them, are a bracket; a slur, a tie, the line after a
syllable and a hairpin have no hooks, and the bracket of a first ending has no break.

The number is not read: it is taken for a 3, the only one in the hymns so far. The notes between the hooks, on the
side the hooks point to, are each two thirds as long as they are drawn. Where two voices stand there, the bracket
belongs to the voice on its side: over the staff to the stems that go up, under it to the stems that go down.
"""
from __future__ import annotations

from fractions import Fraction

import cv2
import numpy as np

TRIPLETS = True
ARM = (1.0, 0.3, 0.3)          # the arm of a half bracket is at least this many staff spaces long, at most this thick,
#                                and its height changes by at most this much along it
HOOK = (0.3, 2.0, 0.4)         # the hook is from this to this many staff spaces high, and lies in this much of the outer end
BREAK = (0.4, 3.5)             # the break between the two arms is from this to this many staff spaces wide
LEVEL = 0.35                   # the two arms lie at one height, at most this many staff spaces apart
NUMBER = (0.6, 1.9)            # the number in the break is from this to this many staff spaces high
FAR = 6.0                      # a bracket lies at most this many staff spaces from the nearest end of its notes
REACH = 0.9                    # a note of the bracket stands at most this many staff spaces outside the hooks
MEND = 0.25                    # breaks of an arm up to this many staff spaces wide are closed for a second look (0: off)
TOGETHER = 0.6                 # the other voices of the system sing a triplet too when their notes stand in its columns, at most
#                                this many staff spaces off (0: off)
IN_WORDS = (0.3, 1.2, 4.0, 0.5, 0.2, 0.08)   # the hyphens of the words with a syllable between them and an l at each
#  outer end look like a bracket (Al-le-lu). A bracket whose row lies in a band of the words, or at most this many
#  staff spaces outside it, is a piece of the words when the words go on at both of its sides (in the rows up to this
#  many staff spaces over and under its row, the columns up to this many staff spaces beside each hook hold this
#  much ink or more, in squares of a staff space) and its arms are not whole: within this many staff spaces of its
#  row, this share or more of the columns between the hooks is bare beside the two widest gaps. The arms of a
#  bracket are two unbroken lines, and the number in the break between them leaves a gap at each of its sides
#  (at most 0.02 on the pages the limit was set on, 0.16 in the words). (None: off)
RATIO = Fraction(2, 3)         # a note of a triplet has this share of its drawn length


def _half(piece: np.ndarray, space: float) -> dict | None:
    """A free piece of ink as one half of a bracket: {'hook': 'left' | 'right', 'points': 'down' | 'up', 'row': the
    arm's row in the piece}, or None when it is something else."""
    high, wide = piece.shape
    if wide < ARM[0] * space or not HOOK[0] * space <= high <= HOOK[1] * space:
        return None
    top = piece.argmax(axis=0)
    bottom = high - 1 - piece[::-1].argmax(axis=0)
    thick = bottom - top + 1
    tall = np.flatnonzero(thick >= 0.7 * high)
    end = HOOK[2] * space
    if len(tall) == 0:
        return None
    if tall.max() <= end:
        side, arm = 'left', slice(int(end) + 1, wide)
    elif tall.min() >= wide - 1 - end:
        side, arm = 'right', slice(0, wide - 1 - int(end))
    else:
        return None
    flat = thick[arm] <= ARM[1] * space
    if len(flat) < 0.5 * ARM[0] * space or flat.mean() < 0.9:
        return None
    middle = ((top[arm] + bottom[arm]) / 2)[flat]
    if middle.max() - middle.min() > ARM[2] * space:
        return None
    row = float(np.median(middle))
    # The arm lies at one edge of the piece, and the hook goes from it to the other edge.
    if min(row, high - 1 - row) > max(ARM[1] * space, 0.3 * high):
        return None
    return {'hook': side, 'points': 'down' if row < high / 2 else 'up', 'row': row}


def brackets(layers: dict) -> list[dict]:
    """The brackets of a page: {'x0', 'x1' (the hooks), 'y' (the arm's row), 'points': 'down' when the hooks point
    down (the notes stand under the bracket) or 'up'} each."""
    if not TRIPLETS:
        return []
    space = layers['space']
    found = _brackets(layers['bare'], space)
    if MEND:
        # A faint print breaks an arm, or parts the arm from its hook: the breaks are closed, and the brackets that
        # show only then are added.
        size = max(3, int(round(MEND * space)) | 1)
        mended = cv2.morphologyEx(layers['bare'].astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, size), np.uint8))
        for bracket in _brackets(mended, space):
            if not any(bracket['x0'] <= other['x1'] and other['x0'] <= bracket['x1'] and abs(bracket['y'] - other['y']) <= space
                       for other in found):
                found.append(bracket)
    return found


def _brackets(bare: np.ndarray, space: float) -> list[dict]:
    """The brackets in one picture of the page's ink without its staff lines."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(bare.astype(np.uint8), connectivity=8)
    halves, small = [], []
    for label in range(1, count):
        x, y, w, h, _ = (int(value) for value in stats[label])
        if NUMBER[0] * space <= h <= NUMBER[1] * space and w <= 1.6 * space:
            small.append((x, y, w, h))
        if w < ARM[0] * space or h > HOOK[1] * space:
            continue
        half = _half(labels[y:y + h, x:x + w] == label, space)
        if half:
            halves.append(dict(half, x0=x, x1=x + w - 1, y=y + half['row']))
    found = []
    for left in halves:
        if left['hook'] != 'left':
            continue
        for right in halves:
            if right['hook'] != 'right' or right['points'] != left['points']:
                continue
            gap = right['x0'] - left['x1']
            if not BREAK[0] * space <= gap <= BREAK[1] * space or abs(left['y'] - right['y']) > LEVEL * space:
                continue
            row = (left['y'] + right['y']) / 2
            # The number stands in the break, on the arms' row.
            if any(left['x1'] < x + w / 2 < right['x0'] and y - 0.5 * space <= row <= y + h + 0.5 * space
                   for x, y, w, h in small):
                found.append({'x0': left['x0'], 'x1': right['x1'], 'y': row, 'points': left['points']})
                break
    return found


def mark_triplets(layers: dict, heads: list[dict]) -> list[dict]:
    """Gives each head under a bracket head['triplet']: the directions of its stems that the bracket holds ('' for a
    head without a stem). Returns the brackets, each with 'heads': how many heads it holds."""
    space = layers['space']
    found = [bracket for bracket in brackets(layers) if not _in_words(layers, bracket)]
    for bracket in found:
        down = bracket['points'] == 'down'
        near = []
        for head in heads:
            ends = [head['cy']] + [stem['end'] for stem in head['stems']]
            xs = [head['cx']] + [stem['x'] for stem in head['stems']]
            if not any(bracket['x0'] - REACH * space <= x <= bracket['x1'] + REACH * space for x in xs):
                continue
            apart = (min(ends) - bracket['y']) if down else (bracket['y'] - max(ends))
            if -0.5 * space <= apart <= FAR * space:
                near.append((apart, head))
        bracket['heads'] = 0
        if not near:
            continue
        staff = min(near, key=lambda item: item[0])[1]['staff']
        own = [head for _, head in near if head['staff'] == staff]
        if len(own) < 2:
            continue
        # Two voices stand there when at least two heads have a stem on the bracket's side, and one a stem on the other.
        side, other = ('up', 'down') if down else ('down', 'up')
        ways = [stem['direction'] for head in own for stem in head['stems']]
        two = ways.count(side) >= 2 and other in ways
        for head in own:
            mine = [stem['direction'] for stem in head['stems']] or ['']
            if two:
                mine = [way for way in mine if way in (side, '')]
            if mine:
                head['triplet'] = sorted(set(head.get('triplet', [])) | set(mine))
                bracket['heads'] += 1
        if TOGETHER and bracket['heads'] >= 2:
            _together(layers, heads, bracket, [head for head in own if head.get('triplet')], space)
    return found


def _in_words(layers: dict, bracket: dict) -> bool:
    """Whether a bracket is a piece of the words by IN_WORDS."""
    if not IN_WORDS or not layers.get('words'):
        return False
    near, rows, reach, least, row, whole = IN_WORDS
    space, bare = layers['space'], layers['bare']
    if not any(band['top'] - near * space <= bracket['y'] <= band['bottom'] + near * space
               and band['x0'] <= bracket['x0'] and bracket['x1'] <= band['x1'] for band in layers['words']):
        return False
    top, bottom = max(0, int(bracket['y'] - rows * space)), int(bracket['y'] + rows * space)
    left = bare[top:bottom, max(0, int(bracket['x0'] - reach * space)):max(0, int(bracket['x0']) - 2)]
    right = bare[top:bottom, int(bracket['x1']) + 3:int(bracket['x1'] + reach * space)]
    if min(left.sum(), right.sum()) < least * space * space:
        return False
    arms = bare[max(0, int(bracket['y'] - row * space)):int(bracket['y'] + row * space) + 1, int(bracket['x0']):int(bracket['x1']) + 1]
    inked = arms.any(axis=0)
    edges = np.flatnonzero(np.diff(np.concatenate(([1], inked.astype(np.int8), [1]))))
    gaps = sorted(edges[1::2] - edges[::2])
    beside = len(inked) - int(sum(gaps[-2:]))
    return beside > 0 and int(sum(gaps[:-2])) >= whole * beside


def _together(layers: dict, heads: list[dict], bracket: dict, own: list[dict], space: float) -> None:
    """Notes that sound together agree: a choir sings a triplet in all its voices, and the page draws one bracket,
    over the top staff or under the bottom one. A voice of the same system whose notes stand in the columns of the
    bracket's notes, one in each column and no other between the hooks, sings the triplet too."""
    staves = layers['staves']
    system = staves[own[0]['staff']]['system']
    columns = []
    for head in sorted(own, key=lambda head: head['cx']):
        if not columns or head['cx'] - columns[-1] > 0.8 * space:
            columns.append(head['cx'])
    if len(columns) < 2:
        return
    inside = [head for head in heads if staves[head['staff']]['system'] == system
              and bracket['x0'] - REACH * space <= head['cx'] <= bracket['x1'] + REACH * space]
    voices: dict[tuple, list[dict]] = {}
    for head in inside:
        for way in [stem['direction'] for stem in head['stems']] or ['']:
            voices.setdefault((head['staff'], way), []).append(head)
    for (staff, way), group in voices.items():
        at = [min(range(len(columns)), key=lambda number: abs(columns[number] - head['cx'])) for head in group]
        if any(abs(columns[number] - head['cx']) > TOGETHER * space for number, head in zip(at, group)):
            continue
        if set(at) != set(range(len(columns))):
            continue
        for head in group:
            head['triplet'] = sorted(set(head.get('triplet', [])) | {way})

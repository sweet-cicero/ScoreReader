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
    bare, space = layers['bare'], layers['space']
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
    found = brackets(layers)
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
    return found

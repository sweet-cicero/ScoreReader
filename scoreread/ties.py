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
TIE_SIDE = 0.9          # it begins and ends at most this many staff spaces from the heads, sideways
TIE_HIGH = 1.4          # and at most this many staff spaces over or under their middle
TIE_GAP = 0.5           # it may break for this many staff spaces
TIE_SEEN = (0.6, 0.9)   # its ink shows in this share of the columns; its ink or a staff line that hides it in this share
TIE_BOW = (0.2, 3.5)    # the bow is at least and at most this many staff spaces high
TIE_EVEN = 1.0          # its highest place lies in the middle part: the two ends differ by at most this many bow heights
TIE_SMOOTH = 0.35       # and it leaves the curve of a bow by at most this share of its height


def _follow(thin: np.ndarray, lines: np.ndarray, x: int, y: float, last: int, space: float) -> dict | None:
    """Follows thin ink from (x, y) toward the column `last`, to where it breaks off: {'rows': the bow's row in each
    column, 'shown': whether its ink was seen there, 'seen', 'hidden' (how many columns of each), 'end': the last
    column with ink}, or None when there is no ink to follow."""
    height = thin.shape[0]
    most = int(round(TIE_THIN * space)) + 1
    rows, kinds, gap, blind = [], [], 0, 0
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
                y = (top + bottom) / 2
                kind = 'seen'
                gap = blind = 0
        if kind is None:
            row = int(round(y))
            blind += 1
            if lines[max(0, row - 1):row + 2, column].any():
                kind = 'hidden'
            else:
                kind = 'gap'
                gap += 1
                if gap > TIE_GAP * space:
                    break
        rows.append(y)
        kinds.append(kind)
    # The way ends where its ink was seen last.
    while kinds and kinds[-1] != 'seen':
        kinds.pop()
        rows.pop()
    if kinds.count('seen') < 2:
        return None
    return {'rows': np.array(rows), 'shown': np.array([kind == 'seen' for kind in kinds]), 'seen': kinds.count('seen'),
            'hidden': kinds.count('hidden'), 'end': x + len(kinds) - 1}


def _is_bow(way: dict, space: float) -> bool:
    """Is the way that was followed one smooth bow? The curve of a bow (a parabola) is laid through the rows where
    ink was seen: it is high enough, its highest place is in the middle part, and the ink stays close to it. A
    straight line with a hook at its end, and a line with a mark on it, are no bow."""
    count = len(way['rows'])
    if way['seen'] < 8:
        return False
    along = np.linspace(-1.0, 1.0, count)[way['shown']]
    rows = way['rows'][way['shown']]
    bend, lean, level = np.polyfit(along, rows, 2)
    rest = float(np.sqrt(np.mean((rows - (bend * along ** 2 + lean * along + level)) ** 2)))
    high = abs(bend)
    return TIE_BOW[0] * space <= high <= TIE_BOW[1] * space and abs(lean) <= TIE_EVEN * high + 0.2 * space \
        and rest <= TIE_SMOOTH * high + 0.04 * space


def _bow(thin: np.ndarray, lines: np.ndarray, one: dict, two: dict, space: float) -> bool:
    """Is there a bow from the head `one` to the head `two`?"""
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
        for row in starts:
            # A bow that was followed from an earlier column is not followed again.
            if any(abs(row - other) <= 3 for other in tried):
                continue
            way = _follow(thin, lines, column, float(row), last, space)
            if way is None:
                continue
            tried.add(int(round(way['rows'][min(len(way['rows']) - 1, 2)])))
            count = len(way['rows'])
            if way['end'] < last - side or abs(way['rows'][-1] - two['cy']) > high:
                continue
            if way['seen'] < TIE_SEEN[0] * count or way['seen'] + way['hidden'] < TIE_SEEN[1] * count:
                continue
            if not _is_bow(way, space):
                continue
            return True
    return False


def read_ties(layers: dict, heads: list[dict]) -> list[tuple[dict, dict]]:
    """The ties of a page: (first head, second head). Each first head gets 'tie_start' and each second head
    'tie_stop'."""
    if not TIE_FAR:
        return []
    space = layers['space']
    bare, lines = layers['bare'], layers['lines']
    most = int(round(TIE_THIN * space)) + 1
    thin = bare & (1 - cv2.morphologyEx(bare, cv2.MORPH_OPEN, np.ones((most + 1, 1), np.uint8)))
    found = []
    for staff in sorted({head['staff'] for head in heads}):
        own = sorted((head for head in heads if head['staff'] == staff), key=lambda head: head['cx'])
        for number, one in enumerate(own):
            place = round(one['place'])
            ways = {stem['direction'] for stem in one['stems']}
            two = None
            for other in own[number + 1:]:
                if other['x0'] - one['x1'] > TIE_FAR * space:
                    break
                if other['x0'] - one['x1'] < 0.5 * space:
                    continue
                if round(other['place']) == place:
                    two = other
                    break
                # Another note of this voice between the two heads: a bow over it is a slur.
                theirs = {stem['direction'] for stem in other['stems']}
                if (ways & theirs) or (not ways and not theirs) or ((not ways or not theirs) and abs(other['place'] - place) < 2):
                    break
            if two is None:
                continue
            tied = _bow(thin, lines, one, two, space)
            if tied:
                one['tie_start'] = True
                two['tie_stop'] = True
                found.append((one, two))
    return found

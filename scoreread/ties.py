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
TIE_PARTNER = (0.5, 1.8)  # a whole note has the voice that the note in its column has not: a note with a stem at most
#                         this many staff spaces from it along the staff, or beside it (at most a second away) at most
#                         this many (None: a whole note has no voice)
TIE_UNDER = True        # a bow that runs into a staff line and comes out at its other side: while no ink shows, the staff
#                         line within the reach of the search hides it, not only the line at the bow's last row
TIE_FROM_LINE = True    # a bow may begin in a staff line beside its head: it is followed from the line (False: off)
TIE_ROUND = True        # a head between the two heads is of another voice by its place on the staff, not by where its ink lies
TIE_LINE = (0.4, 0.07, 0.2, 2.0, 0.7, 1.6)   # a flat tie that lies in a staff line (None: off): the line is fatter in a
#                         run of columns that is this share of the way between the two heads; fatter by this many
#                         staff spaces; at most this share of the columns is crossed by a stem or a bar line; the
#                         run is this many staff spaces long or more; this share of its columns is fat; the line lies
#                         at most this many staff spaces from the middle of the heads
TIE_BREAK = (3.0, 0.45, 1.8, 1.0, 0.4, 0.6, 1.0, 0.9, 0.5)   # a tie over the end of a line (None: off): a bow leaves the last
#                         note of its voice, is this many staff spaces long or more, shows its ink in this share of its
#                         columns, ends at most this far before the end of the staff and moves at most this far up or
#                         down; or a short one (this long, this share of ink, ending this near the end) with a bow
#                         that comes to the first note of the next line (this long, this share of ink). The first note
#                         of that staff in the next system stands at the same place.


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
            if lines[low:high, column].any() if TIE_UNDER else lines[max(0, row - 1):row + 2, column].any():
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
            way = _follow(thin, lines, column, float(row), last, space)
            if way is None:
                continue
            if row not in hidden:       # a way from a staff line may be another bow's: that bow is still followed from its own start
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


def _half(thin: np.ndarray, lines: np.ndarray, words: list[dict], head: dict, last: int, space: float) -> dict | None:
    """The longest thin way that begins beside a head and goes right, toward the column `last`: {'long' (staff spaces),
    'seen' (the share of its columns with ink), 'togo' (staff spaces from its end to `last`), 'drift' (how far it
    moves up or down)}. None without one, when the ink goes on at the left of the head too (a slur that passes), or
    when it lies in the rows of the words (the line after a syllable)."""
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
                    'drift': abs(float(way['rows'][-1] - way['rows'][0])) / space}
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
            if go is None:
                continue
            tied = go['long'] >= TIE_BREAK[0] and go['seen'] >= TIE_BREAK[1] and go['togo'] <= TIE_BREAK[2] and go['drift'] <= TIE_BREAK[3]
            if not tied and go['long'] >= TIE_BREAK[4] and go['seen'] >= TIE_BREAK[5] and go['togo'] <= TIE_BREAK[6]:
                mirror = dict(two, x0=width - 1 - two['x1'], x1=width - 1 - two['x0'])
                come = _half(flipped, flipped_lines, flipped_words, mirror, width - 1 - int(staves[target]['x0']), space)
                tied = come is not None and come['long'] >= TIE_BREAK[7] and come['seen'] >= TIE_BREAK[8]
            if tied:
                found.append((one, two))
    return found


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
                # Another note of this voice between the two heads: a bow over it is a slur.
                theirs = voices[id(other)]
                if (ways & theirs) or (not ways and not theirs) or ((not ways or not theirs) and abs((round(other['place']) if TIE_ROUND else other['place']) - place) < 2):
                    break
            if two is None:
                continue
            tied = _bow(thin, lines, one, two, space) or bool(TIE_LINE and _in_line(layers, one, two, space))
            if tied:
                one['tie_start'] = True
                two['tie_stop'] = True
                found.append((one, two))
    if TIE_BREAK:
        every = {}
        for head in heads:
            every[id(head)] = {stem['direction'] for stem in head['stems']}
        for one, two in _over_break(layers, heads, thin, every):
            one['tie_start'] = True
            two['tie_stop'] = True
            found.append((one, two))
    return found

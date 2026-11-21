"""Reads the sharps, flats and naturals that stand before notes. No model is used.

A sign is read from its upright strokes, as the signs of a key signature are (scorereader.starts). A flat has one
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
FLAT_FLAG = 0.2          # the flag of an eighth is no flat: a flat whose stroke begins inside the reach of a stem's flag
#                          (the flag's reach and this many staff spaces more, right of the stem) and stands between
#                          that stem's end and its head is the flag's own stroke and hook. A stem in a beam has
#                          no flag, and a flat can stand close behind it, under the beam (None: off)
FLAT_LEG = (0.35, 0.1, 0.4, 0.6)   # a flat whose bowl has a second stroke as its right wall is a natural: the stroke stands
#                    from this far before the sign's right edge to this far past it, begins this far under the sign's
#                    top or lower, and ends this far under its bottom (staff spaces; None: off)
SIGN_START = 0.3     # a stroke in the first columns of the notes (this many staff spaces) whose ink goes on to the left
#                    of them, in this many staff spaces of its rows, is the cut end of the clef or of the key: no sign
#                    of a note (0: off)
PAIR_WIDE = 0.6          # each of the two strokes of a sharp is at most this wide, in staff spaces (0.45: as it was, and
#                          as it is for a flat and a natural; a heavy print draws the strokes of a sharp half a staff
#                          space wide)
FLAT_BOLD = 0.5          # the wall of a flat's bowl may be as heavy as a stroke of a sharp (PAIR_WIDE) where the flat's
#                          long stroke is a hairline against it, at most this share of the wall's width: an engraved
#                          flat swells in its bowl, and the two sides of a hollow head's rim, which the limit of 0.45
#                          is for, are as heavy as each other. A rule for one case: of the 139 pairs of strokes on
#                          LitChoir's scan pages that stand as a flat does and are refused for a heavy stroke, 137
#                          have a heavy long stroke (a stem with ink beside it, the flat of a heavy copy), one is the
#                          wire of a paperclip across a stem (0.83 of the other stroke's width) and one is a flat
#                          whose long stroke the print left faint (0.4 of the wall's width). None: off
PAIR_TOUCH = True        # two strokes with no column between them are joined: the heavy bars of a sharp fill the room
#                          between its strokes, and the room has no ink of its own to count (False: as it was)
PAIR_FREE = True         # a sharp with a stroke wider than 0.45 staff spaces stands free: two heavy strokes that lie on a
#                          head are a part of that head (its rim, or the stroke at the side of a breve). False: off
SHARP_HEAD = (1.7, 0.3, 1.4, 0.95)   # a heavy sharp whose middle closed is no head: a mark with a stem that lies on the two
#                          strokes of a sharp (each this many staff spaces high or more), reaches less than this share of
#                          a head's width past them, and is this many staff spaces high or more, or narrower than this
#                          share of the page's heads (None: off)
SHARP_OWN = True         # such a mark is no head either, whatever its size, when its middle lies between the two strokes and
#                          each of its stems is one of them: a head stands beside its sign (False: off)
SHARP_ROOM = True        # the paper between a heavy sharp and the head after it is no hollow head: a staff line and the ledger
#                          line that joins the two close it in. A hollow mark that lies on the sharp and whose closed paper
#                          begins at the sharp's strokes and goes on to the mark's right edge: the inside of a head ends
#                          at its rim. (A census of every hollow mark that lies on a sharp of two strokes on LitChoir's
#                          pages, 246 marks: the paper of every other one ends 3 pixels or more before the mark's edge.
#                          A rule for one case.) False: off
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
JOINED_ENDS = True              # ... and its ends are the first and the last row of its own ink without the staff lines: the
                                # stroke of a sign is followed into a staff line past its end, over a gap of paper. Such
                                # a sign lies before its head, not in its box (SHARP_JOINED[4], with a stem too)
                                # (False: the rows of the stroke)
JOINED_HEAD = True              # the middle of a joined sharp (SHARP_JOINED) that was taken for a head is no head: a mark whose
                                # middle and stems lie in the columns of the one wide stroke (False: off)
NATURAL_OWN = True              # the paper that the strokes and the bars of a natural close in is no hollow head: a mark whose
                                # middle lies between the two strokes and each of whose stems is one of them (False: off)
NATURAL_LONE = True             # the right stroke of a natural is no stem of a hollow head after it either where it is that
                                # head's only stem, when another head of its column has a stem (a whole note under a
                                # half note) (False: only a second stem, as NATURAL_STEM says)
SIGN_WORDS = True               # the strokes of a sign are read without the rows of the words (False: with them)
GLUED_CHORD = True              # a sign glued to the heads of a chord: it lies on all of them and changes the one at
                                # its place (False: a sign that lies on a head at another place is none)
GLUED_BEFORE = 1.0              # a mark that begins at least this many head widths before a sign and ends where the sign
                                # ends is the head before the sign, with a bar of the sign glued to it: the sign does not
                                # lie on it (None: such a sign lies on a head, and is none)
WHOLE_SIGN = True               # a heavy sharp that symbols.SIGN_WHOLE cut off its head is that head's sharp, whatever
#                                 the strokes say: its bars hide the top of a stroke, and the two strokes make no pair
THIN_SIGN = False               # a head that was read from its stem (symbols.thin_heads) whose stem is a stroke of a
                                # sign of two strokes is no head: the ink at the stroke's end is a slur, or a bar of the
                                # sign (False: the head stays, and the stroke is its stem). Off: it gained 2 notes on
                                # the clean copies and took 4 notes that are not there away, and lost 6 notes on one
                                # piece of the fresh set; the thin heads of LitChoir show no measure that parts them
STEM_APART = 0.25               # a stroke beside the stem of a head is no part of that stem where a column between the
                                # stem's middle column and the stroke holds ink (without the staff lines) in under this
                                # share of the rows that they share: the stroke of a sign close behind the stem of the
                                # note before it (None: the place alone, as it was)


NATURAL_ROWS = 1.9       # the two strokes of a natural stand side by side for at most this many staff spaces (1.5: as it
#                          was; the naturals of a heavy print are higher)
NATURAL_WIDE = 0.5        # each stroke of a natural is at most this wide, in staff spaces (0.45: as it was, and as a flat's
#                          stem; a small heavy print has naturals with strokes of 0.46 and 0.47)
NATURAL_LOW = (0.2, 0.3, 0.1)   # two nearly level strokes are a natural and no sharp: the right one begins this many staff
#                          spaces lower than the left one, begins and ends this much lower together, and at most this
#                          much ink sticks out at the left of the left one (None: off)
FADED_SHARP = (0.75, 1.3, 0.4, 1.6, 0.2, 0.6, 1.8, 3.0)   # a sharp whose two strokes faded: its two bars are left as two marks,
#   one over the other, each from this to this wide and from this to this high (staff spaces) with at least this area;
#   the paper between them is at most this high, and both together are from this to this high (None: off)
FADED_THICK = 0.47       # and the middle one of its columns holds at most this much ink, in staff spaces: a bar is a thin
#                          slanting stroke (0.42 at most where it was counted), a note head is thick (0.52 or more). At
#                          most one of the two marks was read as a note (0: the first form, which took two heads of a
#                          chord for the two bars and lost 167 notes for 1)
FADED_STEM = 0.9         # and no column of its box holds a piece of a stem this long, in staff spaces: the strokes of this
#                          sharp are gone but for stubs (0.58 at most), and two thin marks on a stem are the worn heads of
#                          a chord (1.18; one case each side of the limit and five more under it; 0: not looked at)
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


PAIR_LINE = True          # the end of a stroke is not the staff line that it was followed into: two strokes that make no sign
#   are measured again without an end piece that lies in the rows of a staff line, with paper between it and the rest of
#   the stroke, and are a sharp where they then stand as the strokes of a sharp do. Such a sharp stands before its head,
#   not in its box, as a joined sign whose ends were cut does (SHARP_JOINED[4]): on a thick copy the two sides of a
#   hollow head's rim passed as its strokes (False: off)


def _own_ends(layers: dict, staff: dict, stroke: dict) -> dict:
    """The stroke without an end piece that is a staff line (PAIR_LINE): the stroke itself where it has none."""
    first, last = int(stroke['top']), int(stroke['bottom'])
    rows = layers['ink'][first:last + 1, int(stroke['x0']):int(stroke['x1']) + 1].any(axis=1)
    empty = np.nonzero(~rows)[0]
    if not len(empty):
        return stroke
    reach = staff['thick'] / 2 + 1.5
    top, bottom = first, last
    # The piece over the first row of paper, and the piece under the last one: each wholly in the rows of a line.
    if any(abs(first - line) <= reach and abs(first + empty[0] - 1 - line) <= reach for line in staff['rows']):
        after = np.nonzero(rows[empty[0]:])[0]
        if len(after):
            top = first + int(empty[0] + after[0])
    if any(abs(first + empty[-1] + 1 - line) <= reach and abs(last - line) <= reach for line in staff['rows']):
        before = np.nonzero(rows[:empty[-1]])[0]
        if len(before):
            bottom = first + int(before[-1])
    if (top == first and bottom == last) or bottom - top < 3:
        return stroke
    return dict(stroke, top=top, bottom=bottom, high=(bottom - top + 1) / staff['space'])


def pair_signs(layers: dict, staff: dict, strokes: list[dict]) -> list[dict]:
    """The signs that two upright strokes show: {'kind', 'x0', 'x1', 'place', 'top', 'bottom'}."""
    space, rows = staff['space'], staff['rows']
    slim = [stroke for stroke in strokes if 0.9 <= stroke['high'] <= SIGN_STROKE[1] and stroke['wide'] <= PAIR_WIDE]
    found, used = [], set()

    def fit(left: dict, right: dict) -> dict | None:
        top, bottom = max(left['top'], right['top']), min(left['bottom'], right['bottom'])
        if bottom - top < 0.45 * space:
            return None
        # Ink joins the two strokes, in the rows that both have.
        gap = max(1.0, right['x0'] - left['x1'] - 1)
        if not (PAIR_TOUCH and right['x0'] - left['x1'] <= 1) \
                and _ink(layers, left['x1'] + 1, right['x0'] - 1, top, bottom) < 0.25 * gap * min(0.5 * space, bottom - top):
            return None
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
            return None
        if kind != 'sharp' and max(left['wide'], right['wide']) > (NATURAL_WIDE if kind == 'natural' else 0.45) \
                and not (FLAT_BOLD and kind == 'flat' and left['wide'] <= min(0.45, FLAT_BOLD * right['wide'])):
            return None      # only a sharp has two heavy strokes: the rim of a large hollow head is no flat
        return {'kind': kind, 'x0': float(left['x0']), 'x1': float(right['x1']), 'pair': True,
                'touch': bool(PAIR_TOUCH) and right['x0'] - left['x1'] <= 1,
                'wide': float(max(left['wide'], right['wide'])),
                'place': 4 - 2 * (middle - rows[0]) / space, 'top': min(left['top'], right['top']),
                'bottom': max(left['bottom'], right['bottom'])}

    for number, left in enumerate(slim):
        if id(left) in used:
            continue
        for right in slim[number + 1:]:
            if id(right) in used or not PAIR[0] * space <= right['x'] - left['x'] <= PAIR[1] * space:
                continue
            sign = fit(left, right)
            if sign is None and PAIR_LINE:
                # The end of a stroke is not the staff line that it was followed into.
                cut = [_own_ends(layers, staff, stroke) for stroke in (left, right)]
                if cut[0] is not left or cut[1] is not right:
                    sign = fit(*cut)
                    sign = dict(sign, cut=True) if sign is not None and sign['kind'] == 'sharp' else None
            if sign is None:
                continue
            found.append(sign)
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

    def apart(stroke: dict, stem: dict, top: float, bottom: float) -> bool:
        # A column of paper between the stem's middle column and the stroke, in the rows that they share.
        column = int(stem.get('mid', stem['x']))
        if column < stroke['x0']:
            columns = range(column + 1, int(stroke['x0']))
        else:
            columns = range(int(stroke['x1']) + 1, column)
        rows = layers['bare'][int(max(top, stroke['top'])):int(min(bottom, stroke['bottom'])) + 1]
        return len(columns) > 0 and rows.shape[0] > 0 \
            and any(float(rows[:, x].mean()) < STEM_APART for x in columns if 0 <= x < rows.shape[1])

    def stem_of_head(stroke: dict, beside: float = 0.3) -> bool:
        for head in full:
            for stem in head['stems']:
                top, bottom = min(head['cy'], stem['end']), max(head['cy'], stem['end'])
                if stroke['x0'] - beside * space <= stem['x'] <= stroke['x1'] + beside * space \
                        and min(bottom, stroke['bottom']) - max(top, stroke['top']) >= 0.5 * (stroke['bottom'] - stroke['top']):
                    if STEM_APART is not None and beside > 0 and apart(stroke, stem, top, bottom):
                        continue
                    return True
        return False

    def flag_of_stem(sign: dict) -> bool:
        for head in full:
            for stem in head['stems']:
                marks = stem.get('marks') or []
                reach = max((mark['far'] for mark in marks if mark.get('right')), default=None)
                if reach is None or any(mark.get('beam') for mark in marks) \
                        or not (head.get('tails') or {}).get(stem['direction']):
                    continue      # no flag, or a stem in a beam: a flat can stand close behind it, under the beam
                top, bottom = min(head['cy'], stem['end']), max(head['cy'], stem['end'])
                if stem['x'] < sign['x0'] <= stem['x'] + (reach + FLAT_FLAG) * space \
                        and top - 0.1 * space <= sign['top'] and sign['bottom'] <= bottom + 0.1 * space:
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
                if SHARP_ROOM and head.get('hollow') and _room(layers, head, sign):
                    ghosts.append(head)
                    continue
                if head.get('thin') or not head['stems'] or head['x1'] - sign['x1'] >= SHARP_HEAD[1] * wide:
                    continue
                if head['y1'] - head['y0'] + 1 >= SHARP_HEAD[2] * space or head['x1'] - head['x0'] + 1 < SHARP_HEAD[3] * wide:
                    ghosts.append(head)
                elif SHARP_OWN and sign['x0'] <= head['cx'] <= sign['x1'] and all(
                        any(stroke['x0'] - 1 <= stem['x'] <= stroke['x1'] + 1 for stroke in parts) for stem in head['stems']):
                    ghosts.append(head)     # its middle lies between the two strokes, and its stem is one of them
        full = [head for head in full if not any(head is ghost for ghost in ghosts)]
    if JOINED_HEAD and SHARP_JOINED:
        # A heavy sharp whose two strokes are one mark, with its middle read as a head and one of its strokes as that
        # head's stem: the mark is a sharp by its ends and its closed paper, and the head lies inside its columns.
        for stroke in strokes:
            if not 0.45 < stroke['wide'] <= 1.2 or stroke['high'] > 3.4:
                continue
            inside = [head for head in full if head['stems'] and stroke['x0'] <= head['cx'] <= stroke['x1']
                      and all(stroke['x0'] - 1 <= stem['x'] <= stroke['x1'] + 1 for stem in head['stems'])]
            if inside and _joined_sharp(layers, {'x0': stroke['x0'], 'x1': stroke['x1'], 'top': stroke['top'],
                                                 'bottom': stroke['bottom']}, space) == 'sharp':
                ghosts.extend(inside)
        full = [head for head in full if not any(head is ghost for ghost in ghosts)]
    if NATURAL_OWN:
        # The middle of a natural, closed in by its strokes and bars, read as a hollow head with the right stroke as its
        # stem. A head stands beside its sign, not between its strokes.
        for sign in pair_signs(layers, staff, strokes):
            if sign['kind'] != 'natural':
                continue
            parts = [stroke for stroke in strokes if sign['x0'] <= stroke['x'] <= sign['x1']]
            for head in lying(sign, full):
                if head.get('hollow') and head['stems'] and sign['x0'] <= head['cx'] <= sign['x1'] and all(
                        any(stroke['x0'] - 1 <= stem['x'] <= stroke['x1'] + 1 for stroke in parts) for stem in head['stems']):
                    ghosts.append(head)
        full = [head for head in full if not any(head is ghost for ghost in ghosts)]
    strays = []
    if THIN_SIGN:
        # A thin head is read from an upright stroke and a small piece of ink at its end. The stroke of a sign has
        # such pieces at its ends too: the end of a slur that passes under it, the bar of a natural.
        for sign in pair_signs(layers, staff, strokes):
            parts = [stroke for stroke in strokes if sign['x0'] <= stroke['x'] <= sign['x1']
                     and stroke['top'] <= sign['bottom'] and sign['top'] <= stroke['bottom']]
            if len(parts) < 2:
                continue
            for head in full:
                if head.get('thin') and len(head['stems']) == 1 and any(
                        stroke['x0'] - 1 <= head['stems'][0]['x'] <= stroke['x1'] + 1
                        and min(stroke['bottom'], max(head['cy'], head['stems'][0]['end']))
                        - max(stroke['top'], min(head['cy'], head['stems'][0]['end'])) >= 0.5 * (stroke['bottom'] - stroke['top'])
                        for stroke in parts):
                    strays.append((sign, head))
        full = [head for head in full if not any(head is stray for _, stray in strays)]
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
                        lone = NATURAL_LONE and head.get('hollow') and head['cx'] > right['x1'] and any(
                            other is not head and other['stems'] and abs(other['cx'] - head['cx']) <= 0.5 * wide for other in full)
                        if (len(head['stems']) >= 2 or lone) and right['x0'] <= stem['x'] <= right['x1'] \
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
            if FLAT_FLAG is not None and flag_of_stem(sign):
                continue
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
        if GLUED_BEFORE is not None:
            on = [head for head in on if not (abs(head['x1'] - sign['x1']) <= 1 and sign['x0'] - head['x0'] >= GLUED_BEFORE * wide)]
        if PAIR_FREE and on and (sign.get('wide', 0.0) > 0.45 or sign.get('touch')):
            continue      # a heavy stroke and the rim of a hollow head, or the stroke at the side of a breve; or the
            #               heavy stem of a head on a ledger line, cut in two strokes that touch
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
        drop = lying(sign, small) + bowls + lying(sign, ghosts) + [head for other, head in strays
                                                                    if other['x0'] <= sign['x1'] and sign['x0'] <= other['x1']]
        best = None
        for head in own:
            if any(head is other for other in drop):
                continue
            ahead = (head['x0'] - sign['x1']) / space
            if any(head is other for other in glued) or (BEFORE[0] <= ahead <= BEFORE[1] and abs(head['place'] - place) <= HIGH):
                rank = (not any(head is other for other in glued), abs(head['place'] - place) > 0.8, ahead)
                if best is None or rank < best[0]:
                    best = (rank, head)
        if best and (sign.get('joined') or (sign.get('pair') and sign.get('cut'))) and SHARP_JOINED and SHARP_JOINED[4]:
            head = best[1]
            if (not head['stems'] or sign.get('cut')) \
                    and min(sign['x1'], head['x1']) - max(sign['x0'], head['x0']) + 1 > SHARP_JOINED[4] * (sign['x1'] - sign['x0'] + 1):
                continue      # a part of the head, no sign before it (a sign whose ends were cut: also a head with a
                #               stem, two hollow heads one over the other that a faint copy joined)
        if best:
            for right, head, stem in legs:
                if sign['kind'] == 'natural' and right['x1'] == sign['x1'] and head is best[1]:
                    head['stems'] = [other for other in head['stems'] if other is not stem]     # no stem: the sign's stroke
                    head.get('tails', {}).pop(stem['direction'], None)
            out.append(dict(sign, head=best[1], drop=drop))
    if WHOLE_SIGN:
        for head in own:
            if not head.get('sharp'):
                continue
            x0, y0, x1, y1 = head['sharp']
            same = [sign for sign in out if sign['head'] is head
                    or (sign['x0'] <= x1 and x0 <= sign['x1'] and sign['top'] <= y1 and y0 <= sign['bottom'])]
            drop = [other for sign in same for other in sign['drop'] if other is not head]
            drop += [other for other in own if other is not head and x0 <= other['cx'] <= x1 and y0 <= other['cy'] <= y1
                     and not any(other is known for known in drop)]
            out = [sign for sign in out if not any(sign is other for other in same)]
            out.append({'kind': 'sharp', 'x0': float(x0), 'x1': float(x1), 'top': float(y0), 'bottom': float(y1),
                        'place': head['place'], 'whole': True, 'head': head, 'drop': drop})
    if TANGLE:
        signed = {id(sign['head']) for sign in out} | {id(head) for sign in out for head in sign['drop']}
        for head in full:
            if id(head) not in signed and head['x0'] - TANGLE_NEAR[0] * space > first:
                sign = tangle_sign(layers, staff, head, own)
                if sign:
                    out.append(dict(sign, head=head, drop=lying(sign, small)))
    if FADED_SHARP:
        signed = {id(sign['head']) for sign in out} | {id(head) for sign in out for head in sign['drop']}
        taken = [(sign['x0'], sign['x1'], sign['top'], sign['bottom']) for sign in out]
        for head in full:
            if id(head) not in signed and head['x0'] - TANGLE_NEAR[0] * space > first:
                sign = faded_sharp(layers, staff, head, own)
                if sign and not any(sign['x0'] <= x1 and x0 <= sign['x1'] and sign['top'] <= bottom and top <= sign['bottom']
                                    for x0, x1, top, bottom in taken):
                    parts = sign.pop('parts')
                    out.append(dict(sign, head=head, drop=lying(sign, small) + [part for part in parts
                                                                             if not any(part is other for other in lying(sign, small))]))
                    taken.append((sign['x0'], sign['x1'], sign['top'], sign['bottom']))
    return out


def _room(layers: dict, head: dict, sign: dict) -> bool:
    """Whether the largest piece of closed paper of a mark begins at the strokes of the sign that the mark lies on and
    goes on to the mark's right edge (SHARP_ROOM)."""
    y0, x0 = max(0, int(head['y0']) - 1), max(0, int(head['x0']) - 1)
    holes = np.ascontiguousarray(layers['holes'][y0:int(head['y1']) + 2, x0:int(head['x1']) + 2]).astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(holes, connectivity=4)
    if count < 2:
        return False
    x, _, width, _, _ = stats[1 + int(np.argmax(stats[1:, 4]))]
    return x0 + int(x) <= sign['x1'] + 1 and int(x) + int(width) >= holes.shape[1]


def _inside(head: dict, x: int, y: int, wide: int, high: int) -> float:
    """The share of a head's box that lies in the box x, y, wide, high."""
    over = min(head['x1'], x + wide - 1) - max(head['x0'], x) + 1
    tall = min(head['y1'], y + high - 1) - max(head['y0'], y) + 1
    if over <= 0 or tall <= 0:
        return 0.0
    return over * tall / float((head['x1'] - head['x0'] + 1) * (head['y1'] - head['y0'] + 1))


def faded_sharp(layers: dict, staff: dict, head: dict, heads: list[dict]) -> dict | None:
    """The sharp of a faint print before a head: the two thin strokes faded and the two heavy bars are left, as two
    marks of one width, one over the other, with the stubs of the strokes on them. Each mark lies whole in the room
    before the head, the two cover the same columns, and the head stands at the height of the paper between them."""
    space = staff['space']
    ink = layers['bare'] & (1 - layers['stems'])
    height, width = ink.shape
    x0, x1 = int(head['x0'] - (BEFORE[1] + 1.4) * space), int(head['x0'] + 0.05 * space)
    y0, y1 = int(head['cy'] - 2.2 * space), int(head['cy'] + 2.2 * space)
    if x0 < 1 or y0 < 1 or y1 >= height - 1 or x1 >= width - 1:
        return None
    count, labels, stats, _ = cv2.connectedComponentsWithStats(np.ascontiguousarray(ink[y0:y1 + 1, x0:x1 + 1]), connectivity=8)
    bars = []
    for index in range(1, count):
        x, y, wide, high, area = stats[index]
        if x > 0 and y > 0 and x + wide < labels.shape[1] and y + high < labels.shape[0] \
                and FADED_SHARP[0] * space <= wide <= FADED_SHARP[1] * space \
                and FADED_SHARP[2] * space <= high <= FADED_SHARP[3] * space and area >= FADED_SHARP[4] * space * space:
            # A bar is a thin slanting stroke: most of its columns hold little ink. A head is as thick as it is high.
            thick = float(np.median((labels[y:y + high, x:x + wide] == index).sum(axis=0))) / space
            if FADED_THICK and thick > FADED_THICK:
                continue
            bars.append((int(x), int(y), int(wide), int(high), thick, float(area) / space / space))
    bars.sort(key=lambda bar: bar[1])
    for number, upper in enumerate(bars):
        for lower in bars[number + 1:]:
            shared = min(upper[0] + upper[2], lower[0] + lower[2]) - max(upper[0], lower[0])
            between = lower[1] - (upper[1] + upper[3])
            whole = lower[1] + lower[3] - upper[1]
            if shared < 0.8 * min(upper[2], lower[2]) or not -0.15 * space <= between <= FADED_SHARP[5] * space \
                    or not FADED_SHARP[6] * space <= whole <= FADED_SHARP[7] * space:
                continue
            left, right = x0 + min(upper[0], lower[0]), x0 + max(upper[0] + upper[2], lower[0] + lower[2]) - 1
            top, bottom = y0 + upper[1], y0 + lower[1] + lower[3] - 1
            middle = (y0 + upper[1] + upper[3] + y0 + lower[1]) / 2
            ahead = (head['x0'] - right) / space
            if not BEFORE[0] <= ahead <= BEFORE[1] or abs(head['cy'] - middle) > 0.5 * HIGH * space:
                continue
            # A head that lies on the two marks: one of the bars itself, read as a small note, or another note, and
            # then this is not the sign of this head.
            parts, free = [], True
            for other in heads:
                if other is head or other['x1'] < left or other['x0'] > right or other['y1'] < top or other['y0'] > bottom:
                    continue
                inside = max(_inside(other, x0 + bar[0], y0 + bar[1], bar[2], bar[3]) for bar in (upper, lower))
                if inside >= 0.7:
                    parts.append(other)
                else:
                    free = False
            if not free or (FADED_THICK and len(parts) > 1):
                continue
            if FADED_STEM:
                stems = layers['stems'][max(0, top - 2):bottom + 3, max(0, left - 2):right + 3] > 0
                longest = 0
                for column in np.nonzero(stems.any(axis=0))[0]:
                    edges = np.diff(np.concatenate(([0], stems[:, column].astype(np.int8), [0])))
                    longest = max(longest, int((np.nonzero(edges == -1)[0] - np.nonzero(edges == 1)[0]).max()))
                if longest >= FADED_STEM * space:
                    continue
            return {'kind': 'sharp', 'x0': float(left), 'x1': float(right), 'top': float(top), 'bottom': float(bottom),
                    'place': 4 - 2 * (middle - staff['rows'][0]) / space, 'faded': True, 'parts': parts,
                    'bars': [(bar[2] / space, bar[3] / space, bar[4], bar[5]) for bar in (upper, lower)]}
    return None


def _joined_sharp(layers: dict, sign: dict, space: float) -> str | None:
    """'sharp' when one wide stroke is a sharp whose two strokes a heavy print joined: both strokes stand out over and
    under the bars, and the strokes and the bars close in a piece of paper. 'natural' when its left stroke stands
    alone at the top and its right one alone at the bottom. None when it is neither."""
    x0, x1, top, bottom = int(sign['x0']), int(sign['x1']) + 1, int(sign['top']), int(sign['bottom']) + 1
    if JOINED_ENDS and JOINED_BARE:
        rows = np.nonzero(layers['bare'][top:bottom, x0:x1].any(axis=1))[0]
        if len(rows) and (rows[0] > 0 or top + int(rows[-1]) + 1 < bottom):
            top, bottom = top + int(rows[0]), top + int(rows[-1]) + 1
            sign['cut'] = True
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

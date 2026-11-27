"""Finds the time signatures of a staff, so that their numbers are not read as notes or as sharps. No model is used.

A time signature is two numbers, one over the other. The upper number fills the staff from the top line to the
middle line, and the lower number fills it from the middle line to the bottom line. No note does that: a head is one
staff space high, and the stem of a note leaves the staff, or it has a head on one half of the staff only.

The shape alone is not sure in the middle of a staff (a rest, or a note with a flag in a poor copy, can fill both
halves): there the music must agree. The staves of a system change the time at one place, and the new time stands
right after a bar line.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

TIME_EDGE = 0.2          # a number begins and ends at most this far from the top, middle or bottom line, in staff spaces
TIME_LOOSE = (0.3, 0.5)  # or at most as far as the first number (a print whose numbers stand a little short of the lines,
#                          or over them), where no numbers are found by TIME_EDGE in the same columns. The signs of a key
#                          fill the two halves of a staff within the wider limit too (two flats of a bass staff, a heavy
#                          sharp): at the start of a staff such numbers stand after the key signature, at most the second
#                          number of staff spaces before its end. After the start of the notes they are numbers as the
#                          others are: there the staves of a system must agree, or a bar line stands before them.
#                          Of the 23 such signs at the starts of LitChoir's staves, each looked at, the 7 that are signs
#                          of a key begin 1.2 staff spaces or more before the key's end, and the 16 time signatures 0.17
#                          or more after it. Where the key signature is not known yet (the first look at a start, which
#                          reaches 13 staff spaces past the clef), such numbers do not count: a note with a flag passed
#                          there (None: off)
TIME_WIDE = (0.6, 2.2)   # each number is this wide, in staff spaces
TIME_WIDER = 1.0         # and one of the two is at least this wide (a quarter rest fills the staff too, but it is slim)
TIME_HIGH = 1.4          # each number is at least this high
TIME_INK = 0.2           # the ink of a number fills at least this share of its box
TIME_OVER = 0.6          # the two numbers stand one over the other: this share of the narrower one
TIME_BAR = 0.97          # no column of the numbers is ink along this share of the staff's height: that is a bar line
TIME_WAIST = (0.3, 0.45) # the ink within this many staff spaces of the middle line is at least this wide, or there is none
TIME_PAIR = 1.5          # the staves of a system change the time at one place: at most this far apart, in staff spaces
TIME_AFTER = 3.0         # in a system of one staff, a bar line stands at most this far before the numbers
TIME_MATE = True         # the staves of a system change the time at one place, after a bar line. Where one staff shows
#                          the numbers by every measure, with a bar line at most TIME_AFTER before them, the ink of
#                          another staff of the system that stands in the same columns after its bar line, and fills
#                          the two halves of the staff as two numbers do, is the same signature: it missed a limit of
#                          the checks for a bar line, a head and a stem by a pixel (two numbers that touch and are a
#                          hair narrower than TIME_STACK asks). Alone such ink is no signature (False: off)
TIME_HEAD = (0.7, 0.05)  # and no ink is as thick as this in every direction, in staff spaces, over more than this
#                          share of a square staff space: that is the head of a note (a bold number has small such spots)
TIME_STACK = (1.25, 1.9, 1.1, 0.85, 0.08, 0.25, 0.85, 0.45)   # two numbers that touch, or bold numbers, fail the checks
#  for a bar line and for a head. They are numbers all the same when the two are this wide together (least, most),
#  each is this wide or more, the columns that are ink along this share of the staff's height or more (the stem of a
#  4 over the stem of a 4, or two numbers that meet) all lie between two shares of the width (from this for numbers
#  that fill the staff from top to bottom, from this for other numbers; to this), and this share or more of the
#  inked columns is ink along a part of the staff only. A bar line and a closing bar are full columns at the edges
#  with little beside them; the stem of a note stands at the edge of its head and is shorter than the staff. One
#  engraving sets the stem of its 4 at 0.83 of the width of two touching numbers. (None: off)
TIME_LINES = True        # numbers are also found in the ink without the staff lines that the ink alone shows, where no
#                          other sign stands. The layer of the lines keeps a line where closed paper touches it (the
#                          inside of a head), and a heavy print that sets its time signature close after the key closes
#                          paper between the last sign of the key, the first number and two staff lines: the lines then
#                          join the numbers to the key, and the numbers were read as whole notes. That ink is a second
#                          look only: numbers that touch each other along the middle line fall apart in it. On LitChoir's
#                          pages it finds 21 signatures on 12 pages, each looked at: 20 true ones, at the start of a staff
#                          and after a bar line, in print and by hand, and the flat of a key that the reader does not read
#                          on its page (it takes no note); none on the fresh set (False: off)
TIME_BLACK = True        # in the middle of a staff, numbers are also found in the ink without the lines kept to the
#                          page's black ink (layers.BLACK), where no other sign stands: a hairline of the scan, grey, that
#                          runs through the numbers from over the staff to far under it joins them into one piece that
#                          ends nowhere near a line, and the numbers were read as heads with the hairline as their stem
#                          (non-liturgical-jesus-prayer pg0647). The numbers so found pass mid_signs as any others: in a
#                          system of two staves or more, beside numbers of another staff. A census at the reader's own
#                          step on every page of LitChoir and of the fresh set, each looked at: 10 signatures that only
#                          this ink finds, all on LitChoir's pages; one is kept, the 4/4 of pg0647, whose mate over it had
#                          been found and refused for want of it. The 9 others are refused there: no other staff of
#                          their system shows numbers in their columns (two heads one over the other with their stem, the
#                          flag of an eighth, stems and slurs of thick copies, and a 4/4 at the start of a staff). The
#                          3/2 of pg0648 is not found: the 3 of the staff over it is worn into specks (False: off)
COMMON = True            # the sign of common time (C) at the start of a staff is found too (False: only numbers)
COMMON_HIGH = (1.5, 2.7) # the C is this high, in staff spaces
COMMON_WIDE = (0.35, 2.3)    # and this wide (a hand copy draws a thin bow, and the staff lines take its two ends)
COMMON_OFF = 0.6         # its middle stands at most this far from the middle line
COMMON_INK = 0.5         # its ink fills at most this share of its box
COMMON_WHOLE = 0.8       # the bow has ink in this share of its rows
COMMON_END = 0.2         # the two ends of the bow: this share of its height each
COMMON_BOW = (-0.05, 0.1)    # each end begins at least this far right of the middle of the bow, and one of them this far
COMMON_BLOT = 0.5        # the thickest spot of the bow is under this, in staff spaces: a thicker one is the head of a note
#                          with its stem down (on the wide test the signs have 0.27 to 0.46, such a note 0.54 and more)
COMMON_THICK = 0.65      # the stroke in the middle of the bow is at most this thick, and nothing stands right of it


def _free(layers: dict) -> np.ndarray:
    """The ink without the staff lines (and without the filling of the holes)."""
    if 'unfilled' not in layers:
        layers['unfilled'] = layers['ink'] & (1 - layers['lines'])
    return layers['unfilled']


def _number_ink(layers: dict) -> np.ndarray:
    """The ink without the staff lines that the ink alone shows (TIME_LINES)."""
    if 'number_ink' not in layers:
        from .layers import staff_lines
        layers['number_ink'] = layers['ink'] & (1 - staff_lines(layers['ink'], layers['staves']))
    return layers['number_ink']


def _black_ink(layers: dict) -> np.ndarray:
    """The ink without the lines of the layers, kept to the page's black ink (TIME_BLACK)."""
    if 'black_free' not in layers:
        layers['black_free'] = _free(layers) & layers['black']
    return layers['black_free']


def _stacked(columns: np.ndarray, wides: list[int], space: float, crosses: bool) -> bool:
    """Whether the ink of two halves is two numbers one over the other by TIME_STACK. `columns` holds the share of ink
    of each column between the top and the bottom line, `wides` the width of each half, and `crosses` says that a
    column is ink along the whole staff."""
    if not TIME_STACK:
        return False
    least, most, each, long, from_cross, from_other, to, part = TIME_STACK
    if not least * space <= len(columns) <= most * space or min(wides) < each * space:
        return False
    full = np.nonzero(columns >= long)[0]
    inked = columns > 0.05
    if not len(full) or ((columns >= 0.15) & (columns <= long)).sum() < part * inked.sum():
        return False
    return (from_cross if crosses else from_other) <= full.min() / len(columns) and full.max() / len(columns) <= to


def time_signs(layers: dict, staff: dict, first: float | None = None, last: float | None = None, weak: bool = False,
               black: bool = False) -> list[dict]:
    """The time signatures of a staff between the columns first and last (the whole staff when they are not given):
    each {'x0', 'x1'}. The numbers that pass only by the wider limit of TIME_LOOSE are marked ('loose': True). With
    `weak`, also the ink that fills the two halves of the staff as two numbers do and fails a check for a bar line,
    a head or a stem ('weak': True): see TIME_MATE. Numbers that are found only in the ink without the lines that the
    ink alone shows (TIME_LINES) come after all others, where no other sign stands, and with `black` after them the
    numbers that are found only in the page's black ink (TIME_BLACK)."""
    found = _signs_in(layers, staff, first, last, weak, False)
    if TIME_LINES:
        found += [sign for sign in _signs_in(layers, staff, first, last, False, True) if _apart(sign, found)]
        found.sort(key=lambda sign: sign['x0'])
    if black and TIME_BLACK and layers.get('black') is not None:
        found += [sign for sign in _signs_in(layers, staff, first, last, False, 'black') if _apart(sign, found)]
        found.sort(key=lambda sign: sign['x0'])
    return found


def _apart(sign: dict, others: list[dict]) -> bool:
    return not any(sign['x0'] <= other['x1'] and other['x0'] <= sign['x1'] for other in others)


def _signs_in(layers: dict, staff: dict, first: float | None, last: float | None, weak: bool, alone: bool | str) -> list[dict]:
    """The time signatures of time_signs() in one ink: the ink without the lines of the layers, or (`alone`) without
    the lines that the ink alone shows, or (`alone` is 'black') the first kept to the page's black ink."""
    found = _time_signs(layers, staff, first, last, weak, TIME_EDGE, alone)
    if TIME_LOOSE:
        wider = [dict(sign, loose=True) for sign in _time_signs(layers, staff, first, last, weak, TIME_LOOSE[0], alone)]
        # Numbers that pass every check come before ink that fails one, and the closer limit before the wider one.
        sure = [sign for sign in found if not sign.get('weak')]
        sure += [sign for sign in wider if not sign.get('weak') and _apart(sign, sure)]
        for sign in [sign for sign in found + wider if sign.get('weak')]:
            if _apart(sign, sure):
                sure.append(sign)
        found = sorted(sure, key=lambda sign: sign['x0'])
    return found


def _time_signs(layers: dict, staff: dict, first: float | None, last: float | None, weak: bool, limit: float,
                alone: bool | str = False) -> list[dict]:
    """The time signatures of time_signs() whose numbers begin and end at most `limit` staff spaces from their lines,
    in the ink without the lines of the layers or (`alone`) without the lines that the ink alone shows (or, where
    `alone` is 'black', the first kept to the page's black ink)."""
    free = _black_ink(layers) if alone == 'black' else _number_ink(layers) if alone else _free(layers)
    height, width = free.shape
    space, rows = staff['space'], staff['rows']
    top, middle, bottom = rows[0], rows[2], rows[4]
    edge = limit * space
    y0, y1 = max(0, int(top - 1.5 * space)), min(height, int(bottom + 1.5 * space) + 1)
    x0 = max(0, int(staff['x0'] if first is None else first))
    x1 = min(width, int(staff['x1'] if last is None else last) + 1)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return []
    # The staff lines were taken away: a mark is joined again over the rows of the lines.
    region = cv2.morphologyEx(np.ascontiguousarray(free[y0:y1, x0:x1]), cv2.MORPH_CLOSE,
                              np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)
    parts = []
    for label in range(1, count):
        x, y, wide, high, _ = stats[label]
        begin, end = y0 + y, y0 + y + high - 1
        if wide > TIME_WIDE[1] * space:
            continue
        upper = abs(begin - top) <= edge and (abs(end - middle) <= edge or abs(end - bottom) <= edge)
        lower = abs(end - bottom) <= edge and abs(begin - middle) <= edge
        if upper or lower:
            parts.append((int(x), int(x + wide - 1), label))
    parts.sort()
    groups = []
    for part in parts:
        if groups and part[0] <= groups[-1][1] + 0.4 * space:
            groups[-1][1] = max(groups[-1][1], part[1])
            groups[-1][2].append(part[2])
        else:
            groups.append([part[0], part[1], [part[2]]])
    found = []
    split = int(round(middle - y0))
    for begin, end, own in groups:
        if not TIME_WIDE[0] * space <= end - begin + 1 <= TIME_WIDE[1] * space:
            continue
        mask = np.isin(labels[:, begin:end + 1], own)
        boxes = []
        for half in (mask[:split], mask[split:]):
            ys, xs = np.nonzero(half)
            if not len(ys):
                break
            wide, high = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
            if wide < TIME_WIDE[0] * space or high < TIME_HIGH * space or len(ys) < TIME_INK * wide * high:
                break
            boxes.append((int(xs.min()), int(xs.max())))
        if len(boxes) < 2:
            continue
        shared = min(boxes[0][1], boxes[1][1]) - max(boxes[0][0], boxes[1][0]) + 1
        if shared < TIME_OVER * min(boxes[0][1] - boxes[0][0] + 1, boxes[1][1] - boxes[1][0] + 1):
            continue
        if max(box[1] - box[0] + 1 for box in boxes) < TIME_WIDER * space:
            continue
        # A bar line, a double bar or the line that opens a system crosses the whole staff.
        inside = mask[max(0, int(top - y0)):int(bottom - y0) + 1]
        columns = inside.mean(axis=0)
        crosses = bool((columns >= TIME_BAR).any())
        stacked = _stacked(columns, [box[1] - box[0] + 1 for box in boxes], space, crosses)
        refused = crosses and not stacked
        # A note with a flag fills both halves too (its head in one, its flag in the other): a head is a thick blot.
        size = max(3, int(round(TIME_HEAD[0] * space)))
        thick = cv2.erode(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
        if thick.sum() > TIME_HEAD[1] * space * space and not stacked:
            refused = True
        # The stem of a note crosses the middle line as one thin stroke. Two numbers meet there with more ink, or
        # they do not meet.
        waist = mask[max(0, split - int(TIME_WAIST[0] * space)):split + int(TIME_WAIST[0] * space) + 1].any(axis=0).sum()
        if 0 < waist < TIME_WAIST[1] * space and not (crosses and stacked):
            refused = True
        if refused and not weak:
            continue
        found.append(dict({'x0': float(x0 + begin), 'x1': float(x0 + end)}, **({'weak': True} if refused else {})))
    return found


def common_signs(layers: dict, staff: dict, first: float, last: float) -> list[dict]:
    """The signs of common time (a C) of a staff between the columns first and last: each {'x0', 'x1', 'common'}.

    The C is an open bow about two staff spaces high around the middle line: one thin stroke at its left that an
    end turns to the right, and nothing in its middle or at its right. A note head is one space high, the stroke
    of a flat and of a natural is straight, and a flat has its bowl beside the stroke. (The sign of cut time, a C
    with an upright stroke through it, is not looked for: on the copies of the wide test nearly every find was a
    note.)"""
    free = _free(layers)
    height, width = free.shape
    space, rows = staff['space'], staff['rows']
    middle = rows[2]
    y0, y1 = max(0, int(rows[0] - 1.5 * space)), min(height, int(rows[4] + 1.5 * space) + 1)
    x0, x1 = max(0, int(first)), min(width, int(last) + 1)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return []
    region = cv2.morphologyEx(np.ascontiguousarray(free[y0:y1, x0:x1]), cv2.MORPH_CLOSE,
                              np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)
    found = []
    for label in range(1, count):
        x, y, bw, bh, _ = stats[label]
        if not COMMON_HIGH[0] * space <= bh <= COMMON_HIGH[1] * space or not COMMON_WIDE[0] * space <= bw <= COMMON_WIDE[1] * space:
            continue
        if abs(y0 + y + bh / 2 - middle) > COMMON_OFF * space:
            continue
        box = labels[y:y + bh, x:x + bw] == label
        if box.mean() > COMMON_INK:
            continue
        # The bow: its left edge stands furthest left in the middle, and an end turns to the right (the staff lines
        # often take the other end of a thin bow).
        inked = box.any(axis=1)
        if inked.mean() < COMMON_WHOLE:
            continue
        left = np.where(inked, box.argmax(axis=1), bw).astype(float)
        end = max(1, int(round(COMMON_END * bh)))
        heart = left[end:bh - end][inked[end:bh - end]]
        if not len(heart) or not inked[:end].any() or not inked[bh - end:].any():
            continue
        inner = float(np.percentile(heart, 20))
        top, bottom = left[:end][inked[:end]].min() - inner, left[bh - end:][inked[bh - end:]].min() - inner
        if min(top, bottom) < COMMON_BOW[0] * space or max(top, bottom) < COMMON_BOW[1] * space:
            continue
        # The middle rows hold one thin stroke at the left, and nothing right of it.
        quarter = max(1, bh // 4)
        reach = int(inner + COMMON_THICK * space)
        if box[quarter:bh - quarter, reach:].any(axis=1).mean() > 0.15:
            continue
        # A note with its stem down is a stroke with a turn at its top too: its head is a thick blot.
        if 2 * cv2.distanceTransform(np.pad(box.astype(np.uint8), 2), cv2.DIST_L2, 5).max() >= COMMON_BLOT * space:
            continue
        found.append({'x0': float(x0 + x), 'x1': float(x0 + x + bw - 1), 'common': True})
    return sorted(found, key=lambda sign: sign['x0'])


COMMON_BOLD = (1.8, 2.6, 0.15, 1.0, 1.9, 0.5, 0.25, 0.75, -0.05)   # the bold C of a print, which is read as a note
#   or two: its ink without the staff lines is one piece or two side by side, each this high (two numbers, in staff
#   spaces) with its middle at most this far from the middle line; together they are this wide (two numbers), at
#   most this far apart, they fill this share of their box (two numbers), they close in one piece of paper at most
#   (the ends of a bold C can touch), and the left edge stands further left in the middle rows than in the upper and
#   the lower quarter, by this at least (the bow; negative: left). A head is one space high and a head with its stem
#   is higher, the numbers of a time signature stand over and under the middle line, and an eighth rest, a double
#   sharp and two whole notes one over the other have a waist at the left where the C has its bow (a census of the
#   clean pages, each of 61 pieces looked at: 39 signs from -0.25 to -0.07, and 20 of the 22 other pieces from 0.0
#   on). The upper limit of the height was 2.45, from the clean pages; the census of every page of LitChoir with 2.8
#   (22 more pieces, each looked at) held 18 true signs from 2.45 to 2.57, then a head with its stem at 2.70, two
#   true signs at 2.76 and 2.78 and a quarter rest by hand at 2.79. None: off
COMMON_ARM = 0.6         # and its two ends turn to the right: in the upper and in the lower fifth of its rows the ink reaches
#   this share of its width (the signs of the clean pages: 0.81 and more; a flat that a hand draws large has its
#   stroke at the left over its bowl: up to 0.52 at one end, 14 such marks on the copies by hand)
# The ends of a bold C that stand apart from its bow begin at most this far past the bow's right edge and lie within
# this much of its rows (staff spaces). A head counts as ink of the sign only this near the middle line (COMMON_ROWS,
# staff spaces): a held note that is printed under the staff in the sign's columns is a note.
COMMON_ENDS = (0.5, 0.25)
COMMON_ROWS = 2.25
COMMON_CUT = (3.2, 0.9, 0.3, 0.75, 0.15)   # the sign of cut time is such a C with an upright stroke through it, and the
#   stroke closes the C in two or three pieces of paper, which were read as whole notes one over the other. The sign is
#   at most the first number of staff spaces high, one column from the third to the fourth share of its width has ink
#   in the second share of its rows (the stroke), and the stroke stands out of the C at both ends: the first and the
#   last row of the sign hold ink only within the last number of staff spaces of the stroke. A sharp and a natural
#   have two strokes, and one stands out at the top and the other at the bottom; the stem of a head stands out at one
#   end. (A census of every piece of the size and the place of a C that closes in more than one piece of paper, 416
#   on LitChoir's pages: two printed signs of cut time, each looked at; a third on a thick copy is one blot.) None: off
COMMON_AT = (4.5, 1.6)   # and it stands where a time signature stands: it begins at most this far after the clef and
#   the key signature, or at most this far after a bar line, in staff spaces (the signs of the census: up to 4.0 and
#   1.3; the two other pieces with a bow, a rest and a flag, stand in the middle of a bar)


def _waist(box: np.ndarray) -> float:
    """How far the left edge of a piece of ink stands in at its middle rows, against its upper and its lower quarter
    (px): the bow of a C stands furthest left in its middle, and two heads one over the other have a waist there."""
    tall = box.shape[0]
    inked = box.any(axis=1)
    left = np.where(inked, box.argmax(axis=1), box.shape[1]).astype(float)
    quarter = max(1, tall // 4)
    middle = left[int(0.4 * tall):int(0.6 * tall) + 1]
    return float(np.median(middle) - max(left[:quarter].min(), left[tall - quarter:].min()))


def _cut_stroke(box: np.ndarray, space: float) -> bool:
    """Whether a piece of ink with the size of a C has the upright stroke of the sign of cut time through it, which
    stands out of the C at its top and at its bottom (COMMON_CUT)."""
    tall, wide = box.shape
    full = box.mean(axis=0)
    first, last = int(COMMON_CUT[2] * wide), int(COMMON_CUT[3] * wide) + 1
    columns = [column for column in range(first, min(last, wide)) if full[column] >= COMMON_CUT[1]]
    if not columns:
        return False
    slack = COMMON_CUT[4] * space
    for row in (box[0], box[-1]):
        inked = np.nonzero(row)[0]
        if not len(inked) or inked[0] < columns[0] - slack or inked[-1] > columns[-1] + slack:
            return False
    return True


def bold_commons(layers: dict, staff: dict, first: float, last: float, every: bool = False) -> list[dict]:
    """The bold signs of common time of a staff between the columns first and last, by their shape (COMMON_BOLD): each
    {'x0', 'x1', 'common', 'bold'} with the measures 'high', 'wide', 'ink', 'waist' (staff spaces) and 'arms' (how
    far the ink reaches to the right in the upper and in the lower fifth of its rows, as a share of the width). With
    `every`, the pieces with any waist and any arms (for a census)."""
    if not COMMON_BOLD:
        return []
    low, high, off, narrow, wide, apart, thin, full, bow = COMMON_BOLD
    free = _free(layers)
    height, width = free.shape
    space, rows = staff['space'], staff['rows']
    y0, y1 = max(0, int(rows[0] - 1.5 * space)), min(height, int(rows[4] + 1.5 * space) + 1)
    x0, x1 = max(0, int(first)), min(width, int(last) + 1)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return []
    region = cv2.morphologyEx(np.ascontiguousarray(free[y0:y1, x0:x1]), cv2.MORPH_CLOSE,
                              np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)
    tall = max(high, COMMON_CUT[0]) if COMMON_CUT else high
    pieces = sorted((int(x), int(y), int(bw), int(bh), label) for label, (x, y, bw, bh, _) in enumerate(stats) if label
                    and low * space <= bh <= tall * space and abs(y0 + y + bh / 2 - rows[2]) <= off * space)
    found, used = [], set()
    for index, (x, y, bw, bh, label) in enumerate(pieces):
        if index in used:
            continue
        group = [(x, y, bw, bh, label)]
        if index + 1 < len(pieces) and pieces[index + 1][0] - (x + bw) <= apart * space \
                and max(bh, pieces[index + 1][3]) <= high * space:      # (a piece as high as the sign of cut time stands alone)
            group.append(pieces[index + 1])
            used.add(index + 1)
        elif COMMON_ENDS and bw < narrow * space:
            # A print parts the two ends of the bow from it: small pieces at its right, in its rows.
            group += [(int(ox), int(oy), int(ow), int(oh), other) for other, (ox, oy, ow, oh, _) in enumerate(stats)
                      if other and other != label and x < ox <= x + bw + COMMON_ENDS[0] * space
                      and y - COMMON_ENDS[1] * space <= oy and oy + oh <= y + bh + COMMON_ENDS[1] * space
                      and ox + ow - x <= wide * space]
        left, right = group[0][0], max(piece[0] + piece[2] for piece in group)
        top, bottom = min(piece[1] for piece in group), max(piece[1] + piece[3] for piece in group)
        if not narrow * space <= right - left <= wide * space:
            continue
        own = np.isin(labels[:, left:right], [piece[4] for piece in group])
        box = own[top:bottom]
        if not thin <= box.mean() <= full:
            continue
        cut = False
        if cv2.connectedComponents(layers['holes'][y0 + top:y0 + bottom, x0 + left:x0 + right].astype(np.uint8))[0] > 2:
            # More than one piece of closed paper: the sign of cut time, by its stroke and the open side of its C.
            cut = bool(COMMON_CUT) and len(group) == 1 and _cut_stroke(box, space)
            if not cut:
                continue
        elif bottom - top > high * space:
            continue
        # Nothing else stands in its columns just over or under it (a stem, a head a third away).
        others = (labels[:, left:right] > 0) & ~own
        if others[max(0, top - int(space / 2)):bottom + int(space / 2)].sum() > 0.1 * space * space:
            continue
        waist = _waist(box) / space
        # The two ends of the bow turn to the right: the stroke of a flat stands at the left over its bowl.
        fifth = max(1, box.shape[0] // 5)
        arms = [float(np.nonzero(rows_.any(axis=0))[0].max() + 1) / box.shape[1] if rows_.any() else 0.0
                for rows_ in (box[:fifth], box[-fifth:])]
        if (waist > bow or min(arms) < COMMON_ARM) and not every:
            continue
        found.append({'x0': float(x0 + left), 'x1': float(x0 + right - 1), 'common': True, 'bold': True, 'cut': cut,
                      'high': (bottom - top) / space, 'wide': (right - left) / space, 'ink': float(box.mean()), 'waist': waist,
                      'arms': arms})
    return found


def start_sign(layers: dict, staff: dict, first: float, last: float, key_end: float | None = None) -> dict | None:
    """The time signature that begins between the columns first and last, at the start of a staff: {'x0', 'x1'};
    two numbers, or with COMMON the sign of common time ('common': True). `key_end` is the column where the key
    signature of the staff ends, where it is known: numbers that pass only by the wider limit stand after it
    (TIME_LOOSE), and where it is not known they do not count."""
    reach = last + TIME_WIDE[1] * staff['space']
    found = [{name: value for name, value in sign.items() if name != 'loose'} for sign in time_signs(layers, staff, first, reach)
             if sign['x0'] <= last and (not sign.get('loose') or key_end is not None and sign['x0'] >= key_end - TIME_LOOSE[1] * staff['space'])]
    if COMMON:
        found += [sign for sign in common_signs(layers, staff, first, reach) if sign['x0'] <= last]
    return min(found, key=lambda sign: sign['x0']) if found else None


def mid_signs(layers: dict, ends: list[float], bars: dict) -> dict:
    """The time signatures after the start of each staff: {staff index: [{'x0', 'x1'}]}. `ends` says where the notes
    of each staff begin, and `bars` holds the bar lines of each staff. In a system of two or more staves, the
    numbers stand at one place in two staves or more. In a system of one staff, a bar line stands before them."""
    staves = layers['staves']
    found = {index: [{name: value for name, value in sign.items() if name != 'loose'}
                     for sign in time_signs(layers, staff, ends[index], weak=bool(TIME_MATE), black=True) if sign['x0'] >= ends[index]]
             for index, staff in enumerate(staves)}
    kept = {index: [] for index in found}

    def after_bar(index: int, sign: dict) -> bool:
        return any(0 <= sign['x0'] - bar <= TIME_AFTER * staves[index]['space'] for bar in bars.get(index, []))

    for index, staff in enumerate(staves):
        space = staff['space']
        mates = [other for other, mate in enumerate(staves) if mate['system'] == staff['system'] and other != index]
        for sign in found[index]:
            middle = (sign['x0'] + sign['x1']) / 2
            if mates:
                there = [(mate, other) for mate in mates for other in found[mate]
                         if abs((other['x0'] + other['x1']) / 2 - middle) <= TIME_PAIR * space]
                if sign.get('weak'):
                    # TIME_MATE: beside the numbers that another staff shows by every measure, both after a bar line.
                    sure = after_bar(index, sign) and any(not other.get('weak') and after_bar(mate, other) for mate, other in there)
                else:
                    sure = any(not other.get('weak') for _, other in there) \
                        or after_bar(index, sign) and any(after_bar(mate, other) for mate, other in there)
            else:
                sure = not sign.get('weak') and after_bar(index, sign)
            if sure:
                kept[index].append(sign)
    # The bold C of a print, at the start of the notes or after a bar line (COMMON_BOLD, COMMON_AT).
    for index, staff in enumerate(staves):
        space = staff['space']
        for sign in bold_commons(layers, staff, ends[index] - 2 * space, staff['x1']):
            if sign['x0'] - ends[index] <= COMMON_AT[0] * space \
                    or any(0 <= sign['x0'] - bar <= COMMON_AT[1] * space for bar in bars.get(index, [])):
                kept[index] = sorted(kept[index] + [sign], key=lambda found: found['x0'])
    return kept


# ----------------------------------------------------------------------------------------------------------------
# Time signature reading: classify numerator, denominator, common time (C), and cut time (C|).

_DIGIT_FONTS = (
    '/usr/share/fonts/noto/NotoSerif-Bold.ttf',
    '/usr/share/fonts/liberation/LiberationSerif-Bold.ttf',
    '/usr/share/fonts/noto/NotoSerif-Regular.ttf',
    '/usr/share/fonts/noto/NotoMusic-Regular.ttf',
)
_SMUFL_DIGITS = {
    '2': '\U0001D100',  # fallback only if font lacks standard digits; serif fonts use ASCII
}
VALID_METERS = {
    (2, 2), (3, 2), (4, 2),
    (2, 4), (3, 4), (4, 4), (5, 4), (6, 4),
    (3, 8), (6, 8), (9, 8), (12, 8),
}
_DIGIT_HOLES = {'2': 0, '3': 0, '4': 1, '6': 1, '8': 2, '9': 1, '12': 0}


def _normalize_glyph(mask: np.ndarray, size: int = 24) -> np.ndarray | None:
    """Tight-crops a binary glyph mask and centers it inside a size x size float32 square."""
    ys, xs = np.nonzero(mask)
    if len(ys) < 6:
        return None
    crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    h, w = crop.shape
    scale = (size - 4) / max(h, w)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    out = np.zeros((size, size), np.float32)
    y0, x0 = (size - nh) // 2, (size - nw) // 2
    out[y0:y0 + nh, x0:x0 + nw] = resized
    return out


def _closed_hole_count(mask: np.ndarray) -> int:
    """Counts interior paper holes in a binary glyph mask."""
    if mask.size == 0:
        return 0
    pad = np.pad((mask == 0).astype(np.uint8), 1, constant_values=1)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(pad, connectivity=4)
    outside = labels[0, 0]
    min_area = max(3, int(0.015 * mask.shape[0] * mask.shape[1]))
    return sum(1 for k in range(1, count) if k != outside and stats[k, cv2.CC_STAT_AREA] >= min_area)


@lru_cache(maxsize=1)
def _digit_templates() -> dict[str, list[np.ndarray]]:
    """Builds multi-font normalized 24x24 templates for time-signature digits."""
    templates: dict[str, list[np.ndarray]] = {d: [] for d in ('2', '3', '4', '6', '8', '9', '12')}
    try:
        from PIL import Image, ImageDraw, ImageFont
        available = [p for p in _DIGIT_FONTS[:3] if Path(p).exists()]
        for font_path in available:
            font = ImageFont.truetype(font_path, 48)
            for digit in templates:
                img = Image.new('L', (96, 96), 255)
                draw = ImageDraw.Draw(img)
                draw.text((48, 48), digit, font=font, fill=0, anchor='mm')
                arr = (np.array(img) < 180).astype(np.uint8)
                norm = _normalize_glyph(arr)
                if norm is not None:
                    templates[digit].append(norm)
                    # Add a slightly bolded variant for heavy prints and scans.
                    bold = cv2.dilate(arr, np.ones((3, 3), np.uint8))
                    nb = _normalize_glyph(bold)
                    if nb is not None:
                        templates[digit].append(nb)
    except Exception:
        pass
    # Always include clean OpenCV Hershey fallback templates so zero external font is required.
    for font_id in (cv2.FONT_HERSHEY_TRIPLEX, cv2.FONT_HERSHEY_DUPLEX, cv2.FONT_HERSHEY_SIMPLEX):
        for digit in templates:
            canvas = np.zeros((96, 96), np.uint8)
            cv2.putText(canvas, digit, (14, 72), font_id, 2.0, 1, 4, cv2.LINE_AA)
            norm = _normalize_glyph(canvas)
            if norm is not None:
                templates[digit].append(norm)
    return templates


def _classify_digit(mask: np.ndarray, allowed: tuple[str, ...]) -> tuple[str | None, float]:
    """Classifies a single time-signature number mask against multi-font templates."""
    norm = _normalize_glyph(mask)
    if norm is None:
        return None, 0.0
    ys, xs = np.nonzero(mask)
    aspect = (xs.max() - xs.min() + 1) / max(1.0, ys.max() - ys.min() + 1)
    holes = _closed_hole_count(mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    vec = norm.ravel()
    vec = vec - vec.mean()
    vnorm = float(np.linalg.norm(vec))
    if vnorm < 1e-6:
        return None, 0.0
    vec /= vnorm
    templates = _digit_templates()
    best_digit, best_score = None, -1.0
    # Measure left-edge openness in the middle band: '3' is open on the left, while '6' has a solid left curve.
    crop_bin = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1] > 0
    ch, cw = crop_bin.shape
    left_mid = float(crop_bin[int(0.25 * ch):max(int(0.25 * ch) + 1, int(0.75 * ch)), :max(1, int(0.32 * cw))].any(axis=1).mean())
    right_mid = float(crop_bin[int(0.25 * ch):max(int(0.25 * ch) + 1, int(0.75 * ch)), max(0, int(0.68 * cw)):].any(axis=1).mean())
    for digit in allowed:
        if digit == '12' and aspect < 0.95:
            continue
        if digit != '12' and aspect > 1.45:
            continue
        best_t = -1.0
        for tpl in templates.get(digit, ()):
            tv = tpl.ravel()
            tv = tv - tv.mean()
            tnorm = float(np.linalg.norm(tv))
            if tnorm > 1e-6:
                score = float(np.dot(vec, tv / tnorm))
                if score > best_t:
                    best_t = score
        # Apply mild shape-structure cues (closed loops + left-vs-right openness for 3 vs 6).
        want_holes = _DIGIT_HOLES.get(digit, 0)
        if holes == want_holes:
            best_t += 0.04
        elif abs(holes - want_holes) >= 2:
            best_t -= 0.08
        if digit == '3':
            if left_mid < 0.65 and right_mid >= 0.70:
                best_t += 0.12
            elif left_mid >= 0.85:
                best_t -= 0.10
        elif digit == '6':
            if left_mid >= 0.80:
                best_t += 0.08
            elif left_mid < 0.55:
                best_t -= 0.12
        if best_t > best_score:
            best_digit, best_score = digit, best_t
    return best_digit, best_score


def read_meter(layers: dict, staff: dict, sign: dict) -> tuple[tuple[int, int, str | None] | None, float]:
    """Reads a detected time-signature box as ((beats, beat_type, symbol), confidence).

    Returns ((4, 4, 'common'), conf) for C, ((2, 2, 'cut'), conf) for cut time,
    or ((num, den, None), conf) for stacked numbers.
    """
    space, rows = staff['space'], staff['rows']
    if sign.get('common'):
        if sign.get('cut'):
            return (2, 2, 'cut'), 0.95
        # Check for a vertical cut-time slash extending over and under the C arc.
        free = _free(layers)
        x0 = max(0, int(sign['x0']) - 1)
        x1 = min(free.shape[1], int(sign['x1']) + 2)
        y0 = max(0, int(rows[0] - 0.8 * space))
        y1 = min(free.shape[0], int(rows[4] + 0.8 * space) + 1)
        if x1 > x0 and y1 > y0:
            crop = cv2.morphologyEx(np.ascontiguousarray(free[y0:y1, x0:x1]), cv2.MORPH_CLOSE,
                                    np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8))
            ys_all = np.nonzero(crop.any(axis=1))[0]
            if len(ys_all):
                c_high = (ys_all[-1] - ys_all[0] + 1) / space
                mid_x0 = int(0.28 * (x1 - x0))
                mid_x1 = max(mid_x0 + 1, int(0.76 * (x1 - x0)))
                col_span = crop[ys_all[0]:ys_all[-1] + 1, mid_x0:mid_x1].mean(axis=0)
                if c_high >= 2.55 and len(col_span) and float(col_span.max()) >= 0.82:
                    return (2, 2, 'cut'), 0.90
        return (4, 4, 'common'), 0.90

    free = _free(layers)
    h, w = free.shape
    x0 = max(0, int(sign['x0']) - 1)
    x1 = min(w, int(sign['x1']) + 2)
    top, mid, bot = rows[0], rows[2], rows[4]
    y_top = max(0, int(top - 0.35 * space))
    y_mid = int(round(mid))
    y_bot = min(h, int(bot + 0.35 * space) + 1)
    if x1 - x0 < 3 or y_mid <= y_top + 2 or y_bot <= y_mid + 2:
        return None, 0.0
    close_k = np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8)
    upper = cv2.morphologyEx(np.ascontiguousarray(free[y_top:y_mid, x0:x1]), cv2.MORPH_CLOSE, close_k)
    lower = cv2.morphologyEx(np.ascontiguousarray(free[y_mid:y_bot, x0:x1]), cv2.MORPH_CLOSE, close_k)
    num, n_conf = _classify_digit(upper, ('2', '3', '4', '6', '9', '12'))
    den, d_conf = _classify_digit(lower, ('2', '4', '8'))
    if num is None or den is None:
        return None, 0.0
    pair = (int(num), int(den))
    if pair not in VALID_METERS:
        return None, 0.0
    conf = 0.5 * (n_conf + d_conf)
    return (pair[0], pair[1], None), conf


def page_meter(layers: dict, starts: list[dict], times: dict[int, list[dict]],
               ends: list[float]) -> tuple[tuple[int, int, str | None] | None, dict[int, list[tuple[float, tuple[int, int, str | None]]]]]:
    """Determines the opening meter of a page (voted across System 0 staves) and any mid-page meter changes.

    Returns (opening_meter, changes_by_staff) where each change is (x_column, (beats, beat_type, symbol)).
    """
    staves = layers['staves']
    if not staves:
        return None, {}
    sys0 = [idx for idx, staff in enumerate(staves) if staff['system'] == 0]
    votes: dict[tuple[int, int, str | None], list[float]] = {}
    for idx in sys0:
        staff = staves[idx]
        space = staff['space']
        cands = []
        if starts[idx].get('time'):
            cands.append(starts[idx]['time'])
        for sign in times.get(idx, []):
            if sign['x0'] <= ends[idx] + 5.0 * space:
                cands.append(sign)
        if not cands:
            # Scan right after the clef/key region on System 0 staves for bold C/cut or stacked numbers.
            key_right = starts[idx].get('end', starts[idx]['x1'])
            scan_left = key_right - 0.5 * space if starts[idx].get('key', 0) != 0 else starts[idx]['x1'] - 0.3 * space
            scan_right = max(ends[idx], key_right) + 5.5 * space
            cands.extend(bold_commons(layers, staff, scan_left - 1.0 * space, scan_right))
            cands.extend(s for s in time_signs(layers, staff, starts[idx]['x1'] - 0.3 * space, scan_right)
                         if s['x0'] <= max(ends[idx], key_right) + 4.5 * space)
        best_here = None
        for sign in cands:
            parsed, conf = read_meter(layers, staff, sign)
            if parsed is not None and conf >= 0.42:
                if best_here is None or conf > best_here[1]:
                    best_here = (parsed, conf)
        if best_here is not None:
            votes.setdefault(best_here[0], []).append(best_here[1])

    opening = None
    if votes:
        best_m = max(votes, key=lambda m: (len(votes[m]), sum(votes[m])))
        # On a single-staff system require higher confidence; on multi-staff allow 1 strong vote or >=2 votes.
        if len(votes[best_m]) >= 2 or max(votes[best_m]) >= 0.55:
            opening = best_m

    changes: dict[int, list[tuple[float, tuple[int, int, str | None]]]] = {}
    for idx, staff in enumerate(staves):
        space = staff['space']
        for sign in times.get(idx, []):
            if idx in sys0 and sign['x0'] <= ends[idx] + 5.0 * space:
                continue
            parsed, conf = read_meter(layers, staff, sign)
            if parsed is not None and conf >= 0.50:
                changes.setdefault(idx, []).append((float(sign['x0']), parsed))
    return opening, changes

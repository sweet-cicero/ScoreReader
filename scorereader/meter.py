"""Finds the time signatures of a staff, so that their numbers are not read as notes or as sharps. No model is used.

A time signature is two numbers, one over the other. The upper number fills the staff from the top line to the
middle line, and the lower number fills it from the middle line to the bottom line. No note does that: a head is one
staff space high, and the stem of a note leaves the staff, or it has a head on one half of the staff only.

The shape alone is not sure in the middle of a staff (a rest, or a note with a flag in a poor copy, can fill both
halves): there the music must agree. The staves of a system change the time at one place, and the new time stands
right after a bar line.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
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
        if weak:
            upper = abs(begin - top) <= edge and middle - edge <= end <= bottom + edge
            lower = abs(end - bottom) <= edge and top - edge <= begin <= bottom - 0.8 * space
        else:
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
        # In mid-staff scans (weak=True, system-verified), include in-staff digit fragments broken by staff lines.
        extra = [label for label in range(1, count)
                 if weak and label not in own
                 and stats[label][3] >= 0.4 * space and stats[label][4] >= 0.08 * space * space
                 and begin <= stats[label][0] and stats[label][0] + stats[label][2] - 1 <= end
                 and top - edge <= y0 + stats[label][1]
                 and y0 + stats[label][1] + stats[label][3] - 1 <= bottom + edge]
        mask = np.isin(labels[:, begin:end + 1], own + extra)
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
        # Reject a narrow right-side arc sitting directly right of a taller cut-time slash.
        if bw < 0.65 * space and any(
                other != label
                and 2.6 * space <= stats[other][3] <= 3.4 * space
                and abs(y0 + stats[other][1] + stats[other][3] / 2 - middle) <= COMMON_OFF * space
                and stats[other][0] < x
                and -0.2 * space <= x - (stats[other][0] + stats[other][2]) <= 0.6 * space
                for other in range(1, count)):
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
COMMON_CUT = (3.6, 0.9, 0.3, 0.75, 0.15)   # the sign of cut time is such a C with an upright stroke through it, and the
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


def _bold_commons_in(layers: dict, staff: dict, first: float, last: float, every: bool,
                     free: np.ndarray) -> list[dict]:
    """Finds bold C and cut-time signs in one ink layer."""
    low, high, off, narrow, wide, apart, thin, full, bow = COMMON_BOLD
    height, width = free.shape
    space, rows = staff['space'], staff['rows']
    y0, y1 = max(0, int(rows[0] - 2.0 * space)), min(height, int(rows[4] + 2.0 * space) + 1)
    x0, x1 = max(0, int(first)), min(width, int(last) + 1)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return []
    region = cv2.morphologyEx(np.ascontiguousarray(free[y0:y1, x0:x1]), cv2.MORPH_CLOSE,
                              np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8))
    # Locate narrow full-staff vertical barlines inside the scan window so barline-adjacent C signs keep after_bar
    # and thin horizontal staff-line bridges trapped between a barline and a bold C are severed cleanly.
    top_rel = max(0, int(round(rows[0] - y0)))
    bot_rel = min(region.shape[0] - 1, int(round(rows[4] - y0)))
    bar_cols: list[float] = []
    half_t = max(2, int(round(staff['thick'])) + 2)
    if bot_rel > top_rel:
        staff_cols = region[top_rel:bot_rel + 1].mean(axis=0)
        full_mask = staff_cols >= 0.90
        col, rw = 0, region.shape[1]
        while col < rw:
            if not full_mask[col]:
                col += 1
                continue
            run_end = col
            while run_end < rw and full_mask[run_end]:
                run_end += 1
            if run_end - col <= max(4, int(round(0.35 * space))):
                left_clear = col == 0 or float(region[top_rel:bot_rel + 1, max(0, col - 2):col].mean()) < 0.15
                if left_clear:
                    bar_cols.append(float(x0 + (col + run_end - 1) / 2.0))
                    # Strip pure thin staff-line bridge columns trapped between this barline and an adjacent C bow.
                    bridge_end = min(rw, run_end + int(round(1.2 * space)))
                    if bridge_end > run_end:
                        for row_y in rows[1:4]:
                            ry = int(round(row_y - y0))
                            r0, r1 = max(0, ry - half_t), min(region.shape[0], ry + half_t + 1)
                            if r0 > 0 and r1 < region.shape[0]:
                                above_clear = region[r0 - 1, run_end:bridge_end] == 0
                                below_clear = region[r1, run_end:bridge_end] == 0
                                thin_cols = np.nonzero(above_clear & below_clear)[0]
                                if len(thin_cols):
                                    region[r0:r1, run_end + thin_cols] = 0
                    right_touch = run_end < rw and float(region[top_rel:bot_rel + 1, run_end:min(rw, run_end + 3)].mean()) >= 0.04
                    if right_touch:
                        region[:, col:run_end] = 0
            col = run_end
    count, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)
    tall = max(high, COMMON_CUT[0]) if COMMON_CUT else high
    tall_scan = max(tall, 5.8) if COMMON_CUT else high
    pieces = sorted((int(x), int(y), int(bw), int(bh), label) for label, (x, y, bw, bh, _) in enumerate(stats) if label
                    and low * space <= bh <= tall_scan * space and abs(y0 + y + bh / 2 - rows[2]) <= off * space)
    found, used = [], set()
    for index, (x, y, bw, bh, label) in enumerate(pieces):
        if index in used:
            continue
        group = [(x, y, bw, bh, label)]
        if index + 1 < len(pieces) and pieces[index + 1][0] - (x + bw) <= apart * space \
                and max(bh, pieces[index + 1][3]) <= tall * space \
                and max(x + bw, pieces[index + 1][0] + pieces[index + 1][2]) - x <= wide * space:
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
        oversized = (right - left > wide * space) or (bottom - top > tall * space)
        if oversized:
            if not (narrow * space <= right - left <= 2.85 * space and bottom - top <= tall_scan * space):
                continue
        elif not narrow * space <= right - left <= wide * space:
            continue
        own = np.isin(labels[:, left:right], [piece[4] for piece in group])
        box = own[top:bottom]
        if not thin <= box.mean() <= full:
            continue
        cut = False
        after_bar = any(0 <= (x0 + left) - bx <= COMMON_AT[1] * space for bx in bar_cols)
        has_multi_holes = (_closed_hole_count(box.astype(np.uint8)) > 1 if after_bar
                           else cv2.connectedComponents(layers['holes'][y0 + top:y0 + bottom, x0 + left:x0 + right].astype(np.uint8))[0] > 2)
        if has_multi_holes:
            # More than one piece of closed paper: the sign of cut time, by its stroke and the open side of its C.
            cut = bool(COMMON_CUT) and _cut_stroke(box, space)
            if not cut:
                continue
        elif bottom - top > high * space:
            cut = bool(COMMON_CUT) and _cut_stroke(box, space)
            if not cut:
                continue
        elif bottom - top >= 2.4 * space and COMMON_CUT and _cut_stroke(box, space):
            cut = True
        # Nothing else stands in its columns just over or under it (a stem, a head a third away).
        others = (labels[:, left:right] > 0) & ~own
        pad_other = int(space / 4) if cut else int(space / 2)
        if others[max(0, top - pad_other):bottom + pad_other].sum() > 0.15 * space * space:
            continue
        waist = _waist(box) / space
        # The two ends of the bow turn to the right: on cut time, the vertical slash extends past the C arms.
        arm_band = max(1, box.shape[0] // (3 if cut else 5))
        arms = [float(np.nonzero(rows_.any(axis=0))[0].max() + 1) / box.shape[1] if rows_.any() else 0.0
                for rows_ in (box[:arm_band], box[-arm_band:])]
        if oversized:
            if bottom - top > high * space and (not cut or (right - left) < 2.20 * space):
                continue
            if not cut and (right - left) > 2.40 * space:
                continue
            arm_ok = min(arms) >= 0.65
            waist_ok = waist <= -0.22
        elif cut:
            arm_ok = min(arms) >= 0.48 and max(arms) >= 0.80
            waist_ok = waist <= -0.15 and (right - left) >= 1.18 * space
        else:
            arm_ok = min(arms) >= COMMON_ARM or (min(arms) >= 0.40 and max(arms) >= 0.85 and waist <= -0.08)
            waist_ok = waist <= bow
        if (not waist_ok or not arm_ok) and not every:
            continue
        found.append({'x0': float(x0 + left), 'x1': float(x0 + right - 1), 'common': True, 'bold': True, 'cut': cut,
                      'high': (bottom - top) / space, 'wide': (right - left) / space, 'ink': float(box.mean()), 'waist': waist,
                      'arms': arms, 'after_bar': after_bar})
    return found


def bold_commons(layers: dict, staff: dict, first: float, last: float, every: bool = False) -> list[dict]:
    """The bold signs of common time of a staff between the columns first and last, by their shape (COMMON_BOLD): each
    {'x0', 'x1', 'common', 'bold'} with the measures 'high', 'wide', 'ink', 'waist' (staff spaces) and 'arms' (how
    far the ink reaches to the right in the upper and in the lower fifth of its rows, as a share of the width). With
    `every`, the pieces with any waist and any arms (for a census)."""
    if not COMMON_BOLD:
        return []
    found = _bold_commons_in(layers, staff, first, last, every, _free(layers))
    if TIME_LINES:
        # Second pass on staff-line-stripped ink frees bold C signs bridged to a preceding barline by staff lines.
        extra = [sign for sign in _bold_commons_in(layers, staff, first, last, every, _number_ink(layers))
                 if _apart(sign, found)]
        if extra:
            found = sorted(found + extra, key=lambda sign: sign['x0'])
    return found


def _oversized_time_signs(layers: dict, staff: dict, first: float | None = None, last: float | None = None) -> list[dict]:
    """Finds oversized handwritten numeric time signatures that protrude symmetrically above and below the staff."""
    free = _free(layers)
    height, width = free.shape
    space, rows = staff['space'], staff['rows']
    top, middle, bottom = rows[0], rows[2], rows[4]
    y0, y1 = max(0, int(top - 2.4 * space)), min(height, int(bottom + 2.4 * space) + 1)
    x0 = max(0, int(staff['x0'] if first is None else first))
    x1 = min(width, int(staff['x1'] if last is None else last) + 1)
    if x1 - x0 < 5 or y1 - y0 < 10:
        return []
    region = cv2.morphologyEx(np.ascontiguousarray(free[y0:y1, x0:x1]), cv2.MORPH_CLOSE,
                              np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)
    parts = []
    for label in range(1, count):
        x, y, bw, bh, _ = (int(v) for v in stats[label])
        if not (1.10 * space <= bw <= 2.90 * space and 1.80 * space <= bh <= 8.5 * space):
            continue
        begin, end = y0 + y, y0 + y + bh - 1
        # Either an oversized single stacked piece or an upper/lower digit extending outside the staff.
        upper = (top - 2.35 * space <= begin <= top - 0.65 * space) and (end >= middle - 0.55 * space)
        lower = (bottom + 0.65 * space <= end <= bottom + 2.35 * space) and (begin <= middle + 0.55 * space)
        if upper or lower:
            parts.append((x, x + bw - 1, label))
    parts.sort()
    groups = []
    for part in parts:
        if groups and part[0] <= groups[-1][1] + 0.25 * space and max(groups[-1][1], part[1]) - groups[-1][0] + 1 <= 2.90 * space:
            groups[-1][1] = max(groups[-1][1], part[1])
            groups[-1][2].append(part[2])
        else:
            groups.append([part[0], part[1], [part[2]]])
    split = int(round(middle - y0))
    found = []
    for begin, end, own in groups:
        gw = end - begin + 1
        if not (1.35 * space <= gw <= 2.90 * space):
            continue
        mask = np.isin(labels[:, begin:end + 1], own)
        u_ys, u_xs = np.nonzero(mask[:split])
        l_ys, l_xs = np.nonzero(mask[split:])
        if len(u_ys) < 12 or len(l_ys) < 12:
            continue
        u_top, u_bot = y0 + int(u_ys.min()), y0 + int(u_ys.max())
        l_top, l_bot = y0 + split + int(l_ys.min()), y0 + split + int(l_ys.max())
        u_w, u_h = int(u_xs.max() - u_xs.min() + 1), u_bot - u_top + 1
        l_w, l_h = int(l_xs.max() - l_xs.min() + 1), l_bot - l_top + 1
        if not (top - 2.35 * space <= u_top <= top - 0.65 * space and bottom + 0.65 * space <= l_bot <= bottom + 2.35 * space):
            continue
        if u_w < 1.10 * space or l_w < 1.10 * space or u_h < 1.80 * space or l_h < 1.80 * space:
            continue
        # Require wide glyph ink strictly outside the staff on both top and bottom (rejects stems of stacked chords).
        top_rel = max(1, int(round(top - y0)) - 2)
        bot_rel = min(mask.shape[0] - 1, int(round(bottom - y0)) + 2)
        u_out_xs = np.nonzero(mask[:top_rel])[1]
        l_out_xs = np.nonzero(mask[bot_rel:])[1]
        if not len(u_out_xs) or not len(l_out_xs):
            continue
        u_out_w = int(u_out_xs.max() - u_out_xs.min()) + 1
        l_out_w = int(l_out_xs.max() - l_out_xs.min()) + 1
        if u_out_w < 0.90 * space or l_out_w < 0.90 * space:
            continue
        shared = min(int(u_xs.max()), int(l_xs.max())) - max(int(u_xs.min()), int(l_xs.min())) + 1
        if shared < 0.65 * min(u_w, l_w):
            continue
        # Reject full-staff vertical barlines at the left or right edge and thick filled notehead blots.
        inside = mask[max(0, int(top - y0)):int(bottom - y0) + 1]
        cols = inside.mean(axis=0)
        if inside.size and (cols[0] >= 0.95 or cols[-1] >= 0.95):
            continue
        esize = max(3, int(round(0.78 * space)))
        thick = cv2.erode(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (esize, esize)))
        if thick.sum() > 0.14 * space * space:
            continue
        cand = {
            'x0': float(x0 + begin), 'x1': float(x0 + end),
            'y_top': float(u_top), 'y_bot': float(l_bot), 'oversized': True,
        }
        parsed, conf = read_meter(layers, staff, cand)
        if parsed is not None and conf >= 0.45:
            found.append(cand)
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
    if not found:
        # Fallback for oversized handwritten fonts: check bold C/cut before stacked numbers so giant C| stays cut time.
        if COMMON:
            found += [sign for sign in bold_commons(layers, staff, first, reach + staff['space'])
                      if sign['x0'] <= last and sign['wide'] > COMMON_BOLD[4]]
        if not found:
            found += [sign for sign in _oversized_time_signs(layers, staff, first, reach + staff['space']) if sign['x0'] <= last]
    return min(found, key=lambda sign: sign['x0']) if found else None


def mid_signs(layers: dict, ends: list[float], bars: dict) -> dict:
    """The time signatures after the start of each staff: {staff index: [{'x0', 'x1'}]}. `ends` says where the notes
    of each staff begin, and `bars` holds the bar lines of each staff. In a system of two or more staves, the
    numbers stand at one place in two staves or more. In a system of one staff, a bar line stands before them."""
    staves = layers['staves']
    found = {index: [{name: value for name, value in sign.items() if name != 'loose'}
                     for sign in time_signs(layers, staff, ends[index], weak=bool(TIME_MATE), black=True) if sign['x0'] >= ends[index]]
             for index, staff in enumerate(staves)}
    for index, staff in enumerate(staves):
        extra_ov = _oversized_time_signs(layers, staff, ends[index], staff['x1'])
        for sign in extra_ov:
            if sign['x0'] >= ends[index] and _apart(sign, found[index]):
                found[index].append(sign)
        found[index].sort(key=lambda sign: sign['x0'])
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
                if sign.get('oversized'):
                    at_open = staff['system'] == 0 and sign['x0'] - ends[index] <= 5.5 * space
                    sure = (at_open and bool(there)) or (after_bar(index, sign) and any(after_bar(mate, other) for mate, other in there))
                elif sign.get('weak'):
                    # TIME_MATE: beside the numbers that another staff shows by every measure, both after a bar line.
                    sure = after_bar(index, sign) and any(not other.get('weak') and after_bar(mate, other) for mate, other in there)
                else:
                    sure = any(not other.get('weak') for _, other in there) \
                        or after_bar(index, sign) and any(after_bar(mate, other) for mate, other in there)
            else:
                sure = not sign.get('weak') and (
                    after_bar(index, sign)
                    or (sign.get('oversized') and staff['system'] == 0 and sign['x0'] - ends[index] <= 5.5 * space)
                )
            if sure:
                kept[index].append(sign)
    # The bold C of a print, at the start of the notes or after a bar line (COMMON_BOLD, COMMON_AT).
    bold_by_staff = {index: bold_commons(layers, staff, ends[index] - 2 * staff['space'], staff['x1'])
                     for index, staff in enumerate(staves)}
    for index, staff in enumerate(staves):
        space = staff['space']
        mates = [other for other, mate in enumerate(staves) if mate['system'] == staff['system'] and other != index]
        for sign in bold_by_staff[index]:
            at_start = sign['x0'] - ends[index] <= COMMON_AT[0] * space
            at_bar = any(0 <= sign['x0'] - bar <= COMMON_AT[1] * space for bar in bars.get(index, []))
            if not at_bar and sign.get('after_bar'):
                if not mates:
                    at_bar = True
                else:
                    mid_x = (sign['x0'] + sign['x1']) / 2.0
                    at_bar = any(
                        abs((other['x0'] + other['x1']) / 2.0 - mid_x) <= TIME_PAIR * space
                        for mate in mates for other in bold_by_staff[mate]
                    )
            if (at_start or at_bar) and _apart(sign, kept[index]):
                kept[index] = sorted(kept[index] + [sign], key=lambda found_: found_['x0'])
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
_DIGIT_HOLES = {'2': 0, '3': 0, '4': 1, '5': 0, '6': 1, '8': 2, '9': 1, '12': 0}


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
    templates: dict[str, list[np.ndarray]] = {d: [] for d in ('2', '3', '4', '5', '6', '8', '9', '12')}
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


def _bridge_staff_rows(free: np.ndarray, ink: np.ndarray, staff: dict,
                       y0: int, y1: int, x0: int, x1: int) -> np.ndarray:
    """Bridges vertical staff-line breaks only in a narrow 2-3 px band around each staff line."""
    crop = np.ascontiguousarray(free[y0:y1, x0:x1]).astype(np.uint8)
    out = crop.copy()
    h, w = crop.shape
    half = max(1, min(3, int(round(staff['thick'] / 2.0))))
    for row in staff['rows']:
        ry = int(round(row)) - y0
        r0 = max(0, ry - half)
        r1 = min(h, ry + half + 1)
        if r0 <= 0 or r1 >= h:
            continue
        above = crop[max(0, r0 - 2):r0, :].any(axis=0)
        below = crop[r1:min(h, r1 + 2), :].any(axis=0)
        cols = above & below
        if cols.any():
            out[r0:r1, cols] = np.maximum(out[r0:r1, cols], (ink[y0 + r0:y0 + r1, x0:x1][:, cols] > 0).astype(np.uint8))
    return out


def _digit_scores(mask: np.ndarray, allowed: tuple[str, ...]) -> dict[str, float]:
    """Scores each allowed time-signature digit using multi-font templates, topology cues, and local TimeNet."""
    norm = _normalize_glyph(mask)
    if norm is None:
        return {}
    ys, xs = np.nonzero(mask)
    aspect = (xs.max() - xs.min() + 1) / max(1.0, ys.max() - ys.min() + 1)
    crop_bin = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1] > 0
    holes = _closed_hole_count(crop_bin.astype(np.uint8))
    vec = norm.ravel()
    vec = vec - vec.mean()
    vnorm = float(np.linalg.norm(vec))
    if vnorm < 1e-6:
        return {}
    vec /= vnorm
    templates = _digit_templates()
    # Measure topological cues: left openness, right continuity, flat bottom bar (2 vs 3), and bottom-left lobe.
    ch, cw = crop_bin.shape
    left_mid = float(crop_bin[int(0.25 * ch):max(int(0.25 * ch) + 1, int(0.75 * ch)), :max(1, int(0.32 * cw))].any(axis=1).mean())
    right_mid = float(crop_bin[int(0.25 * ch):max(int(0.25 * ch) + 1, int(0.75 * ch)), max(0, int(0.68 * cw)):].any(axis=1).mean())
    right_upper = float(crop_bin[int(0.22 * ch):max(int(0.22 * ch) + 1, int(0.48 * ch)), max(0, int(0.65 * cw)):].any(axis=1).mean())
    right_lower = float(crop_bin[int(0.55 * ch):max(int(0.55 * ch) + 1, int(0.85 * ch)), max(0, int(0.65 * cw)):].any(axis=1).mean())
    mid_right_lower = float(crop_bin[int(0.55 * ch):max(int(0.55 * ch) + 1, int(0.78 * ch)), max(0, int(0.68 * cw)):].mean())
    bottom_bar = float(crop_bin[int(0.80 * ch):, :].any(axis=0).mean())
    bottom_left = float(crop_bin[int(0.68 * ch):, :max(1, int(0.42 * cw))].mean())
    flat_two = holes == 0 and bottom_bar >= 0.85 and mid_right_lower < 0.42
    scores: dict[str, float] = {}
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
        # Apply shape-structure cues for holes, 3 vs 6 openness, 2 vs 3 bottom bar, and 3 vs 4 bottom-left.
        want_holes = _DIGIT_HOLES.get(digit, 0)
        if holes == want_holes:
            best_t += 0.04
        elif abs(holes - want_holes) >= 2:
            best_t -= 0.08
        if digit == '2':
            if flat_two:
                best_t += 0.05
        elif digit == '3':
            if bottom_left < 0.35:
                best_t -= 0.14
            elif holes == 0 and left_mid < 0.72 and right_mid >= 0.85 and right_lower >= 0.75:
                best_t += 0.12
            elif holes == 0 and not flat_two and left_mid < 0.96 and right_mid >= 0.90 and right_upper >= 0.85 and right_lower >= 0.75:
                best_t += 0.08
            elif left_mid >= 0.98 and holes >= 1:
                best_t -= 0.10
        elif digit == '6':
            if left_mid >= 0.95 and holes >= 1:
                best_t += 0.08
                if right_upper <= 0.75:
                    best_t += 0.04
            elif holes == 0 and right_mid >= 0.90 and right_upper >= 0.85:
                best_t -= 0.14
            elif left_mid < 0.65:
                best_t -= 0.12
        elif digit == '4':
            if bottom_left <= 0.38 and right_mid >= 0.80:
                best_t += 0.06
            elif bottom_left >= 0.60:
                best_t -= 0.08
        scores[digit] = best_t
    if not scores:
        return {}
    best_digit = max(scores, key=lambda d: scores[d])
    best_score = scores[best_digit]
    # Blend multi-font template matching with local offline TimeNet when neural models are enabled.
    try:
        from . import headnet
        from .classify import classify_time_crop
        tn_label, tn_prob = classify_time_crop(mask) if headnet.weights() is not None else (None, 0.0)
    except Exception:
        tn_label, tn_prob = None, 0.0
    if tn_label in scores and tn_prob >= 0.60:
        block_override = (
            (best_digit == '4' and tn_label == '3' and bottom_left <= 0.40)
            or (best_digit == '3' and tn_label == '6' and holes == 0 and right_mid >= 0.90 and right_upper >= 0.85)
            or (best_digit == '4' and best_score >= 0.75 and tn_label == '3')
        )
        if tn_label == best_digit:
            scores[tn_label] = max(scores[tn_label], tn_prob)
        elif not block_override:
            scores[tn_label] = scores[tn_label] + 0.16 * tn_prob
            if tn_prob >= 0.88 and best_score < 0.78:
                scores[tn_label] = max(scores[tn_label], tn_prob)
    return scores


def _classify_digit(mask: np.ndarray, allowed: tuple[str, ...]) -> tuple[str | None, float]:
    """Classifies a single time-signature number mask against multi-font templates and local TimeNet."""
    scores = _digit_scores(mask, allowed)
    if not scores:
        return None, 0.0
    best_digit = max(scores, key=lambda d: scores[d])
    return best_digit, scores[best_digit]


def read_meter(layers: dict, staff: dict, sign: dict) -> tuple[tuple[int, int, str | None] | None, float]:
    """Reads a detected time-signature box as ((beats, beat_type, symbol), confidence).

    Returns ((4, 4, 'common'), conf) for C, ((2, 2, 'cut'), conf) for cut time,
    or ((num, den, None), conf) for stacked numbers.
    """
    space, rows = staff['space'], staff['rows']
    if sign.get('common'):
        if sign.get('cut'):
            return (2, 2, 'cut'), 0.95
        # Check for a vertical cut-time slash extending over and under the C arc (expanding left for split C|).
        free = _free(layers)
        y0 = max(0, int(rows[0] - 0.8 * space))
        y1 = min(free.shape[0], int(rows[4] + 0.8 * space) + 1)
        close_k = np.ones((int(staff['thick'] + 3) | 1, 1), np.uint8)
        for left_pad in (0.0, 0.8 * space):
            x0 = max(0, int(sign['x0'] - left_pad) - 1)
            x1 = min(free.shape[1], int(sign['x1']) + 2)
            if x1 <= x0 or y1 <= y0:
                continue
            crop = cv2.morphologyEx(np.ascontiguousarray(free[y0:y1, x0:x1]), cv2.MORPH_CLOSE, close_k)
            ys_all = np.nonzero(crop.any(axis=1))[0]
            if not len(ys_all):
                continue
            c_high = (ys_all[-1] - ys_all[0] + 1) / space
            c_mid = (y0 + (ys_all[0] + ys_all[-1]) / 2.0 - rows[2]) / space
            mid_x0 = int(0.28 * (x1 - x0))
            mid_x1 = max(mid_x0 + 1, int(0.76 * (x1 - x0)))
            col_span = crop[ys_all[0]:ys_all[-1] + 1, mid_x0:mid_x1].mean(axis=0)
            if 2.55 <= c_high <= 3.65 and abs(c_mid) <= 0.55 and len(col_span) and float(col_span.max()) >= 0.82:
                # For the left-expanded search, also verify the vertical slash stands inside the C rather than on a barline.
                if left_pad == 0.0 or _cut_stroke(crop[ys_all[0]:ys_all[-1] + 1], space):
                    return (2, 2, 'cut'), 0.90
        return (4, 4, 'common'), 0.90

    free = _free(layers)
    ink = layers['ink']
    h, w = free.shape
    x0 = max(0, int(sign['x0']) - 1)
    x1 = min(w, int(sign['x1']) + 2)
    top, mid, bot = rows[0], rows[2], rows[4]
    y_mid = int(round(mid))
    if sign.get('oversized') and 'y_top' in sign and 'y_bot' in sign:
        y_top = max(0, int(sign['y_top']) - 2)
        y_bot = min(h, int(sign['y_bot']) + 3)
    else:
        y_top = max(0, int(top - 0.35 * space))
        y_bot = min(h, int(bot + 0.35 * space) + 1)
    if x1 - x0 < 3 or y_mid <= y_top + 2 or y_bot <= y_mid + 2:
        return None, 0.0
    upper = _bridge_staff_rows(free, ink, staff, y_top, y_mid, x0, x1)
    lower = _bridge_staff_rows(free, ink, staff, y_mid, y_bot, x0, x1)
    u_scores = _digit_scores(upper, ('2', '3', '4', '5', '6', '9', '12'))
    l_scores = _digit_scores(lower, ('2', '4', '8'))
    if not u_scores or not l_scores:
        return None, 0.0
    best_pair = None
    best_conf = -1.0
    for num, den in VALID_METERS:
        ns, ds = str(num), str(den)
        if ns in u_scores and ds in l_scores:
            conf = 0.5 * (u_scores[ns] + l_scores[ds])
            if conf > best_conf:
                best_pair, best_conf = (num, den), conf
    if best_pair is None or best_conf < 0.35:
        return None, 0.0
    return (best_pair[0], best_pair[1], None), best_conf


_BAR_LENGTH_METERS: dict[Fraction, tuple[int, int, str | None]] = {
    Fraction(3, 2): (3, 8, None),
    Fraction(2): (2, 4, None),
    Fraction(3): (3, 4, None),
    Fraction(4): (4, 4, None),
    Fraction(5): (5, 4, None),
    Fraction(6): (3, 2, None),
}


def infer_opening_meter(bar_lengths) -> tuple[int, int, str | None] | None:
    """Infers an opening time signature from bar durations on excerpt pages without a printed opening meter.

    Returns (beats, beat_type, None) when a standard meter accounts for at least half of two or more bars,
    or None when bars are empty or irregular.
    """
    vals: list[Fraction] = []
    for raw in (bar_lengths or ()):
        if raw is None:
            continue
        length = Fraction(raw).limit_denominator(16)
        if length > 0:
            vals.append(length)
    if len(vals) < 2:
        return None
    counts = Counter(vals)
    first_pos = {}
    for pos, length in enumerate(vals):
        first_pos.setdefault(length, pos)
    best_len = max(counts, key=lambda length: (counts[length], -first_pos[length]))
    if counts[best_len] < 2 or counts[best_len] / len(vals) < 0.5:
        return None
    return _BAR_LENGTH_METERS.get(best_len)


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
            if not cands:
                cands.extend(s for s in _oversized_time_signs(layers, staff, starts[idx]['x1'] - 0.3 * space, scan_right)
                             if s['x0'] <= max(ends[idx], key_right) + 5.5 * space)
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

    raw_changes: dict[int, list[tuple[float, tuple[int, int, str | None], float]]] = {}
    for idx, staff in enumerate(staves):
        space = staff['space']
        for sign in times.get(idx, []):
            if idx in sys0 and sign['x0'] <= ends[idx] + 5.0 * space:
                continue
            parsed, conf = read_meter(layers, staff, sign)
            if parsed is not None and conf >= 0.50:
                raw_changes.setdefault(idx, []).append((float(sign['x0']), parsed, conf))

    # Reconcile mid-page meter changes across staves of the same system at matching x-columns,
    # and propagate high-confidence (>= 0.85) changes to mate staves of the same system.
    changes: dict[int, list[tuple[float, tuple[int, int, str | None]]]] = {}
    for idx, staff in enumerate(staves):
        space = staff['space']
        mates = [other for other, mate in enumerate(staves) if mate['system'] == staff['system']]
        reconciled: list[tuple[float, tuple[int, int, str | None]]] = []
        for cx, parsed, conf in raw_changes.get(idx, ()):
            col_votes: dict[tuple[int, int, str | None], list[float]] = {}
            for mate in mates:
                for ox, oparsed, oconf in raw_changes.get(mate, ()):
                    if abs(ox - cx) <= TIME_PAIR * space:
                        col_votes.setdefault(oparsed, []).append(oconf)
            winner = max(col_votes, key=lambda m: (len(col_votes[m]), sum(col_votes[m]))) if col_votes else parsed
            reconciled.append((cx, winner))
        for mate in mates:
            if mate == idx:
                continue
            for ox, oparsed, oconf in raw_changes.get(mate, ()):
                if oconf < 0.85:
                    continue
                if any(abs(ex - ox) <= TIME_PAIR * space for ex, _ in reconciled):
                    continue
                reconciled.append((ox, oparsed))
        if reconciled:
            changes[idx] = sorted(reconciled, key=lambda item: item[0])
    return opening, changes

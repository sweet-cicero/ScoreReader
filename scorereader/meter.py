"""Finds the time signatures of a staff, so that their numbers are not read as notes or as sharps. No model is used.

A time signature is two numbers, one over the other. The upper number fills the staff from the top line to the
middle line, and the lower number fills it from the middle line to the bottom line. No note does that: a head is one
staff space high, and the stem of a note leaves the staff, or it has a head on one half of the staff only.

The shape alone is not sure in the middle of a staff (a rest, or a note with a flag in a poor copy, can fill both
halves): there the music must agree. The staves of a system change the time at one place, and the new time stands
right after a bar line.
"""
from __future__ import annotations

import cv2
import numpy as np

TIME_EDGE = 0.2          # a number begins and ends at most this far from the top, middle or bottom line, in staff spaces
TIME_WIDE = (0.6, 2.2)   # each number is this wide, in staff spaces
TIME_WIDER = 1.0         # and one of the two is at least this wide (a quarter rest fills the staff too, but it is slim)
TIME_HIGH = 1.4          # each number is at least this high
TIME_INK = 0.2           # the ink of a number fills at least this share of its box
TIME_OVER = 0.6          # the two numbers stand one over the other: this share of the narrower one
TIME_BAR = 0.97          # no column of the numbers is ink along this share of the staff's height: that is a bar line
TIME_WAIST = (0.3, 0.45) # the ink within this many staff spaces of the middle line is at least this wide, or there is none
TIME_PAIR = 1.5          # the staves of a system change the time at one place: at most this far apart, in staff spaces
TIME_AFTER = 3.0         # in a system of one staff, a bar line stands at most this far before the numbers
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


def time_signs(layers: dict, staff: dict, first: float | None = None, last: float | None = None) -> list[dict]:
    """The time signatures of a staff between the columns first and last (the whole staff when they are not given):
    each {'x0', 'x1'}."""
    free = _free(layers)
    height, width = free.shape
    space, rows = staff['space'], staff['rows']
    top, middle, bottom = rows[0], rows[2], rows[4]
    edge = TIME_EDGE * space
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
        if crosses and not stacked:
            continue
        # A note with a flag fills both halves too (its head in one, its flag in the other): a head is a thick blot.
        size = max(3, int(round(TIME_HEAD[0] * space)))
        thick = cv2.erode(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
        if thick.sum() > TIME_HEAD[1] * space * space and not stacked:
            continue
        # The stem of a note crosses the middle line as one thin stroke. Two numbers meet there with more ink, or
        # they do not meet.
        waist = mask[max(0, split - int(TIME_WAIST[0] * space)):split + int(TIME_WAIST[0] * space) + 1].any(axis=0).sum()
        if 0 < waist < TIME_WAIST[1] * space and not (crosses and stacked):
            continue
        found.append({'x0': float(x0 + begin), 'x1': float(x0 + end)})
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


COMMON_BOLD = (1.8, 2.45, 0.15, 1.0, 1.9, 0.5, 0.25, 0.75, -0.05)   # the bold C of a print, which is read as a note
#   or two: its ink without the staff lines is one piece or two side by side, each this high (two numbers, in staff
#   spaces) with its middle at most this far from the middle line; together they are this wide (two numbers), at
#   most this far apart, they fill this share of their box (two numbers), they close in one piece of paper at most
#   (the ends of a bold C can touch), and the left edge stands further left in the middle rows than in the upper and
#   the lower quarter, by this at least (the bow; negative: left). A head is one space high and a head with its stem
#   is higher, the numbers of a time signature stand over and under the middle line, and an eighth rest, a double
#   sharp and two whole notes one over the other have a waist at the left where the C has its bow (a census of the
#   clean pages, each of 61 pieces looked at: 39 signs from -0.25 to -0.07, and 20 of the 22 other pieces from 0.0
#   on). None: off
COMMON_ARM = 0.6         # and its two ends turn to the right: in the upper and in the lower fifth of its rows the ink reaches
#   this share of its width (the signs of the clean pages: 0.81 and more; a flat that a hand draws large has its
#   stroke at the left over its bowl: up to 0.52 at one end, 14 such marks on the copies by hand)
# The ends of a bold C that stand apart from its bow begin at most this far past the bow's right edge and lie within
# this much of its rows (staff spaces). A head counts as ink of the sign only this near the middle line (COMMON_ROWS,
# staff spaces): a held note that is printed under the staff in the sign's columns is a note.
COMMON_ENDS = (0.5, 0.25)
COMMON_ROWS = 2.25
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
    pieces = sorted((int(x), int(y), int(bw), int(bh), label) for label, (x, y, bw, bh, _) in enumerate(stats) if label
                    and low * space <= bh <= high * space and abs(y0 + y + bh / 2 - rows[2]) <= off * space)
    found, used = [], set()
    for index, (x, y, bw, bh, label) in enumerate(pieces):
        if index in used:
            continue
        group = [(x, y, bw, bh, label)]
        if index + 1 < len(pieces) and pieces[index + 1][0] - (x + bw) <= apart * space:
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
        if cv2.connectedComponents(layers['holes'][y0 + top:y0 + bottom, x0 + left:x0 + right].astype(np.uint8))[0] > 2:
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
        found.append({'x0': float(x0 + left), 'x1': float(x0 + right - 1), 'common': True, 'bold': True,
                      'high': (bottom - top) / space, 'wide': (right - left) / space, 'ink': float(box.mean()), 'waist': waist,
                      'arms': arms})
    return found


def start_sign(layers: dict, staff: dict, first: float, last: float) -> dict | None:
    """The time signature that begins between the columns first and last, at the start of a staff: {'x0', 'x1'};
    two numbers, or with COMMON the sign of common time ('common': True)."""
    reach = last + TIME_WIDE[1] * staff['space']
    found = [sign for sign in time_signs(layers, staff, first, reach) if sign['x0'] <= last]
    if COMMON:
        found += [sign for sign in common_signs(layers, staff, first, reach) if sign['x0'] <= last]
    return min(found, key=lambda sign: sign['x0']) if found else None


def mid_signs(layers: dict, ends: list[float], bars: dict) -> dict:
    """The time signatures after the start of each staff: {staff index: [{'x0', 'x1'}]}. `ends` says where the notes
    of each staff begin, and `bars` holds the bar lines of each staff. In a system of two or more staves, the
    numbers stand at one place in two staves or more. In a system of one staff, a bar line stands before them."""
    staves = layers['staves']
    found = {index: [sign for sign in time_signs(layers, staff, ends[index]) if sign['x0'] >= ends[index]]
             for index, staff in enumerate(staves)}
    kept = {index: [] for index in found}
    for index, staff in enumerate(staves):
        space = staff['space']
        mates = [other for other, mate in enumerate(staves) if mate['system'] == staff['system'] and other != index]
        for sign in found[index]:
            middle = (sign['x0'] + sign['x1']) / 2
            if mates:
                sure = any(abs((other['x0'] + other['x1']) / 2 - middle) <= TIME_PAIR * space
                           for mate in mates for other in found[mate])
            else:
                sure = any(0 <= sign['x0'] - bar <= TIME_AFTER * space for bar in bars.get(index, []))
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

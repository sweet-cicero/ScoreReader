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


def _free(layers: dict) -> np.ndarray:
    """The ink without the staff lines (and without the filling of the holes)."""
    if 'unfilled' not in layers:
        layers['unfilled'] = layers['ink'] & (1 - layers['lines'])
    return layers['unfilled']


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
        if (inside.mean(axis=0) >= TIME_BAR).any():
            continue
        # A note with a flag fills both halves too (its head in one, its flag in the other): a head is a thick blot.
        size = max(3, int(round(TIME_HEAD[0] * space)))
        thick = cv2.erode(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
        if thick.sum() > TIME_HEAD[1] * space * space:
            continue
        # The stem of a note crosses the middle line as one thin stroke. Two numbers meet there with more ink, or
        # they do not meet.
        waist = mask[max(0, split - int(TIME_WAIST[0] * space)):split + int(TIME_WAIST[0] * space) + 1].any(axis=0).sum()
        if 0 < waist < TIME_WAIST[1] * space:
            continue
        found.append({'x0': float(x0 + begin), 'x1': float(x0 + end)})
    return found


def start_sign(layers: dict, staff: dict, first: float, last: float) -> dict | None:
    """The time signature that begins between the columns first and last, at the start of a staff: {'x0', 'x1'}."""
    found = [sign for sign in time_signs(layers, staff, first, last + TIME_WIDE[1] * staff['space']) if sign['x0'] <= last]
    return found[0] if found else None


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
    return kept

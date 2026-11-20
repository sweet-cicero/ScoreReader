"""Finds the fermatas of a page. No model is used.

A fermata is an arc about half as high as it is wide with a dot in its hollow: a dome over the staff, or a cup under
it for the lower voice. The middle of the arc is as thick as a filled head, and an arm of the arc stands like a
stem, so the symbol step read a fermata as a note with a flat head.

The arc is told by its whole shape. It is one piece of ink that is drawn through from end to end; its outer edge
has dropped little a quarter of the way in and much at its two ends, by about as much at both; its top lies near
its middle; both arms come down nearly to its open side. The dot is a small solid piece under the top of the arc,
in the hollow or just past the open side. A slur with a dot under it is longer and flatter, a bracket by hand
drops at once at its ends, and a letter by hand is no single stroke.

The limits come from a census of every arc with a dot on LitChoir's scan pages: 214 arcs pass, in print and by
hand, and each was looked at. A fermata that a scan cut and one with a pencil line through it are left out.
"""
from __future__ import annotations

import cv2
import numpy as np

ARC = (1.6, 3.6, 0.85, 2.2, 1.3, 4.0, 0.5)
#                                      the arc is from the first to the second number of staff spaces wide and from
#                                      the third to the fourth high, the fifth to the sixth times as wide as high, and
#                                      its ink fills at most the last number of its box. None: no fermata is read.
WHOLE = (0.95, 0.9)                  # this share of its columns holds ink, and this share of the columns of its
#                                      middle (from 0.2 to 0.8 of its width) holds one stroke only
ENDS = (0.08, 0.25, 0.25)            # at this share of its width from each end the outer edge has dropped by at least
#                                      the second number of its height, and the two ends differ by at most the third
QUARTERS = (0.25, 0.4)               # at this share of its width from each end the edge has dropped by at most this
APEX = (0.3, 0.7)                    # its top lies from this to this share of its width
ARMS = (0.15, 0.75)                  # in this share of its width at each end the ink comes down to this share of its
#                                      height
DOT = (0.15, 0.75, 0.5, 0.12, 0.05, 0.5)
#                                      the dot is from the first to the second number of staff spaces wide and high
#                                      and at least the third number of its box is ink; its middle lies within the
#                                      fourth number of the arc's width of the arc's middle, at most the fifth number
#                                      of the arc's height above the inner edge of the arc's middle, and at most the
#                                      last number of staff spaces past the open side
REACH = 0.2                          # a head whose middle lies in a fermata, or this many staff spaces outside it, is
#                                      no note


def fermatas(layers: dict) -> list[dict]:
    """The fermatas of a page: [{'x', 'x0', 'x1', 'top', 'bottom', 'dome', 'dot'}], where 'dome' says whether the arc
    is open at its bottom, and 'top' and 'bottom' hold the arc and its dot ('dot': the dot's own box)."""
    if ARC is None:
        return []
    space = layers['space']
    bare = layers['bare'].astype(np.uint8)
    count, labels, stats, middles = cv2.connectedComponentsWithStats(bare, connectivity=8)
    dots = [number for number in range(1, count)
            if DOT[0] * space <= stats[number][2] <= DOT[1] * space and DOT[0] * space <= stats[number][3] <= DOT[1] * space
            and stats[number][4] >= DOT[2] * stats[number][2] * stats[number][3]]
    out = []
    for number in range(1, count):
        x, y, wide, high, area = (int(value) for value in stats[number][:5])
        if not (ARC[0] * space <= wide <= ARC[1] * space and ARC[2] * space <= high <= ARC[3] * space
                and ARC[4] <= wide / high <= ARC[5] and area <= ARC[6] * wide * high):
            continue
        piece = labels[y:y + high, x:x + wide] == number
        rows = np.nonzero(piece[:, int(wide * 0.4):max(int(wide * 0.4) + 1, int(wide * 0.6))].any(axis=1))[0]
        if not len(rows):
            continue
        dome = bool(rows.mean() < high / 2)
        inner = _arc_shape(piece if dome else piece[::-1])
        if inner is None:
            continue
        for dot in dots:
            beside = (middles[dot][0] - (x + wide / 2)) / wide
            under = ((middles[dot][1] - y) if dome else (y + high - 1 - middles[dot][1])) / high
            if abs(beside) <= DOT[3] and inner - DOT[4] <= under <= 1.0 + DOT[5] * space / high:
                box = [int(stats[dot][0]), int(stats[dot][1]), int(stats[dot][0] + stats[dot][2] - 1), int(stats[dot][1] + stats[dot][3] - 1)]
                out.append({'x': x + wide / 2, 'x0': x, 'x1': x + wide, 'top': min(y, box[1]), 'bottom': max(y + high, box[3] + 1),
                            'dome': dome, 'dot': box})
                break
    return out


def _arc_shape(piece: np.ndarray) -> float | None:
    """Whether a piece of ink, set as a dome, has the shape of the arc of a fermata (see ARC): the inner edge of its
    middle as a share of its height, or None where it is no such arc."""
    high, wide = piece.shape
    inked = piece.any(axis=0)
    if inked.mean() < WHOLE[0]:
        return None
    tops = np.argmax(piece, axis=0).astype(float)
    lows = high - 1 - np.argmax(piece[::-1], axis=0).astype(float)
    runs = (np.diff(np.vstack([np.zeros((1, wide), bool), piece]).astype(np.int8), axis=0) == 1).sum(axis=0)
    # How thick the stroke is at the top of each column: its first run of ink.
    below = np.vstack([piece, np.zeros((1, wide), bool)])
    thick = np.array([np.argmin(below[int(top):, column]) for column, top in enumerate(tops)], float)

    def part(begin: float, end: float) -> np.ndarray:
        columns = np.zeros(wide, bool)
        columns[int(wide * begin):max(int(wide * begin) + 1, int(round(wide * end)))] = True
        return columns & inked

    middle = part(0.2, 0.8)
    if not middle.any() or (runs[middle] == 1).sum() < WHOLE[1] * (int(round(wide * 0.8)) - int(wide * 0.2)):
        return None
    top = tops[inked].min()
    if not APEX[0] <= float(np.argmax(inked & (tops == top))) / max(1, wide - 1) <= APEX[1]:
        return None
    drops = []
    for share in (ENDS[0], 1 - ENDS[0], QUARTERS[0], 1 - QUARTERS[0]):
        columns = part(max(0.0, share - 0.04), min(1.0, share + 0.04))
        if not columns.any():
            return None
        drops.append((tops[columns].mean() - top) / high)
    if min(drops[0], drops[1]) < ENDS[1] or abs(drops[0] - drops[1]) > ENDS[2] or max(drops[2], drops[3]) > QUARTERS[1]:
        return None
    for columns in (part(0.0, ARMS[0]), part(1 - ARMS[0], 1.0)):
        if not columns.any() or (lows[columns].max() + 1) / high < ARMS[1]:
            return None
    columns = part(0.3, 0.7)
    if not columns.any():
        return None
    return float(np.median((tops + thick)[columns])) / high


def on_fermata(head: dict, found: list[dict], space: float) -> bool:
    """Whether the middle of a head lies in a fermata."""
    return any(one['x0'] - REACH * space <= head['cx'] <= one['x1'] + REACH * space
               and one['top'] - REACH * space <= head['cy'] <= one['bottom'] + REACH * space for one in found)

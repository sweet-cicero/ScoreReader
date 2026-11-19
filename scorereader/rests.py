"""Finds the printed quarter rests of a page. No model is used.

A printed quarter rest is one piece of ink of its own, about three staff spaces high and one wide, that closes in no
paper: a stroke that swings to the right, back to the left, to the right again, and ends in a hook at the left. Its
thick middle is as fat as a filled head and its thin strokes stand like a stem, so the symbol step reads it as a
quarter note. The note with a stem has one straight edge, the stem's, from end to end; a pair of sharps, a natural
at its head and a clef close in paper; the rest has neither.

A rest is no note, and it says where a voice is silent: the note before it is not as long as the way to the next
note of its voice (scorereader.music.agree_lengths).

Only the printed quarter rest is read. The rests of a hand, the eighth rest and the rests that hang on a staff line
are not read yet.
"""
from __future__ import annotations

import cv2
import numpy as np

QUARTER = (2.0, 3.6, 0.7, 1.3)       # a quarter rest is from this to this many staff spaces high and from this to this
#                                      many wide (None: the rests are not read)
SWING = (0.12, 0.12, 0.03, 0.08)     # the middle of its ink, in eight parts from top to bottom: it goes right by this
#                                      many staff spaces in the first three parts, back left by this much in parts four
#                                      and five, right again by this much, and left by this much in the last two
EDGE = (0.15, 0.85)                  # neither its left nor its right edge is straight: within this many staff spaces of
#                                      its middle place over at most this share of the rows (a stem is straight)
HOLE = 0.02                          # it closes in no paper larger than this many square staff spaces
HOOK = (0.06, 0.7)                   # ... but the hook at its lower end can close: one piece of paper of at most this
#                                      many square staff spaces whose middle lies this far down the rest or further
#                                      (four rests of LitChoir's pages, 0.024 to 0.043 at 0.8; None: off)
OUTSIDE = 1.0                        # its middle lies in the staff or at most this many staff spaces outside it
REACH = 0.2                          # a head whose middle lies in the rest, or this many staff spaces outside it, is no note


def quarter_rests(layers: dict, ends: list[float]) -> list[dict]:
    """The printed quarter rests of a page: [{'staff', 'x', 'x0', 'x1', 'top', 'bottom', 'middle'}], where 'middle' is
    how many staff spaces the rest's middle lies under the middle line of its staff. `ends` holds for each staff
    where its clef and key signature end: nothing before that is a rest."""
    if QUARTER is None:
        return []
    space = layers['space']
    bare = layers['bare'].astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(bare, connectivity=8)
    out = []
    for number in range(1, count):
        x, y, wide, high = (int(value) for value in stats[number][:4])
        if not (QUARTER[0] * space <= high <= QUARTER[1] * space and QUARTER[2] * space <= wide <= QUARTER[3] * space):
            continue
        at = y + high / 2
        index = next((index for index, staff in enumerate(layers['staves'])
                      if staff['rows'][0] - OUTSIDE * space <= at <= staff['rows'][4] + OUTSIDE * space
                      and staff['x0'] <= x and x + wide <= staff['x1']), None)
        if index is None or x <= ends[index]:
            continue
        piece = labels[y:y + high, x:x + wide] == number
        if not _rest_shape(piece, space):
            continue
        out.append({'staff': index, 'x': x + wide / 2, 'x0': x, 'x1': x + wide, 'top': y, 'bottom': y + high,
                    'middle': (at - layers['staves'][index]['rows'][2]) / space})
    return out


def _rest_shape(piece: np.ndarray, space: float) -> bool:
    """Whether a piece of ink has the shape of a quarter rest (see SWING, EDGE and HOLE)."""
    high = piece.shape[0]
    # No paper closed in.
    paper = (~np.pad(piece, 1)).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
    closed = [number for number in range(1, count) if labels[0, 0] != number and stats[number][4] >= HOLE * space * space]
    if closed and not (HOOK and len(closed) == 1 and stats[closed[0]][4] <= HOOK[0] * space * space
                       and stats[closed[0]][1] + stats[closed[0]][3] / 2 - 1 >= HOOK[1] * high):
        return False
    # No straight edge.
    rows = [np.nonzero(row)[0] for row in piece]
    rows = [row for row in rows if len(row)]
    for edge in (np.array([row[0] for row in rows]), np.array([row[-1] for row in rows])):
        if (np.abs(edge - np.median(edge)) <= EDGE[0] * space).mean() > EDGE[1]:
            return False
    # The swing of the stroke.
    middle = np.array([np.nonzero(row)[0].mean() if row.any() else np.nan for row in piece]) / space
    parts = []
    for number in range(8):
        part = middle[int(high * number / 8):max(int(high * number / 8) + 1, int(high * (number + 1) / 8))]
        if np.isnan(part).all():
            return False
        parts.append(float(np.nanmean(part)))
    right = max(parts[1], parts[2])
    back = min(parts[3], parts[4])
    again = max(parts[4], parts[5])
    return right - parts[0] >= SWING[0] and right - back >= SWING[1] and again - back >= SWING[2] \
        and again - min(parts[6], parts[7]) >= SWING[3]


def in_rest(head: dict, rests: list[dict], space: float) -> bool:
    """Whether the middle of a head lies in a rest of its staff."""
    return any(rest['staff'] == head['staff'] and rest['x0'] - REACH * space <= head['cx'] <= rest['x1'] + REACH * space
               and rest['top'] - REACH * space <= head['cy'] <= rest['bottom'] + REACH * space for rest in rests)


BLOCK = (0.95, 1.8, 0.5, 0.9, 0.82, 0.8, 2.25)
#                                    a whole or a half rest is a block from the first to the second number of staff
#                                    spaces wide and from the third to the fourth high, whose box is at least the fifth
#                                    number ink, whose columns are nearly all ink over its height (at least the sixth
#                                    number of them), and whose middle lies at most the last number of staff spaces from
#                                    the middle line of its staff (None: the blocks are not read)


HANG = (0.15, 0.1)                   # a block hangs from a line where its top is at most the first number of staff spaces
#                                      over the line and the second under it (the top of a whole rest), and
SIT = (0.0, 0.2)                     # sits on a line where its bottom is from the first to the second number under it
#                                      (the bottom of a half rest: the line is ink under the block)


def block_rests(layers: dict, ends: list[float], measure: bool = False) -> list[dict]:
    """The printed whole and half rests of a page, as quarter_rests() gives the quarter rests, with 'kind' 'block'.
    With measure, every piece of the size of a block with its measures ('fill', 'square', 'middle'), and 'rest'
    whether it passes."""
    if BLOCK is None:
        return []
    space = layers['space']
    ink = layers['ink'] > 0
    free = layers['free'].astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(free, connectivity=8)
    out = []
    for number in range(1, count):
        x, y, wide, high = (int(value) for value in stats[number][:4])
        if not (0.8 * space <= wide <= 1.9 * space and 0.25 * space <= high <= 0.95 * space):
            continue
        at = y + high / 2
        index = next((index for index, staff in enumerate(layers['staves'])
                      if staff['rows'][0] - 2 * space <= at <= staff['rows'][4] + 2 * space
                      and staff['x0'] <= x and x + wide <= staff['x1']), None)
        if index is None or x <= ends[index]:
            continue
        box = ink[y:y + high, x:x + wide]
        fill = float(box.mean())
        square = float((box.sum(axis=0) >= 0.8 * high).mean())
        middle = (at - layers['staves'][index]['rows'][2]) / space
        rest = (BLOCK[0] * space <= wide <= BLOCK[1] * space and BLOCK[2] * space <= high <= BLOCK[3] * space
                and fill >= BLOCK[4] and square >= BLOCK[5] and abs(middle) <= BLOCK[6])
        if rest or measure:
            # A whole rest hangs from a line, a half rest sits on a line (the lines and the ledger lines next to them).
            rows = layers['staves'][index]['rows']
            lines = [rows[0] + step * (rows[4] - rows[0]) / 4 for step in range(-2, 7)]
            found = {'staff': index, 'x': x + wide / 2, 'x0': x, 'x1': x + wide, 'top': y, 'bottom': y + high,
                     'middle': middle, 'kind': 'block',
                     'hangs': any(-HANG[0] * space <= y - line <= HANG[1] * space for line in lines),
                     'sits': any(SIT[0] * space <= y + high - line <= SIT[1] * space for line in lines)}
            if measure:
                found.update(fill=fill, square=square, wide=wide / space, high=high / space, rest=rest)
            out.append(found)
    return out

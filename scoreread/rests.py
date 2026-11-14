"""Finds the printed quarter rests of a page. No model is used.

A printed quarter rest is one piece of ink of its own, about three staff spaces high and one wide, that closes in no
paper: a stroke that swings to the right, back to the left, to the right again, and ends in a hook at the left. Its
thick middle is as fat as a filled head and its thin strokes stand like a stem, so the symbol step reads it as a
quarter note. The note with a stem has one straight edge, the stem's, from end to end; a pair of sharps, a natural
at its head and a clef close in paper; the rest has neither.

A rest is no note, and it says where a voice is silent: the note before it is not as long as the way to the next
note of its voice (scoreread.music.agree_lengths).

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
    if any(labels[0, 0] != number and stats[number][4] >= HOLE * space * space for number in range(1, count)):
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

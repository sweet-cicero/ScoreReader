"""Puts the staves of a page into systems, from the page's own ink. No model is used.

Two staves that follow each other belong to one system when one of these is true:

1. The line that opens the system joins them at the left end of the staves (a brace or a bracket also counts).
2. Bar lines go through the gap between them.
3. Their bar lines stand at the same places along the page. A copyist who rules each staff by hand often draws no
   opening line, but the bars of the voices of one system still begin together.

Ink in the margin does not count: the shadow of a binding or the edge of a book stands more than one staff space
outside the staves.
"""
from __future__ import annotations

import numpy as np

from .staves import ink_mask, line_y

COVER = 0.6      # a joining line covers this share of the gap between two staves (measured: 0.73 to 1.00 for one
                 # system, 0.00 to 0.42 for two systems)
OUTSIDE = 1.0    # how far outside the staves' left end the opening line may stand, in staff spaces
INSIDE = 1.0     # and how far inside (a clef begins after that, and a clef's ink reaches into the gap)
ALIGNED = 0.6    # share of the bar lines of two staves that must stand at the same places (measured: 0.50 to 1.00
                 # for one system, 0.00 to 0.40 for two systems)
APART = 0.34     # at or under this share, the bar lines say that the staves are two systems


def _path_cover(window: np.ndarray) -> float:
    """The share of the rows of a window that the best line from its top to its bottom finds ink on. The line may lean:
    it can move one column to the left or to the right in every fourth row."""
    rows = window.shape[0]
    if rows < 3 or window.shape[1] < 1:
        return 0.0
    score = window[0].astype(np.int32)
    for row in range(1, rows):
        if row % 4 == 0:
            shifted = score.copy()
            shifted[1:] = np.maximum(shifted[1:], score[:-1])
            shifted[:-1] = np.maximum(shifted[:-1], score[1:])
            score = shifted
        score = score + window[row]
    return float(score.max() / rows)


def bar_lines(ink: np.ndarray, staff: dict) -> list[float]:
    """The places (x) of the staff's own bar lines: ink from its top line to its bottom line that stops there. A stem
    with its note head goes past an outer line or stops short of the other one. The bar lines at the staff's two ends
    are left out, because every staff of a page has those at the same places."""
    space = staff['space']
    found: list[float] = []
    run: list[int] = []
    for x in range(int(staff['left'] + 2 * space), int(staff['right'] - 2 * space)):
        top, bottom = line_y(staff['lines'][0], x), line_y(staff['lines'][4], x)
        y0, y1 = int(round(top)), int(round(bottom))
        if y0 < 0 or y1 >= ink.shape[0]:
            continue
        column = ink[:, x - 1:x + 2].any(axis=1)
        inside = column[y0:y1 + 1].mean()
        over = column[max(0, int(top - 0.75 * space)):max(0, int(top - 0.3 * space))]
        under = column[int(bottom + 0.3 * space):int(bottom + 0.75 * space)]
        clean = (len(over) == 0 or over.mean() < 0.5) and (len(under) == 0 or under.mean() < 0.5)
        if inside >= 0.97 and clean:
            if run and x - run[-1] > 2:
                found.append(sum(run) / len(run))
                run = []
            run.append(x)
    if run:
        found.append(sum(run) / len(run))
    # A double bar is one place.
    merged: list[float] = []
    for x in found:
        if merged and x - merged[-1] < 0.8 * space:
            merged[-1] = (merged[-1] + x) / 2
        else:
            merged.append(x)
    return merged


def joined(ink: np.ndarray, upper: dict, lower: dict) -> dict:
    """What joins two staves that follow each other: 'opening' (best cover of a line at the left end), 'bars' (lines
    through the gap along the staves), 'aligned' (share of their own bar lines at the same places, None when either
    has fewer than two) and 'same' (True when they are one system)."""
    space = (upper['space'] + lower['space']) / 2
    left = max(upper['left'], lower['left'])
    right = min(upper['right'], lower['right'])
    if right - left < 4 * space:
        return {'opening': 0.0, 'bars': 0, 'aligned': None, 'same': False}

    def gap(x: float) -> tuple[int, int]:
        xa = min(max(x, upper['left']), upper['right'])
        xb = min(max(x, lower['left']), lower['right'])
        return int(round(line_y(upper['lines'][4], xa) + 2)), int(round(line_y(lower['lines'][0], xb) - 2))

    first = max(1, int(min(upper['left'], lower['left']) - OUTSIDE * space))
    last = int(left + INSIDE * space)
    y0, y1 = gap(left)
    opening = _path_cover(ink[y0:y1, first:last]) if y1 - y0 >= 3 else 0.0
    bars = 0
    before = -10 ** 9
    for x in range(last, int(right) + 1):
        y0, y1 = gap(x)
        if y1 - y0 >= 3 and ink[y0:y1, x - 2:x + 3].any(axis=1).mean() >= 0.9:
            if x - before > 0.5 * space:
                bars += 1
            before = x
    own_upper, own_lower = bar_lines(ink, upper), bar_lines(ink, lower)
    aligned = None
    if len(own_upper) >= 2 and len(own_lower) >= 2:
        matched = sum(1 for x in own_upper if any(abs(x - other) <= 0.8 * space for other in own_lower))
        aligned = matched / max(len(own_upper), len(own_lower))
    if opening >= COVER or bars >= 2:
        weight = 2          # ink joins the staves: sure
    elif aligned is not None and aligned >= ALIGNED:
        weight = 1          # their bars begin together: likely one system
    elif aligned is not None and aligned <= APART:
        weight = -1         # their bars do not begin together: likely two systems
    else:
        weight = 0
    return {'opening': round(opening, 2), 'bars': bars, 'aligned': None if aligned is None else round(aligned, 2),
            'weight': weight, 'same': weight > 0}


def find_systems(grey: np.ndarray, staves: list[dict]) -> list[list[int]]:
    """The systems from the top of the page: each a list of staff indexes.

    Most pages have the same number of staves in each system. So the links between the staves are weighed together:
    the number of staves in a system is the one that agrees best with all the links, and it may not put apart two
    staves that ink joins. Then one weak place (a faded staff, a bar line that the copy lost) does not break a system.
    A page that no single number fits (a solo line over a choir, for example) is decided link by link."""
    ink = ink_mask(grey).astype(bool)
    count = len(staves)
    if count < 2:
        return [[index] for index in range(count)]
    links = [joined(ink, staves[index], staves[index + 1]) for index in range(count - 1)]
    weights = [link['weight'] for link in links]
    # Where some systems of the page have an opening line, a gap without any line there is likely between systems.
    if any(link['opening'] >= COVER for link in links):
        weights = [-1 if weight == 0 and link['opening'] < 0.45 and link['bars'] == 0 else weight
                   for weight, link in zip(weights, links)]
    best = None
    for size in range(1, min(count, 6) + 1):
        together = [(index + 1) % size != 0 for index in range(count - 1)]
        if any(weight == 2 and not same for weight, same in zip(weights, together)):
            continue
        score = sum(weight if same else -weight for weight, same in zip(weights, together))
        # Two staves that nothing joins are put into one system only against a cost, and a last system that is
        # not full (a staff that the copy lost) has a cost too.
        score -= sum(1.0 for weight, same in zip(weights, together) if same and weight <= 0)
        score -= 0.75 if count % size else 0.0
        if best is None or score > best[0]:
            best = (score, size)
    if best is not None:
        size = best[1]
        return [list(range(start, min(count, start + size))) for start in range(0, count, size)]
    systems: list[list[int]] = []
    for index in range(count):
        if index and weights[index - 1] > 0:
            systems[-1].append(index)
        else:
            systems.append([index])
    return systems

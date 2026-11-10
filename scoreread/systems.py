"""Puts the staves of a page into systems, from the page's own ink. No model is used.

Two staves that follow each other belong to one system when one of these is true:

1. The line that opens the system joins them at the left end of the staves (a brace or a bracket also counts).
2. Bar lines go through the gap between them.
3. Their bar lines stand at the same places along the page. A copyist who rules each staff by hand often draws no
   opening line, but the bars of the voices of one system still begin together.

Three checks on the whole page follow. A line at the left end that goes on over the first staff or under the last
staff is no opening line (SHADOW). Where the opening lines of a page all join the same number of staves, they say
what a system is, and a staff that no line joins stands alone (BLOCKS). On a page without opening lines, the notes
of the staves of one system stand in the same columns, and the notes of two systems do not (CONTRAST).

Ink in the margin does not count: the shadow of a binding or the edge of a book stands more than one staff space
outside the staves.
"""
from __future__ import annotations

import cv2
import numpy as np

from .staves import _blank, ink_mask, line_ink, line_y

COVER = 0.6      # a joining line covers this share of the gap between two staves (measured: 0.73 to 1.00 for one
                 # system, 0.00 to 0.42 for two systems)
OUTSIDE = 1.0    # how far outside the staves' left end the opening line may stand, in staff spaces
INSIDE = 1.0     # and how far inside (a clef begins after that, and a clef's ink reaches into the gap)
ALIGNED = 0.6    # share of the bar lines of two staves that must stand at the same places (measured: 0.50 to 1.00
                 # for one system, 0.00 to 0.40 for two systems)
APART = 0.34     # at or under this share, the bar lines say that the staves are two systems
SHADOW = (1.5, 5.5)     # a line at the left end that goes on from this many to this many staff spaces over the
#                         page's first staff, or under its last staff, is the shadow of a binding or the edge of the
#                         paper, and no line that opens a system (None: off)
BLOCKS = True           # where every opening line of the page joins the same number of staves, a system is what an
#                         opening line joins, and a staff that no line joins is a system by itself (False: off)
CONTRAST = (0.3, 0.5)   # on a page without opening lines, the systems have the number of staves at which the staves
#                         of a system stand in the same columns (in_step) this much more than two systems do, and at
#                         least this much (None: off)
STEP_START = 8.0        # the marks of two staves are compared from this many staff spaces after their left end
STEP_LEAST = 12.0       # along at least this many staff spaces
STEP_REACH = 2.5        # and up to this many staff spaces over and under each staff (at most to the middle of the gap)
LOST_LINES = (0.3, 2)   # a staff that the copy lost still shows this share of at least this many of its five lines
LOST_SHIFT = 1.0        # and it stands at most this many staff spaces from where the page's whole systems have it


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


def _marks(ink: np.ndarray, staff: dict, reach: float, first: int, last: int) -> np.ndarray:
    """The ink of a staff in each column from first to last, without its lines: the notes, stems and bar lines from
    `reach` px over the top line to `reach` px under the bottom line."""
    space = staff['space']
    xs = np.arange(first, last)
    inside = np.clip(xs, staff['left'], staff['right'])
    lines = np.array([[line_y(points, x) for x in inside[::8]] for points in staff['lines']])
    lines = np.array([np.interp(inside, inside[::8], row) for row in lines])
    top = np.round(lines[0] - reach).astype(int)
    rows = int(round(lines[4].mean() - lines[0].mean() + 2 * reach))
    index = top[None, :] + np.arange(rows)[:, None]
    band = ink[np.clip(index, 0, ink.shape[0] - 1), xs[None, :]].astype(bool)
    band &= (index >= 0) & (index < ink.shape[0])
    thick = max(2.0, 0.12 * space)
    for row in lines:
        band &= np.abs(index - row[None, :]) > thick
    return band.sum(axis=0).astype(np.float32)


def in_step(ink: np.ndarray, upper: dict, lower: dict) -> float | None:
    """How far the marks of two staves stand in the same columns: the correlation of their ink along the page, from
    -1 to 1, or None when they share too little of the page. The voices of one system sing together, so their notes
    stand one under the other; two systems do not line up. The clef and the key signature are left out: every staff
    has them at the same place."""
    space = (upper['space'] + lower['space']) / 2
    first = int(max(upper['left'], lower['left']) + STEP_START * space)
    last = int(min(upper['right'], lower['right']) - space)
    if last - first < STEP_LEAST * space:
        return None
    middle = (first + last) / 2
    gap = line_y(lower['lines'][0], middle) - line_y(upper['lines'][4], middle)
    reach = max(space, min(STEP_REACH * space, gap / 2 - 0.25 * space))
    size = max(3, int(round(space))) | 1
    a = cv2.blur(_marks(ink, upper, reach, first, last)[None, :], (size, 1))[0]
    b = cv2.blur(_marks(ink, lower, reach, first, last)[None, :], (size, 1))[0]
    if a.std() < 1e-6 or b.std() < 1e-6:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def joined(ink: np.ndarray, upper: dict, lower: dict) -> dict:
    """What joins two staves that follow each other: 'opening' (best cover of a line at the left end), 'bars' (lines
    through the gap along the staves), 'aligned' (share of their own bar lines at the same places, None when either
    has fewer than two) and 'same' (True when they are one system)."""
    space = (upper['space'] + lower['space']) / 2
    left = max(upper['left'], lower['left'])
    right = min(upper['right'], lower['right'])
    if right - left < 4 * space:
        return {'opening': 0.0, 'bars': 0, 'aligned': None, 'step': None, 'weight': 0, 'same': False}

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
    link = {'opening': round(opening, 2), 'bars': bars, 'aligned': None if aligned is None else round(aligned, 2),
            'step': in_step(ink, upper, lower) if BLOCKS or CONTRAST else None}
    link['weight'] = weigh(link)
    link['same'] = link['weight'] > 0
    return link


def weigh(link: dict) -> int:
    """How sure it is that two staves are one system (over 0) or two (under 0), from what joined() measured."""
    if link['opening'] >= COVER or link['bars'] >= 2:
        return 2            # ink joins the staves: sure
    if link['aligned'] is not None and link['aligned'] >= ALIGNED:
        return 1            # their bars begin together: likely one system
    if link['aligned'] is not None and link['aligned'] <= APART:
        return -1           # their bars do not begin together: likely two systems
    return 0


def shadows(ink: np.ndarray, staves: list[dict], links: list[dict]) -> None:
    """Takes the lines that are no opening lines out of the links. The line that opens a system ends at the top line
    of its first staff and at the bottom line of its last staff. A line that goes on over the first staff of the page,
    or under its last staff, is the shadow of a binding or the edge of the paper: it joins nothing."""
    def goes_on(staff: dict, down: bool) -> bool:
        space = staff['space']
        first = max(1, int(staff['left'] - OUTSIDE * space))
        last = int(staff['left'] + INSIDE * space)
        row = line_y(staff['lines'][4 if down else 0], staff['left'])
        y0, y1 = (row + SHADOW[0] * space, row + SHADOW[1] * space) if down else (row - SHADOW[1] * space, row - SHADOW[0] * space)
        y0, y1 = max(0, int(y0)), min(ink.shape[0], int(y1))
        return y1 - y0 >= 2 * space and _path_cover(ink[y0:y1, first:last]) >= COVER

    for order, staff, down in ((range(len(links)), staves[0], False), (range(len(links) - 1, -1, -1), staves[-1], True)):
        if not goes_on(staff, down):
            continue
        for index in order:
            if links[index]['opening'] < COVER:
                break
            links[index].update(opening=0.0, shadow=True)
            links[index]['weight'] = weigh(links[index])
            links[index]['same'] = links[index]['weight'] > 0


def _contrast(steps: list, size: int) -> tuple[float, float] | None:
    """For systems of `size` staves from the first staff on: (how much more the staves of a system stand in the same
    columns than two systems do, how much the staves of a system do), from the links' in_step values; None when a
    value is missing or no link lies inside a system."""
    inside = [step for index, step in enumerate(steps) if (index + 1) % size]
    between = [step for index, step in enumerate(steps) if (index + 1) % size == 0]
    if not inside or any(step is None for step in steps):
        return None
    mean = sum(inside) / len(inside)
    return (mean - sum(between) / len(between) if between else mean), mean


def group_staves(links: list[dict], count: int) -> list[list[int]]:
    """The systems of a page of `count` staves from the links between its staves: each a list of staff indexes.

    Most pages have the same number of staves in each system. So the links between the staves are weighed together:
    the number of staves in a system is the one that agrees best with all the links, and it may not put apart two
    staves that ink joins. Then one weak place (a faded staff, a bar line that the copy lost) does not break a system.

    With BLOCKS, the opening lines are believed where they all join the same number of staves and the weighing gives
    other systems: a staff over the first system that is no music, or a verse for one voice over a refrain for the
    choir. With CONTRAST, a page without opening lines takes the number of staves whose notes stand in the same
    columns."""
    weights = [link['weight'] for link in links]
    # Where some systems of the page have an opening line, a gap without any line there is likely between systems.
    if any(link['opening'] >= COVER for link in links):
        weights = [-1 if weight == 0 and link['opening'] < 0.45 and link['bars'] == 0 else weight
                   for weight, link in zip(weights, links)]
    steps = [link.get('step') for link in links]
    sure = [weight == 2 for weight in weights]
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
    if CONTRAST and not any(sure):
        found = None
        for size in range(2, min(count // 2, 6) + 1):
            if count % size == 0:
                contrast = _contrast(steps, size)
                if contrast and contrast[0] >= CONTRAST[0] and contrast[1] >= CONTRAST[1] and (found is None or contrast[0] > found[0]):
                    found = (contrast[0], size)
        if found:
            best = (0.0, found[1])
    if best is not None:
        size = best[1]
        systems = [list(range(start, min(count, start + size))) for start in range(0, count, size)]
    else:
        systems = []
        for index in range(count):
            if index and weights[index - 1] > 0:
                systems[-1].append(index)
            else:
                systems.append([index])
    if BLOCKS and any(sure):
        blocks: list[list[int]] = [[0]]
        for index in range(1, count):
            if sure[index - 1]:
                blocks[-1].append(index)
            else:
                blocks.append([index])
        sizes = {len(block) for block in blocks if len(block) >= 2}
        if len(sizes) == 1 and any(len(block) >= 2 and block not in systems for block in blocks):
            size = sizes.pop()
            systems, alone = [], []

            def close() -> None:
                # Staves that no line joins: systems of the page's size where their notes stand in the same columns.
                run = [steps[index] for index in alone[:-1]]
                contrast = _contrast(run, size) if alone and len(alone) % size == 0 else None
                if contrast and contrast[0] >= (CONTRAST or (0.3, 0.5))[0] and (len(alone) > size or contrast[1] >= 0.6):
                    systems.extend(alone[start:start + size] for start in range(0, len(alone), size))
                else:
                    systems.extend([index] for index in alone)
                alone.clear()

            for block in blocks:
                if len(block) >= 2:
                    close()
                    systems.append(block)
                else:
                    alone.append(block[0])
            close()
    return systems


def find_systems(grey: np.ndarray, staves: list[dict]) -> list[list[int]]:
    """The systems from the top of the page: each a list of staff indexes (see group_staves())."""
    ink = ink_mask(grey).astype(bool)
    count = len(staves)
    if count < 2:
        return [[index] for index in range(count)]
    links = [joined(ink, staves[index], staves[index + 1]) for index in range(count - 1)]
    if SHADOW:
        shadows(ink, staves, links)
    return group_staves(links, count)


def _mean_row(points: list, left: float, right: float) -> float:
    return float(np.mean([line_y(points, x) for x in np.linspace(left, right, 9)]))


def lost_staves(grey: np.ndarray, staves: list[dict], systems: list[list[int]]) -> tuple[list[dict], list[list[int]]]:
    """(staves, systems) with the staves that the copy lost.

    Every system of a choir page has the same staves. A poor copy can lose most of the lines of one staff: then the
    comb of five lines does not find it, a system has fewer staves than the others, and the notes of that staff are
    left over. The lost staff stands as far from its partner as in a system that is whole, and it bends as its
    partner does. What is left of its lines shows that it is there, and moves it into its exact place: at least
    LOST_LINES[1] of the five lines still have ink along LOST_LINES[0] of the staff. A lost staff has 'lost': True."""
    full = max((len(system) for system in systems), default=0)
    whole = [system for system in systems if len(system) == full]
    if full < 2 or len(whole) == len(systems):
        return staves, systems
    ink = ink_mask(grey)
    height = ink.shape[0]

    def distance(first: int, second: int, line: int) -> float:
        """How far line `line` of the staff at place `second` lies under the top line of the staff at place `first`,
        in staff spaces: the middle of the whole systems."""
        found = []
        for system in whole:
            a, b = staves[system[first]], staves[system[second]]
            left, right = max(a['left'], b['left']), min(a['right'], b['right'])
            found.append((_mean_row(b['lines'][line], left, right) - _mean_row(a['lines'][0], left, right)) / a['space'])
        return float(np.median(found))

    def look(anchor: dict, first: int, second: int) -> tuple[float, dict | None]:
        """The lost staff at place `second` of a system whose staff `anchor` stands at place `first`: (the ink on
        its lines, the staff), or (0, None) when the page shows no such staff."""
        space = anchor['space']
        dash = line_ink(ink, max(5, int(0.5 * space)))
        xs = np.arange(int(anchor['left']), int(anchor['right']), 2)
        base = np.array([line_y(anchor['lines'][0], x) for x in xs])
        reach = int(LOST_SHIFT * space)
        best = None
        for shift in range(-reach, reach + 1):
            covers = []
            for line in range(5):
                rows = np.round(base + distance(first, second, line) * space + shift).astype(int)
                inside = (rows >= 1) & (rows < height - 1)
                if inside.sum() < 0.9 * len(xs):
                    covers = None
                    break
                hit = dash[rows[inside] - 1, xs[inside]] | dash[rows[inside], xs[inside]] | dash[rows[inside] + 1, xs[inside]]
                covers.append(float(hit.mean()))
            if covers and (best is None or sum(covers) > best[0]):
                best = (sum(covers), shift, covers)
        if best is None or sum(cover >= LOST_LINES[0] for cover in best[2]) < LOST_LINES[1]:
            return 0.0, None
        lines = [[[point[0], round(line_y(anchor['lines'][0], point[0]) + distance(first, second, line) * space + best[1], 2)]
                  for point in anchor['lines'][0]] for line in range(5)]
        staff = {'left': anchor['left'], 'right': anchor['right'], 'space': space, 'lines': lines, 'lost': True}
        middle = (staff['left'] + staff['right']) / 2
        top, bottom = line_y(lines[0], middle), line_y(lines[4], middle)
        for other in staves:
            x = min(max(middle, other['left']), other['right'])
            if min(bottom, line_y(other['lines'][4], x)) - max(top, line_y(other['lines'][0], x)) > -0.5 * space:
                return 0.0, None        # another staff stands there
        if _blank(ink, staff):
            return 0.0, None
        return best[0], staff

    added: list[tuple[int, dict]] = []      # (the number of the system, the lost staff)
    for number, system in enumerate(systems):
        if len(system) == full:
            continue
        best = None
        for first in range(full - len(system) + 1):
            # The staves of the system stand at the places first, first + 1, ... of a whole system.
            own = {first + k: staves[index] for k, index in enumerate(system)}
            found, total = [], 0.0
            for place in range(full):
                if place in own:
                    continue
                near = min(own, key=lambda other: abs(other - place))
                score, staff = look(own[near], near, place)
                if staff is None:
                    found = None
                    break
                found.append(staff)
                total += score
            if found and (best is None or total > best[0]):
                best = (total, found)
        if best:
            added += [(number, staff) for staff in best[1]]
    if not added:
        return staves, systems
    owner = {id(staves[index]): number for number, system in enumerate(systems) for index in system}
    owner.update({id(staff): number for number, staff in added})
    every = sorted(staves + [staff for _, staff in added],
                   key=lambda staff: line_y(staff['lines'][0], (staff['left'] + staff['right']) / 2))
    out: list[list[int]] = [[] for _ in systems]
    for index, staff in enumerate(every):
        out[owner[id(staff)]].append(index)
    return every, out

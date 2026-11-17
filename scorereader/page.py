"""Builds a clean page from a scan: each system level, one under the other, with white margins. No model is used.

A reader that learned from engraved music expects level staves and a white margin. A scan of a bound copy has staves
that bend near the binding, a tilt, and shadows of the binding in the margin. The clean page takes these away and
keeps every mark of the music itself:

- In each column, every staff line of a system moves to its mean height. Between two lines the move changes evenly,
  and over the top line and under the bottom line it stays the same. So notes, stems and words keep their shapes.
- A system is cut out from the emptiest row over it to the emptiest row under it, so the words under a staff stay
  with their staff.
- Left and right, the cut stops a little outside the staves. The margin's ink does not come along.

clean_page() also returns where each system and each staff stands on the clean page, so a reader's result can be put
back on the scan.
"""
from __future__ import annotations

import cv2
import numpy as np

from .staves import ink_mask, line_y

MARGIN_X = 150       # white at the left and right of the clean page, px
MARGIN_Y = 200       # white over the first and under the last system
BETWEEN = 80         # white between two systems
SIDE = 0.8           # how far outside the staves a system is cut, in staff spaces (room for the opening line)
OVER = (3.0, 9.0)    # rows kept over the page's first staff: at least and at most, in staff spaces
UNDER = (4.0, 14.0)  # rows kept under the page's last staff: at least and at most
EMPTY = 1.8          # a band of paper this many staff spaces high ends the music of the first or the last system


def _level(grey: np.ndarray, staves: list[dict], top_keep: float, bottom_keep: float) -> tuple[np.ndarray, list[float], int]:
    """A system as a level strip: (image, the rows of each staff line in the strip, the scan's x of the strip's left
    edge). top_keep and bottom_keep are the px kept over the first line and under the last line."""
    height, width = grey.shape
    space = float(np.mean([staff['space'] for staff in staves]))
    left = int(max(0, min(staff['left'] for staff in staves) - SIDE * space))
    right = int(min(width, max(staff['right'] for staff in staves) + SIDE * space))
    targets = []       # the mean height of each staff line of the system
    sources = []       # for each line: its height in each column of the strip
    xs = np.arange(left, right)
    for staff in staves:
        inside = np.clip(xs, staff['left'], staff['right'])
        for points in staff['lines']:
            ys = np.array([line_y(points, x) for x in inside])
            own = (xs >= staff['left']) & (xs <= staff['right'])
            targets.append(float(ys[own].mean()))
            sources.append(ys)
    order = np.argsort(targets)
    targets = np.array(targets)[order]
    sources = np.array(sources)[order]
    first_row = targets[0] - top_keep
    rows = int(round(targets[-1] + bottom_keep - first_row))
    out_rows = first_row + np.arange(rows, dtype=np.float32)
    map_x = np.tile(xs.astype(np.float32), (rows, 1))
    map_y = np.zeros((rows, len(xs)), np.float32)
    for column in range(len(xs)):
        moves = sources[:, column] - targets
        map_y[:, column] = out_rows + np.interp(out_rows, targets, moves)
    strip = cv2.remap(grey, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=255)
    return strip, [float(target - first_row) for target in targets], left


PAPER_GREY = 240        # a page whose paper is darker than this somewhere is a photo: its paper is made white first
PAPER_PIECE = 200       # px at 300 dpi: no mark of ink is this large (the paper's brightness is taken over such pieces)
PAPER_LEAST = 70        # a place darker than this is not paper (the table around the page, a black border)


def flat_paper(grey: np.ndarray) -> np.ndarray:
    """The page with its paper made white. A scanner gives white paper; a photo of a page gives grey paper, darker
    at one side, and every limit between ink and paper then fails. The brightness of the paper is the brightest
    grey around each place, taken over pieces larger than any mark of ink; each place is then set against its paper.
    A page with white paper is given back as it is."""
    step = 8
    small = cv2.resize(grey, None, fx=1 / step, fy=1 / step, interpolation=cv2.INTER_AREA)
    size = max(3, PAPER_PIECE // step) | 1
    paper = cv2.morphologyEx(small, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    paper = cv2.GaussianBlur(paper, (0, 0), size / 4)
    if np.percentile(paper, 5) >= PAPER_GREY:
        return grey
    paper = cv2.resize(paper, (grey.shape[1], grey.shape[0]), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    flat = grey.astype(np.float32) * (255.0 / np.maximum(paper, PAPER_LEAST))
    return np.clip(flat, 0, 255).astype(np.uint8)


def _reach(ink: np.ndarray, staff: dict, down: bool, limits: tuple[float, float]) -> float:
    """How many px of the page belong to a staff beyond its outer line, over it or under it: up to the first band of
    paper that is EMPTY staff spaces high. Words, notes on ledger lines and a staff whose lines the copy lost stay
    with the system; a page number or a note at the foot of the page does not."""
    space = staff['space']
    least, most = int(limits[0] * space), int(limits[1] * space)
    line = staff['lines'][4 if down else 0]
    counts = np.zeros(most + 1)
    xs = range(int(staff['left']), int(staff['right']), 3)
    for x in xs:
        base = int(round(line_y(line, x)))
        for step in range(most + 1):
            y = base + step if down else base - step
            if 0 <= y < ink.shape[0]:
                counts[step] += ink[y, x]
    paper = counts <= 0.004 * len(xs)
    need = int(EMPTY * space)
    run = 0
    for step in range(least, most + 1):
        run = run + 1 if paper[step] else 0
        if run >= need:
            return float(step - need + int(0.4 * space))
    return float(most)


def _cuts(grey: np.ndarray, staves: list[dict], systems: list[list[int]]) -> list[tuple[float, float]]:
    """For each system: the px to keep over its first line and under its last line. Between two systems, the cut is
    the emptiest row in the lower part of the gap (the words under a staff belong to the staff over them)."""
    ink = ink_mask(grey)
    keep_under = []
    for number, system in enumerate(systems):
        last = staves[system[-1]]
        if number + 1 == len(systems):
            keep_under.append((_reach(ink, last, True, UNDER), None))
            continue
        following = staves[systems[number + 1][0]]
        x0, x1 = max(last['left'], following['left']), min(last['right'], following['right'])
        if x1 - x0 < 10:
            x0, x1 = last['left'], last['right']
        xs = np.linspace(x0, x1, 9)
        gaps = [line_y(following['lines'][0], x) - line_y(last['lines'][4], x) for x in xs]
        gap = float(np.median(gaps))
        # The ink of each row under the last line, along the staff (so a bent staff gives clean rows).
        profile = np.zeros(max(1, int(gap)))
        for x in range(int(x0), int(x1), 4):
            base = line_y(last['lines'][4], x)
            y0 = int(round(base))
            column = ink[y0:y0 + len(profile), x]
            profile[:len(column)] += column
        smooth = np.convolve(profile, np.ones(7) / 7, mode='same')
        start, end = int(0.5 * gap), max(int(0.5 * gap) + 1, int(0.9 * gap))
        # Two systems that stand side by side have no rows between them.
        cut = start + int(np.argmin(smooth[start:end])) if 0 <= start < min(end, len(smooth)) else max(0, int(gap / 2))
        keep_under.append((float(cut), gap))
    cuts = []
    for number, system in enumerate(systems):
        if number == 0:
            over = _reach(ink, staves[system[0]], False, OVER)
        else:
            under, gap = keep_under[number - 1]
            over = gap - under
        # Two staves that were found side by side at one height lie over each other: no room is kept between them.
        cuts.append((max(0, over) + 3, max(0, keep_under[number][0]) + 3))
    return cuts


def clean_page(grey: np.ndarray, staves: list[dict], systems: list[list[int]]) -> tuple[np.ndarray, list[dict]]:
    """(the clean page, the place of each system on it). Each place: 'top' and 'bottom' (the rows of the system on the
    clean page), 'left' (the scan's x of the clean page's column MARGIN_X), 'staves' (staff indexes), 'lines' (for each
    staff, the rows of its five lines on the clean page) and 'x' (for each staff, its first and last column there)."""
    if not systems:
        return grey.copy(), []
    cuts = _cuts(grey, staves, systems)
    strips = []
    for system, (over, under) in zip(systems, cuts):
        strips.append(_level(grey, [staves[index] for index in system], over, under))
    first_left = min(left for _, _, left in strips)
    # A system that starts further right than the first one needs its own room on the right.
    width = max(left - first_left + strip.shape[1] for strip, _, left in strips) + 2 * MARGIN_X
    height = sum(strip.shape[0] for strip, _, _ in strips) + BETWEEN * (len(strips) - 1) + 2 * MARGIN_Y
    page = np.full((height, width), 255, np.uint8)
    places = []
    y = MARGIN_Y
    for system, (strip, rows, left) in zip(systems, strips):
        x = MARGIN_X + (left - first_left)
        page[y:y + strip.shape[0], x:x + strip.shape[1]] = strip
        places.append({'top': y, 'bottom': y + strip.shape[0], 'left': left - (x - MARGIN_X), 'staves': list(system),
                       'lines': [[round(y + row, 1) for row in rows[5 * k:5 * k + 5]] for k in range(len(system))],
                       'x': [[int(x + staves[index]['left'] - left), int(x + staves[index]['right'] - left)]
                             for index in system]})
        y += strip.shape[0] + BETWEEN
    return page, places

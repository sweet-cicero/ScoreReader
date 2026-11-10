"""Finds the staves of a page image: for each staff, the height of each of its five lines along the page.

No model is used. The method:

1. Keep only long level runs of ink (a morphological opening with a wide, flat kernel). Staff lines stay; note heads,
   stems and most letters go.
2. Measure the page's staff space: the most frequent distance between neighbour lines in narrow bands of the page.
3. In vertical bands of the page, add up the line ink of each row and slide a comb of five teeth over the rows. Where
   all five teeth meet ink and the gaps between them are clean, a staff stands.
4. Link the staves of the bands across the page. The link follows the staff's own slope, so a tilted page and a page
   that bends near the binding are no problem. Pieces of one staff that a weak place separated are joined again.
5. Keep each staff line as points (x, y) with straight pieces between them.
"""
from __future__ import annotations

import cv2
import numpy as np


def ink_mask(grey: np.ndarray) -> np.ndarray:
    """1 where the page is dark. The limit is Otsu's, kept between 110 and 190."""
    limit, _ = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return (grey < min(190, max(110, limit))).astype(np.uint8)


def line_ink(ink: np.ndarray, length: int) -> np.ndarray:
    return cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (length, 1)))


def staff_space(flat: np.ndarray) -> float:
    """The page's staff space in px: the most frequent distance between neighbour lines, 0 when no staff is found."""
    height, width = flat.shape
    band = 80
    votes = np.zeros(80)
    for x0 in range(0, width - band, band):
        profile = flat[:, x0:x0 + band].sum(axis=1)
        rows = np.where(profile >= 0.5 * band)[0]
        if len(rows) < 5:
            continue
        # The middle of each run of rows is a line.
        breaks = np.where(np.diff(rows) > 1)[0]
        starts = np.concatenate([[0], breaks + 1])
        ends = np.concatenate([breaks, [len(rows) - 1]])
        centres = (rows[starts] + rows[ends]) / 2
        steps = np.diff(centres)
        # A staff gives four equal steps in a row.
        for k in range(len(steps) - 3):
            four = steps[k:k + 4]
            if 5 <= four.min() and four.max() < 80 and four.max() - four.min() <= 0.25 * four.mean() + 1:
                votes[int(round(four.mean()))] += 1
    if votes.sum() == 0:
        return 0.0
    best = int(np.argmax(np.convolve(votes, np.ones(3), mode='same')))
    near = np.arange(max(0, best - 1), min(len(votes), best + 2))
    return float((votes[near] * near).sum() / votes[near].sum())


def _band_staves(profile: np.ndarray, width: int, spaces: np.ndarray) -> list[tuple[int, float, float]]:
    """The staves in one band: (top line's row, space, strength), the strongest comb position of each staff."""
    height = len(profile)
    best = np.zeros(height)
    best_space = np.zeros(height)
    for space in spaces:
        offsets = [int(round(k * space)) for k in range(5)]
        reach = height - offsets[-1] - 1
        if reach <= 0:
            continue
        teeth = np.stack([profile[offset:offset + reach] for offset in offsets])
        weakest = teeth.min(axis=0)
        gaps = np.stack([profile[int(round((k + 0.5) * space)):int(round((k + 0.5) * space)) + reach] for k in range(4)])
        score = np.where(weakest >= 0.3 * width, teeth.sum(axis=0) - gaps.sum(axis=0), 0)
        better = score > best[:reach]
        best[:reach][better] = score[better]
        best_space[:reach][better] = space
    found: list[tuple[int, float, float]] = []
    taken: list[int] = []
    for top in np.argsort(-best):
        if best[top] <= 0:
            break
        if all(abs(top - other) > 3 * best_space[top] for other in taken):
            taken.append(int(top))
            found.append((int(top), float(best_space[top]), float(best[top])))
    return sorted(found)


def _predict(chain: list[tuple[float, float, float]], x: float) -> float:
    """The top row that the chain expects at x, from the slope of its last points."""
    if len(chain) < 2:
        return chain[-1][1]
    tail = chain[-4:]
    slope = (tail[-1][1] - tail[0][1]) / (tail[-1][0] - tail[0][0])
    return tail[-1][1] + slope * (x - tail[-1][0])


def _extend(chain: list[tuple[float, float, float]], ink: np.ndarray, band: int, step: int, direction: int) -> None:
    """Follows a staff past the end of its chain, to the left (direction -1) or to the right (1). The comb is strict
    and looks only at long runs of ink, so it loses a staff where a copy made the lines weak or broken. Here all the
    ink counts: a line is a row with much more ink than the rows half a space over and under it. Four of the five
    lines are enough, and they must stand where the staff's line of travel puts them."""
    height, width = ink.shape
    space = float(np.median([s for _, _, s in chain]))
    reach = int(max(4, round(0.3 * space)))
    half = int(round(space / 2))
    misses = 0
    while misses < 3:
        end = chain[0] if direction < 0 else chain[-1]
        x = end[0] + direction * step * (misses + 1)
        x0, x1 = int(x - band / 2), int(x + band / 2)
        if x0 < 0 or x1 > width:
            break
        if direction < 0:
            head = chain[:4]
            slope = (head[-1][1] - head[0][1]) / (head[-1][0] - head[0][0]) if len(head) > 1 else 0.0
            expected = head[0][1] + slope * (x - head[0][0])
        else:
            expected = _predict(chain, x)
        profile = ink[:, x0:x1].sum(axis=1).astype(float)
        profile = np.maximum(profile, np.roll(profile, 1))
        best = None
        for shift in range(-reach, reach + 1):
            for own in (space - 0.5, space, space + 0.5):
                rows = [int(round(expected + shift + k * own)) for k in range(5)]
                if rows[0] - half < 0 or rows[-1] + half >= height:
                    continue
                teeth = profile[rows]
                beside = np.array([(profile[row - half] + profile[row + half]) / 2 for row in rows])
                lines = (teeth >= 0.25 * band) & (teeth >= 1.4 * beside + 0.05 * band)
                key = (int(lines.sum()), float((teeth - beside).sum()))
                if best is None or key > best[0]:
                    best = (key, expected + shift, own)
        if best is not None and best[0][0] >= 4:
            point = (x, best[1], best[2])
            if direction < 0:
                chain.insert(0, point)
            else:
                chain.append(point)
            misses = 0
        else:
            misses += 1


def find_staves(grey: np.ndarray) -> list[dict]:
    """The staves from the top of the page. Each: left, right (px), space (px) and lines: five lists of [x, y]."""
    height, width = grey.shape
    ink = ink_mask(grey)
    space0 = staff_space(line_ink(ink, 25))
    if space0 <= 0:
        return []
    flat = line_ink(ink, int(max(15, round(1.4 * space0))))
    band = int(max(60, round(6 * space0)))
    step = band // 2
    spaces = np.arange(0.85 * space0, 1.2 * space0 + 0.01, 0.25)
    chains: list[list[tuple[float, float, float]]] = []  # each: (band middle x, top row, space)
    for x0 in range(0, width - band + 1, step):
        profile = flat[:, x0:x0 + band].sum(axis=1).astype(float)
        profile = np.maximum(profile, np.roll(profile, 1))  # a line two rows thick counts on both rows
        middle = x0 + band / 2
        for top, space, _ in _band_staves(profile, band, spaces):
            near = [chain for chain in chains
                    if 0 < middle - chain[-1][0] <= 4 * step and abs(_predict(chain, middle) - top) <= max(5.0, 0.3 * space)]
            if near:
                min(near, key=lambda chain: abs(_predict(chain, middle) - top)).append((middle, top, space))
            else:
                chains.append([(middle, top, space)])
    # Join the pieces of one staff: a chain that starts where another chain's line of travel arrives.
    chains.sort(key=lambda chain: chain[0][0])
    joined: list[list[tuple[float, float, float]]] = []
    for chain in chains:
        target = None
        for other in joined:
            gap = chain[0][0] - other[-1][0]
            if 0 < gap <= 14 * step and abs(_predict(other, chain[0][0]) - chain[0][1]) <= max(6.0, 0.45 * chain[0][2]):
                target = other
                break
        if target is not None:
            target.extend(chain)
        else:
            joined.append(list(chain))
    chains = [chain for chain in joined if len(chain) >= 4]
    for chain in chains:
        _extend(chain, ink, band, step, -1)
        _extend(chain, ink, band, step, 1)
    chains.sort(key=lambda chain: float(np.median([top for _, top, _ in chain])))
    staves = []
    for chain in chains:
        space = float(np.median([s for _, _, s in chain]))
        lines = []
        for k in range(5):
            points = []
            for middle, top, own_space in chain:
                guess = top + k * own_space
                y0 = int(round(guess))
                x0, x1 = int(middle - band / 2), int(middle + band / 2)
                reach = int(max(2, round(0.3 * space)))
                first_row = max(0, y0 - reach)
                window = flat[first_row:y0 + reach + 1, x0:x1].sum(axis=1).astype(float)
                if len(window) == 0 or window.max() < 0.2 * band:
                    # A weak or broken line: all the ink of the rows shows it.
                    window = ink[first_row:y0 + reach + 1, x0:x1].sum(axis=1).astype(float)
                if len(window) == 0 or window.max() < 0.2 * band:
                    points.append((middle, float(guess)))
                    continue
                weights = window * (window >= 0.6 * window.max())
                points.append((middle, first_row + float((weights * np.arange(len(window))).sum() / weights.sum())))
            lines.append(points)
        # The staff's ends: the first and last column with ink on at least three of its lines.
        first, last = int(max(0, chain[0][0] - band)), int(min(width, chain[-1][0] + band))
        columns = []
        solid = []
        for x in range(first, last):
            hits = 0
            rows = [line_y(points, x) for points in lines]
            for y in rows:
                y = int(round(y))
                hits += bool(0 <= y < height and ink[max(0, y - 2):y + 3, x].any())
            if hits < 3:
                continue
            columns.append(x)
            # Dark all the way down: a bar line when it is thin, something else when it is wide (the shadow of a
            # binding hole at the staff's end, for example).
            between = sum(bool(ink[int(round((a + b) / 2)), x]) for a, b in zip(rows, rows[1:])
                          if 0 <= int(round((a + b) / 2)) < height)
            if between >= 3:
                solid.append(x)
        wide = set()
        run: list[int] = []
        for x in solid + [10 ** 9]:
            if run and x - run[-1] > 1:
                if len(run) > 0.6 * space:
                    wide.update(run)
                run = []
            run.append(x)
        columns = [x for x in columns if x not in wide]
        if not columns:
            continue
        # Stray ink past the end does not count: the staff ends where the columns with ink stop being dense.
        columns = np.array(columns)
        dense = [x for x in columns if ((columns >= x - 40) & (columns <= x + 40)).sum() >= 40]
        if not dense:
            continue
        columns = [dense[0], dense[-1]]
        staves.append({'left': int(columns[0]), 'right': int(columns[-1]), 'space': space,
                       'lines': [[[round(x, 1), round(y, 2)] for x, y in points] for points in lines]})
    return [staff for staff in _without_twins(staves) if not _blank(ink, staff)]


def _blank(ink: np.ndarray, staff: dict) -> bool:
    """True for a staff without music: ruled lines that nobody wrote on. Measured on the test pages: a blank staff
    has other ink than its lines in 0 % of its columns, and the emptiest staff with music in 8 %."""
    space = staff['space']
    width = staff['right'] - staff['left']
    marked = 0
    looked = 0
    for x in range(int(staff['left'] + 0.03 * width), int(staff['right'] - 0.03 * width), 2):
        rows = [line_y(points, x) for points in staff['lines']]
        y0 = max(0, int(rows[0] - space))
        column = ink[y0:int(rows[4] + space), x].copy()
        for y in rows:
            at = int(round(y)) - y0
            column[max(0, at - 3):at + 4] = 0
        marked += column.sum() >= 0.3 * space
        looked += 1
    return looked > 0 and marked / looked < 0.02


def _without_twins(staves: list[dict]) -> list[dict]:
    """Drops a staff that lies over another staff (the comb can lock one line up or down): the longer one stays."""
    kept: list[dict] = []
    for staff in sorted(staves, key=lambda s: s['left'] - s['right']):
        middle = (staff['left'] + staff['right']) / 2
        top, bottom = line_y(staff['lines'][0], middle), line_y(staff['lines'][4], middle)
        twin = False
        for other in kept:
            if staff['right'] < other['left'] or staff['left'] > other['right']:
                continue
            x = min(max(middle, other['left']), other['right'])
            other_top, other_bottom = line_y(other['lines'][0], x), line_y(other['lines'][4], x)
            own_top, own_bottom = line_y(staff['lines'][0], x), line_y(staff['lines'][4], x)
            overlap = min(own_bottom, other_bottom) - max(own_top, other_top)
            if overlap > 0.5 * (bottom - top):
                twin = True
                break
        if not twin:
            kept.append(staff)
    return sorted(kept, key=lambda s: line_y(s['lines'][0], (s['left'] + s['right']) / 2))


def line_y(points: list, x: float) -> float:
    """The height of a staff line at x: straight pieces between the points, and the end pieces go on straight."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if len(xs) > 1 and x <= xs[0]:
        return ys[0] + (ys[1] - ys[0]) * (x - xs[0]) / (xs[1] - xs[0])
    if len(xs) > 1 and x >= xs[-1]:
        return ys[-1] + (ys[-1] - ys[-2]) * (x - xs[-1]) / (xs[-1] - xs[-2])
    return float(np.interp(x, xs, ys))


def draw(grey: np.ndarray, staves: list[dict]) -> np.ndarray:
    """The page in colour with each staff line drawn in red and each staff's number at its left."""
    colour = cv2.cvtColor(grey, cv2.COLOR_GRAY2BGR)
    for number, staff in enumerate(staves, 1):
        for points in staff['lines']:
            for x in range(staff['left'], staff['right']):
                y = int(round(line_y(points, x)))
                if 0 <= y < colour.shape[0]:
                    colour[max(0, y - 1):y + 2, x] = (0, 0, 255)
        y = int(line_y(staff['lines'][4], staff['left']))
        cv2.putText(colour, str(number), (max(0, staff['left'] - 130), y), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 8)
    return colour

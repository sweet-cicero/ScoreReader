#!/usr/bin/env python3
"""Finds the staves of a page image: for each staff, the height of each of its five lines along the page.

usage: staves.py page.png out.json [debug.png]

Method: keep only long horizontal runs of ink (an opening with a wide, flat kernel). In vertical bands of the page,
add up that ink in each row, and slide a comb of five teeth over the rows: where all five teeth meet ink, a staff
stands. The staves of the bands are linked across the page, also where the page bends near the binding, and each
staff line is kept as points (x, y) with straight pieces between them. A short last staff and beams between the
lines are no problem.
"""
import json
import sys

import cv2
import numpy as np

BAND = 200
STEP = 100


def band_staves(profile, width, spaces):
    """The staves in one band: (top line's row, space, strength), the strongest comb position of each staff."""
    height = len(profile)
    best = np.zeros(height)
    best_space = np.zeros(height)
    for space in spaces:
        offsets = [int(round(k * space)) for k in range(5)]
        reach = height - offsets[-1]
        teeth = np.stack([profile[offset:offset + reach] for offset in offsets])
        weakest = teeth.min(axis=0)
        gaps = np.stack([profile[int(round((k + 0.5) * space)):int(round((k + 0.5) * space)) + reach] for k in range(4)])
        score = np.where(weakest >= 0.3 * width, teeth.sum(axis=0) - gaps.sum(axis=0), 0)
        better = score > best[:reach]
        best[:reach][better] = score[better]
        best_space[:reach][better] = space
    found = []
    order = np.argsort(-best)
    taken = []
    for top in order:
        if best[top] <= 0:
            break
        if all(abs(top - other) > 3 * best_space[top] for other in taken):
            taken.append(int(top))
            found.append((int(top), float(best_space[top]), float(best[top])))
    return sorted(found)


def find_staves(grey):
    height, width = grey.shape
    ink = (grey < 128).astype(np.uint8)
    flat = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (41, 1)))
    spaces = np.arange(18.0, 40.0, 0.25)
    chains = []  # each: list of (band middle x, top row, space)
    for x0 in range(0, width - BAND + 1, STEP):
        profile = flat[:, x0:x0 + BAND].sum(axis=1).astype(float)
        profile = np.maximum(profile, np.roll(profile, 1))  # a line two rows thick counts on both rows
        middle = x0 + BAND / 2
        for top, space, _ in band_staves(profile, BAND, spaces):
            near = [chain for chain in chains if abs(chain[-1][1] - top) <= 10 and 0 < middle - chain[-1][0] <= 3 * STEP]
            if near:
                min(near, key=lambda chain: abs(chain[-1][1] - top)).append((middle, top, space))
            else:
                chains.append([(middle, top, space)])
    chains = [chain for chain in chains if len(chain) >= 4]
    chains.sort(key=lambda chain: np.mean([top for _, top, _ in chain]))
    out = []
    for chain in chains:
        space = float(np.median([s for _, _, s in chain]))
        lines = []
        for k in range(5):
            points = []
            for middle, top, own_space in chain:
                y0 = int(round(top + k * own_space))
                x0, x1 = int(middle - BAND / 2), int(middle + BAND / 2)
                reach = int(round(0.35 * space))
                window = flat[y0 - reach:y0 + reach + 1, x0:x1].sum(axis=1).astype(float)
                if window.max() < 0.2 * BAND:
                    continue
                weights = window * (window >= 0.5 * window.max())
                points.append((middle, y0 - reach + float((weights * np.arange(len(window))).sum() / weights.sum())))
            lines.append(points)
        # The staff's left and right ends: the first and last column with flat ink on at least three of its lines.
        first, last = chain[0][0] - BAND / 2, chain[-1][0] + BAND / 2
        columns = []
        for x in range(int(first), int(last)):
            hits = 0
            for points in lines:
                y = int(round(np.interp(x, [p[0] for p in points], [p[1] for p in points])))
                hits += bool(flat[max(0, y - 2):y + 3, x].any())
            if hits >= 3:
                columns.append(x)
        out.append({'left': columns[0], 'right': columns[-1], 'space': space,
                    'lines': [[[round(x, 1), round(y, 2)] for x, y in points] for points in lines]})
    return out


def line_y(points, x):
    """The height of a staff line at x: straight pieces between the points, and the end pieces go on straight."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if x <= xs[0] and len(xs) > 1:
        return ys[0] + (ys[1] - ys[0]) * (x - xs[0]) / (xs[1] - xs[0])
    if x >= xs[-1] and len(xs) > 1:
        return ys[-1] + (ys[-1] - ys[-2]) * (x - xs[-1]) / (xs[-1] - xs[-2])
    return float(np.interp(x, xs, ys))


def main():
    grey = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    staves = find_staves(grey)
    with open(sys.argv[2], 'w') as file:
        json.dump({'width': grey.shape[1], 'height': grey.shape[0], 'staves': staves}, file)
    for staff in staves:
        ends = [staff['left'], (staff['left'] + staff['right']) / 2, staff['right']]
        print(f"x {staff['left']}-{staff['right']}, space {staff['space']:.2f}; top line at left/middle/right: "
              + ' '.join(f'{line_y(staff["lines"][0], x):.0f}' for x in ends)
              + '; bottom line: ' + ' '.join(f'{line_y(staff["lines"][4], x):.0f}' for x in ends))
    if len(sys.argv) > 3:
        colour = cv2.cvtColor(grey, cv2.COLOR_GRAY2BGR)
        for staff in staves:
            for points in staff['lines']:
                for x in range(staff['left'], staff['right']):
                    y = int(round(line_y(points, x)))
                    colour[y, x] = (0, 0, 255)
        cv2.imwrite(sys.argv[3], colour)


if __name__ == '__main__':
    main()

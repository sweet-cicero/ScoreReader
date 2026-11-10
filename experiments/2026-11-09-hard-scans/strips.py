#!/usr/bin/env python3
"""Cuts a page into one image for each staff, with the options that the experiments compare.

usage: strips.py page.png staves.json out_folder stem [--straight] [--space N] [--lines] [--pad N] [--stack]

Without --straight, each strip is a plain cut of the page. With --straight, each column of the strip is moved and
stretched so that the five staff lines become level and evenly spaced (the page bends near the binding). --space sets
the distance between staff lines in the output (the source's own distance when not given). --lines draws the five
staff lines again in black. --stack puts the strips into one page image instead of one image for each staff.
A strip ends at the emptiest row between the words under its staff and the staff below, so the words stay with it.
The strips are written as <stem>.mvt<N>.png, so score.py reads the readers' outputs one after another.
"""
import argparse
import json
import os

import cv2
import numpy as np

from staves import line_y


def straighten(grey, staff, above, below, space_out=None):
    """The staff as a level strip: (image, row of the top line, output px per source px). above and below are the
    source px kept over the top line and under the bottom line."""
    left, right = staff['left'], staff['right']
    space = staff['space']
    out_space = space_out or space
    scale = out_space / space
    x0, x1 = max(0, left - 20), min(grey.shape[1], right + 20)
    rows_above = int(round(above * scale))
    rows = rows_above + int(round(4 * out_space)) + int(round(below * scale))
    columns = int(round((x1 - x0) * scale))
    map_x = np.zeros((rows, columns), np.float32)
    map_y = np.zeros((rows, columns), np.float32)
    targets = [rows_above + k * out_space for k in range(5)]
    row = np.arange(rows, dtype=np.float32)
    for column in range(columns):
        x = x0 + column / scale
        x_in = min(max(x, left), right)
        sources = [line_y(staff['lines'][k], x_in) for k in range(5)]
        local = (sources[4] - sources[0]) / (4 * out_space)  # source px per output px in this column
        y = np.interp(row, targets, sources)
        y = np.where(row < targets[0], sources[0] + (row - targets[0]) * local, y)
        y = np.where(row > targets[4], sources[4] + (row - targets[4]) * local, y)
        map_y[:, column] = y
        map_x[:, column] = x
    strip = cv2.remap(grey, map_x, map_y, cv2.INTER_CUBIC if scale >= 1 else cv2.INTER_AREA,
                      borderMode=cv2.BORDER_CONSTANT, borderValue=255)
    return strip, rows_above, scale, x0


def gaps_of(grey, staves):
    """For each staff, the source px to keep over its top line and under its bottom line."""
    cuts = []  # under each staff: px from its bottom line to the emptiest row before the next staff
    for index, staff in enumerate(staves):
        space = staff['space']
        middle_x = (staff['left'] + staff['right']) / 2
        if index + 1 < len(staves):
            gap = line_y(staves[index + 1]['lines'][0], middle_x) - line_y(staff['lines'][4], middle_x)
            strip, rows_above, _, _ = straighten(grey, staff, 0, gap)
            ink = (strip < 128).sum(axis=1)
            start = int(4 * space + 0.5 * gap)
            end = int(4 * space + 0.9 * gap)
            smooth = np.convolve(ink, np.ones(7) / 7, mode='same')
            cut = start + int(np.argmin(smooth[start:end])) - int(round(4 * space))
            cuts.append((cut, gap))
        else:
            cuts.append((6.5 * space, None))
    out = []
    for index, staff in enumerate(staves):
        if index == 0:
            above = 5.0 * staff['space']
        else:
            cut, gap = cuts[index - 1]
            above = gap - cut + 4
        out.append((above, cuts[index][0] + 4))
    return out


def strip_of(grey, staves, index, keep, straight, space_out, redraw, pad):
    staff = staves[index]
    above, below = keep[index]
    left, right = staff['left'], staff['right']
    if straight:
        strip, rows_above, scale, x0 = straighten(grey, staff, above, below, space_out)
        if redraw:
            out_space = space_out or staff['space']
            thick = max(2, int(round(out_space / 9)))
            first, last = int(round((left - x0) * scale)), int(round((right - x0) * scale))
            for k in range(5):
                y = int(round(rows_above + k * out_space))
                strip[y - thick // 2:y - thick // 2 + thick, first:last + 1] = 0
    else:
        x0, x1 = max(0, left - 20), min(grey.shape[1], right + 20)
        tops = [line_y(staff['lines'][0], x) for x in (left, right)]
        bottoms = [line_y(staff['lines'][4], x) for x in (left, right)]
        y0 = int(max(0, min(tops) - above))
        y1 = int(min(grey.shape[0], max(bottoms) + below))
        strip = grey[y0:y1, x0:x1].copy()
        if redraw:
            for k in range(5):
                for x in range(left, right + 1):
                    y = int(round(line_y(staff['lines'][k], x))) - y0
                    strip[y - 1:y + 2, x - x0] = 0
    if pad:
        strip = cv2.copyMakeBorder(strip, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
    return strip


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('staves')
    parser.add_argument('out')
    parser.add_argument('stem')
    parser.add_argument('--straight', action='store_true')
    parser.add_argument('--space', type=float, default=None)
    parser.add_argument('--lines', action='store_true')
    parser.add_argument('--pad', type=int, default=40)
    parser.add_argument('--stack', action='store_true')
    args = parser.parse_args()
    grey = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
    with open(args.staves) as file:
        staves = json.load(file)['staves']
    os.makedirs(args.out, exist_ok=True)
    keep = gaps_of(grey, staves)
    strips = [strip_of(grey, staves, index, keep, args.straight, args.space, args.lines, 0 if args.stack else args.pad)
              for index in range(len(staves))]
    if args.stack:
        width = max(strip.shape[1] for strip in strips) + 2 * 150
        gap = 60
        height = sum(strip.shape[0] for strip in strips) + gap * (len(strips) - 1) + 2 * 200
        page = np.full((height, width), 255, np.uint8)
        y = 200
        for strip in strips:
            page[y:y + strip.shape[0], 150:150 + strip.shape[1]] = strip
            y += strip.shape[0] + gap
        cv2.imwrite(os.path.join(args.out, f'{args.stem}.png'), page)
    else:
        for number, strip in enumerate(strips, 1):
            cv2.imwrite(os.path.join(args.out, f'{args.stem}.mvt{number}.png'), strip)
    print(len(strips), 'strips:', ', '.join(f'{strip.shape[1]}x{strip.shape[0]}' for strip in strips))


if __name__ == '__main__':
    main()

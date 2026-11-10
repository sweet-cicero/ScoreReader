#!/usr/bin/env python3
"""Makes every staff of a page level, and keeps the page's layout: flatten.py page.png staves.json out.png

Each staff line is moved to its mean height, column by column. Between two staves the move changes evenly from the
one staff's to the other's, so the words and signs between the staves move with the nearer staff.
"""
import json
import sys

import cv2
import numpy as np

from staves import line_y


def flatten(grey, staves):
    height, width = grey.shape
    # Anchors: for each staff line, its target row (its mean height) and its source row in each column.
    anchors = []
    for staff in staves:
        xs = np.arange(staff['left'], staff['right'] + 1)
        for points in staff['lines']:
            ys = np.array([line_y(points, x) for x in xs])
            anchors.append((float(ys.mean()), staff['left'], staff['right'], ys))
    anchors.sort(key=lambda anchor: anchor[0])
    targets = np.array([anchor[0] for anchor in anchors])
    map_x = np.tile(np.arange(width, dtype=np.float32), (height, 1))
    map_y = np.zeros((height, width), np.float32)
    rows = np.arange(height, dtype=np.float32)
    for x in range(width):
        # The move of each staff line in this column; a column left or right of a staff uses the staff's end.
        moves = np.array([ys[min(max(x, left), right) - left] - target for target, left, right, ys in anchors])
        map_y[:, x] = rows + np.interp(rows, targets, moves)
    return cv2.remap(grey, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=255)


def main():
    grey = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    with open(sys.argv[2]) as file:
        staves = json.load(file)['staves']
    cv2.imwrite(sys.argv[3], flatten(grey, staves))


if __name__ == '__main__':
    main()

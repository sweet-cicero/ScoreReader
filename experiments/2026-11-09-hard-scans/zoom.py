#!/usr/bin/env python3
"""Cuts enlarged pieces of the stacked page: zoom.py out.png staff:x0:x1 [staff:x0:x1 ...]   (staff from 1)"""
import json
import sys

import cv2
import numpy as np

image = cv2.imread('in/straight-page/saturday-of-souls-troparion-p1.png', cv2.IMREAD_GRAYSCALE)
notes = json.load(open('results/cop-straight-page-ledger/saturday-of-souls-troparion-p1.notes.json'))['notes']
tiles = []
for spec in sys.argv[2:]:
    staff, x0, x1 = (int(v) for v in spec.split(':'))
    note = next(n for n in notes if n['staff'] == staff - 1)
    top, bottom = int(note['staff_y0'] - 3.2 * note['sp']), int(note['staff_y1'] + 3.6 * note['sp'])
    tile = cv2.resize(image[top:bottom, x0:x1], None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    tiles.append(tile)
height = max(tile.shape[0] for tile in tiles)
sheet = np.full((height, sum(tile.shape[1] + 30 for tile in tiles)), 255, np.uint8)
x = 0
for tile in tiles:
    sheet[:tile.shape[0], x:x + tile.shape[1]] = tile
    x += tile.shape[1] + 30
cv2.imwrite(sys.argv[1], sheet)
print(sheet.shape)

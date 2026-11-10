#!/usr/bin/env python3
"""Checks the staff finder on the test pages: bench/staves_check.py <pages folder> [out folder for pictures]
The expected numbers come from a look at each page (bench/staves_expected.json)."""
import json
import os
import sys
import time

import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from scoreread.staves import draw, find_staves, line_y  # noqa: E402

expected = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'staves_expected.json')))
pages, out = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
wrong = 0
start = time.time()
for name, want in sorted(expected.items()):
    grey = cv2.imread(os.path.join(pages, name + '.png'), cv2.IMREAD_GRAYSCALE)
    staves = find_staves(grey)
    widths = [staff['right'] - staff['left'] for staff in staves]
    short = [k + 1 for k, w in enumerate(widths) if w < 0.6 * max(widths)] if widths else []
    ok = len(staves) == want
    wrong += not ok
    space = staves[0]['space'] if staves else 0
    print(f"{'ok ' if ok else 'BAD'} {name}: {len(staves)} staves (expected {want}), space {space:.1f}"
          + (f', short staves: {short}' if short else ''))
    if out:
        os.makedirs(out, exist_ok=True)
        cv2.imwrite(os.path.join(out, name + '.png'), cv2.resize(draw(grey, staves), None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA))
print(f'{len(expected) - wrong} of {len(expected)} pages right, {time.time() - start:.0f} s')

#!/usr/bin/env python3
"""Checks the systems finder on the test pages: bench/systems_check.py <kit folder>
The expected number of staves in each system comes from the kit's cases.json."""
import json
import os
import sys

import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from scoreread.staves import find_staves, ink_mask  # noqa: E402
from scoreread.systems import find_systems, joined  # noqa: E402

kit = sys.argv[1]
wrong = 0
pages = 0
for case in json.load(open(os.path.join(kit, 'cases.json')))['cases']:
    for page in case['pages']:
        name = f"{case['id']}-p{page}"
        grey = cv2.imread(os.path.join(kit, 'pages', name + '.png'), cv2.IMREAD_GRAYSCALE)
        staves = find_staves(grey)
        systems = find_systems(grey, staves)
        sizes = [len(system) for system in systems]
        want = len(case['layout'])
        ok = all(size == want for size in sizes)
        pages += 1
        wrong += not ok
        if not ok or '-v' in sys.argv:
            ink = ink_mask(grey).astype(bool)
            links = [joined(ink, staves[k], staves[k + 1]) for k in range(len(staves) - 1)]
            print(f"{'ok ' if ok else 'BAD'} {name}: systems {sizes}, expected {want} in each; links: "
                  + ' '.join(f"{link['opening']:.2f}/{link['bars']}/{link['aligned']}" for link in links))
print(f'{pages - wrong} of {pages} pages right')

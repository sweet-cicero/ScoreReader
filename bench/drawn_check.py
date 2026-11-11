#!/usr/bin/env python3
"""Checks the whole reader on a page that this script draws: bench/drawn_check.py [out folder for the pictures]

The page has one system of two staves with quarter, half, dotted and beamed eighth notes, bar lines and a tie. It
needs no test kit, so it runs anywhere. It is a check that the steps work together, not a measure of hard pages: for that,
see bench/kit.sh."""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from scoreread.layers import picture  # noqa: E402
from scoreread.page import clean_page  # noqa: E402
from scoreread.reader import read_page  # noqa: E402
from scoreread.staves import find_staves  # noqa: E402
from scoreread.systems import find_systems, lost_staves  # noqa: E402

# For each staff, its symbols from the left: (place, kind). Place 0 is the middle line and +1 one step up.
# Kinds: 'q' quarter, 'h' half, 'q.' dotted quarter, 'e' eighth (two in a row are beamed), '|' bar line; 'h~' is a
# half note with a tie to the next note.
MUSIC = [[(-2, 'q'), (-1, 'q'), (0, 'h'), (0, '|'), (1, 'e'), (2, 'e'), (3, 'q'), (-3, 'h~'), (0, '|'), (-3, 'q')],
         [(2, 'q'), (1, 'q'), (-4, 'h'), (0, '|'), (-1, 'q.'), (-2, 'e'), (-3, 'e'), (4, 'h'), (0, '|'), (2, 'q')]]
LENGTHS = {'q': 1.0, 'h': 2.0, 'h~': 2.0, 'q.': 1.5, 'e': 0.5}
NAMES = [{-4: 'E4', -3: 'F4', -2: 'G4', -1: 'A4', 0: 'B4', 1: 'C5', 2: 'D5', 3: 'E5', 4: 'F5'},     # treble clef
         {-4: 'G2', -3: 'A2', -2: 'B2', -1: 'C3', 0: 'D3', 1: 'E3', 2: 'F3', 3: 'G3', 4: 'A3'}]     # bass clef


def draw(space: int = 20) -> np.ndarray:
    """The page as a grey image. `space` is the distance of two staff lines in pixels."""
    width, top = 1800, 300
    image = np.full((2 * top + 16 * space, width), 255, np.uint8)
    left, right = 150, width - 150
    for number, symbols in enumerate(MUSIC):
        middle = top + number * 12 * space + 2 * space
        for line in range(-2, 3):
            cv2.line(image, (left, middle + line * space), (right, middle + line * space), 0, 2)
        x = left + 8 * space
        stems = []        # the stems of the eighth notes: (x, end, direction)
        tied = None       # the head that a tie begins at: (x, y)
        for place, kind in symbols:
            if kind == '|':
                cv2.line(image, (x, middle - 2 * space), (x, middle + 2 * space), 0, 3)
                x += 2 * space
                continue
            y = int(round(middle - place * space / 2))
            cv2.ellipse(image, (x, y), (int(0.62 * space), int(0.42 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)
            if kind in ('h', 'h~'):
                cv2.ellipse(image, (x, y), (int(0.42 * space), int(0.2 * space)), -20, 0, 360, 255, -1, cv2.LINE_AA)
            if tied:          # the bow of the tie, under the two heads
                cv2.ellipse(image, ((tied[0] + x) // 2, y + int(0.6 * space)), ((x - tied[0]) // 2 - int(0.9 * space), int(0.6 * space)),
                            0, 0, 180, 0, 2, cv2.LINE_AA)
            tied = (x, y) if kind == 'h~' else None
            if kind == 'q.':
                cv2.circle(image, (x + int(1.2 * space), y - (space // 2 if place % 2 == 0 else 0)), int(0.16 * space), 0, -1, cv2.LINE_AA)
            up = place < 0
            stem = x + int(0.56 * space) if up else x - int(0.56 * space)
            end = y - int(3.4 * space) if up else y + int(3.4 * space)
            if kind == 'e':
                stems.append((stem, end, up))
                if len(stems) == 2:       # one level beam at the further end of the two stems
                    level = min(stems[0][1], stems[1][1]) if up else max(stems[0][1], stems[1][1])
                    for at, _, _ in stems:
                        cv2.line(image, (at, y if at == stem else level), (at, level), 0, 2)
                    cv2.rectangle(image, (stems[0][0], level - (0 if up else space // 2)), (stems[1][0], level + (space // 2 if up else 0)), 0, -1)
                    end = level
                    stems = []
            cv2.line(image, (stem, y), (stem, end), 0, 2)
            x += 4 * space
    # The opening line and the closing line make the two staves one system.
    for x in (left, right):
        cv2.line(image, (x, top), (x, top + 16 * space), 0, 3)
    return image


def main() -> int:
    grey = draw()
    staves = find_staves(grey)
    systems = find_systems(grey, staves)
    staves, systems = lost_staves(grey, staves, systems)
    page, places = clean_page(grey, staves, systems)
    result = read_page(page, places)
    if len(sys.argv) > 1:
        os.makedirs(sys.argv[1], exist_ok=True)
        cv2.imwrite(os.path.join(sys.argv[1], 'drawn.png'), grey)
        cv2.imwrite(os.path.join(sys.argv[1], 'drawn.layers.png'), picture(result['layers']))
    wrong = 0
    for number, symbols in enumerate(MUSIC):
        want = [(NAMES[number][place], LENGTHS[kind]) for place, kind in symbols if kind != '|']
        read = [(f"{note['step']}{note['octave']}", note['length'])
                for note in sorted((note for note in result['notes'] if note['staff'] == number), key=lambda note: note['x'])]
        ok = want == read
        wrong += not ok
        print(f"{'ok ' if ok else 'BAD'} staff {number + 1}: read {' '.join(f'{name}:{length:g}' for name, length in read)}")
        if not ok:
            print(f"    drawn          {' '.join(f'{name}:{length:g}' for name, length in want)}")
    want = sum(kind.endswith('~') for symbols in MUSIC for _, kind in symbols)
    ties = [(first['staff'], f"{NAMES[first['staff']][round(first['place'])]}") for first, _ in result['ties']]
    wrong += len(ties) != want
    print(f"{'ok ' if len(ties) == want else 'BAD'} ties: read {ties} (drawn {want})")
    systems_ok = [len(system) for system in systems] == [2]
    print(f"{'ok ' if systems_ok else 'BAD'} systems: {[len(system) for system in systems]} (drawn [2]), clefs {result['clefs']}")
    # The words: a line of text as Tesseract gives it is cut into syllables (no Tesseract is needed for this check).
    from scoreread.ocr import _syllables, _words_row
    line = [('Glo', 0, 30, 92), ('-', 32, 40, 90), ('ry', 42, 60, 88), ('to', 70, 90, 95), ('Thee,', 100, 150, 92),
            ('our-', 160, 200, 90), ('God__', 210, 280, 80), ('|', 290, 292, 90), ('mer-cy', 300, 360, 91), ('>', 370, 380, 64)]
    cut = [(syllable['text'], syllable['join']) for syllable in _syllables(line)]
    want = [('Glo', True), ('ry', False), ('to', False), ('Thee,', False), ('our', True), ('God', False), ('mer', True), ('cy', False)]
    words_ok = cut == want and _words_row(line) and not _words_row([('lL', 0, 9, 0), ('te', 10, 20, 21), ('J!', 30, 40, 52)])
    print(f"{'ok ' if words_ok else 'BAD'} words: a line of text cut into {len(cut)} syllables (wanted {len(want)})")
    # The systems: verses on single staves around a refrain that is drawn as a system of two (measured links).
    from scoreread.systems import group_staves, weigh

    def links(rows):
        out = [{'opening': opening, 'bars': bars, 'aligned': aligned, 'step': step} for opening, bars, aligned, step in rows]
        for link in out:
            link['weight'] = weigh(link)
            link['same'] = link['weight'] > 0
        return out
    verses = links([(0.01, 0, 0.67, 0.72), (0.12, 0, 0.0, 0.01), (1.0, 6, None, 0.68), (0.16, 0, None, 0.12), (0.0, 0, 0.0, -0.2), (0.18, 0, 0.2, -0.1)])
    cut_off = links([(0.1, 0, None, 0.85), (0.17, 0, None, 0.04), (1.0, 0, None, 0.76), (0.12, 0, None, 0.16), (0.9, 0, None, 0.78), (0.12, 0, None, 0.21), (1.0, 3, None, 0.83)])
    sizes = [[len(system) for system in group_staves(verses, 7)], [len(system) for system in group_staves(cut_off, 8)]]
    lone_ok = sizes == [[1, 1, 2, 1, 1, 1], [2, 2, 2, 2]]
    print(f"{'ok ' if lone_ok else 'BAD'} systems from links: {sizes} (wanted [[1, 1, 2, 1, 1, 1], [2, 2, 2, 2]])")
    return 1 if wrong or not systems_ok or not words_ok or not lone_ok else 0


if __name__ == '__main__':
    sys.exit(main())

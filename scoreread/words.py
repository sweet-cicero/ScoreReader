"""Finds the rows of the words between the staves, and ends the stems that run into them. No model is used.

The words of a hymn stand in rows over or under a staff. A letter is a small piece of ink that touches nothing else,
and the letters of a row stand side by side, so a row of the page that crosses many small pieces is a row of words,
however few the words are. A stem, a ledger line and a head beside the staff are larger or flatter, or stand alone.

A copyist who has little room draws a stem down to the words, or up to them. The stem then seems to go on into a
letter, and the strokes of that letter hang at its end like a flag. A stem ends where the band of the words begins.
"""
from __future__ import annotations

import cv2
import numpy as np

WORDS = True               # the bands of the words are looked for
LETTERS = (0.35, 1.8, 6.0, 5.0)   # a letter (or a word of joined letters) is a free piece of ink from this to this many
#                                   staff spaces high, at most this wide, and at most this many times as wide as high
LINE = (8, 0.3, 0.6, 2.4)  # a band of words: a row that crosses at least this many letters; the band goes on while its
#                            rows cross this share of them (and two at least); from this to this many staff spaces high
WORDS_FAR = 9.0            # the words stand at most this many staff spaces over the first staff or under the last
STEM_MID = True            # the stem's column is that of its middle when its far end lies in a letter beside it
WORDS_NEAR = 0.3           # a stem's end this many staff spaces before the band lies in the band (a letter's top)


def _gaps(layers: dict) -> list[tuple]:
    """The room for words: over the first staff, between two staves, under the last. (top row, bottom row, the staff
    over it, the staff under it) each."""
    space = layers['space']
    staves = sorted(layers['staves'], key=lambda staff: staff['rows'][0])
    if not staves:
        return []
    height = layers['bare'].shape[0]
    first, last = staves[0], staves[-1]
    gaps = [(max(0, int(first['rows'][0] - WORDS_FAR * space)), int(first['rows'][0] - 0.5 * space), first, first)]
    for upper, lower in zip(staves, staves[1:]):
        gaps.append((int(upper['rows'][4] + 0.5 * space), int(lower['rows'][0] - 0.5 * space), upper, lower))
    gaps.append((int(last['rows'][4] + 0.5 * space), min(height, int(last['rows'][4] + WORDS_FAR * space)), last, last))
    return [gap for gap in gaps if gap[1] - gap[0] >= 1.5 * space]


def word_bands(layers: dict) -> list[dict]:
    """The bands of the words of a page, from their letters: {'top', 'bottom' (rows), 'x0', 'x1' (columns)} each.

    A letter is a small piece of ink that touches nothing else, and the letters of a row of words stand side by
    side: a row of the page that crosses many of them is a row of words, however few the words are. A stem, a note
    beside the staff and a ledger line are larger, flatter or stand alone."""
    if not WORDS:
        return []
    bare, space = layers['bare'], layers['space']
    count, _, stats, _ = cv2.connectedComponentsWithStats(bare.astype(np.uint8), connectivity=8)
    low, high, wide, flat = LETTERS
    letters = [(int(x), int(y), int(w), int(h)) for x, y, w, h, _ in stats[1:count]
               if low * space <= h <= high * space and w <= wide * space and w <= flat * h]
    bands = []
    for top, bottom, upper, lower in _gaps(layers):
        cover = np.zeros(bottom - top, dtype=int)
        for x, y, w, h in letters:
            if y >= top and y + h <= bottom:
                cover[y - top:y + h - top] += 1
        while True:
            peak = int(cover.argmax())
            if cover[peak] < LINE[0]:
                break
            floor = max(2, LINE[1] * cover[peak])
            first = last = peak
            while first > 0 and cover[first - 1] >= floor:
                first -= 1
            while last + 1 < len(cover) and cover[last + 1] >= floor:
                last += 1
            if LINE[2] * space <= last - first + 1 <= LINE[3] * space:
                bands.append({'top': top + first, 'bottom': top + last,
                              'x0': int(min(upper['x0'], lower['x0'])), 'x1': int(max(upper['x1'], lower['x1']))})
            edge = int(0.3 * space)
            cover[max(0, first - edge):last + edge + 1] = 0
    return sorted(bands, key=lambda band: band['top'])


def cut_stems(layers: dict, heads: list[dict], bands: list[dict]) -> int:
    """Ends each stem that runs into a band of words where the band begins: its 'end' is the last row of its own ink
    before the band, and stem['words'] holds the band's rows, so that nothing in the band counts as its flag.
    stem['full'] keeps the end that was found first (see scoreread.symbols.WORD_BEAMS). Returns how many stems were
    cut."""
    if not bands:
        return 0
    bare, space = layers['bare'], layers['space']
    near = WORDS_NEAR * space
    cut = 0
    for head in heads:
        for stem in head['stems']:
            down = stem['direction'] == 'down'
            for band in bands:
                if not band['x0'] <= stem['x'] <= band['x1']:
                    continue
                # The head stands outside the band, and the stem's end lies in it or at its edge.
                if band['top'] - near <= head['cy'] <= band['bottom'] + near:
                    continue
                if down and not (head['cy'] < band['top'] and band['top'] - near <= stem['end'] <= band['bottom'] + space):
                    continue
                if not down and not (head['cy'] > band['bottom'] and band['top'] - space <= stem['end'] <= band['bottom'] + near):
                    continue
                edge = int(band['top'] - 1) if down else int(band['bottom'] + 1)
                # The stem's own ink ends at the band or before it: the last inked row on the way from the head.
                limit = int(head['cy'])
                row = limit
                for column in ([int(round(stem['x'])), int(stem['mid'])] if STEM_MID and 'mid' in stem else [int(round(stem['x']))]):
                    strip = bare[:, max(0, column - 2):column + 3].any(axis=1)
                    reach = edge
                    while (reach > limit if down else reach < limit) and not strip[reach]:
                        reach += -1 if down else 1
                    # The far end of the way can lie in a letter, beside the stem: the stem's own column reaches the band.
                    if (reach > row) if down else (reach < row) or row == limit:
                        if column != int(round(stem['x'])) and reach != row:
                            stem['x'] = column
                        row = reach
                # A head that stands right over the words has no stem left; its stem still ends there.
                stem['full'] = stem['end']
                stem['end'] = row
                stem['words'] = (band['top'], band['bottom'])
                cut += 1
                break
    return cut

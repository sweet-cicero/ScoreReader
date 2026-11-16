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
STAGGER = (5, 0.12, 0.6, 0.3, 1.0)   # rows of words that stand staggered (a refrain beside the rows of the verses) give a
#                            stretch that is too high for one row: it is parted by the lines that its letters stand on.
#                            A row: this many letters or more whose feet lie within this many staff spaces of one line;
#                            two rows are this far apart at least; the row reaches this far under its line (the tails of
#                            g and y) and this far past its first and its last letter (None: such a stretch is dropped)
BESIDE = True              # a row of such a stretch that stands beside the first row under the staff, with no letter
#                            over or under a letter of it, goes on that row: the refrain that every verse sings is
#                            printed once, at the middle of the rows of the verses (band['with']: the number of the first row)
SPARSE = 4                 # a stretch between two staves, or under the last, with no band: a row that crosses this many
#                            letters or more is a row of few words all the same (a word that is held over a long
#                            melody: 'A - men', 'Al - le - lu - i - a'), for the step that reads the words only
#                            (band['few']: every word of its reading must be a word of the list). None: off
WORDS_FAR = 9.0            # the words stand at most this many staff spaces over the first staff or under the last
STEM_MID = True            # the stem's column is that of its middle when its far end lies in a letter beside it
WORDS_NEAR = 0.3           # a stem's end this many staff spaces before the band lies in the band (a letter's top)
STEM_GAP = (0.25, 1.2)     # a letter in a stem's column, outside the band: the stem ends where the paper begins, when
#                            this many staff spaces of paper lie in its column, at most this far before the band (None: off)


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


def _staggered(letters: list[tuple], space: float, left: int, right: int) -> list[dict]:
    """The rows of words in a stretch that is too high for one row (see STAGGER): each row is the line that many of
    the letters stand on. A row is as wide as its own letters, so that it shows nothing of the rows beside it."""
    least, near, apart, under, past = STAGGER
    feet = np.array([y + h for _, y, _, h in letters])
    free = np.ones(len(letters), dtype=bool)
    lines: list[int] = []
    rows = []
    while free.any():
        counts = {int(foot): int((free & (np.abs(feet - foot) <= near * space)).sum()) for foot in set(feet[free].tolist())}
        counts = {foot: count for foot, count in counts.items() if all(abs(foot - line) >= apart * space for line in lines)}
        if not counts:
            break
        line = max(counts, key=lambda foot: (counts[foot], -foot))
        if counts[line] < least:
            break
        lines.append(line)
        members = free & (np.abs(feet - line) <= near * space)
        free &= ~members
        boxes = [letters[index] for index in np.flatnonzero(members)]
        head = min(y for _, y, _, _ in boxes)
        if LINE[2] * space <= line + under * space - head <= LINE[3] * space:
            rows.append({'top': int(head), 'bottom': int(line + under * space),
                         'x0': max(left, int(min(x for x, _, _, _ in boxes) - past * space)),
                         'x1': min(right, int(max(x + w for x, _, w, _ in boxes) + past * space)), 'own': True})
    return rows


def word_rows(layers: dict) -> list[dict]:
    """The rows of the words of a page for the step that reads the words: the bands of word_bands(), and with them
    the rows of a stretch where the rows stand staggered (STAGGER; 'own': True) and the row that each such row
    goes on ('with', see BESIDE), and the row of few words of a stretch with no band ('few': True, see SPARSE). The
    notes are read with the bands alone, as they were."""
    return word_bands(layers, True)


def word_bands(layers: dict, staggered: bool = False) -> list[dict]:
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
        high_stretch = False
        whole = cover.copy()
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
            elif last - first + 1 > LINE[3] * space:
                high_stretch = True
            edge = int(0.3 * space)
            cover[max(0, first - edge):last + edge + 1] = 0
        if (SPARSE and staggered and not high_stretch and top >= upper['rows'][4] and whole.size
                and not any(top <= band['top'] < bottom for band in bands)):
            peak = int(whole.argmax())
            if whole[peak] >= SPARSE:
                floor = max(2, LINE[1] * whole[peak])
                first = last = peak
                while first > 0 and whole[first - 1] >= floor:
                    first -= 1
                while last + 1 < len(whole) and whole[last + 1] >= floor:
                    last += 1
                if LINE[2] * space <= last - first + 1 <= LINE[3] * space:
                    bands.append({'top': top + first, 'bottom': top + last, 'few': True,
                                  'x0': int(min(upper['x0'], lower['x0'])), 'x1': int(max(upper['x1'], lower['x1']))})
        if STAGGER and staggered and high_stretch:
            # The letters between these two staves that stand in no row: with the stretch, the short rows beside it.
            found = [band for band in bands if top <= band['top'] < bottom]
            rest = [(x, y, w, h) for x, y, w, h in letters if y >= top and y + h <= bottom
                    and not any(band['top'] <= y + h / 2 <= band['bottom'] for band in found)]
            bands.extend(_staggered(rest, space, int(min(upper['x0'], lower['x0'])), int(max(upper['x1'], lower['x1']))))
        if BESIDE and staggered:
            _beside([band for band in bands if top <= band['top'] < bottom], letters)
    bands.sort(key=lambda band: band['top'])
    for band in bands:
        if 'with' in band:
            band['with'] = next(number for number, other in enumerate(bands) if other is band['with'])
    return bands


def _beside(bands: list[dict], letters: list[tuple]) -> None:
    """Marks the rows between two staves that go on the first of them (see BESIDE): band['with'] = that first row."""
    def reach(band: dict) -> tuple[int, int]:
        inside = [(x, x + w) for x, y, w, h in letters
                  if band['top'] <= y + h / 2 <= band['bottom'] and band['x0'] <= x + w / 2 <= band['x1']]
        return (min(x for x, _ in inside), max(x for _, x in inside)) if inside else (band['x0'], band['x1'])

    bands = sorted(bands, key=lambda band: band['top'])
    if len(bands) < 2:
        return
    first = bands[0]
    taken = [reach(first)]
    for band in bands[1:]:
        if not (band.get('own') or first.get('own')):
            continue
        low, high = reach(band)
        if all(high < start or low > end for start, end in taken):
            band['with'] = first
            taken.append((low, high))


def cut_stems(layers: dict, heads: list[dict], bands: list[dict]) -> int:
    """Ends each stem that runs into a band of words where the band begins: its 'end' is the last row of its own ink
    before the band, and stem['words'] holds the band's rows, so that nothing in the band counts as its flag.
    stem['full'] keeps the end that was found first (see scoreread.symbols.WORD_BEAMS), and stem['own'] the row where
    the stem's own ink ends in the band, without a break (see scoreread.symbols.THIN_FULL). Returns how many stems
    were cut."""
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
                row, letter = limit, False
                for column in ([int(round(stem['x'])), int(stem['mid'])] if STEM_MID and 'mid' in stem else [int(round(stem['x']))]):
                    strip = bare[:, max(0, column - 2):column + 3].any(axis=1)
                    reach = edge
                    while (reach > limit if down else reach < limit) and not strip[reach]:
                        reach += -1 if down else 1
                    if STEM_GAP and reach == edge:
                        # Ink at the edge of the band can be a letter that stands outside the band, in the stem's
                        # column: then paper lies between the letter and the stem, and the stem ends at the paper.
                        step, empty, at = (-1 if down else 1), 0, edge
                        while (at > limit if down else at < limit) and abs(at - edge) <= STEM_GAP[1] * space:
                            if strip[at]:
                                if empty >= STEM_GAP[0] * space:
                                    reach, letter = at, True
                                    break
                                empty = 0
                            else:
                                empty += 1
                            at += step
                    # The far end of the way can lie in a letter, beside the stem: the stem's own column reaches the band.
                    if (reach > row) if down else (reach < row) or row == limit:
                        if column != int(round(stem['x'])) and reach != row:
                            stem['x'] = column
                        row = reach
                # A head that stands right over the words has no stem left; its stem still ends there.
                stem['full'] = stem['end']
                # The stem's own end: its ink goes on into the band without a break, as far as it was found before.
                own, away = row, (1 if down else -1)
                if not letter:
                    strip = bare[:, max(0, int(round(stem['x'])) - 2):int(round(stem['x'])) + 3].any(axis=1)
                    while 0 <= own + away < len(strip) and strip[own + away] and (own - stem['full']) * away < 0:
                        own += away
                stem['own'] = own
                stem['end'] = row
                stem['words'] = (band['top'], band['bottom'])
                if letter:
                    # The rows of that letter are rows of words for this stem: its ink is no flag.
                    stem['words'] = (min(band['top'], row + 1), band['bottom']) if down else (band['top'], max(band['bottom'], row - 1))
                cut += 1
                break
    return cut

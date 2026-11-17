"""Reads the ison of a chant page of a scan: the drone that a second group holds under the melody. No model is used.

A chant page draws one staff for the melody. The ison is not drawn as a line of notes: a capital letter over the
staff names its note where it begins or moves ("E", "D"), and "Un." stands where the ison sings in unison with the
melody. The letter is read by its shape, with rules for the seven letters A to G only:

- a stem at the left over the whole height: B, D, E, F; no such stem: A, C, G;
- closed-in paper: two pieces for B, one large piece for D, one small piece in the upper half for A;
- the arms of E and F reach to the right at the top (and E at the bottom too), and the right side is open between;
- C and G are round at the left and open at the right; G has a spur at the right in its lower half.

A mark is a letter that stands alone: a letter inside a line of words (a title, the words of the line above) is
none. Anything that fits no letter is left out, so a slur, an accent or a pencil mark makes no ison.
"""
from __future__ import annotations

from fractions import Fraction

import cv2
import numpy as np

from .music import MIDDLE, STEPS

DRONE = True
OVER = (7.0, 0.2, 2.2)  # a letter stands at most this many staff spaces over the top line of its staff; its foot at most
                        # this many under the line, and at most this many over it (0: no limit): a section letter
                        # ("B") stands 3 spaces over the staff, a mark at most 1.5
HIGH = (0.9, 2.1)       # a capital letter is from this to this many staff spaces high
WIDE = (0.45, 1.9)      # and from this to this share of its height wide
WORD = 0.5              # pieces at most this many staff spaces apart are one word
ALONE = 2.5             # a mark stands alone: no word that is no mark within this many staff spaces of it
HEAVY = (0.6, 0.75)     # a heavy D: the paper it closes in lies this far to the right, its stem is this share of the height
ROW = (15.0, 2)         # or in a row of words: this many words that are no marks on its line within this many staff spaces
FLAT = 0.4              # a piece under this many staff spaces high is no letter: a line after the mark, a hyphen


def _holes(piece: np.ndarray) -> list[tuple[float, float, float]]:
    """The pieces of paper that the ink of a letter closes in: (share of the box, middle row, middle column), both
    middles as shares of the height and the width."""
    high, wide = piece.shape
    paper = np.pad(~piece, 1, constant_values=True).astype(np.uint8)
    count, labels, stats, centres = cv2.connectedComponentsWithStats(paper, connectivity=4)
    outside = labels[0, 0]
    out = []
    for label in range(1, count):
        if label == outside or stats[label][4] < max(3, 0.01 * high * wide):
            continue
        out.append((stats[label][4] / (high * wide), (centres[label][1] - 1) / high, (centres[label][0] - 1) / wide))
    return out


def _runs(row: np.ndarray) -> list[tuple[int, int]]:
    """The runs of ink in one row: (first column, last column) each."""
    columns = np.flatnonzero(row)
    if len(columns) == 0:
        return []
    cuts = np.flatnonzero(np.diff(columns) > 1)
    firsts = [columns[0]] + [columns[cut + 1] for cut in cuts]
    lasts = [columns[cut] for cut in cuts] + [columns[-1]]
    return list(zip(firsts, lasts))


def name_letter(piece: np.ndarray) -> str | None:
    """The capital letter A to G that a piece of ink is, or 'U' (the first letter of "Un."), or None."""
    piece = piece.astype(bool)
    rows, columns = np.flatnonzero(piece.any(axis=1)), np.flatnonzero(piece.any(axis=0))
    if len(rows) == 0:
        return None
    piece = piece[rows[0]:rows[-1] + 1, columns[0]:columns[-1] + 1]
    high, wide = piece.shape
    if high < 8 or wide < 5:
        return None
    holes = sorted(_holes(piece), reverse=True)
    left = np.array([np.flatnonzero(row)[0] if row.any() else wide for row in piece]) / wide
    right = np.array([(np.flatnonzero(row)[-1] + 1) if row.any() else 0 for row in piece]) / wide
    count = np.array([len(_runs(row)) for row in piece])

    def band(values: np.ndarray, first: float, last: float) -> np.ndarray:
        return values[int(first * high):max(int(first * high) + 1, int(np.ceil(last * high)))]

    def crossings(share: float) -> list[tuple[float, float]]:
        """The runs of ink in the column at this share of the width: (first row, last row) as shares of the height."""
        return [(first / high, (last + 1) / high) for first, last in _runs(piece[:, min(wide - 1, int(share * wide))])]

    arms = [crossings(share) for share in (0.6, 0.7, 0.8)]
    top, bottom = band(right, 0.0, 0.2).max(), band(right, 0.8, 1.0).max()
    # A stem at the left: the left columns are ink from top to bottom, and no row begins far from the left edge.
    stem = piece[:, :max(2, int(0.4 * wide))].sum(axis=0).max() >= 0.8 * high and (left <= 0.3).mean() >= 0.9
    # Corners at the left (the ends of a stem, or its serifs), as against the round left side of C, G and O.
    corners = band(left, 0.0, 0.1).min() <= 0.1 and band(left, 0.9, 1.0).min() <= 0.1
    if len(holes) >= 2 and holes[1][0] >= 0.03 and abs(holes[0][1] - holes[1][1]) >= 0.25:
        return 'B' if stem and corners else None
    if len(holes) == 1 and 0.3 <= holes[0][1] <= 0.7 and holes[0][2] >= 0.35 and band(right, 0.25, 0.75).min() >= 0.8 \
            and (stem or holes[0][0] >= 0.03):
        # D: the bowl closes the right side from top to bottom, and its right corners are round. At the left it has
        # corners; or, in a heavy face with long serifs, the stem stands upright left of the closed-in paper, which
        # the serifs push to the right.
        upright = max((last - first + 1 for column in range(int(holes[0][2] * wide)) for first, last in _runs(piece[:, column])),
                      default=0) >= HEAVY[1] * high
        if (corners or (holes[0][2] >= HEAVY[0] and upright)) \
                and min(band(right, 0.0, 0.06).max(), band(right, 0.94, 1.0).max()) <= 0.92:
            return 'D'
        return None
    if len(holes) == 1 and holes[0][0] <= 0.2 and 0.3 <= holes[0][2] <= 0.7 and holes[0][1] <= 0.75 and not stem:
        # A: a point at the top, two feet at the bottom, the bar closes the paper between its legs.
        peak = band(right, 0.0, 0.15).max() - band(left, 0.0, 0.15).min()
        if peak <= 0.6 and band(count, 0.8, 1.0).max() >= 2 and band(left, 0.0, 0.15).min() >= 0.2:
            return 'A'
        return None
    if holes:
        return None
    # U: two strokes side by side from the top over more than half of the height, one bowl at the bottom.
    upper = band(count, 0.05, 0.6) == 2
    if upper.mean() >= 0.85 and np.median(band(left, 0.05, 0.6)) <= 0.3 and np.median(band(right, 0.05, 0.6)) >= 0.7 \
            and any(len(runs) == 1 and runs[0][1] - runs[0][0] + 1 >= 0.3 * wide for runs in (_runs(row) for row in band(piece, 0.8, 1.0))):
        return 'U'
    if stem and corners:
        # E: three arms cross a column in the right half, the first at the top and the last at the bottom.
        if top >= 0.8 and bottom >= 0.7 and any(len(runs) == 3 and runs[0][0] <= 0.12 and runs[-1][1] >= 0.88 for runs in arms):
            return 'E'
        # F: two arms, both in the upper part; under them the stem alone, with its foot.
        if top >= 0.8 and band(right, 0.72, 1.0).max() <= 0.75 \
                and any(len(runs) == 2 and runs[0][0] <= 0.12 and runs[-1][1] <= 0.7 for runs in arms):
            return 'F'
        return None
    # C and G: round at the left (the top and bottom rows begin further right than the middle), ink at the top and
    # at the bottom, open at the right over the middle.
    round_left = band(left, 0.3, 0.7).max() <= 0.2 and min(band(left, 0.0, 0.08).min(), band(left, 0.92, 1.0).min()) >= 0.12
    if not round_left or top < 0.75 or bottom < 0.75 or wide < 0.6 * high:
        return None
    if band(right, 0.25, 0.45).min() <= 0.55:
        lower = band(right, 0.62, 0.8)
        if lower.min() >= 0.8 and band(count, 0.62, 0.8).max() >= 2:
            return 'G'
        if band(right, 0.4, 0.6).max() <= 0.55 and band(count, 0.4, 0.6).max() == 1:
            return 'C'
    return None


def letter_marks(layers: dict, index: int, clef: str, after: float = 0.0, trace: list | None = None) -> list[dict]:
    """The ison marks over staff `index`: events as music.staff_columns() gives them ({'x', 'place', 'voice', 'head',
    'length', 'stem_x'}, and 'unison' for "Un."), from the left. Only marks right of the column `after` count (the
    clef stands before it). `trace` collects every word that was looked at, for checks."""
    if not DRONE:
        return []
    staff, space = layers['staves'][index], layers['space']
    top = int(round(staff['rows'][0]))
    first = max(0, int(top - OVER[0] * space))
    last = int(top + OVER[1] * space)
    ink = layers['bare'][first:last + 1].astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    pieces = []
    for label in range(1, count):
        x, y, wide, high, _ = (int(value) for value in stats[label])
        if not max(staff['x0'] - space, after) <= x <= staff['x1'] or max(high, wide) < 0.25 * space or y == 0 \
                or y + high >= ink.shape[0]:
            continue      # a piece that the band cuts at its top belongs to the line above, at its foot to the staff
        if high > HIGH[1] * space or wide > WIDE[1] * HIGH[1] * space:
            continue      # a slur, a pencil stroke
        if any(band['top'] <= y + first + high / 2 <= band['bottom'] and band['x0'] <= x <= band['x1']
               for band in layers.get('words') or []):
            continue      # the words of the line above
        pieces.append({'x0': x, 'x1': x + wide - 1, 'y0': y, 'y1': y + high - 1, 'label': label})
    pieces.sort(key=lambda piece: piece['x0'])
    words: list[list[dict]] = []
    for piece in pieces:
        near = [word for word in words if piece['x0'] - max(other['x1'] for other in word) <= WORD * space
                and min(piece['y1'], max(other['y1'] for other in word)) - max(piece['y0'], min(other['y0'] for other in word)) >= -0.3 * space]
        if near:
            near[-1].append(piece)
        else:
            words.append([piece])
    named = []
    for word in words:
        head = word[0]
        high, wide = head['y1'] - head['y0'] + 1, head['x1'] - head['x0'] + 1
        letter = None
        if HIGH[0] * space <= high <= HIGH[1] * space and WIDE[0] * high <= wide <= WIDE[1] * high:
            letter = name_letter(labels[head['y0']:head['y1'] + 1, head['x0']:head['x1'] + 1] == head['label'])
        rest = [piece for piece in word[1:] if piece['y1'] - piece['y0'] + 1 >= FLAT * space]
        if letter == 'U':
            # "Un.": the n is lower than the U and stands on its line; after it only the full stop, or a stroke that
            # a pencil joined to it, in the lower half.
            mark = 'Un.' if rest and FLAT * space <= rest[0]['y1'] - rest[0]['y0'] + 1 <= 0.85 * high \
                and abs(rest[0]['y1'] - head['y1']) <= 0.3 * space \
                and all(piece['y0'] >= head['y0'] + 0.4 * high for piece in rest[1:]) and len(rest) <= 2 else None
        else:
            mark = letter if letter and not rest else None
        if mark and OVER[2] and top - (head['y1'] + first) > OVER[2] * space:
            mark = None       # a section letter, far over the staff
        if trace is not None:
            trace.append((head['x0'], head['y0'] + first, wide, high, letter, mark, len(word)))
        named.append({'x0': word[0]['x0'], 'x1': max(piece['x1'] for piece in word), 'y0': min(piece['y0'] for piece in word),
                      'y1': max(piece['y1'] for piece in word), 'mark': mark, 'letter': head})
    out = []
    for word in named:
        if word['mark'] is None:
            continue
        # A mark stands alone: a letter in a row of words is a word.
        beside = [max(other['x0'] - word['x1'], word['x0'] - other['x1']) for other in named
                  if other is not word and other['mark'] is None and other['y1'] - other['y0'] + 1 >= 0.6 * space
                  and min(word['y1'], other['y1']) - max(word['y0'], other['y0']) >= 0.3 * space]
        if any(far <= ALONE * space for far in beside) or sum(far <= ROW[0] * space for far in beside) >= ROW[1]:
            continue
        letter = word['letter']
        x = (letter['x0'] + letter['x1']) / 2
        box = {'x0': letter['x0'], 'x1': letter['x1'], 'y0': letter['y0'] + first, 'y1': letter['y1'] + first, 'cx': x,
               'cy': (letter['y0'] + letter['y1']) / 2 + first, 'hollow': True, 'stems': [], 'tails': {}, 'staff': index,
               'letter': word['mark']}
        if word['mark'] == 'Un.':
            out.append({'x': x, 'place': 0, 'voice': 1, 'head': dict(box, place=0), 'length': Fraction(4), 'stem_x': None,
                        'unison': True})
            continue
        octave = 4 if clef == 'G' else 3
        place = 7 * octave + STEPS.index(word['mark']) - MIDDLE[clef]
        out.append({'x': x, 'place': place, 'voice': 1, 'head': dict(box, place=place), 'length': Fraction(4), 'stem_x': None})
    return out

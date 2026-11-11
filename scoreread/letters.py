"""Finds the letters of the words of a page and groups them by shape. No model is used.

One copyist, one typewriter or one type draws a letter the same way each time, so the page teaches its own letters:
the pieces of ink of the rows of words are set on one canvas (scaled by the height of the small letters, placed by
the line that the letters stand on), and the pieces of one shape make one group. The groups have no names here:
scoreread.lyrics names them with a list of words.
"""
from __future__ import annotations

import cv2
import numpy as np

CANVAS = (56, 64)       # rows and columns of the canvas of a letter
BASE, XH = 38, 16       # on the canvas the letters stand on row BASE, and a small letter (an x) is XH rows high
ROW_LEAST = 8           # a row of words holds at least this many pieces of ink
XH_LEAST = 6            # and its small letters are at least this many points high: smaller ones cannot be told apart
STRICT = (1, 5, 0.3)    # two shapes are one letter when neither has a piece of ink that the other lacks: ink within
#                         this many points of the other's ink is no piece, a piece has at least this many points,
#                         and the shapes differ in at most this share of their ink
WIDE = 0.25             # and in at most this share of their width (and one point)


def row_glyphs(layers: dict, band: dict) -> list[dict]:
    """The pieces of ink of a row of words, from the left: {'x0', 'x1', 'y0', 'y1', 'mask', 'parts'} each. The dot
    of an i is joined to its stroke ('parts' is then 2)."""
    ink = layers['ink']
    high = band['bottom'] - band['top'] + 1
    y0, y1 = max(0, band['top'] - high), min(ink.shape[0], band['bottom'] + high)
    crop = (ink[y0:y1, band['x0']:band['x1']] > 0).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(crop, connectivity=8)
    pieces = []
    for label in range(1, count):
        x, y, w, h, area = stats[label]
        middle = y0 + y + h / 2
        if not band['top'] - 0.5 * high <= middle <= band['bottom'] + 0.3 * high or h > 2.2 * high or area < 4:
            continue
        pieces.append({'x0': int(x), 'x1': int(x + w - 1), 'y0': int(y0 + y), 'y1': int(y0 + y + h - 1),
                       'mask': labels[y:y + h, x:x + w] == label})
    pieces.sort(key=lambda piece: piece['x0'])
    # A dot over a stroke (i, j) and the two dots of a colon: pieces that stand over each other are one glyph.
    glyphs = []
    for piece in pieces:
        last = glyphs[-1] if glyphs else None
        if last is not None:
            shared = min(last['x1'], piece['x1']) - max(last['x0'], piece['x0']) + 1
            narrow = min(last['x1'] - last['x0'], piece['x1'] - piece['x0']) + 1
            apart = piece['y0'] > last['y1'] or last['y0'] > piece['y1']
            if shared >= 0.6 * narrow and apart:
                x0, x1 = min(last['x0'], piece['x0']), max(last['x1'], piece['x1'])
                top, bottom = min(last['y0'], piece['y0']), max(last['y1'], piece['y1'])
                mask = np.zeros((bottom - top + 1, x1 - x0 + 1), bool)
                for part in (last, piece):
                    mask[part['y0'] - top:part['y1'] - top + 1, part['x0'] - x0:part['x1'] - x0 + 1] |= part['mask']
                glyphs[-1] = {'x0': x0, 'x1': x1, 'y0': top, 'y1': bottom, 'mask': mask, 'parts': last['parts'] + 1}
                continue
        glyphs.append(dict(piece, parts=1))
    for glyph in glyphs:
        glyph['x0'] += band['x0']
        glyph['x1'] += band['x0']
    return glyphs


def line_metrics(glyphs: list[dict]) -> tuple[int, int | None]:
    """The line that the letters of a row stand on, and the height of its small letters (the x-height): most
    letters stand on the line, and the lower of the two usual heights of those letters is the x-height (the other
    is the height of b, d, h, l and of the capitals). The height is None when the row shows none."""
    bottoms = np.array([glyph['y1'] for glyph in glyphs])
    values, counts = np.unique(bottoms, return_counts=True)
    base = max((sum(c for v, c in zip(values, counts) if abs(v - value) <= 1), value) for value in values)[1]
    least = 0.3 * (base - min(glyph['y0'] for glyph in glyphs))
    heights = np.array([glyph['y1'] - glyph['y0'] + 1 for glyph in glyphs
                        if abs(glyph['y1'] - base) <= 2 and glyph['y1'] - glyph['y0'] > least])
    if not len(heights):
        return int(base), None
    values, counts = np.unique(heights, return_counts=True)
    spread = sorted(((sum(c for v, c in zip(values, counts) if abs(v - value) <= 1), -value) for value in values),
                    reverse=True)[:2]
    return int(base), int(min(-value for count, value in spread if count >= 0.5 * spread[0][0]))


def normal(glyph: dict, base: float, xh: float) -> tuple[np.ndarray, int]:
    """The glyph on the canvas: scaled so that a small letter is XH rows high, and set on the line. Returns the
    canvas and the width of the glyph on it."""
    scale = XH / xh
    mask = glyph['mask'].astype(np.float32)
    high, wide = max(1, int(round(mask.shape[0] * scale))), max(1, int(round(mask.shape[1] * scale)))
    small = cv2.resize(mask, (wide, high), interpolation=cv2.INTER_AREA)
    canvas = np.zeros(CANVAS, np.float32)
    bottom = BASE + int(round((glyph['y1'] - base) * scale))
    top = bottom - high + 1
    r0, r1 = max(0, top), min(CANVAS[0], bottom + 1)
    c1 = min(CANVAS[1], wide)
    if r1 > r0:
        canvas[r0:r1, :c1] = small[r0 - top:r1 - top, :c1]
    return canvas, wide


def differ(one: np.ndarray, other: np.ndarray, edge: int = 1) -> tuple[float, int]:
    """How two shapes on the canvas differ, at the small shift where they fit best: the share of their ink that
    they do not have in common (0 the same, 1 nothing in common), and the size of the largest piece of ink that one
    has and the other lacks (ink within `edge` points of the other's ink does not count). The piece tells an e from
    a c, and an N from an H."""
    best, shift = 1.0, (0, 0)
    total = max(float(one.sum() + other.sum()), 1e-6)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            moved = np.roll(np.roll(other, dy, axis=0), dx, axis=1)
            share = 1.0 - 2.0 * float(np.minimum(one, moved).sum()) / total
            if share < best:
                best, shift = share, (dy, dx)
    moved = np.roll(np.roll(other, shift[0], axis=0), shift[1], axis=1)
    first, second = (one >= 0.5).astype(np.uint8), (moved >= 0.5).astype(np.uint8)
    kernel = np.ones((2 * edge + 1, 2 * edge + 1), np.uint8)
    lacks = (first & ~cv2.dilate(second, kernel)) | (second & ~cv2.dilate(first, kernel))
    if not lacks.any():
        return best, 0
    count, _, stats, _ = cv2.connectedComponentsWithStats(lacks, connectivity=8)
    return best, int(stats[1:count, cv2.CC_STAT_AREA].max())


def group_glyphs(glyphs: list[dict], how: tuple = STRICT) -> list[dict]:
    """Groups the glyphs of a hymn by shape, and sets glyph['group'] (the number of its group). Each glyph joins
    the nearest group that it differs from by no piece of ink, or begins a group. Each group: {'mean' (the mean
    shape on the canvas), 'wide', 'members' (the numbers of its glyphs)}. `how` says how strict the grouping is
    (see STRICT)."""
    edge, least, near_most = how
    groups = []
    for index, glyph in enumerate(glyphs):
        canvas, wide = glyph['canvas'], glyph['wide']
        best, near = None, near_most
        for number, group in enumerate(groups):
            if abs(group['wide'] - wide) > WIDE * max(group['wide'], wide) + 1:
                continue
            share, lacks = differ(group['mean'], canvas, edge)
            if share < near and lacks < least:
                best, near = number, share
        if best is None:
            best = len(groups)
            groups.append({'mean': canvas.copy(), 'wide': float(wide), 'members': [index]})
        else:
            group = groups[best]
            count = len(group['members'])
            group['mean'] = (group['mean'] * count + canvas) / (count + 1)
            group['wide'] = (group['wide'] * count + wide) / (count + 1)
            group['members'].append(index)
        glyph['group'] = best
    return groups


def page_glyphs(layers: dict | None, page: int = 0) -> list[dict]:
    """Every glyph of the rows of words of a page. Each has, beside what row_glyphs() gives: 'band' (the page and
    the number of its row), 'base' and 'xh' (the line and the x-height of its row), and 'canvas' and 'wide' (its
    shape on the canvas)."""
    found = []
    if not layers:
        return found
    for number, band in enumerate(layers.get('words') or []):
        glyphs = row_glyphs(layers, band)
        if len(glyphs) < ROW_LEAST:
            continue
        base, xh = line_metrics(glyphs)
        if not xh or xh < XH_LEAST:
            continue
        for glyph in glyphs:
            glyph.update(band=(page, number), base=base, xh=xh)
            glyph['canvas'], glyph['wide'] = normal(glyph, base, xh)
        found += glyphs
    return found

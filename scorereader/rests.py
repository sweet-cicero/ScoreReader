"""Finds the printed quarter rests of a page. No model is used.

A printed quarter rest is one piece of ink of its own, about three staff spaces high and one wide, that closes in no
paper: a stroke that swings to the right, back to the left, to the right again, and ends in a hook at the left. Its
thick middle is as fat as a filled head and its thin strokes stand like a stem, so the symbol step reads it as a
quarter note. The note with a stem has one straight edge, the stem's, from end to end; a pair of sharps, a natural
at its head and a clef close in paper; the rest has neither.

A rest is no note, and it says where a voice is silent: the note before it is not as long as the way to the next
note of its voice (scorereader.music.agree_lengths).

One older print sets its quarter rest as an X on the middle line of the staff, with a short upright through the
crossing (CROSS). The staff lines close the paper between its arms, and those cells were read as whole notes.

Only the printed quarter rest is read. The rests of a hand, the eighth rest and the rests that hang on a staff line
are not read yet.
"""
from __future__ import annotations

from fractions import Fraction

import cv2
import numpy as np

QUARTER = (2.0, 3.6, 0.52, 1.35)     # a quarter rest is from this to this many staff spaces high and from this to this
#                                      many wide (None: the rests are not read)
SWING = (0.12, 0.12, 0.03, 0.08)     # the middle of its ink, in eight parts from top to bottom: it goes right by this
#                                      many staff spaces in the first three parts, back left by this much in parts four
#                                      and five, right again by this much, and left by this much in the last two
EDGE = (0.15, 0.85)                  # neither its left nor its right edge is straight: within this many staff spaces of
#                                      its middle place over at most this share of the rows (a stem is straight)
HOLE = 0.02                          # it closes in no paper larger than this many square staff spaces
HOOK = (0.06, 0.7)                   # ... but the hook at its lower end can close: one piece of paper of at most this
#                                      many square staff spaces whose middle lies this far down the rest or further
#                                      (four rests of LitChoir's pages, 0.024 to 0.043 at 0.8; None: off)
CROSS = (1.9, 2.5, 1.3, 1.9, 0.3, 0.75, 0.35, 0.7, 0.1, 1.6, 0.5, 0.35)
#                                      the quarter rest of one older print is an X with a short upright through its
#                                      crossing, on the middle line of the staff (None: not read). The staff lines
#                                      close the paper between its arms, and those cells were read as whole notes. It
#                                      is from the first to the second number of staff spaces high and from the third
#                                      to the fourth wide; its middle lies at most [4] staff spaces from the middle
#                                      line. Its waist, the narrowest row of the middle two fifths, is at most [5]
#                                      staff spaces wide and stands from [6] to [7] of the way across; in the three
#                                      tenths of the rows around the middle the ink keeps [8] of the width clear at
#                                      both sides (the sides of two whole notes one over the other, an 8, fill the
#                                      width there, and the C of common time stands at the left); the ink at the top
#                                      and at the bottom is [9] times as wide as the waist, and in [10] of the rows of
#                                      the last quarter its legs stand apart, by [11] staff spaces or more at one row.
#                                      A rule for one print. The census: 753 pieces of ink of LitChoir's scan pages
#                                      have a waist; 43 of them are of this size, in the middle of a staff, with two
#                                      legs: the six rests (three scans of one hymn), 22 signs of common time, 13
#                                      pairs of whole notes, a number and an eighth rest. The rule reads the six.
OUTSIDE = 1.0                        # its middle lies in the staff or at most this many staff spaces outside it
REACH = 0.2                          # a head whose middle lies in the rest, or this many staff spaces outside it, is no note


def quarter_rests(layers: dict, ends: list[float]) -> list[dict]:
    """The printed quarter rests of a page: [{'staff', 'x', 'x0', 'x1', 'top', 'bottom', 'middle', 'kind', 'length'}],
    where 'middle' is how many staff spaces the rest's middle lies under the middle line of its staff.
    Closes thin vertical staff-line breaks per staff so printed quarter rests cut by staff lines stay whole."""
    if QUARTER is None:
        return []
    space = layers['space']
    bare = layers['bare'].astype(np.uint8)
    out = []
    seen: list[tuple[int, float]] = []

    def _scan_mask(mask: np.ndarray, staff_filter: int | None = None, y_offset: int = 0) -> None:
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        for number in range(1, count):
            x, y, wide, high = (int(value) for value in stats[number][:4])
            if not (QUARTER[0] * space <= high <= QUARTER[1] * space and QUARTER[2] * space <= wide <= QUARTER[3] * space):
                continue
            gy = y + y_offset
            at = gy + high / 2
            if staff_filter is not None:
                index = staff_filter
                staff = layers['staves'][index]
                if not (staff['rows'][0] - OUTSIDE * space <= at <= staff['rows'][4] + OUTSIDE * space
                        and staff['x0'] <= x and x + wide <= staff['x1']):
                    continue
            else:
                index = next((i for i, staff in enumerate(layers['staves'])
                              if staff['rows'][0] - OUTSIDE * space <= at <= staff['rows'][4] + OUTSIDE * space
                              and staff['x0'] <= x and x + wide <= staff['x1']), None)
                if index is None:
                    continue
            if x <= ends[index]:
                continue
            cx = x + wide / 2
            if any(si == index and abs(sx - cx) <= 0.6 * space for si, sx in seen):
                continue
            piece = labels[y:y + high, x:x + wide] == number
            if not _rest_shape(piece, space):
                continue
            seen.append((index, cx))
            out.append({'staff': index, 'x': cx, 'x0': x, 'x1': x + wide, 'top': gy, 'bottom': gy + high,
                        'middle': (at - layers['staves'][index]['rows'][2]) / space,
                        'kind': 'quarter', 'length': Fraction(1)})

    # First scan raw bare mask (exact compatibility), then scan staff-line-bridged bare mask for cut rests.
    _scan_mask(bare)
    for index, staff in enumerate(layers['staves']):
        y0 = max(0, int(staff['rows'][0] - 1.5 * space))
        y1 = min(bare.shape[0], int(staff['rows'][4] + 1.5 * space) + 1)
        if y1 <= y0:
            continue
        bridge_h = max(3, int(round(staff['thick'] + 2))) | 1
        bridged = cv2.morphologyEx(np.ascontiguousarray(bare[y0:y1]), cv2.MORPH_CLOSE, np.ones((bridge_h, 1), np.uint8))
        _scan_mask(bridged, staff_filter=index, y_offset=y0)

    if CROSS:
        count, labels, stats, _ = cv2.connectedComponentsWithStats(bare, connectivity=8)
        for number in range(1, count):
            x, y, wide, high = (int(value) for value in stats[number][:4])
            if not (CROSS[0] * space <= high <= CROSS[1] * space and CROSS[2] * space <= wide <= CROSS[3] * space):
                continue
            at = y + high / 2
            index = next((index for index, staff in enumerate(layers['staves'])
                          if abs(at - staff['rows'][2]) <= CROSS[4] * staff['space']
                          and staff['x0'] <= x and x + wide <= staff['x1']), None)
            if index is None or x <= ends[index]:
                continue
            cx = x + wide / 2
            if any(si == index and abs(sx - cx) <= 0.6 * space for si, sx in seen):
                continue
            if _cross_shape(labels[y:y + high, x:x + wide] == number, space):
                seen.append((index, cx))
                out.append({'staff': index, 'x': cx, 'x0': x, 'x1': x + wide, 'top': y, 'bottom': y + high,
                            'middle': (at - layers['staves'][index]['rows'][2]) / space,
                            'cross': True, 'kind': 'quarter', 'length': Fraction(1)})
    return out


def _cross_shape(piece: np.ndarray, space: float) -> bool:
    """Whether a piece of ink has the shape of the X of an older quarter rest (see CROSS)."""
    high, wide = piece.shape
    spans = []
    for row in piece:
        columns = np.nonzero(row)[0]
        spans.append((int(columns[0]), int(columns[-1])) if len(columns) else None)
    # The waist: the crossing of the two strokes.
    middle = [(last - first + 1, (first + last) / 2) for first, last in
              (span for span in spans[int(0.3 * high):max(int(0.3 * high) + 1, int(0.7 * high))] if span)]
    if not middle:
        return False
    waist, where = min(middle)
    if waist > CROSS[5] * space or not CROSS[6] * wide <= where <= CROSS[7] * wide:
        return False
    # Around the middle the ink stands clear of both sides of the box.
    band = np.nonzero(piece[int(0.35 * high):max(int(0.35 * high) + 1, int(0.65 * high))].any(axis=0))[0]
    if not len(band) or band[0] < CROSS[8] * wide or band[-1] > (1 - CROSS[8]) * wide:
        return False
    # The arms: the ink is wide at the top and at the bottom, and two legs stand apart at the bottom.
    for part in (spans[:max(1, high // 4)], spans[high - max(1, high // 4):]):
        reach = [span for span in part if span]
        if not reach or max(last for _, last in reach) - min(first for first, _ in reach) + 1 < CROSS[9] * waist:
            return False
    rows = piece[high - max(1, high // 4):]
    gaps = [int(np.diff(columns).max()) - 1 for columns in (np.nonzero(row)[0] for row in rows) if len(columns) >= 2]
    gaps = [gap for gap in gaps if gap > 0]
    return len(gaps) >= CROSS[10] * len(rows) and max(gaps) >= CROSS[11] * space


def _rest_shape(piece: np.ndarray, space: float) -> bool:
    """Whether a piece of ink has the shape of a quarter rest (see SWING, EDGE and HOLE)."""
    high = piece.shape[0]
    # No paper closed in.
    paper = (~np.pad(piece, 1)).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
    closed = [number for number in range(1, count) if labels[0, 0] != number and stats[number][4] >= HOLE * space * space]
    if closed and not (HOOK and len(closed) == 1 and stats[closed[0]][4] <= HOOK[0] * space * space
                       and stats[closed[0]][1] + stats[closed[0]][3] / 2 - 1 >= HOOK[1] * high):
        return False
    # No straight edge.
    rows = [np.nonzero(row)[0] for row in piece]
    rows = [row for row in rows if len(row)]
    for edge in (np.array([row[0] for row in rows]), np.array([row[-1] for row in rows])):
        if (np.abs(edge - np.median(edge)) <= EDGE[0] * space).mean() > EDGE[1]:
            return False
    # The swing of the stroke.
    middle = np.array([np.nonzero(row)[0].mean() if row.any() else np.nan for row in piece]) / space
    parts = []
    for number in range(8):
        part = middle[int(high * number / 8):max(int(high * number / 8) + 1, int(high * (number + 1) / 8))]
        if np.isnan(part).all():
            return False
        parts.append(float(np.nanmean(part)))
    right = max(parts[1], parts[2])
    back = min(parts[3], parts[4])
    again = max(parts[4], parts[5])
    return right - parts[0] >= SWING[0] and right - back >= SWING[1] and again - back >= SWING[2] \
        and again - min(parts[6], parts[7]) >= SWING[3]


def in_rest(head: dict, rests: list[dict], space: float) -> bool:
    """Whether the middle of a head lies in a rest of its staff."""
    return any(rest['staff'] == head['staff'] and rest['x0'] - REACH * space <= head['cx'] <= rest['x1'] + REACH * space
               and rest['top'] - REACH * space <= head['cy'] <= rest['bottom'] + REACH * space for rest in rests)


BLOCK = (0.95, 1.8, 0.5, 0.9, 0.82, 0.8, 2.25)
#                                    a whole or a half rest is a block from the first to the second number of staff
#                                    spaces wide and from the third to the fourth high, whose box is at least the fifth
#                                    number ink, whose columns are nearly all ink over its height (at least the sixth
#                                    number of them), and whose middle lies at most the last number of staff spaces from
#                                    the middle line of its staff (None: the blocks are not read)


HANG = (0.15, 0.1)                   # a block hangs from a line where its top is at most the first number of staff spaces
#                                      over the line and the second under it (the top of a whole rest), and
SIT = (0.0, 0.2)                     # sits on a line where its bottom is from the first to the second number under it
#                                      (the bottom of a half rest: the line is ink under the block)


def block_rests(layers: dict, ends: list[float], measure: bool = False) -> list[dict]:
    """The printed whole and half rests of a page, as quarter_rests() gives the quarter rests, with 'kind' 'block'.
    With measure, every piece of the size of a block with its measures ('fill', 'square', 'middle'), and 'rest'
    whether it passes."""
    if BLOCK is None:
        return []
    space = layers['space']
    ink = layers['ink'] > 0
    free = layers['free'].astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(free, connectivity=8)
    out = []
    for number in range(1, count):
        x, y, wide, high = (int(value) for value in stats[number][:4])
        if not (0.8 * space <= wide <= 1.9 * space and 0.25 * space <= high <= 0.95 * space):
            continue
        at = y + high / 2
        index = next((index for index, staff in enumerate(layers['staves'])
                      if staff['rows'][0] - 2 * space <= at <= staff['rows'][4] + 2 * space
                      and staff['x0'] <= x and x + wide <= staff['x1']), None)
        if index is None or x <= ends[index]:
            continue
        box = ink[y:y + high, x:x + wide]
        fill = float(box.mean())
        square = float((box.sum(axis=0) >= 0.8 * high).mean())
        middle = (at - layers['staves'][index]['rows'][2]) / space
        rows = layers['staves'][index]['rows']
        lines = [rows[0] + step * (rows[4] - rows[0]) / 4 for step in range(-2, 7)]
        hangs = any(-HANG[0] * space <= y - line <= HANG[1] * space for line in lines)
        sits = any(SIT[0] * space <= y + high - line <= SIT[1] * space for line in lines)
        # Engraved whole/half rests can be 0.36..0.50 spaces tall; accept crisp rectangles sitting on line 3 or hanging from line 4.
        slim_block = (0.90 * space <= wide <= 1.80 * space and 0.36 * space <= high < BLOCK[2] * space
                      and fill >= 0.84 and square >= 0.82
                      and ((abs(y - rows[1]) <= 0.18 * space and hangs) or (abs(y + high - rows[2]) <= 0.22 * space and sits)))
        if slim_block:
            # Verify empty paper on the open side of the rectangle (not a beam or staff smudge).
            pad_h = max(2, int(round(0.25 * space)))
            check_y0, check_y1 = (y + high + 1, min(ink.shape[0], y + high + 1 + pad_h)) if hangs else (max(0, y - pad_h), y)
            if check_y1 <= check_y0 or float(ink[check_y0:check_y1, x:x + wide].mean()) > 0.12:
                slim_block = False
        rest = (BLOCK[0] * space <= wide <= BLOCK[1] * space and BLOCK[2] * space <= high <= BLOCK[3] * space
                and fill >= BLOCK[4] and square >= BLOCK[5] and abs(middle) <= BLOCK[6]) or slim_block
        if rest or measure:
            length = Fraction(4) if (hangs and not sits) or (abs(y - rows[1]) < abs(y + high - rows[2])) else Fraction(2)
            found = {'staff': index, 'x': x + wide / 2, 'x0': x, 'x1': x + wide, 'top': y, 'bottom': y + high,
                     'middle': middle, 'kind': 'block', 'length': length,
                     'hangs': hangs, 'sits': sits}
            if measure:
                found.update(fill=fill, square=square, wide=wide / space, high=high / space, rest=rest)
            out.append(found)
    return out


def rest_dot(layers: dict, rest: dict) -> bool:
    """Returns True when an augmentation dot stands immediately to the right of a rest."""
    bare, space = layers['bare'], layers['space']
    h, w = bare.shape
    x0 = min(w, int(rest['x1'] + 0.18 * space))
    x1 = min(w, int(rest['x1'] + 1.15 * space))
    y0 = max(0, int(rest['top'] - 0.35 * space))
    y1 = min(h, int(rest['bottom'] + 0.35 * space))
    if x1 - x0 < 3 or y1 - y0 < 3:
        return False
    count, _, stats, _ = cv2.connectedComponentsWithStats(np.ascontiguousarray(bare[y0:y1, x0:x1].astype(np.uint8)), connectivity=8)
    for k in range(1, count):
        dx, dy, dw, dh, area = (int(v) for v in stats[k])
        if 0.18 * space <= dw <= 0.55 * space and 0.18 * space <= dh <= 0.55 * space:
            if area >= 0.55 * dw * dh and 0.55 <= dw / dh <= 1.65:
                return True
    return False


def eighth_rests(layers: dict, ends: list[float], heads: list[dict], bars: dict[int, list[float]]) -> list[dict]:
    """Detects printed eighth rests (1/2 beat) and sixteenth rests (1/4 beat) standing free of notes and barlines."""
    space = layers['space']
    bare = layers['bare'].astype(np.uint8)
    out = []
    for index, staff in enumerate(layers['staves']):
        rows = staff['rows']
        y0 = max(0, int(rows[0] - 0.6 * space))
        y1 = min(bare.shape[0], int(rows[4] + 0.6 * space) + 1)
        if y1 <= y0:
            continue
        bridge_h = max(3, int(round(staff['thick'] + 2))) | 1
        region = cv2.morphologyEx(np.ascontiguousarray(bare[y0:y1]), cv2.MORPH_CLOSE, np.ones((bridge_h, 1), np.uint8))
        count, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)
        staff_heads = [h for h in heads if h['staff'] == index]
        staff_bars = bars.get(index, [])
        for k in range(1, count):
            x, y, wide, high, area = (int(v) for v in stats[k])
            if x <= ends[index] + 0.3 * space or x + wide > staff['x1']:
                continue
            if not (1.45 * space <= high <= 3.1 * space and 0.60 * space <= wide <= 1.45 * space):
                continue
            gy = y + y0
            cx, cy = x + wide / 2.0, gy + high / 2.0
            if abs(cy - rows[2]) > 1.25 * space:
                continue
            # Reject anything overlapping a detected notehead, stem, or barline.
            if any(abs(cx - bx) <= 0.45 * space for bx in staff_bars):
                continue
            if any(h['x0'] - 0.35 * space <= cx <= h['x1'] + 0.35 * space and h['y0'] - 0.5 * space <= cy <= h['y1'] + 0.5 * space
                   for h in staff_heads):
                continue
            if any(abs(s['x'] - cx) <= 0.45 * space and min(h['cy'], s['end']) <= cy <= max(h['cy'], s['end'])
                   for h in staff_heads for s in h.get('stems', [])):
                continue
            piece = labels[y:y + high, x:x + wide] == k
            fill = float(piece.mean())
            if not (0.16 <= fill <= 0.52):
                continue
            # Must close no large hole (rules out clefs, hollow notes, flats, sharps, naturals).
            pad = (~np.pad(piece, 1)).astype(np.uint8)
            hc, hlab, hstats, _ = cv2.connectedComponentsWithStats(pad, connectivity=4)
            if any(hlab[0, 0] != j and hstats[j, cv2.CC_STAT_AREA] >= 0.03 * space * space for j in range(1, hc)):
                continue
            # Eighth / sixteenth rests slant forward from bottom-left to top-right and have a heavy bulb at top-left.
            top_half = piece[:high // 2]
            bot_half = piece[high // 2:]
            top_cols = np.nonzero(top_half)[1]
            bot_cols = np.nonzero(bot_half)[1]
            if len(top_cols) < 5 or len(bot_cols) < 5:
                continue
            # Bottom half must be narrow (a single diagonal tail) and lie left/center of top-right hook.
            bot_widths = bot_half.sum(axis=1)
            bot_widths = bot_widths[bot_widths > 0]
            if not len(bot_widths) or float(np.median(bot_widths)) > 0.38 * space:
                continue
            top_right_x = float(np.percentile(np.nonzero(piece[:max(2, high // 3)])[1], 90)) if piece[:max(2, high // 3)].any() else 0.0
            bot_end_x = float(np.mean(np.nonzero(piece[max(0, high - max(2, high // 4)):])[1])) if piece[max(0, high - max(2, high // 4)):].any() else wide
            if top_right_x - bot_end_x < 0.25 * space:
                continue
            # Top-left bulb has substantial ink mass compared to bottom-right quadrant (which is empty paper).
            tl_mass = float(piece[:high // 2, :max(1, wide // 2)].mean())
            br_mass = float(piece[high // 2:, max(1, wide // 2):].mean())
            if tl_mass < 0.20 or br_mass > 0.14:
                continue
            # Distinguish 16th rest (two stacked bulbs -> taller and ink in middle-left) from 8th rest.
            mid_left = float(piece[int(0.35 * high):int(0.68 * high), :max(1, int(0.55 * wide))].mean())
            is_16th = high >= 2.25 * space and mid_left >= 0.28
            out.append({
                'staff': index, 'x': cx, 'x0': x, 'x1': x + wide, 'top': gy, 'bottom': gy + high,
                'middle': (cy - rows[2]) / space,
                'kind': '16th' if is_16th else 'eighth',
                'length': Fraction(1, 4) if is_16th else Fraction(1, 2),
            })
    return out

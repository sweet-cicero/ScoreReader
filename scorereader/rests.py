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
OUTSIDE = 1.45                       # its middle lies in the staff or at most this many staff spaces outside it
REACH = 0.2                          # a head whose middle lies in the rest, or this many staff spaces outside it, is no note


def _symnet_weights(weights: dict | None = None) -> dict | None:
    """Returns SymNet weights when neural classification is enabled, or None when disabled."""
    if weights is not None:
        return weights
    try:
        from . import classify, headnet
        if headnet.weights() is None:
            return None
        return classify.load_weights()
    except Exception:
        return None


def _overlaps_music(x0: float, x1: float, y0: float, y1: float, space: float,
                    staff_heads: list[dict], staff_bars: list[float],
                    staff_existing: list[dict] | None = None) -> bool:
    """Returns True when a candidate box intersects a barline, notehead, stem, or existing rest."""
    if any(x0 - 0.2 * space <= bx <= x1 + 0.2 * space for bx in staff_bars):
        return True
    if any(x0 <= h['x1'] + 0.15 * space and x1 >= h['x0'] - 0.15 * space
           and y0 <= h['y1'] + 0.2 * space and y1 >= h['y0'] - 0.2 * space
           for h in staff_heads):
        return True
    if any(x0 - 0.25 * space <= s['x'] <= x1 + 0.25 * space
           and y0 <= max(h['cy'], s['end']) and y1 >= min(h['cy'], s['end'])
           for h in staff_heads for s in h.get('stems', [])):
        return True
    if staff_existing and any(
            x0 <= r['x1'] + 0.15 * space and x1 >= r['x0'] - 0.15 * space
            and y0 <= r['bottom'] + 0.2 * space and y1 >= r['top'] - 0.2 * space
            for r in staff_existing):
        return True
    return False


def _bridged_sixteenth_rests(layers: dict, ends: list[float], seen: list[tuple[int, float, float]],
                             sym_w: dict) -> list[dict]:
    """Recovers sixteenth rests fused to a neighboring note by a thin horizontal staff-line bridge.

    Only emits candidates whose unstripped component was oversized so unmerged rests are never duplicated
    with eighth_rests(), allowing reader.py's in_rest() filter to strip phantom heads on the rest.
    """
    from . import classify
    space = layers['space']
    bare = layers['bare'].astype(np.uint8)
    cands: list[dict] = []
    for index, staff in enumerate(layers['staves']):
        rows = staff['rows']
        y0 = max(0, int(rows[0] - 0.8 * space))
        y1 = min(bare.shape[0], int(rows[4] + 0.8 * space) + 1)
        if y1 <= y0:
            continue
        bridge_h = max(3, int(round(staff['thick'] + 2))) | 1
        close_k = np.ones((bridge_h, 1), np.uint8)
        strip = np.ascontiguousarray(bare[y0:y1])
        raw_reg = cv2.morphologyEx(strip, cv2.MORPH_CLOSE, close_k)
        _, rlab, rstats, _ = cv2.connectedComponentsWithStats(raw_reg, connectivity=8)
        # Zero pure thin horizontal staff-line bridges (paper directly above and below the staff line).
        cleaned = strip.copy()
        half_t = max(2, int(round(staff['thick'] / 2.0)) + 2)
        for row_y in rows:
            ry = int(round(row_y - y0))
            r0, r1 = max(0, ry - half_t), min(cleaned.shape[0], ry + half_t + 1)
            if r0 > 0 and r1 < cleaned.shape[0]:
                thin = (cleaned[r0 - 1] == 0) & (cleaned[r1] == 0)
                cleaned[r0:r1, thin] = 0
        s_reg = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, close_k)
        cnt, lab, stats, _ = cv2.connectedComponentsWithStats(s_reg, connectivity=8)
        for k in range(1, cnt):
            x, y, wide, high, _ = (int(v) for v in stats[k])
            if x <= ends[index] + 0.3 * space or x + wide > staff['x1']:
                continue
            if not (0.85 * space <= wide <= 1.55 * space and 2.0 * space <= high <= 3.2 * space):
                continue
            gy = y + y0
            cx, cy = x + wide / 2.0, gy + high / 2.0
            middle = (cy - rows[2]) / space
            if abs(middle) > 1.25:
                continue
            if any(si == index and abs(sx - cx) <= 0.6 * space and abs(sy - cy) <= 1.2 * space for si, sx, sy in seen):
                continue
            piece = lab[y:y + high, x:x + wide] == k
            raw_ids = [int(i) for i in np.unique(rlab[y:y + high, x:x + wide][piece]) if i > 0]
            raw_max_w = max((int(rstats[i][2]) for i in raw_ids), default=0)
            raw_max_h = max((int(rstats[i][3]) for i in raw_ids), default=0)
            if raw_max_w <= 1.60 * space and raw_max_h <= 3.5 * space:
                continue
            if _max_hole_area(piece, space) >= 0.42:
                continue
            cands.append({
                'staff': index, 'x': cx, 'cy': cy, 'x0': x, 'x1': x + wide, 'top': gy, 'bottom': gy + high,
                'middle': middle,
            })
    if not cands:
        return []
    pts = [(c['staff'], float(c['x']), float(c['cy'])) for c in cands]
    probs_all = classify.classify_points(layers, pts, sym_w)
    out: list[dict] = []
    for cand, probs in zip(cands, probs_all):
        p_head = float(probs[0] + probs[1] + probs[2] + probs[3])
        if float(probs[8]) >= 0.96 and p_head < 0.02:
            out.append({
                'staff': cand['staff'], 'x': cand['x'], 'x0': cand['x0'], 'x1': cand['x1'],
                'top': cand['top'], 'bottom': cand['bottom'], 'middle': cand['middle'],
                'kind': '16th', 'length': Fraction(1, 4), 'neural': True, 'prob': float(probs[8]),
            })
    return out


def quarter_rests(layers: dict, ends: list[float], weights: dict | None = None) -> list[dict]:
    """The printed quarter rests of a page: [{'staff', 'x', 'x0', 'x1', 'top', 'bottom', 'middle', 'kind', 'length'}],
    where 'middle' is how many staff spaces the rest's middle lies under the middle line of its staff.
    Closes thin vertical staff-line breaks per staff so printed quarter rests cut by staff lines stay whole."""
    if QUARTER is None:
        return []
    space = layers['space']
    bare = layers['bare'].astype(np.uint8)
    out = []
    seen: list[tuple[int, float, float]] = []

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
            if any(si == index and abs(sx - cx) <= 0.6 * space and abs(sy - at) <= 1.2 * space for si, sx, sy in seen):
                continue
            piece = labels[y:y + high, x:x + wide] == number
            if not _rest_shape(piece, space):
                continue
            seen.append((index, cx, at))
            out.append({'staff': index, 'x': cx, 'x0': x, 'x1': x + wide, 'top': gy, 'bottom': gy + high,
                        'middle': (at - layers['staves'][index]['rows'][2]) / space,
                        'kind': 'quarter', 'length': Fraction(1)})

    # First scan raw bare mask (exact compatibility), then scan staff-line-bridged bare mask for cut rests.
    _scan_mask(bare)
    for index, staff in enumerate(layers['staves']):
        y0 = max(0, int(staff['rows'][0] - (OUTSIDE + 1.8) * space))
        y1 = min(bare.shape[0], int(staff['rows'][4] + (OUTSIDE + 1.8) * space) + 1)
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
            if any(si == index and abs(sx - cx) <= 0.6 * space and abs(sy - at) <= 1.2 * space for si, sx, sy in seen):
                continue
            if _cross_shape(labels[y:y + high, x:x + wide] == number, space):
                seen.append((index, cx, at))
                out.append({'staff': index, 'x': cx, 'x0': x, 'x1': x + wide, 'top': y, 'bottom': y + high,
                            'middle': (at - layers['staves'][index]['rows'][2]) / space,
                            'cross': True, 'kind': 'quarter', 'length': Fraction(1)})
    # Reject clear eighth or sixteenth rests that accidentally pass _rest_shape so they keep their true duration.
    sym_w = _symnet_weights(weights)
    if sym_w is not None and out:
        from . import classify
        pts = [(r['staff'], float(r['x']), float((r['top'] + r['bottom']) / 2.0)) for r in out]
        probs_all = classify.classify_points(layers, pts, sym_w)
        out = [
            rest for rest, probs in zip(out, probs_all)
            if not (not rest.get('cross') and (float(probs[7]) >= 0.85 or float(probs[8]) >= 0.85) and float(probs[6]) < 0.15)
        ]
    if sym_w is not None:
        out = out + _bridged_sixteenth_rests(layers, ends, seen, sym_w)
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


def _block_core(box: np.ndarray, space: float) -> tuple[int, int, float, float]:
    """Computes core column bounds, fill, and squareness, ignoring thin ledger-line wings."""
    high, wide = box.shape
    col_heights = box.sum(axis=0)
    core_cols = np.nonzero(col_heights >= 0.35 * space)[0]
    if len(core_cols) and high >= 0.38 * space:
        cx0, cx1 = int(core_cols[0]), int(core_cols[-1]) + 1
        core_box = box[:, cx0:cx1]
    else:
        cx0, cx1 = 0, wide
        core_box = box
    fill = float(core_box.mean()) if core_box.size else 0.0
    square = float((core_box.sum(axis=0) >= 0.8 * high).mean()) if core_box.size else 0.0
    return cx0, cx1, fill, square


def _block_length(box: np.ndarray, y: int, high: int, rows: list[float], hangs: bool, sits: bool,
                  core_wide: int) -> Fraction:
    """Returns whole-rest (4) or half-rest (2) duration from line attachment and ledger wings."""
    if hangs and not sits:
        return Fraction(4)
    if sits and not hangs:
        return Fraction(2)
    if box.shape[1] > core_wide + 2 and high >= 4:
        top_w = int(box[:2].any(axis=0).sum())
        bot_w = int(box[-2:].any(axis=0).sum())
        if top_w >= bot_w + 3:
            return Fraction(4)
        if bot_w >= top_w + 3:
            return Fraction(2)
    return Fraction(4) if abs(y - rows[1]) < abs(y + high - rows[2]) else Fraction(2)


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
        if not (0.8 * space <= wide <= 3.0 * space and 0.25 * space <= high <= 0.95 * space):
            continue
        at = y + high / 2
        index = next((index for index, staff in enumerate(layers['staves'])
                      if staff['rows'][0] - 2 * space <= at <= staff['rows'][4] + 2 * space
                      and staff['x0'] <= x and x + wide <= staff['x1']), None)
        if index is None or x <= ends[index]:
            continue
        box = ink[y:y + high, x:x + wide]
        middle = (at - layers['staves'][index]['rows'][2]) / space
        if abs(middle) > BLOCK[6] or wide > BLOCK[1] * space:
            cx0, cx1, fill, square = _block_core(box, space)
        else:
            cx0, cx1 = 0, wide
            fill = float(box.mean())
            square = float((box.sum(axis=0) >= 0.8 * high).mean())
        bwide = cx1 - cx0
        bx0, bx1 = x + cx0, x + cx1
        rows = layers['staves'][index]['rows']
        lines = [rows[0] + step * (rows[4] - rows[0]) / 4 for step in range(-2, 7)]
        hangs = any(-HANG[0] * space <= y - line <= HANG[1] * space for line in lines)
        sits = any(SIT[0] * space <= y + high - line <= SIT[1] * space for line in lines)

        def _open_side_clear(is_hanging: bool) -> bool:
            pad_h = max(2, int(round(0.25 * space)))
            cy0, cy1 = (y + high + 1, min(ink.shape[0], y + high + 1 + pad_h)) if is_hanging else (max(0, y - pad_h), y)
            return cy1 > cy0 and float(ink[cy0:cy1, bx0:bx1].mean()) <= 0.12

        # Engraved whole/half rests can be 0.36..0.50 spaces tall; accept crisp rectangles sitting on line 3 or hanging from line 4.
        slim_block = (0.90 * space <= bwide <= 1.80 * space and 0.36 * space <= high < BLOCK[2] * space
                      and fill >= 0.84 and square >= 0.82
                      and ((abs(y - rows[1]) <= 0.18 * space and hangs) or (abs(y + high - rows[2]) <= 0.22 * space and sits)))
        if slim_block and not _open_side_clear(hangs and not sits):
            slim_block = False
        # Accept ledger-line whole and half rests outside the staff up to |middle| <= 3.4.
        ledger_block = (BLOCK[6] < abs(middle) <= 3.4
                        and BLOCK[0] * space <= bwide <= BLOCK[1] * space
                        and 0.42 * space <= high <= BLOCK[3] * space
                        and ((fill >= BLOCK[4] and square >= BLOCK[5]) or (fill >= 0.80 and square >= 0.85))
                        and (hangs or sits))
        if ledger_block and not _open_side_clear(hangs and not sits):
            ledger_block = False
        # Wide handwritten-style whole and half rests up to 2.25 spaces wide.
        wide_block = (BLOCK[1] * space < bwide <= 2.25 * space
                      and 0.44 * space <= high <= BLOCK[3] * space
                      and fill >= 0.88 and square >= 0.85
                      and abs(middle) <= BLOCK[6]
                      and (hangs or sits)
                      and _open_side_clear(hangs and not sits))
        in_staff_block = (BLOCK[0] * space <= bwide <= BLOCK[1] * space
                          and BLOCK[2] * space <= high <= BLOCK[3] * space
                          and fill >= BLOCK[4] and square >= BLOCK[5]
                          and abs(middle) <= BLOCK[6])
        rest = in_staff_block or slim_block or ledger_block or wide_block
        if rest or (measure and wide <= 1.9 * space):
            length = _block_length(box, y, high, rows, hangs, sits, bwide)
            found = {'staff': index, 'x': (bx0 + bx1) / 2, 'x0': bx0, 'x1': bx1, 'top': y, 'bottom': y + high,
                     'middle': middle, 'kind': 'block', 'length': length,
                     'hangs': hangs, 'sits': sits}
            if measure:
                found.update(fill=fill, square=square, wide=bwide / space, high=high / space, rest=rest)
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


def eighth_rests(layers: dict, ends: list[float], heads: list[dict], bars: dict[int, list[float]],
                 weights: dict | None = None) -> list[dict]:
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
            # Reject any candidate that overlaps a barline, notehead bbox, or stem span.
            if _overlaps_music(x, x + wide, gy, gy + high, space, staff_heads, staff_bars):
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
    sym_w = _symnet_weights(weights)
    if sym_w is not None and out:
        from . import classify
        pts = [(r['staff'], float(r['x']), float((r['top'] + r['bottom']) / 2.0)) for r in out]
        probs_all = classify.classify_points(layers, pts, sym_w)
        gated = []
        for rest, probs in zip(out, probs_all):
            p_head = float(probs[0] + probs[1] + probs[2] + probs[3])
            p_rest = float(probs[4] + probs[5] + probs[6] + probs[7] + probs[8])
            if p_head >= 0.45 or p_rest < 0.15:
                continue
            # Reject quarter rests misread as eighth rests so neural_rest_candidates keeps their 1-beat duration.
            if float(probs[6]) >= 0.70 and float(probs[7] + probs[8]) < 0.25:
                continue
            gated.append(rest)
        out = gated
    return out


_NEURAL_REST_MAP = {
    4: ('block', Fraction(4)),
    5: ('block', Fraction(2)),
    6: ('quarter', Fraction(1)),
    7: ('eighth', Fraction(1, 2)),
    8: ('16th', Fraction(1, 4)),
}


def _max_hole_area(piece: np.ndarray, space: float) -> float:
    """Returns the largest interior paper hole area in square staff spaces."""
    pad = (~np.pad(piece, 1)).astype(np.uint8)
    hc, hlab, hstats, _ = cv2.connectedComponentsWithStats(pad, connectivity=4)
    areas = [float(hstats[j, cv2.CC_STAT_AREA]) / (space * space) for j in range(1, hc) if hlab[0, 0] != j]
    return max(areas) if areas else 0.0


def _slim_rest_swing(piece: np.ndarray, space: float) -> bool:
    """Returns True when a slim isolated stroke shows the vertical zig-zag swing of a quarter rest."""
    high, wide = piece.shape
    if high < 8 or wide < 3:
        return False
    rows = [np.nonzero(row)[0] for row in piece]
    rows = [row for row in rows if len(row)]
    if len(rows) < int(0.8 * high):
        return False
    for edge in (np.array([row[0] for row in rows]), np.array([row[-1] for row in rows])):
        if (np.abs(edge - np.median(edge)) <= 0.12 * space).mean() > 0.88:
            return False
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
    return (right - parts[0] >= 0.05 and right - back >= 0.05
            and again - back >= 0.02 and again - min(parts[6], parts[7]) >= 0.04)


def neural_rest_candidates(layers: dict, ends: list[float], heads: list[dict],
                           bars: dict[int, list[float]], existing: list[dict],
                           weights: dict | None = None, threshold: float = 0.85) -> list[dict]:
    """Finds isolated non-head marks and near-miss blocks, and classifies them with local SymNet.

    Uses cross-staff system alignment for mid-confidence candidates and returns an empty list when SymNet
    weights are disabled or unavailable.
    """
    sym_w = _symnet_weights(weights)
    if sym_w is None:
        return []
    from . import classify
    space = layers['space']
    bare = layers['bare'].astype(np.uint8)
    free = layers['free'].astype(np.uint8)
    ink = layers['ink'] > 0
    staves = layers['staves']
    heads_by_staff = {i: [h for h in heads if h['staff'] == i] for i in range(len(staves))}
    existing_by_staff = {i: [r for r in existing if r['staff'] == i] for i in range(len(staves))}
    cands: list[dict] = []

    # Group A: isolated non-head connected components on staff-line-bridged bare ink.
    for index, staff in enumerate(staves):
        rows = staff['rows']
        y0 = max(0, int(rows[0] - 3.2 * space))
        y1 = min(bare.shape[0], int(rows[4] + 3.2 * space) + 1)
        if y1 <= y0:
            continue
        bridge_h = max(3, int(round(staff['thick'] + 2))) | 1
        region = cv2.morphologyEx(np.ascontiguousarray(bare[y0:y1]), cv2.MORPH_CLOSE, np.ones((bridge_h, 1), np.uint8))
        count, labels, stats, _ = cv2.connectedComponentsWithStats(region, connectivity=8)
        sh = heads_by_staff[index]
        sb = bars.get(index, [])
        se = existing_by_staff[index]
        small_frags: list[tuple[int, int, int, int, int]] = []
        for k in range(1, count):
            x, y, wide, high, _ = (int(v) for v in stats[k])
            if x <= ends[index] + 0.2 * space or x + wide > staff['x1']:
                continue
            gy = y + y0
            cx, cy = x + wide / 2.0, gy + high / 2.0
            middle = (cy - rows[2]) / space
            if 0.20 * space <= wide <= 1.25 * space and 0.20 * space <= high < 1.05 * space and abs(middle) <= 2.2:
                if not _overlaps_music(x, x + wide, gy, gy + high, space, sh, sb, se):
                    small_frags.append((x, y, wide, high, k))
                continue
            if not (0.35 * space <= wide <= 1.45 * space and 1.05 * space <= high <= 3.6 * space):
                continue
            if abs(middle) > 3.5:
                continue
            if _overlaps_music(x, x + wide, gy, gy + high, space, sh, sb, se):
                continue
            piece = labels[y:y + high, x:x + wide] == k
            hole_area = _max_hole_area(piece, space)
            if hole_area >= 0.42:
                continue
            has_swing = hole_area < 0.09 and (_slim_rest_swing(piece, space) or _rest_shape(piece, space))
            cands.append({
                'staff': index, 'x': cx, 'cy': cy, 'x0': x, 'x1': x + wide, 'top': gy, 'bottom': gy + high,
                'middle': middle, 'is_block': False, 'hole_area': hole_area, 'has_swing': has_swing,
                'slim_swing': (has_swing and 0.35 * space <= wide <= 0.72 * space
                               and 1.70 * space <= high <= 2.40 * space),
            })
        # Reconnect diagonal eighth rests split in two across a removed staff line without merging adjacent notes.
        small_frags.sort(key=lambda f: (f[1], f[0]))
        used_frags: set[int] = set()
        for fi, (ax, ay, aw, ah, ak) in enumerate(small_frags):
            if fi in used_frags:
                continue
            for fj in range(fi + 1, len(small_frags)):
                if fj in used_frags:
                    continue
                bx, by, bw, bh, bk = small_frags[fj]
                vgap = by - (ay + ah)
                if vgap > 0.42 * space:
                    break
                if vgap < -0.15 * space:
                    continue
                if min(ax + aw, bx + bw) < max(ax, bx) - 0.15 * space:
                    continue
                mx0, mx1 = min(ax, bx), max(ax + aw, bx + bw)
                my0, my1 = min(ay, by), max(ay + ah, by + bh)
                mw, mh = mx1 - mx0, my1 - my0
                if not (0.40 * space <= mw <= 1.35 * space and 1.05 * space <= mh <= 2.45 * space):
                    continue
                mgy0, mgy1 = y0 + my0, y0 + my1
                if _overlaps_music(mx0, mx1, mgy0, mgy1, space, sh, sb, se):
                    continue
                merged_piece = (labels[my0:my1, mx0:mx1] == ak) | (labels[my0:my1, mx0:mx1] == bk)
                if _max_hole_area(merged_piece, space) >= 0.09:
                    continue
                used_frags.add(fi)
                used_frags.add(fj)
                mcx, mcy = (mx0 + mx1) / 2.0, (mgy0 + mgy1) / 2.0
                cands.append({
                    'staff': index, 'x': mcx, 'cy': mcy, 'x0': mx0, 'x1': mx1, 'top': mgy0, 'bottom': mgy1,
                    'middle': (mcy - rows[2]) / space, 'is_block': False, 'hole_area': 0.0, 'slim_swing': False,
                })
                break

    # Group B: near-miss rectangular blocks on free ink (including ledger-line wings and wide blocks).
    count, _, stats, _ = cv2.connectedComponentsWithStats(free, connectivity=8)
    for k in range(1, count):
        x, y, wide, high = (int(v) for v in stats[k][:4])
        if not (0.8 * space <= wide <= 3.0 * space and 0.28 * space <= high <= 1.0 * space):
            continue
        at = y + high / 2.0
        index = next((i for i, staff in enumerate(staves)
                      if staff['rows'][0] - 2.0 * space <= at <= staff['rows'][4] + 2.0 * space
                      and staff['x0'] <= x and x + wide <= staff['x1']), None)
        if index is None or x <= ends[index]:
            continue
        rows = staves[index]['rows']
        middle = (at - rows[2]) / space
        if abs(middle) > 3.5:
            continue
        box = ink[y:y + high, x:x + wide]
        cx0, cx1, fill, square = _block_core(box, space)
        bwide = cx1 - cx0
        bx0, bx1 = x + cx0, x + cx1
        if not (0.80 * space <= bwide <= 2.35 * space and fill >= 0.65 and square >= 0.20):
            continue
        sh = heads_by_staff[index]
        sb = bars.get(index, [])
        se = existing_by_staff[index]
        if _overlaps_music(bx0, bx1, y, y + high, space, sh, sb, se):
            continue
        lines = [rows[0] + step * (rows[4] - rows[0]) / 4 for step in range(-2, 7)]
        hangs = any(-HANG[0] * space <= y - line <= HANG[1] * space for line in lines)
        sits = any(SIT[0] * space <= y + high - line <= SIT[1] * space for line in lines)
        # Reject horizontal slurs hanging directly under the top staff line (rows[0]).
        if hangs and not sits and -2.15 <= middle <= -1.45:
            continue
        cands.append({
            'staff': index, 'x': (bx0 + bx1) / 2.0, 'cy': at, 'x0': bx0, 'x1': bx1, 'top': y, 'bottom': y + high,
            'middle': middle, 'is_block': True, 'hangs': hangs, 'sits': sits,
            'block_length': _block_length(box, y, high, rows, hangs, sits, bwide),
            'has_swing': False, 'slim_swing': False,
        })

    if not cands:
        return []
    pts = [(c['staff'], float(c['x']), float(c['cy'])) for c in cands]
    probs_all = classify.classify_points(layers, pts, sym_w)

    # Pre-score geometry-compatible candidates so cross-staff system alignment can corroborate mid-confidence rests.
    sys_counts = {i: sum(1 for st in staves if st['system'] == staves[i]['system']) for i in range(len(staves))}
    scored: list[tuple[dict, int, float, np.ndarray]] = []
    for cand, probs in zip(cands, probs_all):
        cls_idx = int(np.argmax(probs))
        prob = float(probs[cls_idx])
        if cand['is_block'] and cls_idx not in (4, 5):
            continue
        if not cand['is_block']:
            hole_area = cand.get('hole_area', 0.0)
            if hole_area >= 0.09:
                # Allow curled sixteenth rests with closed loops only at very high SymNet confidence inside the staff.
                if cls_idx == 8 and prob >= 0.95 and abs(cand['middle']) <= 1.85:
                    scored.append((cand, cls_idx, prob, probs))
                continue
            if cls_idx in (7, 8) and abs(cand['middle']) > 1.85:
                continue
            if cls_idx == 6 and sys_counts[cand['staff']] == 1 and not cand.get('has_swing'):
                # On single-staff melody systems, require a quarter-rest zig-zag swing to reject ornament hooks and detached flags.
                continue
            if cls_idx not in (6, 7, 8):
                # Keep slim zig-zag quarter-rest candidates for cross-staff mate rescue when SymNet rules out noteheads.
                p_head = float(probs[0] + probs[1] + probs[2] + probs[3])
                if cand.get('slim_swing') and abs(cand['middle']) <= 0.45 and p_head < 0.20:
                    scored.append((cand, 6, float(probs[6]), probs))
                continue
        scored.append((cand, cls_idx, prob, probs))

    # Build system-level mate tables: high-confidence rests (existing + >= threshold) and mid-confidence candidates.
    high_anchors = list(existing)
    for cand, cls_idx, prob, _ in scored:
        if prob >= threshold:
            kind, _ = _NEURAL_REST_MAP[cls_idx]
            high_anchors.append({'staff': cand['staff'], 'x': cand['x'], 'kind': kind})
    mid_anchors = [
        {'staff': cand['staff'], 'x': cand['x'], 'kind': _NEURAL_REST_MAP[cls_idx][0]}
        for cand, cls_idx, prob, _ in scored
        if prob >= min(threshold, 0.48)
    ]

    def _has_mate(staff_idx: int, x_pos: float, kind: str, pool: list[dict], tol: float) -> bool:
        sys_id = staves[staff_idx]['system']
        return any(
            o['staff'] != staff_idx and staves[o['staff']]['system'] == sys_id
            and o['kind'] == kind and abs(o['x'] - x_pos) <= tol * space
            for o in pool
        )

    found: list[dict] = []
    for cand, cls_idx, prob, probs in scored:
        kind, length = _NEURAL_REST_MAP[cls_idx]
        keep = prob >= threshold
        if not keep and cls_idx == 6 and prob >= min(threshold, 0.56) and abs(cand['middle']) <= 0.35:
            # Accept centered slim quarter rests above 0.56 (0 FPs across zero-rest Clean Dev scores).
            keep = True
        if not keep and prob >= min(threshold, 0.38):
            # Accept rests corroborated directly above or below a high-confidence mate rest on the same system.
            if _has_mate(cand['staff'], cand['x'], kind, high_anchors, 0.85):
                keep = True
        if not keep and prob >= min(threshold, 0.48):
            # Accept mid-confidence rests corroborated by a same-kind mate candidate on the same system.
            if _has_mate(cand['staff'], cand['x'], kind, mid_anchors, 0.95):
                keep = True
        if not keep and cls_idx == 6 and cand.get('slim_swing') and abs(cand['middle']) <= 0.45:
            # Rescue slim zig-zag quarter rests paired directly above or below a high-confidence mate quarter rest.
            p_head = float(probs[0] + probs[1] + probs[2] + probs[3])
            if p_head < 0.20 and _has_mate(cand['staff'], cand['x'], 'quarter', high_anchors, 0.85):
                keep = True
        if not keep:
            continue
        # Prevent duplicate overlapping detections inside this neural batch.
        if any(r['staff'] == cand['staff']
               and cand['x0'] <= r['x1'] + 0.15 * space and cand['x1'] >= r['x0'] - 0.15 * space
               and cand['top'] <= r['bottom'] + 0.2 * space and cand['bottom'] >= r['top'] - 0.2 * space
               for r in found):
            continue
        entry = {
            'staff': cand['staff'], 'x': cand['x'], 'x0': cand['x0'], 'x1': cand['x1'],
            'top': cand['top'], 'bottom': cand['bottom'], 'middle': cand['middle'],
            'kind': kind, 'length': length, 'neural': True, 'prob': prob,
        }
        if cand['is_block']:
            entry['hangs'] = cand['hangs']
            entry['sits'] = cand['sits']
            if cand['hangs'] != cand['sits']:
                entry['length'] = cand['block_length']
        found.append(entry)
    return found

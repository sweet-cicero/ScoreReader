"""Finds the staves of a page image: for each staff, the height of each of its five lines along the page.

No model is used. The method:

1. Keep only long level runs of ink (a morphological opening with a wide, flat kernel). Staff lines stay; note heads,
   stems and most letters go.
2. Measure the page's staff space: the most frequent distance between neighbour lines in narrow bands of the page.
3. In vertical bands of the page, add up the line ink of each row and slide a comb of five teeth over the rows. Where
   all five teeth meet ink and the gaps between them are clean, a staff stands.
4. Link the staves of the bands across the page. The link follows the staff's own slope, so a tilted page and a page
   that bends near the binding are no problem. Pieces of one staff that a weak place separated are joined again.
5. Keep each staff line as points (x, y) with straight pieces between them.
"""
from __future__ import annotations

import cv2
import numpy as np


def ink_mask(grey: np.ndarray) -> np.ndarray:
    """1 where the page is dark. The limit is Otsu's, kept between 110 and 190."""
    limit, _ = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return (grey < min(190, max(110, limit))).astype(np.uint8)


def line_ink(ink: np.ndarray, length: int) -> np.ndarray:
    return cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (length, 1)))


FAINT = (11, 10, 40)    # a pale staff line is a level run of this many px (the last number) that is darker than the
#                         paper over and under it by this many grey levels (the second), and thinner than the first,
#                         in px (None: only dark lines are looked for)

FAINT_EDGE = 1.1        # where both looks find a staff, the dark look's staff counts this many times its line ink


UNEVEN = (1.4, 0.85)    # no staff: its widest gap is this many times its narrowest, and its weakest line has ink in
#                         under this share of its columns (None: off)


def faint_lines(grey: np.ndarray) -> np.ndarray:
    """1 on thin level lines that are too pale for ink_mask(): some copies print the staff in hair lines of grey,
    under notes of full black. A line is looked for by its shape (thin, level, long), not by how dark it is."""
    hat = cv2.morphologyEx(grey, cv2.MORPH_BLACKHAT, np.ones((FAINT[0], 1), np.uint8))
    return line_ink((hat >= FAINT[1]).astype(np.uint8), FAINT[2])


def staff_space(flat: np.ndarray) -> float:
    """The page's staff space in px: the most frequent distance between neighbour lines, 0 when no staff is found."""
    height, width = flat.shape
    band = 80
    votes = np.zeros(80)
    for x0 in range(0, width - band, band):
        profile = flat[:, x0:x0 + band].sum(axis=1)
        rows = np.where(profile >= 0.5 * band)[0]
        if len(rows) < 5:
            continue
        # The middle of each run of rows is a line.
        breaks = np.where(np.diff(rows) > 1)[0]
        starts = np.concatenate([[0], breaks + 1])
        ends = np.concatenate([breaks, [len(rows) - 1]])
        centres = (rows[starts] + rows[ends]) / 2
        steps = np.diff(centres)
        # A staff gives four equal steps in a row.
        for k in range(len(steps) - 3):
            four = steps[k:k + 4]
            if 5 <= four.min() and four.max() < 80 and four.max() - four.min() <= 0.25 * four.mean() + 1:
                votes[int(round(four.mean()))] += 1
    if votes.sum() == 0:
        return 0.0
    best = int(np.argmax(np.convolve(votes, np.ones(3), mode='same')))
    near = np.arange(max(0, best - 1), min(len(votes), best + 2))
    return float((votes[near] * near).sum() / votes[near].sum())


def _band_staves(profile: np.ndarray, width: int, spaces: np.ndarray) -> list[tuple[int, float, float]]:
    """The staves in one band: (top line's row, space, strength), the strongest comb position of each staff."""
    height = len(profile)
    best = np.zeros(height)
    best_space = np.zeros(height)
    for space in spaces:
        offsets = [int(round(k * space)) for k in range(5)]
        reach = height - offsets[-1] - 1
        if reach <= 0:
            continue
        teeth = np.stack([profile[offset:offset + reach] for offset in offsets])
        weakest = teeth.min(axis=0)
        gaps = np.stack([profile[int(round((k + 0.5) * space)):int(round((k + 0.5) * space)) + reach] for k in range(4)])
        score = np.where(weakest >= 0.3 * width, teeth.sum(axis=0) - gaps.sum(axis=0), 0)
        better = score > best[:reach]
        best[:reach][better] = score[better]
        best_space[:reach][better] = space
    found: list[tuple[int, float, float]] = []
    taken: list[int] = []
    for top in np.argsort(-best):
        if best[top] <= 0:
            break
        if all(abs(top - other) > 3 * best_space[top] for other in taken):
            taken.append(int(top))
            found.append((int(top), float(best_space[top]), float(best[top])))
    return sorted(found)


ENDS_ON = (1.5, 0.5, 0.25, 0.8, 2, 3.0, 3)   # a staff's lines are followed on past its found end, window by window
#   (the second number of staff spaces wide), each line at the row where the window before puts it (give or take the
#   third number of a staff space): a window counts where three of the five lines fill this share of it, each with
#   paper half a staff space over or under it; the following ends after the fifth number of windows that do not
#   count (or more windows than the last number that are dark at the lines and beside them: a chord is, and a binding
#   hole is wider). The end moves where the lines go on for the first number of staff spaces or more, and the lines
#   get a point every sixth number of staff spaces. A pencil ring, a paperclip or a binder ring over the start of a
#   staff, a faded stretch or a page that bends there hides the lines from the comb, and the staff began after its
#   clef or ended before its last bar (None: off)
ENDS_SIXTH = 0.5   # the followed lines are one line off where more than this share of the windows that count show
#   it: the first line is not there and a sixth line stands one distance under the last, or the other way round (a
#   piece of another copy is pasted on at other rows, or the comb jumped a line on a page that bends steeply). The
#   five lines are then the other four and the sixth (None: as they were followed)
ENDS_GAPS = (0.65, 1.5)   # the rows that a window finds for the lines of a staff stand in order, each this to this
#   many staff spaces from the next (a page that bends at its spine draws the lines 0.8 to 1.35 staff spaces apart). A
#   found row that does not is left out; a line that the window does not find keeps its distance from the lines that
#   it finds, or stands one distance of the found lines from the next where that distance is none (the comb can end
#   a bent staff with two of its lines on one: the staff was then followed 88 pixels high where it is 112)


def _predict(chain: list[tuple[float, float, float]], x: float) -> float:
    """The top row that the chain expects at x, from the slope of its last points."""
    if len(chain) < 2:
        return chain[-1][1]
    tail = chain[-4:]
    slope = (tail[-1][1] - tail[0][1]) / (tail[-1][0] - tail[0][0])
    return tail[-1][1] + slope * (x - tail[-1][0])


def _extend(chain: list[tuple[float, float, float]], ink: np.ndarray, band: int, step: int, direction: int) -> None:
    """Follows a staff past the end of its chain, to the left (direction -1) or to the right (1). The comb is strict
    and looks only at long runs of ink, so it loses a staff where a copy made the lines weak or broken. Here all the
    ink counts: a line is a row with much more ink than the rows half a space over and under it. Four of the five
    lines are enough, and they must stand where the staff's line of travel puts them."""
    height, width = ink.shape
    space = float(np.median([s for _, _, s in chain]))
    reach = int(max(4, round(0.3 * space)))
    half = int(round(space / 2))
    misses = 0
    while misses < 3:
        end = chain[0] if direction < 0 else chain[-1]
        x = end[0] + direction * step * (misses + 1)
        x0, x1 = int(x - band / 2), int(x + band / 2)
        if x0 < 0 or x1 > width:
            break
        if direction < 0:
            head = chain[:4]
            slope = (head[-1][1] - head[0][1]) / (head[-1][0] - head[0][0]) if len(head) > 1 else 0.0
            expected = head[0][1] + slope * (x - head[0][0])
        else:
            expected = _predict(chain, x)
        profile = ink[:, x0:x1].sum(axis=1).astype(float)
        profile = np.maximum(profile, np.roll(profile, 1))
        best = None
        for shift in range(-reach, reach + 1):
            for own in (space - 0.5, space, space + 0.5):
                rows = [int(round(expected + shift + k * own)) for k in range(5)]
                if rows[0] - half < 0 or rows[-1] + half >= height:
                    continue
                teeth = profile[rows]
                beside = np.array([(profile[row - half] + profile[row + half]) / 2 for row in rows])
                lines = (teeth >= 0.25 * band) & (teeth >= 1.4 * beside + 0.05 * band)
                key = (int(lines.sum()), float((teeth - beside).sum()))
                if best is None or key > best[0]:
                    best = (key, expected + shift, own)
        if best is not None and best[0][0] >= 4:
            point = (x, best[1], best[2])
            if direction < 0:
                chain.insert(0, point)
            else:
                chain.append(point)
            misses = 0
        else:
            misses += 1


def find_staves(grey: np.ndarray) -> list[dict]:
    """The staves from the top of the page. Each: left, right (px), space (px) and lines: five lists of [x, y].

    With FAINT the page is looked at twice: with its dark ink alone, and with its pale level lines too. Where the
    two looks give staves at the same place, the one whose weakest line has the most ink along it is kept (the dark
    look's staff unless the other has FAINT_EDGE times as much): a staff that is one line off has a line without
    ink, and a piece of a staff is shorter than the staff."""
    dark = ink_mask(grey)
    staves = _find(dark, dark)
    if not FAINT:
        return _ends_on(dark, _without_false(line_ink(dark, 25), staves))
    both = dark | faint_lines(grey)
    flat = line_ink(both, 25)
    # The dark look is the surer one: the look with the pale lines wins a place only by a clear margin.
    found = [(_support(flat, staff) * (1.0 if look else FAINT_EDGE), -look, staff)
             for look, group in enumerate((staves, _find(both, dark))) for staff in group]
    kept: list[dict] = []
    for _, _, staff in sorted(found, key=lambda item: item[:2], reverse=True):
        if not any(_same_place(staff, other) for other in kept):
            kept.append(staff)
    kept = _ends_on(both, _without_false(flat, kept))
    return sorted(kept, key=lambda staff: line_y(staff['lines'][0], (staff['left'] + staff['right']) / 2))


def _ends_on(ink: np.ndarray, staves: list[dict]) -> list[dict]:
    """The staves with their lines followed on past both ends (see ENDS_ON). Two pieces of one staff that were
    followed into each other are one staff: the longer one stays."""
    if not ENDS_ON:
        return staves
    moved = False
    for staff in staves:
        lines = [[tuple(point) for point in points] for points in staff['lines']]
        left = _end_on(ink, lines, staff['left'], -1, staff['space'])
        right = _end_on(ink, lines, staff['right'], 1, staff['space'])
        if (left, right) != (staff['left'], staff['right']):
            staff['left'], staff['right'] = left, right
            staff['lines'] = [[[round(x, 1), round(y, 2)] for x, y in points] for points in lines]
            moved = True
    if not moved:
        return staves
    kept: list[dict] = []
    for staff in sorted(staves, key=lambda staff: staff['left'] - staff['right']):
        if not any(_same_place(staff, other) for other in kept):
            kept.append(staff)
    return kept


def _without_false(flat: np.ndarray, staves: list[dict]) -> list[dict]:
    """Drops what is no staff: the level strokes of an ornament, of a title in large type or of the edge of a book
    in a photo. Its five 'lines' stand at uneven gaps, and one of them has ink along a part of its length only.
    Measured on 3,663 staves of 484 scans: all 22 such finds were false; a real staff that a hand ruled unevenly
    (gaps up to 1.35 times) stays."""
    if not UNEVEN:
        return staves
    kept = []
    for staff in staves:
        middle = (staff['left'] + staff['right']) / 2
        rows = [line_y(points, middle) for points in staff['lines']]
        gaps = [low - high for high, low in zip(rows, rows[1:])]
        columns = max(1.0, (staff['right'] - staff['left']) / 4)
        if max(gaps) > UNEVEN[0] * max(1e-6, min(gaps)) and _support(flat, staff) < UNEVEN[1] * columns:
            continue
        kept.append(staff)
    return kept


def _support(flat: np.ndarray, staff: dict) -> int:
    """How many columns (of every fourth) have line ink on the weakest of the staff's five lines."""
    height = flat.shape[0]
    hits = [0] * 5
    for x in range(int(staff['left']), int(staff['right']) + 1, 4):
        for number, points in enumerate(staff['lines']):
            y = int(round(line_y(points, x)))
            hits[number] += bool(0 <= y < height and flat[max(0, y - 2):y + 3, x].any())
    return min(hits)


def _same_place(one: dict, two: dict) -> bool:
    """True when two staves share columns and their rows overlap there."""
    left, right = max(one['left'], two['left']), min(one['right'], two['right'])
    if right <= left:
        return False
    x = (left + right) / 2
    return min(line_y(one['lines'][4], x), line_y(two['lines'][4], x)) > max(line_y(one['lines'][0], x), line_y(two['lines'][0], x))


def _find(ink: np.ndarray, dark: np.ndarray) -> list[dict]:
    """The staves that the line ink of `ink` shows. `dark` is the dark ink alone: what stands on a staff is dark."""
    height, width = ink.shape
    space0 = staff_space(line_ink(ink, 25))
    if space0 <= 0:
        return []
    flat = line_ink(ink, int(max(15, round(1.4 * space0))))
    band = int(max(60, round(6 * space0)))
    step = band // 2
    spaces = np.arange(0.85 * space0, 1.2 * space0 + 0.01, 0.25)
    chains: list[list[tuple[float, float, float]]] = []  # each: (band middle x, top row, space)
    for x0 in range(0, width - band + 1, step):
        profile = flat[:, x0:x0 + band].sum(axis=1).astype(float)
        profile = np.maximum(profile, np.roll(profile, 1))  # a line two rows thick counts on both rows
        middle = x0 + band / 2
        for top, space, _ in _band_staves(profile, band, spaces):
            near = [chain for chain in chains
                    if 0 < middle - chain[-1][0] <= 4 * step and abs(_predict(chain, middle) - top) <= max(5.0, 0.3 * space)]
            if near:
                min(near, key=lambda chain: abs(_predict(chain, middle) - top)).append((middle, top, space))
            else:
                chains.append([(middle, top, space)])
    # Join the pieces of one staff: a chain that starts where another chain's line of travel arrives.
    chains.sort(key=lambda chain: chain[0][0])
    joined: list[list[tuple[float, float, float]]] = []
    for chain in chains:
        target = None
        for other in joined:
            gap = chain[0][0] - other[-1][0]
            if 0 < gap <= 14 * step and abs(_predict(other, chain[0][0]) - chain[0][1]) <= max(6.0, 0.45 * chain[0][2]):
                target = other
                break
        if target is not None:
            target.extend(chain)
        else:
            joined.append(list(chain))
    chains = [chain for chain in joined if len(chain) >= 4]
    for chain in chains:
        _extend(chain, ink, band, step, -1)
        _extend(chain, ink, band, step, 1)
    chains.sort(key=lambda chain: float(np.median([top for _, top, _ in chain])))
    staves = []
    for chain in chains:
        space = float(np.median([s for _, _, s in chain]))
        lines = []
        for k in range(5):
            points = []
            for middle, top, own_space in chain:
                guess = top + k * own_space
                y0 = int(round(guess))
                x0, x1 = int(middle - band / 2), int(middle + band / 2)
                reach = int(max(2, round(0.3 * space)))
                first_row = max(0, y0 - reach)
                window = flat[first_row:y0 + reach + 1, x0:x1].sum(axis=1).astype(float)
                if len(window) == 0 or window.max() < 0.2 * band:
                    # A weak or broken line: all the ink of the rows shows it.
                    window = ink[first_row:y0 + reach + 1, x0:x1].sum(axis=1).astype(float)
                if len(window) == 0 or window.max() < 0.2 * band:
                    points.append((middle, float(guess)))
                    continue
                weights = window * (window >= 0.6 * window.max())
                points.append((middle, first_row + float((weights * np.arange(len(window))).sum() / weights.sum())))
            lines.append(points)
        # The staff's ends: the first and last column with ink on at least three of its lines.
        first, last = int(max(0, chain[0][0] - band)), int(min(width, chain[-1][0] + band))
        columns = _line_columns(ink, lines, first, last, space)
        if not columns:
            continue
        # Stray ink past the end does not count: the staff ends where the columns with ink stop being dense.
        columns = np.array(columns)
        dense = [x for x in columns if ((columns >= x - 40) & (columns <= x + 40)).sum() >= 40]
        if not dense:
            continue
        columns = [dense[0], dense[-1]]
        staves.append({'left': int(columns[0]), 'right': int(columns[-1]), 'space': space,
                       'lines': [[[round(x, 1), round(y, 2)] for x, y in points] for points in lines]})
    # What stands on a staff is dark: pale lines beside the rows of a pale staff are no music.
    return [staff for staff in _without_twins(staves) if not _blank(dark, staff)]


def _line_columns(ink: np.ndarray, lines: list, first: int, last: int, space: float) -> list[int]:
    """The columns from first up to last with ink on at least three of the five lines, without the wide dark ones."""
    height = ink.shape[0]
    columns = []
    solid = []
    for x in range(first, last):
        hits = 0
        rows = [line_y(points, x) for points in lines]
        for y in rows:
            y = int(round(y))
            hits += bool(0 <= y < height and ink[max(0, y - 2):y + 3, x].any())
        if hits < 3:
            continue
        columns.append(x)
        # Dark all the way down: a bar line when it is thin, something else when it is wide (the shadow of a
        # binding hole at the staff's end, for example).
        between = sum(bool(ink[int(round((a + b) / 2)), x]) for a, b in zip(rows, rows[1:])
                      if 0 <= int(round((a + b) / 2)) < height)
        if between >= 3:
            solid.append(x)
    wide = set()
    run: list[int] = []
    for x in solid + [10 ** 9]:
        if run and x - run[-1] > 1:
            if len(run) > 0.6 * space:
                wide.update(run)
            run = []
        run.append(x)
    return [x for x in columns if x not in wide]


def _line_rows(found: list, guess: list, space: float):
    """The five rows of a staff in a window, from the rows that were found for some of its lines (None: not found)
    and the rows that the window before expects (see ENDS_GAPS). The found rows that do not stand in order at the
    distance of a staff's lines are set to None in found. None where fewer than three lines are left."""
    have = [(number, float(row)) for number, row in enumerate(found) if row is not None]
    if not ENDS_GAPS:
        if len(have) < 3:
            return None
        move = float(np.median([row - guess[number] for number, row in have]))
        return [float(row) if row is not None else own + move for row, own in zip(found, guess)]

    def fits(first: int, top: float, second: int, bottom: float) -> bool:
        return ENDS_GAPS[0] * space * (second - first) <= bottom - top <= ENDS_GAPS[1] * space * (second - first)

    best, even = None, 0.0
    for mask in range(1, 1 << len(have)):
        some = [item for bit, item in enumerate(have) if mask >> bit & 1]
        if len(some) < 3 or (best is not None and len(some) < len(best)):
            continue
        if not all(fits(*one, *other) for one, other in zip(some, some[1:])):
            continue
        spread = float(np.std([(other[1] - one[1]) / (other[0] - one[0]) for one, other in zip(some, some[1:])]))
        if best is None or len(some) > len(best) or spread < even:
            best, even = some, spread
    if best is None:
        return None
    rows = dict(best)
    for number in range(5):
        if number not in rows:
            found[number] = None
    gap = float(np.median([(other[1] - one[1]) / (other[0] - one[0]) for one, other in zip(best, best[1:])]))
    move = float(np.median([row - guess[number] for number, row in best]))
    for number in sorted(set(range(5)) - set(rows), key=lambda number: min(abs(number - own) for own in rows)):
        near = min(rows, key=lambda other: abs(other - number))
        own = guess[number] + move
        if not (fits(near, rows[near], number, own) if near < number else fits(number, own, near, rows[near])):
            own = rows[near] + gap * (number - near)
        rows[number] = own
    return [rows[number] for number in range(5)]


def _end_on(ink: np.ndarray, lines: list, end: int, direction: int, space: float) -> int:
    """The end of a staff with its lines followed on (see ENDS_ON), to the left (direction -1) or to the right (1).
    Where the end moves, the lines get the points that were followed."""
    height, width = ink.shape
    wide = int(max(4, round(ENDS_ON[1] * space)))
    reach = int(max(2, round(ENDS_ON[2] * space)))
    half = int(round(space / 2))
    rows = [line_y(points, end) for points in lines]
    near = lines[0][:2] if direction < 0 else lines[0][-2:]
    slope = (near[1][1] - near[0][1]) / (near[1][0] - near[0][0]) if len(near) > 1 else 0.0
    seen: list[tuple] = []   # the middle of each window that counts, the row of each line there, a sixth line
    x, misses, dark, far = end, 0, 0, end
    beyond = [0, 0]   # the windows with a sixth line over the staff, and under it
    while misses < ENDS_ON[4] and dark <= ENDS_ON[6]:
        x0, x1 = (x - wide, x) if direction < 0 else (x + 1, x + 1 + wide)
        if x0 < 0 or x1 > width:
            break
        guess = [row + slope * direction * wide for row in rows]

        def line_at(row: float):
            """Whether the window is filled at this row (give or take the reach), and the row of the line there
            (None where it is no thin line)."""
            first, last = int(round(row)) - reach, int(round(row)) + reach + 1
            if first < 1 or last >= height - 1:
                return False, None
            strip = ink[first - 1:last + 1, x0:x1].astype(int)
            fill = np.maximum(strip[1:-1], strip[:-2]).sum(axis=1)   # a line two rows thick fills both rows
            best = int(np.argmin(np.abs(np.arange(len(fill)) - reach) - 1000 * (fill >= ENDS_ON[3] * wide)))
            if fill[best] < ENDS_ON[3] * wide:
                return False, None
            # A line is thin: paper half a staff space over it or under it.
            beside = [int(ink[first + best + side * half, x0:x1].sum()) for side in (-1, 1)
                      if 0 <= first + best + side * half < height]
            return True, (first + best if beside and min(beside) < 0.5 * wide else None)

        looks = [line_at(row) for row in guess]
        found = [row for _, row in looks]
        filled = sum(full for full, _ in looks)
        fitted = _line_rows(found, guess, space)
        if fitted is None and filled >= 3:
            # Dark at the lines and beside them: the heads of a chord, a bar line, a brace. The lines go on behind
            # it, at their slope.
            rows = guess
            dark += 1
        elif fitted is not None:
            moves = [new - own for new, own, row in zip(fitted, guess, found) if row is not None]
            slope += 0.3 * direction * float(np.median(moves)) / wide
            rows = fitted
            # A staff has five lines. Where its first line is not there and a sixth one stands under its last (or
            # the other way round), the rows are one line off: a piece of another copy is pasted on at other rows,
            # or the comb jumped a line on a page that bends.
            sixth = [line_at(2 * rows[0] - rows[1])[1], line_at(2 * rows[4] - rows[3])[1]]
            seen.append(((x0 + x1 - 1) / 2, list(rows), sixth))
            if found[4] is None and sixth[0] is not None:
                beyond[0] += 1
            if found[0] is None and sixth[1] is not None:
                beyond[1] += 1
            misses, dark, far = 0, 0, (x0 if direction < 0 else x1 - 1)
        else:
            rows = guess
            misses += 1
        x = x0 if direction < 0 else x1 - 1
    if abs(far - end) < ENDS_ON[0] * space:
        return end
    seen = [item for item in seen if (item[0] - far) * direction <= 0]
    if ENDS_SIXTH and max(beyond) > ENDS_SIXTH * len(seen):
        # One line off: the five lines are the other four and the sixth.
        if beyond[0] > beyond[1]:
            seen = [(at, [float(sixth[0]) if sixth[0] is not None else 2 * rows[0] - rows[1]] + rows[:4], sixth)
                    for at, rows, sixth in seen]
        else:
            seen = [(at, rows[1:] + [float(sixth[1]) if sixth[1] is not None else 2 * rows[4] - rows[3]], sixth)
                    for at, rows, sixth in seen]
    # A point for each stretch of the way, at its middle: the middle row of the windows there.
    count = int(max(1, round(ENDS_ON[5] * space / wide)))
    pieces = [seen[k:k + count] for k in range(0, len(seen), count)]
    if len(pieces) > 1 and len(pieces[-1]) < count / 2:
        pieces[-2:] = [pieces[-2] + pieces[-1]]
    for piece in pieces:
        middle = round(float(np.mean([item[0] for item in piece])), 1)
        for number, points in enumerate(lines):
            point = (middle, float(np.median([item[1][number] for item in piece])))
            if direction < 0:
                points.insert(0, point)
            else:
                points.append(point)
    return int(far)


def _blank(ink: np.ndarray, staff: dict) -> bool:
    """True for a staff without music: ruled lines that nobody wrote on. Measured on the test pages: a blank staff
    has other ink than its lines in 0 % of its columns, and the emptiest staff with music in 8 %."""
    space = staff['space']
    width = staff['right'] - staff['left']
    marked = 0
    looked = 0
    for x in range(int(staff['left'] + 0.03 * width), int(staff['right'] - 0.03 * width), 2):
        rows = [line_y(points, x) for points in staff['lines']]
        y0 = max(0, int(rows[0] - space))
        column = ink[y0:int(rows[4] + space), x].copy()
        for y in rows:
            at = int(round(y)) - y0
            column[max(0, at - 3):at + 4] = 0
        marked += column.sum() >= 0.3 * space
        looked += 1
    return looked > 0 and marked / looked < 0.02


def _without_twins(staves: list[dict]) -> list[dict]:
    """Drops a staff that lies over another staff (the comb can lock one line up or down): the longer one stays."""
    kept: list[dict] = []
    for staff in sorted(staves, key=lambda s: s['left'] - s['right']):
        middle = (staff['left'] + staff['right']) / 2
        top, bottom = line_y(staff['lines'][0], middle), line_y(staff['lines'][4], middle)
        twin = False
        for other in kept:
            if staff['right'] < other['left'] or staff['left'] > other['right']:
                continue
            x = min(max(middle, other['left']), other['right'])
            other_top, other_bottom = line_y(other['lines'][0], x), line_y(other['lines'][4], x)
            own_top, own_bottom = line_y(staff['lines'][0], x), line_y(staff['lines'][4], x)
            overlap = min(own_bottom, other_bottom) - max(own_top, other_top)
            if overlap > 0.5 * (bottom - top):
                twin = True
                break
        if not twin:
            kept.append(staff)
    return sorted(kept, key=lambda s: line_y(s['lines'][0], (s['left'] + s['right']) / 2))


def line_y(points: list, x: float) -> float:
    """The height of a staff line at x: straight pieces between the points, and the end pieces go on straight."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if len(xs) > 1 and x <= xs[0]:
        return ys[0] + (ys[1] - ys[0]) * (x - xs[0]) / (xs[1] - xs[0])
    if len(xs) > 1 and x >= xs[-1]:
        return ys[-1] + (ys[-1] - ys[-2]) * (x - xs[-1]) / (xs[-1] - xs[-2])
    return float(np.interp(x, xs, ys))


def draw(grey: np.ndarray, staves: list[dict]) -> np.ndarray:
    """The page in colour with each staff line drawn in red and each staff's number at its left."""
    colour = cv2.cvtColor(grey, cv2.COLOR_GRAY2BGR)
    for number, staff in enumerate(staves, 1):
        for points in staff['lines']:
            for x in range(staff['left'], staff['right']):
                y = int(round(line_y(points, x)))
                if 0 <= y < colour.shape[0]:
                    colour[max(0, y - 1):y + 2, x] = (0, 0, 255)
        y = int(line_y(staff['lines'][4], staff['left']))
        cv2.putText(colour, str(number), (max(0, staff['left'] - 130), y), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 8)
    return colour

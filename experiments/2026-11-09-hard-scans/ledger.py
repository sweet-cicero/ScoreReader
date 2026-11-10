#!/usr/bin/env python3
"""The ledger rule: a note just under or over the staff stands on a ledger line when a short level line crosses its
head, whatever its distance from the staff.

A reader that learned from engraved music takes the pitch of a note from its distance to the staff. A copyist who
draws by hand often puts the first ledger line too near the staff, so the reader takes a C under the treble staff for
a D. The line through the head tells the two apart, and it does not depend on the distance.

measure() looks, in the rows of the head, for a level run of ink that passes the middle of the head and reaches well
past it on both sides, but is much shorter than a staff line. A head drawn as a slanted stroke, a stem and a slur give
no such run. The staff's own outer line is found at the note's column, so a tilted or bent staff is no problem.
"""
import numpy as np

REACH = 0.8    # the run must reach this many staff spaces to each side of the head's middle
LONGEST = 2.0  # and no more than this many: a longer run is a staff line
ROWS = 0.3     # rows looked at: this many staff spaces over and under the head's middle (a line at the head's edge is the next note's)
CLEAR = 0.3    # the run must be this many staff spaces outside the staff's outer line


def ink_of(image):
    """True where the page is dark. The limit is Otsu's, kept between 110 and 180."""
    grey = np.asarray(image)
    counts = np.bincount(grey.ravel(), minlength=256).astype(float)
    total = counts.sum()
    levels = np.arange(256)
    weight = np.cumsum(counts)
    mean = np.cumsum(counts * levels)
    with np.errstate(divide='ignore', invalid='ignore'):
        between = (mean[-1] * weight - mean * total) ** 2 / (weight * (total - weight))
    limit = int(np.nanargmax(between))
    return grey < min(180, max(110, limit))


def outer_line(ink, x, guess, sp, below):
    """The row of the staff's outer line (the bottom line when below, else the top line) at column x, or None.
    A staff line has ink on most of the columns near x, and other staff lines stand one and two spaces inside it."""
    x0, x1 = max(0, int(x - 4 * sp)), min(ink.shape[1], int(x + 4 * sp))
    first, last = max(0, int(guess - 1.6 * sp)), min(ink.shape[0] - 1, int(guess + 1.6 * sp))
    if x1 - x0 < 2 or last <= first:
        return None
    density = ink[first:last + 1, x0:x1].mean(axis=1)
    density = np.maximum(density, np.roll(density, 1))
    rows = range(len(density) - 1, -1, -1) if below else range(len(density))
    inward = -1 if below else 1
    for row in rows:
        if density[row] < 0.6:
            continue
        inside = 0
        for step in (1, 2):
            at = row + inward * int(round(step * sp))
            near = density[max(0, at - 2):at + 3] if 0 <= at < len(density) else np.array([])
            inside += bool(len(near) and near.max() >= 0.5)
        if inside == 2 or (inside == 1 and density[row] >= 0.8):
            return first + row
    return None


def measure(ink, box, staff_y0, staff_y1, sp, below):
    """(reach to the left, reach to the right) in staff spaces of the best level run of ink through the head, in the
    rows outside the staff: the run whose shorter side is longest, among the runs that are not staff lines."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    line = outer_line(ink, cx, staff_y1 if below else staff_y0, sp, below)
    if line is None:
        line = staff_y1 if below else staff_y0
    best = (0.0, 0.0)
    first, last = int(round(cy - ROWS * sp)), int(round(cy + ROWS * sp))
    for row in range(max(0, first), min(ink.shape[0] - 1, last + 1)):
        if (row < line + CLEAR * sp) if below else (row > line - CLEAR * sp):
            continue
        dark = ink[row] | ink[row + 1]  # a run may be two rows thick and not quite level
        centre = int(round(cx))
        seeds = [x for x in range(int(cx - 0.3 * sp), int(cx + 0.3 * sp) + 1) if 0 <= x < len(dark) and dark[x]]
        if not seeds:
            continue
        seed = min(seeds, key=lambda x: abs(x - centre))
        left = seed
        while left > 0 and dark[left - 1]:
            left -= 1
        right = seed
        while right + 1 < len(dark) and dark[right + 1]:
            right += 1
        reach = ((cx - left) / sp, (right - cx) / sp)
        if max(reach) > LONGEST:
            continue
        if min(reach) > min(best):
            best = reach
    return best


def apply(rd, image, mode='both'):
    """Corrects the staff position of the notes just outside the staff in a copisteria reading. Returns the changes.
    mode 'out': only moves a note from beside the staff onto the ledger line (when a ledger line crosses its head);
    mode 'in': only the other way (when no line crosses it); mode 'both': both."""
    ink = ink_of(image)
    changed = []
    for sym in rd.layout.syms:
        token = rd.tok.get(sym.i)
        if not token or not str(token['cls']['v']).startswith('note') or sym.staff < 0:
            continue
        pos = token['pos']['v']
        if abs(pos) not in (5, 6):
            continue
        staff = rd.layout.staves[sym.staff]
        left, right = measure(ink, sym.box, staff.y0, staff.y1, staff.sp, below=pos < 0)
        ledger = min(left, right) >= REACH
        wanted = (6 if ledger else 5) * (1 if pos > 0 else -1)
        if wanted == pos or (mode == 'out' and not ledger) or (mode == 'in' and ledger):
            continue
        token['pos']['v'] = wanted
        changed.append({'i': sym.i, 'box': [round(float(v), 1) for v in sym.box], 'from': pos, 'to': wanted,
                        'reach': [round(left, 2), round(right, 2)]})
    return changed

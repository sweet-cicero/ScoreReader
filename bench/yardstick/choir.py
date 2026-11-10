"""Rules that come from how choir scores are written. No model is used.

tenor_clef: in a system of three or more staves, the staff over the bass staff is the tenors' when it has a treble
clef. Tenors sing an octave under a treble clef. Some scores print a small 8 under that clef and many do not, and a
reader that takes the clef as plain treble writes the whole part an octave too high. The rule makes the clef a treble
clef with the 8 under it. A system of two staves is left alone: there the upper staff is the women's.
"""
from __future__ import annotations

from collections import Counter


def _clef(rd, staff_index: int) -> str | None:
    """The clef of a staff: the one that most of its bars with a clef read. (A bar without a clef of its own reads
    None, which means "as before".)"""
    seen = Counter()
    for bar in rd.layout.staves[staff_index].bars:
        token = rd.tok.get(bar)
        if token and 'clef' in token and token['clef']['v']:
            seen[token['clef']['v']] += 1
    return seen.most_common(1)[0][0] if seen else None


def tenor_clef(rd) -> list[int]:
    """Changes a copisteria reading in place. Returns the indexes of the staves that became tenor staves."""
    changed = []
    for system in rd.layout.systems:
        if len(system.staves) < 3:
            continue
        clefs = [_clef(rd, index) for index in system.staves]
        if clefs[-1] != 'F4' or clefs[-2] != 'G2':
            continue
        staff_index = system.staves[-2]
        for bar in rd.layout.staves[staff_index].bars:
            token = rd.tok.get(bar)
            if token and 'clef' in token and token['clef']['v'] == 'G2':
                token['clef']['v'] = 'G2_8b'
        for sym in rd.layout.syms:
            token = rd.tok.get(sym.i)
            if sym.staff == staff_index and token and token['cls']['v'] == 'clef_G2':
                token['cls']['v'] = 'clef_G2_8b'
        changed.append(staff_index)
    return changed

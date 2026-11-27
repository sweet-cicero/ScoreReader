#!/usr/bin/env python3
"""Comprehensive in-repo unit and synthetic regression test suite for scoreread.

Needs no external private scans. Covers music grammar bugs, MusicXML validity, rests,
time signatures, tied barline accidentals, C-clefs, multi-page joining, multi-verse lyrics,
and multi-DPI synthetic score reading.

Usage:
  $PY bench/test_suite.py
"""
from __future__ import annotations

import os
import sys
import traceback
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scorereader.hymn import join_pages
from scorereader.music import build_staff, musicxml, pitch_of
from scorereader.page import clean_page, flat_paper
from scorereader.reader import read_page
from scorereader.staves import find_staves
from scorereader.systems import find_systems, lost_staves


def _dummy_staff(space: float = 20.0) -> dict:
    return {'rows': [100.0 + k * space for k in range(5)], 'x0': 100, 'x1': 1500, 'space': space, 'thick': 2.0,
            'system': 0, 'number': 0, 'top': 40, 'bottom': 260}


def _dummy_head(x: float, place: float, hollow: bool = False, direction: str | None = 'up', tails: int = 0,
                dot: bool = False, sign: int | None = None, tie_start: bool = False, tie_stop: bool = False) -> dict:
    stems = [{'direction': direction, 'x': x + (10 if direction == 'up' else -10), 'end': 80.0}] if direction else []
    head = {
        'x0': int(x - 10), 'x1': int(x + 10), 'y0': 100, 'y1': 120, 'cx': float(x), 'cy': 110.0,
        'place': float(place), 'hollow': hollow, 'stems': stems,
        'tails': {direction: tails} if direction else {}, 'dot': dot,
        'tie_start': tie_start, 'tie_stop': tie_stop,
    }
    if sign is not None:
        head['sign'] = sign
    return head


def test_tied_accidental_across_barline() -> None:
    """An accidental on a note tied across a bar line stays active on the second tied note."""
    staff = _dummy_staff()
    heads = [
        _dummy_head(300, -3, hollow=True, sign=1, tie_start=True),   # F#4 half note, tied across bar
        _dummy_head(500, -3, hollow=False, sign=None, tie_stop=True),  # F4 quarter note, tied stop -> MUST be F#4
        _dummy_head(600, -3, hollow=False, sign=None),                 # F4 quarter note after tie -> natural F4
    ]
    bars = [400.0]
    built = build_staff(staff, heads, bars, 'G', 0, 20.0)
    assert len(built) == 2, f'expected 2 bars, got {len(built)}'
    bar1_f = built[0][0]
    bar2_tied, bar2_next = built[1][0], built[1][1]
    assert (bar1_f['step'], bar1_f['alter']) == ('F', 1), f'bar 1 note wrong: {bar1_f}'
    assert (bar2_tied['step'], bar2_tied['alter']) == ('F', 1), (
        f'tied note across bar line lost its sharp: alter={bar2_tied["alter"]}')
    assert (bar2_next['step'], bar2_next['alter']) == ('F', 0), (
        f'following untied note in bar 2 should revert to key signature: alter={bar2_next["alter"]}')


def test_musicxml_chord_cursor_unequal_lengths() -> None:
    """MusicXML writes valid durations and backup offsets when a chord has two different note lengths."""
    note_hi = {'onset': Fraction(0), 'length': Fraction(1), 'voice': 1, 'step': 'C', 'alter': 0, 'octave': 5, 'midi': 72}
    note_lo = {'onset': Fraction(0), 'length': Fraction(3), 'voice': 1, 'step': 'E', 'alter': 0, 'octave': 4, 'midi': 64}
    note_v1_next = {'onset': Fraction(1), 'length': Fraction(1), 'voice': 1, 'step': 'D', 'alter': 0, 'octave': 5, 'midi': 74}
    note_v2 = {'onset': Fraction(0), 'length': Fraction(2), 'voice': 2, 'step': 'C', 'alter': 0, 'octave': 4, 'midi': 60}
    parts = [[{'notes': [note_hi, note_lo, note_v1_next, note_v2], 'clef': 'G', 'key': 0}]]
    xml_text = musicxml(parts, 'chord-test')
    root = ET.fromstring(xml_text)
    measure = root.find('.//measure')
    divisions = int(measure.findtext('.//divisions'))
    # Walk MusicXML timeline exactly as a standard parser does
    pos = Fraction(0)
    last_on = Fraction(0)
    seen = []
    for el in measure:
        if el.tag == 'backup':
            pos -= Fraction(int(el.findtext('duration')), divisions)
        elif el.tag == 'forward':
            pos += Fraction(int(el.findtext('duration')), divisions)
        elif el.tag == 'note':
            dur = Fraction(int(el.findtext('duration')), divisions)
            if el.find('chord') is not None:
                on = last_on
            else:
                on = pos
                last_on = pos
                pos += dur
            seen.append((el.findtext('voice'), el.findtext('pitch/step'), on, dur))
    assert ('1', 'D', Fraction(1), Fraction(1)) in seen, f'D5 onset wrong: {seen}'
    assert ('2', 'C', Fraction(0), Fraction(2)) in seen, f'voice 2 C4 onset wrong (backup drift): {seen}'


def test_musicxml_rests_and_time_signature() -> None:
    """build_staff() and musicxml() handle rests with exact onsets and emit <time> attributes."""
    staff = _dummy_staff()
    heads = [
        _dummy_head(300, 0, hollow=False),  # B4 quarter at onset 0
        _dummy_head(500, 1, hollow=False),  # C5 quarter after quarter rest -> onset 2
    ]
    rests = [{'x': 400.0, 'length': Fraction(1), 'voice': 1, 'staff': 0}]
    built = build_staff(staff, heads, [], 'G', 0, 20.0, rests=rests)
    notes = built[0]
    pitches = [n for n in notes if not n.get('rest')]
    rest_evs = [n for n in notes if n.get('rest')]
    assert len(rest_evs) == 1 and rest_evs[0]['onset'] == Fraction(1), f'bad rest event: {notes}'
    assert pitches[0]['onset'] == Fraction(0) and pitches[1]['onset'] == Fraction(2), f'onset ignored rest: {pitches}'
    xml_text = musicxml([[{'notes': notes, 'clef': 'G', 'key': 0, 'time': (4, 4, None)}]], 'rest-time-test')
    assert '<rest/>' in xml_text, 'MusicXML missing <rest/>'
    assert '<beats>4</beats><beat-type>4</beat-type>' in xml_text, 'MusicXML missing <time>'


def test_c_clef_pitch() -> None:
    """Alto C-clef maps middle line (place 0) to C4."""
    step, alter, octave, midi = pitch_of(0, 'C', 0)
    assert (step, alter, octave, midi) == ('C', 0, 4, 60), f'C-clef middle line wrong: {(step, alter, octave, midi)}'


def test_join_pages_mixed_staff_counts() -> None:
    """join_pages() aligns parts by clef when page 1 has [G, F] and page 2 has solo [F]."""
    p1 = {'parts': [
        [{'notes': [{'step': 'G'}], 'clef': 'G', 'key': 0}],
        [{'notes': [{'step': 'C'}], 'clef': 'F', 'key': 0}],
    ], 'names': {}}
    p2 = {'parts': [
        [{'notes': [{'step': 'D'}], 'clef': 'F', 'key': 0}],
    ], 'names': {}}
    parts, _ = join_pages([p1, p2])
    assert len(parts) == 2
    assert len(parts[0]) == 2 and parts[0][0]['clef'] == 'G' and parts[0][1]['notes'] == [], f'treble got bass notes: {parts[0]}'
    assert len(parts[1]) == 2 and parts[1][0]['clef'] == 'F' and parts[1][1]['notes'][0]['step'] == 'D', f'bass misaligned: {parts[1]}'


def test_multi_verse_lyrics() -> None:
    """set_under() keeps verse 1 and verse 2 under the same staff instead of dropping verse 2."""
    from scorereader.lyrics import set_under
    staves = [_dummy_staff()]
    bands = [
        {'top': 210, 'bottom': 230, 'x0': 100, 'x1': 1500},
        {'top': 240, 'bottom': 260, 'x0': 100, 'x1': 1500},
    ]
    n0 = {'staff': 0, 'x': 300.0, 'voice': 1, 'midi': 67, 'onset': Fraction(0), 'length': Fraction(1), 'step': 'G', 'alter': 0, 'octave': 4}
    pn0 = dict(n0)
    result = {'layers': {'staves': staves, 'words': bands, 'space': 20.0}, 'notes': [n0], 'part_notes': [pn0]}
    syllables = [
        {'band': (0, 0), 'x0': 290.0, 'x1': 315.0, 'text': 'Lord', 'join': False},
        {'band': (0, 1), 'x0': 290.0, 'x1': 315.0, 'text': 'Save', 'join': False},
    ]
    set_under(result, syllables, 0)
    assert n0.get('lyric') == 'Lord', f'verse 1 missing: {n0}'
    assert n0.get('lyrics') == [(1, 'Lord', 'single'), (2, 'Save', 'single')], f'verse 2 dropped: {n0}'
    xml_text = musicxml([[{'notes': [pn0], 'clef': 'G', 'key': 0}]], 'verses')
    assert '<lyric number="1">' in xml_text and '<lyric number="2">' in xml_text, f'MusicXML missing verse 2:\n{xml_text}'


def test_multi_dpi_synthetic_staves_and_notes() -> None:
    """Staves and basic notes read cleanly at 180 DPI (space=12) and 400 DPI (space=28), not just 300 DPI."""
    from bench.drawn_check import LENGTHS, MUSIC, NAMES, draw
    for space in (12, 20, 28):
        grey = draw(space=space)
        staves = find_staves(grey)
        assert len(staves) == 2, f'space={space}: expected 2 staves, got {len(staves)}'
        systems = find_systems(grey, staves)
        staves, systems = lost_staves(grey, staves, systems)
        assert [len(s) for s in systems] == [2], f'space={space}: bad systems {systems}'
        page, places = clean_page(grey, staves, systems)
        result = read_page(page, places)
        for idx, symbols in enumerate(MUSIC):
            want = [(NAMES[idx][p], LENGTHS[k]) for p, k in symbols if k != '|']
            got = [(f"{n['step']}{n['octave']}", n['length'])
                   for n in sorted((n for n in result['notes'] if n['staff'] == idx), key=lambda n: n['x'])]
            assert got == want, f'space={space} staff {idx + 1}: got {got} != want {want}'


TESTS = [
    test_tied_accidental_across_barline,
    test_musicxml_chord_cursor_unequal_lengths,
    test_musicxml_rests_and_time_signature,
    test_c_clef_pitch,
    test_join_pages_mixed_staff_counts,
    test_multi_verse_lyrics,
    test_multi_dpi_synthetic_staves_and_notes,
]


def main() -> int:
    passed = failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f'PASS {fn.__name__}')
            passed += 1
        except Exception as exc:
            print(f'FAIL {fn.__name__}: {exc}')
            traceback.print_exc(limit=3)
            failed += 1
    print(f'\nSummary: {passed}/{len(TESTS)} passed, {failed} failed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

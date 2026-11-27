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


def test_end_to_end_synthetic_meter_and_rests() -> None:
    """Reads a synthetic engraved score with 4/4 meter, half rest, quarter rest, and exact shifted onsets."""
    from PIL import Image, ImageDraw, ImageFont
    space = 24
    w, h = 2100, 620
    img = np.full((h, w), 255, np.uint8)
    y_top = 180
    rows = [y_top + k * space for k in range(5)]
    x0, x1 = 160, 1920
    for y in rows:
        cv2.line(img, (x0, y), (x1, y), 0, 2)
    cv2.line(img, (x0, rows[0]), (x0, rows[4]), 0, 3)
    cv2.line(img, (x1, rows[0]), (x1, rows[4]), 0, 3)

    # Render treble clef + 4/4 time signature + quarter rest using NotoMusic & NotoSerif
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    music_font = Path('/usr/share/fonts/noto/NotoMusic-Regular.ttf')
    serif_font = Path('/usr/share/fonts/noto/NotoSerif-Bold.ttf')
    assert music_font.exists() and serif_font.exists(), 'required open system fonts missing'
    f_music = ImageFont.truetype(str(music_font), int(4.0 * space))
    f_digit = ImageFont.truetype(str(serif_font), int(2.7 * space))
    draw.text((x0 + int(1.6 * space), rows[2] - int(0.1 * space)), '\U0001D11E', font=f_music, fill=0, anchor='mm')
    draw.text((x0 + int(4.4 * space), rows[1]), '4', font=f_digit, fill=0, anchor='mm')
    draw.text((x0 + int(4.4 * space), rows[3]), '4', font=f_digit, fill=0, anchor='mm')
    # Quarter rest in bar 1 beat 2
    qrest_x = x0 + int(12.5 * space)
    draw.text((qrest_x, rows[2]), '\U0001D13D', font=f_music, fill=0, anchor='mm')
    img = np.array(pil)

    def put_quarter(x: int, place: int) -> None:
        cy = int(round(rows[2] - place * space / 2))
        cv2.ellipse(img, (x, cy), (int(0.62 * space), int(0.45 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)
        sx = x + int(0.56 * space) if place <= 0 else x - int(0.56 * space)
        sy2 = cy - int(3.3 * space) if place <= 0 else cy + int(3.3 * space)
        cv2.line(img, (sx, cy), (sx, sy2), 0, 3)

    # Bar 1: G4 (beat 0), quarter rest (beat 1), A4 (beat 2), B4 (beat 3)
    put_quarter(x0 + int(8.0 * space), -2)
    put_quarter(x0 + int(17.0 * space), -1)
    put_quarter(x0 + int(22.0 * space), 0)
    bar1_x = x0 + int(26.5 * space)
    cv2.line(img, (bar1_x, rows[0]), (bar1_x, rows[4]), 0, 3)
    # Bar 2: C5 half note (beats 0..2), half rest sitting on line 3 (beats 2..4)
    cx2, cy2 = x0 + int(31.0 * space), int(round(rows[2] - 1 * space / 2))
    cv2.ellipse(img, (cx2, cy2), (int(0.65 * space), int(0.46 * space)), -20, 0, 360, 0, -1, cv2.LINE_AA)
    cv2.ellipse(img, (cx2, cy2), (int(0.42 * space), int(0.22 * space)), -20, 0, 360, 255, -1, cv2.LINE_AA)
    cv2.line(img, (cx2 - int(0.58 * space), cy2), (cx2 - int(0.58 * space), cy2 + int(3.3 * space)), 0, 3)
    hrest_x = x0 + int(39.0 * space)
    cv2.rectangle(img, (hrest_x - int(0.6 * space), rows[2] - int(0.48 * space)),
                  (hrest_x + int(0.6 * space), rows[2]), 0, -1)

    staves = find_staves(img)
    assert len(staves) == 1, f'expected 1 staff, got {len(staves)}'
    systems = find_systems(img, staves)
    page, places = clean_page(img, staves, systems)
    result = read_page(page, places)
    assert result['meter'] == (4, 4, None), f'expected (4, 4, None), got {result["meter"]}'
    assert '<beats>4</beats><beat-type>4</beat-type>' in result['musicxml'], 'missing <time> 4/4'
    assert '<rest/>' in result['musicxml'], 'missing <rest/> in MusicXML'
    bar0 = [(n['step'], n['onset'], n['length']) for n in result['notes'] if n['bar'] == 0]
    assert bar0 == [('G', 0.0, 1.0), ('A', 2.0, 1.0), ('B', 3.0, 1.0)], f'bar 1 shifted onsets wrong: {bar0}'
    bar1_rests = [r for r in result['parts'][0][1]['notes'] if r.get('rest')]
    assert len(bar1_rests) == 1 and bar1_rests[0]['length'] == Fraction(2), f'bar 2 half rest wrong: {result["parts"][0][1]}'


def test_local_neural_models_and_grammar() -> None:
    """Offline SymNet, StemNet, TimeNet, and global grammar solver run in pure NumPy and fix an ambiguous bar."""
    from scorereader.classify import load_stem_weights, load_time_weights, load_weights
    from scorereader.grammar import solve_system_durations

    assert load_weights() is not None, 'scorereader/symnet.npz missing'
    assert load_stem_weights() is not None, 'scorereader/stemnet.npz missing'
    assert load_time_weights() is not None, 'scorereader/timenet.npz missing'

    # Construct a 4/4 bar where one voice misread a half note (2) as a quarter (1), while SymNet + bar sum say half (2).
    sym_hollow = np.zeros(19, dtype=np.float32)
    sym_hollow[1] = 0.92
    sym_hollow[0] = 0.08
    sym_filled = np.zeros(19, dtype=np.float32)
    sym_filled[0] = 0.95
    sym_filled[1] = 0.05
    bar = [
        [{'x': 100.0, 'place': 0, 'voice': 1, 'length': Fraction(1), 'stem_x': 110.0, 'head': {'hollow': False, 'symnet': sym_hollow}}],
        [{'x': 200.0, 'place': 1, 'voice': 1, 'length': Fraction(1), 'stem_x': 210.0, 'head': {'hollow': False, 'symnet': sym_filled}}],
        [{'x': 300.0, 'place': 2, 'voice': 1, 'length': Fraction(1), 'stem_x': 310.0, 'head': {'hollow': False, 'symnet': sym_filled}}],
    ]
    bar2 = [
        [{'x': 450.0, 'place': 0, 'voice': 1, 'length': Fraction(4), 'stem_x': None, 'head': {'hollow': True}}],
    ]
    plans = {0: [bar, bar2]}
    changed = solve_system_durations(plans, {0: [380.0]}, 20.0, rests=[], meter=(4, 4, None), is_first_system=False)
    assert changed >= 1, 'grammar solver failed to fix ambiguous 4/4 bar'
    assert bar[0][0]['length'] == Fraction(2), f'expected first note corrected to 2, got {bar[0][0]["length"]}'


TESTS = [
    test_tied_accidental_across_barline,
    test_musicxml_chord_cursor_unequal_lengths,
    test_musicxml_rests_and_time_signature,
    test_c_clef_pitch,
    test_join_pages_mixed_staff_counts,
    test_multi_verse_lyrics,
    test_multi_dpi_synthetic_staves_and_notes,
    test_end_to_end_synthetic_meter_and_rests,
    test_local_neural_models_and_grammar,
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

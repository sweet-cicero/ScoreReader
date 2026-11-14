"""Reads a clean page with the reader's own symbol step: no model, no network, only rules on the ink.

The steps: the layers of the ink (scoreread.layers), the symbols on them (scoreread.symbols), the clef and the key
signature at the start of each staff (scoreread.starts), the sharps, flats and naturals before a note
(scoreread.signs), the ties (scoreread.ties), and the music rules that turn the symbols into notes (scoreread.music).

The yardstick (bench/yardstick, copisteria's network) gives the same kind of result for the same clean page, so the
two can be measured side by side on the test kit. Nothing of it is loaded here.
"""
from __future__ import annotations

import numpy as np

from .drone import letter_marks
from .layers import read_layers
from .meter import mid_signs
from .music import MIDDLE, agree_lengths, bar_sums, build_staff, full_sum, held, musicxml, staff_columns
from . import music as _music
from .rests import in_rest, quarter_rests
from .signs import bar_signs, note_signs
from .starts import read_start, read_starts
from .symbols import bar_lines, bar_marks, faint_bars, big_holes, count_tails, dots, hole_heads, loops_have_flags, lost_stems, read_symbols, \
    thin_heads, without_flag_loops, without_joints
from .ties import read_ties
from .triplets import mark_triplets
from .words import cut_stems, word_bands

SIGNS = 'strokes'
TIMES = True         # the numbers of a time signature in the middle of a staff are no notes (scoreread.meter)
CHECK = True         # the music check: the voices of a system agree on the lengths (scoreread.music.agree_lengths)
OCTAVE = 0.4         # a treble staff with a small 8 under its clef sounds an octave lower, when this share of the staves at
                     # its place in the systems show the 8 (scoreread.starts.octave_mark); None: the 8 is not read
TENORS = 2.5         # a number: a treble staff over the bass staff is the tenors' only when its notes do not sound this many
                     # places under the notes of the bass staff (the middle note of each); None: always the tenors'


def page_starts(grey: np.ndarray, places: list[dict]) -> list[dict]:
    """A first look at a clean page: what the start of each staff shows (its clef and its key signature), for the
    vote of all pages of a hymn on its key (scoreread.starts.hymn_key)."""
    if not places:
        return []
    layers = read_layers(grey, places)
    layers['words'] = word_bands(layers)
    return [read_start(layers, index) for index in range(len(layers['staves']))]


def read_page(grey: np.ndarray, places: list[dict], title: str = '', key_before: int | None = None,
              clefs_before: list[str] | None = None, key_hymn: int | None = None) -> dict:
    """Reads a clean page (a grey image and the places from clean_page()). Returns {'musicxml': text, 'notes': [...],
    'staves': n, 'systems': n, 'key': n, 'clefs': [...], 'layers': the layers}, and what was found on the way
    ('heads', 'bars', 'starts', 'ends', 'signs', 'note_signs', 'keys', 'ties', 'times', 'rests') for pictures and checks.
    `key_before` is the key of the page before in the same hymn: a page that shows no key signature has that key.
    `clefs_before` are the clefs of the staves of a system on that page, and `key_hymn` is the key that the staves
    of all pages of the hymn voted for together (see scoreread.starts).

    'key' is the key of the page, and 'staff_keys' the key of each staff (a page with two pieces has two keys).

    Each note: 'staff', 'bar', 'onset' and 'length' (quarter notes, the onset from the bar's start), 'voice', 'step',
    'alter', 'octave', 'midi', 'x', 'place' (0 is the middle line, +1 a step up), 'agreed' (the music check changed
    its length), 'votes' (how the voices voted on its steps), 'tie_start' and 'tie_stop' (a tie begins or ends at
    the note; the tied notes stay two notes, as in MusicXML) and 'mark': what the note was read from (the size and
    place of the head, hollow or filled, its hole, its dot, its sign, its stems and their flags or beams).

    The words are read after the notes, for the whole hymn at once (scoreread.lyrics): 'part_notes' holds, for each
    note of 'notes', the same note in 'parts', so that a syllable can be set under both."""
    if not places:
        # A page of words only, or of another notation (Byzantine neumes): it holds no staff, so no notes.
        return {'musicxml': musicxml([[]], title), 'parts': [[]], 'notes': [], 'part_notes': [], 'title': title, 'staves': 0, 'systems': 0, 'key': 0, 'clefs': [],
                'layers': None, 'heads': [], 'note_signs': [], 'starts': [], 'ends': [], 'bars': {}, 'signs': [],
                'keys': [], 'staff_keys': [], 'ties': [], 'words': [], 'triplets': [], 'rests': [], 'times': []}
    layers = read_layers(grey, places)
    # The rows of the words: a stem ends where they begin, and a letter under a head is no stem.
    words = layers['words'] = word_bands(layers)
    symbols = read_symbols(layers)
    heads = symbols['heads']
    space = layers['space']
    staves = layers['staves']
    begin = read_starts(layers, key_before, clefs_before, key_hymn)
    big = big_holes(layers, [head for head in heads if head['cx'] > begin['ends'][head['staff']] + 0.3 * space])
    if big is not None:
        # A second look: paper that a slur closes in is no inside of a head, and the page is read without it.
        layers = read_layers(grey, places, big)
        words = layers['words'] = word_bands(layers)
        symbols = read_symbols(layers)
        heads = symbols['heads']
        staves = layers['staves']
        begin = read_starts(layers, key_before, clefs_before, key_hymn)
    system_clefs = {staff['number']: clef for staff, clef in zip(staves, begin['clefs'])}
    key, clefs, ends, keys = begin['key'], list(begin['clefs']), begin['ends'], begin['keys']
    # Notes begin after the clef and the key signature.
    heads = [head for head in heads if head['cx'] > ends[head['staff']] + 0.3 * space]
    # A printed quarter rest is no note: its thick middle was read as a head and its thin strokes as a stem.
    rests = quarter_rests(layers, ends)
    heads = [head for head in heads if not in_rest(head, rests, space)]
    bars = bar_lines(layers, heads)
    # A stem can cross the whole staff as a bar line does, but a head hangs on it.
    for index in bars:
        stems = [stem['x'] for head in heads if head['staff'] == index for stem in head['stems']]
        bars[index] = [x for x in bars[index] if all(abs(x - stem) > 0.4 * space for stem in stems)]
    # A sign that stands against a bar line was read as a small hollow head with the bar line as its stem.
    at_bars = bar_signs(layers, heads)
    for sign in at_bars:
        bars[sign['staff']] = sorted(bars[sign['staff']] + [sign['bar']])
    heads = [head for head in heads if not any(head is sign['mark'] for sign in at_bars)]
    # The paper that a tie closes in where it crosses a bar line was read as a low hollow head on that line. The
    # line is a bar line unless a true head hangs on it: the loop of a flag closes in paper at its stem too.
    crossed = bar_marks(layers, heads)
    heads = [head for head in heads if not any(head is mark for mark in crossed)]
    for mark in crossed:
        at = mark['stems'][0]['x']
        if all(abs(at - x) > 0.4 * space for x in bars[mark['staff']]) and not any(
                head['staff'] == mark['staff'] and head['x0'] - 0.2 * space <= at <= head['x1'] + 0.2 * space
                for head in heads):
            bars[mark['staff']] = sorted(bars[mark['staff']] + [float(at)])
    # The bar lines of a faint print, broken into dashes: the staves of a system agree on them.
    for index, found in faint_bars(layers, heads, bars).items():
        bars[index] = sorted(bars[index] + found)
    lost_stems(layers, heads, bars, ends,
               [head for head in symbols['orphans'] if head['cx'] > ends[head['staff']] + 0.3 * space
                and not in_rest(head, rests, space)])
    heads = without_joints(heads, space)
    heads += thin_heads(layers, heads, bars, ends)
    # A hollow head read from its hole; where the copy broke its rim, it replaces the pieces of the rim.
    from_holes = hole_heads(layers, heads, ends, bars, symbols['signs'])
    from_holes = [head for head in from_holes if not any(head is mark for mark in bar_marks(layers, from_holes))]
    gone = {id(other) for head in from_holes for other in head.get('replaces', [])}
    heads = [head for head in heads if id(head) not in gone] + from_holes
    # The numbers of a new time signature are no notes.
    times = mid_signs(layers, ends, bars) if TIMES else {}
    if TIMES:
        heads = [head for head in heads if not any(sign['x0'] - 0.2 * space <= head['cx'] <= sign['x1'] + 0.2 * space
                                                   for sign in times[head['staff']])]
    # (The other finders of heads can find the sign at the bar line again.)
    heads = [head for head in heads
             if not any(sign['staff'] == head['staff'] and sign['x0'] - 0.2 * space <= head['cx'] <= sign['x1'] + 0.2 * space
                        and sign['top'] - 0.3 * space <= head['cy'] <= sign['bottom'] + 0.3 * space and head is not sign['head']
                        for sign in at_bars)]
    # (The other finders of heads can find a rest again.)
    heads = [head for head in heads if not in_rest(head, rests, space)]
    for head in heads:
        head['staff_ref'] = staves[head['staff']]
    # A stem ends where the words begin.
    cut_stems(layers, heads, words)
    count_tails(layers, heads)
    loops_have_flags(layers, heads)
    heads = without_flag_loops(heads, space)
    dots(layers, heads)
    # The notes under the bracket of a triplet are two thirds as long as they are drawn.
    triplets = mark_triplets(layers, heads)
    # A sharp, a flat or a natural before a head changes that note. Two readers look for it: the strokes of the sign
    # (a thin sign of a hand), and its thick mark (a printed sign).
    found = []
    if 'strokes' in SIGNS:
        for index in range(len(staves)):
            for sign in note_signs(layers, index, heads, ends[index]):
                if any(time['x0'] - 0.2 * space <= (sign['x0'] + sign['x1']) / 2 <= time['x1'] + 0.2 * space
                       for time in times.get(index, [])):
                    continue
                sign['head']['sign'] = {'sharp': 1, 'flat': -1, 'natural': 0}[sign['kind']]
                found.append(sign)
        gone = {id(head) for sign in found for head in sign['drop']} - {id(sign['head']) for sign in found}
        heads = [head for head in heads if id(head) not in gone]
        for sign in at_bars:
            if any(sign['head'] is head for head in heads):
                sign['head']['sign'] = {'flat': -1, 'natural': 0}[sign['kind']]
                found.append(sign)
    if 'marks' in SIGNS:
        for head in heads:
            for sign in symbols['signs']:
                if sign['staff'] == head['staff'] and 0 <= head['x0'] - sign['x1'] <= 1.5 * space \
                        and abs(sign['place'] - head['place']) <= 1.0 and sign['x0'] > ends[head['staff']]:
                    head['sign'] = {'sharp': 1, 'flat': -1, 'natural': 0}[sign['kind']]
    # A tie: a bow from a head to the next head of its pitch.
    ties = read_ties(layers, heads)
    # Choir rule: in a system of three or more staves, a treble staff over the bass staff is the tenors'.
    width = max(staff['number'] for staff in staves) + 1
    if width >= 3:
        low = {staff['system']: clefs[index] for index, staff in enumerate(staves) if staff['number'] == width - 1}
        tenors = [index for index, staff in enumerate(staves)
                  if staff['number'] == width - 2 and clefs[index] == 'G' and low.get(staff['system']) == 'F']
        if TENORS is not None and tenors:
            # The staves of a system stand in the order of their voices: a staff whose notes would sound under
            # the notes of the bass staff is no tenors' staff (the altos have it, and the tenors stand on the
            # bass staff with the basses).
            own = [MIDDLE['G8vb'] + head['place'] for head in heads if head['staff'] in tenors]
            under = [MIDDLE['F'] + head['place'] for head in heads
                     if staves[head['staff']]['number'] == width - 1 and clefs[head['staff']] == 'F']
            if own and under and np.median(own) < np.median(under) - TENORS:
                tenors = []
        for index in tenors:
            clefs[index] = 'G8vb'
    # A small 8 under a treble clef says it outright: the staff sounds an octave lower. The same staff of every
    # system has the same clef, so its staves vote (a copy loses the 8 on one system more easily than it gains one).
    if OCTAVE is not None:
        for number in range(width):
            own = [index for index, staff in enumerate(staves) if staff['number'] == number and clefs[index] in ('G', 'G8vb')]
            marked = [index for index in own if begin['starts'][index].get('eight')]
            if marked and len(marked) >= OCTAVE * len(own):
                for index in own:
                    clefs[index] = 'G8vb'
    parts = [[] for _ in range(width)]
    notes, part_notes = [], []
    plans = {index: staff_columns(staff, [head for head in heads if head['staff'] == index], bars[index], space)
             for index, staff in enumerate(staves)}
    # Music check: the voices of a system agree on the length of each step from column to column.
    agreed = 0
    if CHECK:
        systems = [{index: plans[index] for index, staff in enumerate(staves) if staff['system'] == system}
                   for system in sorted({staff['system'] for staff in staves})]
        # The sum that most bars of the page have: a bar with one open step is as long (scoreread.music.BAR_FULL).
        # On a page whose bars keep their length, a bar that is too long is looked at too (scoreread.music.BAR_OVER).
        sums = [value for own in systems for value in bar_sums(own, bars, space, rests)]
        full, steady = full_sum(sums), full_sum(sums, _music.BAR_OVER) if _music.BAR_OVER else None
        for own in systems:
            agreed += agree_lengths(own, bars, space, rests, full, steady)
    # The ison of a chant page (one staff for the melody): the letters over the staff name its note (scoreread.drone).
    # It is a part of its own after the melody; its notes are in no list of notes, so no syllable is set under them.
    drone, holding = [], {}
    for index, staff in enumerate(staves):
        built = build_staff(staff, [], bars[index], clefs[index], keys[index], space, plans[index])
        if width == 1 and built:
            marks = [[] for _ in built]
            for mark in letter_marks(layers, index, clefs[index]):
                later = [number for number, bar in enumerate(plans[index]) if any(column[0]['x'] >= mark['x'] - 0.6 * space for column in bar)]
                marks[later[0] if later else len(built) - 1].append(mark)

            def pitch(event: dict, staff=staff, index=index) -> dict:
                return build_staff(staff, [], [], clefs[index], keys[index], space, [[[dict(event, voice=1)]]])[0][0]

            for bar in held(built, marks, pitch, space, holding):
                drone.append({'notes': [{name: value for name, value in note.items() if name != 'head'} for note in bar],
                              'clef': clefs[index], 'key': keys[index]})
        for number, bar in enumerate(built):
            parts[staff['number']].append({'notes': bar, 'clef': clefs[index], 'key': keys[index]})
            for note in bar:
                head = note.pop('head')
                part_notes.append(note)
                stem = next((s for s in head['stems'] if (s['direction'] == 'up') == (note['voice'] == 1)), None)
                notes.append(dict(note, staff=index, bar=number, onset=float(note['onset']), length=float(note['length']),
                                  agreed=note.get('agreed', False), votes=note.get('votes'),
                                  mark={'wide': int(head['x1'] - head['x0'] + 1), 'high': int(head['y1'] - head['y0'] + 1),
                                        'y': float(head['cy']), 'at': float(head['place']), 'hollow': bool(head['hollow']),
                                        'hole': float(head.get('hole', 0)), 'core': head.get('core'), 'alt': head.get('alt'), 'thin': bool(head.get('thin')), 'dot': bool(head.get('dot')), 'triplet': bool(head.get('triplet')),
                                        'sign': head.get('sign'), 'stems': [s['direction'] for s in head['stems']],
                                        'stem': {'x': float(stem['x']), 'end': float(stem['end']), 'tails': head['tails'].get(stem['direction'], 0),
                                                 'marks': stem.get('marks', [])} if stem else None}))
    names = {}
    if any(bar['notes'] for bar in drone):
        parts.append(drone)
        names[width] = 'Ison'
    return {'musicxml': musicxml(parts, title, names), 'parts': parts, 'names': names, 'notes': notes, 'part_notes': part_notes, 'title': title,
            'staves': len(staves), 'systems': len({staff['system'] for staff in staves}), 'key': key, 'clefs': clefs, 'layers': layers,
            'system_clefs': [system_clefs[number] for number in sorted(system_clefs)],
            'heads': heads, 'note_signs': found, 'starts': begin['starts'], 'ends': ends, 'bars': bars, 'signs': symbols['signs'],
            'keys': [start['key'] for start in begin['starts']], 'staff_keys': keys, 'ties': ties, 'words': words, 'triplets': triplets,
            'rests': rests, 'times': [([start['time']] if start.get('time') else []) + times.get(index, [])
                      for index, start in enumerate(begin['starts'])]}

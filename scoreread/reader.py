"""Reads a clean page with the reader's own symbol step: no model, no network, only rules on the ink.

read_page() gives the same kind of result as scoreread.engine.read_page() (the copisteria step), so the two can be
measured side by side on the test kit.
"""
from __future__ import annotations

import numpy as np

from .layers import read_layers
from .music import build_staff, musicxml
from .signs import note_signs
from .starts import read_starts
from .symbols import bar_lines, dots, read_symbols, tails, thin_heads

SIGNS = 'strokes'


def read_page(grey: np.ndarray, places: list[dict], title: str = '') -> dict:
    """Reads a clean page (a grey image and the places from clean_page()). Returns {'musicxml': text, 'notes': [...],
    'staves': n, 'systems': n, 'key': n, 'clefs': [...], 'layers': the layers}."""
    layers = read_layers(grey, places)
    symbols = read_symbols(layers)
    heads = symbols['heads']
    space = layers['space']
    staves = layers['staves']
    begin = read_starts(layers)
    key, clefs, ends = begin['key'], list(begin['clefs']), begin['ends']
    # Notes begin after the clef and the key signature.
    heads = [head for head in heads if head['cx'] > ends[head['staff']] + 0.3 * space]
    bars = bar_lines(layers, heads)
    # A stem can cross the whole staff as a bar line does, but a head hangs on it.
    for index in bars:
        stems = [stem['x'] for head in heads if head['staff'] == index for stem in head['stems']]
        bars[index] = [x for x in bars[index] if all(abs(x - stem) > 0.4 * space for stem in stems)]
    heads += thin_heads(layers, heads, bars, ends)
    for head in heads:
        head['staff_ref'] = staves[head['staff']]
        head['tails'] = {stem['direction']: tails(layers, head, stem) for stem in head['stems']}
    dots(layers, heads)
    # A sharp, a flat or a natural before a head changes that note. Two readers look for it: the strokes of the sign
    # (a thin sign of a hand), and its thick mark (a printed sign).
    found = []
    if 'strokes' in SIGNS:
        for index in range(len(staves)):
            for sign in note_signs(layers, index, heads, ends[index]):
                sign['head']['sign'] = {'sharp': 1, 'flat': -1, 'natural': 0}[sign['kind']]
                found.append(sign)
        gone = {id(head) for sign in found for head in sign['drop']} - {id(sign['head']) for sign in found}
        heads = [head for head in heads if id(head) not in gone]
    if 'marks' in SIGNS:
        for head in heads:
            for sign in symbols['signs']:
                if sign['staff'] == head['staff'] and 0 <= head['x0'] - sign['x1'] <= 1.5 * space \
                        and abs(sign['place'] - head['place']) <= 1.0 and sign['x0'] > ends[head['staff']]:
                    head['sign'] = {'sharp': 1, 'flat': -1, 'natural': 0}[sign['kind']]
    # Choir rule: in a system of three or more staves, a treble staff over the bass staff is the tenors'.
    width = max(staff['number'] for staff in staves) + 1
    if width >= 3:
        low = {staff['system']: clefs[index] for index, staff in enumerate(staves) if staff['number'] == width - 1}
        for index, staff in enumerate(staves):
            if staff['number'] == width - 2 and clefs[index] == 'G' and low.get(staff['system']) == 'F':
                clefs[index] = 'G8vb'
    parts = [[] for _ in range(width)]
    notes = []
    for index, staff in enumerate(staves):
        own = [head for head in heads if head['staff'] == index]
        for number, bar in enumerate(build_staff(staff, own, bars[index], clefs[index], key, space)):
            parts[staff['number']].append({'notes': bar, 'clef': clefs[index], 'key': key})
            for note in bar:
                head = note.pop('head')
                stem = next((s for s in head['stems'] if (s['direction'] == 'up') == (note['voice'] == 1)), None)
                notes.append(dict(note, staff=index, bar=number, onset=float(note['onset']), length=float(note['length']),
                                  mark={'wide': int(head['x1'] - head['x0'] + 1), 'high': int(head['y1'] - head['y0'] + 1),
                                        'y': float(head['cy']), 'at': float(head['place']), 'hollow': bool(head['hollow']),
                                        'hole': float(head.get('hole', 0)), 'thin': bool(head.get('thin')), 'dot': bool(head.get('dot')),
                                        'sign': head.get('sign'), 'stems': [s['direction'] for s in head['stems']],
                                        'stem': {'x': float(stem['x']), 'end': float(stem['end']), 'tails': head['tails'].get(stem['direction'], 0),
                                                 'marks': stem.get('marks', [])} if stem else None}))
    return {'musicxml': musicxml(parts, title), 'notes': notes, 'staves': len(staves),
            'systems': len({staff['system'] for staff in staves}), 'key': key, 'clefs': clefs, 'layers': layers,
            'heads': heads, 'note_signs': found, 'starts': begin['starts'], 'ends': ends, 'bars': bars, 'signs': symbols['signs'],
            'keys': [start['key'] for start in begin['starts']]}

"""Turns the symbols of a page (scoreread.symbols) into music: pitches, voices, onsets, and MusicXML. No model is used.

- Pitch: the clef gives the note name of each pitch place, the key signature and the accidentals of the bar give
  its sharp or flat.
- Voices: on a staff of two parts, the upper part's stems go up and the lower part's stems go down. So a note with
  its stem up is voice 1 and a note with its stem down is voice 2. A head with both stems is in both voices.
- Onsets: notes that sound together stand in one column. Inside a bar, each column begins when the voices that
  sing in it are free. So one wrong length moves only the rest of its own bar.
"""
from __future__ import annotations

from fractions import Fraction
from xml.sax.saxutils import escape

STEPS = 'CDEFGAB'
SEMITONES = [0, 2, 4, 5, 7, 9, 11]
SHARPS = [3, 0, 4, 1, 5, 2, 6]      # the note names that the sharps of a key signature raise, in their order: F C G D A E B
FLATS = [6, 2, 5, 1, 4, 0, 3]       # and the flats: B E A D G C F
MIDDLE = {'G': 34, 'G8vb': 27, 'F': 22}   # the note on the middle line of each clef, as 7 * octave + name
TYPES = {Fraction(4): 'whole', Fraction(2): 'half', Fraction(1): 'quarter', Fraction(1, 2): 'eighth',
         Fraction(1, 4): '16th', Fraction(1, 8): '32nd'}
DIVISIONS = 8
ONE_LINE = 0.6       # the stems of two voices on one pitch, or a second apart, are one line: at most this far apart
BESIDE = 1.8         # a whole note beside a note with a stem, on its pitch or a second from it, is at most this far from it
BESIDE_DOT = 2.6     # or this far, at the right of a note with a dot
COLUMN = 0.75        # two notes of two voices sound together when their heads are at most this many staff spaces apart


def key_alters(key: int) -> dict[int, int]:
    """The sharp or flat that a key signature gives each note name: key > 0 counts sharps, key < 0 flats."""
    alters = {}
    for name in (SHARPS[:key] if key > 0 else FLATS[:-key] if key < 0 else []):
        alters[name] = 1 if key > 0 else -1
    return alters


def pitch_of(place: int, clef: str, alter: int) -> tuple[str, int, int, int]:
    """(step, alter, octave, midi) of a pitch place under a clef."""
    diatonic = MIDDLE[clef] + place
    octave, name = divmod(diatonic, 7)
    return STEPS[name], alter, octave, 12 * (octave + 1) + SEMITONES[name] + alter


def length_of(head: dict, tails: int) -> Fraction:
    """The length of a note in quarter notes, from its head, its stem, its flags or beams and its dot."""
    if head['hollow']:
        base = Fraction(2) if head['stems'] else Fraction(4)
    else:
        base = Fraction(1) / (2 ** tails)
    return base * Fraction(3, 2) if head.get('dot') else base


def build_staff(staff: dict, heads: list[dict], bars: list[float], clef: str, key: int, space: float) -> list[list[dict]]:
    """The bars of a staff: each a list of notes {'onset', 'length', 'voice', 'step', 'alter', 'octave', 'midi', 'x',
    'type', 'dot'} with onsets counted from the bar's start, in quarter notes."""
    events = []
    for head in heads:
        place = int(round(head['place']))
        voices = sorted({1 if stem['direction'] == 'up' else 2 for stem in head['stems']}) or [1]
        for voice in voices:
            stem = next((s for s in head['stems'] if (s['direction'] == 'up') == (voice == 1)), None)
            events.append({'x': head['cx'], 'place': place, 'voice': voice, 'head': head,
                           'length': length_of(head, head['tails'].get(stem['direction'], 0) if stem else 0),
                           'stem_x': stem['x'] if stem else None})
    events.sort(key=lambda event: event['x'])
    # A note without a stem (a whole note) under, over or beside a note with a stem is the other voice's note, and
    # the two begin together. Two voices on one pitch, or a second apart, stand side by side: the whole note at the
    # right, after the dot of the other note.
    for event in events:
        if event['stem_x'] is not None:
            continue
        near = []
        for other in events:
            if other['stem_x'] is None:
                continue
            ahead, apart = (event['x'] - other['x']) / space, abs(other['place'] - event['place'])
            reach = BESIDE_DOT if other['head'].get('dot') else BESIDE
            if abs(ahead) <= COLUMN or (apart <= 1 and -BESIDE <= ahead <= reach):
                near.append((abs(ahead), other))
        if near:
            partner = min(near, key=lambda item: item[0])[1]
            event['voice'] = 3 - partner['voice']
            event['partner'] = partner
    edges = [x for x in sorted(bars) if staff['x0'] + 2 * space < x < staff['x1'] - space]
    measures = [[] for _ in range(len(edges) + 1)]
    for event in events:
        measures[sum(1 for x in edges if x < event['x'])].append(event)
    base = key_alters(key)
    out = []
    for measure in measures:
        if not measure:
            continue
        # Columns: notes of two voices that stand at the same place along the staff, and the heads on one stem.
        columns = []
        for event in measure:
            for column in reversed(columns[-2:]):
                same_stem = any(other['voice'] == event['voice'] and other['stem_x'] is not None
                                and event['stem_x'] is not None and abs(other['stem_x'] - event['stem_x']) <= 0.3 * space
                                for other in column)
                other_voice = all(other['voice'] != event['voice'] for other in column) \
                    and abs(column[0]['x'] - event['x']) <= COLUMN * space
                # Two voices on one note, or a second apart, stand side by side with their stems on one line.
                one_line = all(other['voice'] != event['voice'] for other in column) and event['stem_x'] is not None \
                    and any(other['stem_x'] is not None and abs(other['stem_x'] - event['stem_x']) <= ONE_LINE * space
                            for other in column)
                stemless = event['stem_x'] is None and all(other['stem_x'] is None for other in column) \
                    and abs(column[0]['x'] - event['x']) <= COLUMN * space
                partner = any(other is event.get('partner') or other.get('partner') is event for other in column)
                if same_stem or other_voice or one_line or stemless or partner:
                    column.append(event)
                    break
            else:
                columns.append([event])
        free = {1: Fraction(0), 2: Fraction(0)}
        last_onset, last_shortest = None, None
        notes = []
        alters = dict(base)
        for column in columns:
            onset = max(free[voice] for voice in {event['voice'] for event in column})
            if last_onset is not None and onset <= last_onset:
                onset = last_onset + last_shortest
            for voice in {event['voice'] for event in column}:
                lengths = [event['length'] for event in column if event['voice'] == voice]
                length = min(lengths)
                free[voice] = onset + length
                for event in column:
                    if event['voice'] != voice:
                        continue
                    name = (MIDDLE[clef] + event['place']) % 7
                    sign = event['head'].get('sign')
                    if sign is not None:
                        alters[(name, event['place'])] = sign
                    alter = alters.get((name, event['place']), alters.get(name, 0))
                    step, alter, octave, midi = pitch_of(event['place'], clef, alter)
                    notes.append({'onset': onset, 'length': length, 'voice': voice, 'step': step, 'alter': alter,
                                  'octave': octave, 'midi': midi, 'x': event['x'], 'place': event['place'],
                                  'head': event['head']})
            last_onset = onset
            last_shortest = min(event['length'] for event in column)
        out.append(notes)
    return out


def _note_xml(note: dict, chord: bool) -> str:
    length = note['length']
    dotted = length / Fraction(3, 2)
    kind, dot = (TYPES[dotted], True) if dotted in TYPES and length not in TYPES else (TYPES.get(length), False)
    parts = ['<note>']
    if chord:
        parts.append('<chord/>')
    parts.append(f"<pitch><step>{note['step']}</step>"
                 + (f"<alter>{note['alter']}</alter>" if note['alter'] else '')
                 + f"<octave>{note['octave']}</octave></pitch>")
    parts.append(f'<duration>{int(length * DIVISIONS)}</duration><voice>{note["voice"]}</voice>')
    if kind:
        parts.append(f'<type>{kind}</type>')
        if dot:
            parts.append('<dot/>')
    parts.append('</note>')
    return ''.join(parts)


def musicxml(parts: list[list[dict]], title: str = '') -> str:
    """MusicXML of a page. `parts` holds one list for each staff of a system from the top (the same staff of every
    system is one part); each entry is a bar: {'notes': [...], 'clef': 'G' | 'G8vb' | 'F', 'key': int}."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
           '"http://www.musicxml.org/dtds/partwise.dtd">',
           '<score-partwise version="4.0">']
    if title:
        out.append(f'<work><work-title>{escape(title)}</work-title></work>')
    out.append('<identification><encoding><software>scoreread</software></encoding></identification>')
    out.append('<part-list>')
    for number in range(len(parts)):
        out.append(f'<score-part id="P{number + 1}"><part-name>Staff {number + 1}</part-name></score-part>')
    out.append('</part-list>')
    for number, bars in enumerate(parts):
        out.append(f'<part id="P{number + 1}">')
        shown = None
        for index, bar in enumerate(bars or [{'notes': [], 'clef': 'G', 'key': 0}]):
            out.append(f'<measure number="{index + 1}">')
            state = (bar['clef'], bar['key'])
            if state != shown:
                sign, line = ('F', 4) if bar['clef'] == 'F' else ('G', 2)
                octave = '<clef-octave-change>-1</clef-octave-change>' if bar['clef'] == 'G8vb' else ''
                divisions = f'<divisions>{DIVISIONS}</divisions>' if shown is None else ''
                out.append(f'<attributes>{divisions}<key><fifths>{bar["key"]}</fifths></key>'
                           f'<clef><sign>{sign}</sign><line>{line}</line>{octave}</clef></attributes>')
                shown = state
            for voice in (1, 2):
                notes = sorted((note for note in bar['notes'] if note['voice'] == voice),
                               key=lambda note: (note['onset'], -note['midi']))
                if not notes:
                    continue
                position = Fraction(0)
                if voice == 2:
                    ends = [note['onset'] + note['length'] for note in bar['notes'] if note['voice'] == 1]
                    back = max(ends) if ends else Fraction(0)
                    if back:
                        out.append(f'<backup><duration>{int(back * DIVISIONS)}</duration></backup>')
                last_onset = None
                for note in notes:
                    chord = note['onset'] == last_onset
                    if not chord:
                        if note['onset'] > position:
                            out.append(f'<forward><duration>{int((note["onset"] - position) * DIVISIONS)}</duration>'
                                       f'<voice>{voice}</voice></forward>')
                        elif note['onset'] < position:
                            out.append(f'<backup><duration>{int((position - note["onset"]) * DIVISIONS)}</duration></backup>')
                        position = note['onset'] + note['length']
                    out.append(_note_xml(note, chord))
                    last_onset = note['onset']
                if voice == 1:
                    # Voice 2 is written from the end of voice 1's last note: see the backup above.
                    ends = [note['onset'] + note['length'] for note in notes]
                    if position < max(ends):
                        out.append(f'<forward><duration>{int((max(ends) - position) * DIVISIONS)}</duration></forward>')
            out.append('</measure>')
        out.append('</part>')
    out.append('</score-partwise>')
    return '\n'.join(out) + '\n'

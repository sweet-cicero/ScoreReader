"""Turns the symbols of a page (scoreread.symbols) into music: pitches, voices, onsets, and MusicXML. No model is used.

- Pitch: the clef gives the note name of each pitch place, the key signature and the accidentals of the bar give
  its sharp or flat.
- Voices: on a staff of two parts, the upper part's stems go up and the lower part's stems go down. So a note with
  its stem up is voice 1 and a note with its stem down is voice 2. A head with both stems is in both voices.
- Onsets: notes that sound together stand in one column. Inside a bar, each column begins when the voices that
  sing in it are free. So one wrong length moves only the rest of its own bar.
"""
from __future__ import annotations

import re
from fractions import Fraction
from xml.sax.saxutils import escape

STEPS = 'CDEFGAB'
SEMITONES = [0, 2, 4, 5, 7, 9, 11]
SHARPS = [3, 0, 4, 1, 5, 2, 6]      # the note names that the sharps of a key signature raise, in their order: F C G D A E B
FLATS = [6, 2, 5, 1, 4, 0, 3]       # and the flats: B E A D G C F
MIDDLE = {'G': 34, 'G8vb': 27, 'F': 22}   # the note on the middle line of each clef, as 7 * octave + name
TYPES = {Fraction(4): 'whole', Fraction(2): 'half', Fraction(1): 'quarter', Fraction(1, 2): 'eighth',
         Fraction(1, 4): '16th', Fraction(1, 8): '32nd'}
DIVISIONS = 24       # a quarter note has this many parts: a triplet's notes need thirds
TRIPLET = Fraction(2, 3)   # a note under a triplet's bracket has this share of its drawn length
ONE_LINE = 0.6       # the stems of two voices on one pitch, or a second apart, are one line: at most this far apart
BESIDE = 1.8         # a whole note beside a note with a stem, on its pitch or a second from it, is at most this far from it
BESIDE_DOT = 2.6     # or this far, at the right of a note with a dot
ACROSS = 0.9         # the columns of two staves of a system are one column when they stand at most this far apart
AGREE = 2            # this many voices must agree on the length of a step before another voice's note is changed
AGREE_HOLLOW = True  # where as many voices say a half note as say a quarter note (AGREE or more each), the step is a
#                      half note: a copy fills the hole of a half note, and it opens no hole in a quarter note
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

LETTER = re.compile(r'^([A-G])([b♭#♯]?)([↓↑]?)$')
UNISON = re.compile(r'^(Un(is)?\.?|un(is)?\.)$')


def letter_mark(text: str, x: float, clef: str) -> dict | None:
    """The ison mark that a word over a chant staff stands for: the name of a note ("E", "Bb", "G↓": an octave
    lower), or "Un." where the ison sings in unison with the melody. An event as staff_columns() gives it, with
    'unison' for the second kind; None when the word is no such mark. The note lies in the octave from the C under
    the middle of a treble staff upward (C4 to B4), where the typed hymns have their ison; under a bass clef or a
    treble clef with an 8 in the octave under that."""
    if UNISON.match(text):
        return {'x': x, 'place': 0, 'voice': 1, 'head': {'hollow': True, 'stems': [], 'cx': x, 'letter': text},
                'length': Fraction(4), 'stem_x': None, 'unison': True}
    found = LETTER.match(text)
    if not found:
        return None
    octave = (4 if clef == 'G' else 3) + {'↓': -1, '↑': 1}.get(found.group(3), 0)
    place = 7 * octave + STEPS.index(found.group(1)) - MIDDLE[clef]
    head = {'hollow': True, 'stems': [], 'cx': x, 'place': place, 'letter': text}
    if found.group(2):
        head['sign'] = -1 if found.group(2) in 'b♭' else 1
    return {'x': x, 'place': place, 'voice': 1, 'head': head, 'length': Fraction(4), 'stem_x': None}


def held(melody: list[list[dict]], marks: list[list[dict]], pitch, gap: float, state: dict) -> list[list[dict]]:
    """The ison in time with the melody: for each bar of the melody, the notes that the ison holds in it.

    An ison mark holds from the melody's note that it stands at until the next mark, over the bar lines and the
    ends of the lines: it is written as one note in each bar, tied to the next. Before the first mark of a page the
    ison is silent. After a mark of unison the ison sings the melody's notes. `pitch` makes the note of a mark;
    `state` carries the mark that holds from one line to the next."""
    out = []
    for notes, found in zip(melody, marks):
        length = max((note['onset'] + note['length'] for note in notes), default=Fraction(0))
        cuts = []
        for event in sorted(found, key=lambda event: event['x']):
            later = [note['onset'] for note in notes if note['x'] >= event['x'] - 0.6 * gap]
            cuts.append((min(later) if later else length, event))
        bar, at = [], Fraction(0)
        for onset, event in cuts + [(length, None)]:
            if onset > at and state.get('unison'):
                for note in notes:
                    if at <= note['onset'] < onset and note['voice'] == min(other['voice'] for other in notes):
                        bar.append({key: value for key, value in dict(note, tie_start=False, tie_stop=False).items() if key != 'lyric'})
            elif onset > at and state.get('note') is not None:
                piece = dict(state['note'], onset=at, length=onset - at, tie_stop=state.get('last') is not None, tie_start=False)
                if state.get('last') is not None:
                    state['last']['tie_start'] = True
                bar.append(piece)
                state['last'] = piece
            at = max(at, onset)
            if event is not None:
                state['unison'] = bool(event.get('unison'))
                state['note'], state['last'] = (None if state['unison'] else pitch(event)), None
        out.append(bar)
    return out



def staff_columns(staff: dict, heads: list[dict], bars: list[float], space: float) -> list[list[list[dict]]]:
    """The notes of a staff in bars and columns: a list of bars, each a list of columns, each a list of events
    {'x', 'place', 'voice', 'head', 'length', 'stem_x'}. The notes of a column begin together."""
    events = []
    for head in heads:
        place = int(round(head['place']))
        voices = sorted({1 if stem['direction'] == 'up' else 2 for stem in head['stems']}) or [1]
        for voice in voices:
            stem = next((s for s in head['stems'] if (s['direction'] == 'up') == (voice == 1)), None)
            length = length_of(head, head['tails'].get(stem['direction'], 0) if stem else 0)
            if (stem['direction'] if stem else '') in head.get('triplet', ()):
                length *= TRIPLET
            events.append({'x': head['cx'], 'place': place, 'voice': voice, 'head': head, 'length': length,
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
        out.append(columns)
    return out


def agree_lengths(plans: dict[int, list[list[list[dict]]]], bars: dict[int, list[float]], space: float) -> int:
    """A music check for the staves of one system: notes that begin together and whose next notes begin together are
    as long as each other. Returns the number of lengths that were changed.

    `plans` holds what staff_columns() gave for each staff of the system, and `bars` the bar lines of each staff. The
    columns of the staves are lined up by their place along the system. From one column to the next, every voice
    that has a note in both columns says how long that step is. Where two or more voices agree and outnumber the
    others, the step is sure, and a note that says something else is changed: a flag or a dot was missed, a slur
    was taken for a beam, or the hole of a half note was filled by the copy. A note that reaches over several
    columns is only made shorter, never longer: a note can be missing after it, or a rest can stand there."""
    xs = sorted(x for index in plans for x in bars.get(index, []))
    groups = []
    for x in xs:
        if groups and x - groups[-1][-1] <= space:
            groups[-1].append(x)
        else:
            groups.append([x])
    edges = [sum(group) / len(group) for group in groups]
    cells = {}
    for index, measures in plans.items():
        for measure in measures:
            for column in measure:
                x = sorted(event['x'] for event in column)[len(column) // 2]
                cells.setdefault(sum(1 for edge in edges if edge < x), []).append((x, index, column))
    changed = 0
    for group in cells.values():
        group.sort(key=lambda cell: cell[0])
        clusters = []
        for x, index, column in group:
            best = None
            for cluster in clusters[-2:]:
                if all(other[1] != index for other in cluster['cells']) and abs(cluster['x'] - x) <= ACROSS * space \
                        and (best is None or abs(cluster['x'] - x) < abs(best['x'] - x)):
                    best = cluster
            if best is None:
                clusters.append({'x': x, 'cells': [(x, index, column)]})
            else:
                best['cells'].append((x, index, column))
                best['x'] = sum(cell[0] for cell in best['cells']) / len(best['cells'])
        where = {}
        for number, cluster in enumerate(clusters):
            for x, index, column in cluster['cells']:
                for voice in sorted({event['voice'] for event in column}):
                    where.setdefault((index, voice), []).append((number, [event for event in column if event['voice'] == voice]))
        count = len(clusters)
        votes = [dict() for _ in range(count)]
        spans = []
        for sequence in where.values():
            for (number, events), (following, _) in zip(sequence, sequence[1:] + [(count, None)]):
                length = min(event['length'] for event in events)
                spans.append((number, following, events, length))
                if following == number + 1:
                    votes[number][length] = votes[number].get(length, 0) + 1
        sure = [None] * count
        for number in range(count):
            if votes[number]:
                best = max(votes[number], key=votes[number].get)
                if votes[number][best] >= AGREE and votes[number][best] > sum(votes[number].values()) - votes[number][best]:
                    sure[number] = best
                elif AGREE_HOLLOW and len(votes[number]) == 2 and votes[number].get(Fraction(1), 0) >= AGREE \
                        and votes[number].get(Fraction(1)) == votes[number].get(Fraction(2)):
                    sure[number] = Fraction(2)
        for number, following, events, length in spans:
            for event in events:      # for the record: how the voices voted on this note's steps
                event['votes'] = [{str(value): votes[step][value] for value in votes[step]} for step in range(number, following)]
            if any(sure[step] is None for step in range(number, following)):
                continue
            total = sum(sure[number:following], Fraction(0))
            if total == length or not (total in TYPES or total / Fraction(3, 2) in TYPES or total / TRIPLET in TYPES):
                continue
            if following == number + 1 or length > total:
                for event in events:
                    event['length'] = total
                    event['agreed'] = True
                changed += 1
    return changed


def build_staff(staff: dict, heads: list[dict], bars: list[float], clef: str, key: int, space: float,
                measures: list[list[list[dict]]] | None = None) -> list[list[dict]]:
    """The bars of a staff: each a list of notes {'onset', 'length', 'voice', 'step', 'alter', 'octave', 'midi', 'x',
    'type', 'dot'} with onsets counted from the bar's start, in quarter notes. `measures` is what staff_columns()
    gave for this staff, when the lengths were checked against the other staves first."""
    if measures is None:
        measures = staff_columns(staff, heads, bars, space)
    base = key_alters(key)
    out = []
    for columns in measures:
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
                free[voice] = onset + min(lengths)
                for event in column:
                    if event['voice'] != voice:
                        continue
                    # Each head keeps its own length: a head of the other voice whose stem was not found stands in
                    # this voice's column too.
                    length = event['length']
                    name = (MIDDLE[clef] + event['place']) % 7
                    sign = event['head'].get('sign')
                    if sign is not None:
                        alters[(name, event['place'])] = sign
                    alter = alters.get((name, event['place']), alters.get(name, 0))
                    step, alter, octave, midi = pitch_of(event['place'], clef, alter)
                    notes.append({'onset': onset, 'length': length, 'voice': voice, 'step': step, 'alter': alter,
                                  'octave': octave, 'midi': midi, 'x': event['x'], 'place': event['place'],
                                  'head': event['head'], 'agreed': bool(event.get('agreed')),
                                  'tie_start': bool(event['head'].get('tie_start')),
                                  'tie_stop': bool(event['head'].get('tie_stop')),
                                  'votes': event.get('votes')})
            last_onset = onset
            last_shortest = min(event['length'] for event in column)
        out.append(notes)
    return out


def _note_xml(note: dict, chord: bool) -> str:
    length = note['length']
    # A note of a triplet is drawn as a note one and a half times as long.
    drawn = length / TRIPLET
    triplet = length not in TYPES and length / Fraction(3, 2) not in TYPES and (drawn in TYPES or drawn / Fraction(3, 2) in TYPES)
    if not triplet:
        drawn = length
    dotted = drawn / Fraction(3, 2)
    kind, dot = (TYPES[dotted], True) if dotted in TYPES and drawn not in TYPES else (TYPES.get(drawn), False)
    parts = ['<note>']
    if chord:
        parts.append('<chord/>')
    parts.append(f"<pitch><step>{note['step']}</step>"
                 + (f"<alter>{note['alter']}</alter>" if note['alter'] else '')
                 + f"<octave>{note['octave']}</octave></pitch>")
    ties = [name for name, key in (('stop', 'tie_stop'), ('start', 'tie_start')) if note.get(key)]
    parts.append(f'<duration>{int(length * DIVISIONS)}</duration>' + ''.join(f'<tie type="{name}"/>' for name in ties)
                 + f'<voice>{note["voice"]}</voice>')
    if kind:
        parts.append(f'<type>{kind}</type>')
        if dot:
            parts.append('<dot/>')
        if triplet:
            parts.append('<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>')
    if ties:
        parts.append('<notations>' + ''.join(f'<tied type="{name}"/>' for name in ties) + '</notations>')
    if note.get('lyric'):
        syllabic = f'<syllabic>{note["syllabic"]}</syllabic>' if note.get('syllabic') else ''
        parts.append(f'<lyric number="1">{syllabic}<text>{escape(note["lyric"])}</text></lyric>')
    parts.append('</note>')
    return ''.join(parts)


def musicxml(parts: list[list[dict]], title: str = '', names: dict[int, str] | None = None) -> str:
    """MusicXML of a page. `parts` holds one list for each staff of a system from the top (the same staff of every
    system is one part); each entry is a bar: {'notes': [...], 'clef': 'G' | 'G8vb' | 'F', 'key': int}. `names`
    gives a part another name than 'Staff n': the ison that was read from its marks is the part 'Ison'."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
           '"http://www.musicxml.org/dtds/partwise.dtd">',
           '<score-partwise version="4.0">']
    if title:
        out.append(f'<work><work-title>{escape(title)}</work-title></work>')
    out.append('<identification><encoding><software>scoreread</software></encoding></identification>')
    out.append('<part-list>')
    for number in range(len(parts)):
        name = (names or {}).get(number, f'Staff {number + 1}')
        out.append(f'<score-part id="P{number + 1}"><part-name>{escape(name)}</part-name></score-part>')
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

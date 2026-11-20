"""Reads a clean page with the reader's own symbol step: no model, no network, only rules on the ink.

The steps: the layers of the ink (scorereader.layers), the symbols on them (scorereader.symbols), the clef and the key
signature at the start of each staff (scorereader.starts), the sharps, flats and naturals before a note
(scorereader.signs), the ties (scorereader.ties), and the music rules that turn the symbols into notes (scorereader.music).

The yardstick (bench/yardstick, copisteria's network) gives the same kind of result for the same clean page, so the
two can be measured side by side on the test kit. Nothing of it is loaded here.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np

from .drone import letter_marks, without_breves
from .layers import read_layers
from .meter import COMMON_ROWS, mid_signs
from .music import MIDDLE, agree_lengths, bar_sums, build_staff, full_sum, held, musicxml, staff_columns
from . import music as _music
from .rests import block_rests, in_rest, quarter_rests
from .signs import bar_signs, note_signs
from .starts import read_start, read_starts
from .symbols import bar_lines, bar_marks, faint_bars, big_holes, broken_stems, count_tails, dots, hole_heads, loops_have_flags, lost_stems, gone_stems, chord_stems, read_symbols, \
    slit_page, thin_heads, without_bar_pieces, without_end_marks, without_flag_curls, without_flag_loops, without_flag_trails, without_flat_cells, without_f_marks, without_line_marks, without_p_bowls, without_stem_end_marks, without_stem_meets, without_stem_spans, without_joints, without_upright_holes, chord_wholes, dotless_wholes
from .ties import read_ties
from .triplets import mark_triplets
from .words import cut_stems, word_bands, word_rows

SIGNS = 'strokes'
TIMES = True         # the numbers of a time signature in the middle of a staff are no notes (scorereader.meter)
CHECK = True         # the music check: the voices of a system agree on the lengths (scorereader.music.agree_lengths)
REST_HEADS = True    # a head in a printed whole or half rest is no note (scorereader.rests.BLOCK)
REST_QUARTER = 0.75  # ... and a printed quarter rest too, for the voice that its place names: the upper voice's stands at least
#                      this many staff spaces over the middle line, the lower voice's as far under it (one in the middle is
#                      both voices'), where that voice's notes leave a gap of a quarter note or more; the rest is the
#                      quarter note before the voice's next note (None: no quarter rest is written)
REST_VOICE = True    # a printed whole or half rest is written into the music for the voice that is silent there: the voice
#                      of a staff of two parts that has no note in its bar, or the voice whose notes leave a gap where it
#                      stands; it lasts from that voice's last note before it to its next note in the bar, or to the end
#                      of the bar's notes, and never longer than the bar's notes. In a bar of one voice the stems say
#                      nothing of the voice (a part alone is stemmed by its place on the staff): its notes are the part
#                      whose notes in the bars of two voices of the staff are nearer in pitch, and the rest the other's
OCTAVE = 0.4         # a treble staff with a small 8 under its clef sounds an octave lower, when this share of the staves at
                     # its place in the systems show the 8 (scorereader.starts.octave_mark); None: the 8 is not read
TENORS = 2.5         # a number: a treble staff over the bass staff is the tenors' only when its notes do not sound this many
                     # places under the notes of the bass staff (the middle note of each); None: always the tenors'


def page_starts(grey: np.ndarray, places: list[dict]) -> list[dict]:
    """A first look at a clean page: what the start of each staff shows (its clef and its key signature), for the
    vote of all pages of a hymn on its key (scorereader.starts.hymn_key)."""
    if not places:
        return []
    layers = read_layers(grey, places)
    layers['words'] = word_bands(layers)
    return [read_start(layers, index) for index in range(len(layers['staves']))]


ALONE_STEP = 1.3     # a half rest in a bar of one voice is the other voice's where the notes beside it stand no further
#                      apart than this many times the bar's middle step from note to note (see voice_rests)
ALONE_NEAR = 8.0     # ... and no rest of a bar of one voice that stands further than this many staff spaces from every
#                      note of its bar (a bar whose bar lines were not read)
REST_APART = 2.0     # a printed rest stands apart from the notes: a block with the stem of a note at each of its ends, within
#                      this many staff spaces and in the rows of the stem, is the bow of a tie that a thick copy prints into a
#                      staff line, between the heads and the beam of a group (None: not asked)


def _between_stems(block: dict, notes: list[dict], space: float) -> bool:
    """Whether a block stands between the stems of two notes (see REST_APART)."""
    middle = (block['top'] + block['bottom']) / 2

    def stem_at(low, high):
        return any(low <= stem['x'] <= high and min(note['head']['cy'], stem['end']) <= middle <= max(note['head']['cy'], stem['end'])
                   for note in notes for stem in note['head']['stems'])
    return stem_at(block['x0'] - REST_APART * space, block['x0']) and stem_at(block['x1'], block['x1'] + REST_APART * space)


def voice_places(staves: list[dict], plans: dict) -> dict:
    """The mean place of each voice of each staff of a system (by its number), over the bars of the page where both
    voices have notes: {number: {voice: place}}."""
    found = {}
    for index, staff in enumerate(staves):
        for bar in plans[index]:
            events = [event for column in bar for event in column]
            if len({event['voice'] for event in events}) == 2:
                for event in events:
                    found.setdefault(staff['number'], {}).setdefault(event['voice'], []).append(event['place'])
    return {number: {voice: sum(places) / len(places) for voice, places in voices.items()}
            for number, voices in found.items() if len(voices) == 2}


def voice_rests(staff: dict, built: list[list[dict]], plan: list, bars: list[float], blocks: list[dict], space: float,
                means: dict | None = None) -> dict:
    """The printed rests of a staff as rests of its voices (see REST_VOICE and REST_QUARTER): {bar number: [{'voice',
    'onset', 'length'}]}.
    `means` holds the mean place of each voice of the staff (voice_places())."""
    if not blocks or len(built) != len(plan):
        return {}
    edges = [x for x in sorted(bars) if staff['x0'] + 2 * space < x < staff['x1'] - space]
    measures = [sum(1 for x in edges if x < bar[0][0]['x']) for bar in plan]
    out, alone, quarters = {}, [], {}
    every = [note for bar in built for note in bar]
    for block in sorted(blocks, key=lambda block: block['x']):
        quarter = block.get('kind') != 'block'
        if not quarter and REST_APART is not None and _between_stems(block, every, space):
            continue
        measure = sum(1 for x in edges if x < block['x'])
        if measure not in measures:
            continue
        number = measures.index(measure)
        notes = built[number]
        if not notes:
            continue
        end = max(note['onset'] + note['length'] for note in notes)
        gaps = {}
        for voice in (1, 2):
            own = [note for note in notes if note['voice'] == voice]
            if not own or any(block['x0'] - 0.5 * space <= note['x'] <= block['x1'] + 0.5 * space for note in own):
                continue
            before = [note['onset'] + note['length'] for note in own if note['x'] < block['x0']]
            after = [note['onset'] for note in own if note['x'] > block['x1']]
            begin, until = max(before, default=Fraction(0)), min(after, default=end)
            if until > begin:
                gaps[voice] = (begin, until)
        if quarter:
            # A quarter rest is the voice's that its place names, where that voice's notes leave room for it.
            voice = 1 if block['middle'] <= -REST_QUARTER else 2 if block['middle'] >= REST_QUARTER else None
            if voice in gaps:
                quarters[(number, voice) + gaps[voice]] = quarters.get((number, voice) + gaps[voice], 0) + 1
            continue
        if len({note['voice'] for note in notes}) == 1 and not gaps:
            # A bar of one voice that sings on over the rest: the rest is the other voice's, for the whole bar. A whole
            # rest says so itself; a half rest only where a note stands in its columns, or where the notes beside it
            # stand no further apart than the bar's notes do (the onsets do not count the rest: where both voices
            # rest, the notes beside it stand far apart). A rest far from every note of its bar is in a bar whose bar
            # lines were not read.
            xs = sorted(note['x'] for note in notes)
            steps = sorted(b - a for a, b in zip(xs, xs[1:]) if b - a > 0.3 * space)
            left = [x for x in xs if x < block['x0'] - 0.5 * space]
            right = [x for x in xs if x > block['x1'] + 0.5 * space]
            stacked = any(block['x0'] - 0.5 * space <= x <= block['x1'] + 0.5 * space for x in xs)
            even = bool(left and right and steps) and right[0] - left[-1] <= ALONE_STEP * steps[len(steps) // 2]
            near = min(abs(x - block['x']) for x in xs) <= ALONE_NEAR * space
            if near and (block.get('hangs') or stacked or even) and number not in alone:
                alone.append(number)
        elif len(gaps) == 1:
            # The voice whose notes leave a gap where the rest stands (in a bar of one voice: both voices rest there).
            voice, span = next(iter(gaps.items()))
            if not any(rest['voice'] == voice and rest['onset'] < span[1] and span[0] < rest['onset'] + rest['length']
                       for rest in out.get(number, [])):
                out.setdefault(number, []).append({'voice': voice, 'onset': span[0], 'length': span[1] - span[0]})
    # The quarter rests of a gap are its last quarter notes, where the gap holds them all.
    for (number, voice, begin, until), count in sorted(quarters.items()):
        if until - begin >= count and not any(rest['voice'] == voice and rest['onset'] < until and until - count < rest['onset'] + rest['length']
                                              for rest in out.get(number, [])):
            out.setdefault(number, []).append({'voice': voice, 'onset': until - count, 'length': Fraction(count)})
    # The bars of one voice, in runs of bars that follow each other: the stems of a part alone say nothing of its voice,
    # so the run's notes are the voice whose notes stand nearer on the page, and the rest is the other voice's.
    runs = []
    for number in sorted(alone):
        if runs and runs[-1][-1] == number - 1:
            runs[-1].append(number)
        else:
            runs.append([number])
    for run in runs:
        notes = [note for number in run for note in built[number]]
        singer = notes[0]['voice']
        if means and len(means) == 2:
            place = sum(note['place'] for note in notes) / len(notes)
            singer = 1 if abs(place - means[1]) <= abs(place - means[2]) else 2
        for number in run:
            for note in built[number]:
                note['voice'] = singer
            end = max(note['onset'] + note['length'] for note in built[number])
            out.setdefault(number, []).append({'voice': 3 - singer, 'onset': Fraction(0), 'length': end})
    return out


def read_page(grey: np.ndarray, places: list[dict], title: str = '', key_before: int | None = None,
              clefs_before: list[str] | None = None, key_hymn: int | None = None, ties_before: list | None = None) -> dict:
    """Reads a clean page (a grey image and the places from clean_page()). Returns {'musicxml': text, 'notes': [...],
    'staves': n, 'systems': n, 'key': n, 'clefs': [...], 'layers': the layers}, and what was found on the way
    ('heads', 'bars', 'starts', 'ends', 'signs', 'note_signs', 'keys', 'ties', 'times', 'rests') for pictures and checks.
    `key_before` is the key of the page before in the same hymn: a page that shows no key signature has that key.
    `clefs_before` are the clefs of the staves of a system on that page, and `key_hymn` is the key that the staves
    of all pages of the hymn voted for together (see scorereader.starts). `ties_before` is the 'ties_out' of the page
    before: the notes that a tie leaves over the end of that page, as (the number of the staff in its system, the
    place). A tie comes to the first notes of this page only there (see scorereader.ties.TIE_PAGE).

    'key' is the key of the page, and 'staff_keys' the key of each staff (a page with two pieces has two keys).
    'ties_out' are the notes of the last system that a tie leaves over the end of the page (for the next page).

    Each note: 'staff', 'bar', 'onset' and 'length' (quarter notes, the onset from the bar's start), 'voice', 'step',
    'alter', 'octave', 'midi', 'x', 'place' (0 is the middle line, +1 a step up), 'agreed' (the music check changed
    its length), 'votes' (how the voices voted on its steps), 'tie_start' and 'tie_stop' (a tie begins or ends at
    the note; the tied notes stay two notes, as in MusicXML) and 'mark': what the note was read from (the size and
    place of the head, hollow or filled, its hole, its dot, its sign, its stems and their flags or beams).

    The words are read after the notes, for the whole hymn at once (scorereader.lyrics): 'part_notes' holds, for each
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
    # A printed whole or half rest is no note either: it is a block that hangs from a line or sits on it.
    blocks = block_rests(layers, ends)
    if REST_HEADS:
        heads = [head for head in heads if not in_rest(head, blocks, space)]
    # The pieces of a thick bar line between the staff lines are no heads, and the thin line beside it is no stem.
    heads = without_bar_pieces(layers, heads)
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
    orphans = [head for head in symbols['orphans'] if head['cx'] > ends[head['staff']] + 0.3 * space
               and not in_rest(head, rests, space)]
    lost_stems(layers, heads, bars, ends, orphans)
    heads = without_joints(heads, space)
    heads += thin_heads(layers, heads, bars, ends)
    # A head whose stem the scan lost.
    heads += gone_stems(layers, heads, orphans, symbols['marks'])
    # A head of a chord that stands where the stem of a read head begins and was left without it.
    heads += chord_stems(layers, heads, orphans)
    # A hollow head read from its hole; where the copy broke its rim, it replaces the pieces of the rim.
    from_holes = hole_heads(layers, heads, ends, bars, symbols['signs'])
    from_holes = [head for head in from_holes if not any(head is mark for mark in bar_marks(layers, from_holes))]
    gone = {id(other) for head in from_holes for other in head.get('replaces', [])}
    heads = [head for head in heads if id(head) not in gone] + from_holes
    # The numbers of a new time signature are no notes.
    times = mid_signs(layers, ends, bars) if TIMES else {}
    if TIMES:
        heads = [head for head in heads if not any(sign['x0'] - 0.2 * space <= head['cx'] <= sign['x1'] + 0.2 * space
                                                   and (not sign.get('bold') or abs(head['cy'] - staves[head['staff']]['rows'][2])
                                                        <= COMMON_ROWS * staves[head['staff']]['space'])
                                                   for sign in times[head['staff']])]
    # (The other finders of heads can find the sign at the bar line again.)
    heads = [head for head in heads
             if not any(sign['staff'] == head['staff'] and sign['x0'] - 0.2 * space <= head['cx'] <= sign['x1'] + 0.2 * space
                        and sign['top'] - 0.3 * space <= head['cy'] <= sign['bottom'] + 0.3 * space and head is not sign['head']
                        for sign in at_bars)]
    # (The other finders of heads can find a rest again.)
    heads = [head for head in heads if not in_rest(head, rests + (blocks if REST_HEADS else []), space)]
    heads = without_bar_pieces(layers, heads)
    heads = without_end_marks(layers, heads)
    for head in heads:
        head['staff_ref'] = staves[head['staff']]
    # A stem ends where the words begin.
    cut_stems(layers, heads, words)
    # A stem that breaks off before its beam ends at the beam.
    broken_stems(layers, heads)
    count_tails(layers, heads)
    loops_have_flags(layers, heads)
    # A hollow mark whose inside stands upright is the loop of a flag or the room of a double bar line, no head.
    heads = without_upright_holes(layers, heads)
    heads = without_flag_loops(heads, space)
    heads = without_flat_cells(layers, heads)
    heads = without_flag_trails(layers, heads)
    heads = without_flag_curls(heads, space)
    heads = without_stem_end_marks(layers, heads)
    heads = without_stem_spans(layers, heads)
    # A mark that hangs on a line of the system is a head only by its own shape: no stem goes on through the next staff.
    heads = without_line_marks(layers, heads, bars)
    # The letters of the dynamics: the paper between the two letters of an ff is no head, and the bowl of a p is no
    # whole note.
    heads = without_f_marks(layers, heads)
    heads = without_p_bowls(layers, heads)
    heads = without_stem_meets(layers, heads)
    # A whole note that touches the half note of another voice keeps no stem of that note.
    chord_wholes(layers, heads)
    dots(layers, heads)
    # A whole note without a dot keeps no stem of the dotted half notes that it touches.
    dotless_wholes(layers, heads)
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
    slit_page(heads)
    # A tie: a bow from a head to the next head of its pitch.
    ties = read_ties(layers, heads, ties_before)
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
    # The ison's letters over the staves of a chant page, and the breve that a print sets under a letter for the
    # ison's note: it is no note of the melody (scorereader.drone.BREVE).
    letters = {index: letter_marks(layers, index, clefs[index]) for index in range(len(staves))} if width == 1 else {}
    heads = without_breves(layers, heads, letters)
    parts = [[] for _ in range(width)]
    notes, part_notes = [], []
    plans = {index: staff_columns(staff, [head for head in heads if head['staff'] == index], bars[index], space)
             for index, staff in enumerate(staves)}
    # Music check: the voices of a system agree on the length of each step from column to column.
    agreed = 0
    if CHECK:
        systems = [{index: plans[index] for index, staff in enumerate(staves) if staff['system'] == system}
                   for system in sorted({staff['system'] for staff in staves})]
        # The sum that most bars of the page have: a bar with one open step is as long (scorereader.music.BAR_FULL).
        # On a page whose bars keep their length, a bar that is too long is looked at too (scorereader.music.BAR_OVER).
        sums = [value for own in systems for value in bar_sums(own, bars, space, rests)]
        full, steady = full_sum(sums), full_sum(sums, _music.BAR_OVER) if _music.BAR_OVER else None
        for own in systems:
            agreed += agree_lengths(own, bars, space, rests, full, steady)
    # The ison of a chant page (one staff for the melody): the letters over the staff name its note (scorereader.drone).
    # It is a part of its own after the melody; its notes are in no list of notes, so no syllable is set under them.
    drone, holding = [], {}
    places = voice_places(staves, plans) if REST_VOICE else {}
    for index, staff in enumerate(staves):
        built = build_staff(staff, [], bars[index], clefs[index], keys[index], space, plans[index])
        if width == 1 and built:
            marks = [[] for _ in built]
            for mark in letters[index]:
                later = [number for number, bar in enumerate(plans[index]) if any(column[0]['x'] >= mark['x'] - 0.6 * space for column in bar)]
                marks[later[0] if later else len(built) - 1].append(mark)

            def pitch(event: dict, staff=staff, index=index) -> dict:
                return build_staff(staff, [], [], clefs[index], keys[index], space, [[[dict(event, voice=1)]]])[0][0]

            for bar in held(built, marks, pitch, space, holding):
                drone.append({'notes': [{name: value for name, value in note.items() if name != 'head'} for note in bar],
                              'clef': clefs[index], 'key': keys[index]})
        quiet = voice_rests(staff, built, plans[index], bars[index], [block for block in blocks if block['staff'] == index]
                            + ([rest for rest in rests if rest['staff'] == index] if REST_QUARTER is not None else []), space,
                            places.get(staff['number'])) if REST_VOICE else {}
        for number, bar in enumerate(built):
            parts[staff['number']].append({'notes': bar, 'clef': clefs[index], 'key': keys[index]})
            if quiet.get(number):
                parts[staff['number']][-1]['rests'] = quiet[number]
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
    # The notes are read: the step of the words gets the rows that stand staggered too.
    words = layers['words'] = word_rows(layers)
    return {'musicxml': musicxml(parts, title, names), 'parts': parts, 'names': names, 'notes': notes, 'part_notes': part_notes, 'title': title,
            'staves': len(staves), 'systems': len({staff['system'] for staff in staves}), 'key': key, 'clefs': clefs, 'layers': layers,
            'system_clefs': [system_clefs[number] for number in sorted(system_clefs)],
            'ties_out': [[staves[head['staff']]['number'], int(round(head['place']))] for head in heads if head.get('tie_out')],
            'heads': heads, 'note_signs': found, 'starts': begin['starts'], 'ends': ends, 'bars': bars, 'signs': symbols['signs'],
            'keys': [start['key'] for start in begin['starts']], 'staff_keys': keys, 'ties': ties, 'words': words, 'triplets': triplets,
            'rests': rests, 'times': [([start['time']] if start.get('time') else []) + times.get(index, [])
                      for index, start in enumerate(begin['starts'])]}
